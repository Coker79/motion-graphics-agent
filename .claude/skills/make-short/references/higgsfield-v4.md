# Higgsfield in v4: reference images, voice, music, SFX

Higgsfield never renders video in v4, and Seedance is never used. Every frame is rendered in Blender.

Ask the user for a credit budget once per Short; about 30–50 credits covers everything. Log what you spend.

## Prices and settings (checked 2026-11-17)

Prices drift. Preflight every call with `estimate_image_cost` / `estimate_audio_cost` (the connector no longer accepts `get_cost: true`) and quote the live figure when you ask the user. Log the CHARGE from `transactions`, not the quote (Seed Audio charged less than quoted). If a batch call times out after charging, check `balance`/`transactions` before regenerating; prefer one `generate_image` per character sheet (its job id returns at once).

| Asset | Model | Cost | Notes |
|---|---|---|---|
| Character sheet | `nano_banana_2_1`, 2k, 16:9 | 2 per sheet | Pass the style target, `SKILL/v4/style_target.jpg` (uploaded once with `media_upload`), as `image_references`. One sheet per character; redo only what the user rejects. |
| Narration | `seed_audio`, preset voice | ~7 per take (~190 words) | `speech_rate` 40-50 at 48 kHz, quotes left out (lessons 22 and 23). Pace with `voice/pace.py`, which only edits pauses. |
| Character line | `seed_audio`, a second preset voice | 0.4 each | One generation per quoted line, `speech_rate` about 20, inserted by `pace.py --quote/--after`. |
| Music | `elevenlabs_music_v2_5`, `force_instrumental` | 9.02 for 62 s | Prompt for the mood, plus "leaves room for narration". |
| SFX | `mirelo_text_to_audio` | 0.5 per 2 s, priced by length | Use a duration of 2 s or more, check the levels, and normalise (lesson 24). An 8 s ambience costs about 2. |

A 60 s Short with 3 characters and one redo cost 37.7 credits (Dutch-flood test).

## Character sheet prompt

The prompt is the template below. Only the CHARACTER paragraph changes. The kit can build exactly these proportions:
- an egg head;
- a bean body in one costume colour with buttons and one accent;
- stick or sleeve arms with ball hands;
- stick legs with round feet or boots;
- a hat as identity;
- optional moustache, freckles or blush.

> Character model sheet for a stylized 3D animated YouTube Short, in EXACTLY the rendering style of the reference image: a high-end stylized 3D cartoon, like a cozy animated feature or a premium indie game. Soft warm key light with gentle shadow gradients, a subtle rim light, smooth matte materials with a soft painterly texture (fine brush grain), and a crisp dark outline around the character and its big shapes. Rich but natural colours. Not realistic, not flat 2D.
>
> TOY PROPORTIONS (keep exactly, it must be buildable from smooth simple 3D shapes): a big smooth egg-shaped head, about 40% of the standing height; a small rounded bean-shaped body; thin black stick arms and thin black stick legs; round black ball hands without fingers; small rounded black feet. FACE: simple and graphic: two big white oval eyes with a thick dark outline, black pupils with one small white highlight, thick chunky dark eyebrows, a simple mouth, no nose.
>
> CHARACTER: <role, age and attitude; hat; garment + colour + buttons + one accent; facial hair; skin "soft white with a faint cool lavender tint">.
>
> LAYOUT: a character model sheet on a plain light grey background with even studio light. Top row: full body at the same scale, standing on one baseline with the arms held slightly away from the body (A-pose): front view, three-quarter view, side view, back view. Bottom row: six head-and-shoulders expressions: neutral, big smile, shocked, angry, sad, smug.
>
> No text, labels, captions, letters, numbers, logos or watermarks anywhere.

If a design needs a part the kit doesn't have (a new hat, a dress, glasses), say so before building. Either add the part to `char.py`, or adjust the CHARACTER line and regenerate.

## Narration (never time-stretch or pitch-shift: lesson 22)

1. Generate one take of the whole script WITHOUT the quoted lines.
   - Write the spelling you want spoken ("mold", "sixteen seventy-two"). The captions use the script's own words.
2. Generate each quoted line alone, in its own preset voice. Hardtack used Fraser, the deepest, at about 89 Hz; Arthur narrates at about 140 Hz.
3. Prepare every take: highpass 70 Hz and `loudnorm` to -18 LUFS, and silence-trim the quotes.
4. Transcribe with Whisper (small, `--word_timestamps True`). Check that every script word was heard (SKILL §3.3).
5. `voice/pace.py` shortens the pauses and drops each quote into the pause after its lead-in word. Then run Whisper again, `voice/onsets.py` and `timing_dump.py`.
