"""
Procedural 2D Roblox-style expressive face decal generator (512x512 RGBA PNGs).
Generates crisp vector-like cartoon faces mapped onto the front of 3D R6 heads.
"""

from pathlib import Path
from PIL import Image, ImageDraw

FACES_DIR = Path(__file__).resolve().parent / "assets" / "faces"

EXPRESSION_LIST = [
    "neutral",
    "happy",
    "sad",
    "crying",
    "shocked",
    "angry",
    "smirk",
    "monster_grin",
    "closed",
    "blush",
    "dizzy",
    "blind",
    "talk_open",
    "worried",
]


def _draw_thick_arc(draw, bbox, start, end, fill=(20, 20, 25, 255), width=14):
    draw.arc(bbox, start=start, end=end, fill=fill, width=width)


def _draw_eye_normal(draw, cx, cy, rx=34, ry=44, pupil_dx=0, pupil_dy=0, sparkle=True):
    # White sclera with dark ink outline
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(250, 250, 255, 255), outline=(18, 18, 22, 255), width=10)
    # Pupil
    prx, pry = int(rx * 0.54), int(ry * 0.56)
    px, py = cx + pupil_dx, cy + pupil_dy
    draw.ellipse([px - prx, py - pry, px + prx, py + pry], fill=(18, 18, 24, 255))
    if sparkle:
        draw.ellipse([px - prx // 2 - 4, py - pry // 2 - 4, px - prx // 2 + 10, py - pry // 2 + 10], fill=(255, 255, 255, 240))


def _draw_eye_shocked(draw, cx, cy):
    draw.ellipse([cx - 46, cy - 58, cx + 46, cy + 58], fill=(255, 255, 255, 255), outline=(15, 15, 20, 255), width=11)
    draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(15, 15, 20, 255))


def _draw_eye_happy(draw, cx, cy):
    _draw_thick_arc(draw, [cx - 38, cy - 22, cx + 38, cy + 36], 195, 345, width=16)


def _draw_eye_closed(draw, cx, cy):
    _draw_thick_arc(draw, [cx - 36, cy - 18, cx + 36, cy + 28], 15, 165, width=14)


def _draw_eye_blind(draw, cx, cy):
    draw.ellipse([cx - 34, cy - 42, cx + 34, cy + 42], fill=(215, 220, 230, 255), outline=(45, 45, 55, 255), width=9)
    draw.ellipse([cx - 16, cy - 20, cx + 16, cy + 20], fill=(185, 192, 205, 255))


def _draw_brows(draw, mode="neutral"):
    ink = (18, 18, 22, 255)
    if mode == "angry":
        draw.line([(115, 145), (210, 178)], fill=ink, width=16)
        draw.line([(397, 145), (302, 178)], fill=ink, width=16)
    elif mode in ("sad", "crying", "worried"):
        draw.line([(118, 172), (206, 142)], fill=ink, width=14)
        draw.line([(394, 172), (306, 142)], fill=ink, width=14)
    elif mode == "smirk":
        draw.line([(122, 155), (205, 145)], fill=ink, width=13)
        draw.line([(305, 162), (392, 162)], fill=ink, width=13)
    elif mode == "shocked":
        _draw_thick_arc(draw, [120, 118, 210, 165], 190, 350, width=12)
        _draw_thick_arc(draw, [302, 118, 392, 165], 190, 350, width=12)
    else:
        draw.line([(124, 152), (204, 150)], fill=ink, width=12)
        draw.line([(308, 150), (388, 152)], fill=ink, width=12)


def _draw_tears(draw, cx, cy):
    tear_col = (120, 210, 255, 225)
    draw.rectangle([cx - 18, cy + 32, cx + 18, cy + 165], fill=tear_col)
    draw.ellipse([cx - 24, cy + 145, cx + 24, cy + 185], fill=tear_col)


def _draw_sweat_drop(draw):
    draw.polygon([(430, 105), (404, 162), (456, 162)], fill=(110, 215, 255, 235))
    draw.ellipse([404, 142, 456, 192], fill=(110, 215, 255, 235), outline=(25, 45, 70, 255), width=6)


def _draw_blush(draw):
    col = (255, 130, 150, 175)
    draw.ellipse([85, 275, 155, 315], fill=col)
    draw.ellipse([357, 275, 427, 315], fill=col)


def generate_face(expr: str, out_path: Path):
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    ink = (18, 18, 22, 255)
    lx, rx = 166, 346
    ey = 225

    if expr == "neutral":
        _draw_brows(draw, "neutral")
        _draw_eye_normal(draw, lx, ey)
        _draw_eye_normal(draw, rx, ey)
        _draw_thick_arc(draw, [206, 295, 306, 355], 15, 165, width=14)

    elif expr == "happy":
        _draw_brows(draw, "neutral")
        _draw_eye_happy(draw, lx, ey)
        _draw_eye_happy(draw, rx, ey)
        draw.pieslice([195, 290, 317, 385], 0, 180, fill=(210, 65, 80, 255), outline=ink, width=11)
        draw.rectangle([215, 336, 297, 350], fill=(255, 255, 255, 255))

    elif expr == "blush":
        _draw_blush(draw)
        _draw_brows(draw, "neutral")
        _draw_eye_normal(draw, lx, ey, rx=40, ry=50)
        _draw_eye_normal(draw, rx, ey, rx=40, ry=50)
        _draw_thick_arc(draw, [215, 310, 256, 345], 10, 170, width=12)
        _draw_thick_arc(draw, [256, 310, 297, 345], 10, 170, width=12)

    elif expr == "sad":
        _draw_brows(draw, "sad")
        _draw_eye_normal(draw, lx, ey, pupil_dy=8)
        _draw_eye_normal(draw, rx, ey, pupil_dy=8)
        _draw_thick_arc(draw, [202, 325, 310, 385], 195, 345, width=14)

    elif expr == "worried":
        _draw_brows(draw, "worried")
        _draw_eye_normal(draw, lx, ey)
        _draw_eye_normal(draw, rx, ey)
        _draw_sweat_drop(draw)
        # Wavy mouth
        pts = [(205, 348), (230, 335), (256, 352), (282, 335), (307, 348)]
        draw.line(pts, fill=ink, width=12, joint="curve")

    elif expr == "crying":
        _draw_tears(draw, lx, ey)
        _draw_tears(draw, rx, ey)
        _draw_brows(draw, "crying")
        _draw_eye_normal(draw, lx, ey, rx=38, ry=46)
        _draw_eye_normal(draw, rx, ey, rx=38, ry=46)
        _draw_thick_arc(draw, [200, 325, 312, 390], 195, 345, width=15)

    elif expr == "shocked":
        _draw_brows(draw, "shocked")
        _draw_eye_shocked(draw, lx, ey)
        _draw_eye_shocked(draw, rx, ey)
        draw.ellipse([214, 316, 298, 405], fill=(165, 35, 50, 255), outline=ink, width=12)

    elif expr == "angry":
        _draw_brows(draw, "angry")
        _draw_eye_normal(draw, lx, ey, rx=34, ry=38)
        _draw_eye_normal(draw, rx, ey, rx=34, ry=38)
        draw.rounded_rectangle([196, 320, 316, 368], radius=14, fill=(250, 250, 255, 255), outline=ink, width=10)
        for tx in (226, 256, 286):
            draw.line([(tx, 322), (tx, 366)], fill=ink, width=7)

    elif expr == "smirk":
        _draw_brows(draw, "smirk")
        _draw_eye_normal(draw, lx, ey, pupil_dx=8)
        _draw_eye_normal(draw, rx, ey, pupil_dx=8)
        _draw_thick_arc(draw, [215, 298, 322, 352], 10, 145, width=14)

    elif expr == "closed":
        _draw_brows(draw, "neutral")
        _draw_eye_closed(draw, lx, ey)
        _draw_eye_closed(draw, rx, ey)
        _draw_thick_arc(draw, [216, 310, 296, 352], 15, 165, width=12)

    elif expr == "blind":
        _draw_brows(draw, "sad")
        _draw_eye_blind(draw, lx, ey)
        _draw_eye_blind(draw, rx, ey)
        draw.line([(215, 342), (297, 342)], fill=ink, width=12)

    elif expr == "dizzy":
        _draw_brows(draw, "worried")
        for cx in (lx, rx):
            draw.ellipse([cx - 42, ey - 42, cx + 42, ey + 42], fill=(255, 255, 255, 255), outline=ink, width=10)
            draw.ellipse([cx - 24, ey - 24, cx + 24, ey + 24], outline=ink, width=8)
            draw.ellipse([cx - 8, ey - 8, cx + 8, ey + 8], fill=ink)
        draw.line([(205, 348), (235, 336), (265, 352), (305, 340)], fill=ink, width=12)

    elif expr == "talk_open":
        _draw_brows(draw, "neutral")
        _draw_eye_normal(draw, lx, ey)
        _draw_eye_normal(draw, rx, ey)
        draw.ellipse([212, 318, 300, 382], fill=(175, 45, 60, 255), outline=ink, width=11)

    elif expr == "monster_grin":
        # Glowing red eyes + huge jagged human-like grin
        for cx in (lx, rx):
            draw.ellipse([cx - 38, ey - 38, cx + 38, ey + 38], fill=(255, 25, 25, 255), outline=(10, 0, 0, 255), width=10)
            draw.ellipse([cx - 10, ey - 10, cx + 10, ey + 10], fill=(255, 230, 120, 255))
        draw.rounded_rectangle([105, 295, 407, 425], radius=36, fill=(248, 240, 225, 255), outline=(15, 10, 10, 255), width=12)
        draw.line([(110, 360), (402, 360)], fill=(20, 10, 10, 255), width=9)
        for tx in range(145, 380, 38):
            draw.line([(tx, 300), (tx, 420)], fill=(25, 15, 15, 255), width=7)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")


def ensure_all_faces(target_dir: Path = FACES_DIR) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    for expr in EXPRESSION_LIST:
        generate_face(expr, target_dir / f"{expr}.png")
    return target_dir


if __name__ == "__main__":
    out = ensure_all_faces()
    print(f"Generated {len(EXPRESSION_LIST)} face decals in {out}")

