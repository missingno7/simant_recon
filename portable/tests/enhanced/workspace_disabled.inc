/* Host-only device fixtures deliberately have no workspace/UI dependency. */
#include "portable/whole_program/platform/sdl3/native_workspace.h"
int native_workspace_active(void) { return 0; }
int native_workspace_filter(const SDL_Event *event) { (void)event;return 0; }
int native_workspace_input(HostInputState *state) { (void)state;return 0; }
void native_workspace_present(const HostPalette *palette) { (void)palette; }

void native_workspace_manage_window(SDL_Window *window,int logical,int width,int height){(void)window;(void)logical;(void)width;(void)height;}
int native_workspace_shortcut(unsigned message,uintptr_t key){(void)message;(void)key;return 0;}

void native_workspace_reveal_game(void){}
int enhanced_pointer_input(HostInputState *state){(void)state;return 0;}
void enhanced_pointer_poll(void){}
void enhanced_pointer_external_release(void){}
