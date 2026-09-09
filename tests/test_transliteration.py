"""Transliteration behaviour and measured accuracy."""

import pytest
from gold.transliteration_gold import HELD_OUT, IN_LEXICON

from urdukit import transliteration as X


class TestToRoman:
    @pytest.mark.parametrize("urdu,roman", sorted(IN_LEXICON.items()))
    def test_lexicon_words_are_exact(self, urdu, roman):
        assert X.to_roman(urdu) == roman

    def test_sentence(self):
        assert X.to_roman("میں پاکستان سے ہوں۔") == "mein pakistan se hun."

    def test_urdu_punctuation_becomes_latin(self):
        assert X.to_roman("یہ کیا ہے؟") == "yeh kya hai?"

    def test_no_space_before_punctuation(self):
        assert " ." not in X.to_roman("شکریہ دوست۔")

    def test_empty_input(self):
        assert X.to_roman("") == ""

    @pytest.mark.parametrize(
        "urdu,roman",
        [("کھانا", "khana"), ("گھر", "ghar"), ("چھوٹا", "chota")],
    )
    def test_aspirates(self, urdu, roman):
        assert X.to_roman(urdu) == roman

    def test_aspirate_is_not_confused_with_consonant_plus_heh(self):
        """پہاڑ is پ+ہ ("pahar"), not the پھ aspirate ("phar").

        Regression test: the first implementation flattened units to a string
        before inserting vowels, which made the two indistinguishable. The
        property under test is the p-a-h split, not the exact vowels.
        """
        result = X.to_roman("پہاڑ")
        assert result.startswith("pah")
        assert not result.startswith("ph")

    def test_word_final_heh_is_a_vowel(self):
        """مدرسہ ends in the vowel /a/, not /h/ -- "madarasa", never "madarash"."""
        assert X.to_roman("بچہ") == "bacha"
        assert not X.to_roman("مدرسہ").endswith("h")

    def test_output_is_pronounceable(self):
        """Every rule-based output must contain a vowel.

        This is the property the fallback actually guarantees. An earlier,
        higher-scoring heuristic produced "smndr" for سمندر: better on exact
        match, useless to a reader.
        """
        for urdu in HELD_OUT:
            roman = X.to_roman(urdu)
            assert any(c in "aeiou" for c in roman), f"{urdu} -> {roman}"


class TestLexiconAdditions:
    """New LEXICON entries for common words the fallback can't reliably
    guess (family, everyday nouns, nature). See issue #1.

    ``برف``, ``استاد`` and ``بارش`` are deliberately not added here even
    though issue #1 lists them: they're reserved in
    ``tests/gold/transliteration_gold.py``'s HELD_OUT set to measure the
    rule-based fallback honestly, and moving them out of that set is a
    separate call for the maintainer, not something to bundle silently into
    a lexicon PR.
    """

    @pytest.mark.parametrize(
        "urdu,roman",
        [
            ("ماں", "maa"),
            ("باپ", "baap"),
            ("بھائی", "bhai"),
            ("بہن", "behan"),
            ("بچے", "bachay"),
            ("والد", "walid"),
            ("والدہ", "walida"),
            ("علاقہ", "ilaka"),
            ("سڑک", "sarak"),
            ("گاڑی", "gaari"),
            ("جگہ", "jagah"),
            ("چیز", "cheez"),
            ("درخت", "darakht"),
            ("پھول", "phool"),
            ("سورج", "suraj"),
            ("چاند", "chand"),
            ("ستارہ", "sitara"),
            ("آسمان", "aasman"),
            ("زمین", "zameen"),
            ("آگ", "aag"),
            ("موسم", "mausam"),
            ("طالب", "talib"),
        ],
    )
    def test_new_words(self, urdu, roman):
        assert X.LEXICON[urdu] == roman
        assert X.to_roman(urdu) == roman

    def test_school_and_college_already_covered_by_loanwords(self):
        """Both were on issue #1's list but are already handled as
        loanwords (``اسکول``/``سکول`` -> school, ``کالج`` -> college), so
        they're not duplicated into LEXICON."""
        assert X.to_roman("سکول") == "school"
        assert X.to_roman("کالج") == "college"

    def test_held_out_words_are_not_added(self):
        """See the class docstring: these three stay out of LEXICON."""
        for word in ("برف", "استاد", "بارش"):
            assert word not in X.LEXICON


class TestLoanwords:
    """English loanwords written in Urdu script.

    These romanize to their English spelling, which no phonetic rule can
    derive. The table is far more trustworthy than LEXICON because the
    target is an English word rather than a judgement call about Roman Urdu
    spelling.
    """

    @pytest.mark.parametrize(
        "urdu,english",
        [
            ("آرمی", "army"),
            ("آرگن", "organ"),
            ("آرگنائزیشن", "organisation"),
            ("کمپیوٹر", "computer"),
            ("انٹرنیٹ", "internet"),
            ("پولیس", "police"),
            ("یونیورسٹی", "university"),
            ("کرکٹ", "cricket"),
        ],
    )
    def test_known_loanwords(self, urdu, english):
        assert X.to_roman(urdu) == english

    def test_rules_alone_would_fail_these(self):
        """Without the table, آرمی romanizes to nonsense like "aarami"."""
        from urdukit.normalization import normalize

        assert X._romanize_word(normalize("آرمی")) != "army"

    def test_no_multi_word_keys(self):
        """Lookup happens after tokenization, so a two-token key never fires."""
        assert [k for k in X.LOANWORDS if " " in k] == []

    def test_lexicon_wins_over_loanwords(self):
        """A word in both tables must resolve via LEXICON."""
        overlap = set(X.LEXICON) & set(X.LOANWORDS)
        for word in overlap:
            assert X.to_roman(word) == X.LEXICON[word]

    def test_values_are_plausible_english(self):
        import re

        odd = [(k, v) for k, v in X.LOANWORDS.items() if not re.fullmatch(r"[a-z]+", v)]
        assert odd == []

    @pytest.mark.parametrize(
        "urdu,english",
        [
            ("چیک", "cheque"),
            ("کریڈٹ", "credit"),
            ("اکاؤنٹ", "account"),
            ("انشورنس", "insurance"),
            ("ویزا", "visa"),
            ("کرنسی", "currency"),
            ("کلینک", "clinic"),
            ("انجکشن", "injection"),
            ("آپریشن", "operation"),
            ("کینسر", "cancer"),
            ("وائرس", "virus"),
            ("ویکسین", "vaccine"),
            ("نرس", "nurse"),
            ("جج", "judge"),
            ("اپیل", "appeal"),
            ("لائسنس", "license"),
            ("ڈگری", "degree"),
            ("کورس", "course"),
            ("لیکچرر", "lecturer"),
            ("براؤزر", "browser"),
        ],
    )
    def test_new_coverage_categories(self, urdu, english):
        """New entries across finance, medicine, law, and education/tech --
        the categories issue #4's follow-up comment flagged as missing."""
        assert X.to_roman(urdu) == english


class TestPhraseLoanwords:
    """Multi-word English loanwords written as two Urdu tokens.

    LOANWORDS can't hold these -- lookup happens per-token after
    tokenization, so a key with a space could never match. See issue #4.
    """

    @pytest.mark.parametrize(
        "urdu,english",
        [
            ("ویب سائٹ", "website"),
            ("ای میل", "email"),
            ("ٹی وی", "tv"),
            ("لیپ ٹاپ", "laptop"),
        ],
    )
    def test_known_phrases(self, urdu, english):
        assert X.to_roman(urdu) == english

    def test_no_single_word_keys(self):
        assert all(" " in k for k in X.PHRASE_LOANWORDS)

    def test_phrase_in_a_sentence(self):
        assert X.to_roman("میری ویب سائٹ اچھی ہے") == "meri website achhi hai"

    def test_component_tokens_alone_still_resolve(self):
        """A phrase match must not swallow tokens it doesn't recognise --
        splitting "ویب سائٹ پر" should only combine the first two."""
        result = X.to_roman("ویب سائٹ پر")
        assert result.startswith("website")


class TestSpaceRecovery:
    """to_roman recovers an omitted space when the halves are known words.

    Exercises the word_tokenize(recover_spaces=True) integration wired up
    for issue #3, through the public to_roman API.
    """

    def test_recovers_lexicon_word_glued_to_auxiliary(self):
        assert X.to_roman("کتابہے") == "kitab hai"

    def test_recovers_in_a_longer_sentence(self):
        assert X.to_roman("یہ میری کتابہے") == "yeh meri kitab hai"


class TestToUrdu:
    def test_lexicon_round_trip(self):
        for urdu, roman in X.LEXICON.items():
            assert X.to_urdu(roman) == urdu, f"{roman} -> {X.to_urdu(roman)} != {urdu}"

    def test_sentence(self):
        assert X.to_urdu("mein pakistan se hun") == "میں پاکستان سے ہوں"

    def test_empty_input(self):
        assert X.to_urdu("") == ""

    def test_unknown_word_falls_back_to_rules(self):
        assert X.to_urdu("zzz")  # produces something rather than crashing


class TestMeasuredAccuracy:
    """Pins the published numbers so a regression is visible, not silent."""

    def test_lexicon_accuracy_is_total(self):
        hits = sum(1 for u, r in IN_LEXICON.items() if X.to_roman(u) == r)
        assert hits == len(IN_LEXICON)

    def test_held_out_smoke_check(self):
        """A cheap offline floor -- **not** the accuracy benchmark.

        The real number comes from ``scripts/benchmark_dakshina.py`` against
        2,500 held-out words. This 24-word set was hand-written by the author
        before that benchmark existed, so measuring accuracy on it means
        grading against one person's guesses; Dakshina showed 4 of those
        guesses were spellings nobody actually uses.

        It survives only as a network-free smoke check that the romanizer has
        not collapsed. Do not quote this figure anywhere.
        """
        hits = sum(1 for u, r in HELD_OUT.items() if X.to_roman(u) == r)
        assert hits >= 4, f"romanizer may have regressed: only {hits} gold hits"

    def test_pronoun_family_romanizes_consistently(self):
        """ہم is "hum", so ہمارا must be "humara", not "hamara".

        Both spellings are defensible alone; together they were incoherent.
        Resolved in the native-speaker review in favour of a consistent u.
        """
        assert X.LEXICON["ہم"] == "hum"
        assert X.LEXICON["ہمارا"] == "humara"
        assert X.LEXICON["ہمارا"].startswith(X.LEXICON["ہم"])

    def test_reviewer_corrections_are_applied(self):
        """کیسے is "kese", not the "kaise" originally generated.

        Found by spot-check: 1 wrong in 12 sampled romanizations.
        """
        assert X.LEXICON["کیسے"] == "kese"

    def test_house_style_is_single_consonants(self):
        """Reviewed and confirmed: acha, not achha; chota, not chhota.

        The aspirate contrast that ھ marks is deliberately not doubled in
        Roman, matching how the words are actually typed.
        """
        assert X.LEXICON["اچھا"] == "acha"
        assert X.LEXICON["چھوٹا"] == "chota"
        assert X.LEXICON["بچہ"] == "bacha"

    def test_gold_held_out_set_is_not_contaminated(self):
        """A held-out word that leaks into the lexicon inflates the score.

        بچہ did exactly that on the first run.
        """
        leaked = [w for w in HELD_OUT if w in X.LEXICON]
        assert leaked == []
