"""Owner's design changes: plan positions shared by bl/revisions.py (Blender) and
apply_revisions_web.py (web data). SCENE feet on the architect's plan (x west->east, z rear->street)."""

# 7. kitchen skylight opening (plan's 3'-6" x 4'-0", next to the dishwasher) on the east roof plane
KITCHEN_SKY = (34.9, 38.4, 23.6, 27.6)
# 3. foyer skylights on the entry roof's east slope (its ridge runs down the middle of the foyer, x ~18.33
#    since the foyer-side wall lines up with the shared bath, relayout.FOYER_WALL)
FOYER_SKY = [(18.75, 20.75, 31.4, 34.4), (18.75, 20.75, 41.9, 44.7)]
# 1. Bedroom 4 (office) flat ceiling: west wall centre .. foyer-side wall centre, north .. south wall centre
OFFICE_CEILING = (0.0, 15.265, 28.54, 36.90)
# 4. primary bedroom sliding door (the old window W01 opening)
SLIDER_X = (2.45, 9.10)
SLIDER_HEAD = 7.0
# 6. primary bathroom window: between the vanity front (z 22.76) and the shower wet wall (z 25.23)
BATH_WIN_Z = (22.85, 24.85)
# owner's change 2026-11-19 (third round): Bedroom 2's rear window and the primary bath window no longer run to the
# floor; both stop at a 2'-0" sill and keep their heads at the 8 ft ceiling
TALL_SILL = 2.0
# the concept bath window opening (warped to the new plan) that the bath's wall finish is built around
BATH_OLD_HOLE_Y = (5.0, 7.0)
# owner's change 2026-11-19: a skylight over the shower (x 0.36..4.97, z 25.27..28.30), clear of the rain
# head (x <= 2.44) and on the single west roof plane, 2'-0" x 2'-6"
PRIMARY_BATH_SKY = (2.7, 4.7, 25.55, 28.05)
