from __future__ import annotations

from pathlib import Path

import pandas as pd

from country_values_distance.homepage_fetch import fetch_homepages
from country_values_distance.links import extract_internal_links
from country_values_distance.robots import build_robots_url, check_robots


def test_build_robots_url_is_stable() -> None:
    assert build_robots_url("https://example.com/") == "https://example.com/robots.txt"


def test_check_robots_decides_allow_and_reason() -> None:
    frame = pd.DataFrame(
        [
            {
                "company_id": 1,
                "domain": "example.com",
                "final_url": "https://example.com",
            }
        ]
    )

    result = check_robots(frame, html_body="User-agent: *\nDisallow: /private")

    assert not result.loc[0, "robots_allowed"]
    assert "Disallow" in result.loc[0, "robots_reason"]


def test_fetch_homepages_writes_cached_artifacts(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "company_id": 1,
                "final_url": "https://example.com",
            }
        ]
    )

    output_path = tmp_path / "homepage_fetch.csv"
    cache_dir = tmp_path / "homepage_html"
    result = fetch_homepages(frame, output_path=output_path, cache_dir=cache_dir, html_body="<html><body>ok</body></html>")

    assert output_path.exists()
    assert cache_dir.exists()
    assert result["homepage_fetch_success"].sum() == 1


def test_extract_internal_links_writes_machine_readable_rows(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "company_id": 1,
                "final_url": "https://example.com",
                "homepage_html_path": "",
            }
        ]
    )

    output_path = tmp_path / "internal_links.csv"
    html = "<html><body><a href='/about'>About</a><a href='https://example.com/contact'>Contact</a></body></html>"
    result = extract_internal_links(frame, output_path=output_path, html_body=html)

    assert output_path.exists()
    assert len(result) == 2
    assert set(result["company_id"]) == {1}
