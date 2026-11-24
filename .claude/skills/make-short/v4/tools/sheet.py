"""contact sheet: python tools/sheet.py OUT.png COLS CELL img1 img2 ... (labels = file stems)"""
import sys, os
from PIL import Image, ImageDraw
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); files = sys.argv[4:]
rows = (len(files) + cols - 1) // cols; S = Image.new('RGB', (cols * cell, rows * cell), (30, 30, 30)); d = ImageDraw.Draw(S)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB'); im.thumbnail((cell, cell)); x, y = (i % cols) * cell, (i // cols) * cell
    S.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2)); d.text((x + 6, y + 4), os.path.splitext(os.path.basename(f))[0], fill=(255, 60, 60))
S.save(out); print(out, S.size)
