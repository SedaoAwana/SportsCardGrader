import pytest
from pydantic import ValidationError
from app.schemas import Identity, Condition, VisionResult, Verdict, CompListing

def test_identity_confidence_bounds():
    with pytest.raises(ValidationError):
        Identity(player="Luka Doncic", year="2018", set_name="Prizm",
                 search_string="x", confidence=1.5)

def test_condition_rejects_inverted_range():
    with pytest.raises(ValidationError):
        Condition(observations=[], grade_low=8, grade_high=6)

def test_vision_result_photo_rejected_needs_no_identity():
    r = VisionResult(photo_ok=False, photo_issue="too blurry")
    assert r.identity is None

def test_condition_accepts_half_grades():
    c = Condition(observations=[], grade_low=6.5, grade_high=8.5)
    assert c.grade_low == 6.5
    assert c.grade_high == 8.5

def test_comp_listing_rejects_negative_price():
    with pytest.raises(ValidationError):
        CompListing(title="Luka Doncic Prizm", price=-1, graded=False)

def test_vision_result_photo_not_ok_fills_default_issue():
    r = VisionResult(photo_ok=False)
    assert isinstance(r.photo_issue, str)
    assert r.photo_issue
