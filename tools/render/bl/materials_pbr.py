"""Textured PBR implementation of the material library (runs inside Blender).

`materials.py` keeps the public contract (KEYS, get(key), thin_glass()). Its `_build(key)` calls
`build(key)` here first and falls back to the flat Principled version when this returns None or
raises. Glass keys always stay `materials.thin_glass()` (no refraction: see its docstring).

Mapping (the build has NO UVs; everything is driven by world-space position in metres):
  * planar mapping (oriented patterns: boards, tiles, flutes, wood grain, roof seams): vertical
    faces use (a = position along the face's horizontal tangent T = normalize(cross(Z, N)),
    b = height z); horizontal faces use world (x, y). Boards, tiles and grain therefore stay
    correctly oriented on walls of ANY rotation. Tile rows start at the floor (z = 0).
  * triplanar mapping (isotropic textures: fabrics, stucco, concrete, gravel): three world-axis
    projections blended by |N|^k.
  * Normal maps are applied as world-space perturbations along the projection axes (no
    tangents / UVs needed), then chained into procedural Bump where needed.
Poly Haven (CC0) textures come from `assets.texture(id, res)`. Each texture's diffuse map is
graded to the KEYS colour by dividing by its measured mean (cached in tg_stats.json next to the
maps) and multiplying by the target, so the library keeps the KEYS palette exactly while gaining
real texture. If a download fails the material falls back to its procedural-only version.

Per-object knobs (optional, set as custom properties on the Blender object):
  ob['tg_grain'] = 1   rotate wood grain 90 deg on HORIZONTAL faces (default: grain along
                       world X on tops/bottoms; vertical faces always follow the face).
See MATERIALS.md for the per-key table (textures, scale, notes).
"""
import json
import math
import os
import traceback

try:
    import bpy
except Exception:  # pragma: no cover - imported outside Blender
    bpy = None

IN = 0.0254
FT = 0.3048
RES = '2k'
FABRIC_RES = '1k'
GLASS = ('glass_clear', 'glass_frosted', 'glass_picture')

_TEX = {}          # (asset_id, res) -> {'paths':..., 'mean': [r,g,b] linear, 'rough_mean': f} | None


# ---------------------------------------------------------------------------------- colour utils
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _hexlin(h):
    h = h.lstrip('#')
    return tuple(_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


def _keycol(key):
    from .materials import KEYS
    return _hexlin(KEYS[key][0])


def _keyrough(key):
    from .materials import KEYS
    return KEYS[key][1]


def _scale(c, s):
    return tuple(x * s for x in c)


# ------------------------------------------------------------------------------------- textures
def _img_mean(path, srgb):
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    try:
        img.colorspace_settings.name = 'Non-Color'
        n = img.size[0] * img.size[1] * 4
        a = np.empty(n, np.float32)
        img.pixels.foreach_get(a)
        a = a.reshape(-1, 4)[::5, :3]
        if srgb:
            a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
        return [float(x) for x in a.mean(0)]
    finally:
        bpy.data.images.remove(img)


def _texinfo(asset_id, res=RES):
    """Downloaded maps + measured stats for a Poly Haven texture, or None if unavailable."""
    k = (asset_id, res)
    if k in _TEX:
        return _TEX[k]
    info = None
    try:
        from . import assets
        paths = assets.texture(asset_id, res)
        if 'diffuse' not in paths:
            raise FileNotFoundError(f'{asset_id}: no diffuse map')
        sp = os.path.join(os.path.dirname(paths['diffuse']), 'tg_stats.json')
        st = None
        if os.path.exists(sp):
            try:
                st = json.load(open(sp))
            except Exception:
                st = None
        if not st:
            st = {'mean': _img_mean(paths['diffuse'], True)}
            if 'rough' in paths:
                st['rough_mean'] = _img_mean(paths['rough'], False)[0]
            try:
                tmp = f'{sp}.{os.getpid()}.tmp'
                with open(tmp, 'w') as f:
                    json.dump(st, f)
                os.replace(tmp, sp)
            except Exception:
                pass
        info = {'paths': paths, 'mean': st['mean'], 'rough_mean': st.get('rough_mean', 0.5)}
    except Exception as e:
        print(f'[materials_pbr] texture {asset_id} ({res}) unavailable, procedural fallback: {e!r}')
    _TEX[k] = info
    return info


def _image(path, color):
    img = bpy.data.images.load(path, check_existing=True)
    want = 'sRGB' if color else 'Non-Color'
    if img.colorspace_settings.name != want:
        img.colorspace_settings.name = want
    return img


# -------------------------------------------------------------------------------- graph helper
class _G:
    """Tiny expression builder over a material node tree. Values are sockets or constants."""

    def __init__(self, key):
        self.key = key
        m = bpy.data.materials.new('M_' + key)
        try:
            m.use_nodes = True
        except Exception:
            pass
        self.m = m
        self.nt = m.node_tree
        self.nt.nodes.clear()
        self._c = {}

    # ----------------------------------------------------------------- basics
    def new(self, typ, **props):
        n = self.nt.nodes.new(typ)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def put(self, sock, v):
        if v is None:
            return
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sock)
            return
        dv = sock.default_value
        if hasattr(dv, '__len__'):
            n = len(dv)
            if isinstance(v, (int, float)):
                v = (float(v),) * min(n, 3) + ((1.0,) if n == 4 else ())
            else:
                v = tuple(v)
                if len(v) == 3 and n == 4:
                    v = v + (1.0,)
                elif len(v) == 4 and n == 3:
                    v = v[:3]
        sock.default_value = v

    @staticmethod
    def sock(node, ident):
        for s in node.inputs:
            if s.identifier == ident:
                return s
        return node.inputs[ident]

    @staticmethod
    def osock(node, ident):
        for s in node.outputs:
            if s.identifier == ident:
                return s
        return node.outputs[ident]

    # ------------------------------------------------------------------ math
    def f(self, op, a, b=None, c=None, clamp=False):
        n = self.new('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.put(n.inputs[0], a)
        if b is not None:
            self.put(n.inputs[1], b)
        if c is not None:
            self.put(n.inputs[2], c)
        return n.outputs[0]

    def add(self, a, b):
        return self.f('ADD', a, b)

    def sub(self, a, b):
        return self.f('SUBTRACT', a, b)

    def mul(self, a, b):
        return self.f('MULTIPLY', a, b)

    def div(self, a, b):
        return self.f('DIVIDE', a, b)

    def mad(self, a, b, c):
        return self.f('MULTIPLY_ADD', a, b, c)

    def mn(self, a, b):
        return self.f('MINIMUM', a, b)

    def mx(self, a, b):
        return self.f('MAXIMUM', a, b)

    def floor(self, a):
        return self.f('FLOOR', a)

    def fract(self, a):
        return self.f('FRACT', a)

    def absf(self, a):
        return self.f('ABSOLUTE', a)

    def gt(self, a, b):
        return self.f('GREATER_THAN', a, b)

    def clamp01(self, a):
        return self.f('ADD', a, 0.0, clamp=True)

    def lerp(self, a, b, t):
        n = self.new('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        self.put(self.sock(n, 'Factor_Float'), t)
        self.put(self.sock(n, 'A_Float'), a)
        self.put(self.sock(n, 'B_Float'), b)
        return self.osock(n, 'Result_Float')

    def ss(self, x, e0, e1):
        """smoothstep(e0, e1, x) in [0, 1]."""
        n = self.new('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP', clamp=True)
        self.put(n.inputs['Value'], x)
        self.put(n.inputs['From Min'], e0)
        self.put(n.inputs['From Max'], e1)
        self.put(n.inputs['To Min'], 0.0)
        self.put(n.inputs['To Max'], 1.0)
        return n.outputs['Result']

    def remap(self, x, a0, a1, b0, b1, clamp=True):
        n = self.new('ShaderNodeMapRange', interpolation_type='LINEAR', clamp=clamp)
        self.put(n.inputs['Value'], x)
        self.put(n.inputs['From Min'], a0)
        self.put(n.inputs['From Max'], a1)
        self.put(n.inputs['To Min'], b0)
        self.put(n.inputs['To Max'], b1)
        return n.outputs['Result']

    def tri_wave(self, x, period):
        """Mirror-repeat: 0..period..0 triangle wave of x (book-matching)."""
        t = self.f('FLOORED_MODULO', self.div(x, period), 2.0)
        return self.mul(self.absf(self.sub(t, 1.0)), period)

    # --------------------------------------------------------------- vectors
    def vm(self, op, a, b=None, c=None, s=None):
        n = self.new('ShaderNodeVectorMath', operation=op)
        self.put(n.inputs[0], a)
        if b is not None:
            self.put(n.inputs[1], b)
        if c is not None:
            self.put(n.inputs[2], c)
        if s is not None:
            self.put(n.inputs[3], s)
        return n.outputs[1] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else n.outputs[0]

    def vscale(self, v, s):
        return self.vm('SCALE', v, s=s)

    def vadd(self, a, b):
        return self.vm('ADD', a, b)

    def vec(self, x, y, z=0.0):
        n = self.new('ShaderNodeCombineXYZ')
        self.put(n.inputs[0], x)
        self.put(n.inputs[1], y)
        self.put(n.inputs[2], z)
        return n.outputs[0]

    def sep(self, v):
        n = self.new('ShaderNodeSeparateXYZ')
        self.put(n.inputs[0], v)
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def cmix(self, a, b, t, blend='MIX'):
        n = self.new('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_factor=True)
        self.put(self.sock(n, 'Factor_Float'), t)
        self.put(self.sock(n, 'A_Color'), a)
        self.put(self.sock(n, 'B_Color'), b)
        return self.osock(n, 'Result_Color')

    def vmix(self, a, b, t):
        n = self.new('ShaderNodeMix', data_type='VECTOR', clamp_factor=True)
        self.put(self.sock(n, 'Factor_Float'), t)
        self.put(self.sock(n, 'A_Vector'), a)
        self.put(self.sock(n, 'B_Vector'), b)
        return self.osock(n, 'Result_Vector')

    def hsv(self, col, h=0.5, s=1.0, v=1.0):
        n = self.new('ShaderNodeHueSaturation')
        self.put(n.inputs['Hue'], h)
        self.put(n.inputs['Saturation'], s)
        self.put(n.inputs['Value'], v)
        self.put(n.inputs['Color'], col)
        return n.outputs[0]

    def gamma(self, col, g):
        n = self.new('ShaderNodeGamma')
        self.put(n.inputs['Color'], col)
        self.put(n.inputs['Gamma'], g)
        return n.outputs[0]

    # -------------------------------------------------------------- textures
    def noise(self, v, scale, detail=2.0, rough=0.5, distortion=0.0, lac=2.0, dims='3D'):
        n = self.new('ShaderNodeTexNoise', noise_dimensions=dims)
        self.put(n.inputs['Vector'], v)
        self.put(n.inputs['Scale'], scale)
        self.put(n.inputs['Detail'], detail)
        self.put(n.inputs['Roughness'], rough)
        self.put(n.inputs['Lacunarity'], lac)
        self.put(n.inputs['Distortion'], distortion)
        return n.outputs[0], n.outputs[1]

    def noise_w(self, w, scale, detail=2.0, rough=0.5, lac=2.0):
        """1D fractal noise of a scalar (Fac)."""
        n = self.new('ShaderNodeTexNoise', noise_dimensions='1D')
        self.put(n.inputs['W'], w)
        self.put(n.inputs['Scale'], scale)
        self.put(n.inputs['Detail'], detail)
        self.put(n.inputs['Roughness'], rough)
        self.put(n.inputs['Lacunarity'], lac)
        return n.outputs[0]

    def edge_w(self, w, spacing, rnd=1.0, seed=0.0):
        """Distance (in units of w) from w to the nearest edge of a 1D Voronoi partition with mean
        cell size `spacing`: edges sit at irregular, never-repeating positions along w. Also returns
        a random 0..1 per edge (constant on both sides of it): white noise of the lower of the two
        nearest feature points, which are the two cells the edge separates."""
        n = self.new('ShaderNodeTexVoronoi', voronoi_dimensions='1D', feature='DISTANCE_TO_EDGE')
        self.put(n.inputs['W'], w)
        self.put(n.inputs['Scale'], 1.0 / spacing)
        self.put(n.inputs['Randomness'], rnd)
        ids = []
        for feat in ('F1', 'F2'):
            f = self.new('ShaderNodeTexVoronoi', voronoi_dimensions='1D', feature=feat)
            self.put(f.inputs['W'], w)
            self.put(f.inputs['Scale'], 1.0 / spacing)
            self.put(f.inputs['Randomness'], rnd)
            ids.append(self.osock(f, 'W'))
        r, _ = self.white(self.vec(self.mn(ids[0], ids[1]), seed, 3.7))
        return self.mul(n.outputs['Distance'], spacing), r

    def white(self, v):
        n = self.new('ShaderNodeTexWhiteNoise', noise_dimensions='3D')
        self.put(n.inputs['Vector'], v)
        return n.outputs[0], n.outputs[1]

    def voronoi(self, v, scale, feature='F1', rnd=1.0, dims='3D'):
        n = self.new('ShaderNodeTexVoronoi', voronoi_dimensions=dims, feature=feature)
        self.put(n.inputs['Vector'], v)
        self.put(n.inputs['Scale'], scale)
        self.put(n.inputs['Randomness'], rnd)
        return n

    def image(self, img, v):
        n = self.new('ShaderNodeTexImage', projection='FLAT', extension='REPEAT', interpolation='Linear')
        n.image = img
        self.put(n.inputs['Vector'], v)
        return n

    def attr(self, name):
        n = self.new('ShaderNodeAttribute', attribute_type='OBJECT', attribute_name=name)
        return n.outputs[2]

    # -------------------------------------------------------------- geometry
    def geo(self):
        if 'geo' not in self._c:
            self._c['geo'] = self.new('ShaderNodeNewGeometry')
        return self._c['geo']

    def frame(self):
        """World-space position/normal decomposition shared by the mappings."""
        if 'frame' in self._c:
            return self._c['frame']
        geo = self.geo()
        P, N = geo.outputs['Position'], geo.outputs['Normal']
        px, py, pz = self.sep(P)
        nx, ny, nz = self.sep(N)
        hl = self.f('SQRT', self.mx(self.add(self.mul(nx, nx), self.mul(ny, ny)), 1e-8))
        tx = self.div(self.mul(ny, -1.0), hl)
        ty = self.div(nx, hl)
        u = self.add(self.mul(px, tx), self.mul(py, ty))
        horiz = self.gt(self.absf(nz), 0.7071)
        fr = dict(P=P, N=N, px=px, py=py, pz=pz, nx=nx, ny=ny, nz=nz, u=u, horiz=horiz,
                  T=self.vec(tx, ty, 0.0), hl=hl)
        self._c['frame'] = fr
        return fr

    def planar(self, grain_knob=False):
        """(a, b, A, B): plane coordinates (m) and the world axes they increase along.
        Vertical faces: a along the face (T), b = z. Horizontal faces: a = x, b = y
        (or a = y, b = -x when the object sets tg_grain = 1 and grain_knob is on)."""
        ck = ('planar', grain_knob)
        if ck in self._c:
            return self._c[ck]
        fr = self.frame()
        ha, hb, HA, HB = fr['px'], fr['py'], (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
        if grain_knob:
            r = self.clamp01(self.attr('tg_grain'))
            ha = self.lerp(fr['px'], fr['py'], r)
            hb = self.lerp(fr['py'], self.mul(fr['px'], -1.0), r)
            HA = self.vmix((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), r)
            HB = self.vmix((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), r)
        h = fr['horiz']
        a = self.lerp(fr['u'], ha, h)
        b = self.lerp(fr['pz'], hb, h)
        A = self.vmix(fr['T'], HA, h)
        B = self.vmix((0.0, 0.0, 1.0), HB, h)
        self._c[ck] = (a, b, A, B)
        return a, b, A, B

    # ------------------------------------------------------- texture sampling
    def sample(self, tid, a, b, A, B, size, res=RES, grain='u', stretch=1.0,
               maps=('diffuse', 'rough', 'nor_gl')):
        """Sample texture `tid` at plane coords (a along A, b along B; metres). `size` = real
        width of the texture (m); `stretch` lengthens it along a. grain='v' means the image's
        grain runs along its v axis, so the image is turned to put the grain along a.
        Returns {'color','rough','pert','mean','rough_mean'} or None."""
        info = _texinfo(tid, res)
        if info is None:
            return None
        ca = self.div(a, size * stretch)
        cb = self.div(b, size)
        if grain == 'u':
            uv, Au, Av, su, sv = self.vec(ca, cb), A, B, 1.0 / stretch, 1.0
        else:
            uv, Au, Av, su, sv = self.vec(cb, ca), B, A, 1.0, 1.0 / stretch
        out = {'mean': tuple(info['mean']), 'rough_mean': info['rough_mean']}
        for k in maps:
            p = info['paths'].get(k)
            if p is None:
                continue
            img = _image(p, k == 'diffuse')
            out[k] = self.image(img, uv).outputs['Color']
        out['color'] = out.get('diffuse')
        out['rough'] = out.get('rough')
        if out.get('nor_gl') is not None:
            t = self.vm('MULTIPLY_ADD', out['nor_gl'], (2.0, 2.0, 2.0), (-1.0, -1.0, -1.0))
            tx, ty, _ = self.sep(t)
            out['pert'] = self.vadd(self.vscale(Au, self.mul(tx, su)), self.vscale(Av, self.mul(ty, sv)))
        else:
            out['pert'] = None
        return out

    def tri(self, tid, size, res=RES, sharp=8.0, maps=('diffuse', 'rough', 'nor_gl'), offset=(0.0, 0.0, 0.0)):
        """World-axis triplanar sample; same return as sample()."""
        fr = self.frame()
        if 'triw' not in self._c:
            ws = [self.f('POWER', self.absf(c), sharp) for c in (fr['nx'], fr['ny'], fr['nz'])]
            tot = self.add(self.add(ws[0], ws[1]), ws[2])
            self._c['triw'] = [self.div(w, tot) for w in ws]
        w = self._c['triw']
        px, py, pz = fr['px'], fr['py'], fr['pz']
        if any(offset):
            px, py, pz = self.add(px, offset[0]), self.add(py, offset[1]), self.add(pz, offset[2])
        X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
        projs = [(py, pz, Y, Z), (px, pz, X, Z), (px, py, X, Y)]
        res_ = [self.sample(tid, a, b, A, B, size, res, maps=maps) for a, b, A, B in projs]
        if res_[0] is None:
            return None
        out = {'mean': res_[0]['mean'], 'rough_mean': res_[0]['rough_mean']}
        for k in ('color', 'pert'):
            if res_[0].get(k) is None:
                out[k] = None
                continue
            acc = None
            for wi, r in zip(w, res_):
                term = self.vscale(r[k], wi)
                acc = term if acc is None else self.vadd(acc, term)
            out[k] = acc
        if res_[0].get('rough') is not None:
            acc = None
            for wi, r in zip(w, res_):
                term = self.mul(r['rough'], wi)
                acc = term if acc is None else self.add(acc, term)
            out['rough'] = acc
        else:
            out['rough'] = None
        return out

    def grade(self, col, mean, target, contrast=1.0, sat=None):
        """Re-colour a texture to `target` (linear RGB) keeping its relative variation."""
        r = self.vm('DIVIDE', col, tuple(max(m, 1e-4) for m in mean))
        if contrast != 1.0:
            r = self.gamma(r, contrast)
        if sat is not None:
            r = self.hsv(r, s=sat)
        return self.vm('MULTIPLY', r, tuple(target))

    def rough_from(self, s, base, amp=1.0, lo=0.02, hi=1.0):
        if s is None or s.get('rough') is None:
            return base
        v = self.mad(self.sub(s['rough'], s['rough_mean']), amp, base)
        return self.remap(v, lo, hi, lo, hi)

    def normal(self, pert=None, strength=1.0, height=None, dist=0.001, bump=1.0):
        N = self.frame()['N']
        n = N
        if pert is not None and strength:
            n = self.vm('NORMALIZE', self.vm('MULTIPLY_ADD', pert, (strength,) * 3, N))
        if height is not None:
            b = self.new('ShaderNodeBump')
            self.put(b.inputs['Strength'], bump)
            self.put(b.inputs['Distance'], dist)
            self.put(b.inputs['Height'], height)
            if n is not N:
                self.put(b.inputs['Normal'], n)
            n = b.outputs[0]
        return None if n is N else n

    # ----------------------------------------------------------------- output
    def bsdf(self, base, rough, metal=0.0, normal=None, **extra):
        b = self.new('ShaderNodeBsdfPrincipled')
        self.put(b.inputs['Base Color'], base)
        self.put(b.inputs['Roughness'], rough)
        self.put(b.inputs['Metallic'], metal)
        if normal is not None:
            self.put(b.inputs['Normal'], normal)
        for k, v in extra.items():
            self.put(b.inputs[k.replace('_', ' ')], v)
        return b

    def finish(self, shader, disp=None):
        out = self.new('ShaderNodeOutputMaterial')
        self.nt.links.new(shader.outputs[0], out.inputs['Surface'])
        from .materials import KEYS, _hex
        self.m.diffuse_color = _hex(KEYS[self.key][0])
        self.m.roughness = KEYS[self.key][1]
        return self.m


# ============================================================================ pattern helpers
def _boards(g, along, across, width, seg_min, seg_max, split=(0.36, 0.64), seed=0.0):
    """Staggered random-length boards. along/across: float sockets (m) in the board frame.
    Each column of `width` is cut into segments (length seg_min..seg_max, random per column,
    random offset) and every segment is split once at a random point -> random board lengths
    with staggered ends. Returns per-board randoms and distances to the board edges (m)."""
    c = g.div(across, width)
    col = g.floor(c)
    fc = g.sub(c, col)
    _, rc = g.white(g.vec(col, seed, 7.31))
    r0, r1, _ = g.sep(rc)
    S = g.mad(r0, seg_max - seg_min, seg_min)
    s = g.div(g.add(along, g.mul(r1, S)), S)
    seg = g.floor(s)
    fs = g.sub(s, seg)
    rs, _ = g.white(g.vec(col, seg, seed + 3.7))
    sp = g.mad(rs, split[1] - split[0], split[0])
    part = g.gt(fs, sp)
    start = g.mul(part, sp)
    end = g.mad(part, g.sub(1.0, sp), sp)
    d_end = g.mul(g.mn(g.sub(fs, start), g.sub(end, fs)), S)
    d_side = g.mul(g.mn(fc, g.sub(1.0, fc)), width)
    bid = g.vec(col, g.mad(seg, 2.0, part), seed + 11.0)
    _, rnd = g.white(bid)
    _, rnd2 = g.white(g.vadd(bid, (0.0, 0.0, 17.7)))
    return dict(rnd=g.sep(rnd), rnd2=g.sep(rnd2), d_end=d_end, d_side=d_side, col=col, fc=fc)


def _grid(g, a, b, tw, th, offset=0.0, a0=0.0, b0=0.0):
    """Rectangular tile grid (tile tw along a, th along b; rows offset by offset*tw).
    Returns (tile id vector, distance to nearest joint (m), local a, local b)."""
    bb = g.sub(b, b0)
    row = g.floor(g.div(bb, th))
    aa = g.sub(g.sub(a, a0), g.mul(row, offset * tw)) if offset else g.sub(a, a0)
    colf = g.div(aa, tw)
    col = g.floor(colf)
    la = g.mul(g.sub(colf, col), tw)
    lb = g.sub(bb, g.mul(row, th))
    d = g.mn(g.mn(la, g.sub(tw, la)), g.mn(lb, g.sub(th, lb)))
    return g.vec(col, row, 0.0), d, la, lb


def _unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return tuple(x / n for x in v)


def _flow(g, Q, D, warp, scale, detail=5.0, rough=0.55, seed=(0.0, 0.0, 0.0), fine=0.0, fine_scale=7.0, bend=0.0,
          bend_scale=0.3):
    """Flow coordinate for veining: w = dot(Q, D) + fractal domain-warp turbulence (metres). Veins
    drawn as level sets of w are warped parallel sheets ("Perlin marble"): they all flow one way,
    run continuously over edges (it is a 3D field) and cannot close into loops as long as the warp
    gradient stays below |D projected on the face| (keep warp * scale <~ 0.35)."""
    w = g.vm('DOT_PRODUCT', Q, _unit(D))
    n, _ = g.noise(g.vadd(Q, seed), scale, detail=detail, rough=rough)
    w = g.mad(g.sub(n, 0.5), 2.0 * warp, w)
    if fine:
        n2, _ = g.noise(g.vadd(Q, (seed[1] + 3.3, seed[2] + 1.9, seed[0] + 7.1)), fine_scale, detail=3.0, rough=0.6)
        w = g.mad(g.sub(n2, 0.5), 2.0 * fine, w)
    if bend:   # slow meanders over metres, so a wall of veins is not a set of parallel lines
        n3, _ = g.noise(g.vadd(Q, (seed[2] + 6.1, seed[0] + 2.5, seed[1] + 4.2)), bend_scale, detail=1.0)
        w = g.mad(g.sub(n3, 0.5), 2.0 * bend, w)
    return w


def _vein(g, w, Q, spacing, width, seed, presence=(0.3, 0.55), along=1.2, taper=(0.12, 1.5), rag=0.0,
          rag_scale=45.0, strength=(0.3, 1.0)):
    """One vein family: the edges of a 1D Voronoi partition of the flow coordinate w (irregular,
    never-repeating spacing). Each vein draws its own strength (bold / medium / ghost); a 3D noise
    along its length tapers the width and fades it in and out, so veins start, swell and die out
    like real ones. Returns (d, wid, k, r): distance to the vein centre (m), local width (m),
    presence 0..1 and the per-vein random."""
    d, r = g.edge_w(w, spacing, seed=seed[0])
    t, _ = g.noise(g.vadd(Q, seed), along, detail=2.0)
    k = g.mul(g.ss(t, presence[0], presence[1]), g.remap(r, 0.0, 1.0, strength[0], strength[1]))
    wid = g.mul(g.remap(t, presence[0], 0.75, taper[0] * width, taper[1] * width), g.remap(r, 0.0, 1.0, 0.45, 1.7))
    if rag:
        n, _ = g.noise(g.vadd(Q, (seed[2], seed[0], seed[1])), rag_scale, detail=3.0, rough=0.55)
        d = g.mx(g.mad(g.sub(n, 0.5), g.mul(wid, rag), d), 0.0)
    return d, wid, k, r


def _calacatta(g, Q, base, core, body, halo, gold, contrast=1.0, spacing=0.72, width=0.005, D=(-0.55, 0.8, 0.75),
               secondary=0.6, hair=0.4, cloud=0.03, seed=0.0):
    """Calacatta-look quartz / marble-look porcelain on a 3D coordinate Q (m).
    Main veins: broad soft grey drifts (cloudy feathered halo, some gold-tinted) around a soft body
    and a darker tapering core that braids into two strands and merges again. Secondary veins at
    ~30 deg branch off and fade; fine hairlines wander between them. All are level sets of warped
    flow fields, so there are no closed loops and no crackle network. Returns (colour, vein mask)."""
    s = seed
    w1 = _flow(g, Q, D, 0.26, 0.75, detail=3.0, seed=(1.3 + s, 4.1, 2.7), fine=0.006, fine_scale=11.0, bend=0.9)
    d1, wd1, k1, r1 = _vein(g, w1, Q, spacing, width, (5.1 + s, 1.7, 3.3), presence=(0.3, 0.52), along=1.1,
                            rag=0.3, rag_scale=30.0, strength=(0.25, 1.0))
    # braid: two strands at +-off from the centre line that merge and split along the vein
    ob, _ = g.noise(g.vadd(Q, (8.3 + s, 0.4, 5.5)), 2.4, detail=2.0)
    off = g.mul(g.ss(ob, 0.45, 0.7), 0.022)
    ds = g.absf(g.sub(d1, off))
    D2 = (D[0] + 0.6, D[1] + 0.05, D[2] - 0.1)
    w2 = _flow(g, Q, D2, 0.2, 1.1, detail=3.5, seed=(7.7 + s, 2.2, 9.1), fine=0.006, fine_scale=14.0, bend=0.6)
    d2, wd2, k2, _ = _vein(g, w2, Q, spacing * 0.6, width * 0.45, (2.4 + s, 8.8, 6.6), presence=(0.46, 0.64),
                           along=1.6, rag=0.3, strength=(0.0, 1.0))
    D3 = (D[0] - 0.4, D[1] - 0.5, D[2] + 0.3)
    w3 = _flow(g, Q, D3, 0.1, 2.2, detail=4.0, seed=(3.9 + s, 6.4, 0.8), fine=0.01, fine_scale=16.0)
    d3, wd3, k3, _ = _vein(g, w3, Q, spacing * 0.3, 0.0008, (9.2 + s, 3.1, 4.4), presence=(0.54, 0.7),
                           along=2.4, strength=(0.0, 1.0))

    def prof(d, wid):
        return g.sub(1.0, g.ss(d, 0.0, wid))

    # cloudy modulation of the soft parts (so halos are drifts, not airbrushed tubes)
    cm, _ = g.noise(g.vadd(Q, (4.4 + s, 9.9, 1.2)), 9.0, detail=4.0, rough=0.6)
    cmod = g.remap(cm, 0.3, 0.7, 0.35, 1.25)
    core1 = g.mul(g.mx(prof(d1, wd1), g.mul(prof(ds, g.mul(wd1, 0.5)), 0.8)), k1)
    body1 = g.mul(g.mul(prof(d1, g.mad(wd1, 3.0, 0.01)), k1), g.mad(cmod, 0.5, 0.5))
    h1 = prof(d1, g.mad(wd1, 9.0, 0.06))
    halo1 = g.mul(g.mul(g.mul(h1, h1), k1), cmod)
    core2 = g.mul(prof(d2, wd2), k2)
    halo2 = g.mul(g.mul(prof(d2, g.mad(wd2, 6.0, 0.012)), k2), cmod)
    hl3 = g.mul(prof(d3, wd3), k3)
    # faint large-scale clouding
    cl, _ = g.noise(g.vadd(Q, (2.0 + s, 5.0, 8.0)), 2.2, detail=3.0, rough=0.55)
    col = g.vscale(base, g.remap(cl, 0.3, 0.7, 1.0 - cloud, 1.0 + cloud * 0.3))
    # some veins carry a warm gold-taupe halo
    hcol = g.cmix(halo, gold, g.ss(r1, 0.6, 0.8))
    c = contrast
    col = g.cmix(col, hcol, g.mul(halo1, 0.8 * c))
    col = g.cmix(col, halo, g.mul(halo2, 0.55 * c))
    col = g.cmix(col, body, g.mul(body1, 0.7 * c))
    col = g.cmix(col, body, g.mul(core2, 0.85 * c * secondary))
    col = g.cmix(col, core, g.mul(core1, 0.75 * c))
    col = g.cmix(col, body, g.mul(hl3, hair * c))
    mask = g.mx(g.mx(core1, g.mul(body1, 0.5)), g.mul(core2, secondary))
    return col, mask


# ============================================================================== material makers
def _paint(g, key, rough=None, peel=1.0, coat=0.0):
    """Paint: KEYS colour, very fine low orange-peel/roller bump, faint roughness variation."""
    col = _keycol(key)
    rough = _keyrough(key) if rough is None else rough
    fr = g.frame()
    n1, _ = g.noise(fr['P'], 330.0, detail=3.0, rough=0.55)
    n2, _ = g.noise(fr['P'], 2.5, detail=2.0)
    n3, _ = g.noise(fr['P'], 60.0, detail=2.0)
    base = g.vscale(col, g.remap(n2, 0.3, 0.7, 0.985, 1.012))
    r = g.add(rough, g.add(g.mul(g.sub(n2, 0.5), 0.07), g.mul(g.sub(n3, 0.5), 0.05)))
    h = g.add(n1, g.mul(n3, 0.4))
    nrm = g.normal(height=h, dist=0.00012 * peel)
    extra = {}
    if coat:
        extra = {'Coat Weight': coat, 'Coat Roughness': 0.25}
    return g.finish(g.bsdf(base, r, 0.0, nrm, **extra))


def _textured(g, key, tid, size, contrast=1.0, sat=None, rough=None, ramp=0.6, nstr=1.0,
              res=RES, planar=False, sheen=0.0, sheen_rough=0.5, coat=0.0, coat_rough=0.3,
              metal=0.0, grain='u', stretch=1.0, tone_noise=0.0, extra=None):
    """Generic graded Poly Haven material (triplanar by default)."""
    col = _keycol(key)
    rough = _keyrough(key) if rough is None else rough
    if planar:
        a, b, A, B = g.planar(grain_knob=True)
        s = g.sample(tid, a, b, A, B, size, res, grain=grain, stretch=stretch)
    else:
        s = g.tri(tid, size, res)
    fr = g.frame()
    if s is None:
        n, _ = g.noise(fr['P'], 8.0 / size, detail=4.0)
        base = g.vscale(col, g.remap(n, 0.2, 0.8, 0.85, 1.15))
        r, pert = rough, None
    else:
        base = g.grade(s['color'], s['mean'], col, contrast, sat)
        r = g.rough_from(s, rough, ramp)
        pert = s['pert']
    if tone_noise:
        n, _ = g.noise(fr['P'], 0.6 / max(size, 0.05), detail=2.0)
        base = g.vscale(base, g.remap(n, 0.25, 0.75, 1.0 - tone_noise, 1.0 + tone_noise))
    nrm = g.normal(pert, nstr)
    kw = dict(extra or {})
    if sheen:
        kw.update({'Sheen Weight': sheen, 'Sheen Roughness': sheen_rough})
    if coat:
        kw.update({'Coat Weight': coat, 'Coat Roughness': coat_rough})
    return g.finish(g.bsdf(base, r, metal, nrm, **kw))


# ---------------------------------------------------------------------------------- floors
def _oak_floor(g):
    fr = g.frame()
    W = 9.0 * IN
    bd = _boards(g, fr['py'], fr['px'], W, 2.9, 3.6, split=(0.42, 0.58))   # boards 1.22-2.09 m (4-7 ft)
    r0, r1, r2 = bd['rnd']
    q0, q1, q2 = bd['rnd2']
    a = g.mad(r0, 23.7, fr['py'])                 # along the board (N-S), random per board
    b = g.mad(r1, 17.3, fr['px'])
    A, B = (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)
    target = _keycol('oak_floor')
    sA = g.sample('oak_veneer_03', a, b, A, B, 1.0, grain='u', stretch=1.7)
    sB = g.sample('silver_oak_veneer_01', a, b, A, B, 1.0, grain='u', stretch=1.7)
    pick = g.gt(r2, 0.55)
    if sA and sB:
        cA = g.grade(sA['color'], sA['mean'], target, 1.45)
        cB = g.grade(sB['color'], sB['mean'], target, 1.45)
        col = g.cmix(cA, cB, pick)
        rA, rB = g.rough_from(sA, 0.5, 0.5), g.rough_from(sB, 0.5, 0.5)
        rough = g.lerp(rA, rB, pick)
        pert = g.vmix(sA['pert'], sB['pert'], pick)
    else:
        n, _ = g.noise(g.vec(g.mul(a, 4.0), g.mul(b, 60.0), 0.0), 1.0, detail=6.0, rough=0.6)
        col = g.vscale(target, g.remap(n, 0.2, 0.8, 0.85, 1.12))
        rough, pert = 0.5, None
    col = g.vm('MULTIPLY', col, (1.02, 1.0, 0.95))       # oiled white oak: a touch warmer than raw veneer
    # per-board tone: lighter/darker, warmer/cooler
    col = g.vscale(col, g.remap(q0, 0.0, 1.0, 0.95, 1.04))
    col = g.cmix(col, g.vm('MULTIPLY', col, (1.04, 1.0, 0.92)), g.mul(q1, 0.45))
    dmin = g.mn(bd['d_side'], bd['d_end'])
    gap = g.ss(dmin, 0.00015, 0.0011)
    col = g.vscale(col, g.lerp(0.5, 1.0, gap))
    rough = g.add(rough, g.mul(g.sub(q2, 0.5), 0.08))
    height = g.ss(dmin, 0.0, 0.0016)
    nrm = g.normal(pert, 0.6, height=height, dist=0.0007)
    return g.finish(g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.12, 'Coat Roughness': 0.32}))


def _ipe_deck(g):
    a, b, A, B = g.planar()
    W = 5.75 * IN
    bd = _boards(g, a, b, W, 2.6, 4.8)
    r0, r1, r2 = bd['rnd']
    q0, q1, _ = bd['rnd2']
    target = _keycol('ipe_deck')
    s = g.sample('sapele_veneer', g.mad(r0, 19.0, a), g.mad(r1, 7.0, b), A, B, 0.5, grain='v', stretch=2.2)
    if s:
        col = g.grade(s['color'], s['mean'], target, 1.4)
        rough, pert = g.rough_from(s, 0.55, 0.5), s['pert']
    else:
        col, rough, pert = target, 0.55, None
    col = g.vscale(col, g.remap(q0, 0.0, 1.0, 0.8, 1.15))
    col = g.cmix(col, g.vm('MULTIPLY', col, (1.08, 0.97, 0.88)), q1)
    gap_side = g.ss(bd['d_side'], 0.0025, 0.0045)        # ~6 mm open gaps between boards
    gap_end = g.ss(bd['d_end'], 0.0006, 0.0015)
    gap = g.mul(gap_side, gap_end)
    col = g.vscale(col, g.lerp(0.06, 1.0, gap))
    height = g.mul(g.ss(bd['d_side'], 0.003, 0.0065), gap_end)
    nrm = g.normal(pert, 0.7, height=height, dist=0.004)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


def _cladding(g):
    """Vertical cedar / thermo-ash boards with tight shadow gaps."""
    a, b, A, B = g.planar()
    W = 5.0 * IN
    bd = _boards(g, b, a, W, 3.2, 4.8)
    r0, r1, _ = bd['rnd']
    q0, q1, _ = bd['rnd2']
    target = _keycol('wood_cladding')
    _, r2, _ = bd['rnd']
    al, ac = g.mad(r0, 13.0, b), g.mad(r1, 9.0, a)
    # mostly clear straight-grain boards (ash) with some figured / knotty ones (teak)
    sC = g.sample('ash_veneer', al, ac, B, A, 1.0, grain='u', stretch=1.6)
    sK = g.sample('teak_veneer', al, ac, B, A, 1.0, grain='u', stretch=1.6)
    pick = g.gt(r2, 0.68)
    if sC and sK:
        col = g.cmix(g.grade(sC['color'], sC['mean'], target, 2.0, sat=0.65),
                     g.grade(sK['color'], sK['mean'], target, 1.1, sat=0.6), pick)
        rough = g.lerp(g.rough_from(sC, 0.62, 0.4), g.rough_from(sK, 0.62, 0.4), pick)
        pert = g.vmix(sC['pert'], sK['pert'], pick)
    else:
        col, rough, pert = target, 0.62, None
    col = g.vscale(col, g.remap(q0, 0.0, 1.0, 0.88, 1.1))
    col = g.cmix(col, g.vm('MULTIPLY', col, (1.03, 0.99, 0.95)), q1)     # slight per-board warmth
    gap = g.ss(bd['d_side'], 0.0012, 0.0022)
    col = g.vscale(col, g.lerp(0.05, 1.0, gap))
    height = g.ss(bd['d_side'], 0.001, 0.004)
    nrm = g.normal(pert, 0.6, height=height, dist=0.003)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


def _veneer(g, key, tid, size, grain_img, vertical, contrast, rough, coat=0.2, sat=None, stretch=1.0):
    """Finished wood veneer panel. vertical=True -> grain runs up the face (doors)."""
    a, b, A, B = g.planar(grain_knob=True)
    if vertical:
        fr = g.frame()
        # vertical faces: grain along z; horizontal faces keep grain along a
        al = g.lerp(b, a, fr['horiz'])
        ac = g.lerp(a, b, fr['horiz'])
        Al = g.vmix(B, A, fr['horiz'])
        Ac = g.vmix(A, B, fr['horiz'])
        s = g.sample(tid, al, ac, Al, Ac, size, grain=grain_img, stretch=stretch)
    else:
        s = g.sample(tid, a, b, A, B, size, grain=grain_img, stretch=stretch)
    col = _keycol(key)
    if s:
        base = g.grade(s['color'], s['mean'], col, contrast, sat)
        r, pert = g.rough_from(s, rough, 0.4), s['pert']
    else:
        base, r, pert = col, rough, None
    nrm = g.normal(pert, 0.5)
    return g.finish(g.bsdf(base, r, 0.0, nrm, **{'Coat Weight': coat, 'Coat Roughness': 0.28}))


# ---------------------------------------------------------------------------------- stone
def _quartz_calacatta(g):
    fr = g.frame()
    base = _keycol('quartz_calacatta')
    col, v = _calacatta(g, fr['P'], base, core=_hexlin('#7f7c77'), body=_hexlin('#a29d96'),
                        halo=_hexlin('#c8c3ba'), gold=_hexlin('#c9bca5'))
    sp, _ = g.noise(fr['P'], 900.0, detail=1.0)
    col = g.vscale(col, g.remap(sp, 0.3, 0.7, 0.988, 1.008))
    rough = g.add(0.1, g.mul(v, 0.03))
    return g.finish(g.bsdf(col, rough, 0.0, None, **{'Coat Weight': 0.0}))


def _quartz_white(g):
    fr = g.frame()
    base = _keycol('quartz_white')
    sp, _ = g.noise(fr['P'], 700.0, detail=1.0)
    sp2, _ = g.noise(fr['P'], 3.0, detail=2.0)
    col = g.vscale(base, g.mul(g.remap(sp, 0.25, 0.75, 0.975, 1.012), g.remap(sp2, 0.3, 0.7, 0.99, 1.01)))
    return g.finish(g.bsdf(col, 0.18, 0.0, None))


def _ramp(g, x, stops):
    """Colour ramp node: stops = [(pos, linear rgb), ...]."""
    n = g.new('ShaderNodeValToRGB')
    el = n.color_ramp.elements
    while len(el) < len(stops):
        el.new(0.5)
    for e, (pos, c) in zip(el, stops):
        e.position = pos
        e.color = tuple(c) + (1.0,)
    n.color_ramp.interpolation = 'B_SPLINE'
    g.put(n.inputs['Fac'], x)
    return n.outputs['Color']


def _stone_feature(g):
    """Polished book-matched onyx / quartzite slab pair: flowing, layered green-grey, sage, cream and
    taupe bands with milky translucent drifts, and soft gold-rust veins that FOLLOW the bands (they
    are level sets of the same flow field), plus a few faint cross veins. Mapped in OBJECT space so
    the mirror seam sits on the object's origin (its centre); the pattern mirrors again every SLAB
    metres either side (classic book-match)."""
    tc = g.new('ShaderNodeTexCoord')
    Po, No = tc.outputs['Object'], tc.outputs['Normal']
    ox, oy, oz = g.sep(Po)
    nx, ny, nz = g.sep(No)
    hl = g.f('SQRT', g.mx(g.add(g.mul(nx, nx), g.mul(ny, ny)), 1e-8))
    u = g.div(g.sub(g.mul(oy, nx), g.mul(ox, ny)), hl)
    horiz = g.gt(g.absf(nz), 0.7071)
    u = g.lerp(u, ox, horiz)
    v = g.lerp(oz, oy, horiz)
    slab = 1.5                                 # book-match slab width (m)
    uf = g.tri_wave(u, slab)
    Q = g.vec(uf, v, 0.0)
    # flow field: bands rise gently away from the seam and undulate strongly (onyx layering)
    th = math.radians(12.0)
    w = _flow(g, Q, (-math.sin(th), math.cos(th), 0.0), 0.42, 0.42, detail=6.0, rough=0.6, seed=(3.1, 7.2, 0.4),
              fine=0.008, fine_scale=4.0, bend=0.7, bend_scale=0.3)
    # layered bands: fractal 1D noise of the flow coordinate (irregular widths, never periodic);
    # the fine laminations only show in places, the rest is cloudy
    b1 = g.noise_w(w, 1.6, detail=3.0, rough=0.55)
    b2 = g.noise_w(g.add(w, 3.7), 7.0, detail=3.0, rough=0.6)
    b3 = g.noise_w(g.add(w, 9.1), 30.0, detail=2.0, rough=0.5)
    cl, _ = g.noise(g.vadd(Q, (1.0, 2.0, 5.0)), 1.1, detail=4.0, rough=0.55)
    lm, _ = g.noise(g.vadd(Q, (4.0, 8.0, 1.0)), 0.8, detail=2.0)
    lam = g.ss(lm, 0.42, 0.62)
    t = g.add(g.mul(b1, 0.7), g.mul(cl, 0.42))
    t = g.add(t, g.mul(g.add(g.mul(g.sub(b2, 0.5), 0.42), g.mul(g.sub(b3, 0.5), 0.16)), lam))
    t = g.remap(t, 0.36, 0.86, 0.0, 1.0)
    col = _ramp(g, t, [(0.0, _hexlin('#646a5c')), (0.28, _hexlin('#7f8576')), (0.5, _hexlin('#9a9e8c')),
                       (0.7, _hexlin('#b8b7a4')), (0.86, _hexlin('#d4cdba')), (1.0, _hexlin('#ddd2bd'))])
    # milky translucent drifts: soft light clouds elongated along the bands
    md, _ = g.noise(g.vec(g.mul(w, 2.2), g.mul(uf, 0.7), 2.0), 1.0, detail=5.0, rough=0.6)
    col = g.cmix(col, _hexlin('#d9dbd0'), g.mul(g.ss(md, 0.5, 0.8), 0.4))
    # taupe warmth in some bands
    tb = g.noise_w(g.add(w, 17.0), 3.0, detail=2.0)
    col = g.cmix(col, g.vm('MULTIPLY', col, (1.08, 0.98, 0.86)), g.mul(g.ss(tb, 0.55, 0.72), 0.7))
    # gold-rust veins along the flow (slightly off the band direction so they drift across layers)
    wv = g.mad(g.sub(g.noise(g.vadd(Q, (6.0, 1.0, 2.0)), 1.6, detail=2.0)[0], 0.5), 0.07, w)
    d1, wd1, k1, r1 = _vein(g, wv, Q, 0.38, 0.003, (4.2, 8.1, 2.9), presence=(0.42, 0.6), along=2.2,
                            taper=(0.1, 1.6), rag=0.4, rag_scale=40.0, strength=(0.2, 1.0))
    # a few faint cross veins (quartzite fractures healed with iron), sparse and short
    wc = _flow(g, Q, (math.cos(th + 0.35), math.sin(th + 0.35), 0.0), 0.12, 1.2, detail=3.0, seed=(9.4, 0.3, 5.5))
    d2, wd2, k2, _ = _vein(g, wc, Q, 0.55, 0.0012, (7.4, 2.6, 0.9), presence=(0.56, 0.7), along=1.8,
                           taper=(0.1, 1.4), rag=0.4, rag_scale=50.0, strength=(0.0, 1.0))

    def prof(d, wid):
        return g.sub(1.0, g.ss(d, 0.0, wid))

    core1 = g.mul(prof(d1, wd1), k1)
    halo1 = g.mul(prof(d1, g.mad(wd1, 7.0, 0.016)), k1)
    core2 = g.mul(prof(d2, wd2), k2)
    halo2 = g.mul(prof(d2, g.mad(wd2, 5.0, 0.006)), k2)
    gold = _hexlin('#ad8f62')
    rust = _hexlin('#7b5236')
    col = g.cmix(col, gold, g.mul(g.mul(halo1, halo1), 0.4))
    col = g.cmix(col, gold, g.mul(halo2, 0.25))
    col = g.cmix(col, g.cmix(rust, gold, g.ss(r1, 0.3, 0.9)), g.mul(core1, 0.8))
    col = g.cmix(col, rust, g.mul(core2, 0.5))
    # hairline seams at the book-match joints
    dseam = g.mn(uf, g.sub(slab, uf))
    seam = g.sub(1.0, g.ss(dseam, 0.0003, 0.0009))
    col = g.vscale(col, g.lerp(1.0, 0.6, seam))
    vm = g.mx(core1, core2)
    rough = g.add(0.16, g.mul(vm, 0.14))
    nrm = g.normal(height=g.sub(1.0, seam), dist=0.0004)
    return g.finish(g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.5, 'Coat Roughness': 0.05}))


# ---------------------------------------------------------------------------------- tiles
def _tile_wall_porcelain(g):
    """Large-format 24x48in marble-look porcelain, stacked. Every tile is a different 'face' of the
    print (random offset into the Calacatta vein field, and a random mirror so the vein direction
    alternates), with softer, lower-contrast veins than the quartz; 1/16in grout and a micro-bevel."""
    a, b, A, B = g.planar()
    tid, d, la, lb = _grid(g, a, b, 48 * IN, 24 * IN)
    _, rc = g.white(tid)
    r0, r1, r2 = g.sep(rc)
    _, rc2 = g.white(g.vadd(tid, (0.0, 0.0, 9.3)))
    f0, _, _ = g.sep(rc2)
    flip = g.sub(g.mul(g.gt(f0, 0.5), 2.0), 1.0)              # +-1 per tile
    Q = g.vec(g.mad(g.mul(la, flip), 1.0, g.mul(r0, 11.0)), g.mad(r1, 7.0, lb), g.mul(r2, 5.0))
    base = _keycol('tile_wall_porcelain')
    col, v = _calacatta(g, Q, base, core=_hexlin('#9a968f'), body=_hexlin('#b4afa7'), halo=_hexlin('#d0cbc2'),
                        gold=_hexlin('#cfc4b1'), contrast=0.75, spacing=0.8, width=0.004, D=(-0.55, 0.8, 0.0),
                        secondary=0.5, hair=0.3, cloud=0.025, seed=3.0)
    col = g.vscale(col, g.remap(r2, 0.0, 1.0, 0.985, 1.012))
    grout = g.sub(1.0, g.ss(d, 0.0007, 0.001))
    col = g.cmix(col, _hexlin('#d2cec7'), grout)
    rough = g.lerp(g.add(0.24, g.mul(v, 0.05)), 0.8, grout)
    height = g.ss(d, 0.0006, 0.0022)
    nrm = g.normal(height=height, dist=0.0008)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


def _tile_wave_white(g):
    a, b, A, B = g.planar()
    tid, d, _, _ = _grid(g, a, b, 24 * IN, 12 * IN, offset=0.5)
    _, rc = g.white(tid)
    r0, _, _ = g.sep(rc)
    lam, lam2 = 0.07, 0.36
    ph = g.mad(g.f('SINE', g.mul(b, 2 * math.pi / lam2)), 2.2, g.mul(a, 2 * math.pi / lam))
    _, wn = g.noise(g.vec(a, b, 0.0), 3.0, detail=2.0)
    wx, _, _ = g.sep(wn)
    ph = g.mad(wx, 1.2, ph)
    h = g.mad(g.f('SINE', ph), 0.5, 0.5)
    grout = g.sub(1.0, g.ss(d, 0.0007, 0.001))
    edge = g.ss(d, 0.0007, 0.004)
    height = g.mul(g.mad(h, 0.85, 0.15), edge)
    base = g.vscale(_keycol('tile_wave_white'), g.remap(r0, 0.0, 1.0, 0.985, 1.01))
    col = g.cmix(base, _hexlin('#dcd9d3'), grout)
    nrm = g.normal(height=height, dist=0.012)
    rough = g.lerp(0.3, 0.8, grout)
    return g.finish(g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.25, 'Coat Roughness': 0.12}))


def _tile_fluted_black(g):
    a, b, A, B = g.planar()
    tid, d, la, lb = _grid(g, a, b, 12 * IN, 24 * IN)
    _, rc = g.white(tid)
    r0, _, _ = g.sep(rc)
    pitch = 1.2 * IN                     # 10 flutes per 12in tile, joints fall in the valleys
    t = g.fract(g.div(la, pitch))
    x = g.sub(g.mul(t, 2.0), 1.0)
    h = g.f('SQRT', g.mx(g.sub(1.0, g.mul(x, x)), 0.0))
    joint_h = g.sub(1.0, g.ss(g.mn(lb, g.sub(24 * IN, lb)), 0.0006, 0.0011))
    height = g.mul(h, g.sub(1.0, joint_h))
    base = g.vscale(_keycol('tile_fluted_black'), g.remap(r0, 0.0, 1.0, 0.9, 1.1))
    col = g.cmix(base, _hexlin('#3a3a3a'), joint_h)
    nrm = g.normal(height=height, dist=0.006)
    return g.finish(g.bsdf(col, 0.38, 0.0, nrm, **{'Coat Weight': 0.3, 'Coat Roughness': 0.2}))


def _tile_floor_bath(g):
    a, b, A, B = g.planar()
    tid, d, _, _ = _grid(g, a, b, 48 * IN, 24 * IN, offset=1.0 / 3.0)
    _, rc = g.white(tid)
    r0, r1, r2 = g.sep(rc)
    target = _keycol('tile_floor_bath')
    s = g.sample('plastered_wall_04', g.mad(r0, 9.0, a), g.mad(r1, 9.0, b), A, B, 3.2,
                 maps=('diffuse', 'nor_gl'))
    if s:
        col = g.grade(s['color'], s['mean'], target, 1.1, sat=0.6)
    else:
        col = target
    fr = g.frame()
    sp, _ = g.noise(fr['P'], 500.0, detail=1.0)
    col = g.vscale(col, g.mul(g.remap(sp, 0.25, 0.75, 0.97, 1.02), g.remap(r2, 0.0, 1.0, 0.97, 1.03)))
    grout = g.sub(1.0, g.ss(d, 0.0007, 0.001))
    col = g.cmix(col, _hexlin('#8f8b85'), grout)
    rough = g.lerp(0.5, 0.85, grout)
    nrm = g.normal(s['pert'] if s else None, 0.3, height=g.ss(d, 0.0006, 0.002), dist=0.0008)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


def _tile_shower_floor(g):
    a, b, A, B = g.planar()
    tw = 2.0 * IN
    tid, d, _, _ = _grid(g, a, b, tw, tw)
    _, rc = g.white(tid)
    r0, r1, _ = g.sep(rc)
    base = _keycol('tile_shower_floor')
    col = g.vscale(base, g.remap(r0, 0.0, 1.0, 0.93, 1.06))
    col = g.cmix(col, g.vm('MULTIPLY', col, (1.04, 1.0, 0.95)), r1)
    grout = g.sub(1.0, g.ss(d, 0.0014, 0.0019))
    col = g.cmix(col, _hexlin('#b3afa8'), grout)
    height = g.ss(d, 0.0014, 0.005)
    nrm = g.normal(height=height, dist=0.0012)
    rough = g.lerp(0.55, 0.85, grout)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


# ---------------------------------------------------------------------------------- exterior
def _roof_metal(g):
    """Standing seam: seams every 16in running DOWN-SLOPE on every plane. The eave-direction
    coordinate comes from the shading normal: down-slope D = horizontal part of N, seams are
    spaced along E = cross(up, D)."""
    fr = g.frame()
    s = fr['u']                              # dot(P, normalize(cross(Z, N))) = along the eave
    flat = g.gt(g.absf(fr['nz']), 0.985)     # near-flat (crickets / caps): seams along y
    s = g.lerp(s, fr['px'], flat)
    pitch = 16.0 * IN
    sp = g.div(s, pitch)
    panel = g.floor(sp)
    t = g.sub(sp, panel)
    dist = g.mul(g.mn(t, g.sub(1.0, t)), pitch)
    seam = g.sub(1.0, g.ss(dist, 0.0045, 0.012))
    # two faint pencil ribs per panel + slight oil-canning
    rib_t = g.absf(g.sub(g.fract(g.mul(t, 3.0)), 0.5))
    rib = g.mul(g.sub(1.0, g.ss(rib_t, 0.0, 0.06)), 0.04)
    along = g.lerp(fr['pz'], fr['py'], flat)
    oc, _ = g.noise(g.vec(g.mul(panel, 3.1), g.mul(along, 0.8), 0.0), 1.0, detail=2.0)
    height = g.add(g.add(seam, rib), g.mul(oc, 0.03))
    _, rc = g.white(g.vec(panel, 1.0, 2.0))
    r0, _, _ = g.sep(rc)
    base = g.vscale(_keycol('roof_metal'), g.remap(r0, 0.0, 1.0, 0.94, 1.06))
    # raised seam: lighter folded top, darker crease where the rib meets the pan
    top = g.sub(1.0, g.ss(dist, 0.002, 0.005))
    crease = g.mul(g.ss(dist, 0.006, 0.0095), g.sub(1.0, g.ss(dist, 0.0105, 0.016)))
    base = g.vscale(base, g.mul(g.lerp(1.0, 1.45, top), g.lerp(1.0, 0.7, crease)))
    # PVDF/Kynar-painted steel: a matte dielectric paint film (low metallic), so at grazing angles
    # the plane reads as charcoal metal, not a glass mirror
    rough = g.add(0.58, g.mul(g.sub(r0, 0.5), 0.06))
    chalk, _ = g.noise(fr['P'], 1.8, detail=3.0)
    rough = g.add(rough, g.mul(g.sub(chalk, 0.5), 0.08))
    rough = g.lerp(rough, 0.48, top)
    nrm = g.normal(height=height, dist=0.02)
    return g.finish(g.bsdf(base, rough, 0.08, nrm, **{'Specular IOR Level': 0.4}))


def _porch_pavers(g):
    a, b, A, B = g.planar()
    sz = 24.0 * IN
    # centre the paver grid on the recessed porch (SCENE x 14.07..20.69, z 47.0..51.4 ft)
    a0 = (14.07 + 20.69) / 2 * FT - sz / 2
    b0 = -(47.0 + 51.4) / 2 * FT - sz / 2
    tid, d, _, _ = _grid(g, a, b, sz, sz, a0=a0, b0=b0)
    _, rc = g.white(tid)
    r0, r1, r2 = g.sep(rc)
    target = _keycol('porch_pavers')
    s = g.sample('concrete_floor_02', g.mad(r0, 13.0, a), g.mad(r1, 13.0, b), A, B, 2.0)
    if s:
        col = g.grade(s['color'], s['mean'], target, 0.3, sat=0.5)
        rough, pert = g.rough_from(s, 0.75, 0.3), s['pert']
    else:
        col, rough, pert = target, 0.75, None
    col = g.vscale(col, g.remap(r2, 0.0, 1.0, 0.95, 1.05))
    joint = g.sub(1.0, g.ss(d, 0.004, 0.0055))
    col = g.cmix(col, _hexlin('#6f6c66'), joint)
    height = g.ss(d, 0.004, 0.009)
    nrm = g.normal(pert, 0.6, height=height, dist=0.004)
    return g.finish(g.bsdf(col, g.lerp(rough, 0.95, joint), 0.0, nrm))


def _concrete_drive(g):
    a, b, A, B = g.planar()
    target = _keycol('concrete_drive')
    s = g.sample('brushed_concrete_03', a, b, A, B, 2.0)
    fr = g.frame()
    if s:
        col = g.grade(s['color'], s['mean'], target, 0.8, sat=0.5)
        rough, pert = g.rough_from(s, 0.85, 0.4), s['pert']
    else:
        col, rough, pert = target, 0.85, None
    n, _ = g.noise(fr['P'], 0.35, detail=3.0)
    col = g.vscale(col, g.remap(n, 0.3, 0.7, 0.95, 1.04))
    nrm = g.normal(pert, 1.0)
    return g.finish(g.bsdf(col, rough, 0.0, nrm))


def _concrete(g, key, contrast, rough, ramp=0.4, coat=0.0, nstr=0.8, tone=0.04):
    return _textured(g, key, 'concrete_floor_02', 2.0, contrast=contrast, sat=0.5, rough=rough, ramp=ramp,
                     nstr=nstr, coat=coat, coat_rough=0.2, tone_noise=tone)


def _grass(g):
    fr = g.frame()
    target = _keycol('grass_lawn')
    s = g.tri('leafy_grass', 2.0)
    if s:
        col = g.grade(s['color'], s['mean'], target, 1.25, sat=0.6)
        pert = s['pert']
    else:
        col, pert = target, None
    n1, _ = g.noise(fr['P'], 0.25, detail=3.0)
    n2, _ = g.noise(fr['P'], 1.3, detail=3.0)
    col = g.cmix(col, g.vm('MULTIPLY', col, (1.25, 1.1, 0.6)), g.mul(g.ss(n1, 0.5, 0.75), 0.6))
    col = g.vscale(col, g.remap(n2, 0.3, 0.7, 0.85, 1.12))
    fine, _ = g.noise(fr['P'], 400.0, detail=2.0)
    nrm = g.normal(pert, 0.8, height=fine, dist=0.002, bump=0.6)
    return g.finish(g.bsdf(col, 0.85, 0.0, nrm, **{'Sheen Weight': 0.3, 'Sheen Roughness': 0.4,
                                                    'Sheen Tint': (0.9, 1.0, 0.7, 1.0)}))


def _fence(g):
    a, b, A, B = g.planar(grain_knob=True)
    s = g.sample('ash_veneer', a, b, A, B, 1.0, grain='u', stretch=1.5, maps=('diffuse', 'nor_gl'))
    col = _keycol('fence_charcoal')
    if s:
        lum = g.grade(s['color'], s['mean'], (1.0, 1.0, 1.0), 1.5, sat=0.0)
        base = g.vm('MULTIPLY', g.cmix((1.0, 1.0, 1.0), lum, 0.35), col)
        pert = s['pert']
    else:
        base, pert = col, None
    nrm = g.normal(pert, 0.8)
    return g.finish(g.bsdf(base, 0.62, 0.0, nrm))


# ---------------------------------------------------------------------------------- metals etc.
def _stainless(g):
    fr = g.frame()
    a, b, A, B = g.planar()
    lines, _ = g.noise(g.vec(g.mul(a, 3.0), g.mul(b, 2500.0), 0.0), 1.0, detail=3.0, rough=0.6)
    lines2, _ = g.noise(g.vec(g.mul(a, 0.6), g.mul(b, 600.0), 0.0), 1.0, detail=2.0)
    smudge, _ = g.noise(fr['P'], 3.0, detail=3.0)
    base = g.vscale(_keycol('stainless'), g.remap(lines2, 0.3, 0.7, 0.96, 1.02))
    rough = g.add(g.add(0.26, g.mul(g.sub(lines, 0.5), 0.12)), g.mul(g.ss(smudge, 0.55, 0.8), 0.06))
    nrm = g.normal(height=lines, dist=0.00004)
    return g.finish(g.bsdf(base, rough, 1.0, nrm, **{'Anisotropic': 0.55, 'Tangent': A}))


def _powder(g, key, rough, metal=0.0, coat=0.0):
    """Powder coat / satin finishes: fine stipple bump, slight roughness variation."""
    fr = g.frame()
    n1, _ = g.noise(fr['P'], 1600.0, detail=2.0)
    n2, _ = g.noise(fr['P'], 4.0, detail=2.0)
    r = g.add(rough, g.mul(g.sub(n2, 0.5), 0.06))
    nrm = g.normal(height=n1, dist=0.00003)
    kw = {'Coat Weight': coat, 'Coat Roughness': 0.3} if coat else {}
    return g.finish(g.bsdf(_keycol(key), r, metal, nrm, **kw))


def _simple(g, key, rough=None, metal=None, **extra):
    from .materials import KEYS
    _, r0, m0, _ = KEYS[key]
    return g.finish(g.bsdf(_keycol(key), r0 if rough is None else rough, m0 if metal is None else metal, None, **extra))


def _led(g):
    bb = g.new('ShaderNodeBlackbody')
    g.put(bb.inputs['Temperature'], 3000.0)
    b = g.bsdf(_keycol('led_warm'), 0.5, 0.0, None)
    g.put(b.inputs['Emission Color'], bb.outputs[0])
    g.put(b.inputs['Emission Strength'], 8.0)
    return g.finish(b)


def _rug(g, key):
    fr = g.frame()
    col = _keycol(key)
    s = g.tri('hessian_230', 0.42, FABRIC_RES)
    if s:
        base = g.grade(s['color'], s['mean'], col, 0.6, sat=0.15)
        pert = s['pert']
    else:
        base, pert = col, None
    n, _ = g.noise(fr['P'], 1.2, detail=3.0)
    fl, _ = g.noise(fr['P'], 70.0, detail=2.0)
    base = g.vscale(base, g.mul(g.remap(n, 0.3, 0.7, 0.95, 1.04), g.remap(fl, 0.3, 0.7, 0.93, 1.05)))
    fuzz, _ = g.noise(fr['P'], 500.0, detail=2.0)
    nrm = g.normal(pert, 1.3, height=g.add(fuzz, g.mul(fl, 0.5)), dist=0.0012, bump=0.7)
    return g.finish(g.bsdf(base, 0.97, 0.0, nrm, **{'Sheen Weight': 0.6, 'Sheen Roughness': 0.5}))


# ================================================================================ dispatch table
def _maker(key):
    T = _textured
    table = {
        'paint_wall': lambda g: _paint(g, 'paint_wall'),
        'paint_ceiling': lambda g: _paint(g, 'paint_ceiling', peel=0.7),
        'paint_trim': lambda g: _paint(g, 'paint_trim', peel=0.8),
        'door_slab': lambda g: _paint(g, 'door_slab', peel=0.6),
        'paint_black': lambda g: _paint(g, 'paint_black', peel=0.8),
        'fascia_charcoal': lambda g: _paint(g, 'fascia_charcoal', peel=1.2),
        'plaster_white': lambda g: T(g, 'plaster_white', 'plastered_wall_04', 3.2, contrast=0.5, sat=0.3, ramp=0.2, nstr=0.35),
        'stucco': lambda g: T(g, 'stucco', 'white_stucco', 2.0, contrast=0.9, sat=0.4, ramp=0.2, nstr=1.0),
        'wood_cladding': _cladding,
        'roof_metal': _roof_metal,
        'black_aluminum': lambda g: _powder(g, 'black_aluminum', 0.42, metal=0.15),
        'oak_floor': _oak_floor,
        'tile_floor_bath': _tile_floor_bath,
        'tile_shower_floor': _tile_shower_floor,
        'concrete_garage': lambda g: _concrete(g, 'concrete_garage', 0.22, 0.45, ramp=0.3, coat=0.25, nstr=0.4),
        'porch_pavers': _porch_pavers,
        'concrete_drive': _concrete_drive,
        'foundation': lambda g: _concrete(g, 'foundation', 0.25, 0.9, ramp=0.3, nstr=0.9),
        'walnut_slab': lambda g: _veneer(g, 'walnut_slab', 'american_walnut_veneer', 1.0, 'u', False, 1.6, 0.42, coat=0.2),
        'walnut_door': lambda g: _veneer(g, 'walnut_door', 'walnut_veneer', 1.8, 'v', True, 1.4, 0.45, coat=0.2),
        'white_oak_veneer': lambda g: _veneer(g, 'white_oak_veneer', 'oak_veneer_03', 1.0, 'u', False, 1.6, 0.45, coat=0.1, stretch=1.3),
        'quartz_calacatta': _quartz_calacatta,
        'quartz_white': _quartz_white,
        'stone_feature': _stone_feature,
        'tile_wave_white': _tile_wave_white,
        'tile_wall_porcelain': _tile_wall_porcelain,
        'tile_fluted_black': _tile_fluted_black,
        'stainless': _stainless,
        'black_metal': lambda g: _powder(g, 'black_metal', 0.4, metal=0.5),
        'chrome': lambda g: _simple(g, 'chrome', 0.05, 1.0),
        'mirror': lambda g: _simple(g, 'mirror', 0.0, 1.0),
        'ceramic_white': lambda g: _simple(g, 'ceramic_white', 0.07, 0.0, **{'Coat Weight': 0.3, 'Coat Roughness': 0.03}),
        'led_warm': _led,
        'fabric_boucle': lambda g: T(g, 'fabric_boucle', 'curly_teddy_natural', 0.33, contrast=1.0, sat=0.4, ramp=0.2,
                                     nstr=1.0, res=FABRIC_RES, sheen=0.35, sheen_rough=0.5),
        'fabric_linen_white': lambda g: T(g, 'fabric_linen_white', 'rough_linen', 0.27, contrast=1.3, sat=0.0, ramp=0.2,
                                          nstr=0.8, res=FABRIC_RES, sheen=0.25, tone_noise=0.02),
        'fabric_linen_grey': lambda g: T(g, 'fabric_linen_grey', 'rough_linen', 0.27, contrast=1.3, sat=0.0, ramp=0.2,
                                         nstr=0.8, res=FABRIC_RES, sheen=0.25, tone_noise=0.02),
        'fabric_mustard': lambda g: T(g, 'fabric_mustard', 'velour_velvet', 0.28, contrast=1.2, sat=0.5, ramp=0.2,
                                      nstr=0.6, res=FABRIC_RES, sheen=1.0, sheen_rough=0.35),
        'fabric_sage': lambda g: T(g, 'fabric_sage', 'rough_linen', 0.27, contrast=1.3, sat=0.0, ramp=0.2,
                                   nstr=0.8, res=FABRIC_RES, sheen=0.3),
        'leather_tan': lambda g: T(g, 'leather_tan', 'brown_leather', 0.5, contrast=0.35, sat=0.8, rough=0.48, ramp=0.5,
                                   nstr=0.6, res=FABRIC_RES, coat=0.15, coat_rough=0.35),
        'rug_wool_cream': lambda g: _rug(g, 'rug_wool_cream'),
        'rug_wool_grey': lambda g: _rug(g, 'rug_wool_grey'),
        'grass_lawn': _grass,
        'gravel_dark': lambda g: T(g, 'gravel_dark', 'gravel_stones', 2.0, contrast=1.0, sat=0.5, ramp=0.4, nstr=1.0),
        'pebbles_river': lambda g: T(g, 'pebbles_river', 'dry_river_pebbles', 2.0, contrast=0.65, sat=0.35, ramp=0.5,
                                     nstr=1.0),
        'soil_mulch': lambda g: T(g, 'soil_mulch', 'wood_chips', 2.0, contrast=1.1, sat=0.8, ramp=0.3, nstr=1.0),
        'ipe_deck': _ipe_deck,
        'fence_charcoal': _fence,
        'concrete_paver': lambda g: _concrete(g, 'concrete_paver', 0.3, 0.8, ramp=0.3, nstr=0.7),
    }
    return table.get(key)


def build(key):
    """Textured PBR material 'M_<key>' or None (caller falls back to the flat version)."""
    if bpy is None or key in GLASS:
        return None
    mk = _maker(key)
    if mk is None:
        return None
    g = None
    try:
        g = _G(key)
        return mk(g)
    except Exception:
        print(f'[materials_pbr] {key}: build failed, using flat fallback')
        traceback.print_exc()
        try:
            if g is not None and g.m is not None:
                bpy.data.materials.remove(g.m)
        except Exception:
            pass
        return None
