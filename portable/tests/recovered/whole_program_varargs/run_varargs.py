#!/usr/bin/env python3
"""Standalone native controls and source-lowering packet for DOS varargs."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from portable.whole_program.conversions.varargs import adapt
from portable.whole_program.conversions.varargs import _functions as variadic_functions
from portable.tools.whole_program import convert_words
from portable.tools.recover_source import load_function_aliases

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scan_format_literals() -> dict:
    literal_re = re.compile(r'"(?:\\.|[^"\\])*"')
    spec_re = re.compile(r"%(?:[-+#0 ]*)(?:\*|[0-9]*)(?:\.(?:\*|[0-9]*))?l?[diuoxXscp%]")
    counts: dict[str, int] = {}
    spec_counts: dict[str, int] = {}
    unsupported: list[dict[str, str]] = []
    dynamic_formats: list[dict[str, str]] = []
    candidates = 0
    for path in sorted((ROOT / "src").rglob("*.c")):
        text = path.read_text(encoding="latin-1")
        for literal_match in literal_re.finditer(text):
            literal = literal_match.group(0)
            if "%" not in literal:
                continue
            candidates += 1
            pos = 0
            while pos < len(literal):
                if literal[pos] != "%":
                    pos += 1
                    continue
                match = spec_re.match(literal, pos)
                if not match:
                    unsupported.append({"path": path.relative_to(ROOT).as_posix(),
                                        "literal": literal, "offset": str(pos)})
                    pos += 1
                    continue
                token = match.group(0)
                conv = token[-1]
                counts[conv] = counts.get(conv, 0) + 1
                spec_counts[token] = spec_counts.get(token, 0) + 1
                pos = match.end()
        for call in re.finditer(r"\b(printf|sprintf|vsprintf)\s*\(", text):
            line_start = text.rfind("\n", 0, call.start()) + 1
            line_end = text.find("\n", call.end())
            if line_end < 0: line_end = len(text)
            declaration_line = text[line_start:line_end]
            if "extern" in declaration_line:
                continue
            opening = call.end() - 1
            depth = 0
            in_string = False
            escaped = False
            parts = []
            part_start = opening + 1
            close = None
            for index in range(opening + 1, len(text)):
                ch = text[index]
                if in_string:
                    if escaped: escaped = False
                    elif ch == "\\": escaped = True
                    elif ch == '"': in_string = False
                    continue
                if ch == '"': in_string = True; continue
                if ch == "(": depth += 1
                elif ch == ")":
                    if depth == 0:
                        parts.append(text[part_start:index].strip()); close = index; break
                    depth -= 1
                elif ch == "," and depth == 0:
                    parts.append(text[part_start:index].strip()); part_start = index + 1
            if close is None:
                continue
            format_index = 0 if call.group(1) == "printf" else 1
            if len(parts) <= format_index:
                continue
            format_expr = parts[format_index]
            if not format_expr.startswith('"') and not format_expr.startswith("'"):
                dynamic_formats.append({"path": path.relative_to(ROOT).as_posix(),
                                        "function": call.group(1), "expression": format_expr[:120]})
    return {"literal_candidates": candidates, "conversion_counts": dict(sorted(counts.items())),
            "specifier_counts": dict(sorted(spec_counts.items())),
            "unparsed_percent_candidates": unsupported,
            "dynamic_format_expressions": dynamic_formats,
            "scope": "all source C string literals; candidates include non-format strings and are not all proven call arguments"}


def resolve_dynamic_noarg_formats() -> list[dict]:
    """Resolve the nonliteral printf formats through their actual source owners."""
    registry_path = ROOT / "portable/research/whole_program_unprovided_owners_v2.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    aliases = {row["name"]: row for row in registry["source_expression_aliases"]
               if row.get("name") in {"fd_55B3_1CD8", "fd_55B3_1CDC"}}
    if set(aliases) != {"fd_55B3_1CD8", "fd_55B3_1CDC"}:
        raise AssertionError("expected both initialized pointer aliases in the owner registry")
    owner_path = ROOT / "src/root/m15F8.c"
    owner_source = owner_path.read_text(encoding="latin-1")
    owner_sha = sha(owner_path.read_bytes())
    array = re.search(r"char\s+far\s*\*\s*fd_55B3_1CD4\s*\[\]\s*=\s*\{(.*?)\};",
                      owner_source, re.DOTALL)
    if not array:
        raise AssertionError("fd_55B3_1CD4 source initializer not found")
    values = [ast.literal_eval(match.group(0)) for match in re.finditer(r'"(?:\\.|[^"\\])*"', array.group(1))]
    resolved = []
    for name, expected_index in (("fd_55B3_1CD8", 1), ("fd_55B3_1CDC", 2)):
        row = aliases[name]
        if (row["owner"] != "fd_55B3_1CD4" or row["element_index"] != expected_index or
                row["provider_public"]["source_sha256"] != owner_sha):
            raise AssertionError(f"source alias metadata disagrees for {name}")
        if len(values) != row["initializer_count"]:
            raise AssertionError("fd_55B3_1CD4 initializer count disagrees with alias evidence")
        text = values[expected_index]
        if "%" in text:
            raise AssertionError(f"no-argument printf template unexpectedly contains percent syntax: {name}")
        resolved.append({"name": name, "alias_expression": row["expression"],
                         "source": row["source"], "source_sha256": owner_sha,
                         "text": text, "percent_conversions": 0,
                         "basis": "source_expression_aliases owner/element index plus parsed C initializer; no resource bytes inferred"})

    msg_path = ROOT / "src/root/m205F.c"
    msg_source = msg_path.read_text(encoding="latin-1")
    msg_match = re.search(r'\bmsg\s*=\s*("(?:\\.|[^"\\])*")\s*;', msg_source)
    if not msg_match or not re.search(r"if\s*\(mode\s*==\s*-1\)\s*\{\s*printf\(msg\);", msg_source):
        raise AssertionError("printf(msg) source assignment/guard changed")
    msg = ast.literal_eval(msg_match.group(1))
    if "%" in msg:
        raise AssertionError("printf(msg) string assigned to the no-argument route has percent syntax")
    resolved.append({"name": "msg", "source": "src/root/m205F.c", "source_sha256": sha(msg_path.read_bytes()),
                     "text": msg, "percent_conversions": 0,
                     "basis": "literal assigned to msg in adapter==1 case and passed to printf(msg) under mode==-1",
                     "source_boundary": "other adapter values can leave msg uninitialized before the source call; this packet validates only the initialized source assignment, and does not mask that source path"})
    return resolved


def run() -> dict:
    sources = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "src").rglob("*.c"))
    stack_sources = {
        "src/root/m1C62.c": 1, "src/root/m1CE2.c": 2, "src/root/m1FD2.c": 1,
        "src/root/m208F.c": 2, "src/root/m22BF.c": 5, "src/root/m171C.c": 1,
    }
    ledgers = []
    for rel in sources:
        source = (ROOT / rel).read_text(encoding="latin-1")
        converted, ledger = adapt(source, rel)
        if re.search(r"\b(?:v?sprintf|printf)\s*\([^;]*&\s*\w+\s*\+\s*1", converted, re.DOTALL):
            raise AssertionError(f"old stack cursor remains after conversion: {rel}")
        if ledger["output_sha256"] != sha(converted.encode("utf-8")):
            raise AssertionError(f"transformation output hash mismatch: {rel}")
        if converted != source:
            ledgers.append(ledger)
    root_counts = {row["source_path"]: sum(item["stack_vararg_calls"] for item in row["lowered_variadic_functions"])
                   for row in ledgers}
    expected = {"src/root/m1C62.c": 1, "src/root/m1CE2.c": 2, "src/root/m1FD2.c": 1,
                "src/root/m208F.c": 2, "src/root/m22BF.c": 5, "src/root/m171C.c": 1}
    if {path: count for path, count in root_counts.items() if count} != expected:
        raise AssertionError(f"stack-vararg source inventory drift: {root_counts}")
    m22 = next(row for row in ledgers if row["source_path"] == "src/root/m22BF.c")
    repeated = [row for row in m22["lowered_variadic_functions"] if row["stack_vararg_calls"] == 2]
    if len(repeated) != 2 or not all(row["uses_va_copy"] for row in repeated):
        raise AssertionError("m22BF formatter replay must use va_copy for each repeated argument walk")
    m22_text = (ROOT / "src/root/m22BF.c").read_text(encoding="latin-1")
    m22_lowered, _ = adapt(m22_text, "src/root/m22BF.c")
    if m22_lowered.count("va_copy(_dos_va_copy, _dos_va_args);") != 4:
        raise AssertionError("both two-pass m22BF functions must restart each copied argument walk")
    if any("dos_vsprintf" in line and "va_copy(" in line for line in m22_lowered.splitlines()):
        raise AssertionError("va_copy must be a statement before the original formatting call")
    if m22_lowered.count("dos_vsprintf(") != 6:
        raise AssertionError("m22BF should have one prototype plus five source formatting calls")
    for function in ("win_SetObjFormatStr", "win_ObjFormatPrint"):
        signature = f"void far {function}(int32_t _dos_obj_wide, ...)"
        if signature not in m22_lowered:
            raise AssertionError(f"native-wide last parameter missing: {function}")
        start = m22_lowered.find(signature, m22_lowered.find(signature) + 1)
        if start < 0:
            raise AssertionError(f"{function} definition was not widened along with its prototype")
        function_text = m22_lowered[start:start + 300]
        if "int16_t obj = (int16_t)_dos_obj_wide;" not in function_text or "va_start(_dos_va_args, _dos_obj_wide);" not in function_text:
            raise AssertionError(f"{function} does not use a promoted va_start parameter and narrowed source local")
    cross_tu = {}
    for rel in ("src/root/m00F8.c", "src/S09/m35F5.c"):
        converted, ledger = adapt((ROOT / rel).read_text(encoding="latin-1"), rel)
        if "win_SetObjFormatStr(int32_t _dos_obj_wide, ...)" not in converted:
            raise AssertionError(f"cross-TU prototype did not widen: {rel}")
        cross_tu[rel] = ledger["promoted_last_named_parameters"]

    compiler = os.environ.get("SIMANT_CC", "gcc")
    with tempfile.TemporaryDirectory(prefix="simant-varargs-") as temp:
        exe = Path(temp) / "native_format_test.exe"
        command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   "-I", str(ROOT / "portable/whole_program/platform"),
                   str(HERE / "native_format_test.c"),
                   str(ROOT / "portable/whole_program/platform/dos_format.c"),
                   "-o", str(exe)]
        compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if compiled.returncode:
            raise RuntimeError("native formatter compile failed:\n" + compiled.stdout + compiled.stderr)
        executed = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        if executed.returncode:
            raise RuntimeError("native formatter controls failed:\n" + executed.stdout + executed.stderr)
        version = subprocess.run([compiler, "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
        compiler_path = shutil.which(compiler)
        if compiler_path is None:
            raise RuntimeError(f"compiler executable was not resolved: {compiler}")
        executable_sha256 = sha(exe.read_bytes())

        # Compile the actual complete m22BF TU after this adapter and the
        # repository's whole-program target-width lowering, without linking it.
        aliases = load_function_aliases()
        translated_m22, _ = convert_words(m22_lowered, aliases)
        translated_m22, _ = re.subn(
            r"(?m)^\s*extern\s+[^;]*\b_f(?:mem\w+|str\w+)\s*\([^;]*;",
            "", translated_m22)
        generated_m22 = ('#include "dos_types.h"\n'
                         '#include "portable/whole_program/platform/dos_memory.h"\n'
                         '#include "portable/whole_program/platform/dos_io.h"\n'
                         '#pragma pack(push, 2)\n' + translated_m22 + '\n#pragma pack(pop)\n')
        m22_path = Path(temp) / "root_m22BF_varargs.c"
        m22_object = Path(temp) / "root_m22BF_varargs.o"
        m22_path.write_text(generated_m22, encoding="utf-8", newline="\n")
        generated_compile = [compiler, "-std=c11", "-fsigned-char", "-fno-builtin",
                             "-I", str(ROOT), "-I", str(ROOT / "build/workers/whole_program/generated"),
                             "-Werror=implicit-function-declaration", "-Werror=implicit-int",
                             "-c", str(m22_path), "-o", str(m22_object)]
        generated_result = subprocess.run(generated_compile, cwd=ROOT, text=True, capture_output=True)
        if generated_result.returncode:
            raise RuntimeError("adapted whole-TU m22BF compile failed:\n" + generated_result.stdout + generated_result.stderr)

        # Extract the real generated win_SetObjFormatStr definition and execute
        # it with bounded native storage providers. This tests its repeated
        # format walk rather than a handwritten copy of the formatter logic.
        lowered_m22, _ = convert_words(m22_lowered, aliases)
        fn = next(row for row in variadic_functions(lowered_m22) if row[0] == "win_SetObjFormatStr")
        actual_function = lowered_m22[fn[2]:fn[4] + 1]
        # Only the source's packed far-pointer field is supplied through a
        # host-width sidecar. The formatter body/call sequence remains exact.
        fixture_function = actual_function.replace(
            "*(char  *  *  *)(o + 0x2a)", "fixture_record_slot")
        if fixture_function == actual_function:
            raise AssertionError("expected m22BF record-pointer view was not found for the host test provider")
        source_harness = r'''#include "dos_format.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static char object_bytes[256];
static char record_text[128];
static char *record_word = record_text;
static char **record_handle = &record_word;
static char **fixture_record_slot;
static char logged_text[128];
void win_LockWin(int16_t obj) { (void)obj; }
void win_UnlockWin(int16_t obj) { (void)obj; }
char *win_ObjAddr(int16_t obj) { (void)obj; return object_bytes; }
uint16_t _fstrlen(const char *text) { return (uint16_t)strlen(text); }
char *_fstrcpy(char *dst, const char *src) { return strcpy(dst, src); }
char **f_171C_13CA(int32_t bytes, int16_t kind, const char *tag)
{ (void)bytes; (void)kind; (void)tag; return record_handle; }
char **f_171C_18A6(char **record, int32_t bytes, int16_t kind)
{ (void)bytes; (void)kind; return record; }
char *f_171C_1B84(char **record) { return *record; }
void f_171C_1BBA(char **record) { (void)record; }
void WinPrintf(const char *format, ...)
{
    va_list args;
    va_start(args, format);
    (void)dos_vsprintf(logged_text, format, args);
    va_end(args);
}
''' + fixture_function + r'''
int main(void)
{
    strcpy(object_bytes + 0x2e, "value=%d/%ld");
    win_SetObjFormatStr(7, (int16_t)-32768, (int32_t)123456);
    if (strcmp(logged_text, "\n= value=-32768/123456") != 0) return 1;
    if (strcmp(record_text, "value=-32768/123456") != 0) return 2;
    puts("generated m22BF repeated format content passed");
    return 0;
}
'''
        m22_harness = Path(temp) / "m22BF_va_copy_content.c"
        m22_harness_exe = Path(temp) / "m22BF_va_copy_content.exe"
        m22_harness.write_text(source_harness, encoding="utf-8", newline="\n")
        m22_harness_command = [compiler, "-std=c11", "-fsigned-char", "-fno-builtin",
                               "-Wall", "-Wextra", "-Werror", "-pedantic",
                               "-I", str(ROOT / "portable/whole_program/platform"),
                               str(m22_harness), str(ROOT / "portable/whole_program/platform/dos_format.c"),
                               "-o", str(m22_harness_exe)]
        m22_harness_compile = subprocess.run(m22_harness_command, cwd=ROOT, text=True, capture_output=True)
        if m22_harness_compile.returncode:
            raise RuntimeError("generated m22BF content harness compile failed:\n" +
                               m22_harness_compile.stdout + m22_harness_compile.stderr)
        m22_harness_run = subprocess.run([str(m22_harness_exe)], cwd=ROOT, text=True, capture_output=True, timeout=15)
        if m22_harness_run.returncode:
            raise RuntimeError("generated m22BF repeated-format check failed:\n" +
                               m22_harness_run.stdout + m22_harness_run.stderr)
        generated_object_sha256 = sha(m22_object.read_bytes())
        m22_harness_exe_sha256 = sha(m22_harness_exe.read_bytes())

    return {
        "schema": "whole-program-dos-varargs-controls-v1",
        "status": "PASS",
        "source_stack_cursor_lowering": {
            "module_count": len(sources), "changed_module_count": len(ledgers),
            "cursor_call_count": sum(root_counts.values()),
            "counts_by_source": {path: count for path, count in root_counts.items() if count},
            "transformation_ledgers": ledgers,
            "m22bf_copy_proof": repeated,
            "promoted_last_parameters": [row["promoted_last_named_parameters"] for row in ledgers
                                         if row["promoted_last_named_parameters"]],
            "cross_tu_promoted_prototypes": cross_tu,
            "changed_module_paths": sorted(row["source_path"] for row in ledgers),
        },
        "source_literal_scan": scan_format_literals(),
        "format_pipeline_evidence": [
            {"source": "src/root/m15F8.c:fd_4E37_0000",
             "template": "C initializer contains one %d and the source printf supplies 5 - i",
             "status": "source-template grounded; DOS execution not performed"},
            {"source": "src/S10/m35F5.c:formatted menu row",
             "templates": ["%%-%ds", "%%c%%-%ds"],
             "expansion": "source sprintf emits %-<width>s or %c%-<width>s; the resulting format is parsed by this runtime",
             "status": "source-template grounded; width comes from maxLen / maxLen - 1"},
            {"source": "source-owned no-argument printf formats", "resolved": resolve_dynamic_noarg_formats(),
             "status": "the initialized source-owned values were resolved and have zero percent conversions; the m205F uninitialized-msg source path remains explicit debt"},
        ],
        "native_controls": {
            "compiler": compiler, "compiler_path": str(Path(compiler_path).resolve()),
            "compiler_sha256": sha(Path(compiler_path).read_bytes()),
            "compiler_version": version, "executable_sha256": executable_sha256,
            "command": [*command[:-1], "<TEMP>/native_format_test.exe"],
            "result": executed.stdout.strip(),
            "generated_m22bf_tu_compile": {
                "command": ["<TEMP>/root_m22BF_varargs.c" if value == str(m22_path) else
                            "<TEMP>/root_m22BF_varargs.o" if value == str(m22_object) else value
                            for value in generated_compile],
                "passed": True, "object_sha256": generated_object_sha256,
                "transformation": "actual src/root/m22BF.c -> varargs adapter -> whole_program.convert_words; standalone TU compile only",
            },
            "generated_m22bf_repeated_format": {
                "command": ["<TEMP>/m22BF_va_copy_content.c" if value == str(m22_harness) else
                            "<TEMP>/m22BF_va_copy_content.exe" if value == str(m22_harness_exe) else value
                            for value in m22_harness_command],
                "passed": True, "executable_sha256": m22_harness_exe_sha256,
                "result": m22_harness_run.stdout.strip(),
                "function_body_sha256": sha(actual_function.encode("utf-8")),
                "provider_normalization": "one packed DOS pointer at object +0x2a is held in fixture_record_slot because native pointers are wider; the source formatting expressions/call order are unchanged",
            },
            "positive": ["DOS16 signed/unsigned word truncation", "DOS32 signed/unsigned long",
                         "width/precision and dynamic stars", "strings/chars/pointers", "bounded truncation"],
            "negative": ["float", "%n", "field over limit"],
            "dos_oracle_invocations": 0,
            "claim": "native ABI and formatting boundary controls only; no DOS text/pixel equivalence claim",
            "limits": ["C varargs do not encode the number of supplied arguments; future dynamic format pointers must be source/resource-resolved before use.",
                       "%p uses host pointer text for native diagnostics, not DOS far-pointer spelling.",
                       "No generic asset-database format inventory is claimed; the two fd_55B3 strings checked here are source-owned pointer-table entries, not database records."],
        },
        "input_hashes": {
            **{rel: sha((ROOT / rel).read_bytes()) for rel in sources},
            "portable/whole_program/conversions/varargs.py": sha((ROOT / "portable/whole_program/conversions/varargs.py").read_bytes()),
            "portable/tools/whole_program.py": sha((ROOT / "portable/tools/whole_program.py").read_bytes()),
            "portable/tools/recover_source.py": sha((ROOT / "portable/tools/recover_source.py").read_bytes()),
            "portable/research/whole_program_unprovided_owners_v2.json": sha((ROOT / "portable/research/whole_program_unprovided_owners_v2.json").read_bytes()),
            "build/workers/whole_program/generated/dos_types.h": sha((ROOT / "build/workers/whole_program/generated/dos_types.h").read_bytes()),
            "portable/whole_program/platform/dos_format.h": sha((ROOT / "portable/whole_program/platform/dos_format.h").read_bytes()),
            "portable/whole_program/platform/dos_format.c": sha((ROOT / "portable/whole_program/platform/dos_format.c").read_bytes()),
            "portable/tests/recovered/whole_program_varargs/native_format_test.c": sha((HERE / "native_format_test.c").read_bytes()),
            "portable/tests/recovered/whole_program_varargs/README.md": sha((HERE / "README.md").read_bytes()),
            "portable/tests/recovered/whole_program_varargs/run_varargs.py": sha(Path(__file__).read_bytes()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = run()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        target = args.report if args.report.is_absolute() else ROOT / args.report
        if target.exists():
            raise SystemExit(f"refusing to overwrite existing report: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": report["status"], "calls": report["source_stack_cursor_lowering"]["cursor_call_count"],
                      "compiler": report["native_controls"]["compiler_version"],
                      "unsupported_literal_candidates": len(report["source_literal_scan"]["unparsed_percent_candidates"]),
                      "report": str(args.report) if args.report else None}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
