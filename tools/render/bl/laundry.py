"""Laundry closet contents (runs inside Blender, called by bl/revisions.laundry_closet after the warp).

Everything here is authored directly in new-plan SCENE feet (x west->east, y up, z rear->street), from the
numbers in bl/revision_spec.py, so nothing is reshaped by bl/warp.py:

* a stacked front-load pair: washer below (detergent drawer, kick panel with the drain-filter cover, feet),
  dryer above, a stainless stacking trim between them. Each body is 27 x 30 1/4 x 39 in: white enamel cabinet,
  rounded door panel and control strip, a round door (chrome bezel, dark inner frame, dark tinted glass, grip),
  a chrome-ringed dial, a black display with lit digits and a row of buttons;
* on the back wall: a recessed washer outlet box (the recess itself is cut by the revision) with hot / cold
  valves, braided supply hoses and the corrugated drain hose, the dryer's 4 in foil vent duct rising behind
  the stack into a wall collar, a 240 V receptacle with the dryer cord;
* a small flush LED ceiling light;
* the door's lever sets and hinge knuckles (the leaf itself is built by the revision).

Naming / collections (see the bake rules in bake_web.classify): every object is called 'laundry closet ...'
and lives in 'kd_laundry' under 'zone_kitchen_dining'. "closet" keeps the pieces in the always-visible 'base'
class of the web model and gives the washer a walk-collision box; nothing here is in 'openings' (a glass-named
material there would get a light portal), and the hatch glass material is not called "glass" (the bake would
export it as a transparent pane). The units' round doors are called "hatch" in object names: bake_web.WALL_PART
files anything named "door" under the walls.
"""
import math

import bmesh
import bpy
from mathutils import Vector

from . import revision_spec as S
from .common import FT

COLL, ZONE = 'kd_laundry', 'zone_kitchen_dining'
LIGHTS = 'kd_lights'
PFX = 'Z_laundry_'
N = 'laundry closet'

DOOR_R = 0.80            # round door: outer radius of the chrome bezel (19 in door on a 27 in front)
DOOR_V = 1.60            # door centre above the unit's bottom
STRIP_H = 0.47           # control strip height
KICK_H = 0.42            # washer kick panel top


def P(x, y, z):
    """SCENE feet -> Blender metres."""
    return (x * FT, -z * FT, y * FT)


def _srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def _mat(name, color, rough, metal=0.0, coat=0.0, spec=0.5):
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = _srgb(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.04
    m.diffuse_color = _srgb(color)
    return m


def _glow(name, color, strength):
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = tuple(color) + (1.0,)
    em.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


class Kit:
    """Mesh helpers in SCENE feet; every object goes into one collection."""

    def __init__(self, ctx, coll=COLL, parent=ZONE):
        self.ctx = ctx
        self.coll = coll
        ctx.coll(coll, parent)
        self.objects = []

    def m(self, mat):
        return self.ctx.mat(mat) if isinstance(mat, str) else mat

    def _obj(self, name, bm, mat, smooth=True, sharp=40.0):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(self.m(mat))
        if smooth:
            me.shade_smooth()
            try:
                me.set_sharp_from_angle(angle=math.radians(sharp))
            except Exception:
                pass
        ob = bpy.data.objects.new(name, me)
        self.ctx.coll(self.coll).objects.link(ob)
        self.objects.append(ob)
        return ob

    def box(self, name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0, seg=3):
        ob = self.ctx.box(name, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1),
                          self.m(mat), self.coll, bevel, seg)
        self.objects.append(ob)
        return ob

    def boxes(self, name, items, mat, bevel=0.0):
        """Several axis-aligned boxes [(x0, x1, y0, y1, z0, z1), ...] as one mesh."""
        bm = bmesh.new()
        for x0, x1, y0, y1, z0, z1 in items:
            vs = [bm.verts.new(P(x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
            for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
                bm.faces.new([vs[i] for i in q])
        ob = self._obj(name, bm, mat, smooth=False)
        if bevel:
            self.ctx.add_bevel(ob, bevel, 2)
        return ob

    def revolve(self, name, prof, c, axis, mat, segs=72, sharp=40.0):
        """Surface of revolution around the line through SCENE point c along `axis` ('y' = up, 'n' = north, the
        -z direction the unit fronts face). prof = [(r, d), ...]: radius and distance along the axis from c.
        Give a closed outline (start and end on the axis, or first point == last point) so the solid is closed."""
        cx, cy, cz = c
        bm = bmesh.new()
        rings = []
        for r, d in prof:
            if r <= 1e-6:
                rings.append([bm.verts.new(P(cx, cy + d, cz) if axis == 'y' else P(cx, cy, cz - d))])
                continue
            ring = []
            for k in range(segs):
                a = 2 * math.pi * k / segs
                if axis == 'y':
                    ring.append(bm.verts.new(P(cx + r * math.cos(a), cy + d, cz + r * math.sin(a))))
                else:
                    ring.append(bm.verts.new(P(cx + r * math.cos(a), cy + r * math.sin(a), cz - d)))
            rings.append(ring)
        for A, B in zip(rings, rings[1:]):
            if len(A) == 1 and len(B) == 1:
                continue
            for k in range(segs):
                k2 = (k + 1) % segs
                if len(A) == 1:
                    bm.faces.new((A[0], B[k], B[k2]))
                elif len(B) == 1:
                    bm.faces.new((A[k], A[k2], B[0]))
                else:
                    bm.faces.new((A[k], A[k2], B[k2], B[k]))
        return self._obj(name, bm, mat, sharp=sharp)

    def cyl(self, name, p0, p1, r, mat, verts=24):
        """Capped cylinder between two SCENE points."""
        a, b = Vector(P(*p0)), Vector(P(*p1))
        d = b - a
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r * FT, radius2=r * FT, depth=d.length)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        try:
            me.set_sharp_from_angle(angle=math.radians(40))
        except Exception:
            pass
        me.materials.append(self.m(mat))
        ob = bpy.data.objects.new(name, me)
        ob.location = (a + b) / 2
        ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        self.ctx.coll(self.coll).objects.link(ob)
        self.objects.append(ob)
        return ob

    def tube(self, name, pts, r, mat, segs=16, rib=None, amp=0.0, smooth_path=2):
        """Round tube along SCENE points (corner-cut `smooth_path` times). rib = spacing (ft) of rings whose
        radius alternates by +-amp (corrugated hose, foil duct)."""
        path = [Vector(p) for p in pts]
        for _ in range(smooth_path):                       # Chaikin corner cutting, ends kept
            q = [path[0]]
            for a, b in zip(path, path[1:]):
                q += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
            q.append(path[-1])
            path = q
        step = rib if rib else max(r * 0.9, 0.02)
        res, carry = [path[0]], 0.0                        # resample at equal spacing
        for a, b in zip(path, path[1:]):
            L = (b - a).length
            t = step - carry
            while t <= L:
                res.append(a.lerp(b, t / L))
                t += step
            carry = (carry + L) % step
        if (res[-1] - path[-1]).length > step * 0.3:
            res.append(path[-1])
        pb = [Vector(P(*p)) for p in res]
        bm = bmesh.new()
        rings, nrm = [], None
        for i, p in enumerate(pb):
            tan = (pb[min(i + 1, len(pb) - 1)] - pb[max(i - 1, 0)]).normalized()
            if nrm is None:
                nrm = tan.orthogonal().normalized()
            else:
                nrm = (nrm - tan * nrm.dot(tan)).normalized()
            bi = tan.cross(nrm)
            rr = r * (1.0 + (amp if i % 2 else -amp)) * FT if rib else r * FT
            rings.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * k / segs) + bi * math.sin(2 * math.pi * k / segs)) * rr)
                          for k in range(segs)])
        for A, B in zip(rings, rings[1:]):
            for k in range(segs):
                k2 = (k + 1) % segs
                bm.faces.new((A[k], A[k2], B[k2], B[k]))
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
        return self._obj(name, bm, mat, sharp=75.0 if rib else 40.0)


# ------------------------------------------------------------------------------------------ the units
_SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc',
        '8': 'abcdefg', '9': 'abfgcd'}


def _digits(text, h):
    """Seven-segment text as rectangles (u0, u1, v0, v1) in a frame with u to the right and v up; -> (rects, width)."""
    w, s = h * 0.52, h * 0.13
    seg = {'a': (s * 0.6, w - s * 0.6, h - s, h), 'd': (s * 0.6, w - s * 0.6, 0.0, s),
           'g': (s * 0.6, w - s * 0.6, h / 2 - s / 2, h / 2 + s / 2),
           'b': (w - s, w, h / 2 + s * 0.35, h - s * 0.6), 'c': (w - s, w, s * 0.6, h / 2 - s * 0.35),
           'f': (0.0, s, h / 2 + s * 0.35, h - s * 0.6), 'e': (0.0, s, s * 0.6, h / 2 - s * 0.35)}
    out, u = [], 0.0
    for ch in text:
        if ch == ':':
            for v in (h * 0.28, h * 0.66):
                out.append((u, u + s, v, v + s))
            u += s + h * 0.2
            continue
        for k in _SEG[ch]:
            a, b, c, d = seg[k]
            out.append((u + a, u + b, c, d))
        u += w + h * 0.2
    return out, u - h * 0.2


def _unit(kit, tag, box, washer, time_text):
    """One front-load unit in the body box (x0, x1, y0, y1, z0, z1); its front is the z0 face and looks north.
    Panel positions use the viewer's frame: u from the viewer's left (the east edge) to the right, v up from the
    unit's bottom, d out of the front."""
    x0, x1, y0, y1, zf, zb = box
    W, H = x1 - x0, y1 - y0
    nm = f'{N} {tag}'
    enamel = _mat('enamel_white', '#f0f1f0', 0.22, coat=0.35)
    dark = _mat('trim_dark', '#1a1b1d', 0.3)
    tint = _mat('porthole_tint', '#030407', 0.03, spec=0.8, coat=1.0)       # dark door glass (opaque: reads as black glass)
    display = _mat('display_black', '#040404', 0.05, coat=1.0)
    rubber = _mat('rubber_black', '#101010', 0.7)

    def fb(name, u0, u1, v0, v1, d0, d1, mat, bevel=0.0, seg=3):
        return kit.box(f'{nm} {name}', x1 - u1, x1 - u0, y0 + v0, y0 + v1, zf - d1, zf - d0, mat, bevel, seg)

    vb = 0.07 if washer else 0.0                       # the washer stands on levelling feet
    if washer:
        for i, (fx, fz) in enumerate(((x0 + 0.2, zf + 0.22), (x1 - 0.2, zf + 0.22), (x0 + 0.2, zb - 0.22), (x1 - 0.2, zb - 0.22))):
            kit.revolve(f'{nm} foot {i}', [(0.0, 0.0), (0.085, 0.0), (0.085, 0.02), (0.05, 0.035), (0.05, vb + 0.01), (0.0, vb + 0.01)],
                        (fx, y0, fz), 'y', rubber, 24)
    # cabinet, rounded door panel and control strip (a fine joint between them), kick panel on the washer
    fb('cabinet', 0.0, W, vb, H, -(zb - zf), -0.045, enamel, 0.012, 2)
    panel_v0 = KICK_H if washer else 0.012
    fb('front panel', 0.0, W, panel_v0, H - STRIP_H, -0.06, 0.0, enamel, 0.026, 5)
    fb('control strip', 0.0, W, H - STRIP_H + 0.007, H, -0.06, 0.0, enamel, 0.026, 5)
    if washer:
        fb('kick panel', 0.012, W - 0.012, vb, KICK_H - 0.007, -0.06, -0.02, enamel, 0.01, 2)
        fb('filter cover', 0.15, 0.55, vb + 0.085, KICK_H - 0.085, -0.03, -0.012, enamel, 0.012, 3)
        fb('filter cover notch', 0.30, 0.40, KICK_H - 0.125, KICK_H - 0.105, -0.02, -0.0095, dark, 0.004, 2)
    # round door: chrome bezel, dark inner frame, domed dark glass, grip on the opening side
    c = ((x0 + x1) / 2, y0 + DOOR_V, zf)
    R = DOOR_R
    kit.revolve(f'{nm} hatch bezel', [(R, 0.0), (R, 0.03), (R - 0.013, 0.052), (R - 0.045, 0.066), (R - 0.1, 0.07),
                                    (R - 0.125, 0.066), (R - 0.135, 0.056), (R - 0.135, 0.0), (R, 0.0)], c, 'n', 'chrome', 96)
    ri = R - 0.135
    kit.revolve(f'{nm} hatch frame', [(ri, 0.0), (ri, 0.054), (ri - 0.01, 0.06), (ri - 0.105, 0.064), (ri - 0.12, 0.058),
                                    (ri - 0.125, 0.05), (ri - 0.125, 0.0), (ri, 0.0)], c, 'n', dark, 96)
    rg = ri - 0.125
    bowl = [(rg * 0.84, 0.068), (rg * 0.80, 0.063), (rg * 0.76, 0.071)] if washer else []     # the washer's inner bowl rim
    kit.revolve(f'{nm} hatch window', [(0.0, 0.0), (rg, 0.0), (rg, 0.048), (rg - 0.02, 0.056)] + bowl +
                [(rg * 0.6, 0.081), (rg * 0.3, 0.09), (0.0, 0.093)], c, 'n', tint, 96, sharp=25.0)
    side = 1.0 if washer else -1.0                     # washer: hinged at the viewer's left, grip on the right
    uc = W / 2 + side * (R - 0.066)
    fb('hatch grip', uc - 0.06, uc + 0.06, DOOR_V - 0.19, DOOR_V + 0.19, 0.02, 0.082, dark, 0.022, 4)
    # control strip: [detergent drawer] | dial | display with digits and buttons
    vs = H - STRIP_H / 2 + 0.003
    if washer:
        fb('detergent drawer', 0.09, 0.80, vs - 0.155, vs + 0.155, -0.01, 0.009, enamel, 0.009, 3)
        fb('detergent drawer pull', 0.24, 0.65, vs - 0.137, vs - 0.105, 0.0, 0.0115, dark, 0.004, 2)
    dial_c = (x1 - W / 2, y0 + vs, zf)
    kit.revolve(f'{nm} dial ring', [(0.0, 0.0), (0.172, 0.0), (0.172, 0.022), (0.160, 0.04), (0.14, 0.044), (0.0, 0.044)],
                dial_c, 'n', 'chrome', 64)
    kit.revolve(f'{nm} dial knob', [(0.0, 0.0), (0.132, 0.0), (0.132, 0.082), (0.122, 0.094), (0.105, 0.098), (0.0, 0.098)],
                dial_c, 'n', dark, 64)
    fb('dial mark', W / 2 - 0.008, W / 2 + 0.008, vs + 0.07, vs + 0.12, 0.09, 0.0995, _glow('dial_mark', (0.85, 0.93, 1.0), 2.5))
    du0, du1 = 1.40, W - 0.11
    fb('display', du0, du1, vs - 0.125, vs + 0.125, -0.01, 0.007, display, 0.006, 2)
    rects, tw = _digits(time_text, 0.10)
    u_d, v_d = du0 + 0.09, vs - 0.05
    kit.boxes(f'{nm} display digits',
              [(x1 - (u_d + b), x1 - (u_d + a), y0 + v_d + c2, y0 + v_d + d2, zf - 0.0085, zf - 0.0068) for a, b, c2, d2 in rects],
              _glow('display_glow', (0.72, 0.9, 1.0), 4.0))
    nb = 4
    for i in range(nb):
        bu = u_d + tw + 0.085 + i * 0.058
        if bu > du1 - 0.04:
            break
        kit.revolve(f'{nm} button {i}', [(0.0, 0.0), (0.019, 0.0), (0.019, 0.004), (0.015, 0.0065), (0.0, 0.0065)],
                    (x1 - bu, y0 + vs - 0.045, zf - 0.007), 'n', 'chrome', 20)
        kit.revolve(f'{nm} button lamp {i}', [(0.0, 0.0), (0.0065, 0.0), (0.0065, 0.0015), (0.0, 0.0015)],
                    (x1 - bu, y0 + vs + 0.045, zf - 0.007), 'n', _glow('display_glow', (0.72, 0.9, 1.0), 4.0), 12)
    return {'hatch centre': (round(c[0], 3), round(c[1], 3), round(zf, 3))}


def _stack(kit, units):
    w, d = units['washer'], units['dryer']
    out = {'washer': _unit(kit, 'washer', w, True, '0:48'), 'dryer': _unit(kit, 'dryer', d, False, '1:05')}
    # stacking kit: a brushed strip between the two cabinets, set back from the fronts
    kit.box(f'{N} stacking trim', w[0] + 0.004, w[1] - 0.004, w[3], d[2], w[4] + 0.014, w[5] - 0.02, 'stainless', 0.004, 2)
    return out


# ------------------------------------------------------------------------------- hookups on the back wall
def _hookups(kit, units, recess):
    """Washer outlet box in the wall recess `recess` = (x0, x1, y0, y1, depth), supply and drain hoses, the dryer's
    vent duct and wall collar, the dryer receptacle and cord. The back wall's face is LAUNDRY_CLEAR[3]."""
    wall = S.LAUNDRY_CLEAR[3]
    w, d = units['washer'], units['dryer']
    back = w[5]                                         # the cabinets' rear face
    white = _mat('plastic_white', '#ecece8', 0.35)
    chrome, steel = 'chrome', 'stainless'
    bx0, bx1, by0, by1, dep = recess
    t, fl = 0.012, 0.07
    # box liner (five thin panels inside the recess) and the face flange around it, standing 1/8 in off the wall
    kit.boxes(f'{N} outlet box', [(bx0, bx1, by0, by1, wall + dep - t, wall + dep),
                                  (bx0, bx0 + t, by0, by1, wall, wall + dep), (bx1 - t, bx1, by0, by1, wall, wall + dep),
                                  (bx0, bx1, by0, by0 + t, wall, wall + dep), (bx0, bx1, by1 - t, by1, wall, wall + dep),
                                  (bx0 - fl, bx1 + fl, by1 - 0.004, by1 + fl, wall - 0.012, wall + 0.004),
                                  (bx0 - fl, bx1 + fl, by0 - fl, by0 + 0.004, wall - 0.012, wall + 0.004),
                                  (bx0 - fl, bx0 + 0.004, by0, by1, wall - 0.012, wall + 0.004),
                                  (bx1 - 0.004, bx1 + fl, by0, by1, wall - 0.012, wall + 0.004)], white, 0.004)
    zv = wall + dep * 0.52
    ports = [(bx0 + 0.15, _mat('valve_blue', '#1f5fae', 0.4), w[0] + 0.24), (bx0 + 0.34, _mat('valve_red', '#b3261e', 0.4), w[0] + 0.42)]
    for i, (xv, col, xw) in enumerate(ports):
        kit.cyl(f'{N} valve body {i}', (xv, by1 - t, zv), (xv, by1 - 0.21, zv), 0.034, chrome, 20)
        kit.box(f'{N} valve handle {i}', xv - 0.02, xv + 0.02, by1 - 0.125, by1 - 0.095, zv - 0.14, zv - 0.02, col, 0.008, 2)
        kit.cyl(f'{N} hose nut {i}', (xv, by1 - 0.20, zv), (xv, by1 - 0.28, zv), 0.047, steel, 12)
        kit.tube(f'{N} supply hose {i}', [(xv, by1 - 0.27, zv), (xv, by0 + 0.2, zv - 0.01), (xv, by0 + 0.09, wall - 0.01),
                                          (xv + 0.02, by0 - 0.12, wall - 0.09), ((xv + xw) / 2, w[3] + 0.05, wall - 0.13),
                                          (xw, w[3] - 0.1, wall - 0.15), (xw, w[3] - 0.3, back + 0.12), (xw, w[3] - 0.32, back - 0.02)],
                 0.03, steel, 12)
    # drain: the washer's corrugated hose loops up behind the stack and hooks into the box's standpipe socket
    xd = bx0 + 0.53
    kit.revolve(f'{N} drain socket', [(0.0, 0.0), (0.085, 0.0), (0.085, 0.03), (0.06, 0.03), (0.06, 0.004), (0.0, 0.004)],
                (xd, by0 + t, zv), 'y', _mat('abs_black', '#0c0c0c', 0.45), 24)
    xo = w[1] - 0.5
    kit.tube(f'{N} drain hose', [(xo, w[3] - 0.55, back - 0.02), (xo, w[3] - 0.5, back + 0.14), (xo - 0.25, w[3] - 0.1, back + 0.2),
                                 (xd + 0.5, by0 + 0.35, wall - 0.14), (xd + 0.09, by1 - 0.09, wall - 0.05), (xd, by1 - 0.13, zv - 0.02),
                                 (xd, by0 + 0.2, zv), (xd, by0 + 0.02, zv)], 0.042, _mat('hose_grey', '#8e9296', 0.55), 14, rib=0.022, amp=0.07)
    # dryer vent: 4 in foil duct from the dryer's rear outlet, up behind it, into a wall collar above the stack
    xv, r = d[0] + 1.44, 0.167
    y_out, y_col = d[2] + 0.46, 7.25                 # the collar's flange starts below 7 ft: the web bake files anything that
                                                     # starts higher under "ceiling" (hidden in the dollhouse)
    zc = (back + wall) / 2
    br = zc - back                                      # bend radius = half the gap
    pts = [(xv, y_out, back - 0.08), (xv, y_out, back)]
    pts += [(xv, y_out + br - br * math.cos(a), back + br * math.sin(a)) for a in (math.radians(k) for k in range(15, 91, 15))]
    pts += [(xv, y_col - br + br * math.sin(a), wall - br * math.cos(a)) for a in (math.radians(k) for k in range(0, 91, 15))]
    pts.append((xv, y_col, wall + 0.03))
    foil = _mat('duct_foil', '#d2d4d5', 0.3, metal=1.0)
    kit.tube(f'{N} dryer vent duct', pts, r - 0.006, foil, 28, rib=0.03, amp=0.035, smooth_path=0)
    kit.revolve(f'{N} dryer vent collar', [(r + 0.012, 0.0), (r + 0.11, 0.0), (r + 0.11, 0.012), (r + 0.03, 0.016),
                                           (r + 0.012, 0.03), (r + 0.012, 0.0)], (xv, y_col, wall), 'n', white, 48)
    kit.revolve(f'{N} dryer vent clamp', [(r + 0.004, 0.0), (r + 0.016, 0.0), (r + 0.016, 0.05), (r + 0.004, 0.05), (r + 0.004, 0.0)],
                (xv, y_col - br - 0.12, zc), 'y', steel, 40)
    # 240 V dryer receptacle on the back wall beside the stack, cord from the dryer's back
    ex = S.LAUNDRY_CLEAR[1] - 0.2
    kit.box(f'{N} dryer receptacle plate', ex - 0.13, ex + 0.13, 3.62, 4.0, wall - 0.012, wall + 0.002, white, 0.006, 2)
    grey = _mat('cord_grey', '#3b3d40', 0.5)
    kit.cyl(f'{N} dryer plug', (ex, 3.81, wall - 0.012), (ex, 3.81, wall - 0.10), 0.085, grey, 24)
    kit.tube(f'{N} dryer cord', [(ex, 3.78, wall - 0.09), (ex, 3.6, wall - 0.17), (ex - 0.1, 3.42, wall - 0.2),
                                 (d[1] - 0.25, d[2] + 0.3, back + 0.1), (d[1] - 0.3, d[2] + 0.36, back - 0.02)], 0.024, grey, 10)
    return {'outlet box': (bx0, bx1, by0, by1), 'vent collar': (round(xv, 3), y_col), 'receptacle': (round(ex, 3), 3.81)}


# ------------------------------------------------------------------------------------- ceiling light
def _ceiling_light(ctx, x, z, ceil):
    """Flush 6 in LED disc on the ceiling: white trim, glowing lens, a soft point lamp under it."""
    from . import lighting
    kit = Kit(ctx, LIGHTS)
    r, drop = 0.26, 0.06
    kit.revolve(f'{N} ceiling light trim', [(0.0, 0.0), (r, 0.0), (r, -drop * 0.6), (r - 0.02, -drop), (r - 0.035, -drop),
                                           (r - 0.035, -drop * 0.5), (0.0, -drop * 0.5)], (x, ceil, z), 'y', 'paint_trim', 48)
    kit.revolve(f'{N} ceiling light lens', [(0.0, -drop * 0.5), (r - 0.036, -drop * 0.5), (r - 0.036, -drop * 0.93),
                                           (r * 0.5, -drop * 1.02), (0.0, -drop * 1.05)], (x, ceil, z), 'y',
                lighting.emitter('laundry_flush', 3500, 6.0), 48)
    ld = bpy.data.lights.new(f'{N} ceiling light', 'POINT')
    ld.energy = 12.0
    ld.color = lighting.kelvin_rgb(3500)
    ld.shadow_soft_size = 0.22 * FT
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = P(x, ceil - drop - 0.12, z)
    try:                                               # the lens is what the camera and reflections see
        lo.visible_camera = False
        lo.visible_glossy = False
    except AttributeError:
        pass
    ctx.coll(LIGHTS).objects.link(lo)
    return lo


# -------------------------------------------------------------------------------------- door hardware
def door_hardware(ctx, leaf, coll):
    """Lever sets on both faces of the leaf (dict from revision_spec.laundry_leaf) and three butt-hinge knuckles on
    its pin axis, in the house's black hardware. Works at any opening angle: the knuckles stand in the corner
    between the leaf's outer face and the jamb liner, where the pins of an outward-opening door show."""
    kit = Kit(ctx, coll, None)
    (ox, oz), (ax, az), (tx, tz) = leaf['corner'], leaf['along'], leaf['through']
    px, pz = leaf['pivot']
    w, _, th = leaf['size']

    def pt(u, y, v):                                   # u along the leaf from its hinge edge, v through it from its outer face
        return (ox + ax * u + tx * v, y, oz + az * u + tz * v)
    ul, yl = w - 0.23, 3.0                             # 2 3/4 in backset, 36 in high
    for tag, v0, sgn in (('outer', 0.0, -1.0), ('inner', th, 1.0)):
        kit.cyl(f'Laundry closet door lever rose {tag}', pt(ul, yl, v0), pt(ul, yl, v0 + sgn * 0.022), 0.088, 'black_metal', 32)
        kit.cyl(f'Laundry closet door lever neck {tag}', pt(ul, yl, v0 + sgn * 0.02), pt(ul, yl, v0 + sgn * 0.15), 0.03, 'black_metal', 20)
        kit.cyl(f'Laundry closet door lever {tag}', pt(ul + 0.025, yl, v0 + sgn * 0.135), pt(ul - 0.36, yl, v0 + sgn * 0.135), 0.024,
                'black_metal', 20)
    r = 0.021                                          # 1/2 in barrel, 3 1/2 in hinges with ball tips
    for i, yh in enumerate((0.75, 3.3, 5.85)):
        kit.cyl(f'Laundry closet door hinge {i}', (px, yh - 0.146, pz), (px, yh + 0.146, pz), r, 'black_metal', 20)
        for k, (ya, yb) in enumerate(((yh - 0.146, yh - 0.168), (yh + 0.146, yh + 0.168))):
            kit.revolve(f'Laundry closet door hinge {i} tip {k}', [(0.0, 0.0), (r * 0.8, 0.0), (r * 0.62, (yb - ya) * 0.6), (0.0, yb - ya)],
                        (px, ya, pz), 'y', 'black_metal', 16)
    return len(kit.objects)


# --------------------------------------------------------------------------------------------- build
def build(ctx, recess=None, ceil=None):
    """Stacked pair, hookups and the ceiling light. recess = (x0, x1, y0, y1, depth) of the outlet-box recess the
    revision cut into the back wall (None: no outlet box). Returns the placed boxes for the build log."""
    kit = Kit(ctx)
    units = S.laundry_units()
    res = {'units': {k: tuple(round(v, 3) for v in b) for k, b in units.items()}}
    res.update(_stack(kit, units))
    if recess:
        res['hookups'] = _hookups(kit, units, recess)
    lx, lz = S.LAUNDRY_LIGHT
    _ceiling_light(ctx, lx, lz, S.LAUNDRY_CEILING if ceil is None else ceil)
    res['light'] = (round(lx, 3), round(lz, 3))
    res['objects'] = len(kit.objects)
    return res
