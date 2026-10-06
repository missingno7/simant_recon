"""Bounded functional owner for the fixed clip rectangle destination.

Every write to fd_50F6_3C14 is a whole sentinel-terminated rectangle list.
The source census proves an inductive 256-record bound for every execution
prefix before the first Punt entry.  Original instructions retain the
255-record positive, the 256-record fatal boundary and a returning-Punt
contrast which writes beyond the owner and is outside the admitted domain.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
import types
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError("Run witness checks without Python -O")
import canonical
import csrc

ORACLE_PIN = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"
OWNER_KEY = "source-owned:clip-rect-buffer"
OWNER_DECLARATION = ("struct Rect { int left ; int top ; int right ; int bottom ; } ; "
                     "struct Rect far fd_50F6_3C14 [ 256 ] ;")
RECORDS = 256
RECORD_BYTES = 8
SENTINEL = "0x8000"

# Each destination writer, the bound that dominates its copy, and its source.
DESTINATION_WRITERS = {
    "clip_SetWin": [
        "g_5746 = fd_50F6_3B60 [ win >> 8 ]",
        "_fmemcpy ( fd_50F6_3C14 , p , size )",
    ],
    "f_1E57_0296": [
        "g_5746 = g_574A",
        "_fmemcpy ( fd_50F6_3C14 , p , size )",
    ],
    "clip_SubInclude": [
        "n = 1 ; * p = * r ;",
        "if ( ( n = p - buf ) >= 256 ) Punt ( \"CL074:Temp clip overflow in SubInclude\" )",
        "g_5AAC = fd_50F6_3C14 ; _fmemcpy ( g_5AAC , f_171C_1B84 ( h ) , ( n + 1 ) << 3 )",
    ],
    "f_1E57_08F5": [
        "for ( n = 0 ; r -> top != ( int ) 0x8000 ; p ++ , r ++ , n ++ ) * p = * r ;",
        "if ( ( n = p - buf ) >= 256 ) Punt ( \"CL074:Temp clip overflow in SubInclude\" )",
        "g_5AAC = fd_50F6_3C14 ; _fmemcpy ( g_5AAC , f_171C_1B84 ( h ) , ( n + 1 ) << 3 )",
    ],
    "clip_SubExclude": [
        "if ( ( n = p - buf ) >= 256 ) Punt ( \"CL074:Temp clip overflow in SubExclude\" )",
        "g_5AAC = fd_50F6_3C14 ; _fmemcpy ( g_5AAC , f_171C_1B84 ( h ) , ( n + 1 ) << 3 )",
    ],
    "f_1E57_0C2D": [
        "if ( ( n = p - buf ) >= 256 ) Punt ( \"CL174:Temp clip overflow in SubExclude\" )",
        "n = 1 ; * buf = * r ;",
        "g_5AAC = fd_50F6_3C14 ; _fmemcpy ( g_5AAC , buf , ( n + 1 ) << 3 )",
    ],
    "clip_Pop": [
        "fd_50F6_3B5C = node [ 0 ]",
        "_fmemcpy ( fd_50F6_3C14 , g_5AAC , size )",
    ],
    "f_1E57_0FDC": [
        "g_5AAC = fd_50F6_3C14 ; f_1D8E_003F ( r , & g_5A9C , fd_50F6_3C14 , 0L )",
    ],
}

# Producers of the lists copied by clip_SetWin, f_1E57_0296 and clip_Pop.
SOURCE_LIST_PRODUCERS = {
    "f_1E57_038E": [
        "* list = g_5A9C ; list [ 1 ] . top = 0x8000 ;",
        "if ( count >= 256 ) Punt ( \"C097: Clip overflow %d\" , count )",
        "if ( count >= 256 ) Punt ( \"C098: Clip overflow %d\" , count )",
        "if ( n >= 256 ) Punt ( \"C099: Clip overflow %d\" , n )",
        "g_574A = f_171C_1B2C ( g_574A , n , 1 )",
    ],
    "clip_Push": [
        "_fmemcpy ( node + 2 , g_5AAC , size )",
        "if ( ++ g_5756 > 20 ) Punt ( \"Error CL98463: Pushed it too far\" )",
    ],
}

# In-mode rectangle production: at most one record per input plus sentinel.
HELPER_FACTS = {
    "f_1D8E_02BD": [
        "res = f_1D8E_003F ( list , c , in , out ) ; if ( out ) out = res ; else in = res ;",
        "* in = * c ; res = in + 1 ;",
    ],
    "f_1D8E_003F": [
        "if ( in ) * in ++ = * r ;",
        "* in ++ = t ; in -> top = RECT_END ; return in ;",
    ],
}

# Complete non-1E57 references to the copied list owners and pointer.
EXPECTED_FOREIGN_CLIP_POINTER_REFERENCES = {
    "src/root/m1B73.asm": ["lea di, _g_5AAC", "pop word ptr _g_5AAC", "pop word ptr _g_5AAE"],
    "src/root/m1C62.c": ["g_5AAC = 0 ;", "g_5AAC = 0 ;"],
    "src/S10/m35F5.c": ["saved = g_5AAC ;", "g_5AAC = 0 ;", "g_5AAC = saved ;"],
}


# Read-only users: clip iteration and first-record emptiness tests.
CLIP_POINTER_READERS = ("src/root/m1D8E.c", "src/root/m21FA.c", "src/S00/m31AD.asm",
                        "src/S01/m3126.asm", "src/S02/m3126.asm", "src/S03/m3126.asm",
                        "src/S22/m39C7.c")
POINTER_STORE = re.compile(r"g_5AAC \[ [^\]]+ \] =[^=]|g_5AAC\s*=[^=]|g_5AAC\s*(?:\+\+|--|[-+]=)"
                           r"|^(?!cmp |push |test )\w+ (?:d?word ptr )?_g_5AA[CE]\b")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized(text: str) -> str:
    return " ".join(t.text for t in csrc.tokenize(text)
                    if t.kind not in {"ws", "nl", "cmt"})


def function_text(text: str, name: str) -> str:
    fn = csrc.Source(text).function(name)
    return normalized(text[fn.head_s:fn.body.e])


def inventory(program_override=None, source_overrides=None):
    program = program_override or canonical.load()
    source_overrides = source_overrides or {}
    texts = {}
    for module in program["modules"]:
        raw = source_overrides.get(module["source"])
        if raw is None:
            raw = (ROOT / module["source"]).read_bytes()
        if sha(raw) != module["source_sha256"]:
            raise ValueError("canonical source pin differs: " + module["source"])
        texts[module["source"]] = raw.decode("latin1")
    return texts, program


def enclosing(text: str, offset: int) -> str:
    for fn in csrc.Source(text).functions():
        if fn.head_s <= offset < fn.body.e:
            return fn.name
    return "<file scope>"


def census(texts: dict[str, str], name: str) -> list[list[object]]:
    rows = []
    pattern = re.compile(r"(?<![A-Za-z0-9_@])_?" + re.escape(name) + r"(?![A-Za-z0-9_])")
    for path, text in sorted(texts.items()):
        if path.endswith(".asm"):
            for line_no, line in enumerate(text.splitlines(), 1):
                code = line.split(";", 1)[0]
                if pattern.search(code):
                    rows.append([path, line_no, "<asm>", code.strip()])
            continue
        for token in csrc.tokenize(text):
            if token.kind == "id" and token.text == name:
                rows.append([path, text.count("\n", 0, token.s) + 1,
                             enclosing(text, token.s), token.text])
    return rows


def statement_census(texts: dict[str, str], name: str) -> dict[str, list[str]]:
    """Every foreign statement/instruction naming ``name`` outside root:1E57."""
    found: dict[str, list[str]] = {}
    for path, text in sorted(texts.items()):
        if path == "src/root/m1E57.c":
            continue
        if path.endswith(".asm"):
            for line in text.splitlines():
                code = " ".join(line.split(";", 1)[0].split())
                # The far pointer's segment word has the registered alias g_5AAE.
                if re.search(r"(?<![A-Za-z0-9_])_(?:" + name + r"|g_5AAE)(?![A-Za-z0-9_])", code) \
                        and not code.startswith("extrn"):
                    found.setdefault(path, []).append(code)
            continue
        for statement in normalized(text).split(";"):
            if re.search(r"(?<![A-Za-z0-9_])" + name + r"(?![A-Za-z0-9_])", statement) \
                    and "extern" not in statement:
                found.setdefault(path, []).append(statement.strip().split("{")[-1].split("}")[-1].strip() + " ;")
    return found


def static_facts(texts: dict[str, str], program: dict) -> dict:
    modules = {m["key"]: m for m in program["modules"]}
    provider = modules.get(OWNER_KEY)
    if provider is not None:
        expected = [{"name": "_fd_50F6_3C14", "kind": "far", "length": RECORDS * RECORD_BYTES,
                     "count": RECORDS, "element_size": RECORD_BYTES}]
        assert provider["storage_contract"]["communals"] == expected
        assert normalized(texts[provider["source"]]).endswith(OWNER_DECLARATION)
    clip = texts["src/root/m1E57.c"]
    helper = texts["src/root/m1D8E.c"]
    definitions = {}
    for group, source in ((DESTINATION_WRITERS, clip), (SOURCE_LIST_PRODUCERS, clip),
                          (HELPER_FACTS, helper)):
        for name, needles in group.items():
            body = function_text(source, name)
            for needle in needles:
                assert needle in body, (name, needle)
            definitions[name] = sha(body.encode())
    # Every overflow check precedes its destination copy.
    for name in ("clip_SubInclude", "f_1E57_08F5", "clip_SubExclude", "f_1E57_0C2D"):
        body = function_text(clip, name)
        assert body.index(">= 256 ) Punt") < body.index("g_5AAC = fd_50F6_3C14 ;"), name
    body = body_038E = function_text(clip, "f_1E57_038E")
    assert body.index("C098") < body.index("fd_50F6_3B60 [ next >> 8 ] = f_171C_1A9E")
    assert body.index("C099") < body.index("g_574A = f_171C_1B2C")
    assert "fd_50F6_3C14" not in body

    rows = census(texts, "fd_50F6_3C14")
    writers = sorted({row[2] for row in rows if row[0] == "src/root/m1E57.c"} - {"<file scope>"})
    assert writers == sorted(DESTINATION_WRITERS), writers
    files = {row[0] for row in rows}
    allowed = {"src/root/m1E57.c"} | ({provider["source"]} if provider else set())
    assert files == allowed, files

    handle_rows = census(texts, "fd_50F6_3B60")
    assert {r[0] for r in handle_rows} == {"src/root/m1E57.c", "src/state/window-clip-handles.c"}
    handle_writers = sorted({r[2] for r in handle_rows if r[0] == "src/root/m1E57.c"} - {"<file scope>"})
    assert handle_writers == ["clip_SetWin", "f_1E57_0239", "f_1E57_038E"], handle_writers
    # Only f_1E57_038E stores list handles, and only after its overflow checks.
    stores = re.findall(r"fd_50F6_3B60 \[ [^\]]+ \] = f_171C_1A9E", normalized(clip))
    assert len(stores) == 2 and all(s in body_038E for s in stores)
    stack_rows = census(texts, "fd_50F6_3B5C")
    assert {r[0] for r in stack_rows} == {"src/root/m1E57.c", "src/state/ui-resource-scalars.c"}
    assert sorted({r[2] for r in stack_rows if r[0] == "src/root/m1E57.c"} - {"<file scope>"}) == ["clip_Pop", "clip_Push"]
    out_rows = census(texts, "g_574A")
    assert {r[0] for r in out_rows} == {"src/root/m1E57.c"}

    foreign = statement_census(texts, "g_5AAC")
    assert set(foreign) == set(EXPECTED_FOREIGN_CLIP_POINTER_REFERENCES) | \
        set(CLIP_POINTER_READERS) | {"src/state/clip-pointer.c"}, sorted(foreign)
    for path, expected in EXPECTED_FOREIGN_CLIP_POINTER_REFERENCES.items():
        for needle in expected:
            assert any(needle in item for item in foreign[path]), (path, needle)
    for reader in CLIP_POINTER_READERS:
        assert not any(POINTER_STORE.search(item) for item in foreign[reader]), reader
        if reader.endswith(".asm"):
            assert all(item in ("mov ax, word ptr _g_5AAE", "lds si, dword ptr _g_5AAC")
                       for item in foreign[reader]), reader
    # The cursor callback temporarily selects the one-record screen list.
    cursor = [" ".join(l.split(";", 1)[0].split()) for l in texts["src/root/m1B73.asm"].splitlines()]
    at = cursor.index("lea di, _g_5AAC")
    assert cursor[at + 1:at + 9] == [
        "push word ptr [di]", "push word ptr [di+2]", "push word ptr _fd_55B3_3DE6",
        "push word ptr _fd_55B3_3DE8", "mov cx, DGROUP", "mov word ptr [di+2], cx",
        "mov cx, offset DGROUP:_g_5A9C", "mov word ptr [di], cx"]
    # The one assembly list walk only compares and advances SI until it restores DS.
    lines = [" ".join(l.split(";", 1)[0].split()) for l in texts["src/S00/m31AD.asm"].splitlines()]
    start = lines.index("lds si, dword ptr _g_5AAC")
    walk = lines[start + 1:start + 1 + lines[start + 1:].index("pop ds")]
    assert all(not re.match(r"(?!cmp |test )\w+ (?:d?word |byte )?(?:ptr )?\[si", l) for l in walk)
    assert sum("[si" in l for l in walk) >= 4
    helper_body = normalized(helper)
    assert not re.search(r"clip -> \w+ (?:=[^=]|\+\+|--)|\* clip =[^=]", helper_body)

    callers = [row for row in census(texts, "f_1E57_08F5")
               if row[0] != "src/root/m1E57.c" and row[2] != "<file scope>"]
    assert [(r[0], r[2]) for r in callers] == [("src/root/m0250.c", "f_0250_5058")]
    caller = function_text(texts["src/root/m0250.c"], "f_0250_5058")
    for needle in ("struct Rect rects [ 3 ] ;", "rects [ 2 ] . top = 0x8000 ;",
                   "f_1E57_08F5 ( rects ) ;"):
        assert needle in caller
    definitions["f_0250_5058"] = sha(caller.encode())

    guard = normalized(texts["src/root/m1C62.c"])
    assert "static int g_54F8 = 0 ;" in guard
    guard_rows = census(texts, "g_54F8")
    assert {r[0] for r in guard_rows} == {"src/root/m1C62.c"}
    assert {r[2] for r in guard_rows} == {"<file scope>", "Punt"}
    punt = function_text(texts["src/root/m1C62.c"], "Punt")
    assert "if ( g_54F8 == 0 ) { g_54F8 = 1 ;" in punt
    definitions["Punt"] = sha(punt.encode())

    return {
        "function_definition_sha256": definitions,
        "destination_census": {"rows": rows,
                               "sha256": sha(json.dumps(rows, separators=(",", ":")).encode())},
        "destination_writers": sorted(DESTINATION_WRITERS),
        "source_list_owners": {"window_clip_handles": handle_writers,
                               "clip_stack": ["clip_Pop", "clip_Push"],
                               "active_clip_output": ["src/root/m1E57.c"]},
        "foreign_clip_pointer_writers": {k: v for k, v in sorted(foreign.items())
                                         if k in EXPECTED_FOREIGN_CLIP_POINTER_REFERENCES},
        "include_list_callers": [["src/root/m0250.c", "f_0250_5058", 2]],
    }


# ---------------------------------------------------------------- original controls

def original_controls() -> list[dict]:
    import behavior as b
    import exe
    import functions

    image = exe.load()
    if image.sha256 != ORACLE_PIN or sha(image.path.read_bytes()) != ORACLE_PIN:
        raise ValueError("reviewed oracle pin differs")
    destination = b.symbol_address("fd_50F6_3C14")
    assert destination == 0x50F60 + 0x3C14
    guard_address = 0x55B30 + 0x54F8
    punt = b.symbol_address("Punt")
    fixture_list = 0x60000
    heap = 0x70000
    handles = 0x68000

    def execute(records: int, guard: int) -> dict:
        m = b.Machine(types.SimpleNamespace(function=functions.get("clip_SubExclude"),
            vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors}))
        allocs: dict[int, dict] = {}
        events: list[dict] = []
        stopped = False

        def far(address):
            return (address & 15, address >> 4)

        def alloc(m, args):
            size = args[0] | args[1] << 16
            tag = m.read(args[4] * 16 + args[3], 20).split(b"\0", 1)[0].decode("ascii")
            handle = handles + 4 * len(allocs)
            address = heap + 0x1000 * len(allocs)
            allocs[handle] = dict(address=address, size=size, tag=tag)
            m.write(address, b"\x7a" * (size + 64))
            m.write(handle, struct.pack("<HH", *far(address)))
            events.append(dict(event="allocate", tag=tag, bytes=size))
            return far(handle)

        def lock(m, args):
            return far(allocs[args[1] * 16 + args[0]]["address"])

        def resize(m, args):
            events.append(dict(event="resize", bytes=args[2] | args[3] << 16))
            return (args[0], args[1])

        def copy(m, args):
            dst, src, size = args[1] * 16 + args[0], args[3] * 16 + args[2], args[4]
            m.write(dst, m.read(src, size))
            events.append(dict(event="copy", destination_offset=dst - destination, bytes=size))
            return (args[0], args[1])

        def scratch(cpu, access, address, size, value, user):
            for row in allocs.values():
                end = row["address"] + row["size"]
                if address < end + 64 and address + size > end:
                    events.append(dict(event="scratch-overrun", tag=row["tag"],
                                       displacement=address - row["address"], bytes=size))

        def code(cpu, address, size, user):
            nonlocal stopped
            if address == punt:
                stack = m.reg("ss") * 16 + m.reg("sp")
                off, seg = struct.unpack("<2H", m.read(stack + 4, 4))
                events.append(dict(event="Punt-entry", guard=m.word(guard_address),
                    message=m.read(seg * 16 + off, 48).split(b"\0", 1)[0].decode("ascii")))
                if m.word(guard_address) == 0:
                    stopped = True
                    cpu.emu_stop()

        m.cpu.hook_add(b.uc.UC_HOOK_MEM_WRITE, scratch)
        m.cpu.hook_add(b.uc.UC_HOOK_CODE, code)
        rects = b"".join(struct.pack("<4h", 2 * i, 0, 2 * i + 1, 1) for i in range(records))
        clipped = struct.pack("<4h", 0, 100, 10, 110)
        callbacks = {"f_171C_1A9E": b.Callback(5, alloc), "f_171C_1B84": b.Callback(2, lock),
                     "f_171C_1BBA": b.Callback(2, lock), "f_171C_1C0A": b.Callback(2, lambda m, a: None),
                     "f_171C_1B2C": b.Callback(5, resize), "__fmemcpy": b.Callback(5, copy)}
        writes = [(fixture_list, rects + struct.pack("<4h", 0, -32768, 0, 0)),
                  (fixture_list + 0x4000, clipped),
                  (b.symbol_address("g_5AAC"), struct.pack("<HH", 0, fixture_list >> 4)),
                  (b.symbol_address("g_5742"), bytes(8)),
                  (guard_address, b.words(guard)),
                  (destination, b"\x5c" * (RECORDS * RECORD_BYTES + 64))]
        try:
            m.run(b.Case(f"subexclude-{records}-guard{guard}", args=[0, (fixture_list + 0x4000) >> 4],
                writes=writes, callbacks=callbacks, return_kind="void",
                max_instructions=2_000_000, max_blocks=400_000, observe_at_calls=False))
        except b.ExecutionError:
            if not stopped:
                raise
        copies = [e for e in events if e["event"] == "copy" and e["destination_offset"] == 0]
        fatal = [e for e in events if e["event"] == "Punt-entry"]
        written = copies[0]["bytes"] if copies else 0
        tail = m.read(destination + RECORDS * RECORD_BYTES, 8)
        tops = [struct.unpack("<h", m.read(destination + i * RECORD_BYTES + 2, 2))[0]
                for i in range(RECORDS + 1)]
        sentinel = tops.index(-32768) if written and -32768 in tops else None
        if sentinel is not None:
            assert m.read(destination, sentinel * RECORD_BYTES) == rects[:sentinel * RECORD_BYTES]
        return dict(input_records=records, incoming_guard=guard, completed=m.completed,
                    destination_sentinel_record=sentinel,
                    stopped_at_first_fatal_entry=stopped,
                    Punt_entries=[dict(guard=e["guard"], message=e["message"]) for e in fatal],
                    destination_bytes_written=written,
                    beyond_owner_bytes=max(0, written - RECORDS * RECORD_BYTES),
                    owner_tail_unchanged=tail == b"\x5c" * 8,
                    temporary_overrun_before_fatal=any(e["event"] == "scratch-overrun" and e["tag"] == "subexclude"
                                                       for e in events[:events.index(fatal[0])]) if fatal else False)

    cases = [execute(255, 0), execute(256, 0), execute(256, 1)]
    positive, fatal, returning = cases
    assert positive["completed"] and not positive["Punt_entries"]
    assert positive["destination_bytes_written"] == RECORDS * RECORD_BYTES
    assert positive["owner_tail_unchanged"] and positive["beyond_owner_bytes"] == 0
    assert positive["destination_sentinel_record"] == RECORDS - 1
    assert returning["destination_sentinel_record"] == RECORDS
    assert fatal["stopped_at_first_fatal_entry"] and fatal["destination_bytes_written"] == 0
    assert fatal["Punt_entries"] == [dict(guard=0, message="CL074:Temp clip overflow in SubExclude")]
    assert fatal["owner_tail_unchanged"]
    assert returning["completed"] and returning["Punt_entries"] == [
        dict(guard=1, message="CL074:Temp clip overflow in SubExclude")]
    assert returning["destination_bytes_written"] == (RECORDS + 1) * RECORD_BYTES
    assert returning["beyond_owner_bytes"] == RECORD_BYTES and not returning["owner_tail_unchanged"]
    return cases


def collect(program_override=None, source_overrides=None, *, run_original=True) -> dict:
    texts, program = inventory(program_override, source_overrides)
    facts = {
        "schema": "simant-clip-rect-owner-v1",
        "scope": ("Every execution prefix before the first Punt entry. Overflow diagnostics, "
                  "returning-Punt continuation, generation reachability, the heap-temporary "
                  "pre-check overrun, original producer TU and historical placement are excluded."),
        "program_sha256": sha(((json.dumps(program, indent=2) + "\n").encode())
                              if program_override is not None
                              else (ROOT / "src/program.json").read_bytes()),
        **static_facts(texts, program),
        "owner": {"records": RECORDS, "record_bytes": RECORD_BYTES,
                  "extent_bytes": RECORDS * RECORD_BYTES,
                  "maximum_live_records": RECORDS - 1, "sentinel_records": 1,
                  "initialization": "MSC far communal zero initialization; every reader is preceded by a whole-list write"},
        "historical_extent": "UNCLAIMED",
    }
    if run_original:
        facts["original_boundary_controls"] = original_controls()
    return facts


def check(run_original=True) -> dict:
    actual = collect(run_original=run_original)
    expected = json.loads((Path(__file__).parent / "facts.json").read_text())
    if not run_original:
        expected.pop("original_boundary_controls", None)
    if actual != expected:
        raise ValueError("clip owner proof differs from reviewed facts")
    return actual


if __name__ == "__main__":
    check()
    print("PASS: 256-record clip destination owner before the first Punt entry; returning-Punt contrast retained")
