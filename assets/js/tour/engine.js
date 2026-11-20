// Real-time engine of the tour (three.js r170, vendored in assets/vendor/three).
// It grew out of the engine of the single-file page (assets/js/house3d.js, removed): that file's
// methods (applyVisibility, setProjection, render(eye, aim, ...), the 'walk' / 'top' / 'orbit' mode
// names) still work the same way and are marked "legacy" below; the photoreal exterior orbit uses
// them. Test harness: tools/web/dev/.
//
// The GLB (tools/render/bake_web.py) carries Cycles-baked, display-referred colour in each
// texture, so everything renders UNLIT: the browser shows the same global illumination,
// soft shadows and materials as the path-traced panoramas, at real-time speed.
//
// Sweeps (setSweeps / setPanorama / setSweepBlend): the camera rests only on sweeps, the points the
// path-traced 360° panoramas were rendered from. At rest the frame IS that panorama: one full-screen
// equirectangular lookup, no mesh drawn. A move between two sweeps projects both panoramas onto the
// model from their own centres and cross-fades them while the camera glides, so walls, floors and
// furniture keep their path-traced look with correct parallax. Each panorama is tested against a depth
// cube rendered from its sweep: a surface one sweep cannot see takes the other panorama, a surface
// neither sees takes the nearer panorama without the test (never the low-resolution bake).
// None of this needs the model at rest: before load() has resolved the engine already draws the
// panorama of a sweep (no depth, so nothing can be picked and the overlay is not occluded yet).
// A sharper level of a panorama (setPanorama on a sweep that already has one) is uploaded in slices
// over several frames and, on the sweep the camera rests on, fades in over the level on screen
// (LEVEL_FADE); dropUpgrade(id) stops such an upload when the page no longer needs it.
//
// Drawing on demand: dirty() says whether the next frame would differ although the page changed
// nothing itself, and engine.onDirty (a function the page may set) is called at that moment, so a
// page whose view stands still can let its animation loop sleep. `blend` is what setSweepBlend was
// last given.
//
// Dollhouse / floor plan (setMode): the baked model from outside, house only: ceilings, roof, facade,
// grounds and everything outside the footprint are hidden, walls are cut a little above 8 ft and
// capped, and the exterior walls on the viewer's side are discarded per fragment so the rooms show.
//
// Photoreal exterior (setPanorama's `frame` + setProjection): the same projection with perspective
// frames, path-traced from orbit positions around the house (tools/render/render_exterior.py).
//
// Coordinates: the GLB is in metres with SCENE axes (x east, y up, z south), so scaling the
// root by 1/0.3048 puts it in SCENE feet, the unit of the whole app. three.js and the app share
// handedness, -Z-forward cameras and vertical FOV. The panoramas use the same frame
// (assets/panos/manifest.json: centre column = yaw `offset`, yaw 0 = -z).
//
// Visibility classes (node.extras.tg_class):
//   exterior   roof / facade             -> exterior mode only
//   ceiling    ceilings, ceiling lights  -> inside; fades with setClassOpacity during a fly-out
//   wall,glass walls/trim/windows/doors  -> cut at 8 ft and near-side culled in dollhouse / floor plan
//   decor_high art, uppers, mirrors      -> follows the furniture toggle
//   furniture  furniture + low decor     -> furniture toggle
//   landscape  grounds, deck, fences     -> garden toggle; never in dollhouse / floor plan
//   base       floors, built-ins         -> always
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

const FT = 0.3048;
const CUT_Y = 2.1;                       // ft, the legacy cutaway ('top' / 'orbit' modes)
const CAP = new THREE.Color(0x3b403d);   // poché colour seen inside cut walls (legacy modes)
const CLEAR = new THREE.Color(0.79, 0.88, 0.94);
const GLASS_OPACITY = 0.16;

// Dollhouse / floor plan.
const DOLL_CLIP_Y = 8.01;                // ft: walls are cut here (ceilings and wall tops sit at 8.0)
const DOLL_CLIP_OPEN = 16;               // ft: the cut height while the ceilings are still fully shown
const DOLL_CAP = new THREE.Color(0xa9a8a4);   // neutral colour of the cut wall tops
const DOLL_UNLIT = 0.045;                    // linear grey that replaces unlit (black) bake texels in the dollhouse
const DOLL_SHELL = 0.9;                  // ft: exterior wall (0.45) + casings and the recessed garage door
const DOLL_MARGIN = 0.5;                 // ft: furniture and decor may stick out of the footprint this far
const DOLL_MARGIN_BASE = 0.03;           // ft: floors end with the house (the porch slab is not a strip along the walls)
const FOOT_MAX = 16;                     // footprint rectangles the shaders accept

// Eye adaptation (bake only): per-channel gain k of the highlight-preserving curve
// f(x) = k x / (1 + (k - 1) x) on linear display colour, shared by every non-glass material.
// k = 1 is the bake as-is; tools/render/adapt_web.py measures each tour stop's k so the bake matches
// that stop's panorama exposure and white balance. It never touches panorama pixels.
// Outdoor groups ('exterior', 'landscape') were baked at the exterior exposure (bake_web.py
// --exposure-ext), so they get their own gain ko.
const ADAPT_TAU = 0.35;                  // s, easing time constant
const ADAPT_SNAP = 0.5;                  // s without frames -> jump straight to the target

// Panorama projection.
const PANO_DEPTH_SIZE = 512;             // depth cube face size (texels); opts.depthSize overrides
const PANO_DEPTH_FAR = 160;              // ft; farther surfaces count as visible
const PANO_DEPTH_FAR_EXTERIOR = 700;     // ft, for the exterior frames (~100 ft out, neighbours behind)
const PANO_DEPTH_POOL = 4;               // depth cubes (rest + transition target + two prepared); opts.depthPool
const PANO_FADE = 0.25;                  // s, fade-in once a panorama arrives (legacy setProjection only)
const PANO_TAU = 0.12;                   // s, easing of the blend weights (legacy setProjection only)
const PANO_OCCLUSION = [0.03, 0.4];      // ft from a stop over which its occlusion test fades in
const BACKDROP_RADIUS = 300;             // ft
const REST_EPS = 0.02;                   // ft: the camera counts as standing on a sweep within this
const SLICE_BYTES = 8192 * 256 * 4;      // texels uploaded per frame by the sliced upload (8K: 16 frames)
const LEVEL_FADE = 220;                  // ms: a sharper level of the resting sweep fades in over the one on screen

// Resolution levels of a panorama and the texture budget (opts.budget overrides).
const LEVEL_RANK = { '2k': 1, '4k': 2, '8k': 3 };
const RANK_LEVEL = [null, '2k', '4k', '8k'];
const BUDGET = { max8k: 1, max4k: 2, max2k: 8, maxBytes: 420 * 1048576 };

// Class codes stored in the alpha channel of the depth cubes (255 = nothing within the far plane).
const CLASS_CODE = { base: 1, wall: 2, ceiling: 3, furniture: 4, decor_high: 5, exterior: 6, landscape: 7, glass: 8 };
const CODE_CLASS = Object.keys(CLASS_CODE).reduce((a, k) => { a[CLASS_CODE[k]] = k; return a; }, []);

// Equirectangular lookup shared by the model and the backdrop. The derivatives come from whichever
// of u and u + 0.5 is continuous here, so the seam at the back of the panorama never drops to the
// smallest mip level.
//
// A perspective frame (uTgPersp = 1) is looked up through its camera's projection x view matrix
// instead; its alpha is the frame coverage, feathered over the outer 3% so frames end softly.
// p.w = 0 projects a direction (the backdrop, at infinity).
const PANO_SAMPLE_GLSL = `
uniform float uTgOn;
uniform vec2 uTgW;
uniform vec2 uTgOffset;
uniform vec2 uTgPersp;
uniform mat4 uTgMatA;
uniform mat4 uTgMatB;
uniform sampler2D uTgPanoA;
uniform sampler2D uTgPanoB;
uniform float uTgSweep;
uniform float uTgFade;
uniform float uTgFallback;
varying vec3 vTgWorld;
vec3 tgPano( sampler2D t, vec3 d, float offset ) {
	float s = ( atan( d.x, - d.z ) - offset ) * 0.15915494309189535 + 0.5;
	vec2 uv = vec2( fract( s ), 0.5 - asin( clamp( d.y, - 1.0, 1.0 ) ) * 0.3183098861837907 );
	vec2 uv2 = vec2( fract( s + 0.5 ), uv.y );
	vec2 dx = dFdx( uv ), dy = dFdy( uv ), dx2 = dFdx( uv2 ), dy2 = dFdy( uv2 );
	if ( abs( dx2.x ) + abs( dy2.x ) < abs( dx.x ) + abs( dy.x ) ) { dx = dx2; dy = dy2; }
	return textureGrad( t, uv, dx, dy ).rgb;
}
vec4 tgFrame( sampler2D t, mat4 m, vec4 p ) {
	vec4 c = m * p;
	vec2 ndc = c.xy / max( c.w, 1e-4 );
	vec2 e = smoothstep( vec2( 1.0 ), vec2( 0.97 ), abs( ndc ) );
	vec3 rgb = texture( t, vec2( ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5 ) ).rgb;
	return vec4( rgb, e.x * e.y * step( 1e-4, c.w ) );
}
vec4 tgSample( sampler2D t, float persp, mat4 m, vec4 p, vec3 d, float offset ) {
	if ( persp > 0.5 ) return tgFrame( t, m, p );
	return vec4( tgPano( t, d, offset ), 1.0 );
}
`;

// Visibility of a surface point from a stop: compare its distance with the depth cube rendered
// there (distance / far packed into RGB, the class code in A). The tolerance grows with distance and
// at grazing angles (one cube texel spans more depth). Five taps around the direction, keeping the
// most pessimistic, widen every occluder by about a texel: the antialiased edges of thin things
// (pendants, stems, chair legs) then never smear onto the surfaces behind them. Only occluders inside
// the house envelope count. Planting and fences outside are simplified in the model, so their depth
// would wrongly hide what the render shows between the leaves and slats.
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
	float s = unpackRGBToDepth( textureCube( depth, d ).rgb ) * uTgFar;
	vec3 hit = c + d * s;
	// Cleared texels (nothing within the cube's far plane) unpack to ~far: never an occluder.
	bool inside = s < uTgFar * 0.998 && hit.x > uTgBox.x && hit.z > uTgBox.y && hit.x < uTgBox.z && hit.z < uTgBox.w;
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

// Sweep blend (uTgSweep = 1, setSweepBlend): the weights are the transition clock itself. Each
// panorama counts with weight x visibility, so a surface only one of them sees shows that one at full
// strength however small its weight; a surface neither sees takes the panoramas without the test,
// switching from A to B around the middle of the move (uTgFallback = 1), or the bake in the dollhouse
// (uTgFallback = 0). uTgFade scales the whole projection (fly to / from the dollhouse).
// Legacy (uTgSweep = 0, setProjection): the original rule, bake where no panorama sees.
const PANO_FRAGMENT = `
	if ( uTgOn > 0.5 ) {
		vec3 tgN = normalize( cross( dFdx( vTgWorld ), dFdy( vTgWorld ) ) );
		vec3 tgSum = vec3( 0.0 );
		float tgSeenW = 0.0;
		vec3 tgA = vec3( 0.0 );
		vec3 tgB = vec3( 0.0 );
		float tgVis = 0.0;
		if ( uTgW.x > 0.0 ) {
			vec3 r = vTgWorld - uTgCenterA;
			float dist = max( length( r ), 1e-4 );
			vec4 c = tgSample( uTgPanoA, uTgPersp.x, uTgMatA, vec4( vTgWorld, 1.0 ), r / dist, uTgOffset.x );
			float v = c.a * tgSeen( uTgDepthA, uTgCenterA, r / dist, dist, uTgOcc.x, tgN );
			tgSum += uTgW.x * v * c.rgb;
			tgSeenW += uTgW.x * v;
			tgA = c.rgb;
			tgVis = max( tgVis, v );
		}
		if ( uTgW.y > 0.0 ) {
			vec3 r = vTgWorld - uTgCenterB;
			float dist = max( length( r ), 1e-4 );
			vec4 c = tgSample( uTgPanoB, uTgPersp.y, uTgMatB, vec4( vTgWorld, 1.0 ), r / dist, uTgOffset.y );
			float v = c.a * tgSeen( uTgDepthB, uTgCenterB, r / dist, dist, uTgOcc.y, tgN );
			tgSum += uTgW.y * v * c.rgb;
			tgSeenW += uTgW.y * v;
			tgB = c.rgb;
			tgVis = max( tgVis, v );
		}
		if ( uTgSweep > 0.5 ) {
			float tgT = uTgW.y / max( uTgW.x + uTgW.y, 1e-6 );
			vec3 tgBlind = mix( tgA, tgB, uTgW.x <= 0.0 ? 1.0 : uTgW.y <= 0.0 ? 0.0 : smoothstep( 0.35, 0.65, tgT ) );
			float tgK = clamp( tgVis * 2.0, 0.0, 1.0 );
			vec3 tgC = mix( tgBlind, tgSum / max( tgSeenW, 1e-9 ), tgK );
			diffuseColor.rgb = mix( diffuseColor.rgb, tgC, uTgFade * mix( tgK, 1.0, uTgFallback ) );
		} else {
			float tgStrength = clamp( uTgW.x + uTgW.y, 0.0, 1.0 ) * smoothstep( 0.0, 0.35, tgSeenW );
			diffuseColor.rgb = mix( diffuseColor.rgb, tgSum / max( tgSeenW, 1e-5 ), tgStrength );
		}
	}`;

// Dollhouse / floor plan rules. The footprint is a union of rectangles (x0, z0, x1, z1) in feet.
// Walls, glass and wall caps: nothing above the cut, nothing outside the footprint, and nothing in
// the outer shell on the viewer's side: a fragment goes when stepping DOLL_SHELL out of it, along
// its own normal turned to the viewer or along a plan axis that points to the viewer, leaves the
// footprint. That removes the whole thickness of a near exterior wall (both faces, reveals, sills,
// casings, panes) and keeps the far walls and every interior wall. Seen from straight above no axis
// points to the viewer, so the floor plan keeps all four sides.
const SHELL_GLSL = `
uniform float uTgClipY;
uniform float uTgCull;
uniform int uTgFootN;
uniform vec4 uTgFoot[ ${FOOT_MAX} ];
bool tgInFoot( vec2 p, float m ) {
	for ( int i = 0; i < ${FOOT_MAX}; i ++ ) {
		if ( i >= uTgFootN ) break;
		vec4 r = uTgFoot[ i ];
		if ( p.x > r.x - m && p.y > r.y - m && p.x < r.z + m && p.y < r.w + m ) return true;
	}
	return false;
}
`;
const SHELL_DISCARD = `
	if ( vTgWorld.y > uTgClipY ) discard;
	if ( uTgCull > 0.5 ) {
		vec2 tgP = vTgWorld.xz;
		vec3 tgV = isOrthographic ? vec3( viewMatrix[ 0 ][ 2 ], viewMatrix[ 1 ][ 2 ], viewMatrix[ 2 ][ 2 ] ) : normalize( cameraPosition - vTgWorld );
		vec3 tgF = normalize( cross( dFdx( vTgWorld ), dFdy( vTgWorld ) ) );
		if ( dot( tgF, tgV ) < 0.0 ) tgF = - tgF;
		if ( ! tgInFoot( tgP, 0.02 ) ) discard;
		if ( ! tgInFoot( tgP + tgF.xz * ${DOLL_SHELL.toFixed(2)}, 0.0 ) ) discard;
		if ( tgV.x > 0.04 && ! tgInFoot( tgP + vec2( ${DOLL_SHELL.toFixed(2)}, 0.0 ), 0.0 ) ) discard;
		if ( tgV.x < - 0.04 && ! tgInFoot( tgP - vec2( ${DOLL_SHELL.toFixed(2)}, 0.0 ), 0.0 ) ) discard;
		if ( tgV.z > 0.04 && ! tgInFoot( tgP + vec2( 0.0, ${DOLL_SHELL.toFixed(2)} ), 0.0 ) ) discard;
		if ( tgV.z < - 0.04 && ! tgInFoot( tgP - vec2( 0.0, ${DOLL_SHELL.toFixed(2)} ), 0.0 ) ) discard;
	}`;
const FOOT_DISCARD = (margin) => `
	if ( uTgCull > 0.5 && ! tgInFoot( vTgWorld.xz, ${margin.toFixed(2)} ) ) discard;`;

// flags: shell (wall / glass / cap rules), pano (bake + adaptation + panorama projection),
// outdoor (exterior exposure push), cap (back faces show the section colour while cutting),
// tight (dollhouse: nothing outside the footprint; floors).
function prepareMaterial(mat, proj, flags = {}, adapt = null) {
  const { shell = false, pano = false, outdoor = false, cap = false, tight = false } = flags;
  if (cap) mat.side = THREE.DoubleSide;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, proj);
    if (adapt) shader.uniforms.uAdapt = adapt;
    shader.vertexShader = 'varying vec3 vTgWorld;\n' + shader.vertexShader.replace('#include <project_vertex>',
      '#include <project_vertex>\n\tvTgWorld = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;');
    let head = '#include <packing>\n' + SHELL_GLSL;
    let body = (shell ? SHELL_DISCARD : FOOT_DISCARD(tight ? DOLL_MARGIN_BASE : DOLL_MARGIN)) + '\n\t#include <map_fragment>';
    // dollhouse / floor plan: with the near walls and ceilings gone, surfaces that never saw light in the bake
    // (cabinet backs, the far side of the fireplace, slab edges) show. Black reads as a hole in the model, so
    // texels with almost no light go to a dark neutral grey, like a cut surface.
    body += '\n\tif ( uTgCull > 0.5 ) { float tgUnlit = dot( diffuseColor.rgb, vec3( 0.2126, 0.7152, 0.0722 ) );'
      + ' diffuseColor.rgb = mix( vec3( ' + DOLL_UNLIT.toFixed(3) + ' ), diffuseColor.rgb, smoothstep( 0.0, 0.03, tgUnlit ) ); }';
    if (pano) {
      head += 'uniform vec3 uAdapt;\nuniform float uTgDebug;\n' + PANO_SAMPLE_GLSL + PANO_DEPTH_GLSL;
      body += '\n\tdiffuseColor.rgb = uAdapt * diffuseColor.rgb / ( 1.0 + ( uAdapt - 1.0 ) * diffuseColor.rgb );';
      if (outdoor) {
        // pushed several stops brighter (seen from inside), highlights go to white the way the panoramas'
        // filmic view does, instead of staying saturated
        body += '\n\tfloat tgL = dot( diffuseColor.rgb, vec3( 0.2126, 0.7152, 0.0722 ) );'
          + '\n\tfloat tgPush = clamp( ( max( max( uAdapt.r, uAdapt.g ), uAdapt.b ) - 1.5 ) / 5.0, 0.0, 1.0 );'
          + '\n\tdiffuseColor.rgb = mix( diffuseColor.rgb, vec3( tgL ), tgPush * smoothstep( 0.25, 0.95, tgL ) );';
      }
      body += '\n\tif ( uTgDebug > 0.5 ) diffuseColor.rgb = vec3( 1.0, 0.0, 1.0 );';   // test hook: where the bake shows
      body += PANO_FRAGMENT;
    } else {
      head += 'varying vec3 vTgWorld;\n';
    }
    if (cap) {
      head += 'uniform float uTgCapOn;\nuniform vec3 uTgCapColor;\n';
      body += '\n\tif ( ! gl_FrontFacing && uTgCapOn > 0.5 ) diffuseColor.rgb = uTgCapColor;';
    }
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\n' + head)
      .replace('#include <map_fragment>', body);
  };
  const key = 'tg4' + (shell ? 's' : '') + (pano ? 'p' : '') + (outdoor ? 'o' : '') + (cap ? 'c' : '') + (tight ? 't' : '');
  mat.customProgramCacheKey = () => key;
  return mat;
}

// Bilinear distance lookup in a depth cube (the texture itself is nearest-filtered, packed RGB):
// the four texel centres around the direction on its own face.
const CUBE_BILINEAR_GLSL = `
uniform float uTgCubeN;
float tgTexelDist( samplerCube t, vec3 d ) {
	return unpackRGBToDepth( textureCube( t, d ).rgb );
}
float tgCubeDist( samplerCube t, vec3 d ) {
	vec3 a = abs( d );
	vec3 w, u, v;
	if ( a.x >= a.y && a.x >= a.z ) { w = vec3( d.x < 0.0 ? - 1.0 : 1.0, 0.0, 0.0 ); u = vec3( 0.0, 1.0, 0.0 ); v = vec3( 0.0, 0.0, 1.0 ); }
	else if ( a.y >= a.z ) { w = vec3( 0.0, d.y < 0.0 ? - 1.0 : 1.0, 0.0 ); u = vec3( 1.0, 0.0, 0.0 ); v = vec3( 0.0, 0.0, 1.0 ); }
	else { w = vec3( 0.0, 0.0, d.z < 0.0 ? - 1.0 : 1.0 ); u = vec3( 1.0, 0.0, 0.0 ); v = vec3( 0.0, 1.0, 0.0 ); }
	float ma = max( a.x, max( a.y, a.z ) );
	vec2 p = vec2( dot( d, u ), dot( d, v ) ) / ma;
	vec2 x = ( p * 0.5 + 0.5 ) * uTgCubeN - 0.5;
	vec2 i = clamp( floor( x ), 0.0, uTgCubeN - 2.0 );
	vec2 f = clamp( x - i, 0.0, 1.0 );
	vec2 p0 = ( i + 0.5 ) / uTgCubeN * 2.0 - 1.0;
	float e = 2.0 / uTgCubeN;
	float s00 = tgTexelDist( t, w + u * p0.x + v * p0.y );
	float s10 = tgTexelDist( t, w + u * ( p0.x + e ) + v * p0.y );
	float s01 = tgTexelDist( t, w + u * p0.x + v * ( p0.y + e ) );
	float s11 = tgTexelDist( t, w + u * ( p0.x + e ) + v * ( p0.y + e ) );
	return mix( mix( s00, s10, f.x ), mix( s01, s11, f.x ), f.y );
}
`;

function levelName(level, image) {
  if (typeof level === 'string' && LEVEL_RANK[level]) return level;
  const w = typeof level === 'number' && level > 16 ? level : (image && image.width) || 0;
  if (level === false) return '2k';
  if (level === true) return w > 6000 ? '8k' : '4k';
  if (typeof level === 'number' && level >= 1 && level <= 3) return RANK_LEVEL[level];
  return w > 6000 ? '8k' : w > 3000 ? '4k' : '2k';
}

function toVec3(v, out) {
  return Array.isArray(v) || ArrayBuffer.isView(v) ? out.set(v[0], v[1], v[2]) : out.copy(v);
}

export function createEngine(canvas, opts = {}) {
  const gl = opts.context || canvas.getContext('webgl2', {
    antialias: opts.antialias !== false, preserveDrawingBuffer: opts.preserveDrawingBuffer !== false,
    alpha: false, powerPreference: 'high-performance',
  });
  if (!gl) throw new Error('WebGL2 is not available');
  const renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: true, preserveDrawingBuffer: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.localClippingEnabled = true;
  renderer.autoClear = true;
  renderer.info.autoReset = false;        // one frame = scene + overlay (+ depth cubes rendered in it)
  renderer.setClearColor(CLEAR, 1);
  const caps = {
    maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
    maxAnisotropy: renderer.capabilities.getMaxAnisotropy(),
    renderer: (() => { const x = gl.getExtension('WEBGL_debug_renderer_info'); return x ? gl.getParameter(x.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); })(),
  };

  const scene = new THREE.Scene();
  const root = new THREE.Group();
  root.scale.setScalar(1 / FT);           // metres -> SCENE feet
  scene.add(root);
  const camera = new THREE.PerspectiveCamera(45, 1, 0.08, 900);
  const orthoCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.5, 1200);
  let activeCam = camera;
  // Rings, reticle and other markers of the page: drawn after the scene, depth-tested against it,
  // never part of a depth cube or a pick.
  const overlayScene = new THREE.Scene();
  const overlay = new THREE.Group();
  overlay.name = 'overlay';
  overlayScene.add(overlay);
  const byClass = {};
  const glassMats = [];
  const maxAniso = caps.maxAnisotropy;
  let state = { mode: 'exterior', cut: true, furniture: true, garden: true };
  const adapt = { value: new THREE.Vector3(1, 1, 1) };
  const adaptTarget = new THREE.Vector3(1, 1, 1);
  const adaptOut = { value: new THREE.Vector3(1, 1, 1) };
  const adaptOutTarget = new THREE.Vector3(1, 1, 1);
  let adaptClock = 0;
  let parts = 0;
  let dirtyFlag = true;                   // something the engine draws changed since the last render (touch())
  // The page may hang a function on engine.onDirty: it is called whenever the next frame would differ
  // although the page changed nothing itself (a panorama arrived, a level swapped, the model came in),
  // so a page that draws on demand can sleep in between.
  let api = null;
  function touch() {
    dirtyFlag = true;
    if (api && typeof api.onDirty === 'function') api.onDirty();
  }
  let animating = false;                  // adaptation or legacy weights still easing
  let sizeKey = '';

  const depthSize = opts.depthSize || PANO_DEPTH_SIZE;
  const depthPool = Math.max(3, opts.depthPool || PANO_DEPTH_POOL);
  const budget = Object.assign({}, BUDGET, opts.budget || {});
  if (Number.isFinite(opts.maxFull)) budget.max4k = opts.maxFull;       // legacy option names
  const cacheSize = opts.cacheSize || budget.max8k + budget.max4k + budget.max2k;
  const mipmap8k = opts.mipmap8k === true;
  const pickCopies = Math.max(1, opts.pickCopies || 2);
  const dollClipY = Number.isFinite(opts.clipY) ? opts.clipY : DOLL_CLIP_Y;
  const dollCap = new THREE.Color(opts.capColor !== undefined ? opts.capColor : DOLL_CAP);

  // Projection uniforms, shared by reference with every material (and the backdrop).
  const proj = {
    uTgOn: { value: 0 },
    uTgW: { value: new THREE.Vector2() },
    uTgOcc: { value: new THREE.Vector2() },
    uTgOffset: { value: new THREE.Vector2() },
    uTgPersp: { value: new THREE.Vector2() },
    uTgMatA: { value: new THREE.Matrix4() },
    uTgMatB: { value: new THREE.Matrix4() },
    uTgCenterA: { value: new THREE.Vector3() },
    uTgCenterB: { value: new THREE.Vector3() },
    uTgPanoA: { value: null },
    uTgPanoB: { value: null },
    uTgDepthA: { value: null },
    uTgDepthB: { value: null },
    uTgFar: { value: PANO_DEPTH_FAR },
    uTgTexel: { value: 2.5 / depthSize },                   // tap spacing: 2.5 texels at a face centre
    uTgBox: { value: new THREE.Vector4(-1e9, -1e9, 1e9, 1e9) },   // house envelope (x0, z0, x1, z1), ft
    uTgSweep: { value: 0 },
    uTgFade: { value: 1 },
    uTgFallback: { value: 0 },
    uTgDebug: { value: 0 },
    uTgClipY: { value: 1e9 },
    uTgCull: { value: 0 },
    uTgFootN: { value: 0 },
    uTgFoot: { value: Array.from({ length: FOOT_MAX }, () => new THREE.Vector4()) },
    uTgCapOn: { value: 1 },
    uTgCapColor: { value: CAP.clone() },
  };
  // opts.interior = [x0, z0, x1, z1]: the house envelope in SCENE feet (default: the bounding box of
  // the footprint). The margin keeps window frames and the wall thickness inside it.
  // Outside (exterior frames) every occluder counts.
  const boxAll = new THREE.Vector4(-1e9, -1e9, 1e9, 1e9);
  const boxInterior = boxAll.clone();
  let interiorGiven = false;
  if (Array.isArray(opts.interior) && opts.interior.length === 4) {
    const [x0, z0, x1, z1] = opts.interior;
    boxInterior.set(x0 - 0.3, z0 - 0.3, x1 + 0.3, z1 + 0.3);
    interiorGiven = true;
  }
  proj.uTgBox.value.copy(boxInterior);
  let footprint = [];                     // [[x0, z0, x1, z1], ...]
  let footKey = '';

  const sweeps = new Map();               // id -> {p: Vector3, offset}
  const panos = new Map();                // id -> entry (see setPanorama)
  const cubes = [];                       // depth cube pool: {rt, owner}
  const projWeights = new Map();          // id -> eased blend weight (legacy)
  let projTargets = [];
  let projWanted = new Set();
  let projClock = 0;
  let projInfo = { on: false, slots: [] };
  let projMode = '';
  let visKey = '';
  const blend = { a: null, b: null, t: 0 };   // setSweepBlend
  let projFade = 1;                       // setProjectionFade
  const classOpacity = {};                // setClassOpacity
  let restEntry = null;                   // the sweep the last frame rested on (pure panorama), or null
  let lastSet = null;                     // id of the panorama set last
  let debugNoRest = false;                // test hook: draw the model even when resting on a sweep
  const clearTmp = new THREE.Color();
  const background = CLEAR.clone();

  // Sky and anything without geometry (through windows, the skylight): the blended panoramas
  // looked up by view direction, i.e. at infinity. In the rest state (uTgPure) it is the whole frame:
  // the panorama exactly, and the depth of the sweep's depth cube so the overlay is occluded by walls.
  const backdropUniforms = Object.assign({
    uTgSky: { value: CLEAR }, uTgBg: { value: background }, uTgPure: { value: 0 }, uTgDepthOn: { value: 0 },
    uTgBackFade: { value: 1 },
    uTgProjZ: { value: new THREE.Vector2() }, uTgCubeN: { value: depthSize },
  }, proj);
  const backdrop = new THREE.Mesh(new THREE.SphereGeometry(BACKDROP_RADIUS, 48, 24), new THREE.ShaderMaterial({
    uniforms: backdropUniforms,
    vertexShader: 'varying vec3 vTgWorld;\nvoid main() {\n\tvec4 w = modelMatrix * vec4( position, 1.0 );\n\tvTgWorld = w.xyz;\n\tgl_Position = ( projectionMatrix * viewMatrix * w ).xyww;\n\tgl_Position.z *= 0.99999;\n}',
    fragmentShader: '#include <packing>\n' + PANO_SAMPLE_GLSL + CUBE_BILINEAR_GLSL + `uniform vec3 uTgSky;
uniform vec3 uTgBg;
uniform float uTgPure;
uniform float uTgDepthOn;
uniform float uTgBackFade;
uniform vec2 uTgProjZ;
uniform samplerCube uTgDepthA;
uniform float uTgFar;
void main() {
	vec3 d = normalize( vTgWorld - cameraPosition );
	vec3 c = vec3( 0.0 );
	float a = 0.0;
	if ( uTgW.x > 0.0 ) {
		vec4 s = tgSample( uTgPanoA, uTgPersp.x, uTgMatA, vec4( d, 0.0 ), d, uTgOffset.x );
		c += uTgW.x * s.a * s.rgb;
		a += uTgW.x * s.a;
	}
	if ( uTgW.y > 0.0 ) {
		vec4 s = tgSample( uTgPanoB, uTgPersp.y, uTgMatB, vec4( d, 0.0 ), d, uTgOffset.y );
		c += uTgW.y * s.a * s.rgb;
		a += uTgW.y * s.a;
	}
	gl_FragDepth = 1.0;
	if ( uTgPure > 0.5 ) {
		gl_FragColor = vec4( c / max( a, 1e-5 ), 1.0 );
		if ( uTgDepthOn > 0.5 ) {
			// distance along this ray to the first surface the sweep sees, pushed back a little so
			// markers lying on a floor or a wall pass the test
			float s = tgCubeDist( uTgDepthA, d );
			if ( s < 0.99 ) {
				s = s * uTgFar * 1.012 + 0.05;
				float z = s * dot( d, - vec3( viewMatrix[ 0 ][ 2 ], viewMatrix[ 1 ][ 2 ], viewMatrix[ 2 ][ 2 ] ) );
				gl_FragDepth = clamp( ( uTgProjZ.y - uTgProjZ.x * z ) / max( z, 1e-4 ) * 0.5 + 0.5, 0.0, 1.0 );
			}
		}
	} else {
		// Legacy projection: steeply up the backdrop is only seen through a skylight, where the
		// panoramas show the ceiling around their own skylight instead: use the sky there.
		float up = smoothstep( 0.45, 0.7, d.y ) * ( 1.0 - uTgSweep );
		vec3 col = mix( uTgSky, c / max( a, 1e-5 ), clamp( a, 0.0, 1.0 ) );
		col = mix( col, uTgSky * 1.08, up );
		gl_FragColor = vec4( mix( uTgBg, col, uTgBackFade ), 1.0 );
	}
	#include <colorspace_fragment>
}`,
    side: THREE.BackSide, depthTest: false, depthWrite: false,
  }));
  backdrop.frustumCulled = false;
  backdrop.renderOrder = -1e9;
  backdrop.visible = false;
  scene.add(backdrop);

  // Distance from a stop, packed into RGB, and the class code in A (RGBA8: renderable everywhere;
  // sampled with nearest filtering).
  const depthUniforms = { uCenter: { value: new THREE.Vector3() }, uFar: { value: PANO_DEPTH_FAR } };
  const depthMats = {};
  function depthMaterial(cls) {
    if (!depthMats[cls]) {
      depthMats[cls] = new THREE.ShaderMaterial({
        uniforms: { uCenter: depthUniforms.uCenter, uFar: depthUniforms.uFar, uCls: { value: (CLASS_CODE[cls] || 0) / 255 } },
        vertexShader: 'varying vec3 vW;\nvoid main() {\n\tvec4 w = modelMatrix * vec4( position, 1.0 );\n\tvW = w.xyz;\n\tgl_Position = projectionMatrix * viewMatrix * w;\n}',
        fragmentShader: '#include <packing>\nuniform vec3 uCenter;\nuniform float uFar;\nuniform float uCls;\nvarying vec3 vW;\nvoid main() {\n\tgl_FragColor = vec4( packDepthToRGB( clamp( length( vW - uCenter ) / uFar, 0.0, 0.999 ) ), uCls );\n}',
        side: THREE.DoubleSide, blending: THREE.NoBlending,
      });
    }
    return depthMats[cls];
  }
  // One scratch target with a depth buffer serves every cube face (rendered there, then copied texel
  // for texel), so a cube costs only its colour faces.
  let scratch = null;
  let cubeCams = null;
  const blitMat = new THREE.ShaderMaterial({
    uniforms: { uSrc: { value: null } },
    vertexShader: 'void main() {\n\tgl_Position = vec4( position.xy, 0.0, 1.0 );\n}',
    fragmentShader: 'uniform sampler2D uSrc;\nvoid main() {\n\tgl_FragColor = texelFetch( uSrc, ivec2( gl_FragCoord.xy ), 0 );\n}',
    depthTest: false, depthWrite: false, blending: THREE.NoBlending,
  });
  const blitScene = new THREE.Scene();
  {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
    const m = new THREE.Mesh(g, blitMat);
    m.frustumCulled = false;
    blitScene.add(m);
  }

  // Cut wall tops of the dollhouse / floor plan (built from a slice through the wall meshes).
  const capMat = prepareMaterial(new THREE.MeshBasicMaterial({ color: dollCap, side: THREE.DoubleSide }), proj, { shell: true });
  const capMesh = new THREE.Mesh(new THREE.BufferGeometry(), capMat);
  capMesh.frustumCulled = false;
  capMesh.visible = false;
  capMesh.userData.tg_class = 'cap';
  scene.add(capMesh);
  let capKey = '';

  const nextTask = () => new Promise((resolve) => setTimeout(resolve, 0));
  // the next animation frame, or 60 ms when frames are not running (hidden tab)
  const nextFrame = () => new Promise((resolve) => {
    let done = false;
    const go = () => { if (!done) { done = true; resolve(); } };
    setTimeout(go, 60);
    if (typeof requestAnimationFrame === 'function') requestAnimationFrame(go);
  });
  let prepass = opts.prepass !== false;
  let prepassSkip = ['glass', 'furniture', 'decor_high', 'landscape', 'exterior'];
  const prepassMat = new THREE.MeshBasicMaterial({ colorWrite: false, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 2 });

  const draco = new DRACOLoader();
  draco.setDecoderPath(new URL('../../vendor/three/examples/jsm/libs/draco/gltf/', import.meta.url).href);
  // the decoder (205 kB) comes while the model downloads, not after it
  if (opts.preloadDecoder !== false) { try { draco.preload(); } catch (err) { /* it is fetched when the model needs it */ } }
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
        prepareMaterial(mat, proj, { shell: true });
        glassMats.push(mat);
        o.renderOrder = 2;
      } else {
        const map = old && old.map ? old.map : null;
        if (map) { map.anisotropy = Math.min(8, maxAniso); map.colorSpace = THREE.SRGBColorSpace; }
        mat = new THREE.MeshBasicMaterial({ map, color: map ? 0xffffff : (old && old.color ? old.color : 0xdddddd) });
        const outdoor = cls === 'exterior' || cls === 'landscape';
        prepareMaterial(mat, proj, { shell: cls === 'wall', pano: true, outdoor, cap: cls === 'wall', tight: cls === 'base' }, outdoor ? adaptOut : adapt);
        // Ceilings fade during a fly-out (setClassOpacity): always in the transparent pass, so the
        // fade never recompiles a program. At opacity 1 that draws the same pixels.
        if (cls === 'ceiling') { mat.transparent = true; o.renderOrder = 1; }
      }
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
    root.updateMatrixWorld(true);
    for (const o of added) {
      if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
      o.userData.tg_box = new THREE.Box3().copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld);
    }
    parts += 1;
    footKey = '';
    capKey = '';
    applyVisibility(state);
    return added.length;
  }

  // Resolves with the number of meshes once the part is on the GPU: programs compiled, atlases and
  // vertex buffers uploaded in small steps (opts.warm = false skips that; the first frames that draw
  // the model then pay for it, several hundred milliseconds on an integrated GPU).
  function load(url, onProgress) {
    return new Promise((resolve, reject) => {
      loader.load(url, (g) => {
        const n = adopt(g);
        if (opts.warm === false) resolve(n);
        else warm().then(() => resolve(n), () => resolve(n));
      }, (e) => onProgress && e.total && onProgress(e.loaded / e.total), reject);
    });
  }

  // Draws every mesh once into a corner of the canvas (8 x 8 pixels, the screen's own framebuffer
  // state: a render target would compile other program variants), a few megapixels of atlas or a few
  // hundred thousand triangles per task.
  let warming = null;
  function warm() {
    if (warming) return warming;
    warming = (async () => {
      const meshes = [];
      root.traverse((o) => { if (o.isMesh && !o.userData.tg_warm) meshes.push(o); });
      if (renderer.compileAsync) await renderer.compileAsync(scene, camera);
      const cam = new THREE.PerspectiveCamera(60, 1, 0.5, 5000);
      cam.position.set(20, 60, 28);
      cam.lookAt(20, 0, 28.001);
      cam.updateMatrixWorld();
      const vp = new THREE.Vector4(), sc = new THREE.Vector4();
      const draw = (set, override) => {
        const saved = [];
        root.traverse((o) => { if (o.isMesh) { saved.push(o, o.visible, o.frustumCulled); o.visible = set.has(o); o.frustumCulled = false; } });
        const shown = [root.visible, backdrop.visible, capMesh.visible];
        root.visible = true; backdrop.visible = false; capMesh.visible = false;
        const target = renderer.getRenderTarget();
        const scissor = renderer.getScissorTest();
        renderer.getViewport(vp);
        renderer.getScissor(sc);
        renderer.setRenderTarget(null);
        renderer.setViewport(0, 0, 8, 8);
        renderer.setScissor(0, 0, 8, 8);
        renderer.setScissorTest(true);
        renderer.autoClear = false;
        renderer.clearDepth();
        scene.overrideMaterial = override || null;
        renderer.render(scene, cam);
        scene.overrideMaterial = null;
        renderer.autoClear = true;
        renderer.setScissorTest(scissor);
        renderer.setScissor(sc);
        renderer.setViewport(vp);
        renderer.setRenderTarget(target);
        [root.visible, backdrop.visible, capMesh.visible] = shown;
        for (let i = 0; i < saved.length; i += 3) { saved[i].visible = saved[i + 1]; saved[i].frustumCulled = saved[i + 2]; }
        touch();                   // the page redraws its frame over the corner
      };
      let batch = new Set();
      let cost = 0;
      for (const o of meshes) {
        const map = o.material.map;
        const g = o.geometry;
        batch.add(o);
        o.userData.tg_warm = true;
        cost += (map && map.image ? (map.image.width * map.image.height) / 3e6 : 0) + (g.index ? g.index.count : g.attributes.position.count) / 9e5;
        if (cost >= 1) {
          draw(batch);
          batch = new Set();
          cost = 0;
          await nextTask();
        }
      }
      if (batch.size) draw(batch);
      await nextTask();
      draw(new Set(meshes), prepassMat);
    })().finally(() => { warming = null; });
    return warming;
  }

  // ---- Modes and visibility ------------------------------------------------------------------

  const isDoll = (mode) => mode === 'dollhouse' || mode === 'floorplan';
  const isInside = (mode) => mode === 'walk' || mode === 'inside';
  const isLegacy = (mode) => !isDoll(mode) && mode !== 'inside';

  // rects: [[x0, z0, x1, z1], ...] in SCENE feet; their union is the outline of the house.
  function setFootprint(rects) {
    footprint = (Array.isArray(rects) ? rects : []).filter((r) => r && r.length === 4).slice(0, FOOT_MAX).map((r) => r.map(Number));
    proj.uTgFootN.value = footprint.length;
    footprint.forEach((r, i) => proj.uTgFoot.value[i].set(Math.min(r[0], r[2]), Math.min(r[1], r[3]), Math.max(r[0], r[2]), Math.max(r[1], r[3])));
    if (!interiorGiven && footprint.length) {
      const x0 = Math.min(...footprint.map((r) => r[0])), z0 = Math.min(...footprint.map((r) => r[1]));
      const x1 = Math.max(...footprint.map((r) => r[2])), z1 = Math.max(...footprint.map((r) => r[3]));
      boxInterior.set(x0 - 0.3, z0 - 0.3, x1 + 0.3, z1 + 0.3);
    }
    footKey = '';
    capKey = '';
    applyVisibility(state);
  }

  function inFoot(x, z, m = 0) {
    for (const r of footprint) if (x > r[0] - m && z > r[1] - m && x < r[2] + m && z < r[3] + m) return true;
    return false;
  }

  // Nodes entirely away from the house (the neighbours' garage doors are class 'wall').
  function tagOutside() {
    const key = `${parts}|${JSON.stringify(footprint)}`;
    if (key === footKey) return;
    footKey = key;
    for (const list of Object.values(byClass)) {
      for (const o of list) {
        const b = o.userData.tg_box;
        o.userData.tg_outside = !!(footprint.length && b) && !footprint.some((r) => b.max.x > r[0] - 1.5 && b.min.x < r[2] + 1.5 && b.max.z > r[1] - 1.5 && b.min.z < r[3] + 1.5);
      }
    }
  }

  // The walls have no top faces (culled at bake, they sat under the ceilings). Slice the wall meshes
  // a little below the cut and fill the outlines: one flat mesh that closes every cut wall.
  function buildCaps() {
    const key = `${parts}|${JSON.stringify(footprint)}|${dollClipY}`;
    if (key === capKey) return;
    capKey = key;
    const y = dollClipY - 0.0253;         // just under the wall tops: only full-height walls are cut
    const segs = [];
    const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
    const cut = (p, q, out) => {
      const t = (y - p.y) / (q.y - p.y);
      out.push(p.x + (q.x - p.x) * t, p.z + (q.z - p.z) * t);
    };
    for (const o of byClass.wall || []) {
      const box = o.userData.tg_box;
      if (o.userData.tg_outside || !box || box.min.y > y || box.max.y < y) continue;
      const pos = o.geometry.attributes.position;
      const idx = o.geometry.index;
      const n = idx ? idx.count : pos.count;
      for (let i = 0; i < n; i += 3) {
        a.fromBufferAttribute(pos, idx ? idx.getX(i) : i).applyMatrix4(o.matrixWorld);
        b.fromBufferAttribute(pos, idx ? idx.getX(i + 1) : i + 1).applyMatrix4(o.matrixWorld);
        c.fromBufferAttribute(pos, idx ? idx.getX(i + 2) : i + 2).applyMatrix4(o.matrixWorld);
        const sa = a.y > y, sb = b.y > y, sc = c.y > y;
        if (sa === sb && sb === sc) continue;
        const pts = [];
        if (sa !== sb) cut(a, b, pts);
        if (sb !== sc) cut(b, c, pts);
        if (sc !== sa) cut(c, a, pts);
        if (pts.length !== 4 || Math.abs(pts[1] - pts[3]) < 1e-5) continue;
        // outward normal of the face, x component: the solid lies on the other side
        const nx = (b.y - a.y) * (c.z - a.z) - (b.z - a.z) * (c.y - a.y);
        if (nx === 0) continue;
        const s = pts[1] < pts[3] ? [pts[0], pts[1], pts[2], pts[3]] : [pts[2], pts[3], pts[0], pts[1]];
        segs.push({ x0: s[0], z0: s[1], x1: s[2], z1: s[3], w: nx < 0 ? 1 : -1 });
      }
    }
    // Scan in z: between two consecutive endpoint rows no segment starts or ends, so the solid is a
    // set of trapezoids between the segments where the winding number is positive.
    const rows = [...new Set(segs.flatMap((s) => [Math.round(s.z0 * 1e4) / 1e4, Math.round(s.z1 * 1e4) / 1e4]))].sort((p, q) => p - q);
    segs.sort((p, q) => p.z0 - q.z0);
    const verts = [];
    const xAt = (s, z) => s.x0 + (s.x1 - s.x0) * Math.min(1, Math.max(0, (z - s.z0) / (s.z1 - s.z0)));
    let next = 0;
    let active = [];
    const yc = dollClipY - 0.02;
    for (let r = 0; r + 1 < rows.length; r++) {
      const z0 = rows[r], z1 = rows[r + 1], zm = (z0 + z1) / 2;
      if (z1 - z0 < 2e-4) continue;
      while (next < segs.length && segs[next].z0 < zm) active.push(segs[next++]);
      active = active.filter((s) => s.z1 > zm);
      const row = active.map((s) => ({ s, x: xAt(s, zm) })).sort((p, q) => p.x - q.x || q.s.w - p.s.w);
      let wind = 0;
      let start = null;
      for (const { s } of row) {
        const was = wind;
        wind += s.w;
        if (was <= 0 && wind > 0) start = s;
        else if (was > 0 && wind <= 0 && start) {
          const ax = xAt(start, z0), bx = xAt(s, z0), cx = xAt(s, z1), dx = xAt(start, z1);
          if (Math.max(bx - ax, cx - dx) > 1e-4 && (!footprint.length || inFoot((ax + bx + cx + dx) / 4, zm, 0.05))) {
            verts.push(ax, yc, z0, cx, yc, z1, bx, yc, z0, ax, yc, z0, dx, yc, z1, cx, yc, z1);
          }
          start = null;
        }
      }
    }
    capMesh.geometry.dispose();
    capMesh.geometry = new THREE.BufferGeometry();
    capMesh.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(verts), 3));
  }

  function classAlpha(cls) {
    const v = classOpacity[cls];
    return v === undefined ? 1 : v;
  }

  function applyVisibility(s) {
    state = Object.assign({}, state, s);
    const { mode, cut, furniture, garden } = state;
    const doll = isDoll(mode);
    const inside = isInside(mode);
    const legacy = isLegacy(mode);
    const cutaway = legacy && mode !== 'walk' && mode !== 'exterior' && cut;   // the 2.1 ft cutaway of 'top' / 'orbit'
    const show = {
      base: true,
      wall: true,
      glass: true,
      exterior: mode === 'exterior',
      ceiling: inside || doll,              // in the dollhouse only while setClassOpacity keeps it up
      furniture: furniture,
      decor_high: furniture && !cutaway,
      landscape: garden && !doll,
    };
    if (doll) tagOutside();
    for (const [cls, list] of Object.entries(byClass)) {
      const alpha = legacy ? 1 : classAlpha(cls);
      const v = (show[cls] !== undefined ? show[cls] : true) && alpha > 0.003;
      for (const o of list) {
        o.visible = v && !(doll && o.userData.tg_outside);
        if (cls === 'glass') continue;
        const m = o.material;
        const transparent = cls === 'ceiling' || alpha < 1;
        if (m.transparent !== transparent) { m.transparent = transparent; m.needsUpdate = true; }
        m.opacity = alpha;
      }
    }
    // The neighbourhood (landscape) has inside-out pieces (the neighbours' houses: Cycles renders both
    // sides, so the bake and the renders never minded). Outside, draw both sides so the drawn surface is
    // the one the exterior frames show; otherwise a frame lands on a house's far inner wall, fails the
    // depth test against the near one and drops to the bake.
    const side = mode === 'exterior' ? THREE.DoubleSide : THREE.FrontSide;
    for (const o of byClass.landscape || []) {
      if (o.material && o.material.side !== side) {
        o.material.side = side;
        o.material.needsUpdate = true;
      }
    }
    // Cut: per fragment (no clipping planes, so a mode change never recompiles a program). While the
    // ceilings are still up (start of a fly-out) the cut sits above the vaults and comes down with them.
    if (doll) {
      const up = Math.min(1, Math.max(0, classAlpha('ceiling')));
      proj.uTgClipY.value = dollClipY + (DOLL_CLIP_OPEN - dollClipY) * up * up * (3 - 2 * up);
      proj.uTgCapOn.value = 1;
      proj.uTgCapColor.value.copy(dollCap);
      proj.uTgCull.value = footprint.length ? 1 : 0;
      if (parts > 0) buildCaps();
    } else {
      proj.uTgClipY.value = cutaway ? CUT_Y : 1e9;
      proj.uTgCapOn.value = mode === 'inside' ? 0 : 1;
      proj.uTgCapColor.value.copy(CAP);
      proj.uTgCull.value = 0;
    }
    capMesh.visible = doll && parts > 0;
    // Depth cubes are rendered with their own fixed class sets (sweeps: the inside view; exterior
    // frames: the exterior view), whatever the mode: only these toggles and new parts make them stale.
    const key = `${furniture}|${garden}|${parts}`;
    if (key !== visKey) {
      visKey = key;
      for (const e of panos.values()) { e.depthReady = false; e.cpu = null; }
    }
    touch();
  }

  // 'inside' | 'dollhouse' | 'floorplan' | 'exterior' (the legacy names 'walk' | 'top' | 'orbit' go
  // through applyVisibility). Resets the fly-out controls to the mode's own state: inside = projection
  // fully on, ceilings opaque; dollhouse / floor plan = projection off, ceilings gone.
  function setMode(mode) {
    const doll = isDoll(mode);
    projFade = doll ? 0 : 1;
    for (const k of Object.keys(classOpacity)) delete classOpacity[k];
    if (doll) classOpacity.ceiling = 0;
    applyVisibility({ mode });
  }

  // 0..1 opacity of a class ('ceiling' is the one made for it: no recompile). Holds until setMode.
  function setClassOpacity(cls, value) {
    const v = Math.min(1, Math.max(0, Number(value)));
    if (classAlpha(cls) === v) return;
    classOpacity[cls] = v;
    applyVisibility(state);
  }

  // 0..1 strength of the sweep projection on the model and the backdrop (1 = panoramas, 0 = bake and
  // background colour). Holds until setMode.
  function setProjectionFade(value) {
    const v = Math.min(1, Math.max(0, Number(value)));
    if (v !== projFade) { projFade = v; touch(); }
  }

  // Clear colour; also what the backdrop fades to with setProjectionFade. Any THREE.Color input.
  function setBackground(color) {
    background.set(color);
    renderer.setClearColor(background, 1);
    touch();
  }

  // k = [r, g, b] gains (see prepareMaterial), or null for the bake as-is; ko the same for the outdoor
  // groups (defaults to k). Eased in render(); instant = true applies it at once (the dollhouse's
  // house-wide value: nothing to adapt to, and no tail of frames after a flight).
  function setAdaptation(k, ko, instant) {
    if (k && k.length === 3) adaptTarget.set(k[0], k[1], k[2]);
    else adaptTarget.set(1, 1, 1);
    if (ko && ko.length === 3) adaptOutTarget.set(ko[0], ko[1], ko[2]);
    else adaptOutTarget.copy(adaptTarget);
    // out of walk mode the outdoor groups are the view itself: back to the bake at once, not eased
    if (!(k && k.length === 3)) adaptOut.value.set(1, 1, 1);
    if (instant) { adapt.value.copy(adaptTarget); adaptOut.value.copy(adaptOutTarget); }
    touch();
  }

  function stepAdaptation() {
    const now = performance.now();
    const dt = (now - adaptClock) / 1000;
    adaptClock = now;
    if (dt > ADAPT_SNAP) {
      adapt.value.copy(adaptTarget);
      adaptOut.value.copy(adaptOutTarget);
    } else {
      adapt.value.lerp(adaptTarget, 1 - Math.exp(-dt / ADAPT_TAU));
      adaptOut.value.lerp(adaptOutTarget, 1 - Math.exp(-dt / ADAPT_TAU));
    }
    return adapt.value.distanceToSquared(adaptTarget) + adaptOut.value.distanceToSquared(adaptOutTarget) > 1e-8;
  }

  // ---- Panoramas -----------------------------------------------------------------------------

  // list: [{id, p: [x, y, z] (the eye, SCENE feet), offset?: radians}] - tour.json's sweeps as they are.
  // setPanorama(id, image, level) then needs no centre.
  function setSweeps(list) {
    for (const s of list || []) {
      if (!s || s.id === undefined || !s.p) continue;
      const p = new THREE.Vector3(s.p[0], s.p[1], s.p[2]);
      sweeps.set(s.id, { p, offset: Number.isFinite(s.offset) ? s.offset : 0 });
      const e = panos.get(s.id);
      if (e && !e.persp && e.center.distanceToSquared(p) > 1e-10) {
        e.center.copy(p);
        e.depthReady = false;
        e.cpu = null;
      }
    }
    touch();
  }

  function makeTexture(image, persp, rank) {
    const tex = new THREE.Texture(image);
    tex.flipY = false;
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = persp ? THREE.ClampToEdgeWrapping : THREE.RepeatWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.magFilter = THREE.LinearFilter;
    // 8K with mipmaps is 179 MB; without, 134 MB. At rest an 8K panorama is close to 1:1 on screen.
    const mips = rank < 3 || mipmap8k;
    tex.minFilter = mips ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
    tex.generateMipmaps = mips;
    tex.anisotropy = mips ? Math.min(persp ? 8 : 16, maxAniso) : 1;
    tex.userData.bytes = Math.round((image.width || 0) * (image.height || 0) * 4 * (mips ? 4 / 3 : 1));
    tex.userData.uploaded = false;
    tex.userData.dead = false;
    tex.userData.glTex = null;
    tex.onUpdate = () => {                 // uploaded: the decoded copy is no longer needed
      tex.onUpdate = null;
      tex.userData.uploaded = true;
      if (image.close) image.close();
    };
    tex.needsUpdate = true;
    return tex;
  }

  const sliceable = (image) => typeof ImageBitmap !== 'undefined' && image instanceof ImageBitmap && typeof createImageBitmap === 'function';

  // Uploads a panorama in horizontal slices over several frames instead of one texImage2D (a 4K
  // upload freezes an integrated GPU for ~50 ms, an 8K one for ~350 ms): storage first, then
  // SLICE_BYTES of texels per frame, then the mipmaps. The WebGL texture is handed to three.js as the
  // texture's own. Resolves 'done' (on the GPU), 'dead' (released meanwhile) or 'failed'.
  async function uploadSliced(tex) {
    if (tex.userData.uploaded) return 'done';
    const image = tex.image;
    if (!sliceable(image)) {
      renderer.initTexture(tex);
      return 'done';
    }
    const w = image.width, h = image.height;
    const mips = tex.generateMipmaps;
    const st = renderer.state;
    const glTex = gl.createTexture();
    tex.userData.glTex = glTex;             // releaseTexture deletes it
    const live = () => !tex.userData.dead && !tex.userData.uploaded && tex.userData.glTex === glTex;
    const drop = () => {
      if (tex.userData.glTex === glTex) { gl.deleteTexture(glTex); tex.userData.glTex = null; }
      return tex.userData.uploaded ? 'done' : tex.userData.dead ? 'dead' : 'failed';
    };
    try {
      st.bindTexture(gl.TEXTURE_2D, glTex);
      gl.texStorage2D(gl.TEXTURE_2D, mips ? Math.floor(Math.log2(Math.max(w, h))) + 1 : 1, gl.SRGB8_ALPHA8, w, h);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, tex.wrapS === THREE.RepeatWrapping ? gl.REPEAT : gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, mips ? gl.LINEAR_MIPMAP_LINEAR : gl.LINEAR);
      const aniso = renderer.extensions.get('EXT_texture_filter_anisotropic');
      if (aniso && tex.anisotropy > 1) gl.texParameterf(gl.TEXTURE_2D, aniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(tex.anisotropy, maxAniso));
      st.unbindTexture();
      const rows = Math.max(16, Math.min(h, Math.floor(SLICE_BYTES / (w * 4))));
      if (w * h * 4 > 4 * SLICE_BYTES) {     // allocating a large texture is a slice of work in itself
        await nextFrame();
        if (!live()) return drop();
      }
      let sent = 0;
      for (let y = 0; y < h; y += rows) {
        const n = Math.min(rows, h - y);
        // (A slice is cropped into a bitmap of its own first. Uploading a sub-rectangle of the whole
        // bitmap with UNPACK_SKIP_ROWS saves that copy for a bitmap decoded from a file, but takes
        // 130 to 200 ms a slice for one that comes from a canvas: tools/web/dev, section `levels`.)
        const part = await createImageBitmap(image, 0, y, w, n);
        if (!live()) { part.close(); return drop(); }
        st.bindTexture(gl.TEXTURE_2D, glTex);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
        gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
        gl.pixelStorei(gl.UNPACK_ALIGNMENT, 4);
        gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, y, gl.RGBA, gl.UNSIGNED_BYTE, part);
        st.unbindTexture();
        part.close();
        sent += w * n * 4;
        if (sent >= SLICE_BYTES && y + rows < h) {
          sent = 0;
          await nextFrame();
          if (!live()) return drop();
        }
      }
      if (mips) {
        await nextFrame();
        if (!live()) return drop();
        st.bindTexture(gl.TEXTURE_2D, glTex);
        gl.generateMipmap(gl.TEXTURE_2D);
        st.unbindTexture();
      }
      // three.js binds a texture whose version it already "uploaded" without touching it
      const props = renderer.properties.get(tex);
      props.__webglTexture = glTex;
      props.__webglInit = true;
      props.__version = tex.version;
      tex.onUpdate = null;
      tex.userData.uploaded = true;
      if (image.close) image.close();
      return 'done';
    } catch (err) {
      return drop();
    }
  }

  // Two forms.
  //   setPanorama(id, image, level, {center, offset, instant, frame}?)  level '2k' | '4k' | '8k' (or a
  //     width in pixels, or omitted = from the image); centre and offset default to setSweeps'.
  //   setPanorama(id, image, center, offset = 0, full = false, instant = false, frame = null)  (legacy;
  //     `full` may also be a level name).
  // image: ImageBitmap / HTMLImageElement of an equirectangular panorama (sRGB, top row = up).
  // center: the stop's eye point in SCENE feet; offset: the manifest's yaw offset (radians).
  // A lower level arriving for an id that already holds (or is taking in) a higher one is ignored.
  // A higher level for a panorama that is already on the GPU is an upgrade: the one on screen stays
  // while the new one is uploaded in slices, then they swap (hasPanorama reports `pending` meanwhile).
  // instant: skip the fade-in of the legacy projection.
  // frame: for a perspective render instead of a panorama, {matrix}: its camera's projection x view
  // (column-major, SCENE feet -> clip, the app's mul(perspective, lookAt)); center is then its eye.
  // Returns true when the image was taken.
  function setPanorama(id, image, a, b, c, d, f) {
    let center, offset, level, instant, frame;
    if (Array.isArray(a) || ArrayBuffer.isView(a)) {
      center = a; offset = b || 0; level = c === undefined ? false : c; instant = !!d; frame = f || null;
    } else {
      const o = b && typeof b === 'object' ? b : {};
      const s = sweeps.get(id);
      level = a;
      center = o.center || (s && s.p.toArray());
      offset = Number.isFinite(o.offset) ? o.offset : s ? s.offset : 0;
      instant = !!o.instant;
      frame = o.frame || null;
    }
    const fail = (msg) => {
      if (image && image.close) image.close();
      if (msg) throw new Error(msg);
      return false;
    };
    if (!center) return fail(`setPanorama: unknown sweep "${id}" (call setSweeps first or pass a centre)`);
    const name = levelName(level, image);
    const rank = LEVEL_RANK[name];
    if (image.width > caps.maxTextureSize || image.height > caps.maxTextureSize) return fail();
    let e = panos.get(id);
    if (e && Math.max(e.rank, e.next ? e.next.fields.rank : 0) > rank) return fail();
    const persp = frame && frame.matrix ? new THREE.Matrix4().fromArray(frame.matrix) : null;
    const tex = makeTexture(image, persp, rank);
    const now = performance.now();
    const fields = { tex, level: name, rank, full: rank >= 2, offset, persp, width: image.width, height: image.height };
    if (e) {
      if (e.next) { releaseTexture(e.next.fields.tex); e.next = null; }
      if (e.tex.userData.uploaded && sliceable(image)) {
        const next = { fields, job: null };
        e.next = next;
        lastSet = id;
        trimPanoramas();                     // room for the new level first: it counts toward its cap from here on
        next.job = uploadSliced(tex).then((state) => {
          if (e.next !== next || panos.get(id) !== e) return false;
          e.next = null;
          if (state === 'dead') return false;
          // 'failed': swap anyway, three.js uploads it whole. On the sweep the camera rests on the new
          // level fades in over the old one (updateSweep), which lives that much longer.
          dropPrev(e);
          if (restEntry === e && e.tex.userData.uploaded) e.prev = { tex: e.tex, t0: 0 };
          else releaseTexture(e.tex);
          Object.assign(e, fields);
          touch();
          trimPanoramas();
          return true;
        });
      } else {
        releaseTexture(e.tex);
        Object.assign(e, fields);
      }
      if (instant) e.born = now - PANO_FADE * 1000;
    } else {
      e = Object.assign({
        id, center: new THREE.Vector3(center[0], center[1], center[2]), next: null, prev: null,
        cube: null, depthReady: false, depthFar: PANO_DEPTH_FAR, cpu: null, cpuJob: null, preparing: null,
        born: instant ? now - PANO_FADE * 1000 : now, used: now,
      }, fields);
      panos.set(id, e);
    }
    lastSet = id;
    trimPanoramas();
    touch();
    return true;
  }

  // The level that is being taken in for a sweep is no longer needed (the visitor has left it): the
  // upload stops and its memory is freed; the level on screen stays. True when there was one.
  function dropUpgrade(id) {
    const e = panos.get(id);
    if (!e || !e.next) return false;
    releaseTexture(e.next.fields.tex);
    e.next = null;
    return true;
  }
  // The level a sharper one is fading in over.
  function dropPrev(e) {
    if (!e.prev) return;
    releaseTexture(e.prev.tex);
    e.prev = null;
    touch();
  }

  // ids the page still needs although they are not on screen (the route of a move through several
  // sweeps, the sweep under the cursor): evicted last. Keep it short. Shared with setProjection's list.
  function setWanted(ids) {
    projWanted = new Set(Array.isArray(ids) ? ids : []);
  }

  // A texture that was never drawn still holds its decoded image (onUpdate closes it on upload).
  function releaseTexture(tex) {
    tex.userData.dead = true;
    if (tex.onUpdate && tex.image && tex.image.close) tex.image.close();
    tex.onUpdate = null;
    if (tex.userData.glTex) {              // uploaded (or being uploaded) in slices: ours to delete
      gl.deleteTexture(tex.userData.glTex);
      tex.userData.glTex = null;
    }
    tex.dispose();
  }

  // hasPanorama(id) -> null, or {level, full, depth, uploaded, pending, shown, width}: level / full /
  //   width of the best image taken; pending = an upgrade is still uploading and `shown` (the level on
  //   screen) is lower; uploaded = on the GPU; depth = the depth cube is rendered.
  // hasPanorama(id, level) -> true when the panorama held (or being taken in) is at least that level.
  function hasPanorama(id, level) {
    const e = panos.get(id);
    if (!e) return level !== undefined ? false : null;
    const best = e.next ? e.next.fields : e;
    if (level !== undefined) return best.rank >= (LEVEL_RANK[levelName(level, null)] || 1);
    return {
      level: best.level, full: best.rank >= 2, depth: e.depthReady && !!e.cube && e.cube.owner === e,
      uploaded: e.tex.userData.uploaded && !e.next, pending: !!e.next, shown: e.level, width: best.width,
    };
  }

  // targets: [{id, weight}] (weights summing to 1; the nearest stops the camera can see), or null.
  // wanted: ids the page is loading for the route ahead; they are never evicted (keep it short).
  // Legacy, eased projection; used by the exterior orbit. Sweeps use setSweepBlend.
  function setProjection(targets, wanted) {
    projTargets = Array.isArray(targets) ? targets.filter((t) => t && t.weight > 0) : [];
    projWanted = new Set(Array.isArray(wanted) ? wanted : []);
    touch();
  }

  // The deterministic projection of the tour: panorama idA, cross-faded to idB by t (0..1). No easing,
  // no fade-in: the page owns the clock. t = 0 with idB = null is the rest state; with the camera on
  // the sweep the frame is then the pure panorama. setSweepBlend(null) turns it off.
  function setSweepBlend(idA, idB = null, t = 0) {
    const a = idA === undefined ? null : idA;
    const b = a === null || idB === undefined ? null : idB;
    const v = b === null ? 0 : Math.min(1, Math.max(0, Number(t) || 0));
    if (a === blend.a && b === blend.b && v === blend.t) return;
    blend.a = a; blend.b = b; blend.t = v;
    touch();
  }

  function dropPanorama(e) {
    if (e.next) { releaseTexture(e.next.fields.tex); e.next = null; }
    dropPrev(e);
    releaseTexture(e.tex);
    if (e.cube && e.cube.owner === e) e.cube.owner = null;
    e.cpu = null;
    panos.delete(e.id);
    projWeights.delete(e.id);
    if (lastSet === e.id) lastSet = null;
  }

  // Evict least recently used panoramas beyond the budget: at most max8k / max4k / max2k per level,
  // cacheSize entries and maxBytes in all. A level that is still being taken in counts as well as
  // the one on screen, so room is made before its texture is allocated, not after the swap. Never the
  // resting or transition sweeps, a frame on screen one being prepared or the one set last. `wanted`
  // ids (setWanted, setProjection) go last, and only for a level cap (8k, 4k) or the byte budget. With
  // everything protected the caps are exceeded for a while rather than a needed panorama dropped.
  function trimPanoramas() {
    for (const e of panos.values()) if (e.prev && e !== restEntry) dropPrev(e);     // a fade nobody is looking at
    const hard = new Set(projTargets.map((t) => t.id));
    for (const [id, w] of projWeights) if (w > 0) hard.add(id);
    if (blend.a !== null) hard.add(blend.a);
    if (blend.b !== null) hard.add(blend.b);
    for (const e of panos.values()) if (e.preparing) hard.add(e.id);
    if (lastSet !== null) hard.add(lastSet);      // a panorama is never the victim of its own arrival
    const lru = (pred) => [...panos.values()].filter((e) => !hard.has(e.id) && pred(e)).sort((p, q) => p.used - q.used);
    const holds = (e, rank) => e.rank === rank || (!!e.next && e.next.fields.rank === rank);
    const count = (rank) => { let n = 0; for (const e of panos.values()) if (holds(e, rank)) n += 1; return n; };
    const cap = [0, budget.max2k, budget.max4k, budget.max8k];
    for (const rank of [3, 2, 1]) {
      for (const wanted of [false, true]) {
        if (wanted && rank === 1) continue;
        for (const e of lru((x) => holds(x, rank) && projWanted.has(x.id) === wanted)) {
          if (count(rank) <= cap[rank]) break;
          dropPanorama(e);
        }
      }
    }
    for (const e of lru((x) => !projWanted.has(x.id))) {
      if (panos.size <= cacheSize && panoBytes() <= budget.maxBytes) return;
      dropPanorama(e);
    }
    for (const e of lru(() => true)) {
      if (panoBytes() <= budget.maxBytes) return;
      dropPanorama(e);
    }
  }

  function panoBytes() {
    let n = 0;
    for (const e of panos.values()) n += e.tex.userData.bytes + (e.next ? e.next.fields.tex.userData.bytes : 0) + (e.prev ? e.prev.tex.userData.bytes : 0);
    return n;
  }

  // Depth cubes come from a small pool; a stop that loses its cube simply renders it again when it
  // is next needed.
  function cubeFor(e, busy) {
    if (e.cube && e.cube.owner === e) return e.cube;
    let c = cubes.find((x) => !x.owner);
    if (!c && cubes.length < depthPool) {
      c = {
        rt: new THREE.WebGLCubeRenderTarget(depthSize, {
          type: THREE.UnsignedByteType, format: THREE.RGBAFormat, generateMipmaps: false, depthBuffer: false,
          minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
        }),
        owner: null,
      };
      cubes.push(c);
    }
    if (!c) c = cubes.filter((x) => !busy.has(x.owner)).sort((p, q) => p.owner.used - q.owner.used)[0];
    if (c.owner) { c.owner.cube = null; c.owner.depthReady = false; }
    c.owner = e;
    e.cube = c;
    e.depthReady = false;
    return c;
  }

  // Sweeps see the inside view (ceilings, no roof), exterior frames the outside view (roof, no
  // ceilings), whatever the current mode. Glass never occludes.
  function depthShows(cls, exterior) {
    if (cls === 'glass') return false;
    if (cls === 'exterior') return exterior;
    if (cls === 'ceiling') return !exterior;
    if (cls === 'furniture' || cls === 'decor_high') return state.furniture;
    if (cls === 'landscape') return state.garden;
    return true;
  }

  function renderDepth(e, busy) {
    const c = cubeFor(e, busy);
    if (e.depthReady) return;
    const exterior = !!e.persp;
    const far = exterior ? PANO_DEPTH_FAR_EXTERIOR : PANO_DEPTH_FAR;
    if (!scratch) {
      scratch = new THREE.WebGLRenderTarget(depthSize, depthSize, {
        type: THREE.UnsignedByteType, format: THREE.RGBAFormat, generateMipmaps: false, depthBuffer: true,
        minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
      });
      blitMat.uniforms.uSrc.value = scratch.texture;
      const cc = new THREE.CubeCamera(0.05, far, c.rt);    // only for its six cameras, in three's cube layout
      cc.coordinateSystem = renderer.coordinateSystem;
      cc.updateCoordinateSystem();
      cubeCams = cc;
    }
    for (const cam of cubeCams.children) {
      if (cam.far !== far) { cam.far = far; cam.updateProjectionMatrix(); }
    }
    cubeCams.position.copy(e.center);
    cubeCams.updateMatrixWorld(true);
    const saved = [];
    for (const [cls, list] of Object.entries(byClass)) {
      const v = depthShows(cls, exterior);
      const m = v ? depthMaterial(cls) : null;
      for (const o of list) {
        saved.push(o, o.visible, o.material);
        o.visible = v;
        if (v) o.material = m;
      }
    }
    const rootShown = root.visible, backdropShown = backdrop.visible, capShown = capMesh.visible;
    root.visible = true;
    backdrop.visible = false;
    capMesh.visible = false;
    depthUniforms.uCenter.value.copy(e.center);
    depthUniforms.uFar.value = far;
    renderer.getClearColor(clearTmp);
    const clearAlpha = renderer.getClearAlpha();
    const target = renderer.getRenderTarget();
    const autoClear = renderer.autoClear;
    renderer.autoClear = true;
    renderer.setClearColor(0xffffff, 1);   // cleared texels unpack to "far": visible; class 255
    for (let i = 0; i < 6; i++) {
      renderer.setRenderTarget(scratch);
      renderer.render(scene, cubeCams.children[i]);
      renderer.setRenderTarget(c.rt, i);
      renderer.render(blitScene, cubeCams.children[i]);
    }
    renderer.setRenderTarget(target);
    renderer.autoClear = autoClear;
    renderer.setClearColor(clearTmp, clearAlpha);
    for (let i = 0; i < saved.length; i += 3) {
      saved[i].visible = saved[i + 1];
      saved[i].material = saved[i + 2];
    }
    root.visible = rootShown;
    backdrop.visible = backdropShown;
    capMesh.visible = capShown;
    e.depthReady = true;
    e.depthFar = far;
    e.cpu = null;
    e.cpuJob = null;
  }

  function ensureDepth(e, busy) {
    if (!e.depthReady || !e.cube || e.cube.owner !== e) renderDepth(e, busy);
  }

  function busySet() {
    const s = new Set();
    for (const id of [blend.a, blend.b]) if (id !== null && panos.has(id)) s.add(panos.get(id));
    return s;
  }

  // CPU copy of a sweep's depth cube for pick(): read back once, asynchronously (pixel buffer objects).
  function readDepth(e) {
    if (e.cpu) return Promise.resolve(true);
    if (e.cpuJob) return e.cpuJob;
    if (!e.depthReady || !e.cube || e.cube.owner !== e) return Promise.resolve(false);
    const n = depthSize;
    const rt = e.cube.rt;
    const faces = [];
    const jobs = [];
    try {
      for (let i = 0; i < 6; i++) {
        const buf = new Uint8Array(n * n * 4);
        faces.push(buf);
        jobs.push(renderer.readRenderTargetPixelsAsync(rt, 0, 0, n, n, buf, i));
        gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);     // three leaves its buffer bound while it waits
      }
    } catch (err) {
      return Promise.resolve(false);
    }
    const far = e.depthFar;
    const job = Promise.all(jobs).then(() => {
      if (e.cpuJob !== job) return false;              // the cube was rendered again meanwhile
      e.cpuJob = null;
      e.cpu = { n, far, faces };
      // keep the copies of the most recent sweeps only (24 MB each at 1024)
      const held = [...panos.values()].filter((x) => x.cpu && x.id !== blend.a && x.id !== blend.b && x !== e).sort((p, q) => q.used - p.used);
      const fixed = [...panos.values()].filter((x) => x.cpu && (x.id === blend.a || x.id === blend.b || x === e)).length;
      held.slice(Math.max(0, pickCopies - fixed)).forEach((x) => { x.cpu = null; });
      return true;
    }, () => { if (e.cpuJob === job) e.cpuJob = null; return false; });
    e.cpuJob = job;
    return job;
  }

  // Everything a move to sweep `id` needs, ahead of time and outside the animation: the texture on the
  // GPU (with its mipmaps), the depth cube, and the CPU copy for pick(). Resolves true when ready,
  // false when the panorama is not there (call setPanorama first), below `level`, or evicted meanwhile.
  // o.pick === false leaves the CPU copy out (a neighbour prepared ahead of a possible move: the copy
  // is 6 faces of read-back that only the sweep the camera rests on needs, and that one reads its own).
  function prepare(id, level, o = {}) {
    const e = panos.get(id);
    if (!e || (level !== undefined && level !== null && !hasPanorama(id, level))) return Promise.resolve(false);
    if (e.preparing) return e.preparing;
    e.used = performance.now();
    const job = (async () => {
      await nextTask();
      for (let i = 0; i < 4 && panos.get(id) === e && (e.next || !e.tex.userData.uploaded); i++) {
        if (e.next) await e.next.job;                       // an upgrade on its way: wait for the swap
        else if ((await uploadSliced(e.tex)) === 'failed' && panos.get(id) === e && !e.tex.userData.uploaded) renderer.initTexture(e.tex);
      }
      await nextTask();
      if (panos.get(id) !== e) return false;
      if (parts > 0) {
        const busy = busySet();
        busy.add(e);
        ensureDepth(e, busy);
        if (o.pick !== false) await readDepth(e);
      }
      return panos.get(id) === e;
    })().then((ok) => { e.preparing = null; return ok; }, (err) => { e.preparing = null; throw err; });
    e.preparing = job;
    return job;
  }

  function projGroup(mode) {
    return isInside(mode) || mode === 'exterior' ? (mode === 'exterior' ? 'exterior' : 'walk') : 'other';
  }

  function smooth(a, b, x) {
    const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
    return t * t * (3 - 2 * t);
  }

  function setSlots(slots, w, occ, cam) {
    proj.uTgW.value.set(w[0], w[1]);
    proj.uTgOcc.value.set(occ[0], occ[1]);
    proj.uTgOffset.value.set(slots[0] ? slots[0].offset : 0, slots[1] ? slots[1].offset : 0);
    proj.uTgPersp.value.set(slots[0] && slots[0].persp ? 1 : 0, slots[1] && slots[1].persp ? 1 : 0);
    if (slots[0] && slots[0].persp) proj.uTgMatA.value.copy(slots[0].persp);
    if (slots[1] && slots[1].persp) proj.uTgMatB.value.copy(slots[1].persp);
    proj.uTgCenterA.value.copy(slots[0] ? slots[0].center : cam.position);
    proj.uTgCenterB.value.copy(slots[1] ? slots[1].center : cam.position);
    proj.uTgPanoA.value = slots[0] ? slots[0].tex : null;
    proj.uTgPanoB.value = slots[1] ? slots[1].tex : null;
    proj.uTgDepthA.value = slots[0] && slots[0].cube ? slots[0].cube.rt.texture : null;
    proj.uTgDepthB.value = slots[1] && slots[1].cube ? slots[1].cube.rt.texture : null;
  }

  function setBackdrop(on, pure, cam) {
    const m = backdrop.material;
    backdrop.visible = on;
    backdropUniforms.uTgPure.value = pure ? 1 : 0;
    m.depthTest = pure;
    m.depthWrite = pure;
    m.depthFunc = pure ? THREE.AlwaysDepth : THREE.LessEqualDepth;
    backdrop.position.copy(cam.position);
    backdrop.updateMatrixWorld();
    const p = cam.projectionMatrix.elements;
    backdropUniforms.uTgProjZ.value.set(p[10], p[14]);
  }

  // The sweep projection: weights straight from setSweepBlend.
  function updateSweep(cam, now) {
    const mode = state.mode;
    const doll = isDoll(mode);
    const A = panos.get(blend.a) || null;
    const B = blend.b !== null ? panos.get(blend.b) || null : null;
    const first = A || B;
    restEntry = null;
    proj.uTgSweep.value = 1;
    proj.uTgFade.value = projFade;
    proj.uTgFallback.value = doll ? 0 : 1;
    proj.uTgBox.value.copy(boxInterior);
    proj.uTgFar.value = PANO_DEPTH_FAR;
    const on = !!first && projFade > 0.001;
    if (!on) {
      proj.uTgOn.value = 0;
      setSlots([], [0, 0], [0, 0], cam);
      setBackdrop(false, false, cam);
      root.visible = true;
      for (const m of glassMats) m.opacity = GLASS_OPACITY;
      projInfo = { on: false, sweep: true, pure: false, fade: projFade, slots: [] };
      return false;
    }
    // t only counts when both panoramas are there; a missing one leaves the other at full weight.
    const t = A && B ? blend.t : A ? 0 : 1;
    const persp = cam.isPerspectiveCamera;
    const dA = A ? cam.position.distanceTo(A.center) : Infinity;
    const dB = B ? cam.position.distanceTo(B.center) : Infinity;
    const restOn = persp && !doll && projFade >= 0.999 && !debugNoRest ? (t <= 0.001 && dA < REST_EPS ? A : t >= 0.999 && dB < REST_EPS ? B : null) : null;
    const busy = busySet();
    if (restOn) {
      // Pure panorama: the backdrop alone, depth from the sweep's cube for the overlay.
      restOn.used = now;
      if (parts > 0) {
        ensureDepth(restOn, busy);
        if (!restOn.cpu && !restOn.cpuJob) readDepth(restOn);
      }
      proj.uTgOn.value = 1;
      // A sharper level that has just arrived fades in over the one that was on screen: the same
      // panorama twice, so the frame stays this sweep's panorama all the way.
      let mix = 1;
      const old = restOn.prev;
      if (old) {
        if (!old.t0) old.t0 = now;
        const k = (now - old.t0) / LEVEL_FADE;
        if (k >= 1) dropPrev(restOn);
        else mix = k * k * (3 - 2 * k);
      }
      if (restOn.prev) setSlots([restOn, { tex: old.tex, offset: restOn.offset, persp: null, center: restOn.center, cube: null }], [mix, 1 - mix], [0, 0], cam);
      else setSlots([restOn], [1, 0], [0, 0], cam);
      backdropUniforms.uTgDepthOn.value = parts > 0 ? 1 : 0;
      setBackdrop(true, true, cam);
      root.visible = false;
      restEntry = restOn;
      projInfo = { on: true, sweep: true, pure: true, fade: 1, levelFade: restOn.prev ? mix : 1, slots: [{ id: restOn.id, weight: 1, occlusion: 0, full: restOn.full, level: restOn.level }] };
      return !!restOn.prev;
    }
    const slots = [A, B].filter(Boolean);
    for (const e of slots) dropPrev(e);                 // a move does not wait for a level fade
    const w = A && B ? [1 - t, t] : [1, 0];
    const occ = [0, 0];
    slots.forEach((e, i) => {
      e.used = now;
      occ[i] = smooth(PANO_OCCLUSION[0], PANO_OCCLUSION[1], cam.position.distanceTo(e.center));
      if (parts > 0 && (occ[i] > 0 || !e.cube)) ensureDepth(e, busy);
    });
    proj.uTgOn.value = 1;
    setSlots(slots, w, occ, cam);
    // Flying out to the dollhouse the backdrop (the panorama at infinity) only makes sense from within
    // the room: it is gone by the time the camera is through the ceiling.
    backdropUniforms.uTgBackFade.value = doll ? projFade * (1 - smooth(1.0, 5.0, Math.min(dA, dB))) : projFade;
    setBackdrop(persp, false, cam);
    root.visible = true;
    for (const m of glassMats) m.opacity = GLASS_OPACITY * (1 - projFade);   // the panoramas already show the glass
    projInfo = {
      on: true, sweep: true, pure: false, fade: projFade,
      slots: slots.map((e, i) => ({ id: e.id, weight: Math.round(w[i] * 1000) / 1000, occlusion: Math.round(occ[i] * 1000) / 1000, full: e.full, level: e.level })),
    };
    return false;
  }

  function updateProjection(cam) {
    const now = performance.now();
    const dt = (now - projClock) / 1000;
    projClock = now;
    backdropUniforms.uTgSky.value = CLEAR;
    if (state.mode !== 'exterior' && blend.a !== null) {
      projWeights.clear();
      const fading = updateSweep(cam, now);            // a level fading in: the next frame differs too
      trimPanoramas();
      return fading;
    }
    restEntry = null;
    root.visible = true;
    proj.uTgSweep.value = 0;
    proj.uTgFade.value = 1;
    proj.uTgFallback.value = 0;
    const group = projGroup(state.mode);
    const walk = group !== 'other';       // the walk, or the exterior orbit
    if (group !== projMode) {             // the other mode's panoramas never blend in
      projMode = group;
      projWeights.clear();
    }
    proj.uTgBox.value.copy(group === 'exterior' ? boxAll : boxInterior);
    proj.uTgFar.value = group === 'exterior' ? PANO_DEPTH_FAR_EXTERIOR : PANO_DEPTH_FAR;
    const target = new Map(walk ? projTargets.map((t) => [t.id, t.weight]) : []);
    // Ease the blend weights so a stop coming into view (through a doorway) never pops.
    const k = dt > ADAPT_SNAP ? 1 : 1 - Math.exp(-dt / PANO_TAU);
    let moving = false;
    for (const id of new Set([...projWeights.keys(), ...target.keys()])) {
      const was = projWeights.get(id) || 0;
      const w = was + ((target.get(id) || 0) - was) * k;
      if (Math.abs(w - (target.get(id) || 0)) > 5e-4) moving = true;
      if (w < 0.002 && !target.has(id)) projWeights.delete(id);
      else projWeights.set(id, w);
    }
    // The two heaviest stops whose panorama is on the GPU.
    const slots = [];
    for (const [id, w] of [...projWeights].sort((a, b) => b[1] - a[1])) {
      const e = panos.get(id);
      if (!e || slots.length === 2) continue;
      e.used = now;
      const fade = Math.min(1, (now - e.born) / (PANO_FADE * 1000));
      if (fade < 1) moving = true;
      slots.push({ e, w, fade });
    }
    const busy = new Set(slots.map((x) => x.e));
    if (parts > 0) for (const x of slots) ensureDepth(x.e, busy);
    const raw = slots.reduce((s, x) => s + x.w * x.fade, 0);
    const strength = Math.min(1, slots.reduce((s, x) => s + x.fade, 0));
    const on = walk && raw > 1e-4;
    proj.uTgOn.value = on ? 1 : 0;
    const w = [0, 0];
    const occ = [0, 0];
    slots.forEach((x, i) => {
      w[i] = on ? (x.w * x.fade / raw) * strength : 0;
      occ[i] = smooth(PANO_OCCLUSION[0], PANO_OCCLUSION[1], cam.position.distanceTo(x.e.center));
    });
    setSlots(slots.map((x) => x.e), w, occ, cam);
    const total = on ? w[0] + w[1] : 0;
    for (const m of glassMats) m.opacity = GLASS_OPACITY * (1 - total);   // the panoramas already show the glass
    backdropUniforms.uTgBackFade.value = 1;
    setBackdrop(on && cam.isPerspectiveCamera, false, cam);
    projInfo = {
      on,
      slots: slots.map((x, i) => ({ id: x.e.id, weight: Math.round(w[i] * 1000) / 1000, occlusion: Math.round(occ[i] * 1000) / 1000, full: x.e.full })),
    };
    trimPanoramas();
    return moving;
  }

  // ---- Rendering -----------------------------------------------------------------------------

  const upTmp = new THREE.Vector3();
  const dirTmp = new THREE.Vector3();

  // render(view) draws one frame.
  //   view = { eye: [x, y, z], aim: [x, y, z], up?: [x, y, z], fovY (radians), near?, far?,
  //            width?, height?, pixelRatio? }                       perspective
  //        | { ortho: { halfHeight }, eye, aim, up?, near?, far?, width?, height?, pixelRatio? }
  //   eye / aim / halfHeight in SCENE feet; up defaults to +y (to -z, north up, when looking straight
  //   down or up); near / far default to 0.08 / 400 inside and 0.5 / 1200 elsewhere; width / height are
  //   drawing-buffer pixels and default to the canvas' own size.
  // render(eye, aim, fovY, width, height, pixelRatio) is the legacy form (the exterior orbit).
  function render(a, aim, fovY, width, height, pixelRatio) {
    const view = Array.isArray(a) || ArrayBuffer.isView(a)
      ? { eye: a, aim, fovY, width, height, pixelRatio: pixelRatio || 1, legacy: true }
      : a;
    renderer.info.reset();
    const easing = stepAdaptation();
    const w = Math.max(1, Math.round(view.width || canvas.width));
    const h = Math.max(1, Math.round(view.height || canvas.height));
    const pr = view.pixelRatio || 1;
    const key = `${w}x${h}@${pr}`;
    if (view.legacy || key !== sizeKey || canvas.width !== Math.floor(w * pr) || canvas.height !== Math.floor(h * pr)) {
      sizeKey = key;
      renderer.setPixelRatio(pr);
      renderer.setSize(w, h, false);
    }
    const inside = isInside(state.mode);
    const near = Number.isFinite(view.near) ? view.near : inside ? 0.08 : 0.5;
    const far = Number.isFinite(view.far) ? view.far : inside ? 400 : 1200;
    let cam;
    if (view.ortho) {
      cam = orthoCamera;
      const hh = view.ortho.halfHeight;
      cam.top = hh; cam.bottom = -hh; cam.right = hh * w / h; cam.left = -cam.right;
    } else {
      cam = camera;
      cam.fov = view.fovY * 180 / Math.PI;
      cam.aspect = w / h;
    }
    cam.near = near;
    cam.far = far;
    cam.updateProjectionMatrix();
    toVec3(view.eye, cam.position);
    toVec3(view.aim, dirTmp);
    if (view.up) toVec3(view.up, upTmp);
    else {
      upTmp.set(0, 1, 0);
      const dx = dirTmp.x - cam.position.x, dy = dirTmp.y - cam.position.y, dz = dirTmp.z - cam.position.z;
      if (dx * dx + dz * dz < 1e-8 * dy * dy) upTmp.set(0, 0, -1);
    }
    cam.up.copy(upTmp);
    cam.lookAt(dirTmp);
    cam.updateMatrixWorld();
    activeCam = cam;
    const moving = updateProjection(cam);
    if (prepass && projInfo.sweep && projInfo.on && !projInfo.pure && state.mode === 'inside' && classAlpha('ceiling') >= 1) {
      // A move shades every fragment with two panoramas and ten depth taps: lay the depth of the
      // architecture down first (floors, walls, ceilings: 200 k triangles, front faces only, a hair
      // behind), so what they hide is never shaded.
      const hidden = [];
      for (const cls of prepassSkip) for (const o of byClass[cls] || []) if (o.visible) { o.visible = false; hidden.push(o); }
      backdrop.visible = false;
      scene.overrideMaterial = prepassMat;
      renderer.render(scene, cam);
      scene.overrideMaterial = null;
      backdrop.visible = true;
      for (const o of hidden) o.visible = true;
      renderer.autoClear = false;
      renderer.render(scene, cam);
      renderer.autoClear = true;
    } else {
      renderer.render(scene, cam);
    }
    if (overlay.visible && overlay.children.length) {
      renderer.autoClear = false;
      renderer.render(overlayScene, cam);
      renderer.autoClear = true;
    }
    dirtyFlag = false;
    animating = easing || moving;
    return true;
  }

  // True when the next frame would differ although the page changed nothing itself: a panorama or the
  // model arrived, a mode / blend / fade / background call was made, invalidate() was called, or an
  // easing (adaptation, legacy projection weights) is still running. The camera is the page's business:
  // render when the view changed or dirty() is true.
  function dirty() {
    return dirtyFlag || animating;
  }

  // Call after changing anything in `overlay` (the engine cannot see those edits).
  function invalidate() {
    touch();
  }

  // projection x view of the last render (perspective or orthographic), column-major (same layout as
  // the app's mul(perspective, lookAt)).
  function pv() {
    const m = new THREE.Matrix4().multiplyMatrices(activeCam.projectionMatrix, activeCam.matrixWorldInverse);
    return Array.from(m.elements);
  }

  // point [x, y, z] ft -> {x, y} in NDC (-1..1, y up), z = NDC depth, behind = true behind the camera.
  function project(point) {
    const v = new THREE.Vector4(point[0], point[1], point[2], 1).applyMatrix4(activeCam.matrixWorldInverse).applyMatrix4(activeCam.projectionMatrix);
    const w = Math.abs(v.w) < 1e-9 ? 1e-9 : v.w;
    return { x: v.x / w, y: v.y / w, z: v.z / w, behind: v.w <= 0 };
  }

  // The view ray through an NDC point of the last render: {origin, direction} in SCENE feet.
  function ray(ndcX, ndcY) {
    const cam = activeCam;
    if (cam.isOrthographicCamera) {
      const o = new THREE.Vector3(ndcX, ndcY, -1).unproject(cam);
      const d = new THREE.Vector3(0, 0, -1).transformDirection(cam.matrixWorld);
      return { origin: o.toArray(), direction: d.toArray() };
    }
    const d = new THREE.Vector3(ndcX, ndcY, 0.5).unproject(cam).sub(cam.position).normalize();
    return { origin: cam.position.toArray(), direction: d.toArray() };
  }

  // ---- Picking -------------------------------------------------------------------------------

  // Direction <-> cube face texel, the OpenGL cube map layout (faces +x -x +y -y +z -z).
  function cubeTexel(d, n, out) {
    const ax = Math.abs(d.x), ay = Math.abs(d.y), az = Math.abs(d.z);
    let face, sc, tc, ma;
    if (ax >= ay && ax >= az) { ma = ax; if (d.x > 0) { face = 0; sc = -d.z; tc = -d.y; } else { face = 1; sc = d.z; tc = -d.y; } }
    else if (ay >= az) { ma = ay; if (d.y > 0) { face = 2; sc = d.x; tc = d.z; } else { face = 3; sc = d.x; tc = -d.z; } }
    else { ma = az; if (d.z > 0) { face = 4; sc = d.x; tc = -d.y; } else { face = 5; sc = -d.x; tc = -d.y; } }
    out.face = face;
    out.x = Math.min(n - 1, Math.max(0, Math.floor((sc / ma * 0.5 + 0.5) * n)));
    out.y = Math.min(n - 1, Math.max(0, Math.floor((tc / ma * 0.5 + 0.5) * n)));
    return out;
  }

  function texelDir(face, x, y, n, out) {
    const sc = (x + 0.5) / n * 2 - 1, tc = (y + 0.5) / n * 2 - 1;
    if (face === 0) out.set(1, -tc, -sc);
    else if (face === 1) out.set(-1, -tc, sc);
    else if (face === 2) out.set(sc, 1, tc);
    else if (face === 3) out.set(sc, -1, -tc);
    else if (face === 4) out.set(sc, -tc, 1);
    else out.set(-sc, -tc, -1);
    return out.normalize();
  }

  // distance (ft) and class code of one texel; null where nothing lies within the far plane
  function texelRead(cpu, face, x, y) {
    const b = cpu.faces[face];
    const i = (y * cpu.n + x) * 4;
    if (b[i + 3] === 255) return null;
    return { dist: (b[i] / 256 + b[i + 1] / 65536 + b[i + 2] / 16711680) * cpu.far, code: b[i + 3] };
  }

  const pickT = { face: 0, x: 0, y: 0 };
  const pickD = new THREE.Vector3();
  const pickP = new THREE.Vector3();
  const pickU = new THREE.Vector3();
  const pickV = new THREE.Vector3();
  const pickN = new THREE.Vector3();

  function pickCube(e, dir) {
    const cpu = e.cpu;
    if (!cpu) {
      if (!e.cpuJob) readDepth(e);
      return null;
    }
    const n = cpu.n;
    const t = cubeTexel(dir, n, pickT);
    const hit = texelRead(cpu, t.face, t.x, t.y);
    if (!hit) return null;
    const at = (x, y, out) => {
      const h = texelRead(cpu, t.face, x, y);
      if (!h) return null;
      texelDir(t.face, x, y, n, out).multiplyScalar(h.dist);
      return h.dist;
    };
    at(t.x, t.y, pickP);
    // Neighbours along each texel axis: the one on the same surface (smaller jump in distance).
    const side = (dx, dy, out) => {
      const x1 = t.x + dx, y1 = t.y + dy, x0 = t.x - dx, y0 = t.y - dy;
      const tmp = new THREE.Vector3();
      const d1 = x1 < n && y1 < n ? at(x1, y1, out) : null;
      const d0 = x0 >= 0 && y0 >= 0 ? at(x0, y0, tmp) : null;
      if (d1 === null && d0 === null) return 0;
      if (d1 === null || (d0 !== null && Math.abs(d0 - hit.dist) < Math.abs(d1 - hit.dist))) {
        out.copy(tmp).sub(pickP).negate();
        return 1;
      }
      out.sub(pickP);
      return 1;
    };
    let normal = null;
    let dist = hit.dist;
    if (side(1, 0, pickU) && side(0, 1, pickV)) {
      pickN.crossVectors(pickU, pickV);
      if (pickN.lengthSq() > 1e-18) {
        pickN.normalize();
        if (pickN.dot(dir) > 0) pickN.negate();
        normal = pickN;
        // Where the ray itself meets that plane: sub-texel, so a reticle slides instead of stepping.
        const den = pickN.dot(dir);
        if (den < -0.02) {
          const s = pickN.dot(pickP) / den;
          if (s > 0 && Math.abs(s - hit.dist) < 0.08 * hit.dist + 0.1) dist = s;
        }
      }
    }
    if (!normal) normal = pickN.copy(dir).negate();
    return {
      point: [e.center.x + dir.x * dist, e.center.y + dir.y * dist, e.center.z + dir.z * dist],
      normal: normal.toArray(),
      distance: dist,
      cls: CODE_CLASS[hit.code] || 'base',
      source: 'depth',
    };
  }

  const raycaster = new THREE.Raycaster();

  function pickRay(ndcX, ndcY, classes) {
    const cam = activeCam;
    scene.updateMatrixWorld();
    raycaster.setFromCamera(new THREE.Vector2(ndcX, ndcY), cam);
    raycaster.near = 0;
    raycaster.far = Infinity;
    const doll = isDoll(state.mode);
    const list = [];
    for (const cls of classes) for (const o of byClass[cls] || []) if (o.visible && !(doll && o.userData.tg_outside)) list.push(o);
    const dir = raycaster.ray.direction;
    for (const hit of raycaster.intersectObjects(list, false)) {
      const cls = hit.object.userData.tg_class;
      const p = hit.point;
      const nrm = hit.face ? pickN.copy(hit.face.normal).transformDirection(hit.object.matrixWorld) : pickN.copy(dir).negate();
      if (nrm.dot(dir) > 0) nrm.negate();
      if (doll) {
        // the same rules as the shaders, so nothing that is not drawn can be picked
        const shell = cls === 'wall' || cls === 'glass';
        if (shell && p.y > proj.uTgClipY.value) continue;
        if (footprint.length) {
          if (!inFoot(p.x, p.z, shell ? 0.02 : cls === 'base' ? DOLL_MARGIN_BASE : DOLL_MARGIN)) continue;
          if (shell) {
            if (!inFoot(p.x + nrm.x * DOLL_SHELL, p.z + nrm.z * DOLL_SHELL)) continue;
            if (-dir.x > 0.04 && !inFoot(p.x + DOLL_SHELL, p.z)) continue;
            if (-dir.x < -0.04 && !inFoot(p.x - DOLL_SHELL, p.z)) continue;
            if (-dir.z > 0.04 && !inFoot(p.x, p.z + DOLL_SHELL)) continue;
            if (-dir.z < -0.04 && !inFoot(p.x, p.z - DOLL_SHELL)) continue;
          }
        }
      }
      return { point: p.toArray(), normal: nrm.toArray(), distance: hit.distance, cls, source: 'ray', node: hit.object.name };
    }
    return null;
  }

  // What lies under an NDC point (-1..1, y up) of the last rendered view:
  //   { point: [x, y, z], normal: [x, y, z] (unit, towards the viewer), distance (ft, from the eye),
  //     cls (tg_class of the surface), source: 'depth' | 'ray' }  or null.
  // Inside, resting on a sweep: from that sweep's depth cube (O(1), fine for every mouse move; null
  // until the cube's CPU copy has arrived, which prepare() waits for). During a move: null.
  // Dollhouse / floor plan: a ray cast against the floor classes (opts.classes, default ['base'];
  // opts.walls adds 'wall'), about a millisecond. opts.raycast forces the ray cast in any state.
  function pick(ndcX, ndcY, o = {}) {
    if (!parts) return null;
    if (!o.raycast && restEntry && panos.get(restEntry.id) === restEntry) {
      pickD.set(ndcX, ndcY, 0.5).unproject(activeCam).sub(activeCam.position).normalize();
      return pickCube(restEntry, pickD);
    }
    if (o.raycast || isDoll(state.mode)) {
      return pickRay(ndcX, ndcY, o.classes || (o.walls ? ['base', 'wall'] : ['base']));
    }
    return null;
  }

  // ---- Overlay helpers -----------------------------------------------------------------------

  // A flat ring in the xz plane (normal +y), centred on the origin, radii in feet. uv.x runs 0 (inner
  // edge) .. 1 (outer edge), uv.y around. ring(0, r) is a disc.
  function ring(radiusInner, radiusOuter, segments = 72) {
    const pos = [], uv = [], nrm = [], idx = [];
    for (let i = 0; i <= segments; i++) {
      const a = i / segments * Math.PI * 2, c = Math.cos(a), s = Math.sin(a);
      pos.push(c * radiusInner, 0, s * radiusInner, c * radiusOuter, 0, s * radiusOuter);
      uv.push(0, i / segments, 1, i / segments);
      nrm.push(0, 1, 0, 0, 1, 0);
      if (i < segments) { const k = i * 2; idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx);
    return g;
  }

  // Material for markers: unlit, premultiplied alpha, no depth write, both sides. With `soft` the
  // alpha feathers across uv.x (ring(): inner / outer edge) by that fraction of the width, at least a
  // pixel: {color, opacity, soft: 0.25 | [inner, outer]}. The feathering can be changed afterwards
  // through material.userData.soft.value (a Vector2: inner, outer).
  function overlayMaterial(o = {}) {
    const mat = new THREE.MeshBasicMaterial({
      color: o.color !== undefined ? o.color : 0xffffff, opacity: o.opacity !== undefined ? o.opacity : 1,
      transparent: true, premultipliedAlpha: true, depthWrite: false, depthTest: o.depthTest !== false,
      side: THREE.DoubleSide, toneMapped: false,
    });
    const soft = Array.isArray(o.soft) ? o.soft : [o.soft || 0, o.soft || 0];
    mat.defines = { USE_UV: '' };
    mat.userData.soft = { value: new THREE.Vector2(soft[0], soft[1]) };
    mat.onBeforeCompile = (shader) => {
      shader.uniforms.uSoft = mat.userData.soft;
      shader.fragmentShader = 'uniform vec2 uSoft;\n' + shader.fragmentShader.replace('#include <map_fragment>',
        '#include <map_fragment>\n\tfloat tgPx = fwidth( vUv.x );\n\tdiffuseColor.a *= smoothstep( 0.0, max( uSoft.x, tgPx ), vUv.x ) * smoothstep( 0.0, max( uSoft.y, tgPx ), 1.0 - vUv.x );');
    };
    mat.customProgramCacheKey = () => 'tg3overlay';
    return mat;
  }

  // ---- Introspection -------------------------------------------------------------------------

  function memory() {
    const seen = new Set();
    let atlas = 0, geometry = 0;
    root.traverse((o) => {
      if (!o.isMesh) return;
      const map = o.material && o.material.map;
      if (map && map.image && !seen.has(map)) { seen.add(map); atlas += (map.image.width || 0) * (map.image.height || 0) * 4 * 4 / 3; }
      const g = o.geometry;
      for (const k of Object.keys(g.attributes)) geometry += g.attributes[k].array.byteLength;
      if (g.index) geometry += g.index.array.byteLength;
    });
    const face = depthSize * depthSize * 4;
    let cpu = 0;
    for (const e of panos.values()) if (e.cpu) cpu += face * 6;
    const levels = { '2k': 0, '4k': 0, '8k': 0 };
    for (const e of panos.values()) levels[e.level] += 1;
    return {
      panoramas: panoBytes(), panoramaLevels: levels,
      depthCubes: cubes.length * 6 * face + (scratch ? 2 * face : 0),
      atlases: Math.round(atlas), geometry,
      gpu: Math.round(panoBytes() + cubes.length * 6 * face + (scratch ? 2 * face : 0) + atlas + geometry),
      pickCopies: cpu,
    };
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
      triangles: Math.round(tris), meshes, parts, calls: renderer.info.render.calls, drawn: renderer.info.render.triangles,
      classes: Object.keys(byClass), mode: state.mode,
      adaptation: adapt.value.toArray().map((v) => Math.round(v * 1000) / 1000),
      adaptationOutdoor: adaptOut.value.toArray().map((v) => Math.round(v * 1000) / 1000),
      projection: Object.assign({ cached: [...panos.keys()] }, projInfo),
      memory: memory(),
    };
  }

  function dispose() {
    for (const e of [...panos.values()]) dropPanorama(e);
    for (const c of cubes) c.rt.dispose();
    if (scratch) scratch.dispose();
    root.traverse((o) => {
      if (!o.isMesh) return;
      o.geometry.dispose();
      if (o.material.map) o.material.map.dispose();
      o.material.dispose();
    });
    draco.dispose();
    renderer.dispose();
  }

  if (opts.footprint) setFootprint(opts.footprint);
  if (opts.sweeps) setSweeps(opts.sweeps);

  api = {
    onDirty: null,
    gl, renderer, scene, camera, orthoCamera, overlay, caps,
    load, applyVisibility, setAdaptation, render, pv, stats,
    setPanorama, hasPanorama, setProjection,
    projectionInfo: () => Object.assign({ cached: [...panos.keys()], box: proj.uTgBox.value.toArray().map((v) => Math.round(v * 100) / 100) }, projInfo),
    resetState: () => renderer.resetState(),
    get loaded() { return parts > 0; },
    // v3
    setSweeps, setSweepBlend, setWanted, dropUpgrade, prepare, pick, ray, project,
    setMode, setBackground, setFootprint, setClassOpacity, setProjectionFade,
    ring, overlayMaterial, dirty, invalidate, memory, dispose,
    // test hooks: {bake: true} paints the bake magenta wherever it shows; {noRest: true} draws the
    // projected model even when resting on a sweep; {prepass: false} turns the depth pre-pass off
    setDebug: (o = {}) => {
      proj.uTgDebug.value = o.bake ? 1 : 0;
      debugNoRest = !!o.noRest;
      if (o.prepass !== undefined) prepass = !!o.prepass;
      if (o.prepassAll !== undefined) prepassSkip = o.prepassAll ? ['glass'] : ['glass', 'furniture', 'decor_high', 'landscape', 'exterior'];
      touch();
    },
    get mode() { return state.mode; },
    get resting() { return restEntry ? restEntry.id : null; },
    // what setSweepBlend was last given: {a, b, t}
    get blend() { return { a: blend.a, b: blend.b, t: blend.t }; },
  };
  return api;
}
