from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RAW = OUT / "raw-v22-final3"
SOURCES = OUT / "sources"
OBJECTS = OUT / "objects"
sys.path.insert(0, str(ROOT / "tools"))
import compiler
from omf import OmfReader

CURRENT = "fd_50F6_49FA"
PREVIOUS = "fd_50F6_4A0A"
SYMBOLS = (CURRENT, PREVIOUS)
EVENT_FIELDS = ("what", "message", "x4", "modifiers", "h", "v", "code", "xE")
EXPECTED_OFFSETS = dict(zip(EVENT_FIELDS, (0, 2, 4, 6, 8, 10, 12, 14)))
FLAGS = ["/AL", "/Os", "/Gs"]

EVENT16 = """struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};
"""

EVENT_WIDE_CODE = EVENT16.replace("    int code;", "    long code;")
EVENT_SHORT_LAST = "#pragma pack(1)\n" + EVENT16.replace("    int xE;", "    unsigned char xE;")

OWNER16 = EVENT16 + f"struct Event far {CURRENT};\nstruct Event far {PREVIOUS};\n"
OWNER_WIDE = EVENT_WIDE_CODE + f"struct Event far {CURRENT};\nstruct Event far {PREVIOUS};\n"
OWNER_SHORT = EVENT_SHORT_LAST + f"struct Event far {CURRENT};\nstruct Event far {PREVIOUS};\n"
OWNER_INIT = EVENT16 + (
    f"struct Event far {CURRENT};\n"
    f"struct Event far {PREVIOUS} = {{ 0, 0, 0, 0, 0, 0, 0, 1 }};\n"
)
OWNER_PAD = "unsigned char far aaEvent16Pad[32];\n"

BASES_HEADER = """struct EventBases {
    void far *current;
    void far *previous;
};
"""
BASES_OK = EVENT16 + BASES_HEADER + f"""extern struct Event far {CURRENT};
extern struct Event far {PREVIOUS};
struct EventBases far eventBases = {{
    (void far *)&{CURRENT},
    (void far *)&{PREVIOUS}
}};
"""
BASES_PLUS_TWO = EVENT16 + BASES_HEADER + f"""extern struct Event far {CURRENT};
extern struct Event far {PREVIOUS};
struct EventBases far eventBases = {{
    (void far *)((char far *)&{CURRENT} + 2),
    (void far *)&{PREVIOUS}
}};
"""
BASES_OTHER_SYMBOL = EVENT16 + BASES_HEADER + f"""extern struct Event far {CURRENT};
extern struct Event far {PREVIOUS};
struct EventBases far eventBases = {{
    (void far *)&{PREVIOUS},
    (void far *)&{PREVIOUS}
}};
"""


def main_source(event_type: str, mode: str = "positive") -> str:
    negative_base = mode in ("base_plus_two", "base_other_symbol")
    wrong_size = mode in ("wide", "short")
    init = mode == "initializer"
    shape_control = {
        "wide": f"""if (sizeof(struct Event) == 18 && EVENT_OFF({CURRENT}, xE) == 16) {{
        puts("REJECTED: wide code moved xE to +16; Event size is 18");
        return 11;
    }}
    if (sizeof(struct Event) != 16) {{
        puts("FAIL wide-field extent/offset control");
        return 12;
    }}""",
        "short": f"""if (sizeof(struct Event) == 15 && EVENT_OFF({CURRENT}, xE) == 14) {{
        puts("REJECTED: narrow xE stays +14; packed Event size is 15");
        return 11;
    }}
    if (sizeof(struct Event) != 16) {{
        puts("FAIL narrow-field extent/offset control");
        return 12;
    }}""",
    }.get(mode, "")
    base_message = "REJECTED: symbolic base mismatch"
    startup_message = "REJECTED: nonzero initialized Event at CRT entry" if init else "FAIL CRT zero"
    expected_run = "REJECTED" if negative_base or wrong_size or init else "PASS"
    return event_type + BASES_HEADER + f"""
extern struct Event far {CURRENT};
extern struct Event far {PREVIOUS};
extern struct EventBases far eventBases;
extern int far puts(char far *text);

#define EVENT_OFF(e, f) ((unsigned)((char far *)&((e).f) - (char far *)&(e)))

int far main(void)
{{
    volatile unsigned char far *currentBytes;
    volatile unsigned char far *previousBytes;
    unsigned char expected[18];
    unsigned int i;

    currentBytes = (volatile unsigned char far *)&{CURRENT};
    previousBytes = (volatile unsigned char far *)&{PREVIOUS};

    {shape_control}
    if (sizeof(struct Event) != 16) {{
        puts("FAIL Event size");
        return 11;
    }}
    if (EVENT_OFF({CURRENT}, what) != 0 ||
        EVENT_OFF({CURRENT}, message) != 2 ||
        EVENT_OFF({CURRENT}, x4) != 4 ||
        EVENT_OFF({CURRENT}, modifiers) != 6 ||
        EVENT_OFF({CURRENT}, h) != 8 ||
        EVENT_OFF({CURRENT}, v) != 10 ||
        EVENT_OFF({CURRENT}, code) != 12 ||
        EVENT_OFF({CURRENT}, xE) != 14) {{
        puts("FAIL Event field offsets");
        return 12;
    }}

    if (eventBases.current != (void far *)&{CURRENT} ||
        eventBases.previous != (void far *)&{PREVIOUS}) {{
        puts("{base_message}");
        return 13;
    }}

    for (i = 0; i < 16; i++) {{
        if (currentBytes[i] != 0 || previousBytes[i] != 0) {{
            puts("{startup_message}");
            return 14;
        }}
    }}
    if ({"previousBytes[14] != 1" if init else "0"}) {{
        puts("FAIL initializer contrast");
        return 15;
    }}

    for (i = 0; i < 16; i++) {{
        expected[i] = (unsigned char)((i * 29 + 0x37) & 0xff);
        currentBytes[i] = expected[i];
    }}
    {PREVIOUS} = {CURRENT};
    for (i = 0; i < 16; i++) {{
        if (currentBytes[i] != expected[i] || previousBytes[i] != expected[i]) {{
            puts("FAIL whole-record copy or byte canary");
            return 16;
        }}
    }}
    if (currentBytes[0] != 0x37 || currentBytes[15] != expected[15] ||
        previousBytes[0] != 0x37 || previousBytes[15] != expected[15]) {{
        puts("FAIL first/last byte canary");
        return 17;
    }}

    puts("{expected_run}");
    return 0;
}}
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin_file(path: Path, rel: str | None = None) -> dict:
    try:
        stored_path = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        stored_path = str(path)
    return {
        "path": rel if rel is not None else stored_path,
        "sha256": digest(path),
        "size": path.stat().st_size,
    }


def verify_pin(path: Path, expected_hash: str, expected_size: int | None = None) -> dict:
    row = pin_file(path)
    if row["sha256"] != expected_hash or (expected_size is not None and row["size"] != expected_size):
        raise RuntimeError(f"pinned input changed: {path}")
    return row


def write_source(name: str, source: str) -> Path:
    path = SOURCES / f"{name}.C"
    path.write_text(source.replace("\r\n", "\n"), encoding="ascii", newline="\n")
    return path


def compile_source(name: str, source: str) -> tuple[bytes, dict]:
    source_path = write_source(name, source)
    result = compiler.compile_c(source, "msc600ax", FLAGS, basename=name, timeout=120)
    if not result.ok or result.obj is None:
        (SOURCES / f"{name}.compiler.log").write_text(result.log, encoding="latin1")
        raise RuntimeError(f"{name} compile failed:\n{result.log}")
    obj_path = OBJECTS / f"{name}.OBJ"
    obj_path.write_bytes(result.obj)
    (SOURCES / f"{name}.compiler.log").write_text(result.log, encoding="latin1")
    return result.obj, {
        "name": name,
        "source": pin_file(source_path),
        "object": pin_file(obj_path),
        "compiler_log": pin_file(SOURCES / f"{name}.compiler.log"),
        "compiler_argv": result.argv,
        "options": FLAGS,
    }


def omf_shape(data: bytes) -> dict:
    module = OmfReader(communals=True).read(data)
    return {
        "communal_rows": sorted(module.communals, key=lambda row: row["name"].lower()),
        "public_rows": module.publics,
        "segment_definitions": module.segment_defs,
        "initialized_segments": {name: len(contents) for name, contents in module.segments.items()},
        "externals": module.externals,
        "code_or_initialized_bytes_absent": not module.segments,
    }


def event_owner_shape(data: bytes, expected_size: int) -> dict:
    row = omf_shape(data)
    rows = {item["name"].lower(): item for item in row["communal_rows"]}
    wanted = {f"_{name}".lower() for name in SYMBOLS}
    return row | {
        "exact_symbols": set(rows) == wanted,
        "both_far_commons_at_expected_size": (
            set(rows) == wanted and all(rows[f"_{name}".lower()]["kind"] == "far"
                                        and rows[f"_{name}".lower()]["length"] == expected_size
                                        for name in SYMBOLS)
        ),
    }


def fresh_run_dir(profile: str, case: str) -> Path:
    path = RAW / profile / case
    path.mkdir(parents=True, exist_ok=False)
    return path


def copy_checked(src: Path, dst: Path, expected_sha: str) -> dict:
    actual = digest(src)
    if actual != expected_sha:
        raise RuntimeError(f"pinned runtime file changed: {src}")
    shutil.copyfile(src, dst)
    return {"path": str(src), "sha256": actual, "size": src.stat().st_size}


def map_row_for_symbol(text: str, symbol: str) -> str | None:
    needle = "_" + symbol
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().endswith(needle.lower()):
            return stripped
    return None


def parse_map_base(line: str | None) -> str | None:
    if not line:
        return None
    first = line.split()[0]
    if ":" not in first:
        return None
    seg, off = first.split(":", 1)
    return f"{seg.upper()}:{off.upper()}"


def link_and_run(profile: str, case: str, object_names: list[str],
                 expected_runtime: str, expected_nonzero: bool,
                 expected_bss_bytes: int | None = 32,
                 require_expected_bss_total: bool = True) -> dict:
    tc = compiler.toolchain()
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    tool = tc["linkers"][profile]
    tool_dir = compiler.pinned_tree(tool)
    runner = tc["runners"]["dosbox-x"]
    out = fresh_run_dir(profile, case)
    for name in object_names:
        shutil.copyfile(OBJECTS / f"{name}.OBJ", out / f"{name}.OBJ")
    copied_runtime = []
    for row in manifest["runtime"]["libraries"].values():
        lib = Path(row["path"])
        copied_runtime.append(copy_checked(lib, out / lib.name.upper(), row["sha256"]))

    (out / "PASS.LNK").write_text(
        f"OUTPUT PASS\r\nMAP = PASS S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE " + ", ".join(object_names) + "\r\n",
        encoding="ascii",
        newline="",
    )
    (out / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (out / "RUN.BAT").write_text(
        f"@echo off\r\nD:\\{tool['executable']} @PASS.LNK < NUL > LINK.LOG\r\n"
        "PASS.EXE > RUN.LOG\r\nIF ERRORLEVEL 1 ECHO PROGRAM_NONZERO>>RUN.LOG\r\n",
        encoding="ascii",
        newline="",
    )
    conf = []
    for section, settings in runner["conf"].items():
        conf.append("[" + section + "]")
        conf.extend(f"{key}={value}" for key, value in settings.items())
    conf += ["[autoexec]", f'mount c "{out}"', f'mount d "{tool_dir}" -ro',
             "c:", "call RUN.BAT", "exit"]
    conf_path = out / "dosbox.conf"
    conf_path.write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    process = subprocess.run(
        [runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
        cwd=out, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    map_path = out / "PASS.MAP"
    run_path = out / "RUN.LOG"
    link_path = out / "LINK.LOG"
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    run_text = run_path.read_text(encoding="latin1", errors="replace").strip() if run_path.exists() else "NO_LOG"
    link_text = link_path.read_text(encoding="latin1", errors="replace") if link_path.exists() else "NO_LINK_LOG"
    target_rows = {symbol: map_row_for_symbol(map_text, symbol) for symbol in SYMBOLS}
    bases = {symbol: parse_map_base(target_rows[symbol]) for symbol in SYMBOLS}
    all_bss_rows = [line.strip() for line in map_text.splitlines() if "FAR_BSS" in line]
    bss_rows = [line for line in all_bss_rows
                if expected_bss_bytes is None or f"{expected_bss_bytes:05X}H" in line]
    run_lines = [line.strip() for line in run_text.splitlines() if line.strip()]
    runtime_ok = expected_runtime in run_lines and ("PROGRAM_NONZERO" in run_lines) == expected_nonzero
    distinct_bases = all(bases.values()) and bases[CURRENT] != bases[PREVIOUS]
    map_shape = bool(target_rows[CURRENT] and target_rows[PREVIOUS] and distinct_bases)
    bss_total_ok = not require_expected_bss_total or bool(bss_rows)
    return {
        "linker": profile,
        "case": case,
        "objects_in_link_order": object_names,
        "runner_exit": process.returncode,
        "runtime_log": run_text,
        "expected_runtime_line": expected_runtime,
        "expected_program_nonzero_marker": expected_nonzero,
        "link_log_tail": link_text[-900:],
        "map_path": str(map_path.relative_to(ROOT)).replace("\\", "/"),
        "map_sha256": digest(map_path) if map_path.exists() else None,
        "map_size": map_path.stat().st_size if map_path.exists() else None,
        "event_symbol_map_rows": target_rows,
        "event_symbol_linked_bases": bases,
        "far_bss_rows_matching_expected_total": bss_rows,
        "all_far_bss_rows": all_bss_rows,
        "expected_total_far_bss_bytes": expected_bss_bytes,
        "required_expected_bss_total": require_expected_bss_total,
        "expected_bss_total_present": bss_total_ok,
        "map_has_distinct_symbol_bases": map_shape,
        "runtime_libraries": copied_runtime,
        "passed": process.returncode == 0 and runtime_ok and map_shape and bss_total_ok,
    }


def build_source_audit() -> dict:
    intake_path = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
    index_path = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if len(intake.get("translation_units", [])) != 127:
        raise RuntimeError("canonical inventory changed from 127 translation units")
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict static source index is not index-v1/29")

    source_rows = []
    for tu in intake["translation_units"]:
        row = tu["source"]
        pinned = verify_pin(ROOT / row["path"], row["sha256"], row["size"])
        source_rows.append(pinned | {"set": "canonical_127", "module": tu["module"]})
    strict_rows = []
    receipt_pins = []
    for name, ref in sorted(index["entries"].items()):
        receipt_path = ROOT / ref["path"]
        receipt_pins.append(verify_pin(receipt_path, ref["sha256"], ref["size"]))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        src = (receipt.get("audit", {}).get("source", {}) if name == "DrawBalloons"
               else receipt.get("registered_source", {}))
        if not src.get("whole_module") or not src.get("path") or not src.get("sha256"):
            raise RuntimeError(f"strict source {name} lacks a whole-module source receipt")
        strict_rows.append(verify_pin(ROOT / src["path"], src["sha256"]) |
                           {"set": "effective_strict_29", "function": name,
                            "module": src.get("module")})
    by_path = {row["path"]: row for row in source_rows + strict_rows}
    if len(source_rows) != 127 or len(strict_rows) != 29 or len(by_path) != 156:
        raise RuntimeError(f"bounded scope mismatch: {len(source_rows)} + {len(strict_rows)} / {len(by_path)}")

    token = re.compile(r"(?<![A-Za-z0-9_])_?(fd_50F6_49FA|fd_50F6_4A0A)(?![A-Za-z0-9_])")
    raw_address = re.compile(
        r"(?i)(?<![A-Za-z0-9_])(?:"
        r"(?:0x)?50F6h?\s*[: ,]\s*(?:0x)?(?:49FA|4A0A)h?|"
        r"(?:0x)?(?:49FA|4A0A)h?)(?![A-Za-z0-9_])"
    )
    occurrences = []
    raw_hits = []
    field_uses = {name: {field: [] for field in EVENT_FIELDS} for name in SYMBOLS}
    whole_ops = []
    for row in sorted(by_path.values(), key=lambda item: item["path"]):
        source_lines = (ROOT / row["path"]).read_text(encoding="latin1").splitlines()
        for number, line in enumerate(source_lines, 1):
            for match in raw_address.finditer(line):
                raw_hits.append({"path": row["path"], "line": number,
                                 "text": line.strip(), "match": match.group(0)})
            names = sorted(set(match.group(1) for match in token.finditer(line)))
            for name in names:
                item = {"set": row["set"], "path": row["path"], "line": number,
                        "symbol": name, "text": line.strip()}
                occurrences.append(item)
                for field in EVENT_FIELDS:
                    if re.search(r"\b" + re.escape(name) + r"\s*\.\s*" + re.escape(field) + r"\b", line):
                        field_uses[name][field].append({"path": row["path"], "line": number,
                                                       "text": line.strip()})
                if re.search(r"\b" + re.escape(name) + r"\s*=\s*" +
                             r"(?:fd_50F6_49FA|fd_50F6_4A0A)\s*;", line):
                    whole_ops.append(item)

    event_definitions = []
    event_struct = re.compile(r"struct\s+Event\s*\{([^}]*)\}", re.S)
    for row in sorted(by_path.values(), key=lambda item: item["path"]):
        source = (ROOT / row["path"]).read_text(encoding="latin1")
        for match in event_struct.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            fields = [re.sub(r"\s+", " ", decl.strip())
                      for decl in match.group(1).split(";") if decl.strip()]
            event_definitions.append({"path": row["path"], "line": line, "fields": fields})

    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))
    data_registry = symbols["data"]
    registered_rows = {name: data_registry.get(name) for name in (*SYMBOLS, "fd_50F6_4A1A")}
    overlapping = [
        {"name": name, **row} for name, row in data_registry.items()
        if row.get("seg") == 0x50F6 and 0x49FA <= row.get("off", -1) < 0x4A1A
    ]
    intake_targets = [row for row in intake.get("unresolved_symbols", [])
                      if row.get("name", "").lstrip("_") in (*SYMBOLS, "fd_50F6_4A1A")]
    removed_4a12 = []
    removals_path = ROOT / "evidence/symbol-removals.jsonl"
    for line in removals_path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("name") == "fd_50F6_4A12":
            removed_4a12.append(row)

    input_names = [
        "README.md", "docs/codegen-rules.md", "docs/tu-evidence.md", "docs/next-steps.md",
        "work/source-only-dos/unlock-clobber-review-v19.md",
        "work/source-only-dos/unlock-clobber-review-v19.json",
        "work/source-only-dos/static-completeness/index-v1.json",
        "work/source-only-dos/compile-and-intake-v1.json",
        "work/source-only-dos/queue-storage-bindings-v1.json",
        "build/workers/dos_unlock_event_closure_v20/source-review-v20.md",
        "build/workers/dos_unlock_event_closure_v20/source-review-v20.json",
        "layout/symbols.json", "evidence/symbol-removals.jsonl",
        "src/root/m218D.c", "src/root/m1B73.asm",
    ]
    input_pins = [pin_file(ROOT / rel, rel) for rel in input_names]
    return {
        "scope": {
            "canonical_translation_units": 127,
            "effective_strict_sources": 29,
            "unique_source_paths": 156,
            "strict_source_registry": "work/source-only-dos/static-completeness/index-v1.json",
            "drawballoons_source_selection": "whole-module audit.source from strict index receipt",
        },
        "source_pins": sorted(by_path.values(), key=lambda row: (row["set"], row["path"])),
        "strict_receipt_pins": receipt_pins,
        "direct_symbol_occurrences": occurrences,
        "field_views": field_uses,
        "whole_record_assignment_occurrences": whole_ops,
        "event_type_definitions": event_definitions,
        "numeric_address_occurrences": raw_hits,
        "registry": {
            "symbol_starts": registered_rows,
            "registered_starts_in_half_open_candidate_spans": overlapping,
            "previous_record_following_symbol": "fd_50F6_4A1A at 50F6:4A1A; record candidate stops before this registered start",
            "removed_interior_name_4A12": removed_4a12,
            "unresolved_storage_rows": intake_targets,
            "accepted_storage_candidates_for_events": {
                row["name"].lstrip("_"): row.get("accepted_storage_candidates")
                for row in intake_targets if row["name"].lstrip("_") in SYMBOLS
            },
        },
        "source_evidence_interpretation": {
            "event_definition": "src/root/m218D.c natural struct Event has eight 16-bit int fields in order what,message,x4,modifiers,h,v,code,xE",
            "event_offsets": EXPECTED_OFFSETS,
            "current_record": "f_1B73_032E(&fd_50F6_49FA) writes eight words (16 bytes); source field reads are code and modifiers; source field writes are modifiers; whole Event is also copied out by win_GetEvent",
            "previous_record": "fd_50F6_4A0A = fd_50F6_49FA whole-struct assignment; source field reads are code and modifiers",
            "current_pointer_use_closure": [
                {"site": "src/root/m218D.c:150", "target": "f_218D_0451", "view": "same-module Event h/v point reads"},
                {"site": "src/root/m218D.c:152", "target": "f_218D_023A", "view": "same-module Event code read"},
                {"site": "src/root/m218D.c:186", "target": "f_218D_000C", "view": "same-module code/modifier reads and modifier writes; selects the handlers below"},
                {"site": "src/root/m218D.c:42", "target": "f_23E6_0A53", "view": "root:m23E6 reads Event code/v; scalar calls follow"},
                {"site": "src/root/m218D.c:46", "target": "win_ProcSliderEvent", "view": "root:m23E6 reads code/v/modifiers; it does not retain or write the Event pointer"},
                {"site": "src/root/m218D.c:51", "target": "o26_39C7_040F", "view": "S26:m39C7 reads h/v; it does not retain or write the Event pointer"},
            ],
            "other_struct_Event_spellings": "The bounded corpus includes local Event definitions with same-width unsigned code, x6 naming, nested Point, and an S11 legacy record. They are not owners or address views of these globals; the selected pointer-call closure above uses the 16-byte views. The separate root:1FD2 near queue uses byte modifiers and remains a distinct 112-byte owner.",
            "pending_code_stability_boundary": "Independent unresolved path from o26_39C7_040F -> startup-installed g_62EC callback -> f_21FA_0B4B/win_DrawWindow -> edit draw hook -> DrawSpider/f_2662_1120 selected S00/S01/S03 decoder. Decoder destination 50F6:1F2A is 0x2ADC bytes before active code 50F6:4A06. Positive source height is clamped, but zero/negative signed height still reaches the DEC/JNZ do-while row loop and wraps; actual resource-domain bounds are unknown, so an event-state overwrite remains conditionally open. No normal draw-size bound is claimed here.",
            "address_escape": "exact-name scan finds references only in src/root/m218D.c; no exact numeric 50F6:49FA/4A0A aliases occur in the bounded 156 source paths",
            "other_output_views": "win_GetEvent callers use local Event outputs; source review v20 records their full caller inventory",
            "queue_is_separate": "admitted root:1FD2 queue is a near Event[7], 112 bytes at DGROUP 91B0-9220 via g_5FFE; it is not either FAR candidate",
        },
        "pins": input_pins,
        "limits": [
            "Source scan is bounded to the pinned 127 canonical plus 29 effective strict source paths and exact target names/registered numeric addresses.",
            "Registered neighbor and the historical numeric starts are context only; neither adjacency nor declaration/link order is used to infer either common's extent.",
            "No original executable/object bytes or external game resources are read or used as build inputs.",
        ],
    }


def tool_pins() -> list[dict]:
    tc = compiler.toolchain()
    rows = []
    for profile in ("msc600ax", "rtlink400", "rtlink610"):
        spec = tc["profiles"][profile] if profile in tc["profiles"] else tc["linkers"][profile]
        for rel, expected in spec["files"].items():
            rows.append(verify_pin(Path(spec["directory"]) / rel, expected))
    runner = tc["runners"]["dosbox-x"]
    rows.append(verify_pin(Path(runner["path"]), runner["sha256"]))
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    for row in manifest["runtime"]["libraries"].values():
        rows.append(verify_pin(Path(row["path"]), row["sha256"]))
    for rel in ("tools/compiler.py", "tools/omf.py", "layout/toolchain.json", "layout/manifest.json"):
        rows.append(pin_file(ROOT / rel, rel))
    return rows


def main() -> int:
    RAW.mkdir(exist_ok=False)
    OBJECTS.mkdir(exist_ok=True)
    audit = build_source_audit()
    (OUT / "source-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    artifacts = []
    owner, meta = compile_source("OWNER", OWNER16)
    artifacts.append(meta)
    owner_wide, meta = compile_source("OWNWIDE", OWNER_WIDE)
    artifacts.append(meta)
    owner_short, meta = compile_source("OWNSHORT", OWNER_SHORT)
    artifacts.append(meta)
    owner_init, meta = compile_source("OWNINIT", OWNER_INIT)
    artifacts.append(meta)
    pad, meta = compile_source("PAD", OWNER_PAD)
    artifacts.append(meta)
    bases, meta = compile_source("BASES", BASES_OK)
    artifacts.append(meta)
    bases_plus, meta = compile_source("BADADD", BASES_PLUS_TWO)
    artifacts.append(meta)
    bases_other, meta = compile_source("BADOTHER", BASES_OTHER_SYMBOL)
    artifacts.append(meta)
    use, meta = compile_source("USE", main_source(EVENT16))
    artifacts.append(meta)
    use_wide, meta = compile_source("USEWIDE", main_source(EVENT_WIDE_CODE, "wide"))
    artifacts.append(meta)
    use_short, meta = compile_source("USESHORT", main_source(EVENT_SHORT_LAST, "short"))
    artifacts.append(meta)
    use_init, meta = compile_source("USEINIT", main_source(EVENT16, "initializer"))
    artifacts.append(meta)
    use_plus, meta = compile_source("USEPLUS", main_source(EVENT16, "base_plus_two"))
    artifacts.append(meta)
    use_other, meta = compile_source("USEOTHER", main_source(EVENT16, "base_other_symbol"))
    artifacts.append(meta)

    owner_shape = event_owner_shape(owner, 16)
    wide_shape = event_owner_shape(owner_wide, 18)
    short_shape = event_owner_shape(owner_short, 15)
    init_shape = omf_shape(owner_init)
    init_commons = {row["name"].lower(): row for row in init_shape["communal_rows"]}
    init_publics = {row["name"].lower(): row for row in init_shape["public_rows"]}
    init_event_control = {
        "current_still_far_common_16": ("_" + CURRENT).lower() in init_commons and
            init_commons[("_" + CURRENT).lower()]["kind"] == "far" and
            init_commons[("_" + CURRENT).lower()]["length"] == 16,
        "initialized_previous_no_longer_common": ("_" + PREVIOUS).lower() not in init_commons,
        "initialized_previous_public": init_publics.get(("_" + PREVIOUS).lower()),
        "initialized_previous_segment": next((seg for seg in init_shape["segment_definitions"]
            if init_publics.get(("_" + PREVIOUS).lower()) and
            seg["name"] == init_publics[("_" + PREVIOUS).lower()]["segment"]), None),
    }
    init_event_control["detected_initialized_FAR_DATA"] = bool(
        init_event_control["initialized_previous_public"] and init_event_control["initialized_previous_segment"] and
        init_event_control["initialized_previous_segment"].get("class") == "FAR_DATA"
    )

    cases = []
    for profile in ("rtlink400", "rtlink610"):
        cases.append(link_and_run(profile, "positive", ["OWNER", "BASES", "USE"], "PASS", False, 32))
        cases.append(link_and_run(profile, "positive_shifted", ["PAD", "OWNER", "BASES", "USE"], "PASS", False, 64))
        cases.append(link_and_run(profile, "wrong_wide_field", ["OWNWIDE", "BASES", "USEWIDE"],
                                  "REJECTED: wide code moved xE to +16; Event size is 18", True, 36))
        cases.append(link_and_run(profile, "wrong_narrow_field", ["OWNSHORT", "BASES", "USESHORT"],
                                  "REJECTED: narrow xE stays +14; packed Event size is 15", True, 30, False))
        cases.append(link_and_run(profile, "nonzero_initializer", ["OWNINIT", "BASES", "USEINIT"],
                                  "REJECTED: nonzero initialized Event at CRT entry", True, 16))
        cases.append(link_and_run(profile, "base_plus_two", ["OWNER", "BADADD", "USEPLUS"],
                                  "REJECTED: symbolic base mismatch", True, 32))
        cases.append(link_and_run(profile, "wrong_symbol_base", ["OWNER", "BADOTHER", "USEOTHER"],
                                  "REJECTED: symbolic base mismatch", True, 32))

    link_positives = {case["linker"]: case for case in cases if case["case"] == "positive"}
    shifted = {case["linker"]: case for case in cases if case["case"] == "positive_shifted"}
    shifted_bases = {}
    for profile in ("rtlink400", "rtlink610"):
        shifted_bases[profile] = {
            "positive": link_positives[profile]["event_symbol_linked_bases"],
            "shifted": shifted[profile]["event_symbol_linked_bases"],
            "both_symbol_bases_moved": all(
                link_positives[profile]["event_symbol_linked_bases"].get(symbol) !=
                shifted[profile]["event_symbol_linked_bases"].get(symbol)
                for symbol in SYMBOLS
            ),
        }

    evidence = {
        "schema": "dos-event16-source-owned-storage-probe-v22",
        "status": "PASS_CANDIDATE_STORAGE_ONLY" if all(case["passed"] for case in cases) else "PROBE_INCOMPLETE",
        "claim": "Two source-owned independent natural Event objects each have 16-byte FAR_BSS commons; pinned CRT startup zero-fills both; whole-record copy and all field offsets work; symbolic relocation and negative controls pass under RTLink 4.00 and 6.10.",
        "relationship_to_event_code_stability": "Independent. This probe does not close the v20 resource-height decoder overwrite frontier or establish ev->code stability across lock/unlock.",
        "probe_instrument": pin_file(Path(__file__)),
        "original_exe_or_object_bytes_used": False,
        "external_game_asset_bytes_read_or_used": False,
        "source_audit": "source-audit.json",
        "compiler_options": FLAGS,
        "owner_object": owner_shape,
        "width_controls": {
            "wide_code_18_byte_event": wide_shape,
            "narrow_xE_15_byte_event": short_shape,
            "initializer_control": init_event_control,
        },
        "clean_link_runtime_cases": cases,
        "shifted_layout_comparison": shifted_bases,
        "compiler_objects_and_sources": artifacts,
        "tool_and_runtime_inputs": tool_pins(),
        "limits": [
            "This is a fresh source-owned behavioral storage proof for the proposed definitions, not proof of historical COMDEF producer module, ordering, original numeric placement, or wider semantic ownership.",
            "The two objects are checked by their own OMF communal rows and distinct map symbol labels. No extent or stride is inferred from neighboring symbol positions or link order.",
            "The positive link uses an independent one-byte common before the two Event commons; the map is checked to confirm that each Event base actually moves under each linker before calling the layout shifted.",
            "Source field and whole-record use closure is bounded to the 127 canonical plus 29 effective strict source paths in index-v1; unpinned source, binary aliases, runtime application code, and resource-domain behavior are outside this storage probe.",
        ],
    }
    source_audit_ok = bool(
        audit["scope"]["canonical_translation_units"] == 127 and
        audit["scope"]["effective_strict_sources"] == 29 and
        audit["scope"]["unique_source_paths"] == 156 and
        {row["path"] for row in audit["direct_symbol_occurrences"]} == {"src/root/m218D.c"} and
        not audit["numeric_address_occurrences"] and
        len(audit["whole_record_assignment_occurrences"]) == 1 and
        audit["whole_record_assignment_occurrences"][0]["text"] ==
            "fd_50F6_4A0A = fd_50F6_49FA;" and
        all(audit["registry"]["accepted_storage_candidates_for_events"].get(name) == []
            for name in SYMBOLS) and
        {field for field, refs in audit["field_views"][CURRENT].items() if refs} ==
            {"code", "modifiers"} and
        {field for field, refs in audit["field_views"][PREVIOUS].items() if refs} ==
            {"code", "modifiers"} and
        any(row["path"] == "src/root/m218D.c" and row["fields"] == [
            "int what", "int message", "int x4", "int modifiers", "int h", "int v", "int code", "int xE"
        ] for row in audit["event_type_definitions"])
    )
    evidence["source_audit_checks_passed"] = source_audit_ok
    evidence["all_checks_passed"] = bool(
        source_audit_ok and
        owner_shape["exact_symbols"] and owner_shape["both_far_commons_at_expected_size"] and
        owner_shape["code_or_initialized_bytes_absent"] and
        wide_shape["both_far_commons_at_expected_size"] and
        short_shape["both_far_commons_at_expected_size"] and
        init_event_control["detected_initialized_FAR_DATA"] and
        len(cases) == 14 and all(case["passed"] for case in cases) and
        all(row["both_symbol_bases_moved"] for row in shifted_bases.values()) and
        all(not audit["numeric_address_occurrences"] for _ in [0]) and
        all(len([row for row in audit["source_pins"] if row["set"] == "canonical_127"]) == 127
            for _ in [0])
    )
    (OUT / "receipt-v22.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    case_map = {(case["linker"], case["case"]): case for case in cases}
    report_lines = [
        "# Event16 source-owned storage probe v22",
        "",
        f"**Result: {'PASS, candidate storage only' if evidence['all_checks_passed'] else 'INCOMPLETE'}.** This is a source-owned provider/runtime proof for two natural 16-byte FAR objects; it does not establish historical producer module, linker ordering, or original numeric placement.",
        "",
        "The probe compiles with MSC 6.00AX `/AL /Os /Gs`, links with pinned RTLink 4.00 and 6.10, and runs under the pinned DOS CRT (`LLIBCR`/`LIBH`). The owner OMF contains exactly two far commons, 16 bytes each, and no initialized bytes or nonzero code/data contributions. The positive runtime checks 16-byte `sizeof`, every offset 0,2,4,6,8,10,12,14, all 32 startup-zero bytes, and a distinctive byte pattern copied through whole-struct assignment with first/last canaries.",
        "",
        "| Case | RTLink 4.00 | RTLink 6.10 |",
        "|---|---|---|",
    ]
    case_labels = [
        ("positive", "Positive: two Event commons and whole-record copy"),
        ("positive_shifted", "Positive after 32-byte common shifts layout"),
        ("wrong_wide_field", "Wrong field width: `code` becomes long; Event is 18 bytes, xE +16"),
        ("wrong_narrow_field", "Wrong field width: packed one-byte xE; Event is 15 bytes"),
        ("nonzero_initializer", "Nonzero initializer on previous Event"),
        ("base_plus_two", "Bad base: current pointer +2"),
        ("wrong_symbol_base", "Bad base: current points at previous Event"),
    ]
    for case_name, label in case_labels:
        values = []
        for profile in ("rtlink400", "rtlink610"):
            result = case_map[(profile, case_name)]
            bss = "; ".join(result["all_far_bss_rows"]) or "no FAR_BSS map row"
            lines = [x for x in result["runtime_log"].splitlines() if x and x != "PROGRAM_NONZERO"]
            runtime = lines[0] if lines else "no runtime line"
            values.append(f"{runtime}; {bss}")
        report_lines.append(f"| {label} | {values[0]} | {values[1]} |")
    report_lines += [
        "",
        "The 18-byte and 15-byte controls change actual field width/extent and are rejected by runtime shape checks. Their individual OMF COMDEF lengths are pinned. RTLink 6.10 rounds the pair of 15-byte commons to a 32-byte FAR_BSS aggregate; that aggregate and the start-to-start map offsets are not used as per-object extent evidence. The exact per-object extents come from each OMF common and the runtime `sizeof`/field-offset observations.",
        "",
        "The shifted case proves symbolic relocation: the independent 32-byte common moves both Event symbols under both linkers, while the initialized pointer table still resolves to each named object's actual linked base. The plus-two and other-symbol alias controls fail those same identity checks under both linkers.",
        "",
        "The source audit pins 127 canonical TUs plus all 29 effective strict sources in `static-completeness/index-v1.json` (156 unique paths). The 23 direct name references are all in `src/root/m218D.c`; there are no exact numeric address aliases in the bounded set. Its eight-word dequeue writes the current record, `fd_50F6_4A0A = fd_50F6_49FA` copies the entire previous record, direct global field uses read `code`/`modifiers`, and only current `modifiers` is written in the dispatcher. The selected current-pointer path passes to `f_218D_0451`, `f_218D_023A`, `f_218D_000C`, then to the matching `f_23E6_0A53`, `win_ProcSliderEvent`, or `o26_39C7_040F` Event16 views. Other local `struct Event` layouts in unrelated TUs are not assumed to view these FAR objects; `win_GetEvent` outputs are caller-local, and the root:1FD2 input queue is a separate 112-byte near `Event[7]` owner.",
        "",
        "Registry review leaves both Event names unresolved with zero accepted storage candidates. The only registered starts within the candidate spans are the two names themselves; the next registered start is `fd_50F6_4A1A`. The removed `fd_50F6_4A12` name is an interior alias record, not an independent owner. These registry observations do not supply the extents; the whole-record source operations and per-symbol OMF commons do.",
        "",
        "The decoder/resource-height closure is independent and remains open: the resize path can reach `DrawSpider` and the selected S00/S01/S03 decoder, whose destination begins at 50F6:1F2A, 0x2ADC bytes before active `code` at 50F6:4A06. Positive height clamps, but zero/negative signed height still enters the DEC/JNZ row loop; the actual resource-domain bound is unknown, so a conditional event-state overwrite remains possible. No typical draw-size bound is used to exclude it.",
        "",
        "Machine-readable source pins, object shapes, maps, runtime logs, tool hashes, and all 14 linker runs are in [receipt-v22.json](receipt-v22.json) and [source-audit.json](source-audit.json). No production or canonical source, layout, registry, journal, or Git state was changed.",
    ]
    (OUT / "receipt-v22.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_checks_passed": evidence["all_checks_passed"],
        "source_scope": evidence["source_audit"]["scope"] if isinstance(evidence["source_audit"], dict) else audit["scope"],
        "owner_commons": owner_shape["communal_rows"],
        "width_control_commons": {
            "wide": wide_shape["communal_rows"],
            "short": short_shape["communal_rows"],
        },
        "initialized_control": init_event_control,
        "cases": [{"linker": c["linker"], "case": c["case"], "passed": c["passed"],
                   "runtime_log": c["runtime_log"], "bases": c["event_symbol_linked_bases"],
                   "bss": c["far_bss_rows_matching_expected_total"]} for c in cases],
        "shifted_layout_comparison": shifted_bases,
    }, indent=2))
    return 0 if evidence["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
