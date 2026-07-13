# Compile HyperFrames CLI from local build_assets/hyperframes (no gpu50-baseimage required).
FROM node:24-bookworm
RUN apt-get update && apt-get install -y curl unzip \
    && curl -fsSL https://bun.sh/install | bash \
    && ln -sf /root/.bun/bin/bun /usr/local/bin/bun \
    && rm -rf /var/lib/apt/lists/*
COPY build_assets/hyperframes /app/hyperframes
WORKDIR /app/hyperframes
RUN bun install && bun run build
