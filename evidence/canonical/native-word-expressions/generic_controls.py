from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import hashlib
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
HERE = Path(__file__).parent
sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Run proof controls without Python -O')
sys.path.insert(0, str(ROOT / "portable"))
from canonical_native_abi.word_islands import convert, literal_type
from canonical_native_abi import scalar

parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path)
args = parser.parse_args()
OUT = (args.out or ROOT / "build" / ("native-integer-generic-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))).resolve()
OUT.relative_to(ROOT / "build")
if OUT.exists():
    raise ValueError("fresh --out required")
OUT.mkdir(parents=True)


def expression(text):
    source, receipt = convert("result = " + text + ";")
    return scalar.convert(source[len("result = "):-1]), receipt


controls = {}
for source in (
    "(unsigned)a + 2L <= (unsigned)b",
    "(unsigned)a + 2.0 <= (unsigned)b",
    "(unsigned)a + unknown <= (unsigned)b",
    "(unsigned)a * 2 <= (unsigned)b",
    "(unsigned)a << 2 <= (unsigned)b",
    "(int)a + 2 < (int)b",
    "(unsigned char)a + 2 < (unsigned char)b",
    "(unsigned near)a + 2 < (unsigned)b",
    "(unsigned)a >= 0",
    "#define ADD(x) ((unsigned)(x) + 2)\n",
    "_asm { mov ax,2 }\n",
):
    output, receipt = convert(source)
    assert output == source and not receipt["operators"], (source, output)
    controls[source] = "UNCHANGED_UNSUPPORTED_OR_OUTSIDE_WORD_CLASS"

# Operator precedence negative: literal 2 is the RHS of addition, never an
# independent comparison lhs. The earlier naive all-token-start scan failed it.
output, receipt = convert("if ((unsigned)a + 2 <= (unsigned)b) use();")
assert len(receipt["operators"]) == 1 and receipt["operators"][0]["source"] == "(unsigned)a + 2"
controls["precedence_rhs_is_not_independent_comparison"] = "PASS"

for literal, typ in (("32767", "s16"), ("32768", "s32"), ("0x8000", "u16"),
                     ("0xffff", "u16"), ("0x10000", "s32"), ("0100000", "u16"),
                     ("65535U", "u16"), ("65536U", "u32"), ("0xffffL", "s32"),
                     ("0xffffffff", "u32"), ("1.0", None)):
    assert literal_type(literal)[0] == typ
controls["MSC16_literal_type_matrix"] = "PASS"

expressions = {
    "add2": "(unsigned)a + 2",
    "add256": "(unsigned)a + 0x100",
    "sub2": "(unsigned)a - 2",
    "chain": "((unsigned)a + 2) - 0x100",
    "negative_add": "(unsigned)a + -1",
    "signed_compare": "(unsigned)a < (int)b",
    "large_hex_compare": "(int)b == 0xffff",
    "large_decimal_contrast": "(unsigned)a + 32768",
}
native_expressions = {name: expression(text)[0] for name, text in expressions.items()}
assert not expression(expressions["large_decimal_contrast"])[1]["operators"]

probe = """#include <stdint.h>
#include <stdio.h>
static uint16_t calls;
static uint16_t next(void) { ++calls; return 65535; }
int main(void) {
    uint32_t i;
    int16_t a, b;
    for (i = 0; i < 65536; ++i) {
        a = (int16_t)i;
        b = (int16_t)(65535 - i);
"""
reference = {"add2": "(uint16_t)(i + 2)", "add256": "(uint16_t)(i + 256)",
             "sub2": "(uint16_t)(i - 2)", "chain": "(uint16_t)(i + 2 - 256)",
             "negative_add": "(uint16_t)(i - 1)", "signed_compare": "i < (uint16_t)b",
             "large_hex_compare": "(uint16_t)b == 65535",
             "large_decimal_contrast": "i + 32768"}
for name in expressions:
    probe += f"        if (({native_expressions[name]}) != ({reference[name]})) return {len(probe) % 100 + 2};\n"
probe += "    }\n"
side_effect_source = """if (((unsigned)next() + 2) != 1 || calls != 1) return 101;
if (0 && (unsigned)next() + 2 < 3) return 102;
if (calls != 1) return 103;
if (((unsigned)next() + 2) - 0x100 != 0xff01 || calls != 2) return 104;
"""
side_effect_output, side_receipt = convert(side_effect_source)
probe += scalar.convert(side_effect_output)
probe += '    puts("524288 exhaustive expression rows and single-evaluation/short-circuit controls passed");\n    return 0;\n}\n'
path = OUT / "expression_probe.c"
path.write_text(probe)
gcc = "C:/msys64/mingw64/bin/gcc.exe"
for optimize in ("-O0", "-O2"):
    target = OUT / ("expression_probe_" + optimize[1:] + ".exe")
    result = subprocess.run([gcc, "-std=c11", "-fsigned-char", "-Wall", "-Wextra", optimize, str(path), "-o", str(target)], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(target)], capture_output=True, text=True, cwd=HERE, timeout=10)
    assert result.returncode == 0, (optimize, result.returncode, result.stdout, result.stderr)
    controls[optimize] = result.stdout.strip()
receipt = {"schema": "word-islands-generic-controls-v1", "passed": True, "controls": controls,
           "expressions": expressions, "generated_expressions": native_expressions,
           "exhaustive_rows_per_optimization": 65536 * len(expressions),
           "side_effect_conversion": side_receipt}
receipt['input_and_output_pins'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (Path(__file__), ROOT / 'portable/canonical_native_abi/word_islands.py',
              ROOT / 'portable/canonical_native_abi/tokenizer.py', ROOT / 'portable/canonical_native_abi/scalar.py',
              Path(gcc), path, OUT / 'expression_probe_O0.exe', OUT / 'expression_probe_O2.exe')}
(OUT / "generic-controls.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"passed": True, "controls": len(controls), "exhaustive_rows_per_optimization": receipt["exhaustive_rows_per_optimization"]}, indent=2))
