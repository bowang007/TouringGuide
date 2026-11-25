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
   planes) to the continuous east-facing roof plane over the sink / dishwasher run. (3'-6" x 4'-0" until the
   seventh round; 1'-10" x 3'-10", the size the architect's plan draws, since the eighth: see "v7 roof" below.
   v7 final: its east edge where the 3'-6" opening's stood, so it lies over the sink: revision_spec.KITCHEN_SKY.)
(8, the dining table in line with the island, is built by the kitchen zone.)

Second round (2026-11-19):
9. Primary bathroom: a 2'-0" x 2'-6" skylight over the shower.
10. The office / bedroom-3 foyer-side wall lines up with the shared bath's east wall: that is the
    conversion itself (relayout.FOYER_WALL); here only the office ceiling and the foyer skylights follow.

Third round (2026-11-19): 5 and 6 stop at a 2'-0" sill (revision_spec.TALL_SILL) instead of the floor.

Fourth round (2026-11-19, corrected by the owner on 2026-11-20):
11. Laundry closet carved out of Bedroom 4's north-east corner, opening east onto the foyer (revision_spec.LAUNDRY_*):
    2'-10" wide x 3'-0" deep inside. A 2'-6" x 6'-8" opening is cut into the Bedroom 4 / foyer wall and gets a pair of
    narrow leaves that stand wide open against the foyer wall; two new full-height walls (west, south) close it off
    from the bedroom; jamb liners, head trim, hinges, pulls, an oak threshold, baseboards on every face, a flush
    ceiling light, a recessed outlet box in the back wall and a stacked washer / dryer facing east (bl/laundry.py).
    Bedroom 4 is L-shaped after it; its desk moved into the niche beside the closet (bl/zones/bedrooms.py), which also
    hangs the picture and the hook rail on the closet's bedroom faces. (The first attempt built the closet in the
    kitchen's south-west corner; the owner rejected it and nothing of it is left.)

Sixth round (2026-11-20), the primary bath on the architect's sheet (revision_spec.BATH_* / PRIMARY_BATH_*; until
the fifth round the room was mirrored north-south):
12. bath_door: door D08 moves to the east end of the north wall, hinged on the east jamb, its leaf open against the
    east wall; the recess for the shower niche is cut into the same wall. bath_window (6): W13 at the sheet's place,
    3'-0" wide, with a mullion on the shower's south glass line. primary_bath_skylight (9): W20 over the shower in the
    north-west corner. primary_bath_fit_out: the room's finishes and fixtures, built after the warp in plan feet by
    bl/zones/baths_primary.build_room.
13. suite_rooms / suite_fit_out (revision_spec.SUITE_*): the 8 ft zone between the primary bedroom and the bath is
    divided as on the sheet. The walk-in closet is an enclosed room (6'-1" x 8'-0") behind a new 5 in wall with a
    sliding pocket door centred on it (the leaf slides south and stands 0.30 ft out of its pocket); the vestibule
    (4'-7" x 8'-0") is open to the bedroom and carries the attic access hatch; the suite entry (D09) is a 2'-8"
    opening with a sliding panel on the hall side, parked south. Geometry: bl/zones/primary_suite_rooms.py; the
    bedroom's furniture as drawn, the vestibule and the closet's fit-out: bl/zones/primary_suite.fit_out, in plan
    feet. (Until the seventh round the suite entry stood 1.66 ft south of the sheet's place, beside Bedroom 2's
    entry alcove; since the eighth it is at revision_spec.SUITE_ENTRY_SHEET_Z, see 19, hall_block.)
14. bedroom3_bath_window (revision_spec.BED3_BATH_WIN_*): the Bedroom 3 bathroom's shower window W11 is taller,
    sill 3'-0", head 7'-6" (was 5'-0" / 7'-0"); width, place, frosted glazing and frame as before; the tile around
    it, the tiled jamb returns and the quartz sill are the baths zone's (bl/zones/baths.py, build_suite3).

Seventh round (2026-11-21), the owner: "Set all windows to white color, and it should have grid line for these
windows":
15. white_windows (revision_spec.WINDOW_*), the last step of all: every window and glazed door of the built model
    (since the eighth round: the windows W01, W02, W05, W07..W09, W11..W15, W17, the two sliding glass doors and the
    front door's two sidelights; the garden door D14 and W03 / W04 / W06 / W10 are gone; the five skylights keep
    their frames) gets satin white frames, sashes,
    mullions and transom bars and a grid of white bars on both faces of the glass, lites as close to 14 x 16 1/2 in
    as each sash allows; the kitchen's W08 keeps 2 x 4 lites per sash; two centre mullions go back to the middle
    of their windows; roller shades are seated on the room side of the bars; the primary bedroom slider's pull
    is white too. (The same round's refrigerator, living room and primary bath are the zones' own work, and the
    sky that stood 180 degrees off the sun is bl/lighting.py.)

Repairs to the conversion run first: ceiling_seam and floor_seam close seams the slab warp opened; floor_overlap
and ceiling_overlap end two slabs on one line where they overlapped in one plane (coplanar faces of two objects
shade each other: a dark stripe on the floor across Bedroom 4 and the foyer, a dark rectangle on the foyer's
ceiling, both in front of the laundry closet); foyer_corner fills the notch in the wall corner between the foyer
and the kitchen's pantry wall and the bare strip of floor at its foot.

Eighth round (2026-11-23/24), the model on the architect's sheet SKA002 (each step's own docstring has the detail;
the numbers are those docstrings' numbers, the order is apply()'s):
*   v7 glazing: primary_slider (4) and bedroom2_tall_window (5) at the sheet's widths, living_slider (one four-panel
    sliding door in place of the garden door and the two fixed lights), primary_west_window (W15),
    living_east_windows (W05, W07). v7 final: primary_west_window_south gives W14, the owner's second west window,
    the same unit as W15.
*   v7 roof: roof_v7 (bl/roof.py), the sheets' roof, every plane 5 in 12, with Bedroom 3's vault and the entry vault
    under it; it runs before the skylights, which cut their wells through it. living_skylight: the sheet's skylight
    over the living room (W21, the fifth).
16. bedrooms_west_windows: Bedroom 4's west window W12 at 5'-0", Bedroom 3's west window W10 closed.
17. bedroom3_rooms: the wall between Bedroom 3 and its bath / closet, Bedroom 3's and Bedroom 4's entries.
18. bedroom3_fit_out (bl/zones/bedrooms_rooms.py, baths_suite3.py): Bedroom 3's bath and closet fitted out.
19. hall_block (bl/zones/hall_block.py): Bedroom 2's closet block and the hall beside it, the furnace and storage
    closets, the shared bath's door.
20. hall_block_fit_out: Bedroom 2's closet and the hall fitted out.
*   v7 garage: garage_v7 (bl/garage.py), the garage's lowered floor, step and doors, the front door unit, the water
    heater. v7 site: site_shell, the shell pieces that meet the ground work.

Five general repairs run last, after every change has cut or moved walls and slabs, in this order: floor_level (two
floor pieces that stood 0.008 ft proud of the oak floor), floor_gaps (thin floor seams and the bare strips under door
openings), living_east_baseboard (the house baseboard behind the living room's own on its east wall), skirting_trim
(baseboards cut back to the walls behind them) and skirting_joints (the gaps between baseboard runs on one wall).
white_windows (15) alone runs after them.
(v7 final: comment; it named two repairs and had no entry for the eighth round.)
"""
import math
import re

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .common import FT, ft2bl

COLL_SHELL, COLL_OPEN = 'shell', 'openings'

from .revision_spec import (BATH_OLD_HOLE_Y, BATH_WIN_Z, BED2_WIN_X, FOYER_CORNER_INFILL, FOYER_SKY,  # noqa: F401
                            KITCHEN_CEILING, KITCHEN_SKY, LAUNDRY_CEILING,
                            LAUNDRY_CLEAR, LAUNDRY_DOOR_HEAD, LAUNDRY_DOOR_LINER, LAUNDRY_DOOR_LINER_PROUD,
                            LAUNDRY_DOOR_Z, LAUNDRY_HOOKUP_RECESS, LAUNDRY_HOST_WALL, LAUNDRY_HOST_WALL_X,
                            LAUNDRY_THRESHOLD_Y, LAUNDRY_WALL_T, OFFICE_CEILING, PRIMARY_BATH_SKY, REAR_WALL_C, SLIDER_HEAD,
                            SLIDER_X, TALL_SILL, WEST_WALL_C, R, laundry_leaves, laundry_walls)


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
    # v7 repair: the ceiling's surface at the lining's OUTER corners too (before anything is cut), so the lining's
    # foot follows a sloping ceiling over its whole thickness (the entry vault; 8.0 on the flat ceilings)
    ceil_o = [ceiling_y(x, z) for x, z in ((x0 - pad, z0 - pad), (x1 + pad, z0 - pad), (x1 + pad, z1 + pad), (x0 - pad, z1 + pad))]
    ceil_o = [co if abs(co - ci) < 0.2 else ci for co, ci in zip(ceil_o, ceil)]
    y_lo = min(ceil + ceil_o) - 0.05
    # cut: everything between the ceiling and the sky over the opening
    # v7 repair: the ceiling and whatever stands above it are cut to the lining's OUTER outline, like the roof (below).
    # Cut to the clear well, the ceiling slab ran on under the four linings: the linings' feet lay in the plane of
    # the ceiling's underside (a ring 0.12 ft wide round every well) and the slab's cut faces in the plane of the
    # linings' inner faces: two surfaces in one plane, which rendered as dark wedges and streaks round the wells.
    cutter = ctx.box(f'{name} cutter', x0 - pad, x1 + pad, y_lo, max(roof) + 3.0, z0 - pad, z1 + pad, None, COLL_OPEN)
    targets, roofs = [], []
    rx = re.compile(cut_ceiling_pat, re.I)
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob is cutter or not len(ob.data.vertices):
            continue
        cols = {c.name for c in ob.users_collection}
        if not (cols & {COLL_SHELL, 'exterior_shell', COLL_OPEN}) and not any(c.startswith('zone_') for c in cols):
            continue
        b = bbox(ob)
        if not _overlap(b, x0 - pad, x1 + pad, z0 - pad, z1 + pad, y_lo, max(roof) + 3.0):     # v7 repair: outer outline
            continue
        is_roof = 'exterior_shell' in cols and not re.search(r'stucco', ob.name, re.I)
        if is_roof and re.match(r'v7 roof (cap|flashing)', ob.name):         # v7 roof: open strips lying on the planes
            continue
        is_ceiling = bool(rx.search(ob.name))
        attic = b[2] >= y_lo - 0.01 and (COLL_SHELL in cols or is_roof)      # infill / knee walls above
        if is_roof:
            roofs.append(ob)
        elif is_ceiling or attic:
            targets.append(ob)
    n = _cut(targets, cutter)
    # v7 roof: the roof is a slab 6 1/2 in thick now (bl/roof.py), not a sheet. Its hole is the lining's OUTER outline,
    # so the lining stands in the hole and the slab's cut faces lie behind it (cut to the inner outline they would lie
    # in the plane of the lining's faces: two surfaces in one plane all round the well).
    # (v7 repair: one cutter for the ceilings and the roof now, both on the outer outline)
    if roofs:
        n += _cut(roofs, cutter)
    bpy.data.objects.remove(cutter, do_unlink=True)
    # lining: four walls from the ceiling surface up to 0.25 ft above the roof
    top = [r + 0.25 for r in roof]
    inner = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    outer = [(x0 - pad, z0 - pad), (x1 + pad, z0 - pad), (x1 + pad, z1 + pad), (x0 - pad, z1 + pad)]
    for i in range(4):
        j = (i + 1) % 4
        # v7 repair: the foot is the only surface in the ceiling's plane over the ring (ceil_o at the outer corners)
        lo = [(*_xz(inner[i], ceil[i]),), (*_xz(inner[j], ceil[j]),), (*_xz(outer[j], ceil_o[j]),), (*_xz(outer[i], ceil_o[i]),)]
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
    # v7 roof: curb flashing. The lining stands 0.25 ft out of the roof as the curb; a skirt of the roof's metal
    # wraps it from inside the roof slab up to the frame, so no white lining shows on the roof and the joint
    # between curb and roofing is covered.
    fl = 0.03
    skirt = [(x0 - pad - fl, z0 - pad - fl), (x1 + pad + fl, z0 - pad - fl), (x1 + pad + fl, z1 + pad + fl), (x0 - pad - fl, z1 + pad + fl)]
    for i in range(4):
        j = (i + 1) % 4
        lo = [_xz(outer[i], roof[i] - 0.2), _xz(outer[j], roof[j] - 0.2), _xz(skirt[j], roof[j] - 0.2), _xz(skirt[i], roof[i] - 0.2)]
        hi = [_xz(outer[i], top[i]), _xz(outer[j], top[j]), _xz(skirt[j], top[j]), _xz(skirt[i], top[i])]
        _slab(f'{name} curb flashing {i}', lo, hi, 'roof_metal', COLL_OPEN, ctx)
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
    # hairline open to the attic along the ceiling at the hall end of the kitchen's pantry wall (found with a fine ray
    # scan; check_holes' 0.2 ft grid is too coarse to see it). Slide the west corner along the panel's own west edge
    # to the east corner's z:
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
        fw, fe, b3n = R.X_FOYER_W, R.X_FOYER_E, R.Z_B3_N       # the foyer's two wall faces, Bedroom 3's north face
        row = [o for o, b in pieces if b[1] > fe - 0.2 and b[4] < R.Z_GAR_N and b3n + 0.8 < b[5] < b3n + 2.3]
        west = [b for o, b in pieces if b[1] < fw + 0.05 and b3n + 0.1 < b[4] < b3n + 0.9]
        hall = find(rf'^\d* ?{front}$')
        if len(row) != 1 or len(west) != 1 or len(hall) != 1:
            out[fam] = f'not found ({len(row)}, {len(west)}, {len(hall)})'
            continue
        z = west[0][4]
        out[fam] = {'seam z': round(z, 3),
                    'row front verts': _set_z(row[0], lambda v: v > b3n + 0.1, z),
                    'foyer slab rear verts': _set_z(hall[0], lambda v: v < b3n + 2.3, z)}
    return out


def floor_overlap(ctx):
    """Corner mapping once more, in the floor: the oak slab under the bedroom-4 / foyer row had its north edge on a
    line from z 30.72 (west wall) to 30.84 (garage wall), the slab north of it has its south edge on a line from 30.72
    to 31.24 across the whole house. Between the two lines both slabs lay in one plane, a wedge up to 0.16 ft wide
    that crosses Bedroom 4 and the foyer and ends in front of the laundry closet's doors. Two coplanar faces of
    different objects shade each other, so the wedge rendered as a darker stripe on the floor (and would flicker in
    the web model). The row slab's north edge is put on the north slab's south edge: the two meet on one line, each
    stretch of floor is one surface at one height (the oak material is mapped in world space, so the planks run
    through). floor_gaps, which runs last, would patch the joint from below if it ever opened."""
    pieces = [(o, bbox(o)) for o in find(r'^\d* ?Oak floor substrate$', COLL_SHELL)]
    # (the row slab ends in the garage's west wall and starts about 2 ft south of Bedroom 4's north face; the north
    # slab runs to the east wall, from the old front wall to the kitchen / garage wall)
    row = [o for o, b in pieces if R.X_FOYER_E - 0.2 < b[1] < R.X_GAR_W + 0.05 and R.Z_B4_N + 1.6 < b[4] < R.Z_B4_N + 2.3
           and b[5] > R.Z_B3_N - 0.2]
    north = [o for o, b in pieces if b[1] > R.X_LIV_E - 0.2 and R.Z_PBATH_S - 0.1 < b[4] < R.Z_B4_N
             and R.Z_KIT_S - 0.05 < b[5] < R.Z_GAR_N + 0.03]
    if len(row) != 1 or len(north) != 1:
        return f'slabs not found ({len(row)}, {len(north)})'
    top = bbox(row[0])[3]
    if abs(top - bbox(north[0])[3]) > 1e-4:
        return {'row slab top': round(top, 4), 'north slab top': round(bbox(north[0])[3], 4), 'verts': 0}
    wn, _ = _world(north[0])
    nx, nz = wn[:, 0] / FT, -wn[:, 1] / FT
    xw, xe = float(nx.min()), float(nx.max())           # the north slab's south edge: its west and east front corners
    zw, ze = float(nz[np.abs(nx - xw) < 1e-3].max()), float(nz[np.abs(nx - xe) < 1e-3].max())
    wr, mr = _world(row[0])
    rx, rz = wr[:, 0] / FT, -wr[:, 1] / FT
    edge = rz < rz.min() + 0.5                          # the row slab's north edge (its south edge is 12 ft away)
    target = zw + (ze - zw) * (rx[edge] - xw) / (xe - xw)
    old = sorted({(round(float(p), 3), round(float(q), 3)) for p, q in zip(rx[edge], rz[edge])})
    if len(wr) != 8 or int(edge.sum()) != 4 or float(np.abs(target - rz[edge]).max()) > 0.5:
        return {'row slab north edge': old, 'verts': 0}
    wr[edge, 1] = -target * FT
    _set_world(row[0], wr, mr)
    new = sorted({(round(float(p), 3), round(float(q), 3)) for p, q in zip(rx[edge], target)})
    return {'row slab north edge': [old, new], 'verts': int(edge.sum())}


def ceiling_overlap(ctx):
    """The same thing overhead: the original house's central ceiling panel reaches south to the kitchen / garage
    wall's centre line (z 31.24) across the foyer's whole width, and the bedroom-hall ceiling starts at the old front
    wall (z 28.54), so over the foyer's north end, right in front of the laundry closet, the two undersides lay in
    one plane for 2.7 ft. It rendered as a darker rectangle with sharp edges on the ceiling (found with a ray scan
    for coplanar first surfaces and seen in the stills). The bedroom-hall ceiling now starts on the central panel's
    front edge, so each stretch of ceiling is one surface. Runs after ceiling_seam, which squares that front edge,
    and before the skylight cuts, while the hall ceiling is still a plain prism. (The 0.02 ft the central panel's
    skewed west edge leaves uncovered lies on the Bedroom 4 / foyer wall's centre line, inside the wall.)"""
    cen = find(r'^\d* ?Original house ceiling central panel', COLL_SHELL)
    hall = find(r'^\d* ?Bedroom hall flat ceiling', COLL_SHELL)
    if len(cen) != 1 or len(hall) != 1:
        return f'panels not found ({len(cen)}, {len(hall)})'
    wc, _ = _world(cen[0])
    cx, cz = wc[:, 0] / FT, -wc[:, 1] / FT
    front = float(cz.max())
    fx = cx[np.abs(cz - front) < 2e-3]                 # the front edge's ends (one corner only if it is still skewed)
    hb, cb = bbox(hall[0]), bbox(cen[0])
    out = {'central panel front': [round(float(fx.min()), 3), round(float(fx.max()), 3), round(front, 3)],
           'hall ceiling was z': [round(hb[4], 3), round(hb[5], 3)]}
    wh, _ = _world(hall[0])
    north = -wh[:, 1] / FT < front - 1e-3
    ok = (abs(hb[2] - cb[2]) < 1e-4 and len(wh) == 8 and int(north.sum()) == 4 and hb[5] > front + 1.0
          and fx.min() < hb[0] + 0.1 and fx.max() > hb[1] - 1e-3)
    if not ok:                                         # not the situation described above: leave it alone, say so
        out['verts'] = 0
        return out
    out['verts'] = _set_z(hall[0], lambda v: v < front - 1e-3, front)
    return out


def foyer_corner(ctx):
    """Outside corner where the foyer's east wall (the garage's west wall) turns into the kitchen's south wall: each
    wall stops on the other's centre line, which leaves a square notch (revision_spec.FOYER_CORNER_INFILL), floor to
    ceiling, beside the refrigerator's end panel, with the two baseboards bridging it in the air. Fill it with a
    copy of the garage wall (same paint, same `scene_index`, so it bakes as a wall). The first laundry closet
    (2026-11-19, in this corner) had closed it; the closet left, the notch came back."""
    def one(pat):
        obs = [o for o in find(pat, COLL_SHELL) if o.type == 'MESH' and len(o.data.vertices) == 8]
        return obs[0] if len(obs) == 1 else None
    west = one(r'^\d+ Garage interior access — north infill wall$')
    south = one(r'^\d+ Kitchen / garage separation$')
    if west is None or south is None:
        return f'walls not found ({west is not None}, {south is not None})'
    wb, sb = bbox(west), bbox(south)
    x0, x1, z0, z1 = wb[0], sb[0], sb[4], wb[4]         # foyer face .. kitchen wall's end, kitchen face .. garage wall's end
    if max(abs(a - b) for a, b in zip((x0, x1, z0, z1), FOYER_CORNER_INFILL)) > 0.02 or x1 - x0 < 0.01 or z1 - z0 < 0.01:
        return {'notch': [round(v, 3) for v in (x0, x1, z0, z1)], 'expected': list(FOYER_CORNER_INFILL), 'built': False}
    ob = _like(west, 'Foyer corner infill (garage west wall / kitchen wall)', x0, x1, wb[2], wb[3], z0, z1)
    _paint_all(ob)
    out = {'notch': [round(v, 3) for v in (x0, x1, z0, z1)], 'y': [round(wb[2], 3), round(wb[3], 3)], 'built': True}
    # The floor at the foot of that corner: the oak slab's skewed south edge (see floor_overlap) stops up to 0.06 ft
    # short of the kitchen wall's face from the foyer row slab's east edge (x1) to about x 25.8, so the foundation
    # showed as a dark line under the baseboard between the corner and the refrigerator's end panel (further east
    # the cabinets stand on it). floor_gaps cannot see it: its probes land on the baseboard. One patch of the same
    # oak, 1/32 in below the finished floor like floor_gaps' patches, under the slab's edge, the baseboard and the wall.
    slabs = [o for o in find(r'^\d+ Oak floor substrate$', COLL_SHELL)
             if _overlap(bbox(o), x1 + 0.2, x1 + 0.4, z0 - 0.5, z0 - 0.3)]
    if slabs:
        fy = max(bbox(o)[3] for o in slabs)
        px0, px1, pz0, pz1 = x1 - 0.06, x1 + 4.6, z0 - 0.12, z0 + 0.03
        patch = ctx.box('Floor seam patch kitchen corner', px0, px1, fy - 0.1, fy - 0.0026, pz0, pz1, None, COLL_SHELL)
        if slabs[0].data.materials:
            patch.data.materials.append(slabs[0].data.materials[0])
        out['floor patch'] = [round(v, 3) for v in (px0, px1, pz0, pz1)]
    return out


# ---------------------------------------------------------------------------------- changes
def bedroom4_flat(ctx):
    n = remove(find(r'Bedroom 4 vaulted ceiling|Bedroom 4 gable infill'))
    cx0, cx1, cz0, cz1 = OFFICE_CEILING
    box(ctx, 'Bedroom 4 flat ceiling', cx0, cx1, 8.0, 8.12, cz0, cz1, 'paint_ceiling', COLL_SHELL)
    # The vault's cans sat on the slope above the new ceiling: drop them (the pendant lights the room).
    n += remove([ob for ob in find(r'^slope can')
                 if (lambda b: b[1] < OFFICE_CEILING[1] + 0.3 and OFFICE_CEILING[2] < b[4] and b[5] < OFFICE_CEILING[3])(bbox(ob))])
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
            if 'tall sash glass' in ob.name:
                # v7 repair: the panes stopped 0.44 in above the bottom rail (rail top 0.092, glass from 0.13) and
                # short of the head (glass to 7.37, top rail 7.408..7.493, top band from 7.5): unglazed slits along
                # all three sashes. The glass runs into the bottom rail and up through the top rail into the band.
                move_face(ob, 'y', 0.13, 0.05)
                move_face(ob, 'y', 7.37, 7.52)
        k += 1
    return {'removed': n, 'extended': k}


def primary_slider(ctx):
    """4. The primary bedroom's sliding glass door in the rear wall. v7 glazing (eighth round): the wall opening is
    the sheet's, 6'-4" at x 2.439..8.772 (revision_spec.SLIDER_X; 6'-0" clear between the frames), and the door is
    built like the living room's (_glz_slider): a fixed west panel on the room-side track, the sliding east panel on
    the outer one, closed. It was 6'-7 13/16" wide at x 2.450..9.100 with 0.14 ft frames."""
    from . import revision_spec as RS
    x0, x1 = SLIDER_X
    out = _glz_opening(r'^\d+ Primary — rear wall$', r'Painted skirting — Primary — rear wall', r'^\d+ Primary — rear wall$',
                       'x', R.ZN, x0, x1, 0.0, SLIDER_HEAD, 'primary sliding door')
    out['sills removed'] = remove(_sills(out['was'][0] - 0.1, out['was'][1] + 0.1))
    out['overlay baseboards split'] = _glz_split_runs(r'^\d+ Primary rear — (painted baseboard|baseboard top reveal)$', 'x', x0, x1)
    out['door'] = _glz_slider(ctx, 'Primary slider', (x0, x1), SLIDER_HEAD, RS.slider_panels((x0, x1), 2))
    return out


def bedroom2_tall_window(ctx):
    """5. Bedroom 2's rear window W02 runs from a 2'-0" sill (TALL_SILL, third round) up to the 8 ft ceiling (owner).
    v7 glazing (eighth round): it is 6'-0" wide at the sheet's place, x 13.923..19.923
    (revision_spec.BED2_REAR_WIN_X; the concept's window, carried over by the warp, was 5'-3 13/16" at
    x 14.456..19.772). The wall is re-cut, the window rebuilt in plan feet (_glz_window), and the room's ceiling-track
    drapes are set to the new jambs (revision_spec.BED2_DRAPE)."""
    from . import revision_spec as RS
    a0, a1 = RS.BED2_REAR_WIN_X
    pat = r'^\d+ Bedroom 2 — rear wall$'
    out = _glz_opening(pat, r'Painted skirting — Bedroom 2 — rear wall', pat, 'x', R.ZN, a0, a1, TALL_SILL, 8.0,
                       'rear window W02')
    out['sills removed'] = remove(_sills(out['was'][0] - 0.1, out['was'][1] + 0.1))
    out['window'] = _glz_window(ctx, 'Bedroom 2 rear window W02', 'x', REAR_WALL_C, a0, a1, TALL_SILL, 8.0)
    # the drapes (bl/zones/bedrooms.py builds them on the concept plan; the warp carries them rigidly with the room's
    # furniture): one stack each side, covering the glass by BED2_DRAPE['over'] from the jamb
    d = RS.BED2_DRAPE
    parts = {k: [o for o in find(rf'^B2 drape {k}$') if o.type == 'MESH'] for k in ('track', 'left drape', 'right drape')}
    if all(len(v) == 1 for v in parts.values()):
        spans = {'left drape': (a0 + d['over'] - d['stack'], a0 + d['over']),
                 'right drape': (a1 - d['over'], a1 - d['over'] + d['stack'])}
        spans['track'] = (spans['left drape'][0] - d['track_past'], spans['right drape'][1] + d['track_past'])
        for k, (u0, u1) in spans.items():
            _glz_fit_x(parts[k][0], u0, u1)
        out['drapes'] = {k: [round(v, 3) for v in s] for k, s in spans.items()}
    else:
        out['drapes'] = 'zone bedrooms not built: skipped'
    return out


# ============================================================================================ v7 glazing
# Eighth round (2026-11-24), stage B, track "glazing": the rear and east openings and the primary bedroom's west
# window W15 at the sheet's widths and places (revision_spec, "v7 glazing"; audit F13, F14, F16, F17, F20, F21).
# primary_slider and bedroom2_tall_window above use these helpers too. Everything is rebuilt in plan feet after the
# warp: the wall is re-cut between the two solid pieces that flank the old opening, the old unit goes, and the new
# one is built on the sheet's numbers. Frame members are built in the frames' black aluminium and the panes in
# `glass_clear`, all in `openings`: white_windows, the last revision, makes them white and gives them their grid.
def _glz_wall(pat, axis, a0, a1, y0, y1, label):
    """Re-cut an exterior wall for the opening a0..a1 along `axis` ('x': the rear wall, 'z': the west / east wall)
    from the height y0 to y1. `pat` names the wall's shell pieces (plain boxes: full-height solids, and the pieces
    below and above the old windows). The full-height piece that starts before a0 and the one that ends after a1
    take the new jambs; every piece between them goes; the wall below y0 and above y1 is a copy of the first (same
    paint inside, stucco outside, same `scene_index`: it bakes as a wall). Returns the old opening (`was`), the
    wall's `span` along the axis and its two faces (`across`)."""
    k0, k1, c0, c1 = (0, 1, 4, 5) if axis == 'x' else (4, 5, 0, 1)
    pcs = [(o, bbox(o)) for o in find(pat, COLL_SHELL)
           if o.type == 'MESH' and len(o.data.vertices) == 8 and not SKIRT.search(o.name)]
    full = [(o, b) for o, b in pcs if b[2] < 0.01 and b[3] > 7.9]
    left = [p for p in full if p[1][k0] < a0 - 0.02]
    right = [p for p in full if p[1][k1] > a1 + 0.02]
    if not left or not right:
        raise RuntimeError(f'{label}: no solid wall piece {"before" if not left else "after"} {a0:.3f}..{a1:.3f} ({pat!r})')
    lo, lb = max(left, key=lambda p: p[1][k0])
    ro, rb = min(right, key=lambda p: p[1][k1])
    if lo is ro or lb[k1] > rb[k0] + 0.01 or max(abs(lb[c0] - rb[c0]), abs(lb[c1] - rb[c1])) > 0.01:
        raise RuntimeError(f'{label}: the wall is not where the spec expects it: {[round(float(v), 3) for v in lb + rb]}')
    n = remove([o for o, b in pcs if o is not lo and o is not ro and b[k0] > lb[k1] - 0.02 and b[k1] < rb[k0] + 0.02])
    move_face(lo, axis, lb[k1], a0)
    move_face(ro, axis, rb[k0], a1)
    base = re.sub(r'^\d+ ', '', lo.name)
    for nm, ya, yb in (('below', lb[2], y0), ('above', y1, lb[3])):
        if yb - ya > 0.01:
            b = (a0, a1, ya, yb, lb[4], lb[5]) if axis == 'x' else (lb[0], lb[1], ya, yb, a0, a1)
            _like(lo, f'{base} ({nm} the {label})', *b)
    return {'was': (round(float(lb[k1]), 3), round(float(rb[k0]), 3)), 'opening': (round(a0, 3), round(a1, 3)),
            'y': (y0, y1), 'wall pieces removed': n, 'span': (float(lb[k0]), float(rb[k1])),
            'across': (float(lb[c0]), float(lb[c1]))}


def _glz_skirting(pat, axis, face, span, a0, a1, to_floor):
    """The baseboard runs named by `pat` on the wall's room face (`face`) between span[0] and span[1]: the first
    and the last keep their far ends; a run between them (under the old window, on an old pier) goes. Under a
    window the first runs on to the far jamb, where the last begins; at an opening down to the floor they end on
    its two edges. (skirting_trim, which runs later, checks every run against the wall behind it.)"""
    k0, k1, c0, c1 = (0, 1, 4, 5) if axis == 'x' else (4, 5, 0, 1)
    runs = []
    for o in find(pat, COLL_SHELL):
        if o.type != 'MESH' or len(o.data.vertices) != 8 or not SKIRT.search(o.name):
            continue
        b = bbox(o)
        if abs((b[c0] + b[c1]) / 2 - face) < 0.09 and b[k1] > span[0] + 0.05 and b[k0] < span[1] - 0.05:
            runs.append((b[k0], o))
    runs.sort(key=lambda t: t[0])
    if len(runs) < 2:
        return {'runs': len(runs)}
    first, last = runs[0][1], runs[-1][1]
    n = remove([o for _, o in runs[1:-1]])
    move_face(first, axis, bbox(first)[k1], a0 if to_floor else a1)
    move_face(last, axis, bbox(last)[k0], a1)
    return {'runs': 2, 'removed': n, 'ends': [round(float(bbox(first)[k1]), 3), round(float(bbox(last)[k0]), 3)]}


def _glz_opening(walls, skirts, opens, axis, face, a0, a1, y0, y1, label):
    """_glz_wall for the new opening, then the old unit's pieces in `openings` (named by `opens`, standing in the old
    opening) and the baseboards (_glz_skirting)."""
    out = _glz_wall(walls, axis, a0, a1, y0, y1, label)
    k = 0 if axis == 'x' else 4
    lo, hi = out['was']
    out['old pieces removed'] = remove([o for o in find(opens, COLL_OPEN) if o.type == 'MESH'
                                        and (lambda b: lo - 0.25 < (b[k] + b[k + 1]) / 2 < hi + 0.25)(bbox(o))])
    out['baseboards'] = _glz_skirting(skirts, axis, face, out['span'], a0, a1, y0 < 0.01)
    return out


def _glz_fit_x(ob, u0, u1):
    """Set a mesh object's extent along x to u0..u1 (its vertices are spread in proportion)."""
    w, mw = _world(ob)
    x = w[:, 0] / FT
    lo, hi = float(x.min()), float(x.max())
    w[:, 0] = (u0 + (x - lo) / max(hi - lo, 1e-9) * (u1 - u0)) * FT
    _set_world(ob, w, mw)


def _glz_split_runs(pat, axis, a0, a1):
    """A baseboard run (named by `pat`) that crosses an opening down to the floor becomes two runs that end on the
    opening's edges. (skirting_trim would keep only the first stretch of such a run: it cuts the copy of a piece it
    has already cut, which is why the primary bedroom's second baseboard ended at the sliding door until now.)"""
    k0, k1, k = (0, 1, 0) if axis == 'x' else (4, 5, 1)
    sgn = 1.0 if axis == 'x' else -1.0
    n = 0
    for o in find(pat, COLL_SHELL):
        if o.type != 'MESH' or not SKIRT.search(o.name):
            continue
        b = bbox(o)
        if b[k0] < a0 - 0.05 and b[k1] > a1 + 0.05:
            for ob, lo, hi in ((_copy(o, f'{o.name} (beyond the opening)'), a1, b[k1]), (o, b[k0], a0)):
                w, mw = _world(ob)
                w[:, k] = sgn * np.clip(sgn * w[:, k] / FT, lo, hi) * FT
                _set_world(ob, w, mw)
            n += 1
    return n


def _glz_box(ctx, name, axis, u0, u1, y0, y1, n0, n1, mat='black_aluminum', bevel=0.0):
    """Box given along the wall (u), up (y) and through it (n), for a wall that runs along `axis`."""
    b = (u0, u1, y0, y1, n0, n1) if axis == 'x' else (n0, n1, y0, y1, u0, u1)
    return ctx.box(name, *b, mat, COLL_OPEN, bevel=bevel, segments=2)


def _glz_window(ctx, name, axis, wc, a0, a1, y0, y1, stool=None, mullion=None):
    """A two-sash window in the wall opening a0..a1 (along `axis`), y0..y1, on the wall's centre line `wc`
    (revision_spec.GLAZING_WIN_*): a frame as deep as the wall, standing 0.015 ft proud of both faces like the
    shell's window heads and sills (so no wall end shows in the reveals), and inside it the two sashes' stiles and
    rails with one mullion (their meeting stiles: in the middle, or on the line `mullion`) and a pane each, let
    0.008 ft into the sash. `stool`: a painted stool under the sill (revision_spec.GLAZING_STOOL), given with the
    room's side (+1 / -1 along n)."""
    from . import revision_spec as RS
    f, s, sd, m = RS.GLAZING_WIN_FRAME, RS.GLAZING_WIN_SASH, RS.GLAZING_WIN_SASH_D, RS.GLAZING_WIN_MULLION
    d0, d1 = wc - R.WALL / 2 - 0.015, wc + R.WALL / 2 + 0.015
    bx = lambda nm, *b, **kw: _glz_box(ctx, f'{name} {nm}', axis, *b, **kw)   # noqa: E731
    bx('frame head', a0, a1, y1 - f, y1, d0, d1)
    bx('frame sill', a0, a1, y0, y0 + f, d0, d1)
    bx('frame jamb a', a0, a0 + f, y0 + f, y1 - f, d0, d1)
    bx('frame jamb b', a1 - f, a1, y0 + f, y1 - f, d0, d1)
    i0, i1, j0, j1 = a0 + f, a1 - f, y0 + f, y1 - f                    # inside the frame
    s0, s1 = wc - sd / 2, wc + sd / 2
    e = 0.004                                                          # the sashes are let this far into the frame
    bx('sash rail bottom', i0 - e, i1 + e, j0 - e, j0 + s, s0, s1, bevel=0.004)
    bx('sash rail top', i0 - e, i1 + e, j1 - s, j1 + e, s0, s1, bevel=0.004)
    bx('sash stile a', i0 - e, i0 + s, j0 + s, j1 - s, s0, s1, bevel=0.004)
    bx('sash stile b', i1 - s, i1 + e, j0 + s, j1 - s, s0, s1, bevel=0.004)
    um = (a0 + a1) / 2 if mullion is None else mullion
    bx('mullion', um - m / 2, um + m / 2, j0 + s, j1 - s, s0, s1, bevel=0.004)
    lites = []
    for tag, u0, u1 in (('a', i0 + s, um - m / 2), ('b', um + m / 2, i1 - s)):
        g = bx(f'sash {tag} glass', u0 - 0.008, u1 + 0.008, j0 + s - 0.008, j1 - s + 0.008, wc - 0.016, wc + 0.016,
               mat='glass_clear')
        g.visible_shadow = True
        lites.append((round(u0, 3), round(u1, 3)))
    out = {'frame': (round(a0, 3), round(a1, 3), y0, y1), 'daylight': lites, 'daylight y': (round(j0 + s, 3), round(j1 - s, 3))}
    if stool:
        g = RS.GLAZING_STOOL
        n0, n1 = (d0 + 0.015 - g['out'], d1 - 0.015 + g['room']) if stool > 0 else (d0 + 0.015 - g['room'], d1 - 0.015 + g['out'])
        bx('stool', a0 - g['past'], a1 + g['past'], g['y'][0], g['y'][1], n0, n1, mat='paint_trim', bevel=0.008)
        out['stool'] = (round(a0 - g['past'], 3), round(a1 + g['past'], 3))
    return out


def _glz_slider(ctx, name, x, head, panels):
    """A sliding glass door in the rear wall's opening x = (x0, x1), floor to `head` (revision_spec.GLAZING_*): a
    frame as deep as the wall and 0.015 ft proud of both faces (2 in jambs and head), a low threshold with the two
    track ribs, and the panels of revision_spec.slider_panels on their tracks (stiles, rails, a pane let 0.008 ft into
    them). Each sliding panel has a pull on both faces of its lock stile: the stile that closes on the jamb (two
    panels) or on the other centre panel (four)."""
    from . import revision_spec as RS
    c = COLL_OPEN
    x0, x1 = x
    fr, st, rb, pt = RS.GLAZING_FRAME, RS.GLAZING_STILE, RS.GLAZING_RAIL_BOTTOM, RS.GLAZING_PANEL_T
    tr, th = RS.GLAZING_TRACK, RS.GLAZING_THRESHOLD
    zc = REAR_WALL_C
    d0, d1 = zc - R.WALL / 2 - 0.015, zc + R.WALL / 2 + 0.015
    box(ctx, f'{name} head', x0, x1, head - fr, head, d0, d1, 'black_aluminum', c)
    box(ctx, f'{name} jamb W', x0, x0 + fr, -0.01, head - fr, d0, d1, 'black_aluminum', c)
    box(ctx, f'{name} jamb E', x1 - fr, x1, -0.01, head - fr, d0, d1, 'black_aluminum', c)
    sill = box(ctx, f'{name} sill', x0 + fr, x1 - fr, -0.01, th, d0, d1, 'black_aluminum', c)
    ctx.add_bevel(sill, 0.012, 2)
    for tag, sg in (('inner', 1.0), ('outer', -1.0)):
        box(ctx, f'{name} sill track {tag}', x0 + fr, x1 - fr, th - 0.004, th + 0.014, zc + sg * tr - 0.014, zc + sg * tr + 0.014,
            'black_aluminum', c)
    ya, yb = th + 0.010, head - fr + 0.004                # a panel rides on its track rib and runs up into the head
    sliding = [p for p in panels if p[3] == 'outer']
    cm = (x0 + x1) / 2
    out = {'clear': [round(v, 3) for v in RS.slider_clear(x)], 'head': head, 'panels': {}}
    for tag, a, b, track in panels:
        z = zc + (tr if track == 'inner' else -tr)
        za, zb = z - pt / 2, z + pt / 2
        for nm, u0, u1, v0, v1 in (('stile a', a, a + st, ya, yb), ('stile b', b - st, b, ya, yb),
                                   ('rail bottom', a + st, b - st, ya, ya + rb), ('rail top', a + st, b - st, yb - st, yb)):
            ctx.box(f'{name} {tag} {nm}', u0, u1, v0, v1, za, zb, 'black_aluminum', c, bevel=0.005, segments=2)
        g = box(ctx, f'{name} {tag} glass', a + st - 0.008, b - st + 0.008, ya + rb - 0.008, yb - st + 0.008,
                z - 0.012, z + 0.012, 'glass_clear', c)
        g.visible_shadow = True
        out['panels'][tag] = (round(a, 3), round(b, 3), track)
        if track != 'outer':
            continue
        # the interlock: a fin on the stile that covers a fixed panel's stile, across the slot between the two tracks
        mid = (a + b) / 2
        ui = (a + st / 2) if (mid < cm) == (len(sliding) == 2) else (b - st / 2)
        box(ctx, f'{name} {tag} interlock', ui - 0.03, ui + 0.03, ya, yb, zb, zc + tr - pt / 2, 'black_aluminum', c)
        # the lock stile: toward the middle of a four-panel door, toward the jamb of a two-panel one
        mid = (a + b) / 2
        west = (mid > cm) if len(sliding) == 2 else (mid < cm)
        uc = a + st / 2 if west else b - st / 2
        for side, zf, sg in (('inside', zb, 1.0), ('outside', za, -1.0)):
            for k, yp in enumerate((3.02, 4.18)):
                ctx.box(f'{name} {tag} pull {side} post {k}', uc - 0.016, uc + 0.016, yp - 0.016, yp + 0.016,
                        min(zf, zf + sg * 0.034), max(zf, zf + sg * 0.034), 'black_metal', c)
            ctx.box(f'{name} {tag} pull {side} bar', uc - 0.02, uc + 0.02, 2.9, 4.3, min(zf + sg * 0.03, zf + sg * 0.052),
                    max(zf + sg * 0.03, zf + sg * 0.052), 'black_metal', c, bevel=0.006, segments=2)
    return out


def living_slider(ctx):
    """The living room's rear wall (audit F17): ONE four-panel sliding glass door, 12'-4" wide, x 25.528..37.861
    (revision_spec.LIVING_SLIDER_*), in place of the garden door D14 and the two fixed lights W03 / W04. Head 7'-6" as
    the lights it replaces, a threshold 5/8 in above the floor. The two centre panels slide over the fixed end
    panels; the east one is shown 2'-3" open (the tour's way to the landing)."""
    from . import revision_spec as RS
    x0, x1 = RS.LIVING_SLIDER_X
    out = _glz_opening(r'^\d+ Living — rear wall$', r'Painted skirting — Living — rear wall',
                       r'^\d+ Living — rear wall$|^\d+ (Open glass garden door|Garden door white)', 'x', R.ZN, x0, x1,
                       0.0, RS.LIVING_SLIDER_HEAD, 'living room sliding door')
    out['sills removed'] = remove(_sills(out['was'][0] - 0.1, out['was'][1] + 0.1))
    out['door'] = _glz_slider(ctx, 'Living slider', (x0, x1), RS.LIVING_SLIDER_HEAD,
                              RS.slider_panels((x0, x1), 4, *RS.LIVING_SLIDER_OPEN))
    out['way'] = [round(v, 3) for v in RS.living_slider_way()]
    return out


def primary_west_window(ctx):
    """The primary bedroom's north west window W15 (audit F13): 3'-0" wide at the sheet's place, z 1.225..4.225
    (revision_spec.PRIMARY_WEST_WIN_Z; the concept's window, carried over by the warp, was 2'-9 15/16" at
    z 1.107..3.937). Sill, head and the painted stool as before. W14, the second west window, is rebuilt by
    primary_west_window_south (v7 final)."""
    from . import revision_spec as RS
    z0, z1 = RS.PRIMARY_WEST_WIN_Z
    y0, y1 = RS.GLAZING_WIN_Y
    out = _glz_opening(r'^\d+ Primary — west wall$|^\d+ Primary west wall — north of added window$',
                       r'Painted skirting — Primary (— west wall|west wall — north of added)',
                       r'^\d+ Primary — west wall$|^\d+ Primary existing west window', 'z', R.XW, z0, z1, y0, y1,
                       'west window W15')
    out['window'] = _glz_window(ctx, 'Primary west window W15', 'z', WEST_WALL_C, z0, z1, y0, y1, stool=1)
    return out


def primary_west_window_south(ctx):                                                          # v7 final
    """The primary bedroom's south west window W14 (the owner's second west window; the sheet has none there): the
    same unit as W15, in the opening it has (revision_spec.PRIMARY_WEST_WIN_S_Z, z 9.197..12.071, 2'-10 1/2"; sill
    2'-6", head 7'-0"). The wall is not touched: the opening is the shell's, carried by the warp, and is checked
    against the spec. The shell's unit goes (two lights one above the other with a meeting rail, painted jambs flush
    with both wall faces, a head and a sill reveal, a stone sill 0.19 ft into the room) and _glz_window builds
    W15's kit in its place: the frame 0.015 ft proud of both wall faces, two sashes side by side with one mullion
    in the middle, the painted stool. white_windows then gives each sash the 1 x 3 lights W15's have (the sashes
    are 0.76 in narrower than W15's: the opening is 1 1/2 in narrower). Its roller shade is the zone's
    (bl/zones/primary_suite.build_shades), hung like W15's."""
    from . import revision_spec as RS
    z0, z1 = RS.PRIMARY_WEST_WIN_S_Z
    y0, y1 = RS.GLAZING_WIN_Y

    def one(pat):
        obs = [o for o in find(pat, COLL_SHELL) if o.type == 'MESH']
        if len(obs) != 1:
            raise RuntimeError(f'west window W14: {len(obs)} wall pieces {pat!r}, expected 1')
        return bbox(obs[0])
    was = (one(r'^\d+ Primary west wall — north of added window$')[5], one(r'^\d+ Primary west wall — south of added window$')[4],
           one(r'^\d+ Primary west wall — added window sill wall$')[3], one(r'^\d+ Primary west wall — added window header$')[2])
    if max(abs(a - b) for a, b in zip(was, (z0, z1, y0, y1))) > 0.005:
        raise RuntimeError(f'west window W14: the opening is {[round(float(v), 3) for v in was]}, the spec has '
                           f'{[round(v, 3) for v in (z0, z1, y0, y1)]}')
    out = {'opening': (round(z0, 3), round(z1, 3)), 'y': (y0, y1),
           'old pieces removed': remove([o for o in find(r'^\d+ Primary added west window — ', COLL_OPEN) if o.type == 'MESH'])}
    out['window'] = _glz_window(ctx, 'Primary west window W14', 'z', WEST_WALL_C, z0, z1, y0, y1, stool=1)
    return out


def living_east_windows(ctx):
    """The east wall's two windows north of the kitchen (audit F20, F21). W05: ONE 6'-0" unit at z 0.368..6.368
    (revision_spec.LIVING_EAST_WIN_Z) in place of the two 2'-10 7/16" windows W05 / W06 and the 9 in pier between
    them. W07, the living / dining window: 5'-0" at z 16.066..21.066 (DINING_EAST_WIN_Z; it was 3'-11 7/16" at
    z 17.615..21.570), its mullion where the sheet draws it (DINING_EAST_WIN_MULLION, z 19.44: two unequal lights).
    Sill 2'-6" and head 7'-0" as before."""
    from . import revision_spec as RS
    pat = r'^\d+ Living / kitchen — east wall$'
    walls = pat + r'|^\d+ Kitchen east wall beside arch$'
    y0, y1 = RS.GLAZING_WIN_Y
    out = {}
    for tag, name, (z0, z1), zm in (('W05', 'Living east window W05', RS.LIVING_EAST_WIN_Z, None),
                                    ('W07', 'Living / dining east window W07', RS.DINING_EAST_WIN_Z,
                                     RS.DINING_EAST_WIN_MULLION)):
        o = _glz_opening(walls, r'Painted skirting — Living / kitchen — east wall', pat, 'z', R.X_LIV_E, z0, z1, y0, y1,
                         f'east window {tag}')
        o['window'] = _glz_window(ctx, name, 'z', RS.EAST_WALL_C, z0, z1, y0, y1, mullion=zm)
        out[tag] = o
    return out


def bedroom3_bath_window(ctx):
    """Sixth round (2026-11-20): the Bedroom 3 bathroom's shower window W11 (the shell's "Ensuite privacy window", on
    the west wall inside the shower) is vertically larger: sill 3'-0", head 7'-6" (revision_spec.BED3_BATH_WIN_Y)
    instead of 5'-0" / 7'-0". Width, place, the frosted glazing and the frame (two rails, two jambs and a centre
    mullion in black aluminium) stay.

    * shell: the wall below the window is cut down to the new sill and the header above it up to the new head (both
      keep paint inside, stucco outside and in the reveals);
    * frame and pane: stretched onto the new opening, the rails keeping their section. The pane also runs into the two
      jamb sections now: the shell's pane stops 0.03 to 0.04 ft short of them, a clear slit beside the frosted glass
      that the old window showed only sky through and the taller one, from the bath's sweep, the side-yard fence.
      The pane's origin goes to its centre, because lighting.add_window_portals puts a pane's light portal there;
    * finish: the wall tile around the opening, the tiled jamb returns and the quartz sill are built by the baths zone
      from the same heights (bl/zones/baths.py, build_suite3); here they are only checked against the opening as built
      (a `--zones none` build has none).
    Nothing else stands on this wall: the valve, the niche and the rain head's arm are on the shower's north wall."""
    from .revision_spec import BED3_BATH_WIN_OLD_Y, BED3_BATH_WIN_Y, BED3_BATH_WIN_Z
    z0, z1 = BED3_BATH_WIN_Z
    (s, h), (s_old, h_old) = BED3_BATH_WIN_Y, BED3_BATH_WIN_OLD_Y

    def one(pat):
        obs = [ob for ob in find(pat, COLL_SHELL) if ob.type == 'MESH']
        if len(obs) != 1:
            raise RuntimeError(f'{pat!r}: {len(obs)} shell pieces, expected 1')
        b = bbox(obs[0])
        if max(abs(b[4] - z0), abs(b[5] - z1)) > 0.01:
            raise RuntimeError(f'{obs[0].name!r} is not where the spec expects it: {[round(float(v), 3) for v in b]}')
        return obs[0]
    low, high = one(r'^\d+ Ensuite privacy window sill wall$'), one(r'^\d+ Ensuite privacy window head wall$')
    if move_face(low, 'y', s_old, s) != 4 or move_face(high, 'y', h_old, h) != 4:
        raise RuntimeError(f'wall below / above the window does not end at the concept sill {s_old} / head {h_old}')
    frame = [ob for ob in find(r'^\d+ Ensuite privacy window (frame|mullion|glazing)$', COLL_OPEN) if ob.type == 'MESH']
    for ob in frame:
        map_y(ob, [(s_old, s), (s_old + 0.1, s + 0.1), (h_old - 0.1, h - 0.1), (h_old, h)])
    panes = [ob for ob in frame if 'glazing' in ob.name and ob.parent is None]
    jambs = [bbox(ob) for ob in frame if 'mullion' in ob.name]
    jn, js = [b for b in jambs if b[4] < z0 < b[5]], [b for b in jambs if b[4] < z1 < b[5]]
    for ob in panes:
        b = bbox(ob)
        if jn and b[4] > z0:                            # into the north jamb section, 0.01 ft past the opening's edge
            move_face(ob, 'z', b[4], z0 + 0.01)
        if js and b[5] < z1:
            move_face(ob, 'z', b[5], z1 - 0.01)
        w, _ = _world(ob)
        ob.location = Vector([float(v) for v in (w.min(axis=0) + w.max(axis=0)) / 2])
        bpy.context.view_layer.update()
        _set_world(ob, w, np.array(ob.matrix_world))
    out = {'opening z': (z0, z1), 'sill, head': (s, h), 'was': (s_old, h_old), 'frame pieces': len(frame),
           'glass': [[round(float(v), 3) for v in bbox(ob)] for ob in panes]}
    # the bath zone's finish around the opening
    fin = {ob.name: bbox(ob) for ob in bpy.data.objects if ob.type == 'MESH' and re.match(r'A3 (tile west|window)', ob.name)}
    across = [n for n, b in fin.items() if n.startswith('A3 tile west')
              and b[4] < z1 - 0.01 and b[5] > z0 + 0.01 and b[2] < h - 0.01 and b[3] > s + 0.01]
    off = [n for n, b in fin.items() if n.startswith('A3 window')
           and (b[4] < z0 - 0.02 or b[5] > z1 + 0.02 or b[2] < s - 0.02 or b[3] > h + 0.02)]
    if across or off:
        raise RuntimeError(f'bath finish does not fit the opening: tile across it {across}, sill / returns off it {off}')
    out['finish'] = {n: [round(float(v), 3) for v in b] for n, b in fin.items() if n.startswith('A3 window')}
    return out


def _copy(ob, name):
    c = ob.copy()
    c.data = ob.data.copy()
    c.name = name
    for col in ob.users_collection:
        col.objects.link(c)
    return c


def bath_door(ctx):
    """Sixth round (2026-11-20): the primary bath's door D08 at the architect's position (sheet SKA002;
    revision_spec.BATH_DOOR_*). The shell builds the concept opening at x 5.914..8.516 with a leaf hinged on its east
    jamb; the sheet has the opening hard against the bath's east wall, x 6.89..9.45.

    * walls: the wall west of the opening (shell piece 1885) is carried east to the new west jamb, the header (1903)
      is put over the new opening and the wall east of it (1845, which runs on as the shared bath's north wall) starts
      at the new east jamb; all three are interior on every face, so every face gets the interior paint (the shell
      gives the jamb ends exterior stucco);
    * the shower niche (revision_spec.BATH_NICHE): a real recess in that wall's bath face. The wall is split around
      it like the laundry closet's outlet box: west of it, east of it, below, above, and a 0.11 ft back toward the
      walk-in closet (copies of the wall: same paint, same `scene_index`);
    * the door like the house's other interior doors: painted jamb liners and head trim (proud of the vestibule face
      like the house's casing, and of the bath's wainscot on the bath face), an oak saddle between the vestibule's oak
      and the bath's stone floor, a flush slab leaf hinged on the EAST jamb and standing open at 90 degrees along the
      bath's east wall (revision_spec.bath_door_leaf), three black butt hinges, a lever handle on each face;
    * baseboards: the two runs on the vestibule face are cut / carried to the new liners, the bath-face run east of
      the door is cut at the liner (the bath's own finish covers the bath face);
    * the old leaf, its handle and the primary-suite zone's paint skins in the old jambs ('ps D08 ...') go: the
      liners do their job at the new place."""
    from . import laundry
    from . import revision_spec as S
    d0, d1 = S.BATH_DOOR_X
    o0, o1 = S.BATH_DOOR_OLD_X
    zn, zs = S.PRIMARY_BATH_NORTH_WALL_Z
    head, ln = S.BATH_DOOR_HEAD, S.BATH_DOOR_LINER
    pn, pb = S.BATH_DOOR_LINER_PROUD
    c = COLL_OPEN
    out = {}

    def shell_one(pat):
        obs = [o for o in find(pat, COLL_SHELL) if o.type == 'MESH' and len(o.data.vertices) == 8]
        if len(obs) != 1:
            raise RuntimeError(f'{pat!r}: {len(obs)} shell pieces, expected 1')
        return obs[0]
    west, hdr = shell_one(r'^\d+ Ensuite north / closet south$'), shell_one(r'^\d+ Ensuite entry$')
    east = shell_one(r'^\d+ Shared bathroom north / walk-in south$')
    wb, hb, eb = bbox(west), bbox(hdr), bbox(east)
    off = max(abs(wb[1] - o0), abs(hb[0] - o0), abs(hb[1] - o1), abs(eb[0] - o1), abs(wb[4] - zn), abs(wb[5] - zs),
              abs(eb[4] - zn), abs(eb[5] - zs))
    if off > 0.02:
        raise RuntimeError(f'the door wall is not where the spec expects it: {[round(float(v), 3) for v in wb + hb + eb]}')
    move_face(west, 'x', wb[1], d0)
    move_face(east, 'x', eb[0], d1)
    _reshape(hdr, d0, d1, head, hb[3], hb[4], hb[5])
    for ob in (west, hdr, east):
        _paint_all(ob)
    out['opening x'] = [(round(float(wb[1]), 3), round(float(eb[0]), 3)), (d0, d1)]

    # ---- the shower niche: a recess in the bath face of the wall west of the door
    nx0, nx1, ny0, ny1, dep = S.BATH_NICHE
    wb = bbox(west)
    if wb[0] < nx0 - 0.3 and wb[1] > nx1 + 0.3 and wb[5] - wb[4] > dep + 0.05:
        nm = 'Ensuite north / closet south'
        _like(west, f'{nm} (east of the shower niche)', nx1, wb[1], wb[2], wb[3], wb[4], wb[5])
        _like(west, f'{nm} (below the shower niche)', nx0, nx1, wb[2], ny0, wb[4], wb[5])
        _like(west, f'{nm} (above the shower niche)', nx0, nx1, ny1, wb[3], wb[4], wb[5])
        _like(west, f'{nm} (behind the shower niche)', nx0, nx1, ny0, ny1, wb[4], wb[5] - dep)
        move_face(west, 'x', wb[1], nx0)
        out['niche'] = [nx0, nx1, ny0, ny1, round(wb[5] - dep, 3)]
    else:
        out['niche'] = 'FAILED: the wall does not take the niche'

    # ---- the old door and the paint skins in its jambs
    out['removed'] = remove(find(r'^\d+ Primary bathroom privacy door', COLL_OPEN)) + remove(find(r'^ps D08 '))

    # ---- baseboards on the wall's two faces (shell pieces named "skirting")
    def runs(face_z):
        return [o for o in find(r'^\d+ Painted skirting — (Ensuite north / closet south|Shared bathroom north / walk-in sou)',
                                COLL_SHELL) if o.type == 'MESH' and abs((bbox(o)[4] + bbox(o)[5]) / 2 - face_z) < 0.08]
    sk = {}
    for side, face_z in (('vestibule', zn), ('bath', zs)):
        for ob in runs(face_z):
            b = bbox(ob)
            if b[1] < (d0 + d1) / 2:                     # the run west of the door: up to the west liner
                if side == 'vestibule' and abs(b[1] - (d0 - ln)) > 0.005:
                    move_face(ob, 'x', b[1], d0 - ln)
            elif b[0] < d1 + ln - 0.005:                 # the run east of it: from the east liner
                move_face(ob, 'x', b[0], d1 + ln)
            sk[side + ' ' + re.sub(r'^\d+ ', '', ob.name)[-24:]] = [round(float(v), 3) for v in bbox(ob)[:2]]
    out['baseboards'] = sk

    # ---- liners, head trim, saddle
    box(ctx, 'Primary bath door jamb W', d0 - ln, d0 + ln, 0.0, head - 0.08, zn - pn, zs + pb, 'paint_trim', c)
    box(ctx, 'Primary bath door jamb E', d1 - ln, d1 + ln, 0.0, head - 0.08, zn - pn, zs + pb, 'paint_trim', c)
    box(ctx, 'Primary bath door head trim', d0 - ln, d1 + ln, head - 0.08, head + 0.06, zn - pn, zs + pb, 'paint_trim', c)
    sd = box(ctx, 'Primary bath door saddle', d0 + ln, d1 - ln, -0.005, S.BATH_DOOR_SADDLE_Y, zn - pn, zs + pb,
             'white_oak_veneer', c)
    ctx.add_bevel(sd, 0.012, 2)

    # ---- the leaf, open against the east wall, and its hardware
    leaf = S.bath_door_leaf()
    ctx.box_c(leaf['name'], leaf['center'], leaf['size'], leaf['rot'], 'door_slab', c, bevel=0.006, segments=2)
    kit = laundry.Kit(ctx, c, None)
    (ox, oz), (ax, az), (tx, tz) = leaf['corner'], leaf['along'], leaf['through']
    px, pz = leaf['pivot']
    w, _, th = leaf['size']

    def pt(u, y, v):                                     # u along the leaf from its hinge edge, v through it from its bath face
        return (ox + ax * u + tx * v, y, oz + az * u + tz * v)
    r, hh = 0.021, 0.146                                 # 1/2 in barrels, 3 1/2 in high, on the pin axis
    for i, yh in enumerate(S.BATH_DOOR_HINGE_Y):
        kit.cyl(f'Primary bath door hinge {i}', (px, yh - hh, pz), (px, yh + hh, pz), r, 'black_metal', 20)
        for k, ya in enumerate((yh - hh - 0.02, yh + hh)):
            kit.cyl(f'Primary bath door hinge {i} tip {k}', (px, ya, pz), (px, ya + 0.02, pz), r * 0.7, 'black_metal', 16)
    inset, yl = S.BATH_DOOR_LEVER
    ul = w - inset
    for tag, v0, sg in (('bath', 0.0, -1.0), ('room', th, 1.0)):       # one lever on each face, pointing to the hinge
        kit.cyl(f'Primary bath door lever {tag} rose', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.02), 0.085, 'black_metal', 32)
        kit.cyl(f'Primary bath door lever {tag} neck', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.17), 0.03, 'black_metal', 20)
        kit.cyl(f'Primary bath door lever {tag} bar', pt(ul + 0.02, yl, v0 + sg * 0.15), pt(ul - 0.38, yl, v0 + sg * 0.15),
                0.024, 'black_metal', 20)
    out['leaf'] = [round(float(v), 3) for v in leaf['aabb']]
    return out


def bath_window(ctx):
    """Primary bath west window W13: clear glass from a 2'-0" sill (TALL_SILL, third round) to the 8 ft ceiling with a
    transom at 6 ft. Sixth round: at the architect's position (revision_spec.BATH_WIN_Z, 3'-0" wide) and with a mullion
    on the shower's south glass line (BATH_WIN_MULLION_Z): the north lite is inside the shower, the south lite in the
    room. The concept window (sill 5'-0", head 7'-0") goes; the solid walls north and south of it end on the new
    jambs, and the wall below the sill is a copy of the neighbouring wall (paint inside, stucco outside), so nothing
    of the old opening is left inside or outside.

    The room's finish around the opening (shower tile and tiled reveal, the shower lite's stone sill, wainscot and
    plaster, the dry lite's oak stool and roman shade, the post that carries the shower glass on the mullion) is
    built by the baths zone after the warp, from the same numbers (bl/zones/baths_primary.py)."""
    from .revision_spec import BATH_WIN_MULLION_Z, BATH_WIN_TRANSOM_Y
    z0, z1 = BATH_WIN_Z
    zm, yt = BATH_WIN_MULLION_Z, BATH_WIN_TRANSOM_Y
    s = TALL_SILL
    gone = remove(find(r'Primary bathroom west wall — (below|above) privacy window|Primary bathroom privacy-window|'
                       r'Primary bathroom operable awning|Primary bathroom obscured privacy glazing'))
    gone += remove(find(r'Painted skirting — Primary bathroom west wall — below'))
    north = [o for o in find(r'^\d+ Primary bathroom west wall — north solid$', COLL_SHELL) if o.type == 'MESH']
    south = [o for o in find(r'^\d+ Primary bathroom west wall — south solid$', COLL_SHELL) if o.type == 'MESH']
    if len(north) != 1 or len(south) != 1:
        raise RuntimeError(f'west wall solids not found ({len(north)}, {len(south)})')
    nb, sb = bbox(north[0]), bbox(south[0])
    was = (round(float(nb[5]), 3), round(float(sb[4]), 3))
    move_face(north[0], 'z', nb[5], z0)                  # the concept jambs (22.20 / 24.89 on the plan) -> the new jambs
    move_face(south[0], 'z', sb[4], z1)
    nb = bbox(north[0])
    # the wall below the sill: a copy of the north solid stretched across the opening, up to the sill
    _like(north[0], 'Primary bathroom west wall — below tall window', nb[0], nb[1], nb[2], s, z0, z1)
    xc, fd, fw, mw = WEST_WALL_C, 0.22, 0.12, 0.10       # on the west wall's centre line
    c = COLL_OPEN
    box(ctx, 'Primary bath tall window head', xc - fd / 2, xc + fd / 2, 8.0 - fw, 8.0, z0, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window sill', xc - fd / 2, xc + fd / 2, s, s + 0.08, z0, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window jamb N', xc - fd / 2, xc + fd / 2, s, 8.0, z0, z0 + fw, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window jamb S', xc - fd / 2, xc + fd / 2, s, 8.0, z1 - fw, z1, 'black_aluminum', c)
    box(ctx, 'Primary bath tall window mullion', xc - fd / 2, xc + fd / 2, s + 0.08, 8.0 - fw, zm - mw / 2, zm + mw / 2,
        'black_aluminum', c)
    # clear glass: the side yard outside is fenced (6'-2") and screened by an evergreen (exterior_plants)
    lites = {}
    for tag, a, b in (('north', z0 + fw, zm - mw / 2), ('south', zm + mw / 2, z1 - fw)):
        box(ctx, f'Primary bath tall window {tag} transom', xc - fd / 2, xc + fd / 2, yt, yt + 0.1, a, b, 'black_aluminum', c)
        for part, y0, y1 in (('lower', s + 0.08, yt), ('upper', yt + 0.1, 8.0 - fw)):
            g = box(ctx, f'Primary bath tall window {tag} {part} glass', xc - 0.015, xc + 0.015, y0, y1, a, b, 'glass_clear', c)
            g.visible_shadow = True
        lites[tag] = (round(a, 3), round(b, 3))
    return {'removed': gone, 'opening z': (z0, z1), 'was': was, 'mullion z': zm, 'sill': s, 'lites': lites}


def kitchen_skylight(ctx):
    gone = remove(find(r'^\d+ Kitchen skylight —'))
    gone += remove(find(r'^\d+ House ceiling — skylight (east|north|south) panel$'))
    kx0, kx1, kz0, kz1 = KITCHEN_CEILING
    box(ctx, 'Kitchen ceiling (east of the central panel)', kx0, kx1, 8.0, 8.12, kz0, kz1, 'paint_ceiling', COLL_SHELL)
    n = skylight(ctx, 'Kitchen skylight', *KITCHEN_SKY, r'ceiling')
    return {'removed': gone, 'cut': n}


def foyer_skylights(ctx):
    out = {}
    for i, r in enumerate(FOYER_SKY):
        out[f'foyer {i}'] = skylight(ctx, f'Foyer skylight {i}', *r, r'ceiling|vault')
    return out


def primary_bath_skylight(ctx):
    """Skylight W20 over the primary bath's shower (revision_spec.PRIMARY_BATH_SKY). Sixth round: it moved with the
    shower into the room's north-west corner; the opening is cut into the shell as built, so nothing is left where it
    was."""
    return skylight(ctx, 'Primary bath skylight', *PRIMARY_BATH_SKY, r'ceiling')


# v7 roof -----------------------------------------------------------------------------------------------------------
def roof_v7(ctx):
    """Eighth round (2026-11-24), track "roof": the concept's roof (planes of 4.0 to 6.5 in 12, eaves of 5 1/4 in, an
    entry ridge that fell toward the street, a flat porch canopy) is removed and the sheets' roof built in plan feet
    by bl/roof.py: every plane 5 in 12, main ridge 14'-7", garage ridge 12'-4 1/2", level wing and entry ridges,
    1'-0" eaves with a 6 1/2 in fascia, the entry gable running on over the porch; Bedroom 3's vault and the entry
    vault re-fitted under it. It runs before the skylights, which cut their wells through the roof that is there."""
    from . import roof
    return roof.rebuild(ctx)


def living_skylight(ctx):
    """The sheet's "(N) SKYLIGHT" over the living room (SK1, 1'-10" x 3'-10"; revision_spec.LIVING_SKY), on the east
    roof plane, with its well through the ceiling slab kitchen_skylight builds (so it runs after it)."""
    from .revision_spec import LIVING_SKY
    return skylight(ctx, 'Living skylight', *LIVING_SKY, r'ceiling')


def primary_bath_fit_out(ctx):
    """Sixth round (2026-11-20): the primary bath is laid out on the architect's sheet (revision_spec.BATH_*) and
    fitted out here, after the warp and in plan feet, by the baths zone (bl/zones/baths_primary.build_room): wall and
    ceiling finishes, the shower, the vanity wall, the toilet, fixtures, lights. It runs after bath_door, bath_window
    and primary_bath_skylight, which prepare the walls, the window and the shaft. The shell's shower floor slab (the
    concept's shower in the south-west corner) goes. Without the baths zone (`--zones` without it) only the slab is
    removed."""
    out = {'old shower floor removed': remove(find(r'^\d+ Primary shower stone floor', COLL_SHELL))}
    if bpy.data.collections.get('zone_baths_primary') is None:
        out['fit-out'] = 'baths zone not built: skipped'
        return out
    from .zones import baths_primary
    out.update(baths_primary.build_room(ctx))
    return out


def entry_vault_closure(ctx):
    """Close the strip between the entry vault's rear edge and the rear gable below it (eaves 8 ft): looking up
    from the foyer it opened into the attic. (The vault is level since the eighth round, bl/roof.entry_ceiling:
    9.719 ft at the walls, 10.917 ft at the ridge; the concept's fell from 11.2 to 9.05 ft.)   v7 final: comment"""
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


def _paint_all(ob):
    """Every face of a wall piece on its first material slot (interior paint)."""
    for poly in ob.data.polygons:
        poly.material_index = 0


def laundry_closet(ctx):
    """Fourth round, owner's correction of 2026-11-20: the laundry closet carved out of Bedroom 4's north-east
    corner, opening east onto the foyer (revision_spec.LAUNDRY_*), and its stacked pair.

    The opening is cut into the Bedroom 4 / foyer wall (the "host", shell piece 3338): the piece north of it and the
    header are copies of the host, the host itself keeps the part south of the opening. The two new walls are copies
    of the host too, so every piece carries its interior paint on all faces and its `scene_index` (the web bake files
    them under 'wall'); both rooms use the same wall paint, so each face has the paint of the room it looks into.
    The west wall is split around a real recess for the washer outlet box (a thin piece is left behind it on the
    bedroom side). Baseboards: the two existing runs on the host wall are cut at the jamb liners; new runs (copies of
    them) go along both faces of the new walls and round the outside corner. The door follows the house's other
    interior doors: painted jamb liners and head trim standing off both wall faces, flush slab leaves (a pair, shown
    wide open against the foyer wall), black hardware; an oak threshold strip marks the opening in the floor."""
    from . import laundry
    cx0, cx1, cz0, cz1 = LAUNDRY_CLEAR
    t = LAUNDRY_WALL_T
    d0, d1 = LAUNDRY_DOOR_Z
    head, ln, ow = LAUNDRY_DOOR_HEAD, LAUNDRY_DOOR_LINER, LAUNDRY_DOOR_LINER_PROUD
    embed = 0.01                                        # new wall ends run this far into the walls they butt against
    out = {}

    def shell_one(pat, pick=lambda b: True):
        obs = [o for o in find(pat, COLL_SHELL) if o.type == 'MESH' and len(o.data.vertices) == 8 and pick(bbox(o))]
        return obs[0] if obs else None

    # ---- the host wall and the door opening in it
    host = shell_one(rf'^\d+ {re.escape(LAUNDRY_HOST_WALL)}$')
    if host is None:
        raise RuntimeError(f'host wall {LAUNDRY_HOST_WALL!r} not found')
    hb = bbox(host)
    hx0, hx1 = hb[0], hb[1]
    if max(abs(hx0 - LAUNDRY_HOST_WALL_X[0]), abs(hx1 - LAUNDRY_HOST_WALL_X[1])) > 0.01 or hb[4] > d0 - 0.1 or hb[5] < d1 + 0.1:
        raise RuntimeError(f'host wall is not where the spec expects it: {[round(v, 3) for v in hb]}')
    _paint_all(host)
    ceil = [ceiling_y(x, z) for x, z in ((cx0 + 0.1, cz0 + 0.1), (cx1 - 0.1, cz0 + 0.1), (cx0 + 0.1, cz1 - 0.1),
                                         (cx1 - 0.1, cz1 - 0.1), ((cx0 + cx1) / 2, (cz0 + cz1) / 2), (cx0 - t / 2, cz1 + t / 2))]
    top = max(LAUNDRY_CEILING, max(ceil))
    out['ceiling y'] = [round(min(ceil), 3), round(max(ceil), 3)]
    walls = {}
    for name, wx0, wx1, wy0, wy1, wz0, wz1 in laundry_walls():
        wy1 = top if wy1 == LAUNDRY_CEILING else wy1
        if name.endswith('north return'):               # the host's own faces and north end
            wx0, wx1, wz0 = hx0, hx1, hb[4]
        elif name.endswith('header'):
            wx0, wx1 = hx0, hx1
        elif name.endswith('west wall'):                # into Bedroom 4's north wall
            wz0 -= embed
        elif name.endswith('south wall'):               # into the new west wall and into the host wall
            wx0, wx1 = wx0 - embed, hx0 + embed
        walls[name] = _like(host, name, wx0, wx1, wy0, wy1, wz0, wz1)
    move_face(host, 'z', hb[4], d1)                     # the host keeps the part between the opening and door D04
    out['host wall'] = {'was z': [round(hb[4], 3), round(hb[5], 3)], 'now z': [round(v, 3) for v in bbox(host)[4:6]]}
    out['walls'] = len(walls) + 1

    # ---- recess for the washer outlet box: the west wall is split around it (north / below / above / behind)
    recess = None
    ww = walls.get('Laundry closet west wall')
    if ww is not None:
        rz0, rz1, ry0, ry1, dep = LAUNDRY_HOOKUP_RECESS
        b = bbox(ww)
        if b[4] < rz0 - 0.05 and b[5] > rz1 + 0.05 and b[1] - b[0] > dep + 0.05:
            _like(ww, 'Laundry closet west wall (north of the outlet box)', b[0], b[1], b[2], b[3], b[4], rz0)
            _like(ww, 'Laundry closet west wall (below the outlet box)', b[0], b[1], b[2], ry0, rz0, rz1)
            _like(ww, 'Laundry closet west wall (above the outlet box)', b[0], b[1], ry1, b[3], rz0, rz1)
            _like(ww, 'Laundry closet west wall (behind the outlet box)', b[0], b[1] - dep, ry0, ry1, rz0, rz1)
            move_face(ww, 'z', b[4], rz1)
            recess = LAUNDRY_HOOKUP_RECESS
    out['outlet recess'] = bool(recess)

    # ---- baseboards (shell pieces named "skirting": skirting_trim and check_holes look after them)
    def host_run(pick):
        return shell_one(r'^\d+ Painted skirting — ' + re.escape(LAUNDRY_HOST_WALL[:24]),
                         lambda b: pick(b) and b[4] < d0 and b[5] > d1)
    sk_bed = host_run(lambda b: b[1] < hx0 + 0.02)       # Bedroom 4 face of the host wall
    sk_foy = host_run(lambda b: b[0] > hx1 - 0.02)       # foyer face
    src = sk_bed or sk_foy or shell_one(r'^\d+ Painted skirting')
    if sk_bed is not None:
        sb = bbox(sk_bed)
        sy0, sy1, proud, sunk = sb[2], sb[3], hx0 - sb[0], sb[1] - hx0
    else:
        sy0, sy1, proud, sunk = 0.025, 0.455, 0.055, 0.002
    nb = shell_one(r'^\d+ Painted skirting — Old front wall below shared', lambda b: b[4] > cz0 - 0.05 and b[1] > cx1 - 0.5)
    zn = bbox(nb)[5] if nb is not None else cz0 + proud  # the face of the north wall's own run: the others butt into it

    def skirt(name, bx0, bx1, bz0, bz1, corner=False):
        nm = f'Laundry closet plinth block {name}' if corner else f'Painted skirting — Laundry closet {name}'
        if src is not None:
            return _like(src, nm, bx0, bx1, sy0, sy1, bz0, bz1)
        return box(ctx, nm, bx0, bx1, sy0, sy1, bz0, bz1, 'paint_trim', COLL_SHELL)
    la, lb = d0 - ln, d1 + ln                           # outer edges of the jamb liners
    xo, zo = cx0 - t, cz1 + t                           # the new walls' Bedroom 4 faces
    if sk_bed is not None:                              # Bedroom 4 side of the host wall: closet N stub | closet S stub | bedroom
        sb = bbox(sk_bed)
        _like(sk_bed, 'Painted skirting — Laundry closet inside east N', sb[0], sb[1], sy0, sy1, sb[4], la)
        _like(sk_bed, 'Painted skirting — Laundry closet inside east S', sb[0], sb[1], sy0, sy1, lb, cz1 - proud)
        move_face(sk_bed, 'z', sb[4], zo + proud)
    if sk_foy is not None:                              # foyer side: north of the door | south of the door
        sb = bbox(sk_foy)
        _like(sk_foy, 'Painted skirting — Laundry closet foyer face N', sb[0], sb[1], sy0, sy1, sb[4], la)
        move_face(sk_foy, 'z', sb[4], lb)
    skirt('inside west', cx0 - sunk, cx0 + proud, zn, cz1 - proud)
    skirt('inside south', cx0 - sunk, hx0 + sunk, cz1 - proud, cz1 + sunk)
    skirt('west wall, Bedroom 4 face', xo - proud, xo + sunk, zn, zo)
    skirt('south wall, Bedroom 4 face', xo, hx0 + sunk, zo - sunk, zo + proud)
    # the outside corner is closed with a block: a run that turned the corner would have no wall behind its last
    # 5/8 in and skirting_trim would cut it back
    skirt('SW', xo - proud, xo, zo, zo + proud, corner=True)
    out['baseboards'] = {'section y': [round(sy0, 3), round(sy1, 3)], 'proud': round(proud, 3),
                         'host runs cut': [sk_bed is not None, sk_foy is not None]}

    # ---- floor: the oak slabs run under the host wall, so the floor continues through the opening; a flat oak
    # threshold strip between the liners marks the line (its top stays under the closed leaves' bottom edge).
    # One patch of the same oak lies 1/32 in under the floor over the whole footprint and the opening (like
    # floor_gaps' patches): the north slab's skewed north edge stops up to 0.05 ft short of Bedroom 4's north wall
    # inside the closet (under that wall's baseboard, where floor_gaps' probes cannot see it), and the two slabs'
    # joint (floor_overlap) crosses the closet under the units.
    floor = [o for o in find(r'^\d+ Oak floor substrate$', COLL_SHELL) if _overlap(bbox(o), cx0, cx1, cz0, cz1)]
    if floor:
        fy = max(bbox(o)[3] for o in floor)
        patch = ctx.box('Floor seam patch laundry closet', cx0 - 0.1, hx1 - 0.01, fy - 0.1, fy - 0.0026, cz0 - 0.1, cz1 + 0.1,
                        None, COLL_SHELL)
        if floor[0].data.materials:
            patch.data.materials.append(floor[0].data.materials[0])
    out['floor'] = [re.sub(r'^\d+ ', '', o.name) for o in floor]
    c = COLL_OPEN
    th = box(ctx, 'Laundry closet door threshold', hx0 - ow, hx1 + ow, -0.005, LAUNDRY_THRESHOLD_Y, d0 + ln, d1 - ln,
             'white_oak_veneer', c)
    ctx.add_bevel(th, 0.006, 2)
    th['tg_grain'] = 1                                  # v7 repair: the grain runs along the strip (it lies along z)

    # ---- door: jamb liners and head trim like the other interior doors, a pair of flush slab leaves standing open
    box(ctx, 'Laundry closet door jamb N', hx0 - ow, hx1 + ow, 0.0, head - 0.08, d0 - ln, d0 + ln, 'paint_trim', c)
    box(ctx, 'Laundry closet door jamb S', hx0 - ow, hx1 + ow, 0.0, head - 0.08, d1 - ln, d1 + ln, 'paint_trim', c)
    box(ctx, 'Laundry closet door head trim', hx0 - ow, hx1 + ow, head - 0.08, head + 0.06, d0 - ln, d1 + ln, 'paint_trim', c)
    leaves = laundry_leaves()
    for leaf in leaves:
        ctx.box_c(leaf['name'], leaf['center'], leaf['size'], leaf['rot'], 'door_slab', c, bevel=0.006, segments=2)
        laundry.door_hardware(ctx, leaf, c)
    out['door'] = {'opening z': (round(d0, 4), round(d1, 4)), 'head': head,
                   'leaves': {leaf['side']: [round(v, 3) for v in leaf['aabb']] for leaf in leaves}}

    # ---- contents: stacked washer / dryer, hookups, ceiling light
    out['contents'] = laundry.build(ctx, recess, top)
    out['clear'] = [round(v, 3) for v in LAUNDRY_CLEAR]

    # ---- Bedroom 4's side of the new walls: picture and hook rail (the room's furniture is the bedrooms zone's)
    try:
        from .zones import bedrooms
        out['bedroom 4 faces'] = bedrooms.bed4_closet_faces(ctx)
    except Exception as e:                              # decoration only: the closet stands without it
        import traceback
        traceback.print_exc()
        out['bedroom 4 faces'] = f'FAILED: {e!r}'
    return out


def suite_rooms(ctx):
    """Sixth round (2026-11-20), the owner: "The walk in closet in the primary bedroom is not correct, you should refer to
    the floor plan of sizes.pdf last page for that, there should be a door since it's a small room for walk in closet".
    The 8 ft zone between the primary bedroom and the primary bath, one open dressing area until now, is divided as
    on sheet SKA002 (revision_spec.SUITE_*): the WALK-IN CLOSET, an enclosed room behind a new 5 in wall with a
    sliding pocket door centred on it; the VESTIBULE, open to the bedroom (x 6.725..11.308), with the attic access
    hatch in its ceiling; and the SUITE ENTRY (D09), a 2'-8" opening with a sliding panel on the hall side that parks
    south of it. The geometry is in bl/zones/primary_suite_rooms.py (walls as copies of the existing wall, so they
    bake as walls and carry the interior paint; jambs, leaves and hardware; baseboards on every new face). Runs after
    bath_door, which carries the bath wall's vestibule-side baseboard across the place of the closet's new wall."""
    from .zones import primary_suite_rooms
    return primary_suite_rooms.build(ctx)


def suite_fit_out(ctx):
    """The primary suite's furniture on the architect's plan: the bedroom as the sheet draws it (king bed on the west
    wall between the two windows, two nightstands, rug), the vestibule's mirror and lights, the walk-in closet's
    hanging on three sides. bl/zones/primary_suite.py is written in plan feet and builds here, after the warp and
    after suite_rooms; a build without that zone (`--zones none`, another zone's preview) skips it."""
    if 'primary_suite' not in ctx.stats:
        return 'zone primary_suite not built: skipped'
    from .zones import primary_suite
    return primary_suite.fit_out(ctx)


# v7 bedrooms -------------------------------------------------------------------------------------------------------
# Eighth round (2026-11-24), stage B, track "bedrooms" (revision_spec, section "v7 bedrooms"; geometry in
# bl/zones/bedrooms_rooms.py and bl/zones/baths_suite3.py). They run after laundry_closet (Bedroom 4's door wall) and
# bedroom3_bath_window (W11), before floor_gaps, skirting_trim and white_windows.
def bedrooms_west_windows(ctx):
    """16. Bedroom 4's west window W12 is 5'-0" wide and centred on the room's west wall, as on the sheet; Bedroom 3's
    west window W10, which the sheet does not have, is closed while revision_spec.BED3_WEST_WINDOW is False (solid
    wall, paint and baseboard inside, stucco outside)."""
    from .zones import bedrooms_rooms
    return bedrooms_rooms.west_windows(ctx)


def bedroom3_rooms(ctx):
    """17. The wall between Bedroom 3 and its bath / closet as the sheet draws it: the bath's hinged 2'-4" door at the
    east end of the bath's south wall, the closet's 4'-8" opening with two sliding panels (the two pocket doors go);
    Bedroom 3's entry 2'-8" at the sheet's place, hinged on the north jamb; a leaf sized to its opening for Bedroom 4's
    entry; hinges, levers, liners, saddle, baseboards."""
    from .zones import bedrooms_rooms
    return bedrooms_rooms.rooms(ctx)


def bedroom3_fit_out(ctx):
    """18. Bedroom 3's bath fitted out on the sheet's layout (shower 3'-0", toilet bay 2'-6", vanity bay 2'-9", toilet
    and vanity on the north wall) and its closet as a reach-in fitted to its 2'-3 1/2" depth, after the warp and in
    plan feet; the picture over Bedroom 3's bed on the closed west wall; Bedroom 4's shade in the wider window."""
    from .zones import bedrooms_rooms
    return bedrooms_rooms.fit_out(ctx)


# v7 hall -----------------------------------------------------------------------------------------------------------
# Eighth round (2026-11-24), stage B, track "hall" (revision_spec, section "v7 hall" and SUITE_ENTRY_* /
# SUITE_CLOSET_DOOR_*; geometry in bl/zones/hall_block.py). They run after bath_door and suite_rooms (which build the
# suite entry and the pocket door at their new numbers), before floor_gaps, skirting_trim and white_windows.
def hall_block(ctx):
    """19. Bedroom 2's closet block and the hall as the sheet draws them (audit F08, F09, F10, F11, F42, P3): the hall
    3'-3" wide beside a block 7'-8" x 4'-8" whose south face is 17'-4" from the rear wall, 3'-4" of hall south of it;
    Bedroom 2's south wall with its hinged 2'-8" entry and the closet's 6'-0" sliding doors; the furnace closet with
    a louvred 1'-8" door and the storage closet with a 2'-4" door; the shared bath's hinged 2'-4" door with a leaf;
    the open corner at the bath's north-east closed. (The concept's entry alcove, its doorless opening and the wall
    south of it are gone; the suite entry stands at the sheet's place, revision_spec.SUITE_ENTRY_SHEET_Z.)"""
    from .zones import hall_block as hb
    return hb.build(ctx)


def hall_block_fit_out(ctx):
    """20. Bedroom 2's closet fitted to its 6'-10" x 1'-11" and the hall's ledge, picture, switch and lights placed
    in the 3'-3" / 3'-4" hall (nothing deeper than 6 in on a hall wall), after the warp and in plan feet."""
    from .zones import hall_block as hb
    return hb.fit_out(ctx)


# v7 garage ---------------------------------------------------------------------------------------------------------
def garage_v7(ctx):
    """Eighth round, stage B, the garage track (bl/garage.py; numbers bl/garage_spec.py): the vehicle door's opening
    15'-0" wide with its head 7'-0" above the garage floor, the garage floor 11 in below the house floor with the
    step at the house door, the door between house and garage at the sheet's place and hinged on its north jamb,
    the garage's side door in the east wall, the front door with a sidelight each side, and the tank water heater in
    the garage's north-east corner. Runs before floor_gaps, skirting_trim and white_windows (which gives the
    sidelights their grid bars). Each step reports under its own name; one that fails reads FAILED."""
    from . import garage
    return garage.apply(ctx)


# v7 site ------------------------------------------------------------------------------------------------------------
def site_shell(ctx):
    """Eighth round (2026-11-24), stage B, track "site": the shell pieces that meet the ground work (audit F61, P2,
    F50; the ground, the landings, the porch slab and the walls below the floor line are bl/zones/exterior_site.py).

    * Outside corners. The exterior walls stop on each other's centre lines, which left a square of wall open,
      floor to 8 ft, at four outside corners (rear west, rear east, the garage's front east, Bedroom 3's front
      west) and at the two front corners beside the porch (Bedroom 3's and the garage's, behind the porch's
      piers). The concept's three "stucco front corner return"
      boxes stood on the side walls beside the front corners, wider than the walls (0.035 ft proud outside, 0.02
      to 0.09 ft into the rooms). Each of them now IS the missing corner: it fills the open square exactly, its
      two outer faces on the sheet's wall lines, the other two against the wall ends. Three copies close the rear
      corners and the garage's corner at the porch. All faces are stucco.
    * Porch. The paving at house-floor level is taken out: the porch floor is the exterior's slab at
      exterior_layout.PORCH_TOP (-0.4583 since the repair: two risers of 5 1/2 in; A1.3's -0.336 before). The two
      baseboards on the porch's side walls ran on from the foyer in one piece; each is cut in the front door wall
      and its porch part is removed (no baseboard outdoors: the porch walls are clad from the slab to the soffit,
      bl/roof.py).   v7 final: comment (it gave -0.336 and porch parts standing on the lower slab)"""
    from .zones import exterior_layout as L
    out = {}

    def edge(pat, k, pick, default):
        """bbox coordinate k (0 x0, 1 x1, 4 z0, 5 z1) of the shell walls named `pat`; `default` if they are gone
        or renamed (the walls' centre lines, where they have always ended)."""
        v = [bbox(o)[k] for o in find(pat) if o.type == 'MESH' and re.match(r'^\d+ ' + pat, o.name)
             and any(c.name == COLL_SHELL for c in o.users_collection)]
        if not v:
            return default
        got = pick(v)
        return got if abs(got - default) < 0.05 else default

    half = R.WALL / 2
    front = (R.WALL - R.STUCCO) / 2                    # the three front walls' shell box, behind the stucco skin
    xw = edge('(Primary — rear wall|Bedroom 3 front wall beside bay)', 0, min, R.XW_OUT + half)
    xe_rear = edge('Living — rear wall', 1, max, R.XE_OUT - half)
    xe_gar = edge('Garage — front / vehicle door', 1, max, R.XE_OUT - half)
    zn_w = edge('Primary — west wall', 4, min, R.ZN_OUT + half)
    zn_e = edge('Living / kitchen — east wall', 4, min, R.ZN_OUT + half)
    z_gar = edge('Garage — east side', 5, max, R.Z_GAR_S + front)
    z_b3w = edge('Bedroom 3 front extension west pier', 5, max, R.Z_B3_S + front)
    z_b3e = edge('Bedroom 3 / recessed porch exterior', 5, max, R.Z_B3_S + front)
    x_b3e = edge('Bedroom 3 front wall beside bay', 1, max, (R.FOYER_WALL[0] + R.FOYER_WALL[1]) / 2)
    x_garw = edge('Garage — front / vehicle door', 0, min, (R.X_FOYER_E + R.X_GAR_W) / 2)
    z_garw = edge('Garage interior access — south wall', 5, max, R.Z_GAR_S + front)
    returns = sorted((o for o in find(r'stucco front corner return') if o.type == 'MESH'),
                     key=lambda o: bbox(o)[0])
    # v7 repair: the two corner pieces beside the porch had their porch-side face IN the plane of the porch's side
    # wall, where the pier's face lies too (two stucco faces in one plane behind each pier, and a bare stucco strip
    # 0.04 ft wide between the wall's finish and the pier). That face stands 0.004 ft back now: the porch's wood
    # cladding (bl/roof.porch) covers it up to the pier and the pier from there on.
    PORCH_CORNER_BACK = 0.004
    corners = {
        'Bedroom 3 front west': (R.XW_OUT, xw, z_b3w, R.Z_B3_OUT),
        'Bedroom 3 front, porch side': (x_b3e, R.FOYER_WALL[1] - PORCH_CORNER_BACK, z_b3e, R.Z_B3_OUT),
        'garage front east': (xe_gar, R.XE_OUT, z_gar, R.Z_GAR_OUT),
        'rear west': (R.XW_OUT, xw, R.ZN_OUT, zn_w),
        'rear east': (xe_rear, R.XE_OUT, R.ZN_OUT, zn_e),
        'garage front, porch side': (R.X_FOYER_E + PORCH_CORNER_BACK, x_garw, z_garw, R.Z_GAR_OUT),
    }
    if len(returns) == 3:
        pieces = list(zip(list(corners)[:3], returns))
        pieces += [(k, _copy(returns[0], f'{returns[0].name} · {k}')) for k in list(corners)[3:]]
        for k, ob in pieces:
            x0, x1, z0, z1 = corners[k]
            _reshape(ob, x0, x1, 0.0, 8.0, z0, z1)
            for poly in ob.data.polygons:
                poly.material_index = 1                # stucco on every face
            out[k] = [round(v, 4) for v in (x0, x1, z0, z1)]
    else:
        out['corners'] = f'FAILED: {len(returns)} corner returns found, 3 expected'
    # ---- porch
    out['porch paving removed'] = remove(find(r'Open front porch paving', COLL_SHELL))
    px0, px1, pz0, _ = R.ROOMS['porch']
    cut = R.Z_FOYER_S + 0.05                            # inside the front door wall
    for ob in [o for o in find(r'Painted skirting', COLL_SHELL) if o.type == 'MESH']:
        x0, x1, y0, y1, z0, z1 = bbox(ob)
        on_side = (abs((x0 + x1) / 2 - px0) < 0.1 or abs((x0 + x1) / 2 - px1) < 0.1) and (z1 - z0) > (x1 - x0)
        if not on_side or z1 < pz0 + 0.5 or y0 < -0.1:
            continue
        if z0 < cut - 0.1:                              # the foyer's part stays where it is
            _reshape(_copy(ob, f'{ob.name} · foyer'), x0, x1, y0, y1, z0, cut)
        # v7 repair: no baseboard outdoors. The porch part of each run (it had gone down with the slab) is removed:
        # the porch's two side walls are clad in wood from the slab to the roof (bl/roof.porch).
        out[re.sub(r'^\d+ ', '', ob.name)[-40:]] = 'porch part removed (z %.3f..%.3f)' % (max(z0, pz0 - 0.02), z1)
        bpy.data.objects.remove(ob, do_unlink=True)
    # v7 integrate: (1) the short baseboards on the PORCH face of the front door wall (what the front door unit with
    # its sidelights left of them, 3 in each side) go down with the slab like the two side walls' runs: they stood
    # 4 in above them at the two inside corners. (2) The wall between Bedroom 3 and the porch is one box from inside
    # the foyer out along the porch, and its east face was one face in the porch's wood cladding: the last 0.83 ft
    # of the foyer's west wall, beside the front door's sidelight, was wood. The box is cut in the middle of the
    # front door wall; the foyer part's east face is painted like the rest of the foyer.
    zc = R.Z_FOYER_S + R.WALL / 2
    low = []
    for ob in [o for o in find(r'Painted skirting — Centered front entrance', COLL_SHELL) if o.type == 'MESH']:
        x0, x1, y0, y1, z0, z1 = bbox(ob)
        if (z0 + z1) / 2 > zc and y0 > -0.1 and (x1 - x0) > (z1 - z0):
            # v7 repair: removed, not lowered (no baseboard outdoors; they stood inside the stucco skin)
            low.append([round(v, 3) for v in (x0, x1, z0, z1)])
            bpy.data.objects.remove(ob, do_unlink=True)
    out['front door wall, porch face baseboards removed'] = low
    for ob in [o for o in find(r'^\d+ Bedroom 3 / recessed porch exterior$', COLL_SHELL) if o.type == 'MESH']:
        x0, x1, y0, y1, z0, z1 = bbox(ob)
        if not (z0 < zc - 0.3 < zc + 0.3 < z1):
            continue
        paint = next((i for i, sl in enumerate(ob.material_slots) if sl.material and 'paint' in sl.material.name.lower()), None)
        inner = _copy(ob, f'{ob.name} · foyer')
        _reshape(inner, x0, x1, y0, y1, z0, zc)
        _reshape(ob, x0, x1, y0, y1, zc, z1)
        n = 0
        if paint is not None:
            w, _ = _world(inner)
            for poly in inner.data.polygons:
                cx = np.mean([w[i, 0] for i in poly.vertices]) / FT
                if abs(cx - x1) < 1e-3 and poly.material_index != paint:           # the face toward the foyer
                    poly.material_index = paint
                    n += 1
        out['foyer west wall beside the front door'] = {'cut at z': round(zc, 3), 'foyer part z': [round(z0, 3), round(zc, 3)],
                                                        'faces painted': n}
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
        # v7 integrate: the copies for the further stretches are made BEFORE the first one is clipped (a copy of the
        # clipped piece collapsed to zero length, so a run cut in two lost its second stretch)
        pieces = [ob] + [_copy(ob, f'{ob.name} {i}') for i in range(1, len(runs))]
        for piece, (a, b) in zip(pieces, runs):
            w, mw = _world(piece)
            if along_x:
                w[:, 0] = np.clip(w[:, 0], a * FT, b * FT)
            else:
                w[:, 1] = -np.clip(-w[:, 1] / FT, a, b) * FT
            _set_world(piece, w, mw)
        out[key] = [(round(a, 2), round(b, 2)) for a, b in runs] + [f'was {a0:.2f}..{a1:.2f}']
    return out


# ------------------------------------------------------------------------------- v7 repair (inside half)
def floor_level(ctx):
    """v7 repair (reviews P7 / E5): two floor pieces stood 0.008 ft (0.1 in) above the oak floor round them, the
    foyer's south end ('Hall in enclosed porch substrate') and Bedroom 3's front strip ('Bedroom 3 front extension
    substrate'): a lip across the foyer 4 ft inside the front door, along the middle of Bedroom 3's doorway and
    across Bedroom 3. Their tops come down to the oak's. Runs before floor_gaps."""
    oak = [bbox(o)[3] for o in find(r'^\d* ?Oak floor substrate$', COLL_SHELL)]
    if not oak:
        return 'no oak floor'
    top = max(oak)
    out = {}
    for ob in find(r'^\d* ?(Hall in enclosed porch substrate|Bedroom 3 front extension substrate)$', COLL_SHELL):
        b = bbox(ob)
        if 1e-4 < abs(b[3] - top) < 0.03:
            out[re.sub(r'^\d+ ', '', ob.name)] = {'top was': round(b[3], 4), 'now': round(top, 4),
                                                  'verts': move_face(ob, 'y', b[3], top, tol=0.002)}
    return out


def living_east_baseboard(ctx):
    """v7 repair (review E3): the living room's east wall carried only the room's own baseboard (0.39 ft with its
    reveal), which met the rear wall's 0.455 ft house baseboard in the north-east corner beside the sliding door
    with a step of 0.065 ft. The west wall has the house baseboard behind the room's own (0.003 ft back, so it reads
    as one 0.455 ft board with a line at 0.39); the east wall gets the same. Runs before skirting_trim."""
    own = find(r'^\d+ Living east — painted baseboard$', COLL_SHELL)
    src = find(r'^\d+ Painted skirting — Living — rear wall$', COLL_SHELL)
    if len(own) != 1 or not src:
        return f'not found ({len(own)}, {len(src)})'
    b, sb = bbox(own[0]), bbox(src[0])
    _like(src[0], 'Painted skirting — Living east wall', b[0] + 0.003, R.X_LIV_E + 0.002, sb[2], sb[3], b[4], b[5])
    return {'x': (round(b[0] + 0.003, 3), round(R.X_LIV_E + 0.002, 3)), 'y': (round(sb[2], 3), round(sb[3], 3)),
            'z': (round(b[4], 3), round(b[5], 3))}


def skirting_joints(ctx):
    """v7 repair (review E4 and the integration's list): the shell cuts every baseboard 0.02 ft short at both ends
    of its wall piece, so two runs on adjacent pieces of one wall leave about 0.046 ft of bare wall between them
    (the foyer's west wall opposite the garage door and beside the front door, under Bedroom 4's window jambs, ...).
    Where two runs of the same section lie on one line with up to 0.07 ft between their ends and nothing of an
    opening (a liner, a casing, a frame) stands in the gap, the first runs on to the second. Runs after
    skirting_trim."""
    runs = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and len(o.data.vertices) == 8 and SKIRT.search(o.name) \
                and any(c.name == COLL_SHELL for c in o.users_collection):
            b = bbox(o)
            runs.append((o, b, (b[1] - b[0]) >= (b[5] - b[4])))
    stops = [bbox(o) for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices)
             and any(c.name == COLL_OPEN for c in o.users_collection)]
    todo = []
    for oa, a, ax in runs:
        for ob, b, bx in runs:
            if ob is oa or ax != bx or abs(a[2] - b[2]) > 0.005 or abs(a[3] - b[3]) > 0.005:
                continue
            k = 4 if ax else 0                               # the section across the run
            if abs(a[k] - b[k]) > 0.006 or abs(a[k + 1] - b[k + 1]) > 0.006:
                continue
            g0, g1 = (a[1], b[0]) if ax else (a[5], b[4])
            if not 0.002 < g1 - g0 <= 0.07:
                continue
            gb = (g0, g1, a[2], a[3], a[4], a[5]) if ax else (a[0], a[1], a[2], a[3], g0, g1)
            if any(s[0] < gb[1] and s[1] > gb[0] and s[2] < gb[3] and s[3] > gb[2] and s[4] < gb[5] and s[5] > gb[4]
                   for s in stops):
                continue
            todo.append((oa, 'x' if ax else 'z', g0, g1))
    out = []
    for oa, axis, g0, g1 in todo:
        if move_face(oa, axis, g0, g1, tol=0.001) == 4:
            b = bbox(oa)
            out.append((re.sub(r'^\d+ Painted skirting — ', '', oa.name)[:34], axis, round(g0, 3), round(g1, 3),
                        round((b[0] + b[1]) / 2 if axis == 'z' else (b[4] + b[5]) / 2, 2)))
    return {'joints closed': len(out), 'runs': out}


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
        # v7 repair: a patch runs 0.16 ft past both ends of its seam (0.06 / 0.04 before). The probes cannot see a
        # seam under a baseboard, so the hall / living patch started 0.03 ft in front of the shared bath's corner
        # baseboard and left a pinhole to the foundation there (review P4). Under intact floor the patch is hidden.
        ex, ez = (0.16, 0.04) if along_x else (0.06, 0.16)
        px1 = x1 + ex
        # v7 verify: a seam along x that the probes lose within 0.75 ft of the east wall is patched on to the wall.
        # The hall / living seam tapers to a hairline there (0.012..0.028 in wide over x 38.86..39.25, in front of
        # the living / dining east window's south jamb) and stayed open to the foundation past the patch's end.
        if along_x and 0.0 < R.X_LIV_E - px1 < 0.75:
            px1 = R.X_LIV_E + 0.05
        patch = ctx.box(f'Floor seam patch {k}', x0 - ex, px1, y - 0.1, y - 0.0026, z0 - ez, z1 + ez,
                        None, COLL_SHELL)
        if src.data.materials:
            patch.data.materials.append(src.data.materials[0])
        out.append((re.sub(r'^\d+ ', '', name)[:24], round(x0, 2), round(x1, 2), round(z0, 3), round(z1, 3)))
    return out


# ------------------------------------------------------------- seventh round: white windows with grid lines
def _ww_rect(ob, u):
    """(u0, u1, y0, y1, n0, n1) of an object, SCENE feet, in the vertical plane whose horizontal direction on the
    plan is u = (ux, uz): u along the wall, y up, n square to the wall."""
    w, _ = _world(ob)
    x, y, z = w[:, 0] / FT, w[:, 2] / FT, -w[:, 1] / FT
    a, n = x * u[0] + z * u[1], z * u[0] - x * u[1]
    return (float(a.min()), float(a.max()), float(y.min()), float(y.max()), float(n.min()), float(n.max()))


def _ww_axis(ob):
    """Plan direction (ux, uz) of the long horizontal side of a pane (or of a shade's cassette)."""
    w, _ = _world(ob)
    x, z = w[:, 0] / FT, -w[:, 1] / FT
    dx, dz = np.ptp(x), np.ptp(z)
    if min(dx, dz) < 0.1:                                # in a wall along x or along z
        return (1.0, 0.0) if dx >= dz else (0.0, 1.0)
    val, vec = np.linalg.eigh(np.cov(np.vstack([x - x.mean(), z - z.mean()])))   # canted (the bay's sides)
    v = vec[:, int(np.argmax(val))]
    if v[0] < 0:
        v = -v
    return float(v[0]), float(v[1])


def _ww_daylight(p, members, near=0.08, eps=0.012):
    """The daylight openings of a pane: its rectangle p = (u0, u1, y0, y1), run to the frame members that stop just
    short of its edges (the shell's panes leave a slit beside the jambs) and divided by the members that cross it
    (mullions, transom bars). Members are rectangles in the pane's plane. Returns [(u0, u1, y0, y1), ...]."""
    u0, u1, y0, y1 = p
    w, h = u1 - u0, y1 - y0
    tall = [m for m in members if min(y1, m[3]) - max(y0, m[2]) > 0.6 * h]
    wide = [m for m in members if min(u1, m[1]) - max(u0, m[0]) > 0.6 * w]
    a = [m[1] for m in tall if m[0] < u0 + eps and abs(m[1] - u0) <= near]
    b = [m[0] for m in tall if m[1] > u1 - eps and abs(m[0] - u1) <= near]
    c = [m[3] for m in wide if m[2] < y0 + eps and abs(m[3] - y0) <= near]
    d = [m[2] for m in wide if m[3] > y1 - eps and abs(m[2] - y1) <= near]
    u0, u1, y0, y1 = max(a, default=u0), min(b, default=u1), max(c, default=y0), min(d, default=y1)
    cross = [m for m in members if min(u1, m[1]) - max(u0, m[0]) > eps and min(y1, m[3]) - max(y0, m[2]) > eps]

    def cuts(lo, hi, k):
        v = sorted({lo, hi} | {min(max(m[k + i], lo), hi) for m in cross for i in (0, 1)})
        return [t for i, t in enumerate(v) if i == 0 or t - v[i - 1] > 1e-4]
    us, ys = cuts(u0, u1, 0), cuts(y0, y1, 2)
    free = {(i, j) for i in range(len(us) - 1) for j in range(len(ys) - 1)
            if not any(m[0] < (us[i] + us[i + 1]) / 2 < m[1] and m[2] < (ys[j] + ys[j + 1]) / 2 < m[3] for m in cross)}
    out = []
    while free:
        todo, part = [free.pop()], set()
        while todo:
            i, j = todo.pop()
            part.add((i, j))
            for q in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if q in free:
                    free.discard(q)
                    todo.append(q)
        i0, i1 = min(i for i, _ in part), max(i for i, _ in part)
        j0, j1 = min(j for _, j in part), max(j for _, j in part)
        if len(part) != (i1 - i0 + 1) * (j1 - j0 + 1):
            raise RuntimeError(f'a glass opening is not a rectangle: {p}')
        if us[i1 + 1] - us[i0] > 0.25 and ys[j1 + 1] - ys[j0] > 0.25:
            out.append((us[i0], us[i1 + 1], ys[j0], ys[j1 + 1]))
    return sorted(out)


def _ww_layout(bays, tiers, cells, lite, max_ratio, keep=None):
    """Columns per bay and rows per tier of one window. bays: [(u0, u1)], tiers: [(y0, y1, is_transom)], cells: the
    (bay, tier) pairs that are glass. A transom tier is one row; every other lite is brought as close to the house's
    lite (width, height) as whole numbers allow, in log space, with no lite wider than max_ratio times its height.
    Rows are shared by the bays of a tier and columns by the tiers of a bay, so the bars run on in line."""
    import itertools
    w0, h0 = lite
    if keep:
        return [keep[0]] * len(bays), [1 if t[2] else keep[1] for t in tiers]
    best = None
    opts = [[1] if t[2] else range(1, 13) for t in tiers]
    for rows in itertools.product(*opts):
        cols, total = [], 0.0
        for i, (a, b) in enumerate(bays):
            def cost(c):
                s = 0.0
                for j, t in enumerate(tiers):
                    if (i, j) not in cells or t[2]:
                        continue
                    w, h = (b - a) / c, (t[1] - t[0]) / rows[j]
                    s += abs(math.log(w / w0)) + abs(math.log(h / h0)) + (1000.0 if w / h > max_ratio else 0.0)
                return s if s else abs(math.log((b - a) / c / w0))
            c = min(range(1, 13), key=lambda c: (cost(c), c))
            cols.append(c)
            total += cost(c)
        key = (round(total, 9), sum(cols) + sum(rows))
        if best is None or key < best[0]:
            best = (key, cols, list(rows))
    return best[1], best[2]


def white_windows(ctx):
    """Seventh round (2026-11-21), the owner: "Set all windows to white color, and it should have grid line for these
    windows". One late revision for every window and glazed door of the built model, whoever built it (the shell, the
    kitchen's W08, the revisions above), so a window that is added or moved later is covered without another edit.
    Numbers: revision_spec.WINDOW_*.

    * WHITE: every frame piece in the `openings` collection that carries the black aluminium (heads, sills, jambs,
      mullions, transom bars, the rails and stiles of the primary bedroom's slider and of the living room's garden
      door D14, the bay's sash jambs and rails, the entry's upper window) gets the library's satin white
      `window_white`; so do the pieces named in WINDOW_WHITE_ALSO (the primary bath's stool and mullion post, the
      slider's pull bar). The skylights keep their frames; shower glass, mirrors, cabinet glass, the garage door
      and the front door are not windows here.
    * GRID: each daylight opening (the glass between two frame members) is divided into lites as close to the
      house's lite WINDOW_LITE as whole numbers allow (_ww_layout). The sashes of one window share their rows and a
      transom keeps the columns of the sash under it and is one row, so the bars run on in line across mullions and
      transoms, and windows of one height get the same rows all round the house. Bars are WINDOW_BAR_W wide and
      stand WINDOW_BAR_PROUD off each face of the glass: one piece through the pane (no face of a bar lies in a
      face of the glass), the vertical bars continuous, the horizontal ones between them, all ending in the frame
      members. Where a sash is shallower than the bars are proud (the slider's panels) they stop just inside it.
      The kitchen's W08 keeps the 2 x 4 lites per sash of the owner's kitchen-window picture (WINDOW_GRID_KEEP);
      its bars are built here like all the others (bl/zones/kitchen_dining_window.py no longer builds black ones).
    * Two centre mullions that the conversion to the architect's plan left off centre (WINDOW_MULLION_CENTRE) go
      back to the middle of their windows first: with a grid the two sashes would show lites of two widths.
    * Shades stay in front of the grid: a roller shade that stands in or beyond its window's bars (the bay's three
      stood outside the glass) is turned square to its pane and set 0.01 ft on the room side of the bars. One that
      had to be turned (the bay's two side shades) is also set back in the middle of its pane.

    The glass is not touched: every pane stays the light portal lighting.add_window_portals makes of it (the bars
    are not glass and are skipped there)."""
    from mathutils import Matrix
    from . import revision_spec as RS
    from .common import DATA_DIR
    import json
    import os
    white = ctx.mat(RS.WINDOW_WHITE)
    was = bpy.data.materials.get('M_' + RS.WINDOW_FRAME_WAS)
    skip = re.compile(RS.WINDOW_SKIP, re.I)
    gone = remove([ob for ob in bpy.data.objects if re.search(RS.WINDOW_OLD_BARS, ob.name)])
    opens = [ob for ob in ctx.coll(COLL_OPEN).all_objects if ob.type == 'MESH' and len(ob.data.vertices)
             and not skip.search(ob.name)]
    frames = [ob for ob in opens if any(m is not None and m in (was, white) for m in ob.data.materials)]
    glass = [ob for ob in opens if ob.data.materials and ob.data.materials[0] is not None
             and ob.data.materials[0].name in RS.WINDOW_GLASS]
    panes = [(ob, u) for ob, u in ((ob, _ww_axis(ob)) for ob in glass)
             if (lambda r: r[3] - r[2] > 0.5 and r[5] - r[4] < 0.3)(_ww_rect(ob, u))]   # upright and flat

    def in_plane(pr, u):
        """Frame members in the plane of a pane (rectangle pr, direction u), as rectangles with their object."""
        out = []
        for ob in frames:
            m = _ww_rect(ob, u)
            if m[5] > pr[4] - 0.02 and m[4] < pr[5] + 0.02 and m[5] - m[4] < 0.7 \
                    and m[1] > pr[0] - 0.3 and m[0] < pr[1] + 0.3 and m[3] > pr[2] - 0.3 and m[2] < pr[3] + 0.3:
                out.append(m + (ob,))
        return out

    # mullions the warp left off centre: back to the middle of their window
    centred = {}
    for ob, u in panes:
        if not any(re.search(p, ob.name) for p in RS.WINDOW_MULLION_CENTRE):
            continue
        pr = _ww_rect(ob, u)
        mem = in_plane(pr, u)
        tall = [m for m in mem if min(pr[3], m[3]) - max(pr[2], m[2]) > 0.6 * (pr[3] - pr[2])]
        mid = [m for m in tall if m[0] > pr[0] + 0.2 and m[1] < pr[1] - 0.2]
        if len(mid) != 1:
            raise RuntimeError(f'{ob.name!r}: {len(mid)} mullions, expected 1')
        left = max([m[1] for m in tall if m[1] < mid[0][0]], default=pr[0])
        right = min([m[0] for m in tall if m[0] > mid[0][1]], default=pr[1])
        d = (left + right) / 2 - (mid[0][0] + mid[0][1]) / 2
        mid[0][6].location += Vector((u[0] * d * FT, -u[1] * d * FT, 0.0))
        centred[re.sub(r'^\d+ ', '', ob.name)] = round(d, 3)
    bpy.context.view_layer.update()

    # daylight openings of every pane
    lights, depth = [], {}
    for ob, u in panes:
        pr = _ww_rect(ob, u)
        mem = in_plane(pr, u)
        depth[ob.name] = [pr[4] - RS.WINDOW_BAR_PROUD, pr[5] + RS.WINDOW_BAR_PROUD]
        for o in _ww_daylight(pr[:4], [m[:4] for m in mem]):
            by = [m for m in mem if m[1] > o[0] - 0.02 and m[0] < o[1] + 0.02 and m[3] > o[2] - 0.02 and m[2] < o[3] + 0.02]
            n0, n1 = pr[4] - RS.WINDOW_BAR_PROUD, pr[5] + RS.WINDOW_BAR_PROUD
            lo, hi = max([m[4] for m in by], default=n0 - 1) + 0.004, min([m[5] for m in by], default=n1 + 1) - 0.004
            if lo > n0 and pr[4] - lo >= 0.015:          # the sash is shallower than the bar is proud: stop inside it
                n0 = lo
            if hi < n1 and hi - pr[5] >= 0.015:
                n1 = hi
            lights.append({'ob': ob, 'u': u, 'r': o, 'n': (n0, n1), 'nm': (pr[4] + pr[5]) / 2})
            depth[ob.name] = [n0, n1]

    # openings of one window: side by side or one above the other in one plane
    group = list(range(len(lights)))

    def root(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i
    for i, a in enumerate(lights):
        for j in range(i + 1, len(lights)):
            b = lights[j]
            if abs(a['u'][0] * b['u'][0] + a['u'][1] * b['u'][1]) < 0.999 or abs(a['nm'] - b['nm']) > 0.35:
                continue
            (au0, au1, ay0, ay1), (bu0, bu1, by0, by1) = a['r'], b['r']
            ou, oy = min(au1, bu1) - max(au0, bu0), min(ay1, by1) - max(ay0, by0)
            if a['ob'] is b['ob'] or (-ou <= 0.45 and oy > 0.5 * min(ay1 - ay0, by1 - by0)) \
                    or (-oy <= 0.45 and ou > 0.5 * min(au1 - au0, bu1 - bu0)):
                group[root(i)] = root(j)
    windows = {}
    for i, a in enumerate(lights):
        windows.setdefault(root(i), []).append(a)

    # the schedule's number of each window (data/measurements.json, the architect's plan)
    with open(os.path.join(DATA_DIR, 'measurements.json')) as f:
        meas = json.load(f)

    def centre(ws):
        u = ws[0]['u']
        ua = sum((a['r'][0] + a['r'][1]) / 2 for a in ws) / len(ws)
        nm = sum(a['nm'] for a in ws) / len(ws)
        return ua * u[0] - nm * u[1], ua * u[1] + nm * u[0]

    def label(ws):
        u = ws[0]['u']
        cx, cz = centre(ws)
        for w in meas['windows']:
            if w.get('kind') == 'skylight' or w['axis'] not in ('x', 'z'):
                continue
            along, across = (cx, cz) if w['axis'] == 'x' else (cz, cx)
            if w['start'] - 0.3 <= along <= w['end'] + 0.3 and abs(across - w['c']) < 2.6 \
                    and abs(u[0] if w['axis'] == 'x' else u[1]) > 0.5:
                return w['id']
        for d in meas['doors']:
            if 'lazed' in d.get('type', '') and d['axis'] in ('x', 'z'):
                along, across = (cx, cz) if d['axis'] == 'x' else (cz, cx)
                if d['start'] - 3.0 <= along <= d['end'] + 3.0 and abs(across - d['c']) < 3.0:
                    return d['id']
        return re.sub(r'^\d+ ', '', ws[0]['ob'].name)[:24]

    # lay out and build the bars, one mesh per window
    bw, bars_total, grids = RS.WINDOW_BAR_W, 0, {}
    named = {}
    for ws in windows.values():
        named.setdefault(label(ws), []).append(ws)
    for name, parts in sorted(named.items()):
        parts.sort(key=centre)
        for k, ws in enumerate(parts):
            tag = name if len(parts) == 1 else f'{name}{"abcdefgh"[k]}'
            bays, tiers = [], []
            for a in ws:
                if not any(abs(a['r'][0] - b[0]) < 0.05 and abs(a['r'][1] - b[1]) < 0.05 for b in bays):
                    bays.append(a['r'][:2])
                if not any(abs(a['r'][2] - t[0]) < 0.05 and abs(a['r'][3] - t[1]) < 0.05 for t in tiers):
                    tiers.append(a['r'][2:])
            bays.sort()
            tiers.sort()
            tiers = [(t[0], t[1], any(s[1] <= t[0] + 0.3 and t[1] - t[0] < RS.WINDOW_TRANSOM_RATIO * (s[1] - s[0]) for s in tiers))
                     for t in tiers]

            def cell(a):
                return (next(i for i, b in enumerate(bays) if abs(a['r'][0] - b[0]) < 0.05 and abs(a['r'][1] - b[1]) < 0.05),
                        next(j for j, t in enumerate(tiers) if abs(a['r'][2] - t[0]) < 0.05 and abs(a['r'][3] - t[1]) < 0.05))
            cells = {cell(a) for a in ws}
            keep = next((v for p, v in RS.WINDOW_GRID_KEEP.items() if any(re.search(p, a['ob'].name) for a in ws)), None)
            cols, rows = _ww_layout(bays, tiers, cells, RS.WINDOW_LITE, RS.WINDOW_LITE_MAX_RATIO, keep)
            boxes = []
            for a in ws:
                i, j = cell(a)
                (u0, u1, y0, y1), (n0, n1), c, r = a['r'], a['n'], cols[i], rows[j]
                ucs = [u0 + (u1 - u0) * q / c for q in range(1, c)]
                for uc in ucs:
                    boxes.append((a['u'], uc - bw / 2, uc + bw / 2, y0 - 0.004, y1 + 0.004, n0, n1))
                ends = [u0 - 0.004] + [v for uc in ucs for v in (uc - bw / 2, uc + bw / 2)] + [u1 + 0.004]
                for q in range(1, r):
                    yc = y0 + (y1 - y0) * q / r
                    for s in range(0, len(ends), 2):
                        boxes.append((a['u'], ends[s], ends[s + 1], yc - bw / 2, yc + bw / 2, n0, n1))
            sizes = sorted({(round((bays[i][1] - bays[i][0]) / cols[i] * 12, 1), round((tiers[j][1] - tiers[j][0]) / rows[j] * 12, 1))
                            for i, j in cells})
            grids[tag] = ' + '.join(f'{cols[i]}x{rows[j]}' for j in range(len(tiers)) for i in range(len(bays)) if (i, j) in cells) \
                + ' lites ' + ', '.join(f'{w:g}x{h:g}' for w, h in sizes) + ' in'
            if not boxes:
                continue
            verts, faces = [], []
            for (ux, uz), a0, a1, b0, b1, c0, c1 in boxes:
                base = len(verts)
                for cn in (c0, c1):
                    for bv in (b0, b1):
                        for av in (a0, a1):
                            verts.append(ft2bl(av * ux - cn * uz, bv, av * uz + cn * ux))
                faces += [tuple(base + q for q in f) for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6),
                                                                (0, 2, 6, 4), (1, 5, 7, 3))]
            org = sum(verts, Vector()) / len(verts)
            ob = ctx.mesh_object(f'{tag} window grid bars', [v - org for v in verts], faces, RS.WINDOW_WHITE, COLL_OPEN)
            ob.location = org
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(ob.data)
            bm.free()
            ctx.add_bevel(ob, RS.WINDOW_BAR_BEVEL, 2)
            bars_total += len(boxes)

    # shades hang square to their window, on the room side of its bars
    shades, seated, slid = {}, {}, {}
    for ob in bpy.data.objects:
        m = re.match(RS.WINDOW_SHADES, ob.name)
        if m and ob.type == 'MESH' and ob.parent is None and len(ob.data.vertices):
            shades.setdefault(m.group(1), []).append(ob)
    for tag, obs in sorted(shades.items()):
        lead = max(obs, key=lambda o: (o.name.endswith('cassette'), max(o.dimensions)))
        v, best = _ww_axis(lead), None
        for ob, u in panes:
            pr, r = _ww_rect(ob, u), _ww_rect(lead, u)
            over = min(pr[1], r[1]) - max(pr[0], r[0])
            gap = max(r[4] - pr[5], pr[4] - r[5], 0.0)
            if abs(u[0] * v[0] + u[1] * v[1]) > 0.99 and over > 0.5 and gap < 0.5 and r[3] > pr[2] and r[2] < pr[3] + 0.3 \
                    and (best is None or (round(over, 2), -gap) > best[0]):
                best = ((round(over, 2), -gap), ob, u, pr)
        if best is None:
            continue
        _, pane, u, pr = best
        if u[0] * v[0] + u[1] * v[1] < 0:
            v = (-v[0], -v[1])
        turn = math.atan2(v[0] * u[1] - v[1] * u[0], v[0] * u[0] + v[1] * u[1])      # on the plan, from the shade to the pane
        if abs(turn) > 1e-4:
            x0, x1, y0, y1, z0, z1 = bbox(lead)
            pv = ft2bl((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            rot = Matrix.Translation(pv) @ Matrix.Rotation(-turn, 4, 'Z') @ Matrix.Translation(-pv)
            for ob in obs:
                ob.matrix_basis = rot @ ob.matrix_basis
            bpy.context.view_layer.update()
            # A shade that had to be turned hangs in a canted facet (the bay's sides), which the conversion
            # stretched while the shade was carried rigidly with whatever it touched: it stood off the middle of
            # its sash, toward the corner pier, by 0.19 ft until the seventh round and by 0.26 ft with the 5 in
            # walls. Back to the middle of its pane (a facet has one), where the zone hangs it.
            r = _ww_rect(lead, u)
            a = (pr[0] + pr[1]) / 2 - (r[0] + r[1]) / 2
            if abs(a) > 1e-4:
                for ob in obs:
                    ob.location += Vector((u[0] * a * FT, -u[1] * a * FT, 0.0))
                bpy.context.view_layer.update()
                slid[tag] = round(a, 3)
        rs = [_ww_rect(ob, u) for ob in obs]
        lo, hi = min(r[4] for r in rs), max(r[5] for r in rs)
        ua, nm = (pr[0] + pr[1]) / 2, (pr[4] + pr[5]) / 2
        room = (RS.WINDOW_HOUSE_CENTRE[0] - (ua * u[0] - nm * u[1])) * -u[1] + (RS.WINDOW_HOUSE_CENTRE[1] - (ua * u[1] + nm * u[0])) * u[0]
        b0, b1 = depth[pane.name]
        d = (b0 - 0.01 - hi if hi > b0 else 0.0) if room < 0 else (b1 + 0.01 - lo if lo < b1 else 0.0)
        if d:
            for ob in obs:
                ob.location += Vector((-u[1] * d * FT, -u[0] * d * FT, 0.0))
        if d or abs(turn) > 1e-4:
            seated[tag] = (round(math.degrees(turn), 2), round(d, 3))
    bpy.context.view_layer.update()

    # white frames, sashes, mullions and transom bars; white stools
    n = 0
    for ob in frames + [o for p in RS.WINDOW_WHITE_ALSO for o in find(p) if o.type == 'MESH']:
        if ob.data.users > 1:
            ob.data = ob.data.copy()
        every = ob not in frames
        for s in range(len(ob.data.materials)):
            if every or ob.data.materials[s] is was:
                ob.data.materials[s] = white
        n += 1
    left = sorted({ob.name for ob in opens if was is not None and was in list(ob.data.materials)})
    if left:
        raise RuntimeError(f'frame pieces left black: {left[:5]}')
    bpy.context.view_layer.update()
    return {'panes': len(panes), 'windows': len(grids), 'white pieces': n, 'bars': bars_total, 'old bars removed': gone,
            'mullions centred': centred, 'shades re-seated (deg, ft)': seated,
            'turned shades centred on their pane (ft along it)': slid, 'grids': grids}


def apply(ctx):
    bpy.context.view_layer.update()
    res = {}
    for f in (ceiling_seam, ceiling_overlap, floor_seam, floor_overlap, foyer_corner, bedroom4_flat, bay_to_floor, primary_slider,
              bedroom2_tall_window, living_slider, primary_west_window, living_east_windows,   # v7 glazing
              primary_west_window_south,                                         # v7 final: W14 like W15
              bedroom3_bath_window,
              bath_door, bath_window,
              roof_v7,                                                           # v7 roof (before the skylights)
              kitchen_skylight, living_skylight, foyer_skylights, primary_bath_skylight, entry_vault_closure,
              laundry_closet,
              suite_rooms, suite_fit_out,
              primary_bath_fit_out,
              hall_block, hall_block_fit_out,                                    # v7 hall
              bedrooms_west_windows, bedroom3_rooms, bedroom3_fit_out,           # v7 bedrooms
              garage_v7,                                                         # v7 garage
              site_shell,                                                        # v7 site
              floor_level, floor_gaps, living_east_baseboard, skirting_trim, skirting_joints,   # v7 repair: floor_level,
              white_windows):                                                    # living_east_baseboard, skirting_joints
        try:
            res[f.__name__] = f(ctx)
        except Exception as e:                       # report, keep building
            import traceback
            traceback.print_exc()
            res[f.__name__] = f'FAILED: {e!r}'
        bpy.context.view_layer.update()
    return res
