#!/usr/bin/env python3
"""Benchmark tokenization, sentence splitting, stemming and stopwords
against the Urdu Universal Dependencies treebank (UD Urdu-UDTB).

UDTB is about 5,100 sentences of Urdu news, tokenized, lemmatized and
part-of-speech tagged by human annotators (Bhat et al., 2017). That makes it
the closest thing Urdu has to an independent referee for the parts of
urdukit that are not transliteration.

    python scripts/benchmark_ud.py                 # test split
    python scripts/benchmark_ud.py --split train --errors

Tune on train or dev; report on test only.

Licensing
---------
UDTB is CC BY-NC-SA 4.0: non-commercial and share-alike, so none of it may
be redistributed inside this MIT-licensed package -- not the text, and not
word lists derived from it. This script downloads the files to a gitignored
directory at runtime and never vendors them. Measuring against a dataset is
not redistributing it.

If you publish numbers produced by this script, cite the treebank:

    Bhat et al. (2017), "The Hindi/Urdu Treebank Project", in Handbook of
    Linguistic Annotation, Springer.
    https://github.com/UniversalDependencies/UD_Urdu-UDTB

What each number measures
-------------------------
tokenization
    Token precision/recall of ``word_tokenize`` against the gold forms, per
    sentence. UDTB writes some multi-word expressions joined with ``_``
    (``بات_چیت``); running text has a space there, so ``_`` is read as a
    space on both sides rather than counted against the tokenizer.

sentences
    Boundary precision/recall of ``sentence_tokenize`` over the whole split
    joined into one text.

stemming
    Conflation, scored pairwise over distinct noun, verb and adjective
    forms. Two forms *should* share a stem if the annotators gave them the
    same lemma; precision is the share of urdukit's merges that are right,
    recall the share of right merges urdukit makes. Recall cannot reach
    100%: some lemmas are irregular (``کیا`` -> ``کرنا``) or broken plurals
    (``افراد`` -> ``فرد``) that no suffix rule can reach. A lemma is also
    stricter than a stem -- UD keeps ``لڑکا`` and ``لڑکی`` apart, which a
    retrieval stemmer may reasonably merge -- so precision is a lower
    bound.

stopwords
    Token-level precision/recall of ``is_stopword`` against closed-class
    parts of speech (adpositions, auxiliaries, pronouns, determiners,
    conjunctions, particles). A proxy: a stopword list is a judgement, not a
    POS tag, but a list that misses common postpositions is wrong by any
    standard.
"""

from __future__ import annotations

import argparse
import collections
import os
import sys
import urllib.request
from collections.abc import Callable

BASE_URL = "https://raw.githubusercontent.com/UniversalDependencies/UD_Urdu-UDTB/master"
DEFAULT_CACHE = os.path.join(os.path.dirname(__file__), "..", ".ud_cache")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from urdukit import (  # noqa: E402
    is_stopword,
    normalize,
    sentence_tokenize,
    stem,
    word_tokenize,
)

CONTENT_POS = {"NOUN", "VERB", "ADJ"}
CLOSED_POS = {"ADP", "AUX", "PRON", "DET", "CCONJ", "SCONJ", "PART"}

Token = tuple[str, str, str]  # form, lemma, upos
Sentence = tuple[str, list[Token]]


def fetch(cache_dir: str, split: str) -> str:
    name = f"ur_udtb-ud-{split}.conllu"
    path = os.path.join(cache_dir, name)
    if not os.path.exists(path):
        os.makedirs(cache_dir, exist_ok=True)
        print(f"  downloading {name} ...", file=sys.stderr)
        urllib.request.urlretrieve(f"{BASE_URL}/{name}", path)
    return path


def read_conllu(path: str) -> list[Sentence]:
    sentences: list[Sentence] = []
    text = ""
    tokens: list[Token] = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if line.startswith("# text ="):
                text = line[len("# text =") :].strip()
            elif not line:
                if tokens:
                    sentences.append((text, tokens))
                text, tokens = "", []
            elif not line.startswith("#"):
                cols = line.split("\t")
                if "-" in cols[0] or "." in cols[0]:
                    continue  # multiword-token ranges and empty nodes
                tokens.append((cols[1], cols[2], cols[3]))
    if tokens:
        sentences.append((text, tokens))
    return sentences


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return 100 * p, 100 * r, 100 * f


def eval_tokenization(sentences: list[Sentence]) -> tuple[float, float, float]:
    tp = fp = fn = 0
    for text, tokens in sentences:
        gold = [
            part
            for form, _, _ in tokens
            for part in normalize(form.replace("_", " ")).split()
        ]
        pred = word_tokenize(normalize(text.replace("_", " ")))
        g, p = collections.Counter(gold), collections.Counter(pred)
        match = sum((g & p).values())
        tp += match
        fp += sum(p.values()) - match
        fn += sum(g.values()) - match
    return _prf(tp, fp, fn)


def eval_sentences(sentences: list[Sentence]) -> tuple[float, float, float]:
    texts = [normalize(text) for text, _ in sentences]
    gold, offset = set(), 0
    for text in texts:
        offset += len(text)
        gold.add(offset)
        offset += 1  # the joining space
    joined = " ".join(texts)
    pred, cursor = set(), 0
    for sentence in sentence_tokenize(joined):
        start = joined.find(sentence, cursor)
        if start < 0:
            continue
        cursor = start + len(sentence)
        pred.add(cursor)
    tp = len(gold & pred)
    return _prf(tp, len(pred) - tp, len(gold) - tp)


def content_lemmas(sentences: list[Sentence]) -> dict[str, str]:
    """Map each distinct content-word form to its most frequent lemma."""
    counts: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    for _, tokens in sentences:
        for form, lemma, upos in tokens:
            # Forms joined with _ are multi-word expressions, not words.
            if upos in CONTENT_POS and lemma != "_" and "_" not in form:
                counts[normalize(form)][normalize(lemma)] += 1
    return {form: c.most_common(1)[0][0] for form, c in counts.items()}


def _pairs(groups: dict[str, set[str]]) -> set[tuple[str, str]]:
    out = set()
    for members in groups.values():
        ordered = sorted(members)
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                out.add((a, b))
    return out


def eval_stemming(
    lemma_of: dict[str, str], stemmer: Callable[[str], str] = stem
) -> dict[str, object]:
    by_stem: dict[str, set[str]] = collections.defaultdict(set)
    by_lemma: dict[str, set[str]] = collections.defaultdict(set)
    for form, lemma in lemma_of.items():
        by_stem[stemmer(form)].add(form)
        by_lemma[lemma].add(form)
    predicted, gold = _pairs(by_stem), _pairs(by_lemma)
    tp = len(predicted & gold)
    p, r, f = _prf(tp, len(predicted) - tp, len(gold) - tp)
    # Errors, grouped so the worst offenders surface first.
    false_merges = sorted(
        (
            (len({lemma_of[w] for w in members}), s, sorted(members)[:6])
            for s, members in by_stem.items()
            if len({lemma_of[w] for w in members}) > 1
        ),
        reverse=True,
    )
    missed = sorted(
        (
            (len({stemmer(w) for w in members}), lemma, sorted(members)[:6])
            for lemma, members in by_lemma.items()
            if len({stemmer(w) for w in members}) > 1
        ),
        reverse=True,
    )
    return {
        "p": p,
        "r": r,
        "f": f,
        "types": len(lemma_of),
        "false_merges": false_merges,
        "missed": missed,
    }


def eval_stopwords(
    sentences: list[Sentence],
) -> tuple[float, float, float, list[tuple[str, int]]]:
    tp = fp = fn = 0
    missing: collections.Counter[str] = collections.Counter()
    for _, tokens in sentences:
        for form, _, upos in tokens:
            word = normalize(form)
            flagged, closed = is_stopword(word), upos in CLOSED_POS
            tp += flagged and closed
            fp += flagged and not closed
            fn += closed and not flagged
            if closed and not flagged:
                missing[word] += 1
    p, r, f = _prf(tp, fp, fn)
    return p, r, f, missing.most_common(15)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE)
    parser.add_argument(
        "--split",
        default="test",
        choices=["train", "dev", "test"],
        help="Report on this split. Tune on train/dev; report on test only.",
    )
    parser.add_argument(
        "--errors", action="store_true", help="Print the largest error groups."
    )
    args = parser.parse_args()

    sentences = read_conllu(fetch(args.cache_dir, args.split))
    lemma_of = content_lemmas(sentences)
    rows = [
        ("tokenization", eval_tokenization(sentences)),
        ("sentence splitting", eval_sentences(sentences)),
    ]
    stemming = eval_stemming(lemma_of)
    baseline = eval_stemming(lemma_of, stemmer=lambda w: w)
    sp, sr, sf, missing = eval_stopwords(sentences)

    print()
    print(f"  UD Urdu-UDTB / {args.split} split  ({len(sentences):,} sentences)")
    print(f"  {'-' * 58}")
    print(f"  {'':28}{'precision':>10}{'recall':>9}{'F1':>8}")
    for name, (p, r, f) in rows:
        print(f"  {name:28}{p:>9.1f}%{r:>8.1f}%{f:>7.1f}%")
    print(
        f"  {'stemming (conflation)':28}{stemming['p']:>9.1f}%"
        f"{stemming['r']:>8.1f}%{stemming['f']:>7.1f}%"
    )
    print(
        f"  {'  no stemming, for scale':28}{'-':>10}"
        f"{baseline['r']:>8.1f}%{baseline['f']:>7.1f}%"
    )
    print(f"  {'stopwords (closed class)':28}{sp:>9.1f}%{sr:>8.1f}%{sf:>7.1f}%")
    print(f"  {'-' * 58}")
    print(f"  stemming scored over {stemming['types']:,} distinct content-word forms")

    if args.errors:
        print("\n  stems that merge different lemmas (lemma count, stem, forms):")
        for n, s, forms in stemming["false_merges"][:25]:  # type: ignore[index]
            print(f"    {n:3}  {s:12} {' '.join(forms)}")
        print("\n  lemmas split across stems (stem count, lemma, forms):")
        for n, lemma, forms in stemming["missed"][:25]:  # type: ignore[index]
            print(f"    {n:3}  {lemma:12} {' '.join(forms)}")
        print("\n  closed-class words not in STOPWORDS:")
        print("    " + "  ".join(f"{w} {c}" for w, c in missing))

    print()
    print("  UD Urdu-UDTB is CC BY-NC-SA 4.0 (Bhat et al., 2017). Cite it if")
    print("  you publish these numbers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
