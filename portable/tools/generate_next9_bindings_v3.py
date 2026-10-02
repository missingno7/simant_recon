"""Generate typed Next9 SaveRec rows and an independent address-sentinel map."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "build/workers/recovered_source_next9/generated"
EXPECTED_PROFILE = "e3547a24caab7a9037f4b1aa6727078a8f8759a6feba65bcca7dbbcd6ff10156"
INVENTORY = ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"
SYMBOLS = ROOT / "layout/symbols.json"
SAVE_DIR = ROOT / "portable/game/save"
TEST_DIR = ROOT / "portable/tests/save/support"
EVIDENCE = ROOT / "portable/tests/save/evidence/legacy-save-codec-v3"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    profile_path = PROFILE / "provenance.json"
    if sha(profile_path) != EXPECTED_PROFILE:
        raise RuntimeError("pinned Next9 state profile changed")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    header = (PROFILE / "recovered_state.h").read_text(encoding="utf-8")
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))["table"]["records"]
    symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))["data"]
    field_rows = {f["name"]: f for f in profile["recovered_state"]["fields"]}
    added = profile["recovered_state"].get("next9_added_members", [])
    for row in added:
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?", row["type"])
        if not match: raise RuntimeError(f"unsupported Next9 added type: {row['type']}")
        field_rows[row["name"]] = {"name":row["name"],"type":match.group(1),
                                    "dims":[match.group(2)] if match.group(2) else []}
    macros = dict(re.findall(r"(?m)^#define\s+([A-Za-z_]\w*)\s+([^\r\n]+)$", header))

    def type_width(field: dict) -> int:
        typ = field["type"].strip()
        widths = {"int8_t":1,"uint8_t":1,"char":1,"signed char":1,"unsigned char":1,
                  "int16_t":2,"uint16_t":2,"int32_t":4,"uint32_t":4,"int":2,"unsigned":2}
        if typ in widths: return widths[typ]
        struct_widths = {"struct Pt":4,"RecoveredPoint":4,"RecoveredXY":4,"struct Rect":8,
                         "struct TriPoints":12,"RecoveredPointBytes18":18}
        if typ in struct_widths: return struct_widths[typ]
        raise RuntimeError(f"unsupported portable backing type {typ} for {field['name']}")

    def policy_for(field: dict) -> tuple[str,int]:
        struct_type = field["type"].strip()
        if struct_type in ("RecoveredPoint","RecoveredXY","struct Pt","struct Rect","struct TriPoints"):
            return "PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_16",2
        if struct_type == "RecoveredPointBytes18":
            return "PORTABLE_LEGACY_SAVE_RAW_BYTES",1
        width = type_width(field)
        if width == 1: return "PORTABLE_LEGACY_SAVE_RAW_BYTES",1
        if width == 2: return "PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_16",2
        if width == 4: return "PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_32",4
        raise RuntimeError(f"no storage-order policy for {field['name']}")

    bindings, map_rows, canonical_bases = [], [], {}
    for idx, row in enumerate(inventory):
        expr = row["pointer_expression"].strip()
        interior = 0
        if expr.startswith("&"):
            source_name = expr[1:]
        elif expr == "(fd_3D57_087A + 20)":
            source_name, interior = "fd_3D57_087A",20
        else:
            raise RuntimeError(f"unsupported pointer expression row {idx}: {expr}")
        macro = macros.get(source_name, source_name).strip()
        if not re.fullmatch(r"[A-Za-z_]\w*", macro):
            raise RuntimeError(f"non-object member alias in SaveRec row {idx}: {source_name} -> {macro}")
        member = macro
        field = field_rows.get(member)
        if field is None:
            raise RuntimeError(f"no Next9 backing member for SaveRec row {idx}: {source_name} -> {member}")
        src_symbol = symbols.get(source_name)
        member_symbol = symbols.get(member)
        if src_symbol is None or member_symbol is None:
            raise RuntimeError(f"missing layout symbol address for row {idx}: {source_name}/{member}")
        src_linear = src_symbol["seg"]*16 + src_symbol["off"] + interior
        base_linear = member_symbol["seg"]*16 + member_symbol["off"]
        delta = src_linear - base_linear
        if delta < 0:
            raise RuntimeError(f"alias precedes canonical backing in row {idx}: {source_name} -> {member}")
        storage, component = policy_for(field)
        total = row["serialized_bytes"]
        if total % component:
            raise RuntimeError(f"row {idx} extent {total} not divisible by backing element width {component}")
        if idx == 99 and (member != "fd_3D57_087A" or delta != 20 or storage != "PORTABLE_LEGACY_SAVE_RAW_BYTES"):
            raise RuntimeError("row99 must stay the raw source byte-table interior")
        declared = type_width(field)
        for dim in field.get("dims",[]): declared *= int(dim)
        if delta + total > declared:
            raise RuntimeError(f"row {idx} exceeds Next9 backing extent for {member}")
        expr_c = f"(&{source_name})" if interior == 0 else "(fd_3D57_087A + 20)"
        bindings.extend([
            f"    /* row {idx}: {expr} -> state.{member}+{delta}; {field['type']} / {storage} */",
            f"    bindings[{idx}].bytes = (uint8_t *)(void *)({expr_c});",
            f"    bindings[{idx}].extent = (size_t)specs[{idx}].element_size * specs[{idx}].element_count;",
            f"    bindings[{idx}].storage_order = {storage};",
        ])
        map_rows.append({"index":idx,"source_expression":expr,"source_symbol":source_name,
                         "source_linear_address":src_linear,"source_segment":src_symbol["seg"],"source_offset":src_symbol["off"]+interior,
                         "portable_member":member,"portable_type":field["type"],"member_extent_bytes":declared,
                         "member_source_linear_address":base_linear,"member_byte_offset":delta,
                         "element_size":row["element_size"],"element_count":row["element_count"],
                         "serialized_bytes":total,"storage_order":storage,"component_width":component})
        canonical_bases[member] = (base_linear, field, component)
    rows_path = SAVE_DIR / "next9_bindings_v3_rows.inc"
    rows_path.write_text("\n".join(bindings)+"\n", encoding="utf-8", newline="")

    TEST_DIR.mkdir(parents=True, exist_ok=True)
    sentinels = ["#include \"next9_source_sentinels_v3.h\"", "#include <stdint.h>", "#include <stddef.h>",
                 "static uint8_t source_sentinel_byte(uint32_t address)", "{",
                 "    uint32_t x = address;", "    x ^= x >> 11;", "    x *= 0x45D9F3Bu;", "    x ^= x >> 16;", "    return (uint8_t)(x ^ (x >> 8) ^ (x >> 24));", "}",
                 "void portable_next9_fill_source_address_sentinels(RecoveredState *state)", "{",
                 "    if (state == NULL) return;"]
    # Build the sentinel catalog from the complete Next9 state-field inventory and
    # layout symbol map, independently of SaveRec rows/canonical_bases. The DOS
    # writer is the separate authority for which fields and offsets are serialized.
    sentinel_fields = dict(field_rows)
    sentinel_catalog = {}
    for member, field in sentinel_fields.items():
        if member not in symbols:
            continue
        typ = field["type"].strip()
        if "*" in typ:
            continue
        try:
            component = policy_for(field)[1]
            extent = type_width(field)
        except RuntimeError:
            continue
        for dim in field.get("dims", []):
            extent *= int(dim)
        sym = symbols[member]
        base = sym["seg"] * 16 + sym["off"]
        sentinel_catalog[member] = (base, field, component, extent)
    missing_sentinels = sorted(set(canonical_bases) - set(sentinel_catalog))
    if missing_sentinels:
        raise RuntimeError(f"SaveRec bindings lack independent state sentinels: {missing_sentinels}")

    sentinel_map = []
    for member,(base,field,component,declared) in sorted(sentinel_catalog.items()):
        # Portable struct arrays have a compile-time extent; fill each whole
        # source-backed state object independently of the SaveRec row list.
        sentinels.extend([f"    {{ uint8_t *p = (uint8_t *)(void *)&state->{member};",
                          f"      size_t n = sizeof(state->{member}); size_t i;",
                          f"      for (i = 0; i < n; ++i) {{ uint32_t a = UINT32_C({base}) + (uint32_t)i; (void)a;"])
        if component == 1:
            sentinels.append("        p[i] = source_sentinel_byte(a);")
        else:
            sentinels.extend(["#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN",
                              f"        p[i] = source_sentinel_byte(UINT32_C({base}) + (uint32_t)((i / {component}u) * {component}u + ({component-1}u - (i % {component}u))));",
                              "#else", "        p[i] = source_sentinel_byte(a);", "#endif"])
        sentinels.extend(["      } };"])
        sentinel_map.append({"member":member,"type":field["type"],"source_linear_address":base,
                             "extent_bytes":declared,"component_width":component,
                             "catalog_source":"Next9 recovered_state.fields + layout/symbols.json; independent of SaveRec inventory"})
    sentinels.extend(["}"])
    (TEST_DIR / "next9_source_sentinels_v3.c").write_text("\n".join(sentinels)+"\n",encoding="utf-8",newline="")
    (TEST_DIR / "next9_source_sentinels_v3.h").write_text(
        "#ifndef SIMANT_NEXT9_SOURCE_SENTINELS_V3_H\n#define SIMANT_NEXT9_SOURCE_SENTINELS_V3_H\n"
        "#include <stdint.h>\n#include \"recovered_state.h\"\n"
        "void portable_next9_fill_source_address_sentinels(RecoveredState *state);\n#endif\n",
        encoding="utf-8",newline="")
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE / "binding-map.json").write_text(json.dumps({
        "schema":"simant-next9-save-row-type-map-v3","status":"GENERATED_SOURCE_MAP_NOT_ACCEPTANCE",
        "profile_provenance_sha256":EXPECTED_PROFILE,"inventory_sha256":sha(INVENTORY),
        "symbol_map_sha256":sha(SYMBOLS),"rows":map_rows,"sentinel_members":sentinel_map,
    },indent=2)+"\n",encoding="utf-8",newline="")
    print(f"next9_v3_rows={len(map_rows)} members={len(sentinel_map)} rows_sha256={sha(rows_path)}")

if __name__ == "__main__": main()
