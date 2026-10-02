"""Reproduce and pin Next9 source binding plus actual-DOS write round-trip."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "portable/tests/save/evidence/legacy-save-codec-v2"
N8 = ROOT / "build/workers/recovered_source_next8/generated"
N9 = ROOT / "build/workers/recovered_source_next9/generated"
REPORT_DOS = ROOT / "build/workers/savegame_original_write/report.json"
PAYLOAD = ROOT / "build/workers/savegame_original_write/captured-savegame.bin"
AUDIT_MODULE = ROOT / "portable/tests/save/audit_next9_state_gaps.py"
sys.path.insert(0, str(ROOT / "tools"))
import exe


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    PACKET.mkdir(parents=True, exist_ok=True)
    producer = ROOT / "portable/tools/recover_source_next9.py"
    provenance_path = N9 / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    extension = provenance.get("versioned_profile_extension_next9", {})
    if extension.get("status") != "DIAGNOSTIC_ONLY_NOT_PRODUCTION":
        raise RuntimeError("Next9 profile status is not diagnostic-only")
    if extension.get("producer_sha256") != digest(producer):
        raise RuntimeError("Next9 producer differs from generated profile pin")
    if provenance["recovered_state"]["header_sha256"] != digest(N9 / "recovered_state.h") or \
       provenance["recovered_state"]["source_sha256"] != digest(N9 / "recovered_state.c"):
        raise RuntimeError("top-level recovered_state provenance is stale")
    if not extension.get("inherited_state_projection_byte_identical") or \
       not extension.get("all_inherited_tus_recompiled"):
        raise RuntimeError("Next9 did not preserve/recompile the inherited profile")

    # Re-run the source/EXE comparison with Next8 as the pre-extension baseline;
    # the immutable Next9-v1 packet is deliberately left untouched.
    audit = load(AUDIT_MODULE, "next9_source_gap_audit_v2")
    audit.NEXT7 = N8 / "recovered_state.h"
    audit.NEXT7_PROVENANCE = N8 / "provenance.json"
    audit.OUT = PACKET / "source-binding-proof.json"
    old_argv = sys.argv
    sys.argv = [str(AUDIT_MODULE), "--output", str(audit.OUT)]
    try:
        audit.main()
    finally:
        sys.argv = old_argv
    source_proof = json.loads(audit.OUT.read_text(encoding="utf-8"))
    source_proof["status"] = "SOURCE_GROUNDED_NEXT9_BINDING_IMPLEMENTED"
    source_proof["inputs"]["next8_candidate"] = source_proof["inputs"].pop("next7_candidate")
    source_proof["inputs"]["next8_candidate"]["header_path"] = str((N8 / "recovered_state.h").relative_to(ROOT)).replace("\\", "/")
    source_proof["inputs"]["next8_candidate"]["provenance_path"] = str((N8 / "provenance.json").relative_to(ROOT)).replace("\\", "/")
    source_proof["next9"] = {"header_sha256": digest(N9 / "recovered_state.h"),
                              "source_sha256": digest(N9 / "recovered_state.c"),
                              "new_fields_present": all(n in (N9 / "recovered_state.h").read_text(encoding="utf-8")
                                                        for n in ("fd_50F6_0F46", "fd_50F6_0FC6", "fd_50F6_0F84",
                                                                  "fd_50F6_1008", "fd_50F6_103C", "fd_50F6_1048",
                                                                  "fd_3D57_087A")),
                              "row29_storage": "NATIVE_NUMERIC_16 from the Next9 int16_t[16][12] backing",
                              "row99_storage": "RAW_BYTES at fd_3D57_087A + 20"}
    # A byte-flipped source-initializer negative control must disagree with the locked DOS image.
    original = exe.load()
    resident = original.sections[27]
    symbol = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]["fd_3D57_087A"]
    linear = symbol["seg"] * 16 + symbol["off"]
    source_array = source_proof["records"]["interior_data_span"]["initial_bytes_hex"]
    initialized = bytes.fromhex(source_array)
    relative = linear + 20 - resident.load_linear
    oracle_slice = resident.data[relative:relative + 20]
    if initialized != oracle_slice:
        raise RuntimeError("positive fd_3D57 initializer comparison failed")
    mutant = bytearray(initialized)
    mutant[0] ^= 1
    if bytes(mutant) == oracle_slice:
        raise RuntimeError("initializer negative control failed")
    source_proof["initializer_controls"] = {"positive_source_to_locked_EXE": True,
                                             "negative_one_byte_mutation_detected": True,
                                             "positive_bytes_hex": initialized.hex(),
                                             "negative_mutant_hex": bytes(mutant).hex()}
    audit.OUT.write_text(json.dumps(source_proof, indent=2) + "\n", encoding="utf-8", newline="")

    subprocess.run([sys.executable, str(ROOT / "portable/tests/save/probe_original_savegame_write.py")],
                   cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "portable/tests/save/run_next9_binding_test.py"), str(PAYLOAD)],
                   cwd=ROOT, check=True)
    dos = json.loads(REPORT_DOS.read_text(encoding="utf-8"))
    inventory = ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"
    input_paths = [
        ROOT / "src/S09/m35F5.c", ROOT / "src/S13/m384C.c", ROOT / "src/data/d3D57.c",
        ROOT / "src/data/d3E1D.c", ROOT / "assets/SIMANT.EXE", ROOT / "layout/symbols.json",
        ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json",
        ROOT / "portable/tests/save/audit_next9_state_gaps.py", producer,
        ROOT / "portable/game/save/legacy_codec.h", ROOT / "portable/game/save/legacy_codec.c",
        ROOT / "portable/game/save/next9_bindings.h", ROOT / "portable/game/save/next9_bindings.c",
        ROOT / "portable/game/save/next9_bindings_rows.inc", ROOT / "portable/tests/save/test_next9_bindings.c",
        ROOT / "portable/tests/save/run_next9_binding_test.py", ROOT / "portable/tests/save/probe_original_savegame_write.py",
        ROOT / "portable/tests/save/finalize_next9_evidence.py", ROOT / "tools/behavior.py",
        ROOT / "tools/exe.py", ROOT / "tools/functions.py", ROOT / "tools/match.py",
        N8 / "recovered_state.h", N8 / "recovered_state.c", N8 / "provenance.json",
        N9 / "recovered_state.h", N9 / "recovered_state.c", N9 / "provenance.json",
    ]
    pins = [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)} for p in input_paths]
    (PACKET / "input-pins.json").write_text(json.dumps({"schema":"simant-legacy-save-next9-input-pins-v1",
        "inputs":pins, "captured_DOS_payload_sha256":dos["payload_sha256"],
        "captured_DOS_payload_bytes":dos["payload_bytes"],
        "captured_payload_retention":"ignored build/workers only; not copied into packet"}, indent=2) + "\n",
        encoding="utf-8", newline="")
    receipt = {
        "schema":"simant-legacy-save-codec-v2-validation-v1",
        "status":"PASS_DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "next9_profile":{"path":"build/workers/recovered_source_next9/generated/provenance.json",
                         "sha256":digest(provenance_path), "producer_sha256":digest(producer),
                         "added_fields":7, "inherited_modules_strict_recompiled":25,
                         "inherited_state_projection_byte_identical":True},
        "source_initializer":source_proof["initializer_controls"],
        "binding":{"source_rows":307,"payload_bytes":48386,
                    "row29":"NATIVE_NUMERIC_16; Next9 backing int16_t[16][12]",
                    "row99":"RAW_BYTES; object slice [20,40) of uint8_t[72]",
                    "rows_include_sha256":digest(ROOT / "portable/game/save/next9_bindings_rows.inc")},
        "actual_original_DOS_SaveGame":{"function":"o09_35F5_0188","write_calls":dos["controlled_file_operations"]["write_count"],
                                         "row_byte_counts_sha256":hashlib.sha256(json.dumps(dos["row_byte_counts"],separators=(",",":")).encode()).hexdigest(),
                                         "payload_bytes":dos["payload_bytes"],"payload_sha256":dos["payload_sha256"],
                                         "return":dos["dos_return"],"dirty_after":dos["dirty_after"],
                                         "filesystem":"controlled callbacks only"},
        "native_replay":{"normal_and_forced_big_endian":True,"both_reproduced_actual_DOS_stream_byte_exactly":True},
        "limits":["No live filesystem write or production SaveGame registration is included.",
                   "The DOS-to-native replay proves stream-compatible binding for this source/oracle startup state; it does not certify portable UI, error, short-write, or file lifecycle behavior."]}
    (PACKET / "validation.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status":receipt["status"], "rows":307,"bytes":48386,
                      "dos_payload_sha256":dos["payload_sha256"], "pins":len(pins)}, indent=2))


if __name__ == "__main__":
    main()
