"""Strict mechanical adapter for the DOS root:0093 RNG translation unit.

This converts the nine original inline-assembly RNG bodies and the BIOS-style
absolute read in GetRRandSeed. Other function bodies remain source-derived;
only their target-width C types and the explicit DOS CRT symbol namespace are
adapted for the host compiler.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

SOURCE_SHA256 = "dd5a593457dd72297e41dabef1e00e0be2fbca53d7586adc2c47812e960297af"
SOURCE_PATH = "src/root/m0093.c"

MASKS = (
    ("SRand2", "d2", "1", 0x0001),
    ("SRand4", "d4", "3", 0x0003),
    ("SRand8", "d8", "7", 0x0007),
    ("SRand16", "d16", "0fh", 0x000F),
    ("SRand32", "d32", "1fh", 0x001F),
    ("SRand64", "d64", "3fh", 0x003F),
    ("SRand128", "d128", "7fh", 0x007F),
    ("SRand256", "d256", "0ffh", 0x00FF),
)

SRAND1_RE = re.compile(
    r"int far SRand1\(unsigned int range\)\s*\{.*?^\s*return result;\s*\}",
    re.MULTILINE | re.DOTALL,
)
MASK_MACRO_RE = re.compile(
    r"^#define SRAND_MASK\(name, label, mask\).*?^SRAND_MASK\(SRand256, d256, 0ffh\)\s*$",
    re.MULTILINE | re.DOTALL,
)
GET_R_SEED_RE = re.compile(
    r"unsigned long far GetRRandSeed\(void\)\s*\{\s*"
    r"return \*\(unsigned long far \*\)0x046C0000L;\s*\}",
)

_ASM_FUNCTION_NAMES = ("SRand1", *(row[0] for row in MASKS))
_C_BODY_NAMES = (
    "SGIRand", "SGRand", "SGSRand", "SetSRandSeed", "GetSRandSeed",
    "SetRRandSeed", "GetRRandSeed", "SeedSRand", "SeedRRand", "RRand",
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*\([^;]*\)\s*\{{", source, re.DOTALL)
    if not match:
        raise ValueError(f"required function body not found: {name}")
    start = source.index("{", match.start())
    depth = 0
    i = start
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == "/" and nxt == "*":
                state = "comment"; i += 2; continue
            if ch == "/" and nxt == "/":
                state = "line"; i += 2; continue
            if ch == '"': state = "string"
            elif ch == "'": state = "char"
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[start:i + 1]
        elif state == "comment":
            if ch == "*" and nxt == "/": state = "code"; i += 2; continue
        elif state == "line":
            if ch == "\n": state = "code"
        elif state in ("string", "char"):
            if ch == "\\": i += 2; continue
            if (state == "string" and ch == '"') or (state == "char" and ch == "'"):
                state = "code"
        i += 1
    raise ValueError(f"unterminated function body: {name}")


def _type_lower(text: str) -> str:
    text = re.sub(r"\bunsigned\s+long\b", "uint32_t", text)
    text = re.sub(r"\bunsigned\s+int\b", "uint16_t", text)
    text = re.sub(r"\bint\b", "int16_t", text)
    return re.sub(r"\bfar\b", "", text)


def _mask_function(name: str, mask_literal: str) -> str:
    suffix = mask_literal.lower().replace("h", "")
    value = int(suffix, 16) if "h" in mask_literal.lower() else int(mask_literal, 10)
    return (
        f"int16_t {name}(void)\n{{\n"
        f"    uint16_t ax = rng_advance_seed();\n"
        f"    return (int16_t)(ax & UINT16_C(0x{value:04x}));\n"
        f"}}"
    )


def adapt(source: str) -> tuple[str, dict[str, Any]]:
    """Return host-normalized source and an auditable source-transformation ledger.

    Reject source drift instead of attempting a fuzzy rewrite. The caller owns
    platform leaves `TickCount`, `dos_host_read_u32`, `dos_host_divide_fault`,
    `dos_crt_srand`, and `dos_crt_rand`.
    """
    source_sha = _sha(source)
    if source_sha != SOURCE_SHA256:
        raise ValueError(f"unexpected {SOURCE_PATH} bytes: {source_sha}")
    if source.count("_asm") != 8:
        raise ValueError("expected one SRand1 asm block and seven macro statements expanded by eight invocations")
    if len(re.findall(r"^SRAND_MASK\(SRand(?:2|4|8|16|32|64|128|256),", source, re.MULTILINE)) != 8:
        raise ValueError("expected exactly eight SRAND_MASK instantiations")

    original_bodies = {name: _function_body(source, name) for name in _C_BODY_NAMES}
    sr1_match = SRAND1_RE.search(source)
    macro_match = MASK_MACRO_RE.search(source)
    get_r_match = GET_R_SEED_RE.search(source)
    if not sr1_match or not macro_match or not get_r_match:
        raise ValueError("expected original inline asm/GetRRandSeed spellings not found")
    sr1_original, macro_original, get_r_original = sr1_match.group(0), macro_match.group(0), get_r_match.group(0)

    sr1_c = """int16_t SRand1(uint16_t range)
{
    uint16_t ax = rng_advance_seed();
    if (range == 0)
        dos_host_divide_fault();
    return (int16_t)(ax % range);
}"""
    mask_c = "\n\n".join(_mask_function(name, literal) for name, _label, literal, _value in MASKS)
    get_r_c = "uint32_t GetRRandSeed(void)\n{\n    return dos_host_read_u32(UINT32_C(0x46c0));\n}"

    output = source[:sr1_match.start()] + sr1_c + source[sr1_match.end():]
    macro_match2 = MASK_MACRO_RE.search(output)
    if not macro_match2:
        raise AssertionError("macro range moved or changed after SRand1 replacement")
    output = output[:macro_match2.start()] + mask_c + output[macro_match2.end():]
    get_r_match2 = GET_R_SEED_RE.search(output)
    if not get_r_match2:
        raise AssertionError("GetRRandSeed body moved or changed after asm replacement")
    output = output[:get_r_match2.start()] + get_r_c + output[get_r_match2.end():]
    output = _type_lower(output)
    output = re.sub(r"(?m)^extern void\s+srand\(", "extern void dos_crt_srand(", output)
    output = re.sub(r"(?m)^extern int16_t\s+rand\(", "extern int16_t dos_crt_rand(", output)
    seed_rrand = _function_body(output, "SeedRRand")
    output = output.replace(seed_rrand, re.sub(r"\bsrand\s*\(", "dos_crt_srand(",
                                               re.sub(r"\brand\s*\(", "dos_crt_rand(", seed_rrand)), 1)
    rrand_body = _function_body(output, "RRand")
    output = output.replace(rrand_body, re.sub(r"\brand\s*\(", "dos_crt_rand(", rrand_body), 1)

    # Private seed remains one private module-owned word. The target's int is
    # 16 bits; making that width explicit avoids host-int widening.
    output = re.sub(r"static\s+uint16_t\s+seed\s*;", "static uint16_t seed;", output, count=1)
    if not re.search(r"static\s+uint16_t\s+seed\s*;", output):
        raise AssertionError("private seed declaration was not preserved as one uint16_t owner")

    declarations = """#include <stdint.h>

extern uint32_t dos_host_read_u32(uint32_t physical_address);
_Noreturn void dos_host_divide_fault(void);
extern void dos_crt_srand(uint16_t seed_value);
extern int16_t dos_crt_rand(void);

"""
    helper = """static uint16_t rng_advance_seed(void)
{
    uint16_t ax = seed;
    uint16_t carry = (uint16_t)(ax & UINT16_C(0x8000));
    ax = (uint16_t)(ax << 1);
    if (carry != 0)
        ax ^= UINT16_C(0x1bf5);
    seed = ax;
    return ax;
}
"""
    # Place host interfaces before the source declarations and the seed
    # recurrence directly after its one private source-owned seed word.
    output = declarations + output
    seed_decl = "static uint16_t seed;"
    if output.count(seed_decl) != 1:
        raise AssertionError("expected exactly one target-width private seed declaration")
    output = output.replace(seed_decl, seed_decl + "\n\n" + helper, 1)
    if "_asm" in output or "SRAND_MASK(" in output or "0x046C0000" in output:
        raise AssertionError("unconverted asm/macro/absolute pointer residue")

    preserved = {}
    for name in _C_BODY_NAMES:
        if name in ("GetRRandSeed", "SeedRRand"):
            continue
        before = _type_lower(original_bodies[name])
        if name == "RRand":
            before = re.sub(r"\brand\b", "dos_crt_rand", before)
        after = _function_body(output, name)
        if before != after:
            raise AssertionError(f"non-ASM C body changed beyond width normalization: {name}")
        preserved[name] = {"original_body_sha256": _sha(original_bodies[name]),
                           "normalized_body_sha256": _sha(after),
                           "body_preserved_after_target_width_lowering": True}
    seed_rrand_expected = _type_lower(original_bodies["SeedRRand"])
    seed_rrand_expected = re.sub(r"\bsrand\s*\(", "dos_crt_srand(",
                                 re.sub(r"\brand\s*\(", "dos_crt_rand(", seed_rrand_expected))
    seed_rrand_after = _function_body(output, "SeedRRand")
    if seed_rrand_expected != seed_rrand_after:
        raise AssertionError("SeedRRand body changed beyond target widths and explicit runtime namespace")
    preserved["SeedRRand"] = {"original_body_sha256": _sha(original_bodies["SeedRRand"]),
                              "normalized_body_sha256": _sha(seed_rrand_after),
                              "body_preserved_after_width_and_runtime_symbol_adaptation": True}
    expected_get_r_body = "{\n    return dos_host_read_u32(UINT32_C(0x46c0));\n}"
    if _function_body(output, "GetRRandSeed") != expected_get_r_body:
        raise AssertionError("GetRRandSeed must be only the explicit physical-address host leaf")

    ledger: dict[str, Any] = {
        "schema": "whole-program-rng-conversion-v1",
        "source": {"path": SOURCE_PATH, "sha256": source_sha},
        "host_output_sha256": _sha(output),
        "replacements": {
            "inline_asm_rng_forms": [{"function": "SRand1", "original_body_sha256": _sha(sr1_original),
                                      "operations": ["carry from original bit 15", "16-bit shift", "conditional XOR 0x1bf5",
                                                     "private seed write before unsigned 16-bit DIV", "AX receives DX remainder"]},
                                     *[{"function": name, "original_macro_invocation": f"SRAND_MASK({name}, {label}, {literal})",
                                        "mask": value, "ax_return": True}
                                       for name, label, literal, value in MASKS]],
            "absolute_read": {"function": "GetRRandSeed", "original_body_sha256": _sha(get_r_original),
                              "host_leaf": "dos_host_read_u32", "physical_address": "0x46c0",
                              "source_far_pointer": "046C:0000", "platform_provider": "unprovided"},
            "runtime_names": {"srand": "dos_crt_srand(uint16_t)", "rand": "dos_crt_rand(void) -> int16_t",
                              "state_provider": "caller-owned runtime provider; may use portable/game/simulation/rng.c MSC recurrence"},
            "zero_divisor": {"leaf": "dos_host_divide_fault", "noreturn": True,
                              "called_after_private_seed_advance": True},
            "source_type_lowering": {"unsigned int": "uint16_t", "int": "int16_t", "unsigned long": "uint32_t", "far": "removed",
                                     "scope": "target ABI spelling normalization only; no private RNG state is copied"},
        },
        "preserved_non_asm_bodies": preserved,
        "private_seed": {"owner": "static uint16_t seed in adapted root:0093 module", "storage_count": 1},
        "unprovided_platform_leaves": ["TickCount", "dos_host_read_u32", "dos_host_divide_fault"],
        "other_c_bodies": {"GetRRandSeed": "only replaced absolute memory access with host physical-address leaf",
                            "SeedRRand": "body retains original call order; only srand/rand namespace symbols and widths are adapted"},
    }
    return output, ledger
