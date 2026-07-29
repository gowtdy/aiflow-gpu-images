---
name: aiflow-build-frame-html
description: "Dispatch per-frame workers to write compositions/frames/*.html from a visually designed STORYBOARD.md. Use when STORYBOARD.md already has time-coded shot sequences and ## Video direction. Not visual design, storyboard narrative, audio, assemble index, or final render."
---

# AIFlow build frame HTML

Build every storyboard frame as an HTML composition. This skill does **not** own visual design (shot sequences), narrative planning, audio, assemble `index.html`, or final render. Visual design is `/aiflow-build-frame-visual`.

You are the orchestrator. Work in the HyperFrames project root. Do not put design or motion rules here beyond what workers need; those live in `sub-agents/frame-worker.md`, `references/cut-catalog.md`, and `../hyperframes-animation/`.

---

## Prerequisites

**Must already exist:**

- `hyperframes.json`, `frame.md`, and a `STORYBOARD.md` that has already passed `/aiflow-build-frame-visual`: every frame has a time-coded shot sequence with invented `focal`/`roles`, and a video-wide `## Video direction` block exists.
- `.hyperframes/frame-packets/` — already built upstream (pipeline runs `frame-packets.mjs` before this skill). One bounded packet per frame (the frame's exact storyboard block + the blueprint body + every cited rule recipe, inlined) and `_role.md` (`../hyperframes-core/references/frame-worker-core.md` + this skill's `sub-agents/frame-worker.md`, concatenated verbatim — the complete worker role).

If `STORYBOARD.md` or `frame.md` is missing, or visual design is incomplete (no `## Video direction`, missing shot sequences) → stop and report the blocker. Do **not** invent or fill in visual design yourself — that belongs to `/aiflow-build-frame-visual`.

If `.hyperframes/frame-packets/` or `_role.md` is missing, or a storyboard frame has no matching packet → stop and report the blocker. Do **not** run `frame-packets.mjs` in this skill.

**Out of scope:** `hyperframes init`, brief writing, storyboard narrative/script planning, writing shot sequences / `## Video direction`, `frame-packets.mjs`, `audio.mjs`, assemble `index.html`, transitions inject, `hyperframes lint` / `check` / `preview` / `render`. Verification (transitions + lint/check + snapshot) is `/aiflow-verify-frame`.

---

## Build Frames

Goal: Build every storyboard frame as an HTML composition and assemble the playable video.

Before dispatch, read `../hyperframes-core/references/subagent-dispatch.md`. Consume the pre-built packets under `.hyperframes/frame-packets/` — do not rebuild them. Dispatch one sub-agent per frame, in parallel if possible; otherwise run workers in waves. Each worker gets exactly one frame: its prompt carries `_role.md` and that frame's packet — paste both in full, or hand the two file paths for the worker to read first (equivalent; the worker starts from exactly those two documents either way) — plus a dispatch context with `PROJECT_DIR`, `frame_id`, whether the frame has a **confirmed sketch** on disk (the worker dresses that layout rather than redrawing it — frame-worker core § When a confirmed sketch exists), canvas size, and caption status + keep-out band if captions are enabled.

Workers read only their packet and `frame.md`; they never open `STORYBOARD.md` or the skill documents (the packet inlines what was selected upstream). Each worker writes only `compositions/frames/NN-*.html`. Workers must never edit `STORYBOARD.md`.

**Full-bleed backgrounds ride on a `class="clip"` layer, never the `#root`.** A frame's ground (color field / gradient / grid) is **one** full-duration background clip on the lowest content track — a `background` set on the `#root` / `data-composition-id` element is clip-gated to the frame's window and is not a dependable ground, so dark content can land on the black host `body` and render invisible. Other full-duration ambience nests inside that clip or uses higher tracks (never N sibling clips overlapping on the same `data-track-index`). The video's base ground is painted by the assembler from `frame.md`'s `canvas` color onto the index `#root`. (Full rule + self-check: `../hyperframes-core/references/frame-worker-core.md`.)

As each worker returns, the orchestrator marks that frame as `animated` in `STORYBOARD.md`.

Assemble the index:
`node /app/scripts/assemble-index.mjs --videodir ${videodir}`

If a command fails, surface stderr and stop — don't pile on recovery commands. Fix it yourself: the cheapest safe edit to `compositions/frames/NN-*.html`, then rerun the failed check.

**Gate:** every frame is marked `animated`, `index.html` exists.

---

## Quick Reference

| Read | When |
| ---- | ---- |
| [`references/cut-catalog.md`](references/cut-catalog.md) | Within-frame seams (worker) |
| [`../hyperframes-animation/rules-index.md`](../hyperframes-animation/rules-index.md) + [`../hyperframes-animation/rules/`](../hyperframes-animation/rules/) | Motion recipes for workers |
| [`sub-agents/frame-worker.md`](sub-agents/frame-worker.md) | Per-frame workers |
| [`../hyperframes-core/references/subagent-dispatch.md`](../hyperframes-core/references/subagent-dispatch.md) | Safe sub-agent dispatch |
