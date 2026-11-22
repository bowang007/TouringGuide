#!/usr/bin/env bash
# Deploy a mirror of the site for visitors who cannot reach GitHub Pages (github.io is unreliable from mainland
# China). Only index.html and assets/ are uploaded: tools/, sizes/, styles/ (third-party reference images) and the
# old single-file walkthrough stay out of the mirror.
#
#   tools/web/deploy_mirror.sh             upload the working tree's page to the mirror (default host: netlify)
#   tools/web/deploy_mirror.sh --dry-run   only build the upload folder and print what would be sent
#
# MIRROR_HOST=netlify (default): https://mckinley-house-tour.netlify.app
#   Needs no domain. Sign in once on this machine: `npx netlify-cli@17 login` (the token is kept in
#   ~/.config/netlify). A netlify.app address was reachable from most mainland test locations in mid-2026 but can
#   be slow; have someone there try it. New free accounts protect every site with a Netlify login: that
#   "team login protection" is switched off for this site (site setting sso_login = false). The free plan puts a
#   "Powered by Netlify" badge in the lower right corner; the page lifts its controls clear of it (tour.css
#   .host-badge, set in main.js on *.netlify.app).
#   NETLIFY_SITE   site name or id (default: mckinley-house-tour)
#   NETLIFY_CLI    CLI version (default 17: the last that runs on Node 18; newer ones need Node 22)
#
# MIRROR_HOST=edgeone: Tencent EdgeOne Pages ("EdgeOne Makers")
#   Needs an API token (https://edgeone.ai, Pages console, tab "API Token") in ~/.edgeone_token or
#   $EDGEONE_API_TOKEN, and a domain name added to the project in the console: the project's own address serves
#   mainland visitors only through preview links that expire after 3 hours; a custom domain in the area
#   "Global AZ (excluding Chinese mainland)" (EDGEONE_AREA=overseas, the default) needs no ICP filing.
#   EDGEONE_PROJECT (default: house-tour), EDGEONE_AREA (overseas | global), EDGEONE_CLI (default 1.7.6)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOST="${MIRROR_HOST:-netlify}"
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

case "$HOST" in
  netlify)
    SITE="${NETLIFY_SITE:-mckinley-house-tour}"
    CLI="netlify-cli@${NETLIFY_CLI:-17}"
    echo "host: netlify   site: $SITE   cli: $CLI"
    if [[ $DRY == 1 ]]; then echo "dry run: nothing uploaded"; exit 0; fi
    npx --yes "$CLI" deploy --prod --dir "$OUT" --site "$SITE" --message "tour $VERSION" --timeout 900
    ;;
  edgeone)
    PROJECT="${EDGEONE_PROJECT:-house-tour}"
    AREA="${EDGEONE_AREA:-overseas}"
    CLI="edgeone@${EDGEONE_CLI:-1.7.6}"
    echo "host: edgeone   project: $PROJECT   area: $AREA   cli: $CLI"
    if [[ $DRY == 1 ]]; then echo "dry run: nothing uploaded"; exit 0; fi
    TOKEN="${EDGEONE_API_TOKEN:-}"
    if [[ -z "$TOKEN" && -f "$HOME/.edgeone_token" ]]; then TOKEN="$(tr -d ' \n\r' < "$HOME/.edgeone_token")"; fi
    if [[ -z "$TOKEN" ]]; then
      echo "no API token: set EDGEONE_API_TOKEN or write the token to ~/.edgeone_token (see the header of this script)" >&2
      exit 2
    fi
    npx --yes "$CLI" makers deploy "$OUT" -n "$PROJECT" -a "$AREA" -t "$TOKEN"
    ;;
  *) echo "unknown MIRROR_HOST '$HOST' (netlify or edgeone)" >&2; exit 2 ;;
esac
