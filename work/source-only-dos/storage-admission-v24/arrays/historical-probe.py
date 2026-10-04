"""Rebuild whole-module FAR_BSS controls and clean storage-only DOS probes.

All generated sources/objects/links/logs stay in this worker directory. No original
game object, image bytes, or game-function adapter is part of the runtime fixture.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))

import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader


ARRAYS = {
    "fd_50F6_0334": {"count": 12, "bytes": 24, "owner": "S06:35F5", "type": "int far"},
    "fd_50F6_38CA": {"count": 15, "bytes": 30, "owner": "S13:384C", "type": "int far"},
    "fd_50F6_38E8": {"count": 17, "bytes": 34, "owner": "S13:384C", "type": "int far"},
    "fd_50F6_390A": {"count": 17, "bytes": 34, "owner": "S13:384C", "type": "int far"},
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def fixup_key(f):
    return tuple(f[k] for k in (
        "segment", "offset", "width", "loc", "self_relative", "target_kind",
        "target", "displacement", "frame_kind", "frame", "encoded_addend"))


def omf_packet(o):
    return {
        "segments": {k: {"length": len(v), "sha256": sha(bytes(v))}
                     for k, v in sorted(o.segments.items())},
        "segment_defs": o.segment_defs,
        "segment_lengths": o.segment_lengths,
        "groups": o.groups,
        "publics": o.publics,
        "ordered_fixups": [fixup_key(f) for f in o.linker_fixups],
        "external_names": o.externals,
        "external_scopes": o.external_scopes,
        "communals": o.communals,
    }


def map_public_sections(map_path: Path):
    lines = map_path.read_text(encoding="latin1", errors="replace").splitlines()
    names = {"_" + n for n in ARRAYS} | {"_yard_probe_base_" + n.rsplit("_", 1)[1] for n in ARRAYS}
    name_header = next((i for i, s in enumerate(lines) if "Publics by Name" in s), None)
    value_header = next((i for i, s in enumerate(lines) if "Publics by Value" in s), None)
    if name_header is None or value_header is None or value_header <= name_header:
        raise RuntimeError(f"missing Name/Value public sections in {map_path}")

    def rows(section):
        out = []
        for raw in section:
            fields = raw.split()
            if len(fields) >= 3 and fields[-1] in names:
                address = fields[0]
                out.append({"name": fields[-1], "address": address, "kind": fields[-2], "raw": raw.strip()})
        return out

    by_name = rows(lines[name_header + 1:value_header])
    by_value = rows(lines[value_header + 1:])
    expected = names
    if {r["name"] for r in by_name} != expected or {r["name"] for r in by_value} != expected:
        raise RuntimeError(f"Name/Value public map rows incomplete in {map_path}: {by_name} / {by_value}")
    bss_lines = [line.strip() for line in lines if " FAR_BSS" in line and "FAR_BSS" in line]
    return {"by_name": by_name, "by_value": by_value, "far_bss_map_line": bss_lines[:1]}


def compile_obj(text: str, profile: str, flags: list[str], label: str, source_basename: str | None = None):
    result = compiler.compile_c(text, profile, flags, basename=source_basename or label, keep=False)
    if not result.ok:
        raise RuntimeError(f"compile failed: {label}\n{result.log}")
    (OUT / f"{label}.OBJ").write_bytes(result.obj)
    return OmfReader(communals=True).read(result.obj), result.obj


def compile_whole_module(manifest, key, expected_decls, replacements, negative_specs):
    row = manifest["modules"][key]
    short = key.split(":", 1)[0]
    original_path = ROOT / row["source"]
    # The manifest objects were compiled under the normal tools/compiler.py default.
    # Keep the generated module/segment name stable (UNIT_TEXT) for the control/candidate pair.
    source_basename = "UNIT"
    source = original_path.read_text(encoding="ascii")
    for old in expected_decls:
        if source.count(old) != 1:
            raise AssertionError(f"{key}: expected one declaration: {old}")
    control, control_bytes = compile_obj(source, row["profile"], row["flags"], short + "CTL", source_basename)
    if row.get("object_sha256") and sha(control_bytes) != row["object_sha256"]:
        raise AssertionError(f"fresh control does not match manifest object for {key}")
    candidate_source = source
    for old, new in replacements:
        candidate_source = candidate_source.replace(old, new)
    (OUT / (key.replace(":", "_") + "_tentative_owner.c")).write_text(candidate_source, encoding="ascii")
    candidate, candidate_bytes = compile_obj(candidate_source, row["profile"], row["flags"], short + "OWN", source_basename)

    controls = omf_packet(control)
    candidate_packet = omf_packet(candidate)
    expected_scope_names = {"_" + old.split()[-1].split("[")[0].rstrip(";") for old, _ in replacements}
    baseline_names = [n for n in controls["external_names"] if n not in expected_scope_names]
    candidate_names = [n for n in candidate_packet["external_names"] if n not in expected_scope_names]
    baseline_scopes = dict(zip(controls["external_names"], controls["external_scopes"]))
    candidate_scopes = dict(zip(candidate_packet["external_names"], candidate_packet["external_scopes"]))
    checks = {
        "all_segment_bytes_identical": controls["segments"] == candidate_packet["segments"],
        "segment_definitions_lengths_groups_identical": all(controls[k] == candidate_packet[k] for k in ("segment_defs", "segment_lengths", "groups")),
        "publics_identical": controls["publics"] == candidate_packet["publics"],
        "ordered_fixups_identical": controls["ordered_fixups"] == candidate_packet["ordered_fixups"],
        "other_external_name_order_identical": baseline_names == candidate_names,
    }
    if set(baseline_scopes) != set(candidate_scopes):
        raise AssertionError(f"{key} external name set changed")
    scope_deltas = [{"name": name, "control": baseline_scopes[name], "candidate": candidate_scopes[name]}
                    for name in baseline_scopes if baseline_scopes[name] != candidate_scopes[name]]
    actual_scope_names = {x["name"] for x in scope_deltas}
    checks["only_expected_extern_to_communal_scope_changes"] = (
        actual_scope_names == expected_scope_names and
        all(x["control"] == "external" and x["candidate"] == "communal" for x in scope_deltas)
    )
    for name, wanted in checks.items():
        if not wanted:
            raise AssertionError(f"{key} whole-module check failed: {name}")
    if control.communals:
        raise AssertionError(f"{key} control unexpectedly has communal records")

    negatives = {}
    for i, (label, negative_source, expect) in enumerate(negative_specs):
        nobj, nbytes = compile_obj(negative_source, row["profile"], row["flags"], short + "N" + str(i), source_basename)
        ncomms = {c["name"]: c for c in nobj.communals}
        actual = {name: ncomms.get(name, {}).get("length") for name in expect}
        if actual != expect:
            raise AssertionError(f"{key} negative {label} communal lengths {actual} != {expect}")
        npacket = omf_packet(nobj)
        negatives[label] = {"object": short + "N" + str(i) + ".OBJ", "object_sha256": sha(nbytes),
                            "expected_communal_lengths": expect, "actual_communal_rows": nobj.communals,
                            "emitted_segment_lengths": npacket["segment_lengths"],
                            "segments_equal_control": npacket["segments"] == controls["segments"]}
    return {
        "module": key,
        "source": row["source"],
        "source_sha256": row["source_sha256"],
        "profile": row["profile"],
        "flags": row["flags"],
        "manifest_object_sha256": row.get("object_sha256"),
        "fresh_control_object_sha256": sha(control_bytes),
        "candidate_object_sha256": sha(candidate_bytes),
        "object_size_delta": len(candidate_bytes) - len(control_bytes),
        "checks": checks,
        "scope_deltas": scope_deltas,
        "candidate_communal_rows": candidate.communals,
        "negative_controls": negatives,
    }


OWNER_TEXT = r'''int far fd_50F6_0334[12];
int far fd_50F6_38CA[15];
int far fd_50F6_38E8[17];
int far fd_50F6_390A[17];
'''

RUNTIME_TEXT = r'''extern int far fd_50F6_0334[12];
extern int far fd_50F6_38CA[15];
extern int far fd_50F6_38E8[17];
extern int far fd_50F6_390A[17];
extern int far yard_probe_base_0334[12];
extern int far yard_probe_base_38CA[15];
extern int far yard_probe_base_38E8[17];
extern int far yard_probe_base_390A[17];
extern int far puts(char far *text);
extern void far _fmemset(void far *p, int value, unsigned long count);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far grassSaveRow = { 2, 12, (void far *)&fd_50F6_0334 };
int main(void)
{
    unsigned i;
    unsigned char far *raw = (unsigned char far *)grassSaveRow.data;
    if (grassSaveRow.size != 2 || grassSaveRow.count != 12 || raw != (unsigned char far *)fd_50F6_0334 ||
        yard_probe_base_0334 != fd_50F6_0334 || yard_probe_base_38CA != fd_50F6_38CA ||
        yard_probe_base_38E8 != fd_50F6_38E8 || yard_probe_base_390A != fd_50F6_390A)
        goto fail;
    for (i = 0; i < 12; ++i) if (fd_50F6_0334[i] != 0) goto fail;
    for (i = 0; i < 15; ++i) if (fd_50F6_38CA[i] != 0) goto fail;
    for (i = 0; i < 17; ++i) if (fd_50F6_38E8[i] != 0 || fd_50F6_390A[i] != 0) goto fail;

    /* Test-only reproduction of the source reset stores; no game routine is linked. */
    fd_50F6_0334[0] = fd_50F6_0334[1] = fd_50F6_0334[2] = 0;
    for (i = 3; i < 12; ++i) fd_50F6_0334[i] = -1;
    _fmemset(fd_50F6_38CA, -1, 0x1eUL);
    _fmemset(fd_50F6_38E8, -1, 0x22UL);
    _fmemset(fd_50F6_390A, -1, 0x22UL);
    if (fd_50F6_0334[0] || fd_50F6_0334[1] || fd_50F6_0334[2]) goto fail;
    for (i = 3; i < 12; ++i) if (fd_50F6_0334[i] != -1) goto fail;
    for (i = 0; i < 15; ++i) if (fd_50F6_38CA[i] != -1) goto fail;
    for (i = 0; i < 17; ++i) if (fd_50F6_38E8[i] != -1 || fd_50F6_390A[i] != -1) goto fail;
    fd_50F6_38CA[0] = -1;
    if (fd_50F6_38CA[0] >= 0) goto fail;

    /* Every element is independently addressable; raw bytes agree with signed words. */
    for (i = 0; i < 12; ++i) fd_50F6_0334[i] = (int)(0x1200 + i);
    for (i = 0; i < 15; ++i) fd_50F6_38CA[i] = (int)(0x2100 + i);
    for (i = 0; i < 17; ++i) { fd_50F6_38E8[i] = (int)(0x3200 + i); fd_50F6_390A[i] = (int)(0x4300 + i); }
    for (i = 0; i < 12; ++i) {
        unsigned v = (unsigned)(0x1200 + i);
        if (fd_50F6_0334[i] != (int)v || raw[2*i] != (unsigned char)v || raw[2*i+1] != (unsigned char)(v >> 8)) goto fail;
    }
    for (i = 0; i < 15; ++i) if (fd_50F6_38CA[i] != (int)(0x2100 + i)) goto fail;
    for (i = 0; i < 17; ++i)
        if (fd_50F6_38E8[i] != (int)(0x3200 + i) || fd_50F6_390A[i] != (int)(0x4300 + i)) goto fail;
    if (puts("PASS") == -1) return 2;
    return 0;
fail:
    puts("FAIL");
    return 1;
}
'''

SIGNED_NEGATIVE_TEXT = RUNTIME_TEXT.replace(
    "extern int far fd_50F6_38CA[15];", "extern unsigned int far fd_50F6_38CA[15];"
).replace(
    "for (i = 0; i < 15; ++i) if (fd_50F6_38CA[i] != -1) goto fail;",
    "for (i = 0; i < 15; ++i) if ((int)fd_50F6_38CA[i] != -1) goto fail;"
)

INIT_OWNER_TEXT = r'''int far fd_50F6_0334[12] = { 1 };
int far fd_50F6_38CA[15];
int far fd_50F6_38E8[17];
int far fd_50F6_390A[17];
'''


def compile_runtime(label, source, flags):
    path = OUT / f"{label}.C"
    path.write_text(source, encoding="ascii")
    obj, raw = compile_obj(source, "msc600ax", flags, label)
    return path, raw, obj


def run_runtime_case(profile_name, case_name, consumer_obj, owner_obj, alias_delta, expect, tc, runtimes, linker, runner, tool_dir):
    d = OUT / profile_name / case_name
    d.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (d / name).unlink(missing_ok=True)
    (d / "CRT.OBJ").write_bytes(consumer_obj)
    (d / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row["path"], d / Path(row["path"]).name.upper())
    aliases = []
    for sym in ARRAYS:
        delta = alias_delta.get(sym, 0)
        suffix = sym.rsplit("_", 1)[1]
        aliases.append(f"DEFINE _yard_probe_base_{suffix} = _{sym}" + (f" + {delta}" if delta else ""))
    script = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\n"
              "FILE CRT\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n" +
              "\r\n".join(aliases) + "\r\n")
    (d / "PROBE.LNK").write_bytes(script.encode("ascii"))
    (d / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (d / "RUN.BAT").write_bytes((f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf = []
    for section, settings in runner["conf"].items():
        conf += [f"[{section}]"] + [f"{k}={v}" for k, v in settings.items()]
    conf += ["[autoexec]", f'mount c "{d}"', f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"]
    (d / "dosbox.conf").write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed = False
    try:
        result = subprocess.run([runner["path"], "-conf", str(d / "dosbox.conf"), "-fastlaunch", "-exit", "-nomenu"],
                                cwd=d, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        timed = True
        result = type("Timeout", (), {"returncode": -1})()
    actual = (d / "RUN.LOG").read_text(encoding="latin1").strip() if (d / "RUN.LOG").exists() else "NO RUN.LOG"
    link_log = (d / "LINK.LOG").read_text(encoding="latin1", errors="replace") if (d / "LINK.LOG").exists() else ""
    map_publics = map_public_sections(d / "PROBE.MAP") if (d / "PROBE.MAP").exists() else {"error": "missing map"}
    files = [{"name": p.name, "sha256": dos.pin(p)[1]} for p in sorted(d.iterdir()) if p.is_file()]
    passed = actual == expect and result.returncode == 0 and not timed
    return {"linker": profile_name, "case": case_name, "expected": expect, "actual": actual,
            "exit": result.returncode, "timed_out": timed, "passed": passed,
            "alias_delta": alias_delta, "resolved_map_publics": map_publics,
            "link_log_tail": link_log[-1000:], "artifacts": files}


def main():
    denied = dos.install_input_guard()
    manifest_raw, manifest_pin = dos.pin(ROOT / "layout/manifest.json")
    manifest = json.loads(manifest_raw)
    m06 = manifest["modules"]["S06:35F5"]
    m13 = manifest["modules"]["S13:384C"]

    inventory_root = ROOT / "build/workers/dos_far_word_inventory_v22"
    source_pins_path = inventory_root / "source-pins-v22.json"
    cohorts_path = inventory_root / "cohorts-v22.json"
    numeric_path = inventory_root / "numeric-alias-asm-v22.json"
    overlap_path = inventory_root / "provider-overlap-v22.json"
    source_pins_raw, source_pins_pin = dos.pin(source_pins_path)
    source_pins = json.loads(source_pins_raw)
    source_receipts = source_pins["source_receipts"]
    source_paths = {r["path"] for r in source_receipts}
    if len(source_receipts) != 156 or len(source_paths) != 156 or source_pins.get("unique_source_paths") != 156:
        raise AssertionError("expected the pinned canonical 127 + effective strict-29 source census")
    verified_sources = 0
    for receipt in source_receipts:
        dos.pin(ROOT / receipt["path"], receipt["sha256"])
        verified_sources += 1
    cohorts_raw, cohorts_pin = dos.pin(cohorts_path)
    cohorts = json.loads(cohorts_raw)
    cohort = next(c for c in cohorts["cohorts"] if c["id"] == "simyard_grass_and_animation_arrays")
    member_by_address = {m["address"]: m for m in cohort["members"]}
    numeric_raw, numeric_pin = dos.pin(numeric_path)
    numeric = json.loads(numeric_raw)
    numeric_by_address = {m["address"]: m for m in numeric["members"]}
    overlap_raw, overlap_pin = dos.pin(overlap_path)
    overlap = json.loads(overlap_raw)
    symbols_raw, symbols_pin = dos.pin(ROOT / "layout/symbols.json")
    symbols = json.loads(symbols_raw)
    source_to_member = {
        "fd_50F6_0334": "50F6:0334",
        "fd_50F6_38CA": "50F6:38CA",
        "fd_50F6_38E8": "50F6:38E8",
        "fd_50F6_390A": "50F6:390A",
    }
    registry_view_audit = {}
    for name, address in source_to_member.items():
        member = member_by_address[address]
        size = ARRAYS[name]["bytes"]
        row = symbols["data"].get(name)
        if not row or row.get("seg") != 0x50F6:
            raise AssertionError(f"missing registered base row for {name}")
        start = row["off"]
        same_span = [{"name": n, "offset": v["off"], "alias_of": v.get("alias_of")}
                     for n, v in symbols["data"].items()
                     if v.get("seg") == 0x50F6 and start <= v.get("off", -1) < start + size]
        if same_span != [{"name": name, "offset": start, "alias_of": row.get("alias_of")}]:
            raise AssertionError(f"interior or duplicate data symbol in independently measured span {name}: {same_span}")
        if member.get("current_provider_span_overlaps"):
            raise AssertionError(f"current provider span overlap for {name}")
        num = numeric_by_address[address]
        if any(num.get(k) for k in ("exact_symbol_asm_occurrences", "explicit_50F6_segment_or_far_address_occurrences", "explicit_hex_offset_literal_occurrences")):
            raise AssertionError(f"numeric/ASM escape census found a hit for {name}")
        registry_view_audit[name] = {
            "complete_array_declarations": member["complete_array_declarations"],
            "exact_base_registry_rows": member["exact_base_registry_rows"],
            "same_span_registered_data_names": same_span,
            "non_save_address_escapes": member.get("non_save_address_escapes", []),
            "bounded_bulk_operation_count": len(member.get("bounded_bulk_operation_receipts", [])),
            "current_provider_span_overlaps": member.get("current_provider_span_overlaps", []),
            "numeric_asm_hits": {
                k: num.get(k, []) for k in (
                    "exact_symbol_asm_occurrences", "explicit_50F6_segment_or_far_address_occurrences",
                    "explicit_hex_offset_literal_occurrences")
            },
        }
    source_audit = {
        "inventory_cohort": cohort["id"],
        "source_owner_role": cohort["source_owner"],
        "source_set_counts": source_pins["sets"],
        "unique_source_path_count": source_pins["unique_source_paths"],
        "source_pin_receipts_verified": verified_sources,
        "inventory_status": source_pins["status"],
        "numeric_scan": {
            "source_path_count": numeric["source_path_count"],
            "selected_address_count": numeric["selected_addresses"],
            "exact_symbol_assembly_hit_count": numeric["exact_symbol_assembly_hit_count"],
            "explicit_far_segment_or_address_hit_count": numeric["explicit_far_segment_or_address_hit_count"],
            "explicit_exact_hex_offset_hit_count": numeric["explicit_exact_hex_offset_hit_count"],
            "status": numeric["status"],
        },
        "registered_views_and_spans": registry_view_audit,
        "save_record": {
            "fd_50F6_0334": {"source": "src/S09/m35F5.c:974", "shape": {"size": 2, "count": 12}, "serialized_bytes": 24,
                              "address_view": "extern unsigned char far[]; address is passed as SaveRec data; no byte indexing in S09"},
            "animation_arrays": "No SaveRec rows for fd_50F6_38CA, fd_50F6_38E8, or fd_50F6_390A.",
        },
        "lifecycle_and_bounds": {
            "grass": "InitGrassMap writes all 12 words: slots 0..2=0; slots 3..11=-1. Normal GetMowDir checks IsValidYard before NotMowed; x is 0..11 and y is 0..15. NotMowed itself has no local bounds test; the SaveRec loader can restore arbitrary word payloads, so no malformed-value safety claim is made.",
            "rain_handles": "Draw_SimYard first-animation-set branch performs the whole 30-byte -1 reset. DrawRain uses indices 0..13 (14 iterations); the no-rain cleanup reads/removes slots 0..14. Slot 14 has no normal producer write in the scanned source.",
            "swarm_handles": "The two first-animation-set resets each cover 34 bytes. Each DrawSwarm producer checks i>=16 before indexing, and cleanup ends at i<16; normal handle access is indices 0..15. Dynamic count and companion coordinate payload values remain separate runtime-domain questions; handle slot 16 is reset but not read/written in the scanned normal path.",
            "lifecycle": "All three handle arrays reset only when mode<=1 and fd_50F6_10DA is false. Draw_SimYard then reuses handles, removing slots and setting them back to -1 as sources change; it does not reset on every draw.",
        },
        "audit_artifact_pins": [source_pins_pin, cohorts_pin, numeric_pin, overlap_pin, symbols_pin],
    }

    s06 = (ROOT / m06["source"]).read_text(encoding="ascii")
    s13 = (ROOT / m13["source"]).read_text(encoding="ascii")
    old06 = "extern int far fd_50F6_0334[12];"
    old13 = ["extern int far fd_50F6_38CA[15];", "extern int far fd_50F6_38E8[17];", "extern int far fd_50F6_390A[17];"]
    candidate06 = "int far fd_50F6_0334[12];"
    candidate13 = [x.replace("extern ", "") for x in old13]
    negs06 = [
        ("short_extent", s06.replace(old06, "int far fd_50F6_0334[11];"), {"_fd_50F6_0334": 22}),
        ("byte_width", s06.replace(old06, "unsigned char far fd_50F6_0334[24];"), {"_fd_50F6_0334": 24}),
        ("wide_width", s06.replace(old06, "long far fd_50F6_0334[12];"), {"_fd_50F6_0334": 48}),
        ("initialized", s06.replace(old06, "int far fd_50F6_0334[12] = { 1 };"), {"_fd_50F6_0334": None}),
    ]
    negs13 = []
    for old, count, label, length in [
        (old13[0], 14, "rain_short_extent", 28),
        (old13[1], 16, "swarm_short_extent", 32),
        (old13[2], 16, "fly_short_extent", 32),
        (old13[0], 30, "rain_byte_width", 30),
        (old13[1], 68, "swarm_byte_width", 68),
        (old13[2], 68, "fly_byte_width", 68),
    ]:
        typ = "unsigned char far" if "byte_width" in label else "int far"
        replacement = f"{typ} {old.split()[-1].split('[')[0]}[{count}];"
        # Keep all other arrays as extern so only the tested declaration becomes a communal.
        negs13.append((label, s13.replace(old, replacement), {"_" + old.split()[-1].split("[")[0]: length}))
    s13_init = s13
    for old in old13:
        if old == old13[0]:
            s13_init = s13_init.replace(old, "int far fd_50F6_38CA[15] = { 1 };")
    negs13.append(("initialized_rain", s13_init, {"_fd_50F6_38CA": None}))

    review06 = compile_whole_module(manifest, "S06:35F5", [old06], [(old06, candidate06)], negs06)
    review13 = compile_whole_module(manifest, "S13:384C", old13, list(zip(old13, candidate13)), negs13)

    s09meta = manifest["modules"]["S09:35F5"]
    s09source = (ROOT / s09meta["source"]).read_text(encoding="ascii")
    s09control, s09bytes = compile_obj(s09source, s09meta["profile"], s09meta["flags"], "S09CTL", "UNIT")
    if sha(s09bytes) != s09meta.get("object_sha256"):
        raise AssertionError("fresh S09 extern-view control differs from its pinned manifest object")
    save_public = next((p for p in s09control.publics if p["name"] == "_fd_4E4B_0000"), None)
    if not save_public:
        raise AssertionError("S09 SaveRec table has no measured public base")
    save_fixups = [f for f in s09control.linker_fixups
                   if f["target"] == "_fd_50F6_0334" and f["segment"] == save_public["segment"]]
    if len(save_fixups) != 1:
        raise AssertionError(f"expected exactly one S09 SaveRec pointer relocation to grass storage: {save_fixups}")
    save_fixup = save_fixups[0]
    save_relative = save_fixup["offset"] - save_public["offset"]
    if save_fixup["width"] != 4 or save_fixup["loc"] != "pointer32" or save_fixup["encoded_addend"] != "00000000" or save_relative % 8 != 4:
        raise AssertionError(f"unexpected SaveRec pointer relocation shape/offset: {save_fixup}, base={save_public}")
    save_fixup_evidence = {
        "source": s09meta["source"], "source_sha256": s09meta["source_sha256"],
        "object_sha256": sha(s09bytes), "manifest_object_sha256": s09meta["object_sha256"],
        "save_record_array_public": save_public,
        "table_relative_byte_offset": save_relative,
        "row_index_from_compiled_stride_8": save_relative // 8,
        "pointer_field_offset_in_record": save_relative % 8,
        "source_save_row_line": 974,
        "source_row_value": "{ 2, 12, (void far *)&fd_50F6_0334 },",
        "compiled_pointer_fixup": save_fixup,
        "interpretation": "The full S09 source object has a width-4 FAR pointer fixup in the measured SaveRec table segment, targeting _fd_50F6_0334 with zero encoded addend at the compiled row's data member. The row shape is source-confirmed size=2/count=12. This supports the SaveRec byte view only; it does not establish historical storage-owner identity or runtime game behavior.",
    }

    m06path = OUT / "S06_35F5_tentative_owner.c"
    m13path = OUT / "S13_384C_tentative_owner.c"
    owner_path, owner_bytes, owner_obj = compile_runtime("YDOWNER", OWNER_TEXT, ["/AL", "/Os", "/Gs"])
    consumer_path, consumer_bytes, consumer_obj = compile_runtime("YARDCRT", RUNTIME_TEXT, ["/AL", "/Os", "/Zi"])
    signed_path, signed_bytes, signed_obj = compile_runtime("YARDSIGN", SIGNED_NEGATIVE_TEXT, ["/AL", "/Os", "/Zi"])
    init_path, init_bytes, init_obj = compile_runtime("YARDINIT", INIT_OWNER_TEXT, ["/AL", "/Os", "/Gs"])
    measured_comms = {}
    for module_review_path in (OUT / "S06OWN.OBJ", OUT / "S13OWN.OBJ"):
        ob = OmfReader(communals=True).read(module_review_path.read_bytes())
        for c in ob.communals:
            if c["name"] in {"_" + n for n in ARRAYS}:
                measured_comms[c["name"]] = c
    measured_sizes = {name: row["bytes"] for name, row in ARRAYS.items()}
    for name, size in measured_sizes.items():
        comm = measured_comms.get("_" + name)
        if not comm or comm["length"] != size:
            raise AssertionError(f"whole-module candidate lacks expected {name} communal extent {size}: {comm}")
    test_comms = OmfReader(communals=True).read(owner_bytes).communals
    expected_comms = {"_" + n: ARRAYS[n]["bytes"] for n in ARRAYS}
    actual_comms = {c["name"]: c["length"] for c in test_comms}
    if actual_comms != expected_comms:
        raise AssertionError(f"test owner communal rows differ: {actual_comms}")

    tc = compiler.toolchain()
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    runner = tc["runners"]["dosbox-x"]
    msc = compiler.verify_profile("msc600ax")
    selected_tool_pins = {
        "compiler": {"profile": "msc600ax", "directory": msc["directory"],
                     "executable": msc["executable"], "flags": ["/AL", "/Os", "/Gs"],
                     "files": msc["files"]},
        "linkers": {name: {"directory": tc["linkers"][name]["directory"],
                            "executable": tc["linkers"][name]["executable"],
                            "files": tc["linkers"][name]["files"]}
                     for name in ("rtlink400", "rtlink610")},
        "runtime_libraries": runtime_rows,
        "runner": runner,
    }
    inputs = [manifest_pin, dos.pin(Path(__file__))[1], source_pins_pin, cohorts_pin, numeric_pin, overlap_pin, symbols_pin]
    for p in (m06path, m13path, owner_path, consumer_path, signed_path, init_path):
        inputs.append(dos.pin(p)[1])
    inputs.append(dos.pin(OUT / "S09CTL.OBJ")[1])
    for row in (m06, m13):
        p = ROOT / row["source"]
        inputs.append(dos.pin(p, row["source_sha256"])[1])
    for rel, digest in msc["files"].items():
        inputs.append(dos.pin(Path(msc["directory"]) / rel, digest)[1])
    inputs.append(dos.pin(Path(runner["path"]), runner["sha256"])[1])
    for row in runtime_rows:
        inputs.append(dos.pin(Path(row["path"]), row["sha256"])[1])

    specs = [
        ("positive_zero_all_elements_raw_grass_SaveRec_reset", consumer_bytes, owner_bytes, {}, "PASS"),
        ("negative_shifted_grass_base", consumer_bytes, owner_bytes, {"fd_50F6_0334": 2}, "FAIL"),
        ("negative_shifted_rain_base", consumer_bytes, owner_bytes, {"fd_50F6_38CA": 2}, "FAIL"),
        ("negative_unsigned_handle_view", signed_bytes, owner_bytes, {}, "FAIL"),
        ("negative_initialized_grass_owner", consumer_bytes, init_bytes, {}, "FAIL"),
    ]
    cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        for rel, digest in linker["files"].items():
            inputs.append(dos.pin(Path(linker["directory"]) / rel, digest)[1])
        tool_dir = compiler.pinned_tree(linker)
        for name, cbytes, obytes, alias_delta, expected in specs:
            cases.append(run_runtime_case(linker_name, name, cbytes, obytes, alias_delta, expected,
                                          tc, runtime_rows, linker, runner, tool_dir))

    report = {
        "schema": "simant-dos-yard-reset-arrays-v22-review-v1",
        "status": "RESEARCH_ONLY_NOT_ADMITTED",
        "scope": list(ARRAYS),
        "candidate_functional_source_owners": {
            "fd_50F6_0334": {"module": "S06:35F5", "function": "InitGrassMap", "source": m06["source"], "source_sha256": m06["source_sha256"], "object_sha256": m06.get("object_sha256"), "rationale": "InitGrassMap explicitly writes all twelve int slots; NotMowed consumes indexed words only after GetMowDir checks IsValidYard."},
            "fd_50F6_38CA": {"module": "S13:384C", "function": "Draw_SimYard", "source": m13["source"], "source_sha256": m13["source_sha256"], "object_sha256": m13.get("object_sha256"), "rationale": "The first animation-set path resets this entire array with 30 bytes of 0xff before DrawRain reads or writes its handles."},
            "fd_50F6_38E8": {"module": "S13:384C", "function": "Draw_SimYard", "source": m13["source"], "source_sha256": m13["source_sha256"], "object_sha256": m13.get("object_sha256"), "rationale": "The first animation-set path resets this entire array with 34 bytes of 0xff before DrawSwarm reads or writes its handles."},
            "fd_50F6_390A": {"module": "S13:384C", "function": "Draw_SimYard", "source": m13["source"], "source_sha256": m13["source_sha256"], "object_sha256": m13.get("object_sha256"), "rationale": "The first animation-set path resets this entire array with 34 bytes of 0xff before DrawSwarm reads or writes its handles."},
            "historical_COMDEF_module_identity": "NOT_CLAIMED",
        },
        "array_inventory": ARRAYS,
        "source_audit": source_audit,
        "whole_module_measurements": [review06, review13],
        "save_record_fixup_measurement": save_fixup_evidence,
        "runtime": {
            "owner_source": str(owner_path.relative_to(ROOT)),
            "owner_sha256": sha(owner_bytes),
            "owner_flags": ["/AL", "/Os", "/Gs"],
            "owner_communal_lengths": actual_comms,
            "measured_from_full_functional_owner_candidates": {name: measured_comms["_" + name] for name in ARRAYS},
            "full_game_modules_linked": False,
            "game_function_stubs": 0,
            "cases": cases,
            "all_expected_outcomes_pass": len(cases) == 10 and all(x["passed"] for x in cases),
            "fixture_scope": "A genuine MSC C main checks zero BSS fill across every element, the actual grass SaveRec row shape (size=2,count=12), raw grass bytes versus int words, and test-local reproductions of InitGrassMap and the three Draw_SimYard _fmemset payloads. It then reads/writes every word. It does not execute game functions, and the animation handles have no SaveRec row.",
        },
        "pins": {"manifest": manifest_pin,
                 "inputs": sorted({json.dumps(x, sort_keys=True): x for x in inputs}.values(),
                                  key=lambda x: json.dumps(x, sort_keys=True)),
                 "selected_tools": selected_tool_pins},
        "denied_original_input_reads": denied,
        "scope_limits": [
            "No source owner is inferred from neighboring address gaps; each extent is independently corroborated by typed source and measured COMDEF length.",
            "InitGrassMap assigns every grass slot, but malformed save-file payloads may replace it; LoadGame uses direct two-byte SaveRec reads with no source-side sanity check. IsValidYard bounds the normal NotMowed caller path; NotMowed itself has no private bounds check.",
            "Rain storage has 15 elements; DrawRain writes indices 0..13 and the mode-off cleanup scans 0..14. Slot 14 has no normal producer write in these sources.",
            "Each swarm handle array has 17 elements; DrawSwarm's producer and cleanup loops stop at indices 0..15, and index 16 is initialized but has no normal read/write path here. The count values are dynamic; source guards cap accesses at 16 entries, while malformed/loaded companion coordinate payloads are outside this extent-only contract.",
            "Draw_SimYard resets animation arrays only on the first mode<=1 call when fd_50F6_10DA is false; handles are then reused and removed per slot. It does not reset them on every invocation. SaveRec does not serialize these handles.",
            "No claim is made that the runtime fixture proves gameplay, malformed state safety, historical object identity, or absolute placement.",
        ],
    }
    report["runtime"]["all_expected_outcomes_pass"] = len(cases) == 10 and all(x["passed"] for x in cases)
    write_json(OUT / "yard-array-owner-review.json", report)
    lines = [
        "# SimYard FAR_BSS array owner review",
        "",
        "Status: `RESEARCH_ONLY_NOT_ADMITTED`. All outputs are worker scratch; canonical sources, production tools, manifest, and admission packets were not changed.",
        "",
        "The candidate source-functional owners are `InitGrassMap` in `src/S06/m35F5.c` for the grass map and `Draw_SimYard` in `src/S13/m384C.c` for the three animation arrays. This is based on each module's full-source reads/writes/reset path, not neighboring address gaps. Historical COMDEF-producing object identity, allocation ordering, and absolute placement are unclaimed.",
        "",
        "| Array | Type and extent | Source reset / view | SaveRec |",
        "|---|---:|---|---|",
        "| `fd_50F6_0334` | `int far[12]`, 24 bytes | slots 0–2 become 0; slots 3–11 become -1 | `{2,12}` at S09 line 974; 24 bytes |",
        "| `fd_50F6_38CA` | `int far[15]`, 30 bytes | first animation-set creation fills 30 bytes with `0xff` | none |",
        "| `fd_50F6_38E8` | `int far[17]`, 34 bytes | first animation-set creation fills 34 bytes with `0xff` | none |",
        "| `fd_50F6_390A` | `int far[17]`, 34 bytes | first animation-set creation fills 34 bytes with `0xff` | none |",
        "",
        f"The v22 source inventory pins and reverified all {source_audit['unique_source_path_count']} distinct sources ({source_audit['source_set_counts']['canonical_127']} canonical plus {source_audit['source_set_counts']['effective_strict_29']} effective strict sources). Its exact-symbol/ASM/numeric census reports {source_audit['numeric_scan']['exact_symbol_assembly_hit_count']} exact identifier ASM hits, {source_audit['numeric_scan']['explicit_far_segment_or_address_hit_count']} explicit far-address hits, and {source_audit['numeric_scan']['explicit_exact_hex_offset_hit_count']} exact offset-literal hits across the selected addresses. The per-array registry scan found only each exact registered base within its independently measured span; no provider span overlaps were recorded. See the artifact pins and per-member receipts in the JSON.",
        "",
        "The full S09 extern-view control matches its manifest object. Its compiled SaveRec table fixup is a 4-byte `pointer32` relocation in `UNIT7_DATA` at offset 644 (row base + 4): target `_fd_50F6_0334`, encoded addend `00000000`. This measures the source SaveRec pointer view, not the storage owner's historical identity.",
        "",
        "## Whole-module controls",
        "",
        "Fresh extern controls matched their manifest object hashes. The tentative-definition candidates preserve every compiler-emitted segment byte and definition/length/group, every public and every ordered fixup; the only scope change for each owned name is external to communal. The measured FAR COMDEF extents are 24, 30, 34, and 34 bytes. Candidate hashes and symbol-by-symbol scope changes are in `yard-array-owner-review.json`.",
        "",
        "The contrast objects independently vary short counts, byte/long widths, and initialized storage. Their OMF rows include the exact element count, element size, and total length; initialized definitions emit no communal row. These compiler controls test declaration shape only.",
        "",
        "## Startup/runtime controls",
        "",
        f"A fresh MSC 6.00AX `/AL /Os /Gs` data-only provider and a real MSC `main` consumer ran under both pinned RTLink 4.00 and 6.10. Each linker had one PASS positive (BSS zero across all elements; exact raw grass SaveRec bytes; observed grass and `-1` reset values; reads/writes of every word) and four expected FAIL controls (grass base +2, rain base +2, unsigned handle view, initialized nonzero grass). Result: {len(cases)} of {len(cases)} expected outcomes passed. Per-case Name and Value public rows, map/link/run artifact hashes, and tool/runtime pins are retained in the JSON.",
        "",
        "The runtime reproduces the source reset stores in a test-only consumer and links storage only: it executes no game routine, includes no game stub or original image bytes, and makes no gameplay or malformed-state safety claim. Normal `NotMowed` calls are gated by `IsValidYard` (x 0–11, y 0–15); `NotMowed` itself has no local bounds check, and loaded grass words can be arbitrary. Rain's normal producer uses slots 0–13 while disable cleanup checks 0–14. Swarm's normal loops guard indices at 16; slot 16 is reset but not normally read/written. Handle reset occurs only on the initial animation-set path, then values are reused and removed per slot. Companion loaded payloads and handle validity remain separate semantic questions.",
        "",
        "Rebuild with `python build/workers/dos_yard_reset_arrays_v22/yard-array-owner-probe.py`. The probe regenerates full-module controls/candidates and all runtime fixtures; it does not rely on an ignored object prerequisite.",
        "",
    ]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"all_module_checks_pass": True,
                      "module_communal_sizes": {k: v["length"] for k, v in measured_comms.items()},
                      "runtime_cases": [(x["linker"], x["case"], x["actual"], x["passed"]) for x in cases],
                      "runtime_all_pass": report["runtime"]["all_expected_outcomes_pass"],
                      "denied_original_input_reads": denied,
                      "report": str(OUT / "yard-array-owner-review.json")}, indent=2))
    return 0 if report["runtime"]["all_expected_outcomes_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
