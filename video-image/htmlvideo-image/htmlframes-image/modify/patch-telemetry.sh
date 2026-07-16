#!/usr/bin/env bash
# Patch HyperFrames telemetry → mogofun.com proxy
#
# Usage:
#   ./patch-telemetry.sh [BUILD_ASSETS_DIR]
# Default: ../build_assets/hyperframes (relative to this script)

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly HF_ROOT="${1:-${SCRIPT_DIR}/../build_assets/hyperframes}"

readonly TELEMETRY_HOST="https://mogofun.com"
readonly TELEMETRY_BATCH_PATH="/lapi/htmlvideo/batch/"

readonly TELEMETRY_FILES=(
  "packages/cli/src/telemetry/client.ts"
  "packages/studio/src/utils/studioTelemetry.ts"
  "packages/studio/src/telemetry/client.ts"
)

log() { printf '[patch-telemetry] %s\n' "$*"; }
die() { printf '[patch-telemetry] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -d "${HF_ROOT}" ]] || die "HyperFrames root not found: ${HF_ROOT}"

rewrite_posthog_host() {
  local indent="$1"
  local host="$2"
  printf '%s// const POSTHOG_HOST = "https://us.i.posthog.com";  // gowtd mod\n' "${indent}"
  printf '%sconst POSTHOG_HOST = "%s";\n' "${indent}" "${host}"
}

patch_file() {
  local file="$1"
  local tmp
  tmp="$(mktemp)"

  local line indent
  # Keep regex in a variable: unquoted ';' inside [[ =~ ]] is a syntax error.
  local host_re='^([[:space:]]*)const POSTHOG_HOST = "(https://us\.i\.posthog\.com|https://mogofun\.com|https://mogofu\.com)";[[:space:]]*$'
  # Patterns with '/' must live in variables — ${var//pat/repl} treats '/' as delimiter.
  local old_batch='${POSTHOG_HOST}/batch/'
  local new_batch='${POSTHOG_HOST}'"${TELEMETRY_BATCH_PATH}"
  local old_url='https://us.i.posthog.com/batch/'
  local new_url="${TELEMETRY_HOST}${TELEMETRY_BATCH_PATH}"
  local bad_batch="${TELEMETRY_HOST}/batch/"

  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" =~ $host_re ]]; then
      indent="${BASH_REMATCH[1]}"
      rewrite_posthog_host "${indent}" "${TELEMETRY_HOST}"
      continue
    fi

    line="${line//"$old_batch"/$new_batch}"
    line="${line//"$old_url"/$new_url}"

    if [[ "${line}" == *"$bad_batch"* ]] \
      && [[ "${line}" != *"$new_url"* ]]; then
      line="${line//"$bad_batch"/$new_url}"
    fi

    printf '%s\n' "${line}"
  done < "${file}" > "${tmp}"

  grep -q 'const POSTHOG_HOST = "'"${TELEMETRY_HOST}"'"' "${tmp}" \
    || die "failed to set POSTHOG_HOST in ${file}"
  grep -qE '\$\{POSTHOG_HOST\}/batch/|https://us\.i\.posthog\.com/batch/' "${tmp}" \
    && die "leftover /batch/ endpoint in ${file}"

  mv "${tmp}" "${file}"
}

log "HyperFrames root: ${HF_ROOT}"
log "Telemetry host: ${TELEMETRY_HOST}"
log "Telemetry path: ${TELEMETRY_BATCH_PATH}"

patched=0
for rel in "${TELEMETRY_FILES[@]}"; do
  file="${HF_ROOT}/${rel}"
  if [[ ! -f "${file}" ]]; then
    log "skip (missing): ${rel}"
    continue
  fi
  if ! grep -q 'POSTHOG_HOST' "${file}"; then
    log "skip (no POSTHOG_HOST): ${rel}"
    continue
  fi
  patch_file "${file}"
  log "patched: ${rel}"
  patched=$((patched + 1))
done

[[ "${patched}" -gt 0 ]] || die "no telemetry files were patched"
log "done (${patched} file(s) patched)"