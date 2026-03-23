#!/usr/bin/env python3
"""Fetch reproducible external context for a paper-reading report."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) paper-reading-skill/4.0"
INTERPRETATION_HINTS = (
    "解读",
    "详解",
    "论文",
    "阅读",
    "笔记",
    "review",
    "精读",
    "拆解",
    "解析",
    "推理",
    "sota",
    "重构",
)
GENERIC_EXCLUDES = (
    "知乎 - 有问题",
    "发现 - 知乎",
    "话题广场",
    "用户主页",
    "下载",
    "专栏目录",
    "alphaXiv",
    "ChatPaper",
    "Bytez",
    "GitHub",
)
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "that",
    "this",
    "using",
    "towards",
    "vision",
    "language",
    "action",
    "thinking",
    "space",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch external report context from arXiv, hjfy, and papers.cool."
        )
    )
    parser.add_argument("--artifacts", required=True, help="Path to outputs/<paper_id>/artifacts.json")
    parser.add_argument("--arxiv-id", help="Optional arXiv ID or URL override.")
    parser.add_argument("--output", help="Optional explicit output path for report_context.json")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_arxiv_id(value: str) -> str | None:
    candidate = value.strip().removeprefix("arxiv:")
    match = re.search(r"(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?(?:\.pdf)?", candidate)
    if match:
        return match.group(1)
    match = re.fullmatch(r"([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", candidate)
    if match:
        return match.group(1)
    return None


def request_text(url: str, timeout: int = 30, headers: dict[str, str] | None = None) -> str:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def request_json(url: str, timeout: int = 30, headers: dict[str, str] | None = None) -> dict[str, Any]:
    return json.loads(request_text(url, timeout=timeout, headers=headers))


def visit_url(url: str, timeout: int = 30) -> None:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        response.read(512)


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(strip_tags(value))).strip()


def normalize_text_for_match(value: str) -> str:
    lowered = normalize_space(value).lower()
    lowered = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def resolve_arxiv_base_id(artifacts: dict[str, Any], override: str | None) -> str | None:
    candidates: list[str] = []
    if override:
        candidates.append(override)

    input_source = artifacts.get("input_source")
    if isinstance(input_source, dict):
        for key in ("arxiv_id", "original", "local_pdf", "source_tar", "local_source_tar"):
            value = input_source.get(key)
            if isinstance(value, str):
                candidates.append(value)

    paper_id = artifacts.get("paper_id")
    if isinstance(paper_id, str):
        candidates.append(paper_id)

    for candidate in candidates:
        arxiv_id = parse_arxiv_id(candidate)
        if arxiv_id:
            return arxiv_id
    return None


def parse_latest_versioned_id(base_id: str, html: str) -> str:
    patterns = [
        rf"https://arxiv\.org/abs/({re.escape(base_id)}v\d+)",
        rf"arXiv:({re.escape(base_id)}v\d+)",
        rf"({re.escape(base_id)}v\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return f"{base_id}v1"


def parse_arxiv_title(html: str) -> str | None:
    match = re.search(r'<h1[^>]*class="title[^"]*"[^>]*>(.*?)</h1>', html, flags=re.DOTALL)
    if not match:
        return None
    title = normalize_space(match.group(1))
    title = re.sub(r"^Title:\s*", "", title, flags=re.IGNORECASE)
    return title or None


def parse_papers_cool_keywords(html: str, base_id: str) -> list[str]:
    pattern = rf'<div id="{re.escape(base_id)}" class="panel paper" keywords="([^"]*)"'
    match = re.search(pattern, html)
    if not match:
        return []
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def parse_papers_cool_entries(html: str, target_base_id: str) -> list[dict[str, str]]:
    panel_pattern = re.compile(
        r'<div id="(?P<paper_id>[^"]+)" class="panel paper" keywords="(?P<keywords>[^"]*)">(?P<body>.*?)<hr id="fold-[^"]+"',
        re.DOTALL,
    )
    title_pattern = re.compile(
        r'<a id="title-[^"]+" class="title-link[^"]*" href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.DOTALL,
    )
    summary_pattern = re.compile(r'<p id="summary-[^"]+" class="summary[^"]*">(?P<summary>.*?)</p>', re.DOTALL)
    date_pattern = re.compile(r'<span class="date-data">(?P<date>.*?)</span>', re.DOTALL)

    entries: list[dict[str, str]] = []
    for match in panel_pattern.finditer(html):
        paper_id = normalize_space(match.group("paper_id"))
        if paper_id == target_base_id:
            continue

        body = match.group("body")
        title_match = title_pattern.search(body)
        if not title_match:
            continue

        summary_match = summary_pattern.search(body)
        date_match = date_pattern.search(body)
        keywords = [item.strip() for item in match.group("keywords").split(",") if item.strip()]
        summary = normalize_space(summary_match.group("summary")) if summary_match else ""
        publish_date = normalize_space(date_match.group("date")) if date_match else ""
        notes = summary[:180] + ("..." if len(summary) > 180 else "")

        entries.append(
            {
                "paper_id": paper_id,
                "title": normalize_space(title_match.group("title")),
                "url": f"https://papers.cool{title_match.group('href')}",
                "why_related": "papers.cool related search keyword overlap",
                "notes": f"Publish: {publish_date}. Summary: {notes}".strip(),
                "keywords": ", ".join(keywords),
            }
        )
    return entries


def derive_title_metadata(title: str) -> dict[str, Any]:
    clean_title = normalize_space(title)
    acronym = ""
    if ":" in clean_title:
        prefix, remainder = clean_title.split(":", 1)
        prefix = prefix.strip()
        if 2 <= len(prefix) <= 40 and re.search(r"[A-Za-z]", prefix):
            acronym = prefix
        core_source = remainder.strip()
    else:
        core_source = clean_title

    core_phrase_words = core_source.split()
    core_phrase = " ".join(core_phrase_words[:8]).strip()
    if not core_phrase:
        core_phrase = clean_title

    keyword_candidates = [token for token in re.findall(r"[A-Za-z0-9-]+", clean_title) if len(token) >= 3]
    keywords: list[str] = []
    for token in keyword_candidates:
        lowered = token.lower()
        if lowered in STOPWORDS:
            continue
        if lowered not in keywords:
            keywords.append(lowered)

    return {
        "full_title": clean_title,
        "acronym": acronym,
        "core_phrase": core_phrase,
        "keywords": keywords[:10],
        "full_title_norm": normalize_text_for_match(clean_title),
        "acronym_norm": normalize_text_for_match(acronym),
        "core_phrase_norm": normalize_text_for_match(core_phrase),
    }


def canonicalize_blog_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    path = parsed.path

    zhihu_match = re.match(r"^/p/(\d+)$", path)
    if netloc == "zhuanlan.zhihu.com" and zhihu_match:
        return f"https://zhuanlan.zhihu.com/p/{zhihu_match.group(1)}"

    csdn_match = re.search(r"(/[^/]+/article/details/\d+)$", path)
    if netloc.endswith(".csdn.net") and csdn_match:
        return f"https://{netloc}{csdn_match.group(1)}"

    return None


def classify_page_type(url: str) -> str | None:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc == "zhuanlan.zhihu.com" and re.match(r"^/p/\d+$", parsed.path):
        return "知乎专栏文章"
    if netloc.endswith(".csdn.net") and re.search(r"/article/details/\d+$", parsed.path):
        return "CSDN 博客文章"
    return None


def title_mentions_target(title: str, meta: dict[str, Any]) -> bool:
    title_norm = normalize_text_for_match(title)
    if meta["acronym_norm"] and meta["acronym_norm"] in title_norm:
        return True
    if meta["core_phrase_norm"] and meta["core_phrase_norm"] in title_norm:
        return True
    hits = sum(1 for token in meta["keywords"] if token in title_norm)
    return hits >= 4 and ("vla" in title_norm or "driving" in title_norm or "autonomous" in title_norm)


def candidate_mentions_target(title: str, snippet: str, meta: dict[str, Any]) -> bool:
    if title_mentions_target(title, meta):
        return True
    combined = normalize_text_for_match(f"{title} {snippet}")
    return bool(meta["full_title_norm"] and meta["full_title_norm"] in combined)


def candidate_looks_like_interpretation(title: str, snippet: str) -> bool:
    combined = normalize_space(f"{title} {snippet}")
    lowered = combined.lower()
    if any(term.lower() in lowered for term in GENERIC_EXCLUDES):
        return False
    if any(term.lower() in lowered for term in INTERPRETATION_HINTS):
        return True
    return len(normalize_space(snippet)) >= 80 and any(symbol in combined for symbol in (":", "：", "！"))


def fetch_page_title(url: str) -> tuple[str | None, str]:
    try:
        page_html = request_text(url, headers={"Referer": url})
    except Exception as exc:  # noqa: BLE001
        return None, f"抓取受限：{exc}"

    match = re.search(r"<title>(.*?)</title>", page_html, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return None, "正文可访问，但未提取到标题"
    return normalize_space(match.group(1)), "正文可访问"


def extract_last_html_text(html: str, end_index: int) -> str:
    window = html[max(0, end_index - 2000) : end_index]
    candidates = re.findall(r"<p[^>]*>(.*?)</p>", window, flags=re.DOTALL | re.IGNORECASE)
    if not candidates:
        candidates = re.findall(r'<div[^>]*class="[^"]*(?:summary|ellipsis|space-txt)[^"]*"[^>]*>(.*?)</div>', window, flags=re.DOTALL | re.IGNORECASE)
    if not candidates:
        return ""
    return normalize_space(candidates[-1])


def parse_sogou_zhihu_candidates(html: str, meta: dict[str, Any]) -> list[dict[str, Any]]:
    pattern = re.compile(
        r'data-url="(?P<url>https://zhuanlan\.zhihu\.com/p/\d+)"[^>]*data-title="(?P<title>[^"]+)"',
        flags=re.DOTALL,
    )
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for match in pattern.finditer(html):
        url = canonicalize_blog_url(match.group("url"))
        if not url or url in seen:
            continue

        raw_title = normalize_space(unquote(match.group("title")))
        snippet = extract_last_html_text(html, match.start())

        if raw_title.startswith("http"):
            raw_title = ""
        if not raw_title:
            window = html[max(0, match.start() - 1200) : match.start()]
            headings = re.findall(r"<h3[^>]*>(.*?)</h3>", window, flags=re.DOTALL | re.IGNORECASE)
            if headings:
                raw_title = normalize_space(headings[-1])

        if not raw_title:
            continue
        if not candidate_mentions_target(raw_title, snippet, meta):
            continue
        if not candidate_looks_like_interpretation(raw_title, snippet):
            continue

        page_title, verification_status = fetch_page_title(url)
        final_title = page_title or raw_title
        candidates.append(
            {
                "title": final_title,
                "url": url,
                "platform": "知乎",
                "page_type": "知乎专栏文章",
                "verification_status": verification_status if page_title else "搜索摘要可核验",
                "why_worth_reading": snippet[:160] + ("..." if len(snippet) > 160 else "") if snippet else "搜索结果摘要表明它在解读该论文，而不是聚合转发。",
            }
        )
        seen.add(url)

    return candidates


def search_zhihu_articles(query: str, meta: dict[str, Any]) -> list[dict[str, Any]]:
    html = request_text(f"https://www.sogou.com/web?query={quote(query)}")
    return parse_sogou_zhihu_candidates(html, meta)


def search_csdn_articles(engine_query: str, meta: dict[str, Any]) -> list[dict[str, Any]]:
    api_url = "https://so.csdn.net/api/v3/search?" + urlencode({"q": engine_query, "p": 1, "t": "blog"})
    data = request_json(api_url, headers={"Referer": "https://so.csdn.net/"})
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in list(data.get("result_vos") or []):
        if not isinstance(item, dict):
            continue
        url = canonicalize_blog_url(str(item.get("url") or ""))
        if not url or url in seen:
            continue

        title = normalize_space(str(item.get("title") or ""))
        snippet = normalize_space(str(item.get("body") or ""))
        if not title:
            continue
        if not candidate_mentions_target(title, snippet, meta):
            continue
        if not candidate_looks_like_interpretation(title, snippet):
            continue

        page_title, verification_status = fetch_page_title(url)
        final_title = page_title or title
        candidates.append(
            {
                "title": final_title,
                "url": url,
                "platform": "CSDN",
                "page_type": "CSDN 博客文章",
                "verification_status": verification_status if page_title else "搜索摘要可核验",
                "why_worth_reading": snippet[:160] + ("..." if len(snippet) > 160 else "") if snippet else "搜索结果摘要表明它在具体拆解论文机制或结果。",
            }
        )
        seen.add(url)

    return candidates


def build_community_query_specs(meta: dict[str, Any]) -> list[dict[str, str]]:
    full_title = meta["full_title"]
    acronym = meta["acronym"]
    core_phrase = meta["core_phrase"]

    specs = [
        {"platform": "zhihu", "stage": "primary", "human_query": f'zhihu "{full_title}"', "engine_query": f'zhihu "{full_title}"'},
        {"platform": "csdn", "stage": "primary", "human_query": f'csdn "{full_title}"', "engine_query": full_title},
        {"platform": "zhihu", "stage": "secondary", "human_query": f'zhuanlan.zhihu.com "{full_title}"', "engine_query": f'zhuanlan.zhihu.com "{full_title}"'},
        {"platform": "zhihu", "stage": "secondary", "human_query": f'site:zhuanlan.zhihu.com "{full_title}"', "engine_query": f'site:zhuanlan.zhihu.com "{full_title}"'},
        {"platform": "csdn", "stage": "secondary", "human_query": f'site:blog.csdn.net "{full_title}"', "engine_query": full_title},
    ]

    if acronym:
        specs.extend(
            [
                {"platform": "zhihu", "stage": "fallback", "human_query": f"zhihu {acronym}", "engine_query": f"zhihu {acronym}"},
                {"platform": "csdn", "stage": "fallback", "human_query": f"csdn {acronym}", "engine_query": acronym},
            ]
        )
    if core_phrase and core_phrase != full_title:
        specs.extend(
            [
                {"platform": "zhihu", "stage": "fallback", "human_query": f'zhihu "{core_phrase}"', "engine_query": f'zhihu "{core_phrase}"'},
                {"platform": "csdn", "stage": "fallback", "human_query": f'csdn "{core_phrase}"', "engine_query": core_phrase},
            ]
        )
    return specs


def dedupe_community_blogs(blogs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for blog in blogs:
        url = str(blog.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(blog)
    return unique


def collect_community_blogs(meta: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    blogs: list[dict[str, Any]] = []
    query_log: list[dict[str, str]] = []
    gaps: list[str] = []

    specs = build_community_query_specs(meta)
    title_stage_count = 0

    for spec in specs:
        if spec["stage"] == "fallback" and title_stage_count >= 5:
            break

        query_log.append(
            {
                "platform": spec["platform"],
                "stage": spec["stage"],
                "query": spec["human_query"],
                "backend": "sogou-web" if spec["platform"] == "zhihu" else "so.csdn.net/api/v3/search",
            }
        )

        try:
            if spec["platform"] == "zhihu":
                found = search_zhihu_articles(spec["engine_query"], meta)
            else:
                found = search_csdn_articles(spec["engine_query"], meta)
        except Exception as exc:  # noqa: BLE001
            gaps.append(f'{spec["platform"]} 查询失败：{spec["human_query"]} -> {exc}')
            continue

        if found:
            blogs.extend(found)
            blogs = dedupe_community_blogs(blogs)
        if spec["stage"] != "fallback":
            title_stage_count = len(blogs)

    if not blogs:
        gaps.append("标题优先检索、站点补检与简称补救后，仍未独立检索到可核验的知乎 / CSDN 论文解读博客。")
    elif len(blogs) < 5:
        gaps.append(f"当前仅独立检索到 {len(blogs)} 条可核验的知乎 / CSDN 论文解读博客，数量不足 5 条。")

    return blogs[:8], query_log, gaps


def build_empty_context(base_id: str | None, title_guess: str | None) -> dict[str, Any]:
    return {
        "paper_title": title_guess,
        "arxiv_id_base": base_id,
        "arxiv_id_versioned": None,
        "arxiv_abs_url": None,
        "hjfy_url": None,
        "hjfy_visited_at": None,
        "papers_cool_paper_url": None,
        "papers_cool_keywords": [],
        "papers_cool_related_query_url": None,
        "papers_cool_related_papers": [],
        "context_gaps": [],
    }


def main() -> int:
    args = parse_args()
    artifacts_path = Path(args.artifacts).resolve()
    output_dir = artifacts_path.parent
    output_path = Path(args.output).resolve() if args.output else output_dir / "report_context.json"

    artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
    title_guess = str(artifacts.get("title_guess") or "").strip() or None
    base_id = resolve_arxiv_base_id(artifacts, args.arxiv_id)
    context = build_empty_context(base_id, title_guess)

    if base_id is None:
        context["context_gaps"].append("no reliable arXiv ID could be resolved from artifacts or override")
        output_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Generated report context: {output_path}")
        return 0

    arxiv_abs_base_url = f"https://arxiv.org/abs/{base_id}"
    abs_html = ""
    try:
        abs_html = request_text(arxiv_abs_base_url)
        versioned_id = parse_latest_versioned_id(base_id, abs_html)
        if not context["paper_title"]:
            context["paper_title"] = parse_arxiv_title(abs_html)
    except Exception as exc:  # noqa: BLE001
        versioned_id = f"{base_id}v1"
        context["context_gaps"].append(f"failed to fetch arXiv abs page: {exc}")

    context["arxiv_id_versioned"] = versioned_id
    context["arxiv_abs_url"] = f"https://arxiv.org/abs/{versioned_id}"

    hjfy_url = f"https://hjfy.top/arxiv/{versioned_id}"
    context["hjfy_url"] = hjfy_url
    context["hjfy_visited_at"] = utc_now()
    try:
        visit_url(hjfy_url)
    except Exception as exc:  # noqa: BLE001
        context["context_gaps"].append(f"failed to visit hjfy URL: {exc}")

    papers_cool_paper_url = f"https://papers.cool/arxiv/{versioned_id}"
    context["papers_cool_paper_url"] = papers_cool_paper_url
    try:
        papers_cool_html = request_text(papers_cool_paper_url)
        keywords = parse_papers_cool_keywords(papers_cool_html, base_id)
        context["papers_cool_keywords"] = keywords
    except Exception as exc:  # noqa: BLE001
        context["context_gaps"].append(f"failed to fetch papers.cool paper page: {exc}")
        keywords = []

    if keywords:
        keyword_query = ",".join(keywords)
        related_query_url = f"https://papers.cool/arxiv/search?query={quote(keyword_query)}"
        context["papers_cool_related_query_url"] = related_query_url
        try:
            related_html = request_text(related_query_url)
            entries = parse_papers_cool_entries(related_html, base_id)
            context["papers_cool_related_papers"] = entries[:5]
            if not context["papers_cool_related_papers"]:
                context["context_gaps"].append("papers.cool related search returned no usable related paper entries")
        except Exception as exc:  # noqa: BLE001
            context["context_gaps"].append(f"failed to fetch papers.cool related search page: {exc}")
    else:
        context["context_gaps"].append("papers.cool keywords were unavailable for this paper")

    output_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated report context: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
