"""side-by-side: python tools/compare.py OUT.png H label1=img1 label2=img2 ... (all scaled to height H, labelled)"""
import sys
from PIL import Image, ImageDraw
out, H = sys.argv[1], int(sys.argv[2]); items = [a.split('=', 1) for a in sys.argv[3:]]
ims = []
for lab, f in items:
    im = Image.open(f).convert('RGB'); im = im.resize((int(im.width * H / im.height), H), Image.LANCZOS); ims.append((lab, im))
W = sum(im.width for _, im in ims) + 12 * (len(ims) - 1); S = Image.new('RGB', (W, H + 40), (24, 24, 24)); d = ImageDraw.Draw(S); x = 0
for lab, im in ims:
    S.paste(im, (x, 40)); d.text((x + 8, 12), lab, fill=(255, 220, 120)); x += im.width + 12
S.save(out); print(out, S.size)
