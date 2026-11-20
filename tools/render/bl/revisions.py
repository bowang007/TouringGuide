"""Owner's design changes on the architect's plan (runs inside Blender, after bl/warp.py).

All coordinates are on the NEW plan (SCENE feet, x west->east, z rear->street). Each change works on
the built objects by name, so it survives re-runs of the build:

1. Bedroom 4 (the plan's office): flat 8 ft ceiling instead of the vault.
2. Front bedroom (tour "Bedroom 3", the plan's Bedroom #2): the canted bay is glazed down to the
   floor (plaster base, outside plinth and sills removed; glass, jambs and piers run to the floor).
3. Foyer: two skylights, on the entry roof's east slope (the ridge runs down the foyer's middle):
   one over the hall section, one in the vaulted entry.
4. Primary bedroom: the large rear window becomes a two-panel sliding door to the garden.
5. Bedroom 2 (next to the primary): its rear window runs up to the ceiling (from a 2'-0" sill, third round).
6. Primary bathroom: a tall west window (clear glass, a transom at 6 ft, a 2'-0" sill since the third round),
   between the vanity and the shower; the linen cabinet that stood in front of it is gone.
7. Kitchen skylight: moved off the garage-gable ridge (where the old 4 x 3 ft unit straddled two roof
   planes) to the continuous east-facing roof plane over the sink / dishwasher run, 3'-6" x 4'-0"
   as on the architect's plan.
(8, the dining table in line with the island, is built by the kitchen zone.)

Second round (2026-11-19):
9. Primary bathroom: a 2'-0" x 2'-6" skylight over the shower.
10. The office / bedroom-3 foyer-side wall lines up with the shared bath's east wall: that is the
    conversion itself (relayout.FOYER_WALL); here only the office ceiling and the foyer skylights follow.

Third round (2026-11-19): 5 and 6 stop at a 2'-0" sill (revision_spec.TALL_SILL) instead of the floor.

Fourth round (2026-11-19):
11. Laundry closet (the architect's "W / D", sheet SKA002) in the kitchen's south-west corner, 3'-10" x 3'-5" over
    its walls: new west and east walls and a north face with a 2'-6" x 6'-8" door (hinged east, open 90 degrees to the
    north), baseboards, a flush ceiling light, a recessed outlet box in the back wall, and a stacked washer / dryer
    (bl/laundry.py). The kitchen zone moved its fridge column and ovens east of the closet (kitchen_dining_kitchen.py).

Repairs to the conversion run first: ceiling_seam and floor_seam close seams the slab warp opened. Two general
repairs run last, after every change has cut or moved walls and slabs: floor_gaps (thin floor seams and the bare
strips under door openings) and skirting_trim (baseboards cut back to the walls behind them).
"""
import math
import re

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .common import FT, ft2bl

COLL_SHELL, COLL_OPEN = 'shell', 'openings'

from .revision_spec import (BATH_OLD_HOLE_Y, BATH_WIN_Z, FOYER_SKY, KITCHEN_SKY, LAUNDRY_CEILING,  # noqa: F401
                            LAUNDRY_CLEAR, LAUNDRY_DOOR_HEAD, LAUNDRY_DOOR_LINER, LAUNDRY_DOOR_LINER_PROUD,
                            LAUNDRY_DOOR_X, LAUNDRY_HOOKUP_RECESS, LAUNDRY_OUTER, LAUNDRY_WALL_T, OFFICE_CEILING,
                            PRIMARY_BATH_SKY, SLIDER_HEAD, SLIDER_X, TALL_SILL, laundry_leaf, laundry_walls)


# ------------------------------------------------------------------------------------- helpers
def _world(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world)
    return co @ mw[:3, :3].T + mw[:3, 3], mw


def _set_world(ob, w, mw):
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    inv = np.linalg.inv(mw)
    ob.data.vertices.foreach_set('co', (w @ inv[:3, :3].T + inv[:3, 3]).ravel())
    ob.data.update()


def bbox(ob):
    """(x0, x1, y0, y1, z0, z1) in SCENE feet."""
    if ob.type == 'MESH' and len(ob.data.vertices):
        w, _ = _world(ob)
        return (w[:, 0].min() / FT, w[:, 0].max() / FT, w[:, 2].min() / FT, w[:, 2].max() / FT,
                -w[:, 1].max() / FT, -w[:, 1].min() / FT)
    t = ob.matrix_world.translation
    return t.x / FT, t.x / FT, t.z / FT, t.z / FT, -t.y / FT, -t.y / FT


def find(pattern, coll=None):
    rx = re.compile(pattern, re.I)
    out = []
    for ob in bpy.data.objects:
        if not rx.search(ob.name):
            continue
        if coll and not any(c.name == coll or c.name.startswith(coll) for c in ob.users_collection):
            continue
        out.append(ob)
    return out


def remove(obs):
    n = 0
    for ob in list(obs):
        bpy.data.objects.remove(ob, do_unlink=True)
        n += 1
    return n


def map_y(ob, pairs, only_below=None):
    """Piecewise-linear remap of vertex heights (SCENE ft): pairs [(old, new), ...] sorted by old."""
    w, mw = _world(ob)
    y = w[:, 2] / FT
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]
    ny = np.interp(y, xs, ys, left=None, right=None)
    lo, hi = xs[0], xs[-1]
    ny = np.where(y < lo, y + (ys[0] - lo), ny)
    ny = np.where(y > hi, y + (ys[-1] - hi), ny)
    if only_below is not None:
        ny = np.where(y <= only_below, ny, y)
    w[:, 2] = ny * FT
    _set_world(ob, w, mw)


def move_face(ob, axis, old, new, tol=0.02):
    """Move every vertex whose SCENE coordinate `axis` ('x', 'y', 'z') equals `old` to `new`."""
    w, mw = _world(ob)
    k = {'x': 0, 'y': 2, 'z': 1}[axis]
    sgn = -1.0 if axis == 'z' else 1.0
    v = sgn * w[:, k] / FT
    sel = np.abs(v - old) < tol
    w[sel, k] = sgn * new * FT
    _set_world(ob, w, mw)
    return int(sel.sum())


def box(ctx, name, x0, x1, y0, y1, z0, z1, mat, coll):
    return ctx.box(name, x0, x1, y0, y1, z0, z1, mat, coll)


def _ray(origin_ft, down=True):
    dg = bpy.context.evaluated_depsgraph_get()
    o = ft2bl(*origin_ft)
    d = Vector((0, 0, -1 if down else 1))
    return bpy.context.scene.ray_cast(dg, o, d)


def roof_y(x, z, skip=()):
    """Height of the roof's top surface above (x, z): first hit from above on an exterior-shell
    roof piece (stucco walls and bay canopy skipped)."""
    o = ft2bl(x, 60.0, z)
    dg = bpy.context.evaluated_depsgraph_get()
    d = Vector((0, 0, -1))
    for _ in range(12):
        hit, loc, n, i, ob, _m = bpy.context.scene.ray_cast(dg, o, d)
        if not hit:
            return None
        if any(c.name == 'exterior_shell' for c in ob.users_collection) and ob.name not in skip \
                and not re.search(r'stucco|bay|cornice', ob.name, re.I):
            return loc.z / FT
        o = loc + d * 0.002
    return None


def ceiling_y(x, z, y0=7.2):
    """Height of the first ceiling surface above (x, y0, z)."""
    hit, loc, *_ = _ray((x, y0, z), down=False)
    return loc.z / FT if hit else 8.0


def _cut(obs, cutter):
    n = 0
    for ob in obs:
        m = ob.modifiers.new('revision cut', 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.solver = 'EXACT'
        m.object = cutter
        bpy.context.view_layer.objects.active = ob
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.object.modifier_apply(modifier=m.name)
        n += 1
    return n


def _overlap(b, x0, x1, z0, z1, y0=-1e9, y1=1e9):
    return b[0] < x1 and b[1] > x0 and b[4] < z1 and b[5] > z0 and b[2] < y1 and b[3] > y0


def _plane_mesh(name, quads, mats, coll_name, ctx):
    """Mesh from quads given as 4 SCENE-ft points each (with a material index)."""
    bm = bmesh.new()
    for pts, mi in quads:
        vs = [bm.verts.new(ft2bl(*p)) for p in pts]
        f = bm.faces.new(vs)
        f.material_index = mi
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(ctx.mat(m))
    ob = bpy.data.objects.new(name, me)
    ctx.coll(coll_name).objects.link(ob)
    return ob


def _slab(name, corners_lo, corners_hi, mat, coll_name, ctx):
    """Closed prism between two quads (4 points each, same order), any heights."""
    q = []
    lo, hi = corners_lo, corners_hi
    q.append(([lo[3], lo[2], lo[1], lo[0]], 0))
    q.append(([hi[0], hi[1], hi[2], hi[3]], 0))
    for i in range(4):
        j = (i + 1) % 4
        q.append(([lo[i], lo[j], hi[j], hi[i]], 0))
    ob = _plane_mesh(name, q, [mat], coll_name, ctx)
    me = ob.data
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    # weld the six faces into one closed shell first: on loose faces recalc can't tell outside from
    # inside, and inward normals bake black for the walk model
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return ob


# -------------------------------------------------------------------------------- skylights
def skylight(ctx, name, x0, x1, z0, z1, cut_ceiling_pat):
    """Roof-mounted skylight over the plan rectangle: holes through the ceiling and roof, a white
    lined shaft between them, a black curb and frame and clear glass parallel to the roof plane."""
    pad = 0.12                                       # shaft lining thickness
    corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    roof = [roof_y(x, z) for x, z in corners]
    if any(r is None for r in roof):
        print(f'[revisions] {name}: no roof above, skipped', flush=True)
        return 0
    ceil = [ceiling_y(x, z) for x, z in corners]
    y_lo = min(ceil) - 0.05
    # cut: everything between the ceiling and the sky over the opening
    cutter = ctx.box(f'{name} cutter', x0, x1, y_lo, max(roof) + 3.0, z0, z1, None, COLL_OPEN)
    targets = []
    rx = re.compile(cut_ceiling_pat, re.I)
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob is cutter or not len(ob.data.vertices):
            continue
        cols = {c.name for c in ob.users_collection}
        if not (cols & {COLL_SHELL, 'exterior_shell', COLL_OPEN}) and not any(c.startswith('zone_') for c in cols):
            continue
        b = bbox(ob)
        if not _overlap(b, x0, x1, z0, z1, y_lo, max(roof) + 3.0):
            continue
        is_roof = 'exterior_shell' in cols and not re.search(r'stucco', ob.name, re.I)
        is_ceiling = bool(rx.search(ob.name))
        attic = b[2] >= y_lo - 0.01 and (COLL_SHELL in cols or is_roof)      # infill / knee walls above
        if is_roof or is_ceiling or attic:
            targets.append(ob)
    n = _cut(targets, cutter)
    bpy.data.objects.remove(cutter, do_unlink=True)
    # lining: four walls from the ceiling surface up to 0.25 ft above the roof
    top = [r + 0.25 for r in roof]
    inner = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    outer = [(x0 - pad, z0 - pad), (x1 + pad, z0 - pad), (x1 + pad, z1 + pad), (x0 - pad, z1 + pad)]
    for i in range(4):
        j = (i + 1) % 4
        lo = [(*_xz(inner[i], ceil[i]),), (*_xz(inner[j], ceil[j]),), (*_xz(outer[j], ceil[j]),), (*_xz(outer[i], ceil[i]),)]
        hi = [(*_xz(inner[i], top[i]),), (*_xz(inner[j], top[j]),), (*_xz(outer[j], top[j]),), (*_xz(outer[i], top[i]),)]
        _slab(f'{name} lining {i}', lo, hi, 'paint_ceiling', COLL_OPEN, ctx)
    # curb + frame (black) and glass, parallel to the roof
    fr = 0.14
    for i in range(4):
        j = (i + 1) % 4
        a_i, a_j = outer[i], outer[j]
        b_i = (inner[i][0] + (0.0 if i in (0, 3) else 0.0), inner[i][1])
        lo = [_xz(a_i, top[i]), _xz(a_j, top[j]), _xz(_toward(a_j, inner[j], fr + pad), top[j]), _xz(_toward(a_i, inner[i], fr + pad), top[i])]
        hi = [(p[0], p[1] + 0.12, p[2]) for p in lo]
        _slab(f'{name} frame {i}', lo, hi, 'black_aluminum', COLL_OPEN, ctx)
    g_lo = [_xz(inner[k], top[k] + 0.06) for k in range(4)]
    g_hi = [(p[0], p[1] + 0.03, p[2]) for p in g_lo]
    gl = _slab(f'{name} glass', g_lo, g_hi, 'glass_clear', COLL_OPEN, ctx)
    gl.visible_shadow = True
    # recessed cans that would now hang in the opening
    gone = remove([ob for ob in bpy.data.objects
                   if re.search(r'\bcan\b|can lens|can trim', ob.name) and _inside_xz(ob, x0 - 0.4, x1 + 0.4, z0 - 0.4, z1 + 0.4)])
    print(f'[revisions] {name}: cut {n}, roof y {min(roof):.2f}-{max(roof):.2f}, ceiling {min(ceil):.2f}-{max(ceil):.2f}, cans removed {gone}', flush=True)
    return n


def _xz(p, y):
    return (p[0], y, p[1])


def _toward(a, b, d):
    """Point a moved by d toward b along both axes (clamped)."""
    dx = b[0] - a[0]
    dz = b[1] - a[1]
    return (a[0] + math.copysign(min(d, abs(dx)), dx), a[1] + math.copysign(min(d, abs(dz)), dz))


def _inside_xz(ob, x0, x1, z0, z1):
    b = bbox(ob)
    cx, cz = (b[0] + b[1]) / 2, (b[4] + b[5]) / 2
    return x0 <= cx <= x1 and z0 <= cz <= z1


# ------------------------------------------------------------------------------------ repairs
def ceiling_seam(ctx):
    """The original house's two flat ceiling panels (west of the addition | central) met on one line
    of the concept plan. warp.py maps each slab corner with the room it borders, and the far ends of
    that line border different rooms (Bedroom 2 / the shared bath at one, the hall at the other), so
    the seam opened into a wedge up to 1.9 ft wide over Bedroom 2 and the shared bath, open to the
    attic. Put the west panel's east edge on the central panel's west edge. Runs before any skylight
    cut, while both panels are still plain 8-vertex prisms."""
    west = find(r'^\d* ?Original house ceiling west of addition')
    cen = find(r'^\d* ?Original house ceiling central panel')
    if len(west) != 1 or len(cen) != 1:
        return f'panels not found ({len(west)}, {len(cen)})'
    wc, mc = _world(cen[0])
    cx, cz = wc[:, 0] / FT, -wc[:, 1] / FT
    side = sorted({(round(a, 4), round(b, 4)) for a, b in zip(cx, cz) if a < cx.min() + 2.5}, key=lambda p: p[1])
    (xa, za), (xb, zb) = side[0], side[-1]          # the central panel's west edge, rear .. front
    ww, mw = _world(west[0])
    wx, wz = ww[:, 0] / FT, -ww[:, 1] / FT
    east = wx > wx.max() - 0.6
    old = sorted({(round(a, 2), round(b, 2)) for a, b in zip(wx[east], wz[east])})
    nx = xa + (xb - xa) * (wz[east] - za) / (zb - za)
    ww[east, 0] = nx * FT
    _set_world(west[0], ww, mw)
    new = sorted({(round(a, 2), round(b, 2)) for a, b in zip(nx, wz[east])})
    out = {'edge': [(xa, za), (xb, zb)], 'west panel east edge': [old, new]}
    # The same corner mapping skews the central panel's front edge: its west corner is mapped with the hall
    # (z 30.84) and its east corner with the kitchen (z 31.24, the kitchen / garage wall's centre line). Between the
    # garage west wall and x 22.5 the edge therefore stopped up to 0.03 ft short of that wall's north face: a
    # hairline open to the attic along the back of the laundry closet's ceiling (fourth round; check_holes' 0.2 ft
    # grid is too coarse to see it). Slide the west corner along the panel's own west edge to the east corner's z:
    # the front edge is square on the wall line and the west edge stays where the west panel was just put.
    front = float(cz.max())
    if 0.01 < front - zb < 1.0:
        corner = (np.abs(cx - xb) < 2e-3) & (np.abs(cz - zb) < 2e-3)
        nxb = xa + (xb - xa) * (front - za) / (zb - za)
        wc[corner, 0] = nxb * FT
        wc[corner, 1] = -front * FT
        _set_world(cen[0], wc, mc)
        out['central panel front corner'] = [(round(xb, 3), round(zb, 3)), (round(nxb, 3), round(front, 3)), int(corner.sum())]
    return out


def _set_z(ob, pick, value):
    """Move the vertices whose SCENE z satisfies pick(z) to z = value."""
    w, mw = _world(ob)
    m = pick(-w[:, 1] / FT)
    w[m, 1] = -value * FT
    _set_world(ob, w, mw)
    return int(m.sum())


def floor_seam(ctx):
    """The same corner mapping at the foyer's rear end: the floor (and foundation) slab under the
    bedroom-4 / foyer row ended on a line from z 43.18 (bedroom 3 side) to 44.17 (foyer side), while
    bedroom 3's slab starts at 43.18 and the foyer front slab at 44.17. That left a wedge up to 0.28 ft
    wide across the foyer floor, open to the plinth, and an overlap under bedroom 3. Square both
    seams on bedroom 3's rear edge (the foyer front slab is extended back to it)."""
    out = {}
    for fam, front in (('Oak floor substrate', 'Hall in enclosed porch substrate'),
                       ('Foundation', 'Front hall infill foundation')):
        pieces = [(o, bbox(o)) for o in find(rf'^\d* ?{fam}$')]
        row = [o for o, b in pieces if b[1] > 21.0 and b[4] < 31.5 and 43.5 < b[5] < 45.0]
        west = [b for o, b in pieces if b[1] < 15.6 and 42.8 < b[4] < 43.6]
        hall = find(rf'^\d* ?{front}$')
        if len(row) != 1 or len(west) != 1 or len(hall) != 1:
            out[fam] = f'not found ({len(row)}, {len(west)}, {len(hall)})'
            continue
        z = west[0][4]
        out[fam] = {'seam z': round(z, 3),
                    'row front verts': _set_z(row[0], lambda v: v > 42.8, z),
                    'foyer slab rear verts': _set_z(hall[0], lambda v: v < 45.0, z)}
    return out


# ---------------------------------------------------------------------------------- changes
def bedroom4_flat(ctx):
    n = remove(find(r'Bedroom 4 vaulted ceiling|Bedroom 4 gable infill'))
    cx0, cx1, cz0, cz1 = OFFICE_CEILING
    box(ctx, 'Bedroom 4 flat ceiling', cx0, cx1, 8.0, 8.12, cz0, cz1, 'paint_ceiling', COLL_SHELL)
    # The vault's cans sat on the slope above the new ceiling: drop them (the pendant lights the room).
    n += remove([ob for ob in find(r'^slope can') if (lambda b: b[1] < OFFICE_CEILING[1] + 0.3 and 28.5 < b[4] and b[5] < 37.0)(bbox(ob))])
    # The pendant hung from the vault on a long stem. Rehang it as one piece under the flat ceiling:
    # canopy at the ceiling, globe (with its collar) 0.35 ft below, the stem shortened to span the gap.
    parts = {k: find(rf'^B4 pendant {k}$') for k in ('canopy', 'collar', 'globe', 'stem')}
    lamp = find(r'^B4 globe lamp')
    lowered = 0
    if all(parts.values()):
        canopy, collar, globe, stem = (parts[k][0] for k in ('canopy', 'collar', 'globe', 'stem'))
        ceil = 7.995
        canopy.location.z += (ceil - bbox(canopy)[3]) * FT   # its top was at the old vault
        g = bbox(globe)
        g_top = ceil - 0.35
        dg = g_top - g[3]
        for ob in (globe, collar):                   # the collar is the globe's fitter; they move together
            ob.location.z += dg * FT
        bpy.context.view_layer.update()
        s = bbox(stem)
        top, bot = bbox(canopy)[2] + 0.02, max(g_top, bbox(collar)[3]) - 0.02
        stem.scale.z *= max(0.05, (top - bot) / max(1e-3, s[3] - s[2]))
        bpy.context.view_layer.update()
        s = bbox(stem)
        stem.location.z += (bot - s[2]) * FT
        gc = (g_top + (g_top - (g[3] - g[2]))) / 2
        for ob in lamp:                              # the bulb sits in the middle of the globe
            ob.location.z = gc * FT
        lowered = 4 + len(lamp)
    bpy.context.view_layer.update()
    return {'removed': n, 'rehung': lowered}


def _sills(x0, x1):
    """Old window sills / stools on the rear wall between x0 and x1."""
    return [ob for ob in bpy.data.objects if ob.type == 'MESH' and re.search(r'sill|stool', ob.name, re.I)
            and any(c.name in (COLL_OPEN, COLL_SHELL) for c in ob.users_collection)
            and (lambda b: b[0] > x0 - 0.3 and b[1] < x1 + 0.3 and b[5] < 0.8 and b[4] > -0.8 and b[3] < 3.2)(bbox(ob))]


def bay_to_floor(ctx):
    n = remove(find(r'Bedroom 3 bay low plaster base|Bay stucco plinth|Bedroom 3 bay projecting white sill|^B3 seat'))
    k = 0
    for ob in find(r'Bedroom 3 bay (tall sash glass|sash jamb|deep white pier|transom and meeting rail)'):
        if ob.type != 'MESH':
            continue
        b = bbox(ob)
        if b[2] > 7.0:                               # top rails / bands stay
            continue
        if b[3] < 1.3:                               # bottom rail: drop to the floor
            ob.location.z -= 1.0 * FT
        else:
            map_y(ob, [(1.0, 0.0), (1.13, 0.13), (7.37, 7.37), (7.5, 7.5)], only_below=7.0)
        k += 1
    return {'removed': n, 'extended': k}


def primary_slider(ctx):
    x0, x1 = SLIDER_X
    gone = remove([ob for ob in find(r'^\d+ Primary — rear wall$')
                   if (lambda b: b[3] <= 2.6 and b[0] > x0 - 0.1 and b[1] < x1 + 0.1 and b[4] < 0.3)(bbox(ob))
                   and any(c.name == COLL_SHELL for c in ob.users_collection)])
    gone += remove([ob for ob in find(r'Painted skirting — Primary — rear wall')
                    if (lambda b: b[0] > x0 - 0.1 and b[1] < x1 + 0.1)(bbox(ob))])
    gone += remove([ob for ob in find(r'^\d+ Primary — rear wall$') if any(c.name == COLL_OPEN for c in ob.users_collection)])
    gone += remove(_sills(x0, x1))
    zc, fd, fw = 0.0, 0.22, 0.14
    c = COLL_OPEN
    # outer frame
    box(ctx, 'Primary slider head', x0, x1, SLIDER_HEAD - fw, SLIDER_HEAD, zc - fd / 2, zc + fd / 2, 'black_aluminum', c)
    box(ctx, 'Primary slider sill', x0, x1, 0.0, 0.06, zc - fd / 2, zc + fd / 2, 'black_aluminum', c)
    box(ctx, 'Primary slider jamb W', x0, x0 + fw, 0.0, SLIDER_HEAD, zc - fd / 2, zc + fd / 2, 'black_aluminum', c)
    box(ctx, 'Primary slider jamb E', x1 - fw, x1, 0.0, SLIDER_HEAD, zc - fd / 2, zc + fd / 2, 'black_aluminum', c)
    # two panels: west fixed (outer track), east sliding (inner track); they overlap at the middle
    xm = (x0 + x1) / 2
    panels = [('fixed', x0 + fw, xm + 0.08, zc - 0.05), ('sliding', xm - 0.08, x1 - fw, zc + 0.05)]
    st = 0.13
    for tag, a, b, z in panels:
        for nm, ax0, ax1, ay0, ay1 in (('stile a', a, a + st, 0.06, SLIDER_HEAD - fw), ('stile b', b - st, b, 0.06, SLIDER_HEAD - fw),
                                       ('rail bottom', a, b, 0.06, 0.06 + st + 0.05), ('rail top', a, b, SLIDER_HEAD - fw - st, SLIDER_HEAD - fw)):
            box(ctx, f'Primary slider {tag} {nm}', ax0, ax1, ay0, ay1, z - 0.04, z + 0.04, 'black_aluminum', c)
        g = box(ctx, f'Primary slider {tag} glass', a + st, b - st, 0.06 + st + 0.05, SLIDER_HEAD - fw - st, z - 0.012, z + 0.012,
                'glass_clear', c)
        g.visible_shadow = True
    box(ctx, 'Primary slider pull', xm + 0.02, xm + 0.08, 3.0, 4.6, zc + 0.10, zc + 0.14, 'black_metal', c)
    return {'removed': gone}


def bedroom2_tall_window(ctx):
    """Bedroom 2's rear window (concept sill 2'-6", head 7'-0") runs from a 2'-0" sill (TALL_SILL) up to the 8 ft
    ceiling: the wall below keeps its skirting and is cut down to the sill, the stool and outside sill drop with it, the
    header above goes."""
    s = TALL_SILL
    shell = [ob for ob in find(r'^\d+ Bedroom 2 — rear wall$') if any(cc.name == COLL_SHELL for cc in ob.users_collection)
             and (lambda b: b[0] > 14.3 and b[1] < 19.8)(bbox(ob))]
    low = [ob for ob in shell if bbox(ob)[3] <= 2.6]
    gone = remove([ob for ob in shell if bbox(ob)[2] >= 6.9])
    for ob in low:
        map_y(ob, [(0.0, 0.0), (2.5, s)])
    sills = _sills(14.3, 19.8)
    for ob in sills:
        ob.location.z -= (2.5 - s) * FT
    k = 0
    for ob in find(r'^\d+ Bedroom 2 — rear wall$', COLL_OPEN):
        map_y(ob, [(2.5, s), (2.6, s + 0.1), (6.9, 7.9), (7.0, 8.0)])
        k += 1
    return {'removed header': gone, 'wall below cut to the sill': len(low), 'sills lowered': len(sills), 'stretched': k}


def _copy(ob, name):
    c = ob.copy()
    c.data = ob.data.copy()
    c.name = name
    for col in ob.users_collection:
        col.objects.link(c)
    return c


def _clamp(ob, z=None, y=None):
    """Clamp vertex z (SCENE ft) to the range z and height to the range y; the rest of the mesh collapses onto it."""
    w, mw = _world(ob)
    if z is not None:
        w[:, 1] = -np.clip(-w[:, 1] / FT, *z) * FT
    if y is not None:
        w[:, 2] = np.clip(w[:, 2] / FT, *y) * FT
    _set_world(ob, w, mw)


def _cut_finish(ob, z0, z1, y0, y1, below=None):
    """Split a west-wall finish piece around the opening z0..z1 x y0..y1: the parts north and south of it and those
    below and above it (each a copy clamped to its range; the part below stops at `below`, under the stool).
    Returns the pieces; the original goes."""
    b = bbox(ob)
    if b[5] <= z0 + 0.005 or b[4] >= z1 - 0.005 or b[3] <= y0 + 0.005 or b[2] >= y1 - 0.005:
        return [ob]
    out = []
    for tag, zr, yr in (('N', (b[4], z0), (b[2], b[3])), ('S', (z1, b[5]), (b[2], b[3])),
                        ('below', (z0, z1), (b[2], min(b[3], y0 if below is None else below))),
                        ('above', (z0, z1), (max(b[2], y1), b[3]))):
        if zr[1] - zr[0] > 0.01 and yr[1] - yr[0] > 0.01:
            c = _copy(ob, f'{ob.name} {tag}')
            _clamp(c, zr, yr)
            out.append(c)
    remove([ob])
    return out


def bath_window(ctx):
    """Primary bath west window between the vanity and the shower: clear glass from a 2'-0" sill (TALL_SILL) to the
    8 ft ceiling with a transom at 6 ft. The wall below the sill is a copy of the neighbouring wall (paint inside,
    stucco outside); the room's west-wall finish ('A0 tile west ...', built by the baths zone around the concept
    window) is cut around the new opening and closed where the concept window was; a stool and a linen roman shade."""
    z0, z1 = BATH_WIN_Z
    s = TALL_SILL
    gone = remove(find(r'Primary bathroom west wall — (below|above) privacy window|Primary bathroom privacy-window|'
                       r'Primary bathroom operable awning|Primary bathroom obscured privacy glazing'))
    gone += remove(find(r'Painted skirting — Primary bathroom west wall — below'))
    gone += remove(find(r'^A0 (linen|succulent)'))
    north = find(r'Primary bathroom west wall — north solid')
    for ob in north:
        move_face(ob, 'z', 22.20, z0)
    for ob in find(r'Primary bathroom west wall — south solid'):
        move_face(ob, 'z', 24.89, z1)
    if north:                               # stretch a copy of the north solid across the opening, up to the sill
        apron = _copy(north[0], 'Primary bathroom west wall — below tall window')
        w, mw = _world(apron)
        z = -w[:, 1] / FT
        w[:, 1] = -(z0 + (z - z.min()) / (z.max() - z.min()) * (z1 - z0)) * FT
        w[:, 2] = np.minimum(w[:, 2], s * FT)
        _set_world(apron, w, mw)
    stool_t = 0.06
    pieces = []
    for ob in find(r'^A0 tile west'):
        pieces += _cut_finish(ob, z0, z1, s, 8.0, below=s - stool_t)
    face = max([bbox(p)[1] for p in pieces if bbox(p)[1] < 1.0] or [0.29])     # room face of the wall finish
    closed = 0
    h0, h1 = BATH_OLD_HOLE_Y
    for ob in pieces:                       # beside the new opening, close the concept window's hole
        b = bbox(ob)
        if abs(b[3] - h0) < 0.02 and (b[5] <= z0 + 0.01 or b[4] >= z1 - 0.01) and b[4] < 25.0 and b[5] > 22.0:
            closed += move_face(ob, 'y', h0, h1) > 0
    xc, fd, fw = 0.0, 0.22, 0.12
    c = COLL_OPEN
    box(ctx, 'Primary bath tall window head', xc - fd / 2, xc + fd / 2, 8.0 - fw, 8.0, z0, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window sill', xc - fd / 2, xc + fd / 2, s, s + 0.08, z0, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window jamb N', xc - fd / 2, xc + fd / 2, s, 8.0, z0, z0 + fw, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window jamb S', xc - fd / 2, xc + fd / 2, s, 8.0, z1 - fw, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window transom', xc - fd / 2, xc + fd / 2, 6.0, 6.1, z0, z1, 'black_aluminum', c)
    # clear glass: the side yard outside is fenced (6'-2") and screened by an evergreen (exterior_plants)
    g = box(ctx, 'Primary bath tall window lower glass', xc - 0.015, xc + 0.015, s + 0.08, 6.0, z0 + fw, z1 - fw,
            'glass_clear', c)
    g.visible_shadow = True
    g2 = box(ctx, 'Primary bath tall window upper glass', xc - 0.015, xc + 0.015, 6.1, 8.0 - fw, z0 + fw, z1 - fw,
             'glass_clear', c)
    g2.visible_shadow = True
    # interior stool on the apron (its front lip with short horns on the wall finish) and a linen roman shade,
    # inside-mounted under the head, drawn up to about 6'-4"
    box(ctx, 'Primary bath window stool', fd / 2, face, s - stool_t, s, z0, z1, 'white_oak_veneer', c)
    box(ctx, 'Primary bath window stool lip', face, face + 0.07, s - 0.075, s, z0 - 0.07, z1 + 0.07, 'white_oak_veneer', c)
    box(ctx, 'Primary bath roman shade headrail', 0.13, 0.27, 7.74, 8.0 - fw, z0 + 0.02, z1 - 0.02, 'paint_trim', c)
    box(ctx, 'Primary bath roman shade fabric', 0.215, 0.235, 6.62, 7.74, z0 + 0.03, z1 - 0.03, 'fabric_linen_white', c)
    for i, yb in enumerate((6.30, 6.47)):
        fold = box(ctx, f'Primary bath roman shade fold {i}', 0.20, 0.30 - 0.025 * i, yb, yb + 0.19, z0 + 0.03, z1 - 0.03,
                   'fabric_linen_white', c)
        ctx.add_bevel(fold, 0.06, 4)
    return {'removed': gone, 'finish pieces': len(pieces), 'old hole closed': closed, 'finish face x': round(face, 3)}


def kitchen_skylight(ctx):
    gone = remove(find(r'^\d+ Kitchen skylight —'))
    gone += remove(find(r'^\d+ House ceiling — skylight (east|north|south) panel$'))
    box(ctx, 'Kitchen ceiling (east of the central panel)', 28.41, 39.42, 8.0, 8.12, 0.0, 31.24, 'paint_ceiling', COLL_SHELL)
    n = skylight(ctx, 'Kitchen skylight', *KITCHEN_SKY, r'ceiling')
    return {'removed': gone, 'cut': n}


def foyer_skylights(ctx):
    out = {}
    for i, r in enumerate(FOYER_SKY):
        out[f'foyer {i}'] = skylight(ctx, f'Foyer skylight {i}', *r, r'ceiling|vault')
    return out


def primary_bath_skylight(ctx):
    return skylight(ctx, 'Primary bath skylight', *PRIMARY_BATH_SKY, r'ceiling')


def entry_vault_closure(ctx):
    """Close the strip between the entry vault's rear edge (eaves 9.05 ft, ridge 11.2 ft) and the
    rear gable below it (eaves 8 ft): looking up from the foyer it opened into the attic."""
    vault = find(r'Coordinated entry vaulted ceiling')
    gable = find(r'Coordinated entry rear gable')
    if not vault or not gable:
        return 0
    vb = [bbox(o) for o in vault]
    x0 = min(b[0] for b in vb)
    x1 = max(b[1] for b in vb)
    z0 = min(b[4] for b in vb)
    xr = (x0 + x1) / 2
    eave = min(b[2] for b in vb) + 0.10
    ridge = max(b[3] for b in vb) + 0.10
    zf, zb = z0 - 0.06, z0 + 0.06
    for tag, xa, xb, ya, yb in (('W', x0, xr, eave, ridge), ('E', xr, x1, ridge, eave)):
        lo = [(xa, 7.95, zf), (xb, 7.95, zf), (xb, 7.95, zb), (xa, 7.95, zb)]
        hi = [(xa, ya, zf), (xb, yb, zf), (xb, yb, zb), (xa, ya, zb)]
        _slab(f'Entry vault rear infill {tag}', lo, hi, 'paint_wall', COLL_SHELL, ctx)
    return 2


def _reshape(ob, x0, x1, y0, y1, z0, z1):
    """Stretch a plain box piece (a wall, a baseboard) onto the SCENE-ft box x0..x1, y0..y1, z0..z1."""
    w, mw = _world(ob)
    for k, sgn, (a, b) in ((0, 1.0, (x0, x1)), (2, 1.0, (y0, y1)), (1, -1.0, (z0, z1))):
        v = sgn * w[:, k] / FT
        lo, hi = v.min(), v.max()
        w[:, k] = sgn * (a + (v - lo) / max(hi - lo, 1e-9) * (b - a)) * FT
    _set_world(ob, w, mw)
    return ob


def _like(src, name, *b):
    """A copy of the shell piece `src` reshaped onto the box b. The copy keeps src's materials, collection and
    `scene_index`, so it is baked with its family (a wall copy is class 'wall', not 'base') and is found by the
    shell checks (baseboards, check_holes)."""
    return _reshape(_copy(src, name), *b)


def laundry_closet(ctx):
    """Fourth round: the laundry closet of the architect's sheet (revision_spec.LAUNDRY_*) and its stacked pair.

    Walls are copies of the garage west wall, so they carry its paint and bake as walls. The foyer's east baseboard
    is extended along the closet's west face; new runs go round the outside and the inside. The door follows the
    house's other interior doors: painted jamb liners and head trim, a flush slab leaf (here open), black levers.
    The outlet box is a real recess: the back wall is split around it, with a thin piece left behind it."""
    from . import laundry
    x0, x1, z0, z1 = LAUNDRY_OUTER
    t = LAUNDRY_WALL_T
    cx0, cx1, cz0, cz1 = LAUNDRY_CLEAR
    d0, d1 = LAUNDRY_DOOR_X
    head, ln = LAUNDRY_DOOR_HEAD, LAUNDRY_DOOR_LINER
    out = {}

    def shell_one(pat, pick=lambda b: True):
        obs = [o for o in find(pat, COLL_SHELL) if o.type == 'MESH' and len(o.data.vertices) == 8 and pick(bbox(o))]
        return obs[0] if obs else None

    # ---- walls: full height to the ceiling above (flat 8 ft here; measured, so a different ceiling is still met)
    src = shell_one(r'^\d+ Garage interior access — north infill wall$') or shell_one(r'^\d+ Kitchen / garage separation$')
    if src is None:
        raise RuntimeError('no shell wall to copy for the closet walls')
    ceil = [ceiling_y(x, z) for x, z in ((x0 + 0.1, z0 + 0.1), (x1 - 0.1, z0 + 0.1), (x0 + 0.1, z1 - 0.1),
                                         (x1 - 0.1, z1 - 0.1), ((x0 + x1) / 2, (z0 + z1) / 2))]
    top = max(LAUNDRY_CEILING, max(ceil))
    for name, wx0, wx1, wy0, wy1, wz0, wz1 in laundry_walls():
        _like(src, name, wx0, wx1, wy0, top if wy1 == LAUNDRY_CEILING else wy1, wz0, wz1)
    out['ceiling y'] = [round(min(ceil), 3), round(max(ceil), 3)]

    # ---- recess for the washer outlet box: the back wall is split around it (west / below / above / behind)
    recess = None
    back = shell_one(r'^\d+ Kitchen / garage separation$')
    if back is not None:
        rx0, rx1, ry0, ry1, dep = LAUNDRY_HOOKUP_RECESS
        b = bbox(back)
        if b[0] < rx0 - 0.05 and b[1] > rx1 + 0.05 and abs(b[4] - cz1) < 0.02 and b[5] - b[4] > dep + 0.05:
            nm = re.sub(r'^\d+ ', '', back.name)
            _like(back, f'{nm} (west of the laundry outlet box)', b[0], rx0, b[2], b[3], b[4], b[5])
            _like(back, f'{nm} (below the laundry outlet box)', rx0, rx1, b[2], ry0, b[4], b[5])
            _like(back, f'{nm} (above the laundry outlet box)', rx0, rx1, ry1, b[3], b[4], b[5])
            _like(back, f'{nm} (behind the laundry outlet box)', rx0, rx1, ry0, ry1, b[4] + dep, b[5])
            move_face(back, 'x', b[0], rx1)
            recess = LAUNDRY_HOOKUP_RECESS
    out['outlet recess'] = bool(recess)

    # ---- baseboards (shell pieces named "skirting": skirting_trim and check_holes look after them)
    sk_src = shell_one(r'^\d+ Painted skirting — Garage interior access', lambda b: b[1] < x0 + 0.1 and abs(b[4] - z1) < 0.4)   # the foyer's east run
    if sk_src is not None:
        sb = bbox(sk_src)
        sy0, sy1, proud, sunk = sb[2], sb[3], x0 - sb[0], sb[1] - x0
        move_face(sk_src, 'z', sb[4], z0)               # ... now also runs along the closet's west face
    else:
        sy0, sy1, proud, sunk = 0.025, 0.455, 0.045, 0.002
    any_sk = sk_src or shell_one(r'^\d+ Painted skirting')

    def skirt(name, bx0, bx1, bz0, bz1, corner=False):
        nm = f'Laundry closet plinth block {name}' if corner else f'Painted skirting — Laundry closet {name}'
        if any_sk is not None:
            return _like(any_sk, nm, bx0, bx1, sy0, sy1, bz0, bz1)
        return box(ctx, nm, bx0, bx1, sy0, sy1, bz0, bz1, 'paint_trim', COLL_SHELL)
    if sk_src is None:
        skirt('west face', x0 - proud, x0 + sunk, z0, cz1)
    kit_front = [bbox(o)[4] for o in find(r'^kd tall wall door panel run') if o.type == 'MESH']
    zk = min(kit_front) if kit_front else z1            # the pantry wall's fronts: the kitchen-side run dies into them
    la, lb = d0 - ln, d1 + ln                           # outer edges of the jamb liners
    skirt('north face W', x0, la, z0 - proud, z0 + sunk)
    skirt('north face E', lb, x1, z0 - proud, z0 + sunk)
    skirt('east face', x1 - sunk, x1 + proud, z0, zk)
    # the two outside corners are closed with blocks: a run that turned the corner would have no wall behind its
    # last 1/2 in and skirting_trim would cut it back
    skirt('NW', x0 - proud, x0, z0 - proud, z0, corner=True)
    skirt('NE', x1, x1 + proud, z0 - proud, z0, corner=True)
    zb = cz1 - 0.052                                    # the back wall's own run (0.052 deep) stays; the others butt into it
    skirt('inside W', cx0 - sunk, cx0 + proud, cz0 + proud, zb)
    skirt('inside E', cx1 - proud, cx1 + sunk, cz0 + proud, zb)
    skirt('inside NW', cx0 - sunk, la, cz0 - sunk, cz0 + proud)
    skirt('inside NE', lb, cx1 + sunk, cz0 - sunk, cz0 + proud)
    # the back wall's run used to start 0.2 ft west of the wall's end, in the open hall: now it starts inside the closet
    kb = shell_one(r'^\d+ Painted skirting — Kitchen / garage separation$', lambda b: b[5] < cz1 + 0.05 and b[0] < cx0)
    if kb is not None:
        move_face(kb, 'x', bbox(kb)[0], cx0 - sunk)

    # ---- floor: the oak runs through. The slab warp's hairline seam (see floor_gaps) crosses the closet; floor_gaps
    # runs after this and stops at the new walls and baseboards, so the footprint gets one patch under the floor here.
    # Its ends lie 0.03 ft past floor_gaps' scan columns (x = 0.3 + 0.1 k) beside the walls: the neighbouring patches
    # reach 0.06 ft past their last column, so the three overlap under the baseboards.
    floor = [o for o in find(r'^\d+ Oak floor substrate$', COLL_SHELL) if _overlap(bbox(o), x0, x1, z0, z1)]
    if floor:
        fy = max(bbox(o)[3] for o in floor)
        px0 = 0.3 + 0.1 * math.floor((x0 - 0.05 - 0.3) / 0.1) + 0.03
        px1 = 0.3 + 0.1 * math.ceil((x1 + 0.05 - 0.3) / 0.1) - 0.03
        patch = ctx.box('Floor seam patch laundry closet', px0, px1, fy - 0.1, fy - 0.0026, z0, z1, None, COLL_SHELL)
        if floor[0].data.materials:
            patch.data.materials.append(floor[0].data.materials[0])
    out['floor'] = [re.sub(r'^\d+ ', '', o.name) for o in floor]

    # ---- door: jamb liners and head trim like the other interior doors, flush slab leaf standing open
    c = COLL_OPEN
    ow = LAUNDRY_DOOR_LINER_PROUD                       # the liners stand this far off both wall faces
    box(ctx, 'Laundry closet door jamb W', d0 - ln, d0 + ln, 0.0, head - 0.08, z0 - ow, z0 + t + ow, 'paint_trim', c)
    box(ctx, 'Laundry closet door jamb E', d1 - ln, d1 + ln, 0.0, head - 0.08, z0 - ow, z0 + t + ow, 'paint_trim', c)
    box(ctx, 'Laundry closet door head trim', d0 - ln, d1 + ln, head - 0.08, head + 0.06, z0 - ow, z0 + t + ow, 'paint_trim', c)
    leaf = laundry_leaf()
    ctx.box_c('Laundry closet door leaf (open)', leaf['center'], leaf['size'], leaf['rot'], 'door_slab', c, bevel=0.006, segments=2)
    laundry.door_hardware(ctx, leaf, c)
    out['door'] = {'opening x': (round(d0, 4), round(d1, 4)), 'head': head, 'leaf': [round(v, 3) for v in leaf['aabb']]}

    # ---- contents: stacked washer / dryer, hookups, ceiling light
    out['contents'] = laundry.build(ctx, recess, top)
    out['clear'] = [round(v, 3) for v in LAUNDRY_CLEAR]
    return out


# ---- repairs that run last (after every change above has cut or moved walls and slabs)
def _bvh(colls, skip=None):
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys, owner = [], [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.hide_render or not ({c.name for c in ob.users_collection} & colls):
            continue
        if skip is not None and skip(ob):
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw, base = ob.matrix_world, len(verts)
        verts += [mw @ v.co for v in me.vertices]
        for p in me.polygons:
            polys.append([base + i for i in p.vertices])
            owner.append(ob)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys), owner


SKIRT = re.compile(r'skirting|baseboard', re.I)


def skirting_trim(ctx):
    """Every baseboard needs a wall right behind it. The warp carries a run with its wall, but where a wall got
    shorter (the kitchen / garage wall's end in the hall, the garage wall at the porch) or an opening was cut
    afterwards (the primary bedroom's sliding door) the run stuck out into the room on its own. Each run is
    sampled every 0.05 ft and cut back to the stretches with a shell wall within 0.25 ft behind it; a run with
    none is removed."""
    bvh, _ = _bvh({COLL_SHELL, 'exterior_shell'},
                  skip=lambda ob: bool(SKIRT.search(ob.name)) or bool(re.search(r'glass|glazing', ob.name, re.I)))
    step, out = 0.05, {}
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and SKIRT.search(o.name)
               and any(c.name == COLL_SHELL for c in o.users_collection)]:
        x0, x1, _, _, z0, z1 = bbox(ob)
        along_x = (x1 - x0) >= (z1 - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        if a1 - a0 < 0.1:
            continue
        backed = []
        t = a0 + step / 2
        while t < a1:
            x, z = (t, (z0 + z1) / 2) if along_x else ((x0 + x1) / 2, t)
            o = ft2bl(x, 0.2, z)
            ok = False
            for d in ((0, -1, 0), (0, 1, 0)) if along_x else ((1, 0, 0), (-1, 0, 0)):
                if bvh.ray_cast(o, Vector(d), 0.25 * FT)[0] is not None:
                    ok = True
                    break
            backed.append((t, ok))
            t += step
        runs = []
        for t, ok in backed:
            if not ok:
                continue
            if runs and t - runs[-1][1] < 0.2:
                runs[-1][1] = t
            else:
                runs.append([t, t])
        runs = [(max(a0, a - step / 2), min(a1, b + step / 2)) for a, b in runs if b - a + step >= 0.15]
        if len(runs) == 1 and runs[0][0] - a0 < 0.08 and a1 - runs[0][1] < 0.08:
            continue
        key = re.sub(r'^\d+ ', '', ob.name)
        if not runs:
            remove([ob])
            out[key] = 'removed (no wall behind it)'
            continue
        for i, (a, b) in enumerate(runs):
            piece = ob if i == 0 else _copy(ob, f'{ob.name} {i}')
            w, mw = _world(piece)
            if along_x:
                w[:, 0] = np.clip(w[:, 0], a * FT, b * FT)
            else:
                w[:, 1] = -np.clip(-w[:, 1] / FT, a, b) * FT
            _set_world(piece, w, mw)
        out[key] = [(round(a, 2), round(b, 2)) for a, b in runs] + [f'was {a0:.2f}..{a1:.2f}']
    return out


def floor_gaps(ctx):
    """Slab warp seams too thin for floor_seam's targeted fix: where the floor slabs part, the foundation shows as
    grey lines across the oak (the hall's north end, the hall / living line), and under door openings, where
    the slabs stop at the wall faces. A 0.1 x 0.03 ft grid of downward rays (under a roof: a ceiling or door
    head above) finds them; each find is then followed along its line in 0.1 ft steps, probing across it every
    0.005 ft, until the seam runs out (they taper to a hairline), and collinear finds are merged. Each seam gets
    a patch of the neighbouring floor's material 1/32 in below the finished floor."""
    import collections
    bvh, owner = _bvh({COLL_SHELL, COLL_OPEN, 'exterior_shell'})
    down = Vector((0, 0, -1))

    def probe(x, z):
        """(is exposed foundation, floor object or None, floor y)"""
        loc, _, i, _ = bvh.ray_cast(ft2bl(x, 1.0, z), down, 3 * FT)
        if loc is None:
            return False, None, None
        ob, y = owner[i], loc.z / FT
        if re.search(r'foundation', ob.name, re.I):
            up = bvh.ray_cast(ft2bl(x, 1.0, z), Vector((0, 0, 1)), 12 * FT)[0]
            return (-0.5 < y and up is not None and up.z / FT > 6.0), None, None
        return False, (ob if -0.005 < y < 0.2 else None), y

    hits = []
    x = 0.3
    while x < 39.6:
        z = 0.3
        while z < 54.0:
            if probe(x, z)[0]:
                hits.append((x, z))
            z += 0.03
        x += 0.1
    clusters = []
    for x, z in hits:
        for c in clusters:
            if any(abs(x - p[0]) < 0.25 and abs(z - p[1]) < 0.2 for p in c[-80:]):
                c.append((x, z))
                break
        else:
            clusters.append([(x, z)])
    seams = []
    for c in clusters:
        xs, zs = [p[0] for p in c], [p[1] for p in c]
        along_x = max(xs) - min(xs) >= max(zs) - min(zs)
        a0, a1 = (min(xs), max(xs)) if along_x else (min(zs), max(zs))
        b0, b1 = (min(zs), max(zs)) if along_x else (min(xs), max(xs))
        for sgn in (-1, 1):                                  # follow the seam past both ends
            t, miss = (a0 if sgn < 0 else a1), 0
            while miss < 3 and 0.0 < t < 55.0:
                t += 0.1 * sgn
                across = [b0 - 0.15 + k * 0.005 for k in range(int((b1 - b0 + 0.3) / 0.005) + 1)]
                found = [v for v in across if probe(*((t, v) if along_x else (v, t)))[0]]
                if found:
                    miss = 0
                    a0, a1 = min(a0, t), max(a1, t)
                    b0, b1 = min(b0, min(found)), max(b1, max(found))
                else:
                    miss += 1
        seams.append([along_x, a0, a1, b0, b1])
    merged = []
    for sm in sorted(seams, key=lambda v: (v[0], v[1])):
        m = merged[-1] if merged else None
        if m and m[0] == sm[0] and sm[1] <= m[2] + 0.3 and abs((sm[3] + sm[4]) - (m[3] + m[4])) / 2 < 0.15:
            m[2], m[3], m[4] = max(m[2], sm[2]), min(m[3], sm[3]), max(m[4], sm[4])
        else:
            merged.append(list(sm))
    out = []
    for k, (along_x, a0, a1, b0, b1) in enumerate(merged):
        x0, x1, z0, z1 = (a0, a1, b0, b1) if along_x else (b0, b1, a0, a1)
        nb = collections.Counter()
        for fx, fz in ((x0 - 0.1, (z0 + z1) / 2), (x1 + 0.1, (z0 + z1) / 2), ((x0 + x1) / 2, z0 - 0.1),
                       ((x0 + x1) / 2, z1 + 0.1), (x0 + 0.3, z0 - 0.08), (x1 - 0.3, z1 + 0.08)):
            _, ob, y = probe(fx, fz)
            if ob is not None:
                nb[(ob.name, round(y, 3))] += 1
        if not nb:
            continue
        (name, y), _ = nb.most_common(1)[0]
        src = bpy.data.objects[name]
        patch = ctx.box(f'Floor seam patch {k}', x0 - 0.06, x1 + 0.06, y - 0.1, y - 0.0026, z0 - 0.04, z1 + 0.04,
                        None, COLL_SHELL)
        if src.data.materials:
            patch.data.materials.append(src.data.materials[0])
        out.append((re.sub(r'^\d+ ', '', name)[:24], round(x0, 2), round(x1, 2), round(z0, 3), round(z1, 3)))
    return out


def apply(ctx):
    bpy.context.view_layer.update()
    res = {}
    for f in (ceiling_seam, floor_seam, bedroom4_flat, bay_to_floor, primary_slider, bedroom2_tall_window, bath_window, kitchen_skylight,
              foyer_skylights, primary_bath_skylight, entry_vault_closure, laundry_closet, floor_gaps, skirting_trim):
        try:
            res[f.__name__] = f(ctx)
        except Exception as e:                       # report, keep building
            import traceback
            traceback.print_exc()
            res[f.__name__] = f'FAILED: {e!r}'
        bpy.context.view_layer.update()
    return res
