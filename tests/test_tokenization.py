"""Tokenization behaviour."""

from urdukit import tokenization as T


class TestSentenceTokenize:
    def test_splits_on_urdu_full_stop(self):
        assert T.sentence_tokenize("سلام۔ دنیا۔") == ["سلام۔", "دنیا۔"]

    def test_splits_on_question_mark(self):
        assert T.sentence_tokenize("آپ کیسے ہیں؟ میں ٹھیک ہوں۔") == [
            "آپ کیسے ہیں؟",
            "میں ٹھیک ہوں۔",
        ]

    def test_keeps_terminator_attached(self):
        for sentence in T.sentence_tokenize("ایک۔ دو؟ تین!"):
            assert sentence[-1] in "۔؟!"

    def test_final_sentence_without_terminator(self):
        assert T.sentence_tokenize("سلام۔ دنیا") == ["سلام۔", "دنیا"]

    def test_decimal_does_not_split(self):
        """A terminator between digits is a decimal point, not a boundary."""
        assert len(T.sentence_tokenize("۵۔۲ فیصد اضافہ ہوا۔")) == 1

    def test_ellipsis_does_not_split_midway(self):
        assert T.sentence_tokenize("سلام۔۔۔ دنیا۔") == ["سلام۔۔۔", "دنیا۔"]

    def test_closing_quote_stays_with_sentence(self):
        result = T.sentence_tokenize('اس نے کہا "سلام۔" پھر وہ چلا گیا۔')
        assert result[0].endswith('"')

    def test_empty_input(self):
        assert T.sentence_tokenize("") == []
        assert T.sentence_tokenize("   ") == []

    def test_no_terminator_at_all(self):
        assert T.sentence_tokenize("سلام دنیا") == ["سلام دنیا"]

    def test_splits_without_space_after_terminator(self):
        """Omitting the space after ۔ is endemic in real Urdu text.

        The tokenizer must not depend on the punctuation normalizer having
        run first.
        """
        assert T.sentence_tokenize("ایک۔دو۔تین۔") == ["ایک۔", "دو۔", "تین۔"]

    def test_number_before_terminator_still_splits(self):
        """A digit before ۔ is only a decimal if a digit also follows it."""
        assert T.sentence_tokenize("یہ 2026۔ اگلا سال آئے گا۔") == [
            "یہ 2026۔",
            "اگلا سال آئے گا۔",
        ]

    def test_ascii_period_is_not_a_boundary(self):
        """Splitting on '.' would shatter URLs and English abbreviations."""
        assert T.sentence_tokenize("example.com دیکھیں۔") == ["example.com دیکھیں۔"]

    def test_mixed_terminators_group_together(self):
        assert T.sentence_tokenize("کیا؟! واقعی؟") == ["کیا؟!", "واقعی؟"]


class TestWordTokenize:
    def test_basic_split(self):
        assert T.word_tokenize("میں پاکستان سے ہوں") == [
            "میں",
            "پاکستان",
            "سے",
            "ہوں",
        ]

    def test_separates_trailing_full_stop(self):
        assert T.word_tokenize("سلام۔") == ["سلام", "۔"]

    def test_punctuation_can_be_dropped(self):
        assert T.word_tokenize("سلام، دنیا۔", keep_punctuation=False) == [
            "سلام",
            "دنیا",
        ]

    def test_urdu_digits_stay_together(self):
        assert T.word_tokenize("۲۰۲۶") == ["۲۰۲۶"]

    def test_ascii_digits_stay_together(self):
        assert T.word_tokenize("2026") == ["2026"]

    def test_decimal_stays_one_token(self):
        assert T.word_tokenize("۵٫۲") == ["۵٫۲"]

    def test_latin_code_switching(self):
        """Mixed Urdu/English is the norm, not the exception."""
        assert T.word_tokenize("میں computer استعمال کرتا ہوں") == [
            "میں",
            "computer",
            "استعمال",
            "کرتا",
            "ہوں",
        ]

    def test_zwnj_does_not_split_a_word(self):
        assert T.word_tokenize("کام‌کاج") == ["کام‌کاج"]

    def test_diacritics_stay_with_their_letter(self):
        assert T.word_tokenize("مُحَمَّد") == ["مُحَمَّد"]

    def test_empty_input(self):
        assert T.word_tokenize("") == []

    def test_collapses_extra_whitespace(self):
        assert T.word_tokenize("سلام    دنیا") == ["سلام", "دنیا"]

    def test_documented_limitation_omitted_space(self):
        """We do not recover omitted spaces -- this is a known, documented gap.

        ``کتابہے`` should be ``کتاب ہے``. Splitting it needs a lexicon, so the
        rule-based tokenizer leaves it alone. This test pins the *current*
        behaviour so that adding lexicon-based splitting later is a visible,
        deliberate change rather than a silent one.
        """
        assert T.word_tokenize("کتابہے") == ["کتابہے"]


class TestRecoverSpaces:
    """Opt-in recovery of an omitted space via lexicon-based splitting.

    Off by default -- see ``test_documented_limitation_omitted_space`` above,
    which is unaffected by any of this. See issue #3.
    """

    def test_default_vocabulary_alone_may_not_recover_content_words(self):
        """ "کتاب" is a content word, not a stopword, so recover_spaces alone
        (without a richer known_words) does not split "کتابہے" -- to_roman
        passes a richer vocabulary for exactly this reason.
        """
        assert T.word_tokenize("کتابہے", recover_spaces=True) == ["کتابہے"]

    def test_unrelated_glued_token_is_untouched(self):
        assert T.word_tokenize("ذرہذرہ", recover_spaces=True) == ["ذرہذرہ"]

    def test_recovers_with_explicit_vocabulary(self):
        assert T.word_tokenize(
            "کتابہے", recover_spaces=True, known_words={"کتاب", "ہے"}
        ) == ["کتاب", "ہے"]

    def test_default_vocabulary_is_stopwords(self):
        """دور ("far") and ہے ("is") are both stopwords; splits without help."""
        assert T.word_tokenize("دورہے", recover_spaces=True) == ["دور", "ہے"]

    def test_ambiguous_split_is_left_alone(self):
        """ "دورہے" could be "دو" + "رہے" (two + stay) or "دور" + "ہے" (far + is).

        Two valid splits means neither is safe to guess -- the token is left
        untouched rather than picking one arbitrarily.
        """
        vocab = {"دو", "رہے", "دور", "ہے"}
        assert T.word_tokenize("دورہے", recover_spaces=True, known_words=vocab) == [
            "دورہے"
        ]

    def test_short_token_is_untouched(self):
        assert T.word_tokenize("و", recover_spaces=True, known_words={"و"}) == ["و"]

    def test_recover_spaces_false_ignores_known_words(self):
        assert T.word_tokenize(
            "کتابہے", recover_spaces=False, known_words={"کتاب", "ہے"}
        ) == ["کتابہے"]


class TestNonJoiningLetters:
    def test_set_contents(self):
        assert T.NON_JOINING_LETTERS == frozenset("ادڈذرڑزژوے")

    def test_all_are_urdu_letters(self):
        from urdukit.characters import URDU_LETTERS

        assert T.NON_JOINING_LETTERS <= URDU_LETTERS
