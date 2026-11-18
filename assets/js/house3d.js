// Real-time renderer for the baked house model (three.js r170, vendored in assets/vendor/three).
//
// The GLB (tools/render/bake_web.py) carries Cycles-baked, display-referred colour in each
// texture, so everything renders UNLIT: the browser shows the same global illumination,
// soft shadows and materials as the path-traced panoramas, at real-time speed.
//
// Photoreal walk (setPanorama / setProjection): in walk mode the path-traced 360° panoramas
// themselves are projected onto the model from the camera stops they were rendered at, the way
// Matterport-style tours work. Standing on a stop shows that panorama pixel for pixel, lined up
// with the geometry; moving between stops blends the two nearest panoramas on the geometry, so
// walls, furniture and floors keep their path-traced look with correct parallax. Each panorama is
// tested against a depth cube rendered from its stop: surfaces that stop cannot see fall back to
// the other panorama, then to the bake.
//
// Coordinates: the GLB is in metres with SCENE axes (x east, y up, z south), so scaling the
// root by 1/0.3048 puts it in SCENE feet, the unit the rest of the app (camera, hotspots,
// minimap, collision, measurements) already uses. No other conversion is needed: three.js
// and the app share handedness, -Z-forward cameras and vertical FOV. The panoramas use the
// same frame (assets/panos/manifest.json: centre column = yaw `offset`, yaw 0 = -z).
//
// Visibility classes (node.extras.tg_class) reproduce the app's per-mode rules:
//   exterior   roof / facade             -> exterior mode only
//   ceiling    ceilings, ceiling lights  -> walk mode only
//   wall,glass walls/trim/windows/doors  -> clipped at 2.1 ft in cutaway (dollhouse / plan)
//   decor_high art, uppers, mirrors      -> hidden in cutaway, follows the furniture toggle
//   furniture  furniture + low decor     -> furniture toggle
//   landscape  grounds, deck, fences     -> garden toggle
//   base       floors, built-ins         -> always
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

const FT = 0.3048;
const CUT_Y = 2.1;                       // ft, same as the original cutaway
const CAP = new THREE.Color(0x3b403d);   // poché colour seen inside cut walls
const CLEAR = new THREE.Color(0.79, 0.88, 0.94);
const GLASS_OPACITY = 0.16;

// Eye adaptation (walk mode): per-channel gain k of the highlight-preserving curve
// f(x) = k x / (1 + (k - 1) x) on linear display colour, shared by every non-glass material.
// k = 1 is the bake as-is; tools/render/adapt_web.py measures each tour stop's k so the walk matches
// that stop's panorama exposure and white balance. It only affects the bake, never the panoramas.
const ADAPT_TAU = 0.35;                  // s, easing time constant
const ADAPT_SNAP = 0.5;                  // s without frames -> jump straight to the target

// Panorama projection.
const PANO_DEPTH_SIZE = 512;             // depth cube face size (texels); opts.depthSize overrides
const PANO_DEPTH_FAR = 160;              // ft; farther surfaces count as visible
const PANO_CACHE = 6;                    // panorama textures kept on the GPU; opts.cacheSize overrides
const PANO_MAX_FULL = 2;                 // of which full resolution (4K + mips = 45 MB); opts.maxFull
const PANO_DEPTH_POOL = 3;               // depth cubes (two slots + one spare), re-rendered on reuse
const PANO_FADE = 0.25;                  // s, fade-in once a panorama arrives
const PANO_TAU = 0.12;                   // s, easing of the blend weights between stops
const PANO_OCCLUSION = [0.03, 0.4];      // ft from a stop over which its occlusion test fades in
const BACKDROP_RADIUS = 300;             // ft, inside the walk camera's far plane

// Equirectangular lookup shared by the model and the backdrop. The derivatives come from whichever
// of u and u + 0.5 is continuous here, so the seam at the back of the panorama never drops to the
// smallest mip level.
const PANO_SAMPLE_GLSL = `
uniform float uTgOn;
uniform vec2 uTgW;
uniform vec2 uTgOffset;
uniform sampler2D uTgPanoA;
uniform sampler2D uTgPanoB;
varying vec3 vTgWorld;
vec3 tgPano( sampler2D t, vec3 d, float offset ) {
	float s = ( atan( d.x, - d.z ) - offset ) * 0.15915494309189535 + 0.5;
	vec2 uv = vec2( fract( s ), 0.5 - asin( clamp( d.y, - 1.0, 1.0 ) ) * 0.3183098861837907 );
	vec2 uv2 = vec2( fract( s + 0.5 ), uv.y );
	vec2 dx = dFdx( uv ), dy = dFdy( uv ), dx2 = dFdx( uv2 ), dy2 = dFdy( uv2 );
	if ( abs( dx2.x ) + abs( dy2.x ) < abs( dx.x ) + abs( dy.x ) ) { dx = dx2; dy = dy2; }
	return textureGrad( t, uv, dx, dy ).rgb;
}
`;

// Visibility of a surface point from a stop: compare its distance with the depth cube rendered
// there. The tolerance grows with distance and at grazing angles (one cube texel spans more depth).
// Five taps around the direction, keeping the most pessimistic, widen every occluder by about a
// texel: the antialiased edges of thin things (pendants, stems, chair legs) then never smear onto
// the surfaces behind them. Only occluders inside the house envelope count. Planting and fences
// outside are simplified in the model, so their depth would wrongly hide what the render shows
// between the leaves and slats.
const PANO_DEPTH_GLSL = `
uniform vec2 uTgOcc;
uniform vec3 uTgCenterA;
uniform vec3 uTgCenterB;
uniform samplerCube uTgDepthA;
uniform samplerCube uTgDepthB;
uniform float uTgFar;
uniform float uTgTexel;
uniform vec4 uTgBox;
float tgTap( samplerCube depth, vec3 c, vec3 d, float dist, float tol ) {
	float s = unpackRGBAToDepth( textureCube( depth, d ) ) * uTgFar;
	vec3 hit = c + d * s;
	bool inside = hit.x > uTgBox.x && hit.z > uTgBox.y && hit.x < uTgBox.z && hit.z < uTgBox.w;
	return inside ? 1.0 - smoothstep( tol, 2.0 * tol, dist - s ) : 1.0;
}
float tgSeen( samplerCube depth, vec3 c, vec3 d, float dist, float occ, vec3 n ) {
	if ( occ <= 0.0 ) return 1.0;
	float tol = ( 0.06 + 0.012 * dist ) / max( abs( dot( n, d ) ), 0.12 );
	vec3 t1 = normalize( cross( d, abs( d.y ) < 0.9 ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 ) ) );
	vec3 t2 = cross( d, t1 );
	float e = uTgTexel;
	float v = tgTap( depth, c, d, dist, tol );
	v = min( v, tgTap( depth, c, normalize( d + t1 * e ), dist, tol ) );
	v = min( v, tgTap( depth, c, normalize( d - t1 * e ), dist, tol ) );
	v = min( v, tgTap( depth, c, normalize( d + t2 * e ), dist, tol ) );
	v = min( v, tgTap( depth, c, normalize( d - t2 * e ), dist, tol ) );
	return mix( 1.0, v, occ );
}
`;

const PANO_FRAGMENT = `
	if ( uTgOn > 0.5 ) {
		vec3 tgN = normalize( cross( dFdx( vTgWorld ), dFdy( vTgWorld ) ) );
		vec3 tgSum = vec3( 0.0 );
		float tgSeenW = 0.0;
		if ( uTgW.x > 0.0 ) {
			vec3 r = vTgWorld - uTgCenterA;
			float dist = max( length( r ), 1e-4 );
			float w = uTgW.x * tgSeen( uTgDepthA, uTgCenterA, r / dist, dist, uTgOcc.x, tgN );
			tgSum += w * tgPano( uTgPanoA, r / dist, uTgOffset.x );
			tgSeenW += w;
		}
		if ( uTgW.y > 0.0 ) {
			vec3 r = vTgWorld - uTgCenterB;
			float dist = max( length( r ), 1e-4 );
			float w = uTgW.y * tgSeen( uTgDepthB, uTgCenterB, r / dist, dist, uTgOcc.y, tgN );
			tgSum += w * tgPano( uTgPanoB, r / dist, uTgOffset.y );
			tgSeenW += w;
		}
		float tgStrength = clamp( uTgW.x + uTgW.y, 0.0, 1.0 ) * smoothstep( 0.0, 0.35, tgSeenW );
		diffuseColor.rgb = mix( diffuseColor.rgb, tgSum / max( tgSeenW, 1e-5 ), tgStrength );
	}`;

function prepareMaterial(mat, cap, adapt, proj) {
  // cap: back faces of clipped walls show a solid section colour instead of the wall's inside.
  if (cap) mat.side = THREE.DoubleSide;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, proj);
    shader.uniforms.uAdapt = adapt;
    shader.vertexShader = 'varying vec3 vTgWorld;\n' + shader.vertexShader.replace('#include <project_vertex>',
      '#include <project_vertex>\n\tvTgWorld = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;');
    let head = '#include <packing>\nuniform vec3 uAdapt;\n' + PANO_SAMPLE_GLSL + PANO_DEPTH_GLSL;
    let body = '#include <map_fragment>\n\tdiffuseColor.rgb = uAdapt * diffuseColor.rgb / ( 1.0 + ( uAdapt - 1.0 ) * diffuseColor.rgb );' + PANO_FRAGMENT;
    if (cap) {
      shader.uniforms.capColor = { value: CAP };
      head += 'uniform vec3 capColor;\n';
      body += '\n\tif ( ! gl_FrontFacing ) diffuseColor.rgb = capColor;';
    }
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\n' + head)
      .replace('#include <map_fragment>', body);
  };
  mat.customProgramCacheKey = () => (cap ? 'tgcap2' : 'tgpano2');
  return mat;
}

export function createEngine(canvas, opts = {}) {
  const gl = opts.context || canvas.getContext('webgl2', {
    antialias: true, preserveDrawingBuffer: true, alpha: false, powerPreference: 'high-performance',
  });
  if (!gl) throw new Error('WebGL2 is not available');
  const renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: true, preserveDrawingBuffer: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.localClippingEnabled = true;
  renderer.autoClear = true;
  renderer.setClearColor(CLEAR, 1);

  const scene = new THREE.Scene();
  const root = new THREE.Group();
  root.scale.setScalar(1 / FT);           // metres -> SCENE feet
  scene.add(root);
  const camera = new THREE.PerspectiveCamera(45, 1, 0.08, 900);
  const cutPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), CUT_Y);
  const byClass = {};
  const wallMats = [];
  const glassMats = [];
  const maxAniso = renderer.capabilities.getMaxAnisotropy();
  let state = { mode: 'exterior', cut: true, furniture: true, garden: true };
  const adapt = { value: new THREE.Vector3(1, 1, 1) };
  const adaptTarget = new THREE.Vector3(1, 1, 1);
  let adaptClock = 0;
  let parts = 0;

  // Projection uniforms, shared by reference with every material (and the backdrop).
  const proj = {
    uTgOn: { value: 0 },
    uTgW: { value: new THREE.Vector2() },
    uTgOcc: { value: new THREE.Vector2() },
    uTgOffset: { value: new THREE.Vector2() },
    uTgCenterA: { value: new THREE.Vector3() },
    uTgCenterB: { value: new THREE.Vector3() },
    uTgPanoA: { value: null },
    uTgPanoB: { value: null },
    uTgDepthA: { value: null },
    uTgDepthB: { value: null },
    uTgFar: { value: PANO_DEPTH_FAR },
    uTgTexel: { value: 2.5 / PANO_DEPTH_SIZE },             // tap spacing: 2.5 texels at a face centre
    uTgBox: { value: new THREE.Vector4(-1e9, -1e9, 1e9, 1e9) },   // house envelope (x0, z0, x1, z1), ft
  };
  const depthSize = opts.depthSize || PANO_DEPTH_SIZE;
  const cacheSize = opts.cacheSize || PANO_CACHE;
  const maxFull = Number.isFinite(opts.maxFull) ? opts.maxFull : PANO_MAX_FULL;
  proj.uTgTexel.value = 2.5 / depthSize;
  // opts.interior = [x0, z0, x1, z1]: the house footprint in SCENE feet. The margin keeps window
  // frames and the wall thickness inside it.
  if (Array.isArray(opts.interior) && opts.interior.length === 4) {
    const [x0, z0, x1, z1] = opts.interior;
    proj.uTgBox.value.set(x0 - 0.3, z0 - 0.3, x1 + 0.3, z1 + 0.3);
  }
  const panos = new Map();                // id -> {tex, full, offset, center, cube, depthReady, born, used}
  const cubes = [];                       // depth cube pool: {rt, owner}
  const projWeights = new Map();          // id -> eased blend weight
  let projTargets = [];
  let projWanted = new Set();
  let projClock = 0;
  let projInfo = { on: false, slots: [] };
  let visKey = '';
  let cubeCam = null;
  const clearTmp = new THREE.Color();

  // Sky and anything without geometry (through windows, the skylight): the blended panoramas
  // looked up by view direction, i.e. at infinity.
  const backdrop = new THREE.Mesh(new THREE.SphereGeometry(BACKDROP_RADIUS, 48, 24), new THREE.ShaderMaterial({
    uniforms: Object.assign({ uTgSky: { value: CLEAR } }, proj),
    vertexShader: 'varying vec3 vTgWorld;\nvoid main() {\n\tvec4 w = modelMatrix * vec4( position, 1.0 );\n\tvTgWorld = w.xyz;\n\tgl_Position = projectionMatrix * viewMatrix * w;\n}',
    fragmentShader: PANO_SAMPLE_GLSL + `uniform vec3 uTgSky;
void main() {
	vec3 d = normalize( vTgWorld - cameraPosition );
	vec3 c = vec3( 0.0 );
	if ( uTgW.x > 0.0 ) c += uTgW.x * tgPano( uTgPanoA, d, uTgOffset.x );
	if ( uTgW.y > 0.0 ) c += uTgW.y * tgPano( uTgPanoB, d, uTgOffset.y );
	float a = uTgW.x + uTgW.y;
	gl_FragColor = vec4( mix( uTgSky, c / max( a, 1e-5 ), clamp( a, 0.0, 1.0 ) ), 1.0 );
	#include <colorspace_fragment>
}`,
    side: THREE.BackSide, depthTest: false, depthWrite: false,
  }));
  backdrop.frustumCulled = false;
  backdrop.renderOrder = -1e9;
  backdrop.visible = false;
  scene.add(backdrop);

  // Distance from a stop, packed into RGBA8 (renderable everywhere; sampled with nearest filtering).
  const depthMat = new THREE.ShaderMaterial({
    uniforms: { uCenter: { value: new THREE.Vector3() }, uFar: { value: PANO_DEPTH_FAR } },
    vertexShader: 'varying vec3 vW;\nvoid main() {\n\tvec4 w = modelMatrix * vec4( position, 1.0 );\n\tvW = w.xyz;\n\tgl_Position = projectionMatrix * viewMatrix * w;\n}',
    fragmentShader: '#include <packing>\nuniform vec3 uCenter;\nuniform float uFar;\nvarying vec3 vW;\nvoid main() {\n\tgl_FragColor = packDepthToRGBA( clamp( length( vW - uCenter ) / uFar, 0.0, 0.999 ) );\n}',
    side: THREE.DoubleSide,
  });

  const draco = new DRACOLoader();
  draco.setDecoderPath(new URL('../vendor/three/examples/jsm/libs/draco/gltf/', import.meta.url).href);
  const loader = new GLTFLoader();
  loader.setDRACOLoader(draco);

  function adopt(gltf) {
    const added = [];
    gltf.scene.traverse((o) => {
      if (!o.isMesh) return;
      const cls = (o.userData && o.userData.tg_class) || (o.parent && o.parent.userData && o.parent.userData.tg_class) || 'base';
      const old = o.material;
      let mat;
      if (cls === 'glass') {
        mat = new THREE.MeshBasicMaterial({ color: 0xd4e6e8, transparent: true, opacity: GLASS_OPACITY, depthWrite: false, side: THREE.DoubleSide });
        glassMats.push(mat);
      } else {
        const map = old && old.map ? old.map : null;
        if (map) { map.anisotropy = Math.min(8, maxAniso); map.colorSpace = THREE.SRGBColorSpace; }
        mat = new THREE.MeshBasicMaterial({ map, color: map ? 0xffffff : (old && old.color ? old.color : 0xdddddd) });
        prepareMaterial(mat, cls === 'wall', adapt, proj);
        if (cls === 'wall') wallMats.push(mat);
      }
      if (cls === 'glass') wallMats.push(mat);
      if (old && old !== mat) old.dispose();
      o.material = mat;
      o.matrixAutoUpdate = false;
      o.updateMatrix();
      o.userData.tg_class = cls;
      (byClass[cls] = byClass[cls] || []).push(o);
      added.push(o);
    });
    gltf.scene.updateMatrixWorld(true);
    root.add(gltf.scene);
    parts += 1;
    applyVisibility(state);
    return added.length;
  }

  function load(url, onProgress) {
    return new Promise((resolve, reject) => {
      loader.load(url, (g) => resolve(adopt(g)), (e) => onProgress && e.total && onProgress(e.loaded / e.total), reject);
    });
  }

  function applyVisibility(s) {
    state = Object.assign({}, state, s);
    const { mode, cut, furniture, garden } = state;
    const cutaway = mode !== 'walk' && mode !== 'exterior' && cut;
    const show = {
      base: true,
      wall: true,
      glass: true,
      exterior: mode === 'exterior',
      ceiling: mode === 'walk',
      furniture: furniture,
      decor_high: furniture && !cutaway,
      landscape: garden,
    };
    for (const [cls, list] of Object.entries(byClass)) {
      const v = show[cls] !== undefined ? show[cls] : true;
      for (const o of list) o.visible = v;
    }
    const planes = cutaway ? [cutPlane] : null;
    for (const m of wallMats) {
      if ((m.clippingPlanes ? 1 : 0) !== (planes ? 1 : 0)) m.needsUpdate = true;
      m.clippingPlanes = planes;
    }
    // Depth cubes describe the walk-mode geometry; they are stale once furniture or garden change.
    const key = `${furniture}|${garden}|${parts}`;
    if (key !== visKey) {
      visKey = key;
      for (const e of panos.values()) e.depthReady = false;
    }
  }

  // k = [r, g, b] gains (see prepareMaterial), or null for the bake as-is. Eased in render().
  function setAdaptation(k) {
    if (k && k.length === 3) adaptTarget.set(k[0], k[1], k[2]);
    else adaptTarget.set(1, 1, 1);
  }

  function stepAdaptation() {
    const now = performance.now();
    const dt = (now - adaptClock) / 1000;
    adaptClock = now;
    if (dt > ADAPT_SNAP) adapt.value.copy(adaptTarget);
    else adapt.value.lerp(adaptTarget, 1 - Math.exp(-dt / ADAPT_TAU));
  }

  // ---- Panorama projection -------------------------------------------------------------------

  // image: ImageBitmap / HTMLImageElement of an equirectangular panorama (sRGB, top row = up).
  // center: the stop's eye point in SCENE feet; offset: the manifest's yaw offset (radians).
  // full: true for the full-resolution file (a later half-resolution copy is ignored).
  // instant: skip the fade-in (the page already shows this panorama, e.g. coming from the 360° view).
  function setPanorama(id, image, center, offset = 0, full = false, instant = false) {
    let e = panos.get(id);
    if (e && e.full && !full) {
      if (image.close) image.close();
      return;
    }
    const tex = new THREE.Texture(image);
    tex.flipY = false;
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.magFilter = THREE.LinearFilter;
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    tex.generateMipmaps = true;
    tex.anisotropy = Math.min(8, maxAniso);
    tex.onUpdate = () => {                 // uploaded: the decoded copy is no longer needed
      tex.onUpdate = null;
      if (image.close) image.close();
    };
    tex.needsUpdate = true;
    const now = performance.now();
    if (e) {
      releaseTexture(e.tex);
      Object.assign(e, { tex, full, offset });
      if (instant) e.born = now - PANO_FADE * 1000;
    } else {
      e = {
        id, tex, full, offset, center: new THREE.Vector3(center[0], center[1], center[2]),
        cube: null, depthReady: false, born: instant ? now - PANO_FADE * 1000 : now, used: now,
      };
      panos.set(id, e);
    }
    trimPanoramas();
  }

  // A texture that was never drawn still holds its decoded image (onUpdate closes it on upload).
  function releaseTexture(tex) {
    if (tex.onUpdate && tex.image && tex.image.close) tex.image.close();
    tex.dispose();
  }

  function hasPanorama(id) {
    const e = panos.get(id);
    return e ? { full: e.full, depth: e.depthReady } : null;
  }

  // targets: [{id, weight}] (weights summing to 1; the nearest stops the camera can see), or null.
  // wanted: ids the page is loading for the route ahead; they are never evicted (keep it short).
  function setProjection(targets, wanted) {
    projTargets = Array.isArray(targets) ? targets.filter((t) => t && t.weight > 0) : [];
    projWanted = new Set(Array.isArray(wanted) ? wanted : []);
  }

  function dropPanorama(e) {
    releaseTexture(e.tex);
    if (e.cube && e.cube.owner === e) e.cube.owner = null;
    panos.delete(e.id);
    projWeights.delete(e.id);
  }

  // Evict least recently used panoramas, never one on screen or still wanted, and keep at most
  // maxFull at full resolution.
  function trimPanoramas() {
    const keep = new Set(projTargets.map((t) => t.id));
    for (const [id, w] of projWeights) if (w > 0) keep.add(id);
    const victims = (pred) => [...panos.values()].filter((e) => pred(e) && !keep.has(e.id)).sort((a, b) => a.used - b.used);
    let fulls = [...panos.values()].filter((e) => e.full).length;
    for (const e of victims((x) => x.full)) {
      if (fulls <= maxFull) break;
      dropPanorama(e);
      fulls -= 1;
    }
    for (const id of projWanted) keep.add(id);
    for (const e of victims(() => true)) {
      if (panos.size <= cacheSize) break;
      dropPanorama(e);
    }
  }

  // Depth cubes come from a small pool (each holds a colour and a depth buffer per face); a stop
  // that loses its cube simply renders it again when it is next on screen.
  function cubeFor(e, busy) {
    if (e.cube && e.cube.owner === e) return e.cube;
    let c = cubes.find((x) => !x.owner);
    if (!c && cubes.length < PANO_DEPTH_POOL) {
      c = {
        rt: new THREE.WebGLCubeRenderTarget(depthSize, {
          type: THREE.UnsignedByteType, format: THREE.RGBAFormat, generateMipmaps: false,
          minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
        }),
        owner: null,
      };
      cubes.push(c);
    }
    if (!c) c = cubes.filter((x) => !busy.has(x.owner)).sort((a, b) => a.owner.used - b.owner.used)[0];
    if (c.owner) { c.owner.cube = null; c.owner.depthReady = false; }
    c.owner = e;
    e.cube = c;
    e.depthReady = false;
    return c;
  }

  function renderDepth(e, busy) {
    const rt = cubeFor(e, busy).rt;
    if (e.depthReady) return;
    if (!cubeCam) cubeCam = new THREE.CubeCamera(0.05, PANO_DEPTH_FAR, rt);
    cubeCam.renderTarget = rt;
    cubeCam.position.copy(e.center);
    cubeCam.updateMatrixWorld(true);
    const hidden = [];
    for (const o of byClass.glass || []) if (o.visible) { o.visible = false; hidden.push(o); }
    const backdropShown = backdrop.visible;
    backdrop.visible = false;
    depthMat.uniforms.uCenter.value.copy(e.center);
    scene.overrideMaterial = depthMat;
    renderer.getClearColor(clearTmp);
    const clearAlpha = renderer.getClearAlpha();
    renderer.setClearColor(0xffffff, 1);   // cleared texels unpack to "far": visible
    cubeCam.update(renderer, scene);
    renderer.setClearColor(clearTmp, clearAlpha);
    scene.overrideMaterial = null;
    backdrop.visible = backdropShown;
    for (const o of hidden) o.visible = true;
    e.depthReady = true;
  }

  function smooth(a, b, x) {
    const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
    return t * t * (3 - 2 * t);
  }

  function updateProjection() {
    const now = performance.now();
    const dt = (now - projClock) / 1000;
    projClock = now;
    const walk = state.mode === 'walk';
    if (!walk) projWeights.clear();       // depth cubes are only valid for the walk-mode geometry
    const target = new Map(walk ? projTargets.map((t) => [t.id, t.weight]) : []);
    // Ease the blend weights so a stop coming into view (through a doorway) never pops.
    const k = dt > ADAPT_SNAP ? 1 : 1 - Math.exp(-dt / PANO_TAU);
    for (const id of new Set([...projWeights.keys(), ...target.keys()])) {
      const w = (projWeights.get(id) || 0) + ((target.get(id) || 0) - (projWeights.get(id) || 0)) * k;
      if (w < 0.002 && !target.has(id)) projWeights.delete(id);
      else projWeights.set(id, w);
    }
    // The two heaviest stops whose panorama is on the GPU.
    const slots = [];
    for (const [id, w] of [...projWeights].sort((a, b) => b[1] - a[1])) {
      const e = panos.get(id);
      if (!e || slots.length === 2) continue;
      e.used = now;
      slots.push({ e, w, fade: Math.min(1, (now - e.born) / (PANO_FADE * 1000)) });
    }
    const busy = new Set(slots.map((x) => x.e));
    for (const x of slots) if (!x.e.depthReady || !x.e.cube || x.e.cube.owner !== x.e) renderDepth(x.e, busy);
    const raw = slots.reduce((s, x) => s + x.w * x.fade, 0);
    const strength = Math.min(1, slots.reduce((s, x) => s + x.fade, 0));
    const on = walk && raw > 1e-4;
    proj.uTgOn.value = on ? 1 : 0;
    const w = [0, 0];
    const occ = [0, 0];
    slots.forEach((x, i) => {
      w[i] = on ? (x.w * x.fade / raw) * strength : 0;
      occ[i] = smooth(PANO_OCCLUSION[0], PANO_OCCLUSION[1], camera.position.distanceTo(x.e.center));
    });
    proj.uTgW.value.set(w[0], w[1]);
    proj.uTgOcc.value.set(occ[0], occ[1]);
    proj.uTgOffset.value.set(slots[0] ? slots[0].e.offset : 0, slots[1] ? slots[1].e.offset : 0);
    proj.uTgCenterA.value.copy(slots[0] ? slots[0].e.center : camera.position);
    proj.uTgCenterB.value.copy(slots[1] ? slots[1].e.center : camera.position);
    proj.uTgPanoA.value = slots[0] ? slots[0].e.tex : null;
    proj.uTgPanoB.value = slots[1] ? slots[1].e.tex : null;
    proj.uTgDepthA.value = slots[0] ? slots[0].e.cube.rt.texture : null;
    proj.uTgDepthB.value = slots[1] ? slots[1].e.cube.rt.texture : null;
    const total = on ? w[0] + w[1] : 0;
    for (const m of glassMats) m.opacity = GLASS_OPACITY * (1 - total);   // the panoramas already show the glass
    backdrop.visible = on;
    backdrop.position.copy(camera.position);
    backdrop.updateMatrixWorld();
    projInfo = {
      on,
      slots: slots.map((x, i) => ({ id: x.e.id, weight: Math.round(w[i] * 1000) / 1000, occlusion: Math.round(occ[i] * 1000) / 1000, full: x.e.full })),
    };
    trimPanoramas();
  }

  // eye / aim in SCENE feet; fovY radians.
  function render(eye, aim, fovY, width, height, pixelRatio) {
    stepAdaptation();
    renderer.setPixelRatio(pixelRatio || 1);
    renderer.setSize(width, height, false);
    camera.fov = fovY * 180 / Math.PI;
    camera.aspect = width / height;
    camera.near = state.mode === 'walk' ? 0.08 : 0.5;
    camera.far = state.mode === 'walk' ? 400 : 1200;
    camera.updateProjectionMatrix();
    camera.position.set(eye[0], eye[1], eye[2]);
    camera.lookAt(aim[0], aim[1], aim[2]);
    camera.updateMatrixWorld();
    updateProjection();
    renderer.render(scene, camera);
  }

  // projection x view, column-major (same layout as the app's mul(perspective, lookAt)).
  function pv() {
    const m = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    return Array.from(m.elements);
  }

  function stats() {
    let tris = 0;
    let meshes = 0;
    root.traverse((o) => {
      if (o.isMesh) {
        meshes++;
        const g = o.geometry;
        tris += g.index ? g.index.count / 3 : g.attributes.position.count / 3;
      }
    });
    return {
      triangles: Math.round(tris), meshes, parts, calls: renderer.info.render.calls, classes: Object.keys(byClass),
      adaptation: adapt.value.toArray().map((v) => Math.round(v * 1000) / 1000),
      projection: Object.assign({ cached: [...panos.keys()] }, projInfo),
    };
  }

  return {
    gl, renderer, scene, camera, load, applyVisibility, setAdaptation, render, pv, stats,
    setPanorama, hasPanorama, setProjection,
    projectionInfo: () => Object.assign({ cached: [...panos.keys()], box: proj.uTgBox.value.toArray().map((v) => Math.round(v * 100) / 100) }, projInfo),
    resetState: () => renderer.resetState(),
    get loaded() { return parts > 0; },
  };
}
