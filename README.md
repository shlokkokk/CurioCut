<div align="center">

# 🎬 CurioCut

### Autonomous Short-Form Video Studio & Publishing Pipeline
**Fully automated • Dual 3D Render Engines • Zero Monthly Cloud Cost**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Blender 4.3](https://img.shields.io/badge/Blender-4.3_EEVEE_Next-E87D0D?style=for-the-badge&logo=blender&logoColor=white)](https://blender.org)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL_Studio-000000?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org)
[![Kokoro TTS](https://img.shields.io/badge/Kokoro_TTS-Neural_Voice-7C3AED?style=for-the-badge)](https://github.com/thewh1teagle/kokoro-onnx)
[![Cloudflare Workers](https://img.shields.io/badge/Cloudflare-Edge_Worker-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://workers.cloudflare.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<br/>

*CurioCut autonomously researches trending topics, generates natural screenplays, animates 3D scenes, synthesizes dual-speaker neural audio, aligns word-synced subtitles, and publishes finished vertical videos to YouTube Shorts and Instagram Reels — with zero manual intervention and $0 monthly compute cost.*

</div>

---

## ⚡ Highlights

- **$0 Serverless Stack**: Orchestrated across Cloudflare Edge, GitHub Actions, and cloud GPU environments with round-robin quota rotation.
- **Dual 3D Engines**: Headless WebGL (Three.js/Chrome) for fast dynamic studio dialogue + Headless Blender 4.3 (EEVEE Next) for procedural 3D narrative films.
- **Multi-Speaker Neural Speech**: Ultra-fast ONNX-powered Kokoro TTS paired with acoustic silence trimming and phonetic tech normalization.
- **Phonetic Word-Level Subtitles**: Sub-second alignment powered by faster-whisper, generating highlighted kinetic captions directly onto the canvas.
- **Autonomous Multi-Platform Publishing**: Direct automated publishing to YouTube Shorts (YouTube Data API v3) and Instagram Reels (Meta Graph API v21).
- **24/7 Edge Comment-to-DM Engine**: Cloudflare Worker instantly detects keyword triggers on reels and delivers private resource DMs in seconds.
- **Real-Time Discord Observability**: Live frame-by-frame render meters, remote control trigger buttons, and versioned execution logs.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 1. CLOUDFLARE EDGE WORKER                   │
│  • Precision Cron Schedulers (3 Daily Release Slots)        │
│  • 24/7 Instagram Comment-to-DM Lead Delivery               │
│  • Discord Remote Control & Emergency Quota Protection      │
└──────────────────────────────┬──────────────────────────────┘
                               │ repository_dispatch
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. GITHUB ACTIONS DISPATCHER               │
│  • Multi-Account Pool Manager (Automated Round-Robin)       │
│  • Account Health Check & Failover Switching                │
└──────────────────────────────┬──────────────────────────────┘
                               │ triggers GPU runner
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. CLOUD GPU RUNNER                       │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │    Narrative AI       │       │    Audio Synthesis    │  │
│  │ • Gemini / Groq LLMs  │  ──►  │ • Kokoro ONNX Dual-TTS│  │
│  │ • Anti-cliché prompts │       │ • Whisper Alignments  │  │
│  └───────────────────────┘       └───────────────────────┘  │
│              │                               │              │
│              ▼                               ▼              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 Dual Visual Render Engines            │  │
│  │  • Three.js WebGL (Headless Chrome + Puppeteer)       │  │
│  │  • Blender 4.3 EEVEE Next (Procedural 3D Cinema)      │  │
│  │  • FFmpeg 1080x1920 (9:16 Vertical HD Muxing)         │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │ publishes video
                               ▼
        ┌─────────────────────────────────────────────┐
        │             DISTRIBUTION NETWORK            │
        │  • YouTube Shorts (OAuth v3 API)            │
        │  • Instagram Reels (Meta Graph API v21)     │
        │  • Discord Community Live Stream Feeds      │
        └─────────────────────────────────────────────┘
```

---

## 🎨 Creative Animation Suites

CurioCut intelligently matches story scripts to distinct visual worlds:

| Style | Engine | Description |
|---|---|---|
| **`claude-desk`** | Three.js / WebGL | **Flagship Tech Studio.** Two 3D characters (*Guide* + *Skeptic*) at a glowing desk debating dev tools and AI skills with dynamic holographic props. |
| **`dev-studio`** | Three.js / WebGL | **Developer Loft.** Seated developer and a hovering ceramic mascot robot exploring open-source GitHub breakthroughs. |
| **`town-rule`** | Blender 4.3 EEVEE | **Cinematic 3D Narrative.** Procedural environments, custom facial decal rigs, atmospheric lighting, and rule-based psychological horror/mystery. |
| **`deep-dive`** | Three.js / WebGL | **Medical & Anatomy Explainer.** Zack D. Films style 3D biological cross-sections, glowing cyan X-ray views, and macro vessel journeys. |
| **`tall-tale`** | Three.js / WebGL | **Cartoon True Stories.** Flat 2D animated characters moving through a sunny 3D town world exploring bizarre loopholes and heists. |
| **`night-file`** | Three.js / WebGL | **Investigative Mystery.** Low-key 3D noir corridors, cork evidence boards with connecting red strings, and typewriter archives. |
| **`paper-atlas`** | Three.js / WebGL | **Historical Cut-Paper.** Aged parchment maps, crimson movement routes, and wax seals chronicling turning points in history. |

---

## 🔄 Daily Production Slots (IST)

| Slot | Local Time | Topic Focus | Visual Engine |
|---|---|---|---|
| **Slot 1** | **1:00 PM IST** (11:55 AM trigger) | Rule-based suspense / Classic true stories | Blender 4.3 EEVEE Next / WebGL |
| **Slot 2** | **7:00 PM IST** (05:55 PM trigger) | Claude skills & autonomous developer tools | Three.js (`claude-desk`) |
| **Slot 3** | **9:30 PM IST** (08:55 PM trigger) | Open-source GitHub exploits & AI break-outs | Three.js (`dev-studio`) |

*All slots can be triggered on demand or skipped via the Discord remote panel.*

---

## 🚀 The Core Pipeline

### 1. Intelligent Scripting & Directing
* Dynamic topic harvesting from curated vaults and real-time open-source repositories.
* Screenplay generation optimized for spoken cadence, short conversational cuts (1.5–2.5s), and zero AI buzzwords.
* Phonetic normalizer transforms technical jargon (`API` $\rightarrow$ `A.P.I.`, `MCP` $\rightarrow$ `M.C.P.`, `$50K` $\rightarrow$ `fifty thousand dollars`).

### 2. Dual-Speaker Audio Engineering
* **Guide**: Grounded, resonant masculine voice (`am_fenrir`).
* **Skeptic / Mascot**: Bright, emotive questioning voice (`af_bella`).
* Phonetic word timestamps generated by faster-whisper drive dynamic speaker switching and kinetic captions.
* Procedural sound effects and lo-fi audio beds mixed via NumPy.

### 3. Headless GPU Video Rendering
* Headless Chrome captures synchronized 1080×1920 frames via Chrome DevTools Protocol.
* Blender 4.3 EEVEE Next renders procedural geometry, volumetric lighting, and camera paths.
* Direct pipe to FFmpeg for hardware-accelerated H.264 video compression.

### 4. Edge Comment-to-DM Automation
* Viewers comment the designated trigger keyword (e.g. `TOOL`, `CLAUDE`, `AGENT`) on Instagram Reels.
* Cloudflare Worker checks deduplication in KV cache and live Meta Graph API.
* Automatically posts a public reply and sends a private direct message with the resource link.

---

## 📡 Discord Command & Observability Suite

CurioCut streams every phase of production to a dedicated Discord operations center:

- **`#live-progress`**: A single auto-updating message reflecting real-time render percentage, active frame counts, and platform links.
- **`#panel`**: Interactive buttons to trigger slots on demand, inject custom topics, skip upcoming slots, or execute an emergency stop.
- **`#run-logs`**: Versioned execution cards with attached logs for cloud runs.
- **`#youtube-posts` & `#instagram-posts`**: Instant notifications with direct link buttons when videos go live.
- **`#dms-sent`**: Real-time audit log of automated Instagram direct messages delivered.

---

## 🛠️ Local Development & Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Chrome (for local WebGL rendering)
- FFmpeg

### Installation
```bash
# Clone the repository
git clone https://github.com/shlokkokk/CurioCut.git
cd CurioCut

# Install dependencies
pip install -r requirements.txt
```

### Render a Single Short Locally
```bash
# Generate and render a claude-desk video
python make_short.py --style claude-desk

# Render a fast draft preview
python make_short.py --style tall-tale --draft

# Render and publish directly
python make_short.py --style claude-desk --upload
```

### Environment Configuration
Create a `.env` file in the root directory:

```env
# AI Scripting Engines
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Social Platforms
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id
INSTAGRAM_ACCESS_TOKEN=your_instagram_token

# Discord Observability (Bot & Webhooks)
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_APPLICATION_ID=your_discord_app_id
DISCORD_WEBHOOK_LIVE_PROGRESS=your_webhook_url
DISCORD_WEBHOOK_ENGINE_LOGS=your_webhook_url
```

*For YouTube Shorts, run `python authenticate_youtube.py` once to establish OAuth credentials.*

---

## 📄 License

This project is licensed under the MIT License. Included third-party visual components and libraries are subject to their respective upstream licenses.
