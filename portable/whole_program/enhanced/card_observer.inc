/* Appended to the converted Info TU: read private source hit tables only.
 * Coordinates remain original. Never recreates DisplayCard or modifies it. */
#include "portable/whole_program/enhanced/snapshot.h"
void enhanced_read_card_links(EnhancedCardsSnapshot *out)
{
    unsigned n=0;
    struct Rect content;
    const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[5];
    if(!entry->bound || entry->view.count<3)return;
    memcpy(&content,entry->view.object_table[2],8);
    for(int i=0;i<g_8C22 && i<64;++i){
        memcpy(&out->links[n].rect,&fd_4EE5_0280[i].r,8);
        out->links[n].rect.left+=content.left;out->links[n].rect.right+=content.left;
        out->links[n].rect.top+=content.top;out->links[n].rect.bottom+=content.top;
        out->links[n++].target=fd_4EE5_0280[i].id;
    }
    for(int i=0;i<g_8C24 && i<64;++i){
        memcpy(&out->links[n].rect,&fd_4EE5_0000[i].r,8);
        out->links[n].target=-fd_4EE5_0000[i].id;
        for(unsigned j=0;j<sizeof(fd_4EE5_0500)/sizeof(fd_4EE5_0500[0]);++j)if(fd_4EE5_0500[j].id==fd_4EE5_0000[i].id){
            memcpy(out->links[n].label,fd_4EE5_0500[j].name,32);out->links[n].label[32]=0;break;
        }
        ++n;
    }
    out->link_count=n;out->links_available=1;
}
