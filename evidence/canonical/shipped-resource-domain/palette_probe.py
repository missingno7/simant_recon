"""Original DOS event auto-selection gate with the shipped anomalous-color object.

The actual root:218D body executes in the existing isolated Unicorn oracle.
Object lookup/lock, timing, clip and selection service calls are explicit models.
This corroborates a local control-flow premise, not a full-game DOSBox trace.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import json
import struct
import sys

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
import exe
import functions
import modctx
import resource_domains

OBJSEG = 0xa000
EVSEG = 0xa100


def noop(machine, args):
    return None


def toggle(machine, args):
    if args[0] != 0x1203:
        raise ValueError("unexpected selection object")
    at = OBJSEG * 16 + 36
    flags = machine.word(at)
    machine.set_word(at, (flags & ~4) | ((args[1] & 1) << 2))


def run_case(pair, raw, flags):
    obj = bytearray(raw)
    struct.pack_into("<H", obj, 36, flags)
    event = b.words(0, 0, 0, 0, 20, 20, 0x1203, 0)
    callbacks = {
        "win_LockWin": b.Callback(0, noop, ("ax",)),
        "win_UnlockWin": b.Callback(0, noop, ("ax",)),
        "win_ObjAddr": b.Callback(0, lambda m, a: (0, OBJSEG), ("ax",)),
        "TickCount": b.Callback(0, lambda m, a: (100, 0)),
        "win_SetObjSelectedState": b.Callback(0, toggle, ("ax", "dx")),
        "clip_Push": b.Callback(0, noop),
        "clip_Pop": b.Callback(0, noop),
        "f_1E57_0351": b.Callback(0, noop),
        "f_208F_0530": b.Callback(1, noop),
    }
    case = b.Case(label=f"palette-help-flags-{flags:04x}", args=[0, EVSEG],
        writes=[(OBJSEG * 16, bytes(obj)), (EVSEG * 16, event),
                (b.symbol_address("fd_50F6_49FA"), event),
                (b.symbol_address("fd_50F6_4A0A"), bytes(16))],
        observe=[b.Range("object", OBJSEG * 16, len(obj))],
        callbacks=callbacks, return_kind="void", callee_pop=4)
    result = b.Machine(pair).run(case)
    calls = [x for x in result["trace"] if x["name"] == "win_SetObjSelectedState"]
    return dict(flags=flags, selection_calls=[x["args"] for x in calls],
                object_unchanged=result["ranges"]["object"] == bytes(obj).hex(),
                blocks=result["blocks"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = modctx.under_build(ROOT / args.out)
    out.mkdir(parents=True, exist_ok=False)
    records = resource_domains.decoder().parse_records("HCEGANT")[1]
    raw = next(x["payload"] for x in records if (x["id"], x["kind"]) == (18, 0))
    window = resource_domains.window_domain(raw)
    anomalous = window["objects"][3]
    start = anomalous["offset"]
    obj = raw[start:start + anomalous["size"]]
    flags = anomalous["flags"]
    if flags != 0xa003 or anomalous["selected_color"] != 63:
        raise ValueError("shipped anomalous-color object changed")
    image = exe.load()
    pair = SimpleNamespace(function=functions.get("f_218D_000C"),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors},
        identity={"oracle_sha256": image.sha256})
    actual = run_case(pair, obj, flags)
    contrast = run_case(pair, obj, flags | 0x800)
    if actual["selection_calls"] or not actual["object_unchanged"]:
        raise ValueError("ordinary shipped help-object event selected the object")
    if contrast["selection_calls"] != [[0x1203, 1], [0x1203, 0]]:
        raise ValueError("auto-selection-bit contrast did not exercise the guarded route")
    report = dict(schema="simant-palette-selection-gate-oracle-v1", status="PASS",
        oracle_sha256=image.sha256, original_function="f_218D_000C", actual=actual, contrast=contrast,
        model_boundaries=["object lookup/lock", "TickCount", "clip push/pop/reset", "selection primitive", "five-tick wait"],
        inputs={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
            ("src/root/m218D.c", "src/root/m22BF.c", "assets/HCEGANT.DAT", "assets/HCEGANT.NDX", "tools/behavior.py")},
        scope="Original event body runs with the actual shipped object; one-bit altered object is a negative premise contrast. No full-game or indirect-call exclusion.")
    (out / "palette.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
