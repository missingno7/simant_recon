/* Acceptance-only sound schedule. Coordinates are observed DOS service counts,
 * never derived from expected playback state. Ordinary play has no tape. */
extern void portable_whole_audio_replay_interrupt(unsigned) __attribute__((weak));
static FILE *test_audio_timer, *test_audio_commands;
static uint64_t test_audio_at, test_audio_ticks, test_audio_runs;
static unsigned test_audio_fast;
static int test_audio_ready, test_audio_busy;
static void test_audio_next(void) {
  char tag;
  int fields=fscanf(test_audio_timer," %c",&tag);
  if (fields!=1) abort();
  if (tag=='E') { test_audio_ready=0;return; }
  if (tag!='T' || fscanf(test_audio_timer,"%" SCNu64 " %u",&test_audio_at,&test_audio_fast)!=2 || test_audio_fast>2) abort();
  test_audio_ready=1;
}
static void test_audio_close(void) {
  if (test_audio_commands) {
    fprintf(test_audio_commands,"E %" PRIu64 " %u %u\n",test_services,test_step,test_phase);
    fclose(test_audio_commands);test_audio_commands=NULL;
  }
}
static void test_audio_load(void) {
  const char *path=getenv("SIMANT_TEST_AUDIO_TIMER");
  if (path) {
    test_audio_timer=fopen(path,"r");if (!test_audio_timer) abort();
    test_audio_next();
  }
  path=getenv("SIMANT_TEST_AUDIO_COMMANDS");
  if (path) {
    test_audio_commands=fopen(path,"w");if (!test_audio_commands) abort();
    fputs("SIMANT_AUDIO_COMMANDS 1\n",test_audio_commands);
    atexit(test_audio_close);
  }
}
static void test_audio_drain(void) {
  if (test_audio_busy) return;
  test_audio_busy=1;
  while (test_audio_ready && test_audio_at<=test_services) {
    if (test_audio_at!=test_services) { fprintf(stderr,"Missed audio timer boundary\n");abort(); }
    unsigned fast=test_audio_fast;
    test_audio_next();
    if (!getenv("SIMANT_TEST_DISABLE_AUDIO_TIMER")) {
      if (!portable_whole_audio_replay_interrupt) abort();
      portable_whole_audio_replay_interrupt(fast);
      ++test_audio_runs;
    }
    ++test_audio_ticks;
  }
  test_audio_busy=0;
}
void portable_test_audio_write(uint16_t port,uint8_t value) {
  if (test_audio_commands && ((port>=0x388 && port<=0x38b) ||
      (port>=0x220 && port<=0x22f) || port<=0xf || (port>=0x80 && port<=0x8f)))
    fprintf(test_audio_commands,"W %" PRIu64 " %u %u %X %X\n",test_services,test_step,test_phase,port,value);
}
