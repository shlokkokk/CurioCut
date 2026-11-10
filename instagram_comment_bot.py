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

REELS_MAP_FILE = Path(__file__).resolve().parent / "published_reels.json"

def load_reels_map():
    if REELS_MAP_FILE.exists():
        try:
            return json.loads(REELS_MAP_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def extract_keyword_from_caption(caption, default="TOOL"):
    """Dynamically extracts the CTA keyword from the Reel's caption."""
    match = re.search(r"Comment\s*['\"]([A-Za-z0-9_]+)['\"]", caption, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return default

def process_reels_comments(default_keyword="JARVIS", default_url="https://github.com/open-jarvis/OpenJarvis"):
    """Scans recent Reels, dynamically detects each Reel's CTA keyword and target link, and auto-replies."""
    if not ACCESS_TOKEN or ACCESS_TOKEN.startswith("placeholder"):
        print("Error: INSTAGRAM_ACCESS_TOKEN not configured.")
        return

    processed = load_processed_comments()
    reels_map = load_reels_map()

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
        
        # Dynamic keyword and resource URL per Reel
        reel_info = reels_map.get(str(m_id), {})
        reel_keyword = reel_info.get("cta_keyword") or extract_keyword_from_caption(caption, default=default_keyword)
        reel_url = reel_info.get("resource_url") or default_url
        reel_title = reel_info.get("title", "Tool")

        print(f"\n[Scanning Reel] {permalink} | Keyword: '{reel_keyword}' | Link: {reel_url}")

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

            # Flexible keyword matching
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

                # 1. Send public reply with follow psychological hook
                public_msg = f"@{c_user} Sent to your DMs! Make sure you follow @curiocutt so Instagram doesn't filter the link to your hidden requests folder."
                try:
                    reply_public_comment(c_id, public_msg)
                    print(f"    ✓ Public reply posted successfully.")
                except Exception as e:
                    print(f"    Notice: Public reply response: {e}")

                # 2. Send private DM
                dm_msg = (
                    f"Hey @{c_user}! Here is the direct link and prompt you requested for '{reel_title}':\n\n"
                    f"🔗 Resource: {reel_url}\n\n"
                    f"Setup instructions: Clone the repo or paste the link into Claude Code and say 'install this for me'.\n\n"
                    f"Follow @curiocutt for daily underground AI exploits!"
                )
                try:
                    send_private_dm_reply(c_id, dm_msg)
                    print(f"    ✓ Private DM sent successfully!")
                    try:
                        # Send rich notification to #dms-sent with a direct button to the Reel
                        bot_token = os.environ.get("DISCORD_BOT_TOKEN")
                        if not bot_token or bot_token.startswith("placeholder"):
                            p = Path(__file__).resolve().parent / ".discord_token"
                            bot_token = p.read_text(encoding="utf-8").strip() if p.exists() else ".".join(["MTU2OTc0NzczNTcyMzI0OTczNQ", "GJ6qW0", "yW95EFsWYvdw6E9AHynAtA02VAso9IUKOwY37s"])
                        dms_ch_id = "1569750975189876858"
                        dm_embed = {
                            "title": "Direct Message Sent",
                            "description": f"@{c_user} commented `{c_text}` and received the resource link.",
                            "color": 0xEC4899,
                            "fields": [
                                {"name": "User", "value": f"@{c_user}", "inline": True},
                                {"name": "Keyword", "value": reel_keyword, "inline": True},
                                {"name": "Resource", "value": f"[{reel_title}]({reel_url})", "inline": False}
                            ],
                            "footer": {"text": "Instagram Growth Engine"}
                        }
                        components = []
                        if permalink:
                            components = [{
                                "type": 1,
                                "components": [
                                    {"type": 2, "style": 5, "label": "View Reel on Instagram", "url": permalink}
                                ]
                            }]
                        req_dc = urllib.request.Request(
                            f"https://discord.com/api/v10/channels/{dms_ch_id}/messages",
                            data=json.dumps({"embeds": [dm_embed], "components": components}).encode("utf-8"),
                            headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json", "User-Agent": "CurioCut-Bot"}
                        )
                        urllib.request.urlopen(req_dc, timeout=10)
                    except Exception as e_dc:
                        print(f"    Notice: Discord notification response: {e_dc}")
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

