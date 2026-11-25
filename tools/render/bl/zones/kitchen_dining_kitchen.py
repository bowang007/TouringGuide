"""Warm vintage-American kitchen for the kitchen_dining zone (owner's style images: "kitchen
closet / cloest style", "kitchen island and style", "kitchen window (style)").

Same plan as before (fridge column + wall ovens at the west end of the south wall, cooktop under the
hood, dishwasher and sink on the east wall under the window, island with the dining table in line at
its west end, see kitchen_dining_dining),
restyled: painted cream shaker base and upper cabinetry with unlacquered-brass cup pulls and knobs,
crown moulding and a painted toe kick; the tall fridge/oven wall in a soft greige as the "pantry
wall": a stainless-steel French-door refrigerator standing in its bay under a two-door cabinet, beside
the oven tower with a built-in microwave over a wall oven (owner's seventh round, 2026-11-21: the
panelled, integrated refrigerator read as a pantry: "there is no refrigerator now"); glass-front uppers
with dishes; a walnut open-shelf bay with brass gallery rails against whitewashed brick; honed
grey-veined marble worktops with a scalloped marble slab behind the cooktop and a brass pot filler;
a cream plaster hood with a dentil band; a white fireclay apron-front sink with a brass bridge
faucet; a white-oak drawer island with brass knobs under a thick honed quartzite top.

All numbers are SCENE feet on the concept plan (bl/warp.py carries them onto the architect's plan).
Plan anchors: south (garage) wall face z=31.41, east wall face x=40.61, flat ceiling y=8.0;
W08 window z 23.387-29.387, sill 3.15, head 7.75 (sink centred at z 26.387); W07 ended at z 21.814.

Eighth round (2026-11-24, the architect's sheet SKA002): the counters are 2'-0" deep and the island is
7'-0" x 4'-0" at the sheet's place, 3'-6" from the east counter's front and 4'-0" from the south counter's.
Those sizes are stated in feet on the ARCHITECT'S plan (PLAN_* below, from relayout's wall faces) and carried
back to the concept plan with the inverse of the maps bl/warp.py applies to this zone (_px, _pz): built,
the south counter's front is z 29.058, the east counter's x 37.308, the island's worktop x 26.808-33.808,
z 21.058-25.058 (concept: z 29.388, x 38.532, x 27.611-34.892, z 21.296-25.342). The east run starts at the
south jamb of the 5'-0" living / dining window (worktop from z 21.072; the sheet: 21.058). The tall wall's fronts
stand one door thickness in front of the 2'-0" line (a 24in carcass). Everything keeps its place ALONG the
walls: only the depths changed. The island itself is built in plan feet (C.PlanFace), like the refrigerator.

Warp naming: run fronts / carcasses / crowns / splashes are '... panel / carcass / cove / splash /
tile ...' (fitted, reshaped with the room); knobs and cup pulls are '... hardware panel' (fitted, so
each stays on its front, see kitchen_dining_cabs); appliances, appliance pulls, the faucet and pot
filler are loose (moved rigidly); the hood is '... soffit ...' (fitted) so it keeps meeting the
cabinets. The refrigerator is the exception among the appliances: it fills its fitted bay, so its
parts are '... panel' (fitted) and are dimensioned on the architect's plan (see _refrigerator).
"""
import math
import sys

import bmesh

from ..common import RENDER_DIR
from . import kitchen_dining_cabs as C
from . import kitchen_dining_mats as KM
from .kitchen_dining_geo import Geo, P, principled, srgb

if RENDER_DIR not in sys.path:
    sys.path.insert(0, RENDER_DIR)
import relayout as R  # noqa: E402  (the concept -> architect's plan maps that bl/warp.py applies to this zone)

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


def _inv(f, v):
    """Concept coordinate that the piecewise-linear relayout map `f` carries to the new-plan value v."""
    ps = f.pairs
    if v <= ps[0][1]:
        return ps[0][0] + (v - ps[0][1])
    if v >= ps[-1][1]:
        return ps[-1][0] + (v - ps[-1][1])
    for (a0, b0), (a1, b1) in zip(ps, ps[1:]):
        if b0 <= v <= b1:
            return a0 + (v - b0) / (b1 - b0) * (a1 - a0)


def _px(x):
    """Concept x of an x on the architect's plan (region 'kitchen + dining': relayout.X_HALL)."""
    return _inv(R.X_HALL, x)


def _pz(z):
    """Concept z of a z on the architect's plan (region 'kitchen + dining': relayout.Z_RIGHT)."""
    return _inv(R.Z_RIGHT, z)


# v7 kitchen (eighth round): the sheet's kitchen, feet on the ARCHITECT'S plan, from relayout's wall faces
PLAN_COUNTER_D = 2.0                       # worktop front to the wall face, east and south runs: 2'-0"
PLAN_AISLE_E = 3.5                         # island's east end to the east counter's front: 3'-6"
PLAN_AISLE_S = 4.0                         # island's south edge to the south counter's front: 4'-0"
PLAN_ISLAND_L, PLAN_ISLAND_D = 7.0, 4.0    # island worktop: 7'-0" x 4'-0"
PLAN_CT_E = R.X_LIV_E - PLAN_COUNTER_D     # east counter's front, x 37.308
PLAN_CT_S = R.Z_KIT_S - PLAN_COUNTER_D     # south counter's front, z 29.058
PLAN_ISLAND = (PLAN_CT_E - PLAN_AISLE_E - PLAN_ISLAND_L, PLAN_CT_E - PLAN_AISLE_E,      # x 26.808 .. 33.808
               PLAN_CT_S - PLAN_AISLE_S - PLAN_ISLAND_D, PLAN_CT_S - PLAN_AISLE_S)      # z 21.058 .. 25.058
ISLAND_END = 0.25         # worktop past the end panels (3in)
ISLAND_LIP_S = 0.09       # worktop past the drawer faces on the kitchen side (1in)
ISLAND_LIP_N = 1.0        # worktop past the panelled back on the living-room side: a 12in seating overhang
ISLAND_STACKS = 4         # drawer stacks (19in each) / back panels

# North end of the east run: the worktop ends on the south jamb of the living / dining east window W07, as it
# always has (RUN_E0 was 21.84, the old window's jamb). Eighth round: that window is the sheet's 5'-0" at
# z 16.066..21.066 on the built plan (revision_spec.DINING_EAST_WIN_Z, the glazing track), so the run is the
# sheet's 10'-0" long (ska002 KT02 starts at z 21.058) and its first cabinet is 6in wider.
try:
    from ..revision_spec import DINING_EAST_WIN_Z as _W07_Z
except Exception:                          # a spec without it: the sheet's own numbers
    _W07_Z = (R.ZN + 15.841, R.ZN + 20.841)
PLAN_RUN_E0 = _W07_Z[1] + 0.026            # the end panel's face; the worktop ends 0.02 north of it, clear of the jamb
RUN_E0 = _pz(PLAN_RUN_E0)                  # 21.330
CT_FRONT_S = _pz(PLAN_CT_S)       # 29.388 (29.13 until the seventh round: 2'-3" deep on the built plan)
FRONT_S = CT_FRONT_S + 0.08       # face of the south-run base fronts
TALL_FRONT_S = CT_FRONT_S - FT_T  # face of the tall wall's fronts: a 2'-0" carcass with its doors in front
CT_FRONT_E = _px(PLAN_CT_E)       # 38.532 (38.405 until the seventh round: 2'-1 1/2" deep on the built plan)
FRONT_E = CT_FRONT_E + 0.083      # face of the east-run fronts
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
# fireclay apron sink outer footprint (x0, x1, z0, z1): 30in wide, 18-1/2in front to back (20in until the
# counter became 2'-0" deep: the bridge faucet keeps its place in front of the window stool, so the bowl gave
# up 3/4in); the apron stands 0.035 behind the worktop's front edge, as before
SINK = (CT_FRONT_E + 0.035, CT_FRONT_E + 0.035 + 1.60, 25.137, 27.637)
SINK_BOT = 2.16           # bottom of the apron (10in apron)
Y_B0 = TOE_H + 0.012      # bottom of base fronts
Y_B1 = CT_UNDER - 0.012   # top of base fronts
Y_DR = Y_B1 - 0.5         # top drawer bottom (6in drawers)
# 36in gas cooktop (x0, x1, z0, z1): the same deck (20-1/2in), 1-1/2in behind the worktop's front edge
COOK = (33.30, 36.30, CT_FRONT_S + 0.125, CT_FRONT_S + 0.125 + 1.73)
# island worktop (x0, x1, z0, z1) on the concept plan; the dining table continues its west end
ISLAND = (_px(PLAN_ISLAND[0]), _px(PLAN_ISLAND[1]), _pz(PLAN_ISLAND[2]), _pz(PLAN_ISLAND[3]))
POT_FILLER = (34.80, 4.55)               # (x, y) on the wall inside the slab's scallop


# Appliances of the tall wall (owner's seventh round). West -> east: refrigerator bay | oven tower.
APPL_HANDLE = 'brass'     # handles of the refrigerator, the microwave and the wall oven: 'brass' (the kitchen's
                          # hardware; the wall oven has had it since the third round) or 'stainless'
TOPCAB_Y0 = 6.03          # bottom of the top doors, one line across the refrigerator bay and the oven tower
OVEN_Y = (1.60, 3.78)     # 27in wall oven (lower unit of the tower): fascia bottom / top
MW_Y = (3.92, 5.50)       # built-in microwave above it: 27in trim kit, 19in high (the oven's face is 26in)
# Refrigerator: 36in-class counter-depth French-door with a bottom freezer drawer. Feet on the ARCHITECT'S plan
# (C.PlanFace): it fills the fitted bay between the hall-side end panel and the oven tower.
RF_SIDE = 0.012           # reveal between the appliance and the bay's sides (1/8in)
RF_FOOT = 0.085           # underside of the case above the floor (rollers, behind the base grille)
RF_CASE_TOP = 5.76        # top of the case: 69-1/8in
RF_DOOR_TOP = 5.80        # top of the doors: 69-5/8in
RF_CAP_TOP = 5.885        # top of the hinge covers: 70-5/8in over all
RF_SPLIT = 2.385          # centre of the reveal between the freezer drawer and the doors
RF_REVEAL = 0.03          # that reveal (3/8in)
RF_MID = 0.02             # reveal between the two doors (1/4in)
RF_PROUD = 0.20           # door faces in front of the cabinet fronts (2-3/8in): the case stands flush behind
                          # the fronts, as a counter-depth unit does; the doors swing clear of the surround
RF_DOOR_T = 0.245         # door / drawer-front thickness (3in)
RF_GASKET = 0.03          # gasket zone between the doors and the case
RF_BACK = 0.085           # air space between the case and the wall (1in)
RF_GRIP = (0.033, 0.165)  # handles: bar radius (a 13/16in tube), its axis in front of the door face (2in)

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
        # appliances: brushed stainless is the house material 'stainless' (the wall oven, the hood liner)
        self.steel = g._mat('stainless')
        self.handle = self.brass if APPL_HANDLE == 'brass' else self.steel
        self.appl_case = principled('appliance_case', srgb('#3a3c3f'), 0.55)        # painted steel case
        self.appl_dark = principled('appliance_dark', srgb('#161719'), 0.5)         # base grille, vent slots
        self.appl_grey = principled('appliance_grey', srgb('#85888c'), 0.38)        # hinge covers
        self.screen = principled('appliance_screen', srgb('#191b1e'), 0.28)         # microwave window mesh
        self.keys = principled('appliance_keys', srgb('#2e3034'), 0.45)             # touch-pad legends
        self.display = principled('appliance_display', srgb('#070d10'), 0.06)
        self.digits = principled('appliance_digits', srgb('#9fdcff'), 0.4, emission=srgb('#8fd6ff'), strength=3.0)


def build(ctx, g: Geo):
    M = _Mats(g)
    col = g.sub(COLL)
    hw = g.sub('kd hardware')
    lights = g.sub('kd_lights')
    notes = []
    _tall_wall(g, M, col, hw)
    _refrigerator(g, M, col, hw)
    _wall_oven(g, M, col)
    _microwave(g, M, col)
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
    notes.append('kitchen: greige pantry wall (stainless French-door refrigerator in its bay, built-in microwave '
                 'over a wall oven), cream shaker L runs 2ft deep, glass uppers, walnut open shelves, plaster hood, '
                 'fireclay sink, oak island 7ft x 4ft with quartzite top')
    notes.append(appliance_plan())
    notes.append(island_plan())
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
def _plan_face(w=0.0):
    """Face frame of the tall wall's fronts in feet on the ARCHITECT'S plan (region 'kitchen + dining':
    relayout.X_HALL / Z_RIGHT), `w` in front of the fronts."""
    return C.PlanFace('mz', R.Z_RIGHT(TALL_FRONT_S) - w, lambda x: _inv(R.X_HALL, x), lambda z: _inv(R.Z_RIGHT, z))


def _fridge_bay():
    """(x0, x1, z of the cabinet fronts, depth to the wall) of the refrigerator bay on the architect's plan."""
    zf = R.Z_RIGHT(TALL_FRONT_S)
    return R.X_HALL(FRIDGE[0]), R.X_HALL(FRIDGE[1]), zf, R.Z_RIGHT(WALL_S) - zf


def appliance_plan():
    """The tall wall's appliances on the built (architect's) plan, feet: what the build log and the notes
    report. The oven tower's units are loose: bl/warp.py moves them by the shift of their centre."""
    b0, b1, zf, depth = _fridge_bay()
    oc = R.X_HALL((OVEN[0] + OVEN[1]) / 2)
    r = lambda v: round(v, 3)                                            # noqa: E731
    return {'refrigerator': {'bay_x': [r(b0), r(b1)], 'body_x': [r(b0 + RF_SIDE), r(b1 - RF_SIDE)],
                             'width_in': r((b1 - b0 - 2 * RF_SIDE) * 12), 'height_in': r(RF_CAP_TOP * 12),
                             'case_depth_in': r((depth - RF_BACK - RF_GASKET - (RF_DOOR_T - RF_PROUD)) * 12),
                             'depth_with_doors_in': r((depth - RF_BACK + RF_PROUD) * 12),
                             'cabinet_fronts_z': r(zf), 'door_face_z': r(zf - RF_PROUD),
                             'handle_front_z': r(zf - RF_PROUD - RF_GRIP[1] - RF_GRIP[0]),
                             'doors_y': [RF_SPLIT + RF_REVEAL / 2, RF_DOOR_TOP],
                             'drawer_y': [r(Y_B0), RF_SPLIT - RF_REVEAL / 2]},
            'microwave': {'x': [r(oc - 1.125), r(oc + 1.125)], 'y': list(MW_Y), 'height_in': r((MW_Y[1] - MW_Y[0]) * 12)},
            'wall_oven': {'x': [r(oc - 1.125), r(oc + 1.125)], 'y': list(OVEN_Y)},
            'top_doors_y': [TOPCAB_Y0, UPPER_TOP]}


def _tall_wall(g, M, col, hw):
    """The greige 'pantry wall' of the closet references: the refrigerator's bay (hall-side end panel, a
    two-door cabinet over the appliance) and the oven tower (drawer, wall oven, microwave, top door) under
    one frieze and crown. The appliances themselves: _refrigerator, _wall_oven, _microwave."""
    F = C.Face('mz', TALL_FRONT_S)
    acc = C.Acc()
    # oven tower: drawer, niche backing (the appliances are loose, in front of it; it shows as the flat face
    # frame between and above them), top door
    o0, o1 = OVEN
    acc.shaker(F, o0 + GAP / 2, o1 - GAP / 2, Y_B0, 1.54)
    acc.shaker(F, o0 + GAP / 2, o1 - GAP / 2, TOPCAB_Y0, UPPER_TOP)
    acc.done(g, 'kd tall wall door panel run', M.greige, col)
    niche = C.Acc()
    niche.box(F, o0, o1, 1.55, 6.02, -FT_T, -0.02)
    niche.done(g, 'kd tall niche panel', M.greige, col, bevel=0.0)
    # cabinet over the refrigerator: two doors on the bay's centre line (built plan, like the appliance under
    # them: the reveal between the doors stands over the reveal between the refrigerator's doors)
    b0, b1, _, _ = _fridge_bay()
    um = (b0 + b1) / 2
    Fb = _plan_face()
    top = C.Acc()
    top.shaker(Fb, b0 + GAP / 2, um - GAP / 2, TOPCAB_Y0, UPPER_TOP)
    top.shaker(Fb, um + GAP / 2, b1 - GAP / 2, TOPCAB_Y0, UPPER_TOP)
    top.done(g, 'kd tall top door panel run', M.greige, col)
    # end panels (two stacked shaker panels on the hall side), side panel to the counter, kick, carcass
    side = C.Acc()
    Fw = C.Face('mx', TALL_X0)
    side.shaker(Fw, TALL_FRONT_S, WALL_S, 0.0, 3.4, sw=0.24)
    side.shaker(Fw, TALL_FRONT_S, WALL_S, 3.4, UPPER_TOP, sw=0.24)
    side.wbox(OVEN[1], BASE_X0, 0.0, UPPER_TOP, TALL_FRONT_S, WALL_S)
    side.done(g, 'kd tall end panel', M.greige, col)
    # The refrigerator stands on the floor in an open bay (no toe kick, no carcass behind it: its side and top
    # reveals are real gaps); the carcass is the oven tower and the cabinet over the bay.
    g.box('kd tall plinth', OVEN[0], OVEN[1], 0.0, TOE_H, TALL_FRONT_S + 0.10, WALL_S - 0.02, M.greige, coll=col)
    g.box('kd tall carcass', OVEN[0], OVEN[1], TOE_H, CEIL - 0.006, TALL_FRONT_S + FT_T + 0.01, WALL_S, M.greige, coll=col)
    g.box('kd tall carcass over refrigerator', FRIDGE[0], FRIDGE[1], TOPCAB_Y0 - 0.008, CEIL - 0.006,
          TALL_FRONT_S + FT_T + 0.01, WALL_S, M.greige, coll=col)
    # frieze behind the crown + crown with mitred returns on both ends
    g.box('kd tall carcass frieze', TALL_X0, BASE_X0, UPPER_TOP, CEIL - 0.006, TALL_FRONT_S + 0.004, TALL_FRONT_S + FT_T + 0.012,
          M.greige, coll=col)
    # v7 repair: the frieze returns along both ends behind the crown's returns. The end panels stop at UPPER_TOP and
    # the crown starts at CROWN_Y, 0.02 ft higher: a dark slot ran under the crown on both end faces (review E9).
    g.box('kd tall carcass frieze return W', TALL_X0 + 0.004, TALL_X0 + FT_T + 0.012, UPPER_TOP - 0.01, CEIL - 0.006,
          TALL_FRONT_S + FT_T + 0.012, WALL_S, M.greige, coll=col)
    g.box('kd tall carcass frieze return E', BASE_X0 - FT_T - 0.012, BASE_X0 - 0.004, UPPER_TOP - 0.01, CEIL - 0.006,
          TALL_FRONT_S + FT_T + 0.012, WALL_S, M.greige, coll=col)
    C.sweep(g, 'kd tall crown cove', [(TALL_X0, WALL_S - 0.004), (TALL_X0, TALL_FRONT_S), (BASE_X0, TALL_FRONT_S), (BASE_X0, WALL_S - 0.004)],
            C.crown_profile(0.24, CROWN_H), CROWN_Y, M.greige, col)
    # hardware: cups on the tower's drawer, a knob on each top door (the pair over the refrigerator on its
    # meeting stiles, the tower's on its east stile), all at one height
    _hw_drawer(g, M, F, o0, o1, Y_B0, 1.54, hw)
    for u in (um - GAP / 2 - 0.12, um + GAP / 2 + 0.12):
        C.knob(g, M.brass, Fb, u, 6.3, hw)
    C.knob(g, M.brass, F, o1 - 0.12, 6.3, hw)


def _refrigerator(g, M, col, hw):
    """Stainless-steel French-door refrigerator with a bottom freezer drawer, 36in class, counter depth, about
    70in high, standing in the bay at the hall end of the tall wall, directly beside the oven tower.

    Built in feet on the ARCHITECT'S plan (C.PlanFace) and named '... panel' (fitted): it fills the fitted
    bay, so it is 34-3/4in wide there (the bay is 35in; a 36in-class unit is 35-3/4in). The case stands flush
    behind the cabinet fronts with 1in of air behind it; doors and drawer front stand RF_PROUD in front of the
    fronts; the base grille stands in the plane of the oven tower's toe kick. Seen from the room (looking
    south) the viewer's left is +x."""
    b0, b1, _, depth = _fridge_bay()
    F = _plan_face()                     # w=0: the cabinet fronts
    Fd = _plan_face(RF_PROUD)            # w=0: the door faces
    u0, u1, um = b0 + RF_SIDE, b1 - RF_SIDE, (b0 + b1) / 2
    w_door = RF_PROUD - RF_DOOR_T        # back of the doors
    w_case = w_door - RF_GASKET          # front of the case
    y_dr0, y_dr1 = Y_B0, RF_SPLIT - RF_REVEAL / 2
    y_d0, y_d1 = RF_SPLIT + RF_REVEAL / 2, RF_DOOR_TOP
    N = 'kd refrigerator'
    case = C.Acc()
    case.box(F, u0, u1, RF_FOOT, RF_CASE_TOP, -(depth - RF_BACK), w_case)
    case.done(g, f'{N} case panel', M.appl_case, col, bevel=0.006)
    gasket = C.Acc()                     # dark behind every reveal between the doors and the drawer
    gasket.box(F, u0 + 0.035, u1 - 0.035, y_dr0 + 0.035, y_d1 - 0.035, w_case - 0.004, w_door + 0.004)
    gasket.done(g, f'{N} gasket panel', M.rubber, col, bevel=0.0)
    doors = C.Acc()
    doors.box(F, u0, um - RF_MID / 2, y_d0, y_d1, w_door, RF_PROUD)
    doors.box(F, um + RF_MID / 2, u1, y_d0, y_d1, w_door, RF_PROUD)
    doors.box(F, u0, u1, y_dr0, y_dr1, w_door, RF_PROUD)
    doors.done(g, f'{N} door panel', M.steel, col, bevel=0.014, seg=3)
    # base grille: a louvred kick plate in the plane of the tower's toe kick
    gr = C.Acc()
    gr.box(F, u0 + 0.012, u1 - 0.012, 0.015, TOE_H, -0.135, -0.118)
    n = 6
    for i in range(n):
        v = 0.052 + i * (TOE_H - 0.09) / (n - 1)
        gr.box(F, u0 + 0.05, u1 - 0.05, v - 0.013, v + 0.013, -0.12, -0.10)
    gr.done(g, f'{N} base grille panel', M.appl_dark, col, bevel=0.003)
    # hinge covers on the case's top corners, reaching forward over the doors' hinge pins
    caps = C.Acc()
    prof = [(-0.42, RF_CASE_TOP), (-0.42, RF_CAP_TOP), (RF_PROUD - 0.10, RF_CAP_TOP),
            (RF_PROUD - 0.10, RF_DOOR_TOP + 0.008), (w_door, RF_DOOR_TOP + 0.008), (w_door, RF_CASE_TOP)]
    caps.poly_u(F, prof, u0 + 0.012, u0 + 0.40)
    caps.poly_u(F, prof, u1 - 0.40, u1 - 0.012)
    caps.done(g, f'{N} top cap panel', M.appl_grey, col, bevel=0.008)
    # maker's badge, top corner of the left-hand door as one stands before it (no lettering)
    badge = C.Acc()
    badge.box(Fd, u1 - 0.36, u1 - 0.16, y_d1 - 0.30, y_d1 - 0.252, 0.0, 0.005)
    badge.done(g, f'{N} badge panel', g._mat('chrome'), col, bevel=0.0015)
    # handles: a vertical bar on each door's meeting edge, a horizontal bar across the top of the drawer
    names = (f'{N} grip panel', f'{N} grip mount panel', f'{N} grip foot panel')
    r, so = RF_GRIP
    for u in (um - RF_MID / 2 - 0.115, um + RF_MID / 2 + 0.115):
        C.tube_handle(g, M.handle, Fd, u, y_d0 + 0.20, u, y_d0 + 2.60, hw, names, r=r, standoff=so)
    C.tube_handle(g, M.handle, Fd, u0 + 0.27, y_dr1 - 0.17, u1 - 0.27, y_dr1 - 0.17, hw, names, r=r, standoff=so)


def _wall_oven(g, M, col):
    """27in wall oven, the lower unit of the tower (unchanged since the third round): loose appliance.
    Stainless door with a black-glass viewing window (closet reference: a stainless oven) rather than a full
    black-glass door, which read as a heavy dark slab in the greige wall."""
    oc = (OVEN[0] + OVEN[1]) / 2
    k = 0
    oy0, oy1 = OVEN_Y
    ox0, ox1 = oc - 1.125, oc + 1.125
    g.box(f'kd oven {k} fascia', ox0, ox1, oy0, oy1, TALL_FRONT_S - 0.035, TALL_FRONT_S + 0.012, 'stainless', 0.01, coll=col)
    g.box(f'kd oven {k} door', ox0 + 0.05, ox1 - 0.05, oy0 + 0.05, oy1 - 0.3, TALL_FRONT_S - 0.05, TALL_FRONT_S - 0.03,
          'stainless', 0.008, coll=col)
    g.box(f'kd oven {k} window', ox0 + 0.32, ox1 - 0.32, oy0 + 0.3, oy1 - 0.62, TALL_FRONT_S - 0.053, TALL_FRONT_S - 0.047,
          M.black_glass, 0.002, coll=col)
    g.box(f'kd oven {k} controls', ox0 + 0.05, ox1 - 0.05, oy1 - 0.22, oy1 - 0.05, TALL_FRONT_S - 0.045, TALL_FRONT_S - 0.03,
          M.black_glass, 0.006, coll=col)
    for kx in (-0.55, 0.55):
        g.cyl_axis(f'kd oven {k} knob', (oc + kx, oy1 - 0.135, TALL_FRONT_S - 0.045), (oc + kx, oy1 - 0.135, TALL_FRONT_S - 0.09),
                   0.045, M.handle, 24, col)
    hy = oy1 - 0.38
    g.cyl_axis(f'kd oven {k} handle', (ox0 + 0.2, hy, TALL_FRONT_S - 0.17), (ox1 - 0.2, hy, TALL_FRONT_S - 0.17), 0.028, M.handle, 20, col)
    for xx in (ox0 + 0.32, ox1 - 0.32):
        g.cyl_axis(f'kd oven {k} handle post', (xx, hy, TALL_FRONT_S - 0.05), (xx, hy, TALL_FRONT_S - 0.17), 0.017, M.handle, 16, col)


# seven-segment digits of the microwave's clock: segments a (top), b, c (right), d (bottom), e, f (left), g
_SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged'}


def _microwave(g, M, col):
    """Built-in microwave, the upper unit of the tower: a 27in stainless trim kit (vent slots in its top and
    bottom rails) around a black-glass door hinged on the left with a vertical handle on its right edge, and a
    black-glass control strip with a small clock display and a touch pad on the right, the refrigerator's
    side. 19in high: clearly lower than the 26in wall oven under it. Loose appliance like the oven (every part
    is named '... oven ...': 'microwave' alone contains bl/warp.py's fitted word 'wave'); concept feet are its
    real size. Seen from the room (looking south) the viewer's right is -x."""
    oc = (OVEN[0] + OVEN[1]) / 2
    y0, y1 = MW_Y
    ox0, ox1 = oc - 1.125, oc + 1.125
    N = 'kd microwave oven'
    zt = TALL_FRONT_S - 0.035                  # face of the trim kit (the wall oven's fascia plane)
    zd = zt - 0.05                        # face of the door and the control strip
    LAYER = 0.003                         # printed / applied layers stand 1mm proud (as the oven's window does)
    g.box(f'{N} trim', ox0, ox1, y0, y1, zt, TALL_FRONT_S + 0.012, 'stainless', 0.01, coll=col)
    ix0, ix1, iy0, iy1 = ox0 + 0.10, ox1 - 0.10, y0 + 0.16, y1 - 0.16
    slots = C.Acc()
    for yy in (y0 + 0.058, y0 + 0.100, y1 - 0.100, y1 - 0.058):
        slots.wbox(ix0 + 0.12, ix1 - 0.12, yy - 0.008, yy + 0.008, zt - LAYER, zt + 0.004)
    slots.done(g, f'{N} vent slots', M.appl_dark, col, bevel=0.0)
    cs = 0.50                             # control strip width
    dx0 = ix0 + cs + 0.012                # the door's right (west) edge
    g.box(f'{N} door', dx0, ix1, iy0, iy1, zd, zt + 0.004, M.black_glass, 0.006, coll=col)
    g.box(f'{N} door window', dx0 + 0.22, ix1 - 0.11, iy0 + 0.13, iy1 - 0.13, zd - LAYER, zd + 0.003, M.screen, coll=col)
    g.box(f'{N} control strip', ix0, ix0 + cs, iy0, iy1, zd, zt + 0.004, M.black_glass, 0.006, coll=col)
    # clock display at the top of the strip, digits 12:00 read from the room (viewer's right = -x)
    cx = ix0 + cs / 2
    g.box(f'{N} display', cx - 0.19, cx + 0.19, iy1 - 0.215, iy1 - 0.085, zd - LAYER, zd + 0.003, M.display, coll=col)
    dig = C.Acc()
    dw, dh, t = 0.034, 0.064, 0.0075
    yc = iy1 - 0.150
    za, zb = zd - 1.5 * LAYER, zd - 0.5 * LAYER

    def seg(s0, s1, v0, v1):              # s: to the viewer's right from the display's centre
        dig.wbox(cx - s1, cx - s0, v0, v1, za, zb)
    for ch, s in zip('1200', (-0.118, -0.066, 0.032, 0.084)):
        a, b = s, s + dw
        segs = {'a': (a, b, yc + dh / 2 - t, yc + dh / 2), 'g': (a, b, yc - t / 2, yc + t / 2),
                'd': (a, b, yc - dh / 2, yc - dh / 2 + t),
                'f': (a, a + t, yc, yc + dh / 2), 'e': (a, a + t, yc - dh / 2, yc),
                'b': (b - t, b, yc, yc + dh / 2), 'c': (b - t, b, yc - dh / 2, yc)}
        for k in _SEG[ch]:
            seg(*segs[k])
    for v in (yc + 0.014, yc - 0.014 - t):
        seg(-0.004, 0.004, v, v + t)      # colon
    dig.done(g, f'{N} display digits', M.digits, col, bevel=0.0)
    # touch pad: two rows of function keys, a number pad, start / stop
    keys = C.Acc()
    kz0, kz1 = zd - LAYER, zd + 0.003
    for row, v in enumerate((0.30, 0.40, 0.535, 0.635, 0.735, 0.835)):
        for i in (-1, 0, 1):
            keys.wbox(cx + i * 0.135 - 0.052, cx + i * 0.135 + 0.052, iy1 - v - 0.062, iy1 - v, kz0, kz1)
    for i in (-1, 1):
        keys.wbox(cx + i * 0.10 - 0.085, cx + i * 0.10 + 0.085, iy1 - 1.085, iy1 - 0.985, kz0, kz1)
    keys.done(g, f'{N} control keys', M.keys, col, bevel=0.0)
    # handle on the door's right edge: the wall oven's bar (same radius, same distance from the fronts), upright
    hx = dx0 + 0.105
    bar = g.cyl_axis(f'{N} handle', (hx, iy0 + 0.10, TALL_FRONT_S - 0.17), (hx, iy1 - 0.10, TALL_FRONT_S - 0.17), 0.028,
                     M.handle, 20, col)
    g.bevel_mod(bar, 0.008, 3)
    for yy in (iy0 + 0.24, iy1 - 0.24):
        g.cyl_axis(f'{N} handle post', (hx, yy, zd), (hx, yy, TALL_FRONT_S - 0.17), 0.017, M.handle, 16, col)


# ============================================================================= base runs
def _base_runs(g, M, col, hw, lights):
    Fs = C.Face('mz', FRONT_S)
    Fe = C.Face('mx', FRONT_E)
    acc = C.Acc()
    # the two runs meet in the corner: each ends just short of the other's worktop front (the units along the
    # walls keep their places; the last one of each run took up what the 2'-0" depth changed)
    S_END, E_END = CT_FRONT_E - 0.005, CT_FRONT_S - 0.01
    for (x0, x1), kind in (((BASE_X0, 30.70), 'doors2'), ((30.70, 33.30), 'drawers3'),
                           ((33.30, 36.30), 'drawers3'), ((36.30, S_END), 'doors2')):
        _base_unit(acc, g, M, Fs, x0, x1, kind, hw)
    # blind corner fillers
    acc.box(Fs, S_END, FRONT_E + FT_T, Y_B0, Y_B1, -FT_T, 0.0)
    acc.box(Fe, E_END, FRONT_S + FT_T, Y_B0, Y_B1, -FT_T, 0.0)
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
    _base_unit(acc, g, M, Fe, 27.887, E_END, 'drawers3', hw)
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
def island_plan():
    """The island on the built (architect's) plan, feet: what the build log and the notes report."""
    x0, x1, z0, z1 = PLAN_ISLAND
    r = lambda v: round(v, 3)                                            # noqa: E731
    return {'east_run_north_end_z': {'worktop': r(R.Z_RIGHT(RUN_E0 - 0.02)), 'end_panel': r(PLAN_RUN_E0)},
            'island': {'top_x': [r(x0), r(x1)], 'top_z': [r(z0), r(z1)],
                       'body_x': [r(x0 + ISLAND_END), r(x1 - ISLAND_END)],
                       'body_z': [r(z0 + ISLAND_LIP_N), r(z1 - ISLAND_LIP_S)],
                       'aisle_east': r(PLAN_CT_E - x1), 'aisle_south': r(PLAN_CT_S - z1),
                       'stacks': ISLAND_STACKS, 'stools': 0},
            'counter_front': {'east_x': r(PLAN_CT_E), 'south_z': r(PLAN_CT_S),
                              'tall_fronts_z': r(R.Z_RIGHT(TALL_FRONT_S))}}


def _island(g, M, col, hw):
    """White-oak drawer island under a 2in honed quartzite top with an eased edge: 7'-0" x 4'-0" at the
    sheet's place (eighth round; 5'-9" x 3'-0" before). Four 19in drawer stacks to the kitchen, a panelled
    back toward the living room under a 12in overhang, furniture end panels with a centre stile; the dining
    table stands against the west one. No stools: the table continues the island (architect's plan).

    Built in feet on the ARCHITECT'S plan (C.PlanFace; _px / _pz for the boxes) and named as fitted pieces, so
    after the warp every number here is the built one: stiles, rails and reveals are true to size."""
    x0, x1, z0, z1 = PLAN_ISLAND
    t = 0.167
    top = g.box('kd island top', _px(x0), _px(x1), TOP - t, TOP, _pz(z0), _pz(z1), M.quartzite, coll=col)
    _soft_edge(g, top, 0.022, 3)
    bx0, bx1 = x0 + ISLAND_END, x1 - ISLAND_END       # outer faces of the end panels
    zf = z1 - ISLAND_LIP_S                            # drawer faces
    zb = z0 + ISLAND_LIP_N                            # back panel faces
    bz0, bz1 = zb + FT_T, zf - FT_T                   # carcass back / front
    yt = TOP - t - 0.002

    def face(facing, plane):
        return C.PlanFace(facing, plane, _px, _pz)
    # end panels: one frame over the whole depth with a centre stile (two upright panels: the body is 35in deep)
    ends = C.Acc()
    zm = (zb + zf) / 2
    for F in (face('mx', bx0), face('px', bx1)):
        ends.shaker(F, zb, zf, 0.0, yt, sw=0.22, rw=0.24)
        ends.box(F, zm - 0.11, zm + 0.11, 0.24, yt - 0.24, -RECESS, 0.0)
    ends.done(g, 'kd island end panel', M.oak, col)
    g.box('kd island carcass', _px(bx0 + FT_T), _px(bx1 - FT_T), TOE_H, yt, _pz(bz0), _pz(bz1), M.oak, coll=col)
    g.box('kd island plinth', _px(bx0 + FT_T), _px(bx1 - FT_T), 0.0, TOE_H, _pz(bz0 + 0.15), _pz(bz1 - 0.15), M.oak,
          coll=col)
    Ff = face('pz', zf)
    Fb = face('mz', zb)
    fronts = C.Acc()
    a0, a1 = bx0 + FT_T, bx1 - FT_T
    n = ISLAND_STACKS
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
