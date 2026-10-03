#include "portable/whole_program/platform/handles.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    char **h;
    FILE *f;
    char text[2048];
    size_t n;
    assert(sim_handles_global_configure(4096, 16) == SIM_HANDLE_OK);
    h = f_171C_13CA(37, SIM_HANDLE_SOFT, "dump-soft");
    assert(h && f_171C_1B84(h));
    assert(f_171C_1BBA(h));
    assert(sim_handles_dump("handle-dump-test.txt", "test-point"));
    assert(sim_handles_global_last_status() == SIM_HANDLE_OK);
    f = fopen("handle-dump-test.txt", "rb");
    assert(f);
    n = fread(text, 1, sizeof(text) - 1, f);
    fclose(f);
    text[n] = '\0';
    assert(strstr(text, "Ralloc native handle dump at test-point"));
    assert(strstr(text, "size=37"));
    assert(strstr(text, "SOFT"));
    assert(strstr(text, "age=") || strstr(text, "name="));
    remove("handle-dump-test.txt");
    f_171C_13E4(h);
    puts("native handle dump inventory test passed");
    return 0;
}
