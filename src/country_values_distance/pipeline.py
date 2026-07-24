from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from country_values_distance.avail_check import run_availability_checks
from country_values_distance.cleaning import prepare_companies
from country_values_distance.config import (
    OUTPUT_AVAILABILITY_CHECK,
    OUTPUT_CLEANED_TARGET_COUNTRIES_PATH,
    OUTPUT_CRAWL_AUDIT_PATH,
    OUTPUT_DOMAIN_CHECKED_PATH,
    OUTPUT_DUPLICATE_DOMAIN_REVIEW_PATH,
    OUTPUT_HOMEPAGE_FETCH_PATH,
    OUTPUT_INTERNAL_LINKS_PATH,
    OUTPUT_PRODUCTION_FINAL_PATH,
    OUTPUT_ROBOTS_VALIDATED_PATH,
    OUTPUT_RUN_MANIFEST_PATH,
    OUTPUT_SCRAPE_READY_PATH,
    OUTPUT_SEED_SAMPLE_PATH,
    OUTPUT_TRANSLATION_CACHE_PATH,
    OUTPUT_TRANSLATION_PATH,
    PROCESSED_DATA_DIR,
    RANDOM_SEED,
    RAW_COMPANY_PATH,
)
from country_values_distance.crawler import CRAWL_COLUMNS, run_company_crawls
from country_values_distance.domains import qualify_domains
from country_values_distance.homepage_fetch import fetch_homepages
from country_values_distance.io import write_csv_atomic
from country_values_distance.links import extract_internal_links
from country_values_distance.robots import check_robots
from country_values_distance.sampling import sample_candidates
from country_values_distance.selection import select_final_candidates
from country_values_distance.translation import translate_candidates


def _path(output_dir: Path, default: Path) -> Path:
    return default if output_dir == PROCESSED_DATA_DIR else output_dir / default.name


def qualify_and_sample_companies(
    input_path: Path = OUTPUT_CLEANED_TARGET_COUNTRIES_PATH,
    domain_output_path: Path = OUTPUT_DOMAIN_CHECKED_PATH,
    review_output_path: Path = OUTPUT_DUPLICATE_DOMAIN_REVIEW_PATH,
    sample_output_path: Path = OUTPUT_SEED_SAMPLE_PATH,
) -> dict[str, int]:
    cleaned_companies = pd.read_csv(input_path)
    domain_result = qualify_domains(cleaned_companies)
    seed_sample = sample_candidates(domain_result.automatic_candidates).copy()
    if not seed_sample.empty:
        seed_sample.insert(
            0, "company_id", [f"C{number:04d}" for number in range(1, len(seed_sample) + 1)]
        )

    write_csv_atomic(domain_result.domain_checked, domain_output_path)
    write_csv_atomic(domain_result.review_candidates, review_output_path)
    write_csv_atomic(seed_sample, sample_output_path)
    return {
        "domain_checked_rows": len(domain_result.domain_checked),
        "domain_keep_rows": int(
            domain_result.domain_checked["qualification_status"].eq("keep").sum()
        ),
        "domain_review_rows": int(
            domain_result.domain_checked["qualification_status"].eq("review").sum()
        ),
        "domain_remove_rows": int(
            domain_result.domain_checked["qualification_status"].eq("remove").sum()
        ),
        "duplicate_domain_review_rows": len(domain_result.review_candidates),
        "automatic_candidate_rows": len(domain_result.automatic_candidates),
        "seed_sample_rows": len(seed_sample),
    }


def check_availability(
    input_path: Path = OUTPUT_SEED_SAMPLE_PATH,
    output_path: Path = OUTPUT_AVAILABILITY_CHECK,
    workers: int = 5,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    availability = run_availability_checks(
        dataframe=frame,
        checkpoint_path=output_path,
        max_workers=max(workers, 1),
    )
    result = asyncio.run(availability) if asyncio.iscoroutine(availability) else availability
    write_csv_atomic(result, output_path)
    return {
        "input_rows": len(frame),
        "output_rows": len(result),
        "checkpoint_path": str(output_path),
    }


def check_robots_stage(
    input_path: Path = OUTPUT_SCRAPE_READY_PATH,
    output_path: Path = OUTPUT_ROBOTS_VALIDATED_PATH,
    *,
    resume: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    cached = pd.DataFrame()
    pending = frame
    if resume and not force and output_path.exists():
        cached = pd.read_csv(output_path)
        requested = set(frame["company_id"])
        cached = cached.loc[cached["company_id"].isin(requested)].copy()
        pending = frame.loc[~frame["company_id"].isin(cached["company_id"])].copy()
    new = check_robots(pending)
    result = (
        pd.concat([cached, new], ignore_index=True)
        .drop_duplicates("company_id", keep="last")
        .reset_index(drop=True)
    )
    write_csv_atomic(result, output_path)
    return {
        "input_rows": len(frame),
        "new_rows": len(pending),
        "output_rows": len(result),
        "allowed_rows": int(result.get("robots_allowed", pd.Series(dtype=bool)).sum()),
        "output_path": str(output_path),
    }


def build_scrape_ready_stage(
    input_path: Path = OUTPUT_AVAILABILITY_CHECK,
    output_path: Path = OUTPUT_SCRAPE_READY_PATH,
) -> dict[str, Any]:
    """Filter availability results into notebook 02's documented input contract."""
    frame = pd.read_csv(input_path)
    mask = frame["final_url"].notna()
    if "is_website_reachable" in frame:
        mask &= frame["is_website_reachable"].fillna(False)
    if "content_type" in frame:
        mask &= frame["content_type"].fillna("").str.contains(
            "text/html|application/xhtml\\+xml", case=False, regex=True
        )
    if "qualification_status" in frame:
        mask &= frame["qualification_status"].eq("keep")
    elif "domain_match_status" in frame:
        mask &= frame["domain_match_status"].eq("keep")
    result = frame.loc[mask].copy().reset_index(drop=True)
    if "company_id" not in result.columns:
        result.insert(
            0,
            "company_id",
            [f"C{number:04d}" for number in range(1, len(result) + 1)],
        )
    result["scraping_ready"] = True
    write_csv_atomic(result, output_path)
    return {
        "input_rows": len(frame),
        "output_rows": len(result),
        "output_path": str(output_path),
    }


def fetch_homepages_stage(
    input_path: Path = OUTPUT_ROBOTS_VALIDATED_PATH,
    output_path: Path = OUTPUT_HOMEPAGE_FETCH_PATH,
    cache_dir: Path | None = None,
    *,
    resume: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    if "robots_allowed" in frame:
        frame = frame.loc[frame["robots_allowed"].fillna(False)].copy()
    cache_dir = cache_dir or PROCESSED_DATA_DIR / "homepage_html"
    cached = pd.DataFrame()
    pending = frame
    if resume and not force and output_path.exists():
        cached = pd.read_csv(output_path)
        requested = set(frame["company_id"])
        cached = cached.loc[cached["company_id"].isin(requested)].copy()
        pending = frame.loc[~frame["company_id"].isin(cached["company_id"])].copy()
    temporary_output = output_path.with_name(f".{output_path.name}.new")
    new = fetch_homepages(
        pending, output_path=temporary_output, cache_dir=cache_dir
    )
    temporary_output.unlink(missing_ok=True)
    result = (
        pd.concat([cached, new], ignore_index=True)
        .drop_duplicates("company_id", keep="last")
        .reset_index(drop=True)
    )
    write_csv_atomic(result, output_path)
    return {
        "input_rows": len(frame),
        "new_rows": len(pending),
        "output_rows": len(result),
        "successful_rows": int(
            result.get("homepage_fetch_success", pd.Series(dtype=bool)).sum()
        ),
        "cache_dir": str(cache_dir),
    }


def extract_links_stage(
    input_path: Path = OUTPUT_HOMEPAGE_FETCH_PATH,
    output_path: Path = OUTPUT_INTERNAL_LINKS_PATH,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    if "homepage_fetch_success" in frame:
        frame = frame.loc[frame["homepage_fetch_success"].fillna(False)].copy()
    result = extract_internal_links(dataframe=frame, output_path=output_path)
    return {
        "input_rows": len(frame),
        "output_rows": len(result),
        "output_path": str(output_path),
    }


def crawl_websites_stage(
    input_path: Path = OUTPUT_HOMEPAGE_FETCH_PATH,
    output_path: Path = OUTPUT_CRAWL_AUDIT_PATH,
    *,
    resume: bool = False,
    force: bool = False,
    scorer: Any | None = None,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    mask = frame["homepage_fetch_url"].notna()
    if "robots_allowed" in frame:
        mask &= frame["robots_allowed"].fillna(False)
    if "homepage_error" in frame:
        mask &= frame["homepage_error"].fillna("").eq("")
    crawl_input = frame.loc[mask].copy()

    cached = pd.DataFrame(columns=CRAWL_COLUMNS)
    pending = crawl_input
    if resume and not force and output_path.exists():
        cached = pd.read_csv(output_path)
        completed = set(cached.get("company_id", pd.Series(dtype=object)))
        pending = crawl_input.loc[~crawl_input["company_id"].isin(completed)].copy()
    if pending.empty:
        new_pages = pd.DataFrame(columns=CRAWL_COLUMNS)
    else:
        new_pages = asyncio.run(run_company_crawls(pending, scorer=scorer))
    result = (
        pd.concat([cached, new_pages], ignore_index=True)
        .drop_duplicates(["company_id", "url"], keep="last")
        .reset_index(drop=True)
    )
    write_csv_atomic(result, output_path)
    return {
        "input_rows": len(crawl_input),
        "new_company_rows": len(pending),
        "output_rows": len(result),
        "companies_crawled": result.get(
            "company_id", pd.Series(dtype=object)
        ).nunique(),
        "output_path": str(output_path),
    }


def select_values_stage(
    input_path: Path = OUTPUT_CRAWL_AUDIT_PATH,
    output_path: Path = OUTPUT_PRODUCTION_FINAL_PATH,
) -> dict[str, Any]:
    crawled = pd.read_csv(input_path)
    result = select_final_candidates(crawled)
    write_csv_atomic(result, output_path)
    return {
        "input_rows": len(crawled),
        "output_rows": len(result),
        "output_path": str(output_path),
    }


def translate_values_stage(
    input_path: Path = OUTPUT_PRODUCTION_FINAL_PATH,
    output_path: Path = OUTPUT_TRANSLATION_PATH,
    cache_path: Path = OUTPUT_TRANSLATION_CACHE_PATH,
    *,
    force: bool = False,
) -> dict[str, Any]:
    candidates = pd.read_csv(input_path)
    result = translate_candidates(
        candidates, cache_path=cache_path, output_path=output_path, rerun=force
    )
    return {
        "input_rows": len(candidates),
        "output_rows": len(result),
        "translated_rows": int(
            result.get("translation_status", pd.Series(dtype=str))
            .eq("translated")
            .sum()
        ),
        "output_path": str(output_path),
        "cache_path": str(cache_path),
    }


def run_all(
    input_path: Path | None = None,
    output_dir: Path | None = None,
    config_path: Path | None = None,
    resume: bool = False,
    force: bool = False,
    workers: int = 5,
    seed: int = RANDOM_SEED,
    translate: bool = False,
) -> dict[str, Any]:
    """Run all collection and selection stages; optionally translate with Ollama."""
    output_dir = Path(output_dir or PROCESSED_DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "prepared_output": _path(output_dir, OUTPUT_CLEANED_TARGET_COUNTRIES_PATH),
        "domain_output": _path(output_dir, OUTPUT_DOMAIN_CHECKED_PATH),
        "review_output": _path(output_dir, OUTPUT_DUPLICATE_DOMAIN_REVIEW_PATH),
        "sample_output": _path(output_dir, OUTPUT_SEED_SAMPLE_PATH),
        "availability_output": _path(output_dir, OUTPUT_AVAILABILITY_CHECK),
        "scrape_ready_output": _path(output_dir, OUTPUT_SCRAPE_READY_PATH),
        "robots_output": _path(output_dir, OUTPUT_ROBOTS_VALIDATED_PATH),
        "homepage_output": _path(output_dir, OUTPUT_HOMEPAGE_FETCH_PATH),
        "links_output": _path(output_dir, OUTPUT_INTERNAL_LINKS_PATH),
        "crawl_output": _path(output_dir, OUTPUT_CRAWL_AUDIT_PATH),
        "final_output": _path(output_dir, OUTPUT_PRODUCTION_FINAL_PATH),
        "translation_output": _path(output_dir, OUTPUT_TRANSLATION_PATH),
        "translation_cache": _path(output_dir, OUTPUT_TRANSLATION_CACHE_PATH),
        "manifest_output": _path(output_dir, OUTPUT_RUN_MANIFEST_PATH),
    }
    started = time.perf_counter()
    prepare_summary = prepare_companies(
        input_path=input_path or RAW_COMPANY_PATH,
        output_path=paths["prepared_output"],
    )
    qualification_summary = qualify_and_sample_companies(
        paths["prepared_output"],
        paths["domain_output"],
        paths["review_output"],
        paths["sample_output"],
    )
    availability_summary = check_availability(
        paths["sample_output"], paths["availability_output"], workers
    )
    scrape_ready_summary = build_scrape_ready_stage(
        paths["availability_output"], paths["scrape_ready_output"]
    )
    robots_summary = check_robots_stage(
        paths["scrape_ready_output"],
        paths["robots_output"],
        resume=resume,
        force=force,
    )
    homepage_summary = fetch_homepages_stage(
        paths["robots_output"],
        paths["homepage_output"],
        output_dir / "homepage_html",
        resume=resume,
        force=force,
    )
    links_summary = extract_links_stage(
        paths["homepage_output"], paths["links_output"]
    )
    crawl_summary = crawl_websites_stage(
        paths["homepage_output"],
        paths["crawl_output"],
        resume=resume,
        force=force,
    )
    selection_summary = select_values_stage(
        paths["crawl_output"], paths["final_output"]
    )
    translation_summary = (
        translate_values_stage(
            paths["final_output"],
            paths["translation_output"],
            paths["translation_cache"],
            force=force,
        )
        if translate
        else None
    )
    manifest = {
        "command": "run-all",
        "input": str(input_path or RAW_COMPANY_PATH),
        "output_dir": str(output_dir),
        "config_path": str(config_path) if config_path else None,
        "resume": resume,
        "force": force,
        "translate": translate,
        "workers": workers,
        "seed": seed,
        "stage_duration_seconds": round(time.perf_counter() - started, 4),
        "prepare_summary": prepare_summary,
        "qualification_summary": qualification_summary,
        "availability_summary": availability_summary,
        "scrape_ready_summary": scrape_ready_summary,
        "robots_summary": robots_summary,
        "homepage_summary": homepage_summary,
        "links_summary": links_summary,
        "crawl_summary": crawl_summary,
        "selection_summary": selection_summary,
        "translation_summary": translation_summary,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
    }
    paths["manifest_output"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
