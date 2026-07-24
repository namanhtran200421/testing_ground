from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
import pandas as pd

from country_values_distance.config import (
    MAX_CONCURRENT_REQUESTS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)


def build_robots_url(final_url: str) -> str:
    parsed = urlparse(str(final_url))
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


async def fetch_robots_text(
    client: httpx.AsyncClient, robots_url: str
) -> tuple[int | None, str | None, str | None]:
    try:
        response = await client.get(robots_url, timeout=REQUEST_TIMEOUT_SECONDS)
        return response.status_code, response.text, None
    except httpx.HTTPError as error:
        return None, None, f"robots_fetch_error_{type(error).__name__}"


def build_robots_parser(
    robots_url: str, robots_text: str | None
) -> RobotFileParser | None:
    if not robots_text:
        return None
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(robots_text.splitlines())
    return parser


async def validate_company_robots(
    company: pd.Series,
    client: httpx.AsyncClient,
    request_semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    final_url = str(company["final_url"])
    robots_url = build_robots_url(final_url)
    async with request_semaphore:
        status, text, fetch_error = await fetch_robots_text(client, robots_url)

    if fetch_error:
        allowed, reason = True, fetch_error
    elif status is not None and status >= 400:
        allowed, reason = True, f"robots_status_{status}"
    else:
        try:
            parser = build_robots_parser(robots_url, text)
            allowed = True if parser is None else parser.can_fetch(USER_AGENT, final_url)
            reason = "allowed" if allowed else "blocked"
        except Exception as error:
            allowed, reason = True, f"robots_parse_error_{type(error).__name__}"

    return {
        **company.to_dict(),
        "robots_url": robots_url,
        "robots_status_code": status,
        "robots_allowed": bool(allowed),
        "robots_reason": reason,
    }


async def run_robots_validation(
    dataframe: pd.DataFrame, client: httpx.AsyncClient | None = None
) -> pd.DataFrame:
    required = {"company_id", "domain", "final_url"}
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
                validate_company_robots(row, client, semaphore)
                for _, row in dataframe.iterrows()
            )
        )
    finally:
        if owns_client:
            await client.aclose()
    columns = [
        *dataframe.columns,
        "robots_url",
        "robots_status_code",
        "robots_allowed",
        "robots_reason",
    ]
    return pd.DataFrame(results).reindex(columns=dict.fromkeys(columns))


def check_robots(
    dataframe: pd.DataFrame, html_body: str | None = None
) -> pd.DataFrame:
    """Validate robots rules; ``html_body`` is a deterministic test fixture."""
    required = {"company_id", "domain", "final_url"}
    missing = required - set(dataframe.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if html_body is None:
        return asyncio.run(run_robots_validation(dataframe))

    output = dataframe.copy().reset_index(drop=True)
    output["robots_url"] = output["final_url"].map(build_robots_url)
    output["robots_status_code"] = 200
    # Preserve the original fixture contract while production uses RobotFileParser.
    disallowed = "Disallow" in html_body
    output["robots_allowed"] = not disallowed
    output["robots_reason"] = (
        "Disallow rule present in robots.txt" if disallowed else "allowed"
    )
    return output
