#!/usr/bin/env python3
import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import requests

ARXIV_ID_RE = re.compile(r'(?P<base>\d{4}\.\d{4,5})(?P<version>v\d+)?', re.I)


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


def fetch_latest_version(base_id: str, timeout: int = 20) -> Optional[str]:
    url = f"https://arxiv.org/abs/{base_id}"
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "paper-reading-skill"})
    r.raise_for_status()
    html = r.text
    candidates = re.findall(rf'{re.escape(base_id)}v(\d+)', html)
    if candidates:
        return f"v{max(int(x) for x in candidates)}"
    m = re.search(r'this version,\s*v(\d+)', html, re.I)
    if m:
        return f"v{m.group(1)}"
    return None


def resolve_ids(input_text: str) -> Dict[str, str]:
    parsed = extract_arxiv_id(input_text)
    if not parsed:
        raise ValueError(f"Could not parse arXiv id from input: {input_text}")
    base_id, version = parsed
    latest = version or fetch_latest_version(base_id)
    paper_id_with_version = f"{base_id}{latest}" if latest else base_id
    return {
        "input": input_text,
        "arxiv_id": base_id,
        "version": latest or "",
        "paper_id_with_version": paper_id_with_version,
        "arxiv_abs_url": f"https://arxiv.org/abs/{paper_id_with_version}",
        "arxiv_pdf_url": f"https://arxiv.org/pdf/{paper_id_with_version}.pdf",
        "hjfy_url": f"https://hjfy.top/arxiv/{paper_id_with_version}",
        "papers_cool_url": f"https://papers.cool/arxiv/{paper_id_with_version}",
        "ar5iv_url": f"https://ar5iv.org/html/{paper_id_with_version}",
        "arxiv_src_url": f"https://arxiv.org/src/{paper_id_with_version}",
    }


def ensure_workspace(root: Path, arxiv_id: str) -> Path:
    base = root / arxiv_id
    for sub in ["raw", "images", "cache", "logs"]:
        (base / sub).mkdir(parents=True, exist_ok=True)
    return base


def write_json(path: Path, payload: Dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_workspace(root: Path, input_text: str):
    ids = resolve_ids(input_text)
    workspace = ensure_workspace(root, ids["arxiv_id"])
    return workspace, ids


def http_get(url: str, timeout: int = 30):
    return requests.get(url, timeout=timeout, headers={"User-Agent": "paper-reading-skill"})
