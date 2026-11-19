# Render pipeline: path-traced tour and baked real-time model

This folder turns the tour's measured model (`data/scene.json`, frozen from `index.html`) into:

| Output | Script | Used by the site as |
|---|---|---|
| 27 path-traced 360° panoramas (4096×2048) | `render_panos.py` | Styled Tour (`assets/panos/`, via `tools/web/publish_panos.py`) |
| Perspective hero stills | `render_heroes.py` | Front page and Design window images (`assets/design/`) |
| 32 path-traced exterior orbit frames (3000×2000) | `render_exterior.py` | Photoreal Exterior view (`assets/exterior/`, via `tools/web/publish_exterior.py`) |
| Lightmapped web model (GLB + walk collision) | `bake_web.py` | Dollhouse / 3D Walk / Floor plan / Exterior (`assets/model/`, drawn by `assets/js/house3d.js`) |
| Walk eye adaptation (`adapt.json`) | `adapt_web.py` | Per-stop exposure / white balance for the 3D walk |

The architecture and every dimension come 1:1 from the original model. Only the design changes:
finishes, fixtures, furniture, lighting and landscape follow the modern language of the neighbouring
new build at 1077 W McKinley Ave. `DESIGN.md` is the design brief and the code contract;
`bl/MATERIALS.md` documents the material library.

## Requirements

* **Blender 5.2 LTS.** Cycles uses an NVIDIA GPU through OptiX; the CPU works but is slow. Set `BLENDER=/path/to/blender`.
* **Internet on the first build.** CC0 textures, models and the sky HDRI are fetched from Poly Haven
  into `.cache/polyhaven/`; `ASSETS.md` lists them.
* **Python 3 with numpy and Pillow** for review sheets and publishing. One way to get it:
  `python3 -m venv .cache/venv && .cache/venv/bin/pip install numpy pillow`.

Everything generated goes to `tools/render/.cache/` (git-ignored).

## Full run

```bash
export BLENDER=/path/to/blender
cd tools/render
# 1. build the scene (~25 s; downloads assets the first time)
$BLENDER -b --factory-startup --python build_scene.py -- --zones all --strict --out .cache/house.blend
# 2. path-trace the 27 stops (4096x2048, adaptive up to 768 spp, OptiX denoised)
$BLENDER -b .cache/house.blend --python render_panos.py -- --nodes all --width 4096 --samples 768 --out .cache/panos
# 3. publish into the site (full WebP + 2k rung + thumbnails + manifest with offset 0)
.cache/venv/bin/python ../web/publish_panos.py .cache/panos
# 4. hero stills for the design window
$BLENDER -b .cache/house.blend --python render_heroes.py -- --width 2400 --samples 1024 --out .cache/heroes
# 5. bake the real-time model (reads .cache/panos/render_meta.json for the house-wide exposure/white balance)
$BLENDER -b .cache/house.blend --python bake_web.py -- --out ../../assets/model/house.glb
# 6. per-stop eye adaptation for the 3D walk (a few seconds)
$BLENDER -b .cache/house.blend --python adapt_web.py -- --out ../../assets/model/adapt.json
# 7. exterior orbit frames (~30 s each), then publish them
$BLENDER -b .cache/house.blend --python render_exterior.py -- --width 3000 --samples 512 --out .cache/exterior
.cache/venv/bin/python ../web/publish_exterior.py .cache/exterior
```

`final_run.sh [width] [samples]` runs steps 1, 2, 4–6 and the exterior frames of step 7 into `.cache/` (about two hours at 4096 px /
768 spp on one RTX-class GPU); publish with the commands at the top of the script.

Bump `HOUSE_VERSION` in `index.html` when you publish a new model, so browsers don't serve a cached copy.

## Architect's plan and the owner's changes

The tour now follows the architect's floor plan (`sizes/sizes.pdf`, sheet SKA002, Option A). It has
the same rooms in the same arrangement as the earlier concept model, but different sizes.

* **`relayout.py`:** maps every concept-plan coordinate onto the plan's clear dimensions, region
  by region. Its breakpoints are the wall faces.
* **`apply_relayout.py`:** converted the web tour's `SCENE` and `MEASUREMENTS`, together with
  `data/`. It is a one-off and refuses to run twice.
* **Blender build:** it still reads the concept data (`data/concept/`), because the room modules
  are written against it. After the zones are built, `bl/warp.py` carries the house onto the new
  plan with the same map:
  * architecture and fitted pieces are reshaped;
  * loose furniture moves in clusters and keeps its size;
  * flat slabs follow the rooms on each side.

  The exterior zone is built directly on the new site plan and is not warped.
* **`bl/revisions.py`:** applies the owner's changes on the new plan. The positions live in
  `bl/revision_spec.py`. `apply_revisions_web.py` records the same changes in the web data.
  * Bedroom 4: flat ceiling.
  * Front bedroom: bay glazed to the floor.
  * Foyer: two skylights.
  * Primary bedroom: sliding door to the garden.
  * Bedroom 2: floor-to-ceiling window.
  * Primary bath: floor-to-ceiling obscured window.
  * Kitchen: skylight on the east roof plane.

  The dining table in line with the island is built by the kitchen zone.
* **`tools/web/dimension_plan.py`:** redraws the Dimensions sheet from `SCENE` and `MEASUREMENTS`.

## How the look is controlled

* **Daylight.** A Poly Haven sky HDRI with its own sun clamped out, plus a sun lamp (late-morning,
  south-east). Window portals help interiors converge. Constants are in `bl/lighting.py`.
* **Light balance.** `lighting.apply_balance()` runs in every render script and scales the built
  scene at render time:
  * fixture lamps ×0.12;
  * emission shaders ×0.4;
  * sky ×2 and sun ×2.

  The result is daylight-led, with the lights visibly on (a listing-photo look). Override per run with
  `--interior-gain / --emission-gain / --sky-gain / --sun-gain`.
* **Exposure and white balance per stop.** A 512×256 probe sets the exposure: the median luminance of the
  horizon band maps to `TARGET_MEDIAN`. White painted surfaces (walls, ceilings, trim, white doors, stucco)
  are masked with a one-off emission-swap render. Their median chromaticity (counted per pixel, so hot
  pools under downlights don't dominate) is brought to `WB_TARGET`, a slightly warm white, as a
  photographer would. The values are written to `render_meta.json`.
  `--wb 6000,-10` forces a fixed balance.
* **Colour pipeline.** AgX with the Base Contrast look. The web bake reuses the median exposure and white
  balance of the panoramas, so the 3D model matches the 360s.

## Web model contract (`bake_web.py`)

The model is grouped by visibility class and plan region, one GLB node per group, with
`extras.tg_class` set to one of:

| `tg_class` | Contents | Visibility |
|---|---|---|
| `base` | Floors and built-ins | Always visible |
| `wall` | Walls, trim, windows, doors | Clipped at 2.1 ft in cutaway |
| `glass` | Glazing | Clipped at 2.1 ft in cutaway |
| `furniture` | Furniture | Furniture toggle |
| `decor_high` | High decor | Hidden in cutaway; furniture toggle |
| `ceiling` | Ceilings | Walk mode only |
| `exterior` | Roof and facade | Exterior mode only |
| `landscape` | Garden and site | Garden toggle |

* **Lighting** is the full Cycles result (GI, soft shadows, materials), baked into per-group
  atlases. It is saved display-referred and shown unlit by three.js.
* **Compression:** Draco geometry and WebP textures.
* **Collision:** `collision.json` holds furniture footprints for walking. Boxes that would block a
  tour stop or edge are dropped and reported.
* **Metals:** a bake records diffuse light only, so for the bake each metal gets its diffuse
  equivalent (base colour, metallic 0). Mirrors and polished chrome get a mid silver-grey, so they
  don't come out black.
* **Eye adaptation:** the bake uses one interior exposure and white balance (the median of the stops).
  `adapt_web.py` stores, per stop, the per-channel gain `k` of the highlight-preserving curve
  `k·x / (1 + (k−1)·x)` that maps the bake's look to that stop's panorama look. In walk mode the page
  eases towards the nearest visible stop's `k`, like a camera's auto exposure, so dim bedrooms and
  baths match their panoramas.
* **Not baked:** vegetation, which is skipped.

## Photoreal 3D walk (page side)

In walk mode the page projects the path-traced panoramas themselves onto this model
(`assets/js/house3d.js`: `setPanorama`, `setProjection`), the way Matterport-style tours do:

* **On a stop** the view is that stop's 4K panorama, pixel for pixel, lined up with the geometry.
  It matches the 360° viewer to within texture filtering.
* **Between stops** the two nearest stops in view are blended on the geometry, weighted by
  inverse squared distance. A depth cube rendered from each stop (from this GLB) rejects surfaces
  that stop cannot see. Those fall back to the other stop's panorama, then to the bake with eye
  adaptation. Only occluders inside the house footprint count, because planting and fences
  outside are simplified in the model. The sky and anything without geometry show the panoramas
  at infinity.
* **Loading:** 2k panoramas while moving, the 4K file once you stand on a stop, and neighbours
  prefetched. Panorama textures and depth cubes are cached (six of each). Depth cubes are
  1024² on desktops and 512² on touch and low-memory devices.
* **Opt-out:** `?walk=model` shows the baked model alone. Hiding furniture also turns the
  projection off, because the panoramas contain the furniture.
* **Exterior frames:** the same engine takes perspective frames (`setPanorama(..., frame)` with the
  frame camera's projection × view matrix); see "Photoreal exterior" above.

The projection needs the stops to match the render cameras exactly. `render_panos.py` places
each equirectangular camera at the stop's `p` (eye height included), with yaw 0 = −z, so a
re-render keeps them aligned.

## Photoreal exterior (orbit frames)

The Exterior view orbits a fixed target. `render_exterior.py` renders perspective frames from orbit
positions the page can reach exactly:

* **Rings:** 24 frames at drone height (~50 ft, every 15°) and 8 roof-overview frames (~95 ft, every 45°).
* **Framing:** 90° horizontal, 3:2. That is wider than any screen, so a window of any shape is a crop
  of the frame.
* **Look:** one shared exposure and white balance, so neighbouring frames blend without a step.

The page projects them onto the baked model, like the walk (below), with these differences:

* **Settling:** the camera settles on the nearest frame when you let go; a short drag moves one frame
  that way.
* **Zoom:** zoom narrows the field of view from the frame position, so the view stays exact.
* **Occluders:** every occluder counts outside, and the depth cubes reach 700 ft.
* **Double-sided neighbourhood:** the neighbours' houses in the web model are partly inside out.
  Cycles renders both sides, so the bake never showed it. The Exterior view therefore draws the
  `landscape` class double-sided.

`?exterior=model` shows the baked model alone, and so does hiding the garden.

From the air the whole neighbourhood is in view. `bl/zones/exterior_far.py` fills it out:

* **Streets:** parallel streets every 219 ft, laid out like the aerial photo of the street
  (`assets/references/img-3202.webp`), cross streets, and street trees.
* **Lots:** about 1,250 ranch lots with houses, driveways, fences, backyard trees and the odd pool.
* **Horizon:** a tree belt to the horizon and the hills around the valley.

It lives in the `ext_far` collection, excluded from the view layer. Only `render_exterior.py`
switches it on, so the panoramas, hero stills and the web bake are unchanged.

The neighbouring houses' roof colours follow the aerial photo (`NEIGHBOUR_ROOFS` in
`exterior_context.py`): red-brown next door to the east, grey to the west, orange-tan behind.

## Review tools

| Tool | Purpose |
|---|---|
| `review.sh <blend> <nodes\|all> <out> [width] [samples] [render args]` | Renders panoramas and 4-view contact sheets (`<ID>_sheet.png`) |
| `dev_preview.sh <zones> <nodes>` | Builds only some zones, then review renders |
| `top_view.py -- --rect=x0,x1,z0,z1 --out top.png` | Orthographic plan check (ceilings/roof hidden) |
| `whatis.py -- --node K0 --at y=90,p=-10` | Names the object, material and owning zone at a view direction |
| `pano_views.py PANO --base-yaw R --yaws 0,90` | Cuts rectilinear views out of an equirect |
| `check_glb.py <glb> <out.png> [hide] [view]` | Quick unlit render of a baked GLB |
| `gpu.sh <blender args>` | Runs a Blender GPU job under a machine-wide lock (parallel agents/scripts) |

## Files

* **`bl/` modules:**
  * `common.py`: scene context and geometry helpers.
  * `shell.py`: exact architecture with modern finishes.
  * `lighting.py`: sky, sun, portals, fixtures and balance.
  * `materials.py` + `materials_pbr.py`: material library (`KEYS` contract).
  * `assets.py`: Poly Haven fetch, cache and attribution.
  * `zones/<zone>*.py`: one module family per area (kitchen_dining, living, primary_suite, bedrooms, baths,
    hall_entry_garage, exterior).
* **`data/`:**
  * `scene.json`: the frozen tour model.
  * `measurements.json`, `primitives.json`.
  * `scene_classification.json` + `room_inventory.json`: room regions and roles.
  * `hero_cameras.json`.
* **`extract_scene.py` / `classify_scene.py`:** regenerate `data/` from `index.html`.
* **`final_run.sh`:** the full production run (build, panoramas, hero stills, bake, adaptation).
