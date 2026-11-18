#include "portable/whole_program/enhanced/workspace.h"
#include <assert.h>
#include <string.h>
int main(int argc, char * * argv) {
    assert(argc == 2);
    Workspace w, copy, bad;
    ws_reset(& w);
    unsigned checks = 0;
    for (unsigned i = 0; i < 12000; ++ i) {
        ws_exercise(& w, i);
        assert(ws_validate(& w));
        ++ checks;
    }
    assert(ws_attach(& w, WS_MAP, WS_RIGHT, 300));
    assert(ws_attach(& w, WS_ANT, WS_TOP, 4));
    assert(ws_detach(& w, WS_MAP));
    FILE * f = fopen(argv [1], "w+");
    assert(f && ws_write(& w, f));
    rewind(f);
    assert(ws_read(& copy, f));
    fclose(f);
    copy.revision = w.revision;
    assert(! memcmp(& w, & copy, sizeof (w)));
    ++ checks;
    bad = w;
    bad.panels [0].edge = 99;
    assert(! ws_validate(& bad));
    bad = w;
    bad.panels [0].zoom = 0;
    assert(! ws_validate(& bad));
    const char * invalid [] = {
        "SIMANT-WORKSPACE 1\n", "SIMANT-WINDOWS 99\n", "garbage"
    };
    for (unsigned i = 0; i < 3; ++ i) {
        f = fopen(argv [1], "w+");
        assert(f);
        fputs(invalid [i], f);
        rewind(f);
        bad = w;
        assert(! ws_read(& bad, f));
        assert(! memcmp(& bad, & w, sizeof (w)));
        fclose(f);
        ++ checks;
    }
    f = fopen(argv [1], "w+");
    assert(f && ws_write(& w, f));
    fputs("trailing data", f);
    rewind(f);
    assert(! ws_read(& copy, f));
    fclose(f);
    ++ checks;
    const int percentages[]={0,100,125,150,175,200,250,300};
    for(unsigned i=0;i<8;++i){w.ui_scale=percentages[i];f=fopen(argv[1],"w+");assert(f&&ws_write(&w,f));rewind(f);assert(ws_read(&copy,f)&&copy.ui_scale==w.ui_scale);fclose(f);++checks;}
    bad=w;bad.ui_scale=130;assert(!ws_validate(&bad));++checks;
    /* Read existing v2 layouts as Auto without altering their frame data. */
    f=fopen(argv[1],"w+");assert(f);fprintf(f,"SIMANT-WINDOWS 2\n");
    for(int i=0;i<WS_PANELS;++i){WsPanel *p=&w.panels[i];fprintf(f,"%d %d %d %d %d %d %d %d %d %d %s\n",p->x,p->y,p->w,p->h,p->edge,p->offset,p->visible,p->camera_x,p->camera_y,p->zoom,p->monitor[0]?p->monitor:"-");}
    rewind(f);assert(ws_read(&copy,f)&&copy.ui_scale==0&&!memcmp(w.panels,copy.panels,sizeof(w.panels)));fclose(f);++checks;
    assert(ws_resizable(WS_GAME) && ! ws_resizable(WS_MAP) && ! ws_closable(WS_STATUS) && ! ws_closable(WS_ANT));
    printf("{\"passed\":true,\"checks\":%u,\"operations\":\"attach/detach/move/resize/zoom/reset/persistence/rejection\"}\n", checks);
    return 0;
}
