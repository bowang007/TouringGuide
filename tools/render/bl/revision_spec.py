"""Owner's design changes: plan positions shared by bl/revisions.py (Blender) and
apply_revisions_web.py (web data). SCENE feet on the architect's plan (x west->east, z rear->street)."""

# 7. kitchen skylight opening (plan's 3'-6" x 4'-0", next to the dishwasher) on the east roof plane
KITCHEN_SKY = (34.9, 38.4, 23.6, 27.6)
# 3. foyer skylights on the entry roof's east slope (its ridge runs down the foyer at x ~17.9)
FOYER_SKY = [(18.55, 20.65, 31.4, 34.4), (18.55, 20.65, 41.9, 44.7)]
# 4. primary bedroom sliding door (the old window W01 opening)
SLIDER_X = (2.45, 9.10)
SLIDER_HEAD = 7.0
# 6. primary bathroom window: between the vanity front (z 22.76) and the shower wet wall (z 25.23)
BATH_WIN_Z = (22.85, 24.85)
