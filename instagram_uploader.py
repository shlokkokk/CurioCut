# Uploads vertical mp4 to Instagram Reels via Meta Graph API
import os
import sys
import re
import time
import json
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# Load environment variables from .env
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

def _api_request(url, method="GET", headers=None, data=None):
    """Executes a JSON HTTP request using standard library urllib."""
    hdrs = headers.copy() if headers else {}
    req_data = None
    if data is not None:
        if isinstance(data, dict):
            req_data = urllib.parse.urlencode(data).encode("utf-8")
            if "Content-Type" not in hdrs:
                hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, (bytes, bytearray)):
            req_data = data
        elif isinstance(data, str):
            req_data = data.encode("utf-8")

    req = urllib.request.Request(url, data=req_data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            content = resp.read().decode("utf-8")
            try:
                return json.loads(content)
            except Exception:
                return content
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", error_body)
        except Exception:
            msg = error_body
        raise RuntimeError(f"Meta Graph API error ({e.code}): {msg}")

def upload_to_temp_host(video_path):
    """Uploads video to a fast, temporary hosting service so Meta servers can ingest it."""
    import subprocess
    v_path = Path(video_path).resolve()
    print(f"  Uploading video ({v_path.stat().st_size / (1024*1024):.1f} MB) to temporary ingest host...")

    # Strategy 1: Catbox / Litterbox (1 hour auto-delete)
    cmd = [
        "curl.exe" if os.name == 'nt' else "curl",
        "-s", "-F", "reqtype=fileupload",
        "-F", "time=1h",
        "-F", f"fileToUpload=@{str(v_path)}",
        "https://litterbox.catbox.moe/resources/internals/api.php"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        url = res.stdout.strip()
        if url.startswith("http") and ("catbox" in url or "litterbox" in url):
            print(f"  Ingest URL ready: {url}")
            return url
    except Exception as e:
        print(f"  Litterbox upload note: {e}")

    # Strategy 2: Uguu.se (3 hour auto-delete fallback)
    cmd_uguu = [
        "curl.exe" if os.name == 'nt' else "curl",
        "-s", "-F", f"files[]=@{str(v_path)}",
        "https://uguu.se/upload"
    ]
    try:
        res = subprocess.run(cmd_uguu, capture_output=True, text=True, timeout=180)
        data = json.loads(res.stdout)
        if data.get("success") and data.get("files"):
            url = data["files"][0]["url"]
            print(f"  Ingest URL ready: {url}")
            return url
    except Exception as e:
        print(f"  Uguu fallback note: {e}")

    raise RuntimeError("Failed to host video for Instagram Reels ingest. Check internet connection.")

def register_reel_edge(media_id, metadata=None, caption="", permalink=""):
    """Automatically registers published Reel comment-to-DM rules in Cloudflare Edge KV."""
    if not media_id:
        return False

    worker_url = os.environ.get("CURIOCUT_EDGE_URL", "https://curiocut-corn.pcgpt00.workers.dev").rstrip("/")
    dms_webhook = os.environ.get("DISCORD_WEBHOOK_DMS_SENT", "").strip()
    explicit_secret = os.environ.get("EDGE_REGISTER_SECRET", "").strip()
    auth_token = explicit_secret or (hashlib.sha256(dms_webhook.encode("utf-8")).hexdigest() if dms_webhook else "")
    if not auth_token:
        return False

    meta = dict(metadata or {})
    kw = (meta.get("cta_keyword") or meta.get("keyword") or "").strip()
    if not kw and caption:
        m = re.search(r"(?:comment|reply|drop)\s*['\"]([A-Za-z0-9_*\-\s]+?)['\"]", caption, flags=re.IGNORECASE)
        if m:
            kw = m.group(1).strip().upper()

    raw_url = (meta.get("resource_url") or "").strip()
    resource_url = raw_url if raw_url.startswith(("http://", "https://")) else ""
    mode = "dm" if (resource_url and meta.get("mode", "dm") != "story") else "story"

    payload = {
        "media_id": str(media_id),
        "title": meta.get("title") or (caption.splitlines()[0][:80] if caption else "CurioCut Reel"),
        "mode": mode,
        "keyword": kw if mode == "dm" else "",
        "resource_url": resource_url,
        "public_reply": meta.get("public_reply"),
        "dm_text": meta.get("dm_text"),
        "permalink": permalink or f"https://www.instagram.com/reel/{media_id}/",
        "category": meta.get("category") or ("story" if mode == "story" else "breaking_tech"),
        "is_claude_skill": bool(meta.get("is_claude_skill"))
    }

    for attempt in range(2):
        try:
            req = urllib.request.Request(
                f"{worker_url}/register-reel",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Curio-Auth": auth_token,
                    "User-Agent": "CurioCut-Publisher/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("ok"):
                    print(f"  Edge Comment-to-DM rule registered automatically ({mode}, keyword={kw or 'none'}).")
                    return True
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
            else:
                print(f"  Edge registry note: {e}")
    return False

def post_first_comment(media_id, comment_text, access_token):
    """Posts an initial creator comment after a Reel finishes propagating."""
    if not media_id or not comment_text or not access_token:
        return False
    time.sleep(3)
    for attempt in range(3):
        try:
            resp = _api_request(
                f"{GRAPH_API_BASE}/{media_id}/comments",
                method="POST",
                data={"message": comment_text, "access_token": access_token},
            )
            if isinstance(resp, dict) and resp.get("id"):
                print(f"  First comment posted (ID: {resp['id']}): {comment_text[:60]}...")
                return True
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"  First comment note: {e}")
    return False

def upload_reel(video_source, caption="New Short by CurioCut", ig_user_id=None, access_token=None, metadata=None, first_comment=None):
    """Full workflow to publish a Reel on Instagram.
    video_source can be either a public HTTPS URL or a local path to an MP4.
    """
    ig_user_id = ig_user_id or os.environ.get("INSTAGRAM_ACCOUNT_ID")
    access_token = access_token or os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    if not ig_user_id or not access_token:
        raise ValueError(
            "Missing Instagram credentials! Set INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN in .env or secrets."
        )

    print("\n" + "="*60)
    print("   INSTAGRAM REELS PUBLISHER   ")
    print("="*60)
    print(f"Account ID: {ig_user_id}")
    print(f"Caption: {caption[:50]}...")

    # Step 1: Ensure we have a public video URL for Meta ingest
    if str(video_source).startswith("http://") or str(video_source).startswith("https://"):
        video_url = str(video_source)
    else:
        video_url = upload_to_temp_host(video_source)

    # Step 2: Create Reels Container
    print("Creating Instagram Reels media container...")
    container_endpoint = f"{GRAPH_API_BASE}/{ig_user_id}/media"
    container_payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token
    }

    container_resp = _api_request(container_endpoint, method="POST", data=container_payload)
    container_id = container_resp.get("id")
    if not container_id:
        raise RuntimeError(f"Failed to create Instagram container: {container_resp}")

    print(f"Container created (ID: {container_id}). Waiting for Meta video processing...")

    # Step 3: Poll Container Status until FINISHED
    status_url = f"{GRAPH_API_BASE}/{container_id}?fields=status_code,status&access_token={access_token}"
    max_checks = 40  # up to ~3.5 minutes
    ready = False
    for i in range(max_checks):
        time.sleep(5)
        check = _api_request(status_url, method="GET")
        status_code = check.get("status_code")
        print(f"  Status check [{i+1}/{max_checks}]: {status_code} ({check.get('status', '')})")

        if status_code == "FINISHED":
            ready = True
            break
        elif status_code == "ERROR":
            raise RuntimeError(f"Meta failed to process Reel video: {check}")
        elif status_code == "EXPIRED":
            raise RuntimeError(f"Meta upload container expired: {check}")

    if not ready:
        raise TimeoutError("Meta took too long to process video. Upload timed out.")

    # Step 4: Publish Reel
    print("Publishing Reel to Instagram feed...")
    publish_endpoint = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token
    }
    publish_resp = _api_request(publish_endpoint, method="POST", data=publish_payload)
    media_id = publish_resp.get("id")
    if not media_id:
        raise RuntimeError(f"Failed to publish Reel: {publish_resp}")

    # Fetch permalink
    permalink = f"https://www.instagram.com/reel/{media_id}/"
    try:
        info = _api_request(f"{GRAPH_API_BASE}/{media_id}?fields=permalink&access_token={access_token}")
        if info.get("permalink"):
            permalink = info["permalink"]
    except Exception:
        pass

    print("\n" + "="*60)
    print(f"REEL SUCCESSFULLY PUBLISHED!")
    print(f"Instagram Media ID: {media_id}")
    print(f"Live URL: {permalink}")
    print("="*60 + "\n")

    register_reel_edge(media_id, metadata=metadata, caption=caption, permalink=permalink)
    if first_comment:
        post_first_comment(media_id, first_comment, access_token)
    return media_id, permalink

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python instagram_uploader.py <video_path_or_url> [caption]")
        sys.exit(1)

    vid = sys.argv[1]
    cap = sys.argv[2] if len(sys.argv) > 2 else "Watch daily viral shorts on CurioCut! #shorts #viral #story"
    upload_reel(vid, caption=cap)
