#!/usr/bin/env bash
# Build hyperframes-local image (FROM gpu50-baseimage:0.1). Run 時由 base entrypoint 依 AIGC_UID/AIGC_GID 建立 aigc，B 機可傳 -e AIGC_UID=$(id -u aigc) -e AIGC_GID=$(id -g aigc)，未傳則預設 1001。
#
# Usage:
#   ./build-hyperframes-image.sh           # build builder + runtime (default)
#   ./build-hyperframes-image.sh builder   # compile HyperFrames CLI only
#   ./build-hyperframes-image.sh runtime   # runtime image only (builder must exist)
#
# Override image tags:
#   BUILDER_IMAGE=my-registry/hyperframes-builder:0.1 RUNTIME_IMAGE=hyperframes-local-image:0.1 ./build-hyperframes-image.sh
set -euo pipefail

BUILDER_IMAGE="${BUILDER_IMAGE:-hyperframes-builder:0.1}"
RUNTIME_IMAGE="${RUNTIME_IMAGE:-hyperframes-local-image:0.1}"
TARGET="${1:-all}"

build_builder() {
  docker build --progress=plain -t "${BUILDER_IMAGE}" -f Dockerfile.builder .
}

build_runtime() {
  docker build --progress=plain -t "${RUNTIME_IMAGE}" \
    --build-arg BUILDER_IMAGE="${BUILDER_IMAGE}" \
    -f Dockerfile.runtime .
}

case "${TARGET}" in
  builder)
    build_builder
    ;;
  runtime)
    build_runtime
    ;;
  all|"")
    build_builder
    build_runtime
    ;;
  *)
    echo "Unknown target: ${TARGET} (use: builder | runtime | all)" >&2
    exit 1
    ;;
esac
