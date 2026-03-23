"""Validate that a generated paper-reading report embeds figures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_report import collect_embeddable_figures, normalize_markdown_path


IMAGE_MARKDOWN_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate that report.md embeds figures from artifacts.json.")
    parser.add_argument("--artifacts", required=True, help="Path to outputs/<paper_id>/artifacts.json")
    parser.add_argument("--report", required=True, help="Path to outputs/<paper_id>/report.md")
    return parser.parse_args()


def strip_relative_prefix(path: str) -> str:
    normalized = normalize_markdown_path(path).strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def main() -> int:
    args = parse_args()
    artifacts_path = Path(args.artifacts).resolve()
    report_path = Path(args.report).resolve()

    artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
    report_text = report_path.read_text(encoding="utf-8")

    embeddable_figures = collect_embeddable_figures(artifacts)
    if not embeddable_figures:
        raise SystemExit(
            f"Validation failed: no embeddable figures found in artifacts.json: {artifacts_path}"
        )

    embedded_paths = {
        strip_relative_prefix(match.group(1))
        for match in IMAGE_MARKDOWN_PATTERN.finditer(report_text)
    }
    if not embedded_paths:
        raise SystemExit(f"Validation failed: report contains no markdown images: {report_path}")

    expected_paths = {
        strip_relative_prefix(str(figure["path"]))
        for figure in embeddable_figures
    }
    if embedded_paths.isdisjoint(expected_paths):
        raise SystemExit(
            "Validation failed: report embeds images, but none match the figure paths from artifacts.json. "
            f"report={report_path} artifacts={artifacts_path}"
        )

    print(
        "Validation passed: report embeds figures "
        f"({len(embedded_paths)} markdown image(s), {len(expected_paths)} embeddable artifact figure(s))."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
