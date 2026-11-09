"""Master Autonomous Short Generator.
Orchestrates the entire pipeline end-to-end:
1. Topic / Script Generation (Groq / Llama 3.3 70B or story bank)
2. Kokoro AI Voiceover (voice.py)
3. Whisper Millisecond Caption Timing (words.py)
4. Procedural Sound FX & Music Synthesis (mix.py)
5. Headless Chrome DevTools 3D Capture & FFmpeg Video Assembly
6. Automated YouTube Shorts Publishing
"""
import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
SKILL_DIR = WORKSPACE / "faceless-shorts-skill" / "faceless-shorts"
FACELSS_HOME = Path.home() / ".faceless-shorts"
BIN_DIR = FACELSS_HOME / "bin"
VENV_PYTHON = FACELSS_HOME / "venv" / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")

def run_cmd(cmd, cwd=None, env=None):
    """Helper to run command with properly configured PATH."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    # Prepend bin directory to PATH
    bin_str = str(BIN_DIR)
    if bin_str not in merged_env.get("PATH", ""):
        merged_env["PATH"] = f"{bin_str};{merged_env.get('PATH', '')}" if os.name == 'nt' else f"{bin_str}:{merged_env.get('PATH', '')}"

    res = subprocess.run(cmd, cwd=cwd, env=merged_env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error executing {' '.join(cmd)}:")
        print(res.stderr)
        raise RuntimeError(f"Command failed with code {res.returncode}")
    return res.stdout

def build_short(topic=None, style="tall-tale", upload=False, privacy="public", draft=False):
    print("\n" + "="*70)
    print("   CURIO CUT - AUTONOMOUS 3D SHORTS GENERATOR   ")
    print("="*70 + "\n")

    # 1. Generate Script
    print("[1/5] Writing viral script...")
    from generate_script import generate_script
    script_data = generate_script(topic)
    title = script_data.get("title", "Untitled Short")
    print(f"Title: {title}")

    # 2. Setup Project Folder from Style Template
    slug = "".join(c if c.isalnum() else "_" for c in title.lower())[:30].strip("_")
    project_dir = WORKSPACE / "projects" / slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
        
    template_dir = SKILL_DIR / "styles" / style / "example"
    print(f"[2/5] Initializing '{style}' scene in {project_dir.name}...")
    shutil.copytree(template_dir, project_dir)
    
    # Write custom script.json
    (project_dir / "script.json").write_text(json.dumps(script_data, indent=2))
    
    # Clean previous audio/renders
    for f in ["data/narration.wav", "data/mix.wav"]:
        p = project_dir / f
        if p.exists(): p.unlink()
        
    (project_dir / "renders").mkdir(exist_ok=True)
    (project_dir / "review").mkdir(exist_ok=True)

    # 3. Audio & Voiceover (Kokoro + Whisper + Mix)
    print("[3/5] Generating voiceover (Kokoro TTS) & subtitle timings (Whisper)...")
    run_cmd([str(VENV_PYTHON), str(SKILL_DIR / "scripts" / "voice.py"), "."], cwd=project_dir)
    run_cmd([str(VENV_PYTHON), str(SKILL_DIR / "scripts" / "words.py"), "."], cwd=project_dir)

    print("Synthesizing procedural sound effects and music bed...")
    node_exe = str(BIN_DIR / "node.exe") if os.name == 'nt' else "node"
    run_cmd([node_exe, "tools/capture.mjs", "cues"], cwd=project_dir)
    run_cmd([str(VENV_PYTHON), "tools/mix.py", "."], cwd=project_dir)

    # 4. 3D Render (Headless Chrome + FFmpeg)
    output_mp4 = project_dir / "renders" / f"{slug}.mp4"
    print(f"[4/5] Rendering 3D animation (1080x1920) in headless Chrome...")
    capture_args = [node_exe, "tools/capture.mjs", "video", str(output_mp4)]
    if draft:
        capture_args.append("--draft")
        
    run_cmd(capture_args, cwd=project_dir)
    print(f"Render complete: {output_mp4.resolve()} ({output_mp4.stat().st_size / (1024*1024):.2f} MB)")

    # 5. Multi-Platform Auto Upload (YouTube & Instagram)
    if upload:
        print("[5/5] Multi-Platform Publishing...")
        desc = f"{title}. Watch daily animated stories on CurioCut! #shorts #viral #curiosity"

        # 5a. YouTube Shorts
        if (WORKSPACE / "youtube_token.json").exists():
            try:
                print("\n  >> Uploading to YouTube Shorts...")
                from youtube_uploader import upload_short
                v_id, v_url = upload_short(str(output_mp4), title=title, description=desc, privacy_status=privacy)
                print(f"  Live on YouTube: {v_url}")
            except Exception as e:
                print(f"  YouTube upload error: {e}")
        else:
            print("  Skipping YouTube (youtube_token.json not found).")

        # 5b. Instagram Reels
        ig_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        ig_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
        if ig_token and ig_id:
            try:
                print("\n  >> Uploading to Instagram Reels...")
                from instagram_uploader import upload_reel
                ig_media_id, ig_permalink = upload_reel(str(output_mp4), caption=desc)
                print(f"  Live on Instagram: {ig_permalink}")
            except Exception as e:
                print(f"  Instagram Reels upload error: {e}")
        else:
            print("  Skipping Instagram (INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_ACCOUNT_ID not configured).")
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
    parser.add_argument("--style", help="Video style (tall-tale, deep-dive, inside-out)", default="tall-tale")
    parser.add_argument("--upload", action="store_true", help="Upload directly to YouTube Shorts & Instagram Reels")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--draft", action="store_true", help="Fast draft rendering mode")
    
    args = parser.parse_args()
    build_short(topic=args.topic, style=args.style, upload=args.upload, privacy=args.privacy, draft=args.draft)

