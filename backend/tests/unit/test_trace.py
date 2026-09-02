from app.ai.pipeline import normalize_description, extract_attributes
from app.services.embedding_service import generate_embedding
from app.services.matching_engine import (
    semantic_score, fuzzy_score, attribute_score, technical_score,
    validate_critical_attributes, compute_final_score, apply_critical_vetoes,
    classify_match, build_explanation
)
from app.services.national_code_service import _segment


def test_end_to_end_trace():
    # 1. Source material: CPCL legacy valve
    raw_source = 'BALL VLV 2" SS-316 PN16 FLG'
    norm_source = normalize_description(raw_source)
    emb_source = generate_embedding(norm_source)
    attrs_source = extract_attributes(raw_source)

    # 2. Candidate material: IOCL equivalent valve
    raw_cand = '2 INCH BALL VALVE STAINLESS STEEL 316 PN16 FLANGED'
    norm_cand = normalize_description(raw_cand)
    emb_cand = generate_embedding(norm_cand)
    attrs_cand = extract_attributes(raw_cand)

    # 3. Multi-signal scoring
    sem = semantic_score(emb_source, emb_cand)
    fuz = fuzzy_score(norm_source, norm_cand)
    att = attribute_score(attrs_source, attrs_cand)
    rule_score, failures = validate_critical_attributes(attrs_source, attrs_cand)
    tec = (technical_score({"unit_of_measure": "EA"}, {"unit_of_measure": "EA"}) + rule_score) / 2
    raw_final = compute_final_score(sem, fuz, att, tec)
    final = apply_critical_vetoes(raw_final, failures)
    match_type = classify_match(final)
    expl = build_explanation(sem, fuz, att, tec, final)

    # 4. National Material Code preview
    code_prefix = "-".join([
        "NMC",
        _segment("Valves", "GEN"),
        _segment(attrs_source.get("product_type"), "ITEM"),
        _segment(attrs_source.get("material_grade"), "NA"),
        _segment(attrs_source.get("size"), "NA")
    ])
    nmc_code = f"{code_prefix}-0001"

    assert match_type == "IDENTICAL"
    assert final >= 95.0
    assert nmc_code == "NMC-VALVES-BALLVALVE-SS316-DN50-0001"
    assert expl["weights"]["semantic"] == 0.35
