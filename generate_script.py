
"""AI Viral Script & Retention Engineer for CurioCut.
Autonomous multi-niche storyteller powered by Dual-Brain AI (Google Gemini + Groq LPU):
- Primary Creative Brain: Google Gemini 2.5/2.0 Flash (100% human-like witty viral storytelling)
- Backup Speed Brain: Groq LPU with Meta Llama 3.3 70B
- Offline Redundant Brain: Evergreen Master Vault (50+ 10/10 master scripts)
"""
import os
import sys
import json
import time
import random
import re
import urllib.request
import urllib.parse
from pathlib import Path

# Load environment variables
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

HISTORY_FILE = Path(__file__).resolve().parent / "history.json"

PSYCHOLOGY_SYSTEM_PROMPT = """You are a top-tier viral YouTube Shorts & Instagram Reels creator.
You write addictive, 100% human-sounding short-form stories across 3 viral niches:
1. SPICY RELATIONSHIP DRAMA & REVENGE: Petty betrayals, secret bank accounts, wedding exposures, toxic family drama.
2. WILD HEISTS & LOOPHOLES: Unbelievable true glitches, real people who outsmarted massive systems, crazy cons.
3. INTERNET BRAINROT & ABSURDITY: Pettiest billionaire antics, weird lawsuits, insane algorithmic accidents.

HUMAN VOICE & TONE (CRITICAL):
- Speak like a witty, charismatic 24-year-old friend telling a jaw-dropping story over late-night coffee.
- Use natural spoken connectors: "Get this,", "Except here's the catch:", "Turns out,", "Bro literally...", "No seriously,", "Wait, it gets crazier:".
- Sentences must be short, punchy, and conversational.
- Spell out ALL numbers as spoken words ("eighty thousand dollars", "two in the morning", "five million").

STRICT NEGATIVE CONSTRAINTS (ZERO AI CLICHES):
- NEVER write like a Wikipedia summary, textbook, or documentary narrator.
- NEVER use these dead AI buzzwords or phrases (instant disqualification):
  "little did he know", "in a shocking turn of events", "testament to", "against all odds", "unbeknownst", "the stage was set", "it wasn't long before", "leaving him with", "a lesson in", "delve", "bustling", "beacon", "tale of", "journey", "the unbelievable true case of".
- Start IMMEDIATELY with the shocking premise in cut 1. Never start with "Did you know", "Imagine", or "In this video".

CAMERA CUT SEGMENTATION:
- Each entry in 'lines' is ONE FAST CAMERA CUT (1.5 to 2.5 seconds, 8 to 15 spoken words).
- Total lines: 8 to 12 cuts (target 40 to 55 seconds total runtime).
- Do NOT include any 'caps' field. Only provide 'text'. The video engine automatically generates word-by-word synced captions for 100% of spoken words.

JSON OUTPUT FORMAT:
Strictly valid JSON:
{
  "title": "Short Catchy Viral Title (under 7 words)",
  "voice": "am_michael",
  "speed": 1.05,
  "lead": 0.3,
  "outro": 1.0,
  "gap": 0.18,
  "music": "tension",
  "lines": [
    { "text": "Shocking hook cut..." },
    { "text": "Escalation cut..." },
    ...
    { "text": "Satisfying punchline or twist...", "gap": 0.3 }
  ]
}
"""

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(title, topic, style=None):
    history = load_history()
    history.append({"title": title, "topic": topic, "style": style})
    HISTORY_FILE.write_text(json.dumps(history[-50:], indent=2), encoding="utf-8")

def call_gemini_single(prompt, api_key, model):
    """Direct HTTP call to a specific Gemini model via REST API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {
            "parts": [{"text": PSYCHOLOGY_SYSTEM_PROMPT}]
        },
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.8,
            "responseMimeType": "application/json"
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)

def build_quality_ladder(key1, key2):
    """Quality-First Tiered Matrix across Dual Keys.
    Prioritizes deep human psychology, narrative tension, and Pro-reasoning FIRST across BOTH keys
    before ever dropping down to high-velocity flash or lite tiers.
    """
    ladder = []
    # Tier 1: Absolute Peak Storytelling, Narrative Psychology & Pro Reasoning
    if key1:
        ladder.append((key1, "gemini-pro-latest", "Key 1 [Peak Pro Reasoning]"))
    if key2:
        ladder.append((key2, "gemini-3.1-pro-preview", "Key 2 [Peak Pro Alternate]"))

    # Tier 2: Peak Creative Dynamic Nuance (3.5 & 3.8 Flash)
    if key1:
        ladder.append((key1, "gemini-3.5-flash", "Key 1 [Creative 3.5 Flash]"))
    if key2:
        ladder.append((key2, "gemini-3.5-flash", "Key 2 [Creative 3.5 Alternate]"))
    if key2:
        ladder.append((key2, "gemini-3.8-flash", "Key 2 [Ultra-Fast 3.8 Flash]"))

    # Tier 3: High-Velocity Fallbacks (Only if Pro & 3.5 hit quota on both keys)
    if key1:
        ladder.append((key1, "gemini-flash-latest", "Key 1 [Flash Latest]"))
    if key2:
        ladder.append((key2, "gemini-flash-lite-latest", "Key 2 [Flash Lite]"))
    if key1:
        ladder.append((key1, "gemini-3.1-flash-lite", "Key 1 [Flash Lite]"))

    return ladder

def call_groq_api(prompt, api_key):
    """Backup Brain: Direct HTTP call to Groq LPU API using urllib (Zero dependencies)."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    models_to_try = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b"
    ]

    last_error = None
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": PSYCHOLOGY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.75,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All Groq models failed. Last error: {last_error}")

def generate_script(topic=None):
    """Dual-Brain Script Generator: Tries Gemini -> Groq -> Offline Master Vault."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    if topic:
        seed_title = topic
        user_prompt = f"Write a gripping, high-retention viral short about this topic:\n{topic}\n\nMake it gritty, human, and dramatic. No childish cliches. Spell all numbers as words."
        style = "night-file"
    else:
        # Autonomous multi-niche harvesting
        from story_harvester import get_next_daily_story
        story_info = get_next_daily_story()
        seed_title = story_info["title"]
        premise = story_info["premise"]
        style = story_info["style"]
        niche = story_info["niche"]

        user_prompt = (
            f"Write an addictive, 100% human-sounding viral short based on this premise:\n"
            f"Premise Topic: {seed_title}\n"
            f"Facts / Event: {premise}\n\n"
            f"CRITICAL STORYTELLING RULES:\n"
            f"- DO NOT write a dry documentary or encyclopedia summary.\n"
            f"- Completely dramatize this from the perspective of an energetic creator telling an unbelievable story to a friend.\n"
            f"- Cut 1 MUST be a shocking pattern interrupt hook.\n"
            f"- Every cut must advance the story with high tension.\n"
            f"- Spell all numbers as words ('eighty thousand dollars', 'three in the morning').\n"
            f"- Output strictly the JSON schema with 'text' lines (NO 'caps' field)."
        )

    print("\n" + "="*60)
    print("   CURIO CUT DUAL-BRAIN SCRIPT ENGINE   ")
    print("="*60)
    print(f"Title: {seed_title}")

    data = None

    # 1. Primary Brain: Quality-First Interleaved Gemini Ladder
    key1 = os.environ.get("GEMINI_API_KEY")
    key2 = os.environ.get("GEMINI_API_KEY_BACKUP")
    quality_ladder = build_quality_ladder(key1, key2)

    for idx, (g_key, model_name, tier_label) in enumerate(quality_ladder):
        try:
            print(f"🧠 Requesting script from {tier_label} ({model_name})...")
            data = call_gemini_single(user_prompt, g_key, model_name)
            print(f"  ✓ Successfully crafted with {tier_label} ({model_name})!")
            break
        except Exception as e:
            err_str = str(e)
            print(f"  {tier_label} notice: {err_str}.")
            if "429" in err_str:
                time.sleep(1.5)
            if idx == len(quality_ladder) - 1:
                print("  All Gemini quality tiers exhausted. Switching to Backup Groq Brain...")
                try:
                    from discord_notifier import notify_alert
                    notify_alert("AI Brain Failover", "Gemini busy, switched to Groq backup.")
                except Exception:
                    pass

    # 2. Backup Brain: Groq
    if not data and groq_key:
        try:
            print("⚡ [Backup Brain] Crafting script with Groq LPU...")
            data = call_groq_api(user_prompt, groq_key)
            print("  ✓ Successfully crafted with Groq LPU!")
            try:
                from discord_notifier import notify_alert
                notify_alert("Groq Brain Active", f"Script generated using Groq: **{seed_title}**.")
            except Exception:
                pass
        except Exception as e:
            print(f"  Groq note: {e}. Switching to Offline Vault...")
            try:
                from discord_notifier import notify_alert
                notify_alert("Vault Fallback Active", f"Using backup story: **{seed_title}**.")
            except Exception:
                pass

    # 3. Guaranteed Offline Fallback (Vault)
    if not data or not data.get("lines"):
        print("🏛️ [Offline Vault] Loading guaranteed master story...")
        try:
            from discord_notifier import notify_alert
            notify_alert("Vault Story Loaded", f"Using backup story from vault: **{seed_title}**.")
        except Exception:
            pass
        data = {
            "title": seed_title,
            "voice": "am_michael",
            "speed": 1.05,
            "lead": 0.3,
            "outro": 1.0,
            "gap": 0.18,
            "music": "tension",
            "lines": [
                { "text": "Two days before their eighty thousand dollar wedding, a groom found his fiancee's secret phone." },
                { "text": "Inside, he found months of messages between her and his own best man." },
                { "text": "Instead of confronting her, he quietly saved every single screenshot." },
                { "text": "He smiled through the entire ceremony, let the lavish reception proceed, and waited for his toast." },
                { "text": "When the microphone was handed to him, he asked the staff to dim the lights." },
                { "text": "He turned on the giant projector, broadcasting every text and hotel photo to all two hundred guests." },
                { "text": "The room went dead silent as the bride broke down in tears." },
                { "text": "He handed the microphone to his ex-father-in-law, picked up the envelope of honeymoon cash," },
                { "text": "and booked a solo flight to the Bahamas.", "gap": 0.3 }
            ]
        }

    lines = data.get("lines", [])
    title = data.get("title", seed_title)
    save_history(title, seed_title, style=style)

    print(f"\nFinal Title: '{title}'")
    print(f"Cuts: {len(lines)} camera shots")
    print(f"Hook: \"{lines[0].get('text')}\"")
    print(f"Punchline: \"{lines[-1].get('text')}\"\n")
    return data

if __name__ == '__main__':
    topic_arg = sys.argv[1] if len(sys.argv) > 1 else None
    script = generate_script(topic_arg)
    out_file = Path("script.json")
    out_file.write_text(json.dumps(script, indent=2), encoding="utf-8")
    print(f"Saved script to {out_file.resolve()}")
