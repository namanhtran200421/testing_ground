from dataclasses import dataclass
import re
import unicodedata

import pandas as pd
import tldextract

from country_values_distance.config import (
    COUNTRY_DOMAIN_SUFFIXES,
    DOMAIN_KEEP_MIN_SCORE,
    DOMAIN_REVIEW_MIN_SCORE,
    LEGAL_COMPANY_WORDS,
)

_TLD_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())


@dataclass
class DomainQualificationResult:
    domain_checked: pd.DataFrame
    review_candidates: pd.DataFrame
    automatic_candidates: pd.DataFrame


def normalise_to_ascii(value: object) -> str:
    if pd.isna(value):
        return ""

    text = str(value).lower().strip()
    text = unicodedata.normalize("NFKD", text)

    return text.encode("ascii", "ignore").decode("ascii")


def normalise_company_tokens(company_name: object):
    normalised_name = normalise_to_ascii(company_name)
    normalised_name = re.sub(r"[^a-z0-9]+", " ", normalised_name)

    return [
        token
        for token in normalised_name.split()
        if token not in LEGAL_COMPANY_WORDS and len(token) > 1
    ]


def normalise_domain_tokens(domain_name: object):
    if pd.isna(domain_name):
        return []

    extracted = _TLD_EXTRACT(str(domain_name).lower().strip())
    registered_domain = normalise_to_ascii(extracted.domain)

    return [
        token
        for token in re.split(r"[-._]+", registered_domain)
        if len(token) > 1
    ]


def compute_exact_matches(
    company_tokens: list[str],
    domain_tokens: list[str],
):
    matched_tokens = set(company_tokens).intersection(domain_tokens)

    if not matched_tokens:
        return 0, set()

    score = min(len(matched_tokens) * 80, 100)

    return score, matched_tokens


def compute_substring_match(
    company_tokens: list[str],
    domain_tokens: list[str],
    already_matched: set[str],
):
    matched_tokens: set[str] = set()

    for company_token in company_tokens:
        if company_token in already_matched:
            continue

        if len(company_token) < 4:
            continue

        for domain_token in domain_tokens:
            if company_token in domain_token or domain_token in company_token:
                matched_tokens.add(company_token)
                break

    if not matched_tokens:
        return 0, set()

    score = min(len(matched_tokens) * 35, 100)

    return score, matched_tokens


def compute_abbreviation_score(
    company_tokens: list[str],
    domain_tokens: list[str],
):
    if len(company_tokens) < 2 or not domain_tokens:
        return 0, set()

    abbreviation = "".join(token[0] for token in company_tokens)

    for domain_token in domain_tokens:
        if domain_token == abbreviation:
            return 60, set(company_tokens)

        if len(abbreviation) >= 3 and domain_token.startswith(abbreviation):
            return 40, set(company_tokens)

    return 0, set()

def compute_match_score(
    company_name: object,
    domain_name: object,
) -> dict[str, object]:
    company_tokens = normalise_company_tokens(company_name)
    domain_tokens = normalise_domain_tokens(domain_name)

    exact_score, exact_matches = compute_exact_matches(
        company_tokens,
        domain_tokens,
    )

    substring_score, substring_matches = compute_substring_match(
        company_tokens,
        domain_tokens,
        exact_matches,
    )

    matched_before_abbreviation = exact_matches.union(substring_matches)

    abbreviation_score = 0
    abbreviation_matches: set[str] = set()

    if not matched_before_abbreviation:
        abbreviation_score, abbreviation_matches = compute_abbreviation_score(
            company_tokens,
            domain_tokens,
        )

    final_score = min(
        exact_score + substring_score + abbreviation_score,
        100,
    )

    all_matched_tokens = (
        exact_matches
        .union(substring_matches)
        .union(abbreviation_matches)
    )

    return {
        "company_tokens": company_tokens,
        "domain_tokens": domain_tokens,
        "exact_score": exact_score,
        "substring_score": substring_score,
        "abbreviation_score": abbreviation_score,
        "domain_match_score": final_score,
        "matched_tokens": sorted(all_matched_tokens),
    }

def classify_country_domain(
    country: object,
    domain_name: object,
) -> str:
    if pd.isna(country) or pd.isna(domain_name):
        return "unknown"

    normalised_country = str(country).lower().strip()

    extracted = _TLD_EXTRACT(str(domain_name).lower().strip())
    public_suffix = extracted.suffix

    if not public_suffix:
        return "unknown"

    expected_suffixes = COUNTRY_DOMAIN_SUFFIXES.get(
        normalised_country,
        set(),
    )

    def matches_country_suffix(
        suffix: str,
        country_suffix: str,
    ) -> bool:
        return (
            suffix == country_suffix
            or suffix.endswith(f".{country_suffix}")
        )

    if any(
        matches_country_suffix(public_suffix, suffix)
        for suffix in expected_suffixes
    ):
        return "country_match"

    all_country_suffixes = {
        suffix
        for suffixes in COUNTRY_DOMAIN_SUFFIXES.values()
        for suffix in suffixes
    }

    if any(
        matches_country_suffix(public_suffix, suffix)
        for suffix in all_country_suffixes
    ):
        return "country_mismatch"

    return "global_domain"

def classify_domain_match(
    domain_match_score: int,
    country_domain_status: str,
) -> str:
    if country_domain_status == "country_mismatch":
        return "review"

    if domain_match_score >= DOMAIN_KEEP_MIN_SCORE:
        return "keep"

    if domain_match_score >= DOMAIN_REVIEW_MIN_SCORE:
        return "review"

    return "remove"

def evaluate_domain(
    company_name: object,
    country: object,
    domain_name: object,
) -> dict[str, object]:
    match_result = compute_match_score(
        company_name=company_name,
        domain_name=domain_name,
    )

    country_domain_status = classify_country_domain(
        country=country,
        domain_name=domain_name,
    )

    qualification_status = classify_domain_match(
        domain_match_score=match_result["domain_match_score"],
        country_domain_status=country_domain_status,
    )

    return {
        **match_result,
        "country_domain_status": country_domain_status,
        "qualification_status": qualification_status,
    }

def qualify_domains(
    df: pd.DataFrame,
) -> DomainQualificationResult:
    required_columns = {"name", "country", "domain"}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    domain_checked = df.copy().reset_index(drop=True)

    qualification_results = domain_checked.apply(
        lambda row: evaluate_domain(
            company_name=row["name"],
            country=row["country"],
            domain_name=row["domain"],
        ),
        axis=1,
        result_type="expand",
    )

    domain_checked = pd.concat(
        [
            domain_checked,
            qualification_results.reset_index(drop=True),
        ],
        axis=1,
    )

    missing_domain = (
        domain_checked["domain"].isna()
        | domain_checked["domain"].astype(str).str.strip().eq("")
    )

    domain_checked.loc[
        missing_domain,
        "qualification_status",
    ] = "remove"

    company_identifier = (
        "company_id"
        if "company_id" in domain_checked.columns
        else "name"
    )

    domain_checked["companies_using_domain"] = (
        domain_checked.groupby(
            "domain",
            dropna=False,
        )[company_identifier]
        .transform("nunique")
    )

    domain_checked["countries_using_domain"] = (
        domain_checked.groupby(
            "domain",
            dropna=False,
        )["country"]
        .transform("nunique")
    )

    domain_checked["is_shared_domain"] = (
        domain_checked["companies_using_domain"] > 1
    )

    domain_checked.loc[
        domain_checked["is_shared_domain"],
        "qualification_status",
    ] = "review"

    review_candidates = domain_checked.loc[
        domain_checked["qualification_status"] == "review"
    ].copy()

    automatic_candidates = domain_checked.loc[
        domain_checked["qualification_status"] == "keep"
    ].copy()

    return DomainQualificationResult(
        domain_checked=domain_checked,
        review_candidates=review_candidates,
        automatic_candidates=automatic_candidates,
    )