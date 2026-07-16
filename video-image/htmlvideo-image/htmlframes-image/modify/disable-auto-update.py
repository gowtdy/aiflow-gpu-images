#!/usr/bin/env python3
"""
Comment out auto-update logic in build_assets/hyperframes.

Modifies:
  1. packages/cli/src/cli.ts
     - Blocks the background update check + auto-install block
     - Blocks the beforeExit update-notice prints
  2. packages/cli/src/commands/init.ts
     - Blocks the keepSkillsCurrent() calls (auto skills-freshness check)

Usage:
  python3 modify/disable-auto-update.py
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HYPERFRAMES_ROOT = PROJECT_ROOT / "build_assets" / "hyperframes"

CLI_TS = HYPERFRAMES_ROOT / "packages" / "cli" / "src" / "cli.ts"
INIT_TS = HYPERFRAMES_ROOT / "packages" / "cli" / "src" / "commands" / "init.ts"

# Sentinel comments we inject so the script is idempotent.
# These are used WITHOUT the "// " prefix so the comment_lines function
# can prepend its own "// " without producing "// // ".
MARK_BEGIN = "gowtd-mod: auto-update disabled begin"
MARK_END = "gowtd-mod: auto-update disabled end"


def comment_lines(lines: list[str], start: int, end: int) -> list[str]:
    """Prefix lines[start:end] with '//' (preserving indent)."""
    for i in range(start, end):
        stripped = lines[i].rstrip("\n")
        if stripped.strip() == "":
            # Preserve blank lines as-is
            lines[i] = "\n" if lines[i].endswith("\n") else ""
        elif stripped.strip().startswith("//"):
            # Already commented
            lines[i] = stripped + "\n" if not stripped.endswith("\n") else stripped
        else:
            lines[i] = lines[i].replace(stripped, "// " + stripped, 1)
    return lines


def block_comment_lines(lines: list[str], start: int, end: int) -> list[str]:
    """Wrap lines[start:end] in /* */ block comment with sentinel markers inside."""
    # Find the indent of the first non-empty line
    indent = ""
    for i in range(start, end):
        m = re.match(r"^(\s*)", lines[i])
        if m and lines[i].strip():
            indent = m.group(1)
            break

    lines.insert(start, f"{indent}/* {MARK_BEGIN}\n")
    lines.insert(end + 1, f"{indent}{MARK_END} */\n")
    return lines


def process_cli_ts(path: Path) -> bool:
    """Comment out auto-update logic in cli.ts."""
    content = path.read_text()
    if MARK_BEGIN in content:
        print(f"  [skip] {path.relative_to(PROJECT_ROOT)} — already processed")
        return False

    lines = content.splitlines(keepends=True)

    # ----------------------------------------------------------------
    # Block 1: the auto-update check block (if statement that does
    # reportCompletedUpdate / checkForUpdate / scheduleBackgroundInstall /
    # checkSkillsForUpdate).
    # It starts with the comment:
    #   // `events` skips the update check too ...
    # and the if-block follows immediately after that comment block.
    # We find the if () { ... } that contains 'autoUpdate.js' or
    # 'updateCheck.js' or 'skillsUpdateCheck.js'.
    # ----------------------------------------------------------------
    block1_start = None
    block1_end = None

    for i, line in enumerate(lines):
        if block1_start is None:
            if (
                "autoUpdate.js" in line
                and "reportCompletedUpdate" in line
                and line.strip().startswith("import(")
            ):
                # Walk backwards to find the `if (` line
                for j in range(i, -1, -1):
                    if re.match(r"^\s*if\s*\(\s*$", lines[j]):
                        block1_start = j
                        break
        if block1_start is not None and block1_end is None:
            # Walk forward to find the matching closing brace.
            # The if-block ends with a `}` that is at the same indent level
            # as the `if`.
            if_block_indent = len(re.match(r"^(\s*)", lines[block1_start]).group(1))
            if lines[i].rstrip() == "}" and len(re.match(r"^(\s*)", lines[i]).group(1)) == if_block_indent:
                # Verify this is the right closing brace by checking the
                # next significant line is `const commandStart`
                for j in range(i + 1, min(i + 5, len(lines))):
                    if "const commandStart" in lines[j]:
                        block1_end = i + 1  # inclusive
                        break
                if block1_end is not None:
                    break

    if block1_start is None or block1_end is None:
        print(f"  [warn] Could not locate auto-update if-block in cli.ts")
        return False

    print(f"  Block 1 (auto-update check): lines {block1_start + 1}-{block1_end}")

    # ----------------------------------------------------------------
    # Block 2: the beforeExit handler that prints update notices.
    #   _printUpdateNotice?.();
    #   _printSkillsUpdateNotice?.();
    # ----------------------------------------------------------------
    block2_start = None
    block2_end = None

    for i, line in enumerate(lines):
        if "_printUpdateNotice?.()" in line:
            # This line and the next one (_printSkillsUpdateNotice) should be
            # commented out
            block2_start = i
            # The next line should be _printSkillsUpdateNotice
            if i + 1 < len(lines) and "_printSkillsUpdateNotice?.()" in lines[i + 1]:
                block2_end = i + 2  # exclusive
            else:
                block2_end = i + 1  # exclusive
            break

    if block2_start is None:
        print(f"  [warn] Could not locate beforeExit update notices in cli.ts")
        return False

    print(f"  Block 2 (beforeExit notices): lines {block2_start + 1}-{block2_end}")

    # Apply edits in reverse order so line numbers stay valid.
    # Block 2 is later in the file, so process it first.
    lines = comment_lines(lines, block2_start, block2_end)
    # Block 1 is earlier — use block comment for the whole if-block
    lines = block_comment_lines(lines, block1_start, block1_end)

    path.write_text("".join(lines))
    return True


def process_init_ts(path: Path) -> bool:
    """Comment out keepSkillsCurrent() calls in init.ts."""
    content = path.read_text()
    if MARK_BEGIN in content:
        print(f"  [skip] {path.relative_to(PROJECT_ROOT)} — already processed")
        return False

    lines = content.splitlines(keepends=True)

    changes = 0
    for i, line in enumerate(lines):
        if "keepSkillsCurrent(destDir)" in line and "await keepSkillsCurrent" in line.strip():
            indent = re.match(r"^(\s*)", line).group(1)
            # Replace the entire line with a commented-out version + sentinel markers
            lines[i] = (
                f"{indent}// {MARK_BEGIN}\n"
                f"{indent}// await keepSkillsCurrent(destDir);  // {MARK_END}\n"
            )
            changes += 1
            print(f"  Commented out keepSkillsCurrent() at line {i + 1}")

    if changes == 0:
        print(f"  [warn] No keepSkillsCurrent() calls found in init.ts")
        return False

    path.write_text("".join(lines))
    return True


def main():
    print("Disabling auto-update logic in build_assets/hyperframes...\n")

    if not CLI_TS.exists():
        print(f"ERROR: {CLI_TS} not found", file=sys.stderr)
        sys.exit(1)
    if not INIT_TS.exists():
        print(f"ERROR: {INIT_TS} not found", file=sys.stderr)
        sys.exit(1)

    print(f"[1/2] {CLI_TS.relative_to(PROJECT_ROOT)}")
    changed1 = process_cli_ts(CLI_TS)

    print(f"\n[2/2] {INIT_TS.relative_to(PROJECT_ROOT)}")
    changed2 = process_init_ts(INIT_TS)

    print()
    if changed1 or changed2:
        print("Done. Auto-update logic has been commented out.")
    else:
        print("No changes needed (already processed).")


if __name__ == "__main__":
    main()