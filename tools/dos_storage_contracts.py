"""Read-only validator for root-authored v24 storage-contract candidates.

The JSON contract is evidence; policy is the independent root literal.  This
module reads only those two JSON documents.  It never opens pinned binaries,
maps, logs, source files, or invokes a compiler/linker/emulator.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any


class GateError(ValueError):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise GateError(message)


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def normalized_publics(section: Any) -> dict[str, str]:
    need(isinstance(section, dict), "public matrix section must be a name/address object")
    out: dict[str, str] = {}
    for name, address in section.items():
        need(isinstance(name, str) and name, "empty public name")
        need(isinstance(address, str) and re.fullmatch(r"[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}", address),
             f"invalid address for {name}")
        key = name.casefold()
        need(key not in out, f"duplicate public name {name}")
        out[key] = address.upper()
    return out


def addr_parts(text: str) -> tuple[int, int]:
    seg, off = text.split(":")
    return int(seg, 16), int(off, 16)


def same_names(actual: Any, expected: Any) -> bool:
    if not isinstance(actual, list) or not isinstance(expected, list):
        return False
    if not all(isinstance(v, str) and v for v in actual + expected):
        return False
    a, e = [v.casefold() for v in actual], [v.casefold() for v in expected]
    return len(a) == len(set(a)) and sorted(a) == sorted(e)


def _check_omf(contract: dict[str, Any], policy: dict[str, Any]) -> None:
    observed = contract.get("compiler_controls")
    rules = policy.get("compiler_controls")
    need(isinstance(observed, dict) and isinstance(rules, dict) and rules,
         "compiler_controls and independent policy rules are required")
    need(set(observed) == set(rules), "compiler control key set differs from policy")
    for key, rule in rules.items():
        obj = observed[key]
        need(isinstance(obj, dict), f"{key}: OMF shape must be an object")
        need(rule.get("owner_names"), f"{key}: empty owner-name policy")
        need(obj.get("module_name") == rule["module_name"], f"{key}: module name mismatch")
        owner_names = {n.casefold() for n in rule["owner_names"]}
        all_comm = obj.get("communals", [])
        rows = all_comm if rule.get("full_communals") else [
            r for r in all_comm if r.get("name", "").casefold() in owner_names]
        shape = [{k: r.get(k) for k in ("name", "kind", "count", "element_size", "length")}
                 for r in rows]
        comm_literal = rule.get("all_communals", []) if rule.get("full_communals") else rule["owner_communals"]
        expected = [{k: r.get(k) for k in ("name", "kind", "count", "element_size", "length")}
                    for r in comm_literal]
        need(canon(shape) == canon(expected), f"{key}: owner communal OMF shape mismatch")
        all_publics = obj.get("publics", [])
        publics = all_publics if rule.get("full_publics") else [
            r for r in all_publics if r.get("name", "").casefold() in owner_names]
        publics_literal = rule.get("all_publics", []) if rule.get("full_publics") else rule["owner_publics"]
        expected_publics = [{k: r.get(k) for k in ("name", "segment", "offset")}
                             for r in publics_literal]
        need(canon(publics) == canon(expected_publics), f"{key}: owner PUBDEF shape mismatch")
        lengths = obj.get("segment_lengths", {})
        if rule.get("full_segment_lengths"):
            need(lengths == rule.get("all_segment_lengths"), f"{key}: full segment length table mismatch")
        for segment, size in rule.get("segment_lengths", {}).items():
            need(lengths.get(segment) == size, f"{key}: {segment} length mismatch")
        data = obj.get("initialized_data_hex", {})
        if rule.get("full_initialized_data"):
            need(data == rule.get("all_initialized_data_hex"), f"{key}: complete initialized-data table mismatch")
        for segment, rawhex in rule.get("initialized_data_hex", {}).items():
            need(data.get(segment) == rawhex, f"{key}: initialized {segment} bytes mismatch")
            need(len(rawhex) % 2 == 0, f"{key}: malformed initialized-data hex")
        # Policies name only target data segments; debugger, CONST, and CODE
        # payloads are deliberately outside this semantic comparison.
        target_segments = set(rule.get("segment_lengths", {})) | set(rule.get("initialized_data_hex", {}))
        fixups = [f for f in obj.get("linker_fixups", []) if f.get("segment") in target_segments]
        projection = ("segment", "offset", "width", "loc", "self_relative", "target_kind",
                      "target", "frame_kind", "frame", "displacement", "encoded_addend")
        got = [{k: f.get(k) for k in projection} for f in fixups]
        want = [{k: f.get(k) for k in projection} for f in rule.get("linker_fixups", [])]
        need(canon(got) == canon(want), f"{key}: target-data-segment fixup geometry mismatch")
        if rule.get("data_only"):
            need(lengths == rule["segment_lengths"] and data == rule["initialized_data_hex"],
                 f"{key}: complete natural owner segments changed")
            need(canon(shape) == canon(expected) and len(all_comm) == len(expected)
                 and canon(all_publics) == canon(expected_publics),
                 f"{key}: extra natural owner storage or publics")
            need(obj.get("externals") == [r["name"] for r in all_comm],
                 f"{key}: natural owner has unrelated externals")
        if rule.get("no_external_fixups"):
            need(not any(f.get("target_kind") == "external" for f in obj.get("linker_fixups", [])),
                 f"{key}: unexpected external fixup in natural owner/control object")


def validate(contract: dict[str, Any], policy: dict[str, Any]) -> int:
    # Admission requires a separately reviewed source and raw evidence packet.
    for key in ("module", "root_reviewed", "all_required_checks_pass", "communals",
                "required_cases", "inputs", "cases", "probe_source"):
        need(key in contract, f"missing generic contract field {key}")
    need(contract["module"] == policy["module"], "module mismatch")
    need(contract["root_reviewed"] is True and contract["all_required_checks_pass"] is True,
         "review flags are false; candidate is not admitted")
    need(canon(contract["communals"]) == canon(policy["communals"]), "provider communal layout differs from root literal")
    required = policy["required_cases"]
    need(contract["required_cases"] == required, "required case marker matrix differs from root literal")
    need(set(required.values()) == {"PASS", "FAIL"}, "case matrix must contain positive and negative controls")
    linkers = policy["linkers"]
    need(linkers == ["rtlink400", "rtlink610"], "policy must use the reviewed rtlink400/rtlink610 pair")
    inputs = contract["inputs"]
    need(isinstance(inputs, list) and inputs, "strict source/tool/runtime input pins are required")
    seen_inputs: set[tuple[str, str]] = set()
    for pin in inputs:
        need(all(k in pin for k in ("path", "sha256", "size")), "input pin missing path/hash/size")
        need(re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None and pin["size"] > 0,
             f"invalid input pin {pin.get('path')}")
        identity = (pin["path"].casefold(), pin["sha256"])
        need(identity not in seen_inputs, "duplicate input pin")
        seen_inputs.add(identity)
    expected_keys = {(linker, case) for linker in linkers for case in required}
    rows = contract["cases"]
    need(isinstance(rows, list) and len(rows) == len(expected_keys), "case matrix has missing/extra rows")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.get("linker"), row.get("case"))
        need(key in expected_keys and key not in seen, f"unexpected or duplicate case {key}")
        seen.add(key)
        marker = required[key[1]]
        need(row.get("expected") == marker and row.get("actual") == marker,
             f"{key}: expected/actual marker mismatch")
        raw = row.get("raw", {})
        need(raw.get("hex") == (marker + "\r\n").encode("ascii").hex(),
             f"{key}: raw bytes are not the full CRLF marker")
        raw_bytes = bytes.fromhex(raw["hex"])
        digest = hashlib.sha256(raw_bytes).hexdigest()
        need(raw.get("sha256") == digest and raw.get("size") == len(raw_bytes), f"{key}: raw hash/size mismatch")
        pin = raw.get("artifact_pin", {})
        need(pin.get("sha256") == digest and pin.get("size") == len(raw_bytes) and pin.get("path"),
             f"{key}: raw artifact pin mismatch")
        for pin_name in ("link_pin", "map_pin"):
            lp = row.get(pin_name, {})
            need(lp.get("path") and re.fullmatch(r"[0-9a-f]{64}", lp.get("sha256", "")) and
                 isinstance(lp.get("size"), int) and lp["size"] > 0,
                 f"{key}: original {pin_name} is missing or malformed")
        need(row.get("runner_exit") == 0 and row.get("timed_out") is False, f"{key}: runner not clean")
        need(row.get("clean") is True and row.get("linker_diagnostics") == [] and
             row.get("linker_produced_executable") is True and row.get("linker_produced_map") is True,
             f"{key}: clean link metadata mismatch (no linker exit is inferred)")
        owners = policy["owners"]
        need(same_names(row.get("expected_owner_publics"), owners), f"{key}: expected owner list mismatch")
        need(same_names(row.get("owner_publics_found"), owners), f"{key}: found owner list mismatch")
        maps = row.get("map_sections", {})
        matrix = row.get("public_address_matrix", {})
        need(set(maps) == {"Name", "Value"} and set(matrix) == {"Name", "Value"}, f"{key}: both map sections required")
        sections = {name: normalized_publics(matrix[name]) for name in ("Name", "Value")}
        need(sections["Name"] == sections["Value"], f"{key}: Name/Value public matrices differ")
        for name in ("Name", "Value"):
            heading = maps[name]
            need(heading.get("heading_present") is True and heading.get("heading_count") == 1,
                 f"{key}: {name} section heading count mismatch")
            need(heading.get("public_count") == len(sections[name]), f"{key}: {name} public count mismatch")
            need(all(owner.casefold() in sections[name] for owner in owners), f"{key}: owner public absent from map")
        aliases = row.get("aliases")
        expected_aliases = policy["aliases"].get(key[1], [])
        alias_key = lambda x: (x.get("alias", "").casefold(), x.get("target", "").casefold(), x.get("delta"))
        need(isinstance(aliases, list) and sorted(map(alias_key, aliases)) ==
             sorted(map(alias_key, expected_aliases)), f"{key}: alias rows differ from root literal")
        need(len({alias_key(x) for x in aliases}) == len(aliases), f"{key}: duplicate alias row")
        for alias in aliases:
            a, t = alias["alias"].casefold(), alias["target"].casefold()
            need(a in sections["Name"] and t in sections["Name"], f"{key}: alias/target absent")
            aseg, aoff = addr_parts(sections["Name"][a]); tseg, toff = addr_parts(sections["Name"][t])
            need(aseg == tseg and aoff - toff == alias["delta"], f"{key}: alias delta does not recompute")
    need(seen == expected_keys, "incomplete linker/case cross-product")
    need(set(policy.get("aliases", {})) == set(required), "alias policy is incomplete")
    _check_omf(contract, policy)
    fixups = contract.get("save_rec_pointer_fixups")
    need(isinstance(fixups, list) and canon(fixups) == canon(policy["save_rec_pointer_fixups"]),
         "symbolic SaveRec pointer-fixup rows differ from root literal")
    probe = contract["probe_source"]
    need(isinstance(probe, dict) and probe.get("path") and
         re.fullmatch(r"[0-9a-f]{64}", probe.get("sha256", "")) and
         isinstance(probe.get("size"), int) and probe["size"] > 0,
         "probe source path/hash/size pin missing")
    return len(rows)



STRING_ORDER = '046C 034C 106E 1078 1086 1096 10A8 10B4 020A 0218 021C 0234 023A'.split()
YARD_LONGS = '0220 107E 109C'.split()
YARD_INTS = '0202 022C 023E 0244 0246 0364 036E 046A 0470 047A 04BE 04C6 04E4 0506 0624 07C2 105C 1066 108C 10A0 10B0 10BC'.split()
ARRAYS = [('0334',12),('38CA',15),('38E8',17),('390A',17)]
CASES = {
 'source-owned:remaining-preparestrings-string-pointers': {
  'typed_far_pointer_halves_zero_and_write':'PASS','independent_BYTE_pointer_storage_roundtrip':'PASS',
  'initialized_nonzero_owner_typed_zero_contrast':'FAIL','initialized_nonzero_owner_BYTE_zero_contrast':'FAIL',
  'wrong_near_outer_pointer_view':'FAIL','wrong_near_row_pointer_view':'FAIL','wrong_pointer_depth_view':'FAIL',
  'wrong_eight_byte_array_extent_view':'FAIL','wrong_plus2_shifted_base_alias':'FAIL'},
 'source-owned:yard-init-state': {'typed_raw_startup0':'PASS','unsigned_signedness_contrast':'FAIL',
  'shifted_SaveRec_base':'FAIL','initialized_owner_startup_contrast':'FAIL'},
 'source-owned:yard-animation-arrays': {'positive_zero_all_elements_raw_grass_SaveRec_reset':'PASS',
  'negative_shifted_grass_base':'FAIL','negative_shifted_rain_base':'FAIL','negative_unsigned_handle_view':'FAIL',
  'negative_initialized_grass_owner':'FAIL'}}

def symbol(suffix):return '_fd_50F6_'+suffix
def communal(name,count,element=1):
    return dict(name=name,kind='far',count=count,element_size=element,length=count*element)
def data_rule(basename,rows,*,publics=None,data=None,fixups=None):
    lengths={basename+'_TEXT':0,'_DATA':0,'CONST':0,'_BSS':0}
    data=data or {}; lengths.update({k:len(v)//2 for k,v in data.items()})
    return {'module_name':basename+'.C','owner_names':[r['name'] for r in rows]+[r['name'] for r in publics or []],
            'owner_communals':rows,'owner_publics':publics or [],'segment_lengths':lengths,
            'initialized_data_hex':data,'linker_fixups':fixups or [],'data_only':True}

def policy(module,provider_communals):
    names=sorted(r['name'] for r in provider_communals)
    result={'module':module,'communals':provider_communals,'required_cases':CASES[module],
            'linkers':['rtlink400','rtlink610'],'owners':names,'aliases':{},
            'compiler_controls':{},'save_rec_pointer_fixups':[]}
    rules=result['compiler_controls']
    if module=='source-owned:remaining-preparestrings-string-pointers':
        order=[symbol(s) for s in STRING_ORDER]
        rules['owner']=data_rule('LANGPTR',[communal(n,4) for n in order])
        rules['wide']=data_rule('LANGWIDE',[communal(n,2,4) for n in order])
        backings=['_test_backing'+n for n in order]
        rules['backings']=data_rule('LANGSHFT',[communal(n,2,4) for n in backings])
        segment='LANGINIT5_DATA'
        fixups=[{'segment':segment,'offset':offset,'width':4,'loc':'pointer32','target_kind':'segment',
            'target':segment,'displacement':0,'encoded_addend':'00000000','frame_kind':'target',
            'frame':segment,'self_relative':False} for offset in range(100,51,-4)]
        rules['initialized']=data_rule('LANGINIT',[],
            publics=[{'name':n,'segment':segment,'offset':52+4*i} for i,n in enumerate(order)],
            data={segment:'00'*104},fixups=fixups)
        result['aliases']['wrong_plus2_shifted_base_alias']=[
            {'alias':n.lower(),'target':('_test_backing'+n).lower(),'delta':2} for n in names]
    elif module=='source-owned:yard-init-state':
        rows=[communal(symbol(s),4) for s in YARD_LONGS]+[communal(symbol(s),2) for s in YARD_INTS]
        rules['positive_provider']=data_rule('OWNV22',rows)
        rules['unsigned_same_width']=data_rule('SIGOWN',rows)
        rules['wrong_width']=data_rule('WIDBAD',[dict(r,count=2,length=2) if r['name']==symbol('0220') else r for r in rows])
        rules['initialized_nonzero']=data_rule('INITBAD',[r for r in rows if r['name']!=symbol('109C')],
            publics=[{'name':symbol('109C'),'segment':'INITBAD5_DATA','offset':0}],
            data={'INITBAD5_DATA':'01000000'})
        order=YARD_LONGS+[s for s in YARD_INTS if s not in ('0364','036E')]
        result['save_rec_pointer_fixups']=[{'probe':'CRTPOS','offset':4+8*i,'width':4,'loc':'pointer32',
            'target':symbol(s),'displacement':0,'encoded_addend':'00000000'} for i,s in enumerate(order)]
        result['save_rec_pointer_fixups'].append({'probe':'CRTSHFT','offset':4,'width':4,'loc':'pointer32',
            'target':symbol('0220'),'displacement':0,'encoded_addend':'01000000'})
    else:
        rules['owner']=data_rule('YDOWNER',[communal(symbol(s),n,2) for s,n in ARRAYS])
        controls={'short_extent':('0334',11,2),'byte_width':('0334',24,1),'wide_width':('0334',12,4),
            'rain_short_extent':('38CA',14,2),'swarm_short_extent':('38E8',16,2),'fly_short_extent':('390A',16,2),
            'rain_byte_width':('38CA',30,1),'swarm_byte_width':('38E8',68,1),'fly_byte_width':('390A',68,1)}
        for key,(suffix,count,element) in controls.items():
            rules[key]={'module_name':'UNIT.C','owner_names':[symbol(s) for s,_ in ARRAYS],
                'owner_communals':[communal(symbol(suffix),count,element)],'owner_publics':[],
                'segment_lengths':{},'initialized_data_hex':{},'linker_fixups':[]}
        for key,suffix,size in [('initialized','0334',24),('initialized_rain','38CA',30)]:
            segment='UNIT7_DATA'
            rules[key]={'module_name':'UNIT.C','owner_names':[symbol(s) for s,_ in ARRAYS],
                'owner_communals':[],'owner_publics':[{'name':symbol(suffix),'segment':segment,'offset':0}],
                'segment_lengths':{segment:size},'initialized_data_hex':{segment:'01'+'00'*(size-1)},'linker_fixups':[]}
        for case in CASES[module]:
            result['aliases'][case]=[{'alias':'_yard_probe_base_'+s.lower(),'target':symbol(s).lower(),
                'delta':2 if case=={'0334':'negative_shifted_grass_base','38CA':'negative_shifted_rain_base'}.get(s) else 0}
                for s,_ in ARRAYS]
        result['save_rec_pointer_fixups']=[{'segment':'UNIT7_DATA','offset':644,'width':4,'loc':'pointer32',
            'target':symbol('0334'),'displacement':0,'encoded_addend':'00000000'}]
    for case in CASES[module]:result["aliases"].setdefault(case,[])
    return result
