"""Daylight, sky, window portals and interior light helpers (runs inside Blender).

Daylight: a Poly Haven CC0 pure-sky HDRI (fair-weather cumulus) for the visible sky, reflections and
sky fill, plus a sun lamp for the direct sun, late morning in Sunnyvale. The HDRI's own sun is clamped
out and the HDRI is rotated so its bright side matches the lamp. If the HDRI can't be fetched, a
physical (Nishita) sky without sun disc is used instead. The house's street side faces south (SCENE +z)
and the garden faces north, so a south-east sun rakes through the east living/kitchen windows and the
front rooms.

Room modules should create interior fixtures through `can()`, `pendant_light()`, `strip()`
so color temperature and intensity stay consistent across the house.
"""
import math

import bpy
from mathutils import Vector

from .common import FT, ft2bl

SUN_AZIMUTH_DEG = 128.0      # clockwise from north (SCENE -z); 90 = east, 180 = south
SUN_ELEVATION_DEG = 42.0
SUN_STRENGTH = 5.5           # W/m^2 (Blender sun units)
SUN_KELVIN = 5700            # late-morning sun; renders are auto-white-balanced per stop (render_panos)
SKY_STRENGTH = 1.0           # physical-sky fallback only
WARM_K = 3000
# Sky HDRI (exterior zone tuning). None -> physical sky. The sky fill is ~1/3 of the old physical sky so
# the sun reads as the key light (crisp shadows); the tint keeps sky-lit (north) rooms neutral under the
# pipeline's white balance instead of cyan.
SKY_HDRI = 'kloofendal_48d_partly_cloudy_puresky'
SKY_HDRI_RES = '4k'
SKY_HDRI_STRENGTH = 2.4
SKY_HDRI_TINT = (1.0, 1.0, 1.0)  # the HDRI's own sky colour (was bluish to suit a fixed 9000K white balance)
SKY_HDRI_CLAMP = 40.0        # radiance cap that removes the HDRI's own sun (the lamp is the only sun)


def kelvin_rgb(k):
    """Approximate linear RGB for a blackbody temperature (Tanner Helland fit, then linearized)."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    srgb = [min(max(v, 0), 255) / 255 for v in (r, g, b)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)


def sun_direction():
    """Unit vector (Blender) pointing from the scene toward the sun."""
    az, el = math.radians(SUN_AZIMUTH_DEG), math.radians(SUN_ELEVATION_DEG)
    # north = Blender +Y, east = +X
    return Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))


def _hdri_sun_rotation(path):
    """Mapping rotation (radians about Z) that puts the HDRI's brightest pixel (its sun) at the lamp's
    azimuth. Cached next to the HDRI as <file>.sun.json."""
    import json
    import os
    side = path + '.sun.json'
    u = None
    if os.path.exists(side):
        try:
            u = json.load(open(side))['u']
        except Exception:
            u = None
    if u is None:
        import numpy as np
        img = bpy.data.images.load(path, check_existing=True)
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        lum = px.reshape(h, w, 4)[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        iy, ix = np.unravel_index(int(np.argmax(lum)), lum.shape)
        u = (ix + 0.5) / w
        try:
            json.dump({'u': u, 'v': (iy + 0.5) / h}, open(side, 'w'))
        except OSError:
            pass
    # Blender equirect lookup: u = atan2(D.y, -D.x) / 2pi + 0.5 for world direction D
    a = (u - 0.5) * 2 * math.pi
    hdri_az = math.atan2(math.sin(a), -math.cos(a))
    d = sun_direction()
    return hdri_az - math.atan2(d.y, d.x)


def setup_daylight(ctx, hdri_path=None, hdri_rotation_deg=0.0):
    """World sky + sun lamp. Default sky: SKY_HDRI (see module doc). If hdri_path is given, use that
    equirect HDRI as-is (rotated by hdri_rotation_deg) instead."""
    auto_hdri = False
    if hdri_path is None and SKY_HDRI:
        try:
            from . import assets
            hdri_path = assets.hdri(SKY_HDRI, res=SKY_HDRI_RES)
            hdri_rotation_deg = math.degrees(_hdri_sun_rotation(hdri_path))
            auto_hdri = True
        except Exception as e:  # offline / download failure: physical sky
            print('[lighting] sky HDRI unavailable, using the physical sky:', e)
            hdri_path = None
    sc = bpy.context.scene
    world = bpy.data.worlds.get('TG World') or bpy.data.worlds.new('TG World')
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = SKY_STRENGTH
    d = sun_direction()
    if hdri_path:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Rotation'].default_value = (0, 0, math.radians(hdri_rotation_deg))
        env = nt.nodes.new('ShaderNodeTexEnvironment')
        env.image = bpy.data.images.load(hdri_path, check_existing=True)
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
        if auto_hdri:
            cl = nt.nodes.new('ShaderNodeVectorMath')
            cl.operation = 'MINIMUM'
            cl.inputs[1].default_value = (SKY_HDRI_CLAMP,) * 3
            tn = nt.nodes.new('ShaderNodeVectorMath')
            tn.operation = 'MULTIPLY'
            tn.inputs[1].default_value = SKY_HDRI_TINT
            nt.links.new(env.outputs['Color'], cl.inputs[0])
            nt.links.new(cl.outputs['Vector'], tn.inputs[0])
            nt.links.new(tn.outputs['Vector'], bg.inputs['Color'])
            bg.inputs['Strength'].default_value = SKY_HDRI_STRENGTH
        else:
            nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    else:
        sky = nt.nodes.new('ShaderNodeTexSky')
        for t in ('MULTIPLE_SCATTERING', 'NISHITA'):
            try:
                sky.sky_type = t
                break
            except TypeError:
                continue
        try:
            sky.sun_disc = False
        except AttributeError:
            pass
        sky.sun_elevation = math.radians(SUN_ELEVATION_DEG)
        # Nishita sun_rotation: angle about Z measured from +Y toward -X; we want the sky's
        # bright side to match the lamp, so derive from the direction vector.
        sky.sun_rotation = math.atan2(-d.x, d.y) % (2 * math.pi)
        try:
            sky.altitude = 30.0
            sky.air_density = 1.0
            sky.dust_density = 0.6
            sky.ozone_density = 1.0
        except AttributeError:
            pass
        nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    try:
        world.cycles_visibility.diffuse = True
    except AttributeError:
        pass

    sun_data = bpy.data.lights.get('TG Sun') or bpy.data.lights.new('TG Sun', 'SUN')
    sun_data.energy = SUN_STRENGTH
    sun_data.angle = math.radians(0.53)
    sun_data.color = kelvin_rgb(SUN_KELVIN)
    sun = bpy.data.objects.get('TG Sun') or bpy.data.objects.new('TG Sun', sun_data)
    if sun.name not in ctx.coll('lights').objects:
        ctx.coll('lights').objects.link(sun)
    sun.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return sun


def add_window_portals(ctx):
    """Cycles light portals over every exterior glass opening so interior sky light converges fast."""
    n = 0
    for ob in list(ctx.coll('openings').all_objects):
        if ob.type != 'MESH' or not ob.data.materials:
            continue
        mname = ob.data.materials[0].name
        if not mname.startswith('M_glass'):
            continue
        dims = ob.dimensions
        if max(dims) < 0.3:
            continue
        # thin axis of the pane = portal normal
        axis = min(range(3), key=lambda k: dims[k])
        if axis == 2:                       # horizontal glass (skylight): portal facing down
            size = (dims.x, dims.y)
            rot = (math.pi, 0, 0)
        elif axis == 0:                     # pane in Y-Z plane
            size = (dims.y, dims.z)
            rot = (0, math.pi / 2, 0)
        else:                               # pane in X-Z plane
            size = (dims.x, dims.z)
            rot = (math.pi / 2, 0, 0)
        ld = bpy.data.lights.new(f'portal {ob.name}'[:60], 'AREA')
        ld.shape = 'RECTANGLE'
        ld.size, ld.size_y = size
        try:
            ld.cycles.is_portal = True
        except AttributeError:
            ld.is_portal = True
        lo = bpy.data.objects.new(ld.name, ld)
        lo.matrix_world = ob.matrix_world.copy()
        lo.rotation_euler = (ob.rotation_euler.x + rot[0], ob.rotation_euler.y + rot[1], ob.rotation_euler.z + rot[2])
        lo.location = ob.matrix_world.translation
        ctx.coll('portals', 'lights').objects.link(lo)
        n += 1
    return n


def _emitter_material(name, kelvin, strength):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = kelvin_rgb(kelvin) + (1,)
    em.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def can(ctx, x, z, ceil=8.0, watts=10.0, kelvin=WARM_K, coll='lights_interior', diameter_in=4.0, beam_deg=75.0,
        lens_strength=18.0, parent='lights'):
    """Recessed 4in LED downlight at SCENE (x, ceil, z): flush trim + glowing lens + spot light.
    `parent` is the collection `coll` is created under the first time it is used."""
    ctx.coll(coll, parent)
    r = diameter_in / 24.0                   # radius in ft
    lens = ctx.cylinder(f'can lens {x:.1f},{z:.1f}', (x, ceil - 0.004, z), r * 0.78, 0.006, None, coll, verts=32)
    lens.data.materials.append(_emitter_material(f'E_can_{kelvin}_{lens_strength:g}', kelvin, lens_strength))
    trim = ctx.cylinder(f'can trim {x:.1f},{z:.1f}', (x, ceil - 0.003, z), r, 0.004, 'paint_trim', coll, verts=32)
    ld = bpy.data.lights.new(f'can {x:.1f},{z:.1f}', 'SPOT')
    ld.energy = watts
    ld.color = kelvin_rgb(kelvin)
    ld.spot_size = math.radians(beam_deg * 1.6)
    ld.spot_blend = 0.85
    ld.shadow_soft_size = r * 0.6 * FT
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(x, ceil - 0.05, z)          # spot points down its local -Z: default is straight down
    ctx.coll(coll).objects.link(lo)
    return lo


def point_light(ctx, x, y, z, watts=20.0, kelvin=2700, radius_ft=0.15, coll='lights_interior', name='lamp'):
    ld = bpy.data.lights.new(f'{name} {x:.1f},{z:.1f}', 'POINT')
    ld.energy = watts
    ld.color = kelvin_rgb(kelvin)
    ld.shadow_soft_size = radius_ft * FT
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(x, y, z)
    ctx.coll(coll).objects.link(lo)
    return lo


def emitter(name, kelvin=WARM_K, strength=12.0):
    """Emission material for LED strips, ring pendants, lamp diffusers, backlit mirrors."""
    return _emitter_material(f'E_{name}_{kelvin}_{strength:g}', kelvin, strength)


# ---------------------------------------------------------------------------------------------
# Render-time light balance (applied by render_panos / render_heroes / bake_web on a built .blend,
# so the daylight-vs-interior balance can be tuned without rebuilding the scene). Idempotent: the
# built values are remembered in custom properties and every call scales from those.
# Calibrated on the full house (K0/L0/H2/B2/P0): with the zones' fixture wattages as built, the
# fixtures supplied ~90% of the light on white walls even in daylit rooms (kitchen R/G 2.35 linear),
# i.e. a night-time look. Listing photos are daylight-led with the lights visibly on: daylight x2 and
# fixture lamps x0.12 give ~45-55% daylight in the kitchen and >80% in bedrooms, while the visible
# glowing parts (lenses, LED strips, shades, mirrors) keep a brighter x0.4 so the fixtures read 'on'.
INTERIOR_GAIN = 0.12     # fixture lamps' energy (spots, points, areas; not the sun, not portals)
EMISSION_GAIN = 0.4      # every emission shader (lenses, LED strips, shades, mirrors); None = INTERIOR_GAIN
SKY_GAIN = 2.0           # world background strength
SUN_GAIN = 2.0           # sun lamp strength


def _scale_emission(nt, gain, seen):
    if nt is None or nt.as_pointer() in seen:
        return 0
    seen.add(nt.as_pointer())
    n = 0
    for node in nt.nodes:
        if node.type == 'GROUP' and node.node_tree:
            n += _scale_emission(node.node_tree, gain, seen)
            continue
        if node.type == 'EMISSION':
            sock = node.inputs.get('Strength')
        elif node.type == 'BSDF_PRINCIPLED':
            sock = node.inputs.get('Emission Strength')
        else:
            continue
        if sock is None or sock.is_linked:
            continue
        key = f'tg_em0:{node.name}'
        if key not in nt:
            nt[key] = float(sock.default_value)
        sock.default_value = nt[key] * gain
        n += 1
    return n


def apply_balance(interior=None, sky=None, sun=None, emission=None):
    """Scale fixtures (lights + emission shaders), sky and sun relative to their built values."""
    interior = INTERIOR_GAIN if interior is None else interior
    emission = (EMISSION_GAIN if EMISSION_GAIN is not None else interior) if emission is None else emission
    sky = SKY_GAIN if sky is None else sky
    sun = SUN_GAIN if sun is None else sun
    nl = 0
    for ob in bpy.data.objects:
        if ob.type != 'LIGHT':
            continue
        ld = ob.data
        is_portal = getattr(getattr(ld, 'cycles', None), 'is_portal', False) or getattr(ld, 'is_portal', False)
        if is_portal:
            continue
        if 'tg_e0' not in ld:
            ld['tg_e0'] = float(ld.energy)
        ld.energy = ld['tg_e0'] * (sun if ld.type == 'SUN' else interior)
        nl += 1
    seen = set()
    ne = sum(_scale_emission(m.node_tree, emission, seen) for m in bpy.data.materials if m.use_nodes and m.node_tree)
    w = bpy.context.scene.world
    if w and w.use_nodes:
        for node in w.node_tree.nodes:
            if node.type == 'BACKGROUND':
                key = f'tg_bg0:{node.name}'
                if key not in w:
                    w[key] = float(node.inputs['Strength'].default_value)
                node.inputs['Strength'].default_value = w[key] * sky
    print(f'[balance] lights x{interior:g} ({nl}), emission x{emission:g} ({ne}), sky x{sky:g}, sun x{sun:g}', flush=True)
