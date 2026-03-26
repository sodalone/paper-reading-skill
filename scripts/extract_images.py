#!/usr/bin/env python3
import argparse
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from common import get_workspace, write_json


def download(url: str, out: Path):
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "paper-reviewer-skill/final-v2"})
        r.raise_for_status()
        out.write_bytes(r.content)
        return True, ""
    except Exception as e:
        return False, str(e)


def parse_figures_from_ar5iv(html: str, base_url: str, out_dir: Path):
    soup = BeautifulSoup(html, "html.parser")
    figures = []
    idx = 1
    for fig in soup.find_all(["figure", "div"]):
        caption_tag = fig.find(["figcaption", "caption"])
        img = fig.find("img")
        if not img:
            continue
        src = img.get("src")
        if not src:
            continue
        caption = caption_tag.get_text(" ", strip=True) if caption_tag else f"Figure {idx}"
        full = urljoin(base_url, src)
        out_path = out_dir / f"figure_{idx:02d}.png"
        ok, err = download(full, out_path)
        figures.append({
            "index": idx,
            "caption": caption,
            "source_url": full,
            "saved_path": str(out_path.relative_to(out_dir.parent)),
            "suggested_sections": [
                "1.2 问题设定",
                "2.3 核心推导与算法构造",
                "3.3 实验结果的解释力度",
                "3.4 潜在未讨论因素",
            ],
            "download_ok": ok,
            "error": err,
        })
        idx += 1
    return figures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace, ids = get_workspace(root, args.input)
    img_dir = workspace / "images"
    ar5iv_path = workspace / "raw" / "ar5iv.html"

    figures = []
    if ar5iv_path.exists():
        html = ar5iv_path.read_text(encoding="utf-8", errors="ignore")
        figures = parse_figures_from_ar5iv(html, ids["ar5iv_url"], img_dir)

    payload = {
        "figures": figures,
        "note": "这些图片是插图候选。最终必须按上下文插入到主报告相关小节，不能集中堆到单独章节。",
    }
    write_json(workspace / "cache" / "images_manifest.json", payload)
    print("Image manifest saved:", workspace / "cache" / "images_manifest.json")


if __name__ == "__main__":
    main()
