# CurioCut

A fully autonomous short-form video pipeline that runs on a $0 stack. Every day it picks a topic, generates a script, renders a 3D animated scene, voices it with Kokoro TTS, and uploads the finished video to YouTube Shorts and Instagram Reels, all without touching a single button.

---

## How It Works

Three cron slots fire daily (1 PM, 7 PM, and 9:30 PM IST). Each slot:

1. Cloudflare Edge Worker wakes up and fires a `repository_dispatch` event to GitHub Actions
2. GitHub Actions triggers `trigger_kaggle.py`, which queues the job on a Kaggle GPU notebook
3. Kaggle pulls the repo, generates the script and dialogue, renders the video in headless Chrome with WebGL, and uploads to YouTube + Instagram
4. Live render progress streams to Discord in real-time via the bot. Post notifications with direct action buttons arrive in `#youtube-posts` and `#instagram-posts`
5. Instagram comments matching the CTA keyword (`MCPSER`, `TOOL`, etc.) get an auto-reply and a DM with the resource link: handled 24/7 by Cloudflare Edge, not Kaggle

Total monthly cost: $0.

---

## Video Styles

The pipeline has two modes. `claude-desk` is the flagship 3D style; the rest rotate through classic 2D/3D animation styles for story content.

| Style | Description |
|---|---|
| `claude-desk` | Two 3D characters (Guide + Skeptic) at a glowing desk debating a dev tool or Claude skill. Cinematic speaker cuts, dynamic props, Kokoro dual-voice. |
| `tall-tale` | 2D toon characters in a 3D sunny world. True stories told fast and funny. |
| `deep-dive` | Zack D. Films style 3D anatomy/science explainer. |
| `night-file` | Dark mystery and true crime. Low key lighting, dramatic pacing. |
| `inside-out` | 2D x-ray cutaway explainer. |
| `paper-atlas` | Cut-paper collage look for history topics. |
| `stick-story` | Minimal stick-figure survival and life-hack format. |

---

## Repo Layout

```
.
├── make_short.py               # Main pipeline entry point (script → audio → render → upload)
├── generate_script.py          # Story script generator (Gemini / Groq / offline fallback)
├── generate_tech_dialogue.py   # Two-person dialogue generator for claude-desk style
├── tech_harvester.py           # Finds trending MCP servers, GitHub repos, HN posts
├── story_harvester.py          # Finds story topics from Reddit, Wikipedia, Groq
├── dual_voice.py               # Kokoro TTS for Guide + Skeptic voices
├── discord_notifier.py         # Discord Bot API helpers for all 9 channels
├── instagram_comment_bot.py    # Comment auto-responder and DM dispatcher (backup)
├── instagram_uploader.py       # Uploads reel via Meta Graph API v21
├── youtube_uploader.py         # Uploads short via YouTube Data API v3
├── kaggle_worker.py            # Cloud runner that executes on Kaggle GPU
├── trigger_kaggle.py           # Dispatches and streams Kaggle notebook run
├── authenticate_youtube.py     # One-time OAuth flow to generate youtube_token.json
├── published_reels.json        # Maps Instagram media IDs to reel metadata for comment bot
├── requirements.txt
│
├── cloudflare/
│   ├── worker.js               # Edge worker: cron triggers, Discord interactions, IG webhooks
│   └── wrangler.toml           # Deployment config (3 cron slots)
│
├── faceless-shorts-skill/
│   └── faceless-shorts/
│       ├── scripts/            # voice.py (Kokoro TTS), words.py (Whisper captions), mix.py
│       └── styles/
│           ├── claude-desk/    # 3D studio scene (Three.js: toon.js, shots.js, props.js, etc.)
│           ├── tall-tale/
│           ├── deep-dive/
│           ├── night-file/
│           ├── inside-out/
│           ├── paper-atlas/
│           └── stick-story/
│
└── .github/workflows/
    └── daily-shorts.yml        # GitHub Actions: receives dispatch, triggers Kaggle
```

---

## The Rendering Stack

Each animation style is a self-contained Three.js scene running in headless Chrome via Puppeteer. The capture pipeline:

- `tools/capture.mjs`: drives Chrome DevTools Protocol, captures frames at 1080x1920 (9:16), pipes raw frames to FFmpeg
- `tools/mix.py`: blends the Kokoro voiceover, procedural sound cues, and music bed into `data/mix.wav`
- `scripts/words.py`: runs faster-whisper on the audio to get word-level timestamps for the caption system
- `scripts/voice.py`: single-speaker Kokoro TTS for non-dialogue styles

For `claude-desk`, `dual_voice.py` runs first to alternate between Guide (`am_fenrir`) and Skeptic (`af_bella`) voices and produce `data/lines.json` with per-line speaker + timing data that `shots.js` reads to drive cinematic speaker cuts.

---

## Discord Control Panel

The `#panel` channel has buttons to trigger any slot on demand, create a custom topic, skip the next slot, or emergency stop. All button interactions are handled by the Cloudflare worker (no server needed).

The `#live-progress` channel shows a single message that edits in real-time as frames render, with a progress bar and frame counter. Buttons for YouTube and Instagram appear once the upload is done.

---

## Comment-to-DM

When a viewer comments the CTA keyword on a reel, the Cloudflare worker:

1. Verifies the comment has no existing replies (live Meta Graph API check)
2. Posts a public reply on the reel
3. Sends a private DM with the resource link
4. Updates the `#dms-sent` Discord channel

Deduplication runs at two layers: a 24-hour edge cache keyed by comment ID, and a live reply check on the Meta API before any action is taken.

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Chrome (for local rendering)
- Kaggle account (for cloud GPU rendering)
- Cloudflare account (free tier)

### Credentials needed

Create a `.env` file in the project root:

```env
GROQ_API_KEY=
GEMINI_API_KEY=
GEMINI_API_KEY_BACKUP=

INSTAGRAM_ACCOUNT_ID=
INSTAGRAM_ACCESS_TOKEN=

DISCORD_BOT_TOKEN=
DISCORD_APPLICATION_ID=
DISCORD_PUBLIC_KEY=
```

For YouTube, run `authenticate_youtube.py` once to generate `youtube_token.json`.

### GitHub Actions secrets

The workflow reads these from GitHub Secrets:

```
GEMINI_API_KEY, GEMINI_API_KEY_BACKUP, GROQ_API_KEY
KAGGLE_USERNAME, KAGGLE_API_TOKEN
YOUTUBE_TOKEN_JSON
INSTAGRAM_ACCOUNT_ID, INSTAGRAM_ACCESS_TOKEN
DISCORD_BOT_TOKEN
```

### Cloudflare Worker secrets

```bash
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put DISCORD_BOT_TOKEN
npx wrangler secret put INSTAGRAM_ACCESS_TOKEN
```

### Local render (single video)

```bash
pip install -r requirements.txt
python make_short.py --style claude-desk
python make_short.py --style tall-tale --upload
```

### Deploy Cloudflare worker

```bash
cd cloudflare
npx wrangler deploy
```

---

## Cron Schedule (IST)

| Slot | Trigger | Style |
|---|---|---|
| 1 | 11:55 AM | Classic rotation |
| 2 | 6:25 PM | Classic rotation |
| 3 | 8:55 PM | `claude-desk` (flagship) |

All three slots can also be manually triggered from Discord `#panel` or via GitHub Actions `workflow_dispatch`.

---

## License

MIT. The Three.js vendor files in `faceless-shorts-skill/` are MIT licensed separately (see `vendor/LICENSE-three.txt` in each style directory).

