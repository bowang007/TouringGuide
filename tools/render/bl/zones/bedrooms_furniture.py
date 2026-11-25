"""Furniture, soft goods, lighting fixtures and decor builders for the bedrooms zone.

All builders take a `Kit` and a `Frame` (SCENE feet). Unless noted, a frame's origin sits on
the floor at the back-centre of the piece (against its wall) and local +z points into the room.
"""
import math

import bpy

from . import bedrooms_kit as K
from .bedrooms_kit import Frame
from ..common import FT, ft2bl


# ------------------------------------------------------------------------------ materials
def mats():
    """Zone materials (created once)."""
    return {
        'linen_white': K.fabric('Z_bedrooms_linen_white', '#f3f1ec', 0.9, 0.5, 380, 0.22, crumple=0.22),
        'linen_ivory': K.fabric('Z_bedrooms_linen_ivory', '#ece6da', 0.9, 0.5, 380, 0.22, crumple=0.22),
        'linen_grey': K.fabric('Z_bedrooms_linen_grey', '#b9b3a9', 0.9, 0.55, 300, 0.3),
        'linen_oat': K.fabric('Z_bedrooms_linen_oat', '#d9cfbf', 0.9, 0.55, 300, 0.3),
        'linen_charcoal': K.fabric('Z_bedrooms_linen_charcoal', '#4c4a47', 0.9, 0.6, 300, 0.3, crumple=0.18),
        'linen_sage': K.fabric('Z_bedrooms_linen_sage', '#98a28c', 0.9, 0.6, 300, 0.3),
        'velvet_ochre': K.fabric('Z_bedrooms_velvet_ochre', '#b9872f', 0.7, 1.0, 600, 0.1),
        'boucle': K.boucle('Z_bedrooms_boucle_cream', '#ebe5d9'),
        'boucle_oat': K.boucle('Z_bedrooms_boucle_oat', '#ddd3c2'),
        'knit_charcoal': K.knit('Z_bedrooms_knit_charcoal', '#5f5c58', 26),
        'knit_oat': K.knit('Z_bedrooms_knit_oat', '#c9bba3', 26),
        'knit_sage': K.knit('Z_bedrooms_knit_sage', '#8a9a78', 26),
        'eucalyptus': K.principled('Z_bedrooms_eucalyptus_leaf', '#8c9d93', 0.55, sheen=0.4),
        'storage': K.fabric('Z_bedrooms_storage_linen', '#d6ccbb', 0.9, 0.5, 300, 0.3),
        'leather': K.principled('Z_bedrooms_leather_tab', '#8a5a35', 0.45),
        'soil': K.principled('Z_bedrooms_soil', '#2e2722', 0.95, bump=(300, 0.6, 4)),
        'shade': K.translucent_fabric('Z_bedrooms_lampshade', '#f2ece1', 0.55),
        'roller': K.translucent_fabric('Z_bedrooms_roller_shade', '#e6dfd2', 0.5),
        'drape': K.translucent_fabric('Z_bedrooms_drape_linen', '#f0ece4', 0.42),
        'stoneware': K.principled('Z_bedrooms_stoneware', '#d8d1c4', 0.55, bump=(220, 0.15, 3)),
        'stoneware_dark': K.principled('Z_bedrooms_stoneware_dark', '#3d3a36', 0.6, bump=(220, 0.15, 3)),
        'lacquer_cream': K.principled('Z_bedrooms_lacquer_cream', '#e8e3d8', 0.32, spec=0.45),
        'melamine': K.principled('Z_bedrooms_melamine', '#f3f2ee', 0.38, spec=0.45),
        'brass': K.principled('Z_bedrooms_brass', '#b8935a', 0.32, metal=1.0),
        'pages': K.principled('Z_bedrooms_pages', '#eee6d4', 0.8),
        'cover_charcoal': K.fabric('Z_bedrooms_book_charcoal', '#35322f', 0.75, 0.3, 500, 0.15, False),
        'cover_sand': K.fabric('Z_bedrooms_book_sand', '#cdbb9b', 0.75, 0.3, 500, 0.15, False),
        'cover_sage': K.fabric('Z_bedrooms_book_sage', '#7f8a74', 0.75, 0.3, 500, 0.15, False),
        'cover_white': K.fabric('Z_bedrooms_book_white', '#ece9e2', 0.75, 0.3, 500, 0.15, False),
        'cover_rust': K.fabric('Z_bedrooms_book_rust', '#9a5b38', 0.75, 0.3, 500, 0.15, False),
        'hanger_wood': K.principled('Z_bedrooms_hanger_wood', '#c9a77c', 0.45),
        'leaf': K.principled('Z_bedrooms_eucalyptus', '#7d8f7e', 0.6, sheen=0.3),
        'stem': K.principled('Z_bedrooms_stem', '#5d5447', 0.7),
    }


GARMENTS = ['#f2f0ea', '#2f3a4a', '#c8b59a', '#7d8576', '#2b2a29', '#e3ddd2', '#5d6f88', '#a7a29a', '#b08a5a',
            '#ece9e3', '#46423e']


# ------------------------------------------------------------------------------ beds
BED_STYLES = {
    # headboard (width extra over mattress, top y, thickness, base y), rails (top y, base y, overhang),
    # mattress (bottom y, thickness)
    'channel': dict(hb_extra=0.85, hb_top=4.05, hb_t=0.42, hb_y0=0.12, rail_top=1.06, rail_y0=0.3,
                    over=0.17, m_y0=0.96, m_t=0.82, plinth='paint_black'),
    'low_linen': dict(hb_extra=0.9, hb_top=2.42, hb_t=0.45, hb_y0=0.2, rail_top=0.94, rail_y0=0.22,
                      over=0.17, m_y0=0.84, m_t=0.8, plinth='white_oak_veneer'),
    'oak': dict(hb_extra=0.55, hb_top=2.4, hb_t=0.2, hb_y0=0.02, rail_top=0.9, rail_y0=0.36,
                over=0.12, m_y0=0.8, m_t=0.78, plinth=None),
}


def bed(kit, M, fr, tag, style, W_m=5.0, L_m=6.67, upholstery=None, bedding=None):
    """Complete made bed in frame `fr` (origin on the wall face at the headboard centre; +z = foot).
    Returns dict with useful local dimensions."""
    st = BED_STYLES[style]
    up = upholstery or M['linen_grey']
    hb_t = st['hb_t']
    hb_w = W_m + st['hb_extra']
    z_m0 = hb_t + 0.05                     # mattress head end
    z_m1 = z_m0 + L_m
    m_y1 = st['m_y0'] + st['m_t']
    rail_w = W_m + 2 * st['over']
    rail_z0, rail_z1 = hb_t, z_m1 + st['over']
    # ---- headboard
    if style == 'channel':
        n = 9
        cw = hb_w / n
        kit.soft(f'{tag} headboard back', fr, (0, (st['hb_y0'] + st['hb_top']) / 2 - 0.05, 0.09),
                 (hb_w - 0.04, st['hb_top'] - st['hb_y0'] - 0.18, 0.16), up, 0.04, 2, 1)
        for i in range(n):
            x = -hb_w / 2 + cw * (i + 0.5)
            kit.soft(f'{tag} headboard channel {i}', fr, (x, (st['hb_y0'] + st['hb_top']) / 2, hb_t / 2 + 0.05),
                     (cw + 0.01, st['hb_top'] - st['hb_y0'], hb_t - 0.08), up, 0.11, 3, 1)
    elif style == 'low_linen':
        kit.soft(f'{tag} headboard', fr, (0, (st['hb_y0'] + st['hb_top']) / 2, hb_t / 2),
                 (hb_w, st['hb_top'] - st['hb_y0'], hb_t), up, 0.14, 3, 1, wrinkle=0.002)
    else:  # oak
        kit.box(f'{tag} headboard', fr, (0, (st['hb_y0'] + st['hb_top']) / 2, hb_t / 2),
                (hb_w, st['hb_top'] - st['hb_y0'], hb_t), 'white_oak_veneer', 0.03, 3)
        # upholstered pad set into the oak headboard
        kit.soft(f'{tag} headboard pad', fr, (0, m_y1 + 0.42, hb_t + 0.07),
                 (W_m - 0.2, 0.62, 0.14), up, 0.05, 3, 1)
    # ---- base / rails
    if style == 'oak':
        kit.box(f'{tag} bed rail', fr, (0, (st['rail_y0'] + st['rail_top']) / 2, (rail_z0 + rail_z1) / 2),
                (rail_w, st['rail_top'] - st['rail_y0'], rail_z1 - rail_z0), 'white_oak_veneer', 0.03, 3)
        for sx in (-1, 1):
            for zz in (rail_z0 + 0.45, rail_z1 - 0.45):
                v, f = K.frustum_geo(0.15, 0.15, 0.2, 0.2, st['rail_y0'])
                kit.mesh(f'{tag} bed leg', v, f, 'white_oak_veneer', fr.p(sx * (rail_w / 2 - 0.35), 0, zz), fr.r())
    else:
        kit.soft(f'{tag} bed rail', fr, (0, (st['rail_y0'] + st['rail_top']) / 2, (rail_z0 + rail_z1) / 2 + 0.02),
                 (rail_w, st['rail_top'] - st['rail_y0'], rail_z1 - rail_z0 - 0.04), up, 0.09, 3, 1)
        kit.box(f'{tag} bed plinth', fr, (0, st['rail_y0'] / 2 + 0.005, (rail_z0 + rail_z1) / 2),
                (rail_w - 0.5, st['rail_y0'] - 0.01, rail_z1 - rail_z0 - 0.5), st['plinth'], 0.01, 2)
    # ---- mattress (fitted sheet)
    bed_m = bedding or {}
    kit.soft(f'{tag} mattress', fr, (0, st['m_y0'] + st['m_t'] / 2, (z_m0 + z_m1) / 2),
             (W_m, st['m_t'], L_m), M['linen_white'], 0.16, 3, 1)
    # ---- duvet over 3 sides
    t_d, r_d = 0.11, 0.31
    top_d = m_y1 + t_d + 0.03
    hem_d = st['rail_top'] - 0.38 if style != 'oak' else st['rail_top'] - 0.3
    kit.drape(f'{tag} duvet', fr, (0, 0, z_m0 + 0.12), W_m, L_m - 0.12, top_d, r_d, hem_d,
              bed_m.get('duvet', M['linen_white']), 'lrf', t_d, folds=0.022, seed=sum(map(ord, tag)) % 97,
              wrinkle=0.011)
    # ---- throw across the foot
    throw = bed_m.get('throw')
    if throw is not None:
        t_t = 0.07
        gap = 0.035
        top_t = top_d + t_t + gap
        r_t = r_d + t_t + gap
        L_t = bed_m.get('throw_len', 1.75)
        kit.drape(f'{tag} throw', fr, (0, 0, z_m1 - L_t - 0.55), W_m, L_t, top_t, r_t, hem_d + 0.05,
                  throw, 'lr', t_t, folds=0.03, seed=7 + len(tag), wrinkle=0.008)
        top_on_foot = top_t
    else:
        top_on_foot = top_d
    # ---- pillows: each row sinks into the duvet and leans on the headboard / the row behind it
    # (contact solved on the pillows' real lens-shaped side profiles, not on bounding boxes)
    if style == 'channel':
        hb_prof = [(st['hb_y0'], st['hb_top'], hb_t + 0.01)]
    elif style == 'low_linen':
        hb_prof = [(st['hb_y0'], st['hb_top'] - 0.1, hb_t), (st['hb_top'] - 0.1, st['hb_top'], hb_t - 0.04)]
    else:
        hb_prof = [(st['hb_y0'], m_y1 + 0.11, hb_t), (m_y1 + 0.11, m_y1 + 0.73, hb_t + 0.14),
                   (m_y1 + 0.73, st['hb_top'], hb_t)]
    support = PillowStack(hb_prof)
    for row in bed_m.get('pillows', []):
        kind, mat, count, phi, pw, pd, pt = row
        pinch = 0.08 if kind != 'lumbar' else 0.05
        yc, zc, prof = support.place(pw, pd, pt, math.radians(phi), pinch, top_d)
        if count == 1:
            xs = [0.0]
        else:
            # neighbours squash into each other a little (no dark slit between them)
            span = min(W_m - pw * 0.92, (pw * 0.9) * (count - 1))
            xs = [-span / 2 + span * i / (count - 1) for i in range(count)]
        obs = [kit.pillow(f'{tag} pillow {kind} {i}', fr, (x, yc, zc), pw, pd, pt, mat, tilt=math.radians(phi),
                          lrot=(0.03 * (i - (count - 1) / 2)), pinch=pinch) for i, x in enumerate(xs)]
        yc += settle(obs, top_d, 0.025)
        support.add(prof, yc, zc)
    return dict(z_m0=z_m0, z_m1=z_m1, rail_z1=rail_z1, rail_w=rail_w, top=top_on_foot, hb_w=hb_w, m_y1=m_y1)


def settle(obs, surface_y, sink=0.025):
    """Shift soft goods vertically so the lowest point of the first object's EVALUATED mesh (after
    subdivision, which rounds a pillow's corners up by a few hundredths of a foot) sits `sink` ft into
    the surface at surface_y. All objects in `obs` share the same shape and get the same shift."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ob = obs[0]
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    y_min = min((mw @ v.co).z for v in me.vertices) / FT
    ev.to_mesh_clear()
    dy = (surface_y - sink) - y_min
    for o in obs:
        o.location.z += dy * FT
    return dy


class PillowStack:
    """Side-profile (local z = toward the foot, y = up) contact solver for pillows leaning in rows.
    Obstacles are kept as the front-most z per 0.02 ft height bin; each new pillow is dropped so its
    lowest point sinks `sink` into the surface below, then slid back until its back profile meets the
    obstacles (pressed in by `squish`)."""
    DY = 0.02

    def __init__(self, segments, sink=0.03, squish=0.035):
        self.front = {}
        self.sink, self.squish = sink, squish
        for y0, y1, z in segments:
            for k in range(int(y0 / self.DY), int(y1 / self.DY) + 1):
                self.front[k] = max(self.front.get(k, -9.0), z)

    @staticmethod
    def profile(w, d, t, tilt, pinch, n=16):
        """(z, y) points of the pillow_geo mesh rotated by `tilt` (top leaning back toward -z)."""
        v, _ = K.pillow_geo(w, d, t, n, pinch)
        c, s = math.cos(tilt), math.sin(tilt)
        return [(pz * c + py * s, py * c - pz * s) for (_px, py, pz) in v]

    def place(self, w, d, t, tilt, pinch, surface):
        prof = self.profile(w, d, t, tilt, pinch)
        # subdivision rounds the lens inward by ~0.01 ft: sink a little deeper to keep the contact
        yc = surface - self.sink + 0.01 - min(p[1] for p in prof)
        back = {}
        for z, y in prof:
            k = int(round((y + yc) / self.DY))
            back[k] = min(back.get(k, 9.0), z)
        need = [self.front[k] - bz for k, bz in back.items() if k in self.front]
        zc = (max(need) if need else 0.0) - self.squish
        return yc, zc, prof

    def add(self, prof, yc, zc):
        for z, y in prof:
            k = int(round((y + yc) / self.DY))
            self.front[k] = max(self.front.get(k, -9.0), z + zc)


# ------------------------------------------------------------------------------ case goods
def nightstand(kit, M, fr, tag, style='oak', w=1.75, h=1.95, d=1.45):
    if style == 'oak':
        kit.box(f'{tag} plinth', fr, (0, 0.12, d / 2 - 0.05), (w - 0.25, 0.24, d - 0.25), 'paint_black', 0.01, 2)
        kit.box(f'{tag} body', fr, (0, (0.24 + h) / 2, (d - 0.03) / 2 + 0.005), (w, h - 0.24, d - 0.04),
                'white_oak_veneer', 0.025, 3)
        dh = (h - 0.24 - 0.06) / 2
        for i in range(2):
            y = 0.24 + 0.03 + dh * (i + 0.5)
            kit.box(f'{tag} drawer {i}', fr, (0, y, d - 0.03), (w - 0.06, dh - 0.03, 0.035), 'white_oak_veneer', 0.008, 2)
            # recessed black finger-pull channel under each front's top edge
            kit.box(f'{tag} pull {i}', fr, (0, y + dh / 2 - 0.05, d - 0.006), (0.55, 0.035, 0.012), 'black_metal', 0.004, 2)
    elif style == 'lacquer':
        # cream lacquer box with an oak top on four slim oak legs
        leg_h = 0.55
        for sx in (-1, 1):
            for sz in (0.12, d - 0.16):
                v, f = K.frustum_geo(0.07, 0.07, 0.1, 0.1, leg_h)
                kit.mesh(f'{tag} leg', v, f, 'white_oak_veneer', fr.p(sx * (w / 2 - 0.12), 0, sz), fr.r())
        kit.box(f'{tag} body', fr, (0, (leg_h + h - 0.08) / 2, d / 2), (w - 0.04, h - 0.08 - leg_h, d - 0.04),
                M['lacquer_cream'], 0.03, 3)
        kit.box(f'{tag} top', fr, (0, h - 0.04, d / 2), (w, 0.08, d), 'white_oak_veneer', 0.015, 3)
        kit.box(f'{tag} drawer line', fr, (0, leg_h + (h - 0.08 - leg_h) * 0.55, d - 0.015),
                (w - 0.14, 0.012, 0.012), 'paint_black', 0.0)
        kit.cyl(f'{tag} knob', fr, (0, leg_h + (h - 0.08 - leg_h) * 0.75, d - 0.005), 0.035, 0.06,
                M['brass'], 16, 'Z')
    else:  # 'compact' oak open nightstand
        kit.box(f'{tag} top', fr, (0, h - 0.04, d / 2), (w, 0.08, d), 'white_oak_veneer', 0.015, 3)
        kit.box(f'{tag} shelf', fr, (0, 0.55, d / 2), (w - 0.1, 0.07, d - 0.1), 'white_oak_veneer', 0.012, 2)
        kit.box(f'{tag} drawer', fr, (0, h - 0.33, d / 2), (w - 0.1, 0.45, d - 0.06), 'white_oak_veneer', 0.012, 2)
        kit.box(f'{tag} drawer gap', fr, (0, h - 0.33 + 0.2, d - 0.03), (w - 0.14, 0.012, 0.012), 'paint_black', 0.0)
        for sx in (-1, 1):
            for sz in (0.08, d - 0.08):
                kit.box(f'{tag} leg', fr, (sx * (w / 2 - 0.05), (h - 0.08) / 2, sz), (0.09, h - 0.08, 0.09),
                        'white_oak_veneer', 0.01, 2)
    return h


def table_lamp(kit, M, fr, tag, base='stoneware', scale=1.0, watts=1.8, bulb=6.0):
    """Ceramic gourd lamp with a linen drum shade. fr origin = lamp foot centre on the surface."""
    s = scale
    prof = [(0.0, 0.0), (0.17 * s, 0.0), (0.2 * s, 0.03 * s), (0.27 * s, 0.22 * s), (0.29 * s, 0.4 * s),
            (0.25 * s, 0.6 * s), (0.16 * s, 0.76 * s), (0.08 * s, 0.86 * s), (0.065 * s, 0.93 * s), (0.0, 0.93 * s)]
    kit.lathe(f'{tag} base', fr, (0, 0, 0), prof, M[base], 48)
    kit.cyl(f'{tag} neck', fr, (0, 1.0 * s, 0), 0.03 * s, 0.16 * s, M['brass'], 16)
    y0, y1 = 1.05 * s, 1.75 * s
    rb, rt = 0.56 * s, 0.5 * s
    th = 0.012
    prof_s = [(rb, y0), (rt, y1), (rt - th, y1), (rb - th, y0)]
    sh = kit.lathe(f'{tag} shade', fr, (0, 0, 0), prof_s, M['shade'], 64, closed=True)
    # bulb (glows, casts no shadow) + the actual light
    bulb = kit.cyl(f'{tag} bulb', fr, (0, 1.32 * s, 0), 0.07 * s, 0.22 * s, kit.emitter('bedroom_bulb', 2800, bulb), 16)
    bulb.visible_shadow = False
    x, y, z = fr.p(0, 1.42 * s, 0)
    kit.point(x, y, z, watts, 2800, 0.1, f'{tag} lamp')
    return sh


def book_stack(kit, M, fr, tag, books, lrot=0.0):
    """books: list of (w, d, t, cover_key); stacked from fr origin upward."""
    y = 0.0
    for i, (w, d, t, cov) in enumerate(books):
        r = lrot + 0.06 * ((i * 37) % 5 - 2)
        sub = fr.sub(0, 0, r)
        kit.box(f'{tag} book {i} cover', sub, (0, y + t / 2, 0), (w, t, d), M[cov], 0.008, 2)
        kit.box(f'{tag} book {i} pages', sub, (0.012, y + t / 2, 0), (w - 0.02, t - 0.03, d - 0.035), M['pages'], 0.0)
        y += t
    return y


def bud_vase(kit, M, fr, tag, mat='stoneware', h=0.55, stems=4, seed=1):
    """Stoneware bud vase with a few silver-dollar eucalyptus stems."""
    import random
    rng = random.Random(seed)
    prof = [(0.0, 0.0), (0.12, 0.0), (0.16, 0.12), (0.15, 0.3 * h / 0.55), (0.07, 0.48 * h / 0.55),
            (0.045, h - 0.03), (0.055, h), (0.035, h), (0.035, h - 0.04), (0.0, h - 0.04)]
    kit.lathe(f'{tag} vase', fr, (0, 0, 0), prof, M[mat], 40)
    for k in range(stems):
        a = math.tau * k / stems + rng.uniform(-0.3, 0.3)
        lean = rng.uniform(0.18, 0.42)
        L = rng.uniform(1.0, 1.45)
        _eucalyptus(kit, M, fr, f'{tag} stem {k}', (0, h - 0.06, 0), a, lean, L, rng)



def _eucalyptus(kit, M, fr, tag, base, azim, lean, L, rng, segs=5):
    """Curved stem with paired round leaves (silver-dollar eucalyptus)."""
    from mathutils import Vector
    pts = []
    for i in range(segs + 1):
        t = i / segs
        r = lean * L * (t + 0.6 * t * t)
        pts.append((base[0] + math.cos(azim) * r, base[1] + L * t * (1 - 0.15 * t), base[2] + math.sin(azim) * r))
    for i in range(segs):
        a, b = pts[i], pts[i + 1]
        mid = tuple((a[j] + b[j]) / 2 for j in range(3))
        ob = kit.cyl(f'{tag} seg {i}', fr, mid, 0.008, math.dist(a, b) + 0.01, M['stem'], 6)
        d = Vector((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
        # local frame -> world: rotate by frame yaw
        c, s_ = math.cos(fr.rot), math.sin(fr.rot)
        wx, wy, wz = d.x * c + d.z * s_, d.y, -d.x * s_ + d.z * c
        ob.rotation_euler = Vector((wx, -wz, wy)).normalized().to_track_quat('Z', 'Y').to_euler()
    n = 2 * segs + 2
    for i in range(n):
        t = 0.18 + 0.8 * i / n
        k = min(segs - 1, int(t * segs))
        f = t * segs - k
        a, b = pts[k], pts[k + 1]
        p = tuple(a[j] + (b[j] - a[j]) * f for j in range(3))
        side = 1 if i % 2 else -1
        ang = azim + side * 1.4 + rng.uniform(-0.3, 0.3)
        r = 0.075 * (1.15 - 0.55 * t)
        px, py, pz = p[0] + math.cos(ang) * r * 0.9, p[1], p[2] + math.sin(ang) * r * 0.9
        lf = kit.cyl(f'{tag} leaf {i}', fr, (px, py, pz), r, 0.008, M['eucalyptus'], 14)
        lf.rotation_euler = (rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), fr.rot + rng.uniform(0, 3.1))


def snake_plant(kit, M, fr, tag, planter='stoneware', r=0.46, h=1.15, n=14, seed=3):
    """Sansevieria in a modern cylindrical planter. fr origin = planter centre on the floor."""
    import random
    rng = random.Random(seed)
    prof = [(0.0, 0.0), (r - 0.04, 0.0), (r, 0.05), (r, h - 0.02), (r - 0.02, h), (r - 0.07, h), (r - 0.07, h - 0.12), (0.0, h - 0.12)]
    kit.lathe(f'{tag} planter', fr, (0, 0, 0), prof, M[planter], 64)
    kit.cyl(f'{tag} soil', fr, (0, h - 0.13, 0), r - 0.075, 0.03, M['soil'], 40)
    mat = K.snake_plant_material()
    for i in range(n):
        ang = math.tau * i / n + rng.uniform(-0.3, 0.3)
        rr = rng.uniform(0.0, r - 0.17)
        L = rng.uniform(1.7, 3.1) * (1.0 if rr < 0.15 else 0.85)
        v, f = K.blade_geo(L, rng.uniform(0.17, 0.26), rng.uniform(0.02, 0.14), rng.uniform(-0.7, 0.7),
                           rng.uniform(0.0, 0.12), i)
        x, y, z = fr.p(math.cos(ang) * rr, h - 0.14, math.sin(ang) * rr)
        ob = kit.mesh(f'{tag} leaf {i}', v, f, mat, (x, y, z), fr.rot + ang - math.pi / 2 + rng.uniform(-0.4, 0.4), smooth=True)
        K.Kit.solidify(ob, 0.012, 0.0)


# ------------------------------------------------------------------------------ textiles
def rug(kit, name, x0, x1, z0, z1, mat, y0=0.012, t=0.04):
    return kit.wbox(name, x0, x1, y0, y0 + t, z0, z1, mat, 0.018, 2)


def roller_shade(kit, M, fr, tag, w, y_head, drop, depth=0.16):
    """Inside-mount roller shade. fr: origin at the window's inside face centre, +z into the room;
    the cassette sits just inside the reveal."""
    kit.box(f'{tag} cassette', fr, (0, y_head - 0.11, -depth / 2 - 0.02), (w, 0.22, depth), 'paint_trim', 0.02, 2)
    ob = kit.box(f'{tag} fabric', fr, (0, y_head - 0.22 - drop / 2, -depth / 2 - 0.02), (w - 0.06, drop, 0.006),
                 M['roller'], 0.0)
    kit.box(f'{tag} hem bar', fr, (0, y_head - 0.22 - drop - 0.03, -depth / 2 - 0.02), (w - 0.05, 0.06, 0.03),
            'paint_trim', 0.008, 2)
    return ob


def ripplefold(kit, M, tag, x0, x1, zc, y0=0.06, y1=7.88, amp=0.12, lam=0.34, seed=1):
    """Stacked ripplefold drape panel along x at depth zc (world)."""
    import random
    rng = random.Random(seed)
    nx = max(8, int((x1 - x0) / 0.025))
    ys = [y0, y0 + 0.3, 0.9, 2.0, 3.4, 4.8, 6.2, 7.2, y1]
    verts, faces = [], []
    ph = rng.uniform(0, 6.28)
    for j, y in enumerate(ys):
        flare = 1.0 + 0.18 * (1 - y / y1)
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            z = zc + amp * flare * math.sin(2 * math.pi * (x - x0) / lam + ph) + 0.015 * math.sin(7.3 * x + 2 * y)
            verts.append((x, y, z))
    m = nx + 1
    for j in range(len(ys) - 1):
        for i in range(nx):
            faces.append((j * m + i, j * m + i + 1, (j + 1) * m + i + 1, (j + 1) * m + i))
    ob = kit.mesh(f'{tag} drape', verts, faces, M['drape'], (0, 0, 0), smooth=True)
    K.Kit.solidify(ob, 0.012, 0.0)
    s = ob.modifiers.new('Subsurf', 'SUBSURF')
    s.levels = s.render_levels = 1
    return ob


# ------------------------------------------------------------------------------ wall art
def canvas_art(kit, fr, tag, w, h, img_arr, frame='white_oak_veneer', y_c=5.0, depth=0.12, gap=0.035):
    """Floater-framed canvas on a wall. fr origin = wall surface point under the art centre."""
    img = K.to_image(f'Z_bedrooms_art_{tag}', img_arr)
    mat = K.image_material(f'Z_bedrooms_art_{tag}', img)
    kit.box(f'{tag} canvas', fr, (0, y_c, depth / 2 + 0.01), (w, h, depth), 'paint_trim', 0.004, 1)
    hw, hh = w / 2, h / 2
    v = [(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)]
    kit.mesh(f'{tag} canvas face', v, [(0, 1, 2, 3)], mat, fr.p(0, y_c, depth + 0.012), fr.r(),
             uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    fw, fd = 0.045, depth + 0.06
    W, H = w + 2 * gap + 2 * fw, h + 2 * gap + 2 * fw
    kit.box(f'{tag} frame back', fr, (0, y_c, 0.008), (W, H, 0.012), frame, 0.0)
    for nm, cx, cy, sx, sy in (('top', 0, H / 2 - fw / 2, W, fw), ('bottom', 0, -H / 2 + fw / 2, W, fw),
                               ('left', -W / 2 + fw / 2, 0, fw, H - 2 * fw), ('right', W / 2 - fw / 2, 0, fw, H - 2 * fw)):
        kit.box(f'{tag} frame {nm}', fr, (cx, y_c + cy, fd / 2), (sx, sy, fd), frame, 0.006, 2)


def framed_print(kit, fr, tag, w, h, img_arr, mat_border=0.32, y_c=5.0):
    """Thin black frame, white mat, paper print."""
    img = K.to_image(f'Z_bedrooms_art_{tag}', img_arr)
    mat = K.image_material(f'Z_bedrooms_art_{tag}', img, 0.9)
    fw, fd = 0.06, 0.09
    W, H = w + 2 * mat_border + 2 * fw, h + 2 * mat_border + 2 * fw
    kit.box(f'{tag} backing', fr, (0, y_c, 0.03), (W - 0.02, H - 0.02, 0.05), 'paint_trim', 0.0)
    kit.box(f'{tag} mat', fr, (0, y_c, 0.06), (W - 2 * fw + 0.01, H - 2 * fw + 0.01, 0.012), 'plaster_white', 0.0)
    hw, hh = w / 2, h / 2
    v = [(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)]
    kit.mesh(f'{tag} print', v, [(0, 1, 2, 3)], mat, fr.p(0, y_c, 0.069), fr.r(), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    for nm, cx, cy, sx, sy in (('top', 0, H / 2 - fw / 2, W, fw), ('bottom', 0, -H / 2 + fw / 2, W, fw),
                               ('left', -W / 2 + fw / 2, 0, fw, H - 2 * fw), ('right', W / 2 - fw / 2, 0, fw, H - 2 * fw)):
        kit.box(f'{tag} frame {nm}', fr, (cx, y_c + cy, fd / 2), (sx, sy, fd), 'black_metal', 0.008, 2)


# ------------------------------------------------------------------------------ seating / desks
def boucle_bench(kit, M, fr, tag, w=4.0, d=1.35, h=1.5):
    """Upholstered boucle bench (rounded ends, piped top seam) on an inset white-oak base.
    fr origin = bench centre on the floor."""
    base_h = 0.5
    # oak base: inset 0.1 ft all round so the cushion overhangs and casts a contact shadow on it
    kit.prism(f'{tag} base', fr, (0, 0, 0), K.rounded_rect(w - 0.2, d - 0.2, 0.5, 10), 0.0, base_h,
              'white_oak_veneer', bevel=0.02, seg=2)
    # upholstered body (slightly domed by the bevel + subdivision)
    kit.prism(f'{tag} body', fr, (0, 0, 0), K.rounded_rect(w, d, 0.6, 12), base_h, h, M['boucle'],
              bevel=0.12, seg=4, sub=1)
    # piping along the top seam: a thin rounded ring just proud of the body's side
    kit.prism(f'{tag} welt', fr, (0, 0, 0), K.rounded_rect(w + 0.012, d + 0.012, 0.606, 12), h - 0.2, h - 0.17,
              M['boucle'], bevel=0.012, seg=2)


def barrel_chair(kit, M, fr, tag):
    """Sculptural boucle barrel desk chair on four splayed oak legs. fr origin = seat centre on the
    floor, +z = the direction the sitter faces."""
    seat_y = 1.55
    # curved back: arc slab around the rear of the seat
    R, th, a0, a1 = 0.98, 0.2, math.radians(200), math.radians(340)
    n = 24
    verts, faces = [], []
    ys = (seat_y - 0.15, seat_y + 1.0)
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        for rr in (R, R - th):
            for y in ys:
                # the back is lower at its arms
                yy = y if y == ys[0] else ys[1] - 0.32 * (abs(k - n / 2) / (n / 2)) ** 2
                verts.append((rr * math.cos(a), yy, rr * math.sin(a)))
    # verts per k: [outer-bottom, outer-top, inner-bottom, inner-top]
    for k in range(n):
        o = k * 4
        p = (k + 1) * 4
        faces += [(o + 0, p + 0, p + 1, o + 1), (o + 2, o + 3, p + 3, p + 2), (o + 1, p + 1, p + 3, o + 3), (o + 0, o + 2, p + 2, p + 0)]
    faces += [(0, 1, 3, 2), (n * 4 + 0, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
    v, f = K._merge(verts, faces)
    ob = kit.mesh(f'{tag} back', v, f, M['boucle_oat'], fr.p(0, 0, 0), fr.r())
    K.Kit.soften(ob, 0.07, 3, 1)
    # seat cushion
    poly = [(math.cos(TA) * 0.95, math.sin(TA) * 0.88) for TA in [i * math.tau / 40 for i in range(40)]]
    seat = kit.prism(f'{tag} seat', fr, (0, 0, 0), poly, seat_y - 0.32, seat_y, M['boucle_oat'], bevel=0.1, seg=3, sub=1)
    # legs (splayed, tapered oak)
    for i, a in enumerate((45, 135, 225, 315)):
        ar = math.radians(a)
        lx, lz = math.cos(ar) * 0.62, math.sin(ar) * 0.58
        v, f = K.frustum_geo(0.09, 0.09, 0.12, 0.12, seat_y - 0.28)
        kit.mesh(f'{tag} leg {i}', v, f, 'white_oak_veneer', fr.p(lx, 0, lz), fr.r())
    return seat


def desk(kit, M, fr, tag, w=4.0, d=1.75, h=2.5, legs='oak'):
    """Writing desk. fr origin = wall face centre on the floor, +z into the room."""
    kit.box(f'{tag} top', fr, (0, h - 0.06, d / 2), (w, 0.12, d), 'white_oak_veneer', 0.02, 3)
    kit.box(f'{tag} apron', fr, (0, h - 0.24, d / 2 - 0.05), (w - 0.5, 0.24, d - 0.3), 'white_oak_veneer', 0.012, 2)
    kit.box(f'{tag} drawer gap', fr, (0, h - 0.24, d - 0.345), (w * 0.42, 0.012, 0.012), 'paint_black', 0.0)
    if legs == 'oak':
        for sx in (-1, 1):
            for sz in (0.18, d - 0.2):
                v, f = K.frustum_geo(0.09, 0.09, 0.13, 0.13, h - 0.12)
                kit.mesh(f'{tag} leg', v, f, 'white_oak_veneer', fr.p(sx * (w / 2 - 0.18), 0, sz), fr.r())
    else:  # black steel sled legs
        for sx in (-1, 1):
            x = sx * (w / 2 - 0.2)
            kit.box(f'{tag} sled upright f', fr, (x, (h - 0.12) / 2, d - 0.15), (0.08, h - 0.12, 0.08), 'black_metal', 0.01, 2)
            kit.box(f'{tag} sled upright b', fr, (x, (h - 0.12) / 2, 0.15), (0.08, h - 0.12, 0.08), 'black_metal', 0.01, 2)
            kit.box(f'{tag} sled foot', fr, (x, 0.04, d / 2), (0.08, 0.08, d - 0.22), 'black_metal', 0.01, 2)
            kit.box(f'{tag} sled head', fr, (x, h - 0.16, d / 2), (0.08, 0.08, d - 0.22), 'black_metal', 0.01, 2)


def side_chair(kit, M, fr, tag, seat_mat=None):
    """White-oak side chair: tapered legs, rear legs running up into the back posts, a curved back
    rail whose ends are housed in the posts, an apron and an upholstered seat pad.
    fr origin = seat centre on the floor, +z = the direction the sitter faces."""
    sy = 1.5                                  # seat top (18 in)
    oak = 'white_oak_veneer'
    zr = -0.47                                # rear leg / back post line
    for i, lx in enumerate((-0.58, 0.58)):
        v, f = K.frustum_geo(0.085, 0.085, 0.115, 0.115, sy - 0.2)
        ob = kit.mesh(f'{tag} front leg {i}', v, f, oak, fr.p(lx, 0, 0.52), fr.r())
        kit.ctx.add_bevel(ob, 0.01, 2)
    for i, lx in enumerate((-0.6, 0.6)):
        v, f = K.frustum_geo(0.09, 0.09, 0.105, 0.105, sy + 1.12)
        ob = kit.mesh(f'{tag} back post {i}', v, f, oak, fr.p(lx, 0, zr), fr.r())
        kit.ctx.add_bevel(ob, 0.012, 2)
    kit.box(f'{tag} apron', fr, (0, sy - 0.26, 0.02), (1.1, 0.13, 0.95), oak, 0.01, 2)
    kit.soft(f'{tag} seat', fr, (0, sy - 0.09, 0.03), (1.42, 0.17, 1.3), seat_mat or oak, 0.06, 3, 1)
    # curved back rail (bows 1.6 in backward at the middle), ends housed in the posts
    n, R = 18, 1.4
    a1 = math.asin(0.6 / R)
    verts, faces = [], []
    for k in range(n + 1):
        a = -a1 + 2 * a1 * k / n
        for rr in (R, R - 0.065):
            for y in (sy + 0.72, sy + 1.08):
                verts.append((rr * math.sin(a), y, zr - (rr * math.cos(a) - R * math.cos(a1))))
    for k in range(n):
        o, p = k * 4, (k + 1) * 4
        faces += [(o, p, p + 1, o + 1), (o + 2, o + 3, p + 3, p + 2), (o + 1, p + 1, p + 3, o + 3), (o, o + 2, p + 2, p)]
    faces += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
    v, f = K._merge(verts, faces)
    ob = kit.mesh(f'{tag} back rail', v, f, oak, fr.p(0, 0, 0), fr.r())
    K.Kit.soften(ob, 0.015, 2, 0)


# ------------------------------------------------------------------------------ ceiling fixtures
def vault_y(x, x_w=0.225, x_r=7.036, x_e=13.892, eave=8.0, ridge=11.5):
    """Underside height of the bedroom 3/4 vaulted ceilings at SCENE x."""
    if x <= x_r:
        return eave + (ridge - eave) * (x - x_w) / (x_r - x_w)
    return eave + (ridge - eave) * (x_e - x) / (x_e - x_r)


def slope_can(kit, x, z, watts=3.0, tag='slope can', lens=16.0):
    """4in recessed LED downlight set into the vault slope (trim follows the slope)."""
    y = vault_y(x)
    slope = (11.5 - 8.0) / (7.036 - 0.225) if x < 7.036 else -(11.5 - 8.0) / (13.892 - 7.036)
    ang = math.atan(slope)
    r = 4.0 / 24.0
    lens_strength = lens
    trim = kit.ctx.cylinder(f'{tag} trim {x:.1f},{z:.1f}', (x, y - 0.004, z), r, 0.006, 'paint_trim', kit.lcoll, verts=32)
    lens = kit.ctx.cylinder(f'{tag} lens {x:.1f},{z:.1f}', (x, y - 0.008, z), r * 0.75, 0.006, None, kit.lcoll, verts=32)
    lens.data.materials.append(kit.emitter('bed_can', 3000, lens_strength))
    # tilt about SCENE z (Blender -Y): positive slope (rising to +x) -> rotate so the disc follows
    for ob in (trim, lens):
        ob.rotation_euler = (0, -ang, 0)
    ld = bpy.data.lights.new(f'{tag} {x:.1f},{z:.1f}', 'SPOT')
    ld.energy = watts
    from ..lighting import kelvin_rgb
    ld.color = kelvin_rgb(3000)
    ld.spot_size = math.radians(110)
    ld.spot_blend = 0.85
    ld.shadow_soft_size = 0.03
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(x, y - 0.08, z)
    kit.ctx.coll(kit.lcoll).objects.link(lo)
    kit.lights += 1
    kit.n += 2


def ridge_canopy(kit, M, x, z, tag, radius=0.22, mat='paint_trim', vault=None):
    """Round canopy whose top follows both vault slopes at the ridge (no gap, no intersection).
    `vault` (v7 repair): the ceiling's underside as a function of x when it is not the concept's (vault_y)."""
    import bmesh
    vault_y = vault or globals()['vault_y']
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=radius * FT, radius2=radius * FT, depth=0.25 * FT)
    for v in bm.verts:
        if v.co.z > 0:
            wx = x + v.co.x / FT
            v.co.z = (vault_y(wx) - 0.004) * FT
        else:
            v.co.z = (vault_y(x) - 0.004 - 0.14 - radius * 0.52) * FT
    me = bpy.data.meshes.new(f'{tag} canopy')
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    ob = bpy.data.objects.new(me.name, me)
    p = ft2bl(x, 0, z)
    ob.location = (p.x, p.y, 0)
    me.materials.append(kit.mat(mat))
    kit.ctx.coll(kit.cname).objects.link(ob)
    kit.n += 1
    return vault_y(x) - 0.14 - radius * 0.52


def ring_pendant(kit, M, x, z, y_ring, tag, R=1.25, watts_strength=55.0):
    """Slim LED ring pendant (matte black outer, warm diffuser underneath) on three thin cables
    from a ridge canopy."""
    y_can = ridge_canopy(kit, M, x, z, f'{tag} pendant', 0.2, 'black_metal')
    # build the ring as a lathe-like torus with a rectangular section
    segs = 128
    prof = [(R + 0.05, y_ring - 0.03), (R + 0.05, y_ring + 0.04), (R - 0.05, y_ring + 0.04), (R - 0.05, y_ring - 0.03)]
    fr = Frame(x, z, 0.0)
    kit.lathe(f'{tag} pendant ring', fr, (0, 0, 0), prof, 'black_metal', segs, closed=True, smooth=False)
    prof_d = [(R + 0.042, y_ring - 0.034), (R - 0.042, y_ring - 0.034), (R - 0.042, y_ring - 0.02), (R + 0.042, y_ring - 0.02)]
    d = kit.lathe(f'{tag} pendant diffuser', fr, (0, 0, 0), prof_d, kit.emitter('bed_ring', 3000, watts_strength),
                  segs, closed=True, smooth=False)
    d.visible_shadow = False
    pendant_cables(kit, tag, x, z, y_can, y_ring + 0.04, R)


def pendant_cables(kit, tag, x, z, y_can, y_top, R=1.25):
    """The ring pendant's three cables from its canopy (underside y_can) to the ring's top face (y_top). (v7 repair:
    split off ring_pendant so that bedrooms_rooms can hang Bedroom 3's ring again from the ridge as built.)"""
    for k in range(3):
        a = math.tau * k / 3 + 0.4
        cx, cz = x + math.cos(a) * (R - 0.0), z + math.sin(a) * (R - 0.0)
        top = (x + math.cos(a) * 0.12, y_can + 0.02, z + math.sin(a) * 0.12)
        bot = (cx, y_top, cz)
        L = math.dist(top, bot)
        mid = tuple((top[i] + bot[i]) / 2 for i in range(3))
        cb = kit.ctx.cylinder(f'{tag} pendant cable {k}', mid, 0.006, L, 'black_metal', kit.cname, verts=6)
        dx, dy, dz = bot[0] - top[0], bot[1] - top[1], bot[2] - top[2]
        # direction in Blender: (dx, -dz, dy); align local Z
        from mathutils import Vector
        vb = Vector((dx, -dz, dy)).normalized()
        cb.rotation_euler = vb.to_track_quat('Z', 'Y').to_euler()
        kit.n += 1


def globe_pendant(kit, M, x, z, y_c, tag, r=0.5, strength=2.2, watts=12.0):
    """Opal glass globe on a brass stem from a ridge canopy. The globe glows warm-white (brighter
    toward its centre, see _opal) and a lamp inside lights the room; the glass casts no shadow so
    the lamp reaches the room directly."""
    y_can = ridge_canopy(kit, M, x, z, f'{tag} pendant', 0.2, M['brass'])
    stem_top = y_can + 0.02
    stem_bot = y_c + r - 0.05
    kit.ctx.cylinder(f'{tag} pendant stem', (x, (stem_top + stem_bot) / 2, z), 0.022, stem_top - stem_bot,
                     M['brass'], kit.cname, verts=16)
    kit.ctx.cylinder(f'{tag} pendant collar', (x, stem_bot - 0.02, z), 0.09, 0.14, M['brass'], kit.cname, verts=24)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=r * FT)
    me = bpy.data.meshes.new(f'{tag} pendant globe')
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    ob = bpy.data.objects.new(me.name, me)
    ob.location = ft2bl(x, y_c, z)
    me.materials.append(_opal(kit, strength))
    ob.visible_shadow = False
    kit.ctx.coll(kit.cname).objects.link(ob)
    kit.point(x, y_c, z, watts, 3000, 0.12, f'{tag} globe lamp')
    kit.n += 3


def _opal(kit, strength=2.2):
    """Satin opal glass: a white glossy-coated diffuse shell (reads off-white in daylight) plus a
    warm-white glow (3400K, desaturated toward white) that is strongest where the shell faces the
    viewer and falls off toward the silhouette, like a lamp seen through milky glass. The emission
    strength stays an unlinked socket so lighting.apply_balance still scales it."""
    m = bpy.data.materials.get('Z_bedrooms_opal')
    if m:
        return m
    m = bpy.data.materials.new('Z_bedrooms_opal')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    from ..lighting import kelvin_rgb
    warm = kelvin_rgb(3400)
    glow = tuple(0.8 * c + 0.2 for c in warm)            # warm cream-white, not orange
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.86, 0.85, 0.83, 1)
    b.inputs['Roughness'].default_value = 0.35
    b.inputs['Coat Weight'].default_value = 0.6
    b.inputs['Coat Roughness'].default_value = 0.06
    b.inputs['Subsurface Weight'].default_value = 0.35
    b.inputs['Subsurface Radius'].default_value = (0.03, 0.03, 0.025)
    # facing falloff: 1 at the centre of the disc -> ~0.3 at the rim
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.5
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs['Facing'], inv.inputs[1])
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 1.6
    nt.links.new(inv.outputs[0], pw.inputs[0])
    fl = nt.nodes.new('ShaderNodeMapRange')
    fl.inputs['To Min'].default_value = 0.3
    fl.inputs['To Max'].default_value = 1.0
    nt.links.new(pw.outputs[0], fl.inputs['Value'])
    col = nt.nodes.new('ShaderNodeMix')
    col.data_type = 'RGBA'
    col.blend_type = 'MULTIPLY'
    sock = {s_.identifier: s_ for s_ in col.inputs}
    sock['Factor_Float'].default_value = 1.0
    sock['A_Color'].default_value = glow + (1,)
    nt.links.new(fl.outputs[0], sock['B_Color'])
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = strength
    nt.links.new([o for o in col.outputs if o.identifier == 'Result_Color'][0], em.inputs['Color'])
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(b.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (0.9, 0.88, 0.84, 1)
    return m


def disk_light(kit, x, z, tag, ceil=8.0, r=0.3, watts=4.0, kelvin=5000):
    """Slim surface-mounted LED disk (closets)."""
    kit.ctx.cylinder(f'{tag} disk body', (x, ceil - 0.03, z), r, 0.06, 'paint_trim', kit.lcoll, verts=48)
    lens = kit.ctx.cylinder(f'{tag} disk lens', (x, ceil - 0.061, z), r * 0.86, 0.004, None, kit.lcoll, verts=48)
    lens.data.materials.append(kit.emitter('bed_disk', kelvin, 3.0))
    lens.visible_shadow = False
    ld = bpy.data.lights.new(f'{tag} disk', 'AREA')
    ld.shape = 'DISK'
    ld.size = r * 1.6 * FT
    ld.energy = watts
    from ..lighting import kelvin_rgb
    ld.color = kelvin_rgb(kelvin)
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(x, ceil - 0.075, z)
    kit.ctx.coll(kit.lcoll).objects.link(lo)
    kit.lights += 1
    kit.n += 2


# ------------------------------------------------------------------------------ closets
def storage_box(kit, M, fr, tag, w, h, d):
    """Linen-wrapped lidded storage box with a leather pull tab. fr origin = bottom centre."""
    kit.soft(f'{tag} box', fr, (0, (h - 0.12) / 2, 0), (w - 0.02, h - 0.12, d - 0.02), M['storage'], 0.025, 2, 1)
    kit.soft(f'{tag} lid', fr, (0, h - 0.07, 0), (w, 0.14, d), M['storage'], 0.03, 2, 1)
    kit.box(f'{tag} tab', fr, (0, h - 0.24, d / 2 - 0.005), (0.28, 0.12, 0.02), M['leather'], 0.01, 2)



# colour-blocked like a staged closet: whites -> blues -> neutrals -> darks
SHIRTS = ['#f2f0ea', '#eae6dd', '#c9d3dc', '#a9b8c6', '#dcd2c0', '#c9bba3', '#8d8a85', '#5e5d5a', '#2b2c2e']
JACKETS = ['#b08a5e', '#3c4250', '#d6cfc2', '#1f1f21']
TROUSERS = ['#2f3032', '#c8bea9', '#454b57', '#e4ddcf', '#6f6b64', '#b6a789']


def _cloth(col, kind='shirt', along='x'):
    if kind == 'jacket':        # suiting wool: softer sheen, coarser twill bump
        return K.fabric(f'Z_bedrooms_wool_{col[1:]}', col, 0.9, 0.35, 260, 0.32)
    if kind == 'stripe':        # white shirting with sky-blue bengal stripes running down the garment
        m = K.fabric(f'Z_bedrooms_cloth_{col[1:]}_stripe_{along}', col, 0.82, 0.5, 520, 0.18)
        return K.stripe(m, '#93acc7', 'Y' if along == 'x' else 'X', 0.5, 0.4)
    return K.fabric(f'Z_bedrooms_cloth_{col[1:]}', col, 0.82, 0.5, 520, 0.18)


def hanger_row(kit, M, a0, a1, c, y_rail, tag, along='x', seed=1, items=None, rod_r=0.04, start='a1', front=1,
               floor_y=0.3, subsurf=1):
    """Hangers + garments on a rail running along `along` ('x' or 'z') from a0 to a1 at plan coordinate
    c (z for an x-rail, x for a z-rail), rail centre height y_rail.
    items: list of (kind, colour) with kind in shirt/jacket/trousers, hung from the `start` end at uneven
    0.2-0.32 ft centres (trousers 0.15-0.2) with smoothly varying yaw; whatever does not fit is dropped.
    Shirts/jackets (bedrooms_garments.garment: shoulders, sleeves, collar/lapels) hang on contoured oak
    hangers; trousers fold over an oak slack bar. front=+1/-1 turns the garment fronts toward +/- the
    rail direction (the side the camera sees). floor_y: nothing hangs below this height. subsurf: 0 for
    rows no camera sees from close up (saves ~30k triangles per garment)."""
    import random
    from mathutils import Vector
    from . import bedrooms_garments as G
    rng = random.Random(seed)
    sway = Vector((rng.random() * 30, rng.random() * 30, rng.random() * 30))
    lo, hi = min(a0, a1), max(a0, a1)
    sgn = -1 if start == 'a1' else 1
    pos = (hi if start == 'a1' else lo) + sgn * 0.13
    ph = rng.uniform(0, 6.3)
    for i, (kind, col) in enumerate(items or []):
        mat_kind = kind
        if kind == 'stripe':
            kind = 'shirt'
        if i:
            pos += sgn * (rng.uniform(0.15, 0.2) if kind == 'trousers' else rng.uniform(0.2, 0.32))
        centre = pos + rng.uniform(-0.015, 0.015)
        if centre < lo + 0.1 or centre > hi - 0.1:
            break
        yaw = 0.05 * math.sin(0.9 * i + ph) + rng.uniform(-0.018, 0.018)
        p = (centre, c) if along == 'x' else (c, centre)
        nm = f'{tag} {i}'
        if kind == 'trousers':
            sh_y = y_rail - 0.13
            v, f = K.tube_geo(K.hook_pts(p, along, y_rail, rod_r, sh_y + 0.015), 0.011, 8)
            kit.mesh(f'{nm} hook', v, f, 'chrome', smooth=True)
            _bar_hanger(kit, M, nm, p, along, sh_y, yaw)
            lb = min(rng.uniform(1.45, 1.8), sh_y - floor_y)
            v, f = G.trousers(p, along, sh_y, rng.uniform(1.12, 1.38), lb, rng.uniform(0.28, 0.33),
                              seed + 31 * i, yaw, sway, front)
        else:
            top = y_rail - 0.14 - 0.035
            hy = G.hanger_curve(top, 0.62, 0.13)
            pts = []
            for k in range(-12, 13):
                d = 0.62 * k / 12
                lc, ld = d * math.sin(yaw), d * math.cos(yaw)
                pts.append((p[0] + lc, hy(d), p[1] + ld) if along == 'x' else (p[0] + ld, hy(d), p[1] + lc))
            v, f = K.tube_geo(pts, 0.021, 10)
            kit.mesh(f'{nm} hanger', v, f, M['hanger_wood'], smooth=True)
            v, f = K.tube_geo(K.hook_pts(p, along, y_rail, rod_r, top), 0.011, 8)
            kit.mesh(f'{nm} hook', v, f, 'chrome', smooth=True)
            L = rng.uniform(2.2, 2.6) if kind == 'shirt' else rng.uniform(2.4, 2.65)
            L = min(L, top - floor_y)
            shw = rng.uniform(1.3, 1.44) if kind == 'shirt' else rng.uniform(1.46, 1.56)
            v, f = G.garment(kind, p, along, hy, L, shw, seed + 31 * i, yaw, sway, front)
        v, f = K._merge(v, f, 1e-7)
        ob = kit.mesh(f'{nm} {kind}', v, f, _cloth(col, mat_kind, along), smooth=True)
        if kind != 'trousers':                     # open fabric tubes get real cloth thickness
            K.Kit.solidify(ob, 0.009 if kind == 'jacket' else 0.007, 0.0)
        if subsurf:
            s_ = ob.modifiers.new('Subsurf', 'SUBSURF')
            s_.levels = s_.render_levels = subsurf


def _bar_hanger(kit, M, nm, p, along, sh_y, yaw):
    """Oak slack (trouser) hanger: a single round-edged bar the trousers fold over."""
    rot = yaw if along == 'x' else math.pi / 2 - yaw          # matches the garments' width direction
    # boxes are built with their long side along local z (= across an x-rail)
    fr = Frame(p[0], p[1], rot)
    kit.box(f'{nm} bar', fr, (0, sh_y, 0), (0.036, 0.036, 1.22), M['hanger_wood'], 0.014, 2)


def closet_rod(kit, tag, a0, a1, c, y, along='x', r=0.04):
    """Round brushed-chrome closet rod between two side panels, with flange cups at both ends."""
    if along == 'x':
        kit.ctx.cylinder(f'{tag} rod', ((a0 + a1) / 2, y, c), r, a1 - a0, 'chrome', kit.cname, verts=24, axis='X')
        for a in (a0 + 0.012, a1 - 0.012):
            kit.ctx.cylinder(f'{tag} rod cup', (a, y, c), r + 0.035, 0.024, 'chrome', kit.cname, verts=24, axis='X')
    else:
        kit.ctx.cylinder(f'{tag} rod', (c, y, (a0 + a1) / 2), r, a1 - a0, 'chrome', kit.cname, verts=24, axis='Z')
        for a in (a0 + 0.012, a1 - 0.012):
            kit.ctx.cylinder(f'{tag} rod cup', (c, y, a), r + 0.035, 0.024, 'chrome', kit.cname, verts=24, axis='Z')
    kit.n += 3


def folded_stack(kit, M, fr, tag, n, w=1.0, d=0.85, t=0.2, seed=1):
    """Stack of folded knits / tees. Each item is two crisp soft layers so the fold line reads
    (not a pillow): lower layer ~55% of the thickness, upper one slightly inset."""
    import random
    rng = random.Random(seed)
    y = 0.0
    for i in range(n):
        ci = (i * 3 + seed) % len(GARMENTS)
        gm = _cloth(GARMENTS[ci])
        tt = t * rng.uniform(0.85, 1.1)
        h1 = tt * 0.55
        dx, dz, r = rng.uniform(-0.03, 0.03), rng.uniform(-0.02, 0.02), rng.uniform(-0.035, 0.035)
        kit.soft(f'{tag} folded {i} a', fr, (dx, y + h1 / 2, dz), (w, h1, d), gm, min(0.04, h1 * 0.42), 3, 0, lrot=r)
        h2 = tt - h1 + 0.006
        kit.soft(f'{tag} folded {i} b', fr, (dx - 0.012, y + h1 - 0.006 + h2 / 2, dz + 0.01), (w - 0.03, h2, d - 0.035),
                 gm, min(0.045, h2 * 0.45), 3, 0, lrot=r + 0.012)
        y += tt
    return y
