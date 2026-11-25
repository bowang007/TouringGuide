"""Exterior zone: everything outside the walls (runs inside Blender).

Grounds and hardscape (exterior_site), charcoal slat fences + gates (exterior_fence), the stained-cedar
carriage-house garage door (owner's styles/grage_stype.jpg) with its inside hardware, black coach lanterns
and house number (exterior_garage), lawn / pebbles / ornamental grasses / Poly Haven trees and shrubs
(exterior_plants) and the neighbourhood context (exterior_context). exterior_far fills out the whole
neighbourhood for the drone-height exterior renders only (excluded from the view layer by default).
Site plan: exterior_layout.
"""
import time

import bpy

from . import exterior_context, exterior_far, exterior_fence, exterior_garage, exterior_plants, exterior_site
from .exterior_util import coll, mesh_tris

SUBS = ('site', 'fence', 'garage_door', 'lights', 'plants', 'context', 'far', 'library', 'library_proc', 'lib_pebbles')


def _tri_stats(root):
    """Unique (mesh data) triangles and instanced triangle estimate for the zone."""
    seen = set()
    unique = 0
    objs = 0
    for ob in root.all_objects:
        objs += 1
        if ob.type == 'MESH' and ob.data.name not in seen:
            seen.add(ob.data.name)
            unique += mesh_tris(ob.data)
    return objs, unique


def build(ctx):
    t0 = time.time()
    root = coll(ctx)
    for s in SUBS:
        coll(ctx, s)
    out = {}
    t = time.time()
    out['site'] = exterior_site.build(ctx)
    surfaces = {k: out['site'].pop(k) for k in ('lawns', 'beds', 'pebbles')}
    out['t_site'] = round(time.time() - t, 1)
    t = time.time()
    out['fence'] = exterior_fence.build(ctx)
    out['garage'] = exterior_garage.build(ctx)
    out['t_fence_garage'] = round(time.time() - t, 1)
    t = time.time()
    out['plants'] = exterior_plants.build(ctx, surfaces)
    out['t_plants'] = round(time.time() - t, 1)
    t = time.time()
    out['context'] = exterior_context.build(ctx)
    out['t_context'] = round(time.time() - t, 1)
    t = time.time()
    out['far'] = exterior_far.build(ctx)        # excluded from the view layer; render_exterior.py turns it on
    out['t_far'] = round(time.time() - t, 1)
    out['settle'] = exterior_site.settle(ctx)   # v7 site: the level site set down on the ground of sheet A1.3
    objs, unique = _tri_stats(root)
    out['objects'] = objs
    out['unique_tris'] = unique
    out['assets'] = sorted(set(ctx.stats.get('exterior_assets', [])))
    out['seconds'] = round(time.time() - t0, 1)
    try:
        from .. import assets
        assets.write_manifest()
    except Exception as e:  # never fail a build over attribution bookkeeping
        print('[exterior] write_manifest failed:', e)
    ctx.stats['exterior'] = out
    return out
