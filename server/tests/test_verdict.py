from app.verdict import decide
from app.schemas import Authenticity, CompsSummary, Condition


def comps(**kw):
    base = dict(source="active_listings", raw_count=5, raw_low=60.0, raw_median=90.0,
                graded_count=0, graded_low=None, graded_median=None)
    base.update(kw)
    return CompsSummary(**base)


def cond(lo=6, hi=8):
    return Condition(observations=[], grade_low=lo, grade_high=hi)


def auth(risk, flags=None):
    return Authenticity(red_flags=flags if flags is not None else [], risk=risk)


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


# --- Authenticity gate ----------------------------------------------------

def test_high_risk_vetoes_undervalued():
    # The headline regression: a likely counterfeit must never read "UNDERVALUED",
    # even when the ask is far below the comp range.
    v = decide(comps(), cond(), 30.0, 0.9,
               authenticity=auth("high", ["print pattern looks off"]))
    assert v.verdict == "authenticity_risk"
    # Range stays as context ("if genuine...") but the label is a veto.
    assert v.value_low == 60.0 and v.value_high == 90.0
    assert "Counterfeit red flags" in v.reasoning
    assert "resolve authenticity" in v.reasoning


def test_high_risk_without_ask_still_flagged():
    v = decide(comps(), cond(), None, 0.9, authenticity=auth("high", ["fuzzy logo"]))
    assert v.verdict == "authenticity_risk"
    assert v.value_low == 60.0 and v.value_high == 90.0


def test_caution_keeps_label_but_annotates_reasoning():
    v = decide(comps(), cond(), 30.0, 0.9, authenticity=auth("caution", ["odd gloss"]))
    assert v.verdict == "undervalued"
    assert "authenticity flags" in v.reasoning


def test_low_risk_behaves_exactly_as_no_authenticity():
    with_low = decide(comps(), cond(), 30.0, 0.9, authenticity=auth("low"))
    without = decide(comps(), cond(), 30.0, 0.9)
    assert with_low == without
    assert without.verdict == "undervalued"


def test_authenticity_none_is_backward_compatible():
    v = decide(comps(), cond(), 75.0, 0.9)
    assert v.verdict == "fair"
    assert v.value_low == 60.0 and v.value_high == 90.0


def test_low_identity_confidence_beats_high_risk():
    # Gate order: unidentifiable card downgrades before any authenticity call.
    v = decide(comps(), cond(), 30.0, 0.4, authenticity=auth("high", ["x"]))
    assert v.verdict == "not_enough_data"


# --- Condition weighting ---------------------------------------------------

def test_heavy_wear_tightens_value_high_to_midpoint():
    v = decide(comps(), cond(lo=2, hi=4), None, 0.9)
    # midpoint of (raw_low 60, raw_median 90) = 75
    assert v.value_low == 60.0 and v.value_high == 75.0
    assert "Heavy wear" in v.reasoning


def test_heavy_wear_changes_the_label():
    # Old range: overpriced threshold 90 * 1.2 = 108 -> 95 would be "fair".
    # Heavy wear: value_high 75, threshold 75 * 1.2 = 90 -> 95 is overpriced.
    assert decide(comps(), cond(), 95.0, 0.9).verdict == "fair"
    assert decide(comps(), cond(lo=2, hi=4), 95.0, 0.9).verdict == "overpriced"


def test_grade_ceiling_above_heavy_wear_max_is_unweighted():
    v = decide(comps(), cond(lo=3, hi=4.5), None, 0.9)
    assert v.value_high == 90.0
    assert "Heavy wear" not in v.reasoning


# --- Stakes guardrails -----------------------------------------------------

def test_commodity_priced_card_is_low_value_regardless_of_ask():
    cheap = comps(raw_low=5.0, raw_median=8.0)
    # Ask that would be undervalued (1 <= 5*0.7) and one that would be
    # overpriced (50 >= 8*1.2) both collapse to low_value.
    for ask in (1.0, 50.0, None):
        v = decide(cheap, cond(), ask, 0.9)
        assert v.verdict == "low_value"
        assert v.value_low == 5.0 and v.value_high == 8.0
        assert "Commodity-priced" in v.reasoning


def test_median_exactly_at_low_value_floor_prices_normally():
    # strict <: a $10 median is not "too cheap to call"
    v = decide(comps(raw_low=6.0, raw_median=10.0), cond(), 8.0, 0.9)
    assert v.verdict == "fair"


def test_high_value_card_is_never_an_under_over_call():
    pricey = comps(raw_low=800.0, raw_median=1500.0)
    v = decide(pricey, cond(), 500.0, 0.9)  # 500 <= 800*0.7 would be "undervalued"
    assert v.verdict == "high_value"
    assert v.value_low == 800.0 and v.value_high == 1500.0
    assert "Professional authentication" in v.reasoning


def test_high_value_without_ask_still_flagged():
    v = decide(comps(raw_low=800.0, raw_median=1500.0), cond(), None, 0.9)
    assert v.verdict == "high_value"


def test_value_high_exactly_at_ceiling_prices_normally():
    # strict >: a $1000 value_high still gets a real call
    v = decide(comps(raw_low=500.0, raw_median=1000.0), cond(), 800.0, 0.9)
    assert v.verdict == "fair"


# --- Gate precedence ---------------------------------------------------------

def test_high_risk_beats_high_value():
    v = decide(comps(raw_low=800.0, raw_median=1500.0), cond(), 500.0, 0.9,
               authenticity=auth("high", ["x"]))
    assert v.verdict == "authenticity_risk"


def test_high_risk_beats_low_value():
    v = decide(comps(raw_low=5.0, raw_median=8.0), cond(), 1.0, 0.9,
               authenticity=auth("high", ["x"]))
    assert v.verdict == "authenticity_risk"


def test_thin_comps_beats_high_risk():
    # Without a comp range there is no "if genuine, $X–$Y" context to give.
    thin = comps(raw_count=1)
    v = decide(thin, cond(), 30.0, 0.9, authenticity=auth("high", ["x"]))
    assert v.verdict == "not_enough_data"


def test_heavy_wear_midpoint_feeds_high_value_gate():
    # value_high after weighting: (900 + 1300) / 2 = 1100 > 1000 -> still high_value
    v = decide(comps(raw_low=900.0, raw_median=1300.0), cond(lo=2, hi=4), None, 0.9)
    assert v.verdict == "high_value"
    assert v.value_high == 1100.0


def test_heavy_wear_midpoint_can_defuse_high_value_gate():
    # Unweighted value_high 1050 would trip the ceiling; midpoint (500+1050)/2 = 775
    # does not — the wear-adjusted range is what the stakes gate sees.
    v = decide(comps(raw_low=500.0, raw_median=1050.0), cond(lo=2, hi=4), None, 0.9)
    assert v.verdict == "no_ask"
    assert v.value_high == 775.0
