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
    assert(ws_resizable(WS_GAME) && ! ws_resizable(WS_MAP) && ! ws_closable(WS_STATUS) && ! ws_closable(WS_ANT));
    printf("{\"passed\":true,\"checks\":%u,\"operations\":\"attach/detach/move/resize/zoom/reset/persistence/rejection\"}\n", checks);
    return 0;
}
