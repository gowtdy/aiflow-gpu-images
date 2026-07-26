#!/usr/bin/env python3
"""
Patch build_assets/scripts/assemble-index.mjs for container layout:

  1. Require --videodir <dir> (no default ".")
     Assigns to hyperframesDir (replaces --hyperframes).
  2. Point bgmDefaultVolume import at container media-use path
     /app/hyperframes/skills/media-use/audio/scripts/lib/bgm.mjs

Usage:
  python3 modify/patch-assemble-index.py [ASSEMBLE_INDEX_MJS]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "build_assets" / "scripts" / "assemble-index.mjs"

BGM_IMPORT_NEW = (
    'import { bgmDefaultVolume } from '
    '"/app/hyperframes/skills/media-use/audio/scripts/lib/bgm.mjs";'
)

# Idempotent sentinels (appear in replaced code comments / markers).
MARK = "gowtd-mod: assemble-index paths"

OLD_HYPERFRAMES = re.compile(
    r'^const hyperframesDir = resolve\(flag\("hyperframes", "\."\)\);\s*$',
    re.M,
)
# Previous modify iteration used --hyperframes; migrate to --videodir.
LEGACY_HYPERFRAMES_ARG = re.compile(
    r'^(?:// gowtd-mod: assemble-index paths\n)?'
    r'const hyperframesArg = flag\("hyperframes", null\);\s*\n'
    r'if \(!hyperframesArg\) die\("--hyperframes <dir> is required"\);\s*\n'
    r'const hyperframesDir = resolve\(hyperframesArg\);\s*$',
    re.M,
)

# Already-patched shapes (allow re-run / path refresh).
PATCHED_VIDEODIR = re.compile(
    r'^const videoDirArg = flag\("videodir", null\);\s*\n'
    r'if \(!videoDirArg\) die\("--videodir <dir> is required"\);\s*\n'
    r'const hyperframesDir = resolve\(videoDirArg\);\s*$',
    re.M,
)

NEW_VIDEODIR = """\
const videoDirArg = flag("videodir", null);
if (!videoDirArg) die("--videodir <dir> is required");
const hyperframesDir = resolve(videoDirArg);
"""

USAGE_OLD = re.compile(
    r'--hyperframes <project root>',
)
USAGE_NEW = "--videodir <project root>"

# Upstream relative import, or any prior absolute/relative variant of the same module.
OLD_BGM_IMPORT = re.compile(
    r'^import \{ bgmDefaultVolume \} from "[^"]*media-use/audio/scripts/lib/bgm\.mjs";\s*$',
    re.M,
)
PATCHED_BGM_IMPORT = re.compile(
    r'^import \{ bgmDefaultVolume \} from '
    r'"/app/hyperframes/skills/media-use/audio/scripts/lib/bgm\.mjs";\s*$',
    re.M,
)


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

    if USAGE_OLD.search(text):
        text = USAGE_OLD.sub(USAGE_NEW, text, count=1)
        print("  [patch] header comment --videodir")

    if PATCHED_BGM_IMPORT.search(text):
        print("  [ok] bgmDefaultVolume import already uses container path")
    elif OLD_BGM_IMPORT.search(text):
        text = OLD_BGM_IMPORT.sub(BGM_IMPORT_NEW, text, count=1)
        print("  [patch] bgmDefaultVolume import → /app/hyperframes/skills/media-use/...")
    else:
        print("  [error] could not find bgmDefaultVolume import", file=sys.stderr)
        return False

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
        print(f"error: assemble-index.mjs not found: {target}", file=sys.stderr)
        return 1

    print(f"patch-assemble-index: {target}")
    changed = patch(target)
    print("done" if changed else "no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
