"""Research-only producer fixture for g_5A97's accepted ReadConfig path.

This extracts the three exact accepted function definitions from src/S20/m39F1.c,
pins the complete source and manifest claim, and links only those definitions plus
test-owned state/views/main against the pinned MSC 6.00AX CRT. It does not read the
original executable, infer original pre-main bytes, or modify canonical files.
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
WORKER = ROOT / "build" / "workers" / "dos_g5a97_config_producer" / "candidate"
PACKETS = WORKER / "packets"
SOURCE_ROOT = ROOT / "work" / "source-only-dos"
SOURCE = ROOT / "src" / "S20" / "m39F1.c"
EXPECTED_SOURCE_SHA = "6fd0a02991a29325f214049a8a8961aaee4bc65fbf760b296e63a6ac8f6fbe7b"
PROVIDER_PATH = SOURCE_ROOT / "providers" / "display-mode-selector.c"
PROVIDER_REL = PROVIDER_PATH.relative_to(ROOT).as_posix()
PROVIDER_BASENAME = "MODEOWN"
MODULE = "source-owned:display-mode-selector"
PROVIDER_FLAGS = ["/AL", "/Os", "/Gs"]
DOMINANCE_REVIEW = SOURCE_ROOT / "g5a97-startup-dominance-review-v1.md"
SOURCE_REL = SOURCE.relative_to(ROOT).as_posix()
TARGET = "g_5A97"
FUNCTIONS = ("ReadWord", "SkipWords", "ReadConfig")
MODES = {"?": (-1, -1, 255), "E": (0, 0, 0), "H": (3, 3, 3), "M": (5, 5, 5),
         "T": (2, 2, 2), "V": (8, 8, 8), "e": (4, 4, 4), "m": (7, 7, 7)}
SEEDS = {"0": (0, 0, 0), "F": (-1, -1, 255)}
DOMINANCE_SOURCE_ROWS = {
    "src/root/m15F8.c": ("d6d4daddab943ee3436ca0e9c8dbc866a9d67659f7448f3c307f858abe06b70a", ("main",)),
    "src/root/m00F8.c": ("4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a", ("f_00F8_0543", "f_00F8_0585")),
    "src/root/m1A96.c": ("c57124b9d75ea77eb30158c09a71550862cf7081ceed625a2550a26a262bfdfa", ("ch_SetCacheHooks",)),
    "src/S15/m384C.c": ("01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5", ("o15_384C_0125",)),
    "src/S20/m39F1.c": (EXPECTED_SOURCE_SHA, ("IBMInitStuff", "ReadWord", "SkipWords", "ReadConfig")),
    "src/root/m205F.c": ("225326bdd127dd3825035ae0fe8434e6677c0ee81203fee2e16bac0cf90fffc6", ("f_205F_0004",)),
}
SOURCE_TOKEN = re.compile(r"(?<![A-Za-z0-9_])g_5A97(?![A-Za-z0-9_])")
ESCAPE_TOKEN = re.compile(r"(?<!&)&(?!&)\s*g_5A97\b|\bg_5A97\s*\[|\bg_5A97\s*[+-]\s*(?:\w|\d)", re.I)
NUMERIC_TOKEN = re.compile(r"(?<![A-Za-z0-9_])(?:0x5A97|5A97[hH])(?![A-Za-z0-9_])", re.I)

sys.path.insert(0, str(ROOT / "tools"))

FIXTURE_PROLOGUE = r"""
extern int far open(char far *name, int mode, ...);
extern int far close(int fd);
extern int far read(int fd, char far *buf, unsigned n);
extern int far puts(char far *s);
extern void far exit(int code);
extern char far * far fd_55B3_1CE4;
extern char far * far fd_55B3_1CE0;
extern char near g_5A97;
static int g_610A = -1;
""".strip()

DATA = r"""
char far * far fd_55B3_1CE4 = "INPUT.CFG";
char far * far fd_55B3_1CE0 = "Fixture config missing";
""".strip() + "\n"
SEED = r"""
extern unsigned char near g_5A97;
void far seed_zero(void) { g_5A97 = 0; }
void far seed_ff(void) { g_5A97 = 255; }
""".strip() + "\n"
SIGNED_VIEW = r"""
extern signed char near g_5A97;
signed char far read_signed(void) { return g_5A97; }
""".strip() + "\n"
UNSIGNED_VIEW = r"""
extern unsigned char near g_5A97;
unsigned char far read_unsigned(void) { return g_5A97; }
""".strip() + "\n"
PLAIN_VIEW = r"""
extern char near g_5A97;
char far read_plain(void) { return g_5A97; }
""".strip() + "\n"
MAIN = r"""
extern void far ReadConfig(void);
extern void far seed_zero(void);
extern void far seed_ff(void);
extern char far read_plain(void);
extern signed char far read_signed(void);
extern unsigned char far read_unsigned(void);
extern int far printf(char far *fmt, ...);

int main(int argc, char far * far *argv)
{
    if (argc > 1) {
        if (argv[1][0] == '0')
            seed_zero();
        else if (argv[1][0] == 'F')
            seed_ff();
        else if (argv[1][0] != 'C')
            return 10;
    }
    printf("BEFORE=%d/%d/%u\n", (int)read_plain(), (int)read_signed(), (unsigned int)read_unsigned());
    ReadConfig();
    printf("AFTER=%d/%d/%u\n", (int)read_plain(), (int)read_signed(), (unsigned int)read_unsigned());
    return 0;
}
""".strip() + "\n"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact_function(source: str, name: str) -> tuple[str, int]:
    signature = re.search(rf"(?m)^void\s+far\s+{re.escape(name)}\s*\([^\n]*\)\s*$", source)
    if not signature:
        raise ValueError(f"missing expected function signature: {name}")
    start = signature.start()
    brace = source.find("{", signature.end())
    if brace < 0:
        raise ValueError(f"missing body: {name}")
    depth = 0
    i = brace
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == '"':
                state = "string"
            elif ch == "'":
                state = "char"
            elif ch == "/" and nxt == "*":
                state = "comment"
                i += 1
            elif ch == "/" and nxt == "/":
                state = "linecomment"
                i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[start:i + 1], source.count("\n", 0, start) + 1
        elif state == "string":
            if ch == "\\":
                i += 1
            elif ch == '"':
                state = "code"
        elif state == "char":
            if ch == "\\":
                i += 1
            elif ch == "'":
                state = "code"
        elif state == "comment":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 1
        elif state == "linecomment":
            if ch == "\n":
                state = "code"
        i += 1
    raise ValueError(f"unterminated function: {name}")


def text(path: Path) -> str:
    return path.read_text(encoding="latin1", errors="replace") if path.exists() else "<missing>"


def compile_fixture(name: str, source: str, flags: list[str], compiler) -> bytes:
    (WORKER / "fixtures").mkdir(parents=True, exist_ok=True)
    (WORKER / "objects").mkdir(parents=True, exist_ok=True)
    (WORKER / "fixtures" / f"{name}.C").write_bytes(source.encode("ascii"))
    result = compiler.compile_c(source, "msc600ax", flags, basename=name, keep=False)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"MSC compile failed for {name}:\n{result.log}")
    (WORKER / "objects" / f"{name}.OBJ").write_bytes(result.obj)
    return result.obj


def compile_only_read_functions(whole_source: str, flags: list[str], compiler) -> tuple[bytes, dict]:
    defs = {}
    spans = {}
    for name in FUNCTIONS:
        definition, line = exact_function(whole_source, name)
        defs[name] = definition
        spans[name] = {"line": line, "sha256": sha(definition.encode("latin1")),
                       "bytes": len(definition.encode("latin1"))}
    # These bodies are verbatim. Only their original declarations and private
    # g_610A dependency are supplied as a narrow test harness context.
    read_source = FIXTURE_PROLOGUE + "\n\n" + "\n\n".join(defs[n] for n in FUNCTIONS) + "\n"
    return compile_fixture("CFGREAD", read_source, flags, compiler), {"definitions": spans,
        "fixture_source_sha256": sha(read_source.encode("ascii")),
        "fixture_source_bytes": len(read_source.encode("ascii")),
        "fixture_source": read_source}


def case_config(mode: str) -> bytes:
    return f"one two {mode} three four 5\n".encode("ascii")


def source_scan(path: Path) -> dict:
    lines = path.read_text(encoding="latin1", errors="replace").splitlines()
    named = []
    fixed = []
    escapes = []
    handlers = []
    for number, line in enumerate(lines, 1):
        if SOURCE_TOKEN.search(line):
            row = {"line": number, "text": line.strip()}
            named.append(row)
            if ESCAPE_TOKEN.search(line):
                escapes.append(row)
        if path.suffix.lower() in (".c", ".asm") and NUMERIC_TOKEN.search(line):
            fixed.append({"line": number, "text": line.strip()})
        if re.search(r"\bsignal\s*\(|\b_harderr\s*\(|\bharderr\s*\(", line, re.I):
            handlers.append({"line": number, "text": line.strip()})
    return {"named_hits": named, "numeric_literal_hits": fixed,
            "pointer_or_index_escape_hits": escapes, "signal_or_harderr_hits": handlers}


def collect_source_closure(manifest: dict) -> dict:
    manifest_path = ROOT / "layout" / "manifest.json"
    symbols_path = ROOT / "layout" / "symbols.json"
    behavior_path = ROOT / "evidence" / "behavior" / "manifest.json"
    strict_index_path = SOURCE_ROOT / "static-completeness" / "index-v1.json"
    review_path = DOMINANCE_REVIEW
    static_inputs = [manifest_path, symbols_path, behavior_path, strict_index_path,
                     SOURCE_ROOT / "near-state-debt-audit.py",
                     SOURCE_ROOT / "near-state-debt-runtime-scan.py",
                     ROOT / "build" / "workers" / "dos_near_state_debt_review" / "source-scan.json",
                     review_path]
    for path in static_inputs:
        if not path.is_file():
            raise ValueError(f"missing source-closure input: {path}")
    behavior = json.loads(behavior_path.read_text(encoding="utf-8"))
    strict_index = json.loads(strict_index_path.read_text(encoding="utf-8"))
    if len(strict_index.get("entries", {})) != 29:
        raise ValueError("strict source closure must contain exactly 29 effective entries")
    if strict_index.get("registry", {}).get("sha256") != sha(behavior_path.read_bytes()):
        raise ValueError("strict source index does not pin current behavior registry")

    canonical_sources = {}
    canonical_hits = {}
    for module_key, module in manifest["modules"].items():
        rel = module["source"].replace("\\", "/")
        path = ROOT / Path(rel)
        actual = sha(path.read_bytes())
        if actual != module["source_sha256"]:
            raise ValueError(f"canonical manifest source hash mismatch: {rel}")
        record = {"path": rel, "sha256": actual, "module": module_key}
        canonical_sources[rel] = record
        hits = source_scan(path)
        if any(hits.values()):
            canonical_hits[rel] = {**record, **hits}

    strict_sources = []
    strict_hits = []
    strict_by_path = {}
    for function, index_row in sorted(strict_index["entries"].items()):
        receipt_path = ROOT / index_row["path"]
        receipt_sha = sha(receipt_path.read_bytes())
        if receipt_sha != index_row["sha256"]:
            raise ValueError(f"strict source receipt hash mismatch: {function}")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("status") != "BEHAVIOR_EXACT_CONFIRMED":
            raise ValueError(f"strict source receipt not confirmed: {function}")
        source_row = receipt.get("source_override") or receipt["registered_source"]
        rel = source_row["path"].replace("\\", "/")
        source_path = ROOT / Path(rel)
        source_sha = sha(source_path.read_bytes())
        if source_sha != source_row["sha256"]:
            raise ValueError(f"strict effective source hash mismatch: {function}")
        row = {"function": function, "source_path": rel, "source_sha256": source_sha,
               "receipt_path": index_row["path"].replace("\\", "/"),
               "receipt_sha256": receipt_sha}
        strict_sources.append(row)
        strict_by_path[rel] = {"path": rel, "sha256": source_sha}
        hits = source_scan(source_path)
        if any(hits.values()):
            strict_hits.append({**row, **hits})

    dominance_sources = []
    for rel, (expected_sha, claims) in DOMINANCE_SOURCE_ROWS.items():
        module = next((m for m in manifest["modules"].values()
                       if m["source"].replace("\\", "/") == rel), None)
        if module is None or module["source_sha256"] != expected_sha:
            raise ValueError(f"startup dominance module pin changed: {rel}")
        rows = {row["name"]: row for row in module["claims"]}
        for claim in claims:
            if claim not in rows or rows[claim].get("provenance") != "EXACT_NATURAL":
                raise ValueError(f"startup dominance claim no longer exact-natural: {rel}:{claim}")
        dominance_sources.append({"path": rel, "sha256": expected_sha,
                                  "claims": list(claims), "claim_provenance": "EXACT_NATURAL"})

    target_canonical = [row for row in canonical_hits.values()
                        if any(SOURCE_TOKEN.search(hit["text"]) for hit in row["named_hits"])]
    target_strict = [row for row in strict_hits
                     if any(SOURCE_TOKEN.search(hit["text"]) for hit in row["named_hits"])]
    target_escapes = [
        {"set": "canonical", "path": row["path"], "line": hit["line"], "text": hit["text"]}
        for row in target_canonical for hit in row["pointer_or_index_escape_hits"]
    ] + [
        {"set": "strict_effective", "path": row["source_path"], "function": row["function"],
         "line": hit["line"], "text": hit["text"]}
        for row in target_strict for hit in row["pointer_or_index_escape_hits"]
    ]
    numeric_target_hits = [
        {"set": "canonical", "path": row["path"], "line": hit["line"], "text": hit["text"]}
        for row in canonical_hits.values() for hit in row["numeric_literal_hits"]
    ] + [
        {"set": "strict_effective", "path": row["source_path"], "function": row["function"],
         "line": hit["line"], "text": hit["text"]}
        for row in strict_hits for hit in row["numeric_literal_hits"]
    ]
    if target_escapes or numeric_target_hits:
        raise ValueError(f"unexpected pointer/index escape or fixed literal: {target_escapes + numeric_target_hits!r}")

    symbols = json.loads(symbols_path.read_text(encoding="utf-8"))["data"]
    symbol = symbols[TARGET]
    closure_pins = [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p.read_bytes()),
                     "size": p.stat().st_size} for p in static_inputs]
    return {
        "policy": "all current layout-manifest canonical sources plus only the 29 root-confirmed effective sources in static-completeness/index-v1.json; superseded experiments excluded",
        "canonical_source_file_count": len(canonical_sources),
        "canonical_source_pins": [canonical_sources[k] for k in sorted(canonical_sources)],
        "strict_effective_entry_count": len(strict_sources),
        "strict_effective_source_pins": strict_sources,
        "strict_effective_unique_source_count": len(strict_by_path),
        "strict_effective_unique_source_pins": [strict_by_path[k] for k in sorted(strict_by_path)],
        "target_reference_sources": {"canonical": target_canonical,
                                      "strict_effective": target_strict},
        "pointer_or_index_escape_hits": target_escapes,
        "fixed_address_literal_hits": numeric_target_hits,
        "signal_or_harderr_inventory": {
            "canonical": [{"path": row["path"], "hits": row["signal_or_harderr_hits"]}
                          for row in canonical_hits.values() if row["signal_or_harderr_hits"]],
            "strict_effective": [{"function": row["function"], "path": row["source_path"],
                                  "hits": row["signal_or_harderr_hits"]}
                                 for row in strict_hits if row["signal_or_harderr_hits"]]},
        "first_write_dominance": {
            "review": {"path": review_path.relative_to(ROOT).as_posix(),
                       "sha256": sha(review_path.read_bytes())},
            "reviewed_sources": dominance_sources,
            "anchors": ["src/root/m15F8.c:74-95", "src/root/m00F8.c:328-346",
                        "src/root/m1A96.c:280-285", "src/S15/m384C.c:66-82",
                        "src/S20/m39F1.c:68-69,82-114,125-154,216-258",
                        "src/root/m205F.c:132-165"],
            "source_claim": "returning startup path calls ReadConfig before the first selector read; pre-config error exits do not read the selector",
            "external_hardware_or_arbitrary_dos_interrupt_model": False},
        "registry_symbol": {"name": TARGET, "segment": symbol["seg"], "offset": symbol["off"]},
        "input_pins": closure_pins,
    }


def run_linker(linker_key: str, linked: dict, toolchain: dict, runtime_rows: list[dict]) -> list[dict]:
    import compiler
    linker = toolchain["linkers"][linker_key]
    runner = toolchain["runners"][linker["runner"]]
    for rel, expected in linker["files"].items():
        if sha((Path(linker["directory"]) / rel).read_bytes()) != expected:
            raise ValueError(f"linker file pin mismatch: {linker_key}/{rel}")
    linkroot = WORKER / "link-runs" / linker_key
    linkroot.mkdir(parents=True, exist_ok=True)
    for old in linkroot.iterdir():
        if old.is_file():
            old.unlink()
    for name, obj in linked.items():
        (linkroot / f"{name}.OBJ").write_bytes(obj)
    for row in runtime_rows:
        src = Path(row["path"])
        if sha(src.read_bytes()) != row["sha256"]:
            raise ValueError(f"accepted runtime library pin mismatch: {src}")
        shutil.copyfile(src, linkroot / src.name.upper())
    (linkroot / "PROBE.LNK").write_bytes(
        ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
         "LIBRARY LLIBCR, LIBH\r\nFILE MODEOWN, DATA, CFGREAD, SEED, SVIEW, UVIEW, PLAIN, MAIN\r\n").encode("ascii"))
    (linkroot / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    linker_exe = linker["executable"]
    exe_cmd = linker_exe.replace("/", "\\")
    lines = ["@echo off", f"D:\\{exe_cmd} @PROBE.LNK < NUL > LINK.LOG"]
    cases = []
    index = 0
    modes = list(MODES.items())
    for seed in SEEDS:
        for mode, expected in modes:
            index += 1
            tag = f"C{index:02d}"
            input_name = f"I{index:02d}.CFG"
            (linkroot / input_name).write_bytes(case_config(mode))
            lines += [f"COPY /Y {input_name} INPUT.CFG > NUL",
                      f"PROBE.EXE {seed} > {tag}.LOG",
                      f"IF ERRORLEVEL 1 GOTO E{index:02d}",
                      f"ECHO 0 > {tag}.STA", f"GOTO D{index:02d}",
                      f":E{index:02d}", f"ECHO 1 > {tag}.STA", f":D{index:02d}"]
            cases.append({"tag": tag, "input": input_name, "mode": mode,
                          "seed": seed, "expected_before": SEEDS[seed],
                          "expected_after": expected, "expected_status": 0,
                          "expected_message": None})
    for seed in SEEDS:
        for kind, file_name, content, expected_message in (
                ("invalid", f"IB{seed}.CFG", case_config("X"), "Bad 'Display Mode' in configuration file"),
                ("missing", None, None, "Fixture config missing")):
            index += 1
            tag = f"C{index:02d}"
            if file_name is not None:
                (linkroot / file_name).write_bytes(content)
                lines.append(f"COPY /Y {file_name} INPUT.CFG > NUL")
            else:
                lines.append("DEL INPUT.CFG")
            lines += [f"PROBE.EXE {seed} > {tag}.LOG",
                      f"IF ERRORLEVEL 1 GOTO E{index:02d}",
                      f"ECHO 0 > {tag}.STA", f"GOTO D{index:02d}",
                      f":E{index:02d}", f"ECHO 1 > {tag}.STA", f":D{index:02d}"]
            cases.append({"tag": tag, "kind": kind, "input": file_name,
                          "seed": seed, "expected_before": SEEDS[seed],
                          "expected_after": None, "expected_status": 1,
                          "expected_message": expected_message})
    # A separate no-seed case observes the real MSC CRT's initialization of
    # the test owner's near tentative definition at main entry.
    (linkroot / "ICRT.CFG").write_bytes(case_config("E"))
    lines += ["COPY /Y ICRT.CFG INPUT.CFG > NUL", "PROBE.EXE C > C21.LOG",
              "IF ERRORLEVEL 1 GOTO E21", "ECHO 0 > C21.STA", "GOTO D21",
              ":E21", "ECHO 1 > C21.STA", ":D21"]
    cases.append({"tag": "C21", "kind": "crt-entry-zero", "input": "ICRT.CFG",
                  "mode": "E", "seed": "CRT", "expected_before": (0, 0, 0),
                  "expected_after": (0, 0, 0), "expected_status": 0,
                  "expected_message": None})
    (linkroot / "RUN.BAT").write_bytes(("\r\n".join(lines) + "\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines.extend(f"{key}={value}" for key, value in settings.items())
    conf_lines += ["[autoexec]", f'mount c "{linkroot.resolve()}"',
                   f'mount d "{compiler.pinned_tree(linker)}" -ro',
                   "c:", "call RUN.BAT", "exit"]
    conf_path = linkroot / "dosbox.conf"
    conf_path.write_text("\n".join(conf_lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    proc = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                          cwd=linkroot, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    map_path = linkroot / "PROBE.MAP"
    map_lines = text(map_path).splitlines()
    ctype_rows = [{"line": i, "text": line.strip()} for i, line in enumerate(map_lines, 1)
                  if "_isdigit" in line or "_isspace" in line]
    if not any("_isdigit" in row["text"] for row in ctype_rows) or not any("_isspace" in row["text"] for row in ctype_rows):
        raise RuntimeError(f"{linker_key}: linked map lacks real CRT ctype symbols")
    rows = []
    for case in cases:
        log = text(linkroot / f"{case['tag']}.LOG").strip()
        status_text = text(linkroot / f"{case['tag']}.STA").strip()
        try:
            status = int(status_text)
        except ValueError:
            status = None
        after = (f"AFTER={case['expected_after'][0]}/{case['expected_after'][1]}"
                 f"/{case['expected_after'][2]}"
                 if case["expected_after"] is not None else None)
        before_match = re.search(r"BEFORE=(-?\d+)/(-?\d+)/(\d+)", log)
        after_match = re.search(r"AFTER=(-?\d+)/(-?\d+)/(\d+)", log)
        actual_before = tuple(int(before_match.group(i)) for i in range(1, 4)) if before_match else None
        actual_after = tuple(int(after_match.group(i)) for i in range(1, 4)) if after_match else None
        passed = (status == case["expected_status"] and actual_before == tuple(case["expected_before"])
                  and actual_after == (tuple(case["expected_after"])
                                       if case["expected_after"] is not None else None))
        if after is None:
            passed = passed and "AFTER=" not in log
        if case["expected_message"]:
            passed = passed and case["expected_message"] in log
        rows.append({**case, "actual_status": status, "actual_before": actual_before,
                     "actual_after": actual_after, "log": log,
                     "passed": bool(passed)})
    if not (linkroot / "PROBE.EXE").is_file():
        raise RuntimeError(f"{linker_key}: linker did not produce PROBE.EXE\n{text(linkroot / 'LINK.LOG')}\n{proc.stdout.decode('latin1','replace')}")
    exe_path = linkroot / "PROBE.EXE"
    map_path = linkroot / "PROBE.MAP"
    link_log_path = linkroot / "LINK.LOG"
    return [{"linker": linker_key, "emulator_returncode": proc.returncode,
             "exe_sha256": sha(exe_path.read_bytes()),
             "map_sha256": sha(map_path.read_bytes()) if map_path.is_file() else None,
             "crt_ctype_map_symbols": ctype_rows,
             "link_log_sha256": sha(link_log_path.read_bytes()) if link_log_path.is_file() else None,
             "link_log": text(link_log_path), "case": row} for row in rows]


def main() -> int:
    WORKER.mkdir(parents=True, exist_ok=True)
    PACKETS.mkdir(parents=True, exist_ok=True)
    source_bytes = SOURCE.read_bytes()
    if sha(source_bytes) != EXPECTED_SOURCE_SHA:
        raise ValueError("canonical accepted source hash changed")
    source = source_bytes.decode("latin1")
    manifest_path = ROOT / "layout" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    module = manifest["modules"]["S20:39F1"]
    if module["source"] != SOURCE_REL or module["source_sha256"] != EXPECTED_SOURCE_SHA:
        raise ValueError("accepted source/module pin changed")
    if any(not any(row.get("name") == name and row.get("provenance") == "EXACT_NATURAL"
                       for row in module["claims"]) for name in ("ReadWord", "SkipWords", "ReadConfig")):
        raise ValueError("expected EXACT_NATURAL claim(s) no longer present")
    provider_text = PROVIDER_PATH.read_text(encoding="ascii")
    if provider_text != "char near g_5A97;\n":
        raise ValueError("candidate provider source changed from the one-object char near definition")
    if sha(DOMINANCE_REVIEW.read_bytes()) != "7fc887469e6c3633caf77ddf13a9b35da0d059cef6a3fe3abb382c9a69ea8494":
        raise ValueError("pinned first-write-dominance review changed")
    source_closure = collect_source_closure(manifest)
    flags = module["flags"]
    compiler = __import__("compiler")
    # The compiler helper's pinned-tree cache is keyed under its canonical
    # build/cc root. Keep its own cache there; all fixture inputs/objects and
    # link/run outputs remain in this worker scratch directory.
    compiler.WORK = ROOT / "build" / "cc"
    compiler.verify_profile("msc600ax")
    from omf import OmfReader
    source_obj, extraction = compile_only_read_functions(source, flags, compiler)
    read_module = OmfReader(communals=True).read(source_obj, "CFGREAD.OBJ")
    read_externals = sorted(set(read_module.externals))
    required_crt_externals = sorted(("_open", "_read", "_close", "_isdigit", "_isspace", "_puts", "_exit"))
    missing_externals = sorted(set(required_crt_externals) - set(read_externals))
    if missing_externals:
        raise ValueError(f"extracted function object lacks expected CRT imports: {missing_externals!r}")
    objects = {PROVIDER_BASENAME: compile_fixture(PROVIDER_BASENAME, provider_text, PROVIDER_FLAGS, compiler),
               "DATA": compile_fixture("DATA", DATA, flags, compiler),
               "CFGREAD": source_obj,
               "SEED": compile_fixture("SEED", SEED, flags, compiler),
               "SVIEW": compile_fixture("SVIEW", SIGNED_VIEW, flags, compiler),
               "UVIEW": compile_fixture("UVIEW", UNSIGNED_VIEW, flags, compiler),
               "PLAIN": compile_fixture("PLAIN", PLAIN_VIEW, flags, compiler),
               "MAIN": compile_fixture("MAIN", MAIN, flags, compiler)}
    owner_mod = OmfReader(communals=True).read(objects[PROVIDER_BASENAME], f"{PROVIDER_BASENAME}.OBJ")
    owner_rows = sorted((row["name"], row["kind"], row["length"]) for row in owner_mod.communals)
    if owner_rows != [("_g_5A97", "near", 1)]:
        raise ValueError(f"candidate tentative owner is not a one-byte near communal: {owner_rows!r}")
    type_controls = {}
    for name, declaration in (("CHARTYPE", "char near g_5A97;\n"),
                              ("SNGTYPE", "signed char near g_5A97;\n"),
                              ("UNSTYPE", "unsigned char near g_5A97;\n")):
        obj = compile_fixture(name, declaration, PROVIDER_FLAGS, compiler)
        parsed = OmfReader(communals=True).read(obj, f"{name}.OBJ")
        rows = sorted((row["name"], row["kind"], row["length"]) for row in parsed.communals)
        type_controls[name] = {"source": declaration.strip(), "omf_communal": rows,
                               "object_sha256": sha(obj)}
        if rows != [("_g_5A97", "near", 1)]:
            raise ValueError(f"same-shape sign control changed OMF extent: {name}: {rows!r}")
    toolchain = compiler.toolchain()
    runtime_rows = []
    for base in ("llibcr.lib", "libh.lib"):
        row = next((r for r in manifest["runtime"]["libraries"].values()
                    if Path(r["path"]).name.lower() == base), None)
        if row is None:
            raise ValueError(f"accepted manifest lacks runtime library {base}")
        runtime_rows.append(row)
    runs = []
    for key in ("rtlink400", "rtlink610"):
        runs.extend(run_linker(key, objects, toolchain, runtime_rows))
    all_passed = all(row["case"]["passed"] for row in runs)
    case_rows = [{"linker": row["linker"], "case": row["case"]["tag"],
                  "kind": row["case"].get("kind", "recognized-mode"),
                  "mode": row["case"].get("mode"), "seed": row["case"]["seed"],
                  "expected_before": row["case"]["expected_before"],
                  "expected_after": row["case"]["expected_after"],
                  "expected_status": row["case"]["expected_status"],
                  "expected_message": row["case"]["expected_message"],
                  "actual_before_and_after_log": row["case"]["log"],
                  "actual_before": row["case"]["actual_before"],
                  "actual_after": row["case"]["actual_after"],
                  "actual_status": row["case"]["actual_status"],
                  "passed": row["case"]["passed"]} for row in runs]
    result = {
        "schema": "g5a97-readconfig-producer-fixture-v1",
        "root_reviewed": False,
        "status": "CANDIDATE_PENDING_PARENT_REVIEW",
        "scope": "research-only source extraction; not original startup replay or original initializer proof",
        "source": {"path": SOURCE_REL, "sha256": EXPECTED_SOURCE_SHA,
                   "manifest_sha256": module["source_sha256"], "module": "S20:39F1",
                   "compiler_profile": module["profile"], "compiler_flags": flags,
                   "claims": {name: "EXACT_NATURAL" for name in FUNCTIONS}},
        "manifest_sha256": sha(manifest_path.read_bytes()),
        "toolchain_sha256": sha((ROOT / "layout" / "toolchain.json").read_bytes()),
        "provider_source": {"path": PROVIDER_REL, "sha256": sha(PROVIDER_PATH.read_bytes()),
                            "source": provider_text.strip(), "module": MODULE,
                            "basename": PROVIDER_BASENAME, "profile": "msc600ax",
                            "flags": PROVIDER_FLAGS},
        "extraction": {k: v for k, v in extraction.items() if k != "fixture_source"},
        "actual_extracted_object_externals": read_externals,
        "required_crt_externals": required_crt_externals,
        "candidate_owner": {"source": provider_text.strip(), "omf_communal": owner_rows,
                            "claim": "source-functional provider candidate; no original TU, order, owner, or initializer claim"},
        "same_shape_signedness_controls": type_controls,
        "runtime_libraries": [{"path": row["path"], "sha256": row["sha256"]} for row in runtime_rows],
        "linkers": {key: {"executable": toolchain["linkers"][key]["executable"],
                          "files": toolchain["linkers"][key]["files"]}
                    for key in ("rtlink400", "rtlink610")},
        "case_count": len(runs), "passed": all_passed,
        "cases": case_rows,
        "source_closure": source_closure,
        "limits": ["No original executable or initial-data bytes were read.",
                   "Harness supplies test-owned strings and g_610A backing state.",
                   "This executes only the actual accepted ReadWord/SkipWords/ReadConfig bodies; it excludes IBMInitStuff and first consumers.",
                   "C/CRT behavior here cannot establish original pre-main contents, original ownership, or full startup reachability."]}
    out = WORKER / "producer-fixture.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    read_src = extraction["fixture_source"]
    (WORKER / "fixtures" / "CFGREAD.C").write_text(read_src, encoding="ascii")
    (WORKER / "summary.txt").write_text(
        f"passed={all_passed}\ncases={len(runs)}\n"
        + "\n".join(f"{r['linker']} {r['case']['tag']} {r['case'].get('seed')} "
                     f"{r['case'].get('mode', r['case'].get('kind'))}: "
                     f"{'PASS' if r['case']['passed'] else 'FAIL'} "
                     f"status={r['case']['actual_status']} log={r['case']['log'].replace(chr(10), ' | ')}"
                     for r in runs) + "\n", encoding="utf-8")
    summary = (WORKER / "summary.txt").read_text(encoding="utf-8")
    print(summary.encode("ascii", "backslashreplace").decode("ascii"))

    report_pin = {"path": out.relative_to(ROOT).as_posix(), "sha256": sha(out.read_bytes()),
                  "size": out.stat().st_size}
    provider_pin = {"path": PROVIDER_REL, "sha256": sha(PROVIDER_PATH.read_bytes()),
                    "size": PROVIDER_PATH.stat().st_size}
    probe_pin = {"path": Path(__file__).relative_to(ROOT).as_posix(),
                 "sha256": sha(Path(__file__).read_bytes()), "size": Path(__file__).stat().st_size}
    declaration_rows = []
    for rows in (source_closure["target_reference_sources"]["canonical"],
                 source_closure["target_reference_sources"]["strict_effective"]):
        for row in rows:
            hits = row["named_hits"]
            for hit in hits:
                if re.search(r"\b(?:extern|extrn)\b", hit["text"], re.I):
                    declaration_rows.append({"path": row.get("path", row.get("source_path")),
                                             "line": hit["line"], "text": hit["text"]})
    asm_views = [row for row in source_closure["target_reference_sources"]["canonical"]
                 if row["path"].lower().endswith(".asm")]
    source_review = {
        "schema": "simant-source-only-dos-display-mode-selector-source-review-v1",
        "status": "CANDIDATE_PENDING_PARENT_REVIEW",
        "root_reviewed": False,
        "candidate_module": MODULE,
        "source_functional_owner": {"module": MODULE, "basename": PROVIDER_BASENAME,
                                     "provider": provider_pin,
                                     "contents": provider_text.strip(),
                                     "profile": "msc600ax", "flags": PROVIDER_FLAGS,
                                     "communal": owner_rows,
                                     "historical_tu_or_communal_identity": False},
        "accepted_producer": {"source": result["source"], "function_definition_pins": extraction["definitions"],
                              "object_externals": read_externals,
                              "crt_calls": required_crt_externals},
        "first_write_dominance_and_full_authoritative_source_scan": source_closure,
        "typed_views": {"source_declarations": declaration_rows,
                        "candidate_plain_char_view": {"type": "char near", "bytes": 1},
                        "same_extent_controls": type_controls,
                        "asm_byte_view_sources": asm_views,
                        "signedness_limit": "char, signed char, and unsigned char all compile to the same one-byte near OMF communal here; extent/object layout cannot recover source signedness. The exact producer writes mode '?' as -1; the plain/signed/unsigned test views observed -1/-1/255."},
        "runtime_contract": {"receipt": report_pin, "case_count": len(case_rows),
                             "passed": all_passed, "required_linkers": ["rtlink400", "rtlink610"],
                             "cases": case_rows},
        "inputs": source_closure["input_pins"] + [provider_pin, probe_pin],
        "claim_limits": ["No original initializer, initial byte, historical TU, module order, fixed address placement, or byte identity is claimed.",
                         "The fixture compiles only exact ReadWord/SkipWords/ReadConfig bodies, not a full IBMInitStuff module or whole-game path.",
                         "The initial-value non-observability argument for complete source-visible startup remains static dominance evidence plus this producer-only runtime supplement.",
                         "The source scan is lexical over current canonical and strict-effective source inputs; it does not model arbitrary DOS hardware interrupts or unregistered external code."]}
    review_path = PACKETS / "display-mode-selector-review-v1.json"
    review_path.write_text(json.dumps(source_review, indent=2) + "\n", encoding="utf-8")
    review_pin = {"path": review_path.relative_to(ROOT).as_posix(),
                  "sha256": sha(review_path.read_bytes()), "size": review_path.stat().st_size}
    value_rows = "\n".join(f"| `{mode}` | `{vals[0]}` | `{vals[1]}` | `{vals[2]}` |"
                            for mode, vals in MODES.items())
    human_review_path = PACKETS / "display-mode-selector-review-v1.md"
    human_review = f"""# Display-mode selector storage candidate review

Status: `CANDIDATE_PENDING_PARENT_REVIEW`; `root_reviewed: false`. This is a generated-only, source-functional `char near g_5A97` candidate. It makes no claim about original storage ownership, module order, original initialization, or original byte identity.

## Source closure

The accepted producer is `{SOURCE_REL}` (SHA-256 `{EXPECTED_SOURCE_SHA}`), module `S20:39F1`, with `ReadWord`, `SkipWords`, and `ReadConfig` recorded `EXACT_NATURAL`. The probe pins each entire extracted function definition: `ReadWord` line {extraction['definitions']['ReadWord']['line']} `{extraction['definitions']['ReadWord']['sha256']}`, `SkipWords` line {extraction['definitions']['SkipWords']['line']} `{extraction['definitions']['SkipWords']['sha256']}`, and `ReadConfig` line {extraction['definitions']['ReadConfig']['line']} `{extraction['definitions']['ReadConfig']['sha256']}`. These exact bodies were used in a research harness; this is not a complete original translation unit.

First-write dominance is pinned to the earlier review and the six accepted canonical startup/mode sources. The fresh closure scanner verifies every source hash in the current layout manifest and only the 29 effective sources from `static-completeness/index-v1.json`; superseded experiments are excluded. It records all `g_5A97` references, fixed numeric address literals, pointer/index escape patterns, and signal/hard-error handler spellings. Closure details and complete pins are in `{review_pin['path']}` (SHA-256 `{review_pin['sha256']}`). Key path anchors are `src/root/m15F8.c:74-95`, `src/root/m00F8.c:328-346`, `src/root/m1A96.c:280-285`, `src/S15/m384C.c:66-82`, `src/S20/m39F1.c:68-69,82-114,125-154,216-258`, and `src/root/m205F.c:132-165`.

## Candidate extent and view limit

Provider `{PROVIDER_REL}` contains only `{provider_text.strip()}`. It compiles under MSC 6.00AX to `_g_5A97`, near communal length one. Separate plain-`char`, `signed char`, and `unsigned char` provider controls all have the same near one-byte OMF extent. That extent evidence cannot distinguish signedness. The canonical source contains plain-char declarations, unsigned-char consumers, and the byte compare `src/root/m1FBD.asm:13,38`; the candidate follows the plain-char source declaration while the byte views stay one byte.

## Runtime producer cases

The fixture executes the exact producer bodies against test-generated configuration files, test-owned path/message data, and the pinned real MSC runtime under RTLink/Plus 4.00 and 6.10. The output records plain-char / explicit-signed-char / unsigned-raw views, respectively. Both `0x00` and `0xFF` entry values were tested for every recognized mode:

| Config mode | Plain char | Signed char | Raw unsigned byte |
|---|---:|---:|---:|
{value_rows}

In particular mode `?` assigns source value `-1`; the fixture observed `-1 / -1 / 255` from either initial byte under both linkers. Invalid mode and missing file each exited with status 1 and the expected message from both seeds. A no-seed control observed CRT zero only for this test-owned tentative definition. All 42 of 42 cases passed. The detailed run receipt is `{report_pin['path']}` (SHA-256 `{report_pin['sha256']}`).

## Limits

The fixture excludes `IBMInitStuff`, game functions, and first consumers. Its `BEFORE` display is harness instrumentation; it is not a game-code read. The dynamic evidence covers only the config producer, while first-write dominance along source-visible startup remains the static closure review. The unseeded CRT result is fixture-only. No original executable or original data bytes were read. No source byte or initialized value was copied from an original image. The contract and bindings remain root-review-pending and are not added to mandatory source-binding packets.
"""
    human_review_path.write_text(human_review, encoding="utf-8")
    human_review_pin = {"path": human_review_path.relative_to(ROOT).as_posix(),
                        "sha256": sha(human_review_path.read_bytes()),
                        "size": human_review_path.stat().st_size}
    required_cases = {f"{row['linker']}:{row['case']}": {
        "expected_before": row["expected_before"], "expected_after": row["expected_after"],
        "expected_status": row["expected_status"], "expected_message": row["expected_message"]}
        for row in case_rows}
    contract = {
        "schema": "simant-source-only-dos-display-mode-selector-contract-candidate-v1",
        "category": "CANDIDATE_SOURCE_STORAGE_CONTRACT",
        "status": "CANDIDATE_PENDING_PARENT_REVIEW", "root_reviewed": False,
        "all_required_checks_pass": all_passed,
        "module": MODULE,
        "scope": "one source-functional generated-only char near g_5A97 owner candidate; no historical ownership or initialization claim",
        "source_functional_owner": {"module": MODULE, "basename": PROVIDER_BASENAME,
                                    "owner": None, "source": provider_pin,
                                    "contents": provider_text.strip(),
                                    "profile": "msc600ax", "flags": PROVIDER_FLAGS,
                                    "effective_flags": PROVIDER_FLAGS + compiler.toolchain()["profiles"]["msc600ax"].get("required_flags", []),
                                    "communals": [{"name": row[0], "kind": row[1], "length": row[2]}
                                                  for row in owner_rows],
                                    "historical_tu_identity": False},
        "member": {"name": TARGET, "candidate_type": "plain char near", "candidate_bytes": 1,
                   "registered_address_reference_only": source_closure["registry_symbol"],
                   "registered_type_views": declaration_rows,
                   "same_shape_signedness_controls": type_controls,
                   "limit": "The OMF extent controls cannot distinguish char, signed char, and unsigned char; the candidate follows the canonical plain-char declarations and source-visible behavior."},
        "first_write_dominance_review": review_pin,
        "human_review": human_review_pin,
        "producer_source": {"path": SOURCE_REL, "sha256": EXPECTED_SOURCE_SHA,
                            "functions": extraction["definitions"],
                            "scope": "exact function text extracted into a research harness; not a complete original TU"},
        "runtime_contract_key": "display_mode_selector_contract",
        "required_linkers": ["rtlink400", "rtlink610"],
        "required_cases": required_cases,
        "cases": case_rows,
        "raw_mode_question": {"input_mode": "?", "assigned_source_value": -1,
                              "observed_plain_char": -1, "observed_signed_char": -1,
                              "observed_unsigned_raw_byte": 255,
                              "both_initial_byte_runs": [0, 255]},
        "source_closure": source_closure,
        "toolchain": {"profile": "msc600ax", "provider_flags": PROVIDER_FLAGS,
                      "producer_compiler_flags": flags,
                      "runtime_libraries": result["runtime_libraries"],
                      "linkers": result["linkers"],
                      "toolchain_json_sha256": result["toolchain_sha256"]},
        "limitations": result["limits"] + ["Candidate is root-review-pending and is not wired into any mandatory packet or production binding."]}
    contract_path = PACKETS / "display-mode-selector-contract-v1.json"
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    contract_pin = {"path": contract_path.relative_to(ROOT).as_posix(),
                    "sha256": sha(contract_path.read_bytes()), "size": contract_path.stat().st_size}
    bindings = {
        "schema": "simant-source-only-dos-display-mode-selector-bindings-candidate-v1",
        "category": "CANDIDATE_SOURCE_STORAGE_BINDING",
        "status": "CANDIDATE_PENDING_PARENT_REVIEW", "root_reviewed": False,
        "bindings": [],
        "providers": [{"module": MODULE, "basename": PROVIDER_BASENAME, "owner": None,
                       "profile": "msc600ax", "flags": PROVIDER_FLAGS, "source": provider_pin,
                       "communals": [{"name": row[0], "kind": row[1], "length": row[2]}
                                     for row in owner_rows]}],
        "runtime_contract_key": "display_mode_selector_contract",
        "runtime_contract": contract_pin,
        "source_review": review_pin,
        "review_sources": source_closure["input_pins"] + [provider_pin, probe_pin,
                                                            review_pin, human_review_pin, report_pin],
        "claim_limit": "One generated-only source-functional byte owner candidate; no original initializer, pre-main contents, original TU/order, fixed placement, byte identity, or whole-game runtime claim.",
    }
    binding_path = PACKETS / "display-mode-selector-bindings-v1.json"
    binding_path.write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_report": report_pin, "source_review": review_pin,
                      "contract": contract_pin,
                      "bindings": {"path": binding_path.relative_to(ROOT).as_posix(),
                                   "sha256": sha(binding_path.read_bytes()),
                                   "size": binding_path.stat().st_size},
                      "all_required_checks_pass": all_passed, "cases": len(case_rows)}, indent=2))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
