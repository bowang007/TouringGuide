"""Television and media console for the living room's west wall (runs inside Blender).

Plan feet, like bl/zones/living.py. Both pieces stand on a wall whose room face is at `wall_x` and look east (+x);
`zc` is their centre line along the wall.

tv(): a wall-mounted flat screen (16:9; 75 in = 65.4 x 36.8 in picture). A thin panel with a 1/4 in bezel, a
shallower housing behind it and the mount plate on the wall, so from the side the set reads as a slab standing
1 7/8 in off the wall. The screen is dark glass that mirrors the room faintly; nothing on it is emissive. No cables:
the feed is in the wall.

console(): a low white-oak media console on two black steel sled legs. The top and bottom run over the ends, four
flat push-to-open doors sit a little behind the carcass edge with a dark shadow gap above them, and the grain runs
the length of the piece.
"""
import math

import bpy

from . import living_geo as G

COLL = 'zone_living'


def _principled(name, color, rough, **inputs):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = color + (1,)
    b.inputs['Roughness'].default_value = rough
    for k, v in inputs.items():
        b.inputs[k].default_value = v
    m.diffuse_color = color + (1,)
    return m


def screen_material():
    """A switched-off screen: near-black glass with a soft anti-glare reflection under a thin sharp one."""
    return _principled('Z_living_tv_screen', (0.004, 0.0045, 0.005), 0.22,
                       **{'IOR': 1.5, 'Coat Weight': 0.25, 'Coat Roughness': 0.03})


def body_material():
    return _principled('Z_living_tv_body', (0.012, 0.012, 0.013), 0.42)


def tv(ctx, parent, wall_x, zc, yc, diag_in=75.0):
    """Wall-mounted television centred on (zc, yc). Returns its extents: z0, z1, y0, y1 (outer edge of the
    bezel) and face_x (the screen)."""
    k = math.hypot(16.0, 9.0)
    w, h = diag_in * 16.0 / k / 12.0, diag_in * 9.0 / k / 12.0          # picture, ft
    bez, chin = 0.018, 0.032
    z0, z1 = zc - w / 2 - bez, zc + w / 2 + bez
    y0, y1 = yc - h / 2 - chin, yc + h / 2 + bez
    xm, xh, xp = wall_x + 0.045, wall_x + 0.105, wall_x + 0.150          # mount / housing / panel fronts
    face_x = xp + 0.003
    out = []
    v, f = G.box_verts(wall_x, xm, yc - 0.6, yc + 0.6, zc - 0.9, zc + 0.9)
    out.append(G.obj(ctx, 'living tv wall mount', v, f, 'black_metal', COLL, parent, smooth=False))
    v, f = G.box_verts(xm, xh, y0 + 0.35, y1 - 0.35, z0 + 0.4, z1 - 0.4)
    o = G.obj(ctx, 'living tv housing', v, f, body_material(), COLL, parent, smooth=False)
    G.bevel(o, 0.02, 3)
    out.append(o)
    v, f = G.box_verts(xh, xp, y0, y1, z0, z1)
    o = G.obj(ctx, 'living tv panel', v, f, body_material(), COLL, parent, smooth=False)
    G.bevel(o, 0.004, 2)
    out.append(o)
    v, f = G.box_verts(xp - 0.002, face_x, yc - h / 2, yc + h / 2, zc - w / 2, zc + w / 2)
    out.append(G.obj(ctx, 'living tv screen', v, f, screen_material(), COLL, parent, smooth=False))
    return {'z0': z0, 'z1': z1, 'y0': y0, 'y1': y1, 'face_x': face_x, 'objects': out}


def console(ctx, parent, wall_x, zc, L=7.5, D=1.4, top=1.7, leg_h=0.5, doors=4):
    """Low oak media console, its back 0.075 ft off the wall (clear of the baseboard). Returns its extents:
    x0, x1, z0, z1 and top."""
    oak = 'white_oak_veneer'
    t = 0.07                                   # carcass panel thickness
    x0, x1 = wall_x + 0.075, wall_x + 0.075 + D
    z0, z1 = zc - L / 2, zc + L / 2
    yb = leg_h                                 # underside of the carcass
    out = []

    def panel(name, bounds, mat=oak, bevel=0.006, grain=False):
        v, f = G.box_verts(*bounds)
        o = G.obj(ctx, name, v, f, mat, COLL, parent, smooth=False)
        if bevel:
            G.bevel(o, bevel, 2)
        if grain:
            o['tg_grain'] = 1                  # materials_pbr: grain along SCENE z on horizontal faces
        out.append(o)
        return o

    panel('living console top', (x0, x1, top - t, top, z0, z1), grain=True)
    panel('living console bottom', (x0, x1, yb, yb + t, z0, z1), grain=True)
    panel('living console end N', (x0, x1, yb + t, top - t, z0, z0 + t))
    panel('living console end S', (x0, x1, yb + t, top - t, z1 - t, z1))
    panel('living console back', (x0, x0 + 0.03, yb + t, top - t, z0 + t, z1 - t), bevel=0)
    # the dark inside, seen only through the door reveals and the finger gap above the doors
    panel('living console recess', (x0 + 0.03, x1 - 0.085, yb + t, top - t, z0 + t, z1 - t), 'paint_black', 0)
    gap, finger, dt = 0.012, 0.04, 0.06
    zo0, zo1 = z0 + t, z1 - t
    dw = (zo1 - zo0 - (doors + 1) * gap) / doors
    for i in range(doors):
        za = zo0 + gap + i * (dw + gap)
        panel(f'living console door {i + 1}', (x1 - 0.012 - dt, x1 - 0.012, yb + t + gap, top - t - finger, za, za + dw),
              bevel=0.005)
    # black steel sled legs
    tw, inset = 0.06, 0.08
    for tag, zl in (('N', z0 + 0.8), ('S', z1 - 0.8)):
        za, zb = zl - tw / 2, zl + tw / 2
        v, f = G.merge(G.box_verts(x0 + inset, x1 - inset, 0.0, tw, za, zb),
                       G.box_verts(x0 + inset, x1 - inset, yb - tw, yb, za, zb),
                       G.box_verts(x0 + inset, x0 + inset + tw, 0.0, yb, za, zb),
                       G.box_verts(x1 - inset - tw, x1 - inset, 0.0, yb, za, zb))
        o = G.obj(ctx, f'living console leg {tag}', v, f, 'black_metal', COLL, parent, smooth=False)
        G.bevel(o, 0.006, 2)
        out.append(o)
    return {'x0': x0, 'x1': x1, 'z0': z0, 'z1': z1, 'top': top, 'objects': out}
