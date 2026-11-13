
# Dispatches video generation jobs to Kaggle cloud runner
import os
import sys
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

# Load environment variables if local .env exists
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

KAGGLE_TOKEN = os.environ.get("KAGGLE_API_TOKEN", "")
KAGGLE_USER = os.environ.get("KAGGLE_USERNAME") or "shlokkshahh"
KERNEL_SLUG = "curiocut-gpu-engine"

WORKER_SCRIPT = Path(__file__).resolve().parent / "kaggle_worker.py"
worker_code = WORKER_SCRIPT.read_text(encoding="utf-8")

# Prepare secrets to pass to the remote container
secrets_to_pass = {
    "GROQ_API_KEY": os.environ.get("GROQ_API_KEY", ""),
    "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
    "GEMINI_API_KEY_BACKUP": os.environ.get("GEMINI_API_KEY_BACKUP", ""),
    "INSTAGRAM_ACCOUNT_ID": os.environ.get("INSTAGRAM_ACCOUNT_ID", ""),
    "INSTAGRAM_ACCESS_TOKEN": os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
    "YOUTUBE_TOKEN_JSON": os.environ.get("YOUTUBE_TOKEN_JSON", ""),
    "DISCORD_WEBHOOK_ENGINE_LOGS": os.environ.get("DISCORD_WEBHOOK_ENGINE_LOGS", ""),
    "DISCORD_WEBHOOK_ALERTS": os.environ.get("DISCORD_WEBHOOK_ALERTS", ""),
    "DISCORD_WEBHOOK_ERRORS": os.environ.get("DISCORD_WEBHOOK_ERRORS", ""),
    "DISCORD_WEBHOOK_YT_POSTS": os.environ.get("DISCORD_WEBHOOK_YT_POSTS", ""),
    "DISCORD_WEBHOOK_YT_ERRORS": os.environ.get("DISCORD_WEBHOOK_YT_ERRORS", ""),
    "DISCORD_WEBHOOK_IG_POSTS": os.environ.get("DISCORD_WEBHOOK_IG_POSTS", ""),
    "DISCORD_WEBHOOK_IG_ERRORS": os.environ.get("DISCORD_WEBHOOK_IG_ERRORS", ""),
    "DISCORD_WEBHOOK_DMS_SENT": os.environ.get("DISCORD_WEBHOOK_DMS_SENT", ""),
    "DISCORD_WEBHOOK_LIVE_PROGRESS": os.environ.get("DISCORD_WEBHOOK_LIVE_PROGRESS", ""),
    "CURIO_SLOT": os.environ.get("CURIO_SLOT", "auto"),
}

yt_file = Path(__file__).resolve().parent / "youtube_token.json"
if yt_file.exists() and not secrets_to_pass["YOUTUBE_TOKEN_JSON"]:
    secrets_to_pass["YOUTUBE_TOKEN_JSON"] = yt_file.read_text(encoding="utf-8").strip()

injected_header = f"""# AUTO-INJECTED CLOUD SECRETS
import os
os.environ["GROQ_API_KEY"] = {repr(secrets_to_pass["GROQ_API_KEY"])}
os.environ["GEMINI_API_KEY"] = {repr(secrets_to_pass["GEMINI_API_KEY"])}
os.environ["GEMINI_API_KEY_BACKUP"] = {repr(secrets_to_pass["GEMINI_API_KEY_BACKUP"])}
os.environ["INSTAGRAM_ACCOUNT_ID"] = {repr(secrets_to_pass["INSTAGRAM_ACCOUNT_ID"])}
os.environ["INSTAGRAM_ACCESS_TOKEN"] = {repr(secrets_to_pass["INSTAGRAM_ACCESS_TOKEN"])}
os.environ["YOUTUBE_TOKEN_JSON"] = {repr(secrets_to_pass["YOUTUBE_TOKEN_JSON"])}
os.environ["CURIO_SLOT"] = {repr(secrets_to_pass["CURIO_SLOT"])}
os.environ["DISCORD_WEBHOOK_ENGINE_LOGS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_ENGINE_LOGS"])}
os.environ["DISCORD_WEBHOOK_ALERTS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_ALERTS"])}
os.environ["DISCORD_WEBHOOK_ERRORS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_ERRORS"])}
os.environ["DISCORD_WEBHOOK_YT_POSTS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_YT_POSTS"])}
os.environ["DISCORD_WEBHOOK_YT_ERRORS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_YT_ERRORS"])}
os.environ["DISCORD_WEBHOOK_IG_POSTS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_IG_POSTS"])}
os.environ["DISCORD_WEBHOOK_IG_ERRORS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_IG_ERRORS"])}
os.environ["DISCORD_WEBHOOK_DMS_SENT"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_DMS_SENT"])}
os.environ["DISCORD_WEBHOOK_LIVE_PROGRESS"] = {repr(secrets_to_pass["DISCORD_WEBHOOK_LIVE_PROGRESS"])}
# ----------------------------------------------------
"""

full_worker_code = injected_header + worker_code

latest_kernel_url = f"https://www.kaggle.com/code/{KAGGLE_USER}/{KERNEL_SLUG}"

def push_kernel(enable_gpu=True):
    global latest_kernel_url
    mode_str = "NVIDIA Tesla T4 GPU (16 GB VRAM)" if enable_gpu else "High-Speed 4-Core Cloud Compute"
    print(f"\nDispatching kernel: {KAGGLE_USER}/{KERNEL_SLUG} [{mode_str}]...")
    
    payload = {
        "slug": f"{KAGGLE_USER}/{KERNEL_SLUG}",
        "newTitle": "CurioCut GPU Engine",
        "text": full_worker_code,
        "language": "python",
        "kernelType": "script",
        "isPrivate": True,
        "enableGpu": enable_gpu,
        "enableInternet": True,
        "datasetDataSources": [],
        "competitionDataSources": [],
        "kernelDataSources": []
    }

    req = urllib.request.Request(
        "https://www.kaggle.com/api/v1/kernels/push",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {KAGGLE_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if res.get("hasError") or res.get("error"):
            err_msg = res.get("error") or res.get("errorNullable") or "Unknown Kaggle API error"
            raise RuntimeError(f"Kaggle API Error: {err_msg}")
        v_num = res.get("versionNumber")
        base_url = (res.get("url") or f"https://www.kaggle.com/code/{KAGGLE_USER}/{KERNEL_SLUG}").split("?")[0]
        latest_kernel_url = f"{base_url}?versionNumber={v_num}" if v_num else base_url
        print(f"[OK] Job accepted by Kaggle cloud API (Version #{v_num})!")
        print(f"URL: {latest_kernel_url}")
        try:
            from discord_notifier import notify_engine
            notify_engine(
                title=f"Autonomous Video Pipeline Triggered (v{v_num})" if v_num else "Autonomous Video Pipeline Triggered",
                description=f"CurioCut dispatched **{secrets_to_pass['CURIO_SLOT'].upper()}** to Kaggle Cloud GPU runner.\n\n[Open Kaggle Run v{v_num}]({latest_kernel_url})",
                fields=[
                    {"name": "Slot", "value": secrets_to_pass["CURIO_SLOT"].upper(), "inline": True},
                    {"name": "Hardware", "value": "NVIDIA GPU (T4/P100)" if "GPU" in mode_str else "Cloud CPU", "inline": True},
                    {"name": "Kernel Version", "value": f"Version #{v_num}" if v_num else "Latest", "inline": True}
                ],
                color=0x38BDF8,
                button_label=f"View Run v{v_num} on Kaggle" if v_num else "View Cloud Runner on Kaggle",
                button_url=latest_kernel_url
            )
        except Exception:
            pass
        return res

print("\n" + "="*70)
print("   CURIO CUT - AUTONOMOUS CLOUD DISPATCHER   ")
print("="*70)

# Try GPU first
gpu_requested = True
try:
    push_kernel(enable_gpu=True)
except Exception as e:
    print(f"Notice: Initial GPU push returned: {e}. Falling back to standard cloud runner.")
    gpu_requested = False
    push_kernel(enable_gpu=False)

status_url = f"https://www.kaggle.com/api/v1/kernels/status?userName={KAGGLE_USER}&kernelSlug={KERNEL_SLUG}"
out_url = f"https://www.kaggle.com/api/v1/kernels/output?userName={KAGGLE_USER}&kernelSlug={KERNEL_SLUG}"

print("\nMonitoring Cloud execution...")
start_t = time.time()
max_wait = 21600  # 360 minutes (6 hours) unbreakable ceiling
queued_start = time.time()
has_alerted_2h = False
has_alerted_2_5h = False

while time.time() - start_t < max_wait:
    time.sleep(10)
    elapsed = int(time.time() - start_t)
    
    # 2-hour and 2.5-hour Quota Guardian check-in
    if elapsed >= 7200 and not has_alerted_2h:
        has_alerted_2h = True
        print(f"  [ALERT] 2 hours elapsed on GPU worker. Dispatching Quota Guardian check to Discord...")
        try:
            from discord_notifier import notify_long_run_alert
            notify_long_run_alert(elapsed, latest_kernel_url)
        except Exception as ex:
            print(f"  Notice: Long run alert dispatch: {ex}")

    if elapsed >= 9000 and not has_alerted_2_5h:
        has_alerted_2_5h = True
        print(f"  [ALERT] 2.5 hours elapsed on GPU worker. Dispatching follow-up Quota Guardian check...")
        try:
            from discord_notifier import notify_long_run_alert
            notify_long_run_alert(elapsed, latest_kernel_url)
        except Exception as ex:
            print(f"  Notice: Long run alert dispatch: {ex}")

    # Check if user triggered emergency stop via Discord
    try:
        req_chk = urllib.request.Request(
            "https://curiocut-corn.pcgpt00.workers.dev/api/logs?check_stop=1",
            headers={"User-Agent": "Mozilla/5.0 CurioCut-Runner/1.0"}
        )
        with urllib.request.urlopen(req_chk, timeout=4) as resp_chk:
            chk_d = json.loads(resp_chk.read().decode("utf-8"))
            if chk_d.get("should_stop"):
                print("\n[STOP SIGNAL] User requested termination via Discord. Exiting Cloud dispatcher...")
                sys.exit(0)
    except Exception:
        pass

    try:
        req_st = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {KAGGLE_TOKEN}"})
        with urllib.request.urlopen(req_st, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            st = data.get("status", "unknown")
            fail_msg = data.get("failureMessage", "")
            script_v_id = data.get("scriptVersionId") or data.get("versionId") or data.get("id")
            if script_v_id:
                latest_kernel_url = f"https://www.kaggle.com/code/{KAGGLE_USER}/{KERNEL_SLUG}?scriptVersionId={script_v_id}"
            
            print(f"  [{elapsed}s] Cloud Worker Status: {st.upper()}")
            
            # Kaggle API takes 30-45s to transition away from previous run's status.
            # If status reports complete/error in the first 60 seconds, it's stale status from the prior run.
            if elapsed < 60 and st in ("error", "complete"):
                print(f"  [{elapsed}s] Waiting for Kaggle container to initialize new job (ignoring stale '{st}')...")
                continue

            # Keep waiting for GPU (Kaggle batch GPU queue normally takes 2-8 minutes, ceiling 30 mins)
            if gpu_requested and st == "queued" and (time.time() - queued_start) > 1800:
                print("\n[WARNING] GPU queue reached 30-minute wait ceiling. Auto-switching to Cloud Compute...")
                gpu_requested = False
                push_kernel(enable_gpu=False)
                queued_start = time.time()
                continue

            if st == "complete":
                print("\n" + "="*70)
                print("VIDEO SUCCESSFULLY RENDERED & PUBLISHED!")
                print("="*70)
                # Fetch output logs
                try:
                    req_out = urllib.request.Request(out_url, headers={"Authorization": f"Bearer {KAGGLE_TOKEN}"})
                    with urllib.request.urlopen(req_out, timeout=15) as resp_out:
                        out_data = json.loads(resp_out.read().decode("utf-8"))
                        log = out_data.get("log", "")
                        if log:
                            print("\n--- CLOUD WORKER LOGS ---")
                            print(log[-1000:] if len(log) > 1000 else log)
                except Exception:
                    pass
                sys.exit(0)
            elif st == "error":
                print(f"\n[ERROR] Cloud Execution Error: {fail_msg}")
                try:
                    req_out = urllib.request.Request(out_url, headers={"Authorization": f"Bearer {KAGGLE_TOKEN}"})
                    with urllib.request.urlopen(req_out, timeout=15) as resp_out:
                        out_data = json.loads(resp_out.read().decode("utf-8"))
                        print("\n--- CLOUD ERROR LOGS ---")
                        print(out_data.get("log", ""))
                except Exception:
                    pass
                sys.exit(1)
            elif st == "cancelAcknowledged":
                print("\nJob cancelled.")
                sys.exit(1)
    except Exception as e:
        print(f"  Status check: {e}")

print("\nTimeout waiting for completion.")
sys.exit(1)
