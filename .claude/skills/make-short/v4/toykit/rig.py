"""toykit.rig: an armature for a toykit Character plus a small acting API.

Bones (character faces -Y, metres): root (floor, yaw/placement) > hips > chest > head; arms = upperarm + forearm
(B-bone noodles, IK to hand_ik under the chest, elbow pole behind); legs = thigh + shin (IK to foot_ik under root).
Coat / sleeves / legs deform (weights by height / along the limb); every other part rides a bone rigidly.

Acting: Actor.pose(f, name or dict, ramp) keys named poses with OVERLAP built in (hips lead, head and hands trail a few
frames), look(f, yaw, pitch, tilt), wave(f0, f1), breathe(f0, f1), hop(f, h). Keys are Bezier (eased both ends)."""
import bpy, math
from mathutils import Vector, Matrix, Euler

UP = Vector((0, 0, 1))


def _signed_angle(u, v, n):
    a = u.angle(v)
    return -a if u.cross(v).dot(n) < 0 else a


def _pole_angle(base, ikb, pole):
    pn = (ikb.tail - base.head).cross(pole - base.head)
    proj = pn.cross(base.tail - base.head)
    return _signed_angle(base.x_axis, proj, base.tail - base.head)


def _parent_to_bone(obj, arm, bone):
    bpy.context.view_layer.update()   # a .location set just before is not in matrix_world until an update: the prop landed at the origin
    mw = obj.matrix_world.copy()
    obj.parent = arm; obj.parent_type = 'BONE'; obj.parent_bone = bone
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone]
    pm = arm.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    obj.matrix_parent_inverse = pm.inverted(); obj.matrix_basis = mw


def _deform(obj, arm, weights):
    """weights: {group: fn(vertex_co) -> w}; adds an Armature modifier FIRST in the stack."""
    for g, fn in weights.items():
        vg = obj.vertex_groups.get(g) or obj.vertex_groups.new(name=g)
        for v in obj.data.vertices:
            w = fn(v.co)
            if w > 1e-4: vg.add([v.index], w, 'REPLACE')
    md = obj.modifiers.new('rig', 'ARMATURE'); md.object = arm; md.use_vertex_groups = True; md.use_deform_preserve_volume = False
    obj.modifiers.move(len(obj.modifiers) - 1, 0)
    mw = obj.matrix_world.copy(); obj.parent = arm; obj.matrix_parent_inverse = arm.matrix_world.inverted(); obj.matrix_world = mw


def _smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- rig builder
def build(ch):
    s = ch.spec; b = s['body']; lg = s['legs']; hd = s['head']
    z0, z1 = b['z0'], b['z1']; mid = z0 + 0.48 * (z1 - z0); hz = hd['z']; h = hd['h']
    ad = bpy.data.armatures.new(ch.name + '_rig'); arm = bpy.data.objects.new(ch.name + '_rig', ad); ch.coll.objects.link(arm)
    ad.display_type = 'BBONE'; arm.show_in_front = True
    bpy.context.view_layer.objects.active = arm
    for o in bpy.context.view_layer.objects: o.select_set(False)
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); E = ad.edit_bones
    def bone(name, head, tail, parent=None, deform=True, segs=1, roll=0.0, connect=False):
        e = E.new(name); e.head = Vector(head); e.tail = Vector(tail); e.roll = roll; e.use_deform = deform
        e.bbone_segments = segs
        if parent: e.parent = E[parent]; e.use_connect = connect
        return e
    bone('root', (0, 0, 0), (0, 0.25, 0), deform=False)
    bone('hips', (0, 0, z0 + 0.03), (0, 0, mid), 'root')
    bone('chest', (0, 0, mid), (0, 0, z1), 'hips', connect=True)
    neck_z = hz - h * 0.40
    bone('head', (0, 0, neck_z), (0, 0, hz + h * 0.5), 'chest', deform=False)
    poles = {}
    for nm, sd in (('L', 1), ('R', -1)):
        p0, p1 = ch.arm[nm]; p0, p1 = Vector(p0), Vector(p1)
        el = (p0 + p1) * 0.5 + Vector((0, 0.035, -0.01))           # slight elbow bend backwards defines the IK plane
        bone(f'upperarm.{nm}', p0, el, 'chest', segs=6)
        bone(f'forearm.{nm}', el, p1, f'upperarm.{nm}', segs=6, connect=True)
        hr = s['arms']['hand']['r']; d = (p1 - p0).normalized()
        bone(f'hand.{nm}', p1, p1 + d * hr * 1.4, f'forearm.{nm}', deform=False, connect=True)
        bone(f'hand_ik.{nm}', p1, p1 + UP * 0.06, 'chest', deform=False)
        pole = el + Vector((sd * 0.05, 0.30, -0.05)); bone(f'elbow.{nm}', pole, pole + UP * 0.04, 'chest', deform=False)
        poles['arm' + nm] = (f'upperarm.{nm}', f'forearm.{nm}', pole)
        x = sd * lg['hip_x']; zh, za = lg['z_hip'], lg['z_ankle'] + 0.02
        kn = Vector((x, -0.012, 0.5 * (zh + za)))
        bone(f'thigh.{nm}', (x, 0, zh), kn, 'hips', segs=3)
        bone(f'shin.{nm}', kn, (x, 0, za), f'thigh.{nm}', segs=3, connect=True)
        bone(f'foot_ik.{nm}', (x, 0, za), (x, 0, za + 0.05), 'root', deform=False)
        kp = kn + Vector((0, -0.35, 0)); bone(f'knee.{nm}', kp, kp + UP * 0.04, 'root', deform=False)
        poles['leg' + nm] = (f'thigh.{nm}', f'shin.{nm}', kp)
    angles = {k: _pole_angle(E[a], E[bn], p) for k, (a, bn, p) in poles.items()}
    for e in E:
        if e.bbone_segments > 1: e.bbone_easein = 1.0; e.bbone_easeout = 1.0
    bpy.ops.object.mode_set(mode='POSE')
    P = arm.pose.bones
    for pb in P: pb.rotation_mode = 'XYZ'
    for nm in ('L', 'R'):
        for lim, chain, tgt, pole in (('arm', f'forearm.{nm}', f'hand_ik.{nm}', f'elbow.{nm}'), ('leg', f'shin.{nm}', f'foot_ik.{nm}', f'knee.{nm}')):
            c = P[chain].constraints.new('IK'); c.target = arm; c.subtarget = tgt; c.pole_target = arm; c.pole_subtarget = pole
            c.pole_angle = angles[lim + nm]; c.chain_count = 2; c.use_stretch = True
        P[f'upperarm.{nm}'].ik_stretch = 0.08; P[f'forearm.{nm}'].ik_stretch = 0.08
        # the hand ball keeps its own orientation (no wrist snapping)
        cr = P[f'hand.{nm}'].constraints.new('COPY_ROTATION'); cr.target = arm; cr.subtarget = 'chest'
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    # ---- skinning
    coat = ch.parts['body']
    wc = {'hips': lambda co: 1 - _smooth(z0 + 0.35 * (z1 - z0), z0 + 0.70 * (z1 - z0), co.z),
          'chest': lambda co: _smooth(z0 + 0.35 * (z1 - z0), z0 + 0.70 * (z1 - z0), co.z)}
    _deform(coat, arm, wc)
    if 'coatproxy' in ch.parts:
        cp = ch.parts['coatproxy']
        for g, fn in wc.items():
            vg = cp.vertex_groups.new(name=g)
            for v in cp.data.vertices:
                w = fn(v.co)
                if w > 1e-4: vg.add([v.index], w, 'REPLACE')
        md = cp.modifiers.new('rig', 'ARMATURE'); md.object = arm; cp.modifiers.move(len(cp.modifiers) - 1, 0)
    for nm in ('L', 'R'):
        p0, p1 = (Vector(v) for v in ch.arm[nm]); L = (p1 - p0).length; dd = (p1 - p0).normalized()
        t = lambda co, p0=p0, dd=dd, L=L: max(0.0, min(1.0, (co - p0).dot(dd) / L))
        _deform(ch.parts['sleeve' + nm], arm, {f'upperarm.{nm}': lambda co, t=t: 1 - _smooth(0.35, 0.65, t(co)),
                                               f'forearm.{nm}': lambda co, t=t: _smooth(0.35, 0.65, t(co))})
        x = (1 if nm == 'L' else -1) * lg['hip_x']; zh, za = lg['z_hip'], lg['z_ankle'] + 0.02
        tl = lambda co, zh=zh, za=za: max(0.0, min(1.0, (zh - co.z) / (zh - za)))
        _deform(ch.parts['leg' + nm], arm, {f'thigh.{nm}': lambda co, tl=tl: 1 - _smooth(0.35, 0.65, tl(co)),
                                            f'shin.{nm}': lambda co, tl=tl: _smooth(0.35, 0.65, tl(co))})
    # ---- rigid parts
    rigid = {'head': 'head', 'brim': 'head', 'hat': 'head', 'hat_top': 'head', 'visor': 'head', 'hair': 'head', 'moustache': 'head', 'glasses': 'head', 'bandana_neck': 'chest', 'sash_end': 'chest',
             'neck': 'chest', 'collar': 'chest', 'hood': 'chest', 'belt': 'hips', 'sashknot': 'hips', 'epauletteL': 'chest', 'epauletteR': 'chest',
             'handL': 'hand.L', 'handR': 'hand.R', 'bootL': 'foot_ik.L', 'bootR': 'foot_ik.R'}
    for part, bn in rigid.items():
        if part in ch.parts: _parent_to_bone(ch.parts[part], arm, bn)
    # decals drawn on the body (apron, seam) project along their own local axis: they must turn with the chest,
    # otherwise an apron slides round to the character's side as soon as the root yaws
    body = ch.parts.get('body')
    if body is not None:
        for o in list(body.children):
            if o.type == 'MESH' and any(k in o.name for k in ('_apron', '_seam', '_bandana', '_sash')): _parent_to_bone(o, arm, 'chest')
    deformed = {ch.parts.get(k) for k in ('body', 'sleeveL', 'sleeveR', 'legL', 'legR')}
    for o in list(ch.coll.objects):          # anything still loose (buttons, toggles, trims) rides the chest
        if o.parent is None and o is not arm and o not in deformed and o.type in ('MESH', 'FONT'):
            _parent_to_bone(o, arm, 'chest')
    ch.rig = arm
    return arm


# ---------------------------------------------------------------- acting
# hands: (out, fwd, up, reach) = direction from the SHOULDER (out = away from the body, mirrored per side; fwd = toward
# the camera-facing front; up) and reach as a fraction of the arm length (1 = straight, <1 bends the elbow).
# rotations in degrees: 'head' / 'chest' = (nod/bend forward +, turn to the character's left +, tilt to its left +).
# 'hips' = (x, fwd, up) metres.
POSES = {
    'rest':     {'hand.L': (0.82, 0.0, -0.57, 1.0), 'hand.R': (0.82, 0.0, -0.57, 1.0)},
    'idle':     {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.42, 0.10, -0.90, 0.96), 'chest': (2, 0, 0)},
    'relaxed':  {'hand.L': (0.32, 0.06, -0.94, 0.97), 'hand.R': (0.32, 0.06, -0.94, 0.97), 'chest': (3, 0, 0), 'head': (-3, 0, 0)},
    'wave_up':  {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.55, 0.30, 0.78, 0.86), 'chest': (-4, 0, -4), 'head': (-4, 0, -5)},
    'shocked':  {'hand.L': (0.30, 0.62, 0.72, 0.80), 'hand.R': (0.30, 0.62, 0.72, 0.80), 'chest': (-9, 0, 0), 'head': (-8, 0, 0), 'hips': (0, 0.02, 0)},
    'cheer':    {'hand.L': (0.45, 0.15, 0.88, 1.0), 'hand.R': (0.45, 0.15, 0.88, 1.0), 'chest': (-8, 0, 0), 'head': (-10, 0, 0)},
    'shrug':    {'hand.L': (0.85, 0.45, 0.25, 0.70), 'hand.R': (0.85, 0.45, 0.25, 0.70), 'chest': (-2, 0, 0), 'head': (2, 0, 9)},
    'hips':     {'hand.L': (0.55, -0.10, -0.83, 0.62), 'hand.R': (0.55, -0.10, -0.83, 0.62), 'chest': (-3, 0, 0)},
    'think':    {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (-0.47, 0.79, 0.39, 0.98), 'chest': (4, 0, 0), 'head': (-6, 0, -8)},
    'point':    {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.20, 0.95, 0.25, 1.06), 'chest': (0, 0, -5), 'head': (0, 0, 0)},
    'sad':      {'hand.L': (0.20, 0.15, -0.97, 0.97), 'hand.R': (0.20, 0.15, -0.97, 0.97), 'chest': (12, 0, 0), 'head': (16, 0, 0), 'hips': (0, 0, -0.012)},
    'angry':    {'hand.L': (0.35, -0.20, -0.92, 0.95), 'hand.R': (0.35, -0.20, -0.92, 0.95), 'chest': (7, 0, 0), 'head': (6, 0, 0), 'hips': (0, -0.01, -0.01)},
    'hold_out': {'hand.L': (0.30, 0.90, 0.30, 0.80), 'hand.R': (0.30, 0.90, 0.30, 0.80), 'chest': (3, 0, 0), 'head': (8, 0, 0)},
}
# overlap: frames each channel trails the pose key (hips lead, head and hands follow through)
LAG = {'hips': -1, 'chest': 0, 'head': 2, 'hand.L': 3, 'hand.R': 3}


class Actor:
    def __init__(self, ch, arm):
        self.ch = ch; self.arm = arm; self.P = arm.pose.bones; self.cur = {}

    # ---- low level
    def _hand_loc(self, off):
        x, y, z = off; return Vector((x, z, -y))                    # bone pointing +Z: local (X, Y, Z) = world (X, Z, -Y)

    def hand_offset(self, side, v):
        """(out, fwd, up, reach) -> IK-target offset (character space) from the rest wrist."""
        if len(v) == 3: return Vector(v)                           # raw offset
        out, fwd, up, reach = v; sd = 1 if side == 'L' else -1
        p0, p1 = (Vector(q) for q in self.ch.arm[side]); L = (p1 - p0).length
        d = Vector((sd * out, -fwd, up)).normalized()
        return p0 + d * reach * L - p1

    def key(self, f, bone, loc=None, rot=None, scale=None):
        pb = self.P[bone]
        if loc is not None: pb.location = loc; pb.keyframe_insert('location', frame=f)
        if rot is not None: pb.rotation_euler = Euler([math.radians(a) for a in rot]); pb.keyframe_insert('rotation_euler', frame=f)
        if scale is not None: pb.scale = scale; pb.keyframe_insert('scale', frame=f)

    def _apply(self, f, pose, chans=None):
        for ch_, v in pose.items():
            if chans and ch_ not in chans: continue
            ff = f + LAG.get(ch_, 0)
            if ch_.startswith('hand.'): self.key(ff, ch_.replace('hand.', 'hand_ik.'), loc=self._hand_loc(self.hand_offset(ch_[-1], v)))
            elif ch_ == 'head': self.key(ff, 'head', rot=(v[0], v[1], -v[2]))          # bone axes: X nod, Y twist (turn), Z tilt
            elif ch_ == 'chest': self.key(ff, 'chest', rot=(v[0], v[1], -v[2]))
            elif ch_ == 'hips': self.key(ff, 'hips', loc=Vector((v[0], v[2], -v[1])))
            elif ch_ == 'root': self.key(ff, 'root', loc=Vector(v[:3]), rot=(0, 0, v[3] if len(v) > 3 else 0))

    def pose(self, f, name, ramp=8, hold_prev=True, skip=()):
        """key a pose at f; the previous pose is held until f - ramp (eased transition), with overlap lags.
        skip: channels left alone (e.g. ('head',) while look() is aiming the head, ('hips',) during a hop)."""
        p = dict(POSES[name]) if isinstance(name, str) else dict(name)
        full = {'hand.L': POSES['rest']['hand.L'], 'hand.R': POSES['rest']['hand.R'], 'head': (0, 0, 0), 'chest': (0, 0, 0), 'hips': (0, 0, 0)}
        full.update(p)
        for k in skip: full.pop(k, None)
        if hold_prev and self.cur: self._apply(f - ramp, {k: v for k, v in self.cur.items() if k in full})
        self._apply(f, full); self.cur.update(full); return self

    def look(self, f, nod=0.0, turn=0.0, tilt=0.0, ramp=None):
        if ramp and 'head' in self.cur:
            h = self.cur['head']; self.key(f - ramp, 'head', rot=(h[0], h[1], -h[2]))
        self.key(f, 'head', rot=(nod, turn, -tilt)); self.cur['head'] = (nod, turn, tilt); return self

    def turn_body(self, f, deg, ramp=10, x=None, y=None):
        """yaw the whole character on the spot (root), hips leading by a couple of frames. The start pose is read from the
        ANIMATION at f - ramp (frame_set() elsewhere overwrites the Python-side pose values: v4.1 drift bug)."""
        from .film import value_at
        r = self.P['root']; pth = 'pose.bones["root"].'
        loc = value_at(self.arm, pth + 'location', f - ramp, r.location.copy())
        rz = math.degrees(value_at(self.arm, pth + 'rotation_euler', f - ramp, r.rotation_euler.copy()).z)
        self.key(f - ramp, 'root', loc=loc, rot=(0, 0, rz))
        nl = Vector((x if x is not None else loc.x, y if y is not None else loc.y, loc.z))
        self.key(f, 'root', loc=nl, rot=(0, 0, deg)); return self

    def wave(self, f0, f1, hand='R', period=10, amp=0.06):
        """side-to-side hand wave on top of the current pose (needs a raised-hand pose keyed at f0)."""
        base = self.hand_offset(hand, self.cur.get('hand.' + hand, (0, 0, 0))); f = f0; k = 0
        while f <= f1:
            off = base + Vector(((1 if k % 2 else -1) * amp, 0, 0.01 * (k % 2)))
            self.key(f, 'hand_ik.' + hand, loc=self._hand_loc(off)); f += period // 2; k += 1
        self.key(f, 'hand_ik.' + hand, loc=self._hand_loc(base)); return self

    def breathe(self, f0, f1, period=48, amp=0.012):
        """subtle chest scale + hips bob for life in holds."""
        f = f0; k = 0
        while f <= f1:
            s = 1.0 + (amp if k % 2 else 0.0)
            self.key(f, 'chest', scale=(1 + (s - 1) * 0.5, s, 1 + (s - 1) * 0.5)); f += period // 2; k += 1
        return self

    def hop(self, f, height=0.06, dur=12):
        """anticipation squash -> airborne (feet leave the ground) -> landing squash -> settle."""
        self.key(f - 5, 'hips', loc=Vector((0, 0, 0)), scale=(1, 1, 1))
        self.key(f, 'hips', loc=Vector((0, -0.02, 0)), scale=(1.06, 0.9, 1.06))
        self.key(f + dur // 2, 'hips', loc=Vector((0, height, 0)), scale=(0.95, 1.08, 0.95))
        self.key(f + dur, 'hips', loc=Vector((0, -0.015, 0)), scale=(1.06, 0.92, 1.06))
        self.key(f + dur + 7, 'hips', loc=Vector((0, 0, 0)), scale=(1, 1, 1))
        for nm, lag in (('L', 0), ('R', 1)):
            fb = f'foot_ik.{nm}'
            self.key(f + 1 + lag, fb, loc=Vector((0, 0, 0)))
            self.key(f + dur // 2 + lag, fb, loc=Vector((0, height * 0.85, 0)))
            self.key(f + dur - 1 + lag, fb, loc=Vector((0, 0, 0)))
        return self


# ---------------------------------------------------------------- walking (procedural, distance-phased: feet never slide)
def _ss(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def _walk(self, f0, f1, path, stride=0.30, lift=0.045, bob=0.014, sway=0.010, arm_swing=0.09, twist=4.0, ease=0.25):
    """walk along `path` (world (x, y) points) from frame f0 to f1. Root follows the path (eased start/stop) and faces
    along it; each foot is planted while the body passes over it, then swings (lift arc) to its next plant; hips bob at
    the passing pose and sway over the stance foot; arms swing opposite the legs; the chest counter-twists."""
    if f1 <= f0: raise ValueError(f'walk {self.ch.name}: ends at {f1} before it starts at {f0} (a W() lookup that found an earlier word? pass after=)')
    arm = self.arm; Minv = arm.matrix_world.inverted(); P = [Minv @ Vector((x, y, 0)) for x, y in path]
    seg = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]; S = sum(seg)
    def at(s):
        s = max(0.0, min(S, s))
        for i, L in enumerate(seg):
            if s <= L or i == len(seg) - 1:
                d = (P[i + 1] - P[i]); t = 0 if L < 1e-9 else s / L; return P[i] + d * min(1.0, t), math.atan2(d.y, d.x) + math.pi / 2
            s -= L
    lg = self.ch.spec['legs']; hip_x = lg['hip_x']; za = lg['z_ankle'] + 0.02
    dur = f1 - f0; Lmb = stride
    def s_of(f):   # eased distance along the path
        t = (f - f0) / dur; a = ease
        if t <= 0: return 0.0
        if t >= 1: return S
        v = 1.0 / (1 - a)                                           # trapezoid speed profile (accel a, decel a)
        if t < a: return S * v * t * t / (2 * a)
        if t > 1 - a: return S * (1 - v * (1 - t) ** 2 / (2 * a))
        return S * v * (t - a / 2)
    base = {k: Vector(v) for k, v in (('hand.L', self.hand_offset('L', POSES['idle']['hand.L'])), ('hand.R', self.hand_offset('R', POSES['idle']['hand.R'])))}
    for f in range(f0, f1 + 1):
        s = s_of(f); p, yaw = at(s); x = s / Lmb
        w = min(_ss(s / (0.5 * Lmb)), _ss((S - s) / (0.5 * Lmb))) if S > Lmb else 0.0
        self.key(f, 'root', loc=Vector((p.x, p.y, 0)), rot=(0, 0, math.degrees(yaw)))
        for nm, o, sd in (('L', 0.0, 1), ('R', 0.5, -1)):
            xx = x + o; n = math.floor(xx); fr = xx - n
            if fr < 0.5: fs, h = (n + 0.25 - o) * Lmb, 0.0
            else:
                u = (fr - 0.5) / 0.5; fs = (n + 0.25 - o + _ss(u)) * Lmb; h = lift * math.sin(math.pi * u)
            rel = (fs - s) * w; h *= w                                   # foot position relative to the body, along the path
            # in root space the path direction is the character's forward (-Y)
            self.key(f, f'foot_ik.{nm}', loc=Vector((0, h, rel)))       # bone axes: (X, Y, Z) = world (X, Z, -Y)
        bobv = -bob * w * (0.5 - 0.5 * math.cos(4 * math.pi * (x - 0.25)))
        swy = sway * w * math.sin(2 * math.pi * x)
        self.key(f, 'hips', loc=Vector((swy, bobv, 0)))
        sw = arm_swing * w * math.cos(2 * math.pi * x)
        for nm, sgn in (('L', -1), ('R', 1)):
            off = base['hand.' + nm] + Vector((0, -sgn * sw, 0.015 * abs(sw) / max(arm_swing, 1e-6)))
            self.key(f, f'hand_ik.{nm}', loc=self._hand_loc(off))
        self.key(f, 'chest', rot=(3, twist * w * math.cos(2 * math.pi * x), 0))
    self.cur.update({'hand.L': POSES['idle']['hand.L'], 'hand.R': POSES['idle']['hand.R'], 'chest': (3, 0, 0), 'hips': (0, 0, 0)})
    return self


Actor.walk = _walk


def _snap(self, f, pose=None, root=None):
    """instant change at a CUT (keys at f-0.6 = current, f-0.5 = new; no lag, no motion-blur smear).
    root=(x, y, yaw_deg) teleports the character."""
    from .film import _const_before
    from .film import value_at
    def jump(bone, attr, val):
        pb = self.P[bone]; path = f'pose.bones["{bone}"].{attr}'
        setattr(pb, attr, value_at(self.arm, path, f - 0.6, getattr(pb, attr).copy())); pb.keyframe_insert(attr, frame=f - 0.6)
        setattr(pb, attr, val); pb.keyframe_insert(attr, frame=f - 0.5)
        _const_before(self.arm, path, f - 0.6)
    if root is not None:
        x, y, yaw = root; Minv = self.arm.matrix_world.inverted(); p = Minv @ Vector((x, y, 0))
        jump('root', 'location', Vector((p.x, p.y, 0))); jump('root', 'rotation_euler', Euler((0, 0, math.radians(yaw))))
    if pose is not None:
        p = dict(POSES[pose]) if isinstance(pose, str) else dict(pose)
        full = {'hand.L': POSES['rest']['hand.L'], 'hand.R': POSES['rest']['hand.R'], 'head': (0, 0, 0), 'chest': (0, 0, 0), 'hips': (0, 0, 0)}
        full.update(p)
        for ch_, v in full.items():
            if ch_.startswith('hand.'): jump(ch_.replace('hand.', 'hand_ik.'), 'location', self._hand_loc(self.hand_offset(ch_[-1], v)))
            elif ch_ == 'head': jump('head', 'rotation_euler', Euler([math.radians(a) for a in (v[0], v[1], -v[2])]))
            elif ch_ == 'chest': jump('chest', 'rotation_euler', Euler([math.radians(a) for a in (v[0], v[1], -v[2])]))
            elif ch_ == 'hips': jump('hips', 'location', Vector((v[0], v[2], -v[1])))
        self.cur = full
    return self


def _hand(self, f, side, v):
    """key one hand target (out, fwd, up, reach) at f (with the usual lag)."""
    self.key(f, f'hand_ik.{side}', loc=self._hand_loc(self.hand_offset(side, v))); self.cur[f'hand.{side}'] = v; return self


Actor.snap = _snap
Actor.hand = _hand
POSES.update({
    'rifle_up':  {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.15, 0.35, 0.92, 0.92), 'chest': (-5, 0, 0), 'head': (-4, 0, 0)},
    'rifle_down': {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.10, 0.75, -0.10, 0.80), 'chest': (10, 0, 0), 'head': (8, 0, 0)},
    'bite':      {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (-0.45, 0.85, 0.30, 0.88), 'chest': (2, 0, 0), 'head': (-4, 0, 0)},
    'jaw':       {'hand.L': (-0.55, 0.62, 0.55, 0.92), 'hand.R': (0.25, 0.75, 0.10, 0.80), 'chest': (4, 0, 4), 'head': (4, 0, 10)},
    'look_at_hand': {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.10, 0.95, 0.30, 0.85), 'chest': (3, 0, 0), 'head': (10, 0, 0)},
    'hug':       {'hand.L': (-0.30, 0.95, -0.25, 0.62), 'hand.R': (-0.30, 0.95, -0.25, 0.62), 'chest': (-3, 0, 0), 'head': (-10, 0, -6)},
    'carry':     {'hand.L': (0.05, 0.95, -0.20, 0.70), 'hand.R': (0.05, 0.95, -0.20, 0.70), 'chest': (-4, 0, 0), 'head': (-3, 0, 0)},
    'offer':     {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.15, 0.95, 0.15, 0.95), 'chest': (4, 0, 0), 'head': (2, 0, 6)},
    'skim':      {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (-0.10, 0.92, -0.30, 0.80), 'chest': (8, 0, 0), 'head': (10, 0, 0)},
    'laugh':     {'hand.L': (0.55, 0.30, -0.70, 0.75), 'hand.R': (0.55, 0.30, -0.70, 0.75), 'chest': (-10, 0, 0), 'head': (-12, 0, 0)},
    'hold_up':   {'hand.L': (0.42, 0.10, -0.90, 0.96), 'hand.R': (0.05, 0.90, 0.40, 0.85), 'chest': (0, 0, 0), 'head': (6, 0, 0)},
})
