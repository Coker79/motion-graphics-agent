# make-short: animated 3D Shorts with Claude Code

> **To install:** start a new Claude Code session, drag this zip in and send "Install this skill and everything it needs." Claude follows `INSTALL.md`.

**What it makes.** Claude Code makes a 45–60 s animated YouTube Short from one idea, in one of two modes:
- **With characters:** stylized 3D toy-family characters that you design (you can be one of them: give Claude a photo), with real expressions, acting in a sunlit, painterly world.
- **Without characters:** an explainer told with objects, machines and landscape in a 3D miniature diorama, like a "How to invent X" Short. Give it a reference Short and it matches that look.

Either way it is built in **Blender with code** and rendered free on your own computer, with a camera that never sits still.

**How it works:**
- **Script.** It comes from a formula reverse-engineered from viral explainer Shorts. An independent critic and a cold listener review it once, and you approve it with both reports.
- **Higgsfield** makes the reference images (your characters' model sheets), the voice, the music and the sound effects. It never makes video: Blender renders every frame.
- **Three previews, one final.** Every shot is checked as a still. Then three 480p previews go through automatic checks (camera paths, sharpness regressions, missing frames, the voice level) and independent reviewers. The 1080p film renders once, after you approve the last preview, and you choose whether a critic reviews it.

**Credits.** The original concept and the one-step installers come from **make-short by [NoCodeHack](https://github.com/nocodehack/make-short)** (MIT). Their original README is in `README-original.md`. This edition replaces the engine with `toykit`, a Blender kit written for it.

## Install (Claude Code only)
It runs Blender, Python and ffmpeg on your own computer, so it doesn't work as a claude.ai Skills upload.
1. Download the zip.
2. Start a new Claude Code session, in the desktop app or a terminal.
3. Drag the zip in and send: **Install this skill and everything it needs.**

Claude unzips it, follows `INSTALL.md` and runs the installer for your computer, which installs the skill and every tool it needs:
- no admin password, and safe to run again;
- the first install downloads about 1–1.5 GB and takes about 10–30 minutes;
- it ends with **READY**. Then quit Claude Code, open it again and type `/make-short <your idea>`.

**Mac:** Apple Silicon (M1 or newer), macOS 14 or later. **Windows:** 10 or 11, 64-bit. To install by hand instead, see `INSTALL.md`.

To check your setup any time, run `bash ~/.claude/skills/make-short/setup/check.sh --smoke` (on Windows, in Git Bash). It builds one character and renders its turnaround.

**Optional font.** Captions use Montserrat ExtraBold, free from Google Fonts. Without it they fall back to a system font.

## Higgsfield
Add the Higgsfield connector to your Claude account. Claude asks for a credit budget once per Short and logs every call.

| Asset | Credits (approx.) |
|---|---|
| One model sheet per character (you approve the designs) | 2 each |
| Narration (one take; its pauses paced in post, never stretched) | ~7 |
| Each character's line (a second voice) | ~0.4 |
| Music bed | ~9 |
| Sound effects | ~0.5 per 2 s |
| A typical 60 s Short (3 characters, one redo) | ~35–40 |
| A Short without characters (no model sheets) | ~25–30 |

## Render time
Free, locally. On an M1 Pro, for a 50 s Short:
- **Stills:** about 1.5 s per shot.
- **Previews (480p):** 15 minutes to 2 hours each, depending on the scene, and about twice that for the last one, which renders every frame. The 61 s beehive Short's first preview, with crop fields and an elephant, took 1 h 50 min.
- **The final (1080p, rendered once):** about 1–2½ hours. The 61 s Dutch flood took 88 minutes; the 52 s pineapple pit, with volume smoke, snow and steam, took 132 minutes; the 61 s beehive Short took 140 minutes.

The renders run unattended. On Windows, times depend on your GPU.

## Rules it keeps
- Nothing is posted unless you type `go`.
- API keys never go in the chat.
- No self-scoring: independent critics score the script and the previews.
- Your characters, your story; no stock cast.
- Honest claims: you approve the script and the designs; Claude writes the shots and code; Blender renders.

## What's inside
```
make-short/
├── SKILL.md                 the steps Claude follows
├── references/              script-formula.md, toykit-api.md, lessons-v4.md, higgsfield-v4.md, windows-troubleshooting.md
├── setup/                   setup-mac.sh / setup-windows.ps1 (install everything), check.sh (health check + smoke render)
├── Install on Windows.cmd   double-click launcher
└── v4/                      the project template (copied per Short)
    ├── toykit/              look, face, char, rig, world, props, camera, film
    ├── fx.py                steam, smoke, snow and sparks
    ├── tools/               camstats, campath_scan, sharpcheck, motion_strips, gatesheet, compare, grid, sheet,
    │                        measure_script, draft_timing
    ├── specs/               example characters (keeper, recruit, cook, oldhand)
    ├── tk_turn.py           turnaround + expressions of a spec
    ├── animatic.sh          the 480p previews (on twos, or every frame with --ones)
    ├── render.sh            the one 1080p render (three Blender workers)
    ├── finish.py            captions, the mix and the loudness gates
    ├── voice/               pace.py (pause-only pacing + character lines), onsets.py
    ├── timing_dump.py       voice/timing.json for finish.py
    ├── style_target.jpg     the look every character sheet is generated against
    └── example-hardtack/    a complete 48 s Short: script, story, film.py, cues, critic briefs
```
MIT License: see `LICENSE` (original © NoCodeHack; this edition © Matt Loui). Third-party credits are in `THIRD-PARTY.md`. The changes are listed in `CHANGELOG.md`.
