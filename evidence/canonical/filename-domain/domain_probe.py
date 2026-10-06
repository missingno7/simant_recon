"""FileSelect supported-domain capacities (gate filename-selector-local-capacity).

Checks the canonical S09 source facts every capacity bound depends on, then
computes the worst-case byte requirement of each FileSelect write under the
supported-domain premises:
  * incoming uninitialized name: strlen <= 46 (a NUL within name[0..46]);
  * every selected DOS directory string, including "X:\\", <= 32 characters;
  * DOS 8.3 file and directory names;
  * fewer than 200 listed entries (subdirectories plus *.ant files) per directory.
Out-of-domain contrasts (66-character inherited directory, L=33 retry, 200
entries, long incoming residue) are computed and retained, not waived.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
sys.dont_write_bytecode = True
import canonical
import csrc

SOURCE = "src/S09/m35F5.c"
PREMISES = {"incoming_name_max_strlen": 46, "max_directory_chars": 32, "max_leaf_chars": 12,
            "max_listed_entries": 199}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def norm(text: str) -> str:
    return " ".join(t.text for t in csrc.tokenize(text) if t.kind not in {"ws", "nl", "cmt"})


def function(text: str, name: str) -> str:
    fn = csrc.Source(text).function(name)
    return norm(text[fn.head_s:fn.body.e])


REQUIRED = {
    "LoadGame": ["char name [ 100 ] ;", "o09_35F5_03C6 ( name , \"Load Game\" , \"LOAD\" , 0 )"],
    "o09_35F5_0188": ["char name [ 100 ] ;", "_fstrcpy ( name , fd_50F6_3862 ) ; goto tryit ;",
                      "if ( o09_35F5_03C6 ( name , \"Save Game\" , \"SAVE\" , 1 ) == 0 )"],
    "o09_35F5_03C6": [
        "char buf [ 80 ] ;", "char path [ 67 ] ;", "char fname [ 14 ] ;",
        "if ( * name != 0 && f_1F66_00AF ( s_2966 - '@' , path ) != 0 ) { if ( path [ _fstrlen ( path ) - 1 ] != '\\\\' ) _fstrcat ( path , \"\\\\\" ) ; sprintf ( buf , \"%s%s\" , path , name ) ; _fstrcpy ( name , buf ) ; }",
        "h = f_171C_13CA ( 0xC80L , 0 , \"File list\" ) ;",
        "* name = fname [ 0 ] = 0 ;",
        "sprintf ( buf , \"%s*.*\" , path ) ;",
        "_fstrcpy ( name , _fstrrchr ( fd_50F6_3862 , '\\\\' ) + 1 ) ;",
        "if ( count >= 200 - s_2968 ) break ;",
        "sprintf ( p + 1 , \"\\1%s>\" , ff . name ) ;", "nDirs ++ ; * p = '0' ; p += 16 ;",
        "* p ++ = '0' ; sprintf ( p , \"%-12s\" , ff . name ) ; p += 15 ;",
        "* p = 0 ;",
        "o09_36EE_0092 ( x , y , name , 9 , 0 ) ;",
        "sprintf ( buf , \"%c:%s\" , s_2966 , name + 1 ) ;",
        "_fstrcpy ( lastDir , path ) ; _fstrcpy ( buf , name ) ; sprintf ( name , \"%s%s\" , path , buf ) ;",
    ],
    "o09_35F5_0D2B": ["for ( i = 0 ; i < 8 ; i ++ )", "_fstrcpy ( name , \".ant\" ) ;"],
}


def capacities(premises: dict) -> list[dict]:
    """Worst-case bytes (including NUL) per write; P = directory prefix after the separator."""
    L, S, F, N = (premises["max_directory_chars"], premises["incoming_name_max_strlen"],
                  premises["max_leaf_chars"], premises["max_listed_entries"])
    P = L + 1
    rows = [
        ("path after drive helper and separator append", P + 1, 67),
        ("lastDir copy of path", P + 1, 67),
        ("initial path+incoming name into buf", P + S + 1, 80),
        ("copy-back of buf into name", P + S + 1, 100),
        ("listing filespec path*.* in buf", P + 3 + 1, 80),
        ("directory entry \\1name> at list+1", 1 + 1 + F + 1 + 1, 16),
        ("file entry '0' + %-12s", 1 + max(F, 12) + 1, 16),
        ("list terminator after N entries", N * 16 + 1, 0xC80),
        ("drive-relative chdir argument in buf", 2 + F + 1 + 1, 80),
        ("leaf copy into buf", F + 1, 80),
        ("returned path+leaf into name", P + F + 1, 100),
        ("declined-overwrite retry: path + previous full path", P + (L + 1 + F) + 1, 80),
    ]
    return [{"write": w, "bytes": b, "capacity": c, "fits": b <= c} for w, b, c in rows]


def collect(program_override=None, source_overrides=None) -> dict:
    program = program_override or canonical.load()
    row = next(m for m in program["modules"] if m["source"] == SOURCE)
    raw = (source_overrides or {}).get(SOURCE) or (ROOT / SOURCE).read_bytes()
    if sha(raw) != row["source_sha256"]:
        raise ValueError("canonical S09 source pin differs")
    text = raw.decode("latin1")
    definitions = {}
    for name, needles in REQUIRED.items():
        body = function(text, name)
        for needle in needles:
            if needle not in body:
                raise AssertionError(f"{name}: missing {needle}")
        definitions[name] = sha(body.encode())
    if "static char lastDir [ 67 ] ;" not in norm(text) or "static int s_2968 = 0 ;" not in norm(text):
        raise AssertionError("FileSelect statics changed")
    if norm(text).count("s_2968 =") != 1:
        raise AssertionError("s_2968 gained a writer")
    supported = capacities(PREMISES)
    if not all(r["fits"] for r in supported):
        raise AssertionError("a supported-domain write exceeds its capacity")
    contrasts = {
        "incoming_name_strlen_47": capacities({**PREMISES, "incoming_name_max_strlen": 47}),
        "directory_33_chars": capacities({**PREMISES, "max_directory_chars": 33}),
        "directory_66_chars_inherited": capacities({**PREMISES, "max_directory_chars": 66}),
        "listed_entries_200": capacities({**PREMISES, "max_listed_entries": 200}),
    }
    for name, rows in contrasts.items():
        if all(r["fits"] for r in rows):
            raise AssertionError(f"negative contrast {name} unexpectedly fits")
    receipt = json.loads((Path(__file__).parent / "receipt.json").read_text())
    if receipt.get("status") != "POSITIVE_AND_NEGATIVE_CONFIRMED":
        raise AssertionError("DOSBox-X deep-path control receipt changed")
    return {
        "schema": "simant-fileselect-domain-v1",
        "premises": PREMISES,
        "function_definition_sha256": definitions,
        "supported_capacities": supported,
        "negative_contrasts": {k: [r for r in v if not r["fits"]] for k, v in contrasts.items()},
        "observed_residue": "residue-receipt.json (0..15 bytes on every ordinary chain, both builds)",
        "dosbox_deep_path_control": {"receipt_sha256": sha((Path(__file__).parent / "receipt.json").read_bytes())},
    }


def check() -> dict:
    actual = collect()
    expected = json.loads((Path(__file__).parent / "domain-facts.json").read_text())
    if actual != expected:
        raise ValueError("FileSelect domain facts differ from reviewed facts")
    return actual


if __name__ == "__main__":
    if "--write-facts" in sys.argv:
        (Path(__file__).parent / "domain-facts.json").write_text(json.dumps(collect(), indent=2) + "\n")
    print(json.dumps({k: v for k, v in check().items() if k == "premises"}))
