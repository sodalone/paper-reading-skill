#!/usr/bin/env python3
import argparse
import re
import tarfile
from pathlib import Path

import fitz

from common import get_workspace, write_json

IMG_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".eps"}
GRAPHICS_RE = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
CAPTION_RE = re.compile(r'\\caption(?:\[[^\]]*\])?\{(.+?)\}', re.S)
LABEL_RE = re.compile(r'\\label\{([^}]+)\}')
SECTION_RE = re.compile(r'\\(section|subsection|subsubsection)\{(.+?)\}')
INCLUDE_RE = re.compile(r'\\(input|include)\{([^}]+)\}')


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
            graphics = GRAPHICS_RE.findall(block)
            for g in graphics:
                g = g.split(",")[0].strip()
                refs.append(
                    {
                        "graphics_target": g,
                        "caption": caption_m.group(1).strip() if caption_m else "",
                        "label": label_m.group(1).strip() if label_m else "",
                        "section_hint": current_section,
                        "first_reference_hint": current_section,
                        "source_tex": seg["source_tex"],
                        "order": seg["order"],
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


def convert_to_png(src: Path, dst: Path):
    ext = src.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg"}:
        dst.write_bytes(src.read_bytes())
        return True, "copied"
    if ext == ".pdf":
        doc = fitz.open(src)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pix.save(str(dst))
        return True, "pdf_rendered"
    return False, f"unsupported:{ext}"


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
                ok, mode = convert_to_png(src_img, out_path)
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
