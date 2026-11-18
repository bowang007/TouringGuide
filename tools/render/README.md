# Render pipeline: path-traced tour and baked real-time model

This folder turns the tour's measured model (`data/scene.json`, frozen from `index.html`) into:

| Output | Script | Used by the site as |
|---|---|---|
| 27 path-traced 360° panoramas (4096×2048) | `render_panos.py` | Styled Tour (`assets/panos/`, via `tools/web/publish_panos.py`) |
| Perspective hero stills | `render_heroes.py` | Design window images (`assets/design/`) |
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
```

`final_run.sh [width] [samples]` runs steps 1, 2 and 4–6 into `.cache/` (about two hours at 4096 px /
768 spp on one RTX-class GPU); publish with the commands at the top of the script.

Bump `HOUSE_VERSION` in `index.html` when you publish a new model, so browsers don't serve a cached copy.

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
