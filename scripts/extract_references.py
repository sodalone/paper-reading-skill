#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

from bs4 import BeautifulSoup
from common import get_workspace, write_json


def parse_references_from_ar5iv(html: str):
    soup = BeautifulSoup(html, "html.parser")
    refs = []
    for li in soup.find_all(["li", "p"]):
        txt = li.get_text(" ", strip=True)
        if len(txt) > 50 and re.search(r"\b(19|20)\d{2}\b", txt):
            refs.append(txt)

    seen = set()
    out = []
    for x in refs:
        key = re.sub(r"\s+", " ", x)
        if key not in seen:
            seen.add(key)
            out.append({"raw_text": x})
    return out[:150]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace, _ = get_workspace(root, args.input)
    ar5iv_path = workspace / "raw" / "ar5iv.html"

    refs = []
    source = "none"
    if ar5iv_path.exists():
        html = ar5iv_path.read_text(encoding="utf-8", errors="ignore")
        refs = parse_references_from_ar5iv(html)
        if refs:
            source = "ar5iv_html"

    payload = {
        "source": source,
        "count": len(refs),
        "items": refs,
        "note": "仅为中间提取结果。最终使用到的外部文献，必须写入主报告正文和附录 B。",
    }
    write_json(workspace / "cache" / "references.json", payload)
    print("Extracted references:", len(refs))


if __name__ == "__main__":
    main()
