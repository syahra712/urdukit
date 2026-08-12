"""Gold-standard Urdu -> Roman Urdu pairs for measuring accuracy.

Split deliberately into two sets so the headline number cannot be inflated
by simply growing the lexicon:

``IN_LEXICON``
    Words present in :data:`urdukit.transliteration.LEXICON`. Accuracy here
    should be 100% -- anything less is a lookup bug.

``HELD_OUT``
    Words deliberately *absent* from the lexicon. Accuracy here measures the
    rule-based fallback alone, which is the number that actually matters and
    the number that is honest to publish.

Romanizations follow everyday Pakistani Roman Urdu, not scholarly ALA-LC.
Where usage genuinely varies (``nahi``/``nahin``), the most common spelling
is used.
"""

#: Words that are in the lexicon. Exact match expected.
IN_LEXICON: dict[str, str] = {
    "میں": "mein",
    "پاکستان": "pakistan",
    "کتاب": "kitab",
    "محبت": "mohabbat",
    "دوست": "dost",
    "شکریہ": "shukriya",
    "زندگی": "zindagi",
    "اردو": "urdu",
    "کراچی": "karachi",
    "لاہور": "lahore",
    "پانی": "pani",
    "گھر": "ghar",
    "لڑکی": "larki",
    "آدمی": "aadmi",
    "وقت": "waqt",
}

#: Words NOT in the lexicon. Measures the rule-based fallback honestly.
HELD_OUT: dict[str, str] = {
    # --- words the rules get right ------------------------------------
    "پہاڑ": "pahaar",
    "کمال": "kamaal",
    "سلامت": "salamat",
    "درد": "dard",
    "برف": "barf",
    "شام": "shaam",
    "خبر": "khabar",
    "قلم": "qalam",
    "نظر": "nazar",
    # --- words the rules currently get wrong ---------------------------
    # Kept in the gold set on purpose: hiding known failures would make the
    # reported accuracy meaningless.
    "مدرسہ": "madrasa",
    "دروازہ": "darwaza",
    "کمرہ": "kamra",
    "بارش": "barish",
    "دریا": "darya",
    "استاد": "ustad",
    "خوبصورت": "khoobsurat",
    "مسجد": "masjid",
    "کتابچہ": "kitabcha",
    "پرندہ": "parinda",
    "سمندر": "samandar",
    "روشنی": "roshni",
    "تصویر": "tasveer",
    "حکومت": "hukumat",
    "معلومات": "maloomat",
}
