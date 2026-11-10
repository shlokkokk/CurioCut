"""Dual-Character Viral Tech Dialogue Generator for CurioCut.
Generates high-retention 2-character dialogue (Tech Guide / Red Claude + Skeptical Viewer / Pink Avatar).
Inspired by the @SKILLWARS.AI format with physical 3D scene props and header chapter plaques.

Powered by Dual Google Gemini 3.8 Flash keys + Groq 70B fallback.
"""
import os
import sys
import json
import time
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DIALOGUE_SYSTEM_PROMPT = """You are an elite short-form scriptwriter creating natural, viral 2-character dialogue for YouTube Shorts and Instagram Reels.
Two friends are talking in a tech studio:
1. 'guide' (Male Tech Creator): Deep, masculine, confident insider. Speaks like he is showing a close friend a crazy secret on his laptop. Natural spoken cadence, direct, punchy, zero robotic script-reading vibes.
2. 'skeptic' (Female Friend): Sharp, expressive, skeptical. Represents the viewer's exact thoughts. She calls out doubts, reacts with surprise, and asks genuine questions with rising inflection.

CRITICAL CONVERSATIONAL & VOICE RULES:
- NEVER sound like an AI reading a script or software manual.
- BANNED: Do NOT use "Step 1", "Step 2", "Step 3" phrasing! Talk like real people: "All you have to do is...", "Then the craziest part is...", "Check this out..."
- BANNED AI BUZZWORDS: "game-changer", "revolutionary", "delve", "testament", "tapestry", "landscape".
- SKEPTIC QUESTIONS MUST SOUND LIKE QUESTIONS: Every line where the skeptic doubts or asks MUST end with a question mark ('?') and use natural conversational phrases ('Wait, how is that even possible?', 'Hold on, is that actually free?', 'Okay, what is the catch?').
- GUIDE DELIVERY: Grounded, punchy, confident answers ('Look. It runs completely on your own machine.', 'Zero subscriptions. Forever.').
- Numbers must be spelled out phonetically as words ('two hundred dollars', 'three clicks').
- Length: 9 to 11 cuts total.
- Final cut MUST be the Guide calling to action with the CTA keyword ('Comment [KEYWORD] below and I will DM you the direct repo link.').

JSON OUTPUT FORMAT:
Output strictly valid JSON with no markdown wrapping:
{
  "title": "Short Punchy Title (under 7 words)",
  "cta_keyword": "KEYWORD",
  "tool_name": "ToolName",
  "resource_url": "https://github.com/...",
  "lines": [
    {
      "speaker": "guide",
      "text": "Spoken line (8 to 14 words)",
      "header": "SHORT HEADER (ALL CAPS)",
      "prop": "sword_cut"
    }
  ]
}
Props available: ["sword_cut", "glowing_orb", "terminal_desk", "falling_letters", "scanner_beam", "waveform_audio", "server_tower", "comment_ui"]
"""

def call_gemini_dialogue_single(prompt, api_key, model):
    """Direct HTTP call to a specific Gemini model for tech dialogue."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {"parts": [{"text": DIALOGUE_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
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
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)

def build_dialogue_quality_ladder(key1, key2):
    """Quality-First Ladder for 2-character tech dialogue.
    Prioritizes human conversational banter, witty timing, and Pro reasoning across BOTH keys
    before ever dropping down to high-velocity flash or lite tiers.
    """
    ladder = []
    # Tier 1: Absolute Peak Conversational Banter & Pro Reasoning
    if key1:
        ladder.append((key1, "gemini-pro-latest", "Key 1 [Peak Pro Reasoning]"))
    if key2:
        ladder.append((key2, "gemini-3.1-pro-preview", "Key 2 [Peak Pro Alternate]"))

    # Tier 2: Peak Creative Dialogue Dynamic Flow (3.5 & 3.8 Flash)
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

def call_groq_dialogue(prompt, api_key):
    """Fallback to Groq high-speed OSS models."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    models = ["openai/gpt-oss-120b", "llama-3.1-70b-versatile"]
    for m in models:
        payload = {
            "model": m,
            "messages": [
                {"role": "system", "content": DIALOGUE_SYSTEM_PROMPT + "\nRespond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "response_format": {"type": "json_object"}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return json.loads(data["choices"][0]["message"]["content"])
        except Exception:
            continue
    raise RuntimeError("All Groq models failed for dialogue generation.")

def generate_dialogue_script(story_info=None):
    """Generates the full 2-character dialogue script from harvested tech intel."""
    if not story_info:
        from tech_harvester import get_next_tech_story
        story_info = get_next_tech_story()

    title = story_info.get("title", "")
    tool = story_info.get("tool_name", "")
    premise = story_info.get("premise", "")
    cta = story_info.get("cta_keyword", "TOOL")
    url = story_info.get("resource_url", "")

    prompt = (
        f"Write a viral 2-character dialogue short about this breakthrough tool:\n"
        f"Title: {title}\n"
        f"Tool Name: {tool}\n"
        f"CTA Keyword: {cta}\n"
        f"Resource URL: {url}\n"
        f"Premise Details: {premise}\n\n"
        f"Remember: Guide is the calm Red Claude character, Skeptic is the soft pink character. "
        f"Make it fast, witty, and high stakes. End with comment '{cta}' to get the link."
    )

    print(f"\n[Tech Dialogue Engine] Generating 2-character script for '{title}'...")
    key1 = os.environ.get("GEMINI_API_KEY")
    key2 = os.environ.get("GEMINI_API_KEY_BACKUP")
    quality_ladder = build_dialogue_quality_ladder(key1, key2)

    script_data = None
    for idx, (g_key, model_name, tier_label) in enumerate(quality_ladder):
        try:
            print(f"  Attempting with {tier_label} ({model_name})...")
            script_data = call_gemini_dialogue_single(prompt, g_key, model_name)
            print(f"  ✓ Dialogue script successfully crafted via {tier_label} ({model_name})!")
            break
        except Exception as e:
            err_str = str(e)
            print(f"  {tier_label} notice: {err_str}")
            if "429" in err_str:
                time.sleep(1.5)

    if not script_data or not script_data.get("lines"):
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            try:
                print("  Failing over to Groq 120B...")
                script_data = call_groq_dialogue(prompt, groq_key)
                print("  ✓ Dialogue script generated via Groq!")
            except Exception as e:
                print(f"  Groq notice: {e}")

    # Fallback to verified conversational master dialogue if offline
    if not script_data or not script_data.get("lines"):
        print("  Loading verified high-retention conversational tech dialogue...")
        script_data = {
            "title": "Run Full AI On Your Laptop",
            "cta_keyword": "LOCAL",
            "tool_name": "Ollama DeepSeek",
            "resource_url": "https://github.com/ollama/ollama",
            "lines": [
                {
                    "speaker": "guide",
                    "text": "Stop paying twenty dollars a month for artificial intelligence.",
                    "header": "STOP PAYING FOR AI",
                    "prop": "sword_cut"
                },
                {
                    "speaker": "skeptic",
                    "text": "Wait— what do you mean? How else am I supposed to use it?",
                    "header": "HOW ELSE CAN I USE IT?",
                    "prop": "glowing_orb"
                },
                {
                    "speaker": "guide",
                    "text": "You can download the entire model directly to your laptop for free.",
                    "header": "DOWNLOAD IT FOR FREE",
                    "prop": "glowing_orb"
                },
                {
                    "speaker": "skeptic",
                    "text": "Hold on— don't you need a ten thousand dollar supercomputer for that?",
                    "header": "DO I NEED A SUPERCOMPUTER?",
                    "prop": "terminal_desk"
                },
                {
                    "speaker": "guide",
                    "text": "Not anymore. A brand new breakthrough lets you run full reasoning models on a basic Mac.",
                    "header": "RUNS ON A BASIC LAPTOP",
                    "prop": "terminal_desk"
                },
                {
                    "speaker": "skeptic",
                    "text": "Okay, but is it actually as smart as ChatGPT?",
                    "header": "IS IT AS SMART?",
                    "prop": "scanner_beam"
                },
                {
                    "speaker": "guide",
                    "text": "It literally beat ChatGPT in math and coding benchmarks last week.",
                    "header": "BEAT CHATGPT IN CODING",
                    "prop": "scanner_beam"
                },
                {
                    "speaker": "skeptic",
                    "text": "And it works when my WiFi is completely disconnected?",
                    "header": "WORKS OFFLINE?",
                    "prop": "server_tower"
                },
                {
                    "speaker": "guide",
                    "text": "Completely offline. One hundred percent private. Zero monthly fees.",
                    "header": "100% PRIVATE · $0.00",
                    "prop": "server_tower"
                },
                {
                    "speaker": "guide",
                    "text": "Comment LOCAL below and I will send you the one-click install link right now.",
                    "header": "COMMENT 'LOCAL' BELOW",
                    "prop": "comment_ui"
                }
            ]
        }

    script_data["style"] = "claude-desk"
    script_data["category"] = story_info.get("category", "breaking_tech")
    script_data["tool_name"] = story_info.get("tool_name", "")
    script_data["resource_url"] = story_info.get("resource_url", "")
    return script_data

if __name__ == "__main__":
    script = generate_dialogue_script()
    print("\nGenerated Dialogue Lines:")
    for line in script["lines"]:
        spk = line["speaker"].upper()
        print(f"[{spk}] ({line['header']}) -> {line['text']}")

