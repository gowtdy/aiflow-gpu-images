# Compile HyperFrames CLI from local build_assets/hyperframes.
# Requires pre-built base: ./build-htmlframes-base-image.sh
# Build: ./build-htmlframes-builder-image.sh
#
# Caching strategy: sources are tiered by change frequency so editing cli or
# studio does not invalidate the foundation build.
#
# Tier 1a (foundation: parsers/lint/studio-server/core — circular dep, sources co-resident)
#   -> 1b (engine+shader) -> 1c (producer, heavy) -> 1d (player/sdk/cloud/playground)
# Tier 2 (studio) -> Tier 3 (cli, most volatile).
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

# BuildKit cache for entire bun store (download cache + global package store).
# Caching /root/.bun (not just install/cache) allows the linking phase to reuse
# hardlinked packages from the global store across builds.
RUN --mount=type=cache,target=/root/.bun \
  chmod +x /tmp/bun-install-with-progress.sh \
  && /tmp/bun-install-with-progress.sh \
  && echo "==> [2/6] bun install done"

# ==============================================================================
# Tier 1a -- Foundation: parsers / lint / studio-server / core (4 packages)
# Core source is co-resident because studio-server <-> core have circular imports.
# All four are copied in ONE layer, then built in two RUNs for tight error scopes.
# ==============================================================================
COPY build_assets/hyperframes/scripts            /app/hyperframes/scripts
COPY build_assets/hyperframes/packages/parsers       /app/hyperframes/packages/parsers
COPY build_assets/hyperframes/packages/lint          /app/hyperframes/packages/lint
COPY build_assets/hyperframes/packages/studio-server /app/hyperframes/packages/studio-server
COPY build_assets/hyperframes/packages/core          /app/hyperframes/packages/core

RUN echo "==> [T1a] build parsers / lint / studio-server" \
  && bun run --filter '@hyperframes/{parsers,lint,studio-server}' build \
  && echo "==> [T1a] parsers / lint / studio-server done"

RUN echo "==> [T1a] build core" \
  && bun run --filter @hyperframes/core build \
  && echo "==> [T1a] core done"

# ==============================================================================
# Tier 1b -- Engine + shader-transitions (small, occasionally change, parallel safe)
# ==============================================================================
COPY build_assets/hyperframes/packages/shader-transitions /app/hyperframes/packages/shader-transitions
COPY build_assets/hyperframes/packages/engine            /app/hyperframes/packages/engine

RUN echo "==> [T1b] build shader-transitions + engine (parallel)" \
  && ( \
    bun run --filter @hyperframes/shader-transitions build & \
    bun run --filter @hyperframes/engine build & \
    wait \
  ) \
  && echo "==> [T1b] shader-transitions + engine done"

# ==============================================================================
# Tier 1c -- Producer (heavy, 52MB source; isolated tier so engine changes
# don't force a producer COPY miss when the engine API hasn't changed.)
# Builds: fonts -> hf-stub -> runtime:modular -> esbuild bundle
# ==============================================================================
COPY build_assets/hyperframes/packages/producer /app/hyperframes/packages/producer

RUN echo "==> [T1c] build producer" \
  && bun run --filter @hyperframes/producer build \
  && echo "==> [T1c] producer done"

# ==============================================================================
# Tier 1d -- Player / SDK / cloud adapters / playground (light, built in one RUN)
# ==============================================================================
COPY build_assets/hyperframes/packages/player           /app/hyperframes/packages/player
COPY build_assets/hyperframes/packages/sdk              /app/hyperframes/packages/sdk
COPY build_assets/hyperframes/packages/sdk-playground   /app/hyperframes/packages/sdk-playground
COPY build_assets/hyperframes/packages/aws-lambda       /app/hyperframes/packages/aws-lambda
COPY build_assets/hyperframes/packages/gcp-cloud-run    /app/hyperframes/packages/gcp-cloud-run

# Tier 1d COPY overwrites the patched aws-lambda package.json -- re-apply.
RUN echo "==> [T1d] re-patch aws-lambda package.json after COPY" \
  && node -e "\
  const fs = require('fs'); \
  const p = 'packages/aws-lambda/package.json'; \
  const pkg = JSON.parse(fs.readFileSync(p, 'utf8')); \
  delete pkg.dependencies['ffmpeg-static']; \
  delete pkg.dependencies['ffprobe-static']; \
  fs.writeFileSync(p, JSON.stringify(pkg, null, 2) + '\n'); \
" \
  && echo "==> [T1d] package.json re-patched"

RUN echo "==> [T1d] build player / sdk / cloud-adapters / playground" \
  && bun run --filter '@hyperframes/{player,sdk,aws-lambda,gcp-cloud-run,sdk-playground}' build \
  && echo "==> [T1d] build done"

# ==============================================================================
# Tier 2 -- Studio (cached when only cli changes)
# ==============================================================================
COPY build_assets/hyperframes/packages/studio /app/hyperframes/packages/studio

RUN echo "==> [T2] build studio" \
  && bun run --filter @hyperframes/studio build \
  && echo "==> [T2] studio done"

# ==============================================================================
# Tier 3 -- CLI (most frequently changed; cached when nothing changed)
# Registry + skills are only needed for build:copy -> moved here from Tier 1.
# ==============================================================================
COPY build_assets/hyperframes/packages/cli /app/hyperframes/packages/cli

# Root-level assets for cli build:copy (registry examples + skills).
# .dockerignore limits these to warm-grain + 3 skill dirs.
COPY build_assets/hyperframes/registry /app/hyperframes/registry
COPY build_assets/hyperframes/skills   /app/hyperframes/skills

RUN echo "==> [T3] build cli" \
  && bun run --filter @hyperframes/cli build \
  && echo "==> [T3] cli done"

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