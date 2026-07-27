---
name: aiflow-build-frame-html
description: "Dispatch per-frame workers to write compositions/frames/*.html from a visually designed STORYBOARD.md. Use when STORYBOARD.md already has time-coded shot sequences and ## Video direction. Not visual design, storyboard narrative, audio, assemble index, or final render."
---

# AIFlow build frame HTML

Build every storyboard frame as an HTML composition. This skill does **not** own visual design (shot sequences), narrative planning, audio, assemble `index.html`, or final render. Visual design is `/aiflow-build-frame-visual`.

You are the orchestrator. Work in the HyperFrames project root. Do not put design or motion rules here beyond what workers need; those live in `sub-agents/frame-worker.md`, `references/cut-catalog.md`, and `../hyperframes-animation/`.

---

## Prerequisites

**Must already exist:** `hyperframes.json`, `frame.md`, and a `STORYBOARD.md` that has already passed `/aiflow-build-frame-visual`: every frame has a time-coded shot sequence with invented `focal`/`roles`, and a video-wide `## Video direction` block exists.

If `STORYBOARD.md` or `frame.md` is missing, or visual design is incomplete (no `## Video direction`, missing shot sequences) → stop and report the blocker. Do **not** invent or fill in visual design yourself — that belongs to `/aiflow-build-frame-visual`.

**Out of scope:** `hyperframes init`, brief writing, storyboard narrative/script planning, writing shot sequences / `## Video direction`, `audio.mjs`, assemble `index.html`, transitions inject, `hyperframes lint` / `check` / `preview` / `render`.

---

## Build Frames

Goal: Build every storyboard frame as an HTML composition.

Before dispatch, read `sub-agents/frame-worker.md` and `../hyperframes-core/references/subagent-dispatch.md`. Dispatch one sub-agent per frame, in parallel if possible; otherwise run workers in waves. Each worker gets exactly one frame.

Each worker context must include `PROJECT_DIR`, `frame_id`, whether the frame has a **confirmed sketch** on disk (for this skill: none — sketches were skipped upstream), canvas size, caption status and keep-out band if captions are enabled, and `RULES_DIR` as the absolute path to this skill's `../hyperframes-animation/rules/`. Each worker reads `frame.md`, its own `## Frame N` block from `STORYBOARD.md`, the local rule recipe (`../hyperframes-animation/rules/<id>.md`) for each cited motion, and the frame's blueprint template (`../hyperframes-animation/blueprints/<id>.md`). Each worker writes only `compositions/frames/NN-*.html`. Workers must never edit `STORYBOARD.md`.

**Full-bleed backgrounds ride on a `class="clip"` layer, never the `#root`.** A frame's ground (color field / gradient / grid) is its own full-duration background clip — a `background` set on the `#root` / `data-composition-id` element is clip-gated to the frame's window and is not a dependable ground, so dark content can land on the black host `body` and render invisible. The video's base ground is painted later by the assembler from `frame.md`'s `canvas` color onto the index `#root`. (Full rule + self-check: `sub-agents/frame-worker.md`.)

As each worker returns, the orchestrator marks that frame as `animated` in `STORYBOARD.md`.

Do **not** assemble `index.html` in this skill.

**Gate:** every frame is marked `animated`.

---

## Quick Reference

| Read | When |
| ---- | ---- |
| [`references/cut-catalog.md`](references/cut-catalog.md) | Within-frame seams (worker) |
| [`../hyperframes-animation/rules-index.md`](../hyperframes-animation/rules-index.md) + [`../hyperframes-animation/rules/`](../hyperframes-animation/rules/) | Motion recipes for workers |
| [`sub-agents/frame-worker.md`](sub-agents/frame-worker.md) | Per-frame workers |
| [`../hyperframes-core/references/subagent-dispatch.md`](../hyperframes-core/references/subagent-dispatch.md) | Safe sub-agent dispatch |
