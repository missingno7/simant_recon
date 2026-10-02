#ifndef SIMANT_TESTS_DIALOGS_MENU_QUIT_PROBE_H
#define SIMANT_TESTS_DIALOGS_MENU_QUIT_PROBE_H
#include <stddef.h>
#include <stdint.h>
#include "../../ui_model/dialogs/menu_quit.h"
#define MQ_MAX_PROMPTS 8
#define MQ_MAX_INPUTS 24
#define MQ_MAX_TRACE 512
#define MQ_TEXT_CAP 256
typedef struct {
    int16_t dirty, screen_width_metric;
    uint8_t frame_enabled, prompt_count;
    uint8_t key_count[MQ_MAX_PROMPTS], event_count[MQ_MAX_PROMPTS];
    int16_t keys[MQ_MAX_PROMPTS][MQ_MAX_INPUTS];
    int16_t events[MQ_MAX_PROMPTS][MQ_MAX_INPUTS];
    uint8_t save_count;
    int16_t saves[MQ_MAX_INPUTS];
    PortableMenuQuitRect window_rect, text_rect;
} MenuQuitProbeInput;
typedef struct {
    int16_t kind, argc;
    int32_t args[8];
    uint16_t text_length;
    char text[MQ_TEXT_CAP];
} MenuQuitProbeEvent;
typedef struct {
    int16_t status;
    int16_t choice;
    int16_t dirty_after;
    uint16_t event_count;
    MenuQuitProbeEvent events[MQ_MAX_TRACE];
} MenuQuitProbeResult;
int menu_quit_probe_load_resource(const char *database_root,
                                  char *buffer, size_t capacity,
                                  size_t *length);
int menu_quit_probe_run(const MenuQuitProbeInput *input,
                        const char *resource_text, size_t resource_length,
                        MenuQuitProbeResult *result);
#endif
