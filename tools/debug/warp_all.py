"""warp_all.py: run every scene of tools/debug/scenes.gba.txt from a cold boot and check each one arrived.

    python -X utf8 tools/debug/warp_all.py [--rom build/x.gba] [--only REGEX] [--jobs 3] [--out work/qa/warps]
                                           [--states]   # also save work/states/<scene>.mss on arrival
                                           [--resume]   # skip scenes already ok in OUT (resume a killed run)
                                           [--check-only]  # grade OUT as it stands, run nothing

A scene passes when its log has `WARP <scene>`, its shot warp.png is not one flat colour, and, for event scenes
with `msg=N`, the game fetched message N after arrival. Writes OUT/report.tsv and OUT/sheet*.png (all shots,
labelled by scene in OUT/sheet_index.txt). Exit 1 if any scene failed.
"""
import argparse
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS  # noqa: E402

sys.path.insert(0, SCRIPTS)
import sheet  # noqa: E402

ROM = ROOT / "rom" / "Fantastic Children (Japan).gba"
SCENES = ROOT / "tools" / "debug" / "scenes.gba.txt"


def load_scenes():
    out = []
    for line in SCENES.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            name, *kv = line.split()
            out.append((name, dict(x.split("=", 1) for x in kv)))
    return out


def run(rom, out, name, kv, states, resume=False):
    d = out / name
    if resume and (d / "log.txt").exists():
        prev = check(d, name, kv, subprocess.CompletedProcess([], -1))
        if prev[1] == "ok" and (not states or (ROOT / "work" / "states" / f"{name}.mss").exists()):
            return prev
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    # Mesen keeps one battery file per ROM *name* (tools/mesen/Saves/<name>.sav): a uniquely named copy per run
    # keeps parallel runs (and a scene that saves in game) from sharing it
    own = d / f"warp_{name}.gba"
    shutil.copy(rom, own)
    wait = int(kv.get("wait", "360"))
    frames = 2600 + wait + 600  # a cap: warp.lua stops the run after its shot
    try:
        return check(d, name, kv, subprocess.run(
            emu_cmd(own, d, name, kv, frames, out, states), capture_output=True, text=True))
    finally:
        own.unlink()


def emu_cmd(rom, d, name, kv, frames, out, states):
    cmd = [sys.executable, "-X", "utf8", str(Path(SCRIPTS) / "emu.py"), str(rom), "--out", str(d),
           "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", f"SCENE='{name}'", "--var", "STOP_AFTER_SHOT=1",
           "--frames", str(frames), "--timeout", "240"]
    # own blank EEPROM per run: without --sav every Mesen shares tools/mesen/Saves/, and a scene that saves
    # (save_prompt + mash) turns NEW GAME into a loaded game for the runs after it
    blank = out / "_blank.sav"
    cmd += ["--sav", str(blank)]
    if "keys" not in kv and "boot" not in kv:
        cmd += ["--mash", "40"]
    if states:
        st = (ROOT / "work" / "states" / f"{name}.mss").as_posix()
        cmd += ["--var", f"STATE_OUT=[[{st}]]"]
    return cmd


def check(d, name, kv, p):
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
    m = re.search(r"^f(\d+) WARP ", log, re.M)
    if not m:
        err = (d / "lua_error.txt").read_text(errors="replace").strip() if (d / "lua_error.txt").exists() else ""
        return name, "FAIL", f"no arrival (exit {p.returncode}) {err}"[:200]
    shot = d / "warp.png"
    if not shot.exists():
        return name, "FAIL", "no shot"
    if kv.get("blank") != "1" and sheet.is_blank(sheet.read_png(shot)):  # blank=1: black by design
        return name, "FAIL", "blank shot"
    if "msg" in kv:
        t = int(m.group(1))
        ids = [int(i) for f, i in re.findall(r"^f(\d+) MSG (\d+)", log, re.M) if int(f) >= t - 30]
        want = {int(i) for i in kv["msg"].split(",")}
        if not want & set(ids):
            return name, "FAIL", f"msg {kv['msg'][:40]} not fetched (got {ids[:8]})"
    return name, "ok", m.group(0).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", type=Path, default=ROM)
    ap.add_argument("--only")
    ap.add_argument("--jobs", type=int, default=3)  # each Mesen holds ~590 MB; 8 ran the machine out of memory
    ap.add_argument("--out", type=Path, default=ROOT / "work" / "qa" / "warps")
    ap.add_argument("--states", action="store_true")
    # keep scenes whose earlier run in OUT already passes (a killed run resumes where it stopped)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--check-only", action="store_true", help="grade existing OUT dirs, run nothing")
    a = ap.parse_args()
    scenes = [(n, kv) for n, kv in load_scenes() if not a.only or re.search(a.only, n)]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "_blank.sav").write_bytes(b"\xff" * 8192)
    if a.check_only:
        res = [check(a.out / n, n, kv, subprocess.CompletedProcess([], -1)) if (a.out / n / "log.txt").exists()
               else (n, "FAIL", "not run") for n, kv in scenes]
    else:
        with ThreadPoolExecutor(a.jobs) as ex:
            res = list(ex.map(lambda s: run(a.rom, a.out, s[0], s[1], a.states, a.resume), scenes))
    rows = ["scene\tresult\tdetail"] + [f"{n}\t{r}\t{d}" for n, r, d in res]
    (a.out / "report.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    shots = [a.out / n / "warp.png" for n, r, _ in res if (a.out / n / "warp.png").exists()]
    names = [p.parent.name for p in shots]
    for k in range(0, len(shots), 30):
        page = shots[k:k + 30]
        sheet.sheet([sheet.read_png(p) for p in page], 6, a.out / f"sheet_{k // 30 + 1:02d}.png", div=2)
    (a.out / "sheet_index.txt").write_text(
        "\n".join(f"sheet_{k // 30 + 1:02d}.png: " + " ".join(names[k:k + 30]) for k in range(0, len(names), 30))
        + "\n", encoding="utf-8")
    bad = [r for r in res if r[1] != "ok"]
    print(f"{len(res) - len(bad)}/{len(res)} scenes ok; report {a.out / 'report.tsv'}")
    for n, _, d in bad:
        print(f"FAIL {n}: {d}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
