"""Bake the path-traced lighting of the built house into lightmap atlases and export a web GLB.

The result is the dollhouse and floor-plan model of the tour and the surface the panoramas are projected
on during a move: every surface carries its Cycles global illumination, soft shadows and material
colour, tone-mapped exactly like the panoramas. three.js displays it unlit.

  blender -b tools/render/.cache/house.blend --python tools/render/bake_web.py -- \
      --out assets/model/house.glb [--texel 45] [--detail 2] [--tex-budget 320] [--samples 512]
      [--max-atlas 4096] [--groups REGEX] [--only classes] [--prep-only] [--bake-dir DIR] [--keep-blend]

  --detail F | base=F,furniture=G   extra texel density (linear) for floors/built-ins ('base') and furniture,
                                    so the model holds up when it is the picture (dollhouse, floor plan)
  --tex-budget MB                   GPU memory all atlases may take as RGBA8 with mipmaps; the boosted
                                    groups are stepped down (x0.75 at a time) until the total fits
  --groups REGEX                    bake only the groups whose name matches (e.g. 'furniture__2_0|decor_high'):
                                    the fastest partial bake; everything else still lights and occludes

Next to the GLB it writes collision.json, <name>.bake.json (per-group statistics) and <name>.summary.json
(GLB size, texture memory, the house-wide exposure / white balance used; adapt_web.py reads it).

Output GLB contract (consumed by index.html):
  * one mesh node per bake group; node.extras.tg_class in
      'base'      floors, foundations, built-ins, kitchen base cabinets, appliances (washer / dryer)
      'wall'      walls/trim/windows/doors/the house's garage door/wall tile
      'furniture' furniture + low decor
      'decor_high' wall art, uppers, mirrors, sconces (centre > 4.8 ft)
      'ceiling'   ceilings, ceiling lights, pendants
      'exterior'  roof, fascia, facade skins
      'landscape' grounds, the rear landings, fences, paths, the street and the neighbours (incl. their garage doors)
      'glass'     all glazing (not baked; transparent material)            (treated like 'wall')
    An object (or a parent) can force its class with a custom property tg_class = one of the names above.
  * node.extras.tg_region: coarse plan region (for debugging / future per-room streaming)
  * TEXCOORD_0 = lightmap UV; baseColorTexture = baked, display-referred sRGB colour (WebP).
  * metres, glTF Y-up (exporter converts Blender Z-up): same frame as SCENE x 0.3048.
"""
import argparse
import json
import math
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import relayout as R  # noqa: E402  (pure Python: the sheet's wall faces)
from bl import garage_spec as GS  # noqa: E402  (pure Python: the garage floor's level)
from bl.common import CACHE_DIR, DATA_DIR, FT, bl2ft  # noqa: E402

VEG = re.compile(r'tree|shrub|grass|bush|fern|weed|plant_bed|hedge|leaf|leaves|foliage|flower|ivy|lawn_blade|'
                 r'(?<!porch )canopy', re.I)                # (a tree's canopy; "porch canopy" was the flat porch
#                                                             roof's name until the eighth round's gable replaced it)
INDOOR_PLANT = re.compile(r'potted|pachira|calathea|anthurium|ficus|fiddle|olive|planter|pampas|vase', re.I)
WALLISH_GROUPS = {'walls', 'trim', 'windows', 'glass', 'garageDoor', 'door'}
CLASSES = ('base', 'wall', 'glass', 'furniture', 'decor_high', 'ceiling', 'exterior', 'landscape')
# Laundry closet (bl/laundry.py, bl/revisions.laundry_closet): the stacked washer / dryer, hookups and vent are
# appliances like the fridge ('base'); without this rule the dryer (centre above 4.8 ft) would be 'decor_high'.
LAUNDRY = re.compile(r'laundry|\bwasher|\bdryer', re.I)      # (not the kitchen's dishwasher)
WALL_PART = re.compile(r'\bwall\b|partition|jamb|header|head trim|casing|architrave|\bdoor\b|\bleaf\b|lever|hinge|'
                       r'baseboard|skirting|plinth block|infill', re.I)
HOUSE_PAD = (-1.5, 41.0, -1.5, 57.5)     # footprint + margin (ft): the house's own garage door lies inside it


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--texel', type=float, default=45.0, help='lightmap texels per metre')
    ap.add_argument('--detail', default='1',
                    help="extra texel density (linear factor) for floors/built-ins and furniture: '2' or "
                         "'base=2,furniture=1.5'")
    ap.add_argument('--tex-budget', type=float, default=320.0,
                    help='MB of GPU texture memory (RGBA8 + mipmaps) all atlases together may take')
    ap.add_argument('--groups', default=None, help='regex: bake only the groups whose name (class__region) matches')
    ap.add_argument('--prep-only', action='store_true', help='plan, unwrap and report; no bake, no export (no GPU)')
    ap.add_argument('--bake-dir', default=None, help='scratch directory for the atlases (default <cache>/bake)')
    ap.add_argument('--wb-int', default=None, help='interior white balance kelvin,tint; default = median of the panoramas')
    ap.add_argument('--webp-quality', type=int, default=None, help='WebP quality of the atlases in the GLB (exporter default 75)')
    ap.add_argument('--samples', type=int, default=512)
    ap.add_argument('--max-atlas', type=int, default=4096)
    ap.add_argument('--min-atlas', type=int, default=256)
    ap.add_argument('--exposure-int', type=float, default=None, help='stops; default = median of panorama exposures')
    ap.add_argument('--exposure-ext', type=float, default=-1.2, help='stops for roof/facade/site (sunlit front probes ~-1.8, shaded garden ~+1)')
    ap.add_argument('--wb-ext', default='8000,-8', help='white balance kelvin,tint for roof/facade/site')
    ap.add_argument('--max-tris', type=int, default=25000, help='decimate imported models above this')
    ap.add_argument('--keep-blend', action='store_true')
    ap.add_argument('--only', default=None, help='comma list of classes to bake (debug)')
    ap.add_argument('--meta', default=os.path.join(CACHE_DIR, 'panos', 'render_meta.json'),
                    help='render_meta.json of the panoramas (house-wide exposure / white balance)')
    return ap.parse_args(argv)


# ---------------------------------------------------------------------------------- classify
def legacy_group(ob):
    idx = ob.get('scene_index')
    if idx is None:
        p = ob.parent
        while p is not None and idx is None:
            idx = p.get('scene_index')
            p = p.parent
    return idx


def zone_of(ob):
    """'living' for an object anywhere under the zone_living collection tree, else None."""
    parents = _parent_map()
    for c in ob.users_collection:
        n, k = c.name, 0
        while n is not None and k < 12:
            if n.startswith('zone_'):
                return n[5:]
            n, k = parents.get(n), k + 1
    return None


_PARENTS = {}


def _parent_map():
    if not _PARENTS:
        for p in bpy.data.collections:
            for ch in p.children:
                _PARENTS[ch.name] = p.name
    return _PARENTS


def mat_names(ob):
    return [m.name for m in ob.data.materials if m] if ob.type == 'MESH' else []


def is_glass(ob):
    ms = mat_names(ob)
    return bool(ms) and all(m.startswith('M_glass') or 'glass' in m.lower() for m in ms)


def is_emitter_only(ob):
    ms = mat_names(ob)
    return bool(ms) and all(m.startswith('E_') for m in ms)


def forced_class(ob):
    """tg_class custom property of the object or of a parent (lets a builder decide the class itself)."""
    p, k = ob, 0
    while p is not None and k < 12:
        v = p.get('tg_class')
        if isinstance(v, str) and v in CLASSES:
            return v
        p, k = p.parent, k + 1
    return None


def in_collection(ob, name):
    """True when ob is in collection `name` or in one nested below it."""
    parents = _parent_map()
    for c in ob.users_collection:
        n, k = c.name, 0
        while n is not None and k < 12:
            if n == name:
                return True
            n, k = parents.get(n), k + 1
    return False


def classify(ob, scene_objs, world_bb):
    """(class, region) for a render object, or (None, reason) to skip."""
    name = ob.name
    x0, x1, y0, y1, z0, z1 = world_bb
    cy = (y0 + y1) / 2
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    region = f'{int(cx // 14)}_{int(cz // 14)}'
    forced = forced_class(ob)
    if forced:
        return forced, region
    idx = legacy_group(ob)
    core = {c.name for c in ob.users_collection}
    zone = None if idx is not None or core & {'openings', 'exterior_shell', 'shell'} else zone_of(ob)
    outside = idx is None and not core & {'openings', 'exterior_shell', 'shell'} and (
        zone == 'exterior' or zone is None and (x1 < 0 or x0 > 39.7 or z1 < 0 or z0 > 54.0))   # architect-plan outline
    if outside:                                          # site, garden, fences, neighbours, garage door
        if VEG.search(name) or any(VEG.search(m) for m in mat_names(ob)):
            return None, 'vegetation'
        # Only the house's own garage door is part of the house. The neighbours' doors (ext_context,
        # 'ext nb ... garage door', up to 280 ft away) used to match the name too and became 18 stray
        # 'wall__*' nodes that floated around the dollhouse: they are site context like their houses.
        at_house = x0 > HOUSE_PAD[0] and x1 < HOUSE_PAD[1] and z0 > HOUSE_PAD[2] and z1 < HOUSE_PAD[3]
        if re.search(r'garage.?door', name, re.I) and at_house and (
                in_collection(ob, 'ext_garage_door') or not in_collection(ob, 'ext_context')):
            return ('glass' if is_glass(ob) else 'wall'), region
        if y0 > 7.0 and (x0 > -1 and x1 < 40.8 and z0 > -1 and z1 < 56.5):
            return 'exterior', region
        return 'landscape', region                       # (far glazing is baked opaque here)
    if is_glass(ob):
        return 'glass', region
    if idx is not None:                                  # shell / openings / exterior shell
        g = scene_objs[idx]['group'] if idx < len(scene_objs) else 'walls'
        if g in ('roof', 'facade'):
            return 'exterior', region
        if g in ('ceiling', 'lighting', 'mirror'):
            return 'ceiling', region
        if g in WALLISH_GROUPS:
            return 'wall', region
        return 'base', region
    if core & {'openings'}:                               # core-built opening parts (e.g. W08 window, closet door)
        # skylight frames and shaft linings start at the ceiling line: with the ceilings they are hidden in
        # the dollhouse / floor plan (as 'wall' they hung over the rooms as dark boxes)
        return ('ceiling' if y0 >= 7.9 else 'wall'), region
    if core & {'exterior_shell'}:
        return 'exterior', region
    if core & {'shell'}:                                  # revision-built shell pieces without a SCENE object
        if y0 >= 7.9:
            return 'ceiling', region
        tall_thin = (y1 - y0) >= 3.0 and min(x1 - x0, z1 - z0) <= 1.0
        return ('wall' if WALL_PART.search(name) or tall_thin else 'base'), region
    # interior zone objects
    if y0 >= 7.0 or (is_emitter_only(ob) and y1 > 7.5):
        return 'ceiling', region
    if LAUNDRY.search(name):                              # before the height rule: the dryer sits above 4.8 ft
        return ('wall' if WALL_PART.search(name) else 'base'), region
    if re.search(r'tile|skin|wainscot|backsplash|splash', name, re.I) and (y1 - y0) > 3.0:
        return 'wall', region
    if cy > 4.8 and (y1 - y0) < 4.5:
        return 'decor_high', region
    if re.search(r'cabinet|counter|worktop|island|fridge|oven|vanity|wardrobe|closet|shelving|builtin|fireplace|hearth|feature', name, re.I):
        return 'base', region
    return 'furniture', region


# ---------------------------------------------------------------------------------- helpers
def prune_collision(boxes, r=0.29):
    """The app walks between tour stops along straight edges and refuses any move whose path
    touches a collision box (inflated by r). Furniture must never cut the tour graph, so drop
    (and report) any box that blocks a stop or an edge corridor."""
    tour = json.load(open(os.path.join(DATA_DIR, 'scene.json')))['tour']
    nodes = {n['id']: n['p'] for n in tour['nodes']}
    edges = tour.get('edges') or tour.get('undirected_edges') or []

    def hits(b, x, z):
        return b['x0'] - r < x < b['x1'] + r and b['z0'] - r < z < b['z1'] + r
    keep = []
    for b in boxes:
        bad = [k for k, p in nodes.items() if hits(b, p[0], p[2])]
        for ea, eb in edges:
            if ea not in nodes or eb not in nodes:
                continue
            (ax, _, az), (bx, _, bz) = nodes[ea], nodes[eb]
            steps = max(1, int(math.hypot(bx - ax, bz - az) / 0.12) + 1)
            if any(hits(b, ax + (bx - ax) * t / steps, az + (bz - az) * t / steps) for t in range(steps + 1)):
                bad.append(f'{ea}-{eb}')
        if bad:
            print(f"[bake] collision: dropped {b['name']!r} (blocks {', '.join(bad[:4])})")
        else:
            keep.append(b)
    return keep


def world_bbox_ft(ob):
    pts = [bl2ft(ob.matrix_world @ Vector(c)) for c in ob.bound_box]
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def evaluated_copy(ob, depsgraph, coll):
    """Realised, modifier-applied, world-space mesh copy of ob (instances included)."""
    ev = ob.evaluated_get(depsgraph)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=False, depsgraph=depsgraph)
    me.transform(ob.matrix_world)
    cp = bpy.data.objects.new('bk_' + ob.name[:50], me)
    coll.objects.link(cp)
    return cp


def lawn_green(cp):
    """The rendered lawn is instanced grass blades over an olive thatch surface. The blades are not
    baked (VEG), so the walk model would show the thatch: bake the lawn surfaces in the blades' green."""
    mats = cp.data.materials
    for i, m in enumerate(mats):
        if m and m.name.startswith('Z_exterior_lawn_soil'):
            g = bpy.data.materials.get('WEB_lawn_green')
            if g is None:
                g = bpy.data.materials.new('WEB_lawn_green')
                g.use_nodes = True
                bsdf = g.node_tree.nodes.get('Principled BSDF')
                bsdf.inputs['Base Color'].default_value = (0.085, 0.165, 0.028, 1.0)   # ~#52722e, blade mid tone
                bsdf.inputs['Roughness'].default_value = 0.9
            mats[i] = g


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def decimate(ob, max_tris):
    n = tri_count(ob.data)
    if n <= max_tris:
        return n
    m = ob.modifiers.new('dec', 'DECIMATE')
    m.ratio = max(0.02, max_tris / n)
    m.use_collapse_triangulate = True
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=m.name)
    return tri_count(ob.data)


TEXEL_SCALE = {'base': 1.4, 'wall': 1.0, 'furniture': 1.3, 'decor_high': 1.1, 'ceiling': 0.6,
               'exterior': 0.55, 'landscape': 0.45}
INSIDE = (-0.05, 39.5, -0.05, 53.95)  # house footprint (ft, architect's plan) for attic-side culling


def floor_level(x, z):
    """The floor's level at a plan point (SCENE ft): the garage floor, 11 in below the house floor since the
    owner's eighth round (bl/garage_spec.py FLOOR_Y), inside the garage's clear rectangle; the house floor
    elsewhere. The same rule as floor_y() in check_holes.py."""
    gx0, gx1, gz0, gz1 = R.ROOMS['garage']
    return GS.FLOOR_Y if gx0 <= x <= gx1 and gz0 <= z <= gz1 else 0.0


def cull_hidden_faces(ob, cls):
    """Delete faces that can never be seen, so atlases spend texels on visible surfaces only.
    An upward face of a 'base' piece below the floor of its place is a foundation top under a floor. The
    garage's slab and the step at its house door lie below the HOUSE floor and are floors themselves: they
    are measured against the garage's level (without that the dollhouse and the floor plan show a garage
    without a floor, a click there finds nothing, and a move projects the panorama onto nothing)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = []
    for f in bm.faces:
        n = f.normal
        c = f.calc_center_median()
        x, y, z = c.x / FT, c.z / FT, -c.y / FT          # SCENE feet
        inside = INSIDE[0] < x < INSIDE[1] and INSIDE[2] < z < INSIDE[3]
        if cls == 'base' and (n.z < -0.5 or (y < floor_level(x, z) - 0.005 and n.z > 0.5)):
            kill.append(f)                               # slab/foundation undersides, foundation tops under floors
        elif cls == 'wall' and ((n.z > 0.5 and y > 7.95) or (n.z < -0.5 and y < 0.05)):
            kill.append(f)                               # wall tops under ceilings, bottoms on floors
        elif cls == 'ceiling' and n.z > 0.5:
            kill.append(f)                               # attic side of ceilings
        elif cls == 'exterior' and n.z < -0.3 and inside and y > 8.1:
            kill.append(f)                               # roof undersides over the house (attic)
        elif cls in ('furniture', 'decor_high') and n.z < -0.9 and y < 0.06:
            kill.append(f)                               # bottoms resting on the floor
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    return len(kill)


def surface_area(me):
    return sum(p.area for p in me.polygons)


def join(objs, name):
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    ctx = {'object': objs[0], 'active_object': objs[0], 'selected_objects': objs, 'selected_editable_objects': objs}
    with bpy.context.temp_override(**ctx):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


MARGINS = (3.0, 2.0, 1.5, 1.0, 0.5, 0.25)   # px between islands, tried in this order
KEEP_COVER = 0.5                         # a margin is accepted when the layout keeps half of the UV area that a
                                         # pack without any margin covers (i.e. loses at most 30 % of resolution)
CRUMB_PARTS, CRUMB_TRIS = 60, 80         # an object of >= 60 loose parts averaging <= 80 triangles is "crumbly"


def loose_parts(me):
    """Number of connected pieces of a mesh (leaves of a plant, pebbles of a fire bed ...)."""
    import numpy as np
    nv, ne = len(me.vertices), len(me.edges)
    if not nv or not ne:
        return nv
    ev = np.empty(ne * 2, dtype=np.int64)
    me.edges.foreach_get('vertices', ev)
    a, b = ev[0::2], ev[1::2]
    label = np.arange(nv)
    for _ in range(4000):
        m = np.minimum(label[a], label[b])
        new = label.copy()
        np.minimum.at(new, a, m)
        np.minimum.at(new, b, m)
        new = new[new]                                   # pointer jumping
        if np.array_equal(new, label):
            break
        label = new
    used = np.zeros(nv, dtype=bool)
    used[a] = True
    used[b] = True
    return int(len(np.unique(label[used])))


def tag_crumbly(cp, pid):
    """Mark a crumbly copy for a planar unwrap: face attribute tg_pid = pid and corner attribute tg_puv =
    its vertices projected along the thinnest bounding-box axis, in metres from the box corner. See unwrap."""
    import numpy as np
    me = cp.data
    nv = len(me.vertices)
    co = np.empty(nv * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    lo, ext = co.min(0), co.max(0) - co.min(0)
    ax = [k for k in range(3) if k != int(np.argmin(ext))]
    vi = np.empty(len(me.loops), dtype=np.int32)
    me.loops.foreach_get('vertex_index', vi)
    puv = (co[vi][:, ax] - lo[ax]).astype(np.float32)
    at = me.attributes.new('tg_puv', 'FLOAT2', 'CORNER')
    at.data.foreach_set('vector', puv.ravel())
    at = me.attributes.new('tg_pid', 'INT', 'FACE')
    at.data.foreach_set('value', np.full(len(me.polygons), pid, dtype=np.int32))


def split_long_faces(ob, max_len):
    """Cut every face longer than `max_len` metres with axis-aligned planes and separate the pieces.

    The packer scales all islands of a group by one factor, so the longest island must fit the atlas
    side. One 12 to 17 m strip (the foundation's edge, a floor seam patch, a ceiling slab across the house)
    in a group of 12 to 30 m2 forced the whole group, floors included, down to a fraction of its atlas
    (base__1_1 / base__1_2: 20 % and 6 % of the atlas used, the hall and foyer floors at 84 texels/m while
    their neighbours had 210). Cut into pieces no longer than the atlas side at the nominal density, such
    strips pack like everything else. Returns the number of cuts."""
    import numpy as np
    me = ob.data
    n = len(me.loops)
    if not n:
        return 0
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    vi = np.empty(n, dtype=np.int64)
    me.loops.foreach_get('vertex_index', vi)
    ls = np.empty(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get('loop_start', ls)
    pc = co.reshape(-1, 3)[vi]
    ext = np.maximum.reduceat(pc, ls) - np.minimum.reduceat(pc, ls)       # per-face extent along x, y, z
    if not (ext > max_len).any():
        return 0
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    cuts = 0
    for axis in range(3):
        faces = [bm.faces[i] for i in np.nonzero(ext[:, axis] > max_len)[0] if bm.faces[i].is_valid] if axis == 0 else \
            [f for f in bm.faces if max(v.co[axis] for v in f.verts) - min(v.co[axis] for v in f.verts) > max_len]
        if not faces:
            continue
        lo = min(v.co[axis] for f in faces for v in f.verts)
        hi = max(v.co[axis] for f in faces for v in f.verts)
        parts = int(math.ceil((hi - lo) / max_len))
        normal = Vector([1.0 if k == axis else 0.0 for k in range(3)])
        for k in range(1, parts):
            geom = list({e for f in faces for e in f.edges} | {v for f in faces for v in f.verts}) + faces
            res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=normal * (lo + (hi - lo) * k / parts),
                                         plane_no=normal, clear_inner=False, clear_outer=False)
            edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
            if edges:
                bmesh.ops.split_edges(bm, edges=edges)
                cuts += 1
            faces = [f for f in res['geom'] if isinstance(f, bmesh.types.BMFace) and f.is_valid]
    bm.to_mesh(me)
    bm.free()
    me.update()
    return cuts


def uv_layout(me, layer='lm'):
    """(uv [loops, 2], per-face UV area, per-face loop start, per-face loop count) of a UV layer."""
    import numpy as np
    n = len(me.loops)
    uv = np.empty(n * 2, dtype=np.float32)
    me.uv_layers[layer].data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2).astype(np.float64)
    ls = np.empty(len(me.polygons), dtype=np.int64)
    lt = np.empty(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get('loop_start', ls)
    me.polygons.foreach_get('loop_total', lt)
    nxt = np.arange(n) + 1
    nxt[ls + lt - 1] = ls
    cross = uv[:, 0] * uv[nxt, 1] - uv[nxt, 0] * uv[:, 1]
    area = np.abs(np.add.reduceat(cross, ls)) * 0.5 if n else np.zeros(0)
    return uv, area, ls, lt


def _planar(me):
    """(per-face planar id, per-loop planar id, per-loop planar coordinates in metres, ids) or None."""
    import numpy as np
    pid_at, puv_at = me.attributes.get('tg_pid'), me.attributes.get('tg_puv')
    if pid_at is None or puv_at is None:
        return None
    pid = np.empty(len(me.polygons), dtype=np.int32)
    pid_at.data.foreach_get('value', pid)
    if not pid.any():
        return None
    lt = np.empty(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get('loop_total', lt)
    puv = np.empty(len(me.loops) * 2, dtype=np.float32)
    puv_at.data.foreach_get('vector', puv)
    return pid, np.repeat(pid, lt), puv.reshape(-1, 2).astype(np.float64), [int(k) for k in np.unique(pid[pid > 0])]


def _activate(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def _edit_pack(margin):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')              # (hidden faces stay out of the pack)
    # AABB packing: our islands are near-rectangular and the default concave packer is ~1000x slower
    try:
        bpy.ops.uv.pack_islands(rotate=True, rotate_method='CARDINAL', shape_method='AABB',
                                margin_method='FRACTION', margin=margin)
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=False, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')


def _cover(me):
    """(layout lies inside the unit square, UV area it covers) over the faces the packer sees."""
    import numpy as np
    uv, area, _, lt = uv_layout(me)
    hide = np.zeros(len(me.polygons), dtype=bool)
    me.polygons.foreach_get('hide', hide)
    if hide.all():
        return False, 0.0
    u = uv[np.repeat(~hide, lt)]
    return bool(u.min() >= -1e-4 and u.max() <= 1.0 + 1e-4), float(area[~hide].sum())


def unwrap(ob):
    """Lightmap unwrap of `ob` into UV layer 'lm' (not yet packed for an atlas size: see pack_layout).

    smart_project cuts the mesh into islands. A crumbly object (tag_crumbly: the leaves of a plant, the
    pebbles of the fire bed) would add thousands of islands of a few texels each, so it is not cut up:
    it gets ONE planar projection. Its faces are hidden from the packer and a stand-in quad of the
    projection's size is packed for it; finish_unwrap maps the object into the quad's final place.
    The pieces of such an object share the texels where they overlap, which is what foliage needs."""
    import numpy as np
    me = ob.data
    for uv in list(me.uv_layers):
        if uv.name == 'lm':
            me.uv_layers.remove(uv)
    me.uv_layers.new(name='lm')
    me.uv_layers.active = me.uv_layers['lm']   # bake target; keep the original active_render for textures
    _activate(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    pl = _planar(me)
    if pl is None:
        return 0
    pid, loop_pid, puv, ids = pl
    _, area, _, _ = uv_layout(me)
    world = np.empty(len(me.polygons), dtype=np.float64)
    me.polygons.foreach_get('area', world)
    ok = (pid == 0) & (world > 1e-10) & (area > 0)
    r = float(np.sqrt(area[ok].sum() / world[ok].sum())) if ok.any() else 0.05     # UV units per metre
    bm = bmesh.new()
    bm.from_mesh(me)
    layer = bm.loops.layers.uv['lm']
    cursor = 2.0                                          # beside the smart-project layout (which is in 0..1)
    for i, k in enumerate(ids):
        w, h = (max(float(v), 1e-3) * r for v in puv[loop_pid == k].max(0))
        z = -50.0 - i                                     # a 1 mm stand-in far below the house; removed again
        f = bm.faces.new([bm.verts.new(c) for c in ((0, 0, z), (0.001, 0, z), (0.001, 0.001, z), (0, 0.001, z))])
        for loop, (du, dv) in zip(f.loops, ((0, 0), (w, 0), (w, h), (0, h))):
            loop[layer].uv = (cursor + du, 2.0 + dv)
        cursor += w + 0.25
    bm.to_mesh(me)
    bm.free()
    hide = np.zeros(len(me.polygons), dtype=bool)
    hide[:len(pid)] = pid > 0
    me.polygons.foreach_set('hide', hide)
    me.update()
    return len(ids)


def pack_layout(ob, size):
    """Pack the islands of `ob` for a size x size atlas. Returns {'margin_px', 'cover'}.

    The packer is asked for a margin that is a fixed fraction of the atlas. When thousands of small
    islands cannot have that margin at any scale, Blender's packer shrinks every island to almost
    nothing (and may let the layout overflow the unit square): no texel centre lies inside any island,
    the bake writes nothing and the atlas stays BLACK. That is what happened to furniture__2_0,
    decor_high__2_1 and decor_high__0_1 with the fixed 3 px margin (1,800 to 15,000 islands in 256 /
    512 px atlases). So the layout is measured after every pack: the margin steps down from 3 px until
    the layout lies inside the unit square and still covers KEEP_COVER of what a pack without margin
    covers; a bake can never run on an empty atlas."""
    import numpy as np
    me = ob.data
    _activate(ob)
    _edit_pack(0.0)
    _, tight = _cover(me)
    for m in MARGINS:
        _edit_pack(m / size)
        inside, cover = _cover(me)
        if inside and cover >= KEEP_COVER * tight:
            return {'margin_px': m, 'cover': round(cover, 3), 'tight': round(tight, 3)}
    _edit_pack(0.0)
    inside, cover = _cover(me)
    if not inside:                                        # last resort: scale the tight pack into the square
        uv, _, _, _ = uv_layout(me)
        lo, hi = uv.min(0), uv.max(0)
        k = 1.0 / max(1e-9, float((hi - lo).max()))
        me.uv_layers['lm'].data.foreach_set('uv', ((uv - lo) * k * 0.998 + 0.001).astype(np.float32).ravel())
        me.update()
        cover *= k * k
    print(f'[bake] WARNING {ob.name}: no margin fits a {size}px atlas, packed without one (cover {cover:.2f})', flush=True)
    return {'margin_px': 0.0, 'cover': round(cover, 3), 'tight': round(tight, 3)}


def finish_unwrap(ob):
    """After the final pack_layout: move each crumbly object into its stand-in quad and drop the quads."""
    import numpy as np
    me = ob.data
    pl = _planar(me)
    if pl is not None:
        pid, loop_pid, puv, ids = pl
        uv, _, ls, _ = uv_layout(me)
        first = len(me.polygons) - len(ids)               # the stand-ins are the last faces
        for i, k in enumerate(ids):
            c = uv[ls[first + i]:ls[first + i] + 4]       # corners (0,0) (w,0) (w,h) (0,h), wherever the packer put them
            sel = loop_pid == k
            s = puv[sel] / np.maximum(puv[sel].max(0), 1e-3)
            uv[sel] = c[0] + s[:, :1] * (c[1] - c[0]) + s[:, 1:] * (c[3] - c[0])
        me.uv_layers['lm'].data.foreach_set('uv', uv.astype(np.float32).ravel())
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        verts = {v for f in bm.faces[first:] for v in f.verts}
        bmesh.ops.delete(bm, geom=list(verts), context='VERTS')
        bm.to_mesh(me)
        bm.free()
        me.polygons.foreach_set('hide', np.zeros(len(me.polygons), dtype=bool))
        me.update()
    for name in ('tg_pid', 'tg_puv'):
        at = me.attributes.get(name)
        if at is not None:
            me.attributes.remove(at)


def set_bake_target(ob, img):
    for slot in ob.material_slots:
        m = slot.material
        if m is None or not m.use_nodes:
            continue
        nt = m.node_tree
        node = nt.nodes.get('TG_BAKE')
        if node is None:
            node = nt.nodes.new('ShaderNodeTexImage')
            node.name = 'TG_BAKE'
            node.location = (-1200, -800)
        node.image = img
        nt.nodes.active = node


def denoise(img, w, h, bake_dir=None):
    """Denoise a baked float image in a throwaway compositor scene (OIDN)."""
    sc = bpy.data.scenes.new('tg_denoise')
    try:
        sc.render.resolution_x, sc.render.resolution_y = w, h
        sc.render.resolution_percentage = 100
        tree = None
        if hasattr(sc, 'compositing_node_group'):
            tree = bpy.data.node_groups.new('tg_dn', 'CompositorNodeTree')
            sc.compositing_node_group = tree
        else:
            sc.use_nodes = True
            tree = sc.node_tree
            tree.nodes.clear()
        n_img = tree.nodes.new('CompositorNodeImage')
        n_img.image = img
        dn = tree.nodes.new('CompositorNodeDenoise')
        try:
            dn.prefilter = 'ACCURATE'
            dn.quality = 'HIGH'
        except AttributeError:
            pass
        tree.links.new(n_img.outputs[0], dn.inputs[0])
        out = None
        for t in ('CompositorNodeComposite', 'NodeGroupOutput'):
            try:
                out = tree.nodes.new(t)
                break
            except RuntimeError:
                continue
        if out.bl_idname == 'NodeGroupOutput':
            tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        tree.links.new(dn.outputs[0], out.inputs[0])
        sc.render.engine = 'CYCLES'
        sc.view_settings.view_transform = 'Standard'
        sc.render.image_settings.file_format = 'OPEN_EXR'
        sc.render.image_settings.color_depth = '32'
        tmp = os.path.join(bake_dir or os.path.join(CACHE_DIR, 'bake'), f'_dn_{img.name}.exr')
        sc.render.filepath = tmp
        # an empty scene renders instantly; the compositor does the work
        with bpy.context.temp_override(scene=sc):
            bpy.ops.render.render(write_still=True, scene=sc.name)
        res = bpy.data.images.load(tmp)
        res.colorspace_settings.name = 'Linear Rec.709'
        return res
    finally:
        bpy.data.scenes.remove(sc)


def save_display(img, path, exposure, src_scene):
    """Save a linear image as display-referred sRGB using the panorama colour pipeline."""
    vs = src_scene.view_settings
    keep = vs.exposure
    vs.exposure = exposure
    st = src_scene.render.image_settings
    keep_fmt = (st.file_format, st.color_depth)
    st.file_format = 'PNG'
    st.color_depth = '8'
    img.save_render(path, scene=src_scene)
    st.file_format, st.color_depth = keep_fmt
    vs.exposure = keep
    out = bpy.data.images.load(path)
    out.colorspace_settings.name = 'sRGB'
    return out


def unlit_material(name, img):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'lm'
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Linear'
    nt.links.new(uv.outputs[0], tex.inputs[0])
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 1.0
    bsdf.inputs['Specular IOR Level'].default_value = 0.0
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return m


def glass_material():
    m = bpy.data.materials.get('WEB_glass') or bpy.data.materials.new('WEB_glass')
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.78, 0.86, 0.88, 1)
    bsdf.inputs['Alpha'].default_value = 0.18
    bsdf.inputs['Roughness'].default_value = 0.05
    try:
        m.surface_render_method = 'BLENDED'
    except AttributeError:
        m.blend_method = 'BLEND'
    return m


# ---------------------------------------------------------------------------------- main
def metal_proxies():
    """Baking records diffuse light only, so metals (which have no diffuse response) would come out
    black: mirrors, stainless appliances, chrome and brass fittings. For the bake, each Principled
    BSDF gets its diffuse equivalent instead:
      * metallic is set to 0 (texture links removed) and the base colour kept, because a metal's base
        colour is its reflectance and a rough metal reads at about that brightness;
      * perfect mirrors and polished chrome (roughness <= 0.06) get a mid silver-grey, a stand-in for a
        blurred reflection of the room (as white they would read as painted panels).
    Only the in-memory scene used by this script changes; the panoramas are unaffected."""
    mats = 0
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree:
            continue
        changed = False
        for node in m.node_tree.nodes:
            if node.type != 'BSDF_PRINCIPLED':
                continue
            mi = node.inputs['Metallic']
            if not mi.is_linked and mi.default_value <= 0.0:
                continue
            polished = (not mi.is_linked and mi.default_value >= 0.9 and not node.inputs['Roughness'].is_linked
                        and node.inputs['Roughness'].default_value <= 0.06)
            for link in list(mi.links):
                m.node_tree.links.remove(link)
            mi.default_value = 0.0
            if polished and not node.inputs['Base Color'].is_linked:
                node.inputs['Base Color'].default_value = (0.52, 0.55, 0.57, 1.0)
            changed = True
        mats += changed
    print(f'[bake] metal proxies: {mats} materials')


def parse_detail(text):
    """'2' -> {'base': 2, 'furniture': 2}; 'base=2,furniture=1.5' -> per class (any class name works)."""
    out = {}
    if '=' in text:
        for part in text.split(','):
            k, v = part.split('=')
            out[k.strip()] = float(v)
    else:
        out['base'] = out['furniture'] = float(text)
    return {k: v for k, v in out.items() if abs(v - 1.0) > 1e-6}


def tex_mb(size):
    """GPU megabytes of a size x size RGBA8 texture with mipmaps (three.js uploads the WebP atlases uncompressed)."""
    return size * size * 4 * (4.0 / 3.0) / 1e6


def fit_budget(plan, budget_mb):
    """Step the detail-boosted atlases down (x0.75, multiples of 64 px; WebGL2 mipmaps any size) until all
    atlases fit `budget_mb`. The largest atlas goes first; none goes below its size without the boost."""
    def total():
        return sum(tex_mb(p['size']) for p in plan)
    steps = 0
    while total() > budget_mb:
        cand = [p for p in plan if p['size'] > p['floor']]
        if not cand:
            print(f'[bake] WARNING textures need {total():.0f} MB even without --detail (budget {budget_mb:.0f} MB): '
                  f'lower --texel or --max-atlas', flush=True)
            break
        q = max(cand, key=lambda p: (p['size'], p['side'] and p['size'] / p['side']))
        q['size'] = max(q['floor'], int(round(q['size'] * 0.75 / 64.0)) * 64)
        steps += 1
    return steps, total()


def main():
    import numpy as np
    import render_panos as rp
    a = parse()
    t0 = time.time()
    sc = bpy.context.scene
    scene = json.load(open(os.path.join(DATA_DIR, 'scene.json')))
    scene_objs = scene['objects']
    bake_dir = a.bake_dir or os.path.join(CACHE_DIR, 'bake')
    os.makedirs(bake_dir, exist_ok=True)
    detail = parse_detail(a.detail)
    only_groups = re.compile(a.groups) if a.groups else None

    # render / bake settings (GPU)
    sc.render.engine = 'CYCLES'
    if not a.prep_only:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == 'OPTIX'
        sc.cycles.device = 'GPU'
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 12
    sc.cycles.diffuse_bounces = 6
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 12
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.sample_clamp_indirect = 10.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    rb = sc.render.bake
    rb.use_pass_direct = True
    rb.use_pass_indirect = True
    rb.use_pass_diffuse = True
    rb.use_pass_glossy = False
    rb.use_pass_transmission = True
    rb.use_pass_emit = True
    rb.margin = 6
    try:
        rb.margin_type = 'EXTEND'
    except AttributeError:
        pass
    vs = sc.view_settings
    vs.view_transform = 'AgX'
    try:
        vs.look = 'AgX - Base Contrast'
    except TypeError:
        pass
    # Same light balance as the panoramas; ONE house-wide white balance and interior exposure (this is the
    # dollhouse's exposure): the medians of the values the panoramas of the tour's sweeps were rendered with.
    from bl import lighting
    lighting.apply_balance()
    metal_proxies()
    meta = json.load(open(a.meta)) if os.path.exists(a.meta) else {}
    sweep_ids = {n['id'] for n in scene.get('tour', {}).get('nodes', []) if not n.get('outdoor')}
    exp_int, (wb_t, wb_n) = rp.house_look(meta, sweep_ids)
    if a.exposure_int is not None:
        exp_int = a.exposure_int
    if a.wb_int:
        v = [float(x) for x in a.wb_int.split(',')]
        wb_t, wb_n = v[0], (v[1] if len(v) > 1 else wb_n)
    try:
        vs.use_white_balance = True
        vs.white_balance_temperature = wb_t
        vs.white_balance_tint = wb_n
    except AttributeError:
        pass
    wb_ext = tuple(float(v) for v in a.wb_ext.split(','))
    print(f'[bake] exposure interior {exp_int:+.2f}, exterior {a.exposure_ext:+.2f}, wb {wb_t:.0f}K/{wb_n:+.1f}'
          + ('' if meta else f'  (no {a.meta}: defaults)'))

    # ---- collect + classify render objects
    depsgraph = bpy.context.evaluated_depsgraph_get()
    work = bpy.data.collections.new('TG_WEB')
    sc.collection.children.link(work)
    groups = {}
    skipped = {}
    collision = []
    for ob in list(sc.objects):
        if ob.type != 'MESH' or ob.hide_render or not ob.visible_get():
            continue
        if any(c.name in ('portals',) for c in ob.users_collection) or ob.name.startswith(('skylight cutter',)):
            continue
        if not ob.data.polygons and not ob.modifiers:
            continue
        bb = world_bbox_ft(ob)
        cls, region = classify(ob, scene_objs, bb)
        if cls is None:
            skipped[region] = skipped.get(region, 0) + 1
            continue
        if a.only and cls not in a.only.split(','):
            continue
        if cls == 'landscape':
            # one huge ground plane would starve the whole site of texels: split the site into the
            # ground plane, far context (street, neighbours) and the near garden, each its own atlas
            if ob.data.polygons and surface_area(ob.data) * max(ob.matrix_world.to_scale()) ** 2 > 20000:
                key = 'ground'
            elif any(c.name == 'ext_context' for c in ob.users_collection) or \
                    re.search(r'street|sidewalk|curb|park strip|asphalt|\bnb\b', ob.name, re.I):
                key = 'context'
            else:
                key = 'near'
        else:
            key = region if cls != 'exterior' else cls
        # walk-mode collision footprints for new interior furniture / built-ins (SCENE feet)
        if cls in ('furniture', 'base') and legacy_group(ob) is None and zone_of(ob) not in (None, 'exterior'):
            x0, x1, y0, y1, z0, z1 = bb
            fp = (x1 - x0) * (z1 - z0)
            if y0 < 1.6 and (y1 - y0) > 1.0 and 0.25 < fp < 140:
                collision.append({'name': ob.name[:40], 'x0': round(x0, 3), 'x1': round(x1, 3),
                                  'z0': round(z0, 3), 'z1': round(z1, 3), 'h': round(y1, 2)})
        if only_groups and not only_groups.search(f'{cls}__{key}'):
            continue
        groups.setdefault((cls, key), []).append(ob)
    print('[bake] groups:', {f'{k[0]}/{k[1]}': len(v) for k, v in groups.items()}, 'skipped:', skipped)
    stray = sorted(f'{c}__{k}' for (c, k), v in groups.items() if c in ('base', 'wall', 'glass', 'furniture', 'decor_high', 'ceiling')
                   and not any(-3 < world_bbox_ft(o)[0] < 42.5 and -3 < world_bbox_ft(o)[4] < 59 for o in v))
    if stray:
        print(f'[bake] WARNING house-class groups far outside the footprint: {", ".join(stray)}', flush=True)

    # ---- copies, one joined mesh per group, atlas plan
    # (the full scene stays visible so baking sees all occluders and bounce light, vegetation
    # shadows included; only the copies are baked)
    exports = []
    stats = {}
    origins = {}
    plan = []
    for (cls, region), objs in sorted(groups.items()):
        tg = time.time()
        copies = []
        tris = 0
        crumbly = 0
        for ob in objs:
            cp = evaluated_copy(ob, depsgraph, work)
            if not cp.data.polygons:
                bpy.data.objects.remove(cp)
                continue
            lawn_green(cp)
            n = decimate(cp, a.max_tris) if legacy_group(ob) is None else tri_count(cp.data)
            tris += n
            if cls in ('furniture', 'decor_high', 'base') and n >= 800:
                parts = loose_parts(cp.data)
                if parts >= CRUMB_PARTS and n / parts <= CRUMB_TRIS:
                    crumbly += 1
                    tag_crumbly(cp, crumbly)
            cp.hide_render = True                 # copies never occlude the bake
            copies.append(cp)
        if not copies:
            continue
        name = f'{cls}__{region}'
        g = join(copies, name)
        g['tg_class'] = cls
        g['tg_region'] = region
        origins[g.name] = objs
        exports.append(g)
        if cls == 'glass':
            g.data.materials.clear()
            g.data.materials.append(glass_material())
            for uv in list(g.data.uv_layers):
                g.data.uv_layers.remove(uv)
            stats[name] = {'tris': tris, 'atlas': 0}
            continue
        culled = cull_hidden_faces(g, cls)
        area = surface_area(g.data)
        scale = TEXEL_SCALE.get(cls, 1.0) * {'context': 0.4, 'ground': 0.0}.get(region, 1.0)
        side = math.sqrt(area / 0.62) * a.texel * scale            # px for the nominal texel density

        def atlas(f):
            return int(2 ** math.ceil(math.log2(max(a.min_atlas, min(a.max_atlas, side * f)))))
        floor = atlas(1.0)
        size = atlas(detail.get(cls, 1.0))
        if region == 'ground':
            floor = size = 512                    # flat lawn far from the house: lighting only
        tu = time.time()
        # no island may be longer than the atlas side at the nominal density (see split_long_faces)
        cuts = split_long_faces(g, max(1.5, 0.8 * math.sqrt(area / 0.62))) if region != 'ground' else 0
        planar = unwrap(g)
        lay = pack_layout(g, floor)
        bumped = False
        if lay['margin_px'] < 1.5 and floor < a.max_atlas and cls not in ('landscape', 'exterior'):
            # so many islands that not even 1.5 px fit between them: this group of the house needs a larger
            # atlas (the site keeps its size: it is seen from far away and is the largest atlas already)
            floor *= 2
            size = max(size, floor)
            bumped = True
            lay = None
        plan.append({'name': name, 'size': size, 'floor': min(floor, size), 'side': side, 'packed': floor if lay else 0,
                     'lay': lay})
        stats[name] = {'tris': tris, 'area_m2': round(area, 1), 'culled': culled, 'crumbly': crumbly, 'planar': planar,
                       'cuts': cuts, 'bumped': bumped, 'prep_s': round(tu - tg, 1), 'uv_s': round(time.time() - tu, 1)}
    steps, total_mb = fit_budget(plan, a.tex_budget)
    if steps:
        print(f'[bake] texture budget {a.tex_budget:.0f} MB: {steps} step(s) down on the detail-boosted atlases', flush=True)
    for p in plan:
        tg = time.time()
        g = bpy.data.objects[p['name']]
        st = stats[p['name']]
        st['atlas'] = p['size']
        st.update(p['lay'] if p['packed'] == p['size'] else pack_layout(g, p['size']))
        finish_unwrap(g)
        st['uv_s'] = round(st['uv_s'] + time.time() - tg, 1)
        print(f"[prep] {p['name']}: {st['tris']} tris, {st['area_m2']} m2, atlas {p['size']}px"
              + (f" (nominal {p['floor']})" if p['size'] != p['floor'] else '') + (' (raised: many islands)' if st['bumped'] else '')
              + f", margin {st['margin_px']}px, cover {st['cover']}"
              + (f", {st['planar']} planar" if st['planar'] else '') + (f", {st['cuts']} cuts" if st['cuts'] else '')
              + f", prep {st['prep_s']}s uv {st['uv_s']}s", flush=True)
    mp = sum(p['size'] ** 2 for p in plan) / 1e6
    print(f'[bake] plan: {len(exports)} groups, {len(plan)} atlases, {mp:.1f} MP = {total_mb:.0f} MB of GPU texture memory '
          f'(RGBA8 + mipmaps; budget {a.tex_budget:.0f} MB), detail {detail or "none"}', flush=True)
    if a.prep_only:
        print(f'[bake] prep only: nothing baked or exported ({time.time() - t0:.0f}s)')
        return

    # ---- bake each group against the ORIGINAL scene (copies are hidden from render)
    black = []
    for g in exports:
        if g['tg_class'] == 'glass':
            continue
        size = stats[g.name]['atlas']
        img = bpy.data.images.new(f'bake_{g.name}', size, size, float_buffer=True, alpha=False)
        img.colorspace_settings.name = 'Linear Rec.709'
        # bake on the copy: make it renderable and hide the originals it replaces (coincident geometry)
        g.hide_render = False
        for o in origins[g.name]:
            o.hide_render = True
        set_bake_target(g, img)
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        g.select_set(True)
        bpy.context.view_layer.objects.active = g
        tb = time.time()
        bpy.ops.object.bake(type='COMBINED', use_clear=True, margin=6)
        g.hide_render = True
        for o in origins[g.name]:
            o.hide_render = False
        # an atlas the bake left empty is a bug in the unwrap (see pack_layout), never a dark room
        px = np.empty(size * size * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        lit = float((px.reshape(-1, 4)[:, :3].max(1) > 0).mean())
        stats[g.name]['lit'] = round(lit, 3)
        if lit < 0.02:
            black.append(g.name)
            print(f'[bake] WARNING {g.name}: the bake wrote only {lit * 100:.1f}% of the atlas', flush=True)
        try:
            dn = denoise(img, size, size, bake_dir)
        except Exception as e:  # keep going with the raw bake
            print('[bake] denoise failed:', e)
            dn = img
        outdoor = g['tg_class'] in ('exterior', 'landscape')
        ev = a.exposure_ext if outdoor else exp_int
        try:
            vs.white_balance_temperature, vs.white_balance_tint = (wb_ext if outdoor else (wb_t, wb_n))
        except AttributeError:
            pass
        png = os.path.join(bake_dir, f'{g.name}.png')
        disp = save_display(dn, png, ev, sc)
        g.data.materials.clear()
        g.data.materials.append(unlit_material(f'WEB_{g.name}', disp))
        for uv in list(g.data.uv_layers):
            if uv.name != 'lm':
                g.data.uv_layers.remove(uv)
        stats[g.name]['bake_s'] = round(time.time() - tb, 1)
        print(f'[bake] {g.name}: {size}px, {stats[g.name]["tris"]} tris, lit {lit:.2f}, {stats[g.name]["bake_s"]}s', flush=True)

    # ---- export
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for g in exports:
        g.hide_render = False
        g.hide_set(False)
        g.select_set(True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    kw = dict(filepath=a.out, export_format='GLB', use_selection=True, export_extras=True,
              export_texcoords=True, export_normals=False, export_materials='EXPORT',
              export_image_format='WEBP', export_cameras=False, export_lights=False, export_apply=True,
              export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
              export_draco_position_quantization=14, export_draco_texcoord_quantization=12)
    if a.webp_quality is not None:
        kw['export_image_quality'] = a.webp_quality
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop('export_image_format')
        kw.pop('export_image_quality', None)
        bpy.ops.export_scene.gltf(**kw)
    base = os.path.splitext(a.out)[0]
    json.dump(stats, open(base + '.bake.json', 'w'), indent=1)
    collision = prune_collision(collision)
    if not only_groups and not a.only:            # a partial bake must not replace the full collision file
        with open(os.path.join(os.path.dirname(os.path.abspath(a.out)), 'collision.json'), 'w') as f:
            json.dump({'units': 'ft', 'boxes': collision}, f, separators=(',', ':'))
        print(f'[bake] collision boxes: {len(collision)}')
    if a.keep_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(bake_dir, 'web_baked.blend'))
    total_tris = sum(v['tris'] for v in stats.values())
    glb_mb = os.path.getsize(a.out) / 1e6
    summary = {'glb_mb': round(glb_mb, 2), 'texture_mb': round(total_mb, 1), 'megapixels': round(mp, 1),
               'atlases': len(plan), 'groups': len(exports), 'tris': total_tris, 'seconds': round(time.time() - t0),
               'texel': a.texel, 'detail': detail, 'tex_budget': a.tex_budget, 'samples': a.samples,
               'exposure_int': round(exp_int, 4), 'wb_int': [round(wb_t), round(wb_n, 1)],
               'exposure_ext': a.exposure_ext, 'wb_ext': list(wb_ext), 'black_atlases': black,
               'partial': bool(only_groups or a.only), 'meta': os.path.abspath(a.meta)}
    json.dump(summary, open(base + '.summary.json', 'w'), indent=1)
    print(f'[bake] exported {a.out} ({glb_mb:.1f} MB), {len(exports)} groups, {total_tris} tris, '
          f'{len(plan)} atlases {mp:.1f} MP = {total_mb:.0f} MB GPU texture memory, {time.time() - t0:.0f}s')
    if glb_mb > 14.0:
        print(f'[bake] WARNING the GLB is {glb_mb:.1f} MB (target: below about 14 MB): lower --detail or --webp-quality')
    if black:
        raise RuntimeError(f'black atlases: {", ".join(black)}')


if __name__ == '__main__':
    main()
