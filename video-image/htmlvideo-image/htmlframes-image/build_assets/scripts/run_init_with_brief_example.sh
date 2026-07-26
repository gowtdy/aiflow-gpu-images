#!/usr/bin/env bash
# Debug wrapper for init_with_brief.py — edit flags below, then:
#   bash build_assets/scripts/run_init_with_brief_example.sh
# Extra args are forwarded (e.g. --dry-run, --json, --data-dir /tmp/videos).
# After init completes, runs assemble-index.mjs → <project>/index.html.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SCRIPT="${SCRIPT_DIR}/init_with_brief.py"
ASSEMBLE_SCRIPT="${SCRIPT_DIR}/assemble-index.mjs"

NAME="first-video"
DATA_DIR="/app/videos"
PROJECT_DIR="${DATA_DIR}/${NAME}"

python3 "${INIT_SCRIPT}" \
  --name "${NAME}" \
  --data-dir "${DATA_DIR}" \
  --example blank \
  --skip-skills \
  --topic "如何选择一支股票？" \
  --aspect 1920x1080 \
  --language zh \
  --length 40s \
  --angle practitioner \
  --angle how-to \
  --tone humorous \
  --audience "everyday investors" \
  --preset capsule \
  "$@"

echo "assemble-index → ${PROJECT_DIR}/index.html"
node "${ASSEMBLE_SCRIPT}" --videodir "${PROJECT_DIR}"
