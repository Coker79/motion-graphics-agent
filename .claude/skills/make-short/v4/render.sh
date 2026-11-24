#!/bin/bash
# render.sh SET [SET ...]   -> renders/final/f#####.png for every frame of the listed sets (1080x1920, on ones, motion blur),
# then finish.py -> out/short.mp4. Render this ONCE, after the user approves P3 (SKILL §6, lesson 28).
# Three Blender workers; TK_SAMPLES defaults to 16 (A/B'd against 32 at PSNR 52-54 dB: indistinguishable, about half the time).
#   bash render.sh camp cupboard museum            (M1 Pro: about 50-70 min for a 50 s Short)
# Measured: the 61 s Dutch flood (1842 frames, water-heavy) took 88 min: 2.6 s/frame with all 3 workers busy,
# 4.1 s/frame for a lone worker; water/transparency sets are slowest (its hook: 13 s/frame per worker).
. "$(dirname "$0")/env.sh"; cd "$HERE";
[ voice/timing.json -nt voice/voice.json ] || "$BL" -b -P timing_dump.py > logs_timing.txt 2>&1 || { echo "timing_dump.py failed (see logs_timing.txt)"; exit 1; }
 mkdir -p renders/final logs
export TK_SAMPLES="${TK_SAMPLES:-16}"; CH=""
for S in "$@"; do
  R=$("$BL" -b -P film.py -- "$S" renders/final none 2>/dev/null | grep "^FILM $S " | awk '{print $3, $4}'); [ -n "$R" ] || { echo "film.py did not report set $S"; exit 1; }
  read F0 F1 <<< "$R"; LASTF=$F1; n=$((F1 - F0 + 1)); k=$(( (n + 159) / 160 ))
  for i in $(seq 0 $((k - 1))); do a=$((F0 + i * n / k)); b=$((F0 + (i + 1) * n / k - 1)); CH="$CH $S:$a-$b"; done
done
echo "chunks:$CH"; Q=$(mktemp -d) || { echo "mktemp failed"; exit 1; }
# Shared queue: each worker claims the next unclaimed chunk (mkdir is atomic), so no worker idles while chunks remain.
# (A fixed 3-way split left 2 of 3 workers idle for the last 20-27 min of the Dutch-flood final.)
work() { for c in $CH; do mkdir "$Q/${c//:/_}" 2>/dev/null || continue; S=${c%%:*}; F=${c#*:}
  "$BL" -b -P film.py -- "$S" renders/final "$F" > "logs/render_${S}_${F}.log" 2>&1 || echo "FAILED $c (see logs)"; done; }
date; work & work & work & wait; date; rm -rf "$Q"
n=$(ls renders/final/f*.png 2>/dev/null | wc -l | tr -d ' '); echo "$n frames rendered"
# rc3: every frame must exist before the mix: a crashed worker (Blender 5.2's shrinkwrap BVH race) leaves a gap (lesson 82)
python3 - "$LASTF" <<'PY' || exit 1
import os, re, sys
have = {int(m.group(1)) for f in os.listdir('renders/final') if (m := re.match(r'f(\d{5})\.png$', f))}
last = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else max(have); miss = [f for f in range(min(have), last + 1) if f not in have]
if miss: print(f'MISSING {len(miss)} frames: {miss[:40]} -> re-render them: blender -b -P film.py -- SET renders/final a,b,c (then python3 finish.py)'); sys.exit(1)
print('all frames present')
PY
python3 finish.py && echo "done: out/"
