#include "../../../game/session.h"
#include "../../../game/recovered/engine.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void test_failure(const char *expression, const char *file, int line)
{
    fprintf(stderr, "CHECK failed: %s at %s:%d\n", expression, file, line);
    exit(1);
}
#undef assert
#define assert(expression) ((expression) ? (void)0 : test_failure(#expression, __FILE__, __LINE__))

enum { LOG_CAP = 256, CONTROL_FIELD_MASK_CAP = 64 };

typedef struct ProviderCall {
    unsigned op;
    uint16_t a;
    uint16_t b;
    int32_t c;
    int16_t words[10];
} ProviderCall;

enum { OP_CLIP = 1, OP_OFF, OP_HELP, OP_GROUP, OP_SELECT, OP_RECT,
       OP_DRAW, OP_POLL, OP_STILL };

typedef struct Fixture {
    SimRecoveredEngine *engine;
    SimSetupRect rect;
    SimSetupPoint samples[8];
    unsigned sample_count;
    unsigned sample_at;
    int down;
    int fail_op;
    unsigned host_tick_calls;
    unsigned host_query_calls;
    unsigned host_effect_calls;
    SimSetupControlKind current_kind;
    SimRecoveredQuery query_ids[LOG_CAP];
    uintptr_t query_args[LOG_CAP][2];
    uint8_t query_counts[LOG_CAP];
    unsigned callbacks;
    unsigned callback_snapshot_checks;
    unsigned callback_snapshot_failures;
    unsigned nested_checks;
    unsigned nested_failures;
    SimSetupControlKind nested_kind;
    SimControlEventPrivateState *private_state;
    SimControlEventProvider *provider;
    SimControlEventMessage nested_message;
    ProviderCall calls[LOG_CAP];
} Fixture;

static int note(Fixture *f, unsigned op, uint16_t a, uint16_t b, int32_t c,
                const int16_t *words, unsigned word_count)
{
    ProviderCall *r;
    RecoveredState snapshot;
    const SimSetupControls *controls;
    const SimSetupTriangle *level;
    int16_t auto_flag;
    SimRecoveredEngineStatus nested;
    if (f->callbacks < LOG_CAP) {
        r = &f->calls[f->callbacks];
        memset(r, 0, sizeof(*r));
        r->op = op; r->a = a; r->b = b; r->c = c;
        if (word_count > 10) word_count = 10;
        if (words != NULL) memcpy(r->words, words, word_count * sizeof(words[0]));
    }
    ++f->callbacks;
    if (f->fail_op == (int)op) return 0;
    if (f->engine == NULL || !sim_recovered_engine_snapshot(f->engine, &snapshot)) {
        ++f->callback_snapshot_failures;
        return 0;
    }
    ++f->callback_snapshot_checks;
    controls = &f->engine->session->setup_controls;
    if (f->current_kind == SIM_SETUP_MODE_CONTROL) {
        if (snapshot.ModeAuto != controls->mode_auto ||
            memcmp(snapshot.modeLevels, &controls->mode_level,
                   sizeof controls->mode_level) != 0 ||
            memcmp(snapshot.fd_3D57_0810, controls->mode_levels,
                   sizeof controls->mode_levels) != 0 ||
            snapshot.fd_50F6_0358.x != controls->mode_point.x ||
            snapshot.fd_50F6_0358.y != controls->mode_point.y)
            ++f->callback_snapshot_failures;
    } else {
        if (snapshot.CasteAuto != controls->caste_auto ||
            memcmp(snapshot.casteLevels, &controls->caste_level,
                   sizeof controls->caste_level) != 0 ||
            memcmp(snapshot.fd_3D57_07F2, controls->caste_levels,
                   sizeof controls->caste_levels) != 0 ||
            memcmp(snapshot.IdealCaste, controls->ideal_caste,
                   4 * sizeof controls->ideal_caste[0]) != 0 ||
            snapshot.fd_50F6_022E.x != controls->caste_point.x ||
            snapshot.fd_50F6_022E.y != controls->caste_point.y)
            ++f->callback_snapshot_failures;
    }
    if (f->nested_checks == 0 && f->nested_kind <= SIM_SETUP_CASTE_CONTROL) {
        ++f->nested_checks;
        nested = sim_recovered_engine_control_event(f->engine, f->nested_kind,
                    &f->nested_message, f->private_state, f->provider);
        if (nested != SIM_RECOVERED_ENGINE_INVALID_ARGUMENT)
            ++f->nested_failures;
    }
    if (f->engine->recovered_binding_active == 0) {
        /* snapshot must be the currently published TLS view during callback. */
        ++f->callback_snapshot_failures;
        return 0;
    }
    if (op == OP_DRAW) {
        if (a == SIM_SETUP_MODE_CONTROL) {
            level = &controls->mode_level; auto_flag = controls->mode_auto;
            if (snapshot.ModeAuto != auto_flag ||
                memcmp(snapshot.modeLevels, level, sizeof(*level)) != 0 ||
                snapshot.fd_50F6_0358.x != controls->mode_point.x ||
                snapshot.fd_50F6_0358.y != controls->mode_point.y)
                ++f->callback_snapshot_failures;
            if (words == NULL || word_count < 1 || f->private_state == NULL ||
                words[0] != f->private_state->mode_percent)
                ++f->callback_snapshot_failures;
        } else {
            level = &controls->caste_level; auto_flag = controls->caste_auto;
            if (snapshot.CasteAuto != auto_flag ||
                memcmp(snapshot.casteLevels, level, sizeof(*level)) != 0 ||
                snapshot.fd_50F6_022E.x != controls->caste_point.x ||
                snapshot.fd_50F6_022E.y != controls->caste_point.y)
                ++f->callback_snapshot_failures;
            if (words == NULL || word_count < 1 || f->private_state == NULL ||
                words[0] != f->private_state->caste_percent)
                ++f->callback_snapshot_failures;
        }
    }
    return 1;
}

static int clip(void *p, uint16_t id) { return note(p, OP_CLIP, id, 0, 0, NULL, 0); }
static int off(void *p) { return note(p, OP_OFF, 0, 0, 0, NULL, 0); }
static int help(void *p, uint16_t id) { return note(p, OP_HELP, id, 0, 0, NULL, 0); }
static int group(void *p, uint16_t w, uint8_t g, int v)
{ return note(p, OP_GROUP, w, g, v, NULL, 0); }
static int select_object(void *p, uint16_t id)
{ return note(p, OP_SELECT, id, 0, 0, NULL, 0); }
static int get_rect(void *p, uint16_t id, SimSetupRect *r)
{
    Fixture *f = p;
    int16_t words[4];
    *r = f->rect;
    words[0] = r->left; words[1] = r->top; words[2] = r->right; words[3] = r->bottom;
    return note(f, OP_RECT, id, 0, 0, words, 4);
}
static int draw(void *p, SimSetupControlKind k, uint16_t flags,
                const SimSetupControls *c, int16_t percent)
{
    const SimSetupTriangle *t = k == SIM_SETUP_MODE_CONTROL ? &c->mode_level : &c->caste_level;
    const int16_t words[8] = {percent, (int16_t)t->frac, (int16_t)t->mid,
        (int16_t)t->weight,
        k == SIM_SETUP_MODE_CONTROL ? c->mode_current : c->caste_current,
        k == SIM_SETUP_MODE_CONTROL ? c->mode_auto : c->caste_auto,
        k == SIM_SETUP_MODE_CONTROL ? c->mode_point.x : c->caste_point.x,
        k == SIM_SETUP_MODE_CONTROL ? c->mode_point.y : c->caste_point.y};
    return note(p, OP_DRAW, (uint16_t)k, flags, 0, words, 8);
}
static int poll(void *p, SimSetupPoint *point)
{
    Fixture *f = p;
    int16_t words[2];
    if (f->sample_at < f->sample_count) *point = f->samples[f->sample_at++];
    words[0] = point->x; words[1] = point->y;
    return note(f, OP_POLL, 0, 0, 0, words, 2);
}
static int still(void *p, int *down)
{
    Fixture *f = p;
    *down = f->sample_at < f->sample_count ? 1 : f->down;
    return note(f, OP_STILL, 0, 0, *down, NULL, 0);
}

static int host_tick(void *p, int32_t *value)
{ Fixture *f = p; *value = (int32_t)f->host_tick_calls++; return 1; }
static int host_query(void *p, SimRecoveredQuery q, const uintptr_t *args,
                      uint8_t count, int32_t *value)
{
    Fixture *f = p;
    if (f->host_query_calls < LOG_CAP) {
        f->query_ids[f->host_query_calls] = q;
        f->query_counts[f->host_query_calls] = count;
        if (args != NULL && count > 0) f->query_args[f->host_query_calls][0] = args[0];
        if (args != NULL && count > 1) f->query_args[f->host_query_calls][1] = args[1];
    }
    ++f->host_query_calls;
    if (q == SIM_RECOVERED_QUERY_GET_OBJECT_RECT && args != NULL && count == 2) {
        PortableWindowRect r;
        int16_t *out = (int16_t *)args[1];
        if (out == NULL || f->engine->session->window_registry == NULL ||
            portable_window_registry_get_object_rect(f->engine->session->window_registry,
              (uint16_t)args[0], &r) != PORTABLE_WINDOW_REGISTRY_OK) return 0;
        out[0] = r.left; out[1] = r.top; out[2] = r.right; out[3] = r.bottom;
        *value = 1;
        return 1;
    }
    if (q == SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS && args == NULL && count == 0) {
        *value = 0; /* Controlled BDA fixture: no BIOS keyboard flags set. */
        return 1;
    }
    return 0;
}
static int host_effect(void *p, const SimRecoveredEffect *e)
{ Fixture *f = p; if (e == NULL) return 0; ++f->host_effect_calls; return 1; }
static int song_done(void *p) { (void)p; return 1; }

static void allow_bytes(uint8_t *mask, size_t offset, size_t size)
{ assert(offset + size <= sizeof(RecoveredState)); memset(mask + offset, 1, size); }

static void assert_only_control_tls_changed(const RecoveredState *before,
    const RecoveredState *after, SimSetupControlKind kind)
{
    uint8_t mask[sizeof(RecoveredState)] = {0};
    const uint8_t *a = (const uint8_t *)before, *b = (const uint8_t *)after;
    if (kind == SIM_SETUP_MODE_CONTROL) {
        allow_bytes(mask, offsetof(RecoveredState, ModeAuto), sizeof before->ModeAuto);
        allow_bytes(mask, offsetof(RecoveredState, modeLevels), sizeof before->modeLevels);
        allow_bytes(mask, offsetof(RecoveredState, fd_3D57_0810), sizeof before->fd_3D57_0810);
        allow_bytes(mask, offsetof(RecoveredState, fd_50F6_0358), sizeof before->fd_50F6_0358);
    } else {
        allow_bytes(mask, offsetof(RecoveredState, CasteAuto), sizeof before->CasteAuto);
        allow_bytes(mask, offsetof(RecoveredState, casteLevels), sizeof before->casteLevels);
        allow_bytes(mask, offsetof(RecoveredState, fd_3D57_07F2), sizeof before->fd_3D57_07F2);
        allow_bytes(mask, offsetof(RecoveredState, IdealCaste), 4 * sizeof(before->IdealCaste[0]));
        allow_bytes(mask, offsetof(RecoveredState, fd_50F6_022E), sizeof before->fd_50F6_022E);
    }
    for (size_t i = 0; i < sizeof(RecoveredState); ++i)
        if (!mask[i]) assert(a[i] == b[i]);
}

static void assert_tls_matches_controls(const RecoveredState *state,
                                        const SimSetupControls *controls,
                                        SimSetupControlKind kind)
{
    if (kind == SIM_SETUP_MODE_CONTROL) {
        assert(state->ModeAuto == controls->mode_auto);
        assert(memcmp(state->modeLevels, &controls->mode_level,
                      sizeof controls->mode_level) == 0);
        assert(memcmp(state->fd_3D57_0810, controls->mode_levels,
                      sizeof controls->mode_levels) == 0);
        assert(state->fd_50F6_0358.x == controls->mode_point.x &&
               state->fd_50F6_0358.y == controls->mode_point.y);
    } else {
        assert(state->CasteAuto == controls->caste_auto);
        assert(memcmp(state->casteLevels, &controls->caste_level,
                      sizeof controls->caste_level) == 0);
        assert(memcmp(state->fd_3D57_07F2, controls->caste_levels,
                      sizeof controls->caste_levels) == 0);
        assert(memcmp(state->IdealCaste, controls->ideal_caste,
                      4 * sizeof controls->ideal_caste[0]) == 0);
        assert(state->fd_50F6_022E.x == controls->caste_point.x &&
               state->fd_50F6_022E.y == controls->caste_point.y);
    }
}

static unsigned window_id(SimSetupControlKind k)
{ return k == SIM_SETUP_MODE_CONTROL ? 0x1200u : 0x1300u; }

static void expect_ops(const Fixture *f, const unsigned *ops, unsigned count)
{
    if (f->callbacks != count) {
        fprintf(stderr, "provider trace count: actual=%u expected=%u ops=", f->callbacks, count);
        for (unsigned i = 0; i < f->callbacks && i < LOG_CAP; ++i)
            fprintf(stderr, "%u ", f->calls[i].op);
        fputc('\n', stderr);
    }
    assert(f->callbacks == count);
    for (unsigned i = 0; i < count; ++i) assert(f->calls[i].op == ops[i]);
}

static const char *op_name(unsigned op)
{
    switch (op) {
    case OP_CLIP: return "clip"; case OP_OFF: return "off";
    case OP_HELP: return "help"; case OP_GROUP: return "group";
    case OP_SELECT: return "select"; case OP_RECT: return "rect";
    case OP_DRAW: return "draw"; case OP_POLL: return "poll";
    case OP_STILL: return "still"; default: return "?";
    }
}

static void print_trace(const Fixture *f, SimSetupControlKind kind, uint16_t code)
{
    printf("trace kind=%s code=%04x host_query=%d argc=%u callbacks=",
        kind == SIM_SETUP_MODE_CONTROL ? "mode" : "caste", code,
        (int)f->query_ids[f->host_query_calls - 1],
        (unsigned)f->query_counts[f->host_query_calls - 1]);
    for (unsigned i = 0; i < f->callbacks; ++i) {
        const ProviderCall *r = &f->calls[i];
        printf("%s%s(%u,%u,%ld", i == 0 ? "" : ";", op_name(r->op),
               r->a, r->b, (long)r->c);
        for (unsigned j = 0; j < 10; ++j)
            printf(",%d", (int)r->words[j]);
        putchar(')');
    }
    putchar('\n');
}

static void run_control_case(SimRecoveredEngine *engine, Fixture *fixture,
    SimControlEventProvider *provider, SimControlEventPrivateState *private_state,
    SimSetupControlKind kind, uint16_t code, SimSetupPoint initial,
    SimSetupPoint *samples, unsigned sample_count, int16_t *percent)
{
    RecoveredState before, after;
    SimRng rng_before;
    SimControlEventMessage message = {code, initial};
    SimSetupControls *c = &engine->session->setup_controls;
    unsigned ticks = fixture->host_tick_calls, queries = fixture->host_query_calls;
    unsigned effects = fixture->host_effect_calls, old_tick_count;
    (void)percent;
    fixture->callbacks = 0; fixture->sample_at = 0;
    fixture->current_kind = kind;
    fixture->callback_snapshot_checks = 0;
    fixture->callback_snapshot_failures = 0;
    fixture->nested_checks = 0;
    fixture->nested_failures = 0;
    fixture->sample_count = sample_count;
    fixture->down = 0;
    if (sample_count) memcpy(fixture->samples, samples, sample_count * sizeof(*samples));
    fixture->rect = kind == SIM_SETUP_MODE_CONTROL ? c->mode_rect : c->caste_rect;
    assert(sim_recovered_engine_snapshot(engine, &before));
    rng_before = engine->session->rng;
    old_tick_count = (unsigned)engine->completed_ticks;
    assert(sim_recovered_engine_control_event(engine, kind, &message,
                 private_state, provider) == SIM_RECOVERED_ENGINE_OK);
    assert(sim_recovered_engine_snapshot(engine, &after));
    assert_only_control_tls_changed(&before, &after, kind);
    assert_tls_matches_controls(&after, c, kind);
    assert(memcmp(&rng_before, &engine->session->rng, sizeof rng_before) == 0);
    assert(engine->completed_ticks == old_tick_count);
    assert(fixture->host_tick_calls == ticks && fixture->host_effect_calls == effects);
    assert(fixture->host_query_calls == queries + 1);
    assert(fixture->query_ids[queries] == SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS &&
           fixture->query_counts[queries] == 0);
    assert(fixture->callback_snapshot_failures == 0);
    assert(fixture->callback_snapshot_checks == fixture->callbacks);
    assert(fixture->nested_checks == 1 && fixture->nested_failures == 0);
    assert(after.triWidth == before.triWidth && after.triHeight == before.triHeight &&
           after.triWidthL == before.triWidthL);
    assert(engine->control_request == NULL && engine->recovered_binding_active == 0);
    assert(fixture->callbacks > 0);
    assert(fixture->calls[0].op == OP_CLIP && fixture->calls[0].a == window_id(kind));
    assert(fixture->calls[fixture->callbacks - 1].op == OP_OFF);
    print_trace(fixture, kind, code);
}

int main(void)
{
    static SimSession session = SIM_SESSION_INITIALIZER;
    static SimRecoveredEngine engine;
    PortableDatabase db = {0};
    PortableWindowRegistry registry = {0};
    const SimNewGameConfig config = {1, 0, 11, 8};
    SimNestRequest clock = {{1000, 1001}, 2};
    Fixture fixture = {0};
    SimRecoveredHost host = {0};
    SimControlEventPrivateState private_state;
    SimControlEventProvider provider;
    SimSetupControls *controls;
    SimRng rng_after_tick;
    SimRecoveredEngineStatus status;

    assert(portable_db_open(&db, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &db, 0) == PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_load(&registry, 0) == PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_recalculate(&registry, 0, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(sim_session_init(&session, "assets", &db, &registry) == SIM_SESSION_OK);
    assert(sim_session_seed_startup(&session, 0x5a31u, 0x12345678u) == SIM_SESSION_OK);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);

    fixture.engine = &engine;
    host.context = &fixture;
    host.tick_count = host_tick;
    host.query = host_query;
    host.effect = host_effect;
    host.song_done = song_done;
    host.audio_driver_ready = 1;
    host.screen_width = 640;
    host.hardware_profile = (uint8_t)registry.profile_id;
    assert(sim_recovered_engine_init(&engine, &session, &host) ==
           SIM_RECOVERED_ENGINE_INIT_OK);
    controls = &session.setup_controls;
    assert(session.new_game_ready && controls->source_data_initialized);
    assert(controls->mode_rect.right > controls->mode_rect.left &&
           controls->caste_rect.bottom > controls->caste_rect.top);
    assert(sim_recovered_engine_tick(&engine, &clock) == SIM_RECOVERED_ENGINE_OK);
    assert(engine.completed_ticks == 1);
    rng_after_tick = session.rng;

    private_state.mode_percent = 0;
    private_state.caste_percent = 0;
    private_state.triangle_width = engine.recovered.triWidth;
    private_state.triangle_height = engine.recovered.triHeight;
    private_state.triangle_width_left = engine.recovered.triWidthL;
    fixture.private_state = &private_state;
    fixture.provider = &provider;
    fixture.nested_kind = SIM_SETUP_CASTE_CONTROL;
    fixture.nested_message = (SimControlEventMessage){0x1302u, {0, 0}};
    provider = (SimControlEventProvider){clip, off, help, group, select_object,
        get_rect, draw, poll, still, &fixture, 16};

    /* Source preset, Auto and percentage commands in both control windows. */
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_MODE_CONTROL, 0x1208u, (SimSetupPoint){0, 0}, NULL, 0,
        &private_state.mode_percent);
    assert(controls->mode_current == 2 && controls->mode_auto == 0);
    {
        const unsigned ops[] = {OP_CLIP, OP_SELECT, OP_CLIP, OP_DRAW, OP_GROUP, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        assert(fixture.calls[0].a == 0x1200 && fixture.calls[1].a == 0x1205 &&
               fixture.calls[2].a == 0x1200 && fixture.calls[3].b == 3 &&
               fixture.calls[4].a == 0x1200 && fixture.calls[4].b == 4 &&
               fixture.calls[4].c == 1);
    }
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_MODE_CONTROL, 0x1204u, (SimSetupPoint){0, 0}, NULL, 0,
        &private_state.mode_percent);
    assert(controls->mode_auto == 1);
    {
        const unsigned ops[] = {OP_CLIP, OP_GROUP, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        assert(fixture.calls[1].a == 0x1200 && fixture.calls[1].b == 4 &&
               fixture.calls[1].c == 0);
    }
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_MODE_CONTROL, 0x120fu, (SimSetupPoint){0, 0}, NULL, 0,
        &private_state.mode_percent);
    assert(private_state.mode_percent == 1);
    {
        const unsigned ops[] = {OP_CLIP, OP_DRAW, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        assert(fixture.calls[1].a == SIM_SETUP_MODE_CONTROL &&
               fixture.calls[1].b == 3 && fixture.calls[1].words[0] == 1);
    }
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_CASTE_CONTROL, 0x1308u, (SimSetupPoint){0, 0}, NULL, 0,
        &private_state.caste_percent);
    assert(controls->caste_current == 2 && controls->caste_auto == 0);
    {
        const unsigned ops[] = {OP_CLIP, OP_SELECT, OP_CLIP, OP_DRAW, OP_GROUP, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        assert(fixture.calls[0].a == 0x1300 && fixture.calls[1].a == 0x1305 &&
               fixture.calls[4].a == 0x1300 && fixture.calls[4].b == 4 &&
               fixture.calls[4].c == 1);
    }
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_CASTE_CONTROL, 0x1304u, (SimSetupPoint){0, 0}, NULL, 0,
        &private_state.caste_percent);
    assert(controls->caste_auto == 1);
    {
        const unsigned ops[] = {OP_CLIP, OP_GROUP, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        assert(fixture.calls[1].a == 0x1300 && fixture.calls[1].b == 4 &&
               fixture.calls[1].c == 0);
    }
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_CASTE_CONTROL, 0x130fu, (SimSetupPoint){0, 0}, NULL, 0,
        &private_state.caste_percent);
    assert(private_state.caste_percent == 1);
    {
        const unsigned ops[] = {OP_CLIP, OP_DRAW, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        assert(fixture.calls[1].a == SIM_SETUP_CASTE_CONTROL &&
               fixture.calls[1].b == 3 && fixture.calls[1].words[0] == 1);
    }

    /* Outside drag, then an in-triangle drag with a repeated pointer sample. */
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_MODE_CONTROL, 0x120du,
        (SimSetupPoint){(int16_t)(controls->mode_rect.left - 4),
                        (int16_t)(controls->mode_rect.top - 4)}, NULL, 0,
        &private_state.mode_percent);
    {
        const unsigned ops[] = {OP_CLIP, OP_RECT, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        assert(fixture.calls[1].a == 0x120du &&
               fixture.calls[1].words[0] == controls->mode_rect.left &&
               fixture.calls[1].words[1] == controls->mode_rect.top &&
               fixture.calls[1].words[2] == controls->mode_rect.right &&
               fixture.calls[1].words[3] == controls->mode_rect.bottom);
    }
    run_control_case(&engine, &fixture, &provider, &private_state,
        SIM_SETUP_CASTE_CONTROL, 0x130du,
        (SimSetupPoint){(int16_t)(controls->caste_rect.left - 4),
                        (int16_t)(controls->caste_rect.top - 4)}, NULL, 0,
        &private_state.caste_percent);
    {
        const unsigned ops[] = {OP_CLIP, OP_RECT, OP_OFF};
        expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
    }
    {
        SimSetupPoint center = {
            (int16_t)(controls->mode_rect.left +
                      (controls->mode_rect.right - controls->mode_rect.left) / 2),
            (int16_t)(controls->mode_rect.top +
                      (controls->mode_rect.bottom - controls->mode_rect.top) / 3)};
        SimSetupPoint repeated[2] = {center, center};
        run_control_case(&engine, &fixture, &provider, &private_state,
            SIM_SETUP_MODE_CONTROL, 0x120du, center, repeated, 2,
            &private_state.mode_percent);
        {
            const unsigned ops[] = {OP_CLIP, OP_RECT, OP_SELECT, OP_GROUP,
                OP_CLIP, OP_DRAW, OP_POLL, OP_STILL, OP_POLL, OP_STILL, OP_OFF};
            expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
            assert(fixture.calls[1].a == 0x120du && fixture.calls[2].a == 0x1205 &&
                   fixture.calls[3].a == 0x1200 && fixture.calls[3].b == 4 &&
                   fixture.calls[3].c == 1);
        }
    }
    {
        SimSetupPoint center = {
            (int16_t)(controls->caste_rect.left +
                      (controls->caste_rect.right - controls->caste_rect.left) / 2),
            (int16_t)(controls->caste_rect.top +
                      (controls->caste_rect.bottom - controls->caste_rect.top) / 3)};
        SimSetupPoint repeated[2] = {center, center};
        run_control_case(&engine, &fixture, &provider, &private_state,
            SIM_SETUP_CASTE_CONTROL, 0x130du, center, repeated, 2,
            &private_state.caste_percent);
        {
            const unsigned ops[] = {OP_CLIP, OP_RECT, OP_SELECT, OP_GROUP,
                OP_CLIP, OP_DRAW, OP_POLL, OP_STILL, OP_POLL, OP_STILL, OP_OFF};
            expect_ops(&fixture, ops, sizeof ops / sizeof ops[0]);
        }
    }
    /* Caller-owned selectors and percentages survive actual RandYard/NewGame
     * source initControls; shared recovered geometry is the engine's active
     * source image and remains owned by RandYard, not by this event wrapper. */
    {
        const int16_t mode_selector = controls->mode_current;
        const int16_t caste_selector = controls->caste_current;
        const int16_t mode_percent = private_state.mode_percent;
        const int16_t caste_percent = private_state.caste_percent;
        assert(memcmp(&rng_after_tick, &session.rng, sizeof rng_after_tick) == 0);
        status = sim_recovered_engine_action(&engine, SIM_RECOVERED_ACTION_RAND_YARD,
                                             1, 0);
        assert(status == SIM_RECOVERED_ENGINE_OK);
        assert(controls->mode_current == mode_selector &&
               controls->caste_current == caste_selector);
        assert(private_state.mode_percent == mode_percent &&
               private_state.caste_percent == caste_percent);
    }
    assert(engine.completed_ticks == 1);

    /* A typed public call rejects invalid kinds. The private dispatcher action
     * cannot be invoked directly without its synchronous request. */
    {
        RecoveredState before = engine.recovered, after;
        SimControlEventMessage m = {0x1206u, {0, 0}};
        assert(sim_recovered_engine_control_event(&engine,
            (SimSetupControlKind)99, &m, &private_state, &provider) ==
               SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
        assert(sim_recovered_engine_action(&engine,
            SIM_RECOVERED_ACTION_CONTROL_EVENT, 0, 0) ==
               SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
        assert(sim_recovered_engine_action(&engine,
            (SimRecoveredAction)0x7fff, 0, 0) ==
               SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
        assert(sim_recovered_engine_snapshot(&engine, &after));
        assert(memcmp(&before, &after, sizeof before) == 0);
        assert(engine.control_request == NULL && !engine.recovered_binding_active);
    }

    /* Provider rejection crosses the engine fault boundary and cleans up its
     * recovered/RNG/audio bindings while preserving its published partial state. */
    {
        SimControlEventMessage m = {0x1203u, {0, 0}};
        RecoveredState before, after;
        SimRng rng = session.rng;
        fixture.fail_op = OP_HELP;
        assert(sim_recovered_engine_snapshot(&engine, &before));
        status = sim_recovered_engine_control_event(&engine,
            SIM_SETUP_MODE_CONTROL, &m, &private_state, &provider);
        assert(status == SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL);
        assert(engine.failed_service != NULL && engine.control_request == NULL);
        assert(!engine.recovered_binding_active && engine.control_request == NULL);
        assert(sim_recovered_engine_snapshot(&engine, &after));
        assert_only_control_tls_changed(&before, &after, SIM_SETUP_MODE_CONTROL);
        assert(memcmp(&rng, &session.rng, sizeof rng) == 0);
    }

    /* A fresh engine can bind and execute after the provider-fault longjmp,
     * proving that outer active-engine/abort bindings were released. */
    {
        static SimRecoveredEngine recovered_again;
        SimControlEventMessage m = {0x1202u, {0, 0}}; /* source unknown no-op */
        fixture.engine = &recovered_again;
        fixture.fail_op = 0;
        fixture.nested_checks = 1;
        assert(sim_recovered_engine_init(&recovered_again, &session, &host) ==
               SIM_RECOVERED_ENGINE_INIT_OK);
        assert(sim_recovered_engine_control_event(&recovered_again,
            SIM_SETUP_MODE_CONTROL, &m, &private_state, &provider) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(recovered_again.control_request == NULL &&
               !recovered_again.recovered_binding_active);
    }

    sim_session_close(&session);
    portable_window_registry_destroy(&registry);
    portable_db_close(&db);
    puts("resource-backed control engine boundary probes passed");
    return 0;
}
