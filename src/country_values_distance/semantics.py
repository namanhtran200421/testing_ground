from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import numpy as np
from bs4 import BeautifulSoup, NavigableString, Tag

from country_values_distance.config import (
    CONTENT_SCORING_CHARACTERS,
    EXCLUDED_SECTION_ANCESTORS,
    MAX_HEADING_CHARACTERS,
    MAX_SECTION_CHARACTERS,
    MAX_SECTION_ELEMENTS,
    MIN_HEADING_SIMILARITY,
    MIN_SECTION_CHARACTERS,
    MODEL_NAME,
    NEGATIVE_CONTENT_THEMES,
    PRIMARY_VALUE_HEADING_PATTERNS,
    SECTION_HEADING_THEMES,
    SECTION_REJECTION_THEMES,
    SECTION_VERIFICATION_THEMES,
    TARGET_CONTENT_THEMES,
    TARGET_LINK_THEMES,
    VALUE_SECTION_PATTERNS,
    VALUE_WORD_PATTERNS,
)
from country_values_distance.web import build_feature_text


def is_explicit_primary_value_heading(heading_text: str) -> bool:
    cleaned = re.sub(r"\s+", " ", str(heading_text)).strip().lower()
    return any(re.search(pattern, cleaned) for pattern in PRIMARY_VALUE_HEADING_PATTERNS)


def split_text_into_chunks(
    text: str, chunk_size: int = 1_500, overlap: int = 250
) -> list[str]:
    if overlap < 0 or chunk_size <= overlap:
        raise ValueError("chunk_size must be positive and greater than overlap")
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        if chunk := cleaned[start:end].strip():
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = end - overlap
    return chunks


def calculate_value_evidence(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"\s+", " ", str(text)).strip().lower()
    section_matches = sum(
        bool(re.search(pattern, cleaned)) for pattern in VALUE_SECTION_PATTERNS
    )
    value_word_matches = sum(
        bool(re.search(pattern, cleaned)) for pattern in VALUE_WORD_PATTERNS
    )
    return {
        "value_section_matches": section_matches,
        "named_value_matches": value_word_matches,
        "contains_value_signal": section_matches >= 1 or value_word_matches >= 3,
    }


class SemanticScorer:
    """Load notebook 02's multilingual model once and reuse its theme embeddings."""

    def __init__(self, model_name: str = MODEL_NAME, model: Any | None = None) -> None:
        try:
            import torch
            from sentence_transformers import SentenceTransformer, util
        except ImportError as error:  # pragma: no cover - exercised by packaging users
            raise RuntimeError(
                "Semantic crawling requires the 'semantic' project dependencies."
            ) from error

        self.torch = torch
        self.util = util
        self.model = model or SentenceTransformer(model_name)
        self.link_theme_embeddings = self._encode(TARGET_LINK_THEMES)
        self.positive_content_theme_embeddings = self._encode(TARGET_CONTENT_THEMES)
        self.negative_content_theme_embeddings = self._encode(NEGATIVE_CONTENT_THEMES)
        self.section_heading_theme_embeddings = self._encode(SECTION_HEADING_THEMES)
        self.section_verification_embeddings = self._encode(
            SECTION_VERIFICATION_THEMES
        )
        self.section_rejection_embeddings = self._encode(SECTION_REJECTION_THEMES)

    def _encode(self, texts: list[str]) -> Any:
        return self.model.encode(
            texts, convert_to_tensor=True, normalize_embeddings=True
        )

    def score_discovered_links(
        self, links: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        valid_links: list[dict[str, str]] = []
        features: list[str] = []
        for link in links:
            feature = build_feature_text(link["anchor_text"], link["url_path"])
            if feature.strip():
                valid_links.append(link)
                features.append(feature)
        if not valid_links:
            return []

        scores = self.util.cos_sim(self._encode(features), self.link_theme_embeddings)
        maximums, indexes = self.torch.max(scores, dim=1)
        return [
            {
                **link,
                "feature_text": feature,
                "similarity_score": float(score),
                "matched_theme": TARGET_LINK_THEMES[index],
            }
            for link, feature, score, index in zip(
                valid_links,
                features,
                maximums.cpu().tolist(),
                indexes.cpu().tolist(),
            )
        ]

    def score_page_content(self, page_text: str) -> dict[str, float]:
        chunks = split_text_into_chunks(
            str(page_text)[:CONTENT_SCORING_CHARACTERS]
        )
        if not chunks:
            return {
                "content_positive_score": float("nan"),
                "content_negative_score": float("nan"),
                "semantic_margin": float("nan"),
            }
        embeddings = self._encode(chunks)
        positive = self.util.cos_sim(
            embeddings, self.positive_content_theme_embeddings
        ).max(dim=1).values
        negative = self.util.cos_sim(
            embeddings, self.negative_content_theme_embeddings
        ).max(dim=1).values
        margins = positive - negative
        best = int(self.torch.argmax(margins).item())
        return {
            "content_positive_score": float(positive[best].cpu().item()),
            "content_negative_score": float(negative[best].cpu().item()),
            "semantic_margin": float(margins[best].cpu().item()),
        }

    def extract_candidate_sections_from_html(
        self,
        html: str,
        max_elements: int = MAX_SECTION_ELEMENTS,
        max_characters: int = MAX_SECTION_CHARACTERS,
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav",
                "form",
                "aside",
                "iframe",
                "svg",
                "button",
            ]
        ):
            tag.decompose()

        heading_names = ["h1", "h2", "h3", "h4", "h5", "h6"]
        records = []
        texts = []
        for heading in soup.find_all(heading_names):
            text = re.sub(r"\s+", " ", heading.get_text(" ", strip=True)).strip()
            if text and len(text) <= MAX_HEADING_CHARACTERS:
                records.append((heading, text))
                texts.append(text)
        if not records:
            return []

        scores = self.util.cos_sim(
            self._encode(texts), self.section_heading_theme_embeddings
        )
        maximums, indexes = self.torch.max(scores, dim=1)
        sections: list[dict[str, Any]] = []
        heading_tag_set = set(heading_names)

        for (heading, heading_text), score, theme_index in zip(
            records, maximums.cpu().tolist(), indexes.cpu().tolist()
        ):
            heading_similarity = float(score)
            if heading_similarity < MIN_HEADING_SIMILARITY:
                continue
            heading_level = int(heading.name[1])
            parts = [heading_text]
            seen = {heading_text}
            count = 0
            for node in heading.next_elements:
                if node is heading:
                    continue
                if isinstance(node, Tag) and node.name in heading_tag_set:
                    if int(node.name[1]) <= heading_level:
                        break
                if isinstance(node, Tag) and node.name == "img":
                    image_text = re.sub(
                        r"\s+",
                        " ",
                        " ".join(
                            str(value).strip()
                            for value in (
                                node.get("alt", ""),
                                node.get("title", ""),
                                node.get("aria-label", ""),
                            )
                            if value and str(value).strip()
                        ),
                    ).strip()
                    if image_text and image_text not in seen:
                        parts.append(image_text)
                        seen.add(image_text)
                        count += 1
                    if count >= max_elements:
                        break
                    continue
                if not isinstance(node, NavigableString) or node.parent is None:
                    continue
                if any(
                    getattr(ancestor, "name", None) in EXCLUDED_SECTION_ANCESTORS
                    for ancestor in [node.parent, *node.parent.parents]
                ):
                    continue
                text = re.sub(r"\s+", " ", str(node)).strip()
                if not text or text in seen:
                    continue
                parts.append(text)
                seen.add(text)
                count += 1
                if count >= max_elements:
                    break

            section_text = re.sub(r"\s+", " ", " ".join(parts)).strip()[
                :max_characters
            ]
            if len(section_text) < MIN_SECTION_CHARACTERS:
                continue
            sections.append(
                {
                    "section_heading": heading_text,
                    "section_text": section_text,
                    "heading_similarity_score": heading_similarity,
                    "heading_matched_theme": SECTION_HEADING_THEMES[theme_index],
                    "is_primary_value_heading": is_explicit_primary_value_heading(
                        heading_text
                    ),
                }
            )
        return sections

    def select_best_candidate_section(self, html: str) -> dict[str, Any]:
        sections = self.extract_candidate_sections_from_html(html)
        empty = {
            "candidate_section_heading": "",
            "candidate_section_text": "",
            "heading_similarity_score": np.nan,
            "heading_matched_theme": "",
            "section_positive_score": np.nan,
            "section_negative_score": np.nan,
            "section_semantic_margin": np.nan,
            "candidate_section_count": len(sections),
            "contains_primary_value_section": False,
        }
        if not sections:
            return empty

        features = [
            f"Heading: {s['section_heading']}. Section: {s['section_text'][:1_500]}"
            for s in sections
        ]
        embeddings = self._encode(features)
        positive = self.util.cos_sim(
            embeddings, self.section_verification_embeddings
        ).max(dim=1).values
        negative = self.util.cos_sim(
            embeddings, self.section_rejection_embeddings
        ).max(dim=1).values
        margins = positive - negative
        qualified = []

        for index, section in enumerate(sections):
            pos = float(positive[index].cpu().item())
            neg = float(negative[index].cpu().item())
            margin = float(margins[index].cpu().item())
            heading = float(section["heading_similarity_score"])
            primary = bool(section["is_primary_value_heading"])
            if primary:
                passes = (
                    (heading >= 0.65 and pos >= 0.40 and margin >= 0.05)
                    or (heading >= 0.48 and pos >= 0.44 and margin >= 0.10)
                    or (heading >= 0.38 and pos >= 0.50 and margin >= 0.18)
                )
            else:
                passes = (
                    (heading >= 0.68 and pos >= 0.42 and margin >= 0.07)
                    or (heading >= 0.50 and pos >= 0.47 and margin >= 0.14)
                )
            if passes:
                qualified.append(
                    {
                        **section,
                        "section_positive_score": pos,
                        "section_negative_score": neg,
                        "section_semantic_margin": margin,
                        "section_priority_score": (
                            margin
                            + 0.20 * heading
                            + 0.10 * pos
                            - 0.10 * neg
                            + (0.20 if primary else 0.0)
                        ),
                        "original_index": index,
                    }
                )
        if not qualified:
            return empty

        primary_sections = [
            section for section in qualified if section["is_primary_value_heading"]
        ]
        supporting = [
            section
            for section in qualified
            if not section["is_primary_value_heading"]
        ]
        rank_key = lambda section: (
            section["section_priority_score"],
            section["section_semantic_margin"],
            section["section_positive_score"],
        )
        if primary_sections:
            selected = primary_sections.copy()
            if supporting:
                selected.append(max(supporting, key=rank_key))
        else:
            selected = [max(supporting, key=rank_key)]
        selected.sort(key=lambda section: section["original_index"])

        parts: list[str] = []
        keys: list[str] = []
        for section in selected:
            text = re.sub(r"\s+", " ", section["section_text"]).strip()
            key = text.lower()
            if text and not any(key in old or old in key for old in keys):
                parts.append(text)
                keys.append(key)

        return {
            "candidate_section_heading": " | ".join(
                dict.fromkeys(s["section_heading"] for s in selected)
            ),
            "candidate_section_text": re.sub(
                r"\s+", " ", " ".join(parts)
            ).strip()[:MAX_SECTION_CHARACTERS],
            "heading_similarity_score": max(
                s["heading_similarity_score"] for s in selected
            ),
            "heading_matched_theme": " | ".join(
                dict.fromkeys(s["heading_matched_theme"] for s in selected)
            ),
            "section_positive_score": max(
                s["section_positive_score"] for s in selected
            ),
            "section_negative_score": min(
                s["section_negative_score"] for s in selected
            ),
            "section_semantic_margin": max(
                s["section_semantic_margin"] for s in selected
            ),
            "candidate_section_count": len(sections),
            "contains_primary_value_section": bool(primary_sections),
        }


@lru_cache(maxsize=1)
def get_semantic_scorer(model_name: str = MODEL_NAME) -> SemanticScorer:
    """Return the process-wide model instance used by notebook-compatible helpers."""
    return SemanticScorer(model_name=model_name)


def score_discovered_links(
    links: list[dict[str, str]], scorer: SemanticScorer | None = None
) -> list[dict[str, Any]]:
    return (scorer or get_semantic_scorer()).score_discovered_links(links)


def score_page_content(
    page_text: str, scorer: SemanticScorer | None = None
) -> dict[str, float]:
    return (scorer or get_semantic_scorer()).score_page_content(page_text)


def extract_candidate_sections_from_html(
    html: str,
    max_elements: int = MAX_SECTION_ELEMENTS,
    max_characters: int = MAX_SECTION_CHARACTERS,
    scorer: SemanticScorer | None = None,
) -> list[dict[str, Any]]:
    return (scorer or get_semantic_scorer()).extract_candidate_sections_from_html(
        html, max_elements=max_elements, max_characters=max_characters
    )


def select_best_candidate_section(
    html: str, scorer: SemanticScorer | None = None
) -> dict[str, Any]:
    return (scorer or get_semantic_scorer()).select_best_candidate_section(html)
