# Cloud runner for rendering and uploading on Kaggle GPU
import os
import sys
import time
import shutil
import subprocess
import json
import urllib.request
import threading
import re
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

LOG_RELAY_URL = "https://curiocut-corn.pcgpt00.workers.dev/api/logs"
RUN_MESSAGE_ID = os.environ.get("DISCORD_RUN_MESSAGE_ID", "").strip()
worker_boot_time = time.time()
active_subprocesses = set()
active_subprocesses_lock = threading.Lock()

class CloudLogStreamer:
    """Buffers stdout/stderr in memory and tees to original stdout/stderr for Kaggle execution logs."""
    def __init__(self):
        self.all_logs = []
        self.lock = threading.Lock()
        self.orig_stdout = sys.__stdout__
        self.orig_stderr = sys.__stderr__

    def write(self, s, is_stderr=False):
        if not s:
            return
        target = self.orig_stderr if is_stderr else self.orig_stdout
        target.write(s)
        target.flush()
        with self.lock:
            self.all_logs.append(s)
            # Cap in-memory history to ~8 MB (approx 70,000 lines)
            if len(self.all_logs) > 70000:
                self.all_logs = self.all_logs[-50000:]

    def flush(self):
        pass

    def get_full_log(self):
        with self.lock:
            return "".join(self.all_logs)

class StdoutTee:
    def __init__(self, streamer, is_stderr=False):
        self._s = streamer
        self._err = is_stderr
    def write(self, s):
        self._s.write(s, self._err)
    def flush(self):
        self._s.flush()
    def fileno(self):
        return (self._s.orig_stderr if self._err else self._s.orig_stdout).fileno()

streamer = CloudLogStreamer()
sys.stdout = StdoutTee(streamer, is_stderr=False)
sys.stderr = StdoutTee(streamer, is_stderr=True)

def force_emergency_shutdown(target_proc=None):
    sys.stderr.write("\n[STOP SIGNAL] Emergency stop confirmed from Discord. Terminating GPU engine to preserve weekly quota...\n")
    sys.stderr.flush()
    if target_proc:
        try:
            target_proc.kill()
        except Exception:
            pass
    with active_subprocesses_lock:
        for p in list(active_subprocesses):
            try:
                p.kill()
            except Exception:
                pass
    if sys.platform != "win32":
        try:
            os.system("pkill -9 -f blender 2>/dev/null || true")
            os.system("pkill -9 -f ffmpeg 2>/dev/null || true")
            os.system("pkill -9 -f make_short 2>/dev/null || true")
        except Exception:
            pass
    os._exit(0)

def run_command_logged(cmd, check=True, timeout=None, env=None, cwd=None):
    """Executes a subprocess and streams all lines live through the cloud logger."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        cwd=cwd
    )
    with active_subprocesses_lock:
        active_subprocesses.add(proc)
    try:
        for line in iter(proc.stdout.readline, ""):
            sys.stdout.write(line)
            sys.stdout.flush()
        proc.wait(timeout=timeout)
    finally:
        with active_subprocesses_lock:
            active_subprocesses.discard(proc)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return proc.returncode

def _detect_phase_from_log(log_text):
    checks = [
        (("[GPU] NVIDIA", "AUTONOMOUS CLOUD EXECUTION WORKER"), "BOOTING CONTAINER"),
        (("[1/4]", "Cloning", "Updating CurioCut"), "SYNCING REPOSITORY"),
        (("[2/4]", "Verifying Google Chrome", "official Google Chrome"), "INSTALLING CHROME"),
        (("[3/4]", "Installing Python dependencies", "pip install"), "INSTALLING PACKAGES"),
        (("[3b/4]", "Installing portable Blender", "portable Blender", "Linux libraries for Blender"), "CONFIGURING BLENDER GPU"),
        (("[4/4]", "Starting 3D short generation", "Cloud Video Engine Booted"), "INITIALIZING ENGINE"),
        (("[1/5]", "Writing viral script", "Generating 2-character dialogue"), "WRITING SCRIPT"),
        (("[2/6]", "Generating fresh AI story", "Generating episode"), "GENERATING STORY"),
        (("[3/6]", "Synthesizing narration", "Synthesizing Speech"), "SYNTHESIZING AUDIO"),
        (("[5/6]", "Launching Blender", "Rendering 3D"), "STARTING RENDER"),
        (("Append frame ", "Fra:"), "RENDERING FRAMES"),
        (("[6/6]", "Muxing audio", "Burning Captions"), "FINALIZING VIDEO"),
        (("Uploading to YouTube", "Uploading to Instagram", "Publishing to"), "UPLOADING"),
    ]
    latest = (-1, "RUNNING")
    for markers, phase in checks:
        idx = max((log_text.rfind(m) for m in markers), default=-1)
        if idx > latest[0]:
            latest = (idx, phase)
    return latest[1]

def _worker_background_heartbeat():
    last_discord_update = 0
    while True:
        time.sleep(20)
        try:
            req_check = urllib.request.Request(f"{LOG_RELAY_URL}?check_stop=1", headers={"User-Agent": "Mozilla/5.0 CurioCut-Runner/1.0"})
            with urllib.request.urlopen(req_check, timeout=4) as chk_resp:
                chk_data = json.loads(chk_resp.read().decode("utf-8"))
                if chk_data.get("should_stop"):
                    force_emergency_shutdown()
        except Exception:
            pass

        now = time.time()
        if RUN_MESSAGE_ID and (now - last_discord_update >= 50):
            try:
                from discord_notifier import update_run_log
                current_log = streamer.get_full_log()
                slot_name = os.environ.get("CURIO_SLOT", "auto").upper()
                phase = _detect_phase_from_log(current_log)
                title_match = re.search(r"(?:Final Title:|Generated)\s*['\"]?([^'\"\n]+)", current_log, re.IGNORECASE)
                update_run_log(
                    RUN_MESSAGE_ID,
                    None,
                    slot_name,
                    None,
                    phase,
                    now - worker_boot_time,
                    log_text=current_log,
                    title=title_match.group(1).strip() if title_match else None
                )
                last_discord_update = now
            except Exception:
                pass

heartbeat_thread = threading.Thread(target=_worker_background_heartbeat, daemon=True)
heartbeat_thread.start()

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
    run_command_logged(["git", "clone", "https://github.com/shlokkokk/CurioCut.git", str(WORKSPACE)], check=True, timeout=300)
else:
    print("\n[1/4] Updating CurioCut repository...", flush=True)
    run_command_logged(["git", "-C", str(WORKSPACE), "pull"], check=False, timeout=300)

os.chdir(WORKSPACE)
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

# Step 2: Ensure Google Chrome is installed non-interactively
print("\n[2/4] Verifying Google Chrome...", flush=True)
chrome_path = shutil.which("google-chrome")
apt_flags = ["-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold"]

if not chrome_path:
    print("Downloading and installing official Google Chrome stable deb...", flush=True)
    try:
        run_command_logged(["wget", "-q", "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"], check=True, timeout=120)
        run_command_logged(["apt-get", "update", "-y"] + apt_flags, check=False, timeout=120)
        run_command_logged(["apt-get", "install", "-y"] + apt_flags + ["./google-chrome-stable_current_amd64.deb", "libegl1", "libgles2"], check=True, timeout=300)
    except Exception as e:
        print(f"Chrome install notice: {e}", flush=True)
    chrome_path = shutil.which("google-chrome") or "/usr/bin/google-chrome"

print(f"Browser ready: {chrome_path}", flush=True)

# Step 3: Install Python Dependencies
print("\n[3/4] Installing Python dependencies...", flush=True)
run_command_logged([
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
            run_command_logged(["curl", "-L", "-s", "https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz", "-o", str(tar_path)], check=True)
            run_command_logged(["tar", "-xf", str(tar_path), "-C", str(blender_dir)], check=True)
            tar_path.unlink(missing_ok=True)
        subprocess.run(["chmod", "+x", str(blender_bin)], check=False)
        test_res = subprocess.run([str(blender_bin), "--version"], capture_output=True, text=True)
        if test_res.returncode != 0:
            print(f"Installing missing Linux libraries for Blender: {test_res.stderr.strip()}", flush=True)
            nonint_env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", NEEDRESTART_MODE="a", NEEDRESTART_SUSPEND="1")
            run_command_logged(["apt-get", "update", "-y", "-q"] + apt_flags, env=nonint_env, check=False)
            run_command_logged(["apt-get", "install", "-y", "-q"] + apt_flags + [
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

cmd = [sys.executable, "-u", "make_short.py", "--style", style_arg, "--upload", "--privacy", "public"]
ret_code = run_command_logged(cmd, check=False)

if ret_code == 0:
    print("\n" + "="*70, flush=True)
    print("SHORT SUCCESSFULLY CREATED AND PUBLISHED TO CLOUD!", flush=True)
    print("="*70 + "\n", flush=True)
    if RUN_MESSAGE_ID:
        try:
            from discord_notifier import update_run_log
            update_run_log(
                RUN_MESSAGE_ID, None, slot.upper(), None,
                "COMPLETED", time.time() - worker_boot_time,
                log_text=streamer.get_full_log()
            )
        except Exception:
            pass
else:
    print(f"\nWorker exited with error code {ret_code}", flush=True)
    if RUN_MESSAGE_ID:
        try:
            from discord_notifier import update_run_log
            update_run_log(
                RUN_MESSAGE_ID, None, slot.upper(), None,
                "FAILED", time.time() - worker_boot_time,
                log_text=streamer.get_full_log()
            )
        except Exception:
            pass
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
