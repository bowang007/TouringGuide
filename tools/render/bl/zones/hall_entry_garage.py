"""Zone: hall_entry_garage -- front hall + entry vault, common hall circulation, garage.

Design (1077 W McKinley language): calm white walls, light oak floor (shell), a black console
with woven-cane fronts under a round black-framed mirror, ceramic vases with flowering branches,
large abstract art on the long hall walls, a three-ring LED pendant in the entry vault, flush
ring + 4in can lighting along the halls. The garage is a clean finished garage: white walls,
sealed concrete (shell) with saw-cut control joints, wall-hung light-grey cabinet system with a
white-oak worktop, slatwall with shelf and bins, EV wall charger, tankless water heater and
4ft LED linear ceiling fixtures. Room for two cars is kept clear.

All coordinates are SCENE feet. See hall_entry_garage_lib.Frame for the wall-local (u, v, n).
"""
import math
import random

import bpy
from mathutils import Euler, Matrix, Vector

from .. import lighting
from ..common import FT, ft2bl, move_to_collection, world_bbox_ft
from . import hall_entry_garage_art as ART
from . import hall_entry_garage_lib as L
from .hall_entry_garage_lib import (EAST_FACING_WEST, NORTH_FACING_SOUTH, SOUTH_FACING_NORTH,
                                    WEST_FACING_EAST, Frame)

Z = 'zone_hall_entry_garage'
C_ENTRY = 'heg_entry'
C_HALL = 'heg_hall'
C_GAR = 'heg_garage'
C_LIGHT = 'heg_lights'
C_DECOR = 'heg_decor'
# Colour temperature of the hall's lights. render_panos white-balances every stop for daylight (9000K,
# tint +18), so a 3000K (or even 4000K) can renders deep orange in this windowless hall; a listing
# photographer would balance for the interior light instead. 5000K reads as warm white under the
# current grade and still slightly warm if the global white balance is later moved toward 6500K.
HALL_K = 5000
PENDANT_K = 4500


# ----------------------------------------------------------------------------- anchors
def _face(ctx, name_re, side, default):
    """Wall face coordinate from an original SCENE wall's AABB (side: 'x0','x1','z0','z1')."""
    idx = ctx.find(name=name_re, role='shell')
    if not idx:
        return default
    a = ctx.aabb(idx[0])
    return {'x0': a[0], 'x1': a[1], 'z0': a[4], 'z1': a[5]}[side]


def anchors(ctx):
    A = {}
    A['hall_w'] = _face(ctx, r'^Suite 3 services / hall wall$', 'x1', 14.2517)          # west hall face
    A['hall_e'] = _face(ctx, r'^Garage interior access — south wall$', 'x0', 20.4647)   # east hall face
    A['gar_w'] = _face(ctx, r'^Garage interior access — south wall$', 'x1', 20.9147)    # garage west face
    A['gar_n'] = _face(ctx, r'^Kitchen / garage separation$', 'z1', 31.7717)
    A['gar_e'] = _face(ctx, r'^Garage — east side$', 'x0', 40.6117)
    A['front'] = _face(ctx, r'^Centered front entrance — west wall$', 'z0', 46.7217)
    A['corr_w'] = _face(ctx, r'^Original shared bath — east$', 'x1', 16.3617)
    A['junc_n'] = _face(ctx, r'^Upper closet — bottom wall KEPT$', 'z1', 15.5017)
    d = [m for m in ctx.meas['doors'] if m['id'] == 'D02']
    A['d02'] = (d[0]['start'], d[0]['end']) if d else (36.8, 39.8)
    return A


def floor_y(x, z, default=0.0):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, ft2bl(x, 3.0, z), Vector((0, 0, -1)))
    return loc.z / FT if hit else default


# ----------------------------------------------------------------------------- materials
def mats(ctx):
    M = {}
    M['lacquer'] = L.principled('lacquer_black', '#141414', rough=0.38, coat=0.15)
    M['cab'] = L.principled('cab_grey', '#d9d9d5', rough=0.32, coat=0.05)
    M['cab_case'] = L.principled('cab_case', '#cfd0cc', rough=0.4)
    M['plastic_w'] = L.principled('plastic_white', '#eeeeec', rough=0.3, coat=0.2)
    M['plastic_dk'] = L.principled('plastic_dark', '#3a3c3e', rough=0.45)
    M['plastic_blk'] = L.principled('plastic_black', '#18191a', rough=0.4)
    M['glass_blk'] = L.principled('glass_black', '#0b0c0d', rough=0.06, coat=0.8)
    M['slat'] = L.principled('slatwall', '#cdcecb', rough=0.42)
    M['slat_back'] = L.principled('slatwall_groove', '#77797a', rough=0.6)
    M['steel_grey'] = L.principled('steel_powder', '#55585b', rough=0.45, metal=0.6)
    M['conduit'] = L.principled('conduit', '#a9abab', rough=0.35, metal=0.9)
    M['copper'] = L.principled('copper', '#b87352', rough=0.3, metal=1.0)
    M['rubber_blk'] = L.principled('rubber_black', '#141414', rough=0.55)
    M['hose'] = L.principled('hose_green', '#2c3a2c', rough=0.5)
    M['joint'] = L.principled('saw_joint', '#55534f', rough=0.9)
    M['bark'] = L.principled('bark', '#3a2b20', rough=0.8)
    M['petal'] = L.principled('petal', '#f6f1ea', rough=0.55, sss=0.25)
    M['stamen'] = L.principled('stamen', '#d8c27a', rough=0.6)
    M['plume'] = L.principled('plume', '#d9cbb0', rough=0.95, sss=0.3, sheen=1.0)
    M['stem'] = L.principled('stem', '#b59a6e', rough=0.8)
    M['canvas_edge'] = L.principled('canvas_edge', '#efece5', rough=0.85)
    M['book_a'] = L.principled('book_cream', '#d9d0bf', rough=0.7)
    M['book_b'] = L.principled('book_charcoal', '#34322f', rough=0.65)
    M['book_c'] = L.principled('book_sage', '#9aa38d', rough=0.7)
    M['pages'] = L.principled('pages', '#f1ece0', rough=0.85)
    M['ceramic_blk'] = L.principled('ceramic_black', '#1d1c1b', rough=0.62)
    M['ceramic_cream'] = L.principled('ceramic_cream', '#e9e3d7', rough=0.45)
    # LED diffusers must read as lit after lighting.apply_balance (emission x0.4): 16 -> 6.4 at render
    # time, i.e. near-white glowing lines, clearly brighter than the white ceiling around them.
    M['ring_led'] = lighting.emitter('heg_ring', PENDANT_K, 16.0)
    M['flush_led'] = lighting.emitter('heg_flush', HALL_K, 16.0)
    M['garage_led'] = L.diffuser_mat('garage_lens', strength=4.0, color=lighting.kelvin_rgb(5000))
    M['undercab_led'] = lighting.emitter('heg_undercab', 5000, 8.0)
    M['status_led'] = L.emit_mat('ev_status', (0.55, 0.95, 0.75), 6.0)
    return M


# ----------------------------------------------------------------------------- generic pieces
def canvas(ctx, M, fr, name, uc, vc, w, h, art_mat, coll, depth=0.125, frame_mat='white_oak_veneer'):
    """Gallery-wrapped canvas in a thin floater frame, hung on wall frame `fr`."""
    n_back = 0.03
    hw, hh, hd = w / 2, h / 2, depth / 2
    v = [(sx * hw, sy * hh, sz * hd) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    idx = lambda i, j, k: i * 4 + j * 2 + k
    F = [((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
         ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
         ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
         ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),
         ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
         ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))]
    faces = [tuple(idx(*c) for c in f) for f in F]
    uvs = []
    for f in F:
        for (i, j, k) in f:
            uvs.append((i, j) if f is F[0] else (0.5, 0.5))
    ob = L.mesh_from(ctx, f'art {name}', v, faces, coll, [art_mat, M['canvas_edge']], [0, 1, 1, 1, 1, 1], uvs)
    fr.place(ob, uc, vc, n_back + hd)
    ctx.add_bevel(ob, 0.008, 2)
    if frame_mat:
        g, t = 0.035, 0.035                 # gap to canvas, frame wall thickness
        d1 = n_back + depth + 0.012
        fm = frame_mat
        fr.box(ctx, f'art {name} frame L', uc - hw - g - t, uc - hw - g, vc - hh - g - t, vc + hh + g + t, 0.0, d1, fm, coll, 0.006, 2)
        fr.box(ctx, f'art {name} frame R', uc + hw + g, uc + hw + g + t, vc - hh - g - t, vc + hh + g + t, 0.0, d1, fm, coll, 0.006, 2)
        fr.box(ctx, f'art {name} frame B', uc - hw - g, uc + hw + g, vc - hh - g - t, vc - hh - g, 0.0, d1, fm, coll, 0.006, 2)
        fr.box(ctx, f'art {name} frame T', uc - hw - g, uc + hw + g, vc + hh + g, vc + hh + g + t, 0.0, d1, fm, coll, 0.006, 2)
        fr.box(ctx, f'art {name} frame back', uc - hw - g, uc + hw + g, vc - hh - g, vc + hh + g, 0.0, n_back, M['lacquer'], coll)
    return ob


def disc_on_wall(ctx, fr, name, uc, vc, r_in, r_out, n0, n1, mat, coll, seg=96):
    """Flat annulus (r_in>0) or disc (r_in=0) on a wall, extruded n0..n1."""
    verts, faces = [], []
    if r_in <= 0:
        for k, n in enumerate((n0, n1)):
            for i in range(seg):
                a = 2 * math.pi * i / seg
                verts.append((r_out * math.cos(a), r_out * math.sin(a), n))
        faces.append(tuple(range(seg - 1, -1, -1)))
        faces.append(tuple(range(seg, 2 * seg)))
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((i, j, seg + j, seg + i))
    else:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            c, s = math.cos(a), math.sin(a)
            for r, n in ((r_in, n0), (r_out, n0), (r_out, n1), (r_in, n1)):
                verts.append((r * c, r * s, n))
        for i in range(seg):
            j = (i + 1) % seg
            a, b = 4 * i, 4 * j
            faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b + 3, a + 3),
                      (a + 3, b + 3, b, a)]
    ob = L.mesh_from(ctx, name, verts, faces, coll, [mat], smooth=True, sharp_deg=45)
    fr.place(ob, uc, vc, 0.0)
    return ob


def switch_plate(ctx, M, fr, name, u, v, gangs=1, coll=C_HALL):
    w = 0.245 if gangs == 1 else 0.38
    h = 0.375
    fr.box(ctx, f'switch plate {name}', u - w / 2, u + w / 2, v - h / 2, v + h / 2, 0.0, 0.022, M['plastic_w'], coll, 0.008, 2)
    for g in range(gangs):
        cu = u + (g - (gangs - 1) / 2) * 0.15
        fr.box(ctx, f'switch rocker {name} {g}', cu - 0.045, cu + 0.045, v - 0.11, v + 0.11, 0.022, 0.034, M['plastic_w'], coll, 0.006, 2)


def place_asset(ctx, asset_id, target_h, x, y, z, rot, coll, res='1k'):
    """Import a Poly Haven model, scale to target height (ft), put bottom-centre at SCENE (x,y,z)."""
    from .. import assets
    try:
        path = assets.model(asset_id, res=res)
    except Exception as e:                 # offline: caller falls back to procedural
        print(f'[hall_entry_garage] asset {asset_id} unavailable: {e}')
        return None
    roots = ctx.link_asset(path)
    if not roots:
        return None
    move_to_collection(roots, ctx.coll(coll))
    bpy.context.view_layer.update()
    x0, x1, y0, y1, z0, z1 = world_bbox_ft(roots)
    f = target_h / max(y1 - y0, 1e-6)
    for r in roots:
        r.scale = (r.scale[0] * f, r.scale[1] * f, r.scale[2] * f)
        r.location = r.location * f
        r.rotation_euler.z += rot
    bpy.context.view_layer.update()
    x0, x1, y0, y1, z0, z1 = world_bbox_ft(roots)
    off = ft2bl(x, y, z) - ft2bl((x0 + x1) / 2, y0, (z0 + z1) / 2)
    for r in roots:
        r.location = r.location + off
    bpy.context.view_layer.update()
    for r in roots:
        r.name = f'{asset_id} {r.name}'[:60]
    return roots


# ----------------------------------------------------------------------------- decor
def blossom_mesh(ctx, M):
    """One small five-petal blossom (about 1in across), shared by all instances."""
    me = bpy.data.meshes.get('heg blossom')
    if me:
        return me
    verts, faces, mi = [], [], []
    for p in range(5):
        a0 = 2 * math.pi * p / 5
        base = len(verts)
        verts.append((0.0, 0.0, 0.0))
        ring = 9
        for i in range(ring):
            t = -0.55 + 1.1 * i / (ring - 1)
            ang = a0 + t * 0.62
            rr = 0.042 * (0.55 + 0.45 * math.cos(t * 1.4))
            verts.append((rr * math.cos(ang) * FT, rr * math.sin(ang) * FT, (0.012 * (rr / 0.042) ** 2) * FT))
        for i in range(ring - 1):
            faces.append((base, base + 1 + i, base + 2 + i))
            mi.append(0)
    c = len(verts)
    for i in range(6):
        a = 2 * math.pi * i / 6
        verts.append((0.008 * FT * math.cos(a), 0.008 * FT * math.sin(a), 0.006 * FT))
    faces.append(tuple(range(c, c + 6)))
    mi.append(1)
    me = bpy.data.meshes.new('heg blossom')
    me.from_pydata(verts, [], faces)
    me.materials.append(M['petal'])
    me.materials.append(M['stamen'])
    for poly, k in zip(me.polygons, mi):
        poly.material_index = k
    me.validate()
    me.shade_smooth()
    return me


def flowering_branches(ctx, M, base, coll, seed=3, n_main=4, wall_x=None, wall_dir=1, height=1.9, spread=0.95):
    """Flowering branches (quince / cherry style) rising from a vase mouth at SCENE `base`."""
    rng = random.Random(seed)
    bmesh_ = blossom_mesh(ctx, M)
    nb = 0
    tips = []

    def grow(p0, d, length, r0, depth, tag):
        nonlocal nb
        pts, rad = [p0], [r0]
        p = Vector(p0)
        dv = Vector(d).normalized()
        steps = max(6, int(length / 0.07))
        for s in range(steps):
            dv = (dv + Vector((rng.uniform(-0.18, 0.18), rng.uniform(-0.05, 0.12), rng.uniform(-0.18, 0.18)))).normalized()
            if wall_x is not None:                      # keep clear of the wall / mirror plane
                if (p.x - wall_x) * wall_dir < 0.28:
                    dv.x += 0.15 * wall_dir
                    dv.normalize()
            p = p + dv * (length / steps)
            pts.append(tuple(p))
            rad.append(r0 * (1 - 0.82 * (s + 1) / steps))
        L.tube(ctx, f'branch {tag}', pts, rad, coll, M['bark'], bevel_res=2)
        tips.append(pts[-1])
        # blossoms along the outer 55% (clusters at nodes)
        for k in range(int(steps * 0.45), steps + 1):
            if rng.random() < (0.68 if depth == 0 else 0.8):
                q = Vector(pts[k])
                for b in range(rng.randint(1, 4)):
                    off = Vector((rng.uniform(-1, 1), rng.uniform(-0.6, 1), rng.uniform(-1, 1))).normalized() * 0.03
                    ob = bpy.data.objects.new('blossom', bmesh_)
                    ob.location = ft2bl(*(q + off))
                    ob.rotation_euler = Euler((rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), rng.uniform(0, 6.28)))
                    s_ = rng.uniform(0.75, 1.15)
                    ob.scale = (s_, s_, s_)
                    ctx.coll(coll).objects.link(ob)
                    nb += 1
        # side twigs
        if depth == 0:
            for t in range(rng.randint(2, 3)):
                k = rng.randint(int(steps * 0.35), int(steps * 0.8))
                sd = (dv + Vector((rng.uniform(-0.9, 0.9), rng.uniform(-0.1, 0.4), rng.uniform(-0.9, 0.9)))).normalized()
                grow(pts[k], sd, length * rng.uniform(0.3, 0.45), rad[k] * 0.6, 1, f'{tag}.{t}')

    for i in range(n_main):
        a = 2 * math.pi * (i + rng.uniform(-0.2, 0.2)) / n_main
        lean = spread * rng.uniform(0.6, 1.0)
        d = (math.cos(a) * lean * 0.55, 1.0, math.sin(a) * lean)
        if wall_x is not None and d[0] * wall_dir < 0:
            d = (-d[0] * 0.4, d[1], d[2])
        grow(base, d, height * rng.uniform(0.78, 1.0), 0.016, 0, f'{i}')
    return nb


def books(ctx, M, cx, y, cz, rot, coll, specs):
    """Stack of hardcover books: specs = [(w, d, t, material), ...] bottom to top (ft)."""
    yy = y
    out = []
    for i, (w, d, t, mt) in enumerate(specs):
        a = rot + (0.06 if i % 2 else -0.04)
        ob = ctx.box_c(f'book {i}', (cx, yy + t / 2, cz), (w, t, d), a, mt, coll, 0.008, 2)
        pg = ctx.box_c(f'book {i} pages', (cx + 0.01 * math.cos(a), yy + t / 2, cz - 0.01 * math.sin(a)),
                       (w - 0.03, t - 0.02, d - 0.01), a, M['pages'], coll)
        out += [ob, pg]
        yy += t
    return yy


def _hair_material(name, color, rough=0.5, radial=0.8):
    full = 'Z_hall_entry_garage_' + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    h = nt.nodes.new('ShaderNodeBsdfHairPrincipled')
    try:
        h.parametrization = 'COLOR'
    except Exception:
        pass
    for k, val in (('Color', tuple(color) + (1,)), ('Roughness', rough), ('Radial Roughness', radial),
                   ('Coat', 0.0), ('Random Color', 0.12), ('Random Roughness', 0.2)):
        if k in h.inputs:
            h.inputs[k].default_value = val
    nt.links.new(h.outputs[0], out.inputs['Surface'])
    m.diffuse_color = tuple(color) + (1,)
    return m


def bunny_tails(ctx, M, mouth, coll, seed=9, n=10, wall_z=None):
    """Dried bunny-tail grass (Lagurus ovatus) loosely gathered in a bottle vase.

    Each stem is a thin straw that leans out of the neck and droops progressively toward the tip
    (curvature grows along the stem, 6-18 deg of total bend), with +/-25% length variation and an
    uneven, one-sided spray rather than a symmetric fan. Each head is an egg-shaped plume (widest
    about a third of the way up, tapering to a soft point; 1.4-2.6in long) of fine hair-curve
    fibres whose lengths follow a lumpy per-plume envelope, plus a scatter of longer awns that
    break the silhouette, so the heads read as fluff rather than as cotton swabs.
    wall_z: SCENE z of the wall behind the vase (stems are kept in front of it)."""
    import numpy as np
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    me = bpy.data.meshes.get('heg plume core')
    if me is None:
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
        for v in bm.verts:                             # unit-length spindle, scaled per plume
            v.co = Vector((v.co.x * 0.5 * FT, v.co.y * 0.5 * FT, v.co.z * 0.5 * FT))
        me = bpy.data.meshes.new('heg plume core')
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        me.materials.append(M['plume'])
    mx, my, mz = mouth
    up = Vector((0.0, 1.0, 0.0))
    fibres, radii = [], []
    # uneven spray: azimuths cluster loosely around a 'front' direction (away from the wall) with a
    # few strays, leans differ a lot (a couple of near-vertical stems, a couple of low arcs)
    az0 = math.pi / 2                                   # +z = away from the wall
    for k in range(n):
        a = az0 + rng.gauss(0.0, 1.05)
        out = Vector((math.cos(a), 0.0, math.sin(a)))
        th0 = math.radians(rng.choice((4, 8, 12, 16, 20, 25, 30)) + rng.uniform(-3, 3))
        bend = math.radians(rng.uniform(10.0, 24.0))
        L_ = 1.18 * rng.uniform(0.75, 1.25)             # from 0.35 ft inside the neck to the plume base
        wob = Vector((-math.sin(a), 0.0, math.cos(a))) * rng.uniform(-0.03, 0.03)
        p = Vector((mx + rng.uniform(-0.012, 0.012), my - 0.35, mz + rng.uniform(-0.012, 0.012)))
        pts = [tuple(p)]
        steps = 16
        for i in range(1, steps + 1):
            s_ = i / steps
            th = th0 + bend * s_ ** 1.7                 # droop grows toward the tip
            d = (up * math.cos(th) + out * math.sin(th) + wob * s_).normalized()
            p = p + d * (L_ / steps)
            if wall_z is not None and p.z < wall_z + 0.12:
                p.z = wall_z + 0.12
            pts.append(tuple(p))
        rad0 = rng.uniform(0.0038, 0.005)
        L.tube(ctx, f'grass stem {k}', pts, [rad0 * (1 - 0.45 * i / steps) for i in range(steps + 1)], coll,
               M['stem'], 2)
        # plume axis: stem tangent at the tip, nodding a little further
        ax_v = (Vector(pts[-1]) - Vector(pts[-3])).normalized()
        nod = math.radians(rng.uniform(2.0, 9.0))
        ax_v = (ax_v * math.cos(nod) + (out - up * 0.3).normalized() * math.sin(nod)).normalized()
        size = rng.uniform(0.72, 1.3)
        plen = 0.15 * size                              # plume length (ft): ~1.4-2.6in
        pw = plen * rng.uniform(0.24, 0.3)              # fluff radius at the widest point
        base = Vector(pts[-1]) - ax_v * 0.012
        # small core well inside the fluff (gives the head some density, never seen as a solid)
        ob = bpy.data.objects.new('grass plume core', me)
        ob.location = ft2bl(*(base + ax_v * plen * 0.42))
        dirb = Vector((ax_v.x, -ax_v.z, ax_v.y))
        ob.rotation_euler = dirb.to_track_quat('Z', 'Y').to_euler()
        ob.scale = (pw * 0.8, pw * 0.8, plen * 0.72)     # mesh is a 1 ft sphere
        ctx.coll(coll).objects.link(ob)
        ax = np.array([ax_v.x, ax_v.y, ax_v.z])
        side = np.cross(ax, [0.31, 0.12, 0.94])
        side /= np.linalg.norm(side)
        up2 = np.cross(ax, side)
        c0 = np.array(tuple(base))
        # lumpy envelope: per-plume low-frequency harmonics over azimuth and along the axis
        ph = nrng.uniform(0, 2 * math.pi, 4)
        amp = nrng.uniform(0.06, 0.16, 3)
        nf = int(1500 * size ** 1.5)
        for _ in range(nf):
            t = nrng.beta(1.6, 1.9)                     # more fibres low/mid in the head
            psi = nrng.uniform(0, 2 * math.pi)
            env = (t ** 0.55) * (1 - t) ** 0.85 / 0.38  # egg: widest ~0.4, soft tip
            env *= 1 + amp[0] * math.sin(2 * psi + ph[0]) + amp[1] * math.sin(3 * psi + ph[1] + 4 * t) \
                + amp[2] * math.sin(7 * t + ph[2])
            R = math.cos(psi) * side + math.sin(psi) * up2
            org = c0 + ax * (t * plen * 0.9) + R * 0.004
            ln = pw * env * nrng.uniform(0.6, 1.15) + 0.004
            dirf = R * 0.85 + ax * (0.25 + 0.6 * t)
            dirf /= np.linalg.norm(dirf)
            f = [org]
            dd = dirf.copy()
            for _s in range(3):
                dd = dd + nrng.normal(0, 0.22, 3)
                dd /= np.linalg.norm(dd)
                f.append(f[-1] + dd * ln / 3)
            fibres.append(f)
            radii.append((0.00019, 0.00016, 0.00012, 0.00007))
        # awns: sparse longer, finer bristles poking out of the upper two thirds
        for _ in range(int(70 * size)):
            t = nrng.uniform(0.3, 1.0)
            psi = nrng.uniform(0, 2 * math.pi)
            R = math.cos(psi) * side + math.sin(psi) * up2
            org = c0 + ax * (t * plen * 0.85)
            ln = pw * nrng.uniform(1.1, 1.9)
            dirf = R * 0.6 + ax * (0.6 + 0.5 * t)
            dirf /= np.linalg.norm(dirf)
            f = [org]
            dd = dirf.copy()
            for _s in range(3):
                dd = dd + nrng.normal(0, 0.12, 3)
                dd /= np.linalg.norm(dd)
                f.append(f[-1] + dd * ln / 3)
            fibres.append(f)
            radii.append((0.00011, 0.00009, 0.00007, 0.00004))
    fib = np.array(fibres)                             # (N, 4, 3) SCENE ft
    N = fib.shape[0]
    hc = bpy.data.hair_curves.new('heg bunny tail fluff')
    hc.add_curves([4] * N)
    bl = np.stack([fib[..., 0] * FT, -fib[..., 2] * FT, fib[..., 1] * FT], -1).astype(np.float32)
    hc.position_data.foreach_set('vector', bl.ravel())
    rad = hc.attributes.new('radius', 'FLOAT', 'POINT')
    rad.data.foreach_set('value', np.array(radii, np.float32).ravel())
    hc.materials.append(_hair_material('plume_hair', (0.76, 0.69, 0.56), rough=0.5, radial=0.9))
    ob = bpy.data.objects.new('heg bunny tail fluff', hc)
    ctx.coll(coll).objects.link(ob)
    return n


def vault_infill(ctx, A, cnt):
    """The original data leaves an open strip between the 8 ft hall side walls and the entry
    vault eaves (~9.05 ft) that looks straight into the attic. Close it with knee walls in the
    wall plane -- only if the strip is still open (so a later shell fix cannot double it)."""
    made = 0
    for side, xf, xo, dx in (('W', A['hall_w'], 13.89, -1.0), ('E', A['hall_e'], 20.91, 1.0)):
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        hit, loc, *_ = bpy.context.scene.ray_cast(dg, ft2bl(17.38, 8.6, 41.5), Vector((dx, 0, 0)))
        if hit and abs(loc.x / FT - xf) < 0.2:
            continue
        tops = [L.ceiling_y(xf - dx * 0.05, z, y0=8.2)[0] for z in (40.9, 42.0, 43.5, 45.0, 46.6)]
        top = min(max(tops) + 0.2, 9.8)
        x0, x1 = sorted((xf, xo))
        ctx.box(f'entry vault knee wall {side}', x0, x1, 8.0, top, 40.80, 46.90, 'paint_wall', C_ENTRY)
        made += 1
    cnt['vault_infill'] = made


# ----------------------------------------------------------------------------- entry
def build_entry(ctx, M, A, cnt):
    W = WEST_FACING_EAST(A['hall_w'])          # u = -z
    E = EAST_FACING_WEST(A['hall_e'])          # u = +z
    fy = floor_y(17.0, 40.0, 0.016)
    lac, legm = M['lacquer'], 'black_metal'

    # --- console: black lacquer case, three woven-cane doors, black metal legs -------------
    z0c, z1c = 38.15, 42.65
    u0, u1 = -z1c, -z0c
    n0, n1 = 0.06, 1.31
    hleg, top = 0.36, 2.50
    for uu in (u0 + 0.16, u1 - 0.16):
        for nn in (n0 + 0.13, n1 - 0.13):
            W.box(ctx, 'console leg', uu - 0.045, uu + 0.045, fy, fy + hleg + 0.01, nn - 0.045, nn + 0.045, legm, C_ENTRY, 0.008, 2)
    W.box(ctx, 'console bottom', u0, u1, fy + hleg, fy + hleg + 0.06, n0, n1, lac, C_ENTRY, 0.006, 2)
    W.box(ctx, 'console top', u0, u1, top - 0.085, top, n0, n1, lac, C_ENTRY, 0.012, 3)
    W.box(ctx, 'console side N', u1 - 0.06, u1, fy + hleg + 0.06, top - 0.085, n0, n1, lac, C_ENTRY, 0.006, 2)
    W.box(ctx, 'console side S', u0, u0 + 0.06, fy + hleg + 0.06, top - 0.085, n0, n1, lac, C_ENTRY, 0.006, 2)
    W.box(ctx, 'console back', u0 + 0.06, u1 - 0.06, fy + hleg + 0.06, top - 0.085, n0, n0 + 0.04, lac, C_ENTRY)
    cane = ART.cane_material()
    span0, span1, gap = u0 + 0.072, u1 - 0.072, 0.014
    dw = (span1 - span0 - 2 * gap) / 3
    dv0, dv1 = fy + hleg + 0.075, top - 0.098
    fn0, fn1 = n1 - 0.07, n1 - 0.008
    st = 0.105
    for k in range(3):
        a = span0 + k * (dw + gap)
        b = a + dw
        W.box(ctx, f'console door {k} stile L', a, a + st, dv0, dv1, fn0, fn1, lac, C_ENTRY, 0.007, 2)
        W.box(ctx, f'console door {k} stile R', b - st, b, dv0, dv1, fn0, fn1, lac, C_ENTRY, 0.007, 2)
        W.box(ctx, f'console door {k} rail B', a + st, b - st, dv0, dv0 + st, fn0, fn1, lac, C_ENTRY, 0.007, 2)
        W.box(ctx, f'console door {k} rail T', a + st, b - st, dv1 - st, dv1, fn0, fn1, lac, C_ENTRY, 0.007, 2)
        W.box(ctx, f'console door {k} cane', a + st - 0.01, b - st + 0.01, dv0 + st - 0.01, dv1 - st + 0.01,
              fn1 - 0.04, fn1 - 0.03, cane, C_ENTRY)
        W.box(ctx, f'console door {k} back', a + st - 0.01, b - st + 0.01, dv0 + st - 0.01, dv1 - st + 0.01,
              fn0, fn0 + 0.012, lac, C_ENTRY)
    cnt['console'] = 1

    # --- round mirror with thin black metal rim ---------------------------------------------
    mu, mv, mr = -40.4, 4.78, 1.30
    disc_on_wall(ctx, W, 'mirror round glass', mu, mv, 0, mr - 0.02, 0.03, 0.055, ctx.mat('mirror'), C_ENTRY)
    disc_on_wall(ctx, W, 'mirror round rim', mu, mv, mr - 0.035, mr + 0.012, 0.012, 0.075, ctx.mat('black_metal'), C_ENTRY)
    disc_on_wall(ctx, W, 'mirror round back', mu, mv, 0, mr - 0.03, 0.0, 0.03, M['lacquer'], C_ENTRY)

    # --- console styling: tall vase + flowering branches, round vase, books ----------------
    xw = A['hall_w']
    vz, vn = 39.12, 0.66
    vx = xw + vn
    tall = place_asset(ctx, 'ceramic_vase_01', 1.22, vx, top, vz, 0.6, C_DECOR)
    if tall is None:
        tall_ob = L.lathe(ctx, 'vase tall', [(0.17, 0), (0.25, 0.25), (0.27, 0.55), (0.2, 0.9), (0.09, 1.1),
                                             (0.1, 1.22)], C_DECOR, [M['ceramic_cream']])
        tall_ob.location = ft2bl(vx, top, vz)
        mouth_y = top + 1.22
    else:
        mouth_y = world_bbox_ft(tall)[3]
    nb = flowering_branches(ctx, M, (vx, mouth_y - 0.35, vz), C_DECOR, seed=5, n_main=4,
                            wall_x=xw + 0.1, wall_dir=1, height=2.05, spread=0.9)
    cnt['blossoms'] = nb
    rz = 41.12
    rnd = place_asset(ctx, 'ceramic_vase_02', 0.62, xw + 0.62, top, rz, 1.9, C_DECOR)
    if rnd is None:
        o = L.lathe(ctx, 'vase round', [(0.12, 0), (0.25, 0.15), (0.28, 0.32), (0.2, 0.52), (0.13, 0.62)],
                    C_DECOR, [M['ceramic_cream']])
        o.location = ft2bl(xw + 0.62, top, rz)
    ytop = books(ctx, M, xw + 0.66, top, 42.02, math.pi / 2 + 0.05, C_DECOR,
                 [(0.95, 0.74, 0.09, M['book_b']), (0.86, 0.66, 0.075, M['book_a'])])
    bowl = L.lathe(ctx, 'bowl black', [(0.07, 0), (0.16, 0.02), (0.22, 0.08), (0.24, 0.13), (0.225, 0.135),
                                       (0.2, 0.09), (0.12, 0.04), (0.0, 0.035)], C_DECOR, [M['ceramic_blk']], cap_bottom=True)
    bowl.location = ft2bl(xw + 0.66, ytop, 42.02)

    # --- art: gestural black line on the east wall (visible past the open front door) ------
    canvas(ctx, M, E, 'entry scribble', 41.45, 4.9, 2.4, 3.3, ART.art_material('scribble', 'scribble'), C_ENTRY)

    # --- switch plates ----------------------------------------------------------------------
    S = SOUTH_FACING_NORTH(A['front'])        # u = -x
    switch_plate(ctx, M, S, 'front door', -15.38, 4.0, 2, C_ENTRY)
    switch_plate(ctx, M, E, 'garage door hall', A['d02'][0] - 0.42, 4.0, 1, C_ENTRY)

    # --- statement pendant in the entry vault: three cascading LED rings ------------------
    entry_pendant(ctx, M, 17.38, 43.55)


def entry_pendant(ctx, M, x, z):
    ridge = min(L.ceiling_y(x + 0.02, z)[0], L.ceiling_y(x - 0.02, z)[0])
    can_top = ridge + 0.06
    canopy = ctx.cylinder('pendant canopy', (x, ridge - 0.12, z), 0.21, 0.36, 'black_metal', C_LIGHT, verts=48)
    hub_y = ridge - 0.30
    rings = [(1.22, 7.95, 0.0, 22.0), (0.90, 8.42, 0.7, 14.0), (0.58, 8.88, 1.4, 8.0)]
    for i, (r, y, a0, watts) in enumerate(rings):
        ob = L.ring_mesh(ctx, f'pendant ring {i}', r, 0.075, 0.12, C_LIGHT, [ctx.mat('black_metal'), M['ring_led']])
        ob.location = ft2bl(x, y, z)
        for k in range(3):
            a = a0 + 2 * math.pi * k / 3
            px, pz = x + (r - 0.01) * math.cos(a), z + (r - 0.01) * math.sin(a)
            L.cyl_between(ctx, f'pendant cable {i}.{k}', (px, y + 0.06, pz), (x, hub_y, z), 0.0065, C_LIGHT, 'stainless', 8)
        ld = bpy.data.lights.new(f'pendant ring light {i}', 'AREA')
        ld.shape = 'DISK'
        ld.size = 2 * r * FT
        ld.energy = watts
        ld.color = lighting.kelvin_rgb(PENDANT_K)
        lo = bpy.data.objects.new(ld.name, ld)
        lo.location = ft2bl(x, y - 0.07, z)
        lo.visible_glossy = False
        ctx.coll(C_LIGHT).objects.link(lo)
    ctx.cylinder('pendant hub', (x, hub_y + 0.03, z), 0.035, 0.08, 'black_metal', C_LIGHT, verts=16)
    ctx.cylinder('pendant stem', (x, (hub_y + ridge) / 2, z), 0.012, ridge - hub_y, 'black_metal', C_LIGHT, verts=12)


def flush_ring(ctx, M, x, z, ceil=8.0, r=0.82, watts=70.0, name='flush ring'):
    """Modern flush-mount 'orbit' fixture: white ring + centre canopy, glowing underside."""
    ob = L.ring_mesh(ctx, f'{name} ring', r, 0.13, 0.09, C_LIGHT, [ctx.mat('paint_trim'), M['flush_led']],
                     inner_mat=1, bottom_mat=1)
    ob.location = ft2bl(x, ceil - 0.135, z)
    ctx.cylinder(f'{name} canopy', (x, ceil - 0.035, z), 0.24, 0.07, 'paint_trim', C_LIGHT, verts=48)
    for k in range(2):
        a = math.pi * k + 0.4
        p0 = (x + 0.2 * math.cos(a), ceil - 0.06, z + 0.2 * math.sin(a))
        p1 = (x + (r - 0.06) * math.cos(a), ceil - 0.12, z + (r - 0.06) * math.sin(a))
        L.cyl_between(ctx, f'{name} arm {k}', p0, p1, 0.016, C_LIGHT, 'paint_trim', 10)
    ld = bpy.data.lights.new(f'{name} light', 'AREA')
    ld.shape = 'DISK'
    ld.size = 2 * r * FT
    ld.energy = watts
    ld.color = lighting.kelvin_rgb(HALL_K)
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(x, ceil - 0.2, z)
    lo.visible_glossy = False
    ctx.coll(C_LIGHT).objects.link(lo)


def slot_diffuser(ctx, M, x, z, length, ceil=8.0, slots=2):
    """Linear slot HVAC diffuser across the hall: slim white frame with black slots."""
    w = 0.08 + slots * 0.07
    ctx.box('slot diffuser frame', x - length / 2, x + length / 2, ceil - 0.02, ceil, z - w / 2, z + w / 2, 'paint_trim', C_LIGHT, 0.006, 2)
    for k in range(slots):
        zc = z - w / 2 + 0.04 + 0.035 + k * 0.07
        ctx.box(f'slot diffuser slot {k}', x - length / 2 + 0.04, x + length / 2 - 0.04, ceil - 0.0215, ceil - 0.0195,
                zc - 0.022, zc + 0.022, M['lacquer'], C_LIGHT)


def smoke_detector(ctx, x, z, ceil=8.0):
    ctx.cylinder('smoke detector', (x, ceil - 0.065, z), 0.23, 0.13, 'paint_trim', C_LIGHT, verts=40)
    ctx.cylinder('smoke detector rim', (x, ceil - 0.135, z), 0.15, 0.012, 'paint_trim', C_LIGHT, verts=32)


# ----------------------------------------------------------------------------- halls
def build_halls(ctx, M, A, cnt):
    E = EAST_FACING_WEST(A['hall_e'])
    CW = WEST_FACING_EAST(A['corr_w'])         # u = -z
    NJ = NORTH_FACING_SOUTH(A['junc_n'])       # u = +x

    # art
    canvas(ctx, M, E, 'hall arches', 33.9, 4.9, 2.2, 2.9, ART.art_material('arches', 'arches'), C_HALL,
           frame_mat=M['lacquer'])
    canvas(ctx, M, CW, 'corridor plaster', -25.3, 4.85, 3.0, 4.0, ART.plaster_relief_material(), C_HALL,
           depth=0.14)
    canvas(ctx, M, NJ, 'junction horizon', 19.45, 4.95, 4.2, 2.8, ART.art_material('horizon', 'horizon'), C_HALL)

    # floating walnut ledge under the horizon piece, with a black bottle vase and a bowl on books
    lu0, lu1, lv0, lv1 = 17.25, 21.65, 2.55, 2.83
    NJ.box(ctx, 'ledge walnut', lu0, lu1, lv0, lv1, 0.004, 0.92, 'walnut_slab', C_HALL, 0.012, 3)
    zl = A['junc_n']
    bottle = L.lathe(ctx, 'vase bottle black', [(0.1, 0), (0.17, 0.05), (0.2, 0.3), (0.19, 0.62), (0.12, 0.8),
                                                (0.05, 0.92), (0.045, 1.12), (0.055, 1.16), (0.0, 1.16)],
                     C_DECOR, [M['ceramic_blk']])
    bottle.location = ft2bl(18.15, lv1, zl + 0.48)
    stems = bunny_tails(ctx, M, (18.15, lv1 + 1.1, zl + 0.48), C_DECOR, seed=9, n=10, wall_z=zl + 0.13)
    ytop = books(ctx, M, 20.85, lv1, zl + 0.46, 0.08, C_DECOR,
                 [(1.0, 0.78, 0.1, M['book_c']), (0.9, 0.7, 0.08, M['book_a'])])
    bowl = L.lathe(ctx, 'bowl cream', [(0.06, 0), (0.15, 0.015), (0.2, 0.06), (0.215, 0.1), (0.2, 0.105),
                                       (0.17, 0.065), (0.1, 0.03), (0.0, 0.028)], C_DECOR, [M['ceramic_cream']])
    bowl.location = ft2bl(20.85, ytop, zl + 0.46)

    # thermostat (matte black glass square) and switch plates
    CW.box(ctx, 'thermostat', -22.1 - 0.17, -22.1 + 0.17, 4.9 - 0.17, 4.9 + 0.17, 0.0, 0.07, M['glass_blk'], C_HALL, 0.02, 3)
    switch_plate(ctx, M, NJ, 'junction', 15.52, 4.0, 2, C_HALL)

    # lighting: cans along the front hall, along the corridor to the foyer, flush ring at the junction
    xh = (A['hall_w'] + A['hall_e']) / 2
    for zc in (31.6, 35.2, 38.8):
        lighting.can(ctx, xh, zc, coll=C_LIGHT, kelvin=HALL_K)
    for zc in (21.9, 25.3, 28.7):
        lighting.can(ctx, 19.4, zc, coll=C_LIGHT, kelvin=HALL_K)
    lighting.can(ctx, 19.4, 18.15, coll=C_LIGHT, kelvin=HALL_K)
    flush_ring(ctx, M, 15.45, 18.15, name='junction flush ring')
    smoke_detector(ctx, xh, 33.4)
    slot_diffuser(ctx, M, xh, 37.0, 3.4)
    # junction detector: in the corridor toward the foyer, ~6 ft clear of the flush ring and between cans
    smoke_detector(ctx, 18.0, 23.6)
    cnt['cans'] = cnt.get('cans', 0) + 7


# ----------------------------------------------------------------------------- garage
def cabinet(ctx, M, fr, name, u0, u1, v0, v1, n0, n1, doors=2, drawer=False, pull='v', coll=C_GAR):
    """Wall-hung garage cabinet: case + slab doors with 1/8in reveals + black bar pulls."""
    cm, dm = M['cab_case'], M['cab']
    t = 0.06
    fr.box(ctx, f'{name} case', u0, u1, v0, v1, n0, n1 - t, cm, coll, 0.01, 2)
    g = 0.012
    fv0 = v0 + g
    rows = []
    if drawer:
        dh = 0.55
        rows.append(('drawer', v1 - dh + g / 2, v1 - g))
        rows.append(('door', fv0, v1 - dh - g / 2))
    else:
        rows.append(('door', fv0, v1 - g))
    for kind, a, b in rows:
        k = 1 if kind == 'drawer' else doors
        w = (u1 - u0 - (k + 1) * g) / k
        for i in range(k):
            du0 = u0 + g + i * (w + g)
            du1 = du0 + w
            fr.box(ctx, f'{name} {kind} {i}', du0, du1, a, b, n1 - t, n1, dm, coll, 0.012, 2)
            pm = ctx.mat('black_metal')
            if kind == 'drawer':
                cu, cv = (du0 + du1) / 2, (a + b) / 2
                fr.box(ctx, f'{name} pull d{i}', cu - 0.3, cu + 0.3, cv - 0.02, cv + 0.02, n1, n1 + 0.1, pm, coll, 0.01, 2)
            else:
                edge = du1 - 0.12 if (i == 0 and k == 2) else du0 + 0.12
                if k == 1:
                    edge = du0 + 0.12
                if pull == 'v_low':
                    cv0, cv1 = a + 0.15, a + 0.75
                elif pull == 'v_high':
                    cv0, cv1 = b - 0.75, b - 0.15
                else:
                    mid = min(b - 0.4, 4.2)
                    cv0, cv1 = mid - 0.45, mid + 0.45
                fr.box(ctx, f'{name} pull {i}', edge - 0.02, edge + 0.02, cv0, cv1, n1, n1 + 0.1, pm, coll, 0.01, 2)


def build_garage(ctx, M, A, cnt):
    GN = NORTH_FACING_SOUTH(A['gar_n'])      # u = x, n = z - 31.77
    GE = EAST_FACING_WEST(A['gar_e'])        # u = z
    GW = WEST_FACING_EAST(A['gar_w'])        # u = -z
    fy = floor_y(30.0, 41.0, 0.025)

    # --- cabinet wall (north): full-width wall-hung system, uppers over the worktop -------------
    n0 = 0.006
    xs = [21.1, 23.5, 25.9, 29.4, 32.9, 36.4, 38.8, A['gar_e'] - 0.11]
    kinds = ['T', 'T', 'B', 'B', 'B', 'T', 'T']
    for i, kd in enumerate(kinds):
        a, b = xs[i], xs[i + 1]
        if kd == 'T':
            cabinet(ctx, M, GN, f'gar tall {i}', a, b, 0.5, 7.5, n0, 2.0, doors=2 if b - a > 2.0 else 1)
        else:
            cabinet(ctx, M, GN, f'gar base {i}', a, b, 0.5, 2.98, n0, 2.0, doors=2, drawer=True, pull='v_high')
            cabinet(ctx, M, GN, f'gar wall {i}', a, b, 5.0, 7.5, n0, 1.17, doors=2, pull='v_low')
    wt0, wt1 = xs[2], xs[5]
    GN.box(ctx, 'gar worktop oak', wt0, wt1, 2.98, 3.11, n0, 2.08, 'white_oak_veneer', C_GAR, 0.012, 3)
    GN.box(ctx, 'gar undercab led', wt0 + 0.1, wt1 - 0.1, 4.975, 5.0, 0.95, 1.05, M['undercab_led'], C_GAR)
    # a single tool case on the worktop
    GN.box(ctx, 'gar toolcase', 26.6, 27.9, 3.11, 3.48, 0.35, 1.25, M['plastic_dk'], C_GAR, 0.04, 3)
    GN.box(ctx, 'gar toolcase latch', 27.1, 27.4, 3.3, 3.4, 1.25, 1.28, M['plastic_blk'], C_GAR, 0.01, 2)
    cnt['garage_cabinets'] = len(kinds) + 3

    # --- EV charger on the east wall -----------------------------------------------------------
    eu, ev0, ev1 = 36.0, 3.7, 4.95
    GE.box(ctx, 'ev charger body', eu - 0.27, eu + 0.27, ev0, ev1, 0.0, 0.2, M['plastic_w'], C_GAR, 0.06, 4)
    GE.box(ctx, 'ev charger face', eu - 0.22, eu + 0.22, ev0 + 0.08, ev1 - 0.08, 0.2, 0.215, M['glass_blk'], C_GAR, 0.03, 3)
    GE.box(ctx, 'ev charger status', eu - 0.12, eu + 0.12, ev1 - 0.25, ev1 - 0.23, 0.215, 0.22, M['status_led'], C_GAR)
    GE.box(ctx, 'ev holster', eu + 0.62, eu + 0.86, 3.95, 4.2, 0.0, 0.16, M['plastic_w'], C_GAR, 0.03, 3)
    GE.box(ctx, 'ev connector', eu + 0.66, eu + 0.82, 3.5, 4.02, 0.06, 0.2, M['rubber_blk'], C_GAR, 0.04, 3)
    pts_l = [(eu, ev0 + 0.02, 0.1), (eu, 3.0, 0.13), (eu + 0.08, 2.35, 0.17), (eu + 0.3, 2.08, 0.19),
             (eu + 0.58, 2.2, 0.17), (eu + 0.72, 2.8, 0.14), (eu + 0.74, 3.3, 0.13), (eu + 0.74, 3.5, 0.13)]
    cab = L.catmull([GE.pt(*p) for p in pts_l], 6)
    L.tube(ctx, 'ev cable', cab, [0.04] * len(cab), C_GAR, M['rubber_blk'], 3)
    L.cyl_between(ctx, 'ev conduit', GE.pt(eu, ev1 - 0.05, 0.05), GE.pt(eu, 8.0, 0.05), 0.04, C_GAR, M['conduit'], 12)

    # --- slatwall with shelf, bins and a hose on the east wall ---------------------------------
    s0, s1, sv0 = 38.2, 46.2, 3.5
    GE.box(ctx, 'slatwall backer', s0, s1, sv0, sv0 + 4.0, 0.0, 0.025, M['slat_back'], C_GAR)
    for k in range(16):
        a = sv0 + k * 0.25
        GE.box(ctx, f'slat {k}', s0, s1, a + 0.012, a + 0.238, 0.025, 0.065, M['slat'], C_GAR, 0.008, 2)
    sh0, sh1, shv = 39.0, 42.2, 6.05
    GE.box(ctx, 'slat shelf', sh0, sh1, shv - 0.05, shv, 0.065, 1.1, M['steel_grey'], C_GAR, 0.01, 2)
    GE.box(ctx, 'slat shelf lip', sh0, sh1, shv - 0.05, shv + 0.08, 1.07, 1.1, M['steel_grey'], C_GAR, 0.006, 2)
    for uu in (sh0 + 0.3, sh1 - 0.3):
        GE.box(ctx, 'slat shelf bracket', uu - 0.02, uu + 0.02, shv - 0.55, shv - 0.05, 0.065, 0.95, M['steel_grey'], C_GAR, 0.006, 2)
    bw, bg = 0.95, 0.09
    for i in range(3):
        a = sh0 + 0.12 + i * (bw + bg)
        GE.box(ctx, f'bin {i}', a, a + bw, shv, shv + 0.66, 0.14, 1.02, M['plastic_dk'], C_GAR, 0.035, 3)
        GE.box(ctx, f'bin {i} lid', a - 0.02, a + bw + 0.02, shv + 0.66, shv + 0.74, 0.12, 1.04, M['plastic_blk'], C_GAR, 0.03, 3)
        GE.box(ctx, f'bin {i} label', a + bw / 2 - 0.18, a + bw / 2 + 0.18, shv + 0.3, shv + 0.45, 1.02, 1.025, M['canvas_edge'], C_GAR)
    # hose hanger + coiled hose
    hu, hv = 44.3, 5.55
    GE.box(ctx, 'hose hanger', hu - 0.25, hu + 0.25, hv + 0.15, hv + 0.45, 0.065, 0.12, M['steel_grey'], C_GAR, 0.02, 2)
    GE.box(ctx, 'hose hanger arm', hu - 0.22, hu + 0.22, hv + 0.15, hv + 0.2, 0.065, 0.55, M['steel_grey'], C_GAR, 0.015, 2)
    pts = []
    turns = 7
    rngh = random.Random(4)
    radii = [0.52 + rngh.uniform(-0.05, 0.07) for _ in range(turns + 1)]
    for i in range(turns * 40 + 1):
        t = i / 40.0
        k = int(t)
        f = t - k
        r = radii[k] * (1 - f) + radii[min(k + 1, turns)] * f
        a = 2 * math.pi * t
        sag = 0.06 * (1 - math.cos(a)) * (0.5 + 0.5 * math.sin(1.3 * k))
        pts.append(GE.pt(hu + r * math.sin(a) * (1 + 0.04 * math.sin(2 * a)),
                         hv + 0.17 - r * (1 - math.cos(a)) - sag, 0.12 + 0.058 * t))
    L.tube(ctx, 'hose coil', pts, [0.032] * len(pts), C_GAR, M['hose'], 2)

    # --- tankless water heater on the west wall ------------------------------------------------
    wu, wv0, wv1 = -46.6, 4.4, 6.3
    GW.box(ctx, 'water heater', wu - 0.58, wu + 0.58, wv0, wv1, 0.02, 0.72, M['plastic_w'], C_GAR, 0.04, 3)
    GW.box(ctx, 'water heater display', wu - 0.18, wu + 0.18, 5.55, 5.85, 0.72, 0.73, M['glass_blk'], C_GAR, 0.01, 2)
    L.cyl_between(ctx, 'water heater vent', GW.pt(wu, wv1 - 0.02, 0.38), GW.pt(wu, 8.0, 0.38), 0.13, C_GAR, M['conduit'], 24)
    for j, (du, m) in enumerate(((-0.3, M['copper']), (0.0, M['steel_grey']), (0.3, M['copper']))):
        L.cyl_between(ctx, f'water heater pipe {j}', GW.pt(wu + du, wv0 + 0.02, 0.36), GW.pt(wu + du, 3.6, 0.36),
                      0.035, C_GAR, m, 12)
        L.cyl_between(ctx, f'water heater pipe {j} in', GW.pt(wu + du, 3.6, 0.40), GW.pt(wu + du, 3.6, 0.0),
                      0.035, C_GAR, m, 12)
        L.cyl_between(ctx, f'water heater valve {j}', GW.pt(wu + du - 0.07, 3.95, 0.36), GW.pt(wu + du + 0.07, 3.95, 0.36),
                      0.05, C_GAR, M['plastic_blk'] if j != 1 else M['copper'], 12)

    # --- door-side switch + opener button (garage face of the west wall) -----------------------
    switch_plate(ctx, M, GW, 'garage lights', -(A['d02'][0] - 0.42), 4.0, 2, C_GAR)
    GW.box(ctx, 'opener button', -(A['d02'][0] - 0.95) - 0.11, -(A['d02'][0] - 0.95) + 0.11, 3.85, 4.2, 0.0, 0.05,
           M['plastic_w'], C_GAR, 0.015, 2)
    GW.box(ctx, 'opener button key', -(A['d02'][0] - 0.95) - 0.07, -(A['d02'][0] - 0.95) + 0.07, 3.9, 4.06, 0.05, 0.065,
           M['plastic_w'], C_GAR, 0.01, 2)

    # --- saw-cut control joints in the slab -----------------------------------------------------
    xm = (A['gar_w'] + A['gar_e']) / 2
    zm = (A['gar_n'] + 50.83) / 2
    ctx.box('gar saw joint NS', xm - 0.012, xm + 0.012, fy, fy + 0.002, A['gar_n'] + 0.06, 50.77, M['joint'], C_GAR)
    ctx.box('gar saw joint EW', A['gar_w'] + 0.06, A['gar_e'] - 0.06, fy, fy + 0.002, zm - 0.012, zm + 0.012, M['joint'], C_GAR)

    # --- 4ft LED linear ceiling fixtures --------------------------------------------------------
    k = 0
    for xc in (26.3, 35.3):
        for zc in (37.6, 44.9):
            ctx.box(f'gar led housing {k}', xc - 0.24, xc + 0.24, 7.86, 8.0, zc - 2.0, zc + 2.0, M['plastic_w'], C_LIGHT, 0.02, 2)
            ctx.box(f'gar led lens {k}', xc - 0.2, xc + 0.2, 7.82, 7.87, zc - 1.95, zc + 1.95, M['garage_led'], C_LIGHT, 0.02, 3)
            ld = bpy.data.lights.new(f'gar led light {k}', 'AREA')
            ld.shape = 'RECTANGLE'
            ld.size = 0.38 * FT
            ld.size_y = 3.9 * FT
            ld.energy = 32.0
            ld.color = lighting.kelvin_rgb(5000)
            lo = bpy.data.objects.new(ld.name, ld)
            lo.location = ft2bl(xc, 7.80, zc)
            lo.visible_glossy = False
            ctx.coll(C_LIGHT).objects.link(lo)
            k += 1
    cnt['garage_leds'] = k


# ----------------------------------------------------------------------------- entry point
def _tri_count(coll):
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for ob in coll.all_objects:
        if ob.type not in ('MESH', 'CURVE'):
            continue
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ev.to_mesh_clear()
    return tris


def build(ctx):
    root = ctx.coll(Z)
    for c in (C_ENTRY, C_HALL, C_GAR, C_LIGHT, C_DECOR):
        ctx.coll(c, Z)
    A = anchors(ctx)
    M = mats(ctx)
    cnt = {}
    build_entry(ctx, M, A, cnt)
    vault_infill(ctx, A, cnt)
    build_halls(ctx, M, A, cnt)
    build_garage(ctx, M, A, cnt)
    bpy.context.view_layer.update()
    cnt['objects'] = len(root.all_objects)
    cnt['triangles'] = _tri_count(root)
    try:
        from .. import assets
        assets.write_manifest()
    except Exception:
        pass
    ctx.stats['hall_entry_garage'] = cnt
    return cnt
