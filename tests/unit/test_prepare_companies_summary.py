from __future__ import annotations

import pandas as pd

from country_values_distance.cleaning import prepare_companies


def test_prepare_companies_returns_stage_summary(tmp_path) -> None:
    raw_input = tmp_path / "input.csv"
    pd.DataFrame(
        {
            "NAME": ["Acme Group", "Solo Shop", "Outlier"],
            "WEBSITE": ["https://acmegroup.fr", "soloshop.com", "example.org"],
            "COUNTRY": ["france", "france", "france"],
            "INDUSTRY": ["retail", "unknown industry", "retail"],
            "FOUNDED": [2020, 2018, 2021],
            "SIZE": ["51-200", "11-50", "11-50"],
        }
    ).to_csv(raw_input, index=False)

    output_path = tmp_path / "cleaned.csv"
    summary = prepare_companies(input_path=raw_input, output_path=output_path)

    assert summary["written_rows"] == 3
    assert summary["unmapped_industry_rows"] == 1
    assert summary["input_rows"] == 3
