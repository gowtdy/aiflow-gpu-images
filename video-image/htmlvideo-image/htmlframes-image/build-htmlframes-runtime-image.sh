#!/usr/bin/env bash
# Build htmlframes runtime image only (FROM gpu50-baseimage + builder artifacts).
# Requires a pre-built builder image (does NOT build builder automatically):
#   ./build-htmlframes-builder-image.sh
#
# Usage:
#   ./build-htmlframes-runtime-image.sh
#
# Override:
#   RUNTIME_IMAGE=htmlframes-image:0.1 BUILDER_IMAGE=htmlframes-builder:0.1 ./build-htmlframes-runtime-image.sh
#
# Day-to-day: only rebuild runtime when changing skills/config/runtime assets;
# rebuild builder when changing HyperFrames CLI / monorepo sources.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

export DOCKER_BUILDKIT=1

BUILDER_IMAGE="${BUILDER_IMAGE:-htmlframes-builder:0.1}"
RUNTIME_IMAGE="${RUNTIME_IMAGE:-htmlframes-image:0.1}"

docker build --progress=plain -t "${RUNTIME_IMAGE}" \
  --build-arg "BUILDER_IMAGE=${BUILDER_IMAGE}" \
  -f Dockerfile.runtime .
