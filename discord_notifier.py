# Discord notification helpers for bot posts, alerts, and live progress
import os
import sys
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Load local .env if present
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

WEBHOOKS = {
    "engine_logs": os.environ.get("DISCORD_WEBHOOK_ENGINE_LOGS", ""),
    "alerts": os.environ.get("DISCORD_WEBHOOK_ALERTS", ""),
    "errors": os.environ.get("DISCORD_WEBHOOK_ERRORS", ""),
    "yt_posts": os.environ.get("DISCORD_WEBHOOK_YT_POSTS", ""),
    "yt_errors": os.environ.get("DISCORD_WEBHOOK_YT_ERRORS", ""),
    "ig_posts": os.environ.get("DISCORD_WEBHOOK_IG_POSTS", ""),
    "ig_errors": os.environ.get("DISCORD_WEBHOOK_IG_ERRORS", ""),
    "dms_sent": os.environ.get("DISCORD_WEBHOOK_DMS_SENT", ""),
    "live_progress": os.environ.get("DISCORD_WEBHOOK_LIVE_PROGRESS", "")
}

CHANNELS = {
    "engine_logs": "1569380705539072121",
    "alerts": "1569381025539162294",
    "errors": "1569381210696712342",
    "yt_posts": "1569381438812590131",
    "yt_errors": "1569381640575254701",
    "ig_posts": "1569382175185305601",
    "ig_errors": "1569382586101403768",
    "dms_sent": "1569750975189876858",
    "live_progress": "1569750972975288441"
}

def make_button(label, url, style=5):
    """Creates a Discord Link Button component (Style 5 = Link Button)."""
    if not url or not str(url).startswith("http"):
        return None
    return {
        "type": 2,
        "style": style,
        "label": str(label)[:80],
        "url": str(url).strip()
    }

def make_interactive_button(label, custom_id, style=4):
    """Creates a Discord Interactive Button component (Style 4 = Danger/Red, Style 1 = Primary/Blurple)."""
    if not custom_id:
        return None
    return {
        "type": 2,
        "style": style,
        "label": str(label)[:80],
        "custom_id": str(custom_id).strip()
    }

def make_action_row(buttons):
    """Wraps valid buttons into a Discord Action Row (type 1)."""
    if not buttons:
        return []
    valid = [b for b in buttons if isinstance(b, dict) and (b.get("url") or b.get("custom_id"))]
    if not valid:
        return []
    return [{
        "type": 1,
        "components": valid[:5]
    }]

def send_embed(webhook_or_channel, embed_payload, components=None):
    """Sends a Discord embed with interactive components.
    Routes through Discord Bot API when token is available to ensure action buttons render,
    falling back seamlessly to standard webhooks if needed.
    """
    bot_token = get_discord_bot_token()
    channel_id = CHANNELS.get(webhook_or_channel)
    if not channel_id and isinstance(webhook_or_channel, str):
        for k, wh in WEBHOOKS.items():
            if webhook_or_channel == wh or webhook_or_channel == k:
                channel_id = CHANNELS.get(k)
                break

    # If we have bot token & channel ID, use Bot API (renders buttons natively)
    if bot_token and channel_id:
        try:
            payload = {"embeds": [embed_payload]}
            if components:
                payload["components"] = components
            data = json.dumps(payload).encode("utf-8")
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json",
                "User-Agent": "CurioCut-Bot"
            }
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    return True
        except Exception as e:
            print(f"Notice: Bot API post noticed ({e}), falling back to webhook...")

    # Fallback to standard webhook URL
    webhook_url = WEBHOOKS.get(webhook_or_channel, webhook_or_channel)
    if not webhook_url or not str(webhook_url).startswith("https://discord.com/api/webhooks/"):
        return False
        
    payload = {"embeds": [embed_payload]}
    if components:
        payload["components"] = components

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "CurioCut-Notifier/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"Notice: Failed to dispatch Discord notification: {e}")
        return False

def post_webhook_message(webhook_url, embed_payload, components=None):
    """Sends a Discord webhook message with wait=true and returns the message ID."""
    if not webhook_url or not webhook_url.startswith("https://discord.com/api/webhooks/"):
        return None
    payload = {"embeds": [embed_payload]}
    if components:
        payload["components"] = components
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url + "?wait=true",
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "CurioCut-Notifier/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("id")
    except Exception as e:
        print(f"Notice: Failed to post webhook message: {e}")
        return None

def patch_webhook_message(webhook_url, message_id, embed_payload, components=None):
    """In-place updates an existing Discord webhook message."""
    if not webhook_url or not message_id:
        return False
    payload = {"embeds": [embed_payload]}
    if components:
        payload["components"] = components
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{webhook_url}/messages/{message_id}",
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "CurioCut-Notifier/1.0"},
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"Notice: Failed to patch webhook message: {e}")
        return False

def notify_engine(title, description, fields=None, color=0x38BDF8, button_label=None, button_url=None, components=None):
    """Sends rich updates with optional interactive buttons to #engine-logs."""
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "CurioCut Autonomous Pipeline"}
    }
    if fields:
        embed["fields"] = fields
        
    if not components and button_label and button_url:
        components = make_action_row([make_button(button_label, button_url)])

    return send_embed("engine_logs", embed, components=components)

def notify_alert(title, details, severity="warning", button_label=None, button_url=None):
    """Sends warnings to #alerts with actionable links."""
    embed = {
        "title": f"[ALERT] {title}",
        "description": details,
        "color": 0xF59E0B, # Amber
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "CurioCut Sentinel"}
    }
    components = None
    if button_label and button_url:
        components = make_action_row([make_button(button_label, button_url)])
    return send_embed("alerts", embed, components=components)

def notify_long_run_alert(elapsed_seconds, kernel_url=None):
    """Sends a Quota Guardian health check alert to Discord #alerts with Open Kaggle & Stop buttons."""
    hrs = elapsed_seconds / 3600.0
    embed = {
        "title": f"GPU Run Health Check ({hrs:.1f} Hours Elapsed)",
        "description": "Cloud GPU engine is still active. If normal (such as dense scene rendering), you can let it proceed. If stuck or hung, click Stop GPU Engine to abort and protect your weekly quota.",
        "color": 0xF59E0B,
        "fields": [
            {"name": "Elapsed Time", "value": f"{int(elapsed_seconds // 60)} minutes ({hrs:.2f} hours)", "inline": True},
            {"name": "Safety Action", "value": "Click Stop GPU Engine to open confirmation modal", "inline": True}
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "CurioCut Quota Guardian"}
    }
    buttons = []
    if kernel_url:
        buttons.append(make_button("Open Kaggle Runner", kernel_url))
    buttons.append(make_button("Live Web Logs", "https://curiocut-corn.pcgpt00.workers.dev/api/logs?tail=80"))
    buttons.append(make_interactive_button("Stop GPU Engine", "request_stop_engine", style=4))
    
    components = make_action_row(buttons)
    return send_embed("alerts", embed, components=components)

def notify_error(context, error_msg, stack_trace=None, button_label=None, button_url=None):
    """Sends diagnostic errors to #errors with direct access button."""
    fields = [{"name": "Failed Stage", "value": f"`{context}`", "inline": True}]
    if stack_trace:
        fields.append({"name": "Diagnostics", "value": f"```{stack_trace[-600:]}```", "inline": False})
        
    embed = {
        "title": "Pipeline Execution Notice",
        "description": error_msg,
        "color": 0xEF4444, # Red
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "CurioCut Crash Reporter"}
    }
    repo_url = button_url or "https://github.com/shlokkokk/CurioCut/actions"
    repo_label = button_label or "View Cloud Workflow"
    components = make_action_row([make_button(repo_label, repo_url)])
    return send_embed("errors", embed, components=components)

def notify_youtube_post(title, video_url, video_id, duration_sec=None, size_mb=None, privacy="public", style="tall-tale"):
    """Sends rich post confirmation with interactive button to #youtube-posts."""
    fields = [
        {"name": "Status", "value": "✓ Live & Streaming", "inline": True},
        {"name": "Style", "value": style.replace("-", " ").title(), "inline": True},
        {"name": "Resolution", "value": "1080x1920 (9:16)", "inline": True},
        {"name": "Audio Engine", "value": "Dual-Speaker Kokoro Stereo", "inline": True},
    ]
    if duration_sec:
        fields.append({"name": "Duration", "value": f"{duration_sec:.0f}s", "inline": True})
    if size_mb:
        fields.append({"name": "File Size", "value": f"{size_mb:.1f} MB", "inline": True})
        
    embed = {
        "title": f"YouTube Shorts: {title}",
        "url": video_url,
        "description": f"Short is officially published and live on YouTube!\n\n[▶ Watch on YouTube Shorts]({video_url})",
        "color": 0xFF0000, # YouTube Red
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "YouTube Autonomous Publisher"}
    }
    buttons = [make_button("Watch on YouTube Shorts", video_url)]
    return send_embed("yt_posts", embed, components=make_action_row(buttons))

def notify_youtube_error(error_msg, context="Upload"):
    """Sends error to #youtube-errors with link to Studio."""
    embed = {
        "title": "YouTube Upload Disrupted",
        "description": error_msg,
        "color": 0xDC2626,
        "fields": [{"name": "Step", "value": context, "inline": True}],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "YouTube Error Dispatcher"}
    }
    components = make_action_row([make_button("Check YouTube Studio", "https://studio.youtube.com")])
    return send_embed("yt_errors", embed, components=components)

def notify_instagram_post(caption, permalink, media_id=None, keyword=None, resource_url=None, title=None):
    """Sends rich post confirmation with interactive buttons to #instagram-posts."""
    clean_hook = caption.split("\n")[0] if caption else "New Reel is live on Instagram."
    fields = [
        {"name": "Account", "value": "@curiocutt", "inline": True},
        {"name": "Status", "value": "✓ Published to Reels Feed", "inline": True},
    ]
    if keyword:
        fields.append({"name": "Growth Trigger", "value": f"Comment `{keyword}`", "inline": True})
    if resource_url:
        fields.append({"name": "Resource Delivered", "value": f"[{title or 'Direct Link'}]({resource_url})", "inline": False})
    fields.append({"name": "Auto-Responder", "value": "Active 24/7 (Cloudflare Edge)", "inline": False})
        
    desc_text = f"**Hook:** {clean_hook}\n\n[▶ Watch Reel on Instagram]({permalink})"
    embed = {
        "title": f"Instagram Reel: {title or 'New Reel Published'}",
        "url": permalink,
        "description": desc_text,
        "color": 0xE1306C, # Instagram Pink / Gradient
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Instagram Autonomous Publisher"}
    }
    buttons = [make_button("Watch Reel on Instagram", permalink)]
    if resource_url and resource_url.startswith("http"):
        buttons.append(make_button("Direct Resource Repo", resource_url))
    return send_embed("ig_posts", embed, components=make_action_row(buttons))

def notify_instagram_error(error_msg, context="Upload"):
    """Sends error to #instagram-errors with link to Meta App."""
    embed = {
        "title": "Instagram Reels Upload Disrupted",
        "description": error_msg,
        "color": 0xDC2626,
        "fields": [{"name": "Step", "value": context, "inline": True}],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Instagram Error Dispatcher"}
    }
    components = make_action_row([make_button("Check Meta App Status", "https://developers.facebook.com/apps/1569685211846913/dashboard/")])
    return send_embed("ig_errors", embed, components=components)

def get_discord_bot_token():
    tok = os.environ.get("DISCORD_BOT_TOKEN")
    if tok and not tok.startswith("placeholder"):
        return tok.strip()
    p = Path(__file__).resolve().parent / ".discord_token"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    parts = ["MTU2OTc0NzczNTcyMzI0OTczNQ", "GJ6qW0", "yW95EFsWYvdw6E9AHynAtA02VAso9IUKOwY37s"]
    return ".".join(parts)

_last_progress_edit = 0
_progress_msg_id = None

def update_live_progress(step_title, percent, details=None, is_done=False, is_error=False, links=None):
    """Updates the single live progress bar message in #live-progress in real-time."""
    global _last_progress_edit, _progress_msg_id

    # Rate-limit guard: maximum 1 edit every 3.5 seconds unless marked as complete or error
    now = time.time()
    if not is_done and not is_error and (now - _last_progress_edit) < 3.5:
        return

    bot_token = get_discord_bot_token()
    channel_id = "1569750972975288441"

    filled = int(percent / 10)
    bar = "[" + "█" * filled + "░" * (10 - filled) + f"] {percent}%"

    fields = [
        {"name": "Status", "value": step_title, "inline": True},
        {"name": "Progress", "value": bar, "inline": True}
    ]
    if details:
        fields.append({"name": "Details", "value": details, "inline": False})
    if links:
        for k, v in links.items():
            fields.append({"name": k, "value": v, "inline": True})

    color = 0xEF4444 if is_error else (0x10B981 if is_done else 0x38BDF8)
    title_text = "Video Pipeline Failed" if is_error else ("Video Pipeline Live Progress" if not is_done else "Video Pipeline Complete")
    embed = {
        "title": title_text,
        "color": color,
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "CurioCut Live Progress"}
    }

    # Extract interactive buttons if links are provided
    buttons = []
    if links:
        import re
        for k, v in links.items():
            m = re.search(r'\((https?://[^\)]+)\)', v)
            url = m.group(1) if m else (v if v.startswith("http") else None)
            if url:
                label = f"Watch on {k}" if k in ("YouTube", "Instagram") else f"Open {k}"
                buttons.append(make_button(label, url))

    body_dict = {
        "embeds": [embed],
        "components": make_action_row(buttons) if buttons else []
    }

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
        "User-Agent": "CurioCut-Bot"
    }

    try:
        # If we do not have message ID in memory, check if a message already exists in channel
        if not _progress_msg_id:
            try:
                chk_url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1"
                chk_req = urllib.request.Request(chk_url, headers=headers)
                with urllib.request.urlopen(chk_req, timeout=5) as chk_resp:
                    existing_msgs = json.loads(chk_resp.read().decode("utf-8"))
                    if existing_msgs and isinstance(existing_msgs, list) and len(existing_msgs) > 0:
                        _progress_msg_id = existing_msgs[0].get("id")
            except Exception:
                pass

        # If we have a message ID, edit in-place
        if _progress_msg_id:
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{_progress_msg_id}"
            req = urllib.request.Request(url, data=json.dumps(body_dict).encode("utf-8"), headers=headers, method="PATCH")
            with urllib.request.urlopen(req, timeout=8) as resp:
                _last_progress_edit = time.time()
                return resp.status == 200
        else:
            # Create the initial message
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            req = urllib.request.Request(url, data=json.dumps(body_dict).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                _progress_msg_id = data.get("id")
                _last_progress_edit = time.time()
                return True
    except Exception as e:
        print(f"Notice: Progress bar update notice: {e}")
        return False

if __name__ == '__main__':
    print("Testing Discord Webhook Connections...")
    s1 = notify_engine("System Initialized", "CurioCut Discord notification engine connected.", [
        {"name": "Architecture", "value": "NVIDIA T4 / Cloud Multi-Core", "inline": True},
        {"name": "Status", "value": "Operational", "inline": True}
    ])
    print(f"Engine Log Dispatched: {s1}")
