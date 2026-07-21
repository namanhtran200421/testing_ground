from __future__ import annotations

import pandas as pd
import pytest

from country_values_distance.cleaning import prepare_companies
from country_values_distance.contracts import CLEANED_COMPANY_COLUMNS


def test_prepare_companies_requires_input_columns(tmp_path) -> None:
    raw_input = tmp_path / "input.csv"
    pd.DataFrame(
        {
            "name": ["Acme"],
            "country": ["france"],
            "industry": ["retail"],
            "size": ["51-200"],
        }
    ).to_csv(raw_input, index=False)

    output_path = tmp_path / "cleaned.csv"

    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_companies(input_path=raw_input, output_path=output_path)


def test_prepare_companies_writes_documented_output_schema(tmp_path) -> None:
    raw_input = tmp_path / "input.csv"
    pd.DataFrame(
        {
            "NAME": ["Acme Group", "Solo Shop"],
            "WEBSITE": ["https://acmegroup.fr", "soloshop.com"],
            "COUNTRY": ["france", "france"],
            "INDUSTRY": ["retail", "retail"],
            "FOUNDED": [2020, 2018],
            "SIZE": ["51-200", "11-50"],
        }
    ).to_csv(raw_input, index=False)

    output_path = tmp_path / "cleaned.csv"
    prepare_companies(input_path=raw_input, output_path=output_path)

    output = pd.read_csv(output_path)

    assert list(output.columns) == CLEANED_COMPANY_COLUMNS
    assert len(output) == 2
    assert set(output["country"]) == {"france"}
    assert set(output["size_bucket"]) <= {"small", "medium", "large", "enterprise"}
    assert output["High_Level_Sector"].notna().all()
