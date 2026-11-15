#include "portable/whole_program/enhanced/workspace.h"
#include <assert.h>
#include <string.h>
#include <stdlib.h>
int main(int argc,char **argv) {
    if(argc!=2){fputs("Usage: workspace-model ROUNDTRIP_FILE\n",stderr);return 2;}
    const char *temp_path=argv[1];
    Workspace w,copy,bad;unsigned checks=0;
    for(int preset=0;preset<4;++preset){ws_preset(&w,preset);assert(ws_validate(&w));++checks;}
    ws_preset(&w,0);
    assert(ws_reveal(&w,1));assert(ws_move(&w,1,0,WS_RIGHT,0));
    assert(ws_reveal(&w,2));assert(ws_move(&w,2,1,WS_BOTTOM,0));
    assert(ws_move(&w,2,1,WS_STACK,0));assert(ws_group(&w,1)==ws_group(&w,2));
    assert(ws_float(&w,1,90000,-90000,480,320));assert(ws_group(&w,1)!=ws_group(&w,2));
    assert(ws_collapse(&w,ws_group(&w,2)));assert(ws_reveal(&w,2));
    assert(!w.nodes[ws_group(&w,2)].collapsed);assert(ws_hide(&w,1));assert(ws_reveal(&w,1));
    for(int p=0;p<WS_PANELS;++p)assert(ws_reveal(&w,p));assert(ws_validate(&w));
    assert(!ws_hide(&w,22));
    FILE *f=fopen(temp_path,"w+");assert(f&&ws_write(&w,f));rewind(f);assert(ws_read(&copy,f));fclose(f);
    copy.revision=w.revision;assert(!memcmp(&w,&copy,sizeof(w)));++checks;
    bad=w;bad.nodes[bad.root].a=bad.root;assert(!ws_validate(&bad));
    bad=w;bad.nodes[bad.root].ratio=0;assert(!ws_validate(&bad));
    bad=w;bad.panels[1].plane=4;assert(!ws_validate(&bad));
    bad=w;int g=ws_group(&bad,0);bad.nodes[g].panels[0]=WS_PANELS;assert(!ws_validate(&bad));
    const char *invalid[]={"SIMANT-WORKSPACE 2\n","garbage","SIMANT-WORKSPACE 1\n999\n"};
    for(int i=0;i<3;++i){f=fopen(temp_path,"w+");assert(f);fputs(invalid[i],f);rewind(f);bad=w;assert(!ws_read(&bad,f));assert(!memcmp(&bad,&w,sizeof(w)));fclose(f);++checks;}
    unsigned random=187;
    for(int i=0;i<12000;++i){random=random*1664525u+1013904223u;int p=random%WS_PANELS;random=random*1664525u+1013904223u;int target=random%WS_PANELS;
        switch(i%7){case 0:ws_reveal(&w,p);break;case 1:ws_move(&w,p,target,random%5,0);break;case 2:ws_float(&w,p,40,50,480,320);break;case 3:ws_hide(&w,p);break;case 4:ws_collapse(&w,ws_group(&w,p));break;case 5:ws_move(&w,p,target,random%4,1);break;case 6:if(i%91==6)ws_preset(&w,(i/91)%4);break;}
        assert(ws_validate(&w));++checks;
    }
    for(int i=0;i<100;++i){ws_exercise(&w,i);assert(ws_validate(&w));++checks;}
    printf("{\"passed\":true,\"checks\":%u,\"operations\":\"dock/split/tab/float/collapse/hide/reveal/preset/reset/persistence/rejection\"}\n",checks);return 0;
}
