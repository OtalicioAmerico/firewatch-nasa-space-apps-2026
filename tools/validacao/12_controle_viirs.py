import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
u=pickle.load(open(os.path.join(SCR,'cache2.pkl'),'rb'))
sub=[r for r in u if r['date']=='2026-07-25' and r['prod'] in('VIIRS_NOAA20_SP','VIIRS_NOAA21_SP','VIIRS_SNPP_SP') and -60<=r['lon']<=-50 and -15<=r['lat']<=-5]
S={k:[r for r in sub if r['sat']==k] for k in('N20','N21','SNPP')}; print({k:len(v) for k,v in S.items()})
def run(a,b,R,T):
    p=cands(S[a],S[b],R,T); hit={i for i,_,_ in p}
    nul=sum(len({i for i,_,_ in cands(S[a],S[b],R,T,shift=sh)}) for sh in[(0.3,0),(-0.3,0),(0,0.3),(0,-0.3)])/4
    h=collections.Counter(d//15*15 for _,_,d in p).most_common(2)
    return len(S[a]),len(hit),round(100*len(hit)/len(S[a]),1),round(100*nul/len(S[a]),2),h,dict(comps(p))
for a,b in(('N20','N21'),('N20','SNPP'),('N21','SNPP')):
    for R in(375,750):
        print(a,b,R,'T60',run(a,b,R,60))
# atributos MODIS vs VIIRS: resolucao
import statistics
for p,s in(('MODIS_SP','Aqua'),('MODIS_SP','Terra'),('VIIRS_NOAA20_SP','N20')):
    a=[r for r in u if r['full'] and r['prod']==p and r['sat']==s]
    sc=[r['scan'] for r in a]; print(p,s,len(a),'scan med/min/max',statistics.median(sc),min(sc),max(sc),'conf',list(collections.Counter(r['conf'] for r in a).most_common(4)))
# registros com duplicidade espacial dentro do mesmo satelite/dia (pixel duplicado)
