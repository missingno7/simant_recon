"""Root literal declarations and natural fixture data/fixup contracts."""
from dos_storage_contracts import communal, data_rule, symbol
from dos_storage_policies_v25 import consumer, fixup, alias

SCALARS = '04E0 04F2 0502 0510 059E 06AC 0736 08DC 08E8 0D9A 0FF8 1004 1006 103A 103C 1044 1046 1048 104A'.split()
SAVE = '04E0 04F2 0502 0510 059E 06AC 0736 08DC 08E8 1004 1006 103C 1044 1048'.split()
CASES = {
 'source-owned:remaining-ui-state':{
  'nonzero_initialized_owner_contrast':'FAIL', 'positive_typed_raw_startup_zero':'PASS',
  'separate_backing_plus2_alias_contrast':'FAIL', 'wrong_near_pointer_view':'FAIL',
  'wrong_pointer_depth_consumer_view':'FAIL', 'wrong_signedness_consumer_view':'FAIL',
  'wrong_width_consumer_view':'FAIL'},
 'source-owned:remaining-window-state':dict(POSITIVE='PASS',UNSIGN='FAIL',WIDE='PASS',INIT='FAIL',DEPTH='PASS',SHIFT02='PASS'),
 'source-owned:remaining-scalar-tail':dict(POSITIVE='PASS',UNSIGN='FAIL',WIDE='PASS',INIT='FAIL',SHIFT02='PASS'),
 'source-owned:balloon-buffer-tables': {
  'six_slot_typed_raw_coupled_positive':'PASS',
  'wrong_pointer_depth_owner_omf_contrast':'MEASURED',
  'unsigned_style_signedness_contrast':'FAIL',
  'wrong_four_byte_plane_width_omf_contrast':'MEASURED',
  'five_slot_short_extent_omf_contrast':'MEASURED',
  'seven_slot_plus_one_extent_omf_contrast':'MEASURED',
  'initialized_nonzero_count_startup_contrast':'FAIL',
  'plus_two_alias_independent_backing_contrast':'FAIL'},
}

def policy(module, provider_communals):
    cases=CASES[module]
    names=sorted(r['name'] for r in provider_communals)
    p=dict(module=module,communals=provider_communals,required_cases=cases,
           linkers=['rtlink400','rtlink610'],owners=names,aliases={c:[] for c in cases},
           compiler_controls={},save_rec_pointer_fixups=[])
    r=p['compiler_controls']
    if module.endswith('remaining-scalar-tail'):
        rows=[communal(symbol(s),4 if s=='0736' else 2) for s in SCALARS]
        r['natural_owner']=data_rule('OWNBASE',rows)
        r['wide_owner']=data_rule('OWNWIDE',[communal(symbol(s),4 if s in ('04E0','0736') else 2) for s in SCALARS])
        r['initialized_owner']=data_rule('OWNINIT',rows[1:],publics=[dict(name=symbol('04E0'),segment='OWNINIT5_DATA',offset=0)],data={'OWNINIT5_DATA':'0100'})
        seg='CRTPOS5_DATA'
        r['positive_fixture']=consumer('CRTPOS',['_V26Save'],publics=[dict(name='_V26Save',segment=seg,offset=0)],
             data={seg:''.join(('0400' if s=='0736' else '0200')+'010000000000' for s in SAVE)},
             fixups=[fixup(seg,4+8*i,symbol(s)) for i,s in reversed(list(enumerate(SAVE)))])
        r['unsigned_contrast_fixture']=consumer('CRTUNSG',names)
        r['wide_consumer_fixture']=consumer('CRTWIDE',names)
        seg='CRTSHFT5_DATA'
        r['separate_backing_fixture']=consumer('CRTSHFT',['_ShiftBk','_ShiftRec'],commons=[communal('_ShiftBk',4)],
             publics=[dict(name='_ShiftRec',segment=seg,offset=0)],data={seg:'0200010002000000'},
             fixups=[fixup(seg,4,'_ShiftBk','02000000')])
        p['save_rec_pointer_fixups']=[dict(probe='CRTPOS',offset=4+8*i,width=4,loc='pointer32',target=symbol(s),displacement=0,encoded_addend='00000000') for i,s in enumerate(SAVE)]
        p['save_rec_pointer_fixups'].append(dict(probe='CRTSHFT',offset=4,width=4,loc='pointer32',target='_ShiftBk',displacement=0,encoded_addend='02000000'))
    elif module.endswith('remaining-ui-state'):
        order='1062 1064 106C 1074 107C 1092 10A6 10AC 10B8 10BA 10CC 10D0 10DA 10DE 10E0 10E2 10E6 10EA 10EE 1102'.split()
        handles=set('10CC 10DA 10E2 10E6 10EA 10EE'.split())
        rows=[communal(symbol(s),1 if s=='106C' else 4 if s in handles else 2) for s in order]
        r['natural_provider']=data_rule('UISTOR26',rows)
        r['10CC_two_element_array']=data_rule('UIA10CC',[communal(symbol(s),2,4) if s=='10CC' else row for s,row in zip(order,rows)])
        # Explicit final storage qualifier is redundant under the selected /AL.
        # This is an equivalent owner spelling, not a pointer-depth negative.
        r['10E2_far_outer_pointer_qualifier_variant']=data_rule('UIPDPOWN',rows)
        r['nonzero_initialized_1062']=data_rule('UINITOWN',rows[1:],
             publics=[dict(name=symbol('1062'),segment='UINITOWN5_DATA',offset=0)],data={'UINITOWN5_DATA':'0100'})
        r['wrong_width_long_1074']=data_rule('UIWIDOWN',[communal(symbol(s),4) if s=='1074' else row for s,row in zip(order,rows)])
        r['separate_backing']=data_rule('UIALOWN',[row for row in rows if row['name']!=symbol('1074')]+[communal('_ui_backing_1074',4)])
        p['aliases']['separate_backing_plus2_alias_contrast']=[alias(symbol('1074'),'_ui_backing_1074',2)]
        # Full S09 SaveRec source spans and exact compiled pointer32 fields.
        p['save_rec_pointer_fixups']=[dict(segment='U0177_DATA',offset=off,width=4,loc='pointer32',target=symbol(s),displacement=0,encoded_addend='00000000')
             for s,off in [('10BA',884),('10AC',876),('1074',1428),('10B8',2244),('10A6',2108)]]
    elif module.endswith('remaining-window-state'):
        # Independent WINSC26 compilation reproduces this COMDEF record order.
        # It is not a claim about the historical communal allocation order.
        order='3938 393C 3944 37D2 37D4 37D6 37DE 37E6 37EA 37EE 37F2 37F6 37FA 37FC 3836 383A 3842 384A 3852 3854 3856 3858 38B2 38B6 38B8 38BC 38C0 38C2 3934'.split()
        words=set('37D2 37D4 37FA 37FC 3852 3854 3856 3858 38B6 38C0'.split())
        rects=set('37D6 3842 384A 38C2 393C'.split())
        rows=[communal(symbol(s),2 if s in words else 8 if s in rects else 4) for s in order]
        r['candidate_owner']=data_rule('WINOWN26',rows)
        r['wide_owner']=data_rule('WINWID26',[communal(symbol(s),4 if s=='37D2' else 2 if s in words else 8 if s in rects else 4) for s in order])
        r['initialized_owner']=data_rule('WININI26',[r for r in rows if r['name']!=symbol('37D2')],
            publics=[dict(name=symbol('37D2'),segment='WININI265_DATA',offset=0)],data={'WININI265_DATA':'0100'})
        for key,base in [('positive_consumer','WINPOS26'),('signedness_contrast','WINSIG26'),('wide_consumer','WINWIDCR')]:r[key]=consumer(base,names)
        r['pointer_depth_consumer']=consumer('WINDEPTH',names+['_V26Master','_V26Payload'],
            commons=[communal('_V26Master',4),communal('_V26Payload',1)])
        seg='WINSHIFT5_DATA'
        r['separate_backing_consumer']=consumer('WINSHIFT',['_ShiftBacking','_ShiftRef'],commons=[communal('_ShiftBacking',8)],
            publics=[dict(name='_ShiftRef',segment=seg,offset=0)],data={seg:'0200010002000000'},
            fixups=[fixup(seg,4,'_ShiftBacking','02000000')])
    else:
        # The fifth owner is fixture-only: production owns count in UI state.
        def tables(n):return [communal(symbol(s),n,elem) for s,elem in [('04A6',4),('04C8',4),('04E6',2),('04F6',2)]]
        count=communal(symbol('1092'),2)
        r['exact']=data_rule('BBEXACT',tables(6)+[count])
        r['wrong_pointer_depth']=data_rule('BBPDEPTH',[communal(symbol('04A6'),4)]+tables(6)[1:]+[count])
        r['wrong_width']=data_rule('BBWIDTH',tables(6)[:3]+[communal(symbol('04F6'),6,4),count])
        r['short_five']=data_rule('BBSHORT',tables(5)+[count])
        r['extra_seven']=data_rule('BBEXTRA',tables(7)+[count])
        r['initialized_count']=data_rule('BBINIT',tables(6),publics=[dict(name=symbol('1092'),segment='BBINIT5_DATA',offset=0)],data={'BBINIT5_DATA':'0100'})
        p['control_outcomes']={c:'PASS' if c=='six_slot_typed_raw_coupled_positive' else 'FAIL' for c in cases}
        p['aliases']['plus_two_alias_independent_backing_contrast']=[alias(a,symbol(s),2) for a,s in [('_BMSG','04A6'),('_BPNT','04C8'),('_BSTY','04E6'),('_BPLN','04F6'),('_BCNT','1092')]]
    return p
