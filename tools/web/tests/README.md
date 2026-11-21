# Browser tests of the tour page

Headless Chrome drives the real page (`index.html` + `assets/js/tour/`) the way a visitor does: real
mouse clicks, touch taps, drags, pinches and keys. The tests hold the page to its contract
(`window.TOUR`, `data-testid`, the requirements of the design: at rest the frame is the panorama, a
hop takes at most 1.2 s, every sweep can be reached by ring clicks, no console errors, works on a
390 x 844 touch screen).

Runner: `node --test` (built into Node, no test framework). One dependency: `puppeteer-core`
(it drives the Chrome that is already installed; nothing is downloaded).

## Run

```
cd tools/web/tests
npm install                     # once per checkout: puppeteer-core only
npm test                        # everything, one file at a time (about 10 minutes)
npm run test:quick              # tools + data + smoke + rest (30 s)
npm run test:igpu               # everything on the integrated GPU (see "GPU" below)

node --test smoke.test.js                                  # one file
node --test --test-name-pattern="ring" nav.test.js         # tests whose name matches
```

Needs Node 18.19 or newer, Google Chrome (`/usr/bin/google-chrome`) and `python3` (only to serve the
files). The page is taken from `http://127.0.0.1:8765/` (`npm run serve` starts that server). If
nothing answers there and `TOUR_BASE` is not set, each test file serves the repository root itself on
a free port for its run. The exit code is 0 only when every test passed.

| Variable | Default | Meaning |
|---|---|---|
| `TOUR_BASE` | `http://127.0.0.1:8765/` | where the page is served (a deployed copy works too; the files on disk are still checked by `data.test.js`). `auto` = always serve the repository root on a free port for the run |
| `TOUR_CHROME_ARGS` | `--use-angle=vulkan --enable-gpu --ignore-gpu-blocklist --enable-features=Vulkan` | Chrome's GPU flags, see below |
| `TOUR_CHROME` | `/usr/bin/google-chrome` | the Chrome binary (`CHROME_PATH` is honoured too) |
| `TOUR_QUERY` | (empty) | URL parameters added to every page load, e.g. `pano=2k` |
| `TOUR_OUT` | `tools/web/tests/out` | where screenshots and failure reports go (git-ignored) |

### GPU

WebGL 2 in headless Chrome needs the right ANGLE backend. Measured on the render machine (RTX 5090 +
Intel integrated graphics, no display):

| `TOUR_CHROME_ARGS` | Renderer | Use |
|---|---|---|
| `--use-angle=vulkan --enable-gpu --ignore-gpu-blocklist --enable-features=Vulkan` | the discrete GPU, 60 fps | the default |
| `--use-angle=gl-egl` | Intel integrated graphics, about 58 fps | while a render owns the big GPU; also a fair stand-in for a laptop |
| none, or `--use-angle=swiftshader` | software, about 1 fps | works, but the time limits are skipped (the harness sees "SwiftShader" in the renderer name) |
| `--use-angle=gl`, `--enable-gpu` alone | no WebGL at all | the page shows its fallback; every 3D test fails |

Before the tour is loaded the harness opens a throwaway page that creates a WebGL 2 context. Without
it the first launch after an idle pause can lose the tour's context.

## What is tested

| File | Tests | What it holds the page to |
|---|---|---|
| `lib.test.js` | 6 | No browser. The test tools themselves: PNG codec, the panorama reference on a synthetic file (yaw, pitch, wrap column, cropping), masks. |
| `data.test.js` | 31 | No browser. `tour.json`: fields of the contract, unique two-character sweep ids, links symmetric, `visible` contains `links` and is symmetric, the graph is connected from the start, links 1.5-14 ft, indoor sweeps inside the footprint, every room has a sweep. The footprint has at most 16 rectangles (the engine's limit), none overlapping, and a canted wall (the Bedroom 3 bay) is cut in steps of a third of a foot at most. The highlight reel starts at the entrance and names each place once. Panorama manifest: every sweep has an entry and a level; every file exists with the declared width, 2:1; the server hands each one out. Measurements and plan SVG agree; design views resolve; exterior frames exist; `index.html` is a slim shell stamped with `tour.json`'s version. `tour.json` `files`: the hashes the page puts on the model and the plan as `?v=` match the files on disk (skipped with a note while the published file predates them). **Rooms inside rooms**: a sweep belongs to the smallest room that contains it, and a room nobody stands in owns the sweep it names, which stands within 8 ft of it; a plan target that lies inside a larger one is drawn on top of it. **Laundry closet** (held to the rule, not to coordinates): room M13 is between 2'-6" and about 3.2 ft each way and has the doors D17 (2'-6" x 6'-8") in the wall of one of its sides; it lies inside Bedroom 4's rectangle, in its north-east corner, with the doors in its east side and the foyer beyond them; the sweep LC stands in the foyer, 2 to 6 ft in front of the opening and within its width, looks at it (15 degrees at most off, level or down to 25 degrees), belongs to the closet and is in the reel; the Design view LC names LC and M13 and places the closet at Bedroom 4 and the foyer, no view mentions it together with the kitchen, and the latest owner's round about it puts it at Bedroom 4 and moves the dining table to the island. **Primary suite, sixth round** (sizes held to the architect's sheet within a tenth of a foot, places to the rule): room M05 is named "Walk-in closet", about 6'-1" x 8'-0", with the pocket door D18 as the only door, in its east side, and no window; a sweep stands in it, is named after it, and its links leave the room only through D18's opening, to the vestibule; room M14 "Primary vestibule" is about 4'-7" x 8'-0", east of the closet with a wall of 4 to 7 inches between them, as wide with it as the bedroom, the bedroom to the north (an open connection over its full width, no door), the bathroom door at its south end, the sliding suite entry in its east side with the hall beyond, and links from it lead to all four neighbours; the reel has one card each for the primary bedroom, the walk-in closet and the primary bathroom, and no sweep, room or door is still named after the dressing area; W11 runs from a 3'-0" sill to a 7'-6" head at its old width, W13 is three feet wide from the 2'-0" sill to the ceiling, the bath's skylight is over its north-west quarter, W14 is still the southern of two west windows of the primary bedroom; the Design view of the primary bathroom puts the stone on the vanity wall and the shower in the north-west corner without a word of the superseded finishes, and the sixth round of the owner's changes is listed. |
| `smoke.test.js` | 10 | Loads, engine ready, `window.TOUR` complete, no console error or warning, no failed request, nothing loaded from another origin; the three landing buttons; a landing button pressed while the model loads; `data-testid`s; `?sweep=ID`; **the address bar follows the visitor** (`?sweep=ID&yaw=&pitch=` at rest inside, `?mode=` in the other views, `&view=` for an exterior preset, other parameters kept) without adding history entries, and its link opens the same view; no request for the old `adapt.json` / `collision.json`; without WebGL 2 the static fallback with the design stills. |
| `loading.test.js` | 9 | A slow line, made with request interception (each test states what it holds back). **A landing button pressed before the page has wired itself** (tour.json 1.5 s late) opens the view it names, not the exterior. **The inside view opens on its panorama while the model still downloads** (model 5 s late: first panorama well under 3 s after the click, no rings, a note about the model, a step is a dissolve, the dollhouse waits with a message and opens when the model is in, then rings and glides); a `?sweep=` link does the same. While the model downloads nothing is fetched for the closed Design sheet, the closed reel or the exterior, and behind the landing page the exterior loads one half-size frame. **With panorama files 2.5 to 3.2 s late no frame shows the bare baked model** (the engine's test hook paints it magenta): a flight over four hops, a far jump (the old panorama stays, a loading mark shows, then a dissolve), a fly-in from the dollhouse (the camera waits, then flies with the panorama projected). **A sharper level of a sweep the visitor has left** is aborted, not decoded, not uploaded; back on the sweep it comes after all. A WebGL context lost while the model downloads leaves the fallback page for good; the sheets' "Visit in 3D" says the view has stopped, and `TOUR.goTo` / `setMode` resolve false. |
| `rest.test.js` | 7 | **At rest the frame equals the published panorama: PSNR >= 40 dB** (and mean difference <= 1.5 / 255) on four sweeps with different looks, one of them straight at the wrap column of the file, and after a real hop. A control shows that a view 2 degrees off scores below 32 dB. The sharp level is on screen within 5 s; looking around makes no request. |
| `nav.test.js` | 19 | A click on a floor ring moves there; **every sweep is reached by ring clicks** (breadth first, one real click per sweep); rings are drawn at the visible sweeps; the cursor ring lies flat on the floor and upright on walls; a click beside a ring moves that way; ArrowUp steps, left / right turn; a drag looks (the picture follows the pointer, inertia) and never moves; wheel zoom has limits; the look direction survives a hop; `goTo` / `jumpTo`; interrupted moves and 24 random inputs still end at rest on a sweep. The Inside button pressed again during a move lets the move finish; a ring reached by Tab + Enter moves there and hands the focus to the view. **A double click is one move**: clicks 70 / 200 / 400 ms apart on a ring fly one hop, never back and never beyond, without zooming; toward a place a double click ends where a single click does. A reel card pressed during a move still arrives on the card's own view. A click while a cut still holds the picture of the view left behind is not taken. **Wheel units**: a notch reported in lines (Firefox) and a trackpad pinch (ctrl + wheel) zoom the inside view, the dollhouse and the exterior as a mouse notch does (a pinch to twice the size = twice the zoom). Key events without a `key` (autofill) raise no error. |
| `transition.test.js` | 6 | **A hop takes at most 1.2 s** from the click to rest (first link and the longest link of the tour); `getState().transition` is `{from, to, t}` with t rising from 0 to 1; no frame of a hop is black or blank, none jumps; a route over two links is flown without stopping. **Entering a view cuts straight to its picture**: no frame of the bare model on "Enter the house", back inside from the exterior, or into the exterior (the engine's test hook paints the bake magenta; every drawn frame is sampled). |
| `modes.test.js` | 15 | Toolbar buttons and `TOUR.setMode` between inside, dollhouse, floor plan and exterior; back inside on the same sweep; dollhouse on a dark background, drag orbits, wheel zooms; a click in the dollhouse flies into the sweep there; floor plan straight down, north up, room names, click on a name or the floor enters; the flight inside <-> dollhouse is continuous (no cut) and at most 4 s. The Inside button brings the visitor back to the sweep **and the direction** they left (from the exterior, the dollhouse and the floor plan); with the reel open the dollhouse and the floor plan frame the house above the strip and give the room back when it closes. With `prefers-reduced-motion` nothing flies: a move between sweeps is a fade (the camera is on a sweep in every frame), a change of view a cross-fade, the chrome does not slide. **A fly-in projects the sweep it lands on** whatever was projected last (walk on, look at the exterior, come back over the floor plan: the same sweep in every flight frame, no pop on landing). A flight cut short (Exterior pressed mid-flight, a sheet's "Visit in 3D") leaves no flight state: the floor plan shows its names and they can be clicked. **Inside <-> exterior is a dissolve** like every other change of view. **A click on a room nobody can stand in** (the laundry closet, cut out of Bedroom 4's rectangle; a reach-in closet), on the floor plan and in the dollhouse: the cursor marks the sweep in front of it, the click enters there and the visitor arrives looking at the room, at the sweep's own pitch (the click goes to a level surface inside the room that the page's own ray cast reports; the dollhouse is turned a quarter at a time until one is in view). **A click in a walled room enters that room**: on the floor plan the cursor marks a sweep of the room at the quarter points of every measured room that has a sweep, and at the point of such a room nearest to the dot of a sweep that stands in the room next door (the floor of the primary bathroom just inside its door, a foot from the vestibule's sweep); real clicks in the walk-in closet (M05), the vestibule (M14) and the primary bathroom, on the floor plan and in the dollhouse, land on a sweep of the room clicked. |
| `ui.test.js` | 22 | Dark round toolbar bottom left / right, active view white, small title top left; highlight reel (order, labels, thumbnails, a card goes to its sweep and is marked); room-name chip; Dimensions (plan targets, select a room and a door by real clicks, lists, millimetres, CSV download, Visit in 3D); Design tabs from `design.json`; menu, About sheet, screenshot download; keys ignored under a sheet. Keyboard: a sheet keeps the focus (everything behind it is inert, Escape returns the focus to the button that opened it), arrow keys walk the menu without moving the view, the reel takes the focus when opened by keyboard. A message raised from a sheet shows above it. **From 320 px to 2560 px wide nothing of the chrome overlaps or leaves the window** in any view, with the longest room name in the chip and the reel open or closed. No toolbar tip is drawn while the reel is open. A sheet opened from the menu, or from another sheet, gives the focus back to the button the visitor started from. **Every button, link and field has an accessible name** in every state (icons are hidden from assistive technology). The first-run hint ("Click a ring to move · drag to look") shows once on entering the inside view, clear of the rest of the chrome, goes with the first interaction or after a few seconds, and does not return in the session. On the floor plan no room name runs over its pill, at three window sizes and four zoom steps. **Dimensions, the closet inside Bedroom 4**: Bedroom 4, M13 and D17 are each selected by a real click on their own target, and "Visit in 3D" from D17 stands on LC looking at the doors. **Dimensions, the primary suite**: M05, M14 and D18 are each selected by a real click on their own target and highlighted alone, the detail gives 6′1″ x 8′0″ for the closet, 4′7″ for the vestibule and names the pocket door, and "Visit in 3D" from M05 stands inside the closet with its name in the chip. **Floor-plan names never cover one another** at three window widths while the plan is zoomed in on the smallest room that lies inside another one; that room's name shows, stands on its own room, and a click on it enters on the room's sweep (looking at the room when the sweep stands outside it). The same zoomed in on the vestibule of the primary suite (M14, 4'-7" wide between the walk-in closet and the hall): its name shows, on its own room and no wider than it, beside the closet's name on a desktop window, and a click on it enters on the vestibule's sweep. |
| `exterior.test.js` | 8 | The ported orbit: front frame at rest, the five side buttons, long drag settles on a frame, short drag is one frame, wheel zoom keeps the frame, arrow key, Hide / Show garden, "Enter the home". **On a frame the picture is the path-traced frame** (PSNR >= 30 dB against the middle of the frame file; measured 37-42 dB). Behind the landing page the exterior fetches one frame, at half size; the full one comes when the visitor chooses the view. **A view that stands still draws nothing**: behind the landing page, in the exterior, inside. |
| `mobile.test.js` | 10 | 390 x 844, device pixel ratio 2, touch only: landing fits; every control on screen, at least 36 px, not covered, not overlapping, in every view; tap a ring to move (<= 1.2 s); one finger looks; pinch zooms; reel; floor plan and Dimensions by touch. **At 390 x 844 and at 844 x 390** in every view, with the reel closed and open: title, chip, message, hint, toolbars, exterior panel, reel and menu never cover one another, and the menu opens above the exterior panel and above the reel; a message closes the menu and the menu takes a message down. The reel names each place once, the entrance first, no caption cut off. A double tap on a ring is one move and does not zoom. |
| `budget.test.js` | 5 | After resting on ten sweeps: textures alive <= 800 MB (desktop) / 420 MB (phone), at most one 8k and two 4k panoramas (phone: none and one), JavaScript heap <= 300 / 250 MB, no growth from stop to stop. Phone: an 8k level in the manifest is never requested. Desktop: an 8k level is used, exactly one such texture, and the frame equals that file. **Walking on about once a second** (nine sweeps, 0.9 s on each) asks for no 8k file and holds at most two 4k textures; stopping brings the 8k level, the only 8k file of the visit (needs published 8k levels; a note says so otherwise). |

Sweep, room, door and design-view ids are read from the page's data; only the ids the design names
(M13, D17, LC of the fifth round; M05, M14, D18, W11, W13, W14 of the sixth) are written in a test. Where
a test has to find a room by what it is, it goes by the rule ("a room no sweep stands in", "a room whose
rectangle lies inside another's", "a measured room": one with a `tag`) or by the room's name ("Bedroom 4",
"Foyer", "Primary bathroom"), never by coordinates; a size the architect's sheet gives (6'-1" x 8'-0",
4'-7", a 3'-0" sill) is held within a tenth of a foot.

### How "the frame equals the panorama" is measured

`lib/panoref.js` cuts the view a camera on the sweep must see out of the published file: the yaw,
pitch and field of view come from `TOUR.getState()`, the picture from `assets/panos/<level>/<ID>.webp`
(the level the state names), the lookup is bilinear, and nothing of the page's engine is involved.
Chrome is used only to decode the WebP (a second page on the same origin draws the needed rectangle
into a 2D canvas and hands it over as PNG); resampling, PSNR and the PNG codec are plain JavaScript in
Node. Two references are computed, interpolated on the stored values and in linear light (the two ways
a GPU samples a texture), and the better one counts. The floor rings and the cursor ring are drawn
over the panorama on purpose, so boxes around them (worked out from the sweep positions and the
camera) are left out; the report line gives the share left out and the PSNR of the whole frame too.

Typical values: 55-61 dB on a sweep, 21 dB for a view turned by 2 degrees, 15-19 dB for a camera
1.5 ft off the sweep (the old free-walk page).

Until the 8k panoramas are published `budget.test.js` makes a stand-in (the start sweep's 4k file enlarged to
8192 x 4096 by Chrome, offered through a rewritten manifest) to exercise the level rules; the walking test
needs real 8k levels and says so when there are none.

### Slow lines

`loading.test.js` (and two tests of `nav.test.js`) hold files back with puppeteer's request interception:
`hold(page, [[/pattern/, ms], ...])` delays every request whose URL matches (the first rule that matches
counts) and returns the log of what was asked for and when. That is latency per file, not a bandwidth
limit: it shows what the page does while a file is missing, not how long a real line takes.
The engine's test hook `engine.setDebug({bake: true})` paints the bare baked model magenta; the tests
count the frames in which it shows.

### Texture memory

`lib/gltrack.js` wraps the WebGL calls that size and delete textures before any page script runs and
keeps a table of the live ones. The numbers are computed from sizes and formats (mip chains count as
one third on top); what the driver really allocates is not visible to a page.

## Output

`out/<file>/` (git-ignored, emptied when the file runs again):

* `<test>--<name>.png`: screenshots and comparison sheets the tests save as evidence, e.g.
  `rest/...--rest-K0.png` (frame | file | difference x 8), `transition/...--hop-frames.png` (eight
  frames of a hop), `nav/...--cursor-floor.png`, `modes/...--fly-frames.png`.
* `<test>--FAILED.png` and `<test>--FAILED.txt` for a failing test: the page as it was, the error,
  `TOUR.getState()`, the console and the failed requests.

Each test also prints its measurements as diagnostics (`# ...` lines in the TAP output).

## Writing a test

```js
const { suite, assert } = require('./lib/harness');
const { test } = suite(__filename);                    // or suite(__filename, { preset: 'phone' })

test('the kitchen shows its panorama', async (s) => {
  await s.open();                                      // load, wait for window.TOUR and the engine
  await s.enter();                                     // the landing page's "Enter the house"
  await s.clickRing('H1');                             // real click on the floor ring of a sweep
  const st = await s.waitRest('H1');                   // TOUR.getState() once at rest there
  assert.equal(st.mode, 'inside');
});
```

A session `s` is one fresh page. The helpers (all in `lib/harness.js`, with comments there):
`open(query)`, `state()`, `waitFor(fn, {what, timeout}, ...args)`, `frames(n)`, `enter()`,
`inside(id)`, `waitRest(id)`, `waitSharp(id)`, `settle()`, `aimAt(id)`, `clickRing(id)`,
`press(selector)` (fails when the element is hidden, off screen or covered), `testid(name)`,
`clickAt(x, y)`, `moveTo`, `drag(a, b)`, `pinch`, `wheel`, `canvas()`, `thumb()`, `shot(name)`,
`savePng(name, image)`, `startRecorder()` / `stopRecorder()` (state and small frames on every
animation frame), `downloads()` / `waitFile()`, `tour()`, `manifest()`, `sweeps()`, `bestLevel(id)`,
`overlayBoxes()`, `note(text)`, `allow(/pattern/)`.

Rules the suite keeps:

* A test fails on any console error, uncaught exception, failed request or response >= 400, unless it
  says `s.allow(/pattern/)` for what it provokes. (Chrome's "GPU stall due to ReadPixels" warning,
  caused by reading the canvas, is ignored.)
* Wait on state (`waitFor`, `waitRest`, `settle`), not on fixed sleeps. `waitFor` reports the state
  it saw when it gives up.
* Enter through the landing button or `TOUR.setMode`; never remove `#landing` from the page (the rest
  of the page stays inert).
* Wait for `engine === 'ready'`. A page whose engine failed still answers, on the fallback.
* Time limits are skipped on a software renderer (`s.gl.software`).
* Ring positions come from `TOUR.project(id)` and are clicked with the real mouse or a touch tap.

## The page contract the tests use

`window.TOUR`: `getState()` -> `{engine, mode, sweep, transition: null | {from, to, t}, yaw, pitch
(radians), fov (degrees, vertical on a landscape screen), pano: {id, level}, sweeps}`, `goTo(id)`,
`jumpTo(id)`, `setLook(yaw, pitch)`, `setMode(mode)`, `sweeps()`, `project(id)`, `screenshot()`;
`data-testid`: `btn-rooms btn-dollhouse btn-floorplan btn-inside btn-exterior btn-dimensions
btn-design landing-enter landing-exterior landing-plan`.

Beyond the design's list, taken from the page as built: `btn-menu`, `menu-help`, `menu-screenshot`,
`exterior-enter`, `reel-<sweep>`, `plan-label-<room>`, `marker-<sweep>` (the focusable button behind
each floor ring); `#hint` (the first-run hint, class `show` while it is up); the address bar
(`?sweep=&yaw=&pitch=`, `?mode=&view=`); `getState().draws` (frames drawn); `getState().transition.fade`
(a move without motion); `TOUR.viewer` for `project([x, y, z])`, `view.fovY`, `view.eye`, `sweeps`,
`on('frame', fn)`, `pick(x, y, {classes})` (the surface point under a screen point of the dollhouse or the floor
plan: `{point, normal}`), `engine.hasPanorama(id)` and the engine's test hook `engine.setDebug({bake: true})`; the ids `#landing #planmodal #designmodal
#infomodal #reel #chip #menu #exteriorControls #exteriorGarden #modelAudit`, the `dimension*` and
`design*` ids, `[data-exterior]`, `[data-design]`, `[data-measure]`, `[data-dimension-tab]`; the
globals `MEASURE` and `DESIGN`; `getState().exterior` (`view`, `garden`, `photo: {frames, on, at,
weight, zoom, settling}`); `getState().dollhouse.hover` / `.floorplan.hover` (the sweep a click at the cursor would
enter) and `.flight`; the canvas is the first `<canvas>` (`#view`). If one of these is renamed,
the test that uses it fails with the selector in the message.

## Not covered

Real phones, Safari and Firefox (Chrome's emulation only); the Fullscreen button; printing; screen
readers themselves (names, roles and focus are checked, not what is spoken); frame rate (only the hop
time is limited); a real 8192 px render; the toolbar tips themselves (headless Chrome reports a device
without hover, where they are off).
