#!/bin/bash
# setup-mac.sh: installs make-short AND everything it needs on an Apple Silicon Mac. No admin password needed.
# Safe to re-run: it skips anything already installed. Run it from wherever you unzipped make-short, e.g.:
#   bash ~/Downloads/make-short/setup/setup-mac.sh [--no-model] [--smoke]
# It never asks for input, so Claude Code can run it for you (in the background: it takes 10-30 minutes).
# --smoke ends with a real Blender render (about 1 minute), proving the whole kit works.
#
# What it installs (every download checked against a pinned SHA-256; about 3 GB of disk):
#   the skill itself           -> ~/.claude/skills/make-short (when run from somewhere else; an older copy moves to ~/.make-short/backups)
#   Blender 5.2.4 LTS          -> /Applications/Blender.app (or ~/Applications if /Applications isn't writable)
#   ffmpeg + ffprobe 9.0.2     -> ~/.local/bin            (native arm64 build from ffmpeg.martin-riedl.de, with captions support)
#   uv 0.13.8                  -> ~/.local/bin            (Python manager from Astral)
#   Python 3.12 + Whisper      -> ~/.make-short/venv      (numpy, pillow, opencv, openai-whisper)
#   Node 24                    -> ~/.make-short/node      (only if you don't already have Node 22 or newer)
#   Whisper "small" model      -> ~/.cache/whisper        (about 460 MB; skip with --no-model, it then downloads on first use)
# It also adds ~/.local/bin to your PATH in ~/.zshrc (one line, marked "make-short") and links `blender` there.
set -euo pipefail
NO_MODEL=0; SMOKE=""
for a in "$@"; do case "$a" in --no-model) NO_MODEL=1 ;; --smoke) SMOKE=--smoke ;; *) echo "unknown option: $a (use --no-model or --smoke)"; exit 1 ;; esac; done
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ "$(uname -s)" = Darwin ] || { echo "This script is for macOS. On Windows, follow INSTALL.md."; exit 1; }
[ "$(uname -m)" = arm64 ] || { echo "Blender 5 only ships for Apple Silicon Macs (M1 or newer); this Mac is $(uname -m)."; exit 1; }
LB="$HOME/.local/bin"; MS="${MAKE_SHORT_HOME:-$HOME/.make-short}"; DL="$MS/downloads"; mkdir -p "$LB" "$DL"
export PATH="$LB:$PATH"
step() { printf '\n== %s\n' "$*"; }
fetch() {   # fetch URL SHA256 OUTFILE : download once, verify, keep
  local url=$1 sha=$2 out=$3
  if [ -f "$out" ] && [ "$(shasum -a 256 "$out" | cut -d' ' -f1)" = "$sha" ]; then echo "  cached $(basename "$out")"; return 0; fi
  echo "  downloading $(basename "$out")"
  if [ -t 2 ]; then curl -fL --retry 3 --progress-bar -o "$out.part" "$url"   # a progress bar in a terminal
  else curl -fsSL --retry 3 -o "$out.part" "$url"; fi                         # plain lines when Claude Code runs it
  if [ "$(shasum -a 256 "$out.part" | cut -d' ' -f1)" != "$sha" ]; then rm -f "$out.part"; echo "CHECKSUM MISMATCH for $url. Stopping; nothing was installed from it."; exit 1; fi
  mv "$out.part" "$out"; echo "  got $(basename "$out") ($(du -m "$out" | cut -f1) MB, checksum OK)"
}
[ -t 2 ] || export TQDM_DISABLE=1   # no progress-bar flood in a log (the Whisper model download)
free_gb=$(df -k "$HOME" | awk 'NR==2{print int($4/1048576)}'); [ "$free_gb" -ge 4 ] || { echo "Only ${free_gb} GB free; make-short setup needs about 4 GB."; exit 1; }

step "0/7 The skill"
DST="$HOME/.claude/skills/make-short"
if [ -d "$DST" ] && [ "$(cd "$DST" && pwd -P)" = "$(cd "$SKILL" && pwd -P)" ]; then echo "  running from $DST"
else
  if [ -e "$DST" ]; then BAK="$MS/backups/make-short-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$MS/backups"; mv "$DST" "$BAK"; echo "  your previous make-short was moved to $BAK"; fi
  mkdir -p "$HOME/.claude/skills"; cp -R "$SKILL" "$DST"
  xattr -dr com.apple.quarantine "$DST" 2>/dev/null || true   # clear the downloaded-from-internet flag
  echo "  installed the skill to $DST"; SKILL="$DST"
fi

step "1/7 Blender 5.2"
BL=""
for c in "$(cat "$MS/blender" 2>/dev/null || true)" /Applications/Blender.app/Contents/MacOS/Blender "$HOME/Applications/Blender.app/Contents/MacOS/Blender"; do
  [ -n "$c" ] && [ -x "$c" ] || continue
  v=$("$c" --version 2>/dev/null | head -1 || true); case "$v" in "Blender 5."*) BL="$c"; break;; esac
done
if [ -n "$BL" ]; then echo "  found $v"
else
  fetch https://download.blender.org/release/Blender5.2/blender-5.2.4-macos-arm64.dmg \
        e73d564f97061b2496ccc5a0bd738937d2d3d0acae23621a00bbc7534dfd135f "$DL/blender-5.2.4-macos-arm64.dmg"
  DEST=/Applications; [ -w /Applications ] || { DEST="$HOME/Applications"; mkdir -p "$DEST"; }
  APP="$DEST/Blender.app"; [ -e "$APP" ] && APP="$DEST/Blender 5.2.app"   # never overwrite another Blender
  MNT="$DL/mnt"; mkdir -p "$MNT"; hdiutil attach -nobrowse -readonly -mountpoint "$MNT" "$DL/blender-5.2.4-macos-arm64.dmg" >/dev/null </dev/null
  ditto "$MNT/Blender.app" "$APP"; hdiutil detach "$MNT" >/dev/null
  BL="$APP/Contents/MacOS/Blender"; echo "  installed $("$BL" --version 2>/dev/null | head -1 || true) at $APP"
fi
echo "$BL" > "$MS/blender"   # env.sh reads this first
ln -sf "$BL" "$LB/blender"     # so `blender -b -P ...` works in any new shell

step "2/7 ffmpeg + ffprobe"
has_ffmpeg() {   # capture first: with pipefail, `ffmpeg | grep -q` fails when grep stops reading early
  command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || return 1
  local f e; f=$(ffmpeg -hide_banner -filters 2>/dev/null || true); e=$(ffmpeg -hide_banner -encoders 2>/dev/null || true)
  grep -q ' subtitles ' <<<"$f" && grep -q ' xstack ' <<<"$f" && grep -q libx264 <<<"$e"; }
if has_ffmpeg; then echo "  found $(ffmpeg -hide_banner -version 2>/dev/null | head -1 | cut -c1-40 || true) with captions support"
else
  B=https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2
  fetch $B/ffmpeg.zip  c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924 "$DL/ffmpeg-9.0.2.zip"
  fetch $B/ffprobe.zip fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6 "$DL/ffprobe-9.0.2.zip"
  unzip -oq "$DL/ffmpeg-9.0.2.zip" -d "$LB" && unzip -oq "$DL/ffprobe-9.0.2.zip" -d "$LB"; chmod +x "$LB/ffmpeg" "$LB/ffprobe"
  hash -r; has_ffmpeg && echo "  installed ffmpeg 9.0.2 in $LB" || { echo "ffmpeg install failed"; exit 1; }
fi

step "3/7 uv"
if command -v uv >/dev/null; then echo "  found $(uv --version)"
else
  fetch https://github.com/astral-sh/uv/releases/download/0.13.8/uv-aarch64-apple-darwin.tar.gz \
        6b71028a6b904f2ae3340ef52e595512de807d06c0a20eaef2f692581b246558 "$DL/uv-0.13.8.tar.gz"
  tar -xzf "$DL/uv-0.13.8.tar.gz" -C "$DL" && cp "$DL"/uv-aarch64-apple-darwin/uv "$DL"/uv-aarch64-apple-darwin/uvx "$LB/"; hash -r; echo "  installed $(uv --version)"
fi

step "4/7 Node 22+"
NV=$( (node -v 2>/dev/null || echo v0) | sed 's/^v//; s/\..*//')
if [ "$NV" -ge 22 ]; then echo "  found Node $(node -v)"
else
  fetch https://nodejs.org/dist/v24.22.3/node-v24.22.3-darwin-arm64.tar.xz \
        1d64136c8a43d648d1b3bad10797a4c995b1ca032d2bde8799de43b37f058fe5 "$DL/node-v24.22.3.tar.xz"
  rm -rf "$MS/node"; mkdir -p "$MS/node"; tar -xJf "$DL/node-v24.22.3.tar.xz" -C "$MS/node" --strip-components 1
  for b in node npm npx; do ln -sf "$MS/node/bin/$b" "$LB/$b"; done; hash -r; echo "  installed Node $(node -v) (linked into $LB)"
fi

step "5/7 Python 3.12 + Whisper"
VP="$MS/venv/bin/python"
if [ -x "$VP" ] && "$VP" -c "import numpy, PIL, whisper, cv2" 2>/dev/null; then echo "  found $("$VP" --version) with numpy, pillow, whisper, opencv"
else
  [ -x "$VP" ] || uv venv --python 3.12 "$MS/venv"
  uv pip install --python "$VP" numpy==2.5.4 pillow==13.0.0 openai-whisper==20250625 torch==2.15.0 opencv-python-headless==4.14.0.94
  "$VP" -c "import numpy, PIL, whisper, cv2; print('  ok: numpy', numpy.__version__, 'pillow', PIL.__version__, 'opencv', cv2.__version__)"
fi

step "6/7 Whisper model"
if [ "$NO_MODEL" = 1 ]; then echo "  skipped (--no-model): it downloads on the first transcribe"
elif [ -f "$HOME/.cache/whisper/small.pt" ]; then echo "  found ~/.cache/whisper/small.pt"
else echo "  downloading the Whisper small model (about 460 MB)"; "$VP" -c "import whisper; whisper.load_model('small'); print('  downloaded the small model')"; fi

step "7/7 PATH + script permissions"
if grep -qs '\.local/bin' "$HOME/.zshrc" "$HOME/.zprofile"; then echo "  ~/.local/bin is already on your PATH"
else printf '\nexport PATH="$HOME/.local/bin:$PATH"   # make-short: ffmpeg, uv, node\n' >> "$HOME/.zshrc"; echo "  added ~/.local/bin to ~/.zshrc (new terminals and Claude Code sessions pick it up)"; fi
chmod +x "$SKILL"/v4/*.sh "$SKILL"/setup/*.sh 2>/dev/null || true

step "Health check"
bash "$SKILL/setup/check.sh" $SMOKE && printf '\nAll set. Quit Claude Code completely and open it again, then type:  /make-short <your idea>\n'
