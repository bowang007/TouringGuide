"""Modern kitchen for the kitchen_dining zone: walnut slab cabinetry with finger-pull channels,
Calacatta quartz worktops and full-height backsplash, stainless column fridge + stacked wall
ovens, induction cooktop under a white plaster hood, undermount sink with a matte-black faucet,
waterfall island with leather counter stools and a linear LED pendant.

All numbers are SCENE feet. Plan anchors (from data/scene.json layout_revision and the
original fixtures):
  south (garage) wall face z=31.41, east wall face x=40.61, flat ceiling y=8.0
  south counter front z=29.13, east counter front x=38.405
  island worktop x 28.4-34.4, z 22-25, top 36in; base 5.8 x 1.92 centred (31.4, 23.96)
  stools (29.4|31.4|33.4, 21.7); pendant centres (30, 23.5) and (32.8, 23.5)
  W08 window z 23.387-29.387, sill 3.15 (sink centred at z 26.387); W07 ends at z 21.814
  original fridge x 22.68-25.48 (tall units), cooktop centred x 34.8
"""
import math

from .kitchen_dining_geo import Geo, principled, srgb

# ----------------------------------------------------------------------------- constants
WALL_S = 31.41
WALL_E = 40.61
CEIL = 8.0
TOP = 3.0                 # finished counter height (36in)
CT_T = 0.1                # perimeter worktop thickness (1.2in)
CT_UNDER = TOP - CT_T     # 2.9
SPL = 0.06                # quartz backsplash slab thickness
FT_T = 0.0625             # 3/4in slab fronts
GAP = 0.011               # reveal between fronts (~1/8in)
TOE_H = 0.333             # toe-kick height (4in)
TOE_D = 0.25              # toe-kick recess (3in)
CT_FRONT_S = 29.13
FRONT_S = 29.21           # face of south-run fronts
CT_FRONT_E = 38.405
FRONT_E = 38.488          # face of east-run fronts
RUN_E0 = 21.84            # north end of the east run (W07 jamb)
TALL_X0 = 22.60           # outer face of the tall-bank end panel
FRIDGE = (22.6625, 25.6625)
OVEN = (25.6625, 28.10)
BASE_X0 = 28.1625
HOOD = (33.2, 36.4)
UPPER_Y0 = 4.75
UPPER_FRONT = 30.2675     # face of the upper doors
SINK_Z = 26.387
SINK_X = (38.68, 40.02)   # undermount bowl (x), 16in front-to-back
SINK_HALF_Z = 1.25        # 30in long bowl
SINK_BOTTOM = 2.15        # bowl floor (9in deep)
# finger-pull channel layout (y): bottom front | channel | top drawer | channel | worktop
Y_LO0, Y_LO1 = TOE_H + 0.012, 1.93
Y_CH0, Y_CH1 = 1.93, 2.06
Y_HI0, Y_HI1 = 2.06, 2.74

COLL = 'kd_kitchen'



STOOLS = True        # kitchen_dining turns them off when the dining table stands at the island

def _mats():
    return {
        'black_glass': principled('black_glass', srgb('#060607'), 0.04, coat=0.0),
        'cooktop_mark': principled('cooktop_mark', srgb('#3a3a3a'), 0.35),
        'oven_cavity': principled('oven_cavity', srgb('#101010'), 0.3),
        'rubber': principled('rubber', srgb('#0d0d0d'), 0.6),
        'led': None,
    }


def build(ctx, g: Geo):
    from ..lighting import emitter
    M = _mats()
    M['led'] = emitter('kd_led_strip', 3000, 25.0)
    col = g.sub(COLL)
    lights = g.sub('kd_lights')
    notes = []

    # ======================================================================= tall bank
    # finished walnut end panel (exposed to the hall), floor to ceiling
    g.box('kd tall end panel', TALL_X0, TALL_X0 + FT_T, 0.0, CEIL - 0.005, FRONT_S - 0.0, WALL_S, 'walnut_slab', 0.006, coll=col)
    # carcass behind fronts
    g.box('kd tall carcass', FRIDGE[0], OVEN[1], 0.0, CEIL - 0.005, FRONT_S + FT_T + 0.01, WALL_S, 'walnut_slab', coll=col)
    g.box('kd tall plinth', FRIDGE[0], OVEN[1], 0.0, TOE_H, FRONT_S + 0.06, FRONT_S + FT_T + 0.02, 'paint_black', coll=col)
    # --- integrated stainless column fridge (over-under), walnut flipper above
    fx0, fx1 = FRIDGE
    zf0, zf1 = FRONT_S - 0.02, FRONT_S + FT_T
    g.box('kd fridge grille', fx0 + 0.04, fx1 - 0.04, 0.03, TOE_H, FRONT_S + 0.03, FRONT_S + 0.05, M['rubber'], coll=col)
    g.box('kd fridge freezer drawer', fx0 + GAP, fx1 - GAP, TOE_H + 0.012, 2.42, zf0, zf1, 'stainless', 0.012, coll=col)
    g.box('kd fridge door', fx0 + GAP, fx1 - GAP, 2.42 + GAP, 6.92, zf0, zf1, 'stainless', 0.012, coll=col)
    g.box('kd fridge top door', fx0 + GAP, fx1 - GAP, 6.92 + GAP, CEIL - 0.012, FRONT_S, FRONT_S + FT_T, 'walnut_slab', 0.006, coll=col)
    # bar handles (round stainless on stand-offs)
    hz = zf0 - 0.12
    g.cyl_axis('kd fridge handle', (fx0 + 0.32, 3.45, hz), (fx0 + 0.32, 5.85, hz), 0.035, 'stainless', coll=col)
    for yy in (3.6, 5.7):
        g.cyl_axis('kd fridge handle post', (fx0 + 0.32, yy, zf0 + 0.005), (fx0 + 0.32, yy, hz), 0.022, 'stainless', coll=col)
    g.cyl_axis('kd freezer handle', (fx0 + 0.45, 2.2, hz), (fx1 - 0.45, 2.2, hz), 0.035, 'stainless', coll=col)
    for xx in (fx0 + 0.6, fx1 - 0.6):
        g.cyl_axis('kd freezer handle post', (xx, 2.2, zf0 + 0.005), (xx, 2.2, hz), 0.022, 'stainless', coll=col)
    # --- stacked wall ovens in a walnut tower
    ox0, ox1 = OVEN
    g.box('kd oven tower drawer', ox0 + GAP, ox1 - GAP, TOE_H + 0.012, 1.55, FRONT_S, FRONT_S + FT_T, 'walnut_slab', 0.006, coll=col)
    g.box('kd oven tower top door', ox0 + GAP, ox1 - GAP, 6.02, CEIL - 0.012, FRONT_S, FRONT_S + FT_T, 'walnut_slab', 0.006, coll=col)
    for k, (oy0, oy1) in enumerate(((1.58, 3.78), (3.80, 6.0))):
        g.box(f'kd oven {k} frame', ox0 + 0.02, ox1 - 0.02, oy0, oy1, FRONT_S - 0.01, FRONT_S + FT_T, 'stainless', 0.01, coll=col)
        g.box(f'kd oven {k} door glass', ox0 + 0.07, ox1 - 0.07, oy0 + 0.06, oy1 - 0.34, FRONT_S - 0.025, FRONT_S - 0.005,
              M['black_glass'], 0.008, coll=col)
        g.box(f'kd oven {k} controls', ox0 + 0.07, ox1 - 0.07, oy1 - 0.24, oy1 - 0.05, FRONT_S - 0.02, FRONT_S - 0.005,
              M['black_glass'], 0.006, coll=col)
        hy = oy1 - 0.42
        g.cyl_axis(f'kd oven {k} handle', (ox0 + 0.25, hy, FRONT_S - 0.14), (ox1 - 0.25, hy, FRONT_S - 0.14), 0.03, 'stainless', coll=col)
        for xx in (ox0 + 0.35, ox1 - 0.35):
            g.cyl_axis(f'kd oven {k} handle post', (xx, hy, FRONT_S - 0.02), (xx, hy, FRONT_S - 0.14), 0.018, 'stainless', coll=col)
    # finished side panel facing the counter (between tall bank front and wall)
    g.box('kd tall side panel', OVEN[1], BASE_X0, 0.0, CEIL - 0.005, FRONT_S, WALL_S, 'walnut_slab', 0.006, coll=col)

    # ===================================================================== base runs
    # carcasses (hidden behind fronts; walnut where reveals show)
    g.box('kd south carcass', BASE_X0, WALL_E, TOE_H, CT_UNDER, FRONT_S + FT_T + 0.012, WALL_S, 'walnut_slab', coll=col)
    # east carcass is split around the undermount bowl: a solid box here would fill the sink and
    # show its walnut top through the worktop cut-out
    ex0, ez0, ez1 = FRONT_E + FT_T + 0.012, RUN_E0 + FT_T, FRONT_S + FT_T + 0.012
    s_z0, s_z1 = SINK_Z - SINK_HALF_Z - 0.03, SINK_Z + SINK_HALF_Z + 0.03
    g.box('kd east carcass n', ex0, WALL_E, TOE_H, CT_UNDER, ez0, s_z0, 'walnut_slab', coll=col)
    g.box('kd east carcass s', ex0, WALL_E, TOE_H, CT_UNDER, s_z1, ez1, 'walnut_slab', coll=col)
    g.box('kd east carcass sink floor', ex0, WALL_E, TOE_H, SINK_BOTTOM - 0.05, s_z0, s_z1, 'walnut_slab', coll=col)
    g.box('kd east carcass sink rail', ex0, SINK_X[0] - 0.03, SINK_BOTTOM - 0.05, CT_UNDER, s_z0, s_z1, 'walnut_slab', coll=col)
    g.box('kd east carcass sink back', SINK_X[1] + 0.03, WALL_E, SINK_BOTTOM - 0.05, CT_UNDER, s_z0, s_z1, 'walnut_slab', coll=col)
    # toe-kick plinths (matte black so the LED glow reads)
    g.box('kd south plinth', BASE_X0, WALL_E, 0.0, TOE_H, FRONT_S + TOE_D, WALL_S, 'paint_black', coll=col)
    g.box('kd east plinth', FRONT_E + TOE_D, WALL_E, 0.0, TOE_H, RUN_E0 + FT_T, FRONT_S + TOE_D, 'paint_black', coll=col)
    # exposed walnut end panel at the north end of the east run
    g.box('kd east end panel', FRONT_E - 0.0, WALL_E, 0.0, CT_UNDER, RUN_E0, RUN_E0 + FT_T, 'walnut_slab', 0.006, coll=col)
    # finger-pull channels (recessed black aluminium profiles)
    ch_s = FRONT_S + FT_T + 0.004
    ch_e = FRONT_E + FT_T + 0.004
    for (y0, y1, tag) in ((Y_CH0, Y_CH1, 'mid'), (Y_HI1, CT_UNDER, 'top')):
        g.box(f'kd south channel {tag}', BASE_X0, 38.55, y0, y1, ch_s, ch_s + 0.03, 'black_metal', coll=col)
        g.box(f'kd east channel {tag}', ch_e, ch_e + 0.03, y0, y1, RUN_E0 + FT_T, 29.30, 'black_metal', coll=col)

    def fronts_south(x0, x1, name, split=True):
        z0, z1 = FRONT_S, FRONT_S + FT_T
        if split:
            g.box(f'{name} lower', x0 + GAP / 2, x1 - GAP / 2, Y_LO0, Y_LO1, z0, z1, 'walnut_slab', 0.006, coll=col)
            g.box(f'{name} drawer', x0 + GAP / 2, x1 - GAP / 2, Y_HI0, Y_HI1, z0, z1, 'walnut_slab', 0.006, coll=col)
        else:
            g.box(f'{name} panel', x0 + GAP / 2, x1 - GAP / 2, Y_LO0, Y_HI1, z0, z1, 'walnut_slab', 0.006, coll=col)

    def fronts_east(z0, z1, name, split=True, lower_split=None):
        x0, x1 = FRONT_E, FRONT_E + FT_T
        if split:
            if lower_split:
                zm = lower_split
                g.box(f'{name} door a', x0, x1, Y_LO0, Y_LO1, z0 + GAP / 2, zm - GAP / 2, 'walnut_slab', 0.006, coll=col)
                g.box(f'{name} door b', x0, x1, Y_LO0, Y_LO1, zm + GAP / 2, z1 - GAP / 2, 'walnut_slab', 0.006, coll=col)
            else:
                g.box(f'{name} lower', x0, x1, Y_LO0, Y_LO1, z0 + GAP / 2, z1 - GAP / 2, 'walnut_slab', 0.006, coll=col)
            g.box(f'{name} drawer', x0, x1, Y_HI0, Y_HI1, z0 + GAP / 2, z1 - GAP / 2, 'walnut_slab', 0.006, coll=col)
        else:
            g.box(f'{name} panel', x0, x1, Y_LO0, Y_HI1, z0 + GAP / 2, z1 - GAP / 2, 'walnut_slab', 0.006, coll=col)

    for i, (x0, x1) in enumerate(((BASE_X0, 30.70), (30.70, 33.30), (33.30, 36.30), (36.30, 38.40))):
        fronts_south(x0, x1, f'kd south unit {i}')
    g.box('kd corner filler a', 38.40, FRONT_E + FT_T, Y_LO0, Y_HI1, FRONT_S, FRONT_S + FT_T, 'walnut_slab', coll=col)
    g.box('kd corner filler b', FRONT_E, FRONT_E + FT_T, Y_LO0, Y_HI1, 29.12, FRONT_S + FT_T, 'walnut_slab', coll=col)
    fronts_east(RUN_E0 + FT_T, 22.887, 'kd east pullout')
    fronts_east(22.887, 24.887, 'kd dishwasher', split=False)
    fronts_east(24.887, 27.887, 'kd sink base', lower_split=SINK_Z)
    fronts_east(27.887, 29.12, 'kd east drawers')

    # toe-kick LED (area lights under the fronts) + under-counter glow
    g.area_light('kd toe led south', (BASE_X0 + 38.4) / 2, TOE_H - 0.02, FRONT_S + 0.10, 38.4 - BASE_X0, 0.05, 1.4, 2900, lights,
                 spread_deg=110)
    g.area_light('kd toe led east', FRONT_E + 0.10, TOE_H - 0.02, (RUN_E0 + 29.2) / 2, 0.05, 29.2 - RUN_E0, 1.1, 2900, lights,
                 spread_deg=110)

    # ====================================================================== worktop
    pts = [(BASE_X0, CT_FRONT_S), (CT_FRONT_E, CT_FRONT_S), (CT_FRONT_E, RUN_E0 - 0.02), (WALL_E - SPL, RUN_E0 - 0.02),
           (WALL_E - SPL, WALL_S - SPL), (BASE_X0, WALL_S - SPL)]
    top = g.poly_prism('kd worktop', pts, CT_UNDER, TOP, 'quartz_calacatta', coll=col)
    # undermount sink cut-out (rounded rectangle)
    sx0, sx1 = SINK_X
    sz0, sz1 = SINK_Z - SINK_HALF_Z, SINK_Z + SINK_HALF_Z
    cut = g.poly_prism('kd sink cutter', _rrect(sx0, sx1, sz0, sz1, 0.09), CT_UNDER - 0.2, TOP + 0.2, None, coll=col)
    g.boolean_cut(top, cut)
    g.bevel_mod(top, 0.012, 2, harden=True)
    top.data.shade_smooth()
    try:
        top.data.set_sharp_from_angle(angle=math.radians(30))
    except Exception:
        pass

    # ===================================================================== backsplash
    bs = 'quartz_calacatta'
    zb0, zb1 = WALL_S - SPL, WALL_S
    g.box('kd splash south a', BASE_X0, HOOD[0], TOP, UPPER_Y0, zb0, zb1, bs, 0.004, coll=col)
    g.box('kd splash south hood', HOOD[0], HOOD[1], TOP, 5.52, zb0, zb1, bs, 0.004, coll=col)
    g.box('kd splash south shelves', HOOD[1], WALL_E - SPL, TOP, CEIL - 0.004, zb0, zb1, bs, 0.004, coll=col)
    xe0, xe1 = WALL_E - SPL, WALL_E
    g.box('kd splash east south pier', xe0, xe1, TOP, CEIL - 0.004, 29.387, WALL_S, bs, 0.004, coll=col)
    g.box('kd splash east ledge', xe0, xe1, TOP, 3.088, 23.387, 29.387, bs, 0.003, coll=col)
    g.box('kd splash east north pier', xe0, xe1, TOP, CEIL - 0.004, RUN_E0 - 0.02, 23.387, bs, 0.004, coll=col)

    # ====================================================================== uppers
    ux0, ux1 = BASE_X0, HOOD[0]
    g.box('kd upper carcass', ux0, ux1, UPPER_Y0, CEIL - 0.004, UPPER_FRONT + FT_T + 0.006, WALL_S, 'walnut_slab', coll=col)
    n = 3
    w = (ux1 - ux0) / n
    for i in range(n):
        a, b = ux0 + i * w, ux0 + (i + 1) * w
        g.box(f'kd upper door {i}', a + GAP / 2, b - GAP / 2, UPPER_Y0, CEIL - 0.014, UPPER_FRONT, UPPER_FRONT + FT_T,
              'walnut_slab', 0.006, coll=col)
    g.area_light('kd under-upper led', (ux0 + ux1) / 2, UPPER_Y0 - 0.02, UPPER_FRONT + 0.25, ux1 - ux0 - 0.2, 0.05, 6.0, 3000, lights)
    g.box('kd under-upper led strip', ux0 + 0.05, ux1 - 0.05, UPPER_Y0 - 0.008, UPPER_Y0, UPPER_FRONT + 0.18, UPPER_FRONT + 0.22,
          M['led'], coll=col)

    # ======================================================================= hood
    hx0, hx1 = HOOD
    g.box('kd hood plaster', hx0, hx1, 5.52, CEIL - 0.003, 29.70, WALL_S, 'plaster_white', 0.02, 3, coll=col)
    g.box('kd hood filter', hx0 + 0.18, hx1 - 0.18, 5.505, 5.53, 29.88, WALL_S - 0.2, 'stainless', 0.004, coll=col)
    for xx in (hx0 + 0.7, hx1 - 0.7):
        g.cyl('kd hood lamp lens', xx, 5.505, 5.525, 29.80, 0.07, M['led'], 24, coll=col)
    g.area_light('kd hood task light', (hx0 + hx1) / 2, 5.49, 30.45, 2.4, 0.8, 7.0, 3000, lights)

    # ============================================================ floating shelves
    for k, ys in enumerate((4.86, 6.24)):
        g.box(f'kd shelf {k}', HOOD[1] + 0.16, WALL_E - SPL, ys, ys + 0.167, 30.50, WALL_S - SPL, 'walnut_slab', 0.01, coll=col)
        g.box(f'kd shelf {k} led', HOOD[1] + 0.22, WALL_E - SPL - 0.05, ys - 0.006, ys + 0.002, 30.56, 30.60, M['led'], coll=col)
        g.area_light(f'kd shelf {k} light', (HOOD[1] + 0.16 + WALL_E - SPL) / 2, ys - 0.012, 30.62,
                     WALL_E - SPL - HOOD[1] - 0.3, 0.05, 3.5, 3000, lights)

    # =================================================================== cooktop
    cx0, cx1, cz0, cz1 = 33.55, 36.05, 29.40, 31.08
    g.box('kd induction cooktop', cx0, cx1, TOP - 0.002, TOP + 0.016, cz0, cz1, M['black_glass'], 0.006, coll=col)
    g.box('kd cooktop trim', cx0 - 0.01, cx1 + 0.01, TOP - 0.003, TOP + 0.008, cz0 - 0.01, cz1 + 0.01, 'stainless', coll=col)
    for (bx, bz, r) in ((34.15, 29.98, 0.30), (35.45, 29.98, 0.24), (34.15, 30.62, 0.24), (35.45, 30.62, 0.30)):
        g.lathe('kd cooktop zone', [(r - 0.006, 0.0), (r + 0.006, 0.0)], bx, bz, M['cooktop_mark'], 48, coll=col,
                y_base=TOP + 0.0165, smooth=False)
    g.box('kd cooktop controls', 34.45, 35.15, TOP + 0.0165, TOP + 0.0168, 29.47, 29.53, M['cooktop_mark'], coll=col)

    # ===================================================================== sink
    _sink(g, sx0, sx1, sz0, sz1, M, col)
    _faucet(g, 40.30, SINK_Z, col)

    # ===================================================================== island
    isl = g.sub('kd island')
    _island(g, M, isl, lights)
    if STOOLS:
        _stools(g, M)
    _pendant(g, M, lights)
    notes.append('kitchen: tall bank (fridge+ovens), L base runs, uppers/hood/shelves, island, 3 stools, linear pendant')
    return notes


def _rrect(x0, x1, z0, z1, r, n=8):
    pts = []
    corners = ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270))
    for cx, cz, a0 in corners:
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def _sink(g, x0, x1, z0, z1, M, col):
    """Undermount stainless single bowl, walls flush with the worktop cut-out."""
    import bmesh
    from .kitchen_dining_geo import P
    bm = bmesh.new()
    rings = []
    spec = ((-0.012, CT_UNDER - 0.001), (-0.012, 2.23), (0.04, 2.16), (0.11, 2.15))
    for inset, y in spec:
        pts = _rrect(x0 + inset, x1 - inset, z0 + inset, z1 - inset, max(0.09 - inset * 0.6, 0.02))
        rings.append([bm.verts.new(P(x, y, z)) for x, z in pts])
    n = len(rings[0])
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((A[k], A[k2], B[k2], B[k]))
    bm.faces.new(rings[-1])
    # hidden flange under the worktop so the rim never shows a gap
    ob = g.from_bmesh('kd sink bowl', bm, 'stainless', col, smooth=True, sharp_deg=60)
    dx, dz = (x0 + x1) / 2 + 0.15, (z0 + z1) / 2 + 0.55
    g.lathe('kd sink drain', [(0.0, 0.0), (0.12, 0.0), (0.13, 0.004), (0.0, 0.004)], dx, dz, 'stainless', 32, col, y_base=2.152)
    g.lathe('kd sink drain hole', [(0.0, 0.0), (0.075, 0.0)], dx, dz, M['rubber'], 24, col, y_base=2.1575)
    return ob


def _faucet(g, x, z, col):
    """Matte-black single-lever pull-down faucet behind the sink (spout reaches toward -x)."""
    b = 'black_metal'
    g.lathe('kd faucet base', [(0.0, 0.0), (0.075, 0.0), (0.075, 0.03), (0.06, 0.06), (0.0, 0.06)], x, z, b, 32, col, y_base=TOP)
    R = 0.30
    cx, cy = x - R, 4.18
    pts = [(x, TOP + 0.05, z), (x, cy, z)]
    for k in range(1, 17):
        a = math.pi * k / 16
        pts.append((cx + R * math.cos(a), cy + R * math.sin(a), z))
    pts.append((x - 2 * R, 4.02, z))
    g.tube('kd faucet spout', pts, 0.042, b, col)
    g.cyl('kd faucet spray head', x - 2 * R, 3.86, 4.04, z, 0.05, b, 32, col)
    g.cyl('kd faucet spray face', x - 2 * R, 3.855, 3.862, z, 0.038, 'paint_black', 24, col)
    # side lever
    g.cyl_axis('kd faucet lever hub', (x, 3.55, z + 0.02), (x, 3.55, z + 0.09), 0.045, b, 24, col)
    g.cyl_axis('kd faucet lever', (x, 3.55, z + 0.09), (x - 0.02, 3.70, z + 0.12), 0.016, b, 12, col)


def _island(g, M, col, lights):
    x0, x1, z0, z1 = 28.4, 34.4, 22.0, 25.0
    t = 0.167                                  # 2in mitred waterfall slab
    sec = [(x0, 0.0), (x0 + t, 0.0), (x0 + t, TOP - t), (x1 - t, TOP - t), (x1 - t, 0.0), (x1, 0.0), (x1, TOP), (x0, TOP)]
    wf = g.section_prism_z('kd island waterfall', sec, z0, z1, 'quartz_calacatta', coll=col)
    g.ctx.add_bevel(wf, 0.012, 2)
    bx0, bx1 = x0 + t + 0.002, x1 - t - 0.002
    bz0, bz1 = 23.0, 24.92                     # base 1.92 ft deep, front face at 24.92
    g.box('kd island carcass', bx0, bx1, TOE_H, TOP - t - 0.001, bz0 + FT_T, bz1 - FT_T - 0.01, 'walnut_slab', coll=col)
    g.box('kd island back panel', bx0, bx1, 0.0, TOP - t - 0.001, bz0, bz0 + FT_T, 'walnut_slab', 0.006, coll=col)
    g.box('kd island plinth', bx0, bx1, 0.0, TOE_H, bz0 + FT_T, bz1 - TOE_D, 'paint_black', coll=col)
    chz = bz1 - FT_T - 0.004
    for (y0, y1, tag) in ((Y_CH0, Y_CH1, 'mid'), (Y_HI1, TOP - t - 0.001, 'top')):
        g.box(f'kd island channel {tag}', bx0, bx1, y0, y1, chz - 0.03, chz, 'black_metal', coll=col)
    n = 3
    w = (bx1 - bx0) / n
    for i in range(n):
        a, b = bx0 + i * w, bx0 + (i + 1) * w
        g.box(f'kd island unit {i} lower', a + GAP / 2, b - GAP / 2, Y_LO0, Y_LO1, bz1 - FT_T, bz1, 'walnut_slab', 0.006, coll=col)
        g.box(f'kd island unit {i} drawer', a + GAP / 2, b - GAP / 2, Y_HI0, Y_HI1, bz1 - FT_T, bz1, 'walnut_slab', 0.006, coll=col)
    g.area_light('kd island toe led', (bx0 + bx1) / 2, TOE_H - 0.02, bz1 - 0.10, bx1 - bx0 - 0.1, 0.05, 0.7, 2900, lights,
                 spread_deg=110)


def _stools(g, M):
    """Three saddle-tan leather swivel counter stools on black pedestal bases (seat 25in)."""
    col = g.sub('kd stools')
    seat_y = 2.08
    # Build one stool at the origin, then instance.
    parts = []
    parts.append(g.lathe('kd stool base', [(0.0, 0.0), (0.66, 0.0), (0.68, 0.012), (0.665, 0.035), (0.50, 0.058),
                                            (0.12, 0.085), (0.0, 0.09)], 0, 0, 'black_metal', 64, col, sharp_deg=70))
    parts.append(g.cyl('kd stool column', 0, 0.08, 1.86, 0, 0.085, 'black_metal', 32, col))
    parts.append(g.torus('kd stool footring', 0, 0.80, 0, 0.53, 0.032, 'black_metal', 64, 12, col))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        parts.append(g.cyl_axis('kd stool spoke', (0.08 * math.cos(a), 0.80, 0.08 * math.sin(a)),
                                (0.51 * math.cos(a), 0.80, 0.51 * math.sin(a)), 0.022, 'black_metal', 12, col))
    parts.append(g.lathe('kd stool plate', [(0.0, 0.0), (0.32, 0.0), (0.32, 0.04), (0.25, 0.07), (0.0, 0.07)], 0, 0,
                         'black_metal', 48, col, y_base=1.84))
    # seat cushion: soft rounded disc
    prof = [(0.0, 0.0), (0.58, 0.0), (0.66, 0.015), (0.70, 0.06), (0.70, 0.11), (0.67, 0.155), (0.60, 0.175), (0.3, 0.18), (0.0, 0.18)]
    parts.append(g.lathe('kd stool seat', prof, 0, 0, 'leather_tan', 64, col, y_base=1.905))
    # low bucket back wrapping the rear of the seat
    def ytop(a):
        c = math.cos(a)
        return seat_y + 0.10 + 0.40 * max(c, 0.0) ** 0.8
    back = g.arc_wall('kd stool back', 0.57, 0.69, -2.05, 2.05, seat_y - 0.07, ytop, 'leather_tan', 48, col)
    g.bevel_mod(back, 0.035, 3)
    g.subsurf(back, 1)
    parts.append(back)
    # instance at the three centres (facing +z = the island)
    import bpy
    centres = [(29.4, 21.7), (31.4, 21.7), (33.4, 21.7)]
    for i, (x, z) in enumerate(centres):
        for p in parts:
            if i == len(centres) - 1:
                p.location = (x * 0.3048 + p.location.x, -z * 0.3048 + p.location.y, p.location.z)
                p.name = f'{p.name} {i}'
            else:
                q = p.copy()
                q.name = f'{p.name} {i}'
                q.location = (x * 0.3048 + p.location.x, -z * 0.3048 + p.location.y, p.location.z)
                g._link(q, col)


def _pendant(g, M, lights):
    """Linear LED pendant (matte black aluminium bar, opal diffuser down) over the island."""
    from ..lighting import emitter
    col = g.sub('kd pendant')
    x0, x1, zc, yb = 29.15, 33.65, 23.5, 6.05
    g.box('pendant bar', x0, x1, yb, yb + 0.12, zc - 0.065, zc + 0.065, 'black_metal', 0.012, coll=col)
    dif = emitter('kd_pendant_diffuser', 3000, 45.0)
    g.box('pendant diffuser', x0 + 0.04, x1 - 0.04, yb - 0.006, yb + 0.004, zc - 0.045, zc + 0.045, dif, coll=col)
    for xx in (30.0, 32.8):
        g.cyl('pendant cable', xx, yb + 0.12, CEIL - 0.05, zc, 0.006, 'black_metal', 8, col)
        g.cyl('pendant canopy', xx, CEIL - 0.055, CEIL - 0.001, zc, 0.19, 'black_metal', 40, col, bevel=0.01)
    g.area_light('pendant light', (x0 + x1) / 2, yb - 0.03, zc, x1 - x0 - 0.1, 0.09, 38.0, 3000, lights)
    g.area_light('pendant uplight', (x0 + x1) / 2, yb + 0.14, zc, x1 - x0 - 0.3, 0.06, 6.0, 3000, lights, facing='up')
