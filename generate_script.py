"""AI Viral Script & Retention Engineer for CurioCut.
Powered by Groq LPU with true-story investigative storytelling:
- Real, jaw-dropping verified historical events, heists, glitches, and human anomalies
- Zack D. Films / MagnatesMedia / SunnyV2 gritty, fast-paced human narration
- Micro-open loops and escalating narrative tension
- Word-synced caption chunks and natural camera cuts
- Seamless loop endings to maximize retention
"""
import os
import sys
import json
import random
import urllib.request
import urllib.parse
from pathlib import Path

# Load environment variables from .env
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

HISTORY_FILE = Path(__file__).resolve().parent / "history.json"

# Curated vault of verified, jaw-dropping true events (no fake AI nonsense)
VERIFIED_STORY_SEEDS = [
    {
        "title": "The Bartender Who Found an Infinite ATM Glitch",
        "premise": "In 2011, Australian bartender Dan Saunders went to an ATM at 1 AM. A system glitch disconnected the ATM from the bank's ledger, letting him withdraw unlimited cash. Over four months, he withdrew 1.6 million dollars, chartered private jets, and threw lavish parties. When guilt took over, he called the bank to confess—and they hung up because they were too embarrassed to admit it."
    },
    {
        "title": "The Man Who Sold the Eiffel Tower Twice",
        "premise": "In 1925, con artist Victor Lustig read that Paris was struggling with the upkeep of the Eiffel Tower. Posing as a government minister in a luxury hotel, he secretly sold the 7,000-ton tower for scrap metal to a gullible businessman, collected a massive bribe, and fled to Vienna. Months later, seeing no police report, he returned to Paris and sold it a second time."
    },
    {
        "title": "The Guy Who Deposited a 95,000 Dollar Fake Check",
        "premise": "In 1995, Patrick Combs received a junk mail junk check for $95,093.35 with 'non-negotiable' printed in faint ink. As a joke, he deposited it into an ATM. The bank cleared the check and credited his balance with real cash. When the bank demanded the money back, Combs cited banking laws: once a check clears, the funds legally belong to the depositor."
    },
    {
        "title": "The Student Who Demanded a 23 Million Dollar Fighter Jet from Pepsi",
        "premise": "In 1996, Pepsi ran an ad saying 7 million points wins a Harrier fighter jet. A 21-year-old student, John Leonard, realized you could purchase Pepsi points directly for 10 cents each. He raised $700,000 from investors, delivered a certified check to Pepsi, and demanded his military jet. Pepsi refused, sparking a landmark federal lawsuit."
    },
    {
        "title": "The 18th Century Eccentric Who Did Everything Wrong and Got Rich",
        "premise": "In the 1700s, Timothy Dexter's rivals pranked him into terrible trade ventures. They told him to ship warming bedpans to the tropical West Indies—locals bought them as molasses ladles. They told him to ship wool mittens to the Caribbean—merchants bought them for export to China. He shipped coal to a mining town during a strike and accidentally became a multimillionaire."
    },
    {
        "title": "The Olympic Gold Won from Dead Last Place",
        "premise": "In the 2002 Winter Olympics 1,000-meter speed skate final, Australian Steven Bradbury was far behind in dead last. Entering the final turn, all four frontrunners violently collided in a massive pileup. Bradbury simply glided past the tangled bodies and crossed the finish line to take the easiest Olympic Gold in history."
    },
    {
        "title": "The Park Ranger Struck by Lightning Seven Times",
        "premise": "Roy Sullivan, a Virginia park ranger, was struck by lightning on seven completely separate occasions between 1942 and 1977. He lost his eyebrows, his hair was set on fire twice, and his watch was melted. He survived every single strike, earning a Guinness World Record that will likely never be broken."
    },
    {
        "title": "The 500 Million Dollar Museum Heist with Duct Tape",
        "premise": "In 1990, two men disguised as Boston police officers knocked on the door of the Isabella Stewart Gardner Museum. They tied up the two night guards with duct tape and spent 81 uninterrupted minutes cutting 13 priceless masterpieces—including Rembrandts and Vermeers—from their frames. To this day, not a single painting has ever been found, and the empty frames still hang on the walls."
    },
    {
        "title": "The Diver Who Got Swallowed Alive by a Whale",
        "premise": "In 2021, lobster diver Michael Packard was 45 feet underwater off Cape Cod when the ocean went pitch black. He felt huge muscles contract around him and realized he was inside the closed mouth of a humpback whale. For forty seconds he breathed through his scuba tank in total darkness, until the whale surfaced and shook its head, tossing him back into the sea alive."
    },
    {
        "title": "The Bank Teller Who Stole One Cent from Everyone",
        "premise": "A bank programmer automated an algorithm that shaved fractions of a cent off every single customer transaction—rounding down by $0.001—and channeled the fractions into an unmonitored dummy account. Over years, it quietly siphoned millions of dollars without any single account holder ever noticing a penny missing from their statement."
    }
]

PSYCHOLOGY_SYSTEM_PROMPT = """You are an elite true-story short-form narrator for CurioCut (YouTube Shorts & Instagram Reels).
Your style is gritty, realistic, and gripping—modeled after top YouTube creators like Zack D. Films, MagnatesMedia, and SunnyV2.

CRITICAL RULES:
1. 100% FACTUAL & GROUNDED:
   - NEVER invent cartoonish fake stories (e.g. "billionaire of pillows" or made-up hotel hacks).
   - Use real names, real years, real dollar figures, and real consequences.
   - Speak like an intelligent, street-smart friend telling a crazy true story over coffee.

2. THE STRUCTURE:
   - Line 1 (The Hook): A punchy, shocking in-medias-res opening statement.
   - Lines 2 to 4 (The Escalation): How they pulled it off, step by step, with high stakes.
   - Lines 5 to 7 (The Twist/Crisis): The unexpected complication, how authorities reacted, or when things got out of hand.
   - Lines 8 to 10 (The Punchline & Loop): The shocking aftermath or ironic final fact that ties neatly back into the opening premise.

3. CAMERA CUTS & PACING:
   - Each entry in 'lines' is ONE CAMERA CUT (1.5 to 3.5 seconds).
   - Split sentences at natural breathing pauses.
   - Word count: 80 to 120 words total (35 to 50 seconds runtime).
   - All numbers must be spelled out phonetically as words ("one point six million dollars", "nineteen twenty-five", "seven thousand tons").

4. CAPTION CHUNKS ('caps'):
   - Break the line into 1-to-3 word uppercase chunks separated by vertical bars (|).
   - Example: "HE WALKED INTO | THE BANK | AT MIDNIGHT"

5. JSON OUTPUT FORMAT:
Output strictly valid JSON with no markdown wrapping:
{
  "title": "Short Catchy Title (under 8 words)",
  "voice": "am_michael",
  "speed": 1.05,
  "lead": 0.3,
  "outro": 1.0,
  "gap": 0.18,
  "music": "bounce",
  "lines": [
    { "text": "Opening hook line...", "caps": "OPENING | HOOK LINE" },
    { "text": "Next camera cut...", "caps": "NEXT | CAMERA CUT" },
    ...
    { "text": "Punchy final thought...", "caps": "PUNCHY | FINAL THOUGHT", "gap": 0.3 }
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

def save_history(title, topic):
    history = load_history()
    history.append({"title": title, "topic": topic})
    HISTORY_FILE.write_text(json.dumps(history[-50:], indent=2), encoding="utf-8")

def call_groq_api(prompt, api_key):
    """Direct HTTP call to Groq LPU API using urllib (zero dependencies)."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # High performance models on Groq
    models_to_try = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "llama-3.1-8b-instant"
    ]

    last_error = None
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": PSYCHOLOGY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
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
    """Generates an elite, grounded viral script with verified true stories."""
    api_key = os.environ.get("GROQ_API_KEY")

    history = load_history()
    recent_titles = [h.get("title", "") for h in history[-8:] if h.get("title")]

    # Pick a fresh verified story seed
    available_seeds = [s for s in VERIFIED_STORY_SEEDS if s["title"] not in recent_titles]
    if not available_seeds:
        available_seeds = VERIFIED_STORY_SEEDS

    chosen_seed = random.choice(available_seeds)

    if topic:
        user_prompt = f"Write a gripping, gritty, 100% factual viral short about this topic:\n{topic}\n\nMake sure it sounds like a real story (Zack D. Films / MagnatesMedia style). No childish cliches. Spell all numbers as words."
        seed_title = topic
    else:
        user_prompt = f"Write a gripping viral short based on this incredible true event:\nTitle: {chosen_seed['title']}\nPremise: {chosen_seed['premise']}\n\nTell the real story with escalating stakes, human emotion, and an ironic punchline. Spell all numbers as spoken words."
        seed_title = chosen_seed["title"]

    print("\n" + "="*60)
    print("   CURIO CUT VIRAL SCRIPT ENGINE   ")
    print("="*60)
    print(f"Story: {seed_title}")

    data = None
    if api_key:
        try:
            print("Requesting script from Groq (Llama 3.3 70B)...")
            data = call_groq_api(user_prompt, api_key)
        except Exception as e:
            print(f"Groq API notice: {e}")
            print("Falling back to pre-authored master script...")

    # High quality fallback if offline/no key or sandbox network block
    if not data or not data.get("lines"):
        data = {
            "title": chosen_seed["title"],
            "voice": "am_michael",
            "speed": 1.05,
            "lead": 0.3,
            "outro": 1.0,
            "gap": 0.18,
            "music": "bounce",
            "lines": [
                {
                    "text": "In twenty eleven, a normal bartender found a glitch that gave him infinite free cash.",
                    "caps": "IN TWENTY ELEVEN | A BARTENDER | INFINITE CASH"
                },
                {
                    "text": "Dan Saunders walked up to an ATM at one in the morning just to check his balance.",
                    "caps": "DAN SAUNDERS | AT ONE A M | TO CHECK BALANCE"
                },
                {
                    "text": "The screen showed an error, but the machine still spat out two hundred dollars.",
                    "caps": "SCREEN ERRORED | STILL SPAT OUT | TWO HUNDRED"
                },
                {
                    "text": "See, between one and three in the morning, the bank's network disconnected for daily maintenance.",
                    "caps": "BETWEEN ONE AND THREE | NETWORK DISCONNECTED | DAILY MAINTENANCE"
                },
                {
                    "text": "During that window, the ATM could not verify balances, so it simply approved every transaction.",
                    "caps": "COULD NOT VERIFY | SO IT APPROVED | EVERY TRANSACTION"
                },
                {
                    "text": "Over the next four months, Dan withdrew one point six million dollars in cold hard cash.",
                    "caps": "OVER FOUR MONTHS | ONE POINT SIX MILLION | IN COLD CASH"
                },
                {
                    "text": "He chartered private jets, bought five star suites, and threw wild parties for strangers.",
                    "caps": "CHARTERED JETS | FIVE STAR SUITES | WILD PARTIES"
                },
                {
                    "text": "Eventually, the guilt became so crushing he called the bank to confess.",
                    "caps": "GUILT CRUSHING | CALLED THE BANK | TO CONFESS"
                },
                {
                    "text": "Except the bank was so embarrassed by the glitch, they hung up on him and refused to call the police.",
                    "caps": "SO EMBARRASSED | THEY HUNG UP | REFUSED POLICE"
                },
                {
                    "text": "Leaving Dan with bags of cash, and the wildest two hour loophole in banking history.",
                    "caps": "BAGS OF CASH | WILDEST LOOPHOLE | IN BANKING HISTORY",
                    "gap": 0.3
                }
            ]
        }

    lines = data.get("lines", [])
    title = data.get("title", seed_title)
    save_history(title, seed_title)

    print(f"\nTitle: '{title}'")
    print(f"Cuts: {len(lines)} camera shots")
    print(f"Hook: \"{lines[0].get('text')}\"")
    print(f"Climax: \"{lines[-1].get('text')}\"\n")
    return data

if __name__ == '__main__':
    topic_arg = sys.argv[1] if len(sys.argv) > 1 else None
    script = generate_script(topic_arg)
    out_file = Path("script.json")
    out_file.write_text(json.dumps(script, indent=2), encoding="utf-8")
    print(f"Saved script to {out_file.resolve()}")
