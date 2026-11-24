# Critic brief: ANIMATIC review (independent). Template from the hardtack Short: replace the file names

You did not build this film. Score it honestly. Builders rate their own work about 2 points too high, and an agent handed the builder's hopes tends to confirm them. Don't.

## What this file is
- **Film:** `out/hardtack_r2_animatic_a.mp4`, 480×854, 30 fps, about 50.8 s.
- It is an **animatic**: 8 render samples, low resolution, and rendered **on twos** (every 2nd frame drawn, each shown twice).
- **Do not mark down** noise, grain, aliasing, softness or the steppy 15 fps motion. The approved final is rendered at 1080×1920, 32 samples, on ones.
- **Do judge** everything else: story, staging, acting, camera, continuity, captions, sound sync and pacing. These are what the animatic exists to fix before a 90-minute final render.

## Context
- **Look:** approved by the client in round 1. Judge only regressions against the approved style target (`design/target.png` or the approved proof render) and any earlier round.
- **Script:** client-approved: `script.txt`, one sentence per line. Do not critique the wording; judge whether each sentence's PICTURE reads.
- **Characters:**
  - the recruit (navy kepi, yellow band, red sash);
  - two old hands (moustaches; one in a green forage cap, one in a navy kepi);
  - the cook (toque, apron, handlebar moustache).
- **Beat list:** `renders/gate3/beats_camp.txt`, `beats_cupboard.txt`, `beats_museum.txt` (frame number and beat name).
- **Word timings:** `voice/lines_v3.txt` (frame of every word).
- **Sound cues:** `sfx/cues.json`. The cue anchors are explained in `finish_generic.py`.

**The client's round-1 notes**, which this round must fix:
1. "the script is hard to follow… very jarring when listening": rewritten (v3).
2. "Ricks clips contained dynamic camera moves whilst ours are quite stagnant": the camera is now one continuous move per set.
3. "Voice feels a little radio staticy": re-voiced without time-stretch or pitch-shift; the character line uses a second voice.

**The round-1 critic's top-5 fixes** are in `critic/critique-r1.md`. Check each one is resolved:
- the rifle butt hits the cracker;
- no blocked or cropped framings;
- hands perform the actions;
- SFX on the hits;
- an energetic, warm ending that loops.

## Method (tools: the kit's Python has cv2, numpy and PIL: `~/.make-short/venv/bin/python3` on a Mac, `python3` on Windows; `ffmpeg` is on PATH)
1. **Frames and sheets.**
   - Extract 2 fps frames into `critic/r2/frames/`.
   - Make contact sheets of 12–16 frames into `critic/r2/sheets/`.
   - Look at every sheet, then at single frames where something seems off. Put anything you check closely in `critic/r2/full/`.
2. **Camera dynamism vs the reference.**
   - The reference grammar (measured on the reference Shorts):
     - never still: median 11 px/frame at 1080 wide;
     - a big move about every 2.3 s, landing on sentence starts;
     - slams that brake hard into a creep;
     - 2–3 hard cuts at most.
   - Measure ours with `python3 tools/camstats.py out/<animatic>.mp4 --twos`. The reference makes a big move about every 1.4 s on this meter; a film the client called "stagnant" made one every 4.8 s.
   - Report:
     - our median px/frame;
     - the % of near-still frames (under 1 px/frame);
     - the number of big moves;
     - whether they land on sentence starts (compare with `voice/lines_v3.txt`).
3. **Sound, in data form.**
   - Measure loudness with ebur128.
   - Check whether the voice has any static, crackle or warble. Look at the spectrum and the noise floor in pauses of `voice/voice.wav`.
   - Check that every SFX lands on its visual hit. Find the hit frames in the picture and compare them with the cue times.
   - Check the captions against the words.
4. **Score each criterion 0–10**, with one sentence of evidence that cites frames.

| # | Criterion |
|---|---|
| 1 | Look vs target (regressions only; ignore animatic noise/softness) |
| 2 | Character fidelity vs the sheets in `design/*_view.png` |
| 3 | Acting: expressions on the right beats, hands DO the actions (smash, bite, grab, dunk, skim, offer, lift, hug, press, rap) |
| 4 | Camera: dynamic like the reference, purposeful landings, nothing blocked, empty or cropped |
| 5 | Story readability: each sentence's picture reads on its own, with the props carrying the facts |
| 6 | Continuity: no popping, floating or teleporting visible on screen; hidden swaps really are hidden; no clipping |
| 7 | Captions: readable, in sync, never over a face or the key prop |
| 8 | Audio: clean voice, music ducked, SFX on the hits, about −14 LUFS |
| 9 | Pacing, hook and loop: the first 2 s stop a scroller; the last frame flows back into frame 1 |

## Output: `critic/critique-r2.md`
- The score table and the mean.
- A checklist marking each of the client's 3 notes and the r1 top-5 as FIXED, PARTLY or NOT, with frame evidence.
- **The top 6 fixes ranked by impact.** Each names a frame range, what is wrong (seen in a frame you looked at), and the concrete change.
  - The builder works in Blender Python. Changes such as "camera lands 6 frames later", "hold the cracker 10 cm lower" or "lift captions for f415–476" are ideal.
- Keep it under 1,000 words. Verify every claim on an actual frame before writing it.
