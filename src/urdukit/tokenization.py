"""Sentence and word tokenization for Urdu.

Two things make Urdu tokenization harder than the space-splitting most
pipelines assume.

**The sentence terminator is not a period.** Urdu ends sentences with ۔
(U+06D4 ARABIC FULL STOP), a vertical bar. Splitting on ``.`` finds nothing;
splitting naively on ۔ breaks decimals and abbreviations.

**Spaces are unreliable.** Urdu is cursive, and ten letters -- ا د ڈ ذ ر ڑ ز
ژ و ے -- do not join to the letter that follows them. A word ending in one
of those already *looks* separated, so writers routinely omit the space
after it: ``کتابہے`` for ``کتاب ہے``. The reverse also happens, with spaces
appearing inside words after a non-joiner.

This module solves the tractable half. Space *insertion* (splitting
``کتابہے`` back into two words) requires a lexicon or a statistical model
and is deliberately out of scope for the rule-based tokenizer; see
:func:`word_tokenize` for what is and is not guaranteed.
"""

from __future__ import annotations

import re

from .characters import (
    URDU_DIACRITICS,
    URDU_DIGITS,
    URDU_LETTERS,
    URDU_HAMZA_FORMS,
    ZERO_WIDTH_NON_JOINER,
)

__all__ = [
    "sentence_tokenize",
    "word_tokenize",
    "NON_JOINING_LETTERS",
]

#: Letters that never connect to the following letter. A word ending in one
#: of these is visually separated from the next word even without a space,
#: which is why writers so often omit that space.
NON_JOINING_LETTERS = frozenset("ادڈذرڑزژوے")

_SENTENCE_TERMINATORS = "۔؟!?"

#: Closing marks that belong to the sentence they close.
_CLOSING_MARKS = "\"'”’)]»"

_TERMINATOR_RUN = re.compile(rf"[{_SENTENCE_TERMINATORS}]+")

_ALL_DIGITS = URDU_DIGITS | set("0123456789٠١٢٣٤٥٦٧٨٩")

# Note: ASCII "." is deliberately *not* a terminator. Urdu sentences end with
# ۔, and treating "." as a boundary would shatter URLs, decimals and English
# abbreviations embedded in the code-switched text that is normal here.

_WORD_CHARACTERS = (
    URDU_LETTERS | URDU_HAMZA_FORMS | URDU_DIACRITICS | {ZERO_WIDTH_NON_JOINER}
)

# A token is: a number (either digit system, with internal separators), a run
# of Urdu word characters, a run of Latin letters (code-switching is endemic
# in Urdu text), or a single other non-space character.
_TOKEN = re.compile(
    rf"""
      [{''.join(URDU_DIGITS)}0-9٠-٩]
      (?: [.,٫٬] [{''.join(URDU_DIGITS)}0-9٠-٩] |
          [{''.join(URDU_DIGITS)}0-9٠-٩] )*
    | [{''.join(sorted(_WORD_CHARACTERS))}]+
    | [A-Za-z]+ (?: ['’-][A-Za-z]+ )*
    | \S
    """,
    re.VERBOSE,
)


def sentence_tokenize(text: str) -> list[str]:
    """Split *text* into sentences.

    Splits on ۔ ؟ ! ?, keeping the terminator attached to its sentence.
    Decimal points and ellipses do not create boundaries, and closing quotes
    or brackets stay with the sentence they close.

        >>> sentence_tokenize("سلام۔ آپ کیسے ہیں؟ میں ٹھیک ہوں۔")
        ['سلام۔', 'آپ کیسے ہیں؟', 'میں ٹھیک ہوں۔']

    Args:
        text: Input text.

    Returns:
        A list of sentences with surrounding whitespace stripped. Empty
        input yields an empty list.
    """
    if not text or not text.strip():
        return []

    sentences: list[str] = []
    start = 0
    length = len(text)

    for match in _TERMINATOR_RUN.finditer(text):
        run_start, run_end = match.span()

        # A lone terminator flanked by digits on *both* sides is a decimal
        # separator (۵۔۲), not a sentence boundary. Requiring both sides is
        # what keeps "2026۔ اگلا سال" splitting correctly.
        if (
            run_end - run_start == 1
            and run_start > 0
            and text[run_start - 1] in _ALL_DIGITS
            and run_end < length
            and text[run_end] in _ALL_DIGITS
        ):
            continue

        cursor = run_end
        while cursor < length and text[cursor] in _CLOSING_MARKS:
            cursor += 1

        sentence = text[start:cursor].strip()
        if sentence:
            sentences.append(sentence)

        # Whitespace after the terminator is optional: Urdu text routinely
        # omits it ("ایک۔دو۔تین۔").
        while cursor < length and text[cursor].isspace():
            cursor += 1
        start = cursor

    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def word_tokenize(text: str, *, keep_punctuation: bool = True) -> list[str]:
    """Split *text* into word tokens.

    Handles the Urdu script, Latin code-switching, and both digit systems.
    Numbers keep their internal decimal and thousands separators.

        >>> word_tokenize("میں ۲۰۲۶ میں پاکستان گیا۔")
        ['میں', '۲۰۲۶', 'میں', 'پاکستان', 'گیا', '۔']

    Args:
        text: Input text.
        keep_punctuation: If ``False``, drop punctuation-only tokens.

    Returns:
        A list of tokens.

    Note:
        This is a rule-based tokenizer: it splits on whitespace and
        punctuation. It does **not** recover omitted spaces -- ``کتابہے``
        stays one token rather than becoming ``کتاب`` + ``ہے``, because
        deciding that split needs a lexicon. See :data:`NON_JOINING_LETTERS`
        for why that error is so common in real Urdu text.
    """
    if not text:
        return []

    tokens = _TOKEN.findall(text)
    tokens = [t for t in (tok.strip() for tok in tokens) if t]

    if not keep_punctuation:
        tokens = [t for t in tokens if any(c.isalnum() or c in _WORD_CHARACTERS for c in t)]
    return tokens
