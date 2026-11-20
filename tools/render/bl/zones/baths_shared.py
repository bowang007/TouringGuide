"""Shared bath (tour stop A1) of zone `baths`; see baths.py for the shared helpers.

Owner's restyle (styles/shared_bathroom_style.jpg + styles/shared bathroom wall style.jpg):
  * West feature wall in rustic-oak wood-look porcelain planks (8in, vertical, staggered). Behind the
    wall-hung WC it steps forward as a full-height 4.8in chase (the WC carrier wall) with a recessed,
    LED-lit two-tier niche over the WC (wood-lined, one wood shelf), and a recessed linear LED in the
    ceiling grazes the planks from above (the warm wash of the reference).
  * The other walls in warm "Spanish cream" stone-look porcelain, 24 x 48in laid vertical (two rows
    to the 8ft ceiling); the floor in light warm limestone-look 24 x 48in tile (a calm light floor
    against the wood wall), one tile centred on the room and a joint along the tub apron.
  * Floating light-oak vanity (one drawer, shadow-gap pull) under a 6.6in honed travertine block with
    an integrated trough basin; wall-mounted brushed-nickel spout with a side lever; rectangular
    backlit mirror; warm toe glow.
  * Alcove tub wall to wall with its fixed glass screen, the shower trim on the wood wall, the furred
    tub back wall with its LED niche (cream tile, travertine sill). All fittings brushed nickel.
  * The cove, niche strips and mirror halo are accents; the cans light the room. A stronger cove (it was
    110) out-lit the cans, and its bounce off the wood tinted the white ceiling the auto white balance
    reads, turning the A1 panorama green-cyan.

The room is built on the concept plan; bl/warp.py then scales it onto the architect's plan (fitted
pieces are reshaped, loose ones move rigidly per cluster, anchored to a wall face within 0.2 ft).
The chase face is 0.4ft off the shell wall, so the loose pieces mounted on it (WC, flush plate,
paper holder, niche decor) are tied to the wall by a hidden carrier and mounted at XB, the concept
x that lands exactly on the warped chase face (see _chase_mount_x).
"""
import bpy

from .. import lighting
from . import baths_kit as K
from . import baths_shared_mats as M
from .baths import CEIL, T, ZONE, _bounds, _toe_glow

FLOOR_NAME = 'Shared bathroom porcelain floor'


def _remap():
    try:
        import relayout as R
        return R.remap_xz
    except Exception as e:                        # concept plan only (no warp available)
        print('[baths_shared] relayout unavailable, identity map:', repr(e))
        return lambda x, z, *a, **k: (x, z)


def _chase_mount_x(remap, xa, xc, zc):
    """Concept x for loose pieces on the chase face xc whose cluster is anchored at xa (a wall-side
    edge within relayout.TOUCH of the shell wall): the cluster moves by f(xa) - xa, so a piece at
    xa + (f(xc) - f(xa)) lands exactly on the warped face f(xc)."""
    return xa + (remap(xc, zc)[0] - remap(xa, zc)[0])


def _square_wc(ctx, f, c, name):
    """Wall-hung WC with a squarer, boxier bowl than the kit's (as in the reference): pan 21in deep x
    14.4in wide, rim 15.6in, closed seat + lid on top (16.9in)."""
    rings = [
        K.R(0.92, 0.08, 1.36, 0.42, 4.0, 8.0),
        K.R(0.945, 0.03, 1.52, 0.51, 4.5, 8.0),
        K.R(1.00, 0.008, 1.64, 0.575, 5.0, 8.0),
        K.R(1.10, 0.0, 1.715, 0.60, 5.5, 8.0),
        K.R(1.272, 0.0, 1.725, 0.60, 5.5, 8.0),
        K.R(1.292, 0.004, 1.717, 0.592, 5.5, 8.0),
        K.R(1.30, 0.012, 1.705, 0.58, 5.5, 8.0),
    ]
    K.loft(ctx, f, name + ' pan', rings, K.CERAMIC, c)
    u0, u1, b, y0 = 0.17, 1.74, 0.60, 1.30
    lid = [
        K.R(y0 + 0.002, u0 + 0.03, u1 - 0.03, b - 0.03, 5.5, 6.0),
        K.R(y0 + 0.012, u0, u1, b, 5.5, 6.0),
        K.R(y0 + 0.032, u0, u1, b, 5.5, 6.0),
        K.R(y0 + 0.039, u0 + 0.008, u1 - 0.012, b - 0.012, 5.5, 6.0),      # seat / lid seam
        K.R(y0 + 0.047, u0, u1 - 0.002, b - 0.002, 5.5, 6.0),
        K.R(y0 + 0.085, u0, u1 - 0.002, b - 0.002, 5.5, 6.0),
        K.R(y0 + 0.098, u0 + 0.03, u1 - 0.035, b - 0.035, 5.5, 6.0),
        K.R(y0 + 0.102, u0 + 0.07, u1 - 0.075, b - 0.075, 5.5, 6.0),
    ]
    K.loft(ctx, f, name + ' seat+lid', lid, K.CERAMIC, c)


def _wall_faucet(ctx, f, c, name, v, y, mat, reach=0.56, lever_dv=0.48):
    """Wall-mounted basin spout (round rose + slim tube) with a separate side lever at the same height."""
    K.fcyl(ctx, f, name + ' plate', 0.012, v, y, 0.085, 0.024, 'u', mat, c, verts=48)
    K.fcyl(ctx, f, name + ' spout', 0.02 + reach / 2, v, y, 0.03, reach, 'u', mat, c)
    K.fcyl(ctx, f, name + ' aerator', reach - 0.02, v, y - 0.03, 0.025, 0.012, 'y', mat, c)
    lv = v + lever_dv
    K.fcyl(ctx, f, name + ' lever plate', 0.012, lv, y, 0.065, 0.024, 'u', mat, c, verts=48)
    K.fcyl(ctx, f, name + ' lever hub', 0.06, lv, y, 0.03, 0.08, 'u', mat, c)
    K.fbox(ctx, f, name + ' lever', 0.088, 0.112, lv - 0.014, lv + 0.014, y - 0.01, y + 0.17, mat, c, bevel=0.006)


def _backlit_mirror(ctx, f, c, name, v0, v1, y0, y1, standoff=0.075, kelvin=4500, glow=6.0):
    """Frameless rectangular mirror floating off the wall with a warm LED halo washing the wall."""
    K.fbox(ctx, f, name + ' glass', standoff - 0.02, standoff, v0, v1, y0, y1, 'mirror', c, bevel=0.006, seg=2)
    back = K.fbox(ctx, f, name + ' backlight', 0.01, standoff - 0.022, v0 + 0.12, v1 - 0.12, y0 + 0.12, y1 - 0.12,
                  None, c)
    back.data.materials.append(lighting.emitter('A1_mirror_back', kelvin, glow))
    back.visible_camera = False


def _hidden(ob):
    ob.hide_render = True
    ob.display_type = 'WIRE'
    ob.visible_camera = False
    ob.visible_shadow = False
    return ob


# -------------------------------------------------------------------------------- shared
def build_shared(ctx):
    c = f'{ZONE}_shared'
    X0, X1, Z0, Z1 = _bounds(ctx, 'M04')
    FL = 0.028
    XW, XE, ZN, ZS = X0 + T, X1 - T, Z0 + T, Z1 - T
    remap = _remap()
    zc = (Z0 + Z1) / 2
    crema, wood, trav = M.crema(ctx), M.woodtile(ctx), M.travertine(ctx)
    oak, nickel = M.oak(ctx), M.nickel(ctx)

    # ---- layout (concept plan, SCENE ft) -------------------------------------------------
    VD = 1.55                                  # vanity depth
    ZV = ZN + VD                               # vanity front = the chase's north face
    XC = X0 + 0.40                             # chase face: 4.8in proud of the shell wall incl. tile
    ZT = ZS - 0.30                             # finished face of the furred tub back wall
    D, TOP = 2.66, 1.62                        # tub depth / rim height
    ZA = ZT - D                                # tub apron line
    C1 = ZA - 0.003                            # chase south face, a hair clear of the apron
    WCZ = 24.8                                 # WC centreline (unchanged)
    NZ0, NZ1, NY0, NY1 = WCZ - 0.75, WCZ + 0.75, 4.05, 6.45     # lit niche over the WC
    SY0, SY1 = 5.17, 5.27                      # its wood shelf
    xa = XW + 0.005                            # wall-side edge of the hidden carrier (anchors the cluster)
    XB = _chase_mount_x(remap, xa, XC, zc)

    # ---- walls ---------------------------------------------------------------------------
    K.skin(ctx, 'A1 tile west', 'x', X0, XW, Z0, Z1, FL, CEIL, wood, c)
    K.skin(ctx, 'A1 wood tile chase', 'x', XW, XC, ZV, C1, FL, CEIL, wood, c, holes=[(NZ0, NZ1, NY0, NY1)])
    K.skin(ctx, 'A1 tile north', 'z', Z0, ZN, XW, XE, FL, CEIL, crema, c, holes=[(13.0113, 15.4800, 0.0, 6.67)])
    K.skin(ctx, 'A1 tile east', 'x', XE, X1, Z0, Z1, FL, CEIL, crema, c)
    # tub back wall furred 3.6in (the shell wall cannot be cut) for a recessed LED niche at the shower end
    TX0, TX1, TY0, TY1 = 11.20, 13.05, 3.95, 4.95
    K.skin(ctx, 'A1 tile south', 'z', ZT, Z1, XW, XE, FL, CEIL, crema, c, holes=[(TX0, TX1, TY0, TY1)])
    K.box(ctx, 'A1 bath niche back', TX0 + 0.001, TX1 - 0.001, TY0, TY1, Z1 - 0.03, Z1, crema, c)
    K.box(ctx, 'A1 bath niche sill', TX0 + 0.002, TX1 - 0.002, TY0 - 0.03, TY0 + 0.012, ZT - 0.004, Z1 - 0.03,
          trav, c, bevel=0.004)
    s = K.box(ctx, 'A1 bath niche led strip', TX0 + 0.02, TX1 - 0.02, TY1 - 0.022, TY1 - 0.004, ZT + 0.03, ZT + 0.14,
              None, c)
    s.data.materials.append(lighting.emitter('A1_niche_led', 3500, 10.0))
    # a 1/2in tile lip at the front of the niche head hides the strip (only its glow shows), as in the WC niche
    K.box(ctx, 'A1 bath niche tile lip', TX0 + 0.001, TX1 - 0.001, TY1 - 0.045, TY1, ZT + 0.003, ZT + 0.028, crema, c)
    K.bottle(ctx, c, 'A1 bath niche bottle 1', 11.62, TY0 + 0.012, Z1 - 0.20, r=0.085, h=0.55,
             mat=M.matte('bottle_amber', '#6b3d1c', 0.35))
    K.bottle(ctx, c, 'A1 bath niche bottle 2', 11.90, TY0 + 0.012, Z1 - 0.20, r=0.085, h=0.55,
             mat=M.matte('bottle_cream', '#e2dccf', 0.5))

    # ---- WC chase: lit two-tier niche with a wood shelf ------------------------------------
    nb = K.box(ctx, 'A1 tile niche back', XW, XW + 0.006, NY0, NY1, NZ0, NZ1, wood, c)
    nb['tg_wood_shift'] = 0.093
    shelf = K.box(ctx, 'A1 niche shelf', XW + 0.006, XC - 0.012, SY0, SY1, NZ0, NZ1, wood, c, bevel=0.004)
    shelf['tg_wood_rot'] = 1.0                 # grain along the shelf edge, not plank joints across it
    # an LED strip under the niche head and under the shelf, each hidden behind a 1/2in wood lip at the
    # front edge, so only the glow shows (and the glass screen does not mirror bare diode lines)
    led = lighting.emitter('A1_niche_led', 3500, 11.0)
    for k, (ytop, xf) in enumerate(((NY1, XC), (SY0, XC - 0.012))):
        lip = K.box(ctx, f'A1 niche shelf lip {k}', xf - 0.03, xf, ytop - 0.045, ytop, NZ0, NZ1, wood, c)
        lip['tg_wood_rot'] = 1.0
        s = K.box(ctx, f'A1 niche led strip {k}', xf - 0.075, xf - 0.035, ytop - 0.014, ytop - 0.002,
                  NZ0 + 0.04, NZ1 - 0.04, None, c)
        s.data.materials.append(led)
    nx = XW + 0.16                             # decor stands mid-depth in the 4in niche
    K.bottle(ctx, c, 'A1 niche bottle 1', nx, NY0, WCZ - 0.30, r=0.075, h=0.50,
             mat=M.matte('bottle_amber', '#6b3d1c', 0.35))
    K.bottle(ctx, c, 'A1 niche bottle 2', nx, NY0, WCZ - 0.06, r=0.07, h=0.42,
             mat=M.matte('bottle_cream', '#e2dccf', 0.5))
    jar = ctx.cylinder('A1 niche jar', (nx, NY0 + 0.085, WCZ + 0.34), 0.10, 0.17, None, c, verts=40)
    jar.data.materials.append(trav)
    ctx.add_bevel(jar, 0.015, 3)
    ctx.cylinder('A1 niche jar lid', (nx, NY0 + 0.18, WCZ + 0.34), 0.085, 0.02, oak, c, verts=40)
    oat = K.towel_band_material('towel_A1_oat', K.OAT_TOWEL)
    for k in range(2):
        K.folded_towel(ctx, c, f'A1 niche folded towel {k}', nx + 0.005, SY1 + 0.075 * k, WCZ - 0.12 + 0.01 * k,
                       0.27, 0.62 - 0.02 * k, 0.075, 0.0, oat)
    # recessed linear LED in the ceiling grazing the wood chase from above
    K.box(ctx, 'A1 cove profile', XC + 0.02, XC + 0.15, CEIL - 0.014, CEIL, ZV + 0.06, C1 - 0.06,
          'paint_trim', c, bevel=0.003)
    s = K.box(ctx, 'A1 cove led strip', XC + 0.04, XC + 0.13, CEIL - 0.017, CEIL - 0.014, ZV + 0.08, C1 - 0.08,
              None, c)
    # an accent: at 110 it out-lit the room's cans ~1.3:1 and its wood bounce tinted the white ceiling
    # orange-red, so the auto white balance turned the A1 panorama green-cyan (4000K/-19)
    s.data.materials.append(lighting.emitter('A1_cove', 4500, 48.0))

    # ---- wall-hung WC on the chase (centreline z = 24.8), flush plate, paper ------------------
    _hidden(K.box(ctx, 'A1 WC carrier', xa, XC, 0.4, 3.6, 23.55, 25.30, None, c))
    fw = K.Frame(XB, WCZ, 1.0, 0.0)
    _square_wc(ctx, fw, c, 'A1 WC')
    K.flush_plate(ctx, fw, c, 0.0, 3.30, 'A1 flush plate')
    K.tp_holder(ctx, K.Frame(XB, 0.0, 1.0, 0.0), c, 'A1 paper', -23.98, 2.25)

    # ---- floating light-oak vanity, travertine block with an integrated trough ------------------
    fv = K.Frame(0.0, ZN, 0.0, 1.0)            # north wall: u = z - ZN, v = x
    v0, v1 = XW, 12.93
    vc = (v0 + v1) / 2
    YB, YT0, YT = 1.15, 2.30, 2.85
    fu1 = VD - 0.035
    fu0 = fu1 - 0.06
    K.fbox(ctx, fv, 'A1 vanity carcass', 0.0, fu0, v0, v1, YB, YT0, oak, c, bevel=0.006)
    K.fbox(ctx, fv, 'A1 vanity front 0', fu0, fu1, v0 + 0.006, v1 - 0.006, YB, YT0 - 0.035, oak, c, bevel=0.006)
    _toe_glow(ctx, fv, c, 'A1 vanity', fu0 - 0.16, fu0 - 0.08, v0 + 0.08, v1 - 0.08, YB)
    top = K.fbox(ctx, fv, 'A1 vanity top', 0.0, VD, v0, v1, YT0, YT, trav, c)
    bu, bv, ba, bb, bd = 0.80, vc + 0.04, 0.40, 0.60, 0.40          # basin centre, half sizes, depth
    cut = K.sink_cutter(ctx, fv, c, 'A1 vanity top cutter', bu, bv, YT - bd, YT + 0.1, ba, bb, 8)
    K.bool_cut(top, cut)
    ctx.add_bevel(top, 0.012, 3)
    K.fcyl(ctx, fv, 'A1 vanity top drain', bu, bv, YT - bd + 0.004, 0.055, 0.008, 'y', nickel, c)
    _wall_faucet(ctx, fv, c, 'A1 faucet', bv, 3.18, nickel)
    _backlit_mirror(ctx, fv, c, 'A1 mirror', vc - 0.875, vc + 0.875, 3.62, 6.30)
    x, z = fv.w(0.32, v1 - 0.21)
    K.bottle(ctx, c, 'A1 soap', x, YT, z, r=0.085, h=0.48, mat=M.matte('bottle_amber', '#6b3d1c', 0.35))
    # hand towel on a short bar on the wood wall beside the mirror
    fwt = K.Frame(XW, 0.0, 1.0, 0.0)            # west wall face: u = x - XW, v = -z
    hv0, hv1, hy = -22.70, -22.00, 4.40
    u = K.towel_bar(ctx, fwt, c, 'A1 hand towel bar', hv0, hv1, hy, u=0.2)
    K.draped(ctx, fwt, c, 'A1 hand towel', u, u, hv0 + 0.07, hv1 - 0.07, hy + 0.026, 0.92, 0.86,
             K.towel_band_material('towel_A1_hand', K.WHITE_TOWEL), th=0.045, rc=0.026)
    K.exhaust_grille(ctx, c, 'A1 exhaust', 14.7, 25.6)

    # ---- alcove tub, wall to wall --------------------------------------------------------
    xc = (XW + XE) / 2
    hb = (XE - XW) / 2 - 0.002
    fb = K.Frame(xc, ZT, 0.0, -1.0)            # u = ZT - z, v = xc - x
    n_o, n_i = 22, 5
    rings = [
        K.R(FL, 0.0, D, hb, n_o, n_o),
        K.R(TOP - 0.035, 0.0, D, hb, n_o, n_o),
        K.R(TOP - 0.01, 0.003, D - 0.003, hb - 0.003, n_o, n_o),
        K.R(TOP, 0.012, D - 0.012, hb - 0.012, n_o, n_o),
        K.R(TOP, 0.22 - 0.012, D - 0.30 + 0.012, hb - 0.29 + 0.012, n_i, n_i),
        K.R(TOP - 0.012, 0.22, D - 0.30, hb - 0.29, n_i, n_i),
        K.R(TOP - 0.07, 0.235, D - 0.315, hb - 0.305, n_i, n_i),
        K.R(0.95, 0.30, D - 0.39, hb - 0.47, 4.5, 4.5),
        K.R(0.48, 0.38, D - 0.48, hb - 0.70, 4.0, 4.0),
        K.R(0.37, 0.45, D - 0.56, hb - 0.84, 3.6, 3.6),
        K.R(0.335, 0.55, D - 0.66, hb - 0.98, 3.2, 3.2),
    ]
    K.loft(ctx, fb, 'A1 tub', rings, K.CERAMIC, c, seg=96)
    ux = (0.55 + D - 0.66) / 2
    x, z = fb.w(ux, hb - 1.25)
    ctx.cylinder('A1 tub drain', (x, 0.338, z), 0.11, 0.008, nickel, c, verts=32)
    # tub / shower trim on the wood wall
    fwest = K.Frame(XW, 0.0, 1.0, 0.0)         # u = x - XW, v = -z
    tz = ZT - D / 2 - 0.04
    K.valve_trim(ctx, fwest, c, 'A1 valve', -tz, 3.45)
    K.fcyl(ctx, fwest, 'A1 spout plate', 0.012, -tz, 2.08, 0.09, 0.024, 'u', nickel, c)
    K.fcyl(ctx, fwest, 'A1 spout', 0.27, -tz, 2.08, 0.045, 0.5, 'u', nickel, c)
    K.rain_head_wall(ctx, fwest, c, 'A1 rain', -tz, 6.70, arm=1.15, dia=0.70)
    # fixed glass panel on the tub rim with a stay to the back wall (glass, channel and stay rod are
    # fitted pieces, so they keep meeting the rim and the back wall after the warp)
    gz = ZA + 0.15
    K.glass_panel(ctx, c, 'A1 glass panel', (XW + 0.006, gz), (13.32, gz), TOP + 0.015, 6.95)
    K.u_channel(ctx, c, 'A1 channel', (XW + 0.004, gz), (13.32, gz), TOP)
    for yy in (TOP + 0.7, 6.25):
        K.clamp(ctx, c, 'A1 wall clamp', XW + 0.08, yy, gz, 'x')
    ctx.cylinder('A1 shower stay rod', (13.24, 6.88, (gz + ZT) / 2), 0.025, ZT - gz - 0.02, nickel, c, verts=24,
                 axis='Z')
    K.clamp(ctx, c, 'A1 stay clamp', 13.24, 6.88, gz, 'x', size=(0.12, 0.10, 0.08))
    ctx.cylinder('A1 stay rose', (13.24, 6.88, ZT - 0.012), 0.055, 0.024, nickel, c, verts=24, axis='Z')

    # ---- bath towel on the east wall at the tub end ----------------------------------------
    fe = K.Frame(XE, 0.0, -1.0, 0.0)
    u = K.towel_bar(ctx, fe, c, 'A1 towel bar', 25.35, 26.95, 4.15)
    yb = 4.15 + 0.026 - 1.04
    K.draped(ctx, fe, c, 'A1 bath towel', u, u, 25.55, 26.75, 4.15 + 0.026, 1.16, 1.04,
             K.towel_band_material('towel_A1_bath', K.OAT_TOWEL, (yb + 0.16, yb + 0.30)), th=0.05, rc=0.026)

    # ---- finishes: brushed nickel for every kit fitting, limestone-look floor -------------------
    black = ctx.mat(K.BLACK)
    for ob in ctx.coll(c).all_objects:
        if ob.type not in ('MESH', 'CURVE'):
            continue
        mats = ob.data.materials
        for i, m in enumerate(mats):
            if m is black:
                mats[i] = nickel
    _floor(ctx, remap, X0, X1, ZA, zc)
    return None


def _floor(ctx, remap, X0, X1, ZA, zc):
    """Swap the room's shell floor slab to the limestone-look tile. The tile grid is world-space, i.e.
    on the FINAL plan: one 24in tile centred across the room and a joint along the tub apron."""
    xm = (remap(X0, zc)[0] + remap(X1, zc)[0]) / 2
    za = remap((X0 + X1) / 2, ZA)[1]
    mat = M.floor(ctx, xm - 1.0, za)
    n = 0
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and FLOOR_NAME in ob.name:
            mats = ob.data.materials
            if len(mats) == 0:
                mats.append(mat)
            for i in range(len(mats)):
                mats[i] = mat
            n += 1
    if n == 0:
        print('[baths_shared] shell floor not found:', FLOOR_NAME)
    return n

