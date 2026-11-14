/* Option-gated scenario services. Kept together to make their production
 * boundary reviewable. No files/options means ordinary host services and no
 * input injection. */
#define SIMANT_TEST_OBSERVER_IMPLEMENTATION
#include "../input_time.h"

static FILE *test_clock_file, *test_input_file, *test_order_output;
static unsigned char *test_service_data;
static size_t test_service_at, test_service_size;
static int test_loaded, test_clock_done;
static int test_disable_clock, test_step_mode, test_control_changed;
static uint64_t test_pumps;
static unsigned test_inputs, test_queued;
static uint64_t test_input_service;
static unsigned test_input_step, test_input_phase;
static unsigned test_step, test_phase;
static char test_input_op[24], test_input_arg[40];
static int test_input_a, test_input_b, test_input_ready;
static unsigned test_input_cx, test_input_dx;
static uint16_t test_raw_cx[128], test_raw_dx[128], test_irq_cx, test_irq_dx;
static Host *test_host;
/* Ordinal inputs join the normal host event boundary before SDL's end-of-poll
 * sentinel. SDL_PushEvent may defer an event to a later polling batch. */
static SDL_Event test_raw[128];
static unsigned test_raw_ids[128], test_raw_sequence;
static unsigned test_raw_head, test_raw_count;
static int test_injecting, test_admitting;
static uint64_t test_services, test_queries;
extern int portable_input_time_host_interrupt(void) __attribute__((weak));
static int test_queue_raw(const SDL_Event *event) {
  if (test_raw_count == 128)
    abort();
  test_raw[(test_raw_head + test_raw_count) % 128] = *event;
  test_raw_ids[(test_raw_head + test_raw_count) % 128] = test_queued + 1;
  test_raw_cx[(test_raw_head + test_raw_count) % 128] = (uint16_t)test_input_cx;
  test_raw_dx[(test_raw_head + test_raw_count) % 128] = (uint16_t)test_input_dx;
  ++test_raw_count;
  return 1;
}
static int test_take_raw(SDL_Event *event) {
  test_raw_sequence = 0;
  if (!test_raw_count)
    return 0;
  *event = test_raw[test_raw_head];
  test_raw_sequence = test_raw_ids[test_raw_head];
  test_irq_cx = test_raw_cx[test_raw_head];
  test_irq_dx = test_raw_dx[test_raw_head];
  test_raw_head = (test_raw_head + 1) % 128;
  --test_raw_count;
  return 1;
}
typedef struct TestRun {
  uint32_t value;
  uint64_t count;
  struct TestRun *next;
} TestRun;
typedef struct TestStream {
  char kind, original_kind;
  int64_t pc;
  uint32_t original_pc;
  TestRun *head, *tail;
  uint64_t completed;
} TestStream;
static TestStream test_streams[256];
static unsigned test_stream_count;
static uint64_t test_reads, test_hash = UINT64_C(1469598103934665603),
                            test_remaining;
static uint64_t test_control_read;

static void test_finish(void) {
  if (test_step_mode)
    return;
  if ((test_clock_file && (!test_clock_done || test_remaining)) ||
      test_input_ready || test_raw_count || test_inputs != test_queued ||
      (test_service_data && test_service_at!=test_service_size)) {
    fprintf(stderr,
            "Observer tape incomplete: clock=%" PRIu64 " input=%d pump=%" PRIu64
            "\n",
            test_remaining, test_input_ready, test_pumps);
    abort();
  }
}
static int test_line(FILE *file, char *line, size_t size) {
  while (fgets(line, (int)size, file))
    if (line[0] != '#' && line[0] != '\n')
      return 1;
  if (ferror(file))
    abort();
  return 0;
}
static void test_next_input(void) {
  char line[240], extra;
  int fields;
  test_input_ready = 0;
  if (!test_input_file || !test_line(test_input_file, line, sizeof(line)))
    return;
  test_input_cx = test_input_dx = 0;
  fields = sscanf(line, "%" SCNu64 " %u %u %23s %39s %d %d %u %u %c",
             &test_input_service, &test_input_step, &test_input_phase,
             test_input_op, test_input_arg, &test_input_a, &test_input_b,
             &test_input_cx, &test_input_dx, &extra);
  if ((fields != 7 && fields != 9) || test_input_cx > UINT16_MAX ||
      test_input_dx > UINT16_MAX)
    abort();
  test_input_ready = 1;
}
static void test_load(void) {
  const char *clock_path, *input_path;
  if (test_loaded)
    return;
  test_loaded = 1;
  test_disable_clock = getenv("SIMANT_TEST_DISABLE_CLOCK") != NULL;
  test_step_mode = getenv("SIMANT_TEST_STEP_CONFIG") != NULL;
  clock_path = getenv("SIMANT_TEST_FULL_CLOCK");
  input_path = getenv("SIMANT_TEST_SERVICE_INPUT");
  if (getenv("SIMANT_TEST_CLOCK_CONTROL_READ")) {
    char *end;
    test_control_read =
        strtoull(getenv("SIMANT_TEST_CLOCK_CONTROL_READ"), &end, 10);
    if (*end || !test_control_read)
      abort();
  }
  if (clock_path && !(test_clock_file = fopen(clock_path, "r")))
    abort();
  if (test_clock_file) {
    char line[200], kind, original_kind, extra;
    int64_t pc;
    uint32_t original_pc, value;
    uint64_t count;
    while (test_line(test_clock_file, line, sizeof(line))) {
      unsigned i;
      TestRun *run;
      if (!strcmp(line, "X\n")) {
        test_clock_done = 1;
        break;
      }
      if (sscanf(line,
                 "%c %" SCNd64 " %c %" SCNu32 " %" SCNu32 " %" SCNu64 " %c",
                 &kind, &pc, &original_kind, &original_pc, &value, &count,
                 &extra) != 6 ||
          !count)
        abort();
      for (i = 0; i < test_stream_count &&
                  (test_streams[i].kind != kind || test_streams[i].pc != pc);
           ++i) {
      }
      if (i == test_stream_count) {
        if (i == 256)
          abort();
        test_streams[i].kind = kind;
        test_streams[i].pc = pc;
        test_streams[i].original_kind = original_kind;
        test_streams[i].original_pc = original_pc;
        ++test_stream_count;
      }
      if (test_streams[i].original_kind != original_kind ||
          test_streams[i].original_pc != original_pc)
        abort();
      run = (TestRun *)malloc(sizeof(*run));
      if (!run)
        abort();
      run->value = value;
      run->count = count;
      run->next = NULL;
      if (test_streams[i].tail)
        test_streams[i].tail->next = run;
      else
        test_streams[i].head = run;
      test_streams[i].tail = run;
      test_remaining += count;
    }
    if (!test_clock_done || !test_remaining)
      abort();
  }
  if (input_path && !(test_input_file = fopen(input_path, "r")))
    abort();
  if ((clock_path || input_path) && atexit(test_finish))
    abort();
  if (getenv("SIMANT_TEST_ORDER_OUTPUT")) test_order_output=fopen(getenv("SIMANT_TEST_ORDER_OUTPUT"), "wb");
  if (getenv("SIMANT_TEST_SERVICE_ORDER")) {
    FILE *order=fopen(getenv("SIMANT_TEST_SERVICE_ORDER"), "rb");
    int64_t length;
    if (!order || _fseeki64(order,0,SEEK_END) || (length=_ftelli64(order))<=0 ||
        (uint64_t)length>SIZE_MAX || _fseeki64(order,0,SEEK_SET)) abort();
    test_service_size=(size_t)length;
    test_service_data=malloc(test_service_size);
    if (!test_service_data || fread(test_service_data,1,test_service_size,order)!=test_service_size ||
        fgetc(order)!=EOF || ferror(order)) abort();
    fclose(order);
  }
  test_next_input();
}
static void test_service(unsigned index) {
  ++test_services;
  if (test_service_data && !test_control_changed) {
    int expected=test_service_at<test_service_size ? test_service_data[test_service_at++] : -1;
    if (expected!=(int)index) {
      fprintf(stderr,"Observer service order mismatch at %" PRIu64 ": expected=%d actual=%u reads=%" PRIu64 " pumps=%" PRIu64 "\n",
              test_services,expected,index,test_reads,test_pumps);
      if (test_order_output) fflush(test_order_output);
      if (portable_test_replay_error) portable_test_replay_error("Global service order differs");
      abort();
    }
  }
}
uint32_t portable_test_clock_read(char kind, void *pc, uint32_t fallback) {
  unsigned i;
  TestStream *stream;
  TestRun *run;
  uint32_t value;
  int64_t delta =
      pc ? (int64_t)(uintptr_t)pc - (int64_t)(uintptr_t)portable_test_clock_read
         : 0;
  test_load();
  if (!test_clock_file)
    return fallback;
  if (!test_remaining)
    exit(0);
  portable_test_before_poll();

  for (i = 0; i < test_stream_count &&
              (test_streams[i].kind != kind || test_streams[i].pc != delta);
       ++i) {
  }
  if (i == test_stream_count || !test_streams[i].head) {
    fprintf(stderr,
            "Observer extra clock read: %c %" PRId64 " (%" PRIu64
            " total reads left) pump=%" PRIu64 "\n",
            kind, delta, test_remaining, test_pumps);
    if (test_order_output) fflush(test_order_output);
    if (portable_test_replay_error)
      portable_test_replay_error("No recorded value for native clock read");
    abort();
  }
  test_service(i);
  stream = &test_streams[i];
  if (test_order_output) { fprintf(test_order_output,"%c %u\n",stream->original_kind,stream->original_pc); }
  ++stream->completed;
  run = stream->head;
  value = run->value;
  --test_remaining;
  ++test_reads;
  if ((kind == 'h' || kind == 'j') && getenv("SIMANT_TEST_DISABLE_DEVICES") &&
      value != fallback) {
    fprintf(stderr, "Observer device control %c read %" PRIu64 ": tape=%" PRIu32
                    " host=%" PRIu32 "\n", kind, test_reads, value, fallback);
    value = fallback;
    test_control_changed = 1;
  }
  if (test_reads == test_control_read ||
      (test_disable_clock && portable_test_clock_is_stateful &&
       portable_test_clock_is_stateful())) {
    if (!test_disable_clock || test_reads == 1)
      fprintf(stderr,
              "Observer negative control read %" PRIu64 ": tape=%" PRIu32
              " host=%" PRIu32 "\n",
              test_reads, value, fallback);
    value = fallback;
    test_control_changed = 1;
  }
  test_hash =
      (test_hash ^ ((uint64_t)stream->original_pc ^
                    ((uint64_t)(unsigned char)stream->original_kind << 32) ^
                    ((uint64_t)value << 8))) *
      UINT64_C(1099511628211);
  if (!--run->count) {
    stream->head = run->next;
    free(run);
  }
  portable_test_before_poll();
  return value;
}
uint64_t portable_test_pump_ordinal(void) { return test_pumps; }
unsigned portable_test_input_count(void) { return test_inputs; }
__attribute__((noinline)) void
portable_test_input_delivered(unsigned sequence) {
  fprintf(stderr, "Observer phase %u %u %u %" PRIu64 " %" PRIu64 " %" PRIu64 " %" PRIu64 "\n", sequence, test_step, test_phase,test_queries,test_services,test_reads,test_pumps);
  for (unsigned i = 0; i < test_stream_count; ++i)
    fprintf(stderr, "Observer position %u %c %u %" PRIu64 "\n", sequence,
            test_streams[i].original_kind, test_streams[i].original_pc,
            test_streams[i].completed);
}

void portable_test_pump(void) {
  test_load();
  test_service(254);
  ++test_pumps;
  if (test_order_output) fputs("Q 0\n",test_order_output);
  portable_test_before_poll();
}

void portable_test_window_pump(void) {
  test_load();
  portable_test_before_poll();
  test_service(255);
  ++test_pumps;
  if (test_order_output) fputs("W 0\n",test_order_output);
  portable_test_before_poll();
}

void portable_test_input_sample(unsigned kind, unsigned value) {
  (void)value;
  test_load();
  if (!test_clock_file && !test_input_file && !test_service_data) return;
  if (test_order_output) fprintf(test_order_output,"S %u\n",kind);
  test_service(kind);
  ++test_queries;
  /* v6: atomic providers have cached their result; entry-only 246 precedes
   * the body. StillDown (247) is observed at exit with its result cached. */
  portable_test_before_poll();
}
void portable_test_before_poll(void) {
  test_load();
  if (test_admitting) return;
  test_admitting = 1;
  while (test_input_ready && test_input_service <= test_services) {
    if (test_service_data && !test_control_changed &&
        test_input_service != test_services) {
      if (portable_test_replay_error) portable_test_replay_error("Missed input service boundary");
      abort();
    }
    SDL_Event raw = {0};
    if (!strcmp(test_input_op, "keydown") || !strcmp(test_input_op, "keyup")) {
      const char *name = !strcmp(test_input_arg, "enter")  ? "Return"
                         : !strcmp(test_input_arg, "kp_5") ? "Keypad 5"
                                                           : test_input_arg;
      raw.type = !strcmp(test_input_op, "keydown") ? SDL_EVENT_KEY_DOWN
                                                   : SDL_EVENT_KEY_UP;
      raw.key.key = SDL_GetKeyFromName(name);
      raw.key.scancode = SDL_GetScancodeFromKey(raw.key.key, &raw.key.mod);
      raw.key.down = raw.type == SDL_EVENT_KEY_DOWN;
      raw.key.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
      if (!raw.key.key || !test_queue_raw(&raw))
        abort();
    } else {
      HostInputState state;
      HostEvent event = {0};
      if (!test_host || !host_get_input_state(test_host, &state))
        abort();
      event.x = state.x;
      event.y = state.y;
      if (!strcmp(test_input_op, "mouse_move")) {
        int x = state.x + test_input_a / 2, y = state.y + test_input_b / 2;
        event.kind = HOST_EVENT_MOUSE_MOVE;
        event.x = (int16_t)(x < 0 ? 0
                            : x > test_host->logical_width - 4
                                ? test_host->logical_width - 4
                                : x);
        event.y = (int16_t)(y < 0 ? 0
                            : y > test_host->logical_height - 4
                                ? test_host->logical_height - 4
                                : y);
      } else if (!strcmp(test_input_op, "mouse_button")) {
        event.kind = !strcmp(test_input_arg, "down") ? HOST_EVENT_MOUSE_DOWN
                                                     : HOST_EVENT_MOUSE_UP;
        event.button = (uint8_t)(test_input_a == 0   ? SDL_BUTTON_LEFT
                                 : test_input_a == 1 ? SDL_BUTTON_RIGHT
                                                     : SDL_BUTTON_MIDDLE);
      } else
        abort();
      test_injecting = 1;
      if (!host_push_pointer_event(test_host, &event))
        abort();
      test_injecting = 0;
    }
    fprintf(stderr,
            "Observer queued input %u pump=%" PRIu64 " reads=%" PRIu64
            " service=%" PRIu64 " step=%u phase=%u %s %s\n",
            ++test_queued, test_pumps, test_reads, test_input_service,
            test_input_step, test_input_phase, test_input_op,
            test_input_arg);
    test_next_input();
    if (!portable_input_time_host_interrupt || portable_input_time_host_interrupt() < 0) abort();
  }
  test_admitting = 0;
}

/* Step observer glue: no canonical game state is written. */
void portable_test_step_boundary(unsigned step, unsigned phase) {
  test_load();
  portable_test_before_poll();
  test_service(phase ? 250 : 251);
  test_step = step;
  test_phase = phase;
  if (!phase) portable_test_before_poll();
}
int portable_test_reference_end(void) {
  test_load();
  return !test_remaining && !test_input_ready && !test_raw_count &&
         test_inputs==test_queued &&
         (!test_service_data || test_service_at==test_service_size);
}
void portable_test_diagnostics(FILE *f) {
  fprintf(f,
          "\"pump_count\":%" PRIu64 ",\"clock_reads\":%" PRIu64
          ",\"clock_order_digest\":%" PRIu64 ",\"inputs_delivered\":%u,\"service_samples\":%" PRIu64 ",\"input_queries\":%" PRIu64,
          test_pumps, test_reads, test_hash, test_inputs,test_services,test_queries);
}
int portable_test_refresh_mode(void) {
  test_load();
  return test_clock_file != NULL ? 1 : 0;
}

void portable_test_irq_context(uint16_t *cx, uint16_t *dx) {
  /* Only a currently admitted raw tape event has DOS register provenance.
   * No tape means the caller's explicit ordinary SDL values remain intact. */
  if (test_input_file && test_raw_sequence &&
      !getenv("SIMANT_TEST_DISABLE_IRQ_CONTEXT")) {
    *cx = test_irq_cx;
    *dx = test_irq_dx;
  }
}
