#include "../../game/render/overview.h"
#include "../../game/session.h"

#include <assert.h>
#include <string.h>

static void test_surface_and_cache(void)
{
    SimGameWorld world;
    SimOverviewImage image;
    SimOverviewInput input;
    uint8_t prior[SIM_OVERVIEW_MAX_PIXELS];

    memset(&world, 0, sizeof world);
    memset(&input, 0, sizeof input);
    input.world = &world;
    input.mode = 1;
    input.hardware_profile = 0;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.width == 128 && image.height == 64 && image.scale_x == 4);
    assert(image.pixels[2u * 128u + 1u] == 0x0b); /* source terrain table[0] */

    world.life_a[1][2] = 8;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.pixels[2u * 128u + 1u] == 0x0f); /* source Life table[1] */

    memset(prior, 0x55, sizeof prior);
    input.fresh = 1;
    input.previous_mode = 1;
    input.previous_pixels = prior;
    world.life_a[1][2] = 0;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.pixels[2u * 128u + 1u] == 0x55); /* fresh cache preserves empty cells */
    input.previous_mode = 2;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.pixels[2u * 128u + 1u] == 0x0b); /* mode change invalidates cache */
}

static void test_nest_and_scent(void)
{
    SimGameWorld world;
    SimOverviewImage image;
    SimOverviewInput input;
    memset(&world, 0, sizeof world);
    memset(&input, 0, sizeof input);
    input.world = &world;
    input.hardware_profile = 8;
    input.mode = 2;
    world.life_b[3][4] = 0x80;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.width == 64 && image.height == 64 && image.left_margin == 128);
    assert(image.pixels[4u * 64u + 3u] == 3);
    world.life_b[3][4] = 0xfe;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.pixels[4u * 64u + 3u] == 1);

    input.mode = 8;
    world.pheromone_a[2][1] = 32; /* source reads src[(y << 5) + x] */
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.width == 128 && image.height == 64 && image.left_margin == 0);
    assert(image.pixels[2u * 128u + 4u] == 0x11);
    assert(image.pixels[2u * 128u + 5u] == 0x11);
    assert(image.pixels[3u * 128u + 4u] == 0x11);
    assert(image.pixels[3u * 128u + 5u] == 0x11);
}

static void test_profile_errors_and_blit(void)
{
    SimGameWorld world;
    SimOverviewImage image;
    SimOverviewInput input;
    PortableFramebuffer fb;
    uint8_t pixels[32u * 24u];
    memset(&world, 0, sizeof world);
    memset(&input, 0, sizeof input);
    input.world = &world;
    input.mode = 0;
    input.hardware_profile = 0;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_UNSUPPORTED_MODE);
    input.mode = 1;
    input.hardware_profile = 6;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_UNSUPPORTED_PROFILE);

    memset(image.pixels, 0, sizeof image.pixels);
    image.pixels[0] = 1;
    image.width = 2;
    image.height = 2;
    image.stride = 2;
    image.scale_x = 4;
    image.scale_y = 4;
    image.left_margin = 1;
    image.hardware_profile = 0;
    memset(pixels, 0, sizeof pixels);
    assert(portable_framebuffer_init(&fb, 32, 24, 32, pixels) == PORTABLE_RENDER_OK);
    portable_framebuffer_set_clip(&fb, (PortableRect){4, 0, 8, 4});
    assert(sim_overview_blit(&image, &fb, 0, 0) == SIM_OVERVIEW_OK);
    assert(pixels[0u * 32u + 4u] == 15);
    assert(pixels[1u * 32u + 4u] == 0);
    assert(pixels[0u * 32u + 3u] == 0);
    image.hardware_profile = 6;
    assert(sim_overview_blit(&image, &fb, 0, 0) == SIM_OVERVIEW_UNSUPPORTED_PROFILE);
    image.hardware_profile = 0;
    image.pixels[0] = 24;
    assert(sim_overview_blit(&image, &fb, 0, 0) == SIM_OVERVIEW_UNSUPPORTED_SELECTOR);
}

static void test_new_game_asset_state(void)
{
    static SimSession session = SIM_SESSION_INITIALIZER;
    PortableDatabase window_database = {0};
    PortableWindowRegistry registry = {0};
    const SimNewGameConfig config = {1, 0, 11, 8};
    SimOverviewInput input = {0};
    SimOverviewImage image;
    size_t i;
    uint8_t colors[256] = {0};
    unsigned color_count = 0;

    assert(portable_db_open(&window_database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &window_database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(sim_session_init(&session, "assets", &window_database, &registry) ==
           SIM_SESSION_OK);
    assert(sim_session_seed_startup(&session, 0x12345678u, 0x87654321u) ==
           SIM_SESSION_OK);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);

    input.world = &session.world;
    input.mode = 1;
    input.hardware_profile = 0;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.hardware_profile == 0);
    for (i = 0; i < (size_t)image.width * image.height; ++i) {
        if (!colors[image.pixels[i]]) {
            colors[image.pixels[i]] = 1;
            ++color_count;
        }
    }
    assert(color_count > 1);

    input.mode = 2;
    assert(sim_overview_prepare(&input, &image) == SIM_OVERVIEW_OK);
    assert(image.width == 64 && image.height == 64 && image.left_margin == 128);
    sim_session_close(&session);
    portable_window_registry_destroy(&registry);
    portable_db_close(&window_database);
}

int main(void)
{
    test_surface_and_cache();
    test_nest_and_scent();
    test_profile_errors_and_blit();
    test_new_game_asset_state();
    return 0;
}
