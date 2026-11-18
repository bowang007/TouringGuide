"""Shaders for the living-room feature wall and linear gas fireplace (runs inside Blender).

- stone_material: polished, book-matched grey-green onyx / quartzite pair (the 1077 W McKinley
  fireplace slab): a warm grey-green ground with domain-warped translucent bands and milky drifts,
  crossed by four families of soft-edged rust-brown veins with gold rims that swell, pinch out and
  follow a gentle flow (iso-lines of a warped field, so they never branch like a voronoi crackle).
  Mirrored about the centre seam in object space and wrapped mitre-style onto the side returns.
- flame_material: one row of small gas flames for a sheet along the burner: staggered layers of
  narrow tongues with their own heights and lean, dim blue roots, golden bodies, orange-red wispy
  tips. Purely additive (emission + transparent) with the mask in the emission colour, so the
  render-time light balance scales it like every other emitter.
- ember_bed_material: dark bed under the media with a thin, broken glow along the burner line.
- media_material: glossy black / smoked-bronze tumbled fire glass that picks up the flames as glints.
"""
import math

import bpy

from . import living_geo as G


class _NB:
    """Tiny node-building helper: every method returns output sockets; inputs accept sockets or values."""

    def __init__(self, nt):
        self.nt, self.n, self.l = nt, nt.nodes, nt.links

    def new(self, t, **kw):
        nd = self.n.new(t)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def put(self, sock, val):
        if isinstance(val, bpy.types.NodeSocket):
            self.l.new(val, sock)
        elif val is not None:
            sock.default_value = val

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.new('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if c is not None:
            self.put(nd.inputs[2], c)
        return nd.outputs[0]

    def vmath(self, op, a, b=None, c=None):
        nd = self.new('ShaderNodeVectorMath', operation=op)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if c is not None:
            self.put(nd.inputs[2], c)
        return nd.outputs[0]

    def sep(self, v):
        nd = self.new('ShaderNodeSeparateXYZ')
        self.put(nd.inputs[0], v)
        return nd.outputs[0], nd.outputs[1], nd.outputs[2]

    def vec(self, x, y, z):
        nd = self.new('ShaderNodeCombineXYZ')
        for i, val in enumerate((x, y, z)):
            self.put(nd.inputs[i], val)
        return nd.outputs[0]

    def noise(self, vec, scale, detail=2.0, rough=0.5):
        nd = self.new('ShaderNodeTexNoise')
        self.put(nd.inputs['Vector'], vec)
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        return nd.outputs['Fac'], nd.outputs['Color']

    def voronoi_f1(self, vec, scale, rnd=1.0):
        nd = self.new('ShaderNodeTexVoronoi', feature='F1')
        self.put(nd.inputs['Vector'], vec)
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Randomness'].default_value = rnd
        return nd.outputs['Distance']

    def mr(self, val, f0, f1, t0=0.0, t1=1.0, smooth=False):
        nd = self.new('ShaderNodeMapRange')
        if smooth:
            nd.interpolation_type = 'SMOOTHSTEP'
        self.put(nd.inputs['Value'], val)
        self.put(nd.inputs['From Min'], f0)
        self.put(nd.inputs['From Max'], f1)
        self.put(nd.inputs['To Min'], t0)
        self.put(nd.inputs['To Max'], t1)
        return nd.outputs['Result']

    def ramp(self, fac, stops):
        nd = self.new('ShaderNodeValToRGB')
        els = nd.color_ramp.elements
        while len(els) < len(stops):
            els.new(0.5)
        for e, (pos, col) in zip(els, stops):
            e.position = pos
            e.color = tuple(col) + (1.0,)
        self.put(nd.inputs['Fac'], fac)
        return nd.outputs['Color']

    def mix(self, fac, a, b):
        nd = self.new('ShaderNodeMix', data_type='RGBA', blend_type='MIX')
        self.put(nd.inputs['Factor'], fac)
        sa, sb = G.sock(nd.inputs, 'A'), G.sock(nd.inputs, 'B')
        self.put(sa, a if isinstance(a, bpy.types.NodeSocket) else tuple(a) + (1.0,))
        self.put(sb, b if isinstance(b, bpy.types.NodeSocket) else tuple(b) + (1.0,))
        return G.sock(nd.outputs, 'Result')


def _fresh(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, _NB(m.node_tree)


# ================================================================================== stone
def _vein_family(nb, Pw, ang_deg, spacing, wmin, wmax, keep, seed, taper_scale=1.6, frag=0.4):
    """One family of flowing veins: iso-lines of the warped across-flow coordinate (so a family never
    branches), one line every `spacing` m. Each line has its own random presence / weight, and along its
    length its half-width swells and pinches to zero (veins taper out instead of ending abruptly).
    Returns (d, w): distance to the line centre and the local half-width (both metres)."""
    ca, sa = math.cos(math.radians(ang_deg)), math.sin(math.radians(ang_deg))
    x, y, _ = nb.sep(Pw)
    t = nb.math('MULTIPLY_ADD', x, -sa, nb.math('MULTIPLY', y, ca))          # across-flow coordinate
    jit, _ = nb.noise(nb.vmath('ADD', Pw, (seed, 2.0 * seed, 0.0)), 0.9, detail=2.0)
    f = nb.math('MULTIPLY_ADD', jit, 1.7, nb.math('DIVIDE', t, spacing))     # lines bunch and spread
    fr = nb.math('FRACT', f)
    d = nb.math('MULTIPLY', nb.math('ABSOLUTE', nb.math('SUBTRACT', fr, 0.5)), spacing)
    lid = nb.math('FLOOR', f)
    wn = nb.new('ShaderNodeTexWhiteNoise', noise_dimensions='2D')
    nb.put(wn.inputs['Vector'], nb.vec(lid, seed, 0.0))
    rnd = wn.outputs['Value']
    present = nb.mr(rnd, 1.0 - keep - 0.03, 1.0 - keep + 0.03, smooth=True)
    weight = nb.mr(rnd, 1.0 - keep, 1.0, 0.3, 1.0)
    # along-line swell / pinch: noise in the along-flow coordinate (offset per line so neighbours differ)
    s = nb.math('MULTIPLY_ADD', x, ca, nb.math('MULTIPLY', y, sa))
    sw, _ = nb.noise(nb.vec(s, nb.math('MULTIPLY', lid, 3.7), seed), taper_scale, detail=2.0, rough=0.5)
    swell = nb.mr(sw, frag, frag + 0.13, 0.0, 1.0, smooth=True)
    wv, _ = nb.noise(nb.vec(nb.math('MULTIPLY', s, 2.6), nb.math('MULTIPLY', lid, 1.3), seed + 0.5), 1.0, detail=2.0)
    w = nb.math('MULTIPLY', nb.math('MULTIPLY', present, weight), swell)
    w = nb.math('MULTIPLY', w, nb.mr(wv, 0.3, 0.7, wmin, wmax))
    return d, w


def _vein_masks(nb, d, w, rim=1.45, halo=5.0, halo_add=0.008):
    """core (soft-edged), gold rim, and a faint diffuse halo around a vein."""
    w = nb.math('MAXIMUM', w, 1e-5)
    core = nb.mr(d, w, nb.math('MULTIPLY', w, 0.5), smooth=True)
    rim_m = nb.mr(d, nb.math('MULTIPLY_ADD', w, rim, 0.0008), nb.math('MULTIPLY', w, 0.9), smooth=True)
    hal = nb.mr(d, nb.math('MULTIPLY_ADD', w, halo, halo_add), w, smooth=True)
    on = nb.mr(w, 2e-5, 4e-4, smooth=True)                # no halo where the vein has pinched out
    return core, nb.math('MULTIPLY', rim_m, on), nb.math('MULTIPLY', hal, on)


JOINT_Y_FT = 2.925       # horizontal slab joint, flush with the head of the firebox trim
# vein families: (angle deg, line spacing m, min / max half-width m, share of lines present, seed,
#                 fragmentation threshold (higher = shorter runs), along-line taper frequency)
VEIN_FAMILIES = ((60.0, 0.18, 0.0032, 0.0160, 0.60, 1.0, 0.40, 1.6),
                 (-28.0, 0.20, 0.0028, 0.0135, 0.60, 5.0, 0.40, 1.8),
                 (15.0, 0.26, 0.0020, 0.0090, 0.55, 3.0, 0.43, 2.0),
                 (-72.0, 0.25, 0.0020, 0.0100, 0.55, 7.0, 0.43, 2.0))


def stone_material(origin_obj):
    """Polished book-matched grey-green onyx / quartzite pair. Texture space = object space of
    `origin_obj` (an Empty on the seam at the stone face, 4 ft up; its Blender +X points into the wall,
    units metres). |Y| mirrors the pattern about the seam; X > 0 wraps it round the side returns (mitre).

    Look (1077 W McKinley slab): a warm grey-green ground with flowing translucent bands and milky
    drifts (domain-warped sine bands, not cells), crossed by soft-edged rust-brown veins with gold rims
    that follow the flow, swell and pinch out. Four vein families at different angles and weights (plus
    fine gold hairlines) give the dense, criss-crossing figure of the reference without a voronoi crack
    network; mirrored at the seam they meet as many small chevrons. A hairline horizontal joint at the firebox head splits each
    side into an upper and a lower slab (the lower piece is a slightly shifted cut of the same block)."""
    name = 'Z_living_stone_bookmatch'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nb = _fresh(name)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    tc = nb.new('ShaderNodeTexCoord')
    tc.object = origin_obj
    X, Y, Z = nb.sep(tc.outputs['Object'])
    ay = nb.math('ABSOLUTE', Y)                       # mirror about the seam
    mx = nb.math('MAXIMUM', X, 0.0)                   # side returns continue the face (mitre)
    u = nb.math('ADD', ay, mx)
    vj = (JOINT_Y_FT - 4.0) * 0.3048
    low = nb.math('LESS_THAN', Z, vj)                 # lower slab: same block, ~1/8in kerf further on
    v = nb.math('MULTIPLY_ADD', low, -0.004, Z)
    u = nb.math('MULTIPLY_ADD', low, 0.006, u)
    P = nb.vec(u, v, 0.37)
    # domain warps: a broad flowing drift for the translucent bands; the veins take a gentler warp
    # (long, mostly straight runs with a few kinks) so they cut across the bands like the reference
    _, wc1 = nb.noise(P, 0.75, detail=4.0, rough=0.55)
    _, wc2 = nb.noise(nb.vmath('ADD', P, (3.1, 7.7, 1.3)), 3.2, detail=3.0, rough=0.55)
    _, wc3 = nb.noise(nb.vmath('ADD', P, (6.3, 2.9, 4.1)), 11.0, detail=2.0, rough=0.5)
    c1 = nb.vmath('SUBTRACT', wc1, (0.5, 0.5, 0.5))
    c2 = nb.vmath('SUBTRACT', wc2, (0.5, 0.5, 0.5))
    c3 = nb.vmath('SUBTRACT', wc3, (0.5, 0.5, 0.5))
    Pb = nb.vmath('MULTIPLY_ADD', c2, (0.10, 0.10, 0.0), nb.vmath('MULTIPLY_ADD', c1, (0.8, 0.8, 0.0), P))
    Pv = nb.vmath('MULTIPLY_ADD', c2, (0.07, 0.07, 0.0), nb.vmath('MULTIPLY_ADD', c1, (0.5, 0.5, 0.0), P))
    Pv = nb.vmath('MULTIPLY_ADD', c3, (0.012, 0.012, 0.0), Pv)

    # --- ground: warm grey-green, low-contrast cloudy tone with soft translucent bands and milky drifts
    ba = math.radians(52)
    bx, by, _ = nb.sep(Pb)
    tb = nb.math('MULTIPLY_ADD', bx, -math.sin(ba), nb.math('MULTIPLY', by, math.cos(ba)))
    bn, _ = nb.noise(nb.vmath('ADD', Pb, (9.0, 1.0, 0.0)), 0.9, detail=5.0, rough=0.55)
    band = nb.math('SINE', nb.math('MULTIPLY_ADD', bn, 8.0, nb.math('MULTIPLY', tb, 2 * math.pi / 0.55)))
    band = nb.math('MULTIPLY_ADD', band, 0.5, 0.5)
    cloud, _ = nb.noise(nb.vmath('ADD', Pb, (1.0, 5.0, 0.0)), 1.3, detail=6.0, rough=0.62)
    tone = nb.math('MULTIPLY_ADD', band, 0.25, nb.math('MULTIPLY', cloud, 0.75))
    ground = nb.ramp(tone, [(0.25, (0.196, 0.198, 0.162)), (0.45, (0.262, 0.265, 0.218)),
                            (0.6, (0.318, 0.317, 0.266)), (0.8, (0.41, 0.402, 0.338))])
    # milky drifts: phase-shifted bands gated by a broad mask, softly striated
    band2 = nb.math('SINE', nb.math('MULTIPLY_ADD', bn, 10.0, nb.math('MULTIPLY', tb, 2 * math.pi / 0.33)))
    mk, _ = nb.noise(nb.vmath('ADD', Pb, (4.0, 8.0, 0.0)), 1.0, detail=3.0)
    milk = nb.math('MULTIPLY', nb.mr(band2, 0.2, 1.0, smooth=True), nb.mr(mk, 0.45, 0.66, smooth=True))
    wisp, _ = nb.noise(nb.vec(nb.math('MULTIPLY', tb, 9.0), nb.math('MULTIPLY', bn, 3.0), 2.0), 1.0, detail=4.0)
    milk = nb.math('MULTIPLY', milk, nb.mr(wisp, 0.3, 0.7, 0.55, 1.0))
    ground = nb.mix(nb.math('MULTIPLY', milk, 0.7), ground, (0.64, 0.63, 0.58))
    grain, _ = nb.noise(Pb, 45.0, detail=2.0)
    scl = nb.new('ShaderNodeVectorMath', operation='SCALE')
    nb.put(scl.inputs[0], ground)
    nb.put(scl.inputs['Scale'], nb.mr(grain, 0.3, 0.7, 0.96, 1.03))
    col = scl.outputs[0]

    # --- veins: four flowing families at different angles and weights, plus fine gold hairlines.
    # No direction dominates, so the book-match mirror makes many small chevrons, never one big V.
    core = rim = halo = None
    wmax_all = None
    for ang, sp, wmin, wmax, keep, seed, frag, tap in VEIN_FAMILIES:
        d, w = _vein_family(nb, Pv, ang, sp, wmin, wmax, keep, seed, taper_scale=tap, frag=frag)
        k, r, h = _vein_masks(nb, d, w)
        wk = nb.math('MULTIPLY', k, w)
        if core is None:
            core, rim, halo, wmax_all = k, r, h, wk
        else:
            core = nb.math('MAXIMUM', core, k)
            rim = nb.math('MAXIMUM', rim, r)
            halo = nb.math('MAXIMUM', halo, h)
            wmax_all = nb.math('MAXIMUM', wmax_all, wk)
    d5, w5 = _vein_family(nb, Pv, 34.0, 0.08, 0.0005, 0.0015, 0.35, 9.0, taper_scale=2.6, frag=0.45)
    k5, r5, _ = _vein_masks(nb, d5, w5, rim=2.5)
    col = nb.mix(nb.math('MULTIPLY', halo, 0.4), col, (0.34, 0.27, 0.17))
    col = nb.mix(nb.math('MULTIPLY', nb.math('MAXIMUM', rim, nb.math('MULTIPLY', r5, 0.6)), 0.75), col, (0.38, 0.27, 0.11))
    # vein core: deep oxblood-brown in the heart of the wide veins, lighter rust-brown in thin ones
    vcore = nb.ramp(nb.mr(wmax_all, 0.0015, 0.009), [(0.0, (0.16, 0.08, 0.038)), (1.0, (0.07, 0.026, 0.015))])
    col = nb.mix(nb.math('MULTIPLY', core, 0.95), col, vcore)
    col = nb.mix(nb.math('MULTIPLY', k5, 0.55), col, (0.30, 0.20, 0.09))
    # hairline epoxy joints: book-match seam (front face only) and the horizontal joint
    seam = nb.mr(ay, 0.0005, 0.0015, 0.6, 0.0)
    front = nb.mr(mx, 0.002, 0.0005)
    joint = nb.mr(nb.math('ABSOLUTE', nb.math('SUBTRACT', Z, vj)), 0.0005, 0.0015, 0.6, 0.0)
    jm = nb.math('MAXIMUM', nb.math('MULTIPLY', seam, front), joint)
    col = nb.mix(jm, col, (0.10, 0.10, 0.095))
    nb.put(bsdf.inputs['Base Color'], col)
    # polished slab: crisp reflections; veins slightly duller and etched, joints a hair recessed
    vein = nb.math('MAXIMUM', nb.math('MAXIMUM', core, k5), nb.math('MULTIPLY', rim, 0.5))
    rough = nb.math('MULTIPLY_ADD', vein, 0.14, nb.math('MULTIPLY_ADD', milk, -0.02, 0.07))
    nb.put(bsdf.inputs['Roughness'], rough)
    bump = nb.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.1
    bump.inputs['Distance'].default_value = 0.0003
    nb.put(bump.inputs['Height'], nb.math('SUBTRACT', 1.0, nb.math('MAXIMUM', nb.math('MULTIPLY', vein, 0.5), jm)))
    nb.put(bsdf.inputs['Normal'], bump.outputs['Normal'])
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    m.diffuse_color = (0.28, 0.28, 0.235, 1)
    return m


# ================================================================================== fire
# Linear gas burner under glass media. Three flame sheets (back, middle, front) along the burner:
# row -> (sheet height ft, nominal flame height range ft, emission strength). Strength is the BUILT value
# (lighting.apply_balance scales emission x0.4 at render time).
FLAME_ROWS = {'back': (0.85, (0.34, 0.62), 0.95),
              'mid': (0.75, (0.28, 0.52), 1.1),
              'front': (0.40, (0.11, 0.22), 0.45)}
FLAME_RAMP = [(0.0, (0.08, 0.16, 0.9)), (0.06, (0.22, 0.2, 0.7)), (0.14, (1.0, 0.36, 0.06)),
              (0.32, (1.0, 0.52, 0.13)), (0.62, (1.0, 0.36, 0.06)), (1.0, (0.75, 0.15, 0.02))]


def _tongues(nb, u2, yy, H, seed, cw, hlo, hhi, off):
    """One layer of flame tongues: the burner is split into ~cw ft cells (jittered), each with its own
    height and width; a tongue is widest (touching its neighbours) at the burner and tapers to a soft
    point. Returns (intensity 0..1, t = height / this tongue's height)."""
    U = nb.math('ADD', nb.math('DIVIDE', u2, cw), off)
    cid = nb.math('FLOOR', U)
    fr = nb.math('SUBTRACT', nb.math('FRACT', U), 0.5)
    wn = nb.new('ShaderNodeTexWhiteNoise', noise_dimensions='2D')
    nb.put(wn.inputs['Vector'], nb.vec(cid, nb.math('ADD', seed, off * 7.0), 0.0))
    r = wn.outputs['Value']
    r1, r2, _ = nb.sep(wn.outputs['Color'])
    hgt = nb.math('MULTIPLY', H, nb.mr(r, 0.0, 1.0, hlo, hhi))
    t = nb.math('DIVIDE', yy, hgt)
    omt = nb.math('MAXIMUM', nb.math('SUBTRACT', 1.0, t), 0.0)
    hw = nb.math('MULTIPLY', nb.math('POWER', omt, 0.6), nb.mr(r2, 0.0, 1.0, 0.34, 0.58))
    # each tongue leans its own way, more with height
    lean = nb.math('MULTIPLY', nb.mr(r1, 0.0, 1.0, -0.35, 0.35), nb.math('MINIMUM', t, 1.0))
    ctr = nb.math('ADD', nb.mr(r1, 0.0, 1.0, -0.1, 0.1), lean)
    dist = nb.math('ABSOLUTE', nb.math('SUBTRACT', fr, ctr))
    I = nb.mr(dist, hw, nb.math('MULTIPLY', hw, 0.05), smooth=True)
    return I, t


def flame_material(row='mid', name=None, length=4.4):
    """A row of small, soft, semi-transparent gas flames on a sheet whose UV u runs along the burner in
    FEET (0..length) and v 0..1 up the sheet (FLAME_ROWS[row][0] ft tall).

    Two staggered layers of tongues (~2-3in wide, each with its own height) rise from a continuous base
    at the burner and taper to soft points; a height-growing sway makes them lean and curl, and noise
    breaks their tips into wisps. Dim blue roots, a golden lower body, orange-red tips; local flame
    height drifts along the burner. The mask scales the emission COLOUR (the strength stays a plain value,
    so the render-time light balance scales it with every other emitter). ObjectInfo.Random re-seeds it."""
    hk, (hmin, hmax), peak = FLAME_ROWS[row]
    name = name or f'Z_living_flame_{row}'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nb = _fresh(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nb.new('ShaderNodeOutputMaterial')
    uvn = nb.new('ShaderNodeUVMap')
    u, v, _ = nb.sep(uvn.outputs['UV'])
    yy = nb.math('MULTIPLY', v, hk)                                     # ft above the burner
    seed = nb.math('MULTIPLY', nb.new('ShaderNodeObjectInfo').outputs['Random'], 53.0)
    hn, _ = nb.noise(nb.vec(nb.math('MULTIPLY', u, 0.9), seed, 0.5), 1.0, detail=1.0)
    H = nb.mr(hn, 0.32, 0.68, hmin, hmax)                               # local flame height (ft)
    # sway: grows with height, so tongues lean and curl; small flicker of the edges
    tg = nb.math('DIVIDE', yy, H)
    wob, _ = nb.noise(nb.vec(nb.math('MULTIPLY', u, 1.3), nb.math('MULTIPLY_ADD', yy, 2.4, seed), 1.5), 1.0, detail=2.0)
    sway = nb.math('MULTIPLY', nb.math('SUBTRACT', wob, 0.5), nb.math('MINIMUM', tg, 1.4))
    u2 = nb.math('MULTIPLY_ADD', sway, 0.4, u)
    fk, _ = nb.noise(nb.vec(nb.math('MULTIPLY', u, 9.0), nb.math('MULTIPLY_ADD', yy, 5.0, seed), 3.0), 1.0, detail=1.0)
    u2 = nb.math('MULTIPLY_ADD', nb.math('SUBTRACT', fk, 0.5), nb.math('MULTIPLY', nb.math('MINIMUM', tg, 1.0), 0.05), u2)
    cw = 0.17 if row == 'front' else 0.23
    Ia, ta = _tongues(nb, u2, yy, H, seed, cw, 0.3, 1.3, 0.0)
    Ib, tb = _tongues(nb, u2, yy, H, seed, cw * 1.3, 0.22, 0.8, 0.5)
    Ic, tc = _tongues(nb, u2, yy, H, seed, cw * 2.6, 0.5, 1.45, 0.25)      # a few broad, merged flames
    I = nb.math('MAXIMUM', nb.math('MAXIMUM', Ia, nb.math('MULTIPLY', Ib, 0.85)), nb.math('MULTIPLY', Ic, 0.55))
    t = nb.math('MINIMUM', nb.math('MINIMUM', ta, tb), tc)
    # wispy tips: noise eats the upper part of each tongue
    wisp, _ = nb.noise(nb.vec(nb.math('MULTIPLY', u2, 7.0), nb.math('MULTIPLY_ADD', yy, 3.0, seed), 5.0), 1.0, detail=2.0)
    I = nb.math('MULTIPLY', I, nb.mr(nb.math('SUBTRACT', wisp, nb.math('MULTIPLY', t, 0.4)), 0.02, 0.32, smooth=True))
    base = nb.mr(yy, 0.0, 0.03, smooth=True)
    ends = nb.math('MULTIPLY', nb.mr(u, 0.0, 0.3, smooth=True), nb.mr(u, length, length - 0.3, smooth=True))
    tcl = nb.math('MINIMUM', t, 1.0)
    # brightness: dim blue roots (broken along the burner), brightest in the lower body, fading tips
    rb, _ = nb.noise(nb.vec(nb.math('MULTIPLY', u, 2.5), seed, 4.0), 1.0, detail=1.0)
    root = nb.mr(rb, 0.35, 0.6, 0.06, 0.25)
    prof = nb.math('MULTIPLY', nb.mr(t, 0.04, 0.18, 0.0, 1.0, smooth=True), nb.mr(t, 0.25, 1.0, 1.0, 0.12, smooth=True))
    prof = nb.math('MAXIMUM', prof, nb.math('MULTIPLY', root, nb.mr(t, 0.12, 0.04)))
    mask = nb.math('MULTIPLY', nb.math('MULTIPLY', I, prof), nb.math('MULTIPLY', base, ends))
    col = nb.new('ShaderNodeVectorMath', operation='SCALE')
    # thin edges of a tongue burn redder than its core
    tcol = nb.math('MINIMUM', nb.math('MULTIPLY_ADD', nb.math('SUBTRACT', 1.0, I), nb.math('MULTIPLY', tcl, 0.35), tcl), 1.0)
    nb.put(col.inputs[0], nb.ramp(tcol, FLAME_RAMP))
    nb.put(col.inputs['Scale'], mask)
    em = nb.new('ShaderNodeEmission')
    nb.put(em.inputs['Color'], col.outputs[0])
    em.inputs['Strength'].default_value = peak
    tr = nb.new('ShaderNodeBsdfTransparent')
    add = nb.new('ShaderNodeAddShader')
    nb.l.new(tr.outputs[0], add.inputs[0])
    nb.l.new(em.outputs[0], add.inputs[1])
    nb.l.new(add.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (1.0, 0.5, 0.15, 0.3)
    return m


def ember_bed_material():
    """Dark crushed-glass bed (mostly hidden under the media); a thin, broken glow along the burner line
    (Generated X across the bed depth, Y along its length) with a few hotter spots."""
    name = 'Z_living_ember_bed'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nb = _fresh(name)
    b = m.node_tree.nodes.get('Principled BSDF')
    gx, gy, _ = nb.sep(nb.new('ShaderNodeTexCoord').outputs['Generated'])
    d = nb.math('ABSOLUTE', nb.math('SUBTRACT', gx, 0.5))
    band = nb.mr(d, 0.09, 0.02, smooth=True)
    fl, _ = nb.noise(nb.vec(nb.math('MULTIPLY', gy, 28.0), nb.math('MULTIPLY', gx, 5.0), 0.0), 1.0, detail=3.0)
    flick = nb.mr(fl, 0.4, 0.72, smooth=True)
    sp = nb.voronoi_f1(nb.vec(nb.math('MULTIPLY', gy, 110.0), nb.math('MULTIPLY', gx, 16.0), 0.0), 1.0)
    spots = nb.mr(sp, 0.35, 0.05, smooth=True)
    glow = nb.math('MULTIPLY', band, nb.math('MULTIPLY', flick, nb.math('MULTIPLY_ADD', spots, 0.6, 0.4)))
    nb.put(b.inputs['Emission Color'], nb.ramp(glow, [(0.0, (0, 0, 0)), (0.5, (0.8, 0.17, 0.02)),
                                                     (1.0, (1.0, 0.42, 0.1))]))
    b.inputs['Emission Strength'].default_value = 1.6
    b.inputs['Base Color'].default_value = (0.015, 0.014, 0.013, 1)
    b.inputs['Roughness'].default_value = 0.3
    m.diffuse_color = (0.08, 0.04, 0.02, 1)
    return m


def media_material(tone='black'):
    """Tumbled fire glass: glossy black or smoked bronze, picks up the flames as small glints."""
    name = f'Z_living_fire_media_{tone}'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    col = (0.012, 0.012, 0.013) if tone == 'black' else (0.07, 0.042, 0.022)
    b.inputs['Base Color'].default_value = col + (1,)
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Specular IOR Level'].default_value = 0.8
    m.diffuse_color = col + (1,)
    return m
