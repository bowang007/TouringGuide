# tools/web: site data, publishers, tests

The page (`index.html` + `assets/js/tour/`) holds no data. Everything it loads is a file written by
one of the tools here. The render side (the Blender build, the production run, the order of a
release) is in `tools/render/README.md`; this file covers what happens between `tools/render/` and
`assets/`.

## What the page loads, and who writes it

| File | Written by | From |
|---|---|---|
| `assets/data/tour.json` | `build_site_data.py` | `tools/render/data/scene.json` (tour, extent, foundations), `measurements.json`, `scene_classification.json` |
| `assets/data/measurements.json` | `build_site_data.py` | `tools/render/data/measurements.json` (rooms, doors, windows, and since the eighth round `spaces` and `overall`) + the `audit` rows of the scene |
| `assets/data/design.json` | `build_site_data.py` | `tools/render/data/design.json` + the owner's change lists of the scene |
| `assets/plans/dimension-plan.svg` | `dimension_plan.py` | scene (walls, door leaves and sliding panels, foundations) + measurements (rooms, openings, `spaces`) |
| `assets/panos/{8k,4k,2k}/<ID>.webp`, `assets/panos/manifest.json`, `assets/thumbs/<ID>.webp` | `publish_panos.py` | `tools/render/.cache/panos/<ID>.png` |
| `assets/design/<key>.webp` | `publish_design.py` | `tools/render/.cache/heroes/<key>.png` |
| `assets/design/roof.svg` | `roof_drawing.py` | the roof's planes and lines (`tools/render/bl/roof.py`), the skylights (`bl/revision_spec.py`), the walls' outer faces (`relayout.py`) |
| `assets/exterior/` (frames, `half/`, `manifest.json`) | `publish_exterior.py` | `tools/render/.cache/exterior/` |
| `assets/model/house.glb` | copied by hand | `tools/render/.cache/web/house.glb` |

Each tool documents its formats and options in the docstring at the top of its file.

## Site data

`sitedata.py` is the one helper every data tool uses: the canonical paths, loaders and savers. A save
is atomic and happens only when the bytes change, so re-running a tool on unchanged data touches
nothing.

```bash
python3 tools/web/sitedata.py                           # status: files, sizes, counts
python3 tools/web/dimension_plan.py [--check]           # the plan drawing
python3 tools/web/roof_drawing.py [--check]             # the Design sheet's roof drawing
python3 tools/web/build_site_data.py [--version V] [--check] [--out DIR]
```

* **`build_site_data.py`** writes the three runtime files and prints the footprint and the room
  table. It checks walls, rooms and sweeps against the footprint and exits 2 on a problem.
  `--check` writes nothing and exits 1 when a file is out of date. `--version V` sets the release
  label in the three files and stamps `?v=V` on the site's own files that `index.html` names; that is
  the only place a tool writes to `index.html`.
* **`tour.json`** (SCENE feet; x west to east, y up, z north to south): `version`, `title`, `eye`,
  `extent`, `start`, `footprint` (at most 16 rectangles whose union is the house outline, the
  engine's limit; the canted bay becomes a fine staircase), `sweeps` (`id, label, room, p, floor,
  yaw, pitch, links, visible, outdoor`; angles in **degrees**, yaw 0 = north, clockwise), `rooms`
  (`id, label, bounds, at, sweep, tag`: the measured rooms, then living, kitchen + dining, hall and
  garage) and `highlights` (the reel: the entrance first, each caption once; a card opens its
  sweep at the sweep's own `yaw` and `pitch`, the view its thumbnail shows). A room nobody can
  stand in, such as the laundry closet or the reach-in closets of Bedrooms 2, 3 and 4, owns the
  sweep in front of it. A room may lie inside
  another room's rectangle (the closet is cut out of Bedroom 4, whose entry stays a rectangle): a
  sweep belongs to the smallest room that contains it, and any other lookup by position has to
  choose the same way. A sweep that stands in no room stands in a doorway, in the thickness of
  the wall between two rooms (`Y0` and `Z0` in the doors of Bedrooms 3 and 4 since the eighth
  round): it belongs to the room it is named after when that is one of the two, else to the
  nearest. There are 53 sweeps and 18 rooms (since the eighth round): the 14 rooms of the
  schedule, then living room, kitchen + dining, hall and garage. The primary suite's walk-in
  closet keeps the id `primary_dressing` (tag M05, sweep
  `C0`) from the open area it replaced, and the vestibule beside it is `primary_vestibule` (M14,
  sweeps `S0`, `S1`); Bedroom 2's closet is `bed2_closet` (M15, seen from `B2`), and Bedroom 3's
  closet (M10) is seen from `B3` since its own stop `C3` went. The furnace and storage closets
  are not rooms of the tour: as rooms they would take over the hall sweep in front of them. An
  open space (living room, kitchen + dining, hall, garage) is entered on
  the reel's card of its own name when that card stands in it, else on the sweep `OPEN_ROOMS`
  names: the living room on `L8` since the seventh round, so a click on its name in the floor
  plan opens the picture the reel shows.
* **Levels and eye heights** (eighth round). A sweep's `p[1]` is its own eye height, 5.0853 ft
  above the level it stands on: lower in the garage (4.169; the floor there is 11 in below the
  house floor), on the porch slab (4.627) and on the rear landing (5.002). An outdoor sweep's
  `room` is its own key, `porch` or `deck`: the stop on the rear landing keeps the key it was
  published with, and its `label` is "Rear landing" since the eighth round. `eye` is the median of the
  indoor sweeps, 5.0853. `floor` is the surface under the stop (rug, tile, slab), where the page
  draws its ring.
* **`measurements.json`** (the schedule). A door's `start` / `end` / `width` are its clear opening
  (between the jamb liners, frames or jamb boards), `wall_start` / `wall_end` the cut in the wall;
  windows, sidelights and the two sliding glass doors keep the unit's wall opening, and the
  sliding doors add `clear_start` / `clear_end` (D14 also `way_start` / `way_end`, its open
  way). `sill` and `head` are measured from the floor the opening stands on; `floor` gives that
  level for the garage's vehicle door and side door. `spaces` lists what the plan shows without
  a room tag (closets nobody enters, the hall's two legs, the garage's floor level and step, the
  porch, the rear landings) and `overall` the outside sizes, levels and ridge heights. The plan
  drawing reads `spaces`; it measures the overall sizes on the drawn walls.
  The Dimensions sheet shows all of it: for a door the wall opening beside its clear width, for a
  sliding glass door the clear width between its jambs and the way as shown open, for the
  garage's doors the floor they stand on; under the rooms a table "Closets, levels and landings"
  with every entry of `spaces` and its floor level; in the footnote the outside size from
  `overall`. "Visit in 3D" from an opening stands on the opening's `node` and turns toward the
  opening (`MEASURE.lookAt`), unless that sweep's own view already faces it.
* **`design.json`** (`tools/render/data/`) is hand-edited: tab order, and per view `label`, `title`,
  `text`, `refs`, `node`, `opening`, `image`. The view `roof` shows a drawing instead of a still:
  `roof_drawing.py` writes `assets/design/roof.svg` from the model's own modules (the ten roof
  planes with their ridges, hips and valleys, the eaves, the walls under them, the five
  skylights), so it is run again after a change to the roof or to a skylight; `--check` exits 1
  when the file is out of date, `--lines FILE` writes the drawn geometry for a check against a
  built model.
* **Release label.** `tour.json` is fetched without caching and names the release; the page appends
  it to the modules, the other data files, the model and the Design images. Panoramas and exterior
  frames carry the content hash of their own manifests.

### Rehearsing in a scratch root

Every tool here reads and writes under one root: `$SITEDATA_ROOT` when set (the publishers also take
`--repo ROOT`), else the repository. A root is any directory with the repository's layout. With a copy
of `tools/render/data` in it, the data tools run there without touching the checkout:

```bash
R=/tmp/tour-root; mkdir -p $R/tools/render $R/assets && cp -r tools/render/data $R/tools/render/
SITEDATA_ROOT=$R python3 tools/web/dimension_plan.py
SITEDATA_ROOT=$R python3 tools/web/build_site_data.py
```

`build_site_data.py --out DIR` alone builds the three runtime files from the checkout's data into
another directory; it never opens `index.html`, also with `--version`.

To look at the result in a browser, complete the root and serve it on another port:

```bash
cp index.html $R/                                   # a copy: --version rewrites its ?v= tokens
for d in js css model vendor design references exterior; do ln -s $PWD/assets/$d $R/assets/$d; done
cp -r assets/panos assets/thumbs $R/assets/         # copies: the publisher writes into them
(cd $R && python3 -m http.server 8766 --bind 127.0.0.1)
```

A new sweep has no panorama until the render is published, and a moved one still shows its old
place. For the rehearsal give each a stand-in: any `<ID>.png` equirect, for example a
low-resolution review render enlarged to 8192×4096 (a narrower source gets fewer levels; one under
2048 px is published as it is, and `data.test.js` then reports its width; the publisher's seam
warning on an enlarged picture can be ignored). Publish them into the root and stamp the root
with a label of its own (the id is the eighth round's new sweep):

```bash
tools/render/.cache/venv/bin/python tools/web/publish_panos.py <stand-ins> --repo $R --only H5
SITEDATA_ROOT=$R python3 tools/web/build_site_data.py --version rehearsal
```

A sweep that left the tour (the eighth round's `C3`) is dropped from the root's manifest by that
call; its files stay until `--prune`. A sweep whose opening view changed (`A3`, `K2`) keeps its
old thumbnail until its own panorama is published again.

The model, the Design stills and the exterior frames of such a root are still the published ones:
the dollhouse and the floor plan show a rebuilt room as it was, under its new name, and a move
projects the new panoramas onto the old walls. After a round that changes levels this shows in
the tests too: in the eighth round's rehearsal the rings of the garage sweeps lay on the new
garage floor, 11 in below the floor of the published model, and `nav.test.js` could not reach
`G0` to `G3` by ring clicks. Such a failure says nothing until the model is baked from the new
build. For such a round bake a stand-in from the new build (about 10 minutes on the GPU) and
make `assets/model` of the root a copy instead of a link:

```bash
tools/render/gpu.sh -b tools/render/.cache/<build>.blend -noaudio --python tools/render/bake_web.py -- \
    --out /tmp/standin/house.glb --bake-dir /tmp/standin/atlases --texel 24 --detail 1 --samples 48 \
    --tex-budget 160 --max-atlas 2048
rm $R/assets/model && mkdir $R/assets/model && cp /tmp/standin/house.glb $R/assets/model/
SITEDATA_ROOT=$R python3 tools/web/build_site_data.py --version rehearsal     # the model's hash goes into tour.json
```

The browser tests about levels ("a lower floor", "a room whose floor lies below the house floor")
hold the model to the data: they fail when one of the two is ahead of the other.
To run the test suite against it, copy `tools/web/tests` (without `node_modules` and `out`) into
the root as well, because `data.test.js` reads the files of the tree it runs from. Run it there with
`TOUR_BASE=http://127.0.0.1:8766`, after `npm install` or with `NODE_PATH` set to a `node_modules`
that holds puppeteer-core.

## Publishers

Run them with the render venv (numpy + Pillow), from the repository root:

```bash
PY=tools/render/.cache/venv/bin/python
$PY tools/web/publish_panos.py tools/render/.cache/panos [--only K0,LC] [--prune]
$PY tools/web/publish_design.py tools/render/.cache/heroes
$PY tools/web/publish_exterior.py tools/render/.cache/exterior [--prune]
```

* **`publish_panos.py`** writes the three levels (8k only from a source at least 8192 px wide; WebP
  quality 84 for 8k, 88 for 4k and 2k), a thumbnail at the sweep's own opening view, and the manifest
  (`widths`, and per sweep `offset`, `levels`, `thumb`). Smaller levels are Lanczos-downsampled with
  the 0/360 seam wrapped; a faint column the renderer leaves at the seam is repaired first. Sweeps
  not in the input keep their entry. Entries of sweeps that left the tour are dropped; their files,
  and any other stray `.webp` in the level folders and `thumbs/`, are deleted only with `--prune`.
  Exit code 1 when a sweep of the tour has no panorama afterwards (`--allow-missing` while a render
  is still running).
* **`publish_design.py`** writes `assets/design/<key>.webp` (1600 px) for the design views that name
  such an image and puts the other stills in `assets/design/extra/`. Exit code 1 when a view's
  picture is missing.
* **`publish_exterior.py`** writes the frames at full and half size and the manifest with each
  frame's orbit position.
* `assets/model/` holds `house.glb` only. `adapt.json` and `collision.json` in `.cache/web/` are
  leftovers of the earlier free-walk page; the page requests neither (a test checks that).

Publish the data last (`build_site_data.py --version <new label>`): the page expects a panorama for
every sweep `tour.json` names.

## Mirror for visitors who cannot reach GitHub Pages

`github.io` is unreliable from mainland China. `deploy_mirror.sh` uploads `index.html` and `assets/` (nothing else)
to a second host:

```bash
tools/web/deploy_mirror.sh --dry-run     # build the upload folder, print file count and size, send nothing
tools/web/deploy_mirror.sh               # upload to https://mckinley-house-tour.netlify.app
```

* **Netlify** (default, in use): needs no domain; sign in once with `npx netlify-cli@17 login`. The site's
  "team login protection", which new free accounts switch on for every site, is off for this site. The free plan
  shows a "Powered by Netlify" badge in the lower right corner; on `*.netlify.app` the page lifts its controls
  clear of it (`main.js` sets `.host-badge`, `tour.css` raises `--bottom`). A `netlify.app` address was reachable
  from most mainland test locations in mid-2026 but can be slow: have someone there try it.
* **Tencent EdgeOne Pages** (`MIRROR_HOST=edgeone`, not set up): needs an API token and a domain name added to the
  project; its own address serves mainland visitors only through preview links that expire after 3 hours.

Run the script after every publish; GitHub Pages stays the address for everyone else.

## Tests

```bash
python3 -m http.server 8765 --bind 127.0.0.1            # in another terminal, from the repository root
cd tools/web/tests
npm install                                             # once: puppeteer-core only
npm test                                                # the whole suite, about 13 minutes
npm run test:quick                                      # tools + data + smoke + rest, 30 s
npm run test:igpu                                       # everything on the integrated GPU
node --test data.test.js                                # the data checks alone, no browser
```

`TOUR_CHROME_ARGS` holds Chrome's GPU flags. The default
(`--use-angle=vulkan --enable-gpu --ignore-gpu-blocklist --enable-features=Vulkan`) uses the discrete
GPU; `--use-angle=gl-egl` (what `test:igpu` sets) uses the integrated one and is the choice while a
render is running. `TOUR_BASE` names another server, `TOUR_OUT` another output directory. What each
file covers, how "the frame equals the panorama" is measured and how to write a test:
`tests/README.md`.

`data.test.js` compares `assets/data`, the panorama manifest, the files on disk and the plan
drawing. It fails while they are out of step, for example after the data tools ran and before the
panoramas of new sweeps are published.

**Eighth round, as published:** release label `2026-11-25a`; the whole suite (`npm test`):
168 of 168 tests pass on the published tree (2026-11-25, 53 sweeps, 70 links; 13 min 47 s).

## Engine harness (`dev/`)

The engine's call reference (options, methods, units) is `assets/js/tour/ENGINE.md`; how it works is in the header
comment of `assets/js/tour/engine.js`.

`dev/engine_harness.html` loads `assets/js/tour/engine.js` alone, without the page
(`?demo=inside&sweep=K0`, `?demo=doll`, `?demo=plan`). `dev/run_engine_checks.js` drives it:

```bash
(cd tools/web/tests && npm install)                     # puppeteer-core, once
NODE_PATH=$PWD/tools/web/tests/node_modules node tools/web/dev/run_engine_checks.js --out /tmp/engine-checks \
    [--only rest,blend,pick,doll,plan,fly,overlay,levels,dirty,perf,exterior] [--gpu egl|vulkan|swiftshader]
```

It needs the same server on port 8765 (`--base` names another) and uses the integrated GPU unless
`--gpu vulkan` is given.

The runner compares the resting frame with the panorama file, checks moves for bake or black pixels,
picking against ray casts, the dollhouse and floor plan, the exterior view against its frame files,
and frame times. It writes `report.json` and screenshots, which still have to be looked at.

## Legacy one-offs

`update_copy.py` (the Design texts of the first restyle; reports only, unless `--force`) and
`extract_assets.py` (moved the embedded assets out of the old single-file page) are kept for the
record. Nothing in the pipeline calls them. `sitedata.py --seed git:ed664e0` recreates a missing data
file (for example `primitives.json`) from the last single-file page. `--compare` was the proof that
the move out of `index.html` lost nothing; the data has moved on since, so it no longer matches.
