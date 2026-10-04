from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORT = HERE / "pinned-build-report-observation-3d4db030.json"
STALE_INTAKE = HERE / "stale-current-intake-reference-1479f57f.json"
OUT = HERE / "v22-static-closure-receipt.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


SOURCE_PINS = [
    "src/root/m1A28.c",
    "src/root/m1A53.c",
    "src/S20/m39F1.c",
    "src/root/m205F.c",
    "src/root/m15F8.c",
    "src/root/m1C62.c",
    "src/root/m1CE2.c",
    "src/S15/m384C.c",
    "src/root/m277E.c",
    "src/root/m0000.c",
    "src/root/m295C.c",
    "src/root/m284A.c",
    "src/root/m28BC.asm",
    "src/root/m1B4E.asm",
    "src/root/m00DF.c",
    "src/root/m293A.c",
    "src/root/m1986.c",
    "src/root/m19A9.c",
    "src/root/m19DC.c",
    "src/root/m1B28.c",
    "src/root/m171C.c",
    "src/root/m1B73.asm",
    "src/root/m00DE.c",
]

PACKET_PINS = [
    "work/source-only-dos/database-record-state-contract-v1.json",
    "work/source-only-dos/database-record-state-bindings-v1.json",
    "work/source-only-dos/database-record-state-review-v1.md",
    "work/source-only-dos/providers/database-record-state.c",
    "work/source-only-dos/database-record-state-probe.py",
    "work/source-only-dos/sound-record-arrays-contract-v1.json",
    "work/source-only-dos/sound-record-arrays-bindings-v1.json",
    "work/source-only-dos/sound-record-arrays-v21/review.json",
    "work/source-only-dos/sound-record-arrays-v21/review.md",
    "work/source-only-dos/sound-record-arrays-v21/provider.c",
    "work/source-only-dos/sound-record-arrays-v21/probe.py",
    "work/source-only-dos/sound-record-arrays-v21/runtime-receipt.json",
    "work/source-only-dos/saved-sound-state-contract-v1.json",
    "work/source-only-dos/saved-sound-state-bindings-v1.json",
    "work/source-only-dos/saved-sound-state-v19/review.json",
    "work/source-only-dos/saved-sound-state-v19/review.md",
    "work/source-only-dos/saved-sound-state-v19/provider.c",
    "work/source-only-dos/saved-sound-state-v19/probe.py",
    "work/source-only-dos/saved-sound-state-v19/runtime-receipt.json",
    "work/source-only-dos/callback-table-reviewed-contract-v1.json",
    "work/source-only-dos/callback-table-bindings-v1.json",
    "work/source-only-dos/callback-table-review-v3.md",
    "work/source-only-dos/providers/callback-table.c",
    "work/source-only-dos/callback-table-probe.py",
    "work/source-only-dos/storage-admission-v21.md",
    "work/source-only-dos/database-punt-static-dependency-proof-candidate-v3.json",
    "work/source-only-dos/database-punt-static-dependency-review-v3.md",
    "work/source-only-dos/database-punt-call-closure-supplement-v3.json",
    "work/source-only-dos/database-punt-effective-overlay-check-v16.json",
    "work/source-only-dos/database-punt-root-review-v17.md",
    "work/source-only-dos/database-punt-crt-control/crt-exit-control-result.json",
    "layout/symbols.json",
    "build/workers/dos_db_punt_gate_v22/verify_boundary_receipt.py",
]

report = json.loads(REPORT.read_text(encoding="utf-8"))
intake = json.loads(STALE_INTAKE.read_text(encoding="utf-8"))
units = report["translation_units"]
canonical = [u for u in units if u.get("source", {}).get("path", "").replace("\\", "/").startswith("src/")]
provider_rows = [u for u in units if u not in canonical]

source_join_errors: list[dict] = []
for unit in units:
    for field in ("source", "generated_source"):
        item = unit.get(field)
        if not item:
            continue
        path = ROOT / item["path"].replace("\\", "/")
        if not path.is_file():
            source_join_errors.append({"module": unit.get("module"), "field": field, "path": item["path"], "error": "missing"})
            continue
        actual = sha256(path)
        if actual != item["sha256"]:
            source_join_errors.append({"module": unit.get("module"), "field": field, "path": item["path"], "expected": item["sha256"], "actual": actual})

unit_by_module = {u.get("module"): u for u in units}
unit_by_unit = {u.get("unit"): u for u in units}
strict_joins: list[dict] = []
strict_errors: list[dict] = []
for name, row in report.get("strict_static_audit", {}).items():
    receipt_ref = row.get("receipt", {})
    receipt_path = ROOT / receipt_ref.get("path", "").replace("\\", "/")
    if not receipt_path.is_file() or sha256(receipt_path) != receipt_ref.get("sha256"):
        strict_errors.append({"name": name, "kind": "receipt", "path": receipt_ref.get("path")})
        continue
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for kind in ("registered_source", "source_override"):
        item = receipt.get(kind) or row.get(kind)
        if item and item.get("path"):
            source_path = ROOT / item["path"].replace("\\", "/")
            if not source_path.is_file() or sha256(source_path) != item.get("sha256"):
                strict_errors.append({"name": name, "kind": kind, "path": item["path"]})
    declared_module = (receipt.get("registered_source") or {}).get("module")
    joined_unit = unit_by_module.get(declared_module) or unit_by_unit.get(declared_module)
    if joined_unit is None:
        joined_unit = next((u for u in units if u.get("module", "").startswith(declared_module + ":")), None)
    if joined_unit is None:
        strict_errors.append({"name": name, "kind": "effective_module_join", "module": declared_module})
    strict_joins.append({
        "name": name,
        "status": row.get("status"),
        "receipt": receipt_ref,
        "registered_source": receipt.get("registered_source"),
        "source_override": receipt.get("source_override") or row.get("source_override"),
        "effective_module": joined_unit.get("module") if joined_unit else None,
        "effective_source": joined_unit.get("source") if joined_unit else None,
        "effective_generated_source": joined_unit.get("generated_source") if joined_unit else None,
    })

targets = ("db_SetDataBase", "db_CloseDataBase", "OpenDB", "CloseDB", "GetFreeHandle", "IBMInitStuff", "f_205F_0004")
target_occurrences: dict[str, list[dict]] = {t: [] for t in targets}
address_takings: dict[str, list[dict]] = {t: [] for t in targets}
symbol_rx = {t: re.compile(r"(?<![A-Za-z0-9_])_?" + re.escape(t) + r"(?![A-Za-z0-9_])") for t in targets}
for unit in units:
    item = unit.get("generated_source")
    if not item:
        continue
    path = ROOT / item["path"].replace("\\", "/")
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith(("//", "/*", "*", ";")):
            continue
        for target, pattern in symbol_rx.items():
            if pattern.search(line):
                target_occurrences[target].append({"module": unit.get("module"), "source": item["path"], "line": number, "text": stripped[:180]})
                if re.search(r"&\s*_?" + re.escape(target) + r"\b|=\s*_?" + re.escape(target) + r"\b(?!\s*\()", line):
                    address_takings[target].append({"module": unit.get("module"), "source": item["path"], "line": number, "text": stripped[:180]})

symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))
aliases = []
target_set = set(targets)
for section in ("code", "data", "runtime"):
    for name, row in symbols.get(section, {}).items():
        if isinstance(row, dict) and row.get("alias_of") in target_set:
            aliases.append({"name": name, "alias_of": row["alias_of"], "section": section})
alias_occurrences: list[dict] = []
for alias in aliases:
    name = alias["name"]
    pattern = re.compile(r"(?<![A-Za-z0-9_])_?" + re.escape(name) + r"(?![A-Za-z0-9_])")
    for unit in units:
        item = unit.get("generated_source")
        if not item:
            continue
        path = ROOT / item["path"].replace("\\", "/")
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("//", "/*", "*", ";")):
                continue
            if pattern.search(line):
                alias_occurrences.append({"alias": name, "alias_of": alias["alias_of"], "module": unit.get("module"), "source": item["path"], "line": number, "text": stripped[:180]})

pin_paths = SOURCE_PINS + PACKET_PINS
pins = []
for relative in pin_paths:
    path = ROOT / relative
    if not path.is_file():
        raise SystemExit(f"missing pinned input: {relative}")
    pins.append({"path": relative, "sha256": sha256(path), "size": path.stat().st_size})

dependencies = {d["id"]: d.get("status") for d in report.get("layout_dependencies", []) if d.get("id") in ("database-open-minus-one-record", "database-handle-plus-four")}
contracts = {
    name: {"root_reviewed": report[name].get("root_reviewed"), "all_required_checks_pass": report[name].get("all_required_checks_pass"), "required_cases": report[name].get("required_cases")}
    for name in ("database_record_state_contract", "sound_record_arrays_contract", "saved_sound_state_contract", "callback_storage_contract")
}

receipt = {
    "schema": "simant-dos-db-punt-static-closure-review-v22",
    "classification": "ROOT_FALSE_UNRESOLVED",
    "gates": {"database-open-minus-one-record": "UNCHANGED_UNRESOLVED", "database-handle-plus-four": "UNCHANGED_UNRESOLVED"},
    "observation": {
        "report_snapshot": REPORT.name,
        "report_sha256": sha256(REPORT),
        "report_size": REPORT.stat().st_size,
        "report_status": report.get("status"),
        "report_translation_units": len(units),
        "effective_canonical_source_rows": len(canonical),
        "source_owned_provider_rows": len(provider_rows),
        "strict_static_audit_entries": len(strict_joins),
        "current_intake_reference": STALE_INTAKE.name,
        "current_intake_sha256": sha256(STALE_INTAKE),
        "current_intake_declared_report_sha256": intake.get("full_local_report", {}).get("sha256"),
        "current_intake_matches_report_snapshot": intake.get("full_local_report", {}).get("sha256") == sha256(REPORT),
        "head_claim": "none; report is a mutable build observation, not asserted to belong to HEAD",
    },
    "verification": {
        "all_report_source_and_generated_source_hashes_match": not source_join_errors,
        "source_rows_verified": len(units) * 2,
        "source_join_errors": source_join_errors,
        "all_strict_receipt_and_registered_source_hashes_match": not strict_errors,
        "strict_receipt_join_count": len(strict_joins),
        "strict_join_errors": strict_errors,
        "strict_joins": strict_joins,
    },
    "source_call_inventory": {
        "symbol_occurrences": target_occurrences,
        "address_takings": address_takings,
        "layout_symbol_aliases": aliases,
        "alias_occurrences": alias_occurrences,
        "scope": "current report's 127 canonical generated source rows plus 37 source-owned rows; references in strict receipts separately pinned and joined above",
    },
    "owner_contracts": contracts,
    "observed_report_gate_status": dependencies,
    "pinned_source_and_owner_inputs": pins,
    "source_conclusion": {
        "sound_attempt_frontier": [
            "main closes its five install.exe probe handles, then calls IBMInitStuff, then db_SetDataBase(\"sound\") only after IBMInitStuff returns.",
            "IBMInitStuff resets g_610A=-1; language DB is conditional on open(language.dat)>0; shared DB is unconditional; lrshare DB is conditional on display selector 2 or 4.",
            "f_205F_0004 is called once from IBMInitStuff. It calls f_1B4E_0025 before its one display db_SetDataBase(path); f_1B4E_0025 copies 25 no-op far pointers into the g_9128..g_9188 table.",
            "With optional language and lrshare both present and all four preceding DB calls returning successfully, the display DB is the fourth active record and main's sound DB is the fifth attempt. Missing either optional open leaves a free record. This bounded count requires all predecessor opens to RETURN SUCCESSFULLY and requires no earlier first Punt to return; four attempted calls alone do not establish it.",
        ],
        "direct_call_findings": [
            "OpenDB's only source caller is db_SetDataBase; GetFreeHandle's only source caller is OpenDB.",
            "The source-exact scan finds only the three IBMInitStuff predecessor calls, the one display DB call, and main's sound DB call; no address-taking of these functions is present in current generated source.",
            "db_CloseDataBase is defined, but the only executable occurrence is its definition; CloseDB is only called inside it. No source-reachable db_CloseDataBase/CloseDB shutdown occurs before main's sound DB open. No repeated f_205F_0004 call is present in the 127 canonical rows or 37 provider rows.",
        ],
        "early_pre_display_failure": {
            "trigger": "A failing language/shared/lrshare OpenDB can call DosPunt/Punt before IBMInitStuff reaches f_205F_0004.",
            "callback_state": "driver_callback_table has no initializer and its slot-zero alias is g_9128; the only source initialization is f_1B4E_0025 inside f_205F_0004, after those DB calls. The first pre-display Punt therefore dispatches through a source-zero far function pointer, target 0000:0000, before the fatal helper.",
            "guard": "Punt writes g_54F8=1 before the indirect g_9128 call. If this first pre-display Punt path returns to startup rather than terminating, the guard remains set; a later full-handle Punt takes the recursive immediate-return branch and exposes OpenDB's slot -1 access. If OpenDB then returns -1, db_SetDataBase writes db_handles[4] before testing handle<0.",
            "result": "The behavior of an indirect call through the zero far pointer to 0000:0000 as code is outside the source/owner proof. No physical IVT bytes were read, no arbitrary callback behavior was assumed, and no original linker-layout inference was used. Because this early-Punt return/termination boundary is not proved, the five-open bound cannot close either gate.",
        },
        "normal_fifth_open_fatal_path": [
            "When all four preceding DB opens succeed with no prior Punt, the fifth-open Punt is the outer first Punt after display setup and g_9128 initialization.",
            "g_2BD4 starts at 1 and fd_55B3_610A starts at -1, so fatal cleanup enters f_277E_0154. Chan cleanup reads the 4A4E.type sentinel; the admitted 33x6-byte FAR_BSS owner starts zero. StopSong skips because g_756E starts zero. f_0000_0429 repeats channel cleanup and scans Voice[0..55]; the admitted 56x6-byte FAR_BSS owner has kind=0 rows. Saved sound state has seven zero words; saved mode zero selects g_68DA[0]=f_277E_0938 (empty).",
            "f_28BC_04E0(0) is a real pre-init timer restore, not a no-op: it writes PIT state and restores INT 08h from the source-owned zero old_int8 field. That side effect remains explicit and requires the game fatal-path DOSBox comparison for execution acceptance; it is not a database-layout structural blocker.",
            "The fatal helper then has an unconditional C exit(0) source path; the pinned standalone MSC/RTLink control verifies C exit termination only, not this game fatal integration or the early zero-callback boundary.",
        ],
        "other_boundary_checks": [
            "No source caller of db_CloseDataBase, no independent CloseDB call, no OpenDB address-taking, and no repeated display setup are found in the current effective source rows.",
            "A db_CloseDataBase call before sound would decrement the active count and clear record name[0], but no such pre-sound path is source-reachable in the audited set.",
            "The post-init /s9 selector/layout issue is separate and not used to bound this pre-init fifth-open frontier.",
            "The old v17 blanket first-Punt/nonreturn review and v3 source-closure artifacts are pinned as historical research only; they are not current admission authority and are not used to claim PASS.",
        ],
    },
    "negative_controls": {
        "actual_owner_shape_controls": {
            "database_records": "actual contract controls: three-record extent, near index pointer, unsigned handle, and nonzero initializer rejected; contract explicitly excludes slot -1 and db_handles[4] semantics",
            "sound_arrays": "actual contract controls: wrong voice count/stride, unsigned word view, near pointer view, short extent, and initialized storage",
            "saved_sound_state": "actual contract controls: nonzero initializer, wrong width, and short extent",
            "callback_table": "actual contract controls: wrong alias offset, nonzero initialized owner, and wrong g_3DF8 base",
            "strict_imports": "29 current strict receipts and their registered source/override paths are hash-verified; these do not test the pre-display null-callback return boundary",
            "crt_exit": "actual standalone MSC/RTLink C exit control; it does not link the game fatal path",
        },
        "proposed_only_boundary_contrast": "A future bounded integration comparison should contrast a normal four-success/fifth-open fatal path with the earliest failing pre-display DB open while g_9128 is source-zero; record whether the external 0000:0000 call traps, returns through fatal handling, or reaches startup continuation. This review runs no probe and makes no injected dummy callback or no-return change.",
    },
    "fail_closed_check": {
        "required_to_close": [
            "prove the pre-display first-Punt zero-target boundary cannot return to startup or otherwise reach the sound DB call, using accepted source/runtime evidence rather than a guessed far-pointer target",
            "keep every effective source, strict-source receipt, owner packet, callback/interrupt target, and full-exit terminator joined by exact hashes",
            "only then close each OOB access as unreachable; do not change owner extent, add a fifth element, add padding, clamp, or annotate Punt noreturn",
        ],
        "current_decision": "UNRESOLVED; keep both production gates unchanged",
    },
}

OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "receipt": str(OUT),
    "report_sha256": sha256(REPORT),
    "report_units": len(units),
    "canonical_rows": len(canonical),
    "provider_rows": len(provider_rows),
    "strict_receipts": len(strict_joins),
    "source_join_errors": len(source_join_errors),
    "strict_join_errors": len(strict_errors),
    "gate_status": dependencies,
    "stale_intake_declared_report_sha256": intake.get("full_local_report", {}).get("sha256"),
}, indent=2))
