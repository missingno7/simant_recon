#!/usr/bin/env python3
"""Compile and execute current generated C consumers of the two ASM DATA owners.

This is a consumer-boundary test, not a DOS differential or production admission.
Outputs are immutable once written; pass a new --out directory for a new run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import re

ROOT = Path(__file__).resolve().parents[4]
PROVIDER_C = ROOT / "portable/whole_program/state/asm_display_data_v1.c"
PROVIDER_H = ROOT / "portable/whole_program/state/asm_display_data_v1.h"
GEN = ROOT / "build/workers/whole_program/generated"
CONSUMERS = {
    "root_m1CE2.c": GEN / "root_m1CE2.c",
    "root_m0250.c": GEN / "root_m0250.c",
}

HARNESS = r'''#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "portable/whole_program/state/asm_display_data_v1.h"

typedef char ** Handle;
struct Rect { int16_t left, top, right, bottom; };
extern char g_21A4;
extern int16_t (*g_9140)(int16_t, int16_t, int16_t, int16_t);
extern void (*g_9148)(int16_t, int16_t, int16_t, int16_t, char *);
extern Handle native_game_fd_50F6_10EE;
extern int16_t fd_50F6_1102;
extern uint8_t g_94E4;
extern void *_fmemcpy(void *, const void *, uint16_t);
void o00_31AD_1A8F(int16_t row, int16_t col);

int16_t (*g_9140)(int16_t, int16_t, int16_t, int16_t);
void (*g_9148)(int16_t, int16_t, int16_t, int16_t, char *);
Handle native_game_fd_50F6_10EE;
int16_t fd_50F6_1102;
uint8_t g_94E4;
static char save_block[512];
char *f_171C_2190(int16_t size, char *name) {
    (void)size; (void)name; return save_block;
}
/*__ACTUAL_GENERATED_CONSUMER_BODIES__*/

static char *tiledata;
static char saved_pixels[0x100];
static int saw_size_flag, saw_save_flag;

static int16_t size_cb(int16_t l, int16_t t, int16_t r, int16_t b) {
    (void)l; (void)t; (void)r; (void)b;
    saw_size_flag = sim_asm_g21a4_read_word() == 0xA501;
    return 0x100;
}
static void save_cb(int16_t l, int16_t t, int16_t r, int16_t b, char *p) {
    (void)l; (void)t; (void)r; (void)b; (void)p;
    saw_save_flag = sim_asm_g21a4_read_word() == 0xA501;
}
void *_fmemcpy(void *d, const void *s, uint16_t n) { return memcpy(d, s, n); }
void o00_31AD_1A8F(int16_t row, int16_t col) { (void)row; (void)col; }

int main(void) {
    struct Rect rect = { 5, 7, 20, 21 };
    char *save_result;
    unsigned i;
    for (i = 0; i < sizeof(sim_asm_g3d20.bytes); ++i)
        if (sim_asm_g3d20.bytes[i] != 0) return 10;
    if (sim_asm_g21a4_read_word() != 0) return 11;

    /* The actual generated C GSaveRect body sees the low-byte source view;
       ASM PUSH/POP WORD PTR view retains the neighboring high byte. */
    sim_asm_g21a4_write_word(0xA500);
    g_9140 = size_cb; g_9148 = save_cb;
    save_result = GSaveRect(&rect);
    if (save_result == 0 || !saw_size_flag || !saw_save_flag) return 12;
    if (sim_asm_g21a4_read_word() != 0xA500) return 13;

    /* Exact S02/root source extent: the row buffer accepts the largest 0x48
       byte mode-2 write and the 0x20 byte mode-3 write without tail damage. */
    {
        static char input[256 * 0x48];
        char *input_ptr = input;
        for (i = 0; i < sizeof(input); ++i) input[i] = (char)((i * 37u + 11u) & 0xffu);
        native_game_fd_50F6_10EE = &input_ptr;
        memset(sim_asm_g3d20.bytes, 0xCD, sizeof(sim_asm_g3d20.bytes));
        fd_50F6_1102 = 2; g_94E4 = 255;
        f_0250_0B86();
        if (memcmp(sim_asm_g3d20.bytes, input + 255u * 0x48u, 0x48) != 0) return 20;
        for (i = 0x48; i < 128; ++i) if (sim_asm_g3d20.bytes[i] != 0xCD) return 21;
        memset(sim_asm_g3d20.bytes, 0xCD, sizeof(sim_asm_g3d20.bytes));
        fd_50F6_1102 = 3; g_94E4 = 255;
        f_0250_0B86();
        if (memcmp(sim_asm_g3d20.bytes, input + (255u << 5), 0x20) != 0) return 22;
        for (i = 0x20; i < 128; ++i) if (sim_asm_g3d20.bytes[i] != 0xCD) return 23;
    }

    /* Positive word-view and byte-view controls share precisely one object. */
    sim_asm_g21a4_write_word(0x80FF);
    if ((uint8_t)g_21A4 != 0xFF || sim_asm_g21a4_read_word() != 0x80FF) return 30;
    g_21A4 = 0x7F;
    if (sim_asm_g21a4_read_word() != 0x807F) return 31;
    return 0;
}
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=False)


def extract_definition(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", text)
    if not match:
        raise SystemExit(f"could not find function definition {name} in {path}")
    brace = text.find("{", match.start())
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                line_start = text.rfind("\n", 0, match.start()) + 1
                return text[line_start:i + 1]
    raise SystemExit(f"unterminated function definition {name} in {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--gcc", default=shutil.which("gcc") or "gcc")
    args = ap.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    gcc = Path(args.gcc).resolve()
    if not gcc.is_file():
        raise SystemExit(f"compiler not found: {gcc}")

    inputs = [PROVIDER_C, PROVIDER_H, *CONSUMERS.values(),
              Path(__file__).resolve(), ROOT / "src/S02/m3126.asm", ROOT / "src/root/m1B4E.asm",
              ROOT / "src/root/m1B73.asm",
              ROOT / "src/root/m1CE2.c", ROOT / "src/root/m0250.c",
              ROOT / "layout/manifest.json", ROOT / "layout/symbols.json"]
    for p in inputs:
        if not p.is_file():
            raise SystemExit(f"missing pinned input: {p}")
    pin_before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    version = run([str(gcc), "--version"], cwd=ROOT)
    if version.returncode:
        raise SystemExit(version.stdout)
    gcc_sha_before = sha(gcc)

    bodies = [extract_definition(CONSUMERS["root_m1CE2.c"], "GSaveRect"),
              extract_definition(CONSUMERS["root_m0250.c"], "f_0250_0B86")]
    harness_text = HARNESS.replace("/*__ACTUAL_GENERATED_CONSUMER_BODIES__*/",
                                   "\n\n".join(bodies), 1)
    harness = out / "consumer_test.c"
    harness.write_text(harness_text, encoding="utf-8", newline="\n")
    flags = ["-std=c11", "-DSIMANT_NATIVE_LITTLE_ENDIAN=1", "-ffunction-sections",
             "-fdata-sections", "-I", str(ROOT)]
    cmds = [
        [str(gcc), *flags, "-c", str(PROVIDER_C), "-o", str(out / "provider.o")],
        [str(gcc), *flags, "-c", str(harness), "-o", str(out / "consumer_test.o")],
        [str(gcc), str(out / "consumer_test.o"), str(out / "provider.o"),
         "-o", str(out / "consumer_test.exe")],
    ]
    command_log = []
    for cmd in cmds:
        result = run(cmd, cwd=ROOT)
        command_log.append({"argv": cmd, "returncode": result.returncode, "output": result.stdout})
        if result.returncode:
            (out / "commands.json").write_text(json.dumps(command_log, indent=2), encoding="utf-8")
            raise SystemExit(f"command failed ({result.returncode}): {cmd}\n{result.stdout}")

    exe = out / "consumer_test.exe"
    execution = run([str(exe)], cwd=ROOT)

    negative_controls = []
    mutants = [
        ("lost-21A4-active-byte", bodies[0].replace("g_21A4 = 1;", "g_21A4 = 0;", 1), bodies[1]),
        ("shortened-3D20-mode2-copy", bodies[0], bodies[1].replace(
            "g_94E4 * 0x48, 0x48", "g_94E4 * 0x48, 0x47", 1)),
    ]
    for index, (name, body21, body3d) in enumerate(mutants):
        if body21 == bodies[0] and body3d == bodies[1]:
            raise SystemExit(f"negative mutant {name} did not alter its source body")
        mutant_source = out / f"negative_{index}.c"
        mutant_obj = out / f"negative_{index}.o"
        mutant_exe = out / f"negative_{index}.exe"
        mutant_source.write_text(HARNESS.replace(
            "/*__ACTUAL_GENERATED_CONSUMER_BODIES__*/", body21 + "\n\n" + body3d, 1),
            encoding="utf-8", newline="\n")
        compile_mutant = run([str(gcc), *flags, "-c", str(mutant_source), "-o", str(mutant_obj)], cwd=ROOT)
        link_mutant = run([str(gcc), str(mutant_obj), str(out / "provider.o"), "-o", str(mutant_exe)], cwd=ROOT) if compile_mutant.returncode == 0 else compile_mutant
        mutant_execution = run([str(mutant_exe)], cwd=ROOT) if link_mutant.returncode == 0 else link_mutant
        negative_controls.append({"name": name, "compile_returncode": compile_mutant.returncode,
                                  "link_returncode": link_mutant.returncode,
                                  "execution_returncode": mutant_execution.returncode,
                                  "source_sha256": sha(mutant_source),
                                  "executable_sha256": sha(mutant_exe) if mutant_exe.is_file() else None,
                                  "detected": compile_mutant.returncode == 0 and link_mutant.returncode == 0 and mutant_execution.returncode != 0})
    pin_after = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    gcc_sha_after = sha(gcc)
    report = {
        "schema": "asm-display-data-owner-consumer-v1",
        "claim": "SOURCE_CONSUMER_CONTROL_ONLY; no DOS differential, whole-program admission, or runtime lifecycle claim",
        "source_anchors": {
            "g_21A4": {
                "definition": "src/S02/m3126.asm _DATA starts DGROUP:219C; four labeled dw 0 values occupy 219C..21A3; following unlabeled dw 0 occupies 21A4..21A5",
                "exact_extent": 2, "initial_bytes_hex": "0000",
                "consumer_views": ["root/m1CE2.c declares char near g_21A4 and writes its low byte",
                                   "root/m1B73.asm extrn byte but performs PUSH/MOV/POP WORD PTR at g_21A4"]
            },
            "g_3D20": {
                "definition": "src/root/m1B4E.asm _g_3D20 db 128 dup (0)",
                "exact_extent": 128, "initial_bytes_hex": "00" * 128,
                "consumer_views": ["root/m0250.c f_0250_0B86 copies 0x48 or 0x20 bytes into the buffer",
                                   "S00/S01/S03 display-driver ASM consumers declare extrn byte and use its address"]
            }
        },
        "input_sha256_before": pin_before,
        "input_sha256_after": pin_after,
        "inputs_stable": pin_before == pin_after,
        "compiler": {"path": str(gcc), "sha256_before": gcc_sha_before,
                     "sha256_after": gcc_sha_after, "version": version.stdout},
        "actual_generated_consumers_compiled": ["GSaveRect body extracted verbatim from root_m1CE2.c", "f_0250_0B86 body extracted verbatim from root_m0250.c"],
        "extracted_consumer_body_sha256": {
            "GSaveRect": hashlib.sha256(bodies[0].encode()).hexdigest(),
            "f_0250_0B86": hashlib.sha256(bodies[1].encode()).hexdigest()
        },
        "harness_source_sha256": sha(harness),
        "controls": {
            "initializer_zeroes": True,
            "word_and_low_byte_are_one_two_byte_owner": True,
            "g21a4_high_byte_survives_real_generated_C_byte_stores": True,
            "g3d20_mode2_0x48_copy_and_unwritten_tail": True,
            "g3d20_mode3_0x20_copy_and_unwritten_tail": True
        },
        "negative_controls": negative_controls,
        "execution": {"returncode": execution.returncode, "output": execution.stdout},
        "compile_commands": command_log,
        "passed": execution.returncode == 0 and all(x["detected"] for x in negative_controls) and pin_before == pin_after and gcc_sha_before == gcc_sha_after,
        "output_sha256": {p.name: sha(p) for p in [exe, out / "provider.o", out / "consumer_test.o"]},
        "all_negative_executables_sha256": {f"negative_{i}.exe": sha(out / f"negative_{i}.exe")
                                             for i in range(len(negative_controls))}
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "output": str(out / "report.json"),
                      "execution_returncode": execution.returncode}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
