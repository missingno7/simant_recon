"""Run a pinned historical compiler/assembler under MS-DOS Player.

Profiles live in layout/toolchain.json.  Every run re-verifies the SHA-256 of the
runner and of each pinned tool file, stages the source as ``UNIT.C`` (CRLF,
ASCII) in a fresh directory under build/scratch/cc/, and returns the object bytes.

The physical tool directory is part of the profile: MSC passes receive their
own directory in the environment block and near-heap pressure can make code
generation depend on its length (observed in stunts_recon).  Never move a
profile directory without re-running the toolchain probes.

Include policy: ``#include "x.h"`` resolves only to tracked ``include/`` files
and ``<x.h>`` only to the profile's INCLUDE directory; both are inlined here
before CL runs so the compiler never searches the host.  Every file reached must be
pinned in the profile's ``include_files`` ({key: sha256}; key = the path relative to
the INCLUDE directory, lower case with ``/``, or ``repo:include/<name>`` for a tracked
header), and names with ``..``, a drive or a leading slash are refused.

DOSBox-X profiles mount a scratch copy that holds only the profile's pinned files
(build/deps/dos-tools/), never the whole tool directory.
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
WORK = ROOT / "build" / "scratch" / "cc"


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
    inc = include_root(prof)
    for key, sha in (prof.get("include_files") or {}).items():
        path = ROOT / key[5:] if key.startswith("repo:") else (inc / key if inc else None)
        if path is None or not path.is_file() or _sha(path) != sha:
            raise CompileError(f"{name}: pinned include {key} missing or changed")
    _verified.add(name)
    return prof


def include_root(prof: dict) -> Path | None:
    if prof.get("include_directory"):
        return Path(prof["include_directory"])
    if prof.get("include"):
        return Path(prof["directory"]) / prof["include"]
    return None


def _include_name_ok(name: str) -> bool:
    parts = name.replace("\\", "/").split("/")
    return (bool(name) and ":" not in name and not name.startswith(("/", "\\"))
            and ".." not in parts and all(parts))


INCLUDE_RE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]', re.M)


def expand_includes(text: str, prof: dict, seen: set | None = None) -> str:
    seen = set() if seen is None else seen
    pins = prof.get("include_files") or {}

    def repl(m):
        kind, name = m.group(1), m.group(2).strip()
        if not _include_name_ok(name):
            raise CompileError(f"include name refused (path traversal/absolute): {name}")
        rel = name.replace("\\", "/")
        if kind == '"':
            path = ROOT / "include" / rel
            pin = "repo:include/" + rel
        else:
            path = (include_root(prof) or Path(prof["directory"]) / "INCLUDE") / rel
            pin = rel.lower()
        if not path.exists():
            raise CompileError(f"include not found under policy: {name}")
        body = path.read_bytes()
        if pins.get(pin) != hashlib.sha256(body).hexdigest():
            raise CompileError(f"include {name} is not pinned in the profile's include_files (key {pin!r})")
        key = str(path).lower()
        if key in seen:
            return ""
        seen.add(key)
        return expand_includes(body.decode("latin1"), prof, seen)

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
    check_flags(flags)
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


def check_flags(flags: list[str]) -> None:
    """Refuse host-mangled options: Git Bash turns '/AL' into 'C:/Program Files/Git/AL', and CL
    then silently compiles near-model code (worker ovlB).  Every option must be a DOS switch;
    the only non-switch operands allowed are pass names after /B1 /B2 /B3."""
    prev = ""
    for f in flags:
        if ":" in f or any(c.isspace() for c in f) or "\\" in f or (not f.startswith("/") and prev not in ("/B1", "/B2", "/B3")):
            raise CompileError(f"suspicious compiler option {f!r} (MSYS path conversion? set MSYS_NO_PATHCONV=1)")
        prev = f


_pinned_ok: set[str] = set()


def pinned_tree(prof: dict) -> Path:
    """A scratch directory holding exactly the profile's pinned files (same relative paths),
    hash-checked once per process; DOSBox mounts it instead of the whole tool directory, so
    the compiler can only reach pinned files (DOS paths are unchanged: D:\BIN\...)."""
    import hashlib as _h
    files = prof["files"]
    tag = _h.sha256(json.dumps(sorted(files.items())).encode()).hexdigest()[:16]
    dest = ROOT / "build" / "deps" / "dos-tools" / tag
    if str(dest) in _pinned_ok:
        return dest
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="tmp", dir=dest.parent))
        for rel in files:
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(prof["directory"]) / rel, tmp / rel)
        try:
            os.rename(tmp, dest)
        except OSError:                      # another process created it first
            shutil.rmtree(tmp, ignore_errors=True)
    present = {p.relative_to(dest).as_posix().lower() for p in dest.rglob("*") if p.is_file()}
    if present != {r.lower() for r in files}:
        raise CompileError(f"pinned tree {dest} holds unpinned or lacks pinned files")
    for rel, sha in files.items():
        if _sha(dest / rel) != sha:
            raise CompileError(f"pinned tree {dest}: hash mismatch for {rel}")
    _pinned_ok.add(str(dest))
    return dest


def _compile_dosbox(prof: dict, runner: dict, work: Path, basename: str, flags: list[str],
                    keep: bool, timeout: int) -> Result:
    """Run CL inside a headless DOSBox-X: the pinned files of the tool tree (pinned_tree) are
    mounted read-only as D:, the work directory as E:.  The passes therefore always see the same DOS paths."""
    bs = "\\"  # DOS path separator
    bat = ["@echo off", f"{prof['executable']} /c {' '.join(flags)} {basename}.C > CL.LOG", "exit"]
    (work / "RUN.BAT").write_bytes(("\r\n".join(bat) + "\r\n").encode("ascii"))
    conf = []
    for sec, kv in runner["conf"].items():
        conf.append(f"[{sec}]")
        conf += [f"{k}={v}" for k, v in kv.items()]
    conf += ["[autoexec]", f'mount d "{pinned_tree(prof)}" -ro', f'mount e "{work.resolve()}"', "e:",
             f"set PATH=D:{bs}{prof.get('bin', '.')}", f"set TMP=E:{bs}", f"set TEMP=E:{bs}", "call RUN.BAT", "exit"]
    (work / "dosbox.conf").write_text("\n".join(conf) + "\n")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    argv = [runner["path"], "-conf", str(work / "dosbox.conf"), "-fastlaunch", "-exit", "-nomenu"]
    logp = work / "CL.LOG"
    for attempt in range(3):
        r = subprocess.run(argv, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=max(timeout, 180), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        # DOSBox-X occasionally fails to run the batch under heavy parallel load: no CL.LOG at all.
        # Retry only then; a compiler diagnostic (CL.LOG present) is a real result.
        if logp.exists():
            break
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
