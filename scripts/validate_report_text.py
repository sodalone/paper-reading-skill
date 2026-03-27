#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from common import get_workspace


SUSPICIOUS_TOKENS = [
    "璁烘枃",
    "闃呰",
    "鍩烘湰",
    "闄勫綍",
    "寰呰ˉ",
    "鏈枃",
    "鏂囩尞",
    "锛",
]


def count_private_use_chars(text: str) -> int:
    return sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)


def build_report_path(root: Path, input_text: str) -> Path:
    workspace, ids = get_workspace(root, input_text)
    return workspace / f"{ids['arxiv_id']}_阅读报告.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    report_path = build_report_path(Path(args.root).resolve(), args.input)
    text = report_path.read_text(encoding="utf-8-sig")

    suspicious_counts = {token: text.count(token) for token in SUSPICIOUS_TOKENS if token in text}
    private_use_count = count_private_use_chars(text)
    replacement_count = text.count("\ufffd")

    has_problem = private_use_count > 0 or replacement_count > 0 or sum(suspicious_counts.values()) >= 3
    if not has_problem:
        print(f"OK: {report_path} looks UTF-8 clean.")
        return 0

    print(f"ERROR: {report_path} looks mojibaked or encoding-corrupted.", file=sys.stderr)
    if private_use_count:
        print(f"- Private-use characters: {private_use_count}", file=sys.stderr)
    if replacement_count:
        print(f"- Replacement characters: {replacement_count}", file=sys.stderr)
    if suspicious_counts:
        print("- Suspicious token counts:", file=sys.stderr)
        for token, count in suspicious_counts.items():
            print(f"  - {token}: {count}", file=sys.stderr)
    print(
        "- Hint: on Windows PowerShell, set UTF-8 first with `. ./scripts/windows_utf8.ps1` "
        "and avoid copying Chinese text from a garbled console back into the report.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
