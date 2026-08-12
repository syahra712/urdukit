"""Invariants on the character tables.

These tests exist because the tables in ``characters.py`` are hand-authored
Unicode. A wrong codepoint there is invisible on screen -- Arabic YEH and
Urdu FARSI YEH render near-identically -- but silently corrupts every
downstream result. Each test below caught a real bug during development.
"""

import unicodedata

import pytest

from urdukit import characters as C


def test_alphabet_is_complete():
    """Urdu has 39 letters; a duplicate in the source string would shrink this."""
    assert len(C.URDU_LETTERS) == 39


@pytest.mark.parametrize(
    "codepoint,name",
    [
        (0x06CC, "ARABIC LETTER FARSI YEH"),
        (0x06A9, "ARABIC LETTER KEHEH"),
        (0x06C1, "ARABIC LETTER HEH GOAL"),
        (0x06BE, "ARABIC LETTER HEH DOACHASHMEE"),
        (0x06D2, "ARABIC LETTER YEH BARREE"),
        (0x06BA, "ARABIC LETTER NOON GHUNNA"),
    ],
)
def test_urdu_specific_letters_are_the_urdu_codepoints(codepoint, name):
    """The letters that differ from Arabic must be the Urdu ones, by name."""
    char = chr(codepoint)
    assert char in C.URDU_LETTERS
    assert unicodedata.name(char) == name


def test_arabic_lookalikes_are_absent_from_the_alphabet():
    """Arabic YEH/KAF/HEH must never appear in the Urdu alphabet itself."""
    for codepoint in (0x064A, 0x0643, 0x0647):
        assert chr(codepoint) not in C.URDU_LETTERS


def test_fold_table_keys_are_single_codepoints():
    """``str.translate`` silently ignores multi-character keys."""
    offenders = [k for k in C.ARABIC_TO_URDU if len(k) != 1]
    assert offenders == []


def test_fold_table_is_idempotent():
    """No fold target may itself be a fold key, or folding would not settle."""
    unstable = {k: v for k, v in C.ARABIC_TO_URDU.items() if v in C.ARABIC_TO_URDU}
    assert unstable == {}


def test_fold_table_has_no_self_mappings():
    assert [k for k, v in C.ARABIC_TO_URDU.items() if k == v] == []


def test_ligature_expansions_contain_no_arabic_leftovers():
    """An expansion must not reintroduce a codepoint we would fold away.

    NFKC decomposes U+FDF2 to ``ا ل ل`` + *Arabic* HEH (U+0647). Emitting that
    would defeat the whole point of the fold table, so the expansions here are
    spelled with Urdu HEH GOAL.
    """
    leaks = {
        lig: [c for c in expansion if c in C.ARABIC_TO_URDU]
        for lig, expansion in C.LIGATURES.items()
        if any(c in C.ARABIC_TO_URDU for c in expansion)
    }
    assert leaks == {}


def test_allah_ligature_uses_urdu_heh_goal():
    assert C.LIGATURES["ﷲ"] == "اللہ"
    assert C.LIGATURES["ﷲ"][-1] == "ہ"  # HEH GOAL, not U+0647


def test_diacritics_are_all_combining_marks():
    """Anything in the aerab table must be a zero-width combining mark."""
    non_combining = [
        f"U+{ord(c):04X}" for c in C.URDU_DIACRITICS if unicodedata.category(c) != "Mn"
    ]
    assert non_combining == []


def test_digit_tables_round_trip():
    urdu = "۰۱۲۳۴۵۶۷۸۹"
    ascii_digits = "0123456789"
    assert "".join(C.TO_URDU_DIGITS[c] for c in ascii_digits) == urdu
    assert "".join(C.TO_ASCII_DIGITS[c] for c in urdu) == ascii_digits


def test_zwnj_is_in_the_invisible_set_and_named_separately():
    assert C.ZERO_WIDTH_NON_JOINER == "‌"
    assert C.ZERO_WIDTH_NON_JOINER in C.INVISIBLE_CHARACTERS


def test_is_urdu_character():
    assert C.is_urdu_character("ی")
    assert C.is_urdu_character("۔")
    assert not C.is_urdu_character("a")
    assert not C.is_urdu_character("ي")  # Arabic YEH is not Urdu
    with pytest.raises(ValueError):
        C.is_urdu_character("ab")


def test_tables_are_immutable():
    with pytest.raises(TypeError):
        C.ARABIC_TO_URDU["x"] = "y"  # type: ignore[index]
