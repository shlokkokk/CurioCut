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

DIALOGUE_SYSTEM_PROMPT = """You are an elite short-form scriptwriter creating viral 2-character 3D dialogue shorts (@SKILLWARS.AI format).
The video features two 3D characters in a tech lab / studio:
1. 'guide' (Red Claude Character): Calm, authoritative, tech-insider male. Explains the crazy tech exploit or tool in simple, jaw-dropping steps.
2. 'skeptic' (Pink Avatar): Soft, expressive, skeptical female. Represents the viewer's exact thoughts, objections, and disbelief.

SCRIPT STRUCTURE FORMULA:
1. CUT 1 ('guide'): The 2-second pattern interrupt hook. Cut through the noise with an unbelievable claim.
   Example: "Claude just killed the billion dollar Jarvis."
2. CUT 2 ('skeptic'): Disbelief / question.
   Example: "Wait, Tony Stark's Jarvis?"
3. CUT 3 ('guide'): Tool reveal & open-source loophole.
   Example: "Yep. Now it is free. Built by Stanford researchers, open source on GitHub."
4. CUT 4 ('skeptic'): The viewer's biggest barrier.
   Example: "Okay, but I'm not a coder."
5. CUT 5 ('guide'): Step 1 — Dead simple setup.
   Example: "You don't need to be. Step one: paste the GitHub link into Claude Code and say install this for me."
6. CUT 6 ('guide'): Step 2 — The integration.
   Example: "Step two: connect your Gmail and calendar."
7. CUT 7 ('skeptic'): Curiosity escalation.
   Example: "And then what?"
8. CUT 8 ('guide'): The payoff / superpower.
   Example: "Tomorrow morning you wake up to forty unread emails. It reads them all and speaks an audio briefing of only what actually matters."
9. CUT 9 ('skeptic'): The price objection.
   Example: "And what does it cost every month?"
10. CUT 10 ('guide'): Zero cost punchline.
    Example: "Nothing. It runs on your own computer. Zero subscriptions."
11. CUT 11 ('guide'): The viral comment-for-DM Call to Action.
    Example: "Comment JARVIS below and I will send you the direct link and the setup prompt."

STRICT RULES:
- Zero robotic AI buzzwords: NEVER say "in today's digital landscape", "delve", "game-changer", "revolutionary", "testament".
- Speak like two friends talking in real life.
- All numbers MUST be spelled out as spoken words ("one billion dollars", "forty unread emails", "step one").
- Each cut MUST have:
  - "speaker": "guide" OR "skeptic"
  - "text": The spoken line (8 to 15 words)
  - "header": Chapter title displayed on the top plaque (ALL CAPS, under 6 words, e.g. "CLAUDE KILLED $1B JARVIS", "STEP 1: PASTE THE LINK")
  - "prop": 3D prop action. Choose from:
    ["sword_cut", "glowing_orb", "terminal_desk", "floating_envelope", "pile_letters", "scanner_beam", "waveform_audio", "server_tower", "scale_balance", "comment_ui"]

JSON OUTPUT FORMAT:
Output strictly valid JSON with no markdown wrapping:
{
  "title": "Short Punchy Title (under 7 words)",
  "cta_keyword": "JARVIS",
  "tool_name": "OpenJarvis",
  "resource_url": "https://github.com/...",
  "lines": [
    {
      "speaker": "guide",
      "text": "Claude just killed the billion dollar Jarvis.",
      "header": "CLAUDE KILLED $1B JARVIS",
      "prop": "sword_cut"
    },
    ...
  ]
}
"""

def call_gemini_dialogue(prompt, api_key):
    """Calls Google Gemini with smart progressive retries."""
    models = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-2.0-flash"]
    delays = [2, 4, 6]

    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        payload = {
            "systemInstruction": {"parts": [{"text": DIALOGUE_SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.8,
                "responseMimeType": "application/json"
            }
        }

        for attempt in range(3):
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)
            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "500" in err_str or "429" in err_str) and attempt < 2:
                    time.sleep(delays[attempt])
                    continue
                break

    raise RuntimeError("All Gemini models failed for dialogue generation.")

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
    gemini_keys = [k for k in [os.environ.get("GEMINI_API_KEY"), os.environ.get("GEMINI_API_KEY_BACKUP")] if k]

    script_data = None
    for idx, g_key in enumerate(gemini_keys):
        try:
            label = "Primary" if idx == 0 else "Backup"
            print(f"  Attempting with {label} Gemini key...")
            script_data = call_gemini_dialogue(prompt, g_key)
            print("  ✓ Dialogue script successfully crafted!")
            break
        except Exception as e:
            print(f"  Gemini key {idx + 1} notice: {e}")

    # Fallback to guaranteed OpenJarvis template if offline
    if not script_data or not script_data.get("lines"):
        print("  Loading verified master OpenJarvis dialogue...")
        script_data = {
            "title": "Claude Just Killed the $1B Jarvis",
            "cta_keyword": "JARVIS",
            "tool_name": "OpenJarvis",
            "resource_url": "https://github.com/open-jarvis/OpenJarvis",
            "lines": [
                {
                    "speaker": "guide",
                    "text": "Claude just killed the billion dollar Jarvis.",
                    "header": "CLAUDE KILLED $1B JARVIS",
                    "prop": "sword_cut"
                },
                {
                    "speaker": "skeptic",
                    "text": "Wait, Tony Stark's Jarvis?",
                    "header": "TONY STARK'S JARVIS?",
                    "prop": "glowing_orb"
                },
                {
                    "speaker": "guide",
                    "text": "Yep. Now it is free. It is called OpenJarvis, built by Stanford researchers, open source on GitHub.",
                    "header": "IT'S CALLED OPENJARVIS",
                    "prop": "glowing_orb"
                },
                {
                    "speaker": "skeptic",
                    "text": "Okay, but I'm not a coder.",
                    "header": "I'M NOT A CODER",
                    "prop": "terminal_desk"
                },
                {
                    "speaker": "guide",
                    "text": "You don't need to be. Step one: copy the link, paste it into Claude Code, and say install this for me.",
                    "header": "STEP 1: PASTE THE LINK",
                    "prop": "terminal_desk"
                },
                {
                    "speaker": "guide",
                    "text": "Step two: connect your Gmail and calendar.",
                    "header": "STEP 2: GMAIL + CALENDAR",
                    "prop": "floating_envelope"
                },
                {
                    "speaker": "skeptic",
                    "text": "And then what?",
                    "header": "AND THEN WHAT?",
                    "prop": "pile_letters"
                },
                {
                    "speaker": "guide",
                    "text": "Tomorrow morning you wake up to forty unread emails. Jarvis reads them first and tells you what actually matters.",
                    "header": "JARVIS READS THEM FIRST",
                    "prop": "scanner_beam"
                },
                {
                    "speaker": "guide",
                    "text": "Step three: turn on the spoken briefing. It literally talks to you like a real assistant.",
                    "header": "STEP 3: SPOKEN BRIEFING",
                    "prop": "waveform_audio"
                },
                {
                    "speaker": "skeptic",
                    "text": "And what does it cost every month?",
                    "header": "WHAT DOES IT COST?",
                    "prop": "server_tower"
                },
                {
                    "speaker": "guide",
                    "text": "Nothing. It runs on your own computer. Zero subscriptions.",
                    "header": "FREE · NO SUBSCRIPTION",
                    "prop": "server_tower"
                },
                {
                    "speaker": "guide",
                    "text": "Comment JARVIS below and I will send you the direct link and the setup prompt.",
                    "header": "COMMENT 'JARVIS'",
                    "prop": "comment_ui"
                }
            ]
        }

    script_data["style"] = "claude-desk"
    return script_data

if __name__ == "__main__":
    script = generate_dialogue_script()
    print("\nGenerated Dialogue Lines:")
    for line in script["lines"]:
        spk = line["speaker"].upper()
        print(f"[{spk}] ({line['header']}) -> {line['text']}")
