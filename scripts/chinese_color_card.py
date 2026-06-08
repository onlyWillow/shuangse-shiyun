#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


PALETTE = [
    ("雪白", "#fffef9"),
    ("鱼肚白", "#f7f4ed"),
    ("月白", "#d6ecf0"),
    ("霜色", "#e9f1f6"),
    ("浅云", "#eaedf1"),
    ("银灰", "#e3e2e4"),
    ("苍白", "#d1d9e0"),
    ("云水蓝", "#baccd9"),
    ("井天蓝", "#c3d7df"),
    ("晴山蓝", "#8fb2c9"),
    ("远山紫", "#ccccd6"),
    ("青白", "#c0ebd7"),
    ("素", "#e0f0e9"),
    ("缟", "#f2ecde"),
    ("米汤娇", "#eeead9"),
    ("瓦罐灰", "#47484c"),
    ("银鼠灰", "#b5aa90"),
    ("墨灰", "#758a99"),
]

FONT_CANDIDATES = {
    "songti": [
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
    ],
    "kaiti": [
        "/System/Library/Fonts/Supplemental/Kaiti.ttc",
        "/System/Library/Fonts/Supplemental/Kai.ttf",
    ],
    "heiti": [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ],
    "pingfang": [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ],
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6-digit hex color, got {value!r}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def srgb_to_linear(channel: float) -> float:
    channel /= 255.0
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = [srgb_to_linear(c) for c in rgb]
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    x, y, z = x / 0.95047, y / 1.0, z / 1.08883

    def f(v: float) -> float:
        if v > 0.008856:
            return v ** (1 / 3)
        return 7.787 * v + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def nearest_color_name(rgb: tuple[int, int, int]) -> tuple[str, str, float]:
    lab = rgb_to_lab(rgb)
    best: tuple[str, str, float] | None = None
    for name, hex_value in PALETTE:
        candidate_lab = rgb_to_lab(hex_to_rgb(hex_value))
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(lab, candidate_lab)))
        if best is None or dist < best[2]:
            best = (name, hex_value, dist)
    assert best is not None
    return best


def extract_core_color(image: Image.Image) -> tuple[int, int, int]:
    small = image.convert("RGB").resize((180, 120), Image.Resampling.LANCZOS)
    quantized = small.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    counts = sorted(quantized.getcolors(), reverse=True)
    idx = counts[0][1]
    return tuple(palette[idx * 3:idx * 3 + 3])


def pick_font(style: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_CANDIDATES.get(style, []) + [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def centered_text(draw: ImageDraw.ImageDraw, size: tuple[int, int], text: str, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = (size[0] - width) / 2 - bbox[0]
    y = (size[1] - height) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Chinese traditional color card and concatenate it with an image.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--orientation", choices=["vertical", "horizontal"], default="vertical")
    parser.add_argument("--card-position", choices=["top", "bottom", "left", "right"], default="top")
    parser.add_argument("--font-style", choices=sorted(FONT_CANDIDATES), default="songti")
    parser.add_argument("--font-size", type=int)
    parser.add_argument("--font-scale", type=float, default=0.0625)
    parser.add_argument("--color-name")
    parser.add_argument("--core-hex")
    parser.add_argument("--text-hex", default="#373D42")
    parser.add_argument("--basename", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    original = Image.open(args.image).convert("RGB")
    core = hex_to_rgb(args.core_hex) if args.core_hex else extract_core_color(original)
    matched_name, matched_hex, distance = nearest_color_name(core)
    name = args.color_name or matched_name
    font_size = args.font_size or max(28, round(original.width * args.font_scale))
    font = pick_font(args.font_style, font_size)
    text_color = hex_to_rgb(args.text_hex)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.basename or args.image.stem
    card_path = args.out_dir / f"{stem}_color_card.png"
    joined_path = args.out_dir / f"{stem}_color_card_joined.png"

    card = Image.new("RGB", original.size, core)
    centered_text(ImageDraw.Draw(card), original.size, name, font, text_color)
    card.save(card_path, "PNG")

    if args.orientation == "vertical":
        if args.card_position not in {"top", "bottom"}:
            raise ValueError("vertical orientation requires --card-position top or bottom")
        joined = Image.new("RGB", (original.width, original.height * 2))
        if args.card_position == "top":
            joined.paste(card, (0, 0))
            joined.paste(original, (0, original.height))
            original_region = np.asarray(joined)[original.height:, :, :]
        else:
            joined.paste(original, (0, 0))
            joined.paste(card, (0, original.height))
            original_region = np.asarray(joined)[:original.height, :, :]
    else:
        if args.card_position not in {"left", "right"}:
            raise ValueError("horizontal orientation requires --card-position left or right")
        joined = Image.new("RGB", (original.width * 2, original.height))
        if args.card_position == "left":
            joined.paste(card, (0, 0))
            joined.paste(original, (original.width, 0))
            original_region = np.asarray(joined)[:, original.width:, :]
        else:
            joined.paste(original, (0, 0))
            joined.paste(card, (original.width, 0))
            original_region = np.asarray(joined)[:, :original.width, :]

    joined.save(joined_path, "PNG")
    identical = bool(np.array_equal(np.asarray(original), original_region))

    print(f"image_size={original.size[0]}x{original.size[1]}")
    print(f"core_rgb={core}")
    print(f"core_hex={rgb_to_hex(core)}")
    print(f"matched_name={matched_name}")
    print(f"matched_hex={matched_hex.upper()}")
    print(f"match_delta_e={distance:.2f}")
    print(f"rendered_name={name}")
    print(f"card_path={card_path}")
    print(f"joined_path={joined_path}")
    print(f"original_region_pixels_identical={identical}")
    return 0 if identical else 2


if __name__ == "__main__":
    raise SystemExit(main())
