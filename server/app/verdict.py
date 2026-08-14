"""Verdict engine: pure pricing decision from comps + condition + authenticity.

v1 assumes the card in hand is raw, so the value range always comes from
the raw bucket; graded prices appear only as upside in the reasoning text.

Gate order (each returns early):
  1. identity confidence          -> not_enough_data
  2. raw-comp sufficiency         -> not_enough_data
  3. authenticity veto (high)     -> authenticity_risk (range kept as context)
  4. condition weighting          -> heavy wear tightens value_high (no early return)
  5. caution caveat               -> reasoning note only (no early return; sits
                                     before the stakes gates so their early
                                     returns still carry the note)
  6. low-stakes guardrail         -> low_value  (commodity-priced card)
  7. high-stakes guardrail        -> high_value (authentication territory)
  8. ask comparison               -> undervalued / fair / overpriced / no_ask
"""
from typing import Optional

from app.schemas import Authenticity, CompsSummary, Condition, Slab, Verdict

MIN_CONFIDENCE = 0.5
MIN_COMPS = 3
UNDERVALUED_RATIO = 0.7
OVERPRICED_RATIO = 1.2
# Grade ceiling at or below which the card trades near the raw floor.
HEAVY_WEAR_MAX = 4.0
# Below this raw median, under/over calls are noise (shipping dominates).
LOW_VALUE_FLOOR = 10.0
# Above this value_high, no call without professional authentication/grading.
HIGH_VALUE_CEILING = 1000.0


def decide(comps: CompsSummary, condition: Condition,
           asking_price: Optional[float], identity_confidence: float,
           authenticity: Optional[Authenticity] = None) -> Verdict:
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

    # Authenticity veto: a likely counterfeit never gets a price call. The
    # range stays populated purely as context for the "if genuine" framing.
    if authenticity is not None and authenticity.risk == "high":
        return Verdict(
            value_low=value_low, value_high=value_high,
            verdict="authenticity_risk",
            reasoning="Counterfeit red flags detected — resolve authenticity "
                      "before trusting any price. If genuine, comparable raw "
                      f"copies range ${value_low:.0f}–${value_high:.0f}.",
        )

    # Condition weighting: heavy-wear copies trade near the floor, so the top
    # of the range collapses to the midpoint of (floor, median).
    heavy_wear = condition.grade_high <= HEAVY_WEAR_MAX
    if heavy_wear:
        value_high = (value_low + comps.raw_median) / 2

    noun = "sold price" if comps.source == "sold" else "current asking price"
    src = noun if comps.raw_count == 1 else noun + "s"
    reasoning = (f"Raw copies range ${value_low:.0f}–${value_high:.0f} "
                 f"based on {comps.raw_count} {src}.")
    if heavy_wear:
        reasoning += " Heavy wear — priced toward the low end of raw comps."
    elif condition.grade_high >= 8 and comps.graded_count and comps.graded_low:
        reasoning += (
            f" If it grades near the top of its "
            f"{condition.grade_low:g}–{condition.grade_high:g} range, "
            f"graded copies start around ${comps.graded_low:.0f}."
        )

    # Appended before the stakes gates so every priced verdict — including
    # low_value/high_value early returns — carries the caveat.
    if authenticity is not None and authenticity.risk == "caution":
        reasoning += (" Note: minor authenticity flags were spotted — "
                      "inspect closely.")

    # Stakes guardrails: at the extremes an under/fair/over call is either
    # meaningless (commodity cards) or irresponsible (authentication territory).
    if comps.raw_median < LOW_VALUE_FLOOR:
        return Verdict(
            value_low=value_low, value_high=value_high,
            verdict="low_value",
            reasoning=reasoning + " Commodity-priced card — shipping and small "
                      "condition differences dominate at this price; an "
                      "under/over call isn't meaningful.",
        )
    if value_high > HIGH_VALUE_CEILING:
        return Verdict(
            value_low=value_low, value_high=value_high,
            verdict="high_value",
            reasoning=reasoning + " High-value card — estimate only. Professional "
                      "authentication and grading are strongly recommended "
                      "before any transaction at this level.",
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


def decide_slab(matching: Optional[CompsSummary], overall: CompsSummary,
                slab: Slab, asking_price: Optional[float],
                identity_confidence: float,
                authenticity: Optional[Authenticity] = None) -> Verdict:
    """Verdict for a professionally graded (slabbed) card.

    Kept separate from decide() so the raw path stays untouched: a slab has no
    condition estimate (the label already graded it) and prices from graded
    comps, so the gates differ:

      1. identity confidence            -> not_enough_data
      2. graded-comp sufficiency        -> range from same-grade comps when
                                           `matching` exists, else all graded
                                           comps as a mixed-grade estimate,
                                           else not_enough_data
      3. authenticity veto (high)       -> authenticity_risk — a fake slab is
                                           the whole con, so the veto points at
                                           the label and hologram
      4. caution caveat                 -> reasoning note only
      5. high-stakes guardrail          -> high_value
         (no low-value guardrail: slabs are rarely sub-$10 — grading alone
          costs more than that, so a sub-$10 slab range is comp noise, not a
          commodity card; an under/over call is still worth making)
      6. ask comparison                 -> undervalued / fair / overpriced / no_ask
    """
    if identity_confidence < MIN_CONFIDENCE:
        return Verdict(
            verdict="not_enough_data",
            reasoning="Card identification confidence is too low to price reliably. "
                      "Try a clearer photo.",
        )

    grade_label = f"{slab.company} {slab.grade}"
    if (matching is not None and matching.graded_count >= MIN_COMPS
            and matching.graded_low is not None
            and matching.graded_median is not None):
        value_low, value_high = matching.graded_low, matching.graded_median
        reasoning = (f"{grade_label} copies range ${value_low:.0f}–${value_high:.0f} "
                     f"based on {matching.graded_count} listings.")
    elif (overall.graded_count >= MIN_COMPS
            and overall.graded_low is not None
            and overall.graded_median is not None):
        value_low, value_high = overall.graded_low, overall.graded_median
        reasoning = (f"Graded copies (mixed grades) range "
                     f"${value_low:.0f}–${value_high:.0f} — "
                     f"few {grade_label} comps found.")
    else:
        return Verdict(
            verdict="not_enough_data",
            reasoning="Too few graded listings found to establish a value for "
                      "this slab.",
        )

    if authenticity is not None and authenticity.risk == "high":
        return Verdict(
            value_low=value_low, value_high=value_high,
            verdict="authenticity_risk",
            reasoning="Counterfeit red flags detected (check slab label and "
                      "hologram) — resolve authenticity before trusting any "
                      "price. If genuine, comparable copies range "
                      f"${value_low:.0f}–${value_high:.0f}.",
        )

    if authenticity is not None and authenticity.risk == "caution":
        reasoning += (" Note: minor authenticity flags were spotted — "
                      "inspect closely.")

    if value_high > HIGH_VALUE_CEILING:
        return Verdict(
            value_low=value_low, value_high=value_high,
            verdict="high_value",
            reasoning=reasoning + " High-value card — estimate only. Verify the "
                      "slab (cert number lookup with the grading company) "
                      "before any transaction at this level.",
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
