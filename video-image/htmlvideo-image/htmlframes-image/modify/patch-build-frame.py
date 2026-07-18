#!/usr/bin/env python3
"""
Patch build_assets/scripts/build-frame.mjs for container layout:

  1. Require --videodir <dir> (no default ".")
  2. Default --preset-dir to
     /app/hyperframes/skills/hyperframes-creative/frame-presets

Usage:
  python3 modify/patch-build-frame.py [BUILD_FRAME_MJS]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "build_assets" / "scripts" / "build-frame.mjs"

PRESET_DIR_DEFAULT = "/app/hyperframes/skills/hyperframes-creative/frame-presets"

# Idempotent sentinels (appear in replaced code comments / markers).
MARK = "gowtd-mod: build-frame paths"

OLD_HYPERFRAMES = re.compile(
    r'^const hyperframesDir = resolve\(flag\("hyperframes", "\."\)\);\s*$',
    re.M,
)
# Previous modify iteration used --hyperframes; migrate to --videodir.
LEGACY_HYPERFRAMES_ARG = re.compile(
    r'^(?:// gowtd-mod: build-frame paths\n)?'
    r'const hyperframesArg = flag\("hyperframes", null\);\s*\n'
    r'if \(!hyperframesArg\) die\("--hyperframes <dir> is required"\);\s*\n'
    r'const hyperframesDir = resolve\(hyperframesArg\);\s*$',
    re.M,
)
OLD_PRESET_DIR = re.compile(
    r'^const presetDir = resolve\(\s*\n'
    r'\s*flag\("preset-dir", join\(__dirname, "[^"]+"\)\),\s*\n'
    r'\s*\);\s*$',
    re.M,
)

# Already-patched shapes (allow re-run / path refresh).
PATCHED_VIDEODIR = re.compile(
    r'^const videoDirArg = flag\("videodir", null\);\s*\n'
    r'if \(!videoDirArg\) die\("--videodir <dir> is required"\);\s*\n'
    r'const hyperframesDir = resolve\(videoDirArg\);\s*$',
    re.M,
)
PATCHED_PRESET_DIR = re.compile(
    r'^const presetDir = resolve\(\s*\n'
    r'\s*flag\("preset-dir", "[^"]+"\),\s*\n'
    r'\s*\);\s*$',
    re.M,
)

NEW_VIDEODIR = """\
const videoDirArg = flag("videodir", null);
if (!videoDirArg) die("--videodir <dir> is required");
const hyperframesDir = resolve(videoDirArg);
"""

NEW_PRESET_DIR = f"""\
const presetDir = resolve(
  flag("preset-dir", "{PRESET_DIR_DEFAULT}"),
);
"""

USAGE_OLD = re.compile(
    r'node build-frame\.mjs --preset capsule --hyperframes \.',
)
USAGE_NEW = "node build-frame.mjs --preset capsule --videodir ."


def patch(path: Path) -> bool:
    text = path.read_text()
    original = text

    if PATCHED_VIDEODIR.search(text):
        print("  [ok] hyperframesDir already requires --videodir")
    elif LEGACY_HYPERFRAMES_ARG.search(text):
        text = LEGACY_HYPERFRAMES_ARG.sub(NEW_VIDEODIR.rstrip("\n"), text, count=1)
        print("  [patch] rename --hyperframes → --videodir")
    elif OLD_HYPERFRAMES.search(text):
        text = OLD_HYPERFRAMES.sub(NEW_VIDEODIR.rstrip("\n"), text, count=1)
        print("  [patch] require --videodir parameter")
    else:
        print("  [error] could not find hyperframesDir assignment", file=sys.stderr)
        return False

    if PATCHED_PRESET_DIR.search(text):
        text2 = PATCHED_PRESET_DIR.sub(NEW_PRESET_DIR.rstrip("\n"), text, count=1)
        if text2 != text:
            text = text2
            print(f"  [patch] refresh presetDir default → {PRESET_DIR_DEFAULT}")
        else:
            print(f"  [ok] presetDir already defaults to {PRESET_DIR_DEFAULT}")
    elif OLD_PRESET_DIR.search(text):
        text = OLD_PRESET_DIR.sub(NEW_PRESET_DIR.rstrip("\n"), text, count=1)
        print(f"  [patch] presetDir default → {PRESET_DIR_DEFAULT}")
    else:
        print("  [error] could not find presetDir assignment", file=sys.stderr)
        return False

    if USAGE_OLD.search(text):
        text = USAGE_OLD.sub(USAGE_NEW, text, count=1)
        print("  [patch] usage comment --videodir")

    if MARK not in text:
        text = text.replace(
            NEW_VIDEODIR.rstrip("\n"),
            f"// {MARK}\n{NEW_VIDEODIR.rstrip(chr(10))}",
            1,
        )

    if text == original:
        print(f"  [skip] {path} — already up to date")
        return False

    path.write_text(text)
    print(f"  [write] {path}")
    return True


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_TARGET
    if not target.is_file():
        print(f"error: build-frame.mjs not found: {target}", file=sys.stderr)
        return 1

    print(f"patch-build-frame: {target}")
    changed = patch(target)
    print("done" if changed else "no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
