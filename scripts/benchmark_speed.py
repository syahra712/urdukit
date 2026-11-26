#!/usr/bin/env python3
"""Time the main urdukit functions on one ordinary sentence.

    python scripts/benchmark_speed.py

Uses only ``timeit``. Each figure is the best of five repeats, per call, on
a 66-character, 14-word Urdu sentence (and its Roman equivalent for
``to_urdu``). Absolute numbers depend on the machine and Python version;
the script prints both so a result can be put in context.
"""

from __future__ import annotations

import os
import platform
import sys
import timeit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import urdukit

URDU = "میں پاکستان سے ہوں اور مجھے اردو کی کتابیں پڑھنا بہت اچھا لگتا ہے۔"
ROMAN = "main pakistan se hoon aur mujhe urdu ki kitabein parhna bohat acha lagta hai."

CASES = [
    ("normalize", lambda: urdukit.normalize(URDU)),
    ("word_tokenize", lambda: urdukit.word_tokenize(URDU)),
    ("sentence_tokenize", lambda: urdukit.sentence_tokenize(URDU)),
    ("stem_tokens", lambda: urdukit.stem_tokens(urdukit.word_tokenize(URDU))),
    ("to_roman", lambda: urdukit.to_roman(URDU)),
    ("to_urdu", lambda: urdukit.to_urdu(ROMAN)),
]


def main() -> int:
    print(f"\n  Python {platform.python_version()} on {platform.machine()}")
    print(f"  Urdu sentence: {len(URDU)} chars, Roman sentence: {len(ROMAN)} chars")
    print(f"  {'-' * 44}")
    for name, call in CASES:
        timer = timeit.Timer(call)
        number, _ = timer.autorange()
        best = min(timer.repeat(repeat=5, number=number)) / number
        rate = 1 / best
        print(f"  {name:20} {best * 1e6:8.1f} µs   {rate:>9,.0f} /s")
    print(f"  {'-' * 44}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
