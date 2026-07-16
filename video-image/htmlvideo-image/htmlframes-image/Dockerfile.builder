# Compile HyperFrames CLI from local build_assets/hyperframes (no gpu50-baseimage required).
FROM node:24-bookworm
RUN apt-get update && apt-get install -y curl unzip \
    && curl -fsSL https://bun.sh/install | bash \
    && ln -sf /root/.bun/bin/bun /usr/local/bin/bun \
    && rm -rf /var/lib/apt/lists/*
COPY build_assets/hyperframes /app/hyperframes
WORKDIR /app/hyperframes

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

RUN echo "==> [2/6] bun install starting (may be quiet during link/postinstall)..." \
  && bun install --verbose \
  && echo "==> [2/6] bun install done"

RUN echo "==> [3/6] build parsers / lint / studio-server" \
  && bun run --filter '@hyperframes/{parsers,lint,studio-server}' build \
  && echo "==> [3/6] done"

RUN echo "==> [4/6] build core" \
  && bun run --filter @hyperframes/core build \
  && echo "==> [4/6] done"

RUN echo "==> [5/6] build engine / producer / player / studio / sdk" \
  && bun run --filter '@hyperframes/{engine,producer,player,studio,sdk}' build \
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
