# Cloud runner for rendering and uploading on Kaggle GPU
import os
import sys
import time
import shutil
import subprocess
import json
import urllib.request
import threading
from pathlib import Path

# Force unbuffered streaming & completely non-interactive package execution
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["DEBIAN_FRONTEND"] = "noninteractive"
os.environ["NEEDRESTART_MODE"] = "a"
os.environ["NEEDRESTART_SUSPEND"] = "1"

# Suppress Ubuntu needrestart interactive service dialogs completely
try:
    needrestart_dir = Path("/etc/needrestart/conf.d")
    needrestart_dir.mkdir(parents=True, exist_ok=True)
    (needrestart_dir / "override.conf").write_text("$nrconf{restart} = 'l';\n$nrconf{ui} = 'NeedRestart::UI::stdio';\n", encoding="utf-8")
except Exception:
    pass

print("\n" + "="*70, flush=True)
print("   CURIO CUT - AUTONOMOUS CLOUD EXECUTION WORKER   ", flush=True)
print("="*70 + "\n", flush=True)

# Check GPU availability
try:
    smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=15)
    if smi.returncode == 0:
        print("[GPU] NVIDIA Hardware GPU Detected:", flush=True)
        for line in smi.stdout.splitlines()[2:9]:
            print(f"   {line}", flush=True)
        os.environ["GPU_ACCEL"] = "1"
        os.environ["NVIDIA_DRIVER_CAPABILITIES"] = "compute,utility,graphics"
    else:
        print("[INFO] Running in High-Speed Multi-Core Cloud CPU mode.", flush=True)
except Exception as e:
    print(f"[INFO] GPU detection notice: {e}", flush=True)

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
if "dev" in slot or "studio" in slot or "mascot" in slot or "slot3" in slot:
    style_arg = "dev-studio"
elif "claude" in slot or "tech" in slot or "slot2" in slot:
    style_arg = "claude-desk"
elif "night" in slot or "crime" in slot or "mystery" in slot:
    style_arg = "night-file"
elif "atlas" in slot or "paper" in slot or "history" in slot:
    style_arg = "paper-atlas"
elif "dive" in slot or "science" in slot or "body" in slot:
    style_arg = "deep-dive"
elif "tall" in slot or "tale" in slot:
    style_arg = "tall-tale"
elif "town" in slot or "rule" in slot or "roblox" in slot or "story" in slot:
    style_arg = "town-rule"
else:
    style_arg = "auto"

if style_arg == "town-rule":
    # Configure NVIDIA EGL headless hardware acceleration for Tesla T4 GPU
    os.environ["NVIDIA_VISIBLE_DEVICES"] = "all"
    os.environ["NVIDIA_DRIVER_CAPABILITIES"] = "all"
    os.environ["EGL_PLATFORM"] = "surfaceless"
    os.environ["EGL_DRIVER"] = "nvidia"
    os.environ["__EGL_VENDOR_LIBRARY_DIRS"] = "/usr/share/glvnd/egl_vendor.d"
    for nvidia_json in [
        "/usr/share/glvnd/egl_vendor.d/10_nvidia.json",
        "/etc/glvnd/egl_vendor.d/10_nvidia.json",
    ]:
        if os.path.exists(nvidia_json):
            os.environ["__EGL_VENDOR_LIBRARY_FILENAMES"] = nvidia_json
            os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
            os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"
            break

    if not shutil.which("blender"):
        blender_dir = Path("/kaggle/working/blender")
        blender_bin = blender_dir / "blender-4.3.2-linux-x64" / "blender"
        if not blender_bin.exists():
            print("[3b/4] Installing portable Blender 4.3.2 for Linux GPU rendering...", flush=True)
            blender_dir.mkdir(parents=True, exist_ok=True)
            tar_path = blender_dir / "blender-4.3.2-linux-x64.tar.xz"
            subprocess.run(["curl", "-L", "-s", "https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz", "-o", str(tar_path)], check=True)
            subprocess.run(["tar", "-xf", str(tar_path), "-C", str(blender_dir)], check=True)
            tar_path.unlink(missing_ok=True)
        subprocess.run(["chmod", "+x", str(blender_bin)], check=False)
        test_res = subprocess.run([str(blender_bin), "--version"], capture_output=True, text=True)
        if test_res.returncode != 0:
            print(f"Installing missing Linux libraries for Blender: {test_res.stderr.strip()}", flush=True)
            nonint_env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", NEEDRESTART_MODE="a", NEEDRESTART_SUSPEND="1")
            subprocess.run(["apt-get", "update", "-y", "-q"] + apt_flags, env=nonint_env, check=False)
            subprocess.run(["apt-get", "install", "-y", "-q"] + apt_flags + [
                "libgl1", "libegl1", "libgles2", "libglvnd0", "libglvnd-dev",
                "libsm6", "libxext6", "libxrender1", "libxi6", "libxkbcommon0", "libxxf86vm1"
            ], env=nonint_env, check=False)
        os.environ["BLENDER_EXE"] = str(blender_bin)
        os.environ["PATH"] = f"{blender_bin.parent}:{os.environ.get('PATH', '')}"

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

LOG_RELAY_URL = "https://curiocut-corn.pcgpt00.workers.dev/api/logs"

# Reset log buffer at start of new run
try:
    req_reset = urllib.request.Request(f"{LOG_RELAY_URL}?reset=1", data=b"", method="POST", headers={"User-Agent": "Mozilla/5.0 CurioCut-Runner/1.0"})
    urllib.request.urlopen(req_reset, timeout=5)
except Exception:
    pass

cmd = [sys.executable, "-u", "make_short.py", "--style", style_arg, "--upload", "--privacy", "public"]
proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

def _watchdog_loop(target_proc):
    while target_proc.poll() is None:
        time.sleep(5)
        try:
            req_check = urllib.request.Request(f"{LOG_RELAY_URL}?check_stop=1", headers={"User-Agent": "Mozilla/5.0 CurioCut-Runner/1.0"})
            with urllib.request.urlopen(req_check, timeout=4) as chk_resp:
                chk_data = json.loads(chk_resp.read().decode("utf-8"))
                if chk_data.get("should_stop"):
                    sys.stderr.write("\n[STOP SIGNAL] Watchdog detected stop signal from Discord. Forcing termination...\n")
                    sys.stderr.flush()
                    try:
                        target_proc.kill()
                    except Exception:
                        pass
                    os._exit(0)
        except Exception:
            pass

watchdog = threading.Thread(target=_watchdog_loop, args=(proc,), daemon=True)
watchdog.start()

log_buffer = []
last_log_post = time.time()

for line in iter(proc.stdout.readline, ""):
    sys.stdout.write(line)
    sys.stdout.flush()
    log_buffer.append(line)
    now = time.time()
    if (len(log_buffer) >= 20 or now - last_log_post >= 6.0) and log_buffer:
        chunk = "".join(log_buffer).encode("utf-8")
        log_buffer.clear()
        last_log_post = now
        try:
            req_post = urllib.request.Request(
                LOG_RELAY_URL,
                data=chunk,
                method="POST",
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                    "User-Agent": "Mozilla/5.0 CurioCut-Runner/1.0"
                }
            )
            with urllib.request.urlopen(req_post, timeout=5) as resp_post:
                resp_json = json.loads(resp_post.read().decode("utf-8"))
                if resp_json.get("should_stop"):
                    print("\n[STOP SIGNAL] User confirmed termination from Discord. Stopping GPU engine to save weekly quota...", flush=True)
                    proc.terminate()
                    sys.exit(0)
        except Exception:
            pass

proc.wait()
if log_buffer:
    chunk = "".join(log_buffer).encode("utf-8")
    try:
        req_post = urllib.request.Request(
            LOG_RELAY_URL,
            data=chunk,
            method="POST",
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "User-Agent": "Mozilla/5.0 CurioCut-Runner/1.0"
            }
        )
        urllib.request.urlopen(req_post, timeout=5)
    except Exception:
        pass

ret_code = proc.returncode

if ret_code == 0:
    print("\n" + "="*70, flush=True)
    print("SHORT SUCCESSFULLY CREATED AND PUBLISHED TO CLOUD!", flush=True)
    print("="*70 + "\n", flush=True)
    # Note: Instagram Comment-to-DM is handled 24/7 in real-time by Cloudflare Edge Webhooks
else:
    print(f"\nWorker exited with error code {ret_code}", flush=True)
    try:
        from discord_notifier import notify_error, update_live_progress
        update_live_progress(
            step_title="Cloud Worker Failed",
            percent=0,
            details=f"Pipeline aborted on cloud runner (exit code {ret_code}). Check logs for details.",
            is_error=True
        )
        notify_error("Cloud Runner", f"Worker stopped with code {ret_code}")
    except Exception:
        pass
    sys.exit(ret_code)
