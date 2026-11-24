#!/bin/bash
# animatic.sh NAME SETS [--only "set:a-b set:a-b ..."] [--ones]     e.g.  bash animatic.sh p1 "camp cupboard museum"
#   A preview for REVIEW at 480x854, 8 samples, motion blur, with the real voice, music, SFX and captions -> out/NAME.mp4.
#   Default (P1, P2): rendered on twos and doubled back to 30 fps. Three Blender workers, about 12 min for 50 s.
#   --ones (P3): every frame rendered, with the final's motion (one-frame pops, whip-start smears and SFX hits show),
#     into renders/animatic_ones. About twice the twos time.
#   --only re-renders just those frame ranges into the existing preview frames (a fix round takes minutes), then re-mixes.
# Plan exactly three previews (SKILL §6) before ONE full render: a full 1080p pass takes 50-130 min (see render.sh).
. "$(dirname "$0")/env.sh"; cd "$HERE";
[ voice/timing.json -nt voice/voice.json ] || "$BL" -b -P timing_dump.py > logs_timing.txt 2>&1 || { echo "timing_dump.py failed (see logs_timing.txt)"; exit 1; }
NAME="${1:-animatic}"; SETS="$2"; ONLY=""; STEP=2
[ -n "$SETS" ] || { echo "usage: bash animatic.sh NAME \"set1 set2 ...\" [--only \"set:a-b ...\"] [--ones]"; exit 1; }
shift 2
while [ $# -gt 0 ]; do
  case "$1" in
    --only) ONLY="$2"; shift 2 ;;
    --ones) STEP=1; shift ;;
    *) echo "unknown option: $1 (use --only \"set:a-b ...\" and/or --ones)"; exit 1 ;;
  esac
done
D=renders/animatic; [ "$STEP" = 1 ] && D=renders/animatic_ones
mkdir -p "$D" logs out; CH=""; LAST=0; CHUNK=$((110 * STEP))     # about 110 renders per chunk either way
for S in $SETS; do
  R=$("$BL" -b -P film.py -- "$S" "$D" none --animatic 2>/dev/null | grep "^FILM $S " | awk '{print $3, $4}'); [ -n "$R" ] || { echo "film.py did not report set $S"; exit 1; }
  read F0 F1 <<< "$R"; [ "$F1" -gt "$LAST" ] && LAST=$F1
  if [ -z "$ONLY" ]; then
    n=$((F1 - F0 + 1)); k=$(( (n + CHUNK - 1) / CHUNK ))
    for i in $(seq 0 $((k - 1))); do a=$((F0 + i * n / k)); b=$((F0 + (i + 1) * n / k - 1)); CH="$CH $S:$a-$b:$STEP"; done
  fi
done
if [ -z "$ONLY" ]; then rm -f "$D"/f*.png
else
  for r in $(echo $ONLY); do S=${r%%:*}; AB=${r#*:}; A=${AB%-*}; B=${AB#*-}
    for f in $(seq $A $B); do rm -f "$D/f$(printf %05d $f).png"; done; CH="$CH $S:$A-$B:$STEP"; done
fi
echo "chunks:$CH"; Q=$(mktemp -d) || { echo "mktemp failed"; exit 1; }
# Shared queue: each worker claims the next unclaimed chunk (mkdir is atomic), so no worker idles while chunks remain.
work() { for c in $CH; do mkdir "$Q/${c//:/_}" 2>/dev/null || continue; S=${c%%:*}; F=${c#*:}
  "$BL" -b -P film.py -- "$S" "$D" "$F" --animatic > "logs/anim_${S}_${F%%:*}.log" 2>&1 || echo "FAILED $c (see logs)"; done; }
T0=$(date +%s); date; work & work & work & wait; T1=$(date +%s); rm -rf "$Q"; echo "render $((T1 - T0)) s"
FT=""; [ "$STEP" = 1 ] && FT="--ones"
python3 fill_twos.py "$D" "$LAST" $FT && python3 finish.py "$D" "out/$NAME.mp4" && echo "done: out/$NAME.mp4 ($(( $(date +%s) - T0 )) s total)"
