import asyncio
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx
import pandas as pd

from country_values_distance.cleaning import normalise_website_url
from country_values_distance.config import (
    HTTP_MAX_RETRIES,
    HTTP_RETRY_BACKOFF_SECONDS,
    RETRYABLE_FAILURE_REASONS,
    TRANSIENT_HTTP_STATUS_CODES,
)
from country_values_distance.io import write_csv_atomic


def build_url_variants(value: object) -> list[str]:
    """Build a deterministic list of website variants for availability probing."""
    norm_url = normalise_website_url(value)

    if norm_url is None:
        return []

    parsed = urlparse(norm_url)
    domain = parsed.netloc.lower().strip()

    if not domain:
        return []

    base_domain = domain[4:] if domain.startswith("www.") else domain
    domains = [base_domain, f"www.{base_domain}"]
    schemes = list(dict.fromkeys([parsed.scheme or "https", "https"]))

    variants: list[str] = []

    for scheme in schemes:
        for candidate_domain in domains:
            candidate = urlunparse(
                (
                    scheme,
                    candidate_domain,
                    parsed.path or "/",
                    "",
                    parsed.query,
                    "",
                )
            )
            if candidate not in variants:
                variants.append(candidate)

    return variants


def unavailable_result(
    variants: list[str],
    failure_reason: str,
    attempts: int,
    status_code: Optional[int] = None,
    content_type: Optional[str] = None,
) -> dict[str, object]:
    return {
        "is_website_reachable": False,
        "final_url": None,
        "status_code": status_code,
        "content_type": content_type,
        "failure_reason": failure_reason,
        "checked_url_variants": json.dumps(variants),
        "http_attempts": attempts,
    }


async def check_website(
    client: httpx.AsyncClient,
    website_url: object,
) -> dict[str, object]:
    """Probe a website using a bounded set of URL variants."""
    variants = build_url_variants(website_url)

    if not variants:
        return unavailable_result(
            variants=[],
            failure_reason="invalid",
            attempts=0,
        )

    attempts = 0
    last_status: Optional[int] = None
    last_content_type: Optional[str] = None
    last_failure_reason = "no_successful_variant"

    for candidate_url in variants:
        for retry_number in range(HTTP_MAX_RETRIES + 1):
            attempts += 1
            try:
                response = await client.get(candidate_url, timeout=10.0)
            except httpx.TimeoutException:
                last_failure_reason = "timeout"
                if retry_number < HTTP_MAX_RETRIES:
                    await asyncio.sleep(HTTP_RETRY_BACKOFF_SECONDS * (2**retry_number))
                    continue
                break
            except httpx.ConnectError:
                last_failure_reason = "connection_error"
                if retry_number < HTTP_MAX_RETRIES:
                    await asyncio.sleep(HTTP_RETRY_BACKOFF_SECONDS * (2**retry_number))
                    continue
                break
            except httpx.TooManyRedirects:
                last_failure_reason = "too_many_redirects"
                break
            except httpx.HTTPError:
                last_failure_reason = "http_error"
                break

            last_status = response.status_code
            last_content_type = response.headers.get("content-type", "").lower()

            if response.status_code in TRANSIENT_HTTP_STATUS_CODES:
                last_failure_reason = f"http_error:{response.status_code}"
                if retry_number < HTTP_MAX_RETRIES:
                    await asyncio.sleep(HTTP_RETRY_BACKOFF_SECONDS * (2**retry_number))
                    continue
                break

            if 300 <= response.status_code < 400:
                last_failure_reason = f"redirect:{response.status_code}"
                break

            if response.status_code >= 400:
                last_failure_reason = f"http_error:{response.status_code}"
                break

            is_html = (
                "text/html" in last_content_type
                or "application/xhtml+xml" in last_content_type
            )

            if not is_html:
                last_failure_reason = f"non_html:{last_content_type or 'missing'}"
                break

            return {
                "is_website_reachable": True,
                "final_url": str(response.url),
                "status_code": response.status_code,
                "content_type": last_content_type,
                "failure_reason": None,
                "checked_url_variants": json.dumps(variants),
                "http_attempts": attempts,
            }

    return unavailable_result(
        variants=variants,
        failure_reason=last_failure_reason,
        attempts=attempts,
        status_code=last_status,
        content_type=last_content_type,
    )


def load_checkpoint(checkpoint_path: Path) -> dict[str, dict[str, object]]:
    if not checkpoint_path.exists():
        return {}

    try:
        checkpoint = pd.read_csv(checkpoint_path)
    except pd.errors.EmptyDataError:
        return {}

    if "availability_key" not in checkpoint.columns:
        return {}

    completed: dict[str, dict[str, object]] = {}
    for row in checkpoint.itertuples(index=False):
        completed[str(getattr(row, "availability_key"))] = row._asdict()

    return completed


def save_checkpoint(checkpoint_path: Path, dataframe: pd.DataFrame) -> None:
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv_atomic(dataframe, checkpoint_path)


async def run_availability_checks(
    dataframe: pd.DataFrame,
    checkpoint_path: Path,
    max_workers: int = 5,
    client: Optional[httpx.AsyncClient] = None,
) -> pd.DataFrame:
    """Run a bounded availability probe over a dataframe and persist a checkpoint."""
    if "website_url" not in dataframe.columns:
        raise ValueError("missing required column: website_url")

    source = dataframe.copy().reset_index(drop=True)
    source["availability_key"] = source["website_url"].apply(build_url_variants)

    completed = load_checkpoint(checkpoint_path)
    pending = source.loc[
        ~source["availability_key"].apply(lambda key: str(key) in completed)
    ].copy()

    semaphore = asyncio.Semaphore(max_workers)

    async def bounded_probe(row: pd.Series) -> pd.Series:
        async with semaphore:
            result = await check_website(
                client=client or httpx.AsyncClient(),
                website_url=row["website_url"],
            )

        result_row = row.copy()
        result_row.update(result)
        return result_row

    checkpoint_records: list[pd.Series] = []
    tasks = [bounded_probe(row) for _, row in pending.iterrows()]

    for task in asyncio.as_completed(tasks):
        checkpoint_records.append(await task)

    if checkpoint_records:
        result_frame = pd.DataFrame(checkpoint_records)
        save_checkpoint(checkpoint_path, result_frame)

    return pd.DataFrame(checkpoint_records)
