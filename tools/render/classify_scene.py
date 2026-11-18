#!/usr/bin/env python3
"""Scene audit for 1095 W McKinley tour: room assignment + role classification.
Writes scene_classification.json and room_inventory.json next to this script."""
import json, math, re, os, collections, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.join(HERE, 'data', 'scene.json')
s = json.load(open(SCENE))
O = s['objects']

# ---------------------------------------------------------------- geometry
def footprint(o):
    """World-space rotated footprint corners (x,z) and AABB, using renderer transform:
    world = p + (a*c + d*sin, b, -a*sin + d*c) with (a,b,d)=unit_vertex*s, c=cos(rot), sin=sin(rot)."""
    r = o.get('rot') or 0
    c, sn = math.cos(r), math.sin(r)
    hx, hz = o['s'][0] / 2, o['s'][2] / 2
    pts = []
    for a, d in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)):
        pts.append((o['p'][0] + a * c + d * sn, o['p'][2] - a * sn + d * c))
    return pts

def aabb(o):
    r = o.get('rot') or 0
    c, sn = abs(math.cos(r)), abs(math.sin(r))
    hx = (o['s'][0] * c + o['s'][2] * sn) / 2
    hz = (o['s'][0] * sn + o['s'][2] * c) / 2
    return [o['p'][0] - hx, o['p'][0] + hx, o['p'][1] - o['s'][1] / 2, o['p'][1] + o['s'][1] / 2,
            o['p'][2] - hz, o['p'][2] + hz]

# ---------------------------------------------------------------- rooms
# (key, tour nodes, x0, x1, z0, z1); first match wins. Feet. x=west->east, z=rear(north)->front(south).
# Audit rooms (M01..M12) use their exact clear bounds; others derived from wall objects.
ROOMS = [
    ('suite3_bath',      ['A3'],                 0.225, 7.725, 37.8317, 42.8317, 'audit M09'),
    ('suite3_wic',       ['C3'],                 8.085, 13.8917, 40.1917, 42.8317, 'audit M10'),
    ('bed4_closet',      ['B4'],                 8.085, 13.8917, 37.8317, 39.8317, 'audit M12'),
    ('bed3',             ['B3', 'T4', 'T6'],     0.225, 13.8917, 43.1917, 53.8317, 'audit M08'),
    ('bed3_bay',         ['B3'],                 3.04, 11.04, 53.8317, 56.30, 'walls 4137-4202'),
    ('bed4',             ['B4'],                 0.225, 13.8917, 29.6383, 37.4717, 'audit M07'),
    ('front_hall',       ['E0', 'H1', 'GA'],     14.2517, 20.4647, 29.6383, 46.7217, 'audit M11'),
    ('ensuite',          ['A0'],                 0.225, 10.3917, 21.2783, 29.2783, 'audit M03'),
    ('shared_bath',      ['A1'],                 10.7517, 16.0017, 21.2783, 29.2783, 'audit M04'),
    ('primary_dressing', ['S0', 'C0', 'P1'],     0.225, 11.8917, 15.5017, 20.9183, 'audit M05'),
    ('primary',          ['P0', 'P1'],           0.225, 11.8917, 0.225, 15.1417, 'audit M01'),
    ('bed2',             ['B2', 'T2'],           12.2517, 22.9183, 0.225, 15.1417, 'audit M02 + entry alcove/closet'),
    ('kitchen',          ['K0'],                 22.5, 40.61, 20.8, 31.41, 'walls; island/cabinet extents'),
    ('dining',           ['D0'],                 23.28, 40.61, 17.0, 20.8, 'open area between living and kitchen'),
    ('living',           ['L0', 'L1', 'L2'],     23.28, 40.61, 0.225, 17.0, 'walls 1797-1823/1835/1855'),
    ('common_hall',      ['H2', 'H3', 'T1', 'T3'], 12.2517, 23.28, 15.14, 31.59, 'walls; open to dining/kitchen'),
    ('garage',           ['G0', 'GA'],           20.91, 40.61, 31.77, 50.83, 'walls 1882/1896/1897/3312'),
    ('porch',            ['E0'],                 14.07, 20.69, 47.08, 51.30, 'recessed front porch'),
]
HOUSE = [(0, 40.8367, 0, 31.5909), (0, 20.69, 31.59, 46.9), (0, 14.07, 43.9, 54.06), (20.69, 40.84, 31.59, 51.06),
         (3.04, 11.04, 54.06, 56.06), (14.07, 20.69, 46.9, 47.1)]

def room_at(x, z):
    for k, nodes, x0, x1, z0, z1, _ in ROOMS:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return k
    return None

def in_house(x, z, tol=0.0):
    return any(x0 - tol <= x <= x1 + tol and z0 - tol <= z <= z1 + tol for x0, x1, z0, z1 in HOUSE)

def rooms_overlapped(b, min_area=0.02):
    out = []
    for k, nodes, x0, x1, z0, z1, _ in ROOMS:
        w = min(b[1], x1) - max(b[0], x0); d = min(b[5], z1) - max(b[4], z0)
        if w > 0 and d > 0 and w * d >= min_area:
            out.append(k)
    return out

def nearest_room(x, z, maxd=0.8):
    best, bd = None, 1e9
    for k, nodes, x0, x1, z0, z1, _ in ROOMS:
        dx = max(x0 - x, 0, x - x1); dz = max(z0 - z, 0, z - z1)
        d = math.hypot(dx, dz)
        if d < bd: best, bd = k, d
    return best if bd <= maxd else None

# ---------------------------------------------------------------- role rules
R = lambda pat: re.compile(pat, re.I)
FIXTURE_FURN = R(r'kitchen|cabinet|worktop|refrigerator|hob|hood|sink|island(?! stool)|vanity|basin|\bWC\b|toilet|tub|fireplace|mantel|hearth|quartz|closet sliding panels')
DOOR_HW = R(r'hinge|lever|rosette|\brose\b|latch|door handle')
CAB_FACE = R(r'raised door|framed drawer|raised-panel door|Island framed|Island cabinet door|Island turned|Island square|Island traditional plinth|vanity .*drawer|vanity drawer|drawer joint|stepped crown|Hood raised molding|range hood cornice|Refrigerator|closet central seam|Closet recessed pull|closet recessed pull|hanging rail|Range backsplash|Kitchen antique brass pull|Sink run brass pull|Island brass drawer pull|dressing .*pull')
PLUMB = R(r'faucet|\btap\b|tap stem|tap spout|spout|flush|WC seat|toilet rim|toilet opening|basin inset|basin interior|recessed vanity basin|shower drain|linear drain|rain head|rain arm|mixer plate|shower shelf|sliding rail|shower door handle|towel rail|shower .*tile|tub apron|Tub tap|Hob burner|outlet')
MIRROR_FRAME = R(r'mirror frame|mirror rim')
FURN_PART = R(r'bed leg|stool leg|desk .*leg|desk leg|sofa .*piping|drawer reveal|drawer handle|Primary drawer|Bedroom \d drawer')
BEDDING = R(r'coverlet|duvet|pillow|linen garment|throw')
RUG = R(r'\brug\b')
ART = R(r'artwork|\bart\b')
PLANT = R(r'plant|leaf|olive|eucalyptus|herbs|stem')
TABLEWARE = R(r'vase|cup|jar|bowl|lemon|book|notebook|coaster|cutting board|soap|bottle|towel|shampoo|log|niche bottle')
CURTAIN = R(r'curtain')

def classify(i, o):
    g, n = o['group'], o['name']
    detail = ''
    if g == 'landscape':
        role = 'landscape'
        detail = 'fence' if re.search(r'fence', n, re.I) else ('ground' if re.search(r'ground|lawn|paving|path|driveway|stepping|bed$|gravel', n, re.I) else 'planting')
    elif g == 'roof':
        role, detail = 'exterior', ('roof_cap' if 'ridge' in n.lower() else 'roof_flashing' if 'flashing' in n.lower() else 'roof_plane')
    elif g == 'facade':
        if re.search(r'garage (raised door panel|high glazed|glazed light)|garage door face', n, re.I):
            role, detail = 'exterior', 'garage_door_face'
        elif 'fascia' in n.lower():
            role, detail = 'exterior', 'fascia'
        elif 'bargeboard' in n.lower() or 'cornice' in n.lower():
            role, detail = 'exterior', 'exterior_trim'
        else:
            role, detail = 'exterior', 'stucco_skin'
    elif g == 'base':
        role, detail = 'shell', 'foundation'
    elif g == 'walls':
        role, detail = 'shell', ('wall_header' if re.search(r'header|lintel|band', n, re.I) else 'gable_infill' if 'gable' in n.lower() else 'wall')
    elif g == 'ceiling':
        if 'pale sky' in n.lower():
            role, detail = 'opening', 'fake_sky_emissive (replace with real sky in path tracer)'
        elif 'skylight' in n.lower() and ('shaft' in n.lower() or 'frame' in n.lower()):
            role, detail = 'opening', 'skylight_shaft' if 'shaft' in n.lower() else 'skylight_frame'
        else:
            role, detail = 'shell', 'ceiling'
    elif g == 'floor':
        if re.search(r'shower tray', n, re.I):
            role, detail = 'fixture', 'shower_tray'
        elif re.search(r'grain|grout', n, re.I):
            role, detail = 'shell', 'floor_line_detail (bake into texture)'
        elif re.search(r'plank|board', n, re.I):
            role, detail = 'shell', 'floor_plank (bake into texture)'
        else:
            role, detail = 'shell', 'floor_slab'
    elif g == 'windows':
        role, detail = 'opening', 'window_frame'
    elif g == 'glass':
        if 'shower' in n.lower():
            role, detail = 'fixture', 'shower_glass'
        elif 'garden door' in n.lower():
            role, detail = 'opening', 'door_glass'
        else:
            role, detail = 'opening', 'window_glass'
    elif g in ('door', 'garageDoor'):
        role, detail = 'opening', 'door_leaf' if g == 'door' else 'garage_door'
    elif g == 'mirror':
        role, detail = 'fixture', 'mirror'
    elif g == 'builtins':
        role, detail = 'fixture', 'builtin_storage'
    elif g == 'lighting':
        if re.search(r'lamp shade|floor lamp|lamp warm lower', n, re.I):
            role, detail = 'decor', 'lamp'
        else:
            role, detail = 'fixture', 'light_fixture'
    elif g == 'trim':
        if re.search(r'skirting|baseboard', n, re.I):
            role, detail = 'shell', 'baseboard'
        elif re.search(r'niche bottle', n, re.I):
            role, detail = 'decor', 'tableware'
        elif re.search(r'shower|wet wall|grout|niche|rain (arm|head)', n, re.I):
            role, detail = 'fixture', 'shower_surround'
        else:
            role, detail = 'opening', 'casing'
    elif g == 'furniture':
        if FIXTURE_FURN.search(n):
            role, detail = 'fixture', ('kitchen' if re.search(r'kitchen|cabinet|worktop|refrigerator|hob|hood|sink|island', n, re.I) else
                                       'fireplace' if re.search(r'fireplace|mantel|hearth', n, re.I) else
                                       'closet_door' if 'sliding panels' in n else 'bath')
        else:
            role = 'furniture'
            detail = ('bed' if re.search(r'bed frame|mattress|sheet|headboard|duvet|pillow', n, re.I) else
                      'seating' if re.search(r'sofa|chair (base|cushion|back)|stool', n, re.I) else
                      'table' if re.search(r'table|desk|nightstand', n, re.I) else 'other')
    elif g == 'decor':
        if DOOR_HW.search(n) and 'shower' not in n.lower():
            role, detail = 'opening', 'door_hardware'
        elif CAB_FACE.search(n):
            role, detail = 'fixture', 'cabinet_face (restyle)'
        elif PLUMB.search(n) or 'shower' in n.lower() or 'seat dark inset' in n:
            role, detail = 'fixture', 'plumbing_or_appliance_detail'
        elif MIRROR_FRAME.search(n):
            role, detail = 'fixture', 'mirror_frame'
        elif 'mortar' in n.lower():
            role, detail = 'fixture', 'fireplace'
        elif FURN_PART.search(n):
            role, detail = 'furniture', 'furniture_part'
        elif CURTAIN.search(n):
            role, detail = 'decor', 'curtain'
        elif RUG.search(n):
            role, detail = 'decor', 'rug'
        elif BEDDING.search(n):
            role, detail = 'decor', 'bedding'
        elif ART.search(n):
            role, detail = 'decor', 'art'
        elif re.search(r'lamp', n, re.I):
            role, detail = 'decor', 'lamp'
        elif TABLEWARE.search(n) and not re.search(r'stem|leaf', n, re.I):
            role, detail = 'decor', 'accessory'
        elif PLANT.search(n):
            role, detail = 'decor', 'plant'
        else:
            role, detail = 'decor', 'other'
    else:
        role, detail = 'decor', 'unknown_group'
    return role, detail

# ---------------------------------------------------------------- run
out = {}
role_counts = collections.Counter()
for i, o in enumerate(O):
    role, detail = classify(i, o)
    b = aabb(o)
    cx, cz = o['p'][0], o['p'][2]
    if role in ('landscape',):
        room = 'exterior'
    elif o['group'] in ('roof', 'facade'):
        room = 'exterior'
    else:
        room = room_at(cx, cz) or nearest_room(cx, cz) or ('exterior' if not in_house(cx, cz, 0.3) else 'unassigned')
    ov = rooms_overlapped(b) if role in ('shell', 'opening', 'exterior') and o['group'] not in ('landscape',) else []
    keep = {'shell': 'exact', 'opening': 'exact', 'exterior': 'exact', 'fixture': 'footprint',
            'furniture': 'replaceable', 'decor': 'replaceable', 'landscape': 'replaceable'}[role]
    if role == 'exterior' and detail == 'garage_door_face': keep = 'restyle'
    if detail.startswith('floor_line') or detail.startswith('floor_plank'): keep = 'texture'
    if detail.startswith('cabinet_face'): keep = 'restyle'
    if detail.startswith('fake_sky'): keep = 'remove'
    rec = {'room': room, 'role': role, 'group': o['group'], 'name': o['name'], 'detail': detail, 'keep': keep,
           'shape': o['shape'], 'aabb_ft': [round(v, 4) for v in b]}
    if ov and (len(ov) > 1 or ov[0] != room):
        rec['rooms_touched'] = ov
    out[str(i)] = rec
    role_counts[role] += 1

meta = {
    '_about': 'Object index -> classification. Index == position in SCENE.objects == node index in the embedded GLB.',
    'roles': {
        'shell': 'walls, foundation, floors, ceilings, baseboards: keep geometry exactly (plank/grain strips may be replaced by a textured slab, keep=texture)',
        'opening': 'windows, glass, doors, casings, skylight shaft/frame, door hardware: keep exactly (hardware may be restyled)',
        'fixture': 'kitchen cabinets/island/appliances, vanities, WCs, tub, showers, built-in wardrobes, fireplace, light fixtures, mirrors: keep footprint/position; restyle allowed',
        'furniture': 'movable furniture: replaceable',
        'decor': 'rugs, bedding, art, plants, accessories, curtains, lamps: replaceable',
        'landscape': 'illustrative garden, fences, paving: replaceable',
        'exterior': 'roof planes, ridge caps, flashing, fascia, stucco skin, gables: keep exactly (garage door face panels restyle)'},
    'keep_values': {'exact': 'preserve geometry', 'footprint': 'preserve position and outer dimensions; materials/details may change',
                    'restyle': 'geometry slot may be restyled', 'texture': 'may be collapsed into a texture on the floor slab',
                    'replaceable': 'free to replace', 'remove': 'remove for physically based rendering'},
    'rooms': {k: {'nodes': nodes, 'bounds_ft_x0x1z0z1': [x0, x1, z0, z1], 'source': src} for k, nodes, x0, x1, z0, z1, src in ROOMS},
    'role_counts': dict(role_counts),
}
json.dump({'meta': meta, 'objects': out}, open(os.path.join(HERE, 'data', 'scene_classification.json'), 'w'), indent=1, ensure_ascii=False)

# per-room inventory
inv = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for i, r in out.items():
    inv[r['room']][r['role']][r['name']] += 1
json.dump({k: {rk: dict(c) for rk, c in v.items()} for k, v in inv.items()},
          open(os.path.join(HERE, 'data', 'room_inventory.json'), 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    print(role_counts)
    print(collections.Counter(r['room'] for r in out.values()))
    print(collections.Counter((r['role'], r['keep']) for r in out.values()))
    cr = collections.Counter((r['role'], r['room']) for r in out.values())
    for k in sorted(cr): print(k, cr[k])
