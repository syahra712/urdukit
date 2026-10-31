# urdukit

A modern, dependency-free NLP toolkit for Urdu — normalization, tokenization, stopwords, stemming and Roman Urdu transliteration.

```bash
pip install git+https://github.com/syahra712/urdukit
```

```python
import urdukit

urdukit.normalize("مُحَمَّد علي")        # 'محمد علی'
urdukit.sentence_tokenize("سلام۔ دنیا۔")  # ['سلام۔', 'دنیا۔']
urdukit.to_roman("میں پاکستان سے ہوں۔")   # 'mein pakistan se hun.'
```

No TensorFlow. No model downloads. No dependencies at all — just the standard library.

## Why this exists

Urdu is spoken by over 230 million people. Its de-facto Python library, [`urduhack`](https://github.com/urduhack/urduhack), still serves **40,000–118,000 downloads a month** — and its last release was **July 2020**.

It no longer works. `urduhack`'s package `__init__` imports TensorFlow unconditionally, even though TensorFlow is declared an *optional* extra:

```console
$ pip install urduhack && python -c "import urduhack"
ModuleNotFoundError: No module named 'tensorflow'
```

That one line is behind six years of unanswered issue reports — [#153](https://github.com/urduhack/urduhack/issues/153), [#155](https://github.com/urduhack/urduhack/issues/155), [#144](https://github.com/urduhack/urduhack/issues/144), [#142](https://github.com/urduhack/urduhack/issues/142), [#107](https://github.com/urduhack/urduhack/issues/107). Its most recent open issue, [#156](https://github.com/urduhack/urduhack/issues/156), asks for Urdu↔Roman transliteration. It was filed in April 2026 and never answered.

`urdukit` is a clean-room replacement that installs, imports, and ships the features that were asked for.

## What it does

### Normalization

The single highest-value operation in Urdu NLP. Arabic and Urdu share a script but not their codepoints — Arabic YEH (`U+064A`) and Urdu FARSI YEH (`U+06CC`) render near-identically, so `"علی" != "علي"` even though both read as *Ali*. Text from real sources mixes them constantly.

```python
from urdukit import normalize, is_normalized

normalize("مُحَمَّد علي")           # 'محمد علی'   — folds Arabic, strips aerab
normalize("ﷲ")                     # 'اللہ'       — expands the ligature
normalize("سلام ۔۔۔ دنیا")          # 'سلام۔ دنیا' — repairs punctuation
normalize("2026 میں", digits="urdu") # '۲۰۲۶ میں'

is_normalized("محمد علی")           # True
is_normalized("محمد علي")           # False
```

Every step is separately callable: `fold_arabic`, `remove_diacritics`, `expand_ligatures`, `normalize_digits`, `normalize_punctuation`, `remove_invisible`, `collapse_whitespace`.

> Note: `urdukit` uses NFC, never NFKC. NFKC decomposes ﷲ using *Arabic* HEH (`U+0647`) rather than Urdu HEH GOAL (`U+06C1`), which quietly reintroduces the exact bug normalization exists to fix.

### Tokenization

```python
from urdukit import sentence_tokenize, word_tokenize

sentence_tokenize("سلام۔ آپ کیسے ہیں؟")   # ['سلام۔', 'آپ کیسے ہیں؟']
sentence_tokenize("ایک۔دو۔تین۔")           # ['ایک۔', 'دو۔', 'تین۔']
word_tokenize("میں computer استعمال کرتا ہوں")
# ['میں', 'computer', 'استعمال', 'کرتا', 'ہوں']
```

Urdu ends sentences with ۔ (`U+06D4`), not `.` — splitting on `.` finds nothing. The tokenizer also handles omitted spaces after ۔ (endemic in real text), decimals, both digit systems, Latin code-switching, and ZWNJ.

### Stopwords and stemming

```python
from urdukit import remove_stopwords, stem_tokens, word_tokenize

tokens = word_tokenize("مجھے کتابیں پڑھنا اچھا لگتا ہے", keep_punctuation=False)
content = remove_stopwords(tokens)   # ['کتابیں', 'پڑھنا', 'اچھا', 'لگتا']
stem_tokens(content)                 # ['کتاب', 'پڑھ', 'اچھ', 'لگ']
```

212 curated stopwords, stored normalized so Arabic-codepoint variants still match.

⚠️ `نہیں` ("not") is a stopword. Strip it before sentiment analysis and you invert your labels.

### Transliteration

The feature [#156](https://github.com/urduhack/urduhack/issues/156) and [#146](https://github.com/urduhack/urduhack/issues/146) asked for.

```python
from urdukit import to_roman, to_urdu

to_roman("میں پاکستان سے ہوں۔")   # 'mein pakistan se hun.'
to_urdu("mein pakistan se hun")   # 'میں پاکستان سے ہوں'
```

**Accuracy, measured on a standard benchmark:**

There are two layers — a lookup table of 143 common words, and a rule-based fallback for everything else.

Benchmarked against the [Dakshina](https://github.com/google-research-datasets/dakshina) Urdu test split (Google Research, LREC 2020) — 2,500 native-script words held out by both word and lemma:

| | |
|---|---|
| Matches the **most-attested** romanization | **16.0%** |
| Matches **any** attested romanization | **34.8%** |
| Same, on the 2,471 words in neither lookup table (rules alone) | **15.2%** / **34.1%** |
| Lexicon words | exact **by construction** — see the caveat below |

Reproduce it yourself:

```bash
python scripts/benchmark_dakshina.py
```

The script fetches only the Urdu lexicon files it needs and does not vendor the dataset — Dakshina is CC BY-SA 4.0, which is incompatible with redistribution inside this MIT package.

**These numbers are low, for two reasons.** First, structural: Urdu script does not record short vowels. `استاد` is *ustad*, but nothing in ا-س-ت-ا-د says the first vowel is *u*. No rule can recover information that was never written down. Second, and more fixable: **a large share of Urdu vocabulary is English loanwords** — `آرمی` is *army*, `آرگنائزیشن` is *organisation*. Those romanize back to English spelling, which phonetic rules will never produce.

There is now a `LOANWORDS` table of 140 such words (measured when it had 123, accuracy on the test-split words it covers went from **0% to 92%** most-attested and **17% to 100%** any-attested). It still only moves the headline by a small amount because 140 words cover a small fraction of 2,500 test words. **Coverage is the entire constraint, and it is the easiest thing to contribute** — see [issue #4](https://github.com/syahra712/urdukit/issues/4).

A small `PHRASE_LOANWORDS` table also now covers a few common *two-word* loanwords that `LOANWORDS` structurally can't (`ویب سائٹ` → `website`, `ای میل` → `email`) — lookup there runs on adjacent token pairs before the single-token tables are checked.

The fallback aims for a *pronounceable approximation*, not a correct answer. The one case where it can do better is text that carries its vowel marks: `to_roman("مُحَمَّد")` reads the aerab and returns `muhammad`, and `اِس` / `اُس` come out as `is` / `us`.

> ⚠️ **The lexicon is seed-quality and not yet fully verified.** Lexicon words return their table entry exactly, which means the *lookup* is reliable — it does **not** mean every entry is right. The initial 118 entries were machine-generated; a native-speaker spot-check of 12 found 1 incorrect, suggesting a few more may remain among the entries added since. Corrections are the most useful thing you can send. See [Contributing](#contributing).

This is why the lexicon matters more than the rules: adding a correct word takes it from a ~35% guess to a reliable answer. It is also why the list needs more eyes than one author's.

### Cleaning text for a model

```python
from urdukit import preprocessing

preprocessing.replace_urls("دیکھیں https://example.com اور")   # 'دیکھیں <URL> اور'
preprocessing.replace_numbers("۳۴ کتابیں")                     # '<NUMBER> کتابیں'
preprocessing.digits_space("سال2026میں")                       # 'سال 2026 میں'
```

Also `replace_emails`, `replace_phone_numbers`, `replace_currency_symbols`, `remove_punctuation`, `english_characters_space` and `all_punctuations_space`. All of them run in linear time on adversarial input — there is a test for it.

## Benchmarks

Every module that can be measured is measured against data annotated by people, not by this project:

```bash
python scripts/benchmark_dakshina.py   # transliteration  (Dakshina, CC BY-SA 4.0)
python scripts/benchmark_ud.py         # everything else  (UD Urdu-UDTB, CC BY-NC-SA 4.0)
```

Both scripts download their data at runtime; neither dataset's licence allows it to ship inside an MIT package. Rules are tuned on the train splits, and the figures below are the test splits, run once.

UD Urdu-UDTB, test split (535 sentences, 1,944 distinct content-word forms for stemming):

| | Precision | Recall | F1 |
|---|---:|---:|---:|
| Word tokenization | 99.9% | 100.0% | 99.9% |
| Sentence splitting | 99.8% | 98.7% | 99.2% |
| Stemming (conflation) | 73.8% | 73.6% | **73.7%** |
| &nbsp;&nbsp;stemmer in 0.1.0, for comparison | 73.5% | 58.8% | 65.3% |
| &nbsp;&nbsp;no stemming, for scale | – | 0.0% | 0.0% |
| Stopwords vs. closed-class POS | 85.8% | 91.3% | 88.5% |

UD Urdu-UDTB is by Bhat et al. (2017), *The Hindi/Urdu Treebank Project*; cite it if you publish these numbers.

Stemming is scored as conflation: two forms should share a stem exactly when the treebank's annotators gave them the same lemma. Some of the "errors" are the treebank being stricter than a search index needs (it keeps the noun `کھیل` apart from the verb `کھیلنا`), so read precision as a lower bound. Recall can't reach 100% either: irregular forms (`کیا` → `کرنا`) and Arabic broken plurals (`افراد` → `فرد`) are out of reach for any suffix rule.

## Migrating from urduhack

Change one import:

```python
# before
from urduhack import normalize
from urduhack.tokenization import sentence_tokenizer, word_tokenizer

# after
from urdukit.compat.urduhack import normalize, sentence_tokenizer, word_tokenizer
```

Or convert a whole module at once:

```python
import urdukit.compat.urduhack as urduhack
```

The shim keeps urduhack's exact signatures, including the ones that differ from `urdukit`'s own — `urduhack.remove_stopwords` takes and returns a *string*, and the shim preserves that.

**Not provided:** `Pipeline`, `CoNLL` and `download`. Those needed TensorFlow and runtime weight downloads — the reason the original became uninstallable. They raise `NotImplementedError` pointing at [stanza](https://stanfordnlp.github.io/stanza/) (which supports Urdu) for POS/NER, rather than failing obscurely.

## Requirements

Python 3.9+. Nothing else.

## Contributing

**If you speak Urdu, you can improve this library without reading a line of its code.**

The transliteration lexicon in [`src/urdukit/transliteration.py`](src/urdukit/transliteration.py) is a plain dictionary of 143 Urdu→Roman pairs. Two things are needed:

1. **Corrections.** The entries were originally machine-generated. A spot-check of the first 118 found 1 wrong, and words added since haven't had a dedicated native-speaker pass either. If a romanization isn't how you'd actually type the word, that's a bug — please say so.
2. **More words.** Common words are still missing — `بازار`, `کھیل`, `سفر`, `خط`, `چائے` and hundreds more. Each one added is a word the library stops guessing at.

```python
LEXICON: dict[str, str] = {
    ...
    "بازار": "bazaar",   # add lines like this
    "چائے": "chai",
}
```

Everyday Roman Urdu — how people actually text — not scholarly transliteration. `mohabbat`, not `muḥabbat`.

An issue saying "`X` should be `Y`" is a complete contribution. You don't need to open a pull request, and you don't need to know Python.

Also welcome: stopwords that are missing or shouldn't be there, stemmer suffixes that over- or under-strip, and any Urdu text this library handles wrongly.

```bash
git clone https://github.com/syahra712/urdukit
cd urdukit
pip install -e ".[dev]"
pytest
```

## Known limitations

Stated up front rather than discovered later:

- **Transliteration of unknown words is 16.0%/34.8% accurate** (most-attested / any-attested, Dakshina test split). See above.
- **The tokenizer does not recover omitted spaces by default.** `کتابہے` stays one token instead of becoming `کتاب` + `ہے`. `word_tokenize(..., recover_spaces=True)` opts in to lexicon-bounded recovery — it only splits where a vocabulary you supply resolves the split unambiguously — and `to_roman(..., recover_spaces=True)` does the same against its own tables. It is off by default in both because it is wrong often enough to matter: measured on 24,922 real single words from Dakshina, it split 1.2% of them (`کاجو`, cashew, became `کا` + `جو`). General word segmentation is still unsolved; see [issue #3](https://github.com/syahra712/urdukit/issues/3).
- **Stemming is not lemmatization.** `گیا` will not become `جانا`, and Arabic broken plurals (`کتاب` → `کتب`) need a dictionary. Words whose last letters look like an ending get over-stemmed (`ہفتے`, week, → `ہف`); a short hand-written `PROTECTED` list covers the commonest (`پانی`, `دنیا`, `کراچی`). Measured against the lemmas of the Urdu UD treebank the stemmer reaches 73.7% F1 on the test split — see [Benchmarks](#benchmarks).
- **No POS tagging or NER.** Use [stanza](https://stanfordnlp.github.io/stanza/) for those.

## License

MIT
