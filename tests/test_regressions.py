"""Regression tests for defects found in the pre-0.2.0 audit.

Each test names the wrong behaviour it replaced, so a future change that
brings one back fails with an explanation rather than a bare diff.
"""

import time

import pytest

import urdukit
from urdukit import characters as C
from urdukit import normalization as N
from urdukit import preprocessing as P
from urdukit import stopwords as S
from urdukit import tokenization as T
from urdukit import transliteration as X

#: Generous enough for a slow CI runner; each of these took 10-60 *seconds*
#: before the fix, so the margin between passing and regressing is ~100x.
_BUDGET_SECONDS = 2.0


def _elapsed(function, argument) -> float:
    start = time.perf_counter()
    function(argument)
    return time.perf_counter() - start


class TestNoQuadraticBlowup:
    """Regexes that restarted from every position inside a long run.

    This is text-cleaning code: it gets pointed at scraped pages, and a
    scraped page with a 50 KB run of spaces is not exotic.
    """

    @pytest.mark.parametrize(
        "function,text",
        [
            (N.normalize, "a" + " " * 50_000 + "b"),
            (N.normalize, "۔" + " " * 50_000 + "x"),
            (N.normalize_punctuation, " " * 50_000),
            (P.replace_urls, "a-" * 20_000),
            (P.replace_emails, "a." * 20_000),
            (P.all_punctuations_space, "a" + " " * 50_000 + "b"),
            (T.word_tokenize, "a." * 30_000),
            (T.word_tokenize, "a-" * 30_000 + "@"),
        ],
    )
    def test_is_linear(self, function, text):
        assert _elapsed(function, text) < _BUDGET_SECONDS


class TestPunctuationDoesNotCorruptText:
    def test_clock_time_is_left_alone(self):
        # Was "12: 30 بجے".
        assert N.normalize("12:30 بجے") == "12:30 بجے"

    def test_url_is_left_alone(self):
        # Was "http: //a.com/x?y=1: 2".
        assert N.normalize("http://a.com/x?y=1:2") == "http://a.com/x?y=1:2"

    def test_urdu_decimal_is_left_alone(self):
        # Was "۵۔ ۲", which the sentence tokenizer then split in two -- the
        # two modules disagreed about what ۵۔۲ was.
        assert N.normalize("قیمت ۵۔۲ ہے") == "قیمت ۵۔۲ ہے"
        assert T.sentence_tokenize(N.normalize("قیمت ۵۔۲ ہے۔")) == ["قیمت ۵۔۲ ہے۔"]

    def test_closing_quote_stays_attached(self):
        # Was 'چلو۔ "', detaching the quote from the sentence it closes.
        text = 'اس نے کہا "چلو۔" ہم چلے۔'
        assert N.normalize(text) == text

    def test_number_then_sentence_still_gets_its_space(self):
        assert N.normalize("2026۔اگلا سال") == "2026۔ اگلا سال"

    def test_ordinary_repair_still_happens(self):
        assert N.normalize("نام:احمد ۔ٹھیک") == "نام: احمد۔ ٹھیک"


class TestTokenizerKeepsWordsWhole:
    def test_unnormalized_arabic_codepoints(self):
        # Was ['عل', 'ي', 'ك', 'تاب']: tokenizing depended on normalizing.
        assert T.word_tokenize("علي كتاب") == ["علي", "كتاب"]

    def test_teh_marbuta_goal(self):
        # ۃ was missing from the inventory; 78 words in Dakshina split on it.
        assert T.word_tokenize("سورۃ البقرۃ") == ["سورۃ", "البقرۃ"]
        assert C.is_urdu_character("ۃ")

    def test_honorific_sign_stays_on_its_word(self):
        assert T.word_tokenize("محمدؐ نے") == ["محمدؐ", "نے"]

    def test_tatweel_is_not_a_boundary(self):
        assert T.word_tokenize("کـتاب") == ["کـتاب"]

    def test_url_is_one_token(self):
        # Was 14 tokens of punctuation.
        assert T.word_tokenize("دیکھیں https://example.com/a?b=1۔") == [
            "دیکھیں",
            "https://example.com/a?b=1",
            "۔",
        ]

    def test_url_does_not_swallow_closing_punctuation(self):
        assert T.word_tokenize("(www.x.pk).") == ["(", "www.x.pk", ")", "."]

    def test_email_is_one_token(self):
        assert T.word_tokenize("میل a.b+c@x.co.uk۔") == ["میل", "a.b+c@x.co.uk", "۔"]

    def test_accented_latin(self):
        assert T.word_tokenize("café naïve") == ["café", "naïve"]

    def test_known_word_is_never_split(self):
        # بلبل (nightingale) is not بل + بل even when both halves are known.
        vocabulary = {"بل", "بلبل"}
        assert T.word_tokenize("بلبل", recover_spaces=True, known_words=vocabulary) == [
            "بلبل"
        ]


class TestArabicIndicDigits:
    """٠-٩ were handled by normalize and the tokenizer but not by these."""

    def test_replace_numbers(self):
        assert P.replace_numbers("٣٤ کتابیں") == "<NUMBER> کتابیں"

    def test_digits_space(self):
        assert P.digits_space("سال٢٠٢٦میں") == "سال ٢٠٢٦ میں"


class TestStopwords:
    @pytest.mark.parametrize(
        "word", ["مجھے", "ہمیں", "انہیں", "اسے", "یہی", "وہی", "وغیرہ", "جبکہ"]
    )
    def test_oblique_pronouns_and_connectives(self, word):
        assert S.is_stopword(word)

    def test_readme_example(self):
        # The README's own example kept مجھے ("to me") as a content word.
        tokens = T.word_tokenize(
            "مجھے کتابیں پڑھنا اچھا لگتا ہے", keep_punctuation=False
        )
        assert S.remove_stopwords(tokens) == ["کتابیں", "پڑھنا", "اچھا", "لگتا"]


class TestToRoman:
    def test_aerab_are_used_not_discarded(self):
        # Was "mahamad": normalize() stripped the marks before the rules
        # could read them, so the diacritic-vowel table was dead code.
        assert X.to_roman("مُحَمَّد") == "muhammad"

    def test_marked_homographs(self):
        assert X.to_roman("اِس اُس اِن اُن") == "is us in un"

    def test_alef_is_only_a_seat_for_its_vowel(self):
        assert X.to_roman("اُمید").startswith("um")

    @pytest.mark.parametrize(
        "urdu,roman", [("علی", "ali"), ("عام", "aam"), ("معاف", "maf")]
    )
    def test_ain_carries_a_vowel(self, urdu, roman):
        # علی was "li": ain was dropped along with the vowel it carries.
        assert X.to_roman(urdu) == roman

    def test_brackets_and_percent_are_tight(self):
        # Was "( salam)" and "50 %".
        assert X.to_roman("(سلام)") == "(salam)"
        assert X.to_roman("50٪") == "50%"

    def test_digits_come_out_ascii(self):
        assert X.to_roman("۲۰۲۶ میں") == "2026 mein"

    def test_honorific_sign_is_silent(self):
        assert X.to_roman("محمدؐ") == X.to_roman("محمد")

    def test_space_recovery_is_opt_in(self):
        # کاجو is "cashew", not کا + جو. On by default this wrongly split
        # 1.2% of real single words and lowered benchmark accuracy.
        assert " " not in X.to_roman("کاجو")
        assert X.to_roman("کتابہے", recover_spaces=True) == "kitab hai"

    def test_loanwords_are_english_words(self):
        # اخبار / جہاز / وزیر were filed here; they are not English.
        for roman in ("akhbar", "jahaz", "wazir"):
            assert roman not in X.LOANWORDS.values()
            assert roman in X.LEXICON.values()


class TestToUrdu:
    def test_loanwords_round_trip(self):
        # Was 'دوکتور ونیوےرسیتی': the reverse table ignored LOANWORDS.
        assert X.to_urdu("doctor university") == "ڈاکٹر یونیورسٹی"

    def test_punctuation_is_converted(self):
        assert X.to_urdu("kya hai?") == "کیا ہے؟"
        assert X.to_urdu("shukriya, dost.") == "شکریہ، دوست۔"

    def test_leading_punctuation(self):
        assert X.to_urdu("(kitab)") == "(کتاب)"

    def test_punctuation_only_token(self):
        assert X.to_urdu("kitab ?") == "کتاب ؟"


class TestPackaging:
    def test_version_is_single_sourced(self):
        from importlib import metadata

        try:
            installed = metadata.version("urdukit")
        except metadata.PackageNotFoundError:
            pytest.skip("urdukit is not installed")
        assert installed == urdukit.__version__

    def test_ships_type_marker(self):
        # pyproject declares "Typing :: Typed"; without py.typed that
        # classifier is false and type checkers ignore the annotations.
        from importlib import resources

        assert resources.files("urdukit").joinpath("py.typed").is_file()
