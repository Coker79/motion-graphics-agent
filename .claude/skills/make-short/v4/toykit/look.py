"""toykit.look: render settings, materials, outlines and the compositor for the stylized-3D look
(target: soft warm key light, gentle shadow gradients, rim light, matte painterly materials, crisp dark outlines,
haze, bloom, shallow focus). Blender 5.2, EEVEE."""
import bpy, math, os

INK = (0.035, 0.022, 0.024)          # dark warm brown-plum outline, not pure black


def lin(*c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def hexc(h):
    h = h.lstrip('#'); return lin(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))


def _try(obj, **kw):
    for k, v in kw.items():
        try: setattr(obj, k, v)
        except Exception as e: print('toykit.look: skip', k, e)


def setup_render(sc, w=1080, h=1920, samples=48, fps=30, motion_blur=True, view='Khronos PBR Neutral', exposure=0.0):
    r = sc.render
    r.engine = 'BLENDER_EEVEE'; r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.fps = fps; r.film_transparent = False; r.image_settings.file_format = 'PNG'
    _try(r, use_motion_blur=motion_blur, motion_blur_shutter=0.45)
    # 16 time steps (or one per sample): a single step is one vector blur, which ghosts and tiles every frame whose shutter
    # straddles the START of a whip (the camera still for half the shutter, then 75% of the move): 30 frames in the Dutch
    # flood. Measured: no extra render time (samples are shared across steps), ordinary frames within 0.8 levels. TK_MB_STEPS overrides.
    _try(sc.eevee, motion_blur_steps=int(os.environ.get('TK_MB_STEPS', max(1, min(16, samples)))))
    vs = sc.view_settings; ok = False
    for vt, lk in ((view, None), ('Khronos PBR Neutral', None), ('AgX', 'AgX - Punchy'), ('AgX', None)):
        try:
            vs.view_transform = vt
            if lk: vs.look = lk
            ok = True; break
        except Exception: pass
    vs.exposure = exposure; vs.gamma = 1.0
    _try(sc.eevee, taa_render_samples=samples, use_raytracing=True, use_shadows=True, shadow_ray_count=2, shadow_step_count=8,
         use_volumetric_shadows=True, volumetric_tile_size='4', volumetric_samples=64, volumetric_end=120.0, bokeh_max_size=60.0,
         fast_gi_method='GLOBAL_ILLUMINATION', fast_gi_distance=2.0, horizon_quality=0.8)
    try:
        ro = sc.eevee.ray_tracing_options; _try(ro, resolution_scale='2', use_denoise=True)
    except Exception: pass
    sc.view_layers[0].use_pass_z = True
    return sc


def world_sky(sc, zenith=(0.24, 0.48, 0.92), horizon=(0.86, 0.80, 0.78), ground=(0.32, 0.30, 0.28), strength=1.0, haze=0.0, haze_col=(0.9, 0.8, 0.75)):
    """gradient sky (stylized), optional volumetric haze for depth + god rays."""
    w = bpy.data.worlds.new('TK_world'); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputWorld'); bg = N('ShaderNodeBackground'); bg.inputs[1].default_value = strength
    tc = N('ShaderNodeTexCoord'); sep = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Generated'], sep.inputs[0])
    # Generated on the world = view direction; z in -1..1
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.15; mr.inputs['From Max'].default_value = 0.85
    L(sep.outputs['Z'], mr.inputs['Value'])
    ramp = N('ShaderNodeValToRGB'); els = ramp.color_ramp.elements
    els[0].position = 0.0; els[0].color = (*ground, 1); els[1].position = 1.0; els[1].color = (*zenith, 1)
    e = els.new(0.17); e.color = (*horizon, 1); e2 = els.new(0.45); e2.color = tuple(0.5 * (a + b) for a, b in zip(horizon, zenith)) + (1,)
    ramp.color_ramp.interpolation = 'EASE'
    L(mr.outputs[0], ramp.inputs[0]); L(ramp.outputs[0], bg.inputs[0]); L(bg.outputs[0], out.inputs['Surface'])
    if haze > 0:
        vol = N('ShaderNodePrincipledVolume'); vol.inputs['Density'].default_value = haze; vol.inputs['Color'].default_value = (*haze_col, 1)
        vol.inputs['Anisotropy'].default_value = 0.45; L(vol.outputs[0], out.inputs['Volume'])
    return w


def strokes(nt, tco, col, amount=0.07, scale=7.0, stretch=3.5, hue=0.012, angle=0.5):
    """painterly dabs: elongated Voronoi cells (noise-warped object coords) each nudge value and hue a little."""
    N = nt.nodes.new; L = nt.links.new
    nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale * 0.6; nz.inputs['Detail'].default_value = 2.0
    L(tco.outputs['Object'], nz.inputs['Vector'])
    wa = N('ShaderNodeVectorMath'); wa.operation = 'MULTIPLY_ADD'; wa.inputs[1].default_value = (0.18, 0.18, 0.18)
    L(nz.outputs['Color'], wa.inputs[0]); L(tco.outputs['Object'], wa.inputs[2])
    mp = N('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (angle * 0.6, angle, angle * 1.3)
    mp.inputs['Scale'].default_value = (scale * stretch, scale, scale); L(wa.outputs[0], mp.inputs['Vector'])
    vo = N('ShaderNodeTexVoronoi'); vo.inputs['Randomness'].default_value = 1.0; L(mp.outputs[0], vo.inputs['Vector'])
    sp = N('ShaderNodeSeparateColor'); L(vo.outputs['Color'], sp.inputs[0])
    hv = N('ShaderNodeHueSaturation')
    mh = N('ShaderNodeMapRange'); mh.inputs['To Min'].default_value = 0.5 - hue; mh.inputs['To Max'].default_value = 0.5 + hue
    mv = N('ShaderNodeMapRange'); mv.inputs['To Min'].default_value = 1 - amount; mv.inputs['To Max'].default_value = 1 + amount
    L(sp.outputs[1], mh.inputs['Value']); L(sp.outputs[0], mv.inputs['Value'])
    L(mh.outputs[0], hv.inputs['Hue']); L(mv.outputs[0], hv.inputs['Value']); L(col, hv.inputs['Color'])
    return hv.outputs[0]


def mat(name, color, rough=0.6, sss=0.0, sheen=0.0, coat=0.0, metal=0.0, brush=0.05, grain=0.25, grain_scale=60.0,
        tex=None, tex_scale=1.0, tex_mix=1.0, emission=None, alpha=None, paint=0.0, paint_scale=7.0, spec=0.35):
    """stylized PBR: Principled BSDF, base colour x subtle painterly brush variation, fine grain bump (paint texture)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); p = N('ShaderNodeBsdfPrincipled')
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    for k, v in (('Subsurface Weight', sss), ('Sheen Weight', sheen), ('Coat Weight', coat)):
        if k in p.inputs: p.inputs[k].default_value = v
    if sss > 0 and 'Subsurface Radius' in p.inputs: p.inputs['Subsurface Radius'].default_value = (0.9, 0.45, 0.3)
    if sss > 0 and 'Subsurface Scale' in p.inputs: p.inputs['Subsurface Scale'].default_value = 0.03
    base = N('ShaderNodeRGB'); base.outputs[0].default_value = (*color[:3], 1); col = base.outputs[0]
    tco = N('ShaderNodeTexCoord')
    if tex:
        mp = N('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (tex_scale,) * 3
        ti = N('ShaderNodeTexImage'); ti.image = bpy.data.images.load(tex, check_existing=True); ti.projection = 'BOX'; ti.projection_blend = 0.25
        L(tco.outputs['Object'], mp.inputs[0]); L(mp.outputs[0], ti.inputs[0])
        mt = N('ShaderNodeMix'); mt.data_type = 'RGBA'; mt.blend_type = 'MULTIPLY'; mt.inputs[0].default_value = tex_mix
        L(col, mt.inputs[6]); L(ti.outputs[0], mt.inputs[7]); col = mt.outputs[2]
    if brush > 0:   # large soft colour variation, like a painted surface
        nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 3.0
        L(tco.outputs['Object'], nz.inputs['Vector'])
        mr = N('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - brush; mr.inputs['To Max'].default_value = 1 + brush
        L(nz.outputs['Fac'], mr.inputs['Value'])
        mb = N('ShaderNodeMix'); mb.data_type = 'RGBA'; mb.blend_type = 'MULTIPLY'; mb.inputs[0].default_value = 1.0
        cc = N('ShaderNodeCombineColor')
        for i in range(3): L(mr.outputs[0], cc.inputs[i])
        L(col, mb.inputs[6]); L(cc.outputs[0], mb.inputs[7]); col = mb.outputs[2]
    if paint > 0: col = strokes(nt, tco, col, paint, paint_scale)
    L(col, p.inputs['Base Color'])
    for k in ('Specular IOR Level', 'Specular'):
        if k in p.inputs: p.inputs[k].default_value = spec; break
    if grain > 0:   # fine brush-grain bump: reads as painted, not plastic
        gn = N('ShaderNodeTexNoise'); gn.inputs['Scale'].default_value = grain_scale; gn.inputs['Detail'].default_value = 6.0
        L(tco.outputs['Object'], gn.inputs['Vector'])
        bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = grain * 0.25; bp.inputs['Distance'].default_value = 0.002
        L(gn.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], p.inputs['Normal'])
    if emission:
        p.inputs['Emission Color'].default_value = (*emission[0][:3], 1); p.inputs['Emission Strength'].default_value = emission[1]
    if alpha is not None:
        p.inputs['Alpha'].default_value = alpha
    L(p.outputs[0], out.inputs[0])
    return m


def flat(name, color, strength=1.0):
    """unlit colour (decal fills that must not shade, e.g. eye whites keep a hint of shading via mix)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (*color[:3], 1); em.inputs[1].default_value = strength
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], o.inputs[0]); return m


def ink_mat(color=None):
    nm = 'TK_ink' if color is None else 'TK_ink_%02x%02x%02x' % tuple(int(c * 255) for c in color[:3])
    m = bpy.data.materials.get(nm)
    if m: return m
    m = flat(nm, INK if color is None else color); m.use_backface_culling = True
    try: m.use_backface_culling_shadow = True
    except Exception: pass
    return m


def outline(obj, width, color=None):
    """inverted-hull outline (solidify, flipped normals, back-face-culled dark material)."""
    if obj.type != 'MESH' or width <= 0: return obj
    obj.data.materials.append(ink_mat(color))
    md = obj.modifiers.new('TK_ink', 'SOLIDIFY'); md.thickness = width; md.offset = 1.0
    md.use_flip_normals = True; md.use_rim = False; md.material_offset = len(obj.data.materials) - 1
    md.use_quality_normals = True
    return obj


def node(nt, kind, loc=(0, 0), **inputs):
    n = nt.nodes.new(kind); n.location = loc
    for k, v in inputs.items():
        try: n.inputs[k].default_value = v
        except Exception as e: print('toykit.look node', kind, k, e)
    return n


def compositor(sc, bloom=0.35, warmth=0.03, vignette=0.22, haze=0.0, haze_col=(0.75, 0.93, 0.94), beams=0.0,
               beam_pos=(0.06, 0.97), saturation=1.0, paint=0):
    """grade: depth haze (mist pass) -> sun beams -> bloom -> saturation -> warm balance -> paint filter -> vignette."""
    sc.render.use_compositing = True
    nt = bpy.data.node_groups.new('TK_comp', 'CompositorNodeTree'); sc.compositing_node_group = nt
    nt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor'); L = nt.links.new; N = nt.nodes.new
    rl = N('CompositorNodeRLayers'); rl.location = (-1400, 0); last = rl.outputs['Image']
    if haze > 0:
        sc.view_layers[0].use_pass_mist = True
        mr = N('ShaderNodeMapRange'); mr.inputs['To Max'].default_value = haze; L(rl.outputs['Mist'], mr.inputs['Value'])
        sky = N('ShaderNodeMapRange'); sky.inputs['From Min'].default_value = 600.0; sky.inputs['From Max'].default_value = 601.0
        sky.inputs['To Min'].default_value = 1.0; sky.inputs['To Max'].default_value = 0.0; L(rl.outputs['Depth'], sky.inputs['Value'])
        hm = N('ShaderNodeMath'); hm.operation = 'MULTIPLY'; L(mr.outputs[0], hm.inputs[0]); L(sky.outputs[0], hm.inputs[1])   # never haze the sky
        mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MIX'; L(hm.outputs[0], mx.inputs[0])
        L(last, mx.inputs[6]); mx.inputs[7].default_value = (*haze_col, 1); last = mx.outputs[2]
    if beams > 0:   # rays come from the SKY only (a bright yellow coat must not streak), then are added over everything
        sky = N('ShaderNodeMapRange'); sky.inputs['From Min'].default_value = 600.0; sky.inputs['From Max'].default_value = 601.0
        L(rl.outputs['Depth'], sky.inputs['Value'])
        sm = N('ShaderNodeMix'); sm.data_type = 'RGBA'; sm.blend_type = 'MULTIPLY'; sm.inputs[0].default_value = 1.0
        L(last, sm.inputs[6]); L(sky.outputs[0], sm.inputs[7])
        sb = N('CompositorNodeGlare'); L(sm.outputs[2], sb.inputs['Image'])
        for k, v in (('Type', 'Sun Beams'), ('Threshold', 0.25), ('Strength', beams), ('Size', 0.6), ('Sun Position', beam_pos), ('Jitter', 0.6)):
            try: sb.inputs[k].default_value = v
            except Exception as e: print('toykit.look beams', k, e)
        ad = N('ShaderNodeMix'); ad.data_type = 'RGBA'; ad.blend_type = 'ADD'; ad.inputs[0].default_value = 1.0
        L(last, ad.inputs[6]); L(sb.outputs['Glare'], ad.inputs[7]); last = ad.outputs[2]
    if bloom > 0:
        gl = N('CompositorNodeGlare'); L(last, gl.inputs['Image'])
        for k, v in (('Type', 'Bloom'), ('Threshold', 0.85), ('Strength', bloom), ('Size', 0.55)):
            try: gl.inputs[k].default_value = v
            except Exception as e: print('toykit.look bloom', k, e)
        last = gl.outputs['Image']
    if saturation != 1.0:
        hs = N('CompositorNodeHueSat'); L(last, hs.inputs['Image']); hs.inputs['Saturation'].default_value = saturation; last = hs.outputs[0]
    cb = N('CompositorNodeColorBalance')
    try:
        cb.inputs['Type'].default_value = 'Lift/Gamma/Gain'
        cb.inputs['Gain'].default_value = (1.0 + warmth, 1.0, 1.0 - warmth, 1)
        cb.inputs['Lift'].default_value = (1.0, 1.0, 1.02, 1)
    except Exception as e: print('color balance', e)
    L(last, cb.inputs['Image']); last = cb.outputs[0]
    if paint > 0:
        kw = N('CompositorNodeKuwahara'); L(last, kw.inputs['Image'])
        for k, v in (('Size', paint), ('Type', 'Anisotropic'), ('Uniformity', 4), ('Sharpness', 0.6), ('Eccentricity', 1.0)):
            try: kw.inputs[k].default_value = v
            except Exception as e: print('toykit.look kuwahara', k, e)
        last = kw.outputs[0]
    if vignette > 0:
        em = N('CompositorNodeEllipseMask')
        try: em.inputs['Size'].default_value = (0.95, 0.85)
        except Exception: pass
        bl = N('CompositorNodeBlur')
        try: bl.inputs['Size'].default_value = (220, 220)
        except Exception: pass
        try: L(em.outputs[0], bl.inputs['Image'])
        except Exception: pass
        mr = N('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - vignette; mr.inputs['To Max'].default_value = 1.0
        L(bl.outputs[0], mr.inputs['Value'])
        mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        L(last, mx.inputs[6]); L(mr.outputs[0], mx.inputs[7]); last = mx.outputs[2]
    go = N('NodeGroupOutput'); L(last, go.inputs[0])
    return nt


def sun(name, rot_deg, energy=4.0, color=(1.0, 0.86, 0.68), angle=2.0):
    l = bpy.data.lights.new(name, 'SUN'); l.energy = energy; l.color = color; l.angle = math.radians(angle)
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = tuple(math.radians(a) for a in rot_deg); return o


def area(name, loc, rot_deg, energy, color=(1, 1, 1), size=2.0):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color; l.size = size
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = tuple(math.radians(a) for a in rot_deg); return o
