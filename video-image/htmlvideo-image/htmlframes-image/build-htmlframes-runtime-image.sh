#!/usr/bin/env bash
# Build htmlframes runtime image only (wrapper around build-htmlframes-image.sh runtime).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

exec ./build-htmlframes-image.sh runtime
