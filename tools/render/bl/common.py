"""Shared context and geometry helpers for the Blender build (runs inside Blender).

Coordinate contract
-------------------
SCENE data (tools/render/data/scene.json) is in FEET, Y-up, right-handed:
  x = west -> east, y = up, z = rear/north (garden, z=0) -> front/south (street, z~54).
Blender is METERS, Z-up. Mapping:  SCENE (x, y, z) ft  ->  Blender (x, -z, y) * 0.3048.
A SCENE rotation `rot` (radians about +Y) becomes rotation_euler.z = rot in Blender.

Every helper in this module that takes coordinates uses SCENE feet so room modules can
work directly from the plan numbers in the audit (rooms, walls, windows, nodes).
"""
import json
import math
import os
import re

import bmesh
import bpy
from mathutils import Matrix, Vector

FT = 0.3048
RENDER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tools/render
DATA_DIR = os.path.join(RENDER_DIR, 'data')
CACHE_DIR = os.environ.get('TG_CACHE', os.path.join(RENDER_DIR, '.cache'))


def ft2bl(x, y, z):
    """SCENE feet point -> Blender meters Vector."""
    return Vector((x * FT, -z * FT, y * FT))


def bl2ft(v):
    """Blender meters Vector -> SCENE feet (x, y, z)."""
    return (v.x / FT, v.z / FT, -v.y / FT)


# The house is built on the concept plan (the frozen pre-PDF SCENE) and then carried onto the
# architect's plan by bl/warp.py; everything after the build (renders, bake) uses DATA_DIR.
CONCEPT_DIR = os.path.join(DATA_DIR, 'concept')


def _load(name):
    path = os.path.join(CONCEPT_DIR, name)
    if not os.path.exists(path):
        path = os.path.join(DATA_DIR, name)
    with open(path) as f:
        return json.load(f)


class Ctx:
    """Everything a build module needs. Create once per build: ctx = Ctx()."""

    def __init__(self):
        self.scene = _load('scene.json')
        self.objs = self.scene['objects']
        cls = _load('scene_classification.json')
        self.cls = cls['objects']            # str(index) -> {room, role, group, name, detail, keep, aabb_ft, ...}
        self.rooms = cls['meta']['rooms']    # room key -> {nodes, bounds_ft_x0x1z0z1, source}
        self.prims = _load('primitives.json')
        self.meas = _load('measurements.json')
        self.nodes = {n['id']: n for n in self.scene['tour']['nodes']}
        self._mats = {}
        self._colls = {}
        self.stats = {}

    # ------------------------------------------------------------------ lookup
    def info(self, idx):
        return self.cls[str(idx)]

    def find(self, room=None, role=None, detail=None, group=None, name=None, keep=None):
        """Indices of SCENE objects matching all given filters.
        `name` and `detail` are regexes (re.search); others exact or a tuple/set of allowed values."""
        def ok(val, want):
            if want is None:
                return True
            if isinstance(want, (tuple, list, set, frozenset)):
                return val in want
            return val == want
        out = []
        for i, o in enumerate(self.objs):
            c = self.cls[str(i)]
            if not ok(c['room'], room) or not ok(c['role'], role) or not ok(o['group'], group) or not ok(c['keep'], keep):
                continue
            if detail is not None and not re.search(detail, c['detail']):
                continue
            if name is not None and not re.search(name, o['name']):
                continue
            out.append(i)
        return out

    def aabb(self, idx):
        """[x0, x1, y0, y1, z0, z1] feet of a SCENE object (rotated footprint AABB)."""
        return self.cls[str(idx)]['aabb_ft']

    def room_bounds(self, room):
        """(x0, x1, z0, z1) feet of a room region (clear interior)."""
        return tuple(self.rooms[room]['bounds_ft_x0x1z0z1'])

    # ------------------------------------------------------------- collections
    def coll(self, name, parent=None):
        if name in self._colls:
            return self._colls[name]
        c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        par = self.coll(parent) if parent else bpy.context.scene.collection
        if c.name not in par.children:
            par.children.link(c)
        self._colls[name] = c
        return c

    # ---------------------------------------------------------------- materials
    def mat(self, key):
        """Material from the shared library (bl/materials.py). Always returns a material."""
        if key not in self._mats:
            from . import materials
            self._mats[key] = materials.get(key)
        return self._mats[key]

    # --------------------------------------------------------- SCENE geometry
    def original_mesh_data(self, idx):
        """(verts, faces) in Blender object-local meters (scaled, not rotated/translated)
        for SCENE object idx, reproducing the app's primitives exactly."""
        o = self.objs[idx]
        sx, sy, sz = o['s']
        shape = o['shape']
        if shape == 'box':
            hx, hy, hz = sx / 2 * FT, sz / 2 * FT, sy / 2 * FT   # blender local: x, y(=-z), z(=y)
            v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
                 (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
            f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            return v, f
        if shape == 'mesh':
            flat = o['geometry']['v']
        else:
            flat = self.prims[shape]['v']
        verts, faces, index = [], [], {}
        for t in range(0, len(flat), 9):
            tri = []
            for k in range(3):
                a, b, d = flat[t + 3 * k:t + 3 * k + 3]
                p = (round(a * sx * FT, 6), round(-d * sz * FT, 6), round(b * sy * FT, 6))
                if p not in index:
                    index[p] = len(verts)
                    verts.append(p)
                tri.append(index[p])
            if len(set(tri)) == 3:
                faces.append(tuple(tri))
        return verts, faces

    def import_original(self, idx, mat=None, coll='shell', name=None, smooth=None):
        """Create a Blender object reproducing SCENE object idx exactly.
        mat: material key (str), bpy Material, or None (grey)."""
        o = self.objs[idx]
        verts, faces = self.original_mesh_data(idx)
        me = bpy.data.meshes.new(name or f'{idx:04d} {o["name"]}'[:60])
        me.from_pydata(verts, [], faces)
        me.validate(clean_customdata=False)
        if smooth is None:
            smooth = o['shape'] in ('cylinder', 'sphere')
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(me.name, me)
        ob.location = ft2bl(*o['p'])
        ob.rotation_euler = (0, 0, o.get('rot') or 0)
        ob['scene_index'] = idx
        if mat is not None:
            me.materials.append(self.mat(mat) if isinstance(mat, str) else mat)
        self.coll(coll).objects.link(ob)
        return ob

    # ----------------------------------------------------------- new geometry
    def box(self, name, x0, x1, y0, y1, z0, z1, mat=None, coll='zone', bevel=0.0, segments=3):
        """Axis-aligned box from SCENE-feet bounds. bevel in feet (0 = sharp)."""
        cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        return self.box_c(name, (cx, cy, cz), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), 0.0, mat, coll, bevel, segments)

    def box_c(self, name, center, size, rot=0.0, mat=None, coll='zone', bevel=0.0, segments=3):
        """Box by SCENE-feet center (x,y,z), size (sx,sy,sz) and rot (radians about +Y)."""
        sx, sy, sz = size
        hx, hy, hz = sx / 2 * FT, sz / 2 * FT, sy / 2 * FT
        v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
             (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        ob = self.mesh_object(name, v, f, mat, coll)
        ob.location = ft2bl(*center)
        ob.rotation_euler = (0, 0, rot)
        if bevel > 0:
            self.add_bevel(ob, bevel, segments)
        return ob

    def mesh_object(self, name, verts, faces, mat=None, coll='zone', smooth=False):
        """Object from raw Blender-local meter verts/faces."""
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.validate()
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(name, me)
        if mat is not None:
            me.materials.append(self.mat(mat) if isinstance(mat, str) else mat)
        self.coll(coll).objects.link(ob)
        return ob

    @staticmethod
    def add_bevel(ob, width_ft, segments=3, harden=True):
        m = ob.modifiers.new('Bevel', 'BEVEL')
        m.width = width_ft * FT
        m.segments = segments
        m.limit_method = 'ANGLE'
        m.harden_normals = harden
        if harden:
            ob.data.shade_smooth()
            try:
                ob.data.set_sharp_from_angle(angle=math.radians(30))
            except Exception:
                pass
        return m

    def cylinder(self, name, center, radius, height, mat=None, coll='zone', verts=48, axis='Y', smooth=True):
        """Cylinder by SCENE-feet center, radius and height (feet). axis: SCENE axis 'X','Y','Z'."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius * FT, radius2=radius * FT, depth=height * FT)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        if smooth:
            me.shade_smooth()
            try:
                me.set_sharp_from_angle(angle=math.radians(40))
            except Exception:
                pass
        ob = bpy.data.objects.new(name, me)
        ob.location = ft2bl(*center)
        if axis == 'X':
            ob.rotation_euler = (0, math.pi / 2, 0)
        elif axis == 'Z':
            ob.rotation_euler = (math.pi / 2, 0, 0)
        if mat is not None:
            me.materials.append(self.mat(mat) if isinstance(mat, str) else mat)
        self.coll(coll).objects.link(ob)
        return ob

    def link_asset(self, blend_or_gltf, name=None, collection_name=None):
        """Import a downloaded model file (glTF/GLB or .blend) and return its root objects.
        Used by room modules for Poly Haven furniture/plants. Objects land in the active collection."""
        before = set(bpy.data.objects)
        if blend_or_gltf.lower().endswith(('.glb', '.gltf')):
            bpy.ops.import_scene.gltf(filepath=blend_or_gltf)
        elif blend_or_gltf.lower().endswith('.blend'):
            with bpy.data.libraries.load(blend_or_gltf, link=False) as (src, dst):
                dst.objects = list(src.objects)
            for ob in dst.objects:
                if ob is not None:
                    bpy.context.scene.collection.objects.link(ob)
        new = [o for o in bpy.data.objects if o not in before]
        roots = [o for o in new if o.parent is None or o.parent not in new]
        return roots


def place(obj, x, y, z, rot=0.0):
    """Place an object at SCENE-feet (x, y, z), rotated `rot` radians about +Y (SCENE)."""
    obj.location = ft2bl(x, y, z)
    obj.rotation_euler = (obj.rotation_euler.x, obj.rotation_euler.y, rot)
    return obj


def move_to_collection(objs, coll):
    """Move objects (and their children) into a bpy collection."""
    stack = list(objs)
    while stack:
        ob = stack.pop()
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
        stack.extend(ob.children)


def world_bbox_ft(objs):
    """Combined world bounding box of objects (and children) in SCENE feet: (x0,x1,y0,y1,z0,z1)."""
    pts = []
    stack = list(objs)
    while stack:
        ob = stack.pop()
        stack.extend(ob.children)
        if ob.type != 'MESH':
            continue
        for c in ob.bound_box:
            pts.append(bl2ft(ob.matrix_world @ Vector(c)))
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
