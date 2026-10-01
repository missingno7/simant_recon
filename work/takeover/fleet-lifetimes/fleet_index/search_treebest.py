from pathlib import Path
import sys
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import search
out=ROOT/'build'/'workers'/'fleet_index';search.ROOT=out
rows=search.run('FindIndex',[out/'findindex-base.c',ROOT/'work'/'takeover'/'blockers'/'index-trees-v111.c'],None,None,None,{},False)
print('RESULTS',[(r['status'],r.get('reasons')) for r in rows])
