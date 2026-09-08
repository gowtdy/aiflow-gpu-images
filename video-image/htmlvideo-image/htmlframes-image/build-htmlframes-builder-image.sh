#!/usr/bin/env bash
# Build htmlframes builder image only (wrapper around build-htmlframes-base-image.sh builder).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

exec ./build-htmlframes-base-image.sh builder
