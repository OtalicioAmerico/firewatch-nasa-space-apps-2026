import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
t0=time.time()
# --- Delta t Aqua/Terra x N20, pares <=1km +-6h
H={}
for y in ('2025','2026'):
    V=sel(y,'VIIRS_NOAA20_SP')
    for s in('Aqua','Terra'):
        M=sel(y,'MODIS_SP',s)
        p=cands(M,V,1000,360)
        h=collections.Counter((d//30)*30 for _,_,d in p); H[(y,s)]=h
        top=h.most_common(3)
        print(y,s,'pares<=1km',len(p),'classes modais(min,n):',top, 'M',len(M),'V',len(V),round(time.time()-t0))
pickle.dump(H,open(os.path.join(SCR,'H.pkl'),'wb'))
