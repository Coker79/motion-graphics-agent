---
name: motion-graphics
description: Entry point for any motion-graphics, animation or video request (reels, promos, product demos, explainers, B-roll, captions, voiceover, sound design, rotoscoping). Picks the right specialist skill from this merged set and enforces the shared verify loop. Use first whenever the user asks to make, edit, animate, caption, voice or sound-design a video.
---

# Motion graphics (router)

Pick ONE primary skill, then layer the support skills.

| Request | Primary skill |
|---|---|
| 12–20 s hype reel / teaser / launch sting | `explainer-high-energy` |
| 45–90 s calm product demo / feature walkthrough | `explainer-default` |
| 10–30 s one-take story / loopable product animation | `explainer-engaging` |
| Animated maps (countries, routes, pins) — combine with director | `map-animation` |
| Stickman / stick-figure explainers, faceless story videos (styles B1–B7, A1–A8) | `directing-stickman-videos` (submodule `vendor/stickman-video-director`) — still follow the LOCKED channel rules below for voice, intro, length, sound and approvals |
| 3D "toy family" or 3D diorama Short (45–60 s) rendered in Blender | `make-short` (v2.3.0). Needs Blender + ffmpeg (its installer supports Apple Silicon Mac and Windows only, not this Linux cloud) and Higgsfield for its default voice/music. **Not the standard route** (hybrid style is locked as standard); only if the user explicitly asks, and ideally on their Mac. Locked channel rules still win: use George (ElevenLabs) for voice and our own score instead of Higgsfield audio; Phil intro first |
| B-roll / cutaways for a talking-head video + transcript | `motion-broll` |
| Anything else, or a full production (VO script, storyboard, 2D/3D, editing raw footage, captions, multi-format) | `motion-video-director` |

Support skills (use whenever relevant):
- `sound-effects` — every video that ships with audio: cue list, beat grid, CC0 SFX, measured loudness.
- `object-separation` — isolate a person/product/hand (text-behind-subject, cutouts, mattes).
- `motion-verify` — mandatory before delivery: contact sheets + `probe-mp4.sh`.

Shared rules:
1. Get the brief in one message (story, length, platform/aspect, brand, CTA); ask only what's missing.
2. Get approval on the plan before building big renders.
3. Every frame must be a pure function of time (seekable, seeded randomness) so previews match finals.
4. Look at your output (contact sheets) after every change; never say "looks good" without having viewed frames, and never say "sounds good" — give the user timestamps to check by ear.
5. Final MP4: H.264, yuv420p, AAC 48 kHz, `+faststart`; verify with `probe-mp4.sh`.

## Channel defaults (The Efficiency Edge) — LOCKED by the user on 24 Nov 2026
These rules override anything older in this repo. Do not deviate unless the user explicitly asks in the current conversation.

### 1. Who appears and who speaks (LOCKED)
- **Long videos:** open with the reusable Phil intro clip `assets/phil/phil-intro.mp4` (audio `assets/phil/phil-intro.mp3`: "Welcome to The Efficiency Edge. I'm Phil. Today, we're decoding the money story behind the headlines."), shown in a fixed frame that never moves or resizes. **George narrates everything after the intro.**
- **Shorts:** also open with the Phil intro clip (user instruction, 24 Nov 2026), framed as a polaroid on the paper page, then George narrates.
- **Never ask the user to generate a new Phil/avatar clip** and never send Phil MP3s, unless the user explicitly asks for new Phil lines. Phil = ElevenLabs avatar "Phil", podcast-studio style, avatar ID `pZbecZhar6mId02mevrC` (API video needs Pro; on Starter the user would make clips in the app).
- **Voice:** George (ElevenLabs voiceId `JBFqnCBsd6RMkjVDRZzb`), via `POST https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb/with-timestamps?output_format=mp3_44100_128` with `{"text":...,"model_id":"eleven_multilingual_v2"}` and header `xi-api-key: proxy-injected` (proxy injects the key; never write keys to files). Use the timings for captions/SRT. Check credits first (`GET /v1/user/subscription`).

### 2. Formats and length (LOCKED)
- Every story = one **16:9 long video (default 2.5–3 min; 2–3 fine; longer only if the story needs it)** + one **9:16 Short (25–50 s)** made from the same story.
- Long video goes live first; the Short 1–2 days later. The user links the Short to the long video in Studio ("Related video", Studio-only); add "Full story: <link>" to the Short's description via `tools/yt.py update`.

### 3. Look and sound (LOCKED)
- **Standard production route (LOCKED 24 Nov 2026):** every video is made with the code-drawn **hybrid** style (stickman + documentary case file), rendered here in the browser renderer (Playwright + ffmpeg). Templates: Short `videos/fed-strong-dollar/stickman/src.html`, long `videos/fed-strong-dollar/src.html`. Do **not** use `make-short`/Blender (too slow on this CPU-only cloud machine) or paid image/video generators unless the user explicitly asks for that specific video.
- Visual style (house style): **hybrid** — B1-style stickman characters (slender, expressive, hand-drawn, Caveat hand lettering) acting out the story INSIDE the documentary world, plus documentary "case file" props: (aged paper, typewriter text, case folders, newspaper clippings with red highlights, polaroids, red-string maps, hand-drawn charts with red circles, stamps) — template `videos/fed-strong-dollar/src.html`. Cinematic variant: `videos/too-big-to-fire-long/`. No real photos of people (copyright): use illustrations/silhouettes.
- Word-by-word captions with yellow emphasis; keep everything clear of the Phil frame.
- Music: TENSE score — pulsing sub-bass ostinato on 8ths (~96 BPM), clock-tick pulse, rising string pads into reveals, short drops before key lines, impacts only on reveals. Voice always on top: background stem 14–16 dB under voice (measure stems with ebur128). Final −14 LUFS / −1.5 dBTP.
- Facts first: only sourced claims; allegations labelled as reported; no buy/sell advice; disclaimer in description.

### 4. Workflow and approvals (LOCKED)
1. Find topic (web search + vidIQ trends if credits allow) → propose to user.
2. Write script → **user approves**.
3. George narration → build → check stills → render both formats → send to user → **user approves**.
4. Thumbnail (Phil frame with eyes open + bold headline, checked at 320×180) and sentence-level `.srt`.
5. Show final title/description/tags/time → **user approves** → upload + schedule with `tools/yt.py` (upload --publish-at, thumbnail, captions). Default publish time **3:00 pm America/New_York**.

### 5. YouTube connection
- `python3 tools/yt.py` (me, upload, thumbnail, captions, update, get, analytics). Secrets in ~/.config/efficiency-edge/ (never in the repo). Full sign-in `token-full.json` (Desktop client + PKCE; user pastes the localhost redirect URL) covers upload, captions and analytics. Testing-mode sign-ins can expire after ~7 days: re-auth by generating a new PKCE URL (redirect http://localhost:8765). vidIQ is now only for trend research (credits are scarce).
