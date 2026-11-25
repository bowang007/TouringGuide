"""Sheet check: query helpers on a dump of the built model (extract.py; SCENE feet). The dump's prefix comes from the
environment variable DUMP. Run under Blender's Python, for mathutils."""
import json, time, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import os
D = os.environ.get('DUMP')
if not D or not os.path.exists(D + '.json') or not os.path.exists(D + '.npz'):
    raise SystemExit('sheet_check: set DUMP=<dump prefix> to a dump written by extract.py (%s.json / .npz not found)' % D)
META = json.load(open(D + '.json'))['meta']
_z = np.load(D + '.npz'); V = _z['V']; T = _z['T']; OWN = _z['OWN']
INT = ('zone_kitchen_dining', 'zone_living', 'zone_primary_suite', 'zone_bedrooms', 'zone_baths', 'zone_hall_entry_garage')
def top(o, *n): return any(k in o['tops'] for k in n)
GROUPS = {
    'shell': lambda o: top(o, 'shell'),
    'so': lambda o: top(o, 'shell', 'openings'),
    'arch': lambda o: top(o, 'shell', 'openings', 'exterior_shell'),
    'ext': lambda o: top(o, 'exterior_shell'),
    'int': lambda o: top(o, 'shell', 'openings', 'exterior_shell', *INT),
    'zones': lambda o: top(o, *INT),
    'all': lambda o: True,
}
class Tree:
    def __init__(self, pred):
        keep = np.array([bool(pred(o)) for o in META])
        tk = keep[OWN]
        self.tri = T[tk]; self.own = OWN[tk]
        used = np.unique(self.tri)
        remap = np.full(len(V), -1, np.int64); remap[used] = np.arange(len(used))
        self.bvh = BVHTree.FromPolygons([Vector(v) for v in V[used].tolist()], remap[self.tri].tolist(), all_triangles=True, epsilon=0.0)
    def cast(self, o, d, maxd=300.0):
        loc, nrm, i, dist = self.bvh.ray_cast(Vector(o), Vector(d), maxd)
        if loc is None: return None
        return dist, (loc.x, loc.y, loc.z), META[int(self.own[i])]['name']
    def cast_all(self, o, d, maxd=300.0, limit=200):
        out = []; o = Vector(o); d = Vector(d).normalized(); tr = 0.0
        while tr < maxd and len(out) < limit:
            loc, nrm, i, dist = self.bvh.ray_cast(o, d, maxd - tr)
            if loc is None: break
            tr += dist
            out.append((tr, (loc.x, loc.y, loc.z), META[int(self.own[i])]['name']))
            o = loc + d * 1e-5; tr += 1e-5
        return out
_cache = {}
def tree(n):
    if n not in _cache: _cache[n] = Tree(GROUPS[n])
    return _cache[n]
AX = {'x': 0, 'y': 1, 'z': 2}
def pair(tr, o, axis):
    """Rays both ways along an axis from o: (lo face, hi face, distance, names)."""
    d = [0, 0, 0]; d[AX[axis]] = 1
    a = tree(tr).cast(o, [-v for v in d]); b = tree(tr).cast(o, d)
    if a is None or b is None: return None
    i = AX[axis]
    return a[1][i], b[1][i], b[1][i] - a[1][i], a[2], b[2]
def fi(ft):
    """feet -> feet-inches to 1/16 in"""
    s = '-' if ft < 0 else ''; ft = abs(ft)
    n = round(ft * 12 * 16); f, r = divmod(n, 12 * 16); i, x = divmod(r, 16)
    fr = ''
    if x:
        import math
        g = math.gcd(x, 16); fr = f' {x // g}/{16 // g}'
    return f"{s}{f}'-{i}{fr}\""
