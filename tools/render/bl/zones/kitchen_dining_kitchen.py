"""Warm vintage-American kitchen for the kitchen_dining zone (owner's style images: "kitchen
closet / cloest style", "kitchen island and style", "kitchen window (style)").

Same plan as before (fridge column + wall ovens at the west end of the south wall, cooktop under the
hood, dishwasher and sink on the east wall under the window, island with the dining table in line at
its west end, see kitchen_dining_dining),
restyled: painted cream shaker base and upper cabinetry with unlacquered-brass cup pulls and knobs,
crown moulding and a painted toe kick; the tall fridge/oven wall in a soft greige as the "pantry
wall" (integrated fridge behind shaker panels with long brass appliance pulls); glass-front uppers
with dishes; a walnut open-shelf bay with brass gallery rails against whitewashed brick; honed
grey-veined marble worktops with a scalloped marble slab behind the cooktop and a brass pot filler;
a cream plaster hood with a dentil band; a white fireclay apron-front sink with a brass bridge
faucet; a white-oak drawer island with brass knobs under a thick honed quartzite top.

All numbers are SCENE feet on the concept plan (bl/warp.py carries them onto the architect's plan).
Plan anchors: south (garage) wall face z=31.41, east wall face x=40.61, flat ceiling y=8.0;
south counter front z=29.13, east counter front x=38.405; island top x 28.4-34.4, z 22-25;
W08 window z 23.387-29.387, sill 3.15, head 7.75 (sink centred at z 26.387); W07 ends at z 21.814.

Warp naming: run fronts / carcasses / crowns / splashes are '... panel / carcass / cove / splash /
tile ...' (fitted, reshaped with the room); knobs and cup pulls are '... hardware panel' (fitted, so
each stays on its front, see kitchen_dining_cabs); appliances, appliance pulls, the faucet and pot
filler are loose (moved rigidly); the hood is '... soffit ...' (fitted) so it keeps meeting the
cabinets.
"""
import math

import bmesh

from . import kitchen_dining_cabs as C
from . import kitchen_dining_mats as KM
from .kitchen_dining_geo import Geo, P, principled, srgb

# ----------------------------------------------------------------------------- constants
WALL_S = 31.41
WALL_E = 40.61
CEIL = 8.0
TOP = 3.0                 # finished counter height (36in)
CT_T = 0.104              # perimeter marble (1-1/4in)
CT_UNDER = TOP - CT_T
SPL = 0.06                # backsplash slab / thin-brick thickness
FT_T = 0.0625             # 3/4in fronts
GAP = 0.011               # reveal between fronts (~1/8in)
RECESS = 0.022            # shaker centre-panel recess (kitchen_dining_cabs.Acc.shaker default)
TOE_H = 0.333             # toe kick height (4in)
TOE_D = 0.25              # toe kick recess (3in)
CT_FRONT_S = 29.13
FRONT_S = 29.21           # face of the south-run fronts
CT_FRONT_E = 38.405
FRONT_E = 38.488          # face of the east-run fronts
RUN_E0 = 21.84            # north end of the east run (W07 jamb)
TALL_X0 = 22.60           # outer face of the tall-wall end panel
FRIDGE = (22.6625, 25.6625)
OVEN = (25.6625, 28.10)
BASE_X0 = 28.1625
HOOD = (33.2, 36.4)
UPPER_Y0 = 4.75
UPPER_TOP = 7.53          # top of the upper / tall doors (crown above)
CROWN_Y = 7.55
CROWN_H = 0.44
UPPER_FRONT = 30.2675     # face of the upper doors
SHELF_FRONT = 30.55       # face of the walnut open-shelf bay
SINK_Z = 26.387
SINK = (38.44, 40.10, 25.137, 27.637)   # fireclay apron sink outer footprint (x0, x1, z0, z1): 30 x 20in
SINK_BOT = 2.16           # bottom of the apron (10in apron)
Y_B0 = TOE_H + 0.012      # bottom of base fronts
Y_B1 = CT_UNDER - 0.012   # top of base fronts
Y_DR = Y_B1 - 0.5         # top drawer bottom (6in drawers)
COOK = (33.30, 36.30, 29.32, 31.05)     # 36in gas cooktop (x0, x1, z0, z1)
ISLAND = (28.4, 34.4, 22.0, 25.0)       # island worktop (x0, x1, z0, z1); the dining table continues its west end
POT_FILLER = (34.80, 4.55)               # (x, y) on the wall inside the slab's scallop

COLL = 'kd_kitchen'
STOOLS = False            # the dining table continues the island (architect's plan): no stools


class _Mats:
    def __init__(self, g):
        self.cream = KM.paint_cream()
        self.greige = KM.paint_greige()
        self.brass = KM.brass()
        self.marble = KM.marble_honed()
        self.quartzite = KM.quartzite()
        self.oak = KM.oak_island()
        self.brick = KM.brick()
        self.plaster = KM.plaster_hood()
        self.fireclay = KM.fireclay()
        self.iron = KM.cast_iron()
        self.enamel = KM.enamel_black()
        self.glass = KM.glass_cabinet()
        self.black_glass = principled('black_glass', srgb('#060607'), 0.04)
        self.rubber = principled('rubber', srgb('#0d0d0d'), 0.6)


def build(ctx, g: Geo):
    M = _Mats(g)
    col = g.sub(COLL)
    hw = g.sub('kd hardware')
    lights = g.sub('kd_lights')
    notes = []
    _tall_wall(g, M, col, hw)
    _base_runs(g, M, col, hw, lights)
    _worktop_and_splash(g, M, col)
    _uppers(g, M, col, hw, lights)
    _open_shelves(g, M, col)
    _hood(g, M, col, lights)
    _cooktop(g, M, col)
    _pot_filler(g, M, col)
    _sink(g, M, col)
    _bridge_faucet(g, M, col)
    isl = g.sub('kd island')
    _island(g, M, isl, hw)
    notes.append('kitchen: greige pantry wall (panelled fridge + ovens), cream shaker L runs, glass uppers, '
                 'walnut open shelves, plaster hood, fireclay sink, oak island with quartzite top')
    return notes


def _soft_edge(g, ob, width, seg):
    """Eased stone edge: a fine bevel on a FLAT-shaded slab. (Smooth normals on the slab's large quads
    interpolate across whole triangles and showed as faceted triangles at the corners in the glossy
    stone; 4-5 flat facets on a 1/4in round are invisible.)"""
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width = width * 0.3048
    m.segments = seg + 1
    m.limit_method = 'ANGLE'
    m.harden_normals = False
    ob.data.shade_flat()


# ======================================================================== shaker helpers
def _hw_door(g, M, F, u0, u1, v0, v1, hinge, hw, upper=False):
    """Knob on the door's free stile, 2.5in in from the edge, near the top (base) / bottom (upper)."""
    u = u1 - 0.12 if hinge == 'l' else u0 + 0.12
    v = v0 + 0.3 if upper else v1 - 0.28
    C.knob(g, M.brass, F, u, v, hw)


def _hw_drawer(g, M, F, u0, u1, v0, v1, hw, kind='cup', sw=0.19, rw=0.19):
    """Short drawers (6in): pull centred on the recessed centre panel, seated on the panel. Deeper
    drawers: cup pull centred on the top rail (as in the closet reference), seated on the rail face.
    (Hardware placed at the outer face over a recessed panel floated 1/4in off it.)"""
    w, h = u1 - u0, v1 - v0
    slab = w < 2 * sw + 0.12 or h < 2 * rw + 0.08          # Acc.shaker falls back to a slab
    if h < 0.75:
        v, depth = (v0 + v1) / 2, (0.0 if slab else -RECESS)
    else:
        v, depth = v1 - rw / 2 - 0.011, 0.0                  # cup spans v-0.035 .. v+0.057
    us = [(u0 + u1) / 2] if w < 2.2 else [u0 + w * 0.27, u1 - w * 0.27]
    for u in us:
        if kind == 'cup':
            C.cup_pull(g, M.brass, F, u, v, hw, w=depth)
        else:
            C.knob(g, M.brass, F, u, v, hw, w=depth)


def _base_unit(acc, g, M, F, u0, u1, kind, hw, hinge='l'):
    """One base cabinet's fronts between u0 and u1 (face frame F). kinds: 'doors2', 'door1',
    'drawers3', 'drawers2', 'panel'."""
    a, b = u0 + GAP / 2, u1 - GAP / 2
    if kind == 'panel':
        acc.shaker(F, a, b, Y_B0, Y_B1)
        return
    if kind in ('drawers3', 'drawers2'):
        if kind == 'drawers3':
            cuts = [Y_B0, Y_B0 + 1.0, Y_DR, Y_B1]
        else:
            cuts = [Y_B0, Y_DR, Y_B1]
        for i in range(len(cuts) - 1):
            v0 = cuts[i] + (GAP / 2 if i else 0.0)
            v1 = cuts[i + 1] - (GAP / 2 if i < len(cuts) - 2 else 0.0)
            small = v1 - v0 < 0.6
            sw, rw = (0.15, 0.11) if small else (0.19, 0.19)
            acc.shaker(F, a, b, v0, v1, sw=sw, rw=rw)
            _hw_drawer(g, M, F, a, b, v0, v1, hw, sw=sw, rw=rw)
        return
    # top drawer over door(s)
    acc.shaker(F, a, b, Y_DR + GAP / 2, Y_B1, sw=0.15, rw=0.11)
    _hw_drawer(g, M, F, a, b, Y_DR + GAP / 2, Y_B1, hw, sw=0.15, rw=0.11)
    if kind == 'doors2':
        m = (a + b) / 2
        acc.shaker(F, a, m - GAP / 2, Y_B0, Y_DR - GAP / 2)
        acc.shaker(F, m + GAP / 2, b, Y_B0, Y_DR - GAP / 2)
        _hw_door(g, M, F, a, m - GAP / 2, Y_B0, Y_DR - GAP / 2, 'l', hw)
        _hw_door(g, M, F, m + GAP / 2, b, Y_B0, Y_DR - GAP / 2, 'r', hw)
    else:
        acc.shaker(F, a, b, Y_B0, Y_DR - GAP / 2)
        _hw_door(g, M, F, a, b, Y_B0, Y_DR - GAP / 2, hinge, hw)


# ============================================================================= tall wall
def _tall_wall(g, M, col, hw):
    """Fridge column + oven tower in greige: the 'pantry wall' of the closet references."""
    F = C.Face('mz', FRONT_S)
    acc = C.Acc()
    x0, x1 = FRIDGE
    # integrated fridge: freezer drawer, French doors, top cabinet
    acc.shaker(F, x0 + GAP / 2, x1 - GAP / 2, Y_B0, 2.41)
    xm = (x0 + x1) / 2
    acc.shaker(F, x0 + GAP / 2, xm - GAP / 2, 2.42, 6.90, sw=0.21)
    acc.shaker(F, xm + GAP / 2, x1 - GAP / 2, 2.42, 6.90, sw=0.21)
    acc.shaker(F, x0 + GAP / 2, x1 - GAP / 2, 6.92, UPPER_TOP)
    # oven tower: drawer, niche backing (ovens are loose appliances in front of it), top door
    o0, o1 = OVEN
    acc.shaker(F, o0 + GAP / 2, o1 - GAP / 2, Y_B0, 1.54)
    acc.shaker(F, o0 + GAP / 2, o1 - GAP / 2, 6.03, UPPER_TOP)
    tall = acc.done(g, 'kd tall wall door panel run', M.greige, col)
    niche = C.Acc()
    niche.box(F, o0, o1, 1.55, 6.02, -FT_T, -0.02)
    niche.done(g, 'kd tall niche panel', M.greige, col, bevel=0.0)
    # end panels (two stacked shaker panels on the hall side), side panel to the counter, kick, carcass
    side = C.Acc()
    Fw = C.Face('mx', TALL_X0)
    side.shaker(Fw, FRONT_S, WALL_S, 0.0, 3.4, sw=0.24)
    side.shaker(Fw, FRONT_S, WALL_S, 3.4, UPPER_TOP, sw=0.24)
    side.wbox(OVEN[1], BASE_X0, 0.0, UPPER_TOP, FRONT_S, WALL_S)
    side.done(g, 'kd tall end panel', M.greige, col)
    g.box('kd tall plinth', FRIDGE[0], OVEN[1], 0.0, TOE_H, FRONT_S + 0.10, WALL_S - 0.02, M.greige, coll=col)
    g.box('kd tall carcass', FRIDGE[0], OVEN[1], TOE_H, CEIL - 0.006, FRONT_S + FT_T + 0.01, WALL_S, M.greige, coll=col)
    # frieze behind the crown + crown with mitred returns on both ends
    g.box('kd tall carcass frieze', TALL_X0, BASE_X0, UPPER_TOP, CEIL - 0.006, FRONT_S + 0.004, FRONT_S + FT_T + 0.012,
          M.greige, coll=col)
    C.sweep(g, 'kd tall crown cove', [(TALL_X0, WALL_S - 0.004), (TALL_X0, FRONT_S), (BASE_X0, FRONT_S), (BASE_X0, WALL_S - 0.004)],
            C.crown_profile(0.24, CROWN_H), CROWN_Y, M.greige, col)
    # hardware: long brass appliance pulls on the French doors, bar on the freezer, cups on the drawer
    for xx in (xm - 0.16, xm + 0.16):
        C.bar_pull(g, M.brass, F, xx, 3.75, xx, 5.55, hw, name='kd fridge pull')
    # freezer bar on the drawer's top rail (2.22-2.41), feet on the rail face
    C.bar_pull(g, M.brass, F, x0 + 0.75, 2.315, x1 - 0.75, 2.315, hw, name='kd freezer pull')
    _hw_drawer(g, M, F, o0, o1, Y_B0, 1.54, hw)
    # lift-up door over the fridge: knob centred on its bottom rail; oven-tower top door: on the stile
    C.knob(g, M.brass, F, xm, 6.92 + 0.095, hw)
    C.knob(g, M.brass, F, o1 - 0.12, 6.3, hw)
    # stacked wall ovens (27in, brass handles): loose appliances. Stainless doors with a black-glass
    # viewing window (closet reference: a stainless oven) rather than full black-glass doors, which
    # read as two heavy dark slabs in the greige wall.
    oc = (o0 + o1) / 2
    for k, (oy0, oy1) in enumerate(((1.60, 3.78), (3.82, 6.0))):
        ox0, ox1 = oc - 1.125, oc + 1.125
        g.box(f'kd oven {k} fascia', ox0, ox1, oy0, oy1, FRONT_S - 0.035, FRONT_S + 0.012, 'stainless', 0.01, coll=col)
        g.box(f'kd oven {k} door', ox0 + 0.05, ox1 - 0.05, oy0 + 0.05, oy1 - 0.3, FRONT_S - 0.05, FRONT_S - 0.03,
              'stainless', 0.008, coll=col)
        g.box(f'kd oven {k} window', ox0 + 0.32, ox1 - 0.32, oy0 + 0.3, oy1 - 0.62, FRONT_S - 0.053, FRONT_S - 0.047,
              M.black_glass, 0.002, coll=col)
        g.box(f'kd oven {k} controls', ox0 + 0.05, ox1 - 0.05, oy1 - 0.22, oy1 - 0.05, FRONT_S - 0.045, FRONT_S - 0.03,
              M.black_glass, 0.006, coll=col)
        for kx in (-0.55, 0.55):
            g.cyl_axis(f'kd oven {k} knob', (oc + kx, oy1 - 0.135, FRONT_S - 0.045), (oc + kx, oy1 - 0.135, FRONT_S - 0.09),
                       0.045, M.brass, 24, col)
        hy = oy1 - 0.38
        g.cyl_axis(f'kd oven {k} handle', (ox0 + 0.2, hy, FRONT_S - 0.17), (ox1 - 0.2, hy, FRONT_S - 0.17), 0.028, M.brass, 20, col)
        for xx in (ox0 + 0.32, ox1 - 0.32):
            g.cyl_axis(f'kd oven {k} handle post', (xx, hy, FRONT_S - 0.05), (xx, hy, FRONT_S - 0.17), 0.017, M.brass, 16, col)


# ============================================================================= base runs
def _base_runs(g, M, col, hw, lights):
    Fs = C.Face('mz', FRONT_S)
    Fe = C.Face('mx', FRONT_E)
    acc = C.Acc()
    for (x0, x1), kind in (((BASE_X0, 30.70), 'doors2'), ((30.70, 33.30), 'drawers3'),
                           ((33.30, 36.30), 'drawers3'), ((36.30, 38.40), 'doors2')):
        _base_unit(acc, g, M, Fs, x0, x1, kind, hw)
    # blind corner fillers
    acc.box(Fs, 38.40, FRONT_E + FT_T, Y_B0, Y_B1, -FT_T, 0.0)
    acc.box(Fe, 29.12, FRONT_S + FT_T, Y_B0, Y_B1, -FT_T, 0.0)
    # east run (u = z): narrow door | dishwasher panel | sink base | drawers
    _base_unit(acc, g, M, Fe, RUN_E0 + FT_T, 22.887, 'door1', hw, hinge='l')
    acc.shaker(Fe, 22.887 + GAP / 2, 24.887 - GAP / 2, Y_B0, Y_B1)                    # dishwasher
    C.bar_pull(g, M.brass, Fe, 23.37, Y_B1 - 0.095, 24.40, Y_B1 - 0.095, hw, name='kd dishwasher pull', standoff=0.1)
    s0, s1 = 24.887, 27.887
    za, zb = SINK[2], SINK[3]
    acc.box(Fe, s0 + GAP / 2, za - 0.006, SINK_BOT, Y_B1, -FT_T, 0.0)                  # stiles beside the apron
    acc.box(Fe, zb + 0.006, s1 - GAP / 2, SINK_BOT, Y_B1, -FT_T, 0.0)
    acc.shaker(Fe, s0 + GAP / 2, SINK_Z - GAP / 2, Y_B0, SINK_BOT - GAP)
    acc.shaker(Fe, SINK_Z + GAP / 2, s1 - GAP / 2, Y_B0, SINK_BOT - GAP)
    _hw_door(g, M, Fe, s0, SINK_Z - GAP / 2, Y_B0, SINK_BOT - GAP, 'l', hw)
    _hw_door(g, M, Fe, SINK_Z + GAP / 2, s1, Y_B0, SINK_BOT - GAP, 'r', hw)
    _base_unit(acc, g, M, Fe, 27.887, 29.12, 'drawers3', hw)
    acc.done(g, 'kd base door panel run', M.cream, col)
    # exposed end panel of the east run (faces north, toward W07)
    ep = C.Acc()
    ep.shaker(C.Face('mz', RUN_E0), FRONT_E, WALL_E, 0.0, CT_UNDER, sw=0.22)
    ep.done(g, 'kd east end panel', M.cream, col)
    # carcasses (hidden), split around the apron sink so nothing shows inside the bowl
    g.box('kd south carcass', BASE_X0, WALL_E, TOE_H, CT_UNDER, FRONT_S + FT_T + 0.012, WALL_S, M.cream, coll=col)
    ex0, ez0, ez1 = FRONT_E + FT_T + 0.012, RUN_E0 + FT_T, FRONT_S + FT_T + 0.012
    g.box('kd east carcass n', ex0, WALL_E, TOE_H, CT_UNDER, ez0, SINK[2] - 0.01, M.cream, coll=col)
    g.box('kd east carcass s', ex0, WALL_E, TOE_H, CT_UNDER, SINK[3] + 0.01, ez1, M.cream, coll=col)
    g.box('kd east carcass sink deck', ex0, WALL_E, TOE_H, SINK_BOT - 0.03, SINK[2] - 0.01, SINK[3] + 0.01, M.cream, coll=col)
    g.box('kd east carcass sink back', SINK[1] + 0.01, WALL_E, SINK_BOT - 0.03, CT_UNDER, SINK[2] - 0.01, SINK[3] + 0.01,
          M.cream, coll=col)
    # painted toe kicks (recessed)
    g.box('kd south plinth', BASE_X0, WALL_E, 0.0, TOE_H, FRONT_S + TOE_D, WALL_S, M.cream, coll=col)
    g.box('kd east plinth', FRONT_E + TOE_D, WALL_E, 0.0, TOE_H, RUN_E0 + FT_T, FRONT_S + TOE_D, M.cream, coll=col)


# ====================================================================== worktop + splash
def _worktop_and_splash(g, M, col):
    sx0, sx1, sz0, sz1 = SINK
    c = 0.005
    pts = [(BASE_X0, CT_FRONT_S), (CT_FRONT_E, CT_FRONT_S), (CT_FRONT_E, sz1 + c), (sx1 + c, sz1 + c),
           (sx1 + c, sz0 - c), (CT_FRONT_E, sz0 - c), (CT_FRONT_E, RUN_E0 - 0.02), (WALL_E - SPL, RUN_E0 - 0.02),
           (WALL_E - SPL, WALL_S - SPL), (BASE_X0, WALL_S - SPL)]
    top = g.poly_prism('kd worktop', pts, CT_UNDER, TOP, M.marble, coll=col)
    _soft_edge(g, top, 0.014, 3)
    # marble slab behind the counter under the uppers and the cooktop, scalloped under the pot filler
    px, _ = POT_FILLER
    r = 0.5
    arc = [(px + r * math.cos(-math.pi * k / 20), UPPER_Y0 + r * math.sin(-math.pi * k / 20)) for k in range(21)]
    poly = [(BASE_X0, TOP), (HOOD[1], TOP), (HOOD[1], UPPER_Y0)] + arc + [(BASE_X0, UPPER_Y0)]
    acc = C.Acc()
    acc.poly_z(poly, WALL_S - SPL, WALL_S)
    acc.done(g, 'kd splash marble', M.marble, col, bevel=0.006, seg=2)
    # whitewashed thin brick: the open-shelf bay and the sink wall (counter to ceiling)
    acc = C.Acc()
    acc.wbox(HOOD[1], WALL_E - SPL, TOP, CEIL - 0.004, WALL_S - SPL, WALL_S)
    acc.wbox(WALL_E - SPL, WALL_E, TOP, CEIL - 0.004, RUN_E0 - 0.02, 23.387)
    acc.wbox(WALL_E - SPL, WALL_E, TOP, CEIL - 0.004, 29.387, WALL_S)
    acc.done(g, 'kd brick tile splash', M.brick, col, bevel=0.0)


# ================================================================================ uppers
def _uppers(g, M, col, hw, lights):
    """Three glass-front upper cabinets (x BASE_X0-HOOD0) with painted interiors, shelves and
    dishes, crown moulding to the ceiling, warm under-cabinet light."""
    ux0, ux1 = BASE_X0, HOOD[0]
    zf = UPPER_FRONT + FT_T + 0.006            # carcass front
    t = 0.06
    acc = C.Acc()
    acc.wbox(ux0, ux1, UPPER_Y0, UPPER_Y0 + t, zf, WALL_S)                     # bottom
    acc.wbox(ux0, ux1, UPPER_TOP - t, CEIL - 0.006, zf, WALL_S)                # top + frieze block
    acc.wbox(ux0, ux1, UPPER_Y0 + t, UPPER_TOP - t, WALL_S - t, WALL_S)        # back
    n = 3
    w = (ux1 - ux0) / n
    xs = [ux0 + i * w for i in range(n + 1)]
    for i, x in enumerate(xs):                                                  # sides + partitions
        a = x if i == 0 else (x - t if i == n else x - t / 2)
        acc.wbox(a, a + t, UPPER_Y0 + t, UPPER_TOP - t, zf, WALL_S - t)
    for ys in (5.66, 6.58):                                                     # shelves
        for i in range(n):
            a = xs[i] + (t if i == 0 else t / 2)
            b = xs[i + 1] - (t if i == n - 1 else t / 2)
            acc.wbox(a, b, ys, ys + 0.055, zf + 0.04, WALL_S - t)
    acc.done(g, 'kd upper carcass', M.cream, col, bevel=0.002)
    # glazed shaker doors
    F = C.Face('mz', UPPER_FRONT)
    doors = C.Acc()
    panes = C.Acc()
    for i in range(n):
        a, b = xs[i] + GAP / 2, xs[i + 1] - GAP / 2
        doors.shaker(F, a, b, UPPER_Y0, UPPER_TOP, sw=0.2, glass=True)
        panes.box(F, a + 0.17, b - 0.17, UPPER_Y0 + 0.17, UPPER_TOP - 0.17, -0.036, -0.028)
        _hw_door(g, M, F, a, b, UPPER_Y0, UPPER_TOP, 'l' if i < 2 else 'r', hw, upper=True)
    doors.done(g, 'kd upper door panel run', M.cream, col)
    panes.done(g, 'kd upper door pane', M.glass, col, bevel=0.0)
    # frieze in the door plane above the doors, crown to the ceiling (dies into the tall-wall return
    # and the hood)
    g.box('kd upper carcass frieze', ux0, ux1, UPPER_TOP + 0.004, CEIL - 0.006, UPPER_FRONT + 0.004, zf, M.cream, coll=col)
    C.sweep(g, 'kd upper crown cove', [(ux0, UPPER_FRONT), (ux1, UPPER_FRONT)], C.crown_profile(0.2, CROWN_H), CROWN_Y,
            M.cream, col)
    # warm under-cabinet light (fixture hidden under the bottom)
    g.area_light('kd under-upper light', (ux0 + ux1) / 2, UPPER_Y0 - 0.02, UPPER_FRONT + 0.35, ux1 - ux0 - 0.3, 0.06, 5.0,
                 2900, lights)


# ========================================================================= open shelves
def _open_shelves(g, M, col):
    """Walnut open-shelf bay between the hood and the east wall (closet reference): side panels
    with a curved corbel foot, two shelves and a top, walnut cornice, brass gallery rails."""
    x0, x1 = HOOD[1] + 0.02, WALL_E - SPL
    zf, zb = SHELF_FRONT, WALL_S - SPL
    st = 0.08
    foot = 4.30
    prof = [(zb, foot), (zb, CROWN_Y), (zf, CROWN_Y), (zf, foot + 0.55)]
    for k in range(1, 12):                        # concave corbel curve from the front down to the back
        a = math.pi / 2 * k / 12
        prof.append((zf + (zb - zf) * 0.62 * (1 - math.cos(a)), foot + 0.55 - 0.55 * math.sin(a)))
    prof.append((zf + (zb - zf) * 0.62, foot))
    sides = C.Acc()
    sides.poly_x(prof, x0, x0 + st)
    sides.poly_x(prof, x1 - st, x1)
    sides.done(g, 'kd shelf side panel', 'walnut_door', col, bevel=0.006)
    shelves = C.Acc()
    for ys in (4.86, 6.18):
        shelves.wbox(x0 + st, x1 - st, ys, ys + 0.1, zf + 0.02, zb)
    shelves.wbox(x0 + st, x1 - st, CROWN_Y - 0.1, CROWN_Y, zf, zb)
    shelves.wbox(x0, x1, CROWN_Y, CEIL - 0.006, zf + 0.004, zb)              # frieze behind the cornice
    shelves.done(g, 'kd shelf walnut', 'walnut_slab', col, bevel=0.006)
    C.sweep(g, 'kd shelf crown cove', [(x0, zf), (x1, zf)], C.crown_profile(0.16, CROWN_H), CROWN_Y, 'walnut_slab', col)
    # brass gallery rails 2.5in above each shelf, with uprights
    for k, ys in enumerate((4.96, 6.28)):
        yr = ys + 0.21
        g.cyl_axis(f'kd shelf rail {k}', (x0 + st, yr, zf + 0.08), (x1 - st, yr, zf + 0.08), 0.014, M.brass, 16, col)
        for xx in (x0 + st + 0.12, (x0 + x1) / 2, x1 - st - 0.12):
            g.cyl_axis(f'kd shelf rail upright {k}', (xx, ys, zf + 0.08), (xx, yr, zf + 0.08), 0.011, M.brass, 12, col)


# ================================================================================== hood
def _hood(g, M, col, lights):
    """Cream plaster hood to the ceiling with a projecting moulded band and a dentil course."""
    hx0, hx1 = HOOD
    zf = 29.80
    yb, yt = 5.52, 5.86
    g.box('kd hood soffit body', hx0, hx1, yt, CEIL - 0.004, zf, WALL_S, M.plaster, 0.008, 2, coll=col)
    g.box('kd hood soffit band', hx0, hx1, yb, yt, zf, WALL_S, M.plaster, 0.004, 2, coll=col)
    prof = [(0.0, 0.0), (0.05, 0.0), (0.06, 0.012), (0.06, 0.05), (0.03, 0.065), (0.03, 0.17)]
    prof += C.cyma(0.03, 0.12, 0.17, 0.31, 10)[1:]
    prof += [(0.13, 0.31), (0.13, 0.34), (0.0, 0.34)]
    path = [(hx0, UPPER_FRONT - 0.006), (hx0, zf), (hx1, zf), (hx1, UPPER_FRONT - 0.006)]
    C.sweep(g, 'kd hood soffit moulding', path, prof, yb, M.plaster, col)
    # dentils: 0.055 wide, 0.07 tall, every 0.1 ft along the front and the returns
    acc = C.Acc()
    dy0, dy1 = yb + 0.085, yb + 0.16
    Ff = C.Face('mz', zf)
    n = int((hx1 - hx0 + 0.06) / 0.1)
    off = (hx1 - hx0 + 0.06 - (n - 1) * 0.1) / 2
    for i in range(n):
        u = hx0 - 0.03 + off + i * 0.1
        acc.box(Ff, u - 0.0275, u + 0.0275, dy0, dy1, 0.02, 0.075)
    for side, Fx in ((-1, C.Face('mx', hx0)), (1, C.Face('px', hx1))):
        z = zf + 0.07
        while z < UPPER_FRONT - 0.05:
            acc.box(Fx, z - 0.0275, z + 0.0275, dy0, dy1, 0.02, 0.075)
            z += 0.1
    acc.done(g, 'kd hood soffit dentils', M.plaster, col, bevel=0.003)
    g.box('kd hood soffit liner', hx0 + 0.14, hx1 - 0.14, yb - 0.012, yb, zf + 0.14, WALL_S - 0.14, 'stainless', 0.004, coll=col)
    g.area_light('kd hood task light', (hx0 + hx1) / 2, yb - 0.03, 30.45, 2.4, 0.8, 6.0, 2900, lights)


# =============================================================================== cooktop
def _cooktop(g, M, col):
    """36in gas cooktop: black enamel deck, three continuous cast-iron grates, brass burner caps and
    front knobs (sits on the worktop)."""
    x0, x1, z0, z1 = COOK
    y = TOP
    g.box('kd cooktop deck', x0, x1, y, y + 0.03, z0, z1, M.enamel, 0.012, coll=col)
    g.box('kd cooktop control strip', x0 + 0.04, x1 - 0.04, y + 0.03, y + 0.034, z0 + 0.03, z0 + 0.2, M.enamel, 0.004, coll=col)
    burners = [(x0 + 0.5, z0 + 0.62, 0.15), (x0 + 0.5, z1 - 0.42, 0.12), ((x0 + x1) / 2, (z0 + 0.2 + z1) / 2, 0.18),
               (x1 - 0.5, z0 + 0.62, 0.12), (x1 - 0.5, z1 - 0.42, 0.15)]
    for i, (bx, bz, r) in enumerate(burners):
        g.lathe(f'kd cooktop burner {i}', [(0.0, 0.0), (r + 0.03, 0.0), (r + 0.03, 0.02), (r, 0.035), (r * 0.75, 0.06),
                                         (r * 0.72, 0.075), (0.0, 0.08)], bx, bz, M.brass, 40, col, y_base=y + 0.03)
    # grates: three cast-iron grids, fingers 0.1 tall over the burners
    gy0, gy1 = y + 0.03, y + 0.165
    acc = C.Acc()
    gx = [x0 + 0.03, x0 + 1.0, x1 - 1.0, x1 - 0.03]
    for k in range(3):
        a, b = gx[k] + 0.015, gx[k + 1] - 0.015
        za, zb = z0 + 0.24, z1 - 0.05
        for (u0, u1, w0, w1) in ((a, b, za, za + 0.05), (a, b, zb - 0.05, zb), (a, a + 0.05, za, zb), (b - 0.05, b, za, zb)):
            acc.wbox(u0, u1, gy1 - 0.035, gy1, w0, w1)
        xm = (a + b) / 2
        zm = (za + zb) / 2
        acc.wbox(xm - 0.02, xm + 0.02, gy1 - 0.035, gy1, za, zb)
        acc.wbox(a, b, gy1 - 0.035, gy1, zm - 0.02, zm + 0.02)
        for (px, pz) in ((a + 0.025, za + 0.025), (b - 0.025, za + 0.025), (a + 0.025, zb - 0.025), (b - 0.025, zb - 0.025)):
            acc.wbox(px - 0.02, px + 0.02, gy0, gy1 - 0.035, pz - 0.02, pz + 0.02)
    acc.done(g, 'kd cooktop grate', M.iron, col, bevel=0.008)
    for i in range(5):
        kx = x0 + 0.42 + i * (x1 - x0 - 0.84) / 4
        g.cyl('kd cooktop knob', kx, y + 0.034, y + 0.1, z0 + 0.115, 0.055, M.iron, 24, col, bevel=0.01)
        g.cyl('kd cooktop knob collar', kx, y + 0.034, y + 0.045, z0 + 0.115, 0.07, M.brass, 24, col)


def _pot_filler(g, M, col):
    """Wall-mounted articulated brass pot filler, folded against the wall inside the scallop."""
    x, y = POT_FILLER
    zw = WALL_S
    b = M.brass
    g.cyl_axis('kd pot filler flange', (x, y, zw), (x, y, zw - 0.04), 0.1, b, 32, col)
    g.cyl_axis('kd pot filler stem', (x, y, zw - 0.04), (x, y, zw - 0.26), 0.035, b, 20, col)
    g.cyl('kd pot filler elbow', x, y - 0.05, y + 0.07, zw - 0.28, 0.05, b, 24, col)
    zc = zw - 0.28
    # first arm runs east along the wall, knuckle, second arm folds back west, spout drops
    g.cyl_axis('kd pot filler arm a', (x, y + 0.03, zc), (x + 0.62, y + 0.03, zc), 0.032, b, 20, col)
    g.cyl('kd pot filler knuckle', x + 0.62, y - 0.04, y + 0.1, zc, 0.048, b, 24, col)
    g.cyl_axis('kd pot filler arm b', (x + 0.62, y - 0.01, zc - 0.075), (x - 0.18, y - 0.01, zc - 0.075), 0.03, b, 20, col)
    g.cyl('kd pot filler knuckle b', x + 0.62, y - 0.05, y + 0.04, zc - 0.075, 0.042, b, 24, col)
    g.cyl_axis('kd pot filler link', (x + 0.62, y - 0.01, zc), (x + 0.62, y - 0.01, zc - 0.075), 0.028, b, 16, col)
    g.cyl_axis('kd pot filler spout', (x - 0.18, y - 0.01, zc - 0.075), (x - 0.18, y - 0.16, zc - 0.075), 0.026, b, 16, col)
    g.cyl('kd pot filler aerator', x - 0.18, y - 0.19, y - 0.155, zc - 0.075, 0.032, b, 20, col)
    for (xx, zz) in ((x + 0.12, zc), (x + 0.45, zc - 0.075)):
        g.cyl_axis('kd pot filler lever', (xx, y + 0.06, zz), (xx, y + 0.16, zz - 0.06), 0.014, b, 12, col)


# ================================================================================== sink
def _sink(g, M, col):
    """White fireclay apron-front sink (30 x 20 x 10in), 1in walls, 9in bowl, brass strainer."""
    x0, x1, z0, z1 = SINK
    yt, yb = TOP - 0.004, SINK_BOT
    wall = 0.08
    floor_y = yb + 0.085
    bm = bmesh.new()

    def ring(xa, xb, za, zb, r, y):
        return [bm.verts.new(P(x, y, z)) for x, z in _rrect(xa, xb, za, zb, r, 6)]
    ob = ring(x0, x1, z0, z1, 0.02, yb)
    ot = ring(x0, x1, z0, z1, 0.02, yt)
    it = ring(x0 + wall, x1 - wall, z0 + wall, z1 - wall, 0.11, yt)
    ib = ring(x0 + wall, x1 - wall, z0 + wall, z1 - wall, 0.11, floor_y)
    n = len(ob)
    for A, B in ((ob, ot), (ot, it), (it, ib)):
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((A[k], A[k2], B[k2], B[k]))
    bm.faces.new(ib)
    bm.faces.new(list(reversed(ob)))
    s = g.from_bmesh('kd fireclay sink tub', bm, M.fireclay, col, smooth=True, sharp_deg=50)
    g.bevel_mod(s, 0.008, 2)
    dx, dz = (x0 + x1) / 2 + 0.1, (z0 + z1) / 2
    g.lathe('kd sink drain', [(0.0, 0.0), (0.14, 0.0), (0.15, 0.006), (0.0, 0.006)], dx, dz, M.brass, 32, col, y_base=floor_y)
    g.lathe('kd sink drain basket', [(0.0, 0.0), (0.085, 0.0)], dx, dz, M.rubber, 24, col, y_base=floor_y + 0.0065)


def _rrect(x0, x1, z0, z1, r, n=8):
    pts = []
    corners = ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270))
    for cx, cz, a0 in corners:
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def _bridge_faucet(g, M, col):
    """Brass bridge faucet on the deck behind the sink: two risers with cross handles, a bridge and
    a tall gooseneck spout reaching over the bowl."""
    b = M.brass
    x = 40.33
    zc = SINK_Z
    for s in (-1, 1):
        z = zc + s * 0.33
        g.lathe('kd bridge faucet base', [(0.0, 0.0), (0.075, 0.0), (0.075, 0.025), (0.05, 0.06), (0.0, 0.06)], x, z, b, 32, col,
                y_base=TOP)
        g.cyl('kd bridge faucet riser', x, TOP + 0.05, TOP + 0.36, z, 0.032, b, 24, col)
        g.cyl('kd bridge faucet bonnet', x, TOP + 0.36, TOP + 0.46, z, 0.045, b, 24, col)
        g.cyl('kd bridge faucet stem', x, TOP + 0.46, TOP + 0.52, z, 0.018, b, 16, col)
        hy = TOP + 0.53
        for ang in (0.0, math.pi / 2):
            dx, dz = 0.11 * math.cos(ang + 0.6), 0.11 * math.sin(ang + 0.6)
            g.cyl_axis('kd bridge faucet handle', (x - dx, hy, z - dz), (x + dx, hy, z + dz), 0.014, b, 12, col)
        g.cyl_axis('kd bridge faucet bridge arm', (x, TOP + 0.28, z), (x, TOP + 0.28, zc), 0.028, b, 20, col)
    g.cyl('kd bridge faucet hub', x, TOP + 0.24, TOP + 0.32, zc, 0.045, b, 24, col)
    # gooseneck spout: up 0.55 from the hub, then a 180 deg arc reaching toward the bowl
    R = 0.28
    pts = [(x, TOP + 0.3, zc), (x, TOP + 0.95, zc)]
    for k in range(1, 19):
        a = math.pi * k / 18
        pts.append((x - R + R * math.cos(a), TOP + 0.95 + R * math.sin(a), zc))
    pts.append((x - 2 * R, TOP + 0.80, zc))
    g.tube('kd bridge faucet spout', pts, 0.03, b, col)
    g.cyl('kd bridge faucet aerator', x - 2 * R, TOP + 0.76, TOP + 0.81, zc, 0.034, b, 20, col)


# ================================================================================ island
def _island(g, M, col, hw):
    """White-oak drawer island (three drawer stacks to the kitchen, panelled back toward the living room,
    furniture end panels; the dining table stands against the west one) under a 2in honed quartzite top
    with an eased edge."""
    x0, x1, z0, z1 = ISLAND
    t = 0.167
    top = g.box('kd island top', x0, x1, TOP - t, TOP, z0, z1, M.quartzite, coll=col)
    _soft_edge(g, top, 0.022, 3)
    bx0, bx1 = 28.65, 34.15
    bz0, bz1 = 23.0, 24.85                      # carcass back / front (fronts overlay outside these)
    yt = TOP - t - 0.002
    zf = bz1 + FT_T                             # drawer faces
    zb = bz0 - FT_T                             # back panel faces
    ends = C.Acc()
    ends.shaker(C.Face('mx', bx0), zb, zf, 0.0, yt, sw=0.22, rw=0.24)
    ends.shaker(C.Face('px', bx1), zb, zf, 0.0, yt, sw=0.22, rw=0.24)
    ends.done(g, 'kd island end panel', M.oak, col)
    g.box('kd island carcass', bx0 + FT_T, bx1 - FT_T, TOE_H, yt, bz0, bz1, M.oak, coll=col)
    g.box('kd island plinth', bx0 + FT_T, bx1 - FT_T, 0.0, TOE_H, bz0 + 0.15, bz1 - 0.15, M.oak, coll=col)
    Ff = C.Face('pz', zf)
    Fb = C.Face('mz', zb)
    fronts = C.Acc()
    a0, a1 = bx0 + FT_T, bx1 - FT_T
    n = 3
    w = (a1 - a0) / n
    cuts = [Y_B0, Y_B0 + 0.98, yt - 0.012 - 0.52, yt - 0.012]
    for i in range(n):
        a, b = a0 + i * w + GAP / 2, a0 + (i + 1) * w - GAP / 2
        for j in range(3):
            v0 = cuts[j] + (GAP / 2 if j else 0.0)
            v1 = cuts[j + 1] - (GAP / 2 if j < 2 else 0.0)
            small = v1 - v0 < 0.6
            fronts.shaker(Ff, a, b, v0, v1, sw=0.16 if small else 0.2, rw=0.12 if small else 0.2)
            # knob on the recessed centre panel (seated on it, not floating at the frame plane)
            C.knob(g, M.brass, Ff, (a + b) / 2, (v0 + v1) / 2 if small else v1 - 0.26, hw,
                   name='kd island hardware panel', w=-RECESS)
        fronts.shaker(Fb, a, b, Y_B0, yt - 0.012, sw=0.2, rw=0.22)
    fronts.done(g, 'kd island drawer panel run', M.oak, col)
