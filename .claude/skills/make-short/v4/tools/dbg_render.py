"""dbg_render.py: render a few frames of a set with ONE thing changed, to find what causes an artefact (lesson 70).
    TK_DBG='unlink:gush' blender -b -P tools/dbg_render.py -- SET renders/dbg/no_gush 100
Each change is applied after film.py builds the scene, just before it renders. Separate several with ';':
    unlink:<name part>           remove every object whose name contains it
    opaque:<material part>       render matching materials DITHERED (opaque pipeline) instead of BLENDED
    overlap:<material part>      turn Transparency Overlap ON for matching materials
    noray:                       ray tracing off
    eevee:<attr>=<value>         e.g. eevee:motion_blur_steps=64, eevee:motion_blur_max=128
    render:<attr>=<value>        e.g. render:motion_blur_shutter=0.2
Render the same frame several ways in parallel, then compare one crop (the Dutch flood found its grass strips in 6 renders)."""
import sys, os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE); os.chdir(HERE)
import toykit.film as tkfilm
_orig = tkfilm.render_range
def patched(sc, out, f0, f1, *a, **k):
    for act in filter(None, os.environ.get('TK_DBG', '').split(';')):
        kind, pat = act.split(':', 1)
        if kind == 'unlink':
            for o in list(bpy.data.objects):
                if pat in o.name:
                    for c in list(o.users_collection): c.objects.unlink(o)
        elif kind in ('opaque', 'overlap'):
            for m in bpy.data.materials:
                if pat in m.name:
                    if kind == 'opaque': m.surface_render_method = 'DITHERED'
                    else: m.use_transparency_overlap = True
        elif kind == 'noray': sc.eevee.use_raytracing = False
        elif kind in ('eevee', 'render'):
            tgt = sc.eevee if kind == 'eevee' else sc.render; k_, v_ = pat.split('='); setattr(tgt, k_, type(getattr(tgt, k_))(v_))
    print('DBG applied:', os.environ.get('TK_DBG', ''))
    return _orig(sc, out, f0, f1, *a, **k)
tkfilm.render_range = patched
exec(compile(open(os.path.join(HERE, 'film.py')).read(), 'film.py', 'exec'), {'__name__': '__main__', '__file__': os.path.join(HERE, 'film.py')})
