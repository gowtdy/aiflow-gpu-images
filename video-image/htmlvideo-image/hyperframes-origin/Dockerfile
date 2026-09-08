FROM gpu50-baseimage:0.1

#ENV DEBIAN_FRONTEND=noninteractive

USER root

RUN rm -rf /app/*
RUN mkdir -p /app /app/log /app/data /app/videos /app/tools /app/tools/chrome
COPY build_assets/ /app/

# 运行依赖：系统库走 apt（体积小），字体走离线 .deb（体积大，预下载到 build_assets/software/fonts/）
#   build_assets/software/node-v24.18.0-linux-x64.tar.xz
#   build_assets/software/chrome-headless-shell-linux64.zip
#   build_assets/software/fonts/*.deb（通过 download-font-packages.sh 预下载）
ARG NODE_VERSION=24.18.0
ARG CHROME_HEADLESS_SHELL_VERSION=148.0.7778.167
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates xz-utils unzip \
    libgbm1 libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 \
    libxdamage1 libxrandr2 libcups2 libasound2t64 libpangocairo-1.0-0 \
    libxshmfence1 libgtk-3-0 \
    && tar -xJf "/app/software/node-v${NODE_VERSION}-linux-x64.tar.xz" \
         -C /usr/local --strip-components=1 \
    && rm -rf /var/lib/apt/lists/* \
    && node --version && npm --version

# 字体包（离线安装，避免在线下载 175 MB 字体包卡住构建）
RUN set -eux; \
    if [ -d /app/software/fonts ] && [ -n "$(ls -A /app/software/fonts/*.deb 2>/dev/null)" ]; then \
      dpkg -i /app/software/fonts/*.deb; \
      rm -rf /app/software/fonts; \
    else \
      echo "WARNING: no font .deb files found, falling back to apt"; \
      apt-get update; \
      apt-get install -y --no-install-recommends \
        fonts-liberation fonts-noto-color-emoji fonts-noto-cjk fonts-noto-core \
        fonts-noto-extra fonts-noto-ui-core fonts-freefont-ttf fonts-dejavu-core \
        fontconfig; \
      rm -rf /var/lib/apt/lists/*; \
    fi; \
    fc-cache -fv

# chrome-headless-shell（BeginFrame 抓帧）；从本地 zip 解压，不再 npx 下载
# zip 顶层为 chrome-headless-shell-linux64/，解压到 puppeteer 兼容布局后 find 二进制
RUN mkdir -p "/app/tools/puppeteer/chrome-headless-shell/linux-${CHROME_HEADLESS_SHELL_VERSION}" \
    && unzip -q "/app/software/chrome-headless-shell-linux64.zip" \
         -d "/app/tools/puppeteer/chrome-headless-shell/linux-${CHROME_HEADLESS_SHELL_VERSION}" \
    && CHS="$(find /app/tools/puppeteer/chrome-headless-shell -name chrome-headless-shell -type f | head -n1)" \
    && test -n "$CHS" \
    && ln -sf "$CHS" /app/tools/chrome/chrome-headless-shell \
    && /app/tools/chrome/chrome-headless-shell --version

ENV HYPERFRAMES_BROWSER_PATH=/app/tools/chrome/chrome-headless-shell
ENV PRODUCER_HEADLESS_SHELL_PATH=/app/tools/chrome/chrome-headless-shell
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

ARG CLAUDE_CODE_VERSION=2.1.201
RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
    && claude --version

# Claude Code 默认开启交互/API 调试日志（无需每次传 --debug）
ENV DEBUG=1
ENV CLAUDE_CODE_DEBUG_LOGS_DIR=/app/log/claude-debug.log
ENV CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose
ENV ANTHROPIC_LOG=debug
ENV CLAUDE_CONFIG_DIR=/app/log/claude
ENV CLAUDE_CODE_ENABLE_TELEMETRY=1
ENV OTEL_LOG_RAW_API_BODIES=file:/app/log/api-bodies

# 安装 Python 依赖（root 安裝到系統路徑，不依賴 /home/aigc/.local）
RUN python3 -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# 安装 HyperFrames agent skills（Claude Code 从 /app/.claude/skills/ 加载）
RUN npx --yes skills add heygen-com/hyperframes \
    --full-depth \
    --yes \
    --all \
    --copy

ENV PYTHONUNBUFFERED=1
#RUN pip install --progress-bar=raw -v -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 给脚本执行权限
#RUN chmod +x /app/start_index-tts.sh
# 使用 base 的 ENTRYPOINT ["/entrypoint.sh"]，僅設 CMD；tts-worker 會覆蓋 CMD
#CMD ["./start_index-tts.sh"]
CMD ["tail", "-f", "/dev/null"]
