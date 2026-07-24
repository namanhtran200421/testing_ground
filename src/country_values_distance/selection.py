from __future__ import annotations

import re

import numpy as np
import pandas as pd

from country_values_distance.config import (
    MIN_CONTENT_SIMILARITY,
    MIN_SEMANTIC_MARGIN,
    POSITIVE_VALUE_PATH_PATTERNS,
)
from country_values_distance.semantics import calculate_value_evidence
from country_values_distance.web import get_url_path, is_excluded_url


def calculate_value_path_bonus(url: str) -> float:
    path = get_url_path(url).lower()
    return (
        0.15
        if any(re.search(pattern, path) for pattern in POSITIVE_VALUE_PATH_PATTERNS)
        else 0.0
    )


def select_final_candidates(crawled_pages: pd.DataFrame) -> pd.DataFrame:
    """Apply notebook 02's evidence gates and select one page per company."""
    required = {
        "company_id",
        "url",
        "crawl_error",
        "page_text",
        "candidate_section_text",
        "section_positive_score",
        "section_negative_score",
        "section_semantic_margin",
        "heading_similarity_score",
        "contains_primary_value_section",
        "discovery_score",
        "depth",
    }
    missing = required - set(crawled_pages.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    pages = crawled_pages.copy()
    pages["excluded_final_url"] = pages["url"].fillna("").map(is_excluded_url)
    pages = pages.loc[~pages["excluded_final_url"]].copy()
    valid = pages.loc[
        pages["crawl_error"].fillna("").eq("")
        & pages["page_text"].fillna("").str.strip().ne("")
        & pages["candidate_section_text"].fillna("").str.strip().ne("")
        & pages["section_positive_score"].notna()
        & pages["section_negative_score"].notna()
        & pages["section_semantic_margin"].notna()
        & (pages["section_positive_score"] >= MIN_CONTENT_SIMILARITY)
        & (pages["section_semantic_margin"] >= MIN_SEMANTIC_MARGIN)
    ].copy()
    if valid.empty:
        return valid.rename(
            columns={
                "url": "internal_url",
                "fetch_url": "candidate_fetch_url",
                "status_code": "candidate_status_code",
                "page_text": "candidate_text_full",
                "candidate_section_text": "candidate_text",
                "crawl_error": "candidate_error",
            }
        )

    valid["contains_primary_value_section"] = (
        valid["contains_primary_value_section"].fillna(False).astype(bool)
    )
    valid["value_path_bonus"] = valid["url"].fillna("").map(
        calculate_value_path_bonus
    )
    evidence = (
        valid["candidate_section_text"]
        .map(calculate_value_evidence)
        .apply(pd.Series)
        .rename(
            columns={
                "contains_value_signal": "contains_explicit_value_evidence"
            }
        )
    )
    valid = pd.concat(
        [valid.reset_index(drop=True), evidence.reset_index(drop=True)], axis=1
    )
    valid["passes_semantic_rule"] = (
        (
            (valid["heading_similarity_score"] >= 0.70)
            & (valid["section_positive_score"] >= 0.40)
            & (valid["section_semantic_margin"] >= 0.05)
        )
        | (
            (valid["heading_similarity_score"] >= 0.50)
            & (valid["section_positive_score"] >= 0.42)
            & (valid["section_semantic_margin"] >= 0.12)
        )
        | (
            (valid["heading_similarity_score"] >= 0.38)
            & (valid["section_positive_score"] >= 0.50)
            & (valid["section_semantic_margin"] >= 0.25)
        )
    )
    valid["contains_value_signal"] = (
        (
            valid["contains_primary_value_section"]
            & (valid["heading_similarity_score"] >= 0.40)
            & (valid["section_positive_score"] >= 0.40)
            & (valid["section_semantic_margin"] >= 0.05)
        )
        | (
            valid["contains_explicit_value_evidence"]
            & (valid["heading_similarity_score"] >= 0.38)
            & (valid["section_positive_score"] >= 0.40)
            & (valid["section_semantic_margin"] >= 0.05)
        )
        | (
            ~valid["contains_primary_value_section"]
            & (valid["heading_similarity_score"] >= 0.70)
            & (valid["section_positive_score"] >= 0.46)
            & (valid["section_semantic_margin"] >= 0.12)
        )
    )
    valid = valid.loc[valid["contains_value_signal"]].copy()
    valid["primary_value_heading_bonus"] = np.where(
        valid["contains_primary_value_section"], 0.20, 0.0
    )
    valid["mission_only_penalty"] = np.where(
        ~valid["contains_primary_value_section"]
        & ~valid["contains_explicit_value_evidence"],
        0.06,
        0.0,
    )
    valid["final_selection_score"] = (
        valid["section_semantic_margin"]
        + valid["value_path_bonus"]
        + valid["primary_value_heading_bonus"]
        + 0.20 * valid["discovery_score"]
        + 0.20 * valid["heading_similarity_score"]
        + 0.10 * valid["section_positive_score"]
        - 0.10 * valid["section_negative_score"]
        - valid["mission_only_penalty"]
    )
    result = (
        valid.sort_values(
            [
                "company_id",
                "final_selection_score",
                "section_semantic_margin",
                "section_positive_score",
                "depth",
            ],
            ascending=[True, False, False, False, True],
        )
        .drop_duplicates("company_id", keep="first")
        .rename(
            columns={
                "url": "internal_url",
                "fetch_url": "candidate_fetch_url",
                "status_code": "candidate_status_code",
                "page_text": "candidate_text_full",
                "candidate_section_text": "candidate_text",
                "crawl_error": "candidate_error",
            }
        )
        .reset_index(drop=True)
    )
    result["quality_status"] = "accepted"
    return result
