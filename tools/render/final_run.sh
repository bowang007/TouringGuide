#!/usr/bin/env bash
# Full production run of the v3 tour:
#   build -> probe pass -> smooth exposure -> panoramas -> hero stills -> web bake -> adapt -> exterior frames
#
#   BLENDER=/path/to/blender tools/render/final_run.sh [width=8192] [samples=192]
#
# Stages (skip any with SKIP, e.g. SKIP="build probe smooth" to resume a run that stopped in the panoramas):
#   build     build_scene.py --zones all --strict             -> .cache/house.blend
#   probe     render_panos.py --preview-only (all sweeps)      -> .cache/panos_probe/{render_meta.json,<ID>_view.png}
#             the automatic exposure / white balance of every sweep, a few seconds each, no panorama
#   smooth    smooth_exposure.py                               -> .cache/panos/pins.json
#             relaxes those values along the tour graph (linked sweeps within ~0.3 stop / 300 K)
#   panos     render_panos.py --pins --skip-existing           -> .cache/panos/{<ID>.png,render_meta.json}
#             <width> x <width/2>, 8-bit RGB; a restart continues with the sweeps that are missing
#   heroes    render_heroes.py (2400 px, 1024 samples)         -> .cache/heroes/<key>.png
#   bake      bake_web.py --detail $BAKE_DETAIL                -> .cache/web/{house.glb,collision.json,house.*.json}
#   adapt     adapt_web.py                                     -> .cache/web/adapt.json
#   exterior  render_exterior.py (3000 px, 512 samples)        -> .cache/exterior/
#
# Every stage is logged with timestamps to .cache/logs/final_run.log (full output of a stage:
# .cache/logs/<stage>.log). The script stops with a non-zero exit code as soon as a stage fails.
#
# Environment:
#   SKIP          space-separated stage names to skip (default: none)
#   NODES         sweeps for the probe and panorama stages (default: all)
#   PANO_ARGS     extra arguments for the panorama pass, e.g. "--adaptive-threshold 0.02 --adaptive-min 96"
#   SMOOTH_ARGS   extra arguments for smooth_exposure.py, e.g. "--move-kelvin 900"
#   BAKE_DETAIL   texel-density boost for floors and furniture in the web model (default 2; budget 320 MB)
#   BAKE_ARGS     extra arguments for bake_web.py
#   TG_CACHE      output directory (default tools/render/.cache)
#
# The run does not publish. Afterwards (from the repository root, PY=tools/render/.cache/venv/bin/python):
#   $PY tools/web/publish_panos.py tools/render/.cache/panos --prune     # assets/panos/{8k,4k,2k}, thumbs, manifest
#   $PY tools/web/publish_design.py tools/render/.cache/heroes           # assets/design
#   cp tools/render/.cache/web/house.glb assets/model/house.glb          # web model (the page reads only this;
#                                                                        # adapt.json / collision.json stay in .cache)
#   $PY tools/web/publish_exterior.py tools/render/.cache/exterior       # assets/exterior
#   python3 tools/web/build_site_data.py --version <YYYY-MM-DDx>         # assets/data/*.json + ?v= tokens
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-blender}"
export BLENDER
WIDTH="${1:-8192}"; SAMPLES="${2:-192}"
SKIP="${SKIP:-}"
NODES="${NODES:-all}"
BAKE_DETAIL="${BAKE_DETAIL:-2}"
C="${TG_CACHE:-$HERE/.cache}"
PY="${TG_PYTHON:-python3}"
LOGS="$C/logs"
LOG="$LOGS/final_run.log"
mkdir -p "$C/panos" "$C/panos_probe" "$C/heroes" "$C/web" "$C/exterior" "$LOGS"
BL=(-noaudio --python-exit-code 1)

log() { echo "[final $(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

# stage <name> <grep pattern of the lines worth showing> <command...>
stage() {
  local name="$1" keep="$2"; shift 2
  if [[ " $SKIP " == *" $name "* ]]; then log "SKIP  $name"; return 0; fi
  local slog="$LOGS/$name.log" t0 rc
  t0=$(date +%s)
  log "START $name"
  set +e
  "$@" 2>&1 | tee "$slog" | grep --line-buffered -v 'HIPEW' \
    | grep --line-buffered -E "$keep|Error|Traceback|FAILED|WARNING" | sed -u 's/^/    /' | tee -a "$LOG"
  rc=${PIPESTATUS[0]}
  set -e
  # Blender exits 0 when a zone or a revision caught its own exception: the log is the witness
  if [ "$rc" -eq 0 ] && grep -qE 'Traceback \(most recent call last\)|FAILED' "$slog"; then rc=97; fi
  if [ "$rc" -ne 0 ]; then
    log "FAIL  $name (exit $rc after $(( $(date +%s) - t0 )) s); full output: $slog"
    exit "$rc"
  fi
  log "DONE  $name ($(( $(date +%s) - t0 )) s)"
}

# (a stage runs inside a pipeline, where `set -e` does not reach: every command returns its own failure)
build() {
  "$BLENDER" -b --factory-startup "${BL[@]}" --python "$HERE/build_scene.py" -- --zones all --strict \
    --out "$C/house.blend" || return $?
  test -f "$C/house.blend"
}

probe() {
  rm -f "$C/panos_probe/render_meta.json"          # always a fresh probe of the scene as built
  "$HERE/gpu.sh" -b "$C/house.blend" "${BL[@]}" --python "$HERE/render_panos.py" -- --nodes "$NODES" \
    --preview-only --preview-width 480 --samples 16 --out "$C/panos_probe" || return $?
  test -s "$C/panos_probe/render_meta.json"
}

smooth() {
  # shellcheck disable=SC2086
  "$PY" "$HERE/smooth_exposure.py" --meta "$C/panos_probe/render_meta.json" --out "$C/panos/pins.json" ${SMOOTH_ARGS:-}
}

panos() {
  test -s "$C/panos/pins.json" || { echo "Error: $C/panos/pins.json is missing (run the probe and smooth stages)"; return 1; }
  # shellcheck disable=SC2086
  "$HERE/gpu.sh" -b "$C/house.blend" "${BL[@]}" --python "$HERE/render_panos.py" -- --nodes "$NODES" \
    --width "$WIDTH" --samples "$SAMPLES" --pins "$C/panos/pins.json" --skip-existing --out "$C/panos" ${PANO_ARGS:-} \
    || return $?
  # every sweep of the tour (or of $NODES) must have its panorama now
  "$PY" - "$HERE/data/scene.json" "$C/panos" "$NODES" "$WIDTH" <<'PYEOF'
import json, os, struct, sys
scene, out, nodes, width = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
ids = [n['id'] for n in json.load(open(scene))['tour']['nodes']]
if nodes != 'all':
    ids = [i for i in ids if i in nodes.split(',')]
bad = []
for i in ids:
    p = os.path.join(out, i + '.png')
    try:
        with open(p, 'rb') as f:
            head = f.read(24)
        if struct.unpack('>I', head[16:20])[0] != width:
            bad.append(i + ' (wrong width)')
    except (OSError, struct.error):
        bad.append(i + ' (missing)')
if bad:
    sys.exit('Error: panoramas not complete: ' + ', '.join(bad))
print(f'[render] all {len(ids)} panoramas present at {width} px')
PYEOF
}

heroes() {
  "$HERE/gpu.sh" -b "$C/house.blend" "${BL[@]}" --python "$HERE/render_heroes.py" -- --width 2400 --samples 1024 \
    --out "$C/heroes"
}

bake() {
  # shellcheck disable=SC2086
  "$HERE/gpu.sh" -b "$C/house.blend" "${BL[@]}" --python "$HERE/bake_web.py" -- --out "$C/web/house.glb" \
    --meta "$C/panos/render_meta.json" --detail "$BAKE_DETAIL" ${BAKE_ARGS:-}
}

adapt() {
  "$BLENDER" -b "$C/house.blend" "${BL[@]}" --python "$HERE/adapt_web.py" -- --meta "$C/panos/render_meta.json" \
    --bake-summary "$C/web/house.summary.json" --out "$C/web/adapt.json"
}

exterior() {
  "$HERE/gpu.sh" -b "$C/house.blend" "${BL[@]}" --python "$HERE/render_exterior.py" -- --width 3000 --samples 512 \
    --force --out "$C/exterior"
}

T0=$(date +%s)
log "final run: panoramas ${WIDTH}x$(( WIDTH / 2 )) at ${SAMPLES} samples, sweeps: ${NODES}, skip: ${SKIP:-nothing}, blender: $BLENDER"
stage build    '^zone|^shell|^warp|^revisions|^portals|^saved'            build
stage probe    '\[render\]'                                                 probe
stage smooth   'smooth_exposure|max link|links over|largest move|wrote|!$'  smooth
stage panos    '\[render\]'                                                 panos
stage heroes   '\[hero\]'                                                   heroes
stage bake     '^\[bake\] (metal|exposure|texture|plan|collision|exported)|dropped' bake
stage adapt    '^\[adapt\] (house|wrote)'                                   adapt
stage exterior '\[exterior\]'                                               exterior
log "done in $(( ($(date +%s) - T0) / 60 )) min; publish commands: see the header of $0"
