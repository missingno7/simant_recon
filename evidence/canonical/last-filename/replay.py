"""Bounded ownership proof for the canonical last selected filename."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
sys.dont_write_bytecode = True
import canonical
import csrc


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def significant_function(path: str, name: str) -> str:
    text = (ROOT / path).read_text(encoding="latin1")
    fn = csrc.Source(text).function(name)
    return " ".join(t.text for t in csrc.tokenize(text[fn.head_s:fn.body.e])
                    if t.kind not in {"ws", "nl", "cmt"})


def inventory(program_override=None, source_overrides=None):
    program = program_override or canonical.load()
    source_overrides = source_overrides or {}
    texts = {}
    for module in program["modules"]:
        raw = source_overrides.get(module["source"])
        if raw is None:
            raw = (ROOT / module["source"]).read_bytes()
        assert sha(raw) == module["source_sha256"]
        texts[module["source"]] = raw.decode("latin1")
    return texts, program


def source_census(texts: dict[str, str]) -> list[list[object]]:
    rows = []
    for path, text in sorted(texts.items()):
        if path.endswith(".asm"):
            for line_no, line in enumerate(text.splitlines(), 1):
                code = line.split(";", 1)[0]
                if re.search(r"(?<![A-Za-z0-9_])_?fd_50F6_3862(?![A-Za-z0-9_])", code):
                    rows.append([path, line_no, code.strip()])
        else:
            for token in csrc.tokenize(text):
                if token.kind == "id" and token.text == "fd_50F6_3862":
                    rows.append([path, text.count("\n", 0, token.s) + 1, token.text])
    return rows


def collect(program_override=None, source_overrides=None) -> dict:
    texts, program = inventory(program_override, source_overrides)
    modules = {m["key"]: m for m in program["modules"]}
    provider = modules["source-owned:last-filename"]
    contract = provider["storage_contract"]
    expected = [{"name": "_fd_50F6_3862", "kind": "far", "length": 100,
                 "count": 100, "element_size": 1}]
    assert contract["communals"] == expected
    source = texts[provider["source"]]
    assert " ".join(t.text for t in csrc.tokenize(source)
                    if t.kind not in {"ws", "nl", "cmt"}) == \
           "char far fd_50F6_3862 [ 100 ] ;"

    load = significant_function("src/S09/m35F5.c", "LoadGame")
    save = significant_function("src/S09/m35F5.c", "o09_35F5_0188")
    select = significant_function("src/S09/m35F5.c", "o09_35F5_03C6")
    extension = significant_function("src/S09/m35F5.c", "o09_35F5_0D2B")
    assert "char name [ 100 ]" in load and "char name [ 100 ]" in save
    whole_s09 = " ".join(t.text for t in csrc.tokenize(texts["src/S09/m35F5.c"])
                         if t.kind not in {"ws", "nl", "cmt"})
    assert "char path [ 67 ]" in select and "static char lastDir [ 67 ]" in whole_s09
    assert load.count("_fstrcpy ( fd_50F6_3862 , name )") == 1
    assert save.count("_fstrcpy ( fd_50F6_3862 , name )") == 2
    assert save.count("_fstrcpy ( name , fd_50F6_3862 )") == 1
    assert save.count("* fd_50F6_3862 = 0") == 2
    assert "for ( i = 0 ; i < 8 ; i ++ )" in extension
    assert "if ( * name == '.' || * name == 0 ) break" in extension
    assert "_fstrcpy ( name , \".ant\" )" in extension

    boundary = json.loads((ROOT / "evidence/canonical/filename-domain/receipt.json").read_text())
    assert boundary["status"] == "POSITIVE_AND_NEGATIVE_CONFIRMED"
    assert "after-slash=66 requires=67 fits67=1" in boundary["run_log"]
    assert "after-slash=68 requires=69 fits67=0" in boundary["run_log"]
    census = source_census(texts)
    assert {row[0] for row in census} == {"src/S09/m35F5.c", "src/state/last-filename.c"}

    return {
        "schema": "simant-last-filename-domain-v1",
        "scope": "Defined successful S09 filename copies through 100-byte automatic objects; selector local overflow remains an explicit semantic gate.",
        "program_sha256": sha(((json.dumps(program, indent=2) + "\n").encode())
                              if program_override is not None
                              else (ROOT / "src/program.json").read_bytes()),
        "function_definition_sha256": {
            "LoadGame": sha(load.encode()),
            "o09_35F5_0188": sha(save.encode()),
            "o09_35F5_03C6": sha(select.encode()),
            "o09_35F5_0D2B": sha(extension.encode()),
        },
        "source_census": {"rows": census,
                          "sha256": sha(json.dumps(census, separators=(",", ":")).encode())},
        "owner": {"characters": 99, "terminator_bytes": 1, "extent_bytes": 100,
                  "initialization": "MSC far communal zero initialization"},
        "fixed_objects": {"caller_name_bytes": 100, "selector_path_bytes": 67,
                          "selector_lastDir_bytes": 67, "selector_buf_bytes": 80},
        "safe_selector_result": {"path_with_separator_bytes": 67,
                                 "maximum_leaf_characters": 12,
                                 "returned_name_bytes": 79},
        "path_contrast": {"positive_required_bytes": 67,
                          "negative_required_bytes": 69,
                          "negative_gate": "filename-selector-local-capacity",
                          "receipt_sha256": sha((ROOT / "evidence/canonical/filename-domain/receipt.json").read_bytes())},
        "historical_extent": "UNCLAIMED",
    }


def check() -> dict:
    actual = collect()
    expected = json.loads((Path(__file__).parent / "facts.json").read_text())
    if actual != expected:
        raise ValueError("last-filename proof differs from reviewed facts")
    return actual


if __name__ == "__main__":
    check()
    print("PASS: 100-byte last-filename owner; local selector overflow retained")
