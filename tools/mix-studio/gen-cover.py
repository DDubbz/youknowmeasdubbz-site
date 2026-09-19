#!/usr/bin/env python3
"""Generate branded cover art for Dubbz mixes.
Usage: python3 tools/mix-studio/gen-cover.py "Mix Title" --subtitle "Venue" --genres hip-hop,rnb --output /tmp/cover.png
"""
import argparse
import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Brand colors — Dubbz dark + cyan + gold
NAVY = (15, 15, 26)
SURFACE = (26, 26, 46)
CYAN = (0, 212, 255)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
MUTED = (146, 146, 173)
DARK_MUTED = (90, 90, 120)


def font(size, bold=False):
    """Load a system font, falling back to default."""
    paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/SFProDisplay-Regular.otf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap(text, font_obj, max_width, draw):
    """Word-wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font_obj)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_height(text, font_obj, draw):
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    return bbox[3] - bbox[1]


def generate_cover(title, subtitle, genres, output_path, size=1200):
    img = Image.new("RGB", (size, size), NAVY)
    draw = ImageDraw.Draw(img)

    # Subtle radial gradient overlay (top-right accent)
    overlay = Image.new("L", (size, size), 0)
    odraw = ImageDraw.Draw(overlay)
    for y in range(size):
        t = max(0.0, 1.0 - y / (size * 0.9))
        odraw.line([(0, y), (size, y)], fill=int(255 * t * 0.6))
    accent = Image.new("RGB", (size, size), (0, 212, 255))
    img = Image.blend(img, accent, alpha=0.12)
    draw = ImageDraw.Draw(img)

    # Border
    margin = 48
    draw.rectangle([margin, margin, size - margin, size - margin],
                   outline=CYAN, width=6)

    # Inner gold accent line
    margin2 = margin + 18
    draw.rectangle([margin2, margin2, size - margin2, size - margin2],
                   outline=GOLD, width=2)

    # Genre pills at top
    pill_y = margin2 + 24
    pill_x = margin2 + 24
    pill_font = font(20)
    for g in genres[:4]:
        label = g.upper()
        bbox = draw.textbbox((0, 0), label, font=pill_font)
        w = bbox[2] - bbox[0] + 20
        h = bbox[3] - bbox[1] + 12
        draw.rounded_rectangle([pill_x, pill_y, pill_x + w, pill_y + h],
                               radius=16, outline=CYAN, width=2)
        draw.text((pill_x + 10, pill_y + 4), label, fill=CYAN, font=pill_font)
        pill_x += w + 12
        if pill_x > size - margin2 - 100:
            pill_x = margin2 + 24
            pill_y += h + 10

    # Main title
    title_font = font(130, bold=True)
    title_y = size // 2 - 180
    # Auto-shrink title if too long
    title_size = 130
    while title_size > 48:
        title_font = font(title_size, bold=True)
        bbox = draw.textbbox((0, 0), title, font=title_font)
        if bbox[2] - bbox[0] <= size - 80:
            break
        title_size -= 8

    title_lines = wrap(title, title_font, size - 80, draw)
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        x = (size - w) // 2
        draw.text((x, title_y), line, fill=WHITE, font=title_font)
        title_y += text_height(line, title_font, draw) + 12

    # Subtitle (venue/event name)
    sub_y = title_y  # default if no subtitle
    if subtitle:
        sub_y = title_y + 20
        sub_font = font(42, bold=True)
        sub_lines = wrap(subtitle, sub_font, size - 120, draw)
        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=sub_font)
            w = bbox[2] - bbox[0]
            x = (size - w) // 2
            draw.text((x, sub_y), line, fill=CYAN, font=sub_font)
            sub_y += text_height(line, sub_font, draw) + 8

    # Bottom branding bar
    bar_h = 80
    bar_y = size - margin - bar_h
    draw.rectangle([margin, bar_y, size - margin, size - margin],
                   outline=CYAN, width=2)

    brand_font = font(28, bold=True)
    draw.text((size // 2, bar_y + 20), "YOUKNOWMEASDUBBZ.COM",
              fill=CYAN, font=brand_font, anchor="mm")

    dj_font = font(22)
    draw.text((size // 2, bar_y + 55), "DUBBZ",
              fill=GOLD, font=dj_font, anchor="mm")

    # Save
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"Cover generated: {output_path} ({os.path.getsize(output_path)} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Generate Dubbz mix cover art")
    parser.add_argument("title", help="Mix title")
    parser.add_argument("--subtitle", default="", help="Venue or event name")
    parser.add_argument("--genres", default="", help="Comma-separated genre tags")
    parser.add_argument("--output", required=True, help="Output PNG path")
    args = parser.parse_args()

    genres = [g.strip() for g in args.genres.split(",") if g.strip()] if args.genres else []
    generate_cover(args.title, args.subtitle, genres, args.output)


if __name__ == "__main__":
    main()
