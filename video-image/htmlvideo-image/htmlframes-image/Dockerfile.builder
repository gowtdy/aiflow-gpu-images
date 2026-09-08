# Compile HyperFrames CLI from local build_assets/hyperframes.
# Requires pre-built base: ./build-htmlframes-base-image.sh
# Build: ./build-htmlframes-builder-image.sh
ARG BUILDER_BASE_IMAGE=htmlframes-builder-base:0.1
FROM ${BUILDER_BASE_IMAGE}

# Optional HTTP proxy (empty = unused). Prefer setting on base; re-declare for this stage.
ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=localhost,127.0.0.1,registry.npmmirror.com,mirrors.aliyun.com,cdn.npmmirror.com
ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    no_proxy=${NO_PROXY}

WORKDIR /app/hyperframes

# Default: npmmirror (China). Override:
#   docker build --build-arg BUN_REGISTRY=https://registry.npmjs.org ...
# Debug HTTP spam (may clip BuildKit logs): --build-arg BUN_INSTALL_VERBOSE=1
ARG BUN_REGISTRY=https://registry.npmmirror.com
ARG BUN_INSTALL_VERBOSE=0
ENV BUN_CONFIG_REGISTRY=${BUN_REGISTRY}
ENV BUN_INSTALL_VERBOSE=${BUN_INSTALL_VERBOSE}

# --- Layer 1: lock + package manifests only (source edits must not bust install) ---
COPY build_assets/hyperframes/package.json build_assets/hyperframes/bun.lock ./
COPY build_assets/hyperframes/packages/aws-lambda/package.json ./packages/aws-lambda/
COPY build_assets/hyperframes/packages/cli/package.json ./packages/cli/
COPY build_assets/hyperframes/packages/core/package.json ./packages/core/
COPY build_assets/hyperframes/packages/engine/package.json ./packages/engine/
COPY build_assets/hyperframes/packages/gcp-cloud-run/package.json ./packages/gcp-cloud-run/
COPY build_assets/hyperframes/packages/lint/package.json ./packages/lint/
COPY build_assets/hyperframes/packages/parsers/package.json ./packages/parsers/
COPY build_assets/hyperframes/packages/player/package.json ./packages/player/
COPY build_assets/hyperframes/packages/producer/package.json ./packages/producer/
COPY build_assets/hyperframes/packages/sdk/package.json ./packages/sdk/
COPY build_assets/hyperframes/packages/sdk-playground/package.json ./packages/sdk-playground/
COPY build_assets/hyperframes/packages/shader-transitions/package.json ./packages/shader-transitions/
COPY build_assets/hyperframes/packages/studio/package.json ./packages/studio/
COPY build_assets/hyperframes/packages/studio-server/package.json ./packages/studio-server/
COPY build_assets/scripts/bun-install-with-progress.sh /tmp/bun-install-with-progress.sh

# Strip aws-lambda binary packages so bun install does not hit GitHub CDN (ffmpeg-static timeout).
RUN echo "==> [1/6] patch aws-lambda package.json (strip ffmpeg-static/ffprobe-static)" \
  && node -e "\
  const fs = require('fs'); \
  const p = 'packages/aws-lambda/package.json'; \
  const pkg = JSON.parse(fs.readFileSync(p, 'utf8')); \
  delete pkg.dependencies['ffmpeg-static']; \
  delete pkg.dependencies['ffprobe-static']; \
  fs.writeFileSync(p, JSON.stringify(pkg, null, 2) + '\n'); \
" \
  && echo "==> [1/6] package.json patched"

# BuildKit cache for bun download store; heartbeat script (no --verbose by default).
RUN --mount=type=cache,target=/root/.bun/install/cache \
  chmod +x /tmp/bun-install-with-progress.sh \
  && /tmp/bun-install-with-progress.sh \
  && echo "==> [2/6] bun install done"

# --- Layer 2: full sources (invalidates compile only) ---
COPY build_assets/hyperframes /app/hyperframes

# Full COPY overwrites the patched aws-lambda package.json — re-apply.
RUN echo "==> [1/6] re-patch aws-lambda package.json after source COPY" \
  && node -e "\
  const fs = require('fs'); \
  const p = 'packages/aws-lambda/package.json'; \
  const pkg = JSON.parse(fs.readFileSync(p, 'utf8')); \
  delete pkg.dependencies['ffmpeg-static']; \
  delete pkg.dependencies['ffprobe-static']; \
  fs.writeFileSync(p, JSON.stringify(pkg, null, 2) + '\n'); \
" \
  && echo "==> [1/6] package.json re-patched"

RUN echo "==> [3/6] build parsers / lint / studio-server" \
  && bun run --filter '@hyperframes/{parsers,lint,studio-server}' build \
  && echo "==> [3/6] done"

RUN echo "==> [4/6] build core" \
  && bun run --filter @hyperframes/core build \
  && echo "==> [4/6] done"

# Sequential (not one parallel filter): BuildKit error summaries clip at the
# tail — a noisy studio success can hide the real failing package. Sequential
# also lowers peak RAM (studio DTS + producer fonts in parallel often OOM).
RUN echo "==> [5/6] build engine" \
  && bun run --filter @hyperframes/engine build \
  && echo "==> [5/6] build producer" \
  && bun run --filter @hyperframes/producer build \
  && echo "==> [5/6] build player" \
  && bun run --filter @hyperframes/player build \
  && echo "==> [5/6] build sdk" \
  && bun run --filter @hyperframes/sdk build \
  && echo "==> [5/6] build studio" \
  && bun run --filter @hyperframes/studio build \
  && echo "==> [5/6] done"

RUN echo "==> [6/6] build cli" \
  && bun run --filter @hyperframes/cli build \
  && echo "==> [6/6] cli build done"

# Export onnxruntime-node to a fixed path (Bun node_modules layout differs from npm).
WORKDIR /app/hyperframes/packages/cli
RUN echo "==> export onnxruntime-node to /opt/hf-export" \
  && node -e "\
  const fs = require('fs'); \
  const path = require('path'); \
  const pkg = require.resolve('onnxruntime-node/package.json'); \
  fs.mkdirSync('/opt/hf-export', { recursive: true }); \
  fs.cpSync(path.dirname(pkg), '/opt/hf-export/onnxruntime-node', { recursive: true }); \
" \
  && echo "==> onnxruntime-node exported"
