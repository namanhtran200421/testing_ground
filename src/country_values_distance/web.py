from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

import pandas as pd
from bs4 import BeautifulSoup

from country_values_distance.config import (
    ANCHOR_TEXT_NOISE,
    EXCLUDED_EXTENSIONS,
    EXCLUDED_PATH_PATTERNS,
    MAX_PAGE_TEXT_CHARACTERS,
)


def normalise_domain(url: str) -> str:
    domain = urlparse(str(url)).netloc.lower().strip()
    return domain[4:] if domain.startswith("www.") else domain


def clean_internal_url(url: str) -> str:
    parsed = urlparse(str(url).strip())
    return urlunparse(parsed._replace(query="", fragment="")).rstrip("/")


def get_url_path(url: str) -> str:
    return urlparse(str(url)).path or "/"


def get_normalised_url_path(url: str) -> str:
    path = get_url_path(url).lower()
    return re.sub(r"\.(html?|php|aspx?)$", "", path).rstrip("/")


def is_same_homepage_domain(url: str, homepage_url: str) -> bool:
    link_domain = normalise_domain(url)
    homepage_domain = normalise_domain(homepage_url)
    return link_domain == homepage_domain or link_domain.endswith(
        "." + homepage_domain
    )


def clean_anchor_text(anchor_text: str) -> str:
    return re.sub(r"\s+", " ", str(anchor_text)).strip()[:300]


def clean_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "header",
            "footer",
            "nav",
            "form",
            "aside",
            "iframe",
            "svg",
            "button",
        ]
    ):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))[
        :MAX_PAGE_TEXT_CHARACTERS
    ]


def is_excluded_url(url: str) -> bool:
    path = get_normalised_url_path(url)
    return any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS) or any(
        re.search(pattern, path) for pattern in EXCLUDED_PATH_PATTERNS
    )


def improved_extract_path_features(url_path: str) -> str:
    if pd.isna(url_path):
        return ""
    path = str(url_path).lower().strip()
    path = re.sub(r"\.[a-zA-Z0-9]+$", "", path)
    for word in (
        "index",
        "home",
        "page",
        "wp-content",
        "uploads",
        "assets",
        "attachment",
    ):
        path = path.replace(word, " ")
    words = re.sub(r"[/_-]+", " ", path)
    for pattern, replacement in {
        r"\bco\b": "company",
        r"\babt\b": "about",
        r"\bprofile\b": "company profile",
        r"\bvis\b": "vision",
        r"\bval\b": "values",
    }.items():
        words = re.sub(pattern, replacement, words)
    return " ".join(words.split())


def build_feature_text(anchor_text: str, url_path: str) -> str:
    anchor = clean_anchor_text(anchor_text)
    path_features = improved_extract_path_features(url_path)
    if anchor.lower() in ANCHOR_TEXT_NOISE:
        anchor = ""
    if anchor and path_features:
        return f"{anchor} ({path_features})"
    return anchor or path_features


def extract_internal_links_from_page(
    html: str,
    current_page_url: str,
    allowed_domain_url: str,
) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    unique_links: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        raw_link = anchor.get("href")
        if not raw_link:
            continue
        internal_url = clean_internal_url(urljoin(current_page_url, raw_link))
        if not internal_url.startswith(("https://", "http://")):
            continue
        if not is_same_homepage_domain(internal_url, allowed_domain_url):
            continue
        if is_excluded_url(internal_url) or internal_url in seen_urls:
            continue
        seen_urls.add(internal_url)
        unique_links.append(
            {
                "raw_link": raw_link,
                "internal_url": internal_url,
                "url_path": get_url_path(internal_url),
                "anchor_text": clean_anchor_text(anchor.get_text(" ")),
            }
        )
    return unique_links
