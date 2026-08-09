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

def is_graded(title: str) -> bool:
    return bool(_GRADED_RE.search(title))

def summarize(listings: list[CompListing], source: str) -> CompsSummary:
    raw = sorted(l.price for l in listings if not l.graded)
    graded = sorted(l.price for l in listings if l.graded)
    return CompsSummary(
        source=source,
        raw_count=len(raw),
        raw_low=raw[0] if raw else None,
        raw_median=statistics.median(raw) if raw else None,
        graded_count=len(graded),
        graded_low=graded[0] if graded else None,
        graded_median=statistics.median(graded) if graded else None,
    )
