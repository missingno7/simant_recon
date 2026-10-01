from pathlib import Path
import sys
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import search
out=ROOT/'build'/'workers'/'fleet_index';search.ROOT=out
rows=search.run('FindIndex',[out/'findindex-base.c',out/'novel'/'004_reverse-compound-boundary.c'],None,None,None,{},False)
print('RESULTS',[(r['status'],r['source_sha256'],r.get('reasons')) for r in rows])
