#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 雨落有声.html（开发版，外链 design/story_data.js 与 assets/ 图片）
打包成单文件版 雨落有声_单文件.html：
  - design/story_data.js -> 内联 <script>
  - SPRITE_URLS.zhiwei / .jiangyan -> base64 data URI
  - SPRITE_CG.bonus（彩蛋图）        -> base64 data URI
  - story_data.js 里 SPRITES[*].src  与 ENDINGS.bonus.cg -> base64 data URI
打包后文件不含任何 "assets/" 引用，可直接双击打开或丢到任意静态托管。
用法: python build_single.py [--also-dist]
"""
import base64, mimetypes, os, re, sys, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_HTML = os.path.join(ROOT, "雨落有声.html")
SRC_DATA = os.path.join(ROOT, "design", "story_data.js")
OUT_HTML = os.path.join(ROOT, "雨落有声_单文件.html")
DIST_DIR = os.path.join(ROOT, "dist")


def data_uri(rel_path):
    """把相对路径（assets/xxx.png）读成 data:image/...;base64,..."""
    abs_path = os.path.join(ROOT, rel_path.replace("/", os.sep))
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"资源不存在: {abs_path}")
    mime, _ = mimetypes.guess_type(abs_path)
    if mime is None:
        ext = os.path.splitext(abs_path)[1].lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".webp": "image/webp"}.get(ext, "application/octet-stream")
    with open(abs_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def inline_asset_refs(text, label):
    """把 text 里所有 'assets/xxx.ext' 字符串替换成对应的 data URI。"""
    pattern = re.compile(r"""(['"])(assets/[A-Za-z0-9_./\-]+\.(?:png|jpg|jpeg|webp))\1""")
    cache = {}

    def repl(m):
        quote, rel = m.group(1), m.group(2)
        if rel not in cache:
            cache[rel] = data_uri(rel)
            print(f"  [{label}] 内联 {rel}  ({len(cache[rel])//1024} KB)")
        return quote + cache[rel] + quote

    return pattern.sub(repl, text)


def build():
    with open(SRC_HTML, encoding="utf-8") as f:
        html = f.read()
    with open(SRC_DATA, encoding="utf-8") as f:
        data = f.read()

    print("1) 内联 story_data.js")
    tag = '<script src="design/story_data.js"></script>'
    if tag not in html:
        raise RuntimeError("找不到 story_data.js 的 script 标签，请检查源文件")
    html = html.replace(tag, "<script>\n" + data + "\n</script>")

    print("2) 内联图片资源（引擎里的 SPRITE_URLS / SPRITE_CG）")
    html = inline_asset_refs(html, "引擎")
    print("3) 内联剧情数据里的图片资源（SPRITES / ENDINGS.cg）")
    html = inline_asset_refs(html, "数据")

    left = html.count("assets/")
    print(f"4) 检查残留 'assets/' 引用: {left}")
    if left:
        for m in re.finditer(r".{40}assets/.{40}", html):
            print("   ! " + m.group(0).replace("\n", " "))
        raise RuntimeError("仍有未内联的资源引用")

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    size_mb = os.path.getsize(OUT_HTML) / 1024 / 1024
    print(f"完成: {OUT_HTML}  ({size_mb:.2f} MB)")

    if "--also-dist" in sys.argv:
        os.makedirs(DIST_DIR, exist_ok=True)
        shutil.copyfile(OUT_HTML, os.path.join(DIST_DIR, "index.html"))
        print(f"已复制到: {os.path.join(DIST_DIR, 'index.html')}")

    return OUT_HTML


if __name__ == "__main__":
    build()
