# Changelog

## 2.3.0 (2026-11-24): release, with the beehive Short's fixes
The beehive Short (the fourth test Short, with the user built as the farmer from a photo) ran on 2.3.0-rc1. Its kit changes and lessons are now in the skill.
- **New character parts** (spec-gated, so existing specs render as before):
  - `hair: crop` (short hair with a quiff) and `glasses` (thin wire rims): build the user from a photo (SKILL §2);
  - `bandana`, a plaid `sash` and `lower` (two-tone trousers) for the wardrobe.
  - The rig carries the glasses and hair on the head, and the bandana and sash on the chest.
- **Fixes:**
  - `CamPath.orbit` keys every frame; every-other-frame keys stuttered mid-arc (lesson 85);
  - `rig._parent_to_bone` updates the view layer first, so a prop parented right after it is placed no longer lands at the origin (lesson 89).
- **Honest render times:** SKILL and README now quote previews at 15 min to 2 h, measured first with a 3-frame test, and P1/P2 render with `TK_MB_STEPS=2` (lesson 86). Finals run 1-2½ h.
- **Shorts framing:** shots step one size wider for the button stack, and big moves stay slow (lessons 87-88).
- Lessons 85-92.
- Tested: the parenting fix (the rc2 code put a fresh prop 832 mm off; 2.3.0 keeps it exactly), orbit keys (41 keys over 40 frames), the new parts on a turnaround and 12 rigged poses, and the full install from the zip.

## 2.3.0-rc2 (2026-11-20): install by asking Claude Code
A viewer downloads the zip, drags it into a new Claude Code session and sends "Install this skill and everything it needs."
- **`INSTALL.md` opens with that flow**, then gives Claude its own steps: unzip, read the installer, run it in the background with `--smoke`, check for READY, then tell the user to restart Claude Code and add the Higgsfield connector. The README and SKILL.md point there.
- **The installers never wait for input:**
  - `hdiutil` reads no keyboard;
  - when Claude Code runs them, downloads print one plain line each (name, size, checksum OK) instead of a progress bar, and the Whisper model download prints no bar at all.
- **`setup-mac.sh --smoke` and `setup-windows.ps1 -Smoke`** end with a real Blender render, so one command proves the whole kit works.
- SKILL §0 gives Claude a Windows install command it can run itself.
- The Windows troubleshooting page covers Claude Code using PowerShell when Git isn't installed, and Claude Code running inside WSL.
- All 10 pinned download links answered with HTTP 200 on 2026-11-20.

## 2.3.0-rc1 (2026-11-20): make the first version as good as possible
The pineapple pit took 19 h 42 min of wall clock, and only 2 h 12 min of that was the one 1080p render. The rest was loops: about 4 h of script rewrites chasing a listener score, about 3½ h of approval messages waiting between sessions overnight, and eight preview cuts (two thrown away unreviewed, three chasing bugs). The goal is now the best possible first version, with every round planned up front (lesson 84).
- **Script (§1.6):** one critic and one cold listener in parallel, ONE rewrite, then the user with both reports. No loop on the listener's score.
- **Previews (§6): exactly three, planned up front.**
  - P1 (twos): the automatic checks, then the motion review and the whole-film critic in parallel, and one fix round.
  - P2 (`--only`): the automatic checks and a re-review of the changed lines, then the user (GATE 4) with the reviewers' open list.
  - P3 (new `animatic.sh --ones`): 480p with every frame rendered and the final's motion, so the faults twos hide show up (lessons 65–71). It gets the critic's last look, plus about 10 1080p stills for fine detail.
  - Never start the next preview before the last one's reviews are in. Make a fourth only for a regression or the user's request.
  - The automatic checks run on every preview: camstats, campath_scan, sharpcheck against the previous preview, and one still per changed effect.
- **After the 1080p (§7):** only the automatic checks (missing frames, sharpcheck against P3, the mix gate). Then the user chooses: ship as is, critic review only, or critic + one fix pass. The critic no longer runs on the 1080p by default.
- **Delegated approvals (§6.5)** run inside the film's own session with a fresh approver subagent, never through a second session.
- **Clock:** a clock table in `P/NOTES.md`, and the running total in every gate message.
- `fill_twos.py --ones` treats any missing frame as an error.
- **Docs:**
  - the README covers both modes, the three previews and measured render times;
  - `critic-brief-final.md` covers P3;
  - `check.sh` labels Whisper as the voice's word timings.
- **Ready to distribute on Mac and Windows.** A static review of the Windows path found three bugs that would have stopped every run; the Windows path still hasn't been run on a real PC.
  - **No `python3` on Windows:** a Windows venv has only python.exe, so Git Bash reached the Microsoft Store stub.
    - The installer now writes `python3` and `blender` commands for Git Bash into `.make-short\bin`.
    - `env.sh` falls back to the venv's python.exe.
    - `check.sh` tests `python3` itself; before, it passed by testing python.exe.
  - **ffmpeg:** `finish.py` hard-coded `~/.local/bin/ffmpeg`, and it and `motion_strips.py` derived ffprobe by renaming the ffmpeg path. Both are now found on their own: the installers' pinned build first, then PATH.
  - **Captions:** a Windows drive colon broke ffmpeg's `subtitles=` filter.
    - ffmpeg now runs in `out/` and loads `captions.ass` by its bare name, which also survives an apostrophe in the path.
    - The captions file is written as UTF-8, and `PYTHONUTF8=1` is set everywhere (cp1252 broke curly quotes and the encode).
  - **OpenCV:** `sharpcheck.py` needs it, and neither installer installed it (the author's own system Python happened to have it). Both now pin `opencv-python-headless==4.14.0.94`, and `check.sh` tests it.
  - **`blender` on PATH:** both installers add the command (a Mac link in `~/.local/bin`, a Git Bash command on Windows). SKILL §0.3 says which Python runs the tools on each computer.
  - **Smaller fixes:**
    - `fill_twos.py` copies frames where hard links fail (exFAT/FAT32, network shares);
    - the Windows home folder comes from `%USERPROFILE%`;
    - curl retries with `--ssl-no-revoke` behind antivirus HTTPS scanning, and the SHA-256 check still applies;
    - the launcher pauses once in every case, so errors stay on screen;
    - setup-mac.sh sets permissions on `v4/` (it still pointed at `v3/`).
  - **Docs:**
    - `INSTALL.md` is rewritten: macOS 14 or later, SmartScreen and Unblock, plain project folders, an accurate manual table;
    - `windows-troubleshooting.md` is rewritten for the Blender route (it still described the old Chrome engine);
    - the critic briefs name the kit's Python and ffmpeg on PATH.

## 2.2.0-rc4 (2026-11-19): character-free explainers
A request for "more explainer type, less characters", with a "How to invent X" reference, never loaded the skill, because its description promised a toy-family cast. That session asked the user to choose Blender or three.js and a Higgsfield or self-recorded voice, and it planned without the skill's gates and checks.
- **No-cast mode** (SKILL "Two modes, one pipeline"):
  - the description names character-free explainers and their triggers;
  - §2 is skipped, and the motion reviewer and the critic drop the character checks;
  - a reference sets the look. Matching it in Blender is the recommended choice over the kit's toy look, confirmed at the stills gate;
  - the reference's script structure and camera win over the formula's character beats. The topic checklist, the script critic and the fact pass stay;
  - §4.3 adds the no-cast picture rule: built, fails, fixed, big in frame, with a 12-24-frame hold on each failure.
- **Never ask which renderer or voice to use:** Blender and Higgsfield Seed Audio are fixed in both modes. A user's own recording goes through §3 steps 2-5.

## 2.2.0-rc3 (2026-11-19): the pineapple pit
The third Short, built end to end with every gate approved by a parent session for the client. The client's own notes, typed live ("some of the camera moves are rough … at 0:36 it seems like there is a repeat"), found two silent bug classes; the parent caught a third (lessons 72–82).
- **Camera pops:** CamPath silently shrank a move whose window the previous move ran into. Two 9-frame whips had become 2-frame pops, and calls out of time order snapped the camera back (the "repeat").
  - CamPath now prints `CAMWARN` for both.
  - `campath_scan` flags `COLLAPSED` whips.
  - SKILL §6.7 runs the scan on EVERY animatic. Rule: end each push or orbit AT the next move's `f - dur`.
- **Effects that vanish:** a vector-math helper returned the zero Vector output of DISTANCE/LENGTH nodes. A near-lens fade then scaled every snowflake and steam puff to 0 for two gates, and pushed a smoke fill outside its room. The fixed effects ship as the new `v4/fx.py`:
  - steam, smoke and sparks;
  - snowfall with roofed holes and a near-lens fade;
  - `smoke_fill(volume=True)` with `smoke_vol_mat2`: charcoal volume smoke with a billowing top.
- **Regression checks:**
  - new `tools/sharpcheck.py` compares sharpness against the last approved cut (a camera fix had parked the lens against a wall: 347 → 103);
  - SKILL §6.8 adds it after every `--only` round, plus a still per changed effect.
- **Crashed chunks:** Blender 5.2's shrinkwrap BVH race can kill a worker.
  - `fill_twos.py` now refuses multi-frame gaps (it used to freeze the shot over them).
  - `render.sh` refuses to mix while any frame is missing.
- **Mix (`finish.py`):**
  - `vo_min` (default 10 dB) is met by per-window music dips and per-cue SFX cuts, never by lowering the whole bed. The old gate checked the 2nd percentile, so a 4.8 dB window had passed;
  - the music duck has a 60 ms attack (20 ms chopped the bed at speech onsets) and an 80 ms lookahead (`duck_lead`);
  - `music_duck` and a 6th cue field (max length) are configurable.
- **Kit:**
  - `char`: a Georgian tie-wig (`hair.kind = 'wig'`, `pouf`, rolls), an optional cravat, a one-sided cheek smear;
  - `film.render_range(only=[])` renders nothing (it rendered everything);
  - `props.coin(name, dia, th, mats, c, rim=True)`: a round coin with a raised rim (lesson 79).
- **Stale step keys (lesson 83):** keying a property "as found" after a `frame_set()` made the curve ramp toward another shot's value. In the shipped film it darkened the dawn shot, found only by the parent's final-vs-animatic diff.
  - New `film.step_prop` / `film.step_socket`, and `jump_obj` now keys the curve's own value.
  - A late change is previewed over every frame its curves reach, not just its own shot.
  - `sharpcheck.py` scales a 1080p final to the animatic's size, and SKILL §7 runs it on every final.
- **Docs:**
  - `get_cost` → `estimate_*_cost`; log the charge, not the quote; batch timeouts;
  - gated runs end their turn after each gate;
  - script-formula field notes (twist position vs length, the cold-listener bar, how to read a channel's uploads);
  - toykit-api: the effects section and the CamPath call-order rule.

## 2.2.0-rc2 (2026-11-18): the Dutch-flood final
The independent final critic, checking the 1080p render, found faults the animatic gates never saw (lessons 65–71).
- **SFX sync:**
  - `amix` started the SFX bus at its first cue, so every SFX played 2.43 s early; the bus is now pinned by a silent full-length input;
  - every stem must be exactly the film's length;
  - generated one-shots whose hit sits late in the file are trimmed so the hit lands on its frame (`lead()`).
- **SFX level:**
  - the gate lowers only the cues sounding in a failing window, not the whole bus;
  - the SFX duck is gentle (the measured gate is the guarantee);
  - hits went from 30–50 dB under the voice to 5–23 dB, and every spoken window keeps at least 10 dB.
- **Whip-start ghosts:** `setup_render` uses 16 motion-blur steps by default. Whip-start frames (`P.move_starts()`) render at 64 via `render_range(mb_steps=)`. One step had rendered the first frame of every whip as a double exposure with tile blocks.
- **Water through grass:** `pour_mat` has a keyable hidden band (`VCUT`..`VEND`), and `world.sink_under_front()` keys it to follow a spreading flood front, so a pour's tongue no longer shows through grass blades as white strips.
- **Docs:**
  - `toykit-api.md`: whips start at `f - dur`, and hidden changes go on `f - dur + 1`;
  - `example-hardtack/critic-brief-final.md` and SKILL §8: the final critic's brief and what to look for.
- **New tool:** `tools/dbg_render.py` renders a frame with ONE thing changed (an object removed, a material made opaque, a render setting), to find what causes an artefact.
- **Also:**
  - BT.709 encode;
  - a shared render queue;
  - measured final-render ETAs.

## 2.2.0-rc1 (2026-11-17): the cold-start test (Dutch flood)
- **Motion review after every 480p render** (Matt: "some of the scenes don't animate properly… the water animation is very rudimentary"):
  - SKILL §6.3, `tools/motion_strips.py` and `example-hardtack/critic-brief-motion.md`;
  - an independent reviewer judges each line's MOTION at 6 fps, with a pass bar of 7/10 (lesson 59).
- **Moving water:** `world.spread_mat` (spreads, drains, recentres), `pour`, `churn`, `boil`, `spray`, `ripple` and `flow_water`.
- **Life:** `alive()` in the example `film.py` puts F-curve noise on every actor's head, chest and weight (lesson 60).
- **Camera:**
  - `campath` prints `NEAR` when the camera is inside or grazing a character, and `campath_scan.py` flags it;
  - lesson 61 covers EXPO whips (one smeared frame) versus push flights, and orbit/whip key order.
- **Kit:** `Timing.word` warns when an unscoped word is in several lines; lesson 62 covers `follow` without `f_off`.
- **Mix v2** (lesson 58): loudness-matched, smoothed, ducked SFX, and a measured voice-margin gate.
- **Motion review round 2** (lesson 63):
  - the pour wobbles sideways and tears its edges (`TEAR`); spray streaks;
  - SKILL caps the motion fix rounds at two, then the user sees the cut with the reviewer's open list.
- **camstats:** the docstring now gives its own reference numbers (median 0.3, mean 3.7, 74 % still, a big move every 1.4 s); the still % is not a target.
- **Colour:** `finish.py` now converts with the BT.709 matrix and tags it. ffmpeg's default (BT.601, untagged) made greens about 6 levels darker in QuickTime, browsers and YouTube. Earlier masters have that shift; re-running `finish.py` fixes one without a re-render.
- **Render speed:**
  - `render.sh` and `animatic.sh` workers claim chunks from a shared queue; the old fixed 3-way split left two workers idle for the last 20-27 min of a final;
  - measured ETAs in `render.sh`'s header: 61 s of water-heavy film took 88 min, about 2.6 s/frame with all three workers busy.
A fresh session ran the skill end to end on a new topic. Every gap it hit is fixed here; the log is `TEST_NOTES.md` in that project.
- **Ships what it promised:**
  - `v4/style_target.jpg` (the look the sheets are generated against);
  - `timing_dump.py` (`finish.py` needs `voice/timing.json`; `animatic.sh` and `render.sh` now refresh it);
  - the newer Hardtack `film.py`: the `campath:a-b` mode, `orbit_from` measuring its start from the landed camera, and per-chunk `NEED` skips.
- **New tools:**
  - `draft_timing.py`: block and gate shots before the voice exists;
  - `campath_scan.py`: lesson 46's reversal/jerk/stall check, automated;
  - `gatesheet.py`: labelled gate contact sheets.
- **Kit:**
  - hats `tricorn` and `wide` (with `flop` and `fray` for straw), `clog` feet, and an analytically fitted `beard`;
  - `world.water` + `shallow_water_mat` (a flood or beach);
  - `walk()` raises when it ends before it starts;
  - `Timing` lists unheard words and ignores dike/dyke and knee deep/knee-deep;
  - `finish.py` takes ffmpeg from PATH.
- **Voice:** `pace.py` takes several `--quote/--after` pairs and warns when a quote finds no pause. SKILL §3 adds a heard-word check before pacing and `timing_dump.py` after it.
- **Script:** `measure_script.py` checks SENTENCES (two fragments hid inside one quote line) and adds the time the quoted lines need.
- **Docs:**
  - SKILL: a no-idea topic menu, a project folder the app can open, silhouette-different cast designs, early blocking, toy scale, ground lift, `W()` scoping, travelling cameras, price preflights, honest ETAs;
  - `higgsfield-v4.md`: rewritten narration steps (no more `tighten.sh`/`atempo`) and live prices;
  - lessons 25 and 26 corrected, and 47-54 new;
  - README updated.

## 2.1.0-rc1 (2026-11-17): hardtack round 2
- **Animatic gate** (`animatic.sh`, `fill_twos.py`): the whole film at 480×854, 8 samples, on twos, with the full mix, in about 12 min. The critic and the user review it; the 1080p final is rendered once, after sign-off.
- **Camera:** `film.CamPath`, one continuous camera per set in the reference's grammar: slam/whip/push/orbit/exit, an accelerating creep after every landing, impact shakes, and sets joined inside one whip.
- **Hands do things:** `props.follow`, `props.grip` and `props.target`, so hands land on keyed props. Added `props.bug`, `props.spoon`, `props.crumbs` and the `mug(coffee=)` colour.
- **Voice:** `voice/pace.py` (pause-only pacing, a second-voice quote, junk-opening drop) and `voice/onsets.py` (word starts snapped out of pauses). `tighten.sh` is retired, because its time-stretch and pitch-shift read as static.
- **Gate:** `film.py SET dir report` (framing numbers per beat) and `beats` stills. `frames_arg` accepts `a-b:2`.
- **Fixes:**
  - `turn_body` drift (it read stale pose values after `frame_set`);
  - the creep aim overshoot after big whips;
  - deterministic blink seeds across workers;
  - the steam origin.
- `finish.py` fits the music to the film length (music only).
- **Client rules folded in:**
  - Scripts are written FOR THE EAR: characters introduced before they act, one tense, lines that lead into each other, and 0-2 fragments that are never back to back. `measure_script.py` flags staccato runs.
  - Every question is a clickable choice.
  - ETAs follow the new tiers (animatic about 12-16 min, final about 50 min at 16 samples).
  - Orbits start where the camera is, and a camera-path scan runs before the final (lesson 46).

## 2.0.0-rc1 (2026-11-16): v4, a ground-up rebuild
- **New engine, `v4/toykit`.** Stylized 3D toy-family characters with real expressions, built from a spec in Blender 5.2.
  - Faces are shape-keyed decals: 14 expressions, blinks, gaze and lip-sync.
  - Hats are fitted to the head: beanie, kepi, forage cap, toque.
  - Moustaches, aprons, sashes and epaulettes.
  - An IK noodle-arm rig with an Actor API: poses with overlap, look, walk, hop, wave.
- **Worlds and props.** Meadow, grass, trees, tents, campfire, sea, lighthouse, clouds; props held in a hand.
- **Look.** A grade tuned to the target: Khronos colour, painterly dabs, sky-masked haze, sun beams, bloom.
- **Film as code** (`film.py`).
  - Word-timed acting.
  - Shots with eased camera moves and blur-free cuts.
  - Dusk light changes.
  - A one-still-per-shot gate.
  - Parallel rendering.
- **Script formula** (`references/script-formula.md`), measured on 29 viral explainer Shorts: a 7-beat template, hook types, language rules and a gated rubric. Every script gets an independent critic.
- **Higgsfield.** Model sheets for your own characters, then measured and rebuilt in 3D (`tools/grid.py`, `compare.py`). Also narration, music and SFX. No video generation.
- **Sound.** `voice/tighten.sh` sets the pace and the character voice; `finish.py` adds Montserrat captions, ducked music, SFX on story beats and ambience.
- **Kept from rc2:** the one-step Mac and Windows installers and `check.sh` (its smoke test now renders a toykit character).
- **Archived, no longer shipped:** the v3 bean engine, the legacy 2D route and their references.

## Earlier (v3 Higgsfield edition)

## 1.0.0-rc2 (2026-11-16)
- **Windows one-step install:** `setup/setup-windows.ps1` + double-click `Install on Windows.cmd`. No admin rights; pinned SHA-256s; installs Blender 5.2.4, ffmpeg 9.0.2, uv, Python 3.12 + Whisper, Node 24 and Portable Git only where missing; user PATH only. Written for Windows PowerShell 5.1. Not yet run on a real Windows PC.
- **Both setups now install the skill too:** run from wherever you unzipped it, they copy it into `~/.claude/skills/make-short` (an older copy moves to `~/.make-short/backups`).
- env.sh, check.sh, measure.sh and finish.mjs know the Windows tool folders.

## 1.0.0-rc1 (2026-11-13)
**macOS (Apple Silicon)**
- `setup/setup-mac.sh`: one-command install with no admin password and pinned checksums (Blender 5.2.4, ffmpeg 9.0.2, uv, Python 3.12 + Whisper, Node 24 if needed).
- `setup/check.sh`: health check with fixes, plus `--smoke` for a real Blender still.
- Mac fixes in env.sh, gate/tune/render.sh, the voice scripts, sets.py fonts and measure.sh. Details in MAC.md.
- `v3/voice/transcribe.sh`: the free voice route (Whisper + word timing) in one command; prints words per second.

**Higgsfield steps (optional; images + voice only, never video)**
- `references/higgsfield.md`: the protocol, costs, verbatim prompt blocks, steps H1–H7 and Gate H.
- `v3/hf/plates.sh`: engine reference stills; `palette.py`: sheet colours → chars.py values; `tileable.py`: seamless painted textures; `boards.py`: storyboard sheet + board-vs-render comparison.
- Critic rubric criterion 11 (board match); CHECKLIST section D; hooks in SKILL.md steps 0, 1, 3, 4, 5 and 6.

**Fixes to the original (all platforms)**
- `shots/validate.js` accepts the `cut` transition and no longer hard-codes the 60 s example's last frame.
- `measure.sh` quotes its file paths.
- All .sh scripts ship executable.
