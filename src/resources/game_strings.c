/*
 * Loads startup resources and prepares game string lists. It provides the resource string lookup
 * used by the interface and simulation messages.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 075B; complete original translation unit.
 * Windows: SIMONE, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 */

#include "strings_ids.h"

typedef char far * far *Handle;
typedef char far * far *StrList;

void far PrepareStrings(void);
extern Handle far db_LoadObject(int object, int kind);
extern void far WinPrintf(char far *format, ...);
extern void far app_cleanup_and_exit(char far *message, int code);
extern void far FlipHandleWords(Handle h);
extern char far * far fd_50F6_0B22;
void far f_075B_00A6(void);
extern void far f_00F8_02E7(void);
extern void far OverlayOutsideTiles(void);
extern int far f_00F8_02EF(void);
extern void far InitSimVars(void);
extern void far SeedSRand(void);
extern void far SeedRRand(void);
extern void far SetSimCursor(int cursor);

void far initStuff(void)
{
    Handle handle;
    int resourceError;

    PrepareStrings();
    handle = db_LoadObject(1000, 9);
    if (handle == 0) {
        WinPrintf("Cannot GetResource (HEX, %d), ResErr %d\n", 1000, resourceError);
        app_cleanup_and_exit("MemDeath", 0);
    }
    FlipHandleWords(handle);
    fd_50F6_0B22 = *handle;
    f_075B_00A6();
    f_00F8_02E7();
    OverlayOutsideTiles();
    if (f_00F8_02EF() == 0) {
        InitSimVars();
        SeedSRand();
        SeedRRand();
    }
    SetSimCursor(0);
}

void far f_075B_00A6(void)
{
}

StrList far LoadStringAnt(int object);
extern StrList far MwinTitle;
extern StrList far ScenarioNameStrs;
extern StrList far WindPromptStrs;
extern StrList far AdviceStrs;
extern StrList far HistGraphStrs;
extern StrList far EggStr;
extern StrList far CasteStr;
extern StrList far ModeStr;
extern StrList far LoadStr;
extern StrList far BoyMsgs;
extern StrList far SpiderMsgs;
extern StrList far BFightMsgs;
extern StrList far RFightMsgs;
extern StrList far EggMsgs;
extern StrList far QueenMsgs;
extern StrList far RestMsgs;
extern StrList far EndGameRatingStrs;
extern StrList far MiscStrs;

void far PrepareStrings(void)
{
    MwinTitle = LoadStringAnt(STR_WINDOW_TITLES);
    ScenarioNameStrs = LoadStringAnt(STR_SCENARIO_NAMES);
    WindPromptStrs = LoadStringAnt(STR_WINDOW_PROMPTS);
    AdviceStrs = LoadStringAnt(STR_ADVICE);
    HistGraphStrs = LoadStringAnt(STR_HISTORY_GRAPH_LABELS);
    EggStr = LoadStringAnt(STR_EGG_STAGES);
    CasteStr = LoadStringAnt(STR_CASTE_NAMES);
    ModeStr = LoadStringAnt(STR_ACTIVITY_NAMES);
    LoadStr = LoadStringAnt(STR_CARRIED_LOAD_NAMES);
    BoyMsgs = LoadStringAnt(STR_HUMAN_BALLOONS);
    SpiderMsgs = LoadStringAnt(STR_SPIDER_BALLOONS);
    BFightMsgs = LoadStringAnt(STR_BLACK_FIGHT_BALLOONS);
    RFightMsgs = LoadStringAnt(STR_RED_FIGHT_BALLOONS);
    EggMsgs = LoadStringAnt(STR_EGG_BALLOONS);
    QueenMsgs = LoadStringAnt(STR_QUEEN_BALLOONS);
    RestMsgs = LoadStringAnt(STR_REST_BALLOONS);
    EndGameRatingStrs = LoadStringAnt(STR_END_GAME_RATINGS);
    MiscStrs = LoadStringAnt(STR_MISCELLANEOUS);
}

extern Handle far mem_Alloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern void far * far _fmemmove(void far *dst, void far *src, unsigned n);

StrList far LoadStringAnt(int object)
{
    Handle h;
    unsigned char far *p;
    int count;
    StrList list;
    int i;
    int len;

    h = db_LoadObject(object, 4);
    if (h == 0) {
        WinPrintf("\n\aWarning: Can't load strings: %d", object);
        return 0;
    }
    p = (unsigned char far *)*h + 1;
    count = *p++;
    list = (StrList)mem_Lock(mem_Alloc((long)(count + 1) << 2, 0, "strptrs"));
    for (i = 0; i < count; i++) {
        list[i] = p;
        len = *p;
        _fmemmove(p, p + 1, len);
        p[len] = 0;
        p += len + 1;
    }
    list[i] = 0;
    return list;
}

void far f_075B_0334(void)
{
}
