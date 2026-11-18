"""Open-area vignette for the kitchen_dining zone: a low walnut sideboard under east window W07.

Why not a dining set: the open strip between the living room (z<14.5, fireplace ledge to z 16.9)
and the island stools (seat backs at z~21.0) is ~6.5 ft deep, so no table + chairs can keep the
36in circulation the brief asks for (and `layout_revision.kitchen_island.north_circulation` keeps
the island's north side open). A sideboard tight to the east wall stays out of every walking line
and gives the D0 / L2 views a calm, staged focal point under the window.

Sideboard: 41 x 18in, 27in high (top stays 3in under the 30in W07 sill), floating walnut case with
three flush doors and a recessed black finger-pull reveal, on two black steel sled frames.
Styling: cream ceramic table lamp with a linen drum shade (lit), two linen books with a small black
bowl, and a charcoal stoneware vase with olive branches.
"""
import math
import random

import bmesh
from mathutils import Vector

from .kitchen_dining_geo import Geo, P, principled, srgb

WALL_E = 40.61
WIN_C = 19.8142               # W07 centre (z 17.8142-21.8142, sill 2.5)
LEN = 3.4                     # along the wall (z): 41in
DEPTH = 1.5                   # x
X1 = WALL_E - 0.02            # back of the case (clear of the 40.55 baseboard: case floats above it)
X0 = X1 - DEPTH               # front face of the case frame
Z0, Z1 = WIN_C - 0.11 - LEN / 2, WIN_C - 0.11 + LEN / 2   # 18.0-21.4: >=0.44 ft to the kitchen run end
LEG_H = 0.50                  # steel sled height (6in of floor visible under the case)
TOP_Y = 2.25                  # 27in
PANEL = 0.06                  # 3/4in walnut panels
COLL = 'kd console'


def footprint():
    """Plan rectangle (x0, x1, z0, z1) for clearance checks."""
    return (X0, X1, Z0, Z1)


def build(ctx, g: Geo):
    col = g.sub(COLL)
    w = 'walnut_slab'
    # ---------------------------------------------------------------- case
    g.box('kd console top', X0, X1, TOP_Y - 0.10, TOP_Y, Z0, Z1, w, 0.012, coll=col)
    g.box('kd console side n', X0, X1, LEG_H, TOP_Y - 0.10, Z0, Z0 + PANEL, w, 0.006, coll=col)
    g.box('kd console side s', X0, X1, LEG_H, TOP_Y - 0.10, Z1 - PANEL, Z1, w, 0.006, coll=col)
    g.box('kd console bottom', X0, X1, LEG_H, LEG_H + PANEL, Z0 + PANEL, Z1 - PANEL, w, 0.006, coll=col)
    g.box('kd console back', X0 + 0.12, X1, LEG_H + PANEL, TOP_Y - 0.10, Z0 + PANEL, Z1 - PANEL, w, coll=col)
    # three flush doors, set 1/8in behind the frame face; reveal channel under the top
    dy0, dy1 = LEG_H + PANEL + 0.012, TOP_Y - 0.23
    dz0, dz1 = Z0 + PANEL + 0.012, Z1 - PANEL - 0.012
    n = 3
    step = (dz1 - dz0) / n
    for i in range(n):
        a, b = dz0 + i * step, dz0 + (i + 1) * step
        g.box(f'kd console door {i}', X0 + 0.01, X0 + 0.07, dy0, dy1, a + 0.006, b - 0.006, w, 0.006, coll=col)
    g.box('kd console pull reveal', X0 + 0.085, X0 + 0.10, dy1, TOP_Y - 0.10, Z0 + PANEL, Z1 - PANEL, 'black_metal', coll=col)
    g.box('kd console door backer', X0 + 0.07, X0 + 0.12, dy0, dy1, Z0 + PANEL, Z1 - PANEL, 'paint_black', coll=col)

    # ---------------------------------------------------------- steel sleds
    bar = 0.055
    for k, zc in enumerate((Z0 + 0.20, Z1 - 0.20)):
        za, zb = zc - bar / 2, zc + bar / 2
        fx0, fx1 = X0 + 0.10, X1 - 0.10            # back post at 40.49 < baseboard face 40.55
        g.box(f'kd console sled {k} foot', fx0, fx1, 0.0, bar, za, zb, 'black_metal', 0.008, coll=col)
        g.box(f'kd console sled {k} head', fx0, fx1, LEG_H - bar, LEG_H, za, zb, 'black_metal', 0.008, coll=col)
        for xx in (fx0, fx1 - bar):
            g.box(f'kd console sled {k} post', xx, xx + bar, bar, LEG_H - bar, za, zb, 'black_metal', 0.008, coll=col)
        # felt glides keep the foot bar visually seated
        g.box(f'kd console sled {k} glide', fx0 + 0.04, fx1 - 0.04, -0.0, 0.004, za + 0.005, zb - 0.005, 'paint_black', coll=col)

    # ------------------------------------------------------------- styling
    _styling(g, col)
    return {'sideboard': 1, 'footprint_xz': [round(v, 2) for v in footprint()]}


def _styling(g, col):
    y = TOP_Y
    # charcoal stoneware vase, south end, olive branches leaning into the room (away from the glass)
    vx, vz = X0 + 0.82, Z1 - 0.55
    char = principled('vase_charcoal_matte', srgb('#2f2e2c'), 0.68)
    k = 1.12
    prof = [(0.0, 0.0), (0.17, 0.0), (0.185, 0.015), (0.27, 0.16), (0.31, 0.36), (0.30, 0.55), (0.24, 0.78),
            (0.15, 0.96), (0.105, 1.07), (0.11, 1.12), (0.095, 1.125), (0.085, 1.08), (0.0, 1.06)]
    prof = [(r * k, h * k) for r, h in prof]
    g.lathe('kd console vase', prof, vx, vz, char, 72, col, y_base=y, sharp_deg=70)
    _olive(g, 'kd console olive', (vx, y + 1.06 * k, vz), col)
    _lamp(g, X0 + 0.80, Z0 + 0.62, y, col)
    # two linen-bound books with a small black ceramic bowl, between lamp and vase
    bx, bz = X0 + 0.60, Z0 + 1.62
    cover1 = principled('book_cream', srgb('#ddd5c6'), 0.8)
    cover2 = principled('book_sage', srgb('#8f9784'), 0.8)
    pages = principled('book_pages', srgb('#efe9dc'), 0.9)
    yb = y
    for k, (bw, bd, bh, rot, cov) in enumerate(((0.80, 0.62, 0.10, 0.08, cover2), (0.72, 0.55, 0.085, -0.05, cover1))):
        _book(g, f'kd console book {k}', bx, yb, bz, bw, bd, bh, rot, cov, pages, col)
        yb += bh
    g.lathe('kd console bowl', [(0.0, 0.0), (0.07, 0.0), (0.08, 0.01), (0.15, 0.05), (0.19, 0.11), (0.195, 0.125),
                                 (0.185, 0.127), (0.175, 0.11), (0.14, 0.06), (0.07, 0.025), (0.0, 0.022)],
            bx + 0.02, bz + 0.02, principled('bowl_black_glaze', srgb('#161616'), 0.35), 64, col, y_base=yb, sharp_deg=70)


def _book(g, name, x, y, z, w, d, h, rot, cover, pages, col):
    """Hardcover lying flat: cover boards + recessed page block, rotated `rot` about +Y."""
    parts = []
    t = 0.012
    ob = g.box(name + ' cover', -d / 2, d / 2, 0.0, h, -w / 2, w / 2, cover, 0.006, coll=col)
    parts.append(ob)
    pg = g.box(name + ' pages', -d / 2 + 0.02, d / 2 + 0.002, t, h - t, -w / 2 + 0.015, w / 2 - 0.015, pages, coll=col)
    parts.append(pg)
    for p in parts:
        p.location = Vector(P(x, y, z)) + p.location
        p.rotation_euler = (0, 0, rot)
    # box() builds meshes centred on their own origin, so rotating about the origin keeps them in place
    return parts


def _olive(g, name, base, col, seed=11):
    """Five olive branches: thin woody stems with narrow silver-green leaves (one merged mesh)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    stems = []
    # headings biased toward the room (-x) and along the wall (+-z): nothing reaches the glass
    heads = (180, 150, 210, 125, 240, 165, 195)
    for i, hd in enumerate(heads):
        phi = math.radians(hd + rnd.uniform(-10, 10))
        L = rnd.uniform(1.5, 2.3)
        sp = rnd.uniform(0.45, 1.0)
        pts = []
        for k in range(10):
            t = k / 9
            r = sp * (t ** 1.5)
            dy = -0.18 * L * max(t - 0.6, 0) ** 2
            pts.append((base[0] + r * math.cos(phi), base[1] + L * t + dy, base[2] + r * math.sin(phi)))
        stems.append(pts)
        nl = rnd.randint(38, 48)
        for j in range(nl):
            t = 0.22 + 0.78 * j / max(nl - 1, 1)
            k = min(int(t * 9), 8)
            f = t * 9 - k
            p = Vector(pts[k]).lerp(Vector(pts[k + 1]), f)
            tang = (Vector(pts[k + 1]) - Vector(pts[k])).normalized()
            side = tang.cross(Vector((0, 1, 0)))
            if side.length < 1e-3:
                side = Vector((1, 0, 0))
            side.normalize()
            ang = rnd.uniform(0, 2 * math.pi)
            side = (side * math.cos(ang) + tang.cross(side) * math.sin(ang)).normalized()
            Ll = rnd.uniform(0.18, 0.26) * (0.75 + 0.25 * (1 - t))  # 2-3in long
            Ww = Ll * 0.22
            axis = (tang * 0.75 + side * 0.65).normalized()        # leaves angle out from the stem
            nrm = axis.cross(side).normalized()
            if nrm.length < 1e-3:
                nrm = Vector((0, 1, 0))
            wdir = nrm.cross(axis).normalized()
            m = 10
            ring = []
            for q in range(m):
                a = 2 * math.pi * q / m
                u = 0.5 + 0.5 * math.cos(a)                          # 0..1 along the leaf
                v = math.sin(a) * math.sin(math.pi * u) ** 0.8
                pt = p + axis * (u * Ll) + wdir * (v * Ww * 0.5) + nrm * (0.02 * Ll * math.sin(math.pi * u))
                ring.append(bm.verts.new(P(*pt)))
            cv = bm.verts.new(P(*(p + axis * (0.5 * Ll) + nrm * 0.012 * Ll)))
            for q in range(m):
                bm.faces.new((cv, ring[q], ring[(q + 1) % m]))
    leaf = principled('olive_leaf', srgb('#6f7a5c'), 0.55, transl=srgb('#93a07a'))
    g.from_bmesh(name + ' leaves', bm, leaf, col, smooth=True)
    wood = principled('olive_twig', srgb('#5b5144'), 0.75)
    for i, pts in enumerate(stems):
        g.tube(f'{name} stem {i}', pts, 0.011, wood, col, res=4)


def _lamp(g, x, z, y, col):
    """Cream glazed ceramic gourd lamp (13in) with a 13in white linen drum shade, lit by a warm
    2700K bulb. Total height ~23in."""
    from ..lighting import kelvin_rgb  # noqa: F401  (keeps the lamp on the shared colour scale)
    glaze = principled('lamp_ceramic', srgb('#e9e2d4'), 0.3, coat=0.4)
    base = [(0.0, 0.0), (0.16, 0.0), (0.18, 0.02), (0.30, 0.18), (0.36, 0.40), (0.34, 0.62), (0.26, 0.82),
            (0.15, 0.98), (0.10, 1.04), (0.10, 1.08), (0.0, 1.08)]
    g.lathe('kd console lamp base', base, x, z, glaze, 72, col, y_base=y, sharp_deg=60)
    brass = 'black_metal'
    g.cyl('kd console lamp neck', x, y + 1.08, y + 1.30, z, 0.035, brass, 24, col)
    g.cyl('kd console lamp socket', x, y + 1.30, y + 1.42, z, 0.06, brass, 24, col)
    # drum shade: open thin-walled cylinder (inner + outer wall), bottom at ~3.6 ft
    R, sh0, sh1, t = 0.54, y + 1.20, y + 1.95, 0.01
    shade = _shade_material()
    import bmesh
    from .kitchen_dining_geo import P
    bm = bmesh.new()
    segs = 96
    rings = []
    for r, yy in ((R, sh0), (R, sh1), (R - t, sh1), (R - t, sh0)):
        rings.append([bm.verts.new(P(x + r * math.cos(2 * math.pi * k / segs), yy, z + r * math.sin(2 * math.pi * k / segs)))
                      for k in range(segs)])
    for i in range(4):
        A, B = rings[i], rings[(i + 1) % 4]
        for k in range(segs):
            k2 = (k + 1) % segs
            bm.faces.new((A[k], A[k2], B[k2], B[k]))
    g.from_bmesh('kd console lamp shade', bm, shade, col, smooth=True, sharp_deg=60)
    # slim spider: ring + 3 spokes to the socket (visible from above)
    for k in range(3):
        a = 2 * math.pi * k / 3
        g.cyl_axis('kd console lamp spider', (x + 0.06 * math.cos(a), y + 1.42, z + 0.06 * math.sin(a)),
                   (x + (R - 0.02) * math.cos(a), sh1 - 0.03, z + (R - 0.02) * math.sin(a)), 0.006, brass, 6, col)
    g.lathe('kd console lamp bulb', [(0.0, 0.0), (0.06, 0.02), (0.075, 0.09), (0.06, 0.16), (0.0, 0.18)], x, z,
            principled('lamp_bulb', srgb('#fff4e0'), 0.3, emission=srgb('#ffd9a8'), strength=6.0), 32, col, y_base=y + 1.42)
    g.point_light('kd console lamp light', x, y + 1.55, z, 26.0, 2700, 0.08, 'kd_lights')


def _shade_material():
    """Off-white linen drum shade that glows when the bulb is on: diffuse linen mixed 55/45 with a
    warm translucent layer (the shared principled() helper's 22% translucency reads as unlit)."""
    import bpy
    name = 'Z_kitchen_dining_lamp_shade_glow'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    df = nt.nodes.new('ShaderNodeBsdfPrincipled')
    df.inputs['Base Color'].default_value = srgb('#f1ece2') + (1,)
    df.inputs['Roughness'].default_value = 0.92
    try:
        df.inputs['Sheen Weight'].default_value = 0.3
    except KeyError:
        pass
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = srgb('#fff0d8') + (1,)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.45
    nt.links.new(df.outputs[0], mix.inputs[1])
    nt.links.new(tl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    m.diffuse_color = srgb('#f1ece2') + (1,)
    return m
