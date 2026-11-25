"""Primary suite zone: primary bedroom, vestibule and walk-in closet (sixth round, 2026-11-20).

Unlike the other zones this one is written in feet ON THE ARCHITECT'S PLAN and built AFTER the warp:
`build(ctx)` (called with the zones, before bl/warp.py) only registers the zone's collections; the furniture and the
closet's fit-out are built by `fit_out(ctx)`, which bl/revisions.suite_fit_out calls once bl/revisions.suite_rooms
(bl/zones/primary_suite_rooms.py) has put up the closet's east wall, its pocket door and the suite entry. The rooms
follow the architect's sheet SKA002 (bl/revision_spec.SUITE_*), so every position is the sheet's, not a concept
number carried through a map.

Design language (unchanged): serene, light, warm-white / white oak / walnut with black accents and one ochre note.

Bedroom (x 0.225..11.308, z 0.225..12.475), furniture as the sheet draws it: a king bed with its headboard on the
west wall, centred on the room (z 6.35), a nightstand each side (2'-0" wide, under the two west windows), a rug.
Both west windows stay (W15 z 1.225..4.225 since the eighth round, 3'-0" as on the sheet; W14 z 9.197..12.071; sills
2'-6"), and the bed as drawn is wider than
the pier between them, so NOTHING on that wall rises above the sills where there is glass behind it: the
channel-tufted headboard is low (2'-4 1/2") and runs the bed's full width under both sills, the nightstands are low
(1'-4 3/4") and carry small dome lamps (tops 2'-4"), and the tall pillows stand within the pier. A colour-field
canvas hangs on the pier above the bed. The east side stays clear from the vestibule to the rear slider (3.6 ft
between the bed's foot and the wall): the arch mirror and a framed print hang there; the concept's bench, dresser,
lounge chair and corner tree are gone (a dresser on the east wall would leave 2.4 ft at the bed's foot).

Vestibule (x 6.725..11.308, z 12.892..20.892): a calm passage. One full-height black-framed mirror on the closet
wall north of the closet door, two recessed cans, the switch by the suite entry. (The attic hatch is built with the
rooms.)

Walk-in closet (x 0.225..6.308, z 12.892..20.892), hanging on three sides as on the sheet, open (no fronts), in the
former wardrobes' finishes (warm-white lacquer uprights, oak shelves, black rods, 4000 K strips):
  west wall   a drawer / shelf tower facing the door (four drawers, lit shelves with folded knits and linen boxes)
              between a double-hang bay (north) and a single long-hang bay (south);
  north wall  double hang: shirts and jackets over trousers, linen boxes on the top shelf;
  south wall  single hang over a low shelf with boxes.
Rods stand 1.0 ft (north, south) and 1.1 ft (west) off the walls. A flush ceiling light in the middle; oak floor and
baseboards are the shell's.
"""
import math
import random
import time

import bpy
from mathutils import Matrix, Vector

from .. import assets, lighting
from .. import revision_spec as RS
from ..common import FT, ft2bl, move_to_collection, world_bbox_ft
from . import primary_suite_art as ART
from . import primary_suite_garments as PG
from . import primary_suite_geo as G
from . import primary_suite_mats as M

ZONE = 'zone_primary_suite'
C_BED = 'ps_bedroom'
C_DRS = 'ps_dressing'          # vestibule + walk-in closet
C_SOFT = 'ps_softgoods'
C_LIT = 'ps_lights'
C_MOD = 'ps_models'

# room datums (SCENE feet on the architect's plan = the sheet's frame, tools/render/relayout.py)
WEST, EAST, NORTH, SOUTH_B = RS.R.ROOMS['primary']    # the bedroom's wall faces: x 0.225, 11.308; z 0.225, 12.475
#                                                       (EAST is the vestibule's east face too; SOUTH_B is the wall
#                                                       between bedroom and closet)
CEIL = 8.0
CX0, CX1, CZ0, CZ1 = RS.SUITE_CLOSET_CLEAR          # walk-in closet inside
VX0, VX1, VZ0, VZ1 = RS.SUITE_VESTIBULE_CLEAR       # vestibule inside

# the two west windows (openings in z) and their sills: what stands in front of glass stays below SILL_CLEAR
W15_Z = RS.PRIMARY_WEST_WIN_Z     # v7 glazing: 3'-0" at the sheet's place, z 1.225..4.225 (it was 1.107..3.937)
W14_Z = RS.PRIMARY_WEST_WIN_S_Z   # v7 final: from the spec (z 9.197..12.071, the shell's opening as the warp carries it)
SILL_CLEAR = 2.43     # underside of the window stools (y 2.442; W14's stone sill was at 2.436); the glass starts at 2.6

BED_ZC = 6.35                                   # the sheet: the bed is centred on the room's depth
BED_HALF = 3.165                                # king mattress, 6'-4" wide
HB_Z0, HB_Z1 = BED_ZC - 3.53, BED_ZC + 3.53     # headboard as drawn: z 2.82..9.88
HB_TOP = 2.38
MAT_X0, MAT_X1 = 0.70, 7.37                     # mattress, 6'-8" long
MAT_TOP = 1.72
NS_W = 2.0                                      # nightstands as drawn: 2'-0" wide, z 0.81..2.81 and 9.89..11.89
NS_Z = ((BED_ZC - 5.54, BED_ZC - 3.54), (BED_ZC + 3.54, BED_ZC + 5.54))
NS_X = (0.30, 1.90)
NS_TOP = 1.40
ART_ZC = BED_ZC                                  # v7 repair: the canvas hangs on the bed's centre line (6.35) and is
ART_W = 3.75                                     # 3'-9" wide (4.2 at z 6.60 since W15 became 3'-0": 3 in off the bed's
#                                                  centre, tight to W15); its frame is 0.18 ft from W15's jamb
RUG = (2.40, 10.40, 1.75, 10.95)                # x0, x1, z0, z1 (8 x 9'-2", centred on the bed)
RUG_TOP = 0.042

CAMS = {'P0': (9.5, 10.5), 'S0': (8.23, VZ0 + 3.985)}     # sweeps of the fifth round's layout (clearance report only)


# ----------------------------------------------------------------------------- materials
def _mats(ctx):
    m = {}
    m['oak'] = ctx.mat('white_oak_veneer')
    m['walnut'] = ctx.mat('walnut_slab')
    m['black'] = ctx.mat('black_metal')
    m['blackpaint'] = ctx.mat('paint_black')
    m['trim'] = ctx.mat('paint_trim')
    m['mirror'] = ctx.mat('mirror')
    m['headboard'] = M.fabric('headboard_linen', '#b7afa3', rough=0.9, sheen=0.5, weave_scale=260, bump=0.35)
    m['sheet'] = M.fabric('sheet_white', '#f3f1ec', rough=0.92, sheen=0.35, weave_scale=520, bump=0.15, tint_var=0.02)
    m['duvet'] = M.fabric('duvet_linen_white_v2', '#f1eee7', rough=0.93, sheen=0.45, weave_scale=380, bump=0.3,
                          tint_var=0.03, wrinkle=0.22)
    m['euro'] = M.fabric('euro_linen_grey', '#c4bcb0', rough=0.9, sheen=0.5, weave_scale=300, bump=0.35)
    m['pillow'] = M.fabric('pillow_linen_white', '#f4f2ed', rough=0.92, sheen=0.4, weave_scale=420, bump=0.25, tint_var=0.02)
    m['lumbar'] = M.fabric('lumbar_ochre', '#b98a3e', rough=0.85, sheen=0.7, weave_scale=200, bump=0.3, kind='velvet')
    m['throw'] = M.fabric('throw_knit_oat', '#cbbca5', rough=0.95, sheen=0.5, weave_scale=420, bump=0.8, kind='knit')
    m['rug'] = M.rug('rug_wool_heather', light='#ddd6c9', dark='#c5bdaf',
                     half=((RUG[1] - RUG[0]) / 2, (RUG[3] - RUG[2]) / 2))
    m['lampbase'] = M.ceramic('lamp_ceramic', '#e9e4da', rough=0.45)
    m['shade'] = M.shade_fabric('lamp_shade_linen', '#f0ebe2')
    m['roller'] = M.roller_fabric('roller_shade', '#ebe5db')
    m['linenbox'] = M.fabric('linen_box', '#cbbfa9', rough=0.9, sheen=0.3, weave_scale=240, bump=0.45)
    m['leather'] = M.simple('leather_tab', '#8a5e38', rough=0.45)
    m['caseback'] = M.simple('case_back_warmwhite', '#efebe3', rough=0.6)
    m['lacquer'] = M.simple('wardrobe_lacquer_warmwhite', '#eeebe4', rough=0.33)
    m['brass'] = M.simple('brushed_brass', '#b8935a', rough=0.32, metal=1.0)
    m['book1'] = M.fabric('book_cloth_sand', '#c9b79a', rough=0.8, sheen=0.2, weave_scale=500, bump=0.2)
    m['book2'] = M.fabric('book_cloth_charcoal', '#3d3b38', rough=0.75, sheen=0.2, weave_scale=500, bump=0.2)
    m['book3'] = M.fabric('book_cloth_sage', '#98a08b', rough=0.8, sheen=0.2, weave_scale=500, bump=0.2)
    m['pages'] = M.simple('book_pages', '#efe9dc', rough=0.85)
    m['vase_dark'] = M.ceramic('vase_charcoal', '#4a4642', rough=0.55)
    m['vase_sand'] = M.ceramic('vase_sand', '#cdbb9e', rough=0.6)
    m['pot'] = M.ceramic('planter_stone', '#dcd6cb', rough=0.7)
    m['led'] = lighting.emitter('ps_led_strip', 4000, 5.0)
    m['ring'] = lighting.emitter('ps_ring_led', 3500, 8.0)
    m['closetlight'] = lighting.emitter('ps_closet_flush_led', 4000, 9.0)
    return m


# ----------------------------------------------------------------------------- utils
def _box(ctx, name, x0, x1, y0, y1, z0, z1, mat, coll, bevel=0.0, seg=3):
    return ctx.box(name, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1),
                   mat, coll, bevel, seg)


def _group(ctx, roots, name, coll):
    """Parent imported roots to an empty so they can be placed as one unit."""
    em = bpy.data.objects.new(name, None)
    ctx.coll(coll).objects.link(em)
    for r in roots:
        mw = r.matrix_world.copy()
        r.parent = em
        r.matrix_parent_inverse = Matrix.Identity(4)
        r.matrix_world = mw
    move_to_collection(roots, ctx.coll(coll))
    return em


def _import(ctx, asset_id, name, coll=C_MOD, res='2k'):
    path = assets.model(asset_id, res=res)
    roots = ctx.link_asset(path)
    em = _group(ctx, roots, name, coll)
    bpy.context.view_layer.update()
    return em, roots


def _place_on(em, roots, x, y, z, rot=0.0, scale=1.0):
    """Place group so its bbox bottom centre lands at SCENE (x, y, z)."""
    em.scale = (scale, scale, scale)
    em.rotation_euler = (0, 0, rot)
    em.location = (0, 0, 0)
    bpy.context.view_layer.update()
    bb = world_bbox_ft(roots)
    cx, cz = (bb[0] + bb[1]) / 2, (bb[4] + bb[5]) / 2
    em.location = ft2bl(x - cx, y - bb[2], z - cz)
    bpy.context.view_layer.update()
    return world_bbox_ft(roots)


def _true_extent(roots):
    """Exact world extent (SCENE ft) from mesh vertices (bound boxes of rotated objects overstate)."""
    from ..common import bl2ft
    pts = []
    stack = list(roots)
    while stack:
        o = stack.pop()
        stack.extend(o.children)
        if o.type == 'MESH':
            mw = o.matrix_world
            pts.extend(bl2ft(mw @ v.co) for v in o.data.vertices)
    xs, ys, zs = zip(*pts)
    return [round(v, 2) for v in (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))]


def _cyl(ctx, name, center, r, h, mat, coll, axis='Y', verts=32):
    return ctx.cylinder(name, center, r, h, mat, coll, verts=verts, axis=axis)


def _book(ctx, name, x0, z0, y0, w, d, h, rot, cover, pages, coll):
    """Hardcover book lying flat: footprint w (along x) x d (along z), thickness h."""
    cx, cz = x0 + w / 2, z0 + d / 2
    ctx.box_c(name + ' cover', (cx, y0 + h / 2, cz), (w, h, d), rot, cover, coll, bevel=0.008, segments=2)
    ctx.box_c(name + ' pages', (cx + 0.012 * math.cos(rot), y0 + h / 2, cz - 0.012 * math.sin(rot)),
              (w - 0.03, h - 0.03, d - 0.035), rot, pages, coll)
    return y0 + h


# ----------------------------------------------------------------------------- bedroom
def build_bed(ctx, m):
    """King bed as the sheet draws it: headboard on the west wall over the bed's full width (z 2.82..9.88), kept
    below the sills of the two windows it passes under; platform rail, mattress, linen."""
    c = C_BED
    s = C_SOFT
    n = 0
    # low headboard: backing panel + vertical channels
    _box(ctx, 'ps headboard back', 0.29, 0.44, 0.04, HB_TOP - 0.06, HB_Z0, HB_Z1, m['headboard'], c, bevel=0.04)
    nch = 10
    cw = (HB_Z1 - HB_Z0) / nch
    for k in range(nch):
        z0 = HB_Z0 + k * cw
        _box(ctx, f'ps headboard channel {k}', 0.40, 0.68, 0.30, HB_TOP, z0 + 0.006, z0 + cw - 0.006,
             m['headboard'], c, bevel=0.13, seg=6)
        n += 1
    # upholstered platform rail, recessed black plinth, mattress
    rz0, rz1 = BED_ZC - BED_HALF - 0.10, BED_ZC + BED_HALF + 0.10
    _box(ctx, 'ps bed rail', 0.66, MAT_X1 + 0.05, 0.25, 0.90, rz0, rz1, m['headboard'], c, bevel=0.08, seg=4)
    _box(ctx, 'ps bed plinth', 0.95, MAT_X1 - 0.27, 0.0, 0.25, rz0 + 0.35, rz1 - 0.35, m['blackpaint'], c)
    mz0, mz1 = BED_ZC - BED_HALF, BED_ZC + BED_HALF
    _box(ctx, 'ps mattress', MAT_X0, MAT_X1, 0.90, MAT_TOP, mz0, mz1, m['sheet'], s, bevel=0.13, seg=5)
    n += 5
    head = MAT_X0 + 1.67
    # duvet (drapes both sides and foot), turn-down band
    G.drape_sheet(ctx, 'ps duvet', MAT_X0, MAT_X1, mz0, mz1, MAT_TOP + 0.005, head=head, drape_side=0.9, drape_foot=0.85,
                  radius=0.2, step=0.07, mat=m['duvet'], coll=s, thick=0.075, seed=11, fold_amp=0.03, top_amp=0.03)
    G.drape_sheet(ctx, 'ps duvet turn-down', MAT_X0, head + 0.85, mz0, mz1, MAT_TOP + 0.085, head=head, drape_side=0.9,
                  drape_foot=0.0, radius=0.28, step=0.07, mat=m['duvet'], coll=s, thick=0.07, seed=12, fold_amp=0.02,
                  top_amp=0.012)
    # throw folded across the foot (concentric with the duvet's rounded edge)
    G.drape_sheet(ctx, 'ps throw', MAT_X0, MAT_X1 - 0.69, mz0, mz1, MAT_TOP + 0.135, head=MAT_X1 - 1.94, drape_side=0.97,
                  drape_foot=0.0, radius=0.33, step=0.06, mat=m['throw'], coll=s, thick=0.055, seed=13, fold_amp=0.012,
                  top_amp=0.01, skew=0.012)
    n += 3

    # pillows: 2 euro shams and 2 standard sleeping pillows, all within the pier between the windows, 1 lumbar
    def lean(xb, yb, zc, w, h, t, ang_deg, mat, name, seed, squash=0.0):
        a = math.radians(ang_deg)
        V = Vector((-math.sin(a), math.cos(a), 0))
        N = Vector((math.cos(a), math.sin(a), 0))
        O = Vector((xb, yb, zc)) + V * (h / 2)
        return G.pillow(ctx, name, w, h, t, O, (0, 0, 1), V, N, mat, s, seed=seed, squash=squash)
    yb = MAT_TOP + 0.05
    lean(MAT_X0 + 0.48, yb, BED_ZC - 1.08, 2.12, 2.08, 0.52, 12, m['euro'], 'ps euro sham N', 21)
    lean(MAT_X0 + 0.48, yb, BED_ZC + 1.08, 2.12, 2.08, 0.52, 13, m['euro'], 'ps euro sham S', 22)
    # (v7 glazing: 1.08 off the bed's centre line like the shams, 1.14 before: W15 is 3'-0" wide now and its south
    # jamb, z 4.225, stood 0.06 ft behind the north pillow's end)
    lean(MAT_X0 + 1.30, yb, BED_ZC - 1.08, 2.17, 1.62, 0.48, 36, m['pillow'], 'ps pillow N', 23)
    lean(MAT_X0 + 1.30, yb, BED_ZC + 1.08, 2.17, 1.62, 0.48, 38, m['pillow'], 'ps pillow S', 24)
    lean(MAT_X0 + 2.00, yb + 0.12, BED_ZC + 0.05, 2.70, 1.10, 0.40, 52, m['lumbar'], 'ps lumbar', 25)
    n += 5
    return n


def build_nightstands(ctx, m):
    """Two low oak nightstands as drawn (2'-0" wide), under the west windows: tops and lamps stay below the sills."""
    c = C_BED
    n = 0
    x0, x1 = NS_X
    top = NS_TOP
    for k, (z0, z1) in enumerate(NS_Z):
        tag = 'N' if k == 0 else 'S'
        _box(ctx, f'ps nightstand {tag} top', x0, x1, top - 0.08, top, z0, z1, m['oak'], c, bevel=0.012)
        _box(ctx, f'ps nightstand {tag} side a', x0, x1, 0.12, top - 0.08, z0, z0 + 0.06, m['oak'], c, bevel=0.006)
        _box(ctx, f'ps nightstand {tag} side b', x0, x1, 0.12, top - 0.08, z1 - 0.06, z1, m['oak'], c, bevel=0.006)
        _box(ctx, f'ps nightstand {tag} bottom', x0, x1, 0.12, 0.19, z0 + 0.06, z1 - 0.06, m['oak'], c, bevel=0.004)
        _box(ctx, f'ps nightstand {tag} back', x0, x0 + 0.04, 0.19, top - 0.08, z0 + 0.06, z1 - 0.06, m['oak'], c)
        _box(ctx, f'ps nightstand {tag} shelf', x0 + 0.04, x1 - 0.03, 0.80, 0.85, z0 + 0.06, z1 - 0.06, m['oak'], c)
        # drawer front (inset) with an under-lip finger reveal at the top
        _box(ctx, f'ps nightstand {tag} drawer', x1 - 0.06, x1, 0.87, top - 0.115, z0 + 0.068, z1 - 0.068,
             m['oak'], c, bevel=0.006)
        _box(ctx, f'ps nightstand {tag} drawer box', x0 + 0.06, x1 - 0.06, 0.87, top - 0.12, z0 + 0.08, z1 - 0.08,
             m['caseback'], c)
        _box(ctx, f'ps nightstand {tag} plinth', x0 + 0.1, x1 - 0.12, 0.0, 0.12, z0 + 0.1, z1 - 0.1, m['blackpaint'], c)
        n += 9
        zc = (z0 + z1) / 2
        lamp(ctx, m, 0.92, top, zc + (0.38 if k == 0 else -0.38), tag)      # toward the bed
        n += 4
    # north stand: two books in the open niche, a small charcoal cup on top
    zc = (NS_Z[0][0] + NS_Z[0][1]) / 2
    y = _book(ctx, 'ps nightstand book 1', 0.62, zc - 0.62, 0.19, 0.78, 0.98, 0.10, 0.04, m['book1'], m['pages'], c)
    _book(ctx, 'ps nightstand book 2', 0.65, zc - 0.58, y, 0.70, 0.90, 0.08, -0.06, m['book2'], m['pages'], c)
    G.lathe(ctx, 'ps nightstand cup', [(0.0, 0.0), (0.085, 0.0), (0.11, 0.03), (0.115, 0.2), (0.105, 0.2), (0.095, 0.04),
                                       (0.0, 0.03)], (1.25, top, zc - 0.5), m['vase_dark'], c, segs=40, cap_top=False,
            cap_bottom=False)
    # south stand: a book and a low ceramic bowl on top
    zc = (NS_Z[1][0] + NS_Z[1][1]) / 2
    yb = _book(ctx, 'ps nightstand book 3', 0.72, zc + 0.02, top, 0.62, 0.78, 0.075, 0.12, m['book3'], m['pages'], c)
    G.lathe(ctx, 'ps nightstand bowl', [(0.0, 0.0), (0.11, 0.0), (0.17, 0.04), (0.2, 0.1), (0.205, 0.12),
                                        (0.19, 0.12), (0.155, 0.06), (0.0, 0.05)],
            (1.03, yb, zc + 0.42), m['vase_dark'], c, segs=48, cap_top=False, cap_bottom=False)
    n += 7
    return n


def lamp(ctx, m, x, y0, z, tag):
    """Small dome table lamp, 11 1/2 in tall: it stands in front of a window, so its top stays under the sill."""
    c = C_BED
    prof = [(0.15, 0.0), (0.175, 0.012), (0.19, 0.05), (0.15, 0.16), (0.075, 0.30), (0.05, 0.42), (0.045, 0.52)]
    G.lathe(ctx, f'ps lamp {tag} base', prof, (x, y0, z), m['lampbase'], c, segs=64)
    _cyl(ctx, f'ps lamp {tag} socket', (x, y0 + 0.56, z), 0.05, 0.10, m['brass'], c, verts=24)
    dome = [(0.37, 0.50), (0.368, 0.58), (0.35, 0.68), (0.31, 0.77), (0.25, 0.85), (0.17, 0.91), (0.08, 0.945), (0.0, 0.955)]
    sh = G.lathe(ctx, f'ps lamp {tag} shade', dome, (x, y0, z), m['shade'], c, segs=72, cap_top=False, cap_bottom=False)
    G.solidify(sh, 0.012, offset=0.0)
    G.lathe(ctx, f'ps lamp {tag} rim', [(0.366, 0.494), (0.376, 0.494), (0.376, 0.506), (0.366, 0.506)],
            (x, y0, z), m['brass'], c, segs=72, cap_top=False, cap_bottom=False)
    lighting.point_light(ctx, x, y0 + 0.70, z, watts=2.0, kelvin=2700, radius_ft=0.09, coll=C_LIT,
                         name=f'ps lamp {tag}')


def build_art(ctx, m):
    """Colour-field canvas on the pier between the two west windows, above the bed."""
    c = C_BED
    img = ART.to_blender_image('Z_primary_suite_art_canvas', 1800, 1000, seed=7)
    mat = M.image_canvas('art_canvas', img)
    W = ART_W
    z0, z1 = ART_ZC - W / 2, ART_ZC + W / 2
    y0 = 4.70
    y1 = y0 + W / 1.8
    cv = _box(ctx, 'ps art canvas', 0.245, 0.375, y0, y1, z0, z1, mat, c, bevel=0.01, seg=2)
    G.uv_project(cv, 'z', 'y', z1, z0, y0, y1)
    # oak floater frame
    g, fw = 0.035, 0.035
    X0, X1 = 0.235, 0.40
    _box(ctx, 'ps art frame top', X0, X1, y1 + g, y1 + g + fw, z0 - g - fw, z1 + g + fw, m['oak'], c, bevel=0.004)
    _box(ctx, 'ps art frame bottom', X0, X1, y0 - g - fw, y0 - g, z0 - g - fw, z1 + g + fw, m['oak'], c, bevel=0.004)
    _box(ctx, 'ps art frame N', X0, X1, y0 - g, y1 + g, z0 - g - fw, z0 - g, m['oak'], c, bevel=0.004)
    _box(ctx, 'ps art frame S', X0, X1, y0 - g, y1 + g, z1 + g, z1 + g + fw, m['oak'], c, bevel=0.004)
    _box(ctx, 'ps art frame back', X0, X0 + 0.02, y0 - g, y1 + g, z0 - g, z1 + g, m['blackpaint'], c)
    return 6


def build_rug(ctx, m):
    x0, x1, z0, z1 = RUG
    _box(ctx, 'ps rug', x0, x1, 0.0005, RUG_TOP, z0, z1, m['rug'], C_BED, bevel=0.012, seg=2)
    return 1


def build_east_mirror(ctx, m):
    """Full-length arch-top mirror hung on the east wall opposite the bed (thin black frame)."""
    c = C_BED
    z0, z1 = BED_ZC - 1.3, BED_ZC + 1.3
    y0, y1 = 0.55, 7.0
    fw = 0.075
    outer = G.arch_outline(z0, z1, y0, y1, 48)
    inner = G.arch_outline(z0 + fw, z1 - fw, y0 + fw, y1 - fw, 48)
    G.prism_x(ctx, 'ps arch mirror frame', outer, EAST - 0.075, EAST - 0.004, m['black'], c, inner=inner)
    G.prism_x(ctx, 'ps arch mirror glass', inner, EAST - 0.05, EAST - 0.03, m['mirror'], c)
    G.prism_x(ctx, 'ps arch mirror back', inner, EAST - 0.03, EAST - 0.006, m['blackpaint'], c)
    return 3


def build_east_art(ctx, m):
    """Matted, glazed watercolour print on the east wall between the arch mirror and the vestibule
    (thin matte-black frame, wide white mat with a weighted bottom, anti-reflective glass)."""
    c = C_BED
    img = ART.to_blender_image('Z_primary_suite_art_wash', 700, 1020, seed=33, variant='wash')
    paper = M.image_paper('art_wash_paper', img)
    matb = M.simple('mat_board', '#f4f2ed', rough=0.92)
    zc, yc = 10.05, 5.05
    W, H = 1.65, 2.15                         # outer frame (z, y)
    fw = 0.062                                # frame face width
    z0, z1, y0, y1 = zc - W / 2, zc + W / 2, yc - H / 2, yc + H / 2
    XB, XF = EAST - 0.003, EAST - 0.09        # frame back (off the wall) / front
    blk = m['blackpaint']
    _box(ctx, 'ps print frame top', XF, XB, y1 - fw, y1, z0, z1, blk, c, bevel=0.006, seg=2)
    _box(ctx, 'ps print frame bottom', XF, XB, y0, y0 + fw, z0, z1, blk, c, bevel=0.006, seg=2)
    _box(ctx, 'ps print frame N', XF, XB, y0 + fw, y1 - fw, z0, z0 + fw, blk, c, bevel=0.006, seg=2)
    _box(ctx, 'ps print frame S', XF, XB, y0 + fw, y1 - fw, z1 - fw, z1, blk, c, bevel=0.006, seg=2)
    # mat board with the window cut (4 strips), print behind it, backing board behind that
    iz0, iz1, iy0, iy1 = z0 + fw, z1 - fw, y0 + fw, y1 - fw
    mz, mt, mb = 0.255, 0.255, 0.30           # mat borders (weighted bottom)
    oz0, oz1, oy0, oy1 = iz0 + mz, iz1 - mz, iy0 + mb, iy1 - mt
    MF, MB = EAST - 0.040, EAST - 0.030       # mat front/back faces
    _box(ctx, 'ps print mat top', MF, MB, oy1, iy1, iz0, iz1, matb, c, bevel=0.003, seg=1)
    _box(ctx, 'ps print mat bottom', MF, MB, iy0, oy0, iz0, iz1, matb, c, bevel=0.003, seg=1)
    _box(ctx, 'ps print mat N', MF, MB, oy0, oy1, iz0, oz0, matb, c, bevel=0.003, seg=1)
    _box(ctx, 'ps print mat S', MF, MB, oy0, oy1, oz1, iz1, matb, c, bevel=0.003, seg=1)
    pr = _box(ctx, 'ps print paper', MB, MB + 0.004, oy0 - 0.05, oy1 + 0.05, oz0 - 0.05, oz1 + 0.05, paper, c)
    G.uv_project(pr, 'z', 'y', oz0, oz1, oy0, oy1)
    _box(ctx, 'ps print backing', MB + 0.004, XB - 0.004, iy0, iy1, iz0, iz1, matb, c)
    _box(ctx, 'ps print glass', XF + 0.018, XF + 0.022, iy0 - 0.02, iy1 + 0.02, iz0 - 0.02, iz1 + 0.02,
         M.museum_glass(), c)
    return 12


def build_details(ctx, m):
    """Small real-world details: outlet on the bedroom's east wall, rocker switch inside the suite entry, a linear
    slot diffuser in the bedroom ceiling."""
    c = C_BED
    plate = M.simple('switch_plate', '#f2f0ec', rough=0.4)
    slot = M.simple('slot_diffuser_dark', '#26272a', rough=0.6)
    # duplex outlet, east wall (between mirror and print)
    _box(ctx, 'ps outlet plate', EAST - 0.02, EAST - 0.002, 1.0, 1.36, 8.30, 8.54, plate, c, bevel=0.008, seg=2)
    for k, yy in enumerate((1.12, 1.24)):
        _box(ctx, f'ps outlet face {k}', EAST - 0.026, EAST - 0.02, yy - 0.04, yy + 0.04, 8.37, 8.47, plate, c,
             bevel=0.004, seg=2)
    # rocker switch on the vestibule's east wall, just north of the suite entry
    sz = RS.SUITE_ENTRY_Z[0] - 0.62
    _box(ctx, 'ps switch plate', EAST - 0.02, EAST - 0.002, 3.85, 4.22, sz, sz + 0.24, plate, C_DRS, bevel=0.008, seg=2)
    _box(ctx, 'ps switch rocker', EAST - 0.03, EAST - 0.02, 3.92, 4.15, sz + 0.06, sz + 0.18, plate, C_DRS, bevel=0.006, seg=2)
    # linear slot diffuser near the rear sliding door
    _box(ctx, 'ps slot diffuser trim', 3.3, 8.3, CEIL - 0.006, CEIL - 0.001, 1.27, 1.53, plate, c)
    _box(ctx, 'ps slot diffuser slot', 3.34, 8.26, CEIL - 0.008, CEIL - 0.006, 1.33, 1.47, slot, c)
    return 7


def build_shades(ctx, m):
    """Inside-mount slim roller shades in the three openings, partly lowered (as before; fitted to the reveals)."""
    c = C_BED
    n = 0
    _WF, _SC = RS.GLAZING_WIN_FRAME, RS.slider_clear(RS.SLIDER_X)      # v7 glazing
    specs = [
        # (depths: from the window in the middle of the 5 in wall to just inside the room face of the wall)
        # v7 glazing: W15 and the rear slider are rebuilt at the sheet's widths (revision_spec, "v7 glazing"); their
        # shades hang inside the new frames, under the frames' heads (the last number: the cassette's top)
        # (v7 repair: W15's hem at W14's height, 6.05; it hung 0.07 ft lower in the same view)
        ('W15', 'z', W15_Z[0] + _WF + 0.005, W15_Z[1] - _WF - 0.005, RS.WEST_WALL_C + 0.08, WEST - 0.005, 6.05,
         RS.GLAZING_WIN_Y[1] - _WF - 0.005),                                       # between the frame's jambs
        # v7 final: W14 has W15's unit now (bl/revisions.primary_west_window_south), so its shade hangs like W15's:
        # between the frame's jambs, the cassette under the frame's head (top 6.935; it hung between the old unit's
        # painted jamb reveals with its top at 6.88, 0.055 ft lower than W15's) and as deep as W15's
        ('W14', 'z', W14_Z[0] + _WF + 0.005, W14_Z[1] - _WF - 0.005, RS.WEST_WALL_C + 0.08, WEST - 0.005, 6.05,
         RS.GLAZING_WIN_Y[1] - _WF - 0.005),
        ('W01', 'x', _SC[0] + 0.005, _SC[1] - 0.005, RS.REAR_WALL_C + RS.GLAZING_TRACK + RS.GLAZING_PANEL_T / 2 + 0.012,
         NORTH + 0.045, 5.98, RS.SLIDER_HEAD - RS.GLAZING_FRAME - 0.005),          # rear slider: between its jambs,
        #                                                                            clear of the fixed panel's room face
    ]
    for tag, along, a0, a1, d0, d1, ybot, ytop in specs:
        dm = (d0 + d1) / 2
        if along == 'z':
            _box(ctx, f'ps shade {tag} cassette', d0, d1, ytop - 0.16, ytop, a0, a1, m['trim'], c, bevel=0.02)
            _box(ctx, f'ps shade {tag} fabric', dm - 0.004, dm + 0.004, ybot, ytop - 0.16, a0 + 0.03, a1 - 0.03,
                 m['roller'], c)
            _box(ctx, f'ps shade {tag} bar', dm - 0.025, dm + 0.025, ybot - 0.07, ybot, a0 + 0.03, a1 - 0.03,
                 m['trim'], c, bevel=0.01)
        else:
            _box(ctx, f'ps shade {tag} cassette', a0, a1, ytop - 0.16, ytop, d0, d1, m['trim'], c, bevel=0.02)
            _box(ctx, f'ps shade {tag} fabric', a0 + 0.03, a1 - 0.03, ybot, ytop - 0.16, dm - 0.004, dm + 0.004,
                 m['roller'], c)
            _box(ctx, f'ps shade {tag} bar', a0 + 0.03, a1 - 0.03, ybot - 0.07, ybot, dm - 0.025, dm + 0.025,
                 m['trim'], c, bevel=0.01)
        n += 3
    return n


def build_ceiling_light(ctx, m):
    c = C_LIT
    x, z = 5.77, BED_ZC                   # the room's centre
    G.lathe(ctx, 'ps ring light body', [(0.0, 7.80), (0.70, 7.80), (0.76, 7.84), (0.76, 7.995), (0.0, 7.995)],
            (x, 0.0, z), m['trim'], c, segs=96)
    G.lathe(ctx, 'ps ring light diffuser', [(0.50, 7.792), (0.68, 7.792), (0.68, 7.801), (0.50, 7.801)],
            (x, 0.0, z), m['ring'], c, segs=96)
    return 2


# ----------------------------------------------------------------------------- vestibule
def build_vestibule(ctx, m):
    """A calm passage: one full-height mirror on the closet wall (north of the closet door), two recessed cans."""
    c = C_DRS
    face = VX0                                  # the closet wall's vestibule face
    d0 = RS.SUITE_CLOSET_DOOR_Z[0]
    mz0, mz1 = VZ0 + 0.50, d0 - 0.42            # between the bedroom opening's jamb and the door's strike jamb
    my0, my1 = 0.60, 6.90
    fx0, fx1 = face + 0.002, face + 0.07
    fw = 0.07
    _box(ctx, 'ps vestibule mirror glass', fx1 - 0.03, fx1 - 0.01, my0 + 0.02, my1 - 0.02, mz0 + 0.02, mz1 - 0.02, m['mirror'], c)
    _box(ctx, 'ps vestibule mirror back', fx0, fx1 - 0.03, my0 + 0.04, my1 - 0.04, mz0 + 0.04, mz1 - 0.04, m['blackpaint'], c)
    _box(ctx, 'ps vestibule mirror frame top', fx0, fx1, my1 - fw, my1, mz0, mz1, m['black'], c, bevel=0.006)
    _box(ctx, 'ps vestibule mirror frame bottom', fx0, fx1, my0, my0 + fw, mz0, mz1, m['black'], c, bevel=0.006)
    _box(ctx, 'ps vestibule mirror frame N', fx0, fx1, my0, my1, mz0, mz0 + fw, m['black'], c, bevel=0.006)
    _box(ctx, 'ps vestibule mirror frame S', fx0, fx1, my0, my1, mz1 - fw, mz1, m['black'], c, bevel=0.006)
    xc = (VX0 + VX1) / 2
    for z in (VZ0 + 4.215, VZ0 + 6.615):        # clear of the attic hatch (0.495..2.985 from the north end)
        lighting.can(ctx, xc, z, coll=C_LIT, kelvin=4700, watts=8.0)
    return 8


# ----------------------------------------------------------------------------- walk-in closet
ROD_R = 0.035
GAP = 0.085            # closet parts stand this far off the walls (clear of the baseboards)
TOP_SHELF = 6.95       # underside of the hanging bays' top shelves
ROD_HI, ROD_LO = 6.72, 3.43
MID_SHELF = 3.62
CLOSET_WATTS = 60.0    # the flush ceiling light's lamp (Blender watts as built; the renders scale fixtures by 0.12)


def _rail(along, a, b):
    """World (x, z) of a point `a` along a rod and `b` across it: rods run along 'x' (at z = fixed) or 'z'."""
    return (a, b) if along == 'x' else (b, a)


def _hanger(ctx, m, name, along, a, fixed, rod_y, bar=False, yaw=0.0, tip=0.66):
    """Slim walnut hanger on a rod that runs along `along` at the other coordinate `fixed`, hung at `a` along it:
    black wire hook wrapped over the rod + contoured shoulder bar, or a single slack bar for trousers."""
    c = C_DRS
    sh_y = rod_y - 0.13

    def w(t, y, d):                            # t along the rod from the hanger, d across it
        return (a + t, y, fixed + d) if along == 'x' else (fixed + d, y, a + t)
    top = sh_y + 0.015 if bar else rod_y - 0.14 - 0.035
    hook = [w(0.0, py, pz) for (_px, py, pz) in G.hook_path(0.0, rod_y, 0.0, ROD_R, top)]
    G.tube(ctx, name + ' hook', hook, 0.011, m['black'], c, segs=8)
    if bar:                                    # open-ended slack (trouser) hanger: the trousers fold over this bar
        size = (0.036, 0.036, 1.22) if along == 'x' else (1.22, 0.036, 0.036)
        x, _, z = w(0.0, 0.0, 0.0)
        ctx.box_c(name + ' bar', (x, sh_y, z), size, yaw if along == 'x' else -yaw, m['walnut'], c, bevel=0.014, segments=2)
        return
    hy = PG.hanger_curve(top, tip, 0.14 * (tip - 0.21) / 0.47)
    pts = [w(tip * k / 12 * math.sin(yaw), hy(tip * k / 12), tip * k / 12 * math.cos(yaw)) for k in range(-12, 13)]
    G.tube(ctx, name + ' shoulders', pts, 0.021, m['walnut'], c, segs=10)


def _hang(ctx, m, tag, along, fixed, a0, a1, rod_y, items, rnd, sway, front=1, pitch=(0.27, 0.40), clear=None):
    """Garments on hangers along a rod from a0 toward a1 (either order). items: [(colour, kind)], kind in shirt /
    stripe / jacket / coat. `clear`: height the hems must stay above (a shelf below). Returns the object count."""
    n = 0
    sgn = 1.0 if a1 >= a0 else -1.0
    a = a0 + sgn * 0.20
    ph = rnd.uniform(0, 6.3)
    top = rod_y - 0.175                              # hanger neck height
    for i, (col, kind) in enumerate(items):
        if i:
            a += sgn * rnd.uniform(*pitch)
        ai = a + rnd.uniform(-0.02, 0.02)
        if (a1 - ai) * sgn < 0.18:
            break
        if kind in ('jacket', 'coat'):
            mat = M.fabric(f'wool_{col[1:]}', col, rough=0.9, sheen=0.35, weave_scale=260, bump=0.32, tint_var=0.04)
            L = rnd.uniform(2.95, 3.15) if kind == 'coat' else rnd.uniform(2.6, 2.75)
            shw = rnd.uniform(1.48, 1.58)
            gk = 'jacket'
        else:
            mat = M.fabric(f'shirting_{col[1:]}{"_stripe" if kind == "stripe" else ""}', col, rough=0.82, sheen=0.5,
                           weave_scale=520, bump=0.18, tint_var=0.035)
            if kind == 'stripe':                     # sky-blue bengal stripe on white (stripes run down)
                M.stripe(mat, '#93acc7', axis='Y', period_in=0.5, duty=0.4)
            L, shw = rnd.uniform(2.3, 2.6), rnd.uniform(1.3, 1.46)
            gk = 'shirt'
        if clear is not None:
            L = min(L, top - clear)
        yaw = 0.05 * math.sin(0.9 * i + ph) + rnd.uniform(-0.02, 0.02)
        tip = min(0.66, shw / 2 - 0.05)
        _hanger(ctx, m, f'ps closet {tag} hanger {i}', along, ai, fixed, rod_y, yaw=yaw, tip=tip)
        hy = PG.hanger_curve(top, tip, 0.14 * (tip - 0.21) / 0.47)
        v, f = PG.garment(gk, _rail(along, ai, fixed), along, hy, L, shw, seed=100 + 7 * sum(map(ord, tag)) + i, yaw=yaw,
                          sway_off=sway, front=front)
        ob = G.mesh_ft(ctx, f'ps closet {tag} garment {i}', v, f, mat, C_DRS, smooth=True)
        G._fix_normals(ob)                           # also welds the shoulder seam
        G.solidify(ob, 0.009 if gk == 'jacket' else 0.007, 0.0)
        G.subsurf(ob, 1)
        n += 3
    return n


def _trousers(ctx, m, tag, along, fixed, a0, a1, rod_y, cols, rnd, sway, front=1):
    n = 0
    sgn = 1.0 if a1 >= a0 else -1.0
    a = a0 + sgn * 0.16
    for i, col in enumerate(cols):
        if i:
            a += sgn * rnd.uniform(0.17, 0.24)
        if (a1 - a) * sgn < 0.14:
            break
        mat = M.fabric(f'cloth_{col[1:]}', col, rough=0.85, sheen=0.4, weave_scale=480, bump=0.25, tint_var=0.04,
                       wrinkle=0.2)
        yaw = 0.04 * math.sin(0.9 * i + 2.0) + rnd.uniform(-0.015, 0.015)
        _hanger(ctx, m, f'ps closet {tag} slack hanger {i}', along, a, fixed, rod_y, bar=True, yaw=yaw)
        v, f = PG.trousers(_rail(along, a, fixed), along, rod_y - 0.13, rnd.uniform(1.12, 1.38), rnd.uniform(1.45, 1.75),
                           rnd.uniform(0.28, 0.33), seed=300 + 7 * sum(map(ord, tag)) + i, yaw=yaw, sway_off=sway, front=front)
        ob = G.mesh_ft(ctx, f'ps closet {tag} trousers {i}', v, f, mat, C_DRS, smooth=True)
        G._fix_normals(ob)
        G.subsurf(ob, 1)
        n += 3
    return n


def _linen_box(ctx, m, name, x0, x1, y0, y1, z0, z1, face):
    """Linen storage box with a leather pull tab on the face that looks into the room: 'x+', 'z+' or 'z-'."""
    c = C_DRS
    _box(ctx, name, x0, x1, y0, y1, z0, z1, m['linenbox'], c, bevel=0.025, seg=3)
    yc = (y0 + y1) / 2 + 0.08
    if face == 'x+':
        ctx.box_c(name + ' tab', (x1 + 0.006, yc, (z0 + z1) / 2), (0.012, 0.09, 0.3), 0.0, m['leather'], c, bevel=0.004, segments=2)
    else:
        zf = z1 + 0.006 if face == 'z+' else z0 - 0.006
        ctx.box_c(name + ' tab', ((x0 + x1) / 2, yc, zf), (0.3, 0.09, 0.012), 0.0, m['leather'], c, bevel=0.004, segments=2)


def build_closet(ctx, m):
    """Walk-in closet fit-out: hanging on three sides as on the sheet, a drawer / shelf tower opposite the door."""
    c = C_DRS
    n = 0
    oak, cb, lac, blk = m['oak'], m['caseback'], m['lacquer'], m['black']
    rnd = random.Random(42)
    sway = Vector((rnd.random() * 30, rnd.random() * 30, rnd.random() * 30))
    T = 0.06                                         # panel thickness
    HT = 7.02                                        # top of the hanging bays' shelves / uprights

    # ---------------- west wall: bay (double hang) | tower | bay (long hang)
    XB = CX0 + GAP                                   # 0.31: backs of the uprights
    XS = XB + 1.30                                   # front of the hanging bays' shelves and short uprights
    XT = XB + 1.80                                   # front of the tower
    XR = CX0 + 1.10                                  # west rod, 1.1 ft off the wall
    zc = (CZ0 + CZ1) / 2
    TZ0, TZ1 = zc - 1.335, zc + 1.335                # tower, centred on the door: z 15.50..18.17
    WZ0, WZ1 = CZ0 + GAP, CZ1 - GAP                  # 12.92..20.75
    TT = 7.30                                        # top of the tower
    _box(ctx, 'ps closet W upright north end', XB, XS, 0.0, HT, WZ0, WZ0 + T, lac, c, bevel=0.004)
    _box(ctx, 'ps closet W upright south end', XB, XS, 0.0, HT, WZ1 - T, WZ1, lac, c, bevel=0.004)
    _box(ctx, 'ps closet tower side N', XB, XT, 0.0, TT, TZ0, TZ0 + T, lac, c, bevel=0.004)
    _box(ctx, 'ps closet tower side S', XB, XT, 0.0, TT, TZ1 - T, TZ1, lac, c, bevel=0.004)
    _box(ctx, 'ps closet tower back', XB, XB + 0.04, 0.33, TT, TZ0 + T, TZ1 - T, cb, c)
    _box(ctx, 'ps closet tower kick', XB, XT - 0.12, 0.0, 0.33, TZ0 + T, TZ1 - T, m['blackpaint'], c)
    _box(ctx, 'ps closet tower top', XB, XT, TT - T, TT, TZ0 + T, TZ1 - T, lac, c)
    n += 7
    za, zb = TZ0 + T, TZ1 - T
    drows = [(0.36, 0.98), (1.01, 1.63), (1.66, 2.28), (2.31, 2.93)]
    for i, (r0, r1) in enumerate(drows):             # slab drawer fronts with a finger lip along the top edge
        _box(ctx, f'ps closet tower drawer {i}', XT - 0.06, XT, r0, r1 - 0.06, za + 0.008, zb - 0.008, oak, c, bevel=0.005)
        _box(ctx, f'ps closet tower drawer lip {i}', XT - 0.06, XT - 0.02, r1 - 0.06, r1, za + 0.008, zb - 0.008, oak, c)
        _box(ctx, f'ps closet tower drawer shadow {i}', XT - 0.022, XT - 0.019, r1 - 0.056, r1 - 0.025, za + 0.02, zb - 0.02,
             m['blackpaint'], c)
        n += 3
    _box(ctx, 'ps closet tower drawer case', XB + 0.04, XT - 0.06, 0.33, 2.95, za, zb, cb, c)
    shelves = [2.95, 3.90, 4.82, 5.74, 6.56]
    for yy in shelves:
        _box(ctx, f'ps closet tower shelf {yy}', XB + 0.04, XT - 0.02, yy, yy + 0.06, za, zb, oak, c, bevel=0.004)
        if yy > 3.0:
            _box(ctx, f'ps closet tower led {yy}', XT - 0.17, XT - 0.13, yy - 0.012, yy, za + 0.04, zb - 0.04, m['led'], C_LIT)
        n += 2
    _box(ctx, 'ps closet tower led top', XT - 0.17, XT - 0.13, TT - T - 0.012, TT - T, za + 0.04, zb - 0.04, m['led'], C_LIT)
    knit = ['#e8e2d6', '#c9b89c', '#8f8b84', '#f0ede6', '#3e3f42', '#b9a07a', '#2f3746', '#d9d4ca']
    xk = (XB + XT) / 2 + 0.12
    stacks = [(3.01, za + 0.62, [0, 6, 1]), (3.01, zb - 0.62, [3, 7, 3]),      # on the deck above the drawers
              (3.96, za + 0.66, [4, 2, 0]), (3.96, zb - 0.64, [5, 1, 6, 3]),
              (4.88, zb - 0.62, [7, 0, 5])]
    for si, (y, zs, seq) in enumerate(stacks):
        for k, ci in enumerate(seq):
            col = knit[ci]
            mat = M.fabric(f'knit_{col[1:]}', col, rough=0.95, sheen=0.5, weave_scale=420, bump=0.7, kind='knit')
            h = rnd.uniform(0.15, 0.19)
            G.folded_item(ctx, f'ps closet tower folded {si}.{k}', xk + rnd.uniform(-0.03, 0.03), y,
                          zs + rnd.uniform(-0.03, 0.03), 1.0, 0.94, h, rnd.uniform(-0.035, 0.035), mat, c)
            y += h - 0.005
            n += 2
    G.lathe(ctx, 'ps closet tower bowl', [(0.0, 0.0), (0.11, 0.0), (0.17, 0.04), (0.2, 0.1), (0.205, 0.12),
                                          (0.19, 0.12), (0.155, 0.06), (0.0, 0.05)],
            (XT - 0.45, 4.88, za + 0.55), m['vase_sand'], c, segs=48, cap_top=False, cap_bottom=False)
    for i, (z0, z1) in enumerate(((za + 0.05, zc - 0.03), (zc + 0.03, zb - 0.05))):
        _linen_box(ctx, m, f'ps closet tower box {i}', XB + 0.25, XT - 0.12, 5.80, 6.46, z0, z1, 'x+')
        _linen_box(ctx, m, f'ps closet tower top box {i}', XB + 0.25, XT - 0.16, 6.62, 7.20, z0, z1, 'x+')
        n += 4
    # hanging bays: top shelf, rod(s), strip light under the shelf
    for tag, z0, z1 in (('WN', WZ0 + T, TZ0), ('WS', TZ1, WZ1 - T)):
        _box(ctx, f'ps closet {tag} top shelf', XB, XS, TOP_SHELF, HT, z0, z1, oak, c, bevel=0.004)
        _cyl(ctx, f'ps closet {tag} rod', (XR, ROD_HI, (z0 + z1) / 2), ROD_R, z1 - z0, blk, c, axis='Z', verts=20)
        _box(ctx, f'ps closet {tag} led', XS - 0.16, XS - 0.12, TOP_SHELF - 0.012, TOP_SHELF, z0 + 0.05, z1 - 0.05, m['led'], C_LIT)
        n += 3
    # WN: double hang (shirts over trousers); garments face south, toward the middle of the closet
    z0, z1 = WZ0 + T, TZ0
    _box(ctx, 'ps closet WN mid shelf', XB, XS, MID_SHELF, MID_SHELF + 0.06, z0, z1, oak, c, bevel=0.004)
    _cyl(ctx, 'ps closet WN rod lower', (XR, ROD_LO, (z0 + z1) / 2), ROD_R, z1 - z0, blk, c, axis='Z', verts=20)
    n += 2
    n += _hang(ctx, m, 'WN', 'z', XR, z1 - 0.05, z0 + 0.05, ROD_HI,
               [('#f4f2ee', 'shirt'), ('#dfe5ea', 'shirt'), ('#ece7dd', 'shirt'), ('#f1f1ee', 'stripe'), ('#c9d3dc', 'shirt'),
                ('#d9ccb4', 'shirt'), ('#f4f2ee', 'shirt')], rnd, sway, front=1, clear=MID_SHELF + 0.13)
    n += _trousers(ctx, m, 'WN', 'z', XR, z1 - 0.05, z0 + 0.05, ROD_LO,
                   ['#2f3134', '#c8bea9', '#454b57', '#e4ddcf', '#6f6b64', '#b6a789', '#8b8e93', '#d9d2c4', '#57534d'],
                   rnd, sway, front=1)
    _linen_box(ctx, m, 'ps closet WN top box 0', XB + 0.1, XS - 0.08, HT, HT + 0.58, z0 + 0.10, z0 + 1.20, 'x+')
    _linen_box(ctx, m, 'ps closet WN top box 1', XB + 0.1, XS - 0.08, HT, HT + 0.58, z0 + 1.28, z1 - 0.08, 'x+')
    n += 4
    # WS: long hang (coats); garments face north
    z0, z1 = TZ1, WZ1 - T
    n += _hang(ctx, m, 'WS', 'z', XR, z0 + 0.05, z1 - 0.05, ROD_HI,
               [('#b9a27c', 'coat'), ('#4f5357', 'coat'), ('#e6dfd1', 'coat'), ('#2f3a4c', 'jacket'), ('#8a8474', 'coat'),
                ('#c2b294', 'jacket'), ('#6b6864', 'coat')], rnd, sway, front=-1, pitch=(0.30, 0.42))
    _linen_box(ctx, m, 'ps closet WS floor box 0', XB + 0.12, XS - 0.05, 0.0, 0.82, z0 + 0.12, z0 + 1.22, 'x+')
    _linen_box(ctx, m, 'ps closet WS floor box 1', XB + 0.12, XS - 0.05, 0.0, 0.82, z0 + 1.30, z1 - 0.10, 'x+')
    _linen_box(ctx, m, 'ps closet WS top box 0', XB + 0.1, XS - 0.08, HT, HT + 0.58, z0 + 0.08, z0 + 1.50, 'x+')
    n += 6

    # ---------------- north and south walls: x NX0..NX1, clear of the west bays' garments
    NX0, NX1 = XT + 0.20, CX1 - 0.06                # 2.31..6.248
    for tag, sgn, wall in (('N', 1.0, CZ0), ('S', -1.0, CZ1)):
        zb_ = wall + sgn * GAP                      # back of the uprights
        zf_ = zb_ + sgn * 1.30                      # front of the shelf
        zr_ = wall + sgn * 1.00                     # rod, 1.0 ft off the wall
        face = 'z+' if sgn > 0 else 'z-'
        _box(ctx, f'ps closet {tag} upright west', NX0, NX0 + T, 0.0, HT, zb_, zf_, lac, c, bevel=0.004)
        _box(ctx, f'ps closet {tag} upright east', NX1 - T, NX1, 0.0, HT, zb_, zf_, lac, c, bevel=0.004)
        _box(ctx, f'ps closet {tag} top shelf', NX0 + T, NX1 - T, TOP_SHELF, HT, zb_, zf_, oak, c, bevel=0.004)
        _cyl(ctx, f'ps closet {tag} rod', ((NX0 + NX1) / 2, ROD_HI, zr_), ROD_R, NX1 - NX0 - 2 * T, blk, c, axis='X', verts=20)
        _box(ctx, f'ps closet {tag} led', NX0 + 0.12, NX1 - 0.12, TOP_SHELF - 0.012, TOP_SHELF, zf_ - sgn * 0.16, zf_ - sgn * 0.12,
             m['led'], C_LIT)
        n += 5
        x0, x1 = NX0 + T, NX1 - T
        if tag == 'N':                              # double hang: shirts and jackets over trousers
            _box(ctx, 'ps closet N mid shelf', x0, x1, MID_SHELF, MID_SHELF + 0.06, zb_, zf_, oak, c, bevel=0.004)
            _cyl(ctx, 'ps closet N rod lower', ((x0 + x1) / 2, ROD_LO, zr_), ROD_R, x1 - x0, blk, c, axis='X', verts=20)
            _box(ctx, 'ps closet N led mid', x0 + 0.06, x1 - 0.06, MID_SHELF - 0.012, MID_SHELF, zf_ - 0.16, zf_ - 0.12, m['led'], C_LIT)
            n += 3
            n += _hang(ctx, m, 'N', 'x', zr_, x1 - 0.04, x0 + 0.04, ROD_HI,
                       [('#f4f2ee', 'shirt'), ('#ece7dd', 'shirt'), ('#dcd3c4', 'shirt'), ('#f1f1ee', 'stripe'),
                        ('#b7c5d2', 'shirt'), ('#d9ccb4', 'shirt'), ('#e9e4d8', 'shirt'), ('#c2b294', 'jacket'),
                        ('#8f8a80', 'jacket'), ('#6b6864', 'jacket'), ('#3f444c', 'jacket')],
                       rnd, sway, front=1, clear=MID_SHELF + 0.13)
            n += _trousers(ctx, m, 'N', 'x', zr_, x1 - 0.04, x0 + 0.04, ROD_LO,
                           ['#2f3134', '#c8bea9', '#454b57', '#e4ddcf', '#6f6b64', '#b6a789', '#8b8e93', '#d9d2c4',
                            '#57534d', '#a39c90', '#34383f', '#cfc6b4', '#7a766e'], rnd, sway, front=1)
            for i, (a, b) in enumerate(((x0 + 0.08, x0 + 1.18), (x0 + 1.28, x0 + 2.38), (x0 + 2.48, x1 - 0.08))):
                _linen_box(ctx, m, f'ps closet N top box {i}', a, b, HT, HT + 0.58, zb_ + 0.06, zf_ - 0.08, face)
                n += 2
        else:                                       # single hang over a low shelf with boxes
            _box(ctx, 'ps closet S low shelf', x0, x1, 1.16, 1.22, zf_, zb_, oak, c, bevel=0.004)
            n += 1
            n += _hang(ctx, m, 'S', 'x', zr_, x1 - 0.04, x0 + 0.04, ROD_HI,
                       [('#e6dfd1', 'coat'), ('#b9a27c', 'coat'), ('#f4f2ee', 'shirt'), ('#9aa38d', 'shirt'),
                        ('#d8c9b0', 'jacket'), ('#f1f1ee', 'stripe'), ('#55585c', 'coat'), ('#ece7dd', 'shirt'),
                        ('#2f3a4c', 'coat'), ('#c9b89c', 'jacket')], rnd, sway, front=1, pitch=(0.30, 0.42), clear=1.45)
            for i, (a, b) in enumerate(((x0 + 0.10, x0 + 1.30), (x0 + 1.42, x0 + 2.62))):
                _linen_box(ctx, m, f'ps closet S floor box {i}', a, b, 0.0, 0.84, zf_ + 0.10, zb_ - 0.06, face)
                n += 2
            # on the low shelf: folded denim and a lidded fabric basket
            denim = ['#3b4a5e', '#5d6f86', '#2c3442', '#8497ad']
            ys = 1.22
            for k, col in enumerate(denim[:3]):
                mat = M.fabric(f'denim_{col[1:]}', col, rough=0.9, sheen=0.3, weave_scale=380, bump=0.5)
                h = rnd.uniform(0.16, 0.2)
                G.folded_item(ctx, f'ps closet S folded {k}', x1 - 0.72 + rnd.uniform(-0.02, 0.02), ys, (zf_ + zb_) / 2 - 0.06,
                              1.05, 0.95, h, rnd.uniform(-0.03, 0.03), mat, c)
                ys += h - 0.005
                n += 2
            G.lathe(ctx, 'ps closet S basket', [(0.0, 0.0), (0.40, 0.0), (0.46, 0.05), (0.50, 0.62), (0.47, 0.66), (0.44, 0.66),
                                                (0.44, 0.60), (0.0, 0.60)],
                    (x1 - 2.0, 1.22, (zf_ + zb_) / 2 - 0.02), m['linenbox'], c, segs=48, cap_top=False, cap_bottom=False)
            n += 1
            _linen_box(ctx, m, 'ps closet S top box 0', x0 + 0.10, x0 + 1.50, HT, HT + 0.58, zf_ + 0.08, zb_ - 0.06, face)
            _linen_box(ctx, m, 'ps closet S top box 1', x1 - 1.40, x1 - 0.10, HT, HT + 0.58, zf_ + 0.08, zb_ - 0.06, face)
            n += 4

    # ---------------- flush ceiling light over the middle of the free floor
    lx, lz = (XT + CX1) / 2, zc
    G.lathe(ctx, 'ps closet flush light body', [(0.0, 7.86), (0.50, 7.86), (0.55, 7.89), (0.55, 7.995), (0.0, 7.995)],
            (lx, 0.0, lz), m['trim'], C_LIT, segs=72)
    G.lathe(ctx, 'ps closet flush light diffuser', [(0.0, 7.853), (0.47, 7.853), (0.47, 7.861), (0.0, 7.861)],
            (lx, 0.0, lz), m['closetlight'], C_LIT, segs=72)
    # the room has no window: a disk lamp under the diffuser does the lighting (the diffuser is what the camera sees)
    ld = bpy.data.lights.new('ps closet flush light', 'AREA')
    ld.shape = 'DISK'
    ld.size = 0.9 * FT
    ld.energy = CLOSET_WATTS
    ld.color = lighting.kelvin_rgb(4000)
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(lx, 7.84, lz)
    lo.visible_camera = False
    lo.visible_glossy = False
    ctx.coll(C_LIT).objects.link(lo)
    n += 3
    return n


# ----------------------------------------------------------------------------- checks
def _zone_meshes(ctx):
    for ob in ctx.coll(ZONE).all_objects:
        if ob.type == 'MESH' and len(ob.data.vertices):
            yield ob


def _world_bbox(ob, dg):
    """Exact world bounds (SCENE ft) of the evaluated mesh (modifiers applied)."""
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    xs = [p.x / FT for p in pts]
    ys = [p.z / FT for p in pts]
    zs = [-p.y / FT for p in pts]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def _checks(ctx, notes):
    """Geometry audit on the built zone: nothing in front of the west windows' glass, the east side of the bedroom
    clear, nothing in the door openings, nothing inside a wall; and the old camera-clearance report."""
    dg = bpy.context.evaluated_depsgraph_get()
    bbs = {ob.name: _world_bbox(ob, dg) for ob in _zone_meshes(ctx)}
    glass, aisle, doors, walls, cams = [], [], [], [], []
    d0, d1 = RS.SUITE_CLOSET_DOOR_Z
    e0, e1 = RS.SUITE_ENTRY_Z
    for name, b in bbs.items():
        x0, x1, y0, y1, z0, z1 = b
        if name.startswith('ps shade'):
            continue
        # west windows: anything within 4 ft of the wall, in a window's z-range, above the sill line
        if x0 < 4.0 and y1 > SILL_CLEAR + 0.006 and y0 < 7.0:
            for tag, (wz0, wz1) in (('W15', W15_Z), ('W14', W14_Z)):
                if z0 < wz1 - 0.01 and z1 > wz0 + 0.01:
                    glass.append((tag, name, round(y1, 3), round(max(z0, wz0), 3), round(min(z1, wz1), 3)))
        # east side of the bedroom: 3 ft clear along the east wall from the vestibule to the slider (below 6.5 ft)
        if 0.1 < y1 and y0 < 6.5 and x1 > EAST - 3.0 and x0 < EAST - 0.12 and z0 < SOUTH_B and z1 > NORTH and name != 'ps rug':
            aisle.append((name, round(x0, 3)))
        # door openings (below the heads)
        for tag, (ax0, ax1, az0, az1) in (('bedroom opening', (VX0, VX1, SOUTH_B - 0.05, VZ0 + 0.05)),
                                          ('closet door', (CX1 - 0.1, VX0 + 0.1, d0 + 0.03, d1 - RS.SUITE_CLOSET_LEAF_SHOWN - 0.03)),
                                          ('suite entry', (VX1 - 0.1, VX1 + 0.6, e0 + 0.03, e1 - 0.08))):
            if x0 < ax1 and x1 > ax0 and z0 < az1 and z1 > az0 and y0 < 6.5 and y1 > 0.05:
                doors.append((tag, name))
        # inside a wall: west / north / south / east faces of the three rooms (0.02 ft tolerance)
        if x0 < WEST - 0.02 or z0 < NORTH - 0.02 or x1 > EAST + 0.02 or z1 > CZ1 + 0.02:
            walls.append((name, [round(v, 3) for v in b]))
        elif z0 < CZ0 - 0.02 and z1 > SOUTH_B + 0.02 and x0 < VX0 - 0.02:
            walls.append((name, [round(v, 3) for v in b]))
        elif x0 < VX0 - 0.02 and x1 > CX1 + 0.02 and z1 > CZ0 + 0.02 and not (z0 > d0 and z1 < d1):
            walls.append((name, [round(v, 3) for v in b]))
        for cid, (cx, cz) in CAMS.items():
            if y0 > 6.5 or y1 < 0.1:
                continue
            if x0 - 1.2 < cx < x1 + 1.2 and z0 - 1.2 < cz < z1 + 1.2:
                cams.append((cid, name))
    notes['in front of window glass'] = glass
    notes['east side of the bedroom (3 ft)'] = aisle
    notes['in a door opening'] = doors
    notes['in a wall'] = walls
    notes['camera_conflicts'] = cams
    bed = [b for n, b in bbs.items() if n.startswith(('ps bed', 'ps mattress', 'ps duvet', 'ps throw'))]
    if bed:
        foot = max(b[1] for b in bed)
        notes['bed foot x'] = round(foot, 3)
        notes['clear east of the bed'] = round(EAST - 0.053 - foot, 3)


def _triangles(ctx):
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for ob in ctx.coll(ZONE).all_objects:
        if ob.type != 'MESH':
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ev.to_mesh_clear()
    return tris


# ----------------------------------------------------------------------------- entry
def build(ctx):
    """Called with the zones, BEFORE the warp: registers the zone only. Everything is built by fit_out() on the
    architect's plan (see the module docstring)."""
    ctx.coll(ZONE)
    for sub in (C_BED, C_DRS, C_SOFT, C_LIT, C_MOD):
        ctx.coll(sub, ZONE)
    res = {'objects': 0, 'note': 'built after the warp by bl/revisions.suite_fit_out (plan feet)'}
    ctx.stats['primary_suite'] = res
    return res


def fit_out(ctx):
    """Bedroom furniture, vestibule and walk-in closet, in SCENE feet on the architect's plan. Called by
    bl/revisions.suite_fit_out after the warp and after the suite's walls and doors are up."""
    t0 = time.time()
    ctx.coll(ZONE)
    for sub in (C_BED, C_DRS, C_SOFT, C_LIT, C_MOD):
        ctx.coll(sub, ZONE)
    m = _mats(ctx)
    notes = {}
    counts = {}
    counts['bed'] = build_bed(ctx, m)
    counts['nightstands'] = build_nightstands(ctx, m)
    counts['art'] = build_art(ctx, m)
    counts['rug'] = build_rug(ctx, m)
    counts['shades'] = build_shades(ctx, m)
    counts['east_mirror'] = build_east_mirror(ctx, m)
    counts['east_art'] = build_east_art(ctx, m)
    counts['details'] = build_details(ctx, m)
    counts['ceiling_light'] = build_ceiling_light(ctx, m)
    counts['vestibule'] = build_vestibule(ctx, m)
    counts['closet'] = build_closet(ctx, m)
    bpy.context.view_layer.update()
    _checks(ctx, notes)
    objs = [o for o in ctx.coll(ZONE).all_objects]
    res = {'objects': len(objs), 'triangles': _triangles(ctx), 'seconds': round(time.time() - t0, 1),
           'parts': counts, 'notes': notes,
           'bed': {'centre z': BED_ZC, 'headboard z': [round(HB_Z0, 3), round(HB_Z1, 3)], 'headboard top': HB_TOP,
                   'mattress x': [MAT_X0, MAT_X1], 'mattress z': [round(BED_ZC - BED_HALF, 3), round(BED_ZC + BED_HALF, 3)]},
           'nightstands z': [[round(a, 3), round(b, 3)] for a, b in NS_Z], 'nightstand top': NS_TOP, 'rug': list(RUG)}
    ctx.stats['primary_suite'] = res
    return res
