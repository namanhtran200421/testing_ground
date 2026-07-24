# Country Values Distance

This repository contains the package-based migration of the company-values
notebooks. The source pipeline now includes notebook 02's multilingual,
relevance-guided crawler and translation workflow.

## Installation

```bash
python3.11 -m pip install -e '.[dev]'
```

The first semantic crawl downloads
`paraphrase-multilingual-MiniLM-L12-v2` through Sentence Transformers.
Translation is optional and expects a local Ollama server with
`translategemma:4b`.

## Full pipeline

Run collection, crawling, semantic section extraction, and final selection:

```bash
python3.11 -m country_values_distance run-all
```

Include translation:

```bash
python3.11 -m country_values_distance --translate run-all
```

Use `--resume` to retain completed company crawl results and process only
missing companies. Use `--force` to rebuild crawl or translation outputs.

## Individual stages

```bash
python3.11 -m country_values_distance prepare-companies
python3.11 -m country_values_distance qualify-domains
python3.11 -m country_values_distance check-availability
python3.11 -m country_values_distance build-scrape-ready
python3.11 -m country_values_distance check-robots
python3.11 -m country_values_distance fetch-homepages
python3.11 -m country_values_distance extract-links
python3.11 -m country_values_distance crawl-websites
python3.11 -m country_values_distance select-values
python3.11 -m country_values_distance translate-values
```

Important notebook 02 artifacts are:

- `data/processed/crawled_pages.csv`: page-level crawl and scoring audit.
- `data/processed/production_final.csv`: one accepted values section per company.
- `data/processed/translation_cache.csv`: reusable language/translation results.
- `data/processed/production_500_sample.csv`: cleaned translation export.

The crawler checks every path against `robots.txt`, stays on the company
domain, removes tracking queries and fragments, filters excluded paths and
file types, and enforces depth, page, branch, and request-concurrency limits.
