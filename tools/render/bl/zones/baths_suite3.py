"""Bedroom 3 bath (tour stop A3) of zone `baths`; see baths.py for the shared helpers.

Eighth round (2026-11-24), the owner after the audit of the model against the architect's set: "can you fix all
these issues?" (finding F33). The room is laid out as sheet SKA002 draws it (bl/revision_spec.py, BED3_BATH_*):

  * shower 3'-0" wide across the west end (x 0.225..3.225), the window W11 inside it as the owner set it;
  * toilet bay 2'-6" (x 3.225..5.725): the wall-hung WC on the NORTH wall, on the bay's centre line;
  * vanity bay 2'-9" (x 5.725..8.475): the floating vanity on the NORTH wall, 1'-9" deep, against the east wall;
  * door D05 at the east end of the south wall (hinged; the leaf opens along the east wall): bl/zones/
    bedrooms_rooms.py builds the wall, the liners, the saddle and the leaf.
  (Until the seventh round, from the concept plan: shower 3'-3 7/16", WC 9 in further east, the vanity on the
  east wall, a pocket door further west.)

Finishes, tile, glass and fittings are the seventh round's, re-arranged: honed limestone-look porcelain on the
walls (Z_baths_porcelain), the furred wet wall with the lit niche over the valve and the rain head, a fixed
walk-in glass panel in a black channel with a ceiling stay, mosaic shower floor with a linear drain, the black
fluted porcelain as a full-height panel behind the vanity and its pill mirror (it was the whole east wall when
the vanity stood there), walnut vanity with a quartz top and an undermount basin, black fittings. The bath
towel hangs on the south wall beside the shower's entry, where the door leaves it free; the soap bottle that
stood in the south wall stands on the vanity.

BUILT AFTER THE WARP, IN PLAN FEET, like the primary bath: build_room() is called by
bl/revisions.bedroom3_fit_out after the revisions that prepare the architecture (bedroom3_bath_window: W11;
bedroom3_rooms: the south wall and its door). baths.build_suite3(), called with the other baths before the warp,
only makes the collection. A number here is a number of the sheet.
"""
import re

import bpy

from .. import lighting
from .. import revision_spec as S
from ..revisions import bbox
from . import baths_kit as K
from .baths import CAN_K, CEIL, T, ZONE, floating_vanity

C = f'{ZONE}_suite3'
FB, FD = 0.055, 0.035                          # fluted tile: bed + rib depth (as in the shared bath)


def build_room(ctx):
    c = C
    ctx.coll(c, ZONE)
    X0, X1, Z0, Z1 = S.BED3_BATH_CLEAR
    FL = S.BED3_BATH_FLOOR_Y
    XW, ZN, XE, ZS = X0 + T, Z0 + T, X1 - T, Z1 - T
    SX = S.BED3_BATH_SHOWER[1]                 # the shower's glass line
    VX0, VX1, _, VZ1 = S.BED3_BATH_VANITY
    ZC = Z0 + FB + FD                          # rib crests of the fluted panel behind the vanity
    ZNF = ZN + 0.30                            # furred shower wet wall (3.6 in) for the LED niche
    SC = (X0 + SX) / 2 + 0.025                 # valve, niche and rain head: the middle of the shower's tiled width
    NX0, NX1, NY0, NY1 = SC - 0.60, SC + 0.60, 4.30, 5.25
    por = K.porcelain_material(ctx)
    WY0, WY1 = S.BED3_BATH_WIN_Y               # W11 as the owner set it: sill 3'-0", head 7'-6"
    WZ0, WZ1 = S.BED3_BATH_WIN_Z
    ln, head = S.DOOR_LINER, S.DOOR_HEAD
    d0, d1 = S.BED3_BATH_DOOR_X

    # ---- walls
    K.skin(ctx, 'A3 tile west', 'x', X0, XW, Z0, Z1, FL, CEIL, por, c, holes=[(WZ0, WZ1, WY0, WY1)])
    K.skin(ctx, 'A3 wetwall', 'z', Z0, ZNF, XW, SX, FL, CEIL, por, c, holes=[(NX0, NX1, NY0, NY1)])
    K.box(ctx, 'A3 niche back', NX0 + 0.001, NX1 - 0.001, NY0, NY1, Z0, ZN + 0.02, por, c)
    K.box(ctx, 'A3 niche sill', NX0 + 0.002, NX1 - 0.002, NY0 - 0.03, NY0 + 0.012, ZN + 0.02, ZNF + 0.004,
          'quartz_white', c, bevel=0.004)
    s = K.box(ctx, 'A3 niche led', NX0 + 0.02, NX1 - 0.02, NY1 - 0.022, NY1 - 0.004, ZNF - 0.14, ZNF - 0.03, None, c)
    s.data.materials.append(lighting.emitter('niche_led', 3500, 16.0))
    K.bottle(ctx, c, 'A3 niche bottle 1', SC - 0.17, NY0 + 0.012, ZN + 0.17, r=0.075, h=0.5)
    K.bottle(ctx, c, 'A3 niche bottle 2', SC + 0.15, NY0 + 0.012, ZN + 0.17, r=0.075, h=0.5,
             mat=K.matte_material('bottle_white', (0.80, 0.79, 0.76), 0.5))
    K.skin(ctx, 'A3 tile north', 'z', Z0, ZN, SX, VX0, FL, CEIL, por, c)          # the toilet bay
    # the vanity bay: black fluted porcelain, floor to ceiling, behind the floating vanity and the pill mirror. Its
    # valleys lie 0.01 ft behind the plain tile's face at both ends, so the plain tile closes the panel's edges.
    K.fluted_wall(ctx, 'A3 fluted tile north', 'z', Z0, 1, VX0, XE, FL, CEIL, FB, FD, 0.10, K.fluted_material(ctx), c)
    K.skin(ctx, 'A3 tile east', 'x', XE, X1, Z0, Z1, FL, CEIL, por, c)
    K.skin(ctx, 'A3 tile south', 'z', ZS, Z1, XW, XE, FL, CEIL, por, c, holes=[(d0 - 2 * ln, d1 + 2 * ln, 0.0, head + 0.06)])
    # W11 sits inside the shower: tiled reveal returns on the jambs and a quartz sill over the frame's inner rail
    K.box(ctx, 'A3 window return sill', X0 - 0.134, XW + 0.012, WY0, WY0 + 0.09, WZ0, WZ1, 'quartz_white', c, bevel=0.006)
    for z0, z1 in ((WZ0, WZ0 + 0.035), (WZ1 - 0.035, WZ1)):
        K.box(ctx, 'A3 window return', X0 - 0.134, XW, WY0 + 0.09, WY1, z0, z1, por, c)

    # ---- curbless shower: mosaic floor, walk-in fixed panel, black trim
    K.box(ctx, 'A3 shower floor', X0, SX, FL, FL + 0.015, Z0, Z1, 'tile_shower_floor', c)
    sy = FL + 0.015
    K.linear_drain(ctx, c, 'A3 drain', 'z', ZNF + 0.15, Z1 - 0.38, XW + 0.18, sy)
    gx = SX - 0.016                            # the glass stands inside the 3'-0"
    gz = Z0 + 2.57                             # its free end: a 2'-5" walk-in gap to the south wall
    K.glass_panel(ctx, c, 'A3 glass', (gx, ZNF + 0.006), (gx, gz), sy + 0.02, 6.75)
    K.u_channel(ctx, c, 'A3 channel', (gx, ZNF + 0.004), (gx, gz), sy)
    for yy in (1.1, 5.9):
        K.clamp(ctx, c, 'A3 wall clamp', gx, yy, ZNF + 0.07, 'z')
    K.clamp(ctx, c, 'A3 post clamp', gx, 6.72, gz - 0.10, 'z', size=(0.10, 0.08, 0.07))
    ctx.cylinder('A3 ceiling stay', (gx, (6.76 + 8.0) / 2, gz - 0.10), 0.025, 8.0 - 6.76, K.BLACK, c, verts=24)
    ctx.cylinder('A3 ceiling stay rose', (gx, 7.99, gz - 0.10), 0.055, 0.02, K.BLACK, c, verts=24)
    fn = K.Frame(0.0, ZN, 0.0, 1.0)            # north wall: u = z - ZN, v = x
    fnf = K.Frame(0.0, ZNF, 0.0, 1.0)          # furred shower wall
    K.valve_trim(ctx, fnf, c, 'A3 valve', SC, 3.65)
    K.rain_head_wall(ctx, fnf, c, 'A3 rain', SC, 6.72, arm=1.1, dia=0.70)

    # ---- wall-hung WC on the north wall, on the centre line of its 2'-6" bay
    tx = S.BED3_BATH_TOILET_X
    fw = K.Frame(tx, ZN, 0.0, 1.0)
    K.wall_hung_wc(ctx, fw, c, 'A3 WC')
    K.flush_plate(ctx, fw, c, 0.0, 3.45, 'A3 flush plate')
    K.tp_holder(ctx, fn, c, 'A3 paper', tx + 0.76, 2.25)

    # ---- floating vanity on the north wall in front of the fluted panel, pill mirror
    fv = K.Frame(0.0, ZC, 0.0, 1.0)            # u = z - ZC (from the rib crests), v = x
    v0, v1 = VX0, XE - 0.012
    sv = S.BED3_BATH_BASIN_X
    depth = VZ1 - ZC                           # the front stands 1'-9" off the wall's face, as the sheet draws it
    uc = 0.90
    floating_vanity(ctx, fv, c, 'A3 vanity', v0, v1, depth, 1.30, 'quartz_white',
                    [(v0 + 0.006, v1 - 0.006, 1.30, 2.58)], holes=[(uc, sv, 0.36, 0.50)])
    K.undermount_bowl(ctx, fv, c, 'A3 basin', uc, sv, 2.675, a=0.38, b=0.52, depth=0.42)
    K.deck_faucet(ctx, fv, c, 'A3 faucet', 0.26, sv, 2.80, height=0.72, reach=0.44, r=0.035)
    K.pill_mirror(ctx, fv, c, 'A3 mirror', sv, 5.0, 1.55, 2.6)
    fe = K.Frame(XE, 0.0, -1.0, 0.0)           # east wall: u = XE - x, v = z
    K.outlet(ctx, fe, c, 'A3 outlet', Z0 + 1.15, 3.55)
    K.exhaust_grille(ctx, c, 'A3 exhaust', tx, Z0 + 3.4)
    x, z = fv.w(0.95, v0 + 0.44)
    sage = K.towel_band_material('towel_sage', K.SAGE_TOWEL)
    K.folded_towel(ctx, c, 'A3 hand towel 0', x, 2.80, z, 0.70, 0.42, 0.075, 0.0, sage)
    K.folded_towel(ctx, c, 'A3 hand towel 1', x, 2.875, z, 0.68, 0.40, 0.075, 0.03, sage)
    x, z = fv.w(0.34, v1 - 0.32)
    K.bottle(ctx, c, 'A3 soap', x, 2.80, z, r=0.09, h=0.5, mat=K.matte_material('bottle_white', (0.80, 0.79, 0.76), 0.5))
    soap = (x, z)

    # ---- bath towel on the south wall, between the shower's entry and the door
    fs = K.Frame(0.0, ZS, 0.0, -1.0)           # south wall: u = ZS - z, v = -x
    bx0, bx1 = SX + 0.62, d0 - 2 * ln - 0.40
    u = K.towel_bar(ctx, fs, c, 'A3 towel bar', -bx1, -bx0, 3.95)
    yb = 3.95 + 0.026 - 0.98
    K.draped(ctx, fs, c, 'A3 bath towel', u, u, -bx1 + 0.20, -bx0 - 0.20, 3.95 + 0.026, 1.10, 0.98,
             K.towel_band_material('towel_A3', K.SAGE_TOWEL, (yb + 0.16, yb + 0.30)), th=0.05, rc=0.026)

    # ---- ceiling lights: one over the rain head, one over the room
    cans = [(SC, Z0 + 1.37), ((SX + X1) / 2, Z0 + 2.9)]
    for x, z in cans:
        lighting.can(ctx, x, z, coll=f'{ZONE}_lights', watts=9.0, kelvin=CAN_K)

    # ---- checks: the finish fits the window as built, nothing stands in a wall
    bpy.context.view_layer.update()
    fin = {ob.name: bbox(ob) for ob in ctx.coll(c).all_objects if ob.type == 'MESH' and re.match(r'A3 (tile west|window)', ob.name)}
    across = [n for n, b in fin.items() if n.startswith('A3 tile west')
              and b[4] < WZ1 - 0.01 and b[5] > WZ0 + 0.01 and b[2] < WY1 - 0.01 and b[3] > WY0 + 0.01]
    off = [n for n, b in fin.items() if n.startswith('A3 window')
           and (b[4] < WZ0 - 0.02 or b[5] > WZ1 + 0.02 or b[2] < WY0 - 0.02 or b[3] > WY1 + 0.02)]
    if across or off:
        raise RuntimeError(f'bath finish does not fit the window: tile across it {across}, sill / returns off it {off}')
    loose = re.compile(r'A3 (WC|vanity|basin|faucet|mirror|soap|hand towel|bath towel|towel bar|paper|flush|outlet)')
    out_of_room = []
    for ob in ctx.coll(c).all_objects:
        if ob.type == 'MESH' and loose.match(ob.name):
            b = bbox(ob)
            if b[0] < X0 - 1e-3 or b[1] > X1 + 1e-3 or b[4] < Z0 - 1e-3 or b[5] > Z1 + 1e-3:
                out_of_room.append((ob.name, [round(float(v), 3) for v in b]))
    if out_of_room:
        raise RuntimeError(f'bath fixtures in a wall: {out_of_room[:6]}')
    r3 = lambda v: [round(float(a), 3) for a in v]       # noqa: E731
    return {'clear': r3(S.BED3_BATH_CLEAR), 'shower x': r3((X0, SX)), 'glass x': round(gx, 3), 'glass z': r3((ZNF + 0.006, gz)),
            'toilet centre x': round(tx, 3), 'vanity': r3((v0, v1, Z0, VZ1)), 'basin centre x': round(sv, 3),
            'fluted panel x': r3((VX0, XE)), 'towel bar x': r3((bx0, bx1)), 'soap (x, z)': r3(soap), 'cans': [r3(p) for p in cans],
            'window finish': {n: r3(b) for n, b in fin.items() if n.startswith('A3 window')},
            'objects': len(ctx.coll(c).all_objects)}
