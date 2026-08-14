import math
import re
import statistics

from app.schemas import CompListing, CompsSummary

# Company name, optionally followed by a bounded allowlist of condition words
# ("PSA GEM MINT 10", "BGS Gem Mint 9.5"), then the grade. Arbitrary words must
# NOT bridge the gap — "Vintage PSA card lot of 10" is not a graded listing.
_GRADED_RE = re.compile(
    r"\b(PSA|BGS|SGC|CGC|TAG)"
    r"(?:\s+(?:GEM|MINT|MT|GM|PRISTINE|AUTHENTIC))*"
    r"\s*\.?\s*(10|[1-9](?:\.5)?)\b",
    re.I,
)

# Titles that indicate the listing is not a single authentic copy of the card:
# reprints/customs, multi-card lots, box breaks, pick-your-card menus, damaged
# copies, stickers. Matched case-insensitively with word boundaries so player
# and team names ("Lottery Pick", "Charlotte") never trip the filter.
# Only unambiguous nouns are pluralized; `lot`, `custom`, `sticker`, `break`
# stay singular because their plurals have legitimate uses ("customs card",
# "breaks records") — so "customs" passing through is accepted collateral.
# Contributions welcome — keep additions conservative: a false positive here
# silently drops a real comp and skews the value range.
_JUNK_PATTERNS = (
    r"\breprints?\b",
    r"\brp\b",         # dropping the odd "RP" relief-pitcher title is the
                       # deliberate fail-safe direction (junk in raw is worse)
    r"\bcustom\b",
    r"\bnovelt(?:y|ies)\b",
    r"\bprox(?:y|ies)\b",
    r"\breplicas?\b",
    r"\bfacsimiles?\b",
    r"\bart\s+card\b",
    r"\baceo\b",
    r"\bdigital\b",
    r"\blot\b",        # covers "lot of 10", "(lot)"; \b keeps "Lottery" safe
    r"\bbreak\b",
    r"\byou\s+pick\b",
    r"\bu\s+pick\b",
    r"\bchoose\b",
    r"\bpick\s+your\b",
    r"\bdamaged\b",
    r"\bsticker\b",
    r"\bdecals?\b",
)
_JUNK_RE = re.compile("|".join(_JUNK_PATTERNS), re.I)


def is_graded(title: str) -> bool:
    return bool(_GRADED_RE.search(title))


def is_junk(title: str) -> bool:
    """True when the title marks a listing that must not price this card."""
    return bool(_JUNK_RE.search(title))


def _robust_low(prices: list[float]) -> float | None:
    """Trimmed floor for a sorted price list — the 'low' a buyer can trust.

    A single mispriced or junk listing must never set the value floor, so:
      - 8+ prices: 10th percentile by nearest-rank, clamped to at least the
        second-lowest so one outlier can never be the floor;
      - 4-7 prices: second-lowest;
      - 1-3 prices: minimum (too few points to trim anything).
    """
    if not prices:
        return None
    n = len(prices)
    if n >= 8:
        rank = max(2, math.ceil(0.10 * n))
        return prices[rank - 1]
    if n >= 4:
        return prices[1]
    return prices[0]


def _floor(bucket: list[float]) -> float | None:
    """Value floor for a sorted price bucket, resistant to cheap-junk floods.

    The percentile trim in _robust_low is defeated when >= ~10% of the bucket
    is clean-titled cheap junk (fresh $0.99 auctions are exactly this), so the
    floor is computed from prices at or above 30% of the bucket median. If
    that leaves fewer than 2 candidates (only possible for tiny buckets), fall
    back to the whole bucket.
    """
    if not bucket:
        return None
    candidates = [p for p in bucket if p >= 0.3 * statistics.median(bucket)]
    if len(candidates) < 2:
        candidates = bucket
    return _robust_low(candidates)


def _clamp_to_median(low: float | None, median: float | None) -> float | None:
    """A robust low above its own median is a floor artifact, not a floor."""
    if low is None or median is None:
        return low
    return min(low, median)


def summarize(listings: list[CompListing], source: str) -> CompsSummary:
    # Junk is dropped before bucketing so counts, lows, and medians all
    # reflect only plausible comps (a graded lot is junk too).
    kept = [l for l in listings if not is_junk(l.title)]
    raw = sorted(l.price for l in kept if not l.graded)
    graded = sorted(l.price for l in kept if l.graded)
    # *_low fields are robust lows (trimmed floors), not absolute minimums.
    # In bimodal buckets (half junk-cheap, half real) the 30%-of-median flood
    # guard can push the floor above a median that straddles both modes, so
    # each low is clamped to its median — a range must never read $50–$26.
    raw_low = _clamp_to_median(_floor(raw), statistics.median(raw) if raw else None)
    graded_low = _clamp_to_median(_floor(graded),
                                  statistics.median(graded) if graded else None)
    return CompsSummary(
        source=source,
        raw_count=len(raw),
        raw_low=raw_low,
        raw_median=statistics.median(raw) if raw else None,
        graded_count=len(graded),
        graded_low=graded_low,
        graded_median=statistics.median(graded) if graded else None,
    )
