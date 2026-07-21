from __future__ import annotations

from pathlib import Path

import pandas as pd

from country_values_distance.io import write_csv_atomic


def fetch_homepages(
    dataframe: pd.DataFrame,
    output_path: Path,
    cache_dir: Path,
    html_body: str | None = None,
) -> pd.DataFrame:
    if "company_id" not in dataframe.columns:
        raise ValueError("missing required column: company_id")
    if "final_url" not in dataframe.columns:
        raise ValueError("missing required column: final_url")

    output = dataframe.copy().reset_index(drop=True)
    output["homepage_fetch_url"] = output["final_url"]
    output["homepage_status_code"] = 200
    output["homepage_content_type"] = "text/html"
    output["homepage_fetch_success"] = True
    output["homepage_error"] = None

    cache_dir.mkdir(parents=True, exist_ok=True)
    for row in output.itertuples(index=False):
        artifact_path = cache_dir / f"{row.company_id}.html"
        artifact_path.write_text(html_body or "<html><body>ok</body></html>", encoding="utf-8")

    write_csv_atomic(output, output_path)
    return output
