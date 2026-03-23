#!/usr/bin/env python3
"""Build the single-file report scaffold for the paper-reading skill."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROLE_TITLES = {
    "overview": "总体结构图",
    "method_detail": "方法细节图",
    "stability_or_training": "训练稳定性图",
    "main_experiment": "主实验相关图",
    "qualitative": "定性结果图",
    "failure_case": "失败案例图（如有）",
}

ROLE_REVIEWER_NOTES = {
    "overview": "说明这张图如何帮助读者理解论文的整体结构、模块关系或核心主张。",
    "method_detail": "说明这张图对应的算法结构、训练流程或关键机制，以及它支撑哪条主张。",
    "stability_or_training": "说明这张图如何支撑训练稳定性、收敛性或某个关键消融结论。",
    "main_experiment": "说明这张图如何帮助解释主结果表中的关键优势或 benchmark 结论。",
    "qualitative": "说明这张图展示了哪些定性优势，以及它与定量结论是否一致。",
    "failure_case": "说明这张图暴露了哪些失败模式、边界条件或未被论文充分讨论的问题。",
}

FALLBACK_ROLE_ORDER = [
    "overview",
    "method_detail",
    "main_experiment",
    "stability_or_training",
    "qualitative",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build outputs/<paper_id>/report.md from artifacts.json.")
    parser.add_argument("--artifacts", required=True, help="Path to outputs/<paper_id>/artifacts.json")
    parser.add_argument("--context", help="Optional path to outputs/<paper_id>/report_context.json")
    parser.add_argument("--template", help="Optional template override.")
    parser.add_argument("--focus-areas", action="append", default=[], help="Comma or semicolon separated focus areas.")
    parser.add_argument("--baseline-papers", action="append", default=[], help="Comma or semicolon separated baseline papers.")
    return parser.parse_args()


def split_items(values: list[str]) -> list[str]:
    items: list[str] = []
    for value in values:
        for chunk in value.replace(";", ",").split(","):
            cleaned = chunk.strip()
            if cleaned:
                items.append(cleaned)
    return items


def render_list(items: list[str], fallback: str) -> str:
    return "、".join(items) if items else fallback


def format_link(label: str, url: str | None) -> str:
    if not url:
        return "N/A"
    return f"[{label}]({url})"


def load_json_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_inline_text(value: str | None, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", (value or "")).strip()
    if not text:
        return "当前未提取到可靠图注，请结合正文补写该图用途。"
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def infer_role_from_path(path: str, index: int = 0) -> str:
    lowered = path.lower()
    if any(token in lowered for token in ("failure", "fail")):
        return "failure_case"
    if any(token in lowered for token in ("qualitative", "visual")):
        return "qualitative"
    if any(token in lowered for token in ("plot", "curve", "training", "loss", "stability")):
        return "stability_or_training"
    if any(token in lowered for token in ("overview", "framework", "pipeline", "paradigm", "intro", "main_fig")):
        return "overview"
    if any(token in lowered for token in ("adapter", "architecture", "module", "method")):
        return "method_detail"
    if any(token in lowered for token in ("result", "benchmark", "surds", "navsim", "nudynamics")):
        return "main_experiment"
    if index < len(FALLBACK_ROLE_ORDER):
        return FALLBACK_ROLE_ORDER[index]
    return "main_experiment"


def fallback_caption_from_path(path: str) -> str:
    stem = Path(path).stem
    stem = re.sub(r"^fig-\d+-", "", stem)
    stem = stem.replace("-", " ").replace("_", " ").strip()
    return stem or "图片标题待补"


def build_fallback_figure_catalog(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    raw_candidates: list[str] = []

    for value in artifacts.get("selected_figures") or []:
        if isinstance(value, str):
            raw_candidates.append(value)
    if not raw_candidates:
        for item in artifacts.get("image_list") or []:
            if isinstance(item, dict) and item.get("path"):
                raw_candidates.append(str(item["path"]))
    if not raw_candidates:
        for path in artifacts.get("page_list") or []:
            raw_candidates.append(str(path))

    seen: set[str] = set()
    for index, path in enumerate(raw_candidates, start=1):
        if path in seen:
            continue
        seen.add(path)
        role = infer_role_from_path(path, index - 1)
        catalog.append(
            {
                "figure_id": f"fallback-{index:03d}",
                "path": path,
                "caption": fallback_caption_from_path(path),
                "label": "",
                "source_tex_file": "",
                "section_hint": "旧版 artifacts.json 缺少 figure_catalog，当前基于文件名或顺序做低置信度归位。",
                "placement_role": role,
                "placement_confidence": "low",
            }
        )
    return catalog


def normalize_figure_catalog(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = artifacts.get("figure_catalog")
    if isinstance(catalog, list) and catalog:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(catalog, start=1):
            if not isinstance(item, dict) or not item.get("path"):
                continue
            normalized.append(
                {
                    "figure_id": str(item.get("figure_id") or f"figure-{index:03d}"),
                    "path": str(item.get("path")),
                    "caption": str(item.get("caption") or ""),
                    "label": str(item.get("label") or ""),
                    "source_tex_file": str(item.get("source_tex_file") or ""),
                    "section_hint": str(item.get("section_hint") or ""),
                    "placement_role": str(item.get("placement_role") or infer_role_from_path(str(item.get("path")), index - 1)),
                    "placement_confidence": str(item.get("placement_confidence") or "high"),
                }
            )
        if normalized:
            return normalized
    return build_fallback_figure_catalog(artifacts)


def group_figures_by_role(artifacts: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {role: [] for role in ROLE_TITLES}
    for figure in normalize_figure_catalog(artifacts):
        role = figure["placement_role"]
        if role not in grouped:
            continue
        grouped[role].append(figure)
    return grouped


def render_figure_group(role: str, figures: list[dict[str, Any]]) -> str:
    title = ROLE_TITLES[role]
    if not figures:
        return f"### {title}\n\n- 当前未提取到适合放在此处的图。\n"

    lines = [f"### {title}", ""]
    for index, figure in enumerate(figures[:2], start=1):
        lines.append(f"![{title}{index}](./{figure['path']})")
        lines.append(f"- 图注摘要：{sanitize_inline_text(figure.get('caption'))}")
        if figure.get("section_hint"):
            lines.append(f"- 原文位置提示：{figure['section_hint']}")
        if figure.get("placement_confidence") == "low":
            lines.append("- 归位说明：图片归位基于低置信度启发式。")
        lines.append(f"- 审稿人提示：{ROLE_REVIEWER_NOTES[role]}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_external_resources(context: dict[str, Any]) -> str:
    lines = [
        f"1. 最新版 arXiv：{format_link(context.get('arxiv_id_versioned') or 'N/A', context.get('arxiv_abs_url'))}",
        f"2. hjfy：{format_link(context.get('arxiv_id_versioned') or 'N/A', context.get('hjfy_url'))}",
        f"3. papers.cool 论文页：{format_link('论文页', context.get('papers_cool_paper_url'))}",
        f"4. papers.cool 相关搜索页：{format_link('相关搜索页', context.get('papers_cool_related_query_url'))}",
        "5. 社区解读博客：见下方专门区块",
    ]
    visited_at = context.get("hjfy_visited_at")
    if visited_at:
        lines.append(f"- hjfy 链接访问时间：`{visited_at}`")

    gaps = list(context.get("context_gaps") or [])
    if gaps:
        lines.append("- 外部上下文缺口：")
        for gap in gaps:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def render_community_blogs(context: dict[str, Any]) -> str:
    blogs = [blog for blog in list(context.get("community_blogs") or []) if isinstance(blog, dict)]
    gaps = [str(item) for item in list(context.get("community_blog_gaps") or []) if str(item).strip()]

    if not blogs:
        lines = ["- 当前未独立检索到可核验的知乎 / CSDN 论文解读博客。"]
        for gap in gaps:
            lines.append(f"- 检索说明：{gap}")
        return "\n".join(lines)

    lines: list[str] = []
    if len(blogs) < 5:
        lines.append(f"- 当前仅独立检索到以下可核验的知乎 / CSDN 论文解读博客，数量不足 5 条。")
        lines.append("")

    for index, blog in enumerate(blogs, start=1):
        title = str(blog.get("title") or f"社区解读博客 {index}").strip()
        url = str(blog.get("url") or "").strip()
        platform = str(blog.get("platform") or "未知平台").strip()
        page_type = str(blog.get("page_type") or "未知页面类型").strip()
        verification_status = str(blog.get("verification_status") or "未标注").strip()
        why_worth_reading = str(blog.get("why_worth_reading") or "").strip()
        lines.append(f"{index}. [{title}]({url})")
        lines.append(f"   - 平台：{platform}")
        lines.append(f"   - 页面类型：{page_type}")
        lines.append(f"   - 核验状态：{verification_status}")
        if why_worth_reading:
            lines.append(f"   - 值得看：{why_worth_reading}")

    for gap in gaps:
        lines.append(f"- 检索说明：{gap}")
    return "\n".join(lines)


def render_related_papers_table(context: dict[str, Any]) -> str:
    papers = list(context.get("papers_cool_related_papers") or [])
    if not papers:
        return "| N/A | N/A | 当前未拿到可用的 related papers | 检查 `report_context.json` 中的 papers.cool 页面结构 |"

    rows: list[str] = []
    for paper in papers[:5]:
        if not isinstance(paper, dict):
            continue
        title = str(paper.get("title") or "Untitled").replace("|", "\\|")
        url = str(paper.get("url") or "").replace("|", "\\|")
        why_related = str(paper.get("why_related") or "papers.cool related search").replace("|", "\\|")
        notes = str(paper.get("notes") or "").replace("|", "\\|")
        rows.append(f"| {title} | {url} | {why_related} | {notes} |")
    return "\n".join(rows) if rows else "| N/A | N/A | 当前未拿到可用的 related papers | 检查 `report_context.json` 中的 papers.cool 页面结构 |"


def render_main_result_tables() -> str:
    return "\n".join(
        [
            "### 主结果表 M1",
            "| 基准 / 设定 | 对照方法 | 论文方法 | 关键指标 | 差值 | 支撑的主张 |",
            "|---|---|---|---|---|---|",
            "| 待从论文主结果表精确转录 |  |  |  |  |  |",
            "审稿人提示：说明这张主结果表主要在支撑哪条主张，以及它是直接证据还是间接证据。",
            "",
            "### 主结果表 M2",
            "| 指标组 | 最强既有方法 | 论文方法 | 关键指标 | 备注 |",
            "|---|---|---|---|---|",
            "| 待从论文主结果表精确转录 |  |  |  |  |",
            "审稿人提示：如果论文有多张主表，继续逐张转录，不要把数值压缩成纯文字总结。",
        ]
    )


def render_key_ablation_tables() -> str:
    return "\n".join(
        [
            "### 关键消融表 A1",
            "| 消融设定 | 关键改动 | 报告指标 | 相对完整模型差值 | 支撑的主张 |",
            "|---|---|---|---|---|",
            "| 待从关键消融表精确转录 |  |  |  |  |",
            "审稿人提示：解释这张表是否真正隔离了核心机制，而不只是说明更多模块会更强。",
            "",
            "### 关键消融表 A2",
            "| 变体 | 被移除 / 替换的组件 | 报告指标 | 解释 | 缺失对照 |",
            "|---|---|---|---|---|",
            "| 待从关键消融表精确转录 |  |  |  |  |",
            "审稿人提示：如果论文存在训练策略、mask、teacher supervision 等关键机制消融，必须优先转录。",
        ]
    )


def render_claim_rows() -> str:
    return "\n".join(
        [
            "| C1 |  | 显式 |  |  |  |",
            "| C2 |  | 显式 |  |  |  |",
            "| C3 |  | 显式 |  |  |  |",
            "| IC1 |  | 隐含 |  |  |  |",
        ]
    )


def render_experiment_rows() -> str:
    return "\n".join(
        [
            "| 主结果 | C? |  |  |",
            "| 关键消融 | C? |  |  |",
            "| 泛化 / 稳定性 / 失败案例 | C? |  |  |",
        ]
    )


def main() -> int:
    args = parse_args()
    artifacts_path = Path(args.artifacts).resolve()
    output_dir = artifacts_path.parent
    context_path = Path(args.context).resolve() if args.context else output_dir / "report_context.json"
    template_path = Path(args.template).resolve() if args.template else Path(__file__).resolve().parents[1] / "templates" / "report_template.md"
    report_path = output_dir / "report.md"

    artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
    context = load_json_if_exists(context_path)
    template = template_path.read_text(encoding="utf-8")
    figure_groups = group_figures_by_role(artifacts)

    focus_areas = split_items(args.focus_areas)
    baseline_papers = split_items(args.baseline_papers)

    replacements = {
        "{{TITLE}}": artifacts.get("title_guess") or "[待确认论文标题]",
        "{{PAPER_ID}}": str(artifacts.get("paper_id") or "paper"),
        "{{INPUT_SOURCE}}": json.dumps(artifacts.get("input_source", {}), ensure_ascii=False),
        "{{TEXT_EXTRACTION_METHOD}}": str(artifacts.get("text_extraction_method") or "unknown"),
        "{{IMAGE_SOURCE}}": str(artifacts.get("image_source") or "unknown"),
        "{{SOURCE_DIR}}": str(artifacts.get("source_dir") or "None"),
        "{{REPORT_DATE}}": datetime.now().strftime("%Y-%m-%d"),
        "{{FOCUS_AREAS}}": render_list(focus_areas, "未指定"),
        "{{BASELINE_PAPERS}}": render_list(baseline_papers, "未指定"),
        "{{EXTERNAL_RESOURCES_SECTION}}": render_external_resources(context),
        "{{COMMUNITY_BLOGS_SECTION}}": render_community_blogs(context),
        "{{RELATED_PAPERS_ROWS}}": render_related_papers_table(context),
        "{{OVERVIEW_FIGURES_SECTION}}": render_figure_group("overview", figure_groups["overview"]),
        "{{METHOD_DETAIL_FIGURES_SECTION}}": render_figure_group("method_detail", figure_groups["method_detail"]),
        "{{MAIN_EXPERIMENT_FIGURES_SECTION}}": render_figure_group("main_experiment", figure_groups["main_experiment"]),
        "{{STABILITY_FIGURES_SECTION}}": render_figure_group("stability_or_training", figure_groups["stability_or_training"]),
        "{{QUALITATIVE_FIGURES_SECTION}}": render_figure_group("qualitative", figure_groups["qualitative"]),
        "{{FAILURE_CASE_FIGURES_SECTION}}": render_figure_group("failure_case", figure_groups["failure_case"]),
        "{{MAIN_RESULT_TABLES_SECTION}}": render_main_result_tables(),
        "{{KEY_ABLATION_TABLES_SECTION}}": render_key_ablation_tables(),
        "{{CLAIM_TABLE_ROWS}}": render_claim_rows(),
        "{{EXPERIMENT_CLAIM_ROWS}}": render_experiment_rows(),
    }

    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)

    report_path.write_text(rendered, encoding="utf-8")
    print(f"Generated report scaffold: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
