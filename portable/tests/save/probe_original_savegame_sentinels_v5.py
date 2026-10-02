"""Run original DOS SaveGame over address-keyed native-state sentinels."""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

OUT = ROOT / "build/workers/savegame_sentinel_v5"
OUT.mkdir(parents=True, exist_ok=True)
PAYLOAD = OUT / "original-dos-sentinel-stream.bin"
SOURCE = ROOT / "src/S09/m35F5.c"
INVENTORY = ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"
SYMBOLS = ROOT / "layout/symbols.json"

def sentinel(address: int) -> int:
    x = address & 0xffffffff
    x ^= x >> 11
    x = (x * 0x045D9F3B) & 0xffffffff
    x ^= x >> 16
    return (x ^ (x >> 8) ^ (x >> 24)) & 0xff

def main() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))["table"]["records"]
    data_symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))["data"]
    rows = []
    init_writes = []
    for index, row in enumerate(inventory):
        expr = row["pointer_expression"].strip()
        interior = 0
        if expr.startswith("&"): name = expr[1:]
        elif expr == "(fd_3D57_087A + 20)": name, interior = "fd_3D57_087A", 20
        else: raise RuntimeError(f"unsupported pointer expression at row {index}: {expr}")
        symbol = data_symbols.get(name)
        if symbol is None: raise RuntimeError(f"source-address map lacks row {index} symbol {name}")
        linear = symbol["seg"] * 16 + symbol["off"] + interior
        size = row["serialized_bytes"]
        expected = bytes(sentinel(linear + i) for i in range(size))
        init_writes.append((linear, expected))
        rows.append({"index":index,"expression":expr,"source_symbol":name,"linear":linear,
                     "size":size,"expected_hex":expected.hex()})

    expected_rows = iter(rows)
    observed = []
    def controlled_write(machine, args):
        if len(args) != 4: raise RuntimeError(f"unexpected write ABI args {args}")
        fd, off, seg, count = args
        row = rows[len(observed)]
        start = seg * 16 + off
        actual = machine.read(start, count)
        if fd != 7 or start != row["linear"] or count != row["size"]:
            raise RuntimeError(f"DOS SaveRec row {len(observed)} disagrees with independent source map: "
                               f"got fd/start/size={fd}/{start:#x}/{count}, expected=7/{row['linear']:#x}/{row['size']}")
        expected = bytes(sentinel(start + i) for i in range(count))
        if actual != expected:
            raise RuntimeError(f"DOS SaveRec row {len(observed)} did not read its address-keyed sentinel")
        observed.append(actual)
        return count

    callbacks = {
        "open": behavior.Callback(3, handler=lambda machine, args: 7),
        "write": behavior.Callback(4, handler=controlled_write),
        "close": behavior.Callback(1, handler=lambda machine, args: 0),
        "f_1C62_0415": behavior.Callback(3, handler=lambda machine, args: 0),
        "f_1C62_00C0": behavior.Callback(2, handler=lambda machine, args: 0),
    }
    pair = behavior.PreparedPair("o09_35F5_0188", source=SOURCE,
                                 out="build/workers/savegame_sentinel_v5/prepared")
    last_name = behavior.symbol_address("fd_50F6_3862")
    dirty = behavior.symbol_address("fd_3D57_02C2")
    case = behavior.Case("SaveGame/address-keyed-sentinel", args=[1],
        writes=[*init_writes,(last_name,b"SENTINEL.ANT\0"),(dirty,b"\x01\x00")],
        callbacks=callbacks,return_kind="s16",observe=[behavior.Range("dirty",dirty,2)])
    result = pair.original_machine.run(case)
    if len(observed) != 307: raise RuntimeError(f"expected 307 DOS write calls, observed {len(observed)}")
    payload = b"".join(observed)
    PAYLOAD.write_bytes(payload)
    if len(payload) != 48386: raise RuntimeError(f"wrong DOS sentinel payload extent {len(payload)}")
    expected = b"".join(bytes.fromhex(row["expected_hex"]) for row in rows)
    if payload != expected: raise RuntimeError("DOS output differs from independent layout-address sentinel stream")
    report = {"schema":"simant-savegame-original-address-sentinels-v5",
      "status":"PASS_ORIGINAL_DOS_SOURCE_ADDRESS_TRACE",
      "function":"o09_35F5_0188","source_sha256":behavior.digest(SOURCE.read_bytes()),
      "oracle_sha256":behavior.exe.load().sha256,"harness_sha256":behavior.digest(behavior.HARNESS_SOURCE),
      "layout_symbols_sha256":hashlib.sha256(SYMBOLS.read_bytes()).hexdigest(),
      "inventory_sha256":hashlib.sha256(INVENTORY.read_bytes()).hexdigest(),
      "rows":rows,"write_calls":len(observed),"payload_bytes":len(payload),
      "payload_sha256":hashlib.sha256(payload).hexdigest(),
      "independent_source_address_expected_stream_sha256":hashlib.sha256(expected).hexdigest(),
      "payload_matches_address_stream":True,"dirty_after":result["ranges"]["dirty"],"return":result["return"],
      "payload_path":str(PAYLOAD.relative_to(ROOT)).replace("\\","/"),
      "limitations":["Original DOS function is executed; CRT file boundaries are controlled callbacks.",
                      "No native live file write is performed; payload stays under ignored build/workers."]}
    (OUT/"original-dos-sentinel-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="")
    print(json.dumps({"status":report["status"],"rows":len(rows),"bytes":len(payload),
                      "payload_sha256":report["payload_sha256"],"dirty":report["dirty_after"],
                      "return":report["return"]},indent=2))

if __name__ == "__main__": main()
