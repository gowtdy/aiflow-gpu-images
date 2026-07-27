#!/usr/bin/env python3
"""
Run one AIFlow Claude skill on an existing HyperFrames project.

Prerequisite: project already has BRIEF.md + frame.md (from init_with_brief.py).

Skills (call separately — shell orchestrates order / inserts steps between):
  --skill storyboard  → /aiflow-build-storyboard  → STORYBOARD.md
  --skill visual      → /aiflow-build-frame-visual → shot sequences + ## Video direction
  --skill html        → /aiflow-build-frame-html   → compositions/frames/*.html

Usage:
  python3 build_assets/scripts/run_aiflow_build_skills.py --videodir /app/videos/my-video --skill storyboard
  python3 build_assets/scripts/run_aiflow_build_skills.py --videodir /app/videos/my-video --skill visual
  python3 build_assets/scripts/run_aiflow_build_skills.py --videodir /app/videos/my-video --skill html
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Iterator


STORYBOARD_PROMPT = """\
/aiflow-build-storyboard

Work in this HyperFrames project directory. BRIEF.md, frame.md, and
capture/extracted/visible-text.txt already exist — do not re-init, do not run
build-frame, audio, or render.

Follow the aiflow-build-storyboard skill: read BRIEF.md (message + intent),
visible-text.txt, and frame.md; write STORYBOARD.md (outline frames with
required narrative fields) and SCRIPT.md when narration is needed.

flow is automation → autonomous: post a short frame-sequence summary as a
heads-up and proceed without waiting for approval. Stop when the skill gate
passes (STORYBOARD.md exists; SCRIPT.md when narration is needed).
"""

FRAME_VISUAL_PROMPT = """\
/aiflow-build-frame-visual

Work in this HyperFrames project directory. hyperframes.json, frame.md, and an
outline-stage STORYBOARD.md already exist — do not re-init, do not invent a
storyboard, do not write HTML, do not run audio, assemble index, or render.

Follow the aiflow-build-frame-visual skill: enrich STORYBOARD.md with time-coded
shot sequences and a ## Video direction block (skip sketch; autonomous). Do not
mark frames animated; do not write compositions/frames/*.html.

flow is automation → autonomous: proceed without waiting for sketch confirmation.
Stop when the skill gate passes (shot sequences + ## Video direction).
"""

FRAME_HTML_PROMPT = """\
/aiflow-build-frame-html

Work in this HyperFrames project directory. hyperframes.json, frame.md, and a
visually designed STORYBOARD.md (shot sequences + ## Video direction) already
exist — do not re-init, do not invent visual design, do not run audio, assemble
index, or render.

Follow the aiflow-build-frame-html skill: dispatch per-frame workers to write
compositions/frames/*.html and mark each frame animated. Sketches were skipped
upstream — none on disk.

flow is automation → autonomous: proceed without waiting for confirmation.
Stop when the skill gate passes (every frame status: animated).
"""


def log_progress(msg: str) -> None:
    print(f"[aiflow-skills] {msg}", flush=True)


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{int(m)}m{s:04.1f}s"
    h, m = divmod(int(m), 60)
    return f"{h}h{m:02d}m{s:04.1f}s"


@contextmanager
def step_progress(
    index: int,
    total: int,
    name: str,
    timings: list[dict[str, object]] | None = None,
) -> Iterator[list[bool]]:
    log_progress(f"[{index}/{total}] START  {name}")
    t0 = time.monotonic()
    ok: list[bool] = [False]
    try:
        yield ok
    finally:
        elapsed = time.monotonic() - t0
        status = "DONE " if ok[0] else "FAIL "
        log_progress(
            f"[{index}/{total}] {status} {name} ({format_duration(elapsed)})"
        )
        if timings is not None:
            timings.append(
                {
                    "index": index,
                    "total": total,
                    "name": name,
                    "seconds": round(elapsed, 3),
                    "ok": ok[0],
                }
            )


class StepTracker:
    def __init__(
        self,
        names: list[str],
        timings: list[dict[str, object]] | None = None,
    ) -> None:
        self.names = names
        self.total = len(names)
        self.timings = timings
        self._i = 0

    def next(self) -> AbstractContextManager[list[bool]]:
        if self._i >= self.total:
            raise RuntimeError(
                f"step overflow: plan has {self.total} steps, "
                f"but next() called for step {self._i + 1}"
            )
        name = self.names[self._i]
        self._i += 1
        return step_progress(self._i, self.total, name, self.timings)

    def check_complete(self) -> None:
        if self._i != self.total:
            print(
                f"warning: planned {self.total} steps but ran {self._i}",
                file=sys.stderr,
            )


def require_claude() -> int | None:
    if shutil.which("claude") is None:
        print(
            "error: claude CLI not found on PATH "
            "(needed to run aiflow build skills)",
            file=sys.stderr,
        )
        return 1
    return None


def run_claude(project_dir: Path, prompt: str) -> int:
    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--permission-mode",
        "bypassPermissions",
        "--output-format",
        "text",
        prompt,
    ]
    print(
        "+",
        "claude --print --dangerously-skip-permissions "
        "--permission-mode bypassPermissions --output-format text <prompt>",
        file=sys.stderr,
    )
    proc = subprocess.run(cmd, cwd=str(project_dir))
    return proc.returncode


def run_aiflow_build_storyboard(project_dir: Path) -> int:
    """Invoke Claude Code with /aiflow-build-storyboard to write STORYBOARD.md."""
    frame_path = project_dir / "frame.md"
    if not frame_path.is_file():
        print(
            f"error: frame.md missing before storyboard step: {frame_path}",
            file=sys.stderr,
        )
        return 1

    err = require_claude()
    if err is not None:
        return err

    print(
        "run_aiflow_build_storyboard params:",
        {
            "cwd": str(project_dir),
            "skill": "aiflow-build-storyboard",
            "frame": str(frame_path),
        },
        flush=True,
    )
    rc = run_claude(project_dir, STORYBOARD_PROMPT)
    if rc != 0:
        return rc

    storyboard_path = project_dir / "STORYBOARD.md"
    if not storyboard_path.is_file():
        print(
            f"error: /aiflow-build-storyboard finished but STORYBOARD.md missing: "
            f"{storyboard_path}",
            file=sys.stderr,
        )
        return 1
    return 0


def run_aiflow_build_frame_visual(project_dir: Path) -> int:
    """Invoke Claude Code with /aiflow-build-frame-visual to enrich STORYBOARD.md."""
    frame_path = project_dir / "frame.md"
    storyboard_path = project_dir / "STORYBOARD.md"
    if not frame_path.is_file():
        print(
            f"error: frame.md missing before frame-visual step: {frame_path}",
            file=sys.stderr,
        )
        return 1
    if not storyboard_path.is_file():
        print(
            f"error: STORYBOARD.md missing before frame-visual step: {storyboard_path}",
            file=sys.stderr,
        )
        return 1

    err = require_claude()
    if err is not None:
        return err

    print(
        "run_aiflow_build_frame_visual params:",
        {
            "cwd": str(project_dir),
            "skill": "aiflow-build-frame-visual",
            "frame": str(frame_path),
            "storyboard": str(storyboard_path),
        },
        flush=True,
    )
    rc = run_claude(project_dir, FRAME_VISUAL_PROMPT)
    if rc != 0:
        return rc

    storyboard_text = storyboard_path.read_text(encoding="utf-8")
    if "## Video direction" not in storyboard_text:
        print(
            "error: /aiflow-build-frame-visual finished but STORYBOARD.md "
            "missing ## Video direction: "
            f"{storyboard_path}",
            file=sys.stderr,
        )
        return 1
    return 0


def run_aiflow_build_frame_html(project_dir: Path) -> int:
    """Invoke Claude Code with /aiflow-build-frame-html to write frame HTML."""
    frame_path = project_dir / "frame.md"
    storyboard_path = project_dir / "STORYBOARD.md"
    if not frame_path.is_file():
        print(
            f"error: frame.md missing before frame-html step: {frame_path}",
            file=sys.stderr,
        )
        return 1
    if not storyboard_path.is_file():
        print(
            f"error: STORYBOARD.md missing before frame-html step: {storyboard_path}",
            file=sys.stderr,
        )
        return 1

    storyboard_text = storyboard_path.read_text(encoding="utf-8")
    if "## Video direction" not in storyboard_text:
        print(
            "error: STORYBOARD.md missing ## Video direction before frame-html "
            f"(needed from /aiflow-build-frame-visual): {storyboard_path}",
            file=sys.stderr,
        )
        return 1

    err = require_claude()
    if err is not None:
        return err

    print(
        "run_aiflow_build_frame_html params:",
        {
            "cwd": str(project_dir),
            "skill": "aiflow-build-frame-html",
            "frame": str(frame_path),
            "storyboard": str(storyboard_path),
        },
        flush=True,
    )
    rc = run_claude(project_dir, FRAME_HTML_PROMPT)
    if rc != 0:
        return rc

    frames_dir = project_dir / "compositions" / "frames"
    html_frames = sorted(frames_dir.glob("*.html")) if frames_dir.is_dir() else []
    if not html_frames:
        print(
            f"error: /aiflow-build-frame-html finished but no compositions/frames/*.html: "
            f"{frames_dir}",
            file=sys.stderr,
        )
        return 1
    return 0


SKILL_CHOICES = ("storyboard", "visual", "html")

SKILL_STEP_NAME = {
    "storyboard": "aiflow-build-storyboard → STORYBOARD.md",
    "visual": "aiflow-build-frame-visual → shot sequences",
    "html": "aiflow-build-frame-html → compositions/frames",
}

SKILL_RUNNERS = {
    "storyboard": run_aiflow_build_storyboard,
    "visual": run_aiflow_build_frame_visual,
    "html": run_aiflow_build_frame_html,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run one aiflow Claude skill on an existing project "
            "(must already have frame.md). Call once per skill."
        )
    )
    p.add_argument(
        "--videodir",
        required=True,
        type=Path,
        help="HyperFrames project directory (must contain frame.md)",
    )
    p.add_argument(
        "--skill",
        required=True,
        choices=SKILL_CHOICES,
        help="Which skill to run: storyboard | visual | html",
    )
    p.add_argument("--json", action="store_true", help="Print JSON result on success")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_dir = args.videodir.expanduser().resolve()
    if not project_dir.is_dir():
        print(f"error: --videodir is not a directory: {project_dir}", file=sys.stderr)
        return 1

    skill = args.skill
    step_name = SKILL_STEP_NAME[skill]
    runner = SKILL_RUNNERS[skill]
    timings: list[dict[str, object]] = []
    steps = StepTracker([step_name], timings)
    pipeline_t0 = time.monotonic()
    pipeline_ok = False
    log_progress(
        f"skill START  skill={skill} project={project_dir}"
    )

    try:
        with steps.next() as ok:
            rc = runner(project_dir)
            if rc != 0:
                print(
                    f"error: aiflow-build-{skill} failed with exit code {rc}",
                    file=sys.stderr,
                )
                return rc
            ok[0] = True
        steps.check_complete()
        pipeline_ok = True
    finally:
        total_seconds = time.monotonic() - pipeline_t0
        status = "DONE" if pipeline_ok else "FAIL"
        log_progress(
            f"skill {status}  skill={skill} total={format_duration(total_seconds)}"
        )

    if not pipeline_ok:
        return 1

    storyboard_path = project_dir / "STORYBOARD.md"
    frames_dir = project_dir / "compositions" / "frames"
    html_frames = (
        sorted(str(p) for p in frames_dir.glob("*.html")) if frames_dir.is_dir() else []
    )

    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "skill": skill,
                    "project": str(project_dir),
                    "storyboard": (
                        str(storyboard_path) if storyboard_path.is_file() else None
                    ),
                    "frames": html_frames if skill == "html" else None,
                    "timings": {
                        "steps": timings,
                        "total_seconds": round(total_seconds, 3),
                    },
                },
                ensure_ascii=False,
            )
        )
    else:
        print(project_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
