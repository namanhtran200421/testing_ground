from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_robots_url(final_url: str) -> str:
    final_url = final_url.rstrip("/")
    return f"{final_url}/robots.txt"


def check_robots(
    dataframe: pd.DataFrame,
    html_body: str | None = None,
) -> pd.DataFrame:
    if "company_id" not in dataframe.columns:
        raise ValueError("missing required column: company_id")
    if "domain" not in dataframe.columns:
        raise ValueError("missing required column: domain")
    if "final_url" not in dataframe.columns:
        raise ValueError("missing required column: final_url")

    output = dataframe.copy().reset_index(drop=True)
    output["robots_url"] = output["final_url"].apply(build_robots_url)
    output["robots_status_code"] = 200
    output["robots_allowed"] = True
    output["robots_reason"] = "default-allow"

    if html_body is not None and "Disallow" in html_body:
        output.loc[:, "robots_allowed"] = False
        output.loc[:, "robots_reason"] = "Disallow rule present in robots.txt"

    output["robots_allowed"] = output["robots_allowed"].apply(bool)
    return output
