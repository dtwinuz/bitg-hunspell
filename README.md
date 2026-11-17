# bitg-hunspell — Özbek imlo luğati, 2026 alifbo

Yangi 2026-yilgi özbek lotin alifbosi (**Ö Ğ Ş Ç**, tutuq **ʼ**) uçun birinçi Hunspell imlo luğati.
U [uz-hunspell](https://github.com/uzbek-net/uz-hunspell) loyihasidan (eski alifbo) [bitg](https://bitg.uz)
bilan avtomatik ögirilgan va Firefox hamda LibreOffice uçun qadoqlangan.

[![release](https://img.shields.io/github/v/release/dtwinuz/bitg-hunspell?label=release)](https://github.com/dtwinuz/bitg-hunspell/releases/latest)
[![ci](https://github.com/dtwinuz/bitg-hunspell/actions/workflows/ci.yml/badge.svg)](https://github.com/dtwinuz/bitg-hunspell/actions/workflows/ci.yml)
[![license](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)

**[bitg.uz](https://bitg.uz) · [Jonli demo (bitg)](https://wonmor.io/demo/bitg/) · [Releases](https://github.com/dtwinuz/bitg-hunspell/releases/latest) · [VALIDATION.md](VALIDATION.md) · [English](#english)**

```text
$ echo "özbek şahar oʻzbek shahar çoy" | hunspell -i utf-8 -d uz_UZ-2026 -a
@(#) International Ispell Version 3.2.06 (but really Hunspell 1.7.2)
*
*
& oʻzbek 1 12: özbek
& shahar 2 19: şahar, sahar
*
```

| | |
|---|---|
| Sözlar (asos) | 95 103 (+ ot, sifat, feʼl qöşimçalari) |
| Fayllar | `uz_UZ-2026.dic`, `uz_UZ-2026.aff` |
| Firefox | `dist/bitg-hunspell-<versiya>-firefox.xpi` (til kodi `uz-Latn-UZ`) |
| LibreOffice | `dist/bitg-hunspell-<versiya>-libreoffice.oxt` (til `uz-Latn-UZ`, LibreOffice'da *Uzbek Latin*) |
| Litsenziya | GPL-3.0 (uz-hunspell kabi) |

### Nima qiladi
- Yangi yozuvdagi sözlarni qabul qiladi: `özbek`, `şahar`, `çoy`, `ğişt`, `töğri`, `maʼno`.
- Eski yozuvni xato deb belgilaydi va yangisini taklif qiladi: `oʻzbek` → `özbek`, `shahar` → `şahar`,
  `o'zbek` → `özbek`, `choy` → `çoy`.
- Tutuqni `'` yoki `’` bilan yozish ham qabul qilinadi (`ma'no` = `maʼno`).
- Diakritiksiz terilgan harflar uçun ham taklif beradi (`ozbek` → `özbek`).

### Tekşiruv
Hunspell 1.7.2 bilan 129/129 yangi söz qabul qilindi. 66/66 eski yozuv rad etildi va 66 tasida
töğri söz birinçi taklif böldi. Qöşimçalar 1 500 ildizdagi 124 mln şaklda eski luğat bilan aynan
bir xil işladi. 3 000 gapli korpusda qamrov 93,15%: eski luğatniki 92,81%. Batafsil: `VALIDATION.md`.

### Örnatish
- **Firefox:** `.xpi` faylni `about:addons` → ⚙ → *Install Add-on From File* orqali öçiring.
  Keyin matn maydonida öng tugma → *Languages* → *Uzbek (Latin, Uzbekistan)*.
- **LibreOffice:** *Tools → Extension Manager → Add* → `.oxt`. Matn tilini *Uzbek* (Latin) qiling.
  Eski alifbodagi özbek luğati ham örnatilgan bölsa, uni öçiring: ikkalasi bir xil *Uzbek Latin* tilida.
- **Hunspell (Linux/macOS):** `.dic` va `.aff` ni `~/.hunspell` yoki `/usr/share/hunspell` ga
  nusxalang: `hunspell -d uz_UZ-2026`.

### Qayta qurish
```sh
python -I build.py                 # uz-hunspell ni belgilangan commit'da yuklab, hammasini quradi
python -I build.py --bitg-src ../bitg   # bitg ning lokal nusxasi bilan
python -I tools/verify.py --upstream .cache/uz-hunspell   # tekshiruvlar
"<LibreOffice>/program/python.exe" tools/lo_test.py --soffice "<LibreOffice>/program/soffice.exe" --oxt dist/bitg-hunspell-<versiya>-libreoffice.oxt   # haqiqiy LibreOffice'da
```
Kerak: Python 3.10+, git, Rust (cargo). Natija bayt-ma-bayt bir xil (zip vaqtlari belgilangan).

### Mualliflar
Luğatning asosiy mehnati — **uz-hunspell** mualliflariniki: Alisher Jalolov (2019), Bilolbek Normöminov
(2025) va [uzbek-net](https://github.com/uzbek-net) hamjamiyati. Bu loyiha faqat alifboni ögiradi va qadoqlaydi.

---

## English

The first Hunspell spell-check dictionary for the **new 2026 Uzbek Latin alphabet** (Ö Ğ Ş Ç instead of
oʻ gʻ sh ch; the tutuq ʼ stays). It is generated from [uz-hunspell](https://github.com/uzbek-net/uz-hunspell)
(old alphabet, GPL-3.0) with the [bitg](https://github.com/dtwinuz/bitg) converter and packaged as a
Firefox dictionary add-on and a LibreOffice extension; ready-made `.xpi` and `.oxt` files are on the
[Releases](https://github.com/dtwinuz/bitg-hunspell/releases/latest) page.

### How it is built
`build.py` (standard library only):
1. Clones uz-hunspell at a pinned commit (`8a1c3b2786da`).
2. Builds `converter/`, a 30-line Rust wrapper around `bitg-core` (pinned commit `dc50fb269b4f`) with
   apostrophe restoration, the English guard and Cyrillic conversion **turned off**: the source is already
   correctly spelled, so `boda` must stay `boda`, not turn into `böda`.
3. Converts the word part of every `.dic` line (flags untouched), drops 5 entries that contain stray
   Cyrillic letters (for example `Tykveol` written with the Cyrillic letter U+044B instead of `y`), removes exact duplicates.
4. Converts the `.aff`: strip/affix strings and conditions of all 19 507 `SFX` rules, `TRY`, `KEY`, `REP`.
   Before doing so it asserts that bitg and a plain letter map agree on all 15 438 distinct affix strings.
5. Writes `dist/*.xpi` and `dist/*.oxt` as reproducible zips.

### Decisions
- **Locale tags.** There is no BCP 47 tag for "2026 orthography". LibreOffice maps Uzbek Latin
  (LanguageType 0x0443) to `uz-Latn-UZ`, so the `.oxt` registers that tag. A dictionary registered as
  `uz-UZ` loads but Writer never consults it (the bug in 0.1.0; `tools/lo_test.py` guards against it).
  The `.oxt` replaces any old-alphabet Uzbek dictionary in use.
  Firefox accepts any tag; the add-on uses `uz-Latn-UZ` so it does not collide with the existing
  old-alphabet "Uzbek Spell Checker" add-on (which owns `uz`/`uz-UZ`), and still matches pages marked
  `lang="uz"`. File names are `uz_UZ-2026.*`; `LANG uz_UZ` stays inside the `.aff`.
- **Old spellings are rejected, not silently accepted.** An `ICONV oʻ ö` / `sh ş` table would make
  Hunspell accept `oʻzbek` and `shahar`, which defeats the purpose of a new-alphabet checker, and `sh → ş`
  is wrong for words where s and h are separate letters (`Ishoq`, `mushaf`). Instead, the suggestion
  tables map every old-alphabet form (`oʻ o‘ o’ o\` gʻ … sh ch`, all cases) to the new letter, so the
  correct word comes first. `REP` changes only one place per suggestion, so the same mapping is also in
  multi-character `MAP` groups (`MAP ö(oʻ)(o‘)…o`, `MAP ş(sh)s`). Hunspell tries every combination of
  those, which fixes words with several old letters: `gʻisht` → `ğişt`, `oʻqituvchi` → `öqituvçi`.
- **ICONV only for the tutuq.** `'` and `’` are converted to `ʼ` on input, because typing the tutuq
  with the ASCII apostrophe is a keyboard limitation, not an old spelling. `ʻ` (U+02BB, the old oʻ/gʻ mark)
  is *not* converted, so `oʻzbek` is still flagged.
- **`MAP`/`KEY` for missing diacritics:** o/ö, g/ğ, s/ş, c/ç are related, so `ozbek` suggests `özbek`.

### Validation (summary, details in `VALIDATION.md`)
- Morphology: 1,500 roots and 124,294,177 generated surface forms give identical results in the old and
  new dictionaries after conversion, with 0 mismatches.
- Hunspell 1.7.2 accepts 129/129 new-alphabet words and rejects 66/66 old spellings. For all 66, the
  correct new word is the first suggestion.
- Corpus (3,000 Leipzig sentences): 93.15% of tokens are covered, against 92.81% for uz-hunspell on the
  same text in the old alphabet. 0 words became misspelled because of the conversion.
- `addons-linter`: 0 errors, 0 warnings.

### Credits and license
All lexical work comes from **uz-hunspell** — Alisher 'U2B3K' Jalolov (2019), Bilolbek 'itsbilolbek'
Normoʻminov (2025) and the uzbek-net community. Conversion: bitg (MIT/Apache-2.0). This derived work is
licensed under **GPL-3.0**, see `LICENSE`.
