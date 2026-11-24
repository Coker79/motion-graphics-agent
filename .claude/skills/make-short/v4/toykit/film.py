"""toykit.film: timing + shots + rendering glue for a whole Short.

A film is a list of SETS. Each set is one Blender scene built by its own script (sets/<name>.py) and covers a frame
range of the global timeline; inside a set the acting is continuous and the camera CUTS between cameras on timeline
markers (one take, hidden cuts). Every frame is rendered with its global frame number, so the sets can render in
parallel and simply concatenate.

Timing comes from Whisper word timestamps (voice/voice.json): T.word('crack') -> frame where that word starts,
T.line(4) -> (first frame, last frame) of script line 4. Script lines live in script.txt (one sentence per line)."""
import bpy, json, math, os, re
from mathutils import Vector

FPS = 30


def _norm(w):
    return re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))


NUM = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten'}


def _toks(text):
    out = []
    for t in re.findall(r"[A-Za-z0-9$%'’-]+", text):
        n = _norm(t)
        out.append(NUM.get(n, n))
    return out


class Timing:
    """word timing from Whisper JSON, aligned to the script (one sentence per line) with a sequence match, so a split
    word ("hard tack"), a digit ("10" for "ten") or a mis-heard word doesn't shift the lines after it. Each script word
    gets a start/end (captions use the script's own spelling)."""

    def __init__(self, whisper_json, script_txt=None, fps=FPS, lead=0):
        import difflib
        j = json.load(open(whisper_json)); self.fps = fps; self.lead = lead
        self.words = [dict(w=w['word'].strip(), s=float(w['start']), e=float(w['end'])) for seg in j['segments'] for w in seg.get('words', [])]
        self.duration = self.words[-1]['e'] if self.words else 0.0
        self.lines = []
        if script_txt and os.path.exists(script_txt):
            L = [re.sub(r'^>[TX]', '', l.strip()) for l in open(script_txt) if l.strip()]
            stoks, owner, raw = [], [], []
            for n, line in enumerate(L):
                for t, r in zip(_toks(line), re.findall(r"[A-Za-z0-9$%'’-]+", line)): stoks.append(t); owner.append(n); raw.append(r)
            wt = [NUM.get(_norm(w['w']), _norm(w['w'])) for w in self.words]
            # glue whisper splits that the script writes as one word (hard + tack -> hardtack)
            sm = difflib.SequenceMatcher(None, stoks, wt, autojunk=False); m = {}
            for a, b, size in sm.get_matching_blocks():
                for k in range(size): m[a + k] = b + k
            for i in range(len(stoks)):              # a script word heard as two tokens ("knee-deep" -> "knee" "deep"): the first one
                if i in m: continue
                lo = max([k for k in m if k < i], default=None); j0 = (m[lo] + 1) if lo is not None else 0
                for jj in range(j0, min(j0 + 3, len(wt) - 1)):
                    if (wt[jj] + wt[jj + 1]).replace('-', '') == stoks[i].replace('-', ''): m[i] = jj; break
            for i in range(len(stoks)):              # unmatched script words: interpolate between matched neighbours
                if i in m: continue
                lo = max([k for k in m if k < i], default=None); hi = min([k for k in m if k > i], default=None)
                if lo is not None and hi is not None and m[hi] - m[lo] > 1:
                    m[i] = m[lo] + max(1, round((i - lo) * (m[hi] - m[lo]) / (hi - lo)))
                    m[i] = min(m[i], m[hi] - 1)
                else: m[i] = m.get(lo, m.get(hi, 0)) if lo is not None or hi is not None else 0
            self.sw = []
            for i, t in enumerate(stoks):
                w = self.words[min(m[i], len(self.words) - 1)]
                nxt = m.get(i + 1); e = w['e']
                if nxt is not None and nxt > m[i] + 1: e = self.words[nxt - 1]['e']       # the script word spans a whisper split
                self.sw.append(dict(w=raw[i], s=w['s'], e=e, line=owner[i] + 1))
            for n, line in enumerate(L):
                ws = [w for w in self.sw if w['line'] == n + 1]
                self.lines.append(dict(n=n + 1, text=line, s=ws[0]['s'] if ws else None, e=ws[-1]['e'] if ws else None, words=ws))
            hit = {a + k for a, b, size in sm.get_matching_blocks() for k in range(size)}
            heard = set(wt) | {a + b for a, b in zip(wt, wt[1:])}          # 'knee' + 'deep' heard for 'knee-deep'
            VAR = {'dike': 'dyke', 'dyke': 'dike'}
            miss = [raw[i] for i in range(len(stoks)) if i not in hit and stoks[i].replace('-', '') not in heard
                    and VAR.get(stoks[i]) not in heard and stoks[i].replace("'", '') not in {w.replace("'", '') for w in wt}]
            if len(miss) > 3: print(f'toykit.film WARNING: {len(miss)} script words not heard in the recording: {miss[:12]}: check the take')

    def f(self, sec):
        return int(round(sec * self.fps)) + self.lead

    def word(self, text, nth=0, after=0.0, end=False):
        """frame where the nth occurrence of `text` (after `after` seconds) starts (or ends)."""
        t = _norm(text); k = 0
        if after == 0.0 and nth == 0:                           # an unscoped word that is in several lines: say which one wins
            hits = sorted({l['n'] for l in self.lines for w in l['words'] if _norm(w['w']) == t or _norm(w['w']).startswith(t)})
            amb = self.__dict__.setdefault('_amb', set())
            if len(hits) > 1 and t not in amb:
                amb.add(t); print(f"TIMING WARNING: W({text!r}) is in lines {hits}; line {hits[0]} wins. Pass after=(S(n) - 1) / 30.0 to pick line n.")
        for w in self.words:
            if w['s'] < after: continue
            if _norm(w['w']) == t or _norm(w['w']).startswith(t):
                if k == nth: return self.f(w['e'] if end else w['s'])
                k += 1
        raise KeyError(f'word not in the recording: {text!r} (nth={nth})')

    def line(self, n):
        l = self.lines[n - 1]; return self.f(l['s']), self.f(l['e'])

    def words_of(self, n):
        """[(start_s, end_s, text)] of script line n (for Face.talk)."""
        return [(w['s'] + self.lead / self.fps, w['e'] + self.lead / self.fps, w['w']) for w in self.lines[n - 1]['words']]

    def all_words(self):
        src = getattr(self, 'sw', None) or self.words
        return [(w['s'] + self.lead / self.fps, w['e'] + self.lead / self.fps, w['w']) for w in src]

    def dump(self, path):
        json.dump(dict(fps=self.fps, lead=self.lead, duration=self.duration, lines=[dict(n=l['n'], text=l['text'], s=l['s'], e=l['e'],
                       words=[dict(w=w['w'], s=w['s'], e=w['e']) for w in l['words']]) for l in self.lines]), open(path, 'w'), indent=1)


def cut(sc, frame, cam_obj, name=None):
    """hard cut to `cam_obj` at `frame` (timeline marker bound to the camera)."""
    m = sc.timeline_markers.new(name or f'cut_{frame}', frame=frame); m.camera = cam_obj; return m


def render_range(sc, out_dir, f0, f1, step=1, only=None, mb_steps=None):
    """mb_steps: {frame: motion-blur steps} for frames that need more, e.g. {f: 64 for f in P.move_starts()}: a frame
    whose shutter straddles a whip's start renders as stepped ghost copies at 16 steps, and a smooth smear at 64 (lesson 68)."""
    os.makedirs(out_dir, exist_ok=True); frames = range(f0, f1 + 1, step) if only is None else only; base = sc.eevee.motion_blur_steps   # [] = render nothing
    for f in frames:
        sc.eevee.motion_blur_steps = max(base, (mb_steps or {}).get(f, base))
        sc.frame_set(f); sc.render.filepath = os.path.join(out_dir, f'f{f:05d}.png'); bpy.ops.render.render(write_still=True)
    sc.eevee.motion_blur_steps = base


def args_after_dashes():
    import sys
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def frames_arg(spec, f0, f1):
    """'all' | '120' | '120,180' | '100-160' | 'every:6' -> frames clipped to the set's range."""
    if spec in (None, '', 'all'): return list(range(f0, f1 + 1))
    if spec.startswith('every:'): return list(range(f0, f1 + 1, int(spec[6:])))
    if '-' in spec and ':' in spec:                                   # 'A-B:2' -> every 2nd frame of A..B, phase anchored at f0
        rng, st = spec.split(':'); a, b = (int(x) for x in rng.split('-')); st = int(st)
        return [f for f in range(a + ((f0 - a) % st), b + 1, st) if f0 <= f <= f1]
    if '-' in spec and ',' not in spec:
        a, b = (int(x) for x in spec.split('-')); return [f for f in range(a, b + 1) if f0 <= f <= f1]
    return [int(x) for x in spec.split(',') if f0 <= int(x) <= f1]


# ---------------------------------------------------------------- camera move presets (all eased at both ends)
def orbit_points(center, radius, az0, az1, z, n=3):
    """positions on an arc around `center` (degrees; az 0 = in front of a character facing -Y)."""
    c = Vector(center); out = []
    for i in range(n):
        a = math.radians(az0 + (az1 - az0) * i / (n - 1)); out.append(c + Vector((math.sin(a) * radius, -math.cos(a) * radius, 0)) + Vector((0, 0, z - c.z)))
    return out


def push(cam, f0, f1, pos0, pos1, aim0, aim1, lens0=None, lens1=None):
    cam.key(f0, pos=pos0, aim=aim0, lens=lens0); cam.key(f1, pos=pos1, aim=aim1, lens=lens1); return cam


def slam_creep(cam, f0, f1, far, near, aim, creep=0.06, slam=6, lens=None):
    """the reference's landing: a fast move (`slam` frames) into `near`, then a slow creep forward for the rest."""
    near = Vector(near); far = Vector(far); d = (near - far).normalized()
    cam.key(f0, pos=far, aim=aim, lens=lens); cam.key(f0 + slam, pos=near, aim=aim)
    cam.key(f1, pos=near + d * creep, aim=aim)
    return cam


# ---------------------------------------------------------------- cutting: jumps at cuts never smear (keys at f-0.6 / f-0.5)
def _const_before(idb, path, f):
    """make the key at frame f (on idb.path) CONSTANT so the value jumps to the next key."""
    from .camera import fcurves
    for fc in fcurves(idb):
        if fc.data_path != path: continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - f) < 1e-3: kp.interpolation = 'CONSTANT'


def value_at(idb, path, frame, fallback):
    """the ANIMATED value of idb.path at `frame` (per array index; falls back to the given current value): the key
    before a cut must hold where the character really is, not whatever Python last wrote into the property."""
    from .camera import fcurves
    fcs = {fc.array_index: fc for fc in fcurves(idb) if fc.data_path == path}
    try: n = len(fallback)
    except TypeError: return fcs[0].evaluate(frame) if 0 in fcs else fallback
    return type(fallback)([fcs[i].evaluate(frame) if i in fcs else fallback[i] for i in range(n)])


def jump_obj(obj, f, **props):
    """set object properties (location, rotation_euler) with a hard jump at cut frame f (keys at f-0.6 and f-0.5).
    rc3: the f-0.6 key holds the CURVE's value there (value_at), not whatever Python last wrote (lesson 83)."""
    for k, v in props.items():
        setattr(obj, k, value_at(obj, k, f - 0.6, getattr(obj, k))); obj.keyframe_insert(k, frame=f - 0.6); setattr(obj, k, v); obj.keyframe_insert(k, frame=f - 0.5)
        _const_before(obj, k, f - 0.6)


def step_prop(o, prop, f, v):
    """switch a custom property (e.g. an effect's o['amp']) to v at frame f: keys at f-0.6 (the curve's OWN value there) and
    f-0.5 (v). Never key `o[prop]` as found: any frame_set() since (hand_point, bone_pos...) left the value of some other frame
    in it, and the curve then RAMPS toward that stale value for hundreds of frames (pineapple pit: a dawn shot filled with
    smoke, lesson 83)."""
    o[prop] = value_at(o, f'["{prop}"]', f - 0.6, o[prop]); o.keyframe_insert(f'["{prop}"]', frame=f - 0.6)
    o[prop] = v; o.keyframe_insert(f'["{prop}"]', frame=f - 0.5)


def step_socket(sock, f, v):
    """the same step for a node-socket value (a material's frost amount, an effect strength): keys on its node tree."""
    sock.default_value = value_at(sock.id_data, sock.path_from_id('default_value'), f - 0.6, sock.default_value)
    sock.keyframe_insert('default_value', frame=f - 0.6); sock.default_value = v; sock.keyframe_insert('default_value', frame=f - 0.5)


FRAMING = {   # size: (lens, vertical metres visible, aim height mode)
    'ECU': (55, 0.50, 'face'), 'CU': (45, 0.62, 'face'), 'MCU': (40, 0.95, 'chest'), 'MS': (35, 1.45, 'body'), 'WS': (30, 2.8, 'body'),
}


def framing(ch, root, size='MCU', az=0.0, el=4.0, off=(0, 0, 0), lens=None):
    """camera (pos, aim, lens) for a character standing at root=(x, y, yaw_deg): az 0 = in front of its face."""
    L, vis, mode = FRAMING[size]; L = lens or L
    fov = 2 * math.atan(18 / L); d = vis / (2 * math.tan(fov / 2))
    if mode == 'face': d += ch.spec['head']['d'] * 0.5          # measure face shots from the face surface, not the head centre
    x, y, yaw = root; hz = ch.spec['head']['z']
    tz = {'face': hz - 0.02, 'chest': hz - 0.22, 'body': hz * 0.62}[mode]
    a = math.radians(yaw + az); e = math.radians(el)
    fwd = Vector((math.sin(a), -math.cos(a), 0))
    aim = Vector((x, y, tz)) + Vector(off)
    pos = aim + fwd * d * math.cos(e) + Vector((0, 0, d * math.sin(e)))
    return pos, aim, L


class Shots:
    """one camera; each shot = eased move from `a` to `b` (dicts pos/aim/lens), hard jump between shots."""

    def __init__(self, cam):
        self.cam = cam; self.list = []

    def add(self, f0, f1, a, b=None, name='', shake=0.0):
        b = b or a; self.list.append(dict(f0=f0, f1=f1, a=a, b=b, name=name, shake=shake)); return self

    def build(self):
        c = self.cam; first = True
        for s in sorted(self.list, key=lambda s: s['f0']):
            f0, f1, a, b = s['f0'], s['f1'], s['a'], s['b']
            if first:
                c.key(f0, pos=a['pos'], aim=a['aim'], lens=a.get('lens')); first = False
            else:
                for o, k, v in ((c.cam, 'location', a['pos']), (c.aim, 'location', a['aim'])):
                    o.keyframe_insert(k, frame=f0 - 0.6); setattr(o, k, v); o.keyframe_insert(k, frame=f0 - 0.5); _const_before(o, k, f0 - 0.6)
                if a.get('lens'):
                    c.cam.data.keyframe_insert('lens', frame=f0 - 0.6); c.cam.data.lens = a['lens']; c.cam.data.keyframe_insert('lens', frame=f0 - 0.5)
                    _const_before(c.cam.data, 'lens', f0 - 0.6)
            c.key(f1, pos=b['pos'], aim=b['aim'], lens=b.get('lens', a.get('lens')))
        return self

    def at(self, f):
        for s in self.list:
            if s['f0'] <= f <= s['f1']: return s
        return None


# ---------------------------------------------------------------- camera v2: a continuous path in the reference's grammar
class CamPath:
    """One camera that never stops. Moves land on sentence starts:
      slam(f, ...)        fast move that brakes HARD into the pose at f (EXPO ease-out, ~10-14 f), then creeps on
      push(f0, f1, ...)   long S-curve push (ease both ends)
      orbit(f0, f1, ...)  eased arc around a point (a key every frame)
      whip(f, ...)        very fast aim swing (6-8 f) ending at f; teleports can hide at its blurriest frame (f - dur//2)
      cut(f, ...)         a true hard cut (keep to 2-3 per film)
    After every landing the camera keeps creeping along its last direction (creep=fraction of the move per beat); the creep
    ACCELERATES out of the landing (ease-in), as measured on the reference (1 -> 8 px/frame over ~18 frames).
      exit(f0, f1, ...)   whip OUT that is still at full speed on the set's last frame (the next set starts mid-whip)
      shake(f, dur, amp)  impact shake on the aim"""

    def __init__(self, cam, creep=0.10):
        self.cam = cam; self.keys = []; self.creep = creep; self.shakes = []        # keys: dict(f, pos, aim, lens, style)

    def _last(self):
        return self.keys[-1] if self.keys else None

    def start(self, f, pos, aim, lens):
        self.keys.append(dict(f=f, pos=Vector(pos), aim=Vector(aim), lens=lens, style='creep')); return self

    def _creep_to(self, f):
        """insert the creep end of the previous landing at frame f: a slow DOLLY-IN toward the aim (creep x the shot distance
        per 45 frames), plus a little drift along the last move. v4.1: the old creep only continued the last move and
        capped at a few cm, which left 28-50 f near-still holds between moves (critic r2)."""
        k = self._last()
        if k is None or f <= k['f'] + 1: return
        prev = self.keys[-2] if len(self.keys) > 1 else None
        tf = min(1.0, (f - k['f']) / 45)
        v = k['aim'] - k['pos']; dist = v.length; fwd = v.normalized() if dist > 1e-6 else Vector((0, 1, 0))
        d = (k['pos'] - prev['pos']) if prev else Vector((0, 0, 0))
        lat = d - fwd * d.dot(fwd)
        drift = lat.normalized() * min(0.05, lat.length * 0.06) * tf if lat.length > 1e-6 else Vector((0, 0, 0))
        dp = fwd * (dist * self.creep * tf) + drift
        da = (k['aim'] - prev['aim']) if prev else Vector((0, 0, 0))
        da = da.normalized() * min(0.03, da.length * 0.05) * tf if da.length > 1e-6 else da
        self.keys.append(dict(f=f, pos=k['pos'] + dp, aim=k['aim'] + da, lens=(k['lens'] or 35) * (1.0 + 0.02 * tf), style='creep'))

    def _warn_start(self, kind, f_start, f_land, planned):
        """rc3: a move STARTS from the previous key. If the previous call's last key sits past this move's planned start,
        the move silently shrinks (a push ending inside a whip window turns an 8-frame whip into a 1-2 frame POP)."""
        k = self._last()
        if k is None: return
        if k['f'] >= f_land: print(f'CAMWARN {kind} landing f{f_land:.0f}: the previous key is at f{k["f"]:.0f} (calls out of time order: the camera snaps back)')
        elif k['f'] > f_start + 1: print(f'CAMWARN {kind} f{f_start:.0f}-{f_land:.0f}: starts late at f{k["f"]:.0f} (the previous move ends inside its window): {f_land - k["f"]:.0f} frames instead of {planned:.0f}')

    def slam(self, f, pos, aim, lens=None, dur=12):
        self._warn_start('slam/whip', f - dur, f, dur)
        self._creep_to(f - dur); self._last()['style'] = 'slam'
        self.keys.append(dict(f=f, pos=Vector(pos), aim=Vector(aim), lens=lens or self._last()['lens'], style='creep')); return self

    def whip(self, f, pos, aim, lens=None, dur=7):
        return self.slam(f, pos, aim, lens, dur)

    def move_starts(self):
        """frames whose shutter straddles the START of a slam or whip (still for half the shutter, then ~75% of the move):
        render them with many motion-blur steps: render_range(..., mb_steps={f: 64 for f in P.move_starts()})."""
        return sorted({int(round(k['f'])) for k in self.keys if k['style'] == 'slam'})   # slam() tags its START key 'slam'

    def push(self, f0, f1, pos, aim, lens=None):
        self._warn_start('push', f0, f1, f1 - f0)
        self._creep_to(f0); self._last()['style'] = 'push'
        self.keys.append(dict(f=f1, pos=Vector(pos), aim=Vector(aim), lens=lens or self._last()['lens'], style='creep')); return self

    def orbit(self, f0, f1, center, radius, az0, az1, z, lens=None, aim_z=None, n=None):
        """eased arc round `center` toward az1 degrees (0 = the -Y side). It always STARTS where the camera is (its azimuth,
        radius, height, aim and lens are read from the last key) and blends to the requested radius/height/aim, so an arc
        can never pop or start the wrong way (v4.1: three orbits jumped 4-18 cm on their first frame). az0 is advisory."""
        self._warn_start('orbit', f0, f1, f1 - f0)
        self._creep_to(f0); c = Vector(center); n = n or max(3, f1 - f0)          # a key every frame: rounding //2 keys left 3-frame gaps (stutter mid-arc)
        k = self._last(); az_z = c.z if aim_z is None else aim_z; aim_end = Vector((c.x, c.y, az_z))
        d = k['pos'] - c; a_s = math.degrees(math.atan2(d.x, -d.y)); r_s = Vector((d.x, d.y)).length; z_s = k['pos'].z
        a_e = az1 if abs(az1 - a_s) <= 180 else az1 + 360 * round((a_s - az1) / 360)
        lens_s = k['lens'] or lens or 35; lens_e = lens or lens_s
        if k['f'] < f0: self.keys.append(dict(f=f0, pos=k['pos'].copy(), aim=k['aim'].copy(), lens=lens_s, style='linear'))
        else: k['style'] = 'linear'
        for i in range(1, n + 1):
            t = i / n; s_ = t * t * (3 - 2 * t); a = math.radians(a_s + (a_e - a_s) * s_); r = r_s + (radius - r_s) * s_
            p = Vector((c.x + math.sin(a) * r, c.y - math.cos(a) * r, z_s + (z - z_s) * s_))
            self.keys.append(dict(f=int(round(f0 + (f1 - f0) * t)), pos=p, aim=k['aim'].lerp(aim_end, s_), lens=lens_s + (lens_e - lens_s) * s_,
                                  style='linear' if i < n else 'creep'))
        return self

    def exit(self, f0, f1, pos, aim, lens=None):
        """accelerating whip out (EXPO ease-in) that is still at full speed on frame f1 (the set's last frame)."""
        self._warn_start('exit', f0, f1, f1 - f0)
        self._creep_to(f0); self._last()['style'] = 'exit'
        self.keys.append(dict(f=f1, pos=Vector(pos), aim=Vector(aim), lens=lens or self._last()['lens'], style='creep')); return self

    def shake(self, f, dur=7, amp=0.012, scale=2.0):
        self.shakes.append((f, dur, amp, scale)); return self

    def cut(self, f, pos, aim, lens=None):
        self._creep_to(f - 1); self._last()['style'] = 'cut'
        self.keys.append(dict(f=f, pos=Vector(pos), aim=Vector(aim), lens=lens or self._last()['lens'], style='creep', after_cut=True)); return self

    def build(self, end=None):
        if end: self._creep_to(end)
        c = self.cam; from .camera import fcurves
        ks = sorted(self.keys, key=lambda k: k['f'])
        for i, k in enumerate(ks):
            if k.get('after_cut'):
                # hard cut: hold the previous pose up to f-0.6, jump at f-0.5 (no motion-blur smear)
                p = ks[i - 1]
                for o, attr, v in ((c.cam, 'location', p['pos']), (c.aim, 'location', p['aim'])):
                    setattr(o, attr, v); o.keyframe_insert(attr, frame=k['f'] - 0.6)
                c.cam.data.lens = p['lens']; c.cam.data.keyframe_insert('lens', frame=k['f'] - 0.6)
                c.key(k['f'] - 0.5, pos=k['pos'], aim=k['aim'], lens=k['lens'])
            c.key(k['f'], pos=k['pos'], aim=k['aim'], lens=k['lens'])
        # per-segment interpolation, set on the key that STARTS each segment
        style_at = {}
        for i, k in enumerate(ks):
            style_at[round(k['f'], 2)] = k['style']
            if k.get('after_cut'): style_at[round(k['f'] - 0.6, 2)] = 'const'; style_at[round(k['f'] - 0.5, 2)] = 'linear'
        for idb in (c.cam, c.aim, c.cam.data):
            for fc in fcurves(idb):
                for kp in fc.keyframe_points:
                    st = style_at.get(round(kp.co.x, 2), 'creep')
                    kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
                    if st == 'slam': kp.interpolation = 'EXPO'; kp.easing = 'EASE_OUT'
                    elif st == 'push': kp.interpolation = 'BEZIER'
                    elif st == 'const': kp.interpolation = 'CONSTANT'
                    elif st == 'exit': kp.interpolation = 'EXPO'; kp.easing = 'EASE_IN'
                    elif st in ('linear', 'creep'): kp.interpolation = 'SINE' if st == 'creep' else 'LINEAR'; kp.easing = 'EASE_IN' if st == 'creep' else 'AUTO'
                fc.update()
        for f, dur, amp, scale in self.shakes:
            for idb, a in ((c.aim, amp), (c.cam, amp * 0.35)):
                for fc in fcurves(idb):
                    if fc.data_path != 'location': continue
                    m = fc.modifiers.new('NOISE'); m.scale = scale; m.strength = a; m.phase = f * 1.7 + fc.array_index * 5.3
                    m.use_restricted_range = True; m.frame_start, m.frame_end = f, f + dur; m.blend_in = 0; m.blend_out = max(1, dur - 2)
        return self

    def hidden_cuts(self):
        """frames at the blurriest point of each whip/slam (teleport characters here instead of hard-cutting)."""
        ks = sorted(self.keys, key=lambda k: k['f']); out = []
        for a, b in zip(ks, ks[1:]):
            if a['style'] == 'slam' and (b['pos'] - a['pos']).length > 0.6: out.append(a['f'] + max(1, (b['f'] - a['f']) // 4))
        return out
