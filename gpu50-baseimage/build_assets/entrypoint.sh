#!/usr/bin/env bash
set -e

AIGC_UID=${AIGC_UID:-1001}
AIGC_GID=${AIGC_GID:-1001}
RUNTIME_HOME=$(getent passwd "$AIGC_UID" | cut -d: -f6)
# 尝试创建 aigc；失败也不影响后续（UID 可能已被 ubuntu 等占用）
getent group aigc >/dev/null 2>&1 || groupadd -g "$AIGC_GID" aigc 2>/dev/null || true
getent passwd aigc >/dev/null 2>&1 || useradd -m -s /bin/bash -u "$AIGC_UID" -g "$AIGC_GID" aigc 2>/dev/null || true
# 用数字 UID/GID chown，ubuntu(1000) 和 aigc(1000) 效果相同
chown -R "$AIGC_UID":"$AIGC_GID" /app
[ -d /home/aigc ] && chown -R "$AIGC_UID":"$AIGC_GID" /home/aigc
if [ -n "$RUNTIME_HOME" ] && [ -d /mnt/ssh-keys ]; then
  mkdir -p "$RUNTIME_HOME"
  ln -snf /mnt/ssh-keys "$RUNTIME_HOME/.ssh"
fi
# gosu 也支持数字 UID
exec gosu "$AIGC_UID" "$@"
