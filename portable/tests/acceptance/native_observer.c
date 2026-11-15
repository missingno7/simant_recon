/* Read-only step observer, linked only by native_build.py. Environment gates it.
 * Offsets come from this executable's DWARF, not a presumed native layout. */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "event_context_rule.h"
#include "animation_identity.h"
#include <windows.h>
static uint64_t collect_ticks, serialize_ticks, frame_ticks, dump_ticks, observed_bytes, hash_bytes, write_calls;
static uint64_t stamp(void) { LARGE_INTEGER t;QueryPerformanceCounter(&t);return (uint64_t)t.QuadPart; }
extern void portable_native_performance(FILE *) __attribute__((weak));
static void profile_result(FILE *f) {
  if(portable_native_performance) portable_native_performance(f);
  LARGE_INTEGER hz;QueryPerformanceFrequency(&hz);
  fprintf(f,"\"profile\":{\"collect_hash_seconds\":%.9f,\"serialize_seconds\":%.9f,\"checkpoint_seconds\":%.9f,\"dump_seconds\":%.9f,\"observed_bytes\":%" PRIu64 ",\"hash_bytes\":%" PRIu64 ",\"write_calls\":%" PRIu64 "},",
    (double)collect_ticks/hz.QuadPart,(double)serialize_ticks/hz.QuadPart,(double)frame_ticks/hz.QuadPart,(double)dump_ticks/hz.QuadPart,observed_bytes,hash_bytes,write_calls);
}

#ifdef SIMANT_TEST_KEY_ALIASES
/* DOS recipe tokens have no spaces. SDL's modifier/Escape names do.
 * The existing host constructs and admits events through its adapter. */
extern uint32_t __real_SDL_GetKeyFromName(const char *);
uint32_t __wrap_SDL_GetKeyFromName(const char *name) {
  const char *sdl_name = !strcmp(name, "lctrl")    ? "Left Ctrl"
                         : !strcmp(name, "lshift") ? "Left Shift"
                         : !strcmp(name, "esc")    ? "Escape"
                         : !strcmp(name, "enter")  ? "Return"
                         : !strcmp(name, "kp_5")   ? "Keypad 5"
                                                   : name;
  return __real_SDL_GetKeyFromName(sdl_name);
}
#endif

/* Stable address anchor for DWARF-bound read-only views. */
__attribute__((noinline)) void portable_test_observer_anchor(void) {}
extern void portable_test_step_boundary(unsigned,unsigned);
extern void portable_test_diagnostics(FILE *);
extern void __real_DoAntSim(void);

typedef struct Slice {
  int64_t delta;
  unsigned bytes;
} Slice;
typedef struct View {
  unsigned verdict, bytes, sentinel, count, event_records, identity_slots;
  Slice *slices;
  uint8_t *data;
} View;
static View *views;
static unsigned count, step, limit, active;
static FILE *actual, *result;
static FILE *context_actual;
static FILE *identity_actual,*identity_raw;
static FILE *machine_actual;
extern uint64_t host_time_ns(void) __attribute__((weak));
static char dump_path[2048];
static unsigned ideal_mode, dump_entry;
static uint32_t *raw_hashes,*context_hashes,*identity_hashes;


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
    portable_test_screen(f,(const void *)((uintptr_t)portable_test_observer_anchor+palette_delta));
    if (fclose(f)) abort();
    ++next;
    return 1;
  }
  return 0;
}

static void load(void) {
  static unsigned loaded;
  const char *path;
  char line[2048];
  char actual_path[2048];
  FILE *config;
  if (loaded++)
    return;
  path = getenv("SIMANT_TEST_STEP_CONFIG");
  if (!path)
    return;
  ideal_mode = getenv("SIMANT_TEST_IDEAL") != NULL;
  if(!ideal_mode) abort();
  config = fopen(path, "r");
  if (!config)
    abort();
  FILE **files[] = {NULL, &actual, &result};
  for (unsigned i = 0; i < 3; ++i) {
    if (!fgets(line, sizeof(line), config))
      abort();
    line[strcspn(line, "\r\n")] = 0;
    if (!i) continue; /* Compatibility placeholder; never open expected state. */
    if (i==1) snprintf(actual_path,sizeof(actual_path),"%s",line);
    *files[i] = fopen(line, i ? "wb" : "rb");
    if (!*files[i])
      abort();
  }
  if (!fgets(dump_path, sizeof(dump_path), config))
    abort();
  dump_path[strcspn(dump_path, "\r\n")] = 0;
  if (fscanf(config, "%u %u", &count, &limit) != 2 || !count || !limit)
    abort();
  raw_hashes=calloc(count,sizeof(*raw_hashes));
  context_hashes=calloc(count,sizeof(*context_hashes));
  identity_hashes=calloc(count,sizeof(*identity_hashes));
  if(!raw_hashes || !context_hashes || !identity_hashes) abort();
  const char *requested_dump=getenv("SIMANT_TEST_DUMP_ENTRY");
  if(requested_dump) {
    char *end;unsigned long n=strtoul(requested_dump,&end,10);
    if(!n || n>limit || *end) abort();dump_entry=(unsigned)n;
  }
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
  unsigned context_count;char rule[64];
  while(fscanf(config," %63s %u",rule,&context_count)==2) {
    if(!getenv("SIMANT_TEST_IDEAL") || !context_count || context_count>count) abort();
    for(unsigned n=0;n<context_count;++n) {
      unsigned index,records;
      if(fscanf(config,"%u %u",&index,&records)!=2 || index>=count || !records) abort();
      if(!strcmp(rule,"KEYBOARD_CONTEXT")) {
        if(views[index].bytes!=16*records) abort();views[index].event_records=records;
      } else if(!strcmp(rule,"IDENTITY_PATTERN")) {
        if(records>17 || views[index].bytes!=2*records) abort();views[index].identity_slots=records;
      } else abort();
    }
    char path[2200];
    if(!strcmp(rule,"KEYBOARD_CONTEXT")) {
      snprintf(path,sizeof(path),"%s.keyboard-context-v1",actual_path);
      context_actual=fopen(path,"wb");if(!context_actual) abort();
    } else {
      snprintf(path,sizeof(path),"%s.ideal-state-v2",actual_path);identity_actual=fopen(path,"wb");
      snprintf(path,sizeof(path),"%s.anim-ids",actual_path);identity_raw=fopen(path,"w");
      if(!identity_actual || !identity_raw) abort();
    }
  }
  /* Both bounded rules belong to ideal-v1, independently of sound mode. */
  if(ideal_mode && (!context_actual || !identity_actual || !identity_raw)) abort();
  fclose(config);
  if(ideal_mode) {
    if(host_time_ns) {
      char path[2200];snprintf(path,sizeof(path),"%s.machine",actual_path);
      machine_actual=fopen(path,"wb");if(!machine_actual) abort();
    }
    if(setvbuf(actual,NULL,_IOFBF,262144)) abort();
    if(context_actual && setvbuf(context_actual,NULL,_IOFBF,262144)) abort();
    if(identity_actual && setvbuf(identity_actual,NULL,_IOFBF,262144)) abort();
    if(identity_raw && setvbuf(identity_raw,NULL,_IOFBF,65536)) abort();
  }
  active = 1;
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
  hash_bytes+=length;
  uint32_t hash = 2166136261u;
  for (unsigned i = 0; i < length; ++i)
    hash = (hash ^ v->data[i]) * 16777619u;
  return hash;
}

static uint32_t context_fingerprint(View *v) {
  if(!v->event_records) return fingerprint(v);
  hash_bytes+=v->bytes;
  uint32_t hash=2166136261u;
  for(unsigned at=0;at<v->bytes;++at)
    if(simant_event_context_includes(v->data,v->event_records,at)) hash=(hash^v->data[at])*16777619u;
  return hash;
}

static void dump_state_to(const char *path) {
  FILE *dump = fopen(path, "wb");
  if (!dump) abort();
  for (unsigned i = 0; i < count; ++i)
    if (fwrite(views[i].data, 1, views[i].bytes, dump) != views[i].bytes) abort();
  if (fclose(dump)) abort();
}

static void finish(void) {
  uint64_t t=stamp();
  if(fflush(actual) || (context_actual && fflush(context_actual)) ||
     (identity_actual && fflush(identity_actual)) || (identity_raw && fflush(identity_raw))) abort();
  serialize_ticks+=stamp()-t;
  fprintf(result, "{\"entries_observed\":%u,\"frame_entry_reached\":%u,", step, step);
  profile_result(result);
  portable_test_diagnostics(result);
  fputs("}\n", result);
  fclose(result);
  fclose(actual);
  if(context_actual) fclose(context_actual);
  if(identity_actual) fclose(identity_actual);
  if(identity_raw) fclose(identity_raw);
  if(machine_actual && fclose(machine_actual)) abort();
  fflush(NULL);
  _Exit(0);
}

extern void portable_test_audio_content_checkpoint(void) __attribute__((weak));
void __wrap_DoAntSim(void) {
  load();
  if (!active) {
    __real_DoAntSim();
    return;
  }
  ++step;
  if(machine_actual) {
    uint64_t ns=host_time_ns();
    if(fwrite(&ns,sizeof(ns),1,machine_actual)!=1) abort();
  }
  portable_test_step_boundary(step, 1);
  if(portable_test_audio_content_checkpoint) portable_test_audio_content_checkpoint();
  uint64_t t=stamp();
  capture_screen();
  frame_ticks+=stamp()-t;
  {
    t=stamp();
    for(unsigned i=0;i<count;++i) {
      View *v=&views[i];unsigned offset=0;
      for(unsigned j=0;j<v->count;++j) {
        uintptr_t at=(uintptr_t)portable_test_observer_anchor+v->slices[j].delta;
        memcpy(v->data+offset,(const void *)at,v->slices[j].bytes);
        offset+=v->slices[j].bytes;
      }
      observed_bytes+=v->bytes;
      raw_hashes[i]=fingerprint(v);
      /* Reuse a hash only for the identical bytes and unchanged rule. Every
       * semantic view is still gathered and hashed at every entry. */
      context_hashes[i]=v->event_records ? context_fingerprint(v) : raw_hashes[i];
      if(v->identity_slots) {
        hash_bytes+=v->bytes;
        identity_hashes[i]=simant_anim_identity_hash(v->data,v->identity_slots);
      } else identity_hashes[i]=context_hashes[i];
    }
    collect_ticks+=stamp()-t;t=stamp();
    if(fwrite(raw_hashes,sizeof(*raw_hashes),count,actual)!=count) abort();
    ++write_calls;
    if(context_actual) {
      if(fwrite(context_hashes,sizeof(*context_hashes),count,context_actual)!=count) abort();
      ++write_calls;
    }
    if(identity_actual) {
      if(fwrite(identity_hashes,sizeof(*identity_hashes),count,identity_actual)!=count) abort();
      ++write_calls;
    }
    if(identity_raw) for(unsigned i=0;i<count;++i) {
      View *v=&views[i];if(!v->identity_slots) continue;
      fprintf(identity_raw,"%u %u",step,i);
      for(unsigned j=0;j<v->identity_slots;++j) fprintf(identity_raw," %04X",simant_anim_word(v->data,j));
      fputc('\n',identity_raw);
    }
    serialize_ticks+=stamp()-t;
  }
  t=stamp();
  /* Startup selection and requested raw byte diagnostic only. */
  if(step==1 || step==dump_entry) {
    char path[2200];snprintf(path,sizeof(path),"%s.%u",dump_path,step);
    dump_state_to(path);
  }
  dump_ticks+=stamp()-t;
  if (step == limit) finish();
  __real_DoAntSim();
  portable_test_step_boundary(step, 0);
}

#ifdef SIMANT_TEST_AUDIO_CONTENT
#include "native_audio_content.inc"
#endif

/* Complete admitted-read trace. Addresses are resolved from this executable,
 * never fed back into the run. No tracing file is opened unless requested. */
void portable_test_charged_read(const char *service, void *caller, uint64_t ns, uint32_t bios, uint32_t game) {
  static FILE *trace;
  static unsigned initialized;
  static uint64_t reads;
  if (!initialized++) {
    const char *path=getenv("SIMANT_TEST_READ_TRACE");
    if (path && !(trace=fopen(path,"w"))) abort();
    if (trace) fprintf(trace,"IMAGE %p\n",GetModuleHandleA(NULL));
  }
  if (!trace) return;
  void *stack[12];
  unsigned n=CaptureStackBackTrace(0,12,stack,NULL);
  fprintf(trace,"%c %" PRIu64 " %" PRIu64 " %p %s",service?'R':'Z',service?++reads:reads,ns,caller,service?service:"internal");
  fprintf(trace," %u %u",bios,game);
  for (unsigned i=0;i<n;++i) fprintf(trace," %p",stack[i]);
  fputc('\n',trace);
}
