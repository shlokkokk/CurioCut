"""
Generative AI Story + Shot-by-Shot 3D Director Blueprint compiler for Town-Rule videos.
Zero hardcoded stories: invents a fresh 'In this town, [rule]...' 4-act micro-movie every run,
avoiding repeats in history.json, and compiles it into a complete 3D episode JSON.
"""

import os
import sys
import json
import random
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

HISTORY_FILE = Path(__file__).resolve().parent / "town_history.json"

TOWN_DIRECTOR_SYSTEM_PROMPT = """You are the showrunner and 3D director of a viral 9:16 Roblox-style animated storytelling channel.
Every episode is a ~90 to 130 second (260 to 340 spoken words) 4-act micro-movie that hooks viewers in 1.5 seconds.

CORE FORMULA (STRICT):
1. HOOK (Shot 1): Must open immediately with "In this town, [1 bizarre, high-stakes rule]..." or "In this world, [1 bizarre rule]...". Zero intro fluff.
2. ACT 1 (Rule + Examples): Show 2 to 3 quick visual examples of how normal people live under the rule.
3. ACT 2 (Protagonist + Emotional Stakes): Introduce our relatable protagonist (kid, poor dad, outcast, sibling) and their personal flaw/bond/goal.
4. ACT 3 (Escalation / Rule Breaking / Countdown): Something goes wrong, a countdown or monster threat closes in, or someone tries to cheat the rule.
5. ACT 4 (Gut-Punch Twist or Clever Loophole): A shocking emotional reveal or smart payoff that flips the meaning of Shot 1!

WRITING RULES:
- Simple, vivid, spoken conversational English. Short punchy sentences.
- Spell out numbers as words in spoken text ("twenty years", "ten coins", "three hundred steps"), OR keep short numbers natural.
- Zero AI cliches ("little did he know", "testament to", "in a shocking turn", "unbeknownst", "it wasn't long before").
- Every shot in "shots" is 2.0 to 3.8 seconds (roughly 7 to 15 spoken words) so the camera cuts constantly! Aim for 24 to 32 shots total.

VISUAL & 3D PROCEDURAL RULES (CRITICAL - NO HARDCODED ASSETS):
You must design the cast, optional procedural creature/monster, environments, and shot-by-shot staging using ONLY our procedural 3D primitives:

Environments ("set"):
- "suburban_street": rows of houses with doors, mail slots, windows, lawns, road, telephone poles
- "house_interior": cozy wood cabin/living room with table, bed, wall notes/receipts, door
- "hospital_room": white tiled room, hospital bed, IV stand, glowing HR 72 monitor
- "medieval_village": half-timbered cottages, cobblestone square, clock tower, stone fountain
- "empty_wasteland": long straight road into dramatic fog with dead grass (great for marches/tension)
- "graveyard": iron fence, tombstones, gnarled dead trees

Lighting ("lighting"): "day", "sunset", "night", "red_horror", "fog_orange"
Weather ("weather"): "none", "snow", "rain", "gold_particles", "smoke"

Camera ("cam"):
- "establishing_aerial": high wide shot looking down the street/village
- "push_in": medium shot smoothly pushing in toward cam_target
- "whip_zoom": fast punch-in on cam_target face
- "closeup_face": tight portrait on cam_target face
- "ots_left" / "ots_right": over-the-shoulder dialogue framing
- "low_angle_monster": dramatic upward angle making monster/character look huge
- "pov_window": looking through a window/door frame
- "crowd_march": high tracking angle over a line of people

Cast ("cast"): 2 to 5 named characters:
- id (lowercase slug, e.g. "leo", "dad", "mayor")
- height: "kid" | "adult" | "elder"
- skin_color: hex (e.g. "#F2C9A0", "#D9A077", "#8D5524", "#A472D9")
- shirt_color: hex
- shirt_pattern: "solid" | "stripes" | "suit" | "hoodie" | "apron" | "gown"
- pants_color: hex
- hair_style: "messy" | "parted" | "bob" | "pigtails" | "bald" | "tophat" | "cap"
- hair_color: hex
- beard: true/false

Optional Procedural Creatures ("creatures"): 0 to 2 custom procedural creatures if the story needs a monster, ghost, or pet!
- id (slug)
- archetype: "fur_giant" | "shadow_stalker" | "tiny_pet" | "winged_beast"
- scale: number (e.g. 2.8 for giant monster, 0.55 for tiny pet, 1.8 for beast)
- primary_color: hex
- secondary_color: hex
- mouth_type: "human_teeth" | "jagged_fangs" | "cute_buckteeth" | "none"
- eye_type: "none" | "glow_red" | "cute_big" | "hollow"
- features: array from ["fur_spikes", "horns", "ears", "tail", "aura_particles"]

Actor state per shot ("actors"):
- id: character or creature id
- pos: [x, y, z] (street center is x=0, houses at x=-6.5 and x=6.5, road runs along z from -40 to +40; interior room is x=-3.5..3.5, z=-3.5..3.5)
- rot_y: degrees (0 faces +Z toward camera, 180 faces -Z, 90 faces +X, -90 faces -X)
- anim: "idle" | "walk" | "run" | "wave" | "cry" | "fall" | "sit" | "hold_hands" | "handstand" | "point" | "peek" | "hunch"
- face: "neutral" | "happy" | "sad" | "crying" | "shocked" | "angry" | "smirk" | "monster_grin" | "closed" | "blush" | "dizzy" | "blind" | "talk_open" | "worried"
- prop: "none" | "coin" | "jar" | "wagon" | "backpack" | "lantern" | "letter" | "rope" | "broom" | "cake" | "cane"
- translucent: true/false
- stone_legs: true/false

Optional overlay per shot ("overlay"):
- null OR { "type": "nameplate"|"counter"|"clock"|"sign"|"warning"|"note", "text": "SHORT TEXT", "color": "#FFD43B" }

Optional SFX per shot ("sfx"): "none" | "clink" | "footsteps" | "door_creak" | "gasp" | "heartbeat" | "beep_monitor" | "radio_static" | "whoosh" | "pop" | "thunder"

Highlight words ("highlight_words"): 8 to 15 important single words from the narration to color-highlight in captions (e.g. {"word": "MIDNIGHT", "color": "#FF4444"}).

OUTPUT: Strictly valid JSON matching this schema:
{
  "title": "Short Viral Title",
  "rule_hook": "One-sentence summary of the town rule",
  "voice": "am_michael",
  "speed": 1.10,
  "music_mood": "mystery",
  "cast": [...],
  "creatures": [...],
  "highlight_words": [{"word": "EXAMPLE", "color": "#FFD43B"}],
  "shots": [
    {
      "text": "Spoken narration for this shot...",
      "set": "suburban_street",
      "lighting": "day",
      "weather": "none",
      "cam": "establishing_aerial",
      "cam_target": "leo",
      "actors": [...],
      "overlay": null,
      "sfx": "whoosh"
    }
  ]
}
"""


def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_history(title: str, rule_hook: str):
    hist = load_history()
    hist.append({"title": title, "rule_hook": rule_hook})
    HISTORY_FILE.write_text(json.dumps(hist[-80:], indent=2), encoding="utf-8")


def _call_gemini(prompt: str, api_key: str, model: str) -> dict:
    import time
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {"parts": [{"text": TOWN_DIRECTOR_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except urllib.error.HTTPError as he:
            if he.code == 429 and attempt < 2:
                wait_sec = 12 * (attempt + 1)
                print(f"[story_director] {model} hit burst rate limit (429), pausing {wait_sec}s for quota reset...")
                time.sleep(wait_sec)
                continue
            raise


def _call_groq(prompt: str, api_key: str) -> dict:
    from groq import Groq
    client = Groq(api_key=api_key)
    last = None
    json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY a valid JSON object strictly matching the schema. No thoughts, no explanations."
    for model in ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": TOWN_DIRECTOR_SYSTEM_PROMPT},
                    {"role": "user", "content": json_prompt},
                ],
                temperature=0.85,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content.strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[story_director] Groq {model} failed: {e}")
            last = e
    raise last


def generate_episode(theme_hint: str = "") -> dict:
    hist = load_history()
    avoid_rules = [h.get("rule_hook", h.get("title", "")) for h in hist[-25:]]
    avoid_str = "\n".join(f"- {r}" for r in avoid_rules) if avoid_rules else "None yet."

    genres = [
        "creepy rule-town with a terrifying monster loophole",
        "emotional family sacrifice with a hidden twist revealed at the end",
        "sci-fi life-counter / resource-limit town where an outcast saves everyone",
        "mystery / coma / ghost town where clues subtly point to the real truth",
        "karma / magic curse town where a clever kid outsmarts a greedy villain",
    ]
    chosen_genre = theme_hint.strip() or random.choice(genres)

    user_prompt = (
        f"Create a brand-new original 2-minute viral episode in the style of: {chosen_genre}.\n"
        f"DO NOT reuse or closely imitate any of these past premises:\n{avoid_str}\n\n"
        f"Make sure the cast, procedural creatures (if any), environments, and 24-30 shots tell a complete, "
        f"gripping 4-act story with an unforgettable ending twist."
    )

    key1 = os.environ.get("GEMINI_API_KEY", "").strip()
    key2 = os.environ.get("GEMINI_API_KEY_BACKUP", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()

    attempts = []
    # Tier 1: Peak Human Psychology & Deep Reasoning (Gemini Pro Models with backoff retry)
    if key1:
        attempts.append(("Gemini Pro Latest (Key 1)", lambda: _call_gemini(user_prompt, key1, "gemini-pro-latest")))
    if key2:
        attempts.append(("Gemini Pro Latest (Key 2)", lambda: _call_gemini(user_prompt, key2, "gemini-pro-latest")))
    if key1:
        attempts.append(("Gemini 2.5 Pro (Key 1)", lambda: _call_gemini(user_prompt, key1, "gemini-2.5-pro")))
    if key2:
        attempts.append(("Gemini 2.5 Pro (Key 2)", lambda: _call_gemini(user_prompt, key2, "gemini-2.5-pro")))

    # Tier 2: High Intelligence Fallbacks (Real Google Endpoints)
    if key1:
        attempts.append(("Gemini Flash Latest (Key 1)", lambda: _call_gemini(user_prompt, key1, "gemini-flash-latest")))
    if key2:
        attempts.append(("Gemini Flash Lite Latest (Key 2)", lambda: _call_gemini(user_prompt, key2, "gemini-flash-lite-latest")))

    # Tier 3: Groq High-Speed LPU Fallback
    if groq_key:
        attempts.append(("Groq LPU Engine", lambda: _call_groq(user_prompt, groq_key)))

    last_err = None
    for label, fn in attempts:
        try:
            print(f"[story_director] Generating episode via {label}...")
            ep = fn()
            if isinstance(ep, dict) and ep.get("shots") and len(ep["shots"]) >= 8:
                save_history(ep.get("title", "Untitled"), ep.get("rule_hook", ""))
                print(f"[story_director] Generated '{ep.get('title')}' ({len(ep['shots'])} shots)")
                return ep
        except Exception as e:
            last_err = e
            print(f"[story_director] {label} failed: {e}")

    raise RuntimeError(f"All AI story providers failed. Last error: {last_err}")


if __name__ == "__main__":
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "work" / "episode.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ep = generate_episode()
    out_path.write_text(json.dumps(ep, indent=2), encoding="utf-8")
    print(f"Saved episode blueprint to {out_path}")
