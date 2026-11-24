"""fx.py: moving effects for a set (steam, smoke, volume smoke fills, snow, sparks). Copy-and-use in film.py: `import fx`.
First built for the pineapple pit (2.2.0-rc3), where steam was the film's water. Scalar vector-math ops return the VALUE
output (`_vmath`: the Vector output of DISTANCE/LENGTH is (0,0,0), which once zeroed every flake and puff, lesson 74).

steam(name, p0, p1, ...)   a column of soft puffs rising from a vent line p0->p1: each puff is born at the vent, rises
                           with ease-out, curls on a widening helix, drifts downwind, grows and thins out to nothing,
                           then is reborn somewhere else on the vent. Geometry nodes (deterministic per frame, no keys),
                           alpha from an instance attribute 'life'. Keyable strength: obj['amp'] (0..1.5).
snowfall(name, box, ...)   flakes falling through a box with a sideways flutter (geometry nodes, wraps in z).
smoke(...)                 steam() with grey smoke colouring (a chimney).
smoke_fill(..., volume=True) + smoke_vol_mat2(...)   a room FILLING with charcoal volume smoke (lesson 76).
sparks(...)                a short burst of hot sparks (key obj['amp']).
Near-lens fade: each steam/snow tree has an Object Info node named CAMINFO; point it at the scene camera after building:
    for ng in bpy.data.node_groups: n = ng.nodes.get('CAMINFO'); n and setattr(n.inputs['Object'], 'default_value', cam)
"""
import bpy, math
from mathutils import Vector
from toykit import look

C = look.hexc


def _gn(name):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput')
    return ng, gi, go


def _math(ng, op, a=None, b=None, c=None):
    n = ng.nodes.new('ShaderNodeMath'); n.operation = op
    for i, v in enumerate((a, b, c)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: ng.links.new(v, n.inputs[i])
    return n.outputs[0]


def _vmath(ng, op, a=None, b=None, scale=None):
    n = ng.nodes.new('ShaderNodeVectorMath'); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (tuple, list, Vector)): n.inputs[i].default_value = tuple(v)
        else: ng.links.new(v, n.inputs[i])
    if scale is not None:
        s = n.inputs.get('Scale') or n.inputs[3]
        if isinstance(scale, (int, float)): s.default_value = scale
        else: ng.links.new(scale, s)
    return n.outputs['Value'] if op in ('DOT_PRODUCT', 'DISTANCE', 'LENGTH') else n.outputs['Vector']   # scalar ops: the VECTOR output is (0,0,0) (round 2's near-lens fade zeroed every flake and steam puff)


def _rand(ng, kind, mn, mx, idsock, seed):
    n = ng.nodes.new('FunctionNodeRandomValue'); n.data_type = kind
    want = 'VECTOR' if kind == 'FLOAT_VECTOR' else 'VALUE'
    ins = [s for s in n.inputs if s.name in ('Min', 'Max') and s.type == want and s.enabled]
    if len(ins) < 2: ins = [s for s in n.inputs if s.name in ('Min', 'Max') and s.type == want]
    ins[0].default_value = tuple(mn) if kind == 'FLOAT_VECTOR' else float(mn)
    ins[1].default_value = tuple(mx) if kind == 'FLOAT_VECTOR' else float(mx)
    outs = [s for s in n.outputs if s.type == want and s.enabled] or [s for s in n.outputs if s.type == want]
    out = outs[0]
    ng.links.new(idsock, n.inputs['ID']); n.inputs['Seed'].default_value = seed
    return out


def _combine(ng, x, y, z):
    n = ng.nodes.new('ShaderNodeCombineXYZ')
    for i, v in enumerate((x, y, z)):
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: ng.links.new(v, n.inputs[i])
    return n.outputs[0]


def puff_mat(name, color=(1.0, 0.98, 0.95), shade=(0.78, 0.80, 0.86), emit=0.75, density=0.30, edge=3.0, noise_scale=2.2, diffuse=0.35):
    """soft, lit puff: diffuse (takes the scene's light) + a little emission, alpha = life envelope x soft sphere edge x
    an evolving 4D noise (the puff breaks into wisps as it thins). Blended, backface-culled, overlap ON (lesson 39)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    at = N('ShaderNodeAttribute'); at.attribute_type = 'INSTANCER'; at.attribute_name = 'alpha'
    lw = N('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    soft = N('ShaderNodeMath'); soft.operation = 'SUBTRACT'; soft.inputs[0].default_value = 1.0; L(lw.outputs['Facing'], soft.inputs[1])
    sp = N('ShaderNodeMath'); sp.operation = 'POWER'; L(soft.outputs[0], sp.inputs[0]); sp.inputs[1].default_value = edge
    tc = N('ShaderNodeTexCoord'); tm = N('ShaderNodeAttribute'); tm.attribute_type = 'INSTANCER'; tm.attribute_name = 'life'
    nz = N('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = noise_scale; nz.inputs['Detail'].default_value = 3.0
    nz.inputs['Roughness'].default_value = 0.55
    L(tc.outputs['Object'], nz.inputs['Vector']); wmul = N('ShaderNodeMath'); wmul.operation = 'MULTIPLY'; wmul.inputs[1].default_value = 3.0
    L(tm.outputs['Fac'], wmul.inputs[0]); L(wmul.outputs[0], nz.inputs['W'])
    nr = N('ShaderNodeMapRange'); nr.inputs['From Min'].default_value = 0.25; nr.inputs['From Max'].default_value = 0.75
    nr.inputs['To Min'].default_value = 0.25; nr.inputs['To Max'].default_value = 1.0
    L(nz.outputs['Fac'], nr.inputs['Value'])
    a1 = N('ShaderNodeMath'); a1.operation = 'MULTIPLY'; L(sp.outputs[0], a1.inputs[0]); L(nr.outputs[0], a1.inputs[1])
    a2 = N('ShaderNodeMath'); a2.operation = 'MULTIPLY'; L(a1.outputs[0], a2.inputs[0]); L(at.outputs['Fac'], a2.inputs[1])
    a3 = N('ShaderNodeMath'); a3.operation = 'MULTIPLY'; L(a2.outputs[0], a3.inputs[0]); a3.inputs[1].default_value = density
    a3.use_clamp = True
    df = N('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = (*[c * diffuse for c in shade], 1)
    em = N('ShaderNodeEmission'); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = emit
    ad = N('ShaderNodeAddShader'); L(df.outputs[0], ad.inputs[0]); L(em.outputs[0], ad.inputs[1])
    tr = N('ShaderNodeBsdfTransparent'); mx = N('ShaderNodeMixShader')
    L(a3.outputs[0], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(ad.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs[0])
    for k, v in (('surface_render_method', 'BLENDED'), ('use_backface_culling', True), ('use_transparency_overlap', True)):
        try: setattr(m, k, v)
        except Exception: pass
    return m


def steam(name, p0, p1, n=90, life=2.8, rise=0.95, curl=0.12, turns=0.8, wind=(0.14, 0.06, 0.0), r0=0.06, r1=0.30,
          amp=1.0, mat=None, c=None, seed=0, fps=30.0, peak=0.14):
    """n puffs alive at once on the vent line p0 -> p1 (world). life: seconds a puff lives; rise: metres it climbs;
    curl: helix radius at the end of its life; wind: drift (m) over its life; r0 -> r1: puff radius at birth -> death.
    Keyable strength obj['amp'] (multiplies alpha; 0 = no steam). Returns the object."""
    me = bpy.data.meshes.new(name + '_m'); me.from_pydata([(0, 0, 0)], [], []); o = bpy.data.objects.new(name, me)
    (c or bpy.context.scene.collection).objects.link(o); o['amp'] = float(amp); o['wind'] = 1.0
    ng, gi, go = _gn(name + '_gn'); L = ng.links.new
    windv = ng.nodes.new('ShaderNodeValue'); windv.name = 'WIND'; windv.outputs[0].default_value = 1.0
    pts = ng.nodes.new('GeometryNodePoints'); pts.inputs['Count'].default_value = n
    idx = ng.nodes.new('GeometryNodeInputIndex').outputs[0]
    t = ng.nodes.new('GeometryNodeInputSceneTime').outputs['Frame']
    sec = _math(ng, 'DIVIDE', t, fps)
    ph = _rand(ng, 'FLOAT', 0.0, 1.0, idx, seed + 1)                                  # each puff's phase in its cycle
    u = _math(ng, 'ADD', _math(ng, 'DIVIDE', sec, life), ph)                          # cycles since start
    cyc = _math(ng, 'FLOOR', u); lf = _math(ng, 'FRACT', u)                            # which cycle, and life 0..1
    rid = _math(ng, 'ADD', _math(ng, 'MULTIPLY', cyc, n), idx)                        # a fresh random id every rebirth
    along = _rand(ng, 'FLOAT', 0.0, 1.0, rid, seed + 2)
    jit = _rand(ng, 'FLOAT_VECTOR', (-0.05, -0.03, 0.0), (0.05, 0.03, 0.02), rid, seed + 3)
    a0 = _rand(ng, 'FLOAT', 0.0, 6.2832, rid, seed + 4)                               # helix start angle
    spd = _rand(ng, 'FLOAT', 0.75, 1.25, rid, seed + 5)                               # some puffs climb faster
    P0, P1 = Vector(p0), Vector(p1)
    base = _vmath(ng, 'ADD', _vmath(ng, 'SCALE', tuple(P1 - P0), None, along), tuple(P0))
    base = _vmath(ng, 'ADD', base, jit)
    ease = _math(ng, 'SUBTRACT', 1.0, _math(ng, 'POWER', _math(ng, 'SUBTRACT', 1.0, lf), 1.7))   # fast off the vent, slowing
    z = _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', ease, rise), spd)
    ang = _math(ng, 'ADD', a0, _math(ng, 'MULTIPLY', lf, 6.2832 * turns))
    rad = _math(ng, 'MULTIPLY', curl, _math(ng, 'POWER', lf, 0.8))
    hx = _math(ng, 'MULTIPLY', rad, _math(ng, 'COSINE', ang)); hy = _math(ng, 'MULTIPLY', rad, _math(ng, 'SINE', ang))
    w15 = _math(ng, 'POWER', lf, 1.5)
    off = _combine(ng, _math(ng, 'ADD', hx, _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', w15, wind[0]), windv.outputs[0])), _math(ng, 'ADD', hy, _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', w15, wind[1]), windv.outputs[0])),
                   _math(ng, 'ADD', z, _math(ng, 'MULTIPLY', w15, wind[2])))
    pos = _vmath(ng, 'ADD', base, off)
    L(pos, pts.inputs['Position'])
    ico = ng.nodes.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = 1.0; ico.inputs['Subdivisions'].default_value = 3
    smo = ng.nodes.new('GeometryNodeSetShadeSmooth'); L(ico.outputs[0], smo.inputs['Geometry'])
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints'); L(pts.outputs[0], iop.inputs['Points']); L(smo.outputs[0], iop.inputs['Instance'])
    sc_ = _math(ng, 'ADD', r0, _math(ng, 'MULTIPLY', r1 - r0, _math(ng, 'POWER', lf, 0.65)))
    sq = _combine(ng, sc_, _math(ng, 'MULTIPLY', sc_, 0.85), _math(ng, 'MULTIPLY', sc_, 1.12))   # a touch taller than wide
    L(sq, iop.inputs['Scale'])
    rot = _combine(ng, _math(ng, 'MULTIPLY', a0, 0.3), 0.0, _math(ng, 'ADD', a0, _math(ng, 'MULTIPLY', lf, 2.0)))
    L(rot, iop.inputs['Rotation'])
    # alpha envelope: quick fade-in off the vent, long thinning tail; x the object's keyable 'amp'
    fin = _math(ng, 'MINIMUM', 1.0, _math(ng, 'DIVIDE', lf, peak))
    tail = _math(ng, 'POWER', _math(ng, 'SUBTRACT', 1.0, lf), 1.35)
    env = _math(ng, 'MULTIPLY', fin, tail)
    ob = ng.nodes.new('GeometryNodeObjectInfo'); ob.inputs['Object'].default_value = o
    amp_ = ng.nodes.new('GeometryNodeInputNamedAttribute')                           # placeholder (object prop read via driver below)
    ampv = ng.nodes.new('ShaderNodeValue'); ampv.name = 'AMP'; ampv.outputs[0].default_value = float(amp)
    cami = ng.nodes.new('GeometryNodeObjectInfo'); cami.name = 'CAMINFO'                 # set to the scene camera by film.py: puffs fade within ~0.9 m of the lens
    dcam = _vmath(ng, 'DISTANCE', pos, cami.outputs['Location'])
    alpha = _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', env, ampv.outputs[0]), _math(ng, 'MINIMUM', 1.0, _math(ng, 'MAXIMUM', 0.0, _math(ng, 'DIVIDE', _math(ng, 'SUBTRACT', dcam, 0.5), 0.45))))
    st = ng.nodes.new('GeometryNodeStoreNamedAttribute'); st.data_type = 'FLOAT'; st.domain = 'INSTANCE'; st.inputs['Name'].default_value = 'alpha'
    L(iop.outputs[0], st.inputs['Geometry']); L(alpha, st.inputs['Value'])
    st2 = ng.nodes.new('GeometryNodeStoreNamedAttribute'); st2.data_type = 'FLOAT'; st2.domain = 'INSTANCE'; st2.inputs['Name'].default_value = 'life'
    L(st.outputs[0], st2.inputs['Geometry']); L(lf, st2.inputs['Value'])
    sm = ng.nodes.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = mat or puff_mat('FX_steam')
    L(st2.outputs[0], sm.inputs['Geometry']); L(sm.outputs[0], go.inputs[0])
    ng.nodes.remove(amp_); ng.nodes.remove(ob)
    md = o.modifiers.new('steam', 'NODES'); md.node_group = ng
    # obj['amp'] drives the AMP value node, so strength can be keyed per shot (o['amp'] = x; o.keyframe_insert('["amp"]', frame=f))
    fc = ampv.outputs[0].driver_add('default_value'); fc.driver.type = 'AVERAGE'
    v = fc.driver.variables.new(); v.name = 'amp'; v.type = 'SINGLE_PROP'; v.targets[0].id = o; v.targets[0].data_path = '["amp"]'
    fw_ = windv.outputs[0].driver_add('default_value'); fw_.driver.type = 'AVERAGE'
    vw = fw_.driver.variables.new(); vw.name = 'wind'; vw.type = 'SINGLE_PROP'; vw.targets[0].id = o; vw.targets[0].data_path = '["wind"]'
    o.visible_shadow = False
    return o


def smoke(name, p0, p1, c=None, seed=0, **kw):
    sm = puff_mat('FX_smoke', color=(0.55, 0.55, 0.58), shade=(0.42, 0.42, 0.46), emit=0.05, density=0.6, edge=1.8)
    args = dict(n=40, life=3.2, rise=1.6, curl=0.12, turns=0.5, wind=(0.55, 0.15, 0.0), r0=0.05, r1=0.28)
    args.update(kw); return steam(name, p0, p1, mat=sm, c=c, seed=seed, **args)


def snow_mat():
    m = bpy.data.materials.get('FX_snowflake')
    if m: return m
    m = look.mat('FX_snowflake', (0.95, 0.97, 1.0), rough=0.9, brush=0.0, grain=0.0, emission=((0.82, 0.88, 1.0), 0.35))
    return m


def snowfall(name, center, size, n=900, speed=0.55, flutter=0.06, r=0.012, c=None, seed=0, fps=30.0, holes=()):
    """n flakes in a box (center, size), falling at `speed` m/s with a sideways flutter; wraps from bottom to top."""
    me = bpy.data.meshes.new(name + '_m'); me.from_pydata([(0, 0, 0)], [], []); o = bpy.data.objects.new(name, me)
    (c or bpy.context.scene.collection).objects.link(o)
    ng, gi, go = _gn(name + '_gn'); L = ng.links.new
    pts = ng.nodes.new('GeometryNodePoints'); pts.inputs['Count'].default_value = n
    idx = ng.nodes.new('GeometryNodeInputIndex').outputs[0]
    t = ng.nodes.new('GeometryNodeInputSceneTime').outputs['Frame']; sec = _math(ng, 'DIVIDE', t, fps)
    cx, cy, cz = center; sx, sy, sz = size
    p = _rand(ng, 'FLOAT_VECTOR', (cx - sx / 2, cy - sy / 2, 0.0), (cx + sx / 2, cy + sy / 2, sz), idx, seed)
    sep = ng.nodes.new('ShaderNodeSeparateXYZ'); L(p, sep.inputs[0])
    sp = _rand(ng, 'FLOAT', 0.7, 1.3, idx, seed + 7)
    fall = _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', sec, speed), sp)
    zz = _math(ng, 'ADD', _math(ng, 'FLOORED_MODULO', _math(ng, 'SUBTRACT', sep.outputs[2], fall), sz), cz - sz / 2)
    ph = _rand(ng, 'FLOAT', 0.0, 6.28, idx, seed + 9)
    fx = _math(ng, 'MULTIPLY', flutter, _math(ng, 'SINE', _math(ng, 'ADD', ph, _math(ng, 'MULTIPLY', sec, 2.1))))
    fy = _math(ng, 'MULTIPLY', flutter * 0.6, _math(ng, 'COSINE', _math(ng, 'ADD', ph, _math(ng, 'MULTIPLY', sec, 1.7))))
    pos = _combine(ng, _math(ng, 'ADD', sep.outputs[0], fx), _math(ng, 'ADD', sep.outputs[1], fy), zz)
    L(pos, pts.inputs['Position'])
    ico = ng.nodes.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = r * 0.75; ico.inputs['Subdivisions'].default_value = 2
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints'); L(pts.outputs[0], iop.inputs['Points']); L(ico.outputs[0], iop.inputs['Instance'])
    ssz = _rand(ng, 'FLOAT', 0.6, 1.4, idx, seed + 11)
    cami = ng.nodes.new('GeometryNodeObjectInfo'); cami.name = 'CAMINFO'                 # set to the scene camera by film.py: no flake within ~1.5 m of the lens
    dcam = _vmath(ng, 'DISTANCE', _combine(ng, _math(ng, 'ADD', sep.outputs[0], fx), sep.outputs[1], zz), cami.outputs['Location'])
    ssz = _math(ng, 'MULTIPLY', ssz, _math(ng, 'MINIMUM', 1.0, _math(ng, 'MAXIMUM', 0.0, _math(ng, 'DIVIDE', _math(ng, 'SUBTRACT', dcam, 0.8), 0.7))))
    for (hx0, hx1, hy0, hy1, hz1) in holes:                     # a flake inside a hole (a roofed glasshouse) shrinks to nothing
        inside = _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', _math(ng, 'GREATER_THAN', pos_x := _math(ng, 'ADD', sep.outputs[0], fx), hx0), _math(ng, 'LESS_THAN', pos_x, hx1)),
                       _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', _math(ng, 'GREATER_THAN', sep.outputs[1], hy0), _math(ng, 'LESS_THAN', sep.outputs[1], hy1)), _math(ng, 'LESS_THAN', zz, hz1)))
        ssz = _math(ng, 'MULTIPLY', ssz, _math(ng, 'SUBTRACT', 1.0, inside))
    L(ssz, iop.inputs['Scale'])
    sm = ng.nodes.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = snow_mat()
    L(iop.outputs[0], sm.inputs['Geometry']); L(sm.outputs[0], go.inputs[0])
    md = o.modifiers.new('snow', 'NODES'); md.node_group = ng; o.visible_shadow = False
    return o


def smoke_fill(name, src, box, f0, n=170, fill_s=1.5, travel=(0.8, 1.4), r0=0.06, r1=(0.26, 0.38), alpha=0.55, roof=None,
               mat=None, c=None, seed=0, fps=30.0, churn=0.07, amp=1.0, keep_out=None, volume=False, voxel=0.035, vmat=None):
    """smoke POURING out of `src` from frame f0 and FILLING a room (parent note: it must visibly fill the glasshouse,
    billowing and spreading, never a static sprite). box = (x0, x1, y0, y1, z0, z1). Every puff has its own resting spot,
    biased up under the roof; it is born at the source when the fill front reaches it (front = 45% distance from the
    source + 55% depth below the roof, over fill_s seconds, so the room fills roof-first and downward), billows there
    with a fast rise and a slower spread, then keeps churning on a slow wobble and grows. roof = (ridge_y, half_depth,
    eave_z, ridge_z) clamps spots under a span roof. keep_out = (x, y, z, r): no resting spot inside that sphere (camera).
    obj['amp'] scales alpha (key it down for the next morning's lingering haze)."""
    me = bpy.data.meshes.new(name + '_m'); me.from_pydata([(0, 0, 0)], [], []); o = bpy.data.objects.new(name, me)
    (c or bpy.context.scene.collection).objects.link(o); o['amp'] = float(amp)
    ng, gi, go = _gn(name + '_gn'); L = ng.links.new
    pts = ng.nodes.new('GeometryNodePoints'); pts.inputs['Count'].default_value = n
    idx = ng.nodes.new('GeometryNodeInputIndex').outputs[0]
    t = ng.nodes.new('GeometryNodeInputSceneTime').outputs['Frame']
    x0, x1, y0, y1, z0, z1 = box; S = Vector(src)
    px = _rand(ng, 'FLOAT', x0, x1, idx, seed + 1); py = _rand(ng, 'FLOAT', y0, y1, idx, seed + 2)
    u = _rand(ng, 'FLOAT', 0.0, 1.0, idx, seed + 3)
    if roof:                                                                          # the ceiling over this (x, y): a span roof
        ry_, hd_, eave_, ridge_ = roof
        dy = _math(ng, 'DIVIDE', _math(ng, 'ABSOLUTE', _math(ng, 'SUBTRACT', py, ry_)), hd_)
        top = _math(ng, 'SUBTRACT', _math(ng, 'SUBTRACT', ridge_, _math(ng, 'MULTIPLY', ridge_ - eave_, dy)), 0.16)
        top = _math(ng, 'MINIMUM', top, z1)
    else: top = _math(ng, 'ADD', z1, 0.0)
    h = _math(ng, 'POWER', u, 1.35)                                                   # 0 = under the roof .. 1 = floor (few low)
    pz = _math(ng, 'SUBTRACT', top, _math(ng, 'MULTIPLY', h, _math(ng, 'SUBTRACT', top, z0)))
    if keep_out:                                                                      # push spots out of a sphere (the camera)
        kx, ky, kz, kr = keep_out
        d = _vmath(ng, 'SUBTRACT', _combine(ng, px, py, pz), (kx, ky, kz))
        dl = _vmath(ng, 'LENGTH', d)
        sc_ = _math(ng, 'MAXIMUM', 1.0, _math(ng, 'DIVIDE', kr, _math(ng, 'MAXIMUM', dl, 0.05)))
        P = _vmath(ng, 'ADD', (kx, ky, kz), _vmath(ng, 'SCALE', d, None, sc_))
    else: P = _combine(ng, px, py, pz)
    dmax = max((Vector((xx, yy, 0)) - Vector((S.x, S.y, 0))).length for xx in (x0, x1) for yy in (y0, y1))
    sepP = ng.nodes.new('ShaderNodeSeparateXYZ'); L(P, sepP.inputs[0])
    dxy = _vmath(ng, 'LENGTH', _vmath(ng, 'SUBTRACT', _combine(ng, sepP.outputs[0], sepP.outputs[1], 0.0), (S.x, S.y, 0.0)))
    q = _math(ng, 'ADD', _math(ng, 'MULTIPLY', _math(ng, 'DIVIDE', dxy, dmax), 0.45), _math(ng, 'MULTIPLY', h, 0.55))
    jit = _rand(ng, 'FLOAT', 0.0, 0.12, idx, seed + 4)
    birth = _math(ng, 'ADD', f0, _math(ng, 'MULTIPLY', _math(ng, 'ADD', _math(ng, 'MULTIPLY', q, fill_s), jit), fps))
    age = _math(ng, 'DIVIDE', _math(ng, 'SUBTRACT', t, birth), fps)                  # seconds since this puff left the stove
    born = _math(ng, 'GREATER_THAN', age, 0.0)
    trav = _rand(ng, 'FLOAT', travel[0], travel[1], idx, seed + 5)
    k = _math(ng, 'MINIMUM', 1.0, _math(ng, 'MAXIMUM', 0.0, _math(ng, 'DIVIDE', age, trav)))
    ez = _math(ng, 'SUBTRACT', 1.0, _math(ng, 'POWER', _math(ng, 'SUBTRACT', 1.0, k), 3.2))     # rises fast...
    exy = _math(ng, 'SUBTRACT', 1.0, _math(ng, 'POWER', _math(ng, 'SUBTRACT', 1.0, k), 1.5))    # ...spreads slower
    D = _vmath(ng, 'SUBTRACT', P, tuple(S)); sD = ng.nodes.new('ShaderNodeSeparateXYZ'); L(D, sD.inputs[0])
    a1 = _rand(ng, 'FLOAT', 0.0, 6.2832, idx, seed + 6); a2 = _rand(ng, 'FLOAT', 0.0, 6.2832, idx, seed + 7)
    wob = _math(ng, 'MULTIPLY', churn, _math(ng, 'MINIMUM', 1.0, _math(ng, 'MAXIMUM', 0.0, age)))
    wx = _math(ng, 'MULTIPLY', wob, _math(ng, 'SINE', _math(ng, 'ADD', a1, _math(ng, 'MULTIPLY', age, 1.3))))
    wy = _math(ng, 'MULTIPLY', wob, _math(ng, 'COSINE', _math(ng, 'ADD', a2, _math(ng, 'MULTIPLY', age, 1.1))))
    wz = _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', wob, 0.6), _math(ng, 'SINE', _math(ng, 'ADD', a2, _math(ng, 'MULTIPLY', age, 0.9))))
    pos = _vmath(ng, 'ADD', tuple(S), _combine(ng, _math(ng, 'ADD', _math(ng, 'MULTIPLY', sD.outputs[0], exy), wx),
                                               _math(ng, 'ADD', _math(ng, 'MULTIPLY', sD.outputs[1], exy), wy),
                                               _math(ng, 'ADD', _math(ng, 'MULTIPLY', sD.outputs[2], ez), wz)))
    L(pos, pts.inputs['Position'])
    ico = ng.nodes.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = 1.0; ico.inputs['Subdivisions'].default_value = 3
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints'); L(pts.outputs[0], iop.inputs['Points']); L(ico.outputs[0], iop.inputs['Instance'])
    rr = _rand(ng, 'FLOAT', r1[0], r1[1], idx, seed + 8)
    grow = _math(ng, 'POWER', _math(ng, 'MINIMUM', 1.0, _math(ng, 'MAXIMUM', 0.0, _math(ng, 'DIVIDE', age, _math(ng, 'ADD', trav, 1.0)))), 0.6)
    rad = _math(ng, 'MULTIPLY', born, _math(ng, 'ADD', r0, _math(ng, 'MULTIPLY', _math(ng, 'SUBTRACT', rr, r0), grow)))
    if volume:   # REAL smoke (parent G4): the puffs become a fog grid with a dark, absorbing Principled Volume (no emission)
        ptv = ng.nodes.new('GeometryNodePointsToVolume'); L(pts.outputs[0], ptv.inputs['Points'])
        for mode in ('Size', 'Voxel Size', 'VOXEL_SIZE'):
            try: ptv.inputs['Resolution Mode'].default_value = mode; break
            except Exception: pass
        ptv.inputs['Voxel Size'].default_value = voxel; ptv.inputs['Density'].default_value = 1.0; L(rad, ptv.inputs['Radius'])
        smv = ng.nodes.new('GeometryNodeSetMaterial'); smv.inputs['Material'].default_value = vmat or smoke_vol_mat()
        L(ptv.outputs[0], smv.inputs['Geometry']); L(smv.outputs[0], go.inputs[0])
        md = o.modifiers.new('fill', 'NODES'); md.node_group = ng; o.visible_shadow = False; o['phase'] = 0.0
        return o
    L(_combine(ng, _math(ng, 'MULTIPLY', rad, 1.15), rad, _math(ng, 'MULTIPLY', rad, 0.85)), iop.inputs['Scale'])   # flattened, wide
    L(_combine(ng, _math(ng, 'MULTIPLY', a1, 0.2), 0.0, _math(ng, 'ADD', a2, _math(ng, 'MULTIPLY', age, 0.22))), iop.inputs['Rotation'])
    fin = _math(ng, 'MINIMUM', 1.0, _math(ng, 'MAXIMUM', 0.0, _math(ng, 'DIVIDE', age, 0.35)))
    ampv = ng.nodes.new('ShaderNodeValue'); ampv.name = 'AMP'; ampv.outputs[0].default_value = float(amp)
    al = _math(ng, 'MULTIPLY', _math(ng, 'MULTIPLY', fin, alpha), ampv.outputs[0])
    st = ng.nodes.new('GeometryNodeStoreNamedAttribute'); st.data_type = 'FLOAT'; st.domain = 'INSTANCE'; st.inputs['Name'].default_value = 'alpha'
    L(iop.outputs[0], st.inputs['Geometry']); L(al, st.inputs['Value'])
    st2 = ng.nodes.new('GeometryNodeStoreNamedAttribute'); st2.data_type = 'FLOAT'; st2.domain = 'INSTANCE'; st2.inputs['Name'].default_value = 'life'
    L(st.outputs[0], st2.inputs['Geometry']); L(_math(ng, 'DIVIDE', _math(ng, 'MAXIMUM', age, 0.0), 6.0), st2.inputs['Value'])   # slow wisps
    sm = ng.nodes.new('GeometryNodeSetMaterial')
    sm.inputs['Material'].default_value = mat or puff_mat('FX_smokefill', color=(0.30, 0.29, 0.30), shade=(0.26, 0.25, 0.27), emit=0.10, density=0.95, edge=4.5, noise_scale=2.6, diffuse=0.14)
    L(st2.outputs[0], sm.inputs['Geometry']); L(sm.outputs[0], go.inputs[0])
    md = o.modifiers.new('fill', 'NODES'); md.node_group = ng
    fc = ampv.outputs[0].driver_add('default_value'); fc.driver.type = 'AVERAGE'
    v = fc.driver.variables.new(); v.name = 'amp'; v.type = 'SINGLE_PROP'; v.targets[0].id = o; v.targets[0].data_path = '["amp"]'
    o.visible_shadow = False
    return o


def smoke_vol_mat(name='FX_smokevol', color=(0.045, 0.04, 0.036), absorb=(0.010, 0.009, 0.008), density=26.0):
    """dark coal smoke as a VOLUME: low-albedo scattering, strong absorption, no emission; density = base x obj['amp'] x a
    4D noise that drifts with obj['phase'] (billows, not a uniform fog)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); pv = N('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = (*color, 1); pv.inputs['Absorption Color'].default_value = (*absorb, 1); pv.inputs['Emission Strength'].default_value = 0.0
    amp = N('ShaderNodeAttribute'); amp.attribute_type = 'OBJECT'; amp.attribute_name = 'amp'
    ph = N('ShaderNodeAttribute'); ph.attribute_type = 'OBJECT'; ph.attribute_name = 'phase'
    tc = N('ShaderNodeTexCoord'); nz = N('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.6; nz.inputs['Detail'].default_value = 3.0
    L(tc.outputs['Object'], nz.inputs['Vector']); L(ph.outputs['Fac'], nz.inputs['W'])
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.34; mr.inputs['From Max'].default_value = 0.70; mr.inputs['To Min'].default_value = 0.10; mr.inputs['To Max'].default_value = 1.35
    L(nz.outputs['Fac'], mr.inputs['Value'])
    d1 = N('ShaderNodeMath'); d1.operation = 'MULTIPLY'; L(amp.outputs['Fac'], d1.inputs[0]); d1.inputs[1].default_value = density
    d2 = N('ShaderNodeMath'); d2.operation = 'MULTIPLY'; L(d1.outputs[0], d2.inputs[0]); L(mr.outputs[0], d2.inputs[1])
    L(d2.outputs[0], pv.inputs['Density']); L(pv.outputs[0], out.inputs['Volume'])
    return m


def smoke_vol_mat2(name='FX_smokevol2', color=(0.03, 0.03, 0.03), absorb=(0.0, 0.0, 0.0), density=26.0, roof=None, floor=0.0, top_frac=0.30,
                   scale=3.0, detail=8.0):
    """CHARCOAL smoke volume (parent G4b): scatter ~0.03 and black absorption, so no lamp can tint it; density = base x
    obj['amp'] x a high-detail 4D noise (drifting with obj['phase']) x a soft falloff over the top `top_frac` of the room,
    measured under a span roof = (ridge_y, half_depth, eave_z, ridge_z), whose edge a second noise breaks up, so the top
    BILLOWS instead of filling the glasshouse as a flat-topped box. Object coords = world coords (the fill sits at the origin)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    def M(op, a, b=None):
        n = N('ShaderNodeMath'); n.operation = op
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    out = N('ShaderNodeOutputMaterial'); pv = N('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = (*color, 1); pv.inputs['Absorption Color'].default_value = (*absorb, 1); pv.inputs['Emission Strength'].default_value = 0.0
    amp = N('ShaderNodeAttribute'); amp.attribute_type = 'OBJECT'; amp.attribute_name = 'amp'
    ph = N('ShaderNodeAttribute'); ph.attribute_type = 'OBJECT'; ph.attribute_name = 'phase'
    tc = N('ShaderNodeTexCoord'); sep = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], sep.inputs[0])
    nz = N('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nz.inputs['Roughness'].default_value = 0.62; L(tc.outputs['Object'], nz.inputs['Vector']); L(ph.outputs['Fac'], nz.inputs['W'])
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.36; mr.inputs['From Max'].default_value = 0.68; mr.inputs['To Min'].default_value = 0.05; mr.inputs['To Max'].default_value = 1.5
    L(nz.outputs['Fac'], mr.inputs['Value'])
    dens = M('MULTIPLY', M('MULTIPLY', amp.outputs['Fac'], density), mr.outputs[0])
    if roof:
        ry, hd, eave, ridge = roof
        dy = M('MINIMUM', 1.0, M('DIVIDE', M('ABSOLUTE', M('SUBTRACT', sep.outputs['Y'], ry)), hd))
        top = M('SUBTRACT', ridge - 0.04, M('MULTIPLY', dy, ridge - eave))                       # the roof over this point
        band = M('MULTIPLY', M('SUBTRACT', top, floor), top_frac)                               # the top 30% of the room's height here
        nz2 = N('ShaderNodeTexNoise'); nz2.noise_dimensions = '4D'; nz2.inputs['Scale'].default_value = 4.0; nz2.inputs['Detail'].default_value = 6.0
        L(tc.outputs['Object'], nz2.inputs['Vector']); L(M('MULTIPLY', ph.outputs['Fac'], 1.3), nz2.inputs['W'])
        edge = M('ADD', M('DIVIDE', M('SUBTRACT', top, sep.outputs['Z']), M('MAXIMUM', band, 0.05)), M('MULTIPLY', M('SUBTRACT', nz2.outputs['Fac'], 0.5), 1.6))
        t_ = M('MINIMUM', 1.0, M('MAXIMUM', 0.0, edge)); fall = M('MULTIPLY', M('MULTIPLY', t_, t_), M('SUBTRACT', 3.0, M('MULTIPLY', t_, 2.0)))   # smoothstep
        dens = M('MULTIPLY', dens, fall)
    L(dens, pv.inputs['Density']); L(pv.outputs[0], out.inputs['Volume'])
    return m


def sparks(name, p0, p1, c=None, seed=0, **kw):
    """a burst column of hot sparks (key obj['amp'] up for a jab, back to 0): tiny, bright, quick, shrinking."""
    m = puff_mat('FX_spark', color=(1.0, 0.55, 0.16), shade=(1.0, 0.5, 0.1), emit=18.0, density=1.0, edge=0.5, noise_scale=0.4, diffuse=0.0)
    args = dict(n=26, life=0.65, rise=0.42, curl=0.07, turns=1.3, wind=(0.0, -0.06, 0.08), r0=0.011, r1=0.004, amp=0.0, peak=0.05)
    args.update(kw); return steam(name, p0, p1, mat=m, c=c, seed=seed, **args)
