# CurioCut Systematic Multi-Platform Batch Uploader
# Uploads selected videos to YouTube Shorts and Instagram Reels with:
# - Rich descriptions and viral hashtags
# - Automatic engagement comments (comment hooks) on both platforms
# - 75-second anti-spam / anti-rate-limit pacing
# - Real-time Discord alerts
import os
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Load local environment
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from youtube_uploader import upload_short, get_authenticated_service
from instagram_uploader import upload_reel, GRAPH_API_BASE
from discord_notifier import (
    notify_engine, notify_youtube_post, notify_youtube_error,
    notify_instagram_post, notify_instagram_error
)

IG_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841434641576009")
IG_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

QUEUE = [
    {
        "id": "atm_glitch",
        "title": "The Infinite ATM Money Glitch",
        "project_dir": "projects/the_infinite_atm_money_glitch",
        "video_path": "projects/the_infinite_atm_money_glitch/renders/the_infinite_atm_money_glitch.mp4",
        "hook_comment": "Would you have walked away with the cash or reported the glitch immediately? Let me know below!",
        "tags": ["shorts", "story", "truestory", "money", "history", "viral", "curiosity", "animation", "atm"]
    },
    {
        "id": "dumb_millionaire",
        "title": "The Dumbest Millionaire In History",
        "project_dir": "projects/the_dumbest_millionaire_in_his",
        "video_path": "projects/the_dumbest_millionaire_in_his/renders/the_dumbest_millionaire_in_his.mp4",
        "hook_comment": "Was Timothy Dexter the luckiest man in human history or secretly a genius? Drop your verdict below!",
        "tags": ["shorts", "history", "mystery", "millionaire", "truestory", "facts", "viral", "crime", "education"]
    },
    {
        "id": "hold_breath",
        "title": "What Holding Your Breath Actually Does",
        "project_dir": "projects/what_holding_your_breath_actua",
        "video_path": "projects/what_holding_your_breath_actua/renders/what_holding_your_breath_actua.mp4",
        "hook_comment": "What's the longest you've ever held your breath? Be honest in the comments!",
        "tags": ["shorts", "science", "biology", "humanbody", "health", "facts", "educational", "curiosity", "medical"]
    },
    {
        "id": "accidental_mayor",
        "title": "Accidental Mayor of an Entire Town",
        "project_dir": "projects/accidental_mayor_of_an_entire",
        "video_path": "projects/accidental_mayor_of_an_entire/renders/accidental_mayor_of_an_entire.mp4",
        "hook_comment": "Imagine running as a joke and waking up with an entire city budget. What's the first law you pass?",
        "tags": ["shorts", "comedy", "funny", "animation", "storytime", "viral", "humor", "election"]
    },
    {
        "id": "1panel_dev",
        "title": "Ditch Paid Server Dashboards with 1Panel",
        "project_dir": "projects/ditch_paid_server_dashboards_w",
        "video_path": "projects/ditch_paid_server_dashboards_w/renders/ditch_paid_server_dashboards_w.mp4",
        "hook_comment": "Comment 'PANEL' and I'll send you the direct verified 1-click Docker command and GitHub repo link!",
        "tags": ["shorts", "coding", "developer", "docker", "selfhosted", "opensource", "servers", "tech", "linux"]
    },
    {
        "id": "claude_cursor",
        "title": "Orchestrate Claude and Cursor for Free",
        "project_dir": "projects/orchestrate_claude_and_cursor",
        "video_path": "projects/orchestrate_claude_and_cursor/renders/orchestrate_claude_and_cursor.mp4",
        "hook_comment": "Comment 'SQUADR' below to get the full autonomous prompt instructions and setup script!",
        "tags": ["shorts", "ai", "claude", "cursor", "coding", "developer", "programming", "software", "techtools"]
    }
]

def post_youtube_comment(youtube_service, video_id, comment_text):
    """Posts a pinned or top-level engagement comment on YouTube Short."""
    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text
                    }
                }
            }
        }
        youtube_service.commentThreads().insert(part="snippet", body=body).execute()
        print(f"  ✓ YouTube engagement comment posted: \"{comment_text[:40]}...\"")
    except Exception as e:
        print(f"  Notice: Could not post YouTube comment ({e})")

def post_instagram_comment(media_id, comment_text):
    """Posts an engagement comment / comment hook on Instagram Reel."""
    if not media_id or not IG_ACCESS_TOKEN:
        return
    try:
        url = f"{GRAPH_API_BASE}/{media_id}/comments"
        data = urllib.parse.urlencode({
            "message": comment_text,
            "access_token": IG_ACCESS_TOKEN
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("id"):
                print(f"  ✓ Instagram engagement comment posted: \"{comment_text[:40]}...\"")
    except Exception as e:
        print(f"  Notice: Could not post Instagram comment ({e})")

def load_metadata(item):
    p_dir = Path(item["project_dir"])
    script_file = p_dir / "script.json"
    data = {}
    if script_file.exists():
        try:
            data = json.loads(script_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    title = data.get("title", item["title"])
    desc_base = data.get("description", "")
    
    # Format high-converting description
    hashtag_str = " ".join([f"#{t}" for t in item["tags"]])
    full_desc = f"{title}\n\n{desc_base}\n\n{item['hook_comment']}\n\n{hashtag_str}"

    return title, full_desc, item["tags"], item["hook_comment"]

def process_queue(privacy_status="public", delay_between_seconds=75):
    print("=" * 70)
    print(f"   CURIO CUT SYSTEMATIC BATCH UPLOADER ({len(QUEUE)} Videos)   ")
    print(f"   Privacy: {privacy_status} | Pacing Delay: {delay_between_seconds}s between posts   ")
    print("=" * 70)

    try:
        yt_service = get_authenticated_service()
    except Exception as e:
        print(f"Warning: YouTube auth check: {e}")
        yt_service = None

    results = []

    for idx, item in enumerate(QUEUE, start=1):
        v_path = Path(item["video_path"])
        if not v_path.exists():
            print(f"[{idx}/{len(QUEUE)}] Skipping missing video file: {v_path}")
            continue

        title, desc, tags, hook = load_metadata(item)
        print(f"\n[{idx}/{len(QUEUE)}] Processing: {title}")
        print(f"  File: {v_path} ({v_path.stat().st_size / (1024*1024):.2f} MB)")

        record = {"title": title, "youtube": None, "instagram": None}

        # 1. Upload to YouTube Shorts
        yt_id = None
        try:
            print("  [1/2] Uploading to YouTube Shorts...")
            upload_res = upload_short(str(v_path), title, description=desc, tags=tags, privacy_status=privacy_status)
            if isinstance(upload_res, tuple):
                yt_id, yt_url = upload_res
            else:
                yt_id = str(upload_res)
                yt_url = f"https://youtube.com/shorts/{yt_id}"

            record["youtube"] = yt_url
            print(f"  ✓ YouTube Short published: {yt_url}")

            # Post pinned engagement comment
            if yt_service and yt_id:
                post_youtube_comment(yt_service, yt_id, hook)

            try:
                notify_youtube_post(title, yt_url, yt_id, style=item.get("style", "viral-story"))
            except Exception as e:
                print(f"  Discord notify note: {e}")

        except Exception as e:
            print(f"  ✗ YouTube upload failed: {e}")
            try:
                notify_youtube_error(f"{title}: {e}")
            except Exception:
                pass

        # 15s pause before Instagram container creation to let temporary host settle
        time.sleep(15)

        # 2. Upload to Instagram Reels
        ig_id = None
        try:
            print("  [2/2] Uploading to Instagram Reels...")
            ig_caption = f"{title}\n\n{hook}\n\n" + " ".join([f"#{t}" for t in tags[:12]])
            ig_resp = upload_reel(str(v_path), caption=ig_caption)
            ig_id = ig_resp.get("id") if isinstance(ig_resp, dict) else str(ig_resp)
            ig_url = f"https://www.instagram.com/reel/{ig_id}/" if ig_id else "Uploaded"
            record["instagram"] = ig_url
            print(f"  ✓ Instagram Reel published: {ig_url}")

            # Post engagement comment hook
            if ig_id:
                post_instagram_comment(ig_id, hook)

            try:
                notify_instagram_post(ig_caption, ig_url, media_id=ig_id, title=title)
            except Exception as e:
                print(f"  Discord notify note: {e}")

        except Exception as e:
            print(f"  ✗ Instagram upload failed: {e}")
            try:
                notify_instagram_error(f"{title}: {e}")
            except Exception:
                pass

        results.append(record)

        # Safe anti-spam pacing delay between uploads
        if idx < len(QUEUE):
            print(f"  Pacing: Waiting {delay_between_seconds} seconds before next upload...")
            time.sleep(delay_between_seconds)

    print("\n" + "=" * 70)
    print("   BATCH UPLOAD COMPLETE   ")
    print("=" * 70)
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    privacy = sys.argv[1] if len(sys.argv) > 1 else "public"
    delay = int(sys.argv[2]) if len(sys.argv) > 2 else 75
    process_queue(privacy_status=privacy, delay_between_seconds=delay)
