from __future__ import annotations

import asyncio
import csv
import re
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from country_values_distance.config import (
    MAX_CONCURRENT_TRANSLATIONS,
    MAX_TRANSLATION_RETRIES,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TRANSLATION_TIMEOUT_SECONDS,
)
from country_values_distance.io import write_csv_atomic


TRANSLATION_COLUMNS = [
    "source_text",
    "detected_language",
    "translation_needed",
    "translated_value_text",
    "translation_method",
    "translation_status",
    "translation_error",
]


def detect_source_language(text: str) -> tuple[str, str]:
    try:
        import pycountry
        from langdetect import DetectorFactory, detect
    except ImportError as error:  # pragma: no cover - packaging failure path
        raise RuntimeError(
            "Translation requires the 'translation' project dependencies."
        ) from error

    DetectorFactory.seed = 0
    code = {"zh-cn": "zh-Hans", "zh-tw": "zh-Hant"}.get(
        detected := detect(text), detected
    )
    overrides = {
        "zh-Hans": "Chinese (Simplified)",
        "zh-Hant": "Chinese (Traditional)",
    }
    if code in overrides:
        return code, overrides[code]
    language = pycountry.languages.get(alpha_2=code.split("-")[0])
    return code, language.name if language else code


def build_translation_prompt(text: str, source_code: str, source_language: str) -> str:
    return (
        f"Translate the following company values text from "
        f"{source_language} ({source_code}) into English.\n\n"
        "Rules:\n"
        "- Translate literally and completely.\n"
        "- Do not summarise.\n"
        "- Do not reorganise the content.\n"
        "- Do not add headings unless they exist in the source.\n"
        "- Do not explain the translation.\n"
        "- Return only the translated text.\n\n"
        f"SOURCE TEXT:\n{text}"
    )


async def translate_value(
    text: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    source_text = str(text).strip()
    try:
        source_code, source_language = detect_source_language(source_text)
    except Exception as error:
        return {
            "source_text": source_text,
            "detected_language": "unknown",
            "translation_needed": None,
            "translated_value_text": None,
            "translation_method": "not_started",
            "translation_status": "language_detection_failed",
            "translation_error": type(error).__name__,
        }
    if source_code == "en":
        return {
            "source_text": source_text,
            "detected_language": "en",
            "translation_needed": False,
            "translated_value_text": source_text,
            "translation_method": "not_required",
            "translation_status": "already_english",
            "translation_error": "",
        }

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": build_translation_prompt(
                    source_text, source_code, source_language
                ),
            }
        ],
        "stream": False,
        "options": {"temperature": 0},
    }
    async with semaphore:
        for attempt in range(MAX_TRANSLATION_RETRIES):
            try:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat", json=payload
                )
                response.raise_for_status()
                translated = response.json()["message"]["content"].strip()
                if not translated:
                    raise ValueError("Empty translation returned")
                if translated.lower().startswith(
                    (
                        "here's a translation",
                        "here is a translation",
                        "translation:",
                        "the translation is",
                    )
                ):
                    raise ValueError("Translation returned commentary")
                return {
                    "source_text": source_text,
                    "detected_language": source_code,
                    "translation_needed": True,
                    "translated_value_text": translated,
                    "translation_method": f"ollama:{OLLAMA_MODEL}",
                    "translation_status": "translated",
                    "translation_error": "",
                }
            except Exception as error:
                if attempt == MAX_TRANSLATION_RETRIES - 1:
                    return {
                        "source_text": source_text,
                        "detected_language": source_code,
                        "translation_needed": True,
                        "translated_value_text": None,
                        "translation_method": f"ollama:{OLLAMA_MODEL}",
                        "translation_status": "failed",
                        "translation_error": type(error).__name__,
                    }
                await asyncio.sleep(2**attempt)
    raise AssertionError("translation retry loop did not return")


async def run_translation(
    texts: list[str], client: httpx.AsyncClient | None = None
) -> list[dict[str, Any]]:
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TRANSLATIONS)
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=TRANSLATION_TIMEOUT_SECONDS)
    try:
        if owns_client:
            health = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            health.raise_for_status()
        return await asyncio.gather(
            *(translate_value(text, client, semaphore) for text in texts)
        )
    finally:
        if owns_client:
            await client.aclose()


def translate_candidates(
    candidates: pd.DataFrame,
    cache_path: Path,
    output_path: Path,
    *,
    rerun: bool = False,
) -> pd.DataFrame:
    required = {"candidate_text", "candidate_error", "quality_status"}
    missing = required - set(candidates.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    selected = candidates.loc[
        candidates["candidate_error"].fillna("").eq("")
        & candidates["candidate_text"].fillna("").str.strip().ne("")
        & candidates["quality_status"].eq("accepted")
    ].copy()
    selected["_translation_key"] = (
        selected["candidate_text"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    unique_texts = selected["_translation_key"].drop_duplicates().tolist()
    if cache_path.exists() and not rerun:
        cache = pd.read_csv(cache_path)
    else:
        cache = pd.DataFrame(columns=TRANSLATION_COLUMNS)
    cached = set(cache.get("source_text", pd.Series(dtype=str)).dropna().astype(str))
    pending = [text for text in unique_texts if text not in cached]
    if pending:
        new = pd.DataFrame(asyncio.run(run_translation(pending)))
        cache = (
            pd.concat([cache, new], ignore_index=True)
            .drop_duplicates("source_text", keep="last")
            .reset_index(drop=True)
        )
        write_csv_atomic(cache, cache_path, encoding="utf-8-sig")

    results = cache.loc[cache["source_text"].isin(unique_texts)].copy()
    translated = (
        selected.merge(
            results,
            left_on="_translation_key",
            right_on="source_text",
            how="left",
            validate="many_to_one",
        )
        .drop(columns=["_translation_key", "source_text"])
    )
    export_columns = [
        "company_id",
        "name",
        "country",
        "size_bucket",
        "internal_url",
        "depth",
        "candidate_section_heading",
        "heading_matched_theme",
        "heading_similarity_score",
        "section_positive_score",
        "section_negative_score",
        "section_semantic_margin",
        "candidate_section_count",
        "candidate_text",
        "quality_status",
        "contains_value_signal",
        "detected_language",
        "translation_needed",
        "translated_value_text",
        "translation_method",
        "translation_status",
        "translation_error",
    ]
    for column in export_columns:
        if column not in translated:
            translated[column] = pd.NA
    export = translated[export_columns].rename(
        columns={"company_id": "id", "detected_language": "detect_language"}
    )
    for column in export.select_dtypes(include=["object", "string"]).columns:
        export[column] = (
            export[column]
            .astype("string")
            .str.replace(r"[\r\n\t]+", " ", regex=True)
            .str.replace(r"\s{2,}", " ", regex=True)
            .str.strip()
        )
    write_csv_atomic(
        export,
        output_path,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    return export
