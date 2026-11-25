# 1095 W McKinley: modern photoreal restyle (design brief and code contract)

The tour's panoramas are path-traced in Blender/Cycles from the **exact** remodel geometry: the
architect's plan (`sizes/sizes.pdf`, sheet SKA002) plus the owner's changes. The architecture (walls,
openings, ceilings, vaults, roof, every dimension in the Dimensions sheet) is fixed, and since the
eighth round the model stands on the sheet's own lines. What we
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
| Seventh | 2026-11-21 | A visible stainless refrigerator beside a built-in microwave. Every window and glazed door white, with grid bars. The primary bath a white room with one stone wall. The living room without its fireplace: sofa on the east wall, television on the west wall. The sky turned to the sun, for a yard that faces north. The owner also asked for an exterior after 1073 W McKinley Ave and then set it aside | "Seventh round" below |
| Eighth | 2026-11-23/24 | The owner asked for an audit of the model against `sizes/sizes.pdf`, read it and said "can you fix all al these issues?". The model is brought to sheet SKA002: its frame is the sheet's and every wall 5 in; Bedroom 2's closet block and the hall, the kitchen island and counters, Bedroom 3's bath and closet, door and window openings, skylights, the garage floor and doors, the roof (5 in 12, the entry gable over the porch), the ground levels, landings and driveway are as drawn; the tour's data follows. 33 of the sheet's 39 printed dimensions match, the other six are the owner's earlier decisions, which all stay. Decided in the round, for the owner to see: Bedroom 3's west window is removed (the sheet has a solid wall; one constant brings it back), and the entry front is 1.45 ft taller. Departures from the brief: foyer and porch 5'-9" and Bedrooms 3 and 4 14'-11" wide, the sidelights narrowed to the foyer, the entry roof's height taken from SKA001's roof plan, a 6 in ledge in the hall | "Eighth round" below |

## Design language (1077 W McKinley)

- **Light and calm.** Warm-white matte walls, flat white ceilings dotted with small 4" recessed
  LED downlights (warm 3000K), slim linear slot diffusers. No crown moulding and no raised
  panels. Doors are flush white slabs with matte-black levers. Casings are minimal.
- **Floors.** Wide-plank (≈9") light white oak with a matte, natural-oil look, used everywhere
  except wet rooms. Wet rooms get large-format 24×48 warm-grey porcelain.
- **Glazing.** Slim frames and clear panes. Since the seventh round every window and glazed door
  is satin white with white grid bars (matte black without divided lights until then); only the
  skylights keep black frames.
- **Kitchen.**
  - Cabinetry: flat-slab walnut with horizontal grain and integrated finger-pull channels.
  - Surfaces: white Calacatta-look quartz worktops with a full-height quartz backsplash.
  - Island: waterfall quartz with a walnut base, plus saddle-tan leather counter stools on
    black pedestal bases.
  - Appliances: stainless and in plain view (seventh round): a French-door refrigerator beside a
    built-in microwave over a wall oven, and a cooktop under the hood.
  - Hood: minimal white plaster or integrated.
  - Lighting: a linear LED pendant (or ring pendants) over the island, warm LED strips under
    the uppers and at the toe kick.
- **Living** (as furnished since the seventh round, which removed the fireplace and its stone
  feature wall; layout in "Seventh round").
  - The east wall is a plain white wall. A white bouclé sofa with ochre and cream pillows stands
    against it, a round walnut side table with a ceramic lamp at each end, an abstract canvas in
    neutral/ochre/charcoal above it.
  - Opposite, on the west wall, a 75 in television over a low white-oak console on black steel
    legs.
  - A round walnut coffee table on a round cream wool rug, one bouclé barrel chair, a money tree
    in a fluted planter beside the console, a few ceramic vases.
- **Dining.** A walnut or oak table, curved bouclé dining chairs, and a double-ring LED chandelier.
- **Bedrooms.** Upholstered low platform beds in light grey/cream with layered white linen
  bedding and a throw. Cream or white-oak nightstands with ceramic lamps. A soft grey or
  cream rug and one large abstract piece above the bed. Flush ring LED ceiling lights or cans.
- **Bathrooms.**
  - Vanity and mirror: floating walnut vanities with white quartz tops and undermount or
    vessel sinks, plus backlit LED mirrors.
  - Fixtures: matte-black faucets and shower trim, wall-hung or skirted one-piece toilets.
  - Shower: frameless glass, a linear drain, and a recessed niche with an LED strip.
  - Walls: the primary bath is white with one wall of stacked stone (sixth and seventh rounds);
    black fluted or large-format marble-look porcelain in the secondary baths.
- **Exterior.**
  - Facade: smooth warm-white stucco with a warm wood (cedar/thermo-ash) cladding accent at the
    recessed entry, charcoal fascia and a charcoal standing-seam roof.
  - Garage door: modern black aluminium with frosted glass.
  - Fence and hardscape: charcoal horizontal slat fences, a broad concrete driveway with grass
    or gravel joints, and large concrete pavers.
  - Back garden: an ipe landing with one step behind each of the two sliding doors (the sheet's
    landings since the eighth round; a deck off the living room before), a lawn and river-pebble
    borders.
  - Planting: ornamental grasses and Mediterranean shrubs, plus multi-stem trees (birch, olive,
    crape myrtle).
- **Staging.** Real-estate-listing calm: few, well-chosen objects, nothing cluttered, everything
  touching the floor or wall it rests on. The palette is warm white, oak, walnut, black,
  ochre and sage.

Daylight is a late-morning sun from the south-east plus a sky HDRI whose bright side stands at
the sun, so the sky over the north-facing garden is the deep-blue side ("Seventh round"), with
the interior lights on (warm). The renders are white-balanced neutral with a slightly warm tilt,
like a listing photographer's.

## Owner's style images (third round, 2026-11-19)

The owner's reference photos in `styles/` (reference only; never copied into the site) override the
language above in four places:

- **Kitchen** (`kitchen_dining_*.py`): warm vintage-American in soft layered neutrals. Cream shaker
  cabinetry with unlacquered brass cup pulls and knobs, glass-front uppers and a greige tall wall
  (the code's "pantry wall") for the refrigerator and the oven tower; since the seventh round a
  stainless refrigerator stands in it in plain view, beside a built-in microwave. A cream plaster
  hood with a dentil band over a scalloped marble splash and a brass pot filler; walnut open
  shelves on whitewashed brick. A fireclay farmhouse sink under a three-sash grid window after
  `styles/kitchen window.jpg` (black steel in this round, white since the seventh) with brass
  sconces and linen cafe curtains. A white-oak island with a honed quartzite top, brass pendants,
  a Persian runner, and a warm oak dining set under a brass lantern.
- **Primary bath** (`baths_primary.py`): the floating solid-oak double vanity with two carved basins
  (`styles/primary bathroom sink.jpg`). The rest of this round's bath was replaced in the sixth
  round, which rebuilt the room after `styles/primary bathroom wall style.jpg`, and the seventh
  made its other walls white: see "Sixth round" and "Seventh round".
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
   4 ft apart with at least 1.2 ft of clearance: 43 instead of 27 (49 since the sixth round, 52
   since the seventh, 53 since the eighth). Soft
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

The rules as they stand after the eighth round.

- **Levels.** The house floor is y 0. The garage floor, the porch slab and the two rear landings
  lie lower (`LEVELS`, read from `bl/garage_spec.py` and `bl/zones/exterior_layout.py`; README,
  "Architect's plan and the owner's changes"). Every height below is counted from the level of the
  place, and a sweep's eye is 5.0853 ft above the level it stands on (`level` in `sweeps.json`).
  The step at the door between the house and the garage is furniture for a sweep and floor for a
  walking line (`STEPS`). Until the seventh round every sweep stood on y 0.
- **Standable cell** (0.25 ft grid): a ray down from eye height lands −0.03..0.15 ft from the
  level of the place and a ray up hits a ceiling. Clearance = the nearest surface in 16 directions
  at 0.6 / 2.0 / 3.5 ft and eye height, limited by the distance to the nearest cell with furniture
  below the eye.
  Reachable = flood fill from the existing stops over cells with ≥ 0.9 ft clearance.
- **Rules:** clearance ≥ 1.2 ft (≥ 0.8 ft only for a seed or a room that would otherwise have no
  sweep); ≥ 4 ft between sweeps that see each other, ≥ 3 ft for doorway, bridge and kept approach
  sweeps; a cell with < 1.5 ft clearance that is not the middle of a passage needs ≥ 5 ft; at most 4 in
  the garage; no second sweep in a bathroom (`FILL_ONE`: the only floor 4 ft from the first one is
  inside the shower); every room region with standing room has a sweep. The reach-in closets of
  Bedrooms 2, 3 and 4 and Bedroom 3's bay count as covered by their rooms.
- **Seeds** (E0 H1 H2 H3 B3 B4 K0 D0 L0 L1 L2 P0 S0 C0 A0 B2 A1 G0 A3) keep their id and position;
  one with less than 1.2 ft clearance is nudged by up to 1.5 ft. A stop the model no longer suits is
  moved or dropped in `apply_revisions_web.py` (`NODE_MOVES`, `NODES_GONE`), not in `sweeps.json`:
  `apply_relayout.py` rebuilds the stops from the concept plan and the placement keeps a seed where
  the scene has it. Both tables act on the seeds only, never on an installed tour. Entries: K0, at
  the west end of the work aisle since the fifth round (the dining chairs stand where the concept
  had it); H3, A3 and G0 since the eighth; C3 is gone (below).
- **Stops set by hand** (`PLACED`; eighth round). Eight places written from the spec modules'
  names, each with its reason: T2 in front of the suite entry and Bedroom 2's door, H5 where the
  hall's two legs meet, H0 on the centre line of the hall's east leg, Y0 and Z0 in the middle of
  the two bedroom doorways, G0 on the garage floor clear of the step and of the open door leaf, L0
  in front of the sofa 1.5 ft clear of the coffee table, K2 in the mouth of the aisle between the
  island and the east counter. They are put down before the seeds, where the place is standable
  with the keep clearance; where it is not, the rules decide and a note says so. Earlier rounds
  set no stop by hand. The rules alone left T2 beside the suite entry's parked panel, put nothing
  at the hall's corner and moved Z0 into the foyer, and the grid's measure of clearance does not
  see a lever, a table's rim or a worktop's edge.
- **The laundry sweep** `LC` stands in the foyer on the axis of the closet's opening,
  `LAUNDRY['dist']` (4 ft) in front of the door wall, and looks at the units with a pitch of
  `LAUNDRY['pitch']` (−14°). From 3 ft the stacked pair spans 79°, more than the page's 68° picture
  holds; from 4 ft it spans 67° and both units are in the opening view. The closet's rectangle and
  opening come from `bl/revision_spec.py`.
- **The walk-in closet's stop** `C0` (`WALKIN`, `place_walkin`; sixth round) is the one seed that
  does not keep its place: the concept's position lies under the closet's south rod. When it has
  lost its clearance it goes to the most open reachable cell inside the closet
  (`SUITE_CLOSET_CLEAR`), among equals the one nearest the pocket door's axis: (4.50, 16.75). A
  6 × 8 ft room hung on three sides leaves an aisle 3.5 ft wide; the usual
  1.5 ft nudge left the camera at its edge, on a line to the vestibule that passed 0.2 ft from the
  leaf's nose. The rule fires only when the stop fails, so a second run keeps C0.
- **Keeping a layout** (`--keep`). A panorama stays valid only while its sweep does not move and
  nothing it sees changes. So after a local change the placement starts from the installed sweeps
  instead of the seeds, and only the sweeps that moved, are new or have a line of sight to a change
  are rendered again (README, "Add or move sweeps" and "Re-render a subset"). Kept sweeps are not
  held to the spacing rule among themselves: K0, moved by the scene, stands 2.8 ft from K3, the
  tour's shortest link. A kept sweep's name follows the scene file (`kept_renames`): a renamed seed
  takes its new label, and so do the kept sweeps that carried its old one (S1 had S0's); an
  outdoor sweep takes the label `OUTDOOR` gives its id (OD, "Rear landing" since the eighth round). A kept
  sweep stays while it has `--keep-clear` of clearance (0.9 ft by default; 1.2 ft, what a new
  sweep needs, when every panorama is rendered again anyway, as in the eighth round). A kept seed
  that fails it is placed again from its stop in the scene file.
- **Opening views.** A seed keeps its authored view, a new sweep looks in its most open direction,
  a kept sweep keeps what it had. `OPENING` in `apply_sweeps.py` overrides that at every install
  with views chosen by eye on renders: G0 and H2; since the sixth round C0 (the closet's
  hanging wall), S1 (through the bath door at the stone wall), A0 (across the vanity) and P5 (the
  bed between the two windows); since the seventh L7, L8 and D0 ("Seventh round"); since the
  eighth A3, H3, H5, H0, H4, T2, K2, Y0, Z0 and D2 ("Eighth round"). A card of the highlight reel
  opens its sweep at this view.
- **Link** = a straight line up to 11 ft that a person can walk (rays at four heights and three
  lateral offsets, bare floor under all three lines; between two levels the lines slope from one
  end's height to the other's), dropped when a third sweep gives two shorter
  legs with less than 20 % detour. Links never pass through glass and must form one component.
  **Visible** = a clear line at eye height and 1 ft below, up to 40 ft, through clear glass; always
  a superset of the links. The page draws rings at the visible sweeps.
- **Ids:** two characters, the first a letter. Seeds keep theirs. New ones are the region's letter plus
  the first free character: L living, D dining, K kitchen, G garage, F foyer, H halls, P primary
  bedroom, S the primary suite's vestibule and walk-in closet (one region, `primary_dressing`),
  A baths, C closets, X / Y / Z = Bedroom 2 / 3 / 4. `LC`, `OP` (porch) and `OD` (the rear landing
  outside the living room; labelled "Rear landing" since the eighth round, its room key is still
  `deck`, as published) are fixed.
  No new id reuses an old one, nor one an earlier round retired after its panorama was published
  (`RETIRED`: L5, C3).
- **Angles:** `sweeps.json` and `assets/data/tour.json` hold degrees; nodes in `scene.json` hold
  radians, as they always did. Yaw 0 looks toward −z (north), positive clockwise seen from above.
- The outdoor sweeps exist only while a walkable line through an open door joins them to an indoor
  sweep: `OP` through the front door, `OD` through the open way of the living room's sliding door
  (the schedule's `way_start` .. `way_end` of D14). The exposure smoothing leaves indoor / outdoor
  links alone.

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
- `check_holes.py` works on a grid (0.2 ft in this round, 0.05 ft since the eighth). The warp maps
  the two front corners of the central ceiling
  panel with different rooms, which left a hairline up to 0.03 ft wide, open to the attic, along the
  kitchen / garage wall at the hall end of the kitchen's tall wall; only a scan at 0.015 ft pitch found it
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
Bedroom 4 zone, the sweep placement and the web data derive from them. The coordinates below are
the eighth round's: the closet keeps its clear size and its place in Bedroom 4's corner, and its
walls are 5 in like every wall.

- **Position and size.** Bedroom 4's north-east corner. Clear inside 3'-0" deep (east-west) ×
  2'-10" wide (north-south): `LAUNDRY_CLEAR`, x 12.142..15.142, z 28.892..31.725, 8.5 sq ft, under the
  room's flat 8 ft ceiling. The north side is Bedroom 4's north wall, the east side the
  Bedroom 4 / foyer wall (`LAUNDRY_HOST_WALL`, shell piece 3338). Two new walls, 5 in thick
  (`LAUNDRY_WALL_T`; 0.36 ft until the seventh round),
  floor to ceiling: west (the units' back wall, x 11.725..12.142) and south (z 31.725..32.142).
  `laundry_walls()` and `laundry_host_wall()` give the boxes, `LAUNDRY_OUTER` the rectangle over the
  walls.
- **Doors (D17).** An opening 2'-6" × 6'-8" in the host wall, centred on the units
  (`LAUNDRY_DOOR_Z`, z 29.058..31.558; 2'-5 1/4" between its jamb liners, which is the width the
  Dimensions sheet gives since the eighth round). A pair of flush white leaves, 1.204 ft each,
  hinged on the two jambs, swung out into the foyer and shown open 160°
  (`LAUNDRY_DOOR_OPEN_DEG`), nearly flat against the foyer wall, where they take 0.58 ft of the
  foyer's 5.75 ft. The brief said "about
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
  z 29.01..29.67, y 3.50..4.10, 0.24 ft deep; the wall is split around it) with valves and hoses,
  the dryer's vent duct to a wall collar at 7.25 ft, a 240 V receptacle. A flush ceiling light sits
  just inside the door head (`LAUNDRY_LIGHT`).
- **The revision** (`revisions.laundry_closet`, after the warp, before `floor_gaps` and
  `skirting_trim`). The host wall keeps its part south of the opening; the return north of the
  opening, the header and the two new walls are copies of it (`_like`), so they carry its paint and
  `scene_index` and bake as walls. The host wall's two baseboards are cut at the jamb liners; new
  runs go on every new face, with a block at the outside corner. An oak patch lies just under the
  floor over the closet's footprint, because the floor slab stops short of the north wall under that
  wall's baseboard.
- **Bedroom 4** is L-shaped: 14'-11" × 8'-0" overall, less 3'-5" × 3'-3" for the
  closet and its two walls (108.22 sq ft; with the walls of the fifth round: 14'-10 3/8" wide, less
  3'-4 3/8" × 3'-2 1/4", 108.15 sq ft). Bed, nightstand, rug and pendant stay. The
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
- **Limits.** From the front door the open leaves show but the units do not (they stand 0.52 ft
  behind the foyer's wall face); they come into view from about z 40 northward. With the leaves open, their
  pulls face the foyer wall. The dryer vent enters the wall shared with Bedroom 4; a real duct would
  turn up into the attic inside it.

Naming rules the closet depends on: its contents are named `laundry closet ...` (the bake files them
as `base`, the sweep placement looks for `laundry` / `washer` / `dryer` inside `LAUNDRY_OUTER`);
nothing with a glass-named material goes into the `openings` collection (it would get a light
portal); appliance parts are not named "door" (the bake files those under walls), hence "hatch"; the
art on the closet's bedroom faces has no "closet" in its names (the bake would file it as a
built-in).

### Dining table and kitchen

- **The table** continues the island's west end, toward the hall: 6'-0" × 2'-9", on the island's
  centre line, its east end 0.02 ft short of the island worktop. Six chairs, three on each long
  side, none at the ends, no rug, the brass lantern over the middle. The floor between the island
  and the living room is open and stays so. As built since the eighth round, when the island
  became the sheet's 7'-0" × 4'-0" (x 26.808..33.808) and the table moved west with its end:
  table x 20.79..26.79, z 21.68..24.43, the chairs' backs at z 20.62 and 25.49. Every way past it
  keeps 3 ft: 3.06 ft from the north chairs to the closet block's south face (the way from the
  hall to the living room), 3.50 ft from the south chairs to the tall wall's cabinet fronts,
  3.30 ft to the refrigerator's doors and to the oven's handle, 3.10 ft to the refrigerator's
  handles; 5.2 ft between the table's west end and the shared bath's east wall.
- **How it is placed.** The set is loose furniture: `bl/warp.py` moves its cluster by the shift of
  the cluster's centre and keeps its size, while the island is fitted and shrinks with the room. So
  `kitchen_dining_dining._rect_centre()` states the position on the built plan (`RECT_GAP` short of
  the island worktop's west edge, `kitchen_dining_kitchen.ISLAND`) and carries the centre back to
  the concept plan with the inverse of `relayout.X_HALL`. Keep the set symmetric about the table's
  centre (the lantern's fitted rod is mapped by the same point) and put no recessed can over it (cans
  are loose and would join the cluster). After a change, compare `'dining': {'plan': ...}` in the
  build log with the built objects.
- **Kitchen south wall:** the third-round layout again, west to east: end panel toward the hall |
  refrigerator bay | oven tower | counter with three glass-front uppers | cooktop under the hood |
  base run to the corner. What stands in the bay and the tower changed in the seventh round; the
  eighth made the counters 2'-0" deep and left everything in its place along the wall
  (`appliance_plan()` and `island_plan()` print the built numbers in the build log).
- **Hero stills.** `K0` stands in the hall and looks east along the table to the island and the
  tall wall; `B4` takes in the desk niche.

### Repairs found in review

- **Coplanar slabs.** Two faces of different objects in one plane shade each other in Cycles (a
  darker band with sharp edges) and flicker in the web model. The slab warp had left two such
  overlaps, both in front of the new closet. `revisions.floor_overlap` puts the north edge of the
  oak slab under the Bedroom 4 / foyer row on the south edge of the slab north of it (a wedge up to
  0.16 ft wide across Bedroom 4 and the foyer). `revisions.ceiling_overlap` starts the bedroom-hall
  ceiling on the central ceiling panel's front edge, the kitchen / garage wall's line (they
  overlapped over the foyer's north end); it runs after `ceiling_seam`, which squares that edge, and
  before the skylight cuts. Both end the two slabs on one line. Offsetting one of them instead
  leaves walls in the air, or two surfaces a fraction of a millimetre apart.
- **Foyer / kitchen wall corner.** The garage's west wall and the kitchen / garage wall each stop on
  the other's centre line, which leaves a notch of half a wall each way (0.21 ft with the 5 in
  walls), floor to ceiling, beside the refrigerator's end panel
  (`revision_spec.FOYER_CORNER_INFILL`). The kitchen closet had filled it.
  `revisions.foyer_corner` fills it with a copy of the garage wall and lays an oak patch under the
  baseboard at its foot, where the floor slab's skewed edge stops short of the kitchen wall.
- **Checks to repeat after any change to slabs or walls:** `check_holes.py` (`no holes`); a
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
| Where the stacked stone of the wall image goes | the two shower walls | **the vanity wall** (the south wall, behind the vanity and the mirrors); plain tile in the shower (cream then, white since the seventh round) |

Two of the four recommendations were wrong. The answers override everything else, the sheet
included (W14); where the answers and the request are silent, the sheet decides.

### Primary suite

Numbers: `bl/revision_spec.py`, `SUITE_*` (SCENE feet on the architect's plan). The clear sizes of
the primary bedroom (11'-1" × 12'-3") and the primary bath (9'-6" × 7'-2") already matched the
sheet. The 8'-0" zone between them (z 12.892..20.892 in the sheet's frame), one open area with
wardrobes until the fifth round, is two rooms as on the sheet.

- **Walk-in closet** (M05, sweep C0): an enclosed room without a window, clear 6'-1" × 8'-0"
  (`SUITE_CLOSET_CLEAR`), behind a new 5 in wall (`SUITE_CLOSET_WALL_X`, x 6.308..6.725). Rods and
  shelves on the north, west and south walls as the sheet draws them, a drawer and shelf tower in
  the middle of the west wall, facing the door, and a flush ceiling light. The aisle is 3.5 ft
  wide.
- **Pocket door** (D18): clear opening 2'-6" × 6'-8", centred on the closet
  (`SUITE_CLOSET_DOOR_CLEAR_Z`, z 15.642..18.142, between the jamb liners since the eighth round;
  the wall opening `SUITE_CLOSET_DOOR_Z` is one liner wider on each side, and until the seventh
  round the 2'-6" was that wall opening); the leaf slides south into the wall. The brief had the door at the wall's
  south end, sliding north: it had taken the leaf, which the sheet draws open inside its pocket,
  for the opening. At 1200 dpi the sheet shows a full jamb, a split jamb 2'-6" south of it, and
  the leaf in a pocket sleeve beyond with its nose out. The leaf is shown 0.30 ft out of the
  pocket (`SUITE_CLOSET_LEAF_SHOWN`; the sheet draws about 0.27), which leaves a 2.23 ft passage
  (2.17 ft with the narrower opening of this round).
  The brief's "about a third out" would leave 1.67 ft, and the sweep placement, which floods the
  floor with a 0.9 ft body radius on a 0.25 ft grid, needs about 2.05 ft to reach the closet.
- **Vestibule** (M14, sweeps S0 S1): clear 4'-7" × 8'-0" (`SUITE_VESTIBULE_CLEAR`), open to the
  bedroom over its whole width under the existing header (D10, no door). The sheet's "(E) 30X22
  ATTIC ACCESS" is a flush panel in a thin frame on the ceiling (`SUITE_ATTIC_HATCH`; nothing is
  cut). One mirror on the closet wall.
- **Suite entry** (D09): a 2'-8" opening with a flush sliding panel on a slim black track on the
  hall face, shown open, parked south of the opening. **In this round and the seventh it stood
  1'-8" south of its place on the sheet.** On the sheet that stretch of the wall faces the hall;
  in the model of those rounds it backed onto Bedroom 2's entry alcove (the concept's layout,
  behind the doorless opening D12), so an opening at the sheet's place would have led into
  Bedroom 2, and the entry was built as far north as the hall allowed. Following the sheet needed
  Bedroom 2's entry and closet re-planned, which the owner had not asked for. The eighth round
  did that: the entry now stands at the sheet's place (`SUITE_ENTRY_CLEAR_Z` =
  `SUITE_ENTRY_SHEET_Z`, z 13.610..16.277 between the liners), 2'-8" clear, with a 3'-4" panel
  as drawn.
- **Bedroom**, furnished as drawn: a king bed with its headboard on the west wall, centred on the
  room (z 6.35) between the two west windows, a nightstand each side, a rug. Both west windows
  stay: W15, and **W14 by the owner's decision**, although the sheet shows only W15. The bed as
  drawn is 7.06 ft wide with its headboard and the pier between the windows 4.97 ft (5.26 ft
  until W15 became the sheet's 3'-0" in the eighth round), so nothing
  on that wall rises above the 2'-6" sills where glass is behind it: the headboard is 2'-4 1/2"
  high, the nightstands 1'-4 3/4" with small dome lamps. No dresser on the east wall (it would
  leave 2.4 ft at the bed's foot): 3.6 ft stay clear from the vestibule to the sliding door.
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
  wall, a slot from 6'-8" to the ceiling that the old door's casing had hidden; the round
  carried it to the wall (`SUITE_BED2_HEADER`). Since the eighth round that piece is the header
  over Bedroom 2's door in the bedroom's south wall, placed by `hall_block`.

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
- Window W13 at the sheet's place, 3'-0" wide (`BATH_WIN_Z`, z 23.003..26.003; the sheet's line
  work puts it 1/4 in further north), with the owner's
  vertical size of the third round: 2'-0" sill to the ceiling, transom at 6 ft, clear glass. Its
  mullion stands on the shower's south glass line (`BATH_WIN_MULLION_Z`, z 24.323), 0.2 ft north
  of the window's centre where the sheet has it, because a glass panel cannot end on glass. The
  north sash is inside the shower (stone sill, tiled reveal); the south sash has a stool and
  the roman shade.
- Skylight W20 (second round: "over the shower") moved with the shower (`PRIMARY_BATH_SKY`).
  It is cut into the shell as built, so nothing is left where it was.
- Finishes take room: the shower tile and the tile base 0.065 ft on a wall, the stone up to
  0.15 ft, so the toilet's tank stands 0.19 ft off the structural wall. The painted walls carry
  no finish: the vanity slab runs its full 6'-6" to the east wall.

**Style, after `styles/primary bathroom wall style.jpg`** (rustic, warm, low saturation), with the
stone where the owner put it, and since the seventh round with white walls where the image and
the sixth round had green boards ("Seventh round"). Materials are `Z_baths_primary_*`
(`baths_primary_mats.py`).

- South (vanity) wall: stacked natural stone over the full width and height, in true displacement
  (Poly Haven Rustic Stone Wall 02; `STONE_SIZE`, `STONE_STRETCH` and `STONE_MID` set the size of
  the stones and the flush sandy mortar bed). On it two oak-framed mirrors, and above them a
  rough dark timber beam with an enamel lamp over each basin.
- Shower: plain matte white tile, 24 × 48 in, on its two solid walls, a white mosaic floor,
  off-white stone trims and low-iron glass. No stone, nothing glazed.
- Other walls: the house's plain white painted wall from the floor to the ceiling, above a
  5 5/8 in base of the shower's tile; the house's white ceiling, with one timber beam across it.
- Floor: quiet warm-grey stone, 24 × 24 in, no pattern. Fittings in brushed nickel. A timber shelf
  on iron brackets with bottles, a botanical print and a trailing plant; striped towels, a cactus
  in a zinc pot, a fringed mat.
- What differs from the image: the walls beside the stone are white, not green boards (the
  owner's seventh round); the room is lit by daylight with the lamps as warm accents, the image
  by one lamp at dusk; the stone's courses are more regular; the floor is lighter; the window
  has a white frame with grid bars, like the house's.

The room is fitted out by `baths_primary.build_room` after the warp (see "Which plan" in the code
contract), so its patterns are laid out on the built room: tile courses start at the floor and the
niche's sill sits on a joint, the floor grid is centred on the room.

### Bedroom 3 bathroom: the taller shower window

W11 on the west wall keeps its 3'-0" width, its frosted glass and its two-sash frame (black in
this round, white with grid bars since the seventh). Sill
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

- 49 sweeps and 58 links in this round (52 and 67 in the seventh, 53 and 70 since the eighth).
  Placed with `--keep`: 43
  stay; C0 moves to the middle of the closet's aisle
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
  in the Dimensions sheet and the round's change list stated the 1'-8" and its reason. Both
  texts were computed from the spec, so they went when the entry moved in the eighth round.
- **A room that must sit on the sheet's lines is fitted out after the warp**, in plan feet. The
  warp moves loose pieces in clusters and decides by name what is loose; that is fine for
  furniture in a room and wrong for a glass line that has to meet a mullion.
- **A door that moves keeps its SCENE leaf**: the old leaf box is moved in place, because the plan
  draws every box of group `door` and an object's index may not shift (since the eighth round a
  piece that is gone for good is marked `removed` instead). `tools/web/dimension_plan.py`:
  a door tag with a room label on both sides of its wall (D18, between the closet and the
  vestibule) slides along the wall to the nearer end of those labels.

## Seventh round (2026-11-21): refrigerator, white windows, white bath, no fireplace, north light

The owner: "put the refrigerator next to the microwave, there is no refrigerator now"; "Set all
windows to white color, and it should have grid line for these windows"; "The walls in primary
bathroom, it's not coherent, some of the wall are green, make it coherent be removing these green
walls and set it to white"; "Seal off the fireplace so that we could put sofa on the fireplace
side, and put a TV on the other side of the wall so that we could watch TV"; and in a second
message: "I think the light is not correct in your model, the yard is facing north".

**The exterior was asked for and set aside.** With the first message the owner asked for an
exterior after 1073 W McKinley Ave, then wrote "forget the exterior now". No photos of that house
were found online. Roof, massing, entry and facade are as they were; outside, only the white
frames and grid bars are new. The round's change list in the Design sheet says so.

How each sentence was read went to the owner before the build, and there was no objection. No
wall and no opening moved in this round: every number in the Dimensions sheet stayed as it was.
(The eighth round then moved every wall onto the sheet's lines; coordinates in this section are
given in that frame where they are given at all.)

### Refrigerator and microwave

The refrigerator was integrated: greige shaker panels at the hall end of the kitchen's tall wall,
beside a tower of two wall ovens. The owner read the panels as a pantry and the tower's upper
unit as the microwave.

- The bay (x 22.01..24.93) is open to the wall and holds a stainless French-door refrigerator
  with a bottom freezer drawer: 34.8 in wide, 70.6 in to the hinge covers, the case flush behind
  the cabinet fronts, the door faces 0.20 ft in front of them and the handles 0.40 ft.
  Above it a two-door cabinet from y 6.03, on one line with the tower's top door.
- The tower's upper unit is a built-in microwave in a 27 in trim kit (y 3.92..5.50; black glass
  door, control strip with a lit clock), over the unchanged wall oven (y 1.60..3.78). The
  refrigerator's door edge is 0.7 in from the trim kit. All three share the library's `stainless`.
- **Fitted, in plan feet.** The relayout map's slope changes inside the bay, so a refrigerator
  written in concept feet comes out lopsided. `_refrigerator()` and the cabinet doors over it are
  dimensioned on the architect's plan through `kitchen_dining_cabs.PlanFace` (the inverse of
  `relayout.X_HALL` / `Z_RIGHT`), and every part is named `kd refrigerator ... panel`, which
  `bl/warp.py` treats as fitted. Keep the warp's loose words out of those names (`fridge`,
  `freezer`, `handle`, `pull`, `hinge`, `post`, `bar` ...). The microwave is loose like the oven,
  as `kd microwave oven ...`: "microwave" alone contains the fitted word "wave".
- **Departures.** 34.8 in, not a 36 in unit: the bay is 35.1 in and nothing else was to move.
  The handles are brass like the kitchen's hardware and the oven's since the third round
  (`APPL_HANDLE = 'stainless'` turns all three). The walkway from the south chairs was 2.81 ft at
  the refrigerator's handles (3.06 ft at the old pulls); with the eighth round's 2'-0" counters
  it is 3.10 ft.
- The `K0` still is aimed 5° further right, so that the refrigerator is whole in the frame.

### White windows with grid bars

One late revision on the built model, `revisions.white_windows` (numbers `WINDOW_*` in
`bl/revision_spec.py`). A window is every upright pane of `glass_clear` or `glass_frosted` in the
`openings` collection whose name has no "skylight", whoever built it: no window builder was
edited, and a window added later is covered. The eighth round's units were: its two sliding
glass doors, the rebuilt windows and the front door's sidelights got their white frames and
grids without a change to this revision. How to change a grid: README, "Change a window's
grid".

- **White.** Every frame piece in `openings` that carried `black_aluminum` (heads, sills, jambs,
  mullions, transom bars, the stiles and rails of the sliding doors) takes the
  new library material `window_white` (#f5f4f1, satin). So do the primary bath's stool and
  mullion post and the slider's pull bar (`WINDOW_WHITE_ALSO`), and in the kitchen zone W08's
  casing and stool. Not touched: the skylights' frames, shower glass, mirrors, cabinet glass, the
  garage door and its lites, the front door, shades and curtains, the charcoal fascia.
- **Bars.** 7/8 in wide, 0.03 ft proud of each face of the glass, chamfered. A bar is one piece
  through the pane, so no bar face lies in a glass face. Vertical bars run through, horizontal
  bars between them, and all end inside the frame members; where a sash is shallower than the
  bars are proud (the sliding doors' panels) they stop just inside it. The panes stay light
  portals. The bars take at most 5 % of a room's light (0.07 stop).
- **The lite rule.** The house's lite is 14 × 16 1/2 in (`WINDOW_LITE`). Each daylight opening,
  the glass between two frame members, gets the whole numbers of columns and rows that bring its
  lites closest to that (in log space), with no lite wider than 1.2 × its height. The sashes of
  one window share their rows. An upper tier lower than 0.6 × the tier under it is a transom:
  one row, the columns of the sash below. So the bars run on in line across mullions and
  transoms, and windows of one height have their bars at the same heights round the house.
- **W08** keeps the 2 × 4 lites per sash it had as a black steel window, after the owner's
  `styles/kitchen window.jpg` (`WINDOW_GRID_KEEP`); the rule alone gives 2 × 3.
- **Repairs on the way.** The centre mullions of W02 and W11, which the warp had left 0.13 and
  0.18 ft off centre, are back in the middle (`WINDOW_MULLION_CENTRE`): with a grid the two
  sashes would show lites of two widths. (Since the eighth round W02 is rebuilt with its mullion
  in the middle, and only W11's is moved.) The bay's three roller shades stood outside the glass
  or askew to it, and the cassettes of W10 and W12 reached into the bars' depth: each is set
  square to its pane, 0.01 ft on the room side of the bars.

Each window's grid is in `WINDOW_GRIDS` (`apply_revisions_web.py`, checked against the build with
`--check-grids`) and, with its lite sizes, on the `revisions:` line of every build: on the
eighth-round model for example 1 × 3 lites per sash in the narrow west windows W11, W14 and W15,
2 × 5 in each panel of the two sliding doors, 1 × 4 in the front door's sidelights.

**Departures.** The lite is not one size (10.5 to 18.1 in wide, 12.7 to 21.4 in tall on the
eighth-round model), because the sashes differ. W14 had only a cross in this round, because its
two sashes were stacked (2 × 1 lites of 15.4 × 24.4 in); the eighth round's last build gave it
W15's unit, two sashes side by side with 1 × 3 lites of 14.6 × 16.8 in. The shell's frames are the old slim profiles, so a two-sash window reads as one grid.
D14, in this round a hinged glazed door and since the eighth the living room's sliding door,
is treated as a window. W08's casing, W13's stool and the sliding doors' pulls are white
although the request names the windows.

### Primary bath: white, with one stone wall

- Removed: the grey-green board wainscot, its cap rail, and the cream plaster skins on walls
  and ceiling, with their materials.
- Every wall except the vanity wall is the shell's own painted wall (`paint_wall`, the house's
  wall white) from the floor to the ceiling; the zone builds nothing on it. At the floor runs a
  5 5/8 in base of the shower's tile, 0.065 ft thick: it covers the shell's skirting, which has
  gaps where the old door and the old window were. The ceiling is the shell's, at y 8.0.
- Shower: matte white tile, a white 2 × 2 in mosaic floor, off-white stone threshold and sills,
  white edge profiles where the tile ends, and low-iron glass (`baths_primary_kit.glass_panel`):
  through the house's `glass_clear` the white tile read pale aqua.
- Kept: the stacked stone, both beams, the mirrors, the vanity, the lamps, the shelf, the floor,
  the fittings and the layout ("Sixth round").
- What remains uneven: the white is warmer near the two 2900 K lamps and dimmer beside the
  stone (bounced light, not paint). The door's jamb liners stand 0.085 ft proud of the painted
  wall (`BATH_DOOR_LINER_PROUD`, sized for the wainscot; it must stay at least 0.065, because the
  base ends on the liner). The shelf's green bottle and the plants stay.

### Living room: no fireplace, sofa east, television west

The fireplace was a mass that the living zone built in front of the east wall: stone surround,
firebox, flames, a walnut ledge. The wall behind it was never cut and the shell has no chimney.
So the zone no longer builds it (`living_fireplace.py` and `living_fire_mats.py` are gone), and
the east wall is the shell's painted wall with one unbroken baseboard.

- **Furnished as the architect's sheet draws it**, on the axis z 8.05. The sofa stands against the
  east wall (z 4.40..11.70), facing west, its north end under the east window and below its
  glass, with a side table at each end (a lamp on the south one; the north one stands under the
  window since the eighth round made that one 6'-0" unit, and carries nothing above the sill) and
  the canvas over its south half. Opposite, on the west
  wall, a 75 in television (z 5.31..10.79, y 2.32..5.44; dark, not emissive) over a low white-oak
  console (z 4.30..11.80). A round coffee table on a round rug, one armchair to the north-west, a
  money tree beside the console, twelve cans (laid out round the skylight's well since the
  eighth round). Every position is in the docstring and the constants of `living.py`.
- Clear: 7.58 ft between the coffee table and the console (the walk from the dining area to the
  rear door), 4.50 ft between the rug and the console, 2.33 ft between the armchair and the
  rear glass; every line from a sofa seat to the screen. In this round furniture covered 55 of
  the room's 249 sq ft (71 before).
- **In plan feet, under one root.** `living.py` is written in SCENE feet on the architect's plan
  and builds with the other zones; every object hangs under the Empty `TG living root` at the
  origin, and `bl/warp.py` skips objects named `TG ...` and objects with a parent. `build()`
  measures the clearances on the built meshes and lists in `notes` what does not hold.
- **Departures from the sheet and the request.** The sofa is 7.3 ft long (7.9 before), to stand
  on the sheet's z 4.4..11.7. The rug and the coffee table are new, round as drawn. One armchair
  instead of two, at (30.16, 3.75) and not at the sheet's (33.5, 2.3), where it would stand 0.9 ft
  from the rear glass and on sweep L1; it stands in front of the sliding door's two west panels,
  2.33 ft off them and 0.33 ft clear of the door's open way (the eighth round moved it 0.35 ft
  west for that). The television is 75 in; the sheet's symbol is about 69 in. The canvas is smaller and
  hangs over the sofa's south half, because the window takes the north half. The floor lamp, the
  pampas and the ledge's vases are gone; the tree moved from the north-east corner to the west
  wall. The sheet's "(N) SKYLIGHT" over the sofa was not in the model in this round and was not
  asked for; the eighth round built it (W21).
- The still `living` looks north from (31.0, 4.8, 20.3): the television wall on the left, the
  rear glass, the sofa wall on the right. The Design sheet has no view of the living room.

### Daylight: the yard faces north

The plan was oriented correctly (garden = north = SCENE −z) and so was the sun lamp: azimuth 128°
clockwise from north, elevation 42°, a late-morning sun near an equinox in Sunnyvale, with the
house's shadow on the near lawn. The sky was wrong. `_hdri_sun_rotation()` took the equirect
image's centre column for −X; Cycles has it at +X. The HDRI's glow therefore stood at azimuth
−52°, in the north-west over the garden, exactly opposite the lamp, in every published render
with this sky.

- **Fix:** one line in `bl/lighting.py` (the Mapping rotation goes from 183.77° to 3.77°). The
  physical-sky fallback had an error of the same kind (the Sky Texture's `sun_rotation` is a
  compass azimuth; the code took it counter-clockwise) and is corrected too; it was in no
  published image. Sun azimuth, elevation and strength are unchanged.
- **The sky is now measured:** every build renders the finished world alone, logs where its
  bright side stands against the lamp and stops on a mismatch (README, "How the look is
  controlled").
- **A north-facing yard, checked by ray casts on this round's model** (28 panes, 600 points each):
  no direct sun through any north or west pane. Sun entered through the four east panes (living
  room ×2, dining, kitchen), the bay's centre and east sashes, the window above the front door
  and the four skylights. The rear facade and the deck by the house were in open shade; the one
  lit patch on the deck was the east window's beam leaving through the glass corner. (The check
  was not repeated on the eighth round's model, which has other east windows, a fifth skylight,
  1'-0" eaves and landings in place of the deck; sun and sky are unchanged.)
- The sky over the garden is half as bright as it was, so the north rooms lost sky fill and
  every pin of the earlier runs was stale.
- Left as it is: the HDRI's own sun stands 48° up, the lamp 42° (the azimuths agree).

### Sweeps, pins, renders

- 52 sweeps, 67 links. Placed with `--keep`: 48 stay and none moves; L5 goes (it stood where the
  sofa is); L6 to L9 are new, all in the living room: L6 at the rear glazing behind the armchair,
  L7 between the console and the coffee table, L8 at the room's south edge, L9 in the corner
  north of the sofa. The round coffee table stands on the old link L0-L1; the bridge rule placed
  L6 to rejoin L1 before the fill added L7, which joins it as well. The layout was kept as the
  tool made it.
- Close stops in this round: L0 was 0.93 ft from the coffee table's rim (the limit for a kept
  sweep is 0.9), L6 and L9 1.2 ft from the rear glazing's grid bars, K4 1.48 ft from the
  refrigerator's handles. The eighth round moved L0 and L9 clear ("Eighth round").
- Opening views (`OPENING` in `apply_sweeps.py`): L7 (yaw 85°, pitch −4°) the sofa wall; L8
  (0°, −4°) the television on the left, the rear glass, the sofa on the right; D0 (−172°, −3°)
  across the dining table at the refrigerator and the microwave.
- **The reel.** The "Living room" card is L8 (`HIGHLIGHTS` in `apply_revisions_web.py`). It was
  L0, which stands in front of the sofa and looks at the television with the sofa behind the
  camera. `build_site_data.py` enters an open space on its card of the reel, so the living room's
  name on the floor plan opens L8 as well (the sliding door D14 in the Dimensions sheet stands
  on L1 since the eighth round). The "Open living area" card, D0, now shows the refrigerator and
  the microwave. The
  "Kitchen" card, K0, still opens east along the work aisle, with the refrigerator behind the
  camera.
- Rendered again: everything. All 52 panoramas, the hero stills (the cameras `K0` and `living`
  changed), the bake and the 32 exterior frames, with pins from a fresh probe; the smoothing
  needed `--move-kelvin 2600`, and the outdoor sweeps' white balance was pinned by hand (README,
  "Render everything again").

### Process notes

- **Measure what a formula sets.** The sky stood half a circle off until the owner said so,
  because its rotation was derived and never compared with the lamp in a picture. The build now
  measures it and refuses a mismatch.
- **A finish that runs through the whole house is one late revision on the built model**, found
  by collection and material, not an edit in every builder.
- **Before removing a thing, find who builds it.** The fireplace was the zone's furniture in
  front of an uncut wall: no revision, no wall repair.
- **Where two places state one fact, a tool compares them.** The Dimensions sheet's texts give
  each window's grid, which the build computes: `apply_revisions_web.py --check-grids`.
- **The owner's words name what they see.** A panelled refrigerator was "no refrigerator", the
  upper oven "the microwave": the answer was to make the thing read as what it is.

## Eighth round (2026-11-23/24): the model on the architect's sheet

The owner asked for an audit: "double check the sizes.pdf and verify the model is correct built
based on the size and standard scaling factor". The owner read its report and wrote: "can you fix
all al these issues?"

### What the audit found

- **Scale: correct.** One model unit is one foot, and every room size the architect printed and
  the owner had not changed was reproduced.
- **Built to the sheet's sizes: only in part.** Of the 39 dimensions printed on SKA002, 19
  matched (within 1/2 in), 2 were within 2 in, 6 differed by the owner's decisions and 12 differed
  without a decision; of the 30 doors and windows drawn, 3 matched.
- **Why.** The walls kept the concept's thicknesses (4.3 in inside, 5.4 in outside, where the
  sheet draws 5 in everywhere), so the house measured 39.870 × 54.117 ft instead of 39'-11" ×
  54'-4" and wall faces stood up to 0.28 ft off the sheet's. Most doors and windows, the hall and
  closets beside Bedroom 2, the Bedroom 3 bath, the kitchen island, the roof, the eaves and the
  ground levels still followed the concept plan.

### What was done

In two stages, both measured on the built model against the sheet as data (every wall, opening
and fixture of SKA002 in SCENE feet, extracted from the PDF).

**Stage A: the frame.** The sheet is the model's coordinate system and every wall is 5 in
(README, "Architect's plan and the owner's changes": `relayout.py`, "the sheet's frame"). No
constant in the spec modules, the plan-feet zones or the exterior layout is an absolute number
any more: each is written from a wall face of `relayout.py`.

**Stage B: seven tracks, built in parallel on one checkout and then integrated.**

| Track | What follows the sheet now | Code |
|---|---|---|
| Hall | Bedroom 2's closet block (7'-8" × 4'-8") with the furnace and storage closets, the hall 3'-3" and 3'-4" wide, Bedroom 2's hinged door in its south wall, the shared bath's door with a leaf, the suite entry at the sheet's place | `bl/zones/hall_block.py`, block "v7 hall" |
| Kitchen | island 7'-0" × 4'-0", aisles 3'-6" and 4'-0", counters 2'-0" deep; the dining table moved west with the island's end | `kitchen_dining_kitchen.py` (`PLAN_*`) |
| Bedrooms | Bedroom 3's bath (shower 3'-0", toilet bay 2'-6", vanity bay 2'-9"), its reach-in closet, the doors of Bedrooms 3 and 4 with leaves sized to their openings, W12 5'-0", W10 removed | `bedrooms_rooms.py`, `baths_suite3.py`, block "v7 bedrooms" |
| Glazing | the living room's 12'-4" four-panel sliding door, the primary bedroom's 6'-4" sliding door, W15 3'-0", W02 6'-0", W05 one 6'-0" unit, W07 5'-0" | `revisions.py` (`_glz_*`), block "v7 glazing" |
| Garage | floor 11 in lower with a step at the house door, vehicle door opening 15'-0", the door to the house hinged on its north jamb, the side door, the front door with sidelights, a tank water heater | `bl/garage.py`, `bl/garage_spec.py` |
| Roof | every plane 5 in 12, main ridge 14'-7", garage ridge 12'-4 1/2", 1'-0" eaves, level wing and entry ridges, the entry gable over the porch; the living room's skylight added, the kitchen's at the sheet's size | `bl/roof.py`, `revisions.living_skylight` |
| Site | floor 11 in above the ground in front and 1'-2" behind, the two landings with equal risers, the porch slab, the driveway 18'-1" wide, six open outside corners closed | `exterior_layout.py`, `exterior_site.py`, `revisions.site_shell` |

The integration found ten places where two tracks met badly (a pier's stucco in the plane of a
room's painted wall, a wood-clad strip inside the foyer, a gable 1/2 in proud of the wall below
it, a slot behind the porch's pads ...) and fixed them; a review of every room and elevation
followed, and its repairs are marked `v7 repair` in the code (baseboards and their joints, two
floor pieces 0.1 in proud, the porch's side walls clad in wood from the slab to the soffit, the
porch slab's level, the olive tree moved from in front of the window W07 to the pier north of
it). A last build before the render (marked `v7 final`) set the kitchen skylight's well against
the east edge of the opening it replaced, so that it lies over the sink's bowl again (it had
kept the old opening's centre, which put it over the aisle); gave the primary bedroom's second
west window W14 the unit of W15 in its own opening (it had two stacked sashes and flush jambs
beside W15's frame, stool and side-by-side sashes); and put the open strip's and the kitchen's
ceiling cans on the living room's lines, one can fewer.

### Result against the sheet

Measured on the built model by the integration's script, which is kept in
`tools/render/sheet_check/` (README, "Verify", step 3); the numbers are those of the round's
final build:

- **SKA002's 39 printed dimensions:** 33 match (the largest difference 0.01 in), none is `small`
  or differs; the other six are the owner's decisions: the foyer-side wall (rows 12, 13, 18, 20)
  and the laundry closet in Bedroom 4 instead of the sheet's closet in the kitchen (rows 11, 34).
- **Outside:** 39.916 × 54.333 ft, 53.000 on the garage side.
- **Doors (20 on the sheet):** 16 match in place, clear width, type and hinge side; 4 are the
  owner's (Bedroom 4's entry and closet doors, the front door unit, the laundry closet).
- **Windows (10 on the sheet):** 6 match; 3 are the owner's (the primary bath's tall window, the
  bay, the kitchen window); 1 is a leftover symbol on the sheet. W14 and W17 exist in the model
  only, by the owner's decisions.
- **Skylights:** the living room's matches; the kitchen's has the sheet's size at the owner's
  place, over the sink; the two in the foyer and the one over the primary bath are the owner's.
- **Levels:** 49 rows match (floors, garage floor and step, ground, landings, driveway, and the
  porch against the round's own decision, below); 17 have no sheet value.
- **Roof:** all ten planes 5.000 in 12; main ridge 14.598 (the sheet prints 14'-7", 0.17 in
  less: 5 in 12 from the sheet's own fascia line over its own half span gives 14.597), garage
  ridge 12.375, eaves 1.000 ft.

### The owner's decisions that stay

All of them, exactly: the foyer-side wall of Bedroom 4 and Bedroom 3 on the shared bath's wall
line, with the front door centred on the narrower foyer; the laundry closet in Bedroom 4's corner
with its pair of doors; Bedroom 4's door at the south end of the foyer wall; the second west
window of the primary bedroom (W14); Bedroom 3's front bay glazed to the floor; the kitchen
window of three sashes over the sink and the kitchen skylight's place over the sink; the two
foyer skylights on the east slope; the skylight over the primary bath's shower; the tall windows
(Bedroom 2 rear, primary bath, Bedroom 3 bath); the kitchen's south wall, the sink and the dining
table at the island's west end; the shared bath's vanity; the sealed fireplace with the sofa
east and the television west; white gridded windows; all finishes and furniture styles. Where a
decision's numbers had been derived with the old walls, its meaning was kept (which wall it
aligns with, which room it is cut from, its clear size) and its coordinates were computed again
in the sheet's frame.

### Decided in this round, for the owner to see

- **Bedroom 3's west window W10 is removed.** The sheet has a solid wall behind the bed and the
  window was never decided. One constant brings it back: `BED3_WEST_WINDOW` in
  `bl/revision_spec.py` (README, "Architect's plan and the owner's changes").
- **The entry front is taller.** The entry roof is a raised gable with a level ridge at 12.60 ft,
  1.45 ft higher at the front than the published model's, and the tallest of the three front
  gables (the wing's is 11.82, the garage's 12.375). See the departures.
- **The living room's sliding door** stands with one centre panel 2'-3" open, which is the way
  onto the landing and to the sweep `OD`; the sheet draws both centre panels part open. The
  primary bedroom's sliding door is shown closed.
- **The furnace and storage closets** are shown closed and empty.
- **No stools at the island**, as in every round since the third; the worktop overhangs 12 in on
  the living-room side if the owner wants them.
- **Not changed although the sheet differs:** Bedroom 3's bed stays where it was (the sheet
  centres it on the west wall).

### Departures from the brief and from the sheet

- **Foyer and porch 5'-9", Bedrooms 3 and 4 14'-11" wide.** The brief carried the old model's
  5'-9 1/4" and 14'-10 3/8". The owner's decision is the alignment with the shared bath's east
  wall; with the sheet's 5 in walls that wall stands at x 15.142..15.558, which gives 5'-9" and
  14'-11". Keeping the old numbers would have put a 1/4 in jog into the wall line. The closets
  between the two rooms stay 6'-3".
- **Sidelights narrowed to the foyer.** The sheet's front door unit is 5'-5 1/2" wide in a 7'-0"
  foyer. In the 5'-9" foyer the unit takes the foyer less 3 in of wall on each side (5'-3") and
  keeps the sheet's members, so each sidelight is 10 1/2 in between its frames where the sheet
  has 11 3/4 in. The 3'-0" door is the sheet's.
- **The entry roof's height comes from SKA001's roof plan.** No sheet of the set has an elevation
  or a section of the addition. SKA001 draws the entry ridge ending on the main roof's south
  plane at z 19.14, which at 5 in 12 puts it at 12.602 ft (`roof.ENTRY_TIP_Z`, `ENTRY_Y`); the
  valley the sheet draws beside it agrees. The ridge is level, as the spec asks.
- **Ridges centred on what is built.** The sheet centres the wing's ridge on the wing and the
  entry's on the foyer. With the owner's foyer-side wall the wing is 1'-3" wider and the foyer
  1'-3" narrower, so the ridges stand at x 7.683 and 18.433, not at the sheet's 7.059 and 17.808.
- **Hall ledge 6 in deep.** The brief allowed "up to 10 in" on the hall's one free wall; with 10 in
  the way past the shared bath wall's corner would be under 2'-10". Nothing on a hall wall is
  deeper than 6 in.
- **Doors.** The house's own 3/4 in jamb liners, not the sheet's 2 in frames: the clear openings
  are the sheet's, the cuts in the walls 3/8 in wider on each side. Hinged leaves are 1/4 in
  narrower than their opening on each side (1/8 in for the two closed closet doors and for the
  garage's and the front door). Sliding glass panels are 3'-1 5/16" where the sheet's schematic
  says 3'-2", and the fixed panels stand on the room-side track, as drawn. Bedroom 4's entry
  keeps its opening, 1/16 in under 2'-8".
- **Kitchen.** The tall wall's fronts stand one door thickness in front of the 2'-0" line. The
  east counter starts on the south jamb of W07 (z 21.072; the sheet: 21.058). The dining table
  stays 2'-9" wide beside the 4'-0" island: a wider one would not leave 3 ft past the north
  chairs.
- **Bedroom 3.** The closet's doorway is at the sheet's x, not centred in the owner's 6'-3"
  closet. The toilet is the wall-hung one the bath had. The vault is lower than it was (11.108 at
  the ridge, 11.50 before): the 5 in 12 roof leaves no room for the old one.
- **Roof and eaves.** The eave's soffit is the roof slab's sloping underside, not a level boxed
  one, which would cross the heads of the windows that run to the ceiling. No gutters. The entry
  vault keeps its old mean height under the higher roof, level now.
- **Levels the set does not give.** The step at the house / garage door is half way (two risers
  of 5 1/2 in). The porch slab is half way between the walk and the floor (`PORCH_TOP`); A1.3's
  −0.336 is the existing porch. The front ground is level from the garage to the sidewalk, so
  the driveway has no fall. The stucco ends on a level line 5 in below the floor, above 6 to 9 in
  of foundation concrete.
- **`relayout.py`'s maps were not retired** for Bedroom 2's alcove and the concept roof: the shell
  still builds both and a revision replaces them after the warp.
- **Within 1/2 in but not on the line:** W13 (0.24 in), the primary bath's door D08 (0.26 in),
  both from the sixth round; W11 (0.09 in).

### Data and the tour

- **A door's width is its clear opening.** Until the seventh round the schedule gave the cut in
  the wall, 3/4 in more than the door, which the audit read as an error. The cut is kept as
  `wall_start` / `wall_end`. So the laundry doors read 2'-5 1/4" (the owner's 2'-6" is their
  wall opening), the vehicle door 14'-10" (15'-0") and the garage's side door 2'-4" (2'-8"); each
  text states both. Windows and the two sliding glass doors keep the unit's wall opening.
- **The furnace and storage closets are `spaces`, not rooms.** As rooms of the schedule they
  would become rooms of the tour, and a room nobody stands in takes over the sweep in front of
  it: the hall stop would read "Storage closet". `spaces` also holds the hall's two legs, the
  garage's floor and step, the porch and the landings; `overall` the outside sizes and levels.
- **The scene follows the build index by index:** existing wall boxes reshaped in place, new ones
  appended, and 339 objects the build no longer has marked `removed` in a group of that name,
  because an index may not shift. The data was compared with the built model box by box.
- **The plan** prints 39′11″ overall, 54′4″ on the west side and 53′0″ on the east, and shows
  the closets, the hall's widths, the steps and the landings.
- **Texts.** The change list `owner_changes_8`; earlier rounds' entries reworded where this one
  overtakes them; the Design views `front`, `roof`, `B3`, `B4`, `K0`, `A1`.

### Sweeps, cameras, renders

- **53 sweeps, 70 links.** Placed on the integrated build with `--keep --keep-clear 1.2`: 26
  unchanged, 25 moved, H5 new where the hall's two legs meet, C3 removed (Bedroom 3's closet is a
  reach-in closet that B3 looks into). Of the moved, 13 are seeds that went 0.06 to 0.29 ft with
  the 5 in walls, seven were set by hand (`PLACED`; "Sweep placement" above), H3 and A3 follow
  their seeds, L9 was nudged, LC follows the closet, OD stands at the sliding door's open way.
  Placed once more on the final build, all 52 stay; D2 is new, in front of the living / dining
  east window, where the olive tree stood (the floor there is 4.0 to 4.5 ft from K2 and L3,
  the nearest stops, which are 6.9 ft apart); OP's eye follows the porch slab; OD's label is "Rear landing" (its id and its room key
  `deck` stay, as published).
- **Different eye heights.** The garage sweeps stand on the garage floor (eye y 4.169), OD on
  the landing (5.002), OP on the porch slab (4.627); `tour.json`'s `eye` stays 5.0853, the house's.
- **Clearance**, measured in 72 directions at 49 heights round each stop on the final build: at least
  1.07 ft everywhere, and 1.2 ft except at A1 (the lever of the shared bath's open door) and P4
  (beside the primary bed). Before, H0, A3, L0 and L9 had under 1.0 ft.
- **Opening views** (`OPENING`): A3 at the shower end of the rebuilt bath (−60° / −8°); H3 (105°),
  H5 (90°), H0 (88°), H4 (75°) and T2 (5°) in the hall; K2 down the east aisle (175° / −6°); Y0
  (−120°) and Z0 (−92°) into the two bedrooms; D2 at the island, the cooktop wall and the dining
  table (−125° / −4°; its automatic view had the olive tree, 2 ft away, across the right 40 %).
  All 53 opening views were looked at again on 1024 px panoramas of the final build.
- **Hero cameras:** `K0` stands 1.7 ft further back in the hall, so that the table, which moved
  west, and its six chairs are whole in the frame; `A1` 0.6 ft west in its doorway, clear of the
  new door leaf, with a fixed exposure; `back` is centred on the four-panel door and its landing.
  After the olive tree moved to the pier it stood cut at the left edge of `K0`: the camera went
  3 in south and turned 2° left, which brings the whole tree and the lamp beside it into the
  picture (from further north the hall's wall end hides the tree's crown; turned right far
  enough to lose the tree, the frame cuts the chairs' legs). `living` is turned 4° left and
  narrowed to 84°: from the dining strip the tree's crown stands in front of the canvas's south
  end, so the frame ends before it. The other eight were rendered and left as they are;
  `primary` holds both west windows.
- **To be rendered again: everything.** Every room changed or sees a changed opening, the eaves
  or the ground: all panoramas with pins from a fresh probe, the hero stills, the bake, the
  exterior frames (README, "Render everything again").

### Process notes

- **The sheet is the frame.** Once the model's coordinates were the sheet's, a number read off
  the drawing could be written into the code as it stands and checked on the built model as it
  stands. Before, every comparison needed a map and an allowance for wall thickness.
- **No absolute numbers.** A position is written from the wall face of its own room
  (`_LIV[1] - KITCHEN_SKY_EAST`, the kitchen skylight's east edge from the east wall), so it
  keeps its meaning when a wall line moves, as every one did in stage A. Which face matters:
  written from its centre, the skylight left the sink when it became narrower.
- **Measure the built model, with a script that does not read the code.** The integration's
  table is rays on dumped meshes against the sheet's numbers; what a constant says is not
  evidence.
- **The data reads the model's numbers by their names**, also from modules it cannot import
  (`blender_spec()`), instead of keeping copies. One copy had gone stale unnoticed.
- **Parallel tracks meet at walls, floors and corners.** Each track measured its own pieces; the
  joints (coplanar faces of two tracks, a strip of one finish in the other's room, levels at a
  threshold) were found only by scans and renders of the combined build.
- **A width needs its definition.** "2'-8" door" was a wall cut in the data and a clear opening
  on the sheet. The schedule now says which, and keeps both.

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
| `lighting.py` | core (exterior zone may tune the sun/sky constants) | Sky and sun, the sky check (`check_sky()`), window portals, `can()`, `point_light()`, `emitter()` |
| `materials.py` | materials | `get(key)` library. KEYS are a stable contract. |
| `assets.py` | core | CC0 Poly Haven fetch and cache: `model()`, `texture()`, `hdri()`, `write_manifest()` |
| `zones/<zone>.py` | one zone agent each | `build(ctx) -> dict` that adds everything inside its zone (the primary suite, the primary bath and Bedroom 3's bath: after the warp, see "Which plan") |
| `warp.py` | core | Carries the built house from the concept plan onto the architect's plan |
| `relayout.py` (in `tools/render/`) | core | The sheet's frame (`WALL`, the named wall faces, `ROOMS`) and the map from the concept plan onto it |
| `revision_spec.py`, `garage_spec.py` | core | The numbers of everything built after the warp. Pure Python; every position written from a wall face of `relayout.py` |
| `revisions.py`, `laundry.py`, `zones/primary_suite_rooms.py`, `zones/hall_block.py`, `zones/bedrooms_rooms.py`, `garage.py`, `roof.py` | core | The owner's changes and the sheet's layout, built after the warp: `apply()` and the modules its steps call (the laundry closet's contents; the primary suite's walls and doors; Bedroom 2's closet block and the hall; Bedroom 3's and 4's doors, windows and Bedroom 3's closet; the garage and the front door; the roof) |

Rules:

- **Units.** All `Ctx` helpers take SCENE feet: x runs west→east, y is up, z runs north/garden
  (0) → south/street (~54). `rot` is radians about +Y. Since the eighth round these are the
  coordinates of sheet SKA002 (x = (X − 1107.075) / 18, z = (Y − 361.808) / 18 in PDF points),
  with the west and the rear wall's interior faces at 0.225. The house floor is y=0 and flat
  ceilings are at y=8.0; the garage floor is 11 in lower. A camera sits 5.0853 ft above the
  level it stands on.
- **Which plan.** Most zone modules are written on the **concept plan** (`data/concept/`); `bl/warp.py`
  carries what they build onto the architect's plan. Code that runs after the warp (`bl/revisions.py`
  and the modules it calls, `bl/laundry.py`, `bedrooms.bed4_closet_faces`) works in new-plan feet,
  which are the sheet's. A zone that needs a new-plan
  number converts it back with the inverse of the `relayout` map (see `_rect_centre` in
  `kitchen_dining_dining.py`, `_b4_desk_x` in `bedrooms.py` and `_px` / `_pz` in
  `kitchen_dining_kitchen.py`).
  Since the sixth round whole rooms are built after the warp, in plan feet: the primary suite
  (`primary_suite.fit_out`, called by `revisions.suite_fit_out`) and the primary bath
  (`baths_primary.build_room`, called by `revisions.primary_bath_fit_out`); since the eighth
  also Bedroom 3's bath (`baths_suite3.build_room`) and closet (`revisions.bedroom3_fit_out`),
  Bedroom 2's closet and the hall's fittings (`hall_block.fit_out`), and, as architecture, the
  hall block, the garage's floor and doors and the roof. A zone's `build()` then only registers
  the zone before the warp, which is how the revision knows that it was asked for; without it
  the fit-out is skipped. When editing them:
  - a number in the code is a position on the sheet and in the built model: no map, no inverse;
  - walls, doors, windows and skylights come from the spec modules (`bl/revision_spec.py`:
    `SUITE_*`, `BATH_*`, `PRIMARY_BATH_*`, `BED3_*`, `BED2_*`, `LIVING_*` ...; `bl/garage_spec.py`);
    read them from there and move them there, never as a literal in the zone, and write a new
    one from a wall face of `relayout.py`, never as an absolute number;
  - the warp does not see these pieces, so its name rules (fitted or loose) do not apply; the
    bake's name rules do, and the primary bath marks its wall finishes with `tg_class = 'wall'`;
  - order matters, and `revisions.apply()` is the list: the roof before the skylights, which cut
    their wells through it; `bath_door`, `bath_window`, `primary_bath_skylight`, then
    `suite_rooms`, `suite_fit_out`, `primary_bath_fit_out`; `hall_block` after `suite_rooms`;
    the bedrooms' steps after `laundry_closet`; everything before the repairs that run last
    (`floor_level`, `floor_gaps`, `living_east_baseboard`, `skirting_trim`, `skirting_joints`)
    and `white_windows`;
  - keep `primary_suite.fit_out`'s audit empty, and check positions on the built model.

  Since the seventh round the living zone is in plan feet too, a third way: `living.build()`
  runs with the other zones before the warp, and every object hangs under the root Empty
  `TG living root` at the SCENE origin. The warp skips objects named `TG ...` and objects with a
  parent, so a new piece must get that parent (the end of `build()` does it for the collection).
  In the kitchen, a zone in concept feet, the refrigerator and since the eighth round the island
  are dimensioned on the plan (`kitchen_dining_cabs.PlanFace`), and the counters' depths and the
  aisles are stated there (`PLAN_*`). The exterior zone has always been written on the plan and
  is not warped; since the eighth round `exterior_layout.py` is written from the house's outer
  faces and holds the ground levels.
- **Windows.** A window's pane and frame members go into the `openings` collection, the frame in
  `black_aluminum`: `revisions.white_windows` finds them there, makes them white and builds the
  grid bars. No zone builds window bars of its own (the garage door's lites are the door's), and
  whatever hangs at a window (shade, curtain) stays at least 0.04 ft on the room side of the
  glass: the bars stand 0.03 ft proud of it.
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
- **Camera clearance.** Every sweep needs at least 1.2 ft of clear space around it. The 19 seed stops
  keep their place (all but C0, which the placement moves to the middle of the walk-in closet's
  aisle, and those `PLACED` sets by hand), so no furniture may swallow one; the other sweeps are placed after the build
  (`place_sweeps.py`), so moving furniture means placing them again (`--keep`) and rendering again
  whatever sees the change.
- **Names matter to the bake.** `bake_web.py` classes objects by collection, `scene_index` and name
  (README, "Web model contract"). A new wall is a copy of an existing wall object. The roof's
  pieces are named `v7 roof ...` and live in `exterior_shell`.

## Zones

Every zone builds everything inside its regions, using the original scene objects (via
`ctx.find(room=..., role=...)`) as anchors for position and footprint. Original
furniture, decor, fixtures and landscape are **not** imported by the shell; the zone decides
what replaces them.

| Zone module | Regions (`scene_classification` rooms) | Sweeps to review |
|---|---|---|
| `kitchen_dining` | kitchen, dining | K0, K1, K2, K3, K4, D0, D1, D2 (also seen from H2, H4, L2) |
| `living` | living | L0, L1, L2, L3, L4, L6, L7, L8, L9 (also seen from D0, D1) |
| `primary_suite` | primary, primary_dressing (the vestibule and the walk-in closet) | P0, P2, P3, P4, P5, S0, S1, C0 |
| `bedrooms` | bed2, bed2_closet, bed3, bed3_bay, bed4, bed4_closet, suite3_wic (Bedroom 3's reach-in closet) | B2, X0, B3, Y0, Y1, Y2, Y3, B4, Z0 |
| `baths` | ensuite, shared_bath, suite3_bath | A0 (also seen from S1), A1, A3 |
| `hall_entry_garage` | front_hall, common_hall, garage, porch (inside face of the entry) | E0, H1, GA, LC, H0, H2, H3, H4, H5, T2, G0, G1, G2, G3 |
| `exterior` | everything outside the walls: grounds, garden, the two rear landings, fences, driveway, trees, garage door (both faces), exterior lights, distant context | OP, OD, and every sweep's window views |

Boundaries: living owns the living region north of z=14.5 on the concept plan (z 14.34 as built);
`kitchen_dining` owns the open area from there southward. Halls own circulation only and leave the
room zones alone. The laundry closet
is not a zone's: `bl/revisions.py` and `bl/laundry.py` build it after the warp (collection
`heg_laundry` under `zone_hall_entry_garage`), and `LC` is the sweep to review it from. The primary
suite's walls and doors and the primary bath's door, window and skylight are revisions too; the two
zones furnish what the revisions leave. The same holds since the eighth round for Bedroom 2's
closet block and the hall beside it (`hall_block.py`: the zones `bedrooms` and
`hall_entry_garage` furnish the closet and the hall through its `fit_out`), for Bedroom 3's bath
and closet, for the garage's floor, step, doors and water heater and the front door unit
(`bl/garage.py`; the zone hangs the garage's fittings above `garage_spec.FLOOR_Y`), and for the
roof with the porch's piers, beam and soffit (`bl/roof.py`; the exterior zone builds the slab
and the piers' lower part).
