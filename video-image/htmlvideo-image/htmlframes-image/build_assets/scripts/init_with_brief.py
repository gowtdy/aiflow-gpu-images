#!/usr/bin/env python3
"""
Non-interactive HyperFrames project scaffold + BRIEF.md writer.

Runs `npx hyperframes init <data-dir>/<name> --non-interactive ...`, then writes
BRIEF.md from CLI fields (no interactive brief questions), writes --topic to
capture/extracted/visible-text.txt, writes capture/extracted/tokens.json
(title=topic, description=intent, empty colors/fonts), and when --preset is set
runs `node build-frame.mjs --preset <name> --videodir <project>` (→ frame.md),
then invokes `/aiflow-build-storyboard` (→ STORYBOARD.md) and
`/aiflow-build-frame` (→ compositions/frames/*.html).

Debug / sample run (edit flags in the wrapper):

  bash build_assets/scripts/run_init_with_brief_example.sh
  bash build_assets/scripts/run_init_with_brief_example.sh --dry-run
  bash build_assets/scripts/run_init_with_brief_example.sh --data-dir /tmp/videos

Defaults:
  --data-dir /app/videos
  --example blank
  BRIEF frontmatter always: workflow=faceless-explainer, flow=automation, storyboard=yes

--aspect {1920x1080,1080x1920,1080x1080}
  BRIEF canvas ratio (exactly one of three). Maps to init --resolution:
    1920x1080  16:9  → landscape   (default destination=youtube)
    1080x1920  9:16  → portrait    (default destination=tiktok)
    1080x1080  1:1   → square      (default destination=x-feed)

--resolution {landscape,portrait,square,landscape-4k,portrait-4k,square-4k}
  Optional init override. Must match --aspect ratio when both are set:
    landscape / 1080p              ↔ 1920x1080
    portrait                       ↔ 1080x1920
    square / 1080p-square          ↔ 1080x1080
    landscape-4k / 4k / uhd        ↔ 1920x1080  (4K pixels, same ratio)
    portrait-4k                    ↔ 1080x1920
    square-4k / 4k-square          ↔ 1080x1080
  Prefer --aspect alone for normal 1080p runs.

--angle (repeatable) — narrative framing: perspective + telling structure
  Perspective: beginner, practitioner, expert, peer, skeptic, first-person, second-person
  Structure:   how-to, concept, listicle, comparison, narrative, problem-solution

--tone — narrative voice (not visual style_preset):
  humorous, warm, serious, calm-authoritative, enthusiastic, provocative, deadpan, conversational

--preset — frame preset name (presetName for build-frame.mjs) → BRIEF style_preset:

CLI --topic → BRIEF message:
CLI --tone  → BRIEF tone:
## Intent / ## Notes are auto-fused from structured fields (no --intent / --note).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants / maps
# ---------------------------------------------------------------------------

DEFAULT_DATA_DIR = "/app/videos"

ASPECT_CHOICES = ("1920x1080", "1080x1920", "1080x1080")

ASPECT_TO_RESOLUTION = {
    "1920x1080": "landscape",
    "1080x1920": "portrait",
    "1080x1080": "square",
}

ASPECT_TO_DESTINATION = {
    "1920x1080": "youtube",
    "1080x1920": "tiktok",
    "1080x1080": "x-feed",
}

DESTINATION_CHOICES = (
    "youtube",
    "website",
    "embed",
    "tiktok",
    "reels",
    "shorts",
    "x-feed",
    "linkedin",
    "instagram",
)

DESTINATION_TO_ASPECT = {
    "youtube": "1920x1080",
    "website": "1920x1080",
    "embed": "1920x1080",
    "tiktok": "1080x1920",
    "reels": "1080x1920",
    "shorts": "1080x1920",
    "x-feed": "1080x1080",
    "linkedin": "1080x1080",
    "instagram": "1080x1080",
}

# alias → canonical resolution preset
RESOLUTION_ALIASES: dict[str, str] = {
    "landscape": "landscape",
    "1080p": "landscape",
    "portrait": "portrait",
    "square": "square",
    "1080p-square": "square",
    "square-1080p": "square",
    "landscape-4k": "landscape-4k",
    "4k": "landscape-4k",
    "uhd": "landscape-4k",
    "portrait-4k": "portrait-4k",
    "square-4k": "square-4k",
    "4k-square": "square-4k",
}

RESOLUTION_TO_ASPECT = {
    "landscape": "1920x1080",
    "portrait": "1080x1920",
    "square": "1080x1080",
    "landscape-4k": "1920x1080",
    "portrait-4k": "1080x1920",
    "square-4k": "1080x1080",
}

ANGLE_LABELS = {
    "beginner": "beginner perspective",
    "practitioner": "practitioner perspective",
    "expert": "expert perspective",
    "peer": "peer-sharing perspective",
    "skeptic": "skeptic perspective",
    "first-person": "first-person lived experience",
    "second-person": "second-person immersion",
    "how-to": "step-by-step how-to",
    "concept": "concept breakdown",
    "listicle": "listicle roundup",
    "comparison": "comparison",
    "narrative": "narrative arc",
    "problem-solution": "problem → solution",
}

KNOWN_ANGLES = frozenset(ANGLE_LABELS)

TONE_LABELS = {
    "humorous": "humorous / witty",
    "warm": "warm / approachable",
    "serious": "serious / formal",
    "calm-authoritative": "calm / authoritative",
    "enthusiastic": "enthusiastic / motivating",
    "provocative": "provocative / sharp",
    "deadpan": "deadpan / restrained",
    "conversational": "conversational / casual",
}

KNOWN_TONES = frozenset(TONE_LABELS)

# frame-presets folder names (build-frame.mjs --preset / BRIEF style_preset)
KNOWN_PRESETS = frozenset(
    {
        "biennale-yellow",
        "blockframe",
        "blue-professional",
        "bold-poster",
        "broadside",
        "capsule",
        "cartesian",
        "claude",
        "cobalt-grid",
        "coral",
        "creative-mode",
        "daisy-days",
        "editorial-forest",
    }
)

ASPECT_NOTES = {
    "1920x1080": "landscape 16:9",
    "1080x1920": "portrait 9:16",
    "1080x1080": "square 1:1",
}

DESTINATION_NOTES = {
    "youtube": "YouTube publish",
    "website": "website embed publish",
    "embed": "embed-page publish",
    "tiktok": "TikTok publish",
    "reels": "Reels publish",
    "shorts": "Shorts publish",
    "x-feed": "X/Twitter feed publish",
    "linkedin": "LinkedIn publish",
    "instagram": "Instagram publish",
}

LANGUAGE_NOTES = {
    "zh": "Mandarin Chinese narration",
    "en": "English narration",
    "ja": "Japanese narration",
    "es": "Spanish narration",
}

HARDCODED_FRONTMATTER = {
    "workflow": "faceless-explainer",
    "flow": "automation",
    "storyboard": "yes",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def yaml_quote(value: str) -> str:
    """Double-quote a YAML scalar and escape \\ and \"."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def normalize_resolution(raw: str) -> str | None:
    return RESOLUTION_ALIASES.get(raw)


def warn_unknown(kind: str, value: str, known: frozenset[str]) -> None:
    if value not in known:
        print(
            f"warning: unknown {kind} {value!r}; "
            f"recommended: {', '.join(sorted(known))}",
            file=sys.stderr,
        )


def derive_canvas(
    aspect: str | None,
    destination: str | None,
    resolution_raw: str | None,
) -> tuple[str | None, str | None, str | None]:
    """
    Return (aspect, destination, resolution_canonical).
    Raises ValueError on conflicts / invalid values.
    """
    resolution: str | None = None
    if resolution_raw is not None:
        resolution = normalize_resolution(resolution_raw)
        if resolution is None:
            raise ValueError(
                f"Invalid --resolution: {resolution_raw!r}. "
                f"Use one of: {', '.join(sorted(set(RESOLUTION_ALIASES)))}"
            )

    # Fill aspect from destination or resolution when missing
    if aspect is None and destination is not None:
        aspect = DESTINATION_TO_ASPECT[destination]
    if aspect is None and resolution is not None:
        aspect = RESOLUTION_TO_ASPECT[resolution]

    # Fill destination / resolution from aspect
    if aspect is not None:
        if destination is None:
            destination = ASPECT_TO_DESTINATION[aspect]
        if resolution is None:
            resolution = ASPECT_TO_RESOLUTION[aspect]

    # Conflict: aspect vs destination
    if aspect is not None and destination is not None:
        expected_aspect = DESTINATION_TO_ASPECT[destination]
        if expected_aspect != aspect:
            raise ValueError(
                f"--aspect {aspect!r} conflicts with --destination {destination!r} "
                f"(expected aspect {expected_aspect!r})"
            )

    # Conflict: aspect vs resolution
    if aspect is not None and resolution is not None:
        expected_aspect = RESOLUTION_TO_ASPECT[resolution]
        if expected_aspect != aspect:
            raise ValueError(
                f"--aspect {aspect!r} conflicts with --resolution {resolution!r} "
                f"(compatible aspect is {expected_aspect!r})"
            )

    return aspect, destination, resolution


def build_intent(
    topic: str,
    audience: str | None,
    angles: list[str],
    tone: str | None,
    length: str | None,
    language: str | None,
    destination: str | None,
    aspect: str | None,
) -> str:
    parts: list[str] = [f"Topic: {topic}."]

    mid: list[str] = []
    if audience:
        mid.append(f"aimed at {audience}")
    if angles:
        labels = " + ".join(ANGLE_LABELS.get(a, a) for a in angles)
        mid.append(f"framed as {labels}")
    if tone:
        mid.append(f"tone leaning {TONE_LABELS.get(tone, tone)}")
    if mid:
        parts.append(" " + "; ".join(mid) + ".")

    tail: list[str] = []
    if length:
        tail.append(f"target length ~{length}")
    if language:
        tail.append(f"language {language}")
    if destination or aspect:
        dest = destination or "?"
        asp = aspect or "?"
        tail.append(f"publish to {dest} ({asp})")
    if tail:
        parts.append(" " + "; ".join(tail) + ".")

    return "".join(parts)


def build_notes(
    aspect: str | None,
    destination: str | None,
    language: str | None,
    length: str | None,
) -> list[str]:
    notes: list[str] = []
    if aspect or destination:
        bits: list[str] = []
        if aspect:
            bits.append(ASPECT_NOTES.get(aspect, aspect))
        if destination:
            bits.append(DESTINATION_NOTES.get(destination, f"{destination} publish"))
        notes.append(", ".join(bits))
    if language:
        notes.append(LANGUAGE_NOTES.get(language, f"language {language}"))
    if length:
        notes.append(f"target length {length}")
    return notes


def render_tokens(*, topic: str, intent: str) -> str:
    return (
        json.dumps(
            {
                "title": topic,
                "description": intent,
                "colors": [],
                "fonts": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def render_brief(
    *,
    topic: str,
    destination: str | None,
    aspect: str | None,
    language: str | None,
    length: str | None,
    angles: list[str],
    tone: str | None,
    audience: str | None,
    preset: str | None,
    assets: list[str],
    customizations: list[str],
) -> str:
    lines: list[str] = ["---"]
    for key, val in HARDCODED_FRONTMATTER.items():
        lines.append(f"{key}: {val}")
    lines.append(f"message: {yaml_quote(topic)}")
    if destination:
        lines.append(f"destination: {destination}")
    if aspect:
        lines.append(f"aspect: {aspect}")
    if language:
        lines.append(f"language: {language}")
    if length:
        lines.append(f"length: {length}")
    if angles:
        if len(angles) == 1:
            lines.append(f"angle: {angles[0]}")
        else:
            lines.append("angle:")
            for a in angles:
                lines.append(f"  - {a}")
    if tone:
        lines.append(f"tone: {tone}")
    if audience:
        lines.append(f"audience: {yaml_quote(audience)}")
    if preset:
        lines.append(f"style_preset: {preset}")
    lines.append("---")
    lines.append("")

    intent = build_intent(
        topic, audience, angles, tone, length, language, destination, aspect
    )
    lines.append("## Intent")
    lines.append("")
    lines.append(intent)
    lines.append("")

    if assets:
        lines.append("## Assets")
        lines.append("")
        for item in assets:
            lines.append(f"- {item}")
        lines.append("")

    if customizations:
        lines.append("## Customizations")
        lines.append("")
        for item in customizations:
            lines.append(f"- {item}")
        lines.append("")

    notes = build_notes(aspect, destination, language, length)
    if notes:
        lines.append("## Notes")
        lines.append("")
        for item in notes:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def run_init(
    project_dir: Path,
    *,
    example: str,
    resolution: str | None,
    video: str | None,
    audio: str | None,
    skip_transcribe: bool,
    whisper_model: str | None,
    whisper_language: str | None,
    tailwind: bool,
    skip_skills: bool,
) -> int:
    cmd = [
        "npx",
        "hyperframes",
        "init",
        str(project_dir),
        "--non-interactive",
        "--example",
        example,
    ]
    if resolution:
        cmd.extend(["--resolution", resolution])
    if video:
        cmd.extend(["--video", video])
    if audio:
        cmd.extend(["--audio", audio])
    if skip_transcribe:
        cmd.append("--skip-transcribe")
    if whisper_model:
        cmd.extend(["--model", whisper_model])
    if whisper_language:
        cmd.extend(["--language", whisper_language])
    if tailwind:
        cmd.append("--tailwind")

    env = os.environ.copy()
    if skip_skills:
        env["HYPERFRAMES_SKIP_SKILLS"] = "1"

    print("+", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, env=env)
    return proc.returncode


def run_build_frame(project_dir: Path, *, preset: str) -> int:
    """Run build-frame.mjs: node build-frame.mjs --preset <preset> --videodir <project>."""
    script = Path(__file__).resolve().parent / "build-frame.mjs"
    if not script.is_file():
        print(f"error: build-frame.mjs not found: {script}", file=sys.stderr)
        return 1

    cmd = [
        "node",
        str(script),
        "--preset",
        preset,
        "--videodir",
        str(project_dir),
    ]
    print("+", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd)
    return proc.returncode


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


def run_aiflow_build_storyboard(project_dir: Path) -> int:
    """Invoke Claude Code with /aiflow-build-storyboard to write STORYBOARD.md."""
    frame_path = project_dir / "frame.md"
    if not frame_path.is_file():
        print(
            f"error: frame.md missing before storyboard step: {frame_path}",
            file=sys.stderr,
        )
        return 1

    if shutil.which("claude") is None:
        print(
            "error: claude CLI not found on PATH "
            "(needed to run /aiflow-build-storyboard)",
            file=sys.stderr,
        )
        return 1

    # -p/--print: non-interactive (print + exit). bypassPermissions: no tool prompts.
    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--permission-mode",
        "bypassPermissions",
        "--output-format",
        "text",
        STORYBOARD_PROMPT,
    ]
    print(
        "+",
        "claude --print --dangerously-skip-permissions "
        "--permission-mode bypassPermissions --output-format text <prompt>",
        file=sys.stderr,
    )
    print(
        "run_aiflow_build_storyboard params:",
        {
            "cwd": str(project_dir),
            "skill": "aiflow-build-storyboard",
            "frame": str(frame_path),
        },
        flush=True,
    )
    proc = subprocess.run(cmd, cwd=str(project_dir))
    if proc.returncode != 0:
        return proc.returncode

    storyboard_path = project_dir / "STORYBOARD.md"
    if not storyboard_path.is_file():
        print(
            f"error: /aiflow-build-storyboard finished but STORYBOARD.md missing: "
            f"{storyboard_path}",
            file=sys.stderr,
        )
        return 1
    return 0


FRAME_PROMPT = """\
/aiflow-build-frame

Work in this HyperFrames project directory. hyperframes.json, frame.md, and an
outline-stage STORYBOARD.md already exist — do not re-init, do not invent a
storyboard, do not run audio, assemble index, or render.

Follow the aiflow-build-frame skill: Part 1 enrich STORYBOARD.md with time-coded
shot sequences (skip sketch; autonomous), then Part 2 dispatch per-frame workers
to write compositions/frames/*.html and mark each frame animated.

flow is automation → autonomous: proceed without waiting for sketch confirmation.
Stop when the skill gate passes (every frame status: animated).
"""


def run_aiflow_build_frame(project_dir: Path) -> int:
    """Invoke Claude Code with /aiflow-build-frame to write frame HTML."""
    frame_path = project_dir / "frame.md"
    storyboard_path = project_dir / "STORYBOARD.md"
    if not frame_path.is_file():
        print(
            f"error: frame.md missing before frame step: {frame_path}",
            file=sys.stderr,
        )
        return 1
    if not storyboard_path.is_file():
        print(
            f"error: STORYBOARD.md missing before frame step: {storyboard_path}",
            file=sys.stderr,
        )
        return 1

    if shutil.which("claude") is None:
        print(
            "error: claude CLI not found on PATH "
            "(needed to run /aiflow-build-frame)",
            file=sys.stderr,
        )
        return 1

    # -p/--print: non-interactive (print + exit). bypassPermissions: no tool prompts.
    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--permission-mode",
        "bypassPermissions",
        "--output-format",
        "text",
        FRAME_PROMPT,
    ]
    print(
        "+",
        "claude --print --dangerously-skip-permissions "
        "--permission-mode bypassPermissions --output-format text <prompt>",
        file=sys.stderr,
    )
    print(
        "run_aiflow_build_frame params:",
        {
            "cwd": str(project_dir),
            "skill": "aiflow-build-frame",
            "frame": str(frame_path),
            "storyboard": str(storyboard_path),
        },
        flush=True,
    )
    proc = subprocess.run(cmd, cwd=str(project_dir))
    if proc.returncode != 0:
        return proc.returncode

    frames_dir = project_dir / "compositions" / "frames"
    html_frames = sorted(frames_dir.glob("*.html")) if frames_dir.is_dir() else []
    if not html_frames:
        print(
            f"error: /aiflow-build-frame finished but no compositions/frames/*.html: "
            f"{frames_dir}",
            file=sys.stderr,
        )
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    epilog = """
aspect ↔ resolution ↔ destination
  1920x1080 → landscape + youtube
  1080x1920 → portrait  + tiktok
  1080x1080 → square    + x-feed

--angle (repeatable): perspective + structure
  beginner practitioner expert peer skeptic first-person second-person
  how-to concept listicle comparison narrative problem-solution

--tone: humorous warm serious calm-authoritative enthusiastic provocative deadpan conversational

--preset: frame presetName (e.g. capsule, claude) → BRIEF style_preset:

--topic maps to BRIEF message:; Intent/Notes are auto-generated.
""".strip()

    p = argparse.ArgumentParser(
        description="Non-interactive hyperframes init + BRIEF.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )

    # Init
    p.add_argument("--name", required=True, help="Project directory basename (required)")
    p.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help=f"Project data root (default: {DEFAULT_DATA_DIR})",
    )
    p.add_argument("--example", default="blank", help="Init example template (default: blank)")
    p.add_argument("--video", help="Path to a video file for init")
    p.add_argument("--audio", help="Path to an audio file for init")
    p.add_argument("--skip-transcribe", action="store_true", help="Skip whisper transcription")
    p.add_argument("--whisper-model", help="Whisper model → init --model")
    p.add_argument("--whisper-language", help="Whisper language → init --language")
    p.add_argument("--tailwind", action="store_true", help="Scaffold with Tailwind")
    p.add_argument(
        "--resolution",
        help="Optional init canvas preset (aliases ok). Usually derived from --aspect.",
    )
    p.add_argument(
        "--skip-skills",
        action="store_true",
        help="Set HYPERFRAMES_SKIP_SKILLS=1 for init",
    )

    # Brief
    p.add_argument(
        "--topic",
        required=True,
        help="Video topic / core claim → BRIEF message: (required)",
    )
    p.add_argument(
        "--aspect",
        choices=ASPECT_CHOICES,
        help="Canvas ratio: 1920x1080 | 1080x1920 | 1080x1080",
    )
    p.add_argument(
        "--destination",
        choices=DESTINATION_CHOICES,
        help="Publish destination (derived from --aspect when omitted)",
    )
    p.add_argument("--language", help="Narration/caption language for BRIEF (e.g. zh, en)")
    p.add_argument("--length", help="Target duration (e.g. 40s)")
    p.add_argument(
        "--angle",
        action="append",
        default=[],
        dest="angles",
        help="Narrative framing (repeatable): perspective and/or structure value",
    )
    p.add_argument("--tone", help="Narrative tone (e.g. humorous)")
    p.add_argument("--audience", help="Who will watch")
    p.add_argument(
        "--preset",
        help="Frame presetName for build-frame.mjs → BRIEF style_preset: (e.g. capsule)",
    )
    p.add_argument(
        "--asset",
        action="append",
        default=[],
        dest="assets",
        help="Asset line for ## Assets (repeatable)",
    )
    p.add_argument(
        "--customization",
        action="append",
        default=[],
        dest="customizations",
        help="Customization line for ## Customizations (repeatable)",
    )
    p.add_argument(
        "--brief-file",
        type=Path,
        help="If set, copy this file as BRIEF.md instead of rendering from flags",
    )
    p.add_argument("--json", action="store_true", help="Print JSON result on success")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print planned paths/BRIEF; do not init or write",
    )

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"[debug] args: {vars(args)}", file=sys.stderr)

    if args.video and args.audio:
        print("error: cannot use --video and --audio together", file=sys.stderr)
        return 2

    topic = args.topic.strip()
    if not topic:
        print("error: --topic must be non-empty", file=sys.stderr)
        return 2

    try:
        aspect, destination, resolution = derive_canvas(
            args.aspect, args.destination, args.resolution
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    angles: list[str] = list(args.angles or [])
    for a in angles:
        warn_unknown("angle", a, KNOWN_ANGLES)
    if args.tone:
        warn_unknown("tone", args.tone, KNOWN_TONES)

    preset = args.preset.strip() if args.preset else None
    if preset:
        warn_unknown("preset", preset, KNOWN_PRESETS)

    data_dir = Path(args.data_dir).expanduser().resolve()
    project_dir = data_dir / args.name
    brief_path = project_dir / "BRIEF.md"
    extracted_dir = project_dir / "capture" / "extracted"
    visible_text_path = extracted_dir / "visible-text.txt"
    tokens_path = extracted_dir / "tokens.json"
    intent = build_intent(
        topic,
        args.audience,
        angles,
        args.tone,
        args.length,
        args.language,
        destination,
        aspect,
    )

    if args.dry_run:
        brief = (
            args.brief_file.read_text(encoding="utf-8")
            if args.brief_file
            else render_brief(
                topic=topic,
                destination=destination,
                aspect=aspect,
                language=args.language,
                length=args.length,
                angles=angles,
                tone=args.tone,
                audience=args.audience,
                preset=preset,
                assets=list(args.assets or []),
                customizations=list(args.customizations or []),
            )
        )
        payload = {
            "ok": True,
            "dry_run": True,
            "project": str(project_dir),
            "brief": str(brief_path),
            "visible_text": str(visible_text_path),
            "tokens": str(tokens_path),
            "resolution": resolution,
            "destination": destination,
            "aspect": aspect,
            "preset": preset,
            "build_frame": (
                f"node build-frame.mjs --preset {preset} --videodir {project_dir}"
                if preset
                else None
            ),
            "build_storyboard": (
                "claude --print --dangerously-skip-permissions "
                "--permission-mode bypassPermissions --output-format text "
                "/aiflow-build-storyboard  # cwd=project"
                if preset
                else None
            ),
            "build_aiflow_frame": (
                "claude --print --dangerously-skip-permissions "
                "--permission-mode bypassPermissions --output-format text "
                "/aiflow-build-frame  # cwd=project"
                if preset
                else None
            ),
            "brief_preview": brief,
            "tokens_preview": json.loads(render_tokens(topic=topic, intent=intent)),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else brief)
        return 0

    # Ensure data root exists; do not pre-create project_dir (init refuses non-empty)
    data_dir.mkdir(parents=True, exist_ok=True)
    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"error: directory already exists and is not empty: {project_dir}", file=sys.stderr)
        return 1

    print(
        "run_init params:",
        {
            "project_dir": str(project_dir),
            "example": args.example,
            "resolution": resolution,
            "video": args.video,
            "audio": args.audio,
            "skip_transcribe": args.skip_transcribe,
            "whisper_model": args.whisper_model,
            "whisper_language": args.whisper_language,
            "tailwind": args.tailwind,
            "skip_skills": args.skip_skills,
        },
        flush=True,
    )
    rc = run_init(
        project_dir,
        example=args.example,
        resolution=resolution,
        video=args.video,
        audio=args.audio,
        skip_transcribe=args.skip_transcribe,
        whisper_model=args.whisper_model,
        whisper_language=args.whisper_language,
        tailwind=args.tailwind,
        skip_skills=args.skip_skills,
    )
    if rc != 0:
        print(f"error: hyperframes init failed with exit code {rc}", file=sys.stderr)
        return rc

    if not project_dir.is_dir():
        print(f"error: init did not create project directory: {project_dir}", file=sys.stderr)
        return 1

    try:
        if args.brief_file:
            if not args.brief_file.is_file():
                print(f"error: --brief-file not found: {args.brief_file}", file=sys.stderr)
                return 1
            print(
                "copy brief_file:",
                {
                    "src": str(args.brief_file),
                    "dst": str(brief_path),
                },
                flush=True,
            )
            shutil.copyfile(args.brief_file, brief_path)
        else:
            print(
                "render_brief params:",
                {
                    "topic": topic,
                    "destination": destination,
                    "aspect": aspect,
                    "language": args.language,
                    "length": args.length,
                    "angles": angles,
                    "tone": args.tone,
                    "audience": args.audience,
                    "preset": preset,
                    "assets": list(args.assets or []),
                    "customizations": list(args.customizations or []),
                },
                flush=True,
            )
            brief = render_brief(
                topic=topic,
                destination=destination,
                aspect=aspect,
                language=args.language,
                length=args.length,
                angles=angles,
                tone=args.tone,
                audience=args.audience,
                preset=preset,
                assets=list(args.assets or []),
                customizations=list(args.customizations or []),
            )
            brief_path.write_text(brief, encoding="utf-8")
    except OSError as e:
        print(f"error: failed to write BRIEF.md: {e}", file=sys.stderr)
        return 1

    try:
        print(
            "write visible-text:",
            {
                "path": str(visible_text_path),
                "topic": topic,
            },
            flush=True,
        )
        extracted_dir.mkdir(parents=True, exist_ok=True)
        visible_text_path.write_text(topic + "\n", encoding="utf-8")
    except OSError as e:
        print(f"error: failed to write visible-text.txt: {e}", file=sys.stderr)
        return 1

    try:
        tokens = render_tokens(topic=topic, intent=intent)
        print(
            "write tokens:",
            {
                "path": str(tokens_path),
                "title": topic,
                "description": intent,
            },
            flush=True,
        )
        tokens_path.write_text(tokens, encoding="utf-8")
    except OSError as e:
        print(f"error: failed to write tokens.json: {e}", file=sys.stderr)
        return 1

    if preset:
        print(
            "run_build_frame params:",
            {
                "preset": preset,
                "videodir": str(project_dir),
            },
            flush=True,
        )
        rc = run_build_frame(project_dir, preset=preset)
        if rc != 0:
            print(f"error: build-frame failed with exit code {rc}", file=sys.stderr)
            return rc

        rc = run_aiflow_build_storyboard(project_dir)
        if rc != 0:
            print(
                f"error: aiflow-build-storyboard failed with exit code {rc}",
                file=sys.stderr,
            )
            return rc

        rc = run_aiflow_build_frame(project_dir)
        if rc != 0:
            print(
                f"error: aiflow-build-frame failed with exit code {rc}",
                file=sys.stderr,
            )
            return rc

    if args.json:
        storyboard_path = project_dir / "STORYBOARD.md"
        frames_dir = project_dir / "compositions" / "frames"
        html_frames = (
            sorted(str(p) for p in frames_dir.glob("*.html"))
            if frames_dir.is_dir()
            else []
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "project": str(project_dir),
                    "brief": str(brief_path),
                    "visible_text": str(visible_text_path),
                    "tokens": str(tokens_path),
                    "preset": preset,
                    "frame": str(project_dir / "frame.md") if preset else None,
                    "storyboard": (
                        str(storyboard_path) if storyboard_path.is_file() else None
                    ),
                    "frames": html_frames if preset else None,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(project_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
