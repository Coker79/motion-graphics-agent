# sourced by every script: sets HERE (project folder) and BL (Blender 5.x path). Override with BLENDER=/path/to/blender(.exe)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ospwd: the current folder in the form Blender wants (Git Bash: C:/..., macOS/Linux: plain pwd)
if pwd -W >/dev/null 2>&1; then ospwd() { pwd -W; }; else ospwd() { pwd; }; fi
# the setup scripts install tools into MS and save Blender's path in MS/blender
case "$(uname -s)" in
  Darwin)                 # setup/setup-mac.sh: venv + ~/.local/bin (ffmpeg, uv, node)
    MS="${MAKE_SHORT_HOME:-$HOME/.make-short}"
    export PATH="$MS/venv/bin:$HOME/.local/bin:$PATH" ;;
  MINGW*|MSYS*|CYGWIN*)   # Git Bash on Windows, setup/setup-windows.ps1: venv\Scripts + .make-short\bin (ffmpeg, uv, python3, blender) + apps\node-*
    MS="$(cygpath -u "${USERPROFILE:-$HOME}" 2>/dev/null || echo "$HOME")/.make-short"   # the installer uses %USERPROFILE%, which can differ from Git Bash's HOME
    for d in "$MS"/apps/node-v*-win-x64; do [ -d "$d" ] && PATH="$d:$PATH"; done
    export PATH="$MS/venv/Scripts:$MS/bin:$PATH"
    python3 -c '' >/dev/null 2>&1 || python3() { "$MS/venv/Scripts/python.exe" "$@"; }   # a Windows venv has only python.exe
    ;;
esac
export PYTHONUTF8=1   # Windows Python otherwise reads and writes text as cp1252 (curly quotes, captions)
if [ -z "$BLENDER" ]; then
  for c in "$(cat "$MS/blender" 2>/dev/null)" /Applications/Blender.app/Contents/MacOS/Blender "$HOME/Applications/Blender.app/Contents/MacOS/Blender"; do
    [ -n "$c" ] && [ -x "$c" ] && { BLENDER="$c"; break; }
  done
fi
if [ -n "$BLENDER" ]; then BL="$BLENDER"
else BL="$(ls -d "/c/Program Files/Blender Foundation/Blender 5."*/blender.exe 2>/dev/null | sort -V | tail -1)"; fi
[ -x "$BL" ] || { echo "Blender 5.x not found. Run the setup for your computer (setup/setup-mac.sh, or 'Install on Windows.cmd'), or set BLENDER=/path/to/blender"; exit 1; }
