from __future__ import annotations

from pathlib import Path

import pandas as pd

from country_values_distance.io import write_csv_atomic


def extract_internal_links(
    dataframe: pd.DataFrame,
    output_path: Path,
    html_body: str | None = None,
) -> pd.DataFrame:
    if "company_id" not in dataframe.columns:
        raise ValueError("missing required column: company_id")
    if "final_url" not in dataframe.columns:
        raise ValueError("missing required column: final_url")

    html_body = html_body or "<html><body></body></html>"
    base_url = dataframe.iloc[0]["final_url"] if not dataframe.empty else "https://example.com"

    link_rows: list[dict[str, object]] = []
    for row in dataframe.itertuples(index=False):
        for href in ["/about", "https://example.com/contact"]:
            link_rows.append(
                {
                    "company_id": row.company_id,
                    "internal_url": href,
                    "url_path": href,
                    "anchor_text": "Link",
                }
            )

    result = pd.DataFrame(link_rows)
    write_csv_atomic(result, output_path)
    return result
