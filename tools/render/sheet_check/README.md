# sheet_check: the built model against the architect's sheet

Measures a built `.blend` against sheet SKA002 of `sizes/sizes.pdf` (and A1.3's heights, SKA001's
site numbers). It is the script the eighth round's integration used, kept here so that the check
outlives that round. It casts rays on a dump of the built meshes and reads no number of the source
code: what a constant says is not evidence.

## Run

From the repository root, CPU only, about two minutes. Nothing is written into the `.blend`, the
repository or `tools/render/.cache`; both prefixes are yours (a scratch folder).

```bash
$BLENDER -b <build>.blend -noaudio --python tools/render/sheet_check/extract.py -- <dump prefix>
DUMP=<dump prefix> $BLENDER -b -noaudio --python tools/render/sheet_check/measure.py -- <out prefix>
grep -n 'Counts' <out prefix>.md; grep -c 'small\|DIFFERS' <out prefix>.md
```

* `extract.py` writes `<dump prefix>.npz` (115 MB: vertices, triangles and the owner of each
  triangle, in SCENE feet) and `<dump prefix>.json` (name, collections and box of each object):
  the shell, the openings, the exterior shell, the six interior zones, and the site, fences and
  garage door of the exterior zone (no plants).
* `measure.py` reads the dump named by `DUMP` and writes `<out prefix>.md` (the tables below; it
  also prints them) and `<out prefix>.json` (every measured value).

## What it must print

On the eighth round's final build (`house_v7d.blend`, 2026-11-24):

```
Counts: {'match': 33, 'owner': 6}          # line 46 of the .md, under "1. SKA002: the 39 printed dimensions"
0                                          # rows that read `small` or `DIFFERS`
```

`match` is within 1/2 in of the sheet, `small` within 2 in, `DIFFERS` beyond; `owner` is a
decision of the owner's that the sheet does not show (`tools/render/DESIGN.md`, "Eighth round").
A clean model has no `small` and no `DIFFERS` row in any table:

| Table | Rows on `house_v7d.blend` |
|---|---|
| 1. SKA002: the 39 printed dimensions | 33 match, 6 owner (rows 11 and 34: the laundry closet; 12, 13, 18, 20: the foyer-side wall) |
| 1b. Overall sizes and ceilings | 13 match |
| 2. Doors of SKA002 | 16 match, 4 owner |
| 3. Windows of SKA002 | 6 match, 3 owner, 1 leftover symbol of the sheet, 2 in the model only (W14, W17) |
| 4. Skylights | 1 match (living room), 1 size match with the owner's place (kitchen), 3 owner |
| 5. Landings, porch, ground, driveway, garage floor | 49 match, 17 without a sheet value |
| 6. Roof | 36 match, 5 owner, 5 without a sheet value; every pitch sample 5.0000 in 12 |
| 7. Kitchen | 10 match, 7 owner or without a sheet value |

(`grep -c '| match |' <out prefix>.md` prints 158: the rows whose verdict is the bare word.)

## Where the expected value is a decision, not the sheet

* **The porch.** The set gives no level for the new covered porch: A1.3 draws the existing one,
  4 in below the floor (−0.336), which leaves risers of 7 in and 4 in. The round built the slab
  half way between the front walk and the house floor. The rows `Porch slab top` (−0.4583),
  `Porch riser to the walk, in` and `Porch riser to the house floor, in` (5 1/2 in each) expect
  that. If the level changes on purpose (`PORCH_TOP` in `bl/zones/exterior_layout.py`), change
  `PORCH_TOP` and `PORCH_RISER_IN` in `measure.py` with it; until then the rows read `small` or
  `DIFFERS`, which is what they are for.
* **The owner's decisions** are marked `owner` in `measure.py` where each row is measured, with
  the round that made them.

## Files

| File | |
|---|---|
| `extract.py` | the dump (runs inside Blender on the built `.blend`) |
| `measure.py` | the measurements and the tables (runs inside Blender for its BVH; opens no `.blend`) |
| `cq.py` | ray queries on the dump (`DUMP`), used by `measure.py` |
| `ska002_geometry.json` | every wall, room, door, window, skylight, fixture, landing and step of SKA002 in the model's coordinates (x west to east, z rear to street, feet; x = (X − 1107.075) / 18, z = (Y − 361.808) / 18 from PDF points), with a legend |
| `pdf_dimensions.json` | the 39 dimensions printed on SKA002, each with what it measures |
| `heights_site.json` | A1.3's heights and SKA001's site numbers |

The three JSON files were extracted from the PDF's vector data by the eighth round's audit; they
change only when the architect's set does.
