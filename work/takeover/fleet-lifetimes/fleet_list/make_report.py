from pathlib import Path
import json,hashlib
root=Path('.')
out=Path('build/workers/fleet_list')
base_path=Path('work/takeover/menu-loader/list-base.c')
def sha(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
series=[]
for folder in ['register-pointer','huge-pointer','far-assignment']:
    obj=json.loads((out/folder/'results.json').read_text())
    rows=[]
    for v in obj['variants']:
        rp=v['result']; claim=rp.get('claims',{}).get('f_23E6_0000',{})
        peer_losses=[name for name in v.get('claims',[]) if name!='f_23E6_0000' and not rp.get('claims',{}).get(name,{}).get('exact')]
        rows.append({'name':v['name'],'source':Path(v['file']).name if v.get('file') else None,'source_sha256_lf':sha(Path(v['file'])) if v.get('file') else None,'compile_ok':rp.get('compile_ok'),'target_exact':claim.get('exact'),'target_reasons':claim.get('reasons',[]),'data_exact':all(d.get('exact') for d in rp.get('data',{}).values()),'peer_losses':peer_losses})
    series.append({'series':folder,'profile':obj['profile'],'flags':obj['flags'],'placements':obj['placements'],'rows':rows})
summary={'task':'root:23E6 f_23E6_0000 bounded far-pointer follow-up','base_source':'work/takeover/menu-loader/list-base.c','base_sha256_lf':sha(base_path),'target_size':159,'base_candidate_size':156,'diagnostic':'One original MOV CX,[BP-0Ah] at +0x73 is absent after pointer offset advancement; the baseline comparison reports first byte difference +0x5D. Target ends 3 bytes later.','profile':'msc600ax','flags':['/AL','/Os','/Oe','/Og','/Gs','/Zi'],'controls':{'novel_hypotheses':20,'compiled_rows_including_each_series_base':23,'series':series},'semantic_evidence':{'existing_xver_pair':False,'correspondence_file':'evidence/cross_version/simantw_correspondence.json','same_module_pointer_walks':['f_23E6_016B','f_23E6_06F1'],'notes':'Existing correspondence has no pair for root:23E6:0000. Same-module accepted helpers support byte-string traversal and offset/segment-separated far-pointer handling; no source-level need for the CX reload is yet established.'},'prior_controls':{'readme':'work/takeover/menu-loader/README.md','value_flow':'work/takeover/menu-loader/list-value-flow.json','assignment_use':'work/takeover/menu-loader/list-assignment-use.json','near_comparison':'work/takeover/menu-loader/list-assignment-near.log','counts':{'value_flow':25,'assignment_use':19,'total':44,'exact_target_rows':0,'accepted_peer_regressions':24}}}
(out/'results-compact.json').write_text(json.dumps(summary,indent=2))
lines=['# f_23E6_0000 far-pointer follow-up','',f'Base whole-module snapshot: `{base_path}` (LF SHA-256 `{summary["base_sha256_lf"]}`). All compiler runs used `{summary["profile"]}` with inherited flags `{", ".join(summary["flags"])}` and manifest placements through `modctx.resolve` and `variants.run(jobs=2)`; each run compiled the 14 accepted peers and checked private data.','',f'The target remains 159 bytes. `list-base.c` remains 156 bytes; its first byte difference is +0x5D. The original instruction at +0x73 is `mov cx, word ptr [bp - 0xa]`, immediately after advancing SI; the baseline does not emit it. No tested source variant is byte-exact.','',f'This worker tested {summary["controls"]["novel_hypotheses"]} new source hypotheses in {summary["controls"]["compiled_rows_including_each_series_base"]} compilation rows (series baselines repeat for independently gated runs).','', '| Series | New variants | Exact target | Peer losses |','|---|---:|---:|---|']
for s in series:
    vals=[r for r in s['rows'] if r['name']!='base']
    exact=sum(bool(r['target_exact']) for r in vals)
    losses=sorted(set(n for r in vals for n in r['peer_losses']))
    lines.append(f'| {s["series"]} | {len(vals)} | {exact} | {", ".join(losses) if losses else "none"} |')
lines += ['', 'The new controls covered C register qualifiers and pointer type qualifiers, an explicit `char huge *` hypothesis, named base-pointer aliasing, and simple/parenthesized explicit far-pointer assignments. Register qualifiers, signedness, constness, and direct assignment forms retained the baseline 156-byte target. A live base alias did not recover the missing segment load and regressed accepted peers; huge pointers pulled `__AHSHIFT` and substantially changed the code.','', 'The previous 44 list series are archived separately and were not repeated. Their `list-value-flow.json`, `list-assignment-use.json`, and `list-assignment-near.log` show no exact target; the README records 24 accepted-peer regressions and the four-byte folded-assignment mismatch.','', 'The existing `evidence/cross_version/simantw_correspondence.json` has no correspondence entry for this function. The DOS window helper siblings `f_23E6_016B` and `f_23E6_06F1` support the list-string and far-pointer semantics but do not explain why MSC would reload the segment into CX here. The CX value has no identified semantic consumer in the decoded target stream.','', 'Conclusion: preserve `f_23E6_0000` as unresolved debt. These natural far-pointer/register/type variants provide no exact source and do not support an assembly classification. No search hit or verify-only promotion candidate exists.','']
(out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
print(out/'REPORT.md')
print(out/'results-compact.json')
