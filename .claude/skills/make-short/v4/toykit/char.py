"""toykit.char: build a toy-family character from a spec (dict / JSON) as real 3D meshes with stylized materials,
outlines and an expressive decal face. Coordinates: the character stands at the origin facing -Y, metres, z up.
Head-relative spec values (face, hat, hair) are in units of the head WIDTH, z from the head centre."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from . import look, face


# ---------------------------------------------------------------- mesh helpers
def link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o); return o


def mesh_obj(name, bm, mats=(), smooth=True, coll=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = smooth
    o = link(bpy.data.objects.new(name, me), coll)
    for m in mats: me.materials.append(m)
    return o


def subsurf(o, lv=1, rlv=2):
    md = o.modifiers.new('sub', 'SUBSURF'); md.levels = lv; md.render_levels = rlv; return o


def ellipsoid(name, size, loc=(0, 0, 0), mats=(), seg=(40, 24), egg=0.0, coll=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg[0], v_segments=seg[1], radius=0.5)
    for v in bm.verts:
        x, y, z = v.co; f = 1.0 + egg * (-2 * z)
        v.co = Vector((x * size[0] * f, y * size[1] * f, z * size[2]))
    o = mesh_obj(name, bm, mats, coll=coll); o.location = loc; return o


def lathe(name, prof, seg=48, sy=1.0, loc=(0, 0, 0), mats=(), closed=False, coll=None):
    """revolve a (r, z) profile about Z; sy scales depth (Y). closed=True joins last->first (a solid ring)."""
    bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((r * ca, r * sa * sy, z)) for (r, z) in prof])
    n = len(prof)
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for j in range(n - (0 if closed else 1)):
            k = (j + 1) % n
            try: bm.faces.new((A[j], B[j], B[k], A[k]))
            except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, mats, coll=coll); o.location = loc; return o


def sweep(name, seg, rfun, prof, mats=(), closed=True, coll=None):
    """non-circular lathe: around Z, profile points (dr, z) are offset from a per-angle base radius rfun(theta)."""
    bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; r0 = rfun(a); ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(((r0 + dr) * ca, (r0 + dr) * sa, z)) for (dr, z) in prof])
    n = len(prof)
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for j in range(n - (0 if closed else 1)):
            k = (j + 1) % n; bm.faces.new((A[j], B[j], B[k], A[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mats, coll=coll)


def cap(name, seg, rings, rbase, z0, H, mats=(), coll=None):
    """dome over a per-angle base radius rbase(theta) at z0, height H (quarter-ellipse profile, closed at the pole)."""
    bm = bmesh.new(); R = []
    for k in range(rings):
        ph = (math.pi / 2) * k / rings
        R.append([bm.verts.new((rbase(2 * math.pi * i / seg) * math.cos(ph) * math.cos(2 * math.pi * i / seg),
                                rbase(2 * math.pi * i / seg) * math.cos(ph) * math.sin(2 * math.pi * i / seg), z0 + H * math.sin(ph)))
                  for i in range(seg)])
    pole = bm.verts.new((0, 0, z0 + H))
    for k in range(rings - 1):
        for i in range(seg): bm.faces.new((R[k][i], R[k][(i + 1) % seg], R[k + 1][(i + 1) % seg], R[k + 1][i]))
    for i in range(seg): bm.faces.new((R[-1][i], R[-1][(i + 1) % seg], pole))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mats, coll=coll)


def tube(name, p0, p1, r0, r1, rings=14, seg=16, mats=(), caps=True, coll=None):
    p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0); dz = d.normalized()
    ref = Vector((0, 0, 1)) if abs(dz.z) < 0.9 else Vector((1, 0, 0)); ux = dz.cross(ref).normalized(); uy = dz.cross(ux)
    bm = bmesh.new(); R = []
    for i in range(rings + 1):
        t = i / rings; c = p0 + d * t; r = r0 + (r1 - r0) * t
        R.append([bm.verts.new(c + (ux * math.cos(2 * math.pi * k / seg) + uy * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)])
    for i in range(rings):
        for k in range(seg):
            bm.faces.new((R[i][k], R[i][(k + 1) % seg], R[i + 1][(k + 1) % seg], R[i + 1][k]))
    if caps:
        for ring, c in ((R[0], p0), (R[-1], p1)):
            cv = bm.verts.new(c)
            for k in range(seg): bm.faces.new((ring[k], ring[(k + 1) % seg], cv))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mats, coll=coll)


def capsule(name, center, length, r, axis=(1, 0, 0), mats=(), coll=None):
    a = Vector(axis).normalized(); c = Vector(center)
    o = tube(name, c - a * length / 2, c + a * length / 2, r, r, rings=4, seg=14, mats=mats, coll=coll)
    subsurf(o, 1, 2); return o


def join(objs, name):
    objs = [o for o in objs if o]
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name; return objs[0]


# ---------------------------------------------------------------- head geometry queries (for fitting hats / hair)
class HeadShape:
    """the head ellipsoid as an implicit surface: radius queries in a (tilted) frame centred on the head."""

    def __init__(self, w, d, h, egg):
        self.w, self.d, self.h, self.egg = w, d, h, egg

    def inside(self, p):
        zn = p[2] / self.h
        if abs(zn) > 0.5: return False
        f = 1 - 2 * self.egg * zn
        return (p[0] / (self.w * f)) ** 2 + (p[1] / (self.d * f)) ** 2 + zn * zn <= 0.25

    def radius(self, th, z, R=Matrix.Identity(3)):
        """distance from the frame's z axis to the head surface along angle th at frame height z (0 if above/below)."""
        lo, hi = 0.0, max(self.w, self.d)
        if not self.inside(R @ Vector((0, 0, z))):
            # off-axis heads (tilted frames): search outward for the first inside point
            for k in range(1, 40):
                r = hi * k / 40
                if self.inside(R @ Vector((r * math.cos(th), r * math.sin(th), z))): lo = r; break
            else: return 0.0
        for _ in range(36):
            mid = 0.5 * (lo + hi)
            if self.inside(R @ Vector((mid * math.cos(th), mid * math.sin(th), z))): lo = mid
            else: hi = mid
        return lo

    def top(self, R=Matrix.Identity(3)):
        lo, hi = 0.0, self.h
        for _ in range(36):
            mid = 0.5 * (lo + hi)
            if any(self.radius(t, mid, R) > 1e-4 for t in (0, math.pi / 2, math.pi, 1.5 * math.pi)): lo = mid
            else: hi = mid
        return lo


# ---------------------------------------------------------------- materials for a spec
def materials(spec):
    C = look.hexc; nm = spec['name']
    skin = look.mat(f'{nm}_skin', C(spec.get('skin', '#F1E4CF')), rough=0.92, sss=0.0, brush=0.035, grain=0.10, spec=0.06)   # matte: no porcelain gloss
    fs = spec.get('face', {})
    return dict(
        skin=skin,
        eye_white=look.mat(f'{nm}_eyewhite', C('#FBF8F2'), rough=0.95, brush=0.0, grain=0.0, spec=0.0, emission=((1.0, 0.99, 0.97), 0.45)),   # crisp white like the sheets
        pupil=look.flat(f'{nm}_pupil', C(fs.get('pupil_color', '#1C1517'))),
        hilite=look.flat(f'{nm}_hilite', (1, 1, 1), 1.4),
        brow=look.mat(f'{nm}_brow', C(fs.get('brows', {}).get('color', '#7A4526')), rough=0.75, brush=0.06, grain=0.0),
        mouth=look.mat(f'{nm}_mouth', C('#5E1C24'), rough=0.7, brush=0.0, grain=0.0),
        teeth=look.mat(f'{nm}_teeth', C('#FBF7EE'), rough=0.6, brush=0.0, grain=0.0),
        tongue=look.mat(f'{nm}_tongue', C('#D8646B'), rough=0.6, brush=0.0, grain=0.0),
        freckle=look.mat(f'{nm}_freckle', C(fs.get('freckle_color', '#C88566')), rough=0.75, brush=0.0, grain=0.0),
        blush=_blush_mat(f'{nm}_blush', C((fs.get('blush') or {}).get('color', '#F2A0A6'))),
        smear=look.mat(f'{nm}_smear', C((fs.get('smear') or {}).get('color', '#3E3A3A')), rough=0.9, brush=0.05, grain=0.4),
        ink=look.flat('TK_decal_ink', look.INK),
    )


def _blush_mat(name, color):
    """soft-edged pink cheek: radial falloff to transparent (generated coords of the little decal)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); p = N('ShaderNodeBsdfPrincipled'); p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = 0.8
    tc = N('ShaderNodeTexCoord'); sub = N('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    L(tc.outputs['Generated'], sub.inputs[0]); ln = N('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L(sub.outputs[0], ln.inputs[0])
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.5; mr.inputs['From Max'].default_value = 0.15
    mr.inputs['To Max'].default_value = 0.85; L(ln.outputs['Value'], mr.inputs['Value']); L(mr.outputs[0], p.inputs['Alpha'])
    L(p.outputs[0], out.inputs[0])
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m


def ribbed(name, color, ribs=30, rough=0.85, sheen=0.5):
    """knit/ribbed fabric: ribs around the object's own Z axis as a bump."""
    m = look.mat(name, color, rough=rough, sheen=sheen, brush=0.07, grain=0.4, grain_scale=160)
    nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    tc = N('ShaderNodeTexCoord'); gr = N('ShaderNodeTexGradient'); gr.gradient_type = 'RADIAL'
    L(tc.outputs['Object'], gr.inputs['Vector'])
    mu = N('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = ribs * 2 * math.pi
    si = N('ShaderNodeMath'); si.operation = 'SINE'
    L(gr.outputs['Fac'], mu.inputs[0]); L(mu.outputs[0], si.inputs[0])
    bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.45; bp.inputs['Distance'].default_value = 0.004
    old = p.inputs['Normal'].links[0].from_node if p.inputs['Normal'].links else None
    L(si.outputs[0], bp.inputs['Height'])
    if old: L(old.outputs['Normal'], bp.inputs['Normal'])
    L(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def plaid_mat(name, base, line, k=26.0):
    """a checked cloth (shuka): base colour with crossing stripes in object space."""
    m = look.mat(name, base, rough=0.85, brush=0.06, grain=0.4, paint=0.06)
    nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    tc = N('ShaderNodeTexCoord'); sx = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], sx.inputs[0])
    outs = []
    for ax in ('X', 'Z'):
        mu = N('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = k; L(sx.outputs[ax], mu.inputs[0])
        fr = N('ShaderNodeMath'); fr.operation = 'FRACT'; L(mu.outputs[0], fr.inputs[0])
        lt = N('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.22; L(fr.outputs[0], lt.inputs[0]); outs.append(lt)
    mx = N('ShaderNodeMath'); mx.operation = 'MAXIMUM'; L(outs[0].outputs[0], mx.inputs[0]); L(outs[1].outputs[0], mx.inputs[1])
    mix = N('ShaderNodeMix'); mix.data_type = 'RGBA'; L(mx.outputs[0], mix.inputs['Factor'])
    if src: L(src, mix.inputs['A'])
    else: mix.inputs['A'].default_value = (*base, 1)
    mix.inputs['B'].default_value = (*line, 1); L(mix.outputs['Result'], p.inputs['Base Color'])
    return m


# ---------------------------------------------------------------- the character
class Character:
    def __init__(self, spec, origin=(0, 0, 0)):
        self.spec = spec; self.name = spec['name']; self.parts = {}
        coll = bpy.data.collections.new('CH_' + self.name); bpy.context.scene.collection.children.link(coll); self.coll = coll
        mats = materials(spec); self.mats = mats
        self._head(spec, mats)
        # the face proxy comes first: every decal (face features, moustache) wraps onto it, never onto an outline shell
        hd = spec['head']; w, h, d = hd['w'], hd['h'], hd['d']
        proxy = ellipsoid(f'{self.name}_faceproxy', (w, d, h), (0, 0, 0), [], seg=(64, 40), egg=hd.get('egg', 0.06), coll=coll)
        md = proxy.modifiers.new('sub', 'SUBSURF'); md.levels = 2; md.render_levels = 2
        proxy.parent = self.parts['head']; proxy.hide_render = True; proxy.display_type = 'WIRE'; self.parts['faceproxy'] = proxy
        face.TARGET[self.parts['head'].name] = proxy
        self._body(spec, mats)
        self._limbs(spec, mats)
        hat = spec.get('hat')
        if hat: {'beanie': self._beanie, 'kepi': self._kepi, 'toque': self._toque, 'tricorn': self._tricorn, 'wide': self._wide}[hat['kind']](hat)
        hair = spec.get('hair')
        if hair and hair['kind'] == 'curly_tuft': self._tuft(hair)
        if hair and hair['kind'] == 'wig': self._wig(hair)
        if hair and hair['kind'] == 'crop': self._crop(hair)
        if spec.get('glasses'): self._glasses(spec['glasses'])
        fh = spec.get('facial_hair')
        if fh: (self._beard if fh.get('style') == 'beard' else self._moustache)(fh)
        # face: decals wrap onto the hidden proxy of the head surface (no outline shell for the rays to hit)
        self.face = face.Face(self.parts['head'], spec.get('face', {}), mats, (w, d, h), target=proxy, coll=coll)

    # ---- head
    def _head(self, spec, mats):
        hd = spec['head']; w, h, d, hz = hd['w'], hd['h'], hd['d'], hd['z']
        head = ellipsoid(f'{self.name}_head', (w, d, h), (0, 0, hz), [mats['skin']], seg=(64, 40), egg=hd.get('egg', 0.06), coll=self.coll)
        subsurf(head, 1, 2); look.outline(head, spec.get('ink', {}).get('head', 0.0065)); self.parts['head'] = head
        self.hshape = HeadShape(w, d, h, hd.get('egg', 0.06)); self.W = w; self.hz = hz

    # ---- coat body, collar, hood, toggles, seam, neck
    def _body(self, spec, mats):
        C = look.hexc; b = spec['body']; coll = self.coll; dep = b.get('depth', 0.8)
        coatm = look.mat(f'{self.name}_coat', C(b['color']), rough=b.get('rough', 0.55), coat=b.get('gloss', 0.08), brush=0.06, grain=0.25)
        z0, z1 = b['z0'], b['z1']; rt, rb = b['top_r'], b['bot_r']
        if b.get('kind') == 'bean':     # rounded egg/bean torso: round bottom, widest low, narrow shoulders (the board look)
            wz = b.get('widest', 0.38); H_ = z1 - z0; zw = z0 + H_ * wz; prof = [(0.0, z0)]
            for i in range(1, 9):       # bottom quarter-ellipse up to the widest point
                a = (math.pi / 2) * i / 8; prof.append((rb * math.sin(a), zw - (zw - z0) * math.cos(a)))
            for i in range(1, 9):       # widest -> shoulders (eased), then a rounded top
                t = i / 8; prof.append((rb + (rt - rb) * (t * t * (3 - 2 * t)), zw + (z1 - zw) * t * 0.92))
            prof += [(rt * 0.7, z1 - 0.004), (0.0, z1 + 0.004)]
        else:
            prof = [(0.0, z0 + 0.012), (rb - 0.012, z0), (rb + 0.004, z0 + 0.014), (rb * 0.95, z0 + (z1 - z0) * 0.30),
                    (rb * 0.84, z0 + (z1 - z0) * 0.58), (rt * 1.04, z0 + (z1 - z0) * 0.88), (rt * 0.86, z1 - 0.004), (0.0, z1 + 0.006)]
        coat = lathe(f'{self.name}_coat', prof, 56, sy=dep, mats=[coatm], coll=coll)
        subsurf(coat, 1, 2); look.outline(coat, 0.0065); self.parts['body'] = coat
        def front_y(z):
            for (r0, zz0), (r1, zz1) in zip(prof, prof[1:]):
                if min(zz0, zz1) <= z <= max(zz0, zz1):
                    u = 0 if abs(zz1 - zz0) < 1e-6 else (z - zz0) / (zz1 - zz0); return -(r0 + (r1 - r0) * u) * dep
            return -rt * dep
        self.front_y = front_y
        if b.get('neck', True):
            neck = tube(f'{self.name}_neck', (0, 0, z1 - 0.06), (0, 0, self.hz - spec['head']['h'] * 0.3), 0.07, 0.07, 4, 24,
                        [look.mat(f'{self.name}_shirt', C(b.get('shirt', '#3B3A42')), rough=0.8, brush=0.03)], coll=coll)
            self.parts['neck'] = neck
        col = b.get('collar')
        if col:
            ch = col.get('h', 0.09); op = math.radians(col.get('open', 26))
            cprof = [(rt * 0.80, z1 - 0.05), (rt * 0.90, z1 + ch * 0.25), (rt * 1.02, z1 + ch * 0.7), (rt * 1.14, z1 + ch)]
            collar = lathe(f'{self.name}_collar', cprof, 64, sy=dep * 1.08, mats=[coatm], coll=coll)
            bm = bmesh.new(); bm.from_mesh(collar.data)
            kill = [f for f in bm.faces if abs(math.atan2(f.calc_center_median().y, f.calc_center_median().x) + math.pi / 2) < op]
            bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(collar.data); bm.free()
            so = collar.modifiers.new('thick', 'SOLIDIFY'); so.thickness = 0.014; so.offset = -1.0; so.use_even_offset = True
            subsurf(collar, 1, 2); look.outline(collar, 0.005); self.parts['collar'] = collar
        if b.get('hood'):
            hood = ellipsoid(f'{self.name}_hood', (rt * 1.9, 0.13, 0.15), (0, rt * 0.70, z1 + 0.01), [coatm], coll=coll)
            subsurf(hood); look.outline(hood, 0.005); self.parts['hood'] = hood
        btn = b.get('buttons')
        if btn and btn.get('kind') != 'none':
            bm_ = look.mat(f'{self.name}_btn', C(btn.get('color', '#2E2A33')), rough=0.5, brush=0.0, grain=0.0)
            zs_ = btn.get('zs') or [1 - (0.22 + 0.21 * i) for i in range(btn.get('n', 3))]
            for i, zf in enumerate(zs_):
                z = z0 + (z1 - z0) * zf; y = front_y(z) - 0.012
                if btn.get('kind') == 'toggle':
                    t = capsule(f'{self.name}_toggle{i}', (0.0, y - 0.004, z), 0.062, 0.0115, (1, 0, -0.10), [bm_], coll=coll)
                    look.outline(t, 0.003)
                    lp = tube(f'{self.name}_loop{i}', (0.035, y + 0.006, z + 0.004), (0.075, y + 0.012, z + 0.004), 0.0045, 0.0045, 4, 8, [bm_], coll=coll)
                    look.outline(lp, 0.002)
                else:
                    t = ellipsoid(f'{self.name}_btn{i}', (0.026, 0.012, 0.026), (0, y + 0.004, z), [bm_], seg=(16, 10), coll=coll); look.outline(t, 0.0025)
        # front seam: a thin ink strip wrapped onto the coat
        if b.get('seam', True):
            zs = [z0 + 0.008 + (z1 - z0 - 0.02) * i / 23 for i in range(24)]
            sx, sw = b.get('seam_x', 0.006), 0.0028
            cp = bpy.data.objects.new(f'{self.name}_coatproxy', coat.data.copy()); coll.objects.link(cp)
            subsurf(cp, 2, 2); cp.parent = coat; cp.hide_render = True; cp.display_type = 'WIRE'
            strip = face.decal(f'{self.name}_seam', coat, {'base': ([(sx - sw, z) for z in zs], [(sx + sw, z) for z in zs])},
                               [look.flat('TK_decal_ink', look.INK)], [(0, 1, 0)], -0.5, 0.0012, parent=coat, target=cp, coll=coll)
            self.parts['coatproxy'] = cp
        self.sh_z = z0 + (z1 - z0) * 0.86; self.rt = rt; self.coatm = coatm
        def r_at(z):
            for (r0, zz0), (r1, zz1) in zip(prof, prof[1:]):
                if min(zz0, zz1) <= z <= max(zz0, zz1):
                    u = 0 if abs(zz1 - zz0) < 1e-6 else (z - zz0) / (zz1 - zz0); return r0 + (r1 - r0) * u
            return rt
        self.r_at = r_at
        bt = b.get('belt')
        if bt:   # a band around the body (belt or sash): its own colour, outlined
            zb = z0 + (z1 - z0) * bt.get('z', 0.28); hb = bt.get('h', 0.045); rr = r_at(zb) + 0.004
            belt = lathe(f'{self.name}_belt', [(rr - 0.004, zb - hb / 2), (rr + 0.006, zb - hb / 2 + 0.006), (rr + 0.008, zb + hb / 2 - 0.006),
                                              (rr - 0.004, zb + hb / 2)], 56, sy=dep, mats=[look.mat(f'{self.name}_beltm', C(bt['color']), rough=0.6, brush=0.05, paint=0.05)],
                         closed=True, coll=coll)
            subsurf(belt, 1, 2); look.outline(belt, 0.004); self.parts['belt'] = belt
            if bt.get('knot'):   # a tied sash: knot + two hanging tails on the character's left hip
                km = belt.data.materials[0]; ka = math.radians(bt.get('knot_angle', -55))
                kx, ky = math.cos(ka) * (rr + 0.006), math.sin(ka) * (rr + 0.006) * dep
                knot = ellipsoid(f'{self.name}_knot', (0.05, 0.035, 0.045), (kx, ky - 0.004, zb), [km], seg=(16, 10), coll=coll)
                tails = []
                for i, (dx, Lt) in enumerate(((-0.012, 0.13), (0.014, 0.10))):
                    t_ = tube(f'{self.name}_tail{i}', (kx + dx, ky - 0.012, zb - 0.01), (kx + dx * 2.2 + 0.006, ky - 0.02, zb - Lt), 0.016, 0.012, 6, 8, [km], coll=coll)
                    for v in t_.data.vertices: v.co.y = ky - 0.016 + (v.co.y - (ky - 0.016)) * 0.45
                    tails.append(t_)
                kn = join([knot] + tails, f'{self.name}_sashknot'); subsurf(kn, 1, 1); look.outline(kn, 0.0035); self.parts['sashknot'] = kn
        ep = b.get('epaulettes')
        if ep:
            em = look.mat(f'{self.name}_epm', C(ep['color']), rough=0.5, brush=0.04, paint=0.05)
            for sd, nm in ((1, 'L'), (-1, 'R')):
                e = ellipsoid(f'{self.name}_epaulette{nm}', (0.085, 0.07, 0.03), (sd * ep.get('x', rt * 0.78), 0.0, ep.get('z', z1 - 0.004)), [em], seg=(24, 12), coll=coll)
                e.rotation_euler = (0, sd * math.radians(-18), 0); subsurf(e, 1, 1); look.outline(e, 0.004); self.parts['epaulette' + nm] = e
        cv = b.get('cravat')
        if cv:   # a white cravat: a soft puff at the throat over the coat front, with a second fold below (rides the chest)
            cm_ = look.mat(f'{self.name}_cravat', C(cv.get('color', '#F7F4EE')), rough=0.85, brush=0.06, paint=0.06)
            zc = z1 - cv.get('drop', 0.03); yc = front_y(zc) - 0.012
            puffs = [ellipsoid(f'{self.name}_cravat0', (0.105, 0.05, 0.075), (0.0, yc, zc), [cm_], seg=(24, 14), coll=coll),
                     ellipsoid(f'{self.name}_cravat1', (0.075, 0.042, 0.07), (0.0, front_y(zc - 0.06) - 0.010, zc - 0.06), [cm_], seg=(20, 12), coll=coll)]
            cvo = join(puffs, f'{self.name}_cravat'); subsurf(cvo, 1, 1); look.outline(cvo, 0.004); self.parts['cravat'] = cvo
        ap = b.get('apron')
        if ap:   # a white apron wrapped onto the coat front (bib + skirt), outlined
            cp = self.parts.get('coatproxy')
            if cp is None:
                cp = bpy.data.objects.new(f'{self.name}_coatproxy', coat.data.copy()); coll.objects.link(cp)
                subsurf(cp, 2, 2); cp.parent = coat; cp.hide_render = True; cp.display_type = 'WIRE'; self.parts['coatproxy'] = cp
            zt, zbm = z0 + (z1 - z0) * ap.get('top', 0.80), z0 + 0.012; zw = z0 + (z1 - z0) * ap.get('waist', 0.42)
            top, bot = [], []
            for i in range(28):       # columns run DOWN the body: left edge = 'top' curve, right edge = 'bot' curve
                z = zt + (zbm - zt) * i / 27
                wb = ap.get('bib', 0.075); ws = r_at(z) * 0.86
                w = wb + (ws - wb) * (1 - 1 / (1 + math.exp((zw - z) / 0.012)))
                top.append((-w, z)); bot.append((w, z))
            am = look.mat(f'{self.name}_apronm', C(ap.get('color', '#F7F4EE')), rough=0.8, brush=0.05, paint=0.06)
            face.decal(f'{self.name}_apron', coat, {'base': (top, bot)}, [am], [(0, 1, 0)], -0.5, 0.0030, parent=coat, target=cp, coll=coll)
            face.decal(f'{self.name}_apron_ink', coat, {'base': face.dilate(top, bot, 0.004)}, [look.flat('TK_decal_ink', look.INK)], [(0, 1, 0)],
                       -0.5, 0.0022, parent=coat, target=cp, coll=coll)

        lw = b.get('lower')
        if lw:   # two-tone bean: trousers below z (absolute), a material split on the same mesh
            lm = look.mat(f'{self.name}_lower', C(lw['color']), rough=lw.get('rough', 0.85), brush=0.06, grain=0.3, paint=0.08)
            coat.data.materials.append(lm)
            for poly in coat.data.polygons:
                if poly.center.z < lw['z']: poly.material_index = 1
        bd_ = b.get('bandana')
        if bd_: self._bandana(bd_, coat, z0, z1, r_at, front_y, dep)
        sh_ = b.get('sash')
        if sh_: self._sash(sh_, coat, z0, z1, r_at, front_y, dep)

    def _coatproxy(self, coat):
        cp = self.parts.get('coatproxy')
        if cp is None:
            cp = bpy.data.objects.new(f'{self.name}_coatproxy', coat.data.copy()); self.coll.objects.link(cp)
            subsurf(cp, 2, 2); cp.parent = coat; cp.hide_render = True; cp.display_type = 'WIRE'; self.parts['coatproxy'] = cp
        return cp

    # ---- bandana: a triangle knotted at the neck (decal on the chest) + a rolled band round the neck + a knot at the back
    def _bandana(self, bd, coat, z0, z1, r_at, front_y, dep):
        C = look.hexc; coll = self.coll; cp = self._coatproxy(coat)
        bm_ = look.mat(f'{self.name}_bandana', C(bd['color']), rough=0.8, brush=0.07, grain=0.3, paint=0.10)
        zt = z1 - bd.get('top', 0.035); zp = z1 - bd.get('drop', 0.17); wt = bd.get('w', 0.10)
        top, bot = [], []
        for i in range(24):
            z = zt + (zp - zt) * i / 23; w = max(0.004, wt * (1 - i / 23) ** 1.1)
            top.append((-w, z)); bot.append((w, z))
        face.decal(f'{self.name}_bandana', coat, {'base': (top, bot)}, [bm_], [(0, 1, 0)], -0.5, 0.0040, parent=coat, target=cp, coll=coll)
        face.decal(f'{self.name}_bandana_ink', coat, {'base': face.dilate(top, bot, 0.004)}, [look.flat('TK_decal_ink', look.INK)], [(0, 1, 0)],
                   -0.5, 0.0030, parent=coat, target=cp, coll=coll)
        zr = z1 - bd.get('ring', 0.03); rr = r_at(zr) + 0.006; hb = bd.get('ring_h', 0.04)
        ring = lathe(f'{self.name}_bandring', [(rr - 0.01, zr - hb / 2), (rr + 0.008, zr - hb / 2 + 0.008), (rr + 0.012, zr), (rr + 0.008, zr + hb / 2 - 0.008),
                                               (rr - 0.01, zr + hb / 2)], 48, sy=dep, mats=[bm_], closed=True, coll=coll)
        knot = ellipsoid(f'{self.name}_bandknot', (0.06, 0.04, 0.045), (0, rr * dep + 0.01, zr), [bm_], seg=(16, 10), coll=coll)
        tails = [tube(f'{self.name}_bandtail{i}', (sx * 0.01, rr * dep + 0.02, zr - 0.005), (sx * 0.045, rr * dep + 0.03, zr - 0.06), 0.014, 0.008, 5, 8, [bm_], coll=coll)
                 for i, sx in enumerate((-1, 1))]
        nb = join([ring, knot] + tails, f'{self.name}_bandana_neck'); subsurf(nb, 1, 1); look.outline(nb, 0.0035); self.parts['bandana_neck'] = nb

    # ---- sash (a shuka cloth): a plaid band from one shoulder across the chest to the other hip, plus the loose end
    def _sash(self, sh, coat, z0, z1, r_at, front_y, dep):
        C = look.hexc; coll = self.coll; cp = self._coatproxy(coat)
        pm = plaid_mat(f'{self.name}_plaid', C(sh.get('color', '#C8322E')), C(sh.get('line', '#2F4FA8')), sh.get('scale', 26.0))
        zs, zh = z1 - sh.get('top', 0.05), z0 + (z1 - z0) * sh.get('hip', 0.28)
        hw = sh.get('w', 0.045); top, bot = [], []
        for i in range(28):
            t = i / 27; z = zs + (zh - zs) * t
            xc = (1 - t) * sh.get('x0', 0.7) * r_at(zs) + t * sh.get('x1', -0.72) * r_at(zh)
            top.append((xc - hw, z)); bot.append((xc + hw, z))
        face.decal(f'{self.name}_sash', coat, {'base': (top, bot)}, [pm], [(0, 1, 0)], -0.5, 0.0045, parent=coat, target=cp, coll=coll)
        face.decal(f'{self.name}_sash_ink', coat, {'base': face.dilate(top, bot, 0.004)}, [look.flat('TK_decal_ink', look.INK)], [(0, 1, 0)],
                   -0.5, 0.0035, parent=coat, target=cp, coll=coll)
        # the loose end hangs down over the shoulder at the front
        xs = sh.get('x0', 0.7) * r_at(zs) + hw * 0.6; ze = z0 + (z1 - z0) * sh.get('end', 0.25)
        end = tube(f'{self.name}_sashend', (xs, front_y(zs) * 0.92, zs + 0.01), (xs + 0.02, front_y(ze) - 0.03, ze), 0.045, 0.05, 10, 14, [pm], coll=coll)
        for v in end.data.vertices:     # flatten into a cloth panel lying on the chest
            v.co.y = front_y(v.co.z) - 0.018 + (v.co.y - (front_y(v.co.z) - 0.018)) * 0.28
        subsurf(end, 1, 1); look.outline(end, 0.004); self.parts['sash_end'] = end

    # ---- arms (A-pose), hands, legs, boots
    def _limbs(self, spec, mats):
        C = look.hexc; b = spec['body']; coll = self.coll
        a = spec['arms']; stick = a.get('style') == 'stick'
        sl = look.mat(f'{self.name}_sleeve', C(a.get('color', '#1E1B22' if stick else b['color'])), rough=0.55 if stick else b.get('rough', 0.55),
                      coat=0.0 if stick else b.get('gloss', 0.08), brush=0.02 if stick else 0.06)
        handm = look.mat(f'{self.name}_hand', C(a['hand']['color']), rough=0.55, brush=0.03)
        ang = math.radians(a.get('angle', 35)); L_ = a['len']; self.arm = {}
        for side, nm in ((1, 'L'), (-1, 'R')):
            p0 = Vector((side * self.rt * 0.92, 0.0, self.sh_z)); p1 = p0 + Vector((side * math.cos(ang), 0.0, -math.sin(ang))) * L_
            r0, r1 = (a.get('r', 0.012), a.get('r', 0.012)) if stick else (a['r0'], a['r1'])
            if stick:
                sx_, sz_ = a.get('shoulder', (self.rt * 0.80, self.sh_z - 0.03))
                p0 = Vector((side * sx_, 0.0, sz_)); p1 = p0 + Vector((side * math.cos(ang), 0.0, -math.sin(ang))) * L_
            sleeve = tube(f'{self.name}_sleeve{nm}', p0, p1, r0, r1, 16, 10 if stick else 16, [sl], coll=coll)
            subsurf(sleeve, 1, 1); look.outline(sleeve, 0.003 if stick else 0.0055)
            hand = ellipsoid(f'{self.name}_hand{nm}', (a['hand']['r'] * 2,) * 3, p1 + (p1 - p0).normalized() * a['hand']['r'] * 0.7, [handm], seg=(32, 18), coll=coll)
            look.outline(hand, 0.0045)
            self.arm[nm] = (p0, p1); self.parts['sleeve' + nm] = sleeve; self.parts['hand' + nm] = hand
        lg = spec['legs']; legm = look.mat(f'{self.name}_leg', C(lg['color']), rough=0.6, brush=0.02)
        ft = spec['feet']; bootm = look.mat(f'{self.name}_boot', C(ft['color']), rough=0.45, coat=0.15, brush=0.05)
        for side, nm in ((1, 'L'), (-1, 'R')):
            x = side * lg['hip_x']
            if ft.get('kind') in ('round', 'clog'): lg['z_ankle'] = min(lg['z_ankle'], ft['r'] * 0.6 - 0.02)     # the stick ends inside the foot
            leg = tube(f'{self.name}_leg{nm}', (x, 0, lg['z_hip']), (x, 0, lg['z_ankle'] + 0.02), lg['r'], lg['r'], 8, 12, [legm], coll=coll)
            look.outline(leg, 0.003)
            bh, br = ft['h'], ft['r']
            if ft.get('kind') == 'round':     # small rounded black feet (the board look)
                boot = ellipsoid(f'{self.name}_boot{nm}', (br * 1.7, br * 2.6, br * 1.1), (x, -br * 0.55, br * 0.52), [bootm], seg=(28, 16), coll=coll)
                subsurf(boot, 1, 1); look.outline(boot, 0.004)
            elif ft.get('kind') == 'clog':     # a Dutch wooden clog: long, rounded, the toe pinched to a point and turned up
                Lc = ft.get('len', br * 3.4); y0 = -Lc * ft.get('fwd', 0.20)
                boot = ellipsoid(f'{self.name}_boot{nm}', (br * 1.75, Lc, br * 1.30), (x, y0, br * 0.62), [bootm], seg=(36, 20), coll=coll)
                bmc = bmesh.new(); bmc.from_mesh(boot.data)
                for v in bmc.verts:
                    u = max(0.0, -v.co.y / (Lc / 2))                     # 0 mid-shoe -> 1 at the toe tip
                    v.co.x *= 1 - 0.45 * u ** 1.6; v.co.z += ft.get('toe_up', 0.45) * br * u ** 2.6
                    if v.co.z < -br * 0.62: v.co.z = -br * 0.62           # flat sole
                bmc.to_mesh(boot.data); bmc.free(); subsurf(boot, 1, 2); look.outline(boot, 0.004)
            else:
                shaft = lathe(f'{self.name}_boot{nm}', [(0.0, 0.0), (br, 0.0), (br * 1.02, 0.02), (br * 0.97, bh * 0.85), (br * 1.06, bh), (br * 0.8, bh + 0.004), (0.0, bh)],
                              32, sy=1.0, loc=(x, 0.006, 0.0), mats=[bootm], coll=coll)
                toe = ellipsoid(f'{self.name}_toe{nm}', (br * 1.9, ft.get('toe', 0.075) * 2, br * 1.15), (x, -br * 0.75, br * 0.5), [bootm], coll=coll)
                boot = join([shaft, toe], f'{self.name}_boot{nm}'); subsurf(boot, 1, 2); look.outline(boot, 0.005)
            self.parts['leg' + nm] = leg; self.parts['boot' + nm] = boot

    # ---- beanie: a dome + folded brim fitted to the head in a tilted frame (front higher)
    def _beanie(self, hat):
        C = look.hexc; W = self.W; hs = self.hshape; coll = self.coll
        tilt = math.radians(hat.get('tilt', 14)); R = Matrix.Rotation(-tilt, 3, 'X')
        zb = hat.get('brim_z', 0.04) * W; bh = hat.get('brim_h', 0.12) * W; th = hat.get('thick', 0.05) * W; clr = 0.004
        hm = ribbed(f'{self.name}_beanie', C(hat['color']), ribs=hat.get('ribs', 26))
        zs = [zb + bh * i / 6 for i in range(7)]
        seg = 64; rin = {}
        for i in range(seg):
            a = 2 * math.pi * i / seg; rin[i] = max(hs.radius(a, z, R) for z in zs) + clr
        rf = lambda a: rin[int(round(a / (2 * math.pi) * seg)) % seg]
        prof = [(0.0, zb + bh * 0.10), (th * 0.30, zb), (th * 0.80, zb), (th * 1.02, zb + bh * 0.16), (th * 1.10, zb + bh * 0.5),
                (th * 1.02, zb + bh * 0.84), (th * 0.80, zb + bh), (th * 0.30, zb + bh), (0.0, zb + bh * 0.90)]
        brim = sweep(f'{self.name}_brim', seg, rf, prof, [hm], closed=True, coll=coll)
        zt = zb + bh * 0.82; Hd = hs.top(R) - zt + hat.get('crown', 0.10) * W
        dome = cap(f'{self.name}_dome', seg, 14, lambda a: rf(a) + th * 0.62, zt, Hd, [hm], coll=coll)
        for o in (brim, dome):
            o.location = (0, 0, self.hz); o.rotation_euler = (-tilt, 0, 0)
            subsurf(o, 1, 2); look.outline(o, 0.006)
        self.parts['hat'] = dome; self.parts['brim'] = brim
        self.hat_frame = dict(R=R, zb=zb, bh=bh, th=th, rf=rf, zt=zt, Hd=Hd, tilt=tilt)
        f = R @ Vector((0, -rf(1.5 * math.pi), zb)); print(f'toykit: beanie brim front lower edge at z={f.z / W:+.3f} W (head centre)')

    def _hat_frame(self, hat, default_tilt):
        W = self.W; tilt = math.radians(hat.get('tilt', default_tilt)); R = Matrix.Rotation(-tilt, 3, 'X')
        return W, tilt, R

    def _fit(self, R, zs, seg=64, clr=0.004):
        rin = {}
        for i in range(seg):
            a = 2 * math.pi * i / seg; rin[i] = max(self.hshape.radius(a, z, R) for z in zs) + clr
        return lambda a: rin[int(round(a / (2 * math.pi) * seg)) % seg]

    def _place(self, objs, tilt, ink=0.006):
        for o in objs:
            o.location = (0, 0, self.hz); o.rotation_euler = (-tilt, 0, 0); subsurf(o, 1, 2); look.outline(o, ink)

    # ---- kepi: fitted band (accent colour) + tall slightly tapered crown + flat top + forward visor
    def _kepi(self, hat):
        C = look.hexc; W, tilt, R = self._hat_frame(hat, 4); coll = self.coll
        zb = hat.get('band_z', 0.10) * W; bh = hat.get('band_h', 0.10) * W; th = 0.012
        H = max(hat.get('crown_h', 0.30) * W, self.hshape.top(R) - (zb + bh * 0.85) + 0.06 * W)    # the crown always clears the head
        rf = self._fit(R, [zb + bh * i / 6 for i in range(7)])
        cm = look.mat(f'{self.name}_kepi', C(hat['color']), rough=0.7, brush=0.06, grain=0.3, paint=0.08)
        bm_ = look.mat(f'{self.name}_kepiband', C(hat.get('band', '#E7B623')), rough=0.55, brush=0.05, paint=0.05)
        vm = look.mat(f'{self.name}_visor', C(hat.get('visor', '#1E1B22')), rough=0.35, coat=0.3, brush=0.02)
        band = sweep(f'{self.name}_kband', 64, rf, [(0, zb), (th, zb), (th * 1.1, zb + bh * 0.5), (th, zb + bh), (0, zb + bh)], [bm_], closed=True, coll=coll)
        soft = hat.get('soft', False)
        tp = hat.get('taper', 1.05); zc0 = zb + bh * 0.85
        rc = self._fit(R, [zc0 + H * i / 8 for i in range(9)])
        rfc = lambda a: max(rf(a), rc(a)) + hat.get('puff', 0.0) * W * 0.5
        crown = sweep(f'{self.name}_kcrown', 64, lambda a: rfc(a) + th * 0.6,
                      [(0, zc0), (th * 0.2, zc0), ((tp - 1) * 0.5 * W + th * 0.4, zc0 + H * 0.96), ((tp - 1) * 0.5 * W, zc0 + H), (0, zc0 + H)], [cm], closed=False, coll=coll)
        top = cap(f'{self.name}_ktop', 64, 6, lambda a: rfc(a) + th * 0.6 + (tp - 1) * 0.5 * W, zc0 + H - 0.003, 0.012, [cm], coll=coll)
        if soft:   # forage cap: replace the drum with a squashed, lumpy crown that falls forward over the visor
            for o in (crown, top): bpy.data.objects.remove(o, do_unlink=True)
            r0 = max(rfc(a) for a in (0, math.pi / 2, math.pi, 1.5 * math.pi)) * hat.get('crown_w', 1.18)
            crown = ellipsoid(f'{self.name}_kcrown', (r0 * 2, r0 * 2 * 1.05, H * 1.15), (0, -hat.get('overhang', 0.12) * W, zc0 + H * 0.42), [cm], seg=(48, 24), coll=coll)
            bmc = bmesh.new(); bmc.from_mesh(crown.data)
            for v in bmc.verts:
                v.co.x += hat.get('slouch', 0.05) * W * max(0.0, v.co.z / (H * 0.6))
                v.co.z -= 0.35 * H * max(0.0, -v.co.y / r0) ** 2                      # the front droops toward the visor
                v.co *= 1 + 0.03 * math.sin(5 * math.atan2(v.co.y, v.co.x))           # soft lumps
                if v.co.z < -H * 0.30: v.co.z = -H * 0.30
            bmc.to_mesh(crown.data); bmc.free(); top = None
            crown.data.transform(Matrix.Translation(crown.location)); crown.location = (0, 0, 0)    # keep the offset through _place
        k = math.tan(math.radians(hat.get('slope', 12)))          # the kepi's top slopes down toward the visor
        ov = hat.get('overhang', 0.0) * W; sl = hat.get('slouch', 0.0) * W
        for o, full in (() if soft else ((crown, False), (top, True))):
            for v in o.data.vertices:
                f = 1.0 if full else max(0.0, (v.co.z - zc0) / H)
                v.co.z += k * v.co.y * f
                v.co.y -= ov * f ** 1.5                                     # a soft forage cap's crown falls forward over the visor
                v.co.x += sl * f ** 1.5                                     # ...and a little to one side
        # visor: front half-ellipse, drooping
        bmv = bmesh.new(); n = 24; rings = []
        for k in range(3):
            rr = []
            for i in range(n + 1):
                a = math.pi * (1.06 + 0.88 * i / n); r0 = rf(a) + th * 0.9
                ext = hat.get('visor_len', 0.13) * W * (math.sin(math.pi * i / n) ** 0.7) * (k / 2)
                d = 0.25 * ext                       # droop
                rr.append(bmv.verts.new(((r0 + ext) * math.cos(a), (r0 + ext) * math.sin(a), zb - d - 0.004 * (k == 0))))
            rings.append(rr)
        for k in range(2):
            for i in range(n): bmv.faces.new((rings[k][i], rings[k][i + 1], rings[k + 1][i + 1], rings[k + 1][i]))
        visor = mesh_obj(f'{self.name}_visor', bmv, [vm], coll=coll)
        so = visor.modifiers.new('thick', 'SOLIDIFY'); so.thickness = 0.008; so.offset = 0
        self._place([o for o in (band, crown, top, visor) if o], tilt)
        self.parts['hat'] = crown; self.parts['brim'] = band; self.parts['visor'] = visor
        if top: self.parts['hat_top'] = top
        self.hat_frame = dict(R=R, zb=zb, bh=bh, th=th, rf=rf, zt=zc0 + H, Hd=0.01, tilt=tilt)

    # ---- chef toque: pleated band + puffy top
    def _toque(self, hat):
        C = look.hexc; W, tilt, R = self._hat_frame(hat, 6); coll = self.coll
        zb = hat.get('band_z', 0.10) * W; th = 0.010
        bh = max(hat.get('band_h', 0.16) * W, self.hshape.top(R) - zb + 0.02 * W)                # the tall pleated tube clears the head
        rf0 = self._fit(R, [zb + bh * i / 10 for i in range(11)]); mr = hat.get('min_r', 0.0) * W
        rf = lambda a: max(rf0(a), mr)
        wm = ribbed(f'{self.name}_toque', C(hat.get('color', '#F8F6F1')), ribs=hat.get('pleats', 18), rough=0.85, sheen=0.2)
        fl = hat.get('flare', 0.05) * W
        band = sweep(f'{self.name}_tband', 64, rf, [(0, zb), (th, zb), (th * 1.3 + fl * 0.3, zb + bh * 0.5), (th * 1.6 + fl, zb + bh), (0, zb + bh)], [wm], closed=True, coll=coll)
        pm = look.mat(f'{self.name}_toquetop', C(hat.get('color', '#F8F6F1')), rough=0.9, brush=0.05, paint=0.06)
        Hp = hat.get('puff_h', 0.42) * W; rp = hat.get('puff_r', 0.62) * W; zp = zb + bh
        balls = [ellipsoid(f'{self.name}_tp0', (rp * 1.25, rp * 1.2, Hp * 0.95), (0, 0, zp + Hp * 0.55), [pm], seg=(32, 18), coll=coll)]
        for i in range(6):
            a_ = 2 * math.pi * i / 6 + math.pi / 6
            balls.append(ellipsoid(f'{self.name}_tp{i + 1}', (rp * 0.95, rp * 0.95, Hp * 0.78),
                                   (math.cos(a_) * rp * 0.52, math.sin(a_) * rp * 0.48, zp + Hp * 0.40), [pm], seg=(28, 16), coll=coll))
        puff = join(balls, f'{self.name}_tpuff')
        puff.data.transform(Matrix.Translation(puff.location)); puff.location = (0, 0, 0)     # hat-frame coords survive _place
        bm = bmesh.new(); bm.from_mesh(puff.data)
        for v in bm.verts:
            if v.co.z < zp + Hp * 0.08: v.co.z = zp + Hp * 0.08 + (v.co.z - zp - Hp * 0.08) * 0.25
        bm.to_mesh(puff.data); bm.free()
        self._place([band, puff], tilt)
        self.parts['hat'] = puff; self.parts['brim'] = band
        self.hat_frame = dict(R=R, zb=zb, bh=bh, th=th, rf=rf, zt=zb + bh, Hd=Hp, tilt=tilt)

    # ---- tricorn: a round crown over a fitted base + a wide brim cocked up on three sides (points at the front and the
    #      two back corners), an optional trim along the brim edge and an optional plume. Values in W (head width).
    def _tricorn(self, hat):
        C = look.hexc; W, tilt, R = self._hat_frame(hat, 4); coll = self.coll
        zb = hat.get('band_z', 0.12) * W; th = 0.010
        rf = self._fit(R, [zb + 0.14 * W * i / 6 for i in range(7)])
        H = max(hat.get('crown_h', 0.24) * W, self.hshape.top(R) - zb + 0.05 * W)
        hm = look.mat(f'{self.name}_tricorn', C(hat['color']), rough=0.8, brush=0.08, grain=0.4, paint=0.10)
        crown = cap(f'{self.name}_tcrown', 64, 14, lambda a: rf(a) + th, zb, H, [hm], coll=coll)
        BW = hat.get('brim_w', 0.30) * W; fold = math.radians(hat.get('fold', 72)); af = 1.5 * math.pi   # front corner at -Y
        nseg, nr = 96, 8; bm = bmesh.new(); rings = []; edge = []
        for i in range(nseg):
            a = 2 * math.pi * i / nseg; c3 = math.cos(3 * (a - af))                  # +1 at the 3 corners, -1 between them
            side = (1 - c3) / 2; bw = BW * (0.82 + 0.40 * ((1 + c3) / 2) ** 3)
            r, z = rf(a) + th, zb; row = [bm.verts.new((r * math.cos(a), r * math.sin(a), z))]
            for k in range(1, nr):
                t = k / (nr - 1); ph = fold * side * min(1.0, t * 1.6)               # the sides fold up toward the crown
                r += bw / (nr - 1) * math.cos(ph); z += bw / (nr - 1) * math.sin(ph) - hat.get('droop', 0.02) * W / (nr - 1) * (1 - side)
                row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
            rings.append(row); edge.append(Vector(row[-1].co))
        for i in range(nseg):
            A, B = rings[i], rings[(i + 1) % nseg]
            for k in range(nr - 1): bm.faces.new((A[k], B[k], B[k + 1], A[k + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        brim = mesh_obj(f'{self.name}_tbrim', bm, [hm], coll=coll)
        so = brim.modifiers.new('thick', 'SOLIDIFY'); so.thickness = hat.get('brim_t', 0.035) * W; so.offset = 0.0
        extra = []
        if hat.get('trim'):                                  # a braid along the brim edge
            tm = look.mat(f'{self.name}_ttrim', C(hat['trim']), rough=0.45, brush=0.04, paint=0.05)
            tr = hat.get('trim_r', 0.018) * W; bt = bmesh.new(); circ = []
            for i, p in enumerate(edge):
                q = edge[(i + 1) % nseg] - edge[i - 1]; tg = q.normalized(); up = Vector((0, 0, 1)); nx = tg.cross(up).normalized(); ny = nx.cross(tg)
                circ.append([bt.verts.new(p + (nx * math.cos(2 * math.pi * j / 8) + ny * math.sin(2 * math.pi * j / 8)) * tr) for j in range(8)])
            for i in range(nseg):
                A, B = circ[i], circ[(i + 1) % nseg]
                for j in range(8): bt.faces.new((A[j], B[j], B[(j + 1) % 8], A[(j + 1) % 8]))
            bmesh.ops.recalc_face_normals(bt, faces=bt.faces); extra.append(mesh_obj(f'{self.name}_ttrimm', bt, [tm], coll=coll))
        if hat.get('plume'):                                 # a few feather blades fanned on the character's left side
            pm = look.mat(f'{self.name}_plume', C(hat['plume']), rough=0.9, brush=0.06, paint=0.08)
            pa = math.radians(hat.get('plume_angle', 20)); base = Vector((math.cos(pa) * (rf(pa) * 0.85), math.sin(pa) * (rf(pa) * 0.85), zb + H * 0.55))
            ps = hat.get('plume_scale', 1.0)
            for k, (rx, ry, ln) in enumerate(((0, -35, 0.62), (14, -50, 0.52), (-12, -22, 0.50))):
                ln *= ps
                f_ = ellipsoid(f'{self.name}_plume{k}', (0.16 * W * ps ** 0.5, 0.08 * W, ln * W), (0, 0, ln * W * 0.45), [pm], seg=(20, 12), coll=coll)
                f_.data.transform(Matrix.Translation((0, 0, ln * W * 0.45)))
                f_.data.transform(Matrix.Rotation(math.radians(ry), 4, 'Y') @ Matrix.Rotation(math.radians(rx), 4, 'X'))
                f_.data.transform(Matrix.Translation(base)); f_.location = (0, 0, 0); extra.append(f_)
        if extra:
            for o in extra: o.location = (0, 0, 0)
            crown = join([crown] + extra, f'{self.name}_tcrown')
        self._place([crown, brim], tilt)
        self.parts['hat'] = crown; self.parts['brim'] = brim
        self.hat_frame = dict(R=R, zb=zb, bh=0.14 * W, th=th, rf=rf, zt=zb + H, Hd=H, tilt=tilt)

    # ---- wide: a capotain / farmer's felt hat: a tall, slightly tapered crown with a rounded top, an accent band and a
    #      wide brim that droops a little at the edge. Values in W (head width).
    def _wide(self, hat):
        C = look.hexc; W, tilt, R = self._hat_frame(hat, 4); coll = self.coll
        zb = hat.get('band_z', 0.10) * W; bh = hat.get('band_h', 0.08) * W; th = 0.012
        Hc = max(hat.get('crown_h', 0.42) * W, self.hshape.top(R) - zb + 0.06 * W)
        rf = self._fit(R, [zb + Hc * 0.3 * i / 6 for i in range(7)]); tp = hat.get('taper', 0.88)
        hm = look.mat(f'{self.name}_wide', C(hat['color']), rough=0.85, brush=0.08, grain=0.4, paint=0.10)
        rt = lambda a: rf(a) * tp + th
        crown = sweep(f'{self.name}_wcrown', 64, lambda a: rf(a) + th,
                      [(0, zb), ((tp - 1) * 0.5 * W * 0.2, zb + Hc * 0.5), ((tp - 1) * 0.5 * W, zb + Hc), (-W * 0.02, zb + Hc + 0.01)], [hm], closed=False, coll=coll)
        top = cap(f'{self.name}_wtop', 64, 8, lambda a: max(0.01, rf(a) + th + (tp - 1) * 0.5 * W - W * 0.02), zb + Hc, hat.get('top_round', 0.05) * W, [hm], coll=coll)
        objs = [crown, top]
        if hat.get('band'):
            bmat = look.mat(f'{self.name}_wband', C(hat['band']), rough=0.6, brush=0.05, paint=0.06)
            objs.append(sweep(f'{self.name}_wband', 64, lambda a: rf(a) + th, [(0, zb), (0.006, zb + 0.004), (0.006, zb + bh - 0.004), (0, zb + bh)], [bmat], closed=True, coll=coll))
        BW = hat.get('brim_w', 0.34) * W; dr = hat.get('droop', 0.05) * W; up = hat.get('front_up', 0.0) * W
        nseg, nr = 96, 6; bm = bmesh.new(); rings = []
        for i in range(nseg):
            a = 2 * math.pi * i / nseg; fr = max(0.0, -math.sin(a)) ** 2      # 1 at the front (-Y)
            r0 = rf(a) + th; row = []; side = math.cos(a) ** 2                  # 1 at the sides (+-X)
            fray = hat.get('fray', 0.0) * W * (0.55 + 0.45 * math.sin(37 * a) * math.sin(13 * a + 1.3))
            flop = hat.get('flop', 0.0) * W * side
            for k in range(nr):
                t = k / (nr - 1); r = r0 + (BW + fray * t ** 4) * t; z = zb - (dr + flop) * t * t + up * fr * t * t
                row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
            rings.append(row)
        for i in range(nseg):
            A, B = rings[i], rings[(i + 1) % nseg]
            for k in range(nr - 1): bm.faces.new((A[k], B[k], B[k + 1], A[k + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        brim = mesh_obj(f'{self.name}_wbrim', bm, [hm], coll=coll)
        so = brim.modifiers.new('thick', 'SOLIDIFY'); so.thickness = hat.get('brim_t', 0.035) * W; so.offset = 0.0
        crown = join(objs, f'{self.name}_wcrown')
        self._place([crown, brim], tilt)
        self.parts['hat'] = crown; self.parts['brim'] = brim
        self.hat_frame = dict(R=R, zb=zb, bh=bh, th=th, rf=rf, zt=zb + Hc, Hd=0.05 * W, tilt=tilt)

    # ---- moustache: a shaped strip drawn on the face (top/bottom curves from a per-style centreline), wrapped onto the
    #      head like the face features, then given depth (solidify), rounded (subsurf) and outlined.
    STACHE = {   # cubic Bezier for the RIGHT half, from the centre (0,0) to the tip, in units of the span; thickness profile
        'handlebar':  (((0, 0), (0.24, -0.13), (0.44, -0.12), (0.50, 0.07)), lambda u: 1 - 0.82 * u ** 1.2),
        'walrus':     (((0, 0.02), (0.20, 0.0), (0.40, -0.13), (0.50, -0.22)), lambda u: 1 - 0.45 * u),
        'bushy_curl': (((0, 0), (0.22, -0.05), (0.43, -0.15), (0.50, 0.05)), lambda u: 1 - 0.78 * u ** 1.4),
        'chevron':    (((0, 0.02), (0.18, 0.0), (0.36, -0.06), (0.48, -0.14)), lambda u: 1 - 0.30 * u),
        'thin':       (((0, 0), (0.2, -0.02), (0.38, -0.04), (0.5, -0.02)), lambda u: 1 - 0.6 * u),
    }

    def _moustache(self, fh):
        C = look.hexc; W = self.W; coll = self.coll
        z = fh.get('z', -0.30) * W; span = fh.get('span', 0.42) * W; thick = fh.get('thick', 0.07) * W
        (p0, p1, p2, p3), wfn = self.STACHE.get(fh.get('style', 'handlebar'), self.STACHE['handlebar'])
        def bez(u):
            q = [(1 - u) ** 3 * a + 3 * (1 - u) ** 2 * u * b_ + 3 * (1 - u) * u * u * c + u ** 3 * d
                 for a, b_, c, d in zip(p0, p1, p2, p3)]
            dq = [3 * (1 - u) ** 2 * (b_ - a) + 6 * (1 - u) * u * (c - b_) + 3 * u * u * (d - c) for a, b_, c, d in zip(p0, p1, p2, p3)]
            return q, dq
        n = 22; top, bot = [], []
        for side in (-1, 1):
            us = [1 - i / (n - 1) for i in range(n)] if side < 0 else [i / (n - 1) for i in range(1, n)]
            for u in us:
                (qx, qz), (dx, dz) = bez(u); x = side * qx * span; zz = z + qz * span
                tx, tz = side * dx, dz; ln = math.hypot(tx, tz) or 1.0; nx, nz = -tz / ln, tx / ln
                if nz < 0: nx, nz = -nx, -nz
                w = thick * max(0.12, wfn(u)) / 2
                top.append((x + nx * w, zz + nz * w)); bot.append((x - nx * w, zz - nz * w))
        mm = look.mat(f'{self.name}_moust', C(fh.get('color', '#7A4A26')), rough=0.8, brush=0.12, grain=0.6, grain_scale=260, paint=0.14, paint_scale=14)
        head = self.parts['head']; d = self.spec['head']['d']
        mo = face.decal(f'{self.name}_moustache', head, {'base': (top, bot)}, [mm], [(0, 1, 0)], -d * 0.5 - 0.3, 0.004,
                        target=self.parts['faceproxy'], coll=coll)
        so = mo.modifiers.new('depth', 'SOLIDIFY'); so.thickness = fh.get('depth', 0.45) * thick; so.offset = -1.0; so.use_even_offset = True
        subsurf(mo, 2, 2); look.outline(mo, 0.004); mo.visible_shadow = True
        self.parts['moustache_decal'] = mo

    # ---- beard: a bushy U from sideburn to sideburn under the mouth (wrapped onto the face like the moustache, then
    #      given depth), plus a hanging tuft below the chin. The upper lip stays bare. Values in W from the head centre.
    def _beard(self, fh):
        C = look.hexc; W = self.W; coll = self.coll; d = self.spec['head']['d']
        # the right half of each edge, from under the mouth (x = 0) up to the sideburn, in W from the head centre;
        # mirrored for the left half. The inner edge passes under the mouth and outside the eyes; keep both edges
        # inside the head's front silhouette (x <= 0.47 W) or the projection misses and the strip spikes.
        IN = fh.get('inner', [(0.0, -0.40), (0.10, -0.39), (0.17, -0.33), (0.22, -0.22), (0.30, -0.13), (0.37, -0.05), (0.41, 0.03)])
        OUT = fh.get('outer', [(0.0, -0.58), (0.20, -0.54), (0.33, -0.45), (0.42, -0.31), (0.46, -0.16), (0.47, -0.03), (0.46, 0.07)])
        assert len(IN) == len(OUT), 'beard: inner and outer need the same number of points'
        top = [(-x * W, z * W) for x, z in reversed(IN[1:])] + [(x * W, z * W) for x, z in IN]
        bot = [(-x * W, z * W) for x, z in reversed(OUT[1:])] + [(x * W, z * W) for x, z in OUT]
        hm = look.mat(f'{self.name}_beard', C(fh.get('color', '#C2571E')), rough=0.85, brush=0.14, grain=0.7, grain_scale=220, paint=0.16, paint_scale=12)
        head = self.parts['head']; hd = self.spec['head']; hw, hdp, hh, egg = hd['w'], hd['d'], hd['h'], hd.get('egg', 0.06)
        def surf(x, z, off):
            # the front surface of the egg head at (x, z), exactly (no raycast: projected decals spike near the silhouette)
            zn = max(-0.5, min(0.5, z / hh)); f = 1.0 - 2 * egg * zn
            q = 1 - (x / (hw * f / 2)) ** 2 - (z / (hh / 2)) ** 2
            q = max(q, 0.0); y = -(hdp * f / 2) * math.sqrt(q)
            n = Vector((2 * x / (hw * f / 2) ** 2, 2 * y / (hdp * f / 2) ** 2, 2 * z / (hh / 2) ** 2)).normalized()
            return Vector((x, y, z)) + n * off
        bm = bmesh.new(); cols, rows_ = len(top), 7; grid = []
        for (xt, zt), (xb, zb) in zip(top, bot):
            grid.append([bm.verts.new(surf(xt + (xb - xt) * r / (rows_ - 1), zt + (zb - zt) * r / (rows_ - 1), 0.003)) for r in range(rows_)])
        for i in range(cols - 1):
            for r in range(rows_ - 1): bm.faces.new((grid[i][r], grid[i + 1][r], grid[i + 1][r + 1], grid[i][r + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f_ in bm.faces:
            if f_.normal.y > 0: f_.normal_flip()
        bd = mesh_obj(f'{self.name}_beardd', bm, [hm], smooth=True, coll=coll); bd.parent = head
        so = bd.modifiers.new('depth', 'SOLIDIFY'); so.thickness = fh.get('depth', 0.12) * W; so.offset = 1.0; so.use_even_offset = True
        subsurf(bd, 2, 2); look.outline(bd, 0.005); bd.visible_shadow = True
        hz = fh.get('hang_z', -0.62) * W; hs = fh.get('hang', (0.78, 0.48, 0.55))
        hg = ellipsoid(f'{self.name}_beardh', (hs[0] * W, hs[1] * W, hs[2] * W), (0, 0, 0), [hm], seg=(40, 24), coll=coll)
        bmh = bmesh.new(); bmh.from_mesh(hg.data)
        for v in bmh.verts:
            u = max(0.0, -v.co.z / (hs[2] * W * 0.5))                              # 0 at the middle -> 1 at the bottom: a soft point
            v.co.x *= 1 - 0.55 * u ** 1.4; v.co.y *= 1 - 0.35 * u ** 1.4
            v.co.x *= 1 + 0.06 * math.sin(9 * math.atan2(v.co.y, v.co.x) + v.co.z * 40)   # tufty edge
        bmh.to_mesh(hg.data); bmh.free()
        hg.parent = head; hg.location = (0, fh.get('hang_y', -0.30) * W, hz); subsurf(hg, 1, 2); look.outline(hg, 0.005)
        self.parts['moustache_decal'] = bd; self.parts['beard_hang'] = hg

    # ---- curly tuft poking out in front of the brim
    def _wig(self, hair):
        """a powdered tie-wig (Georgian): a soft cap over the crown and back of the head, `rolls` fat horizontal curls over
        each ear, and a short queue tied with a black bow at the nape. Fitted to the head implicit; values in W."""
        C = look.hexc; W = self.W; coll = self.coll; hs = self.hshape; hz = self.hz; h, d = hs.h, hs.d
        hm = look.mat(f'{self.name}_wig', C(hair.get('color', '#F1EEE7')), rough=0.9, brush=0.10, grain=0.9, grain_scale=140, paint=0.10)
        bowm = look.mat(f'{self.name}_wigbow', C(hair.get('bow', '#1E1B22')), rough=0.6, brush=0.04)
        back = hair.get('back', 0.25)
        mass = ellipsoid(f'{self.name}_wigmass', (W * 1.02, d * 0.88, h * 0.66), (0, d * back, hz - h * 0.06 + h * hair.get('lift', 0.0)), [hm], seg=(48, 28), egg=0.05, coll=coll)
        objs = [mass]
        if hair.get('pouf'):   # a hatless powdered wig: a tall pouf on the crown (no bald top)
            objs.append(ellipsoid(f'{self.name}_wigpouf', (W * 0.92, d * 0.86, h * 0.62), (0, d * 0.06, hz + h * 0.40), [hm], seg=(40, 24), egg=0.10, coll=coll))
        n = hair.get('rolls', 2); rr = hair.get('roll_r', 0.085) * W
        for s in (-1, 1):
            for k in range(n):
                z = hz - h * hair.get('roll_z', 0.06) - k * rr * 1.75
                ys = (-d * hair.get('roll_front', 0.04), d * hair.get('roll_back', 0.30))   # short sausages front-to-back (long ones read as ear-muffs)
                xr = max(hs.radius(0 if s > 0 else math.pi, z - hz), W * 0.45) + rr * 0.55
                objs.append(capsule(f'{self.name}_roll{s}{k}', (s * xr, (ys[0] + ys[1]) / 2, z), ys[1] - ys[0], rr, axis=(0, 1, 0), mats=[hm], coll=coll))
        q0 = Vector((0, d * 0.50, hz - h * 0.12)); q1 = Vector((0, d * 0.60, hz - h * 0.50))
        objs.append(tube(f'{self.name}_queue', q0, q1, W * 0.075, W * 0.045, 6, 12, [hm], coll=coll))
        for s in (-1, 1):
            objs.append(ellipsoid(f'{self.name}_bow{s}', (W * 0.16, W * 0.05, W * 0.10), (s * W * 0.07, d * 0.56, hz - h * 0.16), [bowm], seg=(16, 10), coll=coll))
        objs.append(ellipsoid(f'{self.name}_knot', (W * 0.06, W * 0.06, W * 0.06), (0, d * 0.57, hz - h * 0.16), [bowm], seg=(12, 8), coll=coll))
        wig = join(objs, f'{self.name}_hair'); subsurf(wig, 1, 1); look.outline(wig, 0.005); self.parts['hair'] = wig

    def _crop(self, hair):
        """short hair: a shell over the crown cut at a hairline (high at the front, sideburns at the sides, low at the back),
        plus a swept-up quiff at the front. Values in W / head height."""
        C = look.hexc; W = self.W; coll = self.coll; hs = self.hshape; hz = self.hz; h, d = hs.h, hs.d
        hm = look.mat(f'{self.name}_hair', C(hair['color']), rough=0.85, brush=0.08, grain=0.5, grain_scale=200, paint=0.07, paint_scale=12)
        g = hair.get('grow', 0.05)
        shell = ellipsoid(f'{self.name}_hairshell', (W * (1 + g), d * (1 + g), h * (1 + g * 0.9)), (0, 0, h * hair.get('lift', 0.01)), [hm], seg=(96, 64), egg=hs.egg, coll=coll)
        f0, s0, b0 = hair.get('front', 0.20), hair.get('side', -0.10), hair.get('back', -0.30)
        a_ = (f0 + 2 * s0 + b0) / 4.0; b_ = (f0 - b0) / 2.0; c_ = (f0 + b0) / 2.0 - a_
        bm = bmesh.new(); bm.from_mesh(shell.data)
        kill = []
        for f_ in bm.faces:
            c = f_.calc_center_median(); az = math.atan2(c.x, -c.y)
            if c.z / h < a_ + b_ * math.cos(az) + c_ * math.cos(2 * az): kill.append(f_)
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        # smooth hairline: slide every boundary vertex onto the cut curve, along the shell's own surface
        Wx, Dy, Hz = W * (1 + g) / 2, d * (1 + g) / 2, h * (1 + g * 0.9) / 2; zoff = h * hair.get('lift', 0.01)
        for v in bm.verts:
            if not v.is_boundary: continue
            az = math.atan2(v.co.x, -v.co.y); zc = (a_ + b_ * math.cos(az) + c_ * math.cos(2 * az)) * h
            zl = zc - zoff; zn = max(-0.999, min(0.999, zl / Hz)); f = 1 - 2 * hs.egg * (zl / (2 * Hz))
            rr = math.sqrt(max(0.0, 1 - zn * zn))
            v.co.x = Wx * f * rr * math.sin(az); v.co.y = -Dy * f * rr * math.cos(az); v.co.z = zc
        bm.to_mesh(shell.data); bm.free()
        so = shell.modifiers.new('thick', 'SOLIDIFY'); so.thickness = W * hair.get('thick', 0.035); so.offset = -1.0; so.use_even_offset = True
        q = hair.get('quiff', (0.74, 0.40, 0.25)); qz = hair.get('quiff_z', 0.40); qy = hair.get('quiff_y', -0.14)
        quiff = ellipsoid(f'{self.name}_quiff', (q[0] * W, q[1] * W, q[2] * W), (0, 0, 0), [hm], seg=(40, 24), coll=coll)
        quiff.location = (hair.get('quiff_x', 0.03) * W, qy * W, qz * h); quiff.rotation_euler = (math.radians(hair.get('quiff_pitch', -16)), 0, math.radians(hair.get('quiff_yaw', 6)))
        bpy.context.view_layer.update(); quiff.data.transform(quiff.matrix_basis); quiff.matrix_basis.identity()
        hr = join([shell, quiff], f'{self.name}_hair'); hr.location = (0, 0, hz)
        bpy.context.view_layer.update(); hr.data.transform(hr.matrix_basis); hr.matrix_basis.identity()
        subsurf(hr, 1, 2); look.outline(hr, 0.005); hr.visible_shadow = True; self.parts['hair'] = hr

    def _glasses(self, gl):
        """thin wire-frame glasses: two rounded-rectangle rims a little in front of the face, a bridge, and temples running
        round the head to behind the ears. Values in W from the head centre."""
        C = look.hexc; W = self.W; coll = self.coll; hd = self.spec['head']; hw, hdp, hh, egg = hd['w'], hd['d'], hd['h'], hd.get('egg', 0.06)
        off = gl.get('off', 0.045) * W; wr = gl.get('wire', 0.0042)
        def surf(x, z, o):
            zn = max(-0.5, min(0.5, z / hh)); f = 1.0 - 2 * egg * zn
            q = max(1 - (x / (hw * f / 2)) ** 2 - (z / (hh / 2)) ** 2, 0.0); y = -(hdp * f / 2) * math.sqrt(q)
            n = Vector((2 * x / (hw * f / 2) ** 2, 2 * y / (hdp * f / 2) ** 2, 2 * z / (hh / 2) ** 2)).normalized()
            return Vector((x, y, z)) + n * o
        cx, cz = gl.get('x', 0.19) * W, gl.get('z', -0.02) * W; lw, lh = gl.get('lw', 0.185) * W, gl.get('lh', 0.11) * W; rc = gl.get('corner', 0.045) * W
        mt = look.mat(f'{self.name}_glasses', C(gl.get('color', '#B9BEC8')), rough=0.38, metal=0.75, brush=0.0, grain=0.0)
        polys = []
        def rrect(xc):
            pts = []
            for k, (sx, sz, a0) in enumerate(((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270))):
                ccx, ccz = xc + sx * (lw - rc), cz + sz * (lh - rc)
                for j in range(9):
                    a = math.radians(a0 + 90 * j / 8); pts.append((ccx + rc * math.cos(a), ccz + rc * math.sin(a)))
            return pts
        for s in (-1, 1):
            polys.append(([surf(x, z, off) for x, z in rrect(s * cx)], True))
        zb = cz + lh * 0.45
        polys.append(([surf(x, zb + 0.02 * W * math.cos(math.pi * x / (2 * (cx - lw) + 1e-6)), off) for x in [-(cx - lw) + 2 * (cx - lw) * i / 8 for i in range(9)]], False))
        hs = self.hshape
        for s in (-1, 1):
            p0 = surf(s * (cx + lw), zb, off); th0 = math.atan2(p0.y, p0.x); th1 = math.radians(gl.get('temple_end', 18)) if s > 0 else -math.pi - math.radians(gl.get('temple_end', 18))
            pts = [p0]
            for i in range(1, 13):
                t = i / 12; th = th0 + (th1 - th0) * t; r = hs.radius(th, zb) + off * (1 - 0.6 * t)
                pts.append(Vector((r * math.cos(th), r * math.sin(th), zb - 0.02 * W * t)))
            polys.append((pts, False))
        cu = bpy.data.curves.new(f'{self.name}_glassescu', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = wr; cu.bevel_resolution = 3; cu.use_fill_caps = True
        for pts, cyc in polys:
            sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
            for i, p in enumerate(pts): sp.points[i].co = (p.x, p.y, p.z, 1)
            sp.use_cyclic_u = cyc
        co = bpy.data.objects.new(f'{self.name}_glassestmp', cu); coll.objects.link(co)
        dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(co.evaluated_get(dg))
        bpy.data.objects.remove(co); bpy.data.curves.remove(cu)
        go = bpy.data.objects.new(f'{self.name}_glasses', me); coll.objects.link(go); me.materials.append(mt)
        for p in me.polygons: p.use_smooth = True
        go.location = (0, 0, self.hz); look.outline(go, gl.get('ink', 0.0016)); self.parts['glasses'] = go

    def _tuft(self, hair):
        C = look.hexc; W = self.W; coll = self.coll; hf = getattr(self, 'hat_frame', None)
        hm = look.mat(f'{self.name}_hair', C(hair['color']), rough=0.85, brush=0.12, grain=0.5)
        blobs = hair.get('blobs', [(0.00, 0.035, 0.062), (-0.085, 0.045, 0.056), (0.09, 0.05, 0.055), (-0.165, 0.075, 0.045),
                                   (0.17, 0.08, 0.044), (-0.04, 0.105, 0.052), (0.06, 0.11, 0.05), (-0.115, 0.125, 0.04),
                                   (0.125, 0.13, 0.038), (-0.035, -0.02, 0.045), (0.045, -0.015, 0.042), (0.0, 0.155, 0.036)])
        objs = []
        for i, (dx, dz, r) in enumerate(blobs):
            x, z, r = dx * W, dz * W, r * W
            if hf:
                zf = hf['zb'] + z
                if zf < hf['zb']: R0 = self.hshape.radius(1.5 * math.pi, zf, hf['R']) + r * 0.25
                elif zf <= hf['zb'] + hf['bh']: R0 = hf['rf'](1.5 * math.pi) + hf['th'] * 1.05
                else:
                    s = min(1.0, (zf - hf['zt']) / hf['Hd']); R0 = (hf['rf'](1.5 * math.pi) + hf['th'] * 0.62) * math.sqrt(max(0.0, 1 - s * s))
                y = -math.sqrt(max(0.0, R0 * R0 - x * x)) - r * 0.35
                p = hf['R'] @ Vector((x, y, zf)) + Vector((0, 0, self.hz))
            else:
                p = Vector((x, -self.hshape.d * 0.45, self.hz + self.hshape.h * 0.3 + z))
            objs.append(ellipsoid(f'{self.name}_curl{i}', (r * 2.1, r * 1.15, r * 1.85), p, [hm], seg=(20, 12), coll=coll))
        tuft = join(objs, f'{self.name}_hair'); subsurf(tuft, 1, 1); look.outline(tuft, 0.004); self.parts['hair'] = tuft
