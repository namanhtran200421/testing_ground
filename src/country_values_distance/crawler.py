from __future__ import annotations

import asyncio
import heapq
from collections import deque
from typing import Any

import httpx
import numpy as np
import pandas as pd

from country_values_distance.config import (
    MAX_CHILDREN_PER_PAGE,
    MAX_CONCURRENT_REQUESTS,
    MAX_CRAWL_DEPTH,
    MAX_PAGES_PER_COMPANY,
    MIN_LINK_SIMILARITY,
    MIN_PAGE_TEXT_CHARACTERS,
    MIN_PAGE_TEXT_WORDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)
from country_values_distance.robots import (
    build_robots_parser,
    fetch_robots_text,
)
from country_values_distance.semantics import SemanticScorer
from country_values_distance.web import (
    clean_internal_url,
    clean_page_text,
    extract_internal_links_from_page,
    is_excluded_url,
    is_same_homepage_domain,
)


CRAWL_COLUMNS = [
    "company_id",
    "name",
    "country",
    "domain",
    "size_bucket",
    "url",
    "fetch_url",
    "parent_url",
    "depth",
    "anchor_text",
    "feature_text",
    "discovery_score",
    "matched_theme",
    "status_code",
    "content_type",
    "page_text",
    "content_positive_score",
    "content_negative_score",
    "semantic_margin",
    "links_discovered",
    "links_queued",
    "crawl_error",
    "candidate_section_heading",
    "candidate_section_text",
    "section_positive_score",
    "section_negative_score",
    "section_semantic_margin",
    "candidate_section_count",
    "heading_similarity_score",
    "heading_matched_theme",
    "contains_primary_value_section",
]


def _result_row(
    company: pd.Series,
    current: dict[str, Any],
    *,
    fetch_url: str | None = None,
    status_code: int | None = None,
    content_type: str | None = None,
    page_text: str = "",
    crawl_error: str = "",
    content_score: dict[str, float] | None = None,
    section_result: dict[str, Any] | None = None,
    links_discovered: int = 0,
    links_queued: int = 0,
) -> dict[str, Any]:
    content_score = content_score or {}
    section_result = section_result or {}
    return {
        "company_id": company["company_id"],
        "name": company.get("name", ""),
        "country": company.get("country", ""),
        "domain": company.get("domain", ""),
        "size_bucket": company.get("size_bucket", ""),
        "url": current["url"],
        "fetch_url": fetch_url,
        "parent_url": current["parent_url"],
        "depth": current["depth"],
        "anchor_text": current["anchor_text"],
        "feature_text": current["feature_text"],
        "discovery_score": current["discovery_score"],
        "matched_theme": current["matched_theme"],
        "status_code": status_code,
        "content_type": content_type,
        "page_text": page_text,
        "content_positive_score": content_score.get(
            "content_positive_score", np.nan
        ),
        "content_negative_score": content_score.get(
            "content_negative_score", np.nan
        ),
        "semantic_margin": content_score.get("semantic_margin", np.nan),
        "links_discovered": links_discovered,
        "links_queued": links_queued,
        "crawl_error": crawl_error,
        "candidate_section_heading": section_result.get(
            "candidate_section_heading", ""
        ),
        "candidate_section_text": section_result.get(
            "candidate_section_text", ""
        ),
        "section_positive_score": section_result.get(
            "section_positive_score", np.nan
        ),
        "section_negative_score": section_result.get(
            "section_negative_score", np.nan
        ),
        "section_semantic_margin": section_result.get(
            "section_semantic_margin", np.nan
        ),
        "candidate_section_count": section_result.get(
            "candidate_section_count", 0
        ),
        "heading_similarity_score": section_result.get(
            "heading_similarity_score", np.nan
        ),
        "heading_matched_theme": section_result.get("heading_matched_theme", ""),
        "contains_primary_value_section": section_result.get(
            "contains_primary_value_section", False
        ),
    }


async def load_company_robots_parser(
    company: pd.Series,
    client: httpx.AsyncClient,
    request_semaphore: asyncio.Semaphore,
):
    robots_url = str(company["robots_url"])
    async with request_semaphore:
        status, text, fetch_error = await fetch_robots_text(client, robots_url)
    if fetch_error or status is None or status >= 400:
        return None
    try:
        return build_robots_parser(robots_url, text)
    except Exception:
        return None


async def crawl_company_website(
    company: pd.Series,
    client: httpx.AsyncClient,
    request_semaphore: asyncio.Semaphore,
    scorer: SemanticScorer,
) -> list[dict[str, Any]]:
    homepage_url = clean_internal_url(str(company["homepage_fetch_url"]))
    robots_parser = await load_company_robots_parser(
        company, client, request_semaphore
    )
    queue = deque(
        [
            {
                "url": homepage_url,
                "parent_url": None,
                "depth": 0,
                "discovery_score": 1.0,
                "matched_theme": "homepage",
                "anchor_text": "",
                "feature_text": "homepage",
            }
        ]
    )
    visited: set[str] = set()
    queued: set[str] = {homepage_url}
    results: list[dict[str, Any]] = []

    while queue and len(visited) < MAX_PAGES_PER_COMPANY:
        current = queue.popleft()
        current_url = current["url"]
        queued.discard(current_url)
        if (
            current_url in visited
            or current["depth"] > MAX_CRAWL_DEPTH
            or is_excluded_url(current_url)
        ):
            continue
        if robots_parser is not None and not robots_parser.can_fetch(
            USER_AGENT, current_url
        ):
            visited.add(current_url)
            results.append(
                _result_row(company, current, crawl_error="robots_blocked")
            )
            continue

        visited.add(current_url)
        try:
            async with request_semaphore:
                response = await client.get(
                    current_url, timeout=REQUEST_TIMEOUT_SECONDS
                )
            status = response.status_code
            content_type = response.headers.get("Content-Type", "").lower()
            fetch_url = clean_internal_url(str(response.url))
            if not is_same_homepage_domain(fetch_url, homepage_url):
                results.append(
                    _result_row(
                        company,
                        current,
                        fetch_url=fetch_url,
                        status_code=status,
                        content_type=content_type,
                        crawl_error="redirected_outside_company_domain",
                    )
                )
                continue
            if status >= 400:
                error = f"http_error_{status}"
                page_text = ""
            elif "text/html" not in content_type:
                error = f"not_html_{content_type}"
                page_text = ""
            else:
                page_text = clean_page_text(response.text)
                if len(page_text) < MIN_PAGE_TEXT_CHARACTERS:
                    error = "page_text_too_short"
                elif len(page_text.split()) < MIN_PAGE_TEXT_WORDS:
                    error = "page_word_count_too_low"
                else:
                    error = ""
            if error:
                results.append(
                    _result_row(
                        company,
                        current,
                        fetch_url=fetch_url,
                        status_code=status,
                        content_type=content_type,
                        crawl_error=error,
                    )
                )
                continue

            content_score = scorer.score_page_content(page_text)
            section_result = scorer.select_best_candidate_section(response.text)
            child_links: list[dict[str, str]] = []
            selected_children: list[dict[str, Any]] = []
            if current["depth"] < MAX_CRAWL_DEPTH:
                child_links = extract_internal_links_from_page(
                    response.text, fetch_url, homepage_url
                )
                eligible = [
                    child
                    for child in scorer.score_discovered_links(child_links)
                    if child["similarity_score"] >= MIN_LINK_SIMILARITY
                    and child["internal_url"] not in visited
                    and child["internal_url"] not in queued
                ]
                selected_children = heapq.nlargest(
                    MAX_CHILDREN_PER_PAGE,
                    eligible,
                    key=lambda child: child["similarity_score"],
                )
                for child in selected_children:
                    child_url = child["internal_url"]
                    queue.append(
                        {
                            "url": child_url,
                            "parent_url": fetch_url,
                            "depth": current["depth"] + 1,
                            "discovery_score": child["similarity_score"],
                            "matched_theme": child["matched_theme"],
                            "anchor_text": child["anchor_text"],
                            "feature_text": child["feature_text"],
                        }
                    )
                    queued.add(child_url)

            results.append(
                _result_row(
                    company,
                    current,
                    fetch_url=fetch_url,
                    status_code=status,
                    content_type=content_type,
                    page_text=page_text,
                    content_score=content_score,
                    section_result=section_result,
                    links_discovered=len(child_links),
                    links_queued=len(selected_children),
                )
            )
        except httpx.HTTPError as error:
            results.append(
                _result_row(
                    company,
                    current,
                    crawl_error=f"fetch_error_{type(error).__name__}",
                )
            )
    return results


async def run_company_crawls(
    dataframe: pd.DataFrame,
    scorer: SemanticScorer | None = None,
    client: httpx.AsyncClient | None = None,
) -> pd.DataFrame:
    required = {"company_id", "homepage_fetch_url", "robots_url"}
    missing = required - set(dataframe.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    scorer = scorer or SemanticScorer()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    owns_client = client is None
    client = client or httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True
    )
    try:
        company_results = await asyncio.gather(
            *(
                crawl_company_website(row, client, semaphore, scorer)
                for _, row in dataframe.iterrows()
            )
        )
    finally:
        if owns_client:
            await client.aclose()
    rows = [page for pages in company_results for page in pages]
    return pd.DataFrame(rows, columns=CRAWL_COLUMNS)
