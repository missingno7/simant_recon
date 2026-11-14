/* Read-only step observer, linked only by step_check.py. Environment gates it.
 * Offsets come from this executable's DWARF, not a presumed native layout. */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef SIMANT_TEST_KEY_ALIASES
/* DOS recipe tokens have no spaces. SDL's modifier/Escape names do.
 * A ~suffix supplies SDL modifiers derived from the physical input tape.
 * The existing host constructs and admits the SDL event through its adapter.
 * The production platform and SDL event projection stay untouched. */
extern uint32_t __real_SDL_GetKeyFromName(const char *);
extern int __real_SDL_GetScancodeFromKey(uint32_t, uint16_t *);
static unsigned replay_has_modifiers;
static uint16_t replay_modifiers;
uint32_t __wrap_SDL_GetKeyFromName(const char *name) {
  char token[64];
  const char *suffix = strchr(name, '~');
  replay_has_modifiers = suffix != NULL;
  if (suffix) {
    char *end;
    size_t length = (size_t)(suffix - name);
    unsigned long bits = strtoul(suffix + 1, &end, 10);
    if (!length || length >= sizeof(token) || end == suffix + 1 || *end || bits & ~65ul)
      abort();
    memcpy(token, name, length);token[length] = 0;name = token;
    replay_modifiers = (uint16_t)bits;
  }
  const char *sdl_name = !strcmp(name, "lctrl")    ? "Left Ctrl"
                         : !strcmp(name, "lshift") ? "Left Shift"
                         : !strcmp(name, "esc")    ? "Escape"
                         : !strcmp(name, "enter")  ? "Return"
                         : !strcmp(name, "kp_5")   ? "Keypad 5"
                                                   : name;
  return __real_SDL_GetKeyFromName(sdl_name);
}
int __wrap_SDL_GetScancodeFromKey(uint32_t key, uint16_t *modifiers) {
  int scan = __real_SDL_GetScancodeFromKey(key, modifiers);
  if (replay_has_modifiers) {
    if (!modifiers) abort();
    *modifiers |= replay_modifiers;
    replay_has_modifiers = 0;
  }
  return scan;
}
#endif

extern uint32_t portable_test_clock_read(char, void *, uint32_t);
extern void portable_test_step_boundary(unsigned, unsigned);
extern void portable_test_before_poll(void) __attribute__((weak));
extern void portable_test_diagnostics(FILE *);
extern int portable_test_reference_end(void) __attribute__((weak));
extern void __real_DoAntSim(void);
extern int32_t __real_MacTickCount(void);

#ifdef SIMANT_TEST_DEVICE_SERVICES
/* Keep the canonical service's side effects, then sample its completed answer.
 * With no tape portable_test_clock_read returns the real host answer. */
extern int16_t __real_snd_service_and_test_stopped(void);
int16_t __wrap_snd_service_and_test_stopped(void) {
  int16_t value = __real_snd_service_and_test_stopped();
  return (int16_t)portable_test_clock_read('h', __builtin_return_address(0),
                                         (uint16_t)value);
}
extern uint8_t __real_snd_port_read_byte(int16_t);
uint8_t __wrap_snd_port_read_byte(int16_t port) {
  uint8_t value = __real_snd_port_read_byte(port);
  return (uint8_t)portable_test_clock_read('j', __builtin_return_address(0), value);
}
#endif

typedef struct Slice {
  int64_t delta;
  unsigned bytes;
} Slice;
typedef struct View {
  unsigned verdict, bytes, sentinel, count;
  Slice *slices;
  uint8_t *data;
} View;
static View *views;
static unsigned count, step, limit, active, first_difference;
static FILE *expected, *actual, *result;
static char dump_path[2048];
static unsigned state_clock;
static unsigned state_entries(void) { return first_difference ? first_difference : step; }

extern void portable_test_screen(FILE *, const void *) __attribute__((weak));
static unsigned capture_screen(void) {
  static unsigned loaded, entries[4096], total, next;
  static int64_t palette_delta;
  static char directory[2048];
  if (!loaded++) {
    const char *path=getenv("SIMANT_TEST_FRAME_CONFIG");
    if (!path) return 0;
    FILE *f=fopen(path,"r");
    if (!f || !portable_test_screen || !fgets(directory,sizeof(directory),f)) abort();
    directory[strcspn(directory,"\r\n")]=0;
    if (fscanf(f,"%" SCNd64 " %u",&palette_delta,&total)!=2 || total>4096) abort();
    for (unsigned i=0;i<total;++i)
      if (fscanf(f,"%u",entries+i)!=1 || !entries[i] || (i && entries[i]<=entries[i-1])) abort();
    fclose(f);
  }
  if (next<total && entries[next]==step) {
    char path[2200];snprintf(path,sizeof(path),"%s/native.screen.%u",directory,step);
    FILE *f=fopen(path,"wb");if (!f) abort();
    portable_test_screen(f,(const void *)((uintptr_t)portable_test_clock_read+palette_delta));
    if (fclose(f)) abort();
    ++next;
    return 1;
  }
  return 0;
}

int portable_test_clock_is_stateful(void) { return state_clock; }

int32_t __wrap_MacTickCount(void) {
  static int loaded, disabled;
  static int64_t pacing[8];
  static unsigned pacing_count;
  if (!loaded) {
    loaded = 1;
    disabled = getenv("SIMANT_TEST_DISABLE_CLOCK") != NULL;
    const char *text = getenv("SIMANT_TEST_PACING_CALLS");
    while (text && *text) {
      char *end;
      if (pacing_count == 8)
        abort();
      pacing[pacing_count++] = strtoll(text, &end, 10);
      if (*end && *end != ',')
        abort();
      text = *end ? end + 1 : end;
    }
  }
  int64_t caller = (int64_t)(uintptr_t)__builtin_return_address(0) -
                   (int64_t)(uintptr_t)portable_test_clock_read;
  unsigned previous = state_clock;
  state_clock = disabled && step > 0;
  for (unsigned i = 0; i < pacing_count; ++i)
    if (caller == pacing[i])
      state_clock = 0;
  int32_t value = __real_MacTickCount();
  state_clock = previous;
  return value;
}

static void load(void) {
  static unsigned loaded;
  const char *path;
  char line[2048];
  FILE *config;
  if (loaded++)
    return;
  path = getenv("SIMANT_TEST_STEP_CONFIG");
  if (!path)
    return;
  config = fopen(path, "r");
  if (!config)
    abort();
  FILE **files[] = {&expected, &actual, &result};
  for (unsigned i = 0; i < 3; ++i) {
    if (!fgets(line, sizeof(line), config))
      abort();
    line[strcspn(line, "\r\n")] = 0;
    *files[i] = fopen(line, i ? "wb" : "rb");
    if (!*files[i])
      abort();
  }
  if (!fgets(dump_path, sizeof(dump_path), config))
    abort();
  dump_path[strcspn(dump_path, "\r\n")] = 0;
  if (fscanf(config, "%u %u", &count, &limit) != 2 || !count || !limit)
    abort();
  views = calloc(count, sizeof(*views));
  if (!views)
    abort();
  for (unsigned i = 0; i < count; ++i) {
    View *v = &views[i];
    if (fscanf(config, "%u %u %u %u", &v->verdict, &v->bytes, &v->sentinel,
               &v->count) != 4 ||
        !v->count || !v->bytes)
      abort();
    v->slices = calloc(v->count, sizeof(*v->slices));
    v->data = malloc(v->bytes);
    if (!v->slices || !v->data)
      abort();
    unsigned total = 0;
    for (unsigned j = 0; j < v->count; ++j) {
      if (fscanf(config, "%" SCNd64 " %u", &v->slices[j].delta,
                 &v->slices[j].bytes) != 2)
        abort();
      total += v->slices[j].bytes;
    }
    if (total != v->bytes)
      abort();
  }
  fclose(config);
  active = 1;
}

void portable_test_replay_error(const char *message) {
  load();
  if (!active)
    abort();
  fprintf(result,
          "{\"steps_compared\":%u,\"missing_step\":%u,\"replay_error\":\"%s\",",
          state_entries(), step + 1, message);
  portable_test_diagnostics(result);
  fputs("}\n", result);
  fclose(actual);
  fclose(expected);
  fclose(result);
  fflush(NULL);
  _Exit(12);
}

static uint32_t fingerprint(View *v) {
  unsigned length = v->bytes;
  if (v->sentinel) {
    for (unsigned i = 0; i + 1 < length; i += 2)
      if (v->data[i] == 0 && v->data[i + 1] == 128) {
        length = i + 2;
        break;
      }
  }
  uint32_t hash = 2166136261u;
  for (unsigned i = 0; i < length; ++i)
    hash = (hash ^ v->data[i]) * 16777619u;
  return hash;
}

static void dump_state_to(const char *path) {
  FILE *dump = fopen(path, "wb");
  if (!dump) abort();
  for (unsigned i = 0; i < count; ++i)
    if (fwrite(views[i].data, 1, views[i].bytes, dump) != views[i].bytes) abort();
  if (fclose(dump)) abort();
}
static void dump_state(void) { dump_state_to(dump_path); }

static void finish(unsigned differs) {
  if ((!differs || getenv("SIMANT_TEST_FRAME_CONFIG")) &&
      portable_test_reference_end && !portable_test_reference_end())
    portable_test_replay_error("Reference ended with unconsumed service inputs");
  fprintf(result, "{\"steps_compared\":%u,\"first_differing_step\":%u,\"frame_entry_reached\":%u,",
          state_entries(), differs ? first_difference : 0, step);
  portable_test_diagnostics(result);
  fputs("}\n", result);
  fclose(result);
  fclose(actual);
  fclose(expected);
  if (!first_difference) dump_state();
  /* State stops at its first difference. With checkpoint capture enabled,
   * services/input and pictures continue independently to the requested end. */
  fflush(NULL);
  _Exit(differs ? 10 : 0);
}

extern void portable_test_audio_content_checkpoint(void) __attribute__((weak));
void __wrap_DoAntSim(void) {
  load();
  if (!active) {
    __real_DoAntSim();
    return;
  }
  ++step;
  portable_test_step_boundary(step, 1);
  if(portable_test_audio_content_checkpoint) portable_test_audio_content_checkpoint();
  unsigned checkpoint = capture_screen();
  unsigned differs = 0;
  for (unsigned i = 0; !first_difference && i < count; ++i) {
    View *v = &views[i];
    unsigned offset = 0;
    for (unsigned j = 0; j < v->count; ++j) {
      uintptr_t at = (uintptr_t)portable_test_clock_read + v->slices[j].delta;
      memcpy(v->data + offset, (const void *)at, v->slices[j].bytes);
      offset += v->slices[j].bytes;
    }
    uint32_t hash = fingerprint(v), reference;
    if (fread(&reference, sizeof(reference), 1, expected) != 1)
      abort();
    if (fwrite(&hash, sizeof(hash), 1, actual) != 1)
      abort();
    if (v->verdict==1 && hash != reference)
      differs = 1;
  }
  fflush(actual);
  /* Same read-only bytes as the hash row, before any simulation/input work.
   * Keep exact checkpoint bytes for auditing separate diagnostic views too. */
  if (checkpoint && !first_difference) {
    char path[2200];
    snprintf(path, sizeof(path), "%s.%u", dump_path, step);
    dump_state_to(path);
  }
  if (differs) { first_difference=step;dump_state(); }
  if (step == limit || (first_difference && !getenv("SIMANT_TEST_FRAME_CONFIG")))
    finish(first_difference);
  if (portable_test_before_poll) portable_test_before_poll();
  __real_DoAntSim();
  portable_test_step_boundary(step, 0);
}

#ifdef SIMANT_TEST_SOUND_SERVICES
#include "sound_services.inc"
static const struct SoundService { unsigned id;void (*function)(void); } sound_services[] = {
#define SOUND_SERVICE(id,symbol) {id,symbol},
#include "sound_services.inc"
#undef SOUND_SERVICE
};
extern int portable_whole_audio_isr_active(void) __attribute__((weak));
extern void portable_test_sound_entry(unsigned);
extern void portable_test_sound_call(unsigned,unsigned,void *);
extern void __real_snd_expand_sample_resource(char ***,uint16_t *,int16_t,int16_t);
void __wrap_snd_expand_sample_resource(char ***handle,uint16_t *size,int16_t object,int16_t type) {
  if (!portable_whole_audio_isr_active || !portable_whole_audio_isr_active()) {
    portable_test_sound_call((uint16_t)object,(uint16_t)type,__builtin_return_address(0));
    if (type==5) portable_test_sound_entry(SOUND_SAMPLE_RESOURCE_ID);
  }
  __real_snd_expand_sample_resource(handle,size,object,type);
}
static struct SoundSlot { void *function;unsigned id; } sound_slots[256];
static unsigned sound_slots_ready;
static unsigned sound_slot(void *function) {
  uintptr_t address=(uintptr_t)function;
  return (unsigned)((address>>4)^(address>>16))&255;
}
static unsigned sound_id(void *function) {
  if (!sound_slots_ready) {
    sound_slots_ready=1;
    for (unsigned i=0;i<sizeof(sound_services)/sizeof(*sound_services);++i) {
      void *entry=(void *)sound_services[i].function;
      if (!entry) continue;
      unsigned at=sound_slot(entry);
      while (sound_slots[at].function) {
        if (sound_slots[at].function==entry) abort(); /* Ambiguous function identity. */
        at=(at+1)&255;
      }
      sound_slots[at].function=entry;sound_slots[at].id=sound_services[i].id;
    }
  }
  unsigned at=sound_slot(function);
  while (sound_slots[at].function) {
    if (sound_slots[at].function==function) return sound_slots[at].id;
    at=(at+1)&255;
  }
  return 0;
}
#endif

/* GCC entry instrumentation covers internal calls within a translation unit,
 * which the linker's --wrap does not intercept. Bodies and arguments stay
 * canonical; the input boundaries and reviewed foreground sound entries advance
 * the observer. Sound ISR calls are filtered by actual execution context. */
extern void portable_test_before_poll(void) __attribute__((weak));
extern void portable_test_input_sample(unsigned, unsigned) __attribute__((weak));
extern int16_t StillDown(void) __attribute__((weak));
extern int16_t edit_scroll_and_redraw(int16_t, int16_t) __attribute__((weak));
__attribute__((no_instrument_function)) void __cyg_profile_func_enter(void *function, void *caller) {
  (void)caller;
#ifdef SIMANT_TEST_SOUND_SERVICES
  if (portable_whole_audio_isr_active && portable_whole_audio_isr_active()) return;
  unsigned sound=sound_id(function);
  if (sound==SOUND_SAMPLE_RESOURCE_ID) return; /* Typed wrapper qualifies the generic hook. */
  if (sound) { portable_test_sound_entry(sound);return; }
#endif
  unsigned kind;
  if (function==(void *)edit_scroll_and_redraw) kind=246;
  else return;
  if (portable_test_before_poll) portable_test_before_poll();
  if (portable_test_input_sample) portable_test_input_sample(kind,0);
}
__attribute__((no_instrument_function)) void __cyg_profile_func_exit(void *function, void *caller) {
  (void)caller;
  if (function==(void *)StillDown && portable_test_input_sample) portable_test_input_sample(247,0);
}

#ifdef SIMANT_TEST_AUDIO_CONTENT
#include "native_audio_content.inc"
#endif
