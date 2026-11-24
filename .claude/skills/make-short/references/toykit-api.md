# toykit API (v4): what a film script calls

## How the pieces fit

`v4/toykit/` is a Blender 5.2 Python kit. Toy-family characters, a world and a camera are all built from code and rendered in EEVEE.

**Units and orientation.** Everything is in metres with z up. A character faces −Y at yaw 0. Positive yaw turns it toward +X.

**Toy scale (lesson 47).** A character is about 1.2 m tall, with the hip at 0.35 m, arms 0.31 m long and a reach of about 0.43 m (1.4 × the arm). Convert any real measure a character touches.

**Ground (lesson 49).** Characters stand at z = 0: the root bone's z is forced to 0. On a dike or bank, lift the armature object (`A.arm.location.z = h`) and add `h` to `framing()`'s `off`.

**Imports.** A film script imports the modules it needs from `toykit`: `look`, `char`, `rig`, `world`, `props`, `camera` and `film`. `hardtack-v4/film.py` (copied to `v4/example-hardtack/film.py`) is the worked example. Copy its structure.

## look: render settings, materials, grade

| Call | What it does |
|---|---|
| `look.setup_render(sc, w, h, samples, motion_blur, view='Khronos PBR Neutral', exposure=0)` | Sets up EEVEE, ray tracing and colour management. Keep Khronos: AgX washes out stylised colour. Motion blur uses 16 time steps (one per sample below 16; `TK_MB_STEPS` overrides). Render whip-start frames at 64: `film.render_range(sc, OUT, F0, F1, only=frames, mb_steps={f: 64 for f in P.move_starts()})`. With one step, the first frame of every whip was a ghosted double exposure with tile blocks (lesson 68). |
| `look.world_sky(sc, zenith, horizon, ground, strength)` | Gradient sky. Returns the world. Its colour-ramp elements can be keyed (dusk changes). |
| `look.mat(name, rgb, rough, sss, sheen, coat, metal, brush, grain, paint, paint_scale, spec, emission=(rgb, s))` | The house material: Principled base colour × soft brush noise × painterly dabs (`paint` 0.05–0.18) + a grain bump. |
| `look.flat(name, rgb)` | Unlit material (ink, pupils). |
| `look.outline(obj, width, color=None)` | Inverted-hull ink. About 0.004–0.006 m on characters and props, 0.01–0.03 m on trees and buildings. |
| `look.sun(name, rot_deg, energy, color, angle)`, `look.area(...)` | Lights. Day defaults: sun 4.6, fill 160, rim 380. |
| `look.compositor(sc, bloom, warmth, vignette, haze, haze_col, beams, beam_pos, saturation, paint)` | The grade: depth haze (sky masked), sun beams from the sky only, bloom, saturation, a warm balance and a vignette. `paint` is an optional Kuwahara size. |

**Colours** are linear. Write them as `look.hexc('#RRGGBB')`.

## char: a character from a spec JSON

```python
ch = char.Character(spec)
# ch.parts {head, body, sleeveL/R, handL/R, legL/R, bootL/R, hat, brim, ...}
# ch.face (a face.Face)
# ch.spec
```

The spec is listed in full under **Spec reference** at the end of this file. Face, hat and hair values are in units of the head width W, with z measured from the head centre. Body values are in metres.

## face: expressions, gaze, blinks, lip-sync

Acting calls are recorded first and written once at the end with `face.bake()`. Call `bake()` once per character, after all acting.

| Call | What it does |
|---|---|
| `face.express(f, name, ramp=6)` | Eased change to an expression. |
| `face.blink(f, dur=7)` | Blinks win over the expression ramps. |
| `face.auto_blink(f0, f1, seed)` | Natural blinks every 2–4 s. |
| `face.gaze(f, gx, gz)` | Pupils, −1..1. Positive gx = the character's left. Eyes should lead a head turn by 2–4 frames. |
| `face.talk(words)` | `words` is `[(start_s, end_s, text)]` from `T.all_words()`. Adds visemes on top of the mouth. |
| `face.bake()` | Writes all recorded keys. |

Expressions available:
- neutral, happy, joy (^^ eyes with a laugh), shocked, angry, sad
- smug, pain, scared, thinking, determined, deadpan, confused, excited

The library is in `face.EXPRESSIONS`. Mix your own by passing a dict:

```python
dict(lid=..., brow=..., brow_L=..., mouth=..., wide=0..1, pupil=0.5..1.2)
```

Its pieces:
- **Lids:** open, half, angry, sad, squint, happy, closed, joy
- **Brows:** neutral, up, angry, sad, focus, raise1
- **Mouths:** neutral, flat, smile, open, O, frown, grimace, smirk

## rig: armature plus the Actor acting API

```python
arm = rig.build(ch)
A = rig.Actor(ch, arm)
```

**The rig.** root > hips > chest > head. Arms are noodles: B-bone upper and fore arm with IK to `hand_ik.*` under the chest. Legs use IK to `foot_ik.*` under the root. Every other part is rigid on a bone.

### Acting calls

**`A.snap(f, pose=None, root=(x, y, yaw))`**
- Instant change at a CUT.
- Keys sit at f−0.6 and f−0.5, so motion blur never smears across the cut, and the pre-cut key reads the animated value.
- Use it at every shot start to place characters.

**`A.pose(f, name_or_dict, ramp=8, skip=())`**
- An eased pose with overlap built in: hips lead, head +2 frames, hands +3 frames.
- `skip=('head',)` while `look()` aims the head; `skip=('hips',)` during a `hop()`.

**`A.hand(f, 'L' | 'R', (out, fwd, up, reach))`**
- One hand target, given as a direction from the shoulder.
- `out` is mirrored per side. `reach` is a fraction of the arm length: 1 = straight, below 1 bends the elbow.

**Other calls:**

| Call | What it does |
|---|---|
| `A.look(f, nod, turn, tilt, ramp)` | Head aim in degrees. +nod = down, +turn = the character's left, +tilt = its left. |
| `A.turn_body(f, deg, ramp)` | Yaws the root. To turn the short way round, give the target as `deg ± 360`. Reads the start pose from the animation (v4.1), so calls after `frame_set()` no longer drag the character back to an old spot. |
| `A.walk(f0, f1, [(x, y), ...], stride=0.30)` | Feet stay planted, hips bob and sway, arms swing. It keys every frame, so don't snap the same character inside its range. |
| `A.hop(f, height, dur)` | Squash, then airborne with the feet lifting, then the landing. |
| `A.wave(f0, f1, hand, period, amp)` | Waves from the current raised-hand pose. |
| `A.breathe(f0, f1)` | Breathing. |

### Pose library (`rig.POSES`)

- rest, idle, relaxed
- wave_up, shocked, cheer, shrug, hips, think, point
- sad, angry, hold_out
- rifle_up, rifle_down
- bite, jaw, look_at_hand, hug, carry, offer, skim, laugh, hold_up

Add your own as dicts:

```python
{'hand.L': (out, fwd, up, reach), 'hand.R': ..., 'head': (nod, turn, tilt), 'chest': (...), 'hips': (x, fwd, up)}
```

## props: hand props and set dressing

- `props.coin(name, dia, th, mats, c=coll, rim=True)` (rc3): a round coin, a torus rim proud of both faces; gold reads at base #B98A28, rough ~0.35, metal 1, no emission (lesson 79).

**Hand props:**
- `props.cracker`, `props.cracker_halves`
- `props.rifle`
- `props.mug(bugs=n)`
- `props.loaf` with `props.mould(loaf, f, amount, slump)`
- `props.cloth` (shape key `open`)
- `props.pasta_jar`
- `props.steam`

**Set dressing:**
- `props.crate(fill=lambda i: ...)`
- `props.field_oven`
- `props.museum_case`, `props.museum_room`
- `props.box`

**Hands that DO things (v4.1).** The prop is the master; the hand follows it. Key the prop in world space where the story needs it (a rifle butt landing ON the cracker, a cracker edge in the teeth, a spoon bowl at the coffee surface), then:
- `g = props.grip(prop, (x, y, z), name)`: an empty riding the prop at a local offset (the handle, the stock wrist, a box side).
- `props.follow(A, side, g, f_on, f_off=None, blend=3)`: a COPY_LOCATION on the IK target, blended in and out. The hand lands exactly on the grip; noodle arms stretch a little when they must, but keep targets within about 1.4× the arm length.
- `props.target(name, [(f, (x, y, z)), ...])`: a keyed empty for hand paths with no prop (a thumb pressing a loaf, knuckles rapping a cracker).
- Only one follow per hand at a time (stagger `f_off` / `f_on` by the blend).
- New props: `props.bug(name, size)` (a weevil with legs), `props.spoon(name, length)` (origin at the handle end), `props.crumbs(name, origin, f, n, spread, up, dur, floor)` (an impact burst), and `props.mug(..., coffee='#7A4A28')` (milky, so dark bugs read).

**Holding.** `props.hold(A, prop, side, f_on, f_off, loc, rot, follow_rot=True)` uses a ChildOf constraint. The prop keeps exactly the world placement it has at `f_on`, so place it with `props.hand_point(A, side, f)` plus an offset. `follow_rot=False` is for props held up for display (they keep facing the camera).

**Visibility.** Use the film's `vis(obj, f_on, f_off)` helper. It keys `hide_render` on the object AND everything parented under it. Children do not inherit `hide_render`.

## world: outdoor sets

| Call | What it builds |
|---|---|
| `world.meadow_height(x, y, cliff_y)` + `world.ground(name, hfn, mat)` | Terrain. |
| `world.grass(name, pts, hfn, h, w, base, tip)` | Grass. Use `world.scatter(n, fn)` for the points. |
| `world.tree`, `world.pine`, `world.fence`, `world.rock` | Trees, fences, rocks. |
| `world.cloud` | Flat-bottomed, lavender underside. |
| `world.sea`, `world.lighthouse` | Sea and lighthouse. |
| `world.water(name, size, center, z)`, `world.shallow_water_mat()` | A flat water sheet you can key up and down (a flood, a beach, a river). See-through near the camera, reflective at grazing angles (lesson 54). |
| `world.spread_mat(name, origin)` | Water that SPREADS from `origin`: key its `REVEAL` node (metres) from 0 outward for a foam-edged front; shrink it to drain. `ORIGIN_X`/`ORIGIN_Y` are keyable (recentre CONSTANT inside a whip). Put it on a `world.water` sheet (lesson 59). |
| `world.pour(name, loc, length, hw, h0)` | A fat tongue of water out of an arch or pipe along local −Y, with UVs and no ink outline. Key `scale.y` 0.001→1 over about 16 frames with SINE ease (EXPO pops on twos). |
| `world.sink_under_front(pour, water, f0, f1, vcut=0.25, margin=0.08, f_off=None)`, `world.pour_band(pour, f, node, v)` | Hides a band of the pour's tongue, from `vcut` along its length to just past a `spread_mat` front's far edge, keyed per frame from the water's REVEAL/ORIGIN keys and the pour's scale; the tongue ahead of the front stays. Use it whenever a pour lies over a thin flood plane: it draws UNDER the plane and shows through every grass blade as a white strip. A height cut fails, because the churn lifts the tail (lesson 70). Call it after reveal/recenter and the pour's growth keys. |
| `world.churn(pour, f0, f1, wobble=0.30)`, `world.boil(pour)` | The tongue churns: a cloud displace slides downstream, a SIDEWAYS wobble keeps the outline moving (from above only the outline reads), and torn edges boil (`TEAR`, keyed). White water boils where it lands (a foam dome parented to the pour; the pour's `hide_render` drives it). |
| `world.spray(name, at, f0, f1, stretch=2.6)` | Droplets thrown where water lands, a burst every 2–4 frames, stretched along their flight (spheres read as cotton balls). Start it once the water has landed. |
| `world.ripple(name, loc, f, r0, r1, dur)` | A soft fading ring on water (a footstep, a drop, a floating hat). Opaque foam rings read as plastic. On rising water, drive its z from the sheet. |
| `world.flow_water(f0, f1)` | Call once after the build: every water surface's ripples drift and evolve, so no shot holds on glassy still water. |
| `world.tent(camo=True)`, `world.campfire`, `world.barrel` | Camp pieces. |

## camera, film: timing, shots, rendering

### Timing

```python
T = film.Timing(voice/voice.json, script.txt, lead=1)     # voice/draft.json (tools/draft_timing.py) until the voice exists
```

`T.word()` searches the WHOLE film. In every set after the first, pass `after=(F0 - 1) / 30.0` (lesson 48).

This is Whisper aligned to the script with a sequence match, so split words and digits don't drift.

| Call | Returns |
|---|---|
| `T.line(n)` | `(f0, f1)` |
| `T.word('crack', nth, after)` | The frame where that word starts. |
| `T.all_words()` | Every word, for lip-sync. |
| `T.dump(path)` | Writes the timing for `finish.py`. |

Frame 1 = t 0.

### CamPath: one camera that never stops (use this; it replaced Shots in v4.1)

```python
P = film.CamPath(camera.Cam(sc, lens, fstop), creep=0.12)
P.start(f, pos, aim, lens)
P.slam(f, pos, aim, lens, dur=10)        # fast move that brakes HARD into the pose at f (EXPO ease-out), then creeps on
P.whip(f, pos, aim, lens, dur=7)         # a faster slam: scene changes and hidden swaps live in its first 2 frames
                                         #   it STARTS at f - dur; its EXPO puts ~75% of the move in frame f - dur + 1 (the biggest
                                         #   smear): key relights, teleports and set swaps THERE, never from the line start (lesson 69)
P.move_starts()                          # every slam/whip START frame: render them with 64 motion-blur steps (lesson 68)
P.push(f0, f1, pos, aim, lens)           # S-curve push
P.orbit(f0, f1, center, radius, az0, az1, z, aim_z=...)
P.exit(f0, f1, pos, aim)                 # whip OUT, still at full speed on the set's last frame (the next set starts mid-whip, same direction)
P.cut(f, pos, aim, lens)                 # a true hard cut: 2-3 per film at most
P.shake(f, dur, amp)                     # impact shake
P.build(end=None)
```

- **Grammar** (measured on the reference, `railroads-ref/BREAKDOWN.md`):
  - a big move on almost every sentence, about every 2.3 s, landing on its first word;
  - after a landing the camera creeps on and accelerates (it never stops);
  - 2-3 hard cuts in the film.
- **Helpers:**
  - `shot(aim, az, el, d, vh)`: a camera dict with `vh` metres visible top to bottom. az 0 is from −Y; + is counter-clockwise from above.
  - `fr(ch, root, size, az, el)`: wraps `film.framing`.
- **Swaps hide inside whips:** lighting jumps (dusk), character teleports, a held prop exchanged for an identical resting copy. Key them on the whip's first 2 frames. Exposure and look changes too: a lift for one shot burns out the next (lesson 80).
- **Call moves in time order, and end each move AT the next one's start (`f - dur`).** A move starts from the previous CALLED move's last key: a push that ends inside a whip's window shrinks the whip to a 1-2 frame pop, and an out-of-order call snaps the camera back. CamPath prints `CAMWARN` for both; `campath_scan` flags `COLLAPSED` whips (lessons 72-73).

### Step switches (rc3)
- `film.step_prop(o, prop, f, v)`, `film.step_socket(sock, f, v)`, `film.jump_obj(obj, f, **props)`: hard switches at frame f (keys at f−0.6 and f−0.5) whose f−0.6 key holds the CURVE's value there. Never key a property "as found" after any `frame_set()` (lesson 83).

### Effects (`v4/fx.py`, rc3: copy it next to `film.py`, `import fx`)

```python
fx.steam(name, p0, p1, n=90, life=2.8, rise=0.95, wind=(...), c=coll)   # puffs rising from a vent line; obj['amp'] keys strength
fx.smoke(name, p0, p1, ...)                                          # steam() in grey (a chimney)
fx.snowfall(name, center, size, n=900, speed=0.55, r=0.012, holes=[(x0, x1, y0, y1, ztop)])   # flakes; none inside roofed holes
fx.sparks(name, p0, p1)                                              # a burst; key obj['amp'] up for a jab, back to 0
vm = fx.smoke_vol_mat2(roof=(ridge_y, half_depth, eave_z, ridge_z), floor=z0)   # charcoal volume, billowing top (lesson 76)
fx.smoke_fill(name, src, (x0, x1, y0, y1, z0, z1), f0, fill_s=1.2, volume=True, vmat=vm, roof=(...), keep_out=(x, y, z, r))
#   a room FILLING with smoke from src, roof-first; obj['amp'] scales it, obj['phase'] (key it 0 -> 45 over the set) churns it
```

- **Near-lens fade:** steam and snow trees carry an Object Info node named `CAMINFO`; after building the camera, point every one at it (`for ng in bpy.data.node_groups: n = ng.nodes.get('CAMINFO'); n and setattr(n.inputs['Object'], 'default_value', cam.cam)`).
- **Volume smoke:** set `light.volume_factor = 0` on every lamp while the smoke must read black; `sc.eevee.use_volumetric_shadows = True`, `volumetric_end` about 30, tile '8' for animatics and '4' for the final.
- **Foreground snow:** a second `snowfall` box around the camera's path with r about 0.026, on only for that shot (lesson 81).

### Film-level helpers (defined at the top of `example-hardtack/film.py`; copy them)

| Helper | What it does |
|---|---|
| `shot(aim, az, el, d, vh)` | A camera dict with `vh` metres visible. |
| `fr(ch, root, size, az, el, off)` | `film.framing` as a dict. |
| `orbit_from(P, f0, f1, cd, az0, az1)` | An arc that starts exactly where a move landed (no pop). Use it inside long holds. |
| `key(obj, f, loc, rot, scale, ip, easing)` | A world-space prop key that sets its segment's interpolation. |
| `at(obj, f)` | The evaluated world matrix at frame f. |
| `vis(obj, f_on, f_off, kids=True)` | Visibility. Use `kids=False` on containers (lesson 42). |
| `ride(A, prop, 'chest', f_on)` | The prop rides a bone, so hands can follow grips on it while walking. |
| `bone_pos(A, bone, f)` | A bone's world position at frame f. |
| `base_origin(o, p)` | Puts the origin at the base before scale keys (lesson 34). |
| `aim_light(o, target)` | Points a spot light at a target. |
| `beat(f, name, *subjects)` | Registers a beat for the gate stills and the framing report. |

### Shots (v4.0, hard cuts between eased moves; kept for compatibility)

```python
shots = film.Shots(camera.Cam(sc, lens, fstop))
shots.add(f0, f1, a, b, name, shake=0)
shots.build()
```

- `a` and `b` are dicts of pos, aim and lens.
- Each shot is an eased move with a hard jump between shots.
- `cam.ease()`; `cam.handheld(0.0035, 30)` adds a drift so the camera is never still.
- DOF focuses on the aim empty.

**`film.framing(ch, (x, y, yaw), size, az, el, off, lens)`** returns `(pos, aim, lens)`.
- `size` is ECU, CU, MCU, MS or WS.
- These are measured for a 9:16 frame. Face sizes are measured from the face surface.

### Rendering

```
blender -b -P film.py -- SET OUTDIR FRAMES [--preview | --animatic]
```

- FRAMES is one of:
  - `all`;
  - `beats`: one still per `beat()`, the gate;
  - `report`: no render; prints where every subject of every beat sits in frame (0-1, or OUT). Run it before every gate;
  - `campath:a-b`: no render; prints the camera's speed, turn and jerk per frame. Pipe it into `python3 tools/campath_scan.py --starts f1,f2,...`, which flags reversals at speed, unplanned jerks and stalls (lesson 46);
  - `a-b`, or `a-b:2` for every 2nd frame (the animatic).
- `--preview` is 540×960 at 12 samples (gate stills). `--animatic` is 480×854 at 8 samples.
- `python3 tools/camstats.py out/NAME.mp4 [--twos]` measures camera pans and shifts (not push-ins) against the reference measured on the same meter: a big move every 1.4 s, mean 3.7 px/frame. Its "still %" is not a target (lessons 40 and 56).
- `bash animatic.sh NAME "SET SET ..." [--only "set:a-b ..."]` renders the whole film (or only the changed ranges) on twos, doubles it back to 30 fps (`fill_twos.py`) and mixes the full sound into `out/NAME.mp4`. Review that before ONE full render with `render.sh`.
- Every frame is written with its global number, so sets and halves can render in parallel.

## Spec reference (see `v4/specs/*.json`)

### Head and face

```
head  {w, h, d, egg, z}
face  {eyes  {x, z, rx, rz, pupil:[px, pz], line, lid_weight},
       brows {x_in, len, z, thick, taper, line, color},
       mouth {z, w, h, line},
       freckles [[x, z]...],
       blush {x, z, r, color}}
```

- Face values are in units of the head width W, with z from the head centre.
- Taller egg heads read better: h ≈ 1.2 w.

### Body

```
body  {kind: coat | bean, color, z0, z1, top_r, bot_r, widest, depth, neck,
       collar {h, open}, hood, seam,
       buttons {kind: round | toggle | none, color, zs | n},
       belt {color, z, h, knot},
       epaulettes {color, x, z},
       apron {color, top, waist, bib},
       lower {color, z, rough},
       bandana {color, top, drop, w, ring, ring_h},
       sash {color, line, scale, top, hip, w, x0, x1, end}}
```

- `lower`: two-tone trousers, a material split on the body below `z` (absolute metres).
- `bandana`: a triangle on the chest with a rolled band round the neck and a knot at the back.
- `sash`: a plaid cloth (`color` with `line` stripes, `scale` checks per metre) from the shoulder at `x0` to the hip at `x1` (fractions of the body radius), with a loose end hanging at the front.

### Limbs

```
arms  {style: stick | sleeve, r (stick) | r0/r1 (sleeve), len, angle, shoulder:[x, z], hand {r, color}}
legs  {color, r, hip_x, z_hip, z_ankle}
feet  {kind: round | boot | clog, color, h, r, toe, len, toe_up, fwd}
```

### Hats, hair and facial hair

**Hats.** `kind` is one of `beanie`, `kepi`, `toque`, `tricorn` or `wide`.

| Kind | Parameters |
|---|---|
| `beanie` | `brim_z`, `brim_h`, `thick`, `crown`, `ribs`, `tilt` |
| `kepi` | `band_z`, `band_h`, `crown_h`, `taper`, `slope`, `visor_len`, `band`, `visor`. Add `soft:true` with `crown_w`, `overhang`, `slouch` for a forage cap. |
| `toque` | `band_z`, `band_h`, `min_r`, `puff_h`, `puff_r`, `pleats` |
| `tricorn` | `band_z`, `crown_h`, `brim_w`, `fold` (degrees the sides turn up), `droop`, `brim_t`, `trim` (colour), `plume` (colour), `plume_angle`, `plume_scale` |
| `wide` | `band_z`, `band_h`, `band` (colour), `crown_h`, `taper`, `top_round`, `brim_w`, `droop`, `front_up`, `flop` (the sides sag: straw), `fray` (a ragged edge), `brim_t` |

**Hair:**
- `{kind: curly_tuft, color}`.
- Short hair: `{kind: crop, color, front, side, back, grow, thick, quiff: [w, d, h], quiff_x, quiff_y, quiff_z, quiff_pitch, quiff_yaw}`. It is a shell over the crown cut at a hairline: `front`, `side` and `back` are its height in head heights (for example 0.34, −0.12, −0.32), and the quiff sweeps up at the front (for example `quiff: [0.84, 0.62, 0.28]`, `quiff_z` 0.42).

**Glasses:** `glasses {x, z, lw, lh, corner, off, wire, color, temple_end, ink}`. Thin wire rims, each a rounded rectangle centred at ±`x`, `z` (W units), `lw` × `lh` half-size, held `off` in front of the face, with temples running round to behind the ears. Example: `{x: 0.19, z: -0.03, lw: 0.175, lh: 0.10, corner: 0.045, off: 0.035, wire: 0.0032, color: "#B9BEC8"}`. They ride the head bone.

**Facial hair:**
- A moustache: `{style: handlebar | walrus | bushy_curl | chevron | thin, z, span, thick, depth, color}`. Keep `span` at 0.66 W or less (lesson 50).
- A beard: `{style: beard, color, depth, inner: [[x, z], ...], outer: [[x, z], ...], hang_z, hang_y, hang: [w, d, h]}`. The two edges are the right half, from under the mouth out to the sideburn, in W units. It is fitted to the head analytically, the upper lip stays bare, and a tuft hangs under the chin.

**New part kinds** go in `char.py` as a method plus a dispatch entry. Fit hats to the head with `self._fit(R, zs)`, never with a fixed radius.

**Chaining hand follows (hand over hand, a crank, a rope):** set each follow's `f_off` to the NEXT follow's `f_on`, so the two overlap through the blend. With a gap, part of the hand's keyed rest pose leaks into the crossfade: the keeper's hand dropped off the wheel once per stroke ("gone every 4th pose").

**`lean(A, f0, f1, deg)`** (in the example `film.py`) adds a forward lean as an additive F-curve GENERATOR on the chest's pitch. Use it for wading, pushing or bracing: a keyed lean pose gets overwritten by `walk()`'s own chest keys.
