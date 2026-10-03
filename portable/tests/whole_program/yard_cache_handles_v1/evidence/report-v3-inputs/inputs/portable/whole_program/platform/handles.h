#ifndef SIMANT_WHOLE_PROGRAM_HANDLES_H
#define SIMANT_WHOLE_PROGRAM_HANDLES_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Portable owner for source-visible relocatable memory handles.
 * A Handle remains a stable char ** master pointer; only its data pointer may move.
 * The DOS index-encoded 0F0F handles are opaque uintptr_t tags and are never
 * dereferenced. Host addresses are intentionally not normalized to DOS segments. */
typedef struct SimHandleManager SimHandleManager;
typedef char **SimHandle;

typedef enum SimHandleType {
    SIM_HANDLE_HARD = 0,
    SIM_HANDLE_FIRM = 1,
    SIM_HANDLE_SYSTEM = 2,
    SIM_HANDLE_SOFT = 3,
    SIM_HANDLE_DISCARDED = 5
} SimHandleType;

typedef enum SimHandleStatus {
    SIM_HANDLE_OK = 0,
    SIM_HANDLE_INVALID_ARGUMENT,
    SIM_HANDLE_INVALID_HANDLE,
    SIM_HANDLE_NO_MEMORY,
    SIM_HANDLE_LOCKED,
    SIM_HANDLE_UNLOCKED,
    SIM_HANDLE_DISCARDED_DATA,
    SIM_HANDLE_LOCK_LIMIT,
    SIM_HANDLE_BAD_TYPE,
    SIM_HANDLE_HANDLE_LIMIT,
    SIM_HANDLE_IO_ERROR
} SimHandleStatus;

typedef struct SimHandleInfo {
    size_t size;
    uint8_t type;
    uint8_t lock_count;
    uint8_t attributes;
    uint8_t no_ems_hint;
    uint32_t age;
    const char *name;
    int is_discarded;
} SimHandleInfo;

/* An explicit byte budget makes allocation-failure/reclaim tests deterministic.
 * capacity_bytes==SIZE_MAX means no manager-imposed cap. */
SimHandleManager *sim_handles_create(size_t capacity_bytes, size_t max_handles);
void sim_handles_destroy(SimHandleManager *manager);
void sim_handles_reset(SimHandleManager *manager);
SimHandleStatus sim_handles_last_status(const SimHandleManager *manager);
SimHandleStatus sim_handles_allocate(SimHandleManager *manager, int32_t size,
                                     int16_t flags, const char *name,
                                     SimHandle *out_handle);
SimHandleStatus sim_handles_lock(SimHandleManager *manager, SimHandle handle,
                                 char **out_data);
SimHandleStatus sim_handles_unlock(SimHandleManager *manager, SimHandle handle,
                                   SimHandle *out_index_handle);
SimHandleStatus sim_handles_free(SimHandleManager *manager, SimHandle handle);
SimHandleStatus sim_handles_resize(SimHandleManager *manager, SimHandle handle,
                                   int32_t size, int16_t flags);
SimHandleStatus sim_handles_discard(SimHandleManager *manager, SimHandle handle);
/* Evicts the oldest unlocked soft payloads until need_bytes can fit or no
 * eligible soft handle remains. Discarded handles retain identity and metadata. */
size_t sim_handles_reclaim(SimHandleManager *manager, size_t need_bytes);
SimHandleStatus sim_handles_set_type(SimHandleManager *manager, SimHandle handle,
                                     int16_t flags);
SimHandleStatus sim_handles_info(SimHandleManager *manager, SimHandle handle,
                                 SimHandleInfo *out_info);
SimHandle sim_handles_index_token(SimHandleManager *manager, SimHandle handle);
SimHandleStatus sim_handles_resolve(SimHandleManager *manager, SimHandle handle,
                                    SimHandle *out_real_handle);
size_t sim_handles_used_bytes(const SimHandleManager *manager);
size_t sim_handles_soft_bytes(const SimHandleManager *manager);
size_t sim_handles_capacity_bytes(const SimHandleManager *manager);

/* Native pointer-allocation adapter. The registry preserves exact pointers
 * returned by dos_malloc; dos_free/dos_realloc also resolve a live payload
 * address owned by a source handle, as CloseIndex requires. */
void *dos_malloc(uint16_t size);
void *dos_realloc(void *pointer, uint16_t size);
void dos_free(void *pointer);
void *f_171C_2302(void *pointer, uint16_t size);

/* Source-named high-level APIs used outside root:m171C in the migration.
 * Failure mapping: allocation/access return NULL; metadata queries return
 * conservative zero; void mutators leave state unchanged. Inspect
 * sim_handles_global_last_status() for the explicit failure cause. This
 * fail-closed host policy is not the DOS Punt/nonreturn behavior. */
char **f_171C_13CA(int32_t size, int16_t flags, char *name);
char **f_171C_1A9E(int32_t size, int16_t flags, char *name);
char *f_171C_1B84(char **handle);
char **f_171C_1BBA(char **handle);
void f_171C_13E4(char **handle);
void f_171C_1C0A(char **handle);
char **f_171C_1B2C(char **handle, int32_t size, int16_t flags);
char **f_171C_18A6(char **handle, int32_t size, int16_t flags);
int32_t f_171C_1C1C(char **handle);
int32_t f_171C_16EA(char **handle);
int16_t f_171C_1686(char **handle);
int16_t f_171C_1AD4(char **handle);
int16_t f_171C_1794(char **handle);
int16_t f_171C_1E9A(char **handle);
void f_171C_1804(char **handle);
void f_171C_1C82(char **handle);
void f_171C_1E86(char **handle, int16_t flags);
void f_171C_20E2(char **handle);
void f_171C_1EFA(void);
int16_t f_171C_0EDE(void);
int32_t f_171C_1750(void);
int32_t f_171C_1772(void);
char *f_171C_1D40(char **handle);
uint32_t f_171C_14BE(char **handle);
void f_171C_152C(char **handle);
void f_171C_15A2(char **handle, int16_t flags);
char **f_171C_2086(char **handle);
char *f_171C_2190(uint16_t size, char *name);
char *f_171C_21CC(uint16_t size);
void f_171C_0676(void);
SimHandleStatus sim_handles_global_last_status(void);
SimHandleStatus sim_handles_global_configure(size_t capacity_bytes, size_t max_handles);
/* Read-only resource views: no extra lock or ownership transfer. */
int sim_handles_global_resolve_payload(const void *handle,
                                      const uint8_t **bytes, size_t *size);
int sim_handles_global_measure_payload(const void *address, size_t *remaining);
/* Appends a logical handle inventory. Payload sizes are native bytes; physical
 * DOS paragraph ordering and addresses are unavailable in this provider. */
int sim_handles_dump(const char *path, const char *where);
void f_171C_030C(char *where);
char **f_2CFB_0002(int32_t size, int16_t flags, char *name);
void f_2CFB_0007(char **handle);
void f_2CFB_002F(char **handle, int16_t flags);

#ifdef __cplusplus
}
#endif
#endif
