"""Urdu character inventory.

Urdu is written in a Perso-Arabic script that overlaps with, but is not
identical to, Arabic. Text found in the wild is routinely a mixture of the
two: Arabic keyboards, older fonts and careless copy-paste all inject Arabic
codepoints into what should be Urdu. Almost every downstream bug in Urdu NLP
traces back to that mixture, so the tables here are deliberately explicit
about which codepoint is the Urdu one.

Every constant is a ``frozenset`` or an immutable mapping so callers cannot
mutate shared state.

References:
    Unicode 15.1, Arabic (U+0600-U+06FF), Arabic Presentation Forms-A/B.
"""

from types import MappingProxyType

# --------------------------------------------------------------------------
# Letters
# --------------------------------------------------------------------------

#: The 39 letters of the Urdu alphabet, in traditional order.
URDU_LETTERS = frozenset(
    "ا"  # ا  ALEF
    "آ"  # آ  ALEF WITH MADDA ABOVE
    "ب"  # ب  BEH
    "پ"  # پ  PEH
    "ت"  # ت  TEH
    "ٹ"  # ٹ  TTEH
    "ث"  # ث  THEH
    "ج"  # ج  JEEM
    "چ"  # چ  TCHEH
    "ح"  # ح  HAH
    "خ"  # خ  KHAH
    "د"  # د  DAL
    "ڈ"  # ڈ  DDAL
    "ذ"  # ذ  THAL
    "ر"  # ر  REH
    "ڑ"  # ڑ  RREH
    "ز"  # ز  ZAIN
    "ژ"  # ژ  JEH
    "س"  # س  SEEN
    "ش"  # ش  SHEEN
    "ص"  # ص  SAD
    "ض"  # ض  DAD
    "ط"  # ط  TAH
    "ظ"  # ظ  ZAH
    "ع"  # ع  AIN
    "غ"  # غ  GHAIN
    "ف"  # ف  FEH
    "ق"  # ق  QAF
    "ک"  # ک  KEHEH        (not Arabic KAF U+0643)
    "گ"  # گ  GAF
    "ل"  # ل  LAM
    "م"  # م  MEEM
    "ن"  # ن  NOON
    "ں"  # ں  NOON GHUNNA
    "و"  # و  WAW
    "ہ"  # ہ  HEH GOAL     (not Arabic HEH U+0647)
    "ھ"  # ھ  HEH DOACHASHMEE
    "ی"  # ی  FARSI YEH    (not Arabic YEH U+064A)
    "ے"  # ے  YEH BARREE
)

#: Hamza carriers and related composite forms that occur in valid Urdu.
URDU_HAMZA_FORMS = frozenset(
    "ء"  # ء  HAMZA
    "ؤ"  # ؤ  WAW WITH HAMZA ABOVE
    "ئ"  # ئ  YEH WITH HAMZA ABOVE
    "ۂ"  # ۂ  HEH GOAL WITH HAMZA ABOVE
    "ۓ"  # ۓ  YEH BARREE WITH HAMZA ABOVE
)

#: Aerab (harakat): vowel marks and other combining diacritics.
#: These are combining characters -- they occupy no width of their own.
URDU_DIACRITICS = frozenset(
    "ً"  # ً  FATHATAN      (do zabar)
    "ٌ"  # ٌ  DAMMATAN      (do pesh)
    "ٍ"  # ٍ  KASRATAN      (do zer)
    "َ"  # َ  FATHA         (zabar)
    "ُ"  # ُ  DAMMA         (pesh)
    "ِ"  # ِ  KASRA         (zer)
    "ّ"  # ّ  SHADDA        (tashdeed)
    "ْ"  # ْ  SUKUN         (jazm)
    "ٓ"  # ٓ  MADDAH ABOVE
    "ٔ"  # ٔ  HAMZA ABOVE
    "ٕ"  # ٕ  HAMZA BELOW
    "ٖ"  # ٖ  SUBSCRIPT ALEF
    "ٗ"  # ٗ  INVERTED DAMMA (ulta pesh)
    "٘"  # ٘  MARK NOON GHUNNA
    "ٙ"  # ٙ  ZWARAKAY
    "ٚ"  # ٚ  VOWEL SIGN SMALL V ABOVE
    "ٛ"  # ٛ  VOWEL SIGN INVERTED SMALL V ABOVE
    "ٜ"  # ٜ  VOWEL SIGN DOT BELOW
    "ٝ"  # ٝ  REVERSED DAMMA
    "ٞ"  # ٞ  FATHA WITH TWO DOTS
    "ٰ"  # ٰ  SUPERSCRIPT ALEF (khari zabar)
)

# --------------------------------------------------------------------------
# Digits
# --------------------------------------------------------------------------

#: Extended Arabic-Indic digits -- the digits actually used for Urdu.
URDU_DIGITS = frozenset("۰۱۲۳۴۵۶۷۸۹")

#: Arabic-Indic digits -- used for Arabic, frequently mixed into Urdu text.
ARABIC_DIGITS = frozenset("٠١٢٣٤٥٦٧٨٩")

# --------------------------------------------------------------------------
# Punctuation
# --------------------------------------------------------------------------

#: Urdu sentence terminators. U+06D4 is the Urdu full stop -- a vertical bar,
#: not the Latin period, which is why naive ``.``-splitting fails on Urdu.
URDU_SENTENCE_ENDINGS = frozenset("۔؟!.?")

URDU_PUNCTUATION = frozenset(
    "۔"  # ۔  FULL STOP
    "،"  # ،  COMMA
    "؛"  # ؛  SEMICOLON
    "؟"  # ؟  QUESTION MARK
    "٪"  # ٪  PERCENT SIGN
    "٫"  # ٫  DECIMAL SEPARATOR
    "٬"  # ٬  THOUSANDS SEPARATOR
    "٭"  # ٭  FIVE POINTED STAR
    "ـ"  # ـ  TATWEEL (kashida)
)

# --------------------------------------------------------------------------
# Invisible characters
# --------------------------------------------------------------------------

#: Zero-width and directionality marks.
#:
#: ZWNJ (U+200C) is singled out because it is *semantically load-bearing* in
#: Urdu -- it blocks ligature formation in compounds -- whereas the rest are
#: almost always copy-paste noise. Callers that care about compound integrity
#: should preserve it; see :func:`urdukit.normalize.normalize`.
ZERO_WIDTH_NON_JOINER = "‌"

INVISIBLE_CHARACTERS = frozenset(
    "​"  # ZERO WIDTH SPACE
    "‌"  # ZERO WIDTH NON-JOINER
    "‍"  # ZERO WIDTH JOINER
    "‎"  # LEFT-TO-RIGHT MARK
    "‏"  # RIGHT-TO-LEFT MARK
    "‪"  # LEFT-TO-RIGHT EMBEDDING
    "‫"  # RIGHT-TO-LEFT EMBEDDING
    "‬"  # POP DIRECTIONAL FORMATTING
    "‭"  # LEFT-TO-RIGHT OVERRIDE
    "‮"  # RIGHT-TO-LEFT OVERRIDE
    "﻿"  # ZERO WIDTH NO-BREAK SPACE (BOM)
    "­"  # SOFT HYPHEN
)

# --------------------------------------------------------------------------
# Normalization mappings
# --------------------------------------------------------------------------

#: Arabic codepoints that must be folded to their Urdu equivalents.
#:
#: This single table is responsible for the majority of "why doesn't my Urdu
#: string match" bugs. U+064A and U+06CC render near-identically in most
#: fonts but are distinct codepoints, so ``"علی" != "علي"`` even though both
#: look like *Ali*.
ARABIC_TO_URDU = MappingProxyType({
    "ي": "ی",  # ي ARABIC YEH        -> ی FARSI YEH
    "ى": "ی",  # ى ALEF MAKSURA      -> ی FARSI YEH
    "ې": "ی",  # ې E                 -> ی FARSI YEH
    "ك": "ک",  # ك ARABIC KAF        -> ک KEHEH
    "ڪ": "ک",  # ڪ SWASH KAF         -> ک KEHEH
    "ه": "ہ",  # ه ARABIC HEH        -> ہ HEH GOAL
    "ۀ": "ۂ",  # ۀ HEH WITH YEH ABOVE-> ۂ HEH GOAL W/ HAMZA
    "ة": "ہ",  # ة TEH MARBUTA       -> ہ HEH GOAL
    "أ": "ا",  # أ ALEF WITH HAMZA   -> ا ALEF
    "إ": "ا",  # إ ALEF WITH HAMZA BELOW -> ا ALEF
    "ٱ": "ا",  # ٱ ALEF WASLA        -> ا ALEF
    "ٲ": "ا",  # ٲ ALEF WITH WAVY HAMZA -> ا ALEF
    "ٳ": "ا",  # ٳ ALEF WITH WAVY HAMZA BELOW -> ا ALEF
    "ٵ": "ا",  # ٵ HIGH HAMZA ALEF   -> ا ALEF
    "ۍ": "ی",  # ۍ YEH WITH TAIL     -> ی FARSI YEH
    # NOTE: the decomposed sequence <U+064A YEH, U+0654 HAMZA ABOVE> also
    # needs folding to U+0626, but that is a *canonical* composition, so NFC
    # handles it. It is deliberately absent here: every key in this table is
    # a single codepoint, which lets callers use ``str.translate``.
})

#: Presentation-form ligatures that must be decomposed to real letters.
#:
#: Closes urduhack issue #141 (normalize U+FDF2 to the spelled-out form).
LIGATURES = MappingProxyType({
    "ﷲ": "اللہ",  # ﷲ  ALLAH
    "ﷺ": "صلی اللہ علیہ وسلم",  # ﷺ
    "ﷻ": "جل جلالہ",  # ﷻ
    "﷽": "بسم اللہ الرحمن الرحیم",  # ﷽
    "ﻻ": "لا",  # ﻻ  LAM-ALEF
    "ﻵ": "لآ",  # ﻵ  LAM-ALEF WITH MADDA
    "ﻷ": "لا",  # ﻷ  LAM-ALEF WITH HAMZA ABOVE
    "ﻹ": "لا",  # ﻹ  LAM-ALEF WITH HAMZA BELOW
})

#: Digit folding tables, keyed by target system.
_URDU_DIGIT_LIST = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGIT_LIST = "٠١٢٣٤٥٦٧٨٩"
_ASCII_DIGIT_LIST = "0123456789"

TO_URDU_DIGITS = MappingProxyType({
    **{a: u for a, u in zip(_ARABIC_DIGIT_LIST, _URDU_DIGIT_LIST)},
    **{a: u for a, u in zip(_ASCII_DIGIT_LIST, _URDU_DIGIT_LIST)},
})

TO_ASCII_DIGITS = MappingProxyType({
    **{u: a for u, a in zip(_URDU_DIGIT_LIST, _ASCII_DIGIT_LIST)},
    **{u: a for u, a in zip(_ARABIC_DIGIT_LIST, _ASCII_DIGIT_LIST)},
})

#: Every codepoint this library recognises as "Urdu script".
URDU_ALL = (
    URDU_LETTERS
    | URDU_HAMZA_FORMS
    | URDU_DIACRITICS
    | URDU_DIGITS
    | URDU_PUNCTUATION
)


def is_urdu_character(char: str) -> bool:
    """Return ``True`` if *char* is part of the Urdu script inventory.

    Args:
        char: A single character.

    Raises:
        ValueError: If *char* is not exactly one character.
    """
    if len(char) != 1:
        raise ValueError(f"expected a single character, got {len(char)}")
    return char in URDU_ALL
