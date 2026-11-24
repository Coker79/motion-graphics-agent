# Lessons (v4): binding

Read this before writing a film script and before every fix round. Each lesson was paid for with a wasted render.

## Look

1. Colour management is **Khronos PBR Neutral**. AgX washes the stylised palette out until the sky reads teal-grey.
2. Depth haze must **mask the sky** using the Depth pass, or the whole sky goes grey.
3. Sun beams are made **from the sky only**. A bright yellow coat fed into the beams smears glow over the legs.
4. Matte materials with painterly dabs (`paint` 0.06–0.18). Glossy coats look like vinyl toys.
5. Light: a warm sun from the camera-left front, a cool fill, a warm rim. Background DOF at f/2–2.8.
   - Keep the sun SOFT: angle about 14°, fill about 230 W.
   - A 3° sun throws crisp brim and prop shadows across white egg heads, and in close-ups they read as glossy porcelain.
   - Skin is matte (rough 0.92, specular 0.06, no SSS). Eye whites get a little emission so they stay crisp white.

## Characters and faces

6. A face is shape-keyed decals wrapped onto a hidden **proxy** of the head.
   - Never wrap onto a mesh that carries an outline shell. With BACK culling the ray stops at the shell and every vertex misses.
   - Build the proxy before any decal, moustaches included.
7. Blender 5 creates new shape keys at value **1.0**. Set 0, or every shape sums (the "beak" face).
8. Decal strips need row subdivisions (chords ≤ 4.5 mm), or their middles sink into the head.
9. An eye is the OPEN area; lids are part of its shape. Lid lines and skin covers sit above the pupil, so closed eyes are one clean stroke.
10. Hats are fitted to the head implicit at their real height (`_fit`).
    - A drum crown must clear the head top.
    - Objects whose geometry sits away from the hat frame need their offset baked into the mesh data before `_place` (toque puff, forage crown).
11. Measure the Higgsfield sheet's FRONT view on a pixel grid (`tools/grid.py`): head width = W, then the eyes, brows, mouth and hat band in W.
    - Heads drawn as tall eggs need h ≈ 1.2 w.
    - Render the turnaround next to the sheet (`tools/compare.py`) and fix until it matches.

12a. Decals drawn on a deforming body (apron, seam) ride the CHEST BONE; `rig.build` does this. Parented to the body object, they keep projecting along the body's rest axis, and an apron slides round to the character's side whenever the root yaws.
12b. Shape-keyed props: set the mesh to the BASIS shape before `shape_key_add('Basis')`. Editing vertices afterwards changes nothing that renders (the cloth that never covered the loaf).

## Rig and acting

12. Hand targets are a direction from the shoulder plus reach, not offsets. Raw offsets fall out of reach and the arm points sideways.
13. `pose()` keys the head too. Pass `skip=('head',)` while `look()` is aiming the head, or the head snaps back mid-shot.
14. Turning round: give the root target as `deg ± 360` so the body goes the short way, toward where the head looks. Add a `hop()` with lifting feet, or it spins on the spot.
15. Key set-up poses BEFORE frame 1 (negative frames). Keys between frames 0 and 1 motion-blur the first frame.

## Cutting

16. Every cut is a jump with keys at f−0.6 and f−0.5, CONSTANT in between, for characters, camera and lights.
    - The pre-cut key must be the ANIMATED value (`film.value_at`), not whatever Python last wrote.
    - `frame_set()` calls made to place props overwrite pose properties, and characters then drift between shots.
17. Park every character that isn't in a shot (`PARK` + `snap`). Idle characters standing in the camera line is the most common broken gate still.
18. Walks key every frame. Never `snap` the same character inside its walk range, and end walks before that character's next shot.
19. 9:16 is narrow. Depth-stage two-shots (one near and one far, or over the shoulder) instead of side by side.
    - Framing presets are measured from the face surface.
    - An "ECU" shorter than 0.5 m is one eye.
20. Hand-held display props use `follow_rot=False`, or they turn edge-on as the hand rotates (the "duck bill").
21. `vis()` must cover children: crate contents do not inherit `hide_render`, so they float at the hand.

## Sound and voice

22. **Never time-stretch or pitch-shift the narration.** In v1, `atempo` 1.18 plus an `asetrate` pitch shift made the voice "radio staticy" (client note), although the raw take was clean (noise floor about −92 dB).
    - Get the speed from the engine: Seed Audio `speech_rate` 40–50, at 48 kHz.
    - Get the pace by editing only the pauses: `voice/pace.py`, with sentence gaps of about 0.42 s, a 0.32 s cap inside sentences, and `--hold` for story beats.
    - The formula pace is 3.3–3.7 words/s.
    - Then run Whisper again and `voice/onsets.py`. Whisper starts some words inside the pause before them (one "But" sat 0.7 s early), and cues, camera moves and captions all land on those word times.
    - A take can begin with a junk fragment (one began with "of an eye."). `pace.py --script` drops it.
23. A character's line is a **second preset voice**, never the narrator pitched up. Hardtack used Fraser, the deepest at about 92 Hz.
    - Generate the quote alone and silence-trim it.
    - `pace.py --quote quote.wav --after "laughed,"` drops it into the pause after the narrator's lead-in (0.30 s before, 0.40 s after).
24. Mirelo SFX shorter than about 1.5 s often come back silent.
    - Generate at 2 s.
    - Check every file's `max_volume`; replace any that are silent with a similar sound.
    - Do NOT rely on peak normalisation for level: `finish.py` loudness-matches every file (lesson 58).

25a. SFX files start with silence (Mirelo: 0.3–0.5 s). `finish.py` trims every one-shot's leading silence, so a cue lands ON its frame.
    - Swells (whooshes) are cued by their PEAK on the cut.
    - Missing sounds get noticed: give laughs, rustles, clacks and hisses their own cues.
25b. No music fade at the end: the Short loops. Lift captions (`capUp`) wherever the key prop sits in the caption band.

## Process
0. zsh doesn't word-split `$VAR` (use `${=VAR}`), and an empty glob aborts the whole `&&` chain. Write loops accordingly.

25. Gate before the full render: `film.py SET dir beats --preview` gives one still per beat in about 1.5 s each. Look at every still. Expect two or three fix rounds on a new film.
26. `render.sh` runs three Blender workers at 16 samples (A/B'd against 32: indistinguishable). Quote the time measured on this machine, which `render.sh` prints, and not an old figure.
27. The script gets an independent critic (rubric in `script-formula.md`, pass at 8.5 or more). Builders score themselves about 2 points too high.

## v4.1 (hardtack round 2): binding

28. **Animatic before the full render.**
    - `bash animatic.sh NAME "SET ..."` renders 480×854 at 8 samples, on twos, with the full mix: about 12 min for 50 s on an M1 Pro with 3 workers.
    - The independent critic reviews the animatic first, then the user. Fixes re-render only the changed ranges.
    - The 1080p final (50–90 min; measured figures in `render.sh`'s header) is rendered ONCE, after sign-off.
29. **Hands follow props, not the other way round.**
    - Key the prop in world space, put `props.grip()` on it, and attach the hand with `props.follow()`.
    - The rifle butt then lands ON the cracker, the cracker edge sits in the teeth, and the spoon bowl skims the coffee.
    - Posed hands plus ChildOf props miss by centimetres, which is everything in a macro.
30. **Never read pose values from Python after a `frame_set()`.**
    - `hand_point`, `hold`, `at()` and the framing report all evaluate frames; afterwards the Python values hold whatever frame was evaluated last.
    - `turn_body` now reads the animation (`value_at`), and any new rig helper must too.
    - Symptom: a character slowly slides back toward an old position across a whole act.
31. **Run the framing report before rendering any still.** `film.py SET dir report` prints where each beat's subjects sit (0–1, or OUT). In seconds it caught:
    - a 1.3 m character drift;
    - a camera aim that overshot after big whips;
    - a prop held outside an MCU.
32. **Swaps hide inside whips.**
    - That covers dusk lighting, teleports, and a held prop swapped for an identical resting copy.
    - Key them in the first 2 frames of a slam or whip (EXPO ease-out is fastest at the start), when the old and new spots are both off screen.
    - Hand follows must blend out BEFORE a teleport, or the arms stretch across the set for a frame.
33. **Rifles and other flat props show their PROFILE to the camera.**
    - Spin them 90° about the long axis (`rotation_mode = 'ZXY'`).
    - A raised rifle tilts AWAY from the camera's side, so the barrel sits beside the head and never across the face. Shoot the strike from the striker's other side.
34. **Things that grow (steam) need their origin at the base** (`base_origin`), or the scale keys pull them into the ground. That is v1's "white scribble on the grass".
35. **Seeds must be the same in every process:** `sum(map(ord, name))`, never `hash(name)`. Python randomises string hashes per process, so two render workers blinked differently.
36. **Small props need contrast with what they sit on.**
    - Dark weevils vanished on black coffee; milky coffee (`#7A4A28`) made them read.
    - Clear glass at alpha 0.1 or more veils everything behind it grey; use 0.035–0.06.
37. **Keep the shot clean.** A prop a later beat needs (the ration box) appears when the camera is elsewhere, not in the hook's frame.
38. **Sets join inside one whip.** The outgoing set `exit()`s still at full speed on its last frame, and the next set `start()`s mid-whip panning the same way. Mark the join with a whoosh riser cued so its PEAK lands on the join (Mirelo's whoosh peaks 1.74 s after onset).
39. **A fire or oven mouth is a glow gradient,** hot orange at the bottom and fading to near-black at the top. Use an emission colour ramp on the Generated coordinates. A flat emissive disc read as a big red sticker, and cone "flames" read as triangles. The dark top also gives steam something to read against.
40. **Measure the camera like the reference** with `tools/camstats.py film.mp4 [--twos]`.
    - Measured on this meter:
      - the reference: a big move every 1.4 s;
      - v1 (called "stagnant"): one every 4.8 s, mean 1.5 px/frame;
      - round 2: one every 2.7 s, mean 3.5 px/frame (the reference's mean is 3.7).
    - The reference on this meter: median 0.3, mean 3.7 px/frame, 74% "still", a big move every 1.4 s.
    - Push-ins register only partly, so the big-move count is the number to watch, never the still %. refstats-style feature displacement reports about 11 px and 6% still for the same reference. Don't mix the two yardsticks.
41. **The creep is a slow DOLLY-IN toward the subject:** `creep` × the shot distance per 45 frames (0.14 in the camp), plus a little drift. The v4.0 creep only continued the last move and capped at a few cm. The critic measured 28–50 f near-still holds between moves; the reference never holds more than 25 f. Long holds also get an `orbit_from()` (an arc that starts exactly where the last move landed).
42. **A container's visibility must not override its contents:** `vis(box, ..., kids=False)`. Keying the box recursively made its ration crackers visible from frame 129, hovering 0.75 m up before their drop.
43. **Captions move per SHOT, never per word.** Keep one `capUp` window for a whole shot; 8 band jumps read as jitter. Clamp the first card to frame 1, because a word starting at t = 0 computes as frame −1 and misses its lift. When a prop or chin sits in the band (y 0.73–0.80), reframe the shot (aim lower) rather than dropping captions into the Shorts UI zone.
44. **The loop seam needs sound.**
    - Trim the music's silent head (`music.head`) and drop its fade-in (`fade_in: 0`).
    - Land its final downbeat on the last story beat (`music.land`, a few % of tempo).
    - Brighten the last set so frame 1 → frame N doesn't jump in luma (the museum was 25 vs the camp's 44).
45. **Reactions must not read as anger.** In this face kit `pain` reads as angry (two critics flagged it). Use `sad` plus a downward gaze for hurt or disgust.
46. **An orbit must start exactly where the camera is.** Three orbits started 4–18 cm away from the previous landing, or 4° the wrong way. The client caught the first as "the camera movement shifts abruptly" at 2 s. `CamPath.orbit` now reads its start azimuth, radius, height, aim and lens from the last key and blends to the target, with keys every 2 frames.
    - Before the final, run `film.py SET dir campath:a-b` for every set. It prints per-frame camera speed, turn and jerk.
    - Then check: every speed jump must be an intended slam or whip on a sentence start, and there must be NO reversal at speed. The check is in `example-hardtack` as a short Python scan.

## v4.2 (the Dutch-flood cold test): binding

47. **Toy scale.** A character is about 1.2 m, with the hip at 0.35 m, arms 0.31 m and a reach of about 0.43 m. Every real measure a character touches gets converted. The facts said 40 cm of "knee-deep" water, which is waist-deep on a toy, so the film used 0.20 m. The sluice wheel shrank to 0.24 m radius at chest height, or the hand can't reach the knob.
48. **`W()` searches the whole film.** In any later set, pass `after=(F0 - 1) / 30.0`. In the bank set, `W('reached')` found line 5's "reached the cows' knees", so the general's walk ran from frame 1018 back to 509: zero frames and no error, just an empty gate still. `walk()` now raises on that.
49. **Ground height.** Characters stand at z = 0 (the root's z is forced). On a dike or bank, lift the armature (`A.arm.location.z`), give `framing()` the lift, and keep walks on flat ground.
50. **Decals spike near the head's outline.** `face.decal` projects along +Y; a vertex within about 0.1 W of the silhouette grazes the surface, the fallback snaps it elsewhere, and solidify extrudes a spike through the hat. Keep moustache spans at 0.66 W or less. The beard is fitted analytically to the egg head instead (`_beard`).
51. **A moving subject needs a travelling camera.** A single push to "where he'll be" leads or lags an eased walk: the march MCU lost the general. Chain short pushes onto the bone's real position every 6 frames.
52. **Whisper drops words on long takes.** Check `narr.json` against the script before pacing. Two missing words ("drowned field") turned a sentence pause into a comma pause, and the farmer's quote would never have been inserted.
53. **Rotate a whole character by its root BONE, never its armature object.** The armature's origin is at the world origin, so pitching it swings the character in a 4 m arc. The belly flop is `A.key(f, 'root', loc=..., rot=(84, 0, yaw))`.
54. **Shallow water** is a BLENDED mix of a pale Transparent BSDF and a glossy Principled, driven by Layer Weight "Facing": the drowned grass shows near the camera and the sky reflects at grazing angles. Opaque water reads as a swimming pool; refraction reads as murk. Reeds and grass poking through are what say "shallow" from far away.
55. **Register a beat at the PEAK of every key action, not only at camera landings.** The first Dutch-flood animatic scored 5.1. Its top failures were all motion: a wheel turning with the hands below it, feet walking ON the water, the actor who should vanish hidden behind another, a boat floating over its carriers. Landing stills passed every one of them.
56. **A slow creep is still on screen.** `CamPath(creep=0.14)` plus S-curve pushes gave one big move only every 2.5 s, at a median of 0.1 px/frame. The critic read that as a still camera. The fix:
    - use creep 0.2 or more;
    - put an `orbit_from()` on every hold longer than 1.5 s;
    - run `tools/camstats.py out/animatic.mp4 --twos` before the critic sees it.

    Aim for a big move every 2 s or less, at a mean of about 3–6 px/frame. Do NOT target camstats' "still %": phase correlation can't see push-ins or creeps, so the RicksClips reference itself reads 74% still and Matt's approved Hardtack final 80% (lesson 40).
57. **The last set must not relight unless frame 1 does too.** A 'day' preset whose sky ramp differed from the default made the loop seam jump. Also land the last camera key on frame 1's exact transform 2 frames early, and hold it.
58. **Nothing overpowers the voice: measured, every mix.** The client: "at times, the water is so loud that you can't hear the voice over… prevent this from ever happening again." The cause was peak-normalising: a 2 s burst of water noise at −2 dBFS peak is far louder to the ear than speech at −18 LUFS. Only the music was ducked; the SFX never were. `finish.py` (v2) now:
    - loudness-matches every SFX (−27 LUFS) and ambience (−33 LUFS) before its cue volume;
    - smooths each one-shot (15 ms fade-in, 350 ms fade-out, 60 Hz–9 kHz);
    - sidechain-ducks the SFX bus AND the music under the voice;
    - gates the mix in 400 ms windows where the voice really speaks. The SFX alone must stay at least 10 dB under it (strict minimum), and music + SFX at least 8 dB under it (2nd percentile). It lowers whichever stem is at fault, rebuilds, and prints the margins.

    In the Dutch-flood test the gate found the MUSIC was the bigger offender (it needed 4.3 dB less). Tune with `sfx_margin`, `vo_margin`, `sfx_lufs`, `amb_lufs`, `sfx_gain_db` and `music_gain_db` in `cues.json`.
59. **Stills can't see motion: review every 480p render as MOTION, independently, before the user does.** The Dutch-flood animatic passed its framing reports, its landing stills and a 2 fps critic. The client still saw that "some scenes don't animate properly… at 13 seconds, the water animation is very rudimentary": a flat plane rising evenly, and a texture sliding over a static sheet. Two things fix that:
    - `tools/motion_strips.py` (per-line strips at 6 fps) plus an independent motion reviewer (`critic-brief-motion.md`) whose pass bar is 7/10 per line;
    - effects built to MOVE. Use the kit's moving water (`toykit-api.md` § moving water):
      - `world.spread_mat` is a front spreading from where the water lands (a keyed REVEAL radius with a noisy foam band). Shrink it to drain;
      - `world.pour`, `churn` and `boil` give a churning tongue with white water boiling where it lands;
      - `world.spray` throws droplets only;
      - `world.ripple` is a soft fading ring, for steps and floating things;
      - `world.flow_water` makes the surface move.
    The animatic's motion review scored 4.9/10 on these grounds, with 13 of 15 lines under 7.
60. **A still body reads as frozen, however good the keyed acting.** In the motion review, characters were "frozen bar eyes and mouth" for 1–3 s on 6 lines. Two causes:
    - `breathe()` scales the chest by only 1.2%;
    - poses hold dead still between keys.

    The fix: the example `film.py` runs `alive()` over every cast member (cast registers them in `ACTORS`). It puts slow F-curve NOISE modifiers on head nod/turn/tilt, chest lean/sway and a hip weight shift, at about ±2–3°. That sits on top of the keyed acting without fighting it. On a looping Short, keep the noise off the loop frames with `frame_start`/`frame_end` and `blend_in`/`blend_out`. Then give each phrase a pose change of its own: fists on hips, a laugh with shaking shoulders, a head shake, a point, a shrug. A pose held over several words reads as a freeze.
61. **The camera can sit INSIDE a character, and nothing flagged it.** A sock close-up in the end set orbited 2 m from its aim, which put the camera 0.17 m from a soldier standing in the row behind it. A full second rendered as uniform teal, which the reviewer took for a "featureless flight". The `campath:a-b` mode now prints `NEAR` whenever the camera comes within 0.45 m of any character's head, chest or hips, and `campath_scan.py` counts each one as a flag. Two related traps:
    - **Long whips are one smeared frame.** A whip/slam is EXPO: about 75% of the move happens in its first frame, so a 30 m whip renders as one blurred frame on twos. A flight that must read is a `push` (S-curve) of 8–12 frames, with a short shutter (key `scene.render.motion_blur_shutter` to about 0.18) and things to fly past (reeds).
    - **Keys out of order.** An orbit that ends after the next whip's start (`orbit_from(..., F1 - 10)` before a whip that starts at F1 - 12) puts keys out of order. Always end the orbit before `f - dur` of the next move.
62. **A hand that follows a prop keeps following it.** `props.follow(..., f_off=)` is optional. Without it, the two boat carriers' hands stayed locked to the rowboat's grips after the boat was hidden. In the next line their IK arms stretched 4 m across a wading shot as a "soft dark mass". Every `follow` gets an `f_off` at the moment the prop leaves. Likewise, an unscoped `W('word')` silently takes the word's FIRST line in the whole film: the farmer's "then at the keeper" gesture landed on line 1's "French army". `Timing.word` now prints `TIMING WARNING` when an unscoped word is in several lines. Read every warning: when the line it names isn't the one you mean, scope the call with `after=` (lesson 48).
63. **What round 2 of the motion review taught (Dutch flood, 4.9 → 5.5).**
    - **From above, only the outline reads.** Normal displacement and a scrolling texture leave a top-down gush a "straight-edged slab". Wobble it SIDEWAYS (a second Displace along X) and tear its edges with an evolving 4D noise; `world.churn` does both.
    - **An action on the far side of a prop is no action.** The rower prodded with the hidden oar. Put the action on the camera side and make it big (half-stand, a 30° chest swing).
    - **A change hidden in the whip blur never happened.** The water "climbed" during the whip that landed on the post. Start the change after the landing and finish it ON the word ("mark").
    - **A low sun on glassy water is a white blob** that slides as the camera orbits. Set the sun's `specular_factor` to 0 for dusk and low-sun shots over water.
    - **A prop needs contrast against the costume.** A grey sock on a grey-white coat can't be wrung on screen. Use a dark wet sock at 1.45×, a 0.4 s counter-twist, and a chest that pumps with it.
    - **Tracking a runner against a plain sea reads as running on the spot.** Release the track and let him cross the frame.
    - **A bodily move that loops reads as life:** a chest pump with each twist, a bob with each wading step, a heave on each push. A held pose with noise on top still reads as "frozen" at 480p.
64. **Round 3 of the motion review (C2: 5.9 mean; the 13 s gush still scored 3).**
    - **Show the cause.** The pour was filmed from behind the dike, so the arch it bursts from was out of frame and the water read as a slab sliding over grass. The same water filmed from the FIELD side (the arch, the burst, the pool racing toward camera, the keeper cranking above) read at once. Frame every effect with its source.
    - **Turn about the right axis.** Rotating the oar about its own length axis (X) only twisted it, so the blade never touched the water. A dip is a pitch about Y. Check a frame before trusting an animated axis.
    - **Strength in screen pixels.** A 0.3 lateral wobble moved the gush's edge about 6 px at 480p. Size effects in pixels at the shot's distance (±0.3 m ≈ 35 px at 10 m).
    - **A held lean dies under a walk cycle.** Use the additive `lean()`.
    - **Chained follows leak the rest pose** unless they overlap (`toykit-api.md`).
    - **Colour against colour.** A navy sock in navy hands vanished as surely as a grey sock on a grey coat. Pick a colour that contrasts with BOTH the costume and the hands (a red sock), and twist the prop itself with a keyed SIMPLE_DEFORM.
    - **Place props off world features.** A cow at x = 7.0 stood IN a ditch, so under the flood only its face showed: a "ghost cow". Check the terrain height under anything you place on a ditched or uneven set.
    - **Streaks need distance.** Droplets stretched 2.6× read as white sticks right in front of a low lens. Scale spray size and stretch to the camera's distance.

## v4.3 (the Dutch-flood FINAL: what the 1080p render and the final critic found)

65. **The SFX bus can play seconds early, and nothing noticed.** `amix` starts its output at its FIRST input's first timestamp, and a WAV keeps no start offset. With the first cue at f74, the whole SFX and ambience bus played 2.43 s (73 frames) early, and the cues before f74 were lost.
    - It went unnoticed through mix v2, three animatics and the client's "sound is good". The level gate measured the shifted bus, and the motion reviews judged pictures.
    - The final critic found it by checking SFX sync against the cue sheet. A 61.4 s film had a 58.97 s SFX stem.
    - `finish.py` now pins the bus with a silent full-length first input, and refuses any stem that isn't the film's length.
66. **Generated one-shots hide their hit late in the file.** Mirelo's clunk, splash and scrape hit 1.0–1.5 s into their 2 s files. Their leads ran at about −36 dB, too loud for `silenceremove`'s −40 dB, so every hit landed 30–45 frames after its beat.
    - `finish.py`'s `lead()` finds the hit: the first 10 ms within 10 dB of the file's loudest 10 ms.
    - A file whose hit sits more than 0.3 s in is trimmed so the hit lands on its cue.
    - Whooshes are exempt, because their build-up is the sound, and their cues are already set 6–8 frames early.
67. **One loud cue set the level for every hit.** The SFX gate is a strict minimum, so lowering the whole bus to fix the gush's worst window left every other hit 30–50 dB under the voice: inaudible.
    - The gate now lowers only the cues sounding in a failing window.
    - The SFX duck is gentle (2:1 above −20 dBFS); the measured gate is the guarantee.
    - Result: impacts in pauses sit 5–7 dB under the voice, cues under speech 12–23 dB, and every spoken window still has at least 10 dB of voice over SFX.
68. **The first frame of every whip was a ghost.** With one motion-blur step, EEVEE renders a single vector blur. A frame whose shutter straddles a whip's START (the camera still for half the shutter, then about 75% of the move) rendered as a double exposure with 8–16 px tile blocks.
    - The Dutch flood had 30 such frames, and the 480p animatic hid them.
    - 16 steps turned the blocks into a staircase of 8 stepped copies, and a bigger `motion_blur_max` didn't join them.
    - 64 steps gives a smooth smear, at about 4× the time on those frames only.
    - `setup_render` now defaults to 16 steps: no time cost, and ordinary frames change by less than one level.
    - The example `film.py` renders `P.move_starts()` (each slam/whip start frame) at 64 via `render_range(..., mb_steps=...)`. That adds about 7% to a final.
69. **Hide set changes in the whip's biggest smear, never near its landing.** `whip(f, dur)` starts at `f - dur`, and its EXPO puts about 75% of the move into frame `f - dur + 1`. Four frames before the landing, the camera has nearly stopped.
    - The night relight, the farmer's teleport and his lantern were keyed at `S(8) - 2`. They popped on screen at the landing.
    - The farmer's key light went off two frames BEFORE the whip, darkening him on camera.
    - Key every hidden change at `f - dur + 1`, between shutters (relight already keys `f - 0.6`/`f - 0.5`). Keep the leaving set's lights on until then.
    - Compute the frame from the whip call, never from the line start.
70. **A blended effect just above a thin blended plane draws UNDER it.** EEVEE sorts blended objects per object, not per pixel. The hook's gush tail lay 1–17 cm above a 3 cm flood plane. The flood painted over the tail everywhere except where grass blades blocked it, leaving a hard white strip on every blade.
    - Two motion reviews saw "white strips under the grass" and guessed a foam mask; nobody tested it.
    - Find the culprit by removing candidates one at a time and re-rendering one frame, about 20 s each (`tools/dbg_render.py`, e.g. `TK_DBG='unlink:gush'`).
    - A world-height cut failed, because the churn lifts the tail to 0.3 m. Fix: `world.sink_under_front` hides the tongue from v 0.25 to just past the front's edge, keyed per frame. The tongue ahead of the front stays, so the white water still races over dry grass.
71. **What the 1080p final shows that the 480p animatic hides:**
    - whip-start ghosts (lesson 68);
    - set changes that pop after a whip (lesson 69);
    - effects bleeding through grass (lesson 70);
    - off-sheet character details. The farmer's sideburns stuck out as horns at eye level, and his brown apron read as orange fur under the dusk key light.
    
    Catch the last kind at the cast gate: compare the turnaround to the sheet part by part, under the film's own lighting. Leave time after the final for the independent critic, plus one targeted re-render (`film.py SET renders/final a,b,c` with the fixed frames).

## 2.2.0-rc3: the pineapple pit (a parent-approved run; the client's notes typed live)
72. **A move that starts inside the previous move's window silently collapses.** `slam(f, dur)` starts at `f - dur` from the previous call's last key. If that key is later (a push ending inside the whip's window), the whip shrinks: on the pineapple pit, two 9-frame whips became 2-frame POPS (97% of the move in one frame), the client's "rough" moves.
    - `campath_scan` could not see it: the jump sits inside a planned window.
    - CamPath now prints `CAMWARN` when a move starts late, and `campath_scan` flags any slam/whip window of 4 frames or less (`COLLAPSED`).
    - End every push and orbit AT the next move's `f - dur`. Run the scan on EVERY animatic.
73. **CamPath calls out of time order snap the camera back.** A move takes its start pose from the previously CALLED move. Coding a creep after the whip that follows it made the camera whip, snap back, and whip again: "at 0:36 it seems like there is a repeat". CamPath now warns; `campath_scan` shows it as a REVERSAL at speed.
74. **A vector-math node's Vector output is (0,0,0) for DISTANCE, LENGTH and DOT_PRODUCT.** A helper that returned `outputs[0]` for every op made a near-lens fade scale every snowflake to 0 and every steam puff's alpha to 0. Two gates and two animatics went out with no steam (the film's thesis) and no snow. The same bug pushed a smoke fill outside its room.
    - Scalar ops return `outputs['Value']` (`fx._vmath`).
    - After ANY change to an effect's node tree, render one still where the effect is the subject and compare it with the last approved one.
75. **Compare sharpness against the last approved cut after every `--only` round.** A camera change made to clear a `NEAR` flag parked the lens against a wall: 0.7 s of full-frame defocus at the hook (Laplacian variance 347 → 103), missed for two rounds. `tools/sharpcheck.py REF.mp4 NEW.mp4` flags runs of 6+ frames under 40% of the reference.
76. **Smoke that reads as smoke (EEVEE):** `fx.smoke_fill(volume=True)` (Points to Volume) with `fx.smoke_vol_mat2`:
    - charcoal scatter (about 0.03), black absorption, density about 26;
    - high-detail 4D noise times a noise-broken falloff over the top 30% under the roof, so the top billows;
    - `volume_factor = 0` on EVERY lamp while it should read black;
    - check the GLASS in front of it: a frost or snow film on the panes, lit from inside, read as a flat beige box over black smoke. Melt it when the room heats, and test once with the panes removed (`dbg_render.py unlink:`).
77. **The voice gate is per window, and the duck should look ahead.**
    - `vo_min` in cues.json dips the music only around each spoken window that falls short (smooth 0.25 s ramps), instead of lowering the whole bed.
    - A 20 ms sidechain attack chopped the bed by 15 dB at a speech onset: use 60 ms, and lead the key by 80 ms (`duck_lead`), so the bed clears in the pause before the word.
78. **A toy's held-out hand sits at table height.** At shoulder height the merchant's palm sat inside the tablecloth, so the coin "landed" in the cloth. Raise the hand's direction (z about 0.5) over a table. Key a held or landed prop on the hand EVERY frame, AFTER `alive()` adds its noise, or it floats through the holder's hop and sway.
79. **Polished metal props mirror the room.** An emissive, rough-0.16 gold coin blew out white at phone size. What read as a coin: a deeper gold base (#B98A28), roughness about 0.35, a raised rim (`props.coin(..., rim=True)`), and a glint lamp OFF the face's mirror line, so only the curved rim catches it. Focus the close-up on the prop, at f/4.
80. **A view-transform change outlives its shot.** A +0.5 exposure lift for a moonlit wide also burned out the stove close-ups after it. End exposure and look changes inside the next whip's first smear, like set changes (lesson 69).
81. **Foreground snow needs its own emitter along the camera path.** Set-wide 9 mm flakes read as specks. 26 mm flakes (520 in a box around the push, on only for that shot) read as a snowstorm at phone size.
82. **A crashed chunk becomes a frozen shot.** Blender 5.2's shrinkwrap BVH build races in parallel evaluation and can kill a worker. `fill_twos` then doubles the last good frame over the gap. After every render, list the missing frames and re-render only those.
83. **A step key that stores the property "as found" ramps the curve toward a stale value.** A hand-written `set_prop(o, 'amp', f, 0)` keyed `o['amp']` at f−0.6. That held the value left by the last `frame_set()` (1.0 from another shot), not the curve's 0.06, so the house smoke climbed from 0.06 at dawn to 1.0 over 250 frames. The dawn shot on "smoke had killed half his plants" went to murk, and the dead plants vanished.
    - **Key the curve's evaluated value**, not the property as found. Use `film.step_prop(o, prop, f, v)` / `film.step_socket(sock, f, v)` (rc3): they key `fcurve.evaluate(f - 0.6)` (via `value_at`) at f−0.6. `jump_obj` does too now. The alternative is an explicit hold key at the previous value, right where the hold should end.
    - **Preview every frame a late change's curves reach, not just its own shot.** The key sat at f1378, but the curve it changed runs from the previous key (the dawn switch, f1131). My 6 fps check strip covered only f1374–1432 and looked right. Before the final, list each changed curve's span (previous key to new key) and strip or re-render all of it.
    - **Run `sharpcheck.py` on the final against the last animatic.** Lesson 75 covers `--only` rounds; this diff is what caught the dark shot (f1172–1181: 333 → 101), after the last animatic and before anyone watched it closely.
84. **19-20 h for one Short is not sustainable; make the first version as good as possible** (2.3.0, the pineapple pit's clock: 19 h 42 min). Where the time went, and what replaced it:
    - **Script, about 11 h.** v6–v7 spent about 4 h re-scoring for a cold listener stuck at 7/10; the fix that mattered (the smoke twist) came from a note at GATE 1. Now: one critic and one listener in parallel, ONE rewrite, then the user with both reports (SKILL §1.6).
    - **Approval waits, about 3½ h.** A gate reply sent to a busy session waited until its turn ended, overnight. Now: delegated approvals happen inside the session that makes the film, with a fresh approver subagent (SKILL §6.5).
    - **Previews, about 4¾ h for eight cuts.** Two were thrown away before anyone reviewed them, and three rounds chased bugs that the automatic checks now catch (zero-scale steam and snow, collapsed whips, a defocused hook). Now: exactly three planned previews, P1 → P2 → P3, and never the next one before the last one's reviews are in (SKILL §6).
    - **After the 1080p, about 40 min plus fixes.** The critic pass on the 1080p film moved to P3, a 480p preview rendered on ones (`animatic.sh --ones`), which shows the faults twos hide. After the one 1080p render only the automatic checks run, then the user chooses: ship as is, critic review only, or critic + one fix pass (SKILL §7).

**From the beehive Short (2.3.0):**

85. **An orbit keyed every other frame stutters mid-arc.** `CamPath.orbit` keyed every ~2 frames on rounded frame numbers, which left uneven 3-frame gaps. It now keys every frame.
86. **The render is GPU-bound.** On an M1 Pro, 3 workers at 18 s a frame render about as fast as 1 worker at 5.5 s a frame, and motion-blur steps dominate: 8 → 2 steps took 5.5 → 3 s a frame. The 61 s beehive P1 on twos took 1 h 50 min, not 15-20 min. Render P1 and P2 with `TK_MB_STEPS=2`, and quote P3 and the final from a measured 3-frame test.
87. **9:16 needs wider shots than they look.** FRAMING sizes are vertical metres: a 0.42 m toy head needs about 1.1 m of frame to clear the button stack. Step every character shot one size wider than the kit default.
88. **Fast moves ghost under EEVEE's stepped motion blur.** An elephant moving 7 m in 0.7 s, or spinning 270° in 18 frames, showed visible copies. Keep big moves slow.
89. **A prop parented right after it was placed lands at the origin.** `matrix_world` isn't updated until the next view-layer update, so `_parent_to_bone` copied a stale matrix: the farmer's swelling sat at his feet from gate 1. The kit now updates first.
90. **Pausing renders for a recording:** `pkill -STOP` / `pkill -CONT -f "Blender.*film.py"` works within a session, but workers frozen across an app restart or sleep came back stuck at 0% CPU. Kill them and resume with `animatic.sh NAME SETS --only "set:a-b ..."` from each chunk's last saved frame, keeping the chunk's frame parity.
91. **A scripted patch can comment out the code after it.** An inserted string that ended in `# comment`, placed mid-line, swallowed the `;`-chained calls after it (a trunk hold and the scared faces vanished in P2). After any scripted patch, scan film.py's comments for `; name(` before rendering.
92. **`Mesh.transform()` skips shape keys** unless `shape_keys=True`, and a mesh with keys renders from its keys. Re-centring drew every maize row at twice its position from gate 1 to P2 (half-empty fields; the bull "ate" bare dirt). Pass `shape_keys=True`, and probe the evaluated bounding-box centres when a keyed prop looks misplaced.
