---
name: aiflow-build-frame
description: "Enrich STORYBOARD.md with time-coded shot sequences, then dispatch per-frame workers to write compositions/frames/*.html. Use when outline STORYBOARD.md and frame.md already exist. Not storyboard narrative, audio, assemble index, or final render."
---

# AIFlow build frame

Two parts in one run: **Part 1** frame visual design (time-coded shot sequences), then **Part 2** build each frame as HTML. This skill does **not** own narrative planning, audio, assemble `index.html`, or final render.

You are the orchestrator. Work in the HyperFrames project root. Run Part 1, pass its gate, then Part 2. Do not put design or motion rules here beyond what Part 1 cites; those live in `references/`, `sub-agents/frame-worker.md`, and `../hyperframes-animation/`.

---

## Prerequisites

**Must already exist:** `hyperframes.json`, `frame.md`, and an outline-stage `STORYBOARD.md` (from `/aiflow-build-storyboard`: narrative fields filled, `status: outline`).

If `STORYBOARD.md` or `frame.md` is missing → stop and report the blocker. Do not invent a storyboard, do not init a project, do not re-interrogate.

**Out of scope:** `hyperframes init`, brief writing, storyboard narrative/script planning, `audio.mjs`, assemble `index.html`, transitions inject, `hyperframes lint` / `check` / `preview` / `render`.

---

## Part 1: Frame Visual Design

Goal: Add the visual direction, layout intent, and motion choices to each storyboard frame.

**Skip the sketch pass.** This skill runs without collaborative layout review — do not wireframe frames, do not mark `built`, do not wait for sketch confirmation. Write the visual design below directly onto the outline frames (autonomous mode).

Edit `STORYBOARD.md` in place. Do not create another storyboard. Use `frame.md` as source of truth for color, type, layout feel, and style.

Read `references/visual-design.md`, `../hyperframes-animation/blueprints-index.md`, `references/motion-language.md`, and `../hyperframes-animation/rules-index.md`. Use `visual-design.md` for the method (the time-coded shot sequence, the inline Layout vocabulary, and the invented-visual treatment), plus the required `## Video direction` block. Use `../hyperframes-animation/blueprints-index.md` to pick each frame's shot shape. Use `motion-language.md` (the motion vocabulary + the motion doctrine) and `../hyperframes-animation/rules-index.md` (valid rule names) for motion — do not invent motion names.

For every frame, write a **time-coded shot sequence** into `STORYBOARD.md` per `visual-design.md`'s method: pick the frame's blueprint (or compose), instantiate it with THIS frame's **invented** content, and pace each Scene's reveal to the voiceover so the frame develops across its full duration instead of front-loading then freezing. Because visuals are faceless/invented, `focal`/`roles` name the **invented visual elements** (a hero word, a diagram node, a data-viz series) — you are designing them, not selecting captured assets. State layout and motion **inline** per Scene (vocabularies in `visual-design.md` and `motion-language.md`). Add one video-wide `## Video direction` block.

Do not change story, script, `transition_in`, or the source text. Do not write HTML in this part. There is **no asset-staging step** — visuals are built by the workers in Part 2. If the user supplied a real `public/<basename>` image, reference it by path in the relevant frame's `focal`/`roles`; otherwise nothing to stage.

**Gate:** every frame has a time-coded shot sequence whose reveals are paced to the voiceover (no front-loading); each frame names its invented `focal` and/or `roles`; `## Video direction` exists. Only then continue to Part 2.

---

## Part 2: Build Frames

Goal: Build every storyboard frame as an HTML composition.

Before dispatch, read `sub-agents/frame-worker.md` and `../hyperframes-core/references/subagent-dispatch.md`. Dispatch one sub-agent per frame, in parallel if possible; otherwise run workers in waves. Each worker gets exactly one frame.

Each worker context must include `PROJECT_DIR`, `frame_id`, whether the frame has a **confirmed sketch** on disk (for this skill: none — sketches were skipped), canvas size, caption status and keep-out band if captions are enabled, and `RULES_DIR` as the absolute path to this skill's `../hyperframes-animation/rules/`. Each worker reads `frame.md`, its own `## Frame N` block from `STORYBOARD.md`, the local rule recipe (`../hyperframes-animation/rules/<id>.md`) for each cited motion, and the frame's blueprint template (`../hyperframes-animation/blueprints/<id>.md`). Each worker writes only `compositions/frames/NN-*.html`. Workers must never edit `STORYBOARD.md`.

**Full-bleed backgrounds ride on a `class="clip"` layer, never the `#root`.** A frame's ground (color field / gradient / grid) is its own full-duration background clip — a `background` set on the `#root` / `data-composition-id` element is clip-gated to the frame's window and is not a dependable ground, so dark content can land on the black host `body` and render invisible. The video's base ground is painted later by the assembler from `frame.md`'s `canvas` color onto the index `#root`. (Full rule + self-check: `sub-agents/frame-worker.md`.)

As each worker returns, the orchestrator marks that frame as `animated` in `STORYBOARD.md`.

Do **not** assemble `index.html` in this skill.

**Gate:** every frame is marked `animated`.

---

## Quick Reference

| Read | When |
| ---- | ---- |
| [`references/visual-design.md`](references/visual-design.md) | Part 1: shot sequence + Layout vocabulary |
| [`references/motion-language.md`](references/motion-language.md) | Part 1: motion vocabulary + doctrine |
| [`references/cut-catalog.md`](references/cut-catalog.md) | Part 2: within-frame seams (worker) |
| [`../hyperframes-animation/blueprints-index.md`](../hyperframes-animation/blueprints-index.md) | Part 1: pick shot shape |
| [`../hyperframes-animation/rules-index.md`](../hyperframes-animation/rules-index.md) + [`../hyperframes-animation/rules/`](../hyperframes-animation/rules/) | Part 1–2: valid motion names + recipes |
| [`sub-agents/frame-worker.md`](sub-agents/frame-worker.md) | Part 2: per-frame workers |
| [`../hyperframes-core/references/subagent-dispatch.md`](../hyperframes-core/references/subagent-dispatch.md) | Part 2: safe sub-agent dispatch |
