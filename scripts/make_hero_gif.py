"""Generate a GIF of Hero pulsing with a speech balloon."""

import math
import os

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 400, 280
FRAMES = 40
BODY_COLOR = (74, 144, 217)
BODY_OUTLINE = (44, 95, 138)
EYE_WHITE = (255, 255, 255)
PUPIL = (26, 26, 46)
BG = (255, 255, 255)
BALLOON_BG = (255, 255, 255)
BALLOON_TEXT = (30, 30, 30)
BALLOON_OUTLINE = (0, 0, 0)

GREETING = "Hi, it's Hero!\nWanna hear a joke?"


def _load_font() -> ImageFont.FreeTypeFont:
    for path in [
        "/System/Library/Fonts/Courier.dfont",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]:
        try:
            return ImageFont.truetype(path, 15)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_frame(tick: int, font: ImageFont.FreeTypeFont) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    cx, cy = 120, 170
    breath = 1.0 + 0.08 * math.sin(tick * (2 * math.pi / FRAMES))
    r = 60 * breath

    # Radiating rings
    for i in range(3):
        ring_phase = (tick + i * 12) % FRAMES
        ring_r = r + 5 + ring_phase * 1.2
        ring_alpha = max(0, 1.0 - ring_phase / FRAMES)
        if ring_alpha > 0 and ring_r < 140:
            blend_r = int(74 + (BG[0] - 74) * (1 - ring_alpha))
            blend_g = int(144 + (BG[1] - 144) * (1 - ring_alpha))
            blend_b = int(217 + (BG[2] - 217) * (1 - ring_alpha))
            draw.ellipse(
                [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
                outline=(blend_r, blend_g, blend_b),
                width=2,
            )

    # Body
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        fill=BODY_COLOR,
        outline=BODY_OUTLINE,
        width=3,
    )

    # Eyes
    eye_h = 10 * breath
    eye_w = 10 * breath
    for ex in [-18, 18]:
        draw.ellipse(
            [cx + ex - eye_w, cy - 12 - eye_h, cx + ex + eye_w, cy - 12 + eye_h],
            fill=EYE_WHITE,
        )
        pr = 5 * breath
        draw.ellipse(
            [cx + ex - pr, cy - 12 - pr, cx + ex + pr, cy - 12 + pr],
            fill=PUPIL,
        )

    # Mouth
    mouth_w = 12 * breath
    draw.arc(
        [cx - mouth_w, cy + 5, cx + mouth_w, cy + 25],
        start=20,
        end=160,
        fill=PUPIL,
        width=2,
    )

    # Speech balloon
    bx, by = 210, 15
    bw, bh = 175, 70
    border_r = 12

    draw.rounded_rectangle(
        [bx, by, bx + bw, by + bh],
        radius=border_r,
        fill=BALLOON_BG,
        outline=BALLOON_OUTLINE,
        width=2,
    )

    # Balloon tail
    tail_points = [(bx + 10, by + bh), (bx - 5, by + bh + 15), (bx + 30, by + bh)]
    draw.polygon(tail_points, fill=BALLOON_BG, outline=BALLOON_BG)
    draw.line([tail_points[0], tail_points[1]], fill=BALLOON_OUTLINE, width=2)
    draw.line([tail_points[1], tail_points[2]], fill=BALLOON_OUTLINE, width=2)
    # Cover the outline inside the balloon where tail meets body
    draw.line([(bx + 11, by + bh), (bx + 29, by + bh)], fill=BALLOON_BG, width=3)

    # Text
    lines = GREETING.split("\n")
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = bx + (bw - tw) // 2
        ty = by + 14 + i * 22
        draw.text((tx, ty), line, fill=BALLOON_TEXT, font=font)

    return img


font = _load_font()
frames = [draw_frame(t, font) for t in range(FRAMES)]

output = "assets/hero.gif"
os.makedirs("assets", exist_ok=True)
frames[0].save(
    output,
    save_all=True,
    append_images=frames[1:],
    duration=80,
    loop=0,
    optimize=True,
)
print(f"Saved {output} ({os.path.getsize(output)} bytes, {FRAMES} frames)")
