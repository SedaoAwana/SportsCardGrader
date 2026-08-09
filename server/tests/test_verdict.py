from app.verdict import decide
from app.schemas import CompsSummary, Condition


def comps(**kw):
    base = dict(source="active_listings", raw_count=5, raw_low=60.0, raw_median=90.0,
                graded_count=0, graded_low=None, graded_median=None)
    base.update(kw)
    return CompsSummary(**base)


def cond(lo=6, hi=8):
    return Condition(observations=[], grade_low=lo, grade_high=hi)


def test_undervalued():
    v = decide(comps(), cond(), asking_price=30.0, identity_confidence=0.9)
    assert v.verdict == "undervalued"
    assert v.value_low == 60.0 and v.value_high == 90.0


def test_fair():
    assert decide(comps(), cond(), 75.0, 0.9).verdict == "fair"


def test_overpriced():
    assert decide(comps(), cond(), 150.0, 0.9).verdict == "overpriced"


def test_no_ask_returns_value_only():
    v = decide(comps(), cond(), None, 0.9)
    assert v.verdict == "no_ask" and v.value_low == 60.0


def test_low_identity_confidence_downgrades():
    assert decide(comps(), cond(), 30.0, 0.4).verdict == "not_enough_data"


def test_thin_comps_downgrades():
    thin = comps(raw_count=1, graded_count=1)
    assert decide(thin, cond(), 30.0, 0.9).verdict == "not_enough_data"


def test_graded_upside_mentioned_when_high_grade_possible():
    c = comps(graded_count=3, graded_low=150.0, graded_median=400.0)
    v = decide(c, cond(lo=8, hi=9), 30.0, 0.9)
    assert "graded" in v.reasoning.lower()


# --- Boundary tests -------------------------------------------------------

def test_ask_exactly_at_undervalued_boundary():
    # value_low * 0.7 = 42.0 — <= is undervalued
    assert decide(comps(), cond(), 42.0, 0.9).verdict == "undervalued"


def test_ask_exactly_at_overpriced_boundary():
    # value_high * 1.2 = 108.0 — >= is overpriced
    assert decide(comps(), cond(), 108.0, 0.9).verdict == "overpriced"


def test_ask_just_inside_boundaries_is_fair():
    assert decide(comps(), cond(), 42.01, 0.9).verdict == "fair"
    assert decide(comps(), cond(), 107.99, 0.9).verdict == "fair"


def test_thin_raw_bucket_not_rescued_by_graded_comps():
    # value range is built from the raw bucket only, so graded comps must not
    # satisfy the sufficiency gate: 2 raw asks are not enough to price a card
    thin_raw = comps(raw_count=2, graded_count=5, graded_low=100.0, graded_median=200.0)
    assert decide(thin_raw, cond(), 30.0, 0.9).verdict == "not_enough_data"


def test_exactly_min_raw_comps_prices_normally():
    assert decide(comps(raw_count=3), cond(), 75.0, 0.9).verdict == "fair"


def test_no_raw_comps_even_with_graded_is_not_enough_data():
    # v1 prices raw cards only; graded comps alone cannot establish a raw value
    c = comps(raw_count=0, raw_low=None, raw_median=None,
              graded_count=5, graded_low=100.0, graded_median=200.0)
    assert decide(c, cond(), 30.0, 0.9).verdict == "not_enough_data"


def test_missing_raw_median_is_not_enough_data():
    # defensive: a partially-populated raw bucket must not crash or price
    c = comps(raw_count=5, raw_low=60.0, raw_median=None, graded_count=0)
    assert decide(c, cond(), 30.0, 0.9).verdict == "not_enough_data"


def test_confidence_exactly_at_threshold_passes():
    # < is strict: 0.5 exactly should NOT downgrade
    assert decide(comps(), cond(), 75.0, 0.5).verdict == "fair"


def test_no_graded_mention_when_grade_ceiling_below_8():
    c = comps(graded_count=3, graded_low=150.0, graded_median=400.0)
    v = decide(c, cond(lo=5, hi=7.5), 75.0, 0.9)
    assert "graded" not in v.reasoning.lower()


def test_sold_source_reasoning():
    v = decide(comps(source="sold"), cond(), 75.0, 0.9)
    assert "sold prices" in v.reasoning


def test_comp_count_pluralized_in_reasoning():
    v = decide(comps(raw_count=5), cond(), 75.0, 0.9)
    assert "5 current asking prices" in v.reasoning


def test_half_grades_render_in_reasoning():
    c = comps(graded_count=3, graded_low=150.0, graded_median=400.0)
    v = decide(c, cond(lo=6.5, hi=8.5), 30.0, 0.9)
    assert "6.5" in v.reasoning and "8.5" in v.reasoning
