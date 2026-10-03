#ifndef SIMANT_PORTABLE_WHOLE_PROGRAM_WINDOW_REFS_H
#define SIMANT_PORTABLE_WHOLE_PROGRAM_WINDOW_REFS_H

#include <stddef.h>
#include <stdint.h>

/* Host references for one live root-window buffer. `wire` is the mutable DOS
 * record/storage bytes; `object_table` and the Handle lvalues are separate
 * host-width sidecars and never alias the fixed-width fields in `wire`. */
typedef struct SimWindowRefView {
    uint8_t *wire;
    char **source_handle; /* Borrowed owner cell; the only live data pointer. */
    size_t extent;
    uint16_t count;
    char **object_table;
    uint16_t *object_offsets;
    uint16_t *object_sizes;
    uint8_t *object_types;
    char ***object_handles_2a;
    char ***object_handles_34;
} SimWindowRefView;

enum { SIM_WINDOW_REF_REGISTRY_CAPACITY = 45 };

typedef struct SimWindowRefEntry {
    char **source_handle; /* The native Handle cell from the resource owner. */
    size_t payload_extent;
    SimWindowRefView view;
    uint8_t bound;
} SimWindowRefEntry;

typedef struct SimWindowRefRegistry {
    SimWindowRefEntry entries[SIM_WINDOW_REF_REGISTRY_CAPACITY];
} SimWindowRefRegistry;

typedef enum SimWindowRefStatus {
    SIM_WINDOW_REFS_OK = 0,
    SIM_WINDOW_REFS_BAD_ARGUMENT,
    SIM_WINDOW_REFS_TRUNCATED,
    SIM_WINDOW_REFS_BAD_LAYOUT,
    SIM_WINDOW_REFS_OUT_OF_MEMORY,
    SIM_WINDOW_REFS_BAD_HANDLE_SLOT,
    SIM_WINDOW_REFS_UNRESOLVED_DOS_HANDLE
} SimWindowRefStatus;

/* Explicit-width accessors for source module field offsets when a native
 * struct layout would introduce host alignment or pointer-width changes. */
int16_t sim_window_wire_read_i16(const void *base, size_t offset);
uint16_t sim_window_wire_read_u16(const void *base, size_t offset);
void sim_window_wire_write_i16(void *base, size_t offset, int16_t value);
void sim_window_wire_write_u16(void *base, size_t offset, uint16_t value);

/* Bind the current source Handle payload before RepointObjects writes the
 * runtime pointer table. This validates the sequential layout and prepares
 * host sidecars; serialized four-byte table and Handle fields are preserved. */
SimWindowRefStatus sim_window_refs_bind(SimWindowRefView *view,
                                        char **source_handle, size_t extent);
/* Repoint a movable live buffer using the already checked sequential object
 * extents after the source handle cell has changed. On failure, the sidecar
 * table remains bound to its previous buffer; the caller still owns the
 * updated allocator Handle cell and must recover/fail that allocation there. */
SimWindowRefStatus sim_window_refs_repoint(SimWindowRefView *view,
                                           size_t extent);
/* Source fmemset / pointer-null initialization performed by win_LoadWindow.
 * Only the observed type/offset/length pairs are accepted. */
SimWindowRefStatus sim_window_refs_clear_source_runtime_field(
    SimWindowRefView *view, uint16_t object_index,
    uint8_t object_offset, uint8_t byte_count);
void sim_window_refs_release(SimWindowRefView *view);

/* Source-compatible char** handle cell from the window owner; `*h` is the
 * live record buffer. No duplicate host data-pointer state is maintained. */
char **sim_window_refs_window_handle(SimWindowRefView *view);
/* Source-compatible char** object pointer table used by RepointObjects and
 * subsequent m20E8/m22BF/m21FA/m2505 consumers. */
char **sim_window_refs_object_table(SimWindowRefView *view);
/* Source code stores Handle (char far * far *) fields at object-relative
 * +0x2a (types 16–18) and +0x34 (types 4,10). Return the real native
 * char*** lvalue; unsupported type/offset/extent returns NULL. */
char ***sim_window_refs_handle_slot(SimWindowRefView *view,
                                    uint16_t object_index,
                                    uint8_t object_offset);
SimWindowRefStatus sim_window_refs_get_handle_slot(
    SimWindowRefView *view, uint16_t object_index, uint8_t object_offset,
    char ****slot_out);
const char *sim_window_refs_status_string(SimWindowRefStatus status);

/* One entry per DOS window number. The caller passes the real native Handle
 * cell returned by the allocator/database owner plus its exact payload size. */
void sim_window_ref_registry_init(SimWindowRefRegistry *registry);
SimWindowRefStatus sim_window_ref_registry_attach(
    SimWindowRefRegistry *registry, uint16_t window_number,
    char **source_handle, size_t payload_extent);
SimWindowRefStatus sim_window_ref_registry_repoint(
    SimWindowRefRegistry *registry, uint16_t window_number,
    size_t payload_extent);
SimWindowRefStatus sim_window_ref_registry_repoint_handle(
    SimWindowRefRegistry *registry, uint16_t window_number,
    char **source_handle, size_t payload_extent);
/* Source allocation size is a signed DOS long; reject negative or narrowing
 * values before treating it as a host extent. */
SimWindowRefStatus sim_window_ref_registry_repoint_handle_signed(
    SimWindowRefRegistry *registry, uint16_t window_number,
    char **source_handle, int64_t payload_extent);
void sim_window_ref_registry_detach(SimWindowRefRegistry *registry,
                                    uint16_t window_number);
char **sim_window_ref_registry_handle(SimWindowRefRegistry *registry,
                                     uint16_t window_number);
char **sim_window_ref_registry_objects_for_buffer(
    SimWindowRefRegistry *registry, const char *window_buffer);
char ***sim_window_ref_registry_handle_slot_for_buffer(
    SimWindowRefRegistry *registry, const char *window_buffer,
    uint16_t object_index, uint8_t object_offset);
char ***sim_window_ref_registry_handle_slot_for_object(
    SimWindowRefRegistry *registry, const char *object_bytes,
    uint8_t object_offset);
SimWindowRefStatus sim_window_ref_registry_clear_runtime_for_object(
    SimWindowRefRegistry *registry, const char *object_bytes,
    uint8_t object_offset, uint8_t byte_count);
/* Native translation of win_LoadAllWindows' fixed DOS-byte clear. */
void sim_window_clear_draw_hooks(void (**hooks)(int phase), size_t count);

#endif
