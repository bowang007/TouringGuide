# Material library (`bl/materials.py` + `bl/materials_pbr.py`)

`materials.get(key)` is the only entry point room modules use (via `ctx.mat(key)`). `materials._build`
asks `materials_pbr.build(key)` for a textured PBR material first and falls back to the flat
Principled BSDF from `KEYS` if that returns None or raises. Glass keys (`glass_clear`, `glass_frosted`,
`glass_picture`) always use `materials.thin_glass()`: no refraction, so sun and shadow rays pass through.

- `TG_FLAT_MATERIALS=1` forces the flat fallback, which is useful for fast layout checks.
- Each material is named `M_<key>` and is built once per .blend.
- `materials_pbr` never raises at import time. If a texture download fails, the affected key falls back
  to a procedural-only version.

## Mapping (no UVs anywhere)

All patterns are driven by world-space position in metres (`Geometry.Position` and `Geometry.Normal`), so
neighbouring objects (floor slabs, wall pieces, cabinet fronts) continue seamlessly.

| Mapping | Used for | How |
|---|---|---|
| **planar** | Oriented patterns: boards, tiles, flutes, grain, roof seams, brushed steel | Vertical faces use `a` = position along the face's horizontal tangent `T = normalize(cross(Z, N))` and `b` = height `z`. Horizontal faces use world `(x, y)`. Boards, tiles and grain therefore stay correctly oriented on walls of **any** rotation. Tile rows start at the floor (`z = 0`). |
| **triplanar** | Isotropic textures: fabrics, stucco, plaster, concrete, gravel, grass | Three world-axis projections blended by \|N\|^8. |
| **object** | `stone_feature` only | Object-space coordinates, so the book-match mirror seam sits on the object's origin. |

Normal maps are applied as world-space perturbations along each projection's axes, so no tangents are
needed. Procedural relief (board grooves, grout, flutes, waves, seams) is chained in with a `Bump` node.
There is no true displacement.

Each Poly Haven diffuse map is **graded to the KEYS colour**. It is divided by the map's measured mean
(cached in `tg_stats.json` next to the maps) and multiplied by the target. An optional per-channel
contrast (gamma on the ratio) and saturation are then applied. The KEYS palette therefore stays exact,
and the texture adds only its real variation.

### Per-object knob

`ob['tg_grain'] = 1` rotates the wood grain 90° on **horizontal** faces. By default, grain on tops and
bottoms runs along world X (SCENE x, east-west); set the knob on shelves and tops that run north-south.

It applies to `walnut_slab`, `walnut_door`, `white_oak_veneer`, `fence_charcoal` and the planar
textured keys. Vertical faces always follow the face.

## Keys

All sizes are real-world. PH = Poly Haven texture id (CC0). Textures are 2k unless noted.

| Key | Source | Scale / pattern | Notes |
|---|---|---|---|
| `paint_wall` | procedural | orange-peel bump: ~3 mm noise, 0.12 mm deep | KEYS colour ±1% low-frequency tone; roughness ±0.035 |
| `paint_ceiling` | procedural | same, peel 0.7 | flat (0.92) |
| `paint_trim`, `door_slab` | procedural | same, peel 0.8 / 0.6 | satin (0.45 / 0.42) |
| `paint_black`, `fascia_charcoal` | procedural | same | |
| `plaster_white` | PH `plastered_wall_04` | 3.2 m, triplanar | soft trowel mottling (contrast 0.5) |
| `stucco` | PH `white_stucco` | 2.0 m, triplanar | smooth sand finish |
| `wood_cladding` | PH `ash_veneer` (68% of boards) + `teak_veneer` (32%) | vertical 5 in boards, 3.2–4.8 m long, 3 mm dark shadow gaps | Natural grey cedar / thermo-ash like 1077 W McKinley: graded to #9b8268 at saturation 0.6–0.65, so it stays a soft grey-beige in full sun (no orange). Per-board random texture offset, ±11% tone and slight warmth; grain along the board (texture stretched 1.6×). |
| `roof_metal` | procedural | standing seams every 16 in **down-slope** on every roof plane | Seam coordinate = `dot(P, normalize(cross(Z, N)))`, i.e. along the eave. 20 mm raised-seam bump with a lighter folded top and darker crease, faint pencil ribs, ±6% per-panel tone. Matte PVDF paint film: metallic 0.08, roughness 0.58 ± chalky variation (0.48 on the seam tops), specular 0.4, so grazing views read as matte charcoal metal, not a glass mirror. Near-flat faces (\|Nz\| > 0.985) take seams along world X. |
| `black_aluminum` | procedural | fine powder-coat stipple | roughness 0.42, metallic 0.15 |
| `glass_clear`, `glass_frosted` | `materials.thin_glass()` | – | two-sided Schlick, F0 0.04 |
| `glass_picture` | `materials.thin_glass(f0=0.01, grazing=0.55)` | – | Anti-reflective picture-frame glass for framed art: two-sided Schlick with ~1% reflectance at normal incidence and the grazing term cut to 55%, near-neutral tint, glossy roughness 0.02. Camera and shadow rays pass straight through (like `thin_glass`), so the art stays lit and the pane does not mirror the windows. Use it as a 1–3 mm pane just in front of the art. |
| `oak_floor` | PH `oak_veneer_03` / `silver_oak_veneer_01`, chosen per board | 9 in boards running N-S (Blender Y), 1.22–2.09 m (4–7 ft) long with staggered ends | See [oak_floor in detail](#oak_floor-in-detail). |
| `tile_floor_bath` | PH `plastered_wall_04`, per-tile offset | 48 × 24 in, 1/3 running bond, 1/16 in grout | honed warm grey (0.5); faint speckle; ±3% per-tile tone |
| `tile_shower_floor` | procedural | 2 × 2 in mosaic, 1/8 in grout | ±6% per-tile tone, pillowed edges |
| `concrete_garage` | PH `concrete_floor_02` | 2 m, triplanar, contrast 0.22 | sealed: coat 0.25 |
| `porch_pavers` | PH `concrete_floor_02`, per-paver offset | 24 × 24 in, ~3/8 in dark joints, arris bevel | Grid is centred on the recessed porch (SCENE x 14.07–20.69, z 47.0–51.4). |
| `concrete_drive` | PH `brushed_concrete_03` | 2 m, planar | broom lines run E-W (world X), across a N-S driveway |
| `foundation`, `concrete_paver` | PH `concrete_floor_02` | 2 m, triplanar, low contrast | |
| `walnut_slab` | PH `american_walnut_veneer` | 1 m, **horizontal** grain | Graded to #6b4a30 at contrast 1.6, satin coat 0.2. Grain flows continuously across adjacent fronts (grain-matched). |
| `walnut_door` | PH `walnut_veneer` | 1.8 m, **vertical** grain (cathedrals) | coat 0.2 |
| `white_oak_veneer` | PH `oak_veneer_03` | 1 m, horizontal grain (stretched 1.3×) | |
| `quartz_calacatta` | procedural | 3D world space, main veins ~0.7 m apart | See [quartz_calacatta in detail](#quartz_calacatta-in-detail). Roughness 0.10 (+0.03 in the veins). |
| `quartz_white` | procedural | fine speckle | roughness 0.18 |
| `stone_feature` | procedural, **object space** | book-matched slabs 1.5 m wide, mirrored at the object's origin and every 1.5 m either side | Polished green onyx. See [stone_feature in detail](#stone_feature-in-detail). |
| `tile_wave_white` | procedural | 24 × 12 in, half offset, wavy rib relief (λ ≈ 7 cm, 12 mm bump) | glossy glaze (coat) |
| `tile_wall_porcelain` | procedural | 48 × 24 in stacked, 1/16 in grout, micro-bevel | Marble-look print: the `quartz_calacatta` vein model at 75% contrast with softer greys. Every tile is a different face of the print (random offset into the field and a random left/right mirror, so vein directions alternate and nothing repeats tile to tile). Roughness 0.24. |
| `tile_fluted_black` | procedural | 12 × 24 in tiles, 10 half-round flutes per tile (1.2 in pitch, joints in the valleys) | ±10% per-tile tone, satin glaze |
| `stainless` | procedural | brushed lines along the face's horizontal | anisotropic 0.55, tangent = horizontal; roughness 0.26 ± lines; faint smudges |
| `black_metal` | procedural | powder stipple | metallic 0.5, roughness 0.4 |
| `chrome`, `mirror` | flat | – | roughness 0.05 / 0.0 |
| `ceramic_white` | flat | – | roughness 0.07 + clear coat 0.3 |
| `led_warm` | blackbody 3000 K | – | emission strength 8 |
| `fabric_boucle` | PH `curly_teddy_natural` (1k) | 0.33 m, triplanar | curly loop normal, sheen 0.35 |
| `fabric_linen_white`, `fabric_linen_grey`, `fabric_sage` | PH `rough_linen` (1k) | 0.27 m, triplanar | desaturated and re-coloured to KEYS; sheen 0.25–0.3 |
| `fabric_mustard` | PH `velour_velvet` (1k) | 0.28 m | velvet sheen 1.0 |
| `leather_tan` | PH `brown_leather` (1k) | 0.5 m | low-contrast grade (tan), grain normal, coat 0.15 |
| `rug_wool_cream`, `rug_wool_grey` | PH `hessian_230` (1k) | 0.42 m | Loop-weave normal, flecks and fuzz bump, sheen 0.6, roughness 0.97. |
| `grass_lawn` | PH `leafy_grass` | 2 m, triplanar | Large-scale yellow-green patches. Use real blades near cameras. |
| `gravel_dark` | PH `gravel_stones` | 2 m | |
| `pebbles_river` | PH `dry_river_pebbles` | 2 m | desaturated to grey |
| `soil_mulch` | PH `wood_chips` | 2 m | |
| `ipe_deck` | PH `sapele_veneer` | 5.5 in boards with 1/4 in open gaps, 2.6–4.8 m long | Boards run along the face (world X on horizontal decks). Per-board tone. |
| `fence_charcoal` | PH `ash_veneer` (normal + 35% luminance) | grain along the face | painted charcoal, roughness 0.62 |

### `oak_floor` in detail

- **Board layout.** The board columns are 9 in wide and run north-south (Blender Y). Each column is cut
  into segments 2.9–3.6 m long, with a random offset per column. Each segment is split once at 42–58%,
  which gives boards 1.22–2.09 m (4–7 ft) long with staggered ends.
- **Grain.** Each board samples one of the two veneers at a random offset, with the texture stretched
  1.7× along the grain. No two boards repeat.
- **Colour.** The veneer is graded to #d9c4a3 at contrast 1.45, with a slight oil warmth. Each board
  then varies by ±4% in tone and a little in warmth.
- **Joints.** A 1.6 mm micro-bevel groove with gap darkening runs around every board.
- **Finish.** Matte oil: roughness 0.5 ± the roughness map ± 0.04 per board. A soft grazing sheen
  comes from a clear coat (weight 0.12, roughness 0.32).

### `quartz_calacatta` in detail

Veins are drawn from **flow fields**, never from iso-lines of isotropic noise, so they cannot close into
loops or form a crackle network.

- **Flow field.** `w = dot(P, D) + fractal domain warp + slow metre-scale bend`, with `D = (-0.55, 0.8, 0.75)`
  in Blender world space. Its level sets are warped, roughly parallel sheets. The veins therefore flow
  diagonally on tops and on walls of any orientation. Because the field is 3D, the veins run continuously
  over every edge. On the kitchen island, they flow over the east mitre and book-match (mirror) at the west
  mitre. The warp gradient is kept below `|D|` projected on every face, so `w` has no local extrema and
  there are no closed loops.
- **Vein placement.** Veins are the edges of a 1D Voronoi partition of `w`, so they have irregular,
  never-repeating spacing and an exact distance-to-vein. Each vein draws a random strength from its edge
  id: some are bold, some medium and some only ghost drifts. A 3D noise along its length tapers the width
  (0.1–1.5×) and fades it in and out.
- **Main veins** (~0.72 m apart). Each has a soft darker core (2–13 mm) that braids into two strands and
  merges again, a 1–4 cm feathered body, and a 6–15 cm cloudy halo. About a third of the halos are
  gold-taupe (Calacatta gold).
- **Secondary veins.** These run at ~30° to the main ones, are thinner and shorter, and fade out, so they
  read as branches. **Hairlines** (0.3–1 mm) wander between them.
- **Finish.** Faint 2–3% clouding, a fine speckle, and roughness 0.10.

### `stone_feature` in detail

- **Look.** Polished, book-matched green onyx. The slabs show flowing layered bands of green-grey, sage,
  cream and taupe, milky translucent drifts, and soft gold-rust veins that follow the bands.
- **Flow.** The bands are the level sets of an object-space flow field. They rise about 12° away from the
  seam and undulate strongly through a 6-octave warp plus a slow bend. The mirror therefore forms a soft,
  organic figure rather than a hard chevron.
- **Bands.** Band tone comes from fractal 1D noise of the flow coordinate, so bands have irregular widths
  and never repeat. A large-scale cloud is added on top. Fine laminations appear only in patches, and a
  colour ramp maps the result from deep green-grey through sage to cream. Some bands are warmed to taupe.
- **Veins.** The veins are 1D-Voronoi edges of a slightly perturbed copy of the same flow coordinate, so
  they run along the layers and drift gently across them. Each has a rust or gold core (1–5 mm), a soft
  gold halo, and is tapered and faded along its length. A few faint, short cross veins (healed fractures)
  are added. There is no crackle network and there are no dark pools.
- **Seams.** A hairline joint marks each book-match seam.
- **Finish.** Polished: roughness 0.16 (up to 0.30 in the veins), plus a clear coat (weight 0.5,
  roughness 0.05) for depth.
- **Modelling.** Give the feature wall a single object whose origin is at the wall centre. The pattern is
  mirrored at the origin, and again every 1.5 m either side.

## Texture memory

All 51 keys loaded in one scene use 60 image maps, about 0.78 GB worst case if every map is stored
uncompressed as 4-channel bytes. Each 2k texture takes 3 maps (diffuse, roughness, normal); fabrics are
1k. Only the materials actually used in a scene are uploaded to the GPU.

## Validation

- **Swatch board.** `tools/render/.cache/materials/swatches.png` has one tile per key under the
  pipeline daylight, with a 12 in black ruler bar in each tile.
- **Shell renders.** The shell was built with the library (`build_scene.py --zones none`) and rendered at
  L0, K0, A0, B3 and E0, plus close-up and exterior views. The output is in
  `tools/render/.cache/dev_materials/`.

## Known limitations

- Relief is bump-only. Flutes, waves and roof seams don't self-shadow or change the silhouette.
- Planar mapping on **vertical cylinders** collapses the along-face coordinate. Grain and tiles become
  straight bands around the cylinder. This is harmless for horizontal-grain wood, but prefer triplanar
  keys (stone, fabric, paint, metals) for round objects.
- Tile and paver joints align to the world origin, not to room edges. The exception is the porch pavers,
  which are centred on the porch.
- `stone_feature` mirrors about each object's own origin. A wall built from several objects therefore
  shows several book-match centres.
