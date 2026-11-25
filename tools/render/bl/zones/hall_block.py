"""Bedroom 2's closet block, the hall and the doors around it as the architect's sheet draws them (eighth round,
2026-11-24, stage B, track "hall"; audit F08, F09, F10, F11, F42, P3). Runs inside Blender AFTER the warp, from
bl/revisions.hall_block and bl/revisions.hall_block_fit_out, so every number here is SCENE feet on the architect's
plan (the sheet's frame, tools/render/relayout.py); the positions are bl/revision_spec's "v7 hall" block.

Until the seventh round this corner of the house kept the concept plan: an entry alcove 5'-4" wide, open to Bedroom 2
and entered through a doorless opening one wall further south; a 4'-9" closet beside it; a hall 5'-8" deep; no
furnace closet, no storage closet; a shared bath without a door leaf; the suite entry 1'-8" south of its place.

build(ctx), the walls and doors:
* Bedroom 2's south wall (sheet WL16) runs from the hall's west wall to the living-room wall, with the bedroom's
  entry D12 (hinged 2'-8", west jamb, the leaf open at 90 degrees along the bedroom's west wall) and the closet's
  6'-0" opening D13 (two white bypass panels in the wall's thickness, a black top track between the two halves of
  the head trim, flush pulls, a floor guide; both panels stand at the west end as the sheet draws them);
* the closet block (7'-8" x 4'-8" over its walls): its west wall (WL28) with the furnace closet's louvred 1'-8" door,
  the wall between Bedroom 2's closet and the two small closets (WL27), their divider (WL29), the south wall (WL30)
  with the storage closet's flush 2'-4" door; the wall to the living room (WL14) runs on to the block's south face.
  Both small doors are shown closed, with hinges and a pull / a lever;
* the shared bath's door D07 at the sheet's place (hinged 2'-4", east jamb, the leaf open at 90 degrees along the
  bath's east wall, an oak saddle), the bath's wall tile re-cut around it, and the open quarter at the bath's
  north-east outside corner closed (P3: the north wall runs through, the east wall butts against it);
* jamb liners and head trim like the house's other doors, baseboards on every new face, the old runs carried to the
  new jambs and corners; the concept's pieces that have no place any more are removed.
Shell pieces are reshaped where they keep their role (they keep their `scene_index`); new wall pieces are copies of
a wall, so they bake as walls and carry the interior paint on every face. The suite entry (D09) and the walk-in
closet's pocket door (D18) are built by bl/zones/primary_suite_rooms.py at their new numbers; this module only
re-fits the hall face's baseboards around the entry.

fit_out(ctx), what stands in the rooms:
* Bedroom 2's closet (6'-10" x 1'-11"): shelf, chrome rod, a shelf tower at the east end, hanging shirts and jackets,
  folded stacks, a basket, a recessed can;
* the hall: a 6 in deep walnut ledge with the horizon canvas over it on the block's south face (the only wall of
  the hall that is not a door), the bottle vase with dried grass, two books and a bowl on it; the two-gang switch at
  the block's corner; a flush ring light where the two legs meet and a
  recessed can in each leg. Nothing on a hall wall is deeper than 6 in, so the 3'-3" and 3'-4" legs keep 2'-10" clear.
"""
import math
import re

import bmesh
import bpy
from mathutils import Vector

from .. import revision_spec as RS
from ..common import FT, ft2bl
from ..revisions import COLL_OPEN, COLL_SHELL, _like, _paint_all, _reshape, bbox, find, move_face, remove

R = RS.R
SKIRT_PROUD, SKIRT_SUNK = 0.050, 0.002        # the house's baseboard section: off the wall face / into it
EMBED = 0.01                                  # a wall end that butts into another wall's side runs this far into it
LEAF_TOP = RS.DOOR_HEAD - 0.08 - 0.015        # a hinged leaf's top: 3/16 in under the head liner, so it can close
LN = RS.DOOR_LINER
C = COLL_OPEN


def _r(v):
    return [round(float(a), 3) for a in v]


def _shell_boxes(name):
    """Plain 8-vertex shell boxes named '<index> <name>', west to east / north to south."""
    obs = [o for o in find(rf'^\d+ {re.escape(name)}$', COLL_SHELL) if o.type == 'MESH' and len(o.data.vertices) == 8]
    return sorted(obs, key=lambda o: (bbox(o)[0], bbox(o)[4]))


def _one(name, pick=lambda b: True, what=None):
    obs = [o for o in _shell_boxes(name) if pick(bbox(o))]
    if len(obs) != 1:
        raise RuntimeError(f'{what or name}: {len(obs)} shell pieces, expected 1')
    return obs[0]


def _skirts(prefix, pick=lambda b: True):
    """Baseboard boxes of the shell whose name starts 'NNNN Painted skirting — <prefix>' (names are cut at 60)."""
    return [o for o in find(r'^\d+ Painted skirting — ' + re.escape(prefix), COLL_SHELL)
            if o.type == 'MESH' and len(o.data.vertices) == 8 and pick(bbox(o))]


def _set(ob, axis, lo=None, hi=None):
    """Move the low and / or the high end face of a box piece along `axis` ('x' | 'z')."""
    b = bbox(ob)
    k = 0 if axis == 'x' else 4
    for old, new in ((b[k], lo), (b[k + 1], hi)):
        if new is not None and abs(new - old) > 1e-7:
            n = move_face(ob, axis, old, new, tol=1e-4)
            if n != 4:
                raise RuntimeError(f'{ob.name!r}: {n} vertices at {axis} {old:.4f}, expected 4')


# ============================================================================================ doors
def _liners(ctx, tag, axis, wall, clear, proud, ends):
    """Painted jamb liners and head trim of an opening. axis: the direction the opening runs along; wall = the two
    wall faces across it; clear = the opening between the liners; proud = how far the liners stand off the two
    faces; ends = the two jambs' names."""
    (w0, w1), (c0, c1), (p0, p1) = wall, clear, proud
    hd = RS.DOOR_HEAD
    for nm, a0, a1, y0, y1 in ((f'{tag} jamb {ends[0]}', c0 - 2 * LN, c0, 0.0, hd - 0.08),
                               (f'{tag} jamb {ends[1]}', c1, c1 + 2 * LN, 0.0, hd - 0.08),
                               (f'{tag} head trim', c0 - 2 * LN, c1 + 2 * LN, hd - 0.08, hd + 0.06)):
        if axis == 'x':
            ctx.box(nm, a0, a1, y0, y1, w0 - p0, w1 + p1, 'paint_trim', C)
        else:
            ctx.box(nm, w0 - p0, w1 + p1, y0, y1, a0, a1, 'paint_trim', C)


def _leaf_pt(leaf):
    (ox, oz), (ax, az), (tx, tz) = leaf['corner'], leaf['along'], leaf['through']

    def pt(u, y, v):                 # u along the leaf from its hinge edge, v through it from its swing-side face
        return (ox + ax * u + tx * v, y, oz + az * u + tz * v)
    return pt


def _hinges(ctx, kit, tag, leaf):
    """Three black butt hinges on the pin axis (1/2 in barrels, 3 1/2 in high, with tips), as the primary bath's."""
    px, pz = leaf['pivot']
    r, hh = 0.021, 0.146
    for i, yh in enumerate(RS.DOOR_HINGE_Y):
        kit.cyl(f'{tag} hinge {i}', (px, yh - hh, pz), (px, yh + hh, pz), r, 'black_metal', 20)
        for k, ya in enumerate((yh - hh - 0.02, yh + hh)):
            kit.cyl(f'{tag} hinge {i} tip {k}', (px, ya, pz), (px, ya + 0.02, pz), r * 0.7, 'black_metal', 16)


def _levers(kit, tag, leaf, faces):
    """Lever handles (rose, neck, bar pointing to the hinge), as the primary bath's. faces: [(name, 'swing' | 'back')]."""
    pt = _leaf_pt(leaf)
    w, _, th = leaf['size']
    inset, yl = RS.DOOR_LEVER
    ul = w - inset
    for nm, side in faces:
        v0, sg = (0.0, -1.0) if side == 'swing' else (th, 1.0)
        kit.cyl(f'{tag} lever {nm} rose', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.02), 0.085, 'black_metal', 32)
        kit.cyl(f'{tag} lever {nm} neck', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.17), 0.03, 'black_metal', 20)
        kit.cyl(f'{tag} lever {nm} bar', pt(ul + 0.02, yl, v0 + sg * 0.15), pt(ul - 0.38, yl, v0 + sg * 0.15), 0.024,
                'black_metal', 20)


def _bar_pull(kit, tag, leaf, inset=0.16, y0=3.0, y1=3.5):
    """A 6 in round bar on two posts on the leaf's swing-side face, as the laundry closet's leaves."""
    pt = _leaf_pt(leaf)
    up, off = leaf['size'][0] - inset, 0.085
    kit.cyl(f'{tag} pull', pt(up, y0, -off), pt(up, y1, -off), 0.016, 'black_metal', 20)
    for k, yp in enumerate((y0 + 0.07, y1 - 0.07)):
        kit.cyl(f'{tag} pull post {k}', pt(up, yp, 0.0), pt(up, yp, -off), 0.012, 'black_metal', 16)
        kit.cyl(f'{tag} pull rose {k}', pt(up, yp, 0.0), pt(up, yp, -0.008), 0.026, 'black_metal', 20)


def _slab_leaf(ctx, leaf):
    return ctx.box_c(leaf['name'], leaf['center'], leaf['size'], leaf['rot'], 'door_slab', C, bevel=0.006, segments=2)


def _louvre_leaf(ctx, leaf):
    """A louvred leaf (the furnace closet's): stiles, top, lock and bottom rail and two fields of fixed blades that
    slope down toward the hall, lapping so that nothing shows through. One mesh in the leaf's own frame."""
    pt = _leaf_pt(leaf)
    w, h, th = leaf['size']
    y0 = leaf['center'][1] - h / 2
    stile, top, mid, bot = 0.21, 0.30, 0.33, 0.52
    ymid = y0 + 3.0
    bm = bmesh.new()

    def prism(u0, u1, sect):
        """sect: four (v, y) corners of the cross-section, counter-clockwise seen from +u."""
        vs = [bm.verts.new(ft2bl(*pt(u, y, v))) for u in (u0, u1) for v, y in sect]
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            bm.faces.new([vs[i] for i in q])

    def bar(u0, u1, ya, yb):
        prism(u0, u1, ((0.0, ya), (th, ya), (th, yb), (0.0, yb)))
    bar(0.0, stile, y0, y0 + h)
    bar(w - stile, w, y0, y0 + h)
    bar(stile, w - stile, y0, y0 + bot)
    bar(stile, w - stile, ymid - mid / 2, ymid + mid / 2)
    bar(stile, w - stile, y0 + h - top, y0 + h)
    pitch, rise, tk, inset = 0.085, 0.066, 0.022, 0.012
    blades = 0
    for ya, yb in ((y0 + bot, ymid - mid / 2), (ymid + mid / 2, y0 + h - top)):
        n = int((yb - ya - rise - tk) / pitch) + 1
        pad = (yb - ya - ((n - 1) * pitch + rise + tk)) / 2
        for i in range(n):
            y = ya + pad + i * pitch
            prism(stile, w - stile, ((inset, y), (th - inset, y + rise), (th - inset, y + rise + tk), (inset, y + tk)))
            blades += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(leaf['name'])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ctx.mat('door_slab'))
    ob = bpy.data.objects.new(leaf['name'], me)
    ctx.coll(C).objects.link(ob)
    ctx.add_bevel(ob, 0.004, 2)
    # v7 repair: a dark backing behind each field of blades, inside the leaf's thickness (between the blades' inner
    # edges and the leaf's closet face, let 0.01 ft into the stiles and rails): from below eye level one looked up
    # between the blades into the empty, lit closet. (A filter cloth behind a return-air door's louvres.)
    bm = bmesh.new()
    for ya, yb in ((y0 + bot, ymid - mid / 2), (ymid + mid / 2, y0 + h - top)):
        prism(stile - 0.01, w - stile + 0.01, ((th - inset + 0.002, ya - 0.01), (th - 0.004, ya - 0.01),
                                               (th - 0.004, yb + 0.01), (th - inset + 0.002, yb + 0.01)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mb = bpy.data.meshes.new(f"{leaf['name']} louvre backing")
    bm.to_mesh(mb)
    bm.free()
    mb.materials.append(ctx.mat('paint_black'))
    ctx.coll(C).objects.link(bpy.data.objects.new(mb.name, mb))
    return ob, blades


def _hinged(ctx, kit, tag, axis, wall, clear, proud, ends, leaf, levers=(), pull=False, louvre=False):
    _liners(ctx, tag, axis, wall, clear, proud, ends)
    out = {'clear': _r(clear), 'wall opening': _r((clear[0] - LN, clear[1] + LN)), 'head': RS.DOOR_HEAD,
           'leaf': _r(leaf['aabb']), 'leaf width': round(leaf['size'][0], 4)}
    if louvre:
        _, out['blades'] = _louvre_leaf(ctx, leaf)
    else:
        _slab_leaf(ctx, leaf)
    _hinges(ctx, kit, tag, leaf)
    if levers:
        _levers(kit, tag, leaf, levers)
    if pull:
        _bar_pull(kit, tag, leaf)
    return out


# ============================================================================================ walls, doors, trim
def build(ctx):
    from .. import laundry
    out = {}
    walls = RS.hall_block_walls()
    top = RS.HALL_CEILING
    n0, n1 = RS.BED2_SOUTH_WALL_Z
    wx0, wx1 = RS.BLOCK_WEST_WALL_X
    s0, s1 = RS.BLOCK_SOUTH_WALL_Z
    h0, h1 = RS.SHARED_BATH_NORTH_WALL_Z
    bw = RS.HALL_WEST[0]                                     # the hall's / Bedroom 2's west wall face
    b0, b1 = RS.BED2_DOOR_X
    c0, c1 = RS.BED2_CLOSET_DOOR_X
    f0, f1 = RS.FAU_DOOR_Z
    t0, t1 = RS.STO_DOOR_X
    d0, d1 = RS.SHARED_BATH_DOOR_X

    # ------------------------------------------------------------------ 1. the shell pieces as the warp left them
    north = _shell_boxes('Bedroom 2 upper closet — north')            # pier, header, east pier (west to east)
    if len(north) != 3 or bbox(north[1])[2] < 6.0:
        raise RuntimeError(f"Bedroom 2's closet wall: {[_r(bbox(o)) for o in north]}, expected pier, header, pier")
    pier, chead, epier = north
    ehead = _one('Bedroom 2 entry')
    cwest = _one('Bedroom 2 upper closet — west')
    csouth = _one('Upper closet — bottom wall KEPT')
    ereturn = _one('Bedroom 2 entry return')
    divider = _one('Bedroom 2 / living divider')
    bwest = _one('Shared bathroom north / walk-in south')
    bn = _shell_boxes('Original shared bath — north')                 # header, east piece
    if len(bn) != 2 or bbox(bn[0])[2] < 6.0:
        raise RuntimeError(f"shared bath north wall: {[_r(bbox(o)) for o in bn]}, expected header, east piece")
    bhead, beast = bn
    bside = _one('Original shared bath — east')
    for ob, k, want, what in ((pier, 4, n0, "closet wall's z"), (pier, 5, n1, "closet wall's z"),
                              (csouth, 4, R.Z_B2CLO_S, 'wall south of the closet'), (csouth, 5, R.Z_FAU_N, 'wall south of the closet'),
                              (divider, 0, R.X_BED2_E, 'living-room wall'), (divider, 1, R.X_LIV_W, 'living-room wall'),
                              (bhead, 0, RS.SHARED_BATH_DOOR_OLD_X[0], 'shared bath door'),
                              (bhead, 1, RS.SHARED_BATH_DOOR_OLD_X[1], 'shared bath door'),
                              (bwest, 4, h0, "shared bath wall's z"), (bwest, 5, h1, "shared bath wall's z"),
                              (bside, 0, R.X_SBATH_E, "shared bath's east wall"), (bside, 1, R.X_FOYER_W, "shared bath's east wall")):
        if abs(bbox(ob)[k] - want) > 0.02:
            raise RuntimeError(f'{what}: {ob.name!r} is at {_r(bbox(ob))}, the spec expects {want:.3f}')
    xe, xl = bbox(divider)[:2]                               # the living-room wall's two faces as built
    zh0, zh1 = bbox(bwest)[4:6]                              # the shared bath's north wall as built
    xf = bbox(bside)[1]                                      # the foyer passage's face of the bath's east wall

    # ------------------------------------------------------------------ 2. walls
    def new(name, x0, x1, y0, y1, z0, z1):
        ob = _like(csouth, name, x0, x1, y0, y1, z0, z1)
        _paint_all(ob)
        return ob

    def box_of(name):
        return list(walls[name][1])
    # Bedroom 2's south wall (WL16)
    b = box_of('Bedroom 2 south wall west of the entry')
    new('Bedroom 2 south wall west of the entry', b[0] - EMBED, *b[1:])
    _reshape(ehead, *box_of('Bedroom 2 entry'))                           # the old doorless entry's header: over D12 now
    _reshape(pier, *box_of('Bedroom 2 upper closet — north (pier)'))
    _reshape(chead, *box_of('Bedroom 2 upper closet — north (header)'))
    b = box_of('Bedroom 2 upper closet — north (east)')
    _reshape(epier, b[0], xe + EMBED, *b[2:])
    # the block's west wall (WL28)
    b = box_of('Bedroom 2 upper closet — west')
    _reshape(cwest, b[0], b[1], b[2], b[3], b[4] - EMBED, b[5])
    new('Furnace closet door header', *box_of('Furnace closet door header'))
    new('Closet block west wall south of the furnace door', *box_of('Closet block west wall south of the furnace door'))
    # the wall south of Bedroom 2's closet (WL27): its faces stay, its ends go to the block's west wall and into the
    # living-room wall
    _set(csouth, 'x', wx1 - EMBED, xe + EMBED)
    # the divider between the two small closets (WL29)
    b = box_of('Furnace / storage closet divider')
    new('Furnace / storage closet divider', b[0], b[1], b[2], b[3], bbox(csouth)[5] - EMBED, b[5] + EMBED)
    # the block's south wall (WL30): its east end butts on the living-room wall's west face as built
    new('Closet block south wall west of the storage door', *box_of('Closet block south wall west of the storage door'))
    new('Storage closet door header', *box_of('Storage closet door header'))
    b = box_of('Closet block south wall east of the storage door')
    new('Closet block south wall east of the storage door', b[0], xe, *b[2:])
    # the living-room wall (WL14) runs on to the block's south face
    _set(divider, 'z', None, s1)
    # the old wall south of the alcove has no place any more
    gone = remove([ereturn])
    # the shared bath's north wall (WL19) and its door, and the corner P3: the north wall runs to the passage's
    # face, the east wall starts at the north wall's bath face
    _set(bwest, 'x', None, d0 - LN)
    hb = bbox(bhead)
    _reshape(bhead, d0 - LN, d1 + LN, hb[2], hb[3], zh0, zh1)
    _set(beast, 'x', d1 + LN, xf)
    _set(bside, 'z', zh1, None)
    for ob in (ehead, pier, chead, epier, cwest, csouth, divider, bwest, bhead, beast, bside):
        _paint_all(ob)
    out['walls'] = {'new': 7, 'reshaped': 11, 'removed': gone,
                    'block': _r((wx0, xl, n1, s1)), 'living-room wall z1': round(bbox(divider)[5], 4),
                    'P3 corner': _r((bbox(beast)[1], bbox(beast)[4])), 'bath east wall z0': round(bbox(bside)[4], 4)}

    # ------------------------------------------------------------------ 3. old trims
    gone = remove(find(r'^\d+ Bedroom 2 upper closet — north$', COLL_OPEN))
    gone += remove(find(r'^\d+ Original shared bath — north$', COLL_OPEN))
    out['old trims removed'] = gone

    # ------------------------------------------------------------------ 4. doors
    kit = laundry.Kit(ctx, C, None)
    pr = (RS.DOOR_LINER_PROUD, RS.DOOR_LINER_PROUD)
    doors = {}
    # D12, Bedroom 2's entry
    leaf = RS.bed2_door_leaf()
    leaf = dict(leaf, size=(leaf['size'][0], LEAF_TOP - RS.DOOR_LEAF_Y[0], leaf['size'][2]),
                center=(leaf['center'][0], (RS.DOOR_LEAF_Y[0] + LEAF_TOP) / 2, leaf['center'][2]),
                aabb=leaf['aabb'][:3] + (LEAF_TOP,) + leaf['aabb'][4:])
    doors['Bedroom 2 entry (D12)'] = _hinged(ctx, kit, 'Bedroom 2 entry door', 'x', (n0, n1), (b0, b1), pr, 'WE', leaf,
                                             levers=(('bedroom', 'swing'), ('hall', 'back')))
    # D07, the shared bath
    leaf = RS.shared_bath_door_leaf()
    ly0 = RS.SHARED_BATH_DOOR_LEAF_Y[0]
    leaf = dict(leaf, size=(leaf['size'][0], LEAF_TOP - ly0, leaf['size'][2]),
                center=(leaf['center'][0], (ly0 + LEAF_TOP) / 2, leaf['center'][2]),
                aabb=leaf['aabb'][:3] + (LEAF_TOP,) + leaf['aabb'][4:])
    bp = RS.SHARED_BATH_DOOR_LINER_PROUD
    doors['Shared bath (D07)'] = _hinged(ctx, kit, 'Shared bath door', 'x', (zh0, zh1), (d0, d1), bp, 'WE', leaf,
                                         levers=(('bath', 'swing'), ('hall', 'back')))
    sd = ctx.box('Shared bath door saddle', d0, d1, -0.005, RS.SHARED_BATH_DOOR_SADDLE_Y, zh0 - bp[0], zh1 + bp[1],
                 'white_oak_veneer', C)
    ctx.add_bevel(sd, 0.012, 2)
    # the furnace closet (louvred, closed) and the storage closet (flush, closed)
    for key, tag, axis, wall, clear, ends, lf, kw in (
            ('Furnace closet', 'Furnace closet door', 'z', (wx0, wx1), (f0, f1), 'NS', RS.fau_door_leaf(),
             dict(pull=True, louvre=True)),
            ('Storage closet', 'Storage closet door', 'x', (s0, s1), (t0, t1), 'WE', RS.sto_door_leaf(),
             dict(levers=(('hall', 'swing'),)))):
        lf = dict(lf, size=(lf['size'][0], LEAF_TOP - RS.DOOR_LEAF_Y[0], lf['size'][2]),
                  center=(lf['center'][0], (RS.DOOR_LEAF_Y[0] + LEAF_TOP) / 2, lf['center'][2]),
                  aabb=lf['aabb'][:3] + (LEAF_TOP,) + lf['aabb'][4:])
        doors[key] = _hinged(ctx, kit, tag, axis, wall, clear, pr, ends, lf, **kw)
    # D13, Bedroom 2's closet: liners, split head trim with the black track between, the two panels, pulls, guide
    zc = (n0 + n1) / 2
    slot = RS.BED2_CLOSET_PANEL_TRACK + RS.BED2_CLOSET_PANEL_T / 2 + 0.012
    hd, lp = RS.DOOR_HEAD, RS.DOOR_LINER_PROUD
    ty0, ty1 = RS.BED2_CLOSET_TRACK_Y
    ctx.box('Bedroom 2 closet door jamb W', c0 - 2 * LN, c0, 0.0, hd - 0.08, n0 - lp, n1 + lp, 'paint_trim', C)
    ctx.box('Bedroom 2 closet door jamb E', c1, c1 + 2 * LN, 0.0, hd - 0.08, n0 - lp, n1 + lp, 'paint_trim', C)
    ctx.box('Bedroom 2 closet door head trim (bedroom half)', c0 - 2 * LN, c1 + 2 * LN, hd - 0.08, hd + 0.06, n0 - lp, zc - slot,
            'paint_trim', C)
    ctx.box('Bedroom 2 closet door head trim (closet half)', c0 - 2 * LN, c1 + 2 * LN, hd - 0.08, hd + 0.06, zc + slot, n1 + lp,
            'paint_trim', C)
    ctx.box('Bedroom 2 closet door track', c0, c1, ty0, ty1, zc - slot, zc + slot, 'black_metal', C)
    panels = RS.bed2_closet_panels()
    inset, py0, py1 = RS.BED2_CLOSET_PULL
    for p, edge in zip(panels, ('east', 'west')):            # the front panel is pulled by its east edge, the rear by its west
        ctx.box_c(p['name'], p['center'], p['size'], p['rot'], 'door_slab', C, bevel=0.006, segments=2)
        px0, px1, _, _, pz0, _ = p['aabb']
        xc = px1 - inset if edge == 'east' else px0 + inset
        tag = p['name'].replace('sliding panel', 'door flush pull')
        ctx.box(tag, xc - 0.045, xc + 0.045, py0, py1, pz0 - 0.0025, pz0 + 0.012, 'black_metal', C)
        ctx.box(tag + ' cup', xc - 0.022, xc + 0.022, py0 + 0.05, py1 - 0.05, pz0 - 0.004, pz0 + 0.012, 'paint_black', C)
    gx = (c0 + c1) / 2
    ctx.box('Bedroom 2 closet door floor guide plate', gx - 0.09, gx + 0.09, 0.0, 0.012, zc - 0.075, zc + 0.075, 'black_metal', C)
    ctx.box('Bedroom 2 closet door floor guide fin', gx - 0.07, gx + 0.07, 0.0, 0.07, zc - 0.009, zc + 0.009, 'black_metal', C)
    doors['Bedroom 2 closet (D13)'] = {'clear': _r((c0, c1)), 'wall opening': _r((c0 - LN, c1 + LN)), 'head': hd,
                                       'panels': [_r(p['aabb']) for p in panels],
                                       'open': _r((panels[0]['aabb'][1], c1))}
    out['doors'] = doors

    # ------------------------------------------------------------------ 5. the shared bath's wall tile at the door
    tiles = sorted([o for o in find(r'^A1 tile north \d+$') if o.type == 'MESH' and len(o.data.vertices) == 8],
                   key=lambda o: bbox(o)[0])
    if len(tiles) == 3:
        _set(tiles[0], 'x', None, d0 - 2 * LN)
        _set(tiles[1], 'x', d0 - 2 * LN, d1 + 2 * LN)
        _set(tiles[2], 'x', d1 + 2 * LN, None)
        out['bath tile at the door'] = [_r(bbox(o)[:2]) for o in tiles]
    elif tiles:
        out['bath tile at the door'] = f'FAILED: {len(tiles)} pieces, expected 3'
    else:
        out['bath tile at the door'] = 'zone baths not built: skipped'

    # ------------------------------------------------------------------ 6. baseboards
    out['baseboards'] = _baseboards(ctx, xe, xl, zh0, xf)
    return out


def _baseboards(ctx, xe, xl, zh0, xf):
    """Runs on every face of the new walls; the shell's runs carried to the new jambs and corners; the runs of walls
    that are gone removed. At an inside corner one run goes to the wall, the other ends on its face; at an outside
    corner the run on the hall's long face runs SKIRT_PROUD past the wall's end and covers the other one's end."""
    P, S = SKIRT_PROUD, SKIRT_SUNK
    n0, n1 = RS.BED2_SOUTH_WALL_Z
    wx0, wx1 = RS.BLOCK_WEST_WALL_X
    s1 = RS.BLOCK_SOUTH_WALL_Z[1]
    bw = RS.HALL_WEST[0]
    b0, b1 = RS.BED2_DOOR_X[0] - 2 * LN, RS.BED2_DOOR_X[1] + 2 * LN            # outer edges of the liners
    c0, c1 = RS.BED2_CLOSET_DOOR_X[0] - 2 * LN, RS.BED2_CLOSET_DOOR_X[1] + 2 * LN
    f0, f1 = RS.FAU_DOOR_Z[0] - 2 * LN, RS.FAU_DOOR_Z[1] + 2 * LN
    t0, t1 = RS.STO_DOOR_X[0] - 2 * LN, RS.STO_DOOR_X[1] + 2 * LN
    d0, d1 = RS.SHARED_BATH_DOOR_X[0] - 2 * LN, RS.SHARED_BATH_DOOR_X[1] + 2 * LN
    e0, e1 = RS.SUITE_ENTRY_Z[0] - RS.SUITE_ENTRY_LINER, RS.SUITE_ENTRY_Z[1] + RS.SUITE_ENTRY_LINER
    zcs = R.Z_B2CLO_S
    sk = {}

    src = _skirts('Upper closet — bottom wall KEPT', lambda b: b[5] < R.Z_B2CLO_S + 0.02)
    if len(src) != 1:
        raise RuntimeError(f"the closet's south baseboard: {len(src)} pieces, expected 1")
    src = src[0]
    sy0, sy1 = bbox(src)[2:4]

    def run(name, x0, x1, z0, z1, like=None):
        """A run on the box x0..x1, z0..z1: the shell piece `like` reshaped, or a copy of the closet's south run."""
        if like is not None:
            return _reshape(like, x0, x1, sy0, sy1, z0, z1)
        return _like(src, f'Painted skirting — {name}', x0, x1, sy0, sy1, z0, z1)

    def one(prefix, pick, what):
        obs = _skirts(prefix, pick)
        if len(obs) != 1:
            raise RuntimeError(f'baseboard {what}: {len(obs)} pieces, expected 1')
        return obs[0]

    # ---- Bedroom 2: its west run ends on the new south wall; runs on the south wall's bedroom face
    west = one('Original bedroom divider', lambda b: b[0] > bw - 0.02, "Bedroom 2's west run")
    _set(west, 'z', None, n0)
    east = one('Bedroom 2 / living divider', lambda b: b[1] < xe + 0.02, "Bedroom 2's east run")      # runs on through the closet
    xb2e = bbox(east)[0]
    run('Bedroom 2 south wall W', bbox(west)[1], b0, n0 - P, n0 + S)        # from the west run's face
    run('Bedroom 2 south wall mid', b1, c0, n0 - P, n0 + S)
    ep = _skirts('Bedroom 2 upper closet — north')
    if len(ep) != 2:
        raise RuntimeError(f"baseboards of the closet's east pier: {len(ep)} pieces, expected 2")
    ep.sort(key=lambda o: bbox(o)[4])
    run(None, c1, xb2e, n0 - P, n0 + S, like=ep[0])
    # ---- Bedroom 2's closet: its front wall's two piers, its west wall, its south wall
    run(None, c1, xb2e, n1 - S, n1 + P, like=ep[1])
    run('Bedroom 2 closet north wall W', wx1 + P, c0, n1 - S, n1 + P)
    cw = _skirts('Bedroom 2 upper closet — west')
    if len(cw) != 2:
        raise RuntimeError(f"baseboards of the closet's west wall: {len(cw)} pieces, expected 2")
    cw.sort(key=lambda o: bbox(o)[0])
    run(None, wx1 - S, wx1 + P, n1, zcs, like=cw[1])
    _set(src, 'x', wx1 + P, xb2e)
    # ---- the hall's west leg: north wall, the block's west face, the west wall north of the suite entry
    ext = one('Bedroom divider extension', lambda b: b[0] > bw - 0.02, "the old alcove's west run")
    run(None, bbox(ext)[0], bbox(ext)[1], n1, e0, like=ext)
    run('Hall north wall W', bbox(ext)[1], b0, n1 - S, n1 + P)              # from the west run's face
    run('Hall north wall E', b1, wx0, n1 - S, n1 + P)                       # to the block's west face (its run starts on this one)
    run(None, wx0 - P, wx0 + S, n1 + P, f0, like=cw[0])
    run('Closet block west wall S', wx0 - P, wx0 + S, f1, s1 - S)
    gone = remove(_skirts('Aligned primary-suite east wall — no', lambda b: b[0] > bw - 0.02 and b[4] > e0 - 0.02))
    # (the run south of the suite entry was carried to the entry's south liner by primary_suite_rooms; it ends on
    # the face of the run along the shared bath's wall instead of running into it)
    hs = one('Shared bathroom north / walk-in so', lambda b: b[5] < zh0 + 0.02, "the hall's south run, west of the bath door")
    for ob in _skirts('Aligned primary-suite east wall — so', lambda b: b[0] > bw - 0.02):
        if bbox(ob)[5] > bbox(hs)[4]:
            _set(ob, 'z', None, bbox(hs)[4])
    # ---- the hall's south wall (the shared bath's north wall) and the corner P3
    _set(hs, 'x', None, d0)
    he = one('Original shared bath — north', lambda b: b[5] < zh0 + 0.02, "the hall's south run, east of the bath door")
    _set(he, 'x', d1, xf + P)
    for ob in _skirts('Original shared bath — north', lambda b: b[4] > zh0 + 0.2):      # the bath's side (behind the tile)
        _set(ob, 'x', d1, None)
    pe = one('Original shared bath — east', lambda b: b[0] > xf - 0.02, "the foyer passage's run on the bath's east wall")
    _set(pe, 'z', bbox(he)[5], None)
    # ---- the hall's east leg: the block's south face, and the living-room wall's run to the corner
    run('Closet block south wall W', wx0 - P, t0, s1 - S, s1 + P)
    run('Closet block south wall E', t1, xl + P, s1 - S, s1 + P)
    liv = one('Bedroom 2 / living divider', lambda b: b[0] > xl - 0.02, "the living room's west run")
    old_z1 = bbox(liv)[5]
    _set(liv, 'z', None, s1 - S)
    grown = 0
    for ob in find(r'^\d+ Living west — (painted baseboard|baseboard top reveal)$', COLL_SHELL):   # the living room's own
        b = bbox(ob)                                                                           # baseboard on that wall
        if b[5] < old_z1 + 0.02:
            # v7 integrate: to the outer face of the block's south run, so the corner is closed by the room's own
            # baseboard too (it ended 0.23 ft short of the corner and the generic run behind it showed a joint)
            n = move_face(ob, 'z', b[5], s1 + P + 0.003, tol=1e-4)     # as proud of the south run as of the generic one
            grown += 1 if n else 0
    # ---- runs of walls that are gone or now stand inside the two small closets
    gone += remove(_skirts('Bedroom 2 entry return'))
    gone += remove(_skirts('Upper closet — bottom wall KEPT', lambda b: b[4] > R.Z_B2CLO_S + 0.2))
    sk['new runs'] = 8
    sk['removed'] = gone
    sk["living room's own baseboard pieces carried to the corner"] = grown
    sk['hall south run, east of the bath door'] = _r(bbox(he)[:2])
    sk['living-room wall run z1'] = round(bbox(liv)[5], 3)
    return sk


# ============================================================================================ fit-out
def _closet(ctx):
    """Bedroom 2's closet: white melamine shelf and tower, chrome rod, garments (the seventh round's pieces, on the
    sheet's 6'-10" x 1'-11")."""
    from . import bedrooms as B
    from . import bedrooms_furniture as F
    from . import bedrooms_kit as K
    from .bedrooms_kit import Frame
    from .. import lighting                                 # v7 repair (the closet's lamp)
    kit = K.Kit(ctx)
    M = F.mats()
    kit.use('bed2_closet')
    x0, x1, z0, z1 = RS.BED2_CLOSET_CLEAR
    mel = M['melamine']
    back = z1 - 0.006                                       # just off the back (south) wall
    zr = (z0 + z1) / 2                                      # the rod on the closet's centre line: 11 1/2 in off each wall
    kit.wbox('B2 closet shelf', x0 + 0.008, x1 - 0.008, 5.86, 5.94, z1 - 1.30, back, mel, 0.008, 1)
    tx0, tx1 = x1 - 1.56, x1 - 0.008                        # shelf tower at the east end, seen through the open half
    tz0 = z1 - 1.28
    for x in (tx0, tx1 - 0.06):
        kit.wbox('B2 closet tower side', x, x + 0.06, 0.0, 5.86, tz0, back, mel, 0.006, 1)
    for i, y in enumerate((0.0, 1.1, 2.2, 3.3, 4.4)):
        kit.wbox(f'B2 closet tower shelf {i}', tx0 + 0.06, tx1 - 0.06, y, y + 0.06 if i else 0.2, tz0, back, mel, 0.005, 1)
    F.closet_rod(kit, 'B2 closet', x0, tx0, zr, 5.55, 'x')
    tcx, tcz = (tx0 + tx1) / 2, (tz0 + back) / 2 - 0.02
    F.folded_stack(kit, M, Frame(tcx, tcz, 0, 1.16), 'B2 closet stack a', 4, 1.1, 0.95, 0.17, 2)
    F.folded_stack(kit, M, Frame(tcx, tcz, 0, 2.26), 'B2 closet stack b', 3, 1.1, 0.95, 0.2, 5)
    F.folded_stack(kit, M, Frame(tcx, tcz, 0, 3.36), 'B2 closet stack c', 2, 1.1, 0.95, 0.24, 8)
    F.storage_box(kit, M, Frame(tcx, tcz + 0.03, 0, 0.2), 'B2 closet basket', 1.25, 0.75, 1.15)
    F.folded_stack(kit, M, Frame(x0 + 1.9, z1 - 0.68, 0, 5.94), 'B2 closet top stack', 3, 1.2, 1.0, 0.2, 4)
    F.storage_box(kit, M, Frame(x0 + 4.1, z1 - 0.66, 0, 5.94), 'B2 closet top box', 1.3, 0.72, 1.05)
    S, J = F.SHIRTS, F.JACKETS
    F.hanger_row(kit, M, x0 + 0.03, tx0 - 0.03, zr, 5.55, 'B2 closet', 'x', seed=3, start='a1', subsurf=0, items=[
        ('shirt', S[0]), ('shirt', S[1]), ('shirt', S[2]), ('shirt', S[3]), ('shirt', S[4]), ('jacket', J[2]),
        ('shirt', S[5]), ('jacket', J[0]), ('shirt', S[7]), ('jacket', J[1]), ('shirt', S[8])])
    # v7 repair: the closet's can stands in the middle of its depth (it stood 0.3 ft from the header wall, trim 0.13 ft
    # off it, and lit that wall at grazing incidence: the compartment over the shelf read orange-brown from the room)
    # ... and it is a neutral white lamp (4000 K, the others are warm): beside the daylit room the warm lamp alone
    # turned the closet's white walls orange.
    lo = kit.can(x1 - 2.3, zr, watts=B.LIGHTS['B2']['closet'], lens=B.LIGHTS['B2']['lens'])
    lo.data.color = lighting.kelvin_rgb(4000)
    lens = bpy.data.objects.get(f'can lens {x1 - 2.3:.1f},{zr:.1f}')
    if lens is not None:
        lens.data.materials.clear()
        lens.data.materials.append(lighting.emitter('bed2_closet_lens', 4000, B.LIGHTS['B2']['lens']))
    return {'objects': kit.n, 'rod z': round(zr, 3), 'tower x': _r((tx0, tx1))}


def _hall(ctx):
    """The hall's art, ledge, switch and lights on the sheet's plan (the hall zone's pieces of the seventh round)."""
    from .. import lighting
    from . import hall_entry_garage as H
    from . import hall_entry_garage_art as ART
    from . import hall_entry_garage_lib as L
    M = H.mats(ctx)
    for c in (H.C_HALL, H.C_LIGHT, H.C_DECOR):
        ctx.coll(c, H.Z)
    hx0, hx1, hz0, hz1 = RS.HALL_WEST
    ex0, ex1, ez0, ez1 = RS.HALL_EAST
    out = {}
    # the block's south face, between its west corner and the storage closet's door: ledge, canvas, switch
    zl = ez0
    NJ = L.NORTH_FACING_SOUTH(zl)                              # u = +x, n = +z (into the hall)
    wall0, wall1 = ex0, RS.STO_DOOR_X[0] - 2 * LN                # 14.975 .. 19.248
    uc = (wall0 + 0.70 + wall1) / 2                              # centred on the wall east of the switch
    lu0, lu1, lv0, lv1, dep = uc - 1.45, uc + 1.45, 2.55, 2.83, 0.50
    H.canvas(ctx, M, NJ, 'junction horizon', uc, 4.95, 2.7, 1.8, ART.art_material('horizon', 'horizon'), H.C_HALL)
    NJ.box(ctx, 'ledge walnut', lu0, lu1, lv0, lv1, 0.004, dep, 'walnut_slab', H.C_HALL, 0.012, 3)
    zo = zl + 0.24                                               # the things on the ledge stand on its centre line
    bottle = L.lathe(ctx, 'vase bottle black', [(0.1, 0), (0.17, 0.05), (0.2, 0.3), (0.19, 0.62), (0.12, 0.8),
                                                (0.05, 0.92), (0.045, 1.12), (0.055, 1.16), (0.0, 1.16)],
                     H.C_DECOR, [M['ceramic_blk']])
    vx = uc + 0.85
    bottle.location = ft2bl(vx, lv1, zo)
    H.bunny_tails(ctx, M, (vx, lv1 + 1.1, zo), H.C_DECOR, seed=9, n=10, wall_z=zl + 0.09, scale=0.8)   # short stems: the
    #                                                         spray stays within 10 in of the wall
    bx = uc - 0.85
    ytop = H.books(ctx, M, bx, lv1, zo, 0.02, H.C_DECOR,
                   [(0.72, 0.42, 0.1, M['book_c']), (0.64, 0.38, 0.08, M['book_a'])])
    bowl = L.lathe(ctx, 'bowl cream', [(0.06, 0), (0.15, 0.015), (0.2, 0.06), (0.215, 0.1), (0.2, 0.105),
                                       (0.17, 0.065), (0.1, 0.03), (0.0, 0.028)], H.C_DECOR, [M['ceramic_cream']])
    bowl.location = ft2bl(bx, ytop, zo)
    H.switch_plate(ctx, M, NJ, 'junction', wall0 + 0.42, 4.0, 2, H.C_HALL)
    out['ledge'] = _r((lu0, lu1, lv0, lv1, zl, zl + dep))
    out['canvas'] = _r((uc - 1.35, uc + 1.35, 4.05, 5.85))
    # lights: the flush ring where the two legs meet, a can in each leg (the east leg's in line with the passage's)
    rx, rz = (hx0 + hx1) / 2, (ez0 + ez1) / 2
    H.flush_ring(ctx, M, rx, rz, name='junction flush ring')
    cans = [(rx, (hz0 + RS.SUITE_ENTRY_CLEAR_Z[1]) / 2), (R.X_HALL(19.4), rz)]
    for x, z in cans:
        lighting.can(ctx, x, z, coll=H.C_LIGHT, kelvin=H.HALL_K)
    out['flush ring'] = _r((rx, rz))
    out['cans'] = [_r(c) for c in cans]
    return out


def _leftovers(ctx):
    """Pieces the room zones built for the concept's alcove, closet and hall, if a zone still builds them."""
    n = 0
    for pat in (r'^B2 closet ', r'^can (lens|trim) (14\.8,13\.9|14\.8,14\.0|20\.3,14\.[12]|19\.4,18\.[12])$',
                r'^can (14\.8,13\.9|14\.8,14\.0|20\.3,14\.[12]|19\.4,18\.[12])$',
                r'^art junction horizon', r'^ledge walnut$', r'^switch (plate|rocker) junction', r'^junction flush ring'):
        n += remove(find(pat))
    x0, x1, z0, z1 = R.X_BED2_W, R.X_LIV_W, R.Z_WIC_N, R.Z_WIC_S           # loose decor of the old junction ledge
    for ob in find(r'^(vase bottle black|grass stem|grass plume core|book \d|bowl cream)'):
        if any(c.name.startswith('heg_') for c in ob.users_collection):
            bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]         # meshes and the stems' curves alike
            px, pz = sum(p.x for p in bb) / 8 / FT, -sum(p.y for p in bb) / 8 / FT
            if x0 < px < x1 and z0 < pz < z1:
                n += remove([ob])
    return n


def fit_out(ctx):
    out = {'old zone pieces removed': _leftovers(ctx)}
    out['closet'] = _closet(ctx) if 'bedrooms' in ctx.stats else 'zone bedrooms not built: skipped'
    out['hall'] = _hall(ctx) if 'hall_entry_garage' in ctx.stats else 'zone hall_entry_garage not built: skipped'
    bpy.context.view_layer.update()
    out['notes'] = _checks(ctx)
    return out


def _box(ob):
    """(x0, x1, y0, y1, z0, z1) of any object's bounding box, SCENE feet (meshes and the stems' curves alike)."""
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs, ys, zs = [p.x / FT for p in pts], [p.z / FT for p in pts], [-p.y / FT for p in pts]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


DOOR_PARTS = re.compile(r'leaf|panel|pull|lever|hinge|jamb|trim|track|guide|bracket|saddle', re.I)


def _checks(ctx):
    """How much room the hall keeps. Everything that is not shell (room zones, openings) and reaches into the hall
    below 6.5 ft is taken by its bounding box:
    * 'deepest thing on a wall': the furthest any piece that is not part of a door stands off the wall it is on;
    * 'narrowest clear': the smallest width left between those boxes, wall to wall, in the west leg and in the
      stretch of the east leg that has a wall on both sides (west of the shared bath wall's outside corner);
    * 'clear past the bath corner': east of that corner the hall is open to the foyer passage on its south side,
      and what counts is the smallest distance from the corner to anything on the block's south face (the way
      from the passage into the west leg)."""
    cx, cz = RS.SHARED_BATH_NE_CORNER
    wx0, wx1, wz0, wz1 = RS.HALL_WEST
    ex0, ex1, ez0, ez1 = RS.HALL_EAST
    things = []
    for ob in bpy.data.objects:
        if ob.type not in ('MESH', 'CURVE') or not ob.users_collection:
            continue
        if any(c.name in (COLL_SHELL, 'exterior_shell') or c.name.startswith(('zone_exterior', 'ext')) for c in ob.users_collection):
            continue
        b = _box(ob)
        if b[2] > 6.5 or b[3] < 0.06 or b[1] <= wx0 or b[0] >= ex1 or b[5] <= wz0 or b[4] >= wz1 \
                or b[1] - b[0] > 12.0 or b[5] - b[4] > 12.0:
            continue
        things.append((ob.name, b))

    def leg(rect, along_z):
        x0, x1, z0, z1 = rect
        w0, w1, e0, e1 = (x0, x1, z0, z1) if along_z else (z0, z1, x0, x1)      # across the leg, along it
        lo, hi, deepest = {}, {}, (0.0, None)
        for name, b in things:
            if b[1] <= x0 + 1e-3 or b[0] >= x1 - 1e-3 or b[5] <= z0 + 1e-3 or b[4] >= z1 - 1e-3:
                continue
            a0, a1, c0, c1 = (b[4], b[5], b[0], b[1]) if along_z else (b[0], b[1], b[4], b[5])
            if (c0 <= w0 + 0.02 and c1 >= w1 - 0.02) or a1 <= e0 + 0.06 or a0 >= e1 - 0.06:
                continue                              # spans the leg (a saddle), or belongs to the leg's end wall
            near_lo = (c0 + c1) / 2 < (w0 + w1) / 2
            d = (min(c1, w1) - w0) if near_lo else (w1 - max(c0, w0))
            if not DOOR_PARTS.search(name) and d > deepest[0]:
                deepest = (round(d, 3), name)
            side = lo if near_lo else hi
            for k in range(int(math.floor(max(a0, e0) * 20)), int(math.ceil(min(a1, e1) * 20))):
                side[k] = max(side.get(k, 0.0), d)
        clear = min([(w1 - w0) - lo.get(k, 0.0) - hi.get(k, 0.0) for k in set(lo) | set(hi)] or [w1 - w0])
        return {'width': round(w1 - w0, 3), 'deepest thing on a wall': deepest, 'narrowest clear': round(clear, 3)}
    notes = {'west leg': leg(RS.HALL_WEST, True), 'east leg beside the bath wall': leg((ex0, cx, ez0, ez1), False)}
    deepest, near = (0.0, None), (99.0, None)
    for name, b in things:
        if b[1] <= cx or b[0] >= ex1 or b[4] < ez0 - 0.2 or b[4] > ez0 + 1.5:     # on the block's south face, east of the corner
            continue
        d = b[5] - ez0
        if not DOOR_PARTS.search(name) and d > deepest[0]:
            deepest = (round(d, 3), name)
        gap = math.hypot(max(b[0] - cx, 0.0, cx - b[1]), max(b[4] - cz, 0.0, cz - b[5]))
        if gap < near[0]:
            near = (round(gap, 3), name)
    notes['east leg open to the passage'] = {'deepest thing on the north wall': deepest, 'clear past the bath corner': near}
    return notes
