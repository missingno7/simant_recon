"""Root literals derived from reviewed natural declarations and fixture C."""
from dos_storage_contracts import communal, data_rule, symbol

BALLOONS = '050C 059A 0732 07C4'.split()
HISTORY = '0EAC 0EB4 0EF6 0EF8 0EFA 0F06 0F0C 0F0E 0F10 0F12 0F26 0F2E 0F34 0F36 0F3C 0F44 0F7A 0FC0'.split()
WORLD = '0204 0208 0210 0212 0214 0226 0240 0332 037A 0402 0476 047E 0488 048E 0492 049A 04A4'.split()
WORLD_SAVE = '0208 0210 0212 0226 0240 0332 0476 047E 0488 0492 049A 04A4'.split()
ANT_PAIRS = '0A02 0A8A 0AA2 0AB2'.split()
ANT_WORDS = '0A06 0A9C 0AA6 0ACA 0AD8 0AEA 0B06 0B08 0C3A 0D68 0D6C 0D6E 0D70'.split()
CASES = {
 'source-owned:remaining-ant-state': {'positive18':'PASS_18_TYPED_RAW_SIGNED_SAVE_ZERO','wide_control':'WRONG_FOUR_BYTE_SCALAR_OWNER_DETECTED','unsigned_control':'WRONG_UNSIGNED_SCALAR_VIEW_DETECTED','initialized_control':'INITIALIZED_NONZERO_OWNER_DETECTED','shift_plus2_control':'SHIFTED_PLUS_TWO_SAVE_BASE_DETECTED'},
 'source-owned:balloon-deadline-timers': {'startup_zero':'PASS','typed_signed_roundtrip':'PASS','raw_byte_view_roundtrip':'PASS','wrong_width_consumer_view':'FAIL','unsigned_view_sign_contrast':'FAIL','initialized_owner_startup':'FAIL','wrong_shifted_alias':'FAIL'},
 'source-owned:experiment-anchor': {'positive_crt_zero_all_slots_typed_and_byte_views':'PASS','wrong_test_base_plus_two_bytes':'REJECTED_BASE','wrong_initialized_data_owner':'REJECTED_CRT_ZERO','wrong_unsigned_consumer_view':'REJECTED_UNSIGNED_VIEW'},
 'source-owned:window-clip-handles': {'typed_full_180_and_fmemset':'PASS_TYPED_45_180_FMEMSET','independent_byte_full_180_and_fmemset':'PASS_BYTE_180_FMEMSET','wrong_alias_base_plus_zero_control':'FAIL_ALIAS_GEOMETRY'},
 'source-owned:mode-population-vectors': {'typed_raw_SaveRec_startup_zero':'PASS','wrong_element_type_same_extent':'FAIL','wrong_SaveRec_base_B12_plus_one_word':'FAIL','wrong_SaveRec_base_C2A_plus_one_word':'FAIL'},
 'source-owned:floor-task-words': {'typed_raw_positive':'PASS_TYPED_RAW_ZERO_SIGNED','wrong_unsigned_consumer':'WRONG_UNSIGNED_CONSUMER_DETECTED','wrong_width_consumer':'WRONG_WIDTH_LONG_OWNER_DETECTED','initialized_consumer':'INITIALIZED_NONZERO_OWNER_DETECTED','shifted_alias_consumer':'SHIFTED_ALIAS_SEPARATE_BACKING_DETECTED'},
 'source-owned:ui-geometry-state': {'positive':'PASS','unsigned_fields':'PROGRAM_NONZERO','base_plus2':'PROGRAM_NONZERO','nonzero_initializer':'PROGRAM_NONZERO'},
 'source-owned:remaining-history-words': {'typed_raw_zero_write_and_known_SaveRec_pointers':'PASS','unsigned_signedness_contrast':'FAIL','deliberate_four_byte_long_control':'PASS','initialized_owner_startup_contrast':'FAIL','plus2_pointer_to_separate_backing':'PASS'},
 'source-owned:remaining-world-state': {'typed_raw_startup_saverec_pointer32':'PASS_TYPED_RAW_STARTUP_SAVEREC_POINTER32','source_unsigned_long_zero_views':'PASS_SOURCE_UNSIGNED_LONG_ZERO_VIEWS','wrong_unsigned_consumer_of_signed_int':'WRONG_UNSIGNED_VIEW_DETECTED','initialized_nonzero_owner':'INITIALIZED_NONZERO_OWNER_DETECTED','plus2_independent_saverec_backing':'PLUS2_INDEPENDENT_BACKING_DETECTED'},
}

def alias(name, target, delta=0):return {'alias':name.lower(),'target':target.lower(),'delta':delta}
def fixup(segment, offset, target, addend='00000000'):
    return dict(segment=segment,offset=offset,width=4,loc='pointer32',self_relative=False,target_kind='external',target=target,frame_kind='target',frame=target,displacement=0,encoded_addend=addend)
def consumer(basename, owners, *, data=None, publics=None, fixups=None, commons=None):
    return dict(module_name=basename+'.C',owner_names=owners,owner_communals=commons or [],owner_publics=publics or [],
                segment_lengths={k:len(v)//2 for k,v in (data or {}).items()},initialized_data_hex=data or {},linker_fixups=fixups or [])
def policy(module, provider_communals):
    names=sorted(r['name'] for r in provider_communals)
    cases=CASES[module]
    p=dict(module=module,communals=provider_communals,required_cases=cases,linkers=['rtlink400','rtlink610'],
           owners=names,aliases={c:[] for c in cases},compiler_controls={},save_rec_pointer_fixups=[])
    r=p['compiler_controls']
    if module.endswith('remaining-ant-state'):
        rows=[communal(symbol(s),4) for s in ANT_PAIRS]+[communal(symbol(s),2) for s in ANT_WORDS]+[communal(symbol('0C26'),4)]
        r['NAT18']=data_rule('NAT18',rows)
        r['WIDOWN']=data_rule('WIDOWN',[communal(row['name'],4) for row in rows])
        r['SHTPAIR']=data_rule('SHTPAIR',[communal(row['name'],2 if row['name'] in {symbol(s) for s in ANT_PAIRS} else row['length']) for row in rows])
        import struct
        raw=b''.join(struct.pack('<hh',100+i,-100-i) for i in range(4))+b''.join(struct.pack('<h',i) for i in range(1,14))+struct.pack('<l',123456)
        offsets=list(range(0,16,4))+list(range(16,42,2))+[42]
        r['INITOWN']=data_rule('INITOWN',[],publics=[dict(name=row['name'],segment='INITOWN7_DATA',offset=off) for row,off in zip(rows,offsets)],data={'INITOWN7_DATA':raw.hex()})
        for base,shift in [('POSCON',False),('SHICON',True)]:
            seg=base+'7_DATA';target=[symbol('0C26'),symbol('0D70')]
            data='04000100'+('02000000' if shift else '00000000')+'02000100'+('02000000' if shift else '00000000')+'00'*8
            r[base]=consumer(base,['_ProbeRows'],publics=[dict(name='_ProbeRows',segment=seg,offset=0)],data={seg:data},fixups=[fixup(seg,12,target[1],'02000000' if shift else '00000000'),fixup(seg,4,target[0],'02000000' if shift else '00000000')])
            p['save_rec_pointer_fixups'] += [dict(probe=base,segment=seg,offset=4+8*i,width=4,loc='pointer32',target=s.lower(),displacement=0,encoded_addend='02000000' if shift else '00000000') for i,s in enumerate(target)]
        for base in ('WIDCON','UNSCON','INICON'):r[base]=consumer(base,names)
        p['aliases']['wide_control']=[alias('_ProbeWhole'+str(i),symbol(s)) for i,s in enumerate(ANT_WORDS)]+[alias('_ProbeUpper'+str(i),symbol(s),2) for i,s in enumerate(ANT_WORDS)]
        p['control_outcomes']={c:'PASS' if c=='positive18' else 'FAIL' for c in cases}
    elif module.endswith('balloon-deadline-timers'):
        rows=[communal(symbol(s),4) for s in BALLOONS]
        for key in ('BLNTMR','BLNUNSG'):r[key]=data_rule(key,rows)
        r['BLNWID']=data_rule('BLNWID',[communal(symbol(s),2 if s=='050C' else 4) for s in BALLOONS])
        r['BLNSHFT']=data_rule('BLNSHFT',[communal('_BalloonTimerBacking',2,4)]+rows[1:])
        r['BLNINIT']=data_rule('BLNINIT',[],publics=[dict(name=symbol(s),segment='BLNINIT5_DATA',offset=4*i) for i,s in enumerate(BALLOONS)],data={'BLNINIT5_DATA':'01000000020000000300000004000000'})
        p['aliases']['wrong_shifted_alias']=[alias(symbol('050C'),'_BalloonTimerBacking',2)]
    elif module.endswith('experiment-anchor'):
        s=symbol('09FC')
        for key,base,count,elem in [('owner','EXPANCH',2,2),('short_extent','SHORT',1,2),('byte_width','BYTE',4,1),('wide_width','LONGS',2,4),('unsigned_same_width','UNSIGNED',2,2)]:r[key]=data_rule(base,[communal(s,count,elem)])
        r['initialized_nonzero']=data_rule('INIT',[],publics=[dict(name=s,segment='INIT5_DATA',offset=0)],data={'INIT5_DATA':'57136824'})
        p['control_outcomes']={c:'PASS' if c.startswith('positive_') else 'FAIL' for c in cases}
        p['aliases']={c:[alias('_ExperimentAnchorProbeAlias',s,2 if c=='wrong_test_base_plus_two_bytes' else 0)] for c in cases}
    elif module.endswith('window-clip-handles'):
        s=symbol('3B60')
        keys=['natural_handle_45','wrong_near_nested_handle_45','wrong_pointer_depth_same_four_byte_cell','short_handle_44','byte_array_same_180_extent']
        for i,(key,count,elem) in enumerate(zip(keys,[45,45,45,44,180],[4,2,4,4,1]),1):r[key]=data_rule('H450000'+str(i),[communal(s,count,elem)])
        r['initialized_handle_nonzero_control']=data_rule('H4500006',[],publics=[dict(name=s,segment='H45000065_DATA',offset=0)],data={'H45000065_DATA':'78563412'+'00'*176})
        r['wrong_base_name_equal_type']=data_rule('H4500007',[communal('_H45Q4R7_WrongBase',45,4)])
        p['control_outcomes']={c:'FAIL' if c.startswith('wrong_') else 'PASS' for c in cases}
        p['raw_text']={c:('START_BYTE\r\n' if c.startswith('independent_') else 'START_TYPED\r\n')+m+'\r\n' for c,m in cases.items()}
        p['aliases']={c:[alias(symbol('3B61'),s,0 if c.startswith('wrong_') else 1)] for c in cases}
    elif module.endswith('mode-population-vectors'):
        rows=[communal(symbol(s),n,2) for s,n in [('0B12',6),('0C2A',6),('0D40',20),('0D72',20)]]
        r['natural_owner']=data_rule('MPVOWNR',rows)
        for key,base,count,elem in [('short_int5','CTL5WORD',5,2),('byte12','CTLBYTE',12,1),('unsigned_int6','CTLUNSGN',6,2)]:r[key]=data_rule(base,[communal(symbol('0B12'),count,elem)])
        r['initialized_int6']=data_rule('CTLINIT',rows[1:],publics=[dict(name=symbol('0B12'),segment='CTLINIT7_DATA',offset=0)],data={'CTLINIT7_DATA':'0100'+'00'*10})
        for c in cases:p['aliases'][c]=[alias('_SaveB12Alias',symbol('0B12'),2 if c=='wrong_SaveRec_base_B12_plus_one_word' else 0),alias('_SaveC2AAlias',symbol('0C2A'),2 if c=='wrong_SaveRec_base_C2A_plus_one_word' else 0)]
        p['save_rec_pointer_fixups']=[{k:v for k,v in fixup('M35F5SV7_DATA',off,symbol(s)).items() if k in ('segment','offset','width','loc','target','displacement','encoded_addend')} for off,s in [(740,'0B12'),(748,'0C2A')]]
    elif module.endswith('floor-task-words'):
        rows=[communal('_'+s,2) for s in ('DROPdir','Tindex')]
        r['natural_provider']=data_rule('FLOORTSK',rows)
        r['wrong_width_owner']=data_rule('LONGOWR',[communal('_'+s,4) for s in ('DROPdir','Tindex')])
        r['initialized_nonzero_owner']=data_rule('INITOWR',[],publics=[dict(name='_'+s,segment='INITOWR7_DATA',offset=2*i) for i,s in enumerate(('DROPdir','Tindex'))],data={'INITOWR7_DATA':'3412f9ff'})
        r['unsigned_consumer']=consumer('UNSRUN',names)
        p['control_outcomes']={c:'PASS' if c=='typed_raw_positive' else 'FAIL' for c in cases}
        for c in cases:p['aliases'][c]=[alias(symbol('0F3A'),'_DROPdir',2 if c=='shifted_alias_consumer' else 0),alias(symbol('0F18'),'_Tindex',2 if c=='shifted_alias_consumer' else 0)]
        p['aliases']['wrong_width_consumer'] += [alias('_ProbeUpperDrop','_DROPdir',2),alias('_ProbeUpperIndex','_Tindex',2)]
    elif module.endswith('ui-geometry-state'):
        order='10D2 110C 1104 392C'.split();rows=[communal(symbol(s),8) for s in order]
        r['owner']=data_rule('UIGEO',rows);r['unsigned_same_omf']=data_rule('UIGEO',rows)
        for key,base,suffix,width in [('rect_point_prefix4','NEGPOIN','10D2',4),('rect_right_long10','NEGLONG','10D2',10),('bitmap_near6','NEARBIT','392C',6)]:r[key]=data_rule(base,[communal(symbol(s),width if s==suffix else 8) for s in order])
        r['independent_base_backing']=data_rule('BASEOWN',[communal('_geoBaseBacking',4,8)])
        r['initialized_owner']=data_rule('UIGINI',rows[1:],publics=[dict(name=symbol('10D2'),segment='UIGINI5_DATA',offset=0)],data={'UIGINI5_DATA':'3412000000000000'})
        p['control_outcomes']={c:'PASS' if c=='positive' else 'FAIL' for c in cases}
        layout='LAYOUT R=8/0,2,4,6 P=4/0,2 B=8/0,2,4/PTR4\r\n'
        import re
        p['raw_patterns']={'positive':re.escape(layout+'ZERO32='+'0'*64+'\r\nPOST32=F5FF0C004433FEFFF3FF0E005544FCFFF1FF10006655FAFFEFFF1200')+'[0-9A-F]{8}'+re.escape('\r\nPASS\r\n')}
        p['raw_text']={'unsigned_fields':'NEGATIVE unsigned fields read as 65535\r\nPROGRAM_NONZERO\r\n','base_plus2':'NEGATIVE +2 base is not whole Rect base; backing independent\r\nPROGRAM_NONZERO\r\n','nonzero_initializer':layout+'FAIL typed startup zero\r\nPROGRAM_NONZERO\r\n'}
    elif module.endswith('remaining-history-words'):
        rows=[communal(symbol(s),2) for s in HISTORY]
        r['natural_provider']=data_rule('OWNBASE',rows)
        r['wide_provider']=data_rule('OWNWIDE',[communal(symbol(s),4 if s=='0EB4' else 2) for s in HISTORY])
        r['initialized_provider']=data_rule('OWNINIT',[row for row in rows if row['name']!=symbol('0EB4')],publics=[dict(name=symbol('0EB4'),segment='OWNINIT5_DATA',offset=0)],data={'OWNINIT5_DATA':'0100'})
        save='0EAC 0EF8 0EFA 0F0C 0F0E 0F12 0F26 0F34 0F44'.split()
        for key,base in [('positive_fixture','CRTPOS'),('initialized_consumer_fixture','CRTINIT')]:
            seg=base+'5_DATA';r[key]=consumer(base,['_V25Save'],publics=[dict(name='_V25Save',segment=seg,offset=0)],data={seg:'0200010000000000'*9},fixups=[fixup(seg,4+8*i,symbol(s)) for i,s in reversed(list(enumerate(save)))])
        for key,base in [('signedness_fixture','CRTSIGN'),('wide_consumer_fixture','CRTWIDE')]:r[key]=consumer(base,names)
        r['separate_backing_fixture']=consumer('CRTSHFT',['_ShiftBk','_ShiftRec'],commons=[communal('_ShiftBk',4)],publics=[dict(name='_ShiftRec',segment='CRTSHFT5_DATA',offset=0)],data={'CRTSHFT5_DATA':'0200010002000000'},fixups=[fixup('CRTSHFT5_DATA',4,'_ShiftBk','02000000')])
        p['save_rec_pointer_fixups']=[dict(probe='CRTPOS',offset=4+8*i,width=4,loc='pointer32',target=symbol(s),displacement=0,encoded_addend='00000000') for i,s in enumerate(save)]
        p['save_rec_pointer_fixups'].append(dict(probe='CRTSHFT',offset=4,width=4,loc='pointer32',target='_ShiftBk',displacement=0,encoded_addend='02000000'))
    elif module.endswith('remaining-world-state'):
        rows=[communal(symbol(s),4 if s in ('0204','0214') else 2) for s in WORLD]
        for key,base in [('positive_provider','WSCAL25'),('unsigned_same_width','WSCALUNS')]:r[key]=data_rule(base,rows)
        r['wrong_width']=data_rule('WSCALWID',[communal(symbol(s),4 if s in ('0204','0208','0214') else 2) for s in WORLD])
        r['initialized_nonzero']=data_rule('WSCALINI',[row for row in rows if row['name']!=symbol('0208')],publics=[dict(name=symbol('0208'),segment='WSCALINI7_DATA',offset=0)],data={'WSCALINI7_DATA':'0100'})
        r['plus2_independent_backing']=data_rule('WSCALSGN',[communal(symbol('0208'),2),communal('_ProbeIndependentBacking',2)])
        r['consumer_positive']=consumer('WSCALPOS',['_ProbeSaveTable'],publics=[dict(name='_ProbeSaveTable',segment='WSCALPOS7_DATA',offset=0)],data={'WSCALPOS7_DATA':'0200010000000000'*12},fixups=[fixup('WSCALPOS7_DATA',4+8*i,'_ProbeS'+str(i)) for i in reversed(range(12))])
        r['consumer_shifted']=consumer('WSCALSHF',['_ProbeSaveTable'],publics=[dict(name='_ProbeSaveTable',segment='WSCALSHF7_DATA',offset=0)],data={'WSCALSHF7_DATA':'0200010000000000'},fixups=[fixup('WSCALSHF7_DATA',4,'_ProbeShift')])
        for key,base in [('consumer_initialized','WSCALICN'),('consumer_unsigned','WSCALSIG'),('consumer_zero_views','WSCALUZR')]:r[key]=consumer(base,names)
        p['case_owners']={'plus2_independent_saverec_backing':[symbol('0208')]}
        p['control_outcomes']={c:'PASS' if c in ('typed_raw_startup_saverec_pointer32','source_unsigned_long_zero_views') else 'FAIL' for c in cases}
        p['aliases']['typed_raw_startup_saverec_pointer32']=[alias('_ProbeE'+str(i),symbol(s)) for i,s in enumerate(WORLD)]+[alias('_ProbeS'+str(i),symbol(s)) for i,s in enumerate(WORLD_SAVE)]
        p['aliases']['source_unsigned_long_zero_views']=[alias('_ProbeU0',symbol('0204')),alias('_ProbeU1',symbol('0214'))]
        p['aliases']['wrong_unsigned_consumer_of_signed_int']=[alias('_ProbeSign',symbol('0208'))]
        p['aliases']['initialized_nonzero_owner']=[alias('_ProbeInit',symbol('0208'))]
        p['aliases']['plus2_independent_saverec_backing']=[alias('_ProbeShift',symbol('0208'),2),alias('_ProbeBacking','_ProbeIndependentBacking')]
        p['save_rec_pointer_fixups']=[dict(probe='WSCALPOS',offset=4+8*i,width=4,loc='pointer32',target='_ProbeS'+str(i),displacement=0,encoded_addend='00000000') for i in range(12)]
    return p
