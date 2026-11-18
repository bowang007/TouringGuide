#!/usr/bin/env bash
# Run a GPU (Cycles) Blender job under a machine-wide lock so parallel agents/scripts don't exhaust
# GPU memory:   tools/render/gpu.sh <blender args...>     (uses $BLENDER, default 'blender')
HERE="$(cd "$(dirname "$0")" && pwd)"
LOCK="${TG_GPU_LOCK:-$HERE/.cache/gpu.lock}"
mkdir -p "$(dirname "$LOCK")"
exec flock "$LOCK" "${BLENDER:-blender}" "$@"
