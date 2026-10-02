#include "../../../ui_model/windows/control_render/control_raster.h"
#include "../../../ui_model/windows/control_render/control_input_from_session.h"
#include "../../../game/resources/fonts.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct SetupContext {
    PortableDatabase *database;
    PortableWindowRegistry *registry;
} SetupContext;

static int setup_resource(void *context, uint16_t id, uint16_t kind,
                          int16_t *width, int16_t *height)
{
    SetupContext *setup = (SetupContext *)context;
    PortableDatabase *db = setup->database;
    PortableDbRecord record = {0};
    PortableBitmap bitmap;
    int ok = 0;
    if (kind != 2 || portable_db_load(db, (int16_t)id, kind, &record) !=
                     PORTABLE_DB_OK)
        return 0;
    if (portable_bitmap_view(record.data, record.size, &bitmap) == PORTABLE_RENDER_OK &&
        bitmap.width <= INT16_MAX && bitmap.height <= INT16_MAX) {
        *width = (int16_t)bitmap.width;
        *height = (int16_t)bitmap.height;
        ok = 1;
    }
    portable_db_record_free(&record);
    return ok;
}

static int setup_rect(void *context, uint16_t object_id, SimSetupRect *out)
{
    SetupContext *setup = (SetupContext *)context;
    PortableWindowRegistry *registry = setup->registry;
    PortableWindowRect rect;
    if (portable_window_registry_get_object_rect(registry, object_id, &rect) !=
        PORTABLE_WINDOW_REGISTRY_OK)
        return 0;
    *out = (SimSetupRect){rect.left, rect.top, rect.right, rect.bottom};
    return 1;
}

static int setup_refresh(void *context, SimSetupControlKind kind,
                         const SimSetupControls *controls)
{
    (void)context;
    (void)kind;
    return controls != NULL;
}

static int test_animation_resolver(void *state, uint16_t set, uint16_t object,
                                   const uint8_t **bytes, size_t *size)
{
    (void)state; (void)set; (void)object; (void)bytes; (void)size;
    return 0;
}

static uint64_t hash_bytes(const uint8_t *bytes, size_t size)
{
    size_t i;
    uint64_t hash = 14695981039346656037ull;
    for (i = 0; i < size; ++i) {
        hash ^= bytes[i];
        hash *= 1099511628211ull;
    }
    return hash;
}

int main(int argc, char **argv)
{
    char root[1024];
    PortableDatabase database = {0};
    PortableDbRecord colors = {0};
    PortableWindowRegistry registry = {0};
    PortableWindowRenderer renderer = {0};
    PortableFontSet fonts;
    PortableFramebuffer framebuffer;
    SimControlRasterContext raster = {0};
    SimControlRenderBinding binding;
    SimControlRenderInput input = {0};
    SimControlRecoveredVisualState recovered = {1, 1, {10, 20, 30}};
    SimSession session = {0};
    SimSetupControls controls = {0};
    SimSetupHooks hooks = {0};
    SetupContext setup_context = {&database, &registry};
    uint8_t *pixels;
    size_t nonzero = 0, i;
    assert(argc == 2);
    assert(snprintf(root, sizeof(root), "%s/HCEGANT", argv[1]) < (int)sizeof(root));
    assert(portable_db_open(&database, root) == PORTABLE_DB_OK);
    assert(portable_db_load(&database, 0x81, 0, &colors) == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    {
        PortableDbRecord knob = {0};
        PortableBitmap bitmap;
        assert(portable_db_load(&database, 0x578, 2, &knob) == PORTABLE_DB_OK);
        assert(portable_bitmap_view(knob.data, knob.size, &bitmap) == PORTABLE_RENDER_OK);
        assert(knob.id == 0x578 && bitmap.type == 3 && bitmap.mode == 4 &&
               bitmap.width == 14 && bitmap.height == 14);
        portable_db_record_free(&knob);
    }
    portable_fonts_init(&fonts);
    assert(portable_fonts_load(&fonts, argv[1]) == PORTABLE_RENDER_OK);
    renderer.database = &database;
    renderer.colors = colors.data;
    renderer.colors_size = colors.size;
    renderer.screen_width = 640;
    renderer.hardware_profile = 0;
    renderer.fonts[2] = portable_fonts_get(&fonts, 4);
    assert(renderer.fonts[2] != NULL);
    pixels = (uint8_t *)calloc(640u * 480u, 1);
    assert(pixels != NULL);
    assert(portable_framebuffer_init(&framebuffer, 640, 480, 640, pixels) ==
           PORTABLE_RENDER_OK);
    renderer.framebuffer = &framebuffer;
    sim_setup_controls_init_data(&controls);
    hooks.resource_size = setup_resource;
    hooks.get_object_rect = setup_rect;
    hooks.refresh_control = setup_refresh;
    /* Resource lookup uses the active HCEGANT database; geometry comes from
     * the current native registry. These providers must share this session. */
    hooks.context = &setup_context;
    assert(portable_window_registry_recalculate(&registry, 18, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    printf("geometry window=18 object4=%d,%d,%d,%d object12=%d,%d,%d,%d object13=%d,%d,%d,%d\n",
           registry.slots[18].window.objects[4].rect.left,
           registry.slots[18].window.objects[4].rect.top,
           registry.slots[18].window.objects[4].rect.right,
           registry.slots[18].window.objects[4].rect.bottom,
           registry.slots[18].window.objects[12].rect.left,
           registry.slots[18].window.objects[12].rect.top,
           registry.slots[18].window.objects[12].rect.right,
           registry.slots[18].window.objects[12].rect.bottom,
           registry.slots[18].window.objects[13].rect.left,
           registry.slots[18].window.objects[13].rect.top,
           registry.slots[18].window.objects[13].rect.right,
           registry.slots[18].window.objects[13].rect.bottom);
    assert(portable_window_registry_recalculate(&registry, 19, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    printf("geometry window=19 object4=%d,%d,%d,%d object12=%d,%d,%d,%d object13=%d,%d,%d,%d\n",
           registry.slots[19].window.objects[4].rect.left,
           registry.slots[19].window.objects[4].rect.top,
           registry.slots[19].window.objects[4].rect.right,
           registry.slots[19].window.objects[4].rect.bottom,
           registry.slots[19].window.objects[12].rect.left,
           registry.slots[19].window.objects[12].rect.top,
           registry.slots[19].window.objects[12].rect.right,
           registry.slots[19].window.objects[12].rect.bottom,
           registry.slots[19].window.objects[13].rect.left,
           registry.slots[19].window.objects[13].rect.top,
           registry.slots[19].window.objects[13].rect.right,
           registry.slots[19].window.objects[13].rect.bottom);
    assert(sim_setup_init_controls(&controls, &hooks) == SIM_SETUP_OK);
    session.setup_controls = controls;
    session.window_registry = &registry;
    session.window_database = &database;
    session.world.population_black[0] = 77;
    session.controls[SIM_SETUP_MODE_CONTROL].active = 1;
    session.controls[SIM_SETUP_MODE_CONTROL].rectangle = controls.mode_rect;
    session.controls[SIM_SETUP_MODE_CONTROL].point = controls.mode_point;
    session.controls[SIM_SETUP_CASTE_CONTROL].active = 1;
    session.controls[SIM_SETUP_CASTE_CONTROL].rectangle = controls.caste_rect;
    session.controls[SIM_SETUP_CASTE_CONTROL].point = controls.caste_point;
    assert(sim_control_render_binding_from_session(
               &session, &renderer, SIM_SETUP_MODE_CONTROL, 3,
               &recovered, NULL, NULL, &binding) == SIM_CONTROL_SESSION_INPUT_OK);
    assert(binding.input.total == 60 && binding.input.percent == 1);
    assert(binding.input.colors[0] == 40 && binding.input.colors[1] == 43 &&
           binding.input.colors[2] == 39);
    {
        int active_resource_token = 0;
        SimControlActiveAnimation animation = {&active_resource_token, 0x1234, 7};
        session.controls[SIM_SETUP_MODE_CONTROL].animation_resource =
            &active_resource_token;
        assert(sim_control_render_binding_from_session(
                   &session, &renderer, SIM_SETUP_MODE_CONTROL, 3,
                   &recovered, &animation, test_animation_resolver, &binding) ==
               SIM_CONTROL_SESSION_INPUT_OK);
        assert(binding.input.animation_set_live &&
               binding.input.animation_set_handle == 0x1234 &&
               binding.input.animation_object_id == 7 &&
               binding.raster.active_animation_state == &active_resource_token);
        animation.resource = NULL;
        assert(sim_control_render_binding_from_session(
                   &session, &renderer, SIM_SETUP_MODE_CONTROL, 3,
                   &recovered, &animation, test_animation_resolver, &binding) ==
               SIM_CONTROL_SESSION_INPUT_ANIMATION_MISMATCH);
        session.controls[SIM_SETUP_MODE_CONTROL].animation_resource = NULL;
    }
    puts("active animation identity/pointer validation PASS");
    assert(sim_control_render_binding_from_session(
               &session, &renderer, SIM_SETUP_MODE_CONTROL, 3,
               &recovered, NULL, NULL, &binding) == SIM_CONTROL_SESSION_INPUT_OK);
    input = binding.input;
    raster = binding.raster;
    assert(portable_window_registry_recalculate(&registry, 18, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(input.draw_rect.left == registry.slots[18].window.objects[12].rect.left &&
           input.draw_rect.top == registry.slots[18].window.objects[12].rect.top &&
           input.draw_rect.right == registry.slots[18].window.objects[12].rect.right &&
           input.draw_rect.bottom == registry.slots[18].window.objects[12].rect.bottom);
    assert(sim_control_render_raster(&input, &raster) == PORTABLE_RENDER_OK);
    for (i = 0; i < 640u * 480u; ++i) {
        assert(pixels[i] < 16);
        if (pixels[i] != 0) ++nonzero;
    }
    assert(nonzero > 100);
    {
        size_t knob_pixels = 0;
        int x, y;
        for (y = controls.mode_point.y - controls.knob_height / 2;
             y < controls.mode_point.y + controls.knob_height / 2; ++y)
            for (x = controls.mode_point.x - controls.knob_width / 2;
                 x < controls.mode_point.x + controls.knob_width / 2; ++x)
                if (pixels[(size_t)y * 640u + (size_t)x] != 0) ++knob_pixels;
        assert(knob_pixels > 0);
    }
    printf("window=18 pixels=%zu hash=%016llx point=%d,%d rect=%d,%d,%d,%d\n", nonzero,
           (unsigned long long)hash_bytes(pixels, 640u * 480u),
           controls.mode_point.x, controls.mode_point.y,
           input.draw_rect.left, input.draw_rect.top,
           input.draw_rect.right, input.draw_rect.bottom);

    memset(pixels, 0, 640u * 480u);
    assert(sim_control_render_binding_from_session(
               &session, &renderer, SIM_SETUP_CASTE_CONTROL, 3,
               &recovered, NULL, NULL, &binding) == SIM_CONTROL_SESSION_INPUT_OK);
    assert(binding.input.total == 77 && binding.input.colors[0] == 36 &&
           binding.input.colors[1] == 38 && binding.input.colors[2] == 34);
    input = binding.input;
    raster = binding.raster;
    assert(portable_window_registry_recalculate(&registry, 19, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(input.draw_rect.left == registry.slots[19].window.objects[12].rect.left &&
           input.draw_rect.top == registry.slots[19].window.objects[12].rect.top &&
           input.draw_rect.right == registry.slots[19].window.objects[12].rect.right &&
           input.draw_rect.bottom == registry.slots[19].window.objects[12].rect.bottom);
    assert(sim_control_render_raster(&input, &raster) == PORTABLE_RENDER_OK);
    nonzero = 0;
    for (i = 0; i < 640u * 480u; ++i) {
        assert(pixels[i] < 16);
        if (pixels[i] != 0) ++nonzero;
    }
    assert(nonzero > 100);
    {
        size_t knob_pixels = 0;
        int x, y;
        for (y = controls.caste_point.y - controls.knob_height / 2;
             y < controls.caste_point.y + controls.knob_height / 2; ++y)
            for (x = controls.caste_point.x - controls.knob_width / 2;
                 x < controls.caste_point.x + controls.knob_width / 2; ++x)
                if (pixels[(size_t)y * 640u + (size_t)x] != 0) ++knob_pixels;
        assert(knob_pixels > 0);
    }
    printf("window=19 pixels=%zu hash=%016llx point=%d,%d rect=%d,%d,%d,%d\n", nonzero,
           (unsigned long long)hash_bytes(pixels, 640u * 480u),
           controls.caste_point.x, controls.caste_point.y,
           input.draw_rect.left, input.draw_rect.top,
           input.draw_rect.right, input.draw_rect.bottom);

    /* A caller-owned occlusion region remains in force through the source
     * window clip and is restored after the control overlay. */
    memset(pixels, 15, 640u * 480u);
    {
        PortableRect z_clip = {255, 186, 287, 258};
        size_t inside_changed = 0;
        assert(portable_window_registry_recalculate(&registry, 18, NULL) ==
               PORTABLE_WINDOW_REGISTRY_OK);
        assert(sim_control_render_binding_from_session(
                   &session, &renderer, SIM_SETUP_MODE_CONTROL, 3,
                   &recovered, NULL, NULL, &binding) == SIM_CONTROL_SESSION_INPUT_OK);
        input = binding.input;
        raster = binding.raster;
        portable_framebuffer_set_clip(&framebuffer, z_clip);
        assert(sim_control_render_raster(&input, &raster) == PORTABLE_RENDER_OK);
        assert(framebuffer.clip.left == z_clip.left &&
               framebuffer.clip.top == z_clip.top &&
               framebuffer.clip.right == z_clip.right &&
               framebuffer.clip.bottom == z_clip.bottom);
        for (i = 0; i < 640u * 480u; ++i) {
            size_t x = i % 640u, y = i / 640u;
            if (x >= 255 && x < 287 && y >= 186 && y < 258) {
                if (pixels[i] != 15) ++inside_changed;
            } else {
                assert(pixels[i] == 15);
            }
        }
        assert(inside_changed > 0);
        portable_framebuffer_reset_clip(&framebuffer);
        puts("caller z-order clip preserved");
    }

    free(pixels);
    portable_fonts_destroy(&fonts);
    portable_window_registry_destroy(&registry);
    portable_db_record_free(&colors);
    portable_db_close(&database);
    return 0;
}
