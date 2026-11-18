"""Parked cars for the neighbourhood context (runs inside Blender).

A generic modern compact crossover / sedan built from side profiles: a lower body extruded across the
width with real wheel arches cut into it, a tapered greenhouse with dark glazing set into body-coloured
pillars, rounded by a bevel modifier, plus tyres with alloy faces, lamps, grille, mirrors and plates.
One mesh per (style, colour) is built and shared by every parked copy. Seen from 60-120 ft only.
All dimensions are SCENE feet; the car is modelled along +x (front at x=0) and centred on z=0.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from ..common import FT, ft2bl
from .exterior_util import _srgb, coll, flat_mat

# side profiles (x from the front bumper, y above ground), lower body bottom edge without the arches
STYLES = {
    # compact crossover: 15.2 ft long, 6.1 ft wide, 5.4 ft tall
    'suv': dict(L=15.2, W=6.1, wb=(3.0, 11.9), R=1.18, clear=0.62,
                lower=[(0.0, 1.05), (0.05, 2.35), (0.35, 2.85), (3.3, 3.25), (12.6, 3.45), (14.75, 3.55),
                       (15.12, 3.25), (15.25, 2.4), (15.2, 1.0)],
                belt=3.3, green=[(3.4, 3.27), (6.0, 5.02), (13.25, 5.2), (14.7, 3.56)],
                wg=(5.55, 4.75)),
    # mid-size sedan: 15.8 ft long, 6.0 ft wide, 4.7 ft tall
    'sedan': dict(L=15.8, W=6.0, wb=(3.1, 12.6), R=1.1, clear=0.5,
                  lower=[(0.0, 0.9), (0.05, 2.1), (0.4, 2.55), (4.0, 2.95), (12.4, 3.1), (15.3, 3.3),
                         (15.8, 2.9), (15.75, 0.9)],
                  belt=3.0, green=[(4.2, 2.98), (7.1, 4.6), (11.4, 4.62), (14.0, 3.15)],
                  wg=(5.5, 4.4)),
}

PAINTS = {
    'white': ('#e9e9e6', 0.0, 0.32),
    'silver': ('#a9adb1', 0.85, 0.38),
    'grey': ('#55595d', 0.7, 0.36),
    'black': ('#16181a', 0.6, 0.3),
    'red': ('#7a1418', 0.35, 0.3),
    'blue': ('#25384f', 0.6, 0.32),
}


def paint_mat(key):
    name = f'Z_exterior_car_paint_{key}'
    m = bpy.data.materials.get(name)
    if m:
        return m
    hexcol, metal, rough = PAINTS[key]
    m = flat_mat(name, hexcol, rough, metal, spec=0.5)
    b = m.node_tree.nodes.get('Principled BSDF')
    for k, v in (('Coat Weight', 1.0), ('Coat Roughness', 0.04)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


def _mats():
    return {
        'glass': flat_mat('Z_exterior_car_glass', '#0b0e10', 0.03, 0.0, spec=1.0),
        'trim': flat_mat('Z_exterior_car_trim', '#121314', 0.45, 0.0, spec=0.4),
        'tyre': flat_mat('Z_exterior_car_tyre', '#1a1a1b', 0.85, 0.0, spec=0.3),
        'rim': flat_mat('Z_exterior_car_rim', '#8d9093', 0.3, 1.0),
        'well': flat_mat('Z_exterior_car_well', '#070707', 0.9),
        'head': flat_mat('Z_exterior_car_headlamp', '#c9ccce', 0.08, 0.6, spec=1.0),
        'tail': flat_mat('Z_exterior_car_taillamp', '#5a0b0d', 0.12, 0.0, spec=0.9),
        'plate': flat_mat('Z_exterior_car_plate', '#e8e8e2', 0.4),
    }


def _arched_bottom(S):
    """Bottom edge (rear -> front) with semicircular wheel arches cut in."""
    clear, R = S['clear'], S['R'] + 0.14
    yc = S['R']
    pts = []
    for xw in sorted(S['wb'], reverse=True):
        dx = math.sqrt(max(R * R - (clear - yc) ** 2, 0.0))
        seg = []
        a0 = math.atan2(clear - yc, dx)
        a1 = math.pi - a0
        for i in range(13):
            a = a0 + (a1 - a0) * i / 12
            seg.append((xw + R * math.cos(a), yc + R * math.sin(a)))
        pts += seg
    return pts


def _lower_body(S):
    """Profile polygon: front-bottom -> up the nose -> along the top -> rear -> bottom with arches."""
    top = S['lower']
    poly = [(top[0][0], S['clear'] + 0.2)] + top + [(top[-1][0], S['clear'] + 0.15)]
    poly += _arched_bottom(S)
    return poly


def _extrude(bm, poly, w0, w1, mat_side=0):
    """Prism from an x/y polygon between z = w0 .. w1 (car frame: x along, y up, z across)."""
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly)))
    if area < 0:                                   # make it counter-clockwise -> outward normals
        poly = poly[::-1]
    a = [bm.verts.new((x, y, w0)) for x, y in poly]
    b = [bm.verts.new((x, y, w1)) for x, y in poly]
    n = len(poly)
    faces = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    for f in faces:
        f.material_index = mat_side
    return faces


def _greenhouse(bm, S, mi_glass, mi_body):
    """Tapered greenhouse (narrower at the roof). Side windows are a dark inset band on the
    body-coloured side; windshield and backlight are glass faces; the roof is body colour."""
    g = S['green']
    wb, wt = S['wg']
    y0, y1 = S['belt'] - 0.02, max(p[1] for p in g)

    def hw(y):
        t = (y - y0) / (y1 - y0)
        return (wb + (wt - wb) * max(0.0, min(1.0, t))) / 2

    # g runs clockwise in (x, y): front belt -> windshield top -> roof rear -> rear belt
    L_ = [bm.verts.new((x, y, -hw(y))) for x, y in g]
    R_ = [bm.verts.new((x, y, hw(y))) for x, y in g]
    n = len(g)
    fL = bm.faces.new(L_)
    fR = bm.faces.new(R_[::-1])
    fL.material_index = fR.material_index = mi_body
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((L_[i], R_[i], R_[j], L_[j]))
        # 0: windshield (front slope), 1: roof, 2: backlight, 3: belt (hidden)
        f.material_index = mi_glass if i in (0, 2) else mi_body
    return hw


def _side_glass(bm, S, hw, mi_glass):
    """Daylight opening on both sides: the greenhouse side polygon inset by the pillar widths,
    pushed just outside the side surface."""
    g = S['green']
    (xa, ya), (xb, yb), (xc, yc), (xd, yd) = g
    yf0, yr0, yt = ya + 0.1, yd + 0.07, min(yb, yc) - 0.2   # DLO follows the rising belt line

    def x_on(p, q, y):
        t = (y - p[1]) / (q[1] - p[1])
        return p[0] + (q[0] - p[0]) * t
    f0, f1 = x_on((xa, ya), (xb, yb), yf0) + 0.32, x_on((xa, ya), (xb, yb), yt) + 0.22
    r0, r1 = x_on((xd, yd), (xc, yc), yr0) - 0.75, x_on((xd, yd), (xc, yc), yt) - 0.55
    quad = [(f0, yf0), (r0, yr0), (r1, yt), (f1, yt)]
    for s in (-1, 1):
        vs = [bm.verts.new((x, y, s * (hw(y) + 0.012))) for x, y in quad]
        f = bm.faces.new(vs if s > 0 else vs[::-1])
        f.material_index = mi_glass


def _box(bm, x0, x1, y0, y1, z0, z1, mi):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = Vector((x0 + (x1 - x0) * (v.co.x + 0.5), y0 + (y1 - y0) * (v.co.y + 0.5),
                       z0 + (z1 - z0) * (v.co.z + 0.5)))
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mi


def _wheel(bm, xc, yc, zc, R, w, side, mi_tyre, mi_rim, seg=28):
    """Tyre (cylinder along z) with a recessed alloy face on the outer side."""
    def ring(r, z):
        return [bm.verts.new((xc + r * math.cos(2 * math.pi * i / seg), yc + r * math.sin(2 * math.pi * i / seg), z))
                for i in range(seg)]
    zi, zo = zc - side * w / 2, zc + side * w / 2
    ti, to = ring(R, zi), ring(R, zo)
    lip_i = ring(R * 0.93, zo + side * 0.02)
    rim = ring(R * 0.66, zo - side * 0.03)
    hub = bm.verts.new((xc, yc, zo - side * 0.05))
    back = bm.verts.new((xc, yc, zi))
    faces = []
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((bm.faces.new((ti[i], ti[j], to[j], to[i])), mi_tyre))          # tread
        faces.append((bm.faces.new((to[i], to[j], lip_i[j], lip_i[i])), mi_tyre))    # sidewall
        faces.append((bm.faces.new((lip_i[i], lip_i[j], rim[j], rim[i])), mi_tyre))  # sidewall to rim
        faces.append((bm.faces.new((rim[i], rim[j], hub)), mi_rim))                  # alloy face
        faces.append((bm.faces.new((ti[j], ti[i], back)), mi_tyre))
    for f, mi in faces:
        f.material_index = mi


def _wz(S, x):
    """Half-width of the lower body at x: full width amidships, rounded in plan toward both bumpers."""
    L_ = S['L']
    t = max(0.0, min(1.0, x / 1.8, (L_ - x) / 1.5))
    return S['W'] / 2 * (0.84 + 0.16 * (1 - (1 - t) ** 2))


def _arch_flares(bm, S, mi):
    """Black wheel-arch mouldings: an arc band around each arch, just proud of the body side."""
    R0, R1 = S['R'] + 0.12, S['R'] + 0.36
    yc = S['R']
    for xw in S['wb']:
        a0 = math.asin(max(-1.0, min(1.0, (S['clear'] - yc) / R0)))
        for s in (-1, 1):
            z = s * (_wz(S, xw) + 0.03)
            pts = []
            for i in range(15):
                a = a0 + (math.pi - 2 * a0) * i / 14
                pts.append((bm.verts.new((xw + R0 * math.cos(a), yc + R0 * math.sin(a), z)),
                            bm.verts.new((xw + R1 * math.cos(a), yc + R1 * math.sin(a), z))))
            for (p0, p1), (q0, q1) in zip(pts[:-1], pts[1:]):
                f = bm.faces.new((p0, q0, q1, p1) if s > 0 else (p1, q1, q0, p0))
                f.material_index = mi


def car_mesh(style='suv', paint='silver'):
    name = f'ext car {style} {paint}'
    me = bpy.data.meshes.get(name)
    if me:
        return me
    S = STYLES[style]
    M = _mats()
    slots = [paint_mat(paint), M['glass'], M['trim'], M['tyre'], M['rim'], M['well'], M['head'], M['tail'],
             M['plate']]
    PAINT, GLASS, TRIM, TYRE, RIM, WELL, HEAD, TAIL, PLATE = range(9)
    W = S['W']
    # ---- body (bevelled by a modifier on its own object, then joined as mesh data below)
    bm = bmesh.new()
    _extrude(bm, _lower_body(S), -W / 2, W / 2, PAINT)
    # wheel-well ceilings (faces pointing down inside the arches) read black
    for f in bm.faces:
        f.normal_update()
        c = f.calc_center_median()
        if f.normal.y < -0.2 and c.y > S['clear'] + 0.05:
            f.material_index = WELL
    hw = _greenhouse(bm, S, GLASS, PAINT)
    for v in bm.verts:                              # round the plan toward the bumpers
        v.co.z *= _wz(S, v.co.x) / (W / 2)
    body = bpy.data.meshes.new(name + ' body')
    bm.to_mesh(body)
    bm.free()
    ob = bpy.data.objects.new(name + ' tmp', body)
    bpy.context.scene.collection.objects.link(ob)
    md = ob.modifiers.new('bevel', 'BEVEL')
    md.width = 0.24
    md.segments = 3
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(25)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(body)
    # ---- details (unbevelled)
    _side_glass(bm, S, hw, GLASS)
    _arch_flares(bm, S, TRIM)
    L_ = S['L']
    top = S['lower']
    ny = top[1][1]                                   # nose height
    for s in (-1, 1):
        # headlamps and tail lamps wrap the corners a little
        wf, wr = _wz(S, 0.3), _wz(S, L_ - 0.2)
        _box(bm, 0.1, 0.7, ny - 0.12, ny + 0.2, s * (wf - 1.05), s * (wf - 0.12), HEAD)
        yt = S['belt'] - 0.05
        _box(bm, L_ - 0.4, L_ + 0.03, yt - 0.42, yt, s * (wr - 1.35), s * (wr + 0.02), TAIL)
        # mirrors at the A-pillar base
        xm = S['green'][0][0] + 0.55
        _box(bm, xm, xm + 0.5, S['belt'] + 0.1, S['belt'] + 0.42, s * (W / 2 - 0.35), s * (W / 2 + 0.3), PAINT)
        # black lower cladding / rocker between the arches
        x0w, x1w = S['wb']
        _box(bm, x0w + S['R'] + 0.2, x1w - S['R'] - 0.2, S['clear'] - 0.02, S['clear'] + 0.42,
             s * (W / 2 - 0.12), s * (W / 2 + 0.02), TRIM)
    _box(bm, -0.04, 0.2, S['clear'] + 0.35, ny - 0.15, -1.25, 1.25, TRIM)                   # grille / intake
    _box(bm, -0.06, 0.1, S['clear'] + 0.45, S['clear'] + 0.95, -0.55, 0.55, PLATE)          # front plate
    _box(bm, L_ - 0.12, L_ + 0.05, top[-2][1] - 1.15, top[-2][1] - 0.65, -0.55, 0.55, PLATE)
    _box(bm, L_ - 0.15, L_ + 0.07, S['clear'] - 0.02, S['clear'] + 0.7, -_wz(S, L_ - 0.2) + 0.25,
         _wz(S, L_ - 0.2) - 0.25, TRIM)                                                      # lower bumper
    # ---- wheels
    for xw in S['wb']:
        for s in (-1, 1):
            _wheel(bm, xw, S['R'], s * (W / 2 - 0.38), S['R'], 0.72, s, TYRE, RIM)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in slots:
        me.materials.append(m)
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(32))
    except Exception:
        pass
    # car frame (x along, y up, z across) in feet -> Blender meters (x, -z, y)
    me.transform(Matrix(((FT, 0, 0, 0), (0, 0, -FT, 0), (0, FT, 0, 0), (0, 0, 0, 1))))
    return me


def place_car(ctx, x, z, heading, style='suv', paint='silver', y=-0.5, sub='context', name=None):
    """Parked car with its front bumper centre at SCENE (x, z) pointing along `heading` (radians,
    0 = +x / east, pi/2 = +z / south). y = ground level under the tyres."""
    me = car_mesh(style, paint)
    ob = bpy.data.objects.new(name or f'ext car {style} {paint}', me)
    ob.location = ft2bl(x, y, z)
    ob.rotation_euler = (0, 0, math.pi - heading)     # the model's nose points to -x
    coll(ctx, sub).objects.link(ob)
    return ob
