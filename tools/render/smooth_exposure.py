#!/usr/bin/env python3
"""Smooth the per-stop exposure and white balance along the tour graph -> a pins file for render_panos.py.

Why: every sweep is exposed and white-balanced on its own (render_panos.py probe), which is right for a
single 360 and wrong for a walk: the viewer cross-fades between linked sweeps, and neighbours a few feet
apart differed by up to 1.3 stops and 1900 K. This script relaxes the probe values along the graph:

  * linked sweeps end up at most about --max-ev stops, --max-kelvin K and --max-tint apart;
  * links inside one room are pulled together more strongly (x --room-weight) than links across a doorway,
    so a room keeps one look and the change happens at its doors;
  * no value moves further from its probe than --move-ev stops / --move-kelvin K / --move-tint. That limit
    wins: a link the limits cannot close stays open and is marked '!' in the table.

Per channel (exposure, kelvin, tint), with x in units of the link limit, p the probe value:

    minimise   sum_i a_i (x_i - p_i)^2  +  smooth * sum_links w (x_i - x_j)^2
                                        +  rho * sum_links max(0, |x_i - x_j| - 1)^2        (rho -> large)
    subject to |x_i - p_i| <= move_i

a_i = 0 (and no move limit) for a white balance that was not measured (wb_source 'default': too little
white paint in view), so such a sweep takes its neighbours' balance. w = --room-weight inside a room, 1
across a doorway, 0 (and no limit) between an indoor and an outdoor sweep. Exact coordinate descent; the
problem is convex, so the result does not depend on the order of the sweeps.

Usage (plain python3, no Blender):
  python3 tools/render/smooth_exposure.py --meta <probe dir>/render_meta.json --out <pins.json>
      [--scene tools/render/data/scene.json] [--max-ev 0.3] [--max-kelvin 300] [--max-tint 6]
      [--move-ev 0.7] [--move-kelvin 1200] [--move-tint 12] [--room-weight 4] [--smooth 0.25]
      [--fix ID,ID] [--top 14]

Output: {id: {"ev": stops, "kelvin": K, "tint": t}} for every sweep of the tour that has a probe entry,
and a before/after table of the largest link differences on stdout.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def tour_graph(scene):
    """(nodes {id: node}, links [(a, b)]) from scene['tour']: `edges` (or `undirected_edges`), else the
    per-node `links` / `neighbors` lists."""
    tour = scene['tour']
    nodes = {n['id']: n for n in tour['nodes']}
    pairs = tour.get('edges') or tour.get('undirected_edges')
    if not pairs:
        pairs = [(n['id'], m) for n in tour['nodes'] for m in (n.get('links') or n.get('neighbors') or [])]
    seen, links = set(), []
    for a, b in pairs:
        key = (a, b) if a < b else (b, a)
        if a == b or key in seen or a not in nodes or b not in nodes:
            continue
        seen.add(key)
        links.append((a, b))
    return nodes, links


def _solve1(p, a, nb, smooth, rho, lo, hi):
    """Exact minimiser over [lo, hi] of  a (x-p)^2 + sum_j smooth*w_j (x-x_j)^2 + rho*max(0,|x-x_j|-L_j)^2.
    nb = [(x_j, w_j, L_j)]. The derivative is increasing and piecewise linear with kinks at x_j +- L_j."""
    def g(x):
        s = 2.0 * a * (x - p)
        for xj, w, L in nb:
            d = x - xj
            s += 2.0 * smooth * w * d
            if L is not None:
                if d > L:
                    s += 2.0 * rho * (d - L)
                elif d < -L:
                    s += 2.0 * rho * (d + L)
        return s
    ga = g(lo)
    if ga >= 0.0:
        return lo
    gb = g(hi)
    if gb <= 0.0:
        return hi
    xa, xb = lo, hi
    for bp in sorted({xj + s * L for xj, _, L in nb if L is not None for s in (-1.0, 1.0)}):
        if bp <= xa or bp >= xb:
            continue
        gv = g(bp)
        if gv >= 0.0:
            xb, gb = bp, gv
            break
        xa, ga = bp, gv
    return xa if gb == ga else xa - ga * (xb - xa) / (gb - ga)


def relax(ids, links, probe, anchored, move, limit, weight, smooth=0.25, sweeps=4000, tol=1e-7):
    """Smoothed values {id: x}. probe {id: value}; anchored {id: bool}; move {id: max |x - probe| or None};
    limit: allowed link difference; weight {(a, b): w} (0 = link ignored)."""
    x = {i: probe[i] / limit for i in ids}
    p = dict(x)
    nbrs = {i: [] for i in ids}
    for (a, b) in links:
        w = weight[(a, b)]
        if w <= 0.0:
            continue
        nbrs[a].append((b, w))
        nbrs[b].append((a, w))
    big = 1e9
    box = {i: ((p[i] - move[i] / limit, p[i] + move[i] / limit) if move[i] is not None else (-big, big)) for i in ids}
    # sweeps without a measured value start from the mean of the measured ones (they have no data term)
    known = [p[i] for i in ids if anchored[i]]
    for i in ids:
        if not anchored[i] and known:
            x[i] = sum(known) / len(known)
    rho = 1.0
    while rho <= 4.0 ** 9:
        for _ in range(sweeps):
            worst = 0.0
            for i in ids:
                nb = [(x[j], w, 1.0) for j, w in nbrs[i]]
                if not nb and not anchored[i]:
                    continue
                v = _solve1(p[i], 1.0 if anchored[i] else 0.0, nb, smooth, rho, *box[i])
                worst = max(worst, abs(v - x[i]))
                x[i] = v
            if worst < tol:
                break
        rho *= 4.0
    return {i: x[i] * limit for i in ids}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--meta', required=True, help='render_meta.json of the probe pass')
    ap.add_argument('--out', required=True, help='pins file to write')
    ap.add_argument('--scene', default=os.path.join(HERE, 'data', 'scene.json'))
    ap.add_argument('--max-ev', type=float, default=0.3, help='largest exposure step between linked sweeps (stops)')
    ap.add_argument('--max-kelvin', type=float, default=300.0)
    ap.add_argument('--max-tint', type=float, default=6.0)
    ap.add_argument('--move-ev', type=float, default=0.7, help='largest change of a sweep from its probe (stops)')
    ap.add_argument('--move-kelvin', type=float, default=1200.0)
    ap.add_argument('--move-tint', type=float, default=12.0)
    ap.add_argument('--room-weight', type=float, default=4.0, help='pull of a link inside one room (doorway = 1)')
    ap.add_argument('--smooth', type=float, default=0.25, help='strength of the pull between linked sweeps')
    ap.add_argument('--fix', default='', help='comma list of sweep ids that keep their probe values')
    ap.add_argument('--top', type=int, default=14, help='rows of the before/after table')
    a = ap.parse_args()

    meta = json.load(open(a.meta))
    nodes, links = tour_graph(json.load(open(a.scene)))
    have = [i for i in nodes if isinstance(meta.get(i), dict) and 'exposure' in meta[i]]
    missing = [i for i in nodes if i not in have]
    if missing:
        print(f'WARNING {len(missing)} sweeps have no probe entry and get no pin: {", ".join(missing)}', file=sys.stderr)
    stale = [i for i in meta if i not in nodes]
    if stale:
        print(f'note: ignoring {len(stale)} metadata entries that are not sweeps of the tour: {", ".join(stale)}',
              file=sys.stderr)
    if not have:
        sys.exit('no sweep of the tour has a probe entry in ' + a.meta)
    links = [(x, y) for x, y in links if x in have and y in have]
    fixed = {s for s in a.fix.split(',') if s}

    def kind(x, y):
        if bool(nodes[x].get('outdoor')) != bool(nodes[y].get('outdoor')):
            return 'out'
        return 'room' if nodes[x].get('room') and nodes[x].get('room') == nodes[y].get('room') else 'door'
    kinds = {l: kind(*l) for l in links}
    weight = {l: {'room': a.room_weight, 'door': 1.0, 'out': 0.0}[k] for l, k in kinds.items()}

    def wb_of(i):
        wb = meta[i].get('wb') or [6500.0, 10.0]
        return float(wb[0]), float(wb[1] if len(wb) > 1 else 10.0)
    # a white balance that was not measured carries no information: let the neighbours decide
    def wb_measured(e):
        if e.get('wb_source'):
            return e['wb_source'] != 'default'
        wb = e.get('wb')                                  # older metadata: no wb_source
        return bool((e.get('probe') or {}).get('white_rgb')) or (
            wb is not None and [round(wb[0]), round(wb[1], 1)] != [6500, 10.0])
    measured = {i: wb_measured(meta[i]) for i in have}
    channels = [
        ('ev', {i: float(meta[i]['exposure']) for i in have}, {i: True for i in have}, a.max_ev, a.move_ev),
        ('kelvin', {i: wb_of(i)[0] for i in have}, measured, a.max_kelvin, a.move_kelvin),
        ('tint', {i: wb_of(i)[1] for i in have}, measured, a.max_tint, a.move_tint),
    ]
    before, after = {}, {}
    for name, probe, anchored, limit, move in channels:
        mv = {i: (0.0 if i in fixed else move) if anchored[i] else None for i in have}
        before[name] = probe
        after[name] = relax(have, links, probe, anchored, mv, limit, weight, a.smooth)

    pins = {i: {'ev': round(after['ev'][i], 3), 'kelvin': int(round(after['kelvin'][i])),
                'tint': round(after['tint'][i], 1)} for i in have}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w') as f:
        json.dump(pins, f, indent=1)
        f.write('\n')

    # ---- report
    def diff(vals, l):
        return abs(vals[l[0]] - vals[l[1]])
    rows = [(l, kinds[l], diff(before['ev'], l), diff(after['ev'], l), diff(before['kelvin'], l), diff(after['kelvin'], l),
             diff(before['tint'], l), diff(after['tint'], l)) for l in links]
    real = [r for r in rows if r[1] != 'out']
    eps = 1.02                                           # the penalty method stops a hair outside the limit

    def over(r):
        return r[3] > a.max_ev * eps or r[5] > a.max_kelvin * eps or r[7] > a.max_tint * eps
    print(f'smooth_exposure: {len(have)} sweeps, {len(links)} links '
          f'({sum(k == "room" for k in kinds.values())} in a room, {sum(k == "door" for k in kinds.values())} across a doorway'
          + (f', {sum(k == "out" for k in kinds.values())} indoor/outdoor (left alone)' if 'out' in kinds.values() else '') + ')')
    print(f'limits: links {a.max_ev} stop / {a.max_kelvin:.0f} K / tint {a.max_tint}; '
          f'moves {a.move_ev} stop / {a.move_kelvin:.0f} K / tint {a.move_tint}')
    print()
    print('largest link differences (sorted by the exposure step before; "!" = still over a limit)')
    print(f'  {"link":<9}{"kind":<6}{"ev before":>10}{"after":>7}{"K before":>10}{"after":>7}{"tint before":>13}{"after":>7}')
    key = {'ev': 2, 'kelvin': 4}
    shown = set()
    for which in ('ev', 'kelvin'):
        if which == 'kelvin':
            print('  ... sorted by the white balance step before')
        for r in sorted(rows, key=lambda r: -r[key[which]])[:a.top]:
            tag = '!' if r[1] != 'out' and over(r) else ' '
            shown.add(r[0])
            print(f'  {r[0][0] + "-" + r[0][1]:<9}{r[1]:<6}{r[2]:>10.2f}{r[3]:>7.2f}{r[4]:>10.0f}{r[5]:>7.0f}{r[6]:>13.1f}{r[7]:>7.1f} {tag}')
    left = [r for r in real if over(r) and r[0] not in shown]
    if left:
        print('  ... other links still over a limit')
        for r in left:
            print(f'  {r[0][0] + "-" + r[0][1]:<9}{r[1]:<6}{r[2]:>10.2f}{r[3]:>7.2f}{r[4]:>10.0f}{r[5]:>7.0f}{r[6]:>13.1f}{r[7]:>7.1f} !')
    print()
    if real:
        print(f'max link step  exposure {max(r[2] for r in real):.2f} -> {max(r[3] for r in real):.2f} stops   '
              f'white balance {max(r[4] for r in real):.0f} -> {max(r[5] for r in real):.0f} K   '
              f'tint {max(r[6] for r in real):.1f} -> {max(r[7] for r in real):.1f}')
        print(f'links over a limit: {sum(r[2] > a.max_ev * eps or r[4] > a.max_kelvin * eps or r[6] > a.max_tint * eps for r in real)}'
              f' -> {sum(over(r) for r in real)} of {len(real)}')
    for name, _, anchored, _, move in channels:
        d = {i: after[name][i] - before[name][i] for i in have if anchored[i]}
        if not d:
            continue
        worst = max(d, key=lambda i: abs(d[i]))
        at_limit = sorted(i for i in d if abs(d[i]) >= move * 0.995 and i not in fixed)
        unit = {'ev': ' stop', 'kelvin': ' K', 'tint': ''}[name]
        fmt = '.2f' if name == 'ev' else '.0f' if name == 'kelvin' else '.1f'
        print(f'{name:<7}largest move {d[worst]:+{fmt}}{unit} ({worst}), mean |move| {sum(abs(v) for v in d.values()) / len(d):{fmt}}{unit}'
              + (f'; at the move limit: {", ".join(at_limit)}' if at_limit else ''))
    free = [i for i in have if not measured[i]]
    if free:
        print(f'white balance taken from the neighbours (not measured by the probe): {", ".join(free)}')
    print(f'wrote {a.out}: {len(pins)} pins')


if __name__ == '__main__':
    main()
