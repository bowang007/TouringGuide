"""Zone materials of the primary bath (stop A0), named Z_baths_primary_<name>.

Built with the library's graph helper (materials_pbr._G: world-space planar / triplanar mapping, no
UVs) so they follow the same conventions as the shared library. Each builder falls back to a flat
Principled material if anything fails (e.g. a texture download), so the zone always builds.

The room is fitted out AFTER the warp, in plan feet (see baths_primary.py), so world-space patterns
are laid out on the built room: tile courses start at the floor, the floor grid is centred on the room.

Seventh round (2026-11-21), the owner: "some of the wall are green, make it coherent be removing these green
walls and set it to white". The grey-green board wainscot, its cap rail and the cream plaster are gone with their
materials (vgroove, sage_paint, plaster); the walls are the shell's own wall paint (library `paint_wall`) and the
shower's tile, mosaic and stone trims are white, so the room is white with one stone wall.

  stone         stacked natural stone, warm brown-tan with light sandy mortar (Poly Haven
                rustic_stone_wall_02) with TRUE displacement: the vanity (south) wall
  shower_tile   matte white porcelain, 24x48in stack bond, quiet joints: the shower's walls, the niche, the
                tiled window reveal and the low tile base of the room's other walls
  shower_mosaic 2x2in matte white mosaic (shower floor)
  sill          honed off-white stone (shower threshold, niche sill, window sill of the shower lite)
  floor_stone   quiet warm-grey honed stone, 24x24in, fine joints (floor)
  oak           solid oak slab (vanity, mirror frames, window stool)
  timber        reclaimed timber (shelf);  beam: rough dark hewn timber (wall beam, ceiling beam)
  nickel        brushed nickel (taps, shower set, glass fittings, towel bar)
  glass         low-iron (extra-clear) shower glass, neutral;  glass_edge: its pale edge
  enamel        cream vitreous enamel (lamp shades);  bulb / filament: clear lamp bulb
  jute          flat-woven cotton / jute mat, cream with thin dark stripes
  striped       terry towel with woven stripes
  galvanised    dull zinc (plant pot);  cactus, sedum: plant greens;  stoneware, amber, green_glass: shelf
  botanical     small botanical drawing (framed print on the shelf), generated with numpy
"""
import math

import bpy

PFX = 'Z_baths_primary_'
IN = 0.0254
FT = 0.3048


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


def flat(name, hexcol, rough=0.5, metal=0.0, **extra):
    """Plain Principled material PFX+name (small props)."""
    full = PFX + name
    return bpy.data.materials.get(full) or _flat(full, hexlin(hexcol), rough, metal, **extra)


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


# ------------------------------------------------------------------------------------- tiles
# Seventh round: the shower is white. The wall paint is library `paint_wall` #f2f0eb; the tile sits a shade under it
# and is neutral (no cream, no green), so tile, base and painted wall read as one white.
TILE_WHITE = '#eeedea'
TILE_GROUT = '#dddbd6'
MOSAIC_WHITE = '#e9e8e4'


def shower_tile(a0_ft=0.0, floor_ft=0.028):
    """Matte white porcelain, 24x48in, stack bond with the long side horizontal, 1/16in joints in the tile's own
    tone (seventh round: it was honed cream). Plain and quiet: a neutral white a shade under the wall paint, the
    faintest cloud in the body, no veins, no colour. a0_ft puts a vertical joint at that plan coordinate along the
    wall; the courses start at the floor (floor_ft)."""
    white = hexlin(TILE_WHITE)

    def build(g, P):
        a, b, A, B = g.planar()
        tid, d, _, _ = P._grid(g, a, b, 48 * IN, 24 * IN, a0=a0_ft * FT, b0=floor_ft * FT)
        _, rc = g.white(tid)
        r0, r1, r2 = g.sep(rc)
        qx, qy, qz = g.mad(r0, 7.0, a), g.mad(r1, 5.0, b), g.mul(r2, 3.0)       # every tile from another part of the slab
        n1, _ = g.noise(g.vec(g.mul(qx, 1.1), g.mul(qy, 2.4), qz), 1.0, detail=5.0, rough=0.6, distortion=0.3)
        n2, _ = g.noise(g.vec(g.mul(qx, 0.5), g.mul(qy, 1.1), g.add(qz, 5.0)), 1.0, detail=3.0)
        speck, _ = g.noise(g.frame()['P'], 380.0, detail=1.0)
        col = g.vscale(white, g.remap(n2, 0.3, 0.7, 0.98, 1.012))
        col = g.cmix(col, hexlin('#e6e4df'), g.mul(g.ss(n1, 0.55, 0.78), 0.3))
        col = g.vscale(col, g.mul(g.remap(r2, 0.0, 1.0, 0.992, 1.008), g.remap(speck, 0.3, 0.7, 0.995, 1.005)))
        grout = g.sub(1.0, g.ss(d, 0.0007, 0.001))
        col = g.cmix(col, hexlin(TILE_GROUT), grout)
        rough = g.lerp(g.add(0.5, g.mul(g.sub(n2, 0.5), 0.1)), 0.85, grout)
        height = g.add(g.ss(d, 0.0006, 0.0022), g.mul(n1, 0.03))
        nrm = g.normal(height=height, dist=0.0007)
        return _out(g, g.bsdf(col, rough, 0.0, nrm))
    return _make('shower_tile', build, (white, 0.55))


def sill():
    """Honed off-white stone, one piece (threshold strips, niche sill, the shower lite's window sill): the tile's
    white, a shade greyer, so the trims read as stone and not as a second colour."""
    white = hexlin('#e6e3dd')

    def build(g, P):
        fr = g.frame()
        n1, _ = g.noise(fr['P'], 9.0, detail=4.0, rough=0.6)
        n2, _ = g.noise(fr['P'], 240.0, detail=2.0)
        col = g.vscale(white, g.mul(g.remap(n1, 0.3, 0.7, 0.975, 1.02), g.remap(n2, 0.3, 0.7, 0.99, 1.01)))
        nrm = g.normal(height=n2, dist=0.0002)
        return _out(g, g.bsdf(col, g.add(0.42, g.mul(g.sub(n1, 0.5), 0.1)), 0.0, nrm))
    return _make('sill', build, (white, 0.45))


def shower_mosaic():
    """2x2in matte white porcelain mosaic, white grout a shade darker, a slight per-tile tone (shower floor)."""
    def build(g, P):
        a, b, A, B = g.planar()
        tw = 2.0 * IN
        tid, d, _, _ = P._grid(g, a, b, tw, tw)
        _, rc = g.white(tid)
        r0, _, _ = g.sep(rc)
        col = g.vscale(hexlin(MOSAIC_WHITE), g.remap(r0, 0.0, 1.0, 0.965, 1.02))
        grout = g.sub(1.0, g.ss(d, 0.0013, 0.0018))
        col = g.cmix(col, hexlin('#d6d4ce'), grout)
        nrm = g.normal(height=g.ss(d, 0.0013, 0.0045), dist=0.0012)
        return _out(g, g.bsdf(col, g.lerp(0.45, 0.85, grout), 0.0, nrm))
    return _make('shower_mosaic', build, (hexlin(MOSAIC_WHITE), 0.5))


def floor_stone(cx_ft=4.975, cz_ft=24.78):
    """Quiet warm-grey honed stone floor: 24x24in, square grid centred on the room (cx_ft, cz_ft), fine joints a
    shade darker. No pattern: a faint cloud in each tile and a slight tone step from tile to tile."""
    grey = hexlin('#7a7166')

    def build(g, P):
        a, b, A, B = g.planar()
        tw = 24 * IN
        tid, d, _, _ = P._grid(g, a, b, tw, tw, a0=(cx_ft - 1.0) * FT, b0=(-cz_ft - 1.0) * FT)
        _, rc = g.white(tid)
        r0, r1, r2 = g.sep(rc)
        s = g.sample('plastered_wall_04', g.mad(r0, 9.0, a), g.mad(r1, 9.0, b), A, B, 2.6, maps=('diffuse', 'nor_gl'))
        col = g.grade(s['color'], s['mean'], grey, 1.15, sat=0.5) if s else grey
        fr = g.frame()
        n, _ = g.noise(fr['P'], 2.2, detail=3.0)
        sp, _ = g.noise(fr['P'], 420.0, detail=1.0)
        col = g.vscale(col, g.mul(g.mul(g.remap(n, 0.3, 0.7, 0.95, 1.04), g.remap(sp, 0.25, 0.75, 0.975, 1.02)),
                                  g.remap(r2, 0.0, 1.0, 0.955, 1.04)))
        grout = g.sub(1.0, g.ss(d, 0.0008, 0.0012))
        col = g.cmix(col, hexlin('#57534d'), grout)
        rough = g.lerp(g.add(0.52, g.mul(g.sub(n, 0.5), 0.12)), 0.9, grout)
        nrm = g.normal(s['pert'] if s else None, 0.25, height=g.ss(d, 0.0006, 0.0024), dist=0.0008)
        return _out(g, g.bsdf(col, rough, 0.0, nrm))
    return _make('floor_stone', build, (grey, 0.55))


# ------------------------------------------------------------------------------------- stone
STONE_SIZE = 2.3          # m: height of one repeat of the rustic_stone_wall_02 scan (2.2 m: stones 3-9cm tall, 11-43cm long)
STONE_STRETCH = 0.85      # ... and its width as a fraction of that: the stones a little shorter, so the wall reads as
#                           the style image's small stacked rubble (4-12in long, 1 1/2-4in tall), not as long ledge stone
STONE_MID = 0.62          # displacement map value of the mortar bed: everything below it is flat, light sandy mortar,
#                           so the joints are pointed nearly flush and show between the stones, as in the image
STONE_DISP = 0.075        # m per unit of the map above the mortar bed (stone faces ~1.4cm proud, the proudest 2.8cm)


def stone():
    """Stacked natural stone, warm brown-tan, in a light sandy lime mortar: colour, roughness and normal from the
    scan, plus TRUE displacement (material displacement 'BOTH') from its height map in world space, clamped at the
    mortar bed so the relief only comes forward of the mesh plane."""
    target = hexlin('#86694b')
    mortar = hexlin('#b7a481')

    def build(g, P):
        a, b, A, B = g.planar()
        s = g.sample('rustic_stone_wall_02', g.add(a, 0.31), g.add(b, 0.47), A, B, STONE_SIZE, stretch=STONE_STRETCH,
                     maps=('diffuse', 'rough', 'nor_gl', 'displacement'))
        if not s:
            raise RuntimeError('rustic_stone_wall_02 unavailable')
        col = g.grade(s['color'], s['mean'], target, 1.12, sat=1.15)
        h, _, _ = g.sep(s['displacement'])
        # every stone its own shade: a slow noise stretched along the courses moves whole stones lighter / darker,
        # warmer / greyer, as in a wall laid from one quarry's mixed stone
        n, _ = g.noise(g.vec(g.mul(a, 2.2), g.mul(b, 9.0), 0.0), 1.0, detail=2.0)
        n2, _ = g.noise(g.vec(g.mul(a, 3.1), g.mul(b, 11.0), 4.0), 1.0, detail=1.0)
        col = g.vscale(col, g.remap(n, 0.3, 0.7, 0.84, 1.14))
        col = g.cmix(col, g.vm('MULTIPLY', col, (1.09, 0.98, 0.84)), g.ss(n2, 0.5, 0.7))          # ochre stones
        col = g.cmix(col, g.vm('MULTIPLY', col, (0.93, 0.96, 1.0)), g.mul(g.ss(n2, 0.42, 0.25), 0.6))    # greyer ones
        # the mortar bed: light sandy lime, only where the height map lies at its floor (the joints)
        mort = g.sub(1.0, g.ss(h, STONE_MID + 0.012, STONE_MID + 0.085))
        fr = g.frame()
        mn, _ = g.noise(fr['P'], 55.0, detail=3.0)
        col = g.cmix(col, g.vscale(mortar, g.remap(mn, 0.3, 0.7, 0.9, 1.08)), g.mul(mort, 0.8))
        rough = g.lerp(g.rough_from(s, 0.8, 0.6, lo=0.5), 0.95, mort)
        nrm = g.normal(s['pert'], 1.0)
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


def stone_relief_ft(v=0.82):
    """Stone-face offset in front of the stone mesh plane (ft) at map value v: 0.82 is a typical face, 1.0 the
    proudest stones."""
    return (v - STONE_MID) * STONE_DISP / 0.3048


# --------------------------------------------------------------------------------------- wood
def oak():
    """Solid oak slab of glued boards with knots, honey oil finish (Poly Haven oak_wood_planks, 1.2m).
    Grain along world X on tops (the vanity runs east-west) and along each vertical face."""
    target = hexlin('#97775a')          # natural honey oak

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
    """Reclaimed timber board (weathered_brown_planks), mid brown, matte wax: the shelf."""
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


def beam():
    """Old hewn oak beam: dark, dry and rough. The plank scan is stretched along the beam (one long grain, no board
    joints in sight), darkened, with checks (long drying cracks) and adze facets as bump."""
    target = hexlin('#5b4633')

    def build(g, P):
        a, b, A, B = g.planar()
        s = g.sample('weathered_brown_planks', g.add(a, 0.13), g.add(g.mul(b, 0.42), 0.31), A, B, 1.1, stretch=3.2)
        if not s:
            raise RuntimeError('weathered_brown_planks unavailable')
        col = g.grade(s['color'], s['mean'], target, 1.25, sat=0.9)
        n, _ = g.noise(g.vec(g.mul(a, 1.2), g.mul(b, 22.0), 0.0), 1.0, detail=3.0, rough=0.6)      # long fibres
        ck, _ = g.noise(g.vec(g.mul(a, 2.0), g.mul(b, 55.0), 3.0), 1.0, detail=2.0, rough=0.5)     # checks
        check = g.sub(1.0, g.ss(g.absf(g.sub(ck, 0.5)), 0.0, 0.018))
        fac, _ = g.noise(g.vec(g.mul(a, 9.0), g.mul(b, 14.0), 7.0), 1.0, detail=1.0)               # adze facets
        col = g.vscale(col, g.mul(g.remap(n, 0.3, 0.7, 0.85, 1.15), g.lerp(1.0, 0.5, check)))
        height = g.add(g.add(g.mul(n, 0.5), g.mul(fac, 0.7)), g.mul(check, -1.0))
        nrm = g.normal(s['pert'], 1.2, height=height, dist=0.004)
        return _out(g, g.bsdf(col, g.rough_from(s, 0.82, 0.3, lo=0.6), 0.0, nrm))
    return _make('beam', build, (target, 0.85))


# -------------------------------------------------------------------------------------- metal
NICKEL = '#c3c1bc'


def nickel():
    """Brushed nickel: a warm silver, satin, with a fine brushed break-up of the highlight."""
    def build(g, P):
        fr = g.frame()
        n1, _ = g.noise(fr['P'], 18.0, detail=3.0)
        n2, _ = g.noise(g.vec(g.mul(fr['px'], 900.0), g.mul(fr['py'], 900.0), g.mul(fr['pz'], 40.0)), 1.0, detail=2.0)
        col = g.vscale(hexlin(NICKEL), g.remap(n1, 0.3, 0.7, 0.95, 1.04))
        rough = g.add(0.3, g.add(g.mul(g.sub(n1, 0.5), 0.1), g.mul(g.sub(n2, 0.5), 0.1)))
        return _out(g, g.bsdf(col, rough, 1.0, None))
    return _make('nickel', build, (hexlin(NICKEL), 0.32, 1.0))


def _thin_glass(name, tint):
    """Thin-pane glass PFX+name (bl/materials.thin_glass: never refractive); the library's clear glass if that fails."""
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m is not None:
        return m
    from .. import materials
    try:
        return materials.thin_glass(full, tint=tint)
    except Exception as e:  # pragma: no cover
        print(f'[baths_primary] material {full} fallback: {e!r}')
        return materials.get('glass_clear')


def glass():
    """Low-iron (extra-clear) tempered glass of the shower screen (seventh round). The house's window glass
    (`glass_clear`) takes about 6 % more red than green out of the light at every pane, which is right for a window
    but turns white tile behind a shower screen pale aqua: a white bath is glazed with low-iron glass for exactly
    that reason. Neutral, 1 % absorption per face. (The name keeps 'glass': bake_web.py exports it as a pane.)"""
    return _thin_glass('glass_low_iron', (0.99, 0.99, 0.99))


def glass_edge():
    """The polished edge of the low-iron glass: a pale grey-blue line, not the bottle green of ordinary float glass."""
    return _thin_glass('glass_low_iron_edge', (0.80, 0.85, 0.87))


def galvanised():
    """Dull hot-dip zinc with its spangle (plant pot)."""
    def build(g, P):
        fr = g.frame()
        d = g.voronoi(fr['P'], 55.0).outputs['Distance']
        n, _ = g.noise(fr['P'], 30.0, detail=3.0)
        col = g.vscale(hexlin('#8f918f'), g.mul(g.remap(d, 0.0, 0.6, 0.82, 1.1), g.remap(n, 0.3, 0.7, 0.92, 1.06)))
        rough = g.add(0.48, g.mul(g.sub(n, 0.5), 0.2))
        return _out(g, g.bsdf(col, rough, 0.85, None))
    return _make('galvanised', build, (hexlin('#8f918f'), 0.5, 0.85))


# ----------------------------------------------------------------------------------- lamps
def enamel():
    """Cream vitreous enamel on steel (lamp shades): glossy, slightly uneven, a darker rolled rim comes from the
    geometry."""
    def build(g, P):
        fr = g.frame()
        n, _ = g.noise(fr['P'], 14.0, detail=2.0)
        col = g.vscale(hexlin('#e9e2d0'), g.remap(n, 0.3, 0.7, 0.97, 1.02))
        nrm = g.normal(height=n, dist=0.0006)
        return _out(g, g.bsdf(col, 0.16, 0.0, nrm, **{'Coat Weight': 0.6, 'Coat Roughness': 0.05}))
    return _make('enamel', build, (hexlin('#e9e2d0'), 0.18))


def bulb():
    """Clear lamp-bulb glass: thin-glass shader (never refractive), a touch warm."""
    name = PFX + 'bulb'
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    try:
        from .. import materials
        return materials.thin_glass(name, tint=(1.0, 0.97, 0.92), f0=0.05)
    except Exception:
        return _flat(name, (0.9, 0.88, 0.82), 0.05)


# ------------------------------------------------------------------------------------- textiles
def jute():
    """Flat-woven cotton / jute mat: natural cream, pairs of thin charcoal stripes across it every 7in, a coarse
    weave (Poly Haven hessian_230)."""
    target = hexlin('#cbbd9f')

    def build(g, P):
        s = g.tri('hessian_230', 0.16, '1k')
        fr = g.frame()
        n, _ = g.noise(fr['P'], 3.0, detail=3.0)
        if s:
            col = g.grade(s['color'], s['mean'], target, 1.2, sat=0.6)
            pert = s['pert']
        else:
            col, pert = target, None
        wv = g.f('SINE', g.mul(fr['py'], 2 * math.pi / 0.016))                    # weft rows
        col = g.vscale(col, g.mul(g.remap(n, 0.3, 0.7, 0.94, 1.05), g.remap(wv, -1.0, 1.0, 0.9, 1.04)))
        t = g.fract(g.div(fr['px'], 7.0 * IN))                                    # stripes across the mat's length
        st = g.mx(g.sub(1.0, g.ss(g.absf(g.sub(t, 0.42)), 0.022, 0.03)), g.sub(1.0, g.ss(g.absf(g.sub(t, 0.58)), 0.022, 0.03)))
        col = g.cmix(col, hexlin('#4a463d'), g.mul(st, 0.85))
        nrm = g.normal(pert, 1.2, height=g.mad(wv, 0.5, 0.5), dist=0.002, bump=0.7)
        return _out(g, g.bsdf(col, 0.95, 0.0, nrm, **{'Sheen Weight': 0.35, 'Sheen Roughness': 0.5}))
    return _make('jute', build, (target, 0.95))


def fringe():
    return flat('fringe', '#d3c6aa', 0.95)


def striped(name='striped', base='#b5a98a', stripe='#3f3e36', pitch_in=1.5, duty=0.36, axis='z'):
    """Terry towel with woven stripes: `stripe` bands of `duty` x `pitch_in` every pitch_in inches along world
    `axis` ('z' = up the hanging towel, 'x' / 'y' = across a folded one, Blender axes)."""
    def build(g, P):
        fr = g.frame()
        p = {'x': fr['px'], 'y': fr['py'], 'z': fr['pz']}[axis]
        t = g.fract(g.div(p, pitch_in * IN))
        band = g.mul(g.ss(t, 0.5 - duty / 2 - 0.03, 0.5 - duty / 2 + 0.03),
                     g.sub(1.0, g.ss(t, 0.5 + duty / 2 - 0.03, 0.5 + duty / 2 + 0.03)))
        n1, _ = g.noise(fr['P'], 330.0, detail=3.0, rough=0.6)                    # pile
        n2, _ = g.noise(fr['P'], 28.0, detail=2.0)
        col = g.cmix(hexlin(base), hexlin(stripe), band)
        col = g.vscale(col, g.remap(n2, 0.3, 0.7, 0.93, 1.04))
        nrm = g.normal(height=g.add(n1, g.mul(band, 0.4)), dist=0.002, bump=0.6)
        return _out(g, g.bsdf(col, 1.0, 0.0, nrm, **{'Sheen Weight': 0.8, 'Sheen Roughness': 0.45}))
    return _make(name, build, (hexlin(base), 1.0))


# --------------------------------------------------------------------------------------- plants
def cactus():
    """Barrel cactus skin: dull grey-green, paler on the rib crests where the spines sit (the ribs' crests face
    outward; 'pointiness' is not available without bevel, so the tone follows a fine noise)."""
    def build(g, P):
        fr = g.frame()
        n, _ = g.noise(fr['P'], 26.0, detail=3.0)
        sp, _ = g.noise(fr['P'], 420.0, detail=1.0)
        col = g.vscale(hexlin('#6e7b5c'), g.remap(n, 0.3, 0.7, 0.85, 1.12))
        col = g.cmix(col, hexlin('#c9c2a4'), g.mul(g.ss(sp, 0.62, 0.7), 0.7))     # spine clusters
        nrm = g.normal(height=sp, dist=0.0015)
        return _out(g, g.bsdf(col, 0.7, 0.0, nrm))
    return _make('cactus', build, (hexlin('#6e7b5c'), 0.7))


def sedum():
    return flat('sedum', '#8e9c7a', 0.55, Subsurface_Weight=0.15)


# ------------------------------------------------------------------------------------ the print
def botanical(w=300, h=390, seed=5):
    """A small botanical drawing for the framed print on the shelf: three sprigs in grey-green and sepia ink on
    cream paper, generated with numpy (no third-party image). Mapped with the object's generated coordinates
    (the print is a thin box: its two long axes)."""
    name = PFX + 'botanical'
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    import numpy as np
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    paper = np.array([0.90, 0.86, 0.76], np.float32)
    img = np.ones((h, w, 3), np.float32) * paper
    img *= (1.0 + 0.03 * (rng.random((h, w, 1)).astype(np.float32) - 0.5))

    def ink(mask, col, k=0.9):
        nonlocal img
        img = img * (1 - k * mask[..., None]) + np.array(col, np.float32) * (k * mask[..., None])

    def seg(x0, y0, x1, y1, wd):
        dx, dy = x1 - x0, y1 - y0
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
        d = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
        return np.clip(wd + 0.6 - d, 0, 1)

    def leaf(cx, cy, ang, ln, wd):
        c, s = math.cos(ang), math.sin(ang)
        u = (xx - cx) * c + (yy - cy) * s
        v = -(xx - cx) * s + (yy - cy) * c
        t = np.clip(u / ln, 0, 1)
        half = wd * np.clip(np.sin(np.pi * t), 0.0, 1.0) ** 0.8
        body = np.clip(half + 0.7 - np.abs(v), 0, 1) * (u > 0) * (u < ln)
        vein = np.clip(0.9 - np.abs(v), 0, 1) * (u > 0) * (u < ln)
        return body, vein
    green, sepia = (0.36, 0.42, 0.30), (0.33, 0.26, 0.18)
    for sx, base_y, top_y, lean in ((0.30, 0.90, 0.20, -0.10), (0.52, 0.92, 0.12, 0.04), (0.74, 0.90, 0.26, 0.12)):
        n = 9
        pts = [(w * (sx + lean * (k / n) ** 1.5), h * (base_y + (top_y - base_y) * k / n)) for k in range(n + 1)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            ink(seg(x0, y0, x1, y1, 0.9), sepia, 0.8)
        for k in range(2, n + 1):
            x0, y0 = pts[k]
            for side in (-1, 1):
                ang = -math.pi / 2 + side * (0.95 - 0.04 * k) + lean
                body, vein = leaf(x0, y0, ang, w * (0.13 - 0.007 * k), w * (0.032 - 0.0015 * k))
                ink(body, green, 0.62)
                ink(vein * body, sepia, 0.35)
    for k in range(5):                                         # a caption line of 'handwriting'
        x0 = w * (0.3 + 0.08 * k)
        ink(seg(x0, h * 0.965, x0 + w * 0.055, h * 0.965, 0.5), sepia, 0.5)
    arr = np.concatenate([np.clip(img, 0, 1), np.ones((h, w, 1), np.float32)], 2)
    im = bpy.data.images.new(name + '_img', w, h, alpha=False)
    im.pixels.foreach_set(np.ascontiguousarray(arr[::-1]).ravel())
    im.pack()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    com = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], com.inputs['X'])            # the print box is built wide along its local x
    nt.links.new(sep.outputs['Z'], com.inputs['Y'])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = im
    tex.extension = 'EXTEND'
    nt.links.new(com.outputs[0], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    m.diffuse_color = (0.9, 0.86, 0.76, 1)
    return m
