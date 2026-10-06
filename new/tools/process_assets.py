# -*- coding: utf-8 -*-
"""处理 new/assets 下 AI 生成的图：重命名、裁水印、立绘抠透明底。

路径以脚本自身位置为基准，整个项目可以随便挪盘/挪目录。
"""
import os, shutil
from collections import deque
from PIL import Image

# 本文件在 <项目>/new/tools/ 下，素材目录是同级往上两层的 new/assets
_HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(os.path.dirname(_HERE), "assets")
RAW = os.path.join(D, "_raw")

BG_MAP = [
    ("日系动画封面插画",              "bg_title.jpg"),
    ("日系动画插画_赛璐璐上色_电影感", "cg_kiss.jpg"),
    ("大学校园的湖边",                "bg_lake.jpg"),
    ("大学食堂内部",                  "bg_canteen.jpg"),
    ("摩天轮轿厢内部视角",            "bg_ferris.jpg"),
    ("水利工程系馆的顶楼天台",        "bg_rooftop.jpg"),
    ("空无一人的大学阶梯教室",        "bg_classroom.jpg"),
    ("空荡荡的大学教室",              "bg_empty_classroom.jpg"),
    ("雨夜里学校的老旧篮球场",        "bg_old_court.jpg"),
]
SPRITE_MAP = [
    ("11-34-02", "aq_cold.png"),
    ("11-35-06", "aq_awkward.png"),
    ("11-35-07", "aq_soft.png"),
    ("11-35-08", "aq_alarm.png"),
    ("11-36-17", "aq_teary.png"),
]

WATERMARK_CROP_BOTTOM = 80
WHITE_TOL = 34


def all_png():
    out = []
    for root, _, files in os.walk(D):
        if os.path.basename(root) == "_raw":
            continue
        for f in files:
            if f.startswith("_"):
                continue
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                out.append(os.path.join(root, f))
    return out


def find(key):
    for p in all_png():
        if key in os.path.basename(p):
            return p
    return None


def drop_white_bg(im):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    dq = deque()

    def nw(x, y):
        r, g, b, a = px[x, y]
        return a > 0 and r >= 255 - WHITE_TOL and g >= 255 - WHITE_TOL and b >= 255 - WHITE_TOL

    for x in range(w):
        for y in (0, h - 1):
            if nw(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1; dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if nw(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1; dq.append((x, y))

    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and nw(nx, ny):
                seen[ny * w + nx] = 1
                dq.append((nx, ny))

    for y in range(h):
        row = y * w
        for x in range(w):
            if seen[row + x]:
                px[x, y] = (255, 255, 255, 0)

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r, g, b, a = px[x, y]
            if a == 0 or r < 238 or g < 238 or b < 238:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if px[x + dx, y + dy][3] == 0:
                    px[x, y] = (r, g, b, 80)
                    break
    return im


def main():
    os.makedirs(RAW, exist_ok=True)
    used = set()
    n = 0

    for key, name in BG_MAP:
        src = find(key)
        if not src:
            print("  ! 未找到:", key); continue
        im = Image.open(src)
        w, h = im.size
        im = im.crop((0, 0, w, h - WATERMARK_CROP_BOTTOM))
        im.convert("RGB").save(os.path.join(D, name), "JPEG", quality=88)
        used.add(src); n += 1
        print(f"  {name:24s} {im.size}  <- {os.path.basename(src)[:24]}")

    for key, name in SPRITE_MAP:
        src = find(key)
        if not src:
            print("  ! 未找到片段:", key); continue
        im = drop_white_bg(Image.open(src))
        im.save(os.path.join(D, name), "PNG")
        used.add(src); n += 1
        print(f"  {name:24s} {im.size} 透明  <- ...{key}")

    for p in all_png():
        base = os.path.basename(p)
        if p in used or base in {n2 for _, n2 in BG_MAP} | {n2 for _, n2 in SPRITE_MAP}:
            continue
        shutil.move(p, os.path.join(RAW, base))

    if os.path.isdir(os.path.join(D, "aq_teary_raw")):
        try: os.rmdir(os.path.join(D, "aq_teary_raw"))
        except OSError: pass

    print(f"\n完成 {n} 个文件；原始图已移入 _raw/")


if __name__ == "__main__":
    main()
