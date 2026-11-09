"""Autonomous Story Harvester for CurioCut.
Fetches trending, real-world stories across top Reddit communities and feeds them to Groq:

NICHES:
1. 'spicy_drama': High-engagement relationship drama, secret betrayal, wedding revenge (r/BestofRedditorUpdates, r/TrueOffMyChest)
2. 'real_heists': Mind-blowing true heists, glitches, loopholes, and con artists (r/todayilearned, r/history)
3. 'brainrot_absurd': Wild billionaire antics, gamer controversies, ridiculous lawsuits (r/wallstreetbets, r/facepalm)
4. 'body_curiosity': Zack D. Films style body and science explainers
"""
import os
import sys
import json
import random
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

SUBREDDIT_NICHES = {
    "spicy_drama": [
        "BestofRedditorUpdates",
        "TrueOffMyChest",
        "relationship_advice"
    ],
    "real_heists": [
        "todayilearned",
        "history"
    ],
    "brainrot_absurd": [
        "wallstreetbets",
        "facepalm",
        "mildlyinfuriating"
    ]
}

# Evergreen Curated Vault for guaranteed 10/10 backups
EVERGREEN_VAULT = [
    # Spicy Relationship & Revenge
    {
        "niche": "spicy_drama",
        "style": "night-file",
        "title": "The Wedding Projector Cheating Revenge",
        "premise": "A groom discovers his fiancée is secretly having an affair with his best man two days before their luxury wedding. Instead of canceling, he lets the entire $80,000 ceremony proceed. During his toast, he dims the lights and plays the hotel security footage on the giant reception projector screen in front of all 200 guests, hands the mic to his ex-father-in-law, and walks out with all the honeymoon cash."
    },
    {
        "niche": "spicy_drama",
        "style": "night-file",
        "title": "The Billionaire Who Put Everything in His Mother's Name",
        "premise": "During a bitter high-profile divorce, a wealthy star discovers his wife is demanding 50 percent of his entire $70 million fortune. In court, the judge investigates his bank accounts only to discover he owns zero houses, zero cars, and zero bank accounts in his name—every single luxury estate, yacht, and paycheck was legally registered to his mother since day one. His ex-wife walked away with nothing."
    },
    {
        "niche": "spicy_drama",
        "style": "inside-out",
        "title": "The Hidden Nanny Cam Confession",
        "premise": "A wife suspected her husband of lying about his late-night business trips. She placed a tiny voice recorder inside the master bedroom headboard. When she listened to the audio, she didn't just hear infidelity—she heard her husband and her own sister plotting how to drain her trust fund. She quietly transferred the funds, filed an emergency restraining order, and left the audio playing on repeat in the empty house."
    },
    # Real Heists & Glitches
    {
        "niche": "real_heists",
        "style": "tall-tale",
        "title": "The Bartender Who Found an Infinite ATM Glitch",
        "premise": "In 2011, Australian bartender Dan Saunders went to an ATM at 1 AM. Network maintenance disconnected the ATM from the bank ledger, letting him withdraw unlimited cash. Over four months, he withdrew $1.6 million, chartered private jets, and threw lavish parties. When guilt took over, he called the bank to confess—and they hung up because they were too embarrassed to admit it."
    },
    {
        "niche": "real_heists",
        "style": "tall-tale",
        "title": "The Man Who Sold the Eiffel Tower Twice",
        "premise": "In 1925, con artist Victor Lustig read that Paris was struggling to afford maintenance for the Eiffel Tower. Posing as a government minister in an elite hotel suite, he sold the 7,000-ton tower for scrap metal to a gullible businessman, collected a massive bribe, and fled to Vienna. Months later, seeing no police report, he returned to Paris and sold it a second time."
    },
    {
        "niche": "real_heists",
        "style": "paper-atlas",
        "title": "The 242 Million Dollar Fake Airport",
        "premise": "In 1995, Nigerian con artist Emmanuel Nwude impersonated the governor of the Central Bank of Nigeria. He convinced a senior director of a major Brazilian bank to invest $242 million into constructing a brand new international airport in Abuja. The airport was completely fictional, and by the time the bank discovered it, Nwude had vanished with hundreds of millions."
    },
    # Brainrot & Internet Absurdity
    {
        "niche": "brainrot_absurd",
        "style": "inside-out",
        "title": "The 10 Million Dollar Spotify AI Royalty Glitch",
        "premise": "A musician created hundreds of thousands of AI-generated ambient songs and programmed a network of thousands of automated streaming bots to play them on repeat 24 hours a day. For over seven years, the automated streams flew completely under the radar, harvesting over $10 million in streaming royalties before federal agents finally caught on."
    },
    {
        "niche": "brainrot_absurd",
        "style": "stick-story",
        "title": "The Man Who Sued Red Bull for No Wings",
        "premise": "In 2014, a consumer noticed Red Bull's famous slogan claimed 'Red Bull gives you wings'. He filed a massive class-action lawsuit claiming he drank the energy drink for 10 years without growing physical wings or gaining enhanced athletic ability. Red Bull chose to settle the lawsuit for $13 million, offering a $10 check to anyone who bought a can."
    }
]

def fetch_reddit_topic(niche="spicy_drama"):
    """Fetches high-engagement, trending story premises directly from Reddit JSON."""
    subreddits = SUBREDDIT_NICHES.get(niche, ["todayilearned"])
    chosen_sub = random.choice(subreddits)
    url = f"https://www.reddit.com/r/{chosen_sub}/top.json?t=month&limit=15"

    headers = {
        "User-Agent": "CurioCutStoryHarvester/2.0 (compatible; educational short-form bot)"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            posts = data.get("data", {}).get("children", [])

            candidates = []
            for p in posts:
                p_data = p.get("data", {})
                title = p_data.get("title", "")
                text = p_data.get("selftext", "")
                score = p_data.get("score", 0)

                # Skip meta/mod posts
                if "update" in title.lower() or "til" in title.lower() or len(text) > 100:
                    candidates.append({
                        "title": title,
                        "premise": text[:500] if text else title,
                        "source": f"r/{chosen_sub} (Score: {score})"
                    })

            if candidates:
                picked = random.choice(candidates)
                print(f"  Harvested live story from {picked['source']}: {picked['title'][:60]}...")
                return picked
    except Exception as e:
        print(f"  Reddit harvesting note ({chosen_sub}): {e}")

    # Fallback to evergreen vault
    matching = [s for s in EVERGREEN_VAULT if s["niche"] == niche]
    if not matching:
        matching = EVERGREEN_VAULT
    return random.choice(matching)

def get_next_daily_story():
    """Picks a random niche, fetches a fresh story, and maps it to the ideal visual style."""
    niches = ["spicy_drama", "real_heists", "brainrot_absurd"]
    chosen_niche = random.choice(niches)

    print(f"\n[Story Harvester] Selected Daily Niche: {chosen_niche.upper()}")
    story = fetch_reddit_topic(chosen_niche)

    # Map niche to the best animation visual style
    style_mapping = {
        "spicy_drama": "night-file",     # Dramatic, cinematic shadows, red accents
        "real_heists": "tall-tale",      # 3D con artists, bank, city streets
        "brainrot_absurd": "inside-out"  # 2D punchy kinetic graphics, x-ray overlays
    }
    style = story.get("style", style_mapping.get(chosen_niche, "tall-tale"))

    return {
        "niche": chosen_niche,
        "style": style,
        "title": story.get("title"),
        "premise": story.get("premise")
    }

if __name__ == "__main__":
    story = get_next_daily_story()
    print("\nResult:")
    print(json.dumps(story, indent=2))
