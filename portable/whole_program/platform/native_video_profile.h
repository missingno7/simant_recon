#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_NATIVE_VIDEO_PROFILE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_NATIVE_VIDEO_PROFILE_H

#include "graphics.h"
#include "graphics_source_clip.h"

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* These logical presentation profiles are bound from the BIOS video mode the
 * source actually requests. They do not assert that physical hardware exists. */
typedef enum SimNativeVideoProfile {
    SIM_NATIVE_VIDEO_EGA_PROFILE_0 = 0,
    SIM_NATIVE_VIDEO_VGA_PROFILE_8 = 8
} SimNativeVideoProfile;

typedef enum SimNativeVideoStatus {
    SIM_NATIVE_VIDEO_OK = 0,
    SIM_NATIVE_VIDEO_INVALID_ARGUMENT,
    SIM_NATIVE_VIDEO_UNSUPPORTED_PROFILE,
    SIM_NATIVE_VIDEO_NOT_BOUND,
    SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY,
    SIM_NATIVE_VIDEO_GRAPHICS_FAILURE
} SimNativeVideoStatus;

/* Bind the host's virtual VGA capability and indexed graphics owner before
 * entering source gfx_select_driver_resources. The source callback adapter receives the typed
 * pointer-to-pointer slot for clip_active_list_offset; clip_active_list_segment is only the far-pointer segment
 * word and is never modeled as a separate native flag. The source ABI has no error return, so an
 * impossible unbound/rejected callback path terminates rather than returning a
 * fabricated probe or successful mode change.
 */
SimNativeVideoStatus sim_native_video_startup_bind(SimGraphicsDriver *graphics);
void sim_native_video_startup_unbind(void);
SimNativeVideoStatus sim_native_video_startup_status(void);
typedef int (*SimNativeVideoInstallServices)(void *context,
                                             SimGraphicsDriver *graphics,
                                             SimNativeVideoProfile profile);
typedef void (*SimNativeVideoUninstallServices)(void *context);
/* The full application installs capture, raster logic, tile cache and native
 * presentation services after the source selects its real logical mode.
 * Focused startup controls may bind only the common graphics boundary. */
SimNativeVideoStatus sim_native_video_set_mode_services(
    SimNativeVideoInstallServices install, SimNativeVideoUninstallServices uninstall,
    void *context);

/* Source-compatible host providers referenced by root:m205F. */
int16_t gfx_probe_display_adapters(void);
int16_t gfx_bios_has_tandy_signature(void);
void gfx_reset_driver_callbacks(void);
void gfx_planar_init_640x350(void);
void gfx_planar_init_640x480(void);

#ifdef __cplusplus
}
#endif
#endif
