"""Default-VGA exclusion of the monochrome pattern producer and consumers.

The one-byte provider checked by this proof is a linkage object for the supported
domain.  It is not a recovered DOS allocation and does not support odd modes.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import importlib.util
import json
import re
import sys

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
import canonical
import csrc
import exe
import functions
import context


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def significant(text):
    return " ".join(t.text for t in csrc.tokenize(text)
                    if t.kind not in {"ws", "nl", "cmt"})


def definition(path, name):
    text = (ROOT / path).read_text(encoding="latin1")
    function = csrc.Source(text).function(name)
    return significant(text[function.head_s:function.body.e])


def caller_names(name):
    function = functions.get(name)
    key = "%s:%05X" % (function["unit"], function["seg"] * 16 + function["off"])
    edges = context.inventory_edges()[key]["callers"]
    names = {"%s:%05X" % (row["unit"], row["seg"] * 16 + row["off"]):
             functions.name_of(row["unit"], row["seg"], row["off"])
             for row in functions.table()["functions"]}
    return sorted(names.get(edge, edge) for edge in edges)


def source_census(texts):
    names = {"g_8ED8", "LoadMonoPats", "o01_328E_000A",
             "o01_328E_009D", "o01_328E_012C", "o01_328E_01D5",
             "fd_50F6_38B8", "fd_50F6_38BC"}
    rows = []
    for path, text in sorted(texts.items()):
        if path.endswith(".asm"):
            for line_number, line in enumerate(text.splitlines(), 1):
                code = line.split(";", 1)[0]
                for token in re.findall(r"[A-Za-z_@][A-Za-z_0-9]*", code):
                    if token.lstrip("_@") in names:
                        rows.append([path, line_number, token, code.strip()])
        else:
            for token in csrc.tokenize(text):
                if token.kind == "id" and token.text in names:
                    line_number = text.count("\n", 0, token.s) + 1
                    rows.append([path, line_number, token.text])
    return rows


class Boundary(Exception):
    pass


def mini_control(mode):
    image = exe.load()
    pair = SimpleNamespace(function=functions.get("Mini_MakeTable"),
                           vectors={exe.MANAGER_SEG * 16 + v.offset: v
                                    for v in image.vectors})
    machine = b.Machine(pair)

    def stop(cpu, args):
        raise Boundary()

    callbacks = {
        "o00_3126_06A3": b.Callback(4, stop),
        "o00_3126_04D8": b.Callback(4, stop),
        "o03_3253_002F": b.Callback(5, stop),
        "o01_328E_012C": b.Callback(5, stop),
        "o01_328E_01D5": b.Callback(5, stop),
    }
    case = b.Case("mini-mode", args=[0, 0x7000, 0, 0x7100, 6],
                  return_kind="void", callbacks=callbacks,
                  writes=[(b.symbol_address("g_5A97"), bytes([mode])),
                          (b.symbol_address("fd_50F6_3854"), b.words(0x40))])
    try:
        machine.run(case)
    except b.ExecutionError as exc:
        if not isinstance(exc.__cause__, Boundary):
            raise
    else:
        raise AssertionError("Mini_MakeTable missed renderer boundary")
    calls = [row["name"] for row in machine.raw_trace if row["name"] in callbacks]
    assert len(calls) == 1
    return {"mode": mode, "selected": calls[0]}


def collect():
    icon = load("mono_vga_base", "evidence/canonical/icon-handle-view/vga_probe.py")
    vga = icon.check()
    assert vga["config"]["ReadConfig_g_5A97"] == 8
    texts, program, _ = icon.inventory()

    main = definition("src/root/m15F8.c", "main")
    init = definition("src/S12/m384C.c", "InitMapFunctions")
    mini = definition("src/S04/m35F5.c", "Mini_MakeTable")
    assert "if ( g_5A97 & 1 ) LoadMonoPats ( ) ;" in main
    assert "case 8 : fd_50F6_3856 = 4 ; fd_50F6_3858 = 4 ; fd_50F6_38B8 = o00_3126_0000 ; fd_50F6_38BC = o00_3126_0137 ;" in init
    assert "case 8 : if ( fd_50F6_3854 == 0x40 ) o00_3126_06A3 ( src , dst ) ; else o00_3126_04D8 ( src , dst ) ;" in mini
    assert caller_names("LoadMonoPats") == ["main"]
    assert caller_names("o01_328E_012C") == ["Mini_MakeTable"]
    assert caller_names("o01_328E_01D5") == ["Mini_MakeTable"]

    modules = {item["key"]: item for item in program["modules"]}
    provider = modules["source-owned:mono-pattern-vga-linkage"]
    contract = provider["storage_contract"]
    assert provider["source"] == "src/state/mono-pattern-vga-linkage.c"
    assert contract["communals"] == [{"name": "_g_8ED8", "kind": "near", "length": 1}]

    controls = [mini_control(8), mini_control(7)]
    assert controls == [
        {"mode": 8, "selected": "o00_3126_06A3"},
        {"mode": 7, "selected": "o01_328E_01D5"},
    ]
    rows = source_census(texts)
    return {
        "schema": "simant-monochrome-vga-exclusion-v1",
        "scope": "Locked shipped VGA8 successful lifetime only; no odd-mode pattern allocation, resource, caller-state or behavior claim.",
        "oracle_sha256": exe.load().sha256,
        "vga_facts_sha256": sha((ROOT / "evidence/canonical/icon-handle-view/vga-facts.json").read_bytes()),
        "program_sha256": sha((ROOT / "src/program.json").read_bytes()),
        "function_definition_sha256": {
            "main": sha(main.encode()),
            "InitMapFunctions": sha(init.encode()),
            "Mini_MakeTable": sha(mini.encode()),
        },
        "original_callers": {
            "LoadMonoPats": caller_names("LoadMonoPats"),
            "o01_328E_012C": caller_names("o01_328E_012C"),
            "o01_328E_01D5": caller_names("o01_328E_01D5"),
        },
        "source_census": {
            "rows": rows,
            "sha256": sha(json.dumps(rows, separators=(",", ":")).encode()),
        },
        "original_mini_controls": controls,
        "supported_access_bytes": 0,
        "linkage_owner_bytes": 1,
        "historical_extent": "UNCLAIMED",
    }


def check():
    actual = collect()
    expected = json.loads((Path(__file__).parent / "mode-facts.json").read_text())
    if actual != expected:
        raise ValueError("default VGA monochrome proof differs from reviewed facts")
    return actual


if __name__ == "__main__":
    result = check()
    print("PASS: VGA8 excludes monochrome pattern accesses; odd-mode control retained")
