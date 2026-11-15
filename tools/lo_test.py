#!/usr/bin/env python3
"""Spell-check the .oxt inside a real LibreOffice, the way Writer does it.

Installs the extension into a throw-away user profile, then asks LibreOffice's spell-check
dispatcher about every word in tests/words.tsv. Words are looked up by LanguageType 0x0443
(Uzbek Latin), which is what Writer passes for text marked "Uzbek Latin". A dictionary
registered under a tag LibreOffice does not map to that language is never consulted, and every
word then counts as correct, so the old spellings in words.tsv would pass. This test fails in
that case.

Run it with a Python that has the uno module:
    Windows:  "<LibreOffice>/program/python.exe" tools/lo_test.py --soffice "<LibreOffice>/program/soffice.exe" --oxt dist/....oxt
    Linux:    python3 tools/lo_test.py --soffice /usr/bin/soffice --oxt dist/....oxt   (python3-uno)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import uno

ROOT = Path(__file__).resolve().parent.parent
LANGUAGE_UZBEK_LATIN = 0x0443


def unopkg_for(soffice: Path) -> Path:
    for name in ("unopkg.com", "unopkg.exe", "unopkg"):
        p = soffice.parent / name
        if p.exists():
            return p
    found = shutil.which("unopkg")
    if found:
        return Path(found)
    raise SystemExit(f"unopkg not found next to {soffice}")


def connect(soffice: Path, profile_url: str, pipe: str):
    proc = subprocess.Popen([
        str(soffice), "--headless", "--invisible", "--nologo", "--norestore", "--nodefault",
        f"-env:UserInstallation={profile_url}",
        f"--accept=pipe,name={pipe};urp;StarOffice.ComponentContext",
    ])
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
    for _ in range(240):
        try:
            return proc, resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
        except Exception:
            if proc.poll() is not None:
                break
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("LibreOffice did not start")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--soffice", required=True, type=Path)
    ap.add_argument("--oxt", required=True, type=Path)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    rows = [l.split("\t") for l in (ROOT / "tests" / "words.tsv").read_text(encoding="utf-8").splitlines()
            if l and not l.startswith("#")]
    good = [r[1] for r in rows if r[0] == "ok"]
    bad = [(r[1], r[2]) for r in rows if r[0] == "old"]

    tmp = Path(tempfile.mkdtemp(prefix="bitg-lo-"))
    profile_url = tmp.as_uri()
    failures: list[str] = []
    try:
        subprocess.run([str(unopkg_for(args.soffice)), "add", "--suppress-license",
                        f"-env:UserInstallation={profile_url}", str(args.oxt.resolve())], check=True)
        proc, ctx = connect(args.soffice, profile_url, f"bitglotest{int(time.time())}")
        smgr = ctx.ServiceManager
        try:
            lsm = smgr.createInstanceWithContext("com.sun.star.linguistic2.LinguServiceManager", ctx)
            disp = lsm.getSpellChecker()

            uz = [l for l in disp.getLocales() if "uz" in (l.Language, l.Variant.split("-")[0])]
            print("dispatcher Uzbek locales:", [f"{l.Language}|{l.Country}|{l.Variant}" for l in uz])

            # Writer's path: XSpellChecker1 with a LanguageType.
            g_ok = [w for w in good if disp.isValid(w, LANGUAGE_UZBEK_LATIN, ())]
            b_rej, b_top = [], []
            for old, new in bad:
                if not disp.isValid(old, LANGUAGE_UZBEK_LATIN, ()):
                    b_rej.append(old)
                    alt = disp.spell(old, LANGUAGE_UZBEK_LATIN, ())
                    if alt is not None and list(alt.getAlternatives())[:1] == [new]:
                        b_top.append(old)
            print(f"[Writer path, LanguageType 0x0443] new-alphabet accepted: {len(g_ok)}/{len(good)}")
            print(f"[Writer path, LanguageType 0x0443] old spellings rejected: {len(b_rej)}/{len(bad)}; "
                  f"correct word first: {len(b_top)}/{len(bad)}")
            failures += [f"not accepted: {w}" for w in good if w not in g_ok]
            failures += [f"not rejected: {o}" for o, _ in bad if o not in b_rej]
            failures += [f"wrong first suggestion: {o} (want {n})" for o, n in bad if o in b_rej and o not in b_top]
        finally:
            try:
                smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx).terminate()
            except Exception:
                pass
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for f in failures[:40]:
        print("FAIL", f)
    print("OK" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
