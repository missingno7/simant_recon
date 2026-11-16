#ifndef SIMANT_WORKSPACE_H
#define SIMANT_WORKSPACE_H
#include <stdio.h>
/* Host state only. Each record is one ordinary titled window, never a tab. */
enum { WS_PANELS=64 };
enum { WS_FLOAT=-1, WS_LEFT, WS_RIGHT, WS_TOP, WS_BOTTOM };
enum { WS_GAME, WS_BLACK, WS_RED, WS_RESERVED, WS_ANT, WS_YARD_CONTROL,
       WS_MAP, WS_YARD, WS_BEHAVIOR, WS_CASTE, WS_HISTORY, WS_INFO, WS_STATUS };
typedef struct WsPanel {
    int x,y,w,h,edge,offset,visible; /* frame bounds/work-area relative, DIP */
    int camera_x,camera_y,zoom;
    char monitor[64];
} WsPanel;
typedef struct Workspace { WsPanel panels[WS_PANELS]; unsigned revision; } Workspace;
const char *ws_name(int panel);
int ws_resizable(int panel);
int ws_closable(int panel);
void ws_reset(Workspace *);
int ws_attach(Workspace *,int panel,int edge,int offset);
int ws_detach(Workspace *,int panel);
int ws_validate(const Workspace *);
int ws_write(const Workspace *,FILE *);
int ws_read(Workspace *,FILE *); /* transactional; v1 split layouts are rejected */
void ws_exercise(Workspace *,unsigned step); /* actual passive operations */
#endif
