#ifndef SIMANT_WORKSPACE_H
#define SIMANT_WORKSPACE_H
#include <stdio.h>
/* Host-only layout. IDs describe native instances, never logical windows. */
enum { WS_NODES=48, WS_PANELS=24, WS_TABS=24, WS_FLOATS=8 };
enum { WS_LEFT,WS_RIGHT,WS_TOP,WS_BOTTOM,WS_STACK };
typedef struct WsNode {
    int kind,axis,ratio,a,b; /* 0 unused, 1 tabs, 2 split; axis 0 horizontal */
    int count,active,collapsed,panels[WS_TABS];
} WsNode;
typedef struct WsPanel { int plane,x,y,zoom,home; } WsPanel;
typedef struct WsFloat { int root,x,y,w,h; char monitor[64]; } WsFloat;
typedef struct Workspace {
    int root; WsNode nodes[WS_NODES]; WsPanel panels[WS_PANELS];
    WsFloat floats[WS_FLOATS]; unsigned revision;
} Workspace;
const char *ws_name(int panel);
void ws_preset(Workspace *,int preset); /* Play, Colony, Research, Minimal */
int ws_group(const Workspace *,int panel);
int ws_move(Workspace *,int panel,int target,int edge,int outer);
int ws_float(Workspace *,int panel,int x,int y,int w,int h);
int ws_hide(Workspace *,int panel);
int ws_reveal(Workspace *,int panel);
int ws_collapse(Workspace *,int group);
void ws_prompt(Workspace *,int active);
int ws_validate(const Workspace *);
int ws_write(const Workspace *,FILE *);
int ws_read(Workspace *,FILE *); /* transactional, rejects unknown schema/IDs/cycles */
void ws_exercise(Workspace *,unsigned step); /* same operations for passive probes */
#endif
