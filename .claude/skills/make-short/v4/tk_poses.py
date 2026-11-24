"""pose test: blender -b -P tk_poses.py -- specs/keeper.json OUTDIR"""
import bpy, sys, os, json, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from toykit import look, char, rig
args = sys.argv[sys.argv.index('--') + 1:]; spec = json.load(open(os.path.join(HERE, args[0]))); OUT = args[1]; os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
look.setup_render(sc, 900, 900, samples=24, motion_blur=False)
look.world_sky(sc, zenith=(0.62, 0.64, 0.68), horizon=(0.80, 0.80, 0.82), ground=(0.6, 0.6, 0.62), strength=0.9)
look.compositor(sc, bloom=0.2, vignette=0.0)
import bmesh
g = bpy.data.meshes.new('ground'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6); bm.to_mesh(g); bm.free()
go = bpy.data.objects.new('ground', g); sc.collection.objects.link(go); g.materials.append(look.mat('ground', (0.62, 0.62, 0.64), rough=0.9, brush=0.0, grain=0.0))
look.sun('key', (52, 0, -38), energy=3.2, color=(1.0, 0.9, 0.78), angle=4)
look.area('fill', (-2.5, -2.0, 1.6), (70, 0, -50), 120, (0.8, 0.86, 1.0), 3.0)
ch = char.Character(spec); arm = rig.build(ch); A = rig.Actor(ch, arm)
names = ['rest', 'idle', 'wave_up', 'shocked', 'cheer', 'shrug', 'hips', 'think', 'point', 'sad', 'angry', 'hold_out']
faces = {'shocked': 'shocked', 'cheer': 'joy', 'shrug': 'confused', 'think': 'thinking', 'sad': 'sad', 'angry': 'angry', 'wave_up': 'happy', 'point': 'determined', 'hold_out': 'happy'}
for i, n in enumerate(names):
    f = 10 + i * 10; A.pose(f, n, ramp=1, hold_prev=False); ch.face.express(f, faces.get(n, 'neutral'), ramp=1)
ch.face.bake()
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
t = Vector((0, 0, 0.56)); a, e = math.radians(28), math.radians(8)
cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 3.0
cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 58
for i, n in enumerate(names):
    sc.frame_set(10 + i * 10); sc.render.filepath = os.path.join(OUT, f'p{i:02d}_{n}.png'); bpy.ops.render.render(write_still=True)
print('TK_POSES done')
