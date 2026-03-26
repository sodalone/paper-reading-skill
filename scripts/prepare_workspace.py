#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path

from common import ensure_workspace, resolve_ids, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    ids = resolve_ids(args.input)
    root = Path(args.root).resolve()
    workspace = ensure_workspace(root, ids["arxiv_id"])

    metadata = {
        **ids,
        "workspace": str(workspace),
        "report_path": str(workspace / f'{ids["arxiv_id"]}_阅读报告.md'),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "internal_status": {
            "hjfy_visit_status": "未尝试",
            "papers_cool_rel_status": "未尝试",
        },
        "paths": {
            "raw_abs_html": str(workspace / "raw" / "abs.html"),
            "raw_pdf": str(workspace / "raw" / "paper.pdf"),
            "raw_ar5iv_html": str(workspace / "raw" / "ar5iv.html"),
            "raw_hjfy_html": str(workspace / "raw" / "hjfy.html"),
            "raw_papers_cool_html": str(workspace / "raw" / "papers_cool.html"),
            "cache_references_json": str(workspace / "cache" / "references.json"),
            "cache_images_manifest": str(workspace / "cache" / "images_manifest.json"),
        },
    }
    write_json(workspace / "metadata.json", metadata)
    print(workspace)
    print(metadata["report_path"])


if __name__ == "__main__":
    main()
