#!/usr/bin/env python3
"""Validate that the final paper-reading report embeds key figures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import extract_arxiv_id


IMAGE_MARKDOWN_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)\n]+)\)")
RENDERABLE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

ROLE_KEYWORDS = [
    (
        "failure_case",
        [
            "failure",
            "fail",
            "error case",
            "limitation",
            "negative example",
            "失败",
            "错误案例",
            "边界",
            "局限",
        ],
    ),
    (
        "ablation",
        [
            "ablation",
            "sensitivity",
            "component study",
            "analysis",
            "消融",
            "敏感性",
            "组件分析",
        ],
    ),
    (
        "model_architecture",
        [
            "architecture",
            "network",
            "backbone",
            "model structure",
            "model architecture",
            "structure",
            "架构",
            "网络结构",
            "模型结构",
        ],
    ),
    (
        "method_overview",
        [
            "overview",
            "pipeline",
            "framework",
            "overall",
            "model",
            "method",
            "workflow",
            "系统框架",
            "模型",
            "方法",
            "流程",
            "总览",
            "框架",
        ],
    ),
    (
        "module_detail",
        [
            "module",
            "block",
            "component",
            "encoder",
            "decoder",
            "layer",
            "attention",
            "模块",
            "组件",
            "编码器",
            "解码器",
        ],
    ),
    (
        "main_result",
        [
            "result",
            "benchmark",
            "performance",
            "comparison",
            "evaluation",
            "experiment",
            "主结果",
            "实验结果",
            "性能",
            "对比",
        ],
    ),
    (
        "qualitative",
        [
            "qualitative",
            "visualization",
            "visualisation",
            "example",
            "prediction",
            "generation",
            "定性",
            "可视化",
            "示例",
            "预测",
            "生成",
        ],
    ),
    (
        "problem_setup",
        [
            "task",
            "problem",
            "setup",
            "setting",
            "dataset",
            "scenario",
            "任务",
            "问题设定",
            "设置",
            "场景",
        ],
    ),
]

REQUIRED_ROLES = {
    "method_overview",
    "model_architecture",
    "module_detail",
    "main_result",
    "ablation",
    "failure_case",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that {arxiv_id}/{arxiv_id}_阅读报告.md embeds key figures "
            "listed in cache/images_manifest.json."
        )
    )
    parser.add_argument("--input", help="Original arXiv URL or ID used by run_pipeline.sh")
    parser.add_argument("--root", default=".", help="Workspace root containing {arxiv_id}/")
    parser.add_argument("--manifest", help="Explicit path to cache/images_manifest.json")
    parser.add_argument("--report", help="Explicit path to the final Markdown report")
    return parser.parse_args()


def normalize_markdown_path(path: str, workspace: Path | None = None) -> str:
    value = unquote(path.strip()).strip("<>")
    if " " in value and not Path(value).exists():
        value = value.split()[0]
    value = value.split("#", 1)[0].split("?", 1)[0]
    value = value.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]

    candidate = Path(value)
    if workspace and candidate.is_absolute():
        try:
            value = candidate.resolve().relative_to(workspace.resolve()).as_posix()
        except ValueError:
            value = candidate.as_posix()
    return value


def resolve_default_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    if args.manifest and args.report:
        manifest_path = Path(args.manifest).resolve()
        report_path = Path(args.report).resolve()
        return manifest_path, report_path, report_path.parent

    if not args.input:
        raise SystemExit("Validation failed: provide --input, or provide both --manifest and --report.")

    parsed = extract_arxiv_id(args.input)
    if not parsed:
        raise SystemExit(f"Validation failed: could not parse arXiv id from input: {args.input}")

    arxiv_id, _version = parsed
    workspace = Path(args.root).resolve() / arxiv_id
    manifest_path = Path(args.manifest).resolve() if args.manifest else workspace / "cache" / "images_manifest.json"
    report_path = Path(args.report).resolve() if args.report else workspace / f"{arxiv_id}_阅读报告.md"
    return manifest_path, report_path, workspace


def read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Validation failed: missing image manifest: {path}")

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    figures = payload.get("figures", []) if isinstance(payload, dict) else []
    return [item for item in figures if isinstance(item, dict)]


def figure_path(figure: dict) -> str:
    return str(figure.get("saved_path") or figure.get("path") or "").strip()


def figure_search_text(figure: dict) -> str:
    parts = [
        figure_path(figure),
        str(figure.get("caption") or ""),
        str(figure.get("section_hint") or ""),
        str(figure.get("label") or ""),
        str(figure.get("original_file") or ""),
        str(figure.get("graphics_target") or ""),
    ]
    return " ".join(parts).lower()


def classify_figure(figure: dict) -> str:
    search_text = figure_search_text(figure)
    for role, keywords in ROLE_KEYWORDS:
        if any(keyword.lower() in search_text for keyword in keywords):
            return role
    return "other"


def resolve_figure_file(path: str, workspace: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return workspace / path


def is_renderable_existing_figure(path: str, workspace: Path) -> bool:
    if not path or Path(path).suffix.lower() not in RENDERABLE_IMAGE_EXTENSIONS:
        return False
    return resolve_figure_file(path, workspace).exists()


def embedded_image_paths(report_text: str, workspace: Path) -> set[str]:
    paths: set[str] = set()
    for match in IMAGE_MARKDOWN_PATTERN.finditer(report_text):
        paths.add(normalize_markdown_path(match.group(1), workspace))
    return paths


def build_required_candidates(figures: list[dict], workspace: Path) -> tuple[list[dict], int]:
    required: list[dict] = []
    renderable_count = 0

    for figure in figures:
        raw_path = figure_path(figure)
        normalized_path = normalize_markdown_path(raw_path, workspace)
        if not is_renderable_existing_figure(normalized_path, workspace):
            continue

        renderable_count += 1
        role = classify_figure(figure)
        if role not in REQUIRED_ROLES:
            continue

        required.append(
            {
                "path": normalized_path,
                "role": role,
                "caption": str(figure.get("caption") or "").strip(),
                "section_hint": str(figure.get("section_hint") or "").strip(),
                "original_file": str(figure.get("original_file") or "").strip(),
            }
        )

    return required, renderable_count


def main() -> int:
    args = parse_args()
    manifest_path, report_path, workspace = resolve_default_paths(args)

    figures = read_manifest(manifest_path)
    if not figures:
        print(f"OK: no extracted figures found in {manifest_path}; no figure coverage check possible.")
        return 0

    if not report_path.exists():
        raise SystemExit(f"Validation failed: missing report: {report_path}")

    report_text = report_path.read_text(encoding="utf-8-sig")
    embedded_paths = embedded_image_paths(report_text, workspace)
    required, renderable_count = build_required_candidates(figures, workspace)

    if renderable_count == 0:
        print(
            "OK: no renderable extracted figures were found; "
            f"manifest={manifest_path} report={report_path}"
        )
        return 0

    if not required:
        print(
            "OK: no verifiable key figures were detected in the manifest; "
            f"renderable_figures={renderable_count} report_images={len(embedded_paths)}"
        )
        return 0

    missing = [figure for figure in required if figure["path"] not in embedded_paths]
    if missing:
        print("Validation failed: key figures are missing from the report.", file=sys.stderr)
        print(f"- report: {report_path}", file=sys.stderr)
        print(f"- manifest: {manifest_path}", file=sys.stderr)
        for figure in missing:
            print(
                f"- [{figure['role']}] {figure['path']} | "
                f"caption={figure['caption'] or '<empty>'} | "
                f"section={figure['section_hint'] or '<empty>'} | "
                f"original={figure['original_file'] or '<empty>'}",
                file=sys.stderr,
            )
        print(
            "Insert each missing key figure near the relevant analysis section, "
            "then add 1-3 explanatory sentences after it.",
            file=sys.stderr,
        )
        return 1

    print(
        "OK: report embeds all detected key figures "
        f"({len(required)} required, {len(embedded_paths)} markdown image(s))."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
