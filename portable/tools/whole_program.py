#!/usr/bin/env python3
"""Whole-TU mechanical migration lane, independent of the admitted Next10 lane.

Compile success is diagnostic, never a behavioral or link-coverage claim. This
lane retains all declarations and function order rather than selecting bodies.
Unconverted hardware and DOS-layout dependencies remain explicit failures.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from word_spelling import PROTECTED, explicit_unsigned_word
import recover_source as historical_parser
from portable.whole_program.conversions.rng import adapt as adapt_rng
from portable.whole_program.conversions.startup import adapt as adapt_startup
from portable.whole_program.conversions.fonts import adapt as adapt_fonts
from portable.whole_program.conversions.pointer_globals import adapt as adapt_pointer_globals
from portable.whole_program.conversions.audio import adapt as adapt_audio
from portable.whole_program.conversions.history import adapt as adapt_history
from portable.whole_program.conversions.varargs import adapt as adapt_varargs
from portable.whole_program.conversions.windows import convert_window_source
from portable.whole_program.conversions.timer import adapt as adapt_timer
from portable.whole_program.conversions.startup_bundle import convert_startup_sources
from portable.whole_program.conversions.findindex_native_guard import adapt_whole_source as adapt_findindex
from source_state_aliases_v2 import (load_plan as load_initialized_plan,
    validate_historical_pins, validate_source_declarations,
    transform as adapt_initialized_aliases)
from portable.whole_program.platform.graphics_source_convert import convert as adapt_graphics
from portable.whole_program.conversions.unprovided_state_v2 import (
    rewrite_source as adapt_state, emit_owner_source, pinned_consumer_control)
from portable.whole_program.conversions.source_bounded_state import (
    load_plan as load_bounded_plan, render_owners as render_bounded_owners,
    adapt as adapt_bounded_state)

IO_NAMES = {name: 'dos_' + name for name in
            ('open', 'read', 'write', 'lseek', 'close', 'access', 'chdir',
             'getcwd', 'remove', 'stricmp', 'fopen', 'fread', 'fclose')}
IO_NAMES['FILE'] = 'DosFileStream'
RUNTIME_NAMES = {'errno': 'dos_errno', 'malloc': 'dos_malloc', 'free': 'dos_free',
                 '_ffree': 'dos_free', '_frealloc': 'dos_realloc', **IO_NAMES}


def centralize_io(source: str) -> tuple[str, int]:
    """Remove only legacy declarations; actual calls keep their argument order."""
    pattern = (r'(?m)^\s*extern\s+[^;]*\b(?:' +
               '|'.join(IO_NAMES[n] for n in IO_NAMES if n != 'FILE') +
               r')\s*\([^;]*;')
    source, count = re.subn(pattern, '', source)
    source, typedefs = re.subn(r'\btypedef\s+struct\s+_iobuf\s+DosFileStream\s*;', '', source)
    return source, count + typedefs


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def convert_words(source: str, aliases: dict[str, str] | None = None) -> tuple[str, dict]:
    source, unsigned_count = explicit_unsigned_word(source)
    parts = PROTECTED.split(source)
    counts = Counter()
    alias_pattern = re.compile(r"\b(?:" + "|".join(re.escape(name) for name in (aliases or {})) + r")\b") if aliases else None
    substitutions = [
        (r"\bunsigned\s+char\b", "uint8_t"),
        (r"\bsigned\s+char\b", "int8_t"),
        (r"\bunsigned\s+long(?:\s+int)?\b", "uint32_t"),
        (r"\bsigned\s+long(?:\s+int)?\b", "int32_t"),
        (r"\bunsigned\s+(?:short(?:\s+int)?|int)\b", "uint16_t"),
        (r"\bsigned\s+(?:short(?:\s+int)?|int)\b", "int16_t"),
        (r"\blong(?:\s+int)?\b", "int32_t"),
        (r"\bshort(?:\s+int)?\b|\bint\b", "int16_t"),
        # Plain historical char is signed on the pinned MSC profile. Keep char
        # pointers usable with string services by using the native signed-char
        # compiler mode; do not conflate uint8_t storage with signed char.
        (r"\bfar\b|\bnear\b|\b_fastcall\b|\bpascal\b|\bregister\b", ""),
    ]
    for i in range(0, len(parts), 2):
        if alias_pattern:
            parts[i], count = alias_pattern.subn(lambda m: aliases[m.group()], parts[i])
            counts["registered_function_aliases"] += count
        for pattern, replacement in substitutions:
            parts[i], count = re.subn(pattern, replacement, parts[i])
            counts[replacement or "qualifier_removed"] += count
        parts[i], count = re.subn(r"\bmain\s*(?=\()", "dos_game_main", parts[i])
        counts["main_renamed"] += count
        # These are source-owned objects/functions, not the native CRT ABI.
        # Namespace them before including any host headers.
        for old, new in RUNTIME_NAMES.items():
            parts[i], count = re.subn(r"\b" + old + r"\b", new, parts[i])
            counts[old + "_namespaced"] += count
    counts["bare_unsigned"] = unsigned_count
    return "".join(parts), dict(counts)


def source_paths() -> list[Path]:
    return sorted(p for p in (ROOT / "src").glob("*/*.c")
                  if p.parent.name in {"root", "data"} or re.fullmatch(r"S\d+", p.parent.name))


def masked(source: str) -> str:
    return PROTECTED.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), source)


def reviewed_overlays(path: Path, source: str, entries: list[dict]) -> tuple[str, list[dict]]:
    rows = []
    for entry in entries:
        canonical = entry["canonical_translation_unit"]
        if canonical["path"] != path.relative_to(ROOT).as_posix():
            continue
        if digest(path) != canonical["file_sha256"]:
            raise ValueError("canonical source changed after behavior overlay audit")
        reviewed = entry["reviewed_tested_source"]
        tested_path = ROOT / reviewed["path"]
        if digest(tested_path) != reviewed["sha256_registered"]:
            raise ValueError("reviewed behavior source identity changed")
        tested_source = tested_path.read_text(encoding="utf-8")
        tested_heads = [r for r in function_heads(tested_source) if r["name"] == reviewed["body_name"]]
        canonical_heads = [r for r in function_heads(source) if r["name"] == entry["canonical_body"]["body_name"]]
        if len(tested_heads) != 1 or len(canonical_heads) != 1:
            raise ValueError("ambiguous reviewed/canonical code definition")
        tested_head, canonical_head = tested_heads[0], canonical_heads[0]
        body = tested_source[tested_head["start"]:tested_head["end"]]
        source = source[:canonical_head["start"]] + body + source[canonical_head["end"]:]
        rows.append({"function": entry["function"], "proof_category": "BEHAVIOR_EXACT",
                     "path": reviewed["path"], "sha256": digest(tested_path),
                     "different_from_canonical_tokens": not entry["comparison"]["token_equal"]})
    return source, rows


def function_heads(source: str) -> list[dict]:
    """Top-level brace scanner; declarations with initializer braces excluded.

    Macro-generated functions are recorded separately as preprocessor sites.
    Source positions stay aligned because comments/strings are blanked in place.
    """
    # Blank directives in place so source offsets remain exact.
    code = re.sub(r"(?m)^[ \t]*#(?:[^\n]*\\\n)*[^\n]*",
                  lambda m: re.sub(r"[^\n]", " ", m.group()), masked(source))
    result = []
    current_function = None
    knr_function = None
    depth = 0
    start = 0
    for i, ch in enumerate(code):
        if ch == "{" and depth == 0:
            head = code[start:i].strip()
            found = re.search(r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*$", head, re.S)
            if knr_function is not None:
                found = knr_function
            if found and not re.search(r"\btypedef\b|=", head):
                leading = start + len(code[start:i]) - len(code[start:i].lstrip())
                current_function = {"name": found.group(1),
                    "signature": source[leading:i].strip(),
                    "line": source.count("\n", 0, leading) + 1,
                    "start": leading}
                result.append(current_function)
                knr_function = None
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced top-level braces")
            if depth == 0:
                if current_function is not None:
                    current_function["end"] = i + 1
                    current_function = None
                start = i + 1
        elif ch == ";" and depth == 0:
            head = code[start:i].strip()
            # K&R parameter declarations belong to the following function.
            # Do not turn a prototype or pointer initializer into a definition.
            candidate = re.search(r"\b([A-Za-z_]\w*)\s*\(([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\)\s*\n\s*([^{}]+)$", head)
            if candidate and candidate.group(2) != "void" and "=" not in head and not re.search(r"\btypedef\b", head):
                knr_function = candidate
            elif knr_function is None:
                start = i + 1
    if depth:
        raise ValueError("unbalanced source braces")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", default="build/workers/whole_program/generated")
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--link", action="store_true", help="relocatable partial-core link; implies --compile, never produces a runnable game")
    args = ap.parse_args()
    if args.link:
        args.compile = True
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / "build/workers").resolve()):
        raise ValueError("output must be scratch under build/workers")
    output.mkdir(parents=True, exist_ok=True)
    frozen_check = output / "frozen-oracle-check.json"
    subprocess.run([sys.executable, str(ROOT / "tools/oracle_checkpoint.py"),
                    "--output", str(frozen_check)], cwd=ROOT, check=True,
                   capture_output=True, text=True)
    frozen = json.loads(frozen_check.read_text())
    if not frozen["ready"]:
        raise RuntimeError("frozen historical source/evidence input identity failed")
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    rows = []
    declarations = []
    symbols = json.loads((ROOT / "layout/symbols.json").read_text())["data"]
    function_aliases = historical_parser.load_function_aliases()
    overlay_path = ROOT / "portable/research/whole_program_behavior_sources.json"
    overlays = json.loads(overlay_path.read_text(encoding="utf-8"))["entries"]
    if len(overlays) != 29:
        raise ValueError("expected complete frozen behavioral source catalog")
    state_plan_path = ROOT / 'portable/research/whole_program_unprovided_owners_v2.json'
    state_plan = json.loads(state_plan_path.read_text(encoding='utf-8'))
    # The pre-conversion migration hash is a baseline receipt, not a circular
    # constraint on output after its aliases have been wired. The actual
    # immutable historical storage/source identities must still agree.
    for key in ('manifest', 'symbols'):
        pin = state_plan['inputs'][key]
        if digest(ROOT / pin['path']) != pin['sha256']:
            raise ValueError(f"state provenance historical {key} changed")
    for module in state_plan['inputs']['exact_omf_modules']:
        if digest(ROOT / module['source']) != module['source_sha256']:
            raise ValueError('state provenance source changed')
        if module['manifest_object_sha256'] != module['recompiled_object_sha256']:
            raise ValueError('state provenance requires exact historical OMF')
    consumer_control = pinned_consumer_control(state_plan)
    if not all(consumer_control['positive'].values()):
        raise ValueError('state pointer table source control failed')
    initialized_plan = load_initialized_plan()
    bounded_plan = load_bounded_plan()
    alias_failures = (validate_historical_pins(initialized_plan) +
                      validate_source_declarations(initialized_plan))
    if alias_failures:
        raise ValueError(f'initialized state provenance changed: {alias_failures}')
    # Capture conversion/runtime header identities BEFORE reading sources. A
    # helper changed mid-run must fail the final stability check, not silently
    # pin its later bytes alongside output generated by an earlier version.
    conversion_inputs = [Path(__file__), Path(__file__).with_name("word_spelling.py"),
        Path(__file__).with_name("recover_source.py"), ROOT / "layout/symbols.json", overlay_path,
        ROOT / "portable/whole_program/platform/dos_memory.h",
        ROOT / "portable/whole_program/platform/dos_files.h",
        ROOT / "portable/whole_program/platform/crt_rng.h",
        ROOT / "portable/whole_program/platform/seed_source.h",
        ROOT / "portable/game/simulation/rng.h",
        ROOT / "portable/whole_program/types/database.h", ROOT / "portable/platform/memory.h",
        ROOT / "portable/whole_program/conversions/rng.py",
        ROOT / "portable/whole_program/conversions/startup.py"]
    conversion_inputs += [ROOT / "portable/whole_program/conversions/fonts.py",
                          ROOT / "portable/whole_program/types/fonts.h"]
    conversion_inputs += [ROOT / name for name in (
        "portable/whole_program/conversions/pointer_globals.py",
        "portable/whole_program/conversions/pointer_globals.h",
        "portable/whole_program/platform/dos_io.h",
        "portable/whole_program/conversions/audio.py",
        "portable/whole_program/conversions/history.py",
        "portable/whole_program/conversions/varargs.py",
        "portable/whole_program/platform/dos_format.h",
        "portable/tests/history_event_lowering/comparison_report_closure_next10.json",
        "portable/whole_program/platform/audio.h",
        "portable/whole_program/platform/audio_events.h",
        "portable/whole_program/platform/whole_audio_provider.h",
        "portable/research/audio_voice_scheduler.h",
        "portable/research/audio_voice_admission.h",
        "portable/whole_program/platform/handles.h",
        "portable/whole_program/platform/font_blit.h",
        "portable/whole_program/platform/input_time.h",
        "portable/whole_program/platform/sdl3/input_time_host.h",
        "portable/platform/host.h", "portable/game/timing.h",
        "portable/whole_program/platform/directory.h",
        "portable/whole_program/conversions/windows.py",
        "portable/whole_program/window_refs.h",
        "portable/whole_program/conversions/unprovided_state_v2.py",
        "portable/whole_program/conversions/source_bounded_state.py",
        "portable/whole_program/conversions/findindex_native_guard.py",
        "portable/research/whole_program_source_bounded_owners_v3.json",
        "portable/whole_program/platform/ems_dos_abi.h",
        "portable/whole_program/platform/ems_host.h",
        "portable/whole_program/platform/m1b73_main_input.h",
        "portable/whole_program/conversions/timer.py",
        "portable/whole_program/conversions/startup_bundle.py",
        "portable/whole_program/conversions/main_preflight.py",
        "portable/tools/source_state_aliases_v2.py",
        "portable/tests/recovered/whole_program_asm_state/plan_v2.json",
        "portable/whole_program/state/asm_shared_state.h",
        "portable/whole_program/platform/startup_preflight.h",
        "portable/whole_program/platform/startup_host.h",
        "portable/whole_program/types/timer.h",
        "portable/whole_program/platform/m1b73_events.h",
        "portable/whole_program/platform/m1b73_timer_view.h",
        "portable/whole_program/platform/graphics_source_convert.py",
        "portable/whole_program/platform/graphics_source_fields.h",
        "portable/whole_program/platform/graphics.h",
        "portable/whole_program/platform/graphics_line_1499.h",
        "portable/whole_program/text_bitmap.h",
        "portable/whole_program/text_bitmap_bridge.h",
        "portable/render/primitives.h",
        "portable/whole_program/state/source_tables.h",
        "portable/research/whole_program_unprovided_owners_v2.json",
        "portable/whole_program/algorithms/lzss.h",
        "portable/whole_program/algorithms/wildcard.h",
        "portable/whole_program/algorithms/asm_utilities.h",
        "portable/whole_program/algorithms/balloon.h")]
    conversion_inputs += [ROOT / entry['path'] for entry in bounded_plan['inputs'].values()
                         if isinstance(entry, dict) and 'path' in entry]
    conversion_inputs += [ROOT / rel for rel in initialized_plan['pinned_source_hashes']]
    initial_inputs = {p.relative_to(ROOT).as_posix(): digest(p) for p in conversion_inputs}
    native_startups, startup_conversion = convert_startup_sources(
        (ROOT / 'src/root/m15F8.c').read_text(encoding='utf-8'),
        (ROOT / 'src/S15/m384C.c').read_text(encoding='utf-8'))
    for path in source_paths():
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        original_functions = function_heads(source)
        platform_conversions = []
        if rel in native_startups:
            source = native_startups[rel]
            platform_conversions.append(startup_conversion)
        if rel == 'src/root/m1FD2.c':
            source, ledger = adapt_timer(source)
            platform_conversions.append(ledger)
        if rel == 'src/S24/m39C7.c':
            source, ledger = adapt_history(source)
            platform_conversions.append(ledger)
        # These adapters require the original whole-TU identity. Apply before
        # frozen reviewed behavioral body overlays, which retain the converted
        # declarations/macros and change only their reviewed function body.
        if rel in {'src/root/m284A.c', 'src/root/m29F0.c', 'src/root/m277E.c',
                   'src/root/m29D6.c', 'src/root/m293A.c', 'src/root/m290D.c'}:
            source, ledger = adapt_audio(rel, source)
            platform_conversions.append(ledger)
        source, overlay_rows = reviewed_overlays(path, source, overlays)
        if rel == 'src/root/m1986.c':
            source, ledger = adapt_findindex(source, rel)
            platform_conversions.append(ledger)
        state_before = source
        source = adapt_state(source, state_plan, rel)
        if source != state_before:
            platform_conversions.append({'kind': 'SOURCE_PROVEN_SHARED_STATE_ALIASES',
                'provenance': state_plan_path.relative_to(ROOT).as_posix(),
                'provenance_sha256': digest(state_plan_path),
                'changes': 'identifier aliases; pointer-table scalar views become explicit indexed reads',
                'claim': 'Native state ownership conversion, separate from historical exact evidence'})
        source, bounded_ledger = adapt_bounded_state(source, rel, bounded_plan)
        if bounded_ledger:
            platform_conversions.append(bounded_ledger)
        if rel in {'src/root/m15F8.c', 'src/S20/m39F1.c'}:
            source = '#include "portable/whole_program/state/source_tables.h"\n' + source
        source, alias_ledger = adapt_initialized_aliases(source, initialized_plan)
        if any(alias_ledger['replacement_counts'].values()):
            platform_conversions.append({'kind': 'INITIALIZED_DATA_OWNER_ALIASES',
                'plan': 'portable/tests/recovered/whole_program_asm_state/plan_v2.json',
                **alias_ledger})
        if path.parent.name == "root" and path.name == "m0093.c":
            source, ledger = adapt_rng(source)
            platform_conversions.append(ledger)
        if path.parent.name == "S25" and path.name == "m3BA4.c":
            source, adapted = historical_parser.adapt_ax_tail_return(source)
            if not adapted:
                raise ValueError("expected historical AX tail return not found")
            platform_conversions.append({"kind": "EXPLICIT_HISTORICAL_AX_RETURN",
                "function": "o25_3BA4_19AD", "callee": "o25_3BA4_1686",
                "basis": "Original exact MSC body leaves the final callee AX result in AX; same explicit-return conversion is already used by the admitted Next10 generator.",
                "changes": "return final call result; all state assignments and arguments preserved"})
        source, font_conversion = adapt_fonts(rel, source)
        if font_conversion:
            platform_conversions.append(font_conversion)
        source, pointer_conversion = adapt_pointer_globals(rel, source)
        if pointer_conversion:
            platform_conversions.append(pointer_conversion)
        if path.parent.name == 'root' and path.name in {
                'm2505.c', 'm20E8.c', 'm23AE.c', 'm22BF.c', 'm21FA.c', 'm218D.c'}:
            windows = convert_window_source(source)
            if windows.unresolved:
                raise ValueError(f"unconverted native window boundary: {rel}: {windows.unresolved}")
            source = windows.text
            platform_conversions.append({'kind': 'DOS_WINDOW_POINTER_SIDECARS',
                'source': rel, 'replacements': windows.replacements,
                'claim': 'Native pointer/record conversion; no new DOS equivalence claim'})
        source, format_conversion = adapt_varargs(source, rel)
        if (format_conversion['lowered_variadic_functions'] or
                format_conversion['removed_legacy_prototypes'] or
                format_conversion.get('promoted_last_named_parameters')):
            platform_conversions.append(format_conversion)
        # The DOS BDA modifier byte is an input service, never a native pointer.
        source, modifier_reads = re.subn(r"\*\s*\(\s*(?:(unsigned)\s+)?char\s+far\s*\*\s*\)\s*0x0*417L",
            lambda m: "dos_keyboard_modifiers()" if m.group(1) else "(char)dos_keyboard_modifiers()", source, flags=re.I)
        if modifier_reads:
            platform_conversions.append({"kind": "KEYBOARD_MODIFIER_SERVICE",
                "address": "0000:0417", "count": modifier_reads,
                "changes": "source read replaced by logical DOS-bit-position input state query"})
        source, graphics_declarations = adapt_graphics(source)
        if graphics_declarations:
            platform_conversions.append({'kind': 'BOUND_NATIVE_GRAPHICS_SOURCE_ABI',
                'removed_legacy_externs': list(graphics_declarations),
                'changes': 'source graphics fields use one native driver owner; raster call order retained',
                'claim': 'Platform boundary conversion; unsupported driver operations remain explicit'})
        translated, operations = convert_words(source, function_aliases)
        # MSC's default structure alignment is two bytes. Keep that default
        # for pure scalar/file records; native pointer-bearing fields still
        # require the explicit runtime/sidecar conversions recorded separately.
        # Source pack(1) remains in force until the source restores its default.
        translated, default_pack_restores = re.subn(r"(?m)^(\s*#pragma\s+pack)\s*\(\s*\)",
                                                    r"\1(2)", translated)
        operations["source_default_pack_restores"] = default_pack_restores
        operations["default_record_alignment"] = 2
        database_family = path.parent.name == "root" and path.name in {"m1986.c", "m19A9.c", "m1A28.c"}
        if database_family:
            translated, count = re.subn(r"\btypedef\s+struct\s*\{[^{}]*\}\s*(?:IndexEntry|IndexHeader|DBHeader|DBRecordHeader|OpenDBRec)\s*;",
                                        "", translated, flags=re.S)
            expected_count = {"m1986.c": 3, "m19A9.c": 3, "m1A28.c": 2}[path.name]
            if count != expected_count:
                raise ValueError("database source type inventory changed")
            operations["shared_database_types"] = count
        # One word-count ABI for the MSC large-model runtime declarations.
        # Signed/unsigned word call-site declarations passed the same 16 bits.
        translated, removed = re.subn(r"(?m)^\s*extern\s+[^;]*\b_f(?:mem\w+|str\w+)\s*\([^;]*;",
                                      "", translated)
        operations["far_memory_declarations_centralized"] = removed
        translated, removed = centralize_io(translated)
        operations['dos_io_declarations_centralized'] = removed
        prefix = ('#include "dos_types.h"\n'
                  '#include "portable/whole_program/platform/dos_memory.h"\n'
                  '#include "portable/whole_program/platform/dos_io.h"\n')
        if modifier_reads:
            prefix += "uint8_t dos_keyboard_modifiers(void);\n"
        if database_family:
            prefix += '#include "portable/whole_program/types/database.h"\n'
        # These two declarations are absent in S19 but defined in the frozen
        # S24/S13 TUs; retain the caller's original Event view pending common
        # event-layout reconciliation.
        if path.parent.name == "S19":
            translated = translated.replace("int16_t  o19_384C_0000(void)",
                "extern void ProcHistoryEvent(struct Event *);\n"
                "extern void ProcYardEvent(struct Event *);\n\n"
                "int16_t  o19_384C_0000(void)")
            operations["missing_source_event_prototypes"] = 2
        if path.parent.name == "S20":
            prefix += "#include <ctype.h>\n"
            operations["ctype_declaration_header"] = 1
        if path.parent.name == "S09" and path.name == "m35F5.c":
            prefix += '#include "portable/whole_program/platform/dos_files.h"\n'
            operations["dos_directory_record_and_prototypes"] = 1
        target = output / f"{path.parent.name}_{path.stem}.c"
        generated = prefix + "#pragma pack(push, 2)\n" + translated + "\n#pragma pack(pop)\n"
        target.write_text(generated, encoding="utf-8", newline="\n")
        source_functions = function_heads(source)
        generated_functions = function_heads(generated)
        expected_names = [function_aliases.get(r["name"], r["name"]) for r in source_functions]
        expected_names = ['dos_game_main' if n == 'main' else RUNTIME_NAMES.get(n, n) for n in expected_names]
        if expected_names != [r["name"] for r in generated_functions]:
            raise ValueError(f"function membership/order changed: {rel}")
        body_checks = []
        for old, new in zip(source_functions, generated_functions):
            expected, _ = convert_words(source[old["start"]:old["end"]], function_aliases)
            actual = generated[new["start"]:new["end"]]
            # Extern declarations local to a function use the same common ABI.
            expected = re.sub(r"(?m)^\s*extern\s+[^;]*\b_f(?:mem\w+|str\w+)\s*\([^;]*;", "", expected)
            expected, _ = centralize_io(expected)
            if expected != actual:
                raise ValueError(f"unexpected function body edit: {rel}:{old['name']}")
            body_checks.append({"name": new["name"], "mechanical_body_sha256": hashlib.sha256(actual.encode()).hexdigest()})
        hardware = [i + 1 for i, line in enumerate(masked(source).splitlines())
                    if re.search(r"\b_asm\b|\b_based\s*\(|^\s*#include\s*<dos.h>", line)]
        scaffold = re.findall(r"SCAFFOLD BEGIN:\s*(\w+)", source)
        row = {"source": rel, "source_sha256": digest(path),
               "generated": target.relative_to(ROOT).as_posix(),
               "generated_sha256": digest(target), "operations": operations,
               "functions": source_functions, "mechanical_body_checks": body_checks,
               "original_lexical_functions": original_functions,
               "platform_conversions": platform_conversions,
               "module_kind": "DATA" if path.parent.name == "data" else "CODE",
               "hardware_lines": hardware,
               "reviewed_behavior_overlays": overlay_rows,
               "historical_scaffold_markers_retained": scaffold,
               "classification": "MIXED" if hardware else "C_SOURCE",
               "admitted": False}
        row['direct_call_identifiers'] = sorted(set(re.findall(
            r'\b([A-Za-z_]\w*)\s*\(', masked(generated))) -
            {'if', 'for', 'while', 'switch', 'sizeof', 'return'})
        for declaration in historical_parser.object_declarations(source):
            symbol = symbols.get(declaration["name"], {})
            declarations.append({"module": rel, **declaration,
                "layout_address": [symbol.get("seg"), symbol.get("off")],
                "alias_of": symbol.get("alias_of")})
        rows.append(row)
    header = output / "dos_types.h"
    header.write_text("/* Native scalar ABI only; DOS packed records require explicit conversion. */\n"
                      "#ifndef SIMANT_WHOLE_DOS_TYPES_H\n#define SIMANT_WHOLE_DOS_TYPES_H\n"
                      "#include <stdint.h>\n#include <stddef.h>\n"
                      "_Static_assert(sizeof(int16_t)==2, \"DOS int\");\n"
                      "_Static_assert(sizeof(int32_t)==4, \"DOS long\");\n"
                      "_Static_assert((char)-1<0, \"MSC signed char\");\n#endif\n",
                      encoding="utf-8", newline="\n")
    support_rows = []
    bounded_header, bounded_source = render_bounded_owners(bounded_plan)
    (output / 'native_owners.h').write_text(bounded_header, encoding='utf-8', newline='\n')
    bounded_target = output / 'native_owners.c'
    bounded_target.write_text(bounded_source, encoding='utf-8', newline='\n')
    support_rows.append({'source': bounded_target.relative_to(ROOT).as_posix(),
        'source_sha256': digest(bounded_target), 'generated': bounded_target.relative_to(ROOT).as_posix(),
        'module_kind': 'SOURCE_BOUNDED_NATIVE_STATE', 'admitted': False,
        'owners': bounded_plan['summary']['owner_count'],
        'native_bytes': bounded_plan['summary']['native_bytes']})
    state_owners = output / 'source_state_owners.c'
    state_owners.write_bytes(emit_owner_source(state_plan))
    support_rows.append({'source': state_owners.relative_to(ROOT).as_posix(),
        'source_sha256': digest(state_owners), 'generated': state_owners.relative_to(ROOT).as_posix(),
        'module_kind': 'SOURCE_PROVEN_NATIVE_COMMON_STATE', 'admitted': False,
        'provenance_sha256': digest(state_plan_path),
        'owners': len(state_plan['bss_owner_candidates']),
        'source_extent_bytes': sum(g['owner_extent_bytes'] for g in state_plan['bss_owner_candidates'])})
    for rel, kind in [
        ("portable/whole_program/state/database.c", "NATIVE_SHARED_STATE"),
        ("portable/whole_program/state/asm_shared_state.c", "SOURCE_PROVEN_ASM_DATA_SCALARS"),
        ("portable/whole_program/conversions/pointer_globals.c", "NATIVE_SHARED_POINTER_TABLES"),
        ("portable/whole_program/platform/font_blit.c", "SOURCE_DERIVED_FONT_RASTER_AND_STATE"),
        ("portable/whole_program/window_refs.c", "NATIVE_WINDOW_POINTER_OWNERSHIP"),
        ("portable/whole_program/platform/dos_memory.c", "NATIVE_PLATFORM_SERVICE"),
        ("portable/whole_program/platform/crt_rng.c", "NATIVE_RUNTIME_SERVICE"),
        ("portable/whole_program/platform/seed_source.c", "EXPLICIT_HOST_STARTUP_SEED_BOUNDARY"),
        ("portable/whole_program/platform/dos_io.c", "NATIVE_PLATFORM_SERVICE"),
        ("portable/whole_program/platform/startup_preflight.c", "NATIVE_FILE_STARTUP_CONTRACT"),
        ("portable/whole_program/platform/startup_host.c", "NATIVE_LEGACY_PLATFORM_RETIREMENT"),
        ("portable/whole_program/platform/ems_host.c", "NATIVE_NO_EMS_PLATFORM"),
        ("portable/whole_program/platform/ems_dos_abi.c", "NATIVE_NO_EMS_SOURCE_ABI"),
        ("portable/whole_program/platform/audio.c", "NATIVE_PLATFORM_SERVICE"),
        ("portable/whole_program/platform/audio_events.c", "SOURCE_AUDIO_INTENT_CAPTURE"),
        ("portable/whole_program/platform/whole_audio_provider.c", "NATIVE_SOURCE_EVENT_AUDIO_PROVIDER"),
        ("portable/research/audio_voice_scheduler.c", "DOS_VERIFIED_DAC_SAMPLE_SCHEDULER"),
        ("portable/research/audio_voice_admission.c", "DOS_VERIFIED_DAC_VOICE_ARITHMETIC"),
        ("portable/whole_program/platform/handles.c", "NATIVE_PLATFORM_SERVICE"),
        ("portable/whole_program/platform/input_time.c", "NATIVE_PLATFORM_SERVICE"),
        ("portable/whole_program/platform/m1b73_events.c", "SOURCE_DERIVED_EVENT_TIMER_SERVICE"),
        ("portable/whole_program/platform/m1b73_timer_view.c", "NATIVE_TYPED_TIMER_FIELD_BRIDGE"),
        ("portable/whole_program/platform/m1b73_main_input.c", "NATIVE_SOURCE_MAIN_INPUT_BINDING"),
        ("portable/whole_program/platform/graphics.c", "NATIVE_INDEXED_GRAPHICS_BOUNDARY"),
        ("portable/whole_program/platform/graphics_line_1499.c", "DOS_VERIFIED_SOURCE_PIXEL_WALK"),
        ("portable/whole_program/text_bitmap.c", "DOS_VERIFIED_TEXT_BITMAP_ALGORITHM"),
        ("portable/whole_program/text_bitmap_bridge.c", "NATIVE_TEXT_BITMAP_SOURCE_ABI"),
        ("portable/render/primitives.c", "EXISTING_NATIVE_RASTER_STORAGE"),
        ("portable/whole_program/platform/sdl3/input_time_host.c", "NATIVE_HOST_BINDING"),
        ("portable/game/timing.c", "SOURCE_DERIVED_TIMING_CONTRACT"),
        ("portable/whole_program/platform/directory.c", "NATIVE_PLATFORM_SERVICE"),
        ("portable/whole_program/platform/dos_format.c", "NATIVE_RUNTIME_SERVICE"),
        ("portable/whole_program/algorithms/lzss.c", "SOURCE_DERIVED_ASM_ALGORITHMS"),
        ("portable/whole_program/algorithms/wildcard.c", "SOURCE_DERIVED_ASM_ALGORITHMS"),
        ("portable/whole_program/algorithms/asm_utilities.c", "SOURCE_DERIVED_ASM_ALGORITHMS"),
        ("portable/whole_program/algorithms/balloon.c", "SOURCE_DERIVED_ASM_ALGORITHMS"),
        ("portable/game/simulation/rng.c", "EXISTING_VERIFIED_RUNTIME_ALGORITHM"),
        ("portable/platform/memory.c", "EXISTING_PLATFORM_SERVICE")]:
        path = ROOT / rel
        support_rows.append({"source": rel, "source_sha256": digest(path),
                             "generated": rel, "module_kind": kind, "admitted": False})
    if args.compile:
        for row in rows + support_rows:
            target = ROOT / row["generated"]
            object_path = (output / (Path(row["source"]).stem + "-native.o")) if row in support_rows else target.with_suffix(".o")
            command = [compiler, "-std=c11", "-fsigned-char", "-fno-builtin",
                       "-I", str(ROOT),
                       "-I", str(ROOT / 'portable/whole_program'),
                       "-Werror=implicit-function-declaration", "-Werror=implicit-int",
                       "-c", str(target), "-o", str(object_path)]
            if row['source'] == 'src/root/m25E7.c':
                # Keep the entire original renderer body; its original public
                # name is supplied by the checked native span boundary.
                command.insert(1, '-Dfont_MakeImage=sim_font_make_image_source')
                row['compile_boundary'] = {'kind': 'CHECKED_NATIVE_FONT_RENDER_ENTRY',
                    'source_definition': 'sim_font_make_image_source',
                    'public_provider': 'portable/whole_program/platform/font_blit.c:font_MakeImage',
                    'changes': 'linkage name only; all source statements retained'}
            run = subprocess.run(command, capture_output=True, text=True)
            if run.returncode != 0 and object_path.exists():
                object_path.unlink()
            log = output / (object_path.stem + ".compile.txt")
            log.write_text(run.stdout + run.stderr, encoding="utf-8")
            row["compile"] = {"passed": run.returncode == 0, "command": command,
                              "log": log.relative_to(ROOT).as_posix(), "log_sha256": digest(log)}
            if run.returncode == 0:
                row["compile"]["object_sha256"] = digest(object_path)
                row["compile"]["object"] = object_path.relative_to(ROOT).as_posix()
                nm = str(Path(compiler).with_name("nm.exe")) if Path(compiler).is_absolute() else shutil.which("nm")
                if not nm:
                    raise RuntimeError("nm required to audit actual compiled objects")
                names = subprocess.run([nm, "--format=posix", str(object_path)],
                                       capture_output=True, text=True, check=True)
                row["object_symbols"] = [{"name": fields[0], "kind": fields[1]}
                    for line in names.stdout.splitlines() if len(fields := line.split()) >= 2]
    defined = {}
    undefined = {}
    for row in rows + support_rows:
        for symbol in row.get("object_symbols", []):
            if symbol["kind"] == "U":
                undefined.setdefault(symbol["name"], []).append(row["source"])
            elif symbol["kind"] in {"T", "D", "B", "R", "C"} and not symbol["name"].startswith("."):
                defined.setdefault(symbol["name"], []).append(row["source"])
    declarations_by_name = {}
    for declaration in declarations:
        declarations_by_name.setdefault(declaration["name"], []).append(declaration)
    missing = {}
    for name, modules in sorted(undefined.items()):
        if name in defined:
            continue
        call_sites = [r['source'] for r in rows if name in r['direct_call_identifiers'] and r['source'] in modules]
        classification = ('GLOBAL_STATE' if name in declarations_by_name else
                          'DIRECT_CALL_SERVICE' if call_sites else 'UNCLASSIFIED_OBJECT_OR_HOST_ABI')
        missing[name] = {"required_by": modules,
                         "classification": classification,
                         "direct_call_modules": call_sites,
                         "source_views": declarations_by_name.get(name, [])}
    report = {"schema": "simant-whole-program-migration-v1",
              "claim": "DIAGNOSTIC_ONLY: full TU syntax migration, not behavior or link admission",
              "frozen_oracle_check": {"ready": True, "path": frozen_check.relative_to(ROOT).as_posix(),
                                      "sha256": digest(frozen_check)},
              "generator_sha256": digest(Path(__file__)),
              "behavior_overlay_catalog_sha256": digest(overlay_path),
              "scalar_header_sha256": digest(header),
              "source_module_count": len(rows),
              "code_module_count": sum(r["module_kind"] == "CODE" for r in rows),
              "data_module_count": sum(r["module_kind"] == "DATA" for r in rows),
              "source_function_definition_count": sum(len(r["functions"]) for r in rows),
              "original_lexical_function_count": sum(len(r["original_lexical_functions"]) for r in rows),
              "compile_pass_count": sum(r.get("compile", {}).get("passed", False) for r in rows),
              "modules": rows, "native_support": support_rows, "object_declaration_views": declarations,
              "unprovided_object_symbols": {name: paths for name, paths in sorted(undefined.items()) if name not in defined},
              "unprovided_symbol_contracts": missing,
              "duplicate_object_definitions": {name: paths for name, paths in sorted(defined.items()) if len(paths) > 1},
              "limitation": "Typed views are cataloged, not merged. Original DOS-layout casts and allocations remain explicit portability review debt even when syntax compiles."}
    report['unprovided_contract_class_counts'] = dict(Counter(c['classification'] for c in missing.values()))
    report["compiler"] = {"path": str(Path(compiler).resolve()),
                          "sha256": digest(Path(compiler)),
                          "version": subprocess.run([compiler, "--version"], capture_output=True, text=True, check=True).stdout}
    if args.link:
        # Resolve only actual compiled implementations. Undefined services remain
        # in the relocatable object; do not invent successful placeholder bodies.
        objects = [str(ROOT / r["compile"]["object"]) for r in rows + support_rows
                   if r.get("compile", {}).get("passed")]
        linked = output / "whole_program_core.o"
        command = [compiler, "-r", *objects, "-o", str(linked)]
        result = subprocess.run(command, capture_output=True, text=True)
        log = output / "whole_program_core.link.txt"
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode != 0 and linked.exists():
            linked.unlink()
        report["partial_core_link"] = {"passed": result.returncode == 0,
            "command": command, "log": log.relative_to(ROOT).as_posix(),
            "log_sha256": digest(log), "excluded_source_modules": [r["source"] for r in rows
                if not r.get("compile", {}).get("passed")],
            "claim": "RELOCATABLE_PARTIAL_CORE_ONLY: unresolved services retained, no executable or behavior admission"}
        if result.returncode == 0:
            report["partial_core_link"].update(object=linked.relative_to(ROOT).as_posix(), object_sha256=digest(linked))
            names = subprocess.run([nm, "--format=posix", str(linked)], capture_output=True, text=True, check=True)
            report["partial_core_link"]["undefined_symbols"] = [f[0] for line in names.stdout.splitlines()
                if len(f := line.split()) >= 2 and f[1] == "U"]
    report["inputs"] = initial_inputs
    for row in rows + support_rows:
        report["inputs"][row["source"]] = row["source_sha256"]
        for overlay in row.get("reviewed_behavior_overlays", []):
            report["inputs"][overlay["path"]] = overlay["sha256"]
    report['changed_inputs'] = [rel for rel, expected in report['inputs'].items()
                              if digest(ROOT / rel) != expected]
    report["inputs_stable"] = not report['changed_inputs']
    if not report["inputs_stable"]:
        (output / 'rejected-unstable-inputs.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        raise RuntimeError(f"migration inputs changed during generation/compilation: {report['changed_inputs']}")
    (output / "migration.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("source_module_count", "source_function_definition_count", "compile_pass_count")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
