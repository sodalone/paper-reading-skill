#!/usr/bin/env python3
"""Validate the report's understanding-first structure and final readability gates."""

from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from pathlib import Path


ARXIV_ID_RE = re.compile(r"(?P<base>\d{4}\.\d{4,5})(?P<version>v\d+)?", re.I)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", re.DOTALL)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

REQUIRED_HEADINGS = [
    "## 0. 三分钟读懂",
    "### 0.1 论文解决什么问题",
    "### 0.2 核心办法是什么",
    "### 0.3 最重要的结果",
    "### 0.4 最终判断",
    "### 0.5 阅读路线",
    "## 1. 先建立直觉",
    "## 2. 方法如何工作",
    "## 3. 证据是否成立",
    "### 3.1 Claim—Evidence—Verdict 总表",
    "## 4. 最终判断与适用边界",
    "## 附录 A：完整实验表",
    "## 附录 B：数学与实现细节",
    "## 附录 C：本报告实际使用的外部文献",
    "## 附录 D：证据定位",
]

FINAL_PLACEHOLDERS = [
    "待补充",
    "待确认",
    "论文标题待核对",
    "| C1 |  |  |  |  |",
    "- 阅读建议：\n",
    "- 复现建议：\n",
]

FORBIDDEN_WORK_LABELS = ["A级公式", "B级公式", "C级公式", "公式理解卡"]

LINK_SECTION_PATTERNS = [
    r"^- 原始输入链接：https://arxiv\.org/abs/\d{4}\.\d{4,5}$",
    r"^- 最终使用的 arXiv 版本化 ID：\d{4}\.\d{4,5}v\d+$",
    r"^- 原论文 arXiv 链接：https://arxiv\.org/abs/\d{4}\.\d{4,5}v\d+$",
    r"^- 幻觉翻译链接（hjfy）：https://hjfy\.top/arxiv/\d{4}\.\d{4,5}v\d+$",
    r"^- Cool Papers 链接：https://papers\.cool/arxiv/\d{4}\.\d{4,5}v\d+$",
]


def extract_arxiv_id(text: str) -> str:
    match = ARXIV_ID_RE.search(text)
    if not match:
        raise ValueError(f"Could not parse arXiv id from input: {text}")
    return match.group("base")


def resolve_report_path(root: Path, input_text: str, explicit_workspace_name: str = "") -> Path:
    direct_input = Path(input_text).expanduser()
    if not direct_input.is_absolute():
        direct_input = root / direct_input
    if direct_input.is_file():
        return direct_input.resolve()

    arxiv_id = extract_arxiv_id(input_text)
    workspace_name = explicit_workspace_name.strip() or os.environ.get("PAPER_READING_WORKSPACE_NAME", "").strip()
    if workspace_name:
        if Path(workspace_name).name != workspace_name or "/" in workspace_name or "\\" in workspace_name:
            raise ValueError("PAPER_READING_WORKSPACE_NAME must be a directory name, not a path")
        return root / workspace_name / f"{arxiv_id}_阅读报告.md"

    candidates = sorted(root.glob(f"{arxiv_id}_*/{arxiv_id}_阅读报告.md"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        direct = root / arxiv_id / f"{arxiv_id}_阅读报告.md"
        if direct.exists():
            return direct
        raise FileNotFoundError(f"Could not find report for {arxiv_id} under {root}")
    raise RuntimeError(
        f"Multiple reports found for {arxiv_id}; set PAPER_READING_WORKSPACE_NAME: "
        + ", ".join(str(path.parent.name) for path in candidates)
    )


def extract_section(text: str, start_heading: str, next_heading_prefix: str = "## ") -> str:
    start = text.find(start_heading)
    if start < 0:
        return ""
    content_start = start + len(start_heading)
    next_match = re.search(rf"(?m)^{re.escape(next_heading_prefix)}", text[content_start:])
    end = content_start + next_match.start() if next_match else len(text)
    return text[content_start:end]


def normalize_paragraph(paragraph: str) -> str:
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    return paragraph


def duplicate_long_paragraphs(text: str) -> list[str]:
    cleaned = HTML_COMMENT_RE.sub("", text)
    paragraphs = []
    for raw in re.split(r"\n\s*\n", cleaned):
        paragraph = normalize_paragraph(raw)
        if len(paragraph) < 100:
            continue
        if paragraph.startswith(("#", "|", "!", "$$")):
            continue
        paragraphs.append(paragraph)
    counts = Counter(paragraphs)
    return [paragraph for paragraph, count in counts.items() if count > 1]


def validate_report(text: str, final: bool = False) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"缺少必需标题：{heading}")

    link_section = extract_section(text, "### 0.6 论文与链接", "## ")
    link_bullets = re.findall(r"(?m)^- .+$", link_section)
    for pattern in LINK_SECTION_PATTERNS:
        if not re.search(pattern, link_section, re.MULTILINE):
            errors.append(f"0.6 论文与链接未按固定格式填写：{pattern}")
    if len(link_bullets) != len(LINK_SECTION_PATTERNS):
        errors.append("0.6 论文与链接必须且只能包含五行固定字段。")

    appendix_start = text.find("## 附录 A：完整实验表")
    main_text = text[:appendix_start] if appendix_start >= 0 else text
    summary = extract_section(text, "## 0. 三分钟读懂", "## ")
    summary_clean = HTML_COMMENT_RE.sub("", summary).strip()
    main_formula_count = len(DISPLAY_MATH_RE.findall(main_text))
    main_h3_count = len(re.findall(r"(?m)^### ", main_text))
    image_count = len(IMAGE_RE.findall(text))
    table_rows = len(re.findall(r"(?m)^\|.*\|\s*$", text))

    metrics = {
        "summary_chars": len(summary_clean),
        "main_chars": len(HTML_COMMENT_RE.sub("", main_text)),
        "main_formula_count": main_formula_count,
        "main_h3_count": main_h3_count,
        "image_count": image_count,
        "table_rows": table_rows,
    }

    if metrics["main_chars"] > 14000:
        warnings.append(f"正文主线为 {metrics['main_chars']} 字符，超过建议的 14,000；考虑下沉细节到附录。")
    if metrics["main_chars"] > 20000:
        errors.append(f"正文主线为 {metrics['main_chars']} 字符，超过可读性上限 20,000。")
    if main_formula_count > 3:
        warnings.append(f"正文含 {main_formula_count} 个块公式；非理论论文建议控制在 0–3 个。")
    if main_formula_count > 5:
        errors.append(f"正文含 {main_formula_count} 个块公式，超过理论论文主线最多 5 个的上限。")
    # The canonical understanding-first template contains 25 H3 headings.
    # Warn only when authors add enough extra fragmentation to exceed it.
    if main_h3_count > 26:
        warnings.append(f"正文有 {main_h3_count} 个三级标题，可能过度切碎阅读路径。")

    if final:
        if HTML_COMMENT_RE.search(text):
            errors.append("最终报告仍包含模板 HTML 注释。")
        for placeholder in FINAL_PLACEHOLDERS:
            if placeholder in text:
                errors.append(f"最终报告仍包含占位内容：{placeholder!r}")
        for label in FORBIDDEN_WORK_LABELS:
            if label in text:
                errors.append(f"最终报告暴露内部工作标签：{label}")
        if not 300 <= len(summary_clean) <= 2200:
            errors.append(
                f"三分钟摘要为 {len(summary_clean)} 字符；应在 300–2,200 字符之间并覆盖问题、方法、结果、判断和路线。"
            )
        if image_count < 1:
            errors.append("最终报告没有插入任何 Markdown 图片。")
        evidence = extract_section(text, "## 3. 证据是否成立", "## ")
        if "| Claim |" not in evidence:
            errors.append("证据章节缺少 Claim—Evidence—Verdict 表。")
        if "| Claim | 原文位置 |" not in evidence:
            errors.append("Claim—Evidence—Verdict 表缺少逐条原文位置列。")
        if len(re.findall(r"(?m)^\|\s*C\d+\b", evidence)) < 2:
            errors.append("Claim—Evidence—Verdict 表至少应包含两条已填写 Claim。")
        duplicates = duplicate_long_paragraphs(text)
        if duplicates:
            errors.append(f"发现 {len(duplicates)} 个长度至少 100 字符的重复段落。")

    return errors, warnings, metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate paper-reading report structure and readability.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--workspace-name", default="")
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()

    report_path = resolve_report_path(Path(args.root).resolve(), args.input, args.workspace_name)
    text = report_path.read_text(encoding="utf-8-sig")
    errors, warnings, metrics = validate_report(text, final=args.final)

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        print(f"ERROR: {report_path} failed readability validation.")
        for error in errors:
            print(f"- {error}")
        return 1

    stage = "final" if args.final else "skeleton"
    print(f"OK: {report_path} passed {stage} readability validation: {metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
