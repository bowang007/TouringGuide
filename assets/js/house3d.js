// Real-time renderer for the baked house model (three.js r170, vendored in assets/vendor/three).
//
// The GLB (tools/render/bake_web.py) carries Cycles-baked, display-referred colour in each
// texture, so everything renders UNLIT: the browser shows the same global illumination,
// soft shadows and materials as the path-traced panoramas, at real-time speed.
//
// Coordinates: the GLB is in metres with SCENE axes (x east, y up, z south), so scaling the
// root by 1/0.3048 puts it in SCENE feet, the unit the rest of the app (camera, hotspots,
// minimap, collision, measurements) already uses. No other conversion is needed: three.js
// and the app share handedness, -Z-forward cameras and vertical FOV.
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

// Eye adaptation (walk mode): per-channel gain k of the highlight-preserving curve
// f(x) = k x / (1 + (k - 1) x) on linear display colour, shared by every non-glass material.
// k = 1 is the bake as-is; tools/render/adapt_web.py measures each tour stop's k so the walk matches
// that stop's panorama exposure and white balance.
const ADAPT_TAU = 0.35;                  // s, easing time constant
const ADAPT_SNAP = 0.5;                  // s without frames -> jump straight to the target

function prepareMaterial(mat, cap, adapt) {
  // cap: back faces of clipped walls show a solid section colour instead of the wall's inside.
  if (cap) mat.side = THREE.DoubleSide;
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uAdapt = adapt;
    let head = 'uniform vec3 uAdapt;\n';
    let body = '#include <map_fragment>\n\tdiffuseColor.rgb = uAdapt * diffuseColor.rgb / ( 1.0 + ( uAdapt - 1.0 ) * diffuseColor.rgb );';
    if (cap) {
      shader.uniforms.capColor = { value: CAP };
      head += 'uniform vec3 capColor;\n';
      body += '\n\tif ( ! gl_FrontFacing ) diffuseColor.rgb = capColor;';
    }
    shader.fragmentShader = head + shader.fragmentShader.replace('#include <map_fragment>', body);
  };
  mat.customProgramCacheKey = () => (cap ? 'tgcap' : 'tgadapt');
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
  const maxAniso = renderer.capabilities.getMaxAnisotropy();
  let state = { mode: 'exterior', cut: true, furniture: true, garden: true };
  const adapt = { value: new THREE.Vector3(1, 1, 1) };
  const adaptTarget = new THREE.Vector3(1, 1, 1);
  let adaptClock = 0;
  let parts = 0;

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
        mat = new THREE.MeshBasicMaterial({ color: 0xd4e6e8, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide });
      } else {
        const map = old && old.map ? old.map : null;
        if (map) { map.anisotropy = Math.min(8, maxAniso); map.colorSpace = THREE.SRGBColorSpace; }
        mat = new THREE.MeshBasicMaterial({ map, color: map ? 0xffffff : (old && old.color ? old.color : 0xdddddd) });
        prepareMaterial(mat, cls === 'wall', adapt);
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
    };
  }

  return {
    gl, renderer, scene, camera, load, applyVisibility, setAdaptation, render, pv, stats,
    resetState: () => renderer.resetState(),
    get loaded() { return parts > 0; },
  };
}
