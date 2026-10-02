#include "recovered_state.h"
#include "portable/game/recovered/engine.h"
#include "portable/game/recovered/menu_adapter.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

struct S11MenuEvent {
    int16_t what;
    int16_t where[2];
    int16_t when[2];
    int16_t modifiers;
    int16_t message;
};

_Static_assert(sizeof(struct S11MenuEvent) == 14, "S11 event width");
_Static_assert(offsetof(struct S11MenuEvent, message) == 12,
               "S11 ProcMenu reads message at byte 12");
_Static_assert(sizeof(SimRecoveredEvent) == 16, "S22 packed event width");
_Static_assert(offsetof(SimRecoveredEvent, message) == 2,
               "S22 packed event message is at byte 2");

enum {
    HOST_ABOUT = 1, HOST_BEGIN_SONG, HOST_NEW_GAME, HOST_OPEN_EDIT,
    HOST_OPEN_MAP_YARD, HOST_OPEN_MODE, HOST_OPEN_CASTE, HOST_OPEN_HISTORY,
    HOST_OPEN_INFO, HOST_SCORE, HOST_SET_YARD_MODE, HOST_SET_MAP_PLANE,
    HOST_IS_WINDOW_OPEN, HOST_MAP_TO_YARD, HOST_STOP_SONG,
    HOST_MENU_ITEM_STATE, HOST_MENU_TEXT, HOST_EDIT_MESSAGE,
    HOST_CLIP_SET_WIN, HOST_OBJECT_SELECTED, HOST_CLIP_OFF,
    HOST_END_LIFE_TRANSFER, HOST_END_TARGET
};

typedef struct ProcMenuInput {
    int16_t command_id;
    int16_t scenario_state;
    int16_t paused;
    int16_t current_tool;
    int16_t map_plane;
    int16_t yard_mode;
    int16_t speed;
    int16_t yard_window_open;
    int16_t new_game_return;
    int16_t option_states[7];
} ProcMenuInput;

typedef struct ProcMenuHostEvent {
    int16_t kind;
    int32_t args[4];
} ProcMenuHostEvent;

typedef struct ProcMenuOutput {
    int16_t scenario_state;
    int16_t paused;
    int16_t current_tool;
    int16_t map_plane;
    int16_t yard_mode;
    int16_t speed;
    int16_t option_states[7];
    uint16_t host_count;
    ProcMenuHostEvent host[32];
} ProcMenuOutput;

static ProcMenuOutput *active_output;
static const ProcMenuInput *active_input;
static const char *advice_slots[18];
static const char *const advice_text[18] = {
    "AdviceSlot0", "AdviceSlot1", "AdviceSlot2", "AdviceSlot3",
    "AdviceSlot4", "AdviceSlot5", "AdviceSlot6", "AdviceSlot7",
    "AdviceSlot8", "AdviceSlot9", "AdviceSlot10", "AdviceSlot11",
    "AdviceSlot12", "AdviceSlot13", "AdviceSlot14", "AdviceSlot15",
    "AdviceSlot16", "AdviceSlot17"
};

extern void ProcMenu(struct S11MenuEvent *event);

static void hydrate(const ProcMenuInput *input)
{
    int i;
    for (i = 0; i < 18; ++i) advice_slots[i] = advice_text[i];
    MapPlane = input->map_plane;
    YardMode = input->yard_mode;
    fd_55B3_2CBC = input->scenario_state;
    fd_50F6_047E = input->paused;
    fd_50F6_105E = input->current_tool;
    fd_3D57_07CC[0] = input->speed;
    memcpy(fd_3D57_07A8, input->option_states, sizeof(input->option_states));
    fd_50F6_034C = (void **)advice_slots;
}

static void host(int16_t kind, int32_t a, int32_t b, int32_t c, int32_t d)
{
    ProcMenuHostEvent *event;
    if (active_output == NULL || active_output->host_count >= 32) return;
    event = &active_output->host[active_output->host_count++];
    event->kind = kind;
    event->args[0] = a;
    event->args[1] = b;
    event->args[2] = c;
    event->args[3] = d;
}

void AboutDialog(void) { host(HOST_ABOUT, 0, 0, 0, 0); }
void myBeginSong(int16_t id, int16_t arg) { host(HOST_BEGIN_SONG, id, arg, 0, 0); }
int16_t NewGame(int16_t arg)
{
    host(HOST_NEW_GAME, arg, 0, 0, 0);
    return active_input->new_game_return;
}
void OpenEditWindow(void) { host(HOST_OPEN_EDIT, 0, 0, 0, 0); }
void OpenMapYard(void) { host(HOST_OPEN_MAP_YARD, 0, 0, 0, 0); }
void OpenModeWindow(void) { host(HOST_OPEN_MODE, 0, 0, 0, 0); }
void OpenCasteWindow(void) { host(HOST_OPEN_CASTE, 0, 0, 0, 0); }
void OpenHistoryWindow(void) { host(HOST_OPEN_HISTORY, 0, 0, 0, 0); }
void OpenInfoWindow(void) { host(HOST_OPEN_INFO, 0, 0, 0, 0); }
void ScoreDialog(void) { host(HOST_SCORE, 0, 0, 0, 0); }
void SetYardMode(int16_t mode) { host(HOST_SET_YARD_MODE, mode, 0, 0, 0); }
void SetMapPlane(int16_t plane) { host(HOST_SET_MAP_PLANE, plane, 0, 0, 0); }
int16_t win_IsWinOpen(int16_t id)
{
    host(HOST_IS_WINDOW_OPEN, id, 0, 0, 0);
    return active_input->yard_window_open;
}
void MapToYard(void) { host(HOST_MAP_TO_YARD, 0, 0, 0, 0); }
void StopSong(void) { host(HOST_STOP_SONG, 0, 0, 0, 0); }
void SetMenuItemState(int16_t id, int16_t state)
{ host(HOST_MENU_ITEM_STATE, id, state, 0, 0); }
void f_1FD2_0135(int16_t id, char *text)
{
    int32_t text_id = strcmp(text, " Pause") == 0 ? 1
                    : strcmp(text, " Unpause") == 0 ? 2 : -1;
    host(HOST_MENU_TEXT, id, text_id, 0, 0);
}
void EditMessage(void *message, int32_t ticks, int16_t mode)
{
    int32_t slot = message == NULL ? -1 : -2;
    int i;
    for (i = 0; i < 18; ++i)
        if (message == advice_slots[i]) slot = i;
    host(HOST_EDIT_MESSAGE, slot, ticks, mode, 0);
}
void clip_SetWin(int16_t win) { host(HOST_CLIP_SET_WIN, win, 0, 0, 0); }
void win_SetObjSelectedState(int16_t obj, int16_t state)
{ host(HOST_OBJECT_SELECTED, obj, state, 0, 0); }
void clip_Off(void) { host(HOST_CLIP_OFF, 0, 0, 0, 0); }
void EndLifeTransferMode(void) { host(HOST_END_LIFE_TRANSFER, 0, 0, 0, 0); }
void EndTargetMode(void) { host(HOST_END_TARGET, 0, 0, 0, 0); }

int procmenu_native_run(const ProcMenuInput *input, ProcMenuOutput *output)
{
    uint16_t command;
    if (input == NULL || output == NULL) return -1;
    memset(output, 0, sizeof(*output));
    active_output = output;
    active_input = input;
    hydrate(input);
    command = (uint16_t)input->command_id;
    sim_recovered_source_proc_menu_command(command);
    output->scenario_state = fd_55B3_2CBC;
    output->paused = fd_50F6_047E;
    output->current_tool = fd_50F6_105E;
    output->map_plane = MapPlane;
    output->yard_mode = YardMode;
    output->speed = fd_3D57_07CC[0];
    memcpy(output->option_states, fd_3D57_07A8, sizeof(output->option_states));
    active_output = NULL;
    active_input = NULL;
    return 0;
}

/* Negative ABI control: deliberately pass S22's event shape directly to S11.
 * For command 1, the S22 message is at +2 while S11 reads the zero code word
 * at +12, so AboutDialog must not be reached. */
int procmenu_native_s22_layout_negative(const ProcMenuInput *input,
                                         ProcMenuOutput *output)
{
    SimRecoveredEvent event = {0};
    if (input == NULL || output == NULL) return -1;
    memset(output, 0, sizeof(*output));
    active_output = output;
    active_input = input;
    hydrate(input);
    event.message = input->command_id;
    ProcMenu((struct S11MenuEvent *)(void *)&event);
    output->scenario_state = fd_55B3_2CBC;
    output->paused = fd_50F6_047E;
    output->current_tool = fd_50F6_105E;
    output->map_plane = MapPlane;
    output->yard_mode = YardMode;
    output->speed = fd_3D57_07CC[0];
    memcpy(output->option_states, fd_3D57_07A8, sizeof(output->option_states));
    active_output = NULL;
    active_input = NULL;
    return 0;
}
