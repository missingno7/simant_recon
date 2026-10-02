"""Emit source-pinned host lifecycle facts for the legacy SaveGame/LoadGame flow."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "portable/tests/save/evidence/legacy-save-host-lifecycle-v1/contract.json"
S09 = ROOT / "src/S09/m35F5.c"
S15 = ROOT / "src/S15/m384C.c"
S08 = ROOT / "src/S08/m35F5.c"
PRODUCER = Path(__file__)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def function_body(text: str, name: str):
    m = re.search(r"(?m)^\s*(?:int|void)\s+far\s+" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", text)
    if not m: raise ValueError(f"missing function {name}")
    start = text.find("{", m.start()); depth = 0; quoted = None; escaped = False
    for pos in range(start, len(text)):
        ch = text[pos]
        if quoted:
            if escaped: escaped = False
            elif ch == "\\": escaped = True
            elif ch == quoted: quoted = None
        elif ch in ("'", '"'): quoted = ch
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                body = text[m.start():pos+1]
                return {"line_start":text.count("\n",0,m.start())+1,
                        "line_end":text.count("\n",0,pos+1)+1,
                        "body_sha256":sha(body.encode("latin1"))}
    raise ValueError(f"unbalanced function {name}")

def main():
    s09, s15, s08 = (p.read_text(encoding="latin1") for p in (S09, S15, S08))
    funcs = {
        "LoadGame": function_body(s09, "LoadGame"),
        "SaveGame": function_body(s09, "o09_35F5_0188"),
        "FileSelect": function_body(s09, "o09_35F5_03C6"),
        "ResetYardBeforeLoad": function_body(s09, "o09_35F5_0D7A"),
        "RebuildDerivedAfterLoad": function_body(s09, "o09_35F5_0DBB"),
        "DirtyPrompt": function_body(s15, "o15_384C_0239"),
        "RandYard": function_body(s08, "RandYard"),
    }
    record_inventory = json.loads((ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json").read_text(encoding="utf-8"))
    payload = sum(r["serialized_bytes"] for r in record_inventory["table"]["records"])
    contract = {
        "schema":"simant-savegame-host-lifecycle-contract-v1",
        "status":"SOURCE_GROUNDED_DESIGN_NOT_INTEGRATED",
        "inputs":{"S09":{"path":"src/S09/m35F5.c","sha256":sha(S09.read_bytes())},
                   "S15":{"path":"src/S15/m384C.c","sha256":sha(S15.read_bytes())},
                   "S08":{"path":"src/S08/m35F5.c","sha256":sha(S08.read_bytes())},
                   "contract_producer":{"path":"portable/tests/save/write_lifecycle_contract.py",
                                        "sha256":sha(PRODUCER.read_bytes())},
                   "SaveRec_inventory":{"path":"portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json",
                                        "sha256":sha((ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json").read_bytes()),
                                        "rows":len(record_inventory["table"]["records"]),"payload_bytes":payload}},
        "function_anchors":funcs,
        "format":{"records":307,"terminator_rows":1,"payload_bytes":payload,
                   "stream":"concatenated SaveRec rows in source order, no header, no trailing read on load"},
        "dirty_load_gate":{"prompt":"o15_384C_0239(0)",
                           "result_2":"return failure without opening a selector; preserve dirty state",
                           "result_1":"call SaveGame(useLast=0); if it returns 0 repeat prompt; any nonzero save result continues",
                           "other_result":"continue to file selector",
                           "prompt_result_values":"0=discard/continue; 1=save; 2=cancel, source-defined by keyboard and event switches"},
        "load_sequence":[
            "FileSelect(name, 'Load Game', 'LOAD', 0); zero means cancel and returns failure before last-name or dirty changes.",
            "On selection, copy name to lastFileName and clear dirty before attempting open.",
            "Open O_RDONLY|O_BINARY; fd <= 0 is treated as failure; report error and return failure with dirty already clear and selected lastFileName retained.",
            "Before the first read, o09_35F5_0D7A resets selected controls and calls S08 RandYard. RandYard clears arrays, resets yard/world controls, sets yard dimensions, generates 192 seed-table words with RRand(0x7fff), passes the selected table word to RandWorld (which initializes S-RNG), and restores the active ant location. These mutations happen before the first file read.",
            "Read each of 307 records once, requesting exactly size*count bytes. Any result other than the full count, including a positive short read or -1, reports error, stores fd_50F6_0EAC=-1, closes, and returns failure.",
            "There is no state snapshot/rollback: RandYard reset and all earlier/partial destination writes survive a later read failure.",
            "No trailing-byte read/check occurs; a valid prefix is accepted even if the file has extra bytes.",
            "On complete reads, close is called and its result ignored; then UI refresh, derived life-map/count rebuild and optional StopSong run."],
        "save_sequence":[
            "When useLast!=0 and lastFileName is nonempty, copy it and bypass FileSelect; otherwise select with ('Save Game','SAVE',save=1). Selector cancel returns 0 without clearing dirty.",
            "Once a path is selected, copy it to lastFileName before opening/confirmation.",
            "First open O_RDWR|O_BINARY. fd>0 means existing: ask overwrite. Result 0 proceeds; nonzero closes (close result ignored) and returns to selector.",
            "If first open returns <=0, try O_RDWR|O_CREAT|O_TRUNC|O_BINARY with read/write mode. Create failure reports error, clears only the first lastFileName byte, and returns 0.",
            "Existing accepted files are not truncated and writes are not explicitly sought; an old longer tail can remain.",
            "Write each SaveRec row once in order. Only exactly -1 is considered failure; positive short writes are accepted and later rows continue.",
            "On -1, clear first lastFileName byte, report error, close ignoring its result, remove(name), and return 0.",
            "After all row calls, clear dirty before success message and close; both success-message result and close result are ignored; copy name to lastFileName and return 1."],
        "host_design_constraints":[
            "Separate file selection, overwrite confirmation, open/read/write/close/remove, diagnostics, and game-state codec as typed effects; never infer a successful full write from a generic boolean.",
            "Source-compatible mode must decide explicitly whether to preserve positive-short-write acceptance, existing-file non-truncation, fd<=0 tests, no rollback on failed loads, and ignored close errors.",
            "A transactional staged load, full-write loop, atomic replacement, or guaranteed tail truncation is a sensible host policy but differs from the DOS flow and requires an explicit behavior-version boundary.",
            "Cancellation before a path is selected leaves save-state dirty data intact. Once load selection is accepted, the DOS code clears dirty before open and does not restore it after failure.",
            "`o09_35F5_0D7A` executes RandYard before reading record 0; a failed/short load is not side-effect free and can alter terrain, random-dependent state, and current derived world before any file row is accepted."],
        "limitations":["This document is a source-grounded lifecycle design contract, not a SaveGame/LoadGame native DOS differential or a filesystem implementation.",
                       "V2 codec evidence proves 307-row payload binding, not load rollback, prompting, file replacement, or I/O error behavior."]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract,indent=2)+"\n",encoding="utf-8",newline="")
    print(f"lifecycle_contract=PASS rows={payload and 307} bytes={payload} funcs={len(funcs)}")

if __name__ == "__main__": main()
