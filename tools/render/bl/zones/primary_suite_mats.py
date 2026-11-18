"""Zone-specific materials for primary_suite (names prefixed Z_primary_suite_)."""
import bpy

PFX = 'Z_primary_suite_'


def _srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def _sock(sockets, ident):
    for s in sockets:
        if s.identifier == ident:
            return s
    raise KeyError(ident)


def _mix_rgb(nt, a, b, fac=None):
    """ShaderNodeMix (RGBA) -> returns (node, result socket). a/b: colors or sockets."""
    mx = nt.nodes.new('ShaderNodeMix')
    mx.data_type = 'RGBA'
    sa, sb = _sock(mx.inputs, 'A_Color'), _sock(mx.inputs, 'B_Color')
    for s, v in ((sa, a), (sb, b)):
        if isinstance(v, tuple):
            s.default_value = v
        else:
            nt.links.new(v, s)
    sf = _sock(mx.inputs, 'Factor_Float')
    if fac is None:
        sf.default_value = 0.5
    elif isinstance(fac, float):
        sf.default_value = fac
    else:
        nt.links.new(fac, sf)
    return mx, _sock(mx.outputs, 'Result_Color')


def _new(name):
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m is not None:
        return m, None
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    return m, m.node_tree


def _bsdf(nt):
    b = nt.nodes.get('Principled BSDF')
    if b is None:
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = nt.nodes.get('Material Output') or nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(b.outputs[0], out.inputs['Surface'])
    return b


def _set(b, key, val):
    try:
        b.inputs[key].default_value = val
    except (KeyError, TypeError):
        pass


def _pos(nt, scale=1.0):
    """Object-space coordinates (zone objects have their origin at the world origin or close)."""
    tc = nt.nodes.new('ShaderNodeTexCoord')
    if scale == 1.0:
        return tc.outputs['Object']
    mp = nt.nodes.new('ShaderNodeVectorMath')
    mp.operation = 'SCALE'
    mp.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], mp.inputs[0])
    return mp.outputs[0]


def fabric(name, color, rough=0.85, sheen=0.6, weave_scale=420.0, bump=0.25, slub=True, tint_var=0.05,
           sss=0.0, kind='linen', wrinkle=0.0):
    """Woven textile: sheen + fine weave bump + slub variation in tone.
    kind: 'linen' (cross weave + slubs), 'knit' (rib), 'boucle' (loopy), 'velvet' (smooth, strong sheen)."""
    m, nt = _new(name)
    if nt is None:
        return m
    b = _bsdf(nt)
    base = _srgb(color)
    _set(b, 'Roughness', rough)
    _set(b, 'Sheen Weight', sheen)
    _set(b, 'Sheen Roughness', 0.45)
    _set(b, 'Sheen Tint', (1, 1, 1, 1))
    if sss:
        _set(b, 'Subsurface Weight', sss)
        _set(b, 'Subsurface Radius', (0.02, 0.015, 0.01))
        _set(b, 'Subsurface Scale', 0.01)
    co = _pos(nt)
    # tone variation (slubs / dye irregularity)
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9.0
    nz.inputs['Detail'].default_value = 6.0
    nt.links.new(co, nz.inputs['Vector'])
    c0 = tuple(max(0.0, v * (1 - tint_var)) for v in base[:3]) + (1,)
    c1 = tuple(min(1.0, v * (1 + tint_var)) for v in base[:3]) + (1,)
    _, res = _mix_rgb(nt, c0, c1, nz.outputs['Fac'])
    nt.links.new(res, b.inputs['Base Color'])
    # micro structure
    if kind == 'knit':
        tex = nt.nodes.new('ShaderNodeTexWave')
        tex.wave_type = 'BANDS'
        tex.bands_direction = 'Z'
        tex.inputs['Scale'].default_value = weave_scale * 0.25
        tex.inputs['Distortion'].default_value = 2.0
        tex.inputs['Detail'].default_value = 2.0
        nt.links.new(co, tex.inputs['Vector'])
        h = tex.outputs['Fac']
    elif kind == 'boucle':
        tex = nt.nodes.new('ShaderNodeTexVoronoi')
        tex.inputs['Scale'].default_value = weave_scale * 0.6
        nt.links.new(co, tex.inputs['Vector'])
        h = tex.outputs['Distance']
    elif kind == 'velvet':
        tex = nt.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 60.0
        tex.inputs['Detail'].default_value = 4.0
        nt.links.new(co, tex.inputs['Vector'])
        h = tex.outputs['Fac']
    else:  # linen: two crossing fine wave bands + slub noise
        w1 = nt.nodes.new('ShaderNodeTexWave')
        w1.wave_type = 'BANDS'
        w1.bands_direction = 'X'
        w1.inputs['Scale'].default_value = weave_scale
        w1.inputs['Distortion'].default_value = 1.5
        nt.links.new(co, w1.inputs['Vector'])
        w2 = nt.nodes.new('ShaderNodeTexWave')
        w2.wave_type = 'BANDS'
        w2.bands_direction = 'Y'
        w2.inputs['Scale'].default_value = weave_scale
        w2.inputs['Distortion'].default_value = 1.5
        nt.links.new(co, w2.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMath')
        mx.operation = 'MULTIPLY'
        nt.links.new(w1.outputs['Fac'], mx.inputs[0])
        nt.links.new(w2.outputs['Fac'], mx.inputs[1])
        h = mx.outputs[0]
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.0015
    nt.links.new(h, bp.inputs['Height'])
    if wrinkle > 0:
        # soft vertical drape wrinkles (stretched noise, long along Blender Z = up)
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1.0, 1.0, 0.22)
        nt.links.new(co, mp.inputs['Vector'])
        wn = nt.nodes.new('ShaderNodeTexNoise')
        wn.inputs['Scale'].default_value = 14.0
        wn.inputs['Detail'].default_value = 3.0
        wn.inputs['Distortion'].default_value = 0.4
        nt.links.new(mp.outputs[0], wn.inputs['Vector'])
        bw = nt.nodes.new('ShaderNodeBump')
        bw.inputs['Strength'].default_value = wrinkle
        bw.inputs['Distance'].default_value = 0.012
        nt.links.new(wn.outputs['Fac'], bw.inputs['Height'])
        nt.links.new(bw.outputs['Normal'], bp.inputs['Normal'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = base
    return m


def sheer(name='sheer_linen', color='#f4f0e8', opacity=0.42):
    """Sheer linen voile: diffuse+translucent fabric mixed with transparency (no refraction)."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pr = nt.nodes.new('ShaderNodeBsdfPrincipled')
    pr.inputs['Base Color'].default_value = _srgb(color)
    _set(pr, 'Roughness', 0.9)
    _set(pr, 'Sheen Weight', 0.4)
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = _srgb(color)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (1, 1, 1, 1)
    m1 = nt.nodes.new('ShaderNodeMixShader')
    m1.inputs['Fac'].default_value = 0.45
    nt.links.new(pr.outputs[0], m1.inputs[1])
    nt.links.new(tl.outputs[0], m1.inputs[2])
    # weave-driven opacity
    co = _pos(nt)
    w1 = nt.nodes.new('ShaderNodeTexWave')
    w1.wave_type = 'BANDS'
    w1.bands_direction = 'Z'
    w1.inputs['Scale'].default_value = 300.0
    nt.links.new(co, w1.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = opacity - 0.06
    mr.inputs['To Max'].default_value = opacity + 0.06
    nt.links.new(w1.outputs['Fac'], mr.inputs['Value'])
    m2 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mr.outputs[0], m2.inputs['Fac'])
    nt.links.new(tr.outputs[0], m2.inputs[1])
    nt.links.new(m1.outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], out.inputs['Surface'])
    m.diffuse_color = _srgb(color)
    return m


def shade_fabric(name='lamp_shade', color='#efe6d6'):
    """Lamp shade linen: mostly translucent so the inner point light glows through it."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pr = nt.nodes.new('ShaderNodeBsdfPrincipled')
    pr.inputs['Base Color'].default_value = _srgb(color)
    _set(pr, 'Roughness', 0.9)
    _set(pr, 'Sheen Weight', 0.3)
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    # near-neutral linen: the 2700K bulb already supplies the warmth (a peach tint read salmon)
    tl.inputs['Color'].default_value = tuple(min(1.0, c * 1.03) for c in _srgb(color)[:3]) + (1,)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.5
    nt.links.new(pr.outputs[0], mix.inputs[1])
    nt.links.new(tl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    m.diffuse_color = _srgb(color)
    return m


def roller_fabric(name='roller_shade', color='#ece6dc'):
    """Light-filtering roller shade screen: translucent, slightly see-through."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pr = nt.nodes.new('ShaderNodeBsdfPrincipled')
    pr.inputs['Base Color'].default_value = _srgb(color)
    _set(pr, 'Roughness', 0.85)
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = _srgb('#e9dfcf')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    m1 = nt.nodes.new('ShaderNodeMixShader')
    m1.inputs['Fac'].default_value = 0.5
    nt.links.new(pr.outputs[0], m1.inputs[1])
    nt.links.new(tl.outputs[0], m1.inputs[2])
    m2 = nt.nodes.new('ShaderNodeMixShader')
    m2.inputs['Fac'].default_value = 0.88
    nt.links.new(tr.outputs[0], m2.inputs[1])
    nt.links.new(m1.outputs[0], m2.inputs[2])
    # fine weave bump on the opaque part
    co = _pos(nt)
    w1 = nt.nodes.new('ShaderNodeTexWave')
    w1.wave_type = 'BANDS'
    w1.bands_direction = 'Z'
    w1.inputs['Scale'].default_value = 500.0
    nt.links.new(co, w1.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.15
    nt.links.new(w1.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], pr.inputs['Normal'])
    nt.links.new(m2.outputs[0], out.inputs['Surface'])
    m.diffuse_color = _srgb(color)
    return m


def ceramic(name, color, rough=0.35, speckle=True, glaze=0.0):
    """Matte / satin glazed ceramic with fine speckle and slight throwing-ring bump."""
    m, nt = _new(name)
    if nt is None:
        return m
    b = _bsdf(nt)
    base = _srgb(color)
    _set(b, 'Roughness', rough)
    if glaze:
        _set(b, 'Coat Weight', glaze)
        _set(b, 'Coat Roughness', 0.08)
    co = _pos(nt)
    if speckle:
        vo = nt.nodes.new('ShaderNodeTexNoise')
        vo.inputs['Scale'].default_value = 900.0
        vo.inputs['Detail'].default_value = 1.0
        nt.links.new(co, vo.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 0.66
        mr.inputs['From Max'].default_value = 0.72
        nt.links.new(vo.outputs['Fac'], mr.inputs['Value'])
        _, res = _mix_rgb(nt, base, tuple(v * 0.35 for v in base[:3]) + (1,), mr.outputs[0])
        nt.links.new(res, b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = base
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 60.0
    wv.inputs['Distortion'].default_value = 3.0
    nt.links.new(co, wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.05
    nt.links.new(wv.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = base
    return m


def simple(name, color, rough=0.5, metal=0.0, coat=0.0):
    m, nt = _new(name)
    if nt is None:
        return m
    b = _bsdf(nt)
    b.inputs['Base Color'].default_value = _srgb(color)
    _set(b, 'Roughness', rough)
    _set(b, 'Metallic', metal)
    if coat:
        _set(b, 'Coat Weight', coat)
    m.diffuse_color = _srgb(color)
    return m


def image_canvas(name, image, rough=0.7, bump_img=0.15):
    """Painted canvas using a packed image on UVs; weave bump from a fine wave texture."""
    m, nt = _new(name)
    if nt is None:
        return m
    b = _bsdf(nt)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Cubic'
    uvn = nt.nodes.new('ShaderNodeUVMap')
    nt.links.new(uvn.outputs['UV'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    _set(b, 'Roughness', rough)
    co = _pos(nt)
    w1 = nt.nodes.new('ShaderNodeTexWave')
    w1.wave_type = 'BANDS'
    w1.bands_direction = 'Y'
    w1.inputs['Scale'].default_value = 700.0
    nt.links.new(co, w1.inputs['Vector'])
    w2 = nt.nodes.new('ShaderNodeTexWave')
    w2.wave_type = 'BANDS'
    w2.bands_direction = 'Z'
    w2.inputs['Scale'].default_value = 700.0
    nt.links.new(co, w2.inputs['Vector'])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    nt.links.new(w1.outputs['Fac'], add.inputs[0])
    nt.links.new(w2.outputs['Fac'], add.inputs[1])
    # paint relief from the image luminance (thicker dark paint)
    inv = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(tex.outputs['Color'], inv.inputs[0])
    mm = nt.nodes.new('ShaderNodeMath')
    mm.operation = 'MULTIPLY_ADD'
    mm.inputs[1].default_value = -bump_img * 6
    nt.links.new(inv.outputs[0], mm.inputs[0])
    nt.links.new(add.outputs[0], mm.inputs[2])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.12
    bp.inputs['Distance'].default_value = 0.0008
    nt.links.new(mm.outputs[0], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def rug(name='rug_wool_heather', light='#ddd6c9', dark='#c5bdaf', pile_scale=260.0, half=None, border='#b3aa9b',
        band=(0.16, 0.45)):
    """Low-pile hand-loomed wool rug in warm cream / greige: an isotropic fine heathered field (no
    stretched streaks), a whisper of large-scale tonal cloud, a 3.5in tonal border band (needs the rug
    object's origin at its centre; half = (half width x, half depth z) ft) and a soft pile bump.
    Sheen is low and warm so the rug does not pick up the cool skylight."""
    m, nt = _new(name)
    if nt is None:
        return m
    b = _bsdf(nt)
    _set(b, 'Roughness', 0.96)
    _set(b, 'Sheen Weight', 0.1)
    _set(b, 'Sheen Roughness', 0.55)
    _set(b, 'Sheen Tint', (1.0, 0.93, 0.84, 1.0))
    _set(b, 'Specular IOR Level', 0.25)
    co = _pos(nt)
    # heathered yarn field: fine isotropic noise between two close warm tones
    fine = nt.nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 90.0
    fine.inputs['Detail'].default_value = 8.0
    fine.inputs['Roughness'].default_value = 0.65
    nt.links.new(co, fine.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.3
    mr.inputs['From Max'].default_value = 0.7
    nt.links.new(fine.outputs['Fac'], mr.inputs['Value'])
    _, col = _mix_rgb(nt, _srgb(light), _srgb(dark), mr.outputs[0])
    # very low-contrast large tonal cloud (+-3%)
    big = nt.nodes.new('ShaderNodeTexNoise')
    big.inputs['Scale'].default_value = 1.3
    big.inputs['Detail'].default_value = 3.0
    nt.links.new(co, big.inputs['Vector'])
    bm = nt.nodes.new('ShaderNodeMapRange')
    bm.inputs['To Min'].default_value = 0.97
    bm.inputs['To Max'].default_value = 1.03
    nt.links.new(big.outputs['Fac'], bm.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeVectorMath')
    mul.operation = 'SCALE'
    nt.links.new(col, mul.inputs[0])
    nt.links.new(bm.outputs[0], mul.inputs['Scale'])
    col = mul.outputs[0]
    if half:
        FT_M = 0.3048
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(co, sep.inputs['Vector'])
        dists = []
        for comp, h in (('X', half[0]), ('Y', half[1])):
            ab = nt.nodes.new('ShaderNodeMath')
            ab.operation = 'ABSOLUTE'
            nt.links.new(sep.outputs[comp], ab.inputs[0])
            sb = nt.nodes.new('ShaderNodeMath')
            sb.operation = 'SUBTRACT'
            sb.inputs[0].default_value = h * FT_M
            nt.links.new(ab.outputs[0], sb.inputs[1])
            dists.append(sb)
        dm = nt.nodes.new('ShaderNodeMath')
        dm.operation = 'MINIMUM'
        nt.links.new(dists[0].outputs[0], dm.inputs[0])
        nt.links.new(dists[1].outputs[0], dm.inputs[1])
        # hand-loomed edge wobble, then a soft-edged band mask
        wob = nt.nodes.new('ShaderNodeTexNoise')
        wob.inputs['Scale'].default_value = 14.0
        nt.links.new(co, wob.inputs['Vector'])
        wj = nt.nodes.new('ShaderNodeMath')
        wj.operation = 'MULTIPLY_ADD'
        wj.inputs[1].default_value = 0.005
        wj.inputs[2].default_value = -0.0025
        nt.links.new(wob.outputs['Fac'], wj.inputs[0])
        dd = nt.nodes.new('ShaderNodeMath')
        dd.operation = 'ADD'
        nt.links.new(dm.outputs[0], dd.inputs[0])
        nt.links.new(wj.outputs[0], dd.inputs[1])
        lo = nt.nodes.new('ShaderNodeMapRange')
        lo.inputs['From Min'].default_value = band[0] * FT_M - 0.003
        lo.inputs['From Max'].default_value = band[0] * FT_M + 0.003
        nt.links.new(dd.outputs[0], lo.inputs['Value'])
        hi = nt.nodes.new('ShaderNodeMapRange')
        hi.inputs['From Min'].default_value = band[1] * FT_M + 0.003
        hi.inputs['From Max'].default_value = band[1] * FT_M - 0.003
        nt.links.new(dd.outputs[0], hi.inputs['Value'])
        mk = nt.nodes.new('ShaderNodeMath')
        mk.operation = 'MULTIPLY'
        nt.links.new(lo.outputs[0], mk.inputs[0])
        nt.links.new(hi.outputs[0], mk.inputs[1])
        _, bcol = _mix_rgb(nt, _srgb(border), _srgb(dark), mr.outputs[0])
        _, col = _mix_rgb(nt, col, bcol, mk.outputs[0])
    nt.links.new(col, b.inputs['Base Color'])
    pile = nt.nodes.new('ShaderNodeTexVoronoi')
    pile.inputs['Scale'].default_value = pile_scale
    nt.links.new(co, pile.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.5
    bp.inputs['Distance'].default_value = 0.002
    nt.links.new(pile.outputs['Distance'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = _srgb(light)
    return m


def image_paper(name, image, rough=0.85):
    """Giclee print on matte cotton-rag paper: packed image on UVs, fine fibre bump, no canvas weave."""
    m, nt = _new(name)
    if nt is None:
        return m
    b = _bsdf(nt)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Cubic'
    uvn = nt.nodes.new('ShaderNodeUVMap')
    nt.links.new(uvn.outputs['UV'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    _set(b, 'Roughness', rough)
    co = _pos(nt)
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 900.0
    nz.inputs['Detail'].default_value = 4.0
    nt.links.new(co, nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.06
    bp.inputs['Distance'].default_value = 0.0005
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def museum_glass(name='museum_glass_v2', r0=0.01):
    """Anti-reflective picture glazing: two-sided Schlick Fresnel with ~1% head-on reflectance (plain
    glass is 4%), non-refractive (transparent + glossy) and fully transparent to shadow rays."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    nt.links.new(geo.outputs['Incoming'], dot.inputs[1])
    ab = nt.nodes.new('ShaderNodeMath')
    ab.operation = 'ABSOLUTE'
    nt.links.new(dot.outputs['Value'], ab.inputs[0])
    om = nt.nodes.new('ShaderNodeMath')
    om.operation = 'SUBTRACT'
    om.inputs[0].default_value = 1.0
    nt.links.new(ab.outputs[0], om.inputs[1])
    p5 = nt.nodes.new('ShaderNodeMath')
    p5.operation = 'POWER'
    p5.inputs[1].default_value = 5.0
    nt.links.new(om.outputs[0], p5.inputs[0])
    fr = nt.nodes.new('ShaderNodeMath')
    fr.operation = 'MULTIPLY_ADD'
    fr.inputs[1].default_value = 1.0 - r0
    fr.inputs[2].default_value = r0
    nt.links.new(p5.outputs[0], fr.inputs[0])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.02
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fr.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    lp = nt.nodes.new('ShaderNodeLightPath')
    sh = nt.nodes.new('ShaderNodeBsdfTransparent')
    fin = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Shadow Ray'], fin.inputs['Fac'])
    nt.links.new(mix.outputs[0], fin.inputs[1])
    nt.links.new(sh.outputs[0], fin.inputs[2])
    nt.links.new(fin.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (0.9, 0.9, 0.9, 0.2)
    return m


def stripe(m, color, axis='Y', period_in=0.5, duty=0.32):
    """Overlay woven vertical stripes on a fabric() material (bengal / candy stripe shirting).
    axis: Blender object axis the stripes alternate along (garment width direction); period in inches,
    duty = stripe fraction. Applied once per material."""
    nt = m.node_tree
    if nt is None or m.get('striped'):
        return m
    b = _bsdf(nt)
    if not b.inputs['Base Color'].links:
        return m
    src = b.inputs['Base Color'].links[0].from_socket
    co = _pos(nt)
    w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'
    w.bands_direction = axis
    w.wave_profile = 'SAW'
    w.inputs['Scale'].default_value = 0.31416 / (period_in * 0.0254)
    w.inputs['Distortion'].default_value = 0.0
    nt.links.new(co, w.inputs['Vector'])
    mk = nt.nodes.new('ShaderNodeMapRange')
    mk.inputs['From Min'].default_value = duty - 0.04
    mk.inputs['From Max'].default_value = duty + 0.04
    mk.inputs['To Min'].default_value = 1.0
    mk.inputs['To Max'].default_value = 0.0
    nt.links.new(w.outputs['Fac'], mk.inputs['Value'])
    _, res = _mix_rgb(nt, src, _srgb(color), mk.outputs[0])
    nt.links.new(res, b.inputs['Base Color'])
    m['striped'] = 1
    return m
