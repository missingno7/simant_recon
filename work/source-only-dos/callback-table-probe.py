"""Fresh source-only callback-table proof and m1B4E OMF field comparison.

Every OBJ used by a runtime case or full-module comparison is compiled in this
run from source below, the provider file, or canonical m1B4E.asm. No prebuilt or
ignored OBJ/EXE is opened as an input.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

PROBE = Path(__file__).resolve()
PROVIDER = ROOT / "work/source-only-dos/providers/callback-table.c"
CONTRACT = ROOT / "build/workers/dos_callback_table_runtime/callback-table-contract-candidate.json"
OUT = ROOT / "build/workers/dos_callback_table_runtime"
START = 0x9128
END = 0x918C
NAMES = [
    "g_9128", "g_912C", "g_9130", "g_9134", "g_9138", "g_913C",
    "g_9140", "g_9144", "g_9148", "g_914C", "g_9150", "g_9154",
    "g_9158", "g_915C", "g_9160", "g_9164", "g_9168", "g_916C",
    "g_9170", "g_9174", "g_9178", "g_917C", "g_9180", "g_9184", "g_9188",
]
MAIN = r'''#include <stdio.h>
typedef void (far * near SlotFn)();
extern SlotFn near driver_callback_table[25];
extern void far test_reset(void);
extern void far test_copy(void);
extern int far test_pointer_ok(void);
extern void far test_set_canaries(void);
extern int far test_canaries_ok(void);
extern void far test_write_word(void);
extern void far test_entry(void);
extern void far f_1B4E_000C(void);
extern char near g_9128, g_912C, g_9130, g_9134, g_9138, g_913C;
extern char near g_9140, g_9144, g_9148, g_914C, g_9150, g_9154;
extern char near g_9158, g_915C, g_9160, g_9164, g_9168, g_916C;
extern char near g_9170, g_9174, g_9178, g_917C, g_9180, g_9184, g_9188;
#define FAIL_IF(e,t) do { if (e) { printf("FAIL %s\r\n",t); return 1; } } while (0)
#define VIEW(n,o) FAIL_IF((unsigned int)(char near *)&n != base + (o), #n)
int main(void)
{
    unsigned char near *bytes;
    unsigned char near *expected_bytes;
    SlotFn expected;
    unsigned int base;
    int i, j;
    bytes=(unsigned char near *)driver_callback_table;
    base=(unsigned int)(char near *)driver_callback_table;
    FAIL_IF(sizeof(SlotFn)!=4 || sizeof(driver_callback_table)!=100,"period");
    VIEW(g_9128,0); VIEW(g_912C,4); VIEW(g_9130,8); VIEW(g_9134,12); VIEW(g_9138,16);
    VIEW(g_913C,20); VIEW(g_9140,24); VIEW(g_9144,28); VIEW(g_9148,32); VIEW(g_914C,36);
    VIEW(g_9150,40); VIEW(g_9154,44); VIEW(g_9158,48); VIEW(g_915C,52); VIEW(g_9160,56);
    VIEW(g_9164,60); VIEW(g_9168,64); VIEW(g_916C,68); VIEW(g_9170,72); VIEW(g_9174,76);
    VIEW(g_9178,80); VIEW(g_917C,84); VIEW(g_9180,88); VIEW(g_9184,92); VIEW(g_9188,96);
    FAIL_IF(test_pointer_ok()!=1,"symbolic_table_pointer");
    for(i=0;i<100;i++) FAIL_IF(bytes[i]!=0,"MSC_startup_near_zero");
    test_set_canaries(); bytes[0]=0xCC; bytes[99]=0xDD; test_write_word();
    FAIL_IF(bytes[4]!=0x78 || bytes[5]!=0x56,"ASM_word_C_byte_view");
    bytes[4]=0xAA; bytes[5]=0xBB;
    FAIL_IF(*(unsigned int near *)&g_912C!=0xBBAA,"C_byte_ASM_word_view");
    for(i=0;i<100;i++) bytes[i]=0xCC;
    test_reset(); expected=f_1B4E_000C; expected_bytes=(unsigned char near *)&expected;
    for(i=0;i<25;i++) for(j=0;j<4;j++)
        FAIL_IF(bytes[i*4+j]!=expected_bytes[j],"reset_extent_50_words");
    FAIL_IF(test_canaries_ok()!=1,"reset_canary");
    test_copy(); expected=test_entry; expected_bytes=(unsigned char near *)&expected;
    for(i=0;i<25;i++) for(j=0;j<4;j++)
        FAIL_IF(bytes[i*4+j]!=expected_bytes[j],"copy_extent_50_words");
    FAIL_IF(bytes[0]!=expected_bytes[0] || bytes[1]!=expected_bytes[1] ||
            bytes[96]!=expected_bytes[0] || bytes[97]!=expected_bytes[1] ||
            bytes[98]!=expected_bytes[2] || bytes[99]!=expected_bytes[3],"first_last_slots");
    FAIL_IF(test_canaries_ok()!=1,"copy_canary");
    puts("PASS"); return 0;
}
'''

TABLE_ASM = r'''_DATA segment word public 'DATA'
extrn _g_9128:byte
extrn _g_912C:byte
public _g_3DF4, _g_3DF8
_g_3DF4 dd _f_1B4E_000C
_g_3DF8 dd {base}
_test_dispatch_pointer dd DGROUP:_DispatchTest
_DispatchTest label dword
{dispatch}
_DATA ends
DGROUP group _DATA
TEST_TEXT segment word public 'CODE'
assume cs:TEST_TEXT, ds:DGROUP
public _f_1B4E_000C, _f_1B4E_0025, _f_1B4E_0165
public _test_reset, _test_copy, _test_pointer_ok, _test_write_word
public _test_set_canaries, _test_canaries_ok, _test_entry
_f_1B4E_000C proc far
retf
_f_1B4E_000C endp
_test_entry proc far
retf
_test_entry endp
; Source-shaped copies of canonical m1B4E.asm reset and copy procedures.
_f_1B4E_0025 proc far
push di
les bx, dword ptr _g_3DF4
mov ax, es
les di, dword ptr _g_3DF8
mov cx, 19h
L0033:
xchg bx, ax
stosw
xchg bx, ax
stosw
loop L0033
pop di
retf
_f_1B4E_0025 endp
_f_1B4E_0165 proc far
push ds
push di
mov ax, es
les di, dword ptr _g_3DF8
mov ds, ax
mov cx, 32h
rep movsw
pop di
pop ds
retf
_f_1B4E_0165 endp
_test_reset proc far
call far ptr _f_1B4E_0025
retf
_test_reset endp
_test_copy proc far
les si, dword ptr _test_dispatch_pointer
call far ptr _f_1B4E_0165
retf
_test_copy endp
_test_pointer_ok proc far
mov ax, word ptr _g_3DF8
cmp ax, offset _g_9128
jne Lpointer_bad
mov ax, word ptr _g_3DF8+2
mov dx, seg _g_9128
cmp ax, dx
jne Lpointer_bad
mov ax, 1
retf
Lpointer_bad:
xor ax, ax
retf
_test_pointer_ok endp
_test_write_word proc far
mov word ptr _g_912C, 5678h
retf
_test_write_word endp
_test_set_canaries proc far
mov bx, offset DGROUP:_g_9128
mov byte ptr [bx+64h], 0A5h
mov byte ptr [bx+65h], 05Ah
mov byte ptr [bx+66h], 0C3h
mov byte ptr [bx+67h], 03Ch
retf
_test_set_canaries endp
_test_canaries_ok proc far
mov bx, offset DGROUP:_g_9128
cmp byte ptr [bx+64h], 0A5h
jne Lcanary_bad
cmp byte ptr [bx+65h], 05Ah
jne Lcanary_bad
cmp byte ptr [bx+66h], 0C3h
jne Lcanary_bad
cmp byte ptr [bx+67h], 03Ch
jne Lcanary_bad
mov ax, 1
retf
Lcanary_bad:
xor ax, ax
retf
_test_canaries_ok endp
TEST_TEXT ends
end
'''

VIEW_CONTRACTS = {
    "g_9128": "void far (int,int,int)", "g_912C": "void far (void)",
    "g_9130": "void far (void)", "g_9134": "void far (int,int,int,int,int)",
    "g_9138": "void far (int,int,int,int,int)", "g_913C": "void far (int,int,int,int)",
    "g_9140": "int/unsigned int far (int,int,int,int); signedness differs by consumer",
    "g_9144": "int far (int,int,int,int)", "g_9148": "void far (int,int,int,int,char far *)",
    "g_914C": "void far (int,int,char far *,int,int); calls establish five arguments",
    "g_9150": "void far (int,int,char far *,int,int)", "g_9154": "void far (int,int,char far *,int,int)",
    "g_9158": "void far (int,int,char far *,int,int)",
    "g_915C": "provider mode-setter entries; no consumer call arity observed",
    "g_9160": "indirect assembly caller/provider evidence; no canonical C prototype",
    "g_9164": "indirect assembly caller/provider evidence; no canonical C prototype",
    "g_9168": "indirect assembly caller/provider evidence; no canonical C prototype",
    "g_916C": "void far (int,int,int,int,int)", "g_9170": "void far (int,int,int,int,int)",
    "g_9174": "void far (int,int,int,int,int)", "g_9178": "void far (void)",
    "g_917C": "void far (int,int,int)",
    "g_9180": "S00 provider reads far source pointer and two words; no caller upper arity bound",
    "g_9184": "void far (int)", "g_9188": "void far (int,int,int,int,int,int)",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def compile_c(source: str, basename: str):
    result = compiler.compile_c(source, "msc600ax", ["/AL", "/Os", "/Zi"], basename=basename, keep=True)
    if not result.ok:
        raise RuntimeError(f"C compile failed ({basename}):\n{result.log}")
    return result


def assemble(source: str, basename: str):
    result = compiler.assemble(source, "masm510", ["/Mx"], basename=basename, keep=True)
    if not result.ok:
        raise RuntimeError(f"ASM compile failed ({basename}):\n{result.log}")
    return result


def assemble_table(base: str) -> str:
    entries = "\r\n".join("dd _test_entry" for _ in range(25))
    return TABLE_ASM.format(base=base, dispatch=entries)


def records(data: bytes) -> dict:
    return dict(sorted((f"0x{k:02X}", n) for k, n in Counter(kind for kind, _ in OmfReader.records(data)).items()))


def segment_live_report(module) -> dict:
    return {
        "segment_defs": module.segment_defs,
        "segment_lengths": module.segment_lengths,
        "nonempty_segments": {name: len(data) for name, data in module.segments.items() if data},
        "live_code_data_const_bss": {
            name: module.segment_length(name)
            for name in module.segment_lengths
            if name.upper().endswith(("_TEXT", "TEXT")) or name.upper() in {"_DATA", "DATA", "CONST", "_BSS", "BSS"}
        },
    }


def pin_file(path: Path) -> dict:
    raw, pin = dos.pin(path)
    return pin


def run_case(linker_name: str, linker: dict, linker_dir: Path, runner: dict,
             runtime_rows: list[dict], owner_obj: bytes, table_obj: bytes,
             main_obj: bytes, case: str, aliases: dict[str, int], expected: str) -> dict:
    d = OUT / linker_name / case
    d.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "LINK.LOG", "RUN.LOG"):
        (d / name).unlink(missing_ok=True)
    # These objects were just built above from source in this invocation.
    for name, obj in (("OWNER.OBJ", owner_obj), ("TABLE.OBJ", table_obj), ("MAIN.OBJ", main_obj)):
        (d / name).write_bytes(obj)
    for row in runtime_rows:
        shutil.copyfile(row["path"], d / Path(row["path"]).name.upper())
    definitions = "\r\n".join(f"DEFINE _{name} = _driver_callback_table + {off:X}"
                              for name, off in aliases.items())
    lnk = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
           "LIBRARY LLIBCR, LIBH\r\nFILE MAIN, OWNER, TABLE\r\n" + definitions + "\r\n")
    (d / "PROBE.LNK").write_text(lnk, encoding="ascii", newline="")
    (d / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (d / "RUN.BAT").write_text(
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n",
        encoding="ascii", newline="")
    conf = []
    for section, settings in runner["conf"].items():
        conf.append("[" + section + "]")
        conf += [f"{k}={v}" for k, v in settings.items()]
    conf += ["[autoexec]", f'mount c "{d}"', f'mount d "{linker_dir}" -ro', "c:", "call RUN.BAT", "exit"]
    (d / "dosbox.conf").write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    process = subprocess.run([runner["path"], "-conf", str(d / "dosbox.conf"),
                              "-fastlaunch", "-exit", "-nomenu"], cwd=d, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    actual = ((d / "RUN.LOG").read_text(encoding="latin1", errors="replace").strip()
              if (d / "RUN.LOG").exists() else "<missing>")
    link_log = ((d / "LINK.LOG").read_text(encoding="latin1", errors="replace")
                if (d / "LINK.LOG").exists() else "")
    map_text = ((d / "PROBE.MAP").read_text(encoding="latin1", errors="replace")
                if (d / "PROBE.MAP").exists() else "")
    map_publics = {}
    in_publics = False
    for line in map_text.splitlines():
        if "Publics by Name" in line and "Address" in line:
            in_publics = True
            continue
        if in_publics:
            match = re.match(r"\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(_?[A-Za-z_$][A-Za-z0-9_$]*)\s*$", line, re.I)
            if match:
                map_publics[match.group(3)] = {"segment": int(match.group(1), 16),
                                               "offset": int(match.group(2), 16)}
            elif line.strip() and not set(line.strip()) <= {"-"}:
                if map_publics:
                    break
    owner_map = map_publics.get("_driver_callback_table")
    base_map = map_publics.get("_g_9128")
    pointer_map = map_publics.get("_g_3DF8")
    dgrow_map = None
    for line in map_text.splitlines():
        match = re.search(r"([0-9A-F]{1,4}):\s*0\s+DGROUP\s*$", line, re.I)
        if match:
            dgrow_map = int(match.group(1), 16)
            break
    aliases_exact = bool(owner_map and base_map and owner_map == base_map and
                         owner_map["offset"] != 0x9128 and owner_map["segment"] == dgrow_map)
    for i, name in enumerate(NAMES):
        item = map_publics.get("_" + name)
        if (item is None or owner_map is None or item["segment"] != owner_map["segment"] or
                item["offset"] != owner_map["offset"] + 4 * i):
            aliases_exact = False
    pointer_storage_in_dgroup = bool(pointer_map and owner_map and dgrow_map is not None and
                                    pointer_map["segment"] == owner_map["segment"] == dgrow_map)
    map_contract_required = case == "positive"
    return {
        "linker": linker_name, "case": case, "expected": expected, "actual": actual,
        "passed": actual == expected and process.returncode == 0 and
                  (not map_contract_required or (aliases_exact and pointer_storage_in_dgroup)),
        "map_contract_required": map_contract_required,
        "map_contract_passed": aliases_exact if map_contract_required else None,
        "emulator_exit": process.returncode, "alias_offsets": aliases,
        "link_log_tail": link_log[-1400:],
        "fresh_fixture_object_sha256": {"OWNER.OBJ": sha(owner_obj), "TABLE.OBJ": sha(table_obj), "MAIN.OBJ": sha(main_obj)},
        "linked_group_geometry": {
            "DGROUP_segment": dgrow_map,
            "owner_public": owner_map,
            "g_9128_public": base_map,
            "g_3DF8_public": pointer_map,
            "all_aliases_at_exact_owner_offsets": aliases_exact,
            "g_3DF8_pointer_field_is_in_same_DGROUP_segment": pointer_storage_in_dgroup,
            "g_3DF8_minus_owner_offset": (pointer_map["offset"] - owner_map["offset"]
                                         if pointer_map and owner_map and pointer_map["segment"] == owner_map["segment"]
                                         else None),
            "owner_is_link_shifted_from_historical_0x9128": bool(owner_map and owner_map["offset"] != 0x9128),
        },
    }


def raw_record_counts(data: bytes) -> dict:
    return Counter(kind for kind, _ in OmfReader.records(data))


def make_wrong_symbolic(source: str) -> str:
    pat = re.compile(r"(?im)^(_g_3DF8\s+dd\s+)_g_9128(\s*;.*)$")
    changed, n = pat.subn(lambda m: m.group(1) + "_g_9128+4" + m.group(2), source, count=1)
    if n != 1:
        raise ValueError("cannot create wrong-base symbolic negative")
    return changed


OUT.mkdir(parents=True, exist_ok=True)
denied = dos.install_input_guard()
provider_source = PROVIDER.read_text(encoding="ascii")
provider_expected = "void (far * near driver_callback_table[25])();\n"
if provider_source != provider_expected:
    raise ValueError("provider must contain only the requested natural-C array declaration")
owner_build = compile_c(provider_source, "CBLTBL01")
main_build = compile_c(MAIN, "CBLTMAIN")
nonzero_source = "void (far * near driver_callback_table[25])() = {(void far *)1};\n"
nonzero_build = compile_c(nonzero_source, "CBLTNZ01")
table_source = assemble_table("_g_9128")
wrong_pointer_source = assemble_table("_g_9128+4")
table_build = assemble(table_source, "CBLTTBL1")
wrong_pointer_build = assemble(wrong_pointer_source, "CBLTTBL2")

(OUT / "main.c").write_text(MAIN, encoding="ascii")
(OUT / "provider-nonzero.c").write_text(nonzero_source, encoding="ascii")
(OUT / "table.asm").write_text(table_source, encoding="ascii")
(OUT / "table-wrong-pointer.asm").write_text(wrong_pointer_source, encoding="ascii")
for name, build in (("owner", owner_build), ("main", main_build), ("owner-nonzero", nonzero_build),
                    ("table", table_build), ("table-wrong-pointer", wrong_pointer_build)):
    (OUT / (name + ".OBJ")).write_bytes(build.obj)

owner_omf = OmfReader(communals=True).read(owner_build.obj, "CBLTBL01")
main_omf = OmfReader().read(main_build.obj, "CBLTMAIN")
nonzero_omf = OmfReader(communals=True).read(nonzero_build.obj, "CBLTNZ01")
table_omf = OmfReader().read(table_build.obj, "CBLTTBL1")
wrong_table_omf = OmfReader().read(wrong_pointer_build.obj, "CBLTTBL2")
if owner_omf.communals != [{"name": "_driver_callback_table", "kind": "near",
                            "type_index": owner_omf.communals[0]["type_index"], "length": 100}]:
    raise ValueError(f"provider communal is not the exact expected 100-byte near object: {owner_omf.communals}")
if any(owner_omf.segment_length(name) not in (None, 0) for name in
       ("CBLTBL01_TEXT", "_DATA", "CONST", "_BSS")):
    raise ValueError("provider has live code/data/const/BSS")

tc = compiler.toolchain()
manifest_raw, manifest_pin = dos.pin(ROOT / "layout/manifest.json")
manifest = json.loads(manifest_raw)
runtime_rows = list(manifest["runtime"]["libraries"].values())
runner = tc["runners"]["dosbox-x"]
aliases = {name: 4 * i for i, name in enumerate(NAMES)}
wrong_alias = dict(aliases)
wrong_alias["g_9188"] = 94
cases = []
for linker_name in ("rtlink400", "rtlink610"):
    linker = tc["linkers"][linker_name]
    linker_dir = compiler.pinned_tree(linker)
    variants = (
        ("positive", owner_build.obj, table_build.obj, aliases, "PASS"),
        ("wrong_alias_offset", owner_build.obj, table_build.obj, wrong_alias, "FAIL g_9188"),
        ("nonzero_initialized_owner", nonzero_build.obj, table_build.obj, aliases,
         "FAIL MSC_startup_near_zero"),
        ("wrong_g3df8_base", owner_build.obj, wrong_pointer_build.obj, aliases,
         "FAIL symbolic_table_pointer"),
    )
    for case_name, case_owner, case_table, case_aliases, expected in variants:
        cases.append(run_case(linker_name, linker, linker_dir, runner, runtime_rows,
                              case_owner, case_table, main_build.obj, case_name,
                              case_aliases, expected))
        print(linker_name, case_name, cases[-1]["actual"], flush=True)

# Compile the complete canonical module and source-derived alternatives fresh.
canonical_asm_path = ROOT / "src/root/m1B4E.asm"
canonical_asm = canonical_asm_path.read_text(encoding="latin1")
if "_g_3DF8\t\tdd\t_g_9128" not in canonical_asm:
    # Whitespace is source-format detail; verify the actual declaration too.
    if not re.search(r"(?im)^_g_3DF8\s+dd\s+_g_9128\s*;", canonical_asm):
        raise ValueError("canonical module no longer uses the symbolic g_3DF8 pointer")
wrong_symbolic_asm = make_wrong_symbolic(canonical_asm)
(OUT / "m1B4E-symbolic.asm").write_text(canonical_asm, encoding="ascii")
(OUT / "m1B4E-wrong-symbolic-negative.asm").write_text(wrong_symbolic_asm, encoding="ascii")
full_symbolic_build = assemble(canonical_asm, "CBLTM1BS")
full_wrong_build = assemble(wrong_symbolic_asm, "CBLTM1BW")
for name, build in (("m1B4E-symbolic", full_symbolic_build),
                    ("m1B4E-wrong-symbolic-negative", full_wrong_build)):
    (OUT / (name + ".OBJ")).write_bytes(build.obj)

full_objects = {
    "symbolic_candidate": OmfReader(communals=True).read(full_symbolic_build.obj, "CBLTM1BS"),
    "wrong_symbolic_base_negative": OmfReader(communals=True).read(full_wrong_build.obj, "CBLTM1BW"),
}
candidate = full_objects["symbolic_candidate"]
bad_full = full_objects["wrong_symbolic_base_negative"]
table_public = next(p for p in candidate.publics if p["name"] == "_g_3DF8")
field_seg, field_off = table_public["segment"], table_public["offset"]
field_bytes = {key: obj.segment_bytes(field_seg)[field_off:field_off + 4].hex()
               for key, obj in full_objects.items()}
symbolic_field_fixups = [f for f in candidate.fixups if f["segment"] == field_seg and f["offset"] == field_off]
wrong_field_fixups = [f for f in bad_full.fixups if f["segment"] == field_seg and f["offset"] == field_off]
if (candidate.segment_lengths != bad_full.segment_lengths or candidate.publics != bad_full.publics or
        candidate.groups != bad_full.groups):
    raise ValueError("full m1B4E base+4 negative changed segment extent/public/group structure")
segment_diffs = {}
for name in candidate.segments:
    if name not in bad_full.segments:
        raise ValueError("negative lacks segment " + name)
    a, b = candidate.segment_bytes(name), bad_full.segment_bytes(name)
    if len(a) != len(b):
        raise ValueError("full m1B4E segment length changed " + name)
    segment_diffs[name] = [{"offset": i, "candidate": f"{x:02X}", "wrong_base": f"{b[i]:02X}"}
                           for i, x in enumerate(a) if x != b[i]]
candidate_fixup_counts = Counter(tuple(sorted(f.items())) for f in candidate.fixups)
wrong_fixup_counts = Counter(tuple(sorted(f.items())) for f in bad_full.fixups)
fixup_delta = {
    "wrong_base_only": [dict(k) for k, count in (wrong_fixup_counts - candidate_fixup_counts).items() for _ in range(count)],
    "symbolic_candidate_only": [dict(k) for k, count in (candidate_fixup_counts - wrong_fixup_counts).items() for _ in range(count)],
}
record_type_names = {0x80: "THEADR", 0x88: "COMENT", 0x8A: "MODEND16", 0x8C: "EXTDEF",
                     0x90: "PUBDEF16", 0x94: "LINNUM16", 0x96: "LNAMES", 0x98: "SEGDEF16",
                     0x9A: "GRPDEF", 0x9C: "FIXUPP16", 0xA0: "LEDATA16", 0xA2: "LIDATA16",
                     0xB0: "COMDEF", 0xB4: "LEXTDEF", 0xB6: "LPUBDEF"}
def named_records(data: bytes) -> dict:
    return {record_type_names.get(int(k, 16), k): v for k, v in records(data).items()}

debug_classes = {"DEBSYM", "DEBTYP", "DEBUG", "LINNUM"}
candidate_debug = [d for d in candidate.segment_defs if d["class"].upper() in debug_classes]
negative_debug = [d for d in bad_full.segment_defs if d["class"].upper() in debug_classes]
full_module = {
    "source": str(canonical_asm_path.relative_to(ROOT)).replace("\\", "/"),
    "current_source_has_symbolic_initializer": True,
    "canonical_source_is_compared_directly_without_an_initializer_edit": True,
    "symbolic_source": {
        "obj_sha256": sha(full_symbolic_build.obj), "record_counts": named_records(full_symbolic_build.obj),
        "segments": segment_live_report(candidate),
        "publics": candidate.publics,
        "external_symbols": candidate.externals,
        "groups": candidate.groups,
        "field_fixups": symbolic_field_fixups,
        "source_declaration_lines": [line.strip() for line in canonical_asm.splitlines()
                                      if re.search(r"(?i)extrn\s+_g_9128\s*:\s*byte", line)],
    },
    "wrong_symbolic_base_negative": {
        "obj_sha256": sha(full_wrong_build.obj), "record_counts": named_records(full_wrong_build.obj),
        "field_fixups": wrong_field_fixups,
    },
    "field": {
        "public": "_g_3DF8", "segment": field_seg, "offset": field_off,
        "offset_hex": f"0x{field_off:04X}", "width": 4,
        "bytes_by_variant": field_bytes,
    },
    "symbolic_vs_wrong_base_negative": {
        "segment_byte_differences": segment_diffs,
        "live_code_bytes_identical": not segment_diffs.get("VIDEO_TEXT"),
        "live_data_bytes_identical": not segment_diffs.get("_DATA"),
        "fixup_delta": fixup_delta,
        "publics_identical": candidate.publics == bad_full.publics,
        "externals_identical": candidate.externals == bad_full.externals,
        "groups_identical": candidate.groups == bad_full.groups,
        "segment_defs_identical": candidate.segment_defs == bad_full.segment_defs,
        "debug_records": {
            "candidate_codeview_or_linnum_records": {k: v for k, v in named_records(full_symbolic_build.obj).items()
                                                      if k in {"LINNUM16"}},
            "negative_codeview_or_linnum_records": {k: v for k, v in named_records(full_wrong_build.obj).items()
                                                     if k in {"LINNUM16"}},
            "candidate_debug_segments": candidate_debug,
            "negative_debug_segments": negative_debug,
            "any_debug_metadata_present": bool(candidate_debug or negative_debug or
                                               "LINNUM16" in named_records(full_symbolic_build.obj) or
                                               "LINNUM16" in named_records(full_wrong_build.obj)),
        },
    },
}

# Derive bounded aliases from the pinned layout symbol registry and exact
# identifier occurrences in canonical source. Do not depend on an ignored
# source-only build report or its semantic-substitution/import metadata.
symbols_raw, symbols_pin = dos.pin(ROOT / "layout/symbols.json")
symbols = json.loads(symbols_raw)["data"]
REGISTERED = {name for name in NAMES if isinstance(symbols.get(name), dict)}
if len(REGISTERED) != 23:
    raise ValueError(f"expected 23 registered callback slot symbols, found {len(REGISTERED)}")
source_refs = {name: {"canonical": []} for name in NAMES}
token_pats = {name: re.compile(r"(?<![A-Za-z0-9_])_?" + re.escape(name) + r"(?![A-Za-z0-9_])", re.I)
              for name in NAMES}
source_pins = {}
for path in sorted((ROOT / "src").rglob("*")):
    if path.suffix.lower() not in {".c", ".asm"}:
        continue
    lines = path.read_text(encoding="latin1").splitlines()
    relative = str(path.relative_to(ROOT)).replace("\\", "/")
    for no, line in enumerate(lines, 1):
        for name, pattern in token_pats.items():
            if pattern.search(line):
                source_refs[name]["canonical"].append({"source": relative, "line": no, "text": line.strip()})
    if any(source_refs[name]["canonical"] and source_refs[name]["canonical"][-1]["source"] == relative for name in NAMES):
        source_pins[relative] = sha(path.read_bytes())

dispatch = {}
for driver, path_name in {"S00": "src/S00/m3126.asm", "S01": "src/S01/m3126.asm",
                          "S02": "src/S02/m3126.asm", "S03": "src/S03/m3126.asm"}.items():
    text = (ROOT / path_name).read_text(encoding="latin1")
    table_name = "Dispatch" + driver
    m = re.search(r"(?im)^\s*" + table_name + r"\s+label\s+dword\s*$([\s\S]*?)(?=^\s*_?[A-Za-z][A-Za-z0-9_]*\s+(?:dd|dw|db|label|segment|ends)\b)", text)
    if not m:
        raise ValueError("cannot parse " + table_name)
    targets = re.findall(r"(?im)^\s*dd\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", m.group(1))
    if len(targets) != 25:
        raise ValueError(f"{driver} dispatch table has {len(targets)} entries")
    dispatch[driver] = targets

ownership_map = []
for slot, name in enumerate(NAMES):
    off = START + slot * 4
    symbol = symbols.get(name)
    if name in REGISTERED:
        if symbol.get("seg") != 0x55B3 or symbol.get("off") != off:
            raise ValueError("layout symbol is outside the bounded 25-slot range: " + name)
        if not source_refs[name]["canonical"]:
            raise ValueError("registered slot lacks canonical source references: " + name)
    elif isinstance(symbol, dict):
        raise ValueError("test-only position has an unexpected layout symbol: " + name)
    ownership_map.append({
        "slot": slot, "offset_from_owner": slot * 4, "historical_address": f"0x{off:04X}",
        "registered_name": "_" + name if name in REGISTERED else None,
        "test_alias": "_" + name,
        "layout_symbol_grounding": (symbol or {}).get("grounding"),
        "optional_import_join": {
            "status": "not_loaded; ignored build/source-only report is not a probe prerequisite",
            "accepted_storage_candidates": None,
            "declaration_contexts": None,
        },
        "provider_targets": {driver: targets[slot] for driver, targets in dispatch.items()},
        "consumer_contract": VIEW_CONTRACTS[name],
        "canonical_source_refs": source_refs[name]["canonical"],
    })

packet_paths = [ROOT / "work/source-only-dos/source-bindings-v1.json",
                ROOT / "work/source-only-dos/c-data-bindings-v1.json",
                ROOT / "work/source-only-dos/history-storage-bindings-v1.json",
                ROOT / "work/source-only-dos/linker-alias-contract-v1.json"]
packet_mentions = {}
for path in packet_paths:
    raw, packet_pin = dos.pin(path)
    packet_mentions[path.name] = [name for name in NAMES if name in raw.decode("utf-8")]

# Pin every repository source used by the semantic owner proof.
canonical_ref_paths = {row["source"] for bucket in source_refs.values() for row in bucket["canonical"]}
for path_name in canonical_ref_paths:
    source_pins[path_name] = sha((ROOT / path_name).read_bytes())
source_pins["src/root/m1B4E.asm"] = sha(canonical_asm_path.read_bytes())
source_pins["src/S00/m3126.asm"] = sha((ROOT / "src/S00/m3126.asm").read_bytes())
source_pins["src/S01/m3126.asm"] = sha((ROOT / "src/S01/m3126.asm").read_bytes())
source_pins["src/S02/m3126.asm"] = sha((ROOT / "src/S02/m3126.asm").read_bytes())
source_pins["src/S03/m3126.asm"] = sha((ROOT / "src/S03/m3126.asm").read_bytes())

provider_types = {
    "source_path": str(PROVIDER.relative_to(ROOT)).replace("\\", "/"),
    "source_sha256": sha(provider_source.encode("ascii")),
    "object_sha256": sha(owner_build.obj),
    "fresh_compile_profile": "msc600ax /AL /Os /Zi",
    "object_module": owner_omf.name,
    "commdef": owner_omf.communals,
    "segments": segment_live_report(owner_omf),
    "publics": owner_omf.publics,
    "external_scopes": owner_omf.external_scopes,
    "fixups": owner_omf.fixups,
    "assertion": "one near 100-byte COMDEF and zero-length CODE/DATA/CONST/BSS; only debug segments carry bytes",
}

tc_pins = {
    "toolchain_json": pin_file(ROOT / "layout/toolchain.json"),
    "manifest": manifest_pin,
    "msc600ax": {"profile": "msc600ax", "files": compiler.verify_profile("msc600ax")["files"]},
    "masm510": {"profile": "masm510", "files": compiler.verify_profile("masm510")["files"]},
    "dosbox_x": {"path": runner["path"], "sha256": runner["sha256"]},
    "runtimes": [{"path": row["path"], "sha256": row["sha256"]} for row in runtime_rows],
    "linkers": {name: {"executable": tc["linkers"][name]["executable"],
                       "files": tc["linkers"][name]["files"]}
                 for name in ("rtlink400", "rtlink610")},
}
inputs = [pin_file(PROBE), pin_file(PROVIDER), symbols_pin,
          pin_file(ROOT / "src/root/m1B4E.asm"),
          pin_file(ROOT / "src/S00/m3126.asm"), pin_file(ROOT / "src/S01/m3126.asm"),
          pin_file(ROOT / "src/S02/m3126.asm"), pin_file(ROOT / "src/S03/m3126.asm"),
          pin_file(ROOT / "src/S00/m31AD.asm"), pin_file(ROOT / "src/root/m205F.c"),
          pin_file(ROOT / "src/root/m1B73.asm"), manifest_pin]
inputs.extend(pin_file(ROOT / path) for path in sorted(canonical_ref_paths))
inputs.extend(pin_file(path) for path in packet_paths)
for profile_name in ("msc600ax", "masm510"):
    profile = compiler.verify_profile(profile_name)
    for rel, digest in profile["files"].items():
        inputs.append(dos.pin(Path(profile["directory"]) / rel, digest)[1])
inputs.append(dos.pin(Path(runner["path"]), runner["sha256"])[1])
inputs.append(dos.pin(Path(tc["runner"]["path"]), tc["runner"]["sha256"])[1])
for row in runtime_rows:
    inputs.append(dos.pin(Path(row["path"]), row["sha256"])[1])
for linker_name in ("rtlink400", "rtlink610"):
    linker = tc["linkers"][linker_name]
    for rel, digest in linker["files"].items():
        inputs.append(dos.pin(Path(linker["directory"]) / rel, digest)[1])

# Normalize all content/tool pins into a stable path-sorted table. Duplicate
# paths are expected because the owner sources also occur in semantic joins;
# conflicting digests indicate that the input set changed during this run.
normalized_by_path = {}
for pin in inputs:
    normalized = {**pin, "path": pin["path"].replace("\\", "/")}
    previous = normalized_by_path.get(normalized["path"])
    if previous is not None and (previous["sha256"] != normalized["sha256"] or
                                 previous.get("size") != normalized.get("size")):
        raise ValueError("conflicting content pins for " + normalized["path"])
    normalized_by_path[normalized["path"]] = normalized
normalized_inputs = [normalized_by_path[path] for path in sorted(normalized_by_path)]

record_no_debug = not provider_types["segments"]["live_code_data_const_bss"] or all(
    length == 0 for length in provider_types["segments"]["live_code_data_const_bss"].values())
all_runtime_pass = all(case["passed"] for case in cases)
all_aliases_exact = all(row["offset_from_owner"] == 4 * row["slot"] for row in ownership_map)
all_registered_layout_and_sources = (
    len([row for row in ownership_map if row["registered_name"]]) == 23 and
    all(row["layout_symbol_grounding"] and row["canonical_source_refs"]
        for row in ownership_map if row["registered_name"])
)
slot_count = len(ownership_map)
slot_bytes = 4
extent_bytes = slot_count * slot_bytes
extent_exact = (slot_count == 25 and extent_bytes == 100 and
                owner_omf.communals[0]["length"] == extent_bytes and all_aliases_exact)
full_change_pass = (
    field_seg == "_DATA" and field_off == 216 and
    all(not changes for changes in segment_diffs.values()) and
    candidate.segment_lengths == bad_full.segment_lengths and
    candidate.publics == bad_full.publics and
    candidate.groups == bad_full.groups and
    candidate.externals == bad_full.externals and
    candidate.segment_defs == bad_full.segment_defs and
    len(symbolic_field_fixups) == 1 and symbolic_field_fixups[0].get("loc") == "pointer32" and
    symbolic_field_fixups[0].get("target") == "_g_9128" and symbolic_field_fixups[0].get("displacement") == 0 and
    wrong_field_fixups and wrong_field_fixups[0].get("displacement") == 4
)
report = {
    "schema": "simant-dos-callback-table-contract-v3",
    "category": "REVIEWED_SOURCE_STORAGE_CONTRACT",
    "members": [{
        "slot": row["slot"], "name": row["registered_name"],
        "offset_from_owner": row["offset_from_owner"],
        "registered_alias": row["registered_name"] is not None,
    } for row in ownership_map],
    "slots": slot_count,
    "slot_bytes": slot_bytes,
    "extent": extent_bytes,
    "extent_bytes": extent_bytes,
    "extent_exact": extent_exact,
    "all_required_checks_pass": False,
    "probe_source": {"path": str(PROBE.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(PROBE.read_bytes())},
    "provider_source": {"path": str(PROVIDER.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(PROVIDER.read_bytes())},
    "scope": "Review-only source-owned near provider and bounded alias contract; no historical COMDEF TU or order claim.",
    "inputs": normalized_inputs,
    "source_ownership_pins": dict(sorted(source_pins.items())),
    "tool_pins": tc_pins,
    "denied_oracle_reads": denied,
    "provider_fingerprint": provider_types,
    "owner": {
        "candidate_module": "build/source-only-dos/generated/driver_callback_table.c",
        "public_owner": "_driver_callback_table",
        "storage": "near array[25] of far code pointers with old-style unspecified parameter list",
        "extent_bytes": 100,
        "slot_bytes": 4,
        "initializer": "none",
        "ownership_map": ownership_map,
        "optional_source_only_import_join": {
            "status": "not_loaded",
            "required_for_probe": False,
            "source": "build/source-only-dos/build-report.json is intentionally not read or pinned",
            "accepted_storage_candidates": "not joined; absence is not asserted",
            "declaration_contexts": "not joined; absence is not asserted",
        },
        "existing_packet_mentions": packet_mentions,
        "alias_contract": "the 23 non-null layout/symbols.json entries map to owner+4*slot; test-only aliases occupy unnamed slots 13 and 22",
        "source_consumer_basis": "exact identifier occurrences scanned directly from canonical src/**/*.c and src/**/*.asm files",
        "historical_address_is_source_xref_only": True,
        "registry_geometry": {"segment": "0x55B3", "start_offset": "0x9128",
                              "alias_formula": "registered slot n => DGROUP near owner + 4*n",
                              "source_pointer_frame": "existing m1B4E DGROUP offset+segment fixup to _g_9128"},
        "source_extent_basis": ["m1B4E reset: 0x19 iterations x 2 words per slot", "m1B4E copy: 0x32 words", "S00-S03 each contribute 25 dword dispatch entries"],
        "not_neighbor_gap_sized": True,
    },
    "admission_sketch": {
        "status": "review-only; no canonical/tool/promotion edits",
        "candidate_provider_source": str(PROVIDER.relative_to(ROOT)).replace("\\", "/"),
        "candidate_generated_module": "build/source-only-dos/generated/driver_callback_table.c",
        "provider_source_shape": provider_source.strip(),
        "provider_source_sha256": sha(PROVIDER.read_bytes()),
        "fresh_object_sha256": sha(owner_build.obj),
        "expected_omf_owner": owner_omf.communals,
        "bounded_aliases": [{
            "public": row["registered_name"], "owner": "_driver_callback_table",
            "byte_offset": row["offset_from_owner"], "slot": row["slot"],
            "layout_xref_grounding": row["layout_symbol_grounding"],
            "optional_import_join": row["optional_import_join"],
        } for row in ownership_map if row["registered_name"]],
        "test_only_unnamed_slots": [
            {"slot": row["slot"], "byte_offset": row["offset_from_owner"], "alias": row["test_alias"]}
            for row in ownership_map if row["registered_name"] is None
        ],
        "existing_pointer_binding": {
            "module": "src/root/m1B4E.asm", "public_field": "_g_3DF8",
            "source_declaration": "extrn _g_9128:byte; _g_3DF8 dd _g_9128",
            "object_segment": field_seg, "object_offset": field_off, "fixups": symbolic_field_fixups,
            "source_already_symbolic": True,
            "compile_frame_group": candidate.groups,
        },
        "historical_comdef_translation_unit_or_order_claimed": False,
    },
    "runtime": {
        "cases": cases,
        "test_checks": ["MSC main startup bytewise near-zero", "all 25 aliases including unnamed test-only slots",
                        "_g_3DF8 offset+segment relocation", "100-byte reset/copy", "first/last slot values",
                        "C-byte and ASM-word overlap at g_912C", "four one-past canaries"],
        "negative_controls": ["g_9188 alias at +94", "initialized nonzero owner", "test _g_3DF8 points to _g_9128+4"],
        "runtime_toolchain": "MSC 6.00AX startup + LLIBCR/LIBH + RTLink 4.00/6.10 + DOSBox-X",
        "all_required_cases_pass": all_runtime_pass,
    },
    "full_module_m1B4E": full_module,
    "checks": {
        "fresh_provider_is_one_100_byte_near_comdef": owner_omf.communals == [{
            "name": "_driver_callback_table", "kind": "near", "type_index": owner_omf.communals[0]["type_index"], "length": 100}],
        "exact_25_slot_by_4_byte_extent": extent_exact,
        "provider_has_no_live_code_data_const_bss": record_no_debug,
        "all_25_alias_slots_are_exact": all_aliases_exact,
        "all_23_layout_symbols_join_to_canonical_source_consumers": all_registered_layout_and_sources,
        "all_four_provider_tables_have_25_entries": all(len(x) == 25 for x in dispatch.values()),
        "all_RTLink_positive_and_negative_cases_expected": all_runtime_pass,
        "full_m1B4E_symbolic_fixup_and_field_review": full_change_pass,
        "ignored_source_only_build_report_is_not_an_input": not any(
            "build/source-only-dos/build-report.json" in pin["path"].replace("\\", "/")
            for pin in normalized_inputs),
        "no_oracle_input_read": not denied,
    },
}
report["all_required_checks_pass"] = all(report["checks"].values())
CONTRACT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "all_required_checks_pass": report["all_required_checks_pass"],
    "checks": report["checks"],
    "provider_commdef": owner_omf.communals,
    "m1B4E_field": full_module["field"],
    "segment_byte_diffs": segment_diffs,
    "fixup_delta": fixup_delta,
    "cases": [{k: c[k] for k in ("linker", "case", "expected", "actual", "passed")} for c in cases],
}, indent=2))
raise SystemExit(0 if report["all_required_checks_pass"] else 1)
