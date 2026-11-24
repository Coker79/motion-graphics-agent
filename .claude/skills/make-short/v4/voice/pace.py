"""pace.py: set the narration's pace by editing ONLY its pauses. No time-stretch and no pitch-shift: both made v1 sound
"radio staticy". Get the speed from the voice engine itself (Seed Audio speech_rate, 48 kHz); this only tightens the
pauses and drops a character line (a second preset voice) into the gap after a word.

  python3 voice/pace.py voice/narr.wav voice/narr.json voice/voice.wav \
      [--script script.txt] [--quote voice/quote.wav --after "laughed,"] [--quote voice/quote2.wav --after "too."] \
      [--sent 0.42] [--comma 0.32] \
      [--hold "smiled.=0.6" --hold "apart.=0.7"]

  narr.json   Whisper JSON of narr.wav (word_timestamps)
  --script    drop any junk the engine put before the first script word (one take began with "of an eye.")
  --sent      pause after a sentence (only ever shortened; the default sits between the reference's 0.1-0.25 s and
              the client's "don't make it jarring")
  --comma     pause inside a sentence (cap)
  --hold      give one pause (keyed by the word Whisper heard before it) its own length: a beat before a turn, a
              reaction after a gag. "word=keep" leaves it as recorded.
Then: whisper the result, run voice/onsets.py on it, and check the words/s it prints (formula pace: 3.3-3.7)."""
import argparse, json, re, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('narr'); ap.add_argument('narr_json'); ap.add_argument('out')
ap.add_argument('--script')
ap.add_argument('--quote', action='append', default=[]); ap.add_argument('--after', action='append', default=[])   # repeatable pairs, in order
ap.add_argument('--pre', type=float, default=0.30); ap.add_argument('--post', type=float, default=0.40)
ap.add_argument('--sent', type=float, default=0.42); ap.add_argument('--comma', type=float, default=0.32)
ap.add_argument('--hold', action='append', default=[])
ap.add_argument('--quiet-db', type=float, default=-50.0); ap.add_argument('--min-run', type=float, default=0.18)
a = ap.parse_args()


def load(p):
    w = wave.open(p); sw = w.getsampwidth(); ch = w.getnchannels(); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float32)
    return x.reshape(-1, ch).mean(1) / (32768.0 if sw == 2 else 2.0 ** 31), sr


narr, SR = load(a.narr)
assert len(a.quote) == len(a.after), 'give one --after word for every --quote file'
quotes = {}
for qf, aw in zip(a.quote, a.after):
    q, qsr = load(qf); assert qsr == SR, f'{qf}: quote and narration must share a sample rate (resample the quote first)'
    quotes[aw] = q
hop = SR // 100
db = 20 * np.log10(np.sqrt(np.array([np.mean(narr[i:i + hop] ** 2) for i in range(0, len(narr) - hop, hop)])) + 1e-9)
runs, i = [], 0
while i < len(db):
    if db[i] >= a.quiet_db: i += 1; continue
    k = i
    while k < len(db) and db[k] < a.quiet_db: k += 1
    if (k - i) / 100 >= a.min_run: runs.append((i / 100, k / 100))
    i = k
words = [w for s in json.load(open(a.narr_json))['segments'] for w in s.get('words', [])]
norm = lambda t: re.sub(r"[^a-z0-9']", '', t.lower())
before = lambda t: ([w['word'].strip() for w in words if w['end'] <= t + 0.12] or ['^'])[-1]
holds = {}
for h in a.hold:
    k, v = h.rsplit('=', 1); holds[k] = None if v == 'keep' else float(v)

head = 0.0
if a.script:                                   # junk before the first script word: start at the pause before it
    first = norm(open(a.script).read().split()[0])
    w0 = next((w for w in words if norm(w['word']) == first), None)
    if w0 and w0['start'] > 0.05:
        pre = [e for s, e in runs if e <= w0['start'] + 0.15]
        head = max(0.0, (pre[-1] if pre else w0['start']) - 0.04)
        if head > 0: print(f'head: skipping {head:.2f} s before "{w0["word"].strip()}"')

XF = int(0.006 * SR)
def join(parts):
    out = parts[0].copy()
    for p in parts[1:]:
        if len(out) > XF and len(p) > XF:
            r = np.linspace(0, 1, XF, dtype=np.float32); out[-XF:] = out[-XF:] * (1 - r) + p[:XF] * r; out = np.concatenate([out, p[XF:]])
        else: out = np.concatenate([out, p])
    return out

parts, cur = [], int(head * SR)
for s, e in runs:
    if s < head + 0.05: continue
    wb = before(s); dur = e - s
    if wb in quotes:
        parts += [narr[cur:int((s + a.pre / 2) * SR)], np.zeros(int(a.pre / 2 * SR), np.float32), quotes.pop(wb), np.zeros(int(a.post / 2 * SR), np.float32)]
        cur = int((e - a.post / 2) * SR); print(f'{s:6.2f} {wb:>12} {dur:.2f} -> quote'); continue
    tgt = holds.get(wb, a.sent if re.search(r'[.?!:]$', wb) else a.comma)
    if tgt is None or dur <= tgt: continue
    parts.append(narr[cur:int((s + tgt / 2) * SR)]); cur = int((e - tgt / 2) * SR)
    print(f'{s:6.2f} {wb:>12} {dur:.2f} -> {tgt:.2f}')
parts.append(narr[cur:])
if quotes: print('WARNING: no pause found after', ', '.join(f'"{k}"' for k in quotes), '- those quotes were NOT inserted (check the Whisper word, punctuation included)')
f = int(0.004 * SR); parts[0][:f] *= np.linspace(0, 1, f, dtype=np.float32)
out = join(parts)
w = wave.open(a.out, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
n = sum(1 for _ in open(a.script).read().split()) if a.script else len(words)
print(f'wrote {a.out}: {len(out) / SR:.2f} s, about {n / (len(out) / SR):.2f} words/s')
