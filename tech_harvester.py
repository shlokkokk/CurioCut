"""Autonomous Tech & AI Exploit Harvester for CurioCut.
Scrapes cutting-edge developer breakthroughs, underground tools, and AI exploits across 4 tiers:
1. Tier 1: Peak Reddit Developer Communities (r/LocalLLaMA, r/ChatGPTCoding, r/ClaudeAI, r/selfhosted, r/InternetIsBeautiful)
2. Tier 2: Hacker News Firebase API (Real-time top stories, Show HN, high-scoring tech launches)
3. Tier 3: GitHub Trending AI / Developer Repositories
4. Tier 4: Evergreen Master Exploit Vault (Verified 10/10 mind-blowing viral tech stories)

Zero manual API keys required — uses public REST APIs and custom user-agents.
"""
import os
import sys
import json
import random
import re
import urllib.request
import urllib.parse
from pathlib import Path

HISTORY_FILE = Path(__file__).resolve().parent / "history.json"

# Peak Reddit developer & AI subreddits
REDDIT_TECH_SUBREDDITS = [
    "LocalLLaMA",
    "ChatGPTCoding",
    "ClaudeAI",
    "selfhosted",
    "InternetIsBeautiful",
    "ArtificialInteligence",
    "webdev"
]

# Curated Evergreen Master Exploits Vault (Guaranteed 10/10 Viral Tech Stories)
EVERGREEN_TECH_VAULT = [
    {
        "title": "The $1 Billion Jarvis Built for Free on GitHub",
        "tool_name": "OpenJarvis",
        "cta_keyword": "JARVIS",
        "resource_url": "https://github.com/open-jarvis/OpenJarvis",
        "premise": "Stanford researchers just open-sourced OpenJarvis on GitHub, giving anyone Tony Stark's AI assistant completely free. Instead of spending billions or paying monthly subscriptions, it connects to your local machine, reads your unread Gmail and calendar, and speaks an audio briefing every morning highlighting only what matters. It runs 100% locally on your computer with zero data sent to the cloud.",
        "steps": [
            "Copy the OpenJarvis GitHub link and paste it into Claude Code or your terminal",
            "Connect your local email or calendar with one click",
            "Turn on the spoken briefing and wake up to your personal Jarvis reading your day"
        ]
    },
    {
        "title": "Clone Any Website Frontend in 4 Seconds",
        "tool_name": "ScreenToCode",
        "cta_keyword": "CLONE",
        "resource_url": "https://github.com/abi/screenshot-to-code",
        "premise": "A developer created an open-source tool called Screenshot-to-Code that turns any screenshot of a website into 100% production-ready React, Tailwind, and Vue code in four seconds. Instead of hiring a frontend agency for $10,000, you upload an image of Stripe, Airbnb, or any SaaS, and it writes responsive, pixel-perfect clean code instantly.",
        "steps": [
            "Take a screenshot of any website or UI you want to copy",
            "Drop the image into the local vision interface",
            "Download the exported React components and run them locally"
        ]
    },
    {
        "title": "The Autonomous Browser Agent That Works While You Sleep",
        "tool_name": "Browser-Use",
        "cta_keyword": "AGENT",
        "resource_url": "https://github.com/browser-use/browser-use",
        "premise": "An open-source AI called Browser-Use literally takes over your Google Chrome browser and clicks, types, researches, and fills forms like a real human. A guy used it to automatically apply to 500 job postings in 30 minutes, while another user used it to find the cheapest flights across 20 booking sites completely on autopilot.",
        "steps": [
            "Install the browser-use python package with one command",
            "Type your instruction in plain English like 'Find the cheapest flights to Tokyo'",
            "Watch Chrome open and physically navigate, click, and solve the task by itself"
        ]
    },
    {
        "title": "Transcribe 100 Hours of Audio in 3 Minutes for $0",
        "tool_name": "Faster-Whisper",
        "cta_keyword": "AUDIO",
        "resource_url": "https://github.com/SYSTRAN/faster-whisper",
        "premise": "Instead of paying $20 a month for transcription services like Otter or Descript, developers built an optimized local engine called Faster-Whisper. It transcribes audio 4x faster than real-time with 99% accuracy, generates synchronized word-level timestamps, and runs entirely offline on your GPU with zero subscription fees.",
        "steps": [
            "Download the lightweight local model onto your machine",
            "Drop any MP4, podcast, or voice memo into the folder",
            "Get pixel-perfect subtitles and timestamped transcripts in seconds"
        ]
    },
    {
        "title": "Replace a $500/Month SaaS with One Free Self-Hosted Server",
        "tool_name": "Coolify",
        "cta_keyword": "SERVER",
        "resource_url": "https://github.com/coollabsio/coolify",
        "premise": "Coolify is known as the open-source, self-hosted Heroku and Vercel alternative. Developers paying thousands of dollars a month on AWS and Vercel are migrating to a $5 VPS running Coolify, getting unlimited databases, automatic SSL, GitHub auto-deployments, and complete data ownership with zero platform lock-in.",
        "steps": [
            "Spin up a cheap five dollar server on any cloud provider",
            "Run the single curl command to install Coolify",
            "Connect your GitHub and deploy unlimited web apps with free SSL"
        ]
    },
    {
        "title": "The Free AI Coding Copilot That Runs 100% Offline",
        "tool_name": "Ollama + Continue",
        "cta_keyword": "OLLAMA",
        "resource_url": "https://github.com/ollama/ollama",
        "premise": "Companies are banning GitHub Copilot because it leaks proprietary code to cloud servers. A developer set up Ollama with DeepSeek Coder inside VS Code, giving them autocomplete, code refactoring, and bug fixes completely offline on an airplane with zero latency and zero data leakage.",
        "steps": [
            "Install Ollama locally and pull the latest coding model",
            "Add the Continue extension to VS Code or Cursor",
            "Tab-complete and chat with your codebase with zero internet connection"
        ]
    },
    {
        "title": "Open-Source VoiceStudio Replaces ElevenLabs for $0",
        "tool_name": "VoiceStudio",
        "cta_keyword": "VOICE",
        "resource_url": "https://github.com/SparkAudio/VoiceStudio",
        "premise": "Instead of paying hundreds of dollars for ElevenLabs voice generation, VoiceStudio just launched as an open-source, fully-local AI voice clone studio. It clones any voice in three seconds from a short audio clip and runs entirely on your own GPU with zero API bills.",
        "steps": [
            "Clone the VoiceStudio repository on GitHub",
            "Upload a three second voice sample of anyone",
            "Type any text and generate crystal-clear cloned speech for free"
        ]
    },
    {
        "title": "Autonomous Global Intelligence Dashboard Built in 24 Hours",
        "tool_name": "WorldMonitor",
        "cta_keyword": "INTEL",
        "resource_url": "https://github.com/koala73/worldmonitor",
        "premise": "A solo developer built an AI-powered real-time global intelligence dashboard called WorldMonitor that monitors military flights, live satellites, seismic sensors, and financial breaking news faster than Bloomberg terminals costing thirty thousand dollars a year.",
        "steps": [
            "Download the WorldMonitor release on GitHub",
            "Launch the dashboard on your computer",
            "Track global events and live breaking data with zero subscription fees"
        ]
    }
]

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def is_duplicate(title):
    history = load_history()
    recent_titles = [h.get("title", "").lower() for h in history[-50:] if h.get("title")]
    for rt in recent_titles:
        if len(set(title.lower().split()) & set(rt.split())) >= 4:
            return True
    return False

def sanitize(text):
    clean = re.sub(r'https?://\S+', '', text)
    clean = re.sub(r'[\r\n]+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def fetch_reddit_tech():
    """Tier 1: Scrapes trending posts from top developer & AI subreddits."""
    sub = random.choice(REDDIT_TECH_SUBREDDITS)
    url = f"https://www.reddit.com/r/{sub}/top.json?t=month&limit=25"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CurioCutTechHarvester/2.0"
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        posts = data.get("data", {}).get("children", [])

        candidates = []
        for p in posts:
            p_data = p.get("data", {})
            title = p_data.get("title", "")
            selftext = p_data.get("selftext", "")
            url_link = p_data.get("url", "")
            score = p_data.get("score", 0)

            # Filter out meta, stickied, or short discussion posts
            if p_data.get("stickied") or len(title) < 25 or is_duplicate(title):
                continue

            # Look for tool announcements, releases, hacks, or breakthroughs
            keywords = ["release", "built", "open source", "free", "github", "tool", "show hn", "prompt", "model", "loophole", "fast"]
            if not any(k in title.lower() for k in keywords):
                continue

            premise = selftext if len(selftext) > 100 else title
            cta = re.sub(r'[^A-Z]', '', title.split()[0].upper())[:6] or "TOOL"
            candidates.append({
                "title": sanitize(title[:80]),
                "tool_name": title.split()[0][:15],
                "cta_keyword": cta if len(cta) >= 3 else "HACK",
                "resource_url": url_link if "github.com" in url_link else f"https://reddit.com{p_data.get('permalink')}",
                "premise": sanitize(premise[:800]),
                "source": f"Reddit r/{sub} (Score: {score})"
            })

        if candidates:
            picked = random.choice(candidates)
            print(f"  [Tier 1] Harvested breaking tech discovery from {picked['source']}")
            return picked

    raise RuntimeError(f"No suitable candidates found in r/{sub}")

def fetch_hacker_news():
    """Tier 2: Real-time top tech breakthroughs from Hacker News Firebase API."""
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    req = urllib.request.Request(url, headers={"User-Agent": "CurioCut/2.0"})

    with urllib.request.urlopen(req, timeout=8) as resp:
        story_ids = json.loads(resp.read().decode("utf-8"))[:30]

    random.shuffle(story_ids)
    for sid in story_ids[:10]:
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
        req_item = urllib.request.Request(item_url, headers={"User-Agent": "CurioCut/2.0"})
        with urllib.request.urlopen(req_item, timeout=6) as resp:
            item = json.loads(resp.read().decode("utf-8"))
            title = item.get("title", "")
            url_link = item.get("url", "")
            score = item.get("score", 0)

            if score > 50 and not is_duplicate(title):
                # Check for "Show HN" or practical tech
                kw = ["show hn", "open source", "ai", "llm", "tool", "fast", "local", "model", "free", "github"]
                if any(k in title.lower() for k in kw):
                    clean_title = re.sub(r'^(Show HN:\s*|Ask HN:\s*)', '', title, flags=re.IGNORECASE)
                    cta = re.sub(r'[^A-Z]', '', clean_title.split()[0].upper())[:6] or "TOOL"
                    print(f"  [Tier 2] Harvested Hacker News top story: '{title}' (Points: {score})")
                    return {
                        "title": clean_title,
                        "tool_name": clean_title.split()[0][:15],
                        "cta_keyword": cta if len(cta) >= 3 else "TOOL",
                        "resource_url": url_link,
                        "premise": f"{title}. A viral open-source project shared on Hacker News that empowers developers to automate workflows and replace expensive software.",
                        "source": f"Hacker News (Points: {score})"
                    }

    raise RuntimeError("No suitable Hacker News stories found")

def fetch_github_trending():
    """Tier 3: Trending AI & developer tools from GitHub Search API (Zero API key needed)."""
    topics = ["topic:ai", "topic:llm", "topic:agent", "topic:developer-tools", "topic:automation"]
    chosen_topic = random.choice(topics)
    url = f"https://api.github.com/search/repositories?q={chosen_topic}+stars:>300&sort=stars&order=desc"
    req = urllib.request.Request(url, headers={"User-Agent": "CurioCutTechHarvester/2.0"})

    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        items = data.get("items", [])

    random.shuffle(items)
    for repo in items[:15]:
        name = repo.get("name", "")
        desc = repo.get("description", "") or ""
        stars = repo.get("stargazers_count", 0)
        repo_url = repo.get("html_url", "")
        
        if not desc or len(desc) < 20 or is_duplicate(name):
            continue

        cta = re.sub(r'[^A-Z]', '', name.upper())[:6]
        if len(cta) < 3:
            cta = "TOOL"

        print(f"  [Tier 3] Harvested GitHub trending repo: {repo.get('full_name')} ({stars:,} stars)")
        return {
            "title": f"The Free Open-Source {name} Tool",
            "tool_name": name,
            "cta_keyword": cta,
            "resource_url": repo_url,
            "premise": f"{desc}. An open-source developer tool trending on GitHub with over {stars:,} stars that gives developers superpowers for zero cost.",
            "source": f"GitHub Trending ({stars:,} stars)"
        }

    raise RuntimeError("No suitable GitHub repos found")

def get_next_tech_story():
    """Multi-tiered robust harvester: GitHub Trending -> Hacker News -> Reddit -> Evergreen Master Vault."""
    print("\n" + "="*60)
    print("   CURIO CUT TECH & AI INTELLIGENCE HARVESTER   ")
    print("="*60)

    # 1. Try GitHub Trending AI Repos (Free, high-velocity developer tools)
    try:
        return fetch_github_trending()
    except Exception as e:
        print(f"  GitHub Harvester notice: {e}. Switching to Tier 2 (Hacker News)...")

    # 2. Try Hacker News Firebase API
    try:
        return fetch_hacker_news()
    except Exception as e:
        print(f"  Hacker News notice: {e}. Switching to Tier 3 (Reddit)...")

    # 3. Try Reddit Developer Goldmines
    try:
        return fetch_reddit_tech()
    except Exception as e:
        print(f"  Reddit Harvester notice: {e}. Switching to Tier 4 (Evergreen Vault)...")

    # 4. Guaranteed Evergreen Master Vault
    available = [s for s in EVERGREEN_TECH_VAULT if not is_duplicate(s["title"])]
    if not available:
        available = EVERGREEN_TECH_VAULT
    picked = random.choice(available)
    print(f"  [Tier 4 Vault] Loaded master verified tech exploit: '{picked['title']}'")
    return picked

if __name__ == "__main__":
    story = get_next_tech_story()
    print("\nFinal Harvested Story:")
    print(json.dumps(story, indent=2))
