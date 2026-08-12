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
        """پہاڑ is پ+ہ (two units, "pahaar"), not the پھ aspirate ("phaar").

        Regression test: the first implementation flattened units to a string
        before inserting vowels, which made the two indistinguishable.
        """
        assert X.to_roman("پہاڑ") == "pahaar"

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

    def test_held_out_accuracy_does_not_regress(self):
        """The README and module docstring both claim 25%.

        Asserted as a floor: improvements are welcome, silent regressions are
        not. Raise this number when you raise the real one.
        """
        hits = sum(1 for u, r in HELD_OUT.items() if X.to_roman(u) == r)
        accuracy = hits / len(HELD_OUT)
        assert accuracy >= 0.25, f"held-out accuracy fell to {accuracy:.1%}"

    def test_pronoun_family_romanizes_consistently(self):
        """ہم is "hum", so ہمارا must be "humara", not "hamara".

        Both spellings are defensible alone; together they were incoherent.
        Resolved in the native-speaker review in favour of a consistent u.
        """
        assert X.LEXICON["ہم"] == "hum"
        assert X.LEXICON["ہمارا"] == "humara"
        assert X.LEXICON["ہمارا"].startswith(X.LEXICON["ہم"])

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
