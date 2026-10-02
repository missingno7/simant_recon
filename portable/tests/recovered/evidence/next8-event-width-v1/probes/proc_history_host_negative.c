#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    unsigned code;
    int16_t xE;
};

static int trace[32][4];
static int trace_count;
static void record(int id, int a, int b, int c) {
    trace[trace_count][0] = id; trace[trace_count][1] = a;
    trace[trace_count][2] = b; trace[trace_count][3] = c; ++trace_count;
}
static int16_t shownGraphs[4] = {(int16_t)0x8000, (int16_t)0x8000,
                                 (int16_t)0x8000, (int16_t)0x8000};
void DoWinHelp(int16_t a) { record(1, a, 0, 0); }
void ToggleHistButton(int16_t a) { record(2, a, 0, 0); }
void clip_SetWin(int16_t a) { record(3, a, 0, 0); }
int16_t f_1B4E_000D(int16_t a) { record(4, a, 0, 0); return 7; }
void win_FillObjRect(int16_t a, int16_t b) { record(5, a, b, 0); }
void drawHistGraph(int16_t a, int16_t b, int16_t c) { record(6, a, b, c); }
int16_t StillDown(void) { record(7, 0, 0, 0); return 0; }
void win_DrawHistoryWindow(int16_t a) { record(8, a, 0, 0); }
void clip_Off(void) { record(9, 0, 0, 0); }


void  ProcHistoryEvent(struct Event  *ev)
{
    int16_t i;

    switch (ev->code) {
    case 0x150d:
        DoWinHelp(0x150f);
        break;
    case 0x150e:
        clip_SetWin(0x1500);
        win_FillObjRect(0x150e, f_1B4E_000D(0));
        for (i = 0; i < 4; i++)
            if (shownGraphs[i] != (int16_t)0x8000)
                drawHistGraph(shownGraphs[i], 1, i);
        while (StillDown())
            ;
        win_DrawHistoryWindow(3);
        clip_Off();
        break;
    default:
        if (ev->code >= 0x1503 && ev->code <= 0x150c)
            ToggleHistButton(ev->code);
        break;
    }
}

int main(int argc, char **argv) {
    union { long double align; uint8_t bytes[16]; } event_storage;
    int code, xE, i;
    struct Event event;
    if (argc != 3) return 90;
    code = (int)strtol(argv[1], 0, 0); xE = (int)strtol(argv[2], 0, 0);
    memset(&event_storage, 0, sizeof event_storage);
    event_storage.bytes[12] = (uint8_t)code;
    event_storage.bytes[13] = (uint8_t)(code >> 8);
    event_storage.bytes[14] = (uint8_t)xE;
    event_storage.bytes[15] = (uint8_t)(xE >> 8);
    memset(&event, 0, sizeof event);
    memcpy(&event, event_storage.bytes, sizeof event_storage.bytes);
    ProcHistoryEvent(&event);
    for (i = 0; i < trace_count; ++i)
        printf("%d,%d,%d,%d\n", trace[i][0], trace[i][1], trace[i][2], trace[i][3]);
    return 0;
}
