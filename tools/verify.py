#!/usr/bin/env python3
"""Checks for the generated dictionary.

1. Morphology equivalence: for a sample of upstream roots, every surface form the OLD
   dictionary generates (root + up to two suffixes), converted with bitg, must be exactly
   the set of forms the NEW dictionary generates from the converted root.
2. Spell-check behaviour with real Hunspell (or spylls): tests/words.tsv.

    python -I tools/verify.py --upstream DIR [--hunspell PATH] [--sample N]
"""
from __future__ import annotations

import argparse
import random
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


class Aff:
    def __init__(self, text: str):
        self.sfx: dict[str, list[tuple[str, str, str, re.Pattern]]] = defaultdict(list)
        for l in text.splitlines():
            p = l.split()
            if len(p) >= 5 and p[0] == "SFX":
                strip = "" if p[2] == "0" else p[2]
                add, _, cont = p[3].partition("/")
                add = "" if add == "0" else add
                self.sfx[p[1]].append((strip, add, cont, re.compile("(?:" + p[4] + ")$")))

    def forms(self, root: str, flags: str) -> set[str]:
        out = {root}
        for f in flags:
            for strip, add, cont, cond in self.sfx.get(f, ()):
                if not root.endswith(strip) or not cond.search(root):
                    continue
                w1 = root[: len(root) - len(strip)] + add
                out.add(w1)
                for c in cont:
                    for s2, a2, _, c2 in self.sfx.get(c, ()):
                        if w1.endswith(s2) and c2.search(w1):
                            out.add(w1[: len(w1) - len(s2)] + a2)
        return out


def parse_dic(text: str) -> list[tuple[str, str]]:
    res = []
    for l in text.splitlines()[1:]:
        if l.strip():
            w, _, f = l.partition("/")
            res.append((w, f))
    return res


def equivalence(up: Path, exe: Path, n: int) -> int:
    old_aff = Aff((up / "uz_UZ.aff").read_text(encoding="utf-8"))
    new_aff = Aff((ROOT / f"{build.BASENAME}.aff").read_text(encoding="utf-8"))
    old = [e for e in parse_dic((up / "uz_UZ.dic").read_text(encoding="utf-8")) if not build.CYRILLIC.search(e[0])]
    new = parse_dic((ROOT / f"{build.BASENAME}.dic").read_text(encoding="utf-8"))
    new_by = defaultdict(list)
    for w, f in new:
        new_by[w].append(f)
    rnd = random.Random(2026)
    # Random sample plus every root whose ending changes shape (oʻ gʻ sh ch at the end).
    tricky = [e for e in old if re.search("(?:[oOgG]\u02bb|[sScC][hH])$", e[0])]
    tricky = rnd.sample(tricky, min(n // 2, len(tricky)))
    sample = rnd.sample(old, min(n, len(old))) + tricky
    conv_roots = build.convert_lines(exe, [w for w, _ in sample])
    fails, total, by_end = [], 0, defaultdict(int)
    pending: list[tuple[tuple[str, str], str, list[str]]] = []

    def flush() -> None:
        nonlocal total
        flat = [x for _, _, fs in pending for x in fs]
        it = iter(build.convert_lines(exe, flat))
        for (w, f), cw, fs in pending:
            want = {next(it) for _ in fs}
            want = {build.det(x) if build.OKINA in x else x for x in want}
            got = new_aff.forms(cw, f)
            total += len(want)
            if want != got:
                fails.append((w, f, sorted(want - got)[:5], sorted(got - want)[:5]))
                by_end[w[-2:]] += 1
        pending.clear()

    size = 0
    for (w, f), cw in zip(sample, conv_roots):
        cw = build.det(cw) if build.OKINA in cw else cw
        fs = sorted(old_aff.forms(w, f))
        pending.append(((w, f), cw, fs))
        size += len(fs)
        if size > 400_000:
            flush()
            size = 0
    flush()
    print(f"[equivalence] roots={len(sample)} (random {n} + {len(tricky)} ending in oʻ/gʻ/sh/ch) "
          f"surface forms={total} mismatching roots={len(fails)}")
    for x in fails[:25]:
        print("   ", x)
    if by_end:
        print("    mismatches by root ending:", dict(by_end))
    return len(fails)


def spell(hunspell: str | None, words: list[str]) -> tuple[set[str], dict[str, list[str]]]:
    """Returns (accepted words, suggestions for rejected words)."""
    d = str(ROOT / build.BASENAME)
    if hunspell:
        data = ("\n".join(words) + "\n").encode("utf-8")
        out = subprocess.run([hunspell, "-i", "UTF-8", "-d", d, "-a"], input=data, capture_output=True,
                             check=True, env={"LC_ALL": "C.UTF-8", "SystemRoot": "C:\\Windows"}).stdout.decode("utf-8")
        acc, sugg = set(), {}
        # Ispell pipe protocol: a banner line, then one block per input line, blocks end with "".
        body = out.replace("\r\n", "\n").split("\n", 1)[1]
        blocks = body.split("\n\n")
        if len(blocks) < len(words):
            raise SystemExit(f"hunspell returned {len(blocks)} blocks for {len(words)} words")
        for w, block in zip(words, blocks):
            res = [r for r in block.split("\n") if r]
            r = res[0] if len(res) == 1 else ("&?" if res else "")
            if r.startswith(("*", "+", "-")):
                acc.add(w)
            elif r.startswith("&"):
                sugg[w] = [s.strip() for s in r.split(":", 1)[1].split(",")]
            else:
                sugg[w] = []
        return acc, sugg
    from spylls.hunspell import Dictionary  # pure-Python fallback
    dic = Dictionary.from_files(d)
    acc, sugg = set(), {}
    for w in words:
        if dic.lookup(w):
            acc.add(w)
        else:
            sugg[w] = list(dic.suggest(w))[:15]
    return acc, sugg


def behaviour(hunspell: str | None) -> int:
    rows = []
    for l in (ROOT / "tests" / "words.tsv").read_text(encoding="utf-8").splitlines():
        if l and not l.startswith("#"):
            rows.append(l.split("\t"))
    good = [r[1] for r in rows if r[0] == "ok"]
    bad = [(r[1], r[2]) for r in rows if r[0] == "old"]
    acc, sugg = spell(hunspell, good + [b for b, _ in bad])
    g_ok = [w for w in good if w in acc]
    b_rej = [b for b, _ in bad if b not in acc]
    b_top = [b for b, e in bad if e in sugg.get(b, [])[:1]]
    b_any = [b for b, e in bad if e in sugg.get(b, [])]
    eng = "hunspell" if hunspell else "spylls"
    print(f"[behaviour/{eng}] new-alphabet accepted: {len(g_ok)}/{len(good)}")
    print(f"[behaviour/{eng}] old spellings rejected: {len(b_rej)}/{len(bad)}; "
          f"correct new form 1st suggestion: {len(b_top)}/{len(bad)}; in suggestions: {len(b_any)}/{len(bad)}")
    for w in good:
        if w not in acc:
            print("    NOT ACCEPTED:", w, sugg.get(w, [])[:5])
    for b, e in bad:
        if b in acc:
            print("    OLD ACCEPTED:", b)
        elif e not in sugg.get(b, []):
            print(f"    MISSING SUGGESTION: {b} -> {e}; got {sugg.get(b, [])[:6]}")
    return (len(good) - len(g_ok)) + (len(bad) - len(b_rej))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True)
    ap.add_argument("--hunspell", default=shutil.which("hunspell"))
    ap.add_argument("--spylls", action="store_true", help="use spylls even if hunspell is found")
    ap.add_argument("--sample", type=int, default=3000)
    ap.add_argument("--bitg-src")
    ap.add_argument("--skip-equivalence", action="store_true")
    a = ap.parse_args()
    exe = build.build_converter(a.bitg_src)
    bad = 0 if a.skip_equivalence else equivalence(Path(a.upstream), exe, a.sample)
    bad += behaviour(None if a.spylls else a.hunspell)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
