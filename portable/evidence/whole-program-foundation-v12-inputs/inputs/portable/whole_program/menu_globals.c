#include "menu_globals.h"

PortableMenuSourceRecordView g_menu_view;
char ***fd_55B3_6054;

void sim_menu_globals_release(void)
{
    portable_menu_source_record_view_release(&g_menu_view);
    fd_55B3_6054 = NULL;
}
