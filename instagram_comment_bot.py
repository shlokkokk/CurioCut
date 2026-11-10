"""Autonomous Instagram Comment-to-DM Engine for CurioCut.
Listens to comments on Instagram Reels and automatically:
1. Detects comments matching the Call-to-Action keyword (e.g. 'JARVIS', 'CLONE', 'AGENT').
2. Replies publicly to the comment ("Check your DMs! Sent you the full repo link and setup prompt 🚀") to trigger the algorithmic engagement multiplier.
3. Sends a private Direct Message (DM) to the commenter via Meta Graph API with the direct resource link.

100% Free. $0.00 cost. Zero ManyChat subscriptions. Uses permanent Meta Page Access Token.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"
HISTORY_FILE = Path(__file__).resolve().parent / "comment_bot_history.json"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

IG_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841434641576009")
ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

def load_processed_comments():
    if HISTORY_FILE.exists():
        try:
            return set(json.loads(HISTORY_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_processed_comment(comment_id):
    processed = load_processed_comments()
    processed.add(comment_id)
    HISTORY_FILE.write_text(json.dumps(list(processed), indent=2), encoding="utf-8")

def get_recent_media():
    """Fetches the latest published Reels/Media IDs from CurioCut Instagram account."""
    url = f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/media?fields=id,caption,media_type,permalink,timestamp&limit=10&access_token={ACCESS_TOKEN}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])

def get_media_comments(media_id):
    """Fetches all top-level comments on a specific Reel."""
    url = f"https://graph.facebook.com/v21.0/{media_id}/comments?fields=id,text,username,timestamp&limit=50&access_token={ACCESS_TOKEN}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])

def reply_public_comment(comment_id, text):
    """Posts a public reply under the user's comment."""
    url = f"https://graph.facebook.com/v21.0/{comment_id}/replies"
    payload = urllib.parse.urlencode({
        "message": text,
        "access_token": ACCESS_TOKEN
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def send_private_dm_reply(comment_id, message_text):
    """Sends a private DM to the user who left the comment using Meta Graph API."""
    url = f"https://graph.facebook.com/v21.0/me/messages"
    payload = json.dumps({
        "recipient": {"comment_id": comment_id},
        "message": {"text": message_text}
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{url}?access_token={ACCESS_TOKEN}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def extract_keyword_from_caption(caption, default="TOOL"):
    """Dynamically extracts the CTA keyword from the Reel's caption."""
    match = re.search(r"Comment\s*['\"]([A-Za-z0-9_]+)['\"]", caption, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return default

def process_reels_comments(default_keyword="JARVIS", default_url="https://github.com/open-jarvis/OpenJarvis"):
    """Scans recent Reels, dynamically detects each Reel's CTA keyword, and auto-replies."""
    if not ACCESS_TOKEN or ACCESS_TOKEN.startswith("placeholder"):
        print("Error: INSTAGRAM_ACCESS_TOKEN not configured.")
        return

    processed = load_processed_comments()
    print("\n" + "="*60)
    print("   CURIO CUT AUTONOMOUS COMMENT-TO-DM BOT   ")
    print("="*60)

    try:
        media_list = get_recent_media()
        print(f"Found {len(media_list)} recent posts on @curiocutt.")
    except Exception as e:
        print(f"Error fetching media: {e}")
        return

    total_replied = 0
    replied_users_per_media = {}

    for m in media_list:
        m_id = m.get("id")
        caption = m.get("caption", "")
        permalink = m.get("permalink", "")
        
        # Dynamic keyword detection per Reel
        reel_keyword = extract_keyword_from_caption(caption, default=default_keyword)
        print(f"\n[Scanning Reel] {permalink} | Target Keyword: '{reel_keyword}'")

        try:
            comments = get_media_comments(m_id)
        except Exception as e:
            print(f"  Error fetching comments for {m_id}: {e}")
            continue

        replied_users_per_media[m_id] = set()

        for c in comments:
            c_id = c.get("id")
            c_text = c.get("text", "").strip()
            c_user = c.get("username", "user")

            if c_id in processed or c_user in replied_users_per_media[m_id]:
                continue

            # Flexible keyword matching: matches keyword or 'send link' / 'repo' / 'prompt'
            clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', c_text).upper()
            is_match = (
                reel_keyword in clean_text
                or "SEND LINK" in clean_text
                or "GIVE LINK" in clean_text
                or "REPO" in clean_text
                or "PROMPT" in clean_text
            )

            if is_match:
                print(f"\n[!] MATCH FOUND on {permalink}:")
                print(f"    User: @{c_user} | Comment: '{c_text}'")

                # 1. Send public reply
                public_msg = f"@{c_user} Check your DMs! Sent you the full setup link and prompt 🚀"
                try:
                    reply_public_comment(c_id, public_msg)
                    print(f"    ✓ Public reply posted successfully.")
                except Exception as e:
                    print(f"    Notice: Public reply response: {e}")

                # 2. Send private DM
                dm_msg = (
                    f"Hey @{c_user}! Here is the direct link and prompt you requested for '{reel_keyword}':\n\n"
                    f"🔗 Resource: {default_url}\n\n"
                    f"Setup instructions: Clone the repo or paste the link into Claude Code and say 'install this for me'.\n\n"
                    f"Follow @curiocutt for daily underground AI exploits!"
                )
                try:
                    send_private_dm_reply(c_id, dm_msg)
                    print(f"    ✓ Private DM sent successfully!")
                except Exception as e:
                    print(f"    Notice: Private DM response: {e}")

                save_processed_comment(c_id)
                replied_users_per_media[m_id].add(c_user)
                total_replied += 1
                time.sleep(1.5)

    print(f"\nCompleted scan. Replied to {total_replied} new commenters.")

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "JARVIS"
    url = sys.argv[2] if len(sys.argv) > 2 else "https://github.com/open-jarvis/OpenJarvis"
    process_reels_comments(keyword=kw, resource_url=url)

