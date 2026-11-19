"""Carry the built house from the concept plan onto the architect's plan (runs inside Blender).

The shell and the room modules are written against the concept plan (tools/render/data/concept/, the
frozen pre-PDF SCENE). After they have built, warp() maps every object with relayout.py, the same
function that converted the web tour's SCENE, so the render and the web data agree:

  - architecture (shell, openings, exterior shell) and fitted pieces (cabinet carcasses, worktops,
    tiles, closet shelves/rods, shower glass, tubs, rugs, ...) are reshaped vertex by vertex, with
    the map of the region their centre is in (roof planes vertex by vertex with each vertex's own
    region, so shared edges stay closed);
  - loose things (furniture, lamps, decor, appliances, fixtures, art, lights, instanced plants) are
    moved without changing shape. Pieces that touch each other (a nightstand, its lamp and books; a
    bed and its headboard) form one cluster and move by one shared offset, so assemblies stay intact.

The exterior zone is built directly on the new site plan (bl/zones/exterior_layout.py) and is not
warped.
"""
import math
import os
import re
import sys

import bpy
import numpy as np

from .common import FT

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import relayout as R  # noqa: E402

SKIP_COLLS = ('zone_exterior', 'ext_', 'lib ', 'library')
ARCH_COLLS = {'shell', 'openings', 'exterior_shell'}
LOOSE = re.compile(
    r'\b(bed\b|bed rail|bed plinth|headboard|nightstand|lamp|book|bowl|vase|art\b|art |frame|canvas|bench|dresser|'
    r'mirror|sofa|chair|stool|table|desk|lounge|plant|tree|planter|pillow|throw|duvet|cushion|basket|folded|'
    r'hanger|hook|shirt|jacket|trousers|dress|towel|soap|candle|tray|succulent|bottle|pump|faucet|basin|vessel|'
    r'WC|paper|exhaust|can\b|can |sconce|outlet|switch|thermostat|oven|fridge|freezer|dishwasher|pull|handle|'
    r'hinge|clamp|lever|valve|spout|rain|hook|bar\b|rose|post|knob|pendant|chandelier|fixture|bulb|shade|'
    r'cassette|curtain|drape|blind|lens|trim\b|ledge books|olive|lemon|fruit|cutting|board|kettle|pot|pan\b|'
    r'tv|television|speaker|console|cabinet door|stile|rail [BT]|cane|scribble|horizon|arches|plaster\b|'
    r'mat\b|slipper|shoe|bag|hat|box|lid|tab|stack|car\b|bike|bin\b|tool|hose|vacuum|broom|ladder|'
    r'flame|ember|glow|pampas|stem|branch|blossom|leaf|leaves|fluff|tail|bunny|sculpture|object|globe|clock|'
    r'phone|laptop|remote|coaster|glass\b(?! (door|fixed|inline|return|panel))|cup|mug|plate\b|bowl|spoon)',
    re.I)
FITTED = re.compile(
    r'tile|wetwall|wave|fluted|niche (back|sill)|carcass|worktop|splash|plinth|channel|shelf|rod\b|rod cup|track|'
    r'tower side|tub\b|shower|floor|knee wall|hood plaster|hood filter|upper door|upper carcass|end panel|side panel|'
    r'filler|rug|runner|stone feature|firebox|hearth|led strip|deck\b|drawer deck|hang deck|slider|guide|stool\b|'
    r'return|drain grate|drain\b|vanity (carcass|top|front|toe)|linen (carcass|top|door)|island|counter|'
    r'stair|wall\b|infill|soffit|cove|panel', re.I)


def _skip(ob):
    for c in ob.users_collection:
        if c.name.startswith(SKIP_COLLS):
            return True
    return False


def _arch(ob):
    return any(c.name in ARCH_COLLS for c in ob.users_collection)


def _world_co(ob):
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world)
    return co @ mw[:3, :3].T + mw[:3, 3], mw


def _set_world_co(ob, w, mw):
    inv = np.linalg.inv(mw)
    loc = w @ inv[:3, :3].T + inv[:3, 3]
    ob.data.vertices.foreach_set('co', loc.ravel())
    ob.data.update()


def _bbox_ft(ob):
    if ob.type == 'MESH' and len(ob.data.vertices):
        w, _ = _world_co(ob)
        x = w[:, 0] / FT
        z = -w[:, 1] / FT
        return float(x.min()), float(x.max()), float(z.min()), float(z.max())
    t = ob.matrix_world.translation
    return t.x / FT, t.x / FT, -t.y / FT, -t.y / FT


# Pieces that sit in a wall's thickness on a region boundary but belong to the room on one side.
REGION_BY_NAME = [(re.compile(r'entry vault knee wall', re.I), 'foyer + porch')]


def _region_for(ob, x, z):
    for rx, name in REGION_BY_NAME:
        if rx.search(ob.name):
            return next(r for r in R.REGIONS if r[6] == name)
    return R.region((x.min() + x.max()) / 2, (z.min() + z.max()) / 2)


def _warp_slab(ob):
    """Flat slabs (floors, substrates, foundations, ceilings) that run across several rooms: each
    vertex is mapped with the region of a point just inside the slab from it, so every edge follows
    the room it borders."""
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    w, mw = _world_co(ob)
    x = w[:, 0] / FT
    z = -w[:, 1] / FT
    cx, cz = (x.min() + x.max()) / 2, (z.min() + z.max()) / 2
    nx = np.empty_like(x)
    nz = np.empty_like(z)
    for i in range(len(x)):
        px = x[i] + math.copysign(min(0.6, abs(cx - x[i])), cx - x[i])
        pz = z[i] + math.copysign(min(0.6, abs(cz - z[i])), cz - z[i])
        nx[i], nz[i] = R.remap_xz(float(x[i]), float(z[i]), (px, pz))
    w[:, 0] = nx * FT
    w[:, 1] = -nz * FT
    _set_world_co(ob, w, mw)


def _is_slab(ob):
    if ob.type != 'MESH' or not len(ob.data.vertices):
        return False
    w, _ = _world_co(ob)
    dy = (w[:, 2].max() - w[:, 2].min()) / FT
    sx = (w[:, 0].max() - w[:, 0].min()) / FT
    sz = (w[:, 1].max() - w[:, 1].min()) / FT
    return dy < 0.8 and max(sx, sz) > 4.0 and min(sx, sz) > 1.0


def _warp_mesh(ob, per_vertex=False):
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    w, mw = _world_co(ob)
    x = w[:, 0] / FT
    z = -w[:, 1] / FT
    if per_vertex:
        nx = np.empty_like(x)
        nz = np.empty_like(z)
        for i in range(len(x)):
            nx[i], nz[i] = R.remap_xz(float(x[i]), float(z[i]))
    else:
        r = _region_for(ob, x, z)
        nx = np.array([r[4](float(v)) for v in x])
        nz = np.array([r[5](float(v)) for v in z])
    w[:, 0] = nx * FT
    w[:, 1] = -nz * FT
    _set_world_co(ob, w, mw)


def _translate(ob, dx, dz):
    ob.location.x += dx * FT
    ob.location.y -= dz * FT


def _clusters(items, pad=0.12):
    """Union boxes that touch (within pad ft); returns lists of item indices."""
    n = len(items)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    bb = [it[1] for it in items]
    for i in range(n):
        a = bb[i]
        for j in range(i + 1, n):
            b = bb[j]
            if a[0] - pad <= b[1] and b[0] - pad <= a[1] and a[2] - pad <= b[3] and b[2] - pad <= a[3]:
                ra, rb = find(i), find(j)
                if ra != rb:
                    parent[ra] = rb
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def warp():
    bpy.context.view_layer.update()
    stats = {'arch': 0, 'roof': 0, 'fitted': 0, 'loose': 0, 'clusters': 0, 'skipped': 0}
    loose = []
    for ob in list(bpy.data.objects):
        if ob.parent is not None or ob.type in ('CAMERA',) or ob.name.startswith('TG '):
            continue
        if ob.type == 'LIGHT' and ob.data.type == 'SUN':
            continue
        if _skip(ob) or not ob.users_collection:
            stats['skipped'] += 1
            continue
        if ob.type == 'MESH' and _arch(ob) and _is_slab(ob) and not re.search(r'roof|ridge|hip|valley|canopy', ob.name, re.I):
            _warp_slab(ob)
            stats['slab'] = stats.get('slab', 0) + 1
            continue
        if ob.type == 'MESH' and _arch(ob):
            roof = bool(re.search(r'roof|ridge|hip|valley|fascia|gable|eave|soffit|cap\b|flashing|stucco skin', ob.name, re.I))
            _warp_mesh(ob, per_vertex=roof)
            stats['roof' if roof else 'arch'] += 1
            continue
        if ob.type == 'MESH' and len(ob.data.vertices) and FITTED.search(ob.name) and not LOOSE.search(ob.name):
            _warp_mesh(ob)
            stats['fitted'] += 1
            continue
        loose.append((ob, _bbox_ft(ob)))
    for g in _clusters(loose):
        x0 = min(loose[i][1][0] for i in g)
        x1 = max(loose[i][1][1] for i in g)
        z0 = min(loose[i][1][2] for i in g)
        z1 = max(loose[i][1][3] for i in g)
        dx, dz = R.shift_xz((x0 + x1) / 2, (z0 + z1) / 2)
        for i in g:
            _translate(loose[i][0], dx, dz)
        stats['loose'] += len(g)
        stats['clusters'] += 1
    bpy.context.view_layer.update()
    return stats
