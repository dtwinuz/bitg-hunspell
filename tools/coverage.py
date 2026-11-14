#!/usr/bin/env python3
"""Corpus coverage: share of word tokens Hunspell accepts.

Uses bitg's public benchmark (bitg/eval/uz.tsv: 3000 Leipzig sentences, column 2 = old Latin,
column 3 = new 2026 Latin). The new dictionary is run on column 3, the upstream dictionary on
column 2 (apostrophes normalised to ʻ/ʼ), so both numbers measure the same sentences.

    python -I tools/coverage.py --upstream DIR --eval PATH/uz.tsv [--hunspell PATH]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[^\W\d_]+(?:[-ʻʼ'’‘`][^\W\d_]+)*")


def norm_old(s: str) -> str:
    s = re.sub(r"([oOgG])['’‘`ʼ]", "\\1\u02bb", s)
    return re.sub(r"['’‘`]", "\u02bc", s)


def rejected(hunspell: str, dic: str, words: list[str]) -> set[str]:
    data = ("\n".join(words) + "\n").encode("utf-8")
    out = subprocess.run([hunspell, "-i", "UTF-8", "-d", dic, "-l"], input=data, capture_output=True,
                         check=True, env={"LC_ALL": "C.UTF-8", "SystemRoot": "C:\\Windows"}).stdout
    return set(out.decode("utf-8").split())


def measure(hunspell: str, dic: str, texts: list[str]) -> tuple[int, int, int, int]:
    toks = [t for s in texts for t in WORD.findall(s)]
    uniq = sorted(set(toks))
    bad = rejected(hunspell, dic, uniq)
    ok_tok = sum(1 for t in toks if t not in bad)
    return ok_tok, len(toks), len(uniq) - len(bad & set(uniq)), len(uniq)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True)
    ap.add_argument("--eval", required=True)
    ap.add_argument("--hunspell", default=shutil.which("hunspell"))
    a = ap.parse_args()
    rows = [l.split("\t") for l in Path(a.eval).read_text(encoding="utf-8").splitlines()
            if l and not l.startswith("#")]
    rows = [r for r in rows if len(r) >= 3]
    for name, dic, texts in (
        ("uz_UZ (upstream, old alphabet)", str(Path(a.upstream) / "uz_UZ"), [norm_old(r[1]) for r in rows]),
        ("uz_UZ-2026 (new alphabet)", str(ROOT / "uz_UZ-2026"), [r[2] for r in rows]),
    ):
        ok, tot, uok, utot = measure(a.hunspell, dic, texts)
        print(f"{name:32} sentences={len(rows)} tokens {ok}/{tot} = {100 * ok / tot:.2f}%  "
              f"unique {uok}/{utot} = {100 * uok / utot:.2f}%")


if __name__ == "__main__":
    main()
