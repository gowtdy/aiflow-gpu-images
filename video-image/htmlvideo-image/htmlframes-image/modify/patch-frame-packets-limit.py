#!/usr/bin/env python3
"""
Patch frame-packets-core.mjs: raise maxPacketBytes 48_000 → 100_000.

Usage:
  python3 modify/patch-frame-packets-limit.py [FRAME_PACKETS_CORE_MJS]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = (
    PROJECT_ROOT
    / "build_assets"
    / "hyperframes"
    / "skills"
    / "hyperframes-core"
    / "scripts"
    / "lib"
    / "frame-packets-core.mjs"
)

MARK = "gowtd-mod: frame-packets maxPacketBytes"
OLD = re.compile(r"^(\s*maxPacketBytes\s*=\s*)48_000(,?\s*)$", re.M)
PATCHED = re.compile(
    r"^(\s*maxPacketBytes\s*=\s*)100_000(,?\s*(?://.*)?)?$",
    re.M,
)
NEW = r"\g<1>100_000\2"


def patch(path: Path) -> bool:
    text = path.read_text()
    original = text

    if PATCHED.search(text):
        print("  [ok] maxPacketBytes already 100_000")
    elif OLD.search(text):
        text = OLD.sub(NEW, text, count=1)
        print("  [patch] maxPacketBytes 48_000 → 100_000")
    else:
        print("  [error] could not find maxPacketBytes = 48_000", file=sys.stderr)
        return False

    if MARK not in text:
        text = text.replace(
            "maxPacketBytes = 100_000,",
            f"maxPacketBytes = 100_000, // {MARK}",
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
        print(f"error: frame-packets-core.mjs not found: {target}", file=sys.stderr)
        return 1

    print(f"patch-frame-packets-limit: {target}")
    changed = patch(target)
    print("done" if changed else "no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
