---
name: shuangse-shiyun
description: Extract an image's core color, match it to a Chinese traditional color name, create a same-size pure color card with centered Chinese text, and losslessly concatenate the card with the original image. Use when Codex is asked to analyze an uploaded/photo image for its dominant or core color, retrieve or choose a Chinese-style/traditional Chinese color name, generate a labeled color swatch, or stitch a swatch with the original image horizontally or vertically.
---

# 霜色拾韵

## Workflow

Use this skill for image-to-color-card requests, especially Chinese prompts such as “提取核心颜色”, “中国风颜色名称”, “生成色卡”, “拼接图片”, “上下拼接”, or “左右拼接”.

1. Identify the input image path and desired layout.
2. If the user asks to “检索” or requires a verified color source, browse reputable Chinese traditional color references and cite them in the final response. Good starting points are `zhongguose.com` and `chinesecoloratlas.com`.
3. Run `scripts/chinese_color_card.py` to extract the core color, match the nearest Chinese traditional color, create the labeled card, and concatenate it with the original.
4. Save final deliverables as PNG by default. This preserves the original image's decoded pixels in the joined output and avoids another JPEG compression pass.
5. Verify output dimensions and pixel identity for the original-image region before responding.

## Script

Run from the skill folder or pass an absolute path to the script:

```bash
python3 scripts/chinese_color_card.py /path/to/image.jpeg \
  --out-dir /path/to/outputs \
  --orientation vertical \
  --card-position top \
  --font-style songti \
  --font-scale 0.0625
```

Useful options:

- `--orientation vertical` with `--card-position top|bottom` creates an up/down composition.
- `--orientation horizontal` with `--card-position left|right` creates a left/right composition.
- `--font-style songti|kaiti|heiti|pingfang` chooses a Chinese-capable system font when available.
- `--font-size 68` sets an explicit point size; otherwise `--font-scale` is multiplied by image width.
- `--color-name NAME` overrides the matched color name when online research determines a better name.
- `--core-hex '#D4D9E2'` overrides the extracted core color.

## Quality Bar

Always prefer a visually central, low-saturation cluster over tiny accent colors when the task asks for the image's “核心颜色”. For snowy, misty, or sky-heavy images, the largest pale cluster is often more representative than dark branches or small earth tones.

For “无损拼接”, do not resize the original image. Paste the decoded source pixels into a PNG canvas and confirm pixel equality for the original region. Report exact dimensions, selected RGB/hex value, matched name, and output file paths.

## References

Read `references/color-sources.md` when the user asks for source attribution or when the built-in palette's nearest name feels questionable.
