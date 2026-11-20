# 1095 W McKinley: modern photoreal restyle (design brief and code contract)

The tour's panoramas are path-traced in Blender/Cycles from the **exact** remodel geometry: the
architect's plan (`sizes/sizes.pdf`, sheet SKA002) plus the owner's changes. The architecture (walls,
openings, ceilings, vaults, roof massing, every dimension in the Dimensions sheet) is fixed. What we
design is the **look**: finishes, fixtures, furniture, lighting and landscape. The design language
comes from the neighbouring modern new build at 1077 W McKinley Ave; the owner's rounds below override
it where they say so. How to run things is in `README.md`.

| Round | Date | What changed | Where it is described |
|---|---|---|---|
| First | 2026-11-17/18 | Modern restyle; the architect's plan replaces the concept plan; the owner's first changes (flat ceiling in Bedroom 4, glazed bay, skylights, garden door, tall windows) | "Design language" below; `README.md`, "Architect's plan and the owner's changes" |
| Second | 2026-11-19 | Aligned foyer wall, shower skylight, seam repairs | `README.md`, same section |
| Third | 2026-11-19 | The owner's style images; Bedroom 4 bed turned; 2 ft window sills; grounded baseboards | "Owner's style images" below |
| Fourth | 2026-11-19 evening | Matterport-style tour; laundry closet | "Fourth round" below |

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

## Owner's style images (third round, 2026-11-19)

The owner's reference photos in `styles/` (reference only; never copied into the site) override the
language above in four places:

- **Kitchen** (`kitchen_dining_*.py`): warm vintage-American in soft layered neutrals. Cream shaker
  cabinetry with unlacquered brass cup pulls and knobs, glass-front uppers and a greige pantry wall
  with a panelled fridge. A cream plaster hood with a dentil band over a scalloped marble splash and
  a brass pot filler; walnut open shelves on whitewashed brick. A fireclay farmhouse sink under a
  black grid window with brass sconces and linen cafe curtains. A white-oak island with a honed
  quartzite top, brass pendants, a Persian runner, and a warm oak dining set under a brass lantern.
- **Primary bath** (`baths_primary.py`): a sage subway-tile shower with aged-brass fittings, a floating
  solid-oak double vanity with carved basins, brass mirrors and sconces, a sage V-groove wainscot under
  cream plaster, a stacked-stone wall and a blue-and-cream encaustic floor.
- **Shared bath** (`baths_shared.py`): a rustic-oak wood-look tile wall with a lit niche behind the WC,
  warm Spanish-cream stone-look porcelain, a light-oak vanity with a travertine trough basin and a
  limestone-look floor.
- **Garage door** (`exterior_garage.py`): a stained-cedar carriage-house door with a top row of glass
  lites, flanked by black coach lanterns.

## Fourth round (2026-11-19 evening): Matterport-style tour and the laundry closet

The owner's request: the tour "feels very unreal" compared with a day earlier; rebuild it as needed to
feel like a Matterport space; and add a small room "on the right of Bedroom 4" for a stacked washer
and dryer, sized to fit them just right.

### Why the tour looked unreal

The page let the camera rest anywhere ("walk freely") and showed the two nearest panoramas projected
onto the baked model. Standing exactly on a stop, that picture equalled the path-traced panorama
(PSNR 49 to 56 dB). 1.5 ft off a stop it fell to 15 to 19 dB: two panoramas on a simplified mesh double
and smear everything thin, and the third round had just filled the rooms with thin things (pendants,
plants, glass-front cabinets, window muntins). A Matterport tour never rests between sweeps. Three
smaller causes: the panoramas were 4096 px wide (11 px per degree, soft on a desktop; the reference
serves about 23), a hop took up to 2.7 s, and the top view was the raw bake with a neon lawn and black
neighbours.

### The redesign and its rules

1. **The camera rests only on a sweep, and there the frame is the panorama itself.** No free walking,
   no touch pad, no minimap, no guided tour, no second renderer. Requirement: at rest PSNR ≥ 40 dB
   against the published file (measured 55 to 61 dB).
2. **Many sweeps, short hops.** Sweeps are placed by a tool on the built model (rules below), about
   4 ft apart with at least 1.2 ft of clearance: 43 instead of 27. Soft white rings on the floor mark
   the sweeps in view; a cursor ring lies on the surface under the mouse.
3. **A click moves.** To the ring clicked, else to the sweep that best matches the clicked point or
   direction. A hop takes 0.55 to 1.1 s (limit 1.2 s), eased, with both panoramas projected on the
   model and cross-faded while the camera glides. The look direction is kept. Far targets are flown
   through the sweeps between without stopping.
4. **Sharper panoramas.** 8192×4096 (23 px per degree), published as 8k / 4k / 2k; the page shows the
   best level the device can hold.
5. **One look along the way.** Because linked sweeps are cross-faded, their exposure and white balance
   are smoothed along the graph (within 0.3 stop and 300 K across a link).
6. **Dollhouse and floor plan are the baked model, house only**, on a dark background: no lawn,
   neighbours, roof or ceilings; the walls on the viewer's side are culled; the floor plan is the same
   model straight down in orthographic projection with room names. Going between the inside view and
   these is one continuous camera move.
7. **Minimal dark chrome**, like the reference: a small title, round translucent buttons, a highlight
   reel of room thumbnails, a room-name chip on arrival.
8. **Kept:** the landing page, the photoreal exterior orbit, the Dimensions sheet (the architect's
   numbers) and the Design sheet.
9. **Structure.** `index.html` is a shell without data; the data lives in JSON files written by the
   tools through one helper (`tools/web/sitedata.py`); the page is a set of ES modules; no tool patches
   `index.html` any more (except the `?v=` release tokens).
10. **The requirements are executable.** `tools/web/tests` compares the resting frame with the view cut
    out of the published panorama on the CPU (independent of the engine), times hops inside the page,
    walks the sweep graph by ring clicks and counts texture memory.

Where the build departs from the first plan, on purpose: 43 sweeps, not 45 to 50 (the default 4 ft
spacing; the closet makes the foyer's north end a tight cell); the kitchen stop K0 moved 1 ft, because
the closet's open door leaf would have filled a quarter of its panorama; walls in the dollhouse are cut
at 7.45 ft, below the skylight wells, not at 8 ft; the near-wall rule steps 0.9 ft, not 0.6 (the garage
door's panels sit 0.62 ft inside the outline); there is no double-click zoom, because a click always
moves.

### Laundry closet (the architect's sheet SKA002)

The sheet already draws "W / D" directly right of "(N) OFFICE" (the tour's Bedroom 4) across the
foyer's north end: in the kitchen's south-west corner, against the kitchen / garage wall, its west wall
continuing the garage's west wall line north, "REF." immediately east of it, then the range. It is
built exactly there. All numbers are in `bl/revision_spec.py` (`LAUNDRY_*`, new-plan SCENE feet); the
Blender revision, the kitchen zone and the web data all derive from them.

- **Position and size.** 3'-10" (east-west) × 3'-5" over the walls, as printed on the sheet:
  x 21.218..25.051, z 27.641..31.058. Walls 0.36 ft. Clear inside 3'-1 3/8" × 3'-0 5/8"
  (x 21.578..24.691, z 28.001..31.058; 9.52 sq ft) under the flat 8 ft ceiling. The west and east walls
  are new; the back is the existing kitchen / garage wall. A small infill closes the old notch at the
  garage wall, so the foyer's east face is one plane from the closet corner to the garage door.
- **Door (D17).** In the north face: opening x 21.8845..24.3845 (2'-6"), head 6'-8". A white flush
  slab like the other interior doors, hinged on the **east** jamb, swinging north as drawn, shown open
  90° so the units are seen from the hall and the dining side (leaf at x 24.22..24.34,
  z 25.17..27.59). Painted jamb liners and head trim, black lever sets, three hinge knuckles.
  `revision_spec.laundry_leaf(open_deg)` turns the leaf about the hinge-pin axis, and
  `bl/laundry.door_hardware` places knuckles and levers from it, so any angle stays consistent.
- **Units.** A stacked front-load pair, washer below and dryer on top, each 27 × 30 1/4 × 39 in, centred
  (0.43 ft free on each side, 0.40 ft behind for hoses and the vent), with a stacking trim between.
  Modelled procedurally in `bl/laundry.py` (round hatch with a chrome ring and dark glass, control
  strip with a lit display, detergent drawer, kick panel). They are generic models of a typical pair,
  not a selected product, and the Design sheet says so.
- **Services.** A recessed outlet box in the back wall (x 21.70..22.36, y 3.50..4.10, 0.24 ft deep) with
  valves and hoses, the dryer's vent duct to a wall collar at 7.25 ft, a 240 V receptacle, a flush
  ceiling light. The oak floor runs in without a threshold.
- **Kitchen south wall, re-planned to match the sheet**, west to east: closet (east face x 25.051) |
  scribe filler | 36 in panelled fridge (x 25.111..28.111) | oven tower (to 30.455) | one drawer base
  under one glass-front upper (30.515..32.164) | cooktop under the hood (32.164..35.049, unchanged) |
  base run to the corner. Before, the fridge stood at x 21.90..24.82 and the ovens at 24.87..27.12.
  The pantry wall's crown dies into the closet wall.
- **In the tour.** Room M13 and door D17 in the Dimensions sheet, the closet's walls and open leaf on
  the plan, a Design view and a hero still (`LC`), and the sweep `LC` in front of the door: at the
  clear cell nearest to (23.1, 24.5), facing the door and pitched down toward 4.05 ft on the door
  plane (about −18°), so its opening view shows both units.
- **Limits.** From the kitchen side the open leaf hides the units (hinge east, as drawn); they show
  from the dining side and from the hall. On the sheet's raster the door scales to about 2'-4"; the
  2'-6" of the brief was built.

Naming rules the closet depends on: its contents are named `laundry closet ...` (the bake files them
as `base`, the sweep placement looks for `laundry` / `washer` / `dryer`); nothing with a glass-named
material goes into the `openings` collection (it would get a light portal); appliance parts are not
named "door" (the bake files those under walls), hence "hatch".

### Sweep placement (`place_sweeps.py`)

- **Standable cell** (0.25 ft grid): a ray down from eye height (5.0853 ft) lands at y −0.03..0.15 ft
  and a ray up hits a ceiling. Clearance = the nearest surface in 16 directions at 0.6 / 2.0 / 3.5 ft
  and eye height, limited by the distance to the nearest cell with furniture below the eye.
  Reachable = flood fill from the existing stops over cells with ≥ 0.9 ft clearance.
- **Rules:** clearance ≥ 1.2 ft (≥ 0.8 ft only for a seed or a room that would otherwise have no
  sweep); ≥ 4 ft between sweeps that see each other, ≥ 3 ft for doorway, bridge and kept approach
  sweeps; a cell with < 1.5 ft clearance that is not the middle of a passage needs ≥ 5 ft; at most 4 in
  the garage; every room region with standing room has a sweep.
- **Seeds** (E0 H1 H2 H3 B3 B4 K0 D0 L0 L1 L2 P0 S0 C0 A0 B2 A1 G0 A3 C3) keep their id and position;
  one with less than 1.2 ft clearance is nudged by up to 1.5 ft. A stop the model no longer suits is
  moved in `apply_revisions_web.py` (`NODE_MOVES`), not in `sweeps.json`: `apply_relayout.py` rebuilds
  the stops from the concept plan and the placement keeps a seed where the scene has it.
- **Link** = a straight line up to 11 ft that a person can walk (rays at four heights and three
  lateral offsets, bare floor under all three lines), dropped when a third sweep gives two shorter
  legs with less than 20 % detour. Links never pass through glass and must form one component.
  **Visible** = a clear line at eye height and 1 ft below, up to 40 ft, through clear glass; always
  a superset of the links. The page draws rings at the visible sweeps.
- **Ids:** two characters, the first a letter. Seeds keep theirs. New ones are the region's letter plus
  the first free character: L living, D dining, K kitchen, G garage, F foyer, H halls, P primary
  bedroom, S primary dressing, A baths, C closets, X / Y / Z = Bedroom 2 / 3 / 4. `LC`, `OP` (porch) and
  `OD` (deck) are fixed. No new id reuses an old one.
- **Angles:** `sweeps.json` and `assets/data/tour.json` hold degrees; nodes in `scene.json` hold
  radians, as they always did. Yaw 0 looks toward −z (north), positive clockwise seen from above.
- The outdoor sweeps exist only while a walkable line through an open door joins them to an indoor
  sweep. The exposure smoothing leaves indoor / outdoor links alone.

### How the page is built

- **Engine** (`assets/js/tour/engine.js`). One perspective and one orthographic camera. At rest the
  backdrop sphere alone is drawn (the model is not), so the frame is the equirect lookup. During a move
  each fragment takes weight × visibility of the two panoramas, normalised: a surface one sweep cannot
  see shows the other at full strength, a surface neither sees takes the panoramas without the depth
  test. Never the bake, never black. Visibility comes from a depth cube rendered from each sweep
  (distance packed in RGB, the class in A); its CPU copy answers `pick` in about a microsecond.
  Weights come straight from the page's clock, so the same call and camera give the same bytes.
- **Dollhouse and floor plan** are per fragment, driven by uniforms (no clipping planes, no program
  switch on a mode change): a cut height, the footprint rectangles of `tour.json` (at most 16), and the
  near-wall rule: discard a wall or glass fragment when stepping 0.9 ft toward the viewer, along its
  normal or along a plan axis, leaves the footprint. Seen from straight above nothing points to the
  viewer, so the floor plan keeps all four sides. The walls have no top faces, so a cap mesh is
  generated from the wall outlines at the cut. Floors end 0.03 ft outside the footprint; furniture may
  overhang 0.5 ft.
- **Panorama levels.** Per-level caps and a byte budget, least recently used first; the sweeps of the
  current move are never evicted. A higher level is uploaded in slices behind the one on screen (an 8k
  panorama in one call froze the page for a third of a second).
- **Inside navigation** (`inside.js`). A move is a flight along a route of sweeps: distance and speed
  are integrated per frame with constant acceleration and exact braking for the end of the route and
  for corners. One hop derives its acceleration from the hop time, which gives a quadratic ease
  in-out; position within the hop drives the blend (smoothstep 0.2..0.8). Rings and the cursor ring
  are meshes in `engine.overlay`, so the depth cube hides them behind walls; which ring a click means
  is decided in screen space plus depth probes on the ring.
- **Dollhouse camera** (`dollhouse.js`). One camera for both views: a point looked at, heading,
  elevation, the half height of the picture, and a flattening factor z (the eye stands z times farther
  and the lens is z times narrower). z = 1 is the dollhouse (38° lens); at a 0.8° lens the
  orthographic camera takes over, which differs by less than a pixel. A flight between a sweep and the
  orbit moves the eye on a curve that leaves the sweep straight up, while the engine fades the
  projection into the bake and the ceilings out. The way runs against time as smoothstep^1.6, because
  the picture changes most near the sweep. A mode makes its own way out (`controller.depart`), which
  is how the Inside button, a room name, the reel and `goTo` become a fly-in.
- **Shared things have one owner.** `viewer.js`: `util`, the cursor ring, `insets` (the part of the
  screen the chrome covers). `ui.js`: what is inert (`syncInert`) and where the menu opens. `main.js`:
  the link to the current place (`placeUrl()`) and the `?v=` suffix. Modules never import each other.

### Rules that came out of this round

- A plan change has three records that must agree: `bl/revision_spec.py` (numbers), `bl/revisions.py`
  (Blender geometry) and `apply_revisions_web.py` (web data). The web side appends wall boxes to
  `scene.objects` by name and never inserts, because object indices are `scene_index` in the built
  model.
- `check_holes.py` works on a 0.2 ft grid. The warp maps the two front corners of the central ceiling
  panel with different rooms, which left a hairline up to 0.03 ft wide, open to the attic, along the
  kitchen / garage wall inside the new closet; only a scan at 0.015 ft pitch found it
  (`revisions.ceiling_seam` now squares that edge). After changing walls or ceilings near a new room,
  scan its faces finely or look closely at renders of the joints.
- A black atlas in the bake means its UV islands could not have their pixel margin, not bad normals.
- Anything rendered or baked from a build older than the sweeps' build must be redone; the panorama
  metadata records the scene file for that reason.

## How to build and review

```bash
export BLENDER=/path/to/blender           # Blender 5.2 LTS (Cycles, OptiX on RTX)
tools/render/dev_preview.sh <zones> <sweeps> [width] [samples]
#   e.g. tools/render/dev_preview.sh kitchen_dining K0,D0,H2
#   -> tools/render/.cache/dev_kitchen_dining/{K0.png (equirect), K0_sheet.png (4 x 90deg views)}
$BLENDER -b tools/render/.cache/dev_<zone>/scene.blend --python tools/render/top_view.py -- \
    --rect=x0,x1,z0,z1 --out top.png          # orthographic plan check, north up
$BLENDER -b --factory-startup -noaudio --python tools/render/build_scene.py -- --zones all --strict \
    --out tools/render/.cache/house.blend     # the full build; then check_holes.py (README, "Verify")
```

Look at the `_sheet.png` review images after every change; they are the ground truth. Use
`top_view.py` to check layout, clearances and collisions (write `--rect=x0,...` with `=`), and
`whatis.py` to find which object/zone owns a pixel. `review.sh <blend> <sweeps> <out>` renders an
already built scene; every GPU render goes through `gpu.sh` (a lock) so parallel work can't exhaust
GPU memory.

Lighting is balanced at render time (`lighting.apply_balance()`: fixture lamps x0.12, emission x0.4,
sky and sun x2) and every sweep is auto-exposed and auto-white-balanced (then smoothed along the tour
graph in a production run), so a fixture that should read brighter needs a higher built value.
`TG_FLAT_MATERIALS=1` swaps the PBR library for flat colours (fast layout checks);
`ob['tg_grain']=1` turns wood grain 90 degrees on horizontal faces (see `bl/MATERIALS.md`).

## Code contract (`bl/`)

| Module | Owner | Purpose |
|---|---|---|
| `common.py` | core | `Ctx` (scene data, lookups, collections, geometry helpers), `ft2bl`, `place`, `world_bbox_ft` |
| `shell.py` | core | Exact architecture with modern finishes. Builds no furniture or fixtures. |
| `lighting.py` | core (exterior zone may tune the sun/sky constants) | Sky and sun, window portals, `can()`, `point_light()`, `emitter()` |
| `materials.py` | materials | `get(key)` library. KEYS are a stable contract. |
| `assets.py` | core | CC0 Poly Haven fetch and cache: `model()`, `texture()`, `hdri()`, `write_manifest()` |
| `zones/<zone>.py` | one zone agent each | `build(ctx) -> dict` that adds everything inside its zone |
| `warp.py` | core | Carries the built house from the concept plan onto the architect's plan |
| `revision_spec.py`, `revisions.py`, `laundry.py` | core | The owner's changes: numbers, geometry after the warp, the laundry closet's contents |

Rules:

- **Units.** All `Ctx` helpers take SCENE feet: x runs west→east, y is up, z runs north/garden
  (0) → south/street (~54). `rot` is radians about +Y. Floor is y=0, flat ceilings are at
  y=8.0, and every camera sits at y=5.0853.
- **Which plan.** Zone modules are written on the **concept plan** (`data/concept/`); `bl/warp.py`
  carries what they build onto the architect's plan. Code that runs after the warp (`bl/revisions.py`,
  `bl/laundry.py`) works in new-plan feet. A zone that needs a new-plan number converts it back with
  the inverse of the `relayout` map (see `TALL_X0` in `kitchen_dining_kitchen.py`).
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
- **Performance.** Final renders are 8192×4096 at 192 samples (adaptive), about 3.3 minutes each.
  Prefer instancing (shared mesh data / geometry-nodes instances) for grass, leaves and repeated
  items. Keep each zone under ~2M triangles unless it's a hero element.
- **Camera clearance.** Every sweep needs at least 1.2 ft of clear space around it. The 20 seed stops
  keep their place, so no furniture may swallow one; the other sweeps are placed after the build
  (`place_sweeps.py`), so moving furniture means placing them again.
- **Names matter to the bake.** `bake_web.py` classes objects by collection, `scene_index` and name
  (README, "Web model contract"). A new wall is a copy of an existing wall object.

## Zones

Every zone builds everything inside its regions, using the original scene objects (via
`ctx.find(room=..., role=...)`) as anchors for position and footprint. Original
furniture, decor, fixtures and landscape are **not** imported by the shell; the zone decides
what replaces them.

| Zone module | Regions (`scene_classification` rooms) | Sweeps to review |
|---|---|---|
| `kitchen_dining` | kitchen, dining | K0, K1, K2, K3, LC, D0 (also seen from H2, H4, L2) |
| `living` | living | L0, L1, L2, L3, L4, L5 |
| `primary_suite` | primary, primary_dressing | P0, S0, S1, C0 |
| `bedrooms` | bed2, bed3, bed3_bay, bed4, bed4_closet, suite3_wic | B2, X0, B3, Y0, Y1, Y2, Y3, B4, Z0, C3 |
| `baths` | ensuite, shared_bath, suite3_bath | A0, A1, A3 |
| `hall_entry_garage` | front_hall, common_hall, garage, porch (inside face of the entry) | E0, H1, GA, H0, H2, H3, H4, T2, G0, G1, G2, G3 |
| `exterior` | everything outside the walls: grounds, garden, deck, fences, driveway, trees, garage door (both faces), exterior lights, distant context | OP, OD, and every sweep's window views |

Boundaries: living owns the living region north of z=14.5; `kitchen_dining` owns the open area
from z=14.5 southward. Halls own circulation only and leave the room zones alone.
