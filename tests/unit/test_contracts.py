from __future__ import annotations

from country_values_distance.config import PROJECT_ROOT, RAW_COMPANY_PATH
from country_values_distance.contracts import (
    CLEANED_COMPANY_COLUMNS,
    DOMAIN_CHECKED_COLUMNS,
    RAW_COMPANY_REQUIRED_COLUMNS,
)


def test_raw_company_contract_is_documented() -> None:
    assert RAW_COMPANY_REQUIRED_COLUMNS == {
        "name",
        "country",
        "industry",
        "size",
        "website",
    }


def test_cleaned_company_contract_is_documented() -> None:
    assert CLEANED_COMPANY_COLUMNS == [
        "name",
        "country",
        "industry",
        "size",
        "size_bucket",
        "High_Level_Sector",
        "website_url",
        "domain",
    ]


def test_domain_checked_contract_is_documented() -> None:
    assert "company_count_for_country_in_pool" in DOMAIN_CHECKED_COLUMNS
    assert "country_website_status" not in DOMAIN_CHECKED_COLUMNS


def test_config_paths_are_cwd_independent(monkeypatch) -> None:
    monkeypatch.chdir("/")

    assert PROJECT_ROOT.name == "testing_ground"
    assert RAW_COMPANY_PATH.is_absolute()
    assert RAW_COMPANY_PATH.exists()
