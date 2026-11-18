"""Minimal listing-style styling for the kitchen and dining table.

Poly Haven (CC0) models: lemon, ceramic_vase_01/02/04. Everything else is procedural
(white ceramic bowl and plates, oak cutting board, eucalyptus stems, herb pot)."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from ..common import FT, ft2bl, move_to_collection, world_bbox_ft
from .kitchen_dining_geo import Geo, P, principled, srgb

TOP = 3.0
USED_ASSETS = []


_CACHE = {}


def _import(g, asset_id, height_ft, at, rot=0.0, col=None, res='1k', matrix=None):
    """Place a Poly Haven model (single-mesh glTF) scaled to height_ft with its base centre at
    SCENE point `at`, rotated `rot` about +Y. Repeated placements share the mesh data.
    `matrix` (Blender 4x4, unit-scale rotation) overrides `rot` for free orientation."""
    from .. import assets
    if asset_id not in _CACHE:
        path = assets.model(asset_id, res=res)
        roots = g.ctx.link_asset(path)
        meshes = [r for r in roots if r.type == 'MESH']
        assert len(roots) == 1 and meshes, f'{asset_id}: expected one mesh root, got {roots}'
        ob = roots[0]
        bpy.context.view_layer.update()
        bb = world_bbox_ft([ob])
        move_to_collection([ob], g.ctx.coll(col or g.coll_name))
        g.n_objects += 1
        _CACHE[asset_id] = [ob, bb, True]
        if asset_id not in USED_ASSETS:
            USED_ASSETS.append(asset_id)
    ent = _CACHE[asset_id]
    src, bb, fresh = ent
    if fresh:
        ob = src
        ent[2] = False
    else:
        ob = src.copy()
        g._link(ob, col)
    x0, x1, y0, y1, z0, z1 = bb
    s = height_ft / max(y1 - y0, 1e-6)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    if matrix is None:
        matrix = Matrix.Rotation(rot, 4, 'Z')
    # base-centre of the native model -> origin, scale, orient, then move to `at`
    pre = Matrix.Translation(-Vector(ft2bl(cx, y0, cz)))
    ob.matrix_world = Matrix.Translation(ft2bl(*at)) @ matrix @ Matrix.Diagonal((s, s, s, 1.0)) @ pre
    return ob


def _leaf_bouquet(g, name, base, n_stems, height, spread, seed, col, leaf_r=0.06, droop=0.25, leaf_mat=None):
    """Silver-dollar eucalyptus stems rising from `base` (SCENE point at the vase mouth).
    All leaves of the bouquet are merged into one mesh; stems are thin tubes."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    stems = []
    for i in range(n_stems):
        phi = 2 * math.pi * (i + rnd.uniform(-0.25, 0.25)) / n_stems
        L = height * rnd.uniform(0.75, 1.05)
        sp = spread * rnd.uniform(0.6, 1.1)
        pts = []
        for k in range(9):
            t = k / 8
            h = L * t
            r = sp * (t ** 1.4)
            dy = -droop * L * max(t - 0.55, 0) ** 2
            pts.append((base[0] + r * math.cos(phi), base[1] + h + dy, base[2] + r * math.sin(phi)))
        stems.append(pts)
        # leaves: alternate pairs along the upper 80% of the stem
        nl = rnd.randint(11, 15)
        for j in range(nl):
            t = 0.22 + 0.78 * j / max(nl - 1, 1)
            k = min(int(t * 8), 7)
            f = t * 8 - k
            p = Vector(pts[k]).lerp(Vector(pts[k + 1]), f)
            tang = (Vector(pts[k + 1]) - Vector(pts[k])).normalized()
            side = tang.cross(Vector((0, 1, 0)))
            if side.length < 1e-3:
                side = Vector((1, 0, 0))
            side.normalize()
            sgn = 1 if j % 2 else -1
            rr = leaf_r * rnd.uniform(0.75, 1.15) * (0.75 + 0.25 * (1 - t))
            c = p + side * sgn * rr * 0.9
            n = (side * sgn * 0.6 + Vector((0, 1, 0)) * 0.8 + Vector((rnd.uniform(-.4, .4), 0, rnd.uniform(-.4, .4)))).normalized()
            u = n.cross(tang)
            if u.length < 1e-3:
                u = n.cross(Vector((1, 0, 0)))
            u.normalize()
            v = n.cross(u).normalized()
            ring = []
            m = 14
            cv = bm.verts.new(P(*(c + n * rr * 0.12)))
            for q in range(m):
                a = 2 * math.pi * q / m
                w = c + (u * math.cos(a) + v * math.sin(a)) * rr
                ring.append(bm.verts.new(P(*w)))
            for q in range(m):
                bm.faces.new((cv, ring[q], ring[(q + 1) % m]))
    leaf_mat = leaf_mat or principled('eucalyptus', srgb('#5f7a6a'), 0.5, transl=srgb('#86a487'))
    leaves = g.from_bmesh(name + ' leaves', bm, leaf_mat, col, smooth=True)
    stem_mat = principled('stem', srgb('#6d6f55'), 0.6)
    for i, pts in enumerate(stems):
        g.tube(f'{name} stem {i}', pts, 0.008, stem_mat, col, res=4)
    return leaves


def build(ctx, g: Geo, dining=True, herb=True):
    col = g.sub('kd decor')
    n0 = g.n_objects
    stoneware = principled('stoneware', srgb('#ebe6dc'), 0.62)
    glaze = 'ceramic_white'

    # --------------------------------------------------- island: bowl of lemons
    bx, bz = 32.75, 23.30
    bowl_prof = [(0.0, 0.0), (0.16, 0.0), (0.17, 0.012), (0.30, 0.10), (0.42, 0.22), (0.46, 0.27), (0.455, 0.278),
                 (0.40, 0.235), (0.28, 0.13), (0.15, 0.04), (0.0, 0.035)]
    g.lathe('kd decor bowl', bowl_prof, bx, bz, glaze, 72, col, y_base=TOP, sharp_deg=70)
    # lemons lie on their sides, long axis radial, tips raised along the bowl wall;
    # model is 0.313 ft long natively -> 0.27 ft (8cm); half thickness ~0.097 ft
    L = 0.27
    for i, (ang, rho, yc, tilt, roll) in enumerate(((20, 0.15, 0.15, 10, 0.4), (140, 0.15, 0.15, 8, 2.1),
                                                     (260, 0.15, 0.15, 12, 4.4), (75, 0.03, 0.30, -4, 1.0))):
        phi = math.radians(ang)
        psi = math.pi / 2 - phi
        M = Matrix.Rotation(psi, 4, 'Z') @ Matrix.Rotation(math.radians(90 - tilt), 4, 'X') @ Matrix.Rotation(roll, 4, 'Z')
        # the base-centre pivot sits at the lemon's tail; shift so the lemon's middle is at (rho, yc)
        mid = Vector(ft2bl(bx + rho * math.cos(phi), TOP + yc, bz + rho * math.sin(phi)))
        axis = (M @ Vector((0, 0, 1, 0))).to_3d()
        base = mid - axis * (L / 2) * FT
        bl = (base.x / FT, base.z / FT, -base.y / FT)
        _import(g, 'lemon', L, bl, col=col, matrix=M)
    # ---------------------------------------------- island: vase with eucalyptus
    vx, vz = 30.05, 23.55
    _import(g, 'ceramic_vase_01', 0.95, (vx, TOP, vz), 0.6, col)
    _leaf_bouquet(g, 'kd island eucalyptus', (vx, TOP + 0.88, vz), 9, 1.25, 0.55, 7, col, leaf_r=0.07)

    # --------------------------------------- south counter: board + jug + crock
    board = principled('board_oak', srgb('#c69b6d'), 0.5)
    # oak board leaning on the backsplash (bottom edge on the worktop, 12deg lean)
    _cutting_board(g, 31.35, col, 'white_oak_veneer')
    _import(g, 'ceramic_vase_04', 0.62, (32.45, TOP, 30.95), 2.4, col)
    # small salt cellar + oil cruet beside the cooktop
    g.lathe('kd decor salt cellar', [(0.0, 0.0), (0.12, 0.0), (0.13, 0.02), (0.13, 0.17), (0.11, 0.18), (0.10, 0.03), (0.0, 0.03)],
            37.05, 30.55, stoneware, 48, col, y_base=TOP)
    g.lathe('kd decor oil cruet', [(0.0, 0.0), (0.09, 0.0), (0.10, 0.02), (0.10, 0.42), (0.07, 0.50), (0.035, 0.56),
                                   (0.035, 0.64), (0.0, 0.64)], 37.40, 30.75,
            principled('cruet_glass_amber', srgb('#3a2412'), 0.12), 48, col, y_base=TOP)
    g.lathe('kd decor cruet cork', [(0.0, 0.0), (0.03, 0.0), (0.034, 0.08), (0.0, 0.08)], 37.40, 30.75,
            principled('cork', srgb('#a88a63'), 0.8), 16, col, y_base=TOP + 0.64)

    # ------------------------------------------------------- floating shelves
    # lower shelf (top at 5.027): stack of plates + stoneware jar
    sh0, sh1 = 4.86 + 0.167, 6.24 + 0.167
    for k in range(5):
        _plate(g, 37.35, sh0 + 0.004 + k * 0.045, 30.92, 0.46, glaze, col)
    _import(g, 'ceramic_vase_02', 0.55, (39.55, sh0, 30.93), 0.3, col)
    # upper shelf: two nested bowls and a slim vase
    g.lathe('kd decor shelf bowl a', [(0.0, 0.0), (0.12, 0.0), (0.26, 0.12), (0.33, 0.21), (0.32, 0.215), (0.24, 0.13), (0.11, 0.03), (0.0, 0.025)],
            37.55, 30.92, stoneware, 64, col, y_base=sh1, sharp_deg=70)
    g.lathe('kd decor shelf bowl b', [(0.0, 0.0), (0.09, 0.0), (0.18, 0.08), (0.23, 0.15), (0.22, 0.155), (0.17, 0.09), (0.08, 0.02), (0.0, 0.017)],
            37.55, 30.92, glaze, 64, col, y_base=sh1 + 0.035, sharp_deg=70)
    g.lathe('kd decor shelf vase', [(0.0, 0.0), (0.12, 0.0), (0.16, 0.10), (0.17, 0.30), (0.12, 0.58), (0.075, 0.70),
                                    (0.08, 0.76), (0.065, 0.76), (0.06, 0.70), (0.0, 0.69)], 39.35, 30.95,
            principled('vase_charcoal', srgb('#3b3a38'), 0.55), 64, col, y_base=sh1, sharp_deg=70)

    # ----------------------------------------------- sink run: soap + herb pot
    g.lathe('kd decor soap pump', [(0.0, 0.0), (0.10, 0.0), (0.11, 0.02), (0.11, 0.42), (0.08, 0.47), (0.03, 0.48), (0.0, 0.48)],
            40.27, 28.15, stoneware, 48, col, y_base=TOP)
    g.cyl('kd decor soap pump head', 40.27, TOP + 0.48, TOP + 0.56, 28.15, 0.022, 'black_metal', 16, col)
    g.cyl_axis('kd decor soap pump nozzle', (40.27, TOP + 0.545, 28.15), (40.15, TOP + 0.545, 28.15), 0.014, 'black_metal', 12, col)
    # herb pot at the north end of the east run (skipped when the olive tree stands beside the run end)
    hx, hz = 39.85, 22.45
    if herb:
        g.lathe('kd decor herb pot', [(0.0, 0.0), (0.20, 0.0), (0.22, 0.02), (0.24, 0.38), (0.23, 0.40), (0.20, 0.40), (0.0, 0.37)],
                hx, hz, stoneware, 48, col, y_base=TOP)
        herb_m = principled('herb_leaf', srgb('#4d6b3a'), 0.5, transl=srgb('#7ea35a'))
        _leaf_bouquet(g, 'kd herb', (hx, TOP + 0.37, hz), 11, 0.55, 0.35, 21, col, leaf_r=0.045, droop=0.6, leaf_mat=herb_m)

    # -------------------------------------------------------------- dining table
    if not dining:
        return {'decor_objects': g.n_objects - n0, 'assets': list(USED_ASSETS)}
    from .kitchen_dining_dining import TABLE_C, TABLE_TOP
    tx, tz = TABLE_C
    _import(g, 'ceramic_vase_02', 0.62, (tx - 0.1, TABLE_TOP, tz + 0.05), 1.1, col)
    _leaf_bouquet(g, 'kd table eucalyptus', (tx - 0.1, TABLE_TOP + 0.58, tz + 0.05), 11, 1.1, 0.75, 3, col, leaf_r=0.07, droop=0.45)
    # low matte stoneware bowl grouped with the vase (no stray plates)
    g.lathe('kd decor table bowl', [(0.0, 0.0), (0.13, 0.0), (0.14, 0.012), (0.24, 0.07), (0.34, 0.19), (0.36, 0.24),
                                    (0.345, 0.245), (0.32, 0.20), (0.22, 0.09), (0.12, 0.04), (0.0, 0.035)],
            tx + 0.55, tz - 0.42, stoneware, 72, col, y_base=TABLE_TOP, sharp_deg=70)
    return {'decor_objects': g.n_objects - n0, 'assets': list(USED_ASSETS)}


def _plate(g, x, y, z, d, mat, col):
    r = d / 2
    prof = [(0.0, 0.0), (r * 0.55, 0.0), (r * 0.6, 0.008), (r * 0.62, 0.012), (r * 0.95, 0.03), (r, 0.036),
            (r * 0.99, 0.040), (r * 0.94, 0.036), (r * 0.6, 0.02), (0.0, 0.018)]
    return g.lathe('kd decor plate', prof, x, z, mat, 72, col, y_base=y, sharp_deg=75)


def _cutting_board(g, x, col, mat):
    """Oak paddle board (14 x 20in + handle) leaning against the south backsplash."""
    w, h, t = 0.95, 1.18, 0.07
    hw, hl = 0.30, 0.36
    pts = []
    # outline in board-local (u across, v up), rounded corners
    r = 0.12
    def arc(cx, cy, a0, a1, n=6):
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    pts += arc(w / 2 - r, r, -90, 0)
    pts += arc(w / 2 - r, h - r, 0, 60, 3)
    pts += [(hw / 2, h + 0.02), (hw / 2, h + hl - hw / 2)]
    pts += [(hw / 2 * math.cos(math.radians(a)), h + hl - hw / 2 + hw / 2 * math.sin(math.radians(a))) for a in range(0, 181, 20)]
    pts += [(-hw / 2, h + 0.02)]
    pts += arc(-w / 2 + r, h - r, 120, 180, 3)
    pts += arc(-w / 2 + r, r, 180, 270)
    bm = bmesh.new()
    lean = math.radians(11)
    zback = 31.35 - 0.01                 # backsplash face
    base_z = zback - math.sin(lean) * (h + hl) - t - 0.004
    def world(u, v, s):
        # board plane: u -> +x, v up and leaning back toward the wall (+z)
        y = TOP + v * math.cos(lean) + s * math.sin(lean) * 0
        zz = base_z + v * math.sin(lean) + s
        return P(x + u, y, zz)
    front = [bm.verts.new(world(u, v, 0.0)) for u, v in pts]
    back = [bm.verts.new(world(u, v, t)) for u, v in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    ob = g.from_bmesh('kd decor cutting board', bm, mat, col)
    Geo.bevel_mod(ob, 0.015, 3)
    ob.data.shade_smooth()
    # hang hole
    return ob
