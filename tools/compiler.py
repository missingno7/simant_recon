"""Run a pinned historical compiler/assembler under MS-DOS Player.

Profiles live in layout/toolchain.json.  Every run re-verifies the SHA-256 of the
runner and of each pinned tool file, stages the source as ``UNIT.C`` (CRLF,
ASCII) in a fresh directory under build/cc/, and returns the object bytes.

The physical tool directory is part of the profile: MSC passes receive their
own directory in the environment block and near-heap pressure can make code
generation depend on its length (observed in stunts_recon).  Never move a
profile directory without re-running the toolchain probes.

Include policy: ``#include "x.h"`` resolves only to tracked ``include/`` files
and ``<x.h>`` only to the profile's INCLUDE directory; both are inlined here
before CL runs so the compiler never searches the host.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN = ROOT / "layout" / "toolchain.json"
WORK = ROOT / "build" / "cc"


class CompileError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def toolchain() -> dict:
    return json.loads(TOOLCHAIN.read_text())


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_verified: set[str] = set()


def verify_profile(name: str) -> dict:
    tc = toolchain()
    prof = tc["profiles"][name]
    if name in _verified:
        return prof
    runner = tc["runners"][prof["runner"]] if prof.get("runner") else tc["runner"]
    if _sha(Path(runner["path"])) != runner["sha256"]:
        raise CompileError("runner hash mismatch")
    d = Path(prof["directory"])
    for rel, sha in prof["files"].items():
        if _sha(d / rel) != sha:
            raise CompileError(f"{name}: hash mismatch for {d / rel}")
    _verified.add(name)
    return prof


INCLUDE_RE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]', re.M)


def expand_includes(text: str, prof: dict, seen: set | None = None) -> str:
    seen = set() if seen is None else seen

    def repl(m):
        kind, name = m.group(1), m.group(2)
        if kind == '"':
            path = ROOT / "include" / name
        else:
            path = Path(prof.get("include_directory") or Path(prof["directory"]) / prof.get("include", "INCLUDE")) / name
        if not path.exists():
            raise CompileError(f"include not found under policy: {name}")
        key = str(path).lower()
        if key in seen:
            return ""
        seen.add(key)
        return expand_includes(path.read_text(encoding="latin1"), prof, seen)

    return INCLUDE_RE.sub(repl, text)


@dataclass
class Result:
    ok: bool
    obj: bytes | None
    log: str
    workdir: Path
    argv: list


def compile_c(source: str, profile: str, flags: list[str] | None = None,
              basename: str = "UNIT", keep: bool = False, timeout: int = 90) -> Result:
    prof = verify_profile(profile)
    tc = toolchain()
    WORK.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="c", dir=WORK))
    text = expand_includes(source, prof)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    try:
        staged = text.replace("\n", "\r\n").encode("ascii")
    except UnicodeEncodeError as e:
        raise CompileError(f"non-ASCII source: {e}")
    src = work / f"{basename}.C"
    src.write_bytes(staged)
    flags = [*(flags if flags is not None else prof["flags"]), *prof.get("required_flags", [])]
    if prof.get("runner") == "dosbox-x":
        return _compile_dosbox(prof, tc["runners"]["dosbox-x"], work, basename, flags, keep, timeout)
    bindir = Path(prof["directory"]) / prof.get("bin", ".")
    argv = [tc["runner"]["path"], *tc["runner"]["options"], str(bindir / prof["executable"]), "/c",
            *flags, src.name]
    env = {"PATH": str(bindir), "MSDOS_PATH": str(bindir), "TEMP": ".", "TMP": ".", "MSDOS_TEMP": ".",
           "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows")}
    r = subprocess.run(argv, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log = r.stdout.decode("latin1", "replace")
    objp = work / f"{basename}.OBJ"
    obj = objp.read_bytes() if objp.exists() else None
    (work / "compiler.log").write_text(log)
    res = Result(r.returncode == 0 and obj is not None, obj, log, work, argv)
    if not keep and res.ok:
        shutil.rmtree(work, ignore_errors=True)
    return res


def _compile_dosbox(prof: dict, runner: dict, work: Path, basename: str, flags: list[str],
                    keep: bool, timeout: int) -> Result:
    """Run CL inside a headless DOSBox-X: the tool tree is mounted read-only as D:, the
    work directory as E:.  The passes therefore always see the same DOS paths."""
    bs = "\\"  # DOS path separator
    bat = ["@echo off", f"{prof['executable']} /c {' '.join(flags)} {basename}.C > CL.LOG", "exit"]
    (work / "RUN.BAT").write_bytes(("\r\n".join(bat) + "\r\n").encode("ascii"))
    conf = []
    for sec, kv in runner["conf"].items():
        conf.append(f"[{sec}]")
        conf += [f"{k}={v}" for k, v in kv.items()]
    conf += ["[autoexec]", f'mount d "{prof["directory"]}" -ro', f'mount e "{work.resolve()}"', "e:",
             f"set PATH=D:{bs}{prof.get('bin', '.')}", f"set TMP=E:{bs}", f"set TEMP=E:{bs}", "call RUN.BAT", "exit"]
    (work / "dosbox.conf").write_text("\n".join(conf) + "\n")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    argv = [runner["path"], "-conf", str(work / "dosbox.conf"), "-fastlaunch", "-exit", "-nomenu"]
    r = subprocess.run(argv, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=max(timeout, 180), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    logp = work / "CL.LOG"
    log = logp.read_text(encoding="latin1", errors="replace") if logp.exists() else r.stdout.decode("latin1", "replace")
    objp = work / f"{basename}.OBJ"
    obj = objp.read_bytes() if objp.exists() else None
    (work / "compiler.log").write_text(log)
    res = Result(r.returncode == 0 and obj is not None, obj, log, work, argv)
    if not keep and res.ok:
        shutil.rmtree(work, ignore_errors=True)
    return res


def assemble(source: str, profile: str, flags: list[str] | None = None, basename: str = "UNIT",
             keep: bool = False, timeout: int = 90) -> Result:
    prof = verify_profile(profile)
    tc = toolchain()
    WORK.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="a", dir=WORK))
    src = work / f"{basename}.ASM"
    src.write_bytes(source.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    bindir = Path(prof["directory"]) / prof.get("bin", ".")
    argv = [tc["runner"]["path"], *tc["runner"]["options"], str(bindir / prof["executable"]),
            *(flags if flags is not None else prof["flags"]), f"{src.name};"]
    env = {"PATH": str(bindir), "TEMP": ".", "TMP": ".", "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows")}
    r = subprocess.run(argv, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log = r.stdout.decode("latin1", "replace")
    objp = work / f"{basename}.OBJ"
    obj = objp.read_bytes() if objp.exists() else None
    res = Result(r.returncode == 0 and obj is not None, obj, log, work, argv)
    if not keep and res.ok:
        shutil.rmtree(work, ignore_errors=True)
    return res
