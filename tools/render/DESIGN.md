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
| Fourth | 2026-11-19 evening | Matterport-style tour; a laundry closet, built in the kitchen's south-west corner (the wrong place) | "Fourth round" below |
| Fifth | 2026-11-20 | The laundry closet moved into Bedroom 4's north-east corner, opening onto the foyer; the dining table moved to the island's west end; the kitchen's south wall back to the third round's | "Fifth round" below |

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

## Fourth round (2026-11-19 evening): Matterport-style tour

The owner's request: the tour "feels very unreal" compared with a day earlier; rebuild it as needed to
feel like a Matterport space; and add a small room "on the right of Bedroom 4" for a stacked washer
and dryer, sized to fit them just right. This section describes the tour. The closet was built in
the wrong place and moved a day later: see "Fifth round".

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
   4 ft apart with at least 1.2 ft of clearance: 43 instead of 27 (45 since the fifth round). Soft
   white rings on the floor mark the sweeps in view; a cursor ring lies on the surface under the
   mouse.
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

Where the build departs from the first plan, on purpose: 43 sweeps in that round, not 45 to 50 (the
default 4 ft spacing); walls in the dollhouse are cut at 7.45 ft, below the skylight wells, not at
8 ft; the near-wall rule steps 0.9 ft, not 0.6 (the garage door's panels sit 0.62 ft inside the
outline); there is no double-click zoom, because a click always moves.

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
  the stops from the concept plan and the placement keeps a seed where the scene has it. Today's one
  entry is K0, moved to (27.6, 26.9) at the west end of the work aisle: since the fifth round the
  dining chairs stand 0.4 ft from where the concept had it.
- **The laundry sweep** `LC` stands in the foyer on the axis of the closet's opening,
  `LAUNDRY['dist']` (4 ft) in front of the door wall, and looks at the units with a pitch of
  `LAUNDRY['pitch']` (−14°). From 3 ft the stacked pair spans 79°, more than the page's 68° picture
  holds; from 4 ft it spans 67° and both units are in the opening view. The closet's rectangle and
  opening come from `bl/revision_spec.py`.
- **Keeping a layout** (`--keep`). A panorama stays valid only while its sweep does not move and
  nothing it sees changes. So after a local change the placement starts from the installed sweeps
  instead of the seeds, and only the sweeps that moved, are new or have a line of sight to a change
  are rendered again (README, "Add or move sweeps" and "Re-render a subset"). Kept sweeps are not
  held to the spacing rule among themselves: K0, moved by the scene, now stands 2.9 ft from K3, the
  tour's shortest link.
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
  kitchen / garage wall at the hall end of the pantry wall; only a scan at 0.015 ft pitch found it
  (`revisions.ceiling_seam` now squares that edge). After changing walls or ceilings near a new room,
  scan its faces finely or look closely at renders of the joints.
- A black atlas in the bake means its UV islands could not have their pixel margin, not bad normals.
- Anything rendered or baked from a build older than the sweeps' build must be redone; the panorama
  metadata records the scene file for that reason.

## Fifth round (2026-11-20): the closet in Bedroom 4, the dining table at the island's west end

The owner, on seeing the fourth round: "you are doing it very wrong". The washer and dryer belong
"right next to bedroom 4", in "a space of bedroom 4" taken out of that room, "on the left side of
the passway"; and the dining table, which made "the family room area very crowded", belongs "on the
shared bathroom side of the island".

**The first reading of "on the right of Bedroom 4" was wrong.** It was taken to mean the "W / D"
closet that the architect's sheet SKA002 draws across the foyer's north end from the office, in the
kitchen's south-west corner. The closet was built there and the kitchen's south wall was re-planned
around it. The owner meant a space taken out of Bedroom 4 itself, on the left (west) side of the
"passway": the foyer, which runs north from the front door past Bedroom 4. The closet is now the
room's north-east corner, next to the bedroom door, and opens east onto the foyer. Nothing of the
kitchen closet is left in the model or the data; its change list (`owner_changes_4`) stays in the
Design sheet and says that the fifth round superseded it, and its numbers are in commit ac91072.

### Laundry closet

All numbers are in `bl/revision_spec.py` (`LAUNDRY_*`, new-plan SCENE feet). The Blender revision, the
Bedroom 4 zone, the sweep placement and the web data derive from them.

- **Position and size.** Bedroom 4's north-east corner. Clear inside 3'-0" deep (east-west) ×
  2'-10" wide (north-south): `LAUNDRY_CLEAR`, x 12.085..15.085, z 28.72..31.553, 8.5 sq ft, under the
  room's flat 8 ft ceiling. The north side is Bedroom 4's north wall, the east side the
  Bedroom 4 / foyer wall (`LAUNDRY_HOST_WALL`, shell piece 3338). Two new walls, 0.36 ft thick,
  floor to ceiling: west (the units' back wall, x 11.725..12.085) and south (z 31.553..31.913).
  `laundry_walls()` and `laundry_host_wall()` give the boxes, `LAUNDRY_OUTER` the rectangle over the
  walls.
- **Doors (D17).** An opening 2'-6" × 6'-8" in the host wall, centred on the units
  (`LAUNDRY_DOOR_Z`, z 28.8865..31.3865). A pair of flush white leaves, 1.204 ft each, hinged on the
  two jambs, swung out into the foyer and shown open 160° (`LAUNDRY_DOOR_OPEN_DEG`), nearly flat
  against the foyer wall, where they take 0.58 ft of the foyer's 5.77 ft. The brief said "about
  150°"; at 150 the nearer leaf hides most of the units from further down the foyer. Painted jamb
  liners and head trim like the other interior doors, an oak threshold strip, three black knuckle
  hinges and one bar pull per leaf. `laundry_leaf(side, open_deg)` / `laundry_leaves()` turn the
  leaves about their hinge pins and `bl/laundry.door_hardware` places hinges and pulls from the
  result, so any angle stays consistent.
- **Units.** A stacked front-load pair, washer below and dryer on top, each 27 × 30 1/4 × 39 in,
  facing east, centred in the width (0.29 ft free on each side, 0.38 ft behind for hoses and the
  vent), with a stacking trim between (`laundry_units()`). `bl/laundry.py` models them procedurally
  (round hatch with a chrome ring and dark glass, control strip with a lit display, detergent drawer,
  kick panel) in a local frame and turns that a quarter turn onto the plan: a rotation, not a mirror,
  so the displays read correctly. They are generic models of a typical pair, not a selected product,
  and the Design sheet says so.
- **Services.** On the back (west) wall: a recessed outlet box (`LAUNDRY_HOOKUP_RECESS`,
  z 28.84..29.50, y 3.50..4.10, 0.24 ft deep; the wall is split around it) with valves and hoses,
  the dryer's vent duct to a wall collar at 7.25 ft, a 240 V receptacle. A flush ceiling light sits
  just inside the door head (`LAUNDRY_LIGHT`).
- **The revision** (`revisions.laundry_closet`, after the warp, before `floor_gaps` and
  `skirting_trim`). The host wall keeps its part south of the opening; the return north of the
  opening, the header and the two new walls are copies of it (`_like`), so they carry its paint and
  `scene_index` and bake as walls. The host wall's two baseboards are cut at the jamb liners; new
  runs go on every new face, with a block at the outside corner. An oak patch lies just under the
  floor over the closet's footprint, because the floor slab stops short of the north wall under that
  wall's baseboard.
- **Bedroom 4** is L-shaped: 14'-10 3/8" × 8'-0" overall as before, less 3'-4 3/8" × 3'-2 1/4" for the
  closet and its two walls (108.15 sq ft, 118.87 before). Bed, nightstand, rug and pendant stay. The
  desk group moved out of the corner into the niche on the north wall, between the nightstand and
  the closet's west wall: `bedrooms._b4_desk_x` inverts `relayout.X_FRONT_ROOMS` so that the warp
  lands the desk 0.05 ft off that wall. `bedrooms.bed4_closet_faces`, called by the revision after
  the warp, hangs a slim print on the closet's west face and an oak peg rail on its south face,
  behind the open bedroom door. 5.07 ft stay clear between the desk chair's back and the reach-in
  closet's wall.
- **In the tour.** Room M13 and doors D17 in the Dimensions sheet, the closet's walls and open
  leaves on the plan, the Design view and hero still `LC` (from the foyer's east side, looking
  north-west, Bedroom 4's door on the left), and the sweep `LC` in the foyer facing the doors
  ("Sweep placement" above).
- **Limits.** From the front door the open leaves show but the units do not (they stand 0.46 ft
  behind the wall face); they come into view from about z 40 northward. With the leaves open, their
  pulls face the foyer wall. The dryer vent enters the wall shared with Bedroom 4; a real duct would
  turn up into the attic inside it.

Naming rules the closet depends on: its contents are named `laundry closet ...` (the bake files them
as `base`, the sweep placement looks for `laundry` / `washer` / `dryer` inside `LAUNDRY_OUTER`);
nothing with a glass-named material goes into the `openings` collection (it would get a light
portal); appliance parts are not named "door" (the bake files those under walls), hence "hatch"; the
art on the closet's bedroom faces has no "closet" in its names (the bake would file it as a
built-in).

### Dining table and kitchen

- **The table** continues the island's west end, toward the hall: 6'-0" × 2'-9", built
  x 21.43..27.43, z 21.86..24.61, on the island's centre line, its east end 0.02 ft short of the
  island worktop (x 27.45..33.22). Six chairs, three on each long side (backs at z 20.80 and 25.67),
  none at the ends, no rug, the brass lantern over the middle. From the south chairs' backs it is
  3.21 ft to the pantry-wall fronts (z 28.88) and 3.01 ft to the oven handles; nothing stands west
  of x 21.43 (the hall line is x 21.2). The floor between the island and the living room is open and
  stays so.
- **How it is placed.** The set is loose furniture: `bl/warp.py` moves its cluster by the shift of
  the cluster's centre and keeps its size, while the island is fitted and shrinks with the room. So
  `kitchen_dining_dining._rect_centre()` states the position on the built plan (`RECT_GAP` short of
  the island worktop's west edge, `kitchen_dining_kitchen.ISLAND`) and carries the centre back to
  the concept plan with the inverse of `relayout.X_HALL`. Keep the set symmetric about the table's
  centre (the lantern's fitted rod is mapped by the same point) and put no recessed can over it (cans
  are loose and would join the cluster). After a change, compare `'dining': {'plan': ...}` in the
  build log with the built objects.
- **Kitchen south wall:** the third-round layout again (`kitchen_dining_kitchen.py` as in commit
  ed664e0), west to east: end panel toward the hall (x 21.83) | refrigerator column (21.90..24.82) |
  double ovens (24.87..27.12) | counter with three glass-front uppers (27.22..32.06) | cooktop under
  the hood (32.07..35.15) | base run to the corner.
- **Hero stills.** `K0` stands in the hall and looks east along the table to the island and the
  pantry wall; `B4` takes in the desk niche.

### Repairs found in review

- **Coplanar slabs.** Two faces of different objects in one plane shade each other in Cycles (a
  darker band with sharp edges) and flicker in the web model. The slab warp had left two such
  overlaps, both in front of the new closet. `revisions.floor_overlap` puts the north edge of the
  oak slab under the Bedroom 4 / foyer row on the south edge of the slab north of it (a wedge up to
  0.16 ft wide across Bedroom 4 and the foyer). `revisions.ceiling_overlap` starts the bedroom-hall
  ceiling on the central ceiling panel's front edge (z 31.24; they overlapped over the foyer's north
  end, x 15.27..21.40, z 28.54..31.24); it runs after `ceiling_seam`, which squares that edge, and
  before the skylight cuts. Both end the two slabs on one line. Offsetting one of them instead
  leaves walls in the air, or two surfaces a fraction of a millimetre apart.
- **Foyer / kitchen wall corner.** The garage's west wall and the kitchen / garage wall each stop on
  the other's centre line, which leaves a 0.18 × 0.18 ft notch, floor to ceiling, beside the
  refrigerator's end panel (`revision_spec.FOYER_CORNER_INFILL`). The kitchen closet had filled it.
  `revisions.foyer_corner` fills it with a copy of the garage wall and lays an oak patch under the
  baseboard at its foot, where the floor slab's skewed edge stops short of the kitchen wall.
- **Checks to repeat after any change to slabs or walls:** `check_holes.py` (baseline line only); a
  scan for coplanar first surfaces (rays up from 6.9 ft and down from 1.2 ft against each shell
  object separately; flag two objects hit within 0.0006 ft); a fine scan of the changed faces
  (0.012 ft pitch). `floor_gaps` only finds strips its downward probes can reach: a strip under a
  baseboard needs a patch of its own. The scans of this round were one-off scripts and are not in
  the repository.

### Rules that came out of the correction

- A request that places a room is read against the tour's own plan and room names first, the
  architect's sheet second. Where two readings put the room in different places, ask before
  building.
- A room cut out of another room keeps both schedule entries rectangular: the host room's
  `bounds_ft`, width and depth stay, its area and note say what was taken out, and the new room's
  bounds lie inside the host's. Anything that looks a room up by position must take the smallest
  room that contains the point (`build_site_data.room_of`, `viewer.js` `roomAt`). M13's `width_ft`
  is its north-south size, across the doors, and its `depth_ft` the east-west one (the owner's
  2'-10" × 3'-0"); the other rooms' width is their x extent.
- `tools/web/dimension_plan.py` lays the room labels out before the door tags: a tag that would
  cover a label moves across its wall, away from that room (the closet is no bigger than its
  label).

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
  `bl/laundry.py`, `bedrooms.bed4_closet_faces`) works in new-plan feet. A zone that needs a new-plan
  number converts it back with the inverse of the `relayout` map (see `_rect_centre` in
  `kitchen_dining_dining.py` and `_b4_desk_x` in `bedrooms.py`).
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
- **Performance.** Final renders are 8192×4096 at 192 samples (adaptive), about 3.2 minutes each.
  Prefer instancing (shared mesh data / geometry-nodes instances) for grass, leaves and repeated
  items. Keep each zone under ~2M triangles unless it's a hero element.
- **Camera clearance.** Every sweep needs at least 1.2 ft of clear space around it. The 20 seed stops
  keep their place, so no furniture may swallow one; the other sweeps are placed after the build
  (`place_sweeps.py`), so moving furniture means placing them again (`--keep`) and rendering again
  whatever sees the change.
- **Names matter to the bake.** `bake_web.py` classes objects by collection, `scene_index` and name
  (README, "Web model contract"). A new wall is a copy of an existing wall object.

## Zones

Every zone builds everything inside its regions, using the original scene objects (via
`ctx.find(room=..., role=...)`) as anchors for position and footprint. Original
furniture, decor, fixtures and landscape are **not** imported by the shell; the zone decides
what replaces them.

| Zone module | Regions (`scene_classification` rooms) | Sweeps to review |
|---|---|---|
| `kitchen_dining` | kitchen, dining | K0, K1, K2, K3, K4, D0, D1 (also seen from H2, H4, L2) |
| `living` | living | L0, L1, L2, L3, L4, L5 |
| `primary_suite` | primary, primary_dressing | P0, S0, S1, C0 |
| `bedrooms` | bed2, bed3, bed3_bay, bed4, bed4_closet, suite3_wic | B2, X0, B3, Y0, Y1, Y2, Y3, B4, Z0, C3 |
| `baths` | ensuite, shared_bath, suite3_bath | A0, A1, A3 |
| `hall_entry_garage` | front_hall, common_hall, garage, porch (inside face of the entry) | E0, H1, GA, LC, H0, H2, H3, H4, T2, G0, G1, G2, G3 |
| `exterior` | everything outside the walls: grounds, garden, deck, fences, driveway, trees, garage door (both faces), exterior lights, distant context | OP, OD, and every sweep's window views |

Boundaries: living owns the living region north of z=14.5; `kitchen_dining` owns the open area
from z=14.5 southward. Halls own circulation only and leave the room zones alone. The laundry closet
is not a zone's: `bl/revisions.py` and `bl/laundry.py` build it after the warp (collection
`heg_laundry` under `zone_hall_entry_garage`), and `LC` is the sweep to review it from.
