#!/usr/bin/env bash
# Render review panoramas from an already-built .blend and cut 4-view contact sheets.
#   tools/render/review.sh <scene.blend> <nodes|all> <outdir> [width=1536] [samples=128] [extra render_panos args...]
# Output: <outdir>/<NODE>.png (equirect), <NODE>_sheet.png (4 x 90deg views from the node's yaw)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-blender}"
BLEND="$1"; NODES="$2"; OUT="$3"; WIDTH="${4:-1536}"; SAMPLES="${5:-128}"
shift $(( $# < 5 ? $# : 5 ))
mkdir -p "$OUT"
# drop stale results first, so a failed render can never pass for a fresh one
if [ "$NODES" = all ]; then rm -f "$OUT"/??.png "$OUT"/??_sheet.png; else for n in ${NODES//,/ }; do rm -f "$OUT/$n.png" "$OUT/${n}_sheet.png"; done; fi
"$HERE/gpu.sh" -b "$BLEND" -noaudio --python "$HERE/render_panos.py" -- --nodes "$NODES" --width "$WIDTH" \
  --samples "$SAMPLES" --out "$OUT" "$@" 2>&1 | grep -E '\[render\]|\[wb\]|Error|Traceback|line [0-9]+' || true
PY="${TG_PYTHON:-$HERE/.cache/venv/bin/python}"
"$PY" - "$OUT" "$NODES" "$HERE" <<'PYEOF'
import json, sys, os
sys.path.insert(0, sys.argv[3])
from PIL import Image
import pano_views as pv
out = sys.argv[1]
scene = json.load(open(os.path.join(sys.argv[3], 'data', 'scene.json')))
yaw = {n['id']: n['yaw'] for n in scene['tour']['nodes']}
nodes = list(yaw) if sys.argv[2] == 'all' else sys.argv[2].split(',')
for n in nodes:
    p = os.path.join(out, n + '.png')
    if not os.path.exists(p):
        print('missing', p); continue
    ims = pv.views(Image.open(p).convert('RGB'), [0, 90, 180, 270], 90, -8, (800, 500), yaw.get(n, 0.0))
    pv.sheet(ims, [f'{n} yaw{d:+d}' for d in (0, 90, 180, 270)]).save(os.path.join(out, n + '_sheet.png'))
print('sheets in', out)
PYEOF
