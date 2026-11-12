"""
End-to-end Town-Rule Episode Pipeline:
1. Ensure 2D face decals exist
2. Generate fresh AI story + 3D Director JSON (or reuse --episode)
3. Synthesize Kokoro narration + Whisper word timestamps + SFX/music mix
4. Build ASS 1-word highlighted captions
5. Render 3D scene in headless Blender 4.3 EEVEE Next
6. Mux video + audio + burn captions via FFmpeg -> final MP4
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from town_rule.face_atlas import ensure_all_faces
from town_rule.story_director import generate_episode
from town_rule.audio_engine import build_episode_audio
from town_rule.captions import build_ass_subtitles


def find_blender() -> str:
    env_b = os.environ.get("BLENDER_EXE", "").strip()
    if env_b and Path(env_b).exists():
        return env_b
    which_b = shutil.which("blender")
    if which_b:
        return which_b
    candidates = [
        Path.home() / ".faceless-shorts" / "blender" / "blender-4.3.2-windows-x64" / "blender.exe",
        Path("/opt/blender/blender"),
        Path("/usr/local/bin/blender"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise FileNotFoundError("Blender executable not found. Set BLENDER_EXE or install Blender 4.3.")


def find_ffmpeg() -> str:
    which_ff = shutil.which("ffmpeg")
    if which_ff:
        return which_ff
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default="", help="Optional theme hint for AI story generator")
    ap.add_argument("--episode", default="", help="Optional existing episode.json to render")
    ap.add_argument("--out", default="", help="Final output MP4 path")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--draft", action="store_true", help="Fast 540x960 preview")
    ap.add_argument("--reuse-audio", action="store_true", help="Reuse existing episode_timed.json, mix.wav, captions.ass")
    ap.add_argument("--max-frames", type=int, default=0, help="Optional frame cap for quick QA")
    ap.add_argument("--skip-render", action="store_true", help="Only generate story/audio/subs")
    args = ap.parse_args()

    work_dir = Path(__file__).resolve().parent / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    renders_dir = Path(__file__).resolve().parent / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)

    print("[1/6] Ensuring 2D Roblox face decal atlas...")
    faces_dir = ensure_all_faces()

    timed_path = work_dir / "episode_timed.json"
    mix_path = work_dir / "mix.wav"
    ass_path = work_dir / "captions.ass"

    if args.reuse_audio and timed_path.exists() and mix_path.exists() and ass_path.exists():
        print("[2-4/6] Reusing existing timed episode, audio mix, and captions...")
    else:
        if args.episode and Path(args.episode).exists():
            print(f"[2/6] Loading existing episode: {args.episode}")
            ep = json.loads(Path(args.episode).read_text(encoding="utf-8"))
        else:
            print("[2/6] Generating fresh AI story + 3D Director JSON...")
            ep = generate_episode(args.theme)
            (work_dir / "episode.json").write_text(json.dumps(ep, indent=2), encoding="utf-8")

        print("[3/6] Synthesizing narration, word timestamps & SFX/music mix...")
        timed_ep, words, mix_path = build_episode_audio(ep, work_dir)
        print(f"      Total duration: {timed_ep['total_duration']:.2f}s | Words: {len(words)}")

        print("[4/6] Building 1-word highlighted ASS captions...")
        ass_path = build_ass_subtitles(words, timed_ep, ass_path)

    if args.skip_render:
        print("Skipping Blender render (--skip-render).")
        return

    blender_exe = find_blender()
    raw_video = work_dir / "raw_video.mp4"
    render_script = Path(__file__).resolve().parent / "blender_render.py"

    print(f"[5/6] Rendering 3D EEVEE Next scene via {blender_exe}...")
    cmd = [
        blender_exe,
        "--background",
        "--python", str(render_script),
        "--",
        "--episode", str(work_dir / "episode_timed.json"),
        "--out", str(raw_video),
        "--fps", str(args.fps),
        "--faces-dir", str(faces_dir),
    ]
    if args.draft:
        cmd.append("--draft")
    if args.max_frames > 0:
        cmd.extend(["--max-frames", str(args.max_frames)])
    subprocess.run(cmd, check=True)

    if not raw_video.exists():
        raise FileNotFoundError(f"Blender did not produce {raw_video}")

    final_out = Path(args.out) if args.out else renders_dir / ("draft_episode.mp4" if args.draft else "final_episode.mp4")
    final_out.parent.mkdir(parents=True, exist_ok=True)

    print("[6/6] Muxing audio + burning captions with FFmpeg...")
    ffmpeg_exe = find_ffmpeg()
    # Escape colon/backslashes for FFmpeg ass= filter on Windows
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    ff_cmd = [
        ffmpeg_exe, "-y",
        "-i", str(raw_video),
        "-i", str(mix_path),
        "-vf", f"ass='{ass_escaped}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_out),
    ]
    subprocess.run(ff_cmd, check=True)
    print(f"\nDONE! Final video saved to: {final_out}")


if __name__ == "__main__":
    main()

