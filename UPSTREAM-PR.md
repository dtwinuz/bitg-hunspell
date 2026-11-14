# Proposal for uzbek-net/uz-hunspell

Text for an issue (or PR description) at https://github.com/uzbek-net/uz-hunspell. English, ready to paste.

---

**Title:** Offer: a 2026-alphabet variant (ö ğ ş ç) generated from uz_UZ

Hi, and thank you for uz-hunspell. It is the best open Uzbek spelling dictionary we know of.

The new Uzbek Latin alphabet replaces oʻ gʻ sh ch with **ö ğ ş ç** and keeps the tutuq **ʼ**. We needed a
spell checker for it, so we generated one from your `uz_UZ.dic` / `uz_UZ.aff` and would like to give it
back, either as a new file pair in this repository (for example `uz_UZ-2026.dic/.aff`) or just as a link
from your README, whichever you prefer.

**How it is generated (no hand edits):**
- Only the word part of each `.dic` line is converted; flags stay as they are. The `.aff` keeps all
  19,507 `SFX` rules. Only their strip, affix and condition strings are converted
  (`[^kgqgʻ]` → `[^kgqğ]`, `gʻga` → `ğga`).
- Converter: [bitg](https://github.com/dtwinuz/bitg) (MIT/Apache-2.0), with its text heuristics turned
  off because your data is already correctly spelled. It keeps s+h words such as `Ishoq` and `mushaf`
  as s+h. A plain letter map would wrongly give `Işoq`.
- One script (`build.py`) rebuilds everything from a pinned commit of this repo, so a new upstream
  release can be converted again in seconds.

**Checks:**
- Morphology equivalence: we expanded every form (root + up to two suffixes) for a random sample of roots
  plus roots that end in oʻ/gʻ/sh/ch, with both dictionaries. Converting each old form gives exactly the
  set of forms the new dictionary generates, with 0 mismatches. The figures are in `VALIDATION.md`.
- Corpus coverage on 3,000 Leipzig sentences: the new dictionary on the new-alphabet text covers 93.15%
  of tokens. `uz_UZ` on the same sentences in the old alphabet covers 92.81%. No word that `uz_UZ`
  accepts is rejected after conversion.
- Old spellings are rejected and the new word is suggested (`oʻzbek` → `özbek`, `gʻisht` → `ğişt`).
  This works through `REP`/`MAP` entries. `ICONV` would make old spellings pass.

**Things we found in the current data:**
- 5 Latin entries contain the Cyrillic letter U+044B (yeru) instead of a Latin letter: `Alkilsulfonat?`,
  `B?strumgel`, `Exinokandin?`, `T?kveol`, `Xondroitinsulfat?` (`?` = U+044B; `uz_UZ.dic` lines 2181,
  14299, 22818, 84751, 89434). We drop them in the 2026 variant.
- The `NOSUGGEST`/`FORCEUCASE` flag is the Cyrillic letter U+044F (ya). In the default `FLAG` mode this is two bytes.
  It works, but an ASCII flag would be safer.
- `SFX H . gim/…`: the strip field is `.`, so these rules only fire for roots that end in a literal dot.
  This looks unintended.
- `BREAK 1` is followed by a single `BREAK -`. This is fine, just noting it.
- `kompyuter` is missing, but `kompyyuter` is present (typo?).

The license stays GPL-3.0 and all credit stays with you. The generated `.aff` keeps your copyright
lines. If you would rather not host it, a README link is enough, and we are happy to send fixes for the
items above as separate PRs.
