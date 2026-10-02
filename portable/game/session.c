#include "session.h"

#include "render/map.h"
#include "simulation/spider.h"

#include <stdio.h>
#include <string.h>

static int16_t read_be_i16(const uint8_t *bytes)
{
    uint16_t value = (uint16_t)(((uint16_t)bytes[0] << 8) | bytes[1]);
    return (int16_t)value;
}

static int make_path(char *out, size_t capacity, const char *directory,
                     const char *stem, const char *extension)
{
    size_t length;
    int written;
    if (out == NULL || capacity == 0 || directory == NULL || stem == NULL ||
        extension == NULL)
        return 0;
    length = strlen(directory);
    written = snprintf(out, capacity, "%s%s%s.%s", directory,
                       length != 0 && directory[length - 1] != '/' &&
                       directory[length - 1] != '\\' ? "/" : "",
                       stem, extension);
    return written >= 0 && (size_t)written < capacity;
}

static int load_sine_resource(SimSession *session)
{
    PortableDbRecord record;
    PortableDbStatus status;
    size_t i;
    status = portable_db_load(&session->shared_database, 0x03e8, 9, &record);
    if (status != PORTABLE_DB_OK)
        return 0;
    if (record.size != sizeof session->sine_q15 || record.index_flags != 0) {
        portable_db_record_free(&record);
        return 0;
    }
    for (i = 0; i < 64; ++i)
        session->sine_q15[i] = read_be_i16(record.data + i * 2u);
    portable_db_record_free(&record);
    return memcmp(session->sine_q15, sim_spider_sine_table(),
                  sizeof session->sine_q15) == 0;
}

static int load_bitmap_size(SimSession *session, uint16_t object_id,
                            uint16_t kind, int16_t *width, int16_t *height)
{
    PortableDbRecord record;
    PortableBitmap bitmap;
    PortableRenderStatus render_status;
    PortableDbStatus db_status;
    uint8_t *decoded = NULL;
    size_t decoded_size = 0;
    const uint8_t *bytes;
    size_t size;
    int result = 0;

    db_status = portable_db_load(session->window_database,
                                 (int16_t)object_id, (int16_t)kind, &record);
    if (db_status != PORTABLE_DB_OK)
        return 0;
    bytes = record.data;
    size = record.size;
    if (size >= 2 && (bytes[0] == 0xff || bytes[0] == 0x00) &&
        (bytes[1] == 0xff || bytes[1] == 0x80)) {
        render_status = portable_bitmap_decode_packed(bytes, size,
                                                       &decoded, &decoded_size);
        if (render_status != PORTABLE_RENDER_OK)
            goto done;
        bytes = decoded;
        size = decoded_size;
    }
    render_status = portable_bitmap_view(bytes, size, &bitmap);
    if (render_status == PORTABLE_RENDER_OK && bitmap.width != 0 &&
        bitmap.height != 0 && bitmap.width <= INT16_MAX &&
        bitmap.height <= INT16_MAX) {
        *width = (int16_t)bitmap.width;
        *height = (int16_t)bitmap.height;
        result = 1;
    }
done:
    portable_bitmap_release_decoded(decoded);
    portable_db_record_free(&record);
    return result;
}

static int setup_resource_size(void *context, uint16_t object_id,
                               uint16_t kind, int16_t *width, int16_t *height)
{
    SimSession *session = (SimSession *)context;
    if (session == NULL || session->window_database == NULL || width == NULL || height == NULL)
        return 0;
    return load_bitmap_size(session, object_id, kind, width, height);
}

static int setup_object_rect(void *context, uint16_t object_id,
                             SimSetupRect *rect)
{
    SimSession *session = (SimSession *)context;
    PortableWindowRect source;
    if (session == NULL || session->window_registry == NULL || rect == NULL ||
        portable_window_registry_get_object_rect(session->window_registry,
            object_id, &source) != PORTABLE_WINDOW_REGISTRY_OK)
        return 0;
    rect->left = source.left;
    rect->top = source.top;
    rect->right = source.right;
    rect->bottom = source.bottom;
    return 1;
}

static void release_control_animation(SimSessionControlVisual *visual);

static int setup_refresh_control(void *context, SimSetupControlKind kind,
                                 const SimSetupControls *controls)
{
    SimSession *session = (SimSession *)context;
    SimSessionControlVisual *visual;
    const SimSetupRect *rect;
    const SimSetupPoint *point;
    if (session == NULL || controls == NULL ||
        (kind != SIM_SETUP_MODE_CONTROL && kind != SIM_SETUP_CASTE_CONTROL))
        return 0;

    /* The historical Changed handler first runs the corresponding Closed
     * handler. Release only an animation resource this session actually owns. */
    visual = &session->controls[(unsigned)kind];
    if (visual->animation_resource != NULL && visual->release_animation == NULL)
        return 0;
    release_control_animation(visual);
    if (kind == SIM_SETUP_MODE_CONTROL) {
        rect = &controls->mode_rect;
        point = &controls->mode_point;
    } else {
        rect = &controls->caste_rect;
        point = &controls->caste_point;
    }
    visual->rectangle = *rect;
    visual->point = *point;
    visual->active = 1;
    ++visual->generation;
    return 1;
}

static void release_control_animation(SimSessionControlVisual *visual)
{
    if (visual == NULL || visual->animation_resource == NULL)
        return;
    if (visual->release_animation != NULL)
        visual->release_animation(visual->animation_resource);
    visual->animation_resource = NULL;
    visual->release_animation = NULL;
}

static void bind_context(SimSession *session)
{
    session->setup_hooks.resource_size = setup_resource_size;
    session->setup_hooks.get_object_rect = setup_object_rect;
    session->setup_hooks.refresh_control = setup_refresh_control;
    session->setup_hooks.context = session;

    session->worldgen_context.setup_state = &session->setup_state;
    session->worldgen_context.setup_controls = &session->setup_controls;
    session->worldgen_context.setup_hooks = &session->setup_hooks;
    session->worldgen_context.yard_scene = &session->yard_scene;
    session->worldgen_context.rand_world.setup_state = &session->setup_state;
    session->worldgen_context.rand_world.spider = &session->spider;
    session->worldgen_context.rand_world.nest_runtime = &session->nest_runtime;
    session->worldgen_context.rand_world.nest_trace = &session->nest_trace;
    session->worldgen_context.rand_world.sine_q15 = session->sine_q15;
    session->worldgen_context.rand_world.effects = &session->worldgen_effects;
    session->worldgen_context.rand_world.population_effects =
        &session->population_effects;
}

SimSessionStatus sim_session_init(SimSession *session,
                                  const char *assets_directory,
                                  PortableDatabase *window_database,
                                  PortableWindowRegistry *window_registry)
{
    char shared_index[1024], shared_data[1024];
    PortableDbStatus db_status;
    if (session == NULL || assets_directory == NULL || window_database == NULL ||
        window_database->entries == NULL || window_registry == NULL ||
        !window_registry->initialized || window_registry->database != window_database)
        return SIM_SESSION_BAD_ARGUMENT;
    memset(session, 0, sizeof *session);
    if (!make_path(shared_index, sizeof shared_index, assets_directory,
                   "SHARED", "NDX") ||
        !make_path(shared_data, sizeof shared_data, assets_directory,
                   "SHARED", "DAT"))
        return SIM_SESSION_BAD_ARGUMENT;

    db_status = portable_db_open_files(&session->shared_database,
                                       shared_index, shared_data);
    if (db_status != PORTABLE_DB_OK)
        goto database_error;
    session->shared_open = 1;
    session->window_database = window_database;
    session->window_registry = window_registry;
    if (!load_sine_resource(session)) {
        sim_session_close(session);
        return SIM_SESSION_RESOURCE_ERROR;
    }
    if (portable_tileset_load(session->window_database, 0,
                              &session->tileset) != PORTABLE_DB_OK) {
        sim_session_close(session);
        return SIM_SESSION_RESOURCE_ERROR;
    }
    session->tileset_open = 1;

    sim_world_init_sim_vars(&session->world);
    session->world.tick_count_delays[0] = 21;
    session->world.tick_count_delays[1] = 7;
    session->world.tick_count_delays[2] = 0;
    session->world.tick_count_delays[3] = -1;
    session->feeding.next_food_threshold = 0x28;
    session->setup_controls.mode_current = 0;
    session->setup_controls.caste_current = 0;
    bind_context(session);
    session->resources_ready = 1;
    return SIM_SESSION_OK;

database_error:
    sim_session_close(session);
    return SIM_SESSION_DATABASE_ERROR;
}

void sim_session_close(SimSession *session)
{
    unsigned i;
    if (session == NULL)
        return;
    for (i = 0; i < 2; ++i)
        release_control_animation(&session->controls[i]);
    if (session->tileset_open) {
        portable_tileset_free(&session->tileset);
        session->tileset_open = 0;
    }
    if (session->shared_open) {
        portable_db_close(&session->shared_database);
        session->shared_open = 0;
    }
    session->window_registry = NULL;
    session->window_database = NULL;
    session->resources_ready = 0;
    session->rng_seeded = 0;
    session->new_game_ready = 0;
}

SimSessionStatus sim_session_seed_startup(SimSession *session,
                                          uint32_t lfsr_tick,
                                          uint32_t c_runtime_tick)
{
    if (session == NULL || !session->resources_ready)
        return SIM_SESSION_BAD_ARGUMENT;
    if (session->rng_seeded)
        return SIM_SESSION_ALREADY_STARTED;
    sim_worldgen_seed_startup_rng(&session->rng, lfsr_tick, c_runtime_tick);
    session->startup_lfsr_tick = lfsr_tick;
    session->startup_c_tick = c_runtime_tick;
    session->rng_seeded = 1;
    return SIM_SESSION_OK;
}

SimSessionStatus sim_session_new_game(SimSession *session,
                                      const SimNewGameConfig *config)
{
    SimWorldgenStatus status;
    if (session == NULL)
        return SIM_SESSION_BAD_ARGUMENT;
    session->new_game_ready = 0;
    if (config == NULL || !session->resources_ready ||
        !session->rng_seeded || config->scenario < 0 || config->scenario > 3)
        return SIM_SESSION_BAD_ARGUMENT;
    memset(&session->nest_trace, 0, sizeof session->nest_trace);
    memset(&session->worldgen_effects, 0, sizeof session->worldgen_effects);
    sim_population_effects_reset(&session->population_effects);
    status = sim_worldgen_start_new_game(&session->world, &session->rng,
        config, &session->worldgen_context);
    if (status != SIM_WORLDGEN_OK)
        return SIM_SESSION_WORLDGEN_ERROR;
    session->new_game_ready = 1;
    return SIM_SESSION_OK;
}

const char *sim_session_status_string(SimSessionStatus status)
{
    switch (status) {
    case SIM_SESSION_OK: return "ok";
    case SIM_SESSION_BAD_ARGUMENT: return "bad argument or missing startup state";
    case SIM_SESSION_DATABASE_ERROR: return "database open failed";
    case SIM_SESSION_RESOURCE_ERROR: return "required game resource is invalid";
    case SIM_SESSION_REGISTRY_ERROR: return "window registry initialization failed";
    case SIM_SESSION_SETUP_ERROR: return "setup/control initialization failed";
    case SIM_SESSION_WORLDGEN_ERROR: return "source-derived NewGame failed";
    case SIM_SESSION_ALREADY_STARTED: return "startup RNG was already seeded";
    default: return "unknown session status";
    }
}
