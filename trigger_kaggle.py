
# Dispatches video generation jobs to Kaggle cloud runner
import os
import sys
import time
import json
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone
from pathlib import Path

# Load environment variables if local .env exists
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

def load_kaggle_pool():
    """Dynamically loads and deduplicates all Kaggle accounts from environment variables."""
    pool = []
    # 1. Primary account
    u1 = os.environ.get("KAGGLE_USERNAME", "").strip() or "shlokkshahh"
    t1 = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    if t1:
        pool.append({"user": u1, "token": t1})

    # 2. Numbered failover accounts (2, 3, 4, ...)
    for idx in range(2, 25):
        u = os.environ.get(f"KAGGLE_USERNAME_{idx}", "").strip()
        t = os.environ.get(f"KAGGLE_API_TOKEN_{idx}", "").strip()
        if u and t and not any(a["user"] == u for a in pool):
            pool.append({"user": u, "token": t})

    # 3. Delimited KAGGLE_ACCOUNTS string (user:token,user2:token2)
    raw_accs = os.environ.get("KAGGLE_ACCOUNTS", "").strip()
    if raw_accs:
        for entry in raw_accs.split(","):
            if ":" in entry:
                parts = entry.split(":", 1)
                u = parts[0].strip()
                t = parts[1].strip()
                if u and t and not any(a["user"] == u for a in pool):
                    pool.append({"user": u, "token": t})

    if not pool:
        pool = [{"user": u1, "token": t1}]
    return pool

def load_daily_ordered_pool():
    """Loads all accounts and cyclically rotates the active pool based on the day of the year."""
    raw_pool = load_kaggle_pool()
    if not raw_pool:
        return raw_pool
    # Day-of-year modulo (Day 1 -> Acc 1, Day 2 -> Acc 2, Day 3 -> Acc 3, Day 4 -> Acc 4, Day 5 -> Acc 1...)
    day_num = datetime.now(timezone.utc).timetuple().tm_yday
    day_offset = day_num % len(raw_pool)
    ordered = raw_pool[day_offset:] + raw_pool[:day_offset]
    print(f"[ROUND-ROBIN POOL] Day {day_num} of year -> Daily Lead: '{ordered[0]['user']}'")
    print(f"[ROUND-ROBIN POOL] Circular Failover Order: {[a['user'] for a in ordered]}")
    return ordered

KAGGLE_POOL = load_daily_ordered_pool()
current_account_idx = 0

def get_current_account():
    global current_account_idx
    if current_account_idx >= len(KAGGLE_POOL):
        current_account_idx = len(KAGGLE_POOL) - 1
    return KAGGLE_POOL[current_account_idx]

KERNEL_SLUG = "curiocut-gpu-engine"
LOG_RELAY_URL = "https://curiocut-corn.pcgpt00.workers.dev/api/logs"
run_message_id = None
run_started_at = time.time()
latest_worker_log = ""
run_version = None

def get_kernel_url(user, v_num=None):
    base = f"https://www.kaggle.com/code/{user}/{KERNEL_SLUG}"
    return f"{base}?versionNumber={v_num}" if v_num else base

def get_status_url(user):
    return f"https://www.kaggle.com/api/v1/kernels/status?userName={user}&kernelSlug={KERNEL_SLUG}"

def get_out_url(user):
    return f"https://www.kaggle.com/api/v1/kernels/output?userName={user}&kernelSlug={KERNEL_SLUG}"

def is_account_block_error(msg: str) -> bool:
    low = (msg or "").lower()
    block_markers = [
        "quota", "exceeded", "limit reached", "maximum hours",
        "no gpu available", "session running", "concurrent",
        "too many active", "not available for this account",
        "unauthorized", "invalid token", "forbidden", "rate limit"
    ]
    return any(k in low for k in block_markers)

def clean_kaggle_log(raw_log: str) -> str:
    """Parses Kaggle JSON stream log arrays into clean, readable text."""
    if not raw_log:
        return ""
    stripped = raw_log.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            chunks = json.loads(stripped)
            if isinstance(chunks, list):
                return "".join(c.get("data", "") for c in chunks if isinstance(c, dict))
        except Exception:
            pass
    return raw_log

def notify_account_failover(old_user, new_user, reason):
    try:
        from discord_notifier import notify_alert
        new_url = get_kernel_url(new_user)
        notify_alert(
            title="Kaggle Multi-Account Failover Activated",
            details=f"Account `{old_user}` reached limit: **{reason}**.\nAuto-rotating to standby account `{new_user}` ({current_account_idx + 1}/{len(KAGGLE_POOL)} in pool).",
            severity="warning",
            button_label=f"View {new_user} on Kaggle",
            button_url=new_url
        )
    except Exception as ex:
        print(f"Notice: Failover alert error: {ex}")

latest_kernel_url = get_kernel_url(get_current_account()["user"])

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

full_worker_code = ""

def prepare_worker_payload():
    global full_worker_code, run_message_id
    WORKER_SCRIPT = Path(__file__).resolve().parent / "kaggle_worker.py"
    worker_code = WORKER_SCRIPT.read_text(encoding="utf-8")

    secrets_to_pass["DISCORD_RUN_MESSAGE_ID"] = run_message_id or ""

    injected_header = f"""# AUTO-INJECTED CLOUD SECRETS
import os
os.environ["GROQ_API_KEY"] = {repr(secrets_to_pass["GROQ_API_KEY"])}
os.environ["GEMINI_API_KEY"] = {repr(secrets_to_pass["GEMINI_API_KEY"])}
os.environ["GEMINI_API_KEY_BACKUP"] = {repr(secrets_to_pass["GEMINI_API_KEY_BACKUP"])}
os.environ["INSTAGRAM_ACCOUNT_ID"] = {repr(secrets_to_pass["INSTAGRAM_ACCOUNT_ID"])}
os.environ["INSTAGRAM_ACCESS_TOKEN"] = {repr(secrets_to_pass["INSTAGRAM_ACCESS_TOKEN"])}
os.environ["YOUTUBE_TOKEN_JSON"] = {repr(secrets_to_pass["YOUTUBE_TOKEN_JSON"])}
os.environ["CURIO_SLOT"] = {repr(secrets_to_pass["CURIO_SLOT"])}
os.environ["KAGGLE_CURRENT_USER"] = {repr(get_current_account()["user"])}
os.environ["DISCORD_RUN_MESSAGE_ID"] = {repr(secrets_to_pass["DISCORD_RUN_MESSAGE_ID"])}
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
    return full_worker_code

def push_kernel(enable_gpu=True):
    global latest_kernel_url, run_message_id, run_version, current_account_idx
    acc = get_current_account()
    user = acc["user"]
    token = acc["token"]
    prepare_worker_payload()
    mode_str = "NVIDIA Tesla T4 GPU (16 GB VRAM)" if enable_gpu else "CPU (4-Core / High-Speed)"
    print(f"\nDispatching kernel: {user}/{KERNEL_SLUG} [{mode_str}] (Account {current_account_idx + 1}/{len(KAGGLE_POOL)}: {user})...")
    
    payload = {
        "slug": f"{user}/{KERNEL_SLUG}",
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
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "kaggle-api/v1.6.14"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("hasError") or res.get("error"):
                err_msg = res.get("error") or res.get("errorNullable") or "Unknown Kaggle API error"
                raise RuntimeError(f"Kaggle API Error: {err_msg}")
            v_num = res.get("versionNumber")
            run_version = v_num
            base_url = (res.get("url") or f"https://www.kaggle.com/code/{user}/{KERNEL_SLUG}").split("?")[0]
            latest_kernel_url = f"{base_url}?versionNumber={v_num}" if v_num else base_url
            print(f"[OK] Job accepted by Kaggle cloud API on {user} (Version #{v_num})!")
            print(f"URL: {latest_kernel_url}")
            try:
                from discord_notifier import update_run_log
                if run_message_id:
                    update_run_log(
                        run_message_id, v_num, secrets_to_pass["CURIO_SLOT"], latest_kernel_url,
                        "QUEUED", time.time() - run_started_at,
                        f"Kaggle accepted the run on {user}. Waiting for the execution container to start.\n"
                    )
            except Exception as e:
                print(f"Notice: Could not initialize per-run Discord log: {e}")
            try:
                from discord_notifier import notify_engine
                role_str = "Daily Lead" if current_account_idx == 0 else f"Failover Standby #{current_account_idx}"
                notify_engine(
                    title=f"GPU Cloud Engine Dispatched -> `{user}`",
                    description=f"CurioCut dispatched **{secrets_to_pass['CURIO_SLOT'].upper()}** to Kaggle GPU runner.\n**Selected Account**: `{user}` ({role_str}, {current_account_idx + 1}/{len(KAGGLE_POOL)} in pool)\n\n[Open Kaggle Execution v{v_num}]({latest_kernel_url})",
                    fields=[
                        {"name": "Selected Account", "value": f"`{user}` ({role_str})", "inline": True},
                        {"name": "Slot", "value": secrets_to_pass["CURIO_SLOT"].upper(), "inline": True},
                        {"name": "Hardware", "value": "NVIDIA GPU (T4/P100)" if "GPU" in mode_str else "Cloud CPU", "inline": True},
                        {"name": "Kernel Version", "value": f"Version #{v_num}" if v_num else "Latest", "inline": True}
                    ],
                    color=0x38BDF8,
                    button_label=f"View {user} on Kaggle (v{v_num})" if v_num else f"View {user} on Kaggle",
                    button_url=latest_kernel_url
                )
            except Exception:
                pass
            return res
    except urllib.error.HTTPError as he:
        body = ""
        try:
            body = he.read().decode("utf-8")
        except Exception:
            pass
        err_msg = f"HTTP {he.code}: {he.reason} - {body}"
        if is_account_block_error(err_msg) and (current_account_idx + 1 < len(KAGGLE_POOL)):
            next_user = KAGGLE_POOL[current_account_idx + 1]["user"]
            print(f"\n[ACCOUNT BLOCKED / QUOTA EXHAUSTED] Account '{user}': {err_msg[:120]}")
            print(f"[FAILOVER] Auto-switching to standby account: '{next_user}'...")
            current_account_idx += 1
            notify_account_failover(user, next_user, f"Account restriction: {err_msg[:80]}")
            return push_kernel(enable_gpu=enable_gpu)
        raise RuntimeError(f"Kaggle push failed: {err_msg}")
    except RuntimeError as re_err:
        err_str = str(re_err)
        if is_account_block_error(err_str) and (current_account_idx + 1 < len(KAGGLE_POOL)):
            next_user = KAGGLE_POOL[current_account_idx + 1]["user"]
            print(f"\n[ACCOUNT BLOCKED / QUOTA EXHAUSTED] Account '{user}': {err_str[:120]}")
            print(f"[FAILOVER] Auto-switching to standby account: '{next_user}'...")
            current_account_idx += 1
            notify_account_failover(user, next_user, f"Account restriction: {err_str[:80]}")
            return push_kernel(enable_gpu=enable_gpu)
        raise

def fetch_worker_log(include_kaggle_api=False):
    """Fetch official execution logs from Kaggle API when job completes or fails."""
    if include_kaggle_api:
        try:
            acc = get_current_account()
            req_out = urllib.request.Request(
                get_out_url(acc["user"]),
                headers={
                    "Authorization": f"Bearer {acc['token']}",
                    "User-Agent": "kaggle-api/v1.6.14"
                }
            )
            with urllib.request.urlopen(req_out, timeout=20) as resp_out:
                out_data = json.loads(resp_out.read().decode("utf-8"))
                raw = out_data.get("log", "") or ""
                return clean_kaggle_log(raw)
        except Exception:
            pass
    return ""

def describe_run_phase(kaggle_status, log_text):
    if kaggle_status == "queued":
        return "QUEUED"
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
    latest_phase = (-1, "RUNNING")
    for markers, phase in checks:
        marker_at = max((log_text.rfind(marker) for marker in markers), default=-1)
        if marker_at > latest_phase[0]:
            latest_phase = (marker_at, phase)
            if phase == "RENDERING FRAMES":
                frame_m = re.search(r"(?:Append frame\s*(\d+)|Fra:\s*(\d+(?:/\d+)?))", log_text[marker_at:marker_at+120])
                if frame_m:
                    matched_val = frame_m.group(1) or frame_m.group(2)
                    latest_phase = (marker_at, f"RENDERING FRAMES ({matched_val})")
    return latest_phase[1]

def publish_run_log(status, log_text=None):
    global latest_worker_log
    if not run_message_id:
        return
    try:
        from discord_notifier import update_run_log
        current_log = latest_worker_log if log_text is None else log_text
        title_match = re.search(r"(?:Final Title:|Generated)\s*['\"]?([^'\"\n]+)", current_log, re.IGNORECASE)
        style_match = re.search(r"Starting 3D short generation \(Slot:\s*([^|)]+)\|\s*Style:\s*([^\)]+)", current_log, re.IGNORECASE)
        slot_label = secrets_to_pass["CURIO_SLOT"]
        acc_name = get_current_account()["user"]
        slot_label = f"{slot_label} · [{acc_name}]"
        if style_match:
            slot_label = f"{style_match.group(1).strip()} · {style_match.group(2).strip()} · [{acc_name}]"
        update_run_log(
            run_message_id, run_version, slot_label, latest_kernel_url,
            status, time.time() - run_started_at, current_log,
            title=title_match.group(1).strip() if title_match else None
        )
    except Exception as e:
        print(f"Notice: Per-run Discord log update failed: {e}")

def main():
    global run_message_id, run_started_at, latest_worker_log, run_version, latest_kernel_url
    run_started_at = time.time()
    print("\n" + "="*70)
    print("   CURIO CUT - AUTONOMOUS CLOUD DISPATCHER   ")
    print("="*70)

    # Create a per-run card in #run-logs before dispatch so DISCORD_RUN_MESSAGE_ID is injected into Kaggle
    try:
        from discord_notifier import create_run_log, update_run_log
        run_message_id = create_run_log(None, secrets_to_pass["CURIO_SLOT"], latest_kernel_url)
        if run_message_id:
            update_run_log(run_message_id, None, secrets_to_pass["CURIO_SLOT"], latest_kernel_url,
                           "DISPATCHING", 0, "Preparing Kaggle cloud execution.\n")
    except Exception as e:
        print(f"Notice: Could not initialize per-run Discord log: {e}")

    prepare_worker_payload()

    # Try GPU first
    gpu_requested = True
    try:
        push_kernel(enable_gpu=True)
    except Exception as e:
        print(f"Notice: Initial GPU push returned: {e}. Falling back to standard cloud runner.")
        gpu_requested = False
        try:
            push_kernel(enable_gpu=False)
        except Exception as fallback_error:
            latest_worker_log = f"GPU and CPU Kaggle dispatch both failed.\nGPU: {e}\nCPU: {fallback_error}\n"
            try:
                from discord_notifier import update_run_log
                update_run_log(run_message_id, run_version, secrets_to_pass["CURIO_SLOT"], latest_kernel_url,
                               "DISPATCH FAILED", time.time() - run_started_at, latest_worker_log)
            except Exception:
                pass
            raise

    print("\nMonitoring Cloud execution...")
    start_t = time.time()
    max_wait = 43200  # 720 minutes (12 hours) matching Kaggle maximum session ceiling
    queued_start = time.time()
    has_alerted_2h = False
    has_alerted_3h = False
    last_run_log_update = 0
    last_stop_check = 0

    while time.time() - start_t < max_wait:
        time.sleep(10)
        elapsed = int(time.time() - start_t)
        
        # 2-hour and 3-hour Quota Guardian check-in
        if elapsed >= 7200 and not has_alerted_2h:
            has_alerted_2h = True
            print(f"  [ALERT] 2 hours elapsed on GPU worker. Dispatching Quota Guardian check to Discord...")
            try:
                from discord_notifier import notify_long_run_alert
                acc_name = get_current_account()["user"]
                slot_name = secrets_to_pass.get("CURIO_SLOT", "auto")
                phase_label = describe_run_phase(st, latest_worker_log)
                title_match = re.search(r"(?:Final Title:|Generated)\s*['\"]?([^'\"\n]+)", latest_worker_log, re.IGNORECASE)
                ep_title = title_match.group(1).strip() if title_match else None
                notify_long_run_alert(elapsed, latest_kernel_url, account=acc_name, slot=slot_name, phase=phase_label, title=ep_title)
            except Exception as ex:
                print(f"  Notice: Long run alert dispatch: {ex}")

        if elapsed >= 10800 and not has_alerted_3h:
            has_alerted_3h = True
            print(f"  [ALERT] 3 hours elapsed on GPU worker. Dispatching CRITICAL Quota Guardian check to Discord...")
            try:
                from discord_notifier import notify_long_run_alert
                acc_name = get_current_account()["user"]
                slot_name = secrets_to_pass.get("CURIO_SLOT", "auto")
                phase_label = describe_run_phase(st, latest_worker_log)
                title_match = re.search(r"(?:Final Title:|Generated)\s*['\"]?([^'\"\n]+)", latest_worker_log, re.IGNORECASE)
                ep_title = title_match.group(1).strip() if title_match else None
                notify_long_run_alert(elapsed, latest_kernel_url, account=acc_name, slot=slot_name, phase=phase_label, title=ep_title)
            except Exception as ex:
                print(f"  Notice: Long run alert dispatch: {ex}")

        # Check if user triggered emergency stop via Discord (every 20s)
        if (elapsed - last_stop_check >= 20):
            last_stop_check = elapsed
            try:
                req_chk = urllib.request.Request(
                    f"{LOG_RELAY_URL}?check_stop=1",
                    headers={"User-Agent": "Mozilla/5.0 CurioCut-Runner/1.0"}
                )
                with urllib.request.urlopen(req_chk, timeout=4) as resp_chk:
                    chk_d = json.loads(resp_chk.read().decode("utf-8"))
                    if chk_d.get("should_stop"):
                        print("\n[STOP SIGNAL] User requested termination via Discord. Exiting Cloud dispatcher...")
                        latest_worker_log = fetch_worker_log(include_kaggle_api=True) or latest_worker_log
                        latest_worker_log += "\nEmergency stop requested from Discord.\n"
                        publish_run_log("CANCELLED", latest_worker_log)
                        sys.exit(0)
            except Exception:
                pass

        try:
            acc = get_current_account()
            user = acc["user"]
            token = acc["token"]
            req_st = urllib.request.Request(
                get_status_url(user),
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "kaggle-api/v1.6.14"
                }
            )
            with urllib.request.urlopen(req_st, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                st = data.get("status", "unknown")
                fail_msg = data.get("failureMessage", "")
                script_v_id = data.get("scriptVersionId") or data.get("versionId") or data.get("id")
                if script_v_id:
                    latest_kernel_url = f"https://www.kaggle.com/code/{user}/{KERNEL_SLUG}?scriptVersionId={script_v_id}"
                
                print(f"  [{elapsed}s] Cloud Worker Status ({user}): {st.upper()}")
                
                # Kaggle API takes 30-45s to transition away from previous run's status.
                # If status reports complete/error in the first 60 seconds, it's stale status from the prior run.
                if elapsed < 60 and st in ("error", "complete"):
                    print(f"  [{elapsed}s] Waiting for Kaggle container to initialize new job (ignoring stale '{st}')...")
                    continue

                # Keep one live card per Kaggle version; refresh phase every 60 seconds
                if run_message_id and (time.time() - last_run_log_update >= 60):
                    status_label = describe_run_phase(st, latest_worker_log)
                    publish_run_log(status_label)
                    last_run_log_update = time.time()

                # Keep waiting for GPU (Kaggle batch GPU queue normally takes 2-8 minutes, ceiling 30 mins)
                if gpu_requested and st == "queued" and (time.time() - queued_start) > 1800:
                    if current_account_idx + 1 < len(KAGGLE_POOL):
                        next_user = KAGGLE_POOL[current_account_idx + 1]["user"]
                        print(f"\n[QUEUE DELAY] GPU queue reached 30m on {user}. Shifting to standby account {next_user}...")
                        notify_account_failover(user, next_user, "GPU queue 30-minute wait ceiling reached")
                        current_account_idx += 1
                        push_kernel(enable_gpu=True)
                        queued_start = time.time()
                        start_t = time.time()
                        continue
                    else:
                        print("\n[WARNING] All GPU accounts in pool queued. Falling back to Cloud Compute...")
                        try:
                            from discord_notifier import notify_alert
                            notify_alert(
                                title="All GPU Queues Congested - Fallback Activated",
                                details="All accounts in the GPU pool reached 30m queue wait ceiling. Falling back to CPU mode (4-Core / High-Speed).",
                                severity="warning"
                            )
                        except Exception:
                            pass
                        gpu_requested = False
                        push_kernel(enable_gpu=False)
                        queued_start = time.time()
                        continue

                if st == "complete":
                    print("\n" + "="*70)
                    print("VIDEO SUCCESSFULLY RENDERED & PUBLISHED!")
                    print("="*70)
                    latest_worker_log = fetch_worker_log(include_kaggle_api=True) or latest_worker_log
                    publish_run_log("COMPLETED", latest_worker_log)
                    if latest_worker_log:
                        print("\n--- CLOUD WORKER LOGS ---")
                        print(latest_worker_log[-1000:])
                    sys.exit(0)
                elif st == "error":
                    print(f"\n[ERROR] Cloud Execution Error on {user}: {fail_msg}")
                    latest_worker_log = fetch_worker_log(include_kaggle_api=True) or latest_worker_log
                    if fail_msg:
                        latest_worker_log += f"\nKaggle failure: {fail_msg}\n"
                    
                    # Quota auto-failover if killed mid-run:
                    if (is_account_block_error(fail_msg) or is_account_block_error(latest_worker_log)) and (current_account_idx + 1 < len(KAGGLE_POOL)):
                        next_user = KAGGLE_POOL[current_account_idx + 1]["user"]
                        print(f"\n[MID-RUN FAILOVER] Account '{user}' halted: {fail_msg}")
                        print(f"[FAILOVER] Auto-migrating job to standby account '{next_user}'...")
                        notify_account_failover(user, next_user, f"Mid-run termination: {fail_msg or 'Session/Quota limit'}")
                        current_account_idx += 1
                        try:
                            push_kernel(enable_gpu=True)
                            start_t = time.time()
                            queued_start = time.time()
                            has_alerted_2h = False
                            has_alerted_3h = False
                            continue
                        except Exception as failover_err:
                            print(f"[ERROR] Standby failover dispatch failed: {failover_err}")
                            latest_worker_log += f"\nStandby failover dispatch failed: {failover_err}\n"
                            publish_run_log("FAILED", latest_worker_log)
                            sys.exit(1)

                    publish_run_log("FAILED", latest_worker_log)
                    try:
                        from discord_notifier import notify_error
                        notify_error(
                            context=f"Kaggle GPU Execution ({user})",
                            error_msg=fail_msg or "Execution failed on cloud runner",
                            stack_trace=latest_worker_log[-1200:] if latest_worker_log else None,
                            button_label="Inspect Failed Kaggle Run",
                            button_url=latest_kernel_url
                        )
                    except Exception:
                        pass
                    if latest_worker_log:
                        print("\n--- CLOUD ERROR LOGS ---")
                        print(latest_worker_log)
                    sys.exit(1)
                elif st == "cancelAcknowledged":
                    print("\nJob cancelled.")
                    latest_worker_log = fetch_worker_log(include_kaggle_api=True) or latest_worker_log
                    publish_run_log("CANCELLED", latest_worker_log)
                    sys.exit(1)
        except urllib.error.HTTPError as he:
            if he.code in (401, 403) and (current_account_idx + 1 < len(KAGGLE_POOL)):
                next_user = KAGGLE_POOL[current_account_idx + 1]["user"]
                print(f"\n[AUTH BLOCK] Account '{user}' returned HTTP {he.code}. Auto-switching to standby account '{next_user}'...")
                notify_account_failover(user, next_user, f"Authentication/permission error: HTTP {he.code}")
                current_account_idx += 1
                try:
                    push_kernel(enable_gpu=True)
                    start_t = time.time()
                    queued_start = time.time()
                    has_alerted_2h = False
                    has_alerted_3h = False
                    continue
                except Exception as push_err:
                    print(f"[ERROR] Failover push failed: {push_err}")
                    latest_worker_log += f"\nFailover push failed: {push_err}\n"
                    publish_run_log("FAILED", latest_worker_log)
                    sys.exit(1)
            elif he.code == 404 and elapsed < 90:
                print(f"  [{elapsed}s] Waiting for Kaggle API to register kernel endpoint on {user}...")
            else:
                print(f"  Status check HTTP {he.code}: {he.reason}")
        except Exception as e:
            print(f"  Status check: {e}")

    print("\nTimeout waiting for completion.")
    latest_worker_log = fetch_worker_log(include_kaggle_api=True) or latest_worker_log
    latest_worker_log += "\nDispatcher timed out while waiting for Kaggle completion.\n"
    publish_run_log("TIMED OUT", latest_worker_log)
    sys.exit(1)

if __name__ == "__main__":
    main()
