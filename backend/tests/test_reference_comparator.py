from app.services.reference_comparator import compare_references

def test_exact_match():
    # "INV-12345" vs "INV-12345" -> True
    assert compare_references("INV-12345", "INV-12345").is_exact_match is True

def test_case_and_whitespace_differences():
    # " INV-12345 " vs "inv-12345" -> True
    assert compare_references(" INV-12345 ", "inv-12345").is_exact_match is True

def test_different_lengths_do_not_match():
    # "INV-12345" vs "INV-123456" -> False
    assert compare_references("INV-12345", "INV-123456").is_exact_match is False

def test_substrings_do_not_match():
    # "INV-12345" vs "12345" -> False
    assert compare_references("INV-12345", "12345").is_exact_match is False

def test_none_values():
    # None vs "INV-12345" -> False
    assert compare_references(None, "INV-12345").is_exact_match is False
    assert compare_references("INV-12345", None).is_exact_match is False
    # None vs None -> False
    assert compare_references(None, None).is_exact_match is False

def test_blank_values():
    assert compare_references("   ", "INV-12345").is_exact_match is False
    assert compare_references("INV-12345", "   ").is_exact_match is False
    assert compare_references("   ", "   ").is_exact_match is False
    assert compare_references("", "").is_exact_match is False

def test_internal_characters_are_preserved():
    # The comparator must not remove internal spaces or punctuation
    assert compare_references("INV-12345", "INV 12345").is_exact_match is False
    assert compare_references("INV-12345", "INV_12345").is_exact_match is False
