"""finish.py: rendered frames + narration + ducked music + SFX on their story beats + captions -> out/short.mp4
python3 finish.py [frames_dir] [out.mp4]
Captions follow the reference Shorts: Montserrat ExtraBold, white with a black outline and a soft shadow, mostly one
word per card (a short word joins the next), each card hard-cut ~2 frames before its word, low-middle of the frame."""
import json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FPS = 30
FR = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'renders', 'final'))
OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'out', 'short.mp4'))
def _tool(name):   # the installers' pinned build first (Mac ~/.local/bin, Windows ~/.make-short/bin), then PATH
    home = os.path.expanduser('~')
    for c in (os.path.join(home, '.local', 'bin', name), os.path.join(home, '.make-short', 'bin', name + '.exe'), shutil.which(name)):
        if c and os.path.isfile(c): return c
    return name
FF, FP = _tool('ffmpeg'), _tool('ffprobe')
V = os.path.join(HERE, 'voice'); SFX = os.path.join(HERE, 'sfx')

wh = json.load(open(os.path.join(V, 'voice.json')))
words = [dict(w=w['word'].strip(), s=w['start'], e=w['end']) for seg in wh['segments'] for w in seg['words']]
tim = json.load(open(os.path.join(V, 'timing.json')))            # script words (script spelling) with times
swords = [w for l in tim['lines'] for w in l['words']]
norm = lambda t: re.sub(r"[^a-z0-9']", '', t.lower())
def frame(sec): return int(round(sec * FPS)) + 1
def W(text, nth=0, after=0.0):
    k = 0
    for w in words:
        if w['s'] < after: continue
        if norm(w['w']).startswith(norm(text)):
            if k == nth: return frame(w['s'])
            k += 1
    raise KeyError(text)
S = lambda n: frame(tim['lines'][n - 1]['s'])

# ---------------- captions (ASS)
def ts(sec):
    sec = max(0.0, sec); h = int(sec // 3600); m = int(sec // 60) % 60; return f'{h}:{m:02d}:{sec % 60:05.2f}'
clean = lambda w: re.sub(r'["“”.,!?;:]', '', w)
cards = []; i = 0
while i < len(swords):
    w = swords[i]; n = swords[i + 1] if i + 1 < len(swords) else None
    pair = n is not None and len(clean(w['w'])) <= 3 and not re.search(r'[.,!?:]$', w['w']) and n['s'] - w['s'] < 0.45
    cards.append(dict(s=w['s'] - 2 / FPS, text=f"{clean(w['w'])} {clean(n['w'])}" if pair else clean(w['w']), end=(n if pair else w)['e']))
    i += 2 if pair else 1
CF0 = json.load(open(os.path.join(SFX, 'cues.json'))) if os.path.exists(os.path.join(SFX, 'cues.json')) else {}
CAPUP = CF0.get('capUp', [])          # [[first frame, last frame, marginV]]: lift captions off a key prop
ev = []
for k, c in enumerate(cards):
    nxt = cards[k + 1]['s'] if k + 1 < len(cards) else c['end'] + 0.4
    end = min(nxt, c['s'] + 0.9)
    fr_ = max(1, frame(c['s'])); mv = next((m for a, b, m in CAPUP if a <= fr_ <= b), 0)    # the first word starts before frame 1
    ev.append(f"Dialogue: 0,{ts(c['s'])},{ts(end)},W,,0,0,{mv},,{{\\fscx86\\fscy86\\t(0,80,\\fscx100\\fscy100)}}{c['text']}")
ass = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\n"
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
       "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
       "Style: W,Montserrat ExtraBold,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,8,4,2,60,60,420,1\n\n"
       "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + '\n'.join(ev) + '\n')
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True); assf = os.path.join(HERE, 'out', 'captions.ass'); open(assf, 'w', encoding='utf-8').write(ass)   # libass needs UTF-8 (Windows defaults to cp1252)

# ---------------- sound cues from sfx/cues.json (anchors use the same timing the film used)
#   anchors: "word:smashed" | "word:rifle#1" (2nd occurrence) | "word:rifle@40" (after 40 s) | "line:5" | "line:13-" (frame before
#   line 13 starts) | "frame:120" | "end".  cues = [sfx, anchor, frame offset, volume]; ambience = [file, start, end|null, volume]
CF = json.load(open(os.path.join(SFX, 'cues.json')))
def at(a):
    if a in (None, 'end'): return None
    kind, v = a.split(':', 1)
    if kind == 'frame': return int(v)
    if kind == 'line': return S(int(v[:-1])) - 1 if v.endswith('-') else S(int(v))
    nth, after = 0, 0.0
    if '@' in v: v, after = v.split('@'); after = float(after)
    if '#' in v: v, nth = v.split('#'); nth = int(nth)
    return W(v, nth, after)
CUES = [(c[0], at(c[1]) + c[2], c[3], (c[4] if len(c) > 4 else 0.0)) for c in CF.get('cues', [])]   # [sfx, anchor, offset, volume, trim_s, max_dur_s]
CUE_MAX = {i: float(c[5]) for i, c in enumerate(CF.get('cues', [])) if len(c) > 5 and c[5]}
AMB = [(n, at(a0), at(a1), vol) for n, a0, a1, vol in CF.get('ambience', [])]
MUSIC = CF.get('music', {'file': 'music.mp3', 'volume': 0.32})
nframes = len([f for f in os.listdir(FR) if f.endswith('.png')]); dur = nframes / FPS
inputs = ['-framerate', str(FPS), '-start_number', '1', '-i', os.path.join(FR, 'f%05d.png'), '-i', os.path.join(V, 'voice.wav'), '-i', os.path.join(SFX, MUSIC['file'])]
fit = ''
if MUSIC.get('fit'):                     # stretch the music so its last beat lands on the last frame (music only: never the voice)
    md = float(subprocess.run([FP, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                               os.path.join(SFX, MUSIC['file'])], capture_output=True, text=True).stdout.strip() or dur)
    if 0.9 < md / dur < 1.1: fit = f',atempo={md / dur:.5f}'
HEAD = float(MUSIC.get('head', 0.0))     # trim a silent head so the loop seam has music from frame 1
if MUSIC.get('land'):                    # land the music's final downbeat ON a story beat: {"music_s": 48.34, "at": "word:butt@49"}
    tgt = (at(MUSIC['land']['at']) - 1) / FPS; r = (MUSIC['land']['music_s'] - HEAD) / tgt
    if 0.9 < r < 1.1: fit = f',atempo={r:.5f}'; print(f'music: final hit {MUSIC["land"]["music_s"]} s lands at {tgt:.2f} s (tempo x{r:.4f})')
# ---------------- the mix (v2, after the client's "the water is so loud you can't hear the voice"):
#   1. every SFX/ambience file is LOUDNESS-matched (peak-normalising made a 2 s burst of water noise far louder than speech),
#   2. each one-shot is smoothed (short fade in, fade out, a soft high cut),
#   3. the whole SFX bus is DUCKED under the voice (gently: SFX_DUCK; the music harder),
#   4. a measured gate: the voice must sit at least VO_MARGIN dB above everything else in every 400 ms window where it
#      speaks, and SFX_MARGIN dB above the SFX alone; a failing window lowers ONLY the cues sounding in it, then rebuilds,
#   5. each one-shot's HIT lands on its frame (late hits inside generated files are trimmed: lead()), and every stem
#      must come out exactly the film's length (a short stem means shifted audio: the bus once played 2.43 s early).
import wave as _wave, numpy as _np
STEMS = os.path.join(HERE, 'out', 'stems'); os.makedirs(STEMS, exist_ok=True)
VO_MARGIN = float(CF.get('vo_margin', 8.0))            # dB the voice must clear the music + SFX by, in every spoken window
VO_MIN = CF.get('vo_min', 10.0)                            # STRICT floor (default 10 dB; "vo_min": null disables) for voice over music + SFX in EVERY spoken window (e.g. 10): met by
                                                       # per-window music dips (and per-cue SFX cuts), never by lowering the whole bed
SFX_MARGIN = float(CF.get('sfx_margin', 10.0))         # ...and the SFX alone by, in EVERY spoken window (no stray water burst over a word)
SFX_LUFS, AMB_LUFS = float(CF.get('sfx_lufs', -27.0)), float(CF.get('amb_lufs', -33.0))
LCACHE = os.path.join(SFX, '_loudness.json'); lc = json.load(open(LCACHE)) if os.path.exists(LCACHE) else {}
def lufs(path):
    key = f'{os.path.basename(path)}:{int(os.path.getmtime(path))}'
    if key not in lc:
        out = subprocess.run([FF, '-hide_banner', '-nostats', '-i', path, '-af', 'silenceremove=start_periods=1:start_threshold=-40dB,ebur128', '-f', 'null', '-'],
                             capture_output=True, text=True).stderr
        m_ = re.findall(r'I:\s+(-?[\d.]+) LUFS', out); lc[key] = float(m_[-1]) if m_ else -70.0
    return lc[key]
def fdur(path):
    return float(subprocess.run([FP, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip() or 2.0)
def lead(path):
    """seconds from the file's start to its HIT: the first 10 ms that come within 10 dB of the file's loudest 10 ms.
    Generated one-shots often hide the hit late: the Dutch-flood clunk, splash and scrape hit 1.0-1.5 s in, so their
    hits landed 30-45 frames after the beat they mark."""
    key = f'lead:{os.path.basename(path)}:{int(os.path.getmtime(path))}'
    if key not in lc:
        raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', '48000', '-f', 's16le', '-'], capture_output=True).stdout
        x = _np.frombuffer(raw, _np.int16).astype(_np.float32) / 32768; h = 480
        e = 20 * _np.log10(_np.sqrt(_np.mean(x[:len(x) // h * h].reshape(-1, h) ** 2, axis=1)) + 1e-9) if len(x) >= h else _np.zeros(1)
        lc[key] = round(float(_np.argmax(e > e.max() - 10.0)) * 0.01, 2)
    return lc[key]
# A one-shot whose hit sits more than LEAD_MAX s into its file is trimmed so the hit lands on its cue (40 ms of lead kept).
# Whooshes are exempt by default: their build-up IS the sound, and their cues are already set 6-8 frames early.
LEAD_MAX = float(CF.get('lead_max', 0.3)); KEEP_LEAD = CF.get('keep_lead', ['whoosh', 'swoosh', 'swish'])
SFX_DUCK = CF.get('sfx_duck', 'threshold=0.1:ratio=2:attack=8:release=320')   # gentle: the measured gate below is the guarantee
MUSIC_DUCK = CF.get('music_duck', 'threshold=0.03:ratio=6:attack=60:release=400')   # a harder duck keeps the music fuller in the pauses
DUCK_LEAD = float(CF.get('duck_lead', 0.08))   # s: the music duck's key runs this far AHEAD of the voice (lookahead), so the bed clears in the pause before a word
for i, (name, f, vol, cut) in enumerate(CUES):
    p = os.path.join(SFX, f'{name}.mp3')
    if cut or not os.path.exists(p) or any(name.startswith(kl) for kl in KEEP_LEAD): continue
    ld = lead(p)
    if ld > LEAD_MAX:
        CUES[i] = (name, f, vol, round(ld - 0.04, 2)); print(f'sfx: {name}@f{f} hits {ld:.2f} s into its file: trimmed {ld - 0.04:.2f} s so the hit lands on its frame')
SPANS = {}                                # cue key -> (start s, end s, is ambience): which cues sound in a failing window
def build_stems(sfx_gain_db, mus_gain_db=0.0, cue_db=None):
    """voice.wav, music.wav (ducked) and sfx.wav (the SFX bus, ducked): 48 kHz mono, exactly the film's length.
    cue_db: per-cue gain in dB ({('c', i) or ('a', j): dB}), set by the gate so one loud cue only lowers itself."""
    cue_db = cue_db or {}
    ins = ['-i', os.path.join(V, 'voice.wav'), '-i', os.path.join(SFX, MUSIC['file'])]; ch = []; sfx = []; k = 2
    for i, (name, f, vol, cut) in enumerate(CUES):
        p = os.path.join(SFX, f'{name}.mp3')
        if not os.path.exists(p): print('missing sfx', name); continue
        g = SFX_LUFS - lufs(p) + cue_db.get(('c', i), 0.0); d = int((f - 1) / FPS * 1000); L = max(0.3, fdur(p) - (cut or 0.0) - (0.05 if cut else 0.25))
        if i in CUE_MAX: L = min(L, CUE_MAX[i])
        fo = min(0.35, L / 2); SPANS[('c', i)] = (d / 1000, d / 1000 + L, False, f'{name}@f{f}')
        trim = (f'atrim=start={cut},asetpts=PTS-STARTPTS,' if cut else '') + ('' if any(name.startswith(kl) for kl in KEEP_LEAD) else 'silenceremove=start_periods=1:start_threshold=-40dB,')
        ins += ['-i', p]
        ch.append(f'[{k}:a]aresample=48000,aformat=channel_layouts=mono,{trim}highpass=f=60,lowpass=f=9000,afade=t=in:d=0.015,'
                  f'afade=t=out:st={max(0.05, L - fo):.2f}:d={fo:.2f},volume={g:.2f}dB,volume={vol},adelay={d}|{d}[s{k}]'); sfx.append(f'[s{k}]'); k += 1
    for j, (name, f0, f1, vol) in enumerate(AMB):
        p = os.path.join(SFX, f'{name}.mp3')
        if not os.path.exists(p): print('missing amb', name); continue
        g = AMB_LUFS - lufs(p) + cue_db.get(('a', j), 0.0); span = ((f1 or nframes) - f0 + 1) / FPS; d = int((f0 - 1) / FPS * 1000)
        SPANS[('a', j)] = (d / 1000, d / 1000 + span, True, f'{name}@f{f0}')
        ins += ['-stream_loop', '-1', '-i', p]
        ch.append(f'[{k}:a]aresample=48000,aformat=channel_layouts=mono,atrim=0:{span:.2f},lowpass=f=10000,afade=t=in:d=0.4,afade=t=out:st={max(0.0, span - 0.5):.2f}:d=0.5,'
                  f'volume={g:.2f}dB,volume={vol},adelay={d}|{d}[s{k}]'); sfx.append(f'[s{k}]'); k += 1
    fc = ['[0:a]aresample=48000,aformat=channel_layouts=mono,apad,atrim=0:%.3f,asplit=3[vo][k1][k2]' % dur,
          f"[1:a]aresample=48000,aformat=channel_layouts=mono,atrim=start={HEAD:.3f},asetpts=PTS-STARTPTS{fit},volume={MUSIC.get('volume', 0.32)}"
          + (f",afade=t=in:d={MUSIC.get('fade_in', 0.6)}" if MUSIC.get('fade_in', 0.6) else '') + f",apad,atrim=0:{dur:.3f},afade=t=out:st={max(0.0, dur - 0.1):.2f}:d=0.1[mu]",
          (f'[k1]atrim=start={DUCK_LEAD:.3f},asetpts=PTS-STARTPTS,apad,atrim=0:{dur:.3f}[k1l]' if DUCK_LEAD > 0 else '[k1]anull[k1l]'),
          f'[mu][k1l]sidechaincompress={MUSIC_DUCK},volume={mus_gain_db:.2f}dB,apad,atrim=0:{dur:.3f}[duck]'] + ch
    if sfx:
        # amix starts its output at its FIRST input's first timestamp, and a WAV keeps no start offset: with the first cue at
        # f74 the whole bus played 2.43 s early (and cues before f74 were lost). A silent full-length first input pins it to 0.
        fc += [f'anullsrc=r=48000:cl=mono,atrim=0:{dur:.3f}[z0]',
               f"[z0]{''.join(sfx)}amix=inputs={len(sfx) + 1}:normalize=0,volume={sfx_gain_db:.2f}dB,apad,atrim=0:{dur:.3f}[sb]",
               f'[sb][k2]sidechaincompress={SFX_DUCK},apad,atrim=0:{dur:.3f}[sbd]']
    else: fc += ['[k2]anullsrc=r=48000:cl=mono,atrim=0:%.3f[sbd]' % dur]
    subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[vo]', '-ar', '48000', os.path.join(STEMS, 'voice.wav'),
                    '-map', '[duck]', '-ar', '48000', os.path.join(STEMS, 'music.wav'), '-map', '[sbd]', '-ar', '48000', os.path.join(STEMS, 'sfx.wav')], check=True)
    for s_ in ('voice', 'music', 'sfx'):                # a short stem means its content is shifted: never mix one
        w_ = _wave.open(os.path.join(STEMS, f'{s_}.wav')); n_ = w_.getnframes() / w_.getframerate()
        if abs(n_ - dur) > 0.005: raise SystemExit(f'stem {s_}.wav is {n_:.3f} s, the film is {dur:.3f} s: its audio is shifted (see the amix note)')

MUSIC_DIPS = {}                                         # window start (s) -> dB to lower the music around it (per-window ducking, cf. lesson 67)
def apply_music_dips():
    """multiply music.wav by a smooth gain curve: each dip covers its 400 ms window with 0.25 s ramps either side."""
    if not MUSIC_DIPS: return
    p = os.path.join(STEMS, 'music.wav'); w = _wave.open(p); sr = w.getframerate(); ch = w.getnchannels()
    x = _np.frombuffer(w.readframes(w.getnframes()), _np.int16).astype(_np.float32).reshape(-1, ch); w.close()
    t = _np.arange(len(x)) / sr; g = _np.zeros(len(x))
    for t0, d in MUSIC_DIPS.items():
        wgt = _np.clip((0.45 - _np.abs(t - (t0 + 0.2))) / 0.25, 0, 1); wgt = wgt * wgt * (3 - 2 * wgt); g = _np.minimum(g, -d * wgt)
    x = x * (10 ** (g / 20))[:, None]
    w = _wave.open(p, 'wb'); w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr); w.writeframes(_np.clip(x, -32768, 32767).astype(_np.int16).tobytes()); w.close()

def wav(path):
    w = _wave.open(path); x = _np.frombuffer(w.readframes(w.getnframes()), _np.int16).astype(_np.float32) / 32768; return x, w.getframerate()
def margin_report():
    """the voice's lead over the background in every 400 ms window where the voice speaks (RMS dB, 100 Hz high-passed)."""
    v, sr = wav(os.path.join(STEMS, 'voice.wav')); mu, _ = wav(os.path.join(STEMS, 'music.wav')); sf, _ = wav(os.path.join(STEMS, 'sfx.wav'))
    n = min(len(v), len(mu), len(sf)); hop = int(0.1 * sr); win = int(0.4 * sr)
    hp = lambda x: x - _np.convolve(x, _np.ones(int(sr / 100)) / int(sr / 100), 'same')
    v, mu, sf = hp(v[:n]), hp(mu[:n]), hp(sf[:n]); db = lambda x: 20 * _np.log10(_np.sqrt(_np.mean(x ** 2)) + 1e-9); lvs = []
    for i in range(0, n - win, hop):
        lvs.append((i / sr, db(v[i:i + win]), db(mu[i:i + win] + sf[i:i + win]), db(mu[i:i + win]), db(sf[i:i + win])))
    speech = _np.median([r[1] for r in lvs if r[1] > -45]) if lvs else -20.0             # the voice's typical speaking level
    return [(t, lv - lb, 'music' if lm >= ls else 'sfx', lv - ls) for t, lv, lb, lm, ls in lvs if lv > speech - 9.0]   # where it really speaks

sfx_gain, mus_gain = float(CF.get('sfx_gain_db', 0.0)), float(CF.get('music_gain_db', 0.0)); cue_db = {}
for it in range(14):
    build_stems(sfx_gain, mus_gain, cue_db); apply_music_dips(); rows = margin_report()
    srt = sorted(rows, key=lambda r: r[1]); worst = srt[:5]
    bad = srt[:max(1, int(len(srt) * 0.02))]; mn = bad[-1][1] if srt else 99.0      # 2nd percentile: one stray window can't hide a real problem
    smn = min((r[3] for r in rows), default=99.0)                                      # the SFX alone: the strict minimum
    print(f'mix pass {it + 1}: SFX {sfx_gain:+.1f} dB, music {mus_gain:+.1f} dB -> voice margin {mn:.1f} dB (need {VO_MARGIN:.0f}), SFX margin {smn:.1f} dB (need {SFX_MARGIN:.0f}); worst ' + ', '.join(f'{t:.1f}s={m:.1f} ({w})' for t, m, w, _ in worst))
    fails = [r for r in rows if r[3] < SFX_MARGIN]
    if fails:        # lower ONLY the cues sounding in a failing window (one-shots first): one loud cue no longer buries every hit
        need = {}
        for t, _, _, m in fails:
            on = [key for key, (a, b, amb, _) in SPANS.items() if a < t + 0.4 and b > t]
            for key in ([key for key in on if not SPANS[key][2]] or on): need[key] = max(need.get(key, 0.0), SFX_MARGIN - m + 0.5)
        if not need: sfx_gain -= (SFX_MARGIN - smn) + 0.5
        for key, d_ in need.items(): cue_db[key] = cue_db.get(key, 0.0) - d_
        continue
    if VO_MIN is not None:                                  # the strict floor: dip the music (or cut the cues) only where a window is short
        short = [r for r in rows if r[1] < float(VO_MIN)]
        if short:
            for t, m_, who, _ in short:
                if who == 'music': MUSIC_DIPS[round(t, 1)] = max(MUSIC_DIPS.get(round(t, 1), 0.0), MUSIC_DIPS.get(round(t, 1), 0.0) + float(VO_MIN) - m_ + 0.5)
                else:
                    for key in [key for key, (a, b, amb, _) in SPANS.items() if a < t + 0.4 and b > t]: cue_db[key] = cue_db.get(key, 0.0) - (float(VO_MIN) - m_ + 0.5)
            continue
    if mn >= VO_MARGIN: break
    fix = (VO_MARGIN - mn) + 1.0                                                        # lower whichever stem is the one overpowering the voice
    if sum(1 for r in bad if r[2] == 'sfx') >= sum(1 for r in bad if r[2] == 'music'): sfx_gain -= fix
    else: mus_gain -= fix
else: raise SystemExit(f'mix gate never passed: voice margin {mn:.1f} dB (need {VO_MARGIN:.0f}), SFX margin {smn:.1f} dB (need {SFX_MARGIN:.0f})')
if MUSIC_DIPS: print(f'mix: {len(MUSIC_DIPS)} per-window music dips (vo_min {VO_MIN} dB), deepest {max(MUSIC_DIPS.values()):.1f} dB at ' + ', '.join(f'{t_:.1f}s' for t_, d_ in sorted(MUSIC_DIPS.items(), key=lambda kv: -kv[1])[:5]))
vo_min_seen = min((r[1] for r in rows), default=99.0); print(f'mix: per-window minimum, voice over music + SFX: {vo_min_seen:.1f} dB')
if cue_db: print('mix: per-cue SFX cuts ' + ', '.join(f'{SPANS[k_][3]} {v_:+.1f} dB' for k_, v_ in sorted(cue_db.items(), key=lambda kv: SPANS[kv[0]][0])))
json.dump(lc, open(LCACHE, 'w'), indent=1)
# final: voice + background, loudness to -14 LUFS (measured, then a gain + true-peak limiter)
pre = os.path.join(STEMS, 'mix_pre.wav')
subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', os.path.join(STEMS, 'voice.wav'), '-i', os.path.join(STEMS, 'music.wav'), '-i', os.path.join(STEMS, 'sfx.wav'),
                '-filter_complex', '[0:a][1:a][2:a]amix=inputs=3:normalize=0[m]', '-map', '[m]', '-ar', '48000', pre], check=True)
m = re.findall(r'I:\s+(-?[\d.]+) LUFS', subprocess.run([FF, '-hide_banner', '-nostats', '-i', pre, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr)
g = -14.0 - (float(m[-1]) if m else -14.0)
mixf = os.path.join(STEMS, 'mix.wav')
subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', pre, '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:level=false', '-ar', '48000', '-ac', '2', mixf], check=True)
# HD players (QuickTime, browsers, YouTube) decode with the BT.709 matrix; ffmpeg's RGB->YUV default is BT.601, untagged,
# which darkens greens ~6 levels on playback. Convert with BT.709 and tag it (sRGB transfer, as the PNGs are).
cmd = [FF, '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(FPS), '-start_number', '1', '-i', os.path.join(FR, 'f%05d.png'), '-i', mixf,
       '-filter_complex', "[0:v]subtitles=captions.ass,scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p[v]", '-map', '[v]', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow',
       '-crf', '17', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'iec61966-2-1', '-color_range', 'tv', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', f'{dur:.3f}', '-movflags', '+faststart', OUT]
subprocess.run(cmd, check=True, cwd=os.path.dirname(assf))   # captions by bare name: a Windows drive colon or an apostrophe in the path breaks the filter
fin = re.findall(r'I:\s+(-?[\d.]+) LUFS', subprocess.run([FF, '-hide_banner', '-nostats', '-i', OUT, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr)
print('wrote', OUT, f'{dur:.2f} s', len(cards), 'captions', len(CUES), 'sfx', f'| {fin[-1] if fin else "?"} LUFS | voice margin {mn:.1f} dB, SFX margin {smn:.1f} dB')
