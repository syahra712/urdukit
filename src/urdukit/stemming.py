"""A light rule-based stemmer for Urdu.

What this is
------------
A suffix stripper. It removes the most frequent inflectional endings --
plural and oblique markers, verb tense endings, a few common derivational
suffixes -- to collapse surface forms onto a shared stem for retrieval and
indexing.

What this is not
----------------
A lemmatizer. It does not consult a dictionary, does not know parts of
speech, and will not recover irregular forms: ``گیا`` (went) will not become
``جانا`` (to go). Urdu also inherits Persian and Arabic broken plurals
(``کتاب`` → ``کتب``) which no suffix rule can undo.

Stemming is a precision-for-recall trade. Use it for search indexing; do not
use it where the exact surface form matters.
"""

from __future__ import annotations

from .normalization import normalize

__all__ = ["stem", "stem_tokens", "SUFFIXES"]

#: Inflectional suffixes, longest first. Order matters: the stemmer strips
#: the first match, so ``یوں`` must be tried before ``وں`` and ``ں``.
SUFFIXES: tuple[str, ...] = (
    # --- verb / participial endings -------------------------------------
    "ئیں", "یاں", "یوں", "ییں",
    "تیں", "تاں",
    "ہوں", "ہیں",
    "گیا", "گئی", "گئے",
    "نا", "نے", "نی",
    "تا", "تی", "تے",
    "یا", "ئی", "ئے",
    "گا", "گی", "گے",
    # --- derivational ---------------------------------------------------
    # Deliberately excluded: "ستان" and "ان". Both are real suffixes, but
    # they shred proper nouns -- "ستان" turns پاکستان into پاک, which is
    # etymologically true and useless as a stem. The Persian ان-plural is
    # rare in Urdu; وں is the productive one and is kept below.
    "یات", "انہ", "وار", "دار",
    "ات",
    # --- plural / oblique -----------------------------------------------
    "وں", "یں",
    "ں", "ے", "ا", "ی", "و",
)

#: Below this length a stem is more likely noise than signal.
#:
#: Two, not three: core Urdu verb roots are two letters (کر, جا, دے, لے, ہو),
#: and a floor of three mis-stems every one of them -- کرتا would yield کرت
#: instead of کر, because the correct strip would be rejected and a shorter,
#: wrong suffix matched instead.
MIN_STEM_LENGTH = 2


def stem(word: str, *, min_length: int = MIN_STEM_LENGTH) -> str:
    """Strip one inflectional suffix from *word*.

    The word is normalized first, so Arabic-codepoint variants stem the same
    way as their Urdu spellings.

    Args:
        word: A single word.
        min_length: Refuse to produce a stem shorter than this.

    Returns:
        The stem, or the normalized word unchanged if no suffix applies.

        >>> stem("کتابوں")
        'کتاب'
        >>> stem("لڑکیاں")
        'لڑک'

    Only one suffix is removed. Stripping repeatedly tends to over-stem Urdu,
    because many roots legitimately end in ا, ی or ے.
    """
    word = normalize(word)
    if len(word) <= min_length:
        return word

    for suffix in SUFFIXES:
        if word.endswith(suffix):
            candidate = word[: -len(suffix)]
            if len(candidate) >= min_length:
                return candidate
    return word


def stem_tokens(tokens: list[str], *, min_length: int = MIN_STEM_LENGTH) -> list[str]:
    """Stem each token in *tokens*.

        >>> stem_tokens(["کتابوں", "لڑکیاں"])
        ['کتاب', 'لڑک']
    """
    return [stem(token, min_length=min_length) for token in tokens]
