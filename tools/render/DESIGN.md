# 1095 W McKinley: modern photoreal restyle (render pipeline contract)

The tour's 27 camera stops are path-traced in Blender/Cycles from the **exact** remodel geometry
(`data/scene.json`, frozen from `index.html`). The architecture (walls, openings, ceilings,
vaults, roof massing, every dimension in the Dimensions panel) is fixed. What changes is the
**design**: finishes, fixtures, furniture, lighting and landscape. The new design language comes
from the neighbouring modern new build at 1077 W McKinley Ave.

## Design language (1077 W McKinley)

- **Light and calm.** Warm-white matte walls, flat white ceilings dotted with small 4" recessed
  LED downlights (warm 3000K), slim linear slot diffusers. No crown moulding and no raised
  panels. Doors are flush white slabs with matte-black levers. Casings are minimal.
- **Floors.** Wide-plank (≈9") light white oak with a matte, natural-oil look, used everywhere
  except wet rooms. Wet rooms get large-format 24×48 warm-grey porcelain.
- **Glazing.** Slim matte-black aluminium frames and big clear panes, with no divided lights.
- **Kitchen.**
  - Cabinetry: flat-slab walnut with horizontal grain and integrated finger-pull channels.
  - Surfaces: white Calacatta-look quartz worktops with a full-height quartz backsplash.
  - Island: waterfall quartz with a walnut base, plus saddle-tan leather counter stools on
    black pedestal bases.
  - Appliances: integrated stainless column fridge, stacked wall ovens and an induction cooktop.
  - Hood: minimal white plaster or integrated.
  - Lighting: a linear LED pendant (or ring pendants) over the island, warm LED strips under
    the uppers and at the toe kick.
- **Living.**
  - A book-matched green-grey stone feature wall (onyx/quartzite with rust-gold veins) around
    a long linear gas fireplace, with a floating walnut hearth/ledge.
  - Seating: a white bouclé or linen sofa with ochre/mustard accent pillows and sculptural
    bouclé lounge chairs.
  - A walnut coffee table on a large cream wool rug.
  - Accents: big abstract art in neutral/ochre/charcoal, a fiddle-leaf fig or olive tree, and
    ceramic vases with dried pampas.
- **Dining.** A walnut or oak table, curved bouclé dining chairs, and a double-ring LED chandelier.
- **Bedrooms.** Upholstered low platform beds in light grey/cream with layered white linen
  bedding and a throw. Cream or white-oak nightstands with ceramic lamps. A soft grey or
  cream rug and one large abstract piece above the bed. Flush ring LED ceiling lights or cans.
- **Bathrooms.**
  - Vanity and mirror: floating walnut vanities with white quartz tops and undermount or
    vessel sinks, plus backlit LED mirrors.
  - Fixtures: matte-black faucets and shower trim, wall-hung or skirted one-piece toilets.
  - Shower: frameless glass, a linear drain, and a recessed niche with an LED strip.
  - Walls: white 3D wave/ribbed tile on the primary bath feature walls, and black fluted or
    large-format marble-look porcelain in the secondary baths.
- **Exterior.**
  - Facade: smooth warm-white stucco with a warm wood (cedar/thermo-ash) cladding accent at the
    recessed entry, charcoal fascia and a charcoal standing-seam roof.
  - Garage door: modern black aluminium with frosted glass.
  - Fence and hardscape: charcoal horizontal slat fences, a broad concrete driveway with grass
    or gravel joints, and large concrete pavers.
  - Back garden: an ipe deck off the living room, a lawn and river-pebble borders.
  - Planting: ornamental grasses and Mediterranean shrubs, plus multi-stem trees (birch, olive,
    crape myrtle).
- **Staging.** Real-estate-listing calm: few, well-chosen objects, nothing cluttered, everything
  touching the floor or wall it rests on. The palette is warm white, oak, walnut, black,
  ochre and sage.

Daylight is a late-morning sun from the south-east plus a physical sky, with the interior lights
on (warm). The renders are white-balanced neutral with a slightly warm tilt, like a listing
photographer's.

## How to build and review

```bash
export BLENDER=/path/to/blender           # Blender 5.2 LTS (Cycles, OptiX on RTX)
tools/render/dev_preview.sh <zones> <nodes> [width] [samples]
#   e.g. tools/render/dev_preview.sh kitchen_dining K0,D0,H2
#   -> tools/render/.cache/dev_kitchen_dining/{K0.png (equirect), K0_sheet.png (4 x 90deg views)}
$BLENDER -b tools/render/.cache/dev_<zone>/scene.blend --python tools/render/top_view.py -- \
    --rect x0,x1,z0,z1 --out top.png          # orthographic plan check, north up
$BLENDER -b --factory-startup --python tools/render/build_scene.py -- --zones all --strict --out .cache/house.blend
$BLENDER -b .cache/house.blend --python tools/render/render_panos.py -- --nodes all --width 4096 --samples 768
```

Look at the `_sheet.png` review images after every change; they are the ground truth. Use
`top_view.py` to check layout, clearances and collisions (write `--rect=x0,...` with `=`), and
`whatis.py` to find which object/zone owns a pixel. `review.sh <blend> <nodes> <out>` renders an already
built scene; every GPU render goes through `gpu.sh` (a lock) so parallel work can't exhaust GPU memory.

Lighting is balanced at render time (`lighting.apply_balance()`: fixture lamps x0.12, emission x0.4,
sky and sun x2) and every stop is auto-exposed and auto-white-balanced, so a fixture that should read
brighter needs a higher built value. `TG_FLAT_MATERIALS=1` swaps the PBR library for flat colours (fast
layout checks); `ob['tg_grain']=1` turns wood grain 90 degrees on horizontal faces (see `bl/MATERIALS.md`).

## Code contract (`bl/`)

| Module | Owner | Purpose |
|---|---|---|
| `common.py` | core | `Ctx` (scene data, lookups, collections, geometry helpers), `ft2bl`, `place`, `world_bbox_ft` |
| `shell.py` | core | Exact architecture with modern finishes. Builds no furniture or fixtures. |
| `lighting.py` | core (exterior zone may tune the sun/sky constants) | Sky and sun, window portals, `can()`, `point_light()`, `emitter()` |
| `materials.py` | materials | `get(key)` library. KEYS are a stable contract. |
| `assets.py` | core | CC0 Poly Haven fetch and cache: `model()`, `texture()`, `hdri()`, `write_manifest()` |
| `zones/<zone>.py` | one zone agent each | `build(ctx) -> dict` that adds everything inside its zone |

Rules:

- **Units.** All `Ctx` helpers take SCENE feet: x runs west→east, y is up, z runs north/garden
  (0) → south/street (~54). `rot` is radians about +Y. Floor is y=0, flat ceilings are at
  y=8.0, and every camera sits at y=5.0853.
- **Collections.** Put every object in `ctx.coll('zone_<zone>')`, or a child of it.
- **Your files only.** Edit only your own `zones/<zone>.py`, plus any helper files under
  `zones/<zone>_*.py`. If you need a change in a core module, explain it in your final report;
  do not edit core files.
- **Materials.** Use `ctx.mat('<key>')` with keys from `materials.KEYS`. Zone-specific custom
  materials (art canvases, a specific fabric) may be built inside your module; name them
  `Z_<zone>_<name>`. Never use refractive glass (Principled transmission or Glass BSDF) for
  windows or shower screens. Use `materials.thin_glass(...)` (or `ctx.mat('glass_clear')`) so
  sunlight is not lost to caustics.
- **No UVs needed.** Textured library materials use world-space box mapping. Imported Poly Haven
  models keep their own UVs and materials.
- **Models.** Use `assets.model(id, res='2k')` and `ctx.link_asset(path)`, then scale and place.
  Check sizes with `world_bbox_ft()`: real furniture has real dimensions (seat 17–18", table
  29–30", counter 36", bar stool seat 24–26", bed top ≈24"). Hide or remove anything you don't
  use. Run `assets.write_manifest()` at the end. Only Poly Haven (CC0) is allowed as a
  third-party source.
- **Procedural modelling.** Real objects have rounded edges: use `bevel=` on `ctx.box(...)`, and
  subdivision for cushions and soft goods. Nothing floats and nothing intersects: rest on y=0 or
  on the surface below, and sit tight against walls.
- **Lights.** Use `lighting.can(ctx, x, z)` for recessed downlights. Space them about 4–5 ft apart
  in a tidy grid aligned to the room, 2–3 ft from walls. Use `lighting.emitter(...)` for LED
  strips, ring pendants and backlit mirrors, and `lighting.point_light` inside lamp shades.
  Keep interior lights plausible; daylight should still dominate.
- **Performance.** Final renders are 4096×2048 at ~768 spp. Prefer instancing (shared mesh data /
  geometry-nodes instances) for grass, leaves and repeated items. Keep each zone under ~2M
  triangles unless it's a hero element.
- **Camera clearance.** Every camera stop must keep at least 1.2 ft of clear space around its
  position (x, z) up to y=6.5. No furniture may swallow a camera.

## Zones

Every zone builds everything inside its regions, using the original scene objects (via
`ctx.find(room=..., role=...)`) as anchors for position and footprint. Original
furniture, decor, fixtures and landscape are **not** imported by the shell; the zone decides
what replaces them.

| Zone module | Regions (`scene_classification` rooms) | Camera stops to review |
|---|---|---|
| `kitchen_dining` | kitchen, dining | K0, D0, H2 (also visible from L2, H3) |
| `living` | living | L0, L1, L2 |
| `primary_suite` | primary, primary_dressing | P0, P1, S0, C0 |
| `bedrooms` | bed2, bed3, bed3_bay, bed4, bed4_closet, suite3_wic | B2, B3, T4, T6, B4, C3 |
| `baths` | ensuite, shared_bath, suite3_bath | A0, A1, A3 |
| `hall_entry_garage` | front_hall, common_hall, garage, porch (inside face of the entry) | E0, H1, GA, H3, T1, T2, T3, G0 |
| `exterior` | everything outside the walls: grounds, garden, deck, fences, driveway, trees, garage door (both faces), exterior lights, distant context | all stops' window views |

Boundaries: living owns the living region north of z=14.5; `kitchen_dining` owns the open area
from z=14.5 southward. Halls own circulation only and leave the room zones alone.
