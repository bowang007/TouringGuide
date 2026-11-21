#!/usr/bin/env bash
# Deploy a mirror of the site to Tencent EdgeOne Pages (now "EdgeOne Makers"), for visitors who cannot reach
# GitHub Pages (github.io is unreliable from mainland China).
#
#   tools/web/deploy_mirror.sh             upload index.html + assets/ as they are in the working tree
#   tools/web/deploy_mirror.sh --dry-run   only build the upload folder and print what would be sent
#
# What you need once (the script cannot do these for you):
#   1. An EdgeOne account (https://edgeone.ai, "Global" site) and an API token from the Pages / Makers console
#      (tab "API Token"). Put the token in ~/.edgeone_token (chmod 600) or in $EDGEONE_API_TOKEN.
#   2. A domain name you own, added to the project in the console. The project's own address serves visitors in
#      mainland China only through preview links that expire after 3 hours; a custom domain in the area
#      "Global AZ (excluding Chinese mainland)" needs no ICP filing. That area is what "-a overseas" selects here.
#
# Environment:
#   EDGEONE_PROJECT   project name (default: house-tour); created on the first run, updated afterwards
#   EDGEONE_AREA      overseas (default: nodes outside mainland China, no ICP filing) or global (needs a filed domain)
#   EDGEONE_CLI       CLI version (default 1.7.6, run through npx)
#
# Only the page and its assets are uploaded. tools/, sizes/, styles/ (third-party reference images) and the old
# single-file walkthrough stay out of the mirror.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT="${EDGEONE_PROJECT:-house-tour}"
AREA="${EDGEONE_AREA:-overseas}"
CLI="edgeone@${EDGEONE_CLI:-1.7.6}"
DRY=0; [[ "${1:-}" == "--dry-run" ]] && DRY=1

OUT="$(mktemp -d "${TMPDIR:-/tmp}/tour-mirror.XXXXXX")"
trap 'rm -rf "$OUT"' EXIT
cp "$ROOT/index.html" "$OUT/"
cp -r "$ROOT/assets" "$OUT/assets"
VERSION="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "$OUT/assets/data/tour.json")"
FILES="$(find "$OUT" -type f | wc -l)"
SIZE="$(du -sh "$OUT" | cut -f1)"
BIG="$(find "$OUT" -type f -size +20M | wc -l)"
echo "mirror folder: $FILES files, $SIZE, site version $VERSION, files over 20 MB: $BIG"
echo "project: $PROJECT   area: $AREA   cli: $CLI"
if [[ $DRY == 1 ]]; then echo "dry run: nothing uploaded"; exit 0; fi

TOKEN="${EDGEONE_API_TOKEN:-}"
if [[ -z "$TOKEN" && -f "$HOME/.edgeone_token" ]]; then TOKEN="$(tr -d ' \n\r' < "$HOME/.edgeone_token")"; fi
if [[ -z "$TOKEN" ]]; then
  echo "no API token: set EDGEONE_API_TOKEN or write the token to ~/.edgeone_token (see the header of this script)" >&2
  exit 2
fi
npx --yes "$CLI" makers deploy "$OUT" -n "$PROJECT" -a "$AREA" -t "$TOKEN"
