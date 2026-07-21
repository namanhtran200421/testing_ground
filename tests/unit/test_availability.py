from __future__ import annotations

import asyncio
from pathlib import Path

import pandas as pd

from country_values_distance.avail_check import build_url_variants, run_availability_checks


def test_build_url_variants_normalizes_and_deduplicates() -> None:
    variants = build_url_variants("example.com")

    assert variants == [
        "https://example.com/",
        "https://www.example.com/",
    ]


def test_run_availability_checks_uses_bounded_workers(tmp_path: Path, monkeypatch) -> None:
    frame = pd.DataFrame(
        {
            "website_url": [
                "https://example.com",
                "https://example.org",
                "https://example.net",
            ]
        }
    )

    active_count = 0
    max_seen = 0

    async def fake_check_website(client, website_url):
        nonlocal active_count, max_seen
        active_count += 1
        max_seen = max(max_seen, active_count)
        await asyncio.sleep(0.01)
        active_count -= 1
        return {
            "is_website_reachable": True,
            "final_url": website_url,
            "status_code": 200,
            "content_type": "text/html",
            "failure_reason": None,
            "checked_url_variants": "[]",
            "http_attempts": 1,
        }

    monkeypatch.setattr("country_values_distance.avail_check.check_website", fake_check_website)

    checkpoint_path = tmp_path / "availability-checkpoint.csv"
    result = asyncio.run(
        run_availability_checks(
            dataframe=frame,
            checkpoint_path=checkpoint_path,
            max_workers=2,
        )
    )

    assert len(result) == 3
    assert max_seen <= 2
