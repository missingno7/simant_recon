#include "engine.h"
#include "menu_adapter.h"
#include "control_adapter.h"
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
#include "history_adapter.h"
#endif
#include "../../ui_model/windows/game_view.h"
#ifdef SIMANT_ENABLE_BALLOON_STATE_NEXT3
#include "balloon_adapter.h"
#endif

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
struct SimRecoveredControlRequest {
    SimSetupControlKind kind;
    const SimControlEventMessage *message;
    SimControlEventPrivateState *private_state;
    const SimControlEventProvider *provider;
};
#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
extern void RandYard(void);
#endif

static _Thread_local SimRecoveredEngine *active_engine;
static _Thread_local jmp_buf *active_abort_target;
extern int16_t NewGame(int16_t option);

int sim_recovered_engine_new_game_from_modal(SimRecoveredEngine *engine,
                                             int16_t option, int16_t *result)
{
    if (engine == NULL || engine != active_engine || result == NULL ||
        active_abort_target == NULL || !engine->recovered_binding_active ||
        !engine->initialized || !engine->end_game_modal_active || option != 0)
        return 0;
#ifdef SIMANT_ENABLE_NEW_GAME_NEXT5
    *result = NewGame(option);
    return 1;
#else
    return 0;
#endif
}
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
#ifdef SIMANT_ENABLE_BALLOON_STATE_NEXT3
/* Pure source cue submission has no host effects. The next3 state profile
 * supplies the otherwise omitted displayed/pending fields; rendering is a
 * separate source boundary. The old next2 profile retains its named failure. */
void EggBalloons(int16_t x, int16_t y, int16_t plane)
{
    sim_recovered_egg_balloons(x, y, plane);
}
void FightBalloons(int16_t x, int16_t y, int16_t plane)
{
    sim_recovered_fight_balloons(x, y, plane);
}
void QueenBalloons(int16_t x, int16_t y, int16_t plane)
{
    sim_recovered_queen_balloons(x, y, plane);
}
void RestBalloons(int16_t x, int16_t y, int16_t plane)
{
    sim_recovered_rest_balloons(x, y, plane);
}
#else
FAIL_VOID3(EggBalloons, int16_t, x, int16_t, y, int16_t, plane)
FAIL_VOID3(FightBalloons, int16_t, x, int16_t, y, int16_t, plane)
FAIL_VOID3(QueenBalloons, int16_t, x, int16_t, y, int16_t, plane)
FAIL_VOID3(RestBalloons, int16_t, x, int16_t, y, int16_t, plane)
#endif
void EndGameDialog(int16_t code)
{
    SimGameOverInput input;
    int completed;
    (void)code; /* root_m0894's extra caller argument is ignored by S14. */
    if (active_engine == NULL || active_engine->host.end_game == NULL)
        unsupported_call("EndGameDialog");
    memset(&input, 0, sizeof(input));
    input.history_cursor = fd_50F6_04F4;
    input.history_count = fd_3D57_0828;
    memcpy(input.health_history, fd_50F6_073C, sizeof(input.health_history));
    memcpy(input.blue_food_history, fd_50F6_0626,
           sizeof(input.blue_food_history));
    memcpy(input.red_food_history, fd_50F6_06AE,
           sizeof(input.red_food_history));
    input.food_total = fd_50F6_0FC2;
    input.food_used = fd_50F6_1000;
    input.blue_workers = fd_50F6_09FA;
    input.red_workers = fd_50F6_0A00;
    input.scenario = fd_50F6_0EAC;
    input.blue_colony_score = fd_50F6_0A90;
    input.colony_score_a = fd_50F6_0AC4;
    input.colony_score_b = fd_50F6_0A9E;
    memcpy(input.tutorial_marks, fd_3D57_00A4, sizeof(input.tutorial_marks));
    input.health = MeHealth;
    input.world_ticks = fd_50F6_0C26;
    input.losing_side = fd_50F6_0366;
    input.sound_enabled = fd_3D57_07A8[1] != 0;
    input.screen_width = (uint16_t)g_3DB2;
    if (active_engine->end_game_modal_active)
        unsupported_call("recursive EndGameDialog");
    active_engine->end_game_modal_active = 1;
    completed = active_engine->host.end_game(active_engine->host.context, &input,
                                              &active_engine->session->rng);
    active_engine->end_game_modal_active = 0;
    if (!completed)
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, "EndGameDialog");
}
#ifndef SIMANT_ENABLE_NEW_GAME_NEXT5
int16_t NewGame(int16_t option)
{
    (void)option;
    unsupported_call("NewGame");
    return 0;
}
#endif
#ifdef SIMANT_ENABLE_NEW_GAME_NEXT5
extern void win_CasteControlChanged(void);
extern void win_ModeControlChanged(void);

/* S15's source wrappers preserve these ordered calls around the source
 * control-state routines selected from root:m0798. */
void OpenCasteWindow(void)
{
    win_CasteControlChanged();
    win_Open(0x1300);
}

void OpenModeWindow(void)
{
    win_ModeControlChanged();
    win_Open(0x1200);
}

void OpenEditWindow(void)
{
    /* root:20E8:04B6 is the reviewed source alias for win_Open. */
    win_Open(0);
}

/* The original helper accepts one packed int16 result per modal call. The
 * source NewGame consumes the result codes itself, including LoadGame 0x207. */
int16_t DoScenario(int16_t flag)
{
    int16_t result;
    if (active_engine == NULL || active_engine->host.scenario_select == NULL)
        unsupported_call("DoScenario");
    if (!active_engine->host.scenario_select(active_engine->host.context,
                                             (int16_t)flag, &result))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED, "DoScenario");
    return result;
}

/* The 0x207 branch enters the original LoadGame file service. */
int16_t o09_35F5_0000(int16_t a, int16_t b)
{
    (void)a;
    (void)b;
    unsupported_call("LoadGame (o09_35F5_0000)");
    return 0;
}

void f_015B_053C(int16_t plane)
{
    /* layout/symbols.json records this source alias as SetMapPlane. */
    SetMapPlane(plane);
}

int16_t f_22BF_0A65(void)
{
    /* Tutorial scenario uses an implicit historical fastcall register input
     * to query zoom state. Its native call boundary must be made explicit
     * before it can safely consume the source window model. */
    unsupported_call("NewGame tutorial zoom-state fastcall boundary");
    return 0;
}

void o26_39C7_0000(void)
{
    unsupported_call("NewGame tutorial zoom-window boundary");
}

void SetEditWinTitle(char *title)
{
    (void)title; /* Source SetDefaultWindows passes NULL; root:m0250 reads DATA. */
    window_operation(SIM_RECOVERED_WINDOW_SET_EDIT_TITLE_FROM_SCENARIO,
                     1, (uintptr_t)(intptr_t)fd_50F6_0EAC, 0, 0,
                     "SetEditWinTitle");
    if (win_IsWinOpen(0)) {
        clip_Push();
        clip_SetWin(0);
        window_operation(SIM_RECOVERED_WINDOW_DRAW_EDIT_TITLE_OBJECT,
                         1, 0, 0, 0, "SetEditWinTitle/draw");
        clip_Pop();
    }
}

void YardToMap(void)
{
    win_MakeGroupUnselected(0x100, 2);
    if (!win_IsWinOpen(0x100)) {
        if (win_IsWinOpen(0x1900)) {
            SetMapPlane(1);
            win_Swap(0x1900, 0x100);
        } else {
            win_Open(0x100);
        }
    }
}
#else
FAIL_VOID0(OpenCasteWindow)
FAIL_VOID0(OpenEditWindow)
#endif
FAIL_VOID0(OpenInfoWindow)
FAIL_VOID0(OpenMapYard)
#ifndef SIMANT_ENABLE_NEW_GAME_NEXT5
FAIL_VOID0(OpenModeWindow)
#endif
FAIL_VOID0(ScoreDialog)
FAIL_VOID1(SetSimCursor, int16_t, cursor)
FAIL_VOID0(SpiderDialog)
FAIL_VOID0(StopSong)
FAIL_VOID0(f_0250_0E15)
FAIL_VOID0(f_0250_5058)
int16_t f_1B4E_000D(int16_t color)
{
    uintptr_t arguments[] = {(uintptr_t)(uint16_t)color};
    int32_t mapped = host_query(SIM_RECOVERED_QUERY_DRIVER_COLOR,
                                arguments, 1, "f_1B4E_000D");
    uint16_t word;
    int16_t result;
    if (mapped < 0 || mapped > UINT16_MAX)
        unsupported_call("f_1B4E_000D invalid driver color word");
    word = (uint16_t)mapped;
    memcpy(&result, &word, sizeof result);
    return result;
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
#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
/* The selected source control bodies own their globals. Only resource-size
 * lookup and release of an actual host-owned animation cross this boundary. */
void f_208F_0419(struct Pt *size, int16_t id)
{
    SimSetupHooks *hooks;
    int16_t width, height;
    if (active_engine == NULL || size == NULL)
        unsupported_call("f_208F_0419 resource-size arguments");
    hooks = &active_engine->session->setup_hooks;
    if (hooks->resource_size == NULL ||
        !hooks->resource_size(hooks->context, (uint16_t)id, 2,
                              &width, &height))
        interrupt_tick(SIM_RECOVERED_ENGINE_HOST_REJECTED,
                       "f_208F_0419 resource size");
    size->x = width;
    size->y = height;
}

void hanim_RemoveAnimSet(void *handle)
{
    size_t i;
    if (active_engine == NULL || handle == NULL)
        unsupported_call("hanim_RemoveAnimSet arguments");
    for (i = 0; i < 2; ++i) {
        SimSessionControlVisual *visual = &active_engine->session->controls[i];
        if (visual->animation_resource == handle) {
            if (visual->release_animation == NULL)
                unsupported_call("hanim_RemoveAnimSet unowned animation");
            visual->release_animation(handle);
            visual->animation_resource = NULL;
            visual->release_animation = NULL;
            visual->active = 0;
            return;
        }
    }
    unsupported_call("hanim_RemoveAnimSet unknown animation");
}
#else
#ifndef SIMANT_ENABLE_NEW_GAME_NEXT5
FAIL_VOID0(initControls)
#endif
#endif
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
    SimNestStatus nest_status;
    jmp_buf abort_target;
    int jumped;
#ifdef SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC
    const int needs_nest = action == SIM_RECOVERED_ACTION_RAND_YARD ||
                          action == SIM_RECOVERED_ACTION_PROC_MENU ||
                          action == SIM_RECOVERED_ACTION_DIAGNOSTIC_END_GAME;
    const SimRecoveredAction last_action = SIM_RECOVERED_ACTION_DIAGNOSTIC_END_GAME;
    if (action == SIM_RECOVERED_ACTION_DIAGNOSTIC_END_GAME) {
        if (a != 0 || b != 0) return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    }
#else
    const int needs_nest = action == SIM_RECOVERED_ACTION_RAND_YARD ||
                          action == SIM_RECOVERED_ACTION_PROC_MENU;
    const SimRecoveredAction last_action = SIM_RECOVERED_ACTION_HISTORY_EVENT;
#endif
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
        (action == SIM_RECOVERED_ACTION_RAND_YARD &&
            (a < 0 || a > 3 || b != 0)) ||
        (action == SIM_RECOVERED_ACTION_PROC_MENU && b != 0) ||
        (action == SIM_RECOVERED_ACTION_HISTORY_EVENT && b != 0) ||
        (action == SIM_RECOVERED_ACTION_CONTROL_EVENT &&
            (engine->control_request == NULL || a != 0 || b != 0)) ||
        action < SIM_RECOVERED_ACTION_PAUSE ||
        action > last_action)
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    if (needs_nest && !prepare_nest_clock(engine, NULL))
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
    if (needs_nest)
        sim_recovered_nest_bind(&engine->nest_binding);
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
    case SIM_RECOVERED_ACTION_RAND_YARD:
#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
        /* This is the RandYard call boundary, not the surrounding NewGame UI
         * flow. No state reinitialization or RNG reseeding is performed. */
        fd_50F6_0EAC = a;
        RandYard();
        break;
#else
        unsupported_call("RandYard requires selected source initControls");
        break;
#endif
    case SIM_RECOVERED_ACTION_PROC_MENU: {
        uint16_t command;
        memcpy(&command, &a, sizeof(command));
        sim_recovered_source_proc_menu_command(command);
        break;
    }
    case SIM_RECOVERED_ACTION_CONTROL_EVENT: {
        struct SimRecoveredControlRequest *request = engine->control_request;
        SimControlEventStatus status = sim_recovered_source_control_event(
            &engine->session->setup_controls, request->private_state,
            request->kind, request->message, request->provider);
        if (status != SIM_CONTROL_EVENT_OK)
            unsupported_call(sim_control_event_status_string(status));
        break;
    }
    case SIM_RECOVERED_ACTION_HISTORY_EVENT: {
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
        uint16_t command;
        memcpy(&command, &a, sizeof command);
        if (!sim_recovered_source_history_event(command))
            unsupported_call("ProcHistoryEvent native event ABI unavailable");
#else
        unsupported_call("ProcHistoryEvent requires reviewed Next10 profile");
#endif
        break;
    }
#ifdef SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC
    case SIM_RECOVERED_ACTION_DIAGNOSTIC_END_GAME:
        EndGameDialog(0);
        break;
#endif
    default:
        interrupt_tick(SIM_RECOVERED_ENGINE_INVALID_ARGUMENT,
                       "invalid source action");
    }
    recovered_bind_end(&engine->binding_frame, &engine->recovered);
    engine->recovered_binding_active = 0;
    if (!sim_recovered_audio_unbind(&engine->audio_binding))
        abort();
    if (needs_nest) {
        nest_status = sim_recovered_nest_unbind(&engine->nest_binding);
        if (engine->nest_binding.calls != 0 && nest_status != SIM_NEST_OK) {
            engine->status = SIM_RECOVERED_ENGINE_NEST_ERROR;
            engine->failed_service = "source action nest transition";
        }
    }
    recovered_rng_bind(NULL);
    active_abort_target = NULL;
    active_engine = NULL;
    if (engine->status != SIM_RECOVERED_ENGINE_OK)
        return engine->status;
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
    if (needs_nest)
        (void)sim_recovered_nest_unbind(&engine->nest_binding);
    recovered_rng_bind(NULL);
    engine->session->rng = engine->rng_before_tick;
    engine->audio_intents = engine->audio_before_tick;
    active_abort_target = NULL;
    active_engine = NULL;
    return engine->status;
}

SimRecoveredEngineStatus sim_recovered_engine_proc_menu_command(
    SimRecoveredEngine *engine, uint16_t command)
{
    int16_t source_word;
    memcpy(&source_word, &command, sizeof(source_word));
    return sim_recovered_engine_action(engine, SIM_RECOVERED_ACTION_PROC_MENU,
                                        source_word, 0);
}

SimRecoveredEngineStatus sim_recovered_engine_history_event(
    SimRecoveredEngine *engine, uint16_t command)
{
    int16_t source_word;
    memcpy(&source_word, &command, sizeof source_word);
    return sim_recovered_engine_action(engine, SIM_RECOVERED_ACTION_HISTORY_EVENT,
                                       source_word, 0);
}

int sim_recovered_engine_history_ui_snapshot(const SimRecoveredEngine *engine,
    struct PortableHistoryUiSnapshot *ui, int16_t *shown_count)
{
    if (engine == NULL || !engine->initialized || ui == NULL || shown_count == NULL ||
        (active_engine != NULL && active_engine != engine)) return 0;
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
    return sim_recovered_source_history_ui_snapshot(ui, shown_count);
#else
    return 0;
#endif
}

SimRecoveredEngineStatus sim_recovered_engine_control_event(
    SimRecoveredEngine *engine, SimSetupControlKind kind,
    const SimControlEventMessage *message,
    SimControlEventPrivateState *private_state,
    const SimControlEventProvider *provider)
{
    struct SimRecoveredControlRequest request;
    SimRecoveredEngineStatus status;
    if (engine == NULL || !engine->initialized || engine->session == NULL ||
        message == NULL || private_state == NULL ||
        provider == NULL || engine->control_request != NULL ||
        active_engine != NULL || active_abort_target != NULL ||
        (kind != SIM_SETUP_MODE_CONTROL && kind != SIM_SETUP_CASTE_CONTROL))
        return SIM_RECOVERED_ENGINE_INVALID_ARGUMENT;
    request.kind = kind;
    request.message = message;
    request.private_state = private_state;
    request.provider = provider;
    engine->control_request = &request;
    status = sim_recovered_engine_action(engine,
                        SIM_RECOVERED_ACTION_CONTROL_EVENT, 0, 0);
    engine->control_request = NULL;
    return status;
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
