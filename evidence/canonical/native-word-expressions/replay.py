from pathlib import Path
from types import SimpleNamespace
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
HERE = Path(__file__).parent
sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Run proof controls without Python -O')
sys.path.insert(0, str(ROOT / "portable"))
sys.path.insert(0, str(ROOT / "tools"))
from canonical_native_abi import word_islands
from coff_peers import compare as compare_peers
from canonical_native_abi.lexical import function_heads
import behavior as b
import exe
import functions


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(argv, label):
    result = subprocess.run([str(x) for x in argv], cwd=ROOT, capture_output=True, text=True, timeout=45)
    (OUT / (label + ".log")).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(label + " failed\n" + result.stderr[-4000:])
    return result


parser = argparse.ArgumentParser()
parser.add_argument("--build", type=Path, required=True)
parser.add_argument("--out", type=Path)
args = parser.parse_args()
BUILD = args.build.resolve()
OUT = (args.out or ROOT / "build" / ("native-integer-probe-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))).resolve()
OUT.relative_to(ROOT / "build")
if OUT.exists():
    raise ValueError("fresh --out required")
OUT.mkdir(parents=True)
report = json.loads((BUILD / "report.json").read_text())
if not report.get("passed") or not report["input_stability"]["at_end"]:
    raise ValueError("passed stable native build required")
for rel, pin in report['input_pins'].items():
    if sha(ROOT / rel) != pin:
        raise ValueError("native build relevant input differs: " + rel)
row = next(r for r in report["canonical_TUs"] if r["module"] == "root:22BF")
base = row["compile"]["command"]
flags = base[1:base.index("-c")] + ["-O0", "-ffunction-sections", "-fdata-sections"]
gcc = base[0]
original = Path(row["generated"])
source = original.read_text(encoding="latin1")
patterns = [("(uint16_t)win + 0x100", "((uint16_t)((uint16_t)win + 0x100))"),
            ("(uint16_t)win + 2", "((uint16_t)((uint16_t)win + 2))")]
corrected_counts = [source.count(corrected) for _, corrected in patterns]
conversion = row.get("word_expressions")
if not isinstance(conversion, dict) or len(conversion.get("operators", [])) != 2:
    raise ValueError("current root:22BF per-TU word_expressions receipt with exactly two operators required")
if any(op.get("operator") != "+" or op.get("action") != "word-additive-result"
       for op in conversion["operators"]):
    raise ValueError("current reviewed additive operator class differs")
if corrected_counts != [1, 1]:
    raise ValueError("reviewed current corrected whole-TU integer anchors differ")
# The installed builder's actual whole generated TU is the positive lane.
# Exact reviewed two-operator inversions create only the test negative lane.
new_source = source
old_source = source
for old, corrected in patterns:
    old_source = old_source.replace(corrected, old, 1)
new = OUT / "native-whole-22BF.c"
new.write_text(new_source, encoding="latin1")
old = OUT / "negative-whole-22BF.c"
old.write_text(old_source, encoding="latin1")
objects = {}
execution_objects = {}
for label, path in (("old", old), ("new", new)):
    obj = OUT / (label + "-whole.o")
    command([gcc, *flags, "-c", path, "-o", obj], label + "-whole-compile")
    objects[label] = obj
    # The UI-open observer is defined in the same TU. COFF calls its section
    # directly, so the native lane must explicitly exclude this observer body,
    # as the DOS lane excludes its entry below. Target and 45 other peers remain
    # unmodified in this execution-only complete-TU derivative.
    execution_source = path.read_text(encoding="latin1")
    observer = next(f for f in function_heads(execution_source) if f["name"] == "win_IsWinOpen")
    brace = execution_source.index("{", observer["start"])
    execution_source = (execution_source[:brace] + "{ return __wrap_win_IsWinOpen(win); }" + execution_source[observer["end"]:])
    execution_source = "extern int16_t __wrap_win_IsWinOpen(int16_t);\n" + execution_source
    harness_source = OUT / (label + "-observer-whole.c")
    harness_source.write_text('#include <stdint.h>\n' + execution_source, encoding="latin1")
    execution_obj = OUT / (label + "-observer-whole.o")
    command([gcc, *flags, "-c", harness_source, "-o", execution_obj], label + "-observer-whole-compile")
    execution_objects[label] = execution_obj
    # PE keeps globally visible functions. Reuse the current proven complete
    # object inventory, substituting this whole TU and this boundary driver.
    app = report["application_link"]["command"]
    app_source = next(i for i, arg in enumerate(app) if arg.endswith("application.c"))
    link = app[:app_source] + [str(HERE / "prox_driver.c")] + app[app_source + 1:]
    old_obj = row["object"]
    link = [str(execution_obj) if arg == old_obj else arg for arg in link]
    link[link.index("-o") + 1] = str(OUT / (label + ".exe"))
    wrapped = ["win_Open", "_win_SetProxItem", "ButtonHeldInit", "win_IsWinOpen",
               "ButtonHeld", "win_GetProxEvent", "win_GetEvent", "win_Close"]
    link.extend("-Wl,--wrap=" + name for name in wrapped)
    command(link, label + "-link")

wins = [0, 1, 0x0100, 0x7f00, 0x7fff, 0x8000, 0xfeff, 0xff00, 0xff01, 0xff7f, 0xfffe, 0xffff]
cases = sorted({(w, e & 0xffff) for w in wins for e in
                (0, 1, w - 1, w, w + 1, w + 2, w + 3, w + 0xff, w + 0x100, 0xfffe, 0xffff)})
input_text = "".join(f"{w} {e}\n" for w, e in cases)
native = {}
for label in objects:
    native_env = dict(os.environ)
    native_env["PATH"] = str(BUILD) + ";" + native_env.get("PATH", "")
    result = subprocess.run([str(OUT / (label + ".exe"))], input=input_text, cwd=OUT, env=native_env, text=True, capture_output=True, timeout=20)
    if result.returncode:
        raise RuntimeError(label + " execution failed " + str(result.returncode) + result.stderr)
    native[label] = {tuple(row[:2]): tuple(row[2:]) for row in
                     (list(map(int, line.split())) for line in result.stdout.splitlines())}
    if set(native[label]) != set(cases):
        raise RuntimeError("native output case inventory differs")

pair = SimpleNamespace(function=functions.get("win_DoProxMenu"),
                       vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors})
machine = b.Machine(pair)
results = []
for win, ev in cases:
    def is_open(m, args):
        m.state["checks"] = m.state.get("checks", 0) + 1
        return int(m.state["checks"] == 1)
    callbacks = {
        "win_Open": b.Callback(3, lambda m, a: None),
        "ButtonHeldInit": b.Callback(0, lambda m, a: None),
        "win_IsWinOpen": b.Callback(0, is_open, register_args=("ax",)),
        "ButtonHeld": b.Callback(0, lambda m, a: 0),
        "win_GetProxEvent": b.Callback(0, lambda m, a: ev),
        "win_Close": b.Callback(0, lambda m, a: None, register_args=("ax",)),
    }
    case = b.Case(label=f"prox/{win:04x}/{ev:04x}", args=[win, 0xffff, 0, 0], callbacks=callbacks)
    dos = machine.run(case)
    expected = dos["return"], dos["state"]["checks"]
    results.append({"win": win, "event": ev, "dos": expected,
                    "old_native": native["old"][(win, ev)], "new_native": native["new"][(win, ev)],
                    "dos_trace": [r["name"] for r in dos["trace"]]})
    if native["new"][(win, ev)] != expected:
        raise AssertionError(results[-1])

negative = [r for r in results if r["old_native"] != r["dos"]]
if not negative:
    raise AssertionError("old native negative control did not distinguish")
for rel, pin in report['input_pins'].items():
    if sha(ROOT / rel) != pin:
        raise ValueError('native build input drift during proof: ' + rel)
receipt = {"schema": "closed-word-islands-probe-v1", "passed": True,
           "verified_build_input_count": len(report['input_pins']),
           "oracle_sha256": exe.load().sha256,
           "cases": results, "old_native_differences": len(negative),
           "negative_witness": negative[0], "conversion": conversion,
           "negative_mutation": {"method": "Actual current generated whole TU is positive; negative removes exactly two reviewed word-result casts in win_DoProxMenu.",
                                 "operators": [{"old": old, "corrected": corrected} for old, corrected in patterns]},
           "input_pins": {str(p.relative_to(ROOT)): sha(p) for p in
                          (ROOT / "src/root/m22BF.c", original, ROOT / "portable/canonical_native_abi/scalar.py",
                           Path(word_islands.__file__), HERE / "prox_driver.c", Path(__file__), BUILD / "report.json")},
           "whole_tu": {"source": "src/root/m22BF.c",
                        "changed_operators": len(conversion["operators"]),
                        "old_object_sha256": sha(objects["old"]), "new_object_sha256": sha(objects["new"]),
                        "peer_and_storage_control": compare_peers(objects["old"], objects["new"])},
           "domain": "All word-valued win/event fixtures under explicit open/check/event/close boundary callbacks. The win_DoProxMenu body is the complete converted canonical TU compiled at O0. No shipped-window reachability claim.",
           "boundary": "Native execution-only whole-TU derivatives replace only the win_IsWinOpen observer body with its boundary callback, because same-TU COFF section calls bypass GNU --wrap. DOS intercepts that original entry. Both report open on the first check and closed thereafter. Other listed host/UI boundaries use linker wrappers with the same fixed results. The actual old/new complete TUs compile separately and all 46 peer functions plus storage have a full read-only COFF equality control. The target body is never replaced or extracted."}
(OUT / "probe-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"passed": True, "cases": len(results), "old_native_differences": len(negative), "negative_witness": negative[0]}, indent=2))
