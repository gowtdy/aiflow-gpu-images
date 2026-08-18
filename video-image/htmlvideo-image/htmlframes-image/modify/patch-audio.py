#!/usr/bin/env python3
"""
Patch build_assets/scripts/audio.mjs for container layout:

  1. Require --videodir <dir> (no default ".") in runGenerate / runFetchSfx /
     runSyncDurations. Assigns to hyperframesDir (replaces --hyperframes).
  2. Point DEFAULT_ENGINE at container media-use path
     /app/hyperframes/skills/media-use/audio/scripts/audio_local.mjs

Usage:
  python3 modify/patch-audio.py [AUDIO_MJS]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "build_assets" / "scripts" / "audio.mjs"

ENGINE_PATH = "/app/hyperframes/skills/media-use/audio/scripts/audio_local.mjs"
MARK = "gowtd-mod: audio paths"

# Upstream: flag(argv, "hyperframes", ".") — three indented call sites.
OLD_HYPERFRAMES = re.compile(
    r'^(?P<indent>\s*)const hyperframesDir = resolve\(flag\(argv, "hyperframes", "\."\)\);\s*$',
    re.M,
)
# Previous modify iteration used --hyperframes; migrate to --videodir.
LEGACY_HYPERFRAMES_ARG = re.compile(
    r'^(?P<indent>\s*)(?:// gowtd-mod: audio paths\n(?P=indent))?'
    r'const hyperframesArg = flag\(argv, "hyperframes", null\);\s*\n'
    r'(?P=indent)if \(!hyperframesArg\) die\("--hyperframes <dir> is required"\);\s*\n'
    r'(?P=indent)const hyperframesDir = resolve\(hyperframesArg\);\s*$',
    re.M,
)

# Already-patched shape (each mode defines die() before this assignment).
PATCHED_VIDEODIR = re.compile(
    r'^(?P<indent>\s*)const videoDirArg = flag\(argv, "videodir", null\);\s*\n'
    r'(?P=indent)if \(!videoDirArg\) die\("--videodir <dir> is required"\);\s*\n'
    r'(?P=indent)const hyperframesDir = resolve\(videoDirArg\);\s*$',
    re.M,
)

NEW_VIDEODIR_LINES = [
    'const videoDirArg = flag(argv, "videodir", null);',
    'if (!videoDirArg) die("--videodir <dir> is required");',
    "const hyperframesDir = resolve(videoDirArg);",
]

OLD_ENGINE = re.compile(
    r'^const DEFAULT_ENGINE = join\(HERE, "\.\.", "\.\.", "media-use", "audio", "scripts", "audio\.mjs"\);\s*$',
    re.M,
)
# Any prior absolute/relative DEFAULT_ENGINE assignment.
ANY_ENGINE = re.compile(
    r'^const DEFAULT_ENGINE = .+;\s*$',
    re.M,
)
PATCHED_ENGINE = re.compile(
    rf'^const DEFAULT_ENGINE = "{re.escape(ENGINE_PATH)}";\s*$',
    re.M,
)
NEW_ENGINE = f'const DEFAULT_ENGINE = "{ENGINE_PATH}";'

USAGE_OLD = re.compile(r"--hyperframes")
USAGE_NEW = "--videodir"


def indent_block(indent: str, with_mark: bool = False) -> str:
    lines = list(NEW_VIDEODIR_LINES)
    if with_mark:
        lines = [f"// {MARK}"] + lines
    return "\n".join(indent + line for line in lines)


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

    # Replace all remaining unpatched / legacy sites (expect 3: generate / fetch-sfx / sync-durations).
    first = True
    for _ in range(6):
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

    if final_patched < 3:
        print(
            f"  [error] expected 3 --videodir sites, found {final_patched}",
            file=sys.stderr,
        )
        return False

    if PATCHED_ENGINE.search(text):
        print("  [ok] DEFAULT_ENGINE already uses container path")
    elif OLD_ENGINE.search(text):
        text = OLD_ENGINE.sub(NEW_ENGINE, text, count=1)
        print(f"  [patch] DEFAULT_ENGINE → {ENGINE_PATH}")
    elif ANY_ENGINE.search(text):
        text = ANY_ENGINE.sub(NEW_ENGINE, text, count=1)
        print(f"  [patch] DEFAULT_ENGINE → {ENGINE_PATH}")
    else:
        print("  [error] could not find DEFAULT_ENGINE assignment", file=sys.stderr)
        return False

    # Header usage comments only (do not touch engine argv "--hyperframes" passed to media-use).
    usage_hits = 0
    lines = text.splitlines(keepends=True)
    out_lines = []
    for line in lines:
        if line.lstrip().startswith("//") and "--hyperframes" in line:
            line = USAGE_OLD.sub(USAGE_NEW, line)
            usage_hits += 1
        out_lines.append(line)
    if usage_hits:
        text = "".join(out_lines)
        print(f"  [patch] header comment --videodir ({usage_hits})")

    if text == original:
        print(f"  [skip] {path} — already up to date")
        return False

    path.write_text(text)
    print(f"  [write] {path}")
    return True


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_TARGET
    if not target.is_file():
        print(f"error: audio.mjs not found: {target}", file=sys.stderr)
        return 1

    print(f"patch-audio: {target}")
    changed = patch(target)
    print("done" if changed else "no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
