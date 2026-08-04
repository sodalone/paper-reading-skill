#!/usr/bin/env python3
import argparse
from pathlib import Path

from common import get_workspace, read_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the canonical understanding-first report skeleton.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--template")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace, ids = get_workspace(root, args.input)
    metadata = read_json(workspace / "metadata.json")
    report_path = workspace / f"{ids['arxiv_id']}_阅读报告.md"
    template_path = (
        Path(args.template).resolve()
        if args.template
        else Path(__file__).resolve().parents[1] / "templates" / "report_template.md"
    )

    replacements = {
        "{{PAPER_TITLE}}": metadata.get("title") or "论文标题待核对",
        "{{ORIGINAL_ABS_URL}}": f"https://arxiv.org/abs/{metadata['arxiv_id']}",
        "{{PAPER_ID_WITH_VERSION}}": metadata["paper_id_with_version"],
        "{{ARXIV_ABS_URL}}": metadata["arxiv_abs_url"],
        "{{HJFY_URL}}": metadata["hjfy_url"],
        "{{PAPERS_COOL_URL}}": metadata["papers_cool_url"],
    }

    rendered = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        rendered = rendered.replace(key, str(value))

    unresolved = sorted(
        token for token in replacements if token in rendered
    )
    if unresolved:
        raise ValueError(f"Unresolved report template placeholders: {unresolved}")

    report_path.write_text(rendered, encoding="utf-8")
    print(f"Report skeleton created: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
