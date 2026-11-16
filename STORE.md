# Store listings

Text for addons.mozilla.org (AMO) and extensions.libreoffice.org. Copy it into the forms when you upload.

## Common facts

| Field | Value |
|---|---|
| Name (uz) | Özbek imlo luğati (2026 alifbo) |
| Name (en) | Uzbek spelling dictionary (2026 Latin alphabet) |
| Version | 0.1.0 (see `VERSION`) |
| License | GNU GPL v3.0 (derived from uz-hunspell, GPL-3.0) |
| Homepage | https://bitg.uz |
| Source code | the git repository of this project (link it once it is public) |
| Firefox add-on ID | `uz-2026@bitg.uz` |
| Firefox dictionary language | `uz-Latn-UZ` |
| LibreOffice identifier / locale | `uz.bitg.hunspell.uz2026` / `uz-Latn-UZ` (Uzbek Latin) |
| Category (AMO) | Dictionaries & Language Packs → Dictionary |
| Category (LibreOffice) | Dictionary |
| Files | `dist/bitg-hunspell-0.1.0-firefox.xpi`, `dist/bitg-hunspell-0.1.0-libreoffice.oxt` |

## Summary (≤ 250 characters)

**uz:** Yangi özbek lotin alifbosi (Ö Ğ Ş Ç, ʼ) uçun imlo tekşiruvi. 95 mingdan ortiq söz va qöşimçalar.
Eski yozuvdagi sözlarni xato deb belgilab, yangi yozuvini taklif qiladi.

**en:** Spell checker for the new 2026 Uzbek Latin alphabet (Ö Ğ Ş Ç, ʼ). Over 95,000 words with suffix rules.
Old-alphabet spellings are flagged and the new spelling is suggested.

## Description

**uz:**
> 2026-yilgi yangi özbek lotin alifbosida yozuvçilar uçun birinçi imlo luğati.
>
> - Yangi harflar: Ö, Ğ, Ş, Ç va tutuq belgisi ʼ.
> - 95 mingdan ortiq asos söz, ot, sifat va feʼllarning qöşimçali şakllari bilan.
> - Eski yozuvni (oʻ, gʻ, sh, ch) xato deb belgilaydi va töğrisini taklif qiladi: oʻzbek → özbek, shahar → şahar.
> - Tutuqni ' yoki ’ bilan yozsangiz ham qabul qiladi (ma'no = maʼno).
> - Internetsiz işlaydi, heç qanday maʼlumot yiğmaydi.
>
> Luğat uz-hunspell (uzbek-net) loyihasi asosida bitg dasturi bilan ögirilgan. Asosiy mehnat uçun
> Alisher Jalolov, Bilolbek Normöminov va uzbek-net hamjamiyatiga rahmat.
>
> Firefox'da: matn maydonida öng tugma → Tillar → Uzbek (Latin, Uzbekistan).

**en:**
> The first spell-check dictionary for the new 2026 Uzbek Latin alphabet.
>
> - New letters: Ö, Ğ, Ş, Ç and the tutuq ʼ.
> - More than 95,000 base words, with suffixed forms of nouns, adjectives and verbs.
> - Old-alphabet spellings (oʻ, gʻ, sh, ch) are flagged and the new spelling is suggested:
>   oʻzbek → özbek, shahar → şahar.
> - The tutuq may be typed as ' or ’ (ma'no = maʼno).
> - Works offline and collects no data.
>
> Converted from the uz-hunspell project (uzbek-net) with bitg. All lexical credit goes to Alisher
> Jalolov, Bilolbek Normoʻminov and the uzbek-net community.
>
> In Firefox: right-click a text field → Languages → Uzbek (Latin, Uzbekistan).

## Privacy

**en:** This add-on/extension contains only dictionary files (word list and affix rules). It has no code,
makes no network requests, and does not collect, store or transmit any data. The Firefox manifest
declares `data_collection_permissions: { required: ["none"] }`.

**uz:** Bu kengaytma faqat luğat fayllaridan iborat. Unda dastur kodi yöq, internetga ulanmaydi, heç
qanday maʼlumot yiğmaydi, saqlamaydi va yubormaydi.

## License note for reviewers

The dictionary is a derived work of uz-hunspell (https://github.com/uzbek-net/uz-hunspell, GPL-3.0),
so it is distributed under GPL-3.0. The full license is included as `LICENSE` in both packages. The
source and the build script are in this repository. Run `python -I build.py` to rebuild byte-identical
packages.

## AMO reviewer notes

There is no executable code. The package holds `manifest.json`, `dictionaries/uz_UZ-2026.dic`,
`dictionaries/uz_UZ-2026.aff` and `LICENSE`. `addons-linter` reports 0 errors, 0 warnings and
0 notices.
