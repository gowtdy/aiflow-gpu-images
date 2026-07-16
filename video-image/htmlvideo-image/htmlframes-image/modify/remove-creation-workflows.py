#!/usr/bin/env python3
"""
Remove the "Creation workflows" section from CLAUDE.md and AGENTS.md files
under the specified directory.

Handles four section formats:

  1. CLAUDE.md heading style:
     ### Creation workflows
     <blank line>
     - /workflow-skill ...
     ...
     <blank line>
     ### Domain skills ...

  2. AGENTS.md bold-text style:
     **Creation workflows** ... paragraph ...
     <blank line>
     - /workflow-skill ...
     ...
     <blank line>
     (next section)

  3. AGENTS.md bold-text style (variant):
     **Video-creation workflows** ... paragraph ...
     <blank line>
     - /workflow-skill ...
     ...
     <blank line>
     (next section)

  4. Template file style (no heading, inline intro):
     ... The workflows it routes to:
     <blank line>
     - /workflow-skill ...
     ...
     <blank line>
     (next section)

Usage:
  python3 remove-creation-workflows.py [target_dir]
"""

import os
import sys
import re


def _skip_bullet_list(lines, i):
    """Skip blank line, all bullet-point lines, and optionally a trailing blank line.

    Returns the new index after consuming the list.
    """
    # --- Skip the blank line after the header/intro ---
    if i < len(lines) and lines[i].strip() == "":
        i += 1

    # --- Skip all bullet-point lines ---
    while i < len(lines) and lines[i].strip().startswith("- "):
        i += 1

    # --- Optionally skip the trailing blank line when the next
    #     non-empty line is a heading or bold section marker ---
    if i < len(lines) and lines[i].strip() == "":
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines):
            next_stripped = lines[j].strip()
            if (
                next_stripped.startswith("### ")
                or next_stripped.startswith("## ")
                or next_stripped.startswith("**")
            ):
                i += 1  # consume the separating blank line

    return i


def remove_creation_workflows_section(lines):
    """Remove lines belonging to the "Creation workflows" section."""
    result = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # --- Format 1-3: heading-based section markers ---
        is_header = (
            stripped.startswith("### Creation workflows")
            or stripped.startswith("**Creation workflows**")
            or stripped.startswith("**Video-creation workflows**")
        )

        if is_header:
            i += 1  # skip the header line
            i = _skip_bullet_list(lines, i)
            continue

        # --- Format 4: template-file inline intro ---
        #     "... The workflows it routes to:"
        if "The workflows it routes to:" in stripped:
            # Remove the trailing clause, keep the rest of the paragraph.
            # Work on the stripped line so the regex doesn't consume the
            # trailing newline, then re-attach the original line ending.
            orig = lines[i]
            ending = ""
            if orig.endswith("\n"):
                ending = "\n"
            elif orig.endswith("\r"):
                ending = "\r"
            modified = re.sub(
                r"\s*The workflows it routes to:\s*$",
                "",
                orig.rstrip("\n\r"),
            )
            result.append(modified + ending)
            i += 1
            i = _skip_bullet_list(lines, i)
            continue

        result.append(lines[i])
        i += 1

    return result


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "build_assets", "hyperframes",
    )
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
    )
    fallback = os.path.join(
        repo_root,
        "video-image", "htmlvideo-image", "htmlframes-image",
        "build_assets", "hyperframes",
    )

    if not os.path.isdir(target_dir):
        if os.path.isdir(fallback):
            target_dir = fallback
        else:
            print(f"Error: target directory '{target_dir}' not found.", file=sys.stderr)
            sys.exit(1)

    print(f"Scanning: {target_dir}")

    count = 0
    for root, _dirs, files in os.walk(target_dir):
        for name in files:
            if name not in ("CLAUDE.md", "AGENTS.md"):
                continue

            filepath = os.path.join(root, name)
            with open(filepath, "r", encoding="utf-8") as fh:
                original = fh.read()

            original_lines = original.splitlines(keepends=True)
            new_lines = remove_creation_workflows_section(original_lines)
            new_content = "".join(new_lines)

            if new_content != original:
                with open(filepath, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                print(f"  Updated: {filepath}")
                count += 1

    print(f"Done. Modified {count} file(s).")


if __name__ == "__main__":
    main()