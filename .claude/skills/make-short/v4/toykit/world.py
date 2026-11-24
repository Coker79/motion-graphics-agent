"""toykit.world: stylized outdoor set pieces built from code (rolling ground with a cliff, painted grass blades,
faceted trees, a rustic fence, rocks, puffy clouds, a sea and a lighthouse). Everything uses look.mat with painterly
dabs and inverted-hull ink so the world matches the characters. Metres, z up; the camera usually looks toward +Y."""
import bpy, bmesh, math, random
from mathutils import Vector, noise
from . import look
from .char import mesh_obj, subsurf, ellipsoid, lathe, tube, join
from .camera import fcurves as _fcurves

C = look.hexc


def coll(name):
    c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); return c


def _ss(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- terrain
def meadow_height(x, y, flat_r=3.5, cliff_y=14.0, drop=7.0, seed=0.0):
    """gentle rolling meadow, flat around the origin (the stage), sloping down to a cliff edge at y = cliff_y so the
    sea shows as a band under the horizon from eye height."""
    r = math.hypot(x, y)
    h = 0.45 * noise.noise(Vector((x * 0.06, y * 0.06, seed))) + 0.18 * noise.noise(Vector((x * 0.19, y * 0.19, seed + 4)))
    h *= _ss(flat_r * 0.4, flat_r * 2.2, r)
    h += 0.8 * _ss(3, 22, abs(x)) * _ss(-2, 6, y)                         # land rises gently to the sides (frames the sea)
    h -= 0.7 * _ss(4, cliff_y, y) * (1 - _ss(4, 20, abs(x)))               # ...and dips toward the cliff in the middle
    h -= drop * _ss(cliff_y, cliff_y + 2.5, y + 1.0 * noise.noise(Vector((x * 0.12, 7, seed))))
    return h


def ground(name, hfn, size=(70, 56), center=(0, 12), res=(140, 112), mat=None, c=None):
    nx, ny = res; sx, sy = size; cx, cy = center; bm = bmesh.new()
    V = [[bm.verts.new((cx - sx / 2 + sx * i / nx, cy - sy / 2 + sy * j / ny, 0)) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx): bm.faces.new((V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]))
    for v in bm.verts: v.co.z = hfn(v.co.x, v.co.y)
    return mesh_obj(name, bm, [mat] if mat else [], coll=c)


def grass_mat(name='TK_grass', base='#2F6B2A', tip='#B9D65A'):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); p = N('ShaderNodeBsdfPrincipled'); p.inputs['Roughness'].default_value = 0.75
    at = N('ShaderNodeAttribute'); at.attribute_name = 'grad'
    tco = N('ShaderNodeTexCoord'); col = look.strokes(nt, tco, at.outputs['Color'], 0.06, 3.0)
    L(col, p.inputs['Base Color'])
    for k, v in (('Subsurface Weight', 0.0), ('Specular IOR Level', 0.25)):
        if k in p.inputs: p.inputs[k].default_value = v
    # a little light through the blades (backlit grass glows)
    em = N('ShaderNodeMix'); em.data_type = 'RGBA'; em.blend_type = 'MULTIPLY'; em.inputs[0].default_value = 1.0
    L(col, em.inputs[6]); em.inputs[7].default_value = (0.10, 0.12, 0.05, 1)
    L(em.outputs[2], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 1.0
    L(p.outputs[0], out.inputs[0]); return m


def grass(name, pts, hfn, h=(0.16, 0.36), w=(0.02, 0.045), base='#2F6B2A', tip='#B9D65A', bend=0.35, lean=(0.15, 0.05),
          seed=1, c=None, mat=None, segs=4):
    """one joined mesh of curved, tapered blades with a base->tip colour gradient ('grad' attribute)."""
    rnd = random.Random(seed); bm = bmesh.new(); lay = bm.loops.layers.float_color.new('grad')
    cb, ct = Vector(C(base)), Vector(C(tip))
    for (x, y) in pts:
        z = hfn(x, y); H = rnd.uniform(*h); Wd = rnd.uniform(*w); a = rnd.uniform(0, math.pi)
        wax = Vector((math.cos(a), math.sin(a), 0)); bd = Vector((-math.sin(a), math.cos(a), 0)) * rnd.choice((-1, 1))
        bd = (bd + Vector((lean[0], lean[1], 0)) * 2).normalized(); bnd = rnd.uniform(0.6, 1.3) * bend
        o = Vector((x, y, z - 0.02)); tint = rnd.uniform(0.85, 1.12); hue = Vector((rnd.uniform(-0.03, 0.03), 0, rnd.uniform(-0.04, 0.02)))
        lv = []
        for k in range(segs):
            t = k / segs; cc = o + Vector((0, 0, H * t)) + bd * H * bnd * t * t; hw = Wd * 0.5 * (1 - t) ** 0.7
            lv.append((bm.verts.new(cc - wax * hw), bm.verts.new(cc + wax * hw), t))
        tipv = bm.verts.new(o + Vector((0, 0, H)) + bd * H * bnd); faces = []
        for k in range(segs - 1):
            faces.append((bm.faces.new((lv[k][0], lv[k][1], lv[k + 1][1], lv[k + 1][0])), (lv[k][2], lv[k][2], lv[k + 1][2], lv[k + 1][2])))
        faces.append((bm.faces.new((lv[-1][0], lv[-1][1], tipv)), (lv[-1][2], lv[-1][2], 1.0)))
        for f, ts in faces:
            for loop, t in zip(f.loops, ts):
                cl = (cb + (ct - cb) * (t ** 1.3)) * tint + hue * t; loop[lay] = (max(cl.x, 0), max(cl.y, 0), max(cl.z, 0), 1.0)
    o = mesh_obj(name, bm, [mat or grass_mat()], coll=c); o.visible_shadow = True
    return o


def scatter(n, fn, seed=0):
    rnd = random.Random(seed); out = []
    while len(out) < n:
        p = fn(rnd)
        if p: out.append(p)
    return out


# ---------------------------------------------------------------- props
def tree(name, loc, height=4.2, crown=1.5, seed=0, leaf='#3F7D34', leaf_hi='#9CC54B', bark='#6B4A33', c=None, ink=0.02):
    rnd = random.Random(seed); x, y, z = loc
    barkm = look.mat(f'{name}_bark', C(bark), rough=0.85, brush=0.1, grain=0.6, paint=0.08)
    trunk = tube(f'{name}_trunk', (x, y, z - 0.2), (x + rnd.uniform(-0.15, 0.15), y, z + height * 0.62), crown * 0.13, crown * 0.07, 6, 10, [barkm], coll=c)
    look.outline(trunk, ink * 0.6)
    lm = bpy.data.materials.get(f'{name}_leaf') or _leaf_mat(f'{name}_leaf', leaf, leaf_hi)
    blobs = []
    for i in range(rnd.randint(3, 5)):
        r = crown * rnd.uniform(0.55, 0.9)
        p = Vector((x + rnd.uniform(-0.7, 0.7) * crown, y + rnd.uniform(-0.5, 0.5) * crown, z + height * rnd.uniform(0.62, 0.95)))
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        for v in bm.verts:
            v.co *= 1 + 0.16 * noise.noise(v.co * 1.7 + Vector((seed, i, 0))); v.co.z *= 0.82
        o = mesh_obj(f'{name}_crown{i}', bm, [lm], smooth=False, coll=c); o.location = p; blobs.append(o)
    cr = join(blobs, f'{name}_crown'); look.outline(cr, ink)
    return trunk, cr


def _leaf_mat(name, lo, hi):
    m = look.mat(name, C(lo), rough=0.9, brush=0.08, grain=0.0, paint=0.10, paint_scale=2.5, spec=0.15)
    nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    src = p.inputs['Base Color'].links[0].from_socket
    tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Generated'], sp.inputs[0])
    rp = N('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (0.55, 0.6, 0.75, 1); rp.color_ramp.elements[0].position = 0.15
    rp.color_ramp.elements[1].color = (*[h / l if l > 0 else 1 for h, l in zip(C(hi), C(lo))], 1); rp.color_ramp.elements[1].position = 0.95
    L(sp.outputs['Z'], rp.inputs[0])
    mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    L(src, mx.inputs[6]); L(rp.outputs[0], mx.inputs[7]); L(mx.outputs[2], p.inputs['Base Color'])
    return m


def fence(name, p0, p1, n, hfn, wood='#8A6440', c=None, post_h=0.9, ink=0.008, seed=3):
    rnd = random.Random(seed); wm = look.mat(f'{name}_wood', C(wood), rough=0.85, brush=0.12, grain=0.5, paint=0.10)
    p0, p1 = Vector(p0), Vector(p1); parts = []; tops = []
    for i in range(n):
        q = p0 + (p1 - p0) * (i / (n - 1)); z = hfn(q.x, q.y); lean = Vector((rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), 0))
        parts.append(tube(f'{name}_post{i}', (q.x, q.y, z - 0.15), (q.x + lean.x, q.y + lean.y, z + post_h * rnd.uniform(0.92, 1.05)), 0.055, 0.05, 3, 7, [wm], coll=c))
        tops.append(Vector((q.x + lean.x * 0.7, q.y + lean.y * 0.7, z)))
    for k, hh in enumerate((0.42, 0.75)):
        for i in range(n - 1):
            a, b = tops[i] + Vector((0, 0, post_h * hh)), tops[i + 1] + Vector((0, 0, post_h * hh + rnd.uniform(-0.05, 0.05)))
            parts.append(tube(f'{name}_rail{k}{i}', a, b, 0.032, 0.03, 3, 7, [wm], coll=c))
    o = join(parts, name); look.outline(o, ink); return o


def rock(name, loc, size, seed=0, color='#8E8FA3', c=None, ink=0.01):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        v.co *= 1 + 0.22 * noise.noise(v.co * 1.4 + Vector((seed, 0, 0))); v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    o = mesh_obj(name, bm, [look.mat(f'{name}_m', C(color), rough=0.9, brush=0.1, grain=0.4, paint=0.08)], smooth=False, coll=c)
    o.location = loc; look.outline(o, ink); return o


def cloud_mat(name='TK_cloud', top='#FFFAFF', bottom='#B9A9E3'):
    m = bpy.data.materials.get(name)
    if m: return m
    m = look.mat(name, C(top), rough=1.0, brush=0.03, grain=0.0, paint=0.05, paint_scale=0.5, spec=0.0, emission=((1.0, 0.98, 1.0), 0.45))
    nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'); src = p.inputs['Base Color'].links[0].from_socket
    tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Generated'], sp.inputs[0])
    rp = N('ShaderNodeValToRGB'); e = rp.color_ramp.elements
    e[0].position = 0.08; e[0].color = (*[b / t for b, t in zip(C(bottom), C(top))], 1); e[1].position = 0.6; e[1].color = (1, 1, 1, 1)
    L(sp.outputs['Z'], rp.inputs[0])
    mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    L(src, mx.inputs[6]); L(rp.outputs[0], mx.inputs[7]); L(mx.outputs[2], p.inputs['Base Color'])
    return m


def cloud(name, loc, size=6.0, seed=0, c=None):
    rnd = random.Random(seed); m = cloud_mat()
    blobs = []
    for i in range(rnd.randint(6, 9)):
        r = size * rnd.uniform(0.22, 0.42); dx = rnd.uniform(-1, 1) * size * 0.75
        blobs.append(ellipsoid(f'{name}_b{i}', (r * 2, r * 1.6, r * 1.7), (loc[0] + dx, loc[1] + rnd.uniform(-0.3, 0.3) * size,
                                                                         loc[2] + rnd.uniform(0.0, 0.35) * size * (1 - abs(dx) / size)), [m], seg=(24, 14), coll=c))
    o = join(blobs, name)
    bm = bmesh.new(); bm.from_mesh(o.data); zc = loc[2] - size * 0.12
    for v in bm.verts:
        if v.co.z < zc: v.co.z = zc + (v.co.z - zc) * 0.15                  # flat-bottomed, like painted cumulus
    bm.to_mesh(o.data); bm.free()
    look.outline(o, size * 0.010, color=C('#8F86C0')); o.visible_shadow = False
    return o


def lighthouse(name, loc, height=7.0, c=None, ink=0.03):
    x, y, z = loc; parts = []
    white = look.mat(f'{name}_white', C('#F4EFE6'), rough=0.8, brush=0.06, paint=0.06)
    red = look.mat(f'{name}_red', C('#D23B32'), rough=0.75, brush=0.06, paint=0.06)
    dark = look.mat(f'{name}_dark', C('#2C2A36'), rough=0.6)
    glass = look.mat(f'{name}_glass', C('#FFE9A8'), rough=0.3, emission=((1.0, 0.85, 0.45), 2.5))
    r0, r1 = height * 0.11, height * 0.07; nb = 5
    for i in range(nb):
        t0, t1 = i / nb, (i + 1) / nb
        seg = lathe(f'{name}_s{i}', [(0, z + height * t0), (r0 + (r1 - r0) * t0, z + height * t0), (r0 + (r1 - r0) * t1, z + height * t1), (0, z + height * t1)],
                    28, loc=(x, y, 0), mats=[white if i % 2 == 0 else red], coll=c)
        parts.append(seg)
    gz = z + height
    parts.append(lathe(f'{name}_gal', [(0, gz), (r1 * 1.5, gz), (r1 * 1.5, gz + 0.12), (0, gz + 0.12)], 28, loc=(x, y, 0), mats=[dark], coll=c))
    parts.append(lathe(f'{name}_lamp', [(0, gz + 0.12), (r1 * 0.85, gz + 0.12), (r1 * 0.85, gz + height * 0.12), (0, gz + height * 0.12)], 20, loc=(x, y, 0), mats=[glass], coll=c))
    parts.append(lathe(f'{name}_cap', [(0, gz + height * 0.12), (r1 * 1.15, gz + height * 0.12), (r1 * 0.2, gz + height * 0.2), (0, gz + height * 0.21)], 24, loc=(x, y, 0), mats=[red], coll=c))
    o = join(parts, name); look.outline(o, ink); return o


def sea(name, z=-6.5, c=None, color='#2C7FA8', far='#8FD0E0'):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=1.0)
    for v in bm.verts: v.co.x *= 600; v.co.y = v.co.y * 300 + 290; v.co.z = z
    m = bpy.data.materials.new(name + '_m'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); p = N('ShaderNodeBsdfPrincipled'); p.inputs['Roughness'].default_value = 0.22
    tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], sp.inputs[0])
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 20; mr.inputs['From Max'].default_value = 260; L(sp.outputs['Y'], mr.inputs['Value'])
    rp = N('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (*C(color), 1); rp.color_ramp.elements[1].color = (*C(far), 1)
    L(mr.outputs[0], rp.inputs[0]); col = look.strokes(nt, tc, rp.outputs[0], 0.06, 0.08, stretch=8.0)
    L(col, p.inputs['Base Color'])
    wn = N('ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = 1.2; wn.inputs['Detail'].default_value = 4
    mp = N('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 4, 1); L(tc.outputs['Object'], mp.inputs[0]); L(mp.outputs[0], wn.inputs['Vector'])
    bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; L(wn.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], p.inputs['Normal'])
    L(p.outputs[0], out.inputs[0])
    return mesh_obj(name, bm, [m], coll=c)


# ---------------------------------------------------------------- camp pieces
def tent(name, loc, size=(1.6, 2.0, 1.3), rot=0.0, color='#E2D2A8', camo=False, c=None, ink=0.012, seed=0):
    """A-frame canvas tent with a dark open flap, ridge pole and guy pegs; origin on the ground at its centre."""
    w, d, h = size; bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (0, -d / 2 - 0.05, h), (-w / 2, d / 2, 0), (w / 2, d / 2, 0), (0, d / 2 + 0.05, h))]
    bm.faces.new((v[0], v[3], v[5], v[2])); bm.faces.new((v[1], v[2], v[5], v[4])); bm.faces.new((v[0], v[2], v[1])); bm.faces.new((v[3], v[4], v[5]))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    rnd = random.Random(seed)
    for vv in bm.verts:     # canvas sag between the poles
        if 0.05 < vv.co.z < h - 0.05 and abs(vv.co.y) < d / 2 - 0.05: vv.co.x *= 0.96 - 0.02 * rnd.random()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = look.mat(f'{name}_canvas', C(color), rough=0.9, brush=0.12, grain=0.5, paint=0.14 if not camo else 0.0, paint_scale=3)
    if camo:
        nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
        p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'); src = p.inputs['Base Color'].links[0].from_socket
        tc = N('ShaderNodeTexCoord'); nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 2
        L(tc.outputs['Object'], nz.inputs['Vector']); rp = N('ShaderNodeValToRGB'); rp.color_ramp.interpolation = 'CONSTANT'
        e = rp.color_ramp.elements; e[0].color = (*C('#7E7A45'), 1); e[1].position = 0.52; e[1].color = (*C(color), 1)
        e2 = e.new(0.62); e2.color = (*C('#5E6136'), 1); L(nz.outputs['Fac'], rp.inputs[0])
        mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        L(src, mx.inputs[6]); L(rp.outputs[0], mx.inputs[7]); L(mx.outputs[2], p.inputs['Base Color'])
    o = mesh_obj(name, bm, [m], smooth=False, coll=c)
    flap = mesh_obj(f'{name}_door', (lambda b: (b, [b.faces.new([b.verts.new(p) for p in ((-w * 0.18, -d / 2 - 0.02, 0.0), (w * 0.18, -d / 2 - 0.02, 0.0), (0, -d / 2 - 0.045, h * 0.62))])])[0])(bmesh.new()),
                    [look.flat('TK_tentdark', C('#2B2420'))], smooth=False, coll=c)
    pole = tube(f'{name}_pole', (0, -d / 2 - 0.08, 0), (0, -d / 2 - 0.08, h + 0.12), 0.025, 0.022, 3, 8, [look.mat('TK_pole', C('#7A5636'), rough=0.8, paint=0.08)], coll=c)
    t = join([o, flap, pole], name); t.location = loc; t.rotation_euler = (0, 0, rot); look.outline(t, ink); return t


def campfire(name, loc, c=None, ink=0.006, light=True):
    x, y, z = loc; parts = []
    wood = look.mat('TK_firewood', C('#5C3A22'), rough=0.85, brush=0.12, paint=0.1)
    for i in range(5):
        a = i * 2 * math.pi / 5
        parts.append(tube(f'{name}_log{i}', (x + math.cos(a) * 0.32, y + math.sin(a) * 0.32, z + 0.03), (x + math.cos(a) * 0.04, y + math.sin(a) * 0.04, z + 0.2), 0.045, 0.04, 3, 8, [wood], coll=c))
    stones = look.mat('TK_stone', C('#8B8A96'), rough=0.9, paint=0.1)
    for i in range(9):
        a = i * 2 * math.pi / 9; parts.append(ellipsoid(f'{name}_st{i}', (0.13, 0.11, 0.08), (x + math.cos(a) * 0.42, y + math.sin(a) * 0.42, z + 0.03), [stones], seg=(10, 6), coll=c))
    fire = join(parts, name); look.outline(fire, ink)
    fm = look.mat('TK_flame', C('#FF8A1E'), rough=1.0, brush=0.0, grain=0.0, emission=((1.0, 0.42, 0.06), 0.7))
    flames = []
    for i, (dx, dy, hh) in enumerate(((0, 0, 0.42), (0.07, 0.03, 0.30), (-0.06, -0.02, 0.33))):
        f = lathe(f'{name}_flame{i}', [(0, 0), (0.07, 0.05), (0.05, hh * 0.6), (0.0, hh)], 12, loc=(x + dx, y + dy, z + 0.08), mats=[fm], coll=c)
        f.visible_shadow = False; flames.append(f)
    if light:
        lt = bpy.data.lights.new(f'{name}_light', 'POINT'); lt.energy = 120; lt.color = (1.0, 0.6, 0.25); lt.shadow_soft_size = 0.2
        lo = bpy.data.objects.new(f'{name}_light', lt); (c or bpy.context.scene.collection).objects.link(lo); lo.location = (x, y, z + 0.5)
    return fire, flames


def barrel(name, loc, h=0.75, r=0.28, c=None, ink=0.008):
    wood = look.mat('TK_barrelwood', C('#8E5E35'), rough=0.8, brush=0.12, grain=0.5, paint=0.12)
    iron = look.mat('TK_hoop', C('#3C3A44'), rough=0.5, metal=0.4)
    body = lathe(f'{name}_b', [(0, 0), (r * 0.86, 0), (r, h * 0.5), (r * 0.86, h), (0, h)], 28, loc=loc, mats=[wood], coll=c)
    hoops = [lathe(f'{name}_h{i}', [(r * k * 1.005, zz - 0.02), (r * k * 1.03, zz - 0.02), (r * k * 1.03, zz + 0.02), (r * k * 1.005, zz + 0.02)], 28, loc=loc, mats=[iron], closed=True, coll=c)
             for i, (zz, k) in enumerate(((h * 0.12, 0.92), (h * 0.36, 0.985), (h * 0.64, 0.985), (h * 0.88, 0.92)))]
    o = join([body] + hoops, name); subsurf(o, 1, 1); look.outline(o, ink); return o


def pine(name, loc, height=5.0, r=1.3, c=None, ink=0.015, seed=0):
    rnd = random.Random(seed); x, y, z = loc
    lm = look.mat(f'TK_pine{seed % 3}', C(('#4E7A3A', '#5A8440', '#466E36')[seed % 3]), rough=0.9, brush=0.1, paint=0.12, paint_scale=2.0, spec=0.15)
    trunk = tube(f'{name}_t', (x, y, z - 0.1), (x, y, z + height * 0.3), r * 0.12, r * 0.09, 3, 8, [look.mat('TK_pinebark', C('#6B4A33'), rough=0.9, paint=0.1)], coll=c)
    tiers = []
    for i in range(4):
        zz = z + height * (0.18 + 0.2 * i); rr = r * (1.0 - 0.2 * i); hh = height * 0.38
        cone = lathe(f'{name}_c{i}', [(0, zz), (rr, zz + 0.06), (rr * 0.9, zz + 0.12), (0.0, zz + hh)], 9, loc=(x, y, 0), mats=[lm], coll=c)
        bm = bmesh.new(); bm.from_mesh(cone.data)
        for v in bm.verts: v.co.z += 0.06 * math.sin(v.co.x * 9 + seed) * (1 if v.co.z < zz + 0.2 else 0)
        bm.to_mesh(cone.data); bm.free(); tiers.append(cone)
    o = join([trunk] + tiers, name); look.outline(o, ink); return o


# ---------------------------------------------------------------- shallow water (lesson 54)
def shallow_water_mat(name='TK_flood', tint='#CDEBE6', deep='#3E93C2', clarity=0.80, ripple=0.10):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); tc = N('ShaderNodeTexCoord')
    rgb = N('ShaderNodeRGB'); rgb.outputs[0].default_value = (*C(deep), 1)
    col = look.strokes(nt, tc, rgb.outputs[0], 0.10, 0.45, stretch=7.0)
    gl = N('ShaderNodeBsdfPrincipled'); L(col, gl.inputs['Base Color']); gl.inputs['Roughness'].default_value = 0.07
    gl.inputs['IOR'].default_value = 1.33; gl.inputs['Specular IOR Level'].default_value = 0.9
    wn = N('ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = 2.2; wn.inputs['Detail'].default_value = 3
    mp = N('ShaderNodeMapping'); mp.name = 'RIPPLE'; mp.inputs['Scale'].default_value = (1, 3, 1); L(tc.outputs['Object'], mp.inputs[0]); L(mp.outputs[0], wn.inputs['Vector'])
    bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = ripple; L(wn.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], gl.inputs['Normal'])
    tr = N('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (*C(tint), 1)
    lw = N('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35; L(bp.outputs['Normal'], lw.inputs['Normal'])
    mr = N('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - clarity; mr.inputs['To Max'].default_value = 1.0; L(lw.outputs['Facing'], mr.inputs['Value'])
    mx = N('ShaderNodeMixShader'); L(mr.outputs[0], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(gl.outputs[0], mx.inputs[2])
    L(mx.outputs[0], out.inputs[0])
    for k, v in (('surface_render_method', 'BLENDED'), ('use_transparency_overlap', False)):
        try: setattr(m, k, v)
        except Exception as e: print('polder.flood_mat', k, e)
    return m


def water(name, size, center, z, c=None, mat=None):
    """a flat water sheet at height z (key its location.z to flood or drain); shallow_water_mat() by default."""
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=0.5)
    for v in bm.verts: v.co.x *= size[0]; v.co.y *= size[1]
    o = mesh_obj(name, bm, [mat or shallow_water_mat()], smooth=False, coll=c); o.location = (center[0], center[1], z)
    o.visible_shadow = False; return o


def gush_mat(name):
    """rushing water: pale blue with white streaks along the flow (local -Y); key the mapping's location.y to make it run."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); p = N('ShaderNodeBsdfPrincipled'); tc = N('ShaderNodeTexCoord')
    mp = N('ShaderNodeMapping'); mp.name = 'FLOW'; mp.inputs['Scale'].default_value = (3.0, 0.5, 3.0); L(tc.outputs['Object'], mp.inputs[0])
    nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4; L(mp.outputs[0], nz.inputs['Vector'])
    rp = N('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.42; rp.color_ramp.elements[0].color = (*C('#7FC4E6'), 1)
    rp.color_ramp.elements[1].position = 0.62; rp.color_ramp.elements[1].color = (*C('#F6FCFF'), 1); L(nz.outputs['Fac'], rp.inputs[0])
    L(rp.outputs[0], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.15
    L(rp.outputs[0], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 0.25
    p.inputs['Alpha'].default_value = 0.88; L(p.outputs[0], out.inputs[0])
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m


# ---------------------------------------------------------------- moving water (lesson 59): spread, pour, churn, boil, spray
# A level plane that rises reads as "rudimentary" in motion (Dutch-flood test). Water must MOVE: a front that spreads
# from where it lands, a churning tongue, white water boiling at the landing, droplets thrown out.

def spread_mat(name, origin, tint='#CDEBE6', deep='#3E93C2', clarity=0.80, ripple=0.10, foam_w=0.55):
    """water that SPREADS: shallow water inside a radius round `origin` (object-space x, y on the water sheet), a noisy
    foamy leading edge, fully transparent beyond. Key the 'REVEAL' node (metres) to sweep the front out:
      rv = m.node_tree.nodes['REVEAL'].outputs[0]; rv.default_value = 6.0; rv.keyframe_insert('default_value', frame=f)
    Shrinking it DRAINS the water back to the centre; key 'ORIGIN_X'/'ORIGIN_Y' (CONSTANT, inside a whip) to drain toward
    something else (a pumping mill). Only touch the REVEAL F-curve when setting interpolation (filter on its data_path).
    flow_water() scrolls the 'RIPPLE' mapping so the surface never sits glassy and still."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); tc = N('ShaderNodeTexCoord')
    rgb = N('ShaderNodeRGB'); rgb.outputs[0].default_value = (*C(deep), 1)
    col = look.strokes(nt, tc, rgb.outputs[0], 0.10, 0.45, stretch=7.0)
    gl = N('ShaderNodeBsdfPrincipled'); L(col, gl.inputs['Base Color']); gl.inputs['Roughness'].default_value = 0.07
    gl.inputs['IOR'].default_value = 1.33; gl.inputs['Specular IOR Level'].default_value = 0.9
    wn = N('ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = 2.2; wn.inputs['Detail'].default_value = 3
    mp = N('ShaderNodeMapping'); mp.name = 'RIPPLE'; mp.inputs['Scale'].default_value = (1, 3, 1); L(tc.outputs['Object'], mp.inputs[0]); L(mp.outputs[0], wn.inputs['Vector'])
    bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = ripple; L(wn.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], gl.inputs['Normal'])
    tr = N('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (*C(tint), 1)
    lw = N('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35; L(bp.outputs['Normal'], lw.inputs['Normal'])
    mr = N('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - clarity; mr.inputs['To Max'].default_value = 1.0; L(lw.outputs['Facing'], mr.inputs['Value'])
    water_ = N('ShaderNodeMixShader'); L(mr.outputs[0], water_.inputs[0]); L(tr.outputs[0], water_.inputs[1]); L(gl.outputs[0], water_.inputs[2])
    sep = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], sep.inputs[0])
    ox = N('ShaderNodeValue'); ox.name = 'ORIGIN_X'; ox.outputs[0].default_value = origin[0]     # keyable: a drain recentres on the mill
    oy = N('ShaderNodeValue'); oy.name = 'ORIGIN_Y'; oy.outputs[0].default_value = origin[1]
    cx = N('ShaderNodeMath'); cx.operation = 'SUBTRACT'; L(sep.outputs['X'], cx.inputs[0]); L(ox.outputs[0], cx.inputs[1])
    cy = N('ShaderNodeMath'); cy.operation = 'SUBTRACT'; L(sep.outputs['Y'], cy.inputs[0]); L(oy.outputs[0], cy.inputs[1])
    dv = N('ShaderNodeCombineXYZ'); L(cx.outputs[0], dv.inputs['X']); L(cy.outputs[0], dv.inputs['Y'])
    dl = N('ShaderNodeVectorMath'); dl.operation = 'LENGTH'; L(dv.outputs[0], dl.inputs[0])
    en = N('ShaderNodeTexNoise'); en.inputs['Scale'].default_value = 0.35; en.inputs['Detail'].default_value = 2; L(tc.outputs['Object'], en.inputs['Vector'])
    em = N('ShaderNodeMath'); em.operation = 'MULTIPLY_ADD'; L(en.outputs['Fac'], em.inputs[0]); em.inputs[1].default_value = 3.0; em.inputs[2].default_value = -1.5
    d2 = N('ShaderNodeMath'); d2.operation = 'ADD'; L(dl.outputs['Value'], d2.inputs[0]); L(em.outputs[0], d2.inputs[1])
    rv = N('ShaderNodeValue'); rv.name = 'REVEAL'; rv.outputs[0].default_value = 0.0
    df = N('ShaderNodeMath'); df.operation = 'SUBTRACT'; L(rv.outputs[0], df.inputs[0]); L(d2.outputs[0], df.inputs[1])
    inside = N('ShaderNodeMapRange'); inside.inputs['From Min'].default_value = 0.0; inside.inputs['From Max'].default_value = 0.08; L(df.outputs[0], inside.inputs['Value'])
    band = N('ShaderNodeMapRange'); band.inputs['From Min'].default_value = foam_w; band.inputs['From Max'].default_value = 0.0; L(df.outputs[0], band.inputs['Value'])
    fband = N('ShaderNodeMath'); fband.operation = 'MULTIPLY'; L(band.outputs[0], fband.inputs[0]); L(inside.outputs[0], fband.inputs[1])
    fn = N('ShaderNodeTexNoise'); fn.inputs['Scale'].default_value = 9.0; L(tc.outputs['Object'], fn.inputs['Vector'])
    fm = N('ShaderNodeMath'); fm.operation = 'MULTIPLY'; L(fband.outputs[0], fm.inputs[0]); L(fn.outputs['Fac'], fm.inputs[1])
    fmx = N('ShaderNodeMath'); fmx.operation = 'MULTIPLY'; fmx.use_clamp = True; L(fm.outputs[0], fmx.inputs[0]); fmx.inputs[1].default_value = 2.4
    foam = N('ShaderNodeBsdfPrincipled'); foam.inputs['Base Color'].default_value = (*C('#F4FBFF'), 1); foam.inputs['Roughness'].default_value = 0.6
    foam.inputs['Emission Color'].default_value = (*C('#E8F6FF'), 1); foam.inputs['Emission Strength'].default_value = 0.35
    wf = N('ShaderNodeMixShader'); L(fmx.outputs[0], wf.inputs[0]); L(water_.outputs[0], wf.inputs[1]); L(foam.outputs[0], wf.inputs[2])
    clear = N('ShaderNodeBsdfTransparent')
    fin = N('ShaderNodeMixShader'); L(inside.outputs[0], fin.inputs[0]); L(clear.outputs[0], fin.inputs[1]); L(wf.outputs[0], fin.inputs[2])
    L(fin.outputs[0], out.inputs[0])
    for k, v in (('surface_render_method', 'BLENDED'), ('use_transparency_overlap', False)):
        try: setattr(m, k, v)
        except Exception as e: print('world.spread_mat', k, e)
    return m


def pour_band(pour, f, node, v, ip='CONSTANT'):
    """key the pour's hidden band: node 'VCUT' (start, 2 = off) or 'VEND' (end) along its length (UV v)."""
    nt = pour.active_material.node_tree; o = nt.nodes[node].outputs[0]; o.default_value = v; o.keyframe_insert('default_value', frame=f)
    for fc in _fcurves(nt):
        if '"' + node + '"' in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - f) < 1e-3: kp.interpolation = ip


def sink_under_front(pour, water, f0, f1, vcut=0.25, margin=0.08, f_off=None):
    """hide the pour's tongue where a spread_mat front has flooded over it (it draws UNDER the thin flood plane and shows
    through grass as a white strip on every blade, lesson 70). From f0 to f1, keys VCUT (the pour above v=vcut stays) and
    VEND just past the front's far edge, read per frame from the water's REVEAL/ORIGIN keys and the pour's scale; the
    tongue AHEAD of the front stays. Call it after keying reveal(), recenter() and the pour's growth. f_off: VCUT back off."""
    sc = bpy.context.scene; nn = water.active_material.node_tree.nodes; L_ = pour.get('pour_length', 4.2); keep = sc.frame_current
    pour_band(pour, f0, 'VCUT', vcut)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ax = (pour.matrix_world.to_3x3() @ Vector((0, -1, 0))); ax.z = 0; ax.normalize()
        o = Vector((water.location.x + nn['ORIGIN_X'].outputs[0].default_value, water.location.y + nn['ORIGIN_Y'].outputs[0].default_value, 0))
        p0 = pour.matrix_world.translation; a = (o - Vector((p0.x, p0.y, 0))).dot(ax)
        pour_band(pour, f, 'VEND', round((a + nn['REVEAL'].outputs[0].default_value) / (L_ * max(pour.scale.y, 0.05)) + margin, 3), 'LINEAR')
    if f_off is not None: pour_band(pour, f_off, 'VCUT', 2.0)
    sc.frame_set(keep)


def pour_mat(name):
    """rushing water for pour(): streaks along the flow (key node 'FLOW' Location.y to run them), ragged see-through
    edges (UV u) and foam building toward the landing (UV v). It needs the UVs pour() makes."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); p = N('ShaderNodeBsdfPrincipled'); tc = N('ShaderNodeTexCoord')
    mp = N('ShaderNodeMapping'); mp.name = 'FLOW'; mp.inputs['Scale'].default_value = (4.5, 0.6, 4.5); L(tc.outputs['Object'], mp.inputs[0])
    nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4; L(mp.outputs[0], nz.inputs['Vector'])
    rp = N('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.36; rp.color_ramp.elements[0].color = (*C('#5FB2DE'), 1)
    rp.color_ramp.elements[1].position = 0.56; rp.color_ramp.elements[1].color = (*C('#F6FCFF'), 1); L(nz.outputs['Fac'], rp.inputs[0])
    uv = N('ShaderNodeSeparateXYZ'); L(tc.outputs['UV'], uv.inputs[0])
    fo = N('ShaderNodeMapRange'); fo.inputs['From Min'].default_value = 0.55; fo.inputs['From Max'].default_value = 1.0; L(uv.outputs['Y'], fo.inputs['Value'])
    fz = N('ShaderNodeMath'); fz.operation = 'MULTIPLY'; fz.use_clamp = True; L(fo.outputs[0], fz.inputs[0]); L(nz.outputs['Fac'], fz.inputs[1])
    fz2 = N('ShaderNodeMath'); fz2.operation = 'MULTIPLY'; fz2.use_clamp = True; L(fz.outputs[0], fz2.inputs[0]); fz2.inputs[1].default_value = 2.2
    wt = N('ShaderNodeMix'); wt.data_type = 'RGBA'; L(fz2.outputs[0], wt.inputs['Factor']); L(rp.outputs[0], wt.inputs['A']); wt.inputs['B'].default_value = (1, 1, 1, 1)
    L(wt.outputs['Result'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.15
    L(wt.outputs['Result'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 0.25
    a2 = N('ShaderNodeMath'); a2.operation = 'MULTIPLY_ADD'; L(uv.outputs['X'], a2.inputs[0]); a2.inputs[1].default_value = 2.0; a2.inputs[2].default_value = -1.0
    ab = N('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; L(a2.outputs[0], ab.inputs[0])
    en = N('ShaderNodeTexNoise'); en.name = 'TEAR'; en.noise_dimensions = '4D'; en.inputs['Scale'].default_value = 6.0; en.inputs['Detail'].default_value = 4
    L(mp.outputs[0], en.inputs['Vector'])                         # churn() keys TEAR's W: the torn edges boil as well as run
    ad = N('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; L(en.outputs['Fac'], ad.inputs[0]); ad.inputs[1].default_value = 0.70; L(ab.outputs[0], ad.inputs[2])
    edge = N('ShaderNodeMapRange'); edge.inputs['From Min'].default_value = 1.20; edge.inputs['From Max'].default_value = 0.85; L(ad.outputs[0], edge.inputs['Value'])
    al = N('ShaderNodeMath'); al.operation = 'MULTIPLY'; L(edge.outputs[0], al.inputs[0]); al.inputs[1].default_value = 0.92
    # VCUT..VEND (key both; VCUT 2 = off): the tongue is HIDDEN between these points along its length (UV v). A pour lying
    # over a thin BLENDED flood plane draws UNDER it, so it shows only where grass blocks the flood: a white strip on every
    # blade (Dutch-flood final). A height cut fails (the churn lifts the tail); sink_under_front() keys this band (lesson 70).
    uvs = N('ShaderNodeSeparateXYZ'); L(tc.outputs['UV'], uvs.inputs[0])
    vc = N('ShaderNodeValue'); vc.name = 'VCUT'; vc.outputs[0].default_value = 2.0
    ve = N('ShaderNodeValue'); ve.name = 'VEND'; ve.outputs[0].default_value = 10.0
    vc2 = N('ShaderNodeMath'); vc2.operation = 'ADD'; L(vc.outputs[0], vc2.inputs[0]); vc2.inputs[1].default_value = 0.12
    ve2 = N('ShaderNodeMath'); ve2.operation = 'SUBTRACT'; L(ve.outputs[0], ve2.inputs[0]); ve2.inputs[1].default_value = 0.12
    h1 = N('ShaderNodeMapRange'); L(uvs.outputs['Y'], h1.inputs['Value']); L(vc.outputs[0], h1.inputs['From Min']); L(vc2.outputs[0], h1.inputs['From Max'])
    h2 = N('ShaderNodeMapRange'); L(uvs.outputs['Y'], h2.inputs['Value']); L(ve2.outputs[0], h2.inputs['From Min']); L(ve.outputs[0], h2.inputs['From Max'])
    h2.inputs['To Min'].default_value = 1.0; h2.inputs['To Max'].default_value = 0.0
    hd = N('ShaderNodeMath'); hd.operation = 'MULTIPLY'; L(h1.outputs[0], hd.inputs[0]); L(h2.outputs[0], hd.inputs[1])
    kp = N('ShaderNodeMath'); kp.operation = 'SUBTRACT'; kp.inputs[0].default_value = 1.0; L(hd.outputs[0], kp.inputs[1])
    al2 = N('ShaderNodeMath'); al2.operation = 'MULTIPLY'; L(al.outputs[0], al2.inputs[0]); L(kp.outputs[0], al2.inputs[1])
    L(al2.outputs[0], p.inputs['Alpha']); L(p.outputs[0], out.inputs[0])
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m


def pour(name, loc, length=4.2, hw=(0.42, 1.32), h0=0.42, thick=0.08, c=None):
    """a fat tongue of water out of an arch, pipe or breach at `loc`, running along local -Y and down to the ground
    (z 0.04 at the tip). 28 x 10 quads with UVs (pour_mat needs them) and NO ink outline (on water it reads as a paper
    cut-out). Key scale.y 0.001 -> 1 to open it and hide_render to close it; then churn() and boil() it."""
    bm = bmesh.new(); nseg, ncol = 28, 10; rows = []; uvl = bm.loops.layers.uv.new('UVMap')
    for i in range(nseg + 1):
        t = i / nseg; yy = -t * length; zn = (0.16 + 0.22 * (1 - t) ** 2 - 0.16 * t) / 0.38; zz = 0.04 + (h0 - 0.04) * zn
        w_ = hw[0] + (hw[1] - hw[0]) * t ** 1.4
        rows.append([bm.verts.new((u * w_, yy, zz + 0.16 * (1 - u * u) * (1 - 0.6 * t))) for u in [-1 + 2 * j / ncol for j in range(ncol + 1)]])
    for i in range(nseg):
        for j in range(ncol):
            f_ = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            for lp, (jj, ii) in zip(f_.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))): lp[uvl].uv = (jj / ncol, ii / nseg)
    o = mesh_obj(name, bm, [pour_mat(f'{name}_m')], smooth=True, coll=c)
    so = o.modifiers.new('thick', 'SOLIDIFY'); so.thickness = thick
    o.location = loc; o['pour_length'] = length; return o


def churn(obj, f0, f1, c=None, strength=0.20, size=0.22, speed=0.09, wobble=0.30):
    """make a pour() churn: subsurf, a cloud displace whose empty slides downstream (`speed` m/frame along -Y), a SIDEWAYS
    wobble (from above only the outline reads: normal displacement never changes it), then the thickness. Also runs the
    streaks (node 'FLOW') and boils the torn edges (node 'TEAR')."""
    e = bpy.data.objects.new(f'{obj.name}_churn', None); (c or bpy.context.scene.collection).objects.link(e)
    tx = bpy.data.textures.new(f'{obj.name}_tex', 'CLOUDS'); tx.noise_scale = size; tx.noise_depth = 3
    th = obj.modifiers.get('thick'); t_ = th.thickness if th else 0.08
    if th: obj.modifiers.remove(th)
    sb = obj.modifiers.new('sub', 'SUBSURF'); sb.levels = 1; sb.render_levels = 2
    md = obj.modifiers.new('churn', 'DISPLACE'); md.texture = tx; md.texture_coords = 'OBJECT'; md.texture_coords_object = e; md.strength = strength; md.mid_level = 0.5
    tw = bpy.data.textures.new(f'{obj.name}_wob', 'CLOUDS'); tw.noise_scale = 0.55; tw.noise_depth = 2
    mw = obj.modifiers.new('wobble', 'DISPLACE'); mw.texture = tw; mw.texture_coords = 'OBJECT'; mw.texture_coords_object = e; mw.direction = 'X'; mw.strength = wobble; mw.mid_level = 0.5
    so = obj.modifiers.new('thick', 'SOLIDIFY'); so.thickness = t_
    for f, y in ((f0, 0.0), (f1, -speed * (f1 - f0))):
        e.location = (0, y, 0); e.keyframe_insert('location', frame=f)
    flow = obj.active_material.node_tree.nodes.get('FLOW') if obj.active_material else None
    tear = obj.active_material.node_tree.nodes.get('TEAR') if obj.active_material else None
    if tear:
        for f, w in ((f0, 0.0), (f1, 0.09 * (f1 - f0))):
            tear.inputs['W'].default_value = w; tear.inputs['W'].keyframe_insert('default_value', frame=f)
    if flow:
        for f, y in ((f0, 0.0), (f1, 1.2 * speed * (f1 - f0))):
            flow.inputs['Location'].default_value[1] = y; flow.inputs['Location'].keyframe_insert('default_value', frame=f, index=1)
        for fc in _fcurves(obj.active_material.node_tree):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    for fc in _fcurves(e):                                     # action.fcurves is gone in Blender 5: use camera.fcurves
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    return e


def boil(obj, r=2.4, c=None, f0=0, f1=2000):
    """white water boiling where a pour() lands: a low foam dome at its tip, its 4D noise keyed to boil. Parented to the
    pour, so a half-open trickle lands short and the boil grows out with the tongue; the pour's hide_render drives it."""
    m = bpy.data.materials.new(f'{obj.name}_boilm'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); tc = N('ShaderNodeTexCoord')
    nz = N('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 4
    L(tc.outputs['Object'], nz.inputs['Vector'])
    for f, w in ((f0, 0.0), (f1, 0.07 * (f1 - f0))):
        nz.inputs['W'].default_value = w; nz.inputs['W'].keyframe_insert('default_value', frame=f)
    sep = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], sep.inputs[0])
    cmb = N('ShaderNodeCombineXYZ'); L(sep.outputs['X'], cmb.inputs['X']); L(sep.outputs['Y'], cmb.inputs['Y'])
    dl = N('ShaderNodeVectorMath'); dl.operation = 'LENGTH'; L(cmb.outputs[0], dl.inputs[0])
    dn = N('ShaderNodeMath'); dn.operation = 'DIVIDE'; L(dl.outputs['Value'], dn.inputs[0]); dn.inputs[1].default_value = 0.5 * r * 0.75
    rg = N('ShaderNodeMath'); rg.operation = 'MULTIPLY_ADD'; L(nz.outputs['Fac'], rg.inputs[0]); rg.inputs[1].default_value = 0.7; L(dn.outputs[0], rg.inputs[2])
    rim = N('ShaderNodeMapRange'); rim.inputs['From Min'].default_value = 1.25; rim.inputs['From Max'].default_value = 0.85; L(rg.outputs[0], rim.inputs['Value'])
    lumps = N('ShaderNodeMapRange'); lumps.inputs['From Min'].default_value = 0.38; lumps.inputs['From Max'].default_value = 0.52; L(nz.outputs['Fac'], lumps.inputs['Value'])
    al = N('ShaderNodeMath'); al.operation = 'MULTIPLY'; al.use_clamp = True; L(rim.outputs[0], al.inputs[0]); L(lumps.outputs[0], al.inputs[1])
    ramp = N('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.40; ramp.color_ramp.elements[0].color = (*C('#BFE4F5'), 1)
    ramp.color_ramp.elements[1].position = 0.62; ramp.color_ramp.elements[1].color = (1, 1, 1, 1); L(nz.outputs['Fac'], ramp.inputs[0])
    fm = N('ShaderNodeBsdfPrincipled'); L(ramp.outputs[0], fm.inputs['Base Color']); fm.inputs['Roughness'].default_value = 0.55
    L(ramp.outputs[0], fm.inputs['Emission Color']); fm.inputs['Emission Strength'].default_value = 0.35
    tr = N('ShaderNodeBsdfTransparent'); mx = N('ShaderNodeMixShader'); L(al.outputs[0], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(fm.outputs[0], mx.inputs[2])
    L(mx.outputs[0], out.inputs[0])
    m.use_backface_culling = True                              # only the dome's outside: its unlit inside read as grey grit
    for k, v in (('surface_render_method', 'BLENDED'), ('use_transparency_overlap', True)):    # overlap OFF = a depth prepass: its clear dome hid the water
        try: setattr(m, k, v)
        except Exception as e_: print('world.boil', k, e_)
    for fc in _fcurves(nt):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    tip = -0.93 * obj.get('pour_length', 4.2)
    b = ellipsoid(f'{obj.name}_boil', (r, r * 0.75, 0.30), (0, tip, 0.0), [m], seg=(40, 14), coll=c); b.visible_shadow = False
    b.parent = obj
    d = b.driver_add('hide_render').driver; d.type = 'AVERAGE'; v = d.variables.new(); v.name = 'h'
    v.targets[0].id = obj; v.targets[0].data_path = 'hide_render'
    return b


def spray(name, at, f0, f1, c=None, step=4, n=8, r=0.8, up=0.55, dur=12, size=0.07, stretch=2.6):
    """droplets thrown up and out where water lands: a burst every `step` frames from f0 to f1 round `at` (x, y, z).
    Droplets only: stacked foam rings read as white loops. Start it once the water has landed, not on dry ground."""
    fm = bpy.data.materials.get('TK_foam') or look.mat('TK_foam', C('#F4FBFF'), rough=0.6, brush=0.02, grain=0.0, emission=((0.9, 0.97, 1.0), 0.35))
    out = []
    for f in range(int(f0), int(f1), step):
        rnd = random.Random(f); x = at[0] + 0.7 * math.sin(f * 1.7); y = at[1] + 0.6 * math.cos(f * 1.3); z = at[2]
        for i in range(n):
            a = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(0.4, 1.0) * r; v = rnd.uniform(0.6, 1.0) * up; s = rnd.uniform(0.5, 1.0) * size
            d = ellipsoid(f'{name}{f}_{i}', (s, s, s * stretch), (x, y, z), [fm], seg=(10, 6), coll=c); d.visible_shadow = False
            for k in range(0, dur + 1, 2):
                t = k / dur; d.location = (x + math.cos(a) * sp * t, y + math.sin(a) * sp * t, z + 4 * v * t * (1 - t)); d.keyframe_insert('location', frame=f + k)
                vel = Vector((math.cos(a) * sp, math.sin(a) * sp, 4 * v * (1 - 2 * t)))         # long axis along the flight: streaks, not cotton balls
                d.rotation_euler = vel.to_track_quat('Z', 'Y').to_euler(); d.keyframe_insert('rotation_euler', frame=f + k)
            for fr_, h in ((f - 1, True), (f, False), (f + dur + 1, True)):
                d.hide_render = h; d.keyframe_insert('hide_render', frame=fr_)
            for fc in _fcurves(d):
                if fc.data_path == 'hide_render':
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
            out.append(d)
    return out


def flow_water(f0, f1):
    """make every water surface move: scroll and evolve the 'RIPPLE' mapping of each material that has one (shallow_water_mat,
    spread_mat), keyed on ABSOLUTE frames so the ripples are continuous across sets. Call once after the build."""
    from .camera import fcurves as _fc
    for m in {o.active_material for o in bpy.data.objects if o.type == 'MESH' and o.active_material and o.active_material.node_tree
              and o.active_material.node_tree.nodes.get('RIPPLE')}:
        loc = m.node_tree.nodes['RIPPLE'].inputs['Location']
        for f in (f0, f1):
            loc.default_value = (0.008 * f, 0.0, 0.02 * f); loc.keyframe_insert('default_value', frame=f)
        for fc in _fc(m.node_tree):
            if '"RIPPLE"' in fc.data_path:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'


def ripple_mat():
    """soft white for ripples: emission mixed with transparent by the OBJECT colour's alpha (each ripple keys o.color)."""
    m = bpy.data.materials.get('TK_ripple')
    if m: return m
    m = bpy.data.materials.new('TK_ripple'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); oi = N('ShaderNodeObjectInfo'); em = N('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.90, 0.96, 1.0, 1); em.inputs['Strength'].default_value = 0.85
    tr = N('ShaderNodeBsdfTransparent'); mx = N('ShaderNodeMixShader'); L(oi.outputs['Alpha'], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2])
    L(mx.outputs[0], out.inputs[0])
    for k, v in (('surface_render_method', 'BLENDED'), ('use_transparency_overlap', True)):
        try: setattr(m, k, v)
        except Exception as e: print('world.ripple_mat', k, e)
    return m


def ripple(name, loc, f, r0=0.06, r1=0.55, dur=24, alpha=0.7, c=None):
    """a soft ripple spreading on water from frame f (a footstep, a drop, something floating): a thin annulus that grows
    (ease-out) and fades. Thick opaque foam rings read as plastic discs. On rising water, drive its z from the sheet's z."""
    bm = bmesh.new(); seg = 48; o_, i_ = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg; o_.append(bm.verts.new((math.cos(a), math.sin(a), 0))); i_.append(bm.verts.new((0.86 * math.cos(a), 0.86 * math.sin(a), 0)))
    for k in range(seg): bm.faces.new((o_[k], o_[(k + 1) % seg], i_[(k + 1) % seg], i_[k]))
    o = mesh_obj(name, bm, [ripple_mat()], smooth=True, coll=c); o.location = loc; o.visible_shadow = False
    for fr_, s_, a_ in ((f, r0, alpha), (f + dur, r1, 0.0)):
        o.scale = (s_, s_, 1); o.keyframe_insert('scale', frame=fr_); o.color = (1, 1, 1, a_); o.keyframe_insert('color', frame=fr_)
    for fc in _fcurves(o):
        if fc.data_path == 'scale':
            for kp in fc.keyframe_points: kp.interpolation = 'QUAD'; kp.easing = 'EASE_OUT'
    for fr_, h in ((f - 1, True), (f, False), (f + dur + 1, True)):
        o.hide_render = h; o.keyframe_insert('hide_render', frame=fr_)
    for fc in _fcurves(o):
        if fc.data_path == 'hide_render':
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    return o
