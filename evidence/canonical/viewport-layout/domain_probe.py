"""Replay the supported profile-8 viewport-input domain proof.

The source tree, resource databases, and hash-locked DOS executable are read at
runtime. The only runtime output is a fresh temporary directory under build/;
the original mickey callback is executed as a deliberately out-of-domain
negative control.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import struct
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True


def find_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "src/program.json").is_file() and (parent / "tools/context.py").is_file():
            return parent
    raise RuntimeError("cannot locate repository containing src/program.json and tools/context.py")


ROOT = find_root()
PACKAGE = Path(__file__).resolve().parent
PACKET = PACKAGE if (PACKAGE / "resources_probe.py").is_file() else ROOT / "evidence/canonical/viewport-layout"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "build/deps/unicorn"))
sys.path.insert(0, str(PACKET))

import capstone  # noqa: E402
import behavior as behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import resources_probe  # noqa: E402


SCHEMA = "viewport-input-domain-facts-v2"
_UNICORN_KEEPALIVE = []
RELEVANT = (
    "src/root/m1B73.asm",
    "src/S20/m39F1.c",
    "src/root/m15F8.c",
    "src/S17/m384C.c",
    "src/root/m218D.c",
    "src/root/m00BA.c",
    "src/root/m205F.c",
    "src/S26/m39C7.c",
    "src/root/m1FD2.c",
    "src/root/m1CE2.c",
    "src/root/m2505.c",
    "src/root/m20E8.c",
    "src/root/m23AE.c",
    "src/root/m22BF.c",
    "src/root/m00F8.c",
    "src/root/m015B.c",
    "src/root/m205F.c",
    "src/S09/m35F5.c",
    "src/S10/m35F5.c",
    "src/S16/m384C.c",
    "src/root/m0250.c",
    "src/state/screen-clip-list.c",
    "src/state/mouse-words.c",
    "src/S00/m31AD.asm",
    "src/S00/m31AD_2AB4.asm",
)
MOUSE_FUNCTIONS = (
    "f_1B73_0046", "f_1B73_03EE", "f_1B73_0445", "f_1B73_051F",
    "f_1B73_0747", "f_1B73_09E9", "f_1B73_09F7", "f_1B73_09FF",
    "f_1B73_0C80",
)
CONTRACT_URL = (
    "https://www.bitsavers.org/pdf/microsoft/mouse/"
    "Microsoft_-_Microsoft_Mouse_Programmers_Reference_2nd_1991.pdf"
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_source(path: str, overrides: dict[str, bytes | str] | None = None) -> bytes:
    if overrides and path in overrides:
        value = overrides[path]
        return value.encode("latin1") if isinstance(value, str) else value
    return (ROOT / path).read_bytes()


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def asm_procedure(source: str, name: str) -> str:
    start = re.search(rf"(?im)^\s*{re.escape(name)}\s+proc\b", source)
    end = re.search(rf"(?im)^\s*{re.escape(name)}\s+endp\b", source)
    if not start or not end or end.start() <= start.start():
        raise AssertionError(f"missing assembly procedure {name}")
    return source[start.start():end.end()]


def c_function(source: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*(?:void|int|char|long|short|unsigned|struct\s+\w+)\b[^;{{}}]*\b{re.escape(name)}\s*\([^;{{}}]*\)\s*{{", source)
    if not match:
        raise AssertionError(f"missing C function {name}")
    opening = source.find("{", match.start())
    depth = 0
    for pos in range(opening, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise AssertionError(f"unterminated C function {name}")


def c_block(source: str, marker: str) -> str:
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing source marker {marker!r}")
    opening = source.find("{", start)
    if opening < 0:
        raise AssertionError(f"missing block after {marker!r}")
    depth = 0
    for pos in range(opening, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos + 1]
    raise AssertionError(f"unterminated source block {marker!r}")


def strip_comments(raw: bytes, suffix: str) -> str:
    text = raw.decode("latin1")
    if suffix.lower() == ".asm":
        return "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def all_sources(overrides: dict[str, bytes | str] | None = None) -> dict[str, bytes]:
    files = sorted(p for p in (ROOT / "src").rglob("*") if p.is_file() and p.suffix.lower() in (".c", ".asm"))
    result = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in files}
    if overrides:
        for rel, value in overrides.items():
            result[rel] = value.encode("latin1") if isinstance(value, str) else value
    return result


def inventory_pins(paths: tuple[str, ...], overrides: dict[str, bytes | str] | None) -> dict[str, str]:
    program = json.loads((ROOT / "src/program.json").read_bytes())
    inventory = {row["source"]: row["source_sha256"] for row in program["modules"]}
    pins: dict[str, str] = {}
    for rel in paths:
        if rel not in inventory:
            raise AssertionError(f"{rel} is absent from src/program.json")
        current = read_source(rel, overrides)
        if not overrides or rel not in overrides:
            if sha(current) != inventory[rel]:
                raise AssertionError(f"program inventory mismatch for {rel}")
        pins[rel] = sha(current)
    return dict(sorted(pins.items()))


def instruction_rows(image, name: str) -> tuple[dict, list[dict]]:
    row = functions.get(name)
    linear = row["seg"] * 16 + row["off"]
    raw = image.read(row["unit"], linear, row["size"])
    dis = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    insns = list(dis.disasm(raw, linear))
    rows = [{"at": f"{ins.address:05x}", "mnemonic": ins.mnemonic, "operands": ins.op_str}
            for ins in insns]
    return ({k: row[k] for k in ("name", "unit", "seg", "off", "size")}, rows)


def require_instruction(rows: list[dict], mnemonic: str, operands: str) -> None:
    target = (mnemonic.lower(), norm(operands))
    if not any((row["mnemonic"].lower(), norm(row["operands"])) == target for row in rows):
        raise AssertionError(f"missing original instruction {target}")


def comments_and_sites(sources: dict[str, bytes], needle: str) -> list[dict]:
    found = []
    for rel, raw in sorted(sources.items()):
        code = strip_comments(raw, Path(rel).suffix)
        for line_no, line in enumerate(code.splitlines(), 1):
            if needle.lower() in line.lower():
                found.append({"path": rel, "line": line_no, "text": line.strip()})
    return found


def c_call_sites(sources: dict[str, bytes], name: str) -> list[dict]:
    found = []
    pattern = re.compile(rf"\b{re.escape(name)}\s*\(")
    for rel, raw in sorted(sources.items()):
        if Path(rel).suffix.lower() != ".c":
            continue
        code = strip_comments(raw, ".c")
        for line_no, line in enumerate(code.splitlines(), 1):
            match = pattern.search(line)
            if not match:
                continue
            prefix = line[:match.start()].strip()
            if re.search(r"\b(?:extern|void|int|char|long|short)\b", prefix):
                continue
            args = line[match.end():]
            arg = re.match(r"\s*(0x[0-9a-fA-F]+|\d+|NULL|0L)?", args)
            found.append({"path": rel, "line": line_no,
                          "first_arg": arg.group(1) if arg else None,
                          "text": line.strip()})
    return found


def call_sites(sources: dict[str, bytes], name: str) -> list[dict]:
    result = c_call_sites(sources, name)
    asm_pat = re.compile(rf"\bcall\b[^\n]*_?{re.escape(name)}\b", re.I)
    for rel, raw in sorted(sources.items()):
        if Path(rel).suffix.lower() != ".asm":
            continue
        code = strip_comments(raw, ".asm")
        for line_no, line in enumerate(code.splitlines(), 1):
            if asm_pat.search(line):
                result.append({"path": rel, "line": line_no, "first_arg": None, "text": line.strip()})
    return sorted(result, key=lambda item: (item["path"], item["line"]))


def cursor_writers(sources: dict[str, bytes]) -> dict[str, list[dict]]:
    result = []
    c_write = re.compile(r"(?<![\w])(?:\+\+\s*)?(g_912[24])\s*(?:=|\+=|-=|\+\+|--)")
    asm_write = re.compile(r"\b(?:mov|xchg|add|sub|inc|dec)\s+(?:word\s+ptr\s+)?(?:es:)?_g_(912[24])\b", re.I)
    for rel, raw in sorted(sources.items()):
        suffix = Path(rel).suffix.lower()
        code = strip_comments(raw, suffix)
        proc = ""
        for line_no, line in enumerate(code.splitlines(), 1):
            if suffix == ".asm":
                start = re.match(r"\s*(_f_\w+)\s+proc\b", line, re.I)
                end = re.match(r"\s*_f_\w+\s+endp\b", line, re.I)
                if start:
                    proc = start.group(1)
                match = asm_write.search(line)
                if match:
                    result.append({"global": "g_" + match.group(1), "path": rel, "line": line_no,
                                   "owner": proc, "text": line.strip()})
                if end:
                    proc = ""
            elif suffix == ".c":
                match = c_write.search(line)
                if match:
                    result.append({"global": match.group(1), "path": rel, "line": line_no,
                                   "owner": "C", "text": line.strip()})
    return {name: [row for row in result if row["global"] == name]
            for name in ("g_9122", "g_9124")}


def variable_mentions(sources: dict[str, bytes], tokens: tuple[str, ...]) -> dict[str, list[dict]]:
    return {token: comments_and_sites(sources, token) for token in tokens}


def mickey_control(image) -> dict:
    fn = functions.get("f_1B73_03EE")
    pair = type("OriginalPair", (), {})()
    pair.function = fn
    pair.vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector for vector in image.vectors}
    pair.delegate = {}
    machine = behavior.Machine(pair)

    def addr(name: str) -> int:
        return behavior.symbol_address(name)

    def signed(value: int) -> int:
        value &= 0xFFFF
        return value - 0x10000 if value >= 0x8000 else value

    initial = [
        (fn["seg"] * 16 + 8, behavior.words(1)),
        (addr("g_3DB2"), behavior.words(640)),
        (addr("g_3DB4"), behavior.words(480)),
        (addr("g_432C"), behavior.words(0)),
        (addr("g_432E"), behavior.words(0)),
        (addr("g_9122"), behavior.words(408)),
        (addr("g_9124"), behavior.words(369)),
        (addr("g_5FF9"), behavior.words(0)),
    ]
    entry = {"seg": fn["seg"], "off": fn["off"]}
    machine.run(behavior.Case(label="mickey-first", writes=initial,
        registers={"ax": 1, "bx": 1, "cx": 408, "dx": 0, "si": 0, "di": 0xFD1C},
        return_kind="void"), original_entry=entry)
    first_y = signed(machine.word(addr("g_9124")))
    first_previous_y = signed(machine.word(addr("g_432E")))

    callbacks = 0
    while signed(machine.word(addr("g_9124"))) > -32768:
        for y, total in ((1, -738), (0, -740)):
            machine.run(behavior.Case(label="mickey-edge-repeat",
                registers={"ax": 1, "bx": 1, "cx": 408, "dx": y,
                           "si": 0, "di": total & 0xFFFF}, return_kind="void"),
                preserve=True, original_entry=entry)
            callbacks += 1
            if signed(machine.word(addr("g_9124"))) == -32768:
                break
            if callbacks >= 32766:
                raise AssertionError("mickey control exceeded its fixed 32766-callback budget")

    floor_y = signed(machine.word(addr("g_9124")))
    machine.run(behavior.Case(label="mickey-final-in-range-xy",
        registers={"ax": 1, "bx": 1, "cx": 636, "dx": 0,
                   "si": 456, "di": 0xFD1C}, return_kind="void"),
        preserve=True, original_entry=entry)
    final = [signed(machine.word(addr("g_9122"))), signed(machine.word(addr("g_9124")))]
    if (first_y, first_previous_y, callbacks, floor_y, final) != (-2, -370, 32766, -32768, [636, -32767]):
        raise AssertionError("original mickey negative control changed")
    # Unicorn installs Python bound-method hooks; retain the VM until process exit
    # so cyclic GC does not close native handles during a subsequent probe.
    _UNICORN_KEEPALIVE.append(machine)
    return {
        "mode": "mickey_mode=1",
        "target": "hash-locked original 03EE/0445 instructions through tools/behavior.py Machine",
        "driver_callback_coordinates": {"first": [408, 0], "repeat_y": [1, 0], "final": [636, 0],
                                        "requested_range": {"x": [0, 636], "y": [0, 476]}},
        "first_callback_game_y": first_y,
        "first_scaled_previous_y_mickey": first_previous_y,
        "callback_count_to_signed_floor": callbacks,
        "game_y_at_signed_floor": floor_y,
        "final_game_position": final,
        "scope": "Out-of-domain negative control: the real mickey-mode path defeats the nonnegative cursor premise despite in-range driver callback coordinates.",
    }


def resize_negative_control(mickey: dict) -> dict:
    spec = importlib.util.spec_from_file_location("viewport_resize_probe", PACKET / "resize_probe.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("resize_probe.py is not adjacent to domain_probe.py")
    resize_probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(resize_probe)
    worker_dir = ROOT / "build/scratch/viewport-domain"
    worker_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="viewport-domain-", dir=worker_dir) as temp:
        output = resources_probe.fresh_output(ROOT, str(Path(temp) / "resize"))
        resize_probe.OUT = output
        pair = resize_probe.prepare()
        _UNICORN_KEEPALIVE.append(pair)
        case = resize_probe.make_case("mickey-negative-wrap", 357, 480,
                                      tuple(mickey["final_game_position"]))
        comparison = pair.compare(case)
        if not comparison.equal:
            raise AssertionError("original and current resize implementations differ in negative control")
        original = comparison.original
        rows, cols = struct.unpack("<hh", bytes.fromhex(original["ranges"]["viewport_counts"]))
        rect = struct.unpack("<4h", bytes.fromhex(original["ranges"]["viewport_rect"]))
        index = 40 * (rows - 1) + cols - 1
        if (rows, cols, index) != (2046, 36, 81835):
            raise AssertionError("retained mickey resize witness changed")
        return {
            "resize_original_candidate_equal": comparison.equal,
            "root": [14, 22, 404, 357],
            "fresh_f084_center": [408, 369],
            "cursor_after_original_mickey_control": mickey["final_game_position"],
            "object4_rect": list(rect),
            "rows": rows,
            "columns": cols,
            "largest_flat_index": index,
            "scope": "The resize probe executes original DOS resize helpers and separately compiled current S26 code; cursor delivery and held-button lifetime are explicit harness inputs.",
        }


def collect(overrides: dict[str, bytes | str] | None = None, *, run_negative: bool = True) -> dict:
    pins = inventory_pins(RELEVANT, overrides)
    source_bytes = all_sources(overrides)
    source_text = {path: raw.decode("latin1") for path, raw in source_bytes.items()}
    asm = source_text["src/root/m1B73.asm"]
    mickey_init = asm_procedure(asm, "_f_1B73_0046")
    mickey_decl = re.search(r"(?im)^\s*mickey_mode\s+db\s+0\b", asm)
    absolute_handler = asm_procedure(asm, "_f_1B73_0445")
    callback = asm_procedure(asm, "_f_1B73_03EE")
    timer = asm_procedure(asm, "_f_1B73_051F")
    keyboard = asm_procedure(asm, "_f_1B73_0747")

    # The mouse mode is set only by driver version 7.00 or the explicit bug flag.
    for fragment in ("mov ax, 24h", "int 33h", "cmp bx, 700h", "je L005A",
                     "test byte ptr _g_432A", "je L006A", "mov byte ptr cs:mickey_mode, 1"):
        if norm(fragment) not in norm(mickey_init):
            raise AssertionError(f"mouse mode selection source lost {fragment!r}")
    if not (norm("mov dx, word ptr _g_3DB4") in norm(mickey_init)
            and norm("sub dx, 4") in norm(mickey_init)
            and norm("mov ax, 8") in norm(mickey_init)
            and norm("mov dx, word ptr _g_3DB2") in norm(mickey_init)
            and norm("mov ax, 7") in norm(mickey_init)):
        raise AssertionError("function 7/8 absolute ranges are no longer requested")
    startup_center = (
        "mov ax, word ptr _g_3DB4", "shr ax, 1", "mov word ptr _g_9122, ax",
        "mov ax, word ptr _g_3DB2", "shr ax, 1", "mov word ptr _g_9124, ax",
    )
    if any(norm(fragment) not in norm(mickey_init) for fragment in startup_center):
        raise AssertionError("startup cursor coordinate assignments changed")
    for fragment in ("mov word ptr _g_9122, cx", "mov word ptr _g_9124, dx"):
        if norm(fragment) not in norm(absolute_handler):
            raise AssertionError(f"absolute callback copy lost {fragment}")
    if "je _f_1b73_0445" not in norm(callback):
        raise AssertionError("non-mickey callback no longer enters the absolute handler")
    mode_writes = [line.strip() for line in asm.splitlines()
                   if re.search(r"\bmov\s+byte\s+ptr\s+cs:mickey_mode\s*,", line, re.I)]
    if not mickey_decl or len(mode_writes) != 1:
        raise AssertionError("mickey_mode no longer starts clear with a single conditional setter")
    for fragment in (
        "add ax, word ptr _g_9122", "cmp ax, 0", "jge L060E", "xor ax, ax",
        "mov cx, word ptr _g_3DB2", "cmp ax, cx", "jl L0619", "mov ax, cx",
        "dec ax", "mov word ptr _g_9122, ax",
        "add ax, word ptr _g_9124", "cmp ax, 0", "jge L062A", "xor ax, ax",
        "mov cx, word ptr _g_3DB4", "cmp ax, cx", "jl L0635", "mov ax, cx",
        "dec ax", "mov word ptr _g_9124, ax",
    ):
        if norm(fragment) not in norm(timer):
            raise AssertionError(f"timer keyboard X/Y clamp lost {fragment!r}")
    for fragment in ("mov bx, word ptr _g_3DB4", "mov word ptr _g_9124, bx",
                     "cmp bx, 8", "mov word ptr _g_9124, ax",
                     "mov ax, word ptr _g_3DB4", "dec ax", "sub bx, 8",
                     "cmp bx, word ptr _g_9124", "sub ax, 6"):
        if norm(fragment) not in norm(keyboard):
            raise AssertionError(f"keyboard scan Y positioning lost {fragment!r}")
    if "xor dx, bx" not in norm(callback):
        raise AssertionError("original mickey Y-underflow counterexample branch changed")

    # g_432A starts cleared and the only source assignments are /b and BUG=MSMOUSE.
    flag_decl = re.search(r"(?im)^\s*_g_432A\s+db\s+0\b", asm)
    s20 = source_text["src/S20/m39F1.c"]
    initstuff = c_function(s20, "IBMInitStuff")
    writers_432a = []
    for rel, raw in sorted(source_bytes.items()):
        text = strip_comments(raw, Path(rel).suffix)
        for line_no, line in enumerate(text.splitlines(), 1):
            if re.search(r"\bg_432A\s*(?:=|\+=|-=|\+\+|--)", line):
                writers_432a.append({"path": rel, "line": line_no, "text": line.strip()})
    if not flag_decl or len(writers_432a) != 2 or any(row["path"] != "src/S20/m39F1.c" for row in writers_432a):
        raise AssertionError("g_432A initialization/write census changed")
    if ("for (i = 1; i < argc; i++)" not in initstuff or "case 'b':" not in initstuff
        or "g_432A = 1;" not in initstuff or 'getenv("BUG")' not in initstuff
        or '"MSMOUSE"' not in initstuff or "stricmp" not in initstuff):
        raise AssertionError("IBMInitStuff no longer identifies the /b and BUG=MSMOUSE setters")
    main = source_text["src/root/m15F8.c"]
    startup = source_text["src/S17/m384C.c"]
    if main.find("IBMInitStuff(argc, argv);") < 0 or initstuff.find('getenv("BUG")') > initstuff.find("o17_384C_0000();"):
        raise AssertionError("startup order no longer sets the input domain before mouse init")
    if "f_1B73_0046();" not in c_function(startup, "o17_384C_0000"):
        raise AssertionError("mouse mode init is not reached through the startup mouse setup")

    # Prove the blocking resize loop's sample source and exclude in-loop warps/event dispatch.
    resize = c_function(source_text["src/S26/m39C7.c"], "o26_39C7_0671")
    dispatcher = c_function(source_text["src/root/m218D.c"], "f_218D_02D5")
    loop = c_block(resize, "while (ButtonHeld())")
    for fragment in ("f_1FD2_04B3(0xf084, &icon)", "if (ev == 0)",
                     "f_2505_0382(&start, &icon)", "f_1B73_09E9(start.x, start.y)",
                     "pt = start", "f_1FD2_04D0(&pt)",
                     "pt.x - start.x", "pt.y - start.y"):
        if norm(fragment) not in norm(resize):
            raise AssertionError(f"resize setup/sample source lost {fragment}")
    if "f_1b73_09e9" in norm(loop) or "f_1b73_0c80" in norm(loop) or "win_events(" in norm(loop):
        raise AssertionError("resize loop now dispatches another warp or app event")
    if "case 0xf084:" not in norm(dispatcher) or "o26_39c7_0671(0l)" not in norm(dispatcher):
        raise AssertionError("F084 dispatcher no longer enters resize with a null event")
    resize_callers = c_call_sites(source_bytes, "o26_39C7_0671")
    if {(r["path"], r["line"], r["first_arg"]) for r in resize_callers} != {
        ("src/root/m218D.c", 168, "0")
    }:
        raise AssertionError("modal resize caller census changed")
    if "f_1fd2_04d0(&pt)" not in norm(loop) or not re.search(r"pt\.y\s*!=\s*g_9124", loop):
        raise AssertionError("resize loop no longer samples the shared cursor position")
    held = c_function(source_text["src/root/m1FD2.c"], "ButtonHeld")
    still = c_function(source_text["src/root/m1FD2.c"], "StillDown")
    if "g_9124" in held or "g_9124" in still:
        raise AssertionError("held-button polling gained a cursor-position writer")

    # Guard the menu top used by the geometry constraint, including its font premise.
    menu_source = source_text["src/root/m1FD2.c"]
    menu_draw = c_function(menu_source, "f_1FD2_0663")
    screen_rect_api = c_function(source_text["src/root/m1CE2.c"], "f_1CE2_000C")
    screen_init = source_text["src/state/screen-clip-list.c"]
    display_init = c_function(source_text["src/root/m205F.c"], "f_205F_0004")
    vga_font = asm_procedure(source_text["src/S00/m31AD.asm"], "_o00_31AD_168C")
    if ("g_9130()" not in norm(menu_draw)
        or "fd_50f6_393c = *f_1ce2_000c()" not in norm(menu_draw)
        or "fd_50f6_393c.bottom = g_3ddc + fd_50f6_393c.top + 3" not in norm(menu_draw)
        or "return g_5a9c" not in norm(screen_rect_api)):
        raise AssertionError("menu rectangle no longer derives its bottom from the screen and font state")
    if not re.search(r"g_5a9c\s*\[\s*2\s*\].*?\{\s*0\s*,\s*0\s*,", screen_init, re.S | re.I):
        raise AssertionError("screen clip rectangle no longer starts at top zero")
    mode8_start = norm(display_init).find("case 8:")
    mode8_end = norm(display_init).find("default:", mode8_start)
    mode8 = norm(display_init)[mode8_start:mode8_end]
    if (mode8_start < 0 or "o00_31ad_2ae5()" not in mode8
        or "o20_39c7_0211()" not in mode8 or "o20_39c7_0005()" not in mode8
        or "g_5a9c.right = g_3db2" not in norm(display_init)
        or "g_5a9c.bottom = g_3db4" not in norm(display_init)
        or re.search(r"g_5a9c\.(?:left|top)\s*=", norm(display_init))):
        raise AssertionError("VGA screen-top state/setup changed")
    if not ("mov bh, 2" in norm(vga_font) and "int 10h" in norm(vga_font)
            and "mov byte ptr _g_3ddc, 0eh" in norm(vga_font)):
        raise AssertionError("14-pixel VGA font-height primitive changed")
    menu_font_height = 14
    menu_screen_top = 0
    menu_bottom = menu_screen_top + menu_font_height + 3
    if menu_bottom != 17 or menu_bottom < 0:
        raise AssertionError("supported VGA menu bottom is no longer the guarded value 17")

    # Gather every global-position writer and reject any writer outside reviewed handlers.
    writes = cursor_writers(source_bytes)
    allowed_writers = {
        "_f_1B73_0046", "_f_1B73_0445", "_f_1B73_051F", "_f_1B73_0747",
    }
    for name, rows in writes.items():
        if any(row["owner"] not in allowed_writers or row["path"] != "src/root/m1B73.asm" for row in rows):
            raise AssertionError(f"unexpected source writer of {name}")
        if {row["owner"] for row in rows} != allowed_writers:
            raise AssertionError(f"cursor-position writer census for {name} is incomplete")

    # Several nominal routes replay an existing coordinate without bounding it.
    raw_warp = asm_procedure(asm, "_f_1B73_09F7")
    warp_driver = asm_procedure(asm, "_f_1B73_09FF")
    replay = asm_procedure(asm, "_f_1B73_0A1B")
    shift_start = norm(keyboard[keyboard.find("L0803:"):keyboard.find("L0821:")])
    horizontal_edges = norm(keyboard[keyboard.find("L0946:"):keyboard.find("L0979:")])
    vertical_edges = norm(keyboard[keyboard.find("L0979:"):keyboard.find("L09AC:")])
    common_edge_replay = norm(keyboard[keyboard.find("L09E3:"):keyboard.find("_f_1B73_0747 endp")])
    if ("call near ptr _f_1b73_09f7" not in shift_start
        or "_g_9122" in shift_start or "_g_9124" in shift_start):
        raise AssertionError("L0803 no longer replays the existing cursor pair without changing it")
    if ("mov word ptr _g_9122" not in horizontal_edges or "mov word ptr _g_9124" in horizontal_edges
        or "cmp bx, 8" not in horizontal_edges or "mov ax, 6" not in horizontal_edges
        or "call near ptr _f_1b73_09f7" not in common_edge_replay):
        raise AssertionError("horizontal edge commands no longer preserve startY through _09F7")
    if "mov word ptr _g_9124" not in vertical_edges or "mov word ptr _g_9122" in vertical_edges:
        raise AssertionError("vertical edge commands no longer preserve startX")
    if ("mov cx, word ptr _g_9122" not in norm(raw_warp)
        or "mov dx, word ptr _g_9124" not in norm(raw_warp)
        or "call near ptr _f_1b73_0445" not in norm(warp_driver)):
        raise AssertionError("_09F7 raw warp no longer copies both current axes into the shared sample")
    if ("mov cx, word ptr _g_9122" not in norm(replay)
        or "mov dx, word ptr _g_9124" not in norm(replay)
        or "call near ptr _f_1b73_0445" not in norm(replay)):
        raise AssertionError("_0A1B button replay no longer copies both current axes")
    warp_calls = call_sites(source_bytes, "f_1B73_09E9")
    center_calls = call_sites(source_bytes, "f_1B73_0C80")
    expected_warps = {
        ("src/root/m1FD2.c", 429), ("src/S10/m35F5.c", 145),
        ("src/S10/m35F5.c", 378), ("src/S26/m39C7.c", 253),
        ("src/S26/m39C7.c", 325), ("src/root/m1B73.asm", 1792),
    }
    if {(r["path"], r["line"]) for r in warp_calls} != expected_warps:
        raise AssertionError("09E9 caller census changed")
    expected_centers = {("src/root/m218D.c", 305), ("src/root/m218D.c", 332), ("src/S10/m35F5.c", 425)}
    if {(r["path"], r["line"]) for r in center_calls} != expected_centers:
        raise AssertionError("0C80 caller census changed")
    kbd_warps = call_sites(source_bytes, "f_1B73_09F7")
    if {(r["path"], r["line"]) for r in kbd_warps} != {
        ("src/root/m1B73.asm", 310), ("src/root/m1B73.asm", 962),
        ("src/root/m1B73.asm", 1191), ("src/root/m1B73.asm", 1385),
        ("src/root/m1B73.asm", 1416),
    }:
        raise AssertionError("keyboard _09F7 warp/copy caller census changed")

    # The callback installed for mouse dispatch only enqueues; cursor callbacks only draw.
    m1fd2 = source_text["src/root/m1FD2.c"]
    descriptor_rows = {
        "g_6004": "struct timer g_6004 = { { 0, 0, 100, 100 }, f_1b73_030f",
        "g_6016": "struct timer g_6016 = { { 0, 0, 100, 100 }, f_1b73_0d4b",
        "g_6028": "struct timer g_6028 = { { 0, 0, 100, 100 }, f_1b73_0d4b",
        "g_603a": "struct timer g_603a = { { 0, 0, 0x27f, 0x10 }, f_1b73_030f",
    }
    if any(norm(fragment) not in norm(m1fd2) for fragment in descriptor_rows.values()):
        raise AssertionError("registered mouse/cursor descriptor callback bindings changed")
    generic_setup = c_function(m1fd2, "f_1FD2_02FF")
    generic_register = c_function(m1fd2, "f_1FD2_032F")
    dormant_generic = c_function(m1fd2, "f_1FD2_0390")
    enqueue_adapter = asm_procedure(asm, "_f_1B73_030F")
    cursor_callback = asm_procedure(asm, "_f_1B73_0D4C")
    callback_installer = asm_procedure(asm, "_f_1B73_0AA3")
    callback_dispatch = asm_procedure(asm, "_f_1B73_0CB3")
    descriptor_invoke = asm_procedure(asm, "_f_1B73_0CEF")
    callback_callers = c_call_sites(source_bytes, "f_1FD2_032F")
    dormant_callers = c_call_sites(source_bytes, "f_1FD2_0390")
    if ("f_1fd2_032f" not in norm(generic_setup)
        or "f_1b73_0d4b" not in norm(generic_setup)
        or "g_6016.fn = fn" not in norm(generic_register)
        or "f_1b73_09ff" in norm(generic_setup)):
        raise AssertionError("generic cursor descriptor is not bound to its draw callback")
    if {(row["path"], row["line"]) for row in callback_callers} != {("src/root/m1FD2.c", 186)} or dormant_callers:
        raise AssertionError("generic cursor callback caller/reference census changed")
    for fragment in ("call far ptr _f_1b73_036e", "retf"):
        if fragment not in norm(enqueue_adapter):
            raise AssertionError(f"mouse event adapter lost {fragment}")
    if "_f_1b73_09ff" in norm(enqueue_adapter) or "_f_1b73_09e9" in norm(enqueue_adapter):
        raise AssertionError("mouse descriptor callback acquired a cursor-warp route")
    if ("lea ax, _f_1b73_0cb3" not in norm(callback_installer)
        or "mov word ptr _g_5ffa, ax" not in norm(callback_installer)
        or "mov al, 1fh" not in norm(callback_installer)
        or "call word ptr _g_5ffa" not in norm(absolute_handler)):
        raise AssertionError("g_5FFA mouse callback installation/dispatch binding changed")
    if ("lds di, dword ptr es:[si]" not in norm(callback_dispatch)
        or "call near ptr _f_1b73_0cef" not in norm(callback_dispatch)
        or "push word ptr [di+0ch]" not in norm(descriptor_invoke)
        or "call dword ptr es:[di+8]" not in norm(descriptor_invoke)):
        raise AssertionError("mouse descriptor traversal/callback fields changed")
    if ("call near ptr _f_1b73_0da4" not in norm(cursor_callback)
        or "call far ptr _f_1b4e_003b" not in norm(cursor_callback)
        or "_g_9122" in norm(cursor_callback) or "_g_9124" in norm(cursor_callback)
        or "_f_1b73_09ff" in norm(cursor_callback)):
        raise AssertionError("cursor descriptor callback no longer stays on the drawing/save path")
    draw_dispatch = asm_procedure(asm, "_f_1B73_0122")
    if ("mov bx, word ptr _g_4da5" not in norm(draw_dispatch)
        or "call dword ptr es:[bx+8]" not in norm(draw_dispatch)
        or any(f"call dword ptr _g_{ptr}" not in norm(draw_dispatch) for ptr in ("9168", "9128", "9184"))):
        raise AssertionError("cursor rendering no longer calls the configured video drawing primitives")
    if "_f_1b73_09ff" in norm(draw_dispatch) or "_f_1b73_09e9" in norm(draw_dispatch):
        raise AssertionError("video drawing callback path acquired a raw cursor warp")

    f20_refs = comments_and_sites(source_bytes, "f_20E8_0903")
    if len(f20_refs) != 1 or f20_refs[0]["path"] != "src/root/m20E8.c" or "void _fastcall f_20E8_0903" not in f20_refs[0]["text"]:
        raise AssertionError("f_20E8_0903 now has a reference/call/address-taking site")

    swaps = c_call_sites(source_bytes, "win_Swap")
    expected_swaps = {("src/root/m00F8.c", 294, "0x1900"),
                      ("src/root/m00F8.c", 306, "0x100"),
                      ("src/root/m015B.c", 185, "0x100")}
    if {(r["path"], r["line"], r["first_arg"]) for r in swaps} != expected_swaps:
        raise AssertionError("win_Swap caller census changed")
    rect_setters = c_call_sites(source_bytes, "f_22BF_00DD")
    expected_rect_setters = {("src/S09/m35F5.c", 320, "0x1602"),
                             ("src/S09/m35F5.c", 519, "0x1602"),
                             ("src/S16/m384C.c", 85, "0x1a01"),
                             ("src/S16/m384C.c", 120, "0x1a01")}
    if {(r["path"], r["line"], r["first_arg"]) for r in rect_setters} != expected_rect_setters:
        raise AssertionError("direct object-rectangle setter caller census changed")
    load_window_calls = c_call_sites(source_bytes, "win_LoadWindow")
    if {(r["path"], r["line"]) for r in load_window_calls} != {
        ("src/root/m20E8.c", 136), ("src/root/m23AE.c", 58), ("src/root/m23AE.c", 74)
    }:
        raise AssertionError("demand-load/reload caller census changed")
    load_all_calls = c_call_sites(source_bytes, "win_LoadAllWindows")
    if {(r["path"], r["line"]) for r in load_all_calls} != {("src/root/m00BA.c", 48)}:
        raise AssertionError("initial all-window load caller census changed")
    offset_mentions = comments_and_sites(source_bytes, "win_offsets")

    # The shipped root/window-control resource records establish the fresh icon geometry.
    hce_root = resources_probe.resource_payload(ROOT, 0, 0, "HCEGANT")
    root_fields = resources_probe.obj_fields(hce_root, 0)
    object4 = resources_probe.obj_fields(hce_root, 4)
    flags = struct.unpack_from("<H", hce_root, 0x1C)[0]
    min_size = struct.unpack_from("<2h", hce_root, 0x18)
    grid = struct.unpack_from("<2h", hce_root, 0x20)
    rows_index = resources_probe.index_rows(ROOT, "HCEGANT")
    rows_shared = resources_probe.index_rows(ROOT, "SHARED")
    profile8_offset = [row for row in rows_index if row[1:3] == (8, 9)]
    shared_root = [row for row in rows_shared if row[1:3] == (0, 0)]
    if flags != 0x050E or root_fields["origin"] != (14, 22, 404, 357) or object4["rect"] != (64, 41, 416, 362):
        raise AssertionError("decoded HCEGANT root/object-4 facts changed")
    if (root_fields["border_byte28"] != 2 or object4["modes"] != (1, 2, 3, 4)
        or object4["refs"] != (3, 3, 0, 0) or object4["border_byte28"] != 19):
        raise AssertionError("root border or object-4 mode/reference layout changed")
    if min_size != (252, 280) or grid != (16, 16) or profile8_offset or shared_root:
        raise AssertionError("HCEGANT profile-8 root assumptions changed")
    icon_bitmap = resources_probe.resource_payload(ROOT, 0x70, 2, "HCEGANT")
    if struct.unpack_from("<2h", icon_bitmap, 8) != (16, 16):
        raise AssertionError("HCEGANT resize bitmap is not 16 by 16")

    recalc = c_function(source_text["src/root/m2505.c"], "win_Recalc")
    object_axis = c_function(source_text["src/root/m2505.c"], "f_2505_03B9")
    if ("f_2505_03b9(k, win, obj)" not in norm(recalc)
        or "((int far *)(obj + 0x18))[axis]" not in norm(object_axis)
        or "((int far *)(obj + 0x10))[axis]" not in norm(object_axis)
        or "((int far *)(obj + 8))[axis]" not in norm(object_axis)):
        raise AssertionError("object-4 mode/reference geometry is no longer derived by win_Recalc")

    # Verify source control regeneration and all root-0 geometry/offset routes.
    control_builder = c_function(source_text["src/root/m2505.c"], "f_2505_06B9")
    control_center = c_function(source_text["src/root/m2505.c"], "f_2505_0382")
    control_add = c_function(source_text["src/root/m2505.c"], "f_2505_0831")
    control_remove = c_function(source_text["src/root/m2505.c"], "f_2505_08EA")
    if ("0xf084" not in norm(control_builder) or "0x70" not in norm(control_builder)
        or "m = (*((char far * far *)(w + 0x2c)))[0x28]" not in norm(control_builder)):
        raise AssertionError("root resize control is not regenerated from bitmap 70")
    for fragment in ("rect.right -= m", "rect.bottom -= m", "rect.right - size.x",
                     "rect.bottom - size.y", "0xf084"):
        if fragment not in norm(control_builder):
            raise AssertionError(f"F084 root-rectangle construction lost {fragment}")
    if ("(rect->right + rect->left) / 2" not in norm(control_center)
        or "(rect->top + rect->bottom) / 2" not in norm(control_center)):
        raise AssertionError("F084 center calculation changed")
    if "f_2505_06b9(1," not in norm(control_add) or "f_2505_06b9(0," not in norm(control_remove):
        raise AssertionError("root control add/remove paths no longer rebuild F084")
    geometry_s26 = source_text["src/S26/m39C7.c"]
    for fname in ("o26_39C7_040F", "o26_39C7_0671", "o26_39C7_0000"):
        body = c_function(geometry_s26, fname)
        if "f_2505_08ea(" not in norm(body) or "f_2505_0831(" not in norm(body):
            raise AssertionError(f"{fname} no longer refreshes active controls after geometry work")
    winopen = c_function(source_text["src/root/m20E8.c"], "win_Open")
    if "f_2505_0831(" not in norm(winopen):
        raise AssertionError("window open no longer installs controls")
    if not (norm(winopen).find("win_recalc(win)") >= 0
            and norm(winopen).rfind("win_recalc(win)") < norm(winopen).find("f_2505_0831(win)")):
        raise AssertionError("window open no longer recalculates geometry before installing F084")
    close = c_function(source_text["src/root/m20E8.c"], "win_Close")
    send_back = c_function(source_text["src/root/m20E8.c"], "f_20E8_0776")
    stack_order = {
        "open": ["f_2505_08ea(g_5702[0])", "f_2505_0831(win)"],
        "close": ["f_2505_08ea(win)", "f_2505_0831(g_5702[0])"],
        "send_back": ["f_2505_08ea(win)", "f_2505_0831(g_5702[0])"],
    }
    for label, body, sequence in (("open", winopen, stack_order["open"]),
                                  ("close", close, stack_order["close"]),
                                  ("send_back", send_back, stack_order["send_back"])):
        text = norm(body)
        positions = [text.find(fragment) for fragment in sequence]
        if any(pos < 0 for pos in positions) or positions != sorted(positions):
            raise AssertionError(f"active F084 stack transition {label} no longer removes then installs top controls")
    lookup = c_function(source_text["src/root/m1FD2.c"], "f_1FD2_04B3")
    lookup_asm = asm_procedure(asm, "_f_1B73_0C42")
    tag_find = asm_procedure(asm, "_f_1B73_0A89")
    if ("f_1b73_0c42(id, fd_5071_03c4, out)" not in norm(lookup)
        or "call near ptr _f_1b73_0a89" not in norm(lookup_asm)
        or "cmp ax, word ptr es:[di+0ch]" not in norm(tag_find)
        or "add di, 12h" not in norm(tag_find)):
        raise AssertionError("F084 lookup no longer uses the first matching fixed-tag descriptor")
    move = c_function(geometry_s26, "o26_39C7_040F")
    zoom = c_function(geometry_s26, "o26_39C7_0000")
    load_window = c_function(source_text["src/root/m20E8.c"], "win_LoadWindow")
    load_all = c_function(source_text["src/root/m20E8.c"], "win_LoadAllWindows")
    unlock = c_function(source_text["src/root/m23AE.c"], "win_UnlockWin")
    if ("o->width" in move or "o->height" in move
        or "win_offsets[win >> 8]" not in move):
        raise AssertionError("move path no longer preserves size/persists root origin")
    for fragment in ("w->zoomrect =", "= w->zoomrect", "o26_39c7_022f", "f_2505_08ea", "f_2505_0831"):
        if fragment not in norm(zoom):
            raise AssertionError(f"zoom/restore path lost {fragment}")
    if ("win_offsets[(char)(win >> 8)]" not in norm(load_window)
        or "*(struct rect far *)(obj + 8) = win_offsets" not in norm(load_window)
        or "db_loadobject(g_5a97, 9)" not in norm(load_all)
        or "for (i = 0; i < 45; i++) win_offsets[i] = g_635c" not in norm(load_all)):
        raise AssertionError("window resource/offset load path changed")
    if ("if (*(int far *)(w + 0x1c) & 0x1000)" not in close
        or "if (*(int far *)(w + 0x1c) & 0x1000)" not in winopen
        or "(*h)->flags & 0x800" not in unlock):
        raise AssertionError("root open/close/unload offset gates changed")
    save_table = c_block(source_text["src/S09/m35F5.c"], "struct SaveRec far fd_4E4B_0000[308]")
    if any(token in save_table for token in ("win_offsets", "fd_50F6_10DE", "fd_50F6_10E0",
                                              "fd_50F6_110C", "fd_50F6_1114", "fd_50F6_15C4")):
        raise AssertionError("SaveRec table gained a viewport/window-offset field")
    if flags & 0x1000 or flags & 0x0800:
        raise AssertionError("root flags activate save/translate offset branches")
    if ("f_1a53_00f0((char)(win >> 8), 0, 1)" not in norm(load_window)
        or "win_handles[(char)(win >> 8)] = h" not in norm(load_window)
        or "repointobjects(win)" not in norm(load_window)):
        raise AssertionError("window reload no longer uses the retained movable type-1 handle path")
    demand_load = c_function(source_text["src/root/m23AE.c"], "f_23AE_0069")
    if "win_loadwindow(win)" not in norm(demand_load) or "win_handles[n] == 0" not in norm(demand_load):
        raise AssertionError("demand reload no longer routes through win_LoadWindow before active open")

    constraint = c_function(geometry_s26, "o26_39C7_022F")
    if ("r->right - r->left < g_3db2" not in norm(constraint)
        or "r->top > fd_50f6_393c.bottom" not in norm(constraint)
        or "gx -= gx % g" not in norm(constraint)
        or "gy -= gy % h" not in norm(constraint)):
        raise AssertionError("resize/move/zoom width, menu-top, or grid constraints changed")

    # Check row/column arithmetic from source and apply the reviewed conditional bound.
    cache = source_text["src/root/m0250.c"]
    viewport = c_function(cache, "f_0250_0E15")
    if ("fd_50f6_10e0 = (fd_50f6_110c.right - fd_50f6_110c.left) / g_19be" not in norm(viewport)
        or "fd_50f6_10de = (fd_50f6_110c.bottom - fd_50f6_110c.top) / g_19c0 + 1" not in norm(viewport)):
        raise AssertionError("viewport dimension producer formula changed")
    if not re.search(r"fd_50f6_15c4\s*\[\s*30\s*\]\s*\[\s*40\s*\]", cache, re.I):
        raise AssertionError("fixed cache declaration is no longer int[30][40]")
    if not re.search(r"g_19BE\s*=\s*16", cache) or not re.search(r"g_19C0\s*=\s*16", cache):
        raise AssertionError("default viewport tile dimensions are no longer 16 by 16")
    load_tiles = c_function(cache, "LoadTiles")
    profile8_tiles = load_tiles[load_tiles.find("case 8:"):load_tiles.find("case 2:")]
    if not profile8_tiles or re.search(r"g_19B[EC]\s*=", profile8_tiles):
        raise AssertionError("profile 8 LoadTiles path changes the 16-pixel tile dimensions")
    screen_w, screen_h = 640, 480
    initial = root_fields["origin"]
    root_width_max = max(w for w in range(initial[2] % 16, screen_w, 16))
    root_height_bound = max(initial[3], screen_h + 8, 280)
    cols = (root_width_max - 52) // 16
    rows = (root_height_bound - 36) // 16 + 1
    flat = 40 * (rows - 1) + cols - 1
    if (root_width_max, root_height_bound, rows, cols, flat) != (628, 488, 29, 36, 1155):
        raise AssertionError("supported-domain bound arithmetic changed")

    # A moved root can seed one off-screen axis; controls replace or replay axes independently.
    moved_top = 470
    start_x = initial[0] + initial[2] - 10
    start_y = moved_top + initial[3] - 10
    moved_horizontal_sample = [6, start_y]
    timer_sample = [start_x, min(screen_h - 1, start_y - 1)]
    mouse_sample = [636, 476]
    for sample in (moved_horizontal_sample, timer_sample, mouse_sample):
        if not (sample[0] == start_x or 0 <= sample[0] <= screen_w - 1):
            raise AssertionError("modeled cursor control violates the X per-axis invariant")
        if not (sample[1] == start_y or 0 <= sample[1] <= screen_h - 1):
            raise AssertionError("modeled cursor control violates the Y per-axis invariant")
    if (start_x, start_y, moved_horizontal_sample, timer_sample, mouse_sample) != (
        408, 817, [6, 817], [408, 479], [636, 476]
    ):
        raise AssertionError("moved-root horizontal/timer/mouse replacement controls changed")
    signed_int_bounds = {
        "dos_int_range": [-32768, 32767],
        "admitted_root_width": [252, root_width_max],
        "admitted_root_height": [280, root_height_bound],
        "admitted_root_top": [18, screen_h],
        "root_bottom_max": screen_h + root_height_bound,
        "fresh_startY_max": screen_h + root_height_bound - 10,
        "sampleY_minus_startY_range": [-(screen_h + root_height_bound - 10), screen_h - 1],
        "resulting_bottom_max": screen_h + root_height_bound,
        "largest_flat_cache_index": flat,
    }
    signed_intermediates = [signed_int_bounds["root_bottom_max"], signed_int_bounds["fresh_startY_max"],
                            *signed_int_bounds["sampleY_minus_startY_range"],
                            signed_int_bounds["resulting_bottom_max"], signed_int_bounds["largest_flat_cache_index"]]
    if any(value < -32768 or value > 32767 for value in signed_intermediates):
        raise AssertionError("admitted geometry arithmetic exceeds signed 16-bit range")

    image = exe.load()
    original_rows = {}
    for name in MOUSE_FUNCTIONS:
        function_meta, instructions = instruction_rows(image, name)
        original_rows[name] = {"function": function_meta,
                               "sha256": sha(image.read(function_meta["unit"], function_meta["seg"] * 16 + function_meta["off"], function_meta["size"])),
                               "instructions": instructions}
    require_instruction(original_rows["f_1B73_0046"]["instructions"], "cmp", "bx, 0x700")
    require_instruction(original_rows["f_1B73_0046"]["instructions"], "mov", "ax, 8")
    require_instruction(original_rows["f_1B73_0046"]["instructions"], "mov", "ax, 7")
    require_instruction(original_rows["f_1B73_03EE"]["instructions"], "xor", "dx, bx")
    require_instruction(original_rows["f_1B73_0445"]["instructions"], "mov", "word ptr [0x9122], cx")
    require_instruction(original_rows["f_1B73_0445"]["instructions"], "mov", "word ptr [0x9124], dx")
    require_instruction(original_rows["f_1B73_051F"]["instructions"], "mov", "word ptr [0x9122], ax")
    require_instruction(original_rows["f_1B73_051F"]["instructions"], "mov", "word ptr [0x9124], ax")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "mov", "word ptr [0x9122], ax")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "mov", "word ptr [0x9124], bx")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "mov", "word ptr [0x9124], ax")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "cmp", "bx, 8")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "mov", "bx, word ptr [0x3db4]")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "mov", "ax, word ptr [0x3db4]")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "sub", "bx, 8")
    require_instruction(original_rows["f_1B73_0747"]["instructions"], "sub", "ax, 6")
    require_instruction(original_rows["f_1B73_09FF"]["instructions"], "mov", "ax, 4")
    if image.sha256 != exe.EXPECTED_SHA256:
        raise AssertionError("original executable hash changed")

    mentions = variable_mentions(source_bytes, ("g_9122", "g_9124", "g_432A", "f_1B73_09E9", "f_1B73_0C80",
                                                "f_20E8_0903", "win_Swap", "f_22BF_00DD",
                                                "fd_50F6_393C", "g_5A9C", "g_5FFA", "g_6004", "g_6016",
                                                "g_6028", "g_603A", "g_4DA5", "g_9130", "g_3DDC", "f_1B73_030F",
                                                "f_1B73_0D4B", "f_1B73_09FF", "f_1FD2_032F", "f_1FD2_0390"))
    facts = {
        "schema": SCHEMA,
        "source_pins": pins,
        "source_census": {
            "g_432A_writers": writers_432a,
            "mickey_mode_declaration": "MOUSE_TEXT:mickey_mode db 0",
            "mickey_mode_writers": mode_writes,
            "g_9122_writers": writes["g_9122"],
            "g_9124_writers": writes["g_9124"],
            "g_9122_mentions": mentions["g_9122"],
            "g_9124_mentions": mentions["g_9124"],
            "warp_09E9_callers": warp_calls,
            "warp_0C80_callers": center_calls,
            "keyboard_09F7_replay_callers": kbd_warps,
            "modal_resize_callers": resize_callers,
            "f_20E8_0903_references": f20_refs,
            "win_Swap_callers": swaps,
            "f_22BF_00DD_callers": rect_setters,
            "win_LoadWindow_callers": load_window_calls,
            "win_LoadAllWindows_callers": load_all_calls,
            "win_offsets_references": offset_mentions,
            "fd_50F6_393C_mentions": mentions["fd_50F6_393C"],
            "g_5A9C_mentions": mentions["g_5A9C"],
            "g_5FFA_mentions": mentions["g_5FFA"],
            "g_4DA5_hot_box_mentions": mentions["g_4DA5"],
            "descriptor_binding_mentions": {name: mentions[name] for name in ("g_6004", "g_6016", "g_6028", "g_603A")},
            "menu_state_mentions": {name: mentions[name] for name in ("g_9130", "g_3DDC")},
            "callback_reference_mentions": {name: mentions[name] for name in
                                              ("f_1B73_030F", "f_1B73_0D4B", "f_1B73_09FF",
                                               "f_1FD2_032F", "f_1FD2_0390")},
            "generic_cursor_callback_callers": callback_callers,
            "dormant_generic_callback_callers": dormant_callers,
        },
        "domain": {
            "launch_arguments": "empty; IBMInitStuff argument loop cannot set /b or display switches",
            "environment": "BUG absent or not case-insensitively equal to MSMOUSE; source sets g_432A only for that value",
            "mouse_driver": "first pre-reset INT 33h function 24h return has BX != 0700h; mickey mode remains clear from initialized state",
            "requested_ranges": {"x": [0, 636], "y": [0, 476], "screen": [640, 480]},
            "driver_contract": "Operational premise: standard INT 33h ABI; requested 7/8 ranges remain effective; every callback, including button-only and post-function-4 callbacks, supplies bounded absolute CX/DX.",
            "driver_contract_reference": CONTRACT_URL,
            "external_premise": "driver range/callback compliance is external; source itself does not clamp CX/DX in 0445 or the local 09FF warp copy",
            "menu_bottom": "fd_50F6_393C.bottom remains 17: screen top 0, active VGA font height 14, and f_1FD2_0663 formula top + height + 3",
        },
        "original_executable": {
            "sha256": image.sha256,
            "mouse_functions": original_rows,
        },
        "resource_facts": {
            "database": "HCEGANT; profile 8 selected by the DOS display configuration",
            "resource_sha256": {name: sha((ROOT / "assets" / name).read_bytes())
                                 for name in ("HCEGANT.DAT", "HCEGANT.NDX", "SHARED.DAT", "SHARED.NDX")},
            "root_flags": flags,
            "root_origin": list(root_fields["origin"]),
            "root_rect": list(root_fields["rect"]),
            "root_border_byte28": root_fields["border_byte28"],
            "min_size": list(min_size),
            "grid": list(grid),
            "object4_rect": list(object4["rect"]),
            "object4_origin": list(object4["origin"]),
            "object4_refs": list(object4["refs"]),
            "object4_modes": list(object4["modes"]),
            "object4_border_byte28": object4["border_byte28"],
            "object4_size_from_root": ["root width - 52", "root height - 36"],
            "resize_bitmap_70_size": [16, 16],
            "fresh_resize_center_offset": ["root right - 10", "root bottom - 10"],
            "f084_basis": "current root/window rectangle inset by root border byte 2, then bitmap 0x70 size 16x16; center is root right/bottom minus 10",
            "object4_geometry_basis": "serialized object-4 modes/refs resolved by win_Recalc; x=left+50, right=right-2, y=top+19, bottom=bottom-17",
            "profile8_kind9_override": bool(profile8_offset),
            "shared_root_record": bool(shared_root),
        },
        "resize_loop": {
            "entry": "root:m218D:f_218D_02D5 F084 branch calls o26_39C7_0671(NULL) synchronously",
            "control": "unique active F084 descriptor is rebuilt from the current root/window rectangle; cursor warp precedes pt=start; initial delta is zero",
            "sample_invariant": {
                "x": "sampleX in {startX} union [0,639]",
                "y": "sampleY in {startY} union [0,479]",
                "proof_shape": "raw start warp seeds the exceptional axis; updates replace an axis with an in-screen value or replay the prior value",
            },
            "later_samples": [
                "bounded INT 33h absolute callback copied by 0445",
                "INT 08h timer repeat clamps X and Y to [0, extent-1]",
                "INT 15h/INT 09h scan-code center/edge commands set one or both bounded coordinates",
                "_09F7 L0803 shift/copy replays both existing coordinates",
                "_0747 horizontal edge commands replace X and preserve Y; vertical edge commands replace Y and preserve X",
                "_0A1B/L0A21 button emulation replays both existing coordinates through 0445",
            ],
            "button_polling": "ButtonHeld/StillDown poll tick and held-input state; they do not write cursor coordinates or dispatch application events",
            "unbounded_warps_in_modal_loop": 0,
            "other_09E9_and_0C80_callers_are_blocked": True,
            "startup_cursor_coordinates": ["screenHeight/2 -> X", "screenWidth/2 -> Y", "(240,320) at 640x480; axis order is not geometric center"],
            "cursor_global_writers": {"g_9122": writes["g_9122"], "g_9124": writes["g_9124"]},
            "moved_root_horizontal_control": {
                "status": "deterministic source/arithmetic control, not an executed driver trace",
                "root_top": moved_top,
                "start": [start_x, start_y],
                "horizontal_edge_sample": moved_horizontal_sample,
                "delta_y": 0,
                "relevant_routes": ["_0747 L0946/L095E", "L09E3 -> _09F7", "_09F7 -> _09FF -> _0445"],
            },
            "timer_replacement_control": {"status": "deterministic clamp arithmetic", "from": [start_x, start_y],
                                           "one_up_repeat_after_clamp": timer_sample},
            "mouse_replacement_control": {"status": "driver-contract input, not captured hardware delivery",
                                          "absolute_callback": mouse_sample, "requested_range": [[0, 636], [0, 476]]},
        },
        "composition_bridges": {
            "accepted_callback_census": "evidence/canonical/menu-title-owner/review.md:9-17",
            "mouse_dispatch": {
                "g_5FFA_installer": "_f_1B73_0AA3 installs _f_1B73_0CB3 and event mask 0x1f",
                "descriptor_dispatch": "_f_1B73_0445 calls g_5FFA; _0CB3 walks 18-byte descriptors; _0CEF invokes callback +8 with event code +0x0c",
                "event_descriptors": {"g_6004": "_f_1B73_030F enqueue adapter", "g_603A": "_f_1B73_030F enqueue adapter"},
                "cursor_descriptors": {"g_6016": "_f_1B73_0D4B draw/save/restore", "g_6028": "_f_1B73_0D4B draw/save/restore"},
                "generic_callback": "only nominal f_1FD2_032F caller supplies _f_1B73_0D4B; _f_1FD2_0390 has no caller",
                "hot_box_callback": "_0122 invokes the stored descriptor callback at +8; accepted menu review census binds nominal callbacks to enqueue or cursor draw/save/restore routes",
                "vga_draw_dispatch": ["g_9168", "g_9128", "g_9184"],
                "callback_to_warp_excluded": True,
            },
            "active_f084": {
                "lookup": "f_1FD2_04B3 -> _f_1B73_0C42 -> first matching fixed tag search _0A89",
                "owner": "only the active top window has registered controls in the reviewed open/close/send-back lifecycle; root 0 is the pinned HCEGANT resizable window",
                "transitions": stack_order,
                "geometry_rebuild": {name: "remove then add controls" for name in ("o26_39C7_040F", "o26_39C7_0671", "o26_39C7_0000")},
                "reload": "win_LoadWindow uses allocator type 1, restores cached object-0 origin/size, and RepointObjects; demand reload enters through f_23AE_0069; active open recalculates and installs controls before dispatch",
                "offset_and_save_exclusions": "root flags 0x050e omit 0x1000/0x0800; win_LoadAllWindows is initial-only; reviewed SaveRec has no window-offset/viewport field",
                "uniqueness_scope": "nominal valid stack/resource flow; foreign API activation, corrupted descriptors, computed aliases, and exceptional continuations excluded",
            },
            "menu_bottom": {
                "writer": "src/root/m1FD2.c:f_1FD2_0663",
                "screen_rect": "f_1CE2_000C returns g_5A9C; initialized screen top is 0; profile-8 display setup updates right/bottom only",
                "font_binding": "menu redraw calls g_9130; supported VGA font-height premise is g_3DDC=14 (the retained 8x14 VGA primitive sets byte 0x0e)",
                "formula": "fd_50F6_393C.bottom = top + g_3DDC + 3 = 0 + 14 + 3 = 17",
                "lifetime": "the nominal VGA/menu state remains active during resize; protected source pins, mention census and SaveRec exclusions are retained",
                "status": "source formula PROVEN; active 14-pixel font binding is an explicit supported-domain premise",
            },
            "evidence_scope": "Static source/resource census and deterministic arithmetic; not a full gameplay trace or arbitrary-state alias proof",
        },
        "geometry_bound": {
            "screen": [screen_w, screen_h],
            "root_width_max": root_width_max,
            "root_height_max": root_height_bound,
            "object4_width_max": root_width_max - 52,
            "object4_height_max": root_height_bound - 36,
            "cols": cols,
            "rows": rows,
            "cache_shape": [30, 40],
            "largest_flat_index": flat,
            "signed_16bit_bounds": signed_int_bounds,
            "paths": {
                "move": "preserves extent; persists object-0 origin/size; refreshes active controls",
                "zoom_and_restore": "constraint-bound zoom target or saved zoomRect; refreshes controls; restored extent was previously bounded",
                "load_and_offsets": "LoadAllWindows resets then applies selected kind-9 offsets; lock-time loads/reloads apply cached object-0 rects; root profile-8 has no HCEGANT override",
                "open_close": "root flags 050E lack 1000 (translate/save-restore) and 0800 (unload offset save); active controls are rebuilt",
                "unload": "win_UnlockWin offset write is gated by flag 0800; not set for root 0",
                "other_writers": "f_20E8_0903 is definition-only; win_Swap callers are windows 1900/0100; f_22BF_00DD callers are objects 1602/1A01",
                "save_restore": "reviewed SaveRec contains no window-offset geometry record; S09 load does not write root-0 geometry",
            },
        },
        "negative_control": None,
    }
    if run_negative:
        negative_mouse = mickey_control(image)
        facts["negative_control"] = {
            "original_mickey": negative_mouse,
            "resize_composition": resize_negative_control(negative_mouse),
        }
    return facts


def check() -> dict:
    expected_path = PACKAGE / "domain-facts.json"
    expected = json.loads(expected_path.read_bytes())
    actual = collect()
    if actual != expected:
        raise AssertionError("domain-facts.json differs from the replayed source/resource/original-code facts")
    return actual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-facts", action="store_true", help="write fresh worker facts JSON")
    group.add_argument("--check", action="store_true", help="replay and compare against domain-facts.json")
    args = parser.parse_args()
    if args.write_facts:
        result = collect()
        (PACKAGE / "domain-facts.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        result = check()
    print(json.dumps({"ok": True, "schema": result["schema"],
                      "rows": result["geometry_bound"]["rows"],
                      "columns": result["geometry_bound"]["cols"],
                      "mickey_negative_rows": result["negative_control"]["resize_composition"]["rows"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
