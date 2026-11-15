/* Read-only device command coordinates; no schedule or device-answer input. */
static FILE *test_audio_commands;
static unsigned test_step,test_phase;
extern void portable_test_audio_content_opl(uint16_t,uint8_t) __attribute__((weak));
extern void portable_test_audio_content_close(void) __attribute__((weak));
void portable_test_audio_content_head(FILE *f,char tag,uint64_t tick) {
  fprintf(f,"%c %" PRIu64 " %" PRIu64 " %u %u",tag,tick,(uint64_t)(2*test_step-test_phase),test_step,test_phase);
}
static void test_audio_close(void) {
  if(portable_test_audio_content_close) portable_test_audio_content_close();
  if(test_audio_commands) {
    fprintf(test_audio_commands,"E %u %u %u\n",2*test_step-test_phase,test_step,test_phase);
    fclose(test_audio_commands);test_audio_commands=NULL;
  }
}
static void test_audio_load(void) {
  static int loaded;
  if(loaded++) return;
  const char *path=getenv("SIMANT_TEST_AUDIO_COMMANDS");
  if(path) {
    test_audio_commands=fopen(path,"w");if(!test_audio_commands) abort();
    fputs("SIMANT_AUDIO_COMMANDS 1\n",test_audio_commands);
    atexit(test_audio_close);
  }
}
void portable_test_audio_write(uint16_t port,uint8_t value) {
  test_audio_load();
  if(portable_test_audio_content_opl) portable_test_audio_content_opl(port,value);
  if (test_audio_commands && ((port>=0x388 && port<=0x38b) ||
      (port>=0x220 && port<=0x22f) || port<=0xf || (port>=0x80 && port<=0x8f)))
    fprintf(test_audio_commands,"W %" PRIu64 " %u %u %X %X\n",(uint64_t)(2*test_step-test_phase),test_step,test_phase,port,value);
}
