"""
ASS subtitle generator for Town-Rule videos:
1-word (or paired short-word) bold centered lower-third captions (~74% down 1080x1920),
with thick black outline, soft drop shadow, subtle scale pop, and selective color highlights.
"""

import re
from pathlib import Path


def _hex_to_ass_bgr(hex_col: str) -> str:
    h = hex_col.lstrip("#")
    if len(h) != 6:
        return "&H00FFFFFF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}"


def _fmt_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def build_ass_subtitles(words: list[dict], episode: dict, out_ass: Path) -> Path:
    hl_map = {}
    for item in episode.get("highlight_words", []):
        w = re.sub(r"[^a-z0-9]", "", str(item.get("word", "")).lower())
        if w:
            hl_map[w] = _hex_to_ass_bgr(item.get("color", "#FFD43B"))

    # Group very short words (< 3 chars like "a", "in", "to") occasionally if needed,
    # or keep clean 1-word punchy rhythm like the top viral references.
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial Black,102,&H00FFFFFF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,11,5,2,60,60,440,1
Style: Hud,Arial Black,56,&H00FFFFFF,&H000000FF,&H00000000,&HB0101018,-1,0,0,0,100,100,0,0,3,6,0,8,60,60,210,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for shot in episode.get("shots", []):
        ov = shot.get("overlay")
        if isinstance(ov, dict) and ov.get("text"):
            s0 = float(shot.get("start", 0.0))
            s1 = float(shot.get("end", s0 + 1.5))
            col_tag = _hex_to_ass_bgr(ov.get("color", "#FFD43B"))
            ov_text = str(ov["text"]).strip()
            lines.append(f"Dialogue: 1,{_fmt_time(s0)},{_fmt_time(s1)},Hud,,0,0,0,,{{\\c{col_tag}}}{ov_text}")
    for i, w in enumerate(words):
        txt = str(w.get("word", "")).strip()
        if not txt:
            continue
        t0 = float(w["start"])
        t1 = float(w["end"])
        if i + 1 < len(words):
            next_t0 = float(words[i + 1]["start"])
            if next_t0 > t1 and (next_t0 - t1) < 0.12:
                t1 = next_t0
        if t1 - t0 < 0.08:
            t1 = t0 + 0.08

        clean_key = re.sub(r"[^a-z0-9]", "", txt.lower())
        color_tag = ""
        if clean_key in hl_map:
            color_tag = f"\\c{hl_map[clean_key]}"

        # Subtle 92% -> 105% -> 100% pop animation in 70ms
        anim = "{\\fscx92\\fscy92\\t(0,65,\\fscx105\\fscy105)\\t(65,130,\\fscx100\\fscy100)" + color_tag + "}"
        lines.append(f"Dialogue: 0,{_fmt_time(t0)},{_fmt_time(t1)},Cap,,0,0,0,,{anim}{txt}")

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    out_ass.write_text("\n".join(lines), encoding="utf-8")
    return out_ass

