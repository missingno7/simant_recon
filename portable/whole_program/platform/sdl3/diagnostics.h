#ifndef SIMANT_SDL3_DIAGNOSTICS_H
#define SIMANT_SDL3_DIAGNOSTICS_H

#include <SDL3/SDL.h>
#include "host_modes.h"

void simant_diagnostics_init(int debug, const char *root);
void simant_diagnostics_note(const char *label, const char *value);
void simant_diagnostics_launch(const char *assets, uint32_t seed);
void simant_diagnostics_progress(const char *boundary, size_t replay, long loops);
void simant_diagnostics_close(int status, const char *reason);
/* Called after logical coordinate conversion, before DOS key filtering.
 * Scripted events are explicitly tagged by the application's injector. */
int simant_diagnostics_event(void *unused, const SDL_Event *event);
void simant_diagnostics_start(uint64_t now);
void simant_diagnostics_capture(Host *host, long loops);
__declspec(dllexport) __attribute__((noinline)) void simant_diagnostics_test_crash(void);
void simant_diagnostics_test_thread_crash(void);

#endif
