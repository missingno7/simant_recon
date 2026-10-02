"""Capture post-C2 files by replacing only C3 with a DOS file-copy hook.

Run from the repository root:
    python work/takeover/compiler-ir/c2/capture_b3.py

Sources and this script are preserved beside the research notes. Raw captures
and DOSBox setup files stay under ignored build/workers scratch. The pinned
MSC and MASM binaries are mounted read-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TC = json.loads((ROOT / "layout" / "toolchain.json").read_text())
MSC = TC["profiles"]["msc600ax"]
MASM = TC["profiles"]["masm510"]
RUNNER = TC["runners"][MSC["runner"]]
OUT = ROOT / "build" / "workers" / "c2_observability" / "b3"

CASES = {}
FILE_CASES = {
    "toy-far-pointer": ROOT / "work" / "takeover" / "compiler-ir" / "c2" / "sources" / "far-pointer.c",
    "toy-far-pointer-renamed": ROOT / "work" / "takeover" / "compiler-ir" / "c2" / "sources" / "far-pointer-renamed.c",
    "toy-long-home": ROOT / "work" / "takeover" / "compiler-ir" / "c2" / "sources" / "long-home.c",
    "toy-word-home": ROOT / "work" / "takeover" / "compiler-ir" / "c2" / "sources" / "word-home.c",
}

HOOK = r"""; Research-only hook used as /B3: snapshot files after C2, before C3.
.MODEL SMALL
.STACK 100h
.DATA
maskfile DB '*.*',0
srcname  DB 'E:\',13 DUP (0)
dstname  DB 'E:\IR\',13 DUP (0)
inhandle DW ?
outhandle DW ?
dta      DB 43 DUP (0)
buffer   DB 512 DUP (0)
.CODE
start:
    mov ax,@data
    mov ds,ax
    mov dx,OFFSET dta
    mov ah,1Ah
    int 21h
    mov dx,OFFSET maskfile
    xor cx,cx
    mov ah,4Eh
    int 21h
    jc finished
next_file:
    mov si,OFFSET dta+1Eh
    mov di,OFFSET srcname+3
    mov bx,OFFSET dstname+6
    mov cx,13
copy_name:
    mov al,[si]
    mov [di],al
    mov [bx],al
    inc si
    inc di
    inc bx
    loop copy_name
    call copy_file
    mov dx,OFFSET maskfile
    mov ah,4Fh
    int 21h
    jnc next_file
finished:
    mov ax,4C00h
    int 21h
copy_file PROC NEAR
    mov dx,OFFSET srcname
    mov ax,3D00h
    int 21h
    jc copy_done
    mov inhandle,ax
    mov dx,OFFSET dstname
    xor cx,cx
    mov ah,3Ch
    int 21h
    jc close_input
    mov outhandle,ax
copy_loop:
    mov bx,inhandle
    mov cx,512
    mov dx,OFFSET buffer
    mov ah,3Fh
    int 21h
    jc close_both
    or ax,ax
    jz close_both
    mov cx,ax
    mov bx,outhandle
    mov dx,OFFSET buffer
    mov ah,40h
    int 21h
    jc close_both
    jmp copy_loop
close_both:
    mov bx,outhandle
    mov ah,3Eh
    int 21h
close_input:
    mov bx,inhandle
    mov ah,3Eh
    int 21h
copy_done:
    ret
copy_file ENDP
END start
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pins() -> None:
    for prof in (MSC, MASM):
        for rel, expected in prof["files"].items():
            actual = sha(Path(prof["directory"]) / rel)
            if actual != expected:
                raise RuntimeError(f"pinned hash mismatch: {rel}: {actual} != {expected}")
    if sha(Path(RUNNER["path"])) != RUNNER["sha256"]:
        raise RuntimeError("DOSBox-X runner hash mismatch")


def write_conf(work: Path) -> None:
    conf = []
    for section, values in RUNNER["conf"].items():
        conf.append(f"[{section}]")
        conf.extend(f"{key}={value}" for key, value in values.items())
    conf += [
        "[autoexec]",
        f'mount d "{Path(MSC["directory"]).resolve()}" -ro',
        f'mount e "{work.resolve()}"',
        f'mount m "{Path(MASM["directory"]).resolve()}" -ro',
        "e:",
        "set PATH=D:\\BIN",
        "set TMP=E:\\",
        "set TEMP=E:\\",
        "call RUN.BAT",
        "exit",
    ]
    (work / "dosbox.conf").write_text("\n".join(conf) + "\n", encoding="ascii")


def strings(path: Path) -> list[str]:
    data = path.read_bytes()
    found = [m.group().decode("ascii", "replace")
             for m in re.finditer(rb"[\x20-\x7e]{4,}", data)]
    return found


def capture(label: str, source: str, debug_flag: str) -> dict:
    work = OUT / label
    if work.exists():
        raise FileExistsError(f"refusing to replace capture: {work}")
    work.mkdir(parents=True)
    (work / "IR").mkdir()
    (work / "UNIT.C").write_bytes(source.replace("\n", "\r\n").encode("ascii"))
    (work / "CAPB3.ASM").write_bytes(HOOK.replace("\n", "\r\n").encode("ascii"))
    flags = "/AL /Os /Og /Oe /EM" + (f" {debug_flag}" if debug_flag else "")
    run = [
        "@echo off",
        "MD E:\\IR",
        "M:\\MASM.EXE E:\\CAPB3.ASM,E:\\CAPB3.OBJ,E:\\CAPB3.LST; > E:\\MASM.LOG",
        "M:\\LINK.EXE E:\\CAPB3.OBJ,E:\\CAPB3.EXE,,,; > E:\\LINK.LOG",
        f"D:\\BIN\\CL.EXE /c {flags} /B3 E:\\CAPB3.EXE E:\\UNIT.C > E:\\CL.LOG",
        "exit",
    ]
    (work / "RUN.BAT").write_bytes(("\r\n".join(run) + "\r\n").encode("ascii"))
    write_conf(work)
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    argv = [RUNNER["path"], "-conf", str(work / "dosbox.conf"), "-fastlaunch", "-exit", "-nomenu"]
    proc = subprocess.run(argv, cwd=work, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=180,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    (work / "dosbox-output.txt").write_bytes(proc.stdout)
    copied = sorted((work / "IR").iterdir())
    files = []
    for path in copied:
        if path.is_file():
            b = path.read_bytes()
            files.append({"name": path.name, "size": len(b), "sha256": sha(path),
                          "printable_strings": strings(path)})
    summary = {
        "case": label,
        "source_sha256": hashlib.sha256(source.encode("ascii")).hexdigest(),
        "profile": "msc600ax",
        "command": run[-2],
        "hook": "CAPB3.EXE; invoked as /B3 after C2L and before C3L",
        "returncode": proc.returncode,
        "captured_files": files,
        "logs": {n: (work / n).read_text(encoding="latin1", errors="replace")
                 if (work / n).exists() else None
                 for n in ("MASM.LOG", "LINK.LOG", "CL.LOG")},
        "workdir": str(work),
    }
    (work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case": label, "workdir": str(work), "files": [
        (f["name"], f["size"], f["sha256"]) for f in files],
        "logs": summary["logs"]}, indent=2))
    return summary


def main() -> None:
    check_pins()
    OUT.mkdir(parents=True, exist_ok=True)
    reports = []
    for label, (source, debug_flag) in CASES.items():
        summary_path = OUT / label / "summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            expected = hashlib.sha256(source.encode("ascii")).hexdigest()
            if summary.get("source_sha256") != expected:
                raise RuntimeError(f"existing {label} capture has a different source hash; inspect scratch manually")
            reports.append(summary)
        else:
            reports.append(capture(label, source, debug_flag))
    for label, path in FILE_CASES.items():
        if not path.is_file():
            raise FileNotFoundError(f"required probe source is missing: {path}")
        source = path.read_text(encoding="latin1")
        summary_path = OUT / label / "summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            expected = hashlib.sha256(source.encode("ascii")).hexdigest()
            if summary.get("source_sha256") != expected:
                raise RuntimeError(f"existing {label} capture has a different source hash; inspect scratch manually")
            reports.append(summary)
        else:
            reports.append(capture(label, source, "/Zi"))
    (OUT / "matrix.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print(f"matrix={OUT / 'matrix.json'}")


if __name__ == "__main__":
    main()
