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
| Sixth | 2026-11-20 afternoon | The primary suite on the architect's sheet: the walk-in closet a room of its own behind a pocket door, a vestibule, a sliding suite entry, the bed on the west wall. The primary bath rebuilt to the sheet and restyled after the owner's wall image. A taller shower window in the Bedroom 3 bathroom. The owner's four answers: that window from a 3'-0" sill to a 7'-6" head; the bath laid out as on the sheet; the second west window of the primary bedroom (W14) kept although the sheet omits it; the stone on the vanity wall, not in the shower | "Sixth round" below |

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
- **Primary bath** (`baths_primary.py`): the floating solid-oak double vanity with two carved basins
  (`styles/primary bathroom sink.jpg`). The rest of this round's bath was replaced in the sixth
  round, which rebuilt the room after `styles/primary bathroom wall style.jpg`: see "Sixth round".
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
   4 ft apart with at least 1.2 ft of clearance: 43 instead of 27 (49 since the sixth round). Soft
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
- **The walk-in closet's stop** `C0` (`WALKIN`, `place_walkin`; sixth round) is the one seed that
  does not keep its place: the concept's position lies under the closet's south rod. When it has
  lost its clearance it goes to the most open reachable cell inside the closet
  (`SUITE_CLOSET_CLEAR`), among equals the one nearest the pocket door's axis: (4.50, 16.75), with
  2.4 ft all round. A 6 × 8 ft room hung on three sides leaves an aisle 3.5 ft wide; the usual
  1.5 ft nudge left the camera at its edge, on a line to the vestibule that passed 0.2 ft from the
  leaf's nose. The rule fires only when the stop fails, so a second run keeps C0.
- **Keeping a layout** (`--keep`). A panorama stays valid only while its sweep does not move and
  nothing it sees changes. So after a local change the placement starts from the installed sweeps
  instead of the seeds, and only the sweeps that moved, are new or have a line of sight to a change
  are rendered again (README, "Add or move sweeps" and "Re-render a subset"). Kept sweeps are not
  held to the spacing rule among themselves: K0, moved by the scene, now stands 2.9 ft from K3, the
  tour's shortest link. A kept sweep's name follows the scene file (`kept_renames`): a renamed seed
  takes its new label, and so do the kept sweeps that carried its old one (S1 had S0's).
- **Opening views.** A seed keeps its authored view, a new sweep looks in its most open direction,
  a kept sweep keeps what it had. `OPENING` in `apply_sweeps.py` overrides that at every install
  with views chosen by eye on renders: G0 and H2, and since the sixth round C0 (the closet's
  hanging wall), S1 (through the bath door at the stone wall), A0 (across the vanity), P5 (the
  bed between the two windows) and A3 (the taller shower window).
- **Link** = a straight line up to 11 ft that a person can walk (rays at four heights and three
  lateral offsets, bare floor under all three lines), dropped when a third sweep gives two shorter
  legs with less than 20 % detour. Links never pass through glass and must form one component.
  **Visible** = a clear line at eye height and 1 ft below, up to 40 ft, through clear glass; always
  a superset of the links. The page draws rings at the visible sweeps.
- **Ids:** two characters, the first a letter. Seeds keep theirs. New ones are the region's letter plus
  the first free character: L living, D dining, K kitchen, G garage, F foyer, H halls, P primary
  bedroom, S the primary suite's vestibule and walk-in closet (one region, `primary_dressing`),
  A baths, C closets, X / Y / Z = Bedroom 2 / 3 / 4. `LC`, `OP` (porch) and `OD` (deck) are fixed.
  No new id reuses an old one.
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

## Sixth round (2026-11-20 afternoon): the primary suite on the architect's sheet

The owner: in "the bathroom in the front bedroom suite" the window in the shower "is too small,
make it vertically larger"; "the walk in closet in the primary bedroom is not correct, you should
refer to the floor plan of sizes.pdf last page for that, there should be a door since it's a small
room"; "refer to the sizes and floor plans for the primary bedroom, bathroom and the walk in closet
to make it more accurate"; and for the primary bathroom "apply the style in styles folder, there is
a image of primary bathroom wall".

### Asked before building

Four points of the request could be built in more than one way. They went to the owner as direct
questions, each with concrete options and one of them recommended, before the long render:

| Question | Recommended | The owner's answer |
|---|---|---|
| How tall the Bedroom 3 bathroom's shower window becomes | sill 3'-0", head 7'-6" | as recommended |
| Whether the primary bath is rebuilt to the sheet's layout | yes | yes: shower north-west, toilet south-west, double vanity on the south wall, door at the east end of the north wall; the skylight moves with the shower, the west window to the sheet's place, 3 ft wide |
| Whether the primary bedroom's second west window (W14), which the sheet does not show, goes | remove it | **keep it** |
| Where the stacked stone of the wall image goes | the two shower walls | **the vanity wall** (the south wall, behind the vanity and the mirrors); plain cream tile in the shower |

Two of the four recommendations were wrong. The answers override everything else, the sheet
included (W14); where the answers and the request are silent, the sheet decides.

### Primary suite

Numbers: `bl/revision_spec.py`, `SUITE_*` (SCENE feet on the architect's plan). The clear sizes of
the primary bedroom (11'-1" × 12'-3") and the primary bath (9'-6" × 7'-2") already matched the
sheet. The 8'-0" zone between them (z 12.835..20.835), one open area with wardrobes until the
fifth round, is two rooms as on the sheet.

- **Walk-in closet** (M05, sweep C0): an enclosed room without a window, clear 6'-1" × 8'-0"
  (`SUITE_CLOSET_CLEAR`), behind a new 5 in wall (`SUITE_CLOSET_WALL_X`, x 6.308..6.725). Rods and
  shelves on the north, west and south walls as the sheet draws them, a drawer and shelf tower in
  the middle of the west wall, facing the door, and a flush ceiling light. The aisle is 3.5 ft
  wide.
- **Pocket door** (D18): clear opening 2'-6" × 6'-8", centred on the closet (`SUITE_CLOSET_DOOR_Z`,
  z 15.585..18.085); the leaf slides south into the wall. The brief had the door at the wall's
  south end, sliding north: it had taken the leaf, which the sheet draws open inside its pocket,
  for the opening. At 1200 dpi the sheet shows a full jamb, a split jamb 2'-6" south of it, and
  the leaf in a pocket sleeve beyond with its nose out. The leaf is shown 0.30 ft out of the
  pocket (`SUITE_CLOSET_LEAF_SHOWN`; the sheet draws about 0.27), which leaves a 2.17 ft passage.
  The brief's "about a third out" would leave 1.67 ft, and the sweep placement, which floods the
  floor with a 0.9 ft body radius on a 0.25 ft grid, needs about 2.05 ft to reach the closet.
- **Vestibule** (M14, sweeps S0 S1): clear 4'-7" × 8'-0" (`SUITE_VESTIBULE_CLEAR`), open to the
  bedroom over its whole width under the existing header (D10, no door). The sheet's "(E) 30X22
  ATTIC ACCESS" is a flush panel in a thin frame on the ceiling (`SUITE_ATTIC_HATCH`; nothing is
  cut). One mirror on the closet wall.
- **Suite entry** (D09): a 2'-8" opening with a flush sliding panel on a slim black track on the
  hall face, shown open, parked south of the opening. **It stands 1'-8" south of its place on the
  sheet** (`SUITE_ENTRY_Z` 15.21..17.877 against `SUITE_ENTRY_SHEET_Z` 13.56..16.20). On the sheet
  that stretch of the wall faces the hall. In this model it backs onto Bedroom 2's entry alcove
  (the concept's layout, z 12.835..14.75, behind the doorless opening D12), and the hall begins
  at z 15.11: an opening at the sheet's place would lead into Bedroom 2. So the entry is built as
  far north as the hall allows, 0.10 ft off Bedroom 2's wall. Following the sheet needs Bedroom
  2's entry and closet re-planned, which the owner did not ask for. D09's entry in the Dimensions
  sheet and the change list in the Design sheet say where it stands and why.
- **Bedroom**, furnished as drawn: a king bed with its headboard on the west wall, centred on the
  room (z 6.35) between the two west windows, a nightstand each side, a rug. Both west windows
  stay: W15, and **W14 by the owner's decision**, although the sheet shows only W15. The bed as
  drawn is 7.06 ft wide with its headboard and the pier between the windows 5.26 ft, so nothing
  on that wall rises above the 2'-6" sills where glass is behind it: the headboard is 2'-4 1/2"
  high, the nightstands 1'-4 3/4" with small dome lamps. No dresser on the east wall (it would
  leave 2.4 ft at the bed's foot): 3.6 ft stay clear from the vestibule to the garden door.
- **How it is built.** `revisions.suite_rooms` calls `bl/zones/primary_suite_rooms.build`: the
  bedroom / closet wall is carried on to the new wall, the new wall is three copies of it (`_like`:
  same `scene_index`, baked as a wall), the suite entry's three wall pieces are reshaped; then
  jambs, the leaf and the panel with pulls, tracks and floor guides, and baseboards on every new
  face. It raises when a wall is not where the spec expects it, and runs after `bath_door`, which
  carries the bath wall's baseboard across the new wall's place. `revisions.suite_fit_out` calls
  `bl/zones/primary_suite.fit_out` for the furniture and the closet's fit-out. Its audit (`notes`
  on the `revisions:` line) must stay empty: nothing above the sills in front of window glass,
  within 3 ft of the bedroom's east wall, in a door opening or in a wall.
- **Names and a repair.** New wall and door parts are called `Primary closet ...` and
  `Primary suite entry ...`; the SCENE's "Walk-in closet ..." pieces belong to Bedroom 3's closet.
  On the hall face of the suite wall, Bedroom 2's entry header stopped 0.113 ft short of the
  wall, a slot from 6'-8" to the ceiling that the old door's casing had hidden; it now runs to
  the wall (`SUITE_BED2_HEADER`).

### Primary bath

Numbers: `BATH_*` and `PRIMARY_BATH_*`. Until the fifth round the room was mirrored north to
south. Two things changed at once.

**Layout, as on the sheet.**

- Door D08 at the east end of the north wall (`BATH_DOOR_X`, x 6.89..9.45): a 2'-6" leaf hinged
  on the east jamb, open 90° against the east wall, over an oak saddle.
- Shower, 5'-0" × 3'-0", in the north-west corner (`BATH_SHOWER`): curbless, frameless glass on
  its east side (the door and a short fixed return) and its south side (one fixed panel), a rain
  head and a hand shower on the north wall, a niche recessed into that wall (`BATH_NICHE`;
  `bath_door` splits the wall around it). The drain is linear, along the north wall; the sheet
  draws a point drain.
- Toilet in the south-west corner, facing north (`BATH_TOILET_X`), 22 in clear of the shower
  glass.
- Double vanity along the south wall, 6'-6" × 1'-9" (`BATH_VANITY`, basins at `BATH_BASINS_X`):
  the floating solid-oak slab with two carved basins of the owner's sink image, kept.
- Window W13 at the sheet's place, 3'-0" wide (`BATH_WIN_Z`, z 22.89..25.89), with the owner's
  vertical size of the third round: 2'-0" sill to the ceiling, transom at 6 ft, clear glass. Its
  mullion stands on the shower's south glass line (`BATH_WIN_MULLION_Z`, z 24.21), 0.2 ft north
  of the window's centre where the sheet has it, because a glass panel cannot end on glass. The
  north lite is inside the shower (stone sill, tiled reveal); the south lite has the oak stool
  and the roman shade.
- Skylight W20 (second round: "over the shower") moved with the shower (`PRIMARY_BATH_SKY`).
  It is cut into the shell as built, so nothing is left where it was.
- Finishes take room: tile and wainscot 0.065 ft on a wall, the stone up to 0.15 ft. The vanity
  slab therefore shows 6.44 ft of its 6'-6", and the toilet's tank stands 0.19 ft off the
  structural wall.

**Style, after `styles/primary bathroom wall style.jpg`** (rustic, warm, low saturation), with the
stone where the owner put it. Materials are `Z_baths_primary_*` (`baths_primary_mats.py`).

- South (vanity) wall: stacked natural stone over the full width and height, in true displacement
  (Poly Haven Rustic Stone Wall 02; `STONE_SIZE`, `STONE_STRETCH` and `STONE_MID` set the size of
  the stones and the flush sandy mortar bed). On it two oak-framed mirrors, and above them a
  rough dark timber beam with an enamel lamp over each basin.
- Shower: plain honed cream stone-look tile, 24 × 48 in, on its two solid walls and a cream mosaic
  floor. No stone, nothing glazed.
- Other walls: muted grey-green tongue-and-groove wainscot to 3'-8" with a cap rail, warm cream
  plaster above and on the ceiling, one timber beam across the ceiling.
- Floor: quiet warm-grey stone, 24 × 24 in, no pattern. Fittings in brushed nickel. A timber shelf
  on iron brackets with bottles, a botanical print and a trailing plant; striped towels, a cactus
  in a zinc pot, a fringed mat.
- What differs from the image: the room is lit by daylight with the lamps as warm accents, the
  image by one lamp at dusk; the stone's courses are more regular; the floor is lighter; the
  window frames stay black, like the house's.

The room is fitted out by `baths_primary.build_room` after the warp (see "Which plan" in the code
contract), so its patterns are laid out on the built room: tile courses start at the floor and the
niche's sill sits on a joint, the floor grid is centred on the room.

### Bedroom 3 bathroom: the taller shower window

W11 on the west wall keeps its 3'-0" width, its frosted glass and its black two-lite frame. Sill
3'-0", head 7'-6" (`BED3_BATH_WIN_Y`; 5'-0" and 7'-0" before), measured from the house's floor
datum; the bath's tile floor is 0.1 ft higher. `revisions.bedroom3_bath_window` moves the wall
below and the header above, stretches frame and pane, and checks the bath zone's tile, jamb
returns and sill against the opening.

- Two old defects showed in the taller window and are repaired in it. The shell's pane stops 0.03
  to 0.04 ft short of each jamb section, a clear slit beside the frosted glass; the pane now runs
  into the jambs. (Every other window still has the slit, harmless where it shows sky.) And the
  quartz sill, named "stool", was moved by the warp as loose furniture and stood 0.18 ft off the
  opening; as `A3 window return sill` it is reshaped with the wall.
- The window has no shade and got none: privacy rests on the obscured glass, with the sill now at
  hip height in the shower.
- On the west facade its head stands 6 in above the heads of the bedroom windows beside it. That
  is the size the owner confirmed.

### Sweeps, pins, renders

- 49 sweeps, 58 links. Placed with `--keep`: 43 stay; C0 moves to the middle of the closet's aisle
  and S1 in front of the new bath door; P2 to P5 are new, on the bedroom floor the bed left
  uncovered when it moved to the west wall. Every room of the suite has a sweep. The suite's
  links: T2-S0 through the suite entry, S0-P0, S0-C0 through the pocket door, S0-S1, S1-A0 through
  the bath door.
- The nine suite sweeps got new pins, solved from probes of the new rooms with all other pins
  fixed (README, "Re-render a subset"): an enclosed closet and a re-furnished bedroom do not fit
  the exposure of the rooms they replace.
- Rendered again: 32 of the 49 panoramas; the hero stills (the cameras of `primary` and `A0`
  were re-aimed); the bake; all 32 exterior frames, because the two changed west windows (W11,
  W13) and the moved skylight show on the facade and on the roof.

### Process notes

- **Ask before a long render, and offer a recommended answer to each question.** A choice the
  request leaves open (how tall, which wall, the sheet or the tour as it stands) goes to the owner
  as a direct question with concrete options before the render: a round costs about two and a
  half hours of rendering, and the fifth round was the price of not asking. A recommendation speeds
  the answer; it is a guess, not a decision. This time two of four were wrong (W14, the wall the
  stone goes on), and both would have been built wrong without the question.
- **Read a door off the sheet by its jambs and its pocket**, not by the leaf, which is drawn open,
  or by the wall hatch, which runs through every opening on this sheet. Read at 1200 dpi before
  writing a number into a brief.
- **Where the model cannot follow the sheet, say so in the tour**, not only in notes: D09's type
  in the Dimensions sheet and the round's change list state the 1'-8" and its reason. Both
  texts are computed from the spec, so they go when the entry moves.
- **A room that must sit on the sheet's lines is fitted out after the warp**, in plan feet. The
  warp moves loose pieces in clusters and decides by name what is loose; that is fine for
  furniture in a room and wrong for a glass line that has to meet a mullion.
- **A door that moves keeps its SCENE leaf**: the old leaf box is moved in place, because the plan
  draws every box of group `door` and objects are never removed. `tools/web/dimension_plan.py`:
  a door tag with a room label on both sides of its wall (D18, between the closet and the
  vestibule) slides along the wall to the nearer end of those labels.

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
| `zones/<zone>.py` | one zone agent each | `build(ctx) -> dict` that adds everything inside its zone (the primary suite and the primary bath: after the warp, see "Which plan") |
| `warp.py` | core | Carries the built house from the concept plan onto the architect's plan |
| `revision_spec.py`, `revisions.py`, `laundry.py`, `zones/primary_suite_rooms.py` | core | The owner's changes: numbers, geometry after the warp, the laundry closet's contents, the primary suite's walls and doors |

Rules:

- **Units.** All `Ctx` helpers take SCENE feet: x runs west→east, y is up, z runs north/garden
  (0) → south/street (~54). `rot` is radians about +Y. Floor is y=0, flat ceilings are at
  y=8.0, and every camera sits at y=5.0853.
- **Which plan.** Zone modules are written on the **concept plan** (`data/concept/`); `bl/warp.py`
  carries what they build onto the architect's plan. Code that runs after the warp (`bl/revisions.py`,
  `bl/laundry.py`, `bedrooms.bed4_closet_faces`) works in new-plan feet. A zone that needs a new-plan
  number converts it back with the inverse of the `relayout` map (see `_rect_centre` in
  `kitchen_dining_dining.py` and `_b4_desk_x` in `bedrooms.py`).
  Since the sixth round two whole rooms are built after the warp, in plan feet: the primary suite
  (`primary_suite.fit_out`, called by `revisions.suite_fit_out`) and the primary bath
  (`baths_primary.build_room`, called by `revisions.primary_bath_fit_out`). Their `build()` /
  `build_primary()` only register the zone before the warp, which is how the revision knows
  that it was asked for; without it the fit-out is skipped. When editing them:
  - a number in the code is a position on the sheet and in the built model: no map, no inverse;
  - walls, doors, windows and the skylight come from `bl/revision_spec.py` (`SUITE_*`, `BATH_*`,
    `PRIMARY_BATH_*`); read them from there and move them there, never as a literal in the zone;
  - the warp no longer sees these pieces, so its name rules (fitted or loose) do not apply; the
    bake's name rules do, and the bath marks its wall finishes with `tg_class = 'wall'`;
  - order matters: `bath_door`, `bath_window`, `primary_bath_skylight`, then `suite_rooms`,
    `suite_fit_out`, `primary_bath_fit_out`, all before `floor_gaps` and `skirting_trim`;
  - keep `primary_suite.fit_out`'s audit empty, and check positions on the built model.
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
  keep their place (all but C0, which the placement moves to the middle of the walk-in closet's
  aisle), so no furniture may swallow one; the other sweeps are placed after the build
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
| `primary_suite` | primary, primary_dressing (the vestibule and the walk-in closet) | P0, P2, P3, P4, P5, S0, S1, C0 |
| `bedrooms` | bed2, bed3, bed3_bay, bed4, bed4_closet, suite3_wic | B2, X0, B3, Y0, Y1, Y2, Y3, B4, Z0, C3 |
| `baths` | ensuite, shared_bath, suite3_bath | A0 (also seen from S1), A1, A3 |
| `hall_entry_garage` | front_hall, common_hall, garage, porch (inside face of the entry) | E0, H1, GA, LC, H0, H2, H3, H4, T2, G0, G1, G2, G3 |
| `exterior` | everything outside the walls: grounds, garden, deck, fences, driveway, trees, garage door (both faces), exterior lights, distant context | OP, OD, and every sweep's window views |

Boundaries: living owns the living region north of z=14.5; `kitchen_dining` owns the open area
from z=14.5 southward. Halls own circulation only and leave the room zones alone. The laundry closet
is not a zone's: `bl/revisions.py` and `bl/laundry.py` build it after the warp (collection
`heg_laundry` under `zone_hall_entry_garage`), and `LC` is the sweep to review it from. The primary
suite's walls and doors and the primary bath's door, window and skylight are revisions too; the two
zones furnish what the revisions leave.
