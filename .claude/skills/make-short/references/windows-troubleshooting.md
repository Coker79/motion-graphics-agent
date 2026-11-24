# Windows troubleshooting

Run the health check first, in **Git Bash**:
```bash
bash ~/.claude/skills/make-short/setup/check.sh --smoke
```
Every FAIL line prints its fix. After installing anything, **close Claude Code and every terminal, then open them again**: Windows only reads a new PATH in new windows.

| What you see | Why | Fix |
|---|---|---|
| The installer window closes at once, or SmartScreen blocks it | Windows flags files from the internet | Unblock the zip (right-click it, choose Properties, tick Unblock) and extract it again. Or click **More info**, then **Run anyway** |
| Claude Code runs PowerShell instead of Git Bash, or says `bash` isn't found | Git for Windows wasn't installed when Claude Code started | The installer adds Portable Git and points Claude Code at it (`CLAUDE_CODE_GIT_BASH_PATH`). Quit Claude Code completely and open it again |
| Claude Code runs inside WSL (Linux) | this kit installs for Windows itself | Run Claude Code on Windows, not inside WSL |
| `Python was not found; run without arguments to install from the Microsoft Store` | `python3` reached the Windows Store stub instead of the kit's Python | Run **Install on Windows** again: it adds a `python3` command in `%USERPROFILE%\.make-short\bin`. Or turn off the `python3.exe` alias (Settings → Apps → Advanced app settings → App execution aliases) |
| `blender: command not found` | the `blender` command isn't on PATH | Run the installer again, or use Blender's full path. The `.sh` scripts find Blender themselves |
| `Blender 5.x not found` | Blender is in a folder the scripts don't look in | In Git Bash: `export BLENDER="/d/Apps/Blender 5.2/blender.exe"`, or run the installer again |
| `ffmpeg: command not found` | the PATH is stale | Close and reopen Claude Code. `ffmpeg -version` must work in Git Bash |
| `UnicodeDecodeError`, or captions with garbled quotes | Windows Python reads and writes text as cp1252 by default | Use the kit's `python3` (it sets `PYTHONUTF8=1`), or run `export PYTHONUTF8=1` |
| Files vanish, or are "in use", in Desktop or Documents | OneDrive sync or Controlled Folder Access | Keep Shorts in a plain folder such as `C:\shorts` |
| A long render stops halfway | the laptop went to sleep | Plug it in and set sleep to **Never** while it renders |
| A download fails with `CRYPT_E_NO_REVOCATION_CHECK` | antivirus HTTPS scanning | The installer retries without the revocation check, and the SHA-256 check still applies. Or pause the HTTPS scanning while it runs |
| Rendering is very slow on an external drive | exFAT and FAT32 drives have no hard links, so frames are copied | Keep projects on the internal NTFS drive |
| Captions use a plain font | Montserrat ExtraBold isn't installed | Install it from Google Fonts. If captions still look plain, right-click the .ttf and choose **Install for all users** (this needs an admin) |

## Making the `python3` command by hand
Only needed if you installed Python yourself. In Git Bash:
```bash
mkdir -p ~/.make-short/bin
printf '#!/bin/sh\nPYTHONUTF8=1 exec "%s" "$@"\n' "$(cygpath -u "$USERPROFILE")/.make-short/venv/Scripts/python.exe" > ~/.make-short/bin/python3
```
Then add `%USERPROFILE%\.make-short\bin` to your user PATH (Settings → System → About → Advanced system settings → Environment Variables).

Still stuck? Copy the last 20 lines of the error into Claude Code and say "fix this". Never paste API keys anywhere: this skill needs none.
