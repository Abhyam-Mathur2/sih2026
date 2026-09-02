"""
Match service – triggers AI matching, handles the review workflow,
and completes the end-to-end pipeline (approval → NMC generation → mapping).

Critical fixes over the original:
  1. Match approval auto-generates a NationalMaterial + MaterialMapping
  2. Audit trail is written for every state change
  3. Batch duplicate detection endpoint support
  4. Candidate limit raised to handle full dataset
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
from app.models.material_mapping import MaterialMapping, MappingStatus
from app.models.national_material import NationalMaterial, NationalMaterialStatus
from app.models.user import User
from app.services.matching_engine import (
    apply_critical_vetoes,
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
    old_status = match.status.value

    match.status = action
    match.reviewed_by = reviewer.id
    match.reviewer_comment = comment
    match.reviewed_at = datetime.now(timezone.utc)
    if modified_score is not None:
        match.final_score = modified_score
        match.match_type = MatchType(classify_match(modified_score))
    await db.flush()

    # -----------------------------------------------------------------------
    # END-TO-END FLOW: When a match is APPROVED, auto-generate NMC + mapping
    # -----------------------------------------------------------------------
    if action == MatchStatus.APPROVED:
        await _auto_create_nmc_and_mapping(db, match, reviewer)

    # -----------------------------------------------------------------------
    # AUDIT TRAIL
    # -----------------------------------------------------------------------
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=reviewer.id,
        entity_type="MaterialMatch",
        entity_id=match.id,
        action=f"MATCH_{action.value}",
        old_value={"status": old_status},
        new_value={
            "status": action.value,
            "final_score": match.final_score,
            "match_type": match.match_type.value,
            "comment": comment,
        },
    )

    await db.refresh(match)
    return match


async def _auto_create_nmc_and_mapping(
    db: AsyncSession, match: MaterialMatch, reviewer: User
) -> None:
    """
    When a match is approved, find-or-create a NationalMaterial record and
    create MaterialMapping rows linking both materials to it.
    """
    from app.services.national_code_service import generate_code
    from app.services.audit_service import log_action

    # Gather attributes from source material
    src_result = await db.execute(
        select(Material)
        .where(Material.id == match.source_material_id)
        .options(selectinload(Material.attributes))
    )
    source = src_result.scalar_one_or_none()
    if not source:
        return

    source_attrs = {a.attribute_name: a.attribute_value for a in source.attributes}

    # Check if either material already has an approved mapping
    existing_mapping = await db.execute(
        select(MaterialMapping).where(
            MaterialMapping.material_id.in_([
                match.source_material_id, match.candidate_material_id
            ]),
            MaterialMapping.mapping_status == MappingStatus.APPROVED,
        )
    )
    existing = existing_mapping.scalar_one_or_none()

    if existing:
        # Reuse the existing NMC
        nmc_id = existing.national_material_id
    else:
        # Generate a new NMC
        cat_name = None
        if source.category_id:
            from app.models.material_category import MaterialCategory
            cat_result = await db.execute(
                select(MaterialCategory.name).where(MaterialCategory.id == source.category_id)
            )
            cat_name = cat_result.scalar_one_or_none()

        code = await generate_code(db, cat_name, source_attrs)
        nm = NationalMaterial(
            national_material_code=code,
            standard_description=source.normalized_description or source.original_description,
            category_id=source.category_id,
            standard_attributes=source_attrs or None,
            status=NationalMaterialStatus.ACTIVE,
        )
        db.add(nm)
        await db.flush()
        nmc_id = nm.id

        await log_action(
            db,
            user_id=reviewer.id,
            entity_type="NationalMaterial",
            entity_id=nm.id,
            action="NMC_AUTO_GENERATED",
            new_value={"code": code, "description": nm.standard_description},
        )

    # Create mappings for both materials (skip if already mapped)
    for mat_id in [match.source_material_id, match.candidate_material_id]:
        exists = await db.execute(
            select(MaterialMapping.id).where(
                MaterialMapping.material_id == mat_id,
                MaterialMapping.national_material_id == nmc_id,
            )
        )
        if exists.scalar_one_or_none():
            continue

        mapping = MaterialMapping(
            material_id=mat_id,
            national_material_id=nmc_id,
            mapping_status=MappingStatus.APPROVED,
            approved_by=reviewer.id,
            approved_at=datetime.now(timezone.utc),
        )
        db.add(mapping)

        await log_action(
            db,
            user_id=reviewer.id,
            entity_type="MaterialMapping",
            entity_id=f"{mat_id}->{nmc_id}",
            action="MAPPING_AUTO_CREATED",
            new_value={"material_id": mat_id, "national_material_id": nmc_id},
        )

    await db.flush()


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

    # Load candidate materials (all other materials — raised from 500 limit)
    cand_result = await db.execute(
        select(Material)
        .where(Material.id != material_id)
        .options(selectinload(Material.attributes))
        .limit(5000)
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
        raw_final = compute_final_score(sem, fuz, att, tec)
        final = apply_critical_vetoes(raw_final, failures)
        explanation = build_explanation(sem, fuz, att, tec, final)
        explanation["critical_attribute_failures"] = failures
        explanation["technical_validation"] = "FAILED" if failures else "PASSED"

        scored.append((final, cand, explanation))

    # Keep top-k by final score
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    # Batch-load all existing matches for top candidates in a single query
    top_cand_ids = [cand.id for _, cand, _ in top]
    existing_result = await db.execute(
        select(MaterialMatch).where(
            MaterialMatch.source_material_id == material_id,
            MaterialMatch.candidate_material_id.in_(top_cand_ids),
        )
    )
    existing_map = {m.candidate_material_id: m for m in existing_result.scalars().all()}

    created_matches: list[MaterialMatch] = []
    for final, cand, expl in top:
        existing_match = existing_map.get(cand.id)
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
    await db.commit()

    # Audit
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=None,
        entity_type="Material",
        entity_id=material_id,
        action="MATCHING_TRIGGERED",
        new_value={
            "candidates_evaluated": len(candidates),
            "matches_created": len(created_matches),
            "top_score": round(top[0][0], 2) if top else 0,
        },
    )

    return created_matches


async def batch_detect_duplicates(
    db: AsyncSession,
    *,
    top_k: int = 10,
    min_score: float = 60.0,
    limit_materials: int = 500,
) -> dict[str, Any]:
    """
    Batch duplicate detection: iterate all materials and find matches.
    Returns summary statistics.

    PS requirement: "Dashboard for material master analytics and duplicate detection."
    """
    from app.services.audit_service import log_action

    # Get materials that haven't been matched yet (no source_matches)
    already_matched_ids_q = select(MaterialMatch.source_material_id).distinct()
    already_matched_result = await db.execute(already_matched_ids_q)
    already_matched = {row[0] for row in already_matched_result.all()}

    # Get all materials
    all_mats_result = await db.execute(
        select(Material.id).order_by(Material.id).limit(limit_materials)
    )
    all_mat_ids = [row[0] for row in all_mats_result.all()]

    # Filter to only unmatched
    to_process = [mid for mid in all_mat_ids if mid not in already_matched]

    total_matches_created = 0
    total_processed = 0
    duplicates_found = 0

    for mat_id in to_process:
        try:
            matches = await trigger_matching_for_material(db, mat_id, top_k=top_k)
            total_processed += 1
            good_matches = [m for m in matches if m.final_score >= min_score]
            total_matches_created += len(good_matches)
            if good_matches:
                duplicates_found += 1
        except Exception:
            continue

    await db.flush()

    summary = {
        "total_materials": len(all_mat_ids),
        "already_matched": len(already_matched),
        "newly_processed": total_processed,
        "duplicates_found": duplicates_found,
        "total_matches_created": total_matches_created,
        "min_score_threshold": min_score,
    }

    await log_action(
        db,
        user_id=None,
        entity_type="System",
        entity_id="batch_detect",
        action="BATCH_DUPLICATE_DETECTION",
        new_value=summary,
    )

    return summary
