# Build, render, and upload daily short
import os
import sys
import json
import shutil
import argparse
import re
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    from discord_notifier import (
        notify_engine, notify_alert, notify_error,
        notify_youtube_post, notify_youtube_error,
        notify_instagram_post, notify_instagram_error,
        update_live_progress
    )
except ImportError:
    def notify_engine(*a, **kw): pass
    def notify_alert(*a, **kw): pass
    def notify_error(*a, **kw): pass
    def notify_youtube_post(*a, **kw): pass
    def notify_youtube_error(*a, **kw): pass
    def notify_instagram_post(*a, **kw): pass
    def notify_instagram_error(*a, **kw): pass
    def update_live_progress(*a, **kw): pass

WORKSPACE = Path(__file__).resolve().parent
SKILL_DIR = WORKSPACE / "faceless-shorts-skill" / "faceless-shorts"
FACELSS_HOME = Path.home() / ".faceless-shorts"
BIN_DIR = FACELSS_HOME / "bin"
VENV_PYTHON = FACELSS_HOME / "venv" / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

node_candidate = BIN_DIR / ("node.exe" if os.name == 'nt' else "node")
NODE_EXE = str(node_candidate) if node_candidate.exists() else "node"

CLASSIC_STYLES = [
    "tall-tale",     # 3D con/loophole story (e.g. The Girl Who Was Mailed to Grandma)
    "deep-dive",     # Zack D. Films 3D anatomy/science (e.g. What Happens If You Hold Your Breath)
    "night-file",    # Dark mystery / true crime (e.g. D.B. Cooper Hijacking)
    "inside-out",    # 2D x-ray explainer (e.g. What If You Swallow Gum)
    "paper-atlas",   # Cut paper history (e.g. The Great Fire of London)
    "stick-story"    # Survival steps & life hacks (e.g. What If The Power Went Out)
]
ROTATION_STYLES = CLASSIC_STYLES

def run_cmd(cmd, cwd=None, env=None, on_line=None, timeout=600):
    """Helper to run command with properly configured PATH and stream output live with unbreakable timeout guard."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    bin_str = str(BIN_DIR)
    if bin_str not in merged_env.get("PATH", ""):
        merged_env["PATH"] = f"{bin_str};{merged_env.get('PATH', '')}" if os.name == 'nt' else f"{bin_str}:{merged_env.get('PATH', '')}"

    start_time = time.time()
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    output_lines = []
    if process.stdout:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line, end='', flush=True)
            output_lines.append(line)
            if on_line:
                try:
                    on_line(line)
                except Exception:
                    pass
            if time.time() - start_time > timeout:
                process.kill()
                raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(str(c) for c in cmd)}")
        process.stdout.close()

    try:
        remaining_timeout = max(1.0, timeout - (time.time() - start_time))
        return_code = process.wait(timeout=remaining_timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(str(c) for c in cmd)}")

    if return_code != 0:
        raise RuntimeError(f"Command failed with code {return_code}: {' '.join(str(c) for c in cmd)}")
    return ''.join(output_lines)

def get_next_style(history_file):
    """Rotates strictly through the 6 classic styles with time-based anti-repeat guarantee."""
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
            used_styles = [h.get("style") for h in history if h.get("style") in CLASSIC_STYLES]
            if used_styles:
                last_style = used_styles[-1]
                idx = (CLASSIC_STYLES.index(last_style) + 1) % len(CLASSIC_STYLES)
                return CLASSIC_STYLES[idx]
        except Exception:
            pass
    # Resilient fallback: rotates based on day of year and UTC hour so fresh cloud runners never repeat
    now = datetime.now(timezone.utc)
    slot_offset = 0 if now.hour < 10 else (1 if now.hour < 15 else 2)
    idx = (now.timetuple().tm_yday * 3 + slot_offset) % len(CLASSIC_STYLES)
    return CLASSIC_STYLES[idx]

def build_short(topic=None, style=None, upload=False, privacy="public", draft=False):
    print("\n" + "="*70)
    print("   CURIO CUT - AUTONOMOUS VIRAL SHORTS GENERATOR   ")
    print("="*70 + "\n")

    history_file = WORKSPACE / "history.json"
    if not style or style in ["auto", "classic"]:
        style = get_next_style(history_file)

    template_dir = SKILL_DIR / "styles" / style / "example"
    if not template_dir.exists():
        raise FileNotFoundError(f"Style template not found: {template_dir}")

    # Determine script
    from generate_script import generate_script
    if style in ["claude-desk", "dev-studio"]:
        from tech_harvester import get_next_tech_story
        from generate_tech_dialogue import generate_dialogue_script
        if topic and topic != "auto":
            story_data = {"title": topic, "premise": topic, "cta_keyword": "TOOL"}
        else:
            harvest_mode = "skill" if style == "claude-desk" else "tech"
            print(f"[1/5] Harvesting targeted {harvest_mode.upper()} intel for {style}...")
            story_data = get_next_tech_story(force_mode=harvest_mode)
        print(f"[1/5] Generating 2-character dialogue script for '{story_data.get('title')}' ({style})...")
        try:
            script_data = generate_dialogue_script(story_data, style=style)
        except Exception as e:
            print(f"Notice: Dynamic tech dialogue exception: {e}. Using synchronized style script.")
            script_data = None
    elif topic and topic != "auto":
        print(f"[1/5] Writing viral script for topic: {topic}...")
        script_data = generate_script(topic)
    else:
        print(f"[1/5] Dynamically generating fresh viral script for style: '{style}'...")
        try:
            script_data = generate_script()
        except Exception as e:
            print(f"Notice: Dynamic script generation exception: {e}. Using synchronized style script.")
            script_data = None
            
        if not script_data:
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
    update_live_progress(
        step_title="Script & Story Initialized",
        percent=15,
        details=f"Topic: **{title}**\nStyle: `{style}` • Target: {'YouTube + Instagram' if upload else 'Local Only'}"
    )

    # 2. Setup Project Folder
    slug = "".join(c if c.isalnum() else "_" for c in title.lower())[:30].strip("_")
    project_dir = WORKSPACE / "projects" / slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
        
    print(f"[2/5] Initializing '{style}' scene in {project_dir.name}...")
    shutil.copytree(template_dir, project_dir)
    update_live_progress(
        step_title="Setting Up 3D Stage Assets",
        percent=25,
        details=f"Loading WebGL scene template for `{style}`..."
    )
    
    # Save script.json (preserving perfectly matched line cues)
    (project_dir / "script.json").write_text(json.dumps(script_data, indent=2), encoding="utf-8")
    
    # Clean previous audio/renders
    for f in ["data/narration.wav", "data/mix.wav"]:
        p = project_dir / f
        if p.exists(): p.unlink()
        
    (project_dir / "renders").mkdir(exist_ok=True)
    (project_dir / "review").mkdir(exist_ok=True)

    # 3. Audio & Voiceover (Kokoro + Whisper + Mix)
    update_live_progress(
        step_title="Synthesizing Dialogue & Narration",
        percent=35,
        details="Generating neural speech with Kokoro TTS..."
    )
    if style in ["claude-desk", "dev-studio"]:
        print("[3/5] Generating dual-character voiceover (Guide + Skeptic/Mascot)...")
        from dual_voice import synthesize_dialogue
        synthesize_dialogue(str(project_dir))
    else:
        print("[3/5] Generating voiceover (Kokoro TTS)...")
        run_cmd([PYTHON_EXE, str(SKILL_DIR / "scripts" / "voice.py"), "."], cwd=project_dir)

    update_live_progress(
        step_title="Whisper Subtitle Alignment",
        percent=45,
        details="Computing word-level phonetic timestamps & sound cues..."
    )
    print("Generating subtitle timings with Whisper...")
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

    def on_render_frame(line):
        m = re.search(r"\[Render\]\s+Frame\s+(\d+)/(\d+)\s+\((\d+)%\)", line)
        if m:
            cur = int(m.group(1))
            tot = int(m.group(2))
            pct = int(m.group(3))
            overall = 50 + int(pct * 0.38) # scales 50% to 88%
            update_live_progress(
                step_title="Rendering 3D Scene in Chrome",
                percent=overall,
                details=f"Frame {cur}/{tot} ({pct}%) • Headless WebGL @ 1080x1920"
            )

    run_cmd(capture_args, cwd=project_dir, on_line=on_render_frame)
    file_size_mb = output_mp4.stat().st_size / (1024 * 1024)
    print(f"Render complete: {output_mp4.resolve()} ({file_size_mb:.2f} MB)")

    notify_engine(
        title="Video Render Complete",
        description=f"**{title}** is rendered ({file_size_mb:.1f} MB). Ready to upload.",
        fields=[
            {"name": "Style", "value": style, "inline": True}
        ],
        color=0x3B82F6
    )

    # Record history
    try:
        history = json.loads(history_file.read_text(encoding="utf-8")) if history_file.exists() else []
        history.append({
            "title": title,
            "style": style,
            "category": script_data.get("category", "breaking_tech"),
            "tool_name": script_data.get("tool_name", "")
        })
        history_file.write_text(json.dumps(history[-50:], indent=2), encoding="utf-8")
    except Exception:
        pass

    # 5. Multi-Platform Auto Upload (YouTube & Instagram)
    v_url = None
    ig_permalink = None
    if upload:
        print("[5/5] Multi-Platform Publishing...")
        update_live_progress(
            step_title="Publishing to Platforms",
            percent=90,
            details=f"Publishing {file_size_mb:.1f} MB vertical short to YouTube Shorts & Instagram Reels..."
        )
        if style in ["claude-desk", "dev-studio"]:
            cta = script_data.get("cta_keyword", "TOOL")
            desc = (
                f"💬 Follow & comment '{cta}' for the direct link in your DMs!\n\n"
                f"{title}\n\n"
                f"Daily underground AI breakthroughs & open-source developer exploits.\n\n"
                f"#ai #developer #claude #anthropic #tech #github #coding #automation #curiocut #programming #software #opensource #aitools"
            )
        else:
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

        # 5b. Instagram Reels (Paused during Meta review)
        pause_ig = os.environ.get("PAUSE_INSTAGRAM", "false").lower() in ("true", "1", "yes")
        ig_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        ig_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
        if pause_ig:
            print("  [!] Instagram Reels upload temporarily paused while Meta verification appeal is in progress.")
        elif ig_token and ig_id and not ig_token.startswith("placeholder"):
            try:
                print("\n  >> Uploading to Instagram Reels...")
                from instagram_uploader import upload_reel
                ig_media_id, ig_permalink = upload_reel(str(output_mp4), caption=desc)
                print(f"  Live on Instagram: {ig_permalink}")
                notify_instagram_post(
                    caption=desc,
                    permalink=ig_permalink,
                    media_id=ig_media_id,
                    keyword=script_data.get("cta_keyword"),
                    resource_url=script_data.get("resource_url"),
                    title=title
                )

                # Record reel mapping for dynamic Comment-to-DM responder
                reels_map_file = WORKSPACE / "published_reels.json"
                try:
                    reels_map = json.loads(reels_map_file.read_text(encoding="utf-8")) if reels_map_file.exists() else {}
                    reels_map[str(ig_media_id)] = {
                        "title": title,
                        "cta_keyword": script_data.get("cta_keyword", "TOOL"),
                        "resource_url": script_data.get("resource_url", ""),
                        "permalink": ig_permalink
                    }
                    reels_map_file.write_text(json.dumps(reels_map, indent=2), encoding="utf-8")
                except Exception:
                    pass
            except Exception as e:
                print(f"  Instagram Reels upload error: {e}")
                notify_instagram_error(str(e))
        else:
            print("  Skipping Instagram (INSTAGRAM_ACCESS_TOKEN not configured or placeholder).")
    else:
        print(f"[5/5] Video ready! (Pass --upload to publish to YouTube & Instagram).")

    links = {}
    if v_url:
        links["YouTube"] = f"[Watch Short]({v_url})"
    if ig_permalink:
        links["Instagram"] = f"[Watch Reel]({ig_permalink})"

    update_live_progress(
        step_title="Video Pipeline Complete",
        percent=100,
        details=f"**{title}** is rendered and live!\nFile size: {file_size_mb:.1f} MB",
        is_done=True,
        links=links if links else None
    )

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
    try:
        build_short(topic=args.topic, style=args.style, upload=args.upload, privacy=args.privacy, draft=args.draft)
    except Exception as e:
        err_msg = str(e)
        print(f"\n[FATAL ERROR] Video generation failed: {err_msg}")
        update_live_progress(
            step_title="Generation Error",
            percent=0,
            details=f"Pipeline aborted:\n`{err_msg[:400]}`",
            is_error=True
        )
        notify_engine(
            title="Video Pipeline Aborted",
            description=f"Error encountered during short generation:\n```{err_msg[:800]}```",
            color=0xEF4444
        )
        raise
