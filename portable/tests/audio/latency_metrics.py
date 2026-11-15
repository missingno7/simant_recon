import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
def quantile(v,q):
    v=sorted(v);return v[min(len(v)-1,int((len(v)-1)*q))] if v else None
def analyze(directory):
    rows=[json.loads(s) for s in (directory/'queue.jsonl').read_text().splitlines()]
    opened=next(x for x in rows if x['tag']=='open');rate=opened['sample_rate'];period=opened['block_frames']/rate
    q=[x for x in rows if x['tag']=='queue'];events={x['id']:x for x in rows if x['tag']=='trigger'};resolved={x['id']:x for x in rows if x['tag'] in ('head','discarded','pending_at_close')};emissions={x['id']:x for x in rows if x['tag']=='sample_emission'}
    phases=[('startup',0,1),('title',1,12),('quick-game',12,25),('modal-ant-menu',25,54),('minimized',55.1,57.9),('restored',58.2,64),('native-move',65.1,65.9),('move-recovery',66.1,68),('steady-after-move',68,74.8),('breakpoint',75.1,75.9),('break-recovery',76.1,78),('steady-after-break',78,94.9)]
    phase_results=[]
    for name,start,end in phases:
        points=[x for x in q if start<=x['wall_ns']/1e9<end]
        if not points:phase_results.append(dict(name=name,points=0));continue
        phase_results.append(dict(name=name,points=len(points),queue_ms=[min(x['frames'] for x in points)/48,statistics.median(x['frames'] for x in points)/48,max(x['frames'] for x in points)/48],queue_and_partial_max_ms=max(x['frames']+x['pending'] for x in points)/48,source_span_s=(points[-1]['game_ns']-points[0]['game_ns'])/1e9,wall_span_s=(points[-1]['wall_ns']-points[0]['wall_ns'])/1e9))
    latency={}
    for kind,label in ((1,'music_key_on'),(2,'sample_setup_to_first_emission_head')):
        for suffix,predicate in [('',lambda t:True),('_steady',lambda t:1<t['wall_ns']/1e9<64 or 68<t['wall_ns']/1e9<74 or 78<t['wall_ns']/1e9<94)]:
            selected=[(t,resolved.get(i)) for i,t in events.items() if t['kind']==kind and predicate(t)]
            heads=[(t,h) for t,h in selected if h and h['tag']=='head'];upper=[(h['upper_ns']-t['wall_ns'])/1e6 for t,h in heads];lower=[(h['lower_ns']-t['wall_ns'])/1e6 for t,h in heads]
            if kind==2 and heads:assert all(t['id'] in emissions for t,h in heads),'Sample head lacks actual source emission'
            latency[label+suffix]=dict(triggers=len(selected),arrived=len(heads),discarded=sum(bool(h and h['tag']=='discarded') for t,h in selected),pending=sum(bool(not h or h['tag']=='pending_at_close') for t,h in selected),lower_ms=dict(min=min(lower) if lower else None,median=statistics.median(lower) if lower else None,max=max(lower) if lower else None),upper_ms=dict(min=min(upper) if upper else None,median=statistics.median(upper) if upper else None,p95=quantile(upper,.95),max=max(upper) if upper else None),bracket_max_ms=max((h['upper_ns']-h['lower_ns'])/1e6 for t,h in heads) if heads else None)
    resets=[x for x in rows if x['tag']=='replace'];starvation=[];previous=0;previous_wall=q[0]['wall_ns']
    for x in q:
        if x['underruns']>previous:starvation.append(dict(after_seconds=previous_wall/1e9,before_seconds=x['wall_ns']/1e9,additional=x['underruns']-previous))
        previous=x['underruns']
        previous_wall=x['wall_ns']
    return dict(path=str(directory),period_ms=period*1000,points=len(q),phases=phase_results,latency=latency,resets=resets,ordinary_overflow_resets=[x for x in resets if x['reason']==3 and not(x['wall_ns']<1e9 or 66e9<x['wall_ns']<68e9 or 76e9<x['wall_ns']<78e9)],starvation=starvation,pacing=json.loads((directory/'pacing.json').read_text()),session=json.loads((directory/'session.json').read_text()))
r={name:analyze(path) for name,path in [('before',a.before),('after',a.after)]};a.out.write_text(json.dumps(r,indent=2)+'\n')
for side,v in r.items():
 print(side,'latency',json.dumps(v['latency']), 'resets',len(v['resets']),'ordinary_overflows',len(v['ordinary_overflow_resets']),'starvation',sum(x['additional'] for x in v['starvation']))
