#!/usr/bin/env bash
# Run bun install with a rich filesystem/process heartbeat.
# Avoid --verbose by default (BuildKit clips ~200KiB/s). Opt-in: BUN_INSTALL_VERBOSE=1
set -euo pipefail

REGISTRY="${BUN_CONFIG_REGISTRY:-${BUN_REGISTRY:-https://registry.npmmirror.com}}"
VERBOSE_FLAG=()
if [[ "${BUN_INSTALL_VERBOSE:-0}" == "1" ]]; then
  VERBOSE_FLAG=(--verbose)
fi

echo "==> [2/6] bun install starting..."
echo "    registry: ${REGISTRY}"
echo "    verbose: ${BUN_INSTALL_VERBOSE:-0} (set BUN_INSTALL_VERBOSE=1 to debug)"
echo "    note: heartbeat every 15s — when .bun stays flat, check proc/children/log/touched"

LOG=/tmp/bun-install.log
: >"$LOG"
PREV_PKGS_FILE=/tmp/bun-install-prev-pkgs.txt
: >"$PREV_PKGS_FILE"

stdbuf -oL -eL bun install "${VERBOSE_FLAG[@]}" --registry="${REGISTRY}" >"$LOG" 2>&1 &
bun_pid=$!

stdbuf -oL -eL tail -n +1 -F "$LOG" &
tail_pid=$!

join_csv() {
  awk 'NR>1{printf ", "}{printf "%s", $0} END{print ""}'
}

list_bun_pkg_dirs() {
  find node_modules/.bun -mindepth 1 -maxdepth 1 -type d ! -name node_modules 2>/dev/null \
    | sed 's|.*/||' \
    | sed 's|+|/|g' \
    | sort
}

recent_bun_pkgs() {
  local n="${1:-5}"
  find node_modules/.bun -mindepth 1 -maxdepth 1 -type d ! -name node_modules \
    -printf '%T@\t%f\n' 2>/dev/null \
    | sort -nr \
    | head -n "$n" \
    | cut -f2- \
    | sed 's|+|/|g' \
    | join_csv
}

new_since_prev() {
  local now_file="$1" prev_file="$2"
  [[ -s "$prev_file" ]] || return 0
  comm -13 "$prev_file" "$now_file" | head -n 8 | join_csv
}

# Bun process: state, CPU ticks, RSS, IO bytes.
proc_summary() {
  local pid="$1"
  local state rss utime stime read_b write_b cpu_s
  if [[ ! -r "/proc/${pid}/stat" ]]; then
    echo "gone"
    return
  fi
  # stat: field3=state, 14=utime, 15=stime (jiffies); status VmRSS in kB
  state=$(awk '{print $3}' "/proc/${pid}/stat")
  utime=$(awk '{print $14}' "/proc/${pid}/stat")
  stime=$(awk '{print $15}' "/proc/${pid}/stat")
  cpu_s=$(( (utime + stime) / 100 )) # jiffies≈10ms on Linux → /100 ≈ seconds
  rss=$(awk '/VmRSS:/ {print $2}' "/proc/${pid}/status" 2>/dev/null || echo 0)
  read_b=0
  write_b=0
  if [[ -r "/proc/${pid}/io" ]]; then
    read_b=$(awk '/read_bytes:/ {print $2}' "/proc/${pid}/io")
    write_b=$(awk '/write_bytes:/ {print $2}' "/proc/${pid}/io")
  fi
  echo "state=${state} cpu≈${cpu_s}s rss=$((rss / 1024))MB io_r=$((read_b / 1048576))MB io_w=$((write_b / 1048576))MB"
}

# Direct children (lifecycle scripts etc.).
children_summary() {
  local pid="$1"
  local kids
  kids=$(ps --ppid "$pid" -o pid=,etime=,pcpu=,stat=,comm= --no-headers 2>/dev/null | head -n 6 || true)
  if [[ -z "${kids// /}" ]]; then
    echo "-"
    return
  fi
  echo "$kids" | awk '{printf "pid=%s etime=%s cpu=%s%% stat=%s cmd=%s; ", $1,$2,$3,$4,$5} END{print ""}'
}

# Paths under .bun / workspace node_modules touched recently (capped, timed).
touched_summary() {
  {
    timeout 4 find node_modules/.bun packages \
      -mmin -2 \( -type f -o -type l \) \
      ! -path '*/.bun/node_modules/*' \
      2>/dev/null \
      | sed -e 's|^node_modules/||' -e 's|^packages/||' \
      | head -n 10
  } | join_csv
}

# Counts that can move during link even when package-dir count is flat.
tree_counts() {
  local bun_ents ws_ents
  # depth-limited: cheap enough for heartbeat; timeout if FS is huge/slow
  bun_ents=$(timeout 4 find node_modules/.bun -mindepth 2 -maxdepth 3 \
    \( -type f -o -type l \) 2>/dev/null | wc -l | tr -d ' ')
  ws_ents=$(timeout 4 find packages -path '*/node_modules/*' -maxdepth 4 \
    \( -type l -o -type d \) 2>/dev/null | wc -l | tr -d ' ')
  bun_ents=${bun_ents:-0}
  ws_ents=${ws_ents:-0}
  echo "bun_ents=${bun_ents} ws_ents=${ws_ents}"
}

log_tail_summary() {
  grep -v '^[[:space:]]*$' "$LOG" 2>/dev/null | tail -n 3 \
    | sed 's/^/    log| /' || true
}

heartbeat() {
  local elapsed=0 prev_pkgs=0 first=1 prev_cpu=0 prev_io_r=0 prev_io_w=0 prev_bun_files=0
  while kill -0 "$bun_pid" 2>/dev/null; do
    sleep 15
    elapsed=$((elapsed + 15))
    kill -0 "$bun_pid" 2>/dev/null || break

    local pkgs cache_entries delta nm_size now_file new_list recent_list new_count
    local proc kids touched counts bun_files cpu_s io_r io_w d_cpu d_ior d_iow d_files

    now_file=/tmp/bun-install-now-pkgs.txt
    list_bun_pkg_dirs >"$now_file"
    pkgs=$(wc -l <"$now_file" | tr -d ' ')
    cache_entries=$(find /root/.bun/install/cache -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')
    delta=$((pkgs - prev_pkgs))
    prev_pkgs=$pkgs
    nm_size=$(du -sh node_modules 2>/dev/null | awk '{print $1}')
    recent_list=$(recent_bun_pkgs 5)
    [[ -n "$recent_list" ]] || recent_list="-"

    if [[ "$first" -eq 1 ]]; then
      new_list="new: (baseline ${pkgs} pkgs)"
      first=0
    else
      new_list=$(new_since_prev "$now_file" "$PREV_PKGS_FILE")
      new_count=$(comm -13 "$PREV_PKGS_FILE" "$now_file" | wc -l | tr -d ' ')
      if [[ "$new_count" -eq 0 ]]; then
        new_list="new(0): -"
      elif [[ -z "$new_list" ]]; then
        new_list="new(${new_count}): (${new_count} pkgs)"
      elif [[ "$new_count" -gt 8 ]]; then
        new_list="new(${new_count}): ${new_list}, …(+$((new_count - 8)) more)"
      else
        new_list="new(${new_count}): ${new_list}"
      fi
    fi
    cp "$now_file" "$PREV_PKGS_FILE"

    proc=$(proc_summary "$bun_pid")
    kids=$(children_summary "$bun_pid")
    touched=$(touched_summary)
    [[ -n "$touched" ]] || touched="-"
    counts=$(tree_counts)

    # Deltas vs previous heartbeat (prove liveness when .bun is flat).
    cpu_s=$(sed -n 's/.*cpu≈\([0-9]*\)s.*/\1/p' <<<"$proc")
    io_r=$(sed -n 's/.*io_r=\([0-9]*\)MB.*/\1/p' <<<"$proc")
    io_w=$(sed -n 's/.*io_w=\([0-9]*\)MB.*/\1/p' <<<"$proc")
    bun_files=$(sed -n 's/.*bun_ents=\([0-9]*\).*/\1/p' <<<"$counts")
    cpu_s=${cpu_s:-0}
    io_r=${io_r:-0}
    io_w=${io_w:-0}
    bun_files=${bun_files:-0}
    d_cpu=$((cpu_s - prev_cpu))
    d_ior=$((io_r - prev_io_r))
    d_iow=$((io_w - prev_io_w))
    d_files=$((bun_files - prev_bun_files))
    prev_cpu=$cpu_s
    prev_io_r=$io_r
    prev_io_w=$io_w
    prev_bun_files=$bun_files

    echo "==> [2/6] still running ${elapsed}s | .bun=${pkgs} (+${delta}) cache=${cache_entries} | node_modules=${nm_size} | ${counts} (Δents=${d_files})"
    echo "    ${new_list}"
    echo "    recent: ${recent_list}"
    echo "    proc: ${proc} (Δcpu=${d_cpu}s Δio_r=${d_ior}MB Δio_w=${d_iow}MB)"
    echo "    children: ${kids}"
    echo "    touched(~2m): ${touched}"
    log_tail_summary
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
