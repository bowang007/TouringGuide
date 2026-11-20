"""Materials of the shared bath (tour stop A1), all named Z_baths_shared_<name>.

The owner's references (styles/shared_bathroom_style.jpg, styles/shared bathroom wall style.jpg):
  * crema     - warm "Spanish cream" stone-look porcelain, 600 x 1200 mm (24 x 48 in) laid vertical,
                stack bond: soft cloudy beige with sparse low-contrast wandering hairline veins.
  * woodtile  - rustic oak wood-look porcelain planks, 200 mm (8 in) wide, laid vertical with staggered
                ends: warm mid-brown oak grain with grey weathering streaks, dark checks and pin knots.
  * floor     - light warm limestone-look porcelain, 24 x 48 in, honed (the wood wall wants a calm
                light floor, not more wood).
  * travertine- vein-cut travertine / limestone for the vanity block: ivory-beige layered bands with
                small filled pores, honed. 3D world-space field, so the bands run over the block's edges.
  * oak       - light oak veneer (vanity), grain up the fronts.
  * nickel    - brushed nickel fittings.
Everything is world-space mapped (no UVs), with the shared graph helper in materials_pbr (see
bl/MATERIALS.md). Each maker falls back to a flat Principled colour if the node build fails.
"""
import bpy

PFX = 'Z_baths_shared_'
IN = 0.0254
FT = 0.3048


def _flat(name, hexcol, rough, metal=0.0):
    from .. import materials_pbr as P
    m = bpy.data.materials.new(PFX + name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    c = P._hexlin(hexcol)
    b.inputs['Base Color'].default_value = c + (1.0,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = c + (1.0,)
    return m


def _make(name, key, build, fallback):
    """Material PFX+name built by build(g) on a materials_pbr graph seeded from library `key` (for its
    viewport colour); `fallback` = (hex, rough, metal) if anything fails."""
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m is not None:
        return m
    g = None
    try:
        from .. import materials_pbr as P
        g = P._G(key)
        g.m.name = full
        build(g, P)
        g.m.name = full
        return g.m
    except Exception as e:
        print(f'[baths_shared] material {name}: flat fallback ({e!r})')
        if g is not None and g.m is not None:
            try:
                bpy.data.materials.remove(g.m)
            except Exception:
                pass
        return _flat(name, *fallback)


# --------------------------------------------------------------------------------- crema
def _crema(g, P):
    a, b, A, B = g.planar()
    tid, d, la, lb = P._grid(g, a, b, 24 * IN, 48 * IN)
    _, rc = g.white(tid)
    r0, r1, r2 = g.sep(rc)
    _, rc2 = g.white(g.vadd(tid, (0.0, 0.0, 5.7)))
    f0, _, _ = g.sep(rc2)
    flip = g.sub(g.mul(g.gt(f0, 0.5), 2.0), 1.0)                 # vein direction alternates tile to tile
    Q = g.vec(g.mad(g.mul(la, flip), 1.0, g.mul(r0, 9.0)), g.mad(r1, 7.0, lb), g.mul(r2, 5.0))
    base = P._hexlin('#d9c6aa')                     # Spanish cream: peach-beige (ref hue ~35deg), not yellow
    c1, _ = g.noise(Q, 1.5, detail=4.0, rough=0.6)
    c2, _ = g.noise(Q, 6.5, detail=3.0, rough=0.55)
    col = g.vscale(base, g.mul(g.remap(c1, 0.3, 0.7, 0.978, 1.018), g.remap(c2, 0.3, 0.7, 0.99, 1.008)))
    col = g.cmix(col, P._hexlin('#e3d5bf'), g.mul(g.ss(c1, 0.58, 0.8), 0.22))     # paler cream drifts
    col = g.cmix(col, P._hexlin('#cfb999'), g.mul(g.ss(c2, 0.62, 0.8), 0.18))      # warmer patches
    # two families of wandering hairline veins at different angles (they cross, like crema marfil)
    w1 = P._flow(g, Q, (0.75, 0.55, 0.2), 0.28, 0.9, detail=4.0, seed=(1.7, 2.9, 0.4), fine=0.008,
                 fine_scale=13.0, bend=0.7)
    d1, wd1, k1, _ = P._vein(g, w1, Q, 0.22, 0.0008, (3.1, 1.4, 6.2), presence=(0.40, 0.58), along=1.6,
                             rag=0.5, rag_scale=70.0, strength=(0.15, 1.0))
    w2 = P._flow(g, Q, (-0.45, 0.85, 0.3), 0.22, 1.2, detail=4.0, seed=(5.2, 0.8, 3.3), fine=0.008,
                 fine_scale=15.0, bend=0.5)
    d2, wd2, k2, _ = P._vein(g, w2, Q, 0.3, 0.0006, (7.4, 2.2, 1.1), presence=(0.48, 0.64), along=2.0,
                             rag=0.5, rag_scale=80.0, strength=(0.1, 0.8))
    v1 = g.mul(g.sub(1.0, g.ss(d1, 0.0, wd1)), k1)
    h1 = g.mul(g.sub(1.0, g.ss(d1, 0.0, g.mad(wd1, 7.0, 0.004))), k1)
    v2 = g.mul(g.sub(1.0, g.ss(d2, 0.0, wd2)), k2)
    col = g.cmix(col, P._hexlin('#cbb38e'), g.mul(h1, 0.12))
    col = g.cmix(col, P._hexlin('#ab906a'), g.mul(v1, 0.42))
    col = g.cmix(col, P._hexlin('#b39b79'), g.mul(v2, 0.35))
    fr = g.frame()
    sp, _ = g.noise(fr['P'], 450.0, detail=1.0)
    col = g.vscale(col, g.mul(g.remap(sp, 0.3, 0.7, 0.988, 1.01), g.remap(r2, 0.0, 1.0, 0.985, 1.015)))
    grout = g.sub(1.0, g.ss(d, 0.0007, 0.001))
    col = g.cmix(col, P._hexlin('#c8b597'), grout)
    rough = g.lerp(g.add(0.34, g.mul(g.sub(c2, 0.5), 0.08)), 0.8, grout)
    height = g.add(g.ss(d, 0.0006, 0.0022), g.mul(c2, 0.03))
    nrm = g.normal(height=height, dist=0.0008)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


def crema(ctx):
    return _make('crema', 'tile_wall_porcelain', _crema, ('#d9c6aa', 0.35))


# ------------------------------------------------------------------------------ wood tile
def _woodtile(g, P):
    a, b, A, B = g.planar()
    # per-object plank turn (ob['tg_wood_rot'] = 1): on vertical faces the planks run horizontally, so a
    # shelf edge or a lip shows grain along its length (not 8in plank joints across it); tops unchanged
    rot = g.mul(g.clamp01(g.attr('tg_wood_rot')), g.sub(1.0, g.frame()['horiz']))
    a, b, A, B = (g.lerp(a, b, rot), g.lerp(b, g.mul(a, -1.0), rot),
                  g.vmix(A, B, rot), g.vmix(B, g.vscale(A, -1.0), rot))
    # per-object plank shift (ob['tg_wood_shift'], metres): a niche back is cut from other planks than
    # the wall face in front of it, so the recess does not read as the same boards seen through a hole
    sh = g.attr('tg_wood_shift')
    a, b = g.add(a, sh), g.mad(sh, 4.3, b)
    W = 8.0 * IN
    bd = P._boards(g, b, a, W, 2.3, 2.7, split=(0.42, 0.58), seed=4.0)       # planks ~0.95-1.55 m, vertical
    r0, r1, r2 = bd['rnd']
    q0, q1, q2 = bd['rnd2']
    al = g.mad(r0, 13.0, b)                      # along the plank (up the wall), random per plank
    ac = g.mad(r1, 9.0, a)
    target = P._hexlin('#a47e58')
    # rustic, mottled colour from a worn table top (no seams), stretched along the grain ...
    s = g.sample('wood_table_worn', al, ac, B, A, 0.55, grain='u', stretch=2.2)
    # ... carrying the straight open grain of an oak veneer (luminance only) ...
    o = g.sample('oak_veneer_05', g.mad(q0, 5.0, al), g.mad(q1, 3.0, ac), B, A, 1.0, grain='u', stretch=1.8)
    # ... and, on some planks, the cathedral figure of flat-sawn oak
    f = g.sample('oak_veneer_01', g.mad(q2, 7.0, al), g.mad(r2, 5.0, ac), B, A, 1.83, grain='v', stretch=1.6,
                 maps=('diffuse',))
    if s:
        col = g.grade(s['color'], s['mean'], target, 1.0, sat=1.0)
        rough, pert = g.rough_from(s, 0.58, 0.4), s['pert']
    else:
        n, _ = g.noise(g.vec(g.mul(al, 3.0), g.mul(ac, 70.0), 0.0), 1.0, detail=6.0, rough=0.6)
        col = g.vscale(target, g.remap(n, 0.2, 0.8, 0.8, 1.15))
        rough, pert = 0.58, None

    def lum_ratio(smp, k):
        lum = g.vm('DOT_PRODUCT', smp['color'], (0.3, 0.55, 0.15))
        m = smp['mean']
        return g.f('POWER', g.mx(g.div(lum, max(0.3 * m[0] + 0.55 * m[1] + 0.15 * m[2], 1e-4)), 0.05), k)
    if o:
        col = g.vscale(col, lum_ratio(o, 1.1))
        pert = o['pert'] if pert is None else g.vadd(g.vscale(pert, 0.5), g.vscale(o['pert'], 0.6))
    if f:
        col = g.cmix(col, g.vscale(col, lum_ratio(f, 1.3)), g.gt(q2, 0.62))
    # pale weathered pores of brushed grey oak as light streaks (luminance only)
    w = g.sample('grey_oak_veneer_02', g.mad(r2, 11.0, b), g.mad(q2, 7.0, a), B, A, 1.0, grain='u', stretch=1.5,
                 maps=('diffuse',))
    if w:
        streak = g.ss(lum_ratio(w, 1.0), 1.06, 1.35)
        col = g.cmix(col, g.vm('MULTIPLY', g.hsv(col, s=0.6, v=1.4), (1.0, 0.99, 0.97)),
                     g.mul(streak, g.remap(q1, 0.0, 1.0, 0.12, 0.42)))
    # fibrous rough-sawn texture along the grain
    fb, _ = g.noise(g.vec(g.mul(ac, 450.0), g.mul(al, 9.0), g.mul(r2, 5.0)), 1.0, detail=3.0, rough=0.6)
    col = g.vscale(col, g.remap(fb, 0.3, 0.7, 0.93, 1.05))
    # per-plank tone / warmth: printed porcelain planks come in several faces
    col = g.vscale(col, g.remap(q0, 0.0, 1.0, 0.8, 1.14))
    col = g.cmix(col, g.vm('MULTIPLY', col, (1.07, 0.98, 0.86)), g.mul(q1, 0.5))
    # weathered grey-brown patches running along the grain
    st, _ = g.noise(g.vec(g.mul(ac, 22.0), g.mul(al, 0.8), g.mul(r2, 7.0)), 1.0, detail=4.0, rough=0.6)
    grey = g.vm('MULTIPLY', g.hsv(col, s=0.5, v=1.08), (0.98, 0.98, 1.0))
    col = g.cmix(col, grey, g.mul(g.ss(st, 0.58, 0.76), g.remap(q2, 0.0, 1.0, 0.1, 0.45)))
    # darker streaks (old stain / sap) and fine dark checks (cracks) along the grain
    ds, _ = g.noise(g.vec(g.mul(ac, 36.0), g.mul(al, 1.4), g.add(r2, 3.0)), 1.0, detail=3.0, rough=0.55)
    col = g.vscale(col, g.lerp(1.0, 0.8, g.mul(g.ss(ds, 0.6, 0.78), 0.75)))
    dk, rk = g.edge_w(g.mad(r0, 3.0, ac), 0.03, seed=2.0)
    pk, _ = g.noise(g.vec(g.mul(ac, 4.0), g.mul(al, 2.2), g.add(rk, 1.0)), 1.0, detail=2.0)
    check = g.mul(g.sub(1.0, g.ss(dk, 0.0, 0.0008)), g.mul(g.ss(pk, 0.48, 0.62), g.gt(rk, 0.3)))
    col = g.cmix(col, P._hexlin('#2b1e14'), g.mul(check, 0.8))
    # knots, stretched along the grain
    vk = g.voronoi(g.vec(g.mul(ac, 1.0), g.mul(al, 0.33), g.mul(r2, 3.0)), 5.0)
    kd = vk.outputs['Distance']
    kc, _, _ = g.sep(vk.outputs['Color'])
    keep = g.sub(1.0, g.ss(kc, 0.3, 0.34))
    knot = g.mul(g.sub(1.0, g.ss(kd, 0.04, 0.085)), keep)
    ring = g.mul(g.sub(1.0, g.ss(kd, 0.07, 0.2)), keep)
    col = g.vscale(col, g.lerp(1.0, 0.75, ring))
    col = g.cmix(col, P._hexlin('#36241a'), g.mul(knot, 0.9))
    # weathered, greyed rustic oak as in the reference (against its white WC the reference planks are about
    # half as saturated as the raw grade): this also keeps the wood's bounce from tinting the room orange
    col = g.hsv(col, s=0.8, v=0.92)
    # 1/16in joints, slightly eased plank edges
    dmin = g.mn(bd['d_side'], bd['d_end'])
    grout = g.sub(1.0, g.ss(dmin, 0.0007, 0.001))
    col = g.cmix(col, P._hexlin('#3a2e25'), grout)
    rough = g.lerp(g.add(rough, g.mul(g.sub(q2, 0.5), 0.06)), 0.85, grout)
    height = g.add(g.ss(dmin, 0.0006, 0.0025), g.mul(g.add(g.add(st, g.mul(fb, 0.5)), g.mul(check, -2.0)), 0.04))
    nrm = g.normal(pert, 0.5, height=height, dist=0.0008)
    return g.finish(g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.06, 'Coat Roughness': 0.4}))


def woodtile(ctx):
    return _make('woodtile', 'walnut_slab', _woodtile, ('#8c6846', 0.56))


# ---------------------------------------------------------------------------------- floor
def floor(ctx, a0_ft, b0_ft):
    """Light warm limestone-look 24 x 48 in floor tile, long side north-south. The grid is placed in
    FINAL world space (a = SCENE x, b = -SCENE z, metres): a0_ft = SCENE x of a joint, b0_ft = SCENE z
    of a joint (the build passes a tile centred on the room and a joint along the tub apron)."""
    def build(g, P):
        a, b, A, B = g.planar()
        tid, d, la, lb = P._grid(g, a, b, 24 * IN, 48 * IN, a0=a0_ft * FT, b0=-b0_ft * FT)
        _, rc = g.white(tid)
        r0, r1, r2 = g.sep(rc)
        target = P._hexlin('#c9b9a2')                # light warm limestone (reads grey if any cooler)
        s = g.sample('plastered_wall_04', g.mad(r0, 9.0, a), g.mad(r1, 9.0, b), A, B, 2.6,
                     maps=('diffuse', 'nor_gl'))
        col = g.grade(s['color'], s['mean'], target, 1.15, sat=0.45) if s else target
        fr = g.frame()
        Q = g.vadd(fr['P'], g.vscale(rc, 5.0))
        c1, _ = g.noise(Q, 2.2, detail=3.0, rough=0.55)
        col = g.vscale(col, g.remap(c1, 0.3, 0.7, 0.97, 1.03))
        # tiny fossil / calcite specks of a limestone
        sp, _ = g.noise(Q, 220.0, detail=2.0, rough=0.5)
        col = g.cmix(col, P._hexlin('#b3a690'), g.mul(g.ss(sp, 0.66, 0.74), 0.5))
        sp2, _ = g.noise(fr['P'], 600.0, detail=1.0)
        col = g.vscale(col, g.mul(g.remap(sp2, 0.25, 0.75, 0.98, 1.015), g.remap(r2, 0.0, 1.0, 0.975, 1.025)))
        grout = g.sub(1.0, g.ss(d, 0.0007, 0.001))
        col = g.cmix(col, P._hexlin('#b0a693'), grout)
        rough = g.lerp(g.add(0.5, g.mul(g.sub(c1, 0.5), 0.08)), 0.85, grout)
        nrm = g.normal(s['pert'] if s else None, 0.25, height=g.ss(d, 0.0006, 0.002), dist=0.0008)
        return g.finish(g.bsdf(col, rough, 0.0, nrm))
    return _make('floor', 'tile_floor_bath', build, ('#c9b9a2', 0.5))


# ----------------------------------------------------------------------------- travertine
def _travertine(g, P):
    fr = g.frame()
    Pw = fr['P']
    D = (0.0, 0.28, 0.96)                      # layers ~horizontal, dipping a little north-south
    w = g.vm('DOT_PRODUCT', Pw, D)
    wn, _ = g.noise(Pw, 1.4, detail=3.0, rough=0.55)
    w = g.mad(g.sub(wn, 0.5), 0.05, w)
    band = g.noise_w(g.mul(w, 1.0), 14.0, detail=5.0, rough=0.62)
    band2 = g.noise_w(g.add(g.mul(w, 1.0), 3.3), 60.0, detail=3.0, rough=0.5)
    base = P._hexlin('#d9ccb6')
    col = g.vscale(base, g.mul(g.remap(band, 0.3, 0.7, 0.92, 1.05), g.remap(band2, 0.3, 0.7, 0.975, 1.02)))
    col = g.cmix(col, P._hexlin('#cbb894'), g.mul(g.ss(band, 0.58, 0.72), 0.45))     # honey layers
    col = g.cmix(col, P._hexlin('#e6dccb'), g.mul(g.sub(1.0, g.ss(band, 0.3, 0.42)), 0.4))
    # filled pores: small voids stretched along the layers (world X = along the vanity)
    px, py, pz = fr['px'], fr['py'], fr['pz']
    vq = g.vec(g.mul(px, 18.0), g.mul(py, 70.0), g.mul(g.add(pz, g.mul(wn, 0.02)), 70.0))
    vp = g.voronoi(vq, 1.0)
    pd = vp.outputs['Distance']
    pc, _, _ = g.sep(vp.outputs['Color'])
    keep = g.sub(1.0, g.ss(pc, 0.3, 0.36))
    pore = g.mul(g.sub(1.0, g.ss(pd, 0.10, 0.2)), keep)
    col = g.cmix(col, P._hexlin('#a8957a'), g.mul(pore, 0.6))
    sp, _ = g.noise(Pw, 500.0, detail=1.0)
    col = g.vscale(col, g.remap(sp, 0.3, 0.7, 0.985, 1.012))
    rough = g.add(g.add(0.46, g.mul(pore, 0.25)), g.mul(g.sub(band2, 0.5), 0.06))
    height = g.add(g.mul(pore, -1.0), g.mul(band2, 0.15))
    nrm = g.normal(height=height, dist=0.0006)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


def travertine(ctx):
    return _make('travertine', 'quartz_white', _travertine, ('#d9ccb6', 0.46))


# ------------------------------------------------------------------------------------ oak
def _oak(g, P):
    a, b, A, B = g.planar(grain_knob=True)
    fr = g.frame()
    al = g.lerp(b, a, fr['horiz'])                # vertical faces: grain up the face; tops: along a
    ac = g.lerp(a, b, fr['horiz'])
    Al = g.vmix(B, A, fr['horiz'])
    Ac = g.vmix(A, B, fr['horiz'])
    s = g.sample('oak_veneer_03', al, ac, Al, Ac, 1.0, grain='u', stretch=1.3)
    target = P._hexlin('#c4a277')
    if s:
        col = g.grade(s['color'], s['mean'], target, 1.5)
        rough, pert = g.rough_from(s, 0.48, 0.4), s['pert']
    else:
        col, rough, pert = target, 0.48, None
    col = g.vm('MULTIPLY', col, (1.02, 1.0, 0.96))
    nrm = g.normal(pert, 0.5)
    return g.finish(g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.1, 'Coat Roughness': 0.3}))


def oak(ctx):
    return _make('oak', 'white_oak_veneer', _oak, ('#c4a277', 0.48))


# --------------------------------------------------------------------------------- nickel
def _nickel(g, P):
    fr = g.frame()
    a, b, A, B = g.planar()
    lines, _ = g.noise(g.vec(g.mul(a, 3.0), g.mul(b, 1800.0), 0.0), 1.0, detail=3.0, rough=0.6)
    sm, _ = g.noise(fr['P'], 4.0, detail=2.0)
    base = g.vscale(P._hexlin('#c9bfae'), g.remap(sm, 0.3, 0.7, 0.97, 1.02))
    rough = g.add(0.27, g.mul(g.sub(lines, 0.5), 0.1))
    nrm = g.normal(height=lines, dist=0.00004)
    return g.finish(g.bsdf(base, rough, 1.0, nrm))


def nickel(ctx):
    return _make('nickel', 'stainless', _nickel, ('#c9bfae', 0.27, 1.0))


def matte(name, hexcol, rough=0.6):
    m = bpy.data.materials.get(PFX + name)
    return m if m is not None else _flat(name, hexcol, rough)

