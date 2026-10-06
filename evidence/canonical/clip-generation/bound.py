"""Recompute the shipped-resource/window geometry clip bound in memory."""
from pathlib import Path
import sys, struct, json, hashlib, itertools
sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT/'tools'))
import resource_domains
decoder = resource_domains.decoder()
PERSISTENT = {0,1,5,18,19,21,25}
SUPPORTED = set(range(27)) | set(range(29,34))
TRANSIENT = SUPPORTED-PERSISTENT
PAIRS = [{9,i} for i in range(12,18)] + [{26,30}]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def slab_bound(n): return 2*n*n+n+1
def subtract(r,c):
    """The positive-rectangle top/bottom/left/right split in f_1D8E_003F."""
    l,t,rr,b=r; cl,ct,cr,cb=c
    if l>=cr or rr<=cl or t>=cb or b<=ct: return [r]
    out=[]
    if t<ct: out.append((l,t,rr,ct)); t=ct
    if b>cb: out.append((l,cb,rr,b)); b=cb
    if l<cl: out.append((l,t,cl,b)); l=cl
    if rr>cr: out.append((cr,t,rr,b))
    return out
def cells(base,cutters):
    l,t,r,b=base
    xs=sorted({l,r}|{x for c in cutters for x in (c[0],c[2]) if l<x<r})
    ys=sorted({t,b}|{y for c in cutters for y in (c[1],c[3]) if t<y<b})
    covered=sum(any(c[0]<=x and x2<=c[2] and c[1]<=y and y2<=c[3] for c in cutters)
                for x,x2 in zip(xs,xs[1:]) for y,y2 in zip(ys,ys[1:]))
    return {'x_coordinates':len(xs),'y_coordinates':len(ys),
            'total_cells':(len(xs)-1)*(len(ys)-1),
            'uncovered_cells':(len(xs)-1)*(len(ys)-1)-covered}

def compute():
    resources=[]; assets={}
    for stem in ('HCEGANT','SHARED'):
        for ext in ('NDX','DAT'):
            p=ROOT/'assets'/f'{stem}.{ext}'; assets[p.name]=sha(p)
        for row in decoder.parse_records(stem)[1]:
            resources.append({'database':stem,**row})
    windows={}; profiles={}; images=[]; strings=[]
    for row in resources:
        p=row['payload']
        if row['kind']==2:
            packed=struct.unpack_from('<h',p)[0]==-1
            h=decoder.lzss(p[4:],12) if packed else p[:12]
            typ,_,_,_,w,height=struct.unpack('<6h',h)
            if typ not in (0,3) or min(w,height)<=0: raise ValueError('invalid image geometry')
            images.append({'database':row['database'],'id':row['id'],'type':typ,'width':w,'height':height,'inner_packed':packed})
        if row['kind']==4:
            count=p[1]; at=2; lengths=[]
            for _ in range(count):
                n=p[at]; at+=1
                if at+n>len(p): raise ValueError('truncated Pascal string list')
                lengths.append(n); at+=n
            if at!=len(p): raise ValueError('Pascal string list tail')
            strings.append({'database':row['database'],'id':row['id'],'count':count,'maximum_string_bytes':max(lengths,default=0)})
        if row['database']!='HCEGANT': continue
        if row['kind']==9:
            profiles[row['id']]=list(struct.unpack_from('<4h',p))
        if row['kind']!=0 or not 0<=row['id']<34: continue
        n=struct.unpack_from('<h',p,12)[0]; at=44+4*n; objects=[]
        for i in range(n):
            size=struct.unpack_from('<h',p,at+34)[0]
            objects.append({'rect':list(struct.unpack_from('<4h',p,at)),
                'origin':list(struct.unpack_from('<4h',p,at+8)),
                'refs':list(struct.unpack_from('<4h',p,at+16)),
                'modes':list(struct.unpack_from('<4h',p,at+24)),
                'type':p[at+33], 'flags':struct.unpack_from('<H',p,at+36)[0]})
            at+=size
        if at!=len(p): raise ValueError('window object tail')
        windows[row['id']]={'id':row['id'],'flags':struct.unpack_from('<H',p,28)[0],
            'minimum':list(struct.unpack_from('<2h',p,24)),
            'grid':list(struct.unpack_from('<2h',p,32)), 'objects':objects}
    if set(windows)!=set(range(34)): raise ValueError('shipped window ID census changed')
    root=windows[0]
    if root['grid']!=[16,16] or root['minimum']!=[252,280]: raise ValueError('root constraint premise changed')
    if [i for i,r in windows.items() if r['flags']&8]!=[0]: raise ValueError('resize domain changed')
    root_o=root['objects'][0]
    if root_o['modes']!=[0,0,1,2] or any(v%16==0 for v in root_o['origin'][2:]): raise ValueError('root nonzero residue changed')
    if any(r['kind']==9 and r['id']==8 for r in resources): raise ValueError('default VGA geometry override appeared')
    ordinary=SUPPORTED-{0,22,23,26,30}
    for i in ordinary:
        o=windows[i]['objects'][0]
        if o['modes'][2:]!=[1,2] or o['refs'][2:]!=[i<<8,i<<8] or min(o['origin'][2:])<=0:
            raise ValueError(('fixed-extent nonempty premise changed',i))
    special={22:([0,0,1,4],[154,62,245,6]),
             23:([3,4,3,2],[-185,-144,-2,-1]),
             26:([1,2,3,4],[-2,-2,2,2]),
             30:([5,5,5,5],[-5,-4,4,4])}
    for i,(modes,origin) in special.items():
        o=windows[i]['objects'][0]
        if o['modes']!=modes or o['origin']!=origin: raise ValueError(('special geometry premise changed',i))
    if windows[26]['objects'][1]['type']!=6 or not windows[26]['objects'][1]['flags']&0x40:
        raise ValueError('bitmap-frame auto-size premise changed')
    fonts=[]
    for name in ('FONT1','FONT2','FONT3','FONT4'):
        p=ROOT/'assets'/name; raw=p.read_bytes(); hdr=struct.unpack_from('>13h',raw)
        fonts.append({'name':name,'sha256':sha(p),'height':hdr[7], 'line_height':hdr[7]-1})
    max_lines=max([6]+[r['count'] for r in strings])
    max_h=max(r['height'] for r in images); max_line=max(r['line_height'] for r in fonts)
    # Header mode 0,0,1,2 with self refs is an absolute-position fixed extent.
    # The remaining modes are variable, even when their serialized rect looks fixed.
    fixed={}
    for i in TRANSIENT:
        o=windows[i]['objects'][0]
        if o['modes']==[0,0,1,2] and o['refs'][2:]==[i<<8,i<<8]:
            l,t,w,h=o['origin']; fixed[i]=(l,t,l+w,t+h)
    patterns=[set()]+[{i} for i in sorted(TRANSIENT)]+PAIRS
    states=[]
    for modal in patterns:
        ids=PERSISTENT|modal; variable=ids-set(fixed)
        xs={0,640}; ys={0,480}
        for i in modal & set(fixed):
            l,t,r,b=fixed[i]; xs|={x for x in (l,r) if 0<x<640}; ys|={y for y in (t,b) if 0<y<480}
        xcount=len(xs)+2*len(variable); ycount=len(ys)+2*len(variable)
        n=len(ids)
        states.append({'transient_ids':sorted(modal),'persistent_ids':sorted(PERSISTENT),
            'window_count':n,'variable_ids':sorted(variable),'fixed_ids':sorted(ids-variable),
            'crude_cells':(xcount-1)*(ycount-1),'slab_bound':slab_bound(n)})
    max_n=max(r['window_count'] for r in states)
    # Permanent source footprint is untouched; explicit mathematical controls.
    base=(0,0,4,4); coords=range(-1,6)
    rects=[(l,t,r,b) for l,r in itertools.combinations(coords,2) for t,b in itertools.combinations(coords,2)]
    maxima=[0,0]
    for a in rects:
        first=subtract(base,a); maxima[0]=max(maxima[0],len(first))
        for b in rects:
            second=[q for r in first for q in subtract(r,b)]
            if len(second)>slab_bound(2): raise AssertionError('two-cutter bound')
            if len(second)>cells(base,[a,b])['uncovered_cells']: raise AssertionError('cell injection')
            maxima[1]=max(maxima[1],len(second))
    # Exact source outside writes for a zero-height cutter: two empty slabs occur.
    negative={'source':[0,0,8,8],'cutter':[2,4,6,4],
        'original_branch_order_out':[[0,0,8,4],[0,4,8,8],[0,4,2,4],[6,4,8,4]],
        'scope':'Mathematical source trace; zero-height input is outside the nonempty theorem.'}
    # Yard: 8 singleton entries, 14 fixed-priority rain drops, and up to 16
    # entries from each of the two independently counted swarm families.
    # Only swarm/singleton priority reinsertions can leave retirees: 32+8.
    animation_live=8+14+32
    animation_entries=animation_live+32+8
    # Normal input is within screen; x edges are 8-aligned. Non-grid window
    # boundaries are conservatively all 2N coordinates, including the yard.
    xcoords=640//8+1+2*max_n
    ycoords=min(481,2+2*max_n+2*animation_entries)
    animation={'shown_role_bound':animation_live,'entry_bound_at_render':animation_entries,
        'normal_setwin_incoming_bound':slab_bound(max_n-1),
        'normal_screen_cell_bound':(xcoords-1)*(ycoords-1),
        'normal_screen_x_coordinates_bound':xcoords,'normal_screen_y_coordinates_bound':ycoords,
        'empty_C098_fallback_cell_bound':((516+7)//8+1)*(min(325,2+2*animation_entries)-1),
        'first_fatal_emission_bound_from_checked_owner':4*255,
        'rain_image':[r for r in images if r['database']=='HCEGANT' and r['id']==7005],
        'swarm_images':[r for r in images if r['database']=='HCEGANT' and r['id'] in (7006,7007)],
        'arbitrary_position_edge_cell_bound':(2+2*max_n+2*animation_entries-1)**2,
        'scope':'Coordinate bounds require disjoint nonempty incoming tiles and nonempty source sprite rectangles; hook/redraw contexts need the same proof. The 1020 bound permits overflow and uses only the checked pre-first-Punt owner prefix.'}
    report={'schema':'clip-geometry-bound-v1','premises':['successful pinned VGA8 resource acquisition','reviewed nominal supported window/event/save domain','lifetime catalog is a conservative super-set','nonempty normalized window rectangles','no returning-Punt arbitrary-state continuation'],
        'assets':assets,'fonts':fonts,'profiles':profiles,'persistent_ids':sorted(PERSISTENT),
        'transient_ids':sorted(TRANSIENT),'transient_pairs':[sorted(x) for x in PAIRS],
        'states':states,'maximum_stack_ceiling':max_n,
        'maximum_crude_cell_bound':max(r['crude_cells'] for r in states),
        'C097_bound':slab_bound(max_n-1),'C098_bound':max(1,slab_bound(max_n-1)),
        'C099_bound':slab_bound(max_n),'sentinel_inclusive_maximum':slab_bound(max_n)+1,
        'picture_dialog_height_bound':max_h+2+max_lines*max_line+8+8,
        'maximum_pascal_list_count':max_lines,'image_count':len(images),'image_height_range':[min(r['height'] for r in images),max_h],
        'nonempty_resource_guards_passed':True,'root_extent_residues_mod16':[v%16 for v in root_o['origin'][2:]],
        'window_object0_geometry':[{k:v for k,v in windows[i].items() if k!='objects'}|{'object0':windows[i]['objects'][0], 'title_type':windows[i]['objects'][1]['type']} for i in sorted(SUPPORTED)],
        'title_type_drag_ids':[i for i in sorted(SUPPORTED) if windows[i]['objects'][1]['type'] in (12,18)],
        'animation':animation,'controls':{'two_cutters_ordered_cases':len(rects)**2,'maximum_counts':maxima,'degenerate_negative':negative}}
    report['source_pins']={p:sha(ROOT/p) for p in ['src/root/m1D8E.c','src/root/m1E57.c','src/root/m20E8.c','src/root/m218D.c','src/root/m22BF.c','src/root/m2505.c','src/root/m2662.c','src/S05/m3663.c','src/S14/m384C.c','src/S26/m39C7.c']}
    return report

def main():
    report = compute()
    print(json.dumps({k:report[k] for k in ['maximum_stack_ceiling','maximum_crude_cell_bound','C097_bound','C098_bound','C099_bound','sentinel_inclusive_maximum','picture_dialog_height_bound','title_type_drag_ids','animation','controls']},indent=2))
if __name__=='__main__': main()
