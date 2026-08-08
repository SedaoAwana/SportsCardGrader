from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

class Identity(BaseModel):
    player: str
    year: str
    set_name: str
    card_number: Optional[str] = None
    variant: Optional[str] = None
    search_string: str
    confidence: float = Field(ge=0, le=1)

class AreaObservation(BaseModel):
    area: Literal["corners", "edges", "surface", "centering"]
    severity: Literal["none", "minor", "moderate", "heavy"]
    note: str

class Condition(BaseModel):
    observations: list[AreaObservation]
    grade_low: int = Field(ge=1, le=10)
    grade_high: int = Field(ge=1, le=10)

    @model_validator(mode="after")
    def range_ordered(self):
        if self.grade_low > self.grade_high:
            raise ValueError("grade_low must be <= grade_high")
        return self

class Authenticity(BaseModel):
    red_flags: list[str]
    risk: Literal["low", "caution", "high"]

class VisionResult(BaseModel):
    photo_ok: bool
    photo_issue: Optional[str] = None
    identity: Optional[Identity] = None
    condition: Optional[Condition] = None
    authenticity: Optional[Authenticity] = None
    ai_value_note: Optional[str] = None  # model's rough value memory; fallback when comps are empty

class CompListing(BaseModel):
    title: str
    price: float
    graded: bool
    grade_label: Optional[str] = None
    url: Optional[str] = None

class CompsSummary(BaseModel):
    source: Literal["active_listings", "sold"]
    raw_count: int
    raw_low: Optional[float] = None
    raw_median: Optional[float] = None
    graded_count: int
    graded_low: Optional[float] = None
    graded_median: Optional[float] = None

class Verdict(BaseModel):
    value_low: Optional[float] = None
    value_high: Optional[float] = None
    verdict: Literal["undervalued", "fair", "overpriced", "no_ask", "not_enough_data"]
    reasoning: str

class ScanResponse(BaseModel):
    vision: VisionResult
    comps: Optional[CompsSummary] = None
    comps_error: Optional[str] = None
    verdict: Optional[Verdict] = None
