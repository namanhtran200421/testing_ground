from __future__ import annotations

RAW_COMPANY_REQUIRED_COLUMNS = {
    "name",
    "country",
    "industry",
    "size",
    "website",
}

CLEANED_COMPANY_COLUMNS = [
    "name",
    "country",
    "industry",
    "size",
    "size_bucket",
    "High_Level_Sector",
    "website_url",
    "domain",
]

DOMAIN_SCORE_COLUMNS = [
    'company_tokens',
    'domain_tokens',
    'full_match_score',
    'substring_match_score',
    'substring_match_score',
    'abbreviation_score',
    'final_score',
    'domain_match_status'
]

DOMAIN_CHECKED_COLUMNS = [
    *CLEANED_COMPANY_COLUMNS, #unpack
    "company_count_for_country_in_pool",
    "total_countries_in_pool",
    *DOMAIN_SCORE_COLUMNS, #unpack
]

DOMAIN_CANDIDATE_COLUMNS = [
    *DOMAIN_CHECKED_COLUMNS, #unpack
    "country_website_status",
    "country_website_priority",
    "companies_using_domain",
    "countries_using_domain",
]

SCRAPE_READY_COLUMNS = [
    "company_id",
    "name",
    "country",
    "industry",
    "size_bucket",
    "domain",
    "final_url",
    "scraping_ready",
]

ROBOTS_CHECK_COLUMNS = [
    "company_id",
    "domain",
    "final_url",
    "robots_url",
    "robots_status_code",
    "robots_allowed",
    "robots_reason",
]

HOMEPAGE_FETCH_COLUMNS = [
    "company_id",
    "final_url",
    "homepage_fetch_url",
    "homepage_status_code",
    "homepage_content_type",
    "homepage_fetch_success",
    "homepage_error",
]

INTERNAL_LINK_COLUMNS = [
    "company_id",
    "internal_url",
    "url_path",
    "anchor_text",
]



