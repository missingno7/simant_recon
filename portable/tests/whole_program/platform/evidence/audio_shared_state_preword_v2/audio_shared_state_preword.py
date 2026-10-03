"""Strict shared audio-state adapter for source before native word conversion.

Unlike audio_state.py (which consumes generated whole-program C), this adapter
runs on canonical original C after the audio boundary conversion/behavior
overlays. It verifies the immutable original file identity, edits code tokens
only, and rejects every changed struct shape/member count.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

HEADER = '#include "portable/whole_program/platform/audio_state.h"\n'

SOURCE_SHA256 = {
    "src/root/m0000.c": "d9ccffbb69c4fdcae55eef918bf420cff81ead6849f67298271c2844e04199f9",
    "src/root/m277E.c": "4e928689c743f473c5a007bbbbb5287cdf8728d12e9cae5652b1cb55debf09ee",
    "src/root/m2815.c": "7ab16f1356fd280057eb37d2cff8ec2cfbcd9dfbdf8ace444b7e300f49255a38",
    "src/root/m290D.c": "eaec23e8d37bd606616dc44208c7bbcf82ced13e24abe0362ef767c5e4cc4fed",
    "src/root/m295C.c": "d392b6ce886cfd664a192194b79569bb6a0d4dea8b0bc029ffa9e32ff44add89",
    "src/root/m284A.c": "bad7d3701a853ba2de166e4f875ba3043f33ca136b7d0dcff41db8e5459f9fa5",
    "src/root/m293A.c": "601b4e4e9e8b9d128cc97cca3da7dcf0ad863dbb5c6df587c601530cbe4ec5e6",
    "src/root/m29D6.c": "55476efe4ad6d0cd853cd794f731ff8f33df921577e092fc3e80e9b322b4c388",
    "src/root/m29F0.c": "2787050f6b809856cde2d2a60fe120357a195041d396bb55caf7dd1b8084e302",
    "src/data/d55B3_00B8.c": "d04646a28691ff05ad93a50c5e7142405ab64932f875f2d2a4d10d04a4566f3d",
}

_AUDIO_TUS = {
    f"src/root/{name}.c"
    for name in ("m0000", "m277E", "m2815", "m284A", "m290D", "m293A", "m295C", "m29D6", "m29F0")
}

_OWNER_PLAN_PINS = {
    "portable/research/whole_program_unprovided_owners_v2.json":
        "ff91c70e7d1458816e9a10d69945e2d87d0510fd5ebeb4bf8c391028f29229ae",
    "portable/research/whole_program_source_bounded_owners_v3.json":
        "ed54979f50150330df56b206e70da08a67df85ae424ff575006bed622bdfc897",
    "portable/research/whole_program_source_bounded_owners_v5.json":
        "b9ff9a739930c85537dba59edcd3680d52a10b36ca7684878e161f3d436f084e",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_later_scalar_owners(source_path: str) -> tuple[set[str], dict[str, str]]:
    """Return scalar externs owned by the pinned V2/V3/V5 source passes."""
    root = _repo_root()
    names: set[str] = set()
    pins: dict[str, str] = {}
    for rel, expected_sha in _OWNER_PLAN_PINS.items():
        plan_path = root / rel
        raw = plan_path.read_bytes()
        actual_sha = _sha(raw)
        if actual_sha != expected_sha:
            raise ValueError(f"state-owner plan changed: {rel}: {actual_sha}")
        pins[rel] = actual_sha
        plan = json.loads(raw)
        if rel.endswith("unprovided_owners_v2.json"):
            for candidate in plan.get("bss_owner_candidates", []):
                if candidate.get("decision") != "validated-farbss-integer-common-owner-candidate":
                    continue
                for row in candidate.get("assessment", {}).get("view_rows", []):
                    view = row.get("view", {})
                    if (view.get("module") == source_path and not view.get("dims") and
                            view.get("name") in _SHARED_EXTERN_COUNTS.get(source_path, {})):
                        names.add(view["name"])
            continue
        for owner in plan.get("owners", []):
            kind = owner.get("kind", "")
            for row in owner.get("source_mappings", []):
                if row.get("source") != source_path:
                    continue
                view = row.get("view", "")
                scalar_kind = (kind == "scalar-with-serialized-byte-overlay" or
                               view in {"scalar", "word-scalar", "scalar-value"})
                name = row.get("name")
                if scalar_kind and name in _SHARED_EXTERN_COUNTS.get(source_path, {}):
                    names.add(name)
    return names, pins


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lexical_mask(source: str) -> tuple[str, bytearray]:
    """Blank comments/literals while preserving character offsets/newlines."""
    chars = list(source)
    protected = bytearray(len(source))
    state = "code"
    i = 0
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == '"':
                state = "string"
            elif ch == "'":
                state = "char"
            elif ch == "/" and nxt == "*":
                state = "block_comment"
                protected[i] = protected[i + 1] = 1
                chars[i] = chars[i + 1] = " "
                i += 1
            elif ch == "/" and nxt == "/":
                state = "line_comment"
                protected[i] = protected[i + 1] = 1
                chars[i] = chars[i + 1] = " "
                i += 1
        elif state in ("string", "char"):
            protected[i] = 1
            if ch not in "\r\n":
                chars[i] = " "
            if ch == "\\" and i + 1 < len(source):
                i += 1
                protected[i] = 1
                if source[i] not in "\r\n":
                    chars[i] = " "
            elif (state == "string" and ch == '"') or (state == "char" and ch == "'"):
                state = "code"
        elif state == "block_comment":
            protected[i] = 1
            if ch not in "\r\n":
                chars[i] = " "
            if ch == "*" and nxt == "/":
                i += 1
                protected[i] = 1
                chars[i] = " "
                state = "code"
        else:
            protected[i] = 1
            if ch not in "\r\n":
                chars[i] = " "
            if ch in "\r\n":
                state = "code"
        i += 1
    if state in ("string", "char", "block_comment"):
        raise ValueError(f"unterminated C lexical region: {state}")
    return "".join(chars), protected


def _code_sub(source: str, pattern: str, replacement: str, *, label: str,
              expected: int) -> tuple[str, int]:
    masked, protected = _lexical_mask(source)
    matches = list(re.finditer(pattern, masked, flags=re.MULTILINE))
    if len(matches) != expected:
        raise ValueError(f"{label}: expected {expected} code occurrence(s), found {len(matches)}")
    result = source
    for match in reversed(matches):
        if any(protected[match.start():match.end()]):
            raise ValueError(f"{label}: attempted to cross comment/string/character content")
        result = result[:match.start()] + replacement(match) + result[match.end():]
    return result, len(matches)


def _remove_struct(source: str, tag: str, expected_fields: str) -> tuple[str, int]:
    pattern = rf"struct\s+{re.escape(tag)}\s*\{{[^{{}}]*\}}\s*;"
    masked, protected = _lexical_mask(source)
    matches = list(re.finditer(pattern, masked, flags=re.MULTILINE))
    if len(matches) != 1:
        raise ValueError(f"{tag}: expected one complete struct definition, found {len(matches)}")
    match = matches[0]
    if any(protected[match.start():match.end()]):
        raise ValueError(f"{tag}: struct block contains comment/literal; refuse to erase it")
    found = re.sub(r"\s+", " ", masked[match.start():match.end()]).strip()
    wanted = re.sub(r"\s+", " ", expected_fields).strip()
    if found != wanted:
        raise ValueError(f"{tag}: canonical source struct fields changed: {found!r}")
    return source[:match.start()] + source[match.end():], 1


def _tag(source: str, old: str, new: str, expected: int) -> tuple[str, int]:
    return _code_sub(source, rf"\bstruct\s+{re.escape(old)}\b",
                     lambda _m: new, label=f"struct {old} type use", expected=expected)


_CANONICAL_TYPE = {
    "Sample": "PortableWholeAudioSample",
    "Chan": "PortableWholeAudioRuntimeChannel",
    "Voice": "PortableWholeAudioInstrumentEntry",
    "Instr": "PortableWholeAudioInstrumentEntry",
    "SndChan": "PortableWholeAudioRuntimeSample",
    "Drv": "PortableWholeAudioInstrumentEntry",
    "Slot": "PortableWholeAudioVoiceSlot",
}


def _remove_then_tag(source: str, tag: str, fields: str, uses: int) -> str:
    source, _ = _remove_struct(source, tag, fields)
    source, _ = _tag(source, tag, _CANONICAL_TYPE[tag], uses)
    return source


def _m0000(source: str) -> str:
    source = _remove_then_tag(source, "Sample", "struct Sample { Handle data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; char name[15]; int object; };", 6)
    source = _remove_then_tag(source, "Instr", "struct Instr { int kind; PortableWholeAudioSample far *sample; };", 1)
    source, _ = _code_sub(source, r"fd_50F6_0000\[song->bank\[i\]\]\.sample",
                          lambda _m: "portable_whole_audio_sample(&fd_50F6_0000[song->bank[i]])",
                          label="m0000 bank sample payload", expected=3)
    source, _ = _code_sub(source, r"fd_50F6_0000\[i\]\.sample",
                          lambda _m: "portable_whole_audio_sample(&fd_50F6_0000[i])",
                          label="m0000 cleanup sample payload", expected=1)
    return source


def _m277e(source: str) -> str:
    source = _remove_then_tag(source, "Chan", "struct Chan { char type; char num; char c2; char c3; char c4; char c5; };", 1)
    source = _remove_then_tag(source, "Voice", "struct Voice { int a; void *b; };", 10)
    for old, new, expected in (("fd_50F6_0000[i].a", "fd_50F6_0000[i].kind", 1),
                               ("fd_50F6_0000[i].b", "fd_50F6_0000[i].payload", 1),
                               ("src[i].a", "src[i].kind", 1),
                               ("src[i].b", "src[i].payload", 1)):
        source, _ = _code_sub(source, re.escape(old), lambda _m, value=new: value,
                              label=f"m277E {old}", expected=expected)
    return source


def _m2815(source: str) -> str:
    source = _remove_then_tag(source, "Instr", "struct Instr { int a; unsigned char far *p; };", 1)
    source, _ = _code_sub(source, r"fd_50F6_0000\[instr\]\.p",
                          lambda _m: "portable_whole_audio_patch_bytes(&fd_50F6_0000[instr])",
                          label="m2815 patch pointer", expected=2)
    return source


def _m290d(source: str) -> str:
    source = _remove_then_tag(source, "Sample", "struct Sample { char far *data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; };", 9)
    source = _remove_then_tag(source, "SndChan", "struct SndChan { unsigned pos; PortableWholeAudioSample far *snd; unsigned end; unsigned start; unsigned step; unsigned voltab; unsigned char frac; unsigned char flags; PortableWholeAudioSample far *owner; };", 2)
    source = _remove_then_tag(source, "Instr", "struct Instr { int a; unsigned char far *p; };", 1)
    source, _ = _code_sub(source, r"fd_50F6_0000\[instr\]\.p",
                          lambda _m: "portable_whole_audio_sample(&fd_50F6_0000[instr])",
                          label="m290D sample pointer", expected=1)
    return source


def _m295c(source: str) -> str:
    source = _remove_then_tag(source, "Chan", "struct Chan { unsigned char type; unsigned char num; unsigned char c2; unsigned char c3; unsigned char c4; unsigned char c5; };", 3)
    source = _remove_then_tag(source, "Drv", "struct Drv { int count; int far *info; };", 1)
    source = _remove_then_tag(source, "Slot", "struct Slot { long busy; int w4; int w6; int w8; int wA; int wC; struct Snd far *snd; int w12; };", 1)
    source, _ = _code_sub(source, r"fd_50F6_0000\[dev\]\.count",
                          lambda _m: "fd_50F6_0000[dev].kind",
                          label="m295C driver kind", expected=2)
    source, _ = _code_sub(source, r"fd_50F6_0000\[dev\]\.info",
                          lambda _m: "portable_whole_audio_driver_info(&fd_50F6_0000[dev])",
                          label="m295C driver info", expected=6)
    return source


def _data_b8(source: str) -> str:
    source = _remove_then_tag(source, "Sample", "struct Sample { Handle data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; char name[15]; int object; };", 58)
    source = _remove_then_tag(source, "Instr", "struct Instr { int kind; void *p; };", 9)
    return source


_SHARED_EXTERN_COUNTS: dict[str, dict[str, int]] = {
    "src/root/m0000.c": {"fd_50F6_0150": 1, "fd_50F6_0000": 1, "fd_50F6_01F0": 1},
    "src/root/m277E.c": {
        "fd_55B3_74DA": 1, "fd_50F6_4A48": 1, "fd_50F6_4A4C": 1,
        "fd_50F6_01F0": 1, "fd_50F6_4A4E": 1, "fd_50F6_0000": 1,
        "fd_50F6_4A4A": 1, "fd_50F6_4B14": 1, "fd_55B3_6B4A": 1,
        "fd_55B3_74AD": 1, "fd_55B3_6B9C": 1, "fd_55B3_74C0": 1,
        "fd_55B3_74B9": 1, "fd_55B3_74B3": 1, "fd_55B3_74AF": 1,
        "fd_50F6_4B16": 1, "fd_55B3_7564": 1, "fd_55B3_6BA0": 1,
        "fd_55B3_74B5": 1, "fd_50F6_4A46": 1, "fd_55B3_74B7": 1,
        "fd_55B3_74B1": 1,
    },
    "src/root/m2815.c": {"fd_50F6_0000": 1, "fd_50F6_4B16": 1, "fd_55B3_6BA4": 1},
    "src/root/m284A.c": {
        "fd_50F6_4B28": 1, "fd_50F6_4B2C": 1, "fd_55B3_6B42": 1,
        "fd_50F6_4B8E": 1, "fd_50F6_4BAA": 1, "fd_50F6_4B2E": 1,
        "fd_50F6_4B42": 1, "fd_50F6_4B30": 1, "fd_50F6_4B8A": 1,
    },
    "src/root/m290D.c": {"fd_55B3_6B4C": 1, "fd_50F6_0000": 1},
    "src/root/m293A.c": {"fd_50F6_01F0": 1, "fd_50F6_4B14": 1},
    "src/root/m295C.c": {"fd_50F6_4A4E": 1, "fd_55B3_6B4E": 1, "fd_50F6_0000": 1},
    "src/root/m29D6.c": {"fd_50F6_4B14": 1},
}


_TRANSFORMS: dict[str, Callable[[str], str]] = {
    "src/root/m0000.c": _m0000,
    "src/root/m277E.c": _m277e,
    "src/root/m2815.c": _m2815,
    "src/root/m290D.c": _m290d,
    "src/root/m295C.c": _m295c,
    "src/data/d55B3_00B8.c": _data_b8,
}


def adapt(path: str, source: str, original_source: str | bytes, *,
          deferred_scalar_externs: set[str] | frozenset[str] = frozenset()) -> tuple[str, dict[str, object]]:
    """Adapt one original-source-derived TU; original bytes are mandatory pins."""
    rel = path.replace("\\", "/")
    transform = _TRANSFORMS.get(rel)
    if transform is None and rel not in _AUDIO_TUS:
        return source, {"status": "UNCHANGED", "reason": "no shared audio-state view"}
    original = original_source if isinstance(original_source, bytes) else original_source.encode("utf-8")
    expected_sha = SOURCE_SHA256[rel]
    actual_sha = _sha(original)
    if actual_sha != expected_sha:
        raise ValueError(f"{rel}: original-source identity mismatch: {actual_sha}")
    expected_symbols = _SHARED_EXTERN_COUNTS.get(rel, {})
    unknown_deferred = set(deferred_scalar_externs) - set(expected_symbols)
    if unknown_deferred:
        raise ValueError(f"{rel}: cannot defer non-shared scalar declaration(s): {sorted(unknown_deferred)}")
    if HEADER in source:
        raise ValueError(f"{rel}: common audio-state header was already injected")
    output = transform(source) if transform is not None else source
    removed_externs: dict[str, int] = {}
    retained_scalar_externs: dict[str, int] = {}
    for symbol, expected in _SHARED_EXTERN_COUNTS.get(rel, {}).items():
        pattern = rf"(?m)^[ \t]*extern\b[^;\r\n]*\b{re.escape(symbol)}\b[^;\r\n]*;"
        if symbol in deferred_scalar_externs:
            masked, _ = _lexical_mask(output)
            retained = len(re.findall(pattern, masked, flags=re.MULTILINE))
            if retained != expected:
                raise ValueError(f"{rel} shared scalar extern {symbol}: expected to retain {expected}, found {retained}")
            retained_scalar_externs[symbol] = retained
            continue
        output, count = _code_sub(output, pattern, lambda _m: "",
                                  label=f"{rel} shared extern {symbol}", expected=expected)
        removed_externs[symbol] = count
    output = HEADER + output
    if rel.endswith("m0000.c") and re.search(r"fd_50F6_0000\s*\[[^]]+\]\s*\.\s*sample", _lexical_mask(output)[0]):
        raise AssertionError("m0000 direct Sample view remains")
    if rel.endswith("m2815.c") and re.search(r"fd_50F6_0000\s*\[[^]]+\]\s*\.\s*p\b", _lexical_mask(output)[0]):
        raise AssertionError("m2815 direct patch pointer remains")
    if rel.endswith("m295C.c") and re.search(r"fd_50F6_0000\s*\[[^]]+\]\s*\.\s*info\b", _lexical_mask(output)[0]):
        raise AssertionError("m295C direct driver-info pointer remains")
    return output, {
        "status": "SOURCE_SHARED_AUDIO_STATE" if transform is not None else "SOURCE_SHARED_AUDIO_DECLARATIONS",
        "original_sha256": actual_sha,
        "transformed_input_sha256": _sha(source.encode("utf-8")),
        "output_sha256": _sha(output.encode("utf-8")),
        "owner_header": "portable/whole_program/platform/audio_state.h",
        "state_ownership": {
            "pointer_tables_records": "portable/whole_program/platform/audio_state.c",
            "existing_scalar_aliases": "generated source_state_owners.c (V2/V3); no second definitions introduced",
        },
        "centralized_externs_removed": removed_externs,
        "deferred_scalar_externs_retained": retained_scalar_externs,
        "lexical_contract": "Only code tokens and exact complete struct blocks changed; comments and literals are protected by offset-preserving lexer.",
    }


def adapt_production(path: str, source: str, original_source: str | bytes) -> tuple[str, dict[str, object]]:
    """Preword entry for central generation; defer only pinned later-owned scalars."""
    rel = path.replace("\\", "/")
    deferred, pins = resolve_later_scalar_owners(rel)
    output, ledger = adapt(rel, source, original_source, deferred_scalar_externs=deferred)
    ledger["later_scalar_owner_plans"] = pins
    ledger["production_entry"] = "adapt_production"
    return output, ledger
