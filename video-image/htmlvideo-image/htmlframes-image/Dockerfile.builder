# Compile HyperFrames CLI from local build_assets/hyperframes (no gpu50-baseimage required).
FROM node:24-bookworm
RUN apt-get update && apt-get install -y curl unzip \
    && curl -fsSL https://bun.sh/install | bash \
    && ln -sf /root/.bun/bin/bun /usr/local/bin/bun \
    && rm -rf /var/lib/apt/lists/*
COPY build_assets/hyperframes /app/hyperframes
COPY build_assets/scripts/bun-install-with-progress.sh /tmp/bun-install-with-progress.sh
WORKDIR /app/hyperframes

# Default: npmmirror (China). Override:
#   docker build --build-arg BUN_REGISTRY=https://registry.npmjs.org ...
# Debug HTTP spam (may clip BuildKit logs): --build-arg BUN_INSTALL_VERBOSE=1
ARG BUN_REGISTRY=https://registry.npmmirror.com
ARG BUN_INSTALL_VERBOSE=0
ENV BUN_CONFIG_REGISTRY=${BUN_REGISTRY}
ENV BUN_INSTALL_VERBOSE=${BUN_INSTALL_VERBOSE}

# Local image only builds CLI (+ compile deps). Strip aws-lambda binary
# packages so bun install does not hit GitHub CDN (ffmpeg-static timeout).
# Skip aws-lambda / gcp-cloud-run / shader-transitions — CLI marks the first
# two external; shader-transitions is not required for the CLI bundle.
# Split into layers + echo so docker build --progress=plain shows which step is running.
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

# No --verbose by default (BuildKit clips at ~200KiB/s). Heartbeat every 15s:
# package new/recent + proc CPU/IO deltas + children + touched paths + log tail.
# Debug HTTP: --build-arg BUN_INSTALL_VERBOSE=1
RUN chmod +x /tmp/bun-install-with-progress.sh \
  && /tmp/bun-install-with-progress.sh \
  && echo "==> [2/6] bun install done"

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

# 导出 onnxruntime-node 到固定路径（Bun 的 node_modules 布局与 npm 不同，runtime 阶段从此处拷贝）
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
