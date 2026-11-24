# Motion review brief (independent): run after EVERY 480p animatic, before the user sees it

Template from the Dutch-flood test. Replace the file names: `motion_b` becomes your strip folder, `animatic_b2` your animatic.

You did not build this film. In the Dutch-flood test the client said "some of the scenes don't animate properly… the water animation is very rudimentary". Every still-frame gate had missed it. Your job is to judge MOTION, fairly and strictly, line by line.

## What you get
- `critic/motion_b/L01.png` … `L15.png`: one motion strip per script line, at 6 fps, from the animatic `out/animatic_b2.mp4` (480p, 8 samples, on twos). Every tile carries its frame number (30 fps).
- `script.txt` (one line per strip) and `story.md` (what each line should show).
- The look target: `style/target_look.png`.
- You may cut more frames yourself: `ffmpeg -ss <sec> -i out/animatic_b2.mp4 -frames:v 1 ...`, or a 12 fps strip of a range. Put your files in `critic/motion_b/work/`.

## Ignore
Grain, noise, softness and the steppy 15 fps (the final is 1080p, on ones).

## Judge every line on the motion checklist
1. **Effects move like the real thing.** Water flows, with a spreading front, turbulence, foam and splashes where it hits something. Smoke drifts. Nothing reads as a texture sliding over a static shape, a flat plane rising evenly, or a shape popping in.
2. **Contact.** Feet plant on the ground or the water bottom (no gliding, floating or sinking). Hands are ON the prop they work (the wheel, the boat, the socks).
3. **Acting motion.** Anticipation and follow-through on the key action; no character frozen in frame for more than about 1 s unless the stillness is the joke.
4. **Camera.** The camera shows the action, not the back of a hat. No dead hold over about 1.5 s. Motion blur stays readable.
5. **Placeholder smell.** Anything a viewer would call "rudimentary", "prototype" or "cheap".

## Output: `critic/motion-b.md` (under 900 words)
- A table: line | score 0–10 (motion only) | the one biggest motion defect, with its frame range.
- The PASS bar is 7. List every line under 7.
- For each failing line, give a **concrete fix the builder can code in Blender Python**, ranked by impact. For example: "the flood: a front that spreads from the arch over 2 s with a foam band at its edge, the level rising behind it"; "frame the wheel and his hands, not the back of the hat"; "spray particles where the gush lands, every 4 frames".
- Verify every claim on a real frame.
