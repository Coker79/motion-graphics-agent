# Critic brief: FINAL review, last pass (independent; SKILL step 8)

You did not build this film. Score it honestly. Builders rate their own work about 2 points too high, and an agent handed the builder's hopes tends to confirm them. Don't.

## What this file is
- **Film:** `out/short.mp4`, the FINAL: 1080×1920, 30 fps, 16 samples, on ones, about <N> s.
- The client signed off the animatic (`out/<animatic>.mp4`). This pass catches what only the full-quality render shows. The animatic's 480p and its on-twos timing hid all of these on the Dutch flood:
  - the first frame of a whip rendered as a ghosted double exposure;
  - a set change (a relight, a teleport) popping after a whip had landed;
  - a water effect showing through grass blades as white strips;
  - off-sheet character details.
- Judge everything.
- **On P3** (`out/p3.mp4`: 480×854, every frame rendered, 8 samples; raw frames in `renders/animatic_ones/`), run the same checks at preview size: motion, timing, one-frame pops, whip-start smears, relights after a whip, effects bleeding through, SFX on their hits. Leave fine texture and small costume details to the 1080p stills in `renders/p3_1080/`. P3 replaced the old critic pass on the 1080p film; that pass now runs only when the user asks for it.

## Context
- **Look target:** `style/target_look.png`.
- **Script:** client-approved, `script.txt`, one sentence per line (`>T` and `>X` are markers, not spoken). Do not critique the wording; judge whether each sentence's PICTURE reads.
- **Characters:** the approved sheets in `design/`.
- **What each line should show:** the table in `story.md`.
- **Beats:** `renders/<gate>/beats_*.txt` (frame number and beat name).
- **Word timings:** `voice/timing.json` (seconds; frame = round(s × 30) + 1).
- **Sound cues:** `sfx/cues.json` (anchors explained in `finish.py`). The stems are in `out/stems/`.

## Method
Tools: the kit's Python has cv2, numpy and PIL (`~/.make-short/venv/bin/python3` on a Mac, `python3` on Windows); `ffmpeg` is on PATH. The Bash tool's shell may be zsh, which does not word-split variables: run loops with `/bin/bash`. Frames are 1-based (fNNNNN = mp4 index NNNNN−1); the raw frames are `renders/final/fNNNNN.png`.

1. **Frames and sheets.**
   - Extract 2 fps frames and make contact sheets.
   - Then check single full-resolution frames per line: hands on props, the water, the faces.
   - Look at the first frame of every whip or slam (the camera path is in `film.py SET dir campath:a-b`), and at the frames around every relight.
2. **Camera.** Run `python3 tools/camstats.py out/short.mp4`. Report:
   - the median px/frame;
   - the % of near-still frames;
   - the number of big moves;
   - whether the moves land on sentence starts.
3. **Sound, as data.**
   - Measure loudness with ebur128.
   - Check that every stem in `out/stems/` is exactly the film's length. A short stem means shifted audio: the Dutch flood's SFX bus played 2.43 s early.
   - For the key hits, find where each SFX actually peaks, and compare that with its cue frame and the visual hit.
   - Measure each hit's level against the voice.
   - Listen for static or warble in the voice. Check that the captions match the words.
4. **Score each criterion 0–10**, with one sentence of evidence that cites frames.

| # | Criterion |
|---|---|
| 1 | Look vs target, including render quality: noise, flicker, ghosting, smears, swimming textures, effects bleeding through foliage |
| 2 | Character fidelity vs the sheets, part by part, under the film's lighting |
| 3 | Acting: expressions on the right beats; hands DO the actions |
| 4 | Camera: dynamic, purposeful landings, nothing blocked, empty or cropped |
| 5 | Story readability: each sentence's picture reads on its own, with props carrying the facts |
| 6 | Continuity: no popping, floating or teleporting on screen; hidden swaps are really hidden; no clipping |
| 7 | Captions: readable, in sync, never over a face or the key prop |
| 8 | Audio: clean voice, music ducked, SFX ON their hits (measured), about −14 LUFS |
| 9 | Pacing, hook and loop: the first 2 s stop a scroller; the last frame flows back into frame 1 |

## Output: `critic/critique-final.md`
- The score table and the mean.
- **The top 3 fixes, ranked by impact.** Each names a frame range, what is wrong (seen on a frame you looked at), and the concrete change. Ideal changes are:
  - "move the relight to the whip's frame f−dur+1";
  - "lift captions for f415–476";
  - "pin the amix bus".
- Separately, list anything already in the signed-off animatic. That is the client's call.
- Keep it under 1,000 words. Verify every claim on an actual frame or measurement before writing it.
