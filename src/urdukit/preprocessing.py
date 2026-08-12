"""Text preprocessing helpers.

Corpus-cleaning utilities that sit alongside normalization: masking URLs,
emails and numbers before modelling, and repairing the missing spaces that
appear where Urdu text meets Latin characters or digits.
"""

from __future__ import annotations

import re

from .characters import URDU_DIGITS, URDU_LETTERS, URDU_PUNCTUATION
from .normalization import collapse_whitespace

__all__ = [
    "normalize_whitespace",
    "replace_urls",
    "replace_emails",
    "replace_numbers",
    "replace_phone_numbers",
    "replace_currency_symbols",
    "remove_punctuation",
    "digits_space",
    "english_characters_space",
    "all_punctuations_space",
    "preprocess",
]

_URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"]+|\b[\w-]+\.(?:com|org|net|edu|gov|pk|io)\b[^\s<>\"]*",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(
    r"(?:(?:\+|00)\d{1,3}[ -]?)?(?:\(\d{2,4}\)[ -]?)?\d{3,4}[ -]?\d{4,7}\b"
)
_CURRENCY_RE = re.compile(r"[$€£¥₹₨¢]")

_URDU_DIGIT_CLASS = "".join(URDU_DIGITS)
_PUNCTUATION_CLASS = re.escape(
    "".join(URDU_PUNCTUATION) + "!\"#'()*+,-./:;<=>?@[]^_`{|}~"
)
_URDU_LETTER_CLASS = "".join(sorted(URDU_LETTERS))

_DIGIT_BOUNDARY_RE = re.compile(
    rf"(?<=[{_URDU_LETTER_CLASS}])(?=[{_URDU_DIGIT_CLASS}0-9])"
    rf"|(?<=[{_URDU_DIGIT_CLASS}0-9])(?=[{_URDU_LETTER_CLASS}])"
)
_ENGLISH_BOUNDARY_RE = re.compile(
    rf"(?<=[{_URDU_LETTER_CLASS}])(?=[A-Za-z])|(?<=[A-Za-z])(?=[{_URDU_LETTER_CLASS}])"
)
_PUNCTUATION_BOUNDARY_RE = re.compile(rf"\s*([{_PUNCTUATION_CLASS}])\s*")
_PUNCTUATION_STRIP_RE = re.compile(rf"[{_PUNCTUATION_CLASS}]")


def normalize_whitespace(text: str) -> str:
    """Collapse whitespace runs and trim. Alias of :func:`collapse_whitespace`."""
    return collapse_whitespace(text)


def replace_urls(text: str, replace_with: str = "<URL>") -> str:
    """Replace URLs with *replace_with*."""
    return _URL_RE.sub(replace_with, text)


def replace_emails(text: str, replace_with: str = "<EMAIL>") -> str:
    """Replace email addresses with *replace_with*."""
    return _EMAIL_RE.sub(replace_with, text)


def replace_numbers(text: str, replace_with: str = "<NUMBER>") -> str:
    """Replace numbers -- in either digit system -- with *replace_with*."""
    pattern = re.compile(
        rf"[{_URDU_DIGIT_CLASS}0-9]+(?:[.,٫٬][{_URDU_DIGIT_CLASS}0-9]+)*"
    )
    return pattern.sub(replace_with, text)


def replace_phone_numbers(text: str, replace_with: str = "<PHONE>") -> str:
    """Replace phone numbers with *replace_with*.

    Deliberately conservative: it will miss unusual formats rather than
    swallow ordinary numbers. Run it before :func:`replace_numbers`, which is
    greedier and would otherwise consume phone numbers first.
    """
    return _PHONE_RE.sub(replace_with, text)


def replace_currency_symbols(text: str, replace_with: str = "<CUR>") -> str:
    """Replace currency symbols with *replace_with*."""
    return _CURRENCY_RE.sub(replace_with, text)


def remove_punctuation(text: str) -> str:
    """Strip punctuation, leaving a single space where it stood."""
    return collapse_whitespace(_PUNCTUATION_STRIP_RE.sub(" ", text))


def digits_space(text: str) -> str:
    """Insert a space where an Urdu letter abuts a digit.

    >>> digits_space("سال۲۰۲۶میں")
    'سال ۲۰۲۶ میں'
    """
    return _DIGIT_BOUNDARY_RE.sub(" ", text)


def english_characters_space(text: str) -> str:
    """Insert a space where Urdu and Latin letters abut.

    >>> english_characters_space("میںcomputerاستعمال")
    'میں computer استعمال'
    """
    return _ENGLISH_BOUNDARY_RE.sub(" ", text)


def all_punctuations_space(text: str) -> str:
    """Put exactly one space after punctuation and none before it."""
    return collapse_whitespace(_PUNCTUATION_BOUNDARY_RE.sub(r"\1 ", text))


def preprocess(text: str) -> str:
    """Apply the space-repair helpers in a sensible order."""
    text = digits_space(text)
    text = english_characters_space(text)
    text = all_punctuations_space(text)
    return normalize_whitespace(text)
