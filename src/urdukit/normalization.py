"""Urdu text normalization.

The goal of this module is that two strings a human would call "the same
Urdu" compare equal. In practice that means folding Arabic codepoints onto
their Urdu counterparts, stripping optional vowel marks, expanding
presentation-form ligatures and repairing the punctuation spacing that Urdu
text acquires as it moves between editors.

Every step is exposed as its own function so callers can build a pipeline
that matches their task. :func:`normalize` applies a sensible default set.

    >>> from urdukit import normalize
    >>> normalize("مُحَمَّد علي")
    'محمد علی'
"""

from __future__ import annotations

import re
import unicodedata

from .characters import (
    ARABIC_TO_URDU,
    INVISIBLE_CHARACTERS,
    LIGATURES,
    TO_ASCII_DIGITS,
    TO_URDU_DIGITS,
    URDU_DIACRITICS,
    ZERO_WIDTH_NON_JOINER,
)

__all__ = [
    "normalize",
    "normalize_unicode",
    "fold_arabic",
    "remove_diacritics",
    "expand_ligatures",
    "normalize_digits",
    "normalize_punctuation",
    "remove_invisible",
    "collapse_whitespace",
    "is_normalized",
]

#: U+0640 ARABIC TATWEEL -- a purely typographic elongation with no meaning.
_TATWEEL = "ـ"

#: Punctuation that binds tightly to the preceding word: no space before,
#: exactly one space after.
_CLINGING_PUNCTUATION = "۔،؛؟!:"

_ARABIC_FOLD_TABLE = str.maketrans(dict(ARABIC_TO_URDU))
_DIACRITIC_TABLE = str.maketrans({c: None for c in URDU_DIACRITICS})
_INVISIBLE_TABLE = str.maketrans({c: None for c in INVISIBLE_CHARACTERS})
_INVISIBLE_KEEP_ZWNJ_TABLE = str.maketrans(
    {c: None for c in INVISIBLE_CHARACTERS if c != ZERO_WIDTH_NON_JOINER}
)
_TO_URDU_DIGIT_TABLE = str.maketrans(dict(TO_URDU_DIGITS))
_TO_ASCII_DIGIT_TABLE = str.maketrans(dict(TO_ASCII_DIGITS))

_REPEATED_FULL_STOP = re.compile("۔{2,}")
_SPACE_BEFORE_PUNCT = re.compile(rf"\s+([{_CLINGING_PUNCTUATION}])")
_MISSING_SPACE_AFTER_PUNCT = re.compile(
    rf"([{_CLINGING_PUNCTUATION}])(?=[^\s{_CLINGING_PUNCTUATION}])"
)
_WHITESPACE_RUN = re.compile(r"[ \t  -   　]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def normalize_unicode(text: str, form: str = "NFC") -> str:
    """Apply a Unicode normalization *form* (default ``NFC``).

    NFC is the right default for Urdu: it composes sequences such as
    ``<YEH, HAMZA ABOVE>`` into their single-codepoint forms while leaving
    Urdu-specific letters untouched. NFKC is *not* safe here -- it decomposes
    ﷲ using Arabic HEH rather than Urdu HEH GOAL.
    """
    return unicodedata.normalize(form, text)


def fold_arabic(text: str) -> str:
    """Replace Arabic codepoints with their Urdu equivalents.

    This is the single highest-value normalization step. Arabic YEH (U+064A)
    and Urdu FARSI YEH (U+06CC) are visually near-identical but distinct, so
    without folding, ``"علی" != "علي"``.

        >>> fold_arabic("علي") == "علی"
        True
    """
    return text.translate(_ARABIC_FOLD_TABLE)


def remove_diacritics(text: str) -> str:
    """Strip aerab (zabar, zer, pesh, tashdeed, ...).

    Urdu is almost always written without vowel marks; when they appear they
    are pedagogical or religious. Removing them makes text from mixed sources
    comparable.

        >>> remove_diacritics("مُحَمَّد") == "محمد"
        True
    """
    return text.translate(_DIACRITIC_TABLE)


def expand_ligatures(text: str) -> str:
    """Expand presentation-form ligatures into ordinary letters.

    Closes urduhack #141: ``ﷲ`` (U+FDF2) becomes ``اللہ`` spelled with Urdu
    HEH GOAL, not the Arabic HEH that NFKC would produce.
    """
    for ligature, expansion in LIGATURES.items():
        text = text.replace(ligature, expansion)
    return text


def normalize_digits(text: str, to: str = "urdu") -> str:
    """Fold digits into one numeral system.

    Args:
        text: Input text.
        to: ``"urdu"`` for ۰-۹ (U+06F0-U+06F9), or ``"ascii"`` for 0-9.

    Raises:
        ValueError: If *to* is not ``"urdu"`` or ``"ascii"``.
    """
    if to == "urdu":
        return text.translate(_TO_URDU_DIGIT_TABLE)
    if to == "ascii":
        return text.translate(_TO_ASCII_DIGIT_TABLE)
    raise ValueError(f"to must be 'urdu' or 'ascii', got {to!r}")


def remove_invisible(text: str, *, preserve_zwnj: bool = False) -> str:
    """Remove zero-width and bidirectional control characters.

    Args:
        text: Input text.
        preserve_zwnj: Keep U+200C. ZWNJ is semantically load-bearing in Urdu
            compounds -- it blocks ligature formation -- so preserve it when
            round-tripping text you intend to display. For matching and
            model input, removing it is usually what you want.
    """
    table = _INVISIBLE_KEEP_ZWNJ_TABLE if preserve_zwnj else _INVISIBLE_TABLE
    return text.translate(table)


def normalize_punctuation(text: str, *, collapse_repeats: bool = True) -> str:
    """Repair punctuation spacing.

    Removes space before clinging punctuation, guarantees one space after it,
    and optionally collapses runs of ``۔`` (urduhack #52).

        >>> normalize_punctuation("سلام ۔یہ کیا ہے ؟")
        'سلام۔ یہ کیا ہے؟'
    """
    text = text.replace(_TATWEEL, "")
    if collapse_repeats:
        text = _REPEATED_FULL_STOP.sub("۔", text)
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    text = _MISSING_SPACE_AFTER_PUNCT.sub(r"\1 ", text)
    return text


def collapse_whitespace(text: str) -> str:
    """Collapse runs of horizontal whitespace and trim each line."""
    text = _WHITESPACE_RUN.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def normalize(
    text: str,
    *,
    unicode_form: str = "NFC",
    arabic: bool = True,
    diacritics: bool = True,
    ligatures: bool = True,
    digits: str | None = None,
    punctuation: bool = True,
    whitespace: bool = True,
    preserve_zwnj: bool = False,
) -> str:
    """Normalize Urdu text using a sensible default pipeline.

    Args:
        text: Input text.
        unicode_form: Unicode normalization form; ``None`` to skip.
        arabic: Fold Arabic codepoints onto Urdu ones.
        diacritics: Strip aerab.
        ligatures: Expand presentation-form ligatures.
        digits: ``"urdu"``, ``"ascii"``, or ``None`` to leave digits alone.
        punctuation: Repair punctuation spacing.
        whitespace: Collapse whitespace runs and trim.
        preserve_zwnj: Keep U+200C (see :func:`remove_invisible`).

    Returns:
        The normalized text.

    The order matters: ligatures are expanded *before* Arabic folding so that
    any Arabic codepoints an expansion introduces are themselves folded, and
    whitespace is collapsed last so earlier steps cannot leave double spaces.
    """
    if not text:
        return text

    if unicode_form:
        text = normalize_unicode(text, unicode_form)
    text = remove_invisible(text, preserve_zwnj=preserve_zwnj)
    if ligatures:
        text = expand_ligatures(text)
    if arabic:
        text = fold_arabic(text)
    if diacritics:
        text = remove_diacritics(text)
    if digits is not None:
        text = normalize_digits(text, to=digits)
    if punctuation:
        text = normalize_punctuation(text)
    if whitespace:
        text = collapse_whitespace(text)
    return text


def is_normalized(text: str, **kwargs) -> bool:
    """Return ``True`` if *text* is unchanged by :func:`normalize`.

    Closes urduhack #60, which asked for exactly this predicate. Accepts the
    same keyword arguments as :func:`normalize`.
    """
    return text == normalize(text, **kwargs)
