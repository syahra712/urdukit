# Changelog

Notable changes to urdukit. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [0.2.0] - unreleased

### Fixed

- **Quadratic-time regexes.** `normalize`, `normalize_punctuation`, `replace_urls`,
  `replace_emails` and `all_punctuations_space` took tens of seconds on a
  50 KB run of spaces or of `a-`/`a.` pairs. All are now linear.
- **`normalize` corrupted non-prose text.** `12:30` became `12: 30`,
  `http://` became `http: //`, the Urdu decimal `۵۔۲` became `۵۔ ۲`, and a
  closing quote was pushed away from the sentence it closed.
- **The tokenizer split words it should not have.** Text using Arabic
  codepoints (`علي`) was shredded unless normalized first; words ending in
  `ۃ`, words carrying an honorific sign (`محمدؐ`) or a tatweel, and accented
  Latin (`café`) were split; URLs and e-mail addresses came out as a dozen
  punctuation tokens. Each is now one token.
- **`to_roman` ignored vowel marks.** Diacritics were stripped before the
  rules ran, so the one input where the vowels are known was romanized as if
  they were not. `مُحَمَّد` is now `muhammad`, and `اِس` / `اُس` are `is` / `us`.
- **`to_roman` dropped ع**, giving `li` for `علی`. It is now `ali`.
- `to_roman` no longer writes `( salam)` or `50 %`, and converts Urdu digits.
- `to_urdu` now knows the loanword table (`doctor` → `ڈاکٹر`) and converts
  `. , ; ?` to their Urdu forms, including on a token of their own.
- `replace_numbers` and `digits_space` now handle Arabic-Indic digits (٠-٩).
- `fold_arabic` (and so `normalize`) repairs `ےں` to `یں`. Transcoded text
  writes `مےں` for `میں` throughout; in the Urdu UD treebank it is the
  commonest spelling of the word, and stopword matching missed all of it.
- Alphanumeric tokens stay whole: `2G`, `covid19`, `G20`.
- `اخبار`, `جہاز` and `وزیر` were filed under English loanwords. They are not.

### Added

- 22 lexicon words, 20 loanwords, a `PHRASE_LOANWORDS` table for two-word
  loanwords (`ویب سائٹ` → `website`), and lexicon-bounded space recovery:
  `word_tokenize(..., recover_spaces=True, known_words=...)` and
  `to_roman(..., recover_spaces=True)`. Contributed by @mwzkhalil (#5).
- 25 stopwords: oblique pronoun forms (`مجھے`, `ہمیں`, `انہیں`, `اسے`) and,
  from the UD treebank, `کسی`, `کس`, `تحت`, `و`.
- `characters.URDU_HONORIFICS`; `ۃ` in `URDU_HAMZA_FORMS`.
- `py.typed`. The package passes `mypy --strict`.
- The benchmark script reports a rules-only figure, over words in neither
  lookup table.

### Changed

- Space recovery in `to_roman` is **opt-in**. As first contributed it was on
  by default; measured on 24,922 single words from Dakshina it split 1.2% of
  them (`کاجو` → `کا` + `جو`) and lowered benchmark accuracy.
- Dakshina test split: 15.0% → **16.0%** most-attested, 32.8% → **34.8%** any-attested.
- `STOPWORDS` grew from 187 to 212, so `remove_stopwords` removes more.

## [0.1.0]

Initial version: normalization, tokenization, stopwords, stemming,
Urdu ↔ Roman transliteration, and an `urduhack` compatibility layer.
