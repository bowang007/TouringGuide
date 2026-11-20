"""Zone materials of the primary bath (stop A0), named Z_baths_primary_<name>.

Built with the library's graph helper (materials_pbr._G: world-space planar / triplanar mapping, no
UVs) so they follow the same conventions as the shared library. Each builder falls back to a flat
Principled material if anything fails (e.g. a texture download), so the zone always builds.

  sage_subway   glossy handmade-look sage-green 3x12in subway tile, running bond, light grout (shower)
  vgroove       sage-grey painted V-groove panelling, 4in boards (wainscot)
  sage_paint    the same paint without grooves (wainscot cap)
  plaster       warm cream lime plaster above the wainscot
  stone         stacked natural-stone veneer (Poly Haven rustic_stone_wall_02) with TRUE displacement
                (world-space, so the relief lines up with the colour after the warp) - feature wall
  oak           solid oak slab (Poly Haven oak_wood_planks, glued boards, honey oil finish)
  timber        reclaimed timber (Poly Haven weathered_brown_planks) for the shelf over the WC
  brass         aged / brushed brass (fixtures, mirror frames, sconces, towel warmer)
  opal          lit white opal glass (sconce shades)
  encaustic     8in blue-and-cream encaustic cement tile, quatrefoil medallion pattern (floor)
  shower_mosaic 2x2in cream mosaic with light grout (shower floor)
  jute          jute / sisal bath mat
  wicker        coiled seagrass (laundry basket)
"""
import math

import bpy

PFX = 'Z_baths_primary_'
IN = 0.0254


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexlin(h):
    h = h.lstrip('#')
    return tuple(_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


def _flat(name, rgb, rough=0.5, metal=0.0, **extra):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = tuple(rgb) + (1,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    for k, v in extra.items():
        try:
            b.inputs[k.replace('_', ' ')].default_value = v
        except (KeyError, TypeError):
            pass
    m.diffuse_color = tuple(rgb) + (1,)
    return m


def _make(name, build, fallback):
    """Material PFX+name from build(g, P) on a fresh graph; flat `fallback` (rgb, rough, metal) on error."""
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m is not None:
        return m
    g = None
    try:
        from .. import materials_pbr as P
        g = P._G('paint_wall')
        g.m.name = full
        m = build(g, P)
        m.diffuse_color = tuple(fallback[0]) + (1,)
        return m
    except Exception as e:  # pragma: no cover - only on a broken texture / API change
        print(f'[baths_primary] material {full} fallback: {e!r}')
        if g is not None and g.m is not None:
            bpy.data.materials.remove(g.m)
        return _flat(full, *fallback)


def _out(g, shader, disp=None):
    out = g.new('ShaderNodeOutputMaterial')
    g.nt.links.new(shader.outputs[0], out.inputs['Surface'])
    if disp is not None:
        g.nt.links.new(disp, out.inputs['Displacement'])
    return g.m


def _inside(g, sd, e):
    """1 inside (signed distance sd < 0), 0 outside, antialiased over +-e."""
    return g.sub(1.0, g.ss(sd, -e, e))


# ------------------------------------------------------------------------------------- tiles
def sage_subway():
    """Glossy sage-green 3x12in subway, 1/2 running bond from the floor, 1/16in light grout. Every tile
    has its own tone and a slightly wavy handmade glaze, so reflections ripple across the wall."""
    def build(g, P):
        a, b, A, B = g.planar()
        tw, th = 12 * IN, 3 * IN
        tid, d, la, lb = P._grid(g, a, b, tw, th, offset=0.5)
        _, rc = g.white(tid)
        r0, r1, r2 = g.sep(rc)
        base = hexlin('#7f8a72')
        col = g.vscale(base, g.remap(r0, 0.0, 1.0, 0.91, 1.07))
        col = g.cmix(col, g.vm('MULTIPLY', col, (0.95, 1.03, 1.02)), r1)          # greener / greyer tiles
        n, _ = g.noise(g.vec(a, b, g.mul(r2, 9.0)), 7.0, detail=3.0)
        col = g.vscale(col, g.remap(n, 0.3, 0.7, 0.955, 1.04))                    # glaze pooling
        # glaze breaks lighter on the pillowed edges
        rim = g.sub(1.0, g.ss(d, 0.0012, 0.004))
        col = g.cmix(col, g.vm('MULTIPLY', col, (1.12, 1.12, 1.10)), g.mul(rim, 0.6))
        grout = g.sub(1.0, g.ss(d, 0.0007, 0.00095))
        col = g.cmix(col, hexlin('#d9d5ca'), grout)
        wav, _ = g.noise(g.vec(g.mul(a, 1.0), b, g.mul(r1, 13.0)), 5.0, detail=2.0)
        height = g.add(g.ss(d, 0.0005, 0.0045), g.mul(wav, 0.22))
        nrm = g.normal(height=height, dist=0.0016)
        rough = g.lerp(g.add(0.05, g.mul(n, 0.05)), 0.85, grout)
        return _out(g, g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.35, 'Coat Roughness': 0.04}))
    return _make('sage_subway', build, (hexlin('#7f8a72'), 0.08))


SAGE = '#a5aa97'          # wainscot paint (soft sage-grey, like the reference)


def vgroove():
    """Painted tongue-and-groove V-groove panelling: 4in boards running up the wall, 1/8in V joints."""
    def build(g, P):
        a, b, A, B = g.planar()
        pitch = 4.0 * IN
        s = g.div(a, pitch)
        bid = g.floor(s)
        t = g.sub(s, bid)
        dist = g.mul(g.mn(t, g.sub(1.0, t)), pitch)            # m to the nearest joint
        _, rc = g.white(g.vec(bid, 3.1, 7.7))
        r0, _, _ = g.sep(rc)
        fr = g.frame()
        n1, _ = g.noise(fr['P'], 330.0, detail=3.0, rough=0.55)
        n2, _ = g.noise(fr['P'], 2.5, detail=2.0)
        base = g.vscale(hexlin(SAGE), g.mul(g.remap(r0, 0.0, 1.0, 0.985, 1.015), g.remap(n2, 0.3, 0.7, 0.99, 1.01)))
        groove = g.ss(dist, 0.0004, 0.0032)
        col = g.vscale(base, g.lerp(0.55, 1.0, groove))
        height = g.add(g.mul(groove, 1.0), g.mul(n1, 0.02))
        nrm = g.normal(height=height, dist=0.0022)
        rough = g.add(0.42, g.mul(g.sub(n2, 0.5), 0.06))
        return _out(g, g.bsdf(col, rough, 0.0, nrm))
    return _make('vgroove', build, (hexlin(SAGE), 0.45))


def sage_paint():
    def build(g, P):
        fr = g.frame()
        n1, _ = g.noise(fr['P'], 330.0, detail=3.0, rough=0.55)
        n2, _ = g.noise(fr['P'], 2.5, detail=2.0)
        col = g.vscale(hexlin(SAGE), g.remap(n2, 0.3, 0.7, 0.99, 1.01))
        nrm = g.normal(height=n1, dist=0.0001)
        return _out(g, g.bsdf(col, 0.42, 0.0, nrm))
    return _make('sage_paint', build, (hexlin(SAGE), 0.45))


def plaster():
    """Warm cream lime plaster: soft trowel mottling (Poly Haven plastered_wall_04, triplanar)."""
    target = hexlin('#e7dcc8')

    def build(g, P):
        s = g.tri('plastered_wall_04', 2.4)
        fr = g.frame()
        n, _ = g.noise(fr['P'], 1.6, detail=3.0)
        if s:
            col = g.grade(s['color'], s['mean'], target, 0.65, sat=0.35)
            rough = g.rough_from(s, 0.82, 0.25)
            pert = s['pert']
        else:
            col, rough, pert = target, 0.82, None
        col = g.vscale(col, g.remap(n, 0.3, 0.7, 0.975, 1.02))
        nrm = g.normal(pert, 0.35)
        return _out(g, g.bsdf(col, rough, 0.0, nrm))
    return _make('plaster', build, (target, 0.85))


# ------------------------------------------------------------------------------------- stone
STONE_SIZE = 2.2          # m: real width of the rustic_stone_wall_02 scan (stones 3-9cm tall, 11-43cm long)
STONE_MID = 0.52          # displacement map value of the mortar bed
STONE_DISP = 0.07         # m per unit of the map above the mortar bed (stone faces ~2cm proud)


def stone():
    """Stacked natural stone, warm brown-grey: colour, roughness and normal from the scan, plus TRUE
    displacement (material displacement 'BOTH') from its height map in world space, clamped at the
    mortar bed so the relief only comes forward of the mesh plane."""
    target = hexlin('#8e7b66')

    def build(g, P):
        a, b, A, B = g.planar()
        s = g.sample('rustic_stone_wall_02', a, b, A, B, STONE_SIZE,
                     maps=('diffuse', 'rough', 'nor_gl', 'displacement'))
        if not s:
            raise RuntimeError('rustic_stone_wall_02 unavailable')
        col = g.grade(s['color'], s['mean'], target, 1.08, sat=0.95)
        h, _, _ = g.sep(s['displacement'])
        # mortar slightly lighter and duller than the stones
        mort = g.sub(1.0, g.ss(h, STONE_MID + 0.02, STONE_MID + 0.12))
        col = g.cmix(col, g.vm('MULTIPLY', col, (1.12, 1.10, 1.06)), g.mul(mort, 0.5))
        rough = g.rough_from(s, 0.78, 0.6, lo=0.45)
        nrm = g.normal(s['pert'], 0.9)
        hh = g.mx(h, STONE_MID)
        dn = g.new('ShaderNodeDisplacement', space='WORLD')
        g.put(dn.inputs['Height'], hh)
        g.put(dn.inputs['Midlevel'], STONE_MID)
        g.put(dn.inputs['Scale'], STONE_DISP)
        m = _out(g, g.bsdf(col, rough, 0.0, nrm), dn.outputs[0])
        for owner in (m, getattr(m, 'cycles', None)):
            try:
                owner.displacement_method = 'BOTH'
                break
            except Exception:
                continue
        return m
    return _make('stone', build, (target, 0.8))


def stone_relief_ft():
    """Typical stone-face offset in front of the stone mesh plane (ft): map value ~0.82."""
    return (0.82 - STONE_MID) * STONE_DISP / 0.3048


# --------------------------------------------------------------------------------------- wood
def oak():
    """Solid oak slab of glued boards with knots, honey oil finish (Poly Haven oak_wood_planks, 1.2m).
    Grain along world X on tops (the vanity runs east-west) and along each vertical face."""
    target = hexlin('#97775a')          # natural honey oak (was #9a744f: read orange under the bath's warm WB)

    def build(g, P):
        a, b, A, B = g.planar()
        s = g.sample('oak_wood_planks', g.add(a, 0.37), g.add(b, 0.11), A, B, 1.2)
        if not s:
            raise RuntimeError('oak_wood_planks unavailable')
        col = g.grade(s['color'], s['mean'], target, 1.25, sat=0.8)
        rough = g.rough_from(s, 0.42, 0.5)
        nrm = g.normal(s['pert'], 0.6)
        return _out(g, g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.18, 'Coat Roughness': 0.3}))
    return _make('oak', build, (target, 0.45))


def timber():
    """Reclaimed timber beam (weathered_brown_planks), mid brown, matte wax."""
    target = hexlin('#6e543c')

    def build(g, P):
        a, b, A, B = g.planar()
        s = g.sample('weathered_brown_planks', g.add(a, 0.21), g.add(b, 0.043), A, B, 1.4, stretch=1.6)
        if not s:
            raise RuntimeError('weathered_brown_planks unavailable')
        col = g.grade(s['color'], s['mean'], target, 1.1, sat=0.85)
        rough = g.rough_from(s, 0.62, 0.4)
        nrm = g.normal(s['pert'], 0.8)
        return _out(g, g.bsdf(col, rough, 0.0, nrm))
    return _make('timber', build, (target, 0.6))


# -------------------------------------------------------------------------------------- metal
BRASS = '#b8955a'


def brass():
    """Aged satin brass: warm, slightly uneven tone, fine brushed roughness variation."""
    def build(g, P):
        fr = g.frame()
        n1, _ = g.noise(fr['P'], 18.0, detail=3.0)
        n2, _ = g.noise(g.vec(g.mul(fr['px'], 900.0), g.mul(fr['py'], 900.0), g.mul(fr['pz'], 40.0)), 1.0, detail=2.0)
        col = g.vscale(hexlin(BRASS), g.remap(n1, 0.3, 0.7, 0.9, 1.05))
        rough = g.add(0.27, g.add(g.mul(g.sub(n1, 0.5), 0.12), g.mul(g.sub(n2, 0.5), 0.08)))
        return _out(g, g.bsdf(col, rough, 1.0, None))
    return _make('brass', build, (hexlin(BRASS), 0.3, 1.0))


def opal(strength=5.0):
    """Lit white opal glass shade (warm 3000K glow, like the sconce lamps; the balance scales emission
    at render time)."""
    name = PFX + 'opal'
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (0.92, 0.9, 0.86, 1)
    b.inputs['Roughness'].default_value = 0.25
    try:
        b.inputs['Coat Weight'].default_value = 0.6
        bb = nt.nodes.new('ShaderNodeBlackbody')
        bb.inputs['Temperature'].default_value = 3000.0
        nt.links.new(bb.outputs[0], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = strength
    except (KeyError, TypeError):
        pass
    m.diffuse_color = (0.92, 0.9, 0.86, 1)
    return m


# ------------------------------------------------------------------------------------- floors
INK = '#33456a'
CREAM = '#ebe5d6'


def encaustic():
    """8in encaustic cement tile, indigo on cream (the reference floor): an eight-petal centre flower in a
    scalloped medallion ring, pointed leaves around it, ring-and-dot motifs on the edge midpoints and
    corner rosettes (an ink disc with a cream quatrefoil inside a ring) that read as whole circles
    where four tiles meet. Matte sealed cement with a faint mottle, slightly worn ink, 1/16in grout."""
    def build(g, P):
        a, b, A, B = g.planar()
        tw = 8.0 * IN
        tid, d, la, lb = P._grid(g, a, b, tw, tw)
        _, rc = g.white(tid)
        r0, r1, r2 = g.sep(rc)
        px = g.sub(g.div(la, tw), 0.5)
        py = g.sub(g.div(lb, tw), 0.5)
        qx, qy = g.absf(px), g.absf(py)
        u = g.mx(qx, qy)
        w = g.mn(qx, qy)
        r = g.f('SQRT', g.add(g.mul(qx, qx), g.mul(qy, qy)))
        phi = g.f('ARCTAN2', w, g.mx(u, 1e-5))                   # 0 (axis) .. pi/4 (diagonal)
        e = 0.005

        def sq(x):
            return g.mul(x, x)
        # centre: eight petals (long on the axes, shorter on the diagonals), outlined, ink core, cream eye
        c4 = g.absf(g.f('COSINE', g.mul(phi, 4.0)))
        lenf = g.sub(1.0, g.mul(phi, 0.28 / (math.pi / 4)))
        rp = g.mul(g.add(0.05, g.mul(0.17, g.f('POWER', g.mx(c4, 1e-4), 0.55))), lenf)
        ink = g.sub(_inside(g, g.sub(r, rp), e), _inside(g, g.sub(r, g.sub(g.mul(rp, 0.62), 0.006)), e))
        ink = g.mx(ink, _inside(g, g.sub(r, 0.045), e))
        ink = g.mul(ink, g.sub(1.0, _inside(g, g.sub(r, 0.022), e)))
        # scalloped medallion ring
        scal = g.add(0.285, g.mul(0.012, g.f('COSINE', g.mul(phi, 8.0))))
        ink = g.mx(ink, _inside(g, g.sub(g.absf(g.sub(r, scal)), 0.011), e))
        # corner rosette: ink disc, cream quatrefoil, ink eye, outer ring
        cx, cy = g.sub(0.5, qx), g.sub(0.5, qy)
        rcn = g.f('SQRT', g.add(sq(cx), sq(cy)))
        psi = g.f('ARCTAN2', cy, g.mx(cx, 1e-5))
        cf = g.add(0.04, g.mul(0.13, g.f('POWER', g.mx(g.absf(g.f('COSINE', g.mul(psi, 2.0))), 1e-4), 0.7)))
        ink = g.mx(ink, g.mul(_inside(g, g.sub(rcn, 0.205), e), g.sub(1.0, _inside(g, g.sub(rcn, cf), e))))
        ink = g.mx(ink, _inside(g, g.sub(rcn, 0.035), e))
        ink = g.mx(ink, _inside(g, g.sub(g.absf(g.sub(rcn, 0.235)), 0.008), e))
        # edge midpoints: half ring + half dot (ring-and-dot across the joint)
        de = g.f('SQRT', g.add(sq(g.sub(0.5, u)), sq(w)))
        ink = g.mx(ink, _inside(g, g.sub(g.absf(g.sub(de, 0.075)), 0.016), e))
        ink = g.mx(ink, _inside(g, g.sub(de, 0.025), e))
        # pointed leaves between the edge motifs and the corner rosettes
        lf = g.add(g.div(g.absf(g.sub(u, 0.36)), 0.032), sq(g.div(g.sub(w, 0.17), 0.085)))
        ink = g.mx(ink, _inside(g, g.sub(lf, 1.0), 0.1))
        ink = g.clamp01(ink)
        # cement: faint mottle, per-tile tone, slightly faded / worn ink
        fr = g.frame()
        m1, _ = g.noise(fr['P'], 14.0, detail=4.0)
        m2, _ = g.noise(fr['P'], 160.0, detail=2.0)
        cream = g.vscale(hexlin(CREAM), g.mul(g.remap(m1, 0.3, 0.7, 0.965, 1.025), g.remap(r0, 0.0, 1.0, 0.975, 1.02)))
        inkc = g.vscale(hexlin(INK), g.mul(g.remap(r1, 0.0, 1.0, 0.9, 1.1), g.remap(m1, 0.3, 0.7, 0.9, 1.12)))
        wear = g.mul(g.ss(m2, 0.64, 0.8), 0.3)
        col = g.cmix(cream, inkc, g.mul(ink, g.sub(1.0, wear)))
        grout = g.sub(1.0, g.ss(d, 0.0007, 0.00095))
        col = g.cmix(col, hexlin('#c9c3b5'), grout)
        height = g.add(g.ss(d, 0.0005, 0.0018), g.mul(m2, 0.03))
        nrm = g.normal(height=height, dist=0.0008)
        rough = g.lerp(g.add(0.5, g.mul(g.sub(m1, 0.5), 0.12)), 0.9, grout)
        return _out(g, g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.08, 'Coat Roughness': 0.35}))
    return _make('encaustic', build, (hexlin(CREAM), 0.55))


def shower_mosaic():
    """2x2in cream porcelain mosaic, light grout, per-tile tone (shower floor)."""
    def build(g, P):
        a, b, A, B = g.planar()
        tw = 2.0 * IN
        tid, d, _, _ = P._grid(g, a, b, tw, tw)
        _, rc = g.white(tid)
        r0, r1, _ = g.sep(rc)
        col = g.vscale(hexlin('#e3ddcf'), g.remap(r0, 0.0, 1.0, 0.93, 1.05))
        col = g.cmix(col, g.vm('MULTIPLY', col, (0.97, 1.0, 0.97)), r1)
        grout = g.sub(1.0, g.ss(d, 0.0013, 0.0018))
        col = g.cmix(col, hexlin('#c3beb2'), grout)
        nrm = g.normal(height=g.ss(d, 0.0013, 0.0045), dist=0.0012)
        return _out(g, g.bsdf(col, g.lerp(0.4, 0.85, grout), 0.0, nrm))
    return _make('shower_mosaic', build, (hexlin('#e3ddcf'), 0.5))


def jute():
    target = hexlin('#9f8358')

    def build(g, P):
        s = g.tri('hessian_230', 0.16, '1k')
        fr = g.frame()
        n, _ = g.noise(fr['P'], 3.0, detail=3.0)
        if s:
            col = g.grade(s['color'], s['mean'], target, 1.2, sat=0.75)
            pert = s['pert']
        else:
            col, pert = target, None
        # chunky braided rows across the mat
        wv = g.f('SINE', g.mul(fr['px'], 2 * math.pi / 0.022))
        col = g.vscale(col, g.mul(g.remap(n, 0.3, 0.7, 0.93, 1.05), g.remap(wv, -1.0, 1.0, 0.86, 1.04)))
        nrm = g.normal(pert, 1.2, height=g.mad(wv, 0.5, 0.5), dist=0.003, bump=0.8)
        return _out(g, g.bsdf(col, 0.95, 0.0, nrm, **{'Sheen Weight': 0.4, 'Sheen Roughness': 0.5}))
    return _make('jute', build, (target, 0.95))


def wicker():
    """Coiled seagrass rope (horizontal coils 1.2cm apart with a twist), warm straw."""
    target = hexlin('#a68457')

    def build(g, P):
        fr = g.frame()
        a, b, A, B = g.planar()
        coil = g.div(fr['pz'], 0.012)
        t = g.fract(coil)
        prof = g.f('SINE', g.mul(t, math.pi))
        tw = g.f('SINE', g.mul(g.add(g.div(a, 0.006), g.mul(t, 3.0)), math.pi))
        n, _ = g.noise(fr['P'], 40.0, detail=3.0)
        col = g.vscale(target, g.mul(g.remap(prof, 0.0, 1.0, 0.62, 1.05), g.remap(tw, -1.0, 1.0, 0.9, 1.06)))
        col = g.vscale(col, g.remap(n, 0.3, 0.7, 0.9, 1.08))
        h = g.add(g.mul(prof, 1.0), g.mul(tw, 0.15))
        nrm = g.normal(height=h, dist=0.003)
        return _out(g, g.bsdf(col, 0.8, 0.0, nrm, **{'Sheen Weight': 0.3, 'Sheen Roughness': 0.5}))
    return _make('wicker', build, (target, 0.8))
