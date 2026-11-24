"""measuring aid: python tools/grid.py SHEET.png x0 y0 x1 y1 OUT.png [step]  -> crop of the sheet with a labelled pixel grid
(coordinates are in the FULL sheet's pixels, so measurements read straight off the labels)."""
import sys
from PIL import Image, ImageDraw
src, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]; step = int(sys.argv[7]) if len(sys.argv) > 7 else 20
im = Image.open(src).convert('RGB').crop((x0, y0, x1, y1)); s = max(1, 1100 // max(im.size)); s = 1 if s < 1 else s
im = im.resize((im.width * s, im.height * s), Image.NEAREST) if s > 1 else im
d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * s; d.line([(X, 0), (X, im.height)], fill=(255, 0, 0) if x % 100 == 0 else (255, 170, 170), width=1)
    if x % 100 == 0: d.text((X + 2, 2), str(x), fill=(200, 0, 0))
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * s; d.line([(0, Y), (im.width, Y)], fill=(0, 0, 255) if y % 100 == 0 else (170, 170, 255), width=1)
    if y % 100 == 0: d.text((2, Y + 2), str(y), fill=(0, 0, 200))
im.save(out); print(out, im.size, 'scale', s)
