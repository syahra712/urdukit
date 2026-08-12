"""Stemmer behaviour."""

import pytest

from urdukit import stemming as St


class TestStem:
    @pytest.mark.parametrize(
        "word,expected",
        [
            ("کتابوں", "کتاب"),
            ("کتابیں", "کتاب"),
            ("دوستوں", "دوست"),
            ("مسلمانوں", "مسلمان"),
            ("حالات", "حال"),
            ("آدمی", "آدم"),
        ],
    )
    def test_strips_plural_and_oblique(self, word, expected):
        assert St.stem(word) == expected

    @pytest.mark.parametrize(
        "word,expected",
        [
            ("کرتا", "کر"),
            ("کرتی", "کر"),
            ("کرتے", "کر"),
            ("جاتا", "جا"),
            ("دیکھتا", "دیکھ"),
        ],
    )
    def test_recovers_two_letter_verb_roots(self, word, expected):
        """The regression test for MIN_STEM_LENGTH.

        With a floor of 3, کرتا stemmed to کرت: the correct strip to کر was
        rejected as too short, so a shorter, wrong suffix matched instead.
        """
        assert St.stem(word) == expected

    def test_short_words_untouched(self):
        assert St.stem("دن") == "دن"
        assert St.stem("گھر") == "گھر"

    def test_only_one_suffix_is_removed(self):
        """Repeated stripping over-stems Urdu, since many roots end in ا/ی/ے."""
        assert St.stem("کتابوں") == "کتاب"

    def test_normalizes_before_stemming(self):
        """An Arabic-codepoint spelling must stem to the same thing."""
        assert St.stem("كتابوں") == St.stem("کتابوں")

    def test_min_length_is_configurable(self):
        assert St.stem("کرتا", min_length=5) != "کر"


class TestInflectionGroupsCollapse:
    """The property that actually matters for retrieval."""

    @pytest.mark.parametrize(
        "group",
        [
            ["کتاب", "کتابیں", "کتابوں"],
            ["لڑکا", "لڑکی", "لڑکیاں"],
            ["کرتا", "کرتی", "کرتے"],
            ["اچھا", "اچھی", "اچھے"],
        ],
    )
    def test_group_shares_one_stem(self, group):
        assert len({St.stem(w) for w in group}) == 1


class TestKnownLimitations:
    """Documented gaps, pinned so that fixing them is a deliberate change."""

    def test_proper_nouns_ending_in_common_suffixes_are_over_stemmed(self):
        """کراچی -> کراچ.

        The ی-suffix is far too productive to skip, and distinguishing a
        proper noun needs a lexicon the rule-based stemmer does not have.
        Every rule-based stemmer has this class of error.
        """
        assert St.stem("کراچی") == "کراچ"

    def test_pakistan_survives(self):
        """Guards the removal of the ستان and ان rules, which turned
        پاکستان into پاک."""
        assert St.stem("پاکستان") == "پاکستان"

    def test_irregular_verbs_are_not_lemmatized(self):
        """گیا (went) will not become جانا (to go). This is a stemmer."""
        assert St.stem("گیا") != "جانا"

    def test_broken_plurals_are_not_recovered(self):
        """Arabic broken plurals (کتاب -> کتب) need a dictionary."""
        assert St.stem("کتب") != "کتاب"


class TestStemTokens:
    def test_stems_each_token(self):
        assert St.stem_tokens(["کتابوں", "دوستوں"]) == ["کتاب", "دوست"]

    def test_empty_list(self):
        assert St.stem_tokens([]) == []


class TestSuffixTable:
    def test_longest_first_within_each_group(self):
        """وں must be tried before ں, or the longer suffix never fires."""
        suffixes = St.SUFFIXES
        assert suffixes.index("وں") < suffixes.index("ں")
        if "اں" in suffixes:
            assert suffixes.index("یاں") < suffixes.index("اں")

    def test_destructive_suffixes_are_excluded(self):
        assert "ستان" not in St.SUFFIXES
        assert "ان" not in St.SUFFIXES
