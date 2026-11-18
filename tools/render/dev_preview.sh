#!/usr/bin/env bash
# Build a scene with the given zone module(s) and render review images for the given nodes.
#   tools/render/dev_preview.sh <zones> <nodes> [width=1536] [samples=128]
# e.g. tools/render/dev_preview.sh kitchen_dining K0,D0,H2
# Output: tools/render/.cache/dev_<first-zone>/<NODE>.png (equirect), <NODE>_sheet.png (4 views)
# Each zone gets its own .blend/output dir so several builds can run in parallel.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-blender}"
ZONES="$1"; NODES="$2"; WIDTH="${3:-1536}"; SAMPLES="${4:-128}"
TAG="${ZONES%%,*}"
OUT="$HERE/.cache/dev_$TAG"
mkdir -p "$OUT"
"$BLENDER" -b --factory-startup -noaudio --python "$HERE/build_scene.py" -- --zones "$ZONES" --out "$OUT/scene.blend" 2>&1 \
  | grep -vE 'HIPEW|^Blender|^Read blend|^$' | tail -25
"$HERE/gpu.sh" -b "$OUT/scene.blend" -noaudio --python "$HERE/render_panos.py" -- --nodes "$NODES" --width "$WIDTH" \
  --samples "$SAMPLES" --out "$OUT" 2>&1 | grep -E '\[render\]|Error|Traceback|line [0-9]+' || true
PY="${TG_PYTHON:-$HERE/.cache/venv/bin/python}"
"$PY" - "$OUT" "$NODES" "$HERE" <<'EOF'
import json, sys, os
sys.path.insert(0, sys.argv[3])
from PIL import Image
import pano_views as pv
out, nodes = sys.argv[1], sys.argv[2].split(',')
scene = json.load(open(os.path.join(sys.argv[3], 'data', 'scene.json')))
yaw = {n['id']: n['yaw'] for n in scene['tour']['nodes']}
for n in nodes:
    p = os.path.join(out, n + '.png')
    if not os.path.exists(p):
        print('missing', p); continue
    ims = pv.views(Image.open(p).convert('RGB'), [0, 90, 180, 270], 90, -8, (800, 500), yaw.get(n, 0.0))
    pv.sheet(ims, [f'{n} yaw{d:+d}' for d in (0, 90, 180, 270)]).save(os.path.join(out, n + '_sheet.png'))
    print('review:', os.path.join(out, n + '_sheet.png'))
EOF
