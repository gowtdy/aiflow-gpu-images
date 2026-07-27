#!/usr/bin/env python3
"""
Patch build_assets/scripts/frame-packets.mjs for container layout:

  1. Point core import at
     /app/hyperframes/skills/hyperframes-core/scripts/lib/frame-packets-core.mjs
  2. Pin SKILL_DIR to
     /app/hyperframes/skills/aiflow-build-frame-html

Usage:
  python3 modify/patch-frame-packets.py [FRAME_PACKETS_MJS]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "build_assets" / "scripts" / "frame-packets.mjs"

CORE_IMPORT_NEW = (
    'import * as core from '
    '"/app/hyperframes/skills/hyperframes-core/scripts/lib/frame-packets-core.mjs";'
)
SKILL_DIR_NEW = 'const SKILL_DIR = "/app/hyperframes/skills/aiflow-build-frame-html";'

MARK = "gowtd-mod: frame-packets paths"

# Upstream relative import, or any prior absolute/relative variant of the same module.
OLD_CORE_IMPORT = re.compile(
    r'^import \* as core from "[^"]*frame-packets-core\.mjs";\s*$',
    re.M,
)
PATCHED_CORE_IMPORT = re.compile(
    r'^import \* as core from '
    r'"/app/hyperframes/skills/hyperframes-core/scripts/lib/frame-packets-core\.mjs";\s*$',
    re.M,
)

# Upstream: resolve from this file's parent dir.
OLD_SKILL_DIR = re.compile(
    r'^const SKILL_DIR = resolve\(dirname\(fileURLToPath\(import\.meta\.url\)\), "\.\."\);\s*$',
    re.M,
)
# Already-patched (allow re-run / path refresh).
PATCHED_SKILL_DIR = re.compile(
    r'^const SKILL_DIR = "/app/hyperframes(?:/skills)?/aiflow-build-frame-html";\s*$',
    re.M,
)

# Drop dirname/fileURLToPath once SKILL_DIR is a literal (resolve stays for CONFIG).
OLD_PATH_IMPORTS = re.compile(
    r'^import \{ dirname, resolve \} from "node:path";\s*\n'
    r'import \{ fileURLToPath \} from "node:url";\s*\n',
    re.M,
)
PATCHED_PATH_IMPORT = re.compile(
    r'^import \{ resolve \} from "node:path";\s*$',
    re.M,
)
NEW_PATH_IMPORT = 'import { resolve } from "node:path";\n'


def patch(path: Path) -> bool:
    text = path.read_text()
    original = text

    if PATCHED_CORE_IMPORT.search(text):
        print("  [ok] core import already uses container path")
    elif OLD_CORE_IMPORT.search(text):
        text = OLD_CORE_IMPORT.sub(CORE_IMPORT_NEW, text, count=1)
        print(
            "  [patch] core import → "
            "/app/hyperframes/skills/hyperframes-core/scripts/lib/frame-packets-core.mjs"
        )
    else:
        print("  [error] could not find frame-packets-core import", file=sys.stderr)
        return False

    if PATCHED_SKILL_DIR.search(text):
        text2 = PATCHED_SKILL_DIR.sub(SKILL_DIR_NEW, text, count=1)
        if text2 != text:
            text = text2
            print(
                "  [patch] refresh SKILL_DIR → "
                "/app/hyperframes/skills/aiflow-build-frame-html"
            )
        else:
            print(
                "  [ok] SKILL_DIR already pinned to "
                "/app/hyperframes/skills/aiflow-build-frame-html"
            )
    elif OLD_SKILL_DIR.search(text):
        text = OLD_SKILL_DIR.sub(SKILL_DIR_NEW, text, count=1)
        print(
            "  [patch] SKILL_DIR → "
            "/app/hyperframes/skills/aiflow-build-frame-html"
        )
    else:
        print("  [error] could not find SKILL_DIR assignment", file=sys.stderr)
        return False

    if PATCHED_PATH_IMPORT.search(text):
        print("  [ok] path imports already trimmed")
    elif OLD_PATH_IMPORTS.search(text):
        text = OLD_PATH_IMPORTS.sub(NEW_PATH_IMPORT, text, count=1)
        print("  [patch] drop unused dirname / fileURLToPath imports")

    if MARK not in text:
        text = text.replace(
            SKILL_DIR_NEW,
            f"// {MARK}\n{SKILL_DIR_NEW}",
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
        print(f"error: frame-packets.mjs not found: {target}", file=sys.stderr)
        return 1

    print(f"patch-frame-packets: {target}")
    changed = patch(target)
    print("done" if changed else "no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
