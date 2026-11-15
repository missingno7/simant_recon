import sys
sys.dont_write_bytecode=True
from capture_current import ROOT,OUT,run
import concurrent.futures,json
def click(w,x,y,t=16000,release=True):
    return f'{t} move@{w} {x} {y}\n{t+100} mouse-down@{w} Left {x} {y}\n'+(f'{t+200} mouse-up@{w} Left {x} {y}\n' if release else '')
fixture=(ROOT/'portable/tests/runtime/windows-quick.txt').read_text()
experiment=fixture.replace('207 58','44 202')
cases={}
for name,y in [('barriers',28),('dig-fill',45),('add-ants',62),('food',79),('trails',96),('insecticide',113)]:
    cases[name]=(experiment+click('0000',35,29,release=False)+f'16800 move@0900 40 {y}\n',18000)
cases['full-tools']=(fixture.replace('207 58','207 126')+click('0000',35,29,release=False),18000)
cases['about']=(fixture+'16000 menu FD01\n',18000)
cases['population']=(fixture+click('0100',410,294,release=False),18000)
cases['info-help']=(fixture+'16000 menu FD16\n'+click('0500',50,23,18000),19500)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:
    result=list(p.map(lambda a:run(a[0],*a[1]),cases.items()))
(OUT/'tools-capture-report.json').write_text(json.dumps(dict(zip(cases,result)),indent=2))
