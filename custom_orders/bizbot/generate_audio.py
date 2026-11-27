import os
import json
import re
import math
from pathlib import Path
import numpy as np
from scipy.io import wavfile

SR = 24000
BASE_DIR = Path(__file__).resolve().parent
WORK_DIR = BASE_DIR / "work"
WORK_DIR.mkdir(parents=True, exist_ok=True)

SHOTS = [
    {
        "id": "shot_1",
        "text": "Right now, a customer is messaging your WhatsApp to buy from you. But you are asleep, busy, or away from your phone.",
        "sfx": ["sfx_whatsapp_notif", "sfx_clock_tick"]
    },
    {
        "id": "shot_2",
        "text": "By the time you reply, they have already bought from your competitor. In business, delayed replies are lost money.",
        "sfx": ["sfx_sub_drop", "sfx_lost_money"]
    },
    {
        "id": "shot_3",
        "text": "This is BizBot. An intelligent chat system that turns your WhatsApp into a twenty-four-seven sales machine.",
        "sfx": ["sfx_cyber_boot", "sfx_laser_sweep"]
    },
    {
        "id": "shot_4",
        "text": "No more typing long paragraphs. BizBot answers in zero point two seconds with instant interactive buttons that let buyers browse, call, and order on autopilot.",
        "sfx": ["sfx_button_click", "sfx_cash_ding"]
    },
    {
        "id": "shot_5",
        "text": "Starting at just two hundred rupees a month. Make your chats work alone at bizbot dot zernox dot net.",
        "sfx": ["sfx_cinematic_impact", "sfx_riser"]
    }
]

def generate_procedural_sfx(name: str, duration_s: float = 0.5) -> np.ndarray:
    n_samples = int(SR * duration_s)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    
    if name == "sfx_whatsapp_notif":
        # Realistic WhatsApp two-tone bell chime (Marimba style: 1318 Hz + 1760 Hz)
        f1, f2 = 1318.5, 1760.0
        tone1 = np.sin(2 * np.pi * f1 * t) * np.exp(-t * 14.0)
        t_offset = np.maximum(0, t - 0.08)
        tone2 = np.sin(2 * np.pi * f2 * t_offset) * np.exp(-t_offset * 12.0)
        sfx = 0.5 * tone1 + 0.6 * tone2
    elif name == "sfx_sub_drop":
        # Deep cinematic 808 sub bass drop from 90 Hz down to 35 Hz
        freq = np.linspace(90, 35, n_samples)
        phase = 2 * np.pi * np.cumsum(freq) / SR
        env = np.exp(-t * 2.5) * (1.0 - np.exp(-t * 40.0))
        sfx = np.sin(phase) * env * 0.85
    elif name == "sfx_cyber_boot":
        # High-tech servo/cybernetic power up sweep
        freq = 150 + 800 * (t / duration_s)**2
        phase = 2 * np.pi * np.cumsum(freq) / SR
        env = np.sin(np.pi * t / duration_s)**0.5
        sfx = np.sin(phase) * env * 0.6
    elif name == "sfx_button_click":
        # Satisfying mechanical tactile switch click
        burst = np.random.uniform(-1, 1, n_samples) * np.exp(-t * 90.0)
        pop = np.sin(2 * np.pi * 320 * t) * np.exp(-t * 45.0)
        sfx = 0.7 * burst + 0.8 * pop
    elif name == "sfx_cash_ding":
        # Crisp metal bell register ding (2800 Hz harmonic ring)
        f = 2793.8
        bell = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.05 * t)) * np.exp(-t * 6.0)
        sfx = bell * 0.65
    elif name == "sfx_cinematic_impact":
        # Massive trailer braam / boom
        sub = np.sin(2 * np.pi * np.linspace(65, 30, n_samples) * t) * np.exp(-t * 2.0)
        noise = np.random.uniform(-1, 1, n_samples) * np.exp(-t * 15.0) * 0.3
        sfx = (sub + noise) * 0.9
    else:
        # Subtle whoosh transition
        noise = np.random.uniform(-1, 1, n_samples)
        env = np.sin(np.pi * t / duration_s)**2
        sfx = noise * env * 0.35
        
    return np.clip(sfx, -1.0, 1.0).astype(np.float32)

def generate_background_music(total_duration_s: float) -> np.ndarray:
    n_samples = int(SR * total_duration_s)
    t = np.linspace(0, total_duration_s, n_samples, endpoint=False)
    
    # Modern cyber tech ambient bed (Subtle pulsating minor synth chords & rhythmic sub-kick)
    # Chord root: D minor (D3: 146.8 Hz, F3: 174.6 Hz, A3: 220.0 Hz)
    chord1 = np.sin(2 * np.pi * 146.83 * t) + 0.5 * np.sin(2 * np.pi * 174.61 * t) + 0.5 * np.sin(2 * np.pi * 220.0 * t)
    # Chord 2: Bb major (Bb2: 116.5 Hz, D3: 146.8 Hz, F3: 174.6 Hz)
    chord2 = np.sin(2 * np.pi * 116.54 * t) + 0.5 * np.sin(2 * np.pi * 146.83 * t) + 0.5 * np.sin(2 * np.pi * 174.61 * t)
    
    # Bar duration: 4 beats @ 120 bpm = 2.0s per bar
    bar_time = (t % 4.0)
    bar_mask = (bar_time < 2.0).astype(np.float32)
    synth_pad = chord1 * bar_mask + chord2 * (1.0 - bar_mask)
    
    # Gentle 120 bpm kick pulse every 0.5s
    beat_phase = (t % 0.5) / 0.5
    kick = np.sin(2 * np.pi * np.maximum(40, 120 * (1.0 - beat_phase * 3.0)) * beat_phase * 0.5) * np.exp(-beat_phase * 10.0)
    
    # Smooth tape-hiss / vinyl texture for organic warmth
    texture = np.random.uniform(-0.02, 0.02, n_samples)
    
    music = (synth_pad * 0.08 + kick * 0.12 + texture) * 0.22
    # Fade in / out
    fade_in = np.minimum(1.0, t / 1.5)
    fade_out = np.minimum(1.0, (total_duration_s - t) / 2.0)
    return (music * fade_in * fade_out).astype(np.float32)

def main():
    print("[1/4] Synthesizing Kokoro TTS studio narration...")
    from kokoro_onnx import Kokoro
    
    faceless_home = Path.home() / ".faceless-shorts"
    onnx_path = faceless_home / "kokoro" / "kokoro-v1.0.onnx"
    voices_path = faceless_home / "kokoro" / "voices-v1.0.bin"
    kokoro = Kokoro(str(onnx_path), str(voices_path))
    
    # High energy, clear, confident voice: am_michael or am_adam
    voice = "am_michael"
    speed = 1.08
    
    narration_chunks = []
    shot_timings = []
    current_time = 0.4 # Small lead padding
    
    # Add initial lead silence
    narration_chunks.append(np.zeros(int(SR * current_time), dtype=np.float32))
    
    for shot in SHOTS:
        shot_start = current_time
        samples, sr = kokoro.create(shot["text"], voice=voice, speed=speed, lang="en-us")
        if sr != SR:
            ratio = SR / sr
            samples = np.interp(np.linspace(0, len(samples)-1, int(len(samples)*ratio)), np.arange(len(samples)), samples).astype(np.float32)
            
        dur = len(samples) / SR
        shot_end = shot_start + dur
        print(f"  [Voice] Synthesized {shot['id']}: {dur:.2f}s", flush=True)
        
        narration_chunks.append(samples)
        # Small gap between shots
        gap = 0.35
        narration_chunks.append(np.zeros(int(SR * gap), dtype=np.float32))
        
        shot_timings.append({
            "id": shot["id"],
            "text": shot["text"],
            "start": round(shot_start, 3),
            "end": round(shot_end, 3),
            "duration": round(dur, 3),
            "sfx": shot["sfx"]
        })
        current_time = shot_end + gap
        
    # Outro padding
    narration_chunks.append(np.zeros(int(SR * 1.0), dtype=np.float32))
    total_audio = np.concatenate(narration_chunks)
    total_dur = len(total_audio) / SR
    print(f"Total narration duration: {total_dur:.2f} seconds")
    
    narration_wav = WORK_DIR / "narration.wav"
    wavfile.write(str(narration_wav), SR, (total_audio * 32767).astype(np.int16))
    
    print("[2/4] Transcribing word-level phonetic timestamps with Faster-Whisper...", flush=True)
    # Convert narration audio to 16kHz float32 directly to avoid PyAV av.open metadata_errors bug
    target_sr = 16000
    audio_16k = np.interp(
        np.linspace(0, len(total_audio) - 1, int(len(total_audio) * target_sr / SR)),
        np.arange(len(total_audio)),
        total_audio
    ).astype(np.float32)

    from faster_whisper import WhisperModel
    whisper = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, info = whisper.transcribe(audio_16k, word_timestamps=True)
    
    words_data = []
    for seg in segments:
        for w in seg.words:
            clean_word = re.sub(r'^[^\w]+|[^\w]+$', '', w.word).upper()
            if clean_word:
                words_data.append({
                    "word": clean_word,
                    "raw": w.word,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "prob": round(w.probability, 3)
                })
                
    with open(WORK_DIR / "words.json", "w", encoding="utf-8") as f:
        json.dump(words_data, f, indent=2)
    print(f"Aligned {len(words_data)} word timestamps.", flush=True)

    print("[3/4] Designing SFX and master audio mixdown...", flush=True)
    mix_audio = np.copy(total_audio)
    
    # Add procedural SFX synced to shot timestamps
    for s in shot_timings:
        t_start = s["start"]
        for sfx_name in s["sfx"]:
            sfx_wave = generate_procedural_sfx(sfx_name, duration_s=1.2)
            idx_start = int(t_start * SR)
            idx_end = min(len(mix_audio), idx_start + len(sfx_wave))
            len_to_add = idx_end - idx_start
            mix_audio[idx_start:idx_end] += sfx_wave[:len_to_add] * 0.45
            t_start += 0.8
            
    # Add atmospheric music bed
    music_bed = generate_background_music(total_dur)
    min_len = min(len(mix_audio), len(music_bed))
    final_mix = mix_audio[:min_len] + music_bed[:min_len]
    
    # Normalize
    max_peak = np.max(np.abs(final_mix))
    if max_peak > 0:
        final_mix = (final_mix / max_peak) * 0.95
        
    mix_wav = WORK_DIR / "mix.wav"
    wavfile.write(str(mix_wav), SR, (final_mix * 32767).astype(np.int16))
    
    metadata = {
        "title": "BizBot - Chats That Work Alone",
        "client": "ZERNOX",
        "url": "https://bizbot.zernox.net/",
        "duration": round(total_dur, 2),
        "fps": 30,
        "total_frames": int(math.ceil(total_dur * 30)),
        "shots": shot_timings
    }
    with open(WORK_DIR / "episode_timed.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"[4/4] Audio pipeline complete! Work files saved to {WORK_DIR.resolve()}", flush=True)

if __name__ == "__main__":
    main()
