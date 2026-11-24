"""fill_twos.py DIR [LAST] [--ones]: a twos preview renders every 2nd frame; give every missing f#####.png a hard link to
the frame before it (so the encode plays at a steady 30 fps, motion on twos). With --ones (P3, every frame rendered) any
missing frame is an error: nothing is doubled."""
import os, re, shutil, sys
ONES = '--ones' in sys.argv; ARGS = [a for a in sys.argv[1:] if a != '--ones']
d = ARGS[0]; have = sorted(int(m.group(1)) for f in os.listdir(d) if (m := re.match(r'f(\d{5})\.png$', f)))
last = int(ARGS[1]) if len(ARGS) > 1 else have[-1]; prev = None; n = 0; MINRUN = 1 if ONES else 2
hs = set(have); gaps = []; run = []                     # rc3: a crashed chunk leaves a GAP; doubling over it would freeze the shot (lesson 82)
for f in range(1, last + 1):
    if f in hs:
        if len(run) >= MINRUN: gaps.append((run[0], run[-1]))
        run = []
    else: run.append(f)
if len(run) >= MINRUN: gaps.append((run[0], run[-1]))
if gaps:
    print('fill_twos: MISSING RANGES (a crashed chunk?): ' + ', '.join(f'f{a}-{b}' for a, b in gaps) + ' -> re-render them with film.py SET DIR a-b, then re-run')
    sys.exit(1)
for f in range(1, last + 1):
    p = os.path.join(d, f'f{f:05d}.png')
    if os.path.exists(p): prev = p; continue
    src = prev or os.path.join(d, f'f{have[0]:05d}.png')
    try: os.link(src, p)
    except OSError: shutil.copyfile(src, p)   # exFAT/FAT32 drives and network shares have no hard links
    n += 1
print(f'fill_twos: {len(have)} rendered, {n} doubled, frames 1..{last}')
