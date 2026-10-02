#include "recovered_state.h"
#include <stdint.h>
#include <stddef.h>
#include <string.h>

static int16_t rects[2][4];
static int16_t bitmap_wh[2];
static int32_t trace[64];
static size_t trace_count;
/* Source m0798 translation-unit statics, injected as test initial state. */
static int16_t g_1B50;
static int16_t g_1B4E;
static size_t complement_changes;

static size_t check_controls_write_set(const RecoveredState *before,
                                       const RecoveredState *after)
{
    uint8_t allowed[sizeof(RecoveredState)] = {0};
    const uint8_t *a = (const uint8_t *)before;
    const uint8_t *b = (const uint8_t *)after;
    size_t i, n = 0;
#define ALLOW(field) memset(allowed + offsetof(RecoveredState, field), 1, sizeof(after->field))
#define ALLOW_N(field, bytes) memset(allowed + offsetof(RecoveredState, field), 1, (bytes))
    ALLOW(knobSize); ALLOW(ModeAuto); ALLOW(CasteAuto);
    ALLOW(fd_50F6_0468); ALLOW(fd_3D57_07EA);
    ALLOW(fd_50F6_0370); ALLOW(fd_50F6_024E);
    ALLOW_N(modeLevels, 3 * sizeof(uint16_t));
    ALLOW_N(casteLevels, 3 * sizeof(uint16_t));
    ALLOW_N(fd_3D57_0810, 3 * sizeof(uint16_t));
    ALLOW_N(fd_3D57_07F2, 3 * sizeof(uint16_t));
    ALLOW(IdealCaste); ALLOW(triWidth); ALLOW(triWidthL); ALLOW(triWidthR);
    ALLOW(triHeight); ALLOW(fd_50F6_382E); ALLOW(fd_50F6_3816); ALLOW(fd_50F6_3822);
    ALLOW(fd_50F6_0358); ALLOW(fd_50F6_022E);
#undef ALLOW_N
#undef ALLOW
    for (i = 0; i < sizeof(RecoveredState); ++i)
        if (!allowed[i] && a[i] != b[i]) ++n;
    return n;
}

void win_GetObjRect(int16_t id, struct Rect *r)
{
    trace[trace_count++] = 0x20000 | (uint16_t)id;
    const int16_t *v = (id == 0x130d) ? rects[1] : rects[0];
    r->left=v[0]; r->top=v[1]; r->right=v[2]; r->bottom=v[3];
}
void f_208F_0419(struct Pt *size, int16_t id)
{
    if (id != 0x578) return;
    trace[trace_count++] = 0x10000 | ((int32_t)(uint16_t)id << 8) | 2;
    size->x=bitmap_wh[0]; size->y=bitmap_wh[1];
}
void hanim_RemoveAnimSet(void *handle)
{
    trace[trace_count++] = handle == NULL ? 0x40000 : 0x40001;
}
void InitTriVars(int16_t obj, struct TriPoints *tri);
void SetTriLatPoint(uint16_t *level, struct TriPoints *tri, struct Pt *out);
void cvtLevels2IdealCaste(int16_t *ideal);
void win_ModeControlChanged(void);
void win_CasteControlChanged(void);
void win_ModeControlClosed(void);
void win_CasteControlClosed(void);
void initControls(void);

static void call_controls(RecoveredState *s)
{
    RecoveredBindingFrame frame;
    recovered_bind_begin(&frame,s);
    initControls();
    recovered_bind_end(&frame,s);
}

__declspec(dllexport) int controls_next4_run(const int16_t *r, const int16_t *wh,
                                               const int32_t *mut, int32_t *out,
                                               int32_t *events, size_t event_cap)
{
    RecoveredState s;
    RecoveredState before;
    size_t i=0, at=0;
    if (!r || !wh || !mut || !out || !events) return -1;
    memcpy(rects,r,sizeof(rects)); memcpy(bitmap_wh,wh,sizeof(bitmap_wh));
    trace_count=0;
    g_1B50=(int16_t)mut[6]; g_1B4E=(int16_t)mut[7];
    recovered_state_init(&s);
    before=s;
    call_controls(&s);
    complement_changes=check_controls_write_set(&before,&s);
    if (complement_changes) return -2;
    s.fd_3D57_080A[0]=(uint16_t)mut[0]; s.fd_3D57_080A[1]=(uint16_t)mut[1]; s.fd_3D57_080A[2]=(uint16_t)mut[2];
    s.fd_3D57_07EC[0]=(uint16_t)mut[3]; s.fd_3D57_07EC[1]=(uint16_t)mut[4]; s.fd_3D57_07EC[2]=(uint16_t)mut[5];
    for(i=0;i<9;i++) s.fd_3D57_0810[3+i]=(uint16_t)mut[8+i];
    for(i=0;i<9;i++) s.fd_3D57_07F2[3+i]=(uint16_t)mut[17+i];
    before=s;
    call_controls(&s);
    complement_changes=check_controls_write_set(&before,&s);
    if (complement_changes) return -2;
#define P(v) do { out[at++]=(int32_t)(v); } while(0)
    P(s.knobSize.x); P(s.knobSize.y);
    P(s.ModeAuto); P(s.CasteAuto); P(s.fd_50F6_0468); P(s.fd_3D57_07EA); P(g_1B50); P(g_1B4E); P(s.fd_50F6_0370); P(s.fd_50F6_024E);
    for(i=0;i<3;i++) P(s.modeLevels[i]);
    for(i=0;i<3;i++) P(s.casteLevels[i]);
    for(i=0;i<12;i++) P(s.fd_3D57_0810[i]);
    for(i=0;i<12;i++) P(s.fd_3D57_07F2[i]);
    for(i=0;i<4;i++) P(s.IdealCaste[i]);
    P(s.triWidth); P(s.triHeight); P(s.fd_50F6_382E);
    P(s.fd_50F6_3816.apexX); P(s.fd_50F6_3816.apexY); P(s.fd_50F6_3816.leftX); P(s.fd_50F6_3816.leftY); P(s.fd_50F6_3816.rightX); P(s.fd_50F6_3816.rightY);
    P(s.fd_50F6_3822.apexX); P(s.fd_50F6_3822.apexY); P(s.fd_50F6_3822.leftX); P(s.fd_50F6_3822.leftY); P(s.fd_50F6_3822.rightX); P(s.fd_50F6_3822.rightY);
    P(s.fd_50F6_0358.x); P(s.fd_50F6_0358.y); P(s.fd_50F6_022E.x); P(s.fd_50F6_022E.y);
#undef P
    for(i=0;i<trace_count && i<event_cap;i++) events[i]=trace[i];
    return (int)at;
}
__declspec(dllexport) size_t controls_next4_trace_count(void) { return trace_count; }
__declspec(dllexport) size_t controls_next4_complement_changes(void) { return complement_changes; }
