---
name: aiflow-build-frame-visual
description: "Enrich STORYBOARD.md with time-coded shot sequences and a ## Video direction block. Use when outline STORYBOARD.md and frame.md already exist. Not HTML frames, storyboard narrative, audio, assemble index, or final render."
---

# AIFlow build frame visual

Frame visual design only: add time-coded shot sequences and video-wide direction to `STORYBOARD.md`. This skill does **not** write HTML, dispatch workers, own narrative planning, audio, assemble `index.html`, or final render. HTML composition is `/aiflow-build-frame-html`.

You are the orchestrator. Work in the HyperFrames project root. Do not put design or motion rules here beyond what this skill cites; those live in `references/` and `../hyperframes-animation/`.

---

## Prerequisites

**Must already exist:** `hyperframes.json`, `frame.md`, and an outline-stage `STORYBOARD.md` (from `/aiflow-build-storyboard`: narrative fields filled, `status: outline`).

If `STORYBOARD.md` or `frame.md` is missing → stop and report the blocker. Do not invent a storyboard, do not init a project, do not re-interrogate.

**Out of scope:** `hyperframes init`, brief writing, storyboard narrative/script planning, writing HTML, dispatching frame workers, `audio.mjs`, assemble `index.html`, transitions inject, `hyperframes lint` / `check` / `preview` / `render`.

---

## Frame Visual Design

Goal: Add the visual direction, layout intent, and motion choices to each storyboard frame.

**Skip the sketch pass.** This skill runs without collaborative layout review — do not wireframe frames, do not mark `built`, do not wait for sketch confirmation. Write the visual design below directly onto the outline frames (autonomous mode).

Edit `STORYBOARD.md` in place. Do not create another storyboard. Use `frame.md` as source of truth for color, type, layout feel, and style.

Read `references/visual-design.md`, `../hyperframes-animation/blueprints-index.md`, `references/motion-language.md`, and `../hyperframes-animation/rules-index.md`. Use `visual-design.md` for the method (the time-coded shot sequence, the inline Layout vocabulary, and the invented-visual treatment), plus the required `## Video direction` block. Use `../hyperframes-animation/blueprints-index.md` to pick each frame's shot shape. Use `motion-language.md` (the motion vocabulary + the motion doctrine) and `../hyperframes-animation/rules-index.md` (valid rule names) for motion — do not invent motion names.

For every frame, write a **time-coded shot sequence** into `STORYBOARD.md` per `visual-design.md`'s method: pick the frame's blueprint (or compose), instantiate it with THIS frame's **invented** content, and pace each Scene's reveal to the voiceover so the frame develops across its full duration instead of front-loading then freezing. Because visuals are faceless/invented, `focal`/`roles` name the **invented visual elements** (a hero word, a diagram node, a data-viz series) — you are designing them, not selecting captured assets. State layout and motion **inline** per Scene (vocabularies in `visual-design.md` and `motion-language.md`). Add one video-wide `## Video direction` block.

Do not change story, script, `transition_in`, `status`, or the source text. Do not write HTML. There is **no asset-staging step** — visuals are built by `/aiflow-build-frame-html` workers. If the user supplied a real `public/<basename>` image, reference it by path in the relevant frame's `focal`/`roles`; otherwise nothing to stage.

**Gate:** every frame has a time-coded shot sequence whose reveals are paced to the voiceover (no front-loading); each frame names its invented `focal` and/or `roles`; `## Video direction` exists. Stop when the gate passes — do not build HTML.

---

## Quick Reference

| Read | When |
| ---- | ---- |
| [`references/visual-design.md`](references/visual-design.md) | Shot sequence + Layout vocabulary |
| [`references/motion-language.md`](references/motion-language.md) | Motion vocabulary + doctrine |
| [`../hyperframes-animation/blueprints-index.md`](../hyperframes-animation/blueprints-index.md) | Pick shot shape |
| [`../hyperframes-animation/rules-index.md`](../hyperframes-animation/rules-index.md) + [`../hyperframes-animation/rules/`](../hyperframes-animation/rules/) | Valid motion names |
