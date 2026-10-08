#ifndef SIMANT_SDL3_NATIVE_WINDOWS_H
#define SIMANT_SDL3_NATIVE_WINDOWS_H

#include "portable/platform/host.h"
#include <SDL3/SDL.h>

/* Modern presentation: each hosted logical window (window_hosting.h) is an
 * owned, decorated SDL window showing its own planes at the global scale, and
 * each save-under box a native popup; the main SDL window keeps the desktop,
 * the menu bar and windows that are not hosted. */
int native_windows_init(Host *host, SDL_Window *root);
int native_windows_active(void);
int native_windows_scale(void);
void native_windows_shutdown(void);
/* Present every open hosted window; show/hide/size follow the logical state. */
int native_windows_present(const HostPalette *palette);
/* Converts a hosted window's pointer event to logical screen coordinates and
 * applies the raise rule; consumes close/resize requests. Returns 1 handled,
 * 0 not a hosted window, -1 drop. */
int native_windows_translate(SDL_Event *event);
/* Root window pointer filter after render conversion: -1 drops a click whose
 * logical point belongs to a hosted window. */
int native_windows_filter_root(SDL_Event *event);
/* Logical pointer position when the mouse is over a hosted window. */
int native_windows_pointer(float *x, float *y);
/* Native close button / sizing frame of hosted window `id` (also replay). */
int native_windows_request_close(int16_t id);
int native_windows_request_resize(int16_t id, int width, int height);
/* Saves each shown hosted window as <base_path>.<ID>.bmp (smoke captures). */
int native_windows_save_frames(const char *base_path);
/* Test/replay input at window-local logical client coordinates of window `id`. */
int native_windows_push_pointer(int16_t id, const HostEvent *event);
/* For input recording: the hosted window an SDL event came from. */
int native_windows_event_origin(SDL_WindowID window, int16_t *id, int16_t *left, int16_t *top);

#endif
