#ifndef SOURCE_CONTROL_EVENTS_H
#define SOURCE_CONTROL_EVENTS_H

#include <stdint.h>

/* Test-only fixed-width projection of the globals touched by root:m0798.c.
 * A fixture owns one instance for one event invocation, then copies only the
 * source-owned fields back to its comparison record. */
typedef struct SourceCtlResult {
    int16_t automatic, selector, percent;
    uint16_t current[3], presets[12];
    int16_t ideal_caste[4], point[2];
    int event_count;
    int32_t events[64][9];
} SourceCtlResult;

struct Rect { int16_t left, top, right, bottom; };
struct Pt { int16_t x, y; };
struct TriPoints { int16_t apexX, apexY, leftX, leftY, rightX, rightY; };
struct TriLevel { uint16_t frac, mid, weight; };
struct CtlMsg { uint8_t pad[8]; struct Pt pt; int16_t code; };
_Static_assert(sizeof(struct TriLevel)==6,"DOS TriLevel is three 16-bit words");
_Static_assert(sizeof(struct Pt)==4,"DOS Pt is two 16-bit words");
_Static_assert(sizeof(struct Rect)==8,"DOS Rect is four 16-bit words");
_Static_assert(sizeof(struct CtlMsg)==14,"DOS event record is 8-byte prefix plus point/code");

extern int16_t ModeAuto, CasteAuto, g_1B4E, g_1B50, g_1B62, g_1B64;
extern struct TriLevel modeLevels, casteLevels;
extern struct TriLevel fd_3D57_0810[4], fd_3D57_07F2[4];
extern struct TriPoints fd_50F6_3816, fd_50F6_3822;
extern struct Pt fd_50F6_0358, fd_50F6_022E;
extern uint16_t triWidth, triWidthL, triHeight;
extern int16_t IdealCaste[4];

void ProcCasteEvent(struct CtlMsg *msg);
void ProcModeEvent(struct CtlMsg *msg);
int16_t IsPointInIsoTri(struct Pt *pt, struct Rect *r);
void BoundPointToTri(struct Pt *pt, struct Rect *r);
void GetTriLatDist(struct TriLevel *level, struct TriPoints *tri, struct Pt *pt);
void SetTriLatPoint(struct TriLevel *level, struct TriPoints *tri, struct Pt *out);
void cvtLevels2IdealCaste(int16_t *ideal);
void clip_SetWin(int16_t id);
void clip_Off(void);
void DoWinHelp(int16_t id);
void win_MakeGroupInvisible(int16_t win, int16_t group);
void win_MakeGroupVisible(int16_t win, int16_t group);
void win_MakeObjSelected(int16_t id);
void win_GetObjRect(int16_t id, struct Rect *r);
void win_DrawCasteWindow(int16_t flags);
void win_DrawModeWindow(int16_t flags);
int16_t _fmemcmp(const void *a, const void *b, uint16_t n);
void *_fmemcpy(void *d, const void *s, uint16_t n);
void f_1FD2_04D0(struct Pt *pt);
int16_t StillDown(void);

/* kind: 0=mode, 1=caste. rect[4], metrics[3], initial point, control point,
 * then staged cursor samples exactly as in dos-control-events.json. */
int source_control_event_run(int kind, uint16_t code, int16_t start_auto,
    int16_t start_selector, int16_t start_percent,
    const int16_t rect[4], const uint16_t metrics[3],
    const int16_t initial_point[2], const int16_t control_point[2],
    const int16_t *samples, int sample_count, SourceCtlResult *result);

#endif
