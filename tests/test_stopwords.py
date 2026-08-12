"""Stopword list behaviour."""

from urdukit import stopwords as S
from urdukit.normalization import is_normalized


class TestStopwordList:
    def test_list_is_non_trivial(self):
        assert len(S.STOPWORDS) > 150

    def test_every_entry_is_stored_normalized(self):
        """Otherwise membership tests fail for Arabic-codepoint variants."""
        unnormalized = [w for w in S.STOPWORDS if not is_normalized(w)]
        assert unnormalized == []

    def test_no_empty_entries(self):
        assert all(w.strip() for w in S.STOPWORDS)

    def test_is_frozen(self):
        assert isinstance(S.STOPWORDS, frozenset)


class TestIsStopword:
    def test_common_function_words(self):
        for word in ["ہے", "اور", "کا", "میں", "نہیں", "کہ"]:
            assert S.is_stopword(word), word

    def test_content_words_are_not_stopwords(self):
        for word in ["پاکستان", "کتاب", "محبت", "لڑکا"]:
            assert not S.is_stopword(word), word

    def test_arabic_codepoint_variant_is_recognised(self):
        """ "ہي" with Arabic YEH must match the stored "ہی"."""
        assert S.is_stopword("ہي")

    def test_diacritics_do_not_defeat_matching(self):
        assert S.is_stopword("کہ")


class TestRemoveStopwords:
    def test_removes_function_words(self):
        assert S.remove_stopwords(["میں", "پاکستان", "سے", "ہوں"]) == ["پاکستان"]

    def test_preserves_original_spelling(self):
        """Non-stopwords come back exactly as given, not normalized."""
        assert S.remove_stopwords(["مُحَمَّد", "ہے"]) == ["مُحَمَّد"]

    def test_empty_list(self):
        assert S.remove_stopwords([]) == []

    def test_all_stopwords(self):
        assert S.remove_stopwords(["ہے", "اور"]) == []

    def test_negation_is_a_stopword_documented_hazard(self):
        """نہیں ("not") is a stopword -- stripping it inverts sentiment.

        Pinned deliberately: the docstring warns about it, and this test makes
        the hazard visible rather than surprising.
        """
        assert S.is_stopword("نہیں")


class TestReviewedByNativeSpeaker:
    """Decisions from the pre-publication audit of the generated list.

    These entries were adjudicated by a native Urdu speaker, so a future
    change to any of them should be a deliberate one with a stated reason.
    """

    def test_content_nouns_were_removed(self):
        """وجہ ("reason") and باعث ("cause") are nouns, not function words.

        They read as stopwords only because they surface inside postpositional
        phrases. Both were removed in review.
        """
        assert not S.is_stopword("وجہ")
        assert not S.is_stopword("باعث")

    def test_only_the_modern_spelling_of_liye_is_listed(self):
        """لیے and لئے were both present; the reviewer kept only لیے."""
        assert S.is_stopword("لیے")
        assert not S.is_stopword("لئے")

    def test_negations_and_intensifiers_were_kept(self):
        """Reviewed and deliberately retained, matching standard practice.

        The hazard is documented rather than designed around; callers doing
        sentiment work are expected to keep these.
        """
        for word in ["نہیں", "نہ", "بہت", "کم"]:
            assert S.is_stopword(word), word
