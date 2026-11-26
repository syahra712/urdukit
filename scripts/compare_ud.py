#!/usr/bin/env python3
"""Compare urdukit with other Urdu toolkits on the Urdu UD treebank.

Every tool is scored by the same functions as ``benchmark_ud.py``, on the
same split and the same normalized input. Tools that are not installed are
skipped, so this runs anywhere; install the others into a separate
environment, not urdukit's:

    pip install stanza          # then: python -c "import stanza; stanza.download('ur')"
    pip install urduhack        # needs TensorFlow; see the note below
    python scripts/compare_ud.py --tools urdukit stanza urduhack

Getting urduhack 1.0.3 to run in 2026 took, on Python 3.12: ``pip install
"tensorflow==2.16.2" "tf-keras~=2.16" urduhack``; ``urduhack download``;
copying the files from ``~/.urduhack/models/tokenizer/word/v1/
word_tokenizer_extracted/`` up one directory, where the loader looks; and
running with ``TF_USE_LEGACY_KERAS=1``, because the model was saved with
Keras 2. Stanza was 1.9.2 with its matching models: newer Stanza models
need a newer PyTorch than Intel Macs can install.

Read the result with these in mind:

* **Stanza is trained on this treebank.** Its Urdu models learned from the
  UDTB train split, so on the test split it is scored in-domain, on the
  annotation conventions it was taught. That is a real advantage on this
  benchmark and a fair one to report, but it is not evidence about other
  kinds of text.
* **Stanza lemmatizes; urdukit stems.** A lemmatizer looks at context and
  returns a dictionary form, so it should beat a stemmer on lemma
  conflation. Stanza is lemmatizing gold-tokenized sentences here, so its
  lemma score does not include its own tokenization errors.
* **urduhack** has no stemmer or lemmatizer. Its word tokenizer is a neural
  model that needs TensorFlow; if that will not load, only its rule-based
  parts are scored.

Speed is wall-clock time to run the whole split on one CPU core, including
nothing but the calls themselves (model loading is excluded).

UD Urdu-UDTB is CC BY-NC-SA 4.0 (Bhat et al., 2017); see benchmark_ud.py.
"""

from __future__ import annotations

import argparse
import collections
import os
import sys
import time
from collections.abc import Callable
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))
import benchmark_ud as B

from urdukit import (
    is_stopword,
    normalize,
    sentence_tokenize,
    stem,
    word_tokenize,
)


class Tool:
    """What one toolkit offers; ``None`` for a task it does not do."""

    name = ""
    tokenize: Callable[[str], list[str]] | None = None
    split: Callable[[str], list[str]] | None = None
    is_stop: Callable[[str], bool] | None = None

    def conflate(self, sentences: list[B.Sentence]) -> Callable[[str], str] | None:
        return None


class Urdukit(Tool):
    name = "urdukit"
    tokenize = staticmethod(word_tokenize)
    split = staticmethod(sentence_tokenize)
    is_stop = staticmethod(is_stopword)

    def conflate(self, sentences: list[B.Sentence]) -> Callable[[str], str]:
        return stem


class Stanza(Tool):
    name = "stanza"

    def __init__(self, model_dir: str | None) -> None:
        import stanza

        kwargs: dict[str, Any] = {"verbose": False, "download_method": None}
        if model_dir:
            kwargs["dir"] = model_dir
        self._tok = stanza.Pipeline("ur", processors="tokenize", **kwargs)
        self._lem = stanza.Pipeline(
            "ur", processors="tokenize,pos,lemma", tokenize_pretokenized=True, **kwargs
        )

    def tokenize(self, text: str) -> list[str]:  # type: ignore[override]
        return [t.text for s in self._tok(text).sentences for t in s.tokens]

    def split(self, text: str) -> list[str]:  # type: ignore[override]
        return [s.text for s in self._tok(text).sentences]

    def conflate(self, sentences: list[B.Sentence]) -> Callable[[str], str]:
        # Lemmatize in context, then give each form its most frequent lemma,
        # the same reduction the gold side gets in content_lemmas().
        tokenized = [[form for form, _, _ in tokens] for _, tokens in sentences]
        doc = self._lem(tokenized)
        votes: dict[str, collections.Counter[str]] = collections.defaultdict(
            collections.Counter
        )
        for sent in doc.sentences:
            for word in sent.words:
                votes[normalize(word.text)][normalize(word.lemma or word.text)] += 1
        best = {form: c.most_common(1)[0][0] for form, c in votes.items()}
        return lambda w: best.get(w, w)


class Urduhack(Tool):
    name = "urduhack"

    def __init__(self) -> None:
        from urduhack.stop_words import STOP_WORDS
        from urduhack.tokenization import sentence_tokenizer

        stop = {normalize(w) for w in STOP_WORDS}
        self.is_stop = lambda w: normalize(w) in stop  # type: ignore[assignment]
        self.split = sentence_tokenizer  # type: ignore[assignment]
        try:
            from urduhack.tokenization import word_tokenizer

            word_tokenizer("سلام")
            self.tokenize = word_tokenizer  # type: ignore[assignment]
        except Exception as error:  # the neural tokenizer, needs TensorFlow
            print(f"  urduhack word tokenizer unavailable: {error}", file=sys.stderr)


def _timed(function: Callable[[], Any]) -> tuple[Any, float]:
    start = time.perf_counter()
    result = function()
    return result, time.perf_counter() - start


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache-dir", default=B.DEFAULT_CACHE)
    parser.add_argument("--split", default="test", choices=["train", "dev", "test"])
    parser.add_argument("--tools", nargs="+", default=["urdukit", "stanza", "urduhack"])
    parser.add_argument("--stanza-dir", help="Stanza model directory")
    args = parser.parse_args()

    sentences = B.read_conllu(B.fetch(args.cache_dir, args.split))
    lemma_of = B.content_lemmas(sentences)

    tools: list[Tool] = []
    for name in args.tools:
        try:
            if name == "urdukit":
                tools.append(Urdukit())
            elif name == "stanza":
                tools.append(Stanza(args.stanza_dir))
            elif name == "urduhack":
                tools.append(Urduhack())
            else:
                parser.error(f"unknown tool {name!r}")
        except ImportError as error:
            print(f"  skipping {name}: {error}", file=sys.stderr)

    rows: dict[str, dict[str, str]] = {}
    for tool in tools:
        row = rows.setdefault(tool.name, {})
        if tool.tokenize:
            (_, _, f), secs = _timed(
                lambda t=tool: B.eval_tokenization(sentences, t.tokenize)
            )
            row["tokens F1"], row["tokenize s"] = f"{f:.1f}%", f"{secs:.2f}"
        if tool.split:
            _, _, f = B.eval_sentences(sentences, tool.split)
            row["sentences F1"] = f"{f:.1f}%"
        stemmer = tool.conflate(sentences)
        if stemmer:
            r = B.eval_stemming(lemma_of, stemmer)
            row["lemma groups F1"] = f"{r['f']:.1f}%"
        if tool.is_stop:
            _, _, f, _ = B.eval_stopwords(sentences, tool.is_stop)
            row["stopwords F1"] = f"{f:.1f}%"

    columns = [
        "tokens F1",
        "sentences F1",
        "lemma groups F1",
        "stopwords F1",
        "tokenize s",
    ]
    print(f"\n  UD Urdu-UDTB / {args.split} split ({len(sentences):,} sentences)\n")
    print(f"  {'':10}" + "".join(f"{c:>17}" for c in columns))
    for name, row in rows.items():
        print(f"  {name:10}" + "".join(f"{row.get(c, '-'):>17}" for c in columns))
    print("\n  - means the tool does not offer that task.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
