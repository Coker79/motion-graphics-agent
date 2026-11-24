"""onsets.py voice.wav voice.json: Whisper often starts a word inside the pause before it (it swallows the silence).
Move every word start that sits inside a real pause (RMS < -50 dB for >= 0.18 s) to the end of that pause, so cues,
camera moves and captions land on the sound. Writes voice.json in place (a .bak copy first)."""
import json, shutil, sys, wave
import numpy as np
wav, js = sys.argv[1], sys.argv[2]
w = wave.open(wav); sr = w.getframerate(); ch = w.getnchannels()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, ch).mean(1) / 32768
hop = sr // 100
db = 20 * np.log10(np.sqrt(np.array([np.mean(a[i:i + hop] ** 2) for i in range(0, len(a) - hop, hop)])) + 1e-9)
runs, i = [], 0
while i < len(db):
    if db[i] >= -50: i += 1; continue
    k = i
    while k < len(db) and db[k] < -50: k += 1
    if (k - i) >= 18: runs.append((i / 100, k / 100))
    i = k
shutil.copy(js, js + '.bak'); j = json.load(open(js)); n = 0
for seg in j['segments']:
    for wd in seg['words']:
        for s, e in runs:
            if s - 0.15 <= wd['start'] < e - 0.05 and wd['end'] >= e - 0.06:   # the word swallows the pause
                print(f"  {wd['word'].strip():>12}: {wd['start']:.2f} -> {e - 0.02:.2f}"); wd['start'] = round(e - 0.02, 3); n += 1; break
    if seg['words']: seg['start'] = seg['words'][0]['start']
json.dump(j, open(js, 'w')); print(f'{n} word starts moved out of pauses ({len(runs)} pauses)')
