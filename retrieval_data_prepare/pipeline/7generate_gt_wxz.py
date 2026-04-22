"""为 wxz 用例生成与 generate_content.py 相同风格的单字 content 图，并输出编号-字符 CSV。"""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# 编号与 gt 图一致（retrieval_data_prepare/cases/gt/{编号}.jpg）
ENTRIES: list[tuple[str, str]] = [
    ("0015", "璨"),
    ("0023", "霆"),
    ("0053", "鳞"),
    ("0055", "彎"),
    ("0065", "瘻"),
    ("0075", "秦"),
    ("3273", "赢"),
    ("3323", "諢"),
]

FONT_SIZE = 96
CANVAS = (128, 128)
BG = (255, 255, 255)
FG = (0, 0, 0)


def main() -> None:
    root = Path(__file__).resolve().parent
    font_path = root / "data" / "SourceHanSansSC-Regular.otf"
    out_img_dir = root / "retrieval_data_prepare" / "cases" / "content"
    out_csv = root / "retrieval_data_prepare" / "cases" / "wxz_gt_chars.csv"

    out_img_dir.mkdir(parents=True, exist_ok=True)

    font = ImageFont.truetype(str(font_path), FONT_SIZE)

    for num_id, char in ENTRIES:
        img = Image.new("RGB", CANVAS, color=BG)
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), char, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (CANVAS[0] - w) // 2 - bbox[0]
        y = (CANVAS[1] - h) // 2 - bbox[1]
        draw.text((x, y), char, font=font, fill=FG)
        img.save(out_img_dir / f"{num_id}.jpg")

    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["wxz", "编号", "字符"])
        for num_id, char in ENTRIES:
            w.writerow(["wxz", num_id, char])

    print(f"已写入 {len(ENTRIES)} 张图: {out_img_dir}")
    print(f"已写入 CSV: {out_csv}")


if __name__ == "__main__":
    main()
