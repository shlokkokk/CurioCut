# Cloud runner for rendering and uploading on Kaggle GPU
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
slot = os.environ.get("CURIO_SLOT", "auto").lower()
if "dev" in slot or "studio" in slot or "mascot" in slot:
    style_arg = "dev-studio"
elif "claude" in slot or "tech" in slot:
    style_arg = "claude-desk"
elif "tall" in slot or "tale" in slot or "story" in slot or "history" in slot or "slot1" in slot:
    style_arg = "tall-tale"
else:
    style_arg = "tall-tale"
print(f"\n[4/4] Starting 3D short generation (Slot: {slot} | Style: {style_arg})...", flush=True)

try:
    from discord_notifier import notify_engine, notify_error
    notify_engine(
        title="Cloud Video Engine Booted",
        description=f"GPU execution environment active for **{slot.upper()}**.",
        fields=[
            {"name": "Slot", "value": slot.upper(), "inline": True},
            {"name": "Visual Style", "value": style_arg.upper(), "inline": True},
            {"name": "Audio Engine", "value": "Dual Kokoro Stereo", "inline": True}
        ],
        color=0x10B981,
        button_label="View GitHub Repository",
        button_url="https://github.com/shlokkokk/CurioCut"
    )
except Exception:
    pass

cmd = [sys.executable, "make_short.py", "--style", style_arg, "--upload", "--privacy", "public"]
res = subprocess.run(cmd)

if res.returncode == 0:
    print("\n" + "="*70, flush=True)
    print("🎉 SHORT SUCCESSFULLY CREATED AND PUBLISHED TO CLOUD!", flush=True)
    print("="*70 + "\n", flush=True)
    # Note: Instagram Comment-to-DM is handled 24/7 in real-time by Cloudflare Edge Webhooks
else:
    print(f"\nWorker exited with error code {res.returncode}", flush=True)
    try:
        from discord_notifier import notify_error, update_live_progress
        update_live_progress(
            step_title="Cloud Worker Failed",
            percent=0,
            details=f"Pipeline aborted on cloud runner (exit code {res.returncode}). Check logs for details.",
            is_error=True
        )
        notify_error("Cloud Runner", f"Worker stopped with code {res.returncode}")
    except Exception:
        pass
    sys.exit(res.returncode)
