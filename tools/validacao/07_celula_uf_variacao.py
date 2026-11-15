import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
# ---- celula-dia (dia UTC), 10 dias; MODIS = Terra+Aqua; VIIRS = N20
def cellset(pts,cs,shift=(0,0)):
    return {(int(math.floor((p['lat']+shift[0])/cs)),int(math.floor((p['lon']+shift[1])/cs)),p['date']) for p in pts}
print('--- celula-dia')
for y in('2025','2026'):
    M=sel(y,'MODIS_SP'); V=sel(y,'VIIRS_NOAA20_SP')
    for cs in(0.1,0.25,0.5,1.0):
        a=cellset(M,cs); b=cellset(V,cs); j=len(a&b)/len(a|b)
        nj=[]
        for sh in [(0.3,0),(-0.3,0),(0,0.3),(0,-0.3)]:
            bs=cellset(V,cs,sh); nj.append(len(a&bs)/len(a|bs))
        print(y,cs,'cel MODIS',len(a),'cel VIIRS',len(b),'ambos',len(a&b),'so MODIS',len(a-b),'so VIIRS',len(b-a),f'Jaccard={j:.3f} nulo={sum(nj)/4:.3f} MODIS_com_VIIRS={100*len(a&b)/len(a):.0f}%')
# ---- UF (legacy) Spearman e razao
print('--- UF')
for y in('2025','2026'):
    M=sel(y,'MODIS_SP',br=True); V=sel(y,'VIIRS_NOAA20_SP',br=True)
    cm=collections.Counter(r['uf'] for r in M if r['uf']); cv=collections.Counter(r['uf'] for r in V if r['uf'])
    ufs=sorted(set(cm)|set(cv)); x=[cm[u] for u in ufs]; z=[cv[u] for u in ufs]
    print(y,'UFs',len(ufs),'Spearman',round(spearman(x,z),3),'razao geral',round(sum(z)/sum(x),2))
    big=[(u,cm[u],cv[u],round(cv[u]/max(cm[u],1),1)) for u in ufs if cm[u]>=20]; print(' razao UF (>=20 MODIS):',big)
# ---- variacao anual
print('--- variacao anual')
for scope,br in (('retangulo',None),('Brasil',True)):
    for skip in (None,'x'):
        out=[]
        for p in('MODIS_SP','VIIRS_NOAA20_SP'):
            a=len([r for r in sel('2025',p,br=br)]); 
            b=len([r for r in sel('2026',p,br=br,skip=None)]) if skip is None else len([r for r in sel('2026',p,br=br) if r['date']!='2026-07-22'])
            a2=a if skip is None else len([r for r in sel('2025',p,br=br) if r['date']!='2025-07-22'])
            out.append((p,a2,b,round(100*(b/a2-1),1)))
        print(scope,'com 22/07' if skip is None else 'sem 22/07 (ambos anos)',out)
