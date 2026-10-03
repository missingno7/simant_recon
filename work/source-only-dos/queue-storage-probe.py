"""Research-only DOS queue fixture; never reads the historical game image."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader


SOURCE = ROOT / "src/root/m1B73.asm"
PROCS = ("_f_1B73_030F", "_f_1B73_032A", "_f_1B73_032E", "_f_1B73_036E")
QUEUE_SYMBOLS = ("_g_5FF0", "_g_5FF2", "_g_5FF4", "_g_5FF6",
                 "_g_5FF8", "_g_5FF9", "_g_5FFA", "_g_5FFE")
AUDIT_INPUTS = (
    "README.md", "docs/codegen-rules.md", "docs/tu-evidence.md",
    "evidence/behavior/supplemental/enternest-clock-boundary-20261002/dependencies/TickCount-source.asm",
    "evidence/behavior/supplemental/enternest-clock-boundary-20261002/negative-gating-research/TickCount-source.asm",
    "evidence/behavior/helpers/tutorial-contracts-v1/f_1C62_0415/f_1B73_032A.json",
    "evidence/behavior/helpers/tutorial-contracts-v1/f_1C62_0415/f_1B73_032E.json",
    "evidence/behavior/helpers/tutorial-contracts-v1/o10_35F5_0384/f_1B73_032A.json",
    "evidence/behavior/helpers/tutorial-contracts-v1/o10_35F5_0384/f_1B73_032E.json",
    "evidence/behavior/harnesses/tutorial-menu-20261002-e018/source-inputs/symbols.json",
    "evidence/behavior/harnesses/tutorial-menu-20261002-d12a/source-inputs/symbols.json",
    "evidence/behavior/harnesses/tutorial-menu-20261002-7043/source-inputs/symbols.json",
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extract_proc(lines: list[str], name: str) -> str:
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^" + re.escape(name) + r"\s+proc\s+far\b", line, re.I):
            start = i
            break
    if start is None:
        raise ValueError(f"canonical ASM procedure missing: {name}")
    end = None
    for i in range(start + 1, len(lines)):
        if re.match(r"^" + re.escape(name) + r"\s+endp\b", lines[i], re.I):
            end = i
            break
    if end is None:
        raise ValueError(f"canonical ASM endp missing: {name}")
    return "".join(lines[start:end + 1])


def assembly_source(canonical: str, mode: str) -> str:
    lines = canonical.splitlines(keepends=True)
    bodies = [extract_proc(lines, name) for name in PROCS]
    ext = "\r\n".join(f"\textrn\t{name}:byte" for name in QUEUE_SYMBOLS)
    if mode == "canonical_source_assumption":
        # Keep the checked-in segment scope and ASSUME spelling. The only
        # added group member, NULL16, comes from the separate test PREFIX object.
        declarations = f"_DATA segment word public 'DATA'\r\n{ext}\r\n_DATA ends\r\n"
        group = "DGROUP group _DATA\r\n"
        assume = "assume cs:MOUSE_TEXT, ds:DGROUP"
    elif mode == "reviewed_explicit_dgroup":
        # Explicitly includes the test-owned prefix segment in DGROUP while
        # retaining the original extern declaration scope and DS assumption.
        declarations = ("NULL16 segment word public 'DATA'\r\nNULL16 ends\r\n"
                        f"_DATA segment word public 'DATA'\r\n{ext}\r\n_DATA ends\r\n")
        group = "DGROUP group NULL16, _DATA\r\n"
        assume = "assume cs:MOUSE_TEXT, ds:DGROUP"
    elif mode == "data_segment_frame_contrast":
        declarations = ("NULL16 segment word public 'DATA'\r\nNULL16 ends\r\n"
                        f"_DATA segment word public 'DATA'\r\n{ext}\r\n_DATA ends\r\n")
        group = "DGROUP group NULL16, _DATA\r\n"
        assume = "assume cs:MOUSE_TEXT, ds:_DATA"
    else:
        raise ValueError(f"unknown assembly mode: {mode}")
    public = "\r\n".join(f"\tpublic\t{name}" for name in PROCS)
    proc_text = "\r\n\r\n".join(bodies)
    return ("\r\n".join((
        "; Procedures below are copied verbatim from src/root/m1B73.asm.",
        declarations.rstrip("\r\n"),
        group.rstrip("\r\n"),
        "MOUSE_TEXT segment word public 'CODE'",
        assume,
        public,
        "shift_state db 0",
        proc_text,
        "MOUSE_TEXT ends",
        "end",
        "",
    )) + "\r\n")


PREFIX_ASM = """NULL16 segment word public 'DATA'
public _queue_prefix_marker
_queue_prefix_marker dw 0A5A5h
db 14 dup (0A5h)
NULL16 ends
DGROUP group NULL16
end
"""


def c_source(mutation: str) -> str:
    capacity = 8 if mutation == "capacity_eight" else 7
    pointer = "input_queue + 1" if mutation == "buffer_pointer_plus_one" else "input_queue"
    queue_init = ("struct QueueBox near queue_box = { { 0 }, { { 1 } }, { 0 } };"
                  if mutation == "queue_initializer_nonzero"
                  else "struct QueueBox near queue_box;")
    return f'''#include <dos.h>
#include <stdio.h>

struct Rect {{
    int left;
    int top;
    int right;
    int bottom;
}};

struct Event {{
    int word[8];
}};

struct Timer {{
    struct Rect r;
    void (far *fn)();
    int ticks;
    char a;
    char b;
    char c;
    char d;
}};

struct QueueBox {{
    struct Event before;
    struct Event input_queue[7];
    struct Event after;
}};

struct DestBox {{
    struct Event before;
    struct Event event;
    struct Event after;
}};

#define input_queue (queue_box.input_queue)
#define CAPACITY {capacity}
#define CHECK(test) do {{ ++check_id; if (!(test)) {{ printf("FAIL CHECK %u count=%d ticks=%x ptr=%x q0=%x d0=%x q3=%x d3=%x\\r\\n", (unsigned)check_id, f_1B73_032A(), g_5FF2.ticks, pointer_offset((void far *)input_queue), input_queue[0].word[0], dest_box.event.word[0], input_queue[0].word[3], dest_box.event.word[3]); goto fail; }} }} while (0)

static unsigned int pointer_offset(void far *p) {{ return FP_OFF(p); }}
static unsigned int pointer_segment(void far *p) {{ return FP_SEG(p); }}

int g_5FF0 = CAPACITY;
{queue_init}
struct DestBox near dest_box;
struct Timer g_5FF2 = {{ {{ 0, 0, 0, 0xff }}, 0,
    (int)(struct Event near *){pointer}, 5, 0, 10, 0 }};
extern char g_5FF4, g_5FF6, g_5FF8, g_5FF9, g_5FFA, g_5FFE;

extern int far f_1B73_032A(void);
extern int far f_1B73_032E(struct Event far *dest);
extern void far f_1B73_030F(struct Event far *bx_es, int ax, int cx, int dx);
extern int near queue_prefix_marker;
extern int far puts(char far *text);

int main(void)
{{
    int i, j, result, check_id = 0;
    unsigned int shift_before[7], shift_after[7];
    unsigned int tick_before[7], tick_after[7];
    unsigned int far *bios_shift;
    unsigned int far *bios_tick;
    unsigned int delta, observed;

    CHECK(sizeof(struct Event) == 16);
    CHECK(sizeof(struct Timer) == 18);
    CHECK(pointer_offset((void far *)&g_5FF4) - pointer_offset((void far *)&g_5FF2) == 2);
    CHECK(pointer_offset((void far *)&g_5FF6) - pointer_offset((void far *)&g_5FF2) == 4);
    CHECK(pointer_offset((void far *)&g_5FF8) - pointer_offset((void far *)&g_5FF2) == 6);
    CHECK(pointer_offset((void far *)&g_5FF9) - pointer_offset((void far *)&g_5FF2) == 7);
    CHECK(pointer_offset((void far *)&g_5FFA) - pointer_offset((void far *)&g_5FF2) == 8);
    CHECK(pointer_offset((void far *)&g_5FFE) - pointer_offset((void far *)&g_5FF2) == 12);
    CHECK(pointer_offset((void far *)&g_5FF2.ticks) - pointer_offset((void far *)&g_5FF2) == 12);
    CHECK(pointer_offset((void far *)&g_5FF0) >=
          pointer_offset((void far *)&queue_prefix_marker) + 16);
    CHECK(g_5FF2.ticks == pointer_offset((void far *)input_queue));
    CHECK(g_5FF2.ticks != 0x91B0);
    CHECK(pointer_offset((void far *)input_queue) >=
          pointer_offset((void far *)&queue_prefix_marker) + 16);
    CHECK(f_1B73_032A() == 0);
    for (i = 0; i < 7; i++)
        for (j = 0; j < 8; j++)
            CHECK(input_queue[i].word[j] == 0);
    for (j = 0; j < 8; j++) {{
        CHECK(queue_box.before.word[j] == 0);
        CHECK(queue_box.after.word[j] == 0);
    }}

    for (j = 0; j < 8; j++) {{
        queue_box.before.word[j] = 0xC100 + j;
        queue_box.after.word[j] = 0xC200 + j;
        dest_box.before.word[j] = 0xD100 + j;
        dest_box.after.word[j] = 0xD200 + j;
    }}
    for (i = 0; i < 7; i++)
        for (j = 0; j < 8; j++)
            input_queue[i].word[j] = j == 0 ? 0xA000 + i : 0xB000 + i * 8 + j;

    bios_shift = (unsigned int far *)0x00400017L;
    bios_tick = (unsigned int far *)0x0040006cL;
    for (i = 0; i < 6; i++) {{
        shift_before[i] = *bios_shift;
        tick_before[i] = *bios_tick;
        f_1B73_030F((struct Event far *)&input_queue[i],
                    0x1100 + i, 0x2200 + i, 0x3300 + i);
        shift_after[i] = *bios_shift;
        tick_after[i] = *bios_tick;
        CHECK(f_1B73_032A() == i + 1);
    }}
    CHECK(f_1B73_032A() == 6);

    /* A seventh pending record must be dropped while the ring is full. */
    f_1B73_030F((struct Event far *)&input_queue[6], 0x1177, 0x2277, 0x3377);
    CHECK(f_1B73_032A() == 6);
    for (j = 0; j < 8; j++)
        CHECK(input_queue[6].word[j] == (j == 0 ? 0xA006 : 0xB000 + 6 * 8 + j));
    for (j = 0; j < 8; j++) {{
        CHECK(queue_box.before.word[j] == 0xC100 + j);
        CHECK(queue_box.after.word[j] == 0xC200 + j);
    }}

    /* Empty dequeue returns -1 and leaves all sixteen destination bytes alone. */
    for (j = 0; j < 8; j++)
        dest_box.event.word[j] = 0xE000 + j;
    result = f_1B73_032E((struct Event far *)&dest_box.event);
    CHECK(result == 5);
    CHECK(dest_box.event.word[0] == 0xA000);
    CHECK(dest_box.event.word[3] == 0x1100);
    CHECK(dest_box.event.word[4] == 0x2200);
    CHECK(dest_box.event.word[5] == 0x3300);
    CHECK(dest_box.event.word[6] == pointer_offset((void far *)&input_queue[0]));
    CHECK(dest_box.event.word[7] == pointer_segment((void far *)&input_queue[0]));
    CHECK(dest_box.event.word[1] == shift_before[0] || dest_box.event.word[1] == shift_after[0]);
    delta = (tick_after[0] - tick_before[0]) & 0xffff;
    observed = (dest_box.event.word[2] - tick_before[0]) & 0xffff;
    CHECK(delta <= 8 && observed <= delta);
    for (j = 0; j < 8; j++) {{
        CHECK(dest_box.before.word[j] == 0xD100 + j);
        CHECK(dest_box.after.word[j] == 0xD200 + j);
    }}

    /* With the read index advanced, the next enqueue wraps through slot six. */
    shift_before[6] = *bios_shift;
    tick_before[6] = *bios_tick;
    f_1B73_030F((struct Event far *)&input_queue[6], 0x1166, 0x2266, 0x3366);
    shift_after[6] = *bios_shift;
    tick_after[6] = *bios_tick;
    CHECK(f_1B73_032A() == 6);
    CHECK(input_queue[6].word[0] == 0xA006);
    CHECK(input_queue[6].word[3] == 0x1166);
    CHECK(input_queue[6].word[4] == 0x2266);
    CHECK(input_queue[6].word[5] == 0x3366);
    CHECK(input_queue[6].word[6] == pointer_offset((void far *)&input_queue[6]));
    CHECK(input_queue[6].word[7] == pointer_segment((void far *)&input_queue[6]));

    for (i = 1; i < 6; i++) {{
        result = f_1B73_032E((struct Event far *)&dest_box.event);
        CHECK(result == 6 - i);
        CHECK(dest_box.event.word[0] == 0xA000 + i);
        CHECK(dest_box.event.word[3] == 0x1100 + i);
        CHECK(dest_box.event.word[4] == 0x2200 + i);
        CHECK(dest_box.event.word[5] == 0x3300 + i);
        CHECK(dest_box.event.word[6] == pointer_offset((void far *)&input_queue[i]));
        CHECK(dest_box.event.word[7] == pointer_segment((void far *)&input_queue[i]));
        CHECK(dest_box.event.word[1] == shift_before[i] || dest_box.event.word[1] == shift_after[i]);
        delta = (tick_after[i] - tick_before[i]) & 0xffff;
        observed = (dest_box.event.word[2] - tick_before[i]) & 0xffff;
        CHECK(delta <= 8 && observed <= delta);
    }}
    result = f_1B73_032E((struct Event far *)&dest_box.event);
    CHECK(result == 0);
    CHECK(dest_box.event.word[0] == 0xA006);
    CHECK(dest_box.event.word[3] == 0x1166);
    CHECK(dest_box.event.word[4] == 0x2266);
    CHECK(dest_box.event.word[5] == 0x3366);
    CHECK(dest_box.event.word[6] == pointer_offset((void far *)&input_queue[6]));
    CHECK(dest_box.event.word[7] == pointer_segment((void far *)&input_queue[6]));
    CHECK(dest_box.event.word[1] == shift_before[6] || dest_box.event.word[1] == shift_after[6]);
    delta = (tick_after[6] - tick_before[6]) & 0xffff;
    observed = (dest_box.event.word[2] - tick_before[6]) & 0xffff;
    CHECK(delta <= 8 && observed <= delta);
    CHECK(f_1B73_032A() == 0);

    /* A second empty read must preserve every destination word. */
    for (j = 0; j < 8; j++)
        dest_box.event.word[j] = 0xE100 + j;
    result = f_1B73_032E((struct Event far *)&dest_box.event);
    CHECK(result == -1);
    for (j = 0; j < 8; j++)
        CHECK(dest_box.event.word[j] == 0xE100 + j);
    for (j = 0; j < 8; j++) {{
        CHECK(queue_box.before.word[j] == 0xC100 + j);
        CHECK(queue_box.after.word[j] == 0xC200 + j);
        CHECK(dest_box.before.word[j] == 0xD100 + j);
        CHECK(dest_box.after.word[j] == 0xD200 + j);
    }}
    puts("PASS");
    return 0;
fail:
    puts("FAIL");
    return 1;
}}
'''


def fixup_rows(obj: bytes) -> list[dict]:
    module = OmfReader().read(obj, "QUEUE")
    return [
        {key: row.get(key) for key in (
            "segment", "offset", "width", "loc", "target_kind", "target",
            "displacement", "frame_kind", "frame", "encoded_addend")}
        for row in module.linker_fixups
        if row.get("target") in QUEUE_SYMBOLS
    ]


def c_fixup_rows(obj: bytes) -> list[dict]:
    module = OmfReader(communals=True).read(obj, "MAIN")
    return [
        {key: row.get(key) for key in (
            "segment", "offset", "width", "loc", "target_kind", "target",
            "displacement", "frame_kind", "frame", "encoded_addend")}
        for row in module.linker_fixups
        if "g_5ff" in str(row.get("target", "")).lower()
    ]


def run_case(out: Path, linker_name: str, linker: dict, linker_dir: Path,
             runner: dict, prefix_obj: bytes, main_obj: bytes, queue_obj: bytes,
             runtimes: list[dict], expected: str, name: str) -> dict:
    case_dir = out / linker_name / name
    case_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (case_dir / filename).unlink(missing_ok=True)
    for filename, obj in (("PREFIX", prefix_obj), ("MAIN", main_obj), ("QUEUE", queue_obj)):
        (case_dir / (filename + ".OBJ")).write_bytes(obj)
    for row in runtimes:
        shutil.copyfile(row["path"], case_dir / Path(row["path"]).name.upper())
    (case_dir / "PROBE.LNK").write_bytes((
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE PREFIX, MAIN, QUEUE\r\n"
        "DEFINE _g_5FF4 = _g_5FF2 + 2\r\n"
        "DEFINE _g_5FF6 = _g_5FF2 + 4\r\n"
        "DEFINE _g_5FF8 = _g_5FF2 + 6\r\n"
        "DEFINE _g_5FF9 = _g_5FF2 + 7\r\n"
        "DEFINE _g_5FFA = _g_5FF2 + 8\r\n"
        "DEFINE _g_5FFE = _g_5FF2 + 0Ch\r\n").encode("ascii"))
    (case_dir / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (case_dir / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config.append("[" + section + "]")
        config += [f"{key}={value}" for key, value in settings.items()]
    config += ["[autoexec]", f'mount c "{case_dir}"', f'mount d "{linker_dir}" -ro',
               "c:", "call RUN.BAT", "exit"]
    conf = case_dir / "dosbox.conf"
    conf.write_text("\n".join(config) + "\n")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    emu = subprocess.run(
        [runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
        cwd=case_dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    run_log = case_dir / "RUN.LOG"
    output = run_log.read_text(encoding="latin1").strip() if run_log.exists() else "NO_RUN_LOG"
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if lines == ["PASS"]:
        actual = "PASS"
    elif len(lines) >= 2 and lines[0].startswith("FAIL CHECK ") and lines[-1] == "FAIL":
        actual = "FAIL"
    else:
        actual = output or "EMPTY_RUN_LOG"
    exe_exists = (case_dir / "PROBE.EXE").exists()
    return {
        "linker": linker_name,
        "case": name,
        "expected": expected,
        "actual": actual,
        "diagnostic": lines[0] if lines and lines[0].startswith("FAIL CHECK ") else None,
        "exe_built": exe_exists,
        "emulator_exit": emu.returncode,
        "passed": actual == expected and exe_exists and emu.returncode == 0,
        "main_object_sha256": sha(main_obj),
        "queue_object_sha256": sha(queue_obj),
        "prefix_object_sha256": sha(prefix_obj),
        "artifact_hashes": {
            filename: {"sha256": sha((case_dir / filename).read_bytes()),
                       "size": (case_dir / filename).stat().st_size}
            for filename in ("PROBE.EXE", "PROBE.MAP", "PROBE.LNK", "LINK.LOG", "RUN.LOG")
            if (case_dir / filename).is_file()
        },
    }


def main() -> int:
    out = ROOT / "build/workers/dos_queue_runtime"
    out.mkdir(parents=True, exist_ok=True)
    denied = dos.install_input_guard()
    tc = compiler.toolchain()
    inputs = [dos.pin(Path(__file__))[1], dos.pin(SOURCE)[1],
              dos.pin(ROOT / "src/root/m1FD2.c")[1],
              dos.pin(ROOT / "layout/toolchain.json")[1],
              dos.pin(ROOT / "layout/manifest.json")[1]]
    inputs.extend([dos.pin(ROOT / rel)[1] for rel in AUDIT_INPUTS])
    profiles = {}
    for profile_name in ("msc600ax", "masm510"):
        profile = compiler.verify_profile(profile_name)
        profiles[profile_name] = profile
        inputs.extend([dos.pin(Path(profile["directory"]) / rel, digest)[1]
                       for rel, digest in profile["files"].items()])
    runner = tc["runners"]["dosbox-x"]
    inputs.append(dos.pin(Path(runner["path"]), runner["sha256"])[1])
    inputs.append(dos.pin(Path(tc["runner"]["path"]), tc["runner"]["sha256"])[1])
    runtimes = list(json.loads((ROOT / "layout/manifest.json").read_bytes())["runtime"]["libraries"].values())
    inputs.extend([dos.pin(Path(row["path"]), row["sha256"])[1] for row in runtimes])

    canonical_raw = SOURCE.read_text(encoding="latin1")
    if not re.search(r"(?im)^\s*assume\s+cs\s*:\s*MOUSE_TEXT\s*,\s*ds\s*:\s*DGROUP", canonical_raw):
        raise ValueError("canonical m1B73 source ASSUME changed; re-review the fixture")
    prefix_text = PREFIX_ASM.replace("\n", "\r\n")
    prefix_path = out / "PREFIX.asm"
    prefix_path.write_bytes(prefix_text.encode("ascii"))
    prefix_run = compiler.assemble(prefix_text, "masm510", ["/Mx"], basename="PREFIX")
    if not prefix_run.ok:
        raise ValueError(prefix_run.log)
    prefix_obj = prefix_run.obj

    c_objects = {}
    c_sources = {}
    for mutation, basename in (("positive", "MAIN"),
                               ("queue_initializer_nonzero", "NONZERO"),
                               ("buffer_pointer_plus_one", "PTRONE"),
                               ("capacity_eight", "CAP8")):
        source = c_source(mutation)
        c_sources[mutation] = source
        (out / (basename + ".c")).write_bytes(source.replace("\n", "\r\n").encode("ascii"))
        result = compiler.compile_c(source, "msc600ax", ["/AL", "/Os", "/Zi"], basename="MAIN")
        if not result.ok:
            raise ValueError(f"{mutation}: {result.log}")
        c_objects[mutation] = result.obj

    queue_objects = {}
    queue_fixups = {}
    for mode in ("canonical_source_assumption", "reviewed_explicit_dgroup",
                 "data_segment_frame_contrast"):
        source = assembly_source(canonical_raw, mode)
        (out / (mode + ".asm")).write_bytes(source.encode("ascii"))
        result = compiler.assemble(source, "masm510", ["/Mx"], basename="QUEUE")
        if not result.ok:
            raise ValueError(f"{mode}: {result.log}")
        queue_objects[mode] = result.obj
        queue_fixups[mode] = fixup_rows(result.obj)

    manifest = json.loads((ROOT / "layout/manifest.json").read_bytes())
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        inputs.extend([dos.pin(Path(linker["directory"]) / rel, digest)[1]
                       for rel, digest in linker["files"].items()])
        linker_dir = compiler.pinned_tree(linker)
        modes = (
            ("canonical_source_positive", "canonical_source_assumption", "positive", "PASS"),
            ("reviewed_dgroup_positive", "reviewed_explicit_dgroup", "positive", "PASS"),
            ("data_segment_frame_contrast", "data_segment_frame_contrast", "positive", "FAIL"),
            ("queue_initializer_nonzero", "reviewed_explicit_dgroup", "queue_initializer_nonzero", "FAIL"),
            ("buffer_pointer_plus_one", "reviewed_explicit_dgroup", "buffer_pointer_plus_one", "FAIL"),
            ("capacity_eight", "reviewed_explicit_dgroup", "capacity_eight", "FAIL"),
        )
        for name, asm_mode, mutation, expected in modes:
            row = run_case(out, linker_name, linker, linker_dir, runner, prefix_obj,
                           c_objects[mutation], queue_objects[asm_mode], runtime_rows,
                           expected, name)
            row["frame_mode"] = asm_mode
            row["queue_fixups"] = queue_fixups[asm_mode]
            row["main_queue_fixups"] = c_fixup_rows(c_objects[mutation])
            expected_frame = "_DATA" if asm_mode == "data_segment_frame_contrast" else "DGROUP"
            actual_frames = sorted({fixup.get("frame") for fixup in queue_fixups[asm_mode]})
            row["expected_queue_fixup_frame"] = expected_frame
            row["actual_queue_fixup_frames"] = actual_frames
            row["fixup_frame_check"] = bool(queue_fixups[asm_mode]) and actual_frames == [expected_frame]
            row["passed"] = row["passed"] and row["fixup_frame_check"]
            cases.append(row)
            print(linker_name, name, row["actual"], "frames=" + ",".join(actual_frames), flush=True)

    positives = [r for r in cases if r["expected"] == "PASS"]
    contrasts = [r for r in cases if r["expected"] == "FAIL"]
    report = {
        "schema": "simant-dos-queue-runtime-probe-v1",
        "contract": {"ring_slots": 7, "stride": 16, "copy_bytes": 16,
                     "usable_capacity": 6},
        "inputs": inputs,
        "denied_oracle_reads": denied,
        "canonical_source_assumption": "assume cs:MOUSE_TEXT, ds:DGROUP",
        "reference_audit_scope": {
            "canonical_modules": ["root:1B73 src/root/m1B73.asm", "root:1FD2 src/root/m1FD2.c"],
            "canonical_tree_result": "In src/, only these two canonical source files contain the requested g_5FF* names or the 0x91B0 literal.",
            "behavior_sources": "Two TickCount-source.asm copies match canonical m1B73.asm by SHA-256; selected tutorial contract excerpts cite 032A/032E; three selected symbol maps list the identifiers as addresses.",
            "selected_behavior_has_91b0_literal": False,
        },
        "reference_inventory": {
            "g_5FF0": "C initialized to 7 at m1FD2.c:50; ASM reads capacity at m1B73.asm:598,635; no writes found.",
            "g_5FF2": "Timer base; ASM count reads at m1B73.asm:581,591; writes at :594 (dequeue decrement), :643 (enqueue increment); C initializer at m1FD2.c:51 sets Rect.left to 0.",
            "g_5FF4": "Timer+2; tail read at m1B73.asm:632, write at :641.",
            "g_5FF6": "Timer+4; head reads at m1B73.asm:595,639, write at :604.",
            "g_5FF8": "Timer+6; byte write at m1B73.asm:1530.",
            "g_5FF9": "Timer+7; byte read at m1B73.asm:773, byte write at :1534.",
            "g_5FFA": "Timer+8; word indirect call at m1B73.asm:775, word write at :1532.",
            "g_5FFE": "Timer+12; queue-base reads at m1B73.asm:606,644; no direct writes found. C literal 0x91B0 initializes Timer.ticks at m1FD2.c:51.",
            "canonical_buffer_declaration": "No canonical C Event[7] buffer declaration was found in src/; m1FD2.c:51 initializes the Timer.ticks word from literal 0x91B0. The separate QUEUE_DATA family is declared in m1B73.asm:137-152.",
            "queue_mechanics": "Four index doublings at m1B73.asm:607-610 and :645-648 yield 16-byte stride; dequeue copies 8 words at :613-614; enqueue writes words at :651-655 and :667-668. Capacity 7 with head/tail sentinel leaves six usable records.",
            "separate_queue_family": "m1B73.asm:137-152 declares QUEUE_DATA with Queue0 and _fd_5071_* far data; m1B73.asm:122 comments on its separate 18-byte entries, and its callers use _g_5484/_fd_5071_* rather than g_5FF*. Manifest root:1B73 places QUEUE_DATA at 2016 bytes and _DATA at 4519 bytes.",
        },
        "extracted_procedures": {name: sha(extract_proc(canonical_raw.splitlines(keepends=True), name).encode("latin1"))
                                  for name in PROCS},
        "fixture": {
            "timer_descriptor": "struct Timer { struct Rect r; void (far *fn)(); int ticks; char a,b,c,d; }",
            "buffer_declaration": "struct QueueBox near queue_box; struct Event input_queue[7] member;",
            "base_initializer": "(int)(struct Event near *)input_queue",
            "base_initializer_check": "runtime verifies g_5FF2.ticks equals the resolved near input_queue offset and differs from historical literal 0x91B0",
            "overlay_aliases": {"g_5FF4": "RTLink DEFINE _g_5FF2+2",
                                "g_5FF6": "RTLink DEFINE _g_5FF2+4",
                                "g_5FF8": "RTLink DEFINE _g_5FF2+6",
                                "g_5FF9": "RTLink DEFINE _g_5FF2+7",
                                "g_5FFA": "RTLink DEFINE _g_5FF2+8",
                                "g_5FFE": "RTLink DEFINE _g_5FF2+0Ch"},
            "prefix": "NULL16 is the first test-owned DGROUP segment before _DATA and occupies 16 bytes of 0xA5; a runtime offset check requires the _DATA g_5FF0 symbol at least 16 bytes after its marker. Runtime libraries may precede both with their NULL segment.",
            "procedure_return_contract": "f_1B73_032E returns AX as remaining count, or -1 when empty.",
            "ring_slots": 7,
            "usable_capacity": 6,
            "stride_bytes": 16,
            "copy_bytes": 16,
            "startup_zeroing": "all 7 queue records are checked before the fixture writes any sentinels.",
            "runtime_assertions": ["FIFO payload order", "six accepted/seventh dropped", "slot 6 reuse after read-index advance",
                                   "all eight 16-bit words copied", "word 0 sentinel preserved", "queue and destination guards",
                                   "empty returns -1 without changing destination", "BIOS keyboard-state and tick words bracketed by BDA reads"],
            "negative_controls": ["queue initializer nonzero", "buffer pointer plus one Event", "capacity 8"],
        },
        "assembly_modes": {mode: {"queue_fixups": rows, "all_frames": sorted({row.get("frame") for row in rows})}
                            for mode, rows in queue_fixups.items()},
        "cases": cases,
        "all_required_checks_pass": (not denied and all(r["passed"] for r in positives + contrasts)),
        "scope": "Test-owned execution and frame probe for the four exact m1B73 procedures and a C-owned near buffer. Startup zeroing here is only a fixture observation; this report does not establish original game executable startup behavior, historical object ownership, queue data identity, or a game-link contract.",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
