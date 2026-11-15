"""Release: build, gate everything, make the BPS patch, re-apply and verify it, zip patch + README.

    python -X utf8 tools/release.py [--version 1.0] [--force] [--skip-build]

Stops at the first failure, in this order: build -> tools/check.py (tests + lint) -> smoke boot -> jp_left.py
(full ROM, --gba-ptrs, known non-text runs in docs/jp_known.txt) -> qa_gate.py check on every work/qa/**/manifest.tsv
(visual tour and story pass; verdicts in the manifest's sibling `verdicts/`) -> textcover.py work/qa/cover -> no
unticked line in docs/polish.md -> no template placeholder in README.md -> debug tool off -> patch -> re-apply to a
clean original and compare -> zip. Output: release/Fantastic_Children_EN_v<version>.zip (patch + README.txt);
refuses to overwrite an existing version without --force. Never publishes anything.
"""
import argparse
import hashlib
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / "rom/Fantastic Children (Japan).gba"
BUILT = ROOT / "build/fantastic_children_en.gba"
REL = ROOT / "release"
PY = [sys.executable, "-X", "utf8"]


def skill():
    out = subprocess.run([sys.executable, str(ROOT / "tools/skill.py")], capture_output=True, text=True).stdout
    return Path(out.strip()) / "scripts"


def step(name, cmd):
    print(f"== {name}: {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT)
    if r.returncode:
        sys.exit(f"release stopped: {name} failed (exit {r.returncode})")


def hashes(data):
    return {"size": len(data), "crc32": f"{zlib.crc32(data):08X}", "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest()}


def gates(s):
    manifests = sorted((ROOT / "work/qa").rglob("manifest.tsv"))
    if not manifests:
        sys.exit("release stopped: no work/qa/**/manifest.tsv")
    for m in manifests:
        args = [m, m.parent / "verdicts"]
        if (m.parent / "manifest.tsv.build").exists() or m == ROOT / "work/qa/manifest.tsv":
            args += ["--build", BUILT]
        step(f"qa_gate {m.relative_to(ROOT)}", PY + [s / "qa_gate.py", "check", *args])


def polish():
    open_ = [ln for ln in (ROOT / "docs/polish.md").read_text(encoding="utf-8").splitlines()
             if ln.startswith("- [ ]")]
    if open_:
        sys.exit("release stopped: docs/polish.md has unticked lines:\n" + "\n".join(open_))
    print("== polish: every line ticked")


def readme():
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    left = re.findall(r"<(?:Game title|platform|publisher|year|repo|file|size|sha1|game|ext)[^>]*>", t)
    if left:
        sys.exit(f"release stopped: README.md still has template placeholders: {sorted(set(left))}")
    print("== README: no placeholders")


def debug_off():
    """The debug tool is tools/debug/warp.lua, run by the emulator; nothing of it is in the ROM. The release build
    must be the plain build: no marker text (`[id]` pages) and no --qa override."""
    strings = (ROOT / "build/strings.tsv").read_text(encoding="utf-8")
    if (ROOT / "build/qa.gba").exists() and (ROOT / "build/qa.gba").stat().st_mtime > BUILT.stat().st_mtime:
        print("   note: build/qa.gba is newer than the release build (not used)")
    sys.path.insert(0, str(ROOT / "tools"))
    from script_tsv import load
    marker = [r["id"] for r in load().values() if re.match(r"^\[[0-9A-Fa-fpsm]", r["en"])]
    if marker or not strings.strip():
        sys.exit(f"release stopped: debug/marker text in the build source: {marker[:5]}")
    print("== debug tool off: warp is an external Lua script; plain build, no marker rows")


README_TXT = """Fantastic Children (GBA) - English translation patch v{ver}
=============================================================

Unofficial English fan translation of Fantastic Children (Game Boy Advance, Bandai, 2005).
No ROM is included and none will be provided: patch your own dump.

How to patch
------------
1. Get a clean dump of the Japanese game:
     No-Intro: Fantastic Children (Japan)
     File size: {o[size]} bytes
     CRC32:  {o[crc32]}
     MD5:    {o[md5]}
     SHA-1:  {o[sha1]}
2. Apply {patch} with any BPS patcher (Floating IPS / flips, Rom Patcher JS at
   https://www.marcrobledo.com/RomPatcher.js/, beat).
3. The patched ROM should have:
     CRC32:  {n[crc32]}
     SHA-1:  {n[sha1]}

Start from a cold boot (no savestates from the Japanese version). Battery saves from the Japanese game work.
Tested in Mesen 2.2.1 (GBA core) with the official BIOS.

Translation status
------------------
Dialogue and story ........ translated
Menus, items, battle text . translated
Title logo, boot logo ..... redrawn in English
Staff roll ................ redrawn in English (staff-name readings are best guesses from kanji)
Name entry ................ none in this game

Known issues: none known. Please report bugs at
https://github.com/minhnhattonthat/fantastic-children-en/issues (a savestate helps).

Credits
-------
Translation, hacking and tools: minhnhattonthat, with extensive AI assistance (Claude by Anthropic; review
passes by OpenAI Codex). Corrections are very welcome.
Fonts (rendered into the patch, SIL Open Font License 1.1): Lato by Lukasz Dziedzic (dialogue font, boot logo),
Bebas Neue by Dharma Type (title logo), Oswald by Vernon Adams (staff roll).

Fantastic Children is (c) Nippon Animation / Bandai. This is an unofficial fan project, not affiliated with them.
Do not distribute patched ROMs.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    ap.add_argument("--skip-build", action="store_true", help="use the current build/ output (tests still run)")
    a = ap.parse_args()
    name = f"Fantastic_Children_EN_v{a.version}"
    patch, zpath = REL / f"{name}.bps", REL / f"{name}.zip"
    if (patch.exists() or zpath.exists()) and not a.force:
        sys.exit(f"{patch.name} / {zpath.name} already exist; pass --force to overwrite")
    s = skill()
    if not a.skip_build:
        step("build", PY + [ROOT / "build.py"])
    step("tests + lint", PY + [ROOT / "tools/check.py"])
    step("smoke", PY + [s / "emu.py", BUILT, "--out", ROOT / "work/qa/release_smoke", "--route",
                        ROOT / "tools/routes/boot.txt", "--smoke"])
    step("jp_left", PY + [s / "jp_left.py", BUILT, "--tbl", ROOT / "tbl/jp.tbl", "--le16", "--gba-ptrs",
                          "--known", ROOT / "docs/jp_known.txt"])
    gates(s)
    step("textcover", PY + [s / "textcover.py", ROOT / "work/qa/cover", ROOT / "build/strings.tsv"])
    polish()
    readme()
    debug_off()
    REL.mkdir(exist_ok=True)
    step("patch", PY + [s / "bps.py", "make", ORIG, BUILT, patch])
    check = REL / f"{name}.check.gba"
    step("re-apply", PY + [s / "bps.py", "apply", ORIG, patch, check])
    orig, built = ORIG.read_bytes(), BUILT.read_bytes()
    if check.read_bytes() != built:
        sys.exit("release stopped: re-applied patch differs from the build")
    check.unlink()
    o, n = hashes(orig), hashes(built)
    readme_txt = README_TXT.format(ver=a.version, o=o, n=n, patch=patch.name)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(patch, patch.name)
        z.writestr("README.txt", readme_txt.replace("\n", "\r\n"))
    print(f"== done: {zpath.relative_to(ROOT)} ({zpath.stat().st_size} bytes): {patch.name} "
          f"({patch.stat().st_size} bytes) + README.txt; patched CRC32 {n['crc32']} SHA-1 {n['sha1']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
