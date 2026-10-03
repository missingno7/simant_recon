"""Guarded source and typed-owner study for DOS UI resource globals.

Reads only manifest-listed C sources, receipts, JSON metadata and pinned compiler/linker
inputs. It never opens game images, objects or resource/database bytes.
"""
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
OUT = ROOT / "build/workers/dos_v17_fresh/uires"
OUT.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUT / "UIRES.V17.JSON"
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

INTAKE = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
INDEX = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
SYMBOLS = ROOT / "layout/symbols.json"
MANIFEST = ROOT / "layout/manifest.json"
CROSS_VERSION = ROOT / "evidence/cross_version/decisions.json"
PROVIDER = ROOT / "work/source-only-dos/providers/ui-resource-state.c"
FLAGS = ["/AL", "/Os", "/Gs"]

DATA_TARGETS = ("win_numOfWindows", "win_numOfColors", "win_numOfGroups",
                "fd_50F6_3B4C", "fd_50F6_3B58", "fd_50F6_3B5C")
ARRAY_TARGETS = ("win_colors", "win_drawHooks", "win_offsets")
SUPPORT = ("win_LoadAllWindows", "win_LoadWindow", "win_SetWinDrawHook",
           "win_DrawWindow", "win_SetColorNum", "win_SetColorFromObj",
           "clip_Push", "clip_Pop", "f_19DC_001A", "f_19DC_0148",
           "f_205F_0004", "db_LoadObject", "db_PurgeObject", "DBRecall",
           "LoadGame", "SaveGame", "db_SaveObject", "db_StoreObject")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    actual = sha(raw)
    if expected is not None and actual != expected:
        raise RuntimeError(f"stale tool/source input pin: {path}")
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(path.resolve()).replace("\\", "/")
    return {"path": shown, "sha256": actual, "size": len(raw)}


def repo_path(path: str) -> Path:
    return ROOT / path.replace("\\", "/")


def checked_pin(row: dict, label: str) -> dict:
    got = pin(repo_path(row["path"]))
    if got["sha256"] != row["sha256"] or got["size"] != row["size"]:
        raise RuntimeError(f"stale {label} pin: {row['path']}")
    return got


def source_sets() -> tuple[list[dict], list[dict], list[dict]]:
    intake = json.loads(INTAKE.read_text(encoding="utf-8"))
    if len(intake.get("translation_units", [])) != 127:
        raise RuntimeError("canonical manifest source count changed")
    canonical = [checked_pin(tu["source"], "canonical") | {"module": tu["module"]}
                 for tu in intake["translation_units"]]
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict source index is not the expected 29-entry set")
    receipts = [pin(INDEX)]
    effective = []
    for function, ref in sorted(index["entries"].items()):
        receipt_pin = checked_pin(ref, "strict receipt")
        receipts.append(receipt_pin)
        receipt = json.loads(repo_path(ref["path"]).read_text(encoding="utf-8"))
        source = receipt.get("registered_source", {})
        if function == "DrawBalloons":
            source = receipt.get("audit", {}).get("source", {})
        if not source.get("whole_module") or not source.get("path") or not source.get("sha256"):
            raise RuntimeError(f"missing effective whole-module source for {function}")
        source_pin = pin(repo_path(source["path"]))
        if source_pin["sha256"] != source["sha256"]:
            raise RuntimeError(f"stale effective source hash for {function}")
        effective.append(source_pin | {"module": source.get("module"), "function": function,
                                      "role": ("corrected effective whole module" if function == "DrawBalloons"
                                               else "registered effective whole module")})
    if len({r["path"] for r in canonical + effective}) != 156:
        raise RuntimeError("expected 156 unique source paths")
    return canonical, effective, receipts


def access_kind(name: str, line: str) -> str:
    q = re.escape(name)
    if re.search(r"\(\s*\*\s*" + q + r"\s*\)\s*\(", line):
        return "indirect_call"
    if re.search(r"&\s*" + q + r"\b", line):
        return "address_escape"
    if re.search(r"\b(?:_fmemcpy|_fmemset|memcpy|memset)\s*\([^;]*\b" + q + r"\b", line):
        return "bulk_pointer_argument"
    if re.search(r"\b" + q + r"\s*(?:\[[^]]*\])?\s*(?:\+|-)?=", line):
        return "write"
    if re.search(r"\b" + q + r"\s*\[", line):
        return "indexed_access"
    if re.search(r"\b" + q + r"\s*\(", line):
        return "call_or_function_reference"
    return "read_or_declaration"


def inventory(canonical: list[dict], effective: list[dict]) -> dict:
    symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))
    alias_map = dos.identifier_aliases(symbols)
    data = symbols["data"]
    spellings = {name: {name} for name in DATA_TARGETS + ARRAY_TARGETS}
    for name in DATA_TARGETS + ARRAY_TARGETS:
        row = data[name]
        spellings[name].update(n for n, r in data.items()
                               if r.get("seg") == row.get("seg") and r.get("off") == row.get("off"))
        spellings[name].update(old for old, new in alias_map.items()
                               if new == name or new in spellings[name])
    code_spellings = {name: {name} for name in SUPPORT}
    for table in (symbols["code"], symbols["data"]):
        for alias, canonical_name in alias_map.items():
            for name in SUPPORT:
                if canonical_name == name:
                    code_spellings[name].add(alias)
    reverse_targets = {}
    for name, variants in spellings.items():
        for variant in variants:
            reverse_targets[variant] = name
    reverse_support = {}
    for name, variants in code_spellings.items():
        for variant in variants:
            reverse_support[variant] = name
    token = re.compile(r"\b(" + "|".join(sorted(map(re.escape,
        set(reverse_targets) | set(reverse_support)), key=len, reverse=True)) + r")\b")
    sets = {"canonical_127": canonical, "effective_body_29": effective}
    target_hits = {n: [] for n in DATA_TARGETS + ARRAY_TARGETS}
    function_hits = {n: [] for n in SUPPORT}
    source_files = {k: [] for k in sets}
    all_refs = []
    for label, rows in sets.items():
        for row in rows:
            text = repo_path(row["path"]).read_text(encoding="latin1")
            matched = []
            for number, line in enumerate(text.splitlines(), 1):
                names = sorted(set(token.findall(line)))
                if not names:
                    continue
                item = {"line": number, "text": line.strip(), "spellings": names}
                matched.append(item)
                for spelling in names:
                    if spelling in reverse_targets:
                        name = reverse_targets[spelling]
                        target_hits[name].append({"set": label, "path": row["path"],
                            "sha256": row["sha256"], "line": number, "spelling": spelling,
                            "access": access_kind(spelling, line), "text": line.strip()})
                    if spelling in reverse_support:
                        name = reverse_support[spelling]
                        function_hits[name].append({"set": label, "path": row["path"],
                            "sha256": row["sha256"], "line": number, "spelling": spelling,
                            "text": line.strip()})
            if matched:
                source_files[label].append({"path": row["path"], "sha256": row["sha256"],
                                            "module": row.get("module"), "hits": matched})
            all_refs.append(row | {"scan_set": label})
    paths = [x["path"] for x in canonical + effective]
    if len(paths) != 156 or len(set(paths)) != 156:
        raise RuntimeError("source closure changed while scanning")
    return {"counts": {"canonical_127": len(canonical), "effective_body_29": len(effective),
                       "unique_paths": len(set(paths))},
            "source_pins": all_refs, "target_spellings": {k: sorted(v) for k, v in spellings.items()},
            "target_hits": target_hits, "function_hits": function_hits,
            "files_with_target_or_lifecycle_hits": source_files}


def registry_views() -> dict:
    symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))["data"]
    size_hypotheses = {"win_numOfWindows": 2, "win_numOfColors": 2,
        "win_numOfGroups": 2, "fd_50F6_3B4C": 4, "fd_50F6_3B58": 4,
        "fd_50F6_3B5C": 4, "win_drawHooks": 45 * 4,
        "win_offsets": 45 * 8}
    result = {}
    for name, size in size_hypotheses.items():
        row = symbols[name]
        seg, off = row["seg"], row["off"]
        exact = sorted(n for n, v in symbols.items()
                       if v.get("seg") == seg and v.get("off") == off)
        interior = sorted((n, v["off"] - off) for n, v in symbols.items()
                          if v.get("seg") == seg and off < v.get("off", -1) < off + size)
        edge = sorted(n for n, v in symbols.items()
                      if v.get("seg") == seg and v.get("off") == off + size)
        result[name] = {"address": f"{seg:04X}:{off:04X}", "source_size_hypothesis_bytes": size,
            "exact_base_names": exact, "registered_names_strictly_inside_view": interior,
            "registered_names_at_view_edge_not_used_as_extent_evidence": edge,
            "view_status": ("typed source extent candidate" if name in DATA_TARGETS else
                            "minimum source-touched prefix only; maximum unresolved")}
    colors = symbols["win_colors"]
    result["win_colors"] = {"address": f"{colors['seg']:04X}:{colors['off']:04X}",
        "exact_base_names": sorted(n for n,v in symbols.items()
            if v.get("seg")==colors["seg"] and v.get("off")==colors["off"]),
        "extent": None, "interior_scan": None,
        "reason": "dynamic resource count multiplied by six has no source-proven maximum"}
    return result


def save_resource_checks(inventory_report: dict) -> dict:
    save_source = ROOT / "src/S09/m35F5.c"
    text = save_source.read_text(encoding="latin1")
    exact_tokens = list(DATA_TARGETS + ARRAY_TARGETS)
    save_hits = [{"line": n, "text": line.strip()} for n,line in enumerate(text.splitlines(),1)
                 if any(re.search(r"\b"+re.escape(name)+r"\b", line) for name in exact_tokens)]
    writer_names = ("db_SaveObject", "db_ReplaceObject", "DBAdd", "DBDelete", "DBPack")
    writer_rx = re.compile(r"\b(" + "|".join(writer_names) + r")\s*\(")
    source_writer_rows = []
    seen_paths = set()
    for row in inventory_report["source_pins"]:
        if row["path"] in seen_paths:
            continue
        seen_paths.add(row["path"])
        source_text = repo_path(row["path"]).read_text(encoding="latin1")
        for number, line in enumerate(source_text.splitlines(), 1):
            for match in writer_rx.finditer(line):
                name = match.group(1)
                prefix = line[:match.start()].strip()
                is_definition = bool(re.search(r"\b(?:void|int|long|char|unsigned|static|far)\b[^;{}]*$", prefix))
                resource_ids = bool(re.search(r"\(\s*(?:0x80|128|0x81|129|0x83|131)\b", line))
                source_writer_rows.append({"set": row.get("scan_set"), "path": row["path"],
                    "source_sha256": row["sha256"], "line": number, "name": name,
                    "kind": "definition_or_declaration" if is_definition else "call",
                    "resource_id_0x80_0x81_0x83_literal": resource_ids,
                    "text": line.strip()})
    loader = pin(ROOT / "src/root/m20E8.c")
    return {"save_source": pin(save_source), "target_occurrences_in_SaveRec_source": save_hits,
            "resource_loader_source": loader,
            "resource_ids_and_sizes_from_source": [
                {"source": "src/root/m20E8.c", "lines": [98, 100, 106, 107, 110, 115, 125, 126, 128, 131],
                 "facts": "resource (g_5A97,9) copies 0x140 bytes to offsets; (0x80,0) provides three int words; (0x81,0) copies win_numOfColors*6; (0x83,0) copies 0x28 bytes to purge[0x28]."}],
            "database_writer_source_occurrences": source_writer_rows,
            "conclusion": "The source loader consumes external DB records. No target is in S09 SaveRec. The only DB save API occurrence is its generic definition and dynamic DBAdd implementation path; no source call writes IDs 0x80, 0x81, or 0x83. DBRecall and db_LoadObject do not validate the 0x80 count/product."}


def object_dispositions() -> dict:
    return {
        "win_numOfWindows": {"status": "closed source type and extent candidate",
            "source_type": "far signed int", "source_extent_bytes": 2,
            "extent_basis": "word 0 of resource (0x80,0) assigned to int far at src/root/m20E8.c:120; read as int in src/root/m2505.c:251,267",
            "lifetime_domain": "loaded during win_LoadAllWindows; used for the process lifetime; absent from S09 SaveRec",
            "value_domain": "no source validation/max for the resource word",
            "layout_domain": "candidate source ownership only; historical placement and communal order unclaimed"},
        "win_numOfColors": {"status": "closed source type and extent candidate",
            "source_type": "far signed int", "source_extent_bytes": 2,
            "extent_basis": "word 1 of resource (0x80,0) assigned to int far at src/root/m20E8.c:121",
            "lifetime_domain": "loaded during window initialization and used to size the resource-0x81 table copy; absent from S09 SaveRec",
            "value_domain": "no source validation/max; controls a count*6 byte copy",
            "layout_domain": "candidate source ownership only; historical placement and communal order unclaimed"},
        "win_numOfGroups": {"status": "closed source type and extent candidate",
            "source_type": "far signed int", "source_extent_bytes": 2,
            "extent_basis": "word 2 of resource (0x80,0) assigned to int far at src/root/m20E8.c:122",
            "lifetime_domain": "loaded during window initialization; absent from S09 SaveRec",
            "value_domain": "no source validation/max",
            "layout_domain": "candidate source ownership only; historical placement and communal order unclaimed"},
        "fd_50F6_3B4C": {"status": "closed source type and extent candidate",
            "source_type": "EmsSlot far * far * far", "source_extent_bytes": 4,
            "extent_basis": "assigned from f_2CFB_0002 with same return type at src/root/m19DC.c:16,31,69; far pointer ABI and OMF communal control",
            "lifetime_domain": "used after successful EMS initialization; root points to a separate Ralloc allocation sized g_389E*6; not in SaveRec",
            "layout_domain": "pointer extent is known; target allocation's runtime size is page-count dependent; historical placement/order unclaimed"},
        "fd_50F6_3B58": {"status": "closed source type and extent candidate",
            "source_type": "far callback pointer (char far *, char far *, int, int)", "source_extent_bytes": 4,
            "extent_basis": "selected from three far raster routines in src/root/m205F.c:217,223,229 and indirect-called with four typed args in src/root/m2662.c:498,554",
            "lifetime_domain": "set by graphics-driver selection and used by picture blits; not in SaveRec",
            "layout_domain": "pointer extent is known; callback target varies with display mode; historical placement/order unclaimed"},
        "fd_50F6_3B5C": {"status": "closed source type and extent candidate",
            "source_type": "Handle (char far * far *)", "source_extent_bytes": 4,
            "extent_basis": "assigned/read as Handle in clip_Push/clip_Pop at src/root/m1E57.c:444,465,467,482,484; OMF communal control",
            "lifetime_domain": "head of an allocated linked stack; pushed nodes save previous head; pop restores it; separate depth guard is 20; not in SaveRec",
            "layout_domain": "head extent known; list-node count and allocation lifetime depend on clip state; historical placement/order unclaimed"},
        "win_drawHooks": {"status": "array extent open; 45-entry prefix grounded",
            "source_type": "far function pointer table, 4-byte entries", "minimum_source_touched_prefix_bytes": 180,
            "extent_basis": "0xB4-byte reset and 45-entry loop in src/root/m20E8.c:106-107; callback store at line 353",
            "lifetime_domain": "reset during window initialization, callback entries set by registration and invoked during drawing",
            "unresolved": "no maximum index across all callers/callback paths; exact owner extent and layout unclaimed"},
        "win_offsets": {"status": "array extent open; 45-Rect prefix grounded",
            "source_type": "far struct Rect table, 8-byte entries", "minimum_source_touched_prefix_bytes": 360,
            "extent_basis": "45 Rect initializations and 0x140-byte (40 Rect) resource copy in src/root/m20E8.c:107,110; indexed accesses in m20E8.c, m23AE.c, src/S26/m39C7.c",
            "lifetime_domain": "reset, resource-seeded, then updated on window movement/open/close; absent from S09 SaveRec",
            "unresolved": "window count is an unchecked resource word; no maximum index across all callers; exact owner extent and layout unclaimed"},
        "win_colors": {"status": "array extent open",
            "source_type": "far six-char color entries", "entry_stride_bytes": 6,
            "extent_basis": "resource 0x81 copied for win_numOfColors*6 bytes at src/root/m20E8.c:126; indexed six-field records read in m21FA.c and m22BF.c",
            "lifetime_domain": "resource-loaded during window initialization and retained for color lookup/drawing; absent from S09 SaveRec",
            "unresolved": "no source producer/schema or upper bound for win_numOfColors; exact owner extent and layout unclaimed"},
        "win_handles": {"status": "open; no candidate owner", "source_extent_bytes": None,
            "basis": "four unsized extern declarations and unchecked resource-driven indexing; see work/source-only-dos/win-handles-owner-gap-v1.md",
            "unresolved": "do not infer a 45-entry cap from offsets/hooks, neighboring symbols, or Win16 declarations"}}


def naming_evidence() -> dict:
    pairs = json.loads(CROSS_VERSION.read_text(encoding="utf-8"))["pairs"]
    wanted = {"root:50F6:46E2": "_win_colors", "root:50F6:47DE": "_win_drawHooks",
        "root:50F6:47D8": "_win_numOfWindows", "root:50F6:47D6": "_win_numOfColors",
        "root:50F6:47D4": "_win_numOfGroups", "root:50F6:4892": "_win_offsets"}
    selected = {}
    for address, name in wanted.items():
        row = pairs.get(address)
        if not row or row.get("win16") != name or row.get("confidence") not in {"CONFIRMED", "HIGH"}:
            raise RuntimeError(f"missing reviewed Win16 naming decision for {address}/{name}")
        selected[address] = row
    return {"evidence_file": pin(CROSS_VERSION), "pairs": selected,
        "use_limit": "These reviewed pairs establish names only; no Win16 array dimension or storage extent is used."}


def compile_obj(name: str, source: str) -> bytes:
    result = compiler.compile_c(source, "msc600ax", FLAGS, basename=name)
    if not result.ok or result.obj is None:
        (OUT / (name + ".compile.log")).write_text(result.log, encoding="latin1")
        raise RuntimeError(f"compile failed for {name}: {result.log[-1600:]}")
    raw = bytes(result.obj)
    (OUT / (name + ".OBJ")).write_bytes(raw)
    return raw


def omf_fact(raw: bytes) -> dict:
    obj = OmfReader(communals=True).read(raw)
    return {"sha256": sha(raw), "bytes": len(raw), "communals": obj.communals,
        "segments": obj.segment_lengths, "nonempty_segments": {k: len(v) for k,v in obj.segments.items() if v},
        "public_count": len(obj.publics), "local_public_count": len(obj.local_publics),
        "fixups": len(obj.fixups), "linker_fixups": len(obj.linker_fixups),
        "externals": obj.externals, "external_scopes": obj.external_scopes}


PROVIDER_SOURCE = PROVIDER.read_text(encoding="ascii")
CORRECT_CONSUMER = r'''typedef struct { unsigned int age; int file; int page; } EmsSlot;
typedef char far * far *Handle;
extern int far win_numOfWindows, win_numOfColors, win_numOfGroups;
extern EmsSlot far * far * far fd_50F6_3B4C;
extern void (far * far fd_50F6_3B58)(char far *, char far *, int, int);
extern Handle far fd_50F6_3B5C;
extern int far puts(char far *);
static int far calls;
static void far raster(char far *src, char far *dst, int shift, int flag)
{ *dst = *src + shift + flag; calls++; }
int main(void)
{
    EmsSlot slot; EmsSlot far *row; EmsSlot far * far *rows;
    char source, result; char far *payload; Handle h;
    if (sizeof(int) != 2 || sizeof(EmsSlot) != 6 || sizeof(Handle) != 4 ||
        sizeof(fd_50F6_3B4C) != 4 || sizeof(fd_50F6_3B58) != 4 ||
        sizeof(fd_50F6_3B5C) != 4) { puts("FAIL"); return 0; }
    if (win_numOfWindows || win_numOfColors || win_numOfGroups ||
        fd_50F6_3B4C || fd_50F6_3B58 || fd_50F6_3B5C) { puts("FAIL"); return 0; }
    win_numOfWindows = 40; win_numOfColors = 7; win_numOfGroups = 3;
    if (win_numOfWindows != 40 || win_numOfColors != 7 || win_numOfGroups != 3) {
        puts("FAIL"); return 0;
    }
    slot.age = 0; slot.file = 0; slot.page = 0; row = &slot; rows = &row;
    fd_50F6_3B4C = rows;
    (*fd_50F6_3B4C)->age = 0x1234; (*fd_50F6_3B4C)->file = 5; (*fd_50F6_3B4C)->page = 9;
    if (slot.age != 0x1234 || slot.file != 5 || slot.page != 9) { puts("FAIL"); return 0; }
    source = 10; result = 0; fd_50F6_3B58 = raster;
    (*fd_50F6_3B58)(&source, &result, 2, 3);
    if (result != 15 || calls != 1) { puts("FAIL"); return 0; }
    payload = &source; h = &payload; fd_50F6_3B5C = h;
    if (*fd_50F6_3B5C != payload) { puts("FAIL"); return 0; }
    *fd_50F6_3B5C = &result;
    if (*fd_50F6_3B5C != &result) { puts("FAIL"); return 0; }
    puts("PASS"); return 0;
}
'''
WRONG_WIDTH_CONSUMER = r'''extern long far win_numOfWindows;
extern int far puts(char far *);
int main(void) { if (sizeof(win_numOfWindows) == 2) puts("PASS"); else puts("FAIL"); return 0; }
'''
WRONG_NEAR_CONSUMER = r'''typedef char near * near *NearHandle;
extern NearHandle near fd_50F6_3B5C;
extern int far puts(char far *);
int main(void) { if (sizeof(fd_50F6_3B5C) == 4) puts("PASS"); else puts("FAIL"); return 0; }
'''
STARTUP_CONSUMER = CORRECT_CONSUMER


def run_link_case(profile: str, case: str, expected: str, consumer: bytes, owner: bytes,
                  runtime_rows: list, linker: dict, runner: dict, tool_dir: Path) -> dict:
    directory = OUT / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / name).unlink(missing_ok=True)
    (directory / "CRT.OBJ").write_bytes(consumer)
    (directory / "OWNER.OBJ").write_bytes(owner)
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    script = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
              "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    (directory / "PROBE.LNK").write_bytes(script.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    lines = []
    for section, settings in runner["conf"].items():
        lines.append("[" + section + "]")
        lines += [f"{key}={value}" for key, value in settings.items()]
    lines += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
              "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    try:
        run = subprocess.run([runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
            cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        timeout = False
    except subprocess.TimeoutExpired:
        run = type("Timeout", (), {"returncode": -1})()
        timeout = True
    runlog = directory / "RUN.LOG"
    raw_run = runlog.read_bytes().decode("latin1") if runlog.exists() else "NO RUN.LOG"
    actual = raw_run.strip()
    linklog = directory / "LINK.LOG"
    link_text = linklog.read_text(encoding="latin1", errors="replace") if linklog.exists() else ""
    map_path = directory / "PROBE.MAP"
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    expected_owner_publics = sorted("_" + name for name in DATA_TARGETS)
    owner_publics_found = [name for name in expected_owner_publics
                           if re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) +
                                        r"(?![A-Za-z0-9_])", map_text)]
    linker_diagnostics = re.findall(
        r"(?im)^.*(?:unresolved|undefined|unknown external|not defined|symbol not found).*$",
        link_text)
    exe_exists = (directory / "PROBE.EXE").is_file()
    map_exists = map_path.is_file()
    artifacts = [pin(directory / n) for n in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG", "PROBE.LNK")
                 if (directory / n).is_file()]
    row = {"profile": profile, "case": case, "expected": expected, "actual": actual,
        "raw_run_log_latin1": raw_run,
        "exit_code": run.returncode, "timed_out": timeout,
        "passed": (actual == expected and run.returncode == 0 and not timeout and
                   exe_exists and map_exists and not linker_diagnostics and
                   owner_publics_found == expected_owner_publics),
        "linker_produced_executable": exe_exists,
        "linker_produced_map": map_exists,
        "expected_owner_publics": expected_owner_publics,
        "owner_publics_found_in_map": owner_publics_found,
        "linker_diagnostics": linker_diagnostics,
        "link_log_raw_latin1": link_text,
        "link_log_tail": link_text[-500:], "artifacts": artifacts}
    print(profile, case, actual, flush=True)
    return row


def compile_and_run() -> dict:
    provider_obj = compile_obj("UIOWNER", PROVIDER_SOURCE)
    owner = OmfReader(communals=True).read(provider_obj)
    expected = {"_win_numOfWindows": ("far", 2), "_win_numOfColors": ("far", 2),
        "_win_numOfGroups": ("far", 2), "_fd_50F6_3B4C": ("far", 4),
        "_fd_50F6_3B58": ("far", 4), "_fd_50F6_3B5C": ("far", 4)}
    actual = {row["name"]: (row["kind"], row["length"]) for row in owner.communals}
    if actual != expected or len(owner.communals) != len(expected):
        raise RuntimeError(f"candidate COMDEF layout differs from typed source: {owner.communals}")
    if owner.segments or owner.publics or owner.local_publics or owner.fixups or owner.linker_fixups:
        raise RuntimeError("candidate provider unexpectedly emits code/data/publics/fixups")
    initialized_source = PROVIDER_SOURCE.replace(
        "int far win_numOfWindows;", "int far win_numOfWindows=3;")
    initialized_obj = compile_obj("UIINIT", initialized_source)
    wrong_width_obj = compile_obj("UIWID", "long far win_numOfWindows;\n")
    wrong_near_obj = compile_obj("UINEAR", "typedef char near * near *NearHandle; NearHandle near fd_50F6_3B5C;\n")
    width_rows = OmfReader(communals=True).read(wrong_width_obj).communals
    near_rows = OmfReader(communals=True).read(wrong_near_obj).communals
    if not any(r["name"] == "_win_numOfWindows" and r["length"] == 4 for r in width_rows):
        raise RuntimeError(f"wrong-width negative control does not emit a 4-byte far common: {width_rows}")
    if not any(r["name"] == "_fd_50F6_3B5C" and r["length"] == 2 for r in near_rows):
        raise RuntimeError(f"near-pointer negative control does not emit a 2-byte near common: {near_rows}")
    objects = {
        "owner": provider_obj,
        "typed": compile_obj("UITYPE", CORRECT_CONSUMER),
        "wrong_width_view": compile_obj("UIWVIEW", WRONG_WIDTH_CONSUMER),
        "wrong_near_view": compile_obj("UINVW", WRONG_NEAR_CONSUMER),
        "initialized_owner": initialized_obj,
    }
    tc = compiler.toolchain()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    runner = tc["runners"]["dosbox-x"]
    cases = []
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        tool_dir = compiler.pinned_tree(linker)
        cases.append(run_link_case(profile, "typed_startup_and_roundtrip", "PASS",
            objects["typed"], objects["owner"], runtime_rows, linker, runner, tool_dir))
        cases.append(run_link_case(profile, "wrong_scalar_width_guard", "FAIL",
            objects["wrong_width_view"], objects["owner"], runtime_rows, linker, runner, tool_dir))
        cases.append(run_link_case(profile, "initialized_owner_zero_startup_guard", "FAIL",
            objects["typed"], objects["initialized_owner"], runtime_rows, linker, runner, tool_dir))
    if len(cases) != 6 or not all(row["passed"] for row in cases):
        raise RuntimeError("one or more RTLink positive/negative controls differed from expectations")
    tc_pins = []
    compiler_profile = compiler.verify_profile("msc600ax")
    for rel, expected_hash in compiler_profile["files"].items():
        tc_pins.append(pin(Path(compiler_profile["directory"]) / rel, expected_hash))
    for profile in ("rtlink400", "rtlink610"):
        link = tc["linkers"][profile]
        tc_pins.extend(pin(Path(link["directory"]) / rel, expected_hash)
                       for rel, expected_hash in link["files"].items())
    tc_pins.extend(pin(Path(row["path"]), row["sha256"]) for row in runtime_rows)
    tc_pins.append(pin(Path(runner["path"]), runner["sha256"]))
    for rel in ("tools/compiler.py", "tools/omf.py", "tools/source_only_dos.py",
                "layout/toolchain.json"):
        tc_pins.append(pin(ROOT / rel))
    return {"compiler": {"profile": "msc600ax", "flags": FLAGS,
            "required_flags": compiler.verify_profile("msc600ax").get("required_flags", []),
            "effective_flags": [*FLAGS, *compiler_profile.get("required_flags", [])],
            "owner_omf": omf_fact(provider_obj), "wrong_width_omf": omf_fact(wrong_width_obj),
            "wrong_near_omf": omf_fact(wrong_near_obj), "initialized_owner_omf": omf_fact(initialized_obj)},
        "runtime_cases": cases, "tool_pins": tc_pins,
        "objects": {key: omf_fact(value) for key,value in objects.items()},
        "experimental_linkers_not_historical_identity": True,
        "game_objects_or_stubs_linked": False}


def main() -> int:
    if REPORT_PATH.exists():
        raise RuntimeError(f"refusing to overwrite existing fresh report: {REPORT_PATH}")
    denied = dos.install_input_guard()
    canonical, effective, receipts = source_sets()
    source_report = inventory(canonical, effective)
    registry = registry_views()
    save_resource = save_resource_checks(source_report)
    runtime = compile_and_run()
    if denied:
        raise RuntimeError(f"oracle/image input was attempted: {denied}")
    report = {"schema": "simant-dos-ui-resource-owner-study-v17",
        "admission": {"root_reviewed": False, "admitted": False},
        "status": "SOURCE_ONLY_CANDIDATE_SCALAR_SUBFAMILY; RESOURCE_ARRAY_EXTENTS_OPEN",
        "source_inventory": source_report, "registry_views": registry,
        "object_dispositions": object_dispositions(),
        "cross_version_naming_evidence": naming_evidence(),
        "save_and_resource_producer_review": save_resource, "compiler_and_rtlink_controls": runtime,
        "provider_source": pin(PROVIDER), "probe_source": pin(Path(__file__)),
        "pinned_metadata": {"intake": pin(INTAKE), "strict_index": pin(INDEX),
            "symbols": pin(SYMBOLS), "layout_manifest": pin(MANIFEST),
            "cross_version_decisions": pin(CROSS_VERSION),
            "unresolved_win_handles_review": pin(ROOT / "work/source-only-dos/win-handles-owner-gap-v1.md")},
        "source_receipts": receipts,
        "original_bytes_or_existing_objects_read": False,
        "input_guard_denied_paths": denied,
        "canonical_source_layout_manifest_or_git_changed": False,
        "unresolved": [
            "win_colors has no source-proven maximum for the resource-driven win_numOfColors*6 copy.",
            "win_drawHooks and win_offsets have fixed 45-entry initialized prefixes but no complete source-proven maximum index domain across all consumers/callers.",
            "resource (0x80,0)/(0x81,0)/(g_5A97,9) producer/schema bytes are external to the scanned source; db_LoadObject does not validate count/size.",
            "win_handles remains without a proved maximum index/owner; do not infer 45 entries from nearby tables or symbols.",
            "No historical far-communal owner translation unit, placement, or order is claimed; the candidate is a functional source owner only."]}
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("wrote", REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
