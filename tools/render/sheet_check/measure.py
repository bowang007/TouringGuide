"""Sheet check, step 2: measure a dump of the built model (extract.py; SCENE feet) against the architect's sheet
SKA002. Run under Blender's Python:

    DUMP=<dump prefix> $BLENDER -b --python tools/render/sheet_check/measure.py -- <out prefix>

Writes <out>.json and <out>.md and prints the .md. Rays are cast on the dump's triangles (cq.py); nothing reads the
source code's numbers. The sheet as data lies beside this file: ska002_geometry.json (every wall, door, window,
skylight and fixture of SKA002 in the model's coordinates), pdf_dimensions.json (the 39 printed dimensions),
heights_site.json (A1.3's heights, SKA001's site numbers). What a clean model prints: README.md in this folder."""
import sys, os, json, re, math
sys.dont_write_bytecode = True           # keep the folder free of __pycache__
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cq import *                                                     # noqa
import numpy as np
OUT = sys.argv[sys.argv.index('--') + 1]
G = json.load(open(os.path.join(HERE, 'ska002_geometry.json')))
PD = json.load(open(os.path.join(HERE, 'pdf_dimensions.json')))
DIMS = {d['id']: d for s in PD['sheets'] for d in s['dimensions']}
BY = {}
for o in META:
    BY.setdefault(o['name'], []).append(o)
def objs(rx, tops=None, box=None):
    r = re.compile(rx, re.I); out = []
    for o in META:
        if not r.search(o['name']): continue
        if tops and not any(t in o['tops'] or t in o['colls'] for t in tops): continue
        a = o['aabb']
        if box and (a[1] < box[0] or a[0] > box[1] or a[5] < box[2] or a[4] > box[3]): continue
        out.append(o)
    return out
def union(os_):
    if not os_: return None
    a = np.array([o['aabb'] for o in os_])
    return [float(a[:, 0].min()), float(a[:, 1].max()), float(a[:, 2].min()), float(a[:, 3].max()), float(a[:, 4].min()), float(a[:, 5].max())]
def verdict(d_in, owner=False):
    if owner: return 'owner'
    if d_in is None: return 'n.a.'
    a = abs(d_in)
    return 'match' if a <= 0.5 + 1e-6 else ('small' if a <= 2.0 + 1e-6 else 'DIFFERS')
def P(tr, o, axis):
    r = pair(tr, o, axis)
    return None if r is None else {'lo': r[0], 'hi': r[1], 'size': r[2], 'hit_lo': r[3], 'hit_hi': r[4]}
def line(tr, o, d, maxd):
    return [(p, n) for t, p, n in tree(tr).cast_all(o, d, maxd)]
def down(x, z, tr='all', y0=40.0):
    h = tree(tr).cast((x, y0, z), (0, -1, 0))
    return (h[1][1], h[2]) if h else (None, None)
def up(x, z, tr='arch', y0=4.0):
    h = tree(tr).cast((x, y0, z), (0, 1, 0))
    return (h[1][1], h[2]) if h else (None, None)
GROUPS['frames'] = lambda o: top(o, 'shell') or (top(o, 'openings') and re.search(r'jamb|casing|Front door post', o['name']) and not re.search(r'skirting', o['name']))
GROUPS['site'] = lambda o: top(o, 'zone_exterior')
GROUPS['nosite'] = lambda o: not top(o, 'zone_exterior')
R = {}
md = []
def H(t): md.append('\n### ' + t + '\n')
def T(head, rows):
    md.append('| ' + ' | '.join(head) + ' |'); md.append('|' + '---|' * len(head))
    for r in rows: md.append('| ' + ' | '.join(str(c) for c in r) + ' |')
f3 = lambda v: '-' if v is None else '%.3f' % v
f4 = lambda v: '-' if v is None else '%.4f' % v

# ============================================================================== 1. the 39 printed dimensions
rows = []
def D(i, mv, how, owner=False, note=''):
    d = DIMS['SKA002-D%02d' % i]
    diff = None if mv is None else (mv - d['feet']) * 12
    v = verdict(diff, owner)
    rows.append({'no': i, 'text': d['text'], 'measures': d['measures'], 'sheet_ft': d['feet'], 'model_ft': mv, 'diff_in': None if diff is None else round(diff, 2), 'verdict': v, 'how': how, 'note': note})
def sizeof(tr, o, axis):
    r = P(tr, o, axis)
    return (None, 'no hit') if r is None else (r['size'], '%s pair on %s from (%.2f, %.2f, %.2f): %.4f (%s) .. %.4f (%s)' % (axis, tr, o[0], o[1], o[2], r['lo'], r['hit_lo'][:28], r['hi'], r['hit_hi'][:28]))
def lohi(tr, o, axis):
    return P(tr, o, axis)
D(1, *sizeof('shell', (5.5, 4, 7.5), 'x'))
D(2, *sizeof('shell', (17, 4, 6), 'x'))
D(3, *sizeof('shell', (30, 4, 10), 'x'))
D(4, *sizeof('shell', (3, 4, 14), 'x'))
D(5, *sizeof('shell', (9, 7.3, 14.5), 'x'), note='ray above the door heads (the entry and the pocket door are in these two walls)')
# 6: hall beside the block, at the wall piece south of the furnace door and over the heads
h6 = lohi('shell', (13.3, 7.3, 16.5), 'x'); h6b = lohi('shell', (13.3, 4.0, 17.3), 'x')
D(6, h6['size'], 'x pair, shell, y 7.3, z 16.5: %.4f .. %.4f; at y 4, z 17.3: %.4f .. %.4f' % (h6['lo'], h6['hi'], h6b['lo'], h6b['hi']))
liv = lohi('shell', (30, 1.0, 16.5), 'x')
D(7, liv['lo'] - h6['hi'], 'west face of the block %.4f (row 6) to the living-room face of the Bedroom 2 / living wall %.4f (x pair, shell, y 1, z 16.5)' % (h6['hi'], liv['lo']))
# kitchen: island top and counter fronts by name
isl = union(objs(r'^kd island top', ['zone_kitchen_dining'])); R['island_top'] = isl
kx = [(p, n) for p, n in line('int', (26.0, 2.95, 23.2), (1, 0, 0), 13.3)]
kz = [(p, n) for p, n in line('int', (30.0, 2.95, 20.0), (0, 0, 1), 11.2)]
R['kitchen_x_line'] = [[round(p[0], 4), n] for p, n in kx]; R['kitchen_z_line'] = [[round(p[2], 4), n] for p, n in kz]
ix = [p[0] for p, n in kx if re.search('island', n, re.I)]; iz = [p[2] for p, n in kz if re.search('island', n, re.I)]
ecf = min(p[0] for p, n in kx if p[0] > max(ix) + 0.5); scf = min(p[2] for p, n in kz if p[2] > max(iz) + 0.5)
ecn = [n for p, n in kx if abs(p[0] - ecf) < 1e-6][0]; scn = [n for p, n in kz if abs(p[2] - scf) < 1e-6][0]
D(8, ecf - max(ix), 'ray +x at y 2.95, z 23.2: island top east edge %.4f, next surface %.4f (%s)' % (max(ix), ecf, ecn))
D(9, max(ix) - min(ix), 'same ray: island top x %.4f .. %.4f (object box x %.4f .. %.4f)' % (min(ix), max(ix), isl[0], isl[1]))
D(10, *sizeof('shell', (5, 4, 27), 'x'))
lw = lohi('shell', (13.5, 4, 30.2), 'x'); lz = lohi('shell', (13.5, 4, 30.2), 'z')
D(11, None, 'no W / D closet in the kitchen; laundry closet in Bedroom 4\'s corner, inside %.3f x %.3f' % (lw['size'], lz['size']), owner=True, note='owner, 5th round')
D(12, *sizeof('shell', (18.3, 4, 41), 'x'), owner=True, note='owner, 2nd round (foyer wall on the shared bath\'s wall line)')
D(13, *sizeof('shell', (12, 4, 38.2), 'x'), owner=True, note='owner, 2nd round')
# 14..16 Bedroom 3 bath: glass, vanity
b3 = line('int', (0.3, 1.2, 38.5), (1, 0, 0), 8.3); R['bed3bath_x_line_y1.2_z38.5'] = [[round(p[0], 4), n] for p, n in b3]
gl = [p[0] for p, n in b3 if re.search('glass', n, re.I)]
wface = tree('shell').cast((1.5, 1.2, 40.5), (-1, 0, 0))[1][0]
van = union(objs(r'^A3 vanity (top|counter)', ['zone_baths'])) or union(objs(r'^A3 vanity', ['zone_baths']))
vtop = [o for o in objs(r'^A3 vanity', ['zone_baths'])]
R['bed3_vanity_objs'] = {o['name']: [round(v, 4) for v in o['aabb']] for o in vtop}
eface = tree('shell').cast((7.0, 5.0, 40.5), (1, 0, 0))[1][0]
vw = min(o['aabb'][0] for o in vtop) if vtop else None
if gl:
    D(14, max(gl) - wface, 'west wall face %.4f (shell) to the shower glass, outer face %.4f (centre %.4f); ray +x at y 1.2, z 38.5' % (wface, max(gl), (min(gl) + max(gl)) / 2))
    D(15, vw - max(gl), 'glass outer face %.4f to the vanity\'s west edge %.4f (boxes of %d `A3 vanity` objects)' % (max(gl), vw, len(vtop)))
else:
    D(14, None, 'no glass on the ray'); D(15, None, 'no glass')
D(16, eface - vw, 'vanity\'s west edge %.4f to the east wall\'s face %.4f (shell)' % (vw, eface))
pl = line('all', (12.0, 3.0, 54.6), (1, 0, 0), 12.5); R['piers_line'] = [[round(p[0], 4), n] for p, n in pl]
px = [p[0] for p, n in pl if re.search('pier', n, re.I)]
pw = lohi('shell', (18.3, 4, 50.5), 'x')
if len(px) >= 4:
    D(17, px[1] - px[0], 'ray +x at y 3, z 54.6 through the piers: %.4f .. %.4f' % (px[0], px[1]))
    D(18, px[2] - px[1], 'same ray: between the piers %.4f .. %.4f (porch walls %.4f .. %.4f)' % (px[1], px[2], pw['lo'], pw['hi']), owner=True, note='owner, 2nd round')
    D(19, px[3] - px[2], 'same ray: %.4f .. %.4f' % (px[2], px[3]))
else:
    for i in (17, 18, 19): D(i, None, 'piers not found on the ray: %s' % R['piers_line'])
D(20, pw['lo'] - 0.225 if pw else None, 'west wall interior face 0.225 to the porch face of the Bedroom 3 / porch wall %.4f' % pw['lo'], owner=True, note='owner, 2nd round')
D(21, *sizeof('shell', (1.0, 4, 6), 'z'))
D(22, *sizeof('shell', (3, 4, 16.8), 'z'))
D(23, *sizeof('shell', (5.5, 4, 25), 'z'))
D(24, *sizeof('shell', (5, 4, 33), 'z'))
D(25, *sizeof('shell', (7.5, 7.3, 39.5), 'z'), note='ray above the bath door\'s head')
D(26, *sizeof('shell', (2, 4, 48), 'z'))
slab = union(objs(r'^ext porch slab', ['zone_exterior'])); R['porch_slab'] = slab
def face(o, d, tr='arch'):
    h = tree(tr).cast(o, d); return None if h is None else h[1]
b3f = face((2, 4, 60), (0, 0, -1)); gf = face((22.3, 4, 60), (0, 0, -1)); ef = face((15.7, 7.2, 52), (0, 0, -1))
R['front_faces'] = {'bed3': b3f, 'garage': gf, 'entry': ef}
D(27, slab[5] - b3f[2], 'porch slab front edge %.4f less Bedroom 3\'s front wall, outer face %.4f' % (slab[5], b3f[2]))
b2s = tree('shell').cast((13.3, 7.3, 14.0), (0, 0, -1))[1][2]
blk = {'lo': tree('shell').cast((17.0, 4, 19.0), (0, 0, -1))[1][2]}; blk2 = lohi('shell', (15.45, 4, 19.0), 'z')
D(28, blk['lo'] - b2s, 'south face of Bedroom 2\'s south wall %.4f (shell, ray north at x 13.3, y 7.3) to the block\'s south face %.4f (x 17)' % (b2s, blk['lo']))
fy = lohi('shell', (16.0, 7.2, 38), 'z'); b4 = lohi('shell', (5, 4, 33), 'z')
D(29, fy['hi'] - b4['lo'], 'front door wall interior face %.4f (shell, x 16, y 7.2) less the line of Bedroom 4\'s north wall face %.4f' % (fy['hi'], b4['lo']))
D(30, blk2['size'], 'z pair, shell, y 4, x 15.45: %.4f (%s) .. %.4f (%s)' % (blk2['lo'], blk2['hit_lo'][:30], blk2['hi'], blk2['hit_hi'][:30]))
D(31, *sizeof('shell', (11, 4, 25), 'z'))
D(32, gf[2] - ef[2], 'outer faces: front door wall %.4f (x 15.7), garage front %.4f' % (ef[2], gf[2]))
D(33, slab[5] - gf[2], 'slab edge %.4f less the garage front\'s outer face %.4f' % (slab[5], gf[2]))
D(34, None, 'no W / D closet in the kitchen (row 11)', owner=True, note='owner, 5th round')
rear = tree('shell').cast((17.0, 1.0, 6.0), (0, 0, -1))[1][2]
D(35, blk['lo'] - rear, 'rear wall interior face %.4f to the block\'s south face %.4f' % (rear, blk['lo']))
D(36, scf - max(iz), 'ray +z at y 2.95, x 30: island top south edge %.4f, next surface %.4f (%s)' % (max(iz), scf, scn))
D(37, max(iz) - min(iz), 'same ray: island top z %.4f .. %.4f (object box z %.4f .. %.4f)' % (min(iz), max(iz), isl[4], isl[5]))
D(38, *sizeof('shell', (27.3, 7.8, 15), 'z'), note='ray above the sliding door\'s head')
D(39, *sizeof('shell', (22.3, 4, 42), 'z'))
R['dims39'] = rows
H('1. SKA002: the 39 printed dimensions')
T(['No', 'Label', 'Sheet ft', 'Built ft', 'Diff in', 'Verdict', 'How measured'], [[r['no'], r['text'], f3(r['sheet_ft']), f4(r['model_ft']), '-' if r['diff_in'] is None else '%+.2f' % r['diff_in'], r['verdict'] + (' (%s)' % r['note'] if r['note'] else ''), r['how']] for r in rows])
import collections
cnt = collections.Counter(r['verdict'] for r in rows); R['dims39_counts'] = dict(cnt)
md.append('\nCounts: %s' % dict(cnt))

# overall sizes
west = face((-5, 4, 7.5), (1, 0, 0)); east = face((45, 4, 10), (-1, 0, 0)); north = face((1, 4, -5), (0, 0, 1))
gw = lohi('shell', (30, 4, 45), 'x')
ov = [('House width, outside', 39.9167, east[0] - west[0], 'outer faces x %.4f .. %.4f' % (west[0], east[0])),
      ('House depth, Bedroom 3 side', 54.3333, b3f[2] - north[2], 'outer faces z %.4f .. %.4f' % (north[2], b3f[2])),
      ('House depth, garage side', 53.0, gf[2] - north[2], 'outer faces z %.4f .. %.4f' % (north[2], gf[2])),
      ('Garage clear width (A1.1)', 17.5833, gw['size'], 'x pair, shell, y 4, z 45: %.4f .. %.4f' % (gw['lo'], gw['hi']))]
for k, (x, z) in {'primary bedroom': (5.5, 6), 'Bedroom 2': (17, 6), 'living room': (30, 3), 'kitchen': (30, 27), 'hall west leg': (13.3, 15), 'hall east leg': (18, 19), 'Bedroom 4': (5, 33), 'garage (above the house floor datum)': (30, 42), 'foyer north': (17, 35)}.items():
    c = up(x, z); ov.append(('Ceiling, ' + k, 8.0, c[0], 'ray up, shell + openings + exterior shell: %s' % c[1]))
R['overall'] = [{'what': a, 'sheet': b, 'built': c, 'diff_in': (c - b) * 12, 'how': d} for a, b, c, d in ov]
H('1b. Overall sizes and ceilings')
T(['What', 'Sheet ft', 'Built ft', 'Diff in', 'Verdict', 'How'], [[a, f3(b), f4(c), '%+.2f' % ((c - b) * 12), verdict((c - b) * 12), d] for a, b, c, d in ov])

# ============================================================================== 2. doors
SH = {d['id']: d for d in G['doors']}
def shell_opening(axis, c, mid, y=3.4, tr='shell'):
    """Wall opening along the wall's centre line from the middle of the opening."""
    if axis == 'x':
        a = tree(tr).cast((mid, y, c), (-1, 0, 0)); b = tree(tr).cast((mid, y, c), (1, 0, 0)); return (a[1][0] if a else None, b[1][0] if b else None)
    a = tree(tr).cast((c, y, mid), (0, 0, -1)); b = tree(tr).cast((c, y, mid), (0, 0, 1)); return (a[1][2] if a else None, b[1][2] if b else None)
def head_of(axis, c, mid, y0=3.4, tr='shell'):
    o = (mid, y0, c) if axis == 'x' else (c, y0, mid)
    h = tree(tr).cast(o, (0, 1, 0)); g = tree(tr).cast(o, (0, -1, 0))
    return (g[1][1] if g else None, h[1][1] if h else None)
#        sheet id, label, axis, wall centre, mid, prefix of its pieces, kind, owner?, note
DOORS = [
 ('DR01', 'Primary bedroom sliding door', 'x', 0.017, 5.6, r'^Primary slider', 'slide', False, ''),
 ('DR02', 'Living room sliding door', 'x', 0.017, 31.7, r'^Living slider', 'slide', False, ''),
 ('DR03', 'Bedroom 2 entry', 'x', 12.683, 13.39, r'^Bedroom 2 entry door', 'hinged', False, ''),
 ('DR04', 'Primary suite entry (sliding panel)', 'z', 11.517, 14.94, r'^Primary suite entry', 'panel', False, ''),
 ('DR05', 'Walk-in closet pocket door', 'z', 6.5167, 16.9, r'^Primary closet (door|pocket)', 'pocket', False, ''),
 ('DR06', 'Primary bath door', 'x', 21.1, 8.15, r'^Primary bath door', 'hinged', False, ''),
 ('DR07', 'Shared bath door', 'x', 21.1, 13.64, r'^Shared bath door', 'hinged', False, ''),
 ('DR08', 'Bedroom 2 closet sliding doors', 'x', 12.683, 18.8, r'^Bedroom 2 closet', 'bypass', False, ''),
 ('DR09', 'Furnace closet door', 'z', 15.183, 16.18, r'^Furnace closet door', 'hinged', False, ''),
 ('DR10', 'Storage closet door', 'x', 17.351, 20.475, r'^Storage closet door', 'hinged', False, ''),
 ('DR11', 'Bedroom 4 entry', 'z', 15.35, 34.96, r'Bedroom 4 (revised 32 inch entry casing|entry door)', 'hinged', True, 'owner: at the south end of the foyer wall (5th round); wall on the shared bath\'s line (2nd)'),
 ('DR12', 'Bedroom 3 entry', 'z', 15.35, 44.39, r'Bedroom 3 entry (casing|door)', 'hinged', False, 'x of the wall is the owner\'s (2nd round)'),
 ('DR13', 'Bedroom 3 bath door', 'x', 42.517, 6.975, r'^Bedroom 3 bath door', 'hinged', False, ''),
 ('DR14', 'Bedroom 4 closet doors', 'x', 37.1, 12.0, r'Bedroom 4 (bypass closet door|closet door)', 'bypass', True, 'owner: closet 6\'-3" wide (2nd round)'),
 ('DR15', 'Bedroom 3 closet doors', 'x', 42.517, 11.39, r'^Bedroom 3 closet', 'bypass', False, ''),
 ('DR16', 'Front door with sidelights', 'x', 47.6, 18.433, r'^Front door', 'hinged', True, 'owner: centred on the 5\'-9" foyer; unit as wide as the foyer allows'),
 ('DR17', 'House / garage door', 'z', 21.517, 37.83, r'^House / garage door', 'hinged', False, ''),
 ('DR18', 'Garage side door', 'z', 39.517, 36.975, r'^Garage side door', 'hinged', False, ''),
 ('DR19', 'Garage vehicle door', 'x', 52.6, 30.475, r'^ext garage door', 'overhead', False, ''),
 ('DR20', 'Laundry (W / D) closet doors', 'z', 15.35, 30.3, r'^Laundry closet door', 'pair', True, 'owner: laundry closet in Bedroom 4\'s corner (5th round)'),
]
drows = []
for sid, label, axis, c, mid, rx, kind, owner, note in DOORS:
    s = SH[sid]; ai = 0 if axis == 'x' else 4
    yq = 3.4 if sid != 'DR18' else 2.5
    wo = shell_opening(axis, c, mid, yq)
    sill, head = head_of(axis, c, mid, yq)
    jm = [o for o in objs(rx, ['openings', 'zone_exterior']) if re.search(r'jamb|casing|post [WE]$', o['name']) and not re.search('hinge|plate', o['name'])]
    if sid == 'DR16':
        jm = [o for o in jm if re.search('post', o['name'])]
    lo_j = [o['aabb'][ai + 1] for o in jm if (o['aabb'][ai] + o['aabb'][ai + 1]) / 2 < mid]
    hi_j = [o['aabb'][ai] for o in jm if (o['aabb'][ai] + o['aabb'][ai + 1]) / 2 > mid]
    if sid == 'DR19':
        vd = union(objs(r'^ext garage door (section|panel)', ['zone_exterior'])); jb = objs(r'^ext garage door jamb boards$')
        ray = line('all', (mid, 3.0, 52.75), (-1, 0, 0), 9.0); ray2 = line('all', (mid, 3.0, 52.75), (1, 0, 0), 9.0)
        cl = (ray[0][0][0] if ray else None, ray2[0][0][0] if ray2 else None)
        R['vehicle_door_objs'] = {o['name']: [round(v, 4) for v in o['aabb']] for o in objs(r'^ext garage door')}
    else:
        cl = (max(lo_j) if lo_j else None, min(hi_j) if hi_j else None)
    leaf = [o for o in objs(rx, ['openings', 'zone_exterior']) if re.search(r'leaf|sliding panel (front|rear|\(open\))$|bypass closet door \d|glass$', o['name']) and not re.search('hinge|plate|pull|sidelight', o['name'])]
    hinges = [o for o in objs(rx, ['openings']) if re.search(r'hinge( north| south)? \d$', o['name'])]
    hs = None
    if hinges and cl[0] is not None:
        hc = np.mean([(o['aabb'][ai] + o['aabb'][ai + 1]) / 2 for o in hinges])
        hs = ('west' if axis == 'x' else 'north') if abs(hc - cl[0]) < abs(hc - cl[1]) else ('east' if axis == 'x' else 'south')
        if kind == 'pair': hs = 'both jambs (pair)'
    side = None
    if leaf and kind == 'hinged':
        la = union(leaf); pi = 4 if axis == 'x' else 0
        lc = (la[pi] + la[pi + 1]) / 2
        side = ('north' if lc < c else 'south') if axis == 'x' else ('west' if lc < c else 'east')
    sc0, sc1 = s.get('clear_start'), s.get('clear_end')
    ss0, ss1 = s['start'], s['end']
    dr = {'id': sid, 'label': label, 'kind': kind, 'sheet_wall_opening': [ss0, ss1], 'sheet_clear': [sc0, sc1], 'built_wall_opening': wo, 'built_clear': cl, 'sill': sill, 'head': head,
          'hinge_side_built': hs, 'hinge_side_sheet': s.get('hinge_side'), 'swing_built': side, 'swing_sheet': s.get('swings'),
          'leaves': {o['name']: [round(v, 3) for v in o['aabb']] for o in leaf}, 'owner': owner, 'note': note, 'sheet_type': s['type']}
    # verdict: place and width of the clear opening where the sheet has one, else the wall opening
    if sc0 is not None and cl[0] is not None:
        d0, d1 = (cl[0] - sc0) * 12, (cl[1] - sc1) * 12; dw = ((cl[1] - cl[0]) - (sc1 - sc0)) * 12; basis = 'clear'
    else:
        d0, d1 = (wo[0] - ss0) * 12, (wo[1] - ss1) * 12; dw = ((wo[1] - wo[0]) - (ss1 - ss0)) * 12; basis = 'wall opening'
    dr.update(d_start_in=round(d0, 2), d_end_in=round(d1, 2), d_width_in=round(dw, 2), basis=basis)
    worst = max(abs(d0), abs(d1), abs(dw))
    dr['verdict'] = 'owner' if owner else verdict(worst)
    if hs and s.get('hinge_side') and not owner:
        dr['hinge_ok'] = s['hinge_side'].split()[0] == hs.split()[0]
    drows.append(dr)
R['doors'] = drows
H('2. Doors of SKA002 (place, width, type, hinge side)')
T(['Id', 'Door', 'Sheet: wall opening / clear', 'Built: wall opening / clear', 'Diff in (start, end, width; on)', 'Sill..head', 'Type on the sheet -> built', 'Hinge sheet -> built; swing', 'Verdict'],
  [[d['id'], d['label'], '%s..%s / %s..%s' % (f3(d['sheet_wall_opening'][0]), f3(d['sheet_wall_opening'][1]), f3(d['sheet_clear'][0]), f3(d['sheet_clear'][1])),
    '%s..%s / %s..%s' % (f4(d['built_wall_opening'][0]), f4(d['built_wall_opening'][1]), f4(d['built_clear'][0]), f4(d['built_clear'][1])),
    '%+.2f, %+.2f, %+.2f (%s)' % (d['d_start_in'], d['d_end_in'], d['d_width_in'], d['basis']), '%s..%s' % (f3(d['sill']), f3(d['head'])),
    d['sheet_type'][:60] + ' -> ' + d['kind'] + ' (%d leaf / panel objects)' % len(d['leaves']),
    '%s -> %s; %s -> %s' % (d['hinge_side_sheet'], d['hinge_side_built'], d['swing_sheet'], d['swing_built']) if d['hinge_side_sheet'] or d['hinge_side_built'] else '-',
    d['verdict'] + (' (%s)' % d['note'] if d['note'] else '') + ('' if d.get('hinge_ok', True) else ' HINGE SIDE DIFFERS')] for d in drows])

# ============================================================================== 3. windows
SW = {w['id']: w for w in G['windows']}
WINS = [
 ('WN01', 'W02 Bedroom 2 rear', 'x', 0.017, 16.92, 5.0, False, 'height: owner (2\'-0" sill to the ceiling)'),
 ('WN02', 'W15 primary west, north', 'z', 0.017, 2.72, 4.5, False, ''),
 ('WN03', 'W13 primary bath west', 'z', 0.017, 24.5, 5.0, True, 'owner: tall window as set in the 6th round'),
 ('WN04', 'W12 Bedroom 4 west', 'z', 0.017, 32.89, 4.5, False, ''),
 ('WN05', 'W11 Bedroom 3 bath west', 'z', 0.017, 39.81, 5.0, False, 'height: owner (3\'-0" sill, 7\'-6" head)'),
 ('WN06', 'W09 Bedroom 3 front bay', 'x', 53.933, 7.35, 4.5, True, 'owner: three-sided bay glazed to the floor (1st round)'),
 ('WN07', 'W05 living east, north', 'z', 39.517, 3.37, 4.5, False, ''),
 ('WN08', 'W07 living / dining east', 'z', 39.517, 18.57, 4.5, False, ''),
 ('WN09', 'W08 kitchen east (over the sink)', 'z', 39.517, 26.1, 5.0, True, 'owner: three sashes over the sink (3rd round)'),
 ('WN10', 'leftover (E) bath window symbol', 'x', 28.683, 12.64, 4.5, None, 'sheet leftover: no window in the model (Bedroom 4\'s north wall)'),
]
wrows = []
for sid, label, axis, c, mid, y, owner, note in WINS:
    s = SW[sid]
    if owner is None:
        wo = shell_opening(axis, c, mid, y); solid = tree('shell').cast((mid, y, c - 0.5), (0, 0, 1), 1.0)
        wrows.append({'id': sid, 'label': label, 'sheet': [s['start'], s['end']], 'built': None, 'verdict': 'sheet leftover', 'note': note + ('; wall solid there: %s' % (solid[2] if solid else 'NO WALL HIT'))}); continue
    wo = shell_opening(axis, c, mid, y); sill, head = head_of(axis, c, mid, y)
    d0, d1 = (wo[0] - s['start']) * 12, (wo[1] - s['end']) * 12
    wrows.append({'id': sid, 'label': label, 'sheet': [s['start'], s['end']], 'built': wo, 'sill': sill, 'head': head, 'd_start_in': round(d0, 2), 'd_end_in': round(d1, 2),
                  'd_width_in': round(d1 - d0, 2), 'verdict': 'owner' if owner else verdict(max(abs(d0), abs(d1))), 'note': note, 'sashes_sheet': s.get('sashes')})
# model-only windows
for label, axis, c, mid, y in (('W14 primary west, south (owner; not on the sheet)', 'z', 0.017, 10.6, 4.5), ('W17 window over the front door', 'x', 47.6, 18.43, 8.6)):
    wo = shell_opening(axis, c, mid, y); sill, head = head_of(axis, c, mid, y)
    wrows.append({'id': '-', 'label': label, 'sheet': [None, None], 'built': wo, 'sill': sill, 'head': head, 'verdict': 'owner', 'note': 'model only'})
# Bedroom 3 west wall must be solid
solid = [tree('shell').cast((1.5, y, z), (-1, 0, 0)) for y in (3.0, 4.75, 6.5) for z in np.arange(43.0, 53.6, 0.05)]
R['bed3_west_wall'] = {'rays': len(solid), 'x_min': min(h[1][0] for h in solid), 'x_max': max(h[1][0] for h in solid), 'objects': sorted({h[2] for h in solid})}
R['windows'] = wrows
H('3. Windows of SKA002')
T(['Id', 'Window', 'Sheet start..end', 'Built wall opening', 'Diff in (start, end, width)', 'Sill..head', 'Verdict'],
  [[w['id'], w['label'], '%s..%s' % (f3(w['sheet'][0]), f3(w['sheet'][1])), '-' if not w.get('built') else '%s..%s' % (f4(w['built'][0]), f4(w['built'][1])),
    '-' if 'd_start_in' not in w else '%+.2f, %+.2f, %+.2f' % (w['d_start_in'], w['d_end_in'], w['d_width_in']), '-' if 'sill' not in w else '%s..%s' % (f3(w['sill']), f3(w['head'])),
    w['verdict'] + (' (%s)' % w['note'] if w.get('note') else '')] for w in wrows])
md.append('\nBedroom 3 west wall (sheet: solid): %d rays at y 3.0 / 4.75 / 6.5, z 43.0..53.6: inside face x %.4f..%.4f, objects %s' % (R['bed3_west_wall']['rays'], R['bed3_west_wall']['x_min'], R['bed3_west_wall']['x_max'], R['bed3_west_wall']['objects']))

# ============================================================================== 4. skylights
SK = {s['id']: s for s in G['skylights']}
srows = []
def well(name_rx, cx, cz):
    """Clear well at the ceiling: rays up from y 7.9 on a fine grid, free = not stopped below y 8.3."""
    gl = union(objs(name_rx + r'.*glass$', ['openings']))
    lin = objs(name_rx + r'.*lining', ['openings'])
    def free(x, z):
        h = tree('arch').cast((x, 7.6, z), (0, 1, 0)); return h is not None and re.search(name_rx + r'.*(glass|frame)', h[2], re.I) is not None
    def edge(axis, sgn):
        v = cx if axis == 'x' else cz; step = 0.002
        while True:
            v2 = v + sgn * step
            if abs(v2 - (cx if axis == 'x' else cz)) > 4 or not free(v2 if axis == 'x' else cx, cz if axis == 'x' else v2): return v
            v = v2
    x0, x1, z0, z1 = edge('x', -1), edge('x', 1), edge('z', -1), edge('z', 1)
    h = tree('arch').cast((cx, 7.6, cz), (0, 1, 0))
    return [x0, x1, z0, z1], gl, (h[1][1], h[2]) if h else None
for sid, label, rx, cx, cz, owner, note in (('SK1', 'Living room skylight', r'^Living skylight', 35.56, 8.68, False, ''),
                                            ('SK2', 'Kitchen skylight', r'^Kitchen skylight', 36.763, 25.6, 'place', 'place: owner (over the sink, 1st round); size: sheet'),
                                            ('SK3', 'Foyer skylight, north', r'^Foyer skylight 0', 19.85, 33.07, True, 'owner (1st round): on the east slope, 2\'-0" x 3\'-0"'),
                                            ('SK4', 'Foyer skylight, south', r'^Foyer skylight 1', 19.85, 43.47, True, 'owner (1st round)'),
                                            (None, 'Primary bath skylight', r'^Primary bath skylight', 3.2, 22.86, True, 'owner (2nd / 6th round); not on the sheet')):
    w, gl, hit = well(rx, cx, cz)
    s = SK.get(sid)
    row = {'id': sid or '-', 'label': label, 'built_well': [round(v, 4) for v in w], 'built_size': [round(w[1] - w[0], 4), round(w[3] - w[2], 4)], 'glass_box': gl, 'ray_up_from_centre': hit, 'note': note}
    if s:
        row['sheet'] = [s['x0'], s['x1'], s['z0'], s['z1']]; row['sheet_size'] = [s['width_x_ft'], s['depth_z_ft']]
        dsz = max(abs(row['built_size'][0] - s['width_x_ft']), abs(row['built_size'][1] - s['depth_z_ft'])) * 12
        dpl = max(abs(w[i] - row['sheet'][i]) for i in range(4)) * 12
        row['d_size_in'] = round(dsz, 2); row['d_place_in'] = round(dpl, 2)
        row['verdict'] = 'owner' if owner is True else ('size %s, place owner' % verdict(dsz) if owner == 'place' else verdict(max(dsz, dpl)))
    else:
        row['verdict'] = 'owner'
    srows.append(row)
R['skylights'] = srows
H('4. Skylights (clear well at the ceiling, rays up from y 7.6 every 0.002 ft)')
T(['Id', 'Skylight', 'Sheet x0..x1, z0..z1', 'Built well x0..x1, z0..z1', 'Built size', 'Size / place diff in', 'Glass y', 'Verdict'],
  [[r['id'], r['label'], '-' if 'sheet' not in r else '%.3f..%.3f, %.3f..%.3f' % tuple(r['sheet']), '%.3f..%.3f, %.3f..%.3f' % tuple(r['built_well']), '%.3f x %.3f' % tuple(r['built_size']),
    '-' if 'd_size_in' not in r else '%.2f / %.2f' % (r['d_size_in'], r['d_place_in']), '-' if not r['glass_box'] else '%.2f..%.2f' % (r['glass_box'][2], r['glass_box'][3]), r['verdict'] + (' (%s)' % r['note'] if r['note'] else '')] for r in srows])

# ============================================================================== 5. landings, porch, steps, ground, driveway, garage floor
HS = json.load(open(os.path.join(HERE, 'heights_site.json')))
lrows = []
def extent_at(level, tol, fixed, axis, a0, a1, tr='site', step=0.002):
    lo = hi = None
    for v in np.arange(a0, a1, step):
        o = (float(v), 3.0, fixed) if axis == 'x' else (fixed, 3.0, float(v))
        h = tree(tr).cast(o, (0, -1, 0))
        if h and abs(h[1][1] - level) < tol:
            lo = float(v) if lo is None else lo; hi = float(v)
    return (lo, None if hi is None else hi + step)
def add(what, sheet, built, how, owner=False, tol_note=''):
    d = None if (sheet is None or built is None) else (built - sheet) * 12
    lrows.append({'what': what, 'sheet': sheet, 'built': built, 'diff_in': None if d is None else round(d, 2), 'verdict': verdict(d, owner) if sheet is not None else 'no sheet value', 'how': how + tol_note})
for sid, nm, xm, ax0, ax1 in (('LD1', 'LD1 primary bedroom landing', 5.6, 0.0, 12.0), ('LD2', 'LD2 living room landing', 31.7, 22.0, 41.0)):
    s = [l for l in G['landings'] if l['id'] == sid][0]
    top_y, top_n = down(xm, -1.7, 'site', 3.0)
    ex = extent_at(top_y, 0.01, -1.7, 'x', ax0, ax1); ez = extent_at(top_y, 0.01, xm, 'z', -6.0, 0.2)
    add(nm + ': west edge x', s['x0'], ex[0], 'rays down at z -1.7, level %.4f (%s)' % (top_y, top_n)); add(nm + ': east edge x', s['x1'], ex[1], 'same')
    add(nm + ': outer edge z', s['z0'], ez[0], 'rays down at x %.1f' % xm); add(nm + ': edge at the wall z', s['z1'], ez[1], 'same (the platform meets the wall / threshold)')
    add(nm + ': top level', None, top_y, 'ray down at (%.1f, -1.7); spec: about 1 in below the floor' % xm)
    st_y, st_n = down(xm, s['z0'] - 0.3, 'site', 3.0); gr_y, gr_n = down(xm, s['z0'] - 2.5, 'site', 3.0)
    add(nm + ': step top level', None, st_y, 'ray down at (%.1f, %.2f): %s' % (xm, s['z0'] - 0.3, st_n))
    sx = extent_at(st_y, 0.01, s['z0'] - 0.3, 'x', ax0 - 2, ax1 + 2); szz = extent_at(st_y, 0.01, xm, 'z', -7.0, 0.2)
    add(nm + ': step tread (outer edge to platform edge)', None, ez[0] - szz[0], 'step z %.4f .. platform %.4f; step x %.4f .. %.4f' % (szz[0], ez[0], sx[0], sx[1]))
    add(nm + ': riser landing -> step, in', None, (top_y - st_y) * 12, 'spec: equal risers <= 7 3/4 in'); add(nm + ': riser step -> ground, in', None, (st_y - gr_y) * 12, 'ground at (%.1f, %.2f): %.4f (%s)' % (xm, s['z0'] - 2.5, gr_y, gr_n))
    th = union(objs(r'^(Primary|Living) slider sill$' if True else '', ['openings'], box=(ax0, ax1, -0.5, 0.5)))
    add(nm + ': door threshold top above the landing, in', None, (th[3] - top_y) * 12 if th else None, 'sill object top %.4f' % (th[3] if th else float('nan')))
# porch. The set gives no level for the NEW porch slab: A1.3 draws the existing porch, 4 in below the floor (-0.336,
# heights_site.json `porch_floor_existing_ft`), which would leave risers of 7 in and 4 in. The eighth round built the
# slab half way between the front walk and the house floor, two equal risers of 5 1/2 in (the round's spec: "proper
# equal risers at the rear landings and the front entry"). These rows expect that decision.
PORCH_TOP = -(11.0 / 12.0) / 2          # -0.4583: half of A1.3's -0'-11" (the garage floor and the grade at the front)
PORCH_RISER_IN = 5.5
def add_in(what, sheet_in, built_in, how):
    """A row whose values are inches already (add() takes feet and prints the difference in inches)."""
    d = None if (sheet_in is None or built_in is None) else built_in - sheet_in
    lrows.append({'what': what, 'sheet': sheet_in, 'built': built_in, 'diff_in': None if d is None else round(d, 2),
                  'verdict': verdict(d) if sheet_in is not None else 'no sheet value', 'how': how})
ps_top, ps_n = down(18.4, 51.0, 'site', 3.0)
add('Porch slab top', PORCH_TOP, ps_top, 'ray down at (18.4, 51.0): %s; expected: the built decision, half way between the walk and the floor (A1.3\'s existing porch was %.3f)' % (ps_n, HS['A1_3_elevations']['summary']['porch_floor_existing_ft']))
add('Porch slab front edge z', 55.142, slab[5], 'object box of the slab pieces')
wk_y, wk_n = down(18.4, 56.0, 'site', 3.0)
add_in('Porch riser to the walk, in', PORCH_RISER_IN, (ps_top - wk_y) * 12, 'walk at (18.4, 56.0): %.4f (%s); expected: two equal risers of 5 1/2 in' % (wk_y, wk_n))
fl_y, fl_n = down(18.4, 46.5, 'arch', 3.0)
add_in('Porch riser to the house floor, in', PORCH_RISER_IN, (fl_y - ps_top) * 12, 'foyer floor at (18.4, 46.5): %.4f (%s); expected: two equal risers of 5 1/2 in' % (fl_y, fl_n))
fd = union(objs(r'^Front door sill$', ['openings']))
add('Front door sill top above the porch slab, in', None, (fd[3] - ps_top) * 12 if fd else None, 'sill top %.4f' % (fd[3] if fd else float('nan')))
add('Porch between its side walls', None, pw['size'], 'x pair, shell, y 4, z 50.5: %.4f .. %.4f (owner: 5\'-9")' % (pw['lo'], pw['hi']))
# ground
for nm, sheet, pts in (('Ground behind the house', -1.1667, [(5, -8), (20, -12), (35, -8), (15, -1.0)]), ('Ground in front of the house', -0.9167, [(8, 62), (8, 58), (30, 70), (3, 56)])):
    ys = [down(x, z, 'site', 5.0) for x, z in pts]
    add(nm, sheet, float(np.mean([y for y, n in ys])), 'rays down, site only: ' + ', '.join('(%g, %g) %.4f %s' % (x, z, y, n[:22]) for (x, z), (y, n) in zip(pts, ys)))
for z in (5.0, 26.3, 44.0):
    exp = -1.1667 + (z + 0.1917) / 53.0 * 0.25
    for sidex, nm in ((-0.9, 'west'), (40.0, 'east')):
        y, n = down(sidex, z, 'site', 5.0)
        add('Ground beside the house, %s side, z %g' % (nm, z), exp, y, 'ray down at x %g: %s (pebbles lie 0.03 above the ground line; the side pavers stand 0.09 above it); sheet = straight line -1.167 (rear) .. -0.917 (garage front)' % (sidex, n))
y, n = down(30.5, 78.0, 'site', 5.0); add('Sidewalk top', None, y, n)
# driveway
dv_y, dv_n = down(30.5, 60.0, 'site', 5.0)
dx = extent_at(dv_y, 0.012, 60.0, 'x', 19.0, 42.0)
sd = HS.get('site', {}) if isinstance(HS, dict) else {}
add('Driveway west edge x', 21.65, dx[0], 'rays down at z 60, level %.4f (%s)' % (dv_y, dv_n)); add('Driveway east edge x', 39.73, dx[1], 'same')
add('Driveway width', 18.0833, dx[1] - dx[0], 'sheet 18\'-1" (scaled from SKA001: 18\'-0 15/16")')
for z in (52.6, 53.2, 60.0, 70.0, 76.0):
    y, n = down(30.5, z, 'all', 3.0); add('Driveway / slab level at z %g' % z, -0.9167, y, 'ray down at x 30.5 from y 3: %s' % n)
# garage floor
for x, z in ((30, 42), (24, 34.5), (38, 50), (36, 36)):
    y, n = down(x, z, 'nosite', 3.0); add('Garage floor at (%g, %g)' % (x, z), -0.9167, y, n)
st = union(objs(r'^Garage step at the house door$'))
if st:
    for k, i, sh in (('x0', 0, 21.725), ('x1', 1, 22.725), ('z0', 4, 35.983), ('z1', 5, 39.649)):
        add('Garage step ST1 ' + k, sh, st[i], 'object box')
    add('Garage step top', None, st[3], 'object box; risers %.2f in (house floor -> step) and %.2f in (step -> garage floor)' % ((0 - st[3]) * 12, (st[3] + 0.9167) * 12))
gc = up(30, 42, 'arch', 3.0); gfl = down(30, 42, 'nosite', 3.0)
add('Garage floor to ceiling', 8.9167, gc[0] - gfl[0], 'A1.3: 8\'-11"')
wh = union(objs(r'^water heater tank$'))
if wh:
    add('Water heater: centre x', 38.022, (wh[0] + wh[1]) / 2, 'box of `water heater tank`'); add('Water heater: centre z', 32.913, (wh[4] + wh[5]) / 2, 'same')
    add('Water heater: diameter', 1.6667, wh[1] - wh[0], 'same (sheet: 1\'-8" circle)')
    add('Water heater: tank top above the garage floor', None, wh[3] + 0.9167, 'tank y %.3f..%.3f on an 18 in stand' % (wh[2], wh[3]))
old = objs(r'tankless|^gar (water )?heater|wall.hung.*heater')
add('Old wall-hung water heater (objects left)', 0.0, float(len(old)), ', '.join(o['name'] for o in old) or 'none')
for nm, x, z in (('primary bedroom', 5.5, 6.0), ('Bedroom 2', 17.0, 6.0), ('living room', 30.0, 12.0), ('kitchen aisle', 35.5, 23.0), ('hall', 13.3, 16.0), ('foyer', 18.4, 38.0), ('Bedroom 4', 5.0, 33.0), ('Bedroom 3', 5.0, 48.0)):
    y, n = down(x, z, 'arch', 3.0); add('House floor, ' + nm, 0.0, y, 'ray down on shell / openings: %s' % n)
R['water_heater_objs'] = {o['name']: [round(v, 3) for v in o['aabb']] for o in objs(r'water heater|heater', ['zone_hall_entry_garage', 'shell', 'openings'])}
R['levels'] = lrows
H('5. Landings, porch, ground, driveway, garage floor')
T(['What', 'Sheet / spec', 'Built', 'Diff in', 'Verdict', 'How'], [[r['what'], f4(r['sheet']), f4(r['built']), '-' if r['diff_in'] is None else '%+.2f' % r['diff_in'], r['verdict'], r['how']] for r in lrows])

# ============================================================================== 6. roof
rrows = []
def radd(what, sheet, built, how, owner=False):
    d = None if (sheet is None or built is None) else (built - sheet) * 12
    rrows.append({'what': what, 'sheet': sheet, 'built': built, 'diff_in': None if d is None else round(d, 2), 'verdict': verdict(d, owner) if sheet is not None else 'no sheet value', 'how': how})
GROUPS['roofplane'] = lambda o: bool(re.search(r'^v7 roof plane', o['name']))
GROUPS['roof'] = lambda o: bool(re.search(r'^v7 roof', o['name']))
R['roof_objects'] = sorted(o['name'] for o in META if re.search('roof', o['name'], re.I) and top(o, 'exterior_shell', 'shell'))
def pitch(nm, p1, p2):
    a = tree('roofplane').cast((p1[0], 40, p1[1]), (0, -1, 0)); b = tree('roofplane').cast((p2[0], 40, p2[1]), (0, -1, 0))
    if not a or not b: radd('Pitch, ' + nm, 5.0, None, 'no hit'); return
    run = math.hypot(p1[0] - p2[0], p1[1] - p2[1]); rise = abs(a[1][1] - b[1][1])
    rrows.append({'what': 'Pitch, ' + nm + ' (in 12)', 'sheet': 5.0, 'built': 12 * rise / run, 'diff_in': None, 'verdict': 'match' if abs(12 * rise / run - 5.0) < 0.02 else 'DIFFERS',
                  'how': 'two rays down on %s / %s: y %.4f -> %.4f over %.2f ft' % (a[2], b[2], a[1][1], b[1][1], run)})
pitch('main north plane', (20, 2.0), (20, 10.0)); pitch('main west plane', (1.0, 8), (6.0, 8)); pitch('main east plane', (39.0, 8), (34.0, 8))
pitch('main south plane (over the hall)', (18, 15.5), (18, 18.0)); pitch('main south plane (over the primary bath)', (10, 20.0), (10, 22.5))
pitch('garage east plane', (39.0, 45), (32.0, 45)); pitch('garage west plane', (23.5, 45), (29.5, 45))
pitch('wing west plane', (1.0, 40), (6.0, 40)); pitch('wing east plane', (9.0, 40), (13.5, 40))
pitch('entry west plane', (14.6, 40), (17.9, 40)); pitch('entry east plane', (22.3, 37.5), (18.95, 37.5)); pitch('entry east plane over the porch', (22.3, 52), (18.95, 52))
pitch('old entry plane WB (faces west)', (23.0, 21.6), (24.0, 21.6)); pitch('old entry plane SB (faces south)', (26.0, 22.0), (26.0, 25.0))
def ridge(nm, fixed, axis, a0, a1, sheet_y, sheet_pos, owner_pos=False):
    best = (-1e9, None)
    for v in np.arange(a0, a1, 0.005):
        o = (float(v), 40, fixed) if axis == 'x' else (fixed, 40, float(v))
        h = tree('roofplane').cast(o, (0, -1, 0)); hc = tree('roof').cast(o, (0, -1, 0))
        if h and h[1][1] > best[0]: best = (h[1][1], float(v), hc[1][1] if hc else None)
    radd('%s: planes meet at (height)' % nm, sheet_y, best[0], 'highest ray on the plane slabs along %s at %s %g: at %.3f; cap top %.4f' % (axis, 'z' if axis == 'x' else 'x', fixed, best[1], best[2]))
    radd('%s: plan position' % nm, sheet_pos, best[1], 'same scan', owner=owner_pos)
    return best
ridge('Main ridge', 20.0, 'z', 13.0, 16.0, 14.5833, 14.348)
ridge('Garage ridge', 42.0, 'x', 29.0, 32.0, 12.375, 30.516)
w1 = ridge('Wing ridge at z 30', 30.0, 'x', 5.0, 10.0, None, 7.059, True); w2 = ridge('Wing ridge at z 50', 50.0, 'x', 5.0, 10.0, None, 7.059, True)
e1 = ridge('Entry ridge at z 24', 24.0, 'x', 16.0, 21.0, None, 17.808, True); e2 = ridge('Entry ridge at z 40', 40.0, 'x', 16.0, 21.0, None, 17.808, True); e3 = ridge('Entry ridge at z 55.5', 55.5, 'x', 16.0, 21.0, None, 17.808, True)
rrows.append({'what': 'Entry ridge level', 'sheet': 0.0, 'built': max(e1[0], e2[0], e3[0]) - min(e1[0], e2[0], e3[0]), 'diff_in': round((max(e1[0], e2[0], e3[0]) - min(e1[0], e2[0], e3[0])) * 12, 2), 'verdict': verdict((max(e1[0], e2[0], e3[0]) - min(e1[0], e2[0], e3[0])) * 12), 'how': 'fall between z 24, 40 and 55.5 (spec: level)'})
rrows.append({'what': 'Wing ridge level', 'sheet': 0.0, 'built': abs(w1[0] - w2[0]), 'diff_in': round(abs(w1[0] - w2[0]) * 12, 2), 'verdict': verdict(abs(w1[0] - w2[0]) * 12), 'how': 'fall between z 30 and 50'})
def roof_edge(nm, fixed, axis, a0, a1, wallface, sgn):
    lo = hi = None
    for v in np.arange(a0, a1, 0.002):
        o = (float(v), 40, fixed) if axis == 'x' else (fixed, 40, float(v))
        h = tree('roof').cast(o, (0, -1, 0))
        if h:
            lo = float(v) if lo is None else lo; hi = float(v)
    e = lo if sgn < 0 else hi + 0.002
    radd('Eave overhang, ' + nm, 1.0, abs(e - wallface), 'roof edge at %.4f (rays down on the roof pieces), wall outer face %.4f' % (e, wallface))
    return e
ew = roof_edge('west at z 8', 8.0, 'x', -2.0, 0.5, west[0], -1); roof_edge('west at z 45', 45.0, 'x', -2.0, 0.5, face((-5, 4, 45), (1, 0, 0))[0], -1)
roof_edge('east at z 8', 8.0, 'x', 39.0, 41.5, east[0], 1); roof_edge('east at z 45', 45.0, 'x', 39.0, 41.5, face((45, 4, 45), (-1, 0, 0))[0], 1)
roof_edge('rear at x 5', 5.0, 'z', -2.0, 0.5, north[2], -1); roof_edge('rear at x 30', 30.0, 'z', -2.0, 0.5, north[2], -1)
gk = roof_edge('garage gable rake beyond the garage front (z)', 35.0, 'z', 52.0, 54.5, gf[2], 1); roof_edge('wing gable rake beyond Bedroom 3\'s front (z)', 2.0, 'z', 53.5, 56.0, b3f[2], 1)
pe = roof_edge('entry gable beyond the porch slab (z)', 18.0, 'z', 54.5, 57.0, slab[5], 1)
# fascia
for nm, o, d in (('west eave at z 8', (-3.0, 0, 8.0), (1, 0, 0)), ('rear eave at x 30', (30.0, 0, -3.0), (0, 0, 1)), ('east eave at z 8', (43.0, 0, 8.0), (-1, 0, 0))):
    ys = [y for y in np.arange(7.0, 9.0, 0.002) if tree('roof').cast((o[0], float(y), o[2]), d, 2.0) is not None and abs((tree('roof').cast((o[0], float(y), o[2]), d, 2.0)[1][0 if d[0] else 2]) - (o[0] + d[0] * 1.8085 if d[0] else o[2] + d[2] * 1.8085)) < 0.03]
    if ys:
        radd('Fascia top, ' + nm, 8.122, max(ys) + 0.002, 'horizontal rays on the roof pieces that stop on the fascia face'); radd('Fascia bottom, ' + nm, 7.581, min(ys), 'same')
for nm, x, z in (('over the west wall\'s outer face', west[0], 8.0), ('over the rear wall\'s outer face', 30.0, north[2]), ('over the east wall\'s outer face', east[0], 8.0)):
    h = tree('roofplane').cast((x, 40, z), (0, -1, 0)); radd('Roof surface ' + nm, 8.539, h[1][1] if h else None, 'ray down at (%.4f, %.4f)' % (x, z))
# tie beam, piers
for rx in (r'^v7 roof porch beam', r'^v7 roof porch king post', r'^ext porch piers', r'^v7 roof porch soffit'):
    u = union(objs(rx)); R['box ' + rx] = u
R['roof'] = rrows
H('6. Roof')
T(['What', 'Sheet', 'Built', 'Diff in', 'Verdict', 'How'], [[r['what'], f4(r['sheet']), f4(r['built']), '-' if r['diff_in'] is None else '%+.2f' % r['diff_in'], r['verdict'], r['how']] for r in rrows])

# ============================================================================== 7. kitchen
krows = []
def kadd(what, sheet, built, how, owner=False):
    d = None if (sheet is None or built is None) else (built - sheet) * 12
    krows.append({'what': what, 'sheet': sheet, 'built': built, 'diff_in': None if d is None else round(d, 2), 'verdict': verdict(d, owner) if sheet is not None else 'no sheet value', 'how': how})
KT = {k['id']: k for k in G['kitchen']}
for k, i in (('x0', 0), ('x1', 1), ('z0', 4), ('z1', 5)):
    kadd('Island worktop ' + k, KT['KT01'][k], isl[i], 'box of `kd island top`')
kadd('Island worktop top', 3.0, isl[3], 'usual 36 in')
sface = tree('shell').cast((30.0, 5.5, 29.5), (0, 0, 1)); efc = tree('shell').cast((38.0, 5.5, 23.0), (1, 0, 0))
kadd('South counter front (z)', KT['KT03']['z0'], scf, 'ray, row 36'); kadd('South counter depth', 2.0, R['front_faces'] and (tree('shell').cast((28.5, 1.0, 29.5), (0, 0, 1))[1][2] - scf), 'worktop front to the wall\'s face (shell, ray at x 28.5, y 1.0)')
kadd('East counter front (x)', KT['KT02']['x0'], ecf, 'ray, row 8'); kadd('East counter depth', 2.0, tree('shell').cast((38.0, 1.0, 22.0), (1, 0, 0))[1][0] - ecf, 'worktop front to the wall\'s face (shell, ray at z 22, y 1.0)')
ke = line('int', (38.3, 2.95, 19.0), (0, 0, 1), 4.0); R['east_run_north_end_line'] = [[round(p[2], 4), n] for p, n in ke]
kn = [p[2] for p, n in ke if re.search(r'worktop|counter|marble|kd ', n, re.I) and p[2] > 20.5]
kadd('East counter north end (z)', KT['KT02']['z0'], min(kn) if kn else None, 'ray +z at x 38.3, y 2.95')
tb = union(objs(r'^kd dining table top|^kd dining.*table.*top', ['zone_kitchen_dining'])); R['dining_table_top'] = tb
R['dining_objs'] = sorted({re.sub(r'[\d.]+$', '#', o['name']) for o in objs(r'^kd dining')})[:60]
for nm, rx in (('Refrigerator', r'refrigerator|fridge'), ('Cooktop', r'cooktop|hob'), ('Sink', r'^kd sink|sink (bowl|apron)'), ('Dining table', r'^kd dining table'), ('Dining chairs', r'^kd dining chair'), ('Island pendants', r'pendant'), ('Dining lantern', r'lantern')):
    u = union(objs(rx, ['zone_kitchen_dining'])); R['box ' + nm] = u
    if u: krows.append({'what': nm + ' (box x0, x1, y0, y1, z0, z1)', 'sheet': None, 'built': None, 'diff_in': None, 'verdict': 'owner / no sheet value', 'how': ', '.join('%.3f' % v for v in u)})
R['kitchen'] = krows
H('7. Kitchen')
T(['What', 'Sheet', 'Built', 'Diff in', 'Verdict', 'How'], [[r['what'], f4(r['sheet']), f4(r['built']), '-' if r['diff_in'] is None else '%+.2f' % r['diff_in'], r['verdict'], r['how']] for r in krows])

json.dump(R, open(OUT + '.json', 'w'), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating,)) else str(o))
open(OUT + '.md', 'w').write('\n'.join(md) + '\n')
print('\n'.join(md))
