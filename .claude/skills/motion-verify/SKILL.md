---
name: motion-verify
description: Deliver-and-verify toolkit for any motion-graphics output. Freeze an HTML animation at given times (?t=N seek harness), tile frames into a contact sheet, and assert an MP4's real resolution/codec/fps/duration. Use after every render or before telling the user a video is done.
---

# Motion verify

Never claim a video is done without looking at it. Scripts live in `scripts/` next to this file.

| Script | Use for | Command |
|---|---|---|
| `seek-shot.sh` | Standalone HTML/GSAP pages that support `?t=N` (page does `tl.pause(); tl.seek(t)`) | `scripts/seek-shot.sh anim.html 0 1.5 3` |
| `contact-sheet.sh` | Any frames of equal height → one image | `scripts/contact-sheet.sh sheet.png frame-*.png` |
| `probe-mp4.sh` | Final MP4 contract | `scripts/probe-mp4.sh out.mp4 1080x1920 30` |

Loop: render → freeze start/mid/end (and every key beat) → contact sheet → view it (check clipped text, off-canvas elements, safe areas, FOUC, loop seam) → fix → repeat → probe the MP4.

For Remotion use `npx remotion still <Comp> f.png --frame=N`; for Manim use `manim -s`. Then tile and probe the same way.

Needs `ffmpeg`/`ffprobe`; `seek-shot.sh` needs Playwright Chromium.
