#!/usr/bin/env python3
"""Benchmark ``to_roman`` and ``to_urdu`` against the Dakshina Urdu data.

Dakshina (Google Research) is the standard benchmark for South Asian
romanization. Its Urdu test split has 2,500 native-script words held out by
word *and* by lemma, so nothing in it overlaps the training split.

    python scripts/benchmark_dakshina.py                       # to_roman
    python scripts/benchmark_dakshina.py --direction to_urdu   # Roman -> Urdu

The reverse direction is scored two ways, both as exact match after
``normalize``:

- **lexicon pairs**: every attested (word, romanization) pair in the split;
  feed the romanization to ``to_urdu`` and compare with the word. These are
  mostly rare content words.
- **sentences**: Dakshina's romanized Wikipedia sentences, typed by native
  speakers, against their native-script originals. Only sentences whose two
  sides have the same number of tokens are used, so tokens can be paired by
  position; the script prints how many that is. These carry the everyday
  function words (*main*, *he*, *ye*) that spelling variants affect most.
  This data has only dev and test splits; tune on dev.

Both are reported with and without :data:`urdukit.transliteration.ROMAN_VARIANTS`
so the effect of that table is visible on its own.

Licensing
---------
Dakshina is CC BY-SA 4.0, which is share-alike and therefore incompatible
with redistributing its contents inside this MIT-licensed package. So this
script **downloads the data to a gitignored directory at runtime and never
vendors it**. Measuring against a dataset is not redistributing it.

If you publish numbers produced by this script, cite the dataset:

    Roark et al. (2020), "Processing South Asian Languages Written in the
    Latin Script: the Dakshina Dataset", LREC 2020.
    https://www.aclweb.org/anthology/2020.lrec-1.294

Why the download is not just ``curl``
-------------------------------------
The official archive is a single 2 GB uncompressed tar covering 12
languages. The three Urdu lexicon files inside total about 2.6 MB. Since the
tar is uncompressed, its member headers can be walked with HTTP range
requests and only the wanted members fetched -- roughly 176 KB of headers
instead of 2 GB.
"""

from __future__ import annotations

import argparse
import collections
import os
import sys
import urllib.request

TAR_URL = "https://storage.googleapis.com/gresearch/dakshina/dakshina_dataset_v1.0.tar"
BLOCK = 512
DEFAULT_CACHE = os.path.join(os.path.dirname(__file__), "..", ".dakshina_cache")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from urdukit import normalize  # noqa: E402
from urdukit.transliteration import (  # noqa: E402
    LEXICON,
    LOANWORDS,
    to_roman,
    to_urdu,
)


def _range(start: int, length: int) -> bytes:
    request = urllib.request.Request(
        TAR_URL, headers={"Range": f"bytes={start}-{start + length - 1}"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _parse_header(header: bytes):
    if header[:1] == b"\0":
        return None
    name = header[0:100].rstrip(b"\0").decode("utf-8", "replace")
    raw_size = header[124:136].rstrip(b"\0 ").decode() or "0"
    try:
        size = int(raw_size, 8)
    except ValueError:
        size = 0
    prefix = header[345:500].rstrip(b"\0").decode("utf-8", "replace")
    if prefix:
        name = f"{prefix}/{name}"
    return name, size


def download_urdu_lexicons(cache_dir: str) -> None:
    """Fetch only the Urdu lexicon members from the remote tar."""
    os.makedirs(cache_dir, exist_ok=True)
    offset = 0
    found = []
    print("walking remote tar headers (no full download)...", flush=True)
    while True:
        header = _range(offset, BLOCK)
        if len(header) < BLOCK:
            break
        parsed = _parse_header(header)
        if parsed is None:
            break
        name, size = parsed
        wanted = ("/ur/lexicons/" in name and name.endswith(".tsv")) or (
            "/ur/romanized/ur.romanized.rejoined." in name and name.endswith(".txt")
        )
        if wanted:
            found.append((name, offset + BLOCK, size))
        offset += BLOCK + ((size + BLOCK - 1) // BLOCK) * BLOCK
        # Urdu sorts last; once past it there is nothing left to find.
        if found and "/ur/" not in name:
            break

    for name, start, size in found:
        target = os.path.join(cache_dir, os.path.basename(name))
        if os.path.exists(target) and os.path.getsize(target) == size:
            continue
        with open(target, "wb") as handle:
            handle.write(_range(start, size))
        print(f"  fetched {os.path.basename(name)} ({size:,} bytes)")


def load_lexicon(path: str) -> dict[str, dict[str, int]]:
    """Read a Dakshina TSV into ``{word: {romanization: attestations}}``."""
    table: dict[str, dict[str, int]] = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2 or not parts[0] or not parts[1]:
                continue
            count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            table[parts[0]][parts[1]] = count
    return table


def evaluate(table: dict[str, dict[str, int]]) -> dict:
    strict = lenient = 0
    # The same two counts over words neither table knows: what the rules
    # alone achieve, with nothing a table entry could have memorized.
    unseen = unseen_strict = unseen_lenient = 0
    misses: list[tuple[str, str, str]] = []
    for word, romanizations in table.items():
        produced = to_roman(word)
        best = max(romanizations.items(), key=lambda kv: kv[1])[0]
        in_tables = word in LEXICON or word in LOANWORDS
        unseen += not in_tables
        if produced == best:
            strict += 1
            unseen_strict += not in_tables
        if produced in romanizations:
            lenient += 1
            unseen_lenient += not in_tables
        elif len(misses) < 20:
            misses.append((word, best, produced))
    total = len(table)
    return {
        "n": total,
        "strict": strict,
        "lenient": lenient,
        "strict_pct": 100 * strict / total,
        "lenient_pct": 100 * lenient / total,
        "overlap": total - unseen,
        "unseen": unseen,
        "unseen_strict_pct": 100 * unseen_strict / max(unseen, 1),
        "unseen_lenient_pct": 100 * unseen_lenient / max(unseen, 1),
        "misses": misses,
    }


def evaluate_reverse_lexicon(
    table: dict[str, dict[str, int]], *, variants: bool
) -> dict:
    """Score ``to_urdu`` on every attested (word, romanization) pair."""
    pairs = pairs_ok = weight = weight_ok = best_ok = 0
    for word, romanizations in table.items():
        target = normalize(word)
        best = max(romanizations.items(), key=lambda kv: kv[1])[0]
        for roman, count in romanizations.items():
            hit = normalize(to_urdu(roman, variants=variants)) == target
            pairs += 1
            pairs_ok += hit
            weight += count
            weight_ok += hit * count
            best_ok += hit and roman == best
    return {
        "words": len(table),
        "pairs": pairs,
        "pairs_pct": 100 * pairs_ok / pairs,
        "weighted_pct": 100 * weight_ok / weight,
        "best_pct": 100 * best_ok / len(table),
    }


_EDGE = ".,!?;:()[]{}\"'"
_URDU_EDGE = _EDGE + "۔،؛؟"


def _native_tokens(line: str) -> list[str]:
    return [t.strip(_URDU_EDGE) for t in normalize(line).split() if t.strip(_URDU_EDGE)]


def _roman_tokens(line: str) -> list[str]:
    return [t.strip(_EDGE) for t in line.split() if t.strip(_EDGE)]


def evaluate_reverse_sentences(
    native_path: str, roman_path: str, *, variants: bool
) -> dict:
    """Score ``to_urdu`` token by token on position-alignable sentences."""
    with open(native_path, encoding="utf-8") as handle:
        native = handle.read().splitlines()
    with open(roman_path, encoding="utf-8") as handle:
        roman = handle.read().splitlines()
    used = tokens = correct = 0
    for native_line, roman_line in zip(native, roman):
        targets = _native_tokens(native_line)
        sources = _roman_tokens(roman_line)
        if len(targets) != len(sources):
            continue
        used += 1
        for source, target in zip(sources, targets):
            tokens += 1
            correct += normalize(to_urdu(source, variants=variants)) == target
    return {
        "sentences": len(native),
        "used": used,
        "tokens": tokens,
        "pct": 100 * correct / max(tokens, 1),
    }


def report_to_urdu(args) -> int:
    lexicon_path = os.path.join(args.cache_dir, f"ur.translit.sampled.{args.split}.tsv")
    sentence_split = "dev" if args.split == "train" else args.split
    native_path = os.path.join(
        args.cache_dir, f"ur.romanized.rejoined.{sentence_split}.native.txt"
    )
    roman_path = os.path.join(
        args.cache_dir, f"ur.romanized.rejoined.{sentence_split}.roman.txt"
    )
    if not all(os.path.exists(p) for p in (lexicon_path, native_path, roman_path)):
        download_urdu_lexicons(args.cache_dir)
    if not all(os.path.exists(p) for p in (lexicon_path, native_path, roman_path)):
        print("could not obtain the Dakshina files", file=sys.stderr)
        return 1

    table = load_lexicon(lexicon_path)
    lex = {v: evaluate_reverse_lexicon(table, variants=v) for v in (False, True)}
    sent = {
        v: evaluate_reverse_sentences(native_path, roman_path, variants=v)
        for v in (False, True)
    }

    print()
    print("  Dakshina ur / to_urdu (Roman -> Urdu), exact match after normalize")
    print(f"  {'-' * 60}")
    print(f"  {'':34}{'no variants':>13}{'variants':>13}")
    print(f"  lexicon pairs, {args.split} split ({lex[True]['pairs']:,} pairs)")
    for key, label in (
        ("pairs_pct", "every attested pair"),
        ("weighted_pct", "weighted by attestations"),
        ("best_pct", "most-attested romanization"),
    ):
        print(f"    {label:32}{lex[False][key]:12.2f}%{lex[True][key]:12.2f}%")
    s = sent[True]
    print(
        f"  sentences, {sentence_split} split ({s['used']:,} of "
        f"{s['sentences']:,} alignable, {s['tokens']:,} tokens)"
    )
    print(f"    {'tokens correct':32}{sent[False]['pct']:12.2f}%{s['pct']:12.2f}%")
    print(f"  {'-' * 60}")
    print()
    print("  Dakshina is CC BY-SA 4.0 (Roark et al., LREC 2020). Cite it if")
    print("  you publish these numbers.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE)
    parser.add_argument(
        "--split",
        default="test",
        choices=["train", "dev", "test"],
        help="Report on this split. Tune on train/dev; report on test only.",
    )
    parser.add_argument(
        "--direction",
        default="to_roman",
        choices=["to_roman", "to_urdu"],
        help="to_roman: Urdu -> Roman (default). to_urdu: Roman -> Urdu.",
    )
    args = parser.parse_args()
    if args.direction == "to_urdu":
        return report_to_urdu(args)

    path = os.path.join(args.cache_dir, f"ur.translit.sampled.{args.split}.tsv")
    if not os.path.exists(path):
        download_urdu_lexicons(args.cache_dir)
    if not os.path.exists(path):
        print(f"could not obtain {path}", file=sys.stderr)
        return 1

    table = load_lexicon(path)
    result = evaluate(table)

    print()
    print(f"  Dakshina ur / {args.split} split")
    print(f"  {'-' * 52}")
    print(f"  words                        {result['n']:>8,}")
    print(
        f"  avg romanizations per word   "
        f"{sum(len(v) for v in table.values()) / result['n']:>8.2f}"
    )
    print(
        f"  already in urdukit tables    {result['overlap']:>8,}"
        "   (contamination check)"
    )
    print(f"  {'-' * 52}")
    print(
        f"  matches most-attested        {result['strict']:>8,}"
        f"   {result['strict_pct']:5.2f}%"
    )
    print(
        f"  matches any attested         {result['lenient']:>8,}"
        f"   {result['lenient_pct']:5.2f}%"
    )
    print(f"  {'-' * 52}")
    print(f"  rules only ({result['unseen']:,} words in neither table)")
    print(
        f"    matches most-attested                {result['unseen_strict_pct']:5.2f}%"
    )
    print(
        f"    matches any attested                 {result['unseen_lenient_pct']:5.2f}%"
    )
    print(f"  {'-' * 52}")
    print()
    print("  sample misses (word | most-attested | ours):")
    for word, expected, produced in result["misses"][:12]:
        print(f"    {word:16} {expected:18} {produced}")
    print()
    print("  Dakshina is CC BY-SA 4.0 (Roark et al., LREC 2020). Cite it if")
    print("  you publish these numbers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
