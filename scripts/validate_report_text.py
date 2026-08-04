#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path


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

ARXIV_ID_RE = re.compile(r"(?P<base>\d{4}\.\d{4,5})(?P<version>v\d+)?", re.I)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FENCED_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", re.DOTALL)
INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)

MATH_COMPAT_RULES = [
    (
        re.compile(r"\\mathbbm\b"),
        "发现 `\\mathbbm`。KaTeX/Markdown 预览通常不支持该宏，请改写为 `\\mathbf{1}_{\\{...\\}}`、`\\mathbb{I}` 或纯文本伪公式。",
    ),
    (
        re.compile(r"\\tag\s*\{"),
        "发现 `\\tag{}`。请把编号移到正文中，例如“式 (7)”，不要放在公式块内部。",
    ),
]


def count_private_use_chars(text: str) -> int:
    return sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)


def extract_arxiv_id(text: str) -> str:
    match = ARXIV_ID_RE.search(text)
    if not match:
        raise ValueError(f"Could not parse arXiv id from input: {text}")
    return match.group("base")


def strip_non_report_markup(text: str) -> str:
    text = HTML_COMMENT_RE.sub("", text)
    text = FENCED_CODE_BLOCK_RE.sub("", text)
    return text


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def collect_math_issues(text: str) -> list[str]:
    cleaned = strip_non_report_markup(text)
    issues: list[str] = []

    for match in DISPLAY_MATH_RE.finditer(cleaned):
        segment = match.group(1) if match.group(1) is not None else match.group(2)
        base_line = line_number(cleaned, match.start())
        issues.extend(scan_math_segment(segment, base_line))

    inline_source = DISPLAY_MATH_RE.sub("", cleaned)
    for match in INLINE_MATH_RE.finditer(inline_source):
        segment = match.group(1)
        base_line = line_number(inline_source, match.start())
        issues.extend(scan_math_segment(segment, base_line))

    deduped: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue in seen:
            continue
        seen.add(issue)
        deduped.append(issue)
    return deduped


def scan_math_segment(segment: str, base_line: int) -> list[str]:
    issues: list[str] = []

    for pattern, message in MATH_COMPAT_RULES:
        match = pattern.search(segment)
        if not match:
            continue
        issue_line = base_line + segment[: match.start()].count("\n")
        issues.append(f"line {issue_line}: {message}")

    lines = segment.splitlines()
    has_aligned_env = "\\begin{aligned}" in segment or "\\begin{array}" in segment
    if len(lines) > 1 and not has_aligned_env:
        for index, line in enumerate(lines[1:], start=1):
            if re.match(r"^\s*[+\-*]", line):
                issues.append(
                    "line "
                    f"{base_line + index}: 发现裸多行 display 公式续行（以 `+`/`-`/`*` 开头）。"
                    " 请改成单行 `$$ ... $$`，或使用 `aligned` 环境。"
                )
                break

    return issues


def build_report_path(root: Path, input_text: str, explicit_workspace_name: str = "") -> Path:
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

    candidates = []
    direct = root / arxiv_id
    if direct.is_dir():
        candidates.append(direct)
    candidates.extend(sorted(path for path in root.glob(f"{arxiv_id}_*") if path.is_dir()))

    seen: set[Path] = set()
    unique_candidates: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)

    if not unique_candidates:
        raise FileNotFoundError(f"Could not find workspace for arXiv id {arxiv_id} under {root}")

    report_name = f"{arxiv_id}_阅读报告.md"
    report_candidates = [path / report_name for path in unique_candidates if (path / report_name).exists()]
    if len(report_candidates) == 1:
        return report_candidates[0]
    if report_candidates:
        raise RuntimeError(
            f"Multiple reports found for {arxiv_id}; pass --workspace-name: "
            + ", ".join(str(path.parent.name) for path in sorted(report_candidates))
        )

    return unique_candidates[0] / report_name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--workspace-name", default="")
    args = parser.parse_args()

    report_path = build_report_path(Path(args.root).resolve(), args.input, args.workspace_name)
    text = report_path.read_text(encoding="utf-8-sig")

    suspicious_counts = {token: text.count(token) for token in SUSPICIOUS_TOKENS if token in text}
    private_use_count = count_private_use_chars(text)
    replacement_count = text.count("\ufffd")
    math_issues = collect_math_issues(text)

    has_problem = (
        private_use_count > 0
        or replacement_count > 0
        or sum(suspicious_counts.values()) >= 3
        or bool(math_issues)
    )
    if not has_problem:
        print(f"OK: {report_path} looks UTF-8 and math-render clean.")
        return 0

    print(f"ERROR: {report_path} failed report text validation.", file=sys.stderr)
    if private_use_count or replacement_count or suspicious_counts:
        print("- Encoding or text corruption signals:", file=sys.stderr)
        if private_use_count:
            print(f"  - Private-use characters: {private_use_count}", file=sys.stderr)
        if replacement_count:
            print(f"  - Replacement characters: {replacement_count}", file=sys.stderr)
        if suspicious_counts:
            print("  - Suspicious token counts:", file=sys.stderr)
            for token, count in suspicious_counts.items():
                print(f"    - {token}: {count}", file=sys.stderr)
        print(
            "- Hint: on Windows PowerShell, set UTF-8 first with `. ./scripts/windows_utf8.ps1` "
            "and avoid copying Chinese text from a garbled console back into the report.",
            file=sys.stderr,
        )
    if math_issues:
        print("- Markdown math compatibility issues:", file=sys.stderr)
        for issue in math_issues:
            print(f"  - {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
