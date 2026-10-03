"""Preserve a native receipt and its exact readable inputs before further work.

Original assets and compiled tools/products are identity-only. A stale readable
input may be recovered from an explicitly supplied Git ref only if its digest
matches the receipt. This never edits production inputs or historical evidence.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[2]
def digest(data): return hashlib.sha256(data).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--ref',action='append',default=[])
    ap.add_argument('--snapshot-root',action='append',default=[],
        help='Exact readable build snapshot; recovered bytes must match the receipt hash')
    ap.add_argument('--unavailable-diagnostic',action='append',default=[],
        help='Explicitly retain a missing diagnostic JSON hash; C/header/script inputs cannot be waived')
    args=ap.parse_args();report=ROOT/args.report;out=(ROOT/args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT/'portable'):
        raise ValueError('new portable archive directory required')
    raw=report.read_bytes();receipt=json.loads(raw)
    pins={}
    for key in ('inputs','input_sha256','inputs_sha256','inputs_before_sha256',
                'inputs_sha256_before','source_hashes_before','source_asset_pins_before','inputs_before'):
        for rel,value in receipt.get(key,{}).items():
            if isinstance(value,str) and len(value)==64: pins[rel.replace('\\','/')]=value
            elif isinstance(value,dict) and 'path' in value and 'sha256' in value:
                pins[value['path'].replace('\\','/')]=value['sha256']
    if not pins:raise ValueError('receipt has no supported input hash inventory')
    entries=[];contents={}
    for rel,expected in pins.items():
        path=(ROOT/rel).resolve()
        row={'source':rel,'sha256':expected}
        if not path.is_relative_to(ROOT) or path.suffix.lower() in {'.exe','.dll','.o','.a','.bin','.obj','.lib','.bmp','.dat'} or rel.startswith('assets/'):
            row['retention']='IDENTITY_ONLY_BINARY_OR_EXTERNAL';entries.append(row);continue
        data=path.read_bytes() if path.is_file() else b'';origin='workspace'
        if digest(data)!=expected:
            for snapshot in args.snapshot_root:
                candidate=(ROOT/snapshot/rel).resolve()
                base=(ROOT/snapshot).resolve()
                if candidate.is_relative_to(base) and candidate.is_file():
                    recovered=candidate.read_bytes()
                    if digest(recovered)==expected:
                        data=recovered;origin=f'snapshot:{snapshot}';break
        if digest(data)!=expected:
            for ref in args.ref:
                proc=subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}',
                    'show',f'{ref}:{rel}'],cwd=ROOT,capture_output=True)
                if proc.returncode==0 and digest(proc.stdout)==expected:
                    data=proc.stdout;origin=f'git:{ref}';break
            else:
                if rel in args.unavailable_diagnostic and path.suffix.lower()=='.json' and rel.startswith('build/'):
                    row['retention']='UNAVAILABLE_DIAGNOSTIC_CONTEXT'
                    entries.append(row);continue
                raise ValueError(f'exact input unavailable: {rel}')
        try:data.decode('utf-8')
        except UnicodeDecodeError:
            row['retention']='IDENTITY_ONLY_BINARY';entries.append(row);continue
        target='inputs/'+rel
        row.update(retention='EXACT_READABLE_INPUT',archive=target,recovered_from=origin)
        contents[target]=data;entries.append(row)
    out.mkdir(parents=True)
    for name,data in contents.items():
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    (out/'report.json').write_bytes(raw)
    (out/'archive.json').write_text(json.dumps({'schema':'simant-native-input-archive-v1',
        'scope':'Native evidence retention; no new DOS claim',
        'receipt_source':report.relative_to(ROOT).as_posix(),'receipt_sha256':digest(raw),
        'inputs':entries},indent=2)+'\n')
    print(json.dumps({'readable_inputs':len(contents),'identity_only':len(entries)-len(contents)}))
if __name__=='__main__':main()
