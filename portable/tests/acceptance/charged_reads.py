"""Compare complete admitted reads with independently named DOS/native call sites.

Raw PCs/stacks stay in the traces. Canonical function extents qualify the DOS
return PC (or direct BDA instruction); native PE symbols qualify its stack PC.
Every qualified DOS/native call-site pairing must be a bijection for the run.
"""
import argparse,bisect,json,re,subprocess
from pathlib import Path
from .capture_dos_steps import capture_addresses
from .state_schema import ROOT,sha

def compare(reference,native_trace,native_exe,out):
 manifest=json.loads((reference/'manifest.json').read_text())
 boundary=json.loads((reference/'capture/boundary-manifest.json').read_text());base=boundary['runtime_base']
 original=manifest['target']=='original';exe=ROOT/'assets/SIMANT.EXE'
 if not original:
  execution=json.loads((reference/'capture/execution-report.json').read_text())
  pin=next(p for p in execution['inputs'] if p['path'].endswith('build-report.json'))
  exe=ROOT/json.loads((ROOT/pin['path']).read_text())['link']['candidate_executable']['path']
 addresses=capture_addresses(original,exe)
 if not original:
  # The acceptance anchor reader intentionally selects resident cdecl leaves.
  # Callers also include Pascal (@) functions and relocated overlay bodies.
  for line in exe.with_name('SOURCE.MAP').read_text(encoding='latin1').splitlines():
   match=re.match(r'\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(?:Res|Ovl)\s+[_@](\w+)(?=\s|$)',line)
   if match:addresses.setdefault(match[3],int(match[1],16)*16+int(match[2],16))
 claims=[c for m in json.loads((ROOT/'layout/manifest.json').read_text())['modules'].values() for c in m['claims']]
 extents={}
 for c in claims:
  start=base+(c['seg']*16+c['off'] if original else addresses.get(c['name'],-base-c['size']-1))
  extents.setdefault(c['name'],[]).append((start,start+c['size']))
 nm=subprocess.check_output(['C:/msys64/mingw64/bin/nm.exe','-n',str(native_exe)],text=True)
 symbols=sorted((int(a,16),n) for a,n in re.findall(r'^([0-9a-fA-F]+) [Tt] (\S+)$',nm,re.M));ats=[s[0] for s in symbols]
 import pefile
 preferred=pefile.PE(str(native_exe),fast_load=True).OPTIONAL_HEADER.ImageBase
 with native_trace.open() as f:
  image=f.readline().split();runtime=int(image[1],16)
  native=(line.split() for line in f if line.startswith('R '))
  direct={r['pc'] for r in boundary.get('modifier_byte_reads',[])}
  pairs={};reverse={};first=None;count=0;unbound=[];candidate_cache={}
  dos_path=reference/'capture/observer.txt.ideal'
  with dos_path.open() as d:
   dos=(line.split() for line in d if line.startswith('R '))
   from itertools import zip_longest
   for i,(a,b) in enumerate(zip_longest(dos,native),1):
    count=i
    if a is None or b is None or a[1:3]!=b[1:3] or a[4]!=b[4]:
     first=dict(read=i,dos=a,native=b);break
    pc=int(a[3],16);caller=pc if pc in direct or a[4]=='portable_m1b73_source_countdown_get' else int(a[5],16)
    if caller not in candidate_cache:
     candidate_cache[caller]={name for name,ranges in extents.items() if any(lo<=caller<hi for lo,hi in ranges)}
    candidates=candidate_cache[caller]
    found=[]
    for raw in b[7:]:
     at=int(raw,16)-runtime+preferred;ix=bisect.bisect_right(ats,at)-1
     # input_time.c implements the original character adapter directly;
     # read_key calls that helper without the public wrapper frame.
     if ix>=0:
      name=symbols[ix][1]
      identity='kbd_read_bios_char' if name=='portable_input_time_read_char' else name
      if identity in candidates:
       found.append((identity,at-symbols[ix][0]));break
    if not found:
     unbound.append(dict(read=i,dos_pc=a[3],dos_caller=hex(caller),service=a[4],candidates=sorted(candidates),native_stack=b[7:]));continue
    native_site=(a[4],*found[0]);dos_site=(a[4],hex(caller))
    if (dos_site in pairs and pairs[dos_site]['native']!=native_site) or (native_site in reverse and reverse[native_site]!=dos_site):
     first=dict(read=i,kind='CALL_SITE_PAIRING',dos=dos_site,native=native_site);break
    pairs.setdefault(dos_site,dict(native=native_site,first_read=i,reads=0));pairs[dos_site]['reads']+=1;reverse[native_site]=dos_site
 result=dict(status='READS_EQUAL' if first is None and not unbound else 'READS_DIFFERENT' if first else 'CALL_SITES_UNBOUND',
  reads=count,first_difference=first,unbound=unbound[:30],unbound_count=len(unbound),sites=[dict(dos=k,**v) for k,v in pairs.items()],
  dos_trace_sha256=sha(dos_path),native_trace_sha256=sha(native_trace),native_executable_sha256=sha(native_exe),reference_manifest_sha256=sha(reference/'manifest.json'))
 out.write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['reference','native_trace','native_exe','out']:p.add_argument(n,type=Path)
 a=p.parse_args();r=compare(a.reference,a.native_trace,a.native_exe,a.out);print(r['status'],r['reads'],r['first_difference'],'unbound',r['unbound_count'])
