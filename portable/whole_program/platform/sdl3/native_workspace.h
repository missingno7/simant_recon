#ifndef SIMANT_NATIVE_WORKSPACE_H
#define SIMANT_NATIVE_WORKSPACE_H
#include <SDL3/SDL.h>
#include "portable/platform/host.h"
#include "portable/whole_program/enhanced/workspace.h"
#include "portable/whole_program/enhanced/snapshot.h"
int native_workspace_proximity(const EnhancedDialogsSnapshot *menu);
void native_workspace_anchor(int x,int y);
void native_workspace_activate_point(int x,int y);
void native_workspace_request_point(int *x,int *y);
int native_workspace_proximity_modifiers(void);
void native_workspace_place_prompt(SDL_Window *window);
int native_workspace_init(SDL_Window *root);
int native_workspace_active(void);
void native_workspace_shutdown(void);
void native_workspace_present(const HostPalette *palette);
/* 1 consumes workspace input. Scripted guest input remains at its existing boundary. */
int native_workspace_filter(const SDL_Event *);
/* A fixed neutral pointer while native layout owns physical input. */
int native_workspace_input(HostInputState *);
int native_workspace_operation(unsigned step);
int native_workspace_popup_paint(void *window,void *dc,int frame);
int native_workspace_content_paint(void *window,void *dc,int frame);
/* Indexed shipped art, preserving its source mask over the destination DC. */
int native_workspace_art_paint(void *dc,int id,int x,int y);
int native_workspace_capture(const char *path);
const Workspace *native_workspace_layout(void);
int native_workspace_apply(const Workspace *layout);
/* Attach the retained step B/C client to the same ordinary-window policy. */
void native_workspace_manage_window(SDL_Window *window,int logical,int width,int height);
int native_workspace_shortcut(unsigned message,uintptr_t key);
void native_workspace_reveal_game(void);

#endif
