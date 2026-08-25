from app.services.national_code_service import _segment

def test_code_segments_are_safe_and_deterministic():
    assert _segment('BALL_VALVE', 'ITEM') == 'BALLVALVE'
    assert _segment(None, 'NA') == 'NA'
