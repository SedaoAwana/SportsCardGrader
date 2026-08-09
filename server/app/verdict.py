"""Verdict engine: pure pricing decision from comps + condition.

v1 assumes the card in hand is raw, so the value range always comes from
the raw bucket; graded prices appear only as upside in the reasoning text.
"""
from typing import Optional

from app.schemas import CompsSummary, Condition, Verdict

MIN_CONFIDENCE = 0.5
MIN_COMPS = 3
UNDERVALUED_RATIO = 0.7
OVERPRICED_RATIO = 1.2


def decide(comps: CompsSummary, condition: Condition,
           asking_price: Optional[float], identity_confidence: float) -> Verdict:
    if identity_confidence < MIN_CONFIDENCE:
        return Verdict(
            verdict="not_enough_data",
            reasoning="Card identification confidence is too low to price reliably. "
                      "Try a clearer photo.",
        )
    # The value range is built from the raw bucket alone, so sufficiency must
    # come from raw comps — graded listings cannot rescue a thin raw bucket.
    if (comps.raw_count < MIN_COMPS
            or comps.raw_low is None or comps.raw_median is None):
        return Verdict(
            verdict="not_enough_data",
            reasoning="Too few comparable raw listings found to establish a value.",
        )

    value_low, value_high = comps.raw_low, comps.raw_median
    noun = "sold price" if comps.source == "sold" else "current asking price"
    src = noun if comps.raw_count == 1 else noun + "s"
    reasoning = (f"Raw copies range ${value_low:.0f}–${value_high:.0f} "
                 f"based on {comps.raw_count} {src}.")
    if condition.grade_high >= 8 and comps.graded_count and comps.graded_low:
        reasoning += (
            f" If it grades near the top of its "
            f"{condition.grade_low:g}–{condition.grade_high:g} range, "
            f"graded copies start around ${comps.graded_low:.0f}."
        )

    if asking_price is None:
        return Verdict(value_low=value_low, value_high=value_high,
                       verdict="no_ask", reasoning=reasoning)

    if asking_price <= value_low * UNDERVALUED_RATIO:
        label, tail = "undervalued", f" The ${asking_price:.0f} ask is well below the low end."
    elif asking_price >= value_high * OVERPRICED_RATIO:
        label, tail = "overpriced", f" The ${asking_price:.0f} ask is above the typical range."
    else:
        label, tail = "fair", f" The ${asking_price:.0f} ask sits within the typical range."
    return Verdict(value_low=value_low, value_high=value_high,
                   verdict=label, reasoning=reasoning + tail)
