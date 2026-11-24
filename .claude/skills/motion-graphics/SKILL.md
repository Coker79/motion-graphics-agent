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

## Channel defaults (The Efficiency Edge)
- **Voiceover:** always George (ElevenLabs premade, voiceId `JBFqnCBsd6RMkjVDRZzb`). Generate via the ElevenLabs API directly: `POST https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb/with-timestamps?output_format=mp3_44100_128` with `{"text":…,"model_id":"eleven_multilingual_v2"}` and header `xi-api-key: proxy-injected` (the environment proxy injects the real key; never put a key in files). Use the returned character timings for captions and avatar lip-sync. vidIQ voiceover is only a fallback.
- **Shorts style:** 1080×1920, green `#2f3f33` background, gold `#E2B33C`, yellow `#FFD400` emphasis captions, hand-drawn 12 fps boil, timeline header, re-hook by ~5 s. Template: `shorts/ai-bubble/src.html`.
- **Audio:** −14 LUFS / −1.5 dBTP.
- **Publishing:** draft with `vidiq_social_post_draft_create`, show the user, publish only after they approve.
- **Host avatar:** ElevenLabs avatar "Cokerbroun", avatar ID `pZbecZhar6mId02mevrC` (3D-cartoon, white tee, blue crossbody bag). Use it for every on-screen host. Generate talking clips with George's voice via ElevenLabs (`POST /v1/flows/video`, model `creatify-aurora`, image = the avatar, audio = the George VO); the API key needs the **Image & Video generation** permission. Composite the clip into the scene; do not redraw the host as a code-drawn character.
- **Look and pacing:** aiTrends-style cinematic explainers — moody gradient lighting, parallax layers, particles (rain/embers), camera tracking/push-ins, word captions; 16:9 long-form or 9:16 Shorts.
