"""
Matching Engine – multi-signal material similarity scoring.

Signals:
  1. Semantic  – cosine similarity of sentence-transformer embeddings
  2. Fuzzy     – RapidFuzz token_sort_ratio on normalized descriptions
  3. Attribute – Jaccard overlap of extracted attributes
  4. Technical – heuristic keyword overlap (UoM, manufacturer)

Final score = weighted sum (0-100 scale).
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
    if not _NUMPY_AVAILABLE:
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
        # Neither side yielded any attributes -- this tells us NOTHING about
        # whether the two materials match, so treat it as neutral (matching
        # the same "50 = unknown" convention technical_score already uses
        # below), not a false 100% match. The old behaviour silently inflated
        # final_score for exactly the categories extract_attributes couldn't
        # parse -- i.e. it was most confidently wrong where it understood the
        # least.
        return 50.0
    if not attrs_a or not attrs_b:
        return 0.0
    set_a = {f"{k}:{normalize_text(v)}" for k, v in attrs_a.items()}
    set_b = {f"{k}:{normalize_text(v)}" for k, v in attrs_b.items()}
    return 100.0 * len(set_a & set_b) / len(set_a | set_b)


def technical_score(mat_a: Any, mat_b: Any) -> float:
    """Heuristic score based on UoM + manufacturer similarity (0-100)."""
    score = 0.0
    components = 0

    # Unit of measure
    uom_a = (mat_a.unit_of_measure or "").strip().lower()
    uom_b = (mat_b.unit_of_measure or "").strip().lower()
    if uom_a and uom_b:
        components += 1
        score += 100.0 if uom_a == uom_b else 0.0

    # Manufacturer
    mfr_a = (mat_a.manufacturer or "").strip().lower()
    mfr_b = (mat_b.manufacturer or "").strip().lower()
    if mfr_a and mfr_b:
        components += 1
        score += fuzzy_score(mfr_a, mfr_b)

    return score / components if components > 0 else 50.0  # neutral if unknown

def validate_critical_attributes(attrs_a: dict[str, str], attrs_b: dict[str, str]) -> tuple[float, list[str]]:
    """Valves require compatible type, size, grade and pressure before identity."""
    critical = ["product_type", "size", "material_grade", "pressure_rating"]
    failures = [key for key in critical if attrs_a.get(key) and attrs_b.get(key) and attrs_a[key] != attrs_b[key]]
    compared = [key for key in critical if attrs_a.get(key) and attrs_b.get(key)]
    return (0.0 if failures else (100.0 if compared else 50.0), failures)


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
