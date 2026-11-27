#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "biomes.h"
#include "finders.h"
#include "generator.h"
#include "util.h"
#include "c263world.h"
// viz names | viz map seed half step out.bin (surface y=60, plus any-layer cave flag) | viz ray seed angle maxd | viz spawns s0 n
int main(int argc,char**argv){
  if(!strcmp(argv[1],"names")){unsigned char c[256][3];initBiomeColors(c);
    for(int i=0;i<256;i++){const char*s=biome2str(MC_26_3,i); if(s) printf("%d,%s,%d,%d,%d\n",i,s,c[i][0],c[i][1],c[i][2]);} return 0;}
  World w; world_setup(&w,MC_26_3);
  if(!strcmp(argv[1],"spawns")){long long s0=atoll(argv[2]); int n=atoi(argv[3]);
    for(int i=0;i<n;i++){world_seed(&w,(uint64_t)(s0+i)); Pos p=world_spawn(&w); printf("%lld %d %d\n",s0+i,p.x,p.z);} return 0;}
  if(!strcmp(argv[1],"pts")){ // stdin: "S seed" -> "spawn x z" | "P x z" -> surface biome id (y=60) | "Q x y z" -> biome id at that y
    char ln[256]; setvbuf(stdout,NULL,_IOFBF,1<<16);
    while(fgets(ln,sizeof ln,stdin)){
      if(ln[0]=='S'){long long s=atoll(ln+2); world_seed(&w,(uint64_t)s); Pos p=world_spawn(&w); printf("spawn %d %d\n",p.x,p.z); fflush(stdout);}
      else if(ln[0]=='P'){double x,z; sscanf(ln+2,"%lf %lf",&x,&z); printf("%d\n",world_biome(&w,((int)floor(x))>>2,15,((int)floor(z))>>2));}
      else if(ln[0]=='Q'){double x,y,z; sscanf(ln+2,"%lf %lf %lf",&x,&y,&z); printf("%d\n",world_biome(&w,((int)floor(x))>>2,((int)floor(y))>>2,((int)floor(z))>>2));}
      else if(ln[0]=='F') fflush(stdout);
    }
    return 0;}
  long long seed=atoll(argv[2]); world_seed(&w,(uint64_t)seed); Pos sp=world_spawn(&w);
  if(!strcmp(argv[1],"map")){int half=atoi(argv[3]),step=atoi(argv[4]); int n=2*half/step;
    int32_t*a=malloc(4*(size_t)n*n);
    for(int j=0;j<n;j++)for(int i=0;i<n;i++){int x=sp.x-half+i*step,z=sp.z-half+j*step; a[j*n+i]=world_biome(&w,x>>2,15,z>>2);}
    FILE*f=fopen(argv[5],"wb"); int32_t h[4]={n,sp.x,sp.z,step}; fwrite(h,4,4,f); fwrite(a,4,(size_t)n*n,f); fclose(f);
    printf("spawn %d %d\n",sp.x,sp.z); return 0;}
  if(!strcmp(argv[1],"mapc")){int cx=atoi(argv[3]),cz=atoi(argv[4]),half=atoi(argv[5]),step=atoi(argv[6]); int n=2*half/step;
    int32_t*a=malloc(4*(size_t)n*n);
    for(int j=0;j<n;j++)for(int i=0;i<n;i++){int x=cx-half+i*step,z=cz-half+j*step; a[j*n+i]=world_biome(&w,x>>2,argc>8?atoi(argv[8]):15,z>>2);}
    FILE*f=fopen(argv[7],"wb"); int32_t h[4]={n,cx,cz,step}; fwrite(h,4,4,f); fwrite(a,4,(size_t)n*n,f); fclose(f); return 0;}
  if(!strcmp(argv[1],"ray")){double ang=atof(argv[3]); double maxd=atof(argv[4]); double first[256]; for(int i=0;i<256;i++)first[i]=-1;
    printf("spawn %d %d\n",sp.x,sp.z);
    int lqx=1<<30,lqz=1<<30;
    for(double d=0; d<=maxd; d+=1.0){int x=(int)floor(sp.x+0.5+d*cos(ang)), z=(int)floor(sp.z+0.5+d*sin(ang)); int qx=x>>2,qz=z>>2;
      if(qx==lqx&&qz==lqz) continue; lqx=qx;lqz=qz;
      for(int qy=-16;qy<80;qy++){int b=world_biome(&w,qx,qy,qz); if(b>=0&&b<256&&first[b]<0){first[b]=d; printf("hit %d %.0f %d\n",b,d,qy*4);}}}
    return 0;}
  return 1;}
