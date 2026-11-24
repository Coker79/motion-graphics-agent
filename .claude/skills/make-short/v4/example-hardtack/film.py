"""HARDTACK (v4, round 2): the whole Short as code, staged for script v3 with ONE continuous camera per set (CamPath).
blender -b -P film.py -- SET OUTDIR [FRAMES] [--preview | --animatic]
  SET     camp | cupboard | museum
  FRAMES  all | beats (one still per beat: the gate) | report (framing numbers, no render) | none | 120 | 100-160 | every:2
  --preview   540x960, 12 samples (gate stills)        --animatic   480x854, 8 samples (the review cut, rendered on twos)
Timing: voice/voice.json (Whisper, onsets snapped by voice/onsets.py) aligned to script.txt; frame 1 = t 0.
Props that hands use are the MASTER (keyed in world space) and the hands follow grips on them (props.follow), so a
rifle butt lands exactly on the cracker, a spoon exactly in the mug, a thumb exactly on the loaf."""
import bpy, sys, os, json, math, random
from mathutils import Vector, Euler, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); LAB = HERE; sys.path.insert(0, LAB)   # the project is a copy of the skill's v4/: toykit/ and specs/ sit next to film.py
from toykit import look, char, rig, world, camera, props, film
from toykit.camera import fcurves

A_ = film.args_after_dashes(); SET = A_[0]; OUT = os.path.join(HERE, A_[1])
FR = next((a for a in A_[2:] if not a.startswith('--')), 'all')
PREVIEW, ANIM = '--preview' in A_, '--animatic' in A_
T = film.Timing(os.path.join(HERE, 'voice', 'voice.json'), os.path.join(HERE, 'script.txt'), lead=1)
S = lambda n: T.line(n)[0]                   # first frame of script line n
W = lambda w, nth=0, after=0.0, end=False: T.word(w, nth, after, end)
END = T.f(T.duration) + 10                   # short tail: the Short loops back to frame 1
SETS = {'camp': (1, S(13) - 1), 'cupboard': (S(13), S(14) - 1), 'museum': (S(14), END)}
F0, F1 = SETS[SET]
C = look.hexc
REQ = None                                    # the frames this process will render (None = all / gate / report)
if FR not in ('all', 'beats', 'report', 'none', 'shots'):
    try: REQ = film.frames_arg(FR, F0, F1)
    except Exception: REQ = None
NEED = lambda a, b: REQ is None or any(a <= f <= b for f in REQ)      # skip building things this chunk never shows

bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
RW, RH, SMP = (480, 854, 8) if ANIM else (540, 960, 12) if PREVIEW else (1080, 1920, 32)
SMP = int(os.environ.get('TK_SAMPLES', SMP))                # A/B the final's sample count (16 vs 32) before committing to it
look.setup_render(sc, RW, RH, samples=SMP, motion_blur=True)
sc.frame_start, sc.frame_end = F0, F1
V = lambda *a: Vector(a)


def spec(base, **kw):
    d = json.load(open(os.path.join(LAB, 'specs', f'{base}.json'))); d.update(kw); return d


def lean(A, f0, f1, deg, bone='chest'):
    """an ADDITIVE lean (deg, pitch) on a bone from f0 to f1, faded over 6 frames. It rides on top of walk() and pose()
    keys; a keyed lean pose is overwritten by the walk cycle's own chest keys (Dutch flood, lesson 64)."""
    path = f'pose.bones["{bone}"].rotation_euler'
    fc = next((c for c in fcurves(A.arm) if c.data_path == path and c.array_index == 0), None)
    if fc is None:
        A.arm.pose.bones[bone].keyframe_insert('rotation_euler', index=0, frame=f0); fc = next((c for c in fcurves(A.arm) if c.data_path == path and c.array_index == 0), None)
    m = fc.modifiers.new('GENERATOR'); m.mode = 'POLYNOMIAL'; m.use_additive = True; m.coefficients = (math.radians(deg), 0.0)
    m.use_restricted_range = True; m.frame_start = f0; m.frame_end = f1; m.blend_in = 6; m.blend_out = 6


ACTORS = []                                   # every cast member: alive() and the campath clearance check use it


def cast(name, root, base=None, **kw):
    ch = char.Character(spec(base or name, name=name, **kw)); arm = rig.build(ch); A = rig.Actor(ch, arm)
    A.snap(F0 - 4, 'idle', root=root); A.breathe(F0, F1, period=56)
    ch.face.express(F0 - 4, 'neutral', 1); ch.face.auto_blink(F0, F1, seed=sum(map(ord, name)) % 97)   # deterministic in every process
    ACTORS.append((name, ch, A)); return ch, A


def vis(obj, f_on, f_off=None, kids=True):
    """object (and, unless kids=False, everything parented under it) visible only in [f_on, f_off] (hide_render keys)."""
    for o in [obj] + (list(obj.children_recursive) if kids else []):
        o.hide_render = True; o.keyframe_insert('hide_render', frame=min(F0, f_on) - 5)
        o.hide_render = False; o.keyframe_insert('hide_render', frame=f_on)
        if f_off is not None: o.hide_render = True; o.keyframe_insert('hide_render', frame=f_off + 1)


def key(o, f, loc=None, rot=None, scale=None, ip=None, easing=None):
    """world-space key on a free prop (rot in degrees); ip/easing set the interpolation of the segment that STARTS here."""
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = Euler([math.radians(a) for a in rot]); o.keyframe_insert('rotation_euler', frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert('scale', frame=f)
    if ip:
        for fc in fcurves(o):
            for kp in fc.keyframe_points:
                if abs(kp.co.x - f) < 1e-3: kp.interpolation = ip; kp.easing = easing or 'AUTO'


def at(obj, f):
    """evaluated world matrix of obj at frame f (after all animation set up so far)."""
    cur = sc.frame_current; sc.frame_set(f); bpy.context.view_layer.update(); m = obj.matrix_world.copy(); sc.frame_set(cur); return m


def orbit_pos(aim, az, el, d):
    """camera position at azimuth az (0 = from -Y, + = counter-clockwise from above), elevation el, distance d."""
    a, e = math.radians(az), math.radians(el); aim = Vector(aim)
    return aim + Vector((math.sin(a) * math.cos(e) * d, -math.cos(a) * math.cos(e) * d, math.sin(e) * d))


def shot(aim, az, el, d, vh):
    """camera dict looking at `aim` from (az, el, d) with `vh` metres visible top to bottom (9:16, 36 mm on the long side)."""
    aim = Vector(aim); return dict(pos=orbit_pos(aim, az, el, d), aim=aim, lens=36.0 * d / vh)


def fr(ch, root, size, az=0.0, el=3.0, off=(0, 0, 0), lens=None):
    p, a, l = film.framing(ch, root, size, az=az, el=el, off=off, lens=lens); return dict(pos=p, aim=a, lens=l)


def ride(actor, prop, bone, f_on, f_off=None):
    """prop rides a bone (e.g. 'chest') from f_on, keeping the world placement it has at f_on (hands can then follow grips on it)."""
    arm = actor.arm; cur = sc.frame_current; sc.frame_set(f_on); bpy.context.view_layer.update()
    cn = prop.constraints.new('CHILD_OF'); cn.target = arm; cn.subtarget = bone
    cn.inverse_matrix = (arm.matrix_world @ arm.pose.bones[bone].matrix).inverted()
    cn.influence = 0.0; cn.keyframe_insert('influence', frame=f_on - 1); cn.influence = 1.0; cn.keyframe_insert('influence', frame=f_on)
    if f_off is not None: cn.keyframe_insert('influence', frame=f_off - 1); cn.influence = 0.0; cn.keyframe_insert('influence', frame=f_off)
    sc.frame_set(cur); return cn


def bone_pos(actor, bone, f):
    cur = sc.frame_current; sc.frame_set(f); bpy.context.view_layer.update()
    p = (actor.arm.matrix_world @ actor.arm.pose.bones[bone].matrix).translation.copy(); sc.frame_set(cur); return p


def base_origin(o, p):
    """move an object's origin to world point p (keeping the mesh where it is): scale keys then grow from p."""
    p = Vector(p); o.data.transform(Matrix.Translation(-p)); o.location = p; return o


def aim_light(o, target):
    d = (Vector(target) - o.location).normalized()
    o.rotation_euler = Euler((math.acos(max(-1.0, min(1.0, -d.z))), 0, math.atan2(-d.x, d.y)))


def orbit_from(P, f0, f1, cd, az0, az1):
    """orbit that starts EXACTLY at camera dict `cd` (landed at f0) and arcs round its aim point to az1. The start azimuth
    is measured from cd itself (az0 is only the intended value: a mismatch made v2's hook orbit start the wrong way)."""
    c = cd['aim']; d = cd['pos'] - c; a0 = math.degrees(math.atan2(d.x, -d.y)); sweep = az1 - az0
    P.orbit(f0, f1, center=(c.x, c.y, c.z), radius=Vector((d.x, d.y)).length, az0=a0, az1=a0 + sweep, z=cd['pos'].z, aim_z=c.z, lens=cd['lens'])


def lift(A, z):
    """characters stand at z = 0 (the root bone's z is forced): raise the whole armature onto a dike, a bank or a stage (lesson 49)."""
    A.arm.location.z = z


def track(P, A, f0, f1, az, el, d, vh, off=(0, 0, 0), step=6, bone='root'):
    """a camera that travels WITH a walking character: short chained pushes, each landing on where the character really
    is (an eased walk makes a single push lead or lag it), at a fixed az/el/d from (bone + off). Lesson 51."""
    for f in list(range(f0 + step, f1, step)) + [f1]:
        P.push(max(f0, f - step), f, **shot(bone_pos(A, bone, f) + Vector(off), az, el, d, vh))


BEATS = []           # (frame, name, subjects): gate stills + the framing report


def beat(f, name, *subj):
    BEATS.append((int(f), name, subj))


cam = None
# =====================================================================================================================
if SET == 'camp':
    sky = look.world_sky(sc, zenith=C('#2A7FD6'), horizon=C('#9FE6EF'), ground=C('#6E8A55'), strength=1.0)
    sc.world.mist_settings.start = 6.0; sc.world.mist_settings.depth = 90.0
    sun = look.sun('sun', (50, 0, -34), energy=4.2, color=(1.0, 0.86, 0.64), angle=14)       # soft shadows on white egg heads
    fill = look.area('fill', (-3.5, -4.0, 2.4), (62, 0, -40), 230, (0.86, 0.88, 1.0), 6.0)
    rim = look.area('rim', (2.2, 2.6, 2.4), (-55, 0, 150), 380, (1.0, 0.86, 0.66), 2.0)
    Wc = world.coll('WORLD'); hf = lambda x, y: world.meadow_height(x, y, cliff_y=60)
    world.ground('ground', hf, mat=look.mat('TK_ground', C('#5C7A2C'), rough=0.95, brush=0.18, grain=0.4, paint=0.18, paint_scale=1.4, spec=0.15), c=Wc)
    world.grass('grass', world.scatter(9000, lambda r: (r.uniform(-7, 7), r.uniform(-4, 10)), 1), hf, h=(0.10, 0.28), c=Wc, seed=2, base='#2B4620', tip='#AEB04C')
    world.grass('grass_tall', world.scatter(500, lambda r: (r.uniform(-7, 7), r.uniform(-4, 4)) if abs(r.uniform(-1, 1)) > 0.3 else None, 4), hf,
                h=(0.30, 0.55), w=(0.04, 0.08), c=Wc, seed=8, base='#2E5520', tip='#9DBE4A', bend=0.45)
    for i, (x, y, z, s) in enumerate(((-16, 85, 24, 15), (13, 95, 34, 19), (30, 100, 17, 12), (-30, 110, 40, 18), (2, 80, 13, 9))):
        world.cloud(f'cloud{i}', (x, y, z), s, seed=i + 3, c=Wc)
    world.tent('tent0', (-3.6, 4.1, 0), rot=0.35, camo=True, c=Wc)
    world.tent('tent1', (2.9, 4.6, 0), rot=-0.4, color='#E6D7B0', c=Wc, seed=2)
    world.tent('tent2', (0.5, 6.6, 0), rot=0.1, color='#E0D0A6', c=Wc, seed=3)
    FIRE = V(-1.15, 2.75, 0); fire, flames = world.campfire('fire', FIRE, c=Wc)
    for i, (x, y, h) in enumerate(((2.3, 1.3, 0.75), (2.7, 1.8, 0.6), (-3.4, 2.5, 0.7))): world.barrel(f'barrel{i}', (x, y, 0), h=h, c=Wc)
    for i, (x, y) in enumerate(((-5.5, 8.5), (5.2, 9.5), (-8.0, 12), (7.5, 13), (0.8, 14.5), (-3.0, 15))): world.pine(f'pine{i}', (x, y, 0), 5.5, 1.4, c=Wc, seed=i)
    OVEN = V(-2.55, 1.55, 0); oven, _ = props.field_oven('oven', OVEN, c=Wc)
    og = bpy.data.objects['oven_glow']; og.data.energy = 90
    mouth = bpy.data.objects['oven_m']; mouth.data.materials.clear()
    mm = bpy.data.materials.new('TK_ovenglow'); mm.use_nodes = True; nt = mm.node_tree; nt.nodes.clear()   # fire glow: hot below, dark above
    tc_ = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); cr = nt.nodes.new('ShaderNodeValToRGB')
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.4; out_ = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tc_.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Y'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].position = 0.08; cr.color_ramp.elements[0].color = (1.0, 0.45, 0.08, 1)
    cr.color_ramp.elements[1].position = 0.75; cr.color_ramp.elements[1].color = (0.02, 0.008, 0.004, 1)
    mid = cr.color_ramp.elements.new(0.38); mid.color = (0.45, 0.07, 0.02, 1)
    nt.links.new(cr.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], out_.inputs[0]); mouth.data.materials.append(mm)
    wood = look.mat('TK_table', C('#9A6A3C'), rough=0.85, brush=0.12, grain=0.6, paint=0.12)
    TOP = 0.40; table = props.box('table', (1.0, 0.5, TOP), (0, 0, TOP / 2), [wood], Wc, bevel=0.012); look.outline(table, 0.008)
    CK, CT = 0.17, 0.026                                   # every hardtack cracker in the film: 17 cm, 2.6 cm thick
    WS = V(-0.15, 0.06, TOP)                               # the whack spot on the table (in front of the striker)
    WSC = WS + V(0, 0, CT / 2)                             # cracker centre on the whack spot
    BOX = V(0.13, 0.06, TOP)
    box_, _ = props.crate('kidbox', size=(0.32, 0.25, 0.15), loc=BOX, c=Wc)
    MUG = V(-0.41, 0.07, TOP); mug = props.mug('mug', r=0.062, h=0.10, c=Wc, coffee='#7A4A28'); mug.location = MUG; LIQ = TOP + 0.080
    SPOT = (-0.15, 0.42, 0)                                # behind the table, facing the camera side (-Y)
    COOK = (-1.5, 0.78, 30)                                # the cook's place, in front of his oven
    O_FIRE, O2_FIRE = (-0.78, 2.38, 18), (-1.52, 2.30, 34)

    rec, R = cast('recruit', (1.95, 0.78, -70))
    old, O = cast('oldhand', SPOT)
    old2, O2 = cast('oldhand2', (4.0, 3.35, 90), base='oldhand',
                    hat={"kind": "kepi", "color": "#2C3560", "band": "#C9A12E", "visor": "#1E1B22", "band_z": 0.17, "band_h": 0.16,
                         "crown_h": 0.22, "taper": 0.9, "slope": 6, "tilt": 4},
                    facial_hair={"style": "walrus", "z": -0.21, "span": 0.52, "thick": 0.14, "depth": 0.5, "color": "#5A4636"})
    cook, K = cast('cook', COOK)
    extras = []
    for k_, (hat, hair) in enumerate(() if not NEED(F0, S(3) + 30) else ((dict(kind="kepi", color="#3B4A2C", band="#8E6B2E", visor="#1E1B22", band_z=0.17, band_h=0.14, crown_h=0.20, taper=0.9, slope=4, tilt=-3),
                                       dict(style="walrus", z=-0.21, span=0.46, thick=0.12, depth=0.5, color="#2E2620")),
                                      (dict(kind="kepi", color="#2C3560", band="#C9A12E", visor="#1E1B22", band_z=0.17, band_h=0.16, crown_h=0.24, taper=0.85, slope=7, tilt=5),
                                       dict(style="walrus", z=-0.21, span=0.40, thick=0.10, depth=0.5, color="#8A6A4A")))):
        ex, EX = cast(f'marcher{k_}', (4.4 + 0.5 * k_, 3.5 + 0.15 * k_, 90), base='oldhand', hat=hat, facial_hair=hair); extras.append((ex, EX))
    cam = camera.Cam(sc, lens=30, fstop=2.4); P = film.CamPath(cam, creep=0.14)

    # ---- helpers for this set
    def cracker_at(name, center, f_on, f_off=None, rot=(0, 0, 0)):
        o = props.cracker(name, CK, CT, c=Wc); o.location = center; o.rotation_euler = Euler([math.radians(a) for a in rot]); vis(o, f_on, f_off); return o

    def split(name, center, contact, gone, seed=0):
        hl, hr = props.cracker_halves(name, CK, CT, c=Wc); c0 = Vector(center)
        for h_, s in ((hl, -1), (hr, 1)):
            vis(h_, contact, gone)
            key(h_, contact, loc=c0, rot=(0, 0, 0), scale=(1.10, 1.10, 0.60))
            key(h_, contact + 3, scale=(1, 1, 1))
            key(h_, contact + 7, loc=c0 + V(s * 0.05, -0.012, 0), rot=(0, 0, s * 16))
        props.crumbs(name + '_cr', c0 + V(0, 0, CT * 0.5), contact, n=11, spread=0.20, up=0.13, dur=10, floor=TOP, c=Wc, seed=seed)
        return hl, hr

    def rifle_obj(name):
        r = props.rifle(name, c=Wc); r.rotation_mode = 'ZXY'          # R = Ry(side) Rx(-lean) Rz(spin): profile faces -Y
        return r, props.grip(r, (0, 0.0, 0.18), f'{name}_gR', Wc), props.grip(r, (0, 0.012, 0.37), f'{name}_gL', Wc)   # hands low: never across the face

    def rk(r, f, butt, lean=14.0, yaw=0.0, side=0.0, ip='BEZIER', easing='AUTO'):
        key(r, f, loc=butt, rot=(-lean, side, 90.0 + yaw), ip=ip, easing=easing)

    def strike(A, r, spot, contacts, yaw=0.0, rest=0.09, windup=0.19, side=-16.0):
        """rifle-butt strikes that land ON `spot` (world point: the top of the cracker) at each contact frame: rest above ->
        wind-up -> accelerating 6-frame slam -> contact (squash + rebound, held ~5 frames) -> the next wind-up or rest."""
        sp = Vector(spot); tw = Vector((-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0))
        SD = side                                             # barrel tilted AWAY from the camera's side: beside the head, never across the face
        rk(r, contacts[0] - 16, sp + V(0, 0, rest) + tw * 0.02, 7, yaw, side=SD)
        for i, c in enumerate(contacts):
            rk(r, c - 6, sp + V(0, 0, windup) + tw * 0.07, 16, yaw, side=SD - 4, ip='EXPO', easing='EASE_IN')
            rk(r, c, sp, 5, yaw, side=SD); rk(r, c + 2, sp + V(0, 0, 0.024), 6, yaw, side=SD); rk(r, c + 5, sp + V(0, 0, 0.006), 6, yaw, side=SD)
            A.pose(c - 6, {'chest': (-8, 0, 0), 'head': (-9, 0, 0), 'hips': (0, -0.01, 0.0)}, ramp=8, skip=('hand.L', 'hand.R'))
            A.pose(c, {'chest': (14, 0, 0), 'head': (12, 0, 0), 'hips': (0, 0.015, -0.03)}, ramp=3, skip=('hand.L', 'hand.R'))
            A.pose(c + 8, {'chest': (6, 0, 0), 'head': (4, 0, 0), 'hips': (0, 0.005, -0.01)}, ramp=6, skip=('hand.L', 'hand.R'))
            P.shake(c, 7, 0.016)

    # ================= L1 hook: an old hand smashes his cracker with his rifle butt ("Soldiers smashed their bread...")
    hit = W('smashed') + 3
    cracker_at('ck_hook', WSC, F0, hit - 1)
    split('ck_hook_s', WSC, hit, S(2) - 12, seed=1)
    rif_o, gRo, gLo = rifle_obj('rifle_old'); vis(rif_o, F0, W('and') + 4)
    strike(O, rif_o, WS + V(0, 0, CT), [hit])
    rk(rif_o, F0 - 8, WS + V(0, 0.02, 0.10), 7, side=-16)
    rk(rif_o, hit + 18, WS + V(-0.13, 0.11, 0.0), 4)          # then plants the butt on the table beside the halves
    props.follow(O, 'R', gRo, F0 - 8, f_off=W('and')); props.follow(O, 'L', gLo, F0 - 8, f_off=W('and'))   # let go INSIDE the whip blur
    old.face.express(F0 - 4, 'determined', 1); old.face.express(hit - 5, 'angry', 2); old.face.express(hit + 9, 'smug', 3)
    O.look(hit + 16, nod=-3, turn=10, tilt=-5, ramp=6)
    O.snap(W('and') + 5, 'idle', root=(3.65, 3.1, 90))        # hidden inside the whip, AFTER the hands let go: he joins the march (off screen)
    # the cook, smug at his oven: "and the army made it that hard on purpose"
    K.snap(F0 - 3, 'hips', root=COOK); cook.face.express(F0 - 3, 'smug', 1)
    K.look(W('hard') - 2, nod=-5, turn=-8, tilt=-9, ramp=5); K.look(W('purpose') + 8, nod=2, turn=-4, tilt=-4, ramp=6)
    s0 = shot(WS + V(0, 0, 0.12), 34, 5, 0.50, 0.58)
    P.start(F0 - 8, **s0)
    P.push(F0, hit - 1, **shot(WS + V(0, 0, 0.10), 32, 4, 0.42, 0.50))
    ms = shot(V(-0.17, 0.24, 0.62), 40, 3, 1.15, 1.02); P.slam(hit + 20, **ms, dur=14)   # slam-back reveal: who did that (halves in front)
    orbit_from(P, hit + 20, W('and') - 2, ms, 44 + SPOT[2], 20 + SPOT[2])     # then arcs round him (starts exactly where it landed)
    P.whip(W('and') + 8, **fr(cook, COOK, 'MCU', az=-14, el=4), dur=8)     # whip to the cook
    P.push(W('hard'), W('purpose') + 8, **fr(cook, COOK, 'CU', az=-9, el=3))
    beat(F0, 'f1 cracker+butt', 'ck_hook', 'rifle_old'); beat(hit, 'contact', 'ck_hook_s_L', 'rifle_old'); beat(hit + 24, 'slam-back MS', 'oldhand_head', 'rifle_old')
    beat(W('army'), 'cook MCU', 'cook_head'); beat(W('purpose'), 'cook CU', 'cook_head')

    # ================= L2 "You see, on the march, every soldier got a pound of these crackers a day."
    O.walk(W('see') - 60, S(3) + 10, [(3.65, 3.1), (-0.30, 3.05), (O_FIRE[0], O_FIRE[1])], stride=0.36)
    O2.walk(W('see') - 54, S(3) + 16, [(4.0, 3.35), (-0.95, 3.25), (O2_FIRE[0], O2_FIRE[1])], stride=0.36)
    O.turn_body(S(3) + 24, O_FIRE[2], ramp=12); O2.turn_body(S(3) + 30, O2_FIRE[2], ramp=12)
    for k_, (ex, EX) in enumerate(extras):                                                   # the rest of the column marches on, out of the camp
        EX.walk(W('see') - 48 + 6 * k_, S(3) + 30, [(4.4 + 0.5 * k_, 3.5 + 0.15 * k_), (-4.6, 3.3 + 0.15 * k_)], stride=0.36)
        vis(ex.rig, F0, S(3) + 30); [vis(o_, F0, S(3) + 30) for o_ in ex.coll.objects if o_.parent is None]
    rnd = random.Random(5); d0, d1 = W('every') + 8, W('day') + 4; pile = []
    for i in range(10):                                     # the day's ration drops into the kid's box, one by one
        fd = int(round(d0 + (d1 - d0) * i / 9)); z = TOP + 0.024 + CT / 2 + i * (CT - 0.002)
        p = BOX + V(rnd.uniform(-0.03, 0.03), rnd.uniform(-0.025, 0.025), 0); p.z = z; rz = rnd.uniform(-14, 14)
        c_ = cracker_at(f'ck_r{i}', p, fd - 7)
        key(c_, fd - 7, loc=p + V(0, 0, 0.75), rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), rz + 30), ip='QUAD', easing='EASE_IN')
        key(c_, fd, loc=p, rot=(0, 0, rz), scale=(1.06, 1.06, 0.8)); key(c_, fd + 2, loc=p + V(0, 0, 0.008), scale=(1, 1, 1)); key(c_, fd + 4, loc=p)
        pile.append((c_, fd, p, rz))
    R.walk(W('every') + 16, S(3) - 4, [(1.95, 0.78), (0.65, 0.62), (SPOT[0], SPOT[1])], stride=0.32)
    R.turn_body(S(3) + 4, SPOT[2], ramp=8)
    rec.face.express(S(3) - 2, 'happy', 3)
    P.slam(S(2) + 14, pos=V(0.80, -1.75, 1.80), aim=V(0.75, 2.7, 0.75), lens=30, dur=14)     # crane up: the camp, the column on the march
    P.push(S(2) + 16, W('every'), pos=V(0.45, -1.60, 1.62), aim=V(0.30, 2.7, 0.72), lens=31)
    P.push(W('every'), W('every') + 22, **shot(BOX + V(0, 0, 0.17), -22, 18, 0.80, 0.70))    # crane down into the box
    beat(W('march'), 'wide march', 'oldhand_head', 'oldhand2_head'); beat(W('pound'), 'box drops', 'kidbox'); beat(W('day') + 6, 'box full', 'kidbox', 'recruit_head')

    # ================= L3 "When a new recruit bit into his first one, something cracked, and it wasn't the cracker."
    ckb, fdb, pb_, rzb = pile[-1]                           # he takes the top cracker of his ration
    hd = V(SPOT[0], SPOT[1], rec.spec['head']['z']); mouth = hd + V(0, -rec.spec['head']['d'] * 0.5, -0.085)
    bite = W('bit') + 2
    def in_teeth(depth, th):      # cracker centre so that its back edge sits `depth` metres into the mouth, tilted th degrees
        t = math.radians(th); return mouth + V(0, depth, 0) - V(0, CK / 2 * math.cos(t), CK / 2 * math.sin(t))
    key(ckb, S(3) + 2, loc=pb_, rot=(0, 0, rzb), ip='BEZIER')
    key(ckb, S(3) + 9, loc=V(0.02, 0.12, 0.66), rot=(30, 0, 10))
    key(ckb, bite - 2, loc=in_teeth(0.002, 34), rot=(34, 0, 0))
    key(ckb, bite, loc=in_teeth(0.020, 32), rot=(32, 0, 0))                                  # into the teeth
    for j, fg in enumerate(range(bite + 4, W('cracked') - 3, 5)):                            # grinding: the cracker strains in his teeth
        key(ckb, fg, loc=in_teeth(0.019 + 0.002 * (j % 2), 32 + (3 if j % 2 else -3)), rot=(32 + (3 if j % 2 else -3), 0, (2.5 if j % 2 else -2.5)))
        R.look(fg + 1, nod=(-3 if j % 2 else 2), turn=(4 if j % 2 else -4), tilt=(3 if j % 2 else -3), ramp=4)
    key(ckb, W('cracked') - 2, loc=in_teeth(0.018, 32), rot=(32, 0, 0))
    key(ckb, W('cracked') + 6, loc=in_teeth(-0.09, 48) + V(0.02, 0, -0.10), rot=(48, 0, 8))  # pulls it away
    key(ckb, W('wasn') + 2, loc=V(-0.05, 0.12, 0.70), rot=(52, 0, 10))
    key(ckb, S(4) + 2, loc=V(-0.05, 0.12, 0.70), rot=(52, 0, 10))
    key(ckb, S(4) + 12, loc=WSC + V(0, 0, 0.05), rot=(0, 0, 0))
    key(ckb, S(4) + 15, loc=WSC, rot=(0, 0, 0))                                              # set down on the whack spot
    gB = props.grip(ckb, (CK / 2 - 0.012, CK / 4, 0.0), 'ckb_grip', Wc)
    props.follow(R, 'L', gB, S(3) + 2, f_off=S(4) + 16, blend=5)
    rec.face.express(bite - 3, 'determined', 2); rec.face.express(W('cracked'), 'shocked', 2); rec.face.gaze(W('cracked'), 0, 0.15)
    R.pose(W('cracked') + 1, {'chest': (-6, 0, 0), 'head': (-8, 0, 0)}, ramp=2, skip=('hand.L', 'hand.R'))
    R.pose(W('wasn') + 2, {'hand.R': (-0.55, 0.62, 0.55, 0.92), 'chest': (5, 0, -5), 'head': (5, 0, -11)}, ramp=8, skip=('hand.L',))
    rec.face.express(W('wasn'), 'sad', 3); rec.face.gaze(W('wasn'), 0.3, -0.3)          # hurt, not angry (r1 + r2 critic)
    P.slam(S(3) + 10, **fr(rec, SPOT, 'MCU', az=22, el=-1), dur=10)
    P.push(S(3) + 12, W('something'), **fr(rec, SPOT, 'MCU', az=18, el=-1, lens=48))
    P.whip(W('cracked'), **fr(rec, SPOT, 'ECU', az=26, el=0), dur=6); P.shake(W('cracked'), 9, 0.012)
    P.slam(W('wasn') + 4, **fr(rec, SPOT, 'MCU', az=10, el=-2), dur=10)
    beat(S(3) + 12, 'recruit MCU', 'recruit_head', 'ck_r9'); beat(bite + 1, 'bite', 'recruit_head', 'ck_r9'); beat(W('cracked') + 2, 'ECU crack', 'recruit_head')
    beat(W('cracker', after=10.5), 'jaw', 'recruit_head')

    # ================= L4 "So he grabbed his rifle, and it took two whacks just to split it."
    vis(ckb, fdb - 7, S(4) + 15)
    ckw = cracker_at('ck_whack', WSC, S(4) + 16)                                              # identical cracker takes over on the table
    rif_r, gRr, gLr = rifle_obj('rifle_rec')
    LEAN = V(-0.62, 0.30, 0.0)
    rk(rif_r, F0 - 8, LEAN, 0, 0, side=15); rk(rif_r, S(4) + 18, LEAN, 0, 0, side=15)
    rk(rif_r, S(4) + 27, V(-0.56, 0.46, 0.26), 4, 0, side=4)                                 # up past his right side, never across his face
    w1, w2 = W('whacks') + 2, W('split') + 1
    strike(R, rif_r, WS + V(0, 0, CT), [w1, w2], side=16.0)
    rk(rif_r, w2 + 16, WS + V(0, 0.02, 0.10), 7, side=16); rk(rif_r, S(5) + 6, WS + V(0, 0.02, 0.10), 7, side=16)
    rk(rif_r, S(5) + 7, LEAN, 0, 0, side=15, ip='CONSTANT')                                  # back against the table (off screen)
    props.follow(R, 'R', gRr, S(4) + 18, f_off=S(5) + 4, blend=8); props.follow(R, 'L', gLr, S(4) + 30, f_off=S(5) + 4, blend=6)
    key(ckw, w1 - 1, loc=WSC, scale=(1, 1, 1)); key(ckw, w1, loc=WSC, scale=(1.08, 1.08, 0.7))  # first whack: it only bounces
    key(ckw, w1 + 3, loc=WSC + V(0, 0, 0.03), scale=(1, 1, 1)); key(ckw, w1 + 6, loc=WSC)
    props.crumbs('ck_whack_c1', WSC + V(0, 0, CT / 2), w1, n=4, spread=0.12, up=0.08, dur=8, floor=TOP, c=Wc, seed=3)
    vis(ckw, S(4) + 16, w2 - 1)
    hl4, hr4 = split('ck_whack_s', WSC, w2, S(10) - 4, seed=4)
    rec.face.express(S(4), 'angry', 3); rec.face.express(w2 + 3, 'excited', 3)
    P.orbit(S(4), S(4) + 36, center=(SPOT[0], SPOT[1], 0.72), radius=1.25, az0=8, az1=-34, z=0.88, lens=34, aim_z=0.70)
    P.slam(S(4) + 46, **shot(V(-0.09, 0.22, 0.68), -40, 2, 1.25, 1.10), dur=8)            # rifle, cracker AND his whole face
    P.push(w2 + 1, w2 + 16, **shot(WSC + V(0, 0, 0.04), -34, 22, 0.55, 0.40))
    beat(S(4) + 22, 'grab rifle (orbit)', 'recruit_head', 'rifle_rec'); beat(w1, 'whack 1', 'ck_whack', 'rifle_rec', 'recruit_head')
    beat(w2, 'whack 2 split', 'ck_whack_s_L', 'rifle_rec'); beat(w2 + 12, 'halves', 'ck_whack_s_L', 'ck_whack_s_R')

    # ================= L5 "The old soldiers just laughed. 'Soak it in your coffee, kid.'"
    O.pose(S(5) + 2, 'laugh', ramp=6); O2.pose(S(5) + 4, 'laugh', ramp=6)
    old.face.express(S(5), 'joy', 3); old2.face.express(S(5) + 2, 'joy', 3); O2.hop(S(5) + 10, 0.03, 10); O2.hop(S(5) + 30, 0.025, 10); O.hop(S(5) + 18, 0.02, 10)
    q0 = W('soak'); O.pose(q0 - 4, {'hand.R': (0.20, 0.95, 0.25, 1.0), 'hand.L': (0.55, 0.30, -0.70, 0.75), 'chest': (2, 0, -4), 'head': (-2, 0, 4)}, ramp=6)
    old.face.express(q0 - 2, 'smug', 3)
    old.face.talk([w for w in T.all_words() if q0 - 3 <= round(w[0] * 30) <= W('kid') + 4])
    old2.face.express(q0 + 6, 'happy', 4)
    P.whip(S(5) + 8, pos=V(-0.72, 0.62, 1.02), aim=V(-1.12, 2.34, 0.74), lens=30, dur=8)
    P.slam(q0 + 8, **fr(old, O_FIRE, 'CU', az=-6, el=0, off=(0, 0, -0.07)), dur=8)
    beat(W('laughed'), 'old hands laugh', 'oldhand_head', 'oldhand2_head'); beat(W('coffee'), 'quote CU', 'oldhand_head')

    # ================= L6 "So he did, and skimmed off the bugs that floated up."
    piece = cracker_at('ck_dunk', hl4.location.copy(), S(5) + 24, S(10) - 4)                  # a broken-off piece (swapped in off screen)
    for o_ in (piece,): o_.scale = (0.55, 0.55, 1.0)
    vis(hl4, W('split') + 1, S(5) + 23)
    pc0 = WSC + V(-0.055, -0.012, 0)
    key(piece, S(5) + 24, loc=pc0, rot=(0, 0, -16)); key(piece, S(5) + 40, loc=MUG + V(0.02, -0.02, 0.30), rot=(-62, 0, 0))
    key(piece, S(6) + 2, loc=MUG + V(0.02, -0.02, 0.27), rot=(-62, 0, 0))
    key(piece, W('did') + 4, loc=MUG + V(0.01, 0.0, 0.10), rot=(-66, 0, 0))                   # dunk
    key(piece, W('did') + 9, loc=MUG + V(0.01, 0.0, 0.095), rot=(-66, 0, 0))
    key(piece, W('did') + 22, loc=MUG + V(-0.12, 0.06, 0.34), rot=(-50, 0, -10))               # lifts the soaked piece out of the mug
    key(piece, S(7) - 6, loc=MUG + V(-0.12, 0.06, 0.34), rot=(-50, 0, -10))
    vis(piece, S(5) + 24, S(7) - 6)
    gP = props.grip(piece, (0, 0, 0.045), 'piece_grip', Wc)
    props.follow(R, 'R', gP, S(5) + 24, f_off=S(7) - 7, blend=6)
    rnd = random.Random(11); bugs = []
    for i in range(5):
        a = rnd.uniform(0, 2 * math.pi); r_ = rnd.uniform(0.018, 0.042); p = MUG + V(math.cos(a) * r_, math.sin(a) * r_, 0); p.z = LIQ
        bg = props.bug(f'bug{i}', 0.017, c=Wc); f_up = W('did') + 12 + 3 * i
        key(bg, f_up, loc=p - V(0, 0, 0.016), rot=(0, 0, math.degrees(a) + 90)); key(bg, f_up + 8, loc=p, rot=(0, 0, math.degrees(a) + 100), ip='BEZIER')
        key(bg, f_up + 60, loc=p + V(rnd.uniform(-0.006, 0.006), rnd.uniform(-0.006, 0.006), 0), rot=(0, 0, math.degrees(a) + 130))
        vis(bg, f_up, S(10) - 4); bugs.append((bg, p))
    sp = props.spoon('spoon', c=Wc, length=0.25); BOWL = Vector((0, -0.004, 0.242))          # long handle keeps his hand above the macro
    def spoon_key(f, bowl, rot):  # key the spoon so its BOWL centre is at `bowl` (world)
        R_ = Euler([math.radians(a) for a in rot]).to_matrix(); key(sp, f, loc=Vector(bowl) - R_ @ BOWL, rot=rot)
    REST, RROT = MUG + V(0.025, -0.01, 0.055), (162, 0, 20)                                  # resting in the mug, handle up
    spoon_key(F0 - 8, REST, RROT); sk0 = W('skimmed'); spoon_key(sk0 - 6, REST, RROT)
    L0 = LIQ - MUG.z                                                                        # skim: dip, sweep, lift a bug out, flick it
    spoon_key(sk0 - 1, MUG + V(0.04, -0.03, L0 + 0.05), (150, 0, 20))
    spoon_key(sk0 + 4, MUG + V(0.03, -0.025, L0 + 0.002), (150, 0, 20))
    spoon_key(sk0 + 12, MUG + V(-0.02, 0.01, L0 + 0.002), (150, 0, 40))
    spoon_key(sk0 + 20, MUG + V(-0.01, -0.03, L0 + 0.10), (140, 0, 30))
    spoon_key(sk0 + 26, MUG + V(0.07, -0.07, L0 + 0.13), (120, 0, 10))
    spoon_key(sk0 + 34, MUG + V(0.04, -0.02, L0 + 0.06), (150, 0, 20))
    spoon_key(sk0 + 44, REST, RROT)
    gS = props.grip(sp, (0, 0, 0.0), 'spoon_grip', Wc); props.follow(R, 'L', gS, sk0 - 2, f_off=sk0 + 44, blend=6)
    bg, bp = bugs[2]                                                                      # the bug that rides the spoon out
    for f in range(sk0 + 12, sk0 + 27):
        m = at(sp, f); key(bg, f, loc=m @ BOWL + V(0, 0, 0.004))
    for k, f in enumerate(range(sk0 + 27, sk0 + 40)):
        t = (k + 1) / 13; m = at(sp, sk0 + 26); b0 = m @ BOWL
        key(bg, f, loc=b0 + V(0.22 * t, -0.08 * t, 0.18 * t - 0.5 * t * t), rot=(t * 400, t * 200, 0))
    vis(bg, W('did') + 14, sk0 + 39)
    rec.face.express(S(6), 'determined', 3); rec.face.express(sk0 + 6, 'pain', 3); rec.face.gaze(sk0, 0, -0.8)
    R.pose(S(6), {'chest': (10, 0, 0), 'head': (16, 0, 0)}, ramp=8, skip=('hand.L', 'hand.R'))
    P.whip(S(6) + 8, **shot(V(-0.28, 0.26, 0.64), -8, 10, 1.15, 1.0), dur=8)           # him + the mug, then tilt down into it
    P.push(W('did') + 6, W('did') + 22, **shot(MUG + V(0, 0, 0.085), 12, 32, 0.40, 0.26))      # tilt down into the mug
    beat(S(6) + 10, 'dunk MCU', 'recruit_head', 'ck_dunk'); beat(sk0 + 8, 'skim', 'mug', 'spoon', 'bug2'); beat(sk0 + 22, 'bug out', 'bug2', 'spoon')

    # ================= L7 "Then the cook offered him a deal: one warm, soft loaf for his whole box."
    K_DEAL = (-0.80, 0.24, 70)
    K.walk(W('skimmed') - 2, S(7) - 4, [(COOK[0], COOK[1]), (-1.05, 0.40), (K_DEAL[0], K_DEAL[1])], stride=0.30)
    K.turn_body(S(7) + 2, K_DEAL[2], ramp=8)
    R.turn_body(S(7) + 6, -38, ramp=10)
    loaf = props.loaf('loaf', c=Wc); LOAF = V(-0.47, 0.09, 0.66)
    key(loaf, S(7) - 2, loc=LOAF + V(-0.20, 0.05, -0.10), rot=(0, 0, 20)); key(loaf, S(7) + 10, loc=LOAF, rot=(0, 0, 10))
    key(loaf, W('soft') + 2, loc=LOAF + V(0.02, 0, 0.02), rot=(0, 0, 8)); key(loaf, S(8) - 2, loc=LOAF + V(0.02, 0, 0.02), rot=(0, 0, 8))
    sw = S(8) + 2                                                                          # the swap hides inside the slam at S(8)
    gLf = props.grip(loaf, (0.0, 0.0, -0.005), 'loaf_grip', Wc); props.follow(K, 'R', gLf, S(7) - 2, f_off=sw - 2, blend=6)
    vis(loaf, S(7) - 8, sw - 1)
    for s_ in props.steam('loafsteam', (0, 0, 0.09), n=3, h=0.22, c=Wc): s_.parent = loaf; vis(s_, S(7), sw - 1)
    cook.face.express(S(7), 'happy', 3); K.look(W('deal'), nod=4, turn=-10, tilt=8, ramp=6)
    rec.face.express(S(7) + 2, 'confused', 3); rec.face.gaze(S(7) + 2, -0.5, 0.0)
    rec.face.express(W('soft'), 'excited', 3); R.look(W('soft'), nod=6, turn=-14, ramp=6)
    gx1, gx2 = props.grip(box_, (-0.165, -0.05, 0.10), 'box_gL', Wc), props.grip(box_, (0.165, -0.05, 0.10), 'box_gR', Wc)
    BOXUP = BOX + V(-0.13, 0.11, 0.25)
    key(box_, W('whole') - 6, loc=BOX); key(box_, W('box') + 4, loc=BOXUP, rot=(0, 0, -20))  # he lifts his whole box to offer it
    props.follow(R, 'R', gx1, W('whole') - 6, f_off=S(8), blend=5); props.follow(R, 'L', gx2, W('whole') - 6, f_off=S(8), blend=5)
    for c_, fd, p, rz in pile[:-1]:
        c_.parent = box_; c_.matrix_parent_inverse = Matrix.Translation(-BOX)
    P.slam(S(7) + 10, **shot(V(-0.36, 0.28, 0.74), -6, 5, 1.65, 2.28), dur=10)
    P.push(W('warm') - 4, W('soft') + 8, **shot(LOAF + V(0, 0, 0.05), -12, 12, 0.58, 0.42))
    P.whip(W('whole') + 4, **shot(BOXUP + V(0, 0, 0.06), -24, 14, 0.78, 0.66), dur=8)
    beat(S(7) + 14, 'deal two-shot', 'cook_head', 'recruit_head', 'loaf', 'kidbox'); beat(W('soft') + 4, 'loaf CU', 'loaf'); beat(W('box') + 4, 'box', 'kidbox')

    # ================= L8 "Best trade of the war, he thought."  /  L9 "The cook just smiled."
    R.snap(sw, 'hug', root=(SPOT[0], SPOT[1], 8)); rec.face.express(sw, 'joy', 1)
    K.snap(sw, 'carry', root=(K_DEAL[0], K_DEAL[1], -124)); cook.face.express(sw, 'smug', 1)
    loaf2 = props.loaf('loaf_hug', c=Wc); hpL, hpR = props.hand_point(R, 'L', sw + 1), props.hand_point(R, 'R', sw + 1)
    props.hold(R, loaf2, 'R', sw + 1, loc=(hpL + hpR) / 2 + V(0, -0.03, 0.02), rot=(0, 0, math.radians(8)), follow_rot=False); vis(loaf2, sw, S(10) - 4)
    box2, _ = props.crate('kidbox_c', size=(0.32, 0.25, 0.15), c=Wc, fill=lambda i: props.cracker(f'kb2_{i}', CK * 0.9, CT, c=Wc))
    ya = math.radians(-124); kf = V(math.sin(ya), -math.cos(ya), 0)
    box2.location = bone_pos(K, 'chest', sw + 1) + kf * 0.24 + V(0, 0, -0.16); box2.rotation_euler = (0, 0, ya)
    ride(K, box2, 'chest', sw + 1); vis(box2, sw, S(11) - 11)
    g2l, g2r = props.grip(box2, (0.165, -0.04, 0.09), 'box2_gL', Wc), props.grip(box2, (-0.165, -0.04, 0.09), 'box2_gR', Wc)
    props.follow(K, 'L', g2l, sw + 1, f_off=S(11) - 13, blend=1); props.follow(K, 'R', g2r, sw + 1, f_off=S(11) - 13, blend=1)
    vis(box_, S(2) - 12, sw - 1, kids=False)                          # the box alone: each cracker keeps its own drop timing
    for c_, fd, p, rz in pile[:-1]: vis(c_, fd - 7, sw - 1)
    K_STOP = (-1.42, 0.66, -124)
    K.walk(sw + 8, S(9) - 2, [(K_DEAL[0], K_DEAL[1]), (K_STOP[0], K_STOP[1])], stride=0.30)
    K.look(S(9) + 2, nod=-4, turn=66, tilt=8, ramp=7); cook.face.express(W('smiled') - 2, 'smug', 3)
    P.slam(S(8) + 8, **fr(rec, SPOT, 'MCU', az=14, el=2), dur=8)
    P.orbit(S(8) + 9, S(9) - 4, center=(SPOT[0], SPOT[1], 0.70), radius=1.05, az0=14, az1=40, z=0.80, aim_z=0.76)
    P.slam(S(9) + 8, **fr(cook, K_STOP, 'CU', az=68, el=2, off=(0, 0, -0.07)), dur=8)
    beat(S(8) + 10, 'hug', 'recruit_head', 'loaf_hug'); beat(W('smiled') + 4, 'cook smiles', 'cook_head')

    # ================= L10 (DUSK) "But a week later, he unwrapped the loaf, and it was green, fuzzy and falling apart."
    D = S(10)                                                                              # light change hides inside the whip
    for o_, k_, v0, v1 in ((sun.data, 'energy', 4.2, 3.0), (fill.data, 'energy', 230, 120), (rim.data, 'energy', 380, 260)):
        setattr(o_, k_, v0); o_.keyframe_insert(k_, frame=D - 0.6); setattr(o_, k_, v1); o_.keyframe_insert(k_, frame=D - 0.5)
    sun.data.color = (1.0, 0.86, 0.64); sun.data.keyframe_insert('color', frame=D - 0.6); sun.data.color = (1.0, 0.58, 0.32); sun.data.keyframe_insert('color', frame=D - 0.5)
    sun.rotation_euler = Euler([math.radians(a) for a in (50, 0, -34)]); sun.keyframe_insert('rotation_euler', frame=D - 0.6)
    sun.rotation_euler = Euler([math.radians(a) for a in (76, 0, -58)]); sun.keyframe_insert('rotation_euler', frame=D - 0.5)
    ramp = next(n for n in sky.node_tree.nodes if n.bl_idname == 'ShaderNodeValToRGB')
    els = sorted(ramp.color_ramp.elements, key=lambda e: e.position); dusk = [C('#4A4A66'), C('#F4A36A'), C('#D08E98'), C('#4566B0')]
    for e_, c1 in zip(els, dusk):
        e_.keyframe_insert('color', frame=D - 0.6); e_.color = (*c1, 1); e_.keyframe_insert('color', frame=D - 0.5)
    fl = bpy.data.objects.get('fire_light')
    if fl: fl.data.energy = 120; fl.data.keyframe_insert('energy', frame=D - 0.6); fl.data.energy = 260; fl.data.keyframe_insert('energy', frame=D - 0.5)
    for idb in (sun.data, fill.data, rim.data, sun, sky.node_tree) + ((fl.data,) if fl else ()):
        for fc in fcurves(idb):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    R.snap(D, 'carry', root=SPOT); rec.face.express(D, 'happy', 1); rec.face.gaze(D, 0, -0.7)
    BUN = WS + V(0, -0.02, 0)
    bundle = props.cloth('bundle', c=Wc); bundle.location = BUN; vis(bundle, D)
    loaf3 = props.loaf('loaf_moldy', c=Wc); loaf3.location = BUN + V(0, 0, 0.005); vis(loaf3, D)
    props.mould(loaf3, F0, 0.0); props.mould(loaf3, D, 0.80); props.mould(loaf3, W('fuzzy'), 1.0)
    op = bundle.data.shape_keys.key_blocks['open']; op.value = 0; op.keyframe_insert('value', frame=W('unwrapped') - 2)
    op.value = 1.0; op.keyframe_insert('value', frame=W('unwrapped') + 16)
    R.pose(W('unwrapped') - 2, {'chest': (10, 0, 0), 'head': (14, 0, 0)}, ramp=6, skip=('hand.L', 'hand.R'))
    u0 = W('unwrapped')
    for side_, sx in (('L', 1), ('R', -1)):                                                  # both hands take a corner and pull the cloth open
        tg = props.target(f'cloth_{side_}', [(u0 - 8, BUN + V(sx * 0.06, -0.10, 0.15)), (u0 - 2, BUN + V(sx * 0.08, -0.07, 0.13)),
                                            (u0 + 16, BUN + V(sx * 0.25, -0.17, 0.03)), (u0 + 30, BUN + V(sx * 0.27, -0.20, 0.06))], c=Wc)
        props.follow(R, side_, tg, u0 - 6, f_off=u0 + 30, blend=5)
    rec.face.express(W('green') - 2, 'shocked', 2); rec.face.express(W('fuzzy'), 'scared', 4)
    sq = W('falling') + 3; top = BUN + V(0, 0, 0.13)
    press = props.target('press', [(sq - 12, top + V(-0.03, -0.10, 0.12)), (sq - 2, top + V(0, -0.01, 0.03)), (sq + 1, top + V(0, 0, -0.03)),
                                   (sq + 8, top + V(0, 0, -0.045)), (sq + 20, top + V(-0.02, -0.08, 0.10))], c=Wc)
    props.follow(R, 'R', press, sq - 10, f_off=sq + 18, blend=5)
    sk = loaf3.data.shape_keys.key_blocks['slump']; sk.value = 0; sk.keyframe_insert('value', frame=sq - 1); sk.value = 1.0; sk.keyframe_insert('value', frame=sq + 4)
    key(loaf3, sq - 1, scale=(1, 1, 1)); key(loaf3, sq + 4, scale=(1.10, 1.10, 0.58))       # it collapses under his thumb
    rec.face.express(sq, 'sad', 2); rec.face.gaze(sq, 0, -0.8); P.shake(sq, 6, 0.008)            # disgusted-sad, not angry
    P.slam(D + 8, **fr(rec, SPOT, 'MS', az=12, el=9), dur=10)
    P.push(W('unwrapped') - 2, W('loaf', after=30.5) + 14, **shot(V(-0.15, 0.20, 0.66), 8, 18, 1.05, 0.96))      # keeps the loaf in frame
    gs = shot(V(-0.15, 0.16, 0.67), 6, 22, 0.95, 0.86); P.slam(W('green') + 6, **gs, dur=8)
    orbit_from(P, W('green') + 6, S(11) - 3, gs, 6, 26)                                       # arcs round the ruined loaf
    beat(D + 12, 'dusk MS', 'recruit_head', 'bundle'); beat(W('unwrapped') + 14, 'unwrapped', 'loaf_moldy', 'recruit_head')
    beat(W('green') + 8, 'green', 'loaf_moldy', 'recruit_head'); beat(sq + 4, 'squish', 'loaf_moldy', 'recruit_head')

    # ================= L11 "The crackers he'd traded away? Exactly like the day they were baked."
    K11 = COOK; tc = S(11) - 10
    K.snap(tc, {'hand.L': (0.35, 0.55, -0.55, 0.80), 'hand.R': (0.30, 0.62, 0.20, 0.86), 'chest': (-2, 0, 0), 'head': (4, 0, 6)}, root=K11)
    cook.face.express(tc, 'smug', 1)
    yaw = math.radians(K11[2]); fwd = V(math.sin(yaw), -math.cos(yaw), 0); right = V(fwd.y, -fwd.x, 0)
    kh = V(K11[0], K11[1], cook.spec['head']['z'])
    CKP11 = kh + fwd * 0.22 + right * 0.07 + V(0, 0, -0.235)                                  # held up in front of his chest, face to camera
    ck11 = cracker_at('ck_proud', CKP11, tc, S(12) + 30, rot=(90, 0, K11[2]))
    k1, k2 = W('exactly') + 4, W('exactly') + 13
    key(ck11, tc, loc=CKP11, rot=(90, 0, K11[2]))
    for kf in (k1, k2):                                                                    # each rap: the cracker barely moves (hard as a rock)
        key(ck11, kf - 1, loc=CKP11, rot=(90, 0, K11[2])); key(ck11, kf + 1, loc=CKP11 + fwd * -0.008, rot=(88, 0, K11[2])); key(ck11, kf + 4, loc=CKP11, rot=(90, 0, K11[2]))
        P.shake(kf, 4, 0.004)
    gk = props.grip(ck11, (CK / 2 - 0.012, 0, 0), 'ck11_g', Wc); props.follow(K, 'R', gk, tc, f_off=S(12) + 30, blend=1)
    face = CKP11 + fwd * 0.05                                                              # the cracker's front face
    rap = props.target('rap', [(tc, face + right * -0.16 + V(0, 0, -0.10)), (k1 - 6, face + right * -0.12 + fwd * 0.10),
                               (k1, face + right * -0.02), (k1 + 4, face + right * -0.10 + fwd * 0.08), (k2, face + right * -0.03),
                               (k2 + 6, face + right * -0.12 + fwd * 0.10), (k2 + 16, face + right * -0.18 + V(0, 0, -0.12))], c=Wc)
    props.follow(K, 'L', rap, tc, f_off=S(12) + 30, blend=1)
    K.look(k1 - 2, nod=6, turn=-4, tilt=6, ramp=5); K.look(W('baked') - 2, nod=-2, turn=-8, tilt=-6, ramp=6)
    gm = look.flat('TK_glint', C('#FFF4D6'), strength=4.0)                                 # a star glint on "baked": good as new
    glint = props.join([props.ellipsoid('glint_a', (0.045, 0.0035, 0.003), (0, 0, 0), [gm], seg=(10, 6), coll=Wc),
                        props.ellipsoid('glint_b', (0.0035, 0.045, 0.003), (0, 0, 0), [gm], seg=(10, 6), coll=Wc)], 'glint')
    glint.parent = ck11; glint.location = (CK / 2 - 0.02, CK / 2 - 0.02, CT / 2 + 0.004); gb = W('baked')
    for f_, sc_, rz in ((gb - 2, 0.0, 0), (gb + 2, 1.25, 25), (gb + 6, 0.8, 45), (gb + 11, 0.0, 70)): key(glint, f_, rot=(0, 0, rz), scale=(sc_, sc_, sc_))
    vis(glint, gb - 2, gb + 12)
    cm = fr(cook, K11, 'MCU', az=-14, el=2, off=(0.0, 0, 0.02)); P.whip(S(11) + 8, **cm, dur=8)
    orbit_from(P, S(11) + 8, W('exactly') - 2, cm, K11[2] - 14, K11[2] + 4)                   # a slow arc while he gloats
    P.push(W('exactly'), W('baked') + 8, **fr(cook, K11, 'MCU', az=-10, el=1, off=(0.0, 0, 0.06), lens=50))
    beat(S(11) + 12, 'cook + cracker', 'cook_head', 'ck_proud'); beat(k1, 'knock', 'ck_proud', 'cook_head')

    # ================= L12 "You see, mold needs water, and hardtack is baked until almost none is left."
    rnd = random.Random(17); bm_ = look.mat('TK_bead', C('#E8F2FF'), rough=0.02, spec=1.0, coat=1.0, emission=((0.75, 0.88, 1.0), 0.35))
    for i in range(14):                                                                   # beads of water sitting in the fuzz
        a = rnd.uniform(0, 2 * math.pi); u = rnd.uniform(0.1, 0.85); rr = rnd.uniform(0.007, 0.012)
        dx, dy = math.cos(a) * u * 0.16, math.sin(a) * u * 0.105                               # on the SQUASHED loaf (about 3 cm high now)
        hz = 0.005 + 0.030 * math.sqrt(max(0.0, 1 - (dx / 0.16) ** 2 - (dy / 0.105) ** 2)) + rr * 0.55
        bead = props.ellipsoid(f'bead{i}', (rr, rr, rr * 0.8), (0, 0, 0), [bm_], seg=(12, 8), coll=Wc)
        bead.location = BUN + V(dx, dy, hz); vis(bead, S(12) - 6, S(12) + 60)
    TRAY = V(OVEN.x, OVEN.y - 0.68, 0.30)
    tray = props.box('tray', (0.46, 0.34, 0.02), TRAY, [look.mat('TK_tray', C('#55565E'), rough=0.4, metal=0.6)], Wc, bevel=0.004); look.outline(tray, 0.004)
    stand = props.box('tray_stand', (0.40, 0.28, 0.29), TRAY - V(0, 0, 0.155), [look.mat('TK_brick2', C('#A85A3A'), rough=0.9, brush=0.12, paint=0.14)], Wc, bevel=0.01)
    look.outline(stand, 0.006)
    for i in range(6):
        p = TRAY + V(-0.15 + 0.15 * (i % 3), -0.08 + 0.16 * (i // 3), 0.01 + CT / 2)
        c_ = props.cracker(f'ck_tray{i}', 0.13, CT, c=Wc); c_.location = p
        b0 = p + V(0, 0, CT / 2)
        for w_ in props.steam(f'traysteam{i}', b0, n=1, h=0.26, c=Wc, seed=10 + i):
            base_origin(w_, b0); vis(w_, S(12) + 40); w_.data.transform(Matrix.Diagonal((0.55, 1, 1, 1)))   # thinner wisps
            key(w_, S(12) + 40, loc=b0, scale=(1, 1, 0.12)); key(w_, S(12) + 76 + 4 * i, loc=b0 + V(0, 0, 0.02), scale=(1, 1, 1.0))
            key(w_, F1, loc=b0 + V(0, 0, 0.08), scale=(1, 1, 1.15))
    ovf = look.area('ovenfill', tuple(TRAY + V(0.3, -0.9, 0.5)), (62, 0, 18), 0, (1.0, 0.76, 0.52), 1.2)
    a2 = W('and', after=40.0)
    ovf.data.energy = 0; ovf.data.keyframe_insert('energy', frame=a2 + 1); ovf.data.energy = 40; ovf.data.keyframe_insert('energy', frame=a2 + 2)
    P.slam(S(12) + 8, **shot(BUN + V(0, 0, 0.08), 22, 16, 0.40, 0.26), dur=8)
    P.push(S(12) + 10, W('and', after=40.0) - 2, **shot(BUN + V(0.01, 0, 0.075), 30, 14, 0.30, 0.20))   # creeping in on the wet fuzz
    P.whip(a2 + 8, **shot(TRAY + V(0, 0.08, 0.16), -8, 24, 1.0, 0.78), dur=8)
    P.push(a2 + 10, F1 - 14, **shot(TRAY + V(0, 0.04, 0.10), -6, 20, 0.72, 0.56))
    P.exit(F1 - 12, F1, pos=orbit_pos(TRAY + V(0, 0.04, 0.10), -6, 20, 0.72) + V(0.25, 0.10, 0.05), aim=TRAY + V(1.6, 0.6, 0.10))
    beat(S(12) + 12, 'mold macro', 'loaf_moldy'); beat(a2 + 14, 'oven tray', 'tray'); beat(F1 - 16, 'tray push', 'tray')
    P.build(); actors = ((rec, R), (old, O), (old2, O2), (cook, K))
    for ch_, A__ in actors: ch_.face.bake()
    stm = bpy.data.materials.get('TK_steam')
    if stm: stm.node_tree.nodes['MIX'].inputs[0].default_value = 0.20
    look.compositor(sc, bloom=0.40, warmth=0.035, vignette=0.14, haze=0.30, haze_col=C('#B5E3F2'), beams=0.45, beam_pos=(0.04, 0.98), saturation=1.08)

# =====================================================================================================================
elif SET == 'cupboard':
    look.world_sky(sc, zenith=C('#3A3A44'), horizon=C('#5A5248'), ground=C('#2A2622'), strength=0.7)
    Wc = world.coll('CUP')
    wood = look.mat('TK_cupwood', C('#C08A55'), rough=0.8, brush=0.12, grain=0.5, paint=0.12)
    back = look.mat('TK_cupback', C('#6F8E7A'), rough=0.9, brush=0.1, paint=0.12, paint_scale=3)
    props.box('cup_back', (2.4, 0.06, 1.6), (0, 0.32, 0.8), [back], Wc, bevel=0)
    for z in (0.0, 0.62):
        sh = props.box(f'shelf{z}', (2.4, 0.42, 0.04), (0, 0.1, z), [wood], Wc, bevel=0.006); look.outline(sh, 0.006)
    for side in (-1, 1):
        sd = props.box(f'side{side}', (0.05, 0.42, 1.4), (side * 0.78, 0.1, 0.6), [wood], Wc, bevel=0.006); look.outline(sd, 0.006)
    jar, pasta = props.pasta_jar('jar', (-0.05, 0.05, 0.02), c=Wc, seed=1)
    jg = bpy.data.materials['TK_jarglass'].node_tree.nodes['Principled BSDF']; jg.inputs['Alpha'].default_value = 0.06
    for i, (x, col) in enumerate(((-0.42, '#C8483C'), (0.24, '#3C6EA8'), (0.50, '#E2B33A'))):
        jj = props.lathe(f'tin{i}', [(0, 0), (0.07, 0), (0.07, 0.2), (0, 0.2)], 24, loc=(x, 0.06, 0.02),
                         mats=[look.mat(f'TK_tin{i}', C(col), rough=0.5, brush=0.06, paint=0.08)], coll=Wc); look.outline(jj, 0.005)
    for i, x in enumerate((-0.28, 0.40)):                                                  # a few loose hardtack on the top shelf (they keep)
        ck = props.cracker(f'ck_cup{i}', 0.13, 0.026, c=Wc); ck.location = (x, 0.04, 0.035 + 0.013); ck.rotation_euler = (0, 0, 0.3 * i)
    look.sun('sun', (55, 0, -40), energy=3.2, color=(1.0, 0.86, 0.66), angle=8)
    look.area('fill', (-1.2, -1.5, 1.2), (60, 0, -35), 110, (0.86, 0.9, 1.0), 2.0)
    look.area('key', (0.8, -1.0, 0.9), (65, 0, 35), 60, (1.0, 0.85, 0.65), 1.0)
    cam = camera.Cam(sc, lens=40, fstop=2.0); P = film.CamPath(cam, creep=0.12)
    JAR = V(-0.05, 0.05, 0.16)
    P.start(F0, **shot(JAR + V(-0.55, 0.05, 0.05), -60, 8, 0.75, 0.60))                     # arrives mid-whip
    js = shot(JAR, -14, 8, 0.80, 0.62); P.slam(F0 + 9, **js, dur=9)
    orbit_from(P, F0 + 9, W('doesn') - 2, js, -14, 10)                                        # trucks round the jar
    P.push(W('doesn'), W('bad') + 10, **shot(JAR, -8, 7, 0.55, 0.44))
    P.exit(F1 - 9, F1, pos=orbit_pos(JAR, -8, 7, 0.55) + V(0.2, 0.08, 0.02), aim=JAR + V(1.4, 0.6, 0.0))
    P.build()
    beat(F0 + 12, 'pasta jar', 'jar'); beat(W('bad'), 'jar push', 'jar')
    look.compositor(sc, bloom=0.40, warmth=0.035, vignette=0.12, haze=0.0, beams=0.0, saturation=1.10)

# =====================================================================================================================
elif SET == 'museum':
    look.world_sky(sc, zenith=C('#1B1E33'), horizon=C('#2B2F4A'), ground=C('#1A1A24'), strength=0.5)
    Wc = world.coll('MUSEUM')
    rifle_at = props.museum_room('room', c=Wc)
    wallm = bpy.data.materials.get('TK_mwall')
    if wallm: look.mat('TK_mwall2', C('#3B3F7E'), rough=0.85, brush=0.1, paint=0.1, paint_scale=2); bpy.data.objects['room_back'].data.materials[0] = bpy.data.materials['TK_mwall2']
    case = props.museum_case('case', c=Wc, label='HARDTACK\n1863')
    if case.get('label'): case['label'].data.size = 0.052; case['label'].location.z = 0.82
    ck = props.cracker('ck_museum', 0.17, 0.026, c=Wc); ck.location = (0, 0.02, 1.075); ck.rotation_euler = (math.radians(14), 0, 0)
    for o in bpy.data.objects:
        if o.name.startswith('room_bracket'): o.hide_render = True
    brass = look.mat('TK_brass', C('#C9A35A'), rough=0.3, metal=0.8, brush=0.03)
    fr_ = bpy.data.objects.get('case_frame')
    if fr_: fr_.data.materials.clear(); fr_.data.materials.append(brass)
    cg = bpy.data.materials['case_glass'].node_tree.nodes.get('Principled BSDF')
    if cg: cg.inputs['Alpha'].default_value = 0.035
    board = props.box('rack', (0.62, 0.04, 1.40), (0.08, 0.33, 2.02), [look.mat('TK_rack', C('#4A2E22'), rough=0.6, brush=0.1, grain=0.5, paint=0.1)], Wc, bevel=0.01)
    look.outline(board, 0.006)
    RIF, TILT, RL = V(0.0, 0.27, 1.49), 18.0, 1.05                                          # on a display board, butt DOWN just over the case, tilted like f1
    rif = props.rifle('rifle_wall', length=RL, c=Wc); rif.rotation_mode = 'ZXY'; rif.location = RIF; rif.rotation_euler = (0, math.radians(TILT), math.radians(90))
    axis = V(math.sin(math.radians(TILT)), 0, math.cos(math.radians(TILT)))
    for k_, t_ in enumerate((0.42, 0.86)):
        q = RIF + axis * (t_ * RL) + V(0, 0.035, -0.03)
        props.box(f'peg{k_}', (0.05, 0.05, 0.03), q, [look.mat('TK_peg', C('#5A3A26'), rough=0.6)], Wc, bevel=0.006)
    def spot_light(name, loc, target, energy, size, color):
        L_ = bpy.data.lights.new(name, 'SPOT'); L_.energy = energy; L_.spot_size = math.radians(size); L_.spot_blend = 0.45; L_.color = color
        o_ = bpy.data.objects.new(name, L_); Wc.objects.link(o_); o_.location = loc; aim_light(o_, target); return o_
    spot_light('spot_case', (0.0, -0.7, 3.0), (0, 0.02, 1.08), 820, 30, (1.0, 0.80, 0.55))
    ck_ = look.area('casekey', (0.45, -0.95, 2.05), (0, 0, 0), 55, (1.0, 0.78, 0.55), 0.8); aim_light(ck_, (0, 0.0, 1.15))   # warm key on the CASE (not the label)
    spot_light('spot_rifle', (0.55, -0.9, 3.1), RIF + axis * 0.45, 300, 26, (1.0, 0.80, 0.55))
    spot_light('spot_back', (0.0, 0.6, 3.4), (0, 1.5, 1.4), 160, 50, (1.0, 0.72, 0.52))
    look.area('fill', (-1.5, -2.0, 1.6), (60, 0, -30), 105, (0.80, 0.80, 1.0), 3.0)
    cam = camera.Cam(sc, lens=45, fstop=2.2); P = film.CamPath(cam, creep=0.10)
    CKP = V(0, 0.02, 1.08)
    P.start(F0, **shot(CKP + V(-0.55, 0.1, 0.05), -40, 6, 0.70, 0.40))                       # arrives mid-whip (still panning right)
    cs = shot(CKP + V(0, 0, -0.04), 8, 6, 0.62, 0.44); P.slam(F0 + 10, **cs, dur=10)
    orbit_from(P, F0 + 10, W('160') - 2, cs, 8, -12)                                           # arcs round the cracker in its case
    P.slam(W('160') + 12, **shot(V(0, -0.25, 0.81), -6, 4, 0.80, 0.56), dur=12)            # crane down to the label: HARDTACK / 1863
    P.push(W('160') + 14, W('waiting') - 6, **shot(V(0, -0.25, 0.82), 4, 3, 0.70, 0.54))
    P.slam(W('waiting') + 8, **shot(V(0, 0.15, 1.62), -6, 4, 2.3, 2.05), dur=14)             # slam back + tilt up: the WHOLE rifle over the case
    P.push(W('waiting') + 10, END - 2, **shot(V(0, 0.12, 1.25), -6, 2, 1.55, 1.30))           # then settles onto the butt over the cracker (= frame 1)
    P.build(end=END)
    beat(F0 + 12, 'case CU', 'ck_museum'); beat(W('160') + 20, 'label 1863', 'case_label'); beat(W('rifle', after=49.0), 'rifle reveal', 'rifle_wall', 'ck_museum')
    beat(END, 'last frame (loops to f1)', 'rifle_wall', 'ck_museum')
    look.compositor(sc, bloom=0.45, warmth=0.05, vignette=0.12, haze=0.0, beams=0.0, saturation=1.12)

# =====================================================================================================================
cam.handheld(0.0030, 30.0, seed=7)


def alive(A, seed, f0, f1, amp=1.0):
    """life on top of the keyed acting (Dutch-flood motion review: 'frozen' actors, lesson 60): slow F-curve noise on the
    head, chest and weight, faded in/out over 12 frames at f0 / f1 (keep it off the loop frames so they still match)."""
    for bn, prop, idx, st, per in (('head', 'rotation_euler', 0, 0.07, 46), ('head', 'rotation_euler', 1, 0.10, 58), ('head', 'rotation_euler', 2, 0.06, 52),
                                   ('chest', 'rotation_euler', 0, 0.05, 70), ('chest', 'rotation_euler', 2, 0.05, 82), ('hips', 'location', 0, 0.014, 96)):
        path = f'pose.bones["{bn}"].{prop}'
        fc = next((c for c in fcurves(A.arm) if c.data_path == path and c.array_index == idx), None)
        if fc is None:
            A.arm.pose.bones[bn].keyframe_insert(prop, index=idx, frame=F0 - 4)
            fc = next((c for c in fcurves(A.arm) if c.data_path == path and c.array_index == idx), None)
        if fc is None: continue
        m = fc.modifiers.new('NOISE'); m.scale = per; m.strength = st * amp; m.phase = 1 + (seed * 7 + idx * 3) % 50; m.offset = (seed * 37) % 300
        m.use_restricted_range = True; m.frame_start = f0; m.frame_end = f1; m.blend_in = 12; m.blend_out = 12


for name_, ch_, A_ in ACTORS: alive(A_, sum(map(ord, name_)) % 97, F0 - 4, F1 + 4)     # (loop Shorts: keep f0/f1 clear of the loop frames)
world.flow_water(F0 - 10, F1 + 10)                                       # any water surface keeps moving (no glassy holds)
cam.cam.data.dof.focus_object = cam.aim                  # focus = the aim point (always on what the beat is about)
print('FILM', SET, F0, F1, 'beats', len(BEATS))
os.makedirs(OUT, exist_ok=True)
if FR == 'report':                                       # framing numbers for every beat: where each subject sits in frame
    from bpy_extras.object_utils import world_to_camera_view
    for f, name, subj in sorted(BEATS):
        sc.frame_set(f); bpy.context.view_layer.update(); line = []
        for s in subj:
            o = bpy.data.objects.get(s)
            if not o: line.append(f'{s}=?'); continue
            cen = o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
            v = world_to_camera_view(sc, cam.cam, cen); ok = 0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0
            line.append(f"{s}({v.x:.2f},{1 - v.y:.2f}{'' if ok else ' OUT'})")
        print(f'REPORT f{f:5d} {name:24s} lens {cam.cam.data.lens:5.1f} ' + ' '.join(line))
    sys.exit(0)
if FR.startswith('campath:'):                            # per-frame camera numbers: pipe into tools/campath_scan.py
    a, b = (int(x) for x in FR[8:].split('-')); prev = None; prevv = None
    ks = sorted(P.keys, key=lambda k: k['f'])                  # the planned moves: the scan exempts each one's own window
    print('MOVES ' + ' '.join(f"{int(k0['f'])}-{int(k1['f'])}:{k1['style']}" for k0, k1 in zip(ks, ks[1:]) if k1['style'] in ('slam', 'whip', 'exit', 'cut') or k0['style'] in ('slam', 'whip', 'exit', 'push')))   # pushes are planned too (eased)
    for f in range(a, b + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); m = cam.cam.matrix_world; p_ = m.translation.copy(); fwd = -(m.to_3x3() @ Vector((0, 0, 1)))
        if prev:
            v = p_ - prev[0]; ang = math.degrees(fwd.angle(prev[1])) if fwd.length and prev[1].length else 0.0
            acc = (v - prevv).length if prevv is not None else 0.0
            print(f'CAM f{f:5d} pos ({p_.x:6.3f},{p_.y:6.3f},{p_.z:6.3f}) speed {v.length * 1000:6.1f} mm/f  turn {ang:5.2f} deg/f  jerk {acc * 1000:6.1f}  lens {cam.cam.data.lens:5.1f}')
            prevv = v
        prev = (p_, fwd)
        near = min(((((A_.arm.matrix_world @ ((A_.arm.pose.bones[bn].head + A_.arm.pose.bones[bn].tail) / 2)) - p_).length, nm_, bn) for nm_, _, A_ in ACTORS
                    for bn in ('head', 'chest', 'hips') if bn in A_.arm.pose.bones), default=None)
        if near and near[0] < 0.45: print(f'NEAR f{f:5d}: camera {near[0]:.2f} m from {near[1]} {near[2]} (inside or grazing a character)')
    sys.exit(0)
if FR == 'none': sys.exit(0)
if FR == 'beats':
    frames = sorted({f for f, _, _ in BEATS if F0 <= f <= F1})
    with open(os.path.join(OUT, f'beats_{SET}.txt'), 'w') as fh:
        for f, name, _ in sorted(BEATS): fh.write(f'{f} {name}\n')
else: frames = film.frames_arg(FR, F0, F1)
film.render_range(sc, OUT, F0, F1, only=frames, mb_steps={f: 64 for f in P.move_starts()})   # smooth whip starts (lesson 68)
print('FILM done', len(frames))
