"""Assemble work/align/FINDINGS.json from the worker's artefacts (survey, frames, exp*)."""
import json, sys, glob
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(n):
    p = HERE / n
    return json.loads(p.read_text()) if p.exists() else None


survey, frames = load('survey.json'), load('frames.json')
man = json.loads((ROOT / 'layout/manifest.json').read_text())['modules']
ext_mods = {k: v for k, v in man.items() if v.get('extent') and not k.startswith('data:')}
mis = []
for k, v in ext_mods.items():
    for c in survey[k]['code']:
        if v['extent']['start'] % 2 and c['align'] == 'word':
            mis.append({'module': k, 'extent_start': f"{v['extent']['start']:05X}", 'segdef': c['align']})
aligns = sorted({c['align'] for k in ext_mods for c in survey[k]['code']})
trans = frames or []
odd_fill = sum(1 for t in trans if t['prev_odd_end'] and t['gap'] == '00')
even_cont = sum(1 for t in trans if not t['prev_odd_end'] and t['gap'] == '')
odd_cont = [t for t in trans if t['gap'] == '' and t['odd_start']]
exp1, exp2, exp3, exp4 = load('exp.json'), load('exp2.json'), load('exp3.json'), load('exp4.json')
segalign = load('segalign.json')
sb = sorted(glob.glob(str(HERE / 'sb_*.logs')))

F = {
 'worker': 'align', 'date': '2026-09-30',
 'question': 'root:19A9 accepted at odd 0x19A95 although MSC code segments are WORD aligned; root:2CFB '
             'MEMHOOK_TEXT placed after the runtime _TEXT/EMULATOR_TEXT.',
 'task1_alignment_survey': {
   'complete_TU_code_modules': len(ext_mods),
   'code_SEGDEF_alignments_seen': aligns,
   'misaligned_extent_starts': mis,
   'all_compilers_and_options_give_WORD_code_segments': segalign and all(
       any(s[2] == 'word' for s in row[2] if s[1] == 'CODE') for row in segalign if isinstance(row[2], list)),
   'segalign_cases': segalign,
   'oracle_frame_transitions': {'total': len(trans), 'odd_end_then_00_fill': odd_fill,
                                'even_end_contiguous': even_cont,
                                'odd_start_contiguous_violations': [f"{t['unit']}:{t['frame']} at {t['first']}"
                                                                    for t in odd_cont],
                                'others_note': 'remaining transitions have data (tables, copyright string) or an '
                                               'unlisted stub byte between the frames'},
   'data_side': 'DGROUP shows the same rule at the same boundary: 1986 _DATA ends odd at 55B3:3661, a 00 fill '
                'byte follows, 19A9 _DATA starts word aligned at 3662',
   'scripts': ['work/align/survey.py', 'work/align/frames.py', 'work/align/segalign.py'],
 },
 'task2_19A9': {
   'verdict': 'MIS-FRAMED BOUNDARY, not an alignment exception. The three unreferenced retf at 19A95, 19A96, '
              '19A97 are the last three (empty) functions of the index module root:1986; that object ends at the '
              'even 19A98 and root:19A9 starts at 19A9:0008 = 19A98, word aligned, no fill needed.',
   'why_the_frame_was_wrong': 'the three bytes have no reference (no relocation, no call); their rows were '
                              'reviewed as 19A9:0005-0007 by frame arithmetic only (functions.json note "after '
                              "FindIndex's end at 19A9:0004\"). Frame 19A9 is attested only from 19A9:0008 on "
                              '(S27 far pointer 59224 -> 19A9:0008, far calls to 000B, 001D, 0310, 031D).',
   'evidence': [
     'CODEALIGN: every MSC/QC profile and option set pinned here emits WORD code SEGDEFs (/Os, /Ox, /Od, /Zi, /Gs, '
     '/Oeg, /G2, /Gw, /Gc, /Za, /Zp1, /NT...); 84/85 accepted complete TUs and 93/94 code-frame transitions obey it; '
     'the one exception is this boundary',
     'Win16 index TU (MAPSYM order, simantw symbols.csv seg 7 39558-41078): OpenIndex, CreateIndex, CloseIndex, '
     'FindIndex, DeleteCurrentIndex, AddIndex, DeleteIndex. DOS 1986: OpenIndex, CreateIndex (1-byte retf: write '
     'side stubbed empty in the read-only DOS build), CloseIndex, FindIndex, then exactly three 1-byte retf',
     'style: 19A9 stubs its write side with Punt("... READ-ONLY run") (DBAdd/DBDelete/DBPack), the index module with '
     'empty bodies (CreateIndex); three empty functions at the head of 19A9 would have no Win16 counterpart',
     'gate: the corrected root:19A9 source (without the stubs) compiles to 815 bytes and binds exactly at 19A98 '
     '(promote --verify-only: every claim, _DATA, CONST and the whole segment exact; the only refusal is the '
     'function-table rows 19A9:0005-0007, which the reframe moves to 1986:0235-0237)'],
   'hypotheses_tested_with_real_linkers': {
     'instrument': 'work/align/exp.py: synthetic objects of the same shape (odd-length function, then '
                   'retf,retf,retf,sub ax,ax;retf), MSC 6.00AX /AL /Os /Oeg /Gs /Zi, linked with MS LINK 5.10 and '
                   'RTLink/Plus 6.10 (pinned hashes); both linkers agree in every variant',
     'results': {v: {'linker_output_after_IDX': r['mslink510'].get('next_bytes'),
                     'rtlink610_same': r['rtlink610'].get('next_bytes') == r['mslink510'].get('next_bytes'),
                     'reproduces_original': r['mslink510'].get('contiguous_like_original'),
                     'segments': r['mslink510'].get('segments')} for v, r in (exp1 or {}).items()},
     'reading': {
       'V1ACC (accepted split)': 'fill 00 inserted: the accepted layout is not linker output',
       'V2HYPB (3 stubs in 1986)': 'reproduces the original, no fill, 19A9 frame offset 8',
       'V2HYPA (1 stub in 1986)': 'also reproduces the bytes; rejected on the Win16 member count and stub style',
       'V3NT (/NT DB_TEXT shared)': 'one combined segment = one frame (contradicts frames 1986/19A9 and the relocated '
                                    'far call 19AC1 -> 1986:012A, TU-1) and the contribution is still word aligned '
                                    '(fill)',
       'V4ALLOC (#pragma alloc_text)': 'second segment of one object is WORD aligned too: fill',
       'V5MBYTE (MASM segment byte)': 'the only variant that places code at an odd address; excluded because 19A9 '
                                      'is MSC 6.00AX output (755-byte DBRecall, _DATA/CONST contributions, /Zi record '
                                      'breaks) and the jump from DBRecall into 1986 is an ordinary compiled far call',
       'V6MWORD': 'control: MASM word segment gets the fill'}},
 },
 'task2_2CFB': {
   'verdict': 'MEMHOOK_TEXT (class CODE) was read after the runtime library search: the hook object came from a '
              'library (or an object named in the LIBRARY list) searched after LLIBCR/LIBH. A different segment '
              'class is excluded.',
   'evidence': [
     'MS LINK 5.10 and RTLink 6.10 (exp2): an object listed as FILE puts MEMHOOK_TEXT before _TEXT (the t3 result); '
     'MH.LIB searched after LLIBCR puts it after EMULATOR_TEXT (original); MH.LIB searched before LLIBCR: before '
     '_TEXT; RTLink FILE after LIBRARY in the script: still before _TEXT',
     'class hypothesis: a non-CODE class (MEMHOOK) or a class ending in CODE (HOOKCODE) follows ENDCODE in DOSSEG '
     'order; in an overlaid RTLink link (exp3) both land behind the overlay areas in the resident data section '
     '(with C_ETEXT), not in the root. The original has C_ETEXT at 3D57:0000 (crt0 DBDATA base16 word at S27 '
     '5D8F0 = 3D57, relocated) while MEMHOOK_TEXT is at 2CFB2 in the root: excluded',
     'exp4: RTLink 6.10 accepts "LIBRARY LLIBCR, LIBH, R2CFB.OBJ" and then places MEMHOOK_TEXT exactly like the '
     'original (after EMULATOR_TEXT, before $$OVLMGR); tools/rtlink.py patch uses this',
     'MS LIB.EXE used only for exp2/exp3 (C:/tools/msc-6.00/BIN/lib.exe sha256 '
     '418aec4161ef09084aaf2bed66e4de9e007eb6f2bedd1990b73707f624336ff3, not pinned)'],
   'results_exp2': {v: {'mslink510': r['mslink510']['order'], 'rtlink610': r['rtlink610']['order']}
                    for v, r in (exp2 or {}).items()},
   'results_exp3_overlaid_rtlink610': {v: r['verdict'] for v, r in (exp3 or {}).items()},
   'results_exp4': {v: r['segments'] for v, r in (exp4 or {}).items()},
 },
 'task3_deliverables': {
   'gate_patch': {
     'files': {'work/align/patch/tools_modules.py': 'tools/modules.py: code_alignment_reasons (rule '
                                                              'CODEALIGN-1) in verify_extent (extent start) and '
                                                              'verify_module (origin of a later object without extent)',
               'work/align/patch/tools_promote.py': 'tools/promote.py: --drop-extent WHY (journaled), the '
                                                              'sanctioned way to un-complete a mis-framed TU so its rows '
                                                              'can be re-framed (functions.py reframe refuses claimed '
                                                              'rows; extent_row_reasons refuses the corrected extent '
                                                              'while the old rows exist)',
               'work/align/patch/tools_rtlink.py': 'tools/rtlink.py: late root objects in the LIBRARY list '
                                                             'after LLIBCR, LIBH; run_link reads the pin from '
                                                             "toolchain.json 'linkers' (compiler.verify_profile raised "
                                                             "KeyError 'rtlink610': run_link was broken)",
               'work/align/patch/tests_test_codealign.py': 'tests/test_codealign.py',
               'work/align/patch/T13_m19A9_odd_start.c': 'tests/negatives/T13_m19A9_odd_start.c (the '
                                                                   'pre-correction canonical 19A9 source)'},
     'base_md5': (HERE / 'base' / 'MD5SUMS').read_text().splitlines(),
     'install_order': ['copy the patched tools/tests', 'bash work/align/migrate.sh (4 steps: promote '
                       '--drop-extent + release; functions.py reframe x3; promote 1986 claims; promote 19A9 '
                       '--extent 19A98:19DC7)', 'python tools/validate.py'],
     'note': 'with the patch installed and the migration NOT run, validate refuses root:19A9 for CODEALIGN-1 alone '
             '(negative control on real data); the migration is required before or with the patch',
   },
   'drafts': {'work/align/m19A9.c': 'root:19A9 without the three stubs (extent 19A98:19DC7)',
              'work/align/m1986.c': 'root:1986 + f_1986_0235/0236/0237 (empty) after the FindIndex scaffold'},
   'names': 'the three stubs keep placeholder names f_1986_0235..0237; Win16 candidates DeleteCurrentIndex, '
            'AddIndex, DeleteIndex by position only (content-free bodies: xver cannot confirm; a decisions.json '
            'entry needs a second independent anchor)',
   'sandbox_logs': sb,
   'sandbox_status': 'INCOMPLETE: run of 11:51 stopped at session end; its baseline failed only because asm_evidence '
                     'paths under build/workers/ were not copied (sandbox_run.sh fixed). Patched/migrated validate '
                     'not yet run: rerun bash work/align/sandbox_run.sh',
 },
 'not_done': ['no canonical file changed: the migration needs functions.py reframe (layout/) and the new '
              '--drop-extent option, both outside this worker\'s write scope; the sandbox shows the full sequence',
              'the Dec 1991 RTLink/Plus is not available: all linker results are from MS LINK 5.10 and RTLink 6.10'],
}
(HERE / 'FINDINGS.json').write_text(json.dumps(F, indent=1))
print('FINDINGS.json written;', len(mis), 'misaligned extent starts;', len(trans), 'transitions')
