# Install make-short

> **Claude Code only.** It runs Blender, Python and ffmpeg on your own computer, so it does not work as a claude.ai Skills upload.

## The easy way: ask Claude Code
1. Download the zip and leave it zipped. Safari unzips downloads by itself; if yours did, use the `make-short` folder instead of the zip.
2. Open Claude Code (the desktop app's Code tab, or `claude` in a terminal) and start a new session in any folder.
3. Drag the zip into the message box (or click **+** and choose it), then send:

   **Install this skill and everything it needs.**

Claude unzips it, reads this file and runs the installer for your computer. Approve its commands when it asks. If your Mac asks whether Claude may open your Downloads folder, click **Allow**.

- **The first install downloads about 1–1.5 GB** (Blender is a third of it) and takes about 10–30 minutes.
- **It ends with READY and All set.** Then quit Claude Code completely, open it again, and type `/make-short <your idea>`.
- **No admin password.**
- **Safe to run again:** it skips anything already installed.
- **Pinned downloads:** every direct download (Blender, ffmpeg, uv, Node, Git) is checked against a pinned SHA-256, and every Python package is pinned by version.

**Supported:** Macs with Apple Silicon (M1 or newer) on macOS 14 or later, and 64-bit Windows 10 or 11. Intel Macs, Linux and WSL are not supported.

## For Claude Code: how to install this
The user asked you to install this skill and everything it needs. The installers need no admin password and never ask for input.
1. **Unzip it next to the zip.** Skip this if you were given the unzipped `make-short` folder.
   - macOS: `unzip -oq "<zip>" -d "<folder>"`
   - Windows (Git Bash or PowerShell): `powershell -NoProfile -Command "Expand-Archive -Force -LiteralPath '<zip>' -DestinationPath '<folder>'"`
2. **Read the installer before you run it.** On a Mac that is `make-short/setup/setup-mac.sh`; on Windows, `make-short/setup/setup-windows.ps1`. Tell the user in one line what it installs; its header lists everything.
3. **Run it in the background.** It takes 10–30 minutes.
   - macOS: `bash "<folder>/make-short/setup/setup-mac.sh" --smoke`
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "<folder>\make-short\setup\setup-windows.ps1" -Smoke`. From Git Bash, convert the path with `cygpath -w`.
   - Don't run `Install on Windows.cmd`: it waits for a key press.
   - The installer copies the skill into `~/.claude/skills/make-short` itself and moves an older copy to `~/.make-short/backups`. Don't copy the folder there yourself.
   - It writes outside the session's folder and downloads from the internet. If your sandbox is on, run it outside the sandbox.
4. **Check that it worked.** The output must end with `READY` and `All set`. If it stops, read the error and fix its cause (on Windows, `references/windows-troubleshooting.md` lists the usual ones). Then run the same command again: it keeps finished downloads and skips whatever is installed.
5. **Tell the user three things:**
   - quit Claude Code completely and open it again, so it picks up the new PATH;
   - add the Higgsfield connector in Claude's settings (Settings → Connectors) for the voice, music, sound effects and character sheets;
   - type `/make-short <your idea>`.

On an Intel Mac, on Linux or inside WSL, stop and tell the user this kit doesn't support that computer.

## Install by hand
### Mac (Apple Silicon, M1 or newer, macOS 14 or later)
Unzip the download, then in Terminal:
```bash
bash ~/Downloads/make-short/setup/setup-mac.sh
```
It installs:
- **Blender 5.2.4**, in /Applications (or ~/Applications);
- **ffmpeg 9.0.2 and uv**, in `~/.local/bin`;
- **Python 3.12** with numpy, pillow, OpenCV and Whisper, in `~/.make-short/venv`;
- **Node 24**, only if you don't have Node 22 or newer.

It also adds `~/.local/bin` to your PATH in `~/.zshrc` and links the `blender` command there.

### Windows 10/11 (64-bit)
1. Right-click the zip, choose **Properties**, tick **Unblock**, then **OK**. This stops SmartScreen from blocking the installer.
2. Right-click the zip, choose **Extract All**, open the extracted `make-short` folder and double-click **Install on Windows**. If a blue SmartScreen box still appears, click **More info**, then **Run anyway**.

Or, in PowerShell:
```
powershell -NoProfile -ExecutionPolicy Bypass -File "<make-short folder>\setup\setup-windows.ps1"
```
It installs only what is missing, into `%USERPROFILE%\.make-short`:
- **Blender 5.2.4**;
- **ffmpeg 9.0.2** (the gyan.dev build);
- **uv**;
- **Python 3.12** with numpy, pillow, OpenCV and Whisper;
- **Node 24**;
- **Git Bash** (Portable Git), only if you don't have Git for Windows.

It also adds the `python3` and `blender` commands for Git Bash (the shell Claude Code uses on Windows once Git is installed) and adds its folders to your user PATH. It ends with the health check.

**Keep your Shorts in a plain folder** such as `C:\shorts`. OneDrive-synced Desktop and Documents folders can lock files mid-render.

## Then
Quit Claude Code completely, open it again, then type `/make-short <your idea>`.

To check your setup any time (on Windows, run it in Git Bash):
```bash
bash ~/.claude/skills/make-short/setup/check.sh --smoke
```
It builds one toy character in Blender, renders its turnaround, and ends with **READY**.

## Higgsfield
Character sheets, the voice, the music and the sound effects come from the Higgsfield connector in your Claude account (Settings → Connectors). Claude asks for a credit budget once per Short.

## If the setup script can't run
Install these yourself, then run the health check above.

| Tool | Version | Notes |
|---|---|---|
| Blender | 5.2 (any 5.x) | Mac: /Applications/Blender.app. Windows: any folder; set `BLENDER` to the full path of blender.exe if it isn't in `C:\Program Files\Blender Foundation\Blender 5.x\` |
| ffmpeg + ffprobe | 7 or newer, with libass and libx264 | on PATH |
| Python | 3.12 with `numpy pillow opencv-python-headless openai-whisper` | Mac: in `~/.make-short/venv`. Windows: in `%USERPROFILE%\.make-short\venv`, plus a `python3` command for Git Bash (see `references/windows-troubleshooting.md`) |
| Git Bash | Windows only | from Git for Windows |
| Caption font | Montserrat ExtraBold (optional) | free from Google Fonts; without it, captions fall back to a system font |

Problems on Windows: see `references/windows-troubleshooting.md`.
