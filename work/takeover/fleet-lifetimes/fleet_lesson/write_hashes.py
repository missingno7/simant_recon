from pathlib import Path
import hashlib,json
root=Path(__file__).parent
lines=[]
for name in ['base.c','generate_round2.py','generate_round3.py','generate_round4.py','generate_round5.py','generate_round6.py','listing.py','inspect_variants.py','region_compare.py','compare_dispatch.py','compare_best.py','compare_order.py','compare_controls.py','compare_archived.py','write_hashes.py']:
 p=root/name
 if p.exists(): lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}')
for d in ['round2-sources','round3-sources','round4-sources','round5-sources','round6-sources']:
 for p in sorted((root/d).glob('*.c')):
  lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}')
for n in ['case9_split_only.c','case7_nested_only.c','case7_9_nested_short_circuit.c','case7_9_time_result_lifetime.c','case0_based_expression.c','reordered_target_block_order.c','reordered_target_groups.c']:
 p=root/n
 if p.exists() and not any(x.endswith('  '+p.relative_to(root).as_posix()) for x in lines):
  lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}')
for d in ['round2-results','round3-results','round4-results','round5-results','round6-results']:
 p=root/d/'results.json'
 if p.exists():lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}')
for n in ['listing.txt','strict-search.txt','strict-verify-only.txt','REPORT.md']:
 p=root/n
 if p.exists():lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}')
(root/'source-hashes.txt').write_text('\n'.join(lines)+'\n',encoding='ascii')
rows=[]
for d in ['round2-results','round3-results','round4-results','round5-results','round6-results']:
 p=root/d/'results.json'
 if not p.exists():continue
 for v in json.loads(p.read_text())['variants']:
  res=v['result']; c=res['claims'].get('LessonDone',{})
  peers=all(res['claims'].get(n,{}).get('exact') for n in ['Feedback','RunTutor','GiveLesson'])
  data=all(x.get('exact') for x in res.get('data',{}).values())
  why='; '.join(c.get('reasons',[]))
  rows.append((d,v['name'],c.get('exact'),why,peers,data,res.get('object_sha256')))
out=['round\tvariant\tLessonDone_exact\treasons\taccepted_peers_exact\tprivate_data_exact\tobject_sha256']
for row in rows:out.append('\t'.join(str(x) for x in row))
(root/'variant-summary.tsv').write_text('\n'.join(out)+'\n',encoding='utf-8')
