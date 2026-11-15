import sys
sys.dont_write_bytecode=True
from capture_current import *
import concurrent.futures
fixture=(ROOT/'portable/tests/runtime/windows-quick.txt').read_text()
def click(w,x,y,t=16000,release=True):
    return f'{t} move@{w} {x} {y}\n{t+100} mouse-down@{w} Left {x} {y}\n'+(f'{t+200} mouse-up@{w} Left {x} {y}\n' if release else '')
experiment=fixture.replace('207 58','44 202')
cases={
 'minimap':(fixture+click('0000',24,7),18000),
 'help':(fixture+click('0000',13,29,release=False),17400),
 'scent':(fixture+click('0000',24,150,release=False),17400),
 'quick-tools':(fixture+click('0000',35,29,release=False),17400),
 'caste-population':(fixture+click('0100',177,177,release=False),17400),
 'experiment':(experiment,17500),
 'experiment-tools':(experiment+click('0000',35,29,release=False),17400),
 'ant-menu':(fixture+'16000 move@0000 231 150\n16100 mouse-down@0000 Left 231 150\n',16600),
 'zoom':((ROOT/'portable/tests/runtime/modern-zoom.txt').read_text(),18500),
 'load':(fixture+'16000 menu FD04\n',18000),
 'quit-confirm':(fixture+'16000 menu FD08\n',18000),
 'classic':((ROOT/'portable/tests/runtime/full-game-vga.txt').read_text(),17500,False,''),
}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:
    results=list(p.map(lambda a:run(a[0],*a[1]),cases.items()))
(OUT/'extra-capture-report.json').write_text(json.dumps(dict(zip(cases,results)),indent=2))
