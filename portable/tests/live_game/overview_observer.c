/* Test-only diagnostics linker input; it pushes no SDL event. */
#include <stdio.h>
#include <stdlib.h>

__attribute__((destructor)) static void write_overview_observer_count(void)
{
    const char *path = getenv("SIMANT_LIVE_SMOKE_EVENT_REPORT");
    FILE *file;
    if (path == NULL || path[0] == '\0') return;
    file = fopen(path, "wb");
    if (file == NULL) return;
    (void)fputs("0\n", file);
    (void)fclose(file);
}
