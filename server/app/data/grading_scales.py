"""Grading-scale reference data (PSA and TAG).

``PSA_SCALE``: official PSA grading scale (grades 1-10) with labels,
descriptions, and front/back centering tolerances. Carried over verbatim
from the legacy ``sports_card_grader/grading_system.py``
(``GradingSystem.GRADE_SCALE``), minus the ``min`` scoring thresholds that
belonged to the deleted scorer.

``TAG_SCALE`` / ``TAG_CATEGORIES``: TAG grading scale (19 grades, each
scored out of 1000 points) and its four evaluation areas, per the TAG
rubric at https://taggrading.com/pages/rubric.

Used to ground the vision prompt and UI copy.
"""

PSA_SCALE: dict = {
    "10": {
        "label": "Gem Mint",
        "description": "A PSA Gem Mint 10 card is a virtually perfect card. Attributes include four perfectly sharp corners, sharp focus and full original gloss. Must be free of staining of any kind, but an allowance may be made for a slight printing imperfection, if it doesn't impair the overall appeal. Image must be centered within a tolerance not to exceed approximately 55/45 percent on the front, and 75/25 percent on the reverse.",
        "centering_tolerance": {"front": 55, "back": 75}
    },
    "9": {
        "label": "Mint",
        "description": "A PSA Mint 9 is a superb condition card that exhibits only one of the following minor flaws: a very slight wax stain on reverse, a minor printing imperfection or slightly off white borders. Centering must be approximately 60/40 or better on the front and 90/10 or better on the reverse.",
        "centering_tolerance": {"front": 60, "back": 90}
    },
    "8": {
        "label": "Near Mint-Mint",
        "description": "A PSA NM-MT 8 is a super high-end card that appears Mint 9 at first glance, but upon closer inspection, can exhibit: a very slight wax stain on reverse, slightest fraying at one or two corners, a minor printing imperfection, and/or slightly off-white borders. Centering must be approximately 65/35 or better on the front and 90/10 or better on the reverse.",
        "centering_tolerance": {"front": 65, "back": 90}
    },
    "7": {
        "label": "Near Mint",
        "description": "A PSA NM 7 is a card with just a slight surface wear visible upon close inspection. There may be slight fraying on some corners. Picture focus may be slightly out-of register. A minor printing blemish is acceptable. Slight wax staining is acceptable on the back only. Most original gloss is retained. Centering must be approximately 70/30 or better on the front and 90/10 or better on the back.",
        "centering_tolerance": {"front": 70, "back": 90}
    },
    "6": {
        "label": "Excellent-Near Mint",
        "description": "A PSA 6 card may have visible surface wear or a printing defect which does not detract from its overall appeal. A very light scratch may be detected only upon close inspection. Corners may have slightly graduated fraying. Picture focus may be slightly out-of-register. May show some loss of original gloss, minor wax stain on reverse, very slight notching on edges and some off-whiteness on borders. Centering must be 80/20 or better on the front and 90/10 or better on the reverse.",
        "centering_tolerance": {"front": 80, "back": 90}
    },
    "5": {
        "label": "Excellent",
        "description": "On PSA 5 cards, very minor rounding of the corners is becoming evident. Surface wear or printing defects are more visible. There may be minor chipping on edges. Loss of original gloss will be more apparent. Focus of picture may be slightly out-of-register. Several light scratches may be visible upon close inspection, but do not detract from the appeal. May show some off-whiteness of borders. Centering must be 85/15 or better on the front and 90/10 or better on the back.",
        "centering_tolerance": {"front": 85, "back": 90}
    },
    "4": {
        "label": "Very Good-Excellent",
        "description": "Shows moderate corner wear and surface wear. Minor creases may be present.",
        "centering_tolerance": {"front": 90, "back": 90}
    },
    "3": {
        "label": "Very Good",
        "description": "Shows significant wear with rounded corners and surface defects.",
        "centering_tolerance": {"front": 90, "back": 90}
    },
    "2": {
        "label": "Good",
        "description": "Heavy wear with major surface damage and corner rounding.",
        "centering_tolerance": {"front": 90, "back": 90}
    },
    "1": {
        "label": "Poor",
        "description": "Severe damage affecting card integrity and appeal.",
        "centering_tolerance": {"front": 90, "back": 90}
    }
}

TAG_SCALE: dict = {
    "10P": {"label": "TAG Pristine", "score_range": (990, 1000)},
    "10": {"label": "Gem Mint", "score_range": (950, 989)},
    "9": {"label": "Mint", "score_range": (900, 949)},
    "8.5": {"label": "Near Mint - Mint+", "score_range": (850, 899)},
    "8": {"label": "Near Mint - Mint", "score_range": (800, 849)},
    "7.5": {"label": "Near Mint+", "score_range": (750, 799)},
    "7": {"label": "Near Mint", "score_range": (700, 749)},
    "6.5": {"label": "Excellent - Mint+", "score_range": (650, 699)},
    "6": {"label": "Excellent - Mint", "score_range": (600, 649)},
    "5.5": {"label": "Excellent+", "score_range": (550, 599)},
    "5": {"label": "Excellent", "score_range": (500, 549)},
    "4.5": {"label": "Very Good - Excellent+", "score_range": (450, 499)},
    "4": {"label": "Very Good - Excellent", "score_range": (400, 449)},
    "3.5": {"label": "Very Good+", "score_range": (350, 399)},
    "3": {"label": "Very Good", "score_range": (300, 349)},
    "2.5": {"label": "Good+", "score_range": (250, 299)},
    "2": {"label": "Good", "score_range": (200, 249)},
    "1.5": {"label": "Fair", "score_range": (150, 199)},
    "1": {"label": "Poor", "score_range": (100, 149)}
}

TAG_CATEGORIES: dict = {
    "centering": "Image placement relative to card borders; tolerance tightens at higher grades (51/49 at Pristine down to 98.33/1.67 at Fair).",
    "corners": "Wear progression from virtually flawless at top grades to misshaped with portions fallen off at lowest.",
    "surface": "Defects including scratches, wrinkles, creases, stains, water damage, and gloss loss — flawless at top, significantly impaired at bottom.",
    "edges": "From virtually flawless through fray artifacts, chipping, notching, lifting, and roughness to larger tears."
}
