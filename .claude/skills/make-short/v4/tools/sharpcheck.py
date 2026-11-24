"""sharpcheck.py REF.mp4 NEW.mp4 [ratio=0.4] [run=6] (run it after every --only round AND on the final against the last animatic): per-frame sharpness (variance of the Laplacian, grey) of NEW against REF;
flags every run of `run`+ frames where NEW < ratio x REF (a camera parked against a wall, a lost focus key: the pineapple
pit's hook regression went 347 -> 103 over f77-96 and no one saw it for two rounds). Frames are 1-based."""
import sys, cv2, numpy as np
ref, new = sys.argv[1], sys.argv[2]; ratio = float(sys.argv[3]) if len(sys.argv) > 3 else 0.4; run = int(sys.argv[4]) if len(sys.argv) > 4 else 6
def size(path):
    cap = cv2.VideoCapture(path); return int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
RW, RH = size(ref)   # a 1080p final is scaled to the reference animatic's size first (variance of the Laplacian depends on resolution)
def lap(path):
    cap = cv2.VideoCapture(path); out = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        if fr.shape[1] != RW or fr.shape[0] != RH: fr = cv2.resize(fr, (RW, RH), interpolation=cv2.INTER_AREA)
        out.append(cv2.Laplacian(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    return np.array(out)
a, b = lap(ref), lap(new); n = min(len(a), len(b)); a, b = a[:n], b[:n]
low = b < ratio * a; runs = []; i = 0
while i < n:
    if low[i]:
        j = i
        while j + 1 < n and low[j + 1]: j += 1
        if j - i + 1 >= run: runs.append((i + 1, j + 1))
        i = j + 1
    else: i += 1
print(f'{n} frames; median sharpness REF {np.median(a):.0f}, NEW {np.median(b):.0f}; flagged runs (NEW < {ratio:.0%} of REF for {run}+ frames): {len(runs)}')
for f0, f1 in runs:
    print(f'  f{f0}-f{f1} ({f1 - f0 + 1} frames): REF median {np.median(a[f0 - 1:f1]):.0f}, NEW median {np.median(b[f0 - 1:f1]):.0f}')
for lab, (f0, f1) in (('hook f77-96', (77, 96)), ('clod f96-106', (96, 106))):
    print(f'  {lab}: REF median {np.median(a[f0 - 1:f1]):.0f}, NEW median {np.median(b[f0 - 1:f1]):.0f}')
