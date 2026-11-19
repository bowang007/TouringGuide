"""Owner's design changes on the architect's plan (runs inside Blender, after bl/warp.py).

All coordinates are on the NEW plan (SCENE feet, x west->east, z rear->street). Each change works on
the built objects by name, so it survives re-runs of the build:

1. Bedroom 4 (the plan's office): flat 8 ft ceiling instead of the vault.
2. Front bedroom (tour "Bedroom 3", the plan's Bedroom #2): the canted bay is glazed down to the
   floor (plaster base, outside plinth and sills removed; glass, jambs and piers run to the floor).
3. Foyer: two skylights, on the entry roof's east slope (the ridge runs down the foyer's middle):
   one over the hall section, one in the vaulted entry.
4. Primary bedroom: the large rear window becomes a two-panel sliding door to the garden.
5. Bedroom 2 (next to the primary): its rear window runs floor to ceiling.
6. Primary bathroom: the west window runs floor to ceiling (clear glass, a transom at 6 ft), between
   the vanity and the shower; the linen cabinet that stood in front of it is gone.
7. Kitchen skylight: moved off the garage-gable ridge (where the old 4 x 3 ft unit straddled two roof
   planes) to the continuous east-facing roof plane over the sink / dishwasher run, 3'-6" x 4'-0"
   as on the architect's plan.
(8, the dining table in line with the island, is built by the kitchen zone.)

Second round (2026-11-19):
9. Primary bathroom: a 2'-0" x 2'-6" skylight over the shower.
10. The office / bedroom-3 foyer-side wall lines up with the shared bath's east wall: that is the
    conversion itself (relayout.FOYER_WALL); here only the office ceiling and the foyer skylights follow.

Repairs to the conversion run first: ceiling_seam and floor_seam close seams the slab warp opened.
"""
import math
import re

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .common import FT, ft2bl

COLL_SHELL, COLL_OPEN = 'shell', 'openings'

from .revision_spec import (BATH_WIN_Z, FOYER_SKY, KITCHEN_SKY, OFFICE_CEILING, PRIMARY_BATH_SKY,  # noqa: F401
                            SLIDER_HEAD, SLIDER_X)


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
    wc, _ = _world(cen[0])
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
    return {'edge': [(xa, za), (xb, zb)], 'west panel east edge': [old, new]}


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


def bedroom2_full_height(ctx):
    obs = find(r'^\d+ Bedroom 2 — rear wall$')
    gone = remove([ob for ob in obs if any(cc.name == COLL_SHELL for cc in ob.users_collection)
                   and (lambda b: b[0] > 14.3 and b[1] < 19.8 and (b[3] <= 2.6 or b[2] >= 6.9))(bbox(ob))])
    gone += remove([ob for ob in find(r'Painted skirting — Bedroom 2 — rear wall') if (lambda b: b[0] > 14.3 and b[1] < 19.8)(bbox(ob))])
    gone += remove(_sills(14.3, 19.8))
    k = 0
    for ob in find(r'^\d+ Bedroom 2 — rear wall$', COLL_OPEN):
        map_y(ob, [(2.5, 0.0), (2.6, 0.1), (6.9, 7.9), (7.0, 8.0)])
        k += 1
    return {'removed': gone, 'stretched': k}


def bath_window(ctx):
    z0, z1 = BATH_WIN_Z
    gone = remove(find(r'Primary bathroom west wall — (below|above) privacy window|Primary bathroom privacy-window|'
                       r'Primary bathroom operable awning|Primary bathroom obscured privacy glazing'))
    gone += remove(find(r'Painted skirting — Primary bathroom west wall — below'))
    gone += remove(find(r'^A0 (linen|succulent)'))
    gone += remove([ob for ob in find(r'^A0 tile west') if (lambda b: b[4] > 22.1 and b[5] < 24.95)(bbox(ob))])
    for ob in find(r'Primary bathroom west wall — north solid'):
        move_face(ob, 'z', 22.20, z0)
    for ob in find(r'Primary bathroom west wall — south solid'):
        move_face(ob, 'z', 24.89, z1)
    for ob in find(r'^A0 tile west'):
        b = bbox(ob)
        if b[5] < 22.3:
            move_face(ob, 'z', b[5], z0)
        elif b[4] > 24.8:
            move_face(ob, 'z', b[4], z1)
    xc, fd, fw = 0.0, 0.22, 0.12
    c = COLL_OPEN
    box(ctx, 'Primary bath tall window head', xc - fd / 2, xc + fd / 2, 8.0 - fw, 8.0, z0, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window sill', xc - fd / 2, xc + fd / 2, 0.0, 0.08, z0, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window jamb N', xc - fd / 2, xc + fd / 2, 0.0, 8.0, z0, z0 + fw, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window jamb S', xc - fd / 2, xc + fd / 2, 0.0, 8.0, z1 - fw, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window transom', xc - fd / 2, xc + fd / 2, 6.0, 6.1, z0, z1, 'black_aluminum', c)
    # clear glass: the side yard outside is fenced (6'-2") and screened by an evergreen (exterior_plants)
    g = box(ctx, 'Primary bath tall window lower glass', xc - 0.015, xc + 0.015, 0.08, 6.0, z0 + fw, z1 - fw, 'glass_clear', c)
    g.visible_shadow = True
    g2 = box(ctx, 'Primary bath tall window upper glass', xc - 0.015, xc + 0.015, 6.1, 8.0 - fw, z0 + fw, z1 - fw, 'glass_clear', c)
    g2.visible_shadow = True
    return {'removed': gone}


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


def apply(ctx):
    bpy.context.view_layer.update()
    res = {}
    for f in (ceiling_seam, floor_seam, bedroom4_flat, bay_to_floor, primary_slider, bedroom2_full_height, bath_window, kitchen_skylight,
              foyer_skylights, primary_bath_skylight, entry_vault_closure):
        try:
            res[f.__name__] = f(ctx)
        except Exception as e:                       # report, keep building
            import traceback
            traceback.print_exc()
            res[f.__name__] = f'FAILED: {e!r}'
        bpy.context.view_layer.update()
    return res
