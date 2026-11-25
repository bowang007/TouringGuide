"""Bedroom 3 and Bedroom 4, eighth round (2026-11-24), stage B, track "bedrooms": walls, doors and west windows as
the architect's sheet SKA002 draws them (bl/revision_spec.py, section "v7 bedrooms"). Runs inside Blender AFTER the
warp, from bl/revisions.bedrooms_west_windows / bedroom3_rooms / bedroom3_fit_out, so every number here is SCENE
feet on the architect's plan (= the sheet's own coordinates).

* west_windows: Bedroom 4's west window W12 becomes 5'-0" wide, centred on the room's west wall (the shell's wall
  pieces, frame, mullions, pane and baseboards are carried to the new jambs; bl/revisions.white_windows makes it
  white and gives it its grid afterwards). Bedroom 3's west window W10 is closed while
  revision_spec.BED3_WEST_WINDOW is False: the wall below the window is carried up to the ceiling (it keeps the
  paint inside and the stucco outside), the header, frame, mullions and pane go, the baseboard joints at the old
  jambs are closed.
* rooms: the wall between Bedroom 3 and its bath / closet (sheet WL26). The two pocket doors and their cavity
  faces go; the wall is five plain pieces (three walls, two headers) around
    - door D05, bath: hinged 2'-4" at the east end of the bath's south wall, hinged on the east jamb, open at 90
      degrees along the bath's east wall; painted liners and head trim, a quartz saddle ramped to the oak floor;
    - door D06, closet: a 4'-8" clear opening with two 2'-6" bypass panels on a black top track between the two
      halves of the head trim, both parked at the east end, flush pulls, a floor guide;
  and Bedroom 3's entry D03 moves to the sheet's place (2'-8" clear, 4 in from the room's north wall) and is hinged
  on the north jamb; Bedroom 4's entry D04 gets a leaf sized to its opening. Every hinged leaf has three black butt
  hinges, a lever on each face and a latch plate on its free edge. Baseboards follow the new jambs.
* fit_out: Bedroom 3's closet as a reach-in fitted to its 2'-3 1/2" depth (drawer and shelf tower, double hang,
  open shelf tower; the seventh round's wardrobe was a 2.60 ft deep unit standing in the wall), the bath's fit-out
  (bl/zones/baths_suite3.py), the picture over Bedroom 3's bed on the closed west wall and Bedroom 4's roller
  shade for the wider window. Skipped for a zone that was not built (`--zones`).
"""
import math
import re

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .. import revision_spec as RS
from ..common import FT, ft2bl
from ..revisions import COLL_OPEN, COLL_SHELL, _like, _paint_all, _reshape, _set_world, _world, bbox, find, move_face, remove

R = RS.R
SKIRT_PROUD = 0.057                           # the house's baseboard on the 5 in walls: off the wall face
SKIRT_SUNK = 0.002                            # ... and into it


def _r(v):
    return [round(float(a), 3) for a in v]


def _boxes(pat, coll=COLL_SHELL, pick=lambda b: True):
    return [o for o in find(pat, coll) if o.type == 'MESH' and len(o.data.vertices) == 8 and pick(bbox(o))]


def _one(pat, coll=COLL_SHELL, pick=lambda b: True):
    obs = _boxes(pat, coll, pick)
    if len(obs) != 1:
        raise RuntimeError(f'{pat!r}: {len(obs)} pieces in {coll}, expected 1')
    return obs[0]


def _end(ob, axis, old, new, what):
    n = move_face(ob, axis, old, new)
    if n != 4:
        raise RuntimeError(f'{what}: {n} vertices at {axis} {old:.3f}, expected 4')


def _shift_z(ob, dz):
    ob.location.y -= dz * FT


def _recentre(ob):
    """Put a pane's origin in its middle (lighting.add_window_portals stands the light portal on it)."""
    w, _ = _world(ob)
    ob.location = Vector([float(v) for v in (w.min(axis=0) + w.max(axis=0)) / 2])
    bpy.context.view_layer.update()
    _set_world(ob, w, np.array(ob.matrix_world))


# =============================================================================================== west windows
def _window_b4(ctx):
    n0, n1 = RS.BED4_WEST_WIN_Z
    o0, o1 = RS.BED4_WEST_WIN_OLD_Z
    pat = r'^\d+ Bedroom 4 west addition$'
    done = {'piers': 0, 'sill / head wall': 0, 'rails': 0, 'mullions': 0, 'pane': 0, 'baseboards': 0}
    shell = _boxes(pat)
    for ob in shell:
        b = bbox(ob)
        if abs(b[5] - o0) < 0.02 and b[4] < o0 - 0.3:
            _end(ob, 'z', b[5], n0, 'Bedroom 4 west wall, pier north of the window')
            done['piers'] += 1
        elif abs(b[4] - o1) < 0.02 and b[5] > o1 + 0.3:
            _end(ob, 'z', b[4], n1, 'Bedroom 4 west wall, pier south of the window')
            done['piers'] += 1
        elif abs(b[4] - o0) < 0.02 and abs(b[5] - o1) < 0.02:
            _reshape(ob, b[0], b[1], b[2], b[3], n0, n1)
            done['sill / head wall'] += 1
    if done['piers'] != 2 or done['sill / head wall'] != 2:
        raise RuntimeError(f'Bedroom 4 west wall is not where the spec expects it: {done}, '
                           f'{[_r(bbox(o)) for o in shell]}')
    for ob in _boxes(pat, COLL_OPEN):
        b = bbox(ob)
        mid = (b[4] + b[5]) / 2
        if b[5] - b[4] > 1.0:                           # sill rail, head rail, pane: between the jambs as before
            _reshape(ob, b[0], b[1], b[2], b[3], n0 + (b[4] - o0), n1 - (o1 - b[5]))
            if ob.data.materials and ob.data.materials[0] is not None and 'glass' in ob.data.materials[0].name:
                _recentre(ob)
                done['pane'] += 1
            else:
                done['rails'] += 1
        else:                                           # the two jamb sections and the centre mullion
            _shift_z(ob, (n0 - o0) if abs(mid - o0) < 0.15 else (n1 - o1) if abs(mid - o1) < 0.15 else (n0 + n1) / 2 - mid)
            done['mullions'] += 1
    if (done['rails'], done['mullions'], done['pane']) != (2, 3, 1):
        raise RuntimeError(f'Bedroom 4 west window pieces: {done}')
    # v7 repair: the pane stopped 3/8 in short of each jamb section (the shell's unit: pane z 30.454..35.329 between
    # jamb sections that end at 30.423 and start at 35.360), two unglazed slits from sill to head through which the
    # side yard showed beside the shade. The pane runs 0.008 ft into both jamb sections now, as the rebuilt
    # windows' panes run into their sashes (bl/revisions._glz_window).
    bpy.context.view_layer.update()
    jambs = sorted((bbox(o) for o in _boxes(pat, COLL_OPEN) if bbox(o)[5] - bbox(o)[4] <= 1.0), key=lambda b: b[4])
    for ob in _boxes(pat, COLL_OPEN):
        b = bbox(ob)
        if b[5] - b[4] > 1.0 and ob.data.materials and ob.data.materials[0] is not None \
                and 'glass' in ob.data.materials[0].name:
            _reshape(ob, b[0], b[1], b[2], b[3], jambs[0][5] - 0.008, jambs[-1][4] + 0.008)
            _recentre(ob)
            done['pane z'] = _r(bbox(ob)[4:6])
    # baseboards: the three runs are cut at the jambs (0.02 ft off them, as the shell cuts them)
    for ob in _boxes(r'^\d+ Painted skirting — Bedroom 4 west addition$'):
        b = bbox(ob)
        if b[5] < o0 + 0.1:
            _reshape(ob, b[0], b[1], b[2], b[3], b[4], n0 - 0.02)
        elif b[4] > o1 - 0.1:
            _reshape(ob, b[0], b[1], b[2], b[3], n1 + 0.02, b[5])
        else:
            _reshape(ob, b[0], b[1], b[2], b[3], n0 + 0.02, n1 - 0.02)
        done['baseboards'] += 1
    bpy.context.view_layer.update()
    return {'opening z': _r((n0, n1)), 'was': _r((o0, o1)), 'sill, head': RS.BED4_WEST_WIN_Y, 'pieces': done}


def _window_b3(ctx):
    z0, z1 = RS.BED3_WEST_WIN_Z
    if RS.BED3_WEST_WINDOW:
        return {'kept': _r((z0, z1))}
    low = _one(r'^\d+ Bedroom 3 side window sill wall$')
    high = _one(r'^\d+ Bedroom 3 side window head wall$')
    lb, hb = bbox(low), bbox(high)
    if max(abs(lb[4] - z0), abs(lb[5] - z1), abs(hb[4] - z0), abs(hb[5] - z1), abs(lb[2])) > 0.02:
        raise RuntimeError(f'Bedroom 3 west window wall is not where the spec expects it: {_r(lb)}, {_r(hb)}')
    _reshape(low, lb[0], lb[1], 0.0, hb[3], lb[4], lb[5])        # one piece, floor to ceiling: paint inside, stucco outside
    gone = remove([high])
    gone += remove([o for o in find(r'^\d+ Bedroom 3 side window (frame|mullion|glazing)$', COLL_OPEN)])
    # the baseboard under the old window runs on to its neighbours (the shell leaves a 0.04 ft joint at each jamb)
    sk = _boxes(r'^\d+ Painted skirting — Bedroom 3 side window sill wall$')
    closed = 0
    for ob in sk:
        b = bbox(ob)
        same = [bbox(o) for o in _boxes(r'^\d+ Painted skirting — ') if o is not ob and abs(bbox(o)[0] - b[0]) < 0.02
                and abs(bbox(o)[1] - b[1]) < 0.02]
        a0 = max([s[5] for s in same if s[5] <= b[4] + 0.01 and b[4] - s[5] < 0.1], default=b[4])
        a1 = min([s[4] for s in same if s[4] >= b[5] - 0.01 and s[4] - b[5] < 0.1], default=b[5])
        _reshape(ob, b[0], b[1], b[2], b[3], a0, a1)
        closed += 1
    bpy.context.view_layer.update()
    return {'closed z': _r((z0, z1)), 'wall': _r(bbox(low)), 'removed': gone, 'baseboard joints closed': closed}


def west_windows(ctx):
    return {'W12 Bedroom 4': _window_b4(ctx), 'W10 Bedroom 3': _window_b3(ctx)}


# =============================================================================================== doors
def _door_hardware(ctx, leaf, tag, hinge_y=RS.DOOR_HINGE_Y, lever=RS.DOOR_LEVER):
    """Three black butt hinges on the pin axis, a lever on each face pointing to the hinge, a latch plate on the
    free edge (the house's other hinged doors: bl/revisions.bath_door)."""
    from .. import laundry
    kit = laundry.Kit(ctx, COLL_OPEN, None)
    (ox, oz), (ax, az), (tx, tz) = leaf['corner'], leaf['along'], leaf['through']
    px, pz = leaf['pivot']
    w, _, th = leaf['size']

    def pt(u, y, v):                                     # u along the leaf from its hinge edge, v through it from its room face
        return (ox + ax * u + tx * v, y, oz + az * u + tz * v)
    r, hh = 0.021, 0.146                                 # 1/2 in barrels, 3 1/2 in high
    for i, yh in enumerate(hinge_y):
        kit.cyl(f'{tag} hinge {i}', (px, yh - hh, pz), (px, yh + hh, pz), r, 'black_metal', 20)
        for k, ya in enumerate((yh - hh - 0.02, yh + hh)):
            kit.cyl(f'{tag} hinge {i} tip {k}', (px, ya, pz), (px, ya + 0.02, pz), r * 0.7, 'black_metal', 16)
        ctx.box_c(f'{tag} hinge {i} plate', pt(0.001, yh, 0.004 + 0.045), (0.005, 2 * hh, 0.09), leaf['rot'], 'black_metal',
                  COLL_OPEN)
    inset, yl = lever
    ul = w - inset
    for side, v0, sg in (('room', 0.0, -1.0), ('far', th, 1.0)):
        kit.cyl(f'{tag} lever {side} rose', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.02), 0.085, 'black_metal', 32)
        kit.cyl(f'{tag} lever {side} neck', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.17), 0.03, 'black_metal', 20)
        kit.cyl(f'{tag} lever {side} bar', pt(ul + 0.02, yl, v0 + sg * 0.15), pt(ul - 0.38, yl, v0 + sg * 0.15), 0.024,
                'black_metal', 20)
    ctx.box_c(f'{tag} latch plate', pt(w - 0.001, yl, th / 2), (0.006, 0.19, 0.075), leaf['rot'], 'black_metal', COLL_OPEN)
    return len(kit.objects) + 4


def _leaf(ctx, leaf, tag):
    ctx.box_c(leaf['name'], leaf['center'], leaf['size'], leaf['rot'], 'door_slab', COLL_OPEN, bevel=0.006, segments=2)
    _door_hardware(ctx, leaf, tag)
    return _r(leaf['aabb'])


def _prism_x(ctx, name, x0, x1, profile, mat, coll):
    """Solid of constant section along x: profile = [(z, y), ...] counter-clockwise seen from +x... any order works,
    the normals are recalculated."""
    bm = bmesh.new()
    ends = [[bm.verts.new(ft2bl(x, y, z)) for z, y in profile] for x in (x0, x1)]
    bm.faces.new(ends[0])
    bm.faces.new(list(reversed(ends[1])))
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ends[0][i], ends[1][i], ends[1][j], ends[0][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ctx.mat(mat))
    ob = bpy.data.objects.new(name, me)
    ctx.coll(coll).objects.link(ob)
    return ob


def _north_wall(ctx):
    """The wall between Bedroom 3 and its bath / closet: pieces, baseboards, the bath door, the closet doors."""
    out = {}
    zn, zs = RS.BED3_NORTH_WALL_Z
    box = ctx.box
    c = COLL_OPEN
    ln, head = RS.DOOR_LINER, RS.DOOR_HEAD
    # ---- wall pieces
    want = RS.bed3_north_walls()
    pieces = {name: _one(rf'^\d+ {re.escape(name)}$') for name in want}
    old = {n: bbox(o) for n, o in pieces.items()}
    w_end, hdr_b, mid, hdr_c, e_end = (old[n] for n in want)
    off = max(abs(b[4] - zn) for b in old.values()), max(abs(b[5] - zs) for b in old.values()), \
        abs(w_end[0] - RS.WEST_WALL_C), abs(e_end[1] - sum(R.FOYER_WALL) / 2), abs(hdr_b[1] - mid[0]), abs(mid[1] - hdr_c[0]), \
        abs(hdr_c[1] - e_end[0])
    if max(off) > 0.02:
        raise RuntimeError(f'the wall is not where the spec expects it: {[_r(b) for b in old.values()]}')
    for name, b in want.items():
        _reshape(pieces[name], *b)
        _paint_all(pieces[name])
    gone = remove(_boxes(r'^\d+ (Ensuite|Walk-in closet) pocket cavity face$'))
    gone += remove(find(r'^\d+ (Ensuite 32 inch pocket door open|Walk-in closet 32 inch pocket door open|Ensuite pocket jamb|'
                        r'Walk-in closet pocket jamb|Ensuite head casing|Walk-in closet head casing)$', COLL_OPEN))
    out['walls'] = {n: _r(bbox(o)[:2]) for n, o in pieces.items()}
    out['pocket doors removed (pieces)'] = gone

    # ---- baseboards: new runs on the bedroom face and in the closet (the bath's tile covers its face)
    b0, b1 = RS.BED3_BATH_DOOR_X
    c0, c1 = RS.BED3_CLOSET_DOOR_X
    olds = _boxes(r'^\d+ Painted skirting — (Suite service wall|Ensuite pocket cavity face|Walk-in closet pocket cavity face)')
    if not olds:
        raise RuntimeError('no baseboard on the wall to copy')
    src = olds[0]
    sy0, sy1 = bbox(src)[2:4]
    P, S = SKIRT_PROUD, SKIRT_SUNK
    xe = R.FOYER_WALL[0] - P                             # the face of the foyer-side wall's own run
    runs = [('Bedroom 3 north wall, west of the bath door', R.XW + P, b0 - 2 * ln, zs - S, zs + P),
            ('Bedroom 3 north wall, between the doors', b1 + 2 * ln, c0 - 2 * ln, zs - S, zs + P),
            ('Bedroom 3 north wall, east of the closet', c1 + 2 * ln, xe, zs - S, zs + P),
            ('Bedroom 3 closet front wall, west', R.X_CLO_W + P, c0 - 2 * ln, zn - P, zn + S),
            ('Bedroom 3 closet front wall, east', c1 + 2 * ln, xe, zn - P, zn + S)]
    for name, x0, x1, z0, z1 in runs:
        if x1 - x0 > 0.03:
            _like(src, f'Painted skirting — {name}', x0, x1, sy0, sy1, z0, z1)
    out['baseboards'] = {'old runs removed': remove(olds), 'new': [(n, round(a, 3), round(b, 3)) for n, a, b, _, _ in runs]}

    # ---- door D05, the bath: liners, head trim, saddle, leaf
    pb, pr = RS.BED3_BATH_DOOR_LINER_PROUD
    box('Bedroom 3 bath door jamb W', b0 - 2 * ln, b0, 0.0, head - 0.08, zn - pb, zs + pr, 'paint_trim', c)
    box('Bedroom 3 bath door jamb E', b1, b1 + 2 * ln, 0.0, head - 0.08, zn - pb, zs + pr, 'paint_trim', c)
    box('Bedroom 3 bath door head trim', b0 - 2 * ln, b1 + 2 * ln, head - 0.08, head + 0.06, zn - pb, zs + pr, 'paint_trim', c)
    sy = RS.BED3_BATH_DOOR_SADDLE_Y
    # flat over the wall's thickness from the bath's tile, ramped down to the oak on the bedroom side
    sad = _prism_x(ctx, 'Bedroom 3 bath door saddle', b0, b1,
                   [(zn - pb, -0.005), (zn - pb, sy), (zs - 0.10, sy), (zs + pr, 0.022), (zs + pr, -0.005)], 'quartz_white', c)
    ctx.add_bevel(sad, 0.006, 2)
    out['bath door'] = {'clear x': _r((b0, b1)), 'head': head, 'leaf': _leaf(ctx, RS.bed3_bath_door_leaf(), 'Bedroom 3 bath door'),
                        'saddle y': sy}

    # ---- door D06, the closet: liners, split head trim with the track between, two bypass panels
    ow = RS.DOOR_LINER_PROUD
    zc = RS.BED3_NORTH_WALL_C
    slot = RS.BED3_CLOSET_PANEL_TRACK + RS.BED3_CLOSET_PANEL_T / 2 + 0.012
    box('Bedroom 3 closet door jamb W', c0 - 2 * ln, c0, 0.0, head - 0.08, zn - ow, zs + ow, 'paint_trim', c)
    box('Bedroom 3 closet door jamb E', c1, c1 + 2 * ln, 0.0, head - 0.08, zn - ow, zs + ow, 'paint_trim', c)
    box('Bedroom 3 closet door head trim (closet half)', c0 - 2 * ln, c1 + 2 * ln, head - 0.08, head + 0.06, zn - ow, zc - slot,
        'paint_trim', c)
    box('Bedroom 3 closet door head trim (bedroom half)', c0 - 2 * ln, c1 + 2 * ln, head - 0.08, head + 0.06, zc + slot, zs + ow,
        'paint_trim', c)
    ty0, ty1 = RS.BED3_CLOSET_TRACK_Y
    box('Bedroom 3 closet door top track', c0, c1, ty0, ty1, zc - slot, zc + slot, 'black_metal', c)
    panels = RS.bed3_closet_panels()
    inset, py0, py1 = RS.BED3_CLOSET_PULL
    for p in panels:
        x0, x1, y0, y1, z0, z1 = p['aabb']
        ctx.box_c(p['name'], p['center'], p['size'], p['rot'], 'door_slab', c, bevel=0.006, segments=2)
        px = x0 + inset                                   # flush pull: a black plate let into the bedroom face, a dark cup in it
        box(p['name'] + ' flush pull', px - 0.04, px + 0.04, py0, py1, z1 - 0.012, z1 + 0.0025, 'black_metal', c)
        box(p['name'] + ' flush pull cup', px - 0.02, px + 0.02, py0 + 0.05, py1 - 0.05, z1 - 0.012, z1 + 0.004, 'paint_black', c)
    gx = panels[0]['aabb'][0] + 0.25                      # where the two panels overlap
    box('Bedroom 3 closet door floor guide plate', gx - 0.07, gx + 0.07, 0.0, 0.01, zc - slot + 0.01, zc + slot - 0.01, 'black_metal', c)
    box('Bedroom 3 closet door floor guide', gx - 0.035, gx + 0.035, 0.0, 0.07, zc - 0.011, zc + 0.011, 'black_metal', c)
    out['closet door'] = {'clear x': _r((c0, c1)), 'head': head, 'panels': {p['name'][-5:].strip(): _r(p['aabb']) for p in panels},
                          'open x': _r((c0, min(p['aabb'][0] for p in panels)))}
    return out


def _entry(ctx, tag, wall_n, wall_s, header, trims, old_leaf, clear, old_wall_z, leaf):
    """A hinged door in the foyer-side wall: the three shell pieces go to the opening (when it moves), the shell's
    two casings and head trim become liners of the house's section on the new jambs, the leaf is new."""
    out = {}
    d0, d1 = clear
    ln, head, ow = RS.DOOR_LINER, RS.DOOR_HEAD, RS.DOOR_LINER_PROUD
    w0, w1 = d0 - ln, d1 + ln                             # the wall opening
    wn, ws, hd = _one(wall_n), _one(wall_s), _one(header)
    nb, sb, hb = bbox(wn), bbox(ws), bbox(hd)
    if max(abs(nb[5] - old_wall_z[0]), abs(sb[4] - old_wall_z[1]), abs(hb[4] - old_wall_z[0]), abs(hb[5] - old_wall_z[1]),
           abs(hb[2] - head)) > 0.02:
        raise RuntimeError(f'{tag}: the door wall is not where the spec expects it: {_r(nb)}, {_r(hb)}, {_r(sb)}')
    moved = max(abs(nb[5] - w0), abs(sb[4] - w1)) > 1e-4
    if moved:
        _end(wn, 'z', nb[5], w0, f'{tag}: wall north of the door')
        _end(ws, 'z', sb[4], w1, f'{tag}: wall south of the door')
        _reshape(hd, hb[0], hb[1], hb[2], hb[3], w0, w1)
        for ob in (wn, ws, hd):
            _paint_all(ob)
    x0, x1 = RS.BED3_ENTRY_WALL_X[0] - ow, RS.BED3_ENTRY_WALL_X[1] + ow
    cas = sorted(_boxes(trims + r' casing$', COLL_OPEN), key=lambda o: bbox(o)[4])
    ht = _one(trims + r' head trim$', COLL_OPEN)
    if len(cas) != 2:
        raise RuntimeError(f'{tag}: {len(cas)} casings, expected 2')
    _reshape(cas[0], x0, x1, 0.0, head - 0.08, d0 - 2 * ln, d0)
    _reshape(cas[1], x0, x1, 0.0, head - 0.08, d1, d1 + 2 * ln)
    _reshape(ht, x0, x1, head - 0.08, head + 0.06, d0 - 2 * ln, d1 + 2 * ln)
    out['old leaf removed'] = remove(find(old_leaf, COLL_OPEN))
    # baseboards of the two wall pieces end at the liners
    cut = 0
    for ob in _boxes(r'^\d+ Painted skirting — '):
        b = bbox(ob)
        if b[5] - b[4] < b[1] - b[0] or not (nb[0] - 0.08 < (b[0] + b[1]) / 2 < nb[1] + 0.08):
            continue                                      # runs along z on one of this wall's two faces
        if abs(b[5] - old_wall_z[0]) < 0.06 and abs(b[5] - (d0 - 2 * ln)) > 1e-4:
            _reshape(ob, b[0], b[1], b[2], b[3], b[4], d0 - 2 * ln)
            cut += 1
        elif abs(b[4] - old_wall_z[1]) < 0.06 and abs(b[4] - (d1 + 2 * ln)) > 1e-4:
            _reshape(ob, b[0], b[1], b[2], b[3], d1 + 2 * ln, b[5])
            cut += 1
    out.update({'clear z': _r((d0, d1)), 'wall opening was': _r(old_wall_z), 'walls moved': moved, 'baseboards recut': cut,
                'leaf': _leaf(ctx, leaf, tag)})
    return out


def rooms(ctx):
    out = {'bath / closet wall': _north_wall(ctx)}
    gone = remove(find(r'^\d+ Bedroom door lever( rosette)?$', COLL_OPEN))      # the two old leaves' levers
    out['Bedroom 3 entry D03'] = _entry(
        ctx, 'Bedroom 3 entry door', r'^\d+ Suite 3 services / hall wall$', r'^\d+ Bedroom 3 entry south jamb$',
        r'^\d+ Bedroom 3 entry header$', r'^\d+ Bedroom 3 entry', r'^\d+ Bedroom 3 entry door open inward$',
        RS.BED3_ENTRY_Z, RS.BED3_ENTRY_OLD_Z, RS.bed3_entry_leaf())
    out['Bedroom 4 entry D04'] = _entry(
        ctx, 'Bedroom 4 entry door', r'^\d+ Bedroom 4 revised 32 inch entry north jamb$',
        r'^\d+ Bedroom 4 revised 32 inch entry south jamb$', r'^\d+ Bedroom 4 revised 32 inch entry header$',
        r'^\d+ Bedroom 4 revised 32 inch entry', r'^\d+ Bedroom 4 revised 32 inch entry door open inward$',
        RS.BED4_ENTRY_Z, RS.BED4_ENTRY_WALL_Z, RS.bed4_entry_leaf())
    out['old levers removed'] = gone
    bpy.context.view_layer.update()
    return out


# =============================================================================================== fit-out
def _closet(ctx):
    """Bedroom 3's closet as a reach-in behind the two sliding panels: x 8.892..15.142, 2'-3 1/2" deep (z 40.017..
    42.308). West to east: a drawer and shelf tower (in the open half of the doorway), a double-hang bay under a
    shelf, an open shelf tower behind the wall east of the doorway. Nothing is deeper than 1.6 ft."""
    from . import bedrooms as B
    from . import bedrooms_furniture as F
    from . import bedrooms_kit as K
    Frame = K.Frame
    kit = K.Kit(ctx)
    kit.use('bed3_closet')
    M = F.mats()
    mel = M['melamine']
    cx0, cx1, zb, zf = R.ROOMS['bed3_closet']
    d = 1.60                                             # unit depth off the back wall
    # ---- west tower: three drawers, shelves above
    side = SKIRT_PROUD + 0.008                           # the towers stand clear of the side walls' baseboards
    tx0, tx1 = cx0 + side, cx0 + side + 1.50
    z0, z1 = zb + 0.02, zb + d
    kit.wbox('C3 plinth', tx0 + 0.05, tx1 - 0.05, 0.0, 0.15, z0, z1 - 0.08, 'paint_black', 0.0)
    kit.wbox('C3 back', tx0, tx1, 0.15, 7.42, zb + 0.002, z0, mel, 0.0)
    for x in (tx0, tx1 - 0.06):
        kit.wbox('C3 side', x, x + 0.06, 0.15, 7.42, z0, z1, mel, 0.006, 1)
    kit.wbox('C3 top', tx0, tx1, 7.42, 7.5, zb + 0.002, z1, mel, 0.006, 1)
    kit.wbox('C3 drawer deck', tx0 + 0.06, tx1 - 0.06, 0.15, 0.175, z0, z1 - 0.06, mel, 0.0)
    for i in range(3):
        y = 0.18 + i * 0.66
        kit.wbox(f'C3 drawer {i}', tx0 + 0.075, tx1 - 0.075, y, y + 0.62, z1 - 0.06, z1, mel, 0.008, 2)
        kit.wbox(f'C3 drawer pull {i}', tx0 + 0.42, tx1 - 0.42, y + 0.5, y + 0.53, z1, z1 + 0.03, 'black_metal', 0.005, 1)
    for i, y in enumerate((2.2, 3.35, 4.5, 5.65, 6.75)):
        kit.wbox(f'C3 shelf {i}', tx0 + 0.06, tx1 - 0.06, y, y + 0.06, z0, z1 - 0.02, mel, 0.005, 1)
    xc, zc = (tx0 + tx1) / 2, zb + 0.86
    F.folded_stack(kit, M, Frame(xc, zc, 0.0, 2.26), 'C3 stack a', 3, 1.0, 0.95, 0.2, 1)
    F.folded_stack(kit, M, Frame(xc, zc, 0.0, 3.41), 'C3 stack b', 4, 1.0, 0.95, 0.17, 4)
    B._basket(kit, M, Frame(xc, zc + 0.05, 0.0, 4.56), 'C3 basket', 1.0, 0.7, 1.05)
    F.folded_stack(kit, M, Frame(xc, zc, 0.0, 5.71), 'C3 stack c', 2, 1.0, 0.95, 0.22, 6)
    # ---- east tower: open shelves
    ex0, ex1 = cx1 - side - 1.48, cx1 - side
    ez1 = zb + 1.32
    kit.wbox('C3 east back', ex0, ex1, 0.0, 7.0, zb + 0.002, z0, mel, 0.0)
    for x in (ex0, ex1 - 0.06):
        kit.wbox('C3 east side', x, x + 0.06, 0.0, 7.0, z0, ez1, mel, 0.006, 1)
    for i, y in enumerate((0.0, 1.3, 2.6, 3.9, 5.2, 6.5)):
        kit.wbox(f'C3 east shelf {i}', ex0 + 0.06, ex1 - 0.06, y, y + (0.15 if i == 0 else 0.06), z0, ez1 - 0.02, mel, 0.005, 1)
    exc, ezc = (ex0 + ex1) / 2, zb + 0.70
    F.folded_stack(kit, M, Frame(exc, ezc, 0.0, 1.36), 'C3 east stack a', 3, 0.85, 0.75, 0.2, 3)
    F.folded_stack(kit, M, Frame(exc, ezc, 0.0, 2.66), 'C3 east stack b', 2, 0.85, 0.75, 0.24, 7)
    B._basket(kit, M, Frame(exc, ezc, 0.0, 3.96), 'C3 east box', 0.95, 0.65, 0.8)
    tan = K.principled('Z_bedrooms_leather_tan', '#9a6a3e', 0.45)
    canvas = K.principled('Z_bedrooms_canvas_white', '#ecebe6', 0.8)
    for i, (dx, m) in enumerate(((-0.34, tan), (0.30, canvas))):     # two pairs, toes to the room
        for s in (-0.12, 0.12):
            kit.soft(f'C3 shoe {i}{s > 0}', Frame(exc + dx + s, ezc + 0.05, 0.0), (0, 0.15 + 0.13, 0), (0.33, 0.26, 0.9), m, 0.09, 3, 1)
    # ---- the double-hang bay between them
    hx0, hx1 = tx1, ex0
    zr = zb + 1.0                                        # rods 12 in off the back wall
    kit.wbox('C3 hang shelf', hx0, hx1, 6.75, 6.81, zb + 0.002, z1, mel, 0.005, 1)
    kit.wbox('C3 base rail', hx0, hx1, 0.025, 0.455, zb, zb + SKIRT_PROUD, 'paint_trim', 0.0)
    for y in (6.58, 3.48):
        F.closet_rod(kit, f'C3 {y:.2f}', hx0, hx1, zr, y, 'x')
    S, T, J = F.SHIRTS, F.TROUSERS, F.JACKETS
    # packed from the west end, where the doorway stands open; fronts face west, toward the room
    F.hanger_row(kit, M, hx0, hx1, zr, 6.58, 'C3 upper', 'x', seed=6, start='a0', front=-1, floor_y=3.7,
                 items=[('shirt', S[0]), ('stripe', S[0]), ('shirt', S[4]), ('jacket', J[2]), ('shirt', S[2]), ('shirt', S[3]),
                        ('jacket', J[1]), ('shirt', S[6]), ('shirt', S[8])])
    F.hanger_row(kit, M, hx0, hx1, zr, 3.48, 'C3 lower', 'x', seed=9, start='a0', front=-1, floor_y=0.3, subsurf=0,
                 items=[('trousers', T[i]) for i in (1, 3, 0, 5, 2, 4, 1, 0)])
    F.disk_light(kit, (hx0 + hx1) / 2, zb + 1.25, 'C3', 8.0, 0.32, B.LIGHTS['C3']['disk'])
    bpy.context.view_layer.update()
    deepest = max(bbox(o)[5] for o in ctx.coll('zone_bedrooms_bed3_closet').all_objects if o.type == 'MESH')
    lowest = min(bbox(o)[4] for o in ctx.coll('zone_bedrooms_bed3_closet').all_objects if o.type == 'MESH')
    if deepest > zf - 0.2 or lowest < zb - 1e-4:
        raise RuntimeError(f'the closet fit-out leaves its room: z {lowest:.3f}..{deepest:.3f} in {zb:.3f}..{zf:.3f}')
    return {'clear': _r(R.ROOMS['bed3_closet']), 'units x': _r((tx0, tx1, hx0, hx1, ex0, ex1)), 'unit depth': d,
            'contents z': _r((lowest, deepest)), 'free in front (to the wall face)': round(zf - deepest, 3)}


def _bed3_art(ctx):
    """A wide canvas over the bed on the closed west wall, centred on the headboard as built."""
    from . import bedrooms as B
    from . import bedrooms_furniture as F
    from . import bedrooms_kit as K
    hb = [o for o in bpy.data.objects if o.name == 'B3 bed headboard']
    if not hb:
        return 'no bed: skipped'
    b = bbox(hb[0])
    zc = (b[4] + b[5]) / 2
    kit = K.Kit(ctx)
    kit.use('bed3')
    w, h, yc = 4.7, 2.35, 5.2
    F.canvas_art(kit, K.Frame(R.XW, zc, B.WEST), 'B3 art bed', w, h, K.art_brush(1320, 660, seed=12), y_c=yc)
    return {'centre z': round(zc, 3), 'canvas w x h': (w, h), 'y': (round(yc - h / 2, 2), round(yc + h / 2, 2)),
            'headboard top': round(b[3], 3)}


def _bed4_shade(ctx):
    """Bedroom 4's roller shade, inside the wider window's reveal (bl/revisions.white_windows seats it against the
    grid bars afterwards)."""
    from . import bedrooms as B
    from . import bedrooms_furniture as F
    from . import bedrooms_kit as K
    kit = K.Kit(ctx)
    kit.use('bed4')
    n0, n1 = RS.BED4_WEST_WIN_Z
    w = n1 - n0 - 0.02                                  # v7 repair: 1/8 in clear of each reveal (it was 0.07 ft
    #                                                     short each side: daylight beside the cassette's ends)
    F.roller_shade(kit, F.mats(), K.Frame(R.XW, (n0 + n1) / 2, B.WEST), 'B4 W12 shade', w, RS.BED4_WEST_WIN_Y[1],
                   RS.BED4_WEST_WIN_SHADE_DROP)
    return {'width': round(w, 3), 'centre z': round((n0 + n1) / 2, 3)}


def _bed3_pendant(ctx):
    """v7 repair: Bedroom 3's ring pendant hangs from the ridge of the ceiling as built. The zone hangs it from the
    concept's vault (ridge x 7.036 at 11.5 ft); the room is 14'-11" wide now and its ceiling is the roof track's
    (bl/roof.bed3_vault: ridge x 7.683 at 11.108), so the canopy sat inside the roof slab and the three cables came
    out of the west slope 0.64 ft off the ridge. The ring and its diffuser move onto the ridge line; the canopy is
    built again on the ceiling's surface, following both slopes, and the cables run from it to the ring, which hangs
    centred under it."""
    from .. import roof
    from . import bedrooms_furniture as F
    from . import bedrooms_kit as K
    ring = [o for o in bpy.data.objects if o.name in ('B3 pendant ring', 'B3 pendant diffuser')]
    if len(ring) != 2:
        return 'no pendant: skipped'
    b = bbox([o for o in ring if o.name == 'B3 pendant ring'][0])
    xc, zc, y_top = (b[0] + b[1]) / 2, (b[4] + b[5]) / 2, b[3]
    x = roof.WING_X
    for o in ring:
        o.location.x += (x - xc) * FT
    gone = remove(find(r'^B3 pendant (canopy|cable \d+)$'))
    bpy.context.view_layer.update()
    kit = K.Kit(ctx)
    kit.use('bed3_lights')
    y_can = F.ridge_canopy(kit, None, x, zc, 'B3 pendant', 0.2, 'black_metal', vault=roof.bed3_vault)
    for o in find(r'^B3 pendant canopy'):               # (the removed canopy's mesh still holds the plain name)
        o.name = 'B3 pendant canopy'
    F.pendant_cables(kit, 'B3', x, zc, y_can, y_top, (b[1] - b[0]) / 2 - 0.05)
    return {'ridge x': round(x, 3), 'was x': round(xc, 3), 'z': round(zc, 3), 'ceiling at the ridge': round(roof.bed3_vault(x), 3),
            'canopy underside': round(y_can, 3), 'ring top': round(y_top, 3), 'old parts removed': gone}


def _baseboards(ctx):
    """v7 repair: baseboards on the walls that never had one: Bedroom 3's front wall on both sides of the bay and
    Bedroom 4's south wall (west of the closet's opening and the stub east of it). Copies of the room's own run on
    the west wall (same section, 0.057 ft proud of the wall face), butted between the side walls' runs and the
    openings' edges."""
    out = {}
    for room, src_pat, wall_pat, south in (
            ('Bedroom 3 front wall', r'^\d+ Painted skirting — Bedroom 3 front extension west pier$',
             r'^\d+ Bedroom 3 front wall beside bay$', True),
            ('Bedroom 4 south wall', r'^\d+ Painted skirting — Bedroom 4 west addition$',
             r'^\d+ Bedroom 4 service wall — (west solid|east jamb)$', True)):
        src = _boxes(src_pat)
        walls = _boxes(wall_pat)
        if not src or not walls:
            out[room] = f'not found ({len(src)} baseboards, {len(walls)} wall pieces)'
            continue
        sb = bbox(src[0])
        runs = []
        for w in sorted(walls, key=lambda o: bbox(o)[0]):
            wb = bbox(w)
            face = wb[4]                                             # the room's side of a wall on its south
            x0 = max(wb[0], R.XW + SKIRT_PROUD)                      # between the side walls' own runs
            x1 = min(wb[1], R.X_SBATH_E - SKIRT_PROUD)
            nm = f'Painted skirting — {room} {"W" if x0 < 5.0 else "E"}'
            _like(src[0], nm, x0, x1, sb[2], sb[3], face - SKIRT_PROUD, face + SKIRT_SUNK)
            runs.append((nm[19:], round(x0, 3), round(x1, 3), round(face, 3)))
        out[room] = runs
    bpy.context.view_layer.update()
    return out


def _bay_reveals(ctx):
    """v7 repair (review O16): at the two ends of Bedroom 3's front wall, where the bay opens, the wall piece's painted
    end and the end of the stucco skin in front of it lay in one plane (x 3.293 and x 12.024), visible on 0.03 ft of
    each reveal between the room's wall face and the bay's pier, floor to ceiling. The painted wall's ends stand
    0.004 ft into the opening, in front of the stucco's ends."""
    walls = _boxes(r'^\d+ Bedroom 3 front wall beside bay$')
    out = []
    for w in walls:
        b = bbox(w)
        if b[0] < 1.0:                                  # the west piece: its east end
            out.append(('W', round(b[1], 3), round(b[1] + 0.004, 3), move_face(w, 'x', b[1], b[1] + 0.004, tol=0.001)))
        else:                                           # the east piece: its west end
            out.append(('E', round(b[0], 3), round(b[0] - 0.004, 3), move_face(w, 'x', b[0], b[0] - 0.004, tol=0.001)))
    bpy.context.view_layer.update()
    return out


def fit_out(ctx):
    out = {}
    out['bay reveals'] = _bay_reveals(ctx)              # v7 repair
    out['baseboards'] = _baseboards(ctx)                # v7 repair
    if 'bedrooms' in ctx.stats:
        out['closet'] = _closet(ctx)
        out['Bedroom 4 shade'] = _bed4_shade(ctx)
        out['Bedroom 3 pendant'] = _bed3_pendant(ctx)   # v7 repair
        if not RS.BED3_WEST_WINDOW:
            out['picture over the bed'] = _bed3_art(ctx)
    else:
        out['bedrooms'] = 'zone not built: skipped'
    if bpy.data.collections.get('zone_baths_suite3') is not None:
        from . import baths_suite3
        out['bath'] = baths_suite3.build_room(ctx)
    else:
        out['bath'] = 'baths zone not built: skipped'
    bpy.context.view_layer.update()
    return out
