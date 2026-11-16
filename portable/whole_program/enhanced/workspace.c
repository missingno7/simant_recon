#include "workspace.h"
#include <string.h>
static const char * names [WS_PANELS] = {
    "SimAnt - Game", "SimAnt - Black Nest", "SimAnt - Red Nest", "", "Map / Ant Control Panel", "Yard Control Panel", "Map", "Yard", "Behavior Control", "Caste Control", "History", "Info", "Status", "Help", "Prompt", "About"
};
const char * ws_name(int p) {
    return p >= 0 && p < WS_PANELS ? (names [p] ? names [p] : "SimAnt") : "";
}
int ws_resizable(int p) {
    return p >= WS_GAME && p <= WS_RED;
}
int ws_closable(int p) {
    return p != WS_ANT && p != WS_YARD_CONTROL && p != WS_STATUS && p != 14;
}
void ws_reset(Workspace * w) {
    memset(w, 0, sizeof (* w));
    for (int i = 0; i < WS_PANELS; ++ i) w->panels [i] = (WsPanel) {
        .x = 30 + i * 16,.y = 180 + i * 12,.w = 340,.h = 240,.edge = WS_FLOAT,.zoom = 100,.camera_x = - 1,.camera_y = - 1
    };
    w->panels [WS_GAME] = (WsPanel) {
        .x = 26,.y = 210,.w = 460,.h = 370,.edge = WS_FLOAT,.visible = 1,.zoom = 100,.camera_x = - 1,.camera_y = - 1
    };
    w->panels [WS_BLACK] = (WsPanel) {
        .x = 26,.y = 600,.w = 380,.h = 300,.edge = WS_FLOAT,.zoom = 100,.camera_x = 400,.camera_y = 0
    };
    w->panels [WS_RED] = w->panels [WS_BLACK];
    w->panels [WS_RED].x = 420;
    w->panels [WS_ANT] = (WsPanel) {
        .x = 18,.y = 54,.w = 960,.h = 144,.edge = WS_FLOAT,.visible = 1,.zoom = 100
    };
    w->panels [WS_YARD_CONTROL] = (WsPanel) {
        .x = 18,.y = 920,.w = 960,.h = 120,.edge = WS_FLOAT,.visible = 1,.zoom = 100
    };
    w->panels [WS_MAP].x = 510;
    w->panels [WS_MAP].y = 210;
    w->panels [WS_BEHAVIOR].x = 26;
    w->panels [WS_BEHAVIOR].y = 600;
    w->panels [WS_CASTE].x = 280;
    w->panels [WS_CASTE].y = 600;
    w->panels [WS_HISTORY].x = 510;
    w->panels [WS_HISTORY].y = 530;
    w->panels [WS_INFO].x = 510;
    w->panels [WS_INFO].y = 760;
    for (int i = 16; i < WS_PANELS; ++ i) {
        w->panels [i].x = 220;
        w->panels [i].y = 160;
    }
    ++ w->revision;
}
int ws_attach(Workspace * w, int p, int edge, int offset) {
    if (p < 0 || p >= WS_PANELS || edge < WS_LEFT || edge > WS_BOTTOM || offset < 0 || offset > 10000) return 0;
    w->panels [p].edge = edge;
    w->panels [p].offset = offset;
    ++ w->revision;
    return 1;
}
int ws_detach(Workspace * w, int p) {
    if (p < 0 || p >= WS_PANELS) return 0;
    w->panels [p].edge = WS_FLOAT;
    ++ w->revision;
    return 1;
}
int ws_validate(const Workspace * w) {
    for (int i = 0; i < WS_PANELS; ++ i) {
        const WsPanel * p = & w->panels [i];
        if (p->x < - 100000 || p->x > 100000 || p->y < - 100000 || p->y > 100000 || p->w < 80 || p->w > 10000 || p->h < 60 || p->h > 10000 || p->edge < WS_FLOAT || p->edge > WS_BOTTOM || p->offset < 0 || p->offset > 10000 || p->visible < 0 || p->visible > 1 || p->zoom < 25 || p->zoom > 800 || p->camera_x < - 1 || p->camera_x > 2047 || p->camera_y < - 1 || p->camera_y > 1023 || ! memchr(p->monitor, 0, 64)) return 0;
    }
    return 1;
}
int ws_write(const Workspace * w, FILE * f) {
    if (! ws_validate(w)) return 0;
    fprintf(f, "SIMANT-WINDOWS 2\n");
    for (int i = 0; i < WS_PANELS; ++ i) {
        const WsPanel * p = & w->panels [i];
        fprintf(f, "%d %d %d %d %d %d %d %d %d %d %s\n", p->x, p->y, p->w, p->h, p->edge, p->offset, p->visible, p->camera_x, p->camera_y, p->zoom, p->monitor [0] ? p->monitor : "-");
    }
    return ! ferror(f);
}
int ws_read(Workspace * w, FILE * f) {
    Workspace c = {
        0
    };
    char magic [32], tail;
    int version;
    if (fscanf(f, "%31s%d", magic, & version) != 2 || strcmp(magic, "SIMANT-WINDOWS") || version != 2) return 0;
    for (int i = 0; i < WS_PANELS; ++ i) {
        WsPanel * p = & c.panels [i];
        if (fscanf(f, "%d%d%d%d%d%d%d%d%d%d%63s", & p->x, & p->y, & p->w, & p->h, & p->edge, & p->offset, & p->visible, & p->camera_x, & p->camera_y, & p->zoom, p->monitor) != 11) return 0;
        if (! strcmp(p->monitor, "-")) p->monitor [0] = 0;
    }
    if (fscanf(f, " %c", & tail) == 1 || ! ws_validate(& c)) return 0;
    * w = c;
    return 1;
}
void ws_exercise(Workspace * w, unsigned step) {
    switch (step % 8) {
        case 0 :
        ws_attach(w, WS_ANT, WS_TOP, 4);
        break;
        case 1 :
        ws_attach(w, WS_MAP, WS_RIGHT, 180);
        break;
        case 2 :
        ws_detach(w, WS_MAP);
        break;
        case 3 :
        w->panels [WS_GAME].w = 520;
        w->panels [WS_GAME].h = 400;
        break;
        case 4 :
        w->panels [WS_GAME].zoom = 300;
        break;
        case 5 :
        w->panels [WS_GAME].zoom = 50;
        break;
        case 6 :
        ws_detach(w, WS_ANT);
        w->panels [WS_ANT].x = 60;
        break;
        case 7 :
        ws_reset(w);
        break;
    }
}
