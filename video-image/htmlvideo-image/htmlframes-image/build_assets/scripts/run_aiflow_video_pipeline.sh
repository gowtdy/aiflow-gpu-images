#!/usr/bin/env bash
# Debug wrapper for the full AIFlow video build pipeline — edit flags below, then:
#   bash build_assets/scripts/run_aiflow_video_pipeline.sh
# Extra args are forwarded to init_with_brief.py (e.g. --dry-run, --json, --data-dir /tmp/videos).
#
# Pipeline:
#   1. init_with_brief.py                         → project + BRIEF + frame.md
#   2. run_aiflow_build_skills.py --skill storyboard
#   3. run_aiflow_build_skills.py --skill visual
#   4. frame-packets.mjs                          → .hyperframes/frame-packets/
#   5. run_aiflow_build_skills.py --skill html    → compositions/frames/*.html
#   6. assemble-index.mjs                         → index.html
#   7. transitions.mjs inject + verify
#
# Skills are separate invocations so steps can be inserted between them.
# --dry-run stops after step 1 (no skills / assemble / transitions).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SCRIPT="${SCRIPT_DIR}/init_with_brief.py"
SKILLS_SCRIPT="${SCRIPT_DIR}/run_aiflow_build_skills.py"
FRAME_PACKETS_SCRIPT="${SCRIPT_DIR}/frame-packets.mjs"
ASSEMBLE_SCRIPT="${SCRIPT_DIR}/assemble-index.mjs"
TRANSITIONS_SCRIPT="${SCRIPT_DIR}/transitions.mjs"

NAME="second-video"
DATA_DIR="/app/videos"
PROJECT_DIR="${DATA_DIR}/${NAME}"

DRY_RUN=0
for arg in "$@"; do
  if [[ "${arg}" == "--dry-run" ]]; then
    DRY_RUN=1
    break
  fi
done

echo "init_with_brief → ${PROJECT_DIR}"
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

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "dry-run: skipping skills / frame-packets / assemble / transitions"
  exit 0
fi

echo "aiflow skill storyboard → ${PROJECT_DIR}"
python3 "${SKILLS_SCRIPT}" --videodir "${PROJECT_DIR}" --skill storyboard

echo "aiflow skill visual → ${PROJECT_DIR}"
python3 "${SKILLS_SCRIPT}" --videodir "${PROJECT_DIR}" --skill visual

echo "frame-packets → ${PROJECT_DIR}/.hyperframes/frame-packets"
node "${FRAME_PACKETS_SCRIPT}" --project "${PROJECT_DIR}"

echo "aiflow skill html → ${PROJECT_DIR}"
python3 "${SKILLS_SCRIPT}" --videodir "${PROJECT_DIR}" --skill html

echo "assemble-index → ${PROJECT_DIR}/index.html"
node "${ASSEMBLE_SCRIPT}" --videodir "${PROJECT_DIR}"

echo "transitions inject → ${PROJECT_DIR}/index.html"
node "${TRANSITIONS_SCRIPT}" inject --videodir "${PROJECT_DIR}"

echo "transitions verify → ${PROJECT_DIR}/index.html"
node "${TRANSITIONS_SCRIPT}" verify --videodir "${PROJECT_DIR}"
