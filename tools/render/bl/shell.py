"""Architectural shell: exact walls, floors, ceilings, openings, facade and roof from SCENE,
restyled with modern finishes (runs inside Blender).

Geometry is reproduced 1:1 from SCENE (same dimensions as the app's Dimensions/MEASUREMENTS
data). Only styling changes:
  * walls: paint inside, stucco outside, warm wood cladding facing the recessed entry porch
    (decided per face by testing a point just in front of the face against the room regions)
  * traditional details removed: muntins / divided lights / meeting rails, arched-window
    moldings, window casings and aprons; frames become matte black aluminum
  * the segmental-arch kitchen window (W08) becomes a flat-headed black three-panel window with
    the same width, sill and head (crown) height
  * kitchen skylight: fake emissive sky removed, real hole cut through the roof
  * fixtures / furniture / decor / landscape / garage door are NOT built here (room modules).
"""
import re

import bmesh
import bpy
import math

from mathutils import Matrix, Vector

from .common import FT, bl2ft, ft2bl

# Regions that count as conditioned interior for the inside/outside wall-face test.
EXCLUDE_REGIONS = {'porch'}
PORCH = (14.07, 20.69, 47.0, 51.4)        # recessed entry porch (x0, x1, z0, z1) ft

SKIP_DETAIL = re.compile(r'^(floor_plank|floor_line_detail|fake_sky|garage_door)')
SKIP_NAME = re.compile(
    r'muntin|divided light|meeting rail|Kitchen curved white molding|Kitchen arch side casing|'
    r'Kitchen three-sash mullion|Kitchen arched glass|Kitchen curved lintel|Kitchen arch sill|'
    r'sash latch|bronze latch|added west window — apron|added west window — casing head|'
    r'added west window — interior casing|Painted skirting — Living / kitchen — east wall|'
    r'hinge$|Bedroom 4 relocated door handle', re.I)   # concealed hinges (modern flush doors); B4 leftovers
# 'meeting rail' also matches the bay window's bottom/top frame rails; those stay (as black frame).
KEEP_RAIL = re.compile(r'bay transom and meeting rail', re.I)


def material_for(o, c):
    """Material key (or 'WALL' for per-face wall treatment) for a SCENE object, or None to skip."""
    name, detail, group = o['name'], c['detail'], o['group']
    if KEEP_RAIL.search(name):
        y0, y1 = c['aabb_ft'][2], c['aabb_ft'][3]
        return 'black_aluminum' if (y1 < 1.25 or y0 > 7.3) else None
    if SKIP_DETAIL.search(detail) or SKIP_NAME.search(name):
        return None
    if detail in ('wall', 'wall_header', 'gable_infill', 'stucco_skin'):
        return 'WALL'
    if detail == 'baseboard':
        return 'paint_trim'
    if detail == 'ceiling':
        return 'paint_ceiling'
    if detail == 'foundation':
        return 'foundation'
    if detail == 'floor_slab':
        if re.search(r'porcelain floor|warm stone floor', name):
            return 'tile_floor_bath'
        if re.search(r'shower stone floor', name):
            return 'tile_shower_floor'
        if 'Garage concrete' in name:
            return 'concrete_garage'
        if 'porch paving' in name:
            return 'porch_pavers'
        return 'oak_floor'
    if detail == 'window_frame':
        if re.search(r'limestone sill|stone sill', name):
            return 'quartz_white'
        if re.search(r'clerestory', name):
            return 'black_aluminum'
        if re.search(r'sill|reveal|added west window — jamb', name):
            return 'paint_trim'
        return 'black_aluminum'
    if detail == 'window_glass':
        return 'glass_frosted' if re.search(r'obscured|privacy', name) else 'glass_clear'
    if detail == 'door_glass':
        return 'glass_clear'
    if detail == 'door_leaf':
        return 'walnut_door' if 'front entrance' in name else 'door_slab'
    if detail == 'door_hardware':
        return 'black_metal'
    if detail == 'casing':
        if re.search(r'Garden door white (rail|stile)', name):
            return 'black_aluminum'
        if 'threshold' in name:
            return 'white_oak_veneer'
        if 'top track' in name:
            return 'black_metal'
        return 'paint_trim'
    if detail == 'skylight_shaft':
        return 'paint_ceiling'
    if detail == 'skylight_frame':
        return 'black_aluminum'
    if detail in ('fascia', 'exterior_trim'):
        return 'fascia_charcoal'
    if detail in ('roof_plane', 'roof_cap', 'roof_flashing'):
        return 'roof_metal'
    return 'paint_wall'


class _Regions:
    def __init__(self, ctx):
        self.boxes = [tuple(v['bounds_ft_x0x1z0z1']) for k, v in ctx.rooms.items() if k not in EXCLUDE_REGIONS]

    def inside(self, x, z):
        return any(x0 <= x <= x1 and z0 <= z <= z1 for x0, x1, z0, z1 in self.boxes)

    def between(self, x, z, d=0.55):
        """Point inside an interior wall's thickness (rooms on both sides): the jambs and soffits of
        uncased interior openings, which must be painted, not stucco."""
        return (self.inside(x - d, z) and self.inside(x + d, z)) or (self.inside(x, z - d) and self.inside(x, z + d))


def _wall_faces(ob, regions):
    """Assign per-face materials: 0 paint_wall (inside), 1 stucco (outside), 2 wood_cladding (porch)."""
    mw = ob.matrix_world
    rot = mw.to_3x3()
    for poly in ob.data.polygons:
        n = (rot @ poly.normal).normalized()
        c = mw @ poly.center
        x, y, z = bl2ft(c)
        nx, nz = n.x, -n.y                       # SCENE plan normal
        if abs(n.z) > 0.7:                       # horizontal faces: classify by own center
            px, pz = x, z
        else:
            px, pz = x + nx * 0.3, z + nz * 0.3
        if PORCH[0] <= px <= PORCH[1] and PORCH[2] <= pz <= PORCH[3] and y < 9.8:
            poly.material_index = 2
        elif regions.inside(px, pz) or regions.between(px, pz):
            poly.material_index = 0
        else:
            poly.material_index = 1


def _kitchen_window(ctx):
    """Modern flat-headed three-panel window replacing the segmental arch (W08)."""
    w = next(x for x in ctx.meas['windows'] if x['id'] == 'W08')
    x0, x1 = 40.61, 41.06                    # east wall thickness
    xc = 40.8367
    z0, z1 = 23.387, 29.387
    sill, head = 3.15, 7.75
    col = 'openings'
    hdr = ctx.box('W08 modern header', x0, x1, head, 8.0, z0, z1, None, col)
    hdr.data.materials.append(ctx.mat('paint_wall'))
    hdr.data.materials.append(ctx.mat('stucco'))
    hdr.data.materials.append(ctx.mat('wood_cladding'))
    ctx._wall_targets.append(hdr)
    fw, fd = 0.16, 0.22                      # frame face width / depth (ft)
    ctx.box('W08 frame head', xc - fd / 2, xc + fd / 2, head - fw, head, z0, z1, 'black_aluminum', col)
    ctx.box('W08 frame sill', xc - fd / 2, xc + fd / 2, sill, sill + fw, z0, z1, 'black_aluminum', col)
    ctx.box('W08 frame north', xc - fd / 2, xc + fd / 2, sill, head, z0, z0 + fw, 'black_aluminum', col)
    ctx.box('W08 frame south', xc - fd / 2, xc + fd / 2, sill, head, z1 - fw, z1, 'black_aluminum', col)
    for k in (1, 2):
        zm = z0 + (z1 - z0) * k / 3
        ctx.box(f'W08 mullion {k}', xc - fd / 2, xc + fd / 2, sill, head, zm - 0.06, zm + 0.06, 'black_aluminum', col)
    ctx.box('W08 glass', xc - 0.015, xc + 0.015, sill + fw, head - fw, z0 + fw, z1 - fw, 'glass_clear', col)
    ctx.box('W08 interior stool', x0 - 0.06, xc - fd / 2, sill - 0.06, sill, z0, z1, 'quartz_white', col)
    return w


def _skylight_roof_cut(ctx, roof_objs):
    """Boolean a 4x3 ft shaft through every roof object over the skylight (W16)."""
    x0, x1, z0, z1 = 29.40, 33.40, 25.55, 28.55
    cutter = ctx.box('skylight cutter', x0, x1, 9.0, 16.0, z0, z1, None, 'openings')
    hit = 0
    for ob in roof_objs:
        a = ctx.aabb(ob['scene_index'])
        if a[1] < x0 or a[0] > x1 or a[5] < z0 or a[4] > z1 or a[3] < 9.0:
            continue
        m = ob.modifiers.new('skylight', 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.solver = 'EXACT'
        m.object = cutter
        bpy.context.view_layer.objects.active = ob
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.object.modifier_apply(modifier=m.name)
        hit += 1
    bpy.data.objects.remove(cutter, do_unlink=True)
    return hit


# The concept's kitchen skylight straddled the garage-gable ridge; bl/revisions.py removes it and
# builds the architect-plan skylight on the east roof plane instead, so the old roof hole is not cut.
KITCHEN_SKYLIGHT_CUT = False

FRONT_DOOR_PIVOT = (18.74, 46.84)        # hinge axis of the inward-opening front door (SCENE x, z)
FRONT_DOOR_EXTRA_DEG = 25.0              # swing it from 90 to 115 deg, toward the hall wall, clear of E0's view


def _swing_front_door(ob):
    """Rotate a front-door leaf/hardware object about the hinge axis by FRONT_DOOR_EXTRA_DEG."""
    pv = ft2bl(FRONT_DOOR_PIVOT[0], 0.0, FRONT_DOOR_PIVOT[1])
    rot = Matrix.Translation(pv) @ Matrix.Rotation(-math.radians(FRONT_DOOR_EXTRA_DEG), 4, 'Z') @ Matrix.Translation(-pv)
    ob.matrix_basis = rot @ ob.matrix_basis      # (matrix_world is stale until the depsgraph updates)


def build(ctx):
    regions = _Regions(ctx)
    ctx._wall_targets = []
    roof_objs = []
    counts = {}
    for i, o in enumerate(ctx.objs):
        c = ctx.info(i)
        if c['role'] not in ('shell', 'opening', 'exterior'):
            continue
        key = material_for(o, c)
        if key is None:
            counts['skipped'] = counts.get('skipped', 0) + 1
            continue
        coll = {'shell': 'shell', 'opening': 'openings', 'exterior': 'exterior_shell'}[c['role']]
        if key == 'WALL':
            ob = ctx.import_original(i, 'paint_wall', coll)
            ob.data.materials.append(ctx.mat('stucco'))
            ob.data.materials.append(ctx.mat('wood_cladding'))
            ctx._wall_targets.append(ob)
        else:
            ob = ctx.import_original(i, key, coll)
            if key.startswith('glass'):
                ob.visible_shadow = True
        if c['detail'] in ('roof_plane', 'roof_cap', 'roof_flashing'):
            roof_objs.append(ob)
        if o['name'].startswith('Centered front entrance') and c['detail'] in ('door_leaf', 'door_hardware'):
            _swing_front_door(ob)
        counts[key] = counts.get(key, 0) + 1
    _kitchen_window(ctx)
    bpy.context.view_layer.update()
    for ob in ctx._wall_targets:
        _wall_faces(ob, regions)
    if KITCHEN_SKYLIGHT_CUT:
        counts['roof_cut'] = _skylight_roof_cut(ctx, roof_objs)
    ctx.stats['shell'] = counts
    return counts
