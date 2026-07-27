#!/usr/bin/env bash
# Run `bun install --verbose` with live log + heartbeat that reports which
# package is streaming/hardlinking (bun itself goes quiet on large tarballs).
set -euo pipefail

REGISTRY="${BUN_CONFIG_REGISTRY:-${BUN_REGISTRY:-https://registry.npmmirror.com}}"

echo "==> [2/6] bun install starting..."
echo "    registry: ${REGISTRY}"
echo "    note: quiet stretches are normal during hardlink of large tarballs"

LOG=/tmp/bun-install.log
: >"$LOG"

stdbuf -oL -eL bun install --verbose --registry="${REGISTRY}" >"$LOG" 2>&1 &
bun_pid=$!

# Live stream bun verbose lines to docker build log.
stdbuf -oL -eL tail -n +1 -F "$LOG" &
tail_pid=$!

heartbeat() {
  local elapsed=0
  while kill -0 "$bun_pid" 2>/dev/null; do
    sleep 15
    elapsed=$((elapsed + 15))
    kill -0 "$bun_pid" 2>/dev/null || break

    local streamed hardlinked pkgs last phase pkg target size files
    streamed=$(grep -c 'Streamed ' "$LOG" 2>/dev/null || true)
    hardlinked=$(grep -c 'Hardlinking ' "$LOG" 2>/dev/null || true)
    pkgs=$(find node_modules/.bun -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')

    last=$(grep -E '^\[[^]]+\] Streamed |Hardlinking ' "$LOG" 2>/dev/null | tail -1 || true)
    phase="resolving/linking"
    pkg="?"
    size="-"
    files="-"

    if [[ "$last" =~ ^\[([^]]+)\]\ Streamed ]]; then
      phase="streaming"
      pkg="${BASH_REMATCH[1]}"
    elif [[ "$last" == Hardlinking* ]]; then
      phase="hardlinking"
      # path: .../node_modules/.bun/<name>@ver/...
      pkg=$(sed -n 's|.*/\.bun/\([^/]*\)/.*|\1|p' <<<"$last" | sed 's|+|/|g')
      [[ -n "$pkg" ]] || pkg=$(awk '{print $NF}' <<<"$last")
      target=$(awk '{print $NF}' <<<"$last")
      if [[ -e "$target" ]]; then
        size=$(du -sh "$target" 2>/dev/null | awk '{print $1}')
        files=$(find "$target" 2>/dev/null | wc -l | tr -d ' ')
      fi
    fi

    echo "==> [2/6] still running ${elapsed}s | phase=${phase} | pkg=${pkg} | streamed=${streamed} hardlinked=${hardlinked} .bun=${pkgs} | size=${size} files=${files}"
  done
}
heartbeat &
hb_pid=$!

wait "$bun_pid"
status=$?
kill "$tail_pid" "$hb_pid" 2>/dev/null || true
wait "$tail_pid" "$hb_pid" 2>/dev/null || true
exit "$status"
