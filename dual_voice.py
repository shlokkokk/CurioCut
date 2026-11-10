"""Multi-Speaker Synthesis Engine for CurioCut 2-Character Shorts.
Alternates Kokoro TTS voices between Guide (calm human male) and Skeptic (soft expressive female).
Outputs data/narration.wav + data/lines.json with exact millisecond timings and speaker tags.
"""
import os
import sys
import json
import re
import urllib.request
from pathlib import Path
import numpy as np
from scipy.io import wavfile

HOME = Path(os.environ.get('FACELESS_HOME', Path.home() / '.faceless-shorts'))
KDIR = HOME / 'kokoro'
FILES = {
    'kokoro-v1.0.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
    'voices-v1.0.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin',
}

# Curated High-Retention Voice Pairings:
# Guide: am_fenrir (Deep, masculine, chest-resonant US male. Sounds like a confident tech founder, 0% robotic)
# Skeptic: af_bella (Expressive, bright, curious US female. Naturally raises pitch on questions with real emotion)
VOICE_PAIRS = {
    "default": {
        "guide": "am_fenrir",    # Deep, masculine, resonant male
        "skeptic": "af_bella"     # Expressive, lively, questioning female
    },
    "deep_duo": {
        "guide": "am_onyx",       # Deep, commanding male
        "skeptic": "af_sarah"     # Conversational, sharp female
    },
    "lively": {
        "guide": "am_adam",       # Crisp, fast tech male
        "skeptic": "af_bella"     # Bright female
    }
}
SR = 24000

def ensure_models():
    KDIR.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        p = KDIR / name
        if p.exists() and p.stat().st_size > 1_000_000:
            continue
        print(f"  Downloading Kokoro speech model {name} (once)...", flush=True)
        tmp = p.with_suffix('.part')
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(p)

def trim_silence(x, thr=0.008):
    """Cuts leading and trailing silence so line timings are razor-sharp."""
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(0.01 * SR))
    b = min(len(x), idx[-1] + int(0.03 * SR))
    return x[a:b]

def normalize_tech_phonetics(text):
    """Normalizes tech acronyms and numbers to 100% natural conversational human speech."""
    s = text
    # Currency and numbers
    s = re.sub(r'\$([0-9]+)\s*B(?:illion)?\b', r'\1 billion dollars', s, flags=re.IGNORECASE)
    s = re.sub(r'\$([0-9]+)\s*M(?:illion)?\b', r'\1 million dollars', s, flags=re.IGNORECASE)
    s = re.sub(r'\$([0-9]+)\s*K\b', r'\1 thousand dollars', s, flags=re.IGNORECASE)
    s = re.sub(r'\$([0-9]+)', r'\1 dollars', s)
    s = re.sub(r'\b100%', 'one hundred percent', s)
    s = re.sub(r'\b0%', 'zero percent', s)
    s = re.sub(r'%', ' percent', s)
    # Tech acronyms spoken cleanly
    s = re.sub(r'\bAI\b', 'A.I.', s)
    s = re.sub(r'\bAPI\b', 'A.P.I.', s)
    s = re.sub(r'\bAPIs\b', 'A.P.I.s', s)
    s = re.sub(r'\bLLM\b', 'L.L.M.', s)
    s = re.sub(r'\bLLMs\b', 'L.L.M.s', s)
    s = re.sub(r'\bUI\b', 'U.I.', s)
    s = re.sub(r'\bUX\b', 'U.X.', s)
    s = re.sub(r'\bURL\b', 'U.R.L.', s)
    s = re.sub(r'\bPR\b', 'P.R.', s)
    s = re.sub(r'\bPRs\b', 'P.R.s', s)
    s = re.sub(r'\bC\+\+', 'C plus plus', s)
    s = re.sub(r'\bMCP\b', 'M.C.P.', s)
    s = re.sub(r'\bCLI\b', 'C.L.I.', s)
    s = re.sub(r'\bSQL\b', 'sequel', s, flags=re.IGNORECASE)
    s = re.sub(r'\bGitHub\b', 'Git Hub', s, flags=re.IGNORECASE)
    s = re.sub(r'\bVS\s*Code\b', 'V.S. Code', s, flags=re.IGNORECASE)
    s = re.sub(r'\bv([0-9]+)\.([0-9]+)\b', r'version \1 point \2', s)
    # Spell out any vowel-less consonant cluster acronyms cleanly (e.g., SDK -> S.D.K., MCP -> M.C.P.)
    s = re.sub(r'\b([B-DF-HJ-NP-TV-Z]{3,6})\b', lambda m: '. '.join(m.group(1)) + '.', s)
    return s

def synthesize_dialogue(project_dir, pair_name="default"):
    """Takes project/script.json and creates data/narration.wav and data/lines.json."""
    ensure_models()
    from kokoro_onnx import Kokoro

    P = Path(project_dir)
    script_file = P / "script.json"
    if not script_file.exists():
        raise FileNotFoundError(f"Missing script.json in {project_dir}")

    S = json.loads(script_file.read_text(encoding="utf-8"))
    voices = VOICE_PAIRS.get(pair_name, VOICE_PAIRS["default"])

    print(f"\n[Dual-Voice Engine] Synthesizing 2-character dialogue:")
    print(f"  Guide: {voices['guide']} | Skeptic: {voices['skeptic']}")

    k = Kokoro(str(KDIR / 'kokoro-v1.0.onnx'), str(KDIR / 'voices-v1.0.bin'))

    audio_chunks = [np.zeros(int(S.get('lead', 0.35) * SR))]
    current_time = len(audio_chunks[0]) / SR
    lines_meta = []

    for i, line in enumerate(S["lines"]):
        spk = line.get("speaker", "guide").lower()
        active_voice = voices["guide"] if spk == "guide" else voices["skeptic"]
        
        # Guide: deep, grounded pacing (1.03x). Skeptic: expressive, questioning pace (1.06x).
        speed = 1.03 if spk == "guide" else 1.06
        lang = 'en-gb' if active_voice.startswith('b') else 'en-us'

        raw_text = line["text"].strip()

        # Infuse real human conversational prosody
        if spk == "skeptic":
            # Force genuine rising question pitch when asking or reacting with disbelief
            if not raw_text.endswith("?") and not raw_text.endswith("!"):
                if re.search(r'^(wait|hold on|what|how|why|is that|can you|and|okay but|so)\b', raw_text, re.IGNORECASE):
                    raw_text = raw_text.rstrip(".") + "?"
            # Natural thinking beat after conversational openers ("Wait—", "Hold on—")
            raw_text = re.sub(r'^(wait|hold on|okay|look)[,\s]+', r'\1— ', raw_text, flags=re.IGNORECASE)
        else:
            # Guide: assertive, natural cadence without run-ons
            raw_text = re.sub(r'\b(yep|yeah|look|see)[,\s]+', r'\1. ', raw_text, flags=re.IGNORECASE)

        spoken_text = normalize_tech_phonetics(raw_text)
        raw_audio = k.create(spoken_text, voice=active_voice, speed=speed, lang=lang)[0]
        cleaned_audio = trim_silence(np.asarray(raw_audio, dtype=np.float64))

        dur = len(cleaned_audio) / SR
        start_time = current_time
        end_time = current_time + dur

        lines_meta.append({
            "i": i,
            "speaker": spk,
            "header": line.get("header", ""),
            "prop": line.get("prop", ""),
            "text": line["text"],
            "s": round(start_time, 3),
            "start": round(start_time, 3),
            "e": round(end_time, 3),
            "end": round(end_time, 3)
        })

        audio_chunks.append(cleaned_audio)

        # Natural conversational pause between lines
        gap = line.get("gap", 0.18 if spk == "guide" else 0.22)
        pause_samples = np.zeros(int(gap * SR))
        audio_chunks.append(pause_samples)
        current_time = end_time + gap

    # Trailing outro silence
    audio_chunks.append(np.zeros(int(S.get('outro', 0.8) * SR)))
    full_audio = np.concatenate(audio_chunks)

    # Export narration.wav
    data_dir = P / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    wav_path = data_dir / "narration.wav"
    wavfile.write(str(wav_path), SR, (full_audio * 32767).astype(np.int16))

    total_sec = len(full_audio) / SR

    # Export lines.json (matching voice.py schema)
    lines_path = data_dir / "lines.json"
    lines_path.write_text(json.dumps({
        "duration": round(total_sec, 3),
        "lines": lines_meta
    }, indent=2), encoding="utf-8")

    print(f"  ✓ Dual-voice audio rendered: {total_sec:.1f}s ({len(lines_meta)} dialogue cuts)")
    print(f"  ✓ Saved to {wav_path} and {lines_path}")
    return lines_meta

if __name__ == "__main__":
    if len(sys.argv) > 1:
        synthesize_dialogue(sys.argv[1])
    else:
        print("Usage: python dual_voice.py <project_directory>")

