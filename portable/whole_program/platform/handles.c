#include "handles.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdio.h>
#include <time.h>
#define MAX_DOS_HANDLE_SLOTS 65536u
#define DOS_INDEX_TAG ((uintptr_t)0x0F0F0000u)
#define DOS_INDEX_MASK ((uintptr_t)0xFFFF0000u)
#define HANDLE_NAME_CAP 13u
#define DEFAULT_GLOBAL_CAPACITY SIZE_MAX
#define LOCK_DEPTH_MAX 100u
typedef struct SimHandleSlot {
    char *data;
                 /* first member: source-compatible char ** master pointer */    size_t size;
    size_t charged;
    uint32_t age;
    uint32_t index;
    uint8_t type;
    uint8_t lock_count;
    uint8_t attributes;
    uint8_t no_ems_hint;
    uint8_t live;
    char name[HANDLE_NAME_CAP];
}
 SimHandleSlot;
struct SimHandleManager {
    SimHandleSlot **slots;
    size_t slot_count;
    size_t slot_capacity;
    size_t max_handles;
    size_t capacity_bytes;
    size_t used_bytes;
    uint32_t age;
    SimHandleStatus last_status;
}
;
typedef struct DosPointerEntry {
    struct DosPointerEntry *next;
    SimHandle handle;
}
 DosPointerEntry;
static SimHandleManager *g_handles;
static DosPointerEntry *g_dos_ptrs;
static SimHandleStatus set_status(SimHandleManager *m, SimHandleStatus status){
    if (m) m->last_status = status;
    return status;
}
static int valid_type(uint8_t type){
    return type == SIM_HANDLE_HARD || type == SIM_HANDLE_FIRM ||           type == SIM_HANDLE_SYSTEM || type == SIM_HANDLE_SOFT;
}
static void copy_name(char out[HANDLE_NAME_CAP], const char *name){
    size_t i;
    if (!name) name = "";
    for (i = 0;
 i < HANDLE_NAME_CAP - 1 && name[i];
 ++i) out[i] = name[i];
    out[i] = '\0';
    while (++i < HANDLE_NAME_CAP) out[i] = '\0';
}
static SimHandle make_real_handle(SimHandleSlot *slot){
    return slot ? (SimHandle)&slot->data : NULL;
}
static SimHandle make_index_token(const SimHandleSlot *slot){
    uintptr_t token;
    if (!slot || slot->index >= MAX_DOS_HANDLE_SLOTS) return NULL;
    token = DOS_INDEX_TAG + (uintptr_t)slot->index;
    return (SimHandle)token;
}
static int decode_index_token(SimHandle handle, uint32_t *index){
    uintptr_t value = (uintptr_t)handle;
    if ((value & DOS_INDEX_MASK) != DOS_INDEX_TAG) return 0;
    if (index) *index = (uint32_t)(value & (uintptr_t)0xFFFFu);
    return 1;
}
static SimHandleSlot *slot_for(SimHandleManager *m, SimHandle handle){
    size_t i;
    uint32_t index;
    if (!m || !handle) return NULL;
    if (decode_index_token(handle, &index)) {
        if ((size_t)index >= m->slot_count) return NULL;
        return m->slots[index] && m->slots[index]->live ? m->slots[index] : NULL;
    }
    for (i = 0;
 i < m->slot_count;
 ++i) {
        SimHandleSlot *slot = m->slots[i];
        if (slot && slot->live && make_real_handle(slot) == handle) return slot;
    }
    return NULL;
}
static int reserve_slots(SimHandleManager *m, size_t needed){
    size_t cap;
    SimHandleSlot **slots;
    if (needed <= m->slot_capacity) return 1;
    cap = m->slot_capacity ? m->slot_capacity : 16;
    while (cap < needed) {
        if (cap > m->max_handles / 2) {
 cap = m->max_handles;
 break;
 }
        cap *= 2;
    }
    if (cap < needed || cap > SIZE_MAX / sizeof(*slots)) return 0;
    slots = (SimHandleSlot **)realloc(m->slots, cap * sizeof(*slots));
    if (!slots) return 0;
    memset(slots + m->slot_capacity, 0, (cap - m->slot_capacity) * sizeof(*slots));
    m->slots = slots;
    m->slot_capacity = cap;
    return 1;
}
static SimHandleSlot *acquire_slot(SimHandleManager *m){
    size_t i;
    SimHandleSlot *slot;
    for (i = 0;
 i < m->slot_count;
 ++i) {
        if (m->slots[i] && !m->slots[i]->live) return m->slots[i];
    }
    if (m->slot_count >= m->max_handles || m->slot_count >= MAX_DOS_HANDLE_SLOTS ||        !reserve_slots(m, m->slot_count + 1)) return NULL;
    slot = (SimHandleSlot *)calloc(1, sizeof(*slot));
    if (!slot) return NULL;
    slot->index = (uint32_t)m->slot_count;
    m->slots[m->slot_count++] = slot;
    return slot;
}
static size_t charged_size(size_t size){
    /* DOS reserves paragraph-rounded payload bytes, not its 32-byte header. */    if (size > SIZE_MAX - 15u) return SIZE_MAX;
    return (size + 15u) & ~(size_t)15u;
}
static int can_charge(const SimHandleManager *m, size_t amount){
    return amount <= m->capacity_bytes && m->used_bytes <= m->capacity_bytes - amount;
}
static SimHandleStatus require_slot(SimHandleManager *m, SimHandle h, SimHandleSlot **out){
    SimHandleSlot *slot = slot_for(m, h);
    if (!slot) return set_status(m, SIM_HANDLE_INVALID_HANDLE);
    if (out) *out = slot;
    return SIM_HANDLE_OK;
}
SimHandleManager *sim_handles_create(size_t capacity_bytes, size_t max_handles){
    SimHandleManager *m;
    if (!max_handles || max_handles > MAX_DOS_HANDLE_SLOTS) return NULL;
    m = (SimHandleManager *)calloc(1, sizeof(*m));
    if (!m) return NULL;
    m->capacity_bytes = capacity_bytes;
    m->max_handles = max_handles;
    m->last_status = SIM_HANDLE_OK;
    return m;
}
void sim_handles_destroy(SimHandleManager *m){
    size_t i;
    if (!m) return;
    for (i = 0;
 i < m->slot_count;
 ++i) {
        if (m->slots[i]) {
 free(m->slots[i]->data);
 free(m->slots[i]);
 }
    }
    free(m->slots);
    if (m == g_handles) g_handles = NULL;
    free(m);
}
void sim_handles_reset(SimHandleManager *m){
    size_t i;
    if (!m) return;
    for (i = 0;
 i < m->slot_count;
 ++i) {
        SimHandleSlot *s = m->slots[i];
        if (s) {
 free(s->data);
 memset(s, 0, sizeof(*s));
 s->index = (uint32_t)i;
 }
    }
    m->used_bytes = 0;
 m->age = 0;
 m->last_status = SIM_HANDLE_OK;
}
SimHandleStatus sim_handles_last_status(const SimHandleManager *m){
    return m ? m->last_status : SIM_HANDLE_INVALID_ARGUMENT;
}
static size_t discard_oldest_soft(SimHandleManager *m, const SimHandleSlot *exclude){
    SimHandleSlot *oldest = NULL;
    size_t i;
    for (i = 0;
 i < m->slot_count;
 ++i) {
        SimHandleSlot *s = m->slots[i];
        if (!s || s == exclude || !s->live || s->type != SIM_HANDLE_SOFT || s->lock_count || !s->data) continue;
        if (!oldest || s->age < oldest->age) oldest = s;
    }
    if (!oldest) return 0;
    free(oldest->data);
 oldest->data = NULL;
    m->used_bytes -= oldest->charged;
    {
 size_t reclaimed = oldest->charged;
 oldest->charged = 0;
 oldest->type = SIM_HANDLE_DISCARDED;
 return reclaimed;
 }
}
static size_t reclaim_to_budget(SimHandleManager *m, size_t need_bytes, const SimHandleSlot *exclude){
    size_t reclaimed = 0;
    while (!can_charge(m, need_bytes)) {
        size_t n = discard_oldest_soft(m, exclude);
        if (!n) break;
        reclaimed += n;
    }
    set_status(m, can_charge(m, need_bytes) ? SIM_HANDLE_OK : SIM_HANDLE_NO_MEMORY);
    return reclaimed;
}
size_t sim_handles_reclaim(SimHandleManager *m, size_t need_bytes){
    if (!m) return 0;
    return reclaim_to_budget(m, need_bytes, NULL);
}
SimHandleStatus sim_handles_allocate(SimHandleManager *m, int32_t size, int16_t flags,                                     const char *name, SimHandle *out_handle){
    int base_type;
    size_t bytes, charge;
    SimHandleSlot *slot;
    char *data;
    if (out_handle) *out_handle = NULL;
    if (!m || !out_handle || size <= 0) return set_status(m, SIM_HANDLE_INVALID_ARGUMENT);
    base_type = (flags & ~8) & ~0x70;
    if (!valid_type((uint8_t)base_type)) return set_status(m, SIM_HANDLE_BAD_TYPE);
    bytes = (size_t)size;
 charge = charged_size(bytes);
    if (charge == SIZE_MAX) return set_status(m, SIM_HANDLE_NO_MEMORY);
    if (!can_charge(m, charge)) reclaim_to_budget(m, charge, NULL);
    if (!can_charge(m, charge)) return set_status(m, SIM_HANDLE_NO_MEMORY);
    data = (char *)malloc(bytes);
    if (!data) {
        while (!data && discard_oldest_soft(m, NULL)) data = (char *)malloc(bytes);
        if (!data) return set_status(m, SIM_HANDLE_NO_MEMORY);
    }
    slot = acquire_slot(m);
    if (!slot) {
 free(data);
 return set_status(m, SIM_HANDLE_HANDLE_LIMIT);
 }
    slot->data = data;
 slot->size = bytes;
 slot->charged = charge;
    slot->type = (uint8_t)base_type;
 slot->attributes = (uint8_t)(flags & 0x70);
    slot->no_ems_hint = (uint8_t)((flags & 8) != 0);
 slot->lock_count = 0;
    slot->age = ++m->age;
 slot->live = 1;
 copy_name(slot->name, name);
    m->used_bytes += charge;
 *out_handle = make_real_handle(slot);
    return set_status(m, SIM_HANDLE_OK);
}
SimHandleStatus sim_handles_resolve(SimHandleManager *m, SimHandle h, SimHandle *out_real){
    SimHandleSlot *s;
    if (out_real) *out_real = NULL;
    if (!m || !out_real) return set_status(m, SIM_HANDLE_INVALID_ARGUMENT);
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    *out_real = make_real_handle(s);
 return set_status(m, SIM_HANDLE_OK);
}
SimHandle sim_handles_index_token(SimHandleManager *m, SimHandle h){
    SimHandleSlot *s;
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return NULL;
    set_status(m, SIM_HANDLE_OK);
 return make_index_token(s);
}
SimHandleStatus sim_handles_lock(SimHandleManager *m, SimHandle h, char **out_data){
    SimHandleSlot *s;
    if (out_data) *out_data = NULL;
    if (!m || !out_data) return set_status(m, SIM_HANDLE_INVALID_ARGUMENT);
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    if (s->type == SIM_HANDLE_DISCARDED || !s->data) return set_status(m, SIM_HANDLE_DISCARDED_DATA);
    if (s->lock_count >= LOCK_DEPTH_MAX) return set_status(m, SIM_HANDLE_LOCK_LIMIT);
    ++s->lock_count;
 s->age = ++m->age;
 *out_data = s->data;
    return set_status(m, SIM_HANDLE_OK);
}
SimHandleStatus sim_handles_unlock(SimHandleManager *m, SimHandle h, SimHandle *out_index){
    SimHandleSlot *s;
    if (out_index) *out_index = NULL;
    if (!m) return SIM_HANDLE_INVALID_ARGUMENT;
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    if (!s->lock_count) return set_status(m, SIM_HANDLE_UNLOCKED);
    --s->lock_count;
    if (out_index) *out_index = make_index_token(s);
    return set_status(m, SIM_HANDLE_OK);
}
SimHandleStatus sim_handles_free(SimHandleManager *m, SimHandle h){
    SimHandleSlot *s;
    if (!m) return SIM_HANDLE_INVALID_ARGUMENT;
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    if (s->lock_count) return set_status(m, SIM_HANDLE_LOCKED);
    free(s->data);
 s->data = NULL;
    if (s->charged <= m->used_bytes) m->used_bytes -= s->charged;
    s->size = s->charged = 0;
 s->type = 0;
 s->attributes = 0;
    s->no_ems_hint = 0;
 s->age = 0;
 s->live = 0;
 s->name[0] = '\0';
    return set_status(m, SIM_HANDLE_OK);
}
SimHandleStatus sim_handles_resize(SimHandleManager *m, SimHandle h, int32_t size, int16_t flags){
    SimHandleSlot *s;
    size_t new_size, new_charge, old_charge, copy_n;
    int base_type;
    char *new_data;
    if (!m || size <= 0) return set_status(m, SIM_HANDLE_INVALID_ARGUMENT);
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    if (s->lock_count) return set_status(m, SIM_HANDLE_LOCKED);
    if (s->type == SIM_HANDLE_DISCARDED || !s->data) return set_status(m, SIM_HANDLE_DISCARDED_DATA);
    base_type = (flags & ~8) & ~0x70;
    if (!valid_type((uint8_t)base_type)) return set_status(m, SIM_HANDLE_BAD_TYPE);
    new_size = (size_t)size;
 new_charge = charged_size(new_size);
 old_charge = s->charged;
    if (new_charge == SIZE_MAX) return set_status(m, SIM_HANDLE_NO_MEMORY);
    if (new_size == s->size) {
        s->attributes = (uint8_t)(flags & 0x70);
 s->no_ems_hint = (uint8_t)((flags & 8) != 0);
        s->age = ++m->age;
 return set_status(m, SIM_HANDLE_OK);
    }
    if (new_charge > old_charge && !can_charge(m, new_charge - old_charge)) reclaim_to_budget(m, new_charge - old_charge, s);
    if (new_charge > old_charge && !can_charge(m, new_charge - old_charge)) return set_status(m, SIM_HANDLE_NO_MEMORY);
    new_data = (char *)malloc(new_size);
    if (!new_data) {
        while (!new_data && discard_oldest_soft(m, s)) new_data = (char *)malloc(new_size);
        if (!new_data) return set_status(m, SIM_HANDLE_NO_MEMORY);
    }
    copy_n = s->size < new_size ? s->size : new_size;
    if (copy_n) memcpy(new_data, s->data, copy_n);
    free(s->data);
 s->data = new_data;
 s->size = new_size;
 s->charged = new_charge;
    if (new_charge >= old_charge) m->used_bytes += new_charge - old_charge;
    else m->used_bytes -= old_charge - new_charge;
    s->type = (uint8_t)base_type;
 s->attributes = (uint8_t)(flags & 0x70);
    s->no_ems_hint = (uint8_t)((flags & 8) != 0);
 s->age = ++m->age;
    return set_status(m, SIM_HANDLE_OK);
}
SimHandleStatus sim_handles_discard(SimHandleManager *m, SimHandle h){
    SimHandleSlot *s;
    if (!m) return SIM_HANDLE_INVALID_ARGUMENT;
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    if (s->lock_count) return set_status(m, SIM_HANDLE_LOCKED);
    if (s->type == SIM_HANDLE_DISCARDED) return set_status(m, SIM_HANDLE_OK);
    free(s->data);
 s->data = NULL;
    if (s->charged <= m->used_bytes) m->used_bytes -= s->charged;
    s->charged = 0;
 s->type = SIM_HANDLE_DISCARDED;
    return set_status(m, SIM_HANDLE_OK);
}
SimHandleStatus sim_handles_set_type(SimHandleManager *m, SimHandle h, int16_t flags){
    SimHandleSlot *s;
 int type;
    if (!m) return SIM_HANDLE_INVALID_ARGUMENT;
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    if (decode_index_token(h, NULL)) return set_status(m, SIM_HANDLE_INVALID_HANDLE);
    if (s->type == SIM_HANDLE_DISCARDED) return set_status(m, SIM_HANDLE_DISCARDED_DATA);
    type = flags & ~0x78;
    if (!valid_type((uint8_t)type)) return set_status(m, SIM_HANDLE_BAD_TYPE);
    s->type = (uint8_t)type;
 s->attributes = (uint8_t)(flags & 0x78);
    s->age = ++m->age;
 return set_status(m, SIM_HANDLE_OK);
}
SimHandleStatus sim_handles_info(SimHandleManager *m, SimHandle h, SimHandleInfo *out){
    SimHandleSlot *s;
    if (!m || !out) return set_status(m, SIM_HANDLE_INVALID_ARGUMENT);
    if (require_slot(m, h, &s) != SIM_HANDLE_OK) return m->last_status;
    out->size=s->size;
out->type=s->type;
out->lock_count=s->lock_count;
    out->attributes=s->attributes;
out->no_ems_hint=s->no_ems_hint;
    out->age=s->age;
out->name=s->name;
out->is_discarded=(s->type==SIM_HANDLE_DISCARDED);
    return set_status(m,SIM_HANDLE_OK);
}
size_t sim_handles_used_bytes(const SimHandleManager *m) {
 return m ? m->used_bytes : 0;
 }
size_t sim_handles_capacity_bytes(const SimHandleManager *m) {
 return m ? m->capacity_bytes : 0;
 }
size_t sim_handles_soft_bytes(const SimHandleManager *m){
    size_t i,total=0;
if(!m)return 0;
    for(i=0;
i<m->slot_count;
++i)if(m->slots[i]&&m->slots[i]->live&&m->slots[i]->type==SIM_HANDLE_SOFT) {
        if (SIZE_MAX-total < m->slots[i]->charged) return SIZE_MAX;
        total+=m->slots[i]->charged;
    }
    return total;
}
static SimHandleManager *global_manager(void){
    if (!g_handles) g_handles=sim_handles_create(DEFAULT_GLOBAL_CAPACITY,MAX_DOS_HANDLE_SLOTS);
    return g_handles;
}
SimHandleStatus sim_handles_global_last_status(void) {
 return sim_handles_last_status(g_handles);
 }
int sim_handles_global_resolve_payload(const void *handle,
                                      const uint8_t **bytes, size_t *size)
{
    SimHandleSlot *slot;
    if (!g_handles || !handle || !bytes || !size) return 0;
    slot = slot_for(g_handles, (SimHandle)handle);
    if (!slot || !slot->data || slot->type == SIM_HANDLE_DISCARDED) return 0;
    *bytes = (const uint8_t *)slot->data;
    *size = slot->size;
    return 1;
}
int sim_handles_global_measure_payload(const void *address, size_t *remaining)
{
    size_t i;
    uintptr_t p = (uintptr_t)address;
    if (!g_handles || !address || !remaining) return 0;
    for (i = 0; i < g_handles->slot_count; ++i) {
        SimHandleSlot *slot = g_handles->slots[i];
        uintptr_t base;
        if (!slot || !slot->live || !slot->data || slot->type == SIM_HANDLE_DISCARDED)
            continue;
        base = (uintptr_t)slot->data;
        if (p >= base && p - base < slot->size) {
            *remaining = slot->size - (size_t)(p - base);
            return 1;
        }
    }
    return 0;
}
SimHandleStatus sim_handles_global_configure(size_t capacity_bytes,size_t max_handles){
    size_t i;
    if (!max_handles || max_handles>MAX_DOS_HANDLE_SLOTS || g_dos_ptrs) return SIM_HANDLE_INVALID_ARGUMENT;
    if (g_handles) {
        for (i=0;
i<g_handles->slot_count;
++i) if(g_handles->slots[i]&&g_handles->slots[i]->live) return set_status(g_handles,SIM_HANDLE_LOCKED);
        sim_handles_destroy(g_handles);
    }
    g_handles=sim_handles_create(capacity_bytes,max_handles);
    return g_handles?SIM_HANDLE_OK:SIM_HANDLE_NO_MEMORY;
}
char **f_171C_13CA(int32_t size,int16_t flags,char *name){
 SimHandle h=NULL;
 sim_handles_allocate(global_manager(),size,flags,name,&h);
return h;
 }
char **f_171C_1A9E(int32_t size,int16_t flags,char *name){
 SimHandle h=f_171C_13CA(size,flags,name);
return h?sim_handles_index_token(global_manager(),h):NULL;
 }
char *f_171C_1B84(char **h){
 char *p=NULL;
sim_handles_lock(global_manager(),h,&p);
return p;
 }
char **f_171C_1BBA(char **h){
 SimHandle token=NULL;
sim_handles_unlock(global_manager(),h,&token);
return token;
 }
void f_171C_13E4(char **h) {
 sim_handles_free(global_manager(),h);
 }
void f_171C_1C0A(char **h) {
 f_171C_13E4(h);
 }
char **f_171C_1B2C(char **h,int32_t size,int16_t flags){
 SimHandle real=NULL;
if(sim_handles_resize(global_manager(),h,size,flags)!=SIM_HANDLE_OK)return NULL;
return sim_handles_resolve(global_manager(),h,&real)==SIM_HANDLE_OK?real:NULL;
 }
char **f_171C_18A6(char **h,int32_t size,int16_t flags) {
 return f_171C_1B2C(h,size,flags);
 }
int32_t f_171C_1C1C(char **h){
 SimHandleInfo i;
if(sim_handles_info(global_manager(),h,&i)!=SIM_HANDLE_OK||i.size>INT32_MAX)return 0;
return (int32_t)i.size;
 }
int32_t f_171C_16EA(char **h) {
 return f_171C_1C1C(h);
 }
int16_t f_171C_1686(char **h){
 SimHandleInfo i;
return sim_handles_info(global_manager(),h,&i)==SIM_HANDLE_OK?(int16_t)i.type:0;
 }
int16_t f_171C_1AD4(char **h){
 SimHandleInfo i;
return sim_handles_info(global_manager(),h,&i)==SIM_HANDLE_OK?(int16_t)i.lock_count:0;
 }
int16_t f_171C_1794(char **h) {
 return f_171C_1686(h)==SIM_HANDLE_DISCARDED;
 }
int16_t f_171C_1E9A(char **h){
 SimHandleInfo i;
if(sim_handles_info(global_manager(),h,&i)!=SIM_HANDLE_OK)return 0;
return 0;
 }
 /* Host has no DOS EMS region. */void f_171C_1804(char **h) {
 (void)sim_handles_discard(global_manager(),h);
 }
void f_171C_1C82(char **h) {
 SimHandle r=NULL;
if(sim_handles_resolve(global_manager(),h,&r)==SIM_HANDLE_OK)(void)sim_handles_set_type(global_manager(),r,SIM_HANDLE_SOFT);
 }
void f_171C_1E86(char **h,int16_t flags) {
 (void)sim_handles_set_type(global_manager(),h,flags);
 }
void f_171C_20E2(char **h) {
 SimHandle r=NULL;
if(sim_handles_resolve(global_manager(),h,&r)==SIM_HANDLE_OK)(void)sim_handles_set_type(global_manager(),r,SIM_HANDLE_SOFT);
 }
void f_171C_15A2(char **h,int16_t flags) {
 (void)sim_handles_set_type(global_manager(),h,flags);
 }
char **f_171C_2086(char **h) {
 return f_171C_1BBA(h);
 }
void f_171C_0676(void) {
 /* The original entry is explicitly empty. */ }
void f_171C_1EFA(void){
    SimHandleManager *m=global_manager();
size_t i;
    for(i=0;
m&&i<m->slot_count;
++i)if(m->slots[i]&&m->slots[i]->live&&m->slots[i]->type==SIM_HANDLE_SOFT&&!m->slots[i]->lock_count)        (void)sim_handles_discard(m,make_real_handle(m->slots[i]));
}
int16_t f_171C_0EDE(void) {
 return 0;
 }
 /* No segment-fragmented paragraph heap exists to relocate on host. */int32_t f_171C_1750(void){
 SimHandleManager*m=global_manager();
size_t n;
if(!m||m->capacity_bytes==SIZE_MAX)return -1;
n=m->capacity_bytes-m->used_bytes;
return n>INT32_MAX?INT32_MAX:(int32_t)n;
 }
int32_t f_171C_1772(void){
 size_t n=sim_handles_soft_bytes(global_manager());
return n>INT32_MAX?INT32_MAX:(int32_t)n;
 }
char *f_171C_1D40(char **h){
 SimHandleInfo i;
if(sim_handles_info(global_manager(),h,&i)!=SIM_HANDLE_OK)return NULL;
if(i.lock_count){
set_status(global_manager(),SIM_HANDLE_LOCKED);
return NULL;
}
return f_171C_1B84(h);
 }
uint32_t f_171C_14BE(char **h){
 SimHandleInfo i;
return sim_handles_info(global_manager(),h,&i)==SIM_HANDLE_OK?i.age-global_manager()->age:0;
 }
void f_171C_152C(char **h){
 SimHandleInfo i;
SimHandleManager*m=global_manager();
if(sim_handles_info(m,h,&i)==SIM_HANDLE_OK){
SimHandleSlot*s=slot_for(m,h);
s->age=++m->age;
}
 }
static SimHandle find_pointer(void *pointer){
    SimHandleManager*m=global_manager();
size_t i;
    for(i=0;
m&&i<m->slot_count;
++i)if(m->slots[i]&&m->slots[i]->live&&m->slots[i]->data==pointer)return make_real_handle(m->slots[i]);
    return NULL;
}
static void *dos_malloc_named(size_t size,const char*name){
    SimHandle h;
DosPointerEntry*e;
    if(!size)return NULL;
    h=f_171C_13CA((int32_t)size,0,name?(char*)name:"malloc");
if(!h)return NULL;
    e=(DosPointerEntry*)malloc(sizeof(*e));
if(!e){
f_171C_13E4(h);
return NULL;
}
    e->handle=h;
e->next=g_dos_ptrs;
g_dos_ptrs=e;
    /* The source malloc pointer is locked only transiently by its private setup. */    return *h;
}
void dos_free(void *pointer){
    DosPointerEntry **link=&g_dos_ptrs,*e;
SimHandle h;
    if(!pointer)return;
    while((e=*link)!=NULL){
if(e->handle&&*e->handle==pointer){
SimHandleSlot *s;
*link=e->next;
h=e->handle;
free(e);
if(require_slot(global_manager(),h,&s)==SIM_HANDLE_OK)s->lock_count=0;
(void)sim_handles_free(global_manager(),h);
return;
}
link=&e->next;
}
    /* OpenIndex retains the payload address returned by f_171C_13CA, then
     * CloseIndex calls source-visible free(payload). Resolve that live
     * payload identity back to its owning handle. */
    h=find_pointer(pointer);
    if(h){
        SimHandleSlot *s;
        if(require_slot(global_manager(),h,&s)==SIM_HANDLE_OK){
            if(s->lock_count){
                set_status(global_manager(),SIM_HANDLE_LOCKED);
                return;
            }
            (void)sim_handles_free(global_manager(),h);
            return;
        }
    }
    if(g_handles)g_handles->last_status=SIM_HANDLE_INVALID_HANDLE;
}
void *dos_realloc(void *pointer,uint16_t size){
    SimHandle h;
SimHandleSlot*s;
SimHandleManager*m=global_manager();
    if(!pointer)return dos_malloc((uint16_t)size);
    if(!size)return NULL;
    h=find_pointer(pointer);
if(!h)return NULL;
s=slot_for(m,h);
    if(sim_handles_resize(m,h,(int32_t)size,s->type)!=SIM_HANDLE_OK)return NULL;
    return s->data;
}
void *dos_malloc(uint16_t size) {
 return dos_malloc_named(size, "malloc");
 }
char *f_171C_2190(uint16_t size,char *name) {
 return (char *)dos_malloc_named(size,name);
 }
char *f_171C_21CC(uint16_t size) {
 return (char *)dos_malloc(size);
 }
char **f_2CFB_0002(int32_t size,int16_t flags,char *name) {
 return f_171C_13CA(size,flags,name);
 }
void f_2CFB_0007(char **handle) {
 f_171C_13E4(handle);
 }
void f_2CFB_002F(char **handle,int16_t flags) {
 f_171C_15A2(handle,flags);
 }

void *f_171C_2302(void *pointer, uint16_t size)
{
    return dos_realloc(pointer, size);
}

static const char *handle_type_name(uint8_t type)
{
    switch (type) {
    case SIM_HANDLE_SOFT: return "SOFT";
    case SIM_HANDLE_FIRM: return "FIRM";
    case SIM_HANDLE_HARD: return "HARD";
    case SIM_HANDLE_SYSTEM: return "SYSTEM";
    case SIM_HANDLE_DISCARDED: return "DISCARDED";
    default: return "BAD";
    }
}

int sim_handles_dump(const char *path, const char *where)
{
    SimHandleManager *m = global_manager();
    FILE *file;
    time_t now;
    struct tm *local;
    char stamp[64] = "time unavailable";
    size_t i, used = 0, free_bytes, hard = 0, firm = 0, soft = 0;
    if (!m || !path) return 0;
    file = fopen(path, "ab");
    if (!file) {
        set_status(m, SIM_HANDLE_IO_ERROR);
        return 0;
    }
    now = time(NULL);
    local = localtime(&now);
    if (local) (void)strftime(stamp, sizeof(stamp), "%c", local);
    for (i = 0; i < m->slot_count; ++i) {
        SimHandleSlot *s = m->slots[i];
        if (!s || !s->live) continue;
        ++used;
        if (s->type == SIM_HANDLE_HARD) hard += s->size;
        else if (s->type == SIM_HANDLE_FIRM) firm += s->size;
        else if (s->type == SIM_HANDLE_SOFT) soft += s->size;
    }
    free_bytes = m->capacity_bytes == SIZE_MAX ? SIZE_MAX :
        (m->capacity_bytes >= m->used_bytes ? m->capacity_bytes - m->used_bytes : 0);
    (void)fprintf(file, "\n\nRalloc native handle dump at %s, %s\n",
                  where ? where : "(null)", stamp);
    if (m->capacity_bytes == SIZE_MAX)
        (void)fprintf(file, "Free Space: unbounded, Used Space: %zu, Total Space: unbounded bytes\n", m->used_bytes);
    else
        (void)fprintf(file, "Free Space: %zu, Used Space: %zu, Total Space: %zu bytes\n",
                      free_bytes, m->used_bytes, m->capacity_bytes);
    (void)fprintf(file, "Hard space: %zu, Firm space: %zu, Soft space: %zu bytes\n",
                  hard, firm, soft);
    (void)fprintf(file, "Handles allocated: %zu, handles used: %zu max: %zu\n",
                  m->slot_count, used, m->max_handles);
    (void)fprintf(file, "By handles (native identities; DOS paragraph map unavailable):\n");
    for (i = m->slot_count; i > 0; --i) {
        SimHandleSlot *s = m->slots[i - 1];
        if (!s || !s->live) continue;
        (void)fprintf(file, "%p->%p: size=%zu, type=%c%s age=%5u name=%s\n",
                      (void *)&s->data, (void *)s->data, s->size,
                      s->lock_count ? '*' : ' ', handle_type_name(s->type),
                      m->age - s->age, s->name);
    }
    if (fclose(file) != 0) {
        set_status(m, SIM_HANDLE_IO_ERROR);
        return 0;
    }
    set_status(m, SIM_HANDLE_OK);
    return 1;
}

void f_171C_030C(char *where)
{
    (void)sim_handles_dump("ralloc.dmp", where);
}
