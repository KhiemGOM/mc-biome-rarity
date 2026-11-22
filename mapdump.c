// mapdump seed half step out.bin : biome ids on a grid around spawn (y=63, same sampling as raysim)
#include <stdio.h>
#include <stdlib.h>
#include "biomes.h"
#include "finders.h"
#include "generator.h"
#include "util.h"
#include "c263world.h"
// Minecraft version: 263 = Java 26.3 (default; climate and spawn from c263climate.h, biome from the fork's btree263),
// 214 = the old path exactly as before (Cubiomes "1.21").
#ifndef DX_VERSION
#define DX_VERSION 263
#endif
#if DX_VERSION == 263
#define SIM_MC MC_26_3
#else
#define SIM_MC MC_1_21
#endif
int main(int argc,char**argv){
  if(argc<5) return 2;
  long long seed=atoll(argv[1]); int half=atoi(argv[2]), step=atoi(argv[3]);
  World w; world_setup(&w,SIM_MC); world_seed(&w,(uint64_t)seed);
  Pos sp=world_spawn(&w);
  int n=2*half/step; int32_t *a=malloc(sizeof(int32_t)*n*n);
  for(int j=0;j<n;j++)for(int i=0;i<n;i++){
    int x=sp.x-half+i*step, z=sp.z-half+j*step;
    a[j*n+i]=world_biome(&w,x>>2,15,z>>2);}
  FILE*f=fopen(argv[4],"wb"); int32_t h[4]={n,sp.x,sp.z,step}; fwrite(h,4,4,f); fwrite(a,4,(size_t)n*n,f); fclose(f);
  unsigned char col[256][3]; initBiomeColors(col); f=fopen("out/colors.bin","wb"); fwrite(col,1,256*3,f); fclose(f);
  printf("spawn %d %d n=%d\n",sp.x,sp.z,n); return 0;}
