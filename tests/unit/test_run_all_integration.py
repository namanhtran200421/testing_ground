from __future__ import annotations

from pathlib import Path

import pandas as pd

from country_values_distance.pipeline import run_all


def test_run_all_creates_manifest_and_stage_outputs(tmp_path: Path, monkeypatch) -> None:
    raw_input = tmp_path / "raw.csv"
    raw_input.write_text(
        "NAME,WEBSITE,COUNTRY,INDUSTRY,FOUNDED,SIZE\n"
        "Acme Group,https://acmegroup.fr,france,retail,2020,51-200\n"
        "Solo Shop,soloshop.com,france,retail,2018,11-50\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "outputs"

    def fake_run_availability_checks(dataframe, checkpoint_path, max_workers, client=None):
        result = dataframe.copy()
        result["company_id"] = range(1, len(result) + 1)
        result["final_url"] = result["website_url"]
        result["domain"] = result["domain"]
        return result

    monkeypatch.setattr(
        "country_values_distance.pipeline.run_availability_checks",
        fake_run_availability_checks,
    )

    manifest = run_all(
        input_path=raw_input,
        output_dir=output_dir,
        workers=2,
        seed=42,
    )

    assert manifest["prepare_summary"]["input_rows"] == 2
    assert (output_dir / "company_run_manifest.json").exists()
    assert (output_dir / "company_cleaned_target_countries.csv").exists()
    assert (output_dir / "company_seed_sample.csv").exists()
    assert (output_dir / "company_internal_links.csv").exists()
