"""motion_strips.py: cut an animatic into MOTION strips for the motion review (SKILL §6.2).
  python3 tools/motion_strips.py out/animatic.mp4 voice/timing.json critic/motion [fps=6]
One PNG per script line (plus the 1 s tail), every tile labelled with its frame number, so a reviewer sees how things
MOVE (water flowing, feet planting, hands on props), not just whether a still reads. Stills every 0.5 s can't show a
flat plane rising or a texture sliding: the 13 s flood in the Dutch-flood test passed every still gate and still looked
rudimentary in motion."""
import json, os, subprocess, sys, shutil
from PIL import Image, ImageDraw
mp4, tj, out = sys.argv[1], sys.argv[2], sys.argv[3]; fps = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0
FF = shutil.which('ffmpeg') or os.path.expanduser('~/.local/bin/ffmpeg'); FP = shutil.which('ffprobe') or os.path.expanduser('~/.local/bin/ffprobe'); os.makedirs(out, exist_ok=True)
t = json.load(open(tj)); FPS = t.get('fps', 30); lead = t.get('lead', 1)
lines = [(l['n'], l['s'], l['e'], l['text']) for l in t['lines']]
dur = float(subprocess.run([FP, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4], capture_output=True, text=True).stdout)
spans = []
for i, (n, s, e, txt) in enumerate(lines):
    s0 = s - 0.25; e0 = (lines[i + 1][1] - 0.05) if i + 1 < len(lines) else dur
    spans.append((f'L{n:02d}', s0, e0, txt))
tmp = os.path.join(out, '_frames'); os.makedirs(tmp, exist_ok=True)
index = []
for tag, s0, e0, txt in spans:
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    subprocess.run([FF, '-v', 'error', '-ss', f'{max(0, s0):.3f}', '-to', f'{e0:.3f}', '-i', mp4, '-vf', f'fps={fps},scale=200:-1', os.path.join(tmp, 'f%03d.png')], check=True)
    fs = sorted(os.listdir(tmp)); cols = 8; rows = (len(fs) + cols - 1) // cols
    if not fs: continue
    w, h = Image.open(os.path.join(tmp, fs[0])).size
    S = Image.new('RGB', (cols * w, rows * h + 22), (20, 20, 20)); d = ImageDraw.Draw(S)
    d.text((6, 4), f'{tag}  {s0:.1f}-{e0:.1f}s  "{txt[:110]}"', fill=(255, 220, 90))
    for k, f in enumerate(fs):
        im = Image.open(os.path.join(tmp, f)).convert('RGB'); x, y = (k % cols) * w, 22 + (k // cols) * h; S.paste(im, (x, y))
        fr = int(round((max(0, s0) + k / fps) * FPS)) + lead; d.rectangle((x, y, x + 46, y + 12), fill=(0, 0, 0)); d.text((x + 2, y), f'f{fr}', fill=(255, 255, 255))
    p = os.path.join(out, f'{tag}.png'); S.save(p); index.append((tag, s0, e0, p))
shutil.rmtree(tmp)
print(f'{len(index)} strips at {fps:g} fps in {out}')
for tag, s0, e0, p in index: print(f'  {tag} {s0:5.1f}-{e0:5.1f}s {os.path.basename(p)}')
