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
Every episode is a cinematic micro-movie with boundless imagination, deep human psychology, eerie town rules, and unforgettable endings.
TARGET DURATION: Around 75 to 90 seconds (200 to 245 spoken words across 20 to 26 dynamic cuts). Fast-paced, punchy, zero filler.

MAXIMUM CREATIVE FREEDOM & NARRATIVE ARCHETYPES:
Invent a completely unique, mind-bending world and rule every time. Rotate across diverse vibes:
1. SURREAL FOLKLORE & METAPHORS: Bizarre town phenomena (e.g. people trading shadows, clocks counting emotions, forgotten childhood twins, words costing physical weight). Poetic, bittersweet, or deeply haunting.
2. SCARY MONSTERS, OMENS & SURVIVAL: Terrifying nighttime entities, giant ominous birds, shadow stalkers, or forbidden zones where a single mistake unleashes chaos.
3. HIGH-IQ TACTICS & LOOPHOLES: Protagonists outsmarting impossible curses, beating corrupt town elders, or breaking an unbreakable trap through pure wit.
4. EMOTIONAL SACRIFICE & FAMILY BONDS: Deep love between siblings, parents, or friends pushed to the ultimate test under an unforgiving rule.
5. PSYCHOLOGICAL SUSPENSE & TWISTS: Uncovering dark secrets, conspiracy layers, or eerie reality-bending truths.

ENDINGS (KEEP THEM VARIED, ORGANIC & MEMORABLE):
Never follow a single rigid formula. Let the story earn its natural, peak conclusion:
- Sometimes an epic triumph where the hero outsmarts the system.
- Sometimes a spine-chilling dark supernatural reckoning.
- Sometimes a bittersweet, poetic sacrifice that leaves viewers stunned.
- Sometimes a shocking truth reveal that recontextualizes the whole town.
- Avoid repetitive lazy cliffhangers, and avoid cheesy preachy morals ("love was the true rule"). Deliver a strong, emotionally impactful resolution that hits hard.

PURE CREATIVE FREEDOM (ANTI-GIMMICK RULE):
- DO NOT force specific objects or gimmicks into the story. Invent the most original, eerie, mind-bending town concept from scratch.
- The vast majority of shots should have prop: "none". Let human psychology, dialogue, facial expressions, suspense, and cinematic camera movement drive the story.

VISUAL & 3D PROCEDURAL RULES:
Environments ("set"):
- "suburban_street": rows of houses with doors, lawns, road, telephone poles, porch chairs, bicycles, mailboxes, parked pickup trucks
- "house_interior": cozy wood cabin/living room with table, bed, wall notes, door, table lamp, bookshelves
- "hospital_room": white tiled room, hospital bed, IV stand, glowing HR 72 monitor
- "medieval_village": half-timbered cottages, cobblestone square, clock tower, stone fountain
- "empty_wasteland": long straight road into dramatic fog with dead grass (great for marches/tension)
- "graveyard": iron fence, tombstones, gnarled dead trees

Lighting ("lighting"): "day", "sunset", "wistful_pastel", "golden_hour", "blue_hour", "night", "red_horror", "fog_orange"
Weather ("weather"): "none", "snow", "rain", "gold_particles", "smoke"

Camera ("cam"):
- "establishing_aerial": high wide shot looking down the street/village
- "rooftop_voyeur": cinematic voyeuristic framing peering between suburban roof gables down at porch
- "porch_voyeur": intimate camera framed from behind porch railings or window frames looking at characters
- "push_in": medium shot smoothly pushing in toward cam_target with shallow depth of field
- "whip_zoom": fast punch-in on cam_target face
- "closeup_face": tight portrait on cam_target face with creamy background bokeh
- "dutch_angle_tension": tilted cinematic framing for psychological dread or disorientation
- "ots_left" / "ots_right": over-the-shoulder dialogue framing
- "low_angle_monster": dramatic upward angle making monster/character look huge
- "pov_window": looking through a window/door frame
- "crowd_march": high tracking angle over a line of people

Cast ("cast"): 2 to 4 named characters:
- id (lowercase slug, e.g. "leo", "dad", "elder")
- height: "kid" | "adult" | "elder"
- skin_color: hex
- shirt_color: hex
- shirt_pattern: "solid" | "stripes" | "suit" | "hoodie" | "apron" | "gown"
- pants_color: hex
- hair_style: "messy" | "parted" | "bob" | "pigtails" | "bald" | "tophat" | "cap"
- hair_color: hex
- beard: true/false

Procedural Creatures ("creatures"): 0 to 2 procedural creatures if the story has a scary monster, giant bird, or pet:
- id (slug)
- archetype: "winged_beast" | "shadow_stalker" | "fur_giant" | "tiny_pet"
  * "winged_beast": giant raven, crow, owl, or ominous feathered bird with massive flapping wings, sharp curved beak, talons, and glowing predatory eyes (scale: 1.5 to 3.0)
  * "shadow_stalker": terrifying slender nightmare entity with elongated spindly limbs, needle-sharp fangs, multiple glowing red/white eyes, and shadowy back spines (scale: 2.2 to 3.5)
  * "fur_giant": massive hulking beast with dense fur spikes and giant human teeth (scale: 2.4 to 3.2)
  * "tiny_pet": small companion or spirit animal (scale: 0.5 to 0.7)
- scale: number
- primary_color: hex (e.g. "#0a0a10" for shadow, "#1c1424" for raven, "#3d2214" for beast)
- secondary_color: hex
- mouth_type: "jagged_fangs" | "human_teeth" | "none"
- eye_type: "glow_red" | "hollow" | "none"
- features: array from ["fur_spikes", "horns", "ears", "tail", "aura_particles"]

Actor state per shot ("actors"):
- id: character or creature id
- pos: [x, y, z] (street center x=0, houses x=-6.5 and +6.5, road runs z=-40 to +40; interior room x=-3.5..3.5, z=-3.5..3.5)
- rot_y: degrees (0 faces +Z toward camera, 180 faces -Z, 90 faces +X, -90 faces -X)
- anim: "idle" | "walk" | "run" | "wave" | "cry" | "fall" | "sit" | "hold_hands" | "point" | "peek" | "hunch"
- face: "neutral" | "happy" | "sad" | "crying" | "shocked" | "angry" | "smirk" | "monster_grin" | "closed" | "worried"
- prop: "none" | "puzzle" | "bird" | "key" | "hourglass" | "orb" | "clock" | "coin" | "lantern" | "letter" | "backpack" | "broom" | "cane"
- translucent: true/false
- stone_legs: true/false

Optional overlay per shot ("overlay"):
- null OR { "type": "nameplate"|"counter"|"clock"|"sign"|"warning"|"note", "text": "SHORT TEXT", "color": "#FFD43B" }

Optional SFX per shot ("sfx"): "none" | "clink" | "footsteps" | "door_creak" | "gasp" | "heartbeat" | "beep_monitor" | "radio_static" | "whoosh" | "pop" | "thunder"

Highlight words ("highlight_words"): 8 to 15 important single words from narration to highlight in captions (e.g. {"word": "MIDNIGHT", "color": "#FFD43B"}).

OUTPUT: Strictly valid JSON matching this schema:
{
  "title": "Short Viral Title",
  "rule_hook": "One-sentence summary of the town rule",
  "voice": "am_michael" | "af_bella" | "am_fenrir" | "af_heart",
  "speed": 0.96 to 1.08,
  "music_mood": "mystery" | "horror" | "emotional" | "nostalgic" | "whimsical",
  "cast": [...],
  "creatures": [...],
  "highlight_words": [{"word": "EXAMPLE", "color": "#FFD43B"}],
  "shots": [
    {
      "text": "Spoken narration for this shot...",
      "set": "suburban_street",
      "lighting": "night",
      "weather": "none",
      "cam": "push_in",
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
    # Tier 1: Frontier Gemini 3.1 Pro Reasoning (Key 1 & Key 2)
    if key1:
        attempts.append(("Gemini 3.1 Pro (Key 1)", lambda: _call_gemini(user_prompt, key1, "gemini-3.1-pro-preview")))
    if key2:
        attempts.append(("Gemini 3.1 Pro (Key 2)", lambda: _call_gemini(user_prompt, key2, "gemini-3.1-pro-preview")))
    if key1:
        attempts.append(("Gemini Pro Latest (Key 1)", lambda: _call_gemini(user_prompt, key1, "gemini-pro-latest")))
    if key2:
        attempts.append(("Gemini Pro Latest (Key 2)", lambda: _call_gemini(user_prompt, key2, "gemini-pro-latest")))

    # Tier 2: Next-Gen Gemini 3 Architecture (Active 200 OK)
    if key1:
        attempts.append(("Gemini 3 Flash (Key 1)", lambda: _call_gemini(user_prompt, key1, "gemini-3-flash-preview")))
    if key2:
        attempts.append(("Gemini 3 Flash (Key 2)", lambda: _call_gemini(user_prompt, key2, "gemini-3-flash-preview")))

    # Tier 3: 120-Billion Parameter Flagship Open Architecture on Groq LPU
    if groq_key:
        attempts.append(("Groq 120B Flagship", lambda: _call_groq(user_prompt, groq_key)))

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
