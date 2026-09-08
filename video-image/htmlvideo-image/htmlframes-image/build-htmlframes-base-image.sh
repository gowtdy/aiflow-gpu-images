#!/usr/bin/env bash
# Build htmlframes builder-base image only (Node 24 + bun, China-friendly mirrors).
#
# Usage:
#   ./build-htmlframes-base-image.sh
#
# Then:
#   ./build-htmlframes-builder-image.sh
#   ./build-htmlframes-runtime-image.sh
#
# Override:
#   BUILDER_BASE_IMAGE=my-registry/htmlframes-builder-base:0.1 ./build-htmlframes-base-image.sh
#   BUN_VERSION=1.3.14 ./build-htmlframes-base-image.sh
# Optional proxy (from .env or env):
#   HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 ./build-htmlframes-base-image.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

export DOCKER_BUILDKIT=1

BUILDER_BASE_IMAGE="${BUILDER_BASE_IMAGE:-htmlframes-builder-base:0.1}"
BUN_VERSION="${BUN_VERSION:-1.3.14}"
NO_PROXY_DEFAULT="localhost,127.0.0.1,registry.npmmirror.com,mirrors.aliyun.com,cdn.npmmirror.com"
NO_PROXY="${NO_PROXY:-${NO_PROXY_DEFAULT}}"

build_args=(
  --build-arg "BUN_VERSION=${BUN_VERSION}"
  --build-arg "NO_PROXY=${NO_PROXY}"
)
# Only pass proxy when set — avoid baking empty proxy into the image layer hash.
if [[ -n "${HTTP_PROXY:-}" ]]; then
  build_args+=(--build-arg "HTTP_PROXY=${HTTP_PROXY}")
fi
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  build_args+=(--build-arg "HTTPS_PROXY=${HTTPS_PROXY}")
fi

docker build --progress=plain -t "${BUILDER_BASE_IMAGE}" \
  "${build_args[@]}" \
  -f Dockerfile.builder-base .
