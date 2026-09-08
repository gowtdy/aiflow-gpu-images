#!/usr/bin/env bash
# Download ALL build assets for offline Docker build.
#
# Run this ONCE on a Ubuntu 24.04 (noble) amd64 machine to populate
# build_assets/software/ with everything the Dockerfiles need:
#   - Node.js, Chrome Headless Shell, Bun (binary archives)
#   - Font .deb packages (for offline dpkg -i)
#
# After running, the Docker builds need NO network for these assets.
#
# Usage:
#   ./download-font-packages.sh                      # download everything (default)
#   NODE_VERSION=24.18.0 ./download-font-packages.sh  # override versions
#
# Output:
#   build_assets/software/node-v24.18.0-linux-x64.tar.xz      (~31 MB)
#   build_assets/software/chrome-headless-shell-linux64.zip    (~114 MB)
#   build_assets/software/bun-linux-x64.zip                    (~35 MB)
#   build_assets/software/fonts/*.deb                          (~175 MB)
#   Total: ~355 MB
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOFTWARE_DIR="${SCRIPT_DIR}/build_assets/software"
FONTS_DIR="${SOFTWARE_DIR}/fonts"
mkdir -p "${SOFTWARE_DIR}" "${FONTS_DIR}"

# ── Versions (match Dockerfiles) ───────────────────────────────────────────────
NODE_VERSION="${NODE_VERSION:-24.18.0}"
CHROME_VERSION="${CHROME_HEADLESS_SHELL_VERSION:-148.0.7778.167}"
BUN_VERSION="${BUN_VERSION:-1.3.14}"

# ── Mirrors (China-friendly by default; set MIRROR=official for global) ────────
MIRROR="${MIRROR:-cn}"
if [ "${MIRROR}" = "cn" ]; then
  NODE_MIRROR="${NODE_MIRROR:-https://npmmirror.com/mirrors/node}"
  CHROME_MIRROR="${CHROME_MIRROR:-https://npmmirror.com/mirrors/chrome-for-testing}"
  BUN_MIRROR="${BUN_MIRROR:-https://registry.npmmirror.com/-/binary/bun}"
else
  NODE_MIRROR="${NODE_MIRROR:-https://nodejs.org/dist}"
  CHROME_MIRROR="${CHROME_MIRROR:-https://storage.googleapis.com/chrome-for-testing-public}"
  BUN_MIRROR="${BUN_MIRROR:-https://github.com/oven-sh/bun/releases/download}"
fi

download() {
  local url="$1" out="$2" label="${3:-}"
  if [ -f "${out}" ]; then
    echo "    [SKIP] ${label:-$(basename "${out}")} already exists"
    return 0
  fi
  echo "    [FETCH] ${label:-$(basename "${out}")}"
  echo "        ${url}"
  # wget with resume + retry; fallback to curl
  if command -v wget &>/dev/null; then
    wget -c -t 3 --timeout=120 -O "${out}.tmp" "${url}" && mv "${out}.tmp" "${out}"
  else
    curl -C - --retry 3 --connect-timeout 30 --max-time 600 -L -o "${out}.tmp" "${url}" && mv "${out}.tmp" "${out}"
  fi
  echo "        → $(du -h "${out}" | cut -f1)"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Node.js
# ═══════════════════════════════════════════════════════════════════════════════
NODE_FILE="node-v${NODE_VERSION}-linux-x64.tar.xz"
if [ "${MIRROR}" = "cn" ]; then
  NODE_URL="${NODE_MIRROR}/v${NODE_VERSION}/${NODE_FILE}"
else
  NODE_URL="${NODE_MIRROR}/v${NODE_VERSION}/${NODE_FILE}"
fi
download "${NODE_URL}" "${SOFTWARE_DIR}/${NODE_FILE}" "Node.js v${NODE_VERSION}"

# ═══════════════════════════════════════════════════════════════════════════════
# 2. Chrome Headless Shell
# ═══════════════════════════════════════════════════════════════════════════════
CHROME_FILE="chrome-headless-shell-linux64.zip"
if [ "${MIRROR}" = "cn" ]; then
  CHROME_URL="${CHROME_MIRROR}/${CHROME_VERSION}/linux64/${CHROME_FILE}"
else
  CHROME_URL="${CHROME_MIRROR}/${CHROME_VERSION}/linux64/${CHROME_FILE}"
fi
download "${CHROME_URL}" "${SOFTWARE_DIR}/${CHROME_FILE}" "Chrome Headless Shell ${CHROME_VERSION}"

# ═══════════════════════════════════════════════════════════════════════════════
# 3. Bun
# ═══════════════════════════════════════════════════════════════════════════════
BUN_FILE="bun-linux-x64.zip"
if [ "${MIRROR}" = "cn" ]; then
  BUN_URL="${BUN_MIRROR}/v${BUN_VERSION}/${BUN_FILE}"
else
  BUN_URL="${BUN_MIRROR}/bun-v${BUN_VERSION}/${BUN_FILE}"
fi
download "${BUN_URL}" "${SOFTWARE_DIR}/${BUN_FILE}" "Bun v${BUN_VERSION}"

# ═══════════════════════════════════════════════════════════════════════════════
# 4. Font .deb packages (require Ubuntu 24.04 + apt)
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "==> Downloading font .deb packages..."

# These must match the fallback list in Dockerfile.runtime.
FONT_PACKAGES=(
  fonts-liberation
  fonts-noto-color-emoji
  fonts-noto-cjk
  fonts-noto-core
  fonts-noto-extra
  fonts-noto-ui-core
  fonts-freefont-ttf
  fonts-dejavu-core
  fontconfig
)

# Refresh apt cache
sudo apt-get update -qq 2>/dev/null || {
  echo "    WARNING: apt-get update failed; skipping font .deb download"
  echo "    Run on Ubuntu 24.04 (noble) to download font packages"
}

for pkg in "${FONT_PACKAGES[@]}"; do
  # Check if already downloaded
  if ls "${FONTS_DIR}/${pkg}"_*.deb &>/dev/null 2>&1 || \
     ls "${FONTS_DIR}/${pkg}"_*.deb &>/dev/null 2>&1; then
    echo "    [SKIP] ${pkg} already present"
    continue
  fi
  echo "    [FETCH] ${pkg}..."
  (cd "${FONTS_DIR}" && apt-get download "${pkg}" 2>/dev/null && echo "    [OK]   ${pkg}") || \
    echo "    [WARN] ${pkg} failed (may be in base image or unresolvable)"
done

# Download transitively pulled fonts-noto-mono
echo "    [FETCH] fonts-noto-mono (transitive dependency)..."
(cd "${FONTS_DIR}" && apt-get download fonts-noto-mono 2>/dev/null && echo "    [OK]   fonts-noto-mono") || \
  echo "    [WARN] fonts-noto-mono failed"

sudo rm -rf /var/lib/apt/lists/*

# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Download complete — ${SOFTWARE_DIR}"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  Software archives:"
ls -lh "${SOFTWARE_DIR}"/*.tar.xz "${SOFTWARE_DIR}"/*.zip 2>/dev/null || true
echo ""
echo "  Font .deb packages:"
ls -lh "${FONTS_DIR}/"*.deb 2>/dev/null || echo "    (none — run on Ubuntu 24.04)"
echo ""
echo "  Total: $(du -sh "${SOFTWARE_DIR}" | cut -f1)"
echo ""
echo "  Done. Ready for offline build:"
echo "    ./build-htmlframes-runtime-image.sh"
echo "    ./build-htmlframes-builder-image.sh"