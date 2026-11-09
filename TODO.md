# 📋 CurioCut: Master Action Plan

## 1. 🚀 Push to Private GitHub Repo (Takes 2 mins)
- [ ] **Create Private Repo on GitHub:**
  - Go to [github.com/new](https://github.com/new).
  - Repository name: `curiocut-shorts`
  - Choose: **Private** (Do NOT check initialize with README/license/gitignore).
- [ ] **Push the project from your terminal:**
  ```bash
  git branch -M main
  git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/curiocut-shorts.git
  git push -u origin main
  ```
- [ ] **Add your Cloud Secrets in GitHub:**
  - In your repo: **Settings ➔ Secrets and variables ➔ Actions ➔ New repository secret**.
  - **Secret 1:** `GROQ_API_KEY` ➔ Paste your key from `.env`.
  - **Secret 2:** `YOUTUBE_TOKEN_JSON` ➔ Copy and paste the entire text from `youtube_token.json`.
  - **Secret 3 (Tomorrow for Instagram):** `INSTAGRAM_ACCOUNT_ID` ➔ Your Instagram Creator/Business ID (e.g. `178414...`).
  - **Secret 4 (Tomorrow for Instagram):** `INSTAGRAM_ACCESS_TOKEN` ➔ Your Meta Graph API Access Token.

---

## 2. 📱 Instagram Reels Setup (Ready & Pre-Wired!)
Everything for Instagram Reels is already fully coded in `instagram_uploader.py`, `make_short.py`, and GitHub Actions!
- When you get your Meta token tomorrow:
  - Add to `.env` (for local runs) or GitHub Secrets (for cloud automation):
    ```env
    INSTAGRAM_ACCOUNT_ID=your_instagram_user_id
    INSTAGRAM_ACCESS_TOKEN=your_meta_access_token
    ```
  - That's it! When those two keys are present, CurioCut automatically posts to both YouTube Shorts AND Instagram Reels in one go.

---

## 3. ✍️ Upgraded True-Story Engine
- Replaced the hallucinated, nonsensical stories with a verified true-story engine:
  - Real, jaw-dropping true events (Dan Saunders $1.6M ATM glitch, Victor Lustig selling the Eiffel Tower twice, Patrick Combs $95k junk check loophole, 1990 Gardner Museum heist, John Leonard Harrier jet lawsuit, etc.).
  - Zack D. Films / MagnatesMedia / SunnyV2 gritty human storytelling.
  - Flexible duration (35 to 55 seconds), natural sentence pacing, and ironic punchlines.

---

## 4. 🛠️ Useful Local Commands
- **Generate a test script anytime:**
  ```bash
  python generate_script.py
  ```
- **Generate a video locally:**
  ```bash
  python make_short.py --draft
  ```
- **Publish to YouTube & Instagram:**
  ```bash
  python make_short.py --upload --privacy public
  ```
- **Upload any existing MP4 to Instagram directly:**
  ```bash
  python instagram_uploader.py "path/to/video.mp4" "Your Caption Here #shorts #viral"
  ```
- **Upload any existing MP4 to YouTube directly:**
  ```bash
  python youtube_uploader.py "path/to/video.mp4" "Your Video Title" public
  ```
