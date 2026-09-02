from app.ai.pipeline import extract_attributes, normalize_description
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


def test_normalizes_valve_abbreviations():
    assert (
        normalize_description('BALL VLV 2" SS-316 PN16 FLG')
        == "BALL VALVE 2 INCH STAINLESS STEEL 316 PN16 FLANGED"
    )


def test_normalizes_pipe_and_steel_standards():
    t1 = "CS PIPE ASTM A106 GR B DN100 SCH40"
    t2 = "Carbon Steel Pipe ASTM A106 Grade B DN 100 Schedule 40"
    assert normalize_description(t1) == "CARBON STEEL PIPE ASTM A106 GRADE B DN100 SCHEDULE 40"
    assert normalize_description(t2) == "CARBON STEEL PIPE ASTM A106 GRADE B DN100 SCHEDULE 40"


def test_normalizes_plate_and_dimensions():
    t1 = "SS304 Plate 10mm"
    t2 = "Stainless Steel 304 Plate 10 MM"
    assert normalize_description(t1) == "STAINLESS STEEL 304 PLATE 10 MM"
    assert normalize_description(t2) == "STAINLESS STEEL 304 PLATE 10 MM"


def test_extracts_normalized_valve_attributes():
    attrs = extract_attributes('BALL VLV 2" SS-316 PN16 FLG')
    assert attrs["product_type"] == "BALL_VALVE"
    assert attrs["size"] == "DN50"
    assert attrs["material_grade"] == "SS316"
    assert attrs["pressure_rating"] == "PN16"
    assert attrs["connection"] == "FLANGED"


def test_extracts_pipe_and_schedule_attributes():
    attrs = extract_attributes("CS PIPE ASTM A106 GR B DN100 SCH40")
    assert attrs["product_type"] == "PIPE"
    assert attrs["size"] == "DN100"
    assert attrs["material_grade"] == "ASTM A106 GRADE B"
    assert attrs["schedule"] == "SCH 40"


def test_exact_duplicate_matching():
    t1 = "Stainless Steel Plate 304 10mm"
    t2 = "Stainless Steel Plate 304 10mm"
    n1, n2 = normalize_description(t1), normalize_description(t2)
    a1, a2 = extract_attributes(t1), extract_attributes(t2)

    fuz = fuzzy_score(n1, n2)
    att = attribute_score(a1, a2)
    rule_score, failures = validate_critical_attributes(a1, a2)
    tec = 100.0  # same uom / mfr

    final = compute_final_score(100.0, fuz, att, tec)
    final = apply_critical_vetoes(final, failures)
    assert final >= 95.0
    assert classify_match(final) == "IDENTICAL"


def test_near_duplicate_matching():
    t1 = "SS304 Plate 10mm"
    t2 = "Stainless Steel 304 Plate 10 MM"
    n1, n2 = normalize_description(t1), normalize_description(t2)
    a1, a2 = extract_attributes(t1), extract_attributes(t2)

    fuz = fuzzy_score(n1, n2)
    att = attribute_score(a1, a2)
    rule_score, failures = validate_critical_attributes(a1, a2)

    final = compute_final_score(100.0, fuz, att, 100.0)
    final = apply_critical_vetoes(final, failures)
    assert not failures
    assert final >= 80.0
    assert classify_match(final) in ("NEAR_DUPLICATE", "IDENTICAL")


def test_size_conflict_cannot_be_duplicate():
    t1 = "BALL VLV 2\" SS-316 PN16"
    t2 = "BALL VLV 4\" SS-316 PN16"
    a1, a2 = extract_attributes(t1), extract_attributes(t2)

    rule_score, failures = validate_critical_attributes(a1, a2)
    assert "size" in failures
    assert rule_score == 0.0

    raw_final = compute_final_score(85.0, 90.0, 75.0, 50.0)
    final = apply_critical_vetoes(raw_final, failures)
    # Must be capped below near-duplicate threshold (< 80.0)
    assert final < 80.0
    assert classify_match(final) != "IDENTICAL"
    assert classify_match(final) != "NEAR_DUPLICATE"


def test_material_grade_conflict_cannot_be_duplicate():
    t1 = "SS304 Plate 10mm"
    t2 = "SS316 Plate 10mm"
    a1, a2 = extract_attributes(t1), extract_attributes(t2)

    rule_score, failures = validate_critical_attributes(a1, a2)
    assert "material_grade" in failures
    assert rule_score == 0.0

    raw_final = compute_final_score(92.0, 95.0, 70.0, 50.0)
    final = apply_critical_vetoes(raw_final, failures)
    assert final < 80.0
    assert classify_match(final) != "IDENTICAL"
    assert classify_match(final) != "NEAR_DUPLICATE"


def test_product_type_conflict_is_different():
    t1 = "CENTRIFUGAL PUMP 5HP"
    t2 = 'BALL VALVE 2" SS316'
    a1, a2 = extract_attributes(t1), extract_attributes(t2)

    rule_score, failures = validate_critical_attributes(a1, a2)
    assert "product_type" in failures

    raw_final = compute_final_score(40.0, 30.0, 0.0, 50.0)
    final = apply_critical_vetoes(raw_final, failures)
    assert final < 60.0
    assert classify_match(final) == "DIFFERENT"


def test_empty_attributes_return_neutral_score():
    assert attribute_score({}, {}) == 50.0


def test_expanded_product_types_and_inline_attributes():
    attrs_gauge = extract_attributes("PRESSURE GAUGE 0-10 BAR Range:0-10")
    assert attrs_gauge.get("product_type") == "PRESSURE_GAUGE"
    assert attrs_gauge.get("range") == "0-10"

    attrs_bolt = extract_attributes("HEX BOLT M12 Thread:Full")
    assert attrs_bolt.get("product_type") == "HEX_BOLT"
    assert attrs_bolt.get("size") == "M12"
    assert attrs_bolt.get("thread") == "FULL"


def test_explainability_payload():
    expl = build_explanation(95.0, 90.0, 85.0, 80.0, 89.0)
    assert expl["semantic_score"] == 95.0
    assert expl["fuzzy_score"] == 90.0
    assert expl["attribute_score"] == 85.0
    assert expl["technical_score"] == 80.0
    assert expl["final_score"] == 89.0
    assert "weights" in expl


def test_sentence_transformer_semantic_similarity():
    from app.services.embedding_service import generate_embedding

    e1 = generate_embedding(normalize_description("SS304 Plate 10mm"))
    e2 = generate_embedding(normalize_description("Stainless Steel 304 Plate 10 MM"))
    e_diff = generate_embedding(normalize_description("Deep Groove Ball Bearing SKF 6205"))

    sem_match = semantic_score(e1, e2)
    sem_diff = semantic_score(e1, e_diff)

    # Identical normalized text yields 100% semantic score
    assert sem_match >= 98.0
    # Completely different products (Plate vs Bearing) have very low similarity
    assert sem_diff < 50.0


def test_bmim_test_materials_dataset_parsing():
    materials = [
        ("MAT-001", "Stainless Steel Plate SS304 1000mm x 2000mm x 5mm"),
        ("MAT-002", "Carbon Steel Pipe ASTM A106 Grade B DN100 Schedule 40"),
        ("MAT-003", "Copper Cable 4 Core 16 sq mm"),
        ("MAT-004", "Stainless Steel Ball Valve SS316 2 Inch Class 150"),
        ("MAT-005", "Deep Groove Ball Bearing SKF 6205"),
        ("MAT-006", "Industrial Electrical Motor 5 HP Three Phase"),
        ("MAT-007", "Carbon Steel Flange ASTM A105 Class 150"),
        ("MAT-008", "High Tensile Hex Bolt M16 x 100mm"),
        ("MAT-009", "PVC Pipe 110mm Diameter"),
        ("MAT-010", "Aluminium Sheet Grade 6061 3mm Thickness"),
    ]

    for code, desc in materials:
        norm = normalize_description(desc)
        attrs = extract_attributes(desc)
        assert len(norm) > 0
        assert "product_type" in attrs, f"Failed product_type extraction for {code}: {desc}"


def test_classification_product_type_mappings():
    from app.services.classification_service import PRODUCT_TYPE_TO_CATEGORY

    critical_products = [
        ("BALL_VALVE", "VLV"),
        ("PIPE", "PIP"),
        ("PLATE", "PIP"),
        ("CENTRIFUGAL_PUMP", "PMP"),
        ("ELECTRIC_MOTOR", "MTR"),
        ("CIRCUIT_BREAKER", "ELC"),
        ("BALL_BEARING", "BRG"),
        ("HEX_BOLT", "FST"),
        ("SPIRAL_WOUND_GASKET", "GSK"),
        ("PRESSURE_GAUGE", "INS"),
    ]
    for prod, expected_cat in critical_products:
        assert PRODUCT_TYPE_TO_CATEGORY.get(prod) == expected_cat, f"Mismatch for {prod}"


def test_technical_score_dictionary_and_orm_compatibility():
    dict_a = {"unit_of_measure": "EA", "manufacturer": "KITZ"}
    dict_b = {"unit_of_measure": "EA", "manufacturer": "KITZ Corp"}
    score = technical_score(dict_a, dict_b)
    assert score > 80.0


