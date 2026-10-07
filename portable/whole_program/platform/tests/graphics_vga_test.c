#include "../graphics_vga.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char g_3D20[128]; /* source RAM scratch required by the isolated raster DLL */
static SimVga vga;
static uint8_t pixels[640*480];
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"VGA check line %d: %s\n",__LINE__,#x); exit(2); } } while (0)

int main(void)
{
    unsigned p, i;
    sim_vga_reset(&vga);
    /* Map masks and mode-0 CPU writes; unselected planes survive. */
    sim_vga_out(&vga,0x3c4,2); sim_vga_out(&vga,0x3c5,5);
    sim_vga_write(&vga,0xffff,0xa5);
    CHECK(vga.planes[0][65535] == 0xa5 && vga.planes[2][65535] == 0xa5);
    CHECK(vga.planes[1][65535] == 0 && vga.planes[3][65535] == 0);
    /* Reads latch all four planes regardless of read-map. Mode 1 ignores CPU
     * data, ALU and bit mask; changing latches between copies matters. */
    for (p=0;p<4;++p) vga.planes[p][123]=(uint8_t)(0x31u+p*0x23u);
    sim_vga_out(&vga,0x3ce,4); sim_vga_out(&vga,0x3cf,2);
    CHECK(sim_vga_read(&vga,123)==vga.planes[2][123]);
    sim_vga_out(&vga,0x3c4,2); sim_vga_out(&vga,0x3c5,15);
    sim_vga_out(&vga,0x3ce,8); sim_vga_out(&vga,0x3cf,0);
    sim_vga_out(&vga,0x3ce,5); sim_vga_out(&vga,0x3cf,1);
    sim_vga_write(&vga,64000,0xff);
    for(p=0;p<4;++p) CHECK(vga.planes[p][64000]==vga.planes[p][123]);
    /* Mode 0 set/reset, logical XOR, bit-mask merge with the READ latch. */
    sim_vga_out(&vga,0x3ce,5); sim_vga_out(&vga,0x3cf,0);
    sim_vga_out(&vga,0x3ce,0); sim_vga_out(&vga,0x3cf,5);
    sim_vga_out(&vga,0x3ce,1); sim_vga_out(&vga,0x3cf,15);
    sim_vga_out(&vga,0x3ce,3); sim_vga_out(&vga,0x3cf,24);
    sim_vga_out(&vga,0x3ce,8); sim_vga_out(&vga,0x3cf,0xf0);
    sim_vga_write(&vga,123,0);
    CHECK(vga.planes[0][123]==(uint8_t)(0x31^0xf0));
    CHECK(vga.planes[1][123]==0x54);
    /* Negative x, right-edge spill, off-screen rows and 16-bit address wrap. */
    CHECK(sim_vga_pixel_offset(-1,0,80)==65535);
    CHECK(sim_vga_pixel_offset(640,0,80)==80);
    CHECK(sim_vga_pixel_offset(0,480,80)==38400);
    CHECK(sim_vga_pixel_offset(0,818,80)==65440);
    CHECK(sim_vga_pixel_offset(0,820,80)==64);
    sim_vga_reset(&vga);
    sim_vga_store_color(&vga,sim_vga_pixel_offset(639,479,80),639,9);
    sim_vga_store_color(&vga,sim_vga_pixel_offset(640,0,80),640,6);
    sim_vga_store_color(&vga,sim_vga_pixel_offset(0,480,80),0,15);
    sim_vga_present(&vga,pixels,640,480);
    CHECK(pixels[640*480-1]==9);
    CHECK(pixels[640]==6);
    for(i=0;i<640;++i) CHECK(pixels[i]==0);
    CHECK(sim_vga_color(&vga,38400,0)==15); /* retained but not presented */
    puts("PASS: VGA planes, masks, read latches, mode-1 copy, ALU, aperture wrap and visible presentation");
    return 0;
}
