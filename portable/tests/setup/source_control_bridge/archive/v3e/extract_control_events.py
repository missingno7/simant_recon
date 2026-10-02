#!/usr/bin/env python3
"""Create the isolated source-backed control handler draft."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"portable/tools"))
import recover_source
import word_spelling

SOURCE=ROOT/"src/root/m0798.c"
OUT=Path(__file__).resolve().parent/"source_control_events_extracted.c"
NAMES=("ProcCasteEvent","ProcModeEvent","IsPointInIsoTri","BoundPointToTri","GetTriLatDist")
PROVIDERS={"clip_SetWin":"source_clip_set","clip_Off":"source_clip_off",
 "DoWinHelp":"source_help","win_MakeGroupInvisible":"source_group_invisible",
 "win_MakeGroupVisible":"source_group_visible","win_MakeObjSelected":"source_select_object",
 "win_GetObjRect":"source_get_rect","win_DrawCasteWindow":"source_draw_caste",
 "win_DrawModeWindow":"source_draw_mode","f_1FD2_04D0":"source_pointer_update",
 "StillDown":"source_still_down","_fmemcpy":"source_copy_bytes",
 "_fmemcmp":"source_compare_bytes","GetTriLatDist":"source_GetTriLatDist"}
PRIVATE={"g_1B50":"(*source_mode_selector)","g_1B4E":"(*source_caste_selector)",
 "g_1B62":"(*source_mode_percent)","g_1B64":"(*source_caste_percent)"}

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def replace_identifier(text:str,name:str,replacement:str)->str:
    return re.sub(r"\b"+re.escape(name)+r"\b",lambda _:replacement,text)

def lower_trilevel(body:str)->str:
    body=re.sub(r"struct\s+TriLevel\s*\*\s*level", "uint16_t *level", body)
    body=re.sub(r"\blevel\s*->\s*frac\b","level[0]",body)
    body=re.sub(r"\blevel\s*->\s*mid\b","level[1]",body)
    body=re.sub(r"\blevel\s*->\s*weight\b","level[2]",body)
    return body

def adapt(name:str,body:str)->tuple[str,dict]:
    explicit,count=word_spelling.explicit_unsigned_word(body)
    transformed,excluded,ax= recover_source.transform(explicit)
    if excluded or ax:raise RuntimeError(f"unexpected base transform for {name}")
    transformed=transformed.replace('#include "recovered_state.h"\n','')
    if name=="GetTriLatDist":transformed=lower_trilevel(transformed)
    for source,replacement in PROVIDERS.items():transformed=replace_identifier(transformed,source,replacement)
    for source,replacement in PRIVATE.items():transformed=replace_identifier(transformed,source,replacement)
    # RecoveredState stores all control levels and presets as flat uint16_t
    # arrays. Preserve six-byte source copies, translating struct-row indexing
    # into three-word offsets without pointer punning.
    for name_in,sel in (("fd_3D57_0810","source_mode_selector"),
                        ("fd_3D57_07F2","source_caste_selector")):
        transformed=re.sub(r"&"+name_in+r"\s*\[\s*\(\*"+sel+r"\)\s*\]",
                           r"&"+name_in+r"[(uint16_t)(*"+sel+r") * 3u]",transformed)
    transformed=re.sub(r"&\s*modeLevels\b","modeLevels",transformed)
    transformed=re.sub(r"&\s*casteLevels\b","casteLevels",transformed)
    if "&fd_3D57_0810[(*source_mode_selector)]" in transformed or "&fd_3D57_07F2[(*source_caste_selector)]" in transformed:
        raise RuntimeError(f"unlowered struct preset row in {name}")
    row={"function":name,"source_body_sha256":sha(body.encode()),
         "word_spelling_replacements":count,"generated_body_sha256":sha(transformed.encode()),
         "provider_renames":PROVIDERS,"private_state_aliases":PRIVATE}
    return transformed,row

def main()->None:
    srcbytes=SOURCE.read_bytes();source=srcbytes.decode("latin1")
    chunks=["/* Generated only for the source_control_integration draft. */\n",
            '#include "source_control_integration.h"\n']
    rows=[]
    for name in NAMES:
        body,start,end=recover_source.extract_named_function(source,name)
        generated,row=adapt(name,body)
        chunks.append(f"\n/* {name} source lines {start}-{end-1}; original source definition sha256 {row['source_body_sha256']} */\n{generated}\n")
        row["source_lines"]={"start":start,"end":end-1}
        rows.append(row)
    payload="".join(chunks).encode("utf-8")
    OUT.write_bytes(payload)
    report={"schema":"source-control-event-extraction-v1","source":"src/root/m0798.c",
      "source_sha256":sha(srcbytes),"generated":"build/workers/source_control_integration/source_control_events_extracted.c",
      "generated_sha256":sha(payload),"functions":rows,
      "transform_chain":["portable/tools/word_spelling.py: explicit_unsigned_word",
        "portable/tools/recover_source.py: extract_named_function and transform",
        "explicit flat-three-word access lowering; no strict-alias pointer casts"]}
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
