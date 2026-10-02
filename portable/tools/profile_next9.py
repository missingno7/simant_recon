"""Admission checks for the reviewed, explicitly selected Next9 profile.

This admits source-state backing and its codec, not a SaveGame lifecycle claim.
Changes to this exact extension require a new reviewed profile generation.
"""
from __future__ import annotations

PRODUCER_SHA = "c9429350a6c8bc9453e0a34c5e0f13f5c5d10d34ac643e8271e7db00c4beb3ae"
STATE_SHA = {
    "recovered_state.h": "7e01016c0c3a2326176f0a5ce487cc3f47e6d808518687edf95f6e70a9dcc835",
    "recovered_state.c": "7d514c15c50d89798c1b7f809904ab65d5e0e446b0731ea0e71afd45234cafca",
}
MEMBERS = ["fd_50F6_0F46", "fd_50F6_0FC6", "fd_50F6_0F84",
           "fd_50F6_1008", "fd_50F6_103C", "fd_50F6_1048", "fd_3D57_087A"]
TYPES = ["int8_t[50]"] * 4 + ["int16_t"] * 2 + ["uint8_t[72]"]


def validate_next9(provenance: dict) -> tuple[dict[str, str], dict[str, str]]:
    """Return additional file pins and the inherited state identity.

    Raises SystemExit before compilation on an unreviewed extension. The caller
    must check every returned file pin, as it does the other profile inputs.
    """
    ext = provenance.get("versioned_profile_extension_next9", {})
    parent = provenance.get("versioned_profile_extension_next8", {})
    state = provenance.get("recovered_state", {})
    old_state = parent.get("parent_profile", {}).get("state_hashes", {})
    if (ext.get("schema") != "simant-recovered-source-profile-extension-v1" or
            ext.get("id") != "legacy-save-state-bindings-next9-v1" or
            ext.get("status") != "DIAGNOSTIC_ONLY_NOT_PRODUCTION" or
            ext.get("parent_profile") != "Next8" or not parent or
            ext.get("parent_wrapper_sha256") != parent.get("wrapper_sha256") or
            ext.get("producer_path") != "portable/tools/recover_source_next9.py" or
            ext.get("producer_sha256") != PRODUCER_SHA or
            ext.get("parent_state_sha256") != old_state or
            ext.get("all_inherited_tus_recompiled") is not True or
            ext.get("inherited_state_projection_byte_identical") is not True):
        raise SystemExit("Unreviewed Next9 save-state ancestry")
    owners = [{"name": name, "source_owner":
               "src/data/d3D57.c" if name == "fd_3D57_087A" else
               "src/S13/m384C.c:DrawSwarm"} for name in MEMBERS]
    added = [{"name": name, "type": kind} for name, kind in zip(MEMBERS, TYPES)]
    if (ext.get("added_members") != owners or
            state.get("next9_added_members") != added or
            state.get("next9_initializer_checked") is not True or
            state.get("header_sha256") != STATE_SHA["recovered_state.h"] or
            ext.get("state_header_sha256") != STATE_SHA["recovered_state.h"] or
            state.get("source_sha256") != STATE_SHA["recovered_state.c"] or
            ext.get("state_source_sha256") != STATE_SHA["recovered_state.c"]):
        raise SystemExit("Unreviewed Next9 source-state layout")
    modules = provenance.get("modules", [])
    inherited = ext.get("inherited_module_generated_hashes", {})
    if (len(modules) != 25 or len(inherited) != 25 or
            {row["name"]: row["generated_sha256"] for row in modules} != inherited or
            not all(row.get("compile", {}).get("next9_recompiled") is True
                    for row in modules)):
        raise SystemExit("Next9 changed inherited simulation modules")
    binding = ext.get("binding_schema", {})
    exceptions = binding.get("storage_exceptions", [])
    initializer = ext.get("source_initializer_check", {})
    if (binding.get("path") != "portable/game/save/next9_bindings_rows.inc" or
            binding.get("sha256") != "7d7ca24e7aa164bafbda4d3901763d03fe813dc94f87076f3cd56ed2298ac8bc" or
            binding.get("row_count") != 307 or binding.get("payload_bytes") != 48386 or
            binding.get("inventory_path") != "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json" or
            binding.get("inventory_sha256") != "a48c4d650ee7a0a2d37e115d61bce36c442d83586183d7f3997e416573ac85e1" or
            [(row.get("row"), row.get("policy")) for row in exceptions] !=
                [(29, "NATIVE_NUMERIC_16"), (99, "RAW_BYTES")] or
            initializer.get("source_path") != "src/data/d3D57.c" or
            initializer.get("source_sha256") != ext.get("source_initializer_sha256") or
            initializer.get("source_sha256") != "983251ad55176050efcdea33c62f0a34a93686474b0de4b2bdde6c6c808716f5" or
            initializer.get("member") != "fd_3D57_087A" or
            initializer.get("byte_count") != 72 or
            initializer.get("initialized_slice_hex") != "0100000000000000000001000000000000000000"):
        raise SystemExit("Unreviewed Next9 save binding or initializer")
    return {ext["producer_path"]: ext["producer_sha256"],
            binding["path"]: binding["sha256"],
            binding["inventory_path"]: binding["inventory_sha256"],
            initializer["source_path"]: initializer["source_sha256"]}, old_state
