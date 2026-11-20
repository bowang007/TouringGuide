"""Path-trace 360-degree equirectangular panoramas (and optional rectilinear previews) at the
tour's camera stops, matching the web app's panorama convention exactly.

Convention (verified): image centre column (u=0.5) faces SCENE -z (north / yaw 0), u increases
clockwise seen from above (u=0.75 faces +x/east), top row = up. Camera = SCENE node.p.
In Blender: equirect camera at ft2bl(node.p) with rotation (90deg, 0, 0).

Usage:
  blender -b tools/render/.cache/house.blend --python tools/render/render_panos.py -- \
      --nodes all|L0,K0 --width 4096 --samples 768 --out tools/render/.cache/panos \
      [--preview] [--preview-only] [--exposure auto|<stops>] [--fov 90]
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from bl.common import CACHE_DIR, DATA_DIR, ft2bl  # noqa: E402

TARGET_MEDIAN = 0.22       # scene-linear median luminance the exposure maps to (bright real-estate look)
# White balance. 'auto' (default) balances every stop like a listing photographer: the white painted
# surfaces seen in the low-sample exposure probe (walls, ceilings, trim, white doors, stucco) are
# brought to WB_TARGET, a slightly warm white, in the final display image. Stops without enough
# white surface fall back to WB_DEFAULT. A fixed balance is '--wb <kelvin>[,<tint>]'.
WB_DEFAULT = (6500.0, 10.0)        # (temperature K, tint)
WB_KELVIN = WB_DEFAULT[0]          # kept for older callers
WB_TARGET = (1.06, 0.88)           # display R/G and B/G of white paint after balancing
WB_LIMITS = ((3500.0, 14000.0), (-30.0, 35.0))
# Stops whose only white paint is lit by the room's own warm materials: the auto balance would cancel the room's
# colour, so they get a fixed balance (the shared bath's wood-look wall and Spanish-cream stone tint its ceiling).
WB_NODE = {'A1': (5000.0, 0.0)}
WB_MATERIALS = ('M_paint_wall', 'M_paint_ceiling', 'M_paint_trim', 'M_plaster_white', 'M_door_slab', 'M_stucco')
WB_PASS_INDEX = 7


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--nodes', default='all')
    ap.add_argument('--width', type=int, default=4096)
    ap.add_argument('--samples', type=int, default=768)
    ap.add_argument('--out', default=os.path.join(CACHE_DIR, 'panos'))
    ap.add_argument('--preview', action='store_true', help='also render a rectilinear preview at the node yaw')
    ap.add_argument('--preview-only', action='store_true')
    ap.add_argument('--preview-width', type=int, default=1600)
    ap.add_argument('--fov', type=float, default=90.0)
    ap.add_argument('--yaw', type=float, default=None, help='override preview yaw (radians)')
    ap.add_argument('--exposure', default='auto')
    ap.add_argument('--look', default='AgX - Base Contrast')
    ap.add_argument('--wb', default='auto', help="'auto' or '<kelvin>[,<tint>]'")
    ap.add_argument('--interior-gain', type=float, default=None, help='scale all fixtures (default lighting.INTERIOR_GAIN)')
    ap.add_argument('--sky-gain', type=float, default=None)
    ap.add_argument('--sun-gain', type=float, default=None)
    ap.add_argument('--emission-gain', type=float, default=None)
    return ap.parse_args(argv)


def setup_cycles(samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    cy = sc.cycles
    cy.device = 'GPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.008
    cy.adaptive_min_samples = 64
    cy.use_denoising = True
    for den in ('OPENIMAGEDENOISE', 'OPTIX'):
        try:
            cy.denoiser = den
            break
        except TypeError:
            continue
    try:
        cy.denoising_use_gpu = True
        cy.denoising_prefilter = 'ACCURATE'
        cy.denoising_quality = 'HIGH'
    except AttributeError:
        pass
    cy.use_light_tree = True
    cy.max_bounces = 16
    cy.diffuse_bounces = 8
    cy.glossy_bounces = 6
    cy.transmission_bounces = 16
    cy.transparent_max_bounces = 16
    cy.sample_clamp_direct = 0.0
    cy.sample_clamp_indirect = 12.0
    cy.blur_glossy = 0.6
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    sc.render.film_transparent = False
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = 'AgX'
    sc.render.image_settings.color_depth = '8'
    # Neutralize the blue daylight cast like a real-estate photographer would (mixed light).
    vs = sc.view_settings
    try:
        vs.use_white_balance = True
        vs.white_balance_temperature, vs.white_balance_tint = WB_DEFAULT
    except AttributeError:
        pass


def set_look(look):
    vs = bpy.context.scene.view_settings
    try:
        vs.look = look
    except TypeError:
        try:
            vs.look = 'None'
        except TypeError:
            pass


def make_camera():
    cam = bpy.data.objects.get('TG PanoCam')
    if cam is None:
        cd = bpy.data.cameras.new('TG PanoCam')
        cam = bpy.data.objects.new('TG PanoCam', cd)
        bpy.context.scene.collection.objects.link(cam)
    cam.data.clip_start = 0.02
    cam.data.clip_end = 500
    bpy.context.scene.camera = cam
    return cam


def as_pano(cam):
    cd = cam.data
    cd.type = 'PANO'
    try:
        cd.panorama_type = 'EQUIRECTANGULAR'
    except (AttributeError, TypeError):
        cd.cycles.panorama_type = 'EQUIRECTANGULAR'
    cam.rotation_euler = (math.radians(90), 0, 0)


def as_persp(cam, yaw, pitch, fov_deg):
    cd = cam.data
    cd.type = 'PERSP'
    cd.sensor_fit = 'HORIZONTAL'
    cd.angle = math.radians(fov_deg)
    d = Vector((math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def render_to(path, w, h, tries=3):
    """Render the scene camera to `path`; retries (e.g. a transient GPU out-of-memory on a shared GPU)."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    for k in range(tries):
        if os.path.exists(path):
            os.remove(path)
        try:
            bpy.ops.render.render(write_still=True)
        except RuntimeError as e:
            print(f'[render] attempt {k + 1} failed: {e}', flush=True)
        if os.path.exists(path):
            return
        time.sleep(5 * (k + 1))
    raise RuntimeError(f'render failed after {tries} attempts: {path}')


def set_wb(temperature, tint):
    vs = bpy.context.scene.view_settings
    vs.use_white_balance = True
    vs.white_balance_temperature = float(temperature)
    vs.white_balance_tint = float(tint)


def _read_exr(path):
    """{pass name: HxWxC float array} from a multilayer EXR (channels '<layer>.<pass>.<chan>')."""
    import numpy as np
    import OpenImageIO as oiio
    inp = oiio.ImageInput.open(path)
    spec = inp.spec()
    data = np.asarray(inp.read_image(0, 0, 0, spec.nchannels, oiio.FLOAT)).reshape(spec.height, spec.width, spec.nchannels)
    inp.close()
    out = {}
    for i, name in enumerate(spec.channelnames):
        parts = name.split('.')
        key = parts[-2] if len(parts) >= 2 else 'Combined'
        out.setdefault(key, []).append(i)
    return {k: data[:, :, idx] for k, idx in out.items()}


def _display_ratios(rgb, tmpdir):
    """Display-referred (R/G, B/G) of a scene-linear colour (scaled to mid grey) under the current
    view settings: rendered through Blender's own colour pipeline so it matches the final PNGs."""
    import numpy as np
    import OpenImageIO as oiio
    sc = bpy.context.scene
    img = bpy.data.images.get('_tg_wb') or bpy.data.images.new('_tg_wb', 4, 4, float_buffer=True, alpha=False)
    try:
        img.colorspace_settings.name = 'Linear Rec.709'
    except TypeError:
        pass
    c = np.asarray(rgb, dtype=np.float64)
    c = c * (0.30 / max(1e-6, float(c @ [0.2126, 0.7152, 0.0722])))
    img.pixels.foreach_set(np.tile(np.r_[c, 1.0], 16).astype(np.float32))
    st = sc.render.image_settings
    vs = sc.view_settings
    keep = (st.file_format, st.color_depth, vs.exposure)
    st.file_format, st.color_depth, vs.exposure = 'PNG', '16', 0.0
    path = os.path.join(tmpdir, '_tg_wb.png')
    img.save_render(path, scene=sc)
    st.file_format, st.color_depth, vs.exposure = keep
    inp = oiio.ImageInput.open(path)
    px = np.asarray(inp.read_image(0, 0, 0, 3, oiio.FLOAT)).reshape(-1, 3).mean(0)
    inp.close()
    return px[0] / px[1], px[2] / px[1]


def solve_wb(rgb, tmpdir):
    """(temperature, tint) that brings the scene-linear colour `rgb` (lit white paint) to WB_TARGET."""
    import math as m
    (t_lo, t_hi), (n_lo, n_hi) = WB_LIMITS
    t_rg, t_bg = WB_TARGET
    g_target = 2.0 / (t_rg + t_bg)                       # G / mean(R, B)
    T, tint = WB_DEFAULT

    def green(Tv, nv):
        set_wb(Tv, nv)
        rg, bg = _display_ratios(rgb, tmpdir)
        return 2.0 / (rg + bg), bg
    # direction of the tint axis (Blender: +tint = magenta compensation, but measure it)
    tint_up = green(T, n_hi)[0] < green(T, n_lo)[0]          # True: raising tint lowers green
    for _ in range(3):
        lo, hi = m.log(t_lo), m.log(t_hi)                    # higher temperature -> warmer image
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            if green(m.exp(mid), tint)[1] > t_bg:
                lo = mid
            else:
                hi = mid
        T = m.exp(0.5 * (lo + hi))
        lo, hi = n_lo, n_hi
        for _ in range(12):
            mid = 0.5 * (lo + hi)
            too_green = green(T, mid)[0] > g_target
            if too_green == tint_up:
                lo = mid
            else:
                hi = mid
        tint = 0.5 * (lo + hi)
    set_wb(T, tint)
    return T, tint


def white_masks(cam, points, tmpdir, w=512, h=256):
    """{key: HxW bool} of pixels showing white painted surfaces (WB_MATERIALS) from each eye point.
    Every material's surface is temporarily swapped for a flat emission (white for WB_MATERIALS,
    black otherwise) with lights and sky off: one shader swap for all points, then restored."""
    import numpy as np
    sc = bpy.context.scene
    swapped, hidden = [], []
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree:
            continue
        nt = m.node_tree
        out = nt.get_output_node('CYCLES')
        if out is None:
            continue
        sock = out.inputs['Surface']
        old = sock.links[0].from_socket if sock.is_linked else None
        disp = out.inputs.get('Displacement')
        old_disp = disp.links[0].from_socket if disp is not None and disp.is_linked else None
        if old_disp is not None:
            nt.links.remove(disp.links[0])
        em = nt.nodes.new('ShaderNodeEmission')
        v = 1.0 if m.name in WB_MATERIALS else 0.0
        em.inputs['Color'].default_value = (v, v, v, 1.0)
        em.inputs['Strength'].default_value = 1.0
        nt.links.new(em.outputs[0], sock)
        swapped.append((nt, em, sock, old, disp, old_disp))
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT' and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    world = sc.world
    keep_bg = []
    if world is not None:
        bgs = [n for n in world.node_tree.nodes if n.type == 'BACKGROUND'] if world.use_nodes else []
        keep_bg = [(n, n.inputs['Strength'].default_value) for n in bgs]
        for n in bgs:
            n.inputs['Strength'].default_value = 0.0
    st = sc.render.image_settings
    keep = (sc.cycles.samples, sc.cycles.use_denoising, st.file_format, sc.cycles.use_adaptive_sampling)
    sc.cycles.samples, sc.cycles.use_denoising, sc.cycles.use_adaptive_sampling = 2, False, False
    st.file_format = 'OPEN_EXR'
    masks = {}
    try:
        for key, loc in points.items():
            cam.location = loc
            as_pano(cam)
            path = os.path.join(tmpdir, f'_mask_{key}.exr')
            render_to(path, w, h)
            img = _read_exr(path)['Combined']
            os.remove(path)
            masks[key] = img[:, :, 1] > 0.5
    finally:
        for nt, em, sock, old, disp, old_disp in swapped:
            nt.nodes.remove(em)
            if old is not None:
                nt.links.new(old, sock)
            if old_disp is not None:
                nt.links.new(old_disp, disp)
        for ob in hidden:
            ob.hide_render = False
        if world is not None:
            for n, v in keep_bg:
                n.inputs['Strength'].default_value = v
        (sc.cycles.samples, sc.cycles.use_denoising, st.file_format, sc.cycles.use_adaptive_sampling) = keep
    return masks


def probe(cam, node_id, tmpdir, mask=None):
    """Low-sample probe render. Returns (exposure stops mapping the median luminance of the horizon
    band to TARGET_MEDIAN, white balance (temperature, tint) or None, info dict). `mask` (from
    white_masks) marks the white painted pixels the white balance is measured on."""
    import numpy as np
    sc = bpy.context.scene
    st = sc.render.image_settings
    keep = (sc.cycles.samples, st.file_format, sc.cycles.use_denoising, sc.view_settings.exposure)
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.view_settings.exposure = 0.0
    st.file_format = 'OPEN_EXR'
    path = os.path.join(tmpdir, f'_probe_{node_id}.exr')
    render_to(path, 512, 256)
    rgb = _read_exr(path)['Combined'][:, :, :3]
    os.remove(path)
    (sc.cycles.samples, st.file_format, sc.cycles.use_denoising, sc.view_settings.exposure) = keep
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    h = lum.shape[0]
    med = max(float(np.median(lum[int(h * 0.30):int(h * 0.62), ::2])), 1e-5)
    ev = max(-4.0, min(6.0, math.log2(TARGET_MEDIAN / med)))
    info = {'median': round(med, 5)}
    wb = None
    if mask is not None and mask.shape == lum.shape:
        m = mask & (lum > 1e-5)
        info['white_px'] = int(m.sum())
        if m.sum() >= 400:
            # per-pixel chromaticity, median over the typical (mid-luminance) white pixels: weighting by
            # pixel count, not brightness, keeps hot pools under downlights from steering the balance
            sel = lum[m]
            lo, hi = np.percentile(sel, [20, 85])
            use = m & (lum >= lo) & (lum <= hi)
            px = rgb[use]
            g = np.maximum(px[:, 1], 1e-6)
            chroma = np.array([np.median(px[:, 0] / g), 1.0, np.median(px[:, 2] / g)])
            info['white_rgb'] = [round(float(v), 4) for v in chroma]
            wb = solve_wb(chroma, tmpdir)
    return ev, wb, info


def auto_exposure(cam, node_id, tmpdir):
    """Exposure only (older callers)."""
    return probe(cam, node_id, tmpdir)[0]


def main():
    a = parse()
    os.makedirs(a.out, exist_ok=True)
    scene = json.load(open(os.path.join(DATA_DIR, 'scene.json')))
    nodes = scene['tour']['nodes']
    if a.nodes != 'all':
        want = a.nodes.split(',')
        nodes = [n for n in nodes if n['id'] in want]
    setup_cycles(a.samples)
    set_look(a.look)
    from bl import lighting
    lighting.apply_balance(a.interior_gain, a.sky_gain, a.sun_gain, a.emission_gain)
    fixed_wb = None
    if a.wb != 'auto':
        v = [float(x) for x in a.wb.split(',')]
        fixed_wb = (v[0], v[1] if len(v) > 1 else WB_DEFAULT[1])
    cam = make_camera()
    sc = bpy.context.scene
    masks = white_masks(cam, {n['id']: ft2bl(*n['p']) for n in nodes}, a.out) if fixed_wb is None else {}
    meta_path = os.path.join(a.out, 'render_meta.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for n in nodes:
        t0 = time.time()
        x, y, z = n['p']
        cam.location = ft2bl(x, y, z)
        as_pano(cam)
        sc.render.image_settings.file_format = 'PNG'
        ev, wb, info = probe(cam, n['id'], a.out, masks.get(n['id']))
        if a.exposure != 'auto':
            ev = float(a.exposure)
        wb = fixed_wb or WB_NODE.get(n['id']) or wb or WB_DEFAULT
        set_wb(*wb)
        sc.view_settings.exposure = ev
        sc.render.image_settings.file_format = 'PNG'
        if not a.preview_only:
            render_to(os.path.join(a.out, f'{n["id"]}.png'), a.width, a.width // 2)
        if a.preview or a.preview_only:
            yaw = a.yaw if a.yaw is not None else n['yaw']
            as_persp(cam, yaw, n.get('pitch', 0.0), a.fov)
            render_to(os.path.join(a.out, f'{n["id"]}_view.png'), a.preview_width, int(a.preview_width * 0.625))
            as_pano(cam)
        meta[n['id']] = {'exposure': ev, 'wb': [round(wb[0]), round(wb[1], 1)], 'probe': info,
                         'seconds': round(time.time() - t0, 1), 'width': a.width, 'samples': a.samples}
        json.dump(meta, open(meta_path, 'w'), indent=1)
        print(f'[render] {n["id"]} ev={ev:+.2f} wb={wb[0]:.0f}K/{wb[1]:+.1f} {time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
