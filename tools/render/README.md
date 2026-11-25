# 1095 W McKinley tour: render pipeline and site

A Matterport-style tour of the proposed remodel, served as a static site (`index.html` + `assets/`).
The visitor stands on **sweeps**: fixed points where a 360° panorama was path-traced in Blender/Cycles.
At rest the screen shows that panorama itself. A move glides to the next sweep while both
panoramas are projected onto a baked model of the house. The same model, seen from outside, is the
dollhouse and the floor plan; the exterior view orbits the house through path-traced frames.

This folder builds everything the site shows from the measured model of the house:

| Output | Script | Published as |
|---|---|---|
| 53 panoramas, 8192×4096 (51 indoor sweeps, the front porch, the rear landing) | `render_panos.py` | `assets/panos/{8k,4k,2k}/<ID>.webp`, `assets/thumbs/`, by `tools/web/publish_panos.py` |
| 10 hero stills (7 used by the page) | `render_heroes.py` | `assets/design/<key>.webp` (landing page, Design sheet), by `tools/web/publish_design.py` |
| 32 exterior orbit frames, 3000×2000 | `render_exterior.py` | `assets/exterior/`, by `tools/web/publish_exterior.py` |
| Baked model (GLB with lightmap atlases) | `bake_web.py` | `assets/model/house.glb`: dollhouse, floor plan, and the surface the panoramas are projected on during a move |
| Tour graph, rooms, dimension schedule, design text, plan drawing, roof drawing | the data tools below | `assets/data/*.json`, `assets/plans/dimension-plan.svg`, `assets/design/roof.svg` |

The architecture and every dimension follow the architect's plan (`sizes/sizes.pdf`, sheet SKA002) plus
the owner's changes. Since the eighth round the model's coordinate system is that sheet's, and every
wall is the sheet's 5 in ("Architect's plan and the owner's changes"). The design (finishes, fixtures,
furniture, lighting, landscape) is ours.

Other documents: `DESIGN.md` (design brief, code contract for `bl/`, the decisions of each round),
`bl/MATERIALS.md` (material library), `ASSETS.md` (third-party assets), `tools/web/README.md` (site
data formats, publishers, tests), `tools/web/tests/README.md` (the browser test suite).

## Repository layout

```
index.html                  markup only; loads assets/css/tour.css and assets/js/tour/main.js. No data.
assets/
  js/tour/                  the page: main, viewer, engine, inside, dollhouse, exterior, ui, dimensions,
                            design, testapi (see "The page")
  css/tour.css
  data/                     tour.json, measurements.json, design.json   (generated: build_site_data.py)
  plans/dimension-plan.svg  Dimensions sheet drawing                    (generated: dimension_plan.py)
  panos/{8k,4k,2k}/, panos/manifest.json, thumbs/                       (publish_panos.py)
  model/house.glb                                                       (bake_web.py)
  exterior/                 orbit frames, half-size copies, manifest    (publish_exterior.py)
  design/, references/      Design sheet images
  vendor/three/             three.js r170
tools/render/               this folder: Blender build, renders, bake, data tools
  data/                     source data: scene, sweeps, measurements, design, hero cameras
  data/concept/             the frozen concept plan the Blender build is written against
  bl/                       Blender modules: shell, zones, warp, revisions and their specs, roof, garage,
                            laundry, lighting, materials
  sheet_check/              the built model measured against the architect's sheet ("Verify", step 3)
  .cache/                   everything generated (git-ignored): house.blend, panos/, heroes/, web/,
                            exterior/, logs/, polyhaven/, venv/
tools/web/                  site data helper, publishers, dev harness, tests/
sizes/sizes.pdf             the architect's plan
styles/                     the owner's style images (reference only; never copied into the site)
1095-mckinley-walkthrough-v2.html   an older single-file walkthrough; no tool touches it
```

## Requirements

* **Blender 5.2 LTS.** Cycles uses an NVIDIA GPU through OptiX; the CPU works but is slow. Set
  `BLENDER=/path/to/blender`.
* **Internet on the first build.** CC0 textures, models and the sky HDRI are fetched from Poly Haven
  into `.cache/polyhaven/`.
* **Python 3.** The data tools need only the standard library. Review sheets and the publishers need
  numpy and Pillow: `python3 -m venv tools/render/.cache/venv &&
  tools/render/.cache/venv/bin/pip install numpy pillow`.
* **Node 18.19+ and Google Chrome** for the browser tests.

Commands below are run from the repository root, with `PY=tools/render/.cache/venv/bin/python`.

## Data flow

```
tools/render/data/concept/{scene,measurements,scene_classification}.json     frozen concept plan
  │  apply_relayout.py          maps it onto the architect's plan (relayout.py)
  ▼
tools/render/data/{scene,measurements,scene_classification}.json
  │  apply_revisions_web.py     the owner's changes, in the model's own numbers; also data/design.json
  │  apply_sweeps.py            installs data/sweeps.json as the tour (scene.tour.nodes / edges)
  │  extract_scene.py           consistency check; writes nothing
  ▼
tools/web/dimension_plan.py     ->  assets/plans/dimension-plan.svg
tools/web/roof_drawing.py       ->  assets/design/roof.svg      (from bl/roof.py and the skylights' spec)
tools/web/build_site_data.py    ->  assets/data/{tour,measurements,design}.json
```

```bash
python3 tools/render/apply_relayout.py
python3 tools/render/apply_revisions_web.py
python3 tools/render/apply_sweeps.py
python3 tools/render/extract_scene.py            # expect "site data check: ok"
python3 tools/web/dimension_plan.py
python3 tools/web/roof_drawing.py                # only after a change to the roof or to a skylight
python3 tools/web/build_site_data.py --version <label>      # after publishing, see "Publish"
```

* Every step is idempotent and writes only when the bytes change; the whole sequence run twice leaves
  the files as they were. All of them read and write through `tools/web/sitedata.py`.
* `apply_relayout.py` **replaces** `scene.json`, `measurements.json` and `scene_classification.json`
  from the concept data, so the next two steps must follow it every time. Between them the scene lacks
  the owner's changes and the sweeps: do not run the sequence while a render, a bake or
  `place_sweeps.py` is reading `tools/render/data/`.
  To try it without touching the working files, set `SITEDATA_ROOT=<dir>` (see `tools/web/README.md`).
* **The data copies no number of the model.** `apply_revisions_web.py` reads `relayout.py` (wall
  faces, `ROOMS`), `bl/revision_spec.py` and `bl/garage_spec.py`, and through `blender_spec()` the
  plain top-level assignments of three modules that import `bpy` and so cannot be imported:
  `bl/roof.py`, `bl/zones/exterior_layout.py` and `bl/zones/kitchen_dining_kitchen.py` (a statement
  that needs `bpy` is skipped silently, and a name it would have defined is then missing). After a
  constant in one of them changed, run the sequence from `apply_relayout.py` again. The tool also
  writes `scene_classification.json`: the room regions the hall and Bedroom 2 have since the eighth
  round, and a record for every scene object.
* `data/scene.json` is the full scene: objects, the tour, the audit rows, the revision notes. Object
  indices are stable (`scene_index` in the built model, which `bake_web.py` relies on): tools append
  objects, they never insert and never delete. A piece the built model no longer has keeps its index
  and is marked `removed`, in the group `removed`, which nothing draws. `extract_scene.py` fails when
  an index shifted.
* `data/sweeps.json` is the source of truth for the tour graph. `place_sweeps.py` writes it from the
  built model (see "Add or move sweeps"); `apply_sweeps.py` only installs it. When the model or a seed stop
  changed, `place_sweeps.py` runs between `apply_revisions_web.py` and `apply_sweeps.py`: it reads
  the seed stops, the door schedule and the room regions from the data files, and the floor levels
  from the spec modules.
* `data/design.json` is hand-edited (Design sheet text). `apply_relayout.py` does not rebuild it.
  The picture of its view `roof` is a drawing, `assets/design/roof.svg`: `tools/web/roof_drawing.py`
  draws the roof's ten planes, ridges, hips and valleys, the eaves and the five skylights from
  `bl/roof.py` and `bl/revision_spec.py`, read the way `blender_spec()` reads them (`--check`
  exits 1 when the file is out of date).
* The Blender build does not read `data/scene.json`: it builds on `data/concept/` and carries the
  house onto the architect's plan itself (see "Architect's plan and the owner's changes"). It reads
  `data/measurements.json` for the names of the window grid bars and `data/sweeps.json` for the
  living room's clearance report. The renders, the bake and the publishers read the sweeps from
  `data/scene.json`.

## Production run

```bash
export BLENDER=/path/to/blender
tools/render/final_run.sh                 # 8192 px panoramas, 192 samples
SKIP="build probe smooth" tools/render/final_run.sh        # resume a run that stopped in the panoramas
```

`final_run.sh [width=8192] [samples=192]` runs the stages in order and stops at the first one that
fails (exit code, a Python traceback, or `FAILED` in the build log). It does not publish.

| Stage | What it does | Output in `.cache/` | Time on an RTX 5090 |
|---|---|---|---|
| `build` | `build_scene.py --zones all --strict` (ends with the sky check, see "How the look is controlled") | `house.blend` | about 1 min |
| `probe` | automatic exposure and white balance of every sweep, no panorama | `panos_probe/render_meta.json` | 125 s for 52 sweeps |
| `smooth` | `smooth_exposure.py` relaxes those values along the tour graph | `panos/pins.json` | 2 s |
| `panos` | `render_panos.py --pins --skip-existing` | `panos/<ID>.png`, `panos/render_meta.json` | about 3.2 min per sweep (2.6 to 3.9): 2 h 18 min for 43, so about 2 h 50 min for today's 53 |
| `heroes` | `render_heroes.py`, 2400 px, 1024 samples | `heroes/<key>.png` | about 16 min |
| `bake` | `bake_web.py --detail 2` | `web/house.glb`, `web/house.summary.json` | about 13 min |
| `adapt` | `adapt_web.py` | `web/adapt.json` | seconds |
| `exterior` | `render_exterior.py`, 3000 px, 512 samples | `exterior/` | about 18 min |

(Times: the fourth round's run of all 43 sweeps, 2026-11-19, 185 min from the panoramas to the
exterior frames. The fifth and the sixth round each rendered 32 sweeps again, see "Re-render a
subset"; the fifth took 131 min with the hero stills and the bake. The seventh and the eighth
round's runs are full ones with fresh pins, see "Render everything again"; the eighth, all 53
sweeps on 2026-11-24, took 234 min: panoramas 179 min (about 3.4 min each), hero stills 21 min,
bake 15 min, exterior frames 20 min.) A panorama PNG is 8-bit RGB, about
33 MB. While one renders, the card shows about 13.5 GB in use.

* **Environment:** `SKIP` (stage names to skip), `NODES` (comma list of sweeps for the probe and
  panorama stages; default all), `PANO_ARGS`, `SMOOTH_ARGS`, `BAKE_DETAIL` (default 2), `BAKE_ARGS`,
  `TG_CACHE` (output directory instead of `.cache/`).
* **Logs:** `.cache/logs/final_run.log` (timestamps, one line per sweep) and `.cache/logs/<stage>.log`
  (full output of a stage).
* **Resume:** the panorama stage skips a sweep whose PNG exists with the same width, samples, pins and
  scene file. An image is rendered to `_part_<ID>.png` and renamed when complete, so an `<ID>.png` is
  always a finished render. The scene file is compared by name and modification time: after a rebuild
  (or a `cp` onto `house.blend`) every panorama counts as stale.
* **Which build:** the sweeps in `data/sweeps.json` were placed on one particular build (the file's
  `generated_from`). If the build stage changes the model, re-run `place_sweeps.py` before rendering
  (with `--keep` when only part of the house changed). To render a build you already have, copy it
  to `.cache/house.blend` and add `build` to `SKIP`.
* **Outdoor sweeps:** `OD` and `OP` get their white balance pinned by hand between `smooth` and
  `panos`. A run straight through renders them with the probe's balance (13999 K behind the
  house in the seventh round's run): for a release, run the stages as in "Render everything
  again".
* **GPU jobs** go through `tools/render/gpu.sh`, a machine-wide lock, so two jobs never share the card.
* **Alignment:** `render_panos.py` places each equirectangular camera at the sweep's `p` (its eye
  height included, which since the eighth round is 5.0853 ft above the level the sweep stands
  on: lower in the garage, on the porch and on the rear landing) with yaw 0 = −z, which is what
  the page's projection assumes.
* `web/adapt.json` (the `adapt` stage) and `web/collision.json` (the bake) are leftovers of the
  earlier free-walk page. The page reads neither and they are not published.

## Publish

```bash
PY=tools/render/.cache/venv/bin/python
$PY tools/web/publish_panos.py tools/render/.cache/panos --prune    # assets/panos/{8k,4k,2k}, thumbs, manifest
$PY tools/web/publish_design.py tools/render/.cache/heroes          # assets/design/<key>.webp
cp tools/render/.cache/web/house.glb assets/model/                  # the baked model
$PY tools/web/publish_exterior.py tools/render/.cache/exterior      # assets/exterior/
python3 tools/web/build_site_data.py --version <YYYY-MM-DDx>        # assets/data/*.json, ?v= in index.html
```

* `build_site_data.py` comes last: it publishes the tour graph, and the page expects a panorama for
  every sweep it names.
* Use a new `--version` label for every publish. The model, the data files, the Design images and the
  modules are fetched with `?v=<label>`; panoramas and exterior frames carry the content hash of their
  own manifest.
* `--prune` deletes the files of sweeps that left the tour and every other `.webp` in
  `assets/panos/{8k,4k,2k}` and `assets/thumbs` that the manifest does not list.
* What each publisher writes, its options and exit codes: `tools/web/README.md`.
* Never commit third-party images (listing photos, the `styles/` images) into the site.

## Verify

1. **Build log** (`.cache/logs/build.log` in a production run). No `FAILED` on the `revisions:` line
   and no Python traceback; the `warp:` line has no `overflow` entry (the `front bath + closets`
   entries of earlier rounds went when the eighth round fitted that bath and its closet out after
   the warp); the line `[lighting] sky check: ...` ends in `(ok, tolerance 5)`. Then
   `python3 tools/render/apply_revisions_web.py --check-grids <build log>` (writes nothing; exit 1
   when the window grids of the Dimensions sheet's texts are not the built ones). It ends with
   `window grids: 15 in the build log, 15 in WINDOW_GRIDS: the same`. The build names the grid
   bars after the ids of `data/measurements.json`, so the log must come from a build made after
   the data sequence ran: a build on the seventh round's schedule lists the living room's sliding
   door as `W03` / `W04` and the sidelights as `D01 sidelight ...`.
2. **Shell.** `$BLENDER -b tools/render/.cache/house.blend --python tools/render/check_holes.py`
   ray-casts ceilings, floors and floor seams and checks every baseboard for a wall behind it. A
   clean build prints the single line `no holes`. (Until the seventh round the baseline was one
   line, `ceiling 5307 Coordinated entry rear gable ...`: the eighth round's roof rebuilt that
   gable.) A floor must lie at its level: the house floor, or inside the garage's clear rectangle
   (`relayout.ROOMS['garage']`) the garage floor, 11 in lower (`garage_spec.FLOOR_Y`); the step at
   the house door and the garage's baseboards stand above that floor and pass.
   Its grid is 0.05 ft since the eighth round (0.2 ft before, which stepped over a 0.10 ft strip):
   a thinner gap passes (the fourth round found a 0.03 ft one along a ceiling edge only by a finer
   scan). It also cannot see two slabs that lie in one plane (they render as a dark band) or a bare
   strip of floor under a baseboard; the fifth round found both in renders. So look at renders of
   every new wall, floor and ceiling joint (`DESIGN.md`, "Fifth round", lists the finer scans).
3. **Sizes against the architect's sheet.** `tools/render/sheet_check/` measures the built model
   against SKA002: the eighth round's integration script, with the sheet as data beside it
   (`ska002_geometry.json`, `pdf_dimensions.json`, `heights_site.json`; its own `README.md` says
   what each table holds).

   ```bash
   $BLENDER -b <build>.blend -noaudio --python tools/render/sheet_check/extract.py -- <dump prefix>       # reads only; about 1 min, 115 MB
   DUMP=<dump prefix> $BLENDER -b -noaudio --python tools/render/sheet_check/measure.py -- <out prefix>   # writes <out>.md and <out>.json
   grep -n 'Counts' <out prefix>.md; grep -c 'small\|DIFFERS' <out prefix>.md
   ```

   It casts rays on the dumped meshes and reads no number of the source code. Under
   "1. SKA002: the 39 printed dimensions" it must print `Counts: {'match': 33, 'owner': 6}`:
   33 of the sheet's 39 printed dimensions within 1/2 in, and the six that are the owner's
   decisions (rows 11 and 34, the sheet's laundry closet in the kitchen; rows 12, 13, 18 and 20,
   the foyer-side wall). No row of any table (overall sizes, doors, windows, skylights, levels,
   roof, kitchen) may read `small` or `DIFFERS`: the second command prints `0`. The porch rows
   expect what the round built, because the set gives no level for the new porch: the slab at
   −0.4583 and two equal risers of 5 1/2 in (A1.3's −0.336 is the existing porch). After a
   deliberate change of `exterior_layout.PORCH_TOP` change `PORCH_TOP` and `PORCH_RISER_IN` in
   `measure.py` with it.
4. **Renders.** Look at them: `review.sh` contact sheets before a long run, the panoramas after it
   (`pano_views.py` cuts ordinary views out of one).
5. **Data.** `python3 tools/render/extract_scene.py`, `python3 tools/web/dimension_plan.py --check`
   and `python3 tools/web/build_site_data.py --check` (exit 1 = `assets/data` is out of date).
6. **The site.** Serve the repository root and run the browser suite:

   ```bash
   python3 -m http.server 8765 --bind 127.0.0.1          # in another terminal, from the repository root
   cd tools/web/tests && npm install && npm test         # the whole suite, about 10 minutes
   ```

   It drives the page in headless Chrome like a visitor and holds it to its contract: at rest the
   frame equals the published panorama (PSNR ≥ 40 dB), a hop takes at most 1.2 s, every sweep is
   reached by ring clicks, no console errors, texture memory within budget, phone layout.
   `data.test.js` (no browser) checks the published data, panoramas and plan against each other: run
   it after every data or publish step. It fails while `assets/data`, the plan drawing and
   `tools/render/data` are out of step, which is the normal state between a data change and the
   publish.

   Chrome's GPU flags come from `TOUR_CHROME_ARGS`. The default
   (`--use-angle=vulkan --enable-gpu --ignore-gpu-blocklist --enable-features=Vulkan`) uses the
   discrete GPU. While a render owns it, run `npm run test:igpu` (`--use-angle=gl-egl`, the
   integrated GPU). Details and the other variables: `tools/web/tests/README.md`.

## Common jobs

### Change a room's design

1. Edit the zone module(s), `bl/zones/<zone>*.py` (rules in `DESIGN.md`). Find out first which
   plan the code you are about to edit is written on:
   * **Concept-plan feet, carried onto the architect's plan by `bl/warp.py`:** the kitchen and
     dining area, Bedroom 2, the furniture of Bedrooms 3 and 4, the shared bath, the foyer and the
     hall north of it, the garage's fittings. A size that must come out exact on the sheet is stated
     in plan feet and carried back through the inverse of the map (the kitchen's `PLAN_*` constants
     with `_px` / `_pz`; `_rect_centre` for the dining table).
   * **Plan feet, built after the warp** by a revision: the primary suite (`primary_suite.py`:
     bedroom, vestibule, walk-in closet), the primary bath (`baths_primary.py`), Bedroom 2's closet
     block and the hall beside it (`hall_block.py`), Bedroom 3's bath (`baths_suite3.py`), its
     closet, and the doors and west windows of Bedrooms 3 and 4 (`bedrooms_rooms.py`), the
     garage's floor, step, doors and water heater and the front door unit (`bl/garage.py`), the
     roof with the two vaulted ceilings and the porch's frame (`bl/roof.py`).
   * **Plan feet, built with the zones:** the living room (`living.py`), where every object hangs
     under the root Empty `TG living root`, which the warp skips; in the kitchen the island and the
     refrigerator (`kitchen_dining_cabs.PlanFace`); the whole exterior zone
     (`exterior_layout.py`), which is not warped.

   In plan feet a number in the code is the number on the architect's sheet and in the built
   model: edit it directly, with no inverse map. The warp's name rules (fitted or loose) do not
   touch pieces built after it; the bake's name rules still do. Walls, doors, windows and
   skylights are revisions; move those in the spec modules, which the zones, the sweep placement
   and the web data read too: `bl/revision_spec.py` (`SUITE_*`, `BATH_*`, `PRIMARY_BATH_*`, and the
   blocks "v7 glazing", "v7 bedrooms", "v7 hall"), `bl/garage_spec.py`, and the wall faces
   themselves in `relayout.py`. See "Architect's plan and the owner's changes".
2. Preview: `tools/render/dev_preview.sh kitchen_dining K0,D0,H2` builds only that zone and writes
   `.cache/dev_kitchen_dining/K0_sheet.png` (four 90° views) for each sweep named. The revisions
   run in every build, so `dev_preview.sh primary_suite P0,S0,C0` and `dev_preview.sh baths A0,A3`
   show those rooms fitted out; a fit-out whose zone was not asked for is skipped (the walls,
   doors and the roof are built in every build, also with `--zones none`).
3. Full build (about a minute), then steps 1 to 3 of "Verify":

   ```bash
   $BLENDER -b --factory-startup -noaudio --python tools/render/build_scene.py -- \
       --zones all --strict --out tools/render/.cache/house.blend
   ```
4. If furniture moved or the walkable floor changed, place the sweeps again, keeping the layout
   (next job, `--keep`).
5. Re-render what sees the change ("Re-render a subset"), publish, run the tests.
6. Update the room's text in `tools/render/data/design.json` if it describes what changed.

### Add or move sweeps

`place_sweeps.py` ray-casts the built model (CPU only) and decides where the camera may rest. It puts
down the stops set by hand (`PLACED`), keeps the 19 seed stops (the walk-in closet's `C0` goes to the
middle of the closet's aisle, `WALKIN`), keeps an old approach stop only where it joins the graph,
puts a sweep in every doorway that has none within 3 ft, fills the remaining reachable floor
(≥ 1.2 ft clearance, ≥ 4 ft between sweeps that see each other, at most 4 in the garage, no second
one in a bathroom), and adds `LC` in the foyer, 4 ft in front of the laundry closet's door wall and
looking 14° down at the stacked units, and the outdoor sweeps `OP` (porch) and `OD` (the rear
landing outside the living room's sliding door, in front of its open way; labelled "Rear landing"
since the eighth round, while its id and its room key `deck` are as published) when their doors
stand open. It writes `links` (straight lines a person can walk) and
`visible` (line of sight, through clear glass). The result is deterministic and ids are stable; the
rules are in `DESIGN.md`. On the eighth-round model: 53 sweeps (51 indoor, the porch, the rear
landing), 70 links, one component, 17 hops across, links 2.8 to 10.4 ft; the old ids T1 T3 T4 T6
P1 L5 C3 are gone.

```bash
$BLENDER -b tools/render/.cache/house.blend -noaudio --python tools/render/place_sweeps.py -- \
    --keep tools/render/data/sweeps.json \
    --out tools/render/data/sweeps.json --overlay tools/render/.cache/sweeps_overlay.png      # CPU, about 80 s
python3 tools/render/apply_sweeps.py --check        # validate only
python3 tools/render/apply_sweeps.py                # install into data/scene.json
python3 tools/render/extract_scene.py && python3 tools/web/dimension_plan.py
```

* Look at `sweeps_overlay.png` and the `[sweeps] note:` lines before installing. Exit status 2 means
  the graph is not connected and nothing was written.
* **Levels.** The house floor is y 0; the garage floor, the porch slab and the two rear landings
  lie lower (`LEVELS` in `place_sweeps.py`, read from `bl/garage_spec.py` and
  `bl/zones/exterior_layout.py`; the numbers are under "Architect's plan and the owner's
  changes"). A sweep's eye is 5.0853 ft above the level it stands on, so `p[1]` is 4.169 in the
  garage, 4.627 on the porch slab and 5.002 on the rear landing. In `sweeps.json`, `level` is that level and `floor` the
  surface under the stop (rug, tile, slab), where the page draws its ring. The step at the door
  between the house and the garage (`STEPS`) may be crossed by a link and never carries a sweep.
* **`--keep SWEEPS.json` keeps an installed layout** (normally the file the run overwrites), so that
  the panoramas of the untouched rooms stay valid after a change to part of the model. Every sweep
  of that file stays exactly where it is, with its id, yaw and pitch, while the new model
  leaves it at least 0.9 ft of clearance (`--keep-clear`). A seed the scene file has moved since
  (`NODE_MOVES`) follows the scene; a sweep that lost its place is nudged by up to 1.5 ft (a seed:
  placed again from its stop in the scene file) or dropped, with a note; a stop of `PLACED` goes to
  its place; `LC` follows the closet. A label follows the scene file too: a renamed
  seed takes its new name, and with it the kept sweeps that carried its old one; an outdoor sweep
  takes the label `OUTDOOR` gives its id. The usual rules
  then add sweeps only on floor the kept ones leave uncovered, with ids the kept file never used,
  and `links` / `visible` are computed afresh. The file's `"keep"` block (printed by
  `apply_sweeps.py`) lists the unchanged, moved, new, removed and renamed ids. Sixth round: 43
  unchanged; `C0` and `S1` moved; `P2 P3 P4 P5` new, on the floor the bed left uncovered when it
  moved to the west wall; none removed; `S0`, `S1` ("Primary vestibule") and `C0` ("Walk-in
  closet") renamed. Seventh round: 48 unchanged, none moved; `L5` removed (it stood where the
  sofa is now, with no free floor within 1.5 ft); `L6 L7 L8 L9` new in the living room. Eighth
  round (with `--keep-clear 1.2`): 26 unchanged; 25 moved, of them 13 seeds by 0.06 to 0.29 ft
  with the 5 in walls, seven by `PLACED`, `H3` and `A3` with their seeds, `L9` nudged, `LC` with
  the closet and `OD` to the sliding door's open way; `H5` new; `C3` removed. Placed once more on
  the round's final build (the porch slab lowered, the olive tree moved off the east window, the
  kitchen skylight and a west window rebuilt): all 52 stay where they are; `OP`'s eye follows the
  slab (4.749 to 4.627); `D2` is new, in front of the living / dining east window, where the
  tree stood; `OD` is renamed "Rear landing". A second run on its own result keeps all 53.
* **`--keep-clear 1.2`** (the clearance a new sweep needs) is the value to use when every panorama
  is rendered again anyway, as in the eighth round: kept sweeps that a changed model has left with
  less than a new sweep would get are then moved.
* **Stops set by hand** are in `PLACED` in `place_sweeps.py`: id, a place written from the spec
  modules' names, and the reason. Today `T2` (in front of the suite entry and Bedroom 2's door),
  `H5` (where the hall's two legs meet), `H0`, `Y0` and `Z0` (the middle of the two bedroom
  doorways, beside the open leaves), `G0` (on the garage floor, clear of the step and of the open
  leaf), `L0` and `K2`. An entry is used while its place is standable with `--keep-clear` of
  clearance; otherwise the rules decide and a note says so. The tool's own measure of clearance
  (16 directions at four heights) does not see a lever, a table's rim or a worktop's edge: those
  are the cases an entry is for.
* **Opening views chosen by eye** are in `OPENING` in `apply_sweeps.py` and override the automatic
  or kept yaw and pitch at every install: `G0`, `H2`; since the sixth round `C0` (the closet's
  hanging wall), `S1` (through the bath door at the stone wall), `A0` (across the vanity) and `P5`
  (the bed between the two windows); since the seventh `L7` (the sofa wall), `L8` (the television
  on the left, the rear glass, the sofa on the right) and `D0` (across the dining table at the
  refrigerator and the microwave); since the eighth `A3` (the shower end of Bedroom 3's bath as
  rebuilt), `H3`, `H5`, `H0`, `H4` and `T2` in the hall, `K2` (down the aisle between the island
  and the east counter), `Y0` and `Z0` (into the two bedrooms) and `D2` (from the east window at
  the island, the cooktop wall and the dining table; its automatic view has the olive tree across
  the right of the picture). A card of the highlight
  reel opens its sweep at this view and its thumbnail shows it, so `L8` and `D0` are also the
  reel's "Living room" and "Open living area" pictures (`HIGHLIGHTS` in `apply_revisions_web.py`
  names `L8` instead of `L0` since the seventh round, and has no `C3` since the eighth).
* **Without `--keep`** the whole tour is laid out afresh from the seeds: fill sweeps may land
  elsewhere, and then every panorama has to be rendered again.
* **More or fewer sweeps** (a fresh layout): `--min-sep` (default 4.0 ft between sweeps that see each
  other; on the fourth-round model 3.75 gave 45 sweeps and 3.5 gave 50), `--garage-max`,
  `--max-sweeps` (indoor sweeps; default 52, one more than the tour has), `--outdoor both|each|off`,
  `--laundry auto|on|off`.
* **Move or drop one of the seed stops:** `NODE_MOVES` and `NODES_GONE` in `apply_revisions_web.py`;
  run `apply_relayout.py` and `apply_revisions_web.py`, then `place_sweeps.py`, then the sequence
  from `apply_sweeps.py` on. The placement keeps a seed where the scene has it (and nudges it only
  when it has less than 1.2 ft of clearance), so the old `sweeps.json` must not be installed in
  between. Both tables act on the seed stops only: a tour that `apply_sweeps.py` installed is left
  as it is. Today's entries: `K0` at the west end of the work aisle between the island and the
  cooktop counter (the dining chairs stand where the concept had the stop); `H3` in the hall's
  east leg, `A3` between the vanity and the door of Bedroom 3's bath, and `G0` on the garage
  floor (eighth round; `PLACED` then moves `G0` again); `C3` gone, because Bedroom 3's closet is
  a reach-in closet that `B3` looks into.
* **By hand:** `data/sweeps.json` can be edited (degrees; links must be listed on both ends) and
  `apply_sweeps.py` refuses a broken graph, but the next `place_sweeps.py` run regenerates the file.
  A lasting rule belongs in `place_sweeps.py` (`PLACED` for a single stop).
* A sweep that is new or has moved needs a panorama, and so does every sweep that sees a changed
  part of the model ("Re-render a subset"); a removed one is dropped from the site by
  `publish_panos.py --prune`. Ids named by `measurements.json`, `design.json` or the highlight reel
  must survive: `apply_sweeps.py` and `extract_scene.py` warn when one is gone. An id that left
  the tour after its panorama was published is never given out again (`RETIRED`: `L5`, `C3`).

### Add an owner's revision

A plan change has three records that must agree:

1. The numbers, in a pure-Python spec module (no `bpy`): `bl/revision_spec.py`, or
   `bl/garage_spec.py` for the garage and the front door. Write every position from a wall face
   of `relayout.py` (`R.XW`, `R.Z_PBATH_N`, `R.ROOMS[...]`), never as an absolute number: then it
   keeps its place in its room when a wall line moves. A number read off the sheet can be written
   down as it stands, because the sheet's frame is the model's.
2. `bl/revisions.py`: the Blender geometry. Add a function (or a module it calls, as
   `bl/zones/hall_block.py`, `bl/garage.py` and `bl/roof.py` are) and put it in the list in
   `apply()` before the repairs that run last (`floor_level`, `floor_gaps`,
   `living_east_baseboard`, `skirting_trim`, `skirting_joints`) and `white_windows`. Copy an
   existing wall for a new wall (`_like`), so it keeps a
   `scene_index` and bakes as a wall. Raise when a piece is not where the spec expects it: that
   shows as `FAILED` on the `revisions:` line. A zone that must make room reads the same spec:
   a zone written in concept feet carries the number back with the inverse of the map, as
   Bedroom 4 does with the closet wall's face (`bedrooms._b4_desk_x`, `relayout.X_FRONT_ROOMS`).
   Anything put into the `openings`
   collection stays below 7 ft or carries "ceiling" in its name: `check_holes.py` casts its
   ceiling rays up from 7 ft (the suite entry's track ends at 6.99 ft). A new or moved window
   gets its frame members in `black_aluminum`, like the shell's, and its pane in `glass_clear`
   or `glass_frosted`, both in `openings`: `white_windows`, the last step of all, finds it by
   those materials, makes it white and gives it its grid ("Change a window's grid"). The
   eighth round's helpers `_glz_wall`, `_glz_window` and `_glz_slider` re-cut an outer wall and
   build a window or a sliding door that way. A door is given by its clear width between the jamb
   liners (`DOOR_*` and `hinged_leaf()` in `revision_spec.py`): the wall opening is one liner
   wider on each side and the leaf 1/4 in narrower.
3. `apply_revisions_web.py`: the web data. A new change list (`CHANGES_<n>`, or a function like
   `changes_8()` when the text quotes the spec's numbers; it becomes
   `design_revision.owner_changes_<n>` and shows in the Design sheet by itself), rooms / doors /
   windows in the measurements, the wall boxes of `scene.objects`, and the Design view if the
   change gets one. In `scene.objects` an existing piece is reshaped in place and keeps its index
   (since the eighth round by index with the name checked, `Round8Scene`, because the pieces of one
   wall share a name); a new piece is **appended** by name; a door that moves keeps its leaf
   object, moved in place; a piece the build no longer has is marked `removed`. The room table
   of the About sheet (`scene.audit`) is a copy of the schedule's rooms. A change list that a
   later round overrides stays, reworded to say so.

The smallest complete example is the Bedroom 3 bathroom's taller window (sixth round):
`BED3_BATH_WIN_Y` in the spec; `revisions.bedroom3_bath_window` reshapes the wall, the frame and the
pane; `baths_suite3.build_room` lays its tile and builds the sill and the jamb returns from the same
constant; `apply_revisions_web.py` reads it for W11.

For a design still: a camera in `data/hero_cameras.json`, its key in `KEYS` of
`tools/web/publish_design.py`, and `views.<key>` in `data/design.json`.

Before any of it, put what the request leaves open to the owner as direct questions, each with a
recommended answer (`DESIGN.md`, "Sixth round": two of four recommendations were wrong). Then, in
this order: build and verify; `apply_relayout.py` and `apply_revisions_web.py`;
`place_sweeps.py --keep` on the new build (look at the overlay); the sequence from `apply_sweeps.py`
on; render what the change touches ("Re-render a subset"); publish; tests. Add the round to
`DESIGN.md`.

### Change a window's grid

Every window and glazed door is white with grid bars since the seventh round. One revision does
it on the built model, `bl/revisions.white_windows`, from the block `WINDOW_*` of
`bl/revision_spec.py`; no window builder knows about it (the rule and its departures:
`DESIGN.md`, "Seventh round"). The units the eighth round rebuilt or added (the two sliding glass
doors, W02, W05, W07, W12, W15, the front door's sidelights) get their grids the same way.

* **One window:** add its pane's name to `WINDOW_GRID_KEEP` as a regular expression with
  `(columns, rows)` per sash, as the kitchen's `r'^W08 glass$': (2, 4)`. A transom above keeps
  those columns in one row. The pane is the window's glass object in the `openings` collection
  (`whatis.py` names it; the shell's panes carry their scene index, as
  `3198 Primary added west window ...`).
* **All windows:** `WINDOW_LITE` (the house's lite, 14 × 16 1/2 in), `WINDOW_LITE_MAX_RATIO`,
  `WINDOW_TRANSOM_RATIO`; the bars' section is `WINDOW_BAR_W`, `WINDOW_BAR_PROUD`,
  `WINDOW_BAR_BEVEL`.
* **A piece that should be white too** (a stool, a pull, a post built by a zone): its name in
  `WINDOW_WHITE_ALSO`. The kitchen window's casing and stool are white in the zone itself
  (`WHITE` in `kitchen_dining_window.py`).
* **Left alone:** the skylights (`WINDOW_SKIP`; their frames stay `black_aluminum`), and whatever
  is not in the `openings` collection: shower glass, mirrors, cabinet glass, the garage door's
  lites. The front door's leaf stays walnut; its two sidelights are windows (W22, W23).
* **Afterwards:** build; the revision reports `grids` (columns × rows per sash and the lite
  sizes) on the `revisions:` line and fails when a glass opening is not a rectangle, a mullion
  named in `WINDOW_MULLION_CENTRE` is missing, or a frame piece in `openings` is left black.
  Copy the new grid into `WINDOW_GRIDS` in `apply_revisions_web.py` (the window's text in the
  Dimensions sheet states it), run the data sequence and
  `apply_revisions_web.py --check-grids <build log>`. The bars are named after the window's id
  in `data/measurements.json` (`W08 window grid bars`), so a new window is entered in the
  schedule before the build whose log is checked. A unit whose panes are parted by an open way
  is listed in two groups (the living room's sliding door: `D14a`, `D14b`), the bay's three
  sashes as `W09a` to `W09c`; `--check-grids` joins them. Every sweep, still and exterior frame
  that sees the window is rendered again.

### Re-render a subset

* **A few sweeps, same build:** delete their PNGs in `.cache/panos/` (a sweep whose pin changed is
  redone without that), then
  `NODES=K0,LC SKIP="build probe smooth heroes bake adapt exterior" tools/render/final_run.sh`.
* **After a rebuild that changed part of the house** (the procedure of the fifth and the sixth
  round; the sweeps were placed with `--keep` first):
  1. *Which sweeps.* The moved and new ones of the `"keep"` block, and every kept sweep whose eye
     has a line of sight to a changed part of the model, on the old build or on the new one,
     through open doorways and clear glass. The `visible` lists do not answer that: they say which
     sweeps see each other, and the entrance sweep sees the Bedroom 3 bathroom's window through two
     doorways without seeing the sweep in that bathroom. Both rounds cast rays from every sweep to
     a 7×7×7 lattice of points in a box around each changed part, on both builds (one-off scripts,
     not in the repository). A changed part is a room as well as a wall: where a window grew, the
     room is brighter, and every sweep that sees into it is rendered. When in doubt, render: a
     sweep costs three minutes.
     * Fifth round, 32 of 45: the laundry closet, the dining set, the re-planned cabinetry,
       Bedroom 4's east half, the repaired ceiling and floor strips.
     * Sixth round, 32 of 49: the nine sweeps of the primary suite; sixteen in the hall, Bedroom 2,
       the shared bath, the dining area, the kitchen and the living room, because the suite entry
       wall closes the hall's long axis and is seen from as far as the living room; `A3 Y1 B3` and
       the entrance `E0`, which see the taller window; `Y0 Y2 Y3`, which see into that bathroom.
       The 17 kept: `H1 H2 GA LC B4 Z0 C3 G0 G1 G2 G3 L1 L2 L4 L5 OP OD`.
  2. *Pins.* A sweep without an entry in `.cache/panos/pins.json` is rendered with its own
     automatic values (`render_panos.py` prints `NOT pinned`), which would show as a step in the
     cross-fade; and a room that was rebuilt no longer fits its old pins. So probe the render list
     on the new build into a scratch directory (`render_panos.py` with the probe stage's options:
     `--nodes <ids> --preview-only --preview-width 480 --samples 16 --out <dir>`) and compare with
     the automatic values of the published run (`auto` in `.cache/panos/render_meta.json`).
     * Where the probes repeat (the fifth round), the pins stay, and each new sweep gets the
       average of its linked neighbours' pins (`ev`, `kelvin`, `tint`; new sweeps linked to each
       other are solved together). A sweep whose id is reused at another place (`LC`) is pinned
       like a new one.
     * Where a room's probe moved by more than 0.3 stop (the sixth round: the walk-in closet, now
       an enclosed room with its own light, probed 1.35 stop lower, the bedroom 0.45), re-solve
       the sweeps of the changed rooms: `smooth_exposure.py --fix <all other ids>` on a metadata
       file in which the other sweeps carry their pins as probe values, so no kept panorama
       changes. The nine suite sweeps needed `--move-kelvin 2600` to close every link. With the
       old pins and the neighbours' average, the closet and the four new bedroom sweeps would
       have come out about a stop too bright.

     Either way every link must end inside the smoothing limits (0.3 stop, 300 K, 6 tint), and a
     sweep whose pin changed is rendered.
  3. *Render.* Copy the new build to `.cache/house.blend`, then
     `NODES=<ids> SKIP="build probe smooth exterior" tools/render/final_run.sh` renders those
     panoramas, all hero stills and the bake (add `heroes` to `SKIP` when no still shows the change).
     Drop `exterior` from `SKIP` when something outside changed: the stage renders all 32 frames,
     which share one exposure. The sixth round did (the taller and the wider west window, the
     moved skylight). Every sweep of `NODES` is redone, because its metadata names the old build;
     the others are not touched.
  4. Until the next full render `render_meta.json` names two builds, so a run without `NODES` would
     redo the kept sweeps as well: keep passing `NODES`.
* With `NODES`, always skip `probe` and `smooth`: the probe stage starts a fresh metadata file and
  `smooth` would write a `pins.json` that holds only those sweeps. Probing and smoothing all
  sweeps again instead (`SKIP="build panos heroes bake adapt exterior"`, 2 minutes) is the other
  way to follow a change in brightness, but it may move the pins of kept sweeps, which then have
  to be rendered too, and it resets the outdoor sweeps' hand-set pins ("Render everything
  again").
* **Publish only those:** `$PY tools/web/publish_panos.py tools/render/.cache/panos --only K0,LC`
  (the other manifest entries are kept).
* **One hero still:** `tools/render/gpu.sh -b tools/render/.cache/house.blend -noaudio --python
  tools/render/render_heroes.py -- --only LC`, then `publish_design.py`.
* **Review renders, not for publishing:** `tools/render/review.sh tools/render/.cache/house.blend
  K0,D0,H2 /tmp/x 1536 128 --pins tools/render/.cache/panos/pins.json`.
* **The model:** always a full bake for the site. `bake_web.py --groups REGEX --out <scratch>.glb`
  bakes and exports only the matching groups (a test); `--prep-only` prints the atlas plan without
  the GPU.

### Render everything again

When a change shows in every picture, nothing of the last run is kept: all panoramas, the hero
stills, the bake and the exterior frames are rendered, with pins from a fresh probe. The seventh
round was such a change (white window frames and grids, and the sky turned to the sun), and so is
the eighth (every wall moved onto the sheet's lines, new openings, a new roof with 1'-0" eaves,
lower ground). Place the sweeps (`--keep`, and `--keep-clear 1.2` since nothing is kept anyway),
put the reviewed build at `.cache/house.blend`, then:

```bash
SKIP="build panos heroes bake adapt exterior" tools/render/final_run.sh       # probe all sweeps, smooth
SMOOTH_ARGS="--move-kelvin 2600" SKIP="build probe panos heroes bake adapt exterior" \
    tools/render/final_run.sh                                                 # smooth again, if links stayed open
# set the outdoor sweeps' white balance in .cache/panos/pins.json (below)
SKIP="build probe smooth" tools/render/final_run.sh                           # render everything
```

* **Smoothing.** In the `smooth` table (`.cache/logs/smooth.log`) `links over a limit` must end at
  0. With the default limits five links of the primary suite stayed over (up to 536 K apart: the
  bedroom's sweeps probe at 6300 to 9000 K, the vestibule's at 4400 to 4700 K, the closet's at
  3900 K). `--move-kelvin 2600` closed all 65 indoor links (the largest move: −1963 K at `P3`). In the eighth
  round the new hall stop `H5` probes 2.4 stops below the shared bath beside it (its opening view
  faces the bright dining area), and three links stayed over the exposure limit until the move
  limit was raised as well: `--move-kelvin 2600 --move-ev 1.2` closed all 68.
* **Outdoor pins, by hand.** The smoothing leaves `OD` and `OP` at their probe values, and the
  probe's white balance is no daylight balance out there (seventh round: `OD` 13999 K, the upper
  limit of `WB_LIMITS`; `OP` 8107 K). After the last `smooth`, set them in `pins.json` to `OD`
  6300 K, tint 4 and `OP` 6500 K, tint 0, the values of the earlier runs; `ev` stays the probe's.
  The `smooth` stage rewrites the file, so it stays in `SKIP` from then on.
* **A new sweep has no pin and a removed one a stale one.** After the eighth round's placement
  that is `H5` and `D2` (new) and `C3` (gone): a fresh probe and `smooth` over all sweeps give
  each its due, and `publish_panos.py --prune` removes `C3`'s published files.
* **Pins of the last run are worthless after a change of the sky.** With the sky corrected, the
  north rooms lost sky fill (the primary bedroom's probe median fell to 0.64 of its value, its
  automatic exposure rose by 0.6 stop) and the south and east rooms gained a little.

## Architect's plan and the owner's changes

The tour follows the architect's floor plan (`sizes/sizes.pdf`, sheet SKA002, Option A). It has the
same rooms in the same arrangement as the earlier concept model, but different sizes. Since the
eighth round the model stands on that sheet: every wall face, opening and fixture is where the
sheet draws it, to within 1/2 in, except where the owner decided otherwise (`DESIGN.md`, "Eighth
round", lists those decisions and how the model was measured).

* **The frame.** The sheet is the model's coordinate system: a point of SKA002 at (X, Y) in PDF
  points is x = (X − 1107.075) / 18, z = (Y − 361.808) / 18 in SCENE feet (18 pt = 1 ft at
  1/4 in = 1 ft, no rotation). The west wall's interior face is x 0.225 and the rear wall's
  z 0.225. A number read off the sheet is a number of the model. Every wall, inside and outside,
  is 5 in thick, as drawn, and the house measures 39'-11" × 54'-4" outside, 53'-0" on the garage
  side. (Until the seventh round the walls kept the concept's thicknesses, 0.45 and 0.36 ft, and
  wall faces stood up to 0.28 ft off the sheet's.)
* **Levels** (y, with the house floor at 0; sheet A1.3):

  | Level | y | Constant |
  |---|---|---|
  | House floor; flat ceilings 8.0 above it | 0 | |
  | Garage floor (ceiling 8'-11" above it) | −0.917 (11 in) | `garage_spec.FLOOR_Y` |
  | Step at the door between house and garage, 1'-0" × 3'-8" | −0.458 (two risers of 5 1/2 in) | `garage_spec.STEP_Y`, `STEP` |
  | Ground in front: lawn, walk, driveway, sidewalk | −0.917 | `exterior_layout.GRADE_FRONT` |
  | Ground behind the house | −1.167 (1'-2") | `exterior_layout.GRADE_REAR` |
  | Ground along both sides | rises 3 in from the rear wall to the garage front | `exterior_layout.grade(z)` |
  | The two rear landings | −0.083 (1 in) | `exterior_layout.DECK_TOP` |
  | Their step, 12 in wide, round the three open sides | −0.625 (two risers of 6 1/2 in) | `exterior_layout.STEP_TOP` |
  | Porch slab | −0.458 (two risers of 5 1/2 in between walk and floor) | `exterior_layout.PORCH_TOP` |

  A1.3 gives −0.336 for the existing porch and no level for the new covered porch; the slab
  stood at −0.336 until the round's repair made the two risers equal.
* **`relayout.py`** holds the frame and still maps every concept-plan coordinate onto it,
  region by region.
  * The section "the sheet's frame": `WALL` (5 in), the wall faces as named lines (`XW`,
    `X_PRI_E`, `X_LIV_W`, `X_FOYER_W`, `Z_PRI_S`, `Z_B4_N`, `Z_KIT_S`, `Z_GAR_OUT` ...), each a
    chain of the sheet's printed dimensions from the two interior faces at 0.225, and `ROOMS`, the
    20 clear rectangles between them. The spec modules, the zones written in plan feet, the
    exterior layout, the sweep placement and the web data are written from these names, so nothing
    else holds an absolute coordinate.
  * The maps (`X_REAR`, `Z_LEFT` ...; `REGIONS`): their breakpoints are wall faces, the concept's
    on the old side, the sheet's on the new side, so the warp itself stretches every wall, frame,
    casing and baseboard onto 5 in.
  * Owner's change (second round): the foyer-side wall of the office and the front bedroom lines up
    with the shared bath's east wall (`FOYER_WALL`, x 15.142..15.558) instead of the sheet's 1'-3"
    jog. Both rooms are 14'-11" wide (the sheet: 13'-8"), the closets between them 6'-3", the
    foyer and the porch 5'-9" (the sheet: 7'-0"), and the foyer is the plan's 18'-6" long. The
    3'-0" front door stays centred on the foyer.
  * The three front faces (Bedroom 3, the garage, the front door wall) carry a stucco skin
    (`STUCCO`, 0.065 ft). The skin's face is the sheet's outer line and the shell wall behind it is
    thinner by the skin, so the finished wall is 5 in.
  * Rigid things keep an edge on a wall they touch (`shift_box`), so they don't sink into a wall
    where a room narrows.
  * `REGION_BY_NAME` and `PINNED` pin pieces whose centre falls on the wrong side of a region edge.
  * Two things the maps still carry the concept's way, because a revision rebuilds them after the
    warp: Bedroom 2's entry alcove and closet (`X_B2CLO_W`, `X_B2ALC_E`, `Z_B2ALC_S`, `Z_HALL_N`;
    `hall_block` replaces them with the sheet's closet block on the "v7 hall" lines `X_BLOCK_W` to
    `Z_BLOCK_S`), and the concept's roof (`ROOF_LINE`, `WING_RIDGE`, `remap_xz(..., roof=True)`;
    `roof_v7` removes it).
* **Blender build:** shell, zones, warp, revisions, daylight, in that order. It reads the concept
  data (`data/concept/`), because the shell and most room modules are written against it. After the
  zones are built, `bl/warp.py` carries the house onto the sheet with the same map:
  * architecture and fitted pieces are reshaped;
  * loose furniture moves in clusters and keeps its size (a cluster stays within one room; the
    build prints any cluster that would run into a wall as `overflow`; curve objects move with
    their cluster since the eighth round);
  * flat slabs follow the rooms on each side. Each corner takes the map of the room it borders,
    so two slabs that met on one concept line can part, or overlap, where that line crosses into a
    room with a different map. `bl/revisions.py` repairs the known cases first: `ceiling_seam` (the
    wedge in the ceiling over Bedroom 2, the bedroom hall and the shared bath; and the front edge
    of the central ceiling panel, squared onto the kitchen / garage wall line), `floor_seam` (the
    strip across the foyer floor), and `ceiling_overlap` / `floor_overlap` (fifth round: at the
    foyer's north end two ceiling slabs, and two floor slabs, lay in one plane, which renders as a
    dark band; each pair now ends on one line). `foyer_corner` fills the notch the garage's
    west wall and the kitchen / garage wall leave in the corner beside the refrigerator, and lays
    an oak patch at its foot. General repairs run last, after every change has cut or moved walls
    and slabs: `floor_level` (two floor pieces that stood 0.1 in above the oak), `floor_gaps`
    (thinner floor seams and the bare strips under door openings), `living_east_baseboard`,
    `skirting_trim` (every baseboard cut back to the stretches with a wall behind it) and
    `skirting_joints` (the short gaps between two runs on one wall closed).

  The exterior zone is built directly on the sheet's site plan (`bl/zones/exterior_layout.py`,
  written from the house's outer faces) and is not warped.
* **`bl/revisions.py`:** applies the owner's changes and, since the eighth round, the sheet's own
  layout where the concept shell differs from it, after the warp. The positions live in the spec
  modules (`bl/revision_spec.py`, `bl/garage_spec.py`; the roof's in `bl/roof.py`).
  `apply_revisions_web.py` records the same changes in the web data. `apply()` runs them in the
  order below; the first group is the owner's changes of the first three rounds.
  * Bedroom 4: flat ceiling.
  * Front bedroom: bay glazed to the floor.
  * Primary bedroom: a two-panel sliding door to the rear landing (`primary_slider`), since the
    eighth round in the sheet's 6'-4" wall opening (`SLIDER_X`; 6'-0" clear), shown closed.
  * Bedroom 2: tall window from a 2'-0" sill to the ceiling (third round; it ran to the floor
    before), since the eighth round the sheet's 6'-0" wide (`bedroom2_tall_window`,
    `BED2_REAR_WIN_X`).
  * **Rear and east openings at the sheet's widths and places** (eighth round; `living_slider`,
    `primary_west_window`, `living_east_windows`; numbers in the block "v7 glazing", helpers
    `_glz_*`). The living room's rear wall is one four-panel sliding glass door in a 12'-4" wall
    opening, head 7'-6", in place of the garden door and the two fixed lights; it keeps the id D14.
    Its east centre panel stands 2'-3" open (`LIVING_SLIDER_OPEN`), which is the way to the rear
    landing and to the sweep `OD` (`living_slider_way()`). The primary bedroom's north west window
    W15 is 3'-0", the living room's east window W05 one 6'-0" unit (W06 is gone), the living /
    dining east window W07 5'-0" with the sheet's unequal lights. The fixed panels of both sliding
    doors stand on the room-side track, as drawn. A rebuilt window has a frame as deep as the wall.
    The primary bedroom's second west window W14, the owner's, keeps its 2'-10 1/2" opening
    (`PRIMARY_WEST_WIN_S_Z`) and gets W15's unit in it (`primary_west_window_south`): the same
    frame, two sashes side by side, stool and shade, so the two windows beside the bed are a pair.
  * Bedroom 3 bathroom (sixth round, `bedroom3_bath_window`): the shower window W11 runs from a
    3'-0" sill to a 7'-6" head (`BED3_BATH_WIN_Y`; 5'-0" to 7'-0" before). Width and frosted
    glass stay; the bath's fit-out builds tile, jamb returns and sill from the same constant.
  * **Primary bath** (sixth round; `bath_door`, `bath_window`, `primary_bath_skylight`,
    `primary_bath_fit_out`; numbers `BATH_*`, `PRIMARY_BATH_*`). Laid out as on the sheet: door
    D08 at the east end of the north wall, a 5'-0" × 3'-0" shower in the north-west corner under
    the skylight W20, the toilet in the south-west corner, a 6'-6" double vanity on the
    south wall, and window W13, 3'-0" wide from its 2'-0" sill to the ceiling, with its mullion
    on the shower's glass line (clear glass; an evergreen screens it in the fenced side yard).
    `primary_bath_fit_out` calls `bl/zones/baths_primary.build_room` for the finishes: a white
    room with one stone wall (seventh round). Stacked stone on the vanity wall after the owner's
    image `styles/primary bathroom wall style.jpg`, dark timber beams, a plain grey stone
    floor; matte white tile in the shower; every other wall is the shell's own white painted
    wall, floor to ceiling, above a 5 5/8 in base of the shower's tile, under the shell's white
    ceiling. The zone builds nothing on those walls.
  * **The roof of the architect's set** (eighth round; `roof_v7` calls `bl/roof.py`, in plan
    feet). The concept's roof is removed and the sheets' roof built: every plane 5 in 12 (ten
    planes), the roof's surface 8.539 ft above the floor over the walls' outer faces, 1'-0" eaves
    and rakes ending in a plumb 6 1/2 in fascia whose top is at 8.122; the main hip's ridge at
    14.598 (the sheet prints 14'-7"), the garage's at 12.375 (12'-4 1/2"); level ridges over the
    bedroom wing (11.820) and the entry (12.602). The entry roof is a raised gable on two stucco
    cheek walls that runs on over the porch to 1'-0" past the slab, on the two piers, a tie beam
    and a king post, in place of the flat canopy. The wing's and the entry's ridges are centred on
    the wing and the foyer as built (the owner's foyer-side wall), not on the sheet's lines.
    The module also re-fits Bedroom 3's vault (8'-0" at the walls, 11.108 at the ridge) and the
    entry vault (level, 10'-11" at the ridge), builds the foyer's walls above 8 ft and the wall
    over the front door with W17's opening. Its pieces are named `v7 roof ...`. No sheet gives
    the entry ridge's height: it follows from SKA001's plan lines (`ENTRY_TIP_Z`).
  * **Skylights**, cut through that roof after it is built: the kitchen's W16, on the east roof
    plane over the sink where the owner put it, and the living room's W21, where the sheet draws
    it (`living_skylight`, eighth round), both the sheet's 1'-10" × 3'-10" (`SKY_W`, `SKY_L`;
    the kitchen's was 3'-6" × 4'-0" until the seventh round); two in the foyer (W18, W19); one
    over the primary bath's shower (W20). The kitchen's well is written from the east wall's face
    (`KITCHEN_SKY_EAST`, 9 1/2 in): its east edge stands where the wider opening's east edge
    stood, so the narrower well still lies over the sink's bowl (x 36.680..38.513).
  * **Laundry closet** (fifth round, `laundry_closet`): carved out of Bedroom 4's north-east
    corner, opening east onto the foyer, 2'-10" × 3'-0" inside. The revision cuts a 2'-6" × 6'-8"
    opening into the Bedroom 4 / foyer wall and builds the closet's west and south walls as copies
    of that wall, the baseboards, jamb liners, head trim, an oak threshold, a pair of leaves
    standing open against the foyer wall, and the recess for the washer outlet box. `bl/laundry.py`
    builds the stacked washer and dryer (facing east), hookups, vent, ceiling light and the leaves'
    hinges and pulls (collection `heg_laundry`). Bedroom 4 is L-shaped after it:
    `bl/zones/bedrooms.py` stands the desk in the niche beside the closet and dresses the closet's
    two bedroom faces (`bed4_closet_faces`, called by the revision after the warp). Numbers,
    naming rules and the fourth round's closet in the kitchen, which this one replaces:
    `DESIGN.md`, "Fifth round".
  * **Primary suite** (sixth round; `suite_rooms`, `suite_fit_out`; numbers `SUITE_*`). The 8 ft
    zone between the primary bedroom and the primary bath is divided as on the architect's sheet:
    the walk-in closet, an enclosed room (6'-1" × 8'-0") behind a 5 in wall with a sliding
    pocket door (D18, 2'-6" clear; its leaf is shown 0.30 ft out of the pocket, which leaves a
    2.23 ft passage: the sweep placement needs about 2.05 ft to reach the closet); the vestibule
    (4'-7" × 8'-0"), open to the bedroom, with the attic access hatch in its ceiling; and the
    suite entry (D09), 2'-8" clear, with a 3'-4" sliding panel on the hall side, parked south of
    the opening. Since the eighth round the entry stands at the sheet's place
    (`SUITE_ENTRY_SHEET_Z`); it stood 1'-8" south of it while Bedroom 2's entry alcove took that
    stretch of the hall. `bl/zones/primary_suite_rooms.py` builds the walls (copies of the
    bedroom / closet wall), doors, baseboards and the hatch, after `bath_door`.
    `bl/zones/primary_suite.fit_out` furnishes the bedroom as drawn (king bed on the west wall
    between the two west windows; W14 stays by the owner's decision although the sheet omits
    it, with W15's unit since the eighth round), the vestibule and the closet, and reports on the `revisions:` line anything in front of
    window glass, within 3 ft of the bedroom's east wall, in a door opening or in a wall.
  * **Bedroom 2's closet block and the hall** (eighth round; `hall_block`, `hall_block_fit_out`
    call `bl/zones/hall_block.py`; numbers in the block "v7 hall"). As on the sheet: the hall is
    3'-3" wide beside a closet block 7'-8" × 4'-8" over its walls and 3'-4" wide south of it; in
    the block Bedroom 2's closet (6'-10" × 1'-11", two sliding panels in a 6'-0" opening, D13),
    the furnace closet behind a louvred 1'-8" door (D19) and the storage closet behind a 2'-4"
    door (D20), both shown closed and empty; Bedroom 2 is entered through a hinged 2'-8" door in
    its south wall (D12); the shared bath has its hinged 2'-4" door with a leaf (D07). The
    concept's entry alcove, its doorless opening and the wall south of it are gone. The fit-out
    hangs Bedroom 2's closet and puts a 6 in ledge, a canvas and the lights into the hall.
  * **Bedroom 3 and Bedroom 4** (eighth round; `bedrooms_west_windows`, `bedroom3_rooms`,
    `bedroom3_fit_out` call `bl/zones/bedrooms_rooms.py` and `bl/zones/baths_suite3.py`; numbers
    in the block "v7 bedrooms"). Bedroom 3's bath as on the sheet: a 3'-0" shower across the west
    end, a 2'-6" toilet bay and a 2'-9" vanity bay on the north wall, a hinged 2'-4" door at the
    east end of its south wall (D05). Its closet is a reach-in behind two sliding panels in a
    4'-8" opening (D06); the two pocket doors are gone. Bedroom 3's entry (D03, 2'-8") is at the
    sheet's place, hinged on the north jamb; Bedroom 4's entry (D04) stays at the owner's place
    and gets a leaf of its own size. Bedroom 4's west window W12 is 5'-0", centred on its wall.
    **Bedroom 3's west window W10 is removed**, because the sheet has a solid wall behind the bed
    and the owner never decided on the window: `BED3_WEST_WINDOW = False` in
    `bl/revision_spec.py`. Set to `True`, the window builds as it did until the seventh round
    (4'-1 5/8" wide, sill 2'-6", head 7'-0"), with its shade and without the canvas over the
    bed, and the web data brings back its row, its grid and its texts by themselves.
  * **Garage and front door** (eighth round; `garage_v7` calls `bl/garage.py`, six steps that
    report under their own names; numbers `bl/garage_spec.py`, which
    `python3 tools/render/bl/garage_spec.py` prints). The garage floor lies 11 in below the house
    floor, with the step at the house door; the vehicle door's wall opening is the sheet's 15'-0"
    (`relayout.GARAGE_DOOR_RO`), the door 14'-10" between two jamb boards, its head 7'-0" above
    the garage floor; the door between house and garage (D02) is 3'-0", hinged on the north jamb,
    shown open into the garage; the side door in the east wall (D21) is 2'-4" in a 2'-8" opening,
    shown closed; the water heater is a 1'-8" tank on a stand in the north-east corner. The front
    door (D01) is a 3'-0" walnut leaf between two glazed sidelights (W22, W23): the unit takes the
    5'-9" foyer less 3 in of wall on each side, so the sidelights are 10 1/2 in between their
    frames where the sheet has 11 3/4 in. The north cabinet run is fitted into the plan's narrower
    garage (`relayout.X_GARAGE_RUN`) and stops short of the water heater
    (`garage_spec.CABINET_RUN_END_X`).
  * **Ground, landings, porch** (eighth round). The exterior zone builds the ground on A1.3's
    line (`exterior_layout.grade(z)`), the two ipe landings of SKA002 behind the sliding doors
    (13'-0" × 3'-0" and 7'-0" × 3'-0", `DECK` and `LANDING`; the first replaces the deck and
    keeps the object names `ext deck ...`), the porch slab, the front walk and the driveway
    (18'-1" wide, level from the garage slab to the sidewalk). The stucco runs down to a level
    line 5 in below the floor (`exterior_site.SCREED_Y`), with the foundation's concrete below
    it. What is still modelled on a level site at −0.60 (fences, plants, the street, the
    neighbourhood) is set down on the ground line by `exterior_site.settle()` at the end of the
    zone. `site_shell` closes the squares the exterior walls left open at six outside corners
    and takes out the porch's old paving at floor level.
  * **White windows with grid bars** (seventh round, `white_windows`; numbers `WINDOW_*`). The
    last step of `apply()`, and the one place that knows about it: on
    the built model every window, the two sliding glass doors and the front door's sidelights
    (29 panes in 18 grids on the eighth-round model) get the satin white `window_white` on their
    frame pieces and white bars on both faces of the glass, in lites as near 14 × 16 1/2 in as
    each sash allows. The five skylights keep their black frames. It also centres the mullion of
    W11, which the warp leaves off centre, and seats the roller shades on the room side of the
    bars. How to change a grid: "Change a window's grid"; the rule: `DESIGN.md`, "Seventh round";
    each window's grid: `WINDOW_GRIDS` in `apply_revisions_web.py`.

  **Built after the warp.** A room that must sit on the sheet's lines is not written on the
  concept plan, because the warp moves loose furniture in clusters and decides by name what is
  loose. For the primary suite, the primary bath and Bedroom 3's bath the zone's `build()` only
  registers the zone, and the revisions above build the rooms in plan feet; the hall block, the
  closets of Bedrooms 2 and 3, the garage's doors and floor and the roof are built the same way.
  Editing them: "Change a room's design". Decisions, numbers and departures from the sheet:
  `DESIGN.md`, "Sixth round" and "Eighth round".

  Changes made in the zones themselves:
  * The kitchen (`kitchen_dining_kitchen.py`; eighth round): counters 2'-0" deep and the island
    7'-0" × 4'-0" at the sheet's place, 3'-6" from the east counter's front and 4'-0" from the
    south counter's. The sizes are stated on the architect's plan (`PLAN_COUNTER_D`,
    `PLAN_AISLE_E`, `PLAN_AISLE_S`, `PLAN_ISLAND`) and carried back to the concept plan with the
    inverse of the warp's maps (`_px`, `_pz`); the island itself is built in plan feet
    (`_island`, `kitchen_dining_cabs.PlanFace`). `island_plan()` prints the built numbers on the
    `zone kitchen_dining:` line. The owner's kitchen decisions stay: the window over the sink,
    the sink, the cooktop, the refrigerator beside the microwave. No stools at the island.
  * The dining table (`kitchen_dining_dining.build_rect`) continues the island's west end, toward
    the hall and the shared bathroom (fifth round): 6'-0" × 2'-9", long axis east-west on the
    island's centre line, three chairs on each long side, none at the ends, no rug, the brass
    lantern over its middle. It follows the island (`_rect_centre`), so it moved west with the
    island's new end. The floor between the island and the living room, where the table
    stood before, is open.
  * The kitchen's south wall, west to east: the refrigerator's bay at the hall end, the oven
    tower, the counter under three glass-front uppers, the cooktop under the hood (the
    third-round layout). Since the seventh round the bay holds a visible stainless French-door
    refrigerator with a bottom freezer drawer under a two-door cabinet, and the tower a built-in
    microwave over one wall oven (`_refrigerator`, `_microwave`, `_wall_oven` in
    `kitchen_dining_kitchen.py`; `appliance_plan()` prints their built numbers on the
    `zone kitchen_dining:` line). The refrigerator is dimensioned in plan feet
    (`kitchen_dining_cabs.PlanFace`) and its parts are named `kd refrigerator ... panel`.
    `APPL_HANDLE` sets the handle finish of all three. The tall wall's fronts stand one door
    thickness in front of the 2'-0" counter line (`TALL_FRONT_S`).
  * The living room (seventh round, `living.py`, in plan feet under `TG living root`): no
    fireplace. The east wall is the shell's plain painted wall with its baseboard; the sofa
    stands against it and a 75 in television hangs on the west wall opposite, over a low oak
    console (`living_media.py`). Its openings come from the spec (`LIVING_SLIDER_X`,
    `LIVING_EAST_WIN_Z`). `build()` reports the layout's clearances on the `zone living:`
    line and lists in `notes` what does not hold: a piece through a wall, a sightline to the
    screen crossed, something in the sliding door's way or above the sill in front of the east
    window, a tour stop of `data/sweeps.json` closer than 1.2 ft to furniture. The list is empty
    on the eighth-round model.
  * Third round: Bedroom 4's bed is turned across the room (`bedrooms.build_bed4`), and the
    kitchen, the shared bath (`baths_shared.py`) and the garage door follow the owner's style
    images in `styles/`. Of the primary bath's third-round restyle the oak trough vanity
    remains; the sixth round replaced the rest.
* **Web data:** `apply_revisions_web.py` writes the opening list, the room notes and the change
  lists (`design_revision.owner_changes[_N]`; an entry that a later round overtakes is reworded
  to say so), and makes `scene.objects` follow the built walls.
  * **The schedule** (`data/measurements.json`; eighth round). A door's `start` / `end` / `width`
    are its clear opening between the jamb liners, frames or jamb boards, the size the sheet
    gives a door; `wall_start` / `wall_end` keep the cut in the wall, which `start` / `end` were
    until the seventh round. A window, a sidelight and the two sliding glass doors (W01, D14)
    keep the unit's wall opening; the sliding doors also carry `clear_start` / `clear_end`, and
    D14 its open way as `way_start` / `way_end`. `sill` and `head` are measured from the floor
    the opening stands on, and `floor` gives that level where it is not the house floor (the
    garage's vehicle door D15 and side door D21). 14 rooms, 20 doors, 19 windows. New in the
    eighth round: D19, D20 (furnace and storage closet), D21 (garage side door), W21 (living room
    skylight), W22 / W23 (the sidelights), M15 (Bedroom 2's closet). Gone: W03 and W04 (they and
    the garden door are the one sliding door D14), W06 (part of W05), W10 while
    `BED3_WEST_WINDOW` is `False`. `spaces` lists what the plan shows without a room tag (the two
    closed closets, the hall's two legs, the garage with its floor level and its step, the
    porch, the two rear landings); `overall` holds the outside sizes, the levels and the ridges.
  * **The scene** (`data/scene.json`). Wall boxes follow the build piece by piece: an existing
    object is reshaped in place and keeps its index (`reshape()` by name for the rounds up to the
    sixth; `Round8Scene` by index with the name checked, because the pieces of one wall share a
    name); a door that moves keeps its leaf object, moved in place; new walls, leaves, sliding
    panels, panes, the garage step, the porch slab and the landings are appended by name. A
    piece the build no longer has is marked `removed` and moves to the group `removed` (its old
    group is kept in `group_was`), since an index may not shift; `tools/web/dimension_plan.py`
    and `build_site_data.py` do not draw that group. Not mirrored in the scene: the new roof,
    the frames and hardware of rebuilt openings, baseboards and casings. On the round's final
    build the scene has 5,426 objects: 79 reshaped in place, 339 marked removed, 55 appended by
    the round (W14's two panes last, so that no earlier index shifts).
  * **Laundry closet** (from `LAUNDRY_*`): room M13 (2'-10" wide north to south, 3'-0" deep) and
    door D17 (a pair of leaves; 2'-5 1/4" between the liners of the owner's 2'-6" opening), while
    Bedroom 4 (M07) keeps its overall size and loses the closet and its two walls from its area.
  * **Primary suite** (from `SUITE_*`): room M05 is the walk-in closet and keeps its tag, the
    vestibule is room M14, D18 the closet's pocket door. The stops S0 and C0 are named after the
    two rooms (`NODE_NAMES`).
  * **Tour.** The tool sets the highlight reel (`HIGHLIGHTS`: `LC` after `B4`, `L8` as the
    "Living room" card, no `C3`), moves or drops seed stops (`NODE_MOVES`, `NODES_GONE`; see "Add
    or move sweeps"), adds the Design view `LC` when it is absent and prints a note when a
    hand-edited view of `data/design.json` still carries words of a superseded layout
    (`SUPERSEDED`). The Design views themselves are hand edits; there is no Design view of the
    living room (the hero still `living` goes to `assets/design/extra/`).
  * **Window grids.** The `type` of every window and of D14 says "white frame, white grid bars"
    and gives the grid as lites wide × high per sash. The grids are laid out on the built model
    by `white_windows`; the tool's table `WINDOW_GRIDS` repeats them and
    `--check-grids <build log>` compares the two. The concept's fireplace stays in
    `scene.objects` (nothing on the web side draws furniture); the tool stops if one of its
    objects is ever in a group that is drawn.
  * **Classification.** `scene_classification.json` gets the room regions of the eighth round
    (`bed2` without its alcove, `common_hall` from the hall's new north end, the new
    `bed2_closet`) and a record for every scene object. `classify_scene.py`, the concept's
    audit, is not part of the sequence.
  * `tools/web/dimension_plan.py` redraws the Dimensions sheet from the scene and the
    measurements: walls at the 4 ft cut, door leaves and sliding panels, the closets, hall
    widths, steps and landings of `spaces`, and the overall sizes measured on the drawn walls
    (39′11″ wide, 54′4″ deep on the west side, 53′0″ on the east).

## How the look is controlled

* **Daylight.** A Poly Haven sky HDRI with its own sun clamped out, plus a sun lamp (late morning,
  south-east: azimuth 128° clockwise from north, elevation 42°). The garden faces north (SCENE
  −z), the street south. The HDRI is turned until its bright side stands at the lamp's azimuth:
  the glow and the brightest clouds over the street, the deep-blue side over the garden. The
  rear facade, the two landings behind it and the near lawn are in the house's shade, and direct
  sun enters only through east and south glass and the skylights, never through the north-facing
  sliding doors or Bedroom 2's rear window. Window portals help interiors converge. Constants are
  in `bl/lighting.py`.
* **The sky is measured at build time.** Until the seventh round `_hdri_sun_rotation()` took
  the image's centre column for −X (Cycles puts it at +X), so the sky stood 180° off the lamp,
  with its glow in the north-west over the garden; no check caught it. `setup_daylight()` now
  ends with `check_sky()`: it renders the finished world alone (512 × 256, CPU, about a second,
  the clamp lifted so that the peak is the HDRI's sun), compares the brightest direction with
  the sun lamp object and prints
  `[lighting] sky check: sky bright side measured at azimuth 128.1 deg (elevation 48.0), sun lamp at 128.0 deg (elevation 42.0), clockwise from north; difference +0.1 deg (ok, tolerance 5)`.
  Both azimuths and the difference are stored on the world (`tg_sky_az`, `tg_sun_az`,
  `tg_sky_az_diff`), readable from the `.blend`. Above `SKY_CHECK_TOLERANCE_DEG` (5°) the line
  says `MISMATCH` and the build stops with a `RuntimeError` before the portals and before the
  `.blend` is saved, for the default HDRI and for the physical-sky fallback; with a caller's
  own `--hdri` it is only logged. If the measurement itself cannot render, the build goes on
  and prints `WARNING sky check could not run ... NOT verified`.
* **Light balance.** `lighting.apply_balance()` runs in every render script and scales the built
  scene at render time: fixture lamps ×0.12, emission shaders ×0.4, sky ×2 and sun ×2. The result is
  daylight-led, with the lights visibly on (a listing-photo look). Override per run with
  `--interior-gain / --emission-gain / --sky-gain / --sun-gain`.
* **Exposure and white balance per sweep.** A 512×256 probe (24 samples) sets the exposure: the median
  luminance of the horizon band maps to `TARGET_MEDIAN`. White painted surfaces (walls, ceilings,
  trim, white doors, stucco) are masked with a one-off emission-swap render; their median
  chromaticity (counted per pixel, so hot pools under downlights don't dominate) is brought to
  `WB_TARGET`, a slightly warm white, as a photographer would. `WB_NODE` fixes the balance of a sweep
  whose only white paint is lit by the room's own warm materials (the shared bath).
* **Smoothing along the graph.** The viewer cross-fades between linked sweeps, so the production run
  works in two passes. The probe pass writes the automatic values; `smooth_exposure.py` relaxes them
  so linked sweeps differ by at most 0.3 stop, 300 K and 6 tint (rooms keep one look, the change
  happens at doorways, no sweep moves more than 0.7 stop / 1200 K from its probe, and links between
  an indoor and an outdoor sweep are left alone); the final pass renders with those values pinned
  (`--pins`). On the fourth round's 43-sweep run the largest step between linked sweeps went from
  1.36 to 0.30 stops and from 1912 to 300 K. `render_meta.json` records both the values used and the
  automatic ones. `--move-kelvin` (default 1200) is how far a sweep's white balance may be pulled
  from its probe, and that limit wins over the link limit: `SMOOTH_ARGS="--move-kelvin 900"` if a
  room turns too warm (its links then stay further apart), a larger value when links stay open.
  The seventh round's run used `SMOOTH_ARGS="--move-kelvin 2600"`, which closed all 65 indoor
  links (1.38 to 0.30 stops, 1885 to 300 K). The outdoor sweeps' white balance is then pinned by
  hand to daylight ("Render everything again").
* **Colour pipeline.** AgX with the Base Contrast look. The web bake uses one house-wide exposure and
  white balance, the upper medians of the sweeps' values (`render_panos.house_look`).

## Web model contract (`bake_web.py`)

`bake_web.py --out house.glb --detail 2` groups the model by visibility class and plan region, one GLB
node per group, with `extras.tg_class`:

| `tg_class` | Contents | Inside | Dollhouse / floor plan | Exterior |
|---|---|---|---|---|
| `base` | Floors, foundations, built-ins, base cabinets, appliances (washer / dryer) | shown | shown, cut at the footprint | shown |
| `wall`, `glass` | Walls, trim, windows, doors, the house's garage door, wall tile; glazing | shown | cut at 7.45 ft (`DOLL_CUT` in `main.js`) and capped; the viewer's side culled | shown |
| `furniture` | Furniture and low decor | shown | shown | shown |
| `decor_high` | Wall art, uppers, mirrors, sconces (centre above 4.8 ft) | shown | shown | shown |
| `ceiling` | Ceilings, ceiling lights, pendants, skylight frames and shaft linings | shown | hidden (fades during a flight) | hidden |
| `exterior` | Roof, fascia, facade skins | hidden | hidden | shown |
| `landscape` | Grounds, the rear landings, fences, paths, the street and the neighbours | shown (through windows) | hidden | shown; "Hide garden" |

An object or a parent can force its class with a custom property `tg_class` (the primary bath's
wall finishes do: the stone, the shower tile and the tile base are `wall`). Name rules worth
knowing: anything named "door", "leaf", "jamb", "baseboard" ... is filed under walls (`WALL_PART`),
so the washer's round door is called "hatch"; objects named `laundry closet ...` are `base`; a
zone object named "cabinet", "closet", "vanity" ... is a built-in (`base`), so furniture and wall art
must not carry such a word; a material named "glass" is exported as a transparent pane.
A shell piece with a `scene_index` takes its class from the group of that object in
`data/scene.json`, so the bake wants the data sequence run for the same model (a built piece
whose index is marked `removed` there would be filed as `base`; the eighth round's data was
checked for that). Pieces without one: the roof (`v7 roof ...`, in `exterior_shell`) is
`exterior`; a revision-built `shell` piece that starts at 7.9 ft or higher, such as the foyer's
walls above 8 ft, is `ceiling` and hidden with the ceilings. Before baking, faces that can never
be seen are deleted; an upward face of a `base` piece below the floor of its place counts as a
foundation top, and that floor is the garage's 11 in lower level inside the garage
(`floor_level()` in `bake_web.py`, the rule of `check_holes.py`), so the garage keeps its slab
and its step.

* **Lighting** is the full Cycles result (GI, soft shadows, materials), baked into per-group atlases,
  saved display-referred and shown unlit by three.js. The fifth round's bake at `--detail 2` gave
  66 atlases (59 MP, about 315 MB of GPU texture memory as RGBA8 with mipmaps) in a GLB of about
  7 MB.
* **`--detail`** raises the texel density of floors / built-ins and furniture, because in the
  dollhouse and the floor plan the bake is the picture. `--tex-budget` (default 320 MB) caps the total;
  boosted atlases step down until it fits, so atlas sizes are not always powers of two.
* **Compression:** Draco geometry and WebP textures.
* **Metals:** a bake records diffuse light only, so each metal gets its diffuse equivalent (base
  colour, metallic 0). Mirrors and polished chrome get a mid silver-grey, so they don't come out black.
* **Black atlases:** an atlas comes out black when its UV islands cannot have the requested pixel
  margin (thousands of leaf-sized islands in a small atlas). The script measures every layout, steps
  the margin down, gives leafy objects one planar projection, and exits non-zero if a bake still
  wrote less than 2 % of an atlas.
* **Not baked:** vegetation. Lawn surfaces are baked in the grass blades' green (`lawn_green`), not
  the olive thatch under the blades.
* Next to the GLB: `<name>.summary.json` (size, texture memory, the exposure and white balance used),
  `<name>.bake.json` (per-group statistics) and, from a full bake, `collision.json` (unused).

## The page (`index.html` + `assets/js/tour/`)

`index.html` is markup only. The modules do not import each other: each exports one `create*`
function and `main.js` loads them with the release label, so a deploy never mixes old code with new
data. Each file starts with a comment that documents its interface.

| Module | Role |
|---|---|
| `main.js` | Boot, data loading, URL parameters, the link in the address bar, GPU budgets, the look of the dollhouse (`DOLL_CUT`, `DOLL_CAP`, `DOLL_TONE`) |
| `viewer.js` | Mode machine, the one animation loop, input routing, events, the sweep graph, panorama URLs. A mode is a controller (`enter`, `leave`, `depart`, `frame`, pointer / wheel / key handlers, `state`) |
| `engine.js` | three.js r170 on WebGL 2: draws the baked model unlit and projects panoramas and exterior frames onto it |
| `inside.js` | Sweep navigation: look, zoom, rings, cursor ring, hops, flights, panorama loading |
| `dollhouse.js` | Dollhouse and floor plan (one camera), and the flights between the views |
| `exterior.js` | Photoreal exterior orbit |
| `ui.js` | Toolbar, highlight reel, room chip, floor-plan names, landing page, sheets, menu, first-run hint, fallback |
| `dimensions.js`, `design.js` | Dimensions and Design sheets |
| `testapi.js` | `window.TOUR`, the contract with the tests |

* **Inside.** The camera rests only on sweeps, where the frame is the published panorama (one
  full-screen lookup, no geometry). Drag looks (inertia), wheel / pinch / `+` `-` zoom 35 to 80°.
  White rings on the floor mark the sweeps in view; a ring under the mouse lies on the surface it is
  over. A click on a ring, or toward a place, glides there in 0.55 to 1.1 s (350 ms + 55 ms per foot)
  while both panoramas are projected on the model and cross-faded; the look direction is kept. A
  double click is one move. Arrow keys / WASD step, left / right turn 45°. A destination out of view is
  flown through the sweeps between without stopping; more than five hops, or reduced motion, fade.
* **Panorama levels.** 2k on arrival if nothing better is loaded, 4k after 80 ms at rest, 8k after
  700 ms. The 2k level of the sweeps in view is loaded ahead and the nearest get their depth cube, so a
  hop starts at once; a move never waits more than 300 ms for a download. A missing level falls back
  to another one; the picture is never black and never the bare bake.
* **Budgets.** Desktop: one 8k, two 4k, twelve 2k panoramas and six 1024² depth cubes. Touch or
  low-memory devices: no 8k, one 4k, six 2k, four 512² cubes.
* **Dollhouse.** The baked model alone on a dark background; drag orbits, wheel / pinch zooms at the
  cursor, right-drag / Shift-drag / two fingers slide, `0` frames the house again. Dots mark the
  sweeps; a click flies in, to the dot under it or else to the nearest sweep of the room clicked (the
  smallest room of `tour.json` that contains the point). A room nobody can stand in (the laundry
  closet, the reach-in closets of Bedrooms 2, 3 and 4) is entered on the sweep in front of it,
  looking at the room.
  **Floor plan:** the same model in orthographic projection, north up, with the room names of
  `tour.json`.
* **Flights.** Inside ↔ dollhouse / floor plan is one camera move of 1.2 s: the ceilings fade, the
  sweep's panorama stays projected on the model and fades into the baked textures on the way out, and
  back in before the landing. Dollhouse ↔ floor plan takes 0.9 s. Exterior ↔ these views cross-fade.
* **Drawn on demand.** A view that stands still draws nothing, in every mode.
* **Links.** The address bar names the place the visitor is at, rewritten in place:
  `?sweep=ID&yaw=&pitch=` (degrees; `&fov=` when zoomed) inside, `?mode=dollhouse|floorplan|exterior`
  (`&view=front|left|rear|right|roof`) otherwise. Also `?pano=2k|4k|8k` (pin the level),
  `?exterior=model`, `?webgl=off` (show the fallback).
* **Chrome.** Title top left, round dark buttons bottom left (Rooms, Dollhouse, Floor plan, Inside) and
  bottom right (Exterior, Dimensions, Design, fullscreen, menu); a highlight reel of room thumbnails;
  a room-name chip on arrival; a one-line hint on the first visit. Sheets are modal for the keyboard.
  With `prefers-reduced-motion` nothing flies: moves fade, changes of view cross-fade.
* **No WebGL 2, or the model fails to load:** a static page with the design stills; Dimensions and
  Design still work. There is no second renderer. The page needs http(s); it does not run from `file://`.

**Engine in brief** (`createEngine(canvas, opts)`; SCENE feet, radians; it never fetches and never
runs a loop):

* `load(url)`, `setMode('inside'|'dollhouse'|'floorplan'|'exterior')`, `setBackground`,
  `setFootprint`, `render(view)` with `view = {eye, aim, fovY, ...}` or `{ortho: {halfHeight}, ...}`,
  `dirty()` / `invalidate()`.
* Sweeps: `setSweeps`, `setPanorama(id, image, level)`, `prepare(id)` (texture upload and depth cube
  ahead of a move), `setSweepBlend(a, b, t)` (deterministic; `setSweepBlend(id)` at rest is the pure
  panorama), `hasPanorama`, `setWanted`.
* `pick(ndcX, ndcY)` gives the surface point, normal and class under a pixel: from the resting
  sweep's depth cube inside, by ray cast in the dollhouse and floor plan.
* `overlay`: a `THREE.Group` in feet for rings and the reticle, depth-tested against the model, or
  against the depth cube at rest.
* Fly controls: `setProjectionFade`, `setClassOpacity('ceiling', a)`, `setAdaptation(k, ko, instant)`.
* The exterior orbit uses the older calls (`setPanorama(..., frame)`, `setProjection`,
  `applyVisibility`, `render(eye, aim, ...)`), which are kept.

Development harness: `tools/web/dev/` (see `tools/web/README.md`).

## Photoreal exterior (orbit frames)

The Exterior view orbits a fixed target. `render_exterior.py` renders perspective frames from orbit
positions the page can reach exactly:

* **Rings:** 24 frames at drone height (~50 ft, every 15°) and 8 roof-overview frames (~95 ft, every 45°).
* **Framing:** 90° horizontal, 3:2. That is wider than any screen, so a window of any shape is a crop
  of the frame.
* **Look:** one shared exposure and white balance, so neighbouring frames blend without a step.

The page (`assets/js/tour/exterior.js`) projects them onto the baked model:

* **Settling:** the camera settles on the nearest frame when you let go; a short drag moves one frame
  that way. On a frame the picture is that render.
* **Zoom:** zoom narrows the field of view from the frame position, so the view stays exact.
* **Occluders:** every occluder counts outside, and the depth cubes reach 700 ft.
* **Double-sided neighbourhood:** the neighbours' houses in the web model are partly inside out.
  Cycles renders both sides, so the bake never showed it. The Exterior view therefore draws the
  `landscape` class double-sided.

`?exterior=model` shows the baked model alone, and so does hiding the garden.

From the air the whole neighbourhood is in view. `bl/zones/exterior_far.py` fills it out:

* **Streets:** parallel streets every ~240 ft, laid out like the aerial photo of the street
  (`assets/references/img-3202.webp`; its 219 ft spacing is stretched to the site plan's 100 ft deep lot),
  cross streets, and street trees.
* **Lots:** about 1,250 ranch lots with houses, driveways, fences, backyard trees and the odd pool.
* **Horizon:** a tree belt to the horizon and the hills around the valley.

It lives in the `ext_far` collection, excluded from the view layer. Only `render_exterior.py`
switches it on, so the panoramas, hero stills and the web bake are unchanged.

The neighbouring houses' roof colours follow the aerial photo (`NEIGHBOUR_ROOFS` in
`exterior_context.py`): red-brown next door to the east, grey to the west, orange-tan behind.

## Review tools

| Tool | Purpose |
|---|---|
| `review.sh <blend> <sweeps\|all> <out> [width] [samples] [render args]` | Renders panoramas and 4-view contact sheets (`<ID>_sheet.png`); non-zero exit when one is missing |
| `dev_preview.sh <zones> <sweeps>` | Builds only some zones, then review renders |
| `top_view.py -- --rect=x0,x1,z0,z1 --out top.png` | Orthographic plan check (ceilings / roof hidden) |
| `whatis.py -- --node K0 --at y=90,p=-10` | Names the object, material and owning zone at a view direction |
| `pano_views.py PANO --base-yaw R --yaws 0,90` | Cuts rectilinear views out of an equirect |
| `check_holes.py` | Holes in ceilings and floors, floor seams, baseboards without a wall |
| `place_sweeps.py ... --overlay sweeps.png` | Top-down picture of clearance, furniture, walls, links and sweeps |
| `check_glb.py <glb> <out.png> [hide] [view]` | Quick unlit render of a baked GLB |
| `gpu.sh <blender args>` | Runs a Blender GPU job under a machine-wide lock |

## Files

* **`bl/` modules:**
  * `common.py`: scene context and geometry helpers.
  * `shell.py`: exact architecture with modern finishes.
  * `warp.py`: concept plan to architect's plan, inside Blender.
  * `revision_spec.py`, `garage_spec.py`: the numbers of everything built after the warp, pure
    Python, written from `relayout.py`'s wall faces.
  * `revisions.py`: the owner's changes and the sheet's layout, after the warp; with it
    `laundry.py` (the laundry closet's contents), `zones/primary_suite_rooms.py` (the primary
    suite's walls and doors), `zones/hall_block.py` (Bedroom 2's closet block, the hall, the
    doors round it), `zones/bedrooms_rooms.py` (Bedroom 3's and 4's doors, west windows, Bedroom
    3's closet), `garage.py` (garage floor, step, doors, water heater, the front door unit) and
    `roof.py` (the roof, the vaulted ceilings under it, the porch's frame).
  * `lighting.py`: sky, sun, the sky check, portals, fixtures and balance.
  * `materials.py` + `materials_pbr.py`: material library (`KEYS` contract).
  * `assets.py`: Poly Haven fetch, cache and attribution.
  * `zones/<zone>*.py`: one module family per area (kitchen_dining, living, primary_suite, bedrooms, baths,
    hall_entry_garage, exterior). `primary_suite.py`, `baths_primary.py` and `baths_suite3.py`
    build after the warp, in plan feet; `living.py` is in plan feet too, under a root the warp
    skips; `exterior_layout.py` holds the site plan and the ground levels.
* **`data/`** (read and written through `tools/web/sitedata.py`):
  * `scene.json`: the tour's full scene. `sweeps.json`: the sweeps (`place_sweeps.py`).
  * `measurements.json`: the dimension schedule. `design.json`: Design sheet views, text, image paths.
  * `primitives.json`: unit primitives; static; the Blender build (`bl/common.py`) reads it.
  * `scene_classification.json` + `room_inventory.json`: room regions and roles
    (`apply_relayout.py` and `apply_revisions_web.py` write the first).
  * `hero_cameras.json`: cameras of the hero stills.
  * `concept/`: the frozen concept plan (scene, measurements, classification).
* **`sheet_check/`**: `extract.py`, `measure.py`, `cq.py` and the sheet as data: the built model
  measured against SKA002 ("Verify", step 3).
* **Data tools:** `relayout.py` (the sheet's frame and the map onto it), `apply_relayout.py`,
  `apply_revisions_web.py`, `apply_sweeps.py`, `extract_scene.py` (check); in `tools/web/`,
  `dimension_plan.py` and `roof_drawing.py` (the two drawings). `classify_scene.py` is
  the original scene audit that assigned rooms and roles, in concept feet; it overwrites the
  classification files and is not part of the sequence.
* **Render tools:** `build_scene.py`, `place_sweeps.py`, `render_panos.py`, `smooth_exposure.py`,
  `render_heroes.py`, `render_exterior.py`, `bake_web.py`, `adapt_web.py`, `final_run.sh`.
