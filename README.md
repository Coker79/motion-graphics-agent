# Motion graphics agent (merged skills)

Merged from:
- **mattypark/Motion-graphics-skill** → `motion-video-director` (full production playbook: brief → ElevenLabs VO → storyboard → preview loop → render, 2D/3D, editing, QA). Sound & QA sections patched to hand off to the skills below. *No license file in the source repo — personal use only unless the author confirms.*
- **Barty-Bart/motion-graphics** (MIT) → `explainer-high-energy`, `explainer-default`, `explainer-engaging`, `motion-broll`, `object-separation`, `sound-effects` (with bundled CC0 SFX library).
- **iart-ai/motion-skills** (MIT) → `motion-verify` scripts (seek-shot, contact-sheet, probe-mp4). The rest of that repo is an index linking to 19 separate packs — install any with `npx skills add iart-ai/<pack>`.
- **iart-ai/map-animation-skills** (MIT) → `map-animation` (Vox-style maps: pins, routes, highlights).
- **kaomei/stickman-video-director** (MIT) → `directing-stickman-videos`, linked as a git submodule (`vendor/`, ~900 MB of reference media). Clone with `git clone --recursive`, or run `git submodule update --init` after pulling.
- **make-short v2.3.0** (user-supplied zip) → `make-short`: Blender EEVEE 3D toy-family / diorama Shorts. Requires Blender (Mac/Windows installer in `.claude/skills/make-short/setup/`).
- New: `motion-graphics` router skill that picks the right specialist.

Install globally: `git submodule update --init && cp -rL .claude/skills/* ~/.claude/skills/`
