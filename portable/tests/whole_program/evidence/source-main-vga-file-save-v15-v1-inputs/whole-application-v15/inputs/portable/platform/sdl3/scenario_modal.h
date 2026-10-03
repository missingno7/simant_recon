#ifndef SIMANT_PORTABLE_SDL3_SCENARIO_MODAL_H
#define SIMANT_PORTABLE_SDL3_SCENARIO_MODAL_H

#include "../host.h"
#include "../../render/palette.h"
#include "../../game/resources/fonts.h"
#include "../../ui_model/windows/open.h"
#include "../../ui_model/windows/render.h"
#include "../../ui_model/dialogs/scenario_flow.h"

typedef enum PortableScenarioModalStatus {
    PORTABLE_SCENARIO_MODAL_SELECTED = 0,
    PORTABLE_SCENARIO_MODAL_CANCELLED,
    PORTABLE_SCENARIO_MODAL_QUIT_REJECTED,
    PORTABLE_SCENARIO_MODAL_BAD_ARGUMENT,
    PORTABLE_SCENARIO_MODAL_OUT_OF_MEMORY,
    PORTABLE_SCENARIO_MODAL_REGISTRY_ERROR,
    PORTABLE_SCENARIO_MODAL_UNSUPPORTED_GEOMETRY,
    PORTABLE_SCENARIO_MODAL_OPEN_ERROR,
    PORTABLE_SCENARIO_MODAL_RENDER_ERROR,
    PORTABLE_SCENARIO_MODAL_HOST_ERROR,
    PORTABLE_SCENARIO_MODAL_INPUT_OVERFLOW,
    PORTABLE_SCENARIO_MODAL_CLOSE_ERROR,
    PORTABLE_SCENARIO_MODAL_RESTORE_ERROR
} PortableScenarioModalStatus;

/* DOS TickCount provider. The modal does not infer simulation time from SDL. */
typedef uint32_t (*PortableScenarioModalTickSource)(void *context);
typedef int (*PortableScenarioModalRedraw)(void *context,
                                           PortableWindowRenderer *renderer);

typedef struct PortableScenarioModalRequest {
    PortableWindowRegistry *registry;
    PortableWindowOpenScene *open_scene;
    const PortablePalette *palette;
    const PortableFontSet *fonts;
    const PortableWindowRenderer *renderer;
    int16_t screen_width, screen_height;
    PortableWindowRect menu_rect;
    PortableScenarioModalTickSource tick_count;
    void *clock_context;
    PortableScenarioModalRedraw redraw_background;
    void *redraw_context;
    volatile int *quit_flag;
} PortableScenarioModalRequest;

/* Opens real resource window 0x0200 in the caller's window manager, renders
 * its decoded objects, and translates left-button hits to source event codes
 * 0x0200 + object index. BIOS keydowns are retained separately from window
 * event flushing. The returned code is written only for SELECTED/CANCELLED;
 * 0x0207 remains unchanged for NewGame's file-load service. */
PortableScenarioModalStatus portable_scenario_modal_run(
    Host *host, const PortableScenarioModalRequest *request,
    uint16_t *result_code);

const char *portable_scenario_modal_status_string(
    PortableScenarioModalStatus status);

#endif
