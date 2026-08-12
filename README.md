# urdukit

A modern, dependency-free NLP toolkit for Urdu — normalization, tokenization, stopwords, stemming and Roman Urdu transliteration.

```bash
pip install urdukit
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
content = remove_stopwords(tokens)   # ['مجھے', 'کتابیں', 'پڑھنا', 'اچھا', 'لگتا']
stem_tokens(content)                 # ['مجھ', 'کتاب', 'پڑھ', 'اچھ', 'لگ']
```

190 curated stopwords, stored normalized so Arabic-codepoint variants still match.

⚠️ `نہیں` ("not") is a stopword. Strip it before sentiment analysis and you invert your labels.

### Transliteration

The feature [#156](https://github.com/urduhack/urduhack/issues/156) and [#146](https://github.com/urduhack/urduhack/issues/146) asked for.

```python
from urdukit import to_roman, to_urdu

to_roman("میں پاکستان سے ہوں۔")   # 'mein pakistan se hun.'
to_urdu("mein pakistan se hun")   # 'میں پاکستان سے ہوں'
```

**Measured accuracy, honestly:**

| | Exact match |
|---|---|
| Lexicon words (118) | **100%** |
| Held-out words (rules only) | **25%** |

25% is low, and it is low for a structural reason: **Urdu script does not record short vowels.** `استاد` is *ustad*, but nothing in ا-س-ت-ا-د says the first vowel is *u*. No suffix rule can recover information that was never written down.

So there are two layers: an exact lexicon, and a rule-based fallback that aims for a *pronounceable approximation* rather than a correct answer. Adding a word to the lexicon moves it from ~25% to 100% — which makes lexicon contributions the single highest-leverage change anyone can make here. See [Contributing](#contributing).

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

The most valuable contribution needs **Urdu, not familiarity with this codebase**: add words to the transliteration lexicon in [`src/urdukit/transliteration.py`](src/urdukit/transliteration.py). Every word added moves from a ~25% guess to a 100% answer.

Also welcome: stopwords that are missing, stemmer suffixes that over- or under-strip, and any Urdu text this library handles wrongly — a failing example in an issue is genuinely useful.

```bash
git clone https://github.com/syahra712/urdukit
cd urdukit
pip install -e ".[dev]"
pytest
```

## Known limitations

Stated up front rather than discovered later:

- **Transliteration of unknown words is ~25% accurate.** See above.
- **The tokenizer does not recover omitted spaces.** `کتابہے` stays one token instead of becoming `کتاب ہے`. Urdu's ten non-joining letters (ا د ڈ ذ ر ڑ ز ژ و ے) mean writers routinely omit that space, but splitting it back needs a lexicon.
- **Stemming is not lemmatization.** `گیا` will not become `جانا`, and Arabic broken plurals (`کتاب` → `کتب`) need a dictionary. Proper nouns ending in productive suffixes get over-stemmed: `کراچی` → `کراچ`.
- **No POS tagging or NER.** Use [stanza](https://stanfordnlp.github.io/stanza/) for those.

## License

MIT
