from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = Path(__file__).resolve().parent
# Preserve the failed initial fixture as an immutable diagnostic record.
OUT = WORKER_ROOT / "run-v26n"
PROVIDER = WORKER_ROOT / "provider.c"
PROVIDER_TEXT = PROVIDER.read_text(encoding="ascii")
PROFILE = "msc600ax"
FLAGS = ["/AL", "/Os", "/Gs"]
OWNER_NAMES = [
    "_fd_50F6_47DA", "_fd_50F6_4A1A", "_fd_50F6_4A42", "_fd_50F6_4B28",
    "_fd_50F6_4B2C", "_fd_50F6_4B2E", "_fd_50F6_4B8A", "_fd_50F6_4B8E",
    "_fd_50F6_4BAA",
]
POSITIVE_ALIASES = [
    {"alias": "_ProbePtY", "target": "_fd_50F6_47DA", "delta": 2},
    {"alias": "_ProbeFont4", "target": "_fd_50F6_4A1A", "delta": 12},
    {"alias": "_ProbeAnimSeg", "target": "_fd_50F6_4A42", "delta": 2},
    {"alias": "_ProbeHandleSeg", "target": "_fd_50F6_4B28", "delta": 2},
    {"alias": "_ProbeScaleHi", "target": "_fd_50F6_4B8A", "delta": 2},
    {"alias": "_ProbeBankLast", "target": "_fd_50F6_4B8E", "delta": 26},
    {"alias": "_ProbeProgLast", "target": "_fd_50F6_4BAA", "delta": 26},
]

MAIN_POSITIVE = r'''#include <stddef.h>
extern int far puts(char far *text);
struct Pt { int x; int y; };
struct AnimObj;
extern struct Pt far fd_50F6_47DA;
extern void far *fd_50F6_4A1A[4];
extern struct AnimObj far * far fd_50F6_4A42;
extern char far * far * far fd_50F6_4B28;
extern int far fd_50F6_4B2C;
extern int far fd_50F6_4B2E;
extern long far fd_50F6_4B8A;
extern int far fd_50F6_4B8E[14];
extern int far fd_50F6_4BAA[14];
extern int far ProbePtY;
extern void far * far ProbeFont4;
extern unsigned int far ProbeAnimSeg;
extern unsigned int far ProbeHandleSeg;
extern unsigned int far ProbeScaleHi;
extern int far ProbeProgLast;
extern int far ProbeBankLast;
extern char far fontTest0[];
extern char far fontTest1[];
extern char far fontTest2[];
extern char far fontTest3[];
extern char far animTest[];
extern char far payloadTest[];
extern int far far_raw_check(void);
extern void far typed_write_test(void);
typedef char c_int_2[(sizeof(int) == 2) ? 1 : -1];
typedef char c_long_4[(sizeof(long) == 4) ? 1 : -1];
typedef char c_far_void_4[(sizeof(void far *) == 4) ? 1 : -1];
typedef char c_far_int_4[(sizeof(int far *) == 4) ? 1 : -1];
typedef char c_point_4[(sizeof(struct Pt) == 4) ? 1 : -1];
typedef char c_font_table_16[(sizeof(fd_50F6_4A1A) == 16) ? 1 : -1];
typedef char c_program_table_28[(sizeof(fd_50F6_4B8E) == 28) ? 1 : -1];
typedef char c_bank_table_28[(sizeof(fd_50F6_4BAA) == 28) ? 1 : -1];

static int far all_zero(void)
{
    int i;
    unsigned char far *p;
    p = (unsigned char far *)&fd_50F6_47DA;
    for (i = 0; i < 4; i++) if (p[i]) return 0;
    p = (unsigned char far *)fd_50F6_4A1A;
    for (i = 0; i < 16; i++) if (p[i]) return 0;
    p = (unsigned char far *)&fd_50F6_4A42;
    for (i = 0; i < 4; i++) if (p[i]) return 0;
    p = (unsigned char far *)&fd_50F6_4B28;
    for (i = 0; i < 4; i++) if (p[i]) return 0;
    p = (unsigned char far *)&fd_50F6_4B2C;
    for (i = 0; i < 2; i++) if (p[i]) return 0;
    p = (unsigned char far *)&fd_50F6_4B2E;
    for (i = 0; i < 2; i++) if (p[i]) return 0;
    p = (unsigned char far *)&fd_50F6_4B8A;
    for (i = 0; i < 4; i++) if (p[i]) return 0;
    p = (unsigned char far *)fd_50F6_4B8E;
    for (i = 0; i < 28; i++) if (p[i]) return 0;
    p = (unsigned char far *)fd_50F6_4BAA;
    for (i = 0; i < 28; i++) if (p[i]) return 0;
    return 1;
}

int main(void)
{
    int raw_result;
    if (sizeof(fd_50F6_4A1A) != 16 || sizeof(fd_50F6_4B8E) != 28 || sizeof(fd_50F6_4BAA) != 28 ||
        sizeof(fd_50F6_4A42) != 4 || sizeof(fd_50F6_4B28) != 4 || sizeof(fd_50F6_4B8A) != 4) {
        puts("FAIL_WIDTH"); return 1;
    }
    if (!all_zero()) { puts("FAIL_CRT_ZERO"); return 2; }
    if (&fd_50F6_47DA.y != &ProbePtY ||
        (char far *)&fd_50F6_4A1A[3] != (char far *)&ProbeFont4 ||
        (char far *)&((unsigned int far *)&fd_50F6_4A42)[1] != (char far *)&ProbeAnimSeg ||
        (char far *)&((unsigned int far *)&fd_50F6_4B28)[1] != (char far *)&ProbeHandleSeg ||
        (char far *)&((unsigned int far *)&fd_50F6_4B8A)[1] != (char far *)&ProbeScaleHi ||
        &fd_50F6_4B8E[13] != &ProbeBankLast || &fd_50F6_4BAA[13] != &ProbeProgLast) {
        puts("FAIL_PLUS_TWO_OR_LAST_ELEMENT_ALIAS"); return 3;
    }
    if ((char far *)&fd_50F6_4A42 == (char far *)&fd_50F6_4B28 ||
        (char far *)&fd_50F6_4B2C == (char far *)&fd_50F6_4B2E ||
        (char far *)fd_50F6_4B8E == (char far *)fd_50F6_4BAA) {
        puts("FAIL_SEPARATE_BACKING"); return 4;
    }
    typed_write_test();
    if (fd_50F6_47DA.x != -1234 || fd_50F6_47DA.y != 0x2345 ||
        fd_50F6_4A1A[0] != (void far *)fontTest0 ||
        fd_50F6_4A1A[1] != (void far *)fontTest1 ||
        fd_50F6_4A1A[2] != (void far *)fontTest2 ||
        fd_50F6_4A1A[3] != (void far *)fontTest3 ||
        (char far *)fd_50F6_4A42 != animTest ||
        *fd_50F6_4B28 != payloadTest || fd_50F6_4B2C != -1234 ||
        fd_50F6_4B2E != 0x01e0 || fd_50F6_4B8A != 95L ||
        fd_50F6_4B8E[0] != 0 || fd_50F6_4B8E[13] != 52 ||
        fd_50F6_4BAA[0] != 0 || fd_50F6_4BAA[13] != 5) {
        puts("FAIL_TYPED_VIEW"); return 5;
    }
    if (ProbePtY != 0x2345 || ProbeAnimSeg == 0 || ProbeHandleSeg == 0 ||
        ProbeScaleHi != 0 || ProbeBankLast != 52 || ProbeProgLast != 5) {
        puts("FAIL_INTERIOR_VIEW"); return 6;
    }
    raw_result = far_raw_check();
    if (raw_result == 11) { puts("RAW_PT_BYTE0"); return 7; }
    if (raw_result == 12) { puts("RAW_PT_BYTE1"); return 7; }
    if (raw_result == 13) { puts("RAW_PT_BYTE2"); return 7; }
    if (raw_result == 14) { puts("RAW_PT_BYTE3"); return 7; }
    if (raw_result == 1) { puts("RAW_PT_BYTES"); return 7; }
    if (raw_result == 2) { puts("RAW_4B2C_BYTES"); return 7; }
    if (raw_result == 3) { puts("RAW_4B2E_BYTES"); return 7; }
    if (raw_result == 4) { puts("RAW_4B8A_BYTES"); return 7; }
    if (raw_result == 5) { puts("RAW_FONT_POINTERS"); return 7; }
    if (raw_result == 6) { puts("RAW_ANIM_POINTER"); return 7; }
    if (raw_result == 7) { puts("RAW_HANDLE_POINTER"); return 7; }
    if (raw_result == 8) { puts("RAW_PAYLOAD_POINTER"); return 7; }
    if (raw_result == 9) { puts("RAW_ARRAY_VALUES"); return 7; }
    puts("PASS_TYPED_RAW");
    return 0;
}
'''

TYPED_WRITER = r'''struct Pt { int x; int y; };
struct AnimObj;
struct Song { int program[14]; int bank[14]; char far * far *data; };
extern struct Pt far fd_50F6_47DA;
extern void far *fd_50F6_4A1A[4];
extern struct AnimObj far * far fd_50F6_4A42;
extern char far * far * far fd_50F6_4B28;
extern int far fd_50F6_4B2C;
extern int far fd_50F6_4B2E;
extern long far fd_50F6_4B8A;
extern int far fd_50F6_4B8E[14];
extern int far fd_50F6_4BAA[14];
char far fontTest0[2];
char far fontTest1[2];
char far fontTest2[2];
char far fontTest3[2];
char far animTest[4];
char far payloadTest[4];
char far * far handleSlot;
static struct Song sourceSong = {
    { 0, 7, 7, 7, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5 },
    { 0, 25, 53, 3, 54, 35, 46, 50, 51, 48, 0, 12, 43, 52 },
    0
};
void far typed_write_test(void)
{
    int i;
    long tempo;
    long v;
    fd_50F6_47DA.x = -1234;
    fd_50F6_47DA.y = 0x2345;
    fd_50F6_4A1A[0] = fontTest0;
    fd_50F6_4A1A[1] = fontTest1;
    fd_50F6_4A1A[2] = fontTest2;
    fd_50F6_4A1A[3] = fontTest3;
    fd_50F6_4A42 = (struct AnimObj far *)animTest;
    handleSlot = payloadTest;
    fd_50F6_4B28 = &handleSlot;
    fd_50F6_4B2C = -1234;
    fd_50F6_4B2E = 0x01e0;
    tempo = 500000L;
    v = tempo / 1000 * 1194 / (unsigned)fd_50F6_4B2E;
    fd_50F6_4B8A = v / 13;
    for (i = 0; i < 14; i++) {
        fd_50F6_4B8E[i] = sourceSong.bank[i];
        fd_50F6_4BAA[i] = sourceSong.program[i];
    }
}
'''

RAW_READER = r'''extern int far puts(char far *text);
union FarPointerView { void far *p; unsigned int w[2]; unsigned char b[4]; };
extern unsigned char far fd_50F6_47DA[4];
extern unsigned char far fd_50F6_4A1A[16];
extern unsigned char far fd_50F6_4A42[4];
extern unsigned char far fd_50F6_4B28[4];
extern char far * far handleSlot;
extern unsigned char far fd_50F6_4B2C[2];
extern unsigned char far fd_50F6_4B2E[2];
extern unsigned char far fd_50F6_4B8A[4];
extern unsigned char far fd_50F6_4B8E[28];
extern unsigned char far fd_50F6_4BAA[28];
extern char far fontTest0[];
extern char far fontTest1[];
extern char far fontTest2[];
extern char far fontTest3[];
extern char far animTest[];
extern char far payloadTest[];
int far far_raw_check(void)
{
    unsigned char far *pt;
    unsigned char far *s;
    union FarPointerView exp;
    int i;
    pt = fd_50F6_47DA;
    if (pt[0] != 0x2e) return 11;
    if (pt[1] != 0xfb) return 12;
    if (pt[2] != 0x45) return 13;
    if (pt[3] != 0x23) return 14;
    s = fd_50F6_4B2C;
    if (s[0] != 0x2e || s[1] != 0xfb) return 2;
    s = fd_50F6_4B2E;
    if (s[0] != 0xe0 || s[1] != 0x01) return 3;
    s = fd_50F6_4B8A;
    if (s[0] != 95 || s[1] != 0 || s[2] != 0 || s[3] != 0) return 4;
    for (i = 0; i < 4; i++) {
        void far *p;
        if (i == 0) p = fontTest0;
        else if (i == 1) p = fontTest1;
        else if (i == 2) p = fontTest2;
        else p = fontTest3;
        exp.p = p;
        if (fd_50F6_4A1A[4 * i] != exp.b[0] || fd_50F6_4A1A[4 * i + 1] != exp.b[1] ||
            fd_50F6_4A1A[4 * i + 2] != exp.b[2] || fd_50F6_4A1A[4 * i + 3] != exp.b[3]) return 5;
    }
    exp.p = animTest;
    if (fd_50F6_4A42[0] != exp.b[0] || fd_50F6_4A42[1] != exp.b[1] ||
        fd_50F6_4A42[2] != exp.b[2] || fd_50F6_4A42[3] != exp.b[3]) return 6;
    exp.p = (void far *)&handleSlot;
    if (fd_50F6_4B28[0] != exp.b[0] || fd_50F6_4B28[1] != exp.b[1] ||
        fd_50F6_4B28[2] != exp.b[2] || fd_50F6_4B28[3] != exp.b[3]) return 7;
    exp.p = payloadTest;
    s = (unsigned char far *)&handleSlot;
    if (s[0] != exp.b[0] || s[1] != exp.b[1] || s[2] != exp.b[2] || s[3] != exp.b[3]) return 8;
    {
        static unsigned int sourceBank[14] = { 0, 25, 53, 3, 54, 35, 46, 50, 51, 48, 0, 12, 43, 52 };
        static unsigned int sourceProgram[14] = { 0, 7, 7, 7, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5 };
        for (i = 0; i < 14; i++)
            if (fd_50F6_4B8E[2 * i] != (sourceBank[i] & 0xff) ||
                fd_50F6_4B8E[2 * i + 1] != (sourceBank[i] >> 8) ||
                fd_50F6_4BAA[2 * i] != (sourceProgram[i] & 0xff) ||
                fd_50F6_4BAA[2 * i + 1] != (sourceProgram[i] >> 8)) return 9;
    }
    return 0;
}
'''

WIDTH_MAIN = r'''extern int far puts(char far *text);
extern int far fd_50F6_4B2C;
extern int far ProbeUpper;
int main(void)
{
    fd_50F6_4B2C = 0x1234;
    ProbeUpper = 0x5678;
    if (*(unsigned long far *)&fd_50F6_4B2C == 0x56781234UL) {
        puts("WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED"); return 0;
    }
    puts("FAIL_WIDTH_CONTRAST"); return 1;
}
'''

SIGN_MAIN = r'''extern int far puts(char far *text);
extern unsigned int far fd_50F6_4B2C;
int main(void)
{
    fd_50F6_4B2C = -1;
    if (fd_50F6_4B2C > 32767U) { puts("WRONG_UNSIGNED_VIEW_DETECTED"); return 0; }
    puts("FAIL_UNSIGNED_VIEW_CONTRAST"); return 1;
}
'''

INIT_MAIN = r'''extern int far puts(char far *text);
int main(void)
{
    if (fd_50F6_4B2E != 0) { puts("INITIALIZED_NONZERO_OWNER_DETECTED"); return 0; }
    puts("FAIL_INITIALIZER_CONTRAST"); return 1;
}
'''

SHIFT_MAIN = r'''extern int far puts(char far *text);
extern int far fd_50F6_4B2E;
extern int far ProbeAlias;
int main(void)
{
    if (&fd_50F6_4B2E != &ProbeAlias) { puts("SHIFTED_ALIAS_BASE_DETECTED"); return 0; }
    puts("FAIL_SHIFTED_ALIAS_CONTRAST"); return 1;
}
'''

COLLAPSE_MAIN = r'''extern int far puts(char far *text);
extern int far fd_50F6_4B2C;
extern int far fd_50F6_4B2E;
int main(void)
{
    fd_50F6_4B2C = 0x1234;
    fd_50F6_4B2E = 0x5678;
    if (&fd_50F6_4B2C == &fd_50F6_4B2E || fd_50F6_4B2C != 0x1234 || fd_50F6_4B2E != 0x5678) {
        puts("SEPARATE_BACKING_ALIAS_COLLAPSE_DETECTED"); return 0;
    }
    puts("FAIL_SEPARATE_BACKING_CONTRAST"); return 1;
}
'''


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    actual = sha(raw)
    if expected is not None and actual != expected:
        raise RuntimeError(f"hash mismatch for {path}: {actual} != {expected}")
    try:
        rel = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(path.resolve())
    return {"path": rel, "sha256": actual, "size": len(raw)}


def add_pin(rows: list[dict], seen: set[tuple[str, str]], path: Path, expected: str | None = None) -> dict:
    row = pin(path, expected)
    key = (row["path"].casefold(), row["sha256"])
    if key not in seen:
        seen.add(key)
        rows.append(row)
    return row


def compile_unit(source: str, basename: str, out: Path, inputs: list, seen: set):
    if len(basename) > 8:
        raise RuntimeError("MSC basename exceeds eight characters: " + basename)
    source_dir = OUT / "compiled-sources"
    object_dir = OUT / "compiled-objects"
    source_dir.mkdir(exist_ok=True)
    object_dir.mkdir(exist_ok=True)
    source_path = source_dir / (basename + ".c")
    source_path.write_text(source, encoding="ascii", newline="")
    add_pin(inputs, seen, source_path)
    result = compiler.compile_c(source, PROFILE, FLAGS, basename=basename, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"MSC compile failed for {basename}:\n{result.log}")
    object_path = object_dir / (basename + ".OBJ")
    object_path.write_bytes(result.obj)
    add_pin(inputs, seen, object_path)
    if result.workdir and (result.workdir / "CL.LOG").exists():
        add_pin(inputs, seen, result.workdir / "CL.LOG")
    return {"basename": basename, "source": source_path, "object": object_path,
            "object_bytes": result.obj, "compiler_log": result.log, "argv": result.argv}


def omf_shape(raw: bytes) -> dict:
    obj = OmfReader(communals=True).read(raw)
    communals = sorted(bindings.communal_key(row) for row in obj.communals)
    initialized = {name: data.hex() for name, data in obj.segments.items() if data and name != "$$SYMBOLS"}
    return {
        "module_name": obj.name,
        "communals": [dict(zip(("name", "kind", "count", "element_size", "length"), row)) for row in communals],
        "publics": [{k: p.get(k) for k in ("name", "segment", "offset")} for p in obj.publics],
        "externals": sorted(obj.externals),
        "segment_lengths": obj.segment_lengths,
        "initialized_data_hex": initialized,
        "linker_fixups": [{k: f.get(k) for k in ("segment", "offset", "width", "loc", "self_relative",
                                                      "target_kind", "target", "frame_kind", "frame",
                                                      "displacement", "encoded_addend")} for f in obj.linker_fixups],
    }


def parse_public_matrix(map_text: str) -> tuple[dict, dict]:
    lines = map_text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        match = re.match(r"^\s*Address\s+Publics by (Name|Value)\s*$", line, re.I)
        if match:
            hits.append((i, match.group(1).title()))
    matrices = {"Name": {}, "Value": {}}
    headings = {"Name": 0, "Value": 0}
    row_re = re.compile(r"^\s*([0-9A-F]{4}:[0-9A-F]{4})(?:\s+(?:Abs|Res))?\s+([^\s]+)\s*$", re.I)
    for hit_index, (start, kind) in enumerate(hits):
        headings[kind] += 1
        end = hits[hit_index + 1][0] if hit_index + 1 < len(hits) else len(lines)
        for line in lines[start + 1:end]:
            match = row_re.match(line)
            if match:
                address, name = match.groups()
                if name.casefold() in {k.casefold() for k in matrices[kind]}:
                    raise RuntimeError(f"duplicate map public {kind}/{name}")
                matrices[kind][name] = address.upper()
    return matrices, {key: {"heading_present": count > 0, "heading_count": count,
                            "public_count": len(matrices[key])} for key, count in headings.items()}


def run_fixture(linker_name: str, linker: dict, tool_dir: Path, runner: dict,
                runtime_rows: list, objects: list[tuple[Path, str]], case_name: str,
                expected_marker: str, aliases: list[dict] | None = None,
                owner_names: list[str] | None = None) -> dict:
    aliases = aliases or []
    folder = OUT / "fixtures" / linker_name / case_name
    folder.mkdir(parents=True, exist_ok=False)
    for object_path, filename in objects:
        if len(Path(filename).stem) > 8:
            raise RuntimeError("fixture object stem exceeds eight characters: " + filename)
        shutil.copyfile(object_path, folder / filename)
    for row in runtime_rows:
        shutil.copyfile(row["path"], folder / Path(row["path"]).name.upper())
    file_names = ", ".join(Path(filename).stem for _, filename in objects)
    link_lines = ["OUTPUT PROBE", "MAP = PROBE S,N,A,L", "NODEFLIB", "LIBRARY LLIBCR, LIBH",
                  "FILE " + file_names]
    if any(Path(filename).stem.casefold() == "owner" for _, filename in objects):
        link_lines.extend(["BEGINAREA", "SECTION FILE OWNER", "ENDAREA"])
    # RTLink DEFINE offsets are hexadecimal text: encode source-derived byte deltas in hex.
    link_lines.extend(f"DEFINE {row['alias']} = {row['target']} + {row['delta']:X}" if row["delta"] else
                      f"DEFINE {row['alias']} = {row['target']}" for row in aliases)
    (folder / "PROBE.LNK").write_bytes(("\r\n".join(link_lines) + "\r\n").encode("ascii"))
    (folder / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (folder / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "if exist PROBE.EXE PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines.extend(f"{key}={value}" for key, value in settings.items())
    conf_lines.extend(["[autoexec]", f'mount c "{folder.resolve()}"', f'mount d "{tool_dir}" -ro',
                       "c:", "call RUN.BAT", "exit"])
    conf_path = folder / "dosbox.conf"
    conf_path.write_text("\n".join(conf_lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    completed = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                               cwd=folder, env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=90,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    run_path, link_path, map_path = folder / "RUN.LOG", folder / "LINK.LOG", folder / "PROBE.MAP"
    run_raw = run_path.read_bytes() if run_path.exists() else b""
    link_raw = link_path.read_bytes() if link_path.exists() else b""
    map_raw = map_path.read_bytes() if map_path.exists() else b""
    run_text = run_raw.decode("latin1")
    link_text = link_raw.decode("latin1", errors="replace")
    map_text = map_raw.decode("latin1", errors="replace")
    matrices, section_rows = parse_public_matrix(map_text) if map_text else ({"Name": {}, "Value": {}},
                                                                             {"Name": {}, "Value": {}})
    exe = folder / "PROBE.EXE"
    required_publics = list(owner_names or OWNER_NAMES) + [row["alias"] for row in aliases]
    matrices_equal = ({name.casefold(): address for name, address in matrices["Name"].items()} ==
                      {name.casefold(): address for name, address in matrices["Value"].items()})
    missing = {section: [name for name in required_publics if name.casefold() not in
                         {k.casefold() for k in matrices[section]}] for section in ("Name", "Value")}
    diagnostics = []
    for pattern in (r"(?i)warning", r"(?i)unused", r"(?i)unresolved", r"(?i)undefined", r"(?i)not defined", r"(?i)link error"):
        for match in re.finditer(pattern, link_text):
            excerpt = link_text[max(0, match.start() - 60):min(len(link_text), match.end() + 120)].replace("\r", "")
            if excerpt not in diagnostics:
                diagnostics.append(excerpt.strip())
    link_clean = exe.exists() and not diagnostics
    raw_aliases = []
    name_matrix = {name.casefold(): value for name, value in matrices["Name"].items()}
    for row in aliases:
        alias_addr = name_matrix.get(row["alias"].casefold())
        target_addr = name_matrix.get(row["target"].casefold())
        observed = None
        if alias_addr and target_addr:
            aseg, aoff = (int(p, 16) for p in alias_addr.split(":"))
            tseg, toff = (int(p, 16) for p in target_addr.split(":"))
            observed = {"same_segment": aseg == tseg, "delta": aoff - toff}
        raw_aliases.append({**row, "alias_address": alias_addr, "target_address": target_addr,
                            "observed": observed,
                            "passed": bool(observed and observed["same_segment"] and observed["delta"] == row["delta"])})
    expected_raw = (expected_marker + "\r\n").encode("ascii")
    actual_marker = run_raw[:-2].decode("ascii") if run_raw.endswith(b"\r\n") else run_text
    passed = (completed.returncode == 0 and run_raw == expected_raw and link_clean and bool(map_raw)
              and matrices_equal and not any(missing.values())
              and all(row["passed"] for row in raw_aliases))
    raw_pin = pin(run_path) if run_path.exists() else {"path": str(run_path), "sha256": sha(run_raw), "size": 0}
    link_pin = pin(link_path) if link_path.exists() else {"path": str(link_path), "sha256": sha(link_raw), "size": 0}
    map_pin = pin(map_path) if map_path.exists() else {"path": str(map_path), "sha256": sha(map_raw), "size": 0}
    files = [pin(path) for path in sorted(folder.iterdir(), key=lambda p: p.name.casefold()) if path.is_file()]
    return {
        "linker": linker_name, "case": case_name, "expected": expected_marker,
        "actual": actual_marker, "actual_output_verbatim": run_text,
        "runner_exit": completed.returncode, "timed_out": False,
        "clean": link_clean, "linker_diagnostics": diagnostics,
        "linker_produced_executable": exe.exists(), "linker_produced_map": map_path.exists(),
        "expected_owner_publics": required_publics,
        "owner_publics_found": [name for name in required_publics if name.casefold() in name_matrix],
        "raw": {"text": run_text, "hex": run_raw.hex(), "sha256": sha(run_raw),
                "size": len(run_raw), "artifact_pin": raw_pin},
        "link_pin": link_pin, "map_pin": map_pin,
        "link_log_verbatim": link_text, "link_log_hex": link_raw.hex(),
        "map_sections": section_rows, "public_address_matrix": matrices,
        "aliases": raw_aliases, "matrix_equal": matrices_equal, "missing_publics": missing,
        "files": files, "passed": passed,
    }


def main() -> int:
    if len(PROVIDER_TEXT.splitlines()) < 5:
        raise RuntimeError("provider candidate is unexpectedly empty")
    if (OUT / "runtime-receipt-v26.json").exists():
        raise SystemExit("refusing to overwrite a completed v26 runtime run")
    fixture_root = OUT / "fixtures"
    if fixture_root.exists() and any(fixture_root.iterdir()):
        raise SystemExit("refusing to overwrite partial runtime fixtures; use a fresh worker suffix")
    denied = dos.install_input_guard()
    fixture_root.mkdir(parents=True, exist_ok=True)
    compiler.WORK = OUT / "compiler-work"
    pins, seen = [], set()

    toolchain_path = ROOT / "layout/toolchain.json"
    manifest_path = ROOT / "layout/manifest.json"
    profile = compiler.verify_profile(PROFILE)
    toolchain = compiler.toolchain()
    report_path = ROOT / "build/source-only-dos/build-report.json"
    runtime_rows = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in manifest["runtime"]["libraries"].values():
        add_pin(pins, seen, Path(row["path"]), row["sha256"])
        runtime_rows.append(row)
    runner = toolchain["runners"]["dosbox-x"]
    add_pin(pins, seen, Path(runner["path"]), runner["sha256"])

    for path in (PROVIDER, Path(__file__), WORKER_ROOT / "static-audit-v26.json", manifest_path,
                 toolchain_path, report_path, ROOT / "layout/symbols.json",
                 ROOT / "work/source-only-dos/static-completeness/index-v1.json",
                 ROOT / "evidence/behavior/manifest.json", ROOT / "tools/compiler.py",
                 ROOT / "tools/omf.py", ROOT / "tools/dos_source_bindings.py",
                 ROOT / "tools/source_only_dos.py", ROOT / "tools/dos_storage_contracts.py",
                 ROOT / "tools/dos_storage_policies_v25.py"):
        add_pin(pins, seen, path)
    # Every canonical source, effective strict source, and each of the 29 receipts
    # from the static audit remains a pinned runtime input.
    static_audit = json.loads((WORKER_ROOT / "static-audit-v26.json").read_text(encoding="utf-8"))
    for row in static_audit["source_graph"]["source_paths"]:
        add_pin(pins, seen, ROOT / row["path"], row["sha256"])
    for row in static_audit["source_graph"]["receipt_pins"]:
        add_pin(pins, seen, ROOT / row["path"], row["sha256"])
    for rel, expected in profile["files"].items():
        add_pin(pins, seen, Path(profile["directory"]) / rel, expected)
    for rel, expected in (profile.get("include_files") or {}).items():
        include_root = compiler.include_root(profile)
        path = ROOT / rel[5:] if rel.startswith("repo:") else include_root / rel
        add_pin(pins, seen, path, expected)

    # Natural provider and compiler-only contrasts. Unique DOS object basenames
    # stay within MSC's eight-character limit.
    expected_comms = [
        ("_fd_50F6_47DA", "far", 4, 1, 4),
        ("_fd_50F6_4A1A", "far", 4, 4, 16),
        ("_fd_50F6_4A42", "far", 4, 1, 4),
        ("_fd_50F6_4B28", "far", 4, 1, 4),
        ("_fd_50F6_4B2C", "far", 2, 1, 2),
        ("_fd_50F6_4B2E", "far", 2, 1, 2),
        ("_fd_50F6_4B8A", "far", 4, 1, 4),
        ("_fd_50F6_4B8E", "far", 14, 2, 28),
        ("_fd_50F6_4BAA", "far", 14, 2, 28),
    ]
    exact = compile_unit(PROVIDER_TEXT, "SNDST26", OUT, pins, seen)
    wrong_width_source = PROVIDER_TEXT.replace("int far fd_50F6_4B2C;", "long far fd_50F6_4B2C;")
    wrong_width = compile_unit(wrong_width_source, "SNDWD26", OUT, pins, seen)
    wrong_count_source = PROVIDER_TEXT.replace("void far *fd_50F6_4A1A[4];", "void far *fd_50F6_4A1A[3];")
    wrong_count = compile_unit(wrong_count_source, "SNDAR326", OUT, pins, seen)
    wrong_pointer_source = PROVIDER_TEXT.replace("void far *fd_50F6_4A1A[4];", "void near *fd_50F6_4A1A[4];")
    wrong_pointer = compile_unit(wrong_pointer_source, "SNDNR26", OUT, pins, seen)
    initialized_source = PROVIDER_TEXT.replace("int far fd_50F6_4B2E;", "int far fd_50F6_4B2E = 1;")
    initialized = compile_unit(initialized_source, "SNDIN26", OUT, pins, seen)
    collapse_source = PROVIDER_TEXT.replace("int far fd_50F6_4B2E;\n", "")
    collapse_owner = compile_unit(collapse_source, "SNDCOL26", OUT, pins, seen)

    mains = {
        "typed_raw_positive": compile_unit(MAIN_POSITIVE, "RTPOS26", OUT, pins, seen),
        "wrong_width_long_owner": compile_unit(WIDTH_MAIN, "RTWID26", OUT, pins, seen),
        "wrong_signedness_unsigned_view": compile_unit(SIGN_MAIN, "RTSGN26", OUT, pins, seen),
        "initialized_nonzero_owner": compile_unit(initialized_source + "\n" + INIT_MAIN, "RTINI26", OUT, pins, seen),
        "shifted_alias_base_plus_two": compile_unit(SHIFT_MAIN, "RTSFT26", OUT, pins, seen),
        "separate_backing_alias_collapse": compile_unit(COLLAPSE_MAIN, "RTSEP26", OUT, pins, seen),
    }
    writer = compile_unit(TYPED_WRITER, "TYPED26", OUT, pins, seen)
    raw_reader = compile_unit(RAW_READER, "RAWCHK26", OUT, pins, seen)

    shapes = {name: omf_shape(unit["object_bytes"]) for name, unit in {
        "candidate": exact, "wrong_width": wrong_width, "wrong_font_count": wrong_count,
        "wrong_pointer_width": wrong_pointer, "initialized_owner": initialized,
        "separate_backing_owner_missing_4B2E": collapse_owner}.items()}
    got = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(exact["object_bytes"]).communals)
    if got != sorted(expected_comms):
        raise RuntimeError("candidate OMF communal rows differ from exact expected shape:\n" + repr(got))
    exact_shape = shapes["candidate"]
    if exact_shape["publics"] or exact_shape["initialized_data_hex"] or any(exact_shape["segment_lengths"].values()):
        raise RuntimeError("natural candidate is not a data-less uninitialized far communal object")
    if sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(wrong_width["object_bytes"]).communals) == got:
        raise RuntimeError("wrong-width compiler contrast did not alter COMDEF size")
    if sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(wrong_count["object_bytes"]).communals) == got:
        raise RuntimeError("wrong-font-count compiler contrast did not alter COMDEF size")
    if sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(wrong_pointer["object_bytes"]).communals) == got:
        raise RuntimeError("wrong-pointer-width compiler contrast did not alter COMDEF size")
    initialized_obj = OmfReader(communals=True).read(initialized["object_bytes"])
    if any(bindings.communal_key(row)[0].casefold() == "_fd_50f6_4b2e" for row in initialized_obj.communals) or not shapes["initialized_owner"]["initialized_data_hex"]:
        raise RuntimeError("initialized-storage compiler contrast did not emit initialized bytes")
    collapse_comms = sorted(bindings.communal_key(row) for row in
                            OmfReader(communals=True).read(collapse_owner["object_bytes"]).communals)
    if any(row[0].casefold() == "_fd_50f6_4b2e" for row in collapse_comms):
        raise RuntimeError("separate-backing contrast unexpectedly defines the collapsed symbol")

    linkers = {}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for rel, expected in linker["files"].items():
            add_pin(pins, seen, Path(linker["directory"]) / rel, expected)
        linkers[linker_name] = (linker, compiler.pinned_tree(linker))

    all_cases = []
    aliases = {
        "typed_raw_positive": POSITIVE_ALIASES,
        "wrong_width_long_owner": [{"alias": "_ProbeUpper", "target": "_fd_50F6_4B2C", "delta": 2}],
        "wrong_signedness_unsigned_view": [], "initialized_nonzero_owner": [],
        "shifted_alias_base_plus_two": [{"alias": "_ProbeAlias", "target": "_fd_50F6_4B2E", "delta": 2}],
        "separate_backing_alias_collapse": [{"alias": "_fd_50F6_4B2E", "target": "_fd_50F6_4B2C", "delta": 0}],
    }
    expected_markers = {
        "typed_raw_positive": "PASS_TYPED_RAW",
        "wrong_width_long_owner": "WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED",
        "wrong_signedness_unsigned_view": "WRONG_UNSIGNED_VIEW_DETECTED",
        "initialized_nonzero_owner": "INITIALIZED_NONZERO_OWNER_DETECTED",
        "shifted_alias_base_plus_two": "SHIFTED_ALIAS_BASE_DETECTED",
        "separate_backing_alias_collapse": "SEPARATE_BACKING_ALIAS_COLLAPSE_DETECTED",
    }
    for linker_name, (linker, tool_dir) in linkers.items():
        cases = [
            ("typed_raw_positive", [
                (mains["typed_raw_positive"]["object"], "MAIN.OBJ"),
                (writer["object"], "TYPED.OBJ"), (raw_reader["object"], "RAWCHK.OBJ"),
                (exact["object"], "OWNER.OBJ")], expected_markers["typed_raw_positive"]),
            ("wrong_width_long_owner", [
                (mains["wrong_width_long_owner"]["object"], "MAIN.OBJ"),
                (wrong_width["object"], "OWNER.OBJ")], expected_markers["wrong_width_long_owner"]),
            ("wrong_signedness_unsigned_view", [
                (mains["wrong_signedness_unsigned_view"]["object"], "MAIN.OBJ"),
                (exact["object"], "OWNER.OBJ")], expected_markers["wrong_signedness_unsigned_view"]),
            ("initialized_nonzero_owner", [
                (mains["initialized_nonzero_owner"]["object"], "MAIN.OBJ")], expected_markers["initialized_nonzero_owner"]),
            ("shifted_alias_base_plus_two", [
                (mains["shifted_alias_base_plus_two"]["object"], "MAIN.OBJ"),
                (exact["object"], "OWNER.OBJ")], expected_markers["shifted_alias_base_plus_two"]),
            ("separate_backing_alias_collapse", [
                (mains["separate_backing_alias_collapse"]["object"], "MAIN.OBJ"),
                (collapse_owner["object"], "OWNER.OBJ")], expected_markers["separate_backing_alias_collapse"]),
        ]
        for case_name, objects, marker in cases:
            row = run_fixture(linker_name, linker, tool_dir, runner, runtime_rows, objects,
                              case_name, marker, aliases[case_name], OWNER_NAMES)
            all_cases.append(row)
            if not row["passed"]:
                raise RuntimeError("period linker/runtime case failed:\n" + json.dumps(row, indent=2))

    # Persist a compact, generic-contract-shaped worker candidate. It is not
    # reviewed or admitted; the parent must supply its independent policy/review.
    required_cases = {name: marker for name, marker in expected_markers.items()}
    compiler_controls = {}
    for control_name, shape in shapes.items():
        compiler_controls[control_name] = shape
    case_rows = []
    for row in all_cases:
        case_rows.append({key: row[key] for key in (
            "linker", "case", "expected", "actual", "raw", "link_pin", "map_pin", "runner_exit",
            "timed_out", "clean", "linker_diagnostics", "linker_produced_executable",
            "linker_produced_map", "expected_owner_publics", "owner_publics_found", "map_sections",
            "public_address_matrix", "aliases", "link_log_verbatim", "link_log_hex", "files", "passed")})
    expected_communal_dicts = [dict(zip(("name", "kind", "count", "element_size", "length"), row))
                               for row in got]
    final_inputs = sorted(pins, key=lambda row: row["path"].casefold())
    candidate = {
        "schema": "simant-root-source-storage-contract-v25",
        "category": "RESEARCH_CANDIDATE_NOT_ADMITTED",
        "module": "source-owned:remaining-sound-storage-v26",
        "root_reviewed": False,
        "all_required_checks_pass": len(all_cases) == 12 and all(row["passed"] for row in all_cases),
        "admitted": False,
        "communals": expected_communal_dicts,
        "required_cases": required_cases,
        "inputs": final_inputs,
        "cases": case_rows,
        "probe_source": pin(Path(__file__)),
        "compiler": {"profile": PROFILE, "product": profile["product"], "flags": FLAGS,
                     "required_flags": profile.get("required_flags", []), "provider_basename": "SNDST26"},
        "compiler_controls": compiler_controls,
        "candidate_provider": {"path": pin(PROVIDER), "module_name": "SNDST26",
                               "storage_only": True, "initialized_data_hex": exact_shape["initialized_data_hex"],
                               "omf": exact_shape, "provider_object": pin(exact["object"])},
        "control_contrasts": {
            "signed_word_to_long": {"basename": "SNDWD26", "candidate": shapes["candidate"]["communals"],
                                    "control": shapes["wrong_width"]["communals"],
                                    "runtime_marker": "WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED"},
            "font_table_count_4_to_3": {"basename": "SNDAR326", "candidate": shapes["candidate"]["communals"],
                                        "control": shapes["wrong_font_count"]["communals"]},
            "far_to_near_pointer": {"basename": "SNDNR26", "candidate": shapes["candidate"]["communals"],
                                    "control": shapes["wrong_pointer_width"]["communals"]},
            "initialized_nonzero": {"basename": "SNDIN26", "candidate_initialized_data": {},
                                    "control_initialized_data": shapes["initialized_owner"]["initialized_data_hex"]},
            "independent_4B2C_and_4B2E_backing": {"control_basename": "SNDCOL26",
                                               "control_owner_symbols": [r[0] for r in collapse_comms],
                                                   "link_alias": {"alias": "_fd_50F6_4B2E", "target": "_fd_50F6_4B2C", "delta": 0},
                                                   "runtime_marker": "SEPARATE_BACKING_ALIAS_COLLAPSE_DETECTED"},
            "interior_plus_two_views": POSITIVE_ALIASES,
        },
        "save_rec_pointer_fixups": [],
        "denied_oracle_reads": denied,
        "unresolved_sound_arrays": [
            {"name": "fd_50F6_4B30", "reason": "track_count g_7566 comes from song bytes; source has no checked capacity; selected byte pointer g_8E02 escapes"},
            {"name": "fd_50F6_4B42", "reason": "track_count g_7566 and selector g_756C are unchecked against a capacity"},
        ],
        "sound_selector_layout_gate": "OPEN: retain sound-selector-layout-review-v21; /s9 detector[9] data-as-code and conditional cleanup[9] adjacency remain unresolved.",
        "limits": [
            "All runtime fixtures contain only test-owned code and data plus pinned MSC runtime libraries; no game object, asset, original executable, hybrid image or executable fragment was an input.",
            "The candidate covers nine natural source-owned objects only. The two track-indexed arrays remain unresolved; no clamp, 18-entry capacity, or extent was inferred from g_8DD8, writes, neighboring addresses, or Win16 names.",
            "Component startup and ABI controls do not prove historical communal order, whole-song validity, /s9 safety, full sound cleanup, or original FAR_BSS placement.",
            "This worker evidence is root-false and does not write source-only bindings or change the active build report.",
        ],
    }
    candidate_path = OUT / "generic-storage-contract-candidate-v26.json"
    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "schema": "simant-dos-remaining-sound-storage-runtime-v26",
        "status": "ROOT_REVIEW_PENDING",
        "candidate_contract": pin(candidate_path),
        "provider": pin(PROVIDER),
        "static_receipt": pin(WORKER_ROOT / "static-audit-v26.json"),
        "case_count_per_linker": {name: sum(row["linker"] == name for row in all_cases)
                                   for name in ("rtlink400", "rtlink610")},
        "all_required_checks_pass": candidate["all_required_checks_pass"],
        "compiler_controls": compiler_controls,
        "cases": [{"linker": row["linker"], "case": row["case"], "actual": row["actual"],
                   "runner_exit": row["runner_exit"], "clean": row["clean"], "passed": row["passed"],
                   "raw": row["raw"], "public_count_name": row["map_sections"]["Name"]["public_count"],
                   "public_count_value": row["map_sections"]["Value"]["public_count"],
                   "public_address_matrix": row["public_address_matrix"], "aliases": row["aliases"],
                   "link_log_verbatim": row["link_log_verbatim"], "link_log_hex": row["link_log_hex"],
                   "link_pin": row["link_pin"], "map_pin": row["map_pin"], "files": row["files"]}
                  for row in all_cases],
        "inputs": final_inputs,
        "denied_oracle_reads": denied,
        "root_reviewed": False,
        "admitted": False,
    }
    receipt_path = OUT / "runtime-receipt-v26.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": candidate_path.relative_to(ROOT).as_posix(),
                      "receipt": receipt_path.relative_to(ROOT).as_posix(),
                      "communal_count": len(expected_communal_dicts),
                      "total_far_bss_bytes": sum(row["length"] for row in expected_communal_dicts),
                      "case_count_per_linker": receipt["case_count_per_linker"],
                      "all_required_checks_pass": candidate["all_required_checks_pass"],
                      "cases": [{"linker": row["linker"], "case": row["case"], "actual": row["actual"],
                                 "passed": row["passed"]} for row in all_cases]}, indent=2))
    return 0 if candidate["all_required_checks_pass"] else 1


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    import compiler
    import dos_source_bindings as bindings
    import source_only_dos as dos
    from omf import OmfReader

    raise SystemExit(main())
