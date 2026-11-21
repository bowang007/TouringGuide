"""Primary suite, sixth round (2026-11-20): the walls and doors of the 8 ft zone between the primary bedroom and
the primary bath, as the architect's sheet divides it (bl/revision_spec.SUITE_*). Runs inside Blender AFTER the warp,
from bl/revisions.suite_rooms, so every number here is SCENE feet on the architect's plan.

Until the fifth round the zone was one open dressing area. Now:

* the wall between bedroom and closet (shell piece 1836) runs on to x 6.725 and the header over the bedroom opening
  (1901) starts there: the opening bedroom <-> vestibule is x 6.725..11.308;
* the WALK-IN CLOSET's new east wall, x 6.308..6.725, in three pieces (north of the door, the header, the door
  pocket): copies of the wall 1836, so they keep its `scene_index` (web bake class 'wall') and the interior paint on
  every face (closet, vestibule and bedroom share one wall paint);
* the closet's sliding POCKET door, 2'-6" x 6'-8", centred on the closet: a full strike jamb at the north end, a
  split jamb at the pocket mouth, split head trim with the black track between, the flush leaf standing
  SUITE_CLOSET_LEAF_SHOWN out of the pocket with a flush pull on both faces and an edge pull, two floor guides;
* the SUITE ENTRY (D09) in the vestibule's east wall: the three shell pieces are reshaped onto the new 2'-8" opening
  (the old trims, hinged leaf and lever go), painted jamb liners and head trim like the house's other doors, a flush
  sliding panel on a slim black top track on the hall face, parked open to the south, a bar pull on its hall face,
  a flush pull on the back, a floor guide;
* baseboards: the existing runs are carried to the new corners and jambs and new runs (copies of the closet's west
  run) go along both faces of the new wall; the outside corner at the bedroom opening gets a plinth block
  (bl/revisions.skirting_trim would cut a run that turned the corner);
* the attic access hatch in the vestibule's ceiling (a painted panel in a thin frame; nothing is cut).

The closet's interior, the vestibule's mirror and lights and the bedroom's furniture are the zone's:
bl/zones/primary_suite.fit_out, called by bl/revisions.suite_fit_out.
"""
import re

from .. import revision_spec as RS
from ..revisions import COLL_OPEN, COLL_SHELL, _like, _paint_all, _reshape, bbox, ceiling_y, find, move_face, remove

SKIRT_PROUD, SKIRT_SUNK = 0.050, 0.002        # the house's baseboard section: off the wall face / into it
EMBED = 0.01                                  # new wall ends run this far into the walls they butt against


def _r(v):
    return [round(float(a), 3) for a in v]


def _one(pat, pick=lambda b: True, coll=COLL_SHELL):
    """The one plain box piece (8 vertices) of a collection whose name matches `pat`, or None."""
    obs = [o for o in find(pat, coll) if o.type == 'MESH' and len(o.data.vertices) == 8 and pick(bbox(o))]
    return obs[0] if len(obs) == 1 else None


def _need(ob, what):
    if ob is None:
        raise RuntimeError(f'{what}: not found (or more than one)')
    return ob


def _wall_at(x, y, z):
    """True when a shell wall piece (not a baseboard) contains the point."""
    for o in find(r'.', COLL_SHELL):
        if o.type != 'MESH' or len(o.data.vertices) != 8 or re.search(r'skirting|baseboard|plinth', o.name, re.I):
            continue
        b = bbox(o)
        if b[0] <= x <= b[1] and b[2] <= y <= b[3] and b[4] <= z <= b[5] and b[3] - b[2] > 1.0:
            return True
    return False


def _end(ob, axis, old, new, what):
    """Move the end face of a box piece from `old` to `new`; anything but the four corners of one face is an error."""
    n = move_face(ob, axis, old, new)
    if n != 4:
        raise RuntimeError(f'{what}: {n} vertices at {axis} {old:.3f}, expected 4')


def build(ctx):
    out = {}
    cx0, cx1, cz0, cz1 = RS.SUITE_CLOSET_CLEAR
    wx0, wx1 = RS.SUITE_CLOSET_WALL_X
    d0, d1 = RS.SUITE_CLOSET_DOOR_Z
    box = ctx.box

    # ------------------------------------------------------------ 1. bedroom / closet wall and the bedroom opening
    north = _need(_one(rf'^\d+ {re.escape(RS.SUITE_NORTH_WALL)}$'), 'wall between bedroom and closet')
    header = _need(_one(rf'^\d+ {re.escape(RS.SUITE_NORTH_HEADER[:44])}'), 'header over the bedroom opening')
    nb, hb = bbox(north), bbox(header)
    nz0, nz1 = RS.SUITE_NORTH_WALL_Z
    if max(abs(nb[4] - nz0), abs(nb[5] - nz1), abs(nb[1] - RS.SUITE_NORTH_WALL_OLD_X1), abs(hb[0] - nb[1])) > 0.02 \
            or abs(nz1 - cz0) > 1e-6:
        raise RuntimeError(f'bedroom / closet wall is not where the spec expects it: {_r(nb)}, header {_r(hb)}')
    _end(north, 'x', nb[1], wx1, 'bedroom / closet wall, east end')
    _end(header, 'x', hb[0], wx1, 'bedroom opening header, west end')
    _paint_all(north)
    _paint_all(header)
    out['bedroom opening'] = {'x': _r(RS.SUITE_BED_OPENING_X), 'head': round(hb[2], 3),
                              'wall 1836 x': _r(bbox(north)[:2]), 'header 1901 x': _r(bbox(header)[:2])}

    # ------------------------------------------------------------ 2. the closet's east wall
    ceil = [ceiling_y(x, z) for x in (cx0 + 0.5, wx0 + 0.2, wx1 + 0.5, 10.8) for z in (cz0 + 0.3, 16.8, cz1 - 0.3)]
    top = max(RS.SUITE_CEILING, max(ceil))
    out['ceiling y'] = [round(min(ceil), 3), round(max(ceil), 3)]
    walls = {}
    for name, x0, x1, y0, y1, z0, z1 in RS.suite_closet_walls():
        y1 = top if y1 == RS.SUITE_CEILING else y1
        z0 = z0 - EMBED if abs(z0 - cz0) < 1e-6 else z0          # into the bedroom / closet wall
        z1 = z1 + EMBED if abs(z1 - cz1) < 1e-6 else z1          # into the bath's north wall
        walls[name] = _like(north, name, x0, x1, y0, y1, z0, z1)
        _paint_all(walls[name])
    out['closet east wall'] = {n: _r(bbox(o)) for n, o in walls.items()}

    # ------------------------------------------------------------ 3. the closet's pocket door
    c = COLL_OPEN
    head, ln, ow = RS.SUITE_CLOSET_DOOR_HEAD, RS.SUITE_CLOSET_DOOR_LINER, RS.SUITE_CLOSET_DOOR_LINER_PROUD
    xc, slot = RS.SUITE_CLOSET_DOOR_C, RS.SUITE_CLOSET_SLOT
    xl0, xl1 = wx0 - ow, wx1 + ow
    box('Primary closet door jamb N (strike)', xl0, xl1, 0.0, head - 0.08, d0 - ln, d0 + ln, 'paint_trim', c)
    box('Primary closet door jamb S (pocket, closet half)', xl0, xc - slot, 0.0, head - 0.08, d1 - ln, d1 + ln, 'paint_trim', c)
    box('Primary closet door jamb S (pocket, vestibule half)', xc + slot, xl1, 0.0, head - 0.08, d1 - ln, d1 + ln, 'paint_trim', c)
    box('Primary closet door head trim (closet half)', xl0, xc - slot, head - 0.08, head + 0.06, d0 - ln, d1 + ln, 'paint_trim', c)
    box('Primary closet door head trim (vestibule half)', xc + slot, xl1, head - 0.08, head + 0.06, d0 - ln, d1 + ln, 'paint_trim', c)
    box('Primary closet door pocket track', xc - slot, xc + slot, head - 0.045, head + 0.06, d0 + ln, d1 + ln, 'black_metal', c)
    # the slot the leaf runs in, dark, on the pocket wall's end face between the two jamb halves
    box('Primary closet door pocket slot', xc - slot, xc + slot, 0.0, head - 0.045, d1 - 0.006, d1 + 0.004, 'paint_black', c)
    leaf = RS.suite_closet_leaf()
    lx0, lx1, ly0, ly1, lz0, lz1 = leaf['aabb']
    ctx.box_c(leaf['name'], leaf['center'], leaf['size'], leaf['rot'], 'door_slab', c, bevel=0.006, segments=2)
    inset, py0, py1 = RS.SUITE_CLOSET_PULL
    for tag, fx in (('closet', lx0), ('vestibule', lx1)):                   # flush pulls: a black cup let into each face
        s = -1.0 if tag == 'closet' else 1.0
        box(f'Primary closet door flush pull ({tag} face)', min(fx - s * 0.012, fx + s * 0.0025), max(fx - s * 0.012, fx + s * 0.0025),
            py0, py1, lz0 + inset - 0.045, lz0 + inset + 0.045, 'black_metal', c)
        box(f'Primary closet door flush pull cup ({tag} face)', min(fx - s * 0.012, fx + s * 0.004), max(fx - s * 0.012, fx + s * 0.004),
            py0 + 0.05, py1 - 0.05, lz0 + inset - 0.022, lz0 + inset + 0.022, 'paint_black', c)
    box('Primary closet door edge pull', xc - 0.022, xc + 0.022, 3.08, 3.42, lz0 - 0.003, lz0 + 0.01, 'black_metal', c)
    for tag, gx in (('closet', lx0 - 0.019), ('vestibule', lx1 + 0.004)):   # nylon guides either side of the leaf
        box(f'Primary closet door floor guide ({tag} side)', gx, gx + 0.015, 0.0, 0.075, d1 - ln - 0.035, d1 - ln, 'black_metal', c)
    out['closet door'] = {'opening z': _r((d0, d1)), 'head': head, 'pocket': RS.SUITE_CLOSET_DOOR_POCKET,
                          'leaf': _r(leaf['aabb']), 'shown': RS.SUITE_CLOSET_LEAF_SHOWN,
                          'clear passage': round(d1 - RS.SUITE_CLOSET_LEAF_SHOWN - (d0 + ln), 3)}

    # ------------------------------------------------------------ 4. the suite entry (D09)
    ex0, ex1 = RS.SUITE_ENTRY_WALL_X
    e0, e1 = RS.SUITE_ENTRY_Z
    o0, o1 = RS.SUITE_ENTRY_OLD_Z
    eh = RS.SUITE_ENTRY_HEAD
    en = _need(_one(r'^\d+ Aligned primary-suite east wall — north$'), 'suite entry wall, north piece')
    es = _need(_one(r'^\d+ Aligned primary-suite east wall — south$'), 'suite entry wall, south piece')
    eh_ob = _need(_one(r'^\d+ Aligned primary-suite entry header$'), 'suite entry header')
    enb, esb, ehb = bbox(en), bbox(es), bbox(eh_ob)
    if max(abs(enb[5] - o0), abs(esb[4] - o1), abs(enb[0] - ex0), abs(enb[1] - ex1), abs(ehb[2] - eh)) > 0.02:
        raise RuntimeError(f'suite entry wall is not where the spec expects it: {_r(enb)}, {_r(esb)}, {_r(ehb)}')
    _end(en, 'z', enb[5], e0, 'suite entry wall north piece, south end')
    _end(es, 'z', esb[4], e1, 'suite entry wall south piece, north end')
    _reshape(eh_ob, ehb[0], ehb[1], ehb[2], ehb[3], e0, e1)
    for ob in (en, es, eh_ob):
        _paint_all(ob)
    gone = remove(find(r'^\d+ Aligned primary-suite entry trim', COLL_OPEN))
    gone += remove(find(r'^\d+ Primary suite entrance door', COLL_OPEN))
    ln2, ow2 = RS.SUITE_ENTRY_LINER, RS.SUITE_ENTRY_LINER_PROUD
    box('Primary suite entry jamb N', ex0 - ow2, ex1 + ow2, 0.0, eh - 0.08, e0 - ln2, e0 + ln2, 'paint_trim', c)
    box('Primary suite entry jamb S', ex0 - ow2, ex1 + ow2, 0.0, eh - 0.08, e1 - ln2, e1 + ln2, 'paint_trim', c)
    box('Primary suite entry head trim', ex0 - ow2, ex1 + ow2, eh - 0.08, eh + 0.06, e0 - ln2, e1 + ln2, 'paint_trim', c)
    panel = RS.suite_entry_panel()
    px0, px1, py0, py1, pz0, pz1 = panel['aabb']
    ctx.box_c(panel['name'], panel['center'], panel['size'], panel['rot'], 'door_slab', c, bevel=0.006, segments=2)
    ty0, ty1 = RS.SUITE_ENTRY_TRACK_Y
    tz0, tz1 = RS.SUITE_ENTRY_TRACK_Z
    box('Primary suite entry sliding track', px0 - 0.012, px1 + 0.012, ty0, ty1, tz0, tz1, 'black_metal', c)
    for i, tz in enumerate((tz0 + 0.35, (tz0 + tz1) / 2, tz1 - 0.35)):     # the track's standoffs to the wall
        box(f'Primary suite entry sliding track bracket {i}', ex1, px0 - 0.012, ty0 + 0.035, ty1 - 0.035, tz - 0.04, tz + 0.04,
            'black_metal', c)
    inset, by0, by1 = RS.SUITE_ENTRY_PULL
    bz = pz0 + inset
    box('Primary suite entry sliding panel bar pull', px1 + 0.055, px1 + 0.09, by0, by1, bz - 0.0175, bz + 0.0175, 'black_metal', c)
    for i, yy in enumerate((by0 + 0.12, by1 - 0.12)):
        box(f'Primary suite entry sliding panel bar pull post {i}', px1, px1 + 0.06, yy - 0.014, yy + 0.014, bz - 0.014, bz + 0.014,
            'black_metal', c)
    box('Primary suite entry sliding panel flush pull', px0 - 0.0025, px0 + 0.012, 3.0, 3.6, bz - 0.045, bz + 0.045, 'black_metal', c)
    gz = e1 + ln2 + 0.05                                                   # floor guide just south of the south jamb
    box('Primary suite entry floor guide plate', px0 - 0.026, px1 + 0.035, 0.0, 0.012, gz - 0.05, gz + 0.05, 'black_metal', c)
    for tag, gx in (('wall', px0 - 0.025), ('hall', px1 + 0.004)):
        box(f'Primary suite entry floor guide post ({tag} side)', gx, gx + 0.022, 0.0, 0.11, gz - 0.02, gz + 0.02, 'black_metal', c)
    # Bedroom 2's doorless entry D12 butts on this wall's hall face: its header stopped 0.113 ft short of the wall
    b2 = _one(rf'^\d+ {re.escape(RS.SUITE_BED2_HEADER)}$')
    if b2 is not None and abs(bbox(b2)[0] - RS.SUITE_BED2_HEADER_OLD_X0) < 0.02 and bbox(b2)[4] < e0:
        _end(b2, 'x', bbox(b2)[0], ex1, "Bedroom 2 entry header, west end")
        _paint_all(b2)
        out['Bedroom 2 entry header x'] = _r(bbox(b2)[:2])
    out['suite entry'] = {'opening z': _r((e0, e1)), 'head': eh, 'was z': _r((o0, o1)), 'sheet z': _r(RS.SUITE_ENTRY_SHEET_Z),
                          'old door parts removed': gone, 'panel': _r(panel['aabb']),
                          'track': _r((px0 - 0.012, px1 + 0.012, ty0, ty1, tz0, tz1)),
                          'walls': {'north': _r(bbox(en)), 'header': _r(bbox(eh_ob)), 'south': _r(bbox(es))}}

    # ------------------------------------------------------------ 5. baseboards
    P, S = SKIRT_PROUD, SKIRT_SUNK
    src = _need(_one(r'^\d+ Painted skirting — Walk-in closet — west wall$'), "the closet's west baseboard")
    sy0, sy1 = bbox(src)[2:4]
    sk = {}

    def skirt(name, x0, x1, z0, z1, block=False):
        nm = f'Primary closet plinth block {name}' if block else f'Painted skirting — {name}'
        return _like(src, nm, x0, x1, sy0, sy1, z0, z1)

    def runs(z_lo, z_hi, x_lo=-1.0, x_hi=40.0):
        """Baseboard pieces lying along x whose z-range is inside z_lo..z_hi (one face of an east-west wall)."""
        return [(o, bbox(o)) for o in find(r'skirting|baseboard', COLL_SHELL) if o.type == 'MESH' and len(o.data.vertices) == 8
                and (lambda b: b[4] >= z_lo and b[5] <= z_hi and b[1] - b[0] > b[5] - b[4] and b[0] < x_hi and b[1] > x_lo)(bbox(o))]

    # bedroom face of the bedroom / closet wall: the two families of runs go on to the opening's jamb
    moved = 0
    for ob, b in runs(nz0 - 0.08, nz0 + 0.01, x_hi=wx1):
        if abs(b[1] - RS.SUITE_NORTH_WALL_OLD_X1) < 0.05:
            _end(ob, 'x', b[1], wx1, f'bedroom baseboard {ob.name!r}')
            moved += 1
    sk['bedroom south wall runs carried to x %.3f' % wx1] = moved
    zb = min([b[4] for _, b in runs(nz0 - 0.08, nz0 + 0.01, x_hi=wx1)] or [nz0 - 0.046])
    # closet face of that wall: on to the closet's north-east corner
    n_in = [(ob, b) for ob, b in runs(nz1 - 0.01, nz1 + 0.12, x_hi=wx1) if abs(b[1] - RS.SUITE_NORTH_WALL_OLD_X1) < 0.05]
    tn = P
    for ob, b in n_in:
        _end(ob, 'x', b[1], cx1, f'closet north baseboard {ob.name!r}')
        tn = max(tn, b[5] - nz1)
    sk['closet north run carried to x %.3f' % cx1] = len(n_in)
    # the bath's north wall, closet / vestibule face: the run inside the closet ends in its south-east corner; nothing
    # may cross the new wall; whatever lies east of it starts at the vestibule run's face
    ts = P
    south = runs(cz1 - 0.12, cz1 + 0.01, x_hi=wx1 + P + 0.01)
    inside = sorted([(ob, b) for ob, b in south if b[0] < cx1 - 0.5], key=lambda t: -t[1][1])
    for k, (ob, b) in enumerate(inside):
        ts = max(ts, cz1 - b[4])
        if k == 0 and abs(b[1] - cx1) > 1e-4:
            _end(ob, 'x', b[1], cx1, f'closet south baseboard {ob.name!r}')
        elif k > 0 and b[1] > cx1:
            _end(ob, 'x', b[1], cx1, f'closet south baseboard {ob.name!r}')
    for ob, b in south:
        if b[0] >= cx1 - 0.5:
            if b[1] <= wx1 + P + 0.01:
                remove([ob])
            elif b[0] < wx1 + P:
                _end(ob, 'x', b[0], wx1 + P, f'vestibule south baseboard {ob.name!r}')
    sk['closet south run'] = [_r(bbox(ob)) for ob, _ in inside[:1]] or 'none found: built'
    if not inside:
        skirt('Primary closet south wall', cx0 - S, cx1, cz1 - P, cz1 + S)
    # both faces of the new wall, each side of the door
    la, lb = d0 - ln, d1 + ln                                       # outer edges of the jamb liners
    skirt('Primary closet east wall, closet face N', cx1 - P, cx1 + S, cz0 + tn, la)
    skirt('Primary closet east wall, closet face S', cx1 - P, cx1 + S, lb, cz1 - ts)
    skirt('Primary closet east wall, vestibule face N', wx1 - S, wx1 + P, nz0, la)
    skirt('Primary closet east wall, vestibule face S', wx1 - S, wx1 + P, lb, cz1 + S)
    skirt('NE (bedroom opening)', wx1, wx1 + P, zb, nz0, block=True)
    # the short stretch of the bath's north wall between the new wall and the bath door (when that door is where the
    # sheet has it; with no wall behind it bl/revisions.skirting_trim takes the piece away again)
    bath_x0 = getattr(RS, 'BATH_DOOR_X', (None,))[0]
    if bath_x0 is not None and not runs(cz1 - 0.12, cz1 + 0.01, x_lo=wx1 + P + 0.02, x_hi=bath_x0 - 0.04):
        stub_x1 = bath_x0 - getattr(RS, 'BATH_DOOR_LINER', 0.03)
        if stub_x1 - (wx1 + P) > 0.03 and _wall_at((wx1 + P + stub_x1) / 2, 0.2, cz1 + 0.1):
            skirt('Vestibule south wall, west of the bath door', wx1 + P, stub_x1, cz1 - P, cz1 + S)
            sk['vestibule south stub'] = _r((wx1 + P, stub_x1))
    # the suite entry: the vestibule-side runs go to the new jamb liners (and close the 0.04 ft joint at the bedroom
    # opening's east jamb), the hall-side run south of the door too
    for pat, pick, axis_end, new, what in (
            (r'east wall — no', lambda b: b[1] < ex0 + 0.02, 5, e0 - ln2, 'vestibule east run N, south end'),
            (r'east wall — no', lambda b: b[1] < ex0 + 0.02, 4, cz0 - 0.2, 'vestibule east run N, north end'),
            (r'east wall — so', lambda b: b[1] < ex0 + 0.02, 4, e1 + ln2, 'vestibule east run S, north end'),
            (r'east wall — so', lambda b: b[0] > ex1 - 0.02, 4, e1 + ln2, 'hall run S, north end'),
            # (a hall-side run north of the old opening that had no wall behind it until now: it ends at the liner)
            (r'east wall — no', lambda b: b[0] > ex1 - 0.02 and b[5] > e0, 5, e0 - ln2, 'hall run N, south end')):
        # (names are cut at 60 characters)
        ob = _one(r'^\d+ Painted skirting — Aligned primary-suite ' + pat, pick)
        if ob is None:
            sk[what] = 'not found'
            continue
        b = bbox(ob)
        _end(ob, 'z', b[axis_end], new, what)
        sk[what] = round(new, 3)
    # the hall face north of the entry: the shell builds that run in two pieces that stop 0.02 ft short of each other
    # (a joint of the concept's walls); the wall is one piece now, so the northern piece runs on to the southern one
    hall_n = _one(r'^\d+ Painted skirting — Aligned primary-suite east wall — no', lambda b: b[0] > ex1 - 0.02)
    if hall_n is not None:
        hz0 = bbox(hall_n)[4]
        for ob in find(r'^\d+ Painted skirting — ', COLL_SHELL):
            b = bbox(ob)
            if ob is not hall_n and len(ob.data.vertices) == 8 and abs(b[0] - bbox(hall_n)[0]) < 0.01 and 0.005 < hz0 - b[5] < 0.08:
                _end(ob, 'z', b[5], hz0, f'hall run {ob.name!r}, south end')
                sk['hall run joint closed at z'] = round(hz0, 3)
    out['baseboards'] = sk

    # ------------------------------------------------------------ 6. attic access hatch (vestibule ceiling)
    hx0, hx1, hz0, hz1 = RS.SUITE_ATTIC_HATCH
    yc = min(ceiling_y((hx0 + hx1) / 2, (hz0 + hz1) / 2), top)
    fw, fp, gap = 0.085, 0.024, 0.012
    for tag, a in (('N', (hx0 - fw, hx1 + fw, hz0 - fw, hz0)), ('S', (hx0 - fw, hx1 + fw, hz1, hz1 + fw)),
                   ('W', (hx0 - fw, hx0, hz0, hz1)), ('E', (hx1, hx1 + fw, hz0, hz1))):
        box(f'Vestibule ceiling attic access frame {tag}', a[0], a[1], yc - fp, yc, a[2], a[3], 'paint_trim', c)
    box('Vestibule ceiling attic access shadow gap', hx0, hx1, yc - 0.003, yc, hz0, hz1, 'paint_black', c)
    box('Vestibule ceiling attic access panel', hx0 + gap, hx1 - gap, yc - 0.014, yc - 0.0015, hz0 + gap, hz1 - gap, 'paint_ceiling', c)
    box('Vestibule ceiling attic access latch', (hx0 + hx1) / 2 - 0.07, (hx0 + hx1) / 2 + 0.07, yc - 0.018, yc - 0.014,
        hz1 - gap - 0.11, hz1 - gap - 0.06, 'paint_trim', c)
    out['attic hatch'] = {'opening': _r(RS.SUITE_ATTIC_HATCH), 'ceiling y': round(yc, 3)}
    out['closet clear'] = _r(RS.SUITE_CLOSET_CLEAR)
    out['vestibule clear'] = _r(RS.SUITE_VESTIBULE_CLEAR)
    return out
