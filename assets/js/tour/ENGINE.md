# Engine API (`assets/js/tour/engine.js`)

Reference for the page modules in `assets/js/tour/`. Units are SCENE feet (x west to east, y up, z rear to street);
angles are radians in code. The file's header comment explains how the engine works; this is the call reference as
written when the engine was built (2026-11-19). The code wins where the two disagree.

```js
import { createEngine } from './engine.js';          // needs the import map entries 'three' and 'three/addons/'
const engine = createEngine(canvas, opts);
```
Units and conventions everywhere: **SCENE feet**, x west->east, y up, z north->south; yaw 0 looks toward -z, positive
clockwise seen from above; angles in **radians** (tour.json has degrees: convert); points are `[x, y, z]` arrays;
NDC is -1..1 with y up (`ndcX = px/w*2-1`, `ndcY = 1-py/h*2`); matrices are column-major 16-arrays.
The engine never fetches images and never runs a loop: the page loads, decodes, owns the clock and calls `render`.

### 1.1 Options (all optional)
| option | default | meaning |
|---|---|---|
| `context` | engine creates `webgl2` (`antialias`, `preserveDrawingBuffer` true unless `opts.antialias/preserveDrawingBuffer === false`) | an existing WebGL2 context |
| `sweeps` | none | same as `setSweeps(list)` |
| `footprint` | none | same as `setFootprint(rects)`; `tour.json.footprint` as it is |
| `interior` | bounding box of the footprint | `[x0,z0,x1,z1]` envelope inside which occluders count for the panorama depth test (legacy option, still honoured) |
| `depthSize` | 512 | depth cube face size. Use 1024 on desktop, 512 on phones |
| `depthPool` | 4 (min 3) | depth cubes kept (rest + move target + prepared ones) |
| `budget` | `{max8k:1, max4k:2, max2k:8, maxBytes:420 MB}` | panorama texture budget (merge-able: `{max8k:0, max4k:1, max2k:4}` for phones) |
| `cacheSize`, `maxFull` | sum of the caps / `max4k` | legacy names, still honoured |
| `mipmap8k` | false | mipmaps for 8K panoramas (179 MB instead of 134 MB each). Without them an 8K panorama shimmers a little when the FOV is zoomed far out |
| `pickCopies` | 2 | CPU copies of depth cubes kept for `pick` (24 MB each at 1024, 6 MB at 512) |
| `clipY` | 8.01 | height (ft) where the dollhouse cuts the walls |
| `capColor` | `0xa9a8a4` | colour of the cut wall tops |
| `prepass` | true | depth pre-pass during a move (halves the frame time, identical pixels) |
| `warm` | true | `load()` resolves only after programs, atlases and vertex buffers are on the GPU (in small tasks) |

`engine.caps` = `{maxTextureSize, maxAnisotropy, renderer}`: gate 8K on `caps.maxTextureSize >= 8192` (and device
memory). `setPanorama` refuses (returns false) an image larger than `maxTextureSize`.

### 1.2 Model, modes
* `load(url, onProgress) -> Promise<number of meshes>`. With `warm` (default) the first frame that draws the model
  costs ~25 ms instead of 350-800 ms; `load` itself takes ~1.3 s instead of 0.3 s (the warm-up runs in ~40 small tasks,
  it draws into an 8 x 8 px corner of the canvas and sets `dirty()`). The pure panorama (rest state) works **before**
  the model has arrived (no pick / no ring occlusion until then).
* `setMode('inside' | 'dollhouse' | 'floorplan' | 'exterior')`:
  * `inside`: everything incl. ceilings and grounds, no roof / facade. Sweep projection on.
  * `dollhouse`, `floorplan`: ceilings, roof, facade, grounds and every node outside the footprint hidden; all
    fragments outside the footprint discarded; walls + glass cut at 8.01 ft and capped (a generated cap mesh fills the
    cut wall outlines, so the floor plan shows solid walls); near exterior walls culled per fragment (see 2.4).
    Furniture, art, uppers stay. Projection off (bake).
  * `exterior`: as before (roof, facade, no ceilings; legacy `setProjection`).
  * **`setMode` resets the two fly controls** to the mode's own state: inside = projection fade 1, ceilings opaque;
    dollhouse / floorplan = projection fade 0, ceilings gone.
  * `applyVisibility({mode, cut, furniture, garden})` still works (legacy names `walk`, `top`, `orbit`, `exterior`
    behave exactly as in house3d.js; the new names are accepted too). `engine.mode` reads the current mode.
* `setBackground(color)`: clear colour (any `THREE.Color` input: `0x16181d`, `'#16181d'`). Not changed by `setMode`.
* `setFootprint(rects)`: `[[x0,z0,x1,z1], ...]`, at most 16 rectangles, union = house outline (walls included).
* `setClassOpacity(cls, 0..1)`: fade a class. Made for `'ceiling'` (no shader recompile); in the dollhouse the ceilings
  are drawn only while this is > 0, and the wall cut slides from 16 ft down to 8.01 ft as it goes to 0. Holds until
  the next `setMode`.
* `setProjectionFade(0..1)`: strength of the sweep projection on the model (1 = panoramas, 0 = bake). In the dollhouse
  the backdrop (the panorama at infinity) additionally fades out by the time the camera is 5 ft from the sweep.
  Holds until the next `setMode`.
* `setAdaptation(k, ko)`: unchanged (bake exposure only; never touches panorama pixels).

### 1.3 Sweeps and panoramas
* `setSweeps(list)`: `[{id, p:[x, eyeY, z], offset?: radians}]` = `tour.json.sweeps` as they are (the manifest's
  `offset` must be added by the page if it is ever non-zero). Needed before `setPanorama(id, image, level)`.
* `setPanorama(id, image, level, {center?, offset?, frame?}?) -> boolean`
  * `image`: ImageBitmap (preferred) or HTMLImageElement, equirect 2:1, sRGB. The engine closes the bitmap once it is
    on the GPU.
  * `level`: `'2k' | '4k' | '8k'`, or a pixel width, or omitted (taken from `image.width`).
  * A lower level than the one held is ignored (returns false). A higher level for a panorama that is already on the
    GPU is an **upgrade**: the one on screen stays, the new one is uploaded in slices (about 8 MB of texels per
    frame; 8K = ~16 frames at 60 fps instead of a 350 ms freeze), then they swap and `dirty()` goes true.
  * Legacy form `setPanorama(id, image, center, offset, full, instant, frame)` unchanged (exterior frames).
* `hasPanorama(id)` -> `null` or `{level, full, depth, uploaded, pending, shown, width}`: `level/full/width` = best image
  taken (so a loader does not request it twice), `pending` = an upgrade is still uploading and `shown` is the level on
  screen, `uploaded` = on the GPU, `depth` = depth cube rendered. `hasPanorama(id, level) -> boolean` (at least `level`).
* `prepare(id, level?) -> Promise<boolean>`: everything a move to `id` needs, ahead of time and outside the animation:
  sliced texture upload (+ mipmaps), the depth cube, the CPU copy for `pick`. Resolves `false` when the panorama is not
  there (call `setPanorama` first), below `level`, or evicted meanwhile. ~90-120 ms of work for a 4K panorama + 1024
  cube on the iGPU, spread over several tasks / frames. Without `prepare` the same work happens inside the first
  `render` that needs it (one long frame).
* `setSweepBlend(idA, idB = null, t = 0)`: the deterministic projection. No easing, no fade-in, repeatable (the same
  call + camera gives the same bytes).
  * `setSweepBlend(id)` = rest. With the camera within 0.02 ft of the sweep and mode `inside` the frame is the **pure
    equirect panorama**: one draw call, the model is not drawn (`projectionInfo().pure === true`).
  * `setSweepBlend(a, b, t)`: `a` weighs `1-t`, `b` weighs `t`; the camera position is whatever the page renders with
    (normally `lerp(a.p, b.p, s)`). A surface only one of the two sees shows that one at full strength; a surface
    neither sees takes the panoramas without the depth test, switching from `a` to `b` around t = 0.35..0.65. Never the
    bake, never black. At `t = 1` with the camera on `b` the frame is already the pure panorama of `b`.
  * A missing panorama is simply left out (the other one at full weight), so the page may call
    `setSweepBlend(a, b, 0)` at click time, load `b`, `prepare(b)` and only then run `t`.
  * `setSweepBlend(null)` turns the sweep projection off. In mode `exterior` it is ignored (legacy projection).
  * `engine.resting` = id of the sweep the last frame rested on (pure panorama), else `null`.
* `setWanted(ids)`: ids evicted last (route ahead, hovered sweep). Shares the list with `setProjection`'s `wanted`.
* Eviction (LRU beyond the budget): never the two ids of `setSweepBlend` (whether loaded or not), a panorama being
  prepared, the one set last, or a legacy projection target. With everything protected the caps are exceeded for a
  while rather than a needed panorama dropped. **Call `setSweepBlend` with the ids of a move before loading them.**
* `setProjection(targets, wanted)`, `projectionInfo()`: unchanged (legacy, eased; the exterior orbit).
  `projectionInfo()` now also carries `{sweep, pure, fade}` and `level` per slot in sweep mode.

### 1.4 Rendering
* `render(view) -> true`
  ```js
  view = { eye:[x,y,z], aim:[x,y,z], up?:[x,y,z], fovY /* radians */, near?, far?, width?, height?, pixelRatio? }
       | { ortho:{ halfHeight /* ft */ }, eye, aim, up?, near?, far?, width?, height?, pixelRatio? }
  ```
  `up` defaults to +y, and to -z (north up) when looking straight down / up. `near/far` default to 0.08 / 400 inside
  and 0.5 / 1200 elsewhere (pass them explicitly while flying between inside and the dollhouse). `width/height` are
  drawing-buffer pixels and default to `canvas.width/height`; the drawing buffer is only touched when the size changes.
  Legacy `render(eye, aim, fovY, width, height, pixelRatio)` unchanged.
* `pv()`: projection x view of the last render (perspective or orthographic), 16 numbers, column-major.
* `project([x,y,z]) -> {x, y, z, behind}` (NDC of the last render). `ray(ndcX, ndcY) -> {origin, direction}`.
* `dirty() -> boolean`: true when the next frame would differ although the page changed nothing: a panorama / the
  model / an upgrade arrived, a `setMode / setSweepBlend / setProjectionFade / setClassOpacity / setBackground /
  setAdaptation / setProjection` call changed something, `invalidate()` was called, or an easing (adaptation, legacy
  weights) is still running. Page loop: `if (viewChanged || engine.dirty()) engine.render(view)`.
* `invalidate()`: call after editing anything in `engine.overlay`.
* `stats()` (+ `mode`, `drawn` triangles, `memory`), `memory()` -> bytes `{panoramas, panoramaLevels, depthCubes,
  atlases, geometry, gpu, pickCopies}` (computed from sizes, not measured).

### 1.5 Picking
`pick(ndcX, ndcY, opts?) -> { point:[x,y,z], normal:[x,y,z], distance, cls, source } | null`
* `normal` is unit length and turned toward the viewer; `distance` in feet from the eye; `cls` is the `tg_class` of the
  surface (`base` = floors + built-ins, `wall`, `ceiling`, `furniture`, `decor_high`, `landscape` (seen through
  glass: glass never blocks a pick)); `source` is `'depth'` or `'ray'`.
* **Inside, resting on a sweep**: from that sweep's depth cube. About 1 microsecond: call it on every mouse move. The
  point is intersected with the local plane, so a reticle slides smoothly. `null` until the cube's CPU copy has
  arrived (`prepare()` waits for it; otherwise 1-3 frames after the first rest frame) and where there is only sky.
* **During a move**: `null`.
* **Dollhouse / floor plan**: ray cast (about 1 ms) against `opts.classes` (default `['base']`; `opts.walls: true` =
  `['base','wall']`), obeying the same cut / cull rules as the picture. Works with the orthographic camera.
* `opts.raycast: true` forces the ray cast in any state (e.g. with `classes: ['base','furniture']`).
* A floor is `cls === 'base' && normal[1] > 0.7`; a point seen through a window has `cls === 'landscape'`.

### 1.6 Overlay (rings, reticle)
* `engine.overlay`: a `THREE.Group` in feet. Add meshes, set `visible`, move them, then `engine.invalidate()`. Drawn
  after the scene with the normal depth test: against the model during a move and in the dollhouse, and **against the
  resting sweep's depth cube at rest** (the pure-panorama frame writes that depth, bilinearly filtered and pushed back
  0.05 ft + 1.2 %), so any material works and rings behind walls or furniture are hidden. Never in depth cubes or picks.
* `engine.ring(radiusInner, radiusOuter, segments = 72) -> BufferGeometry`: flat in the xz plane, normal +y, `uv.x` 0 at
  the inner edge .. 1 at the outer. `ring(0, r)` is a disc.
* `engine.overlayMaterial({color = 0xffffff, opacity = 1, soft = 0 | [inner, outer], depthTest = true})`: unlit
  `MeshBasicMaterial`, premultiplied alpha, no depth write, double-sided; `soft` feathers the alpha across `uv.x` by that
  fraction of the ring width (at least one pixel). `material.opacity` and `material.userData.soft.value` can be animated.
* Put floor rings at `floor + 0.06` ft; orient a reticle with
  `mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), new THREE.Vector3(...hit.normal))` and lift it 0.04 ft
  along the normal (see `tools/web/dev/harness.js`, demo part, for working code).
* Import three from the same specifier (`'three'`) as the engine so the classes are shared.

### 1.7 Recipes
```js
// boot
const engine = createEngine(canvas, { sweeps: tour.sweeps, footprint: tour.footprint, depthSize: lite ? 512 : 1024,
                                      budget: lite ? { max8k: 0, max4k: 1, max2k: 4 } : undefined });
engine.setBackground(0x16181d);
engine.setMode('inside'); engine.setSweepBlend(start);                 // shows the panorama as soon as it is set,
engine.setPanorama(start, await bitmap(start, '2k'), '2k');            // even before the model has loaded
await engine.load('assets/model/house.glb'); await engine.prepare(start);

// loop
if (viewChanged || engine.dirty()) engine.render({ eye, aim, fovY });

// move a -> b (0.6-1.1 s): declare, load, prepare, then run the clock
engine.setSweepBlend(a, b, 0);
if (!engine.hasPanorama(b)) engine.setPanorama(b, await bitmap(b, '2k'), '2k');
await engine.prepare(b);
each frame: engine.setSweepBlend(a, b, ease(t)); render({ eye: lerp(pa, pb, ease(t)), aim, fovY });
on arrival: engine.setSweepBlend(b);                                    // pure panorama again
then: engine.setPanorama(b, await bitmap(b, '8k'), '8k');               // upgrade in the background, no hitch

// inside -> dollhouse, one camera move (s = 0..1)
engine.setMode('dollhouse'); engine.setProjectionFade(1); engine.setClassOpacity('ceiling', 1);   // same picture as the rest frame
each frame: engine.setProjectionFade(1 - s*1.6); engine.setClassOpacity('ceiling', 1 - s*2.5);
            render({ eye: lerp(sweepEye, orbitEye, e), aim, fovY, near: 0.08 + 0.42*e, far: 1200 });
// dollhouse -> inside: the same backwards, then engine.setMode('inside') with the camera exactly on the sweep.

// floor plan
engine.setMode('floorplan');
render({ ortho: { halfHeight: 31 }, eye: [cx, 60, cz], aim: [cx, 0, cz], up: [0, 0, -1], near: 1, far: 200 });
labels: const n = engine.project([x, 8.1, z]);  click: engine.pick(ndcX, ndcY)  ->  nearest sweep to hit.point
```

---------------------------------------------------------------------------------------------------------------------
