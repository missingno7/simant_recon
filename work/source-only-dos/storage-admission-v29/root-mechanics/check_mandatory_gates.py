import ast,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import compiler,dos_source_bindings as b,dos_alignment_debt as alignment
r=json.loads((ROOT/'build/source-only-dos/build-report.json').read_bytes())
tree=ast.parse((ROOT/'tools/source_only_dos.py').read_text())
link=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='link_units')
names=sorted({n.func.attr for n in ast.walk(link) if isinstance(n,ast.Call)
    and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
    and n.func.value.id=='dos_source_bindings' and n.func.attr.startswith('require_')})
assert len(names)==29
tools=compiler.toolchain()['linkers']
for profile in ('rtlink400','rtlink610'):
    for name in names:getattr(b,name)(r,profile,tools[profile])
    components=[(str(Path(tools[profile]['directory'])/name),digest) for name,digest in tools[profile]['files'].items()]
    components += [(row['path'],row['sha256']) for row in r['runtime_components']]
    alignment.require_contract(r['far_data_alignment_contract'],profile,components)
    print(profile,'PASS',len(names),'mandatory gates plus alignment')
assert len(r['translation_units'])==188 and len(r['unresolved_symbols'])==15
assert sum(row['size'] for row in r['unresolved_data'])==46
assert sum(row['status']=='UNRESOLVED' for row in r['layout_dependencies'])==7
assert r['function_dispositions']['BEHAVIOR_EXACT_CONFIRMED']==29
assert not any(r['original_exe_bytes_used'].values()) and r['denied_oracle_reads']==[]
assert r['standalone_dos_executable'] is False
print('PASS: 188 compiled TUs, 15 unresolved imports, 46 functional data bytes, seven open layout gates, all original-byte counters zero')
