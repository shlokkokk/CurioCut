# Faceless Shorts Windows Setup Script
# Downloads portable Node.js 22, portable FFmpeg, sets up Python venv with Kokoro ONNX and faster-whisper.

$ErrorActionPreference = "Stop"

$FacelessHome = Join-Path $HOME ".faceless-shorts"
$BinDir = Join-Path $FacelessHome "bin"
$KokoroDir = Join-Path $FacelessHome "kokoro"
$VenvDir = Join-Path $FacelessHome "venv"
$TmpDir = Join-Path $FacelessHome "tmp"

New-Item -ItemType Directory -Force -Path $BinDir, $KokoroDir, $TmpDir | Out-Null

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   Setting up Faceless Shorts Engine for Windows    " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Portable Node.js v22
$NodeExe = Join-Path $BinDir "node.exe"
if (-not (Test-Path $NodeExe)) {
    Write-Host "`n[1/4] Downloading portable Node.js v22..." -ForegroundColor Yellow
    $NodeZip = Join-Path $TmpDir "node.zip"
    $NodeUrl = "https://nodejs.org/dist/v22.14.0/node-v22.14.0-win-x64.zip"
    curl.exe -L -o $NodeZip $NodeUrl
    
    Write-Host "Extracting Node.js..." -ForegroundColor Yellow
    $NodeExtract = Join-Path $TmpDir "node-extract"
    if (Test-Path $NodeExtract) { Remove-Item -Recurse -Force $NodeExtract }
    Expand-Archive -Path $NodeZip -DestinationPath $NodeExtract -Force
    
    $ExtractedNodeDir = Join-Path $NodeExtract "node-v22.14.0-win-x64"
    Get-ChildItem -Path $ExtractedNodeDir | Copy-Item -Destination $BinDir -Recurse -Force
    Remove-Item -Force $NodeZip
    Remove-Item -Recurse -Force $NodeExtract
    Write-Host "Node.js installed successfully." -ForegroundColor Green
} else {
    Write-Host "`n[1/4] Node.js is already installed in $BinDir" -ForegroundColor Green
}

# 2. Portable FFmpeg
$FfmpegExe = Join-Path $BinDir "ffmpeg.exe"
$FfprobeExe = Join-Path $BinDir "ffprobe.exe"
if ((-not (Test-Path $FfmpegExe)) -or (-not (Test-Path $FfprobeExe))) {
    Write-Host "`n[2/4] Downloading portable FFmpeg..." -ForegroundColor Yellow
    $FfmpegZip = Join-Path $TmpDir "ffmpeg.zip"
    $FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    curl.exe -L -o $FfmpegZip $FfmpegUrl
    
    Write-Host "Extracting FFmpeg..." -ForegroundColor Yellow
    $FfmpegExtract = Join-Path $TmpDir "ffmpeg-extract"
    if (Test-Path $FfmpegExtract) { Remove-Item -Recurse -Force $FfmpegExtract }
    Expand-Archive -Path $FfmpegZip -DestinationPath $FfmpegExtract -Force
    
    # Locate bin/ffmpeg.exe and bin/ffprobe.exe inside the extracted folder
    $FoundFfmpeg = Get-ChildItem -Path $FfmpegExtract -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    $FoundFfprobe = Get-ChildItem -Path $FfmpegExtract -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
    
    if ($FoundFfmpeg -and $FoundFfprobe) {
        Copy-Item -Path $FoundFfmpeg.FullName -Destination $BinDir -Force
        Copy-Item -Path $FoundFfprobe.FullName -Destination $BinDir -Force
        Write-Host "FFmpeg & FFprobe installed successfully." -ForegroundColor Green
    } else {
        throw "Could not find ffmpeg.exe or ffprobe.exe in the extracted archive."
    }
    Remove-Item -Force $FfmpegZip
    Remove-Item -Recurse -Force $FfmpegExtract
} else {
    Write-Host "`n[2/4] FFmpeg is already installed in $BinDir" -ForegroundColor Green
}

# Add $BinDir to current process PATH and User PATH
$env:Path = "$BinDir;$env:Path"
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    Write-Host "Adding $BinDir to User Environment PATH..." -ForegroundColor Cyan
    [Environment]::SetEnvironmentVariable("Path", "$BinDir;$UserPath", "User")
}

# 3. Python Virtual Environment
$PyVenv = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $PyVenv)) {
    Write-Host "`n[3/4] Creating Python virtual environment in $VenvDir..." -ForegroundColor Yellow
    python -m venv $VenvDir
} else {
    Write-Host "`n[3/4] Python virtual environment exists in $VenvDir" -ForegroundColor Green
}

Write-Host "Installing/Verifying Python packages (numpy, scipy, kokoro-onnx, faster-whisper)..." -ForegroundColor Yellow
& $PyVenv -m pip install -q --upgrade pip
& $PyVenv -m pip install -q numpy scipy kokoro-onnx faster-whisper

# 4. Local Models (Kokoro & Whisper)
Write-Host "`n[4/4] Downloading AI Models (Kokoro TTS & Whisper)..." -ForegroundColor Yellow
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VoicePy = Join-Path $ScriptDir "voice.py"

& $PyVenv $VoicePy --download

Write-Host "Pre-caching Whisper small.en model..." -ForegroundColor Yellow
& $PyVenv -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8'); print('Whisper model loaded successfully.')"

Write-Host "`n====================================================" -ForegroundColor Green
Write-Host "           ALL SET! ENGINE READY TO GO              " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "Node:   $(& $NodeExe -v)" -ForegroundColor Cyan
Write-Host "FFmpeg: $(& $FfmpegExe -version | Select-Object -First 1)" -ForegroundColor Cyan
Write-Host "Python: $(& $PyVenv --version)" -ForegroundColor Cyan

