#!/usr/bin/env python3
import argparse
from pathlib import Path

from common import get_workspace, http_get, read_json, write_json


def save_response(url: str, path: Path, binary: bool = False):
    try:
        r = http_get(url)
        r.raise_for_status()
        if binary:
            path.write_bytes(r.content)
        else:
            path.write_text(r.text, encoding="utf-8")
        return {"ok": True, "status_code": r.status_code, "url": url}
    except Exception as e:
        path.write_text(f"FETCH FAILED: {url}\n{e}\n", encoding="utf-8")
        return {"ok": False, "error": str(e), "url": url}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace, ids = get_workspace(root, args.input)
    metadata_path = workspace / "metadata.json"
    metadata = read_json(metadata_path)

    results = {}
    results["arxiv_abs"] = save_response(ids["arxiv_abs_url"], workspace / "raw" / "abs.html")
    results["arxiv_pdf"] = save_response(ids["arxiv_pdf_url"], workspace / "raw" / "paper.pdf", binary=True)
    results["ar5iv"] = save_response(ids["ar5iv_url"], workspace / "raw" / "ar5iv.html")
    results["hjfy"] = save_response(ids["hjfy_url"], workspace / "raw" / "hjfy.html")
    results["papers_cool"] = save_response(ids["papers_cool_url"], workspace / "raw" / "papers_cool.html")

    metadata["fetch_results"] = results
    metadata["internal_status"]["hjfy_visit_status"] = (
        "已尝试访问"
        if results["hjfy"]["ok"] else f'访问失败：{results["hjfy"].get("error", "unknown error")}'
    )
    metadata["internal_status"]["papers_cool_rel_status"] = (
        "已访问论文页，REL 结果待后续核实"
        if results["papers_cool"]["ok"] else f'访问失败：{results["papers_cool"].get("error", "unknown error")}'
    )
    write_json(metadata_path, metadata)
    print("Fetched sources into", workspace)


if __name__ == "__main__":
    main()
