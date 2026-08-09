import re
import statistics

from app.schemas import CompListing, CompsSummary

_GRADED_RE = re.compile(r"\b(PSA|BGS|SGC|CGC|TAG)\s*\.?\s*(10|[1-9](?:\.5)?)\b", re.I)

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
