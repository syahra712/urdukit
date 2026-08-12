# Contributing to urdukit

The most valuable contributions to this project need **Urdu, not Python.**

## The highest-leverage thing you can do

Add words to the transliteration lexicon in [`src/urdukit/transliteration.py`](src/urdukit/transliteration.py).

Urdu script does not record short vowels. `استاد` is *ustad*, but nothing in ا-س-ت-ا-د tells a program the first vowel is *u*. So the rule-based fallback manages only **15.0%** exact match against the most-attested romanization on the Dakshina benchmark (**32.8%** if any attested spelling counts), while a lexicon word is returned exactly.

Every word you add moves from a guess to an answer.

```python
LEXICON: dict[str, str] = {
    ...
    "استاد": "ustad",      # add lines like this
    "خوبصورت": "khoobsurat",
}
```

Use everyday Roman Urdu — how people actually text — not scholarly ALA-LC with macrons and underdots. `mohabbat`, not `muḥabbat`.

If a word has two common spellings, pick the more frequent one and don't agonise; open an issue if you think the choice is genuinely contested.

## Also genuinely useful

- **Stopwords** that are missing from [`stopwords.py`](src/urdukit/stopwords.py), or entries that shouldn't be there.
- **Stemmer suffixes** that over-strip or under-strip. See the deliberately-excluded list in [`stemming.py`](src/urdukit/stemming.py) — `ستان` was removed because it turned `پاکستان` into `پاک`.
- **Any Urdu text this library handles wrongly.** A failing example in an issue is a real contribution; you do not need to fix it yourself.

## Setup

```bash
git clone https://github.com/syahra712/urdukit
cd urdukit
pip install -e ".[dev]"
pytest
```

## Ground rules for code

**No dependencies.** Not "few" — none. `urdukit` imports nothing outside the standard library, and a test asserts it. This is not stylistic: `urduhack` became uninstallable because its package `__init__` imported TensorFlow unconditionally, and six years of issue reports came from that one line. Any model-backed feature must be lazily imported inside the function that needs it.

**Tests describe behaviour, not implementation.** Tests that reproduce a real urduhack issue cite its number. If you fix something, add the failing case as a test first.

**Known limitations get pinned, not hidden.** Where the library is wrong on purpose — the tokenizer not recovering omitted spaces, the stemmer over-stemming `کراچی` — there is a test asserting the current behaviour. That way, improving it is a visible, deliberate change rather than a silent one. If you improve one, update its test and say so in the PR.

**Don't optimise a metric at the cost of the output.** A transliteration variant once scored higher by emitting `smndr` for `سمندر`. It was rejected: pronounceable-but-wrong beats unpronounceable-and-technically-closer. There is a test asserting every fallback output contains a vowel.

## Running checks

```bash
pytest                      # tests
ruff check src tests        # lint
ruff format src tests       # format
```

Note that `ruff`'s ambiguous-Unicode rules (RUF001/2/3) are disabled in [`pyproject.toml`](pyproject.toml). They flag characters that resemble Latin ones to catch homoglyph attacks, and in an Urdu library they fire 168 times on entirely correct code.

## Loanwords — the easiest high-value contribution

A large share of modern Urdu is English borrowed wholesale. Those words romanize to their **English spelling**, which no phonetic rule can produce:

```
آرگنائزیشن  →  organisation     (the rules produce "aaraganayazishan")
انٹرنیٹ     →  internet         ("anataranit")
پرنٹر       →  printer          ("paranatar")
```

The `LOANWORDS` table in [`src/urdukit/transliteration.py`](src/urdukit/transliteration.py) has 123 of these. Where it applies it is near-exact — on the benchmark words it covers, accuracy goes from 0% to 92%. It only has 123 entries, so it covers very little.

**This is the easiest thing to get right**, because the answer is just an English word — no judgement about Roman Urdu spelling is involved. If you can read the Urdu and recognise the English word, you can add the entry.

Multi-word loanwords (`ویب سائٹ` → `website`) are not supported yet: lookup happens after tokenization, so a two-token key can never match. Fixing that is [issue #4](https://github.com/syahra712/urdukit/issues/4) territory too.
