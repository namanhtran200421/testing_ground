from __future__ import annotations

import asyncio

import httpx
import pandas as pd

from country_values_distance.crawler import run_company_crawls
from country_values_distance.robots import run_robots_validation
from country_values_distance.selection import select_final_candidates
from country_values_distance.semantics import (
    calculate_value_evidence,
    split_text_into_chunks,
)
from country_values_distance.web import extract_internal_links_from_page


def test_internal_link_discovery_normalises_deduplicates_and_filters() -> None:
    html = """
    <a href="/our-values?tracking=1#top">Values</a>
    <a href="/our-values">Duplicate</a>
    <a href="/contact">Contact</a>
    <a href="https://other.example/values">External</a>
    <a href="/report.pdf">PDF</a>
    """
    links = extract_internal_links_from_page(
        html, "https://www.example.com/about", "https://example.com"
    )
    assert [link["internal_url"] for link in links] == [
        "https://www.example.com/our-values"
    ]
    assert links[0]["anchor_text"] == "Values"


def test_text_chunks_overlap_and_value_evidence_matches_notebook_rules() -> None:
    chunks = split_text_into_chunks(" ".join(["word"] * 800), chunk_size=100, overlap=20)
    assert len(chunks) > 1
    evidence = calculate_value_evidence(
        "Integrity, respect, accountability and excellence guide every decision."
    )
    assert evidence["named_value_matches"] == 4
    assert evidence["contains_value_signal"]


def test_final_selection_prefers_primary_values_page() -> None:
    common = {
        "company_id": "C0001",
        "name": "Acme",
        "country": "france",
        "domain": "acme.fr",
        "size_bucket": "large",
        "crawl_error": "",
        "page_text": "x" * 500,
        "candidate_section_count": 1,
        "content_positive_score": 0.6,
        "content_negative_score": 0.2,
        "semantic_margin": 0.4,
        "section_positive_score": 0.55,
        "section_negative_score": 0.25,
        "section_semantic_margin": 0.30,
        "heading_similarity_score": 0.75,
        "discovery_score": 0.8,
        "depth": 1,
        "fetch_url": "",
        "status_code": 200,
    }
    pages = pd.DataFrame(
        [
            {
                **common,
                "url": "https://acme.fr/mission",
                "candidate_section_text": "Our mission is to serve customers.",
                "contains_primary_value_section": False,
            },
            {
                **common,
                "url": "https://acme.fr/our-values",
                "candidate_section_text": "Our values are integrity, trust and respect.",
                "contains_primary_value_section": True,
            },
        ]
    )
    selected = select_final_candidates(pages)
    assert selected.loc[0, "internal_url"] == "https://acme.fr/our-values"
    assert selected.loc[0, "quality_status"] == "accepted"


class _FakeScorer:
    def score_page_content(self, page_text):
        return {
            "content_positive_score": 0.7,
            "content_negative_score": 0.2,
            "semantic_margin": 0.5,
        }

    def select_best_candidate_section(self, html):
        if "Our Values" not in html:
            return {}
        return {
            "candidate_section_heading": "Our Values",
            "candidate_section_text": "Our Values Integrity Respect Accountability",
            "heading_similarity_score": 0.9,
            "heading_matched_theme": "our values",
            "section_positive_score": 0.7,
            "section_negative_score": 0.2,
            "section_semantic_margin": 0.5,
            "candidate_section_count": 1,
            "contains_primary_value_section": True,
        }

    def score_discovered_links(self, links):
        return [
            {
                **link,
                "feature_text": "Our Values (our values)",
                "similarity_score": 0.9,
                "matched_theme": "our core values",
            }
            for link in links
        ]


def test_bounded_crawler_follows_relevant_child_and_records_audit() -> None:
    filler = " ".join(["company"] * 80)

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        if request.url.path == "/":
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text=f"<html><body>{filler}<a href='/our-values'>Values</a></body></html>",
            )
        if request.url.path == "/our-values":
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text=f"<html><body><h2>Our Values</h2><p>{filler}</p></body></html>",
            )
        return httpx.Response(404)

    company = pd.DataFrame(
        [
            {
                "company_id": "C0001",
                "name": "Acme",
                "country": "france",
                "domain": "example.com",
                "size_bucket": "large",
                "homepage_fetch_url": "https://example.com",
                "robots_url": "https://example.com/robots.txt",
            }
        ]
    )

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), follow_redirects=True
        ) as client:
            return await run_company_crawls(
                company, scorer=_FakeScorer(), client=client
            )

    result = asyncio.run(run())
    assert result["url"].tolist() == [
        "https://example.com",
        "https://example.com/our-values",
    ]
    assert result.loc[0, "links_queued"] == 1
    assert result.loc[1, "candidate_section_heading"] == "Our Values"


def test_production_robots_validation_checks_the_exact_company_path() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text="User-agent: *\nDisallow: /private\nAllow: /"
        )

    companies = pd.DataFrame(
        [
            {
                "company_id": "C0001",
                "domain": "example.com",
                "final_url": "https://example.com/private",
            }
        ]
    )

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            return await run_robots_validation(companies, client=client)

    result = asyncio.run(run())
    assert not bool(result.loc[0, "robots_allowed"])
    assert result.loc[0, "robots_reason"] == "blocked"
