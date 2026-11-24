"""draft_timing.py script.txt voice/draft.json [words_per_s]: a Whisper-shaped timing file made from the script alone
(3.55 words/s, 0.42 s after a sentence, 0.25 s after a comma), so shots can be blocked and gated BEFORE the voice exists.
film.py uses it when voice/voice.json is missing; the real take replaces it and the S()/W() anchors carry over."""
import json, re, sys
src, out = sys.argv[1], sys.argv[2]; wps = float(sys.argv[3]) if len(sys.argv) > 3 else 3.55
t = 0.15; words = []
for line in open(src):
    line = re.sub(r'^>[TX]', '', line.strip())
    if not line: continue
    for tok in line.split():
        core = re.sub(r'[^A-Za-z0-9\'-]', '', tok)
        if not core: continue
        d = (0.55 + 0.06 * len(core)) / wps; words.append(dict(word=' ' + tok, start=round(t, 3), end=round(t + d * 0.9, 3))); t += d
        if re.search(r'[.?!]["”]?$', tok): t += 0.42
        elif tok.endswith(','): t += 0.25
json.dump(dict(text='', segments=[dict(start=0.0, end=round(t, 3), text='', words=words)]), open(out, 'w'))
print(f'{out}: {len(words)} words, {t:.1f} s ({len(words) / t:.2f} words/s)')
