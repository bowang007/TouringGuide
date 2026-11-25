"""v7 garage (owner's eighth round, 2026-11-24, stage B): the garage and the two entrances on the architect's sheet
(runs inside Blender, after bl/warp.py; called by bl/revisions.garage_v7). Numbers: bl/garage_spec.py, in plan feet.

  vehicle_opening  the vehicle door's wall opening: 15'-0" wide (the shell builds it there, relayout.GARAGE_DOOR_RO),
                   its head 7'-0" above the GARAGE floor (the door, its jamb boards and its hardware are built on
                   that floor by bl/zones/exterior_garage.py);
  floor            the garage floor 11 in below the house floor: slab and foundation lowered, the walls' inside
                   finish carried down to the slab on four bases, baseboards re-seated, the step at the house door,
                   and whatever of the site (foundation plinth, ground) stands in the lowered room or in the two door
                   openings cut away;
  house_door       the door between the foyer and the garage at the sheet's place (DR17): 3'-0", hinged on the north
                   jamb, open into the garage, spring hinges, levers; its switches on the latch side;
  side_door        the garage's side door in the east wall (DR18): 2'-8" opening, closed solid leaf, frame proud of
                   both faces, threshold on a concrete sill;
  front_door       the front door unit (DR16): 3'-0" walnut leaf centred on the foyer between two glazed sidelights
                   (white frame; bl/revisions.white_windows gives the sidelights their grid bars);
  water_heater     the tank water heater in the garage's north-east corner (FX11), on a stand, strapped to the wall.

Every step reports what it built; a step that does not find the piece it expects raises, which shows as FAILED on
the `revisions:` line.
"""
import math
import re
import traceback

import bpy

from . import garage_spec as GS
from .common import FT, ft2bl

R = GS.R
COLL_SHELL, COLL_OPEN, COLL_EXT = 'shell', 'openings', 'exterior_shell'
C_GAR, C_ENTRY, ZONE = 'heg_garage', 'heg_entry', 'zone_hall_entry_garage'


def _rv():
    from . import revisions
    return revisions


def _r(v, n=3):
    return [round(float(a), n) for a in v]


# ------------------------------------------------------------------------------------------------ helpers
def _boxes(pat, coll=COLL_SHELL, pick=None):
    RV = _rv()
    return [o for o in RV.find(pat, coll) if o.type == 'MESH' and len(o.data.vertices) == 8
            and (pick is None or pick(RV.bbox(o)))]


def _one(pat, coll=COLL_SHELL, pick=None):
    obs = _boxes(pat, coll, pick)
    if len(obs) != 1:
        raise RuntimeError(f'{pat!r}: {len(obs)} pieces in {coll!r}, expected 1')
    return obs[0]


def _plain(name):
    return re.sub(r'^\d+ ', '', name)


def _plan(d, a0, a1, n0, n1):
    """(x0, x1, z0, z1) of a range along a door's wall (a) and a range across it (n)."""
    return (n0, n1, a0, a1) if d['axis'] == 'z' else (a0, a1, n0, n1)


def _bx(ctx, name, d, a0, a1, y0, y1, n0, n1, mat, coll=COLL_OPEN, bevel=0.0):
    x0, x1, z0, z1 = _plan(d, min(a0, a1), max(a0, a1), min(n0, n1), max(n0, n1))
    return ctx.box(name, x0, x1, y0, y1, z0, z1, mat, coll, bevel, 2)


def _kit(ctx, coll, parent=None):
    from . import laundry
    return laundry.Kit(ctx, coll, parent)


def _mat(name, color, **kw):
    from .zones import hall_entry_garage_lib as HL
    return HL.principled(name, color, **kw)


def _frame(ctx, d, tag, mat, lo, hi, foot=None, along=None):
    """A door's frame as the house's other doors have it, in the sheet's size: two jambs between the wall's ends
    and the leaf (d['frame'] wide), a head member, all standing FRAME_PROUD off both wall faces, and door stops on
    the side the leaf closes against. `along` = (a0, a1): the head's extent when it runs over more than the door."""
    w0, w1 = d['wall']
    p = GS.FRAME_PROUD
    r0, r1 = d['ro']
    c0, c1 = d['clear']
    below, above = GS.HEAD_TRIM
    foot = d['floor_y'] if foot is None else foot
    top = d['head'] - below
    e = 0.01                                              # jambs run this far into the wall's ends
    if along is None:
        _bx(ctx, f'{tag} jamb {lo}', d, r0 - e, c0, foot, top, w0 - p, w1 + p, mat, bevel=0.004)
        _bx(ctx, f'{tag} jamb {hi}', d, c1, r1 + e, foot, top, w0 - p, w1 + p, mat, bevel=0.004)
        h0, h1 = r0 - e, r1 + e
    else:
        _bx(ctx, f'{tag} post {lo}', d, r0, c0, foot, top, w0 - p, w1 + p, mat, bevel=0.004)
        _bx(ctx, f'{tag} post {hi}', d, c1, r1, foot, top, w0 - p, w1 + p, mat, bevel=0.004)
        h0, h1 = along
    _bx(ctx, f'{tag} head trim', d, h0, h1, top, d['head'] + above, w0 - p, w1 + p, mat, bevel=0.004)
    # stops: the closed leaf lies against them (its swing-side face is flush with the frame's swing-side edge)
    sw = d['swing']
    face = (w1 + p) if sw > 0 else (w0 - p)               # the frame's swing-side edge, across the wall
    n1 = face - sw * (d['leaf_t'] + 0.008)
    n0 = n1 - sw * 0.045
    st = 0.035
    _bx(ctx, f'{tag} stop {lo}', d, c0, c0 + st, foot, top, n0, n1, mat)
    _bx(ctx, f'{tag} stop {hi}', d, c1 - st, c1, foot, top, n0, n1, mat)
    _bx(ctx, f'{tag} stop head', d, c0 + st, c1 - st, top - st, top, n0, n1, mat)
    return {'jambs': _r((r0, c0, c1, r1)), 'head': round(d['head'], 3)}


def _leaf(ctx, d, tag, mat, spring=False, deadbolt=False, coll=COLL_OPEN):
    """The leaf at its opening angle with its hardware in the house's black metal: three hinges (spring hinges
    with a tension collar when `spring`), a lever on each face pointing to the hinge, and a deadbolt above it."""
    lf = GS.leaf(d)
    ctx.box_c(lf['name'], lf['center'], lf['size'], lf['rot'], mat, coll, bevel=0.006, segments=2)
    kit = _kit(ctx, coll)
    (ox, oz), (ax, az), (tx, tz) = lf['corner'], lf['along'], lf['through']
    px, pz = lf['pivot']
    w, _, th = lf['size']
    fy = d['floor_y']
    bm = 'black_metal'

    def pt(u, y, v):                                     # u along the leaf from its hinge edge, v through it from its swing face
        return (ox + ax * u + tx * v, y, oz + az * u + tz * v)
    r, hh = (0.034, 0.19) if spring else (0.024, 0.1875)  # 4 1/2 in hinges; a spring hinge has a fat barrel
    pw, pt_t = 0.11, 0.006
    c0, c1 = d['clear']
    lo = d['hinge'] == 'lo'
    jface = c0 if lo else c1                              # the hinge jamb's face toward the opening
    sgn = 1.0 if lo else -1.0
    w0, w1 = d['wall']
    edge = (w1 + GS.FRAME_PROUD) if d['swing'] > 0 else (w0 - GS.FRAME_PROUD)
    for i, yh in enumerate(GS.HINGE_Y):
        yh += fy
        kit.cyl(f'{tag} hinge {i}', (px, yh - hh, pz), (px, yh + hh, pz), r, bm, 24)
        for k, ya in enumerate((yh - hh - 0.02, yh + hh)):
            kit.cyl(f'{tag} hinge {i} tip {k}', (px, ya, pz), (px, ya + 0.02, pz), r * 0.7, bm, 16)
        if spring:                                       # tension collar and its pin holes' ring, top of the barrel
            kit.cyl(f'{tag} hinge {i} collar', (px, yh + hh - 0.05, pz), (px, yh + hh - 0.02, pz), r + 0.006, bm, 24)
            kit.cyl(f'{tag} hinge {i} collar low', (px, yh - hh + 0.02, pz), (px, yh - hh + 0.05, pz), r + 0.006, bm, 24)
        ob = ctx.box_c(f'{tag} hinge {i} plate leaf', pt(-pt_t / 2 + 0.001, yh, 0.004 + pw / 2), (pt_t, 2 * hh, pw),
                       lf['rot'], bm, coll)
        kit.objects.append(ob)
        a0, a1 = sorted((jface - sgn * 0.001, jface + sgn * (pt_t - 0.001)))
        n0, n1 = sorted((edge, edge - d['swing'] * pw))
        _bx(ctx, f'{tag} hinge {i} plate jamb', d, a0, a1, yh - hh, yh + hh, n0, n1, bm, coll)
    yl = fy + GS.LEVER_Y
    ul = w - GS.LEVER_INSET
    for side, v0, sg in (('swing side', 0.0, -1.0), ('far side', th, 1.0)):
        kit.cyl(f'{tag} lever {side} rose', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.02), 0.085, bm, 32)
        kit.cyl(f'{tag} lever {side} neck', pt(ul, yl, v0), pt(ul, yl, v0 + sg * 0.17), 0.03, bm, 20)
        kit.cyl(f'{tag} lever {side} bar', pt(ul + 0.02, yl, v0 + sg * 0.15), pt(ul - 0.38, yl, v0 + sg * 0.15), 0.024, bm, 20)
        if deadbolt:
            yd = yl + 0.5
            kit.cyl(f'{tag} deadbolt {side} rose', pt(ul, yd, v0), pt(ul, yd, v0 + sg * 0.035), 0.095, bm, 32)
            if side == 'swing side':                     # the room side: a thumb turn
                ob = ctx.box_c(f'{tag} deadbolt thumb turn', pt(ul, yd, v0 + sg * 0.065), (0.035, 0.12, 0.06), lf['rot'], bm,
                               coll, bevel=0.006, segments=2)
                kit.objects.append(ob)
            else:                                        # outside: the key cylinder
                kit.cyl(f'{tag} deadbolt cylinder', pt(ul, yd, v0 + sg * 0.035), pt(ul, yd, v0 + sg * 0.05), 0.045,
                        'stainless', 24)
    # the latch's face plate on the leaf's free edge
    ob = ctx.box_c(f'{tag} latch plate', pt(w - 0.002, yl, th / 2), (0.006, 0.19, 0.085), lf['rot'], bm, coll)
    kit.objects.append(ob)
    return {'leaf': _r(lf['aabb']), 'width': round(w, 4), 'open deg': d['open_deg'], 'hardware': len(kit.objects)}


def _switch(ctx, frame, name, u, v, gangs, coll):
    from .zones import hall_entry_garage as HEG
    M = {'plastic_w': _mat('plastic_white', '#eeeeec', rough=0.3, coat=0.2)}
    HEG.switch_plate(ctx, M, frame, name, u, v, gangs, coll)
    return M


# ---------------------------------------------------------------------------------------- vehicle door opening
def vehicle_opening(ctx):
    """DR19: the wall's ends stand where the sheet has them (the warp put them there: relayout.GARAGE_DOOR_RO); the
    header comes down with the garage floor, 7'-0" above it (A1.3). Both the shell wall and its stucco skin."""
    RV = _rv()
    out = {}
    r0, r1 = GS.VEHICLE_RO_X
    for label, pat, coll in (('wall', r'^\d+ Garage — front / vehicle door$', COLL_SHELL),
                             ('stucco', r'^\d+ Front stucco · Garage — front / vehicle door$', COLL_EXT)):
        obs = sorted(_boxes(pat, coll), key=lambda o: RV.bbox(o)[0])
        if len(obs) != 3:
            raise RuntimeError(f'{label}: {len(obs)} pieces, expected 3')
        west, hdr, east = obs
        wb, hb, eb = RV.bbox(west), RV.bbox(hdr), RV.bbox(east)
        off = max(abs(wb[1] - r0), abs(hb[0] - r0), abs(hb[1] - r1), abs(eb[0] - r1))
        if off > 0.01:
            raise RuntimeError(f'{label}: the opening is not where the sheet has it: {_r((wb[1], hb[0], hb[1], eb[0]))}')
        RV.move_face(hdr, 'y', hb[2], GS.VEHICLE_HEAD_Y)
        out[label] = {'x': _r((wb[1], eb[0])), 'head y': [round(float(hb[2]), 3), round(GS.VEHICLE_HEAD_Y, 3)]}
    out['width'] = round(r1 - r0, 4)
    out['door'] = _r(GS.VEHICLE_DOOR_X)
    out['height above the garage floor'] = GS.VEHICLE_HEIGHT
    return out


# ------------------------------------------------------------------------------------------------- the floor
def _faces_in(ob, box, e=0.002):
    """Polygons of `ob` whose world box reaches into `box` (x0, x1, y0, y1, z0, z1; SCENE feet)."""
    x0, x1, y0, y1, z0, z1 = box
    me, mw = ob.data, ob.matrix_world
    co = [mw @ v.co for v in me.vertices]
    hit = []
    for poly in me.polygons:
        ps = [co[i] for i in poly.vertices]
        xs, ys, zs = [q.x / FT for q in ps], [q.z / FT for q in ps], [-q.y / FT for q in ps]
        if min(xs) < x1 - e and max(xs) > x0 + e and min(ys) < y1 - e and max(ys) > y0 + e \
                and min(zs) < z1 - e and max(zs) > z0 + e:
            hit.append(poly.index)
    return hit


def _carve(ob, box, hit):
    """Remove what of `ob` lies in `box`: the polygons that reach into it are split on the box's planes and the
    parts inside deleted (no boolean: the site's pieces are plain prisms and planes, and the faces this leaves
    open stand behind the garage's wall bases, its slab and its door frames)."""
    import bmesh
    from mathutils import Vector
    x0, x1, y0, y1, z0, z1 = box
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    inv = ob.matrix_world.inverted()
    rot = inv.to_3x3()
    faces = {bm.faces[i] for i in hit}
    for co, no in ((ft2bl(x0, 0, 0), Vector((1, 0, 0))), (ft2bl(x1, 0, 0), Vector((1, 0, 0))),
                   (ft2bl(0, 0, z0), Vector((0, -1, 0))), (ft2bl(0, 0, z1), Vector((0, -1, 0))),
                   (ft2bl(0, y0, 0), Vector((0, 0, 1))), (ft2bl(0, y1, 0), Vector((0, 0, 1)))):
        geom = list(faces) + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts})
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=inv @ co, plane_no=(rot @ no).normalized(),
                                     clear_inner=False, clear_outer=False)
        faces = {g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)} | {f for f in faces if f.is_valid}
    mw = ob.matrix_world
    gone = []
    for f in faces:
        if not f.is_valid:
            continue
        c = mw @ f.calc_center_median()
        x, y, z = c.x / FT, c.z / FT, -c.y / FT
        if x0 < x < x1 and y0 < y < y1 and z0 < z < z1:
            gone.append(f)
    if gone:                                             # (a piece that only passes by is left as it was)
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        bm.to_mesh(ob.data)
        ob.data.update()
    bm.free()
    return len(gone)


def _pit(ctx, z_end):
    """Nothing of the site may stand in the lowered room or in the two door openings. The site zone builds its
    foundation and stucco bands as a ring under the walls' outer halves, open at both doors, and its ground below
    the slab (bl/zones/exterior_site.plinth), so normally nothing does; a piece that reaches in all the same (a
    solid plinth, a ground plane at the slab's level) is carved back and named in the result. The room's box
    reaches PIT_MARGIN into the walls, behind the bases that carry the inside finish down."""
    RV = _rv()
    g, m = GS.FLOOR_Y, GS.PIT_MARGIN
    y0, y1 = g - 0.01, 0.6
    sd, vr = GS.SIDE_DOOR['ro'], GS.VEHICLE_RO_X
    cuts = [('room', (GS.GX0 - m, GS.GX1 + m, y0, y1, GS.GZ0 - m, GS.GZ1 + m)),
            ('vehicle door', (vr[0], vr[1], y0, y1, GS.GZ1 + m - 0.002, z_end)),
            ('vehicle door, wall', (vr[0], vr[1], g + 0.02, y1, z_end - 0.002, R.Z_GAR_OUT + 0.03)),
            ('side door', (GS.GX1 + m - 0.002, R.XE_OUT - 0.02, y0, y1, sd[0], sd[1])),
            ('side door, outside', (R.XE_OUT - 0.022, R.XE_OUT + 0.03, g + 0.02, y1, sd[0], sd[1]))]
    out = {}
    for label, box in cuts:
        for ob in list(bpy.data.objects):
            if ob.type != 'MESH' or not len(ob.data.vertices) or not any(c.name == 'ext_site' for c in ob.users_collection):
                continue
            b = RV.bbox(ob)
            if not RV._overlap(b, box[0], box[1], box[4], box[5], box[2], box[3]):
                continue
            hit = _faces_in(ob, box)
            if hit:
                out.setdefault(label, {})[ob.name] = _carve(ob, box, hit)
    return out


def floor(ctx):
    """The garage floor 11 in below the house floor (A1.3 "G.F.F.").

    * slab and foundation go down (the slab's top is FLOOR_Y, 4 in thick); the slab runs on through the vehicle
      door's opening to where the driveway starts (exterior_layout.DRIVE);
    * the walls stand on the house floor's level; under each of the garage's four walls a base (a copy of the wall:
      same paint, same `scene_index`) carries the inside finish down to the slab, from the wall's inside face to its
      centre line, with gaps at the vehicle door and the side door;
    * the baseboards sit on the lower floor and end at the step and at the side door's frame;
    * the step at the house door (ST1): 1'-0" x 3'-8", its top half way up (two risers of 5 1/2 in);
    * the site's pieces in the room and the openings are cut away (_pit)."""
    RV = _rv()
    from .zones import exterior_layout as XL
    g = GS.FLOOR_Y
    out = {}
    slab = _one(r'^\d+ Garage concrete$')
    sb = RV.bbox(slab)
    drive, top0 = getattr(XL, 'DRIVE', None), getattr(XL, 'DRIVE_TOP0', None)
    z_end = drive[2] if drive and GS.GZ1 - 0.01 <= drive[2] <= R.Z_GAR_OUT + 0.01 else R.Z_GAR_OUT
    RV._reshape(slab, sb[0], sb[1], g - GS.SLAB_T, g, sb[4], z_end)
    out['slab'] = {'was y': _r(sb[2:4]), 'now': _r(RV.bbox(slab))}
    out['driveway'] = {'starts z': round(drive[2], 3) if drive else None,
                       'top at the garage': round(top0, 3) if top0 is not None else None,
                       'meets the slab': top0 is not None and abs(top0 - g) < 0.002}
    fnd = _boxes(r'^\d+ Foundation$', pick=lambda b: b[0] > GS.GX0 - 0.5 and b[4] > GS.GZ0 - 0.5)
    for ob in fnd:
        fb = RV.bbox(ob)
        RV._reshape(ob, fb[0], fb[1], g - GS.SLAB_T - (fb[3] - fb[2]), g - GS.SLAB_T, fb[4], fb[5])
    out['foundation lowered'] = len(fnd)

    # ---- bases under the four walls
    src = _one(r'^\d+ Garage interior access — south wall$')
    t = R.WALL / 2
    sd, vr = GS.SIDE_DOOR['ro'], GS.VEHICLE_RO_X
    bases = [('west', GS.GX0 - t, GS.GX0, GS.GZ0 - t, GS.GZ1 + t),
             ('north', GS.GX0, GS.GX1, GS.GZ0 - t, GS.GZ0),
             ('east, north of the side door', GS.GX1, GS.GX1 + t, GS.GZ0 - t, sd[0]),
             ('east, south of the side door', GS.GX1, GS.GX1 + t, sd[1], GS.GZ1 + t),
             ('front, west of the vehicle door', GS.GX0, vr[0], GS.GZ1, GS.GZ1 + t),
             ('front, east of the vehicle door', vr[1], GS.GX1, GS.GZ1, GS.GZ1 + t)]
    for name, x0, x1, z0, z1 in bases:
        RV._paint_all(RV._like(src, f'Garage wall base — {name}', x0, x1, g, 0.0, z0, z1))
    out['bases'] = len(bases)

    # ---- baseboards on the garage's faces
    st = GS.STEP
    runs = [o for o in _boxes(r'^\d+ Painted skirting — ')
            if (lambda b: GS.GX0 - 0.08 < (b[0] + b[1]) / 2 < GS.GX1 + 0.08
                and GS.GZ0 - 0.08 < (b[4] + b[5]) / 2 < GS.GZ1 + 0.08)(RV.bbox(o))]
    sk = {}
    for ob in runs:
        b = RV.bbox(ob)
        ob.location.z += (g - b[2]) * FT
        bpy.context.view_layer.update()
        b = RV.bbox(ob)
        key = _plain(ob.name)[19:]
        if abs((b[0] + b[1]) / 2 - GS.GX0) < 0.1:                   # west wall: its two runs end at the step
            if (b[4] + b[5]) / 2 < (st[2] + st[3]) / 2:
                RV.move_face(ob, 'z', b[5], st[2])
            else:
                RV.move_face(ob, 'z', b[4], st[3])
        elif abs((b[0] + b[1]) / 2 - GS.GX1) < 0.1 and b[4] < sd[0] and b[5] > sd[1]:   # east wall: split at the side door
            RV._like(ob, f'Painted skirting — Garage — east side (south of the side door)', b[0], b[1], b[2], b[3],
                     sd[1], b[5])
            RV.move_face(ob, 'z', b[5], sd[0])
        sk[key] = _r(RV.bbox(ob))
    out['baseboards'] = sk

    # ---- the step at the house door
    step = RV._like(slab, 'Garage step at the house door', st[0] - 0.005, st[1], g - 0.01, GS.STEP_Y, st[2], st[3])
    ctx.add_bevel(step, 0.02, 3)
    # an aluminium nosing with a black grit strip along its front edge: the step is the slab's own concrete, and
    # without it its edge does not read from the doorway above
    alu = _mat('step_nosing', '#8e9092', rough=0.42, metal=0.9)
    grit = _mat('step_grit', '#1b1b1b', rough=0.95)
    ny = GS.STEP_Y
    ctx.box('Garage step nosing', st[1] - 0.15, st[1] + 0.008, ny - 0.002, ny + 0.01, st[2] + 0.03, st[3] - 0.03, alu, COLL_SHELL,
            0.003, 2)
    ctx.box('Garage step nosing front', st[1] - 0.002, st[1] + 0.008, ny - 0.11, ny + 0.004, st[2] + 0.03, st[3] - 0.03, alu,
            COLL_SHELL, 0.003, 2)
    ctx.box('Garage step nosing grit', st[1] - 0.115, st[1] - 0.03, ny + 0.01, ny + 0.013, st[2] + 0.05, st[3] - 0.05, grit,
            COLL_SHELL)
    out['step'] = {'box': _r(st), 'top y': round(GS.STEP_Y, 4),
                   'risers in': [round((GS.STEP_Y - g) * 12, 2), round(-GS.STEP_Y * 12, 2)]}

    # ---- the side door's sill: the slab ends on the east wall's centre line
    sill = RV._like(slab, 'Garage side door sill', RV.bbox(slab)[1] - 0.01, R.XE_OUT + 0.03, g - GS.SLAB_T, g, sd[0], sd[1])
    out['side door sill'] = _r(RV.bbox(sill))
    bpy.context.view_layer.update()
    out['cut away'] = _pit(ctx, z_end)
    out['floor y'] = round(g, 4)
    return out


# ---------------------------------------------------------------------------- the door between house and garage
def house_door(ctx):
    """DR17: 3'-0" door, 3'-4" between the wall's ends, hinged on the NORTH jamb, swinging east into the garage and
    shown open at 90 degrees as the sheet draws it. (Until the seventh round the opening stood 11 in further
    south, 3'-2 3/8" wide, with a 21 in leaf hinged on its south jamb.) Solid white leaf on three spring hinges
    (the door to a garage closes by itself), a lever on each face, oak threshold over the wall base; the step is
    floor()'s. The light switches of both rooms and the opener button move to the latch side, south of the door."""
    RV = _rv()
    from .zones import hall_entry_garage_lib as HL
    d = GS.HOUSE_DOOR
    r0, r1 = d['ro']
    out = {}
    north = _one(r'^\d+ Garage interior access — north infill wall$')
    south = _one(r'^\d+ Garage interior access — south wall$')
    hdr = _one(r'^\d+ Garage interior access — header$')
    nb, sb, hb = RV.bbox(north), RV.bbox(south), RV.bbox(hdr)
    if max(abs(nb[0] - d['wall'][0]), abs(nb[1] - d['wall'][1])) > 0.01:
        raise RuntimeError(f'the wall is not where the sheet has it: x {_r(nb[:2])}')
    out['opening z'] = {'was': _r((nb[5], sb[4])), 'now': _r((r0, r1))}
    RV.move_face(north, 'z', nb[5], r0)
    RV.move_face(south, 'z', sb[4], r1)
    RV._reshape(hdr, hb[0], hb[1], d['head'], hb[3], r0, r1)
    out['removed'] = RV.remove(RV.find(r'^\d+ Garage interior access — (north jamb|south jamb|head casing|threshold|'
                                       r'solid door|lever)', COLL_OPEN))
    # the foyer's baseboards on this wall end at the frame (the garage's: floor())
    sk = {}
    for ob in _boxes(r'^\d+ Painted skirting — Garage interior access — '):
        b = RV.bbox(ob)
        if (b[0] + b[1]) / 2 > GS.GX0 - 0.08:
            continue
        if b[4] < r0 and b[5] < r1:
            RV.move_face(ob, 'z', b[5], r0 - 0.01)
        elif b[5] > r1 and b[4] > r0 - 2.0:
            RV.move_face(ob, 'z', b[4], r1 + 0.01)
        sk[_plain(ob.name)[19:]] = _r(RV.bbox(ob)[4:6])
    out['foyer baseboards z'] = sk
    out['frame'] = _frame(ctx, d, 'House / garage door', 'paint_trim', 'N', 'S')
    p = GS.FRAME_PROUD
    th = _bx(ctx, 'House / garage door threshold', d, d['clear'][0], d['clear'][1], -0.005, 0.045, d['wall'][0] - p - 0.01,
             d['wall'][1] + p + 0.012, 'white_oak_veneer', bevel=0.006)
    th['tg_grain'] = 1                                   # v7 repair: the oak's grain runs along the board (it lies along z)
    out.update(_leaf(ctx, d, 'House / garage door', 'door_slab', spring=True))

    # ---- switches: on the latch side (south), 0.42 ft from the opening; the foyer's and the garage's
    RV.remove([o for o in bpy.data.objects if re.match(r'switch (plate|rocker) (garage door hall|garage lights)', o.name)
               or re.match(r'opener button', o.name)])
    E = HL.EAST_FACING_WEST(d['wall'][0])                # foyer face, u = +z
    GW = HL.WEST_FACING_EAST(d['wall'][1])               # garage face, u = -z
    us = r1 + 0.42
    M = _switch(ctx, E, 'garage door hall', us, 4.0, 1, C_ENTRY)
    _switch(ctx, GW, 'garage lights', -us, 4.0, 2, C_GAR)
    ub = -(r1 + 0.95)
    GW.box(ctx, 'opener button', ub - 0.11, ub + 0.11, 3.85, 4.2, 0.0, 0.05, M['plastic_w'], C_GAR, 0.015, 2)
    GW.box(ctx, 'opener button key', ub - 0.07, ub + 0.07, 3.9, 4.06, 0.05, 0.065, M['plastic_w'], C_GAR, 0.01, 2)
    out['switches z'] = round(us, 3)
    return out


# ------------------------------------------------------------------------------------------ garage side door
def side_door(ctx):
    """DR18: the garage's side door in the east wall, 2'-8" between the wall's ends, 2'-4" leaf, hinged on the south
    jamb and swinging into the garage; it stands on the garage floor (head 6'-8" above it). Shown closed: a solid
    white exterior leaf, lever and deadbolt, the frame standing proud of the inside face and of the stucco, an
    aluminium threshold on the concrete sill."""
    RV = _rv()
    d = GS.SIDE_DOOR
    r0, r1 = d['ro']
    wall = _one(r'^\d+ Garage — east side$')
    wb = RV.bbox(wall)
    if max(abs(wb[0] - d['wall'][0]), abs(wb[1] - d['wall'][1])) > 0.01 or wb[4] > r0 - 0.5 or wb[5] < r1 + 0.5:
        raise RuntimeError(f'the east wall is not where the sheet has it: {_r(wb)}')
    nm = _plain(wall.name)
    RV._like(wall, f'{nm} (north of the side door)', wb[0], wb[1], wb[2], wb[3], wb[4], r0)
    RV._like(wall, f'{nm} (over the side door)', wb[0], wb[1], d['head'], wb[3], r0, r1)
    RV.move_face(wall, 'z', wb[4], r1)
    out = {'opening z': _r((r0, r1)), 'sill y': round(d['floor_y'], 4), 'head y': round(d['head'], 4)}
    out['frame'] = _frame(ctx, d, 'Garage side door', 'paint_trim', 'N', 'S')
    p = GS.FRAME_PROUD
    g = d['floor_y']
    _bx(ctx, 'Garage side door threshold', d, d['clear'][0], d['clear'][1], g - 0.003, g + 0.045, d['wall'][0] - p - 0.01,
        d['wall'][1] + p + 0.02, 'stainless', bevel=0.008)
    out.update(_leaf(ctx, d, 'Garage side door', 'door_slab', deadbolt=True))
    # v7 repair: a door sweep under the leaf. The leaf's bottom stands 0.02 ft (1/4 in) above the threshold: closed,
    # a slit of daylight 2.3 ft long showed under the door from inside the garage (review E2). The black sweep hangs
    # from inside the leaf's bottom edge into the threshold's top, 0.02 ft back from both faces of the leaf.
    lf = GS.leaf(d)
    y0, y1 = g + 0.045 - 0.004, lf['aabb'][2] + 0.012
    ctx.box_c('Garage side door sweep', (lf['center'][0], (y0 + y1) / 2, lf['center'][2]),
              (lf['size'][0] - 0.004, y1 - y0, lf['size'][2] - 0.04), lf['rot'], 'paint_black', COLL_OPEN)
    out['sweep y'] = _r((y0, y1))
    return out


# ------------------------------------------------------------------------------------------------ front door
def front_door(ctx):
    """DR16: the front door unit. A 3'-0" walnut leaf centred on the foyer, hinged on the east post and open into
    the foyer, between two glazed sidelights; the unit takes the foyer's width less 3 in of wall each side
    (GS.FRONT_DOOR_UNIT). White frame (1 in outer jambs, 2 in posts, head), an oak sill under the whole unit, a
    bottom rail and clear glass in each sidelight; bl/revisions.white_windows, which runs last, finds the two panes
    and gives them their grid bars like every window of the house. The wall above the unit runs across its whole
    width under the entry window W17, which keeps its place and size. The door's switch moves to the foyer's west
    wall (latch side); the porch sconce is moved by bl/zones/exterior_garage.py."""
    RV = _rv()
    from .zones import hall_entry_garage_lib as HL
    d = GS.FRONT_DOOR
    u0, u1 = GS.FRONT_DOOR_UNIT
    head, sill_y, top_y = GS.FRONT_DOOR_BAND_Y
    out = {}
    for label, pre, coll in (('wall', r'^\d+ ', COLL_SHELL), ('stucco', r'^\d+ Front stucco · ', COLL_EXT)):
        west = _one(pre + r'Centered front entrance — west wall$', coll)
        east = _one(pre + r'Centered front entrance — east wall$', coll)
        band = _one(pre + r'Entry transom structural band$', coll)
        wb, eb, bb = RV.bbox(west), RV.bbox(east), RV.bbox(band)
        o0, o1 = wb[1], eb[0]                                # the old door's opening = the entry window's above
        if max(abs(o0 - GS.FRONT_DOOR_OLD_X[0]), abs(o1 - GS.FRONT_DOOR_OLD_X[1]), abs(bb[3] - sill_y)) > 0.02:
            raise RuntimeError(f'{label}: the door wall is not where the spec expects it: {_r((o0, o1, bb[3]))}')
        RV.move_face(west, 'x', o0, u0)
        RV.move_face(east, 'x', o1, u1)
        RV._reshape(band, u0, u1, head, bb[3], bb[4], bb[5])
        nm = _plain(band.name)
        RV._like(band, f'{nm} (west of the entry window)', u0, o0, bb[3], top_y, bb[4], bb[5])
        RV._like(band, f'{nm} (east of the entry window)', o1, u1, bb[3], top_y, bb[4], bb[5])
        out[label] = {'opening x': {'was': _r((o0, o1)), 'now': _r((u0, u1))}, 'z': _r(bb[4:6])}
    out['removed'] = RV.remove(RV.find(r'^\d+ Centered front entrance — ', COLL_OPEN))
    for ob in _boxes(r'^\d+ Painted skirting — Centered front entrance — '):
        b = RV.bbox(ob)
        if (b[0] + b[1]) / 2 < (u0 + u1) / 2:
            RV.move_face(ob, 'x', b[1], u0 - 0.01)
        else:
            RV.move_face(ob, 'x', b[0], u1 + 0.01)

    # ---- the unit: sill, outer jambs, posts, head, stops
    w0, w1 = d['wall']
    p = GS.FRAME_PROUD
    white = 'window_white'
    foot = GS.FRONT_DOOR_SILL_Y
    top = d['head'] - GS.HEAD_TRIM[0]
    sl = _bx(ctx, 'Front door sill', d, u0, u1, -0.005, foot, w0 - p - 0.03, w1 + p + 0.03, 'white_oak_veneer', bevel=0.008)
    j = GS.FRONT_DOOR_JAMB
    _bx(ctx, 'Front door jamb W', d, u0 - 0.01, u0 + j, foot, top, w0 - p, w1 + p, white, bevel=0.004)
    _bx(ctx, 'Front door jamb E', d, u1 - j, u1 + 0.01, foot, top, w0 - p, w1 + p, white, bevel=0.004)
    out['frame'] = _frame(ctx, d, 'Front door', white, 'W', 'E', foot=foot, along=(u0 - 0.01, u1 + 0.01))
    # ---- sidelights: bottom rail and glass between the outer jamb and the post
    c = d['c']
    lights = {}
    for tag, (a0, a1) in zip('WE', GS.FRONT_DOOR_SIDELIGHTS):
        _bx(ctx, f'Front door sidelight {tag} bottom rail', d, a0, a1, foot, GS.FRONT_DOOR_SIDELIGHT_RAIL_Y, c - 0.073, c + 0.073,
            white, bevel=0.004)
        gl = _bx(ctx, f'D01 sidelight {tag} glass', d, a0 - 0.02, a1 + 0.02, GS.FRONT_DOOR_SIDELIGHT_RAIL_Y - 0.02, top + 0.02,
                 c - 0.02, c + 0.02, 'glass_clear')
        gl.visible_shadow = True
        lights[tag] = {'x': _r((a0, a1)), 'width in': round((a1 - a0) * 12, 2),
                       'glass y': _r((GS.FRONT_DOOR_SIDELIGHT_RAIL_Y, top))}
    out['sidelights'] = lights
    bpy.context.view_layer.update()
    out['sill'] = _r(RV.bbox(sl))
    out.update(_leaf(ctx, d, 'Front door', 'walnut_door', deadbolt=True))

    # ---- the door's switch: off the door wall (no wall is left beside the unit) onto the foyer's west wall
    RV.remove([o for o in bpy.data.objects if re.match(r'switch (plate|rocker) front door', o.name)])
    W = HL.WEST_FACING_EAST(GS.FX0)                          # u = -z
    zs = GS.FZ1 - 0.62
    _switch(ctx, W, 'front door', -zs, 4.0, 2, C_ENTRY)
    out['switch'] = {'wall x': round(GS.FX0, 3), 'z': round(zs, 3)}
    return out


# ---------------------------------------------------------------------------------------------- water heater
def _arc_patch(ctx, name, cx, cz, r, a0, a1, y0, y1, mat, coll, seg=10, thick=0.004):
    """A label or a plate lying on a cylinder's surface: angles in degrees on the plan, 0 = +x, 90 = +z."""
    verts, faces = [], []
    for k in range(seg + 1):
        a = math.radians(a0 + (a1 - a0) * k / seg)
        for rr in (r, r + thick):
            for y in (y0, y1):
                verts.append(tuple(ft2bl(cx + rr * math.cos(a), y, cz + rr * math.sin(a))))
    for k in range(seg):
        b, n = 4 * k, 4 * (k + 1)
        faces += [(b + 2, n + 2, n + 3, b + 3), (b, b + 1, n + 1, n), (b + 1, b + 3, n + 3, n + 1), (b, n, n + 2, b + 2)]
    faces += [(0, 2, 3, 1), (4 * seg, 4 * seg + 1, 4 * seg + 3, 4 * seg + 2)]
    ob = ctx.mesh_object(name, verts, faces, mat, coll)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.shade_smooth()
    try:
        ob.data.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    return ob


def water_heater(ctx):
    """FX11: the sheet draws a 1'-8" circle in the garage's north-east corner. A 50 gallon gas water heater: white
    enamelled jacket 4'-9" tall on an 18 in steel stand (a burner in a garage stands 18 in above the floor), drip
    pan, draft hood and 4 in flue to the ceiling, cold and hot copper lines from the top into the north wall with
    a shut-off on the cold side, relief valve with its discharge pipe, gas control with its supply from the east
    wall, drain valve, labels, and two seismic straps round the tank anchored to the north wall. (Until the
    seventh round a wall-hung tankless unit hung on the west wall; bl/zones/hall_entry_garage.py no longer
    builds it.)"""
    from .zones import hall_entry_garage_lib as HL
    ctx.coll(C_GAR, ZONE)
    cx, cz = GS.WATER_HEATER_C
    r = GS.WATER_HEATER_D / 2
    g = GS.FLOOR_Y
    ys = g + GS.WATER_HEATER_STAND                         # top of the stand
    H = GS.WATER_HEATER_TANK
    yt = ys + 0.03 + H                                     # top of the tank (it stands in the pan, on 3/8 in feet)
    hs = GS.WATER_HEATER_STAND_HALF
    enamel = _mat('wh_enamel', '#e8e8e4', rough=0.32, coat=0.35)
    rim = _mat('wh_rim', '#7d8084', rough=0.4, metal=0.6)
    galv = _mat('conduit', '#a9abab', rough=0.35, metal=0.9)
    steel = _mat('steel_powder', '#55585b', rough=0.45, metal=0.6)
    copper = _mat('copper', '#b87352', rough=0.3, metal=1.0)
    brass = _mat('wh_brass', '#b5a268', rough=0.35, metal=1.0)
    dark = _mat('plastic_dark', '#3a3c3e', rough=0.45)
    red = _mat('wh_red', '#b3261e', rough=0.4)
    yellow = _mat('wh_gas_yellow', '#d9b21c', rough=0.45)
    label = _mat('wh_label', '#f2e9a8', rough=0.6)
    plate = _mat('wh_plate', '#d9d9d6', rough=0.5)
    iron = _mat('wh_black_iron', '#2b2c2e', rough=0.55, metal=0.7)
    kit = _kit(ctx, C_GAR, ZONE)
    n = 'water heater'

    # ---- stand: steel top, four legs, rails
    ctx.box(f'{n} stand top', cx - hs, cx + hs, ys - 0.06, ys, cz - hs, cz + hs, steel, C_GAR, 0.012, 2)
    lg = 0.12
    for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x0, z0 = cx + sx * (hs - 0.03), cz + sz * (hs - 0.03)
        ctx.box(f'{n} stand leg {i}', min(x0, x0 - sx * lg), max(x0, x0 - sx * lg), g, ys - 0.06,
                min(z0, z0 - sz * lg), max(z0, z0 - sz * lg), steel, C_GAR, 0.008, 2)
        ctx.box(f'{n} stand foot {i}', min(x0 + sx * 0.02, x0 - sx * (lg + 0.02)), max(x0 + sx * 0.02, x0 - sx * (lg + 0.02)),
                g, g + 0.02, min(z0 + sz * 0.02, z0 - sz * (lg + 0.02)), max(z0 + sz * 0.02, z0 - sz * (lg + 0.02)),
                steel, C_GAR)
    a, b = hs - 0.03 - lg, hs - 0.03
    for i, (x0, x1, z0, z1) in enumerate(((cx - a, cx + a, cz - b + 0.02, cz - b + 0.06), (cx - a, cx + a, cz + b - 0.06, cz + b - 0.02),
                                         (cx - b + 0.02, cx - b + 0.06, cz - a, cz + a), (cx + b - 0.06, cx + b - 0.02, cz - a, cz + a))):
        ctx.box(f'{n} stand rail {i}', x0, x1, g + 0.3, g + 0.42, z0, z1, steel, C_GAR)
        ctx.box(f'{n} stand apron {i}', x0, x1, ys - 0.2, ys - 0.06, z0, z1, steel, C_GAR)

    # ---- drip pan, tank
    pan = HL.lathe(ctx, f'{n} drip pan', [(r + 0.085, 0.0), (r + 0.1, 0.012), (r + 0.1, 0.14), (r + 0.088, 0.14), (r + 0.088, 0.022),
                                          (0.02, 0.022)], C_GAR, [galv], seg=72, smooth_profile=False)
    pan.location = ft2bl(cx, ys, cz)
    tank = HL.lathe(ctx, f'{n} tank', [(r - 0.03, 0.0), (r, 0.03), (r, H - 0.07), (r - 0.012, H - 0.025), (r - 0.05, H - 0.004),
                                       (r - 0.12, H), (0.03, H)], C_GAR, [enamel], seg=96, smooth_profile=False)
    tank.location = ft2bl(cx, ys + 0.03, cz)
    for k, (y0, y1) in enumerate(((ys + 0.03, ys + 0.11), (yt - 0.15, yt - 0.075))):
        band = HL.ring_mesh(ctx, f'{n} jacket band {k}', r + 0.002, 0.006, y1 - y0, C_GAR, [rim], seg=96, inner_mat=0, bottom_mat=0)
        band.location = ft2bl(cx, (y0 + y1) / 2, cz)

    # ---- draft hood and flue
    for k in range(3):
        an = math.radians(90 + 120 * k)
        px, pz = cx + 0.2 * math.cos(an), cz + 0.2 * math.sin(an)
        kit.cyl(f'{n} draft hood leg {k}', (px, yt - 0.01, pz), (px, yt + 0.13, pz), 0.012, galv, 12)
    hood = HL.lathe(ctx, f'{n} draft hood', [(0.3, 0.0), (0.31, 0.012), (0.19, 0.2), (0.167, 0.22), (0.167, 0.34), (0.16, 0.34),
                                             (0.16, 0.215), (0.29, 0.012)], C_GAR, [galv], seg=64, cap_bottom=False,
                    smooth_profile=False)
    hood.location = ft2bl(cx, yt + 0.12, cz)
    yf0 = yt + 0.12 + 0.3
    ctx.cylinder(f'{n} flue', (cx, (yf0 + GS.CEILING_Y) / 2, cz), 0.167, GS.CEILING_Y - yf0, galv, C_GAR, verts=48)
    for k, yb in enumerate((yf0 + 0.05, (yf0 + GS.CEILING_Y) / 2 + 0.2)):
        ctx.cylinder(f'{n} flue joint {k}', (cx, yb, cz), 0.173, 0.05, galv, C_GAR, verts=48)
    ctx.cylinder(f'{n} flue ceiling collar', (cx, GS.CEILING_Y - 0.012, cz), 0.3, 0.024, galv, C_GAR, verts=48)

    # ---- cold and hot lines: up from the top, back into the north wall
    zw = GS.GZ0
    yl = yt + 0.95
    for tag, dx, m in (('hot', -0.33, copper), ('cold', 0.33, copper)):
        x, z = cx + dx, cz - 0.24
        kit.cyl(f'{n} {tag} nipple', (x, yt - 0.01, z), (x, yt + 0.09, z), 0.05, galv, 20)
        kit.cyl(f'{n} {tag} nut', (x, yt + 0.09, z), (x, yt + 0.15, z), 0.058, brass, 6)
        kit.cyl(f'{n} {tag} riser', (x, yt + 0.15, z), (x, yl, z), 0.036, m, 20)
        kit.cyl(f'{n} {tag} elbow', (x, yl - 0.045, z), (x, yl + 0.045, z), 0.045, m, 20)
        kit.cyl(f'{n} {tag} run', (x, yl, z + 0.03), (x, yl, zw + 0.005), 0.036, m, 20)
        kit.cyl(f'{n} {tag} escutcheon', (x, yl, zw + 0.001), (x, yl, zw + 0.02), 0.1, 'chrome', 32)
    xv, zv, yv = cx + 0.33, cz - 0.24, yt + 0.5              # shut-off on the cold riser
    kit.cyl(f'{n} cold valve body', (xv, yv - 0.07, zv), (xv, yv + 0.07, zv), 0.062, brass, 20)
    kit.cyl(f'{n} cold valve stem', (xv, yv, zv), (xv, yv, zv + 0.1), 0.022, brass, 12)
    ctx.box(f'{n} cold valve handle', xv - 0.03, xv + 0.03, yv - 0.02, yv + 0.3, zv + 0.1, zv + 0.125, red, C_GAR, 0.008, 2)

    # ---- relief valve and its discharge pipe, on the west side (toward the room)
    yr = yt - 0.55
    xr = cx - r
    kit.cyl(f'{n} relief valve', (xr + 0.02, yr, cz + 0.2), (xr - 0.13, yr, cz + 0.2), 0.05, brass, 16)
    ctx.box(f'{n} relief valve lever', xr - 0.14, xr - 0.02, yr + 0.05, yr + 0.07, cz + 0.17, cz + 0.23, steel, C_GAR, 0.004, 2)
    kit.cyl(f'{n} relief elbow', (xr - 0.11, yr - 0.045, cz + 0.2), (xr - 0.11, yr + 0.045, cz + 0.2), 0.04, copper, 16)
    kit.cyl(f'{n} relief discharge', (xr - 0.11, yr - 0.02, cz + 0.2), (xr - 0.11, g + 0.5, cz + 0.2), 0.03, copper, 16)

    # ---- gas control, burner door, supply line from the east wall, drain valve (south face, toward the room)
    yc = ys + 0.03 + 0.62
    _arc_patch(ctx, f'{n} burner door', cx, cz, r + 0.001, 68, 112, ys + 0.14, ys + 0.47, plate, C_GAR, thick=0.012)
    ctx.box(f'{n} gas control', cx - 0.17, cx + 0.17, yc, yc + 0.33, cz + r - 0.02, cz + r + 0.2, dark, C_GAR, 0.02, 3)
    kit.cyl(f'{n} gas control knob', (cx - 0.02, yc + 0.33, cz + r + 0.1), (cx - 0.02, yc + 0.39, cz + r + 0.1), 0.085, red, 32)
    kit.cyl(f'{n} gas control dial', (cx + 0.09, yc + 0.17, cz + r + 0.2), (cx + 0.09, yc + 0.17, cz + r + 0.225), 0.05, plate, 24)
    xg = GS.GX1                                              # the east wall's face
    yg = yc + 0.16
    kit.cyl(f'{n} gas flex', (cx + 0.17, yg, cz + r + 0.09), (cx + 0.72, yg, cz + r + 0.09), 0.026, yellow, 16)
    kit.cyl(f'{n} gas flex nut', (cx + 0.17, yg, cz + r + 0.09), (cx + 0.23, yg, cz + r + 0.09), 0.036, brass, 6)
    kit.cyl(f'{n} gas valve', (cx + 0.72, yg, cz + r + 0.09), (cx + 0.86, yg, cz + r + 0.09), 0.04, brass, 16)
    ctx.box(f'{n} gas valve handle', cx + 0.74, cx + 0.96, yg + 0.04, yg + 0.065, cz + r + 0.07, cz + r + 0.11, yellow, C_GAR,
            0.006, 2)
    kit.cyl(f'{n} gas pipe', (cx + 0.86, yg, cz + r + 0.09), (xg - 0.005, yg, cz + r + 0.09), 0.03, iron, 16)
    kit.cyl(f'{n} gas tee', (cx + 1.0, yg - 0.05, cz + r + 0.09), (cx + 1.0, yg + 0.05, cz + r + 0.09), 0.04, iron, 16)
    kit.cyl(f'{n} gas drip leg', (cx + 1.0, yg - 0.05, cz + r + 0.09), (cx + 1.0, yg - 0.4, cz + r + 0.09), 0.03, iron, 16)
    kit.cyl(f'{n} gas drip cap', (cx + 1.0, yg - 0.4, cz + r + 0.09), (cx + 1.0, yg - 0.45, cz + r + 0.09), 0.04, iron, 16)
    kit.cyl(f'{n} gas escutcheon', (xg - 0.02, yg, cz + r + 0.09), (xg - 0.001, yg, cz + r + 0.09), 0.08, iron, 24)
    ad = math.radians(128)
    dxn, dzn = math.cos(ad), math.sin(ad)
    kit.cyl(f'{n} drain valve', (cx + (r - 0.02) * dxn, ys + 0.28, cz + (r - 0.02) * dzn),
            (cx + (r + 0.14) * dxn, ys + 0.28, cz + (r + 0.14) * dzn), 0.035, brass, 16)
    kit.cyl(f'{n} drain valve cap', (cx + (r + 0.14) * dxn, ys + 0.28, cz + (r + 0.14) * dzn),
            (cx + (r + 0.17) * dxn, ys + 0.28, cz + (r + 0.17) * dzn), 0.045, dark, 16)

    # ---- labels on the jacket
    _arc_patch(ctx, f'{n} energy label', cx, cz, r + 0.001, 122, 150, ys + 2.2, ys + 3.1, label, C_GAR, thick=0.002)
    _arc_patch(ctx, f'{n} rating plate', cx, cz, r + 0.001, 74, 106, ys + 1.5, ys + 2.3, plate, C_GAR, thick=0.002)
    _arc_patch(ctx, f'{n} warning label', cx, cz, r + 0.001, 80, 100, ys + 3.0, ys + 3.6, plate, C_GAR, thick=0.002)

    # ---- seismic straps: a band round the tank in its upper and its lower third, both ends to the north wall
    sw = 0.125
    for k, ysr in enumerate((ys + 0.03 + H / 3, ys + 0.03 + 2 * H / 3)):
        band = HL.ring_mesh(ctx, f'{n} strap {k}', r + 0.006, 0.008, sw, C_GAR, [galv], seg=96, inner_mat=0, bottom_mat=0)
        band.location = ft2bl(cx, ysr, cz)
        for j, sx in enumerate((-1, 1)):
            xs = cx + sx * (r + 0.006)
            ctx.box(f'{n} strap {k} tail {j}', xs - 0.004, xs + 0.004, ysr - sw / 2, ysr + sw / 2, zw + 0.012, cz, galv, C_GAR)
            ctx.box(f'{n} strap {k} anchor {j}', xs - 0.09, xs + 0.09, ysr - 0.11, ysr + 0.11, zw, zw + 0.012, galv, C_GAR, 0.004, 2)
            kit.cyl(f'{n} strap {k} bolt {j}', (xs + sx * 0.05, ysr, zw + 0.012), (xs + sx * 0.05, ysr, zw + 0.04), 0.026, steel, 6)
        ctx.box(f'{n} strap {k} tensioner', cx - 0.09, cx + 0.09, ysr - 0.05, ysr + 0.05, cz + r + 0.008, cz + r + 0.04, galv,
                C_GAR, 0.006, 2)
    return {'centre': _r((cx, cz)), 'diameter': round(2 * r, 4), 'stand top y': round(ys, 3), 'tank top y': round(yt, 3),
            'above the garage floor': round(yt - g, 3), 'flue to y': GS.CEILING_Y,
            'clear of east / north wall': _r((GS.GX1 - cx - r, cz - r - GS.GZ0))}


STEPS = (vehicle_opening, floor, house_door, side_door, front_door, water_heater)


def apply(ctx):
    out = {}
    for f in STEPS:
        try:
            out[f.__name__] = f(ctx)
        except Exception as e:                           # report, keep building
            traceback.print_exc()
            out[f.__name__] = f'FAILED: {e!r}'
        bpy.context.view_layer.update()
    return out
