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
    """Vintage-kitchen styling (owner's references): a cream crock of tall leafy branches and a
    bowl of lemons on the island, dishes behind the glass uppers, plates / a framed print / jars on
    the walnut shelves, oak boards and a utensil crock on the counter, a brass mushroom lamp, a
    vintage kettle on the cooktop, a stoneware soap pump at the sink, a pitcher on the table."""
    from . import kitchen_dining_kitchen as K
    from . import kitchen_dining_mats as KM
    col = g.sub('kd decor')
    n0 = g.n_objects
    stoneware = principled('stoneware', srgb('#ebe6dc'), 0.62)
    glaze = 'ceramic_white'
    crock = KM.stoneware('crock', '#e6dccb', 0.38, 0.35)
    brass = KM.brass()

    # --------------------------------------------------- island: bowl of lemons
    bx, bz = 32.75, 23.30
    bowl_prof = [(0.0, 0.0), (0.16, 0.0), (0.17, 0.012), (0.30, 0.10), (0.42, 0.22), (0.46, 0.27), (0.455, 0.278),
                 (0.40, 0.235), (0.28, 0.13), (0.15, 0.04), (0.0, 0.035)]
    g.lathe('kd decor bowl', bowl_prof, bx, bz, glaze, 72, col, y_base=TOP, sharp_deg=70)
    L = 0.27
    for i, (ang, rho, yc, tilt, roll) in enumerate(((20, 0.15, 0.15, 10, 0.4), (140, 0.15, 0.15, 8, 2.1),
                                                     (260, 0.15, 0.15, 12, 4.4), (75, 0.03, 0.30, -4, 1.0))):
        phi = math.radians(ang)
        psi = math.pi / 2 - phi
        M = Matrix.Rotation(psi, 4, 'Z') @ Matrix.Rotation(math.radians(90 - tilt), 4, 'X') @ Matrix.Rotation(roll, 4, 'Z')
        mid = Vector(ft2bl(bx + rho * math.cos(phi), TOP + yc, bz + rho * math.sin(phi)))
        axis = (M @ Vector((0, 0, 1, 0))).to_3d()
        base = mid - axis * (L / 2) * FT
        bl = (base.x / FT, base.z / FT, -base.y / FT)
        _import(g, 'lemon', L, bl, col=col, matrix=M)
    # ------------------------------- island: cream crock with tall leafy branches
    vx, vz = 30.05, 23.45
    ch = 0.78
    g.lathe('kd decor crock vase', [(0.0, 0.0), (0.27, 0.0), (0.29, 0.02), (0.31, 0.1), (0.31, ch - 0.12), (0.29, ch - 0.05),
                                    (0.27, ch - 0.02), (0.275, ch), (0.255, ch), (0.24, ch - 0.06), (0.0, ch - 0.1)],
            vx, vz, crock, 64, col, y_base=TOP, sharp_deg=50)
    g.lathe('kd decor crock vase band', [(0.312, ch - 0.2), (0.314, ch - 0.18), (0.314, ch - 0.165), (0.312, ch - 0.15)],
            vx, vz, principled('crock_band', srgb('#7a5a3e'), 0.4), 64, col, y_base=TOP)
    leaf = principled('branch_leaf', srgb('#4f6440'), 0.5, transl=srgb('#7f9a55'))
    _leaf_bouquet(g, 'kd island branch', (vx, TOP + ch - 0.08, vz), 9, 1.8, 0.95, 11, col, leaf_r=0.085, droop=0.32,
                  leaf_mat=leaf)

    # --------------------------------------- south counter under the glass uppers
    _cutting_board(g, 29.15, col, KM.oak_island())
    _cutting_board(g, 29.55, col, 'walnut_slab', scale=0.78, out=0.082)
    ux, uz = 31.25, 30.9
    g.lathe('kd decor utensil crock', [(0.0, 0.0), (0.2, 0.0), (0.215, 0.02), (0.22, 0.5), (0.205, 0.52), (0.19, 0.5),
                                       (0.19, 0.05), (0.0, 0.05)], ux, uz, crock, 48, col, y_base=TOP, sharp_deg=60)
    for k, (dx, dz, tilt, h) in enumerate(((-0.06, 0.03, 0.10, 1.05), (0.06, -0.04, -0.12, 1.0), (0.02, 0.07, 0.05, 0.95),
                                           (-0.03, -0.06, -0.05, 1.1))):
        a = (ux + dx, TOP + 0.06, uz + dz)
        b = (ux + dx + tilt * 1.6, TOP + h, uz + dz + tilt * 0.5)
        g.cyl_axis('kd decor spoon stem', a, b, 0.017, KM.oak_island(), 8, col)
        g.lathe('kd decor spoon head', [(0.0, 0.0), (0.04, 0.02), (0.055, 0.08), (0.045, 0.15), (0.0, 0.17)],
                b[0], b[2], KM.oak_island(), 16, col, y_base=b[1] - 0.02)
    _import(g, 'ceramic_vase_04', 0.62, (32.6, TOP, 30.95), 2.4, col)

    # ----------------------------------------- right of the cooktop: brass lamp, salt, cruet
    lx, lz = 37.15, 30.95
    g.lathe('kd decor brass lamp base', [(0.0, 0.0), (0.2, 0.0), (0.21, 0.02), (0.17, 0.05), (0.05, 0.08), (0.0, 0.08)],
            lx, lz, brass, 48, col, y_base=TOP)
    g.cyl('kd decor brass lamp stem', lx, TOP + 0.08, TOP + 0.78, lz, 0.025, brass, 16, col)
    g.lathe('kd decor brass lamp shade', [(0.02, 1.02), (0.12, 1.0), (0.22, 0.94), (0.28, 0.85), (0.3, 0.78), (0.28, 0.77),
                                          (0.0, 0.8)], lx, lz, brass, 64, col, y_base=TOP, sharp_deg=60)
    from ..lighting import emitter
    g.lathe('kd decor brass lamp bulb', [(0.0, 0.0), (0.06, 0.005), (0.0, 0.01)], lx, lz, emitter('kd_lamp_glow', 2600, 20.0),
            24, col, y_base=TOP + 0.775)
    g.point_light('kd decor lamp light', lx, TOP + 0.7, lz, 3.0, 2600, 0.08, g.sub('kd_lights'))
    g.lathe('kd decor salt cellar', [(0.0, 0.0), (0.12, 0.0), (0.13, 0.02), (0.13, 0.17), (0.11, 0.18), (0.10, 0.03), (0.0, 0.03)],
            36.75, 30.45, stoneware, 48, col, y_base=TOP)
    g.lathe('kd decor oil cruet', [(0.0, 0.0), (0.09, 0.0), (0.10, 0.02), (0.10, 0.42), (0.07, 0.50), (0.035, 0.56),
                                   (0.035, 0.64), (0.0, 0.64)], 37.85, 30.75,
            principled('cruet_glass_amber', srgb('#3a2412'), 0.12), 48, col, y_base=TOP)
    g.lathe('kd decor cruet cork', [(0.0, 0.0), (0.03, 0.0), (0.034, 0.08), (0.0, 0.08)], 37.85, 30.75,
            principled('cork', srgb('#a88a63'), 0.8), 16, col, y_base=TOP + 0.64)
    # vintage kettle on the back-left burner grate
    try:
        x0, x1, z0, z1 = K.COOK
        _import(g, 'vintage_electric_kettle', 0.82, (x0 + 0.52, TOP + 0.165, z1 - 0.45), 2.2, col)
    except Exception as e:
        print('[kitchen_dining] kettle skipped:', e)

    # ----------------------------------------------------- glass uppers: dishes
    xs = [K.BASE_X0 + i * (K.HOOD[0] - K.BASE_X0) / 3 for i in range(4)]
    zc = 30.86
    for i in range(3):
        cx = (xs[i] + xs[i + 1]) / 2
        if i != 1:
            for k in range(6):
                _plate(g, cx, K.UPPER_Y0 + 0.06 + 0.004 + k * 0.042, zc, 0.88, glaze, col)
        else:
            for k, dx in enumerate((-0.38, 0.0, 0.38)):
                for j in range(3):
                    _bowl(g, cx + dx, K.UPPER_Y0 + 0.06 + 0.003 + j * 0.07, zc, 0.27, glaze, col)
        ys = 5.66 + 0.055
        for dx in (-0.36, 0.0, 0.36):
            g.lathe('kd decor cup', [(0.0, 0.0), (0.09, 0.0), (0.11, 0.02), (0.13, 0.22), (0.12, 0.22), (0.1, 0.03), (0.0, 0.025)],
                    cx + dx, zc - 0.1, glaze, 32, col, y_base=ys + 0.002, sharp_deg=70)
        ys2 = 6.58 + 0.055
        if i == 1:
            g.lathe('kd decor pitcher', [(0.0, 0.0), (0.2, 0.0), (0.24, 0.12), (0.24, 0.4), (0.18, 0.55), (0.17, 0.62), (0.2, 0.68),
                                         (0.19, 0.69), (0.155, 0.63), (0.0, 0.6)], cx, zc, crock, 48, col, y_base=ys2 + 0.002,
                    sharp_deg=60)
        else:
            for k in range(4):
                _bowl(g, cx, ys2 + 0.003 + k * 0.06, zc, 0.5 - k * 0.07, glaze, col)

    # ------------------------------------------------------- walnut open shelves
    sh0, sh1 = 4.86 + 0.1, 6.18 + 0.1
    for k in range(5):
        _plate(g, 37.25, sh0 + 0.004 + k * 0.045, 31.0, 0.66, glaze, col)
    _import(g, 'ceramic_vase_02', 0.55, (39.75, sh0, 30.98), 0.3, col)
    g.lathe('kd decor jar', [(0.0, 0.0), (0.15, 0.0), (0.16, 0.03), (0.16, 0.42), (0.12, 0.46), (0.12, 0.5), (0.0, 0.5)],
            38.55, 31.0, crock, 40, col, y_base=sh0)
    g.lathe('kd decor jar lid', [(0.0, 0.0), (0.14, 0.0), (0.14, 0.04), (0.05, 0.07), (0.03, 0.12), (0.0, 0.12)],
            38.55, 31.0, KM.oak_island(), 32, col, y_base=sh0 + 0.5)
    _framed_print(g, 37.7, sh1, col)
    for k in range(4):
        _bowl(g, 39.55, sh1 + 0.003 + k * 0.06, 31.0, 0.55 - k * 0.07, stoneware, col)

    # ----------------------------------------------------------- sink run
    sp = KM.stoneware('soap', '#d9cfbf', 0.4, 0.3)
    g.lathe('kd decor soap pump', [(0.0, 0.0), (0.10, 0.0), (0.11, 0.02), (0.11, 0.42), (0.08, 0.47), (0.03, 0.48), (0.0, 0.48)],
            40.15, 28.2, sp, 48, col, y_base=TOP)
    g.cyl('kd decor soap pump head', 40.15, TOP + 0.48, TOP + 0.56, 28.2, 0.022, brass, 16, col)
    g.cyl_axis('kd decor soap pump nozzle', (40.15, TOP + 0.545, 28.2), (40.03, TOP + 0.545, 28.2), 0.014, brass, 12, col)
    hx, hz = 39.85, 22.45
    if herb:
        g.lathe('kd decor herb pot', [(0.0, 0.0), (0.20, 0.0), (0.22, 0.02), (0.24, 0.38), (0.23, 0.40), (0.20, 0.40), (0.0, 0.37)],
                hx, hz, stoneware, 48, col, y_base=TOP)
        herb_m = principled('herb_leaf', srgb('#4d6b3a'), 0.5, transl=srgb('#7ea35a'))
        _leaf_bouquet(g, 'kd herb', (hx, TOP + 0.37, hz), 11, 0.55, 0.35, 21, col, leaf_r=0.045, droop=0.6, leaf_mat=herb_m)

    # ------------------------------------------------------------ dining table
    try:
        from .kitchen_dining_dining import RECT_CX, RECT_Z1, RECT_LEN, RECT_TOP
        tx, tz = RECT_CX + 0.35, RECT_Z1 - RECT_LEN / 2 - 0.9
        g.lathe('kd decor table pitcher', [(0.0, 0.0), (0.17, 0.0), (0.2, 0.1), (0.21, 0.35), (0.16, 0.5), (0.14, 0.56),
                                           (0.16, 0.6), (0.15, 0.61), (0.12, 0.57), (0.0, 0.55)], tx, tz, crock, 48, col,
                y_base=RECT_TOP, sharp_deg=60)
        _leaf_bouquet(g, 'kd table eucalyptus', (tx, RECT_TOP + 0.55, tz), 9, 0.9, 0.55, 3, col, leaf_r=0.06, droop=0.45)
        g.lathe('kd decor table bowl', [(0.0, 0.0), (0.13, 0.0), (0.14, 0.012), (0.24, 0.07), (0.34, 0.19), (0.36, 0.24),
                                        (0.345, 0.245), (0.32, 0.20), (0.22, 0.09), (0.12, 0.04), (0.0, 0.035)],
                RECT_CX - 0.2, RECT_Z1 - RECT_LEN / 2 + 1.0, KM.oak_island(), 72, col, y_base=RECT_TOP, sharp_deg=70)
    except Exception as e:
        print('[kitchen_dining] table decor skipped:', e)
    return {'decor_objects': g.n_objects - n0, 'assets': list(USED_ASSETS)}


def _bowl(g, x, y, z, d, mat, col):
    r = d / 2
    prof = [(0.0, 0.0), (r * 0.45, 0.0), (r * 0.5, 0.008), (r * 0.8, r * 0.22), (r, r * 0.42), (r * 0.96, r * 0.43),
            (r * 0.76, r * 0.24), (r * 0.42, 0.03), (0.0, 0.026)]
    return g.lathe('kd decor bowl', prof, x, z, mat, 48, col, y_base=y, sharp_deg=70)


def _framed_print(g, x, y, col):
    """Small framed botanical print leaning on the back of the upper shelf (walnut frame, cream mat)."""
    from .kitchen_dining_mats import stoneware
    w, h, t = 0.78, 0.98, 0.05
    lean = math.radians(8)
    zb = 31.35 - 0.02
    zf = zb - math.sin(lean) * h - t
    import bmesh
    def slab(name, u0, u1, v0, v1, d0, d1, mat):
        bm = bmesh.new()
        vs = []
        for d in (d0, d1):
            for v in (v0, v1):
                for u in (u0, u1):
                    vs.append(bm.verts.new(P(x + u, y + v * math.cos(lean), zf + v * math.sin(lean) + d)))
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            bm.faces.new([vs[i] for i in q])
        return g.from_bmesh(name, bm, mat, col)
    slab('kd decor art frame', -w / 2, w / 2, 0.0, h, 0.0, t, 'walnut_slab')
    slab('kd decor art mat', -w / 2 + 0.07, w / 2 - 0.07, 0.07, h - 0.07, -0.004, 0.0, stoneware('art_mat', '#ece4d4', 0.85, 0.0))
    slab('kd decor art print', -w / 2 + 0.19, w / 2 - 0.19, 0.22, h - 0.22, -0.006, -0.004,
         principled('art_print', srgb('#9c8a68'), 0.8))
    slab('kd decor art glass', -w / 2 + 0.06, w / 2 - 0.06, 0.06, h - 0.06, -0.012, -0.010, 'glass_picture')


def _plate(g, x, y, z, d, mat, col):
    r = d / 2
    prof = [(0.0, 0.0), (r * 0.55, 0.0), (r * 0.6, 0.008), (r * 0.62, 0.012), (r * 0.95, 0.03), (r, 0.036),
            (r * 0.99, 0.040), (r * 0.94, 0.036), (r * 0.6, 0.02), (0.0, 0.018)]
    return g.lathe('kd decor plate', prof, x, z, mat, 72, col, y_base=y, sharp_deg=75)


def _cutting_board(g, x, col, mat, scale=1.0, out=0.0):
    """Oak paddle board (14 x 20in + handle) leaning against the south backsplash (`out` moves
    it forward so a second, smaller board can lean in front of the first)."""
    w, h, t = 0.95 * scale, 1.18 * scale, 0.07
    hw, hl = 0.30 * scale, 0.36 * scale
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
    # the foot of a full-size board; a smaller board leans `out` in front of it, parallel
    base_z = zback - math.sin(lean) * (1.18 + 0.36) - t - 0.004 - out
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
