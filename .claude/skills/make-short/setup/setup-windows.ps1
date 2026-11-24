# setup-windows.ps1: installs make-short AND everything it needs on a Windows 10/11 PC. No admin rights needed.
#
# Easiest: open the make-short folder and double-click "Install on Windows.cmd". Or, in PowerShell:
#   powershell -NoProfile -ExecutionPolicy Bypass -File "<make-short folder>\setup\setup-windows.ps1" [-NoModel] [-Smoke]
# Safe to run again: it skips anything already installed. It never asks for input (unless -Pause), so Claude Code
# can run it for you, in the background: it takes 10-30 minutes. -Smoke ends with a real Blender render (about 1 minute).
#
# What it installs (every download is checked against a pinned SHA-256; about 4 GB of disk):
#   the skill itself         -> %USERPROFILE%\.claude\skills\make-short  (when you run it from somewhere else, e.g. Downloads)
#   Blender 5.2.4 LTS         -> %USERPROFILE%\.make-short\apps          (skipped if Blender 5.x is already installed)
#   ffmpeg + ffprobe 9.0.2    -> %USERPROFILE%\.make-short\bin           (gyan.dev essentials build, with captions support)
#   uv 0.13.8                 -> %USERPROFILE%\.make-short\bin           (sets up Python)
#   Python 3.12 + Whisper     -> %USERPROFILE%\.make-short\venv          (numpy, pillow, opencv, openai-whisper)
#   Git Bash commands         -> %USERPROFILE%\.make-short\bin           (python3 and blender, for the scripts and Claude Code)
#   Node 24                   -> %USERPROFILE%\.make-short\apps          (only if you don't have Node 22 or newer)
#   Git Bash (Portable Git)   -> %USERPROFILE%\.make-short\apps\git      (only if Git for Windows isn't installed)
#   Whisper "small" model     -> %USERPROFILE%\.cache\whisper            (about 460 MB; skip with -NoModel)
# It adds those folders to YOUR user PATH (not the system PATH), then runs the health check.
# Written for Windows PowerShell 5.1 (built into Windows 10 and 11). Keep this file plain ASCII.

param([switch]$NoModel, [switch]$Pause, [switch]$Smoke)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$MS   = Join-Path $env:USERPROFILE '.make-short'
$Bin  = Join-Path $MS 'bin'
$Apps = Join-Path $MS 'apps'
$DL   = Join-Path $MS 'downloads'
$script:PathAdd = @()
# run by Claude Code (output piped, not a console window): plain download lines instead of progress bars
$Bar = '--progress-bar'
try { if ([Console]::IsErrorRedirected) { $Bar = '-sS'; $env:TQDM_DISABLE = '1' } } catch { }

function Step([string]$t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Say([string]$t)  { Write-Host "  $t" }
function Done([int]$code) {
    if ($Pause) { Write-Host ''; [void](Read-Host 'Press Enter to close this window') }
    exit $code
}
function Stop-Setup([string]$t) { Write-Host ''; Write-Host "STOPPED: $t" -ForegroundColor Red; Done 1 }

# run a program and return its output lines; never throws, even if it writes to stderr
function NativeOut([string]$exe, [string[]]$argList) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $o = & $exe @argList 2>$null } catch { $o = @() } finally { $ErrorActionPreference = $old }
    return @($o)
}

# run a program, show its output, return its exit code; stderr output never aborts the script
function Run([string]$exe, [string[]]$argList) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { & $exe @argList 2>&1 | ForEach-Object { Write-Host "  $_" } } finally { $ErrorActionPreference = $old }
    return $LASTEXITCODE
}

function Get-Sha256([string]$f) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLower() }

# download once, verify the pinned SHA-256, keep it in downloads\
function Fetch([string]$url, [string]$sha, [string]$out) {
    if ((Test-Path -LiteralPath $out) -and ((Get-Sha256 $out) -eq $sha)) { Say "cached $(Split-Path $out -Leaf)"; return }
    Say "downloading $(Split-Path $out -Leaf)"
    $part = "$out.part"
    if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        & curl.exe -fL --retry 3 $Bar -o $part $url
        $rc = $LASTEXITCODE
        if ($rc -ne 0) {   # antivirus HTTPS scanning can break the certificate revocation check; the SHA-256 check below still applies
            Say 'retrying without the certificate revocation check'
            & curl.exe -fL --retry 3 --ssl-no-revoke $Bar -o $part $url
            $rc = $LASTEXITCODE
        }
        $ErrorActionPreference = $old
        if ($rc -ne 0) { Stop-Setup "download failed: $url" }
    } else {
        Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $part
    }
    if ((Get-Sha256 $part) -ne $sha) { Remove-Item -Force -LiteralPath $part; Stop-Setup "checksum mismatch for $url (nothing was installed from it)" }
    Move-Item -Force -LiteralPath $part -Destination $out
    Say ('got {0} ({1:N0} MB, checksum OK)' -f (Split-Path $out -Leaf), ((Get-Item -LiteralPath $out).Length / 1MB))
}

function Unzip([string]$zip, [string]$dest) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    if (Get-Command tar.exe -ErrorAction SilentlyContinue) {
        if ((Run 'tar.exe' @('-xf', $zip, '-C', $dest)) -ne 0) { Stop-Setup "could not unpack $zip" }
    } else {
        Expand-Archive -Force -LiteralPath $zip -DestinationPath $dest
    }
}

# Windows path -> Git Bash path, e.g. D:\My Shorts\x -> /d/My Shorts/x  (the form the bash scripts read)
function MsysPath([string]$p) { return '/' + $p.Substring(0, 1).ToLower() + ($p.Substring(2) -replace '\\', '/') }
function WinPath([string]$p)  { if ($p -match '^/([a-zA-Z])/(.*)$') { return ($Matches[1].ToUpper() + ':\' + ($Matches[2] -replace '/', '\')) } return $p }

function Write-Text([string]$file, [string]$text) { [IO.File]::WriteAllText($file, $text) }   # UTF-8, no BOM

function Add-UserPath([string[]]$dirs) {
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
    $raw = [string]$key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
    $parts = @($raw -split ';' | Where-Object { $_ -ne '' })
    $new = @($dirs | Where-Object { $parts -notcontains $_ })
    if ($new.Count -gt 0) {
        $key.SetValue('Path', (($new + $parts) -join ';'), [Microsoft.Win32.RegistryValueKind]::ExpandString)
        Say ('added to your PATH: ' + ($new -join ', '))
        # tell Windows the environment changed, so newly opened apps (and Claude Code) see it
        if (-not ('MakeShort.Win32' -as [type])) {
            Add-Type -Namespace MakeShort -Name Win32 -MemberDefinition '[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);'
        }
        $r = [UIntPtr]::Zero
        [void][MakeShort.Win32]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, 'Environment', 2, 5000, [ref]$r)
    } else { Say 'your PATH already has the make-short folders' }
    $key.Close()
    $env:Path = ($dirs -join ';') + ';' + $env:Path
}

try {
    Write-Host 'make-short setup for Windows' -ForegroundColor Cyan
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { Stop-Setup "this setup is for 64-bit Intel/AMD PCs; this PC is $($env:PROCESSOR_ARCHITECTURE)." }
    New-Item -ItemType Directory -Force -Path $MS, $Bin, $Apps, $DL | Out-Null
    $drive = Get-PSDrive -Name ($env:USERPROFILE.Substring(0, 1))
    if ($drive -and $drive.Free -and ($drive.Free -lt 5GB)) { Stop-Setup ('only {0:N1} GB free on {1}:; setup needs about 5 GB.' -f ($drive.Free / 1GB), $drive.Name) }

    Step '0/8 The skill'
    $SkillSrc = (Split-Path -Parent $PSScriptRoot).TrimEnd('\')
    $SkillDst = Join-Path $env:USERPROFILE '.claude\skills\make-short'
    if ($SkillSrc -eq $SkillDst) { Say "running from $SkillDst" }
    else {
        if (Test-Path -LiteralPath $SkillDst) {
            $bak = Join-Path $MS ('backups\make-short-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
            New-Item -ItemType Directory -Force -Path (Split-Path $bak) | Out-Null
            Move-Item -LiteralPath $SkillDst -Destination $bak
            Say "your previous make-short was moved to $bak"
        }
        New-Item -ItemType Directory -Force -Path (Split-Path $SkillDst) | Out-Null
        Copy-Item -Recurse -LiteralPath $SkillSrc -Destination $SkillDst
        Say "installed the skill to $SkillDst"
    }
    Get-ChildItem -LiteralPath $SkillDst -Recurse -File | Unblock-File -ErrorAction SilentlyContinue   # clear the downloaded-from-internet flag

    Step '1/8 Git Bash (runs the skill''s scripts)'
    $bash = $null
    $cands = @($env:CLAUDE_CODE_GIT_BASH_PATH, "$env:ProgramFiles\Git\bin\bash.exe", "${env:ProgramFiles(x86)}\Git\bin\bash.exe",
               "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe", (Join-Path $Apps 'git\bin\bash.exe'))
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($git) { $cands += (Join-Path (Split-Path (Split-Path $git.Source)) 'bin\bash.exe') }
    foreach ($c in $cands) { if ($c -and (Test-Path -LiteralPath $c)) { $bash = $c; break } }
    if ($bash) { Say "found $bash" }
    else {
        $pg = Join-Path $DL 'PortableGit-2.56.1-64-bit.7z.exe'
        Fetch 'https://github.com/git-for-windows/git/releases/download/v2.56.1.windows.1/PortableGit-2.56.1-64-bit.7z.exe' '9dd04a608ceb5f6ab32a73709e0ecb159d211da71b697c45ff81f6dd0c6b49c7' $pg
        $gitDir = Join-Path $Apps 'git'
        $p = Start-Process -FilePath $pg -ArgumentList @("-o`"$gitDir`"", '-y') -Wait -PassThru -WindowStyle Hidden
        if ($p.ExitCode -ne 0) { Stop-Setup 'could not unpack Portable Git' }
        $bash = Join-Path $gitDir 'bin\bash.exe'
        if (-not (Test-Path -LiteralPath $bash)) { Stop-Setup 'Portable Git unpacked but bash.exe is missing' }
        [Environment]::SetEnvironmentVariable('CLAUDE_CODE_GIT_BASH_PATH', $bash, 'User')   # lets Claude Code find this Git Bash
        $script:PathAdd += (Join-Path $gitDir 'cmd')
        Say "installed Git Bash at $bash"
    }

    Step '2/8 Blender 5.2'
    $blender = $null
    $cands = @()
    $saved = Join-Path $MS 'blender'
    if (Test-Path -LiteralPath $saved) { $cands += (WinPath ((Get-Content -LiteralPath $saved -Raw).Trim())) }
    $cands += @(Get-ChildItem -Path "$env:ProgramFiles\Blender Foundation\Blender 5.*\blender.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object { $_.FullName })
    $cands += "${env:ProgramFiles(x86)}\Steam\steamapps\common\Blender\blender.exe"
    $cands += @(Get-ChildItem -Path "$Apps\blender-5.*\blender.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object { $_.FullName })
    foreach ($c in $cands) {
        if ($c -and (Test-Path -LiteralPath $c)) {
            $v = (NativeOut $c @('--version') | Select-Object -First 1)
            if ("$v" -like 'Blender 5.*') { $blender = $c; Say "found $v at $c"; break }
        }
    }
    if (-not $blender) {
        $z = Join-Path $DL 'blender-5.2.4-windows-x64.zip'
        Fetch 'https://download.blender.org/release/Blender5.2/blender-5.2.4-windows-x64.zip' 'bbd78f8931dc940444da4ff2983374930f9f5c092ae0e330588e9760bb9d967c' $z
        Say 'unpacking Blender (a few minutes)'
        Unzip $z $Apps
        $blender = Join-Path $Apps 'blender-5.2.4-windows-x64\blender.exe'
        if (-not (Test-Path -LiteralPath $blender)) {   # in case the zip's folder name ever differs
            $found = Get-ChildItem -LiteralPath $Apps -Recurse -Depth 2 -Filter blender.exe -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $blender = $found.FullName } else { Stop-Setup 'Blender unpacked but blender.exe is missing' }
        }
        Say "installed $(NativeOut $blender @('--version') | Select-Object -First 1)"
    }
    Write-Text $saved (MsysPath $blender)   # env.sh reads this

    Step '3/8 ffmpeg + ffprobe'
    $ok = $false
    if ((Get-Command ffmpeg.exe -ErrorAction SilentlyContinue) -and (Get-Command ffprobe.exe -ErrorAction SilentlyContinue)) {
        $f = (NativeOut 'ffmpeg.exe' @('-hide_banner', '-filters')) -join "`n"
        $e = (NativeOut 'ffmpeg.exe' @('-hide_banner', '-encoders')) -join "`n"
        $ok = ($f -match ' subtitles ') -and ($f -match ' xstack ') -and ($e -match 'libx264')
    }
    if ($ok) { Say 'found ffmpeg with captions support' }
    else {
        $z = Join-Path $DL 'ffmpeg-9.0.2-essentials_build.zip'
        Fetch 'https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-essentials_build.zip' '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba' $z
        $tmp = Join-Path $DL 'ffmpeg-unpacked'
        Unzip $z $tmp
        Copy-Item -Force (Join-Path $tmp 'ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe'), (Join-Path $tmp 'ffmpeg-9.0.2-essentials_build\bin\ffprobe.exe') $Bin
        Remove-Item -Recurse -Force -LiteralPath $tmp
        Say "installed ffmpeg 9.0.2 in $Bin"
    }

    Step '4/8 uv'
    if (Get-Command uv.exe -ErrorAction SilentlyContinue) { $uv = (Get-Command uv.exe).Source; Say "found $(NativeOut $uv @('--version'))" }
    else {
        $z = Join-Path $DL 'uv-0.13.8-windows.zip'
        Fetch 'https://github.com/astral-sh/uv/releases/download/0.13.8/uv-x86_64-pc-windows-msvc.zip' '529e78a9cec6cd7e3e014f7ecd8bda0c113969d4ed0f2efeedb85c30943325b8' $z
        Unzip $z $Bin
        $uv = Join-Path $Bin 'uv.exe'
        Say "installed $(NativeOut $uv @('--version'))"
    }

    Step '5/8 Node 22+'
    $nodeMajor = 0
    $nodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($nodeCmd) { $nv = "$(NativeOut $nodeCmd.Source @('-v'))"; if ($nv -match '^v(\d+)') { $nodeMajor = [int]$Matches[1] } }
    if ($nodeMajor -ge 22) { Say "found Node $nv" }
    else {
        $z = Join-Path $DL 'node-v24.22.3-win-x64.zip'
        Fetch 'https://nodejs.org/dist/v24.22.3/node-v24.22.3-win-x64.zip' 'e612af99f626ab415ea225af6bce5c971feb448cb5cae250bb1c3fa50c5f7d9f' $z
        Unzip $z $Apps
        $nodeDir = Join-Path $Apps 'node-v24.22.3-win-x64'
        $script:PathAdd += $nodeDir
        Say "installed Node $(NativeOut (Join-Path $nodeDir 'node.exe') @('-v'))"
    }

    Step '6/8 Python 3.12 + Whisper'
    $py = Join-Path $MS 'venv\Scripts\python.exe'
    $have = $false
    if (Test-Path -LiteralPath $py) { [void](NativeOut $py @('-c', 'import numpy, PIL, whisper, cv2')); $have = ($LASTEXITCODE -eq 0) }
    if ($have) { Say 'found Python with numpy, pillow, whisper and opencv' }
    else {
        if (-not (Test-Path -LiteralPath $py)) {
            if ((Run $uv @('venv', '--python', '3.12', (Join-Path $MS 'venv'))) -ne 0) { Stop-Setup 'could not create the Python environment' }
        }
        if ((Run $uv @('pip', 'install', '--python', $py, 'numpy==2.5.4', 'pillow==13.0.0', 'openai-whisper==20250625', 'torch==2.15.0', 'opencv-python-headless==4.14.0.94')) -ne 0) { Stop-Setup 'could not install the Python packages' }
        if ((Run $py @('-c', "import numpy, PIL, whisper, cv2; print('ok: numpy', numpy.__version__, 'pillow', PIL.__version__, 'opencv', cv2.__version__)")) -ne 0) { Stop-Setup 'Python packages installed but do not import' }
    }

    Step '7/8 Whisper model'
    $model = Join-Path $env:USERPROFILE '.cache\whisper\small.pt'
    if ($NoModel) { Say 'skipped (-NoModel): it downloads on the first transcribe' }
    elseif (Test-Path -LiteralPath $model) { Say "found $model" }
    else {
        Say 'downloading the Whisper model (about 460 MB)'
        if ((Run $py @('-c', "import whisper; whisper.load_model('small'); print('downloaded the small model')")) -ne 0) { Stop-Setup 'could not download the Whisper model (try again, or run with -NoModel)' }
    }

    Step '8/8 PATH'
    # Git Bash commands: python3 (a Windows venv has only python.exe, and python3 would reach the Microsoft Store stub) and blender
    Write-Text (Join-Path $Bin 'python3') ("#!/bin/sh`n" + 'PYTHONUTF8=1 exec "$(dirname "$0")/../venv/Scripts/python.exe" "$@"' + "`n")
    Write-Text (Join-Path $Bin 'blender') ("#!/bin/sh`n" + 'exec "$(cat "$(dirname "$0")/../blender")" "$@"' + "`n")
    Say 'added the python3 and blender commands for Git Bash'
    Add-UserPath (@($Bin, (Join-Path $MS 'venv\Scripts')) + $script:PathAdd)

    Step 'Health check'
    if (-not $env:HOME) { $env:HOME = $env:USERPROFILE }   # Git Bash turns this into /c/Users/<you>
    $ErrorActionPreference = 'Continue'
    $checkArgs = @(MsysPath (Join-Path $SkillDst 'setup\check.sh'))
    if ($Smoke) { $checkArgs += '--smoke' }
    & $bash @checkArgs
    $rc = $LASTEXITCODE
    Write-Host ''
    if ($rc -eq 0) { Write-Host 'All set. Quit Claude Code completely and open it again, then type:  /make-short <your idea>' -ForegroundColor Green }
    else { Write-Host 'Setup finished, but the health check found a problem (see above).' -ForegroundColor Yellow }
    Done $rc
} catch {
    Stop-Setup ($_ | Out-String)
}
