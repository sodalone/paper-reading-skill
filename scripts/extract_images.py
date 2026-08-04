#!/usr/bin/env python3
import argparse
import re
import tarfile
from pathlib import Path

import fitz

from common import get_workspace, write_json

IMG_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".eps"}
GRAPHICS_RE = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
OVERPIC_BEGIN_RE = re.compile(r'\\begin\{overpic\}(?:\[[^\]]*\])?\{([^}]+)\}', re.S)
OVERPIC_END = r'\end{overpic}'
PUT_RE = re.compile(r'\\put\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)\s*\{', re.S)
CAPTION_RE = re.compile(r'\\caption(?:\[[^\]]*\])?\{(.+?)\}', re.S)
LABEL_RE = re.compile(r'\\label\{([^}]+)\}')
SECTION_RE = re.compile(r'\\(section|subsection|subsubsection)\{(.+?)\}')
INCLUDE_RE = re.compile(r'\\(input|include)\{([^}]+)\}')


def find_matching_brace(text: str, start: int):
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif char == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return index
    return None


def unwrap_latex_command(text: str, command: str, leading_arg: bool = False):
    if leading_arg:
        pattern = re.compile(rf"\\{command}\{{([^{{}}]+)\}}\{{")
    else:
        pattern = re.compile(rf"\\{command}\{{")
    match = pattern.search(text)
    if not match:
        return text, None
    opening = match.end() - 1
    closing = find_matching_brace(text, opening)
    if closing is None:
        return text, None
    inner = text[opening + 1 : closing]
    arg = match.group(1) if leading_arg else None
    return text[: match.start()] + inner + text[closing + 1 :], arg


def clean_overlay_text(raw: str):
    rotation = 0.0
    color_name = "black"
    text = raw.strip()

    changed, arg = unwrap_latex_command(text, "rotatebox", leading_arg=True)
    if arg is not None:
        text = changed
        try:
            rotation = float(arg)
        except ValueError:
            rotation = 0.0

    changed, arg = unwrap_latex_command(text, "textcolor", leading_arg=True)
    if arg is not None:
        text = changed
        color_name = arg.strip().lower() or "black"

    text = text.replace(r"\cmark", "✓").replace(r"\xmark", "✗")
    text = re.sub(r"\\(?:tiny|scriptsize|footnotesize|small|normalsize|large|Large|bfseries|itshape)\b", " ", text)
    for _ in range(4):
        updated = re.sub(r"\\[A-Za-z]+\*?\{([^{}]*)\}", r"\1", text)
        if updated == text:
            break
        text = updated
    text = text.replace("{", " ").replace("}", " ")
    text = re.sub(r"\\([%&#_$])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, rotation, color_name


def parse_put_overlays(text: str):
    overlays = []
    cursor = 0
    while True:
        match = PUT_RE.search(text, cursor)
        if not match:
            break
        opening = match.end() - 1
        closing = find_matching_brace(text, opening)
        if closing is None:
            break
        raw = text[opening + 1 : closing]
        label, rotation, color_name = clean_overlay_text(raw)
        overlays.append(
            {
                "x": float(match.group(1)),
                "y": float(match.group(2)),
                "text": label,
                "rotation": int(rotation) if rotation.is_integer() else rotation,
                "color_name": color_name,
            }
        )
        cursor = closing + 1
    return overlays


def parse_graphics_events(block: str):
    events = []
    overpic_spans = []
    for match in OVERPIC_BEGIN_RE.finditer(block):
        end = block.find(OVERPIC_END, match.end())
        if end < 0:
            end = len(block)
        overpic_spans.append((match.start(), end + len(OVERPIC_END)))
        events.append(
            {
                "position": match.start(),
                "target": match.group(1).split(",")[0].strip(),
                "overlays": parse_put_overlays(block[match.end() : end]),
            }
        )

    for match in GRAPHICS_RE.finditer(block):
        if any(start <= match.start() < end for start, end in overpic_spans):
            continue
        events.append(
            {
                "position": match.start(),
                "target": match.group(1).split(",")[0].strip(),
                "overlays": [],
            }
        )

    events.sort(key=lambda event: event["position"])
    for event in events:
        event.pop("position", None)
    return events


def extract_tar(src_tar: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(src_tar, "r:*") as tf:
        safe = []
        for m in tf.getmembers():
            p = Path(m.name)
            if p.is_absolute() or ".." in p.parts:
                continue
            safe.append(m)
        tf.extractall(out_dir, members=safe)


def choose_main_tex(src_dir: Path):
    tex_files = list(src_dir.rglob("*.tex"))
    if not tex_files:
        return None
    scored = []
    for p in tex_files:
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        no_comments = strip_tex_comments(txt)
        has_docclass = "\\documentclass" in no_comments
        has_begin_document = "\\begin{document}" in no_comments
        include_count = len(INCLUDE_RE.findall(no_comments))
        scored.append(
            (
                1 if has_docclass and has_begin_document else 0,
                include_count,
                -len(str(p.relative_to(src_dir))),
                p,
            )
        )
    scored.sort(key=lambda x: (-x[0], -x[1], -x[2], str(x[3])))
    return scored[0][3] if scored else None


def strip_tex_comments(text: str) -> str:
    stripped = []
    for line in text.splitlines():
        out = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "%" and (i == 0 or line[i - 1] != "\\"):
                break
            out.append(ch)
            i += 1
        stripped.append("".join(out))
    return "\n".join(stripped)


def resolve_tex_include(base_tex: Path, target: str):
    target = target.strip()
    if not target:
        return None
    candidate = (base_tex.parent / target).resolve()
    if candidate.suffix.lower() != ".tex":
        candidate = candidate.with_suffix(".tex")
    return candidate if candidate.exists() else None


def expand_tex_tree(main_tex: Path, src_dir: Path):
    visited = set()
    segments = []

    def append_segment(tex_path: Path, chunk: str):
        if not chunk.strip():
            return
        segments.append(
            {
                "source_tex": str(tex_path.relative_to(src_dir)).replace("\\", "/"),
                "text": chunk,
            }
        )

    def visit(tex_path: Path):
        tex_path = tex_path.resolve()
        if tex_path in visited or not tex_path.exists():
            return
        visited.add(tex_path)
        raw = tex_path.read_text(encoding="utf-8", errors="ignore")
        text = strip_tex_comments(raw)
        last = 0
        for m in INCLUDE_RE.finditer(text):
            append_segment(tex_path, text[last:m.start()])
            included = resolve_tex_include(tex_path, m.group(2))
            if included:
                visit(included)
            last = m.end()
        append_segment(tex_path, text[last:])

    visit(main_tex)
    for idx, seg in enumerate(segments, start=1):
        seg["order"] = idx
    return segments


def parse_tex_refs(segments):
    refs = []
    current_section = ""
    figure_re = re.compile(r'\\begin\{figure\*?\}(.+?)\\end\{figure\*?\}', re.S)
    for seg in segments:
        txt = seg["text"]
        events = []
        for m in SECTION_RE.finditer(txt):
            events.append(("section", m.start(), m))
        for m in figure_re.finditer(txt):
            events.append(("figure", m.start(), m))
        events.sort(key=lambda x: x[1])
        for kind, _, match in events:
            if kind == "section":
                current_section = match.group(2).strip()
                continue
            block = match.group(1)
            caption_m = CAPTION_RE.search(block)
            label_m = LABEL_RE.search(block)
            graphics = parse_graphics_events(block)
            for graphic in graphics:
                g = graphic["target"]
                refs.append(
                    {
                        "graphics_target": g,
                        "caption": caption_m.group(1).strip() if caption_m else "",
                        "label": label_m.group(1).strip() if label_m else "",
                        "section_hint": current_section,
                        "first_reference_hint": current_section,
                        "source_tex": seg["source_tex"],
                        "order": seg["order"],
                        "overlays": graphic["overlays"],
                    }
                )
    return refs


def find_image(src_dir: Path, target: str):
    target_path = Path(target)
    stems = {target, str(Path(target).with_suffix("")), target_path.stem}
    candidates = []
    for p in src_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in IMG_EXTS:
            continue
        rel = p.relative_to(src_dir).as_posix()
        rel_stem = str(Path(rel).with_suffix("")).replace("\\", "/")
        if rel in stems or rel_stem in stems or p.stem in stems or rel.endswith(target):
            candidates.append(p)
    candidates.sort(key=lambda x: len(str(x)))
    return candidates[0] if candidates else None


def convert_to_png(src: Path, dst: Path, overlays=None):
    overlays = overlays or []
    warnings = []
    ext = src.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg"} and not overlays:
        dst.write_bytes(src.read_bytes())
        return True, "copied", warnings
    if ext in {".pdf", ".png", ".jpg", ".jpeg"}:
        doc = fitz.open(src)
        if ext != ".pdf":
            converted = fitz.open("pdf", doc.convert_to_pdf())
            doc.close()
            doc = converted
        page = doc[0]
        color_map = {
            "black": (0, 0, 0),
            "red": (1, 0, 0),
            "green": (0, 0.6, 0),
            "blue": (0, 0, 1),
            "white": (1, 1, 1),
        }
        for overlay in overlays:
            text = str(overlay.get("text") or "").replace("✓", "OK").replace("✗", "X")
            if not text:
                continue
            rotation = int(overlay.get("rotation") or 0) % 360
            if rotation not in {0, 90, 180, 270}:
                warnings.append(f"unsupported overlay rotation {rotation}; rendered without rotation")
                rotation = 0
            point = fitz.Point(
                page.rect.width * float(overlay.get("x", 0)) / 100.0,
                page.rect.height * (1.0 - float(overlay.get("y", 0)) / 100.0),
            )
            page.insert_text(
                point,
                text,
                fontsize=max(6, page.rect.width / 45),
                color=color_map.get(str(overlay.get("color_name") or "black").lower(), (0, 0, 0)),
                rotate=rotation,
            )
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pix.save(str(dst))
        doc.close()
        mode = "pdf_rendered_with_overpic_overlay" if overlays else "pdf_rendered"
        return True, mode, warnings
    return False, f"unsupported:{ext}", warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace, _ = get_workspace(root, args.input)
    raw_dir = workspace / "raw"
    cache_dir = workspace / "cache"
    img_dir = workspace / "images"
    cache_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    src_tar = raw_dir / "source.tar"
    unpack_dir = cache_dir / "source_unpack"
    figures = []
    note = ""
    if src_tar.exists():
        try:
            extract_tar(src_tar, unpack_dir)
            main_tex = choose_main_tex(unpack_dir)
            segments = expand_tex_tree(main_tex, unpack_dir) if main_tex else []
            refs = parse_tex_refs(segments) if segments else []
            idx = 1
            seen_targets = set()
            for ref in refs:
                target = ref["graphics_target"]
                if target in seen_targets:
                    continue
                seen_targets.add(target)
                src_img = find_image(unpack_dir, target)
                if not src_img:
                    continue
                out_path = img_dir / f"figure_{idx:02d}.png"
                ok, mode, warnings = convert_to_png(src_img, out_path, ref.get("overlays"))
                if not ok:
                    continue
                figures.append({
                    "index": idx,
                    "original_file": str(src_img.relative_to(unpack_dir)).replace("\\", "/"),
                    "saved_path": str(out_path.relative_to(workspace)),
                    "source": "arxiv_src",
                    "graphics_target": target,
                    "caption": ref.get("caption", ""),
                    "label": ref.get("label", ""),
                    "section_hint": ref.get("section_hint", ""),
                    "first_reference_hint": ref.get("first_reference_hint", ""),
                    "source_tex": ref.get("source_tex", ""),
                    "conversion": mode,
                    "overlay_warnings": warnings,
                })
                idx += 1
            note = "图片优先来自 arXiv 源码包中的作者原始 figure 文件，并结合 LaTeX 引用关系进行定位。"
        except Exception as e:
            figures = []
            note = f"arXiv 源码图片提取失败：{e}"
    else:
        note = "未找到 arXiv 源码包，未执行 source-first 图片提取。"

    payload = {
        "figures": figures,
        "note": note,
        "policy": "prefer_arxiv_src_over_pdf_over_webpage",
    }
    write_json(cache_dir / "images_manifest.json", payload)
    print("Image manifest saved:", cache_dir / "images_manifest.json")


if __name__ == "__main__":
    main()
