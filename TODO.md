# 📋 CurioCut: Tomorrow's Master Action Plan

## 1. 🚀 Push to Private GitHub Repo (Takes 3 mins)
- [ ] **Create Private Repo:**
  - Go to [github.com/new](https://github.com/new).
  - Repository name: `curiocut-shorts`
  - Choose: **Private** (Do NOT initialize with README).
- [ ] **Push the project from your terminal:**
  ```bash
  git init
  git add .
  git commit -m "Launch CurioCut Autonomous Shorts Engine"
  git branch -M main
  git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/curiocut-shorts.git
  git push -u origin main
  ```
- [ ] **Add your 2 Cloud Secrets in GitHub:**
  - In your repo on GitHub: **Settings ➔ Secrets and variables ➔ Actions ➔ New repository secret**.
  - **Secret 1:** `GROQ_API_KEY` ➔ Paste your key (`gsk_...` from `.env`).
  - **Secret 2:** `YOUTUBE_TOKEN_JSON` ➔ Copy and paste the entire text from `youtube_token.json`.

---

## 2. 📱 Instagram Reels Setup & Meta Rate Limit Timing
- [ ] **When to Retry Meta Phone Verification:**
  - **Cooldown Start:** Nov 9 at ~3:00 AM.
  - **Meta Cooldown Window:** Exactly **24 hours**.
  - **Safe Retry Time:** **Nov 10 at 3:00 AM** (or tomorrow afternoon).
  - ⚠️ *Rule:* Do not touch or attempt to submit the phone number before then, or Meta will reset the 24-hour timer.
- [ ] **The Zero-Wait Workaround (Do this tomorrow anytime):**
  - Instead of waiting for your main number's cooldown, simply type a **family member's phone number** to receive the 6-digit code. Meta only needs it once for developer verification and will never message it again.
- [ ] **Generate the Meta Access Token:**
  - Go to [developers.facebook.com/tools/explorer/](https://developers.facebook.com/tools/explorer/).
  - Select your app `ReelsAutoPoster`.
  - Add permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`.
  - Click **Generate Access Token**.
  - Paste it to Antigravity and we will wire up `instagram_uploader.py` in 60 seconds!

---

## 3. ✍️ Storytelling & Script Refinement
- [ ] **The Script Critique:**
  - The first test script (*The Free-Hotel Loophole That Made Him a Billionaire of Pillows*) proved the technical pipeline (loop, audio sync, cuts, 40s duration), but the phrasing was a bit quirky/robotic in the middle.
- [ ] **Tomorrow's Script Enhancements:**
  - Tighten `PSYCHOLOGY_SYSTEM_PROMPT` in `generate_script.py` to sound 100% human, gritty, and grounded (like real YouTube creators: Zack D. Films, MagnatesMedia, or SunnyV2).
  - Inject real historical cases: the guy who sold the Eiffel Tower twice, the bank teller who stole 1 cent from every account, the pilot who faked his way onto Pan Am flights.

---

## 4. 🛠️ Useful Local Commands
- **Generate a test video locally without uploading:**
  ```bash
  python make_short.py --draft
  ```
- **Generate and upload immediately to YouTube Shorts:**
  ```bash
  python make_short.py --upload --privacy public
  ```
- **Upload any existing MP4 to YouTube Shorts:**
  ```bash
  python youtube_uploader.py "path/to/video.mp4" "Your Video Title" public
  ```

