from app.ai.pipeline import extract_attributes, normalize_description
from app.services.matching_engine import classify_match, validate_critical_attributes

def test_normalizes_valve_abbreviations():
    assert normalize_description('BALL VLV 2" SS-316 PN16') == 'BALL VALVE 2 INCH STAINLESS STEEL 316 PN16'

def test_extracts_normalized_valve_attributes():
    assert extract_attributes('BALL VLV 2" SS-316 PN16 FLG')['size'] == 'DN50'

def test_size_conflict_cannot_be_identical():
    score, failures = validate_critical_attributes({'product_type':'BALL_VALVE','size':'DN50'}, {'product_type':'BALL_VALVE','size':'DN100'})
    assert score == 0 and failures == ['size']
    assert classify_match(79.99) == 'FUNCTIONALLY_EQUIVALENT'
