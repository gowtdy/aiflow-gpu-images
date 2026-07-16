#!/usr/bin/env bash
# Debug wrapper for init_with_brief.py — edit flags below, then:
#   bash build_assets/scripts/run_init_with_brief_example.sh
# Extra args are forwarded (e.g. --dry-run, --json, --data-dir /tmp/videos).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SCRIPT="${SCRIPT_DIR}/init_with_brief.py"

exec python3 "${INIT_SCRIPT}" \
  --name stock-selection-guide \
  --example blank \
  --skip-skills \
  --theme "Pick a stock systematically with a 4-step funnel screen" \
  --aspect 1920x1080 \
  --language en \
  --length 40s \
  --angle practitioner \
  --angle how-to \
  --tone humorous \
  --audience "everyday investors" \
  "$@"
