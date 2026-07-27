#!/usr/bin/env python3
"""
Patch build_assets/scripts/transitions.mjs for container layout:

  Require --videodir <dir> (no default ".") in both runInject and runVerify.
  Assigns to hyperframesDir (replaces --hyperframes).

Usage:
  python3 modify/patch-transitions.py [TRANSITIONS_MJS]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "build_assets" / "scripts" / "transitions.mjs"

MARK = "gowtd-mod: transitions paths"

# Upstream: flag(argv, "hyperframes", ".") — two indented call sites (inject + verify).
OLD_HYPERFRAMES = re.compile(
    r'^(?P<indent>\s*)const hyperframesDir = resolve\(flag\(argv, "hyperframes", "\."\)\);\s*$',
    re.M,
)
# Previous modify iteration used --hyperframes; migrate to --videodir.
LEGACY_HYPERFRAMES_ARG = re.compile(
    r'^(?P<indent>\s*)(?:// gowtd-mod: transitions paths\n(?P=indent))?'
    r'const hyperframesArg = flag\(argv, "hyperframes", null\);\s*\n'
    r'(?P=indent)if \(!hyperframesArg\) \{\s*\n'
    r'(?P=indent)  console\.error\("[^"]*"\);\s*\n'
    r'(?P=indent)  process\.exit\(1\);\s*\n'
    r'(?P=indent)\}\s*\n'
    r'(?P=indent)const hyperframesDir = resolve\(hyperframesArg\);\s*$',
    re.M,
)

# Already-patched shape (die/bail are defined later in each function, so use
# inline exit rather than calling them).
PATCHED_VIDEODIR = re.compile(
    r'^(?P<indent>\s*)const videoDirArg = flag\(argv, "videodir", null\);\s*\n'
    r'(?P=indent)if \(!videoDirArg\) \{\s*\n'
    r'(?P=indent)  console\.error\("--videodir <dir> is required"\);\s*\n'
    r'(?P=indent)  process\.exit\(1\);\s*\n'
    r'(?P=indent)\}\s*\n'
    r'(?P=indent)const hyperframesDir = resolve\(videoDirArg\);\s*$',
    re.M,
)

NEW_VIDEODIR_LINES = [
    'const videoDirArg = flag(argv, "videodir", null);',
    "if (!videoDirArg) {",
    '  console.error("--videodir <dir> is required");',
    "  process.exit(1);",
    "}",
    "const hyperframesDir = resolve(videoDirArg);",
]


def indent_block(indent: str, with_mark: bool = False) -> str:
    lines = list(NEW_VIDEODIR_LINES)
    if with_mark:
        lines = [f"// {MARK}"] + lines
    return "\n".join(indent + line for line in lines)


USAGE_OLD = re.compile(
    r'node transitions\.mjs inject --storyboard \./STORYBOARD\.md --hyperframes \.',
)
USAGE_NEW = (
    "node transitions.mjs inject --storyboard ./STORYBOARD.md --videodir ."
)


def _patch_one(text: str, *, add_mark: bool) -> tuple[str, str | None]:
    """Replace a single hyperframesDir assignment. Returns (text, status)."""
    m = LEGACY_HYPERFRAMES_ARG.search(text)
    if m:
        block = indent_block(m.group("indent"), with_mark=add_mark)
        return text[: m.start()] + block + text[m.end() :], "rename --hyperframes → --videodir"

    m = OLD_HYPERFRAMES.search(text)
    if m:
        block = indent_block(m.group("indent"), with_mark=add_mark)
        return text[: m.start()] + block + text[m.end() :], "require --videodir parameter"

    return text, None


def patch(path: Path) -> bool:
    text = path.read_text()
    original = text

    patched_count = len(PATCHED_VIDEODIR.findall(text))
    if patched_count:
        print(f"  [ok] {patched_count} site(s) already require --videodir")

    # Replace all remaining unpatched / legacy sites (expect 2: inject + verify).
    first = True
    for _ in range(4):
        text, status = _patch_one(text, add_mark=first and MARK not in text)
        if status is None:
            break
        print(f"  [patch] {status}")
        first = False

    remaining_old = len(OLD_HYPERFRAMES.findall(text))
    remaining_legacy = len(LEGACY_HYPERFRAMES_ARG.findall(text))
    final_patched = len(PATCHED_VIDEODIR.findall(text))

    if remaining_old or remaining_legacy:
        print(
            "  [error] could not patch all hyperframesDir assignments "
            f"(old={remaining_old}, legacy={remaining_legacy})",
            file=sys.stderr,
        )
        return False

    if final_patched < 2:
        print(
            f"  [error] expected 2 --videodir sites, found {final_patched}",
            file=sys.stderr,
        )
        return False

    if USAGE_OLD.search(text):
        text = USAGE_OLD.sub(USAGE_NEW, text, count=1)
        print("  [patch] header comment --videodir")

    if text == original:
        print(f"  [skip] {path} — already up to date")
        return False

    path.write_text(text)
    print(f"  [write] {path}")
    return True


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_TARGET
    if not target.is_file():
        print(f"error: transitions.mjs not found: {target}", file=sys.stderr)
        return 1

    print(f"patch-transitions: {target}")
    changed = patch(target)
    print("done" if changed else "no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
