import pytest
from pydantic import ValidationError
from app.schemas import Identity, Condition, VisionResult, Verdict

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
