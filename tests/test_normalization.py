"""Normalization behaviour.

Tests tagged with an issue number reproduce a real, still-open report on the
abandoned ``urduhack`` tracker. They are the specification for this library.
"""

import pytest

from urdukit import normalization as N


class TestFoldArabic:
    def test_arabic_yeh_becomes_farsi_yeh(self):
        assert N.fold_arabic("علي") == "علی"

    def test_arabic_kaf_becomes_keheh(self):
        assert N.fold_arabic("كتاب") == "کتاب"

    def test_arabic_heh_becomes_heh_goal(self):
        assert N.fold_arabic("ه") == "ہ"

    def test_teh_marbuta_becomes_heh_goal(self):
        assert N.fold_arabic("ة") == "ہ"

    def test_visually_identical_strings_compare_equal_after_folding(self):
        """The bug this library exists to fix."""
        arabic_spelling = "علي"
        urdu_spelling = "علی"
        assert arabic_spelling != urdu_spelling
        assert N.fold_arabic(arabic_spelling) == N.fold_arabic(urdu_spelling)

    def test_is_idempotent(self):
        once = N.fold_arabic("كتاب علي")
        assert N.fold_arabic(once) == once


class TestDiacritics:
    def test_removes_aerab(self):
        assert N.remove_diacritics("مُحَمَّد") == "محمد"

    def test_leaves_undiacriticised_text_alone(self):
        assert N.remove_diacritics("محمد") == "محمد"

    def test_removes_khari_zabar(self):
        assert N.remove_diacritics("اللٰہ") == "اللہ"


class TestLigatures:
    def test_allah_ligature_expands_with_urdu_heh(self):
        """urduhack #141."""
        assert N.expand_ligatures("ﷲ") == "اللہ"

    def test_lam_alef_expands(self):
        assert N.expand_ligatures("ﻻ") == "لا"

    def test_expansion_survives_arabic_folding(self):
        """Expanding then folding must not leave Arabic codepoints behind."""
        result = N.fold_arabic(N.expand_ligatures("ﷲ"))
        assert result == "اللہ"


class TestDigits:
    def test_ascii_to_urdu(self):
        assert N.normalize_digits("2026", to="urdu") == "۲۰۲۶"

    def test_arabic_indic_to_urdu(self):
        assert N.normalize_digits("٢٠٢٦", to="urdu") == "۲۰۲۶"

    def test_urdu_to_ascii(self):
        assert N.normalize_digits("۲۰۲۶", to="ascii") == "2026"

    def test_rejects_unknown_target(self):
        with pytest.raises(ValueError, match=r"urdu.*ascii"):
            N.normalize_digits("۲۰۲۶", to="roman")


class TestInvisibleCharacters:
    def test_strips_zero_width_space(self):
        assert N.remove_invisible("سلام​دنیا") == "سلامدنیا"

    def test_strips_bom(self):
        assert N.remove_invisible("﻿سلام") == "سلام"

    def test_zwnj_removed_by_default(self):
        assert N.remove_invisible("کام‌کاج") == "کامکاج"

    def test_zwnj_preserved_on_request(self):
        text = "کام‌کاج"
        assert N.remove_invisible(text, preserve_zwnj=True) == text

    def test_preserving_zwnj_still_strips_other_invisibles(self):
        assert N.remove_invisible("کام‌​کاج", preserve_zwnj=True) == "کام‌کاج"


class TestPunctuation:
    def test_removes_space_before_full_stop(self):
        assert N.normalize_punctuation("سلام ۔") == "سلام۔"

    def test_adds_space_after_full_stop(self):
        assert N.normalize_punctuation("سلام۔دنیا") == "سلام۔ دنیا"

    def test_collapses_repeated_full_stops(self):
        """urduhack #52."""
        assert N.normalize_punctuation("سلام۔۔۔") == "سلام۔"

    def test_repeats_preserved_when_disabled(self):
        result = N.normalize_punctuation("سلام۔۔۔ دنیا", collapse_repeats=False)
        assert result.count("۔") == 3

    def test_removes_tatweel(self):
        assert N.normalize_punctuation("سلاـــام") == "سلاام"

    def test_question_mark_spacing(self):
        assert N.normalize_punctuation("یہ کیا ہے ؟") == "یہ کیا ہے؟"


class TestWhitespace:
    def test_collapses_runs(self):
        assert N.collapse_whitespace("سلام    دنیا") == "سلام دنیا"

    def test_trims(self):
        assert N.collapse_whitespace("  سلام  ") == "سلام"

    def test_collapses_ideographic_and_nbsp(self):
        assert N.collapse_whitespace("سلام 　دنیا") == "سلام دنیا"

    def test_preserves_paragraph_breaks(self):
        assert N.collapse_whitespace("ایک\n\n\n\nدو") == "ایک\n\nدو"


class TestNormalize:
    def test_end_to_end(self):
        assert N.normalize("مُحَمَّد علي") == "محمد علی"

    def test_empty_string(self):
        assert N.normalize("") == ""

    def test_is_idempotent(self):
        text = "  مُحَمَّد   علي ۔۔۔ ﷲ  "
        once = N.normalize(text)
        assert N.normalize(once) == once

    def test_steps_can_be_disabled(self):
        assert N.normalize("مُحَمَّد", diacritics=False) == "مُحَمَّد"
        assert N.normalize("علي", arabic=False) == "علي"

    def test_digits_untouched_by_default(self):
        assert N.normalize("2026 میں") == "2026 میں"

    def test_digits_folded_on_request(self):
        assert N.normalize("2026 میں", digits="urdu") == "۲۰۲۶ میں"

    def test_nfkc_is_not_used(self):
        """NFKC would spell ﷲ with Arabic HEH; we must not."""
        assert N.normalize("ﷲ") == "اللہ"


class TestIsNormalized:
    def test_true_for_clean_text(self):
        """urduhack #60."""
        assert N.is_normalized("محمد علی")

    def test_false_for_arabic_codepoints(self):
        assert not N.is_normalized("محمد علي")

    def test_false_for_diacritics(self):
        assert not N.is_normalized("مُحَمَّد")

    def test_respects_kwargs(self):
        assert N.is_normalized("مُحَمَّد", diacritics=False)


class TestImportIsCheap:
    def test_no_heavy_dependencies(self):
        """The regression test for the bug that killed urduhack.

        ``pip install urduhack; import urduhack`` raised ModuleNotFoundError
        for TensorFlow because its package __init__ imported it
        unconditionally. Importing this library must never pull in anything
        outside the standard library.
        """
        import os
        import pathlib
        import subprocess
        import sys

        src = pathlib.Path(__file__).resolve().parent.parent / "src"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys, urdukit; "
                "heavy = {'tensorflow', 'torch', 'numpy', 'keras', 'scipy', 'pandas'}; "
                "found = heavy & set(sys.modules); "
                "print(sorted(found))",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(src)},
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "[]", f"heavy imports leaked: {result.stdout}"
