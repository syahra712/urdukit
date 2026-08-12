"""Urdu ↔ Roman Urdu transliteration.

This is the feature the abandoned ``urduhack`` was asked for twice and never
shipped (its issues #146 and #156, the latter still open and the most recent
report on that tracker).

What "Roman Urdu" means here
----------------------------
Not scholarly ALA-LC romanization with macrons and underdots, but the
everyday Latin-script Urdu that Pakistanis actually text and post in:
``mohabbat``, ``kitab``, ``pakistan``. That is what the requests were asking
for, and it is what downstream code-switching corpora look like.

Why this is hard, stated honestly
---------------------------------
Urdu script under-specifies short vowels. ``کتاب`` is written *k-t-a-b*; the
*i* in ``kitab`` is simply not in the text. Recovering it requires knowing
the word. So this module works in two layers:

1. A lexicon of common words, which is exact.
2. A rule-based fallback with heuristic short-vowel insertion, which is
   approximate and will be wrong on unfamiliar words.

The reverse direction is harder still and genuinely ambiguous: Roman ``s``
can be س, ص or ث, and ``k`` can be ک or ق. :func:`to_urdu` is best-effort
and should be treated as a suggestion, not an answer.

Measured accuracy
-----------------
Exact-match accuracy against ``tests/gold/transliteration_gold.py``:

- Lexicon words: **100%**
- Held-out words, rules only: **25%**

The held-out figure is the honest one, and it is low. Recovering vowels the
script never recorded is not something suffix rules can do well: ``استاد``
is *ustad*, but nothing in ا-س-ت-ا-د says the first vowel is *u*. The
fallback aims at a pronounceable approximation, not a correct answer; the
lexicon is the layer that is actually accurate.

Adding a word to :data:`LEXICON` moves it from ~25% to 100%, which makes
lexicon contributions the highest-leverage change anyone can make here --
and they require Urdu, not familiarity with this codebase.

Use :func:`to_roman` for search normalization, code-switching corpora and
display. Do not use either direction where a wrong character is costly
without checking the result.
"""

from __future__ import annotations

from .normalization import normalize
from .tokenization import word_tokenize

__all__ = ["to_roman", "to_urdu", "LEXICON"]

#: Aspirated consonants: a base consonant followed by ھ (U+06BE HEH
#: DOACHASHMEE). These must be matched before single characters, or ``کھ``
#: romanizes as "kh" only by accident and ``ھ`` leaks through elsewhere.
_ASPIRATES = {
    "بھ": "bh",
    "پھ": "ph",
    "تھ": "th",
    "ٹھ": "th",
    "جھ": "jh",
    "چھ": "chh",
    "دھ": "dh",
    "ڈھ": "dh",
    "رھ": "rh",
    "ڑھ": "rh",
    "کھ": "kh",
    "گھ": "gh",
    "لھ": "lh",
    "مھ": "mh",
    "نھ": "nh",
}

#: Single-character consonant and vowel-carrier mappings.
_CONSONANTS = {
    "ب": "b",
    "پ": "p",
    "ت": "t",
    "ٹ": "t",
    "ث": "s",
    "ج": "j",
    "چ": "ch",
    "ح": "h",
    "خ": "kh",
    "د": "d",
    "ڈ": "d",
    "ذ": "z",
    "ر": "r",
    "ڑ": "r",
    "ز": "z",
    "ژ": "zh",
    "س": "s",
    "ش": "sh",
    "ص": "s",
    "ض": "z",
    "ط": "t",
    "ظ": "z",
    "ع": "",
    "غ": "gh",
    "ف": "f",
    "ق": "q",
    "ک": "k",
    "گ": "g",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "ں": "n",
    "ہ": "h",
    "ھ": "h",
    "ء": "",
    "ؤ": "o",
    "ئ": "y",
    "ۂ": "h",
    "ۓ": "e",
}

#: Vowel carriers, which are context-dependent -- handled in :func:`_romanize`.
_VOWELS = {"ا": "a", "آ": "aa", "و": "o", "ی": "i", "ے": "e"}

#: Diacritics, when a writer has bothered to supply them, are exact.
_DIACRITIC_VOWELS = {
    "َ": "a",  # zabar
    "ِ": "i",  # zer
    "ُ": "u",  # pesh
    "ٰ": "a",  # khari zabar
    "ً": "an",  # do zabar
}

_SHADDA = "ّ"
_SUKUN = "ْ"

#: High-frequency words whose romanization the rules cannot derive, because
#: the short vowels are absent from the script. This layer is exact; the
#: rule-based fallback is not. Extending it is the cheapest way to improve
#: accuracy, and contributions of common words are welcome.
LEXICON: dict[str, str] = {
    # pronouns / function words
    "میں": "mein",
    "ہم": "hum",
    "تم": "tum",
    "آپ": "aap",
    "وہ": "woh",
    "یہ": "yeh",
    "اس": "is",
    "ان": "un",
    "جو": "jo",
    "کون": "kaun",
    "کیا": "kya",
    "کیوں": "kyun",
    "کہاں": "kahan",
    "کب": "kab",
    "کیسے": "kaise",
    "کتنا": "kitna",
    "میرا": "mera",
    "میری": "meri",
    "تمہارا": "tumhara",
    "ہمارا": "hamara",
    "اپنا": "apna",
    # postpositions / conjunctions
    "کا": "ka",
    "کی": "ki",
    "کے": "ke",
    "کو": "ko",
    "نے": "ne",
    "سے": "se",
    "پر": "par",
    "تک": "tak",
    "اور": "aur",
    "یا": "ya",
    "لیکن": "lekin",
    "مگر": "magar",
    "کہ": "keh",
    "اگر": "agar",
    "تو": "to",
    "بھی": "bhi",
    "ہی": "hi",
    "نہ": "na",
    "نہیں": "nahi",
    "ساتھ": "sath",
    "بعد": "baad",
    "پہلے": "pehle",
    "لیے": "liye",
    # verbs / auxiliaries
    "ہے": "hai",
    "ہیں": "hain",
    "تھا": "tha",
    "تھی": "thi",
    "تھے": "the",
    "ہوں": "hun",
    "ہو": "ho",
    "ہوا": "hua",
    "ہوئی": "hui",
    "کرنا": "karna",
    "کرتا": "karta",
    "کرتی": "karti",
    "کرتے": "karte",
    "گیا": "gaya",
    "گئی": "gayi",
    "گئے": "gaye",
    "جانا": "jana",
    "آنا": "aana",
    "دیا": "diya",
    "لیا": "liya",
    "رہا": "raha",
    "رہی": "rahi",
    "رہے": "rahe",
    "سکتا": "sakta",
    "چاہیے": "chahiye",
    # very common nouns / adjectives
    "پاکستان": "pakistan",
    "اردو": "urdu",
    "کتاب": "kitab",
    "کتابیں": "kitabein",
    "گھر": "ghar",
    "پانی": "pani",
    "کھانا": "khana",
    "دوست": "dost",
    "لڑکا": "larka",
    "لڑکی": "larki",
    "آدمی": "aadmi",
    "عورت": "aurat",
    "بچہ": "bacha",
    "شہر": "shehar",
    "ملک": "mulk",
    "دن": "din",
    "رات": "raat",
    "سال": "saal",
    "وقت": "waqt",
    "کام": "kaam",
    "بات": "baat",
    "نام": "naam",
    "زندگی": "zindagi",
    "محبت": "mohabbat",
    "دل": "dil",
    "آنکھ": "aankh",
    "ہاتھ": "hath",
    "اچھا": "acha",
    "برا": "bura",
    "بڑا": "bara",
    "چھوٹا": "chota",
    "نیا": "naya",
    "پرانا": "purana",
    "بہت": "bohat",
    "زیادہ": "zyada",
    "کم": "kam",
    "سب": "sab",
    "کچھ": "kuch",
    "لوگ": "log",
    "اللہ": "allah",
    "سلام": "salam",
    "شکریہ": "shukriya",
    "کراچی": "karachi",
    "لاہور": "lahore",
    "اسلام": "islam",
    "دنیا": "duniya",
    "علم": "ilm",
    "سچ": "sach",
    "جھوٹ": "jhoot",
}

#: Reverse lexicon for Roman -> Urdu. Built from :data:`LEXICON`; where two
#: Urdu words share a romanization the first wins, which is one of several
#: reasons the reverse direction is only a suggestion.
_REVERSE_LEXICON: dict[str, str] = {}
for _urdu, _roman in LEXICON.items():
    _REVERSE_LEXICON.setdefault(_roman, _urdu)

_ROMAN_TO_URDU = {
    "chh": "چھ",
    "kh": "کھ",
    "gh": "گھ",
    "bh": "بھ",
    "ph": "پھ",
    "th": "تھ",
    "jh": "جھ",
    "dh": "دھ",
    "ch": "چ",
    "sh": "ش",
    "aa": "ا",
    "ee": "ی",
    "oo": "و",
    "ai": "ے",
    "au": "و",
    "a": "ا",
    "b": "ب",
    "c": "ک",
    "d": "د",
    "e": "ے",
    "f": "ف",
    "g": "گ",
    "h": "ہ",
    "i": "ی",
    "j": "ج",
    "k": "ک",
    "l": "ل",
    "m": "م",
    "n": "ن",
    "o": "و",
    "p": "پ",
    "q": "ق",
    "r": "ر",
    "s": "س",
    "t": "ت",
    "u": "و",
    "v": "و",
    "w": "و",
    "x": "کس",
    "y": "ی",
    "z": "ز",
}


_ROMAN_VOWELS = set("aeiou")

#: A romanized unit: its text, and whether it acts as a vowel. Tracking this
#: at build time is what lets short-vowel insertion tell a genuine aspirate
#: ("ph" from پھ, one unit) from an accidental consonant pair ("p"+"h" from
#: پ+ہ in پہاڑ, two units) -- they are indistinguishable once flattened to a
#: string, which is why the first version mis-romanized پہاڑ as "phaar".
_Unit = tuple[str, bool]


def _units(word: str) -> list[_Unit]:
    """Map an Urdu word to romanized units, before vowel insertion."""
    out: list[_Unit] = []
    i = 0
    length = len(word)

    while i < length:
        pair = word[i : i + 2]
        if pair in _ASPIRATES:
            out.append((_ASPIRATES[pair], False))
            i += 2
            continue

        char = word[i]
        is_final = i == length - 1

        if char in _DIACRITIC_VOWELS:
            out.append((_DIACRITIC_VOWELS[char], True))
        elif char == _SHADDA:
            if out and out[-1][0]:
                out.append((out[-1][0][-1], False))  # double the consonant
        elif char == _SUKUN:
            pass
        elif char == "ا":
            # Word-initial alef is a bare short vowel; word-final it is short
            # again (لگتا -> lagta); medially it is long.
            out.append(("a" if (i == 0 or is_final) else "aa", True))
        elif char == "آ":
            out.append(("aa", True))
        elif char == "ی":
            out.append(("y" if i == 0 else "i", i != 0))
        elif char == "ے":
            out.append(("e", True))
        elif char == "و":
            out.append(("w" if i == 0 else "o", i != 0))
        elif char == "ہ":
            # Word-final heh goal is the vowel /a/, not /h/: مدرسہ is
            # "madrasa" and دروازہ is "darwaza". Treating it as "h" produced
            # "madrash" and "darwazh".
            if is_final and out:
                out.append(("a", True))
            else:
                out.append(("h", False))
        elif char in _CONSONANTS:
            out.append((_CONSONANTS[char], False))
        else:
            out.append((char, False))
        i += 1

    return [unit for unit in out if unit[0]]


def _romanize_word(word: str) -> str:
    """Romanize a single word by rule, after a failed lexicon lookup."""
    units = _units(word)
    if not units:
        return ""

    out: list[str] = []
    consonant_run = 0
    for text, is_vowel in units:
        if is_vowel or text[0] in _ROMAN_VOWELS:
            consonant_run = 0
            out.append(text)
            continue

        consonant_run += 1
        # Urdu omits short vowels, so a purely mapped word is an
        # unpronounceable cluster (محبت -> "mhbt"). Break runs of three or
        # more with a default "a", leaving word-final clusters alone. This is
        # a heuristic and it is frequently wrong; the lexicon exists for
        # exactly this reason.
        if consonant_run > 1:
            out.append("a")
            consonant_run = 1
        out.append(text)

    return "".join(out)


def to_roman(text: str) -> str:
    """Transliterate Urdu script into everyday Roman Urdu.

        >>> to_roman("میں پاکستان سے ہوں")
        'mein pakistan se hun'

    Known words come from :data:`LEXICON` and are exact. Unknown words fall
    back to rules with heuristic short-vowel insertion and will sometimes be
    wrong; see the module docstring.

    Args:
        text: Urdu text.

    Returns:
        Roman Urdu. Punctuation, digits and Latin runs pass through.
    """
    if not text:
        return text

    pieces: list[str] = []
    for token in word_tokenize(normalize(text)):
        if token in LEXICON:
            pieces.append(LEXICON[token])
        elif token in _PUNCTUATION_TO_LATIN:
            pieces.append(_PUNCTUATION_TO_LATIN[token])
        elif any(c in _CONSONANTS or c in _VOWELS for c in token):
            pieces.append(_romanize_word(token))
        else:
            pieces.append(token)

    return _join_with_punctuation(pieces)


def to_urdu(text: str) -> str:
    """Transliterate Roman Urdu into Urdu script. Best-effort.

        >>> to_urdu("mein pakistan se hun")
        'میں پاکستان سے ہوں'

    Genuinely ambiguous: Roman ``s`` maps to س, ص or ث and ``k`` to ک or ق,
    with no way to choose without knowing the word. Known words are exact;
    everything else is a guess. Always check the output.

    Args:
        text: Roman Urdu text.

    Returns:
        Urdu script.
    """
    if not text:
        return text

    pieces: list[str] = []
    for token in text.split():
        stripped = token.strip(".,!?;:")
        trailing = token[len(stripped) :]
        lowered = stripped.lower()

        if lowered in _REVERSE_LEXICON:
            pieces.append(_REVERSE_LEXICON[lowered] + trailing)
            continue

        out: list[str] = []
        i = 0
        while i < len(lowered):
            for size in (3, 2, 1):
                chunk = lowered[i : i + size]
                if chunk in _ROMAN_TO_URDU:
                    out.append(_ROMAN_TO_URDU[chunk])
                    i += size
                    break
            else:
                out.append(lowered[i])
                i += 1
        pieces.append("".join(out) + trailing)

    return " ".join(pieces)


#: Roman output should carry Latin punctuation, not Urdu marks.
_PUNCTUATION_TO_LATIN = {"۔": ".", "،": ",", "؛": ";", "؟": "?", "٪": "%"}

#: Both scripts' punctuation: to_roman rewrites ؟ to ?, so the Latin forms
#: must be here too or the output reads "hai ?".
_NO_SPACE_BEFORE = set("۔،؛؟!:.,?)]}")


def _join_with_punctuation(pieces: list[str]) -> str:
    """Join tokens with spaces, but keep punctuation tight to its word."""
    out = ""
    for piece in pieces:
        if out and piece and piece[0] not in _NO_SPACE_BEFORE:
            out += " "
        out += piece
    return out
