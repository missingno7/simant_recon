#include "portable/whole_program/platform/handles.h"
#include <stdio.h>
#include <string.h>

static int failures;
#define CHECK(label, expression) do { \
    int passed = !!(expression); \
    printf("check,%s,%d\n", label, passed); \
    if (!passed) ++failures; \
} while (0)

static int discarded(SimHandleManager *m, SimHandle h)
{
    SimHandleInfo i;
    return sim_handles_info(m, h, &i) == SIM_HANDLE_OK &&
           i.type == SIM_HANDLE_DISCARDED && i.size == 0 &&
           i.lock_count == 0 && *h == NULL;
}

static void explicit_public(void)
{
    char **first, **second, **resized, *payload;
    CHECK("public-configure", sim_handles_global_configure(4096, 64) == SIM_HANDLE_OK);
    first = f_171C_13CA(160, SIM_HANDLE_SOFT, "first-soft");
    second = f_171C_13CA(32, SIM_HANDLE_SOFT, "second-soft");
    CHECK("public-two-allocations", first && second && first != second);
    if (!first || !second) return;
    f_171C_1804(first);
    f_171C_1804(second);
    CHECK("public-discarded-sizes-zero", f_171C_1C1C(first) == 0 &&
        f_171C_16EA(first) == 0 && f_171C_1C1C(second) == 0);
    CHECK("public-discarded-type", f_171C_1686(first) == SIM_HANDLE_DISCARDED &&
        f_171C_1686(second) == SIM_HANDLE_DISCARDED && f_171C_1794(second) == 1);
    resized = f_171C_18A6(first, 100, SIM_HANDLE_FIRM);
    CHECK("public-resurrect-same-master", resized == first && *first != NULL);
    CHECK("public-resurrect-size-type", f_171C_1C1C(first) == 100 &&
        f_171C_1686(first) == SIM_HANDLE_FIRM);
    CHECK("public-other-stays-discarded", f_171C_1C1C(second) == 0 &&
        f_171C_1686(second) == SIM_HANDLE_DISCARDED && f_171C_1794(second) == 1 &&
        *second == NULL);
    payload = f_171C_1B84(first);
    CHECK("public-resurrect-lockable", payload != NULL);
    if (payload) {
        /* Only newly written bytes are asserted; no pre-discard payload survives. */
        memset(payload, 0x69, 100);
        f_171C_1BBA(first);
    }
    f_171C_13E4(first);
    f_171C_13E4(second);
}

static void budget_reclaim(void)
{
    SimHandleManager *m = sim_handles_create(192, 2);
    SimHandle first = NULL, second = NULL, token, resolved = NULL;
    SimHandleInfo i;
    char *locked = NULL;
    CHECK("budget-manager", m != NULL);
    if (!m) return;
    CHECK("budget-first", sim_handles_allocate(m, 160, SIM_HANDLE_SOFT, "soft-160", &first) == SIM_HANDLE_OK);
    CHECK("budget-second", sim_handles_allocate(m, 32, SIM_HANDLE_SOFT, "soft-32", &second) == SIM_HANDLE_OK);
    if (!first || !second) { sim_handles_destroy(m); return; }
    token = sim_handles_index_token(m, first);
    CHECK("budget-reclaim-both", sim_handles_reclaim(m, 192) == 192 &&
        sim_handles_used_bytes(m) == 0 && sim_handles_soft_bytes(m) == 0);
    CHECK("budget-discarded-sizes-zero", discarded(m, first) && discarded(m, second));
    CHECK("budget-discarded-lock-refused", sim_handles_lock(m, first, &locked) == SIM_HANDLE_DISCARDED_DATA);
    CHECK("budget-resurrect", sim_handles_resize(m, token, 100, SIM_HANDLE_FIRM) == SIM_HANDLE_OK);
    CHECK("budget-stable-index-master", sim_handles_resolve(m, token, &resolved) == SIM_HANDLE_OK && resolved == first);
    CHECK("budget-resurrect-accounting", sim_handles_used_bytes(m) == 112 &&
        sim_handles_info(m, first, &i) == SIM_HANDLE_OK && i.size == 100 && i.type == SIM_HANDLE_FIRM);
    CHECK("budget-other-stays-discarded", discarded(m, second));
    CHECK("budget-no-spare-master-needed", sim_handles_resize(m, second, 32, SIM_HANDLE_HARD) == SIM_HANDLE_OK &&
        sim_handles_used_bytes(m) == 144);
    sim_handles_destroy(m);
}

static void failed_resurrection(void)
{
    SimHandleManager *m = sim_handles_create(64, 2);
    SimHandle h = NULL, hard = NULL;
    SimHandleInfo i;
    char *payload = NULL;
    CHECK("failure-manager", m != NULL);
    if (!m) return;
    CHECK("failure-soft", sim_handles_allocate(m, 16, SIM_HANDLE_SOFT, "soft", &h) == SIM_HANDLE_OK);
    CHECK("failure-discard", sim_handles_discard(m, h) == SIM_HANDLE_OK);
    CHECK("failure-hard", sim_handles_allocate(m, 64, SIM_HANDLE_HARD, "hard", &hard) == SIM_HANDLE_OK);
    CHECK("failure-over-budget", sim_handles_resize(m, h, 100, SIM_HANDLE_FIRM) == SIM_HANDLE_NO_MEMORY);
    CHECK("failure-target-unchanged", discarded(m, h) && sim_handles_used_bytes(m) == 64 &&
        sim_handles_info(m, hard, &i) == SIM_HANDLE_OK && i.type == SIM_HANDLE_HARD && i.size == 64);
    CHECK("failure-invalid-size", sim_handles_resize(m, h, 0, SIM_HANDLE_FIRM) == SIM_HANDLE_INVALID_ARGUMENT && discarded(m, h));
    CHECK("failure-invalid-type", sim_handles_resize(m, h, 16, 4) == SIM_HANDLE_BAD_TYPE && discarded(m, h));
    CHECK("failure-free-hard", sim_handles_free(m, hard) == SIM_HANDLE_OK);
    CHECK("failure-retry", sim_handles_resize(m, h, 32, SIM_HANDLE_FIRM) == SIM_HANDLE_OK &&
        sim_handles_used_bytes(m) == 32 && sim_handles_lock(m, h, &payload) == SIM_HANDLE_OK && payload != NULL);
    if (payload) sim_handles_unlock(m, h, NULL);
    sim_handles_destroy(m);
}

static void live_resize_regression(void)
{
    SimHandleManager *m = sim_handles_create(128, 1);
    SimHandle h = NULL;
    SimHandleInfo before, after;
    char *payload = NULL;
    CHECK("live-manager", m != NULL);
    if (!m) return;
    CHECK("live-allocate", sim_handles_allocate(m, 32, SIM_HANDLE_SOFT, "live", &h) == SIM_HANDLE_OK);
    if (!h) { sim_handles_destroy(m); return; }
    CHECK("live-lock", sim_handles_lock(m, h, &payload) == SIM_HANDLE_OK);
    if (payload) memset(payload, 0x3a, 32);
    CHECK("live-locked-resize-refused", sim_handles_resize(m, h, 64, SIM_HANDLE_FIRM) == SIM_HANDLE_LOCKED);
    sim_handles_unlock(m, h, NULL);
    sim_handles_info(m, h, &before);
    CHECK("live-same-size-existing-behavior", sim_handles_resize(m, h, 32, SIM_HANDLE_FIRM | 0x10) == SIM_HANDLE_OK &&
        sim_handles_info(m, h, &after) == SIM_HANDLE_OK && after.type == before.type && after.size == 32 && after.attributes == 0x10);
    CHECK("live-grow", sim_handles_resize(m, h, 64, SIM_HANDLE_FIRM) == SIM_HANDLE_OK);
    CHECK("live-payload-prefix-preserved", *h && memcmp(*h, "::::::::::::::::::::::::::::::::", 32) == 0);
    CHECK("live-grow-accounting", sim_handles_used_bytes(m) == 64 &&
        sim_handles_info(m, h, &after) == SIM_HANDLE_OK && after.size == 64 && after.type == SIM_HANDLE_FIRM);
    sim_handles_destroy(m);
}

int main(void)
{
    explicit_public();
    budget_reclaim();
    failed_resurrection();
    live_resize_regression();
    printf("failures,%d\n", failures);
    return failures != 0;
}
