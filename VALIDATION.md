# Validation — bitg-hunspell 0.1.0

Inputs: uz-hunspell `8a1c3b2786da50568913c1481b50b643bfa96ec8` and bitg `dc50fb269b4ffbfbc29e3317a3591aab6a42ffd0`.
Engine: Hunspell 1.7.2 (MSYS2 `mingw-w64-ucrt-x86_64-hunspell`). spylls 0.1.7 was used as a second engine.

## 1. Build facts (`build-report.json`)

| | |
|---|---|
| upstream `.dic` entries | 95,108 |
| `uz_UZ-2026.dic` entries | 95,103 (5 entries with Cyrillic U+044B dropped) |
| `SFX` rules converted | 19,507 in 34 classes |
| distinct affix/strip strings, bitg vs. letter map | 15,438 / 15,438 identical |
| words where bitg differs from a plain letter map | 4: `Ishoq`, `ishoq`, `mushaf` (s+h, not ş), `asʼhob` → `ashob` |
| bitg left an old letter | 1: `OʻFA` (all-caps abbreviation), fixed by the letter map → `ÖFA` |
| `REP` entries | 65 (35 upstream entries, converted, plus old-alphabet → new) |

Reproduce: `python -I build.py`. The packages are byte-identical across runs:
the `.xpi` SHA-256 starts with `3a246bdb` and the `.oxt` with `b8448c4e` for the build checked here.
The hashes change when the build script changes.

## 2. Morphology equivalence (`tools/verify.py`)

For each sampled upstream root, all surface forms are expanded with the old `.aff`: the root, one
suffix, and the suffix's continuation suffixes, following Hunspell condition and strip semantics. The
forms are converted with bitg and compared with the forms the new `.aff` generates from the converted
root.

```
python -I tools/verify.py --upstream <uz-hunspell> --hunspell <hunspell.exe> --sample 1000
[equivalence] roots=1500 (random 1000 + 500 ending in oʻ/gʻ/sh/ch) surface forms=124294177 mismatching roots=0
```
Separately, all 26 roots ending in `oʻ` were checked, with 0 mismatches. This matters because the
old condition `[^kgqgʻ]` also excluded oʻ endings.

## 3. Spell-check behaviour (`tests/words.tsv`, 195 cases)

```
[behaviour/hunspell] new-alphabet accepted: 129/129
[behaviour/hunspell] old spellings rejected: 66/66; correct new form 1st suggestion: 66/66; in suggestions: 66/66
[behaviour/spylls]   new-alphabet accepted: 129/129
[behaviour/spylls]   old spellings rejected: 66/66; correct new form 1st suggestion: 64/66
```
spylls misses `g'isht` and `to'g'ri` (ASCII apostrophe plus two old letters) because it does not apply
ICONV before suggesting. Hunspell, which Firefox and LibreOffice use, does.

Sample outputs (Hunspell `-a`):
```
& oʻzbek 1 0: özbek
& gʻisht 1 0: ğişt
& toʻgʻri 1 0: töğri
& oʻqituvchi 1 0: öqituvçi
& to'g'ri 1 0: töğri
& ishonch 1 0: işonç
& ozbek 3 0: özbek, ozdek, oybek
* ma'no            (ICONV ' -> ʼ)
```

## 4. Corpus coverage (`tools/coverage.py`)

Corpus: `bitg/eval/uz.tsv`, 3,000 Leipzig `uzb_community_2017` sentences (CC BY 4.0). Column 2 is the
old Latin text and column 3 the new Latin text.

```
python -I tools/coverage.py --upstream <uz-hunspell> --eval <bitg>/eval/uz.tsv --hunspell <hunspell.exe>
uz_UZ (upstream, old alphabet)   sentences=3000 tokens 38886/41897 = 92.81%  unique 13591/15952 = 85.20%
uz_UZ-2026 (new alphabet)        sentences=3000 tokens 39026/41897 = 93.15%  unique 13623/15909 = 85.63%
```
Word by word: 0 tokens that uz_UZ accepts are rejected by uz_UZ-2026. The 75 tokens the other way round
are mostly tutuq mistakes in the old text (`aʻzo` for `aʼzo`) that bitg corrects, plus `AQSH` → `AQŞ`.

## 5. Packages

- `addons-linter` (latest, 2026-11-15) on the `.xpi`: 0 errors, 0 warnings, 0 notices.
- The `.oxt` XML files (`description.xml`, `META-INF/manifest.xml`, `dictionaries.xcu`) are well-formed.
  The extension has **not** been installed in a real LibreOffice yet, because LibreOffice is not on the
  build machine.
