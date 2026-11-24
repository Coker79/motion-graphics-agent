# Motion graphics agent (merged skills)

Merged from:
- **mattypark/Motion-graphics-skill** → `motion-video-director` (full production playbook: brief → ElevenLabs VO → storyboard → preview loop → render, 2D/3D, editing, QA). Sound & QA sections patched to hand off to the skills below. *No license file in the source repo — personal use only unless the author confirms.*
- **Barty-Bart/motion-graphics** (MIT) → `explainer-high-energy`, `explainer-default`, `explainer-engaging`, `motion-broll`, `object-separation`, `sound-effects` (with bundled CC0 SFX library).
- **iart-ai/motion-skills** (MIT) → `motion-verify` scripts (seek-shot, contact-sheet, probe-mp4). The rest of that repo is an index linking to 19 separate packs — install any with `npx skills add iart-ai/<pack>`.
- New: `motion-graphics` router skill that picks the right specialist.

Install globally: `cp -r .claude/skills/* ~/.claude/skills/`
