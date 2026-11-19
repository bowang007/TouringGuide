"""Bake the path-traced lighting of the built house into lightmap atlases and export a web GLB.

The result is what the browser shows in Dollhouse / 3D Walk / Floor plan: every surface carries
its Cycles global illumination, soft shadows and material colour, tone-mapped exactly like the
panoramas, so the real-time model matches the 360 renders. three.js displays it unlit.

  blender -b tools/render/.cache/house.blend --python tools/render/bake_web.py -- \
      --out assets/model/house.glb [--texel 45] [--samples 512] [--max-atlas 4096] [--keep-blend]

Output GLB contract (consumed by index.html):
  * one mesh node per bake group; node.extras.tg_class in
      'base'      floors, foundations, built-ins, kitchen base cabinets   (always visible)
      'wall'      walls/trim/windows/doors/garage door/wall tile          (clipped at 2.1 ft in cutaway modes)
      'furniture' furniture + low decor                                    (furniture toggle)
      'decor_high' wall art, uppers, mirrors, sconces (centre > 4.8 ft)   (hidden in cutaway modes + furniture toggle)
      'ceiling'   ceilings, ceiling lights, pendants                       (walk mode only)
      'exterior'  roof, fascia, facade skins                               (exterior mode only)
      'landscape' grounds, deck, fences, paths                             (garden toggle)
      'glass'     all glazing (not baked; transparent material)            (treated like 'wall')
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

from bl.common import CACHE_DIR, DATA_DIR, FT, bl2ft  # noqa: E402

VEG = re.compile(r'tree|shrub|grass|bush|fern|weed|plant_bed|hedge|leaf|leaves|foliage|flower|ivy|lawn_blade|'
                 r'(?<!porch )canopy', re.I)                # (not the covered porch's canopy)
INDOOR_PLANT = re.compile(r'potted|pachira|calathea|anthurium|ficus|fiddle|olive|planter|pampas|vase', re.I)
WALLISH_GROUPS = {'walls', 'trim', 'windows', 'glass', 'garageDoor', 'door'}


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--texel', type=float, default=45.0, help='lightmap texels per metre')
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


def classify(ob, scene_objs, world_bb):
    """(class, region) for a render object, or (None, reason) to skip."""
    name = ob.name
    x0, x1, y0, y1, z0, z1 = world_bb
    cy = (y0 + y1) / 2
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    region = f'{int(cx // 14)}_{int(cz // 14)}'
    idx = legacy_group(ob)
    core = {c.name for c in ob.users_collection}
    zone = None if idx is not None or core & {'openings', 'exterior_shell', 'shell'} else zone_of(ob)
    outside = idx is None and not core & {'openings', 'exterior_shell', 'shell'} and (
        zone == 'exterior' or zone is None and (x1 < 0 or x0 > 39.7 or z1 < 0 or z0 > 54.0))   # architect-plan outline
    if outside:                                          # site, garden, fences, neighbours, garage door
        if VEG.search(name) or any(VEG.search(m) for m in mat_names(ob)):
            return None, 'vegetation'
        if re.search(r'garage.?door', name, re.I):
            return ('glass' if is_glass(ob) else 'wall'), region
        if y0 > 7.0 and (x0 > -1 and x1 < 40.8 and z0 > -1 and z1 < 56.5):
            return 'exterior', region
        return 'landscape', region                       # (far glazing is baked opaque here)
    if is_glass(ob):
        return 'glass', region
    if idx is not None:                                  # shell / openings / exterior shell
        g = scene_objs[idx]['group']
        if g in ('roof', 'facade'):
            return 'exterior', region
        if g in ('ceiling', 'lighting', 'mirror'):
            return 'ceiling', region
        if g in WALLISH_GROUPS:
            return 'wall', region
        return 'base', region
    if core & {'openings'}:                               # core-built opening parts (e.g. W08 window)
        return 'wall', region
    if core & {'exterior_shell'}:
        return 'exterior', region
    if core & {'shell'}:
        return ('ceiling' if y0 >= 7.9 else 'base'), region
    # interior zone objects
    if y0 >= 7.0 or (is_emitter_only(ob) and y1 > 7.5):
        return 'ceiling', region
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


def cull_hidden_faces(ob, cls):
    """Delete faces that can never be seen, so atlases spend texels on visible surfaces only."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = []
    for f in bm.faces:
        n = f.normal
        c = f.calc_center_median()
        x, y, z = c.x / FT, c.z / FT, -c.y / FT          # SCENE feet
        inside = INSIDE[0] < x < INSIDE[1] and INSIDE[2] < z < INSIDE[3]
        if cls == 'base' and (n.z < -0.5 or (y < -0.005 and n.z > 0.5)):
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


def lightmap_uv(ob, margin_px, size):
    me = ob.data
    for uv in list(me.uv_layers):
        if uv.name == 'lm':
            me.uv_layers.remove(uv)
    lm = me.uv_layers.new(name='lm')
    me.uv_layers.active = lm               # bake target; keep the original active_render for textures
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    # AABB packing: our islands are near-rectangular and the default concave packer is ~1000x slower
    try:
        bpy.ops.uv.pack_islands(rotate=True, rotate_method='CARDINAL', shape_method='AABB',
                                margin_method='FRACTION', margin=margin_px / size)
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=False, margin=margin_px / size)
    bpy.ops.object.mode_set(mode='OBJECT')
    return lm


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


def denoise(img, w, h):
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
        tmp = os.path.join(CACHE_DIR, 'bake', f'_dn_{img.name}.exr')
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


def main():
    a = parse()
    t0 = time.time()
    sc = bpy.context.scene
    scene_objs = json.load(open(os.path.join(DATA_DIR, 'scene.json')))['objects']
    bake_dir = os.path.join(CACHE_DIR, 'bake')
    os.makedirs(bake_dir, exist_ok=True)

    # render / bake settings (GPU)
    sc.render.engine = 'CYCLES'
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
    # Same light balance as the panoramas; one house-wide white balance and interior exposure: the
    # medians of the per-stop values the panorama renders chose (render_meta.json).
    from bl import lighting
    lighting.apply_balance()
    metal_proxies()
    meta = json.load(open(a.meta)) if os.path.exists(a.meta) else {}

    def med(vals, default):
        vals = sorted(vals)
        return vals[len(vals) // 2] if vals else default
    wb_t = med([v['wb'][0] for v in meta.values() if 'wb' in v], 6000.0)
    wb_n = med([v['wb'][1] for v in meta.values() if 'wb' in v], 0.0)
    try:
        vs.use_white_balance = True
        vs.white_balance_temperature = wb_t
        vs.white_balance_tint = wb_n
    except AttributeError:
        pass
    wb_ext = tuple(float(v) for v in a.wb_ext.split(','))
    exp_int = a.exposure_int
    if exp_int is None:
        exp_int = med([v['exposure'] for v in meta.values()], 0.5)
    print(f'[bake] exposure interior {exp_int:+.2f}, exterior {a.exposure_ext:+.2f}, wb {wb_t:.0f}K/{wb_n:+.1f}')

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
        groups.setdefault((cls, key), []).append(ob)
        # walk-mode collision footprints for new interior furniture / built-ins (SCENE feet)
        if cls in ('furniture', 'base') and legacy_group(ob) is None and zone_of(ob) not in (None, 'exterior'):
            x0, x1, y0, y1, z0, z1 = bb
            fp = (x1 - x0) * (z1 - z0)
            if y0 < 1.6 and (y1 - y0) > 1.0 and 0.25 < fp < 140:
                collision.append({'name': ob.name[:40], 'x0': round(x0, 3), 'x1': round(x1, 3),
                                  'z0': round(z0, 3), 'z1': round(z1, 3), 'h': round(y1, 2)})
    print('[bake] groups:', {f'{k[0]}/{k[1]}': len(v) for k, v in groups.items()}, 'skipped:', skipped)

    # hide everything not exported? No: the full scene stays visible so baking sees all
    # occluders and bounce light (vegetation shadows included). Only copies are baked.
    exports = []
    stats = {}
    origins = {}
    for (cls, region), objs in sorted(groups.items()):
        tg = time.time()
        copies = []
        tris = 0
        for ob in objs:
            cp = evaluated_copy(ob, depsgraph, work)
            if not cp.data.polygons:
                bpy.data.objects.remove(cp)
                continue
            lawn_green(cp)
            if legacy_group(ob) is None:
                tris += decimate(cp, a.max_tris)
            else:
                tris += tri_count(cp.data)
            cp.hide_render = True                 # copies never occlude the bake
            copies.append(cp)
        if not copies:
            continue
        name = f'{cls}__{region}'
        t_copy = time.time() - tg
        g = join(copies, name)
        t_join = time.time() - tg - t_copy
        g['tg_class'] = cls
        g['tg_region'] = region
        origins[g.name] = objs
        if cls == 'glass':
            g.data.materials.clear()
            g.data.materials.append(glass_material())
            for uv in list(g.data.uv_layers):
                g.data.uv_layers.remove(uv)
            exports.append(g)
            stats[name] = {'tris': tris, 'atlas': 0}
            continue
        culled = cull_hidden_faces(g, cls)
        area = surface_area(g.data)
        scale = TEXEL_SCALE.get(cls, 1.0) * {'context': 0.4, 'ground': 0.0}.get(region, 1.0)
        side = math.sqrt(area / 0.62) * a.texel * scale
        size = int(2 ** math.ceil(math.log2(max(a.min_atlas, min(a.max_atlas, side)))))
        if region == 'ground':
            size = 512                            # flat lawn far from the house: lighting only
        lightmap_uv(g, 3.0, size)
        stats[name] = {'tris': tris, 'area_m2': round(area, 1), 'atlas': size, 'culled': culled}
        print(f'[prep] {name}: copy {t_copy:.1f}s join {t_join:.1f}s uv {time.time() - tg - t_copy - t_join:.1f}s', flush=True)
        exports.append(g)

    # ---- bake each group against the ORIGINAL scene (copies are hidden from render)
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
        try:
            dn = denoise(img, size, size)
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
        print(f'[bake] {g.name}: {size}px, {stats[g.name]["tris"]} tris, {stats[g.name]["bake_s"]}s', flush=True)

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
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop('export_image_format')
        bpy.ops.export_scene.gltf(**kw)
    json.dump(stats, open(os.path.splitext(a.out)[0] + '.bake.json', 'w'), indent=1)
    collision = prune_collision(collision)
    with open(os.path.join(os.path.dirname(os.path.abspath(a.out)), 'collision.json'), 'w') as f:
        json.dump({'units': 'ft', 'boxes': collision}, f, separators=(',', ':'))
    print(f'[bake] collision boxes: {len(collision)}')
    if a.keep_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(bake_dir, 'web_baked.blend'))
    total_tris = sum(v['tris'] for v in stats.values())
    print(f'[bake] exported {a.out} ({os.path.getsize(a.out) / 1e6:.1f} MB), {len(exports)} groups, '
          f'{total_tris} tris, {time.time() - t0:.0f}s')


main()
