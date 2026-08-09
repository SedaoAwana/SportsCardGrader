from app.comps import summarize, is_graded
from app.schemas import CompListing

def L(title, price):
    return CompListing(title=title, price=price, graded=is_graded(title))

def test_is_graded_detects_companies():
    assert is_graded("2018 Prizm Luka Doncic PSA 10")
    assert is_graded("Luka RC BGS 9.5 GEM")
    assert is_graded("Luka Doncic Prizm TAG 9")
    assert not is_graded("2018 Prizm Luka Doncic RC #280")

def test_summarize_buckets_and_medians():
    listings = [L("Luka raw", 40), L("Luka raw RC", 60), L("Luka RC nice", 80),
                L("Luka PSA 10", 400), L("Luka PSA 9", 150)]
    s = summarize(listings, source="active_listings")
    assert (s.raw_count, s.raw_low, s.raw_median) == (3, 40, 60)
    assert (s.graded_count, s.graded_low) == (2, 150)

def test_summarize_empty():
    s = summarize([], source="active_listings")
    assert s.raw_count == 0 and s.raw_low is None
