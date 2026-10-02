#include "history_adapter.h"

#include <stddef.h>

#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    uint16_t code;
    int16_t xE;
};

_Static_assert(sizeof(struct Event) == 16,
               "S24 Event must retain its DOS 16-byte record size");
_Static_assert(offsetof(struct Event, code) == 12,
               "S24 Event.code must remain the unsigned word at byte 12");
_Static_assert(offsetof(struct Event, xE) == 14,
               "S24 Event.xE must remain the following word at byte 14");

extern void ProcHistoryEvent(struct Event *event);
extern void S24_GetHistoryUiSnapshot(int16_t graph_colors[4],
    int16_t history_colors[10], int16_t shown_graphs[4],
    int16_t *shown_graph_count);

int sim_recovered_source_history_event(uint16_t command)
{
    struct Event event = {0};
    event.code = command;
    ProcHistoryEvent(&event);
    return 1;
}

int sim_recovered_source_history_ui_snapshot(
    PortableHistoryUiSnapshot *ui, int16_t *shown_graph_count)
{
    if (ui == NULL || shown_graph_count == NULL)
        return 0;
    S24_GetHistoryUiSnapshot(ui->graph_colors, ui->history_color,
                             ui->shown_graphs, shown_graph_count);
    return 1;
}
#else
int sim_recovered_source_history_event(uint16_t command)
{
    (void)command;
    return 0;
}

int sim_recovered_source_history_ui_snapshot(
    PortableHistoryUiSnapshot *ui, int16_t *shown_graph_count)
{
    (void)ui;
    (void)shown_graph_count;
    return 0;
}
#endif
