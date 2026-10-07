"""Compare raw DOS-format device traces without removing or masking writes."""
from pathlib import Path
import argparse,json
def reads(path):
 rows=[]
 for line in path.read_text().splitlines():
  p=line.split()
  if len(p)>=5 and p[1]=='out':rows.append((float(p[0]),int(p[2],16),int(p[3]),int(p[4],16)))
 return rows
def compare(a,b,anchor,tolerance):
 def formatted(row):
  return {'virtual_time_ms':row[0],'port':f'{row[1]:04X}','size':row[2],'value':f'{row[3]:02X}'} if row is not None else None
 first=next((i for i,(x,y) in enumerate(zip(a,b)) if x[1:]!=y[1:]),None)
 prefix=min(len(a),len(b)) if first is None else first
 if first is None and len(a)!=len(b):first=prefix
 offset=b[anchor][0]-a[anchor][0] if anchor<prefix else None
 absolute=[abs(x[0]-y[0]) for x,y in zip(a[:prefix],b[:prefix])]
 relative=[abs(y[0]-x[0]-offset) for x,y in zip(a[anchor:prefix],b[anchor:prefix])] if offset is not None else []
 return {'order_values':'EQUAL' if first is None else 'DIFFERS','writes':[len(a),len(b)],
  'first_difference':None if first is None else {'index':first,'oracle':formatted(a[first] if first<len(a) else None),'native':formatted(b[first] if first<len(b) else None)},
  'absolute_max_delta_ms':max(absolute,default=None),'anchor_index':anchor,'anchor_offset_ms':offset,
  'relative_max_delta_ms':max(relative,default=None),'tolerance_ms':tolerance,
  'relative_timing':'WITHIN_TOLERANCE' if relative and max(relative)<=tolerance else 'OUTSIDE_TOLERANCE'}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('oracle',type=Path);ap.add_argument('native',type=Path)
 ap.add_argument('--tolerance-ms',type=float,default=2);ap.add_argument('--opl-anchor-index',type=int,default=24)
 ap.add_argument('--out',type=Path);args=ap.parse_args()
 result={};merged=[[],[]]
 for device,anchor in [('sb_dsp',0),('opl',args.opl_anchor_index)]:
  a=reads(args.oracle/f'io-{device}');b=reads(args.native/f'io-{device}')
  result[device]=compare(a,b,anchor,args.tolerance_ms);merged[0]+=a;merged[1]+=b
 result['merged']=compare(sorted(merged[0]),sorted(merged[1]),0,args.tolerance_ms)
 result['scope']='Raw complete streams; relative timing anchored independently. Absolute startup equality is not implied.'
 report=json.dumps(result,indent=2)+'\n';print(report)
 if args.out:args.out.write_text(report)
 return 0 if all(result[k]['order_values']=='EQUAL' for k in ('sb_dsp','opl','merged')) else 1
if __name__=='__main__':raise SystemExit(main())
