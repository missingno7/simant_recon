#include "engine.h"
#include "../../ui_model/windows/game_view.h"

#include <setjmp.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern void DoAntSim(void);
extern void recovered_bind_begin(RecoveredBindingFrame *frame,
                                const RecoveredState *state);
extern void recovered_bind_end(RecoveredBindingFrame *frame,
                              RecoveredState *state);
extern void recovered_rng_bind(SimRng *rng);
extern void recovered_keyboard_set_modifiers(uint8_t dos_flags);
extern void SetPause(int16_t pause);
extern void SetMapPlane(int16_t plane);
extern void SetMenuEntries(void);
extern int16_t YellowCommandKey(int16_t key);

static _Thread_local SimRecoveredEngine *active_engine;
static _Thread_local jmp_buf *active_abort_target;
static void bind_dos_keyboard_flags(void);
static int host_nest_event(void *context, const SimNestEvent *event);

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
};
_Static_assert(sizeof(struct Event) == sizeof(SimRecoveredEvent),
               "native event layout must match source Event");
extern void processEdit(struct Event *event);

static void interrupt_tick(SimRecoveredEngineStatus status,
                           const char *service)
{
    if (active_engine == NULL || active_abort_target == NULL)
        abort();
    active_engine->status = status;
    active_engine->failed_service = service;
    longjmp(*active_abort_target, 1);
}

static int32_t host_tick_count(void)
{
    int32_t value;
    if (active_engine == NULL || active_engine->host.tick_count == NULL ||
        !active_engine->host.tick_count(active_engine->host.context, &value))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, "TickCount");
    return value;
}

static int nest_host_tick_count(void *context, int32_t *value)
{
    SimRecoveredEngine *engine = context;
    if (engine == NULL || engine != active_engine || value == NULL)
        return 0;
    *value = host_tick_count();
    return 1;
}

/* A nonnull request is the controlled/static headless lane. A null request
 * makes EnterNest ask the same host clock lazily at its source call sites. */
static int prepare_nest_clock(SimRecoveredEngine *engine,
                              const SimNestRequest *request)
{
    if (request != NULL) {
        if (request->tick_count != 2)
            return 0;
        engine->nest_request = *request;
        engine->nest_binding.tick_count_provider = NULL;
        engine->nest_binding.tick_count_context = NULL;
    } else {
        memset(&engine->nest_request, 0, sizeof(engine->nest_request));
        engine->nest_binding.tick_count_provider = nest_host_tick_count;
        engine->nest_binding.tick_count_context = engine;
    }
    engine->nest_binding.rng = &engine->session->rng;
    engine->nest_binding.request = &engine->nest_request;
    engine->nest_binding.trace = &engine->nest_trace;
    engine->nest_binding.event_sink = host_nest_event;
    engine->nest_binding.event_context = engine;
    return 1;
}

static int32_t host_query(SimRecoveredQuery query,
                          const uintptr_t *arguments, uint8_t argument_count,
                          const char *service)
{
    int32_t value;
    if (active_engine == NULL || active_engine->host.query == NULL ||
        !active_engine->host.query(active_engine->host.context, query,
                                   arguments, argument_count, &value))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, service);
    return value;
}

static void unsupported_call(const char *name);
struct Event;
struct Rect;

static void host_effect(SimRecoveredEffectKind kind, uintptr_t a,
                        uintptr_t b, uintptr_t c, const char *service)
{
    SimRecoveredEffect effect;
    effect.kind = kind;
    effect.arguments[0] = a;
    effect.arguments[1] = b;
    effect.arguments[2] = c;
    effect.arguments[3] = 0;
    effect.arguments[4] = 0;
    if (active_engine == NULL || active_engine->host.effect == NULL ||
        !active_engine->host.effect(active_engine->host.context, &effect))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, service);
}

static int host_nest_event(void *context, const SimNestEvent *event)
{
    SimRecoveredEngine *engine = context;
    SimRecoveredEffect effect;
    switch ((SimNestEventKind)event->kind) {
    case SIM_NEST_SONG:
        if (event->argument_count < 2 ||
            !portable_audio_begin_song(&engine->audio_intents,
                (int16_t)event->arguments[0],
                (int16_t)event->arguments[1]))
            interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED,
                           "nest song intent");
        break;
    case SIM_NEST_SOUND:
        if (event->argument_count < 3 ||
            !portable_audio_begin_sound(&engine->audio_intents,
                (int16_t)event->arguments[0],
                (int16_t)event->arguments[1],
                (int16_t)event->arguments[2]))
            interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED,
                           "nest sound intent");
        break;
    case SIM_NEST_MAP_INVALIDATE:
        if (event->argument_count < 4)
            interrupt_tick(SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL,
                           "nest map invalidation trace shape");
        effect.kind = SIM_RECOVERED_EFFECT_NEST_MAP_INVALIDATE;
        effect.arguments[0] = (uintptr_t)(intptr_t)event->arguments[0];
        effect.arguments[1] = (uintptr_t)(intptr_t)event->arguments[1];
        effect.arguments[2] = (uintptr_t)(intptr_t)event->arguments[2];
        effect.arguments[3] = (uintptr_t)(intptr_t)event->arguments[3];
        effect.arguments[4] = 0;
        if (!engine->host.effect(engine->host.context, &effect))
            interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED,
                           "nest map invalidation");
        break;
    case SIM_NEST_ALARM_SELECTION:
        if (event->argument_count < 2)
            interrupt_tick(SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL,
                           "nest alarm selection trace shape");
        effect.kind = SIM_RECOVERED_EFFECT_ALARM_SELECTION;
        effect.arguments[0] = (uintptr_t)(intptr_t)event->arguments[0];
        effect.arguments[1] = (uintptr_t)(intptr_t)event->arguments[1];
        effect.arguments[2] = 0;
        effect.arguments[3] = 0;
        effect.arguments[4] = 0;
        if (!engine->host.effect(engine->host.context, &effect))
            interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED,
                           "nest alarm selection");
        break;
    default:
        /* Other entries describe source-internal state/RNG operations. */
        break;
    }
    return 1;
}

int32_t TickCount(void)
{
    return host_tick_count();
}

int32_t MacTickCount(void)
{
    /* The source platform helper is TickCount()*3. Use unsigned arithmetic to
     * preserve the source 32-bit wrap without signed-overflow undefinedness. */
    return (int32_t)((uint32_t)host_tick_count() * UINT32_C(3));
}

void ZapEuMapAt(int16_t plane, int16_t x, int16_t y)
{
    host_effect(SIM_RECOVERED_EFFECT_MAP_CELL_INVALIDATE,
                (uintptr_t)(intptr_t)plane, (uintptr_t)(intptr_t)x,
                (uintptr_t)(intptr_t)y, "ZapEuMapAt");
}

void EditMessage(void *message, int32_t ticks, int16_t mode)
{
    SimRecoveredEffect effect;
    effect.kind = SIM_RECOVERED_EFFECT_EDIT_MESSAGE;
    effect.arguments[0] = (uintptr_t)message;
    effect.arguments[1] = (uintptr_t)(intptr_t)ticks;
    effect.arguments[2] = (uintptr_t)(intptr_t)mode;
    effect.arguments[3] = 0;
    effect.arguments[4] = 0;
    if (active_engine == NULL || active_engine->host.effect == NULL ||
        !active_engine->host.effect(active_engine->host.context, &effect))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, "EditMessage");
}

void SetDefaultWindPrompt(int16_t mode)
{
    int16_t string_slot;
    void *message = NULL;
    SimRecoveredEffect effect;
    if (fd_50F6_047E == 0) {
        string_slot = -1; /* source passes a null text pointer */
    } else if (fd_50F6_105E == -1) {
        string_slot = 2;
    } else if (fd_50F6_105E == 10) {
        string_slot = 3;
    } else if (fd_50F6_105E == 11) {
        string_slot = 17;
    } else {
        return; /* The source routine has no effect for other modal states. */
    }
    if (string_slot >= 0) {
        if (fd_50F6_034C == NULL || fd_50F6_034C[string_slot] == NULL)
            interrupt_tick(SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL,
                           "SetDefaultWindPrompt advice slot unavailable");
        message = fd_50F6_034C[string_slot];
    }
    effect.kind = SIM_RECOVERED_EFFECT_DEFAULT_WIND_PROMPT;
    effect.arguments[0] = (uintptr_t)message;
    effect.arguments[1] = (uintptr_t)(intptr_t)-2;
    effect.arguments[2] = (uintptr_t)(intptr_t)mode;
    effect.arguments[3] = (uintptr_t)(intptr_t)string_slot;
    effect.arguments[4] = (uintptr_t)(intptr_t)fd_50F6_105E;
    if (active_engine == NULL || active_engine->host.effect == NULL ||
        !active_engine->host.effect(active_engine->host.context, &effect))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED,
                       "SetDefaultWindPrompt");
}

void PictStrnDialog(int16_t picture, int16_t string_id, int16_t force)
{
    host_effect(SIM_RECOVERED_EFFECT_PICTURE_STRING_DIALOG,
                (uintptr_t)(intptr_t)picture,
                (uintptr_t)(intptr_t)string_id,
                (uintptr_t)(intptr_t)force, "PictStrnDialog");
}

int16_t win_IsWinOpen(int16_t window)
{
    const uintptr_t args[] = { (uintptr_t)(intptr_t)window };
    return (int16_t)host_query(SIM_RECOVERED_QUERY_WINDOW_OPEN, args, 1,
                               "win_IsWinOpen");
}

int16_t win_Events(void)
{
    return (int16_t)host_query(SIM_RECOVERED_QUERY_WINDOW_EVENTS, NULL, 0,
                               "win_Events");
}

int16_t win_IsWinInFront(int16_t window)
{
    const uintptr_t args[] = { (uintptr_t)(intptr_t)window };
    return (int16_t)host_query(SIM_RECOVERED_QUERY_WINDOW_IN_FRONT, args, 1,
                               "win_IsWinInFront");
}

int16_t StillDown(void)
{
    return (int16_t)host_query(SIM_RECOVERED_QUERY_STILL_DOWN, NULL, 0,
                               "StillDown");
}

int16_t DialogAbortOrCont(void)
{
    return (int16_t)host_query(SIM_RECOVERED_QUERY_DIALOG_ABORT_OR_CONTINUE,
                               NULL, 0, "DialogAbortOrCont");
}

int16_t myButton(void)
{
    /* The original helper runs f_0000_046F before sampling StillDown. The
     * platform query owns that input-polling boundary and returns its result. */
    return (int16_t)host_query(SIM_RECOVERED_QUERY_BUTTON, NULL, 0,
                               "myButton");
}

int16_t win_GetEvent(struct Event *event)
{
    const uintptr_t args[] = { (uintptr_t)event };
    return (int16_t)host_query(SIM_RECOVERED_QUERY_GET_EVENT, args, 1,
                               "win_GetEvent");
}

void win_GetObjRect(int16_t object, struct Rect *rect)
{
    const uintptr_t args[] = {
        (uintptr_t)(intptr_t)object, (uintptr_t)rect
    };
    (void)host_query(SIM_RECOVERED_QUERY_GET_OBJECT_RECT, args, 2,
                     "win_GetObjRect");
}

static void window_operation(SimRecoveredWindowOperation operation,
                            uintptr_t a, uintptr_t b, uintptr_t c,
                            uintptr_t d, const char *service)
{
    SimRecoveredEffect effect;
    effect.kind = SIM_RECOVERED_EFFECT_WINDOW_OPERATION;
    effect.arguments[0] = (uintptr_t)operation;
    effect.arguments[1] = a;
    effect.arguments[2] = b;
    effect.arguments[3] = c;
    effect.arguments[4] = d;
    if (active_engine == NULL || active_engine->host.effect == NULL ||
        !active_engine->host.effect(active_engine->host.context, &effect))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, service);
}

static void graphics_rect(int16_t left, int16_t top, int16_t right,
                          int16_t bottom, int16_t color)
{
    SimRecoveredEffect effect;
    effect.kind = SIM_RECOVERED_EFFECT_GRAPHICS_RECT;
    effect.arguments[0] = (uintptr_t)(intptr_t)left;
    effect.arguments[1] = (uintptr_t)(intptr_t)top;
    effect.arguments[2] = (uintptr_t)(intptr_t)right;
    effect.arguments[3] = (uintptr_t)(intptr_t)bottom;
    effect.arguments[4] = (uintptr_t)(intptr_t)color;
    if (active_engine == NULL || active_engine->host.effect == NULL ||
        !active_engine->host.effect(active_engine->host.context, &effect))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, "g_9134");
}

static void graphics_line(int16_t x0, int16_t y0, int16_t x1,
                          int16_t y1, int16_t color)
{
    SimRecoveredEffect effect;
    effect.kind = SIM_RECOVERED_EFFECT_GRAPHICS_LINE;
    effect.arguments[0] = (uintptr_t)(intptr_t)x0;
    effect.arguments[1] = (uintptr_t)(intptr_t)y0;
    effect.arguments[2] = (uintptr_t)(intptr_t)x1;
    effect.arguments[3] = (uintptr_t)(intptr_t)y1;
    effect.arguments[4] = (uintptr_t)(intptr_t)color;
    if (active_engine == NULL || active_engine->host.effect == NULL ||
        !active_engine->host.effect(active_engine->host.context, &effect))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, "g_916C");
}

void (*g_9134)(int16_t, int16_t, int16_t, int16_t, int16_t) = graphics_rect;
void (*g_916C)(int16_t, int16_t, int16_t, int16_t, int16_t) = graphics_line;

void clip_Off(void)
{ window_operation(SIM_RECOVERED_WINDOW_CLIP_OFF, 0, 0, 0, 0, "clip_Off"); }
void clip_Push(void)
{ window_operation(SIM_RECOVERED_WINDOW_CLIP_PUSH, 0, 0, 0, 0, "clip_Push"); }
void clip_Pop(void)
{ window_operation(SIM_RECOVERED_WINDOW_CLIP_POP, 0, 0, 0, 0, "clip_Pop"); }
void clip_SetWin(int16_t win)
{ window_operation(SIM_RECOVERED_WINDOW_CLIP_SET, (uintptr_t)(intptr_t)win, 0, 0, 0, "clip_SetWin"); }
void clip_SubInclude(struct Rect *rect)
{ window_operation(SIM_RECOVERED_WINDOW_CLIP_INCLUDE, (uintptr_t)rect, 0, 0, 0, "clip_SubInclude"); }
void win_Close(int16_t win)
{ window_operation(SIM_RECOVERED_WINDOW_CLOSE, (uintptr_t)(intptr_t)win, 0, 0, 0, "win_Close"); }
void win_Open(int16_t win)
{ window_operation(SIM_RECOVERED_WINDOW_OPEN, (uintptr_t)(intptr_t)win, 0, 0, 0, "win_Open"); }
void win_FlushEvents(void)
{ window_operation(SIM_RECOVERED_WINDOW_FLUSH_EVENTS, 0, 0, 0, 0, "win_FlushEvents"); }
void win_DrawObjectNum(int16_t object)
{ window_operation(SIM_RECOVERED_WINDOW_DRAW_OBJECT, (uintptr_t)(intptr_t)object, 0, 0, 0, "win_DrawObjectNum"); }
void win_MakeObjSelected(int16_t object)
{ window_operation(SIM_RECOVERED_WINDOW_MAKE_SELECTED, (uintptr_t)(intptr_t)object, 0, 0, 0, "win_MakeObjSelected"); }
void win_MakeGroupUnselected(int16_t win, int16_t group)
{ window_operation(SIM_RECOVERED_WINDOW_UNSELECT_GROUP, (uintptr_t)(intptr_t)win, (uintptr_t)(intptr_t)group, 0, 0, "win_MakeGroupUnselected"); }
void win_MakeObjVisible(int16_t object)
{ window_operation(SIM_RECOVERED_WINDOW_MAKE_VISIBLE, (uintptr_t)(intptr_t)object, 0, 0, 0, "win_MakeObjVisible"); }
void win_MakeObjInvisible(int16_t object)
{ window_operation(SIM_RECOVERED_WINDOW_MAKE_INVISIBLE, (uintptr_t)(intptr_t)object, 0, 0, 0, "win_MakeObjInvisible"); }
void win_MakeObjUnselected(int16_t object)
{ window_operation(SIM_RECOVERED_WINDOW_MAKE_UNSELECTED, (uintptr_t)(intptr_t)object, 0, 0, 0, "win_MakeObjUnselected"); }
void win_SetObjSelectedState(int16_t object, int16_t state)
{ window_operation(SIM_RECOVERED_WINDOW_SET_SELECTED_STATE, (uintptr_t)(intptr_t)object, (uintptr_t)(intptr_t)state, 0, 0, "win_SetObjSelectedState"); }
void win_SetObjBitmap(int16_t object, int16_t bitmap)
{ window_operation(SIM_RECOVERED_WINDOW_SET_BITMAP, (uintptr_t)(intptr_t)object, (uintptr_t)(intptr_t)bitmap, 0, 0, "win_SetObjBitmap"); }
void win_LockWin(int16_t window)
{ window_operation(SIM_RECOVERED_WINDOW_LOCK, (uintptr_t)(intptr_t)window, 0, 0, 0, "win_LockWin"); }
void win_UnlockWin(int16_t window)
{ window_operation(SIM_RECOVERED_WINDOW_UNLOCK, (uintptr_t)(intptr_t)window, 0, 0, 0, "win_UnlockWin"); }
void win_Swap(int16_t from, int16_t to)
{ window_operation(SIM_RECOVERED_WINDOW_SWAP, (uintptr_t)(intptr_t)from, (uintptr_t)(intptr_t)to, 0, 0, "win_Swap"); }
void win_FillObjRect(int16_t object, int16_t color)
{ window_operation(SIM_RECOVERED_WINDOW_FILL_OBJECT, (uintptr_t)(intptr_t)object, (uintptr_t)(intptr_t)color, 0, 0, "win_FillObjRect"); }
int16_t win_DrawBitMap(int16_t x, int16_t y, int16_t bitmap)
{
    window_operation(SIM_RECOVERED_WINDOW_DRAW_BITMAP,
                     (uintptr_t)(intptr_t)x, (uintptr_t)(intptr_t)y,
                     (uintptr_t)(intptr_t)bitmap, 0, "win_DrawBitMap");
    return 1;
}
void win_PrintfAtObj(int16_t object, char *format, ...)
{
    char text[512];
    va_list arguments;
    int formatted;
    va_start(arguments, format);
    formatted = vsnprintf(text, sizeof text, format, arguments);
    va_end(arguments);
    if (formatted < 0 || (size_t)formatted >= sizeof text)
        unsupported_call("win_PrintfAtObj formatted string too long");
    window_operation(SIM_RECOVERED_WINDOW_PRINTF_AT_OBJECT,
                     (uintptr_t)(intptr_t)object, (uintptr_t)text,
                     (uintptr_t)(size_t)formatted, 0, "win_PrintfAtObj");
}
void SetMenuItemState(int16_t item, int16_t state)
{ window_operation(SIM_RECOVERED_WINDOW_SET_MENU_ITEM_STATE, (uintptr_t)(intptr_t)item, (uintptr_t)(intptr_t)state, 0, 0, "SetMenuItemState"); }
void f_1FD2_0135(int16_t item, char *text)
{ window_operation(SIM_RECOVERED_WINDOW_SET_MENU_ITEM_TEXT, (uintptr_t)(intptr_t)item, (uintptr_t)text, 0, 0, "f_1FD2_0135"); }

/* These are source-owned UI/render entries. Their exact source arguments are
 * delivered synchronously to the native window layer; the focused harness
 * records them without claiming to draw pixels. */
void SetMapTitle(void)
{ window_operation(SIM_RECOVERED_WINDOW_SET_MAP_TITLE, 0, 0, 0, 0, "SetMapTitle"); }
void win_YardClosed(void)
{ window_operation(SIM_RECOVERED_WINDOW_YARD_CLOSED, 0, 0, 0, 0, "win_YardClosed"); }
void DrawYard(void)
{ window_operation(SIM_RECOVERED_WINDOW_DRAW_YARD, 0, 0, 0, 0, "DrawYard"); }
void UpdateYard(void)
{ window_operation(SIM_RECOVERED_WINDOW_UPDATE_YARD, 0, 0, 0, 0, "UpdateYard"); }
void DrawSimPayoff(void)
{ window_operation(SIM_RECOVERED_WINDOW_DRAW_SIM_PAYOFF, 0, 0, 0, 0, "DrawSimPayoff"); }
void InvertPatch(int16_t x, int16_t y)
{ window_operation(SIM_RECOVERED_WINDOW_INVERT_PATCH, (uintptr_t)(intptr_t)x, (uintptr_t)(intptr_t)y, 0, 0, "InvertPatch"); }
void drawHistGraph(int16_t graph, int16_t hilite, int16_t slot)
{ window_operation(SIM_RECOVERED_WINDOW_DRAW_HISTORY_GRAPH, (uintptr_t)(intptr_t)graph, (uintptr_t)(intptr_t)hilite, (uintptr_t)(intptr_t)slot, 0, "drawHistGraph"); }
void UpdateEverything(void)
{ window_operation(SIM_RECOVERED_WINDOW_UPDATE_EVERYTHING, 0, 0, 0, 0, "UpdateEverything"); }
void DoWinHelp(int16_t topic)
{ window_operation(SIM_RECOVERED_WINDOW_DO_WIN_HELP, (uintptr_t)(intptr_t)topic, 0, 0, 0, "DoWinHelp"); }
void DoEditUpdateDraw(void)
{ window_operation(SIM_RECOVERED_WINDOW_UPDATE_EDIT, 0, 0, 0, 0, "DoEditUpdateDraw"); }
void UpdateEdit(void)
{ window_operation(SIM_RECOVERED_WINDOW_UPDATE_EDIT_IF_OPEN, 0, 0, 0, 0, "UpdateEdit"); }

void InvalEuMap(int16_t left, int16_t top, int16_t right, int16_t bottom)
{ window_operation(SIM_RECOVERED_WINDOW_INVALIDATE_MAP, (uintptr_t)(intptr_t)left, (uintptr_t)(intptr_t)top, (uintptr_t)(intptr_t)right, (uintptr_t)(intptr_t)bottom, "InvalEuMap"); }

void OverlayTileSet(int16_t type, int16_t id)
{
    window_operation(SIM_RECOVERED_WINDOW_OVERLAY_TILE_SET,
                     (uintptr_t)(intptr_t)type, (uintptr_t)(intptr_t)id,
                     0, 0, "OverlayTileSet");
    if (type == 0 && id == 0x3e9)
        fd_50F6_0480 = 0x90;
    else if (type == 0 && id == 0x3e8)
        fd_50F6_0480 = 0x50;
}

static void source_clamp_camera(void)
{
    int32_t width_limit = (MapPlane == 0 || MapPlane == 1) ? 128 : 64;
    if (fd_50F6_0508[0] < 0) fd_50F6_0508[0] = 0;
    else if ((int32_t)fd_50F6_0508[0] + fd_50F6_10E0 > width_limit)
        fd_50F6_0508[0] = (int16_t)(width_limit - fd_50F6_10E0);
    if (fd_50F6_0508[1] < 0) fd_50F6_0508[1] = 0;
    else if ((int32_t)fd_50F6_0508[1] + fd_50F6_10DE > 64)
        fd_50F6_0508[1] = (int16_t)(64 - fd_50F6_10DE);
}

/* Source root:m0250 f_0250_0D10 followed by f_0250_0F2C/UpdateEdit.
 * The source returns immediately for a zero delta; the caller must not clamp
 * or invalidate in that case. */
static int source_scroll_camera(int16_t delta_x, int16_t delta_y)
{
    int32_t dx = delta_x;
    int32_t dy = delta_y;
    int32_t x_distance = dx < 0 ? -dx : dx;
    int32_t y_distance = dy < 0 ? -dy : dy;
    int32_t ax = x_distance;
    int32_t ay = y_distance;
    int x_step = dx < 0 ? -1 : 1;
    int y_step = dy < 0 ? -1 : 1;
    uint32_t error = 0;
    if (dx == 0 && dy == 0)
        return 0;
    if (ay >= ax) {
        uint32_t fraction = ((uint32_t)x_distance << 16) /
                            (uint32_t)y_distance;
        for (int32_t i = 0; i < y_distance; ++i) {
            fd_50F6_0508[1] = (int16_t)(fd_50F6_0508[1] + y_step);
            error += fraction;
            if ((error >> 16) & 1u) {
                fd_50F6_0508[0] = (int16_t)(fd_50F6_0508[0] + x_step);
                error ^= 0x10000u;
            }
        }
    } else if (x_distance != 0) {
        uint32_t fraction = ((uint32_t)y_distance << 16) /
                            (uint32_t)x_distance;
        for (int32_t i = 0; i < x_distance; ++i) {
            fd_50F6_0508[0] = (int16_t)(fd_50F6_0508[0] + x_step);
            error += fraction;
            if ((error >> 16) & 1u) {
                fd_50F6_0508[1] = (int16_t)(fd_50F6_0508[1] + y_step);
                error ^= 0x10000u;
            }
        }
    }
    source_clamp_camera();
    window_operation(SIM_RECOVERED_WINDOW_UPDATE_EDIT, 0, 0, 0, 0,
                     "f_0250_0D10/UpdateEdit");
    return 1;
}

void CenterEdit(int16_t x, int16_t y)
{
    int32_t dx = (int32_t)x - fd_50F6_10E0 / 2 - fd_50F6_0508[0];
    int32_t dy = (int32_t)y - fd_50F6_10DE / 2 - fd_50F6_0508[1];
    (void)source_scroll_camera((int16_t)dx, (int16_t)dy);
    /* CenterEdit calls f_0250_0F2C after f_0250_0CF6 even when no movement. */
    source_clamp_camera();
}

void InvalQueenStorageDisp(void) { }
void f_0250_0ED2(void) { }
void f_00DF_00E0(void) { }
void f_00DF_015C(void) { }
void f_00DF_0164(void) { }
/* src/root/m00F8.c:239 is an empty native DOS body. The recovered caller's
 * extra parameter is ignored by this source definition. */
void MakeDMap(void) { }
int16_t WinPrintf(char *format, ...)
{ (void)format; return 0; }
void myBeginSoundReverse(int16_t sound, int16_t arg_a, int16_t arg_b)
{ myBeginSound(sound, arg_a, arg_b); }
void SetSRandSeed(uint32_t seed)
{
    if (active_engine == NULL || active_engine->session == NULL)
        unsupported_call("SetSRandSeed");
    sim_rng_set_s_seed(&active_engine->session->rng, (int16_t)seed);
}
uint32_t GetSRandSeed(void)
{
    if (active_engine == NULL || active_engine->session == NULL) {
        unsupported_call("GetSRandSeed");
        return 0;
    }
    return sim_rng_get_s_seed(&active_engine->session->rng);
}

static int waited_enough_source(int32_t *timer, int16_t delay)
{
    int result;
    uint32_t now = (uint32_t)host_tick_count();
    uint32_t timer_value = (uint32_t)*timer;
    if (now < timer_value) {
        result = 1;
    } else {
        uint32_t deadline = timer_value + (uint32_t)(int32_t)delay;
        result = deadline <= (uint32_t)host_tick_count();
    }
    if (result)
        *timer = host_tick_count();
    return result;
}

/* Source root:m00F8 myDelay: wait ticks/3 BIOS ticks, but let window events
 * and dialog abort/continue break the wait. TickCount and both queries are
 * mandatory host services; this retains the original busy-wait condition and
 * never fabricates elapsed time. */
void myDelay(uint16_t ticks)
{
    int32_t timer = host_tick_count();
    int16_t delay = (int16_t)(ticks / 3u);
    while (!waited_enough_source(&timer, delay) &&
           !host_query(SIM_RECOVERED_QUERY_WINDOW_EVENTS, NULL, 0,
                       "myDelay/win_Events") &&
           !host_query(SIM_RECOVERED_QUERY_DIALOG_ABORT_OR_CONTINUE,
                       NULL, 0, "myDelay/DialogAbortOrCont"))
        ;
}

int16_t MagnifyMenu(int16_t x, int16_t y, int16_t plane)
{
    (void)x;
    (void)y;
    (void)plane;
    unsupported_call("MagnifyMenu");
    return 0;
}

static void unsupported_call(const char *name)
{
    interrupt_tick(SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL, name);
}

static void bind_dos_keyboard_flags(void)
{
    int32_t flags = host_query(SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS,
                               NULL, 0, "DOS keyboard flags");
    if (flags < 0 || flags > UINT8_MAX)
        interrupt_tick(SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL,
                       "DOS keyboard flags outside byte range");
    recovered_keyboard_set_modifiers((uint8_t)flags);
}

/* Link-only edges from the generated translation-unit profile fail the
 * current tick with their source identifier. These bodies are deliberately
 * not gameplay/UI implementations and never return to the recovered caller. */
#define FAIL_VOID0(name) void name(void) { unsupported_call(#name); }
#define FAIL_VOID1(name, t1, a1) \
    void name(t1 a1) { (void)a1; unsupported_call(#name); }
#define FAIL_VOID2(name, t1, a1, t2, a2) \
    void name(t1 a1, t2 a2) { (void)a1; (void)a2; unsupported_call(#name); }
#define FAIL_VOID3(name, t1, a1, t2, a2, t3, a3) \
    void name(t1 a1, t2 a2, t3 a3) { \
        (void)a1; (void)a2; (void)a3; unsupported_call(#name); }

FAIL_VOID0(AboutDialog)
void AntMenu(struct Event *event)
{
    (void)event;
    unsupported_call("AntMenu");
}
FAIL_VOID1(DialogWaitInit, int16_t, mode)
FAIL_VOID3(EggBalloons, int16_t, x, int16_t, y, int16_t, plane)
FAIL_VOID1(EndGameDialog, int16_t, code)
FAIL_VOID3(FightBalloons, int16_t, x, int16_t, y, int16_t, plane)
int16_t NewGame(int16_t option)
{
    (void)option;
    unsupported_call("NewGame");
    return 0;
}
FAIL_VOID0(OpenCasteWindow)
FAIL_VOID0(OpenEditWindow)
FAIL_VOID0(OpenInfoWindow)
FAIL_VOID0(OpenMapYard)
FAIL_VOID0(OpenModeWindow)
FAIL_VOID3(QueenBalloons, int16_t, x, int16_t, y, int16_t, plane)
FAIL_VOID3(RestBalloons, int16_t, x, int16_t, y, int16_t, plane)
FAIL_VOID0(ScoreDialog)
FAIL_VOID1(SetSimCursor, int16_t, cursor)
FAIL_VOID0(SpiderDialog)
FAIL_VOID0(StopSong)
FAIL_VOID0(f_0250_0E15)
FAIL_VOID0(f_0250_5058)
int16_t f_1B4E_000D(int16_t color)
{
    (void)color;
    unsupported_call("f_1B4E_000D");
    return 0;
}
int16_t f_1F58_0038(void)
{
    unsupported_call("f_1F58_0038");
    return 0;
}
void f_1FD2_04D0()
{
    unsupported_call("f_1FD2_04D0");
}
FAIL_VOID1(f_20E8_0725, int16_t, window)
FAIL_VOID0(initControls)
FAIL_VOID0(o12_384C_100A)

#undef FAIL_VOID0
#undef FAIL_VOID1
#undef FAIL_VOID2
#undef FAIL_VOID3

SimRecoveredEngineInitStatus sim_recovered_engine_init(
    SimRecoveredEngine *engine, SimSession *session,
    const SimRecoveredHost *host)
{
    SimRecoveredBridgeStatus bridge_status;
    PortableGameViewState view_state;
    PortableGameView view;
    if (engine == NULL || session == NULL || host == NULL ||
        host->tick_count == NULL || host->query == NULL ||
        host->effect == NULL || host->song_done == NULL ||
        (host->screen_width != 320 && host->screen_width != 640) ||
        session->window_registry == NULL ||
        host->hardware_profile != (uint8_t)session->window_registry->profile_id)
        return SIM_RECOVERED_ENGINE_INIT_INVALID_ARGUMENT;
    memset(engine, 0, sizeof(*engine));
    if (!session->resources_ready || !session->new_game_ready ||
        !session->rng_seeded || !session->advice.loaded)
        return SIM_RECOVERED_ENGINE_INIT_SESSION_NOT_READY;
    view_state.pheromone_mode = 0;
    view_state.animation_base = session->world.source_state_07be;
    view_state.queen_frame = 0;
    view_state.young_frame = 0;
    view_state.caste_frame = 0;
    view_state.ega_profile = 0;
    if (portable_game_view_resolve(session->window_registry, &session->world,
                                   &view_state, &view) !=
        PORTABLE_GAME_VIEW_OK)
        return SIM_RECOVERED_ENGINE_INIT_VIEW_UNAVAILABLE;
    bridge_status = sim_recovered_state_from_session(&engine->recovered,
                                                     session);
    if (bridge_status != SIM_RECOVERED_BRIDGE_OK)
        return SIM_RECOVERED_ENGINE_INIT_BRIDGE_ERROR;
    /* SetDefaultWindows derives logical map-cell dimensions from the live Edit
     * viewport. The resolver reads the loaded/recalculated window geometry and
     * applies that source formula, rather than assuming fixed dimensions. */
    engine->recovered.fd_50F6_10E0 = view.map.columns;
    engine->recovered.fd_50F6_10DE = view.map.rows;
    engine->recovered.fd_50F6_110C.left = view.viewport.left;
    engine->recovered.fd_50F6_110C.top = view.viewport.top;
    engine->recovered.fd_50F6_110C.right = view.viewport.right;
    engine->recovered.fd_50F6_110C.bottom = view.viewport.bottom;
    engine->recovered.fd_55B3_19BE = view.map.cell_step_x;
    engine->recovered.fd_55B3_19C0 = view.map.cell_step_y;
    engine->recovered.g_3DB2 = (int16_t)host->screen_width;
    engine->recovered.g_5A97 = (int8_t)host->hardware_profile;
    engine->session = session;
    engine->host = *host;
    engine->status = SIM_RECOVERED_ENGINE_OK;
    portable_audio_intents_init(&engine->audio_intents);
    engine->initialized = 1;
    return SIM_RECOVERED_ENGINE_INIT_OK;
}

SimRecoveredEngineStatus sim_recovered_engine_tick(
    SimRecoveredEngine *engine, const SimNestRequest *nest_clock)
{
    SimRecoveredBridgeStatus bridge_status;
    SimNestStatus nest_status;
    jmp_buf abort_target;
    int jumped;
    if (engine == NULL || !engine->initialized || engine->session == NULL)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    if (nest_clock != NULL && nest_clock->tick_count != 2)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    if (engine->status != SIM_RECOVERED_ENGINE_OK)
        return SIM_RECOVERED_ENGINE_FAULTED;
    if (active_engine != NULL || active_abort_target != NULL)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;

    if (!prepare_nest_clock(engine, nest_clock))
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    engine->rng_before_tick = engine->session->rng;
    engine->audio_before_tick = engine->audio_intents;
    engine->failed_service = NULL;
    engine->status = SIM_RECOVERED_ENGINE_OK;
    engine->audio_binding.intents = &engine->audio_intents;
    engine->audio_binding.driver_ready = engine->host.audio_driver_ready;
    engine->audio_binding.song_done = engine->host.song_done;
    engine->audio_binding.song_done_context = engine->host.context;
    active_engine = engine;
    active_abort_target = &abort_target;
    jumped = setjmp(abort_target);
    if (jumped != 0)
        goto interrupted;

    bind_dos_keyboard_flags();
    recovered_rng_bind(&engine->session->rng);
    sim_recovered_nest_bind(&engine->nest_binding);
    sim_recovered_audio_bind(&engine->audio_binding);
    engine->recovered_binding_active = 1;
    recovered_bind_begin(&engine->binding_frame, &engine->recovered);
    DoAntSim();
    recovered_bind_end(&engine->binding_frame, &engine->recovered);
    engine->recovered_binding_active = 0;
    if (!sim_recovered_audio_unbind(&engine->audio_binding))
        abort();
    nest_status = sim_recovered_nest_unbind(&engine->nest_binding);
    if (engine->nest_binding.calls == 0)
        nest_status = SIM_NEST_OK;
    recovered_rng_bind(NULL);
    active_abort_target = NULL;
    active_engine = NULL;
    if (nest_status != SIM_NEST_OK) {
        engine->status = SIM_RECOVERED_ENGINE_NEST_ERROR;
        engine->failed_service = "o25_3BA4_1035";
        return engine->status;
    }

    bridge_status = sim_session_from_recovered_state(engine->session,
                                                     &engine->recovered);
    if (bridge_status != SIM_RECOVERED_BRIDGE_OK) {
        engine->status = SIM_RECOVERED_ENGINE_BRIDGE_ERROR;
        engine->failed_service = "sim_session_from_recovered_state";
        return engine->status;
    }
    ++engine->completed_ticks;
    return SIM_RECOVERED_ENGINE_OK;

interrupted:
    if (engine->recovered_binding_active) {
        RecoveredBindingFrame restore_frame;
        /* bind_begin snapshots the interrupted TLS image and imports the
         * frame's saved outer image. The temporary snapshot is discarded. */
        recovered_bind_begin(&restore_frame, &engine->binding_frame.previous);
        engine->recovered_binding_active = 0;
    }
    (void)sim_recovered_audio_unbind(&engine->audio_binding);
    (void)sim_recovered_nest_unbind(&engine->nest_binding);
    recovered_rng_bind(NULL);
    engine->session->rng = engine->rng_before_tick;
    engine->audio_intents = engine->audio_before_tick;
    active_abort_target = NULL;
    active_engine = NULL;
    return engine->status;
}

SimRecoveredEngineStatus sim_recovered_engine_action(
    SimRecoveredEngine *engine, SimRecoveredAction action,
    int16_t a, int16_t b)
{
    SimRecoveredBridgeStatus bridge_status;
    jmp_buf abort_target;
    int jumped;
    if (engine == NULL || !engine->initialized || engine->session == NULL)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    if (engine->status != SIM_RECOVERED_ENGINE_OK)
        return SIM_RECOVERED_ENGINE_FAULTED;
    if (active_engine != NULL || active_abort_target != NULL)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    if ((action == SIM_RECOVERED_ACTION_PAUSE && (a < 0 || a > 1)) ||
        (action == SIM_RECOVERED_ACTION_SPEED && (a < 0 || a > 3)) ||
        (action == SIM_RECOVERED_ACTION_PAN &&
            (a < 0 || a >= (engine->recovered.MapPlane <= 1 ? 128 : 64) ||
                                                b < 0 || b >= 64)) ||
        (action == SIM_RECOVERED_ACTION_MAP_PLANE && (a < 0 || a > 3)) ||
        action < SIM_RECOVERED_ACTION_PAUSE ||
        action > SIM_RECOVERED_ACTION_MAP_PLANE)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;

    engine->rng_before_tick = engine->session->rng;
    engine->audio_before_tick = engine->audio_intents;
    engine->failed_service = NULL;
    engine->status = SIM_RECOVERED_ENGINE_OK;
    engine->audio_binding.intents = &engine->audio_intents;
    engine->audio_binding.driver_ready = engine->host.audio_driver_ready;
    engine->audio_binding.song_done = engine->host.song_done;
    engine->audio_binding.song_done_context = engine->host.context;

    active_engine = engine;
    active_abort_target = &abort_target;
    jumped = setjmp(abort_target);
    if (jumped != 0)
        goto interrupted_action;

    bind_dos_keyboard_flags();
    recovered_rng_bind(&engine->session->rng);
    sim_recovered_audio_bind(&engine->audio_binding);
    engine->recovered_binding_active = 1;
    recovered_bind_begin(&engine->binding_frame, &engine->recovered);
    switch (action) {
    case SIM_RECOVERED_ACTION_PAUSE:
        SetPause(a);
        break;
    case SIM_RECOVERED_ACTION_SPEED:
        fd_3D57_07CC[0] = a;
        SetMenuEntries();
        break;
    case SIM_RECOVERED_ACTION_PAN:
        CenterEdit(a, b);
        break;
    case SIM_RECOVERED_ACTION_SCROLL:
        (void)source_scroll_camera(a, b);
        break;
    case SIM_RECOVERED_ACTION_MAP_PLANE:
        SetMapPlane(a);
        break;
    default:
        interrupt_tick(SIM_RECOVERED_ENGINE_INVALID_ARGUMENT,
                       "invalid source action");
    }
    recovered_bind_end(&engine->binding_frame, &engine->recovered);
    engine->recovered_binding_active = 0;
    if (!sim_recovered_audio_unbind(&engine->audio_binding))
        abort();
    recovered_rng_bind(NULL);
    active_abort_target = NULL;
    active_engine = NULL;
    bridge_status = sim_session_from_recovered_state(engine->session,
                                                     &engine->recovered);
    if (bridge_status != SIM_RECOVERED_BRIDGE_OK) {
        engine->status = SIM_RECOVERED_ENGINE_BRIDGE_ERROR;
        engine->failed_service = "sim_session_from_recovered_state";
    }
    return engine->status;

interrupted_action:
    if (engine->recovered_binding_active) {
        RecoveredBindingFrame restore_frame;
        recovered_bind_begin(&restore_frame, &engine->binding_frame.previous);
        engine->recovered_binding_active = 0;
    }
    (void)sim_recovered_audio_unbind(&engine->audio_binding);
    recovered_rng_bind(NULL);
    engine->session->rng = engine->rng_before_tick;
    engine->audio_intents = engine->audio_before_tick;
    active_abort_target = NULL;
    active_engine = NULL;
    return engine->status;
}

SimRecoveredEngineStatus sim_recovered_engine_process_edit_event(
    SimRecoveredEngine *engine, const SimRecoveredEvent *event,
    const SimNestRequest *nest_clock)
{
    SimRecoveredBridgeStatus bridge_status;
    SimNestStatus nest_status;
    struct Event source_event;
    jmp_buf abort_target;
    int jumped;
    if (engine == NULL || event == NULL || !engine->initialized ||
        engine->session == NULL ||
        (nest_clock != NULL && nest_clock->tick_count != 2))
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    if (engine->status != SIM_RECOVERED_ENGINE_OK)
        return SIM_RECOVERED_ENGINE_FAULTED;
    if (active_engine != NULL || active_abort_target != NULL)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    source_event.what = event->what;
    source_event.message = event->message;
    source_event.x4 = event->x4;
    source_event.modifiers = event->modifiers;
    source_event.h = event->h;
    source_event.v = event->v;
    source_event.code = event->code;
    source_event.xE = event->xE;

    if (!prepare_nest_clock(engine, nest_clock))
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    engine->rng_before_tick = engine->session->rng;
    engine->audio_before_tick = engine->audio_intents;
    engine->failed_service = NULL;
    engine->status = SIM_RECOVERED_ENGINE_OK;
    engine->audio_binding.intents = &engine->audio_intents;
    engine->audio_binding.driver_ready = engine->host.audio_driver_ready;
    engine->audio_binding.song_done = engine->host.song_done;
    engine->audio_binding.song_done_context = engine->host.context;
    active_engine = engine;
    active_abort_target = &abort_target;
    jumped = setjmp(abort_target);
    if (jumped != 0)
        goto interrupted_event;

    bind_dos_keyboard_flags();
    recovered_rng_bind(&engine->session->rng);
    sim_recovered_nest_bind(&engine->nest_binding);
    sim_recovered_audio_bind(&engine->audio_binding);
    engine->recovered_binding_active = 1;
    recovered_bind_begin(&engine->binding_frame, &engine->recovered);
    processEdit(&source_event);
    recovered_bind_end(&engine->binding_frame, &engine->recovered);
    engine->recovered_binding_active = 0;
    if (!sim_recovered_audio_unbind(&engine->audio_binding))
        abort();
    nest_status = sim_recovered_nest_unbind(&engine->nest_binding);
    if (engine->nest_binding.calls == 0)
        nest_status = SIM_NEST_OK;
    recovered_rng_bind(NULL);
    active_abort_target = NULL;
    active_engine = NULL;
    if (nest_status != SIM_NEST_OK) {
        engine->status = SIM_RECOVERED_ENGINE_NEST_ERROR;
        engine->failed_service = "o25_3BA4_1035";
        return engine->status;
    }
    bridge_status = sim_session_from_recovered_state(engine->session,
                                                     &engine->recovered);
    if (bridge_status != SIM_RECOVERED_BRIDGE_OK) {
        engine->status = SIM_RECOVERED_ENGINE_BRIDGE_ERROR;
        engine->failed_service = "sim_session_from_recovered_state";
        return engine->status;
    }
    return SIM_RECOVERED_ENGINE_OK;

interrupted_event:
    if (engine->recovered_binding_active) {
        RecoveredBindingFrame restore_frame;
        recovered_bind_begin(&restore_frame, &engine->binding_frame.previous);
        engine->recovered_binding_active = 0;
    }
    (void)sim_recovered_audio_unbind(&engine->audio_binding);
    (void)sim_recovered_nest_unbind(&engine->nest_binding);
    recovered_rng_bind(NULL);
    engine->session->rng = engine->rng_before_tick;
    engine->audio_intents = engine->audio_before_tick;
    active_abort_target = NULL;
    active_engine = NULL;
    return engine->status;
}

SimRecoveredEngineStatus sim_recovered_engine_yellow_command_key(
    SimRecoveredEngine *engine, int16_t key,
    const SimNestRequest *nest_clock, int16_t *handled)
{
    SimRecoveredBridgeStatus bridge_status;
    SimNestStatus nest_status;
    int16_t result;
    jmp_buf abort_target;
    int jumped;
    if (engine == NULL || handled == NULL || !engine->initialized ||
        engine->session == NULL ||
        (nest_clock != NULL && nest_clock->tick_count != 2))
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    if (engine->status != SIM_RECOVERED_ENGINE_OK)
        return SIM_RECOVERED_ENGINE_FAULTED;
    if (active_engine != NULL || active_abort_target != NULL)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;

    if (!prepare_nest_clock(engine, nest_clock))
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    engine->rng_before_tick = engine->session->rng;
    engine->audio_before_tick = engine->audio_intents;
    engine->failed_service = NULL;
    engine->status = SIM_RECOVERED_ENGINE_OK;
    engine->audio_binding.intents = &engine->audio_intents;
    engine->audio_binding.driver_ready = engine->host.audio_driver_ready;
    engine->audio_binding.song_done = engine->host.song_done;
    engine->audio_binding.song_done_context = engine->host.context;
    active_engine = engine;
    active_abort_target = &abort_target;
    jumped = setjmp(abort_target);
    if (jumped != 0)
        goto interrupted_key;

    bind_dos_keyboard_flags();
    recovered_rng_bind(&engine->session->rng);
    sim_recovered_nest_bind(&engine->nest_binding);
    sim_recovered_audio_bind(&engine->audio_binding);
    engine->recovered_binding_active = 1;
    recovered_bind_begin(&engine->binding_frame, &engine->recovered);
    result = YellowCommandKey(key);
    recovered_bind_end(&engine->binding_frame, &engine->recovered);
    engine->recovered_binding_active = 0;
    if (!sim_recovered_audio_unbind(&engine->audio_binding))
        abort();
    nest_status = sim_recovered_nest_unbind(&engine->nest_binding);
    if (engine->nest_binding.calls == 0)
        nest_status = SIM_NEST_OK;
    recovered_rng_bind(NULL);
    active_abort_target = NULL;
    active_engine = NULL;
    if (nest_status != SIM_NEST_OK) {
        engine->status = SIM_RECOVERED_ENGINE_NEST_ERROR;
        engine->failed_service = "o25_3BA4_1035";
        return engine->status;
    }
    bridge_status = sim_session_from_recovered_state(engine->session,
                                                     &engine->recovered);
    if (bridge_status != SIM_RECOVERED_BRIDGE_OK) {
        engine->status = SIM_RECOVERED_ENGINE_BRIDGE_ERROR;
        engine->failed_service = "sim_session_from_recovered_state";
        return engine->status;
    }
    *handled = result;
    return SIM_RECOVERED_ENGINE_OK;

interrupted_key:
    if (engine->recovered_binding_active) {
        RecoveredBindingFrame restore_frame;
        recovered_bind_begin(&restore_frame, &engine->binding_frame.previous);
        engine->recovered_binding_active = 0;
    }
    (void)sim_recovered_audio_unbind(&engine->audio_binding);
    (void)sim_recovered_nest_unbind(&engine->nest_binding);
    recovered_rng_bind(NULL);
    engine->session->rng = engine->rng_before_tick;
    engine->audio_intents = engine->audio_before_tick;
    active_abort_target = NULL;
    active_engine = NULL;
    return engine->status;
}

int sim_recovered_engine_snapshot(const SimRecoveredEngine *engine,
                                  RecoveredState *snapshot)
{
    if (engine == NULL || snapshot == NULL || !engine->initialized)
        return 0;
    if (active_engine == engine && engine->recovered_binding_active) {
        RecoveredBindingFrame *frame = malloc(sizeof(*frame));
        RecoveredState *discard = malloc(sizeof(*discard));
        if (frame == NULL || discard == NULL) {
            free(frame);
            free(discard);
            return 0;
        }
        recovered_bind_begin(frame, &engine->recovered);
        memcpy(snapshot, &frame->previous, sizeof(*snapshot));
        recovered_bind_end(frame, discard);
        free(frame);
        free(discard);
        return 1;
    }
    memcpy(snapshot, &engine->recovered, sizeof(*snapshot));
    return 1;
}

int sim_recovered_engine_next_audio(SimRecoveredEngine *engine,
                                    PortableAudioIntent *intent)
{
    if (engine == NULL || !engine->initialized || intent == NULL)
        return 0;
    return portable_audio_next_intent(&engine->audio_intents, intent);
}

const char *sim_recovered_engine_status_string(
    SimRecoveredEngineStatus status)
{
    switch (status) {
    case SIM_RECOVERED_ENGINE_OK: return "ok";
    case SIM_RECOVERED_ENGINE_INVALID_ARGUMENT: return "invalid argument";
    case SIM_RECOVERED_ENGINE_SESSION_NOT_READY: return "session not ready";
    case SIM_RECOVERED_ENGINE_BRIDGE_ERROR: return "session export failed";
    case SIM_RECOVERED_ENGINE_HOST_REJECTED: return "host service rejected call";
    case SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL: return "unsupported source call";
    case SIM_RECOVERED_ENGINE_NEST_ERROR: return "nest transition failed";
    case SIM_RECOVERED_ENGINE_AUDIO_BIND_ERROR: return "audio binding failed";
    case SIM_RECOVERED_ENGINE_FAULTED: return "engine already faulted";
    default: return "unknown engine status";
    }
}
