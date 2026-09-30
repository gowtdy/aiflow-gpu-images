#!/usr/bin/env bash
# Build htmlframes builder image only (compile HyperFrames CLI).
# Requires a pre-built base image (does NOT build base automatically):
#   ./build-htmlframes-base-image.sh
#
# Usage:
#   ./build-htmlframes-builder-image.sh
#
# Override:
#   BUILDER_IMAGE=my-registry/htmlframes-builder:0.1 ./build-htmlframes-builder-image.sh
#   BUILDER_BASE_IMAGE=htmlframes-builder-base:0.1 BUN_REGISTRY=https://registry.npmmirror.com ./build-htmlframes-builder-image.sh
#   BUN_INSTALL_VERBOSE=1 ./build-htmlframes-builder-image.sh
# Optional proxy (from .env or env):
#   HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 ./build-htmlframes-builder-image.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

export DOCKER_BUILDKIT=1

BUILDER_IMAGE="${BUILDER_IMAGE:-htmlframes-builder:0.1}"
BUILDER_BASE_IMAGE="${BUILDER_BASE_IMAGE:-htmlframes-builder-base:0.1}"
BUN_REGISTRY="${BUN_REGISTRY:-https://registry.npmmirror.com}"
BUN_INSTALL_VERBOSE="${BUN_INSTALL_VERBOSE:-0}"
NO_PROXY_DEFAULT="localhost,127.0.0.1,registry.npmmirror.com,mirrors.aliyun.com,cdn.npmmirror.com"
NO_PROXY="${NO_PROXY:-${NO_PROXY_DEFAULT}}"

build_args=(
  --build-arg "BUILDER_BASE_IMAGE=${BUILDER_BASE_IMAGE}"
  --build-arg "BUN_REGISTRY=${BUN_REGISTRY}"
  --build-arg "BUN_INSTALL_VERBOSE=${BUN_INSTALL_VERBOSE}"
  --build-arg "NO_PROXY=${NO_PROXY}"
)
if [[ -n "${HTTP_PROXY:-}" ]]; then
  build_args+=(--build-arg "HTTP_PROXY=${HTTP_PROXY}")
fi
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  build_args+=(--build-arg "HTTPS_PROXY=${HTTPS_PROXY}")
fi

# Prefer --ignorefile (Docker 23+). Older engines: briefly swap .dockerignore.
ignore_args=()
restore_dockerignore=
if docker build --help 2>&1 | grep -q -- '--ignorefile'; then
  ignore_args=(--ignorefile .dockerignore.builder)
elif [[ -f .dockerignore.builder ]]; then
  if [[ -f .dockerignore ]]; then
    cp .dockerignore .dockerignore.runtime.bak
    restore_dockerignore=1
  fi
  cp .dockerignore.builder .dockerignore
  trap 'if [[ -n "${restore_dockerignore:-}" ]]; then mv -f .dockerignore.runtime.bak .dockerignore; else rm -f .dockerignore; fi' EXIT
fi

docker build --progress=plain -t "${BUILDER_IMAGE}" \
  "${ignore_args[@]}" \
  "${build_args[@]}" \
  -f Dockerfile.builder .
