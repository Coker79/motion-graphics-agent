"""camstats.py VIDEO [--twos]: how much the camera moves, compared like with like against the reference Shorts.
Per frame pair: global image shift by phase correlation (numpy only) on 270-wide greyscale, reported in 1080-wide px.
It sees PANS, TILTS, TRUCKS and SHIFTS only: push-ins, zooms and slow creeps barely register and count as "still".
Reference numbers ON THIS METER (re-measured 2026-11-17):
  RicksClips reference (railroads-ref/ref.mp4)   median 0.3, mean 3.7 px/frame, still 74 %, a big move every 1.4 s
  Hardtack v4 final, approved by Matt              mean 2.6, still 80 %
  Hardtack v1, called "stagnant"                   a big move every 4.8 s, mean 1.5
  Dutch-flood animatic C (--twos)                  mean 5.5, still 72 %, a big move every 2.0 s
So the still % is NOT a target: even the reference is ~74 % "still" here. Watch the BIG-MOVE RATE (aim for one every
1.5-2.5 s, landing on sentence starts) and the mean (about 3-6). (Feature-displacement tools such as refstats see
push-ins too and report a median of ~11 and ~6 % still for the same reference; never mix the two yardsticks.)
  big moves         bursts over 25 px/frame
--twos: the file is an animatic drawn on twos; pairs are measured f -> f+2 and halved."""
import os, subprocess, sys
import numpy as np

vid = sys.argv[1]; twos = '--twos' in sys.argv
W = 270
ff = os.path.expanduser('~/.local/bin/ffmpeg'); ff = ff if os.path.exists(ff) else 'ffmpeg'
probe = subprocess.run([ff, '-i', vid], capture_output=True, text=True).stderr
import re
m = re.search(r'(\d{2,5})x(\d{2,5})', probe.split('Video:')[1]); w0, h0 = int(m.group(1)), int(m.group(2)); H = int(round(h0 * W / w0 / 2) * 2)
fps = float(re.search(r'([\d.]+) fps', probe).group(1))
raw = subprocess.run([ff, '-v', 'error', '-i', vid, '-vf', f'scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
win = np.outer(np.hanning(H), np.hanning(W)).astype(np.float32)
def shift(a, b):
    A = np.fft.fft2((a - a.mean()) * win); B = np.fft.fft2((b - b.mean()) * win)
    R = A * np.conj(B); R /= np.abs(R) + 1e-6; c = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(c), c.shape)
    def sub(m, p, n):                                    # parabolic sub-pixel refinement of the correlation peak
        d = m - 2 * p + n; return 0.0 if abs(d) < 1e-9 else 0.5 * (m - n) / d
    fx = sub(c[y, (x - 1) % W], c[y, x], c[y, (x + 1) % W]); fy = sub(c[(y - 1) % H, x], c[y, x], c[(y + 1) % H, x])
    y = (y - H if y > H // 2 else y) + fy; x = (x - W if x > W // 2 else x) + fx
    return np.hypot(x, y)
step = 2 if twos else 1
v = np.array([shift(fr[i], fr[i + step]) / step for i in range(0, len(fr) - step, step)]) * (1080 / W)
big = v > 25; starts = np.flatnonzero(big & ~np.r_[False, big[:-1]])
dur = len(fr) / fps
print(f'{os.path.basename(vid)}: {len(fr)} frames, {dur:.1f} s')
print(f'  median {np.median(v):.1f} px/frame (1080-wide), mean {v.mean():.1f}; still (<1 px) {100 * np.mean(v < 1):.0f} %')
print(f'  big moves (>25 px/frame bursts): {len(starts)} = one every {dur / max(1, len(starts)):.1f} s; at frames ' +
      ', '.join(str(int(s * step) + 1) for s in starts))
