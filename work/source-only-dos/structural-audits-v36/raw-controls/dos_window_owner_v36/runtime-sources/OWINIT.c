struct Rect { int left,top,right,bottom; };
extern void far callback(int phase);
void (far * far win_drawHooks[45])(int phase) = {callback};
struct Rect far win_offsets[45];
