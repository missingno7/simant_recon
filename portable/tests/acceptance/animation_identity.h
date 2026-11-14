#ifndef SIMANT_ACCEPTANCE_ANIMATION_IDENTITY_H
#define SIMANT_ACCEPTANCE_ANIMATION_IDENTITY_H
/* Observer-only anim-id-pattern-v1. See runtime_views.json and
 * evidence/canonical/native-ideal-clock/animation-identity.md.
 * Preserve -1 and equality classes; assign ordinals by first appearance.
 * Invalid high-bit words are retained literally, never renamed as valid IDs. */
#include <stdint.h>
static inline uint16_t simant_anim_word(const uint8_t *data, unsigned at) {
    return (uint16_t)((unsigned)data[2*at] | ((unsigned)data[2*at+1]<<8));
}
static inline uint16_t simant_anim_identity_word(const uint8_t *data, unsigned at) {
    uint16_t value=simant_anim_word(data,at),seen[17];
    unsigned count=0;
    if(value>=0x8000) return value;
    for(unsigned i=0;i<=at;++i) {
        uint16_t word=simant_anim_word(data,i);
        if(word>=0x8000) continue;
        unsigned j=0;while(j<count && seen[j]!=word) ++j;
        if(j==count) seen[count++]=word;
        if(word==value) return (uint16_t)j;
    }
    return value; /* unreachable for a bound slot */
}
static inline uint32_t simant_anim_identity_hash(const uint8_t *data, unsigned slots) {
    uint32_t hash=2166136261u;
    for(unsigned i=0;i<slots;++i) {
        uint16_t word=simant_anim_identity_word(data,i);
        hash=(hash^(word&255))*16777619u;
        hash=(hash^(word>>8))*16777619u;
    }
    return hash;
}
#endif
