#!/usr/bin/env bash
# Debug wrapper for init_with_brief.py — edit flags below, then:
#   bash build_assets/scripts/run_init_with_brief_example.sh
# Extra args are forwarded (e.g. --dry-run, --json, --data-dir /tmp/videos).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SCRIPT="${SCRIPT_DIR}/init_with_brief.py"

exec python3 "${INIT_SCRIPT}" \
  --name first-video \
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
