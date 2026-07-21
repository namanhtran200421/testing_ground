from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import pandas as pd

from country_values_distance.config import (
    BAD_DOMAIN_PATTERNS,
    BAD_FILE_EXTENSIONS,
    DEFAULT_CHUNKSIZE,
    OUTPUT_CLEANED_TARGET_COUNTRIES_PATH,
    RAW_COMPANY_PATH,
    SIZE_CATEGORY_MAP,
    TARGET_COUNTRIES,
    map_industry_size,
)
from country_values_distance.contracts import CLEANED_COMPANY_COLUMNS


def clean_col_names(dataframe):
    """Standardise DataFrame column names."""
    dataframe.columns = (
        dataframe.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return dataframe


def clean_text_columns(dataframe, columns):
    """Trim and lowercase selected text columns if they exist."""
    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = (
                dataframe[column]
                .astype("string")
                .str.strip()
                .str.lower()
            )
    return dataframe


def normalise_website_url(website):
    """Convert a raw website value into a URL with a protocol."""
    if pd.isna(website):
        return None

    website = str(website).strip()

    if not website:
        return None

    if website.startswith("http://") or website.startswith("https://"):
        return website

    return f"https://{website}"


def extract_domain(url):
    """Extract a lowercase domain and remove the leading www prefix."""
    url = normalise_website_url(url)

    if url is None:
        return None

    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain if domain else None


def is_website_format_usable(website):
    """Return True when a website value looks like a usable company website."""
    if pd.isna(website):
        return False

    website = str(website).strip().lower()

    if not website:
        return False

    if "@" in website:
        return False

    if "." not in website:
        return False

    for extension in BAD_FILE_EXTENSIONS:
        if website.endswith(extension):
            return False

    domain = extract_domain(website)

    if domain is None:
        return False

    for pattern in BAD_DOMAIN_PATTERNS:
        if domain == pattern or domain.endswith("." + pattern):
            return False

    return True


def map_company_size(size):
    """Map a raw employee-size value into a simple size bucket."""
    size = str(size).strip().lower()
    return SIZE_CATEGORY_MAP.get(size, "too_small")

def cleaned_chunk(chunk: pd.DataFrame):
    chunk = clean_col_names(chunk)

    required_columns = {"name", "country", "industry", "size", "website"}
    missing_columns = required_columns.difference(chunk.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    chunk = chunk[
        chunk["name"].notna()
        & chunk["country"].notna()
        & chunk["size"].notna()
        & chunk["website"].notna()
        & chunk["industry"].notna()
    ].copy()

    chunk = clean_text_columns(
        chunk,
        ["name", "website", "country", "industry", "size"],
    )
    chunk = chunk[chunk["country"].isin(TARGET_COUNTRIES)].copy()
    chunk["website_format_usable"] = chunk["website"].apply(
        is_website_format_usable
    )
    chunk = chunk[chunk["website_format_usable"]].copy()

    chunk["website_url"] = chunk["website"].apply(normalise_website_url)
    chunk["domain"] = chunk["website_url"].apply(extract_domain)

    chunk = chunk[chunk["domain"].notna()].copy()

    chunk["size_bucket"] = chunk["size"].apply(map_company_size)
    chunk = chunk[chunk["size_bucket"] != "too_small"].copy()

    chunk["High_Level_Sector"] = chunk["industry"].apply(map_industry_size)

    return chunk[CLEANED_COMPANY_COLUMNS].copy()



def prepare_companies(
    input_path: Path = RAW_COMPANY_PATH,
    output_path: Path = OUTPUT_CLEANED_TARGET_COUNTRIES_PATH,
    chunksize: int = DEFAULT_CHUNKSIZE,
) -> None:
    if chunksize <= 0:
        raise ValueError("chunksize must be a positive integer")

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        dir=output_path.parent,
        delete=False,
        newline="",
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        wrote_header = False

        for chunk in pd.read_csv(input_path, chunksize=chunksize):
            cleaned_chunks = cleaned_chunk(chunk)

            if cleaned_chunks.empty:
                continue

            cleaned_chunks.to_csv(
                temporary_path,
                mode="a",
                index=False,
                header=not wrote_header,
            )
            wrote_header = True

        if not wrote_header:
            pd.DataFrame(columns=CLEANED_COMPANY_COLUMNS).to_csv(
                temporary_path,
                index=False,
            )

        temporary_path.replace(output_path)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()