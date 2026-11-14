#!/usr/bin/env python3
"""Build the 2026 Uzbek Latin Hunspell dictionary from uz-hunspell + bitg.

    python -I build.py                      # clone upstream at the pinned commit, build everything
    python -I build.py --upstream DIR       # use an existing uz-hunspell checkout
    python -I build.py --bitg-src DIR       # build the converter against a local bitg checkout

Outputs: uz_UZ-2026.dic, uz_UZ-2026.aff (repo root) and dist/*.xpi, dist/*.oxt.
Only the Python standard library, git and cargo are needed.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPSTREAM_URL = "https://github.com/uzbek-net/uz-hunspell"
UPSTREAM_REV = "8a1c3b2786da50568913c1481b50b643bfa96ec8"  # uz-hunspell master, 2025-11-18
BITG_URL = "https://github.com/dtwinuz/bitg"
BASENAME = "uz_UZ-2026"
FIREFOX_LANG = "uz-Latn-UZ"
FIREFOX_ID = "uz-2026@bitg.uz"
LIBREOFFICE_LOCALE = "uz-UZ"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
ZIP_DATE = (2026, 1, 1, 0, 0, 0)  # fixed timestamp -> byte-identical archives

OKINA = "ʻ"  # ʻ  old alphabet: oʻ gʻ
TUTUQ = "ʼ"  # ʼ  tutuq belgisi, kept in the new alphabet

# Deterministic old -> new letter map, used for affix strings, conditions and REP lines
# (fragments, not words). build() asserts bitg gives the same result on every affix string.
LETTERS = [
    ("O" + OKINA, "Ö"), ("o" + OKINA, "ö"), ("G" + OKINA, "Ğ"), ("g" + OKINA, "ğ"),
    ("SH", "Ş"), ("Sh", "Ş"), ("sh", "ş"), ("CH", "Ç"), ("Ch", "Ç"), ("ch", "ç"),
]


def det(s: str) -> str:
    for a, b in LETTERS:
        s = s.replace(a, b)
    return s


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), file=sys.stderr)
    return subprocess.run(cmd, check=True, **kw)


# --------------------------------------------------------------------------- inputs

def fetch_upstream(dest: Path) -> Path:
    if not (dest / ".git").exists():
        run(["git", "clone", "--quiet", UPSTREAM_URL, str(dest)])
    run(["git", "-C", str(dest), "checkout", "--quiet", UPSTREAM_REV])
    return dest


def build_converter(bitg_src: str | None) -> Path:
    manifest = ROOT / "converter" / "Cargo.toml"
    cmd = ["cargo", "build", "--release", "--quiet", "--manifest-path", str(manifest)]
    if bitg_src:
        core = Path(bitg_src).resolve() / "crates" / "bitg-core"
        cmd += ["--config", f'patch."{BITG_URL}".bitg-core.path="{core.as_posix()}"']
    run(cmd)
    exe = ROOT / "converter" / "target" / "release" / ("bitg-hunspell-convert" + (".exe" if sys.platform == "win32" else ""))
    return exe


def convert_lines(exe: Path, lines: list[str], chunk: int = 100_000) -> list[str]:
    res: list[str] = []
    for i in range(0, len(lines), chunk):
        part = lines[i : i + chunk]
        data = ("\n".join(part) + "\n").encode("utf-8")
        p = subprocess.run([str(exe)], input=data, capture_output=True)
        out = p.stdout.decode("utf-8").split("\n")[: len(part)]
        if p.returncode != 0 or len(out) != len(part):
            raise SystemExit(f"converter failed (exit {p.returncode}, {len(out)}/{len(part)} lines): "
                             f"{p.stderr.decode('utf-8', 'replace')[-2000:]}")
        res += out
    return res


# --------------------------------------------------------------------------- .dic

CYRILLIC = re.compile("[\\u0400-\\u04ff]")


def convert_dic(exe: Path, text: str, report: dict) -> str:
    lines = [l for l in text.splitlines()[1:] if l.strip()]
    words, flags = [], []
    for l in lines:
        w, sep, f = l.partition("/")
        words.append(w)
        flags.append(sep + f)
    new = convert_lines(exe, words)
    out, seen = [], set()
    dropped, okina_fix, sh_kept = [], [], []
    for old, w, f in zip(words, new, flags):
        if CYRILLIC.search(old):
            dropped.append(old)  # Latin dictionary entries with stray Cyrillic letters (U+044B inside Latin words)
            continue
        if OKINA in w:
            okina_fix.append(f"{old} -> {det(w)}")  # bitg leaves all-caps abbreviations (OʻFA)
            w = det(w)
        if w != det(old):
            sh_kept.append(f"{old} -> {w}")  # bitg knows s|h words (Ishoq, mushaf, asʼhob)
        line = w + f
        if line in seen:
            continue
        seen.add(line)
        out.append(line)
    report.update(dic_in=len(lines), dic_out=len(out), dropped=dropped, okina_fix=okina_fix, bitg_vs_letters=sh_kept)
    return f"{len(out)}\n" + "\n".join(out) + "\n"


# --------------------------------------------------------------------------- .aff

def convert_condition(cond: str) -> str:
    """Hunspell condition: literal chars, '.', [set], [^set]. Inside a set an old letter is
    two characters (g + ʻ); it becomes the one new letter. A lone ʻ left in a set (it used to
    match both oʻ and gʻ endings) is expanded to ö ğ so the set keeps its old meaning."""
    out, i = [], 0
    while i < len(cond):
        if cond[i] == "[":
            j = cond.index("]", i)
            body = det(cond[i + 1 : j])
            neg = body.startswith("^")
            chars = body[1:] if neg else body
            if OKINA in chars:
                chars = chars.replace(OKINA, "") + "".join(c for c in "öğ" if c not in chars)
            out.append("[" + ("^" if neg else "") + chars + "]")
            i = j + 1
        else:
            j = cond.find("[", i)
            j = len(cond) if j < 0 else j
            out.append(det(cond[i:j]))
            i = j
    return "".join(out)


OLD_TO_NEW_REP = [
    # Old-alphabet input -> new letters (suggestions only; old spellings stay misspelled).
    *(f"{o}{m} {n}" for o, n in (("o", "ö"), ("O", "Ö"), ("g", "ğ"), ("G", "Ğ"))
      for m in (OKINA, "‘", "’", "'", "`", TUTUQ)),
    "sh ş", "Sh Ş", "SH Ş", "ch ç", "Ch Ç", "CH Ç",
    # New letters typed without diacritics.
    "o ö", "O Ö", "g ğ", "G Ğ", "s ş", "S Ş", "c ç", "C Ç",
]


def convert_aff(exe: Path, text: str, report: dict, upstream_rev: str, bitg_rev: str) -> str:
    lines = text.splitlines()
    # Check bitg and the letter map agree on every affix string before using the map.
    pieces = sorted({p for l in lines if l.startswith("SFX ") and len(l.split()) >= 5
                     for p in (l.split()[2], l.split()[3].split("/")[0]) if p != "0"})
    conv = convert_lines(exe, pieces)
    mismatch = [(p, c, det(p)) for p, c in zip(pieces, conv) if c != det(p)]
    if mismatch:
        raise SystemExit(f"bitg and letter map disagree on affixes: {mismatch[:20]}")
    report["affix_strings"] = len(pieces)

    out: list[str] = []
    rep: list[str] = []
    changed_conds = {}
    for l in lines:
        p = l.split()
        if not p:
            out.append(l)
            continue
        key = p[0]
        if key == "LANG":
            out.append(l)
            out.append("SET UTF-8")
            out.append("#")
            out.append(f"# {BASENAME}: Uzbek spelling dictionary, 2026 Latin alphabet (ö ğ ş ç ʼ)")
            out.append(f"# Generated by bitg-hunspell {VERSION} from uz-hunspell {upstream_rev}")
            out.append(f"#   ({UPSTREAM_URL}) converted with bitg {bitg_rev[:12]} ({BITG_URL}).")
            out.append("# Do not edit by hand: run build.py. License: GPL-3.0 (same as uz-hunspell).")
        elif key == "SET":
            continue
        elif key == "#" and l.startswith("# (c)"):
            out.append(l)  # original copyright lines, verbatim
        elif key == "#":
            out.append(l)
        elif key == "TRY":
            out.append("TRY -abcdefghijklmnopqrstuvwxyzöğşçABCDEFGHIJKLMNOPQRSTUVWXYZÖĞŞÇʼ")
        elif key == "KEY":
            out.append(det(l) + "|oö|gğ|sş|cç")
        elif key == "WORDCHARS":
            # ʻ ‘ ’ ' stay word characters so "oʻzbek" is checked as one (wrong) word, not "o" + "zbek".
            out.append(l)
            out.append("# Typing the tutuq as ' or ’ is accepted (maʼno = ma'no = ma’no).")
            out.append("ICONV 2")
            out.append("ICONV ' ʼ")
            out.append("ICONV ’ ʼ")
            # MAP (unlike REP) is applied to every combination of positions, so a word with several
            # old letters (gʻisht, toʻgʻri, oʻquvchi) still gets the new spelling as a suggestion.
            # (xy) is a multi-character MAP element.
            marks = (OKINA, "‘", "’", "`", TUTUQ)
            maps = [
                "ö" + "".join(f"(o{m})" for m in marks) + "o",
                "Ö" + "".join(f"(O{m})" for m in marks) + "O",
                "ğ" + "".join(f"(g{m})" for m in marks) + "g",
                "Ğ" + "".join(f"(G{m})" for m in marks) + "G",
                "ş(sh)s", "Ş(Sh)(SH)S", "ç(ch)c", "Ç(Ch)(CH)C",
            ]
            out.append(f"MAP {len(maps)}")
            out.extend(f"MAP {m}" for m in maps)
        elif key == "REP" and len(p) == 2:
            continue  # count rewritten below
        elif key == "REP":
            rep.append(f"{det(p[1])} {det(p[2])}")
        elif key == "SFX" and len(p) >= 5:
            strip = det(p[2])
            add, sep, cont = p[3].partition("/")
            cond = convert_condition(p[4])
            if cond != det(p[4]):
                changed_conds[p[4]] = cond
            out.append(" ".join(["SFX", p[1], strip, det(add) + sep + cont, cond, *p[5:]]))
        else:
            out.append(l)
    # REP block: upstream entries (converted) + old-alphabet entries, de-duplicated, in order.
    seen, reps = set(), []
    for r in rep + OLD_TO_NEW_REP:
        a, b = r.split(" ")
        if a == b or r in seen:
            continue
        seen.add(r)
        reps.append(r)
    idx = next(i for i, l in enumerate(out) if l.startswith("NOSPLITSUGS")) + 1
    out[idx:idx] = [f"REP {len(reps)}"] + [f"REP {r}" for r in reps]
    report["rep_entries"] = len(reps)
    report["conditions_expanded"] = changed_conds
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- packaging

def write_zip(path: Path, files: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])


def fill(template: Path) -> bytes:
    t = template.read_text(encoding="utf-8")
    for k, v in {"@VERSION@": VERSION, "@BASENAME@": BASENAME, "@FIREFOX_LANG@": FIREFOX_LANG,
                 "@FIREFOX_ID@": FIREFOX_ID, "@LO_LOCALE@": LIBREOFFICE_LOCALE}.items():
        t = t.replace(k, v)
    return t.encode("utf-8")


def package(dic: bytes, aff: bytes) -> list[Path]:
    lic = (ROOT / "LICENSE").read_bytes()
    pk = ROOT / "packaging"
    ff = {
        "manifest.json": fill(pk / "firefox" / "manifest.json"),
        f"dictionaries/{BASENAME}.dic": dic,
        f"dictionaries/{BASENAME}.aff": aff,
        "LICENSE": lic,
    }
    json.loads(ff["manifest.json"])  # must be valid JSON
    lo = {
        "description.xml": fill(pk / "libreoffice" / "description.xml"),
        "META-INF/manifest.xml": fill(pk / "libreoffice" / "META-INF" / "manifest.xml"),
        "dictionaries.xcu": fill(pk / "libreoffice" / "dictionaries.xcu"),
        "description-en.txt": fill(pk / "libreoffice" / "description-en.txt"),
        "description-uz.txt": fill(pk / "libreoffice" / "description-uz.txt"),
        f"dictionaries/{BASENAME}.dic": dic,
        f"dictionaries/{BASENAME}.aff": aff,
        "LICENSE": lic,
    }
    xpi = ROOT / "dist" / f"bitg-hunspell-{VERSION}-firefox.xpi"
    oxt = ROOT / "dist" / f"bitg-hunspell-{VERSION}-libreoffice.oxt"
    write_zip(xpi, ff)
    write_zip(oxt, lo)
    return [xpi, oxt]


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", help="existing uz-hunspell checkout (default: clone into .cache/)")
    ap.add_argument("--bitg-src", help="local bitg checkout instead of the pinned git revision")
    ap.add_argument("--no-package", action="store_true")
    a = ap.parse_args()

    up = Path(a.upstream) if a.upstream else fetch_upstream(ROOT / ".cache" / "uz-hunspell")
    upstream_rev = subprocess.run(["git", "-C", str(up), "rev-parse", "HEAD"], capture_output=True,
                                  text=True, check=True).stdout.strip()
    if upstream_rev != UPSTREAM_REV:
        print(f"warning: upstream is at {upstream_rev}, pinned {UPSTREAM_REV}", file=sys.stderr)
    lock = (ROOT / "converter" / "Cargo.toml").read_text(encoding="utf-8")
    bitg_rev = re.search(r'rev = "([0-9a-f]+)"', lock).group(1)

    exe = build_converter(a.bitg_src)
    report: dict = {"upstream": upstream_rev, "bitg": bitg_rev}
    dic = convert_dic(exe, (up / "uz_UZ.dic").read_text(encoding="utf-8"), report)
    aff = convert_aff(exe, (up / "uz_UZ.aff").read_text(encoding="utf-8"), report, upstream_rev[:12], bitg_rev)
    leftover = [c for c in (OKINA, "‘") if c in dic]
    if leftover:
        raise SystemExit(f"old-alphabet characters left in .dic: {leftover}")
    (ROOT / f"{BASENAME}.dic").write_bytes(dic.encode("utf-8"))
    (ROOT / f"{BASENAME}.aff").write_bytes(aff.encode("utf-8"))
    (ROOT / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: (v if not isinstance(v, (list, dict)) else len(v)) for k, v in report.items()}, ensure_ascii=False))
    if not a.no_package:
        for p in package(dic.encode("utf-8"), aff.encode("utf-8")):
            print(p.relative_to(ROOT).as_posix(), p.stat().st_size)


if __name__ == "__main__":
    main()
