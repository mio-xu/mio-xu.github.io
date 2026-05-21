#!/usr/bin/env python3
"""
扫描 images/cities/，自动重命名照片为 1.jpeg/2.jpeg/...，并生成 photos.json。

文件夹结构（两种均支持）：
  有街道（东京/巴黎等）: images/cities/{city}/{street}/{YYYY-MM-DD}/photo.jpg
  无街道（武汉/广州等）: images/cities/{city}/{YYYY-MM-DD}/photo.jpg

日期文件夹必须为 YYYY-MM-DD 格式。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
CITIES_DIR = ROOT / "images" / "cities"
OUTPUT = ROOT / "photos.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def is_date(name):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", name))

def fmt_date(d):
    return d.replace("-", ".")

def rename_in_folder(date_dir):
    """把文件夹内照片按文件名排序，重命名为 1.jpeg / 2.jpeg ..."""
    imgs = sorted([f for f in date_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS])
    renamed = []
    for i, img in enumerate(imgs, 1):
        target = date_dir / f"{i}{img.suffix.lower()}"
        if img != target:
            # 避免同名冲突：先移到临时名再改回
            tmp = date_dir / f"__tmp_{i}{img.suffix.lower()}"
            img.rename(tmp)
            renamed.append((tmp, target))
        else:
            renamed.append((img, img))
    for tmp, target in renamed:
        if tmp != target:
            tmp.rename(target)
    return [target for _, target in renamed]

result = {}
total_renamed = 0

if CITIES_DIR.exists():
    for city_path in sorted(CITIES_DIR.iterdir()):
        if not city_path.is_dir():
            continue
        city = city_path.name
        photos = []

        for level1 in sorted(city_path.iterdir()):
            if not level1.is_dir():
                continue
            name1 = level1.name

            if is_date(name1):
                # 无街道：city/YYYY-MM-DD/
                final_imgs = rename_in_folder(level1)
                total_renamed += len(final_imgs)
                date = fmt_date(name1)
                for img in final_imgs:
                    photos.append({
                        "src": str(img.relative_to(ROOT)).replace("\\", "/"),
                        "location": "",
                        "date": date,
                    })
            else:
                # 有街道：city/street/YYYY-MM-DD/
                street = name1
                for date_path in sorted(level1.iterdir()):
                    if not date_path.is_dir() or not is_date(date_path.name):
                        continue
                    final_imgs = rename_in_folder(date_path)
                    total_renamed += len(final_imgs)
                    date = fmt_date(date_path.name)
                    for img in final_imgs:
                        photos.append({
                            "src": str(img.relative_to(ROOT)).replace("\\", "/"),
                            "location": street,
                            "date": date,
                        })

        result[city] = photos

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

total = sum(len(v) for v in result.values())
print(f"photos.json 已生成：{total} 张照片，{len(result)} 个城市")
