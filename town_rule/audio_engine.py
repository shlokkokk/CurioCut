"""
Audio engine for Town-Rule episodes:
1. Per-shot Kokoro-82M TTS narration (reuses ~/.faceless-shorts/kokoro) -> narration.wav + shot timings
2. Faster-Whisper word-level timestamps -> words.json
3. Procedural diegetic SFX (clink, heartbeat, beep_monitor, door_creak, radio_static, footsteps, whoosh, pop, thunder)
   + ambient emotional/tension/mystery music bed -> mix.wav
"""

import json
import os
import re
from pathlib import Path
import numpy as np
from scipy.io import wavfile

SR = 24000
FACELESS_HOME = Path(os.environ.get("FACELESS_HOME", Path.home() / ".faceless-shorts"))
KDIR = FACELESS_HOME / "kokoro"


def _trim_silence(x: np.ndarray, thr: float = 0.008) -> np.ndarray:
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x[: int(SR * 0.25)]
    pad = int(SR * 0.02)
    s = max(0, int(idx[0]) - pad)
    e = min(len(x), int(idx[-1]) + pad)
    return x[s:e]


def synthesize_narration(episode: dict, work_dir: Path) -> tuple[Path, dict]:
    from kokoro_onnx import Kokoro

    onnx_path = KDIR / "kokoro-v1.0.onnx"
    voices_path = KDIR / "voices-v1.0.bin"
    if not onnx_path.exists() or not voices_path.exists():
        raise FileNotFoundError(
            f"Kokoro models missing in {KDIR}. Run faceless-shorts voice.py --download first."
        )

    kokoro = Kokoro(str(onnx_path), str(voices_path))
    voice = episode.get("voice", "am_michael")
    speed = float(episode.get("speed", 1.10))

    lead_s = 0.25
    outro_s = 1.2
    chunks = [np.zeros(int(SR * lead_s), dtype=np.float32)]
    cursor = lead_s

    shots = episode.get("shots", [])
    for i, shot in enumerate(shots):
        text = shot.get("text", "").strip()
        if not text:
            text = "..."
        samples, sr = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
        if sr != SR:
            # Simple linear resample if needed
            ratio = SR / sr
            n_new = int(len(samples) * ratio)
            samples = np.interp(
                np.linspace(0, len(samples) - 1, n_new),
                np.arange(len(samples)),
                samples,
            ).astype(np.float32)
        samples = _trim_silence(samples.astype(np.float32))
        dur = len(samples) / SR

        shot["start"] = round(cursor, 3)
        shot["end"] = round(cursor + dur, 3)
        shot["duration"] = round(dur, 3)

        chunks.append(samples)
        gap = 0.14 if i < len(shots) - 1 else outro_s
        if i == len(shots) - 2:
            gap = 0.24  # brief beat before final twist shot
        chunks.append(np.zeros(int(SR * gap), dtype=np.float32))
        cursor += dur + gap

    full_audio = np.concatenate(chunks)
    # Normalize peak to 0.88
    peak = np.max(np.abs(full_audio)) or 1.0
    full_audio = (full_audio / peak * 0.88).astype(np.float32)

    nar_path = work_dir / "narration.wav"
    wavfile.write(str(nar_path), SR, (full_audio * 32767).astype(np.int16))

    episode["total_duration"] = round(len(full_audio) / SR, 3)
    timed_path = work_dir / "episode_timed.json"
    timed_path.write_text(json.dumps(episode, indent=2), encoding="utf-8")
    return nar_path, episode


def extract_words(nar_path: Path, episode: dict, work_dir: Path) -> list[dict]:
    from faster_whisper import WhisperModel

    sr_in, wav_i16 = wavfile.read(str(nar_path))
    wav_f32 = wav_i16.astype(np.float32) / 32767.0
    if sr_in != 16000:
        n16 = int(len(wav_f32) * (16000.0 / sr_in))
        wav_f32 = np.interp(
            np.linspace(0, len(wav_f32) - 1, n16),
            np.arange(len(wav_f32)),
            wav_f32,
        ).astype(np.float32)

    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(wav_f32, word_timestamps=True)
    words = []
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            txt = w.word.strip()
            if not txt:
                continue
            words.append({
                "word": txt,
                "start": round(float(w.start), 3),
                "end": round(float(w.end), 3),
            })

    # Fallback if whisper missed anything
    if not words:
        for shot in episode.get("shots", []):
            tokens = shot.get("text", "").split()
            if not tokens:
                continue
            s0, s1 = shot["start"], shot["end"]
            dt = (s1 - s0) / max(1, len(tokens))
            for idx, tok in enumerate(tokens):
                words.append({
                    "word": tok,
                    "start": round(s0 + idx * dt, 3),
                    "end": round(s0 + (idx + 1) * dt, 3),
                })

    words_path = work_dir / "words.json"
    words_path.write_text(json.dumps(words, indent=2), encoding="utf-8")
    return words


def _gen_sfx(kind: str) -> np.ndarray:
    rng = np.random.default_rng(42)
    if kind == "clink":
        t = np.linspace(0, 0.45, int(SR * 0.45), endpoint=False)
        sig = (
            0.55 * np.sin(2 * np.pi * 2650 * t) * np.exp(-12 * t)
            + 0.35 * np.sin(2 * np.pi * 4120 * t) * np.exp(-16 * t)
            + 0.20 * np.sin(2 * np.pi * 6280 * t) * np.exp(-22 * t)
        )
        return sig.astype(np.float32) * 0.28
    if kind == "beep_monitor":
        t = np.linspace(0, 0.14, int(SR * 0.14), endpoint=False)
        env = np.sin(np.pi * t / 0.14) ** 0.8
        return (np.sin(2 * np.pi * 880 * t) * env * 0.12).astype(np.float32)
    if kind == "heartbeat":
        t = np.linspace(0, 0.55, int(SR * 0.55), endpoint=False)
        lub = np.sin(2 * np.pi * 58 * t) * np.exp(-18 * t)
        dub = np.sin(2 * np.pi * 52 * np.maximum(0, t - 0.18)) * np.exp(-20 * np.maximum(0, t - 0.18)) * (t > 0.18)
        return ((lub + 0.8 * dub) * 0.7).astype(np.float32)
    if kind == "whoosh":
        t = np.linspace(0, 0.30, int(SR * 0.30), endpoint=False)
        noise = rng.normal(0, 1, len(t))
        env = np.sin(np.pi * t / 0.30) ** 1.8
        kernel = np.ones(32) / 32
        smooth = np.convolve(noise, kernel, mode="same")
        sub = np.sin(2 * np.pi * np.cumsum(np.linspace(150, 55, len(t))) / SR) * 0.14
        return ((smooth * 0.12 + sub) * env).astype(np.float32)
    if kind == "pop":
        t = np.linspace(0, 0.09, int(SR * 0.09), endpoint=False)
        freq = np.linspace(480, 160, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / SR
        return (np.sin(phase) * np.exp(-32 * t) * 0.38).astype(np.float32)
    if kind == "radio_static":
        t = np.linspace(0, 0.25, int(SR * 0.25), endpoint=False)
        # Subtle walkie-talkie squelch chirp instead of harsh white noise
        freq = np.linspace(920, 680, len(t))
        sig = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-14 * t)
        return (sig * 0.10).astype(np.float32)
    if kind == "door_creak":
        t = np.linspace(0, 0.65, int(SR * 0.65), endpoint=False)
        freq = 190 + 45 * np.sin(2 * np.pi * 7 * t)
        phase = 2 * np.pi * np.cumsum(freq) / SR
        return (np.sin(phase) * np.exp(-3.5 * t) * 0.22).astype(np.float32)
    if kind == "thunder":
        t = np.linspace(0, 1.4, int(SR * 1.4), endpoint=False)
        noise = rng.normal(0, 1, len(t))
        kernel = np.ones(75) / 75
        rumble = np.convolve(noise, kernel, mode="same")
        env = np.exp(-2.2 * t)
        return (rumble * env * 0.75).astype(np.float32)
    if kind == "footsteps":
        t = np.linspace(0, 0.55, int(SR * 0.55), endpoint=False)
        out = np.zeros_like(t)
        for st in (0.0, 0.18, 0.36):
            dt = np.maximum(0.0, t - st)
            mask = (t >= st) & (dt < 0.09)
            out += mask * np.sin(2 * np.pi * 95 * dt) * np.exp(-35 * dt) * 0.35
        return out.astype(np.float32)
    if kind == "gasp":
        t = np.linspace(0, 0.22, int(SR * 0.22), endpoint=False)
        noise = rng.normal(0, 1, len(t))
        kernel = np.ones(36) / 36
        smooth = np.convolve(noise, kernel, mode="same")
        env = np.sin(np.pi * t / 0.22) ** 1.4
        return (smooth * env * 0.12).astype(np.float32)
    return np.zeros(0, dtype=np.float32)


def _gen_music_bed(total_dur: float, mood: str) -> np.ndarray:
    n = int(SR * total_dur)
    t = np.linspace(0, total_dur, n, endpoint=False)
    bed = np.zeros(n, dtype=np.float32)

    if mood in ("emotional", "sad"):
        # Gentle slow piano-like sine+harmonic chord progression (Am - F - C - G)
        chords = [
            [220.0, 261.63, 329.63],
            [174.61, 220.0, 261.63],
            [130.81, 196.0, 261.63],
            [196.0, 246.94, 293.66],
        ]
        bar_len = 2.6
        for idx in range(int(total_dur / bar_len) + 1):
            c = chords[idx % len(chords)]
            s_i = int(idx * bar_len * SR)
            e_i = min(n, int((idx + 1) * bar_len * SR))
            if s_i >= n:
                break
            lt = np.linspace(0, (e_i - s_i) / SR, e_i - s_i, endpoint=False)
            env = np.exp(-1.1 * lt) * (1 - np.exp(-40 * lt))
            bar_sig = sum(np.sin(2 * np.pi * f * lt) + 0.25 * np.sin(4 * np.pi * f * lt) for f in c) / len(c)
            bed[s_i:e_i] += (bar_sig * env).astype(np.float32)
    elif mood in ("horror", "red_horror"):
        # Low ominous drone + subtle dissonant shimmer
        bed = (
            0.55 * np.sin(2 * np.pi * 55.0 * t)
            + 0.30 * np.sin(2 * np.pi * 58.2 * t)
            + 0.18 * np.sin(2 * np.pi * 110.0 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t))
        ).astype(np.float32)
    elif mood == "whimsical":
        # Light pizzicato bounce
        notes = [261.63, 329.63, 392.0, 329.63, 293.66, 349.23, 440.0, 392.0]
        step = 0.45
        for idx in range(int(total_dur / step) + 1):
            f = notes[idx % len(notes)]
            s_i = int(idx * step * SR)
            e_i = min(n, s_i + int(0.38 * SR))
            if s_i >= n:
                break
            lt = np.linspace(0, (e_i - s_i) / SR, e_i - s_i, endpoint=False)
            env = np.exp(-8.5 * lt)
            bed[s_i:e_i] += (np.sin(2 * np.pi * f * lt) * env).astype(np.float32)
    else:
        # Mystery pulse (tight cinematic bass + soft arpeggio)
        notes = [110.0, 164.81, 196.0, 164.81, 130.81, 196.0, 220.0, 196.0]
        step = 0.55
        for idx in range(int(total_dur / step) + 1):
            f = notes[idx % len(notes)]
            s_i = int(idx * step * SR)
            e_i = min(n, s_i + int(0.50 * SR))
            if s_i >= n:
                break
            lt = np.linspace(0, (e_i - s_i) / SR, e_i - s_i, endpoint=False)
            env = np.exp(-4.5 * lt) * (1 - np.exp(-60 * lt))
            bed[s_i:e_i] += (np.sin(2 * np.pi * f * lt) * env).astype(np.float32)

    # Fade in & out
    fade = min(n // 4, int(SR * 1.0))
    if fade > 0:
        bed[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        bed[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = np.max(np.abs(bed)) or 1.0
    return (bed / peak * 0.14).astype(np.float32)


def mix_audio(nar_path: Path, episode: dict, work_dir: Path) -> Path:
    sr_read, nar_i16 = wavfile.read(str(nar_path))
    nar = nar_i16.astype(np.float32) / 32767.0
    total_dur = len(nar) / sr_read

    bed = _gen_music_bed(total_dur, episode.get("music_mood", "mystery"))
    if len(bed) != len(nar):
        bed = np.resize(bed, len(nar))

    sfx_track = np.zeros(len(nar), dtype=np.float32)
    for idx, shot in enumerate(episode.get("shots", [])):
        sfx_name = shot.get("sfx", "none")
        if idx > 0 and sfx_name == "none" and idx % 3 == 0:
            sfx_name = "whoosh"
        if sfx_name and sfx_name != "none":
            clip = _gen_sfx(sfx_name)
            if len(clip) > 0:
                pos = int(float(shot.get("start", 0.0)) * SR)
                end_pos = min(len(sfx_track), pos + len(clip))
                sfx_track[pos:end_pos] += clip[: end_pos - pos]

    mixed = nar + bed + sfx_track
    peak = np.max(np.abs(mixed))
    if peak > 0.95:
        mixed = mixed / peak * 0.92

    mix_path = work_dir / "mix.wav"
    wavfile.write(str(mix_path), SR, (mixed * 32767).astype(np.int16))
    return mix_path


def build_episode_audio(episode: dict, work_dir: Path) -> tuple[dict, list[dict], Path]:
    work_dir.mkdir(parents=True, exist_ok=True)
    nar_path, timed_ep = synthesize_narration(episode, work_dir)
    words = extract_words(nar_path, timed_ep, work_dir)
    mix_path = mix_audio(nar_path, timed_ep, work_dir)
    return timed_ep, words, mix_path

