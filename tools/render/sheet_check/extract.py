"""Sheet check, step 1: dump the built model for measure.py. Evaluated world-space meshes of the architecture, the
interior zones and the non-plant site pieces of a built .blend, in SCENE feet. Read-only (nothing is saved to the
.blend); writes <dump prefix>.npz (vertices, triangles, owner of each triangle) and <dump prefix>.json (name,
collections and box of each object). About 1 minute, 115 MB.

    $BLENDER -b <build>.blend --python tools/render/sheet_check/extract.py -- <dump prefix>

See README.md in this folder."""
import bpy, numpy as np, json, sys, time
FT = 0.3048
OUT = sys.argv[sys.argv.index('--') + 1]
t0 = time.time()
parents = {ch.name: p.name for p in bpy.data.collections for ch in p.children}
def chain(n):
    out = [n]
    while n in parents and len(out) < 12:
        n = parents[n]; out.append(n)
    return out
KEEP_TOP = {'shell', 'openings', 'exterior_shell', 'zone_kitchen_dining', 'zone_living', 'zone_primary_suite',
            'zone_bedrooms', 'zone_baths', 'zone_hall_entry_garage'}
KEEP_EXT = {'ext_site', 'ext_fence', 'ext_garage_door'}
scn = bpy.context.scene
print('units', scn.unit_settings.system, scn.unit_settings.scale_length, flush=True)
dg = bpy.context.evaluated_depsgraph_get()
V, T, OWN, meta, base, n_seen = [], [], [], [], 0, 0
for inst in dg.object_instances:
    ob = inst.object
    if ob.type != 'MESH':
        continue
    n_seen += 1
    orig = inst.parent.original if inst.is_instance else ob.original
    chains = [chain(c.name) for c in orig.users_collection]
    tops = {c[-1] for c in chains}
    allc = {n for c in chains for n in c}
    if not (tops & KEEP_TOP or ('zone_exterior' in tops and allc & KEEP_EXT)):
        continue
    if orig.hide_render:
        continue
    if inst.is_instance and 'zone_exterior' in tops:      # lawn, pebbles, plants: dropped from the audit's mine_small too
        continue
    me = ob.to_mesh()
    nv = len(me.vertices)
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    if nv == 0 or nt == 0 or nt > 400000:
        ob.to_mesh_clear(); continue
    co = np.empty(nv * 3, np.float64); me.vertices.foreach_get('co', co)
    mw = np.array(inst.matrix_world)
    co = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    tri = np.empty(nt * 3, np.int32); me.loop_triangles.foreach_get('vertices', tri)
    ob.to_mesh_clear()
    sc = np.stack([co[:, 0] / FT, co[:, 2] / FT, -co[:, 1] / FT], 1)       # SCENE feet: x east, y up, z south
    V.append(sc); T.append(tri.reshape(-1, 3) + base); OWN.append(np.full(nt, len(meta), np.int32))
    meta.append({'name': orig.name, 'inst': ob.name if inst.is_instance else None, 'tops': sorted(tops), 'colls': sorted(allc), 'nt': int(nt),
                 'aabb': [float(v) for v in (sc[:, 0].min(), sc[:, 0].max(), sc[:, 1].min(), sc[:, 1].max(), sc[:, 2].min(), sc[:, 2].max())]})
    base += nv
np.savez(OUT + '.npz', V=np.concatenate(V), T=np.concatenate(T), OWN=np.concatenate(OWN))
json.dump({'meta': meta, 'blend': bpy.data.filepath, 'units': [scn.unit_settings.system, scn.unit_settings.scale_length]}, open(OUT + '.json', 'w'))
print('mesh instances seen', n_seen, 'kept', len(meta), 'tris', sum(len(t) for t in T), 'in %.1fs' % (time.time() - t0), flush=True)
