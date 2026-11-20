"""Vintage light fittings for the kitchen and dining table (replace the linear LED bars):

* island: two brass-and-glass bell pendants (clear seeded glass bell, ribbed brass gallery and rim,
  brass rod and ceiling canopy, a warm filament bulb inside);
* dining table: one brass cylinder lantern (domed brass crown with a ring finial, four slim brass
  posts, clear glass, a brass bowl underneath, three candle bulbs) on a brass rod.

Glass is materials.thin_glass (no refraction: light passes); the glow is an emitter on the bulbs plus
a point light inside each fitting (lighting.apply_balance scales both at render time).
"""
import math

from . import kitchen_dining_mats as KM
from .kitchen_dining_geo import Geo

CEIL = 8.0


def _canopy(g, name, x, z, brass, col, r=0.2):
    g.lathe(name, [(0.0, CEIL - 0.13), (0.06, CEIL - 0.13), (r * 0.8, CEIL - 0.1), (r, CEIL - 0.04), (r, CEIL - 0.002),
                   (0.0, CEIL - 0.002)], x, z, brass, 48, col, sharp_deg=60)


def bell_pendant(g, name, x, z, y_bot, col, lights, r=0.43, h=0.62):
    """Bell pendant with its glass rim at y_bot (light amber glass)."""
    from ..lighting import emitter
    brass, glass = KM.brass(), KM.glass_amber()
    bulb = emitter('kd_filament', 2400, 60.0)
    yt = y_bot + h
    _canopy(g, f'{name} canopy', x, z, brass, col)
    g.cyl(f'{name} rod', x, yt + 0.12, CEIL - 0.12, z, 0.016, brass, 16, col)
    # gallery (fitter) with a ribbed collar
    g.lathe(f'{name} fitter', [(0.0, yt + 0.12), (0.035, yt + 0.12), (0.045, yt + 0.09), (0.11, yt + 0.06), (0.13, yt + 0.02),
                               (0.13, yt - 0.03), (0.11, yt - 0.04), (0.0, yt - 0.04)], x, z, brass, 48, col, sharp_deg=50)
    # bell glass: narrow shoulder flaring to the rim (single surface)
    prof = []
    for k in range(17):
        t = k / 16
        rr = 0.11 + (r - 0.11) * (math.sin(t * math.pi / 2) ** 1.6 * 0.55 + t ** 2.2 * 0.45)
        prof.append((rr, yt - 0.03 - (h - 0.03) * t))
    g.lathe(f'{name} shade', prof[::-1], x, z, glass, 64, col, sharp_deg=80)
    g.torus(f'{name} rim', x, y_bot, z, r, 0.012, brass, 96, 10, col)
    # bulb: a 'globe' filament lamp hanging in the bell
    g.cyl(f'{name} socket', x, yt - 0.2, yt - 0.04, z, 0.04, brass, 24, col)
    # smooth G25-style globe (a 7-point profile with 50 deg sharp edges read as a cut gem up close)
    R, cy = 0.085, 0.09
    prof = [(R * math.sin(math.pi * k / 16), cy - R * math.cos(math.pi * k / 16)) for k in range(14)]
    prof = [(0.0, cy - R)] + prof[1:] + [(0.03, 0.19), (0.025, 0.2), (0.0, 0.2)]
    g.lathe(f'{name} bulb', prof, x, z, bulb, 40, col, y_base=yt - 0.4, sharp_deg=89)
    g.point_light(f'{name} light', x, yt - 0.3, z, 40.0, 2600, 0.12, lights)
    g.point_light(f'{name} uplight', x, yt + 0.05, z, 6.0, 2600, 0.1, lights)


def lantern(g, name, x, z, y_bot, col, lights, r=0.52, h=1.25):
    """Brass cylinder lantern (19in tall body, 12.5in diameter)."""
    from ..lighting import emitter
    brass, glass = KM.brass(), KM.glass_seeded()
    bulb = emitter('kd_candle', 2400, 45.0)
    y0, y1 = y_bot + 0.18, y_bot + 0.18 + h
    _canopy(g, f'{name} canopy', x, z, brass, col, 0.24)
    g.cyl(f'{name} rod', x, y1 + 0.42, CEIL - 0.12, z, 0.02, brass, 16, col)
    g.torus(f'{name} loop', x, y1 + 0.38, z, 0.06, 0.012, brass, 32, 8, col)
    # brass bowl under the glass and the domed crown with finial
    g.lathe(f'{name} bowl', [(0.0, y_bot), (0.05, y_bot), (0.1, y_bot + 0.02), (r * 0.7, y_bot + 0.08), (r + 0.03, y0 - 0.02),
                             (r + 0.04, y0 + 0.02), (0.0, y0 + 0.02)], x, z, brass, 64, col, sharp_deg=50)
    g.lathe(f'{name} crown', [(0.0, y1 - 0.02), (r + 0.04, y1 - 0.02), (r + 0.05, y1 + 0.02), (r * 0.85, y1 + 0.08),
                              (r * 0.5, y1 + 0.2), (0.12, y1 + 0.27), (0.05, y1 + 0.3), (0.05, y1 + 0.36), (0.0, y1 + 0.36)],
            x, z, brass, 64, col, sharp_deg=50)
    # glass cylinder and four posts
    g.lathe(f'{name} glass', [(r, y0 + 0.02), (r, y1 - 0.02)], x, z, glass, 64, col, smooth=True)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        px, pz = x + (r + 0.012) * math.cos(a), z + (r + 0.012) * math.sin(a)
        g.cyl(f'{name} post', px, y0, y1, pz, 0.016, brass, 12, col)
    # three candle bulbs on a cluster
    g.cyl(f'{name} cluster stem', x, y0 + 0.02, y0 + 0.35, z, 0.025, brass, 16, col)
    for k in range(3):
        a = k * 2 * math.pi / 3
        cx, cz = x + 0.17 * math.cos(a), z + 0.17 * math.sin(a)
        g.cyl_axis(f'{name} cluster arm', (x, y0 + 0.3, z), (cx, y0 + 0.3, cz), 0.014, brass, 10, col)
        g.cyl(f'{name} candle sleeve', cx, y0 + 0.3, y0 + 0.52, cz, 0.032, KM.stoneware('candle_sleeve', '#efe9dc', 0.5, 0.0),
              20, col)
        g.lathe(f'{name} candle bulb', [(0.0, 0.0), (0.022, 0.01), (0.03, 0.05), (0.022, 0.1), (0.0, 0.13)], cx, cz, bulb, 20,
                col, y_base=y0 + 0.52)
    g.point_light(f'{name} light', x, y0 + 0.65, z, 45.0, 2500, 0.2, lights)
