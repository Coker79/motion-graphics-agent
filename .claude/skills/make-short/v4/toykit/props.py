"""toykit.props: hand props and set dressing in the same painterly, outlined style as the characters.
Every builder returns the object (origin at its natural pivot: the grip for hand props, the base for set pieces).
Attach a prop to a hand with `hold(actor, prop, 'R', frame_on, frame_off)`."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from . import look
from .char import mesh_obj, subsurf, ellipsoid, lathe, tube, join

C = look.hexc


def _bevel(o, w=0.006, seg=3):
    md = o.modifiers.new('bevel', 'BEVEL'); md.width = w; md.segments = seg; md.limit_method = 'ANGLE'; return o


def coin(name, dia, th, mats=(), c=None, rim=True):
    """a round coin (origin at its centre, axis +Z). rim=True stands a torus rim proud of both faces, so a close-up catches a
    glint on it. Readable gold in a close-up: base #B98A28, rough ~0.35, metal 1, NO emission; light it with a small lamp OFF the
    face's mirror line (on the line, the flat face blows out white). Lesson 79. (A props.box coin reads as a square tile.)"""
    bm = bmesh.new()
    if rim:
        rr = th * 0.85; R = dia / 2 - rr; seg, rs = 48, 10; ring = []
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=R + rr * 0.2, radius2=R + rr * 0.2, depth=th)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append([bm.verts.new(((R + rr * math.cos(2 * math.pi * j / rs)) * math.cos(a), (R + rr * math.cos(2 * math.pi * j / rs)) * math.sin(a),
                                       rr * math.sin(2 * math.pi * j / rs))) for j in range(rs)])
        for i in range(seg):
            for j in range(rs): bm.faces.new((ring[i][j], ring[(i + 1) % seg][j], ring[(i + 1) % seg][(j + 1) % rs], ring[i][(j + 1) % rs]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    else: bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40, radius1=dia / 2, radius2=dia / 2, depth=th)
    o = mesh_obj(name, bm, mats, smooth=True, coll=c); o.data.set_sharp_from_angle(angle=math.radians(40))
    if not rim: _bevel(o, th * 0.2, 2)
    return o


def box(name, size, loc=(0, 0, 0), mats=(), c=None, bevel=0.006):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = mesh_obj(name, bm, mats, smooth=False, coll=c); o.location = loc
    if bevel: _bevel(o, bevel)
    return o


# ---------------------------------------------------------------- hardtack cracker (procedural dock holes + toasted edges)
def cracker_mat(name='TK_hardtack', base='#E7C27A', toast='#B9813E', holes=4):
    m = bpy.data.materials.get(name)
    if m: return m
    m = look.mat(name, C(base), rough=0.85, brush=0.06, grain=0.9, grain_scale=260, paint=0.06, spec=0.2)
    nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'); src = p.inputs['Base Color'].links[0].from_socket
    tc = N('ShaderNodeTexCoord')
    # toasted edges: distance from the centre in generated coords
    sp = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Generated'], sp.inputs[0])
    def ctr(sock):
        a = N('ShaderNodeMath'); a.operation = 'SUBTRACT'; a.inputs[1].default_value = 0.5; L(sock, a.inputs[0])
        b = N('ShaderNodeMath'); b.operation = 'ABSOLUTE'; L(a.outputs[0], b.inputs[0]); return b.outputs[0]
    mx = N('ShaderNodeMath'); mx.operation = 'MAXIMUM'; L(ctr(sp.outputs['X']), mx.inputs[0]); L(ctr(sp.outputs['Y']), mx.inputs[1])
    ed = N('ShaderNodeMapRange'); ed.inputs['From Min'].default_value = 0.36; ed.inputs['From Max'].default_value = 0.5; L(mx.outputs[0], ed.inputs['Value'])
    tm = N('ShaderNodeMix'); tm.data_type = 'RGBA'; tm.blend_type = 'MIX'; L(ed.outputs[0], tm.inputs[0]); L(src, tm.inputs[6]); tm.inputs[7].default_value = (*C(toast), 1)
    # dock holes: a 4x4 grid of round dents (fraction of a cell)
    gx = N('ShaderNodeMath'); gx.operation = 'MULTIPLY'; gx.inputs[1].default_value = holes; L(sp.outputs['X'], gx.inputs[0])
    gy = N('ShaderNodeMath'); gy.operation = 'MULTIPLY'; gy.inputs[1].default_value = holes; L(sp.outputs['Y'], gy.inputs[0])
    def cell(sock):
        f = N('ShaderNodeMath'); f.operation = 'FRACT'; L(sock, f.inputs[0])
        s_ = N('ShaderNodeMath'); s_.operation = 'SUBTRACT'; s_.inputs[1].default_value = 0.5; L(f.outputs[0], s_.inputs[0]); return s_.outputs[0]
    cb = N('ShaderNodeCombineXYZ'); L(cell(gx.outputs[0]), cb.inputs[0]); L(cell(gy.outputs[0]), cb.inputs[1])
    ln = N('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L(cb.outputs[0], ln.inputs[0])
    hole = N('ShaderNodeMapRange'); hole.inputs['From Min'].default_value = 0.10; hole.inputs['From Max'].default_value = 0.06; L(ln.outputs['Value'], hole.inputs['Value'])
    # holes only on the faces (not the sides): generated Z near 0 or 1
    zf = N('ShaderNodeMath'); zf.operation = 'ABSOLUTE'
    zs = N('ShaderNodeMath'); zs.operation = 'SUBTRACT'; zs.inputs[1].default_value = 0.5; L(sp.outputs['Z'], zs.inputs[0]); L(zs.outputs[0], zf.inputs[0])
    zm = N('ShaderNodeMapRange'); zm.inputs['From Min'].default_value = 0.3; zm.inputs['From Max'].default_value = 0.45; L(zf.outputs[0], zm.inputs['Value'])
    hm = N('ShaderNodeMath'); hm.operation = 'MULTIPLY'; L(hole.outputs[0], hm.inputs[0]); L(zm.outputs[0], hm.inputs[1])
    hc = N('ShaderNodeMix'); hc.data_type = 'RGBA'; hc.blend_type = 'MIX'; L(hm.outputs[0], hc.inputs[0]); L(tm.outputs[2], hc.inputs[6])
    hc.inputs[7].default_value = (*C('#6B4420'), 1); L(hc.outputs[2], p.inputs['Base Color'])
    bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.8; bp.inputs['Distance'].default_value = 0.004; bp.invert = True
    L(hm.outputs[0], bp.inputs['Height'])
    old = p.inputs['Normal'].links[0].from_node if p.inputs['Normal'].links else None
    if old: L(old.outputs['Normal'], bp.inputs['Normal'])
    L(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def cracker(name, size=0.20, thick=0.032, c=None, ink=0.004):
    """a big square hardtack biscuit (stylized: about half a head wide), origin at its centre."""
    o = box(name, (size, size, thick), mats=[cracker_mat()], c=c, bevel=thick * 0.35)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts: v.co.z *= 1.0 + 0.04 * math.sin(v.co.x * 31) * math.sin(v.co.y * 27)       # hand-made unevenness
    bm.to_mesh(o.data); bm.free(); subsurf(o, 1, 1)
    o.modifiers.move(len(o.modifiers) - 1, len(o.modifiers) - 1)
    look.outline(o, ink); return o


def crate(name, size=(0.6, 0.42, 0.34), loc=(0, 0, 0), c=None, fill=None, ink=0.008, seed=1):
    """open wooden ration crate (planks), optionally heaped with `fill(i)`-built objects."""
    rnd = random.Random(seed); wm = look.mat(f'{name}_wood', C('#9A6B3F'), rough=0.85, brush=0.12, grain=0.6, paint=0.12)
    sx, sy, sz = size; t = 0.022; parts = []
    parts.append(box(f'{name}_bottom', (sx, sy, t), (0, 0, t / 2), [wm], c))
    for i, (w, d, x, y) in enumerate(((sx, t, 0, -sy / 2 + t / 2), (sx, t, 0, sy / 2 - t / 2), (t, sy, -sx / 2 + t / 2, 0), (t, sy, sx / 2 - t / 2, 0))):
        for k in range(3):
            hz = sz / 3 - 0.006; parts.append(box(f'{name}_pl{i}{k}', (w, d, hz), (x, y, t + hz / 2 + k * (hz + 0.006)), [wm], c))
    o = join(parts, name); o.location = loc; look.outline(o, ink)
    heap = []
    if fill:
        for i in range(9):
            f = fill(i); f.parent = o
            f.location = (rnd.uniform(-sx * 0.3, sx * 0.3), rnd.uniform(-sy * 0.28, sy * 0.28), sz * 0.72 + 0.03 * (i // 4))
            f.rotation_euler = (rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), rnd.uniform(0, math.pi)); heap.append(f)
    return o, heap


# ---------------------------------------------------------------- rifle (stylized musket)
def rifle(name, length=0.78, c=None, ink=0.004):
    """origin at the butt plate; the barrel points +Z (stand it up, or rotate to hold)."""
    wood = look.mat(f'{name}_wood', C('#7A4B2A'), rough=0.6, brush=0.1, grain=0.5, paint=0.1)
    steel = look.mat(f'{name}_steel', C('#3A3D46'), rough=0.35, metal=0.6, brush=0.03)
    L = length; parts = []
    bm = bmesh.new()       # stock: a tapered wedge from the butt to the fore-end
    prof = [(0.0, 0.055, 0.020), (0.16, 0.040, 0.018), (0.30, 0.028, 0.016), (0.62, 0.022, 0.015)]
    rings = []
    for z, w, d in prof:
        rings.append([bm.verts.new(v) for v in ((-d, -w, z * L / 0.78), (d, -w, z * L / 0.78), (d, w * 0.6, z * L / 0.78), (-d, w * 0.6, z * L / 0.78))])
    for a, b in zip(rings, rings[1:]):
        for i in range(4): bm.faces.new((a[i], a[(i + 1) % 4], b[(i + 1) % 4], b[i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    stock = mesh_obj(f'{name}_stock', bm, [wood], smooth=False, coll=c); _bevel(stock, 0.006)
    barrel = tube(f'{name}_barrel', (0, 0.012, 0.42 * L / 0.78), (0, 0.012, L), 0.009, 0.008, 4, 12, [steel], coll=c)
    plate = box(f'{name}_plate', (0.042, 0.112, 0.008), (0, -0.01, 0.002), [steel], c, bevel=0.002)
    o = join([stock, barrel, plate], name); look.outline(o, ink); return o


# ---------------------------------------------------------------- tin mug of coffee (+ floating bugs, steam)
def mug(name, r=0.055, h=0.09, c=None, ink=0.004, bugs=0, coffee='#3A1F10'):
    tin = look.mat(f'{name}_tin', C('#8E9BB0'), rough=0.4, metal=0.5, brush=0.05, paint=0.05)
    cof = look.mat(f'{name}_coffee', C(coffee), rough=0.15, brush=0.0, grain=0.0, spec=0.6)
    body = lathe(f'{name}_body', [(0, 0), (r, 0), (r * 1.02, h * 0.1), (r * 1.04, h), (r * 0.94, h), (r * 0.92, h * 0.12), (0, h * 0.12)], 32, mats=[tin], coll=c)
    liquid = lathe(f'{name}_liq', [(0, h * 0.8), (r * 0.93, h * 0.8), (r * 0.93, h * 0.78), (0, h * 0.78)], 32, mats=[cof], coll=c)
    handle = tube(f'{name}_h', (r * 0.98, 0, h * 0.78), (r * 1.6, 0, h * 0.6), 0.008, 0.008, 6, 8, [tin], coll=c)
    handle2 = tube(f'{name}_h2', (r * 1.6, 0, h * 0.6), (r * 0.98, 0, h * 0.25), 0.008, 0.008, 6, 8, [tin], coll=c)
    parts = [body, liquid, handle, handle2]
    rnd = random.Random(7)
    for i in range(bugs):
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0, r * 0.7)
        parts.append(ellipsoid(f'{name}_bug{i}', (0.012, 0.007, 0.005), (math.cos(a) * d, math.sin(a) * d, h * 0.805), [look.flat('TK_bug', C('#1A120C'))], seg=(8, 6), coll=c))
    o = join(parts, name); subsurf(o, 1, 1); look.outline(o, ink); return o


# ---------------------------------------------------------------- the soft loaf and its mouldy future (keyed with mould(frame, amount))
def loaf(name, size=(0.26, 0.17, 0.12), c=None, ink=0.005):
    o = ellipsoid(name, size, (0, 0, 0), [], seg=(40, 22), coll=c)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:
        if v.co.z < -size[2] * 0.2: v.co.z = -size[2] * 0.2 + (v.co.z + size[2] * 0.2) * 0.25        # flat bottom
        v.co.z += size[2] * 0.2
        if v.co.z > size[2] * 0.25:   # three scores across the top
            v.co.z -= 0.010 * max(0.0, math.cos(v.co.x * 3 * math.pi / size[0]) ** 24)
    bm.to_mesh(o.data); bm.free()
    m = look.mat(f'{name}_m', C('#D69A4E'), rough=0.75, brush=0.12, grain=0.6, paint=0.1)
    nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'); src = p.inputs['Base Color'].links[0].from_socket
    tc = N('ShaderNodeTexCoord'); nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 7.0; nz.inputs['Detail'].default_value = 6
    L(tc.outputs['Object'], nz.inputs['Vector'])
    amt = N('ShaderNodeValue'); amt.name = 'MOULD'; amt.outputs[0].default_value = 0.0
    # mask = smoothstep over (noise - (1 - amount))
    inv = N('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L(amt.outputs[0], inv.inputs[1])
    d = N('ShaderNodeMath'); d.operation = 'SUBTRACT'; L(nz.outputs['Fac'], d.inputs[0]); L(inv.outputs[0], d.inputs[1])
    mk = N('ShaderNodeMapRange'); mk.inputs['From Min'].default_value = -0.02; mk.inputs['From Max'].default_value = 0.06; L(d.outputs[0], mk.inputs['Value'])
    mold = N('ShaderNodeMix'); mold.data_type = 'RGBA'; mold.blend_type = 'MIX'; L(mk.outputs[0], mold.inputs[0]); L(src, mold.inputs[6])
    gv = N('ShaderNodeTexVoronoi'); gv.inputs['Scale'].default_value = 60; L(tc.outputs['Object'], gv.inputs['Vector'])
    gm = N('ShaderNodeMix'); gm.data_type = 'RGBA'; gm.blend_type = 'MIX'; L(gv.outputs['Distance'], gm.inputs[0])
    gm.inputs[6].default_value = (*C('#5E8A3A'), 1); gm.inputs[7].default_value = (*C('#A9C96A'), 1); L(gm.outputs[2], mold.inputs[7])
    L(mold.outputs[2], p.inputs['Base Color'])
    o.data.materials.append(m); subsurf(o, 1, 2)
    # slump shape key (the loaf collapses as it rots)
    o.shape_key_add(name='Basis', from_mix=False); sk = o.shape_key_add(name='slump', from_mix=False); sk.value = 0.0
    for i, v in enumerate(o.data.vertices):
        co = v.co.copy(); f = max(0.0, co.z) / size[2]
        sk.data[i].co = Vector((co.x * (1 + 0.12 * f), co.y * (1 + 0.12 * f), co.z * (1 - 0.32 * f) - 0.01 * f))
    look.outline(o, ink)
    return o


def mould(loaf_obj, f, amount, slump=None):
    m = loaf_obj.data.materials[0]; v = m.node_tree.nodes['MOULD']
    v.outputs[0].default_value = amount; v.outputs[0].keyframe_insert('default_value', frame=f)
    if slump is not None:
        sk = loaf_obj.data.shape_keys.key_blocks['slump']; sk.value = slump; sk.keyframe_insert('value', frame=f)


# ---------------------------------------------------------------- museum display case (plinth + glass + label)
def museum_case(name, c=None, label='1863', ink=0.006):
    plinth_m = look.mat(f'{name}_plinth', C('#E9E4DA'), rough=0.6, brush=0.04, paint=0.05)
    dark = look.mat(f'{name}_dark', C('#2A2730'), rough=0.5)
    glass = bpy.data.materials.new(f'{name}_glass'); glass.use_nodes = True; nt = glass.node_tree; nt.nodes.clear()
    g = nt.nodes.new('ShaderNodeBsdfPrincipled'); g.inputs['Base Color'].default_value = (0.9, 0.97, 1.0, 1); g.inputs['Roughness'].default_value = 0.02
    g.inputs['Alpha'].default_value = 0.12; out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(g.outputs[0], out.inputs[0])
    try: glass.surface_render_method = 'BLENDED'
    except Exception: pass
    plinth = box(f'{name}_plinth', (0.5, 0.5, 0.95), (0, 0, 0.475), [plinth_m], c, bevel=0.01); look.outline(plinth, ink)
    cap_ = box(f'{name}_cap', (0.54, 0.54, 0.04), (0, 0, 0.97), [dark], c, bevel=0.006); look.outline(cap_, ink)
    case = box(f'{name}_glass', (0.46, 0.46, 0.40), (0, 0, 1.19), [glass], c, bevel=0.004); case.visible_shadow = False
    edges = []
    for x in (-0.23, 0.23):
        for y in (-0.23, 0.23): edges.append(box(f'{name}_edge', (0.012, 0.012, 0.40), (x, y, 1.19), [dark], c, bevel=0.0))
    frame = join(edges, f'{name}_frame'); look.outline(frame, ink * 0.5)
    lab = None
    if label:
        bpy.ops.object.text_add(location=(0, -0.256, 0.80)); lab = bpy.context.active_object; lab.name = f'{name}_label'
        lab.data.body = label; lab.data.size = 0.07; lab.data.align_x = 'CENTER'; lab.data.extrude = 0.002
        lab.rotation_euler = (math.radians(90), 0, 0); lab.data.materials.append(dark)
        for cc in lab.users_collection: cc.objects.unlink(lab)
        (c or bpy.context.scene.collection).objects.link(lab)
    stand = box(f'{name}_stand', (0.10, 0.08, 0.06), (0, 0.02, 1.02), [dark], c, bevel=0.004)
    return dict(plinth=plinth, cap=cap_, glass=case, frame=frame, label=lab, stand=stand, top=Vector((0, 0, 1.06)))


# ---------------------------------------------------------------- holding a prop
def hold(actor, prop, side, f_on, f_off=None, loc=None, rot=None, follow_rot=True):
    """prop rides the hand bone from f_on (ChildOf with the inverse taken at f_on, so the prop keeps exactly the world
    placement it has at f_on: put it where it should sit in the hand at that frame, or pass loc/rot in world space)."""
    sc = bpy.context.scene; arm = actor.arm
    if loc is not None: prop.location = loc
    if rot is not None: prop.rotation_euler = rot
    cur = sc.frame_current; sc.frame_set(f_on); bpy.context.view_layer.update()
    cn = prop.constraints.new('CHILD_OF'); cn.target = arm; cn.subtarget = f'hand.{side}'
    pb = arm.pose.bones[f'hand.{side}']
    bw = arm.matrix_world @ pb.matrix
    if follow_rot: cn.inverse_matrix = bw.inverted()
    else:      # display props: ride the hand's POSITION only and keep their own world orientation (stay facing the camera)
        cn.use_rotation_x = cn.use_rotation_y = cn.use_rotation_z = False
        cn.inverse_matrix = Matrix.Translation(-bw.translation)
    if f_on > sc.frame_start:
        cn.influence = 0.0; cn.keyframe_insert('influence', frame=f_on - 1)
    cn.influence = 1.0; cn.keyframe_insert('influence', frame=f_on)
    if f_off is not None:
        cn.keyframe_insert('influence', frame=f_off - 1); cn.influence = 0.0; cn.keyframe_insert('influence', frame=f_off)
    sc.frame_set(cur); return cn


def hand_point(actor, side, f, ahead=0.0):
    """world position of the hand ball (plus `ahead` metres along the arm) at frame f, for placing held props."""
    sc = bpy.context.scene; cur = sc.frame_current; sc.frame_set(f); bpy.context.view_layer.update()
    arm = actor.arm; pb = arm.pose.bones[f'hand.{side}']
    m = arm.matrix_world @ pb.matrix; p = m.translation + m.to_3x3() @ Vector((0, pb.bone.length * 0.5 + ahead, 0))
    sc.frame_set(cur); return p


# ---------------------------------------------------------------- extra pieces for story beats
def cracker_halves(name, size=0.20, thick=0.032, c=None, ink=0.004):
    """the same cracker split in two along a jagged line: returns (left, right); both keep the whole cracker's centre as
    their origin so they start exactly where the whole one was, then drift apart."""
    n = 9; cut = [(0.012 * math.sin(i * 2.7) * (1 if i % 2 else -1), -size / 2 + size * i / n) for i in range(n + 1)]   # bottom -> top
    polys = {'L': [(-size / 2, -size / 2)] + cut + [(-size / 2, size / 2)],                      # left piece, CCW-ish loop
             'R': [(size / 2, size / 2)] + cut[::-1] + [(size / 2, -size / 2)]}
    out = []
    for k, poly in polys.items():
        bm = bmesh.new(); vb = [bm.verts.new((x, y, -thick / 2)) for x, y in poly]; vt = [bm.verts.new((x, y, thick / 2)) for x, y in poly]
        bm.faces.new(vb); bm.faces.new(vt[::-1])
        for i in range(len(poly)):
            j = (i + 1) % len(poly); bm.faces.new((vb[i], vt[i], vt[j], vb[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = mesh_obj(f'{name}_{k}', bm, [cracker_mat()], smooth=False, coll=c); _bevel(o, thick * 0.3, 2); look.outline(o, ink)
        out.append(o)
    return out


def field_oven(name, loc, c=None, ink=0.01):
    """a brick field oven: box with an arched dark mouth and a chimney; returns (oven, tray_anchor_vector)."""
    x, y, z = loc
    brick = look.mat(f'{name}_brick', C('#B0603F'), rough=0.9, brush=0.14, grain=0.6, paint=0.16, paint_scale=9)
    dark = look.flat(f'{name}_mouth', C('#2A1712'))
    body = box(f'{name}_body', (1.1, 0.9, 0.85), (x, y, z + 0.425), [brick], c, bevel=0.04)
    top = box(f'{name}_top', (1.2, 1.0, 0.1), (x, y, z + 0.9), [brick], c, bevel=0.03)
    chim = box(f'{name}_chim', (0.22, 0.22, 0.6), (x + 0.3, y + 0.2, z + 1.2), [brick], c, bevel=0.02)
    o = join([body, top, chim], name); look.outline(o, ink)
    mouth = lathe(f'{name}_m', [(0, 0), (0.28, 0), (0.28, 0.01), (0, 0.01)], 24, loc=(x, y - 0.452, z + 0.38), mats=[dark], coll=c)
    mouth.rotation_euler = (math.radians(90), 0, 0); mouth.scale = (1.0, 1.0, 1.0)
    glow = bpy.data.lights.new(f'{name}_glow', 'POINT'); glow.energy = 60; glow.color = (1.0, 0.55, 0.2); glow.shadow_soft_size = 0.3
    gl = bpy.data.objects.new(f'{name}_glow', glow); (c or bpy.context.scene.collection).objects.link(gl); gl.location = (x, y - 0.25, z + 0.42)
    return o, Vector((x, y - 0.32, z + 0.30))


def steam(name, loc, n=5, h=0.35, c=None, seed=0):
    """soft white wisps (emissive, semi-transparent ribbons) that rise and fade; key with steam_fade(objs, f0, f1)."""
    rnd = random.Random(seed); out = []
    m = bpy.data.materials.get('TK_steam')
    if not m:
        m = bpy.data.materials.new('TK_steam'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (1, 1, 1, 1); em.inputs[1].default_value = 1.0
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.28; mx.name = 'MIX'
        out_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out_.inputs[0])
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    for i in range(n):
        bm = bmesh.new(); px, py, pz = loc; px += rnd.uniform(-0.08, 0.08); py += rnd.uniform(-0.05, 0.05); ph = rnd.uniform(0, 6)
        prev = None
        for k in range(12):
            t = k / 11; zz = pz + h * t; xx = px + 0.04 * math.sin(ph + t * 7); w = 0.004 + 0.010 * math.sin(math.pi * t)
            a, b = bm.verts.new((xx - w, py, zz)), bm.verts.new((xx + w, py, zz))
            if prev: bm.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)
        o = mesh_obj(f'{name}{i}', bm, [m], coll=c); o.visible_shadow = False; out.append(o)
    return out


def cloth(name, size=0.52, c=None, color='#D9CDB2', ink=0.004):
    """a square cloth wrap (subdivided plane): shape key 'open' lays it flat, basis wraps around a loaf-sized lump."""
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=12, y_segments=12, size=size / 2)
    o = mesh_obj(name, bm, [look.mat(f'{name}_m', C(color), rough=0.9, brush=0.08, grain=0.4, paint=0.08)], coll=c)
    flat_ = [v.co.copy() for v in o.data.vertices]
    for v in o.data.vertices:                     # basis: gathered into a mound over the loaf (set BEFORE the shape keys)
        x, y, _ = v.co; r = math.hypot(x, y) / (size / 2)
        v.co.z = 0.17 * max(0.0, 1 - r * r) ** 0.6 + 0.01; v.co.x *= 0.62; v.co.y *= 0.62
    o.shape_key_add(name='Basis', from_mix=False); op = o.shape_key_add(name='open', from_mix=False); op.value = 0.0
    for i, (x, y, _) in enumerate(flat_):         # 'open': laid flat with soft folds
        op.data[i].co = Vector((x, y, 0.004 + 0.006 * math.sin(x * 40) * math.sin(y * 33)))
    so = o.modifiers.new('thick', 'SOLIDIFY'); so.thickness = 0.004
    look.outline(o, ink); return o


def pasta_jar(name, loc, c=None, ink=0.004, seed=0):
    rnd = random.Random(seed); x, y, z = loc
    glass = bpy.data.materials.get('TK_jarglass')
    if not glass:
        glass = bpy.data.materials.new('TK_jarglass'); glass.use_nodes = True; nt = glass.node_tree; g = nt.nodes['Principled BSDF']
        g.inputs['Base Color'].default_value = (0.85, 0.95, 1.0, 1); g.inputs['Roughness'].default_value = 0.05; g.inputs['Alpha'].default_value = 0.22
        try: glass.surface_render_method = 'BLENDED'
        except Exception: pass
    jar = lathe(f'{name}_jar', [(0, 0), (0.07, 0), (0.075, 0.02), (0.075, 0.24), (0.06, 0.26), (0, 0.26)], 28, loc=loc, mats=[glass], coll=c)
    lid = lathe(f'{name}_lid', [(0, 0.26), (0.066, 0.26), (0.066, 0.29), (0, 0.29)], 28, loc=loc, mats=[look.mat('TK_lid', C('#B8862E'), rough=0.4, metal=0.5)], coll=c)
    pm = look.mat('TK_pasta', C('#EBC873'), rough=0.6, brush=0.06, paint=0.06)
    sticks = [tube(f'{name}_p{i}', (x + rnd.uniform(-0.05, 0.05), y + rnd.uniform(-0.05, 0.05), z + 0.01), (x + rnd.uniform(-0.06, 0.06), y + rnd.uniform(-0.06, 0.06), z + 0.25), 0.005, 0.005, 2, 5, [pm], coll=c)
              for i in range(26)]
    p = join(sticks, f'{name}_pasta'); o = join([jar, lid], name); look.outline(o, ink); return o, p


def museum_room(name, c=None):
    """a dark gallery corner: deep-blue walls, a polished floor, a wall bracket for an old rifle; returns rifle anchor."""
    wall = look.mat('TK_mwall', C('#2E3A5C'), rough=0.85, brush=0.1, paint=0.1, paint_scale=2)
    floor = look.mat('TK_mfloor', C('#6B4A35'), rough=0.35, brush=0.1, paint=0.12, paint_scale=3)
    box(f'{name}_floor', (8, 8, 0.1), (0, 1, -0.05), [floor], c, bevel=0)
    w1 = box(f'{name}_back', (8, 0.2, 4), (0, 1.6, 2.0), [wall], c, bevel=0)
    trim = box(f'{name}_trim', (8, 0.06, 0.12), (0, 1.48, 0.06), [look.mat('TK_mtrim', C('#C9A35A'), rough=0.4, metal=0.4)], c, bevel=0.005)
    br = box(f'{name}_bracket', (0.9, 0.06, 0.05), (0, 1.47, 1.95), [look.mat('TK_mbr', C('#3A2A22'), rough=0.6)], c, bevel=0.01)
    return Vector((0, 1.40, 2.02))


# ---------------------------------------------------------------- hands that DO things (v4.1): follow a keyed target exactly
def follow(actor, side, target, f_on, f_off=None, blend=3):
    """the hand rides `target` (any object or empty, keyed however you like) from f_on: a COPY_LOCATION on the IK target,
    blended in over `blend` frames, so the arm reaches exactly there (noodle arms stretch a little if they must).
    f_off blends back out to the keyed pose. Use it for grips (rifle, spoon), presses and reaches."""
    pb = actor.arm.pose.bones[f'hand_ik.{side}']
    c = pb.constraints.new('COPY_LOCATION'); c.target = target; c.name = f'follow_{target.name}_{f_on}'
    c.influence = 0.0; c.keyframe_insert('influence', frame=f_on - blend)
    c.influence = 1.0; c.keyframe_insert('influence', frame=f_on)
    if f_off is not None:
        c.keyframe_insert('influence', frame=f_off); c.influence = 0.0; c.keyframe_insert('influence', frame=f_off + blend)
    return c


def grip(prop, local, name=None, c=None):
    """an empty riding `prop` at a local offset: a hand target (props.follow) that moves with the prop."""
    e = bpy.data.objects.new(name or f'{prop.name}_grip', None); (c or bpy.context.scene.collection).objects.link(e)
    e.parent = prop; e.location = local; e.empty_display_size = 0.02; return e


def target(name, keys, c=None, interp='BEZIER'):
    """an empty keyed through [(frame, (x, y, z)), ...] in world space: a path for a hand to follow."""
    e = bpy.data.objects.new(name, None); (c or bpy.context.scene.collection).objects.link(e); e.empty_display_size = 0.02
    for f, p in keys: e.location = p; e.keyframe_insert('location', frame=f)
    from .camera import fcurves
    for fc in fcurves(e):
        for kp in fc.keyframe_points: kp.interpolation = interp
    return e


def bug(name, size=0.013, c=None, ink=0.0016):
    """a cartoon weevil: glossy dark oval shell, head + snout, six bent legs; origin at its belly (sits ON a surface)."""
    shell = look.mat('TK_bugshell', C('#3B2416'), rough=0.3, brush=0.0, grain=0.0, paint=0.0, spec=0.7)
    dark = look.flat('TK_bugdark', C('#1A0F08'))
    s = size; parts = [ellipsoid(f'{name}_body', (s, s * 0.66, s * 0.46), (0, 0, s * 0.26), [shell], seg=(14, 9), coll=c),
                       ellipsoid(f'{name}_head', (s * 0.36, s * 0.32, s * 0.28), (s * 0.55, 0, s * 0.24), [dark], seg=(10, 7), coll=c),
                       tube(f'{name}_snout', (s * 0.66, 0, s * 0.22), (s * 0.92, 0, s * 0.08), s * 0.07, s * 0.04, 2, 6, [dark], coll=c)]
    for i, x in enumerate((-0.28, 0.0, 0.28)):
        for sd in (-1, 1):
            p0 = (s * x, sd * s * 0.26, s * 0.16); p1 = (s * (x + 0.10 * (1 if x >= 0 else -1)), sd * s * 0.60, s * 0.20); p2 = (s * (x + 0.16 * (1 if x >= 0 else -1)), sd * s * 0.74, 0.0)
            parts.append(tube(f'{name}_a{i}{sd}', p0, p1, s * 0.045, s * 0.04, 2, 5, [dark], coll=c))
            parts.append(tube(f'{name}_b{i}{sd}', p1, p2, s * 0.04, s * 0.03, 2, 5, [dark], coll=c))
    o = join(parts, name); look.outline(o, ink); return o


def spoon(name, c=None, ink=0.002, length=0.13):
    """a tin spoon; origin at the end of the handle, the bowl centre at +Z (length - 0.008)."""
    tin = look.mat(f'{name}_tin', C('#B4BCCB'), rough=0.3, metal=0.7, brush=0.03, paint=0.03)
    handle = tube(f'{name}_handle', (0, 0, 0), (0, 0, length - 0.03), 0.0045, 0.0055, 2, 8, [tin], coll=c)
    bowl = ellipsoid(f'{name}_bowl', (0.034, 0.012, 0.046), (0, -0.004, length - 0.008), [tin], seg=(14, 9), coll=c)
    o = join([handle, bowl], name); look.outline(o, ink); return o


def crumbs(name, origin, f, n=9, spread=0.18, up=0.12, dur=10, floor=None, c=None, seed=0):
    """a burst of cracker crumbs at frame f: jagged bits fly out on arcs and land on `floor` (z). Hidden before f."""
    rnd = random.Random(seed); out = []; p0 = Vector(origin); zf = p0.z if floor is None else floor
    for i in range(n):
        s = rnd.uniform(0.010, 0.024)
        o = box(f'{name}{i}', (s, s * rnd.uniform(0.6, 1.0), s * 0.55), mats=[cracker_mat()], c=c, bevel=s * 0.2)
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0.35, 1.0) * spread; h = rnd.uniform(0.4, 1.0) * up; spin = rnd.uniform(4, 9)
        o.hide_render = True; o.keyframe_insert('hide_render', frame=f - 1); o.hide_render = False; o.keyframe_insert('hide_render', frame=f)
        for k in range(dur + 1):
            t = k / dur; z = p0.z + 4 * h * t * (1 - t) + (zf - p0.z) * t
            o.location = (p0.x + math.cos(a) * r * t, p0.y + math.sin(a) * r * t, max(zf + s * 0.25, z)); o.keyframe_insert('location', frame=f + k)
            o.rotation_euler = (spin * t, spin * 0.7 * t, a); o.keyframe_insert('rotation_euler', frame=f + k)
        out.append(o)
    return out
