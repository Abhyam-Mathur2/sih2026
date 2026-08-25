"""
Match service – triggers AI matching and handles the review workflow.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.material import Material
from app.models.material_embedding import MaterialEmbedding, PGVECTOR_ENABLED
from app.models.material_match import MatchStatus, MatchType, MaterialMatch
from app.models.user import User
from app.services.matching_engine import (
    attribute_score,
    build_explanation,
    classify_match,
    compute_final_score,
    fuzzy_score,
    semantic_score,
    technical_score,
    validate_critical_attributes,
)


async def get_match(db: AsyncSession, match_id: int) -> MaterialMatch:
    result = await db.execute(
        select(MaterialMatch)
        .where(MaterialMatch.id == match_id)
        .options(
            selectinload(MaterialMatch.source_material),
            selectinload(MaterialMatch.candidate_material),
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        raise NotFoundError("MaterialMatch", match_id)
    return match


async def list_matches(
    db: AsyncSession,
    *,
    status: MatchStatus | None = None,
    match_type: MatchType | None = None,
    source_material_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[MaterialMatch], int]:
    query = select(MaterialMatch)
    count_q = select(func.count()).select_from(MaterialMatch)

    if status is not None:
        query = query.where(MaterialMatch.status == status)
        count_q = count_q.where(MaterialMatch.status == status)
    if match_type is not None:
        query = query.where(MaterialMatch.match_type == match_type)
        count_q = count_q.where(MaterialMatch.match_type == match_type)
    if source_material_id is not None:
        query = query.where(MaterialMatch.source_material_id == source_material_id)
        count_q = count_q.where(MaterialMatch.source_material_id == source_material_id)

    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    query = (
        query.order_by(MaterialMatch.final_score.desc())
        .offset(skip)
        .limit(limit)
        .options(
            selectinload(MaterialMatch.source_material),
            selectinload(MaterialMatch.candidate_material),
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def review_match(
    db: AsyncSession,
    match_id: int,
    action: MatchStatus,
    reviewer: User,
    comment: str | None = None,
    modified_score: float | None = None,
) -> MaterialMatch:
    match = await get_match(db, match_id)
    match.status = action
    match.reviewed_by = reviewer.id
    match.reviewer_comment = comment
    match.reviewed_at = datetime.now(timezone.utc)
    if modified_score is not None:
        match.final_score = modified_score
        match.match_type = MatchType(classify_match(modified_score))
    await db.flush()
    await db.refresh(match)
    return match


async def trigger_matching_for_material(
    db: AsyncSession, material_id: int, top_k: int = 20
) -> list[MaterialMatch]:
    """
    Run the multi-signal matching pipeline for a given material
    against all other active materials with embeddings.
    Creates/updates MaterialMatch rows. Returns created matches.
    """
    # Load source material
    src_result = await db.execute(
        select(Material)
        .where(Material.id == material_id)
        .options(selectinload(Material.attributes))
    )
    source = src_result.scalar_one_or_none()
    if not source:
        raise NotFoundError("Material", material_id)

    # Load source embedding
    emb_result = await db.execute(
        select(MaterialEmbedding).where(MaterialEmbedding.material_id == material_id)
    )
    source_emb = emb_result.scalar_one_or_none()

    # Load candidate materials (excluding source's CPSE to find cross-CPSE matches)
    cand_result = await db.execute(
        select(Material)
        .where(Material.id != material_id)
        .options(selectinload(Material.attributes))
        .limit(500)  # safety limit – in production use ANN index
    )
    candidates = list(cand_result.scalars().all())

    # Load candidate embeddings
    cand_ids = [c.id for c in candidates]
    emb_cand_result = await db.execute(
        select(MaterialEmbedding).where(MaterialEmbedding.material_id.in_(cand_ids))
    )
    embeddings_map: dict[int, list[float]] = {
        e.material_id: list(e.embedding) for e in emb_cand_result.scalars().all()
    }

    source_attrs = {a.attribute_name: a.attribute_value for a in source.attributes}
    source_emb_vec = list(source_emb.embedding) if source_emb else []

    scored: list[tuple[float, Material, dict[str, Any]]] = []
    for cand in candidates:
        cand_attrs = {a.attribute_name: a.attribute_value for a in cand.attributes}
        cand_emb_vec = embeddings_map.get(cand.id, [])

        sem = semantic_score(source_emb_vec, cand_emb_vec) if source_emb_vec and cand_emb_vec else 0.0
        fuz = fuzzy_score(
            source.normalized_description or source.original_description,
            cand.normalized_description or cand.original_description,
        )
        att = attribute_score(source_attrs, cand_attrs)
        rule_score, failures = validate_critical_attributes(source_attrs, cand_attrs)
        tec = (technical_score(source, cand) + rule_score) / 2
        final = compute_final_score(sem, fuz, att, tec)
        # A contradictory critical specification can never be an identical match.
        if failures:
            final = min(final, settings.threshold_near_duplicate - 0.01)
        explanation = build_explanation(sem, fuz, att, tec, final)
        explanation["critical_attribute_failures"] = failures
        explanation["technical_validation"] = "FAILED" if failures else "PASSED"

        scored.append((final, cand, explanation))

    # Keep top-k by final score
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    created_matches: list[MaterialMatch] = []
    for final, cand, expl in top:
        # Avoid duplicates
        existing = await db.execute(
            select(MaterialMatch).where(
                MaterialMatch.source_material_id == material_id,
                MaterialMatch.candidate_material_id == cand.id,
            )
        )
        existing_match = existing.scalar_one_or_none()
        if existing_match:
            # Update scores
            existing_match.final_score = final
            existing_match.semantic_score = expl["semantic_score"]
            existing_match.fuzzy_score = expl["fuzzy_score"]
            existing_match.attribute_score = expl["attribute_score"]
            existing_match.technical_score = expl["technical_score"]
            existing_match.match_type = MatchType(classify_match(final))
            existing_match.explanation = expl
            created_matches.append(existing_match)
        else:
            match = MaterialMatch(
                source_material_id=material_id,
                candidate_material_id=cand.id,
                semantic_score=expl["semantic_score"],
                fuzzy_score=expl["fuzzy_score"],
                attribute_score=expl["attribute_score"],
                technical_score=expl["technical_score"],
                final_score=final,
                match_type=MatchType(classify_match(final)),
                status=MatchStatus.PENDING,
                explanation=expl,
            )
            db.add(match)
            created_matches.append(match)

    await db.flush()
    return created_matches
