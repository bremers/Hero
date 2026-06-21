"""Generate a GIF of Hero pulsing with a speech balloon."""

import math

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 360, 280
FRAMES = 40
BODY_COLOR = (74, 144, 217)
BODY_OUTLINE = (44, 95, 138)
EYE_WHITE = (255, 255, 255)
PUPIL = (26, 26, 46)
BG = (13, 17, 23)  # GitHub dark theme background
BALLOON_BG = (255, 255, 255)
BALLOON_TEXT = (30, 30, 30)
BALLOON_OUTLINE = (180, 180, 180)

GREETING = "Hi, it's Hero!\nWanna hear a joke?"


def draw_frame(tick: int) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    cx, cy = 130, 170
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
    bx, by = 220, 20
    bw, bh = 130, 65
    border_r = 12

    # Balloon body
    draw.rounded_rectangle(
        [bx, by, bx + bw, by + bh],
        radius=border_r,
        fill=BALLOON_BG,
        outline=BALLOON_OUTLINE,
        width=1,
    )

    # Balloon tail (triangle pointing to Hero)
    tail_points = [(bx + 10, by + bh), (bx - 5, by + bh + 15), (bx + 30, by + bh)]
    draw.polygon(tail_points, fill=BALLOON_BG, outline=BALLOON_BG)
    draw.line([tail_points[0], tail_points[1]], fill=BALLOON_OUTLINE, width=1)
    draw.line([tail_points[1], tail_points[2]], fill=BALLOON_OUTLINE, width=1)

    # Text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 14)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except OSError:
            font = ImageFont.load_default()

    lines = GREETING.split("\n")
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = bx + (bw - tw) // 2
        ty = by + 12 + i * 22
        draw.text((tx, ty), line, fill=BALLOON_TEXT, font=font)

    return img


frames = [draw_frame(t) for t in range(FRAMES)]

output = "assets/hero.gif"
import os

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
