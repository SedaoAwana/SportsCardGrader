from app.comps import summarize, is_graded, is_junk
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

# --- junk filter -------------------------------------------------------------

def test_is_junk_matches_obvious_junk():
    assert is_junk("Luka Doncic Prizm RC REPRINT")
    assert is_junk("Luka Doncic rookie RP mint")
    assert is_junk("Luka Doncic custom art card")
    assert is_junk("Luka Doncic novelty card")
    assert is_junk("Luka Doncic proxy")
    assert is_junk("Luka Doncic replica rookie")
    assert is_junk("Luka Doncic facsimile auto")
    assert is_junk("Luka Doncic ACEO rookie")
    assert is_junk("Luka Doncic digital card")
    assert is_junk("Luka Doncic lot of 10")
    assert is_junk("Luka Doncic rookie (lot)")
    assert is_junk("2018 Prizm basketball box BREAK Luka")
    assert is_junk("Luka Doncic you pick")
    assert is_junk("Luka Doncic u pick your card")
    assert is_junk("Luka Doncic choose your card")
    assert is_junk("Luka Doncic pick your player")
    assert is_junk("Luka Doncic rookie damaged corner")
    assert is_junk("Luka Doncic sticker card")
    assert is_junk("Luka Doncic decal")

def test_is_junk_word_boundary_safety():
    # "Lottery" must not trip \blot\b, "Sharp"-style substrings must not
    # trip \brp\b, and clean titles stay clean.
    assert not is_junk("Zach LaVine Lottery Pick insert")
    assert not is_junk("2018 Prizm Luka Doncic RC #280")
    assert not is_junk("Luka Doncic Prizm Rookie Sharp Corners")
    assert not is_junk("Luka Doncic Charlotte Hornets")   # "rlot" is not \blot\b

def test_is_junk_plural_forms():
    assert is_junk("Luka Doncic REPRINTS x3")
    assert is_junk("Luka Doncic replicas rookie")
    assert is_junk("Luka Doncic proxies")
    assert is_junk("Luka Doncic facsimiles auto")
    assert is_junk("Luka Doncic decals set")
    assert is_junk("Luka Doncic novelties")
    # "customs card" does NOT match \bcustom\b — accepted collateral of
    # keeping `custom` singular (see comment on _JUNK_PATTERNS).
    assert not is_junk("Luka Doncic customs card")

def test_summarize_drops_junk_from_both_buckets():
    listings = [L("Luka raw", 40), L("Luka raw RC", 60), L("Luka RC nice", 80),
                L("Luka Doncic REPRINT", 2.99),           # junk raw
                L("Luka Doncic lot of 10 PSA 9", 25),     # junk graded
                L("Luka PSA 10", 400), L("Luka PSA 9", 150)]
    s = summarize(listings, source="active_listings")
    assert (s.raw_count, s.raw_low, s.raw_median) == (3, 40, 60)
    assert (s.graded_count, s.graded_low) == (2, 150)

def test_summarize_keeps_lottery_title_raw():
    listings = [L("Zach LaVine Lottery Pick insert", 20),
                L("Zach LaVine base", 30), L("Zach LaVine RC", 40)]
    s = summarize(listings, source="active_listings")
    assert s.raw_count == 3 and s.raw_low == 20

# --- robust (trimmed) floor --------------------------------------------------

def test_raw_low_trims_outlier_with_ten_listings():
    # A $20 lowball (above the 30%-of-median flood guard, so the trim alone
    # must handle it) does not set the floor with 10 listings.
    prices = [20, 40, 42, 44, 46, 48, 50, 52, 54, 56]
    s = summarize([L(f"Luka raw #{i}", p) for i, p in enumerate(prices)],
                  source="active_listings")
    assert s.raw_count == 10
    assert s.raw_low == 40  # 10th-percentile (nearest-rank) value, not 20

def test_raw_low_extreme_outlier_hits_guard_then_trim():
    # A $0.99 listing is first dropped by the 30%-of-median guard, THEN the
    # percentile trim applies to the 9 survivors — floor is 42, never 0.99.
    prices = [0.99, 40, 42, 44, 46, 48, 50, 52, 54, 56]
    s = summarize([L(f"Luka raw #{i}", p) for i, p in enumerate(prices)],
                  source="active_listings")
    assert s.raw_low == 42

def test_raw_low_second_lowest_with_five_listings():
    prices = [20, 40, 45, 50, 55]   # 20 >= 0.3 * median(45): guard inactive
    s = summarize([L(f"Luka raw #{i}", p) for i, p in enumerate(prices)],
                  source="active_listings")
    assert s.raw_low == 40

def test_raw_low_min_with_three_listings():
    prices = [30, 40, 50]
    s = summarize([L(f"Luka raw #{i}", p) for i, p in enumerate(prices)],
                  source="active_listings")
    assert s.raw_low == 30

def test_raw_low_resists_cheap_junk_flood():
    # Five clean-titled $0.99 auctions (fresh listings) outnumber the trim:
    # the floor must come from the >= 30%-of-median population, not $0.99.
    prices = [0.99, 0.99, 0.99, 0.99, 0.99, 55, 58, 60, 62, 65]
    s = summarize([L(f"Luka raw #{i}", p) for i, p in enumerate(prices)],
                  source="active_listings")
    assert s.raw_count == 10
    assert s.raw_low == 58  # second-lowest of the 5 floor candidates >= 0.3*median

def test_graded_low_resists_cheap_junk_flood():
    prices = [9.99, 9.99, 9.99, 9.99, 9.99, 150, 160, 170, 180, 190]
    s = summarize([L(f"Luka PSA 10 #{i}", p) for i, p in enumerate(prices)],
                  source="active_listings")
    assert s.graded_low == 160

def test_raw_low_single_listing_falls_back_to_min():
    s = summarize([L("Luka raw", 45)], source="active_listings")
    assert s.raw_low == 45  # < 2 floor candidates -> whole bucket

def test_graded_low_uses_same_trimmed_floor():
    prices = [50, 150, 160, 170, 180]   # 50 >= 0.3 * median(160): guard inactive
    s = summarize([L(f"Luka PSA 10 #{i}", p) for i, p in enumerate(prices)],
                  source="active_listings")
    assert s.graded_count == 5
    assert s.graded_low == 150  # second-lowest for 4-7 listings
