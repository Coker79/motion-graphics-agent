#!/bin/bash
# check.sh: is this computer ready for make-short? Prints PASS / WARN / FAIL per item. macOS, or Windows Git Bash.
#   bash ~/.claude/skills/make-short/setup/check.sh [--smoke]
# --smoke also renders one real still in Blender from the shipped example (about 1 minute) and checks it.
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; SMOKE=0; [ "${1:-}" = "--smoke" ] && SMOKE=1
fail=0; warn=0
ok()  { printf '  PASS  %s\n' "$*"; }
bad() { printf '  FAIL  %s\n        fix: %s\n' "$1" "$2"; fail=$((fail+1)); }
wrn() { printf '  WARN  %s\n' "$*"; warn=$((warn+1)); }
MAC=0; WIN=0; case "$(uname -s)" in Darwin) MAC=1;; MINGW*|MSYS*|CYGWIN*) WIN=1;; esac
MS="${MAKE_SHORT_HOME:-$HOME/.make-short}"; [ $WIN = 1 ] && MS="$(cygpath -u "${USERPROFILE:-$HOME}" 2>/dev/null || echo "$HOME")/.make-short"
if [ $MAC = 1 ]; then FIX="bash \"$SKILL/setup/setup-mac.sh\""; export PATH="$MS/venv/bin:$HOME/.local/bin:$PATH"
elif [ $WIN = 1 ]; then FIX="double-click 'Install on Windows.cmd' in the make-short folder"; for d in "$MS"/apps/node-v*-win-x64; do [ -d "$d" ] && PATH="$d:$PATH"; done; export PATH="$MS/venv/Scripts:$MS/bin:$PATH"
else FIX="see INSTALL.md"; fi
echo "make-short check: $SKILL"

[ -f "$SKILL/SKILL.md" ] && [ -f "$SKILL/v4/toykit/char.py" ] && ok "skill files (v4 toykit)" || bad "skill files missing" "reinstall the skill folder"
for f in "$SKILL"/v4/*.sh; do [ -x "$f" ] || { chmod +x "$f" 2>/dev/null; }; done; ok "scripts executable"

BL=$( ( . "$SKILL/v4/env.sh" >/dev/null 2>&1 && echo "$BL" ) )
if [ -n "$BL" ] && V=$("$BL" --version 2>/dev/null | head -1) && echo "$V" | grep -qE '^Blender 5\.'; then ok "$V"
else bad "Blender 5.x not found" "$FIX"; fi

if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then
  F=$(ffmpeg -hide_banner -filters 2>/dev/null); E=$(ffmpeg -hide_banner -encoders 2>/dev/null); miss=""
  for x in subtitles sidechaincompress loudnorm amix silenceremove atempo asetrate; do echo "$F" | grep -qE " $x " || miss="$miss $x"; done
  echo "$E" | grep -q libx264 || miss="$miss libx264"
  [ -z "$miss" ] && ok "ffmpeg $(ffmpeg -hide_banner -version | head -1 | awk '{print $3}') (captions, mixing, sheets)" || bad "ffmpeg lacks:$miss" "$FIX"
else bad "ffmpeg / ffprobe not on PATH" "$FIX"; fi

PY=python; [ $MAC = 1 ] && PY="$MS/venv/bin/python"; [ $WIN = 1 ] && [ -e "$MS/venv/Scripts/python.exe" ] && PY="$MS/venv/Scripts/python"
if "$PY" -c "import numpy, PIL, cv2" 2>/dev/null; then ok "python $("$PY" -c 'import sys;print(sys.version.split()[0])') with numpy, pillow + opencv"; else bad "python with numpy, pillow + opencv" "$FIX"; fi
if [ $WIN = 1 ]; then python3 -c "import numpy, PIL, cv2" 2>/dev/null && ok "python3 runs the kit's Python (Git Bash)" || bad "python3 is not the kit's Python (a Windows venv has only python.exe)" "$FIX"; fi
command -v blender >/dev/null && ok "blender command on PATH" || wrn "no blender command on PATH yet: re-run the setup (scripts still find Blender themselves)"
if "$PY" -c "import whisper" 2>/dev/null && command -v whisper >/dev/null; then ok "whisper (word timings for the voice)"; else bad "whisper not installed" "$FIX"; fi
[ -f "$HOME/.cache/whisper/small.pt" ] && ok "whisper small model cached" || wrn "whisper small model not downloaded yet (about 460 MB on the first transcribe)"


FONT=""; for p in "$HOME/Library/Fonts"/Montserrat-ExtraBold.* /Library/Fonts/Montserrat-ExtraBold.* "$LOCALAPPDATA/Microsoft/Windows/Fonts"/Montserrat-ExtraBold.* /c/Windows/Fonts/Montserrat-ExtraBold.*; do [ -f "$p" ] && FONT="$p"; done
[ -n "$FONT" ] && ok "caption font Montserrat ExtraBold" || wrn "Montserrat ExtraBold not installed: captions fall back to a system font (install it free from Google Fonts)"

if [ $SMOKE = 1 ] && [ $fail = 0 ]; then
  T="$(mktemp -d)/smoke"; cp -R "$SKILL/v4" "$T"
  echo "  ...building a toy character in Blender and rendering its turnaround (about 30 s)"
  if (cd "$T" && "$BL" -b -P tk_turn.py -- specs/keeper.json renders/smoke >/dev/null 2>&1) && [ -f "$T/renders/smoke/x_joy.png" ]; then ok "smoke render: character + 8 expressions rendered ($T/renders/smoke)"
  else bad "smoke render failed" "run: cd \"$T\" && \"$BL\" -b -P tk_turn.py -- specs/keeper.json renders/smoke"; fi
fi
echo "  INFO  Character sheets, voice, music and SFX use the Higgsfield connector in your Claude account; see references/higgsfield-v4.md"
echo; if [ $fail = 0 ]; then echo "READY ($warn warning(s)). In Claude Code: /make-short <your idea>"; else echo "NOT READY: $fail problem(s) above."; exit 1; fi
