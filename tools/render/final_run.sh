#!/usr/bin/env bash
# Full production run: build -> 27 panoramas -> hero stills -> baked web model.
#   BLENDER=/path/to/blender tools/render/final_run.sh [width=4096] [samples=768]
# Outputs in tools/render/.cache/{house.blend,panos,heroes,web}. Publish afterwards with:
#   .cache/venv/bin/python ../web/publish_panos.py .cache/panos
#   .cache/venv/bin/python ../web/publish_design.py .cache/heroes
#   cp .cache/web/house.glb .cache/web/collision.json .cache/web/adapt.json ../../assets/model/
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-blender}"
export BLENDER
WIDTH="${1:-4096}"; SAMPLES="${2:-768}"
C="$HERE/.cache"
mkdir -p "$C/panos" "$C/heroes" "$C/web"
log() { echo "[final $(date +%H:%M:%S)] $*"; }

log "build"
"$BLENDER" -b --factory-startup -noaudio --python "$HERE/build_scene.py" -- --zones all --strict --out "$C/house.blend" \
  2>&1 | grep -E '^zone|^shell|saved|Error|Traceback' || true
test -f "$C/house.blend"

log "panoramas ${WIDTH}px ${SAMPLES}spp"
"$HERE/gpu.sh" -b "$C/house.blend" -noaudio --python "$HERE/render_panos.py" -- --nodes all \
  --width "$WIDTH" --samples "$SAMPLES" --out "$C/panos" 2>&1 | grep -E '\[render\]|\[balance\]|Error|Traceback' || true

log "hero stills"
"$HERE/gpu.sh" -b "$C/house.blend" -noaudio --python "$HERE/render_heroes.py" -- --width 2400 --samples 1024 \
  --out "$C/heroes" 2>&1 | grep -E '\[hero\]|Error|Traceback' || true

log "web bake"
"$HERE/gpu.sh" -b "$C/house.blend" -noaudio --python "$HERE/bake_web.py" -- --out "$C/web/house.glb" \
  --meta "$C/panos/render_meta.json" 2>&1 | grep -E '^\[bake\] (metal|exposure|groups|collision|exported)|dropped|Error|Traceback' || true

log "walk eye adaptation"
"$BLENDER" -b "$C/house.blend" -noaudio --python "$HERE/adapt_web.py" -- --meta "$C/panos/render_meta.json" \
  --out "$C/web/adapt.json" 2>&1 | grep -E '^\[adapt\] wrote|Error|Traceback' || true
log "done"
