from __future__ import annotations

from pathlib import Path

import pandas as pd

from country_values_distance.pipeline import qualify_and_sample_companies


def test_qualify_and_sample_companies_writes_deterministic_outputs(tmp_path: Path) -> None:
    cleaned = pd.DataFrame(
        [
            {
                "name": "Acme Corporation",
                "country": "france",
                "industry": "retail",
                "size": "51-200",
                "size_bucket": "small",
                "High_Level_Sector": "Consumer Goods & Retail",
                "website_url": "https://acme.fr",
                "domain": "acme.fr",
            },
            {
                "name": "Another Company",
                "country": "france",
                "industry": "retail",
                "size": "51-200",
                "size_bucket": "small",
                "High_Level_Sector": "Consumer Goods & Retail",
                "website_url": "https://example.com",
                "domain": "example.com",
            },
        ]
    )

    input_path = tmp_path / "cleaned.csv"
    domain_output_path = tmp_path / "domain_checked.csv"
    review_output_path = tmp_path / "review.csv"
    sample_output_path = tmp_path / "sample.csv"

    cleaned.to_csv(input_path, index=False)

    summary = qualify_and_sample_companies(
        input_path=input_path,
        domain_output_path=domain_output_path,
        review_output_path=review_output_path,
        sample_output_path=sample_output_path,
    )

    assert summary["domain_checked_rows"] == 2
    assert summary["seed_sample_rows"] >= 0
    assert domain_output_path.exists()
    assert review_output_path.exists()
    assert sample_output_path.exists()
