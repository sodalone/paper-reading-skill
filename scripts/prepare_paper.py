#!/usr/bin/env python3
"""Prepare paper artifacts for the paper-reading skill."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from common import build_workspace_name, fetch_arxiv_metadata


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
TEXT_SUFFIXES = {".txt", ".md", ".tex"}
PDF_SUFFIXES = {".pdf"}
SOURCE_HINTS = ("fig", "figure", "figs", "image", "images", "asset", "assets")
SKIP_IMAGE_HINTS = ("logo", "icon", "badge", "favicon")
SECTION_COMMANDS = ("section", "subsection", "subsubsection")
ROLE_HINTS = {
    "failure_case": ("failure", "fail", "error case", "bad case"),
    "qualitative": ("qualitative", "visualization", "visual", "case study", "comparison"),
    "stability_or_training": ("plot", "curve", "training", "convergence", "stability", "loss", "step"),
    "overview": ("overview", "framework", "pipeline", "paradigm", "teaser", "overall", "comparison"),
    "method_detail": ("adapter", "architecture", "module", "design", "strategy", "algorithm"),
    "main_experiment": ("benchmark", "result", "results", "evaluation", "navsim", "surds", "nudynamics"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare outputs/<paper_id>/ for reviewer-level paper analysis. "
            "Supports local PDFs, PDF URLs, arXiv URLs/IDs, pasted text, and optional source tarballs."
        )
    )
    parser.add_argument("--input", required=True, help="Paper input: local path, URL, arXiv ID, or pasted text.")
    parser.add_argument("--input-type", choices=["auto", "pdf", "url", "arxiv", "text"], default="auto")
    parser.add_argument("--source-tar", help="Optional source tarball path or URL.")
    parser.add_argument("--paper-id", help="Optional explicit paper identifier.")
    parser.add_argument("--output-root", default="outputs", help="Root directory for outputs/<paper_id>.")
    parser.add_argument("--keep-downloads", action="store_true", help="Keep remote downloads in the output directory.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower()).strip("-._")
    return slug or fallback


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_arxiv_id(value: str) -> str | None:
    candidate = value.strip().removeprefix("arxiv:")
    match = re.search(r"(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?(?:\.pdf)?", candidate)
    if match:
        return match.group(1)
    match = re.fullmatch(r"([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", candidate)
    if match:
        return match.group(1)
    return None


def detect_input_kind(raw_input: str, explicit_kind: str) -> str:
    if explicit_kind != "auto":
        return explicit_kind
    path = Path(raw_input)
    if path.exists():
        suffix = path.suffix.lower()
        if suffix in PDF_SUFFIXES:
            return "pdf"
        if suffix in TEXT_SUFFIXES:
            return "text"
    if parse_arxiv_id(raw_input):
        return "arxiv"
    if is_url(raw_input):
        return "url"
    return "text"


def resolve_paper_id(raw_input: str, explicit_paper_id: str | None, source_tar: str | None) -> str:
    if explicit_paper_id:
        return slugify(explicit_paper_id, fallback="paper")

    arxiv_id = parse_arxiv_id(raw_input)
    if arxiv_id:
        return arxiv_id

    for candidate in filter(None, [raw_input, source_tar]):
        path = Path(candidate)
        if path.exists():
            stem = re.sub(r"(-source|-src|-paper)$", "", path.stem, flags=re.IGNORECASE)
            return slugify(stem, fallback="paper")
        if is_url(candidate):
            stem = re.sub(r"(-source|-src|-paper)$", "", Path(urlparse(candidate).path).stem, flags=re.IGNORECASE)
            return slugify(stem or "paper", fallback="paper")

    match = re.search(r"^#?\s*([^\n]{1,80})", raw_input.strip())
    if match:
        return slugify(match.group(1), fallback="paper")
    return "paper"


def as_posix_relative(path: Path, start: Path) -> str:
    return path.relative_to(start).as_posix()


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "paper-reading-skill"})
    with urlopen(request) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def extract_source_tar(source_tar: str, source_dir: Path, downloads_dir: Path) -> tuple[Path | None, list[str]]:
    gaps: list[str] = []
    tar_path: Path
    if is_url(source_tar):
        name = Path(urlparse(source_tar).path).name or "source.tar"
        tar_path = downloads_dir / name
        download_file(source_tar, tar_path)
    else:
        tar_path = Path(source_tar)
        if not tar_path.exists():
            return None, [f"source tarball not found: {source_tar}"]

    ensure_clean_dir(source_dir)
    try:
        with tarfile.open(tar_path, "r:*") as archive:
            try:
                archive.extractall(source_dir, filter="data")
            except TypeError:
                archive.extractall(source_dir)
    except tarfile.TarError as exc:
        gaps.append(f"failed to extract source tarball: {exc}")
        return None, gaps
    return tar_path, gaps


def strip_comments(line: str) -> str:
    return re.sub(r"(?<!\\)%.*$", "", line)


def choose_main_tex(tex_files: list[Path]) -> Path | None:
    scored: list[tuple[int, int, Path]] = []
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        score = 0
        if "\\documentclass" in content:
            score += 10
        if "\\begin{document}" in content:
            score += 5
        scored.append((score, tex_file.stat().st_size, tex_file))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][2]


def resolve_tex_reference(base_file: Path, reference: str) -> Path | None:
    path = Path(reference.strip())
    if not path.suffix:
        path = path.with_suffix(".tex")
    resolved = (base_file.parent / path).resolve()
    return resolved if resolved.exists() else None


def expand_tex_file(tex_file: Path, visited: set[Path]) -> str:
    if tex_file in visited:
        return f"\n%% Skipped already visited file: {tex_file.name}\n"
    visited.add(tex_file)

    content = tex_file.read_text(encoding="utf-8", errors="ignore")
    parts = [f"\n%% BEGIN FILE: {tex_file.as_posix()}\n"]
    input_pattern = re.compile(r"\\(?:input|include)\{([^}]+)\}")

    for raw_line in content.splitlines():
        line = strip_comments(raw_line)
        match = input_pattern.search(line)
        if match:
            nested = resolve_tex_reference(tex_file, match.group(1))
            if nested is not None:
                parts.append(expand_tex_file(nested, visited))
                continue
        parts.append(line + "\n")

    parts.append(f"%% END FILE: {tex_file.as_posix()}\n")
    return "".join(parts)


def extract_title_guess(text: str) -> str | None:
    for pattern in (r"\\icmltitle\{(.+?)\}", r"\\title\{(.+?)\}"):
        title_match = re.search(pattern, text, flags=re.DOTALL)
        if title_match:
            title = re.sub(r"\s+", " ", title_match.group(1)).strip()
            return title or None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("%") and not stripped.startswith("\\") and len(stripped) > 15:
            return stripped[:200]
    return None


def extract_text_from_source(source_dir: Path, paper_txt: Path) -> tuple[str | None, str | None, list[str]]:
    tex_files = sorted(source_dir.rglob("*.tex"))
    if not tex_files:
        return None, None, ["no .tex files found in extracted source"]

    main_tex = choose_main_tex(tex_files)
    if main_tex is None:
        return None, None, ["failed to determine a main .tex file"]

    expanded = expand_tex_file(main_tex.resolve(), visited=set())
    paper_txt.write_text(expanded, encoding="utf-8")
    return "latex-source", extract_title_guess(expanded), []


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def extract_text_from_pdf(pdf_path: Path, paper_txt: Path) -> tuple[str | None, list[str]]:
    gaps: list[str] = []
    commands = [
        ("pdftotext", ["pdftotext", "-layout", str(pdf_path), str(paper_txt)]),
        ("mutool", ["mutool", "draw", "-F", "txt", "-o", str(paper_txt), str(pdf_path)]),
    ]
    for name, command in commands:
        if shutil.which(command[0]) is None:
            continue
        result = run_command(command)
        if result.returncode == 0 and paper_txt.exists() and paper_txt.stat().st_size > 0:
            return name, gaps
        gaps.append(f"{name} failed to extract text")
    gaps.append("no supported PDF text extractor found (tried pdftotext and mutool)")
    return None, gaps


def score_image_candidate(path: Path) -> int:
    name = path.as_posix().lower()
    if any(token in name for token in SKIP_IMAGE_HINTS):
        return -100
    score = 0
    if any(token in name for token in ("overview", "framework", "architecture", "pipeline", "method", "teaser", "main_fig")):
        score += 100
    if any(token in name for token in ("result", "results", "benchmark", "leaderboard", "table", "plot")):
        score += 70
    if any(token in name for token in ("ablation", "analysis", "adapter")):
        score += 55
    if any(token in name for token in ("qualitative", "failure", "case", "visual")):
        score += 45
    if any(token in name for token in SOURCE_HINTS):
        score += 20
    return score + min(int(path.stat().st_size / 1024), 50)


def normalize_source_map_key(path: Path | str) -> str:
    return str(Path(path).resolve()).replace("\\", "/").lower()


def copy_ranked_images(
    image_paths: list[Path],
    figures_dir: Path,
    output_dir: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, dict[str, object]]]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    ranked: list[tuple[int, Path]] = []
    for image_path in image_paths:
        if not image_path.is_file():
            continue
        if image_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if image_path.stat().st_size < 8 * 1024:
            continue
        score = score_image_candidate(image_path)
        if score < 0:
            continue
        ranked.append((score, image_path))

    ranked.sort(key=lambda item: (-item[0], item[1].as_posix().lower()))
    image_list: list[dict[str, object]] = []
    selected_figures: list[dict[str, object]] = []
    source_map: dict[str, dict[str, object]] = {}

    for index, (score, image_path) in enumerate(ranked, start=1):
        stem = slugify(image_path.stem, fallback=f"figure-{index:03d}")
        destination = figures_dir / f"fig-{index:03d}-{stem}{image_path.suffix.lower()}"
        shutil.copy2(image_path, destination)
        record = {
            "path": as_posix_relative(destination, output_dir),
            "source_path": image_path.as_posix(),
            "score": score,
        }
        image_list.append(record)
        source_map[normalize_source_map_key(image_path)] = record
        if len(selected_figures) < 5:
            selected_figures.append(record)

    return image_list, selected_figures, source_map


def extract_images_from_pdf(
    pdf_path: Path,
    figures_dir: Path,
    pages_dir: Path,
    output_dir: Path,
) -> tuple[str, list[dict[str, object]], list[str], list[str], list[str]]:
    gaps: list[str] = []
    image_list: list[dict[str, object]] = []
    page_list: list[str] = []
    selected_paths: list[str] = []

    if shutil.which("pdfimages"):
        result = run_command(["pdfimages", "-all", str(pdf_path), str(figures_dir / "pdf-figure")])
        if result.returncode == 0:
            copied, selected, _ = copy_ranked_images(list(figures_dir.glob("pdf-figure*")), figures_dir, output_dir)
            image_list.extend(copied)
            selected_paths.extend(str(item["path"]) for item in selected)
            if image_list:
                return "pdf-embedded", image_list, page_list, selected_paths, gaps
        gaps.append("pdfimages did not produce usable embedded figures")
    else:
        gaps.append("pdfimages is not installed")

    if shutil.which("pdftoppm"):
        result = run_command(["pdftoppm", "-png", str(pdf_path), str(pages_dir / "page")])
        if result.returncode == 0:
            for index, page_path in enumerate(sorted(pages_dir.glob("page-*.png")), start=1):
                renamed = pages_dir / f"page-{index:03d}.png"
                if page_path != renamed:
                    page_path.rename(renamed)
                page_list.append(as_posix_relative(renamed, output_dir))
            selected_paths.extend(page_list[:3])
            return "page-snapshots", image_list, page_list, selected_paths, gaps
        gaps.append("pdftoppm failed to render page snapshots")
    else:
        gaps.append("pdftoppm is not installed")

    return "none", image_list, page_list, selected_paths, gaps


def find_matching_brace(text: str, start_index: int) -> int | None:
    if start_index >= len(text) or text[start_index] != "{":
        return None
    depth = 0
    for index in range(start_index, len(text)):
        char = text[index]
        if char == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif char == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return index
    return None


def extract_command_argument(text: str, command: str) -> str | None:
    pattern = re.compile(rf"\\{command}\*?(?:\[[^\]]*\])?\{{", re.DOTALL)
    match = pattern.search(text)
    if not match:
        return None
    start = match.end() - 1
    end = find_matching_brace(text, start)
    if end is None:
        return None
    return text[start + 1 : end]


def extract_all_includegraphics(text: str) -> list[str]:
    pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    return [item.strip() for item in pattern.findall(text) if item.strip()]


def clean_latex_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = text.replace("\n", " ").replace("~", " ")
    cleaned = re.sub(r"\\(?:cite|ref|cref|autoref|label)\*?(?:\[[^\]]*\])?\{[^{}]*\}", " ", cleaned)
    cleaned = re.sub(r"\\(?:vspace|hspace|vskip|hskip)\*?(?:\[[^\]]*\])?\{[^{}]*\}", " ", cleaned)
    for _ in range(6):
        updated = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", cleaned)
        if updated == cleaned:
            break
        cleaned = updated
    cleaned = re.sub(r"\\([A-Za-z]+)\*?", r"\1", cleaned)
    cleaned = cleaned.replace("{", " ").replace("}", " ").replace("$", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_section_from_line(line: str) -> tuple[str, str] | None:
    for command in SECTION_COMMANDS:
        pattern = re.compile(rf"\\{command}\*?(?:\[[^\]]*\])?\{{")
        match = pattern.search(line)
        if not match:
            continue
        start = match.end() - 1
        end = find_matching_brace(line, start)
        if end is None:
            continue
        return command, clean_latex_text(line[start + 1 : end])
    return None


def resolve_image_reference(base_dir: Path, source_dir: Path, reference: str) -> Path | None:
    candidate = reference.strip()
    candidate = candidate.split("#", 1)[0].strip()
    if not candidate:
        return None

    direct = (base_dir / candidate).resolve()
    if direct.exists() and direct.is_file():
        return direct

    path_obj = Path(candidate)
    if path_obj.suffix:
        for match in source_dir.rglob(path_obj.name):
            if match.suffix.lower() in IMAGE_SUFFIXES:
                return match.resolve()
        return None

    for suffix in sorted(IMAGE_SUFFIXES):
        with_suffix = direct.with_suffix(suffix)
        if with_suffix.exists() and with_suffix.is_file():
            return with_suffix

    for match in source_dir.rglob(f"{path_obj.name}.*"):
        if match.suffix.lower() in IMAGE_SUFFIXES:
            return match.resolve()
    return None


def classify_placement_role(caption: str, label: str, image_refs: list[str], section_hint: str, source_tex_file: str) -> str:
    ref_text = " ".join([label, *image_refs]).lower()
    meta_text = " ".join([caption, section_hint, source_tex_file]).lower()
    text = " ".join([ref_text, meta_text])

    if any(token in ref_text for token in ROLE_HINTS["failure_case"]):
        return "failure_case"
    if any(token in text for token in ROLE_HINTS["overview"]) or "1_intro.tex" in source_tex_file.lower() or "2_related.tex" in source_tex_file.lower():
        return "overview"
    if any(token in text for token in ROLE_HINTS["method_detail"]) or "3_method.tex" in source_tex_file.lower():
        return "method_detail"
    if any(token in ref_text for token in ROLE_HINTS["qualitative"]):
        return "qualitative"
    if any(token in meta_text for token in ROLE_HINTS["failure_case"]):
        return "failure_case"
    if any(token in text for token in ROLE_HINTS["stability_or_training"]):
        return "stability_or_training"
    if any(token in meta_text for token in ROLE_HINTS["qualitative"]):
        return "qualitative"
    if "appendix" in text:
        return "appendix_other"
    if "method" in text or source_tex_file.lower().endswith("3_method.tex"):
        return "method_detail"
    if "experiment" in text or source_tex_file.lower().endswith("4_exp.tex"):
        return "main_experiment"
    if "intro" in source_tex_file.lower() or "related" in source_tex_file.lower():
        return "overview"
    return "main_experiment"


def parse_tex_figures(source_dir: Path, source_map: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    tex_files = sorted(source_dir.rglob("*.tex"))
    figure_catalog: list[dict[str, object]] = []
    counter = 1

    for tex_file in tex_files:
        content = tex_file.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        current_section = ""
        current_subsection = ""
        index = 0

        while index < len(lines):
            line = strip_comments(lines[index])
            section_info = extract_section_from_line(line)
            if section_info:
                level, title = section_info
                if level == "section":
                    current_section = title
                    current_subsection = ""
                elif level == "subsection":
                    current_subsection = title
                elif level == "subsubsection" and current_subsection:
                    current_subsection = f"{current_subsection} / {title}"
                elif level == "subsubsection":
                    current_subsection = title

            if re.search(r"\\begin\{figure\*?\}", line):
                block_lines = [line]
                index += 1
                while index < len(lines):
                    next_line = strip_comments(lines[index])
                    block_lines.append(next_line)
                    if re.search(r"\\end\{figure\*?\}", next_line):
                        break
                    index += 1

                block = "\n".join(block_lines)
                caption = clean_latex_text(extract_command_argument(block, "caption"))
                label = clean_latex_text(extract_command_argument(block, "label"))
                image_refs = extract_all_includegraphics(block)
                section_hint = " / ".join(part for part in [current_section, current_subsection] if part)
                source_tex_file = tex_file.relative_to(source_dir).as_posix()
                role = classify_placement_role(caption, label, image_refs, section_hint, source_tex_file)

                matched_records: list[dict[str, object]] = []
                resolved_source_paths: list[str] = []
                for image_ref in image_refs:
                    resolved = resolve_image_reference(tex_file.parent, source_dir, image_ref)
                    if resolved is None:
                        continue
                    resolved_source_paths.append(resolved.as_posix())
                    mapped = source_map.get(normalize_source_map_key(resolved))
                    if mapped is not None:
                        matched_records.append(mapped)

                if matched_records:
                    best = max(matched_records, key=lambda item: int(item.get("score") or 0))
                    figure_catalog.append(
                        {
                            "figure_id": label or f"figure-{counter:03d}",
                            "path": best["path"],
                            "caption": caption,
                            "label": label,
                            "source_tex_file": source_tex_file,
                            "section_hint": section_hint,
                            "placement_role": role,
                            "placement_confidence": "high",
                            "source_image_paths": image_refs,
                            "matched_source_paths": resolved_source_paths,
                        }
                    )
                    counter += 1
            index += 1

    return figure_catalog


def classify_pdf_role(path: str, index: int) -> str:
    lowered = path.lower()
    if any(token in lowered for token in ("failure", "fail")):
        return "failure_case"
    if any(token in lowered for token in ("plot", "curve", "loss")):
        return "stability_or_training"
    if any(token in lowered for token in ("visual", "qualitative")):
        return "qualitative"
    if any(token in lowered for token in ("overview", "main", "framework")):
        return "overview"
    if any(token in lowered for token in ("adapter", "architecture", "method")):
        return "method_detail"
    if index == 1:
        return "overview"
    if index == 2:
        return "main_experiment"
    if index == 3:
        return "qualitative"
    return "main_experiment"


def build_pdf_figure_catalog(image_list: list[dict[str, object]], page_list: list[str]) -> list[dict[str, object]]:
    catalog: list[dict[str, object]] = []
    if image_list:
        for index, item in enumerate(image_list[:8], start=1):
            path = str(item.get("path") or "")
            if not path:
                continue
            catalog.append(
                {
                    "figure_id": f"pdf-figure-{index:03d}",
                    "path": path,
                    "caption": f"PDF 提取图片 {index}",
                    "label": "",
                    "source_tex_file": "",
                    "section_hint": "PDF-only 输入，当前无法可靠提取图注与原文位置。",
                    "placement_role": classify_pdf_role(path, index),
                    "placement_confidence": "low",
                    "source_image_paths": [],
                }
            )
        return catalog

    for index, path in enumerate(page_list[:5], start=1):
        catalog.append(
            {
                "figure_id": f"pdf-page-{index:03d}",
                "path": path,
                "caption": f"PDF 页面快照 {index}",
                "label": "",
                "source_tex_file": "",
                "section_hint": "PDF-only 输入，当前使用页面快照做低置信度归位。",
                "placement_role": classify_pdf_role(path, index),
                "placement_confidence": "low",
                "source_image_paths": [],
            }
        )
    return catalog


def build_input_record(
    kind: str,
    original: str,
    local_pdf: Path | None,
    source_tar: str | None,
    local_source_tar: Path | None,
) -> dict[str, object]:
    record: dict[str, object] = {"kind": kind, "original": original}
    if local_pdf is not None:
        record["local_pdf"] = local_pdf.as_posix()
    if source_tar is not None:
        record["source_tar"] = source_tar
    if local_source_tar is not None:
        record["local_source_tar"] = local_source_tar.as_posix()
    arxiv_id = parse_arxiv_id(original)
    if arxiv_id:
        record["arxiv_id"] = arxiv_id
    return record


def main() -> int:
    args = parse_args()
    kind = detect_input_kind(args.input, args.input_type)
    paper_id = resolve_paper_id(args.input, args.paper_id, args.source_tar)
    paper_title_for_dir: str | None = None
    arxiv_id_for_dir = parse_arxiv_id(args.input)
    if arxiv_id_for_dir and not args.paper_id:
        try:
            paper_title_for_dir = fetch_arxiv_metadata(arxiv_id_for_dir).get("title")
            paper_id = build_workspace_name(arxiv_id_for_dir, paper_title_for_dir)
        except Exception:
            paper_title_for_dir = None

    output_root = Path(args.output_root).resolve()
    output_dir = output_root / paper_id
    figures_dir = output_dir / "figures"
    pages_dir = output_dir / "pages"
    source_dir = output_dir / "source"
    downloads_dir = output_dir / "_downloads"
    paper_txt = output_dir / "paper.txt"
    artifacts_path = output_dir / "artifacts.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    ensure_clean_dir(figures_dir)
    ensure_clean_dir(pages_dir)
    ensure_clean_dir(downloads_dir)

    unresolved_gaps: list[str] = []
    title_guess: str | None = paper_title_for_dir
    local_pdf: Path | None = None
    local_source_tar: Path | None = None
    text_method: str | None = None
    image_source = "none"
    image_list: list[dict[str, object]] = []
    page_list: list[str] = []
    selected_figures: list[str] = []
    figure_catalog: list[dict[str, object]] = []
    source_dir_record: str | None = None

    if kind == "pdf":
        local_pdf = Path(args.input).resolve()
        if not local_pdf.exists():
            print(f"Input PDF not found: {args.input}", file=sys.stderr)
            return 1
    elif kind in {"url", "arxiv"}:
        pdf_url = args.input
        if kind == "arxiv":
            arxiv_id = parse_arxiv_id(args.input)
            if arxiv_id is None:
                print(f"Could not parse arXiv ID from input: {args.input}", file=sys.stderr)
                return 1
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        local_pdf = downloads_dir / "paper.pdf"
        download_file(pdf_url, local_pdf)
    elif kind == "text":
        if Path(args.input).exists() and Path(args.input).suffix.lower() in TEXT_SUFFIXES:
            source_text = Path(args.input).read_text(encoding="utf-8", errors="ignore")
        else:
            source_text = args.input
        paper_txt.write_text(source_text, encoding="utf-8")
        text_method = "input-text"
        title_guess = extract_title_guess(source_text)
    else:
        print(f"Unsupported input type: {kind}", file=sys.stderr)
        return 1

    if args.source_tar:
        local_source_tar, tar_gaps = extract_source_tar(args.source_tar, source_dir, downloads_dir)
        unresolved_gaps.extend(tar_gaps)
        if local_source_tar is not None:
            source_dir_record = "source"
            source_images, selected_records, source_map = copy_ranked_images(list(source_dir.rglob("*")), figures_dir, output_dir)
            if source_images:
                image_source = "latex-source"
                image_list = source_images
                selected_figures = [str(item["path"]) for item in selected_records]
            source_text_method, source_title, text_gaps = extract_text_from_source(source_dir, paper_txt)
            unresolved_gaps.extend(text_gaps)
            if source_text_method is not None:
                text_method = source_text_method
            if source_title and not title_guess:
                title_guess = source_title
            if image_list:
                figure_catalog = parse_tex_figures(source_dir, source_map)
                if not figure_catalog:
                    unresolved_gaps.append("latex-source figures were extracted, but figure_catalog could not be built")

    if text_method is None and local_pdf is not None:
        extracted_method, text_gaps = extract_text_from_pdf(local_pdf, paper_txt)
        unresolved_gaps.extend(text_gaps)
        text_method = extracted_method

    if image_source == "none" and local_pdf is not None:
        detected_image_source, pdf_images, pdf_pages, selected_paths, image_gaps = extract_images_from_pdf(
            local_pdf,
            figures_dir,
            pages_dir,
            output_dir,
        )
        unresolved_gaps.extend(image_gaps)
        if pdf_images:
            image_list = pdf_images
        if pdf_pages:
            page_list = pdf_pages
        if selected_paths:
            selected_figures = selected_paths
        image_source = detected_image_source
        if image_source in {"pdf-embedded", "page-snapshots"}:
            figure_catalog = build_pdf_figure_catalog(image_list, page_list)

    if text_method is None:
        text_method = "unavailable"
        unresolved_gaps.append("paper text was not extracted")

    if image_source == "none":
        unresolved_gaps.append("no usable figures or page snapshots were extracted")

    artifacts = {
        "paper_id": paper_id,
        "created_at": utc_now(),
        "title_guess": title_guess,
        "input_source": build_input_record(kind, args.input, local_pdf, args.source_tar, local_source_tar),
        "text_extraction_method": text_method,
        "image_source": image_source,
        "image_list": image_list,
        "page_list": page_list,
        "source_dir": source_dir_record,
        "selected_figures": selected_figures,
        "figure_catalog": figure_catalog,
        "paper_txt": "paper.txt" if paper_txt.exists() else None,
        "unresolved_gaps": sorted(dict.fromkeys(unresolved_gaps)),
    }
    artifacts_path.write_text(json.dumps(artifacts, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.keep_downloads and downloads_dir.exists():
        shutil.rmtree(downloads_dir)

    print(f"Prepared paper artifacts in: {output_dir}")
    print(f"paper_id: {paper_id}")
    print(f"text extraction: {text_method}")
    print(f"image source: {image_source}")
    print(f"figure_catalog entries: {len(figure_catalog)}")
    if artifacts["unresolved_gaps"]:
        print("unresolved gaps:")
        for gap in artifacts["unresolved_gaps"]:
            print(f"  - {gap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
