"""CurioCut Autonomous Cloud Worker (Executed on Kaggle GPU / High-Compute Cloud).
Hardened for zero-hang, non-interactive execution:
- Strict non-interactive package management (DEBIAN_FRONTEND=noninteractive)
- Subprocess timeout guards & unbuffered progress streaming
- Direct Google Chrome Headless 3D WebGL Acceleration
- Direct Publishing to YouTube Shorts & Instagram Reels
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Force unbuffered streaming & non-interactive execution
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["DEBIAN_FRONTEND"] = "noninteractive"

print("\n" + "="*70, flush=True)
print("   CURIO CUT - AUTONOMOUS CLOUD EXECUTION WORKER   ", flush=True)
print("="*70 + "\n", flush=True)

# Check GPU availability
try:
    smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=15)
    if smi.returncode == 0:
        print("🚀 NVIDIA Hardware GPU Detected:", flush=True)
        for line in smi.stdout.splitlines()[2:9]:
            print(f"   {line}", flush=True)
        os.environ["GPU_ACCEL"] = "1"
        os.environ["NVIDIA_DRIVER_CAPABILITIES"] = "compute,utility,graphics"
    else:
        print("ℹ️ Running in High-Speed Multi-Core Cloud CPU mode.", flush=True)
except Exception as e:
    print(f"ℹ️ GPU detection notice: {e}", flush=True)

WORKSPACE = Path("/kaggle/working/CurioCut")

# Step 1: Clone or pull repo
if not WORKSPACE.exists():
    print("\n[1/4] Cloning CurioCut repository...", flush=True)
    subprocess.run(["git", "clone", "https://github.com/shlokkokk/CurioCut.git", str(WORKSPACE)], check=True, timeout=300)
else:
    print("\n[1/4] Updating CurioCut repository...", flush=True)
    subprocess.run(["git", "-C", str(WORKSPACE), "pull"], check=False, timeout=300)

os.chdir(WORKSPACE)

# Step 2: Ensure Google Chrome is installed non-interactively
print("\n[2/4] Verifying Google Chrome...", flush=True)
chrome_path = shutil.which("google-chrome")
apt_flags = ["-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold"]

if not chrome_path:
    print("Downloading and installing official Google Chrome stable deb...", flush=True)
    try:
        subprocess.run(["wget", "-q", "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"], check=True, timeout=120)
        subprocess.run(["apt-get", "update", "-y"] + apt_flags, check=False, timeout=120)
        subprocess.run(["apt-get", "install", "-y"] + apt_flags + ["./google-chrome-stable_current_amd64.deb", "libegl1", "libgles2"], check=True, timeout=300)
    except Exception as e:
        print(f"Chrome install notice: {e}", flush=True)
    chrome_path = shutil.which("google-chrome") or "/usr/bin/google-chrome"

print(f"Browser ready: {chrome_path}", flush=True)

# Step 3: Install Python Dependencies
print("\n[3/4] Installing Python dependencies...", flush=True)
subprocess.run([
    sys.executable, "-m", "pip", "install", "--quiet",
    "-r", "requirements.txt",
    "kokoro-onnx", "faster-whisper", "groq", "requests"
], check=True, timeout=600)

# Restore YouTube Token if provided in environment
yt_token = os.environ.get("YOUTUBE_TOKEN_JSON")
if yt_token and not (WORKSPACE / "youtube_token.json").exists():
    (WORKSPACE / "youtube_token.json").write_text(yt_token, encoding="utf-8")
    print("Restored YouTube authentication token.", flush=True)

# Step 4: Run autonomous 3D short generation & upload
print("\n[4/4] Starting 3D short generation and publishing...", flush=True)
cmd = [sys.executable, "make_short.py", "--upload", "--privacy", "public"]
res = subprocess.run(cmd)

if res.returncode == 0:
    print("\n" + "="*70, flush=True)
    print("🎉 SHORT SUCCESSFULLY CREATED AND PUBLISHED TO CLOUD!", flush=True)
    print("="*70 + "\n", flush=True)
else:
    print(f"\nWorker exited with error code {res.returncode}", flush=True)
    sys.exit(res.returncode)
