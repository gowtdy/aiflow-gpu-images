#!/usr/bin/env bash
# Run bun install with a filesystem heartbeat. Avoid --verbose: it floods
# Docker BuildKit past the ~200KiB/s log limit and gets clipped.
# Opt-in verbose: BUN_INSTALL_VERBOSE=1
set -euo pipefail

REGISTRY="${BUN_CONFIG_REGISTRY:-${BUN_REGISTRY:-https://registry.npmmirror.com}}"
VERBOSE_FLAG=()
if [[ "${BUN_INSTALL_VERBOSE:-0}" == "1" ]]; then
  VERBOSE_FLAG=(--verbose)
fi

echo "==> [2/6] bun install starting..."
echo "    registry: ${REGISTRY}"
echo "    verbose: ${BUN_INSTALL_VERBOSE:-0} (set BUN_INSTALL_VERBOSE=1 to debug)"
echo "    note: progress comes from heartbeat every 15s (not HTTP spam)"

LOG=/tmp/bun-install.log
: >"$LOG"

stdbuf -oL -eL bun install "${VERBOSE_FLAG[@]}" --registry="${REGISTRY}" >"$LOG" 2>&1 &
bun_pid=$!

# Stream bun's normal (or verbose) lines without drowning BuildKit.
stdbuf -oL -eL tail -n +1 -F "$LOG" &
tail_pid=$!

# Newest package dir under node_modules/.bun (by mtime).
latest_bun_pkg() {
  find node_modules/.bun -mindepth 1 -maxdepth 1 -type d -printf '%T@\t%p\n' 2>/dev/null \
    | sort -nr \
    | head -1 \
    | cut -f2-
}

heartbeat() {
  local elapsed=0 prev_pkgs=0
  while kill -0 "$bun_pid" 2>/dev/null; do
    sleep 15
    elapsed=$((elapsed + 15))
    kill -0 "$bun_pid" 2>/dev/null || break

    local pkgs cache_entries latest pkg size files delta nm_size
    pkgs=$(find node_modules/.bun -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    cache_entries=$(find /root/.bun/install/cache -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')
    delta=$((pkgs - prev_pkgs))
    prev_pkgs=$pkgs

    latest=$(latest_bun_pkg || true)
    pkg="?"
    size="-"
    files="-"
    if [[ -n "${latest:-}" ]]; then
      pkg=$(basename "$latest" | sed 's|+|/|g')
      size=$(du -sh "$latest" 2>/dev/null | awk '{print $1}')
      files=$(find "$latest" 2>/dev/null | wc -l | tr -d ' ')
    fi
    nm_size=$(du -sh node_modules 2>/dev/null | awk '{print $1}')

    echo "==> [2/6] still running ${elapsed}s | .bun=${pkgs} (+${delta}) cache=${cache_entries} | latest=${pkg} size=${size} files=${files} | node_modules=${nm_size}"
  done
}
heartbeat &
hb_pid=$!

wait "$bun_pid"
status=$?
kill "$tail_pid" "$hb_pid" 2>/dev/null || true
wait "$tail_pid" "$hb_pid" 2>/dev/null || true

if [[ "$status" -ne 0 ]]; then
  echo "==> [2/6] bun install failed (exit ${status}); last 40 log lines:" >&2
  tail -n 40 "$LOG" >&2 || true
fi
exit "$status"
