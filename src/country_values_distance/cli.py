"""Command-line entrypoint for the country values migration package."""

from __future__ import annotations

import argparse

from country_values_distance.cleaning import prepare_companies
from country_values_distance.pipeline import qualify_and_sample_companies, run_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="country-values-distance",
        description="Company values scraping and analysis pipeline.",
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
        prepare_companies()
        return

    if args.command == "qualify-domains":
        qualify_and_sample_companies()
        return

    if args.command == "run-all":
        run_all()
        return

    parser.error(f"unknown command: {args.command}")