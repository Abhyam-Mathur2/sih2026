"""
Matching Engine – multi-signal material similarity scoring.

Signals:
  1. Semantic  – cosine similarity of sentence-transformer embeddings (35%)
  2. Fuzzy     – RapidFuzz token_sort_ratio on normalized descriptions (20%)
  3. Attribute – Jaccard overlap of extracted attributes (25%)
  4. Technical – heuristic overlap (UoM, manufacturer, and domain rules) (20%)

Final score = weighted sum (0-100 scale) with hard domain rule vetoes.
"""
from __future__ import annotations

import re
from typing import Any

from app.core.config import settings

try:
    from rapidfuzz import fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Text normalisation helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str) -> set[str]:
    return set(normalize_text(text).split())


# ---------------------------------------------------------------------------
# Individual score components
# ---------------------------------------------------------------------------

def fuzzy_score(a: str, b: str) -> float:
    """Token-sort fuzzy ratio (0-100)."""
    if not a and not b:
        return 100.0
    if not a or not b:
        return 0.0
    if not _RAPIDFUZZ_AVAILABLE:
        # Fallback: simple keyword overlap Jaccard
        ka, kb = extract_keywords(a), extract_keywords(b)
        if not ka and not kb:
            return 100.0
        if not ka or not kb:
            return 0.0
        return 100.0 * len(ka & kb) / len(ka | kb)
    return float(fuzz.token_sort_ratio(normalize_text(a), normalize_text(b)))


def semantic_score(emb_a: list[float], emb_b: list[float]) -> float:
    """Cosine similarity (0-100) between two embedding vectors."""
    if not emb_a or not emb_b or not _NUMPY_AVAILABLE:
        return 0.0
    va = np.array(emb_a, dtype=np.float32)
    vb = np.array(emb_b, dtype=np.float32)
    norm_a, norm_b = np.linalg.norm(va), np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    cos_sim = float(np.dot(va, vb) / (norm_a * norm_b))
    # Clamp to [0, 1] then scale
    return max(0.0, min(1.0, cos_sim)) * 100.0


def attribute_score(attrs_a: dict[str, str], attrs_b: dict[str, str]) -> float:
    """Jaccard similarity of attribute key-value pairs (0-100)."""
    if not attrs_a and not attrs_b:
        # Neutral baseline when neither record has extracted attributes
        return 50.0
    if not attrs_a or not attrs_b:
        return 0.0

    set_a = {f"{k.lower()}:{normalize_text(v)}" for k, v in attrs_a.items()}
    set_b = {f"{k.lower()}:{normalize_text(v)}" for k, v in attrs_b.items()}
    union_len = len(set_a | set_b)
    if union_len == 0:
        return 50.0
    return 100.0 * len(set_a & set_b) / union_len


def _extract_field(obj: Any, field_name: str) -> str:
    """Extract a string field safely from an ORM model or dictionary."""
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return str(obj.get(field_name) or "").strip().lower()
    return str(getattr(obj, field_name, "") or "").strip().lower()


def technical_score(mat_a: Any, mat_b: Any) -> float:
    """Heuristic score based on UoM + manufacturer similarity (0-100)."""
    score = 0.0
    components = 0

    # Unit of measure
    uom_a = _extract_field(mat_a, "unit_of_measure")
    uom_b = _extract_field(mat_b, "unit_of_measure")
    if uom_a and uom_b:
        components += 1
        score += 100.0 if uom_a == uom_b else 0.0

    # Manufacturer
    mfr_a = _extract_field(mat_a, "manufacturer")
    mfr_b = _extract_field(mat_b, "manufacturer")
    if mfr_a and mfr_b:
        components += 1
        score += fuzzy_score(mfr_a, mfr_b)

    return score / components if components > 0 else 50.0  # neutral if unknown


def validate_critical_attributes(attrs_a: dict[str, str], attrs_b: dict[str, str]) -> tuple[float, list[str]]:
    """
    Validate critical engineering specifications.
    Enforces strict compatibility across product types, sizes, materials, pressure, and electrical specs.
    """
    critical = [
        "product_type",
        "size",
        "material_grade",
        "pressure_rating",
        "voltage",
        "power_rating",
        "schedule",
        "bearing_number",
    ]

    failures: list[str] = []
    compared: list[str] = []

    for key in critical:
        val_a = attrs_a.get(key)
        val_b = attrs_b.get(key)
        if val_a and val_b:
            norm_a = normalize_text(val_a)
            norm_b = normalize_text(val_b)
            compared.append(key)
            if norm_a != norm_b:
                failures.append(key)

    if failures:
        score = 0.0
    elif compared:
        score = 100.0
    else:
        score = 50.0  # neutral when no critical attributes could be compared

    return score, failures


def apply_critical_vetoes(raw_score: float, failures: list[str]) -> float:
    """
    Apply hard domain rule vetoes to composite scores:
    1. If product_type contradicts (e.g. Pump vs Valve), enforce DIFFERENT (< 60%).
    2. If multiple critical specs contradict, enforce DIFFERENT (< 60%).
    3. If any single critical spec contradicts (size, grade, rating), cap below NEAR_DUPLICATE (< 80%).
    """
    if not failures:
        return raw_score

    # Product type conflict is an absolute veto
    if "product_type" in failures:
        return min(raw_score, settings.threshold_functional - 0.01)

    # Multiple critical failures (e.g. size + material grade conflict)
    if len(failures) >= 2:
        return min(raw_score, settings.threshold_functional - 0.01)

    # Single critical attribute failure (e.g. 2" vs 4" size conflict or SS304 vs SS316 grade conflict)
    return min(raw_score, settings.threshold_near_duplicate - 0.01)


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

def compute_final_score(
    sem: float, fuz: float, att: float, tec: float
) -> float:
    """Weighted combination (0-100)."""
    return (
        settings.weight_semantic * sem
        + settings.weight_fuzzy * fuz
        + settings.weight_attribute * att
        + settings.weight_technical * tec
    )


def classify_match(score: float) -> str:
    """Map final score to MatchType enum value."""
    if score >= settings.threshold_identical:
        return "IDENTICAL"
    if score >= settings.threshold_near_duplicate:
        return "NEAR_DUPLICATE"
    if score >= settings.threshold_functional:
        return "FUNCTIONALLY_EQUIVALENT"
    return "DIFFERENT"


def build_explanation(
    sem: float, fuz: float, att: float, tec: float, final: float
) -> dict[str, Any]:
    return {
        "semantic_score": round(sem, 2),
        "fuzzy_score": round(fuz, 2),
        "attribute_score": round(att, 2),
        "technical_score": round(tec, 2),
        "final_score": round(final, 2),
        "weights": {
            "semantic": settings.weight_semantic,
            "fuzzy": settings.weight_fuzzy,
            "attribute": settings.weight_attribute,
            "technical": settings.weight_technical,
        },
    }

