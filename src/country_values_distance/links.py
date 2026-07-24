from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from country_values_distance.io import write_csv_atomic
from country_values_distance.web import (
    clean_anchor_text,
    clean_internal_url,
    get_url_path,
    is_same_homepage_domain,
)


def extract_internal_links(
    dataframe: pd.DataFrame,
    output_path: Path,
    html_body: str | None = None,
) -> pd.DataFrame:
    """Extract canonical same-domain links from each cached homepage."""
    required = {"company_id", "final_url"}
    missing = required - set(dataframe.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    rows: list[dict[str, object]] = []
    for company in dataframe.to_dict("records"):
        base_url = str(company.get("homepage_fetch_url") or company["final_url"])
        html = html_body
        if html is None:
            html_path = str(company.get("homepage_html_path") or "").strip()
            if not html_path or not Path(html_path).is_file():
                continue
            html = Path(html_path).read_text(encoding="utf-8", errors="replace")

        seen: set[str] = set()
        for anchor in BeautifulSoup(html, "html.parser").find_all("a", href=True):
            url = clean_internal_url(urljoin(base_url, anchor.get("href")))
            if (
                not url.startswith(("http://", "https://"))
                or not is_same_homepage_domain(url, base_url)
                or url in seen
            ):
                continue
            seen.add(url)
            rows.append(
                {
                    "company_id": company["company_id"],
                    "internal_url": url,
                    "url_path": get_url_path(url),
                    "anchor_text": clean_anchor_text(anchor.get_text(" ")),
                }
            )

    result = pd.DataFrame(
        rows,
        columns=["company_id", "internal_url", "url_path", "anchor_text"],
    )
    write_csv_atomic(result, output_path)
    return result
