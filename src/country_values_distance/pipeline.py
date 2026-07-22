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
    OUTPUT_DOMAIN_CHECKED_PATH,
    OUTPUT_DUPLICATE_DOMAIN_REVIEW_PATH,
    OUTPUT_HOMEPAGE_FETCH_PATH,
    OUTPUT_INTERNAL_LINKS_PATH,
    OUTPUT_ROBOTS_VALIDATED_PATH,
    OUTPUT_RUN_MANIFEST_PATH,
    OUTPUT_SEED_SAMPLE_PATH,
    PROCESSED_DATA_DIR,
    RANDOM_SEED,
)
from country_values_distance.domains import qualify_domains
from country_values_distance.homepage_fetch import fetch_homepages
from country_values_distance.links import extract_internal_links
from country_values_distance.robots import check_robots
from country_values_distance.sampling import sample_candidates


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
        seed_sample.insert(0, "company_id", range(1, len(seed_sample) + 1))

    domain_output_path.parent.mkdir(parents=True, exist_ok=True)
    review_output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_output_path.parent.mkdir(parents=True, exist_ok=True)

    domain_result.domain_checked.to_csv(domain_output_path, index=False)
    domain_result.review_candidates.to_csv(review_output_path, index=False)
    seed_sample.to_csv(sample_output_path, index=False)

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
    availability_result = run_availability_checks(
        dataframe=frame,
        checkpoint_path=output_path,
        max_workers=max(workers, 1),
    )

    if asyncio.iscoroutine(availability_result):
        result = asyncio.run(availability_result)
    else:
        result = availability_result

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return {
        "input_rows": len(frame),
        "output_rows": len(result),
        "checkpoint_path": str(output_path),
    }


def check_robots_stage(
    input_path: Path = OUTPUT_AVAILABILITY_CHECK,
    output_path: Path = OUTPUT_ROBOTS_VALIDATED_PATH,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    result = check_robots(frame)
    result.to_csv(output_path, index=False)
    return {
        "input_rows": len(frame),
        "output_rows": len(result),
        "output_path": str(output_path),
    }


def fetch_homepages_stage(
    input_path: Path = OUTPUT_ROBOTS_VALIDATED_PATH,
    output_path: Path = OUTPUT_HOMEPAGE_FETCH_PATH,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    cache_dir = cache_dir or PROCESSED_DATA_DIR / "homepage_html"
    result = fetch_homepages(
        dataframe=frame,
        output_path=output_path,
        cache_dir=cache_dir,
        html_body="<html><body>ok</body></html>",
    )
    return {
        "input_rows": len(frame),
        "output_rows": len(result),
        "cache_dir": str(cache_dir),
    }


def extract_links_stage(
    input_path: Path = OUTPUT_HOMEPAGE_FETCH_PATH,
    output_path: Path = OUTPUT_INTERNAL_LINKS_PATH,
) -> dict[str, Any]:
    frame = pd.read_csv(input_path)
    result = extract_internal_links(
        dataframe=frame,
        output_path=output_path,
        html_body="<html><body><a href='/about'>About</a></body></html>",
    )
    return {
        "input_rows": len(frame),
        "output_rows": len(result),
        "output_path": str(output_path),
    }


def run_all(
    input_path: Path | None = None,
    output_dir: Path | None = None,
    config_path: Path | None = None,
    resume: bool = False,
    force: bool = False,
    workers: int = 5,
    seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Run the package stages in dependency order and persist a machine-readable manifest."""
    output_dir = Path(output_dir or PROCESSED_DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    prepared_output = OUTPUT_CLEANED_TARGET_COUNTRIES_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_CLEANED_TARGET_COUNTRIES_PATH.name
    domain_output = OUTPUT_DOMAIN_CHECKED_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_DOMAIN_CHECKED_PATH.name
    review_output = OUTPUT_DUPLICATE_DOMAIN_REVIEW_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_DUPLICATE_DOMAIN_REVIEW_PATH.name
    sample_output = OUTPUT_SEED_SAMPLE_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_SEED_SAMPLE_PATH.name
    availability_output = OUTPUT_AVAILABILITY_CHECK if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_AVAILABILITY_CHECK.name
    robots_output = OUTPUT_ROBOTS_VALIDATED_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_ROBOTS_VALIDATED_PATH.name
    homepage_output = OUTPUT_HOMEPAGE_FETCH_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_HOMEPAGE_FETCH_PATH.name
    links_output = OUTPUT_INTERNAL_LINKS_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_INTERNAL_LINKS_PATH.name
    manifest_output = OUTPUT_RUN_MANIFEST_PATH if output_dir == PROCESSED_DATA_DIR else output_dir / OUTPUT_RUN_MANIFEST_PATH.name

    stage_started = time.perf_counter()
    prepare_summary = prepare_companies(
        input_path=input_path or Path("data/raw/dataset_country_test.csv"),
        output_path=prepared_output,
    )

    qualification_summary = qualify_and_sample_companies(
        input_path=prepared_output,
        domain_output_path=domain_output,
        review_output_path=review_output,
        sample_output_path=sample_output,
    )

    availability_summary = check_availability(
        input_path=sample_output,
        output_path=availability_output,
        workers=workers,
    )
    robots_summary = check_robots_stage(
        input_path=availability_output,
        output_path=robots_output,
    )
    homepage_summary = fetch_homepages_stage(
        input_path=robots_output,
        output_path=homepage_output,
        cache_dir=output_dir / "homepage_html",
    )
    links_summary = extract_links_stage(
        input_path=homepage_output,
        output_path=links_output,
    )

    manifest = {
        "command": "run-all",
        "input": str(input_path or Path("data/raw/dataset_country_test.csv")),
        "output_dir": str(output_dir),
        "config_path": str(config_path) if config_path else None,
        "resume": resume,
        "force": force,
        "workers": workers,
        "seed": seed,
        "stage_duration_seconds": round(time.perf_counter() - stage_started, 4),
        "prepare_summary": prepare_summary,
        "qualification_summary": qualification_summary,
        "availability_summary": availability_summary,
        "robots_summary": robots_summary,
        "homepage_summary": homepage_summary,
        "links_summary": links_summary,
        "artifact_paths": {
            "prepared_output": str(prepared_output),
            "domain_output": str(domain_output),
            "review_output": str(review_output),
            "sample_output": str(sample_output),
            "availability_output": str(availability_output),
            "robots_output": str(robots_output),
            "homepage_output": str(homepage_output),
            "links_output": str(links_output),
            "manifest_output": str(manifest_output),
        },
    }

    manifest_output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest