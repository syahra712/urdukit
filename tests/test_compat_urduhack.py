"""The urduhack compatibility shim.

These tests assert that code written against urduhack's public API keeps
working after changing only the import line.
"""

import pytest

import urdukit.compat.urduhack as uh


class TestApiSurface:
    def test_exports_the_documented_urduhack_names(self):
        """Every name urduhack's own __all__ lists, minus the model API."""
        expected = {
            "normalize",
            "normalize_characters",
            "normalize_combine_characters",
            "remove_diacritics",
            "replace_digits",
            "sentence_tokenizer",
            "word_tokenizer",
            "STOP_WORDS",
            "remove_stopwords",
            "URDU_ALPHABETS",
            "URDU_DIGITS",
            "URDU_PUNCTUATIONS",
            "URDU_DIACRITICS",
            "URDU_ALL_CHARACTERS",
            "normalize_whitespace",
            "replace_urls",
            "replace_emails",
            "replace_numbers",
            "replace_phone_numbers",
            "digits_space",
            "english_characters_space",
            "all_punctuations_space",
            "preprocess",
        }
        missing = expected - set(dir(uh))
        assert missing == set()


class TestNormalization:
    def test_normalize(self):
        assert uh.normalize("مُحَمَّد علي") == "محمد علی"

    def test_normalize_characters(self):
        assert uh.normalize_characters("علي") == "علی"

    def test_remove_diacritics(self):
        assert uh.remove_diacritics("مُحَمَّد") == "محمد"

    def test_replace_digits_defaults_to_english(self):
        """urduhack's default is with_english=True."""
        assert uh.replace_digits("۲۰۲۶") == "2026"

    def test_replace_digits_to_urdu(self):
        assert uh.replace_digits("2026", with_english=False) == "۲۰۲۶"


class TestTokenization:
    def test_sentence_tokenizer(self):
        assert uh.sentence_tokenizer("سلام۔ دنیا۔") == ["سلام۔", "دنیا۔"]

    def test_word_tokenizer(self):
        assert uh.word_tokenizer("میں پاکستان سے ہوں") == [
            "میں",
            "پاکستان",
            "سے",
            "ہوں",
        ]


class TestStopWords:
    def test_stop_words_is_a_frozenset(self):
        assert isinstance(uh.STOP_WORDS, frozenset)
        assert "ہے" in uh.STOP_WORDS

    def test_remove_stopwords_takes_and_returns_a_string(self):
        """urduhack's signature is str -> str, unlike urdukit's list -> list.

        Getting this wrong would break every existing caller silently.
        """
        result = uh.remove_stopwords("میں پاکستان سے ہوں")
        assert isinstance(result, str)
        assert result == "پاکستان"


class TestCharacterSets:
    def test_alphabets_include_hamza_forms(self):
        assert "ا" in uh.URDU_ALPHABETS
        assert "ئ" in uh.URDU_ALPHABETS

    def test_digits(self):
        assert uh.URDU_DIGITS == frozenset("۰۱۲۳۴۵۶۷۸۹")

    def test_diacritics_are_more_complete_than_the_original(self):
        """urduhack listed 6 combining marks; there are 21."""
        assert len(uh.URDU_DIACRITICS) > 6

    def test_all_characters_is_the_union(self):
        assert uh.URDU_DIGITS <= uh.URDU_ALL_CHARACTERS
        assert uh.URDU_PUNCTUATIONS <= uh.URDU_ALL_CHARACTERS


class TestPreprocessing:
    def test_normalize_whitespace(self):
        assert uh.normalize_whitespace("سلام    دنیا") == "سلام دنیا"

    def test_replace_urls(self):
        assert "<URL>" in uh.replace_urls("دیکھیں https://example.com")

    def test_preprocess(self):
        assert uh.preprocess("میںcomputerسے") == "میں computer سے"


class TestUnsupportedModelApi:
    @pytest.mark.parametrize("name", ["Pipeline", "CoNLL", "download"])
    def test_raises_with_an_explanation(self, name):
        with pytest.raises(NotImplementedError, match=r"TensorFlow|downloads"):
            getattr(uh, name)()

    def test_error_points_somewhere_useful(self):
        with pytest.raises(NotImplementedError, match="stanza"):
            uh.Pipeline()


class TestMigrationStory:
    def test_module_can_stand_in_for_urduhack(self):
        """`import urdukit.compat.urduhack as urduhack` must just work."""
        import urdukit.compat.urduhack as urduhack

        text = "مُحَمَّد علي كتاب۔"
        assert urduhack.normalize(text)
        assert urduhack.sentence_tokenizer(text)
        assert urduhack.word_tokenizer(text)

    def test_shim_imports_without_heavy_dependencies(self):
        import os
        import pathlib
        import subprocess
        import sys

        src = pathlib.Path(__file__).resolve().parent.parent / "src"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys, urdukit.compat.urduhack; "
                "print(sorted({'tensorflow','torch','numpy'} & set(sys.modules)))",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(src)},
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "[]"
