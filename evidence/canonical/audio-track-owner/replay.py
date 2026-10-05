"""Fresh current-source game corroboration of FARSEG-2; no owner admission.

python evidence/canonical/audio-track-owner/replay.py --out build/audio-track-owner/current
All writes, including historical compiler staging, stay in a fresh directory below build/.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
MODULE = "root:284A"
SEMANTIC = "f_284A_0138"
TARGETS = ("_fd_50F6_4B30", "_fd_50F6_4B42")
EXPECTED_INITIALIZER_FAILURES = {
    "f_284A_0256", "f_284A_02E4", "f_284A_0325", "f_284A_038F"
}


def repository() -> Path:
    for path in Path(__file__).resolve().parents:
        if all((path / name).is_file() for name in
               ("src/program.json", "layout/manifest.json", "tools/compiler.py")):
            return path
    raise ValueError("cannot locate the repository from the replay's ancestors")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest(value) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": sha(raw)}


def fresh_output(root: Path, requested: Path) -> Path:
    build = (root / "build").resolve()
    if not build.is_relative_to(root.resolve()):
        raise ValueError("resolved build/ must stay inside this repository")
    path = (requested if requested.is_absolute() else root / requested).resolve()
    if path == build or not path.is_relative_to(build) or path.exists():
        raise ValueError("--out must be a fresh directory strictly below this repository's build/")
    path.mkdir(parents=True, exist_ok=False)
    return path


def variants(base: str) -> dict[str, str]:
    declarations = (
        "extern long far fd_50F6_4B42[];",
        "extern unsigned char far fd_50F6_4B30[];",
    )
    if any(base.count(declaration) != 2 for declaration in declarations):
        raise ValueError("the reviewed declaration sites changed; review before replaying")
    result = {"extern_unsized": base}
    for count in (1, 18, 19, 128):
        text = base
        for declaration in declarations:
            text = text.replace(declaration, declaration.replace("[]", f"[{count}]"))
        result[f"extern_{count}"] = text
    for count in (1, 18, 19):
        text = base
        for declaration in declarations:
            text = text.replace(declaration, declaration.removeprefix("extern ").replace(
                "[]", f"[{count}]"), 1)
        result[f"tentative_{count}"] = text
    text = base
    for declaration in declarations:
        replacement = declaration.removeprefix("extern ").replace("[];", "[18] = {0};")
        text = text.replace(declaration, replacement, 1)
    result["initialized_18"] = text
    return result


def live_projection(obj) -> dict:
    """Complete nondebug declarations, payloads, publics and ordered linker fixups."""
    names = {sd["name"] for sd in obj.segment_defs
             if str(sd.get("class", "")).upper() not in ("DEBSYM", "DEBTYP")}
    return {
        "segment_defs": [sd for sd in obj.segment_defs if sd["name"] in names],
        "segment_lengths": {name: obj.segment_lengths[name] for name in sorted(names)},
        "segment_bytes": {name: bytes(obj.segments.get(name, b"")) for name in sorted(names)},
        "groups": obj.groups,
        "publics": [p for p in obj.publics if p["segment"] in names],
        "local_publics": [p for p in obj.local_publics if p["segment"] in names],
        "ordered_fixups": [f for f in obj.linker_fixups if f["segment"] in names],
        "local_externals": obj.local_externals,
    }


def live_hashes(projection: dict) -> dict:
    result = {key: digest(value) for key, value in projection.items() if key != "segment_bytes"}
    result["segment_bytes"] = digest({name: sha(raw)
                                      for name, raw in projection["segment_bytes"].items()})
    return result


def allocation_projection(obj) -> dict:
    return {"external_names": obj.externals, "external_scopes": obj.external_scopes,
            "communals": obj.communals}


def allocation_check(name: str, obj, baseline) -> bool:
    base_names = baseline.externals
    if name == "initialized_18":
        keep = [(n, s) for n, s in zip(base_names, baseline.external_scopes) if n not in TARGETS]
        # Changed code can reorder helper EXTDEF entries. Check the complete
        # name/scope multiset; retain the ordered table separately in the receipt.
        return Counter(zip(obj.externals, obj.external_scopes)) == Counter(keep) and not obj.communals
    scopes = list(baseline.external_scopes)
    if name.startswith("tentative_"):
        count = int(name.rsplit("_", 1)[1])
        for index, target in enumerate(base_names):
            if target in TARGETS:
                scopes[index] = "communal"
        expected = {TARGETS[0]: (count, 1, count), TARGETS[1]: (count, 4, 4 * count)}
        actual = {c["name"]: (c["count"], c["element_size"], c["length"])
                  for c in obj.communals if c["kind"] == "far"}
        valid_commons = len(obj.communals) == 2 and actual == expected
    else:
        valid_commons = not obj.communals
    return obj.externals == base_names and obj.external_scopes == scopes and valid_commons


def run(root: Path, out: Path) -> dict:
    sys.path.insert(0, str(root / "tools"))
    import canonical
    import compiler
    import functions
    import match
    from omf import OmfReader

    compiler.WORK = out / "compiler"
    paths = [root / p for p in (
        "src/root/m284A.c", "src/program.json", "layout/manifest.json", "layout/toolchain.json",
        "layout/functions.json", "layout/symbols.json", "layout/oracle.lock.json",
        "assets/SIMANT.EXE",
        "tools/compiler.py", "tools/omf.py", "tools/match.py", "tools/functions.py",
        "tools/symbols.py", "tools/exe.py", "tools/canonical.py", "tools/csrc.py",
        "evidence/canonical/semantic/f_284A_0138.json",
    )]
    paths.append(Path(__file__).resolve())
    pins = {path.relative_to(root).as_posix(): identity(path) for path in paths}
    manifest = json.loads((root / "layout/manifest.json").read_text())
    record = manifest["modules"][MODULE]
    program = canonical.load()
    current = next(m for m in program["modules"] if m["key"] == MODULE)
    semantic = next(s for s in program["semantics"] if s["function"] == SEMANTIC)
    strict = json.loads((root / semantic["receipt"]).read_text())
    if record["source"] != "src/root/m284A.c" or current["source"] != record["source"]:
        raise ValueError("the current canonical module source changed")
    if any(current[key] != record[key] for key in ("profile", "flags")):
        raise ValueError("canonical and historical profile/flags disagree")
    raw_source_hash = pins[record["source"]]["sha256"]
    if raw_source_hash != current["source_sha256"] or raw_source_hash != record["source_sha256"]:
        raise ValueError("raw canonical source disagrees with the inventory/manifest source pins")
    base = (root / record["source"]).read_text(encoding="latin1")
    claims = record["claims"]
    if len(claims) != 18 or any(c["kind"] != "C" for c in claims):
        raise ValueError("expected the reviewed eighteen historical C peers")
    names = [c["name"] for c in claims] + [SEMANTIC]
    body_pins = {name: canonical.definition_sha(base, name) for name in names}
    if not (semantic["status"] == strict["status"] == "BEHAVIOR_EXACT_CONFIRMED"
            and body_pins[SEMANTIC] == semantic["definition_sha256"] == strict["definition_sha256"]):
        raise ValueError("the existing strict BEH definition/status changed")

    # Verify and retain identities of the actual selected runner/compiler files too.
    profile = compiler.verify_profile(record["profile"])
    toolchain = compiler.toolchain()
    runner = toolchain["runners"][profile["runner"]] if profile.get("runner") else toolchain["runner"]
    tool_paths = [Path(runner["path"])] + [Path(profile["directory"]) / p for p in profile["files"]]
    include = compiler.include_root(profile)
    for key in profile.get("include_files", {}):
        tool_paths.append(root / key[5:] if key.startswith("repo:") else include / key)
    tool_pins = {str(path): identity(path) for path in tool_paths}
    report = {
        "schema": "simant-current-audio-track-farseg2-replay-v1", "module": MODULE,
        "status": "IN_PROGRESS", "scope": "FARSEG-2 game corroboration only; no owner, capacity, whole historical TU exactness or new semantic status",
        "profile": record["profile"], "flags": record["flags"], "input_pins": pins,
        "selected_toolchain_pins": tool_pins, "definition_hashes": body_pins,
        "strict_beh": {"function": SEMANTIC, "status": semantic["status"],
                       "definition_sha256": body_pins[SEMANTIC], "source_unchanged_in_all_controls": True},
        "baseline_peer_extents": {c["name"]: c["size"] for c in claims}, "controls": {},
        "checks": {"raw_source_matches_inventory_and_manifest": True},
    }
    baseline = None
    base_live = None
    try:
        for name, text in variants(base).items():
            unchanged = all(canonical.definition_sha(text, n) == h for n, h in body_pins.items())
            if not unchanged:
                raise ValueError("a control changed a function definition: " + name)
            folder = out / name
            folder.mkdir()
            (folder / "module.c").write_text(text, encoding="latin1")
            compiled = compiler.compile_c(text, record["profile"], record["flags"])
            (folder / "compiler.log").write_text(compiled.log, encoding="latin1")
            if not compiled.ok:
                raise ValueError("compiler failure in " + name + ": " + compiled.log[-500:])
            (folder / "UNIT.OBJ").write_bytes(compiled.obj)
            obj = OmfReader(communals=True).read(compiled.obj)
            projection = live_projection(obj)
            if baseline is None:
                baseline, base_live = obj, projection
            failures = []
            extents = {}
            relocation_orders = Counter()
            for claim in claims:
                target = functions.get(claim["name"])
                public, location = match.public_in(obj, claim["name"])
                if location is None:
                    raise ValueError("missing accepted public " + claim["name"])
                result = match.Binder(match.Target(target["unit"], target["seg"], target["off"], target["size"]),
                                      obj, location["segment"], public, record["placements"]).bind()
                extents[claim["name"]] = result.candidate_extent_size
                relocation_orders[result.reloc_order] += 1
                if not result.exact:
                    failures.append({"claim": claim["name"], "candidate_extent": result.candidate_extent_size,
                                     "target_extent": target["size"], "reasons": result.reasons})
            live_equal = projection == base_live  # compare complete payload bytes, not hashes alone
            allocation_ok = allocation_check(name, obj, baseline)
            row = {
                "source_sha256": identity(folder / "module.c")["sha256"], "object_sha256": sha(compiled.obj),
                "live_facet_hashes": live_hashes(projection), "allocation_projection_sha256": digest(allocation_projection(obj)),
                "full_live_equal_to_baseline": live_equal, "allocation_contract": allocation_ok,
                "function_definitions_unchanged": unchanged, "exact_peer_count": 18 - len(failures),
                "relocation_order_counts": dict(relocation_orders), "failed_claims": failures,
                "scheduler_extent": extents["f_284A_038F"],
                "target_external_scopes": {n: s for n, s in zip(obj.externals, obj.external_scopes) if n in TARGETS},
                "external_table_order_equal_after_target_removal": (
                    list(zip(obj.externals, obj.external_scopes)) ==
                    [(n, s) for n, s in zip(baseline.externals, baseline.external_scopes)
                     if name != "initialized_18" or n not in TARGETS]),
                "communals": [{k: c[k] for k in ("name", "kind", "count", "element_size", "length")} for c in obj.communals],
                "live_segment_lengths": projection["segment_lengths"],
            }
            report["controls"][name] = row
            if name == "initialized_18":
                ok = (not live_equal and allocation_ok and len(failures) == 4
                      and {f["claim"] for f in failures} == EXPECTED_INITIALIZER_FAILURES
                      and extents["f_284A_038F"] == 302 and projection["segment_lengths"].get("CONST") == 18
                      and projection["segment_lengths"].get("UNIT7_DATA") == 90)
            else:
                ok = live_equal and allocation_ok and not failures and extents["f_284A_038F"] == 314
            report["checks"][name] = ok
            print(f"{name}: {row['exact_peer_count']}/18 exact peers; expected control {'PASS' if ok else 'FAIL'}", flush=True)
        report["checks"]["strict_beh_unchanged"] = True
        report["checks"]["all_nine_controls"] = len(report["controls"]) == 9
    finally:
        report["changed_input_pins"] = [p for p, old in pins.items() if identity(root / p) != old]
        report["changed_toolchain_pins"] = [p for p, old in tool_pins.items() if identity(Path(p)) != old]
        report["checks"]["input_pins_preserved"] = not report["changed_input_pins"]
        report["checks"]["toolchain_pins_preserved"] = not report["changed_toolchain_pins"]
        completed = len(report["controls"]) == 9 and report["checks"].get("strict_beh_unchanged", False)
        report["status"] = "PASS" if completed and all(report["checks"].values()) else "FAIL"
        (out / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = repository()
    out = fresh_output(root, args.out)
    report = run(root, out)
    print(f"{report['status']}: {out / 'receipt.json'}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
