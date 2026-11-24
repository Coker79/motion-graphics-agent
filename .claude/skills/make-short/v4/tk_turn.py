"""turnaround + expression test: blender -b -P tk_turn.py -- specs/keeper.json OUTDIR"""
import bpy, sys, os, json, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from toykit import look, char
args = sys.argv[sys.argv.index('--') + 1:]; spec = json.load(open(os.path.join(HERE, args[0]))); OUT = args[1]; os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
look.setup_render(sc, 1080, 1080, samples=32, motion_blur=False)
look.world_sky(sc, zenith=(0.62, 0.64, 0.68), horizon=(0.80, 0.80, 0.82), ground=(0.6, 0.6, 0.62), strength=0.9)
look.compositor(sc, bloom=0.2, vignette=0.0)
g = bpy.data.meshes.new('ground'); import bmesh; bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6); bm.to_mesh(g); bm.free()
go = bpy.data.objects.new('ground', g); sc.collection.objects.link(go); g.materials.append(look.mat('ground', (0.62, 0.62, 0.64), rough=0.9, brush=0.0, grain=0.0))
look.sun('key', (52, 0, -38), energy=3.2, color=(1.0, 0.9, 0.78), angle=4)
look.area('fill', (-2.5, -2.0, 1.6), (70, 0, -50), 120, (0.8, 0.86, 1.0), 3.0)
look.area('rim', (1.2, 2.2, 2.0), (-60, 0, 155), 220, (1.0, 0.92, 0.85), 1.5)
ch = char.Character(spec)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
def shoot(name, az, el, dist, lens, target):
    t = Vector(target); a, e = math.radians(az), math.radians(el)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
f = 1
for nm, az in (('t_front', 0), ('t_34', 35), ('t_side', 90), ('t_back', 180)):
    sc.frame_set(f); shoot(nm, az, 6, 2.9, 58, (0, 0, 0.57))
for i, ex in enumerate(('neutral', 'happy', 'shocked', 'angry', 'sad', 'smug', 'joy', 'pain')):
    fr = 10 + i * 10; ch.face.express(fr, ex, ramp=1)
ch.face.bake()
for i, ex in enumerate(('neutral', 'happy', 'shocked', 'angry', 'sad', 'smug', 'joy', 'pain')):
    fr = 10 + i * 10; sc.frame_set(fr); shoot('x_' + ex, 0, 2, 1.55, 75, (0, 0, 0.83))
print('TK_TURN done')
