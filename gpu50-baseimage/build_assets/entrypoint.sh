#!/usr/bin/env bash
set -e

# Runtime alignment: create aigc user with host UID/GID (default 1001)
AIGC_UID=${AIGC_UID:-1001}
AIGC_GID=${AIGC_GID:-1001}

# Create group and user if they do not exist (ignore errors if ID already in use)
getent group aigc >/dev/null 2>&1 || groupadd -g "$AIGC_GID" aigc 2>/dev/null || true
getent passwd aigc >/dev/null 2>&1 || useradd -m -s /bin/bash -u "$AIGC_UID" -g "$AIGC_GID" aigc 2>/dev/null || true

# Ensure /app and aigc home are owned by aigc (by name, so correct regardless of UID)
chown -R aigc:aigc /app
[ -d /home/aigc ] && chown -R aigc:aigc /home/aigc

exec gosu aigc "$@"
