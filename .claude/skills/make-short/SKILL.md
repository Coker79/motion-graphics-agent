---
name: make-short
description: Make a 45-60 s animated YouTube Short end to end, rendered free in Blender EEVEE, either in a stylized 3D "toy family" look (egg-head characters with real expressions in a sunlit, painterly world) or as a character-free explainer (objects and machines in a 3D miniature diorama, like "How to invent X"). Claude writes the script with a formula reverse-engineered from viral explainer Shorts and gets an independent critic score, designs the user's own characters as Higgsfield model sheets and rebuilds them in 3D (skipped when there are none), generates narration, music and SFX on Higgsfield (never video), writes every shot as code, gates one still per shot, renders, captions, mixes, and has independent critics review the previews. Never uploads without the user's explicit go. Use for "/make-short <idea>", "make a YouTube Short", "make an animated short about ...", an explainer Short with few or no characters, and "turn this into a Short".
---

# make-short (v4: toy-family 3D Shorts)

**SKILL** is this skill's folder. **P** is the user's project folder, a copy of `SKILL/v4`. Paths are relative to P unless they start with SKILL.

**Installing from a download** (an unzipped zip, not yet in `~/.claude/skills`)? Follow `SKILL/INSTALL.md`, section "For Claude Code".

**Binding references:**
- `SKILL/references/script-formula.md`: the story formula.
- `SKILL/references/toykit-api.md`: the kit.
- `SKILL/references/lessons-v4.md`: read before step 4 and before every fix round.
- `SKILL/references/higgsfield-v4.md`: prompts, prices and gotchas.

**The worked example** is `P/example-hardtack/`. It is a 48 s Short: script, story, `film.py`, cues.

**Two modes, one pipeline.** Pick the mode at GATE 1 from the request or the reference; ask (clickable) only if neither says.
- **Cast** (the default): toy-family characters act the story, in the kit's toy look (`SKILL/v4/style_target.jpg`). Every step applies.
- **No cast:** an explainer told with objects, machines and landscape only, such as a "How to invent X" diorama, or a request for "no characters" or "less characters".
  - Skip §2. Tell the motion reviewer and the critic to drop the character checks (faces, hands and feet, acting) and to score the objects and the mechanism instead.
  - **A reference sets the look.** When the user gives one, recommend matching its look in Blender (materials, outlines on or off, light, lens blur) over the kit's toy look, and confirm it at the stills gate. Without a reference, use the toy look.
  - Follow the reference's script structure and camera over the formula's character beats. A slow one-take glide over a diorama is fine; §4.2's big move per sentence is the cast default. Keep the formula's topic checklist, the script critic and the fact pass.
  - Build the world in a project module with `look.mat` (§4.1).
- **Never ask which renderer or voice to use.** In both modes Blender renders every frame and the voice is Higgsfield Seed Audio (§3). If the user brings their own recording, run it through §3 steps 2-5 instead.

## Rules, always
- **Make the first version as good as possible.** A 50-60 s Short should take about 9-11 h of wall clock with a cast, and less without one, not the 19-20 h the pineapple pit took. Read the lessons before you build, run every automatic check before anyone sees a cut, and plan exactly three previews (§6). Keep a clock table in `P/NOTES.md` (step, start, end) and put the running total in every gate message.
- **Nothing is uploaded or posted unless the user types "go".** Never print or ask for API keys.
- **Higgsfield makes reference images, voice, music and SFX only.** Never Seedance, never video, never Higgsfield 3D: every frame is rendered in Blender. Ask once for a credit budget per Short (30-50 is typical) and keep a spend log in `P/story.md`.
- **The user designs their own characters.** Never reuse a stock cast without asking.
- **Look at every still you render** by reading the PNG. Numbers passing is not passing.
- **Never self-score.** The script and the previews (P1, P3) each get an independent critic subagent; the 1080p film gets one only if the user asks (§7).
- **Archive, don't overwrite.** Never overwrite a render or an audio file the user has seen. Archive it to `out/vN-<change>/` first.
- **No false claims.** Never say "one prompt", "one click" or "fully automatic". The user approves the script and the designs; Claude writes and builds the rest.
- **Every question to the user is a clickable choice.** Use AskUserQuestion with options, and put the script or design in the preview. Never mix typed and clickable questions.
- **Quote ETAs from the clock.** On an M1 Pro, for 50-60 s:
  - script critic and cold listener: about 30 min, in parallel (start blocking shots on draft timing meanwhile, §4);
  - stills gate: about 1 min per set (all sets in parallel);
  - previews: P1 15 min to 2 h depending on the scene (the 61 s beehive Short's took 1 h 50 min), P2 (`--only`) 1-10 min, P3 (`--ones`) about twice P1. Before quoting, time a 3-frame `--only` render of the heaviest set and scale up. Render P1 and P2 with `TK_MB_STEPS=2`: motion-blur steps dominate (8 → 2 steps took 5.5 → 3 s a frame). P3 and the final keep full steps;
  - final: see `render.sh` (16 samples, 3 workers sharing the GPU, which on an M1 Pro render about as fast as one); quote the measured figure in its header. The beehive final took 2 h 20 min.
  - Fix rounds re-render only the changed ranges (`animatic.sh --only`), so a round takes 1-5 min.

## 0. Set up
1. Copy `SKILL/v4` to `<current folder>/<slug>` (or the folder the user names; `~/shorts/<slug>` only when there is no working folder). That copy is P. Keep P inside the session's folders so the user can open the script, stills and mp4.
2. Health check: `bash SKILL/setup/check.sh --smoke`.
   - On FAIL, run the installer in the background (it never asks for input; 10-30 min). Mac: `bash SKILL/setup/setup-mac.sh`. Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL>\setup\setup-windows.ps1"`, or the user double-clicks `Install on Windows.cmd`.
   - The installers pin every direct download by SHA-256 (and every Python package by version) and need no admin rights.
3. **Commands on each computer.** The installers put `blender`, `ffmpeg` and `ffprobe` on the PATH (Mac: `~/.local/bin`; Windows: `%USERPROFILE%\.make-short\bin`, used from Git Bash). On Windows, Claude Code uses Git Bash once Git is installed; the installer adds Portable Git if needed and points Claude Code at it, so a restart picks it up.
   - **Run every `python3 ...` command in this file with the kit's Python**, which has numpy, pillow, OpenCV and Whisper. On a Mac, that is `~/.make-short/venv/bin/python3`; the Mac's own `python3` lacks them. On Windows, `python3` is the installer's command for it.
   - The `.sh` scripts set all of this up themselves (`env.sh`).

## 1. Script (GATE 1: the user approves)
0. **No idea given?** Offer 4 topics as clickable options. Each must pass the formula's topic checklist (8 or more). Put its hook, the true mechanism with its source, the checklist score and the new kit parts it needs in the preview. Ask for the credit budget in the same question set.

Follow `script-formula.md` §7 exactly:
1. Run the topic checklist (8 or more, with items 1 and 2 mandatory).
2. Draft 5 hooks and keep the best (5 or more out of 6).
3. Write a 7-beat sheet with word budgets: target seconds × 3.7.
4. Write one sentence per line, **for the ear** (formula §7 step 7: introduce characters before they act, one tense, lines lead into each other, 1-2 fragments at most), into `P/script.txt`. Mark the turn line with `>T` and the explanation line with `>X`.
5. Measure: `python3 tools/measure_script.py script.txt <seconds>`. It checks SENTENCES, not lines: a quote line can hide two fragments back to back.
6. **One review round, then the user.** In parallel, give:
   - a fresh critic subagent the formula, the script and the checked facts, but not your own scores (pass: 8.5 or more with every gate passed);
   - a fresh cold listener only the script, as it will be heard: what was predictable, what was confusing, where they would swipe, and a score out of 10.
   Apply both in ONE rewrite and re-measure. Re-score only if a gate failed, and only once. Then go to the user with both reports (step 8). Don't loop on the listener's score: on the pineapple pit, about 4 h of rewrites never moved it off 7/10, and the fix that mattered came from a note at GATE 1. Both reviews take about 30 min: block shots on draft timing meanwhile (§4).
7. **Fact pass.** Tag every claim TRUE (with its source), FABLE or CHECK. A CHECK blocks the script. Sources go into `P/story.md` with the shot table (one picture per sentence).
8. **Ask the user** to approve the script. Put the full text in the question's preview, with the critic's score and the listener's main note.

## 2. Cast (GATE 2: the user approves the designs)
**No cast?** Skip this section ("Two modes" above).

0. **The user designs the cast.** Offer 2 directions per character as clickable previews (hat, garment and colour, accent, facial hair). **Make the silhouettes different** before generating: body width, hat shape, facial hair and colour family. The template's defaults (egg head, bean body, hat, moustache) make near-identical triplets. In the Dutch-flood test, the farmer was rejected as "very different from the others please".
   - **The user as a character.** If they ask to be in the story, ask for a photo. Their hair, glasses and facial hair are the identity, so keep those recognisable at GATE 2. The kit has `hair: crop` (short hair with a quiff), `glasses` (thin wire rims) and `facial_hair: beard` (stubble down to a full beard); fields in `toykit-api.md`.
1. Make one Higgsfield model sheet per character with the template in `higgsfield-v4.md`. Upload the style target, `SKILL/v4/style_target.jpg`, once (`media_upload`, then a PUT, then `media_confirm`) and pass it as `image_references`. Save the sheets to `P/design/`.
2. Show the sheets to the user. Regenerate only what they reject.
3. **Measure each front view.** Run `python3 tools/grid.py design/X.png x0 y0 x1 y1 out.png` and read off:
   - head width = W, chin, eyes, brows, mouth, moustache and hat band, in W units from the head centre;
   - body, arms, legs and feet in metres (scale = 0.42 m per W).
4. Write `P/specs/<name>.json` (fields in `toykit-api.md`). Start from the closest example spec.
5. **Check against the sheet.** Render `blender -b -P tk_turn.py -- specs/<name>.json renders/fit_<name>` (about 20 s), then `python3 tools/compare.py cmp.png 600 "SHEET=design/X.png" "front=renders/fit_<name>/t_front.png" ...`. Look, fix the spec, repeat until it reads as the same character.
6. A part the kit lacks gets added to `toykit/char.py`, as a method with a dispatch entry, fitted to the head with `_fit`. The hats are beanie, kepi, toque, tricorn and wide (with `flop` and `fray` for straw). The feet are round, boot and clog. Facial hair is the moustache styles or `beard`. Hair is `curly_tuft`, `wig` or `crop`, and `glasses` are wire rims. The wardrobe adds `apron`, `epaulettes`, `bandana`, a plaid `sash` and `lower` (two-tone trousers). Keep moustache spans at 0.66 W or less: decals near the head's outline spike (lesson 50).

## 3. Voice (never time-stretch or pitch-shift it: lesson 22)
1. Generate one Seed Audio take of the whole script, WITHOUT the quoted lines, into `voice/narr.wav`. Use a preset voice, `speech_rate` 40-50, `sample_rate` 48000, and write numbers as words ("sixteen seventy-two"). Generate each quoted character line separately, each in its own preset voice, into `voice/quote_<who>.wav` (lesson 23). Preflight the cost with `estimate_audio_cost` and quote it when you ask (the connector no longer accepts `get_cost`).
2. Prepare both takes: highpass 70 Hz and `loudnorm` to −18 LUFS; trim the quote's silences.
3. Whisper the narration into `voice/narr.json`. Then check that every script word was heard, in order. Whisper can drop words on a long take: the Dutch-flood take lost "drowned field". If any are missing, re-run Whisper on that 5 s clip and splice the words in. Otherwise the pacer misreads the pause and won't insert the quote.
4. Run `python3 voice/pace.py voice/narr.wav voice/narr.json voice/voice.wav --script script.txt [--quote voice/quote_a.wav --after "word,"] [--quote voice/quote_b.wav --after "word."] [--hold "word.=0.6"]`. The `--quote`/`--after` pairs repeat. The keys are Whisper's tokens, punctuation included; a hyphenated word may come back split ("-deep."). It only shortens pauses; aim for 3.3-3.7 words/s.
5. Whisper `voice/voice.wav` into `voice/voice.json`, then run `python3 voice/onsets.py voice/voice.wav voice/voice.json`, then `blender -b -P timing_dump.py`. That writes `voice/timing.json`, which `finish.py` needs, and prints every line's frames. It warns, listing the words, when more than 3 script words weren't heard.

## 4. Film as code (GATE 3: the stills)
0. **Block early.** Right after GATE 1, run `python3 tools/draft_timing.py script.txt voice/draft.json`, which gives Whisper-shaped timing from the script. Then block and gate shots while the critic, the cast and the voice run. `film.py` falls back to it until `voice/voice.json` exists, and every S()/W() anchor carries over.
1. Copy `example-hardtack/film.py` to `P/film.py` and rewrite its sets and shots for this story. A new world goes in a project module (for example `P/polder.py`): build every piece with `look.mat` and outlines, and test it in a 4-view still script first.
   - **Toy scale:** a character is about 1.2 m, with the hip at 0.35 m, arms 0.31 m and a reach of about 0.43 m. Convert every real measure the characters touch: 40 cm of "knee-deep" water is 0.20 m here.
   - **Ground height:** characters stand at z = 0. On a dike or bank, lift the armature (`A.arm.location.z`) and add the lift to `framing()`.
   - **`W()` is global.** In every set after the first, look words up with `after=(F0 - 1) / 30.0`, or `W('reached')` finds an earlier line's "reached" and a walk silently becomes zero frames.
2. **One continuous camera per set (`film.CamPath`).** Put a big move on almost every sentence (slam, whip, orbit, push), landing on its first word. After each landing the camera creeps on. Use 2-3 hard cuts per film at most. See `toykit-api.md` § CamPath.
3. **Each sentence's picture:**
   - Characters live in places and move between them on screen, or teleport inside a whip (lesson 32).
   - They act with `pose`, `look`, `walk`, `hop`, `face.express`, `gaze` and `talk`, keyed to `T.line(n)` and `T.word('...')`.
   - **Hands do the actions** by following keyed props (`props.grip` and `props.follow`, lesson 29).
   - **No cast:** each line's picture is an object or the landscape changing on screen, big in frame: it gets built, it fails, it gets fixed. Hold 12-24 frames on each failure so it reads.
4. Exposition lives in props. The hook frame rhymes with the last frame. Lighting changes and set changes hide inside whips.
5. Register a `beat(frame, name, *subjects)` for every landing AND at the peak of every key action: the hands on the prop, the drop, the first step into water. Motion bugs only show mid-action (lesson 55).
6. **Gate:**
   - Run `blender -b -P film.py -- <set> renders/report report` and fix anything OUT or off-centre.
   - Then run `... <set> renders/gateN beats --preview` for every set, in parallel. That gives about 40 stills in about 1 min.
   - Build labelled contact sheets (`python3 tools/gatesheet.py renders/gateN sheet.png`), look at every still, and fix framing, blocking and props. Expect 2-3 rounds; lessons 16-21, 29-37 and 47-50 cover the usual failures.
   - **Frame for the Shorts screen.** Keep faces out of the right-hand button stack and the bottom 30%. FRAMING sizes are vertical metres, so step every character shot one size wider than looks right in the still: a 0.42 m head needs about 1.1 m of frame (lesson 87).
   - **Keep big moves slow.** EEVEE's stepped motion blur ghosts fast moves: 7 m in 0.7 s, or a 270° spin in 18 frames (lesson 88).
   - A walking subject needs a camera that travels with it. Chain short pushes to its real position (`track()` in the Dutch-flood film); a single push leads or lags an eased walk.

## 5. Sound
1. Generate on Higgsfield, preflighting each price with `estimate_audio_cost` (Mirelo is priced by length):
   - SFX: Mirelo, 2 s each, about 10-12 cues plus 2-3 ambiences;
   - music: ElevenLabs Music v2.5, instrumental, the Short's length. Find its last strong hit and `land` it on the last story beat.
2. Check every file's level and replace any that came back silent (lesson 24). Don't hand-balance by peak: `finish.py` loudness-matches every SFX, ducks SFX and music under the voice, and gates the mix so nothing comes within 10 dB of a spoken word (lesson 58).
3. Write `sfx/cues.json`. Anchors are words or lines; see `example-hardtack/cues.json`.

## 6. Previews (GATE 4: three planned previews at 480p, then the user)
**Plan exactly three previews.** They all render at 480×854, 8 samples, with the full mix. Never start the next one before the last one's reviews are in: two pineapple-pit cuts were thrown away unreviewed. Make a fourth only if P3 shows a regression or the user asks for one.

| Preview | Render | Checks and reviews | Then |
|---|---|---|---|
| **P1** | `bash animatic.sh p1 "<sets>"`, on twos: about 12 min for 50 s, 20 min for 61 s with 4 sets | the automatic checks (step 1); the motion review (step 2) and the whole-film critic (step 3), in parallel | fix everything they flag in ONE round |
| **P2** | `bash animatic.sh p2 "<sets>" --only "set:a-b ..."`: only the fixed ranges, 1-10 min | the automatic checks; re-review only the changed lines | send it to the user with the reviewers' open list (step 4); apply their notes |
| **P3** | `bash animatic.sh p3 "<sets>" --ones`: every frame rendered, the final's motion, about twice P1 | the automatic checks; the critic's last look (§8); 1080p stills of about 10 key frames | the user approves P3, then the ONE 1080p render (§7, lesson 28) |

P3 shows what twos hide: one-frame pops, whip-start smears, relights after a whip and SFX off their hits (lessons 65-71). It replaces the critic pass that used to run on the 1080p film.

1. **Automatic checks, on EVERY preview, before any reviewer or the user sees it:**
   - **Camera:** `python3 tools/camstats.py out/NAME.mp4 --twos` (drop `--twos` for P3). Aim for a big move every 2 s or less (the reference: every 1.4 s, mean 3.7 px/frame). camstats sees pans and shifts only, so its "still %" is about 74% even on the reference: don't chase it. Fix the holds (lesson 56).
   - **Camera paths:** `blender -b -P film.py -- SET renders/x campath:A-B | python3 tools/campath_scan.py` for every set. Fix every `CAMWARN` (a move that starts late because the previous one ends inside its window, or calls out of time order) and every `COLLAPSED` whip: end each push or orbit AT the next move's `f - dur` (lessons 72-73). `film.py` prints the planned moves, so the scan flags only reversals at speed, unplanned jerks and stalls (lesson 46).
   - **Regressions:** `python3 tools/sharpcheck.py out/PREVIOUS.mp4 out/NEW.mp4` flags runs of 6+ frames under 40% of the previous cut's sharpness (a camera parked against a wall, a lost focus key, a late key ramping across earlier shots). Diff every frame, not just the lines you changed (lessons 74-75, 83). Use the kit's Python (§0.3; it has OpenCV).
   - **Effects:** after ANY change to an effect's node tree (steam, snow, smoke), render one still where that effect is the subject and compare it with the last approved one: a silent node bug once zeroed every flake and puff for two gates.
2. **Motion review** (P1, then only the changed lines of P2). Stills can't see motion (lesson 59).
   - Cut the preview into per-line motion strips: `python3 tools/motion_strips.py out/NAME.mp4 voice/timing.json critic/motion_X 6` (6 fps, frame-numbered).
   - A fresh subagent judges MOTION line by line, using `example-hardtack/critic-brief-motion.md`:
     - effects move like the real thing (water spreads with a foamy front and splashes; no sliding textures or flat planes rising evenly);
     - feet and hands make contact; no frozen actors; the camera shows the action.
   - Fix every line under 7/10 in the P1 round. A strict reviewer may never pass every line (the Dutch flood went from 4.9 to 5.5), so lines still under 7 after P2 go to the user as the open list, and they choose whether any is worth more time.
   - The usual fixes:
     - water that moves (`world.spread_mat`, `pour`/`churn`/`boil`, `spray`, `ripple`, `flow_water`);
     - `alive()` on every actor, plus one pose change per phrase (lesson 60);
     - no `follow` without `f_off` (lesson 62);
     - camera clearance and push-not-whip flights (lesson 61). Run `campath` on the set and fix every `NEAR` it flags.
3. **Whole-film critic** (P1): a fresh subagent briefed with `example-hardtack/critic-brief-animatic.md` (§8, about 20 min), in parallel with the motion review. Verify each claim on the frames before fixing it.
4. **Send the user P2** (GATE 4). Tell them it is a preview: steppy motion and grain are expected, and they should judge story, timing, camera, acting and sound. Their notes go into P3.
5. **Delegated approvals** (the user asks Claude to approve the gates for them): approve inside the session that makes the film. At each gate, give a fresh approver subagent the evidence (script, sheets, stills, strips, preview) and the user's taste notes, and act on its verdict. Don't route gates through a second session: a reply to a busy session waits until its turn ends, and one overnight wait on the pineapple pit cost about 3½ h. Keep long renders inside an active turn. On a Mac, `caffeinate -i -w <pid>` keeps it awake; on Windows, plug the laptop in and set sleep to Never while it renders.

## 7. Final render, captions, mix
Run `bash render.sh <set> <set> ...`, ideally while the user is away (50-70 min for 50 s; the water-heavy 61 s Dutch flood took 88; the 52 s pineapple pit, with volume smoke, snow and steam, took 132 including the mix). It refuses to mix while any frame is missing (a crashed worker, lesson 82): re-render the listed frames, then run `python3 finish.py`. Then compare the final with P3: `python3 tools/sharpcheck.py out/p3.mp4 out/short.mp4` (the kit's Python; it scales the final down). Treat every flagged run as a regression until a frame shows otherwise (lesson 83). Three Blender workers pull frame chunks from a shared queue, then `finish.py` produces `out/short.mp4`, encoded with the BT.709 matrix that HD players decode with:
- Montserrat ExtraBold one-word captions;
- music and SFX ducked under the voice, the SFX loudness-matched and smoothed, and a measured gate that keeps the voice on top (lesson 58);
- SFX on their beats;
- ambience;
- loudness at −14 LUFS.

**Then ask the user; don't assume a critic pass.** Once the automatic checks pass (no missing frames, no sharpcheck flags against P3, the mix gate's voice margin, −14 LUFS), send the film and ask (clickable):
- **Ship as is** (recommended when every check passes): P3 already had the critic's last look.
- **Critic review only:** the independent critic on the 1080p film (§8, about 40 min). Nothing changes unless the user approves it.
- **Critic + one fix pass:** the critic, then ONE re-render of only the frames it flags (archive the originals first).

## 8. Independent critic (P1 and P3; the 1080p film only if the user asks)
1. Give a fresh subagent:
   - the preview mp4 (or the 1080p film, when the user chose that pass at §7);
   - the style target;
   - the character sheets;
   - `script.txt`;
   - a request for frames every 0.5 s.

   On P3, and on the 1080p film if the user chose that pass, brief it with `example-hardtack/critic-brief-final.md` (about 40 min). Rendered on ones, they show faults that twos hide (lessons 65–71):
   - ghosted whip-start frames;
   - relights that pop after a whip;
   - effects bleeding through grass;
   - off-sheet costume details (check these on P3's 1080p stills: `TK_SAMPLES=16 blender -b -P film.py -- SET renders/p3_1080 a,b,c`, about 1-2 min per set);
   - SFX off their hits.
2. It scores:
   - look vs target;
   - character fidelity;
   - acting;
   - camera;
   - readability (captions, props);
   - audio sync;
   - pacing.
3. It lists its top 3 fixes by frame range.
4. Verify each claim at full resolution before acting on it.
5. Re-render only the frames you fix (`film.py SET renders/final a-b` or `a,b,c`; archive the originals first), then rerun `finish.py`.

## 9. Deliver
Hand over `out/short.mp4` and the title options from `story.md`.
- Titles start with the object or category and imply the paradox (formula §5).
- The description carries the facts and their sources, plus `#Shorts`.
- The user uploads. Posting through a service only after the user types "go".
