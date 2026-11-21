// mapdump seed half step out.bin : biome ids on a grid around spawn (y=63, same sampling as raysim)
#include <stdio.h>
#include <stdlib.h>
#include "biomes.h"
#include "finders.h"
#include "generator.h"
#include "util.h"
int main(int argc,char**argv){
  if(argc<5) return 2;
  long long seed=atoll(argv[1]); int half=atoi(argv[2]), step=atoi(argv[3]);
  Generator g; setupGenerator(&g,MC_1_21,0); applySeed(&g,0,(uint64_t)seed);
  Pos sp=estimateSpawn(&g,NULL);
  int n=2*half/step; int32_t *a=malloc(sizeof(int32_t)*n*n);
  for(int j=0;j<n;j++)for(int i=0;i<n;i++){
    int x=sp.x-half+i*step, z=sp.z-half+j*step;
    a[j*n+i]=getBiomeAt(&g,4,x>>2,15,z>>2);}
  FILE*f=fopen(argv[4],"wb"); int32_t h[4]={n,sp.x,sp.z,step}; fwrite(h,4,4,f); fwrite(a,4,(size_t)n*n,f); fclose(f);
  unsigned char col[256][3]; initBiomeColors(col); f=fopen("out/colors.bin","wb"); fwrite(col,1,256*3,f); fclose(f);
  printf("spawn %d %d n=%d\n",sp.x,sp.z,n); return 0;}
