/* Read-only acceptance observations. All values come from live source state. */
#include "../../whole_program/platform/audio_state.h"
extern void portable_test_audio_content_head(FILE *, char, uint64_t);
static FILE *content_file;
static uint64_t content_tick;
static unsigned content_opl_index[2],content_dac_argument;
static unsigned content_voice_active[2];
static FILE *content_open(void) {
  if (!content_file) {
    const char *path=getenv("SIMANT_TEST_AUDIO_CONTENT");
    if (!path) return NULL;
    content_file=fopen(path,"w");if (!content_file) abort();
    fputs("SIMANT_AUDIO_CONTENT 1\n",content_file);
  }
  return content_file;
}
static int content_head(char tag) {
  if (!content_open()) return 0;
  portable_test_audio_content_head(content_file,tag,content_tick);return 1;
}
void portable_test_audio_tick(unsigned kind) { content_tick+=kind==0?16:1; }
void portable_test_sample_boundary(unsigned stop,int ch) {
  if (!content_head(stop?'X':'S')) return;
  if (ch<0 || ch>=2) abort();
  content_voice_active[ch]=!stop;
  fprintf(content_file," %d",ch);
  if (!stop) {
    PortableWholeAudioRuntimeSample *c=&snd_sample_channel_records[ch];
    PortableWholeAudioSample *s=c->snd;
    if (!s || !s->data || !*s->data) abort();
    fprintf(content_file," %u %u %u %u %u %u %u ",(uint16_t)s->object,c->step,
        (uint16_t)(c->voltab-snd_volume_table_offset)>>8,c->end,c->start,c->flags&128,s->len);
    for (unsigned i=0;i<s->len;++i) fprintf(content_file,"%02X",((uint8_t *)*s->data)[i]);
  }
  fputc('\n',content_file);
}
void portable_test_audio_mix(unsigned a,unsigned b) {
  for (unsigned ch=0;ch<2;++ch) {
    if (!content_head('P')) return;
    PortableWholeAudioRuntimeSample *c=&snd_sample_channel_records[ch];
    fprintf(content_file," %u %d %u %u\n",ch,c->snd?(uint16_t)c->snd->object:-1,c->pos,ch?b:a);
  }
}
void portable_test_audio_content_opl(uint16_t port,uint8_t value) {
  if (!((port>=0x388 && port<=0x38b) || (port>=0x220 && port<=0x22f) || port<=0xf || (port>=0x80 && port<=0x8f))) return;
  if (port<0x388 || port>0x38b) {
    if(port==0x22c && content_dac_argument) { content_dac_argument=0;return; }
    if(port==0x22c && value==0x10) { content_dac_argument=1;return; }
    char tag=(port==0x226 || (port==0x22c && (value==0xd1 || value==0xd3)))?'K':'U';
    if(content_head(tag)) fprintf(content_file," %u %u\n",port,value);return;
  }
  unsigned bank=(port-0x388)/2;
  if (!(port&1)) content_opl_index[bank]=value;
  else if (content_head('O')) fprintf(content_file," %u %u %u\n",bank,content_opl_index[bank],value);
}
static uint32_t content_hashes[256];
void portable_test_audio_progress(unsigned checkpoint) {
  uint32_t hashes[256];unsigned n=0,changed=0;
  if(!checkpoint) for(unsigned ch=0;ch<2;++ch)
    if(content_voice_active[ch] && !snd_sample_channel_records[ch].snd) portable_test_sample_boundary(1,ch);
  if (!views) load(); /* Observe progress from the first IRQ, before entry 1. */
  if (!views || !content_open()) return;
  for(unsigned i=0;i<count;++i) {
    View *v=&views[i];
    /* Audio IDs come from the config, alongside every ordinary state view. */
    if(v->verdict!=2) continue;
    uint32_t h=2166136261u;
    for(unsigned j=0;j<v->count;++j) {
      const uint8_t *p=(const uint8_t *)((uintptr_t)portable_test_clock_read+v->slices[j].delta);
      for(unsigned k=0;k<v->slices[j].bytes;++k) h=(h^p[k])*16777619u;
    }
    if(n==256) abort();hashes[n]=h;changed|=content_hashes[n]!=h;++n;
  }
  if(!checkpoint && !changed) return;
  if(content_head(checkpoint?'C':'Q')) {
    for(unsigned i=0;i<n;++i) { fprintf(content_file," %08X",hashes[i]);content_hashes[i]=hashes[i]; }
    fputc('\n',content_file);
  }
}
void portable_test_audio_content_checkpoint(void) { portable_test_audio_progress(1); }
void portable_test_audio_content_close(void) {
  if (content_head('E')) { fputc('\n',content_file);fclose(content_file);content_file=NULL; }
}
