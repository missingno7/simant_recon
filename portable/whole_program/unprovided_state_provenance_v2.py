#!/usr/bin/env python3
"""Reclassify whole-program state candidates using frozen storage provenance.

This is a diagnostic planner only. It consumes the previous primitive-view
inventory, the frozen manifest, and exact historical OMF PUBLIC records for
the reviewed owners needed by the regression cases. It never edits game
sources or selects production state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE_PLAN = ROOT / "portable/research/whole_program_unprovided_owners.json"
MIGRATION = ROOT / "build/workers/whole_program/generated/migration.json"
MANIFEST = ROOT / "layout/manifest.json"
SYMBOLS = ROOT / "layout/symbols.json"
OUT_JSON = ROOT / "portable/research/whole_program_unprovided_owners_v2.json"
OUT_MD = ROOT / "portable/research/whole_program_unprovided_owners_v2.md"
OUT_C = ROOT / "build/workers/whole_program/unprovided_state_provenance_v2.c"
FARBSS_SEG = 0x50F6
FARBSS_LAST = 0x4BCF


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    return json.loads(raw), sha(raw)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def address_key(seg: int, off: int) -> str:
    return f"{seg:04X}:{off:04X}"


def address_from_key(value: str) -> tuple[int, int]:
    a, b = value.split(":")
    return int(a, 16), int(b, 16)


def public_source_name(name: str) -> str:
    return name[1:] if name.startswith("_") else name


def exact_omf_publics(manifest: dict[str, Any], keys: list[str]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Compile accepted canonical sources and require the exact manifest object hash."""
    sys.path.insert(0, str(ROOT / "tools"))
    import compiler  # type: ignore
    from omf import OmfReader  # type: ignore

    by_address: dict[str, list[dict[str, Any]]] = {}
    pins = []
    for key in keys:
        module = manifest["modules"][key]
        src = ROOT / module["source"]
        source_bytes = src.read_bytes()
        if sha(source_bytes) != module["source_sha256"]:
            raise SystemExit(f"manifest source pin mismatch: {module['source']}")
        source = source_bytes.decode("latin1")
        if module["lang"] == "asm":
            result = compiler.assemble(source, module["profile"], module["flags"], basename="UNIT", keep=True)
        else:
            result = compiler.compile_c(source, module["profile"], module["flags"], basename="UNIT", keep=True)
        if not result.ok or result.obj is None:
            raise SystemExit(f"historical source compile failed for {key}: {result.log}")
        object_hash = sha(result.obj)
        if object_hash != module["object_sha256"]:
            raise SystemExit(f"historical object hash mismatch for {key}: {object_hash}")
        obj = OmfReader(communals=True).read(result.obj, label=key)
        placements = module.get("placements", {})
        for public in obj.publics:
            placement = placements.get(public["segment"])
            if not placement:
                continue
            if public["offset"] >= placement["size"]:
                raise SystemExit(f"PUBLIC outside manifest placement: {key}:{public}")
            seg, off = placement["seg"], placement["off"] + public["offset"]
            record = {
                "source_module": key,
                "source": module["source"],
                "source_sha256": module["source_sha256"],
                "object_sha256": object_hash,
                "public": public["name"],
                "source_name": public_source_name(public["name"]),
                "segment": public["segment"],
                "object_offset": public["offset"],
                "address": address_key(seg, off),
                "manifest_placement": placement,
            }
            by_address.setdefault(record["address"], []).append(record)
        pins.append({"module": key, "source": module["source"], "source_sha256": module["source_sha256"],
                     "manifest_object_sha256": module["object_sha256"], "recompiled_object_sha256": object_hash,
                     "public_count": len(obj.publics), "segment_lengths": obj.segment_lengths,
                     "data_pointer32_fixups": ([{"segment": f["segment"], "offset": f["offset"],
                                                   "width": f["width"], "loc": f["loc"]}
                                                  for f in obj.linker_fixups
                                                  if f["segment"] == "_DATA" and f.get("width") == 4 and
                                                  f.get("loc") == "pointer32"] if key == "root:15F8" else [])})
    return by_address, pins


def asm_initializer(source_path: str, source_name: str) -> dict[str, Any] | None:
    """Read a literal primitive initializer at the exact PUBLIC label."""
    text = (ROOT / source_path).read_text(encoding="latin1")
    pat = re.compile(r"^\s*" + re.escape("_" + source_name) +
                     r"\s+(db|dw|dd)\s+([^;\r\n]+)", re.I | re.M)
    match = pat.search(text)
    if not match:
        return None
    directive, expr = match.group(1).lower(), match.group(2).strip()
    width = {"db": 1, "dw": 2, "dd": 4}[directive]
    literal = re.match(r"(?:0[xX])?([0-9A-Fa-f]+)(?:[hH])?(?:\s*,|$)", expr)
    if literal:
        token = literal.group(0).split(",", 1)[0].strip()
        if token.lower().endswith("h"):
            value = int(token[:-1], 16)
        elif token.lower().startswith("0x"):
            value = int(token, 16)
        else:
            value = int(token, 10)
        return {"source": source_path, "line": text.count("\n", 0, match.start()) + 1,
                "directive": directive, "storage_width_bytes": width,
                "initializer_expression": expr, "initializer_value": value,
                "storage_type": {1: "uint8_t", 2: "uint16_t", 4: "uint32_t"}[width]}
    return {"source": source_path, "line": text.count("\n", 0, match.start()) + 1,
            "directive": directive, "storage_width_bytes": width,
            "initializer_expression": expr, "initializer_value": None,
            "storage_type": {1: "uint8_t", 2: "uint16_t", 4: "uint32_t"}[width]}


def placement_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, module in manifest["modules"].items():
        for segname, p in module.get("placements", {}).items():
            rows.append({"module": key, "source": module["source"], "segment_name": segname,
                         "seg": p["seg"], "start": p["off"], "end": p["off"] + p["size"],
                         "size": p["size"], "kind": "BSS" if segname.upper() == "_BSS" else "initialized-data",
                         "object_sha256": module.get("object_sha256")})
        extent = module.get("extent")
        if extent:
            seg = module["seg"]
            rows.append({"module": key, "source": module["source"], "segment_name": "CODE",
                         "seg": seg, "start_linear": extent["start"], "end_linear": extent["end"],
                         "size": extent["end"] - extent["start"], "kind": "CODE",
                         "object_sha256": module.get("object_sha256")})
    for module in manifest.get("runtime", {}).get("members", []):
        for p in module.get("data_segments", []):
            linear = p.get("linear")
            if isinstance(linear, int):
                rows.append({"module": "runtime:" + module.get("member", ""), "source": None,
                             "segment_name": p.get("segment"), "start_linear": linear,
                             "end_linear": linear + p.get("size", 0), "size": p.get("size", 0),
                             "kind": "initialized-data", "object_sha256": module.get("member_sha256")})
    return rows


def point_provenance(addr: str, placements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seg, off = address_from_key(addr)
    linear = seg * 16 + off
    found = []
    for p in placements:
        if "start_linear" in p:
            if p["start_linear"] <= linear < p["end_linear"]:
                found.append(p)
        elif p["seg"] == seg and p["start"] <= off < p["end"]:
            found.append(p)
    return found


def controls() -> dict[str, Any]:
    # The controls exercise the classification rules themselves, with synthetic
    # ranges so a future refactor cannot fall back to name-only BSS guesses.
    def classify(rows: list[dict[str, Any]], addr: str) -> set[str]:
        return {x["kind"] for x in point_provenance(addr, rows)}

    def exact_public_alias(candidate_addr: str, provider_addr: str, object_hash_match: bool,
                           placement_contains_public: bool) -> bool:
        return candidate_addr == provider_addr and object_hash_match and placement_contains_public

    def table_element(base: int, element_width: int, count: int, address: int) -> int | None:
        delta = address - base
        if delta < 0 or delta % element_width or delta // element_width >= count:
            return None
        return delta // element_width

    synthetic = [
        {"kind": "initialized-data", "seg": 0x55B3, "start": 0x3D20, "end": 0x4329},
        {"kind": "BSS", "seg": 0x55B3, "start": 0x8BAE, "end": 0x8BCC},
        {"kind": "CODE", "seg": 0x1B73, "start_linear": 0x1B736, "end_linear": 0x1C626},
    ]
    positive = {
        "verified_bss_range_is_distinct_from_data": classify(synthetic, "55B3:8BAE") == {"BSS"},
        "literal_asm_data_is_data_not_bss": classify(synthetic, "55B3:3DB2") == {"initialized-data"},
        "code_extent_is_not_storage": classify(synthetic, "1B73:0006") == {"CODE"},
        "exact_public_and_placement_alias_accepted": exact_public_alias("55B3:19BE", "55B3:19BE", True, True),
        "table_interior_maps_to_index_one": table_element(0x1CD4, 4, 5, 0x1CD8) == 1,
    }
    negative = {
        "initialized_data_never_qualifies_as_bss": "BSS" not in classify(synthetic, "55B3:3DB2"),
        "code_never_qualifies_as_bss": "BSS" not in classify(synthetic, "1B73:0006"),
        "outside_storage_is_unresolved": not classify(synthetic, "1234:5678"),
        "overlapping_storage_classes_rejected": len(classify(synthetic + [
            {"kind": "BSS", "seg": 0x55B3, "start": 0x3DB0, "end": 0x3DC0}], "55B3:3DB2")) > 1,
        "different_public_address_rejected": not exact_public_alias("55B3:19BE", "55B3:19C0", True, True),
        "matching_name_without_object_placement_rejected": not exact_public_alias("55B3:19BE", "55B3:19BE", False, False),
        "table_misaligned_offset_rejected": table_element(0x1CD4, 4, 5, 0x1CD9) is None,
        "table_outside_count_rejected": table_element(0x1CD4, 4, 5, 0x1CE8) is None,
    }
    return {"positive": positive, "negative": negative,
            "passed": all(positive.values()) and all(negative.values()),
            "purpose": "Storage-provenance classifier controls, not behavioral or production acceptance."}


def nm_names(nm_path: Path, obj_path: Path, undefined: bool) -> set[str]:
    flag = "-u" if undefined else "-g --defined-only"
    args = [str(nm_path), *flag.split(), str(obj_path)]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode:
        raise SystemExit(f"nm failed for {obj_path}: {result.stderr}")
    names = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if fields:
            names.add(fields[-1])
    return names


def compile_and_link_owner(owner_c: Path, migration: dict[str, Any]) -> dict[str, Any]:
    """Compile the scratch owners and repeat the pinned partial native link."""
    base_link = migration.get("partial_core_link", {})
    base_command = base_link.get("command", [])
    if not base_link.get("passed") or "-o" not in base_command:
        raise SystemExit("migration does not carry a successful baseline partial link")
    compiler_path = Path(base_command[0])
    nm_path = compiler_path.with_name("nm.exe")
    baseline_object = Path(base_command[-1])
    if not baseline_object.is_file():
        raise SystemExit(f"baseline partial link output is missing: {baseline_object}")
    # Verify every object used by the admitted migration before reusing the
    # link vector. The source/object list is the immutable migration snapshot.
    object_rows = list(migration.get("modules", [])) + list(migration.get("native_support", []))
    for row in object_rows:
        compile_row = row.get("compile", {})
        object_rel = compile_row.get("object")
        if not object_rel:
            continue
        object_path = ROOT / object_rel
        if not object_path.is_file() or sha(object_path.read_bytes()) != compile_row.get("object_sha256"):
            raise SystemExit(f"migration object changed before owner link: {object_rel}")
    owner_obj = ROOT / "build/workers/whole_program/unprovided_state_provenance_v2.o"
    compile_cmd = [str(compiler_path), "-std=c11", "-fsigned-char", "-fno-builtin", "-fno-common",
                   "-Wall", "-Werror", "-c", str(owner_c), "-o", str(owner_obj)]
    compiled = subprocess.run(compile_cmd, capture_output=True, text=True, check=False)
    if compiled.returncode:
        raise SystemExit(f"scratch owner compile failed: {compiled.stderr}")
    owner_defined = nm_names(nm_path, owner_obj, undefined=False)
    before_undefined = nm_names(nm_path, baseline_object, undefined=True)
    linked_object = ROOT / "build/workers/whole_program/unprovided_state_provenance_v2_link.o"
    output_flag = base_command.index("-o")
    link_command = base_command[:output_flag] + [str(owner_obj), "-o", str(linked_object)]
    linked = subprocess.run(link_command, capture_output=True, text=True, check=False)
    if linked.returncode:
        raise SystemExit(f"partial owner link failed: {linked.stderr}")
    after_undefined = nm_names(nm_path, linked_object, undefined=True)
    resolved = sorted((before_undefined - after_undefined) & owner_defined)
    return {"compiler": str(compiler_path), "nm": str(nm_path),
            "compile_command": compile_cmd, "owner_object": rel(owner_obj),
            "owner_object_sha256": sha(owner_obj.read_bytes()),
            "baseline_object": rel(baseline_object), "baseline_object_sha256": sha(baseline_object.read_bytes()),
            "link_command": link_command, "linked_object": rel(linked_object),
            "linked_object_sha256": sha(linked_object.read_bytes()),
            "baseline_undefined_symbol_count": len(before_undefined),
            "owner_defined_symbol_count": len(owner_defined),
            "remaining_undefined_symbol_count": len(after_undefined),
            "unresolved_symbols_removed": len(before_undefined - after_undefined),
            "owner_symbols_satisfying_previous_undefineds": resolved,
            "claim": "Scratch partial-link diagnostic only; no executable, behavior, or production integration claim."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-plan", type=Path, default=BASE_PLAN)
    ap.add_argument("--migration", type=Path, default=MIGRATION)
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--symbols", type=Path, default=SYMBOLS)
    ap.add_argument("--json", type=Path, default=OUT_JSON)
    ap.add_argument("--markdown", type=Path, default=OUT_MD)
    ap.add_argument("--emit", type=Path, default=OUT_C)
    args = ap.parse_args()
    base, base_hash = load(args.base_plan)
    migration, migration_hash = load(args.migration)
    manifest, manifest_hash = load(args.manifest)
    symbols, symbols_hash = load(args.symbols)
    if base.get("schema") != "simant-whole-program-unprovided-state-plan-v1":
        raise SystemExit("unexpected base plan")
    if base.get("inputs", {}).get("migration", {}).get("sha256") != migration_hash:
        raise SystemExit("base primitive plan was produced from a different migration inventory")
    if base.get("inputs", {}).get("frozen_symbols", {}).get("sha256") != symbols_hash:
        raise SystemExit("base primitive plan was produced from a different frozen symbol registry")
    public_index, exact_module_pins = exact_omf_publics(
        manifest, ["root:1B4E", "root:0250", "root:15F8", "data:3D57", "data:3E1D"])
    placements = placement_rows(manifest)
    source_text = {m["source"]: (ROOT / m["source"]).read_text(encoding="latin1")
                   for m in manifest["modules"].values()}

    # FAR_BSS is a real linker-common allocation region. Import the existing
    # accounting routine so candidate extents must agree with the registry's
    # next-address gap and with source/save-table size evidence.
    sys.path.insert(0, str(ROOT / "tools"))
    import farbss  # type: ignore
    import modules as modules_tool  # type: ignore
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from unprovided_state_plan import assess_views, canonical_alias  # type: ignore
    accepted_manifest = modules_tool.load_manifest()
    accepted_c_sources = {k: (ROOT / m["source"]).read_text(encoding="latin1")
                          for k, m in accepted_manifest["modules"].items() if m.get("lang", "c") == "c"}
    farbss_report = farbss.account(accepted_c_sources)
    if not farbss_report["accounted"]:
        raise SystemExit(f"FAR_BSS accounting failed: {farbss_report['failures']}")
    farbss_rows = {r["off"]: r for r in farbss_report["rows"]}

    groups = []
    decisions = Counter()
    alias_map: dict[str, str] = {}
    asm_initializers = []
    bss_candidates = []
    source_expression_aliases = []
    for old in base.get("groups", []):
        g = dict(old)
        addr = g["address"]
        hits = point_provenance(addr, placements)
        pubrows = public_index.get(addr, [])
        asm_rows = [p for p in pubrows if p["source_module"] == "root:1B4E" and p["segment"] == "_DATA"]
        c_rows = [p for p in pubrows if p["source_module"] == "root:0250" and p["segment"] == "_DATA"]
        g["historical_provenance"] = {"address": addr, "placement_matches": hits,
                                      "exact_accepted_omf_publics": pubrows}

        if any(p["kind"] == "CODE" for p in hits):
            g["decision"] = "excluded-code-address"
            g["reason"] = "candidate address lies inside an accepted code extent; no state storage may be emitted"
            g["historical_provenance"]["storage_class"] = "CODE"
        elif asm_rows:
            # Keep only a same-name PUBLIC as a storage definition; an arbitrary
            # same-address public still requires independent alias review.
            by_member = [p for p in asm_rows if p["source_name"] in g.get("unprovided_members", [])]
            if by_member:
                public = by_member[0]
                init = asm_initializer(public["source"], public["source_name"])
                g["decision"] = "initialized-asm-data-candidate"
                g["reason"] = "exact accepted MASM OMF PUBLIC and manifest _DATA placement; source directive supplies a literal initializer"
                g["historical_provenance"].update({"storage_class": "initialized-ASM-DATA",
                                                  "initializer": init})
                if init:
                    asm_initializers.append({"address": addr, "name": public["source_name"],
                                             "public": public, **init})
            else:
                g["decision"] = "initialized-data-address-needs-symbol-review"
                g["reason"] = "exact accepted ASM DATA placement/public exists at address, but candidate name is not that PUBLIC"
                g["historical_provenance"]["storage_class"] = "initialized-ASM-DATA"
        elif c_rows:
            target = next((p for p in c_rows if p["source_name"] == "g_19BE"), None)
            members = g.get("unprovided_members", [])
            if target and "fd_55B3_19BE" in members and target["address"] == addr:
                # The exact accepted OMF proves this PUBLIC is the first byte in
                # the placed _DATA contribution; source declaration is int.
                source = source_text[target["source"]]
                declaration = re.search(r"^\s*int\s+g_19BE\s*=\s*16\s*;", source, re.M)
                if declaration and target["object_offset"] == 0:
                    g["decision"] = "exact-omf-public-alias-rename-candidate"
                    g["reason"] = "far registered view and near C PUBLIC resolve to the same placed address; exact OMF object hash and PUBLIC offset prove one initialized owner"
                    g["owner"] = "g_19BE"
                    g["owner_storage_class"] = "initialized-C-DATA"
                    g["historical_provenance"].update({"storage_class": "initialized-C-DATA",
                                                      "provider_public": target,
                                                      "provider_declaration": "int g_19BE = 16;",
                                                      "provider_initializer": 16,
                                                      "no_duplicate_owner": True})
                    alias_map["fd_55B3_19BE"] = "g_19BE"
                else:
                    g["decision"] = "initialized-data-address-needs-symbol-review"
                    g["reason"] = "near candidate PUBLIC or initialized declaration failed the exact alias criteria"
                    g["historical_provenance"]["storage_class"] = "initialized-C-DATA"
            else:
                g["decision"] = "initialized-data-address-needs-symbol-review"
                g["reason"] = "exact accepted C DATA PUBLIC is present, but no reviewed alias relation is established"
                g["historical_provenance"]["storage_class"] = "initialized-C-DATA"
        elif g.get("decision") == "registered-alias-rename-candidate":
            target = g.get("owner")
            target_public = next((p for p in pubrows if p["source_name"] == target), None)
            if target_public and target_public["address"] == addr:
                for alias_name in g.get("unprovided_members", []):
                    alias_map[alias_name] = target
                g["decision"] = "exact-omf-public-alias-rename-candidate"
                g["reason"] = "registered alias and provider PUBLIC resolve to one address in an exact accepted OMF object whose DATA placement is manifest-pinned"
                g["owner_storage_class"] = "initialized-data"
                g["historical_provenance"].update({"storage_class": "initialized-data-alias",
                                                  "provider_public": target_public,
                                                  "alias_compatibility": g.get("alias_compatibility")})
            else:
                g["decision"] = "initialized-data-address-needs-symbol-review"
                g["reason"] = "legacy alias proposal lacks an exact accepted OMF provider PUBLIC at this placed address"
                g["historical_provenance"]["storage_class"] = "unresolved-alias"
        elif hits:
            classes = sorted({p["kind"] for p in hits})
            g["historical_provenance"]["storage_class"] = classes[0] if len(classes) == 1 else "overlapping-placement-classes"
            if "BSS" in classes and len(classes) == 1:
                g["decision"] = "validated-bss-range-existing-placement"
                g["reason"] = "address lies in a manifest-placed near BSS range; exact existing owner/alias is still required, so do not allocate a second object"
            else:
                g["decision"] = "initialized-data-address"
                g["reason"] = "candidate lies within a manifest-placed DATA/CONST contribution; do not emit zero-initialized storage"
        else:
            seg, off = address_from_key(addr)
            if seg == FARBSS_SEG and 0 <= off <= FARBSS_LAST:
                g["decision"] = "validated-farbss-range-owner-unresolved"
                g["reason"] = "address is inside the all-zero FAR_BSS region, but this region is tiled by registered owners; no uncovered extent or unique alias is proven"
                g["historical_provenance"]["storage_class"] = "validated-FAR_BSS-range"
            else:
                g["decision"] = "unresolved-no-historical-storage-provenance"
                g["reason"] = "no accepted DATA/BSS placement, exact PUBLIC, or validated FAR_BSS range establishes storage here"
                g["historical_provenance"]["storage_class"] = "unresolved"

        # The initialized root:15F8 pointer table has two externally referenced
        # interior elements. Model them as typed source expressions, not as
        # independent objects at those addresses.
        if addr in {"55B3:1CD8", "55B3:1CDC"}:
            source = (ROOT / "src/root/m15F8.c").read_text(encoding="latin1")
            table_decl = re.search(r"char\s+far\s*\*\s*fd_55B3_1CD4\s*\[\s*\]\s*=\s*\{(.*?)\n\s*\};", source, re.S)
            provider = next((p for p in public_index.get("55B3:1CD4", [])
                             if p["source_module"] == "root:15F8" and p["source_name"] == "fd_55B3_1CD4"), None)
            module_pin = next((p for p in exact_module_pins if p["module"] == "root:15F8"), None)
            strings = re.findall(r'"(?:\\.|[^"\\])*"', table_decl.group(1)) if table_decl else []
            required_fixup_offsets = [provider["object_offset"] + 4 * i for i in range(5)] if provider else []
            observed_fixup_offsets = sorted(f["offset"] for f in (module_pin or {}).get("data_pointer32_fixups", []))
            index = (int(addr.split(":")[1], 16) - 0x1CD4) // 4
            views = migration.get("unprovided_symbol_contracts", {}).get(g["unprovided_members"][0], {}).get("source_views", [])
            pointer_views_ok = bool(views) and all(v.get("base") == "char *" and not v.get("dims") for v in views)
            if provider and len(strings) == 5 and required_fixup_offsets == observed_fixup_offsets and \
                    index in (1, 2) and pointer_views_ok and \
                    int(addr.split(":")[1], 16) == 0x1CD4 + 4 * index:
                alias = {"name": g["unprovided_members"][0], "owner": "fd_55B3_1CD4",
                         "expression": f"fd_55B3_1CD4[{index}]", "address": addr,
                         "element_index": index, "element_width_bytes": 4,
                         "declaration_removal_required": True, "provider_public": provider,
                         "omf_pointer32_fixup_offsets": observed_fixup_offsets,
                         "initializer_count": len(strings), "source": "src/root/m15F8.c",
                         "consumer_modules": sorted({v["module"] for v in views})}
                source_expression_aliases.append(alias)
                g["decision"] = "initialized-pointer-array-interior-alias-candidate"
                g["reason"] = "exact accepted OMF PUBLIC at array base plus source-defined five-element far-pointer table proves an interior element"
                g["historical_provenance"].update({"storage_class": "initialized-pointer-array-interior",
                                                   "provider_public": provider, "element_index": index,
                                                   "element_width_bytes": 4})

        # Emit only FAR_BSS integer primitives whose full source view extent is
        # equal to the validated registry gap. Pointer, struct, incomplete, or
        # conflicting views remain explicit debt.
        seg, off = address_from_key(addr)
        if seg == FARBSS_SEG:
            farrow = farbss_rows.get(off)
            assessment = g.get("assessment", {})
            names = g.get("unprovided_members", [])
            extra_names = set(g.get("registered_address_members", [])) - set(names)
            extra_views = []
            alias_targets = {}
            for member in names + sorted(extra_names):
                target, _ = canonical_alias(member, symbols.get("data", {}))
                if member in names and target in extra_names:
                    alias_targets[member] = target
                    view_owner = target
                elif member in extra_names and target in names:
                    alias_targets[member] = target
                    view_owner = target
                else:
                    continue
                extra_views.extend(v for v in migration.get("object_declaration_views", [])
                                   if v.get("name") == view_owner and v.get("layout_address") == [seg, off])
                target_contract = migration.get("unprovided_symbol_contracts", {}).get(view_owner)
                if target_contract:
                    extra_views.extend(v for v in target_contract.get("source_views", [])
                                       if v.get("layout_address") == [seg, off])
            merged_views = [v for name in names
                            for v in migration.get("unprovided_symbol_contracts", {}).get(name, {}).get("source_views", [])]
            merged_views += extra_views
            merged_assessment = assess_views(merged_views, allow_incomplete=False) if merged_views else assessment
            if farrow and farrow["status"] != "unverified" and merged_assessment.get("ok") and \
                    merged_assessment.get("extent_bytes") == farrow["size"] and \
                    all("*" not in str(r["type"].get("base", "")) for r in merged_assessment.get("view_rows", [])):
                # Only extras explicitly registered as same-address aliases
                # and backed by compatible source views can join this owner.
                unproved_extras = extra_names - set(alias_targets.values())
                if not unproved_extras:
                    owner = next(iter(alias_targets.values()), None) or next((n for n in names if not n.startswith("fd_")), names[0])
                    alias_names = set(names) | set(alias_targets)
                    g["bss_aliases"] = sorted(alias_names - {owner})
                    for alias_name in alias_names:
                        if alias_name != owner:
                            alias_map[alias_name] = owner
                    g["decision"] = "validated-farbss-integer-common-owner-candidate"
                    g["reason"] = "source/save-table extent agrees with exact registered FAR_BSS next-symbol gap; merged alias views are complete compatible integer primitives"
                    g["owner"] = owner
                    g["owner_extent_bytes"] = farrow["size"]
                    g["historical_provenance"].update({"storage_class": "validated-FAR_BSS-common",
                        "farbss_gap": farrow, "no_pointer_or_struct_views": True,
                        "merged_view_assessment": merged_assessment,
                        "same_address_alias_targets": alias_targets,
                        "unproved_extra_names": sorted(unproved_extras)})
                    bss_candidates.append(g)
                else:
                    g["historical_provenance"]["farbss_owner_blocker"] = {
                        "reason": "same-address registered members need explicit alias/type review",
                        "members": sorted(unproved_extras)}
            elif farrow:
                g["historical_provenance"]["farbss_owner_blocker"] = {
                    "reason": "not a complete validated integer owner extent",
                    "farbss_gap": farrow,
                    "assessment_reason": assessment.get("reason"),
                    "assessment_extent": assessment.get("extent_bytes")}
        if g["decision"] == "scratch-BSS-owner-candidate":
            raise SystemExit(f"unsafe legacy BSS decision survived provenance classification: {addr}")
        decisions[g["decision"]] += 1
        groups.append(g)

    test_controls = controls()
    if not test_controls["passed"]:
        raise SystemExit("provenance classifier positive/negative controls failed")

    flagged = {}
    for address in ["55B3:3DB2", "55B3:3DB4", "55B3:3DDE", "1B73:0006", "55B3:19BE"]:
        flagged[address] = next((g for g in groups if g["address"] == address), None)
    if any(flagged[a] is None for a in flagged):
        raise SystemExit("expected false-owner regression address missing from candidate inventory")
    if any(flagged[a]["decision"] != "initialized-asm-data-candidate" for a in ["55B3:3DB2", "55B3:3DB4", "55B3:3DDE"]):
        raise SystemExit("initialized ASM candidates were not classified by exact PUBLIC")
    if flagged["1B73:0006"]["decision"] != "excluded-code-address":
        raise SystemExit("code-address regression was not rejected")
    if flagged["55B3:19BE"]["decision"] != "exact-omf-public-alias-rename-candidate":
        raise SystemExit("g19BE same-address owner was not established")

    pointer_common_review = []
    for g in groups:
        if not g["address"].startswith("50F6:") or g["decision"] == "validated-farbss-integer-common-owner-candidate":
            continue
        views = [v for name in g.get("unprovided_members", [])
                 for v in migration.get("unprovided_symbol_contracts", {}).get(name, {}).get("source_views", [])]
        ptr_views = [v for v in views if "*" in str(v.get("base", ""))]
        if not ptr_views:
            continue
        bases = sorted({v.get("base", "") for v in ptr_views})
        dims = sorted({tuple(v.get("dims", [])) for v in ptr_views})
        off = int(g["address"].split(":")[1], 16)
        farrow = farbss_rows.get(off)
        source_declarations = []
        for v in ptr_views:
            text = source_text.get(v["module"], "")
            for line_no, line in enumerate(text.splitlines(), 1):
                if v["name"] in line and "extern" in line:
                    source_declarations.append({"source": v["module"], "line": line_no, "text": line.strip()})
        four_byte_common_candidate = bool(farrow and farrow["size"] == 4 and
            farrow["status"] in {"verified", "pinned", "consistent"} and len(bases) == 1 and
            len(dims) == 1 and dims[0] == () and bases[0].count("*") == 1)
        pointer_common_review.append({"address": g["address"], "members": g.get("unprovided_members", []),
            "source_pointer_views": ptr_views, "pointer_bases": bases, "dimensions": [list(x) for x in dims],
            "farbss_gap": farrow, "four_byte_far_common_candidate": four_byte_common_candidate,
            "source_declarations": source_declarations,
            "decision": "withheld-pointer-owner-review",
            "reason": "typed host-pointer ownership and any address/buffer arithmetic require owner-specific platform review; this generic byte-owner TU does not wire pointer state"})

    owner_addrs = [g["address"] for g in bss_candidates]
    regression_checks = {
        "g_3DB2_initializer_not_zero_owner": flagged["55B3:3DB2"]["decision"] == "initialized-asm-data-candidate" and "55B3:3DB2" not in owner_addrs,
        "g_3DB4_initializer_not_zero_owner": flagged["55B3:3DB4"]["decision"] == "initialized-asm-data-candidate" and "55B3:3DB4" not in owner_addrs,
        "g_3DDE_initializer_not_zero_owner": flagged["55B3:3DDE"]["decision"] == "initialized-asm-data-candidate" and "55B3:3DDE" not in owner_addrs,
        "fd_1B73_0006_code_not_zero_owner": flagged["1B73:0006"]["decision"] == "excluded-code-address" and "1B73:0006" not in owner_addrs,
        "g_19BE_has_one_initialized_owner": flagged["55B3:19BE"]["owner"] == "g_19BE" and "55B3:19BE" not in owner_addrs,
        "pointer_table_interiors_are_expressions": len(source_expression_aliases) == 2 and all(x["declaration_removal_required"] for x in source_expression_aliases) and not ({"55B3:1CD8", "55B3:1CDC"} & set(owner_addrs)),
        "BSS_owner_addresses_are_unique": len(owner_addrs) == len(set(owner_addrs)),
        "each_alias_is_OMF_data_or_validated_common": all(
            any(p["source_name"] == target and p["address"] == next(g["address"] for g in groups if alias in g.get("unprovided_members", []))
                for p in public_index.get(next(g["address"] for g in groups if alias in g.get("unprovided_members", [])), []))
            or any(alias in g.get("bss_aliases", []) and g.get("owner") == target for g in bss_candidates)
            for alias, target in alias_map.items()),
    }
    if not all(regression_checks.values()):
        raise SystemExit(f"storage ownership regression failed: {regression_checks}")

    owner_lines = ["/* Scratch owners from validated FAR_BSS integer common extents.",
                   " * Diagnostic source; it is not selected by the production build. */",
                   "#include <stdint.h>", ""]
    emitted_owner_rows = []
    for group in sorted(bss_candidates, key=lambda x: (x["address"], x["owner"])):
        owner, size = group["owner"], group["owner_extent_bytes"]
        owner_lines.append(f"uint8_t {owner}[{size}];")
        for alias_name in group.get("bss_aliases", group["unprovided_members"]):
            if alias_name != owner:
                owner_lines.append(f"extern uint8_t {alias_name}[{size}] __attribute__((alias(\"{owner}\")));")
        owner_lines.append("")
        emitted_owner_rows.append({"address": group["address"], "owner": owner, "size": size,
                                   "members": group["unprovided_members"]})
    owner_text = "\n".join(owner_lines)
    args.emit.parent.mkdir(parents=True, exist_ok=True)
    args.emit.write_text(owner_text, encoding="utf-8")
    owner_hash = sha(args.emit.read_bytes())
    owner_link = compile_and_link_owner(args.emit, migration)

    report = {
        "schema": "simant-whole-program-unprovided-state-provenance-v2",
        "claim": "Scratch provenance correction only. It identifies historical storage classes and alias candidates; it does not wire state or claim behavior.",
        "inputs": {
            "base_plan": {"path": rel(args.base_plan), "sha256": base_hash},
            "migration": {"path": rel(args.migration), "sha256": migration_hash,
                          "generator_sha256": migration.get("generator_sha256")},
            "manifest": {"path": rel(args.manifest), "sha256": manifest_hash},
            "symbols": {"path": rel(args.symbols), "sha256": symbols_hash},
            "exact_omf_modules": exact_module_pins,
            "farbss_account": {"source": "tools/farbss.py",
                               "source_sha256": sha((ROOT / "tools/farbss.py").read_bytes()),
                               "accounted": farbss_report["accounted"],
                               "variables": farbss_report["variables"],
                               "status_bytes": {k: farbss_report["bytes_" + k]
                                                for k in ("verified", "pinned", "consistent", "unverified")}},
            "omf_reader_sha256": sha((ROOT / "tools/omf.py").read_bytes()),
            "compiler_driver_sha256": sha((ROOT / "tools/compiler.py").read_bytes()),
            "compiler_toolchain_sha256": sha((ROOT / "layout/toolchain.json").read_bytes()),
            "farbss_runtime_inputs": {
                "oracle_lock": {"path": "layout/oracle.lock.json", "sha256": sha((ROOT / "layout/oracle.lock.json").read_bytes())},
                "original_executable": {"path": "assets/SIMANT.EXE", "sha256": sha((ROOT / "assets/SIMANT.EXE").read_bytes())},
                "tools": {p: sha((ROOT / p).read_bytes()) for p in ("tools/exe.py", "tools/match.py", "tools/symbols.py", "tools/modules.py")},
            },
            "farbss_bounds": {"segment": FARBSS_SEG, "last_offset_inclusive": FARBSS_LAST,
                              "source": "tools/farbss.py", "source_sha256": sha((ROOT / "tools/farbss.py").read_bytes())},
        },
        "method": {
            "code": "Manifest code extents are interpreted in their declared frame and excluded before state classification.",
            "data": "Manifest placement ranges and exact recompiled accepted-source OMF hashes/PUBLIC offsets distinguish initialized ASM/C data from BSS.",
            "asm_initializers": "Literal primitive initializers are retained separately as typed candidates from genuine ASM source directives; they are never zeroed.",
            "aliases": "A missing view can rename to a near public only where exact OMF PUBLIC offset plus manifest placement resolve to the same address and source declaration storage width agrees. Names alone are insufficient.",
            "bss": "FAR_BSS owners are emitted only where source/save-table extent evidence matches the exact registered next-symbol gap and every view is a complete compatible integer primitive; pointer, struct, incomplete extent, and conflicting alias groups remain debt.",
            "pointer_tables": "Initialized pointer-array interior addresses are source-expression aliases with standalone declaration removal required; they are never independent objects.",
        },
        "controls": test_controls,
        "regression_controls": regression_checks,
        "summary": {
            "input_candidate_groups": len(groups),
            "decision_counts": dict(sorted(decisions.items())),
            "zero_init_bss_owner_candidates": len(bss_candidates),
            "alias_rename_candidates": len(alias_map),
            "historical_asm_initializer_candidates": len(asm_initializers),
            "source_expression_alias_candidates": len(source_expression_aliases),
            "emitted_owner_bytes": sum(x["owner_extent_bytes"] for x in bss_candidates),
            "pointer_groups_withheld": len(pointer_common_review),
            "pointer_groups_meeting_4byte_far_common_shape": sum(x["four_byte_far_common_candidate"] for x in pointer_common_review),
            "regressions": {"g_3DB2": flagged["55B3:3DB2"]["decision"],
                            "g_3DB4": flagged["55B3:3DB4"]["decision"],
                            "g_3DDE": flagged["55B3:3DDE"]["decision"],
                            "fd_1B73_0006": flagged["1B73:0006"]["decision"],
                            "fd_55B3_19BE": flagged["55B3:19BE"]["decision"]},
        },
        "rename_map": alias_map,
        "asm_initialized_candidates": asm_initializers,
        "source_expression_aliases": source_expression_aliases,
        "pointer_common_review": pointer_common_review,
        "groups": sorted(groups, key=lambda g: (g["address"], g["unprovided_members"])),
        "bss_owner_candidates": bss_candidates,
        "owner_source": {"path": rel(args.emit), "sha256": owner_hash, "definitions": emitted_owner_rows},
        "owner_link_diagnostic": owner_link,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Whole-program state provenance correction v2", "",
          "> Diagnostic only. No state owner is wired into the native program.", "",
          f"Input primitive-view plan SHA-256: `{base_hash}`.",
          f"Frozen manifest SHA-256: `{manifest_hash}`.", "",
          "## Classification", "",
          f"- Candidate groups: {len(groups)}",
          f"- ASM initializer candidates: {len(asm_initializers)}",
          f"- Exact-public alias candidates: {len(alias_map)}",
          f"- Validated integer FAR_BSS owner candidates: {len(bss_candidates)} ({sum(x['owner_extent_bytes'] for x in bss_candidates)} bytes)",
          f"- Previous partial-link unresolveds removed: {owner_link['unresolved_symbols_removed']}",
          "- Provenance regression controls: passed.", "",
          "The prior 131-owner scratch-BSS count is withdrawn by this report. Only integer FAR_BSS common extents with matching registered gaps and source evidence are emitted. Initialized DATA and CODE addresses cannot create BSS owners. Pointers, incomplete arrays, conflicting names, and unverified sizes remain unresolved.", "",
          "## Flagged regressions", "",
          "| Address | Candidate | Result | Evidence |", "|---|---|---|---|"]
    for addr, label in [("55B3:3DB2", "g_3DB2"), ("55B3:3DB4", "g_3DB4"), ("55B3:3DDE", "g_3DDE"),
                        ("1B73:0006", "fd_1B73_0006"), ("55B3:19BE", "fd_55B3_19BE")]:
        row = flagged[addr]
        md.append(f"| `{addr}` | `{label}` | `{row['decision']}` | {row['reason']} |")
    md += ["", "## Initialized ASM candidates", "", "| Address | Name | Directive | Initializer |", "|---|---|---|---|"]
    for x in asm_initializers:
        md.append(f"| `{x['address']}` | `{x['name']}` | `{x['directive']}` ({x['storage_width_bytes']} bytes) | `{x['initializer_expression']}` |")
    md += ["", "## Initialized pointer table aliases", "", "| Address | Alias expression | Owner | Declaration handling |", "|---|---|---|---|"]
    for x in source_expression_aliases:
        md.append(f"| `{x['address']}` | `{x['expression']}` | `{x['owner']}` | Remove standalone declaration of `{x['name']}` |")
    md += ["", "## Pointer common debt", "",
           f"- Pointer groups reviewed and withheld from byte-owner emission: {len(pointer_common_review)}",
           f"- Groups with one scalar pointer view and a consistent four-byte FAR_BSS gap: {sum(x['four_byte_far_common_candidate'] for x in pointer_common_review)}",
           "- No pointer variable is emitted by this scratch owner TU. The report retains source declarations, pointer-level consistency, and FAR_BSS gap evidence for owner-specific host-pointer and address-arithmetic review.", ""]
    md += ["", "## Decision counts", ""]
    for name, count in sorted(decisions.items()):
        md.append(f"- {count}: `{name}`")
    md += ["", f"Exact OMF module/source/object identities, placements, candidate groups, and unresolved explanations are recorded in the JSON report. Scratch owner source: `{rel(args.emit)}` (SHA-256 `{owner_hash}`); it is not selected by the whole-program build. The previous plan and its scratch object are retained as historical diagnostics, not accepted owners.", ""]
    args.markdown.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
