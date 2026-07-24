from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from country_values_distance.config import (
    MAX_CONCURRENT_REQUESTS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)
from country_values_distance.io import write_csv_atomic
from country_values_distance.web import clean_internal_url


async def fetch_company_homepage(
    company: pd.Series,
    client: httpx.AsyncClient,
    request_semaphore: asyncio.Semaphore,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    final_url = str(company["final_url"])
    try:
        async with request_semaphore:
            response = await client.get(final_url, timeout=REQUEST_TIMEOUT_SECONDS)
        status = response.status_code
        content_type = response.headers.get("Content-Type", "").lower()
        if status >= 400:
            error = f"homepage_http_error_{status}"
        elif "text/html" not in content_type:
            error = f"homepage_not_html_{content_type}"
        else:
            error = ""

        artifact_path = ""
        if not error and cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            artifact = cache_dir / f"{company['company_id']}.html"
            artifact.write_text(response.text, encoding="utf-8")
            artifact_path = str(artifact)
        return {
            **company.to_dict(),
            "homepage_status_code": status,
            "homepage_content_type": content_type,
            "homepage_fetch_url": clean_internal_url(str(response.url)),
            "homepage_fetch_success": not error,
            "homepage_error": error,
            "homepage_html_path": artifact_path,
        }
    except httpx.HTTPError as error:
        return {
            **company.to_dict(),
            "homepage_status_code": None,
            "homepage_content_type": "",
            "homepage_fetch_url": None,
            "homepage_fetch_success": False,
            "homepage_error": f"homepage_fetch_error_{type(error).__name__}",
            "homepage_html_path": "",
        }


async def run_homepage_fetch(
    dataframe: pd.DataFrame,
    cache_dir: Path | None = None,
    client: httpx.AsyncClient | None = None,
) -> pd.DataFrame:
    required = {"company_id", "final_url"}
    missing = required - set(dataframe.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    owns_client = client is None
    client = client or httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True
    )
    try:
        results = await asyncio.gather(
            *(
                fetch_company_homepage(row, client, semaphore, cache_dir)
                for _, row in dataframe.iterrows()
            )
        )
    finally:
        if owns_client:
            await client.aclose()
    columns = [
        *dataframe.columns,
        "homepage_status_code",
        "homepage_content_type",
        "homepage_fetch_url",
        "homepage_fetch_success",
        "homepage_error",
        "homepage_html_path",
    ]
    return pd.DataFrame(results).reindex(columns=dict.fromkeys(columns))


def fetch_homepages(
    dataframe: pd.DataFrame,
    output_path: Path,
    cache_dir: Path,
    html_body: str | None = None,
) -> pd.DataFrame:
    """Fetch homepages and cache valid HTML; ``html_body`` is a test fixture."""
    required = {"company_id", "final_url"}
    missing = required - set(dataframe.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    if html_body is None:
        output = asyncio.run(run_homepage_fetch(dataframe, cache_dir=cache_dir))
    else:
        output = dataframe.copy().reset_index(drop=True)
        output["homepage_fetch_url"] = output["final_url"].map(clean_internal_url)
        output["homepage_status_code"] = 200
        output["homepage_content_type"] = "text/html"
        output["homepage_fetch_success"] = True
        output["homepage_error"] = ""
        paths = []
        cache_dir.mkdir(parents=True, exist_ok=True)
        for row in output.itertuples(index=False):
            path = cache_dir / f"{row.company_id}.html"
            path.write_text(html_body, encoding="utf-8")
            paths.append(str(path))
        output["homepage_html_path"] = paths

    write_csv_atomic(output, output_path)
    return output
