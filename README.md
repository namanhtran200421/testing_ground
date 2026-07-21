# Country Values Distance

This repository contains the migration of the company values pipeline into a package-based, testable workflow.

## Installation

```bash
python3.11 -m pip install -e '.[dev]'
```

## Commands

```bash
python3.11 -m country_values_distance --help
python3.11 -m country_values_distance prepare-companies
python3.11 -m country_values_distance qualify-domains
python3.11 -m country_values_distance run-all
```

## Notes

- The package entrypoint is intentionally CLI-first and kept separate from notebook-only execution.
- Cleaning and domain qualification are deterministic for a fixed input and seed.
- The migration favors chunked processing and atomic output writes.
