from app.data.grading_scales import PSA_SCALE, TAG_CATEGORIES, TAG_SCALE

EXPECTED_TAG_GRADES = [
    "10P", "10", "9", "8.5", "8", "7.5", "7", "6.5", "6", "5.5",
    "5", "4.5", "4", "3.5", "3", "2.5", "2", "1.5", "1",
]


def test_psa_scale_has_ten_grades():
    assert set(PSA_SCALE) == {str(n) for n in range(1, 11)}


def test_psa_grade_entries_complete():
    for grade, entry in PSA_SCALE.items():
        assert entry["label"]
        assert entry["description"]


def test_tag_scale_has_expected_grades():
    assert list(TAG_SCALE) == EXPECTED_TAG_GRADES


def test_tag_grade_entries_complete():
    for grade, entry in TAG_SCALE.items():
        assert entry["label"]
        assert entry["score_range"]


def test_tag_score_ranges_contiguous_descending():
    ranges = [entry["score_range"] for entry in TAG_SCALE.values()]
    for low, high in ranges:
        assert 100 <= low <= high <= 1000
    for (prev_low, _), (_, next_high) in zip(ranges, ranges[1:]):
        assert next_high == prev_low - 1


def test_tag_categories():
    assert set(TAG_CATEGORIES) == {"centering", "corners", "surface", "edges"}
    for text in TAG_CATEGORIES.values():
        assert text
