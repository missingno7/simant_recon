from __future__ import annotations
import ctypes as ct, hashlib, importlib.util, json, struct, sys
from pathlib import Path
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'portable/tests/setup/evidence'))
spec=importlib.util.spec_from_file_location('reuse',ROOT/'portable/tests/setup/evidence/setup_reuse_differential.py')
reuse=importlib.util.module_from_spec(spec); sys.modules[spec.name]=reuse; spec.loader.exec_module(reuse)
lib=ct.CDLL(str(ROOT/'build/workers/behavior_controls_next4/native_probe.dll'))
lib.controls_next4_run.argtypes=[ct.POINTER(ct.c_int16),ct.POINTER(ct.c_int16),ct.POINTER(ct.c_int32),ct.POINTER(ct.c_int32),ct.POINTER(ct.c_int32),ct.c_size_t]
lib.controls_next4_run.restype=ct.c_int
lib.controls_next4_trace_count.restype=ct.c_size_t
lib.controls_next4_complement_changes.restype=ct.c_size_t
sha=lambda b:hashlib.sha256(b).hexdigest()
original,machine,fixture,_=reuse.original_reinit()
rect_mode=reuse.base.read_object_rect(machine,fixture['win18_seg'],13)
rect_caste=reuse.base.read_object_rect(machine,fixture['win19_seg'],13)
knob=reuse.base.read_words(machine,'knobSize',2)
rects=(ct.c_int16*8)(*(rect_mode+rect_caste)); wh=(ct.c_int16*2)(*knob); mut=(ct.c_int32*len(reuse.INPUT))(*reuse.INPUT)
out=(ct.c_int32*128)(); events=(ct.c_int32*64)()
count=lib.controls_next4_run(rects,wh,mut,out,events,64)
complement_changes=lib.controls_next4_complement_changes()
if count<0: raise RuntimeError(count)
v=list(out[:count]); trace=list(events[:lib.controls_next4_trace_count()]); at=0; candidate={'mode_rect':rect_mode,'caste_rect':rect_caste}
def take(name,n):
 global at
 candidate[name]=v[at:at+n]; at+=n
take('knob_size',2)
take('controls',8);take('mode_level',3);take('caste_level',3);take('mode_presets',12);take('caste_presets',12);take('ideal_caste',4);take('triangle_dimensions',3);take('mode_triangle_points',6);take('caste_triangle_points',6);take('mode_point',2);take('caste_point',2)
expected={k:original[k] for k in ['mode_level','caste_level','mode_presets','caste_presets','ideal_caste','controls']}
expected.update({'knob_size':knob,'mode_rect':rect_mode,'caste_rect':rect_caste,
 'mode_point':reuse.base.read_words(machine,'fd_50F6_0358',2,signed=True),
 'caste_point':reuse.base.read_words(machine,'fd_50F6_022E',2,signed=True),
 'mode_triangle_points':reuse.base.read_words(machine,'fd_50F6_3816',6,signed=True),
 'caste_triangle_points':reuse.base.read_words(machine,'fd_50F6_3822',6,signed=True),
 'triangle_dimensions':[reuse.base.read_words(machine,'triWidth',1)[0],reuse.base.read_words(machine,'triHeight',1)[0],reuse.base.read_dword(machine,'fd_50F6_382E',signed=True)]})
mismatches={k:{'candidate':candidate[k],'original':expected[k]} for k in expected if candidate.get(k)!=expected[k]}
source=ROOT/'src/root/m0798.c'; profile=ROOT/'build/workers/recovered_source_next4/generated'
prov=json.loads((profile/'provenance.json').read_text())
report={
 'schema':'portable-m0798-next4-controls-selected-source-differential-v1',
 'status':'DIAGNOSTIC_ONLY_NOT_BEHAVIOR_ACCEPTANCE',
 'oracle':{'executable_sha256':reuse.base.exe.load().sha256,'function_id':'root0798:0F0D','function':reuse.base.functions.get('initControls')},
 'source':{'path':'src/root/m0798.c','sha256':sha(source.read_bytes()),'selected_functions':prov['versioned_profile_extension']['selected_source']['function_anchors']},
 'candidate':{'generator_path':'portable/tools/recover_source_next4.py','generator_sha256':sha((ROOT/'portable/tools/recover_source_next4.py').read_bytes()),'profile_status':prov['versioned_profile_extension']['status'],'header_sha256':sha((profile/'recovered_state.h').read_bytes()),'state_source_sha256':sha((profile/'recovered_state.c').read_bytes()),'selected_tu_sha256':sha((profile/'root_m0798_controls.c').read_bytes()),'native_probe_sha256':sha((ROOT/'build/workers/behavior_controls_next4/native_probe.c').read_bytes()),'native_probe_dll_sha256':sha((ROOT/'build/workers/behavior_controls_next4/native_probe.dll').read_bytes())},
 'inputs':{'ndx_sha256':sha((ROOT/'assets/HCEGANT.NDX').read_bytes()),'dat_sha256':sha((ROOT/'assets/HCEGANT.DAT').read_bytes()),'behavior_harness_sha256':reuse.behavior.digest(reuse.behavior.HARNESS_SOURCE),'setup_reuse_runner_sha256':sha((ROOT/'portable/tests/setup/evidence/setup_reuse_differential.py').read_bytes())},
 'domain':{'calls_per_lane':2,'case_count':1,'seed':'HCEGANT profile0 windows 18+19, original reinit mutable defaults/presets','mutation':{'mode_defaults':reuse.MODE_DEFAULT,'caste_defaults':reuse.CASTE_DEFAULT,'mode_rows_1_to_3':reuse.MODE_ROWS,'caste_rows_1_to_3':reuse.CASTE_ROWS,'private_selectors':[2,3]},'geometry':{'mode_rect':rect_mode,'caste_rect':rect_caste},'knob_size':knob},
 'compared':sorted(expected.keys()),'candidate_observation':candidate,'original_observation':expected,'candidate_host_trace':trace,'original_host_trace':original['callback_trace'],'mismatches':mismatches,'mismatch_count':len(mismatches),
 'modified_field_complement_guard':{'fields':'all RecoveredState bytes on both initControls calls','allowed_source_write_ranges':['knobSize','ModeAuto','CasteAuto','fd_50F6_0468','fd_3D57_07EA','fd_50F6_0370','fd_50F6_024E','modeLevels[0..2]','casteLevels[0..2]','fd_3D57_0810[0..2]','fd_3D57_07F2[0..2]','IdealCaste','triWidth','triWidthL','triWidthR','triHeight','fd_50F6_382E','fd_50F6_3816','fd_50F6_3822','fd_50F6_0358','fd_50F6_022E'],'unexplained_changed_bytes':complement_changes,'passed':complement_changes==0},
 'boundary':'The native call executes the eight selected historical source bodies under a RecoveredState binding. Three required UI edges are supplied with identical controlled effects: bitmap size from actual HCEGANT kind-2 object 0x578, rectangles from the original DOS window fixture, and animation cleanup (handles are null in this controlled fixture). The two module-static selectors are explicitly initialized to the original test sentinels 2/3 and verified unchanged; they are not referenced by initControls. Non-null DOS animation-handle cleanup remains a separate host-service case.'}
path=ROOT/'build/workers/behavior_controls_next4/controls_differential_report.json'; path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':str(path),'case_count':1,'calls_per_lane':2,'compared_fields':len(expected),'mismatches':len(mismatches),'report_sha256':sha(path.read_bytes())},indent=2))
if mismatches: raise SystemExit(1)
