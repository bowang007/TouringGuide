"""Primary suite zone: primary bedroom (P0, P1) and open dressing area (S0, C0).

Design (1077 W McKinley language): serene, light, warm-white / white oak / walnut with black
accents and a single ochre note.

Bedroom (x 0.225-11.89, z 0.225-15.14): upholstered channel-tufted low platform bed centred on
the west-wall pier between W15 and W14, layered white linen bedding with turn-down, warm-grey
euro shams, ochre lumbar and an oatmeal knit throw; slim white-oak nightstands with ceramic
lamps (warm-white linen shades); one large original colour-field abstract canvas above the bed
(oak floater frame); walnut + boucle bench at the foot; 8x9 wool rug; low walnut dresser on the
retained south wall with a round black mirror and a few objects; full-length arch mirror and a
small matted watercolour print (anti-reflective glazing) on the east wall; leather lounge chair in
the north-east corner; potted tree in the north-west corner; slim inside-mount roller shades on
W01/W14/W15; flush LED ring light.

Dressing (x 0.225-11.89, z 15.50-20.92): floor-to-ceiling 24in fitted wardrobes (warm-white
lacquer, oak interiors) in the original L (north run x 0.29-6.20, west run z 17.50-20.86) keeping
the 41in aisle: one open double-hang section with colour-blocked shirts/jackets (real-thickness
garments, contoured walnut hangers on wrapped wire hooks) and trousers, one open shelf section
with drawers, folded knits and linen boxes, 4000K LED strips; flush doors with black bar pulls
elsewhere; full-height black-framed mirror on the south wall; 4700K recessed cans.

Shell workaround: the D10 and D08 jambs/soffits get exterior stucco from shell._wall_faces (their
probe points fall in the wall-thickness gap between two room regions), so thin paint skins cover
them here (see build_details); remove them once shell classifies those faces as interior.
"""
import math
import random
import time

import bpy
from mathutils import Matrix, Vector

from .. import assets, lighting
from ..common import FT, ft2bl, move_to_collection, world_bbox_ft
from . import primary_suite_art as ART
from . import primary_suite_garments as PG
from . import primary_suite_geo as G
from . import primary_suite_mats as M

ZONE = 'zone_primary_suite'
C_BED = 'ps_bedroom'
C_DRS = 'ps_dressing'
C_SOFT = 'ps_softgoods'
C_LIT = 'ps_lights'
C_MOD = 'ps_models'

# room datums (SCENE feet)
WEST = 0.225          # west wall interior face
NORTH = 0.225         # rear wall interior face
EAST = 11.89          # east wall interior face
SOUTH_B = 15.14       # retained wall face (bedroom side)
D_NORTH = 15.50       # retained wall face (dressing side)
D_SOUTH = 20.92       # ensuite / shared-bath wall face
CEIL = 8.0

BED_Z0, BED_Z1 = 4.85, 11.05     # pier between W15 (z<=4.75) and W14 (z>=11.15)
BED_ZC = (BED_Z0 + BED_Z1) / 2
RUG = (2.70, 10.70, 3.45, 12.45)  # x0, x1, z0, z1 (8 x 9 ft, centred on the bed)
RUG_TOP = 0.042

CAMS = {'P0': (9.5, 12.0), 'P1': (8.5, 14.0), 'S0': (8.65, 18.2), 'C0': (4.1, 19.3)}


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
    m['boucle'] = M.fabric('bench_boucle', '#ebe5da', rough=0.97, sheen=0.4, weave_scale=180, bump=0.9, kind='boucle')
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
    c = C_BED
    s = C_SOFT
    n = 0
    # headboard: backing panel + 8 vertical channels
    _box(ctx, 'ps headboard back', 0.30, 0.46, 0.04, 3.95, BED_Z0, BED_Z1, m['headboard'], c, bevel=0.04)
    nch = 8
    cw = (BED_Z1 - BED_Z0) / nch
    for k in range(nch):
        z0 = BED_Z0 + k * cw
        _box(ctx, f'ps headboard channel {k}', 0.42, 0.74, 0.30, 4.02, z0 + 0.006, z0 + cw - 0.006,
             m['headboard'], c, bevel=0.15, seg=6)
        n += 1
    # upholstered platform rail, recessed black plinth, mattress
    _box(ctx, 'ps bed rail', 0.74, 7.70, 0.28, 1.05, BED_Z0, BED_Z1, m['headboard'], c, bevel=0.08, seg=4)
    _box(ctx, 'ps bed plinth', 1.0, 7.40, 0.0, 0.28, BED_Z0 + 0.35, BED_Z1 - 0.35, m['blackpaint'], c)
    _box(ctx, 'ps mattress', 0.78, 7.64, 1.05, 1.90, 4.98, 10.92, m['sheet'], s, bevel=0.13, seg=5)
    n += 5
    mz0, mz1, mx1 = 4.98, 10.92, 7.64
    head = 2.45
    # duvet (drapes both sides and foot), turn-down band
    G.drape_sheet(ctx, 'ps duvet', 0.78, mx1, mz0, mz1, 1.905, head=head, drape_side=0.95, drape_foot=0.9,
                  radius=0.2, step=0.07, mat=m['duvet'], coll=s, thick=0.075, seed=11, fold_amp=0.03, top_amp=0.03)
    G.drape_sheet(ctx, 'ps duvet turn-down', 0.78, 3.30, mz0, mz1, 1.985, head=head, drape_side=0.95, drape_foot=0.0,
                  radius=0.28, step=0.07, mat=m['duvet'], coll=s, thick=0.07, seed=12, fold_amp=0.02, top_amp=0.012)
    # throw folded across the foot (concentric with the duvet's rounded edge)
    G.drape_sheet(ctx, 'ps throw', 0.78, 6.95, mz0, mz1, 2.035, head=5.70, drape_side=1.02, drape_foot=0.0,
                  radius=0.33, step=0.06, mat=m['throw'], coll=s, thick=0.055, seed=13, fold_amp=0.012, top_amp=0.01,
                  skew=0.012)
    n += 3
    # pillows: 2 euro shams, 2 sleeping pillows, 1 lumbar
    def lean(xb, yb, zc, w, h, t, ang_deg, mat, name, seed, squash=0.0):
        a = math.radians(ang_deg)
        V = Vector((-math.sin(a), math.cos(a), 0))
        N = Vector((math.cos(a), math.sin(a), 0))
        O = Vector((xb, yb, zc)) + V * (h / 2)
        return G.pillow(ctx, name, w, h, t, O, (0, 0, 1), V, N, mat, s, seed=seed, squash=squash)
    lean(1.26, 1.95, BED_ZC - 1.08, 2.12, 2.08, 0.52, 12, m['euro'], 'ps euro sham N', 21)
    lean(1.26, 1.95, BED_ZC + 1.08, 2.12, 2.08, 0.52, 13, m['euro'], 'ps euro sham S', 22)
    lean(2.08, 1.95, BED_ZC - 1.42, 2.80, 1.62, 0.48, 36, m['pillow'], 'ps pillow N', 23)
    lean(2.08, 1.95, BED_ZC + 1.42, 2.80, 1.62, 0.48, 38, m['pillow'], 'ps pillow S', 24)
    lean(2.78, 2.07, BED_ZC + 0.05, 2.70, 1.10, 0.40, 52, m['lumbar'], 'ps lumbar', 25)
    n += 5
    return n


def build_nightstands(ctx, m):
    c = C_BED
    n = 0
    x0, x1 = 0.30, 1.63
    top = 1.85
    stands = [(2.80, 4.60), (11.30, 13.10)]
    for k, (z0, z1) in enumerate(stands):
        tag = 'N' if k == 0 else 'S'
        _box(ctx, f'ps nightstand {tag} top', x0, x1, top - 0.08, top, z0, z1, m['oak'], c, bevel=0.012)
        _box(ctx, f'ps nightstand {tag} side a', x0, x1, 0.12, top - 0.08, z0, z0 + 0.06, m['oak'], c, bevel=0.006)
        _box(ctx, f'ps nightstand {tag} side b', x0, x1, 0.12, top - 0.08, z1 - 0.06, z1, m['oak'], c, bevel=0.006)
        _box(ctx, f'ps nightstand {tag} bottom', x0, x1, 0.12, 0.19, z0 + 0.06, z1 - 0.06, m['oak'], c, bevel=0.004)
        _box(ctx, f'ps nightstand {tag} back', x0, x0 + 0.04, 0.19, top - 0.08, z0 + 0.06, z1 - 0.06, m['oak'], c)
        _box(ctx, f'ps nightstand {tag} shelf', x0 + 0.04, x1 - 0.03, 1.10, 1.15, z0 + 0.06, z1 - 0.06, m['oak'], c)
        # drawer front (inset) with an under-lip finger reveal at the top
        _box(ctx, f'ps nightstand {tag} drawer', x1 - 0.06, x1, 1.17, top - 0.115, z0 + 0.068, z1 - 0.068,
             m['oak'], c, bevel=0.006)
        _box(ctx, f'ps nightstand {tag} drawer box', x0 + 0.06, x1 - 0.06, 1.17, top - 0.12, z0 + 0.08, z1 - 0.08,
             m['caseback'], c)
        _box(ctx, f'ps nightstand {tag} plinth', x0 + 0.1, x1 - 0.12, 0.0, 0.12, z0 + 0.1, z1 - 0.1, m['blackpaint'], c)
        n += 9
        zc = (z0 + z1) / 2
        lamp(ctx, m, 0.98, top, zc + (0.12 if k == 0 else -0.12), tag)
        n += 5
    # north stand: two books + small charcoal bud vase in the open niche
    zc = (stands[0][0] + stands[0][1]) / 2
    y = _book(ctx, 'ps nightstand book 1', 0.55, zc - 0.62, 0.19, 0.78, 0.98, 0.10, 0.04, m['book1'], m['pages'], c)
    _book(ctx, 'ps nightstand book 2', 0.58, zc - 0.58, y, 0.70, 0.90, 0.08, -0.06, m['book2'], m['pages'], c)
    # south stand: small book + low ceramic bowl on top
    zc = (stands[1][0] + stands[1][1]) / 2
    yb = _book(ctx, 'ps nightstand book 3', 0.48, zc + 0.08, top, 0.62, 0.78, 0.075, 0.12, m['book3'], m['pages'], c)
    G.lathe(ctx, 'ps nightstand bowl', [(0.0, 0.0), (0.11, 0.0), (0.17, 0.04), (0.2, 0.1), (0.205, 0.12),
                                        (0.19, 0.12), (0.155, 0.06), (0.0, 0.05)],
            (0.80, yb, zc + 0.48), m['vase_dark'], c, segs=48, cap_top=False, cap_bottom=False)
    n += 6
    return n


def lamp(ctx, m, x, y0, z, tag):
    c = C_BED
    prof = [(0.15, 0.0), (0.19, 0.015), (0.245, 0.10), (0.275, 0.28), (0.262, 0.50), (0.205, 0.70),
            (0.12, 0.83), (0.075, 0.89), (0.07, 0.93), (0.05, 0.95)]
    G.lathe(ctx, f'ps lamp {tag} base', prof, (x, y0, z), m['lampbase'], c, segs=64)
    _cyl(ctx, f'ps lamp {tag} neck', (x, y0 + 1.2, z), 0.018, 0.5, m['brass'], c, verts=16)
    _cyl(ctx, f'ps lamp {tag} socket', (x, y0 + 1.47, z), 0.055, 0.16, m['brass'], c, verts=24)
    sh = G.lathe(ctx, f'ps lamp {tag} shade', [(0.60, 1.26), (0.53, 2.06)], (x, y0, z), m['shade'], c,
                 segs=72, cap_top=False, cap_bottom=False)
    G.solidify(sh, 0.012, offset=0.0)
    # thin brass rims at the shade edges
    for yy, rr in ((1.26, 0.60), (2.06, 0.53)):
        G.lathe(ctx, f'ps lamp {tag} rim {yy}', [(rr - 0.004, yy - 0.006), (rr + 0.006, yy - 0.006),
                                                  (rr + 0.006, yy + 0.006), (rr - 0.004, yy + 0.006)],
                (x, y0, z), m['brass'], c, segs=72, cap_top=False, cap_bottom=False)
    lighting.point_light(ctx, x, y0 + 1.62, z, watts=2.0, kelvin=2700, radius_ft=0.12, coll=C_LIT,
                         name=f'ps lamp {tag}')


def build_art(ctx, m):
    c = C_BED
    img = ART.to_blender_image('Z_primary_suite_art_canvas', 1800, 1000, seed=7)
    mat = M.image_canvas('art_canvas', img)
    z0, z1 = BED_ZC - 2.25, BED_ZC + 2.25
    y0, y1 = 4.62, 7.12
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


def build_bench(ctx, m):
    c = C_BED
    x0, x1 = 8.10, 9.43
    z0, z1 = BED_ZC - 2.25, BED_ZC + 2.25
    y = RUG_TOP
    _box(ctx, 'ps bench end N', x0, x1, y, y + 1.22, z0, z0 + 0.13, m['walnut'], c, bevel=0.015)
    _box(ctx, 'ps bench end S', x0, x1, y, y + 1.22, z1 - 0.13, z1, m['walnut'], c, bevel=0.015)
    _box(ctx, 'ps bench seat board', x0 + 0.02, x1 - 0.02, y + 1.10, y + 1.22, z0 + 0.13, z1 - 0.13, m['walnut'], c, bevel=0.006)
    _box(ctx, 'ps bench shelf', x0 + 0.1, x1 - 0.1, y + 0.30, y + 0.37, z0 + 0.13, z1 - 0.13, m['walnut'], c, bevel=0.006)
    _box(ctx, 'ps bench cushion', x0 + 0.015, x1 - 0.015, y + 1.22, y + 1.56, z0 + 0.015, z1 - 0.015,
              m['boucle'], c, bevel=0.11, seg=6)
    return 5


def build_rug(ctx, m):
    x0, x1, z0, z1 = RUG
    _box(ctx, 'ps rug', x0, x1, 0.0005, RUG_TOP, z0, z1, m['rug'], C_BED, bevel=0.012, seg=2)
    return 1


def build_dresser(ctx, m):
    c = C_BED
    x0, x1 = 2.0, 6.0
    z0, z1 = 13.58, 15.08           # back clears the retained-wall baseboard (z 15.09)
    yb, yt = 0.24, 2.48
    _box(ctx, 'ps dresser plinth', x0 + 0.12, x1 - 0.12, 0.0, yb, z0 + 0.12, z1 - 0.1, m['blackpaint'], c)
    _box(ctx, 'ps dresser case', x0, x1, yb, yt, z0 + 0.03, z1, m['walnut'], c, bevel=0.01)
    _box(ctx, 'ps dresser top', x0 - 0.01, x1 + 0.01, yt, yt + 0.07, z0 - 0.005, z1, m['walnut'], c, bevel=0.012)
    n = 3
    cols = [(x0 + 0.03, (x0 + x1) / 2 - 0.012), ((x0 + x1) / 2 + 0.012, x1 - 0.03)]
    rows = [(yb + 0.03, yb + 0.74), (yb + 0.77, yb + 1.48), (yb + 1.51, yt - 0.03)]
    for ci, (a, b) in enumerate(cols):
        for ri, (r0, r1) in enumerate(rows):
            # slab front with a recessed finger-pull lip along its top edge
            _box(ctx, f'ps dresser front {ci}{ri}', a, b, r0, r1 - 0.07, z0, z0 + 0.03, m['walnut'], c, bevel=0.005)
            _box(ctx, f'ps dresser lip {ci}{ri}', a, b, r1 - 0.07, r1, z0 + 0.018, z0 + 0.03, m['walnut'], c)
            _box(ctx, f'ps dresser pull shadow {ci}{ri}', a + 0.01, b - 0.01, r1 - 0.066, r1 - 0.03, z0 + 0.016,
                 z0 + 0.018, m['blackpaint'], c)
            n += 3
    # objects on top: two stacked books + charcoal vase, sand vase
    top = yt + 0.07
    y = _book(ctx, 'ps dresser book 1', 2.55, z0 + 0.35, top, 1.05, 0.82, 0.13, 0.05, m['book1'], m['pages'], c)
    y = _book(ctx, 'ps dresser book 2', 2.62, z0 + 0.38, y, 0.92, 0.72, 0.10, -0.03, m['book3'], m['pages'], c)
    G.lathe(ctx, 'ps dresser small bowl', [(0.0, 0.0), (0.09, 0.0), (0.15, 0.035), (0.175, 0.09), (0.165, 0.09),
                                           (0.13, 0.04), (0.0, 0.035)], (3.05, y, z0 + 0.72), m['vase_sand'], c,
            segs=48, cap_top=False, cap_bottom=False)
    G.lathe(ctx, 'ps dresser vase tall', [(0.12, 0.0), (0.2, 0.06), (0.27, 0.35), (0.26, 0.62), (0.15, 0.95),
                                          (0.08, 1.15), (0.075, 1.32), (0.09, 1.36), (0.07, 1.36), (0.055, 1.2)],
            (5.05, top, z0 + 0.72), m['vase_dark'], c, segs=64, cap_top=False)
    G.lathe(ctx, 'ps dresser vase short', [(0.10, 0.0), (0.2, 0.05), (0.24, 0.25), (0.2, 0.5), (0.12, 0.62),
                                           (0.11, 0.66), (0.09, 0.66), (0.08, 0.6)],
            (5.62, top, z0 + 0.85), m['vase_sand'], c, segs=64, cap_top=False)
    # round mirror above (thin black frame)
    mx, my, mz = 4.0, 4.75, SOUTH_B
    rim = ctx.cylinder('ps round mirror frame', (mx, my, mz - 0.045), 1.25, 0.09, m['black'], c, verts=96, axis='Z')
    gl = ctx.cylinder('ps round mirror glass', (mx, my, mz - 0.093), 1.2, 0.012, m['mirror'], c, verts=96, axis='Z')
    n += 8
    return n


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
    """Matted, glazed watercolour print on the east wall between the arch mirror and the corner
    (thin matte-black frame, wide white mat with a weighted bottom, glass with real reflections).
    P0/P1 stand 2.4-3.4 ft from this wall, so it is kept modest in size."""
    c = C_BED
    img = ART.to_blender_image('Z_primary_suite_art_wash', 700, 1020, seed=33, variant='wash')
    paper = M.image_paper('art_wash_paper', img)
    matb = M.simple('mat_board', '#f4f2ed', rough=0.92)
    zc, yc = 12.30, 5.05
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
    # anti-reflective glazing just behind the frame lip (edges tucked into the frame bars); plain 4%
    # glass mirrored the bright W14 window straight behind P0 across the whole print
    _box(ctx, 'ps print glass', XF + 0.018, XF + 0.022, iy0 - 0.02, iy1 + 0.02, iz0 - 0.02, iz1 + 0.02,
         M.museum_glass(), c)
    return 12


def build_details(ctx, m):
    """Small real-world details: outlet on the bedroom east wall, rocker switch by the suite entry,
    a linear slot diffuser in the bedroom ceiling (1077 language)."""
    c = C_BED
    plate = M.simple('switch_plate', '#f2f0ec', rough=0.4)
    slot = M.simple('slot_diffuser_dark', '#26272a', rough=0.6)
    # duplex outlet, east wall (between mirror and art)
    _box(ctx, 'ps outlet plate', EAST - 0.02, EAST - 0.002, 1.0, 1.36, 10.36, 10.60, plate, c, bevel=0.008, seg=2)
    for k, yy in enumerate((1.12, 1.24)):
        _box(ctx, f'ps outlet face {k}', EAST - 0.026, EAST - 0.02, yy - 0.04, yy + 0.04, 10.43, 10.53, plate, c,
             bevel=0.004, seg=2)
    # rocker switch inside the suite entry (dressing east wall, north of D09)
    _box(ctx, 'ps switch plate', EAST - 0.02, EAST - 0.002, 3.85, 4.22, 16.30, 16.54, plate, C_DRS, bevel=0.008, seg=2)
    _box(ctx, 'ps switch rocker', EAST - 0.03, EAST - 0.02, 3.92, 4.15, 16.36, 16.48, plate, C_DRS, bevel=0.006, seg=2)
    # D10 jamb face and header soffit: shell gives them exterior stucco (their probe points fall in the
    # wall-thickness gap between the 'primary' and 'primary_dressing' regions) -> paint skin over them
    wall = ctx.mat('paint_wall')
    _box(ctx, 'ps D10 jamb paint skin', 6.2227, 6.2267, 0.0, 6.668, 15.1427, 15.5007, wall, c)
    _box(ctx, 'ps D10 soffit paint skin', 6.2267, 11.8897, 6.6655, 6.6695, 15.1427, 15.5007, wall, c)
    # same for D08 (bath entry, z 20.92-21.28): west jamb, the east-jamb strip north of the open door, soffit
    _box(ctx, 'ps D08 jamb W paint skin', 6.3134, 6.3174, 0.0, 6.668, 20.9193, 21.2773, wall, C_DRS)
    _box(ctx, 'ps D08 jamb E paint skin', 9.0943, 9.0983, 0.0, 6.668, 20.9193, 21.110, wall, C_DRS)
    _box(ctx, 'ps D08 soffit paint skin', 6.3174, 9.0943, 6.6655, 6.6695, 20.9193, 21.2773, wall, C_DRS)
    # linear slot diffuser near the rear window
    _box(ctx, 'ps slot diffuser trim', 3.6, 8.6, CEIL - 0.006, CEIL - 0.001, 1.52, 1.78, plate, c)
    _box(ctx, 'ps slot diffuser slot', 3.64, 8.56, CEIL - 0.008, CEIL - 0.006, 1.58, 1.72, slot, c)
    return 12


def build_shades(ctx, m):
    """Inside-mount slim roller shades, partly lowered."""
    c = C_BED
    n = 0
    # W15 (west wall, north): reveal x 0..0.225, clear z 1.40-4.65
    specs = [
        ('W15', 'z', 1.42, 4.63, 0.08, 0.22, 6.12),
        ('W14', 'z', 11.28, 14.52, 0.09, 0.22, 6.05),
        ('W01', 'x', 2.69, 9.45, 0.08, 0.22, 5.98),
    ]
    for tag, along, a0, a1, d0, d1, ybot in specs:
        ytop = 6.88
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
    x, z = 6.05, 7.70
    G.lathe(ctx, 'ps ring light body', [(0.0, 7.80), (0.70, 7.80), (0.76, 7.84), (0.76, 7.995), (0.0, 7.995)],
            (x, 0.0, z), m['trim'], c, segs=96)
    G.lathe(ctx, 'ps ring light diffuser', [(0.50, 7.792), (0.68, 7.792), (0.68, 7.801), (0.50, 7.801)],
            (x, 0.0, z), m['ring'], c, segs=96)
    return 2


def build_models(ctx, m, notes):
    n = 0
    # lounge chair (saddle leather + walnut shell) in the north-east corner, facing the room
    try:
        em, roots = _import(ctx, 'mid_century_lounge_chair', 'ps lounge chair')
        _place_on(em, roots, 10.05, 0.0, 2.25, rot=math.radians(-40), scale=0.95)
        notes['lounge_chair_extent'] = _true_extent(roots)
        n += len(roots)
    except Exception as e:  # pragma: no cover
        notes['lounge_chair_error'] = repr(e)
    # potted tree in the north-west corner, planter re-glazed warm stone
    try:
        em, roots = _import(ctx, 'potted_plant_01', 'ps corner tree')
        for r in roots:
            stack = [r]
            while stack:
                o = stack.pop()
                stack.extend(o.children)
                if o.type == 'MESH' and o.name.startswith('potted_plant_01_pot'):
                    o.data.materials.clear()
                    o.data.materials.append(m['pot'])
        _place_on(em, roots, 1.25, 0.0, 1.30, rot=math.radians(30), scale=1.0)
        notes['tree_extent'] = _true_extent(roots)
        n += len(roots)
    except Exception as e:  # pragma: no cover
        notes['tree_error'] = repr(e)
    return n


# ----------------------------------------------------------------------------- dressing
def build_dressing(ctx, m):
    c = C_DRS
    n = 0
    X0 = 0.29                    # carcass back/west (clears baseboard)
    ZB = 15.56                   # north-run back (clears baseboard)
    ZF = 17.50                   # north-run front plane
    XF = 2.225                   # west-run front plane
    XE = 6.20                    # north-run east end
    ZS = 20.86                   # west-run south end (clears baseboard)
    TOP = 7.99
    KICK = 0.33
    T = 0.06                     # panel thickness
    oak, cb, lac = m['oak'], m['caseback'], m['lacquer']

    # ---------------- north run
    _box(ctx, 'ps wardrobe N kick', X0, XE, 0.0, KICK, ZB, ZF - 0.12, m['blackpaint'], c)
    _box(ctx, 'ps wardrobe N back', X0, XE, KICK, TOP, ZB, ZB + 0.04, cb, c)
    _box(ctx, 'ps wardrobe N west side', X0, X0 + T, KICK, TOP, ZB, ZF, lac, c)
    _box(ctx, 'ps wardrobe N divider', 4.17, 4.23, KICK, TOP, ZB, ZF, lac, c, bevel=0.004)
    _box(ctx, 'ps wardrobe N east end', XE - T, XE, 0.0, TOP, ZB, ZF, lac, c, bevel=0.004)
    _box(ctx, 'ps wardrobe N top', X0, XE, TOP - 0.06, TOP, ZB, ZF, lac, c)
    n += 6
    # N1 open double-hang section (x 2.225-4.17, interior runs into the blind corner)
    _box(ctx, 'ps N1 floor', X0 + T, 4.17, KICK, KICK + T, ZB + 0.04, ZF, oak, c, bevel=0.004)
    _box(ctx, 'ps N1 top shelf', X0 + T, 4.17, 6.95, 7.02, ZB + 0.04, ZF - 0.02, oak, c, bevel=0.004)
    _box(ctx, 'ps N1 mid shelf', X0 + T, 4.17, 3.62, 3.68, ZB + 0.04, ZF - 0.02, oak, c, bevel=0.004)
    _box(ctx, 'ps N1 fascia', XF, 4.17, TOP - 0.42, TOP - 0.06, ZF - 0.06, ZF, lac, c, bevel=0.004)
    rod_z = 16.55
    for yy, tag in ((6.76, 'upper'), (3.43, 'lower')):
        _cyl(ctx, f'ps N1 rod {tag}', ((X0 + T + 4.17) / 2, yy, rod_z), 0.035, 4.17 - X0 - T - 0.02, m['black'], c,
             axis='X', verts=20)
    # LED strips under shelves (front edge)
    for yy in (6.95, 3.62):
        _box(ctx, f'ps N1 led {yy}', X0 + 0.1, 4.12, yy - 0.012, yy, ZF - 0.16, ZF - 0.12, m['led'], C_LIT)
    n += 8
    # garments: 8 pieces in a soft white -> oat -> sky -> sand gradient ending in two jackets (the
    # darkest a charcoal-grey, not black), hung from the open east end at uneven 0.25-0.4 ft centres
    # with smoothly varying yaw. primary_suite_garments builds real shirts / jackets (shoulders on the
    # hanger, sleeves, collar + placket or lapels) and trousers folded over slack bars.
    rnd = random.Random(42)
    upper = [('#f4f2ee', 'shirt'), ('#ece7dd', 'shirt'), ('#dcd3c4', 'shirt'), ('#f1f1ee', 'stripe'),
             ('#b7c5d2', 'shirt'), ('#d9ccb4', 'shirt'), ('#c2b294', 'jacket'), ('#6b6864', 'jacket')]
    sway = Vector((rnd.random() * 30, rnd.random() * 30, rnd.random() * 30))
    x_hi, x_lo = 4.17 - 0.05, X0 + T + 0.05          # usable rod span (inside faces of the section)
    top = 6.76 - 0.175                               # hanger neck height on the upper rod
    xg = x_hi - 0.16
    ph = rnd.uniform(0, 6.3)
    for i, (col, kind) in enumerate(upper):
        if i:
            xg -= rnd.uniform(0.25, 0.4)
        xi = xg + rnd.uniform(-0.02, 0.02)
        if xi < x_lo + 0.12:
            break
        if kind == 'jacket':
            mat = M.fabric(f'wool_{col[1:]}', col, rough=0.9, sheen=0.35, weave_scale=260, bump=0.32, tint_var=0.04)
            L, shw = rnd.uniform(2.6, 2.75), rnd.uniform(1.48, 1.58)
        else:
            mat = M.fabric(f'shirting_{col[1:]}{"_stripe" if kind == "stripe" else ""}', col, rough=0.82, sheen=0.5,
                           weave_scale=520, bump=0.18, tint_var=0.035)
            if kind == 'stripe':                     # sky-blue bengal stripe on white (stripes run down)
                M.stripe(mat, '#93acc7', axis='Y', period_in=0.5, duty=0.4)
                kind = 'shirt'
            L, shw = rnd.uniform(2.3, 2.6), rnd.uniform(1.3, 1.46)
        L = min(L, top - 3.75)                          # clear of the mid shelf (3.68)
        yaw = 0.05 * math.sin(0.9 * i + ph) + rnd.uniform(-0.02, 0.02)
        tip = min(0.66, shw / 2 - 0.05)
        _hanger(ctx, m, f'ps N1 up {i}', xi, 6.76, rod_z, yaw=yaw, tip=tip)
        hy = PG.hanger_curve(top, tip, 0.14 * (tip - 0.21) / 0.47)
        v, f = PG.garment(kind, (xi, rod_z), 'x', hy, L, shw, seed=100 + i, yaw=yaw, sway_off=sway, front=1)
        ob = G.mesh_ft(ctx, f'ps N1 garment up {i}', v, f, mat, c, smooth=True)
        G._fix_normals(ob)                           # also welds the shoulder seam
        G.solidify(ob, 0.009 if kind == 'jacket' else 0.007, 0.0)
        G.subsurf(ob, 1)
        n += 2
    tpal = ['#2f3134', '#c8bea9', '#454b57', '#e4ddcf', '#6f6b64', '#b6a789', '#8b8e93', '#d9d2c4',
            '#57534d', '#a39c90']
    xg = x_hi - 0.1
    for i, col in enumerate(tpal):
        if i:
            xg -= rnd.uniform(0.17, 0.24)
        if xg < x_lo + 0.12:
            break
        mat = M.fabric(f'cloth_{col[1:]}', col, rough=0.85, sheen=0.4, weave_scale=480, bump=0.25, tint_var=0.04,
                       wrinkle=0.2)
        yaw = 0.04 * math.sin(0.9 * i + 2.0) + rnd.uniform(-0.015, 0.015)
        _hanger(ctx, m, f'ps N1 low {i}', xg, 3.43, rod_z, bar=True, yaw=yaw)
        sh_y = 3.43 - 0.13
        v, f = PG.trousers((xg, rod_z), 'x', sh_y, rnd.uniform(1.12, 1.38), rnd.uniform(1.45, 1.75),
                           rnd.uniform(0.28, 0.33), seed=300 + i, yaw=yaw, sway_off=sway, front=1)
        ob = G.mesh_ft(ctx, f'ps N1 trousers {i}', v, f, mat, c, smooth=True)
        G._fix_normals(ob)
        G.subsurf(ob, 1)
        n += 2
    # linen boxes on the N1 floor and on the top shelf
    for i, (a, b) in enumerate(((2.32, 3.20), (3.25, 4.10))):
        _linen_box(ctx, m, f'ps N1 floor box {i}', a, b, KICK + T, KICK + T + 0.82, ZF - 1.45, ZF - 0.12)
    for i, (a, b) in enumerate(((2.35, 3.22), (3.27, 4.12))):
        _linen_box(ctx, m, f'ps N1 top box {i}', a, b, 7.02, 7.62, ZF - 1.4, ZF - 0.15)
    n += 4
    # N2 closed tall door with black bar pull
    _box(ctx, 'ps N2 door', 4.24, XE - T - 0.01, KICK + 0.02, TOP - 0.02, ZF - 0.06, ZF, lac, c, bevel=0.006)
    _bar_pull(ctx, m, 'ps N2 pull', 4.42, 3.6, ZF, 'z')
    n += 2

    # ---------------- west run (front plane x = 2.225)
    _box(ctx, 'ps wardrobe W kick', X0, XF - 0.12, 0.0, KICK, ZF, ZS, m['blackpaint'], c)
    _box(ctx, 'ps wardrobe W back', X0, X0 + 0.04, KICK, TOP, ZF, ZS, cb, c)
    _box(ctx, 'ps wardrobe W north side', X0, XF, KICK, TOP, ZF, ZF + T, lac, c, bevel=0.004)
    _box(ctx, 'ps wardrobe W divider', X0, XF, KICK, TOP, 19.17, 19.23, lac, c, bevel=0.004)
    _box(ctx, 'ps wardrobe W south end', X0, XF, 0.0, TOP, ZS - T, ZS, lac, c, bevel=0.004)
    _box(ctx, 'ps wardrobe W top', X0, XF, TOP - 0.06, TOP, ZF, ZS, lac, c)
    n += 6
    # W1 open: 3 drawers + 5 shelves with folded knits and boxes
    za, zb = ZF + T, 19.17
    drows = [(KICK + 0.03, 0.98), (1.01, 1.64), (1.67, 2.28)]
    for i, (r0, r1) in enumerate(drows):
        _box(ctx, f'ps W1 drawer {i}', XF - 0.06, XF, r0, r1 - 0.06, za + 0.008, zb - 0.008, oak, c, bevel=0.005)
        _box(ctx, f'ps W1 drawer lip {i}', XF - 0.06, XF - 0.02, r1 - 0.06, r1, za + 0.008, zb - 0.008, oak, c)
        _box(ctx, f'ps W1 drawer shadow {i}', XF - 0.022, XF - 0.02, r1 - 0.056, r1 - 0.025, za + 0.02, zb - 0.02,
             m['blackpaint'], c)
        n += 3
    shelves = [2.30, 3.22, 4.14, 5.06, 5.98, 6.90]
    for yy in shelves:
        _box(ctx, f'ps W1 shelf {yy}', X0 + 0.04, XF - 0.02, yy, yy + 0.06, za, zb, oak, c, bevel=0.004)
        if yy > 2.5:
            _box(ctx, f'ps W1 led {yy}', XF - 0.17, XF - 0.13, yy - 0.012, yy, za + 0.04, zb - 0.04, m['led'], C_LIT)
        n += 2
    knit = ['#e8e2d6', '#c9b89c', '#8f8b84', '#f0ede6', '#3e3f42', '#b9a07a', '#2f3746', '#d9d4ca']
    stacks = [
        (2.36, 17.68, [0, 6, 1]),          # on the drawers
        (3.28, 18.12, [3, 3, 7, 3]),       # tees
        (4.20, 17.70, [4, 2, 0]),
        (5.12, 18.08, [5, 1, 6]),
    ]
    for si, (yb, zs0, seq) in enumerate(stacks):
        y = yb + 0.06
        for k, ci in enumerate(seq):
            col = knit[ci]
            mat = M.fabric(f'knit_{col[1:]}', col, rough=0.95, sheen=0.5, weave_scale=420, bump=0.7, kind='knit')
            h = rnd.uniform(0.15, 0.19)
            G.folded_item(ctx, f'ps W1 folded {si}.{k}', 1.32 + rnd.uniform(-0.03, 0.03), y,
                          zs0 + 0.47 + rnd.uniform(-0.03, 0.03), 1.0, 0.94, h, rnd.uniform(-0.035, 0.035), mat, c)
            y += h - 0.005
            n += 2
    _linen_box(ctx, m, 'ps W1 box a', 0.45, 2.05, 6.04, 6.74, 17.62, 18.36)
    _linen_box(ctx, m, 'ps W1 box b', 0.45, 2.05, 6.04, 6.74, 18.42, 19.12)
    _linen_box(ctx, m, 'ps W1 box c', 0.45, 2.05, 6.96, 7.62, 17.72, 18.92)
    n += 3
    # W2 closed tall door
    _box(ctx, 'ps W2 door', XF - 0.06, XF, KICK + 0.02, TOP - 0.02, 19.24, ZS - T - 0.01, lac, c, bevel=0.006)
    _bar_pull(ctx, m, 'ps W2 pull', XF, 3.6, 19.42, 'x')
    n += 2

    # ---------------- full-height mirror on the south wall of the aisle
    mx0, mx1 = 3.30, 5.70
    my0, my1 = 0.55, 7.25
    fz0, fz1 = D_SOUTH - 0.07, D_SOUTH - 0.002
    fw = 0.07
    _box(ctx, 'ps dressing mirror glass', mx0 + 0.02, mx1 - 0.02, my0 + 0.02, my1 - 0.02, fz0 + 0.01, fz0 + 0.03,
         m['mirror'], c)
    _box(ctx, 'ps dressing mirror back', mx0 + 0.04, mx1 - 0.04, my0 + 0.04, my1 - 0.04, fz0 + 0.03, fz1, m['blackpaint'], c)
    _box(ctx, 'ps dressing mirror frame top', mx0, mx1, my1 - fw, my1, fz0, fz1, m['black'], c, bevel=0.006)
    _box(ctx, 'ps dressing mirror frame bottom', mx0, mx1, my0, my0 + fw, fz0, fz1, m['black'], c, bevel=0.006)
    _box(ctx, 'ps dressing mirror frame W', mx0, mx0 + fw, my0, my1, fz0, fz1, m['black'], c, bevel=0.006)
    _box(ctx, 'ps dressing mirror frame E', mx1 - fw, mx1, my0, my1, fz0, fz1, m['black'], c, bevel=0.006)
    n += 6
    return n


def _hanger(ctx, m, name, x, rod_y, rod_z, bar=False, yaw=0.0, rod_r=0.035, tip=0.66):
    """Slim walnut hanger: black wire hook wrapped over the rod + contoured shoulder bar (tips at
    +/-tip, just inside the garment's shoulder seams), or a single slack bar for trousers."""
    c = C_DRS
    sh_y = rod_y - 0.13
    if bar:     # open-ended slack (trouser) hanger: the trousers fold over this single bar
        G.tube(ctx, name + ' hook', G.hook_path(x, rod_y, rod_z, rod_r, sh_y + 0.015), 0.011, m['black'], c, segs=8)
        ctx.box_c(name + ' bar', (x, sh_y, rod_z), (0.036, 0.036, 1.22), yaw, m['walnut'], c, bevel=0.014,
                  segments=2)
        return
    # contoured shirt hanger following the garment's neck-and-shoulder line (PG.garment)
    top = rod_y - 0.14 - 0.035
    hy = PG.hanger_curve(top, tip, 0.14 * (tip - 0.21) / 0.47)
    pts = []
    for k in range(-12, 13):
        d = tip * k / 12
        pts.append((x + d * math.sin(yaw), hy(d), rod_z + d * math.cos(yaw)))
    G.tube(ctx, name + ' shoulders', pts, 0.021, m['walnut'], c, segs=10)
    G.tube(ctx, name + ' hook', G.hook_path(x, rod_y, rod_z, rod_r, top), 0.011, m['black'], c, segs=8)


def _bar_pull(ctx, m, name, a, yc, b, face):
    """Vertical matte-black bar pull (1.5ft) on standoffs. face 'z': door faces +z at z=b, pull at x=a.
    face 'x': door faces +x at x=a, pull at z=b."""
    c = C_DRS
    L, off = 1.5, 0.11
    if face == 'z':
        _cyl(ctx, name, (a, yc, b + off), 0.022, L, m['black'], c, axis='Y', verts=20)
        for s in (-1, 1):
            _cyl(ctx, name + f' standoff {s}', (a, yc + s * (L / 2 - 0.12), b + off / 2), 0.014, off, m['black'], c,
                 axis='Z', verts=12)
    else:
        _cyl(ctx, name, (a + off, yc, b), 0.022, L, m['black'], c, axis='Y', verts=20)
        for s in (-1, 1):
            _cyl(ctx, name + f' standoff {s}', (a + off / 2, yc + s * (L / 2 - 0.12), b), 0.014, off, m['black'], c,
                 axis='X', verts=12)


def _linen_box(ctx, m, name, x0, x1, y0, y1, z0, z1):
    c = C_DRS
    _box(ctx, name, x0, x1, y0, y1, z0, z1, m['linenbox'], c, bevel=0.025, seg=3)
    # leather pull tab on the visible face (largest-x face for west-run, +z face for north-run)
    if (x1 - x0) > (z1 - z0) + 0.2:      # deep box seen from +x? (west run) -> tab on +x face
        ctx.box_c(name + ' tab', (x1 + 0.006, (y0 + y1) / 2 + 0.08, (z0 + z1) / 2), (0.012, 0.09, 0.3), 0.0,
                  m['leather'], c, bevel=0.004, segments=2)
    else:
        ctx.box_c(name + ' tab', ((x0 + x1) / 2, (y0 + y1) / 2 + 0.08, z1 + 0.006), (0.3, 0.09, 0.012), 0.0,
                  m['leather'], c, bevel=0.004, segments=2)


def build_dressing_lights(ctx):
    for x, z in ((3.25, 19.15), (5.25, 19.15), (9.05, 18.20)):
        lighting.can(ctx, x, z, coll=C_LIT, kelvin=4700, watts=8.0)
    return 3


# ----------------------------------------------------------------------------- checks
def _camera_clearance(ctx, notes):
    """Report any zone mesh within 1.2 ft (plan) of a camera stop below y=6.5."""
    bad = []
    for ob in ctx.coll(ZONE).all_objects:
        if ob.type != 'MESH':
            continue
        try:
            bb = world_bbox_ft([ob])
        except ValueError:
            continue
        for cid, (cx, cz) in CAMS.items():
            if bb[2] > 6.5 or bb[3] < 0.1:      # above the clearance volume / floor-level (rug)
                continue
            if bb[0] - 1.2 < cx < bb[1] + 1.2 and bb[4] - 1.2 < cz < bb[5] + 1.2:
                bad.append((cid, ob.name))
    notes['camera_conflicts'] = bad


def _triangles(ctx):
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    seen = set()
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
    counts['bench'] = build_bench(ctx, m)
    counts['rug'] = build_rug(ctx, m)
    counts['dresser'] = build_dresser(ctx, m)
    counts['shades'] = build_shades(ctx, m)
    counts['east_mirror'] = build_east_mirror(ctx, m)
    counts['east_art'] = build_east_art(ctx, m)
    counts['details'] = build_details(ctx, m)
    counts['ceiling_light'] = build_ceiling_light(ctx, m)
    counts['models'] = build_models(ctx, m, notes)
    counts['dressing'] = build_dressing(ctx, m)
    counts['dressing_lights'] = build_dressing_lights(ctx)
    bpy.context.view_layer.update()
    _camera_clearance(ctx, notes)
    objs = [o for o in ctx.coll(ZONE).all_objects]
    res = {'objects': len(objs), 'triangles': _triangles(ctx), 'seconds': round(time.time() - t0, 1),
           'parts': counts, 'notes': notes}
    ctx.stats['primary_suite'] = res
    return res
