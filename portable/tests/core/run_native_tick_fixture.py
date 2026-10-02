#!/usr/bin/env python3
"""Run generated DoAntSim on an original-DOS full-state fixture.

Every unresolved non-host symbol is linked to a fail-closed stub. The runner
only reports a differential PASS after DoAntSim returns and all captured
source globals and both RNG streams match the original DOS post-state.
"""
from __future__ import annotations

import hashlib
import gzip
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATED = ROOT / "build/workers/recovered_source/generated"
GENERATED = DEFAULT_GENERATED
FIXTURE_PATH = ROOT / "portable/research/core-proof/original-tick-fixtures.json"
SCRATCH = ROOT / "build/workers/core_proof/native-cycle0"
SEQUENCE_SCRATCH = ROOT / "build/workers/core_proof/sequence-native"


def run(command: list[str], *, capture: bool = False,
        timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=ROOT, text=True, check=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        timeout=timeout,
    )


def byte_array(name: str, data: bytes) -> str:
    values = ",".join(f"0x{byte:02x}" for byte in data)
    return f"static const unsigned char {name}[{len(data)}] = {{{values}}};\n"


def create_fixture_c(row: dict, field_names: list[str]) -> str:
    lines = [
        '#include "recovered_state.h"',
        "#include <stdio.h>",
        "#include <string.h>",
        "",
        "int core_fixture_load(RecoveredState *state)",
        "{",
        "    recovered_state_init(state);",
    ]
    arrays: list[str] = []
    for index, field in enumerate(field_names):
        before = bytes.fromhex(row["pre_tick_ranges"][field])
        after = bytes.fromhex(row["post_tick_ranges"][field])
        after2 = bytes.fromhex(row["consecutive_post_tick_ranges"][field])
        arrays.append(byte_array(f"before_{index}", before))
        arrays.append(byte_array(f"after_{index}", after))
        arrays.append(byte_array(f"after2_{index}", after2))
        lines += [
            f"    if (sizeof(state->{field}) != sizeof(before_{index})) {{",
            f'        fprintf(stderr, "fixture field width mismatch: {field}\\n");',
            "        return 0;",
            "    }",
            f"    memcpy(&state->{field}, before_{index}, sizeof(before_{index}));",
        ]
    lines += ["    return 1;", "}", "", "int core_fixture_compare(const RecoveredState *state)", "{", "    int matched = 1;"]
    for index, field in enumerate(field_names):
        lines += [
            f"    if (memcmp(&state->{field}, after_{index}, sizeof(after_{index})) != 0) {{",
            f'        for (size_t mismatch = 0; mismatch < sizeof(after_{index}); ++mismatch) {{',
            f'            if (((const unsigned char *)&state->{field})[mismatch] != after_{index}[mismatch]) {{',
            f'                fprintf(stderr, "FIRST_STATE_MISMATCH {field} byte=%zu expected=%02x actual=%02x\\n", mismatch, after_{index}[mismatch], ((const unsigned char *)&state->{field})[mismatch]);',
            "                break;",
            "            }",
            "        }",
            "        matched = 0;",
            "    }",
        ]
    lines += ["    return matched;", "}", "", "int core_fixture_compare_consecutive(const RecoveredState *state)", "{", "    int matched = 1;"]
    for index, field in enumerate(field_names):
        lines += [
            f"    if (memcmp(&state->{field}, after2_{index}, sizeof(after2_{index})) != 0) {{",
            f'        fprintf(stderr, "SECOND_STATE_MISMATCH {field}\\n");',
            "        matched = 0;",
            "    }",
        ]
    lines += ["    return matched;", "}", ""]
    return "".join(arrays) + "\n".join(lines)


def create_runtime_c(row: dict, consecutive: bool = False) -> str:
    consecutive_code = ""
    if consecutive:
        consecutive_code = (
            "recovered_bind_end(&state_frame, &state);\n"
            "if (!core_fixture_compare(&state)) return 3;\n"
            f"    if (rng.s_state != (uint16_t){int(row['s_rng_seed_after_tick'])}) return 8;\n"
            "    recovered_bind_begin(&state_frame, &state);\n"
            "    printf(\"TICK_BEGIN:2\\n\"); DoAntSim(); printf(\"TICK_END:2\\n\");"
        )
    return f'''#include "recovered_state.h"
#include "portable/game/recovered/nest_adapter.h"
#include "portable/game/recovered/audio_adapter.h"
#include "portable/game/simulation/rng.h"
#include "portable/game/recovered/memory_adapter.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int core_fixture_load(RecoveredState *state);
extern int core_fixture_compare(const RecoveredState *state);
extern int core_fixture_compare_consecutive(const RecoveredState *state);
extern void recovered_rng_bind(SimRng *rng);
extern void DoAntSim(void);

static SimRng *core_rng;
static char advice_text[32][16];
static void *advice_text_ptrs[32];
static void host_intent(const char *name, long a, long b, long c)
{{ printf("HOST:%s:%ld:%ld:%ld\\n", name, a, b, c); }}
static void host_intent4(const char *name,long a,long b,long c,long d)
{{ printf("HOST:%s:%ld:%ld:%ld:%ld\\n",name,a,b,c,d); }}
static void host_intent5(const char *name,long a,long b,long c,long d,long e)
{{ printf("HOST:%s:%ld:%ld:%ld:%ld:%ld\\n",name,a,b,c,d,e); }}
static long advice_id(void *message)
{{
    unsigned i;
    for (i = 0; i < 32; ++i) if (message == advice_text_ptrs[i]) return i;
    return -1;
}}

int32_t TickCount(void)
{{ host_intent("TickCount", 0, 0, 0); return {int(row['source_tick_count'])}; }}
int32_t MacTickCount(void)
{{ host_intent("MacTickCount", 0, 0, 0); return TickCount() * 3; }}
void SetSRandSeed(uint32_t seed)
{{ if (core_rng == NULL) abort(); sim_rng_set_s_seed(core_rng, (int16_t)seed); }}
uint32_t GetSRandSeed(void)
{{ if (core_rng == NULL) abort(); return sim_rng_get_s_seed(core_rng); }}
int rand(void)
{{ if (core_rng == NULL) abort(); return (int)sim_rng_msc_rand(core_rng); }}
void srand(unsigned seed)
{{ if (core_rng == NULL) abort(); core_rng->c_state = seed & 0xffffu; }}
int16_t myButton(void)
{{ host_intent("myButton", 0, 0, 0); return 0; }}
void f_00DF_015C(void) {{ host_intent("audio-driver-empty-015C", 0, 0, 0); }}
void f_00DF_0164(void) {{ host_intent("audio-driver-empty-0164", 0, 0, 0); }}
void EditMessage(void *message, int32_t ticks, int16_t mode)
{{ host_intent("EditMessage", message == NULL ? 0 : advice_id(message), ticks, mode); }}
void SetDefaultWindPrompt(int16_t mode)
{{ host_intent("SetDefaultWindPrompt", mode, 0, 0); EditMessage(NULL, -2, mode); }}
void ZapEuMapAt(int16_t plane, int16_t x, int16_t y)
{{ host_intent("ZapEuMapAt", plane, x, y); }}
void InvalEuMap(int16_t left, int16_t top, int16_t right, int16_t bottom)
{{ host_intent4("InvalEuMap", left, top, right, bottom); }}
void OverlayTileSet(int16_t a, int16_t b) {{ host_intent("OverlayTileSet", a, b, 0); }}
void PictStrnDialog(int16_t picture, int16_t object, int16_t force)
{{ host_intent("PictStrnDialog", picture, object, force); }}
void drawHistGraph(void) {{ host_intent("drawHistGraph", 0, 0, 0); }}
int16_t WinPrintf(const char *format, ...)
{{ host_intent("WinPrintf", format != NULL, 0, 0); return 0; }}
#define HOST_VOID(name) void name(void) {{ host_intent(#name, 0, 0, 0); }}
#define HOST_ZERO(name) int16_t name(void) {{ host_intent(#name, 0, 0, 0); return 0; }}
HOST_VOID(clip_Off)
HOST_VOID(clip_Pop)
HOST_VOID(clip_Push)
HOST_VOID(clip_SubInclude)
HOST_VOID(clip_SetWin)
HOST_VOID(UpdateEverything)
HOST_VOID(DoWinHelp)
HOST_VOID(DoEditUpdateDraw)
HOST_VOID(DrawSimPayoff)
HOST_VOID(InvalQueenStorageDisp)
HOST_ZERO(win_Events)
HOST_ZERO(win_IsWinInFront)
HOST_ZERO(StillDown)
HOST_ZERO(DialogAbortOrCont)
HOST_ZERO(MagnifyMenu)
#undef HOST_VOID
#undef HOST_ZERO
int16_t win_IsWinOpen(int16_t win)
{{ printf("QUERY:win_IsWinOpen:%d:closed\\n", win); return 0; }}
void DrawRectIntent(int16_t l, int16_t t, int16_t r, int16_t b, int16_t c)
{{ host_intent5("DrawRect", l, t, r, b, c); }}
void (*g_9134)(int16_t, int16_t, int16_t, int16_t, int16_t) = DrawRectIntent;
void (*g_916C)(int16_t, int16_t, int16_t, int16_t, int16_t) = DrawRectIntent;

static int song_done(void *context) {{ (void)context; return 1; }}

int main(void)
{{
    RecoveredState state;
    RecoveredBindingFrame state_frame;
    SimRng rng;
    SimRecoveredNestBinding nest_binding;
    SimNestRequest nest_request = {{{{0, 0}}, 2}};
    SimNestTrace nest_trace;
    SimRecoveredAudioBinding audio_binding;
    PortableAudioIntents audio_intents;
    if (!core_fixture_load(&state)) return 2;
    memset(&rng, 0, sizeof rng);
    rng.s_state = {int(row['s_rng_seed_before_tick'])};
    rng.c_state = 0x{int(row['original_c_rng_state_before_tick']):08x}u;
    core_rng = &rng;
    recovered_bind_begin(&state_frame, &state);
    recovered_rng_bind(&rng);
    memset(&nest_binding, 0, sizeof nest_binding);
    nest_binding.rng = &rng;
    nest_binding.request = &nest_request;
    nest_binding.trace = &nest_trace;
    sim_recovered_nest_bind(&nest_binding);
    portable_audio_intents_init(&audio_intents);
    memset(&audio_binding, 0, sizeof audio_binding);
    audio_binding.intents = &audio_intents;
    audio_binding.driver_ready = 0;
    audio_binding.song_done = song_done;
    sim_recovered_audio_bind(&audio_binding);
    for (unsigned i = 0; i < 32; ++i) {{
        snprintf(advice_text[i], sizeof advice_text[i], "msg-%u", i);
        advice_text_ptrs[i] = advice_text[i];
    }}
    AdviceStrs = advice_text_ptrs;
    printf("TICK_BEGIN:1\\n");
    DoAntSim();
    printf("TICK_END:1\\n");
    {consecutive_code}
    {{
        PortableAudioIntent intent;
        while (portable_audio_next_intent(&audio_intents, &intent))
            printf("AUDIO:%u:%d:%d:%d:%d\\n", (unsigned)intent.sequence,
                   (int)intent.kind, (int)intent.id, (int)intent.arg_a,
                   (int)intent.arg_b);
    }}
    sim_recovered_audio_unbind(&audio_binding);
    (void)sim_recovered_nest_unbind(&nest_binding);
    recovered_rng_bind(NULL);
    recovered_bind_end(&state_frame, &state);
    if (!core_fixture_compare{'_consecutive' if consecutive else ''}(&state)) return 3;
    if (rng.s_state != (uint16_t){int(row['s_rng_seed_after_consecutive_tick'] if consecutive else row['s_rng_seed_after_tick'])}) {{
        fprintf(stderr, "RNG_S_MISMATCH expected={int(row['s_rng_seed_after_consecutive_tick'] if consecutive else row['s_rng_seed_after_tick'])} actual=%u\\n", rng.s_state);
        return 4;
    }}
    if (rng.c_state != 0x{int(row['original_c_rng_state_after_consecutive_tick'] if consecutive else row['original_c_rng_state_after_tick']):08x}u) {{
        fprintf(stderr, "RNG_C_MISMATCH expected=0x{int(row['original_c_rng_state_after_consecutive_tick'] if consecutive else row['original_c_rng_state_after_tick']):08x} actual=0x%08x\\n", rng.c_state);
        return 5;
    }}
    printf("PASS native DoAntSim cycle={int(row['cycle_before_tick'])} rng_s=%u rng_c=%u\\n",
           rng.s_state, rng.c_state);
    return 0;
}}
'''


HOST_PROVIDER_NAMES = {
    "TickCount", "MacTickCount", "SetSRandSeed", "GetSRandSeed", "rand", "srand",
    "myButton", "f_00DF_015C",
    "f_00DF_0164", "EditMessage", "SetDefaultWindPrompt", "ZapEuMapAt",
    "InvalEuMap", "InvalQueenStorageDisp", "OverlayTileSet", "g_9134", "g_916C",
    "o25_3BA4_1035", "myBeginSong", "myBeginSound", "mySongIsDone", "mySoundIsDone",
}

def normalize_original_host_trace(events: list[dict]) -> list[tuple[str, list[int]]] | None:
    supported = {"MacTickCount", "TickCount", "ZapEuMapAt",
                 "SetDefaultWindPrompt", "EditMessage"}
    expected: list[tuple[str, list[int]]] = []
    for event in events:
        name = event["name"]
        if name not in supported:
            continue
        words = event["stack_words_at_entry"]
        if name in {"MacTickCount", "TickCount"}:
            args: list[int] = []
        elif name == "ZapEuMapAt":
            args = [int(value if value < 0x8000 else value - 0x10000)
                    for value in words[2:5]]
        elif name == "SetDefaultWindPrompt":
            value = words[2]
            args = [int(value if value < 0x8000 else value - 0x10000)]
        else:
            pointer = words[2] | (words[3] << 16)
            if pointer != 0:
                # Physical DOS addresses and native pointers are not comparable;
                # a future nonnull message needs an evidence-backed content ID.
                return None
            ticks = words[4] | (words[5] << 16)
            mode = words[6]
            if ticks & 0x80000000:
                ticks -= 0x100000000
            if mode & 0x8000:
                mode -= 0x10000
            args = [0, ticks, mode]
        expected.append((name, args))
    return expected


def create_fail_closed_stubs(symbols: list[str]) -> str:
    lines = ["#include <stdio.h>", "#include <stdlib.h>", ""]
    for name in symbols:
        lines += [
            f"void {name}(void)",
            "{",
            f'    fprintf(stderr, "UNSUPPORTED_UNBOUND_GAME_OR_HOST_CALL {name}\\n");',
            "    exit(77);",
            "}",
        ]
    return "\n".join(lines) + "\n"


def create_sequence_fixture_c(report: dict, fields: list[str], snapshot_path: Path) -> str:
    lines = [
        '#include "recovered_state.h"', "#include <stdio.h>",
        "#include <string.h>", "", "static FILE *snapshots;",
        "int core_fixture_open_snapshots(const char *path)", "{",
        "    snapshots = fopen(path, \"rb\"); return snapshots != NULL;", "}",
        "int core_fixture_load(RecoveredState *state)", "{",
        "    recovered_state_init(state);",
    ]
    arrays: list[str] = []
    for index, field in enumerate(fields):
        before = bytes.fromhex(report["pre_tick_ranges"][field])
        arrays.append(byte_array(f"before_{index}", before))
        lines += [
            f"    if (sizeof(state->{field}) != sizeof(before_{index})) return 0;",
            f"    memcpy(&state->{field}, before_{index}, sizeof(before_{index}));",
        ]
    total_bytes = report["source_global_bytes"]
    lines += [
        "    return 1;", "}",
        "int core_fixture_compare_tick(const RecoveredState *state, unsigned tick)", "{",
        "    int mismatches = 0;",
        f"    static unsigned char expected[{max(report['source_global_bytes'], 1)}];",
        f"    if (snapshots == NULL || fseek(snapshots, (long)(tick * {total_bytes}u), SEEK_SET) != 0) return 0;",
    ]
    for index, field in enumerate(fields):
        lines += [
            f"    if (fread(expected, 1, sizeof(state->{field}), snapshots) != sizeof(state->{field})) return 0;",
            f"    if (memcmp(&state->{field}, expected, sizeof(state->{field})) != 0) {{",
            f'        unsigned shown = 0; for (size_t j = 0; j < sizeof(state->{field}); ++j) if (((const unsigned char *)&state->{field})[j] != expected[j]) {{ if (shown < 8) fprintf(stderr, "STATE_MISMATCH tick=%u field={field} byte=%zu expected=%02x actual=%02x\\n", tick, j, expected[j], ((const unsigned char *)&state->{field})[j]); ++shown; }}',
            f'        fprintf(stderr, "STATE_FIELD_DIFF tick=%u field={field} differing_bytes=%u\\n", tick, shown); ++mismatches;', "    }",
        ]
    lines += ["    return mismatches == 0;", "}", ""]
    arrays.append(f'static const char snapshot_path[] = "{str(snapshot_path).replace(chr(92), "/")}";\n')
    return "".join(arrays) + "\n".join(lines).replace(
        "snapshots = fopen(path, \"rb\"); return snapshots != NULL;",
        "(void)path; snapshots = fopen(snapshot_path, \"rb\"); return snapshots != NULL;",
    )


def create_sequence_runtime_c(report: dict) -> str:
    tick_count = int(report["ticks"])
    expected_s = ",".join(str(int(row["s_rng"]) & 0xFFFF) for row in report["tick_records"])
    expected_c = ",".join(f"0x{int(row['c_rng']):08x}u" for row in report["tick_records"])
    return f'''#include "recovered_state.h"
#include "portable/game/recovered/nest_adapter.h"
#include "portable/game/recovered/audio_adapter.h"
#include "portable/game/simulation/rng.h"
#include "portable/game/recovered/memory_adapter.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int core_fixture_load(RecoveredState *state);
extern int core_fixture_open_snapshots(const char *path);
extern int core_fixture_compare_tick(const RecoveredState *state, unsigned tick);
extern void recovered_rng_bind(SimRng *rng);
extern void DoAntSim(void);
static const uint16_t expected_s[{tick_count}] = {{{expected_s}}};
static const uint32_t expected_c[{tick_count}] = {{{expected_c}}};
static SimRng *core_rng;
static char advice_text[32][16];
static void *advice_text_ptrs[32];
static void host_intent(const char *name, long a, long b, long c)
{{ printf("HOST:%s:%ld:%ld:%ld\\n", name, a, b, c); }}
static void host_intent4(const char *name,long a,long b,long c,long d)
{{ printf("HOST:%s:%ld:%ld:%ld:%ld\\n",name,a,b,c,d); }}
static void host_intent5(const char *name,long a,long b,long c,long d,long e)
{{ printf("HOST:%s:%ld:%ld:%ld:%ld:%ld\\n",name,a,b,c,d,e); }}
static long advice_id(void *message)
{{ for (unsigned i=0;i<32;++i) if (message==advice_text_ptrs[i]) return i; return -1; }}
int32_t TickCount(void) {{ host_intent("TickCount",0,0,0); return {int(report['source_tick_count'])}; }}
int32_t MacTickCount(void) {{ host_intent("MacTickCount",0,0,0); return TickCount()*3; }}
void SetSRandSeed(uint32_t seed) {{ sim_rng_set_s_seed(core_rng,(int16_t)seed); }}
uint32_t GetSRandSeed(void) {{ return sim_rng_get_s_seed(core_rng); }}
int rand(void) {{ return (int)sim_rng_msc_rand(core_rng); }}
void srand(unsigned seed) {{ core_rng->c_state=seed&0xffffu; }}
int16_t myButton(void) {{ host_intent("myButton",0,0,0); return 0; }}
void f_00DF_015C(void) {{ host_intent("audio-driver-empty-015C",0,0,0); }}
void f_00DF_0164(void) {{ host_intent("audio-driver-empty-0164",0,0,0); }}
void EditMessage(void *message,int32_t ticks,int16_t mode)
{{ host_intent("EditMessage",message==NULL?0:advice_id(message),ticks,mode); }}
void SetDefaultWindPrompt(int16_t mode)
{{ host_intent("SetDefaultWindPrompt",mode,0,0); EditMessage(NULL,-2,mode); }}
void ZapEuMapAt(int16_t plane,int16_t x,int16_t y)
{{ host_intent("ZapEuMapAt",plane,x,y); }}
void InvalEuMap(int16_t l,int16_t t,int16_t r,int16_t b) {{ host_intent4("InvalEuMap",l,t,r,b); }}
void OverlayTileSet(int16_t a,int16_t b) {{ host_intent("OverlayTileSet",a,b,0); }}
void PictStrnDialog(int16_t a,int16_t b,int16_t c) {{ host_intent("PictStrnDialog",a,b,c); }}
void drawHistGraph(void) {{ host_intent("drawHistGraph",0,0,0); }}
int16_t WinPrintf(const char *format,...) {{ host_intent("WinPrintf",format!=NULL,0,0); return 0; }}
int16_t win_IsWinOpen(int16_t win) {{ printf("QUERY:win_IsWinOpen:%d:closed\\n",win); return 0; }}
int16_t win_Events(void) {{ printf("QUERY:win_Events:0\\n"); return 0; }}
int16_t win_IsWinInFront(void) {{ printf("QUERY:win_IsWinInFront:0\\n"); return 0; }}
int16_t StillDown(void) {{ printf("QUERY:StillDown:0\\n"); return 0; }}
int16_t DialogAbortOrCont(void) {{ printf("QUERY:DialogAbortOrCont:0\\n"); return 0; }}
int16_t MagnifyMenu(void) {{ printf("QUERY:MagnifyMenu:0\\n"); return 0; }}
void clip_Off(void) {{ host_intent("clip_Off",0,0,0); }}
void clip_Pop(void) {{ host_intent("clip_Pop",0,0,0); }}
void clip_Push(void) {{ host_intent("clip_Push",0,0,0); }}
void clip_SubInclude(void) {{ host_intent("clip_SubInclude",0,0,0); }}
void clip_SetWin(int16_t win) {{ host_intent("clip_SetWin",win,0,0); }}
void UpdateEverything(void) {{ host_intent("UpdateEverything",0,0,0); }}
void DoWinHelp(int16_t topic) {{ host_intent("DoWinHelp",topic,0,0); }}
void DoEditUpdateDraw(void) {{ host_intent("DoEditUpdateDraw",0,0,0); }}
void DrawSimPayoff(void) {{ host_intent("DrawSimPayoff",0,0,0); }}
void InvalQueenStorageDisp(void) {{ host_intent("InvalQueenStorageDisp",0,0,0); }}
void DrawRectIntent(int16_t l,int16_t t,int16_t r,int16_t b,int16_t c)
{{ host_intent5("DrawRect",l,t,r,b,c); }}
void (*g_9134)(int16_t,int16_t,int16_t,int16_t,int16_t)=DrawRectIntent;
void (*g_916C)(int16_t,int16_t,int16_t,int16_t,int16_t)=DrawRectIntent;
static int song_done(void *context) {{ (void)context; return 1; }}
int main(int argc,char **argv)
{{
    (void)argc;(void)argv;
    RecoveredState state; RecoveredBindingFrame frame; SimRng rng={{0}};
    SimRecoveredNestBinding nest_binding={{0}}; SimNestRequest request={{{{0,0}},2}};
    SimNestTrace nest_trace; SimRecoveredAudioBinding audio_binding={{0}};
    PortableAudioIntents audio_intents;
    if (!core_fixture_open_snapshots(NULL) || !core_fixture_load(&state)) return 2;
    rng.s_state={int(report['initial_s_rng'])}; rng.c_state=0x{int(report['initial_c_rng']):08x}u;
    core_rng=&rng; recovered_bind_begin(&frame,&state); recovered_rng_bind(&rng);
    nest_binding.rng=&rng; nest_binding.request=&request; nest_binding.trace=&nest_trace;
    sim_recovered_nest_bind(&nest_binding); portable_audio_intents_init(&audio_intents);
    audio_binding.intents=&audio_intents; audio_binding.driver_ready=0; audio_binding.song_done=song_done;
    sim_recovered_audio_bind(&audio_binding);
    for (unsigned i=0;i<32;++i) {{ snprintf(advice_text[i],sizeof advice_text[i],"msg-%u",i); advice_text_ptrs[i]=advice_text[i]; }}
    AdviceStrs=advice_text_ptrs;
    for (unsigned tick=0;tick<{tick_count}u;++tick) {{
        printf("TICK_BEGIN:%u\\n",tick); DoAntSim(); printf("TICK_END:%u\\n",tick);
        recovered_bind_end(&frame,&state);
        if (!core_fixture_compare_tick(&state,tick)) return 3;
        if (rng.s_state!=expected_s[tick]) {{ fprintf(stderr,"S_RNG_MISMATCH tick=%u expected=%u actual=%u\\n",tick,expected_s[tick],rng.s_state); return 4; }}
        if (rng.c_state!=expected_c[tick]) {{ fprintf(stderr,"C_RNG_MISMATCH tick=%u expected=%08x actual=%08x\\n",tick,expected_c[tick],rng.c_state); return 5; }}
        if (tick+1<{tick_count}u) recovered_bind_begin(&frame,&state);
    }}
    sim_recovered_audio_unbind(&audio_binding); (void)sim_recovered_nest_unbind(&nest_binding);
    recovered_rng_bind(NULL);
    printf("SEQUENCE_STATE_RNG_PASS ticks={tick_count}\\n"); return 0;
}}
'''


def run_sequence_mode(report: dict) -> int:
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc is required")
    if report["recovered_state_header_sha256"] != hashlib.sha256(
            (GENERATED / "recovered_state.h").read_bytes()).hexdigest():
        print("sequence fixture schema hash is stale")
        return 2
    provenance_sha256 = hashlib.sha256((GENERATED / "provenance.json").read_bytes()).hexdigest()
    expected_provenance_sha256 = report.get("comparison_provenance_sha256",
                                           report.get("provenance_sha256"))
    if expected_provenance_sha256 != provenance_sha256:
        print("sequence fixture provenance hash is stale")
        return 2
    for row in report["tick_records"]:
        if any(call.get("normalization") for call in row["host_trace"]):
            print(f"UNSUPPORTED_HOST_TRACE tick={row['tick']} trace={row['host_trace']!r}")
            return 10

    scratch = SEQUENCE_SCRATCH
    scratch.mkdir(parents=True, exist_ok=True)
    compressed = ROOT / report["snapshot_file"]
    if hashlib.sha256(compressed.read_bytes()).hexdigest() != report["snapshot_sha256"]:
        print("original state snapshot hash mismatch")
        return 2
    raw_snapshot = scratch / "poststates.bin"
    with gzip.open(compressed, "rb") as source, raw_snapshot.open("wb") as destination:
        shutil.copyfileobj(source, destination)
    if raw_snapshot.stat().st_size != report["snapshot_uncompressed_bytes"]:
        print("original state snapshot byte count mismatch")
        return 2

    provenance = json.loads((GENERATED / "provenance.json").read_text(encoding="utf-8"))
    fixture_c = scratch / "fixture_sequence.c"
    fixture_c.write_text(create_sequence_fixture_c(
        report, report["source_globals"], raw_snapshot), encoding="utf-8")
    runtime_c = scratch / "tick_sequence_runtime.c"
    runtime_c.write_text(create_sequence_runtime_c(report), encoding="utf-8")
    compat = scratch / "compat.h"
    compat.write_text("typedef char **Handle;\n", encoding="utf-8")
    sources = [ROOT / module["generated"] for module in provenance["modules"]]
    sources += [
        ROOT / provenance["recovered_state"]["source_path"],
        ROOT / provenance["native_adapter_compile"]["path"],
        ROOT / "portable/game/simulation/rng.c",
        ROOT / "portable/game/simulation/movement.c",
        ROOT / "portable/game/simulation/nest.c",
        ROOT / "portable/game/state/world.c",
        ROOT / "portable/platform/memory.c",
        ROOT / "portable/game/recovered/memory_adapter.c",
        ROOT / "portable/game/recovered/nest_adapter.c",
        ROOT / "portable/game/recovered/audio_adapter.c",
        ROOT / "portable/audio/intent.c",
        fixture_c, runtime_c,
    ]
    objects = []
    for index, source in enumerate(sorted(set(sources))):
        output = scratch / f"obj-{index:02d}.o"
        result = run([
            compiler, "-std=c11", "-ffunction-sections", "-fdata-sections",
            f"-include{compat}", f"-I{ROOT}", f"-I{GENERATED}",
            f"-I{ROOT / 'portable'}", "-c", str(source), "-o", str(output),
        ], capture=True)
        if result.returncode:
            print(f"COMPILE_FAILURE {source}\n{result.stdout}")
            return result.returncode
        objects.append(output)
    exe = scratch / "native-sequence.exe"
    link = run([compiler, "-Wl,--gc-sections", *(str(obj) for obj in objects),
                "-o", str(exe)], capture=True)
    unresolved = sorted(set(re.findall("undefined reference to `([^']+)'", link.stdout or "")))
    if link.returncode:
        callable_unresolved = [name for name in unresolved if name not in HOST_PROVIDER_NAMES]
        stub_c = scratch / "fail_closed.c"
        stub_c.write_text(create_fail_closed_stubs(callable_unresolved), encoding="utf-8")
        stub_o = scratch / "fail_closed.o"
        result = run([compiler, "-std=c11", "-ffunction-sections", "-fdata-sections",
                      "-c", str(stub_c), "-o", str(stub_o)], capture=True)
        if result.returncode:
            print(result.stdout or "fail-closed stub compile failed")
            return result.returncode
        link = run([compiler, "-Wl,--gc-sections", *(str(obj) for obj in objects),
                    str(stub_o), "-o", str(exe)], capture=True)
        if link.returncode:
            print(f"LINK_FAILURE unresolved={unresolved}\n{link.stdout}")
            return link.returncode

    try:
        result = run([str(exe)], capture=True, timeout=10)
    except subprocess.TimeoutExpired as error:
        print(f"NATIVE_SEQUENCE_TIMEOUT after 10 seconds; output={error.stdout or ''}")
        return 124
    output = result.stdout or ""
    if result.returncode:
        print(output)
        print(f"NATIVE_SEQUENCE_EXIT {result.returncode}")
        return result.returncode

    target_names = {"MacTickCount", "TickCount", "ZapEuMapAt",
                    "SetDefaultWindPrompt", "EditMessage", "PictStrnDialog"}
    native_by_tick: dict[int, list[tuple[str, list[int]]]] = {}
    unknown_hosts: dict[int, list[str]] = {}
    queries: dict[int, list[int]] = {}
    current_tick = None
    for line in output.splitlines():
        begin = re.fullmatch(r"TICK_BEGIN:(\d+)", line)
        end = re.fullmatch(r"TICK_END:(\d+)", line)
        if begin:
            current_tick = int(begin.group(1))
            native_by_tick[current_tick] = []
            continue
        if end:
            current_tick = None
            continue
        query = re.fullmatch(r"QUERY:([^:]+):(?:(\d+):closed|(\d+))", line)
        if query and current_tick is not None:
            query_name = query.group(1)
            if query_name not in {"win_IsWinOpen", "win_Events", "win_IsWinInFront",
                                  "StillDown", "DialogAbortOrCont", "MagnifyMenu"}:
                print(f"UNKNOWN_QUERY_BOUNDARY tick={current_tick} event={line}")
                return 8
            if query_name == "win_IsWinOpen":
                queries.setdefault(current_tick, []).append(int(query.group(2)))
            continue
        event = re.fullmatch(r"HOST:(\w+):(.+)", line)
        if event and current_tick is not None:
            name = event.group(1)
            if name not in target_names:
                unknown_hosts.setdefault(current_tick, []).append(line)
                continue
            try:
                values = [int(value) for value in event.group(2).split(":")]
            except ValueError:
                print(f"INVALID_HOST_ARGUMENTS tick={current_tick} event={line}")
                return 8
            width = {"MacTickCount": 0, "TickCount": 0, "ZapEuMapAt": 3,
                     "SetDefaultWindPrompt": 1, "EditMessage": 3,
                     "PictStrnDialog": 3}[name]
            native_by_tick[current_tick].append((name, values[:width]))
    if unknown_hosts:
        tick = min(unknown_hosts)
        print(f"UNNORMALIZED_EFFECTFUL_HOST_CALL tick={tick} events={unknown_hosts[tick]!r}")
        return 6
    for row in report["tick_records"]:
        tick = int(row["tick"])
        expected = [(call["name"], call["args"]) for call in row["host_trace"]]
        actual = native_by_tick.get(tick, [])
        if actual != expected:
            print(f"HOST_TRACE_MISMATCH tick={tick} expected={expected!r} actual={actual!r}")
            return 7
        known_windows = {0, 0x100, 0x1500, 0x1900, 0x1902, 0x1A00, 0x1A01}
        if any(window not in known_windows for window in queries.get(tick, [])):
            print(f"WINDOW_QUERY_MISMATCH tick={tick} ids={queries.get(tick, [])!r}")
            return 8
    print(f"PASS native DOS differential ticks={report['ticks']} seed={report['seed']:#x} "
          f"scenario={report['scenario']} fields={report['source_global_count']} "
          f"state_bytes_per_tick={report['source_global_bytes']} "
          f"host_traces={len(report['tick_records'])} unresolved_failclosed={len(unresolved)}")
    return 0


def main() -> int:
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc is required")
    fixture_path = FIXTURE_PATH
    consecutive = False
    profile_arg: Path | None = None
    index = 2
    while index < len(sys.argv):
        if sys.argv[index] == "--consecutive":
            consecutive = True
            index += 1
        elif sys.argv[index] == "--fixture" and index + 1 < len(sys.argv):
            fixture_path = Path(sys.argv[index + 1])
            if not fixture_path.is_absolute():
                fixture_path = ROOT / fixture_path
            index += 2
        elif sys.argv[index] == "--profile" and index + 1 < len(sys.argv):
            profile_arg = Path(sys.argv[index + 1])
            index += 2
        else:
            raise SystemExit(f"unknown argument: {sys.argv[index]}")
    report = json.loads(fixture_path.read_text(encoding="utf-8"))
    profile_path = profile_arg
    if profile_path is None and report.get("generated_profile"):
        profile_path = Path(report["generated_profile"])
    if profile_path is None:
        profile_path = DEFAULT_GENERATED
    if not profile_path.is_absolute():
        profile_path = ROOT / profile_path
    profile_path = profile_path.resolve()
    global GENERATED, SCRATCH, SEQUENCE_SCRATCH
    GENERATED = profile_path
    if profile_path == (ROOT / "build/workers/recovered_source_next2/generated").resolve():
        SCRATCH = ROOT / "build/workers/core_proof_next2/native-cycle0"
        SEQUENCE_SCRATCH = ROOT / "build/workers/core_proof_next2/sequence-native"
    elif profile_path != DEFAULT_GENERATED.resolve():
        SCRATCH = ROOT / "build/workers/core_proof_next/native-cycle0"
        SEQUENCE_SCRATCH = ROOT / "build/workers/core_proof_next/sequence-native"
    else:
        SCRATCH = ROOT / "build/workers/core_proof/native-cycle0"
        SEQUENCE_SCRATCH = ROOT / "build/workers/core_proof/sequence-native"
    try:
        generated_profile = profile_path.relative_to(ROOT).as_posix()
    except ValueError:
        raise SystemExit("generated profile must be inside the workspace")
    expected_profile = report.get("comparison_profile", report.get("generated_profile"))
    if expected_profile and expected_profile != generated_profile:
        raise SystemExit("fixture profile does not match selected --profile")
    provenance = json.loads((GENERATED / "provenance.json").read_text(encoding="utf-8"))
    if report.get("schema") == "original-dos-consecutive-doantsim-v1":
        raise SystemExit("legacy fixture inferred C RNG state; recapture with original_256_tick_probe.py")
    if report.get("schema") == "original-dos-consecutive-doantsim-v2":
        return run_sequence_mode(report)
    header_hash = hashlib.sha256((GENERATED / "recovered_state.h").read_bytes()).hexdigest()
    if report["recovered_state_header_sha256"] != header_hash:
        raise SystemExit("fixture schema hash is stale; regenerate original_tick_probe.py")
    cycle = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0
    row = next(item for item in report["cycles"] if item["cycle_before_tick"] == cycle)
    fields = report["cycles"][0]["recovered_source_globals"]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    compat = SCRATCH / "compat.h"
    compat.write_text("typedef char **Handle;\n", encoding="utf-8")
    fixture_c = SCRATCH / "fixture_state.c"
    fixture_c.write_text(create_fixture_c(row, fields), encoding="utf-8")
    runtime_c = SCRATCH / "tick_runtime.c"
    runtime_c.write_text(create_runtime_c(row, consecutive), encoding="utf-8")

    sources = [ROOT / module["generated"] for module in provenance["modules"]]
    sources += [
        ROOT / provenance["recovered_state"]["source_path"],
        ROOT / provenance["native_adapter_compile"]["path"],
        ROOT / "portable/game/simulation/rng.c",
        ROOT / "portable/game/simulation/movement.c",
        ROOT / "portable/game/simulation/nest.c",
        ROOT / "portable/game/state/world.c",
        ROOT / "portable/platform/memory.c",
        ROOT / "portable/game/recovered/memory_adapter.c",
        ROOT / "portable/game/recovered/nest_adapter.c",
        ROOT / "portable/game/recovered/audio_adapter.c",
        ROOT / "portable/audio/intent.c",
        fixture_c,
        runtime_c,
    ]
    objects: list[Path] = []
    for index, source in enumerate(sorted(set(sources))):
        output = SCRATCH / f"obj-{index:02d}.o"
        result = run([
            compiler, "-std=c11", "-ffunction-sections", "-fdata-sections",
            f"-include{compat}", f"-I{ROOT}", f"-I{GENERATED}", f"-I{ROOT / 'portable'}",
            "-c", str(source), "-o", str(output),
        ], capture=True)
        if result.returncode:
            print(f"COMPILE_FAILURE {source}\n{result.stdout}")
            return result.returncode
        objects.append(output)

    exe = SCRATCH / "native-tick.exe"
    first_link = run([compiler, "-Wl,--gc-sections", *(str(p) for p in objects), "-o", str(exe)], capture=True)
    unresolved = sorted(set(re.findall("undefined reference to `([^']+)'", first_link.stdout or "")))
    if first_link.returncode:
        callable_unresolved = [name for name in unresolved if name not in HOST_PROVIDER_NAMES]
        stub_c = SCRATCH / "fail_closed.c"
        stub_c.write_text(create_fail_closed_stubs(callable_unresolved), encoding="utf-8")
        stub_o = SCRATCH / "fail_closed.o"
        result = run([
            compiler, "-std=c11", "-ffunction-sections", "-fdata-sections",
            "-c", str(stub_c), "-o", str(stub_o),
        ], capture=True)
        if result.returncode:
            print(result.stdout or "fail-closed stubs did not compile")
            return result.returncode
        objects.append(stub_o)
        second_link = run([compiler, "-Wl,--gc-sections", *(str(p) for p in objects), "-o", str(exe)], capture=True)
        if second_link.returncode:
            print(f"LINK_FAILURE unresolved={unresolved}\n{second_link.stdout}")
            return second_link.returncode
    print(f"linked generated tick with {len(unresolved)} fail-closed unresolved references")
    try:
        result = run([str(exe)], capture=True, timeout=10)
    except subprocess.TimeoutExpired as error:
        print(f"NATIVE_TICK_TIMEOUT after 10 seconds; output={error.stdout or ''}")
        return 124
    output = result.stdout or ""
    print(output)
    print(f"native tick exit={result.returncode}")
    if result.returncode:
        return result.returncode
    expected_ticks = [normalize_original_host_trace(row.get("host_entry_stack", []))]
    if consecutive:
        expected_ticks.append(normalize_original_host_trace(
            row.get("consecutive_host_entry_stack", [])))
    if any(expected_tick is None for expected_tick in expected_ticks):
        print("UNSUPPORTED_HOST_POINTER: nonnull DOS message requires content normalization")
        return 10
    actual_ticks: dict[int, list[tuple[str, list[int]]]] = {}
    window_queries: list[int] = []
    active_tick = 0
    for line in output.splitlines():
        begin = re.fullmatch(r"TICK_BEGIN:(\d+)", line)
        end = re.fullmatch(r"TICK_END:(\d+)", line)
        if begin:
            active_tick = int(begin.group(1))
            actual_ticks[active_tick] = []
            continue
        if end:
            active_tick = 0
            continue
        query = re.fullmatch(r"QUERY:win_IsWinOpen:(\d+):closed", line)
        if query:
            window_queries.append(int(query.group(1)))
        match = re.fullmatch(r"HOST:(\w+):(-?\d+):(-?\d+):(-?\d+)", line)
        if match and match.group(1) in {"MacTickCount", "TickCount", "ZapEuMapAt",
                                      "SetDefaultWindPrompt", "EditMessage"}:
            name = match.group(1)
            values = [int(match.group(i)) for i in (2, 3, 4)]
            width = {"MacTickCount": 0, "TickCount": 0, "ZapEuMapAt": 3,
                     "SetDefaultWindPrompt": 1, "EditMessage": 3}[name]
            actual_ticks.setdefault(active_tick, []).append((name, values[:width]))
    for index, expected in enumerate(expected_ticks, start=1):
        actual = actual_ticks.get(index, [])
        if actual != expected:
            print(f"HOST_TRACE_MISMATCH tick={index} expected={expected!r} actual={actual!r}")
            return 6
    if any(window != 0x1500 for window in window_queries):
        print(f"WINDOW_QUERY_MISMATCH expected only closed-window ID 0x1500 actual={window_queries!r}")
        return 7
    effectful_history = [line for line in output.splitlines()
                         if line.startswith(("HOST:drawHistGraph:", "HOST:DrawRect:", "HOST:PictStrnDialog:"))]
    if effectful_history:
        print(f"UNEXPECTED_HISTORY_UI_INTENT {effectful_history!r}")
        return 9
    suffix = " plus consecutive tick state/RNG and host trace" if consecutive else ""
    print(f"PASS exact DOS host boundary trace cycle={cycle}{suffix}: {actual_ticks}; "
          f"pure closed-window query IDs={window_queries}; no history draw/dialog intent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
