"""CurioCut Autonomous Cloud Worker (Executed on Kaggle GPU / High-Compute Cloud).
This script runs in Kaggle's cloud environment with:
- NVIDIA Tesla T4 GPU (16 GB VRAM) / High-Speed Multi-Core vCPUs
- 30 GB System RAM
- Kokoro Neural TTS + Faster-Whisper millisecond subtitles
- Automatic Google Chrome Headless GPU Acceleration (via Xvfb + Hardware WebGL)
- Direct Publishing to YouTube Shorts & Instagram Reels
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

print("\n" + "="*70)
print("   CURIO CUT - AUTONOMOUS CLOUD EXECUTION WORKER   ")
print("="*70 + "\n")

# Check GPU availability
has_gpu = False
try:
    smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
    if smi.returncode == 0:
        has_gpu = True
        print("🚀 NVIDIA Hardware GPU Detected:")
        for line in smi.stdout.splitlines()[2:9]:
            print(f"   {line}")
    else:
        print("ℹ️ Running in High-Speed Multi-Core Cloud CPU mode.")
except Exception as e:
    print(f"ℹ️ GPU detection note: {e}")

WORKSPACE = Path("/kaggle/working/CurioCut")

# Step 1: Clone or pull repo
if not WORKSPACE.exists():
    print("\n[1/4] Cloning CurioCut repository...")
    subprocess.run(["git", "clone", "https://github.com/shlokkokk/CurioCut.git", str(WORKSPACE)], check=True)
else:
    print("\n[1/4] Updating CurioCut repository...")
    subprocess.run(["git", "-C", str(WORKSPACE), "pull"], check=False)

os.chdir(WORKSPACE)

# Step 2: Ensure Google Chrome and Xvfb Virtual Display are installed
print("\n[2/4] Verifying Google Chrome and Virtual GPU Display...")
chrome_path = shutil.which("google-chrome")
if not chrome_path:
    print("Downloading and installing official Google Chrome stable deb...")
    try:
        subprocess.run(["wget", "-q", "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"], check=True)
        subprocess.run(["apt-get", "update", "-y"], check=False)
        subprocess.run(["apt-get", "install", "-y", "./google-chrome-stable_current_amd64.deb", "xvfb"], check=True)
    except Exception as e:
        print(f"Package install notice: {e}")
    chrome_path = shutil.which("google-chrome") or "/usr/bin/google-chrome"
else:
    if not shutil.which("xvfb-run"):
        subprocess.run(["apt-get", "install", "-y", "xvfb"], check=False)

print(f"Browser ready: {chrome_path}")

# Step 3: Install Python Dependencies
print("\n[3/4] Installing Python dependencies...")
subprocess.run([
    sys.executable, "-m", "pip", "install", "--quiet",
    "-r", "requirements.txt",
    "kokoro-onnx", "faster-whisper", "groq", "requests"
], check=True)

# Restore YouTube Token if provided in environment
yt_token = os.environ.get("YOUTUBE_TOKEN_JSON")
if yt_token and not (WORKSPACE / "youtube_token.json").exists():
    (WORKSPACE / "youtube_token.json").write_text(yt_token, encoding="utf-8")
    print("Restored YouTube authentication token.")

# Step 4: Run autonomous 3D short generation & upload with Hardware GPU acceleration
print("\n[4/4] Starting 3D short generation and publishing with GPU acceleration...")
if shutil.which("xvfb-run"):
    cmd = ["xvfb-run", "-s", "-screen 0 1080x1920x24 -ac +extension GLX", sys.executable, "make_short.py", "--upload", "--privacy", "public"]
else:
    cmd = [sys.executable, "make_short.py", "--upload", "--privacy", "public"]

res = subprocess.run(cmd)

if res.returncode == 0:
    print("\n" + "="*70)
    print("🎉 SHORT SUCCESSFULLY CREATED AND PUBLISHED TO CLOUD!")
    print("="*70 + "\n")
else:
    print(f"\nWorker exited with error code {res.returncode}")
    sys.exit(res.returncode)
