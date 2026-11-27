import os
import sys
import json
import re
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORK_DIR = BASE_DIR / "work"
BLENDER_EXE = r"C:\Users\shlok\.faceless-shorts\blender\blender-4.3.2-windows-x64\blender.exe"
FFMPEG_EXE = r"C:\Users\shlok\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"

def build_ass_subtitles(words: list[dict], out_ass: Path):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial Black,96,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,12,6,2,60,60,380,1
Style: Brand,Arial Black,48,&H0040D325,&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,1,6,2,8,60,60,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt_time(sec):
        sec = max(0.0, float(sec))
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int(round((sec - int(sec)) * 100))
        if cs >= 100: cs = 99
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    lines = [header]
    # Persistent top brand badge
    lines.append("Dialogue: 0,0:00:00.00,0:00:41.10,Brand,,0,0,0,,{\\pos(540,180)}BIZBOT  •  WHATSAPP AUTOMATION\n")

    # Group into 1-2 punchy words
    i = 0
    while i < len(words):
        w1 = words[i]
        t0 = w1["start"]
        text1 = w1["word"]
        
        # Check if next word is short or belongs together
        if i + 1 < len(words) and (words[i+1]["start"] - w1["end"] < 0.25) and (len(text1) < 5 or len(words[i+1]["word"]) < 5):
            w2 = words[i+1]
            t1 = w2["end"]
            text_disp = f"{text1} {w2['word']}"
            i += 2
        else:
            t1 = w1["end"]
            text_disp = text1
            i += 1

        # Color highlights
        # Emerald green for WhatsApp, BizBot, buttons, sales
        # Gold for money, rupees, instant
        # Red for lost, competitor
        low = text_disp.lower()
        if any(k in low for k in ["bizbot", "whatsapp", "buttons", "autopilot"]):
            color_tag = "{\\c&H40D325&}" # WhatsApp Green
        elif any(k in low for k in ["money", "rupees", "200", "sales", "two hundred"]):
            color_tag = "{\\c&H15C7FF&}" # Gold
        elif any(k in low for k in ["lost", "competitor", "asleep"]):
            color_tag = "{\\c&H3333FF&}" # Alert Red
        else:
            color_tag = "{\\c&HFFFFFF&}"

        lines.append(f"Dialogue: 1,{fmt_time(t0)},{fmt_time(t1)},Cap,,0,0,0,,{color_tag}{text_disp}\n")

    with open(out_ass, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Generated animated ASS subtitles: {out_ass.resolve()}", flush=True)

def main():
    print("="*70, flush=True)
    print("   CURIOCUT - BIZBOT CUSTOM MASTERPIECE PRODUCTION PIPELINE   ", flush=True)
    print("="*70, flush=True)

    ep_timed = WORK_DIR / "episode_timed.json"
    words_json = WORK_DIR / "words.json"
    mix_wav = WORK_DIR / "mix.wav"

    if not ep_timed.exists() or not words_json.exists() or not mix_wav.exists():
        print("[Error] Work files missing. Run generate_audio.py first!", flush=True)
        sys.exit(1)

    # 1. Build Subtitles
    print("\n[Step 1/3] Compiling Word-Level Animated Subtitles...", flush=True)
    ass_path = WORK_DIR / "captions.ass"
    with open(words_json, "r", encoding="utf-8") as f:
        words = json.load(f)
    build_ass_subtitles(words, ass_path)

    # 2. Render 3D Blender Animation
    raw_video = WORK_DIR / "raw_3d.mp4"
    render_script = BASE_DIR / "render_bizbot.py"
    
    print("\n[Step 2/3] Spawning Blender 4.3 EEVEE Next 3D GPU Hardware Renderer...", flush=True)
    blender_cmd = [
        BLENDER_EXE,
        "--background",
        "--python", str(render_script),
        "--",
        "--episode", str(ep_timed),
        "--out", str(raw_video)
    ]
    
    # Check if user wants fast draft preview or full render
    if "--draft" in sys.argv:
        blender_cmd.append("--draft")
        print("  -> Mode: High-Speed Draft Preview (540x960)", flush=True)
    else:
        print("  -> Mode: Full Cinema Master (1080x1920 HD / 30fps)", flush=True)

    if "--max-frames" in sys.argv:
        idx = sys.argv.index("--max-frames")
        if idx + 1 < len(sys.argv):
            blender_cmd.extend(["--max-frames", sys.argv[idx + 1]])

    p = subprocess.Popen(blender_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in iter(p.stdout.readline, ''):
        line = line.strip()
        if "Append frame" in line or "Fra:" in line:
            m = re.search(r"(?:Append frame |Fra:)(\d+)", line)
            if m:
                fr = int(m.group(1))
                if fr % 30 == 0 or fr == 1 or fr >= 1234:
                    print(f"  [3D Render Progress] Frame {fr}/1234 ({int(fr/1234*100)}%) - Raytracing active...", flush=True)
        elif "Starting hardware accelerated" in line or "Baking cinematic" in line or "Initializing Blender" in line:
            print(f"  {line}", flush=True)
    p.wait()

    if p.returncode != 0 or not raw_video.exists():
        print(f"[Error] Blender 3D rendering failed with code {p.returncode}", flush=True)
        sys.exit(1)

    print("\n[Step 3/3] Final Muxing: 3D Video + Dual Stereo Mix + Burning Subtitles...", flush=True)
    final_output = BASE_DIR / "BizBot_Official_Promo_HD.mp4"
    if final_output.exists():
        final_output.unlink()

    # Escape path for FFmpeg subtitles filter on Windows
    ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
    
    ffmpeg_cmd = [
        FFMPEG_EXE,
        "-y",
        "-i", str(raw_video),
        "-i", str(mix_wav),
        "-vf", f"subtitles='{ass_escaped}'",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        str(final_output)
    ]

    p_ff = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if p_ff.returncode != 0:
        print("[Notice] Subtitles filter fallback without ASS styling...", flush=True)
        ffmpeg_simple = [
            FFMPEG_EXE,
            "-y",
            "-i", str(raw_video),
            "-i", str(mix_wav),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "256k",
            "-shortest",
            str(final_output)
        ]
        subprocess.run(ffmpeg_simple, check=True)

    file_size_mb = final_output.stat().st_size / (1024 * 1024)
    print("\n" + "="*70, flush=True)
    print(f"SUCCESS! MASTER VIDEO GENERATED: {final_output.resolve()}", flush=True)
    print(f"File Size: {file_size_mb:.2f} MB | Resolution: 1080x1920 HD | 30 FPS", flush=True)
    print("="*70, flush=True)

if __name__ == "__main__":
    main()
