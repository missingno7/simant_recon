/* Test-only conservative restart detector. Every SaveRec byte, plus source
 * command/settings state. No invariance rule, exclusion or mask is added. */
#pragma pack(push,2)
struct SweepSaveRec {int16_t size,count;void *data;};
#pragma pack(pop)
extern struct SweepSaveRec save_record_table[];
static uint64_t source_fingerprint(void){
    uint64_t hash=UINT64_C(14695981039346656037);
    for(int n=0;n<308&&save_record_table[n].count;++n){
        const uint8_t *p=save_record_table[n].data;
        for(size_t i=0;i<(size_t)save_record_table[n].size*save_record_table[n].count;++i)hash=(hash^p[i])*UINT64_C(1099511628211);
    }
    const EnhancedSnapshot *s=enhanced_snapshot();
    /* Source display/control state can affect the next transaction even when
     * SaveRec is unchanged (notably frozen Map, Info history and graph slots).
     * Snapshot publication counters are not included. This restart detector
     * does not change any acceptance comparison or invariance exclusion. */
    const void *blocks[]={&s->panels,&s->overview,&s->cards,&s->history};
    const size_t sizes[]={sizeof(s->panels),sizeof(s->overview),sizeof(s->cards),sizeof(s->history)};
    for(unsigned b=0;b<4;++b)for(size_t i=0;i<sizes[b];++i)hash=(hash^((const uint8_t *)blocks[b])[i])*UINT64_C(1099511628211);
    extern char ExpSubStates[];for(unsigned i=0;i<8;++i)hash=(hash^(uint8_t)ExpSubStates[i])*UINT64_C(1099511628211);
    extern uint32_t dos_crt_rng_state(void);uint32_t rng=dos_crt_rng_state();
    for(unsigned i=0;i<4;++i)hash=(hash^((rng>>(8*i))&255))*UINT64_C(1099511628211);
    return hash;
}
