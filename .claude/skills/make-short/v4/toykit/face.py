"""toykit.face (v2): expressive cartoon faces as shape-keyed decals wrapped onto the head.

Every feature is a STRIP between a top and a bottom curve (M columns) drawn in the head's front plane (x right, z up,
head-local metres) and projected onto a hidden proxy of the head with a Shrinkwrap (PROJECT along +Y), so the face
follows squash/stretch and head turns. All shapes of a feature share topology, so expressions morph via shape keys.

Eye = sclera (the OPEN area: the lids are part of its shape) + pupil + highlight, then lid lines (ink) and skin
covers drawn ABOVE the pupil: they clip the pupil to the eye opening and give the upper lid a heavier line. A closed
eye is a zero-height sclera whose two lid lines meet as one clean stroke (blink, ^^ joy).
Layer offsets from the skin (m): sclera .0024 < pupil .0032 < highlight .0040 < lid lines + covers .0050 < freckles
.0056 < brow ink .0060 < brow .0068.  Mouth: ink .0016 < mouth .0024 < clenched teeth .0034.
Face spec values are in units of the head WIDTH, z measured from the head centre (see specs/*.json)."""
import bpy, bmesh, math

M = 28            # columns per feature
TARGET = {}       # head name -> shrinkwrap target (clean proxy of the head surface)
STEP = 0.0045     # max row spacing (m): decal strips are subdivided so their chords hug the curved head


# ---------------------------------------------------------------- 2D curves (x, z)
def xs_cos(m=M):
    return [-math.cos(math.pi * i / (m - 1)) for i in range(m)]          # dense at the ends: smooth tips


def ellipse_tb(cx, cz, rx, rz, m=M):
    xs = xs_cos(m)
    top = [(cx + rx * x, cz + rz * math.sqrt(max(0.0, 1 - x * x))) for x in xs]
    bot = [(cx + rx * x, cz - rz * math.sqrt(max(0.0, 1 - x * x))) for x in xs]
    return top, bot


def eye_tb(cx, cz, rx, rz, side, upper=None, lower=None, closed=None, m=M):
    """eye OPENING for a lid state. upper/lower = (c, t, k): lid edge z = c + t*v + k*u^2 in units of rz, where u runs
    -1..1 across the eye and v = -u*side is +1 at the INNER corner (nose side), -1 at the outer corner.
    closed(u) -> z: a fully closed eye (top == bottom), drawn as one stroke by the lid lines."""
    top, bot = [], []
    for u in xs_cos(m):
        s = math.sqrt(max(0.0, 1 - u * u)); zt, zb = s, -s
        if closed is not None:
            zt = zb = closed(u)
        else:
            v = -u * side
            if upper: c, t, k = upper; zt = min(zt, c + t * v + k * u * u)
            if lower: c, t, k = lower; zb = max(zb, c + t * v + k * u * u)
            if zt < zb: zt = zb = 0.5 * (zt + zb)
        top.append((cx + rx * u, cz + rz * zt)); bot.append((cx + rx * u, cz + rz * zb))
    return top, bot


def brow_tb(p3, thick, taper=0.55, m=M):
    (x0, z0), (x1, z1), (x2, z2) = p3; top, bot = [], []
    for i in range(m):
        u = i / (m - 1)
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * x1 + u * u * x2; z = (1 - u) ** 2 * z0 + 2 * (1 - u) * u * z1 + u * u * z2
        dx = 2 * (1 - u) * (x1 - x0) + 2 * u * (x2 - x1); dz = 2 * (1 - u) * (z1 - z0) + 2 * u * (z2 - z1)
        ln = math.hypot(dx, dz) or 1.0; nx, nz = -dz / ln, dx / ln
        if nz < 0: nx, nz = -nx, -nz
        w = thick * (1 - (1 - taper) * u) * (math.sin(math.pi * u) ** 0.42) * (0.85 + 0.15 * math.cos(math.pi * (u - 0.35)))
        w = max(w, thick * 0.12)
        top.append((x + nx * w / 2, z + nz * w / 2)); bot.append((x - nx * w / 2, z - nz * w / 2))
    return top, bot


def curves_tb(cx, cz, hw, h, top_fn, bot_fn, m=M):
    xs = xs_cos(m)
    top = [(cx + hw * x, cz + h * top_fn(x)) for x in xs]
    bot = [(cx + hw * x, cz + h * min(top_fn(x), bot_fn(x))) for x in xs]
    return top, bot


def dilate(top, bot, d_top, d_bot=None):
    """outward offset of the closed outline top(L->R) + bot(R->L): top verts by d_top, bottom verts by d_bot."""
    d_bot = d_top if d_bot is None else d_bot
    poly = top + bot[::-1]; n = len(poly); m = len(top)
    area = 0.5 * sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = -1.0 if area > 1e-12 else 1.0; out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        e = (c[0] - a[0], c[1] - a[1]); ln = math.hypot(*e); d = d_top if i < m else d_bot
        if ln < 1e-12: out.append(b); continue
        nx, nz = -e[1] / ln, e[0] / ln
        out.append((b[0] + sgn * nx * d, b[1] + sgn * nz * d))
    for it, ib in ((0, n - 1), (m - 1, m)):          # tips: poly index of top end / bottom end at the same column
        if math.hypot(poly[it][0] - poly[ib][0], poly[it][1] - poly[ib][1]) < 1e-9:
            dt, db = d_top, d_bot; p0 = poly[it]
            vx = (out[it][0] - p0[0]) / (dt or 1) + (out[ib][0] - p0[0]) / (db or 1); vz = (out[it][1] - p0[1]) / (dt or 1) + (out[ib][1] - p0[1]) / (db or 1)
            ln = math.hypot(vx, vz)
            if ln > 1e-9:
                dd = 0.5 * (dt + db); q = (p0[0] + vx / ln * dd, p0[1] + vz / ln * dd); out[it] = q; out[ib] = q
    return out[:m], out[m:][::-1]


def scale_tb(tb, cx, cz, sx, sz):
    t, b = tb; f = lambda p: (cx + (p[0] - cx) * sx, cz + (p[1] - cz) * sz); return [f(p) for p in t], [f(p) for p in b]


# ---------------------------------------------------------------- decal builder
def decal(name, head, shapes, mats, rows, y_plane, offset, parent=None, target=None, coll=None):
    """shapes: {key: (top, bot)} (first key = basis). rows: [(frac0, frac1, mat_index)] from top (0) to bottom (1);
    each row band is subdivided so no chord is longer than STEP (keeps the strip on the curved surface)."""
    keys = list(shapes)
    H = max(math.hypot(xt - xb, zt - zb) for tb in shapes.values() for (xt, zt), (xb, zb) in zip(*tb))
    fine = []
    for a, b, mi in rows:
        k = max(1, int(math.ceil((b - a) * H / STEP)))
        fine += [(a + (b - a) * j / k, a + (b - a) * (j + 1) / k, mi) for j in range(k)]
    fr = sorted({round(r[0], 6) for r in fine} | {round(r[1], 6) for r in fine})
    def verts(tb):
        top, bot = tb; out = []
        for (xt, zt), (xb, zb) in zip(top, bot):
            for f in fr: out.append((xt + (xb - xt) * f, zt + (zb - zt) * f))
        return out
    m = len(shapes[keys[0]][0]); nf = len(fr)
    bm = bmesh.new(); V = [bm.verts.new((x, y_plane, z)) for (x, z) in verts(shapes[keys[0]])]
    for i in range(m - 1):
        for (a, b, mi) in fine:
            ia, ib = fr.index(round(a, 6)), fr.index(round(b, 6))
            f = bm.faces.new((V[i * nf + ia], V[(i + 1) * nf + ia], V[(i + 1) * nf + ib], V[i * nf + ib])); f.material_index = mi
    for f in bm.faces:
        f.normal_update()
        if f.normal.y > 0: f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); (coll or bpy.context.scene.collection).objects.link(o)
    for mt in mats: me.materials.append(mt)
    o.parent = parent or head
    o.shape_key_add(name='Basis', from_mix=False)
    for k in keys[1:]:
        sk = o.shape_key_add(name=k, from_mix=False); sk.value = 0.0      # Blender 5 adds new keys at 1.0
        for i, (x, z) in enumerate(verts(shapes[k])): sk.data[i].co = (x, y_plane, z)
    md = o.modifiers.new('wrap', 'SHRINKWRAP'); md.target = target or TARGET.get(head.name, head); md.wrap_method = 'PROJECT'
    md.use_project_y = True; md.use_positive_direction = True; md.use_negative_direction = False
    md.wrap_mode = 'ON_SURFACE'; md.offset = offset; md.cull_face = 'BACK'
    fb = o.modifiers.new('wrap_fallback', 'SHRINKWRAP'); fb.target = md.target; fb.wrap_method = 'NEAREST_SURFACEPOINT'
    fb.wrap_mode = 'ON_SURFACE'; fb.offset = offset          # a ray that misses the head leaves its vertex in mid-air: snap it
    for p in me.polygons: p.use_smooth = True
    o.visible_shadow = False
    return o


# ---------------------------------------------------------------- libraries
LIDS = {   # eye-opening states; 'open' is the basis
    'open':   {},
    'half':   dict(upper=(0.12, 0.0, -0.10)),
    'angry':  dict(upper=(0.32, -0.62, 0.0)),
    'sad':    dict(upper=(0.40, 0.50, 0.0)),
    'squint': dict(upper=(0.30, -0.30, 0.0), lower=(-0.42, 0.0, 0.20)),
    'happy':  dict(lower=(-0.30, 0.0, -0.42)),
    'closed': dict(closed=lambda u: -0.10 - 0.30 * (1 - u * u)),
    'joy':    dict(closed=lambda u: -0.32 + 0.66 * (1 - u * u) ** 0.75),
}
SHUT = ('closed', 'joy')

BROWS = {  # (inner, mid, outer) points in units of brow length: x outward from the nose, z up
    'neutral': ((0.0, 0.00), (0.5, 0.13), (1.0, -0.03)),
    'up':      ((0.0, 0.26), (0.5, 0.42), (1.0, 0.20)),
    'angry':   ((0.06, -0.24), (0.5, -0.02), (1.0, 0.16)),
    'sad':     ((0.0, 0.26), (0.5, 0.18), (1.0, -0.14)),
    'focus':   ((0.04, -0.10), (0.5, 0.04), (1.0, 0.02)),
    'raise1':  ((0.0, 0.16), (0.5, 0.40), (1.0, 0.26)),
}

S_ = lambda x: math.sqrt(max(0.0, 1 - x * x))
MOUTHS = {  # name: (half-width scale, top(x), bottom(x)) in units of the mouth height; 'neutral' is the basis
    'neutral': (1.00, lambda x: -0.22 * (1 - x * x), lambda x: -0.22 * (1 - x * x)),
    'flat':    (0.80, lambda x: -0.02 * (1 - x * x), lambda x: -0.02 * (1 - x * x)),
    'smile':   (1.12, lambda x: -0.42 * (1 - x * x), lambda x: -0.42 * (1 - x * x)),
    'open':    (1.15, lambda x: -0.10 * (1 - x * x) + 0.06, lambda x: -0.82 * (1 - x * x) ** 0.7),
    'O':       (0.46, lambda x: 0.50 * S_(x), lambda x: -0.80 * S_(x)),
    'frown':   (0.60, lambda x: 0.26 * (1 - x * x), lambda x: 0.26 * (1 - x * x)),
    'grimace': (0.95, lambda x: 0.30 * (1 - abs(x) ** 4), lambda x: -0.32 * (1 - abs(x) ** 4)),
    'smirk':   (0.95, lambda x: -0.16 * (1 - x * x) + 0.20 * x + 0.06 * x ** 3, lambda x: -0.16 * (1 - x * x) + 0.20 * x + 0.06 * x ** 3),
    'A':       (0.80, lambda x: 0.06 * (1 - x * x), lambda x: -0.80 * (1 - x * x) ** 0.8),
    'E':       (1.05, lambda x: 0.04 * (1 - x * x), lambda x: -0.40 * (1 - x * x) ** 0.8),
    'O2':      (0.42, lambda x: 0.40 * S_(x), lambda x: -0.50 * S_(x)),
}
MOUTH_ROWS = [(0.0, 0.28, 1), (0.28, 0.76, 2), (0.76, 1.0, 3)]          # teeth | mouth interior | tongue
VISEMES = ('A', 'E', 'O2')

EXPRESSIONS = {
    'neutral':    dict(lid='open', brow='neutral', mouth='neutral'),
    'happy':      dict(lid='happy', brow='up', mouth='smile'),
    'joy':        dict(lid='joy', brow='up', mouth='open'),
    'shocked':    dict(lid='open', wide=1.0, pupil=0.55, brow='up', mouth='O'),
    'angry':      dict(lid='angry', brow='angry', mouth='grimace', pupil=0.9),
    'sad':        dict(lid='sad', brow='sad', mouth='frown', pupil=1.1),
    'smug':       dict(lid='half', brow='neutral', brow_R='raise1', mouth='smirk'),
    'pain':       dict(lid='squint', brow='angry', mouth='grimace'),
    'scared':     dict(lid='open', wide=0.8, pupil=0.55, brow='sad', mouth='grimace'),
    'thinking':   dict(lid='half', brow='focus', brow_L='raise1', mouth='flat'),
    'determined': dict(lid='angry', brow='focus', mouth='flat'),
    'deadpan':    dict(lid='half', brow='neutral', mouth='flat'),
    'confused':   dict(lid='open', brow='focus', brow_R='up', mouth='smirk'),
    'excited':    dict(lid='open', wide=0.5, brow='up', mouth='open', pupil=1.1),
}


def channels(e):
    """expression dict -> {(part, key): value} for every keyed channel of the face."""
    ch = {}
    for nm in ('L', 'R'):
        for k in LIDS:
            if k != 'open': ch[('eye' + nm, k)] = 1.0 if k == e['lid'] else 0.0
        ch[('eye' + nm, 'wide')] = e.get('wide', 0.0)
        p = e.get('pupil', 1.0); shut = 1.0 if e['lid'] in SHUT else 0.0
        ch[('pupil' + nm, 'small')] = max(0.0, min(1.0, (1.0 - p) / 0.45)); ch[('pupil' + nm, 'big')] = max(0.0, min(1.0, (p - 1.0) / 0.15))
        ch[('pupil' + nm, 'shut')] = shut
        b = e.get('brow_' + nm, e['brow'])
        for k in BROWS:
            if k != 'neutral': ch[('brow' + nm, k)] = 1.0 if k == b else 0.0
    for k in MOUTHS:
        if k != 'neutral' and k not in VISEMES: ch[('mouth', k)] = 1.0 if k == e['mouth'] else 0.0
    ch[('clench', 'grimace')] = 1.0 if e['mouth'] == 'grimace' else 0.0
    return ch


# ---------------------------------------------------------------- the face
class Face:
    """face decals on `head` (dims w, d, h in metres) from a face spec. Record acting with express / blink / gaze /
    talk, then call bake() once: it writes clean eased keyframes (blinks override expression ramps)."""

    def __init__(self, head, spec, mats, dims, target=None, coll=None):
        TARGET[head.name] = target or head
        self.head = head; w, d, h = dims; W = w; self.y = -d * 0.5 - 0.3; self.coll = coll
        self.groups = {}; self.events = []; self.blinks = []; self.talks = []; self.gazes = []
        E = spec.get('eyes', {})
        ex, ez = E.get('x', 0.2) * W, E.get('z', -0.15) * W; rx, rz = E.get('rx', 0.12) * W, E.get('rz', 0.125) * W
        line = E.get('line', 0.016) * W; ltop = line * E.get('lid_weight', 1.3)
        prx, prz = (p * r for p, r in zip(E.get('pupil', (0.28, 0.42)), (rx, rz)))
        self.eye = dict(ex=ex, ez=ez, rx=rx, rz=rz, prx=prx, prz=prz)
        ink, skin = mats['ink'], mats['skin']
        F = lambda nm, shapes, mts, rows, off, parent=None: decal(f'{head.name}_{nm}', head, shapes, mts, rows, self.y, off, parent, coll=coll)
        for nm, side in (('L', 1), ('R', -1)):
            cx = side * ex
            op = {k: eye_tb(cx, ez, rx, rz, side, **v) for k, v in LIDS.items()}
            op['wide'] = scale_tb(op['open'], cx, ez, 1.15, 1.15)
            ring = {k: dilate(t, b, ltop, line) for k, (t, b) in op.items()}
            UX, UZ = (1.15 * rx + ltop) * 1.12, (1.15 * rz + ltop) * 1.12
            U = [(cx + UX * u, ez + UZ * S_(u) + 0.25 * rz) for u in xs_cos()]
            Lw = [(cx + UX * u, ez - UZ * S_(u) - 0.25 * rz) for u in xs_cos()]
            parts = [F(f'sclera{nm}', op, [mats['eye_white']], [(0, 1, 0)], 0.0024)]
            # pupil + highlight ride a gaze pivot
            piv = bpy.data.objects.new(f'{head.name}_gaze{nm}', None); (coll or bpy.context.scene.collection).objects.link(piv)
            piv.parent = head; piv.location = (cx, 0, ez); piv.empty_display_size = 0.02
            pp = {'base': ellipse_tb(0, 0, prx, prz), 'small': ellipse_tb(0, 0, prx * 0.55, prz * 0.55),
                  'big': ellipse_tb(0, 0, prx * 1.15, prz * 1.15), 'shut': ellipse_tb(0, 0, prx, 0.0)}
            hx, hz, hr = -prx * 0.32, prz * 0.38, min(prx, prz) * 0.32
            hh = {'base': ellipse_tb(hx, hz, hr, hr), 'small': ellipse_tb(hx * 0.55, hz * 0.55, hr * 0.7, hr * 0.7),
                  'big': ellipse_tb(hx * 1.15, hz * 1.15, hr * 1.1, hr * 1.1), 'shut': ellipse_tb(hx, 0.0, hr, 0.0)}
            pup = [F(f'pupil{nm}', pp, [mats['pupil']], [(0, 1, 0)], 0.0032, piv), F(f'hilite{nm}', hh, [mats['hilite']], [(0, 1, 0)], 0.0040, piv)]
            # lid lines (ink) + skin covers: clip the pupil, draw the eye outline (heavier on top)
            lt = {k: (ring[k][0], op[k][0]) for k in op}; ct = {k: (U, ring[k][0]) for k in op}
            lb = {k: (op[k][1], ring[k][1]) for k in op}; cb = {k: (ring[k][1], Lw) for k in op}
            parts += [F(f'lidT{nm}', lt, [ink], [(0, 1, 0)], 0.0050), F(f'coverT{nm}', ct, [skin], [(0, 1, 0)], 0.0050),
                      F(f'lidB{nm}', lb, [ink], [(0, 1, 0)], 0.0050), F(f'coverB{nm}', cb, [skin], [(0, 1, 0)], 0.0050)]
            self.groups['eye' + nm] = parts; self.groups['pupil' + nm] = pup; self.groups['gaze' + nm] = piv
            # brows (filled + ink outline)
            B = spec.get('brows', {}); bl = B.get('len', 0.25) * W; bth = B.get('thick', 0.058) * W
            bx0 = side * B.get('x_in', 0.085) * W; bz0 = B.get('z', 0.035) * W
            bs = {bn: brow_tb([(bx0 + side * px * bl, bz0 + pz * bl) for (px, pz) in pts], bth, B.get('taper', 0.55)) for bn, pts in BROWS.items()}
            bline = B.get('line', 0.010) * W
            self.groups['brow' + nm] = [F(f'brow{nm}_ink', {k: dilate(t, b, bline) for k, (t, b) in bs.items()}, [ink], [(0, 1, 0)], 0.0060),
                                        F(f'brow{nm}', bs, [mats['brow']], [(0, 1, 0)], 0.0068)]
        # mouth + clenched-teeth overlay
        Mo = spec.get('mouth', {}); mw, mz, mh = Mo.get('w', 0.137) * W, Mo.get('z', -0.38) * W, Mo.get('h', 0.17) * W
        ms = {mn: curves_tb(0, mz, sx * mw, mh, tf, bf) for mn, (sx, tf, bf) in MOUTHS.items()}
        mline = Mo.get('line', 0.016) * W
        self.groups['mouth'] = [F('mouth_ink', {k: dilate(t, b, mline) for k, (t, b) in ms.items()}, [ink], [(0, 1, 0)], 0.0016),
                                F('mouth', ms, [ink, mats['teeth'], mats['mouth'], mats['tongue']], MOUTH_ROWS, 0.0024)]
        g = ms['grimace']; ctr = [(x, 0.5 * (zt + zb)) for (x, zt), (_, zb) in zip(*g)]
        self.groups['clench'] = [F('clench', {'base': (ctr, ctr), 'grimace': scale_tb(g, 0, mz, 0.97, 0.9)},
                                   [mats['teeth'], ink], [(0, 0.46, 0), (0.46, 0.54, 1), (0.54, 1, 0)], 0.0034)]
        bl_ = spec.get('blush')
        if bl_:   # rosy cheeks: soft pink ovals (under the lid lines and covers)
            for s_ in (-1, 1):
                F(f'blush{"L" if s_ > 0 else "R"}', {'base': ellipse_tb(s_ * bl_['x'] * W, bl_['z'] * W, bl_['r'] * W, bl_['r'] * W * 0.62, 16)},
                  [mats['blush']], [(0, 1, 0)], 0.0012)
        for i, (fx, fz) in enumerate(spec.get('freckles', [])):
            for s in (-1, 1):
                F(f'freckle{i}{"L" if s > 0 else "R"}', {'base': ellipse_tb(s * fx * W, fz * W, 0.011 * W, 0.011 * W, 10)},
                  [mats['freckle']], [(0, 1, 0)], 0.0056)
        sm = spec.get('smear')
        if sm:   # ONE smudge on one cheek (a coal smear): a slanted, tapered stroke with a slightly uneven edge
            a = math.radians(sm.get('angle', 15)); L_, th = sm.get('len', 0.16) * W, sm.get('th', 0.07) * W
            cx0, cz0 = sm.get('x', -0.31) * W, sm.get('z', -0.13) * W; ca, sa = math.cos(a), math.sin(a)
            top, bot = [], []
            for x in xs_cos():
                u = 0.5 * (x + 1); h = 0.5 * th * (math.sin(math.pi * u) ** 0.65) * (1 + 0.10 * math.sin(7.3 * u + 1.1))
                h *= 1.0 - 0.25 * u                                  # heavier where the thumb landed
                cx_, cz_ = cx0 + (u - 0.5) * L_ * ca, cz0 + (u - 0.5) * L_ * sa
                top.append((cx_ - sa * h, cz_ + ca * h)); bot.append((cx_ + sa * h, cz_ - ca * h))
            F('smear', {'base': (top, bot)}, [mats['smear']], [(0, 1, 0)], 0.0056)

    # ---------------- acting (recorded, then baked)
    def express(self, f, name, ramp=6):
        self.events.append((f - ramp, f, EXPRESSIONS[name] if isinstance(name, str) else name)); return self

    def blink(self, f, dur=7):
        self.blinks.append((f, dur)); return self

    def auto_blink(self, f0, f1, seed=0, every=(55, 110)):
        """natural blinks every ~2-4 s between f0 and f1 (skips frames that already have a blink nearby)."""
        import random as _r
        rnd = _r.Random(seed); f = f0 + rnd.randint(10, every[0])
        while f < f1:
            if all(abs(f - b) > 20 for b, _ in self.blinks): self.blinks.append((f, rnd.choice((6, 7, 8))))
            f += rnd.randint(*every)
        return self

    def gaze(self, f, gx, gz, hold=False):
        """pupil direction, -1..1 (x screen-right of the character's own left, z up)."""
        self.gazes.append((f, gx, gz)); return self

    def talk(self, words, fps=30, amp=1.0):
        """words: [(start_s, end_s, text)] -> visemes on the mouth (additive with the expression's mouth)."""
        self.talks.append((words, fps, amp)); return self

    def state_at(self, t):
        ev = sorted(self.events, key=lambda e: e[1]); prev = channels(EXPRESSIONS['neutral']); cur = prev
        for f0, f1, e in ev:
            nxt = channels(e)
            if t >= f1: prev = cur = nxt; continue
            if t > f0:
                a = (t - f0) / max(1e-6, f1 - f0); a = a * a * (3 - 2 * a)
                return {k: cur.get(k, 0) + (nxt.get(k, 0) - cur.get(k, 0)) * a for k in nxt}
            break
        return cur

    def bake(self):
        keys = {}                                   # (part, key) -> {frame: value}
        ev = sorted(self.events, key=lambda e: e[1])
        if not ev: ev = [(0, 0, EXPRESSIONS['neutral'])]
        for f0, f1, e in ev:
            for fr in (f0, f1):
                for ch, v in self.state_at(fr).items(): keys.setdefault(ch, {})[fr] = v
        for fb, dur in sorted(self.blinks):
            fe = fb + dur; mid = fb + dur // 2
            for ch, fk in keys.items():
                if not ch[0].startswith(('eye', 'pupil')): continue
                for fr in [k for k in fk if fb < k < fe]: del fk[fr]
            for fr in (fb, fe):
                for ch, v in self.state_at(fr).items():
                    if ch[0].startswith(('eye', 'pupil')): keys.setdefault(ch, {})[fr] = v
            st = self.state_at(mid)
            for nm in ('L', 'R'):
                for k in LIDS:
                    if k != 'open': keys.setdefault(('eye' + nm, k), {})[mid] = 1.0 if k == 'closed' else 0.0
                keys[('eye' + nm, 'wide')][mid] = 0.0
                for k in ('small', 'big'): keys[('pupil' + nm, k)][mid] = st[('pupil' + nm, k)]
                keys[('pupil' + nm, 'shut')][mid] = 1.0
        vis = ('A', 'E', 'O2', 'A', 'E', 'A', 'O2'); j = 0
        for words, fps, amp in self.talks:
            for (s, e, _t) in words:
                f0, f1 = int(round(s * fps)), int(round(e * fps)); n = max(1, int(round((f1 - f0) / 4.0)))
                for k in VISEMES: keys.setdefault(('mouth', k), {})[f0 - 1] = 0.0
                for i in range(n):
                    fa = f0 + int((f1 - f0) * i / n); v = vis[j % len(vis)]; j += 1
                    for k in VISEMES: keys.setdefault(('mouth', k), {})[fa] = (0.85 * amp) if k == v else 0.0
                for k in VISEMES: keys[('mouth', k)][f1 + 1] = 0.0
        for (part, key), fk in keys.items():
            for o in self.groups.get(part, []):
                sk = o.data.shape_keys.key_blocks.get(key) if o.data.shape_keys else None
                if sk is None: continue
                for fr, v in sorted(fk.items()):
                    sk.value = v; sk.keyframe_insert('value', frame=fr)
        e = self.eye
        for f, gx, gz in sorted(self.gazes):
            for nm, side in (('L', 1), ('R', -1)):
                piv = self.groups['gaze' + nm]
                piv.location = (side * e['ex'] + gx * e['rx'] * 0.42, 0, e['ez'] + gz * e['rz'] * 0.36)
                piv.keyframe_insert('location', frame=f)
        return self
