"""Urdu stopwords.

A curated list of high-frequency function words: postpositions, pronouns,
auxiliaries, conjunctions and the light-verb forms that carry grammatical
rather than lexical meaning.

The list is stored normalized (see :mod:`urdukit.normalization`) so that
membership tests are not defeated by Arabic codepoints or stray diacritics.
:func:`is_stopword` normalizes its argument before testing, so callers do not
have to.

A caution that applies to every stopword list: removing these is helpful for
retrieval and topic modelling and actively harmful for tasks that depend on
syntax or negation. ``نہیں`` ("not") is in this list; strip it before
sentiment analysis and you invert your labels.
"""

from __future__ import annotations

from .normalization import normalize

__all__ = ["STOPWORDS", "is_stopword", "remove_stopwords"]

_RAW_STOPWORDS = """
کا کی کے کو نے سے میں پر تک ساتھ لیے بعد پہلے دوران بغیر سوا علاوہ
بارے مطابق ذریعے خلاف طرف جانب اوپر نیچے اندر باہر آگے پیچھے
درمیان سامنے قریب دور
ہے ہیں تھا تھی تھے تھیں ہوں ہو ہوا ہوئی ہوئے ہوتا ہوتی ہوتے ہونا رہا رہی
رہے رہتا رہتی رہتے گا گی گے چاہیے سکتا سکتی سکتے لگا لگی لگے دیا دی دیے
لیا لی لیں کیا کیے کیں گیا گئی گئے
اور یا لیکن مگر کہ اگر تو پھر بھی ہی نہ نہیں جو جس جن جب تب کیونکہ تاکہ
حالانکہ بلکہ ورنہ چونکہ اگرچہ نیز یعنی
یہ وہ اس ان ایک میرا میری میرے ہمارا ہماری ہمارے تمہارا تمہاری تمہارے
آپ ہم تم اپنا اپنی اپنے خود کوئی کچھ سب سبھی ہر تمام دونوں
کون کیوں کہاں کب کیسے کتنا کتنی کتنے کونسا کونسی کونسے
یہاں وہاں جہاں کہیں اب ابھی آج کل پرسوں ہمیشہ کبھی اکثر شاید ضرور
بہت زیادہ کم تھوڑا تھوڑی تھوڑے بس صرف تقریبا لگ بھگ البتہ مثلا
والا والی والے طرح جیسے جیسا جیسی ویسے ایسا ایسی ایسے
کر کرنا کرتا کرتی کرتے کریں کرے کرو
"""

#: Frozen set of normalized Urdu stopwords.
STOPWORDS: frozenset[str] = frozenset(
    normalize(word) for word in _RAW_STOPWORDS.split() if word
)


def is_stopword(word: str) -> bool:
    """Return ``True`` if *word* is an Urdu stopword.

    The word is normalized before the test, so Arabic-codepoint and
    diacritic variants are recognised.

        >>> is_stopword("ہے")
        True
        >>> is_stopword("پاکستان")
        False
    """
    return normalize(word) in STOPWORDS


def remove_stopwords(tokens: list[str]) -> list[str]:
    """Drop stopwords from a token list, preserving the original spellings.

    Args:
        tokens: Tokens, e.g. from :func:`urdukit.word_tokenize`.

    Returns:
        The tokens that are not stopwords, exactly as they were given.

        >>> remove_stopwords(["میں", "پاکستان", "سے", "ہوں"])
        ['پاکستان']
    """
    return [token for token in tokens if not is_stopword(token)]
