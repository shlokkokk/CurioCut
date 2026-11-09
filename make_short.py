"""Master Autonomous Short Generator for CurioCut.
Orchestrates the entire pipeline end-to-end:
1. Dynamic rotation across curated 3D/2D animation styles
2. Perfect synchronization between story voiceover, word captions, and 3D camera cuts
3. Kokoro AI Voiceover (voice.py)
4. Whisper Millisecond Caption Timing (words.py)
5. Procedural Sound FX & Music Synthesis (mix.py)
6. Headless Chrome DevTools 3D/2D Capture & FFmpeg Video Assembly
7. Automated YouTube Shorts & Instagram Reels Publishing
"""
import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

try:
    from discord_notifier import (
        notify_engine, notify_alert, notify_error,
        notify_youtube_post, notify_youtube_error,
        notify_instagram_post, notify_instagram_error
    )
except ImportError:
    def notify_engine(*a, **kw): pass
    def notify_alert(*a, **kw): pass
    def notify_error(*a, **kw): pass
    def notify_youtube_post(*a, **kw): pass
    def notify_youtube_error(*a, **kw): pass
    def notify_instagram_post(*a, **kw): pass
    def notify_instagram_error(*a, **kw): pass

WORKSPACE = Path(__file__).resolve().parent
SKILL_DIR = WORKSPACE / "faceless-shorts-skill" / "faceless-shorts"
FACELSS_HOME = Path.home() / ".faceless-shorts"
BIN_DIR = FACELSS_HOME / "bin"
VENV_PYTHON = FACELSS_HOME / "venv" / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

node_candidate = BIN_DIR / ("node.exe" if os.name == 'nt' else "node")
NODE_EXE = str(node_candidate) if node_candidate.exists() else "node"

ROTATION_STYLES = [
    "tall-tale",     # 3D con/loophole story (e.g. The Girl Who Was Mailed to Grandma)
    "deep-dive",     # Zack D. Films 3D anatomy/science (e.g. What Happens If You Hold Your Breath)
    "night-file",    # Dark mystery / true crime (e.g. D.B. Cooper Hijacking)
    "inside-out",    # 2D x-ray explainer (e.g. What If You Swallow Gum)
    "paper-atlas",   # Cut paper history (e.g. The Great Fire of London)
    "stick-story"    # Survival steps & life hacks (e.g. What If The Power Went Out)
]

def run_cmd(cmd, cwd=None, env=None):
    """Helper to run command with properly configured PATH."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    bin_str = str(BIN_DIR)
    if bin_str not in merged_env.get("PATH", ""):
        merged_env["PATH"] = f"{bin_str};{merged_env.get('PATH', '')}" if os.name == 'nt' else f"{bin_str}:{merged_env.get('PATH', '')}"

    res = subprocess.run(cmd, cwd=cwd, env=merged_env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error executing {' '.join(cmd)}:")
        print(res.stderr)
        raise RuntimeError(f"Command failed with code {res.returncode}")
    return res.stdout

def get_next_style(history_file):
    """Rotates through styles based on previous history."""
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
            used_styles = [h.get("style") for h in history if h.get("style")]
            if used_styles:
                last_style = used_styles[-1]
                idx = (ROTATION_STYLES.index(last_style) + 1) % len(ROTATION_STYLES) if last_style in ROTATION_STYLES else 0
                return ROTATION_STYLES[idx]
        except Exception:
            pass
    return ROTATION_STYLES[0]

def build_short(topic=None, style=None, upload=False, privacy="public", draft=False):
    print("\n" + "="*70)
    print("   CURIO CUT - AUTONOMOUS VIRAL SHORTS GENERATOR   ")
    print("="*70 + "\n")

    history_file = WORKSPACE / "history.json"
    if not style or style == "auto":
        style = get_next_style(history_file)

    template_dir = SKILL_DIR / "styles" / style / "example"
    if not template_dir.exists():
        raise FileNotFoundError(f"Style template not found: {template_dir}")

    # Determine script
    if topic:
        print(f"[1/5] Writing viral script for topic: {topic}...")
        from generate_script import generate_script
        script_data = generate_script(topic)
    else:
        print(f"[1/5] Loading master synchronized script for style: '{style}'...")
        script_path = template_dir / "script.json"
        script_data = json.loads(script_path.read_text(encoding="utf-8"))

    title = script_data.get("title", "Untitled Short")
    print(f"Title: {title}")
    print(f"Style: {style}")

    notify_engine(
        title="Short Generation Started",
        description=f"CurioCut engine started generating: **{title}**",
        fields=[
            {"name": "Style", "value": style, "inline": True},
            {"name": "Upload Target", "value": "YouTube + Instagram" if upload else "Local Only", "inline": True}
        ]
    )

    # 2. Setup Project Folder
    slug = "".join(c if c.isalnum() else "_" for c in title.lower())[:30].strip("_")
    project_dir = WORKSPACE / "projects" / slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
        
    print(f"[2/5] Initializing '{style}' scene in {project_dir.name}...")
    shutil.copytree(template_dir, project_dir)
    
    # Save script.json (preserving perfectly matched line cues)
    (project_dir / "script.json").write_text(json.dumps(script_data, indent=2), encoding="utf-8")
    
    # Clean previous audio/renders
    for f in ["data/narration.wav", "data/mix.wav"]:
        p = project_dir / f
        if p.exists(): p.unlink()
        
    (project_dir / "renders").mkdir(exist_ok=True)
    (project_dir / "review").mkdir(exist_ok=True)

    # 3. Audio & Voiceover (Kokoro + Whisper + Mix)
    print("[3/5] Generating voiceover (Kokoro TTS) & subtitle timings (Whisper)...")
    run_cmd([PYTHON_EXE, str(SKILL_DIR / "scripts" / "voice.py"), "."], cwd=project_dir)
    run_cmd([PYTHON_EXE, str(SKILL_DIR / "scripts" / "words.py"), "."], cwd=project_dir)

    print("Synthesizing procedural sound effects and music bed...")
    run_cmd([NODE_EXE, "tools/capture.mjs", "cues"], cwd=project_dir)
    run_cmd([PYTHON_EXE, "tools/mix.py", "."], cwd=project_dir)

    # 4. Render (Headless Chrome + FFmpeg)
    output_mp4 = project_dir / "renders" / f"{slug}.mp4"
    print(f"[4/5] Rendering animation (1080x1920) in headless Chrome...")
    capture_args = [NODE_EXE, "tools/capture.mjs", "video", str(output_mp4)]
    if draft:
        capture_args.append("--draft")
        
    run_cmd(capture_args, cwd=project_dir)
    print(f"Render complete: {output_mp4.resolve()} ({output_mp4.stat().st_size / (1024*1024):.2f} MB)")

    # Record history
    try:
        history = json.loads(history_file.read_text(encoding="utf-8")) if history_file.exists() else []
        history.append({"title": title, "style": style})
        history_file.write_text(json.dumps(history[-50:], indent=2), encoding="utf-8")
    except Exception:
        pass

    # 5. Multi-Platform Auto Upload (YouTube & Instagram)
    if upload:
        print("[5/5] Multi-Platform Publishing...")
        desc = f"{title}. Watch daily animated stories on CurioCut! #shorts #viral #curiosity"

        # 5a. YouTube Shorts
        yt_file = WORKSPACE / "youtube_token.json"
        if not yt_file.exists() and os.environ.get("YOUTUBE_TOKEN_JSON"):
            yt_file.write_text(os.environ["YOUTUBE_TOKEN_JSON"].strip(), encoding="utf-8")

        if yt_file.exists():
            try:
                print("\n  >> Uploading to YouTube Shorts...")
                from youtube_uploader import upload_short
                v_id, v_url = upload_short(str(output_mp4), title=title, description=desc, privacy_status=privacy)
                print(f"  Live on YouTube: {v_url}")
                file_size_mb = output_mp4.stat().st_size / (1024 * 1024)
                notify_youtube_post(
                    title=title,
                    video_url=v_url,
                    video_id=v_id,
                    size_mb=file_size_mb,
                    privacy=privacy,
                    style=style
                )
            except Exception as e:
                print(f"  YouTube upload error: {e}")
                notify_youtube_error(str(e))
        else:
            print("  Skipping YouTube (youtube_token.json not found).")

        # 5b. Instagram Reels
        ig_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        ig_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
        if ig_token and ig_id and not ig_token.startswith("placeholder"):
            try:
                print("\n  >> Uploading to Instagram Reels...")
                from instagram_uploader import upload_reel
                ig_media_id, ig_permalink = upload_reel(str(output_mp4), caption=desc)
                print(f"  Live on Instagram: {ig_permalink}")
                notify_instagram_post(caption=desc, permalink=ig_permalink, media_id=ig_media_id)
            except Exception as e:
                print(f"  Instagram Reels upload error: {e}")
                notify_instagram_error(str(e))
        else:
            print("  Skipping Instagram (INSTAGRAM_ACCESS_TOKEN not configured or placeholder).")
    else:
        print(f"[5/5] Video ready! (Pass --upload to publish to YouTube & Instagram).")

    print("\n" + "="*70)
    print("ALL DONE! Short ready to watch.")
    print(f"Path: {output_mp4.resolve()}")
    print("="*70 + "\n")
    return output_mp4

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CurioCut Autonomous Video Pipeline")
    parser.add_argument("--topic", help="Topic for the video", default=None)
    parser.add_argument("--style", help="Video style (tall-tale, deep-dive, night-file, inside-out, paper-atlas, stick-story)", default="auto")
    parser.add_argument("--upload", action="store_true", help="Upload directly to YouTube Shorts & Instagram Reels")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--draft", action="store_true", help="Fast draft rendering mode")
    
    args = parser.parse_args()
    build_short(topic=args.topic, style=args.style, upload=args.upload, privacy=args.privacy, draft=args.draft)
