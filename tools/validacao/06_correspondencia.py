import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
t0=time.time()
WIN={'Aqua':(60,150),'Terra':(-300,-210)}  # definida SOMENTE com 2025
SH=[(0.3,0),(-0.3,0),(0,0.3),(0,-0.3)]
res={}
for y in('2025','2026'):
    V=sel(y,'VIIRS_NOAA20_SP')
    for s in('Aqua','Terra'):
        M=sel(y,'MODIS_SP',s); lo,hi=WIN[s]
        for R in(500,1000,3000):
            p=cands(M,V,R,0,tmin=lo,tmax=hi)
            hit={i for i,_,_ in p}
            nul=0
            for sh in SH: nul+=len({i for i,_,_ in cands(M,V,R,0,shift=sh,tmin=lo,tmax=hi)})
            nul/=4
            c=comps(p) if s=='Aqua' else None
            res[(y,s,R)]=(len(M),len(hit),nul,c)
            print(f'{y} {s:5s} R={R:4d} janela[{lo},{hi}] M={len(M)} com_candidato={len(hit)} ({100*len(hit)/len(M):.1f}%) acaso={100*nul/len(M):.2f}% razao_obs/acaso={len(hit)/max(nul,1e-9):.0f} comps={dict(c) if c else ""}',flush=True)
# so dentro do Brasil (MODIS no Brasil, VIIRS todo)
print('--- MODIS dentro do Brasil, Aqua, 1km')
for y in('2025','2026'):
    V=sel(y,'VIIRS_NOAA20_SP'); M=sel(y,'MODIS_SP','Aqua',br=True); lo,hi=WIN['Aqua']
    hit={i for i,_,_ in cands(M,V,1000,0,tmin=lo,tmax=hi)}
    print(y,len(M),len(hit),f'{100*len(hit)/len(M):.1f}%')
# por dia (Aqua, 1 km), sem escolher: incluir dia 22/07/2026
print('--- por dia Aqua 1km janela')
for y in('2025','2026'):
    V=sel(y,'VIIRS_NOAA20_SP')
    for d in D5[y]:
        M=[r for r in sel(y,'MODIS_SP','Aqua') if r['date']==d]; lo,hi=WIN['Aqua']
        hit={i for i,_,_ in cands(M,V,1000,0,tmin=lo,tmax=hi)}
        print(d,len(M),len(hit),f'{100*len(hit)/max(len(M),1):.0f}%')
# sensibilidade a janela estreita (<=60min) e larga
print('--- sensibilidade tempo (Aqua, 500m)')
for y in('2025','2026'):
    V=sel(y,'VIIRS_NOAA20_SP'); M=sel(y,'MODIS_SP','Aqua')
    for T in(30,60,120,180):
        hit={i for i,_,_ in cands(M,V,500,T)}; print(y,'|dt|<=',T,f'{100*len(hit)/len(M):.1f}%')
print('tempo',round(time.time()-t0))
