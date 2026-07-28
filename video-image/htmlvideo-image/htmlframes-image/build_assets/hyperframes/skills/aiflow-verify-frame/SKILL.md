---
name: aiflow-verify-frame
description: "Verify the assembled video: inject transitions, run hyperframes lint/check, snapshot frame midpoints, glance at the contact sheet. Use when index.html and compositions/frames/*.html already exist. Not storyboard, visual design, HTML build, assemble, or final render."
---

# AIFlow verify frame

Verify the assembled video. This skill does **not** own storyboard, visual design, HTML frame builds, assemble `index.html`, or final render. HTML build is `/aiflow-build-frame-html`.

You are the orchestrator. Work in the HyperFrames project root.

---

## Prerequisites

**Must already exist:** `hyperframes.json`, `index.html`, `STORYBOARD.md`, and `compositions/frames/*.html` (from `/aiflow-build-frame-html` + assemble).

If any of these are missing → stop and report the blocker. Do **not** assemble the index yourself, do not invent a storyboard, do not re-init.

**Out of scope:** `hyperframes init`, brief writing, storyboard narrative/script planning, writing shot sequences / `## Video direction`, writing HTML frames, `frame-packets.mjs`, `audio.mjs`, assemble `index.html`, `hyperframes preview` / `render`.

---

## Verify

Goal: Verify the assembled video — inject transitions, pass lint/check, snapshot frame midpoints, glance at the contact sheet.

```bash
node /app/scripts/transitions.mjs inject --videodir ${videodir}
node /app/scripts/transitions.mjs verify --videodir ${videodir}
npx hyperframes lint ${videodir}
npx hyperframes check ${videodir}
AT="$(node /app/scripts/frame-midpoints.mjs --videodir ${videodir})"
npx hyperframes snapshot ${videodir} --at "${AT}"
```

`snapshot` stitches the captured frames into one contact sheet (`snapshots/contact-sheet.jpg`). Glance at it; if nothing is obviously broken, move on — don't linger here.

If a command fails (`transitions inject` / `transitions verify` / `lint` / `check` / `frame-midpoints` / `snapshot`), surface stderr and stop — don't pile on recovery commands. Fix it yourself: the cheapest safe edit to `compositions/frames/NN-*.html`, then rerun the failed check. This applies to every step in this skill, not only snapshot.

**Known false-positive — do not chase it.** `check` may report a handful of `text_box_overflow` findings of ~1–4px on the **caption** highlight words (selector `#caption-word-*` / `.caption-line`). The caption pill uses a deliberately snug `line-height` (set once in `scripts/captions.mjs`) and has **no `overflow:hidden`**, so a heavy display glyph's ink spills a few px into the pill's own padding — nothing is actually clipped. Treat these as expected and proceed. Do **not** inflate the caption `line-height` (it balloons the pill, which is worse). Only act on a `text_box_overflow` when it names a **frame** element (`#el-NN-*`), not a caption word.

**Gate:** `lint` and `check` passed and the snapshots were inspected before render. Stop when the gate passes — do not render.

---

## Quick Reference

| Read | When |
| ---- | ---- |
| [`../hyperframes-cli/SKILL.md`](../hyperframes-cli/SKILL.md) | `lint` / `check` / `snapshot` CLI |
| [`../hyperframes-core/references/production-loop.md`](../hyperframes-core/references/production-loop.md) | Verify stage in the production loop |
