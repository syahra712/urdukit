"""A light rule-based stemmer for Urdu.

What this is
------------
A suffix stripper. It removes inflectional endings in three ordered steps,
to collapse surface forms onto a shared stem for retrieval and indexing:

1. the future auxiliary fused onto a verb: گا گی گے (``کریںگے``);
2. one ending -- plural, oblique, gender, tense or participle (``وں``,
   ``یاں``, ``تا``, ``نے``, ``ی`` ...), longest first;
3. a hamza glide left hanging by step 2 (``ہوئے`` → ``ہوئ`` → ``ہو``).

Each step strips at most once, so ``کریںگے`` becomes ``کر`` but a root that
happens to end in ا, ی or ے is not eaten letter by letter.

How well it works
-----------------
Scored with ``scripts/benchmark_ud.py`` against the lemmas of the Urdu UD
treebank -- do two forms share a stem exactly when annotators gave them the
same lemma -- this design reaches 73.7% F1 on the held-out test split,
against 65.3% for the previous single-strip stemmer. Rules were chosen on
the train and dev splits only. Most remaining "errors" are of two kinds:
verbs and the nouns derived from them (``کھیل`` / ``کھیلنا``), which UD
keeps apart and a search index usually should not, and genuine
homographs (``جان`` *life* / ``جاننا`` *to know*), which no stemmer
without a dictionary can separate.

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

__all__ = ["stem", "stem_tokens", "SUFFIXES", "PROTECTED"]

#: Step 1: the future auxiliary, when written fused to the verb.
_FUTURE: tuple[str, ...] = ("گا", "گی", "گے")

#: Step 2: inflectional suffixes, longest first. Only the first match is
#: stripped, so ``یوں`` must be tried before ``وں`` and ``ں``.
#:
#: Deliberately excluded: ``ستان`` and ``ان`` shred proper nouns (پاکستان
#: → پاک), and the derivational ``انہ``, ``دار`` and ``یات`` each measured
#: worse than leaving the word alone. The Persian ان-plural is rare in Urdu;
#: وں is the productive one.
SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        # plural / oblique
        "یوں یاں ؤں وں یں ییں ئیں ں".split()
        # verb: infinitive, imperfective, perfective, subjunctive
        + "نا نے نی تا تی تے تیں تاں یا ئی ئے یے".split()
        # auxiliaries written fused to the verb
        + "ہوں ہیں".split()
        # Arabic sound plural
        + ["ات"]
        # gender / number / oblique on nouns and adjectives
        + "ا ی ے و ہ".split(),
        key=len,
        reverse=True,
    )
)

#: Shortest stem each suffix may leave. Two is the default because core verb
#: roots are two letters (کر, جا, دے, ہو): a floor of three turns کرتا into
#: کرت. Final ہ needs three, or every two-letter noun in ہ disappears.
_MIN_STEM_FOR = {"ہ": 3}

#: Hamza seats left at the end of a stem once a vowel ending is removed.
_GLIDES = "ئؤ"

#: Words that end like an inflection but are not inflected, mapped to
#: nothing: they and their plurals stem to the word itself. Hand-written;
#: the list is for very common words whose stems would otherwise collide
#: with unrelated words (پانی → پا), not an attempt at a dictionary.
PROTECTED: frozenset[str] = frozenset(
    """
    پانی کہانی رانی نانی کراچی بھائی ساتھی کافی باقی ماضی قاضی راضی
    کشتی بستی مٹی ٹوپی کاپی چھٹی
    دنیا دریا
    اردو ہندو جادو آلو چاقو ترازو خوشبو آرزو پہلو
    زندگی
    چائے رائے گائے
    """.split()
)

#: Below this length a stem is more likely noise than signal.
MIN_STEM_LENGTH = 2


def _protected_form(stem: str) -> str | None:
    """The protected word *stem* is an inflection of, if any."""
    for restored in ("", "ی", "ا", "ے"):
        if stem + restored in PROTECTED:
            return stem + restored
    return None


def stem(word: str, *, min_length: int = MIN_STEM_LENGTH) -> str:
    """Reduce *word* to a stem shared with its inflected forms.

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
        >>> stem("کریںگے")
        'کر'
        >>> stem("کہانیوں")
        'کہانی'
    """
    word = normalize(word)
    if len(word) <= min_length or word in PROTECTED:
        return word

    for suffix in _FUTURE:
        if word.endswith(suffix) and len(word) - len(suffix) >= min_length:
            word = word[: -len(suffix)]
            break

    for suffix in SUFFIXES:
        floor = max(min_length, _MIN_STEM_FOR.get(suffix, 0))
        if word.endswith(suffix) and len(word) - len(suffix) >= floor:
            candidate = word[: -len(suffix)]
            protected = _protected_form(candidate)
            if protected is not None:
                return protected
            word = candidate
            break

    if len(word) > min_length and word[-1] in _GLIDES:
        word = word[:-1]
    return word


def stem_tokens(tokens: list[str], *, min_length: int = MIN_STEM_LENGTH) -> list[str]:
    """Stem each token in *tokens*.

    >>> stem_tokens(["کتابوں", "لڑکیاں"])
    ['کتاب', 'لڑک']
    """
    return [stem(token, min_length=min_length) for token in tokens]
