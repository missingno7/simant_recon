"""Original-read seed tapes; no values are calculated from candidate state."""
import json,re,subprocess
if __package__:
    from .native_acceptance import ROOT,sha
else:
    from native_acceptance import ROOT,sha


def native_seed_sites(exe,objdump='C:/msys64/mingw64/bin/objdump.exe'):
    texts={name:subprocess.check_output([objdump,'-d','--disassemble='+name,str(exe)],text=True)
           for name in ('SeedSRand','SeedRRand')}
    anchor=int(re.search(r'([0-9a-f]+) <SeedSRand>:',texts['SeedSRand'])[1],16)
    sites={}
    for name,text in texts.items():
        calls=re.findall(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*call\s+[^\n]*<TickCount>',text,re.M)
        if len(calls)!=1: raise ValueError('Native clock call binding is not unique: '+name)
        address,raw=calls[0]
        sites[name]=int(address,16)+len(raw.split())-anchor
    return sites,texts


def seed_tape(directory,exe,out,scenario_sha,script_sha):
    manifest=json.loads((directory/'boundary-manifest.json').read_text())
    expected=json.loads((ROOT/'layout/oracle.lock.json').read_text())['inputs']['SIMANT.EXE']['sha256']
    if manifest.get('target')!='original' or manifest['executable_sha256']!=expected or \
            manifest['scenario_sha256']!=scenario_sha or manifest['input_script_sha256']!=script_sha:
        raise ValueError('Seed replay requires matching original executable/scenario/input identities')
    sites,disassembly=native_seed_sites(exe)
    records=[]
    expected_names={f'exec-seed-{name}.{i}.json' for name,n in [('SeedSRand',2),('SeedRRand',1)] for i in range(1,n+1)}
    if {p.name for p in directory.glob('exec-seed-*.json')}!=expected_names:
        raise ValueError('Missing or extra seed read ordinals')
    for name,hits in [('SeedSRand',2),('SeedRRand',1)]:
        for ordinal in range(1,hits+1):
            path=directory/f'exec-seed-{name}.{ordinal}.json';dump=path.with_suffix('.bin')
            if manifest['metadata'].get(path.name)!=sha(path) or manifest['snapshots'].get(dump.name)!=sha(dump):
                raise ValueError('Seed observation identity differs: '+str(path))
            meta=json.loads(path.read_text());r=meta['registers']
            if meta['hit']!=ordinal or int(r['cs'],16)*16+int(r['eip'],16)!=manifest['seed_return_sites'][name]:
                raise ValueError('Seed read site/ordinal differs')
            records.append(dict(site=name,ordinal=ordinal,value=(int(r['eax'],16)&65535)|((int(r['edx'],16)&65535)<<16),
                                emulated_ms=meta['emulated_ms'],metadata_sha256=sha(path),dump_sha256=sha(dump)))
    records.sort(key=lambda r:r['emulated_ms'])
    path=out/'clock-inputs.txt'
    path.write_text('# Original DX:AX; site, native PC delta, per-site read ordinal, value\n'+''.join(
        f'{"S" if r["site"]=="SeedSRand" else "R"} {sites[r["site"]]} {r["ordinal"]} {r["value"]}\n' for r in records))
    receipt=dict(schema='simant-original-seed-inputs-v1',original_manifest_sha256=sha(directory/'boundary-manifest.json'),
        original_executable_sha256=expected,native_executable_sha256=sha(exe),tape_sha256=sha(path),
        scenario_sha256=scenario_sha,input_script_sha256=script_sha,records=records,
        native_return_pc_deltas=sites,native_disassembly=disassembly,
        original_capture_directory=str(directory.resolve()),
        scope='Seed calls only; original per-call-site ordinals, not global TickCount polling ordinals. Other clocks remain unreplayed.')
    (out/'clock-inputs.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return path,receipt
