"""Material library for the modern restyle (runs inside Blender).

CONTRACT: `get(key) -> bpy.types.Material`. Every key in KEYS must resolve. Room modules only
ever ask for materials by key, so finishes can be upgraded here without touching geometry code.

Texture mapping: geometry produced by the build has NO UVs, so textured materials use world-space
mapping in real-world meters: planar mapping along each face's horizontal tangent for oriented
patterns (boards, tiles, grain) and world triplanar for isotropic ones (fabric, stucco, concrete).
Cycles' BOX projection is not used: it blends by the object-space normal and stretches textures on
rotated objects. Details in bl/MATERIALS.md.

`_build` first asks the textured PBR library (bl/materials_pbr.py, see bl/MATERIALS.md) and falls
back to the flat Principled BSDF below on any error or None. Glass keys always use thin_glass().
Set TG_FLAT_MATERIALS=1 to force the flat fallback (fast layout checks).
"""
import os

import bpy

# key: (base color hex, roughness, metallic, description)
KEYS = {
    # --- architecture -------------------------------------------------------------------------
    'paint_wall':        ('#f2f0eb', 0.88, 0.0, 'warm white matte wall paint (eggshell), very subtle roller texture'),
    'paint_ceiling':     ('#f6f5f1', 0.92, 0.0, 'flat white ceiling paint'),
    'paint_trim':        ('#f3f2ee', 0.45, 0.0, 'satin white trim / jambs / flat casings / window returns'),
    'door_slab':         ('#f1f0ec', 0.42, 0.0, 'satin white flush slab interior door'),
    'walnut_door':       ('#5a3b26', 0.45, 0.0, 'rich walnut veneer, vertical grain, front door'),
    'stucco':            ('#eeece6', 0.95, 0.0, 'smooth sand-finish exterior stucco, warm white'),
    'wood_cladding':     ('#9b8268', 0.6, 0.0, 'natural-grey cedar / thermo-ash vertical cladding boards (entry accent), low saturation'),
    'fascia_charcoal':   ('#2a2b2d', 0.55, 0.0, 'charcoal painted fascia / bargeboards'),
    'roof_metal':        ('#2c2e30', 0.58, 0.08, 'matte charcoal (PVDF-painted) standing-seam metal roof, seams ~16in apart running down-slope'),
    'black_aluminum':    ('#1a1b1c', 0.38, 0.4, 'matte black powder-coated aluminum window/door frames'),
    'window_white':      ('#f5f4f1', 0.36, 0.0, 'satin white window / glazed-door frames, sashes and grid bars (seventh round: every window white)'),
    'glass_clear':       ('#ffffff', 0.0, 0.0, 'clear architectural glass (thin pane, slight green tint, ior 1.52)'),
    'glass_frosted':     ('#ffffff', 0.35, 0.0, 'acid-etched / obscured glass'),
    'glass_picture':     ('#ffffff', 0.0, 0.0, 'anti-reflective picture-frame glass (~1% reflectance, two-sided, shadow rays pass)'),
    'oak_floor':         ('#d9c4a3', 0.42, 0.0, 'light white-oak wide-plank floor, ~9in boards, matte oil finish, boards run N-S'),
    'tile_floor_bath':   ('#bdbab4', 0.55, 0.0, 'large-format 24x48in warm-grey porcelain floor tile, fine grout'),
    'tile_shower_floor': ('#9d9a95', 0.6, 0.0, 'small-format 2x2in grey porcelain mosaic shower floor'),
    'concrete_garage':   ('#b9b8b3', 0.6, 0.0, 'sealed light-grey garage concrete'),
    'porch_pavers':      ('#c9c6bf', 0.75, 0.0, 'large-format 24x24in light concrete porch pavers'),
    'concrete_drive':    ('#c4c1ba', 0.85, 0.0, 'light broom-finish concrete driveway'),
    'foundation':        ('#a09f9a', 0.9, 0.0, 'concrete foundation'),
    # --- interior finishes --------------------------------------------------------------------
    'walnut_slab':       ('#6b4a30', 0.4, 0.0, 'walnut veneer flat-slab cabinet fronts, horizontal grain, satin'),
    'white_oak_veneer':  ('#cfb38c', 0.45, 0.0, 'light white-oak veneer (shelves, accents)'),
    'quartz_calacatta':  ('#f4f3f1', 0.12, 0.0, 'Calacatta-look white quartz, soft grey veins, polished'),
    'quartz_white':      ('#f2f1ee', 0.2, 0.0, 'solid white quartz, honed-polished'),
    'stone_feature':     ('#8d958c', 0.18, 0.0, 'book-matched green-grey onyx/quartzite slab with rust-gold veins (fireplace wall)'),
    'tile_wave_white':   ('#f1f0ec', 0.35, 0.0, 'white 3D wave/ribbed ceramic wall tile 12x24in (strong bump)'),
    'tile_wall_porcelain': ('#e6e3dd', 0.3, 0.0, 'large-format 24x48in light marble-look porcelain wall tile'),
    'tile_fluted_black': ('#232323', 0.45, 0.0, 'black fluted/ribbed accent wall tile'),
    'stainless':         ('#c9cbcc', 0.28, 1.0, 'brushed stainless steel appliances'),
    'black_metal':       ('#161616', 0.42, 0.85, 'matte black metal (hardware, faucets, lamp frames)'),
    'chrome':            ('#e5e7e8', 0.06, 1.0, 'polished chrome'),
    'mirror':            ('#f5f6f7', 0.0, 1.0, 'silvered mirror'),
    'ceramic_white':     ('#f6f6f4', 0.08, 0.0, 'glossy white vitreous china / acrylic (sinks, WC, tub)'),
    'led_warm':          ('#ffd9a8', 0.5, 0.0, 'warm 3000K LED emitter (diffusers, strips, ring pendants)'),
    'fabric_boucle':     ('#ece7dd', 0.95, 0.0, 'off-white boucle upholstery'),
    'fabric_linen_white': ('#f1eee8', 0.9, 0.0, 'white stonewashed linen bedding'),
    'fabric_linen_grey': ('#b9b4ab', 0.9, 0.0, 'warm grey linen / upholstered headboard'),
    'fabric_mustard':    ('#c49a3c', 0.85, 0.0, 'ochre / mustard velvet accent pillows'),
    'fabric_sage':       ('#9aa38d', 0.85, 0.0, 'muted sage accent textile'),
    'leather_tan':       ('#9a6a3e', 0.5, 0.0, 'saddle-tan leather (counter stools)'),
    'rug_wool_cream':    ('#e3dccf', 0.98, 0.0, 'cream low-pile wool rug with subtle texture'),
    'rug_wool_grey':     ('#a9a59d', 0.98, 0.0, 'warm grey low-pile wool rug'),
    'paint_black':       ('#1c1c1c', 0.5, 0.0, 'matte black paint'),
    'plaster_white':     ('#efede8', 0.85, 0.0, 'smooth white plaster (range hood, sculptural surfaces)'),
    # --- exterior / landscape -----------------------------------------------------------------
    'grass_lawn':        ('#5f7f3a', 0.9, 0.0, 'healthy lawn (use geometry/hair where close to camera)'),
    'gravel_dark':       ('#55565a', 0.95, 0.0, 'dark grey decomposed granite / gravel'),
    'pebbles_river':     ('#8f8b84', 0.8, 0.0, 'grey river pebbles border'),
    'soil_mulch':        ('#4a3a2c', 0.95, 0.0, 'dark bark mulch planting beds'),
    'ipe_deck':          ('#7a4a2d', 0.55, 0.0, 'ipe hardwood deck boards'),
    'fence_charcoal':    ('#343638', 0.7, 0.0, 'charcoal horizontal slat fence'),
    'concrete_paver':    ('#cfccc5', 0.8, 0.0, 'large concrete stepping pavers'),
}


def _hex(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def _build(key):
    """Textured PBR material from materials_pbr; fallback: plain Principled BSDF from KEYS."""
    col, rough, metal, _ = KEYS[key]
    if key in ('glass_clear', 'glass_frosted'):
        return thin_glass('M_' + key, frosted=(key == 'glass_frosted'))
    if key == 'glass_picture':
        return thin_glass('M_' + key, tint=(0.985, 0.99, 0.985), f0=0.01, grazing=0.55, gloss_rough=0.02)
    if not os.environ.get('TG_FLAT_MATERIALS'):
        try:
            from . import materials_pbr
            pbr = materials_pbr.build(key)
            if pbr is not None:
                return pbr
        except Exception as e:  # never let the PBR library break a build
            print(f'[materials] PBR build of {key!r} failed ({e!r}); using flat fallback')
    m = bpy.data.materials.new('M_' + key)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = _hex(col)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if key.startswith('glass'):
        bsdf.inputs['Transmission Weight'].default_value = 1.0
        bsdf.inputs['IOR'].default_value = 1.52
    if key == 'led_warm':
        bsdf.inputs['Emission Color'].default_value = _hex(col)
        bsdf.inputs['Emission Strength'].default_value = 8.0
    m.diffuse_color = _hex(col)
    return m


def thin_glass(name, tint=(0.93, 0.96, 0.95), frosted=False, f0=0.04, grazing=1.0, gloss_rough=None):
    """Architectural thin-pane glass. MUST NOT use refraction (Principled transmission / Glass
    BSDF): Cycles treats sun through refractive glass as a caustic and drops it, so interiors
    lose all direct sunlight. Instead: Fresnel-mixed Transparent (or Translucent when frosted)
    + Glossy reflection, which lets camera, sun and shadow rays pass straight through.
    f0 = reflectance at normal incidence (0.04 float glass, 0.01 anti-reflective picture glass);
    grazing scales the Schlick grazing term (AR coatings also cut the grazing glare)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    # Two-sided Schlick Fresnel from |N.I|. (The Fresnel node inverts IOR on back faces, which
    # gives total internal reflection -> the pane turns into a mirror for rays leaving the
    # room and blocks all sun shadow rays.)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    nt.links.new(geo.outputs['Incoming'], dot.inputs[1])
    cosv = nt.nodes.new('ShaderNodeMath')
    cosv.operation = 'ABSOLUTE'
    nt.links.new(dot.outputs['Value'], cosv.inputs[0])
    omc = nt.nodes.new('ShaderNodeMath')
    omc.operation = 'SUBTRACT'
    omc.inputs[0].default_value = 1.0
    nt.links.new(cosv.outputs[0], omc.inputs[1])
    p5 = nt.nodes.new('ShaderNodeMath')
    p5.operation = 'POWER'
    p5.inputs[1].default_value = 5.0
    nt.links.new(omc.outputs[0], p5.inputs[0])
    fres = nt.nodes.new('ShaderNodeMath')
    fres.operation = 'MULTIPLY_ADD'
    fres.inputs[1].default_value = (1.0 - f0) * grazing
    fres.inputs[2].default_value = f0
    nt.links.new(p5.outputs[0], fres.inputs[0])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = gloss_rough if gloss_rough is not None else (0.25 if frosted else 0.0)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = tint + (1,)
    base = tr
    if frosted:
        tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
        tl.inputs['Color'].default_value = (0.85, 0.86, 0.86, 1)
        mixf = nt.nodes.new('ShaderNodeMixShader')
        mixf.inputs['Fac'].default_value = 0.88          # mostly diffuse transmission
        nt.links.new(tr.outputs[0], mixf.inputs[1])
        nt.links.new(tl.outputs[0], mixf.inputs[2])
        base = mixf
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fres.outputs[0], mix.inputs['Fac'])
    nt.links.new(base.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    # Shadow rays (sun / lamps) pass the pane as tinted transparency: standard archviz glass.
    lp = nt.nodes.new('ShaderNodeLightPath')
    sh = nt.nodes.new('ShaderNodeBsdfTransparent')
    sh.inputs['Color'].default_value = ((0.55, 0.56, 0.56) if frosted else tint) + (1,)
    final = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Shadow Ray'], final.inputs['Fac'])
    nt.links.new(mix.outputs[0], final.inputs[1])
    nt.links.new(sh.outputs[0], final.inputs[2])
    nt.links.new(final.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (0.8, 0.85, 0.85, 0.3)
    return m


def get(key):
    if key not in KEYS:
        raise KeyError(f'unknown material key {key!r}; add it to materials.KEYS')
    m = bpy.data.materials.get('M_' + key)
    return m if m is not None else _build(key)
