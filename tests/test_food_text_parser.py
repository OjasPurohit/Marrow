"""Deterministic NL parser samples (M4)."""

from marrow.services.food_text_parser import (
    parse_quantity_token,
    parse_segment,
    split_log_segments,
)


def test_parse_quantity_fractions_and_words():
    assert parse_quantity_token("1/2") == 0.5
    assert parse_quantity_token("1 1/2") == 1.5
    assert parse_quantity_token("2 and a half") == 2.5
    assert parse_quantity_token("do") == 2
    assert parse_quantity_token("aadha") == 0.5


def test_split_segments_preserves_compound_amounts():
    parts = split_log_segments("2 and a half roti, 1 katori dal")
    assert len(parts) == 2
    assert "2.5 roti" in parts[0] or "roti" in parts[0]


def test_parse_segment_hinglish():
    seg = parse_segment("2 roti")
    assert seg.amount == 2
    assert seg.unit == "roti"
    assert "chapati" in seg.food_query.lower()

    seg2 = parse_segment("1/2 katori dal")
    assert seg2.amount == 0.5
    assert seg2.unit == "katori"
    assert "dal" in seg2.food_query.lower()

    seg3 = parse_segment("do idli")
    assert seg3.amount == 2
    assert "idli" in seg3.food_query.lower()
