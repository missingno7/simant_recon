#ifndef SIMANT_SDL3_NATIVE_MENU_H
#define SIMANT_SDL3_NATIVE_MENU_H

#include <SDL3/SDL.h>
#include <stdint.h>

/* Native Windows menu bar on the main window from the game's menu resource
 * (g_6054), as Win16 SimAnt's InitMenu. Returns 0 where the video driver has
 * no native window (headless). */
void native_menu_theme_item(void *menu,unsigned position,const char *label);
int native_menu_theme_message(void *owner,unsigned message,intptr_t parameter);
int native_menu_init(SDL_Window *root);
void native_menu_shutdown(void);
/* (Re)build after the game loads or replaces its menu; 1 while a bar exists. */
int native_menu_sync(void);
void native_menu_remeasure(void);
/* Game event pump: post selected commands as the DOS pull-down does. */
void native_menu_pump(void);
/* Queue a menu choice: code 0xFD01 + (menu << 4) + item. */
int native_menu_command(int code);

#endif
