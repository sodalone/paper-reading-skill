#!/usr/bin/env python3
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple
from html import unescape
from urllib.parse import urlparse

import requests

ARXIV_ID_RE = re.compile(r'(?P<base>\d{4}\.\d{4,5})(?P<version>v\d+)?', re.I)
TITLE_RE = re.compile(r'<h1[^>]*class=["\']title\s+mathjax["\'][^>]*>(.*?)</h1>', re.I | re.S)
META_TITLE_RE = re.compile(r'<meta[^>]+name=["\']citation_title["\'][^>]+content=["\'](.*?)["\']', re.I | re.S)
INVALID_PATH_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
WHITESPACE_RE = re.compile(r'\s+')
MAX_TITLE_SLUG_CHARS = 140


def extract_arxiv_id(text: str) -> Optional[Tuple[str, Optional[str]]]:
    match = ARXIV_ID_RE.search(text)
    if match:
        return match.group("base"), match.group("version")
    try:
        path = urlparse(text).path
        match = ARXIV_ID_RE.search(path)
        if match:
            return match.group("base"), match.group("version")
    except Exception:
        pass
    return None


def fetch_arxiv_abs_html(paper_id: str, timeout: int = 20) -> str:
    url = f"https://arxiv.org/abs/{paper_id}"
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "paper-reading-skill"})
    r.raise_for_status()
    return r.text


def parse_latest_version(base_id: str, html: str) -> Optional[str]:
    candidates = re.findall(rf'{re.escape(base_id)}v(\d+)', html)
    if candidates:
        return f"v{max(int(x) for x in candidates)}"
    m = re.search(r'this version,\s*v(\d+)', html, re.I)
    if m:
        return f"v{m.group(1)}"
    return None


def parse_arxiv_title(html: str) -> Optional[str]:
    match = TITLE_RE.search(html) or META_TITLE_RE.search(html)
    if not match:
        return None
    title = re.sub(r"<[^>]+>", " ", match.group(1))
    title = unescape(title)
    title = re.sub(r"^\s*Title:\s*", "", title, flags=re.I)
    title = WHITESPACE_RE.sub(" ", title).strip()
    return title or None


def fetch_arxiv_metadata(base_id: str, version: Optional[str] = None, timeout: int = 20) -> Dict[str, Optional[str]]:
    paper_id = f"{base_id}{version or ''}"
    html = fetch_arxiv_abs_html(paper_id, timeout=timeout)
    return {
        "version": version or parse_latest_version(base_id, html),
        "title": parse_arxiv_title(html),
    }


def fetch_latest_version(base_id: str, timeout: int = 20) -> Optional[str]:
    return fetch_arxiv_metadata(base_id, timeout=timeout)["version"]


def sanitize_title_for_path(title: Optional[str]) -> str:
    if not title:
        return ""
    normalized = unicodedata.normalize("NFKC", title)
    normalized = INVALID_PATH_CHARS_RE.sub(" ", normalized)
    normalized = normalized.replace("'", "").replace("`", "")
    slug = WHITESPACE_RE.sub("_", normalized).strip(" ._-")
    if len(slug) > MAX_TITLE_SLUG_CHARS:
        slug = slug[:MAX_TITLE_SLUG_CHARS].rstrip(" ._-")
    return slug


def build_workspace_name(arxiv_id: str, title: Optional[str]) -> str:
    title_slug = sanitize_title_for_path(title)
    return f"{arxiv_id}_{title_slug}" if title_slug else arxiv_id


def resolve_ids(input_text: str) -> Dict[str, str]:
    parsed = extract_arxiv_id(input_text)
    if not parsed:
        raise ValueError(f"Could not parse arXiv id from input: {input_text}")
    base_id, version = parsed
    metadata = fetch_arxiv_metadata(base_id, version)
    latest = metadata["version"]
    title = metadata["title"] or ""
    paper_id_with_version = f"{base_id}{latest}" if latest else base_id
    return {
        "input": input_text,
        "arxiv_id": base_id,
        "title": title,
        "workspace_name": build_workspace_name(base_id, title),
        "version": latest or "",
        "paper_id_with_version": paper_id_with_version,
        "arxiv_abs_url": f"https://arxiv.org/abs/{paper_id_with_version}",
        "arxiv_pdf_url": f"https://arxiv.org/pdf/{paper_id_with_version}.pdf",
        "hjfy_url": f"https://hjfy.top/arxiv/{paper_id_with_version}",
        "papers_cool_url": f"https://papers.cool/arxiv/{paper_id_with_version}",
        "ar5iv_url": f"https://ar5iv.org/html/{paper_id_with_version}",
        "arxiv_src_url": f"https://arxiv.org/src/{paper_id_with_version}",
    }


def ensure_workspace(root: Path, arxiv_id: str, title: Optional[str] = None, workspace_name: Optional[str] = None) -> Path:
    desired_name = workspace_name or build_workspace_name(arxiv_id, title)
    base = root / desired_name
    if not base.exists():
        matches = sorted(path for path in root.glob(f"{arxiv_id}_*") if path.is_dir())
        if len(matches) == 1:
            base = matches[0]
    for sub in ["raw", "images", "cache", "logs"]:
        (base / sub).mkdir(parents=True, exist_ok=True)
    return base


def write_json(path: Path, payload: Dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_workspace(root: Path, input_text: str):
    ids = resolve_ids(input_text)
    workspace = ensure_workspace(root, ids["arxiv_id"], ids.get("title"), ids.get("workspace_name"))
    return workspace, ids


def http_get(url: str, timeout: int = 30):
    return requests.get(url, timeout=timeout, headers={"User-Agent": "paper-reading-skill"})
