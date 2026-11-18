"""Stone feature wall with a linear gas fireplace and floating walnut ledge (runs inside Blender).

The stone is a polished, book-matched pair of grey-green onyx/quartzite slabs with flowing translucent
bands, milky drifts and soft rust-brown veins with gold rims (shaders in living_fire_mats.py).
Book-matching is done in the shader: texture space is mirrored about the centre seam (|z - seam|) and
wraps the side returns as a mitred edge, so the veins continue around corners; a hairline horizontal
joint at the firebox head splits each side into two slabs. The firebox has a black glass liner, a thin
glowing burner line under tumbled black / bronze fire glass, three rows of small procedural gas flames
(blue roots, golden bodies) and a thin-glass front.
"""
import math

import bpy

from ..common import FT, ft2bl
from .. import lighting
from . import living_fire_mats as FM
from . import living_geo as G

COLL = 'zone_living'


def liner_material():
    name = 'Z_living_firebox_liner'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (0.012, 0.012, 0.013, 1)
    b.inputs['Roughness'].default_value = 0.12
    b.inputs['Specular IOR Level'].default_value = 0.6
    m.diffuse_color = (0.02, 0.02, 0.02, 1)
    return m


# ------------------------------------------------------------------------------ build
def build(ctx, lights_coll, stone_z=(8.2, 15.0), face_x=39.75, wall_x=40.61, fire_y=(1.55, 2.85),
          fire_w=5.0, ledge_z1=16.9, ledge_depth=1.5, ledge_y=(1.05, 1.35), stone='library'):
    out = {}
    z0, z1 = stone_z
    zc = (z0 + z1) / 2
    # texture-space origin at the seam on the front face (Blender +X points into the wall)
    org = bpy.data.objects.new('living stone texspace', None)
    org.location = ft2bl(face_x, 4.0, zc)
    ctx.coll(COLL).objects.link(org)
    # 'library': materials.stone_feature (object-space book-match about the object origin = the
    # centre of this stone mass); 'own': the procedural slab in this module.
    smat = ctx.mat('stone_feature') if stone == 'library' else FM.stone_material(org)

    # stone mass with the firebox opening (EXACT boolean)
    stone = ctx.box('living stone feature wall', face_x, wall_x, 0.0, 8.0, z0, z1, smat, COLL)
    fz0, fz1 = zc - fire_w / 2, zc + fire_w / 2
    fy0, fy1 = fire_y
    cutter = ctx.box('living firebox cutter', face_x - 0.3, wall_x - 0.06, fy0, fy1, fz0, fz1, None, COLL)
    bm = stone.modifiers.new('opening', 'BOOLEAN')
    bm.operation = 'DIFFERENCE'
    bm.solver = 'EXACT'
    bm.object = cutter
    bpy.context.view_layer.objects.active = stone
    with bpy.context.temp_override(object=stone, active_object=stone):
        bpy.ops.object.modifier_apply(modifier=bm.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    # crisp but not razor-sharp arrises (eased 1/16")
    G.bevel(stone, 0.006, 2, angle=60)
    out['stone'] = stone

    # firebox: black reflective liner, trim, ember bed, flames, glass
    depth_back = wall_x - 0.07
    liner = []
    liner.append(G.box_verts(depth_back, depth_back + 0.02, fy0, fy1, fz0, fz1))          # back
    liner.append(G.box_verts(face_x, depth_back + 0.02, fy1 - 0.02, fy1, fz0, fz1))         # roof
    liner.append(G.box_verts(face_x, depth_back + 0.02, fy0, fy0 + 0.02, fz0, fz1))         # floor
    liner.append(G.box_verts(face_x, depth_back + 0.02, fy0, fy1, fz0, fz0 + 0.02))         # ends
    liner.append(G.box_verts(face_x, depth_back + 0.02, fy0, fy1, fz1 - 0.02, fz1))
    v, f = G.merge(*liner)
    G.obj(ctx, 'living firebox liner', v, f, liner_material(), COLL, smooth=False)
    # thin black trim frame proud of the stone by 1/8"
    tw, tp = 0.075, 0.012
    trim = [G.box_verts(face_x - tp, face_x + 0.03, fy1, fy1 + tw, fz0 - tw, fz1 + tw),
            G.box_verts(face_x - tp, face_x + 0.03, fy0 - tw, fy0, fz0 - tw, fz1 + tw),
            G.box_verts(face_x - tp, face_x + 0.03, fy0, fy1, fz0 - tw, fz0),
            G.box_verts(face_x - tp, face_x + 0.03, fy0, fy1, fz1, fz1 + tw)]
    v, f = G.merge(*trim)
    o = G.obj(ctx, 'living firebox trim', v, f, 'black_metal', COLL, smooth=False)
    G.bevel(o, 0.004, 1)
    # ember / glass media bed
    bed_x0 = face_x + 0.12
    v, f = G.box_verts(bed_x0, depth_back - 0.04, fy0 + 0.02, fy0 + 0.13, fz0 + 0.12, fz1 - 0.12)
    G.obj(ctx, 'living firebox ember bed', v, f, FM.ember_bed_material(), COLL, smooth=False)
    # tumbled fire-glass media (1/2-3/4in, black + smoked bronze) covering the bed, a few on top
    import random
    rnd = random.Random(11)
    nug = {'black': [], 'bronze': []}
    for k in range(2000):
        cx = rnd.uniform(bed_x0 + 0.02, depth_back - 0.05)
        cz = rnd.uniform(fz0 + 0.13, fz1 - 0.13)
        s = rnd.uniform(0.02, 0.034)
        nv_, nf_ = _nugget(s, rnd)
        lift = rnd.uniform(-0.012, 0.0) if k < 1550 else rnd.uniform(0.008, 0.02)
        nug['black' if rnd.random() < 0.7 else 'bronze'].append((G.translate(nv_, cx, fy0 + 0.13 + lift, cz), nf_))
    for tone, parts in nug.items():
        nv, nf = G.merge(*parts)
        G.obj(ctx, f'living firebox media {tone}', nv, nf, FM.media_material(tone), COLL, smooth=True)
    # flame sheets along the burner: back, middle and front rows of small procedural gas flames
    # (living_fire_mats.flame_material), purely additive, no shadows
    bz0, bz1 = fz0 + 0.3, fz1 - 0.3
    Lb = bz1 - bz0
    yb = fy0 + 0.11
    rows = (('back', depth_back - 0.16), ('mid', (bed_x0 + depth_back) / 2), ('front', bed_x0 + 0.1))
    for row, xk in rows:
        hk = FM.FLAME_ROWS[row][0]
        vv = [(xk, yb, bz1), (xk, yb, bz0), (xk, yb + hk, bz0), (xk, yb + hk, bz1)]
        uv = [(0.0, 0.0), (Lb, 0.0), (Lb, 1.0), (0.0, 1.0)]
        ob = G.obj(ctx, f'living flame {row}', vv, [(0, 1, 2, 3)], FM.flame_material(row, length=Lb),
                   COLL, smooth=False, uvs=uv)
        ob.visible_shadow = False
    # glass front
    from .. import materials
    glass = bpy.data.materials.get('Z_living_fire_glass') or materials.thin_glass('Z_living_fire_glass', tint=(0.9, 0.9, 0.88))
    ctx.box('living firebox glass', face_x + 0.04, face_x + 0.05, fy0, fy1, fz0, fz1, glass, COLL)
    # warm fire glow (area light just behind the glass, aimed into the room)
    ld = bpy.data.lights.new('living fire glow', 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size = (fire_w - 0.4) * FT
    ld.size_y = 0.35 * FT
    ld.energy = 14.0
    ld.color = lighting.kelvin_rgb(1700)
    try:
        ld.cycles.cast_shadow = True
    except AttributeError:
        pass
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(face_x + 0.25, fy0 + 0.45, zc)
    # area lights emit along local -Z; point it toward SCENE -x (Blender -X)
    lo.rotation_euler = (0, math.radians(90), 0)
    try:
        lo.visible_camera = False
        lo.visible_glossy = False      # the ledge and glass reflect the flames themselves, not a lamp card
    except AttributeError:
        pass
    ctx.coll(lights_coll).objects.link(lo)

    # floating walnut ledge: front edge straight, back scribed to the stone and the wall
    lx0 = face_x - ledge_depth
    outline = [(lx0, z0 - 0.0), (face_x - 0.001, z0 - 0.0), (face_x - 0.001, z1), (wall_x - 0.001, z1),
               (wall_x - 0.001, ledge_z1), (lx0, ledge_z1)]
    v, f = G.prism(outline, ledge_y[0], ledge_y[1])
    led = G.obj(ctx, 'living hearth ledge', v, f, 'walnut_slab', COLL, smooth=False)
    G.bevel(led, 0.02, 3, angle=40)
    out['ledge_top'] = ledge_y[1]
    out['firebox'] = (fz0, fz1, fy0, fy1)
    return out


def _nugget(s, rnd):
    """Small tumbled glass nugget: a once-subdivided octahedron pushed to a squashed, irregular pebble."""
    base = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    tri = [(0, 2, 4), (4, 2, 1), (1, 2, 5), (5, 2, 0), (0, 4, 3), (4, 1, 3), (1, 5, 3), (5, 0, 3)]
    pts = [list(p) for p in base]
    mid = {}

    def m(a, b):
        key = (min(a, b), max(a, b))
        if key not in mid:
            p = [(pts[a][i] + pts[b][i]) / 2 for i in range(3)]
            n = math.sqrt(sum(c * c for c in p))
            pts.append([c / n for c in p])
            mid[key] = len(pts) - 1
        return mid[key]
    faces = []
    for a, b, c in tri:
        ab, bc, ca = m(a, b), m(b, c), m(c, a)
        faces += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    sx, sy, sz = s * rnd.uniform(0.8, 1.25), s * rnd.uniform(0.45, 0.7), s * rnd.uniform(0.8, 1.25)
    yaw = rnd.uniform(0, math.pi)
    cy, sn = math.cos(yaw), math.sin(yaw)
    out = []
    for x, y, z in pts:
        j = rnd.uniform(0.85, 1.12)
        x, y, z = x * sx * j, y * sy * j, z * sz * j
        out.append((x * cy - z * sn, y, x * sn + z * cy))
    return out, faces
