# Stage 1: compile HyperFrames CLI from local build_assets/hyperframes
FROM node:24-bookworm AS hf-builder
RUN apt-get update && apt-get install -y curl unzip \
    && curl -fsSL https://bun.sh/install | bash \
    && ln -sf /root/.bun/bin/bun /usr/local/bin/bun \
    && rm -rf /var/lib/apt/lists/*
COPY build_assets/hyperframes /app/hyperframes
WORKDIR /app/hyperframes
RUN bun install && bun run build

# Stage 2: runtime image
FROM gpu50-baseimage:0.1

#ENV DEBIAN_FRONTEND=noninteractive

USER root
# HyperFrames 需要 Node.js >= 22；固定 Active LTS 24.18.0（2026-07 当前 LTS 最新）
ARG NODE_VERSION=24.18.0
RUN apt-get update && apt-get install -y ca-certificates curl xz-utils \
    && curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
        | tar -xJ -C /usr/local --strip-components=1 \
    && rm -rf /var/lib/apt/lists/* \
    && node --version && npm --version

ARG CLAUDE_CODE_VERSION=2.1.201
RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
    && claude --version

# 复制项目文件（chown 由 base entrypoint 在 run 時依 AIGC_UID/AIGC_GID 處理）
RUN rm -rf /app/*
COPY build_assets/ /app/
COPY --from=hf-builder /app/hyperframes/packages/cli/dist /app/hyperframes/packages/cli/dist

# 安装 Python 依赖（root 安裝到系統路徑，不依賴 /home/aigc/.local）
RUN python3 -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app/hyperframes/packages/cli
RUN npm install -g . && hyperframes --version

WORKDIR /app

# 安装 HyperFrames agent skills（Claude Code 从 /app/.claude/skills/ 加载）
RUN npx --yes skills add /app/hyperframes \
    --all \
    --yes \
    --copy \
    --agent claude-code \
    && for d in /app/hyperframes/skills/_meta/*/; do \
         [ -d "$d" ] && rm -rf "/app/.claude/skills/$(basename "$d")"; \
       done

ENV PYTHONUNBUFFERED=1
#RUN pip install --progress-bar=raw -v -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 给脚本执行权限
#RUN chmod +x /app/start_index-tts.sh
# 使用 base 的 ENTRYPOINT ["/entrypoint.sh"]，僅設 CMD；tts-worker 會覆蓋 CMD
#CMD ["./start_index-tts.sh"]
CMD ["tail", "-f", "/dev/null"]
