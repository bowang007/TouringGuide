"""Zone materials for the warm vintage-American kitchen (names Z_kitchen_dining_<name>).

Owner's style images ("kitchen closet / island / window"): soft layered neutrals, no heavy dark
masses. Painted cream and greige shaker cabinetry, unlacquered brass, honed grey-veined marble, a
white-oak island, whitewashed brick on the sink wall, a cream plaster hood, a fireclay sink, oak
and striped linen for the dining set, sheer striped cafe curtains and a madder-red Persian runner.

Everything is world-space mapped (no UVs, see bl/MATERIALS.md) through the shared node-graph helper
in materials_pbr (imported read-only), except the runner, whose woven pattern is an image generated
here at build time (numpy, packed into the .blend) and mapped with the rug's Generated coordinates.
"""
import math
import os

import bpy

from .. import materials_pbr as MP

PFX = 'Z_kitchen_dining_'
FLAT = os.environ.get('TG_FLAT_MATERIALS') == '1'


def lin(h):
    h = h.lstrip('#')
    return tuple(MP._lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


class _ZG(MP._G):
    """materials_pbr._G writing to a zone material (Z_kitchen_dining_<name>)."""

    def __init__(self, name, viewport, rough):
        self.key = name
        m = bpy.data.materials.new(PFX + name)
        m.use_nodes = True
        self.m = m
        self.nt = m.node_tree
        self.nt.nodes.clear()
        self._c = {}
        self._vp = viewport
        self._r = rough

    def finish(self, shader, disp=None):
        out = self.new('ShaderNodeOutputMaterial')
        self.nt.links.new(shader.outputs[0], out.inputs['Surface'])
        self.m.diffuse_color = tuple(self._vp) + (1.0,)
        self.m.roughness = self._r
        return self.m


def _flat(name, col, rough, metal=0.0):
    m = bpy.data.materials.new(PFX + name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = tuple(col) + (1.0,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = tuple(col) + (1.0,)
    return m


def _get(name, col, rough, maker, metal=0.0):
    m = bpy.data.materials.get(PFX + name)
    if m is not None:
        return m
    if FLAT:
        return _flat(name, col, rough, metal)
    try:
        g = _ZG(name, col, rough)
        return maker(g)
    except Exception:                      # never break the build over a material
        import traceback
        traceback.print_exc()
        old = bpy.data.materials.get(PFX + name)
        if old is not None:
            bpy.data.materials.remove(old)
        return _flat(name, col, rough, metal)


# ------------------------------------------------------------------------------------- paint
CREAM = '#e4dbca'          # perimeter cabinetry (warm cream)
GREIGE = '#bcb09d'         # tall pantry wall (soft greige / mushroom)
PLASTER = '#e8dfcd'        # hood


def _paint(g, col, rough, peel=1.0, brush=0.0):
    """Satin cabinet paint: KEYS-style orange peel plus a faint brushed grain along the face."""
    fr = g.frame()
    n1, _ = g.noise(fr['P'], 330.0, detail=3.0, rough=0.55)
    n2, _ = g.noise(fr['P'], 2.5, detail=2.0)
    n3, _ = g.noise(fr['P'], 60.0, detail=2.0)
    base = g.vscale(col, g.remap(n2, 0.3, 0.7, 0.985, 1.012))
    r = g.add(rough, g.add(g.mul(g.sub(n2, 0.5), 0.06), g.mul(g.sub(n3, 0.5), 0.04)))
    h = g.add(n1, g.mul(n3, 0.4))
    if brush:
        a, b, A, B = g.planar()
        st, _ = g.noise(g.vec(g.mul(a, 4.0), g.mul(b, 900.0), 0.0), 1.0, detail=2.0)
        h = g.add(h, g.mul(st, brush))
    nrm = g.normal(height=h, dist=0.00012 * peel)
    return g.finish(g.bsdf(base, r, 0.0, nrm, **{'Coat Weight': 0.08, 'Coat Roughness': 0.35}))


def paint_cream():
    c = lin(CREAM)
    return _get('paint_cream', c, 0.42, lambda g: _paint(g, c, 0.42, brush=0.25))


def paint_greige():
    c = lin(GREIGE)
    return _get('paint_greige', c, 0.42, lambda g: _paint(g, c, 0.42, brush=0.25))


def plaster_hood():
    c = lin(PLASTER)

    def mk(g):
        s = g.tri('plastered_wall_04', 3.2)
        fr = g.frame()
        if s is None:
            n, _ = g.noise(fr['P'], 3.0, detail=4.0)
            base, r, pert = g.vscale(c, g.remap(n, 0.2, 0.8, 0.97, 1.03)), 0.85, None
        else:
            base = g.grade(s['color'], s['mean'], c, 0.45)
            r = g.rough_from(s, 0.82, 0.5)
            pert = s['pert']
        return g.finish(g.bsdf(base, r, 0.0, g.normal(pert, 0.6)))
    return _get('plaster_hood', c, 0.85, mk)


# -------------------------------------------------------------------------------------- metal
def brass():
    """Unlacquered brass: warm, satin, with soft darker patina drifts and fine wear."""
    c = (0.80, 0.60, 0.30)

    def mk(g):
        fr = g.frame()
        n1, _ = g.noise(fr['P'], 18.0, detail=4.0, rough=0.6)
        n2, _ = g.noise(fr['P'], 420.0, detail=2.0)
        pat = g.ss(n1, 0.45, 0.75)
        base = g.cmix(c, (0.52, 0.38, 0.20), g.mul(pat, 0.55))
        r = g.add(0.24, g.add(g.mul(pat, 0.16), g.mul(g.sub(n2, 0.5), 0.06)))
        nrm = g.normal(height=n2, dist=0.00003)
        return g.finish(g.bsdf(base, r, 1.0, nrm))
    return _get('brass', c, 0.3, mk, metal=1.0)


def cast_iron():
    c = lin('#1e1d1c')

    def mk(g):
        fr = g.frame()
        n1, _ = g.noise(fr['P'], 900.0, detail=2.0)
        r = g.add(0.55, g.mul(g.sub(n1, 0.5), 0.1))
        return g.finish(g.bsdf(c, r, 0.35, g.normal(height=n1, dist=0.00008)))
    return _get('cast_iron', c, 0.55, mk, metal=0.35)


def enamel_black():
    c = lin('#121212')
    return _get('enamel_black', c, 0.22, lambda g: g.finish(g.bsdf(c, 0.22, 0.0, None,
                                                                     **{'Coat Weight': 0.4, 'Coat Roughness': 0.08})))


def fireclay():
    c = lin('#f2efe9')
    return _get('fireclay', c, 0.12, lambda g: g.finish(g.bsdf(c, 0.14, 0.0, None,
                                                                **{'Coat Weight': 0.6, 'Coat Roughness': 0.05})))


# -------------------------------------------------------------------------------------- stone
def _marble(g, base, core, body, halo, warm, contrast, spacing, width, rough, cloud, D, seed, drift=0.55,
            drift_col=None, band=(0.5, 0.74), streak=0.0):
    fr = g.frame()
    col, v = MP._calacatta(g, fr['P'], base, core=core, body=body, halo=halo, gold=warm,
                           contrast=contrast, spacing=spacing, width=width, D=D, cloud=cloud, seed=seed)
    # broad grey clouding (quartzite / honed marble drifts), stretched along the vein flow
    Q = g.vadd(g.vscale(fr['P'], 1.0), g.vscale(MP._unit(D), g.mul(g.vm('DOT_PRODUCT', fr['P'], MP._unit(D)), -0.6)))
    c1, _ = g.noise(g.vadd(Q, (3.1 + seed, 0.7, 5.2)), 1.6, detail=5.0, rough=0.6, distortion=0.4)
    col = g.cmix(col, drift_col or halo, g.mul(g.ss(c1, band[0], band[1]), min(drift * contrast, 1.0)))
    c2, _ = g.noise(g.vadd(Q, (8.4 + seed, 2.2, 1.7)), 3.5, detail=4.0, rough=0.65)
    col = g.cmix(col, body, g.mul(g.ss(c2, 0.6, 0.8), drift * 0.45 * contrast))
    if streak:
        # soft wavy grey streaks along the flow (quartzite's layered banding): a strongly stretched
        # field, so the drifts read as flowing bands rather than round clouds
        S = g.vadd(g.vscale(fr['P'], 1.0), g.vscale(MP._unit(D), g.mul(g.vm('DOT_PRODUCT', fr['P'], MP._unit(D)), -0.88)))
        s1, _ = g.noise(g.vadd(S, (5.5 + seed, 1.9, 7.3)), 2.6, detail=6.0, rough=0.62, distortion=0.8)
        sb = g.sub(1.0, g.ss(g.absf(g.sub(s1, 0.5)), 0.015, 0.075))
        col = g.cmix(col, drift_col or halo, g.mul(sb, streak))
    sp, _ = g.noise(fr['P'], 800.0, detail=1.0)
    col = g.vscale(col, g.remap(sp, 0.3, 0.7, 0.985, 1.01))
    hn, _ = g.noise(fr['P'], 160.0, detail=3.0)
    r = g.add(rough, g.add(g.mul(v, 0.05), g.mul(g.sub(hn, 0.5), 0.05)))
    return g.finish(g.bsdf(col, r, 0.0, g.normal(height=hn, dist=0.00002)))


def marble_honed():
    """Perimeter worktops and the cooktop slab: honed white marble, soft grey veins."""
    b = lin('#eeece7')
    return _get('marble_honed', b, 0.3, lambda g: _marble(
        g, b, core=lin('#8c8883'), body=lin('#aeaaa4'), halo=lin('#cfcbc5'), warm=lin('#cdc5b8'),
        contrast=0.95, spacing=0.62, width=0.005, rough=0.3, cloud=0.04, D=(-0.55, 0.8, 0.75), seed=0.0, drift=0.4))


def quartzite():
    """Island top: thick honed quartzite with heavier, cloudy grey veining (island reference: soft
    grey drifts and flowing bands over much of the slab, not a white slab with a few dark lines)."""
    b = lin('#ebe9e4')
    return _get('quartzite', b, 0.28, lambda g: _marble(
        g, b, core=lin('#7a766f'), body=lin('#958f88'), halo=lin('#bbb6ae'), warm=lin('#c8c0b2'),
        contrast=1.2, spacing=0.42, width=0.007, rough=0.28, cloud=0.06, D=(0.7, 0.55, 0.45), seed=5.7, drift=0.85,
        drift_col=lin('#aaa59d'), band=(0.44, 0.7), streak=0.55))


# --------------------------------------------------------------------------------------- wood
def _veneer(g, col, tid, size, contrast, rough, vertical=False, coat=0.15, stretch=1.3):
    a, b, A, B = g.planar(grain_knob=True)
    if vertical:
        fr = g.frame()
        al = g.lerp(b, a, fr['horiz'])
        ac = g.lerp(a, b, fr['horiz'])
        Al = g.vmix(B, A, fr['horiz'])
        Ac = g.vmix(A, B, fr['horiz'])
        s = g.sample(tid, al, ac, Al, Ac, size, stretch=stretch)
    else:
        s = g.sample(tid, a, b, A, B, size, stretch=stretch)
    if s:
        base = g.grade(s['color'], s['mean'], col, contrast, 0.9)
        r, pert = g.rough_from(s, rough, 0.4), s['pert']
    else:
        base, r, pert = col, rough, None
    return g.finish(g.bsdf(base, r, 0.0, g.normal(pert, 0.5), **{'Coat Weight': coat, 'Coat Roughness': 0.3}))


def oak_island():
    """Warm, mid-tone rift white oak (island base, dining table and chairs)."""
    c = lin('#9f7346')
    return _get('oak_island', c, 0.48, lambda g: _veneer(g, c, 'oak_veneer_03', 1.0, 1.75, 0.48))


def oak_island_v():
    c = lin('#9f7346')
    return _get('oak_island_v', c, 0.48, lambda g: _veneer(g, c, 'oak_veneer_03', 1.0, 1.75, 0.48, vertical=True))


# -------------------------------------------------------------------------------------- brick
def brick():
    """Whitewashed thin-brick veneer (2.25 x 7.6 in face, running bond), cream lime wash."""
    c = lin('#ddd5c8')

    def mk(g):
        a, b, A, B = g.planar()
        s = g.sample('whitewashed_brick', a, b, A, B, 2.0)
        fr = g.frame()
        if s is None:
            n, _ = g.noise(fr['P'], 6.0, detail=4.0)
            return g.finish(g.bsdf(g.vscale(c, g.remap(n, 0.2, 0.8, 0.9, 1.05)), 0.85, 0.0, None))
        base = g.grade(s['color'], s['mean'], c, 0.6, 0.35)
        # extra lime-wash: lift the darker brick faces toward the cream in soft patches
        n, _ = g.noise(fr['P'], 2.2, detail=3.0)
        base = g.cmix(base, c, g.remap(n, 0.3, 0.7, 0.15, 0.45))
        r = g.rough_from(s, 0.86, 0.5)
        return g.finish(g.bsdf(base, r, 0.0, g.normal(s['pert'], 1.25)))
    return _get('brick', c, 0.85, mk)


# ------------------------------------------------------------------------------------- fabric
def _stripes(g, coord, period, width, soft=0.0006):
    """Pin stripes along `coord` (m): 1 on a stripe, 0 between."""
    t = g.fract(g.div(coord, period))
    d = g.mul(g.absf(g.sub(t, 0.5)), period)
    return g.sub(1.0, g.ss(d, width / 2 - soft, width / 2 + soft))


def fabric_stripe():
    """Cream linen with fine brown pin stripes (dining-chair upholstery). The stripes run along
    world Y (Blender), i.e. down the backs and front-to-back on the seats of chairs facing +-x."""
    c = lin('#e7dece')
    s_col = lin('#6c5541')

    def mk(g):
        fr = g.frame()
        s = g.tri('rough_linen', 0.27, MP.FABRIC_RES)
        base = g.grade(s['color'], s['mean'], c, 0.5, 0.2) if s else c
        st = g.mx(_stripes(g, fr['py'], 0.028, 0.0022), _stripes(g, g.add(fr['py'], 0.0045), 0.028, 0.0012))
        base = g.cmix(base, s_col, g.mul(st, 0.85))
        return g.finish(g.bsdf(base, 0.9, 0.0, g.normal(s['pert'] if s else None, 0.8),
                               **{'Sheen Weight': 0.35, 'Sheen Roughness': 0.45}))
    return _get('fabric_stripe', c, 0.9, mk)


def linen_sheer():
    """Cafe curtains: semi-sheer cream linen with faint taupe stripes; lets daylight through."""
    c = lin('#efe8db')
    s_col = lin('#b3a690')

    def mk(g):
        fr = g.frame()
        s = g.tri('rough_linen', 0.27, MP.FABRIC_RES)
        base = g.grade(s['color'], s['mean'], c, 0.45, 0.2) if s else c
        # faint woven stripe (soft-edged so it doesn't read as a crease line on the folds)
        st = _stripes(g, fr['py'], 0.05, 0.005, soft=0.0016)
        base = g.cmix(base, s_col, g.mul(st, 0.22))
        b = g.bsdf(base, 0.9, 0.0, g.normal(s['pert'] if s else None, 0.6),
                   **{'Sheen Weight': 0.3, 'Sheen Roughness': 0.5})
        tl = g.new('ShaderNodeBsdfTranslucent')
        g.put(tl.inputs['Color'], base)
        tr = g.new('ShaderNodeBsdfTransparent')
        g.put(tr.inputs['Color'], (0.95, 0.92, 0.86))
        m1 = g.new('ShaderNodeMixShader')
        g.put(m1.inputs['Fac'], 0.4)
        g.nt.links.new(b.outputs[0], m1.inputs[1])
        g.nt.links.new(tl.outputs[0], m1.inputs[2])
        m2 = g.new('ShaderNodeMixShader')
        g.put(m2.inputs['Fac'], 0.18)
        g.nt.links.new(m1.outputs[0], m2.inputs[1])
        g.nt.links.new(tr.outputs[0], m2.inputs[2])
        return g.finish(m2)
    return _get('linen_sheer', c, 0.9, mk)


def stoneware(name='crock', hexcol='#e9e2d3', rough=0.35, coat=0.3):
    c = lin(hexcol)

    def mk(g):
        fr = g.frame()
        n, _ = g.noise(fr['P'], 14.0, detail=3.0)
        sp, _ = g.noise(fr['P'], 600.0, detail=1.0)
        base = g.vscale(c, g.mul(g.remap(n, 0.3, 0.7, 0.96, 1.03), g.remap(sp, 0.35, 0.65, 0.97, 1.01)))
        return g.finish(g.bsdf(base, rough, 0.0, None, **{'Coat Weight': coat, 'Coat Roughness': 0.12}))
    return _get(name, c, rough, mk)


# ---------------------------------------------------------------------------------- glass/light
def glass_seeded():
    from ..materials import thin_glass
    m = bpy.data.materials.get(PFX + 'glass_seeded')
    if m is None:
        m = thin_glass(PFX + 'glass_seeded', tint=(0.97, 0.94, 0.86), gloss_rough=0.03)
    return m


def glass_amber():
    """Island bell pendants: light amber glass (closet reference). Clear seeded glass all but vanished
    at tour distance, leaving a brass ring floating around the bulb."""
    from ..materials import thin_glass
    m = bpy.data.materials.get(PFX + 'glass_amber')
    if m is None:
        m = thin_glass(PFX + 'glass_amber', tint=(0.90, 0.78, 0.56), f0=0.05, gloss_rough=0.03)
    return m


def glass_cabinet():
    from ..materials import thin_glass
    m = bpy.data.materials.get(PFX + 'glass_cabinet')
    if m is None:
        m = thin_glass(PFX + 'glass_cabinet', tint=(0.95, 0.96, 0.95), f0=0.04, grazing=0.8)
    return m


# ------------------------------------------------------------------------------ Persian runner
def _vnoise(np, rng, h, w, gh, gw):
    """Smooth value noise (h x w) from a random gh x gw grid, bicubic-ish (smoothstep) interp."""
    g = rng.random((gh + 2, gw + 2))
    ys = np.linspace(0, gh, h, endpoint=False)
    xs = np.linspace(0, gw, w, endpoint=False)
    y0 = ys.astype(int)
    x0 = xs.astype(int)
    fy = ys - y0
    fx = xs - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def runner_image(length_in, width_in, ppi=12, seed=7):
    """Paint a vintage Persian (Heriz/Hamadan-style) runner: madder-red field with a navy
    lattice, rosettes and four lozenge medallions, an ivory-guarded navy main border with
    rosettes and a rust vine, abrash banding, wear and knot noise. Returns a packed image."""
    import numpy as np
    name = PFX + 'runner_img'
    old = bpy.data.images.get(name)
    if old is not None:
        return old
    rng = np.random.default_rng(seed)
    W, H = int(length_in * ppi), int(width_in * ppi)
    u = (np.arange(W) + 0.5) / ppi                     # along the length (in)
    v = (np.arange(H) + 0.5) / ppi                     # across (in)
    U, V = np.meshgrid(u, v)
    L, Wd = length_in, width_in
    d_edge = np.minimum(np.minimum(U, L - U), np.minimum(V, Wd - V))

    def c(h):
        h = h.lstrip('#')
        return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    RED, RED2, NAVY, NAVY2 = c('#6b241d'), c('#83301f'), c('#1c1d26'), c('#2a2c38')
    IVORY, GOLD, RUST, BROWN, BLUE = c('#c4ae88'), c('#a17a3d'), c('#93412a'), c('#271813'), c('#4a5566')
    img = np.zeros((H, W, 3))
    img[:] = RED

    def put(mask, col):
        img[mask] = col

    def rosette(x, y, r, petals=8):
        rr = np.hypot(x, y)
        th = np.arctan2(y, x)
        return rr < r * (0.62 + 0.38 * np.abs(np.cos(petals / 2 * th)))

    # ---------------------------------------------------------------- field (inside 4.2 in)
    FB = 4.2
    fu, fv = U - FB, V - FB
    fl, fw = L - 2 * FB, Wd - 2 * FB
    infield = d_edge >= FB
    # dense diamond lattice (cell ~3.4 x 3.6 in), thin dark lines
    P, Q = 3.4, fw / 6.0
    cu = np.mod(fu, P) / P - 0.5
    cv = np.mod(fv, Q) / Q - 0.5
    dl = np.abs(np.abs(cu) + np.abs(cv) - 0.5)
    put(infield & (dl < 0.045), NAVY2)
    xr, yr = cu * P, cv * Q
    # alternate cell motifs: rosette | small leaf cross, checkerboard by cell index
    ci = (np.floor(fu / P) + np.floor(fv / Q)) % 2 == 0
    put(infield & ci & rosette(xr, yr, 0.62), IVORY)
    put(infield & ci & rosette(xr, yr, 0.36, 6), RUST)
    put(infield & ci & (np.hypot(xr, yr) < 0.12), NAVY)
    cross = ((np.abs(xr) < 0.12) & (np.abs(yr) < 0.75)) | ((np.abs(yr) < 0.12) & (np.abs(xr) < 0.7))
    put(infield & ~ci & cross, NAVY)
    put(infield & ~ci & (np.abs(xr) / 0.32 + np.abs(yr) / 0.32 < 1), GOLD)
    # tiny gold/blue knots on the lattice nodes
    xn = (np.mod(fu + P / 2, P) / P - 0.5) * P
    yn = (np.mod(fv + Q / 2, Q) / Q - 0.5) * Q
    put(infield & (np.abs(xn) / 0.32 + np.abs(yn) / 0.28 < 1), BLUE)
    # three stepped lozenge medallions along the centre line
    cy = Wd / 2
    for k in range(3):
        cx = FB + fl * (k + 0.5) / 3
        dx, dy = (U - cx), (V - cy)
        stp = 0.35 * np.round(np.abs(dx) / 0.35)          # stepped (knotted) outline
        def loz(a, b):
            return stp / a + np.abs(dy) / b < 1
        put(infield & loz(6.4, 7.6), IVORY)
        put(infield & loz(5.9, 7.0), NAVY)
        put(infield & loz(4.4, 5.2), RED2)
        put(infield & loz(3.9, 4.6) & ~loz(3.5, 4.1), NAVY2)
        put(infield & rosette(dx, dy, 1.6, 8), IVORY)
        put(infield & rosette(dx, dy, 1.05, 8), GOLD)
        put(infield & rosette(dx, dy, 0.55, 6), RED)
        put(infield & (np.hypot(dx, dy) < 0.2), NAVY)
        for s in (-1, 1):
            put(infield & (np.abs(dx) / 0.6 + np.abs(dy - s * 8.2) / 0.8 < 1), NAVY)
            put(infield & (np.abs(dx - s * 7.2) / 0.7 + np.abs(dy) / 0.6 < 1), NAVY)
    # ---------------------------------------------------------------- borders
    band = (d_edge < FB)
    put(band, NAVY)
    put(d_edge < 0.4, BROWN)                                       # binding
    put((d_edge >= 0.4) & (d_edge < 0.85), RED)                    # outer guard
    put((d_edge >= 3.45) & (d_edge < 3.9), RED)                    # inner guard
    put((d_edge >= 3.9) & (d_edge < FB), BROWN)
    along = np.where(np.minimum(V, Wd - V) < np.minimum(U, L - U), U, V)
    for d0, d1 in ((0.4, 0.85), (3.45, 3.9)):                      # ivory guard dots
        gd = (d_edge >= d0) & (d_edge < d1)
        put(gd & (np.abs(np.mod(along, 0.8) - 0.4) < 0.12) & (np.abs(d_edge - (d0 + d1) / 2) < 0.12), IVORY)
    # main border: rust meander + rosettes every 3 in
    mb = (d_edge >= 0.85) & (d_edge < 3.45)
    mid = (0.85 + 3.45) / 2
    off = d_edge - mid
    vine = np.abs(off - 0.85 * np.sin(along / 3.0 * 2 * np.pi)) < 0.13
    put(mb & vine, RUST)
    ax = np.mod(along, 3.0) - 1.5
    put(mb & rosette(ax, off, 0.95, 8), RED2)
    put(mb & rosette(ax, off, 0.5, 6), IVORY)
    put(mb & (np.hypot(ax, off) < 0.16), NAVY)
    lx = np.mod(along + 1.5, 3.0) - 1.5
    put(mb & ((lx / 0.42) ** 2 + (off / 0.7) ** 2 < 1) & ~vine, GOLD)
    # ---------------------------------------------------------------- age: abrash, wear, knots
    ab = _vnoise(np, rng, 1, W, 1, int(L / 6) + 2)[0]
    img *= (0.9 + 0.16 * ab)[None, :, None]
    wear = _vnoise(np, rng, H, W, int(Wd / 9) + 2, int(L / 9) + 2)
    wear2 = _vnoise(np, rng, H, W, int(Wd / 2.5) + 2, int(L / 2.5) + 2)
    w = np.clip((wear * 0.7 + wear2 * 0.3 - 0.5) * 2.0, 0, 1)[..., None] * 0.22
    img = img * (1 - w) + c('#8f7d66')[None, None, :] * w
    knots = rng.random((H, W))[..., None]
    img *= 0.9 + 0.16 * knots
    # soften the drawing (hand-knotted edges are never razor sharp), mute and darken a touch
    for _ in range(2):
        k = img.copy()
        img = (2 * k + np.roll(k, 1, 0) + np.roll(k, -1, 0) + np.roll(k, 1, 1) + np.roll(k, -1, 1)) / 6
    lum = img.mean(-1, keepdims=True)
    img = (lum + (img - lum) * 0.85) * 0.92
    img = np.clip(img, 0, 1)
    im = bpy.data.images.new(name, W, H, alpha=False)
    rgba = np.ones((H, W, 4), np.float32)
    rgba[..., :3] = img
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im


def rug_persian(length_in, width_in):
    """Wool pile with the woven runner image (Generated coordinates: x along the length, y across)."""
    c = lin('#7c2a22')

    def mk(g):
        im = runner_image(length_in, width_in)
        tc = g.new('ShaderNodeTexCoord')
        gx, gy, _ = g.sep(tc.outputs['Generated'])
        n = g.new('ShaderNodeTexImage', interpolation='Linear', extension='EXTEND')
        n.image = im
        g.put(n.inputs['Vector'], g.vec(gx, gy, 0.0))
        fr = g.frame()
        fuzz, _ = g.noise(fr['P'], 500.0, detail=2.0)
        fl, _ = g.noise(fr['P'], 60.0, detail=2.0)
        base = g.vscale(n.outputs['Color'], g.remap(fl, 0.3, 0.7, 0.93, 1.05))
        nrm = g.normal(height=g.add(fuzz, g.mul(fl, 0.5)), dist=0.0012, bump=0.6)
        return g.finish(g.bsdf(base, 0.95, 0.0, nrm, **{'Sheen Weight': 0.55, 'Sheen Roughness': 0.45}))
    return _get('rug_persian', c, 0.95, mk)
