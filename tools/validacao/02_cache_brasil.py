import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
t0=time.time()
recs=load_all(); print('raw rows',len(recs),time.time()-t0)
seen={}; dup=0
for r in recs:
    k=(r['sat'],r['t'],round(r['lat'],5),round(r['lon'],5))
    if k in seen: dup+=1; seen[k]['files'].add(r['file']); continue
    r['files']={r['file']}; seen[k]=r
u=list(seen.values()); print('unique',len(u),'dups',dup)
idx=ShpIndex(P(r'\IBGE_2025\biomas\lml_bioma_e250k_v20250911_A.shp')); print('shp idx',time.time()-t0)
# so classificar o que for usado (bbox cheio, nao NRT-novembro)
n=0
for r in u:
    r['bioma']=idx.locate(r['lon'],r['lat']); n+=1
    if n%50000==0: print(n,time.time()-t0,flush=True)
pickle.dump(u,open(os.path.join(SCR,'cache.pkl'),'wb'))
print('done',time.time()-t0)
