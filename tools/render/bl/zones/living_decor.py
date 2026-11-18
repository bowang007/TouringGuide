"""Living-zone decor: procedural abstract canvas, dried pampas (hair curves), fluted planter with a
Poly Haven tree, Poly Haven ceramic vases (runs inside Blender)."""
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

from ..common import CACHE_DIR, FT, move_to_collection, place
from . import living_geo as G

COLL = 'zone_living'


# ============================================================================ abstract art
def _bezier(p, n):
    p = np.asarray(p, float)
    t = np.linspace(0, 1, n)[:, None]
    if len(p) == 4:
        pts = ((1 - t) ** 3) * p[0] + 3 * ((1 - t) ** 2) * t * p[1] + 3 * (1 - t) * t * t * p[2] + t ** 3 * p[3]
    elif len(p) == 3:
        pts = ((1 - t) ** 2) * p[0] + 2 * (1 - t) * t * p[1] + t * t * p[2]
    else:
        pts = (1 - t) * p[0] + t * p[1]
    return pts


def _smooth1d(rng, n, k):
    a = rng.random(n + 2 * k)
    ker = np.hanning(2 * k + 1)
    ker /= ker.sum()
    return np.convolve(a, ker, mode='same')[k:k + n]


def _stroke(canvas, rng, ctrl, width, c1, c2, opacity=0.95, dry=0.4, taper=0.25, ragged=0.25, streak=1.0):
    """Stamp a bristle brush stroke along a bezier (pixel coords) onto canvas (H, W, 3) in place."""
    H, W, _ = canvas.shape
    pts = _bezier(ctrl, 400)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = seg.sum()
    n = max(8, int(L / max(2.0, width / 10)))
    pts = _bezier(ctrl, n)
    tang = np.gradient(pts, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    norm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    bristle = _smooth1d(rng, 512, 3) * 0.6 + _smooth1d(rng, 512, 12) * 0.4
    bristle = (bristle - bristle.min()) / (np.ptp(bristle) + 1e-9)
    tone = _smooth1d(rng, 512, 6)
    tone = (tone - tone.min()) / (np.ptp(tone) + 1e-9)
    edge_noise = _smooth1d(rng, n, 4)
    load_noise = _smooth1d(rng, n, 10)
    x0 = int(max(0, pts[:, 0].min() - width)); x1 = int(min(W, pts[:, 0].max() + width + 1))
    y0 = int(max(0, pts[:, 1].min() - width)); y1 = int(min(H, pts[:, 1].max() + width + 1))
    if x1 <= x0 or y1 <= y0:
        return
    A = np.zeros((y1 - y0, x1 - x0), np.float32)
    S = np.zeros_like(A)
    for i in range(n):
        t = i / (n - 1)
        wt = width * (1 - taper * (abs(2 * t - 1) ** 3)) * (0.9 + 0.2 * edge_noise[i])
        cx, cy = pts[i]
        bx0, bx1 = int(max(x0, cx - wt)), int(min(x1, cx + wt + 1))
        by0, by1 = int(max(y0, cy - wt)), int(min(y1, cy + wt + 1))
        if bx1 <= bx0 or by1 <= by0:
            continue
        yy, xx = np.mgrid[by0:by1, bx0:bx1]
        dx, dy = xx - cx, yy - cy
        s = (dx * norm[i, 0] + dy * norm[i, 1]) / (wt / 2)
        a = (dx * tang[i, 0] + dy * tang[i, 1])
        step = L / n
        inside = (np.abs(s) <= 1.0) & (np.abs(a) <= step * 1.2)
        si = np.clip(((s + 1) / 2 * 511).astype(int), 0, 511)
        load = 1.0 - dry * (t ** 1.6) - 0.25 * dry * load_noise[i]
        cov = np.clip((bristle[si] - (1 - load)) * 4.0, 0, 1) * streak + (1 - streak)
        edge = np.clip((1 - np.abs(s)) / (0.08 + ragged * 0.2 * rng.random()), 0, 1)
        cov = cov * edge * inside
        sub = A[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0]
        upd = cov > sub
        sub[upd] = cov[upd]
        Ssub = S[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0]
        Ssub[upd] = tone[si][upd]
    col = np.asarray(c1, np.float32)[None, None, :] * (1 - S[..., None]) + np.asarray(c2, np.float32)[None, None, :] * S[..., None]
    a = (A * opacity)[..., None]
    region = canvas[y0:y1, x0:x1]
    canvas[y0:y1, x0:x1] = region * (1 - a) + col * a


def make_art_image(path, W=2400, H=1440, seed=7):
    """Large contemporary abstract (neutral / ochre / charcoal) in the spirit of gestural
    real-estate staging art. Deterministic; written as an sRGB PNG."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.array([0.935, 0.92, 0.885], np.float32)
    low = (np.sin(xx / W * 3.1 + 0.7) * np.cos(yy / H * 2.3) * 0.012)[..., None]
    canvas = np.ones((H, W, 3), np.float32) * base + low
    P = lambda pts: [(x * W, y * H) for x, y in pts]  # noqa: E731
    char1, char2 = (0.13, 0.13, 0.14), (0.30, 0.30, 0.31)
    grey1, grey2 = (0.50, 0.50, 0.50), (0.68, 0.68, 0.67)
    ochre1, ochre2 = (0.74, 0.53, 0.15), (0.86, 0.69, 0.32)
    white1, white2 = (0.95, 0.94, 0.91), (0.87, 0.86, 0.83)
    # 1 broad pale-grey ground washes (most of the canvas gets some paint)
    _stroke(canvas, rng, P([(-0.05, 0.62), (0.25, 0.42), (0.62, 0.36), (1.05, 0.52)]), 0.42 * H, grey2, white2, 0.5, dry=0.3, streak=0.55)
    _stroke(canvas, rng, P([(-0.02, 0.86), (0.30, 0.74), (0.66, 0.80), (1.02, 0.74)]), 0.26 * H, grey2, white2, 0.42, dry=0.45, streak=0.6)
    _stroke(canvas, rng, P([(0.02, 0.22), (0.30, 0.12), (0.60, 0.16), (0.98, 0.10)]), 0.18 * H, white2, grey2, 0.35, dry=0.5, streak=0.6)
    # 2 the big charcoal gesture (a rising, breaking wave) built from overlapping passes
    _stroke(canvas, rng, P([(0.04, 0.80), (0.20, 0.30), (0.55, 0.20), (0.90, 0.46)]), 0.24 * H, char1, char2, 0.94, dry=0.5)
    _stroke(canvas, rng, P([(0.10, 0.84), (0.26, 0.42), (0.52, 0.34), (0.82, 0.55)]), 0.16 * H, char2, grey1, 0.88, dry=0.6)
    _stroke(canvas, rng, P([(0.16, 0.92), (0.40, 0.64), (0.70, 0.70), (0.96, 0.62)]), 0.15 * H, grey1, char2, 0.85, dry=0.65)
    # 3 knock-back whites carving the mass
    _stroke(canvas, rng, P([(0.20, 0.60), (0.40, 0.48), (0.60, 0.55), (0.84, 0.50)]), 0.10 * H, white1, white2, 0.9, dry=0.45)
    _stroke(canvas, rng, P([(0.50, 0.17), (0.64, 0.12), (0.82, 0.20)]), 0.07 * H, white1, white2, 0.8, dry=0.6)
    _stroke(canvas, rng, P([(0.05, 0.50), (0.12, 0.44), (0.20, 0.47)]), 0.06 * H, white1, white2, 0.8, dry=0.5)
    # 4 ochre band: horizontal glaze + short vertical dabs (gilded rhythm)
    _stroke(canvas, rng, P([(0.36, 0.46), (0.52, 0.43), (0.68, 0.45), (0.86, 0.43)]), 0.07 * H, ochre1, ochre2, 0.92, dry=0.4)
    for k in range(34):
        x = 0.38 + 0.47 * k / 33 + rng.uniform(-0.006, 0.006)
        y = 0.44 + rng.uniform(-0.02, 0.012)
        h = rng.uniform(0.05, 0.16)
        _stroke(canvas, rng, P([(x, y - h * 0.35), (x + rng.uniform(-0.005, 0.005), y + h * 0.65)]),
                rng.uniform(0.012, 0.024) * W, ochre1, ochre2, 0.95, dry=0.3, taper=0.5)
    _stroke(canvas, rng, P([(0.04, 0.70), (0.10, 0.66), (0.16, 0.69)]), 0.05 * H, ochre2, ochre1, 0.6, dry=0.5)
    # 5 slate and rust accents
    _stroke(canvas, rng, P([(0.86, 0.26), (0.89, 0.36), (0.905, 0.48)]), 0.07 * H, (0.25, 0.32, 0.42), (0.34, 0.42, 0.52), 0.92, dry=0.3)
    _stroke(canvas, rng, P([(0.15, 0.58), (0.19, 0.62)]), 0.045 * H, (0.52, 0.27, 0.15), (0.60, 0.35, 0.22), 0.9, dry=0.2)
    # 6 black calligraphic lines
    _stroke(canvas, rng, P([(0.05, 0.30), (0.17, 0.17), (0.30, 0.26), (0.42, 0.16)]), 0.018 * H, (0.04, 0.04, 0.04), (0.12, 0.12, 0.12), 0.95, dry=0.25, taper=0.6, streak=0.4)
    _stroke(canvas, rng, P([(0.50, 0.86), (0.66, 0.93), (0.79, 0.84), (0.94, 0.87)]), 0.016 * H, (0.04, 0.04, 0.04), (0.12, 0.12, 0.12), 0.95, dry=0.3, taper=0.6, streak=0.4)
    _stroke(canvas, rng, P([(0.92, 0.14), (0.935, 0.40), (0.915, 0.66)]), 0.014 * H, (0.04, 0.04, 0.04), (0.12, 0.12, 0.12), 0.9, dry=0.4, taper=0.7, streak=0.4)
    _stroke(canvas, rng, P([(0.30, 0.70), (0.36, 0.60), (0.45, 0.62)]), 0.03 * H, (0.06, 0.06, 0.06), (0.15, 0.15, 0.15), 0.9, dry=0.5, taper=0.5)
    # 7 a few spatters
    for k in range(60):
        cx, cy = rng.uniform(0.1, 0.9) * W, rng.uniform(0.15, 0.85) * H
        r = rng.uniform(1.5, 5.0)
        m = ((xx - cx) ** 2 + (yy - cy) ** 2) < r * r
        c = np.array(char1 if rng.random() < 0.7 else ochre1, np.float32)
        canvas[m] = canvas[m] * 0.2 + c * 0.8
    # canvas weave
    weave = (np.sin(xx * 1.9) * np.sin(yy * 1.9) * 0.012 + rng.normal(0, 0.006, (H, W)))[..., None]
    canvas = np.clip(canvas + weave, 0, 1)
    img8 = (canvas * 255 + 0.5).astype(np.uint8)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = bpy.data.images.new('tmp_art', W, H, alpha=False)
    rgba = np.concatenate([img8[::-1].astype(np.float32) / 255.0, np.ones((H, W, 1), np.float32)], axis=2)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    return path


def art_material(path):
    name = 'Z_living_art_canvas'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.interpolation = 'Cubic'
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.62
    # paint relief from luminance contrast
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(tex.outputs['Color'], bw.inputs[0])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.08
    bump.inputs['Distance'].default_value = 0.0005
    nt.links.new(bw.outputs[0], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (0.8, 0.78, 0.74, 1)
    return m


def wall_art(ctx, wall_x, z0, z1, y0, y1, depth=0.13):
    """Gallery-wrapped canvas on a west wall (face at wall_x, art faces +x) in a thin black floater."""
    path = os.path.join(CACHE_DIR, 'living', 'art_living_abstract_02.png')
    if not os.path.exists(path):
        make_art_image(path)
    gesso = bpy.data.materials.get('Z_living_gesso') or bpy.data.materials.new('Z_living_gesso')
    gesso.use_nodes = True
    gb = gesso.node_tree.nodes.get('Principled BSDF')
    gb.inputs['Base Color'].default_value = (0.86, 0.85, 0.82, 1)
    gb.inputs['Roughness'].default_value = 0.8
    cx0, cx1 = wall_x + 0.02, wall_x + 0.02 + depth
    v, f = G.box_verts(cx0, cx1, y0, y1, z0, z1)
    # viewer faces west: image left = south (z1), right = north (z0)
    uvs = [(1, 0), (1, 0), (1, 1), (1, 1), (0, 0), (0, 0), (0, 1), (0, 1)]
    ob = G.obj(ctx, 'living art canvas', v, f, [gesso, art_material(path)], COLL, smooth=False, uvs=uvs)
    for poly in ob.data.polygons:
        c = poly.center
        if abs(c.x - cx1 * FT) < 1e-4:
            poly.material_index = 1
    G.bevel(ob, 0.008, 2)
    # floater frame
    gap, fw, lip = 0.035, 0.05, 0.02
    fx0, fx1 = wall_x + 0.005, cx1 + lip
    parts = [G.box_verts(fx0, fx1, y0 - gap - fw, y0 - gap, z0 - gap - fw, z1 + gap + fw),
             G.box_verts(fx0, fx1, y1 + gap, y1 + gap + fw, z0 - gap - fw, z1 + gap + fw),
             G.box_verts(fx0, fx1, y0 - gap, y1 + gap, z0 - gap - fw, z0 - gap),
             G.box_verts(fx0, fx1, y0 - gap, y1 + gap, z1 + gap, z1 + gap + fw),
             G.box_verts(fx0, fx0 + 0.02, y0 - gap, y1 + gap, z0 - gap, z1 + gap)]   # floater tray
    v, f = G.merge(*parts)
    fo = G.obj(ctx, 'living art floater frame', v, f, 'paint_black', COLL, smooth=False)
    G.bevel(fo, 0.004, 1)
    return [ob, fo]


# ================================================================================ pampas
def pampas(ctx, base, n_stems=8, seed=3, height=(2.2, 2.9), spread=(6, 28), plume_frac=0.45, fibers=5200):
    """Dried pampas stems with fluffy plumes as hair curves. base = (x, y, z) SCENE feet of the
    vase mouth centre. Returns the curves objects."""
    rng = np.random.default_rng(seed)
    fib_pts, stem_pts = [], []
    # fan toward the room (SCENE -x) and along the wall; keep clear of the wall behind (+x)
    azs = np.linspace(math.radians(80), math.radians(280), n_stems) + rng.uniform(-0.12, 0.12, n_stems)
    for s in range(n_stems):
        az = azs[s]
        tilt = math.radians(rng.uniform(*spread))
        Ls = rng.uniform(*height)
        b = np.array([base[0] + 0.04 * math.cos(az + 1), base[1] - 0.7, base[2] + 0.04 * math.sin(az + 1)])
        hor = np.array([math.cos(az), 0, math.sin(az)])
        npts = 16
        sp = []
        for i in range(npts):
            t = i / (npts - 1)
            L = (Ls + 0.7) * t
            p = b + np.array([0, 1, 0]) * L * math.cos(tilt) + hor * L * math.sin(tilt) * (0.6 + 0.6 * t)
            p[1] -= 0.12 * (t ** 3) * Ls * math.sin(tilt) * 2
            sp.append(p)
        sp = np.array(sp)
        stem_pts.append(sp)
        # plume fibres
        T0 = 1 - plume_frac
        nf = int(fibers * rng.uniform(0.8, 1.15))
        ts = T0 + plume_frac * rng.random(nf) ** 0.85
        for t in ts:
            fi = t * (npts - 1)
            i0 = min(int(fi), npts - 2)
            fr = fi - i0
            S = sp[i0] * (1 - fr) + sp[i0 + 1] * fr
            Tg = sp[i0 + 1] - sp[i0]
            Tg /= np.linalg.norm(Tg)
            a = np.cross(Tg, [0, 0, 1.0])
            if np.linalg.norm(a) < 1e-4:
                a = np.cross(Tg, [1.0, 0, 0])
            a /= np.linalg.norm(a)
            bb = np.cross(Tg, a)
            psi = rng.uniform(0, 2 * np.pi)
            R = math.cos(psi) * a + math.sin(psi) * bb
            beta = math.radians(rng.uniform(22, 62))
            d = Tg * math.cos(beta) + R * math.sin(beta)
            u = (t - T0) / plume_frac
            env = math.sin(math.pi * (0.12 + 0.8 * u)) ** 0.7 * (1 - 0.35 * u)
            ln = 0.46 * env * rng.uniform(0.5, 1.1) + 0.04
            pts = [S]
            dd = d.copy()
            for k in range(1, 4):
                dd = dd + np.array([0, -0.12, 0]) + rng.normal(0, 0.1, 3)
                dd /= np.linalg.norm(dd)
                pts.append(pts[-1] + dd * ln / 3)
            fib_pts.append(pts)
    objs = []
    # fibres
    fib = np.array(fib_pts)                        # (N, 4, 3) SCENE ft
    N = fib.shape[0]
    hc = bpy.data.hair_curves.new('living pampas plumes')
    hc.add_curves([4] * N)
    bl = np.stack([fib[..., 0] * FT, -fib[..., 2] * FT, fib[..., 1] * FT], -1).astype(np.float32)
    hc.position_data.foreach_set('vector', bl.ravel())
    rad = hc.attributes.new('radius', 'FLOAT', 'POINT')
    rr = np.tile(np.array([0.0007, 0.0006, 0.00045, 0.00025], np.float32), N)
    rad.data.foreach_set('value', rr)
    hc.materials.append(_pampas_material())
    o = bpy.data.objects.new('living pampas plumes', hc)
    ctx.coll(COLL).objects.link(o)
    objs.append(o)
    # stems
    ns = len(stem_pts)
    hs = bpy.data.hair_curves.new('living pampas stems')
    hs.add_curves([stem_pts[0].shape[0]] * ns)
    st = np.array(stem_pts)
    bl = np.stack([st[..., 0] * FT, -st[..., 2] * FT, st[..., 1] * FT], -1).astype(np.float32)
    hs.position_data.foreach_set('vector', bl.ravel())
    rad = hs.attributes.new('radius', 'FLOAT', 'POINT')
    rr = np.tile(np.linspace(0.0028, 0.0016, st.shape[1]).astype(np.float32), ns)
    rad.data.foreach_set('value', rr)
    hs.materials.append(_stem_material())
    o = bpy.data.objects.new('living pampas stems', hs)
    ctx.coll(COLL).objects.link(o)
    objs.append(o)
    return objs


def _pampas_material():
    name = 'Z_living_pampas'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    h = nt.nodes.new('ShaderNodeBsdfHairPrincipled')
    try:
        h.parametrization = 'COLOR'
    except Exception:
        pass
    for k, val in (('Color', (0.80, 0.66, 0.46, 1)), ('Roughness', 0.55), ('Radial Roughness', 0.85),
                   ('Coat', 0.0), ('Random Color', 0.15), ('Random Roughness', 0.2)):
        if k in h.inputs:
            h.inputs[k].default_value = val
    nt.links.new(h.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (0.8, 0.7, 0.55, 1)
    return m


def _stem_material():
    name = 'Z_living_pampas_stem'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (0.62, 0.52, 0.36, 1)
    b.inputs['Roughness'].default_value = 0.6
    return m


# ========================================================================= imported models
def import_model(ctx, asset_id, keep=None, res='2k'):
    """Import a Poly Haven model, optionally keeping only mesh objects whose name contains `keep`.
    Bakes transforms into mesh data (identity object matrices) and returns the kept objects."""
    from .. import assets
    path = assets.model(asset_id, res=res)
    before = set(bpy.data.objects)
    ctx.link_asset(path)
    new = [o for o in bpy.data.objects if o not in before]
    kept = []
    for o in new:
        if o.type != 'MESH' or (keep and not any(k in o.name for k in keep)):
            continue
        kept.append(o)
    for o in kept:
        mw = o.matrix_world.copy()
        o.parent = None
        o.data = o.data.copy() if o.data.users > 1 else o.data
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o not in kept:
            bpy.data.objects.remove(o, do_unlink=True)
    move_to_collection(kept, ctx.coll(COLL))
    return kept


def _bounds(objs):
    pts = []
    for o in objs:
        pts.extend(o.matrix_world @ Vector(c) for c in o.bound_box)
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def place_model(ctx, objs, name, x, y, z, rot=0.0, scale=1.0, pivot=None):
    """Group imported objects under an Empty whose origin is `pivot` (Blender coords; default:
    bottom centre of the bounds) and place that origin at SCENE (x, y, z)."""
    mn, mx = _bounds(objs)
    if pivot is None:
        pivot = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in objs:
        o.data.transform(Matrix.Translation(-pivot))
    e = G.group(ctx, name)
    for o in objs:
        o.parent = e
    e.scale = (scale, scale, scale)
    place(e, x, y, z, rot)
    return e


def vase(ctx, asset_id, x, y, z, height_ft, rot=0.0, recolor=None):
    objs = import_model(ctx, asset_id)
    mn, mx = _bounds(objs)
    s = height_ft * FT / (mx.z - mn.z)
    if recolor is not None:
        for o in objs:
            for i, m in enumerate(o.data.materials):
                m2 = m.copy()
                m2.name = f'Z_living_{asset_id}_glaze'
                b = next((n for n in m2.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if b is not None:
                    for l in list(b.inputs['Base Color'].links):
                        m2.node_tree.links.remove(l)
                    b.inputs['Base Color'].default_value = recolor + (1,)
                    b.inputs['Roughness'].default_value = 0.25
                o.data.materials[i] = m2
    e = place_model(ctx, objs, f'living vase {asset_id}', x, y, z, rot, s)
    top = y + height_ft
    return e, top, objs


# ================================================================================ planter
def planter_material():
    name = 'Z_living_planter'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 140.0
    n.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.60, 0.58, 0.54, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.80, 0.78, 0.74, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.78
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    bump.inputs['Distance'].default_value = 0.0008
    nt.links.new(n.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (0.75, 0.73, 0.69, 1)
    return m


def planter_with_tree(ctx, x, z, base_y=0.0, rot=0.0, tree_h_ft=5.2, r_top=0.68, r_bot=0.54, h=1.45):
    """Fluted stoneware planter with a Poly Haven pachira (money tree) planted in it."""
    out = []
    flutes = 22

    def flute(th, r, y):
        if r > r_bot - 0.02 and base_y + 0.06 < y < base_y + h - 0.06:
            return r + 0.022 * abs(math.cos(flutes * th / 2)) ** 0.6
        return r
    prof = [(0.0, base_y), (r_bot - 0.03, base_y), (r_bot, base_y + 0.03)]
    for k in range(1, 12):
        t = k / 12
        prof.append((r_bot + (r_top - r_bot) * t, base_y + 0.03 + (h - 0.06) * t))
    prof += [(r_top, base_y + h - 0.02), (r_top - 0.02, base_y + h), (r_top - 0.07, base_y + h),
             (r_top - 0.08, base_y + h - 0.03), (r_top - 0.085, base_y + h - 0.16), (0.0, base_y + h - 0.16)]
    v, f = G.lathe(prof, n=flutes * 6, cap_bottom=False, mod=flute)
    e = G.group(ctx, 'living planter')
    po = G.obj(ctx, 'living planter body', v, f, planter_material(), COLL, e)
    out.append(po)
    soil_y = base_y + h - 0.16
    v, f = G.lathe([(0.0, soil_y + 0.005), (r_top - 0.085, soil_y + 0.005), (r_top - 0.085, soil_y + 0.03),
                    (0.0, soil_y + 0.045)], n=48, cap_bottom=False)
    out.append(G.obj(ctx, 'living planter soil', v, f, 'soil_mulch', COLL, e))
    place(e, x, 0, z, 0)
    # tree
    objs = import_model(ctx, 'pachira_aquatica_01', keep=('_d',))
    bark = [o for o in objs if 'bark' in o.name]
    # trunk base = centre of the lowest bark vertices
    low = []
    for o in bark:
        zs = [vv.co.z for vv in o.data.vertices]
        zmin = min(zs)
        low += [vv.co for vv in o.data.vertices if vv.co.z < zmin + 0.03]
    piv = Vector((sum(p.x for p in low) / len(low), sum(p.y for p in low) / len(low), min(p.z for p in low)))
    mn, mx = _bounds(objs)
    s = tree_h_ft * FT / (mx.z - piv.z)
    te = place_model(ctx, objs, 'living tree', x, soil_y - 0.12, z, rot, s, pivot=piv)
    return out, te, soil_y
