"""Add the seven source-grounded legacy SaveRec state fields over pinned Next8.

This diagnostic producer leaves all earlier producers and profiles untouched.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NEXT8 = ROOT / "portable/tools/recover_source_next8.py"
NEXT8_SHA = "9951389f4e19b1dc7eea93c0f8f6df02e444e7e7b9a32952b77830c157c3fb64"
NEXT8_PROVENANCE_SHA = "2d6a17dd70cde672233b545318d21c73cead426a468dc4dbdfa12f10c1645c20"
NEXT8_HEADER_SHA = "8d22b87f06dbc9f9761cf7ae33e0219b1f10e6e33ebdfecf80c625af7f454268"
NEXT8_SOURCE_SHA = "697b4013bb4660ab82916e3eb7b8003f2e0078ba272f18cd3c68344cdc82ccbe"
OUT_DIR = "build/workers/recovered_source_next9/generated"
DATA = ROOT / "src/data/d3D57.c"
SOURCE_NAMES = ["fd_50F6_0F46", "fd_50F6_0FC6", "fd_50F6_0F84", "fd_50F6_1008",
                "fd_50F6_103C", "fd_50F6_1048", "fd_3D57_087A"]
INVENTORY = ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"
ROWS_OUT = ROOT / "portable/game/save/next9_bindings_rows.inc"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"expected one {label} anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    if sha(NEXT8.read_bytes()) != NEXT8_SHA:
        raise RuntimeError("pinned Next8 wrapper changed")
    n8dir = ROOT / "build/workers/recovered_source_next8/generated"
    if sha((n8dir / "provenance.json").read_bytes()) != NEXT8_PROVENANCE_SHA:
        raise RuntimeError("pinned Next8 provenance changed")
    if sha((n8dir / "recovered_state.h").read_bytes()) != NEXT8_HEADER_SHA or \
       sha((n8dir / "recovered_state.c").read_bytes()) != NEXT8_SOURCE_SHA:
        raise RuntimeError("pinned Next8 state files changed")

    argv = sys.argv[1:]
    if "--out" not in argv:
        argv += ["--out", OUT_DIR]
    if "--compile" not in argv:
        argv.append("--compile")
    next8 = load(NEXT8, "recover_source_next8_for_next9")
    old_argv = sys.argv
    sys.argv = [str(NEXT8), *argv]
    try:
        result = next8.main()
    finally:
        sys.argv = old_argv
    if result:
        return result
    out_arg = argv[argv.index("--out") + 1]
    out = (ROOT / out_arg).resolve() if not Path(out_arg).is_absolute() else Path(out_arg).resolve()
    prov_path = out / "provenance.json"
    provenance = json.loads(prov_path.read_text(encoding="utf-8"))
    module_hashes = {row["name"]: row["generated_sha256"] for row in provenance["modules"]}

    header_path, source_path = out / "recovered_state.h", out / "recovered_state.c"
    h = header_path.read_text(encoding="utf-8")
    c = source_path.read_text(encoding="utf-8")
    members = """    int8_t fd_50F6_0F46[50];
    int8_t fd_50F6_0FC6[50];
    int8_t fd_50F6_0F84[50];
    int8_t fd_50F6_1008[50];
    int16_t fd_50F6_103C;
    int16_t fd_50F6_1048;
    uint8_t fd_3D57_087A[72];
"""
    h = replace_once(h, "} RecoveredState;\n",
                     members + "} RecoveredState;\n", "appended RecoveredState members")
    globals_text = """_Thread_local int8_t fd_50F6_0F46[50];
_Thread_local int8_t fd_50F6_0FC6[50];
_Thread_local int8_t fd_50F6_0F84[50];
_Thread_local int8_t fd_50F6_1008[50];
_Thread_local int16_t fd_50F6_103C;
_Thread_local int16_t fd_50F6_1048;
_Thread_local uint8_t fd_3D57_087A[72];
"""
    c = replace_once(c, "_Thread_local int16_t EatCnt;\n", "_Thread_local int16_t EatCnt;\n" + globals_text,
                     "TLS definitions")
    h = replace_once(h, "extern _Thread_local int16_t EatCnt;\n",
                     "extern _Thread_local int16_t EatCnt;\n" +
                     "extern _Thread_local int8_t fd_50F6_0F46[50];\n"
                     "extern _Thread_local int8_t fd_50F6_0FC6[50];\n"
                     "extern _Thread_local int8_t fd_50F6_0F84[50];\n"
                     "extern _Thread_local int8_t fd_50F6_1008[50];\n"
                     "extern _Thread_local int16_t fd_50F6_103C;\n"
                     "extern _Thread_local int16_t fd_50F6_1048;\n"
                     "extern _Thread_local uint8_t fd_3D57_087A[72];\n",
                     "TLS declarations")
    # One authoritative TLS/state backing; insert corresponding copies at the existing sorted-copy anchors.
    exp = """    memcpy(&state->fd_50F6_0F46, &fd_50F6_0F46, 50);
    memcpy(&state->fd_50F6_0FC6, &fd_50F6_0FC6, 50);
    memcpy(&state->fd_50F6_0F84, &fd_50F6_0F84, 50);
    memcpy(&state->fd_50F6_1008, &fd_50F6_1008, 50);
    memcpy(&state->fd_50F6_103C, &fd_50F6_103C, 2);
    memcpy(&state->fd_50F6_1048, &fd_50F6_1048, 2);
    memcpy(&state->fd_3D57_087A, &fd_3D57_087A, 72);
"""
    c = replace_once(c, "    memcpy(&state->EatCnt, &EatCnt, sizeof(state->EatCnt));\n",
                     "    memcpy(&state->EatCnt, &EatCnt, sizeof(state->EatCnt));\n" + exp,
                     "export copies")
    imp = exp.replace("state->", "state->").replace("memcpy(&state->", "memcpy(&")
    # Same widths/destinations reversed: generated state is copied into source TLS.
    imp = """    memcpy(&fd_50F6_0F46, &state->fd_50F6_0F46, 50);
    memcpy(&fd_50F6_0FC6, &state->fd_50F6_0FC6, 50);
    memcpy(&fd_50F6_0F84, &state->fd_50F6_0F84, 50);
    memcpy(&fd_50F6_1008, &state->fd_50F6_1008, 50);
    memcpy(&fd_50F6_103C, &state->fd_50F6_103C, 2);
    memcpy(&fd_50F6_1048, &state->fd_50F6_1048, 2);
    memcpy(&fd_3D57_087A, &state->fd_3D57_087A, 72);
"""
    c = replace_once(c, "    memcpy(&EatCnt, &state->EatCnt, sizeof(EatCnt));\n",
                     "    memcpy(&EatCnt, &state->EatCnt, sizeof(EatCnt));\n" + imp,
                     "import copies")
    init_match = re.search(r"unsigned char far fd_3D57_087A\[72\]\s*=\s*\{(.*?)\};", DATA.read_text(encoding="latin1"), re.S)
    if not init_match:
        raise RuntimeError("source initializer not found")
    init_bytes = [int(v, 16) for v in re.findall(r"0x([0-9a-fA-F]+)", init_match.group(1))]
    if len(init_bytes) != 72:
        raise RuntimeError("source initializer extent changed")
    init_literal = ", ".join(f"0x{x:02X}" for x in init_bytes)
    init_decl = f"static const uint8_t recovered_init_fd_3D57_087A[72] = {{ {init_literal} }};\n"
    c = replace_once(c, "void recovered_state_init(RecoveredState *state)\n", init_decl +
                     "\nvoid recovered_state_init(RecoveredState *state)\n", "state initializer declaration")
    init_copy = "    memcpy(&state->fd_3D57_087A, recovered_init_fd_3D57_087A, 72);\n"
    c = replace_once(c, "    memset(state, 0, sizeof(*state));\n",
                     "    memset(state, 0, sizeof(*state));\n" + init_copy,
                     "state initializer copy")
    parent_h = (n8dir / "recovered_state.h").read_text(encoding="utf-8")
    parent_c = (n8dir / "recovered_state.c").read_text(encoding="utf-8")
    old_tls_decl = ("extern _Thread_local int8_t fd_50F6_0F46[50];\n"
                    "extern _Thread_local int8_t fd_50F6_0FC6[50];\n"
                    "extern _Thread_local int8_t fd_50F6_0F84[50];\n"
                    "extern _Thread_local int8_t fd_50F6_1008[50];\n"
                    "extern _Thread_local int16_t fd_50F6_103C;\n"
                    "extern _Thread_local int16_t fd_50F6_1048;\n"
                    "extern _Thread_local uint8_t fd_3D57_087A[72];\n")
    if h.replace(members, "").replace(old_tls_decl, "") != parent_h:
        raise RuntimeError("Next9 changed or reordered inherited state fields/declarations")
    parent_projection = c.replace(globals_text, "").replace(exp, "").replace(imp, "")
    parent_projection = parent_projection.replace(init_decl + "\n", "").replace(init_copy, "")
    if parent_projection != parent_c:
        raise RuntimeError("Next9 changed inherited TLS bind/export/import/initializer behavior")
    header_path.write_text(h, encoding="utf-8", newline="")
    source_path.write_text(c, encoding="utf-8", newline="")

    # Preserve the transformed generated sources in provenance and rebuild all inherited TUs against the new header.
    state_o = out / "recovered_state.o"
    cc = provenance["compiler"]["command"]
    cmd = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-c", str(source_path), "-o", str(state_o)]
    built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise RuntimeError("Next9 state failed strict compile:\n" + built.stdout + built.stderr)
    for row in provenance["modules"]:
        old = row["compile"]["command"]
        # Compile commands use repository-relative generated paths.
        command = [str(x).replace("build/workers/recovered_source_next8/generated",
                                  str(out.relative_to(ROOT)).replace("\\", "/")) for x in old]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(f"Next9 inherited TU {row['name']} failed strict compile:\n" + built.stdout + built.stderr)
        row["compile"]["next9_recompiled"] = True
        row["compile"]["next9_command"] = command
        row["compile"]["next9_object_sha256"] = sha(Path(command[-1]).read_bytes())
    provenance["versioned_profile_extension_next9"] = {
        "schema": "simant-recovered-source-profile-extension-v1",
        "id": "legacy-save-state-bindings-next9-v1",
        "status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "parent_profile": "Next8",
        "parent_wrapper_sha256": NEXT8_SHA,
        "parent_provenance_sha256": NEXT8_PROVENANCE_SHA,
        "parent_state_sha256": {"recovered_state.h": NEXT8_HEADER_SHA, "recovered_state.c": NEXT8_SOURCE_SHA},
        "producer_path": str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"),
        "producer_sha256": sha(Path(__file__).read_bytes()),
        "added_members": [{"name": n, "source_owner": "src/S13/m384C.c:DrawSwarm" if n != "fd_3D57_087A" else "src/data/d3D57.c"} for n in SOURCE_NAMES],
        "state_header_sha256": sha(h.encode()), "state_source_sha256": sha(c.encode()),
        "source_initializer_sha256": sha(DATA.read_bytes()),
        "inherited_module_generated_hashes": module_hashes,
        "all_inherited_tus_recompiled": True,
        "inherited_state_projection_byte_identical": True,
        "limits": ["Diagnostic profile only; do not select in production.",
                   "Next9 adds persistent state backing only; it does not claim SaveGame DOS behavioral equivalence."]}
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    rows = inventory["table"]["records"]
    if len(rows) != 307:
        raise RuntimeError("legacy SaveRec inventory must contain 307 rows")
    emitted = []
    for idx, row in enumerate(rows):
        expr = row["pointer_expression"].strip()
        if expr.startswith("&"):
            ptr = expr
        elif expr == "(fd_3D57_087A + 20)":
            ptr = expr
        else:
            raise RuntimeError(f"unsupported SaveRec address expression at row {idx}: {expr}")
        order = ("PORTABLE_LEGACY_SAVE_RAW_BYTES" if idx == 99 or row["element_size"] == 1 else
                 "PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_16" if row["element_size"] == 2 else
                 "PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_32" if row["element_size"] == 4 else None)
        if order is None:
            raise RuntimeError(f"unsupported element width at row {idx}")
        emitted.extend([
            f"    bindings[{idx}].bytes = (uint8_t *)(void *)({ptr});",
            f"    bindings[{idx}].extent = (size_t)specs[{idx}].element_size * specs[{idx}].element_count;",
            f"    bindings[{idx}].storage_order = {order};",
        ])
    ROWS_OUT.write_text("\n".join(emitted) + "\n", encoding="utf-8", newline="")
    # Keep the top-level profile summary truthful as well as the additive extension.
    provenance["recovered_state"].update({
        "path": str(header_path.relative_to(ROOT)).replace("\\", "/"),
        "header_sha256": sha(header_path.read_bytes()),
        "source_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": sha(source_path.read_bytes()),
        "symbol_count": int(provenance["recovered_state"].get("symbol_count", 0)) + len(SOURCE_NAMES),
        "next9_added_members": [{"name": n, "type": t} for n, t in zip(SOURCE_NAMES,
            ["int8_t[50]", "int8_t[50]", "int8_t[50]", "int8_t[50]", "int16_t", "int16_t", "uint8_t[72]"])],
        "next9_initializer_checked": True,
    })
    provenance["versioned_profile_extension_next9"].update({
        "binding_schema": {"path": str(ROWS_OUT.relative_to(ROOT)).replace("\\", "/"),
                            "sha256": sha(ROWS_OUT.read_bytes()), "row_count": len(rows),
                            "inventory_path": str(INVENTORY.relative_to(ROOT)).replace("\\", "/"),
                            "inventory_sha256": sha(INVENTORY.read_bytes()),
                            "payload_bytes": sum(row["serialized_bytes"] for row in rows),
                            "storage_exceptions": [
                                {"row":29,"policy":"NATIVE_NUMERIC_16","reason":"Next9 portable backing is int16_t[16][12], used by S08/S01 as native numeric cells; codec converts host numeric representation to DOS little endian"},
                                {"row":99,"policy":"RAW_BYTES","reason":"interior [20,40) slice of unsigned char fd_3D57_087A[72] despite 16-bit SaveRec width"}]},
        "state_object_sha256": sha(state_o.read_bytes()),
        "source_initializer_check": {"source_path": "src/data/d3D57.c",
                                     "source_sha256": sha(DATA.read_bytes()),
                                     "member": "fd_3D57_087A", "byte_count": 72,
                                     "initialized_slice_hex": bytes(init_bytes[20:40]).hex()},
    })
    prov_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status":"DIAGNOSTIC_ONLY_NOT_PRODUCTION", "out":str(out),
                      "members_added":len(SOURCE_NAMES), "state_header_sha256":sha(h.encode()),
                      "state_source_sha256":sha(c.encode()), "inherited_TUs_recompiled":len(provenance["modules"]),
                      "interior_init_hex":bytes(init_bytes[20:40]).hex(),
                      "binding_row_source_sha256":sha(ROWS_OUT.read_bytes()), "binding_rows":len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
