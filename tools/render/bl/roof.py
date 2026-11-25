"""v7 roof (eighth round, 2026-11-24): the roof of the architect's set, built in plan feet after the warp.

Until the seventh round the roof was the concept's massing carried along by bl/warp.py: planes of 4.0 to 6.5 in 12,
the main ridge 9.7 in and the garage ridge 6.3 in too low, eaves of 5 1/4 in, an entry ridge that fell 1'-7 1/2"
toward the street and a flat canopy over the porch (audit F46..F49, F61). rebuild() removes all of it and builds
the roof the sheets draw:

  A1.3 (elevations)   every plane 5 in 12; the roof's top surface passes 8.539 ft above the floor over the walls'
                      outer faces and ends 1'-0" outside them in a plumb fascia 6 1/2 in deep (top 8.122, bottom
                      7.581). The slab is 6 1/2 in thick measured plumb, so its underside lands on the walls' outer
                      top corner (7.997) and is the sloping closed soffit of the eaves.
  A1.2 (existing)     hip roof over the main block (eaves on the west, rear and east walls and on the old front
                      wall's line, z 29.892): ridge z 14.35 from x 14.35 to 25.18 at 14.598 (the sheet prints
                      14'-7"); the east plane runs on over the garage, whose ridge (x 30.517, 12.375 = 12'-4 1/2")
                      ends in the front gable; between them the two short planes of the old entry (eaves x 13.808
                      and z 32.729: WB faces west, SB faces south) with their ridge x 27.267, hips and valleys.
  SKA001 (new)        the bedroom wing's gable roof and the entry's, "(N) 5/12", both ridges level. The wing's west
                      plane is the main roof's west plane running on to the front gable. The entry roof is a raised
                      gable: its ridge dies into the main roof's south plane at z 19.14 (SKA001), which puts it at
                      12.602 ft; its eaves stand 1'-0" outside the foyer's side walls, above the wing's and the
                      garage's planes, on two stucco cheek walls; it runs on over the porch to 1'-0" past the slab's
                      front edge (z 56.142) and replaces the flat canopy.

The owner's second round moved the foyer-side wall of Bedroom 4 / Bedroom 3 onto the shared bath's wall line
(relayout.FOYER_WALL): the wing is 1'-3" wider and the foyer 1'-3" narrower than the sheet's. The sheet centres the
wing's ridge on the wing and the entry's on the foyer, so both ridges stay centred on what is built: x 7.683 (sheet
7.059) and x 18.433 (sheet 17.808), as the audit records them ("owner_decision"). Every other line is the sheet's.

Also here, because they follow the roof: the two front gables' stucco, Bedroom 3's vaulted ceiling (re-fitted: 8'-0"
at the walls, 5 in 12, 11.108 at the ridge, a closed 5/8 in void under the roof), the entry vault (level now: 5 in
12 about the foyer's centre line, 10'-11" at the ridge, a closed void above; its rear gable straightened), the
foyer's walls above 8 ft (one wall each instead of 24 stepped knee-wall pieces), the wall over the front door with
the clerestory window's opening, the porch's piers (up to the roof), tie beam, king post and wood soffit.

bl/revisions.py calls rebuild() before the skylights, which cut their wells through whatever roof is there.
Names: every new piece starts with "v7 roof"; the roof's own pieces live in `exterior_shell` (bl/revisions.roof_y
and skylight() treat that collection as roof, names with "stucco" excepted).
"""
import math
import os
import re
import sys

import bmesh
import bpy
import numpy as np

from .common import FT, ft2bl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import relayout as R  # noqa: E402

# ------------------------------------------------------------------------------------------------ the sheets
P = 5.0 / 12.0                      # every plane (A1.2, A1.3, SKA001)
EAVE_Y = 8.122                      # top of the fascia = the roof's surface on the eave line (A1.3)
FASCIA = 6.5 / 12.0                 # plumb depth of the fascia = of the roof slab (A1.3: 8.122 .. 7.581)
OVH = 1.0                           # eave and rake overhang, from the walls' outer faces (A1.0, A1.2, SKA001)
# eave lines
XW_E, ZN_E, XE_E = R.XW_OUT - OVH, R.ZN_OUT - OVH, R.XE_OUT + OVH     # west, rear, east: -1.192, -1.192, 40.725
ZS_E = R.Z_B4_N + OVH               # 29.892: the main block's front eave, 1'-0" outside the old front wall (A1.2)
XG_E = R.X_FOYER_E - OVH            # 20.308: the garage's west eave line (its west wall's outer face is the foyer's)
XWE_E = R.X_FOYER_W + OVH           # 16.558: the wing's east eave line (it dies into the entry's cheek wall before)
XWB_E = R.X_FOYER_E - 7.5           # 13.808: A1.2, the old entry roof's west eave (plane WB)
ZSB_E = 32.729                      # A1.2, the old entry roof's south eave (plane SB)
ZW_R = R.Z_B3_OUT + OVH             # 55.142: Bedroom 3's gable, rake edge
ZG_R = R.Z_GAR_OUT + OVH            # 53.808: the garage's gable, rake edge
# the entry roof
ENTRY_C = (R.X_FOYER_W + R.X_FOYER_E) / 2          # 18.433: ridge, on the foyer's centre line
ENTRY_X = (R.X_SBATH_E - OVH, R.X_GAR_W + OVH)     # 14.142, 22.725: eaves, 1'-0" outside the foyer's side walls
ENTRY_TIP_Z = 19.14                 # SKA001: where the entry ridge meets the main roof's south plane
ENTRY_FRONT = R.Z_PORCH_S + OVH     # 56.142: 1'-0" past the porch slab's front edge (SKA001)
ENTRY_Y = EAVE_Y + (ZS_E - ENTRY_TIP_Z) * P        # 12.602: the entry ridge (level)
ENTRY_EAVE_Y = ENTRY_Y - (ENTRY_C - ENTRY_X[0]) * P    # 10.814: top of the entry roof's fascia
XCW = (R.X_SBATH_E + R.X_FOYER_W) / 2              # 15.350: centre line of the west cheek wall (the lower roofs end in it)
XCE = (R.X_FOYER_E + R.X_GAR_W) / 2                # 21.517: centre line of the east cheek wall
# ceilings that follow the roof
VAULT_T = 0.12                      # ceiling slabs
BED3_SPRING = 8.0                   # Bedroom 3's vault at the walls' faces (the walls end at 8 ft)
ENTRY_VAULT_Y = 10.0 + 11.0 / 12.0  # the entry vault's ridge, level: its height under the pendant until now
# porch
BEAM_Y = (9.55, 10.30)              # tie beam between the piers
BEAM_D = 0.5
SOFFIT_T = 0.035                    # wood lining under the porch roof
CLAD_T = 0.015                      # v7 repair: wood board skin on the porch's two side walls (3/16 in proud)

COLL = 'exterior_shell'
PRE = 'v7 roof'

# planes of the roof's top surface: y = c + ax x + az z
PL = {
    'N': (EAVE_Y - ZN_E * P, 0.0, P),
    'W': (EAVE_Y - XW_E * P, P, 0.0),
    'E': (EAVE_Y + XE_E * P, -P, 0.0),
    'S': (EAVE_Y + ZS_E * P, 0.0, -P),
    'WB': (EAVE_Y - XWB_E * P, P, 0.0),
    'SB': (EAVE_Y + ZSB_E * P, 0.0, -P),
    'GW': (EAVE_Y - XG_E * P, P, 0.0),
    'WE': (EAVE_Y + XWE_E * P, -P, 0.0),
    'EnW': (ENTRY_EAVE_Y - ENTRY_X[0] * P, P, 0.0),
    'EnE': (ENTRY_EAVE_Y + ENTRY_X[1] * P, -P, 0.0),
}


def top(pl, x, z):
    c, ax, az = PL[pl] if isinstance(pl, str) else pl
    return c + ax * x + az * z


# plan points (x, z)
_HALF = (ZS_E - ZN_E) / 2
ZR = ZN_E + _HALF                                   # 14.350  main ridge
MAIN_Y = EAVE_Y + _HALF * P                         # 14.598
M1, M2 = (XW_E + _HALF, ZR), (XE_E - _HALF, ZR)     # its ends, x 14.350 and 25.183
WING_X = (XW_E + XWE_E) / 2                         # 7.683   the wing's ridge
WING_Y = EAVE_Y + (WING_X - XW_E) * P               # 11.820
A_W = (WING_X, ZR + (M1[0] - WING_X))               # its north end, on the main roof's south-west hip (z 21.017)
GAR_X = (XG_E + XE_E) / 2                           # 30.517  the garage's ridge
GAR_Y = EAVE_Y + (XE_E - GAR_X) * P                 # 12.375
XR2 = (XWB_E + XE_E) / 2                            # 27.267  ridge between WB and the east plane
B1 = (XR2, ZR + (XR2 - M2[0]))                      # end of the short south-east hip (z 16.433)
B2 = (XR2, ZSB_E - (XR2 - XWB_E))                   # top of the hip between WB and SB (z 19.270)
B3 = (GAR_X, ZSB_E - (XE_E - GAR_X))                # north end of the garage's ridge (z 22.521)
TP = (ENTRY_C, ENTRY_TIP_Z)                         # north end of the entry's ridge
V_W = (ENTRY_X[0], ENTRY_TIP_Z + (ENTRY_C - ENTRY_X[0]))        # the entry's west eave leaves the south plane (z 23.432)
_XT = (ENTRY_X[1] + XWB_E + (ENTRY_EAVE_Y - EAVE_Y) / P) / 2    # 21.497: valley between the entry's east plane and WB
T1 = (_XT, ENTRY_TIP_Z + (_XT - ENTRY_C))           # ... its north end (S, WB and the entry meet)
T2 = (_XT, ZSB_E - (_XT - XWB_E))                   # ... its south end (WB, SB and the entry meet)
T3 = (ENTRY_X[1], T2[1] + (ENTRY_X[1] - _XT))       # the entry's east eave leaves SB (z 26.269)
Q_W = (XCW, ENTRY_TIP_Z + (ENTRY_C - XCW))          # the entry's west valley over the cheek's centre line
R_W = (XCW, A_W[1] + (XCW - WING_X))                # the valley between S and the wing's east plane, at the cheek
C_E = (XCE, B3[1] + (GAR_X - XCE))                  # the valley between SB and the garage's west plane, at the cheek
Q_E = (XCE, T2[1] + (XCE - _XT))                    # the valley between the entry's east plane and SB, at the cheek
assert _XT < XCE < ENTRY_X[1] and XCW > ENTRY_X[0]


def entry_under(x):
    """Underside of the entry roof (the cheek walls', piers' and gable wall's top; the porch soffit's back)."""
    return ENTRY_Y - FASCIA - abs(x - ENTRY_C) * P


def bed3_vault(x):
    """Bedroom 3's ceiling: 8'-0" at the two wall faces, 5 in 12 up to the wing's ridge."""
    half = (R.X_SBATH_E - R.XW) / 2
    return BED3_SPRING + (half - abs(x - WING_X)) * P


def entry_vault(x):
    return ENTRY_VAULT_Y - abs(x - ENTRY_C) * P


def wing_under(x):
    return min(top('W', x, 0), top('WE', x, 0)) - FASCIA


def garage_under(x):
    return min(top('GW', x, 0), top('E', x, 0)) - FASCIA


# ------------------------------------------------------------------------------------------------ mesh helpers
def _bbox(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world)
    w = co @ mw[:3, :3].T + mw[:3, 3]
    return (w[:, 0].min() / FT, w[:, 0].max() / FT, w[:, 2].min() / FT, w[:, 2].max() / FT,
            -w[:, 1].max() / FT, -w[:, 1].min() / FT)


def _find(pattern, coll=None):
    rx = re.compile(pattern)
    return [ob for ob in bpy.data.objects if rx.search(ob.name)
            and (coll is None or any(c.name == coll for c in ob.users_collection))]


def _remove(obs):
    n = 0
    for ob in list(obs):
        bpy.data.objects.remove(ob, do_unlink=True)
        n += 1
    return n


def _fill(me, verts, faces, face_mat=None):
    """Closed mesh from SCENE-feet vertices (x, y, z) and faces; normals outward; face_mat(normal, centre) -> index
    (both in SCENE axes)."""
    bm = bmesh.new()
    vs = [bm.verts.new(ft2bl(*p)) for p in verts]
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    if face_mat:
        for f in bm.faces:
            n = f.normal
            c = f.calc_center_median()
            f.material_index = face_mat((n.x, n.z, -n.y), (c.x / FT, c.z / FT, -c.y / FT))
    bm.to_mesh(me)
    bm.free()
    me.update()


def _solid(ctx, name, verts, faces, mats, face_mat=None, coll=COLL):
    me = bpy.data.meshes.new(name)
    _fill(me, verts, faces, face_mat)
    for m in mats:
        me.materials.append(ctx.mat(m))
    ob = bpy.data.objects.new(name, me)
    ctx.coll(coll).objects.link(ob)
    return ob


def _prism_faces(n):
    """Faces of a prism whose vertices are a lower ring 0..n-1 and an upper ring n..2n-1."""
    f = [list(range(n - 1, -1, -1)), list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append([i, j, n + j, n + i])
    return f


def _roof_face(n, c):
    return 0 if n[1] > 0.5 else (1 if n[1] < -0.5 else 2)


def slab(ctx, name, poly, pl, soffit='stucco'):
    """One roof plane: a slab FASCIA thick (plumb) under the plane `pl` over the plan polygon `poly`. Top standing
    seam metal, underside the soffit, edges the charcoal fascia / bargeboard."""
    lo = [(x, top(pl, x, z) - FASCIA, z) for x, z in poly]
    hi = [(x, top(pl, x, z), z) for x, z in poly]
    return _solid(ctx, f'{PRE} plane {name}', lo + hi, _prism_faces(len(poly)),
                  ['roof_metal', soffit, 'fascia_charcoal'], _roof_face)


def wall_x(ctx, name, prof, z0, z1, mats, face_mat, coll=COLL):
    """A wall piece whose elevation `prof` [(x, y), ...] is extruded from z0 to z1."""
    lo = [(x, y, z0) for x, y in prof]
    hi = [(x, y, z1) for x, y in prof]
    return _solid(ctx, name, lo + hi, _prism_faces(len(prof)), mats, face_mat, coll)


def box(ctx, name, x0, x1, y0, y1, z0, z1, mat, coll=COLL):
    return wall_x(ctx, name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, [mat], None, coll)


def strip(ctx, name, a, b, pa, pb, half, lift_c, lift_s, valley=False, trim=(0.0, 0.0)):
    """Ridge / hip cap (a low tent of roofing metal over the joint of the planes pa and pb from a to b) or, with
    valley=True, the valley's flashing lying in it. trim = how far it stops short of a and of b (where it would
    run into another cap, or past an eave corner)."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dz)
    a = (a[0] + dx / ln * trim[0], a[1] + dz / ln * trim[0])
    b = (b[0] - dx / ln * trim[1], b[1] - dz / ln * trim[1])
    nx, nz = -dz / ln * half, dx / ln * half
    env = max if valley else min

    def pt(p, s, lift):
        x, z = p[0] + s * nx, p[1] + s * nz
        return (x, env(top(pa, x, z), top(pb, x, z)) + lift, z)
    v = [pt(a, -1, lift_s), pt(a, 0, lift_c), pt(a, 1, lift_s), pt(b, -1, lift_s), pt(b, 0, lift_c), pt(b, 1, lift_s),
         pt(a, 0, -0.01), pt(b, 0, -0.01)]                 # the joint itself under each end: the ends are closed
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new(ft2bl(*p)) for p in v]
    for f in ((0, 1, 4, 3), (1, 2, 5, 4)) + (() if valley else ((0, 6, 2, 1), (3, 4, 5, 7))):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    if bm.faces[0].normal.z < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ctx.mat('roof_metal'))
    ob = bpy.data.objects.new(name, me)
    ctx.coll(COLL).objects.link(ob)
    return ob


def _refit(ob, prof, ridge_from=None, ridge_to=None, above=8.05):
    """Move the vertices of a concept gable piece that stand above `above` onto the profile y = prof(x); the apex
    (x near ridge_from) goes to ridge_to first."""
    mw = ob.matrix_world
    inv = mw.inverted()
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    n = 0
    for v in ob.data.vertices:
        w = mw @ v.co
        x, y, z = w.x / FT, w.z / FT, -w.y / FT
        if y <= above:
            continue
        if ridge_from is not None and abs(x - ridge_from) < 0.6:
            x = ridge_to
        v.co = inv @ ft2bl(x, prof(x), z)
        n += 1
    ob.data.update()
    return n


def _remesh(ob, verts, faces, face_mat=None):
    """Replace an object's mesh, keeping the object (name, collection, materials, scene_index)."""
    ob.matrix_world.identity()
    ob.location = (0, 0, 0)
    ob.rotation_euler = (0, 0, 0)
    ob.scale = (1, 1, 1)
    me = ob.data if ob.data.users == 1 else ob.data.copy()
    ob.data = me
    me.clear_geometry()
    _fill(me, verts, faces, face_mat)


# ------------------------------------------------------------------------------------------------ the roof
OLD_ROOF = (r'^\d+ (Main house hip|Garage gable|Bedroom addition gable|Entry gable|Rear tie-in drainage cricket) '
            r'joined plane|^\d+ Continuous white perimeter fascia|^\d+ Shingle ridge / hip cap|'
            r'^\d+ Recessed metal valley flashing|^\d+ Entry stucco gable / roof cheek|'
            r'^\d+ Entry white gable bargeboard')


def _porch_posts():
    """The two piers (x0, x1, z0, z1) as the exterior zone builds them, or the sheet's when the zone is not built."""
    try:
        from .zones import exterior_layout as L
        return [tuple(p) for p in L.PORCH_POSTS]
    except Exception:
        w = 17.0 / 12.0
        return [(R.X_FOYER_W - w, R.X_FOYER_W, R.Z_PORCH_S - w, R.Z_PORCH_S),
                (R.X_FOYER_E, R.X_FOYER_E + w, R.Z_GAR_OUT - 0.2, R.Z_PORCH_S)]


def planes(ctx):
    pw, pe = _porch_posts()
    polys = {
        'N main rear': ('N', [(XW_E, ZN_E), (XE_E, ZN_E), M2, M1]),
        'W main and wing west': ('W', [(XW_E, ZN_E), M1, A_W, (WING_X, ZW_R), (XW_E, ZW_R)]),
        'E main and garage east': ('E', [(XE_E, ZN_E), (XE_E, ZG_R), (GAR_X, ZG_R), B3, B2, B1, M2]),
        'S main south': ('S', [M1, M2, B1, T1, TP, Q_W, R_W, A_W]),
        'WB old entry west': ('WB', [B1, B2, T2, T1]),
        'SB old entry south': ('SB', [B2, B3, C_E, Q_E, T2]),
        'GW garage west': ('GW', [B3, (GAR_X, ZG_R), (pe[1], ZG_R), (pe[1], R.Z_GAR_OUT), (XCE, R.Z_GAR_OUT), C_E]),
        'WE wing east': ('WE', [A_W, R_W, (XCW, pw[2]), (pw[0], pw[2]), (pw[0], ZW_R), (WING_X, ZW_R)]),
        'EnW entry west': ('EnW', [TP, V_W, (ENTRY_X[0], ENTRY_FRONT), (ENTRY_C, ENTRY_FRONT)]),
        'EnE entry east': ('EnE', [TP, (ENTRY_C, ENTRY_FRONT), (ENTRY_X[1], ENTRY_FRONT), T3, T2, T1]),
    }
    for name, (pl, poly) in polys.items():
        slab(ctx, name, poly, pl)
    return len(polys)


def caps(ctx):
    rc = dict(half=0.22, lift_c=0.02, lift_s=0.008)       # low: the caps' tops stay within 1/2 in of A1.3's heights
    vc = dict(half=0.42, lift_c=0.008, lift_s=0.008, valley=True)
    j = 0.26                                                # a hip's cap stops short of the ridge cap it meets
    ridges = [('ridge main', M1, M2, 'N', 'S', (0, 0)), ('ridge wing', A_W, (WING_X, ZW_R), 'W', 'WE', (0, 0)),
              ('ridge garage', B3, (GAR_X, ZG_R), 'GW', 'E', (0, 0)), ('ridge old entry', B1, B2, 'WB', 'E', (0, 0)),
              ('ridge entry', TP, (ENTRY_C, ENTRY_FRONT), 'EnW', 'EnE', (0, 0)),
              ('hip north-west', (XW_E, ZN_E), M1, 'N', 'W', (0.34, j)),      # ... and of the eave's corner
              ('hip north-east', (XE_E, ZN_E), M2, 'N', 'E', (0.34, j)),
              ('hip south-west', M1, A_W, 'W', 'S', (j, j)), ('hip south-east', M2, B1, 'S', 'E', (j, j)),
              ('hip old entry east', B2, B3, 'SB', 'E', (j, j)), ('hip old entry', B2, T2, 'WB', 'SB', (j, 0.45))]
    xw, xe = R.X_SBATH_E, R.X_GAR_W                         # the cheeks' outer faces
    v = 0.45
    valleys = [('valley wing', A_W, (xw, A_W[1] + (xw - WING_X)), 'S', 'WE', (v, 0)),
               ('valley old entry', B1, T1, 'S', 'WB', (v, v)),
               ('valley garage', B3, (xe, B3[1] + (GAR_X - xe)), 'SB', 'GW', (v, 0)),
               ('valley entry west', TP, V_W, 'S', 'EnW', (v, 0)), ('valley entry east', TP, T1, 'S', 'EnE', (v, v)),
               ('valley entry WB', T1, T2, 'EnE', 'WB', (v, v)), ('valley entry SB', T2, T3, 'EnE', 'SB', (v, 0))]
    for name, a, b, pa, pb, tr in ridges:
        strip(ctx, f'{PRE} cap {name}', a, b, pa, pb, trim=tr, **rc)
    for name, a, b, pa, pb, tr in valleys:
        strip(ctx, f'{PRE} flashing {name}', a, b, pa, pb, trim=tr, **vc)
    return len(ridges) + len(valleys)


WALL_MATS = ['paint_wall', 'stucco', 'wood_cladding', 'paint_trim']


def _face_material(origin, direction):
    """Name of the material on the first face a ray from `origin` (SCENE ft) along `direction` meets ('' if none)."""
    from mathutils import Vector
    dg = bpy.context.evaluated_depsgraph_get()
    d = Vector((direction[0], -direction[2], direction[1]))
    hit, loc, nrm, idx, ob, _m = bpy.context.scene.ray_cast(dg, ft2bl(*origin), d, distance=4.0 * FT)
    if not hit or ob.type != 'MESH':
        return ''
    try:
        me = ob.evaluated_get(dg).data
        m = ob.material_slots[me.polygons[idx].material_index].material
        return m.name.lower() if m else ''
    except Exception:
        return ''


def entry_walls(ctx, zv0):
    """The foyer's two side walls above 8 ft (cheek walls of the raised entry roof) and the wall over the front door.
    zv0 = where the entry vault begins (north of it the foyer has its flat ceiling and the cheeks stand on it)."""
    pw, pe = _porch_posts()
    zd = (R.Z_FOYER_S + R.Z_PORCH_N) / 2                    # the front door wall's centre line
    n = 0
    for tag, x0, x1, inner, zn, zs, pl in (
            ('W', R.X_SBATH_E, R.X_FOYER_W, 1.0, ZS_E - (entry_under(R.X_SBATH_E) - EAVE_Y) / P - 0.5, pw[2], 'S'),
            ('E', R.X_FOYER_E, R.X_GAR_W, -1.0, ZSB_E - (entry_under(R.X_GAR_W) - EAVE_Y) / P - 0.5, pe[2], 'SB')):
        # the porch side of each wall carries on what the wall has below 8 ft (wood on the west wall; the east
        # wall's porch face is painted like its foyer face: one wall piece runs through both)
        below = _face_material(((x1 if inner > 0 else x0) + inner * 1.0, 7.4, zd + 2.2), (-inner, 0.0, 0.0))
        porch_mi = 2 if 'wood' in below else (1 if 'stucco' in below else 0)

        def fm(nrm, c, inner=inner, zd=zd, porch_mi=porch_mi):
            if nrm[0] * inner > 0.5:                        # the face toward the foyer / the porch
                return 0 if c[2] < zd else porch_mi
            return 1
        for part, za, zb, y0 in (('attic', zn, zv0 - 0.2, 8.13), ('foyer', zv0 - 0.2, zd, 8.0), ('porch', zd, zs, 8.0)):
            prof = [(x0, y0), (x1, y0), (x1, entry_under(x1)), (x0, entry_under(x0))]
            # (the part beside the entry vault is a wall of the foyer: collection `shell`, so the web bake shows it
            # indoors like the ceilings; the other two are outside)
            wall_x(ctx, f'{PRE} entry cheek stucco {tag} {part}', prof, za, zb, WALL_MATS, fm,
                   'shell' if part == 'foyer' else COLL)
            n += 1
    # the wall over the front door: from the 8 ft line to the roof, round the clerestory window's opening
    old = _find(r'^\d+ Coordinated entry high-window surround')
    hx0, hx1, head = ENTRY_C - 1.5, ENTRY_C + 1.5, 9.75
    mid = [o for o in old if _bbox(o)[2] > 8.5]
    if mid:
        b = [_bbox(o) for o in mid]
        hx0, hx1, head = min(v[0] for v in b), max(v[1] for v in b), min(v[2] for v in b)
    _remove(old)

    def fg(nrm, c):
        return 0 if nrm[2] < -0.5 else (2 if nrm[2] > 0.5 else 3)
    xa, xb = R.X_FOYER_W, R.X_FOYER_E
    for tag, prof in (('west', [(xa, 8.0), (hx0, 8.0), (hx0, entry_under(hx0)), (xa, entry_under(xa))]),
                      ('east', [(hx1, 8.0), (xb, 8.0), (xb, entry_under(xb)), (hx1, entry_under(hx1))]),
                      ('head', [(hx0, head), (hx1, head), (hx1, entry_under(hx1)), (ENTRY_C, entry_under(ENTRY_C)),
                                (hx0, entry_under(hx0))])):
        wall_x(ctx, f'{PRE} entry gable wall stucco {tag}', prof, R.Z_FOYER_S, R.Z_PORCH_N, WALL_MATS, fg, 'shell')
        n += 1
    return {'pieces': n, 'clerestory opening': (round(hx0, 3), round(hx1, 3), round(head, 3))}


def gables(ctx):
    """The two front gables' stucco and Bedroom 3's two interior gable pieces, onto the new roof / the new vault."""
    out = {}
    for pat, prof, rf, rt in ((r'^\d+ Bedroom 3 solid white stucco front gable', wing_under, 7.66, WING_X),
                              (r'^\d+ Garage stucco front gable', garage_under, 30.45, GAR_X),
                              (r'^\d+ Bedroom 3 solid front gable plaster', lambda x: bed3_vault(x) + VAULT_T, 7.66, WING_X),
                              (r'^\d+ Bedroom 3 gable infill', lambda x: bed3_vault(x) + VAULT_T, 7.70, WING_X)):
        for ob in _find(pat):
            out[ob.name[:40]] = _refit(ob, prof, rf, rt)
    # Bedroom 3's two gable walls above 8 ft stood 0.09 ft behind the faces of the walls below them (a ledge at the
    # 8 ft line); their room-side faces come onto those faces (1 mm proud, so the south one also covers the porch
    # pier, whose north face lies in the front wall's inside face and now runs up past 8 ft)
    # v7 integrate: the garage's stucco gable stood 0.043 ft (1/2 in) in front of the stucco of the wall below it (a
    # shadow line at 8 ft across the garage front); its street face comes onto that face, as Bedroom 3's gable is
    for pat, north_side, z in ((r'^\d+ Bedroom 3 solid front gable plaster', True, R.Z_B3_S - 0.004),
                               (r'^\d+ Bedroom 3 gable infill', False, R.Z_B3_N + 0.004),
                               (r'^\d+ Garage stucco front gable', False, R.Z_GAR_OUT - 0.005)):
        for ob in _find(pat):
            b = _bbox(ob)
            mid = (b[4] + b[5]) / 2
            mw = ob.matrix_world
            inv = mw.inverted()
            for v in ob.data.vertices:
                w = mw @ v.co
                if (-w.y / FT < mid) == north_side:
                    v.co = inv @ ft2bl(w.x / FT, w.z / FT, z)
            ob.data.update()
            out[ob.name[:40] + ' face z'] = round(z, 3)
    # v7 repair: Bedroom 3's gable above 8 ft was smooth wall paint on its street face (as in the concept shell),
    # over the textured stucco of the wall below it: the finish changed along the 8 ft line. Stucco on every face,
    # like the garage's gable.
    for ob in _find(r'^\d+ Bedroom 3 solid white stucco front gable'):
        si = next((i for i, sl in enumerate(ob.material_slots) if sl.material and 'stucco' in sl.material.name.lower()), None)
        if si is None:
            ob.data.materials.append(ctx.mat('stucco'))
            si = len(ob.material_slots) - 1
        if ob.data.users > 1:
            ob.data = ob.data.copy()
        for poly in ob.data.polygons:
            poly.material_index = si
        out[ob.name[:40] + ' finish'] = 'stucco'
    return out


def bed3_ceiling(ctx):
    """Bedroom 3's vaulted ceiling, parallel to the new roof: 8'-0" at the two walls, 5 in 12, ridge on the wing's."""
    out = {}
    was = None
    for ob in _find(r'^\d+ Bedroom 3 vaulted ceiling'):
        b = _bbox(ob)
        was = max(was or 0, b[3] - VAULT_T)
        west = (b[0] + b[1]) / 2 < WING_X
        xa, xb = (b[0], WING_X) if west else (WING_X, b[1])
        ring = [(xa, b[4]), (xb, b[4]), (xb, b[5]), (xa, b[5])]
        lo = [(x, bed3_vault(x), z) for x, z in ring]
        hi = [(x, bed3_vault(x) + VAULT_T, z) for x, z in ring]
        _remesh(ob, lo + hi, _prism_faces(4))
        out['west' if west else 'east'] = (round(xa, 3), round(xb, 3))
    out['ridge was / is'] = (round(was, 3) if was else None, round(bed3_vault(WING_X), 3))
    # the four recessed cans on the slopes: turned by the change of pitch and seated on the new ceiling (lens and
    # trim ring just proud of it, the lamp behind them). One of them (x 3.3, z 51.4) stood 0.06 ft inside the old
    # ceiling slab since the plan conversion shifted it; it is seated like the others.
    from mathutils import Matrix
    old_s = 3.5 / 7.434                                      # the concept vault: 8.0 at the walls, 11.5 at x 7.659
    seat = {'lens': 0.0185, 'trim': 0.014, 'lamp': 0.085}    # centre of each piece below the ceiling's surface
    moved = 0
    for ob in bpy.data.objects:
        if not ob.name.startswith('slope can'):
            continue
        t = ob.matrix_world.translation
        x, y, z = t.x / FT, t.z / FT, -t.y / FT
        if ob.type == 'MESH' and len(ob.data.vertices):
            b = _bbox(ob)
            x, y, z = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
        if not (R.XW < x < R.X_SBATH_E and R.Z_B3_N < z < R.Z_B3_S):
            continue
        west = x < WING_X
        kind = 'lens' if ' lens ' in ob.name else ('trim' if ' trim ' in ob.name else 'lamp')
        phi = (math.atan(old_s) - math.atan(P)) * (1.0 if west else -1.0)
        pv = ft2bl(x, y, z)
        m = Matrix.Translation((0, 0, (bed3_vault(x) - seat[kind] - y) * FT)) @ Matrix.Translation(pv) \
            @ Matrix.Rotation(phi, 4, 'Y') @ Matrix.Translation(-pv)
        ob.matrix_world = m @ ob.matrix_world
        moved += 1
    out['slope cans moved'] = moved
    return out


def entry_ceiling(ctx):
    """The entry vault: level, 5 in 12 about the foyer's centre line (it fell 0.38 ft toward the front with the old
    ridge), with a closed void above; its rear gable, which the warp had skewed, rebuilt square behind it. The
    stepped knee-wall pieces go: the cheek walls stand in their place."""
    vault = _find(r'^\d+ Coordinated entry vaulted ceiling')
    if not vault:
        return {'vault': 'not built'}
    vb = [_bbox(o) for o in vault]
    x0, x1 = min(b[0] for b in vb), max(b[1] for b in vb)
    z0, z1 = min(b[4] for b in vb), max(b[5] for b in vb)
    for ob, b in zip(vault, vb):
        west = (b[0] + b[1]) / 2 < ENTRY_C
        xa, xb = (x0, ENTRY_C) if west else (ENTRY_C, x1)
        ring = [(xa, z0), (xb, z0), (xb, z1), (xa, z1)]
        lo = [(x, entry_vault(x), z) for x, z in ring]
        hi = [(x, entry_vault(x) + VAULT_T, z) for x, z in ring]
        _remesh(ob, lo + hi, _prism_faces(4))
    # v7 integrate: the rear gable stands ON the hall's flat ceiling slab (its foot lay in the plane of that
    # ceiling's underside for 0.10 ft north of the vault's infill: two faces in one plane)
    base = max([_bbox(o)[3] for o in _find(r'^\d+ Bedroom hall flat ceiling')] + [8.0])
    for ob in _find(r'^\d+ Coordinated entry rear gable'):
        prof = [(x0, base), (x1, base), (x1, entry_vault(x1) + 0.1), (ENTRY_C, ENTRY_VAULT_Y + 0.1), (x0, entry_vault(x0) + 0.1)]
        lo = [(x, y, z0 - 0.16) for x, y in prof]
        hi = [(x, y, z0 - 0.02) for x, y in prof]
        _remesh(ob, lo + hi, _prism_faces(5), lambda n, c: 0)
    gone = _remove(_find(r'^entry vault knee wall'))
    return {'z': (round(z0, 3), round(z1, 3)), 'ridge': round(ENTRY_VAULT_Y, 3),
            'at the walls': round(entry_vault(R.X_FOYER_W), 3), 'knee walls removed': gone}


def porch(ctx):
    """The covered porch under the entry roof: the flat canopy goes; the two stucco piers run up to the roof; a
    charcoal tie beam with a king post carries the gable between them; the roof's underside is lined with the
    entry's wood from the door wall to the front edge (a closed soffit that follows the roof)."""
    out = {'canopy removed': _remove(_find(r'^ext porch canopy'))}
    pw, pe = _porch_posts()
    raised = 0
    for ob in _find(r'^ext porch piers$'):
        mw = ob.matrix_world
        inv = mw.inverted()
        ys = [(mw @ v.co).z / FT for v in ob.data.vertices]
        ytop = max(ys)
        for v in ob.data.vertices:
            w = mw @ v.co
            if w.z / FT > ytop - 0.05:
                x = w.x / FT
                v.co = inv @ ft2bl(x, entry_under(x), -w.y / FT)
                raised += 1
        ob.data.update()
    out['pier vertices raised'] = raised
    # wood soffit under the roof over the porch
    # v7 repair: it runs out to the roof's edges (it stopped 0.05 ft short of the eaves and of the front rake, and a
    # 5/8 in rim of the slab's white underside showed between the wood and the fascia). Its own edge faces carry
    # the fascia's charcoal: the fascia reads 3/8 in deeper where the porch is lined.
    za, zb = R.Z_PORCH_N - 0.02, ENTRY_FRONT
    for tag, xa, xb in (('west', ENTRY_X[0], ENTRY_C), ('east', ENTRY_C, ENTRY_X[1])):
        ring = [(xa, za), (xb, za), (xb, zb), (xa, zb)]
        lo = [(x, entry_under(x) - SOFFIT_T, z) for x, z in ring]
        hi = [(x, entry_under(x), z) for x, z in ring]
        _solid(ctx, f'{PRE} porch soffit {tag}', lo + hi, _prism_faces(4), ['wood_cladding', 'fascia_charcoal'],
               lambda n, c: 0 if abs(n[1]) > 0.5 else 1)
    # v7 repair: the porch's two side walls, clad in the entry's wood from the slab to the soffit, from the front door
    # wall to the pier (which stays stucco). Until now the east wall was white wall paint (one wall piece runs from
    # the foyer to the garage front) and the west wall wood only from the floor line to the roof, over a white
    # stucco base, both with an interior baseboard; each wall's finish changed at the 8 ft line (cheek wall), at the
    # corner piece and at the pier's bevel, which showed as joint lines. One board skin per wall, 3/16 in proud of
    # the wall and of the pier's face, covers all of it: one surface, no joint. It ends on the pier's flat face
    # (past the pier's bevelled edge) and stands on the slab.
    try:
        from .zones import exterior_layout as L
        y_slab = L.PORCH_TOP
    except Exception:
        y_slab = -11.0 / 24.0
    for tag, xw, sgn, zp in (('west', R.X_FOYER_W, 1.0, pw[2]), ('east', R.X_FOYER_E, -1.0, pe[2])):
        xo = xw + sgn * CLAD_T
        ya, yb = entry_under(xw) - SOFFIT_T + 0.01, entry_under(xo) - SOFFIT_T + 0.01
        prof = [(min(xw, xo), y_slab - 0.01), (max(xw, xo), y_slab - 0.01),
                (max(xw, xo), yb if sgn > 0 else ya), (min(xw, xo), ya if sgn > 0 else yb)]
        wall_x(ctx, f'{PRE} porch cladding {tag}', prof, R.Z_PORCH_N, zp + 0.03, ['wood_cladding'], None)
    out['side cladding'] = {'thickness': CLAD_T, 'west z': (round(R.Z_PORCH_N, 3), round(pw[2] + 0.03, 3)),
                            'east z': (round(R.Z_PORCH_N, 3), round(pe[2] + 0.03, 3)), 'foot': round(y_slab, 4)}
    # tie beam between the piers and a king post up to the ridge
    bz0 = pw[2] + 0.45
    y0, y1 = BEAM_Y
    b = box(ctx, f'{PRE} porch beam', pw[1], pe[0], y0, y1, bz0, bz0 + BEAM_D, 'fascia_charcoal')
    ctx.add_bevel(b, 0.012, 2)
    k = 0.17
    prof = [(ENTRY_C - k, y1), (ENTRY_C + k, y1), (ENTRY_C + k, entry_under(ENTRY_C + k) - SOFFIT_T + 0.01),
            (ENTRY_C, entry_under(ENTRY_C) - SOFFIT_T + 0.01), (ENTRY_C - k, entry_under(ENTRY_C - k) - SOFFIT_T + 0.01)]
    wall_x(ctx, f'{PRE} porch king post', prof, bz0 + BEAM_D / 2 - k, bz0 + BEAM_D / 2 + k, ['fascia_charcoal'], None)
    out['beam'] = (round(pw[1], 3), round(pe[0], 3), y0, y1, round(bz0, 3), round(bz0 + BEAM_D, 3))
    return out


def rebuild(ctx):
    out = {'removed': _remove(_find(OLD_ROOF, COLL))}
    vault = _find(r'^\d+ Coordinated entry vaulted ceiling')
    zv0 = min(_bbox(o)[4] for o in vault) if vault else R.Z_FOYER_S - 6.41
    out['planes'] = planes(ctx)
    out['caps'] = caps(ctx)
    out['bedroom 3 ceiling'] = bed3_ceiling(ctx)
    out['entry ceiling'] = entry_ceiling(ctx)
    out['entry walls'] = entry_walls(ctx, zv0)
    out['gables'] = gables(ctx)
    out['porch'] = porch(ctx)
    out['ridges'] = {'main': (round(MAIN_Y, 3), round(ZR, 3), round(M1[0], 3), round(M2[0], 3)),
                     'garage': (round(GAR_Y, 3), round(GAR_X, 3)), 'wing': (round(WING_Y, 3), round(WING_X, 3)),
                     'entry': (round(ENTRY_Y, 3), round(ENTRY_C, 3), ENTRY_TIP_Z, round(ENTRY_FRONT, 3))}
    return out
