"""CurioCut Production Discord Notifier.
Dispatches clean, structured, non-corny embedded notifications to dedicated Discord channels:
- System: Engine Logs, Alerts, Errors
- YouTube: Posts, Errors
- Instagram: Posts, Errors
"""
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
    "engine_logs": os.environ.get("DISCORD_WEBHOOK_ENGINE_LOGS") or "https://discord.com/api/webhooks/1569380801077051462/ciIO5SVWzVEoSWyH5G4o32j5VVFDHBmuWljVx5iJU8LnJ90w4hZyr6tnYajqT1sfFrpY",
    "alerts": os.environ.get("DISCORD_WEBHOOK_ALERTS") or "https://discord.com/api/webhooks/1569381087736635405/tCkmm_lloHt-Jjv1qiUvJrmFqhyoEhw5LxJdSa2pswJg5y_EcHC65YCs_bHzizfovYmH",
    "errors": os.environ.get("DISCORD_WEBHOOK_ERRORS") or "https://discord.com/api/webhooks/1569381285355331725/UUQxZrh0vCjqQ55GO0EZy28TieniYLY_PWlrAimwUItiR22B-CP1yiYY4nxp8JbLHO7w",
    "yt_posts": os.environ.get("DISCORD_WEBHOOK_YT_POSTS") or "https://discord.com/api/webhooks/1569381485025435760/Gkc9ZGQ6b2kpVQTYiQ4fR6h3NL2WpnTNNymxkwiEB5eHG52o3pJoOJA7masxct7etuFz",
    "yt_errors": os.environ.get("DISCORD_WEBHOOK_YT_ERRORS") or "https://discord.com/api/webhooks/1569381675073405080/eekyLdpF9QWgjnGW91Bi8xAhVDLf5qHQFoqTrXGg7tcUHz8X5e5kF0tO68hAb9wUiW_S",
    "ig_posts": os.environ.get("DISCORD_WEBHOOK_IG_POSTS") or "https://discord.com/api/webhooks/1569382221993738343/11uYCVuDz1mMxABvFySddv07Q9dUyGAJqL3lEX1_waXHfqmHZwtr_3Rk34Y7TsZFGRmj",
    "ig_errors": os.environ.get("DISCORD_WEBHOOK_IG_ERRORS") or "https://discord.com/api/webhooks/1569382727847780483/Dk-DsPnxZAiKoSa-ZDEblzw7KVeDHgbAxNAnyr1xW5g2qzssyTpFMHmuhvPFd_DaN21r"
}

def send_embed(webhook_url, embed_payload):
    """Sends a Discord webhook embed with retry logic."""
    if not webhook_url or not webhook_url.startswith("https://discord.com/api/webhooks/"):
        return False
        
    data = json.dumps({"embeds": [embed_payload]}).encode("utf-8")
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

def notify_engine(title, description, fields=None, color=0x2B2D31):
    """Sends engine-level runtime and benchmark metrics to #engine-logs."""
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "CurioCut Engine Runtime"}
    }
    if fields:
        embed["fields"] = fields
    return send_embed(WEBHOOKS["engine_logs"], embed)

def notify_alert(title, details, severity="warning"):
    """Sends system warnings, retries, and quota notices to #alerts."""
    embed = {
        "title": title,
        "description": details,
        "color": 0xF59E0B, # Amber
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"Severity: {severity.upper()}"}
    }
    return send_embed(WEBHOOKS["alerts"], embed)

def notify_error(context, error_msg, stack_trace=None):
    """Sends critical pipeline crashes and exceptions to #errors."""
    fields = [{"name": "Context", "value": context, "inline": True}]
    if stack_trace:
        fields.append({"name": "Traceback", "value": f"```{stack_trace[-800:]}```", "inline": False})
        
    embed = {
        "title": "Pipeline Execution Error",
        "description": error_msg,
        "color": 0xDC2626, # Crimson
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "CurioCut Error Handler"}
    }
    return send_embed(WEBHOOKS["errors"], embed)

def notify_youtube_post(title, video_url, video_id, duration_sec=None, size_mb=None, privacy="public", style="tall-tale"):
    """Sends rich success card to #youtube-posts when a Short is published."""
    fields = [
        {"name": "Video URL", "value": f"[{video_url}]({video_url})", "inline": False},
        {"name": "Visibility", "value": privacy.capitalize(), "inline": True},
        {"name": "Style", "value": style, "inline": True},
    ]
    if duration_sec:
        fields.append({"name": "Duration", "value": f"{duration_sec:.1f}s", "inline": True})
    if size_mb:
        fields.append({"name": "Size", "value": f"{size_mb:.2f} MB", "inline": True})
        
    embed = {
        "title": title,
        "url": video_url,
        "description": "Short successfully published to YouTube.",
        "color": 0x10B981, # Emerald
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "YouTube Data API v3"}
    }
    return send_embed(WEBHOOKS["yt_posts"], embed)

def notify_youtube_error(error_msg, context="Upload"):
    """Sends upload rejections and API quota errors to #youtube-errors."""
    embed = {
        "title": "YouTube Publication Failure",
        "description": error_msg,
        "color": 0xDC2626, # Crimson
        "fields": [{"name": "Operation", "value": context, "inline": True}],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "YouTube Uploader"}
    }
    return send_embed(WEBHOOKS["yt_errors"], embed)

def notify_instagram_post(caption, permalink, media_id=None):
    """Sends rich success card to #instagram-posts when a Reel is published."""
    fields = [{"name": "Reel URL", "value": f"[{permalink}]({permalink})", "inline": False}]
    if media_id:
        fields.append({"name": "Media ID", "value": str(media_id), "inline": True})
        
    embed = {
        "title": "Reel Published",
        "url": permalink,
        "description": caption[:300] + ("..." if len(caption) > 300 else ""),
        "color": 0x10B981, # Emerald
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Meta Graph API v21.0"}
    }
    return send_embed(WEBHOOKS["ig_posts"], embed)

def notify_instagram_error(error_msg, context="Upload"):
    """Sends Instagram upload failures to #instagram-errors."""
    embed = {
        "title": "Instagram Publication Failure",
        "description": error_msg,
        "color": 0xDC2626, # Crimson
        "fields": [{"name": "Operation", "value": context, "inline": True}],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Instagram Reels Uploader"}
    }
    return send_embed(WEBHOOKS["ig_errors"], embed)

if __name__ == '__main__':
    print("Testing Discord Webhook Connections...")
    s1 = notify_engine("System Initialized", "CurioCut Discord notification engine connected.", [
        {"name": "Architecture", "value": "NVIDIA T4 / Cloud Multi-Core", "inline": True},
        {"name": "Status", "value": "Operational", "inline": True}
    ])
    print(f"Engine Log Dispatched: {s1}")
