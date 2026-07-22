"""Command-line entrypoint for the country values migration package."""

from __future__ import annotations

import argparse
from pathlib import Path

from country_values_distance.cleaning import prepare_companies
from country_values_distance.config import (
    OUTPUT_AVAILABILITY_CHECK,
    OUTPUT_HOMEPAGE_FETCH_PATH,
    OUTPUT_INTERNAL_LINKS_PATH,
    OUTPUT_ROBOTS_VALIDATED_PATH,
    OUTPUT_SEED_SAMPLE_PATH,
    RAW_COMPANY_PATH,
)
from country_values_distance.pipeline import (
    check_availability,
    check_robots_stage,
    extract_links_stage,
    fetch_homepages_stage,
    qualify_and_sample_companies,
    run_all,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="country-values-distance",
        description="Company values scraping and analysis pipeline.",
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to the raw input CSV. Used by prepare-companies and run-all.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory used for intermediate and final stage outputs.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional configuration file path for the active run.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume completed work from the checkpoint directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force the selected stage to rebuild its outputs.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Concurrency cap used by the bounded availability stage.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic seed used by sampling and downstream selection stages.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "prepare-companies",
        help="Clean and normalize the raw company dataset into the staged output.",
    )
    subparsers.add_parser(
        "qualify-domains",
        help="Qualify domains and build the initial candidate sample.",
    )
    subparsers.add_parser(
        "check-availability",
        help="Check reachable websites and persist availability outcomes.",
    )
    subparsers.add_parser(
        "check-robots",
        help="Validate robots.txt permissions for scrape-ready companies.",
    )
    subparsers.add_parser(
        "fetch-homepages",
        help="Fetch cached homepage HTML and persist metadata for parsing stages.",
    )
    subparsers.add_parser(
        "extract-links",
        help="Extract canonical internal links from cached homepage HTML.",
    )
    subparsers.add_parser(
        "run-all",
        help="Run the full pipeline in dependency order.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "prepare-companies":
        prepare_companies(input_path=args.input or RAW_COMPANY_PATH)
        return

    if args.command == "qualify-domains":
        qualify_and_sample_companies()
        return

    if args.command == "check-availability":
        check_availability(
            input_path=args.input or OUTPUT_SEED_SAMPLE_PATH,
            output_path=(
                args.output_dir / "company_availability_check.csv"
                if args.output_dir is not None
                else OUTPUT_AVAILABILITY_CHECK
            ),
            workers=args.workers,
        )
        return

    if args.command == "check-robots":
        check_robots_stage(
            input_path=args.input or OUTPUT_AVAILABILITY_CHECK,
            output_path=(
                args.output_dir / "company_robots_validated.csv"
                if args.output_dir is not None
                else OUTPUT_ROBOTS_VALIDATED_PATH
            ),
        )
        return

    if args.command == "fetch-homepages":
        fetch_homepages_stage(
            input_path=args.input or OUTPUT_ROBOTS_VALIDATED_PATH,
            output_path=(
                args.output_dir / "company_homepage_fetch.csv"
                if args.output_dir is not None
                else OUTPUT_HOMEPAGE_FETCH_PATH
            ),
            cache_dir=(
                args.output_dir / "homepage_html"
                if args.output_dir is not None
                else None
            ),
        )
        return

    if args.command == "extract-links":
        extract_links_stage(
            input_path=args.input or OUTPUT_HOMEPAGE_FETCH_PATH,
            output_path=(
                args.output_dir / OUTPUT_INTERNAL_LINKS_PATH.name
                if args.output_dir is not None
                else OUTPUT_INTERNAL_LINKS_PATH
            ),
        )
        return

    if args.command == "run-all":
        run_all(
            input_path=args.input or None,
            output_dir=args.output_dir or None,
            config_path=args.config or None,
            resume=args.resume,
            force=args.force,
            workers=args.workers,
            seed=args.seed,
        )
        return

    parser.error(f"unknown command: {args.command}")