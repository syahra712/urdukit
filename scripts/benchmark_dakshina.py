#!/usr/bin/env python3
"""Benchmark ``to_roman`` against the Dakshina Urdu romanization lexicon.

Dakshina (Google Research) is the standard benchmark for South Asian
romanization. Its Urdu test split has 2,500 native-script words held out by
word *and* by lemma, so nothing in it overlaps the training split.

    python scripts/benchmark_dakshina.py

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
from urdukit.transliteration import LEXICON, to_roman  # noqa: E402


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
        if "/ur/lexicons/" in name and name.endswith(".tsv"):
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
    misses: list[tuple[str, str, str]] = []
    for word, romanizations in table.items():
        produced = to_roman(word)
        best = max(romanizations.items(), key=lambda kv: kv[1])[0]
        if produced == best:
            strict += 1
        if produced in romanizations:
            lenient += 1
        elif len(misses) < 20:
            misses.append((word, best, produced))
    total = len(table)
    return {
        "n": total,
        "strict": strict,
        "lenient": lenient,
        "strict_pct": 100 * strict / total,
        "lenient_pct": 100 * lenient / total,
        "overlap": sum(1 for w in table if w in LEXICON),
        "misses": misses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE)
    parser.add_argument(
        "--split",
        default="test",
        choices=["train", "dev", "test"],
        help="Report on this split. Tune on train/dev; report on test only.",
    )
    args = parser.parse_args()

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
        f"  already in urdukit lexicon   {result['overlap']:>8,}"
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
