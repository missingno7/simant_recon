/* Host typography from the immutable shipped FONT2. No source font state. */
int native_workspace_classic(void){return !u.layout.native_look;}
static HFONT label_font(int dpi,int role){return CreateFontA(-scale(role==1?10:13,dpi),0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,"Tahoma");}
static void plain_label(char *out,size_t size,const char *text,unsigned flags){
    size_t n=0;for(;*text&&n+1<size;++text){if(!(flags&DT_NOPREFIX)&&*text=='&'){if(text[1]=='&')++text;else continue;}if(*text=='\\'&&text[1]=='n'){out[n++]='\n';++text;}else out[n++]=*text;}out[n]=0;
}
int native_workspace_text_width(void *output,const char *label,int dpi,int role){
    char text[512];plain_label(text,sizeof(text),label,0);
    if(native_workspace_classic())return scale(enhanced_font_width(text)*(role==2?2:1),dpi);
    HDC dc=output;HFONT font=label_font(dpi,role);HGDIOBJ old=SelectObject(dc,font);SIZE size;GetTextExtentPoint32A(dc,text,(int)strlen(text),&size);SelectObject(dc,old);DeleteObject(font);return size.cx;
}
void native_workspace_text_draw(void *output,const void *bounds,const char *label,unsigned flags,int dpi,int role,unsigned rgb){
    HDC dc=output;RECT r=*(const RECT *)bounds;
    if(!native_workspace_classic()){HFONT font=label_font(dpi,role);HGDIOBJ old=SelectObject(dc,font);SetTextColor(dc,rgb);SetBkMode(dc,TRANSPARENT);DrawTextA(dc,label,-1,&r,flags);SelectObject(dc,old);DeleteObject(font);return;}
    char text[1024];plain_label(text,sizeof(text),label,flags);
    int factor=role==2?2:1,fh=enhanced_font_height(),line=scale(fh*factor,dpi),count=0;
    char lines[64][256];size_t used=0;lines[0][0]=0;
    for(const char *p=text;*p&&count<63;){
        if(*p=='\n'){lines[count++][used]=0;used=0;lines[count][0]=0;++p;continue;}
        const char *end=p;while(*end&&*end!=' '&&*end!='\n')++end;if(end==p)++end;
        size_t n=(size_t)(end-p);if(used+n>=sizeof(lines[0]))n=sizeof(lines[0])-used-1;
        char trial[256];memcpy(trial,lines[count],used);memcpy(trial+used,p,n);trial[used+n]=0;
        if((flags&DT_WORDBREAK)&&used&&scale(enhanced_font_width(trial)*factor,dpi)>r.right-r.left){lines[count++][used]=0;used=0;lines[count][0]=0;if(*p==' '){++p;continue;}}
        if(n){memcpy(lines[count]+used,p,n);used+=n;lines[count][used]=0;p+=n;}else ++p;
    }
    if(used||!count)++count;
    int y=r.top;if(flags&DT_VCENTER)y+=(r.bottom-r.top-count*line)/2;
    int saved=SaveDC(dc);IntersectClipRect(dc,r.left,r.top,r.right,r.bottom);
    for(int i=0;i<count;++i){int width=enhanced_font_width(lines[i]);if(!width)continue;int pixelw=scale(width*factor,dpi),x=r.left;
        if(flags&DT_CENTER)x+=(r.right-r.left-pixelw)/2;else if(flags&DT_RIGHT)x=r.right-pixelw;
        uint8_t *ink=malloc((size_t)width*fh);uint32_t *pixels=malloc((size_t)width*fh*4),*mask=malloc((size_t)width*fh*4);
        if(ink&&pixels&&mask){memset(ink,0,(size_t)width*fh);enhanced_font_draw(ink,width,fh,width,0,0,lines[i],1);
            uint32_t color=(GetRValue(rgb)<<16)|(GetGValue(rgb)<<8)|GetBValue(rgb);
            for(int k=0;k<width*fh;++k){pixels[k]=ink[k]?color:0;mask[k]=ink[k]?0:0xffffff;}
            BITMAPINFO info={.bmiHeader={sizeof(BITMAPINFOHEADER),width,-fh,1,32,BI_RGB}};SetStretchBltMode(dc,COLORONCOLOR);
            StretchDIBits(dc,x,y+i*line,pixelw,line,0,0,width,fh,mask,&info,DIB_RGB_COLORS,SRCAND);StretchDIBits(dc,x,y+i*line,pixelw,line,0,0,width,fh,pixels,&info,DIB_RGB_COLORS,SRCPAINT);
        }free(ink);free(pixels);free(mask);
    }RestoreDC(dc,saved);
}
const char *native_workspace_button_caption(unsigned id){
    switch(id){case 8:case 0x106:return "Surface";case 9:case 0x107:return "Black Nest";case 10:case 0x108:return "Red Nest";
    case 11:case 0x110:return "Yellow";case 12:return "Spider";case 13:return "B. Queen";case 14:return "R. Queen";
    case 0x105:return "Yard";case 0x109:case 0x10c:return "Nest scent";case 0x10a:case 0x10d:return "Trail";case 0x10b:return "Alarm";
    case 0x1907:return "Patch";case 0x1908:return "Yard";case 0xfd22:return "House";case 0x1909:return "Strategic";case 0x190a:return "Graphic";case 0x190b:return "Mate";case 0x1910:return "Queen";
    case 0x190d:return "Automatic";case 0x190e:return "Manual";}return NULL;
}
