from app.comps import summarize, is_graded
from app.schemas import CompListing

def L(title, price):
    return CompListing(title=title, price=price, graded=is_graded(title))

def test_is_graded_detects_companies():
    assert is_graded("2018 Prizm Luka Doncic PSA 10")
    assert is_graded("Luka RC BGS 9.5 GEM")
    assert is_graded("Luka Doncic Prizm TAG 9")
    assert not is_graded("2018 Prizm Luka Doncic RC #280")

def test_is_graded_allows_condition_words_between_company_and_grade():
    assert is_graded("PSA GEM MINT 10")
    assert is_graded("SGC Mint 9")
    assert is_graded("BGS Gem Mint 9.5")

def test_is_graded_rejects_arbitrary_words_between_company_and_number():
    assert not is_graded("Vintage card lot of 10")
    assert not is_graded("Vintage PSA card lot of 10")

def test_is_graded_hopeful_titles_go_to_graded_bucket():
    # a "PSA GEM MINT 10?" hopeful raw listing landing in the graded bucket
    # is the benign direction (keeps slab-ish prices out of raw_median)
    assert is_graded("PSA GEM MINT 10?")

def test_summarize_buckets_and_medians():
    listings = [L("Luka raw", 40), L("Luka raw RC", 60), L("Luka RC nice", 80),
                L("Luka PSA 10", 400), L("Luka PSA 9", 150)]
    s = summarize(listings, source="active_listings")
    assert (s.raw_count, s.raw_low, s.raw_median) == (3, 40, 60)
    assert (s.graded_count, s.graded_low) == (2, 150)

def test_summarize_empty():
    s = summarize([], source="active_listings")
    assert s.raw_count == 0 and s.raw_low is None
