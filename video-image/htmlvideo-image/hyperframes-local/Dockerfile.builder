# Compile HyperFrames CLI from local build_assets/hyperframes (no gpu50-baseimage required).
FROM node:24-bookworm
RUN apt-get update && apt-get install -y curl unzip \
    && curl -fsSL https://bun.sh/install | bash \
    && ln -sf /root/.bun/bin/bun /usr/local/bin/bun \
    && rm -rf /var/lib/apt/lists/*
COPY build_assets/hyperframes /app/hyperframes
WORKDIR /app/hyperframes
RUN bun install && bun run build

# 导出 onnxruntime-node 到固定路径（Bun 的 node_modules 布局与 npm 不同，runtime 阶段从此处拷贝）
WORKDIR /app/hyperframes/packages/cli
RUN node -e "\
  const fs = require('fs'); \
  const path = require('path'); \
  const pkg = require.resolve('onnxruntime-node/package.json'); \
  fs.mkdirSync('/opt/hf-export', { recursive: true }); \
  fs.cpSync(path.dirname(pkg), '/opt/hf-export/onnxruntime-node', { recursive: true }); \
"
