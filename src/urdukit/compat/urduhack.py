"""Drop-in replacement for the ``urduhack`` API.

``urduhack`` was the de-facto Urdu NLP library. Its last release was July
2020, and ``pip install urduhack; import urduhack`` now fails outright on
modern Python: its package ``__init__`` imports TensorFlow unconditionally
even though TensorFlow is declared an optional extra.

This module lets existing code move across by changing one line::

    # before
    from urduhack import normalize
    from urduhack.tokenization import sentence_tokenizer, word_tokenizer

    # after
    from urdukit.compat.urduhack import normalize
    from urdukit.compat.urduhack import sentence_tokenizer, word_tokenizer

Or, to convert a whole module at once::

    import urdukit.compat.urduhack as urduhack

Deliberate differences
----------------------
This is a compatibility layer, not a clone. Behaviour differs where
``urduhack`` was wrong:

- ``normalize`` folds a wider set of Arabic codepoints and expands the ﷲ
  ligature using Urdu HEH GOAL rather than Arabic HEH.
- ``URDU_DIACRITICS`` here contains all 21 combining marks; ``urduhack``
  listed 6.
- Sentence tokenization splits correctly when the space after ۔ is missing.

The model-backed API -- ``Pipeline``, ``CoNLL``, ``download`` -- is not
provided. Those needed TensorFlow and downloaded weights from an S3 bucket;
they are the reason the original became uninstallable. Calling them raises
:class:`NotImplementedError` with a pointer to the closest alternative
rather than failing obscurely.
"""

from __future__ import annotations

from .. import characters as _characters
from .. import normalization as _normalization
from .. import preprocessing as _preprocessing
from .. import stopwords as _stopwords
from .. import tokenization as _tokenization

__all__ = [
    # normalization
    "normalize",
    "normalize_characters",
    "normalize_combine_characters",
    "remove_diacritics",
    "replace_digits",
    # tokenization
    "sentence_tokenizer",
    "word_tokenizer",
    # stop words
    "STOP_WORDS",
    "remove_stopwords",
    # character sets
    "URDU_ALPHABETS",
    "URDU_DIGITS",
    "URDU_PUNCTUATIONS",
    "URDU_DIACRITICS",
    "URDU_ALL_CHARACTERS",
    # preprocessing
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
    # unsupported
    "Pipeline",
    "CoNLL",
    "download",
]


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------


def normalize(text: str) -> str:
    """Normalize Urdu text. See :func:`urdukit.normalize`."""
    return _normalization.normalize(text)


def normalize_characters(text: str) -> str:
    """Fold Arabic codepoints onto their Urdu equivalents."""
    return _normalization.fold_arabic(text)


def normalize_combine_characters(text: str) -> str:
    """Compose decomposed character sequences (NFC)."""
    return _normalization.normalize_unicode(text, "NFC")


def remove_diacritics(text: str) -> str:
    """Strip aerab."""
    return _normalization.remove_diacritics(text)


def replace_digits(text: str, with_english: bool = True) -> str:
    """Fold digits into one system.

    Args:
        text: Input text.
        with_english: ``True`` (the default, matching ``urduhack``) converts
            to ASCII digits; ``False`` converts to Urdu digits.
    """
    return _normalization.normalize_digits(text, to="ascii" if with_english else "urdu")


# --------------------------------------------------------------------------
# Tokenization
# --------------------------------------------------------------------------


def sentence_tokenizer(text: str) -> list[str]:
    """Split text into sentences."""
    return _tokenization.sentence_tokenize(text)


def word_tokenizer(text: str) -> list[str]:
    """Split text into word tokens."""
    return _tokenization.word_tokenize(text)


# --------------------------------------------------------------------------
# Stop words
# --------------------------------------------------------------------------

#: Urdu stopwords, matching ``urduhack.stop_words.STOP_WORDS``.
STOP_WORDS = _stopwords.STOPWORDS


def remove_stopwords(text: str) -> str:
    """Remove stopwords from *text*.

    Note the signature: ``urduhack`` takes and returns a **string**, unlike
    :func:`urdukit.remove_stopwords`, which takes and returns a list of
    tokens. This shim preserves the original behaviour so existing callers
    keep working.
    """
    return " ".join(_stopwords.remove_stopwords(_tokenization.word_tokenize(text)))


# --------------------------------------------------------------------------
# Character sets
# --------------------------------------------------------------------------

URDU_ALPHABETS = _characters.URDU_LETTERS | _characters.URDU_HAMZA_FORMS
URDU_DIGITS = _characters.URDU_DIGITS
URDU_PUNCTUATIONS = _characters.URDU_PUNCTUATION
URDU_DIACRITICS = _characters.URDU_DIACRITICS
URDU_ALL_CHARACTERS = _characters.URDU_ALL


# --------------------------------------------------------------------------
# Preprocessing
# --------------------------------------------------------------------------

normalize_whitespace = _preprocessing.normalize_whitespace
replace_urls = _preprocessing.replace_urls
replace_emails = _preprocessing.replace_emails
replace_numbers = _preprocessing.replace_numbers
replace_phone_numbers = _preprocessing.replace_phone_numbers
replace_currency_symbols = _preprocessing.replace_currency_symbols
remove_punctuation = _preprocessing.remove_punctuation
digits_space = _preprocessing.digits_space
english_characters_space = _preprocessing.english_characters_space
all_punctuations_space = _preprocessing.all_punctuations_space
preprocess = _preprocessing.preprocess


# --------------------------------------------------------------------------
# Unsupported model-backed API
# --------------------------------------------------------------------------

_UNSUPPORTED = (
    "urdukit does not provide {name}. It required TensorFlow and model "
    "weights downloaded at runtime, which is what made urduhack "
    "uninstallable. {alternative}"
)


def _unsupported(name: str, alternative: str):
    def raiser(*_args, **_kwargs):
        raise NotImplementedError(
            _UNSUPPORTED.format(name=name, alternative=alternative)
        )

    raiser.__name__ = name
    return raiser


Pipeline = _unsupported(
    "Pipeline",
    "For POS tagging or NER, use stanza (which supports Urdu) and keep "
    "urdukit for normalization and tokenization.",
)

CoNLL = _unsupported(
    "CoNLL",
    "Use the conllu package to read and write CoNLL-U files.",
)

download = _unsupported(
    "download",
    "No downloads are needed: urdukit ships everything it uses.",
)
