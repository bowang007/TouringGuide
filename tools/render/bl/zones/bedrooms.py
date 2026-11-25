"""Bedrooms zone: Bedroom 2, Bedroom 3 (+ bay), Bedroom 4 and their closets (runs inside Blender).

Design (1077 W McKinley language, three cohesive but distinct rooms):
  * Bedroom 2  - queen bed with a cream boucle channel headboard against the solid east wall,
                 white-oak drawer nightstands with stoneware lamps, charcoal knit throw, oval
                 boucle bench, abstract charcoal/ochre diptych, ceiling-track linen drapes at the
                 garden window, leaning floor mirror, closet rebuilt with flush white bypass
                 sliders (one open onto white shelving + rail).
  * Bedroom 3  - the largest room, vaulted: low wrap-around grey linen bed on the west wall (a solid
                 wall with a wide canvas over the bed since the eighth round; the window W10 only
                 while revision_spec.BED3_WEST_WINDOW), cream lacquer nightstands, built-in
                 upholstered window seat in the canted
                 bay W09 with pillows and roller shades, white-oak desk + sculptural boucle barrel
                 chair, colour-field painting, LED ring pendant hung from the ridge, slope cans.
  * Bedroom 4  - compact (flat 8 ft ceiling, revisions.bedroom4_flat), L-shaped since the laundry closet
                 took its north-east corner (revisions.laundry_closet): white-oak full bed with a sage
                 linen pad turned across the room (headboard on the north wall, its side along the W12
                 window wall) so the room's length stays open, one compact oak nightstand, oak desk on
                 black steel sled legs with an oak/steel chair in the niche between the nightstand and the
                 closet's west wall, brush print above it, a slim line print on the closet wall and an oak
                 peg rail behind the door (bed4_closet_faces), opal globe pendant.
  * Closets    - Bedroom 3 closet (eighth round: a reach-in behind two sliding panels, fitted out after
                 the warp by bedrooms_rooms.py): white built-in (drawers, shelves, double hang with
                 real shirts / a jacket / folded trousers, see bedrooms_garments) + open shelf
                 tower + disk light; Bedroom 4 reach-in: shelf + rail.

Layout positions follow the original scene's anchors (beds, nightstands, desks, closet storage)
except Bedroom 2's bed, which moves from under the garden window to the solid east wall so the
window stays clear and the headboard gets art above it (classic listing composition).
"""
import math
import sys
import time

import bpy

from . import bedrooms_furniture as F
from . import bedrooms_kit as K
from .bedrooms_kit import Frame
from ..common import FT, RENDER_DIR
from ..revision_spec import BED3_WEST_WINDOW, LAUNDRY_CLEAR, LAUNDRY_WALL_T

if RENDER_DIR not in sys.path:
    sys.path.insert(0, RENDER_DIR)
import relayout as R  # noqa: E402  (the concept -> architect's plan maps that bl/warp.py applies to this zone)

PI = math.pi

# Interior light levels (Blender watts / emission strength). Daylight must dominate: the render
# pipeline white-balances for daylight (render_panos.WB_KELVIN), so warm sources read strongly
# orange and are kept low, lowest in the north/west rooms (B2, B4) that get little daylight.
LIGHTS = {
    'B2': dict(can=0.15, lamp=0.15, closet=0.25, lens=6.0, bulb=3.0),
    'B3': dict(slope=0.8, lamp=0.5, ring=3.5, bay=0.8, lens=6.0, bulb=3.0),
    'B4': dict(lamp=0.12, desk=0.1, slope=0.15, globe=0.9, globe_w=12.0, lens=6.0, bulb=3.0),
    'C3': dict(disk=4.0),
}
WEST, EAST, NORTH, SOUTH = PI / 2, -PI / 2, 0.0, PI     # yaw so local +z points away from that wall


def _anchor(ctx, room, name):
    """AABB [x0,x1,y0,y1,z0,z1] of the first original object in `room` whose name matches."""
    ids = ctx.find(room=room, role=('furniture', 'decor', 'fixture'), name=name)
    return ctx.aabb(ids[0]) if ids else None


# ================================================================================== Bedroom 2
def build_bed2(ctx, kit, M):
    kit.use('bed2')
    # original queen bed sat x 15.24-20.76 on the north wall; we keep its z-centre region and turn
    # it onto the solid east wall (x = 22.92).
    zc = 6.3
    wall = 22.92
    fb = Frame(wall - 0.06, zc, EAST)
    info = F.bed(kit, M, fb, 'B2 bed', 'channel', 5.0, 6.67, upholstery=M['boucle'], bedding=dict(
        duvet=M['linen_white'], throw=M['knit_charcoal'], throw_len=1.6,
        pillows=[('euro', M['linen_ivory'], 2, 80, 2.15, 2.15, 0.55),
                 ('std', M['linen_white'], 2, 64, 2.45, 1.6, 0.48),
                 ('accent', M['linen_charcoal'], 2, 66, 1.55, 1.55, 0.42),
                 ('lumbar', M['velvet_ochre'], 1, 58, 2.0, 1.0, 0.38)]))
    # nightstands + lamps
    for side, z in (('n', 2.4), ('s', 10.2)):
        fr = Frame(wall - 0.06, z, EAST)
        h = F.nightstand(kit, M, fr, f'B2 nightstand {side}', 'oak', 1.6, 1.95, 1.45)
        away = -1 if side == 'n' else 1          # local +x points south here
        F.table_lamp(kit, M, fr.sub(0.25 * away, 0.56, 0, h), f'B2 lamp {side}', 'stoneware', 1.0, LIGHTS['B2']['lamp'], LIGHTS['B2']['bulb'])
        if side == 'n':
            F.book_stack(kit, M, fr.sub(0.36, 0.98, 0.15, h), 'B2 books',
                         [(0.6, 0.82, 0.08, 'cover_sand'), (0.55, 0.78, 0.06, 'cover_charcoal')])
        else:
            F.bud_vase(kit, M, fr.sub(-0.4, 1.05, 0, h), 'B2 vase', 'stoneware_dark', 0.5, 3)
    # bench at the foot of the bed (clear of the camera at 14.3, 10.5)
    F.boucle_bench(kit, M, Frame(14.62, zc, EAST), 'B2 bench', 4.0, 1.3, 1.5)
    # rug under the lower two thirds of the bed and the bench
    # pale warm-grey heathered wool with a narrow tonal border (reads as an area rug, lighter than the bed)
    # (v7 repair: its south edge 0.12 ft further north, 10.13: the entry door's leaf, new this round, swept over the
    # rug's south-west corner with its bottom 3/8 in below the rug's top)
    F.rug(kit, 'B2 rug', 13.7, 21.25, 2.35, 10.13, K.rug_material(
        'Z_bedrooms_rug_heather_grey', ['#cbc7bf', '#d7d3cb', '#e2ded6'], 70.0, 'heather',
        border=(3.775, 3.95, '#b3ada2', ((0.22, 0.30),))))
    # diptych above the headboard
    art = K.art_brush(1100, 720, seed=3)
    half = art.shape[1] // 2
    fa = Frame(wall, zc, EAST)
    F.canvas_art(kit, fa.sub(-1.07, 0), 'B2 art left', 1.9, 2.45, art[:, :half], y_c=5.78)
    F.canvas_art(kit, fa.sub(1.07, 0), 'B2 art right', 1.9, 2.45, art[:, half:], y_c=5.78)
    # ceiling-track linen drapes either side of the garden window W02 (x 14.94-20.34)
    kit.wbox('B2 drape track', 13.4, 21.95, 7.9, 8.0, 0.43, 0.6, 'paint_trim', 0.01, 1)
    F.ripplefold(kit, M, 'B2 drape left', 13.5, 15.25, 0.53, seed=2)
    F.ripplefold(kit, M, 'B2 drape right', 20.1, 21.85, 0.53, seed=5)
    # leaning floor mirror on the west wall, north of the bench; snake plant in the NW corner
    _leaning_mirror(kit, 12.25, 2.95, 2.2, 6.1)
    F.snake_plant(kit, M, Frame(12.84, 0.86, 0.3), 'B2 plant', 'stoneware', 0.44, 1.15, 14, 3)
    # large print opposite the bed, above the bench
    F.framed_print(kit, Frame(12.25, 8.3, WEST), 'B2 print west', 2.1, 2.7, K.art_fields(
        600, 770, 17, [(0.06, 0.52, (0.36, 0.35, 0.33)), (0.55, 0.78, (0.78, 0.73, 0.65)), (0.81, 0.94, (0.73, 0.55, 0.30))]),
        0.32, 5.0)
    # recessed cans (4 in a grid)
    for x in (14.7, 19.6):
        for z in (3.3, 9.4):
            kit.can(x, z, watts=LIGHTS['B2']['can'], lens=LIGHTS['B2']['lens'])
    # v7 hall: the concept's entry alcove is hall and the closet is the sheet's 6'-10" x 1'-11" since the eighth
    # round. The closet's doors and fit-out (collection zone_bedrooms_bed2_closet, LIGHTS['B2']['closet']) are built
    # after the warp, in plan feet, by bl/zones/hall_block.py (bl/revisions.hall_block / hall_block_fit_out).
    return info


def _leaning_mirror(kit, wall_x, zc, w, h, lean_deg=6.0):
    fr_yaw = WEST
    a = math.radians(lean_deg)
    t = 0.09
    # origin: bottom-centre of the frame, pushed off the wall so the top touches it
    x = wall_x + 0.06 + h * math.sin(a) + t * math.cos(a) / 2
    v = []
    f = []
    fw = 0.09
    parts = [(-w / 2, -w / 2 + fw, 0, h), (w / 2 - fw, w / 2, 0, h), (-w / 2 + fw, w / 2 - fw, 0, fw), (-w / 2 + fw, w / 2 - fw, h - fw, h)]
    for (x0, x1, y0, y1) in parts:
        base = len(v)
        for (xx, yy, zz) in ((x0, y0, -t / 2), (x1, y0, -t / 2), (x1, y0, t / 2), (x0, y0, t / 2),
                             (x0, y1, -t / 2), (x1, y1, -t / 2), (x1, y1, t / 2), (x0, y1, t / 2)):
            v.append((xx, yy, zz))
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            f.append(tuple(base + i for i in q))
    fr = kit.mesh('B2 mirror frame', v, f, 'black_metal', (x, 0.01, zc), fr_yaw, -a)
    K.Kit.soften(fr, 0.012, 2, 0)
    gv = [(-w / 2 + fw, fw, 0.0), (w / 2 - fw, fw, 0.0), (w / 2 - fw, h - fw, 0.0), (-w / 2 + fw, h - fw, 0.0)]
    gl = kit.mesh('B2 mirror glass', gv, [(0, 1, 2, 3)], 'mirror', (x, 0.01, zc), fr_yaw, -a)
    return gl


def _basket(kit, M, fr, tag, w, h, d):
    F.storage_box(kit, M, fr, tag, w, h, d)


# ================================================================================== Bedroom 3
BAY = dict(x0=3.036, x1=11.036, z_line=56.057, wall=53.83)


def _bay_poly(offset, z_front):
    """Plan polygon of the bay interior offset `offset` ft inward from the bay facet centre lines,
    cut at z_front on the room side."""
    o = offset / math.sqrt(2)
    k_w = (3.036 + o) - (54.057 - o)           # x - z = k_w on the west facet line
    z_c = 56.057 - offset
    xa = z_front + k_w
    xb = z_c + k_w
    return [(xa, z_front), (xb, z_c), (14.072 - xb, z_c), (14.072 - xa, z_front)]


def build_bed3(ctx, kit, M):
    kit.use('bed3')
    wall_w = 0.225
    zc = 49.3
    fb = Frame(wall_w + 0.06, zc, WEST)
    info = F.bed(kit, M, fb, 'B3 bed', 'low_linen', 5.0, 6.67, upholstery=M['linen_grey'], bedding=dict(
        duvet=M['linen_white'], throw=M['knit_oat'], throw_len=1.7,
        # low headboard under the W10 sill (y 2.50): no euro shams; the standards lie back against
        # the headboard and the sage lumbar leans on them, every top below y 3.0
        pillows=[('std', M['linen_white'], 2, 34, 2.45, 1.6, 0.46),
                 ('lumbar', M['linen_sage'], 1, 52, 2.2, 1.05, 0.38)]))
    for side, z, w in (('n', 45.5, 1.4), ('s', 53.06, 1.34)):
        fr = Frame(wall_w + 0.06, z, WEST)
        h = F.nightstand(kit, M, fr, f'B3 nightstand {side}', 'lacquer', w, 1.78, 1.3)
        F.table_lamp(kit, M, fr.sub(0.0, 0.6, 0, h), f'B3 lamp {side}', 'stoneware', 0.92, LIGHTS['B3']['lamp'], LIGHTS['B3']['bulb'])
    F.rug(kit, 'B3 rug', 2.9, 10.6, 45.25, 53.35, K.rug_material(
        'Z_bedrooms_rug_lattice', ['#cdc3b1', '#e8e1d4', '#ece6da'], 3.2, 'lattice'))
    # desk + barrel chair on the east wall (original slim desk anchor x 12.1-13.9, z 47.4-50.6)
    a = _anchor(ctx, 'bed3', r'slim bedroom desk')
    dz = (a[4] + a[5]) / 2 + 0.6 if a else 49.6
    fd = Frame(13.892 - 0.05, dz, EAST)
    F.desk(kit, M, fd, 'B3 desk', 4.0, 1.75, 2.5, 'oak')
    F.barrel_chair(kit, M, Frame(11.35, dz + 0.1, WEST), 'B3 chair')
    F.book_stack(kit, M, fd.sub(-1.25, 1.05, 0.25, 2.5), 'B3 desk books',
                 [(0.85, 1.1, 0.09, 'cover_charcoal'), (0.75, 1.0, 0.07, 'cover_rust'), (0.8, 1.05, 0.06, 'cover_white')])
    F.bud_vase(kit, M, fd.sub(1.3, 1.0, 0, 2.5), 'B3 desk vase', 'stoneware', 0.62, 4, 7)
    # sansevieria in the south-east corner beside the bay
    F.snake_plant(kit, M, Frame(13.3, 53.22, 0.9), 'B3 plant', 'stoneware_dark', 0.42, 1.2, 13, 8)
    # colour-field painting above the desk
    F.canvas_art(kit, Frame(13.892, dz, EAST), 'B3 art desk', 3.0, 2.25, K.art_fields(900, 680, 7), y_c=4.85)
    # (no art on the short north wall between the bath's hinged door and the closet's sliding panels: the B3 lens
    # stands 1.7 ft from it)   (v7 final: comment, it said "between the pocket doors")
    # W10 roller shade (inside mount, partly lowered) + bay window seat & shades. v7 bedrooms: only while the west
    # window is there (revision_spec.BED3_WEST_WINDOW; the sheet has a solid wall, and then a picture hangs over the
    # bed: bl/zones/bedrooms_rooms.py, after the warp)
    if BED3_WEST_WINDOW:
        F.roller_shade(kit, M, Frame(0.225, 46.65, WEST), 'B3 W10 shade', 3.96, 7.0, 0.9)
    _bay_window_seat(ctx, kit, M)
    # lighting: LED ring pendant from the ridge + 4 slope cans + a can in the bay soffit
    kit.use('bed3_lights')
    F.ring_pendant(kit, M, 7.036, 48.75, 8.35, 'B3', 1.25, LIGHTS['B3']['ring'])
    for x in (3.3, 10.75):
        for z in (45.4, 51.7):
            F.slope_can(kit, x, z, LIGHTS['B3']['slope'], lens=LIGHTS['B3']['lens'])
    kit.can(7.036, 55.0, ceil=7.6, watts=LIGHTS['B3']['bay'], lens=LIGHTS['B3']['lens'])
    return info


def _bay_window_seat(ctx, kit, M):
    kit.use('bed3_bay')
    fr0 = Frame(0, 0, 0)
    # painted base (toe kick + body) and an oak top board under the projecting stone sills
    kit.prism('B3 seat toe kick', fr0, (0, 0, 0), _bay_poly(0.16, 53.97), 0.0, 0.3, 'paint_trim')
    kit.prism('B3 seat body', fr0, (0, 0, 0), _bay_poly(0.15, 53.86), 0.3, 0.86, 'paint_trim', bevel=0.01, seg=2)
    top = _bay_poly(0.15, 53.85)
    top = [(3.045, 53.80), (3.045, top[0][1])] + top[1:3] + [(11.027, top[3][1]), (11.027, 53.80)]
    kit.prism('B3 seat top', fr0, (0, 0, 0), top, 0.86, 0.935, 'white_oak_veneer', bevel=0.012, seg=2)
    # upholstered cushion clear of the sills (sill inner edge is 0.24 ft inside the facet lines)
    cush = _bay_poly(0.28, 53.83)
    kit.prism('B3 seat cushion', fr0, (0, 0, 0), cush, 0.935, 1.3, M['linen_oat'], bevel=0.1, seg=3, sub=1)
    # pillows leaning on the glass of the centre facet + a lumbar in the west corner
    yb = 1.3

    def seat_y(w, d, t, phi):
        # centre height that sinks the pillow's lowest point ~0.02 ft into the seat cushion
        return yb - 0.02 - min(p[1] for p in F.PillowStack.profile(w, d, t, phi, 0.07))
    for i, (x, mat, w) in enumerate(((6.15, M['linen_sage'], 1.55), (7.85, M['boucle'], 1.55))):
        phi = math.radians(68)
        d, t = w, 0.45
        ez = d * math.cos(phi) + t * math.sin(phi)
        ob = kit.pillow(f'B3 seat pillow {i}', Frame(x, 56.0 - ez / 2 + 0.02, PI), (0, seat_y(w, d, t, phi), 0), w, d, t,
                        mat, tilt=phi, lrot=0.05 * (1 if i else -1))
        F.settle([ob], yb, 0.025)
    # ochre lumbar angled into the west facet
    phi = math.radians(62)
    ob = kit.pillow('B3 seat lumbar', Frame(4.39, 54.70, 3 * PI / 4), (0, seat_y(1.7, 0.95, 0.38, phi), 0), 1.7, 0.95,
                    0.38, M['velvet_ochre'], tilt=phi)
    F.settle([ob], yb, 0.025)
    # folded knit throw + books at the east end of the seat
    kit.soft('B3 seat throw', Frame(9.38, 54.68, PI / 4), (0, yb + 0.07, 0), (1.3, 0.16, 0.95), M['knit_charcoal'], 0.07, 3, 1)
    F.book_stack(kit, M, Frame(9.43, 54.62, PI / 4 + 0.2, yb + 0.15), 'B3 seat books',
                 [(0.75, 0.98, 0.08, 'cover_sage'), (0.68, 0.9, 0.06, 'cover_sand')])
    # roller shades in the three bay facets, lowered ~10 in from the head
    F.roller_shade(kit, M, Frame(7.036, 56.057, SOUTH), 'B3 bay shade c', 3.36, 7.48, 0.75, 0.12)
    F.roller_shade(kit, M, Frame(4.036, 55.057, 3 * PI / 4), 'B3 bay shade w', 2.22, 7.48, 0.75, 0.12)
    F.roller_shade(kit, M, Frame(10.036, 55.057, -3 * PI / 4), 'B3 bay shade e', 2.22, 7.48, 0.75, 0.12)


def _bed3_closet(ctx, kit, M):
    """v7 bedrooms (eighth round): Bedroom 3's closet is a reach-in behind two sliding panels, as on the architect's
    sheet, 2'-3 1/2" deep. It is fitted out AFTER the warp, in plan feet, by bl/zones/bedrooms_rooms.py (called by
    bl/revisions.bedroom3_fit_out); here only its collection is made. (Until the seventh round a step-in closet was
    built here on the concept plan: its 2.60 ft deep wardrobe stood 0.3 ft in the wall after the conversion.)"""
    kit.use('bed3_closet')


def _shoes(kit, M, x, z, y):
    mat = K.principled('Z_bedrooms_leather_tan', '#9a6a3e', 0.45)
    mat2 = K.principled('Z_bedrooms_canvas_white', '#ecebe6', 0.8)
    for i, (dz, m) in enumerate(((-0.33, mat), (0.03, mat2))):
        for s in (-0.11, 0.11):
            kit.soft(f'C3 shoe {i}{s > 0}', Frame(x - 0.02, z + dz + s, PI / 2), (0, y + 0.13, 0), (0.33, 0.26, 0.9), m, 0.09, 3, 1)


# ================================================================================== Bedroom 4
# Owner's correction of 2026-11-20: the laundry closet (bl/revision_spec.py LAUNDRY_*, built by
# bl/revisions.laundry_closet after the warp) is carved out of this room's north-east corner. On the built plan
# its west wall's bedroom face is x 11.725 and its south wall's bedroom face z 32.142, so the room is an L: the
# full 14'-11" width south of z 32.142 (the door D04 and the reach-in closet), 11'-6" wide north of it (bed,
# nightstand and the desk niche). The desk group that stood in the corner moved into the niche.
B4_DESK_W = 3.5
B4_DESK_GAP = 0.05          # ft between the desk's east end and the closet's west wall (on the built plan)
B4_CHAIR_DX = 0.10          # the chair stands this far east of the desk's centre: its legs clear the rug's corner


def _concept(f, v):
    """Concept coordinate that the piecewise-linear relayout map `f` carries to the new-plan value v."""
    ps = f.pairs
    if v <= ps[0][1]:
        return ps[0][0] + (v - ps[0][1])
    if v >= ps[-1][1]:
        return ps[-1][0] + (v - ps[-1][1])
    for (a0, b0), (a1, b1) in zip(ps, ps[1:]):
        if b0 <= v <= b1:
            return a0 + (v - b0) / (b1 - b0) * (a1 - a0)


def _b4_desk_x():
    """Concept x of the desk's centre. bl/warp.py moves the desk group (desk, chair, lamp, books, plant, print: one
    cluster, as wide as the desk top) rigidly by its centre's shift under relayout.X_FRONT_ROOMS, so the centre that
    must land B4_DESK_GAP + half a desk west of the closet's wall face is that map's inverse."""
    x_new = LAUNDRY_CLEAR[0] - LAUNDRY_WALL_T - B4_DESK_GAP - B4_DESK_W / 2
    return _concept(R.X_FRONT_ROOMS, x_new)


def build_bed4(ctx, kit, M):
    kit.use('bed4')
    # Owner's change (2026-11-19, third round): the bed is turned across the room, headboard on the north wall and
    # its side along the west (window) wall, so the room's length stays open from the bed to the desk and closet.
    wall_w, wall_n = 0.225, 29.638
    xc = wall_w + 0.25 + 2.585                 # duvet (5.17 ft for the 4.5 ft full bed) 3 in off the west wall
    fb = Frame(xc, wall_n + 0.06, NORTH)
    info = F.bed(kit, M, fb, 'B4 bed', 'oak', 4.5, 6.25, upholstery=M['linen_sage'], bedding=dict(
        duvet=M['linen_white'], throw=M['knit_sage'], throw_len=1.5,
        pillows=[('std', M['linen_white'], 2, 66, 2.35, 1.65, 0.5),
                 ('accent', M['linen_oat'], 1, 62, 1.75, 1.75, 0.45),
                 ('lumbar', M['linen_sage'], 1, 55, 1.9, 0.95, 0.36)]))
    # one nightstand + lamp on the open (east) side of the headboard
    fr = Frame(xc + 2.585 + 0.2 + 0.6, wall_n + 0.06, NORTH)
    h = F.nightstand(kit, M, fr, 'B4 nightstand n', 'compact', 1.2, 1.72, 1.15)
    F.table_lamp(kit, M, fr.sub(0.0, 0.55, 0, h), 'B4 lamp n', 'stoneware_dark', 0.8, LIGHTS['B4']['lamp'], LIGHTS['B4']['bulb'])
    # ivory heathered flat-weave with a woven warm-grey border so it reads as an area rug, not carpet: under the
    # lower part of the bed and out into the open floor
    F.rug(kit, 'B4 rug', 1.6, 8.6, 31.7, 36.95, K.rug_material(
        'Z_bedrooms_rug_heather', ['#d3cdc2', '#e0dbd1', '#e9e5dc'], 60.0, 'heather',
        border=(3.25, 2.8, '#8a877e', ((0.3, 0.42), (0.52, 0.55)))))
    # desk group on the north wall, in the niche between the nightstand and the laundry closet's west wall (built
    # plan: desk x 8.175..11.675, 2 in off the closet wall). The lamp stands at the closet end, books and the plant
    # toward the nightstand; the chair is tucked in, clear of the rug.
    dx = _b4_desk_x()
    fd = Frame(dx, 29.64 + 0.05, NORTH)
    F.desk(kit, M, fd, 'B4 desk', B4_DESK_W, 1.6, 2.48, 'sled')
    F.side_chair(kit, M, Frame(dx + B4_CHAIR_DX, 31.95, SOUTH), 'B4 chair', M['linen_sage'])
    F.book_stack(kit, M, fd.sub(-1.15, 0.85, -0.1, 2.48), 'B4 desk books', [(0.8, 1.05, 0.08, 'cover_sage'), (0.72, 0.98, 0.07, 'cover_white')])
    succ, _ = K.import_asset(kit, 'potted_plant_04', '1k')
    x, y, z = fd.p(-0.3, 2.48, 0.62)
    succ.location = (x * FT, -z * FT, y * FT)
    succ.rotation_euler.z = 0.7
    F.table_lamp(kit, M, fd.sub(1.25, 0.6, 0, 2.48), 'B4 desk lamp', 'stoneware', 0.72, LIGHTS['B4']['desk'], LIGHTS['B4']['bulb'])
    F.framed_print(kit, Frame(dx, 29.64, NORTH), 'B4 print', 1.7, 2.2, K.art_brush(560, 720, 21), 0.28, 5.05)
    # (v7 bedrooms: the W12 roller shade is hung after the warp, in the 5'-0" window: bl/zones/bedrooms_rooms.py)
    # bypass closet door pulls (doors themselves are shell geometry)
    kit.wbox('B4 closet pull 1', 10.8, 10.85, 2.75, 3.45, 37.555, 37.58, 'black_metal', 0.005, 1)
    kit.wbox('B4 closet pull 2', 11.12, 11.17, 2.75, 3.45, 37.665, 37.69, 'black_metal', 0.005, 1)
    # reach-in interior (behind closed bypass doors)
    kit.use('bed4_closet')
    kit.wbox('B4 closet shelf', 8.1, 13.87, 6.25, 6.33, 38.6, 39.82, M['melamine'], 0.006, 1)
    kit.wbox('B4 closet rail', 8.15, 13.82, 5.85, 5.91, 38.77, 38.83, 'chrome', 0.01, 1)
    # lighting: opal globe from the ridge + two slope cans on the east slope
    kit.use('bed4_lights')
    F.globe_pendant(kit, M, 7.036, 33.55, 8.45, 'B4', 0.45, LIGHTS['B4']['globe'], LIGHTS['B4']['globe_w'])
    for z in (31.6, 35.6):
        F.slope_can(kit, 10.6, z, LIGHTS['B4']['slope'], lens=LIGHTS['B4']['lens'])
    return info


def bed4_closet_faces(ctx):
    """Bedroom 4's side of the laundry closet's two new walls. Called by bl/revisions.laundry_closet AFTER the warp
    (the walls exist only then), so everything here is in built-plan feet, from revision_spec:

    * west wall (faces the bed, the desk's end stands against it): a slim black-framed line print;
    * south wall (the pocket between the closet and the open door D04): an oak peg rail with black pegs and a canvas
      tote, the usual thing behind a bedroom door. Nothing reaches into the door's swing (south of z 33.60)."""
    kit = K.Kit(ctx)
    kit.use('bed4')
    M = F.mats()
    xw = LAUNDRY_CLEAR[0] - LAUNDRY_WALL_T              # the west wall's bedroom face (11.725)
    zs = LAUNDRY_CLEAR[3] + LAUNDRY_WALL_T              # the south wall's bedroom face (32.142)
    zn = LAUNDRY_CLEAR[2]                               # the room's north wall (28.892)
    out = {}
    # ---- slim print, centred on the wall's width between the desk's back edge and the corner
    zc = (zn + zs) / 2 + 0.2
    F.framed_print(kit, Frame(xw, zc, EAST), 'B4 print slim', 0.9, 1.85, K.art_line(380, 780, 5), 0.2, 5.0)
    out['print'] = {'z': round(zc, 3), 'frame w x h': (round(0.9 + 0.4 + 0.12, 2), round(1.85 + 0.4 + 0.12, 2))}
    # ---- peg rail on the south face
    x0, x1 = xw, LAUNDRY_CLEAR[1]                       # the face runs from the corner to the room's east wall
    fr = Frame((x0 + x1) / 2 - 0.15, zs, NORTH)         # local +x east, +z south (out of the wall)
    yr, rail_w, rail_h, rail_t = 5.55, 2.5, 0.3, 0.07
    kit.box('B4 peg rail', fr, (0, yr, rail_t / 2), (rail_w, rail_h, rail_t), 'white_oak_veneer', 0.012, 2)
    pegs = [-0.9, -0.3, 0.3, 0.9]
    for i, lx in enumerate(pegs):
        kit.cyl(f'B4 peg rail peg {i}', fr, (lx, yr, rail_t + 0.10), 0.028, 0.20, 'black_metal', 20, axis='Z')
        kit.cyl(f'B4 peg rail peg {i} cap', fr, (lx, yr, rail_t + 0.205), 0.045, 0.025, 'black_metal', 24, axis='Z')
    # canvas tote on the second peg: body hanging on two straps that loop over the peg
    lx, zb = pegs[1], rail_t + 0.105                    # the bag hangs under the peg's middle
    bw, bh, bd = 1.0, 1.1, 0.13
    top = yr - 0.62
    kit.soft('B4 peg rail tote', fr, (lx, top - bh / 2, zb), (bw, bh, bd), M['linen_sage'], 0.035, 3, 1, wrinkle=0.004)
    for k, dz in enumerate((-0.045, 0.045)):
        pts = []
        for j in range(13):
            a = math.pi * j / 12                        # over the peg: from the west attachment round to the east one
            pts.append(fr.p(lx - 0.27 * math.cos(a), top - 0.02 + (yr + 0.03 - top + 0.02) * math.sin(a) ** 0.6, zb + dz))
        v, f = K.tube_geo(pts, 0.018, 8)
        kit.mesh(f'B4 peg rail tote strap {k}', v, f, M['leather'], smooth=True)
    out['peg rail'] = {'x': [round(fr.p(-rail_w / 2, 0, 0)[0], 3), round(fr.p(rail_w / 2, 0, 0)[0], 3)], 'y': yr}
    return out


# ================================================================================== entry point
def _tri_count(coll):
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for ob in coll.all_objects:
        if ob.type != 'MESH':
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ev.to_mesh_clear()
    return tris


def build(ctx):
    t0 = time.time()
    kit = K.Kit(ctx)
    M = F.mats()
    build_bed2(ctx, kit, M)
    build_bed3(ctx, kit, M)
    _bed3_closet(ctx, kit, M)
    build_bed4(ctx, kit, M)
    bpy.context.view_layer.update()
    root = ctx.coll('zone_bedrooms')
    per_room = {c.name.replace('zone_bedrooms_', ''): len(c.all_objects) for c in root.children}
    res = {'objects': len(root.all_objects), 'lights': kit.lights, 'triangles': _tri_count(root),
           'per_collection': per_room, 'seconds': round(time.time() - t0, 1)}
    ctx.stats['bedrooms'] = res
    return res
