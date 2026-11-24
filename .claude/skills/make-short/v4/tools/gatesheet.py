"""gatesheet.py DIR OUT.png [cols]: a labelled contact sheet of a beats render (frame + beat name on every still)."""
import os, sys
from PIL import Image, ImageDraw
d_, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 10
names = {}
for fn in os.listdir(d_):
    if fn.startswith('beats_') and fn.endswith('.txt'):
        for l in open(os.path.join(d_, fn)):
            if l.strip(): k, v = l.strip().split(' ', 1); names[k] = v
files = sorted(f for f in os.listdir(d_) if f.startswith('f') and f.endswith('.png'))
cw, ch = 270, 480; rows = (len(files) + cols - 1) // cols
S = Image.new('RGB', (cols * cw, rows * ch), (30, 30, 30)); dr = ImageDraw.Draw(S)
for i, f in enumerate(files):
    im = Image.open(os.path.join(d_, f)).convert('RGB').resize((cw, ch)); x, y = (i % cols) * cw, (i // cols) * ch; S.paste(im, (x, y))
    fr = str(int(f[1:6])); dr.rectangle((x, y, x + cw, y + 14), fill=(0, 0, 0)); dr.text((x + 3, y + 2), f"{fr} {names.get(fr, '')}"[:44], fill=(255, 220, 80))
S.save(out); print(out, S.size)
