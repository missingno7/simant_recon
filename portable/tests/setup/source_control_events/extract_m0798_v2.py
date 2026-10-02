#!/usr/bin/env python3
"""Extract named root:m0798 bodies with the repository's fixed-width transform."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"portable/tools"))
import recover_source

SOURCE=ROOT/"src/root/m0798.c"
OUT=Path(__file__).resolve().parent/"m0798_extracted_v2.c"
FUNCTIONS=("ProcCasteEvent","ProcModeEvent","IsPointInIsoTri","BoundPointToTri",
           "cvtLevels2IdealCaste","GetTriLatDist","SetTriLatPoint")

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def map_default_unsigned_to_dos_word(code:str)->str:
    """Map C's DOS default-int `unsigned` spelling to the 16-bit target word."""
    parts=__import__("re").split(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*)',code,flags=__import__("re").S)
    for i in range(0,len(parts),2):
        parts[i]=__import__("re").sub(r"\bunsigned\b","uint16_t",parts[i])
    return "".join(parts)

def main()->None:
    raw=SOURCE.read_bytes();text=raw.decode("utf-8")
    chunks=[]; rows=[]
    for name in FUNCTIONS:
        body,start,end=recover_source.extract_named_function(text,name)
        transformed,excluded,adapted=recover_source.transform(body)
        transformed=transformed.replace('#include "recovered_state.h"\n','')
        transformed=map_default_unsigned_to_dos_word(transformed)
        if excluded or adapted:raise RuntimeError(f"unexpected scaffold/return transform for {name}")
        chunks.append(f"/* Extracted {name}; source lines {start}-{end-1}; original-body-sha256 {sha(body.encode())}. */\n{transformed}\n")
        rows.append({"name":name,"source_lines":{"start":start,"end":end-1},
                     "original_body_sha256":sha(body.encode()),
                     "transformed_body_sha256":sha(transformed.encode()),
                     "transform":"recover_source.transform for int16_t/uint16_t/int32_t and far removal; additionally maps bare DOS unsigned (default-int spelling) to uint16_t outside comments/literals"})
    generated=("/* Generated from frozen src/root/m0798.c by extract_m0798.py. */\n"
               "#include \"source_control_events.h\"\n\n"+"\n".join(chunks))
    OUT.write_text(generated,encoding="utf-8",newline="")
    print(json.dumps({"source_sha256":sha(raw),"generated_sha256":sha(OUT.read_bytes()),
                      "generated":OUT.relative_to(ROOT).as_posix(),"functions":rows},indent=2))

if __name__=="__main__":main()
