/* Native-text transcriptions of shipped HCEGANT kind-2 menu bitmaps.
 * DOS and Win16 use bitmap labels plus type-1 hit objects, not text objects.
 * Provenance and reproducible image hashes: evidence/enhanced-mode/menus.md.
 * These are presentation labels, never an independent command mapping. */
static const struct {int picture;const char *items[8];} proximity_labels[]={
    {4500,{"Recruit 5","Recruit 10","Release 1/2","Release All","Exchange","Help"}},
    {4502,{"Dig Hole","Start Brood","Help"}},
    {4504,{"Chase","Hunt","Exchange","Help"}},
    {6000,{"OFF","ALARM","B-Nest","B-Trail","R-Nest","R-Trail"}},
    {5000,{"ANT INFO","BARRIERS","DIG/FILL","ADD ANTS","ADD FOOD","DROP TRAILS","INSECTICIDE","START GAME"}},
    {5010,{"EXPERIMENTAL"}},
    {5011,{"Experimental Mode is not available in the full game."}},
    {5001,{"WALLS","ROCKS"}}, {5002,{"DIG","FILL"}},
    {5003,{"BLACK","RED"}}, {5004,{"1 PIECE","20 PIECES"}},
    {5005,{"BLACK NEST","BLACK TRAIL","RED NEST","RED TRAIL","ALARM"}},
    {5006,{"SPRAY","STREAM"}}
};
static const char *proximity_label(int picture,unsigned index){
    for(unsigned i=0;i<sizeof(proximity_labels)/sizeof(proximity_labels[0]);++i)
        if(proximity_labels[i].picture==picture && index<8)return proximity_labels[i].items[index];
    return NULL;
}
