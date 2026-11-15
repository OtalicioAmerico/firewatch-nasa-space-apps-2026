import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import re
BS='/'
u=pickle.load(open(os.path.join(SCR,'cache.pkl'),'rb'))
FULLSB={'292f9b7c','e22d3f8a','de186e6a','dade109b','ef025268','3e533fe8','5e3ea8e5','1b5ff34c','e22d0478'}
def prod(r):
    for f in sorted(r['files']):
        m=re.search(r'(MODIS_SP|MODIS_NRT|VIIRS_NOAA20_SP|VIIRS_NOAA20_NRT|VIIRS_NOAA21_SP|VIIRS_NOAA21_NRT|VIIRS_SNPP_SP)',f)
        if m: return m.group(1)
def isfull(r):
    for f in r['files']:
        if f.split(BS)[1][:3]=='lot' or 'amostras' in f: return True
        if f.split(BS)[-1][:8] in FULLSB: return True
    return False
for r in u: r['prod']=prod(r); r['full']=isfull(r); r['br']=r['bioma'] is not None
pickle.dump(u,open(os.path.join(SCR,'cache2.pkl'),'wb'))
F=[r for r in u if r['full']]
print('unique full-bbox',len(F),'sub-bbox only',len(u)-len(F))
c=collections.Counter((r['prod'],r['sat']) for r in F)
for k in sorted(c): 
    d=sorted({r['date'] for r in F if (r['prod'],r['sat'])==k}); print(k,c[k],'days',len(d),d[0],d[-1])
# calendario de dias por produto SP
days=collections.defaultdict(lambda: collections.Counter())
for r in F:
    if r['prod'] in('MODIS_SP','VIIRS_NOAA20_SP'): days[r['date']][r['prod']]+=1
both=[d for d in sorted(days) if len(days[d])==2]; mo=[d for d in sorted(days) if set(days[d])=={'MODIS_SP'}]; vo=[d for d in sorted(days) if set(days[d])=={'VIIRS_NOAA20_SP'}]
print('SP dias com ambos',len(both),both)
print('MODIS_SP sem N20',len(mo),'primeiro/ultimo',mo[0],mo[-1],' meses',sorted({d[:7] for d in mo}))
print('N20_SP sem MODIS',len(vo),vo)
print('--- referencia: retangulo, 5 dias')
for y in ('2025','2026'):
    for p in('MODIS_SP','VIIRS_NOAA20_SP'):
        n=sum(1 for r in F if r['prod']==p and r['date'] in [f'{y}-07-{d}' for d in('21','22','23','24','25')])
        nb=sum(1 for r in F if r['prod']==p and r['date'] in [f'{y}-07-{d}' for d in('21','22','23','24','25')] and r['br'])
        print(y,p,n,'dentro do Brasil(bioma)',nb)
print('--- por dia / satelite (retangulo; Brasil por bioma)')
for y in ('2025','2026'):
  for d in ('21','22','23','24','25'):
    dd=f'{y}-07-{d}'; row=[]
    for s in ('Terra','Aqua','N20'):
        a=[r for r in F if r['date']==dd and r['sat']==s and r['prod'] in('MODIS_SP','VIIRS_NOAA20_SP')]
        row.append(f'{s}={len(a)}({sum(r["br"] for r in a)})')
    print(dd,' '.join(row))
# horas UTC por satelite/dia (agrupar passagens por gap>40min)
print('--- passagens (clusters gap>30min) 10 dias')
for y in ('2025','2026'):
  for d in ('21','22','23','24','25'):
    dd=f'{y}-07-{d}'
    for s in ('Terra','Aqua','N20'):
        a=sorted(r['t'] for r in F if r['date']==dd and r['sat']==s and r['prod'] in('MODIS_SP','VIIRS_NOAA20_SP'))
        cl=[];
        for t in a:
            if cl and t-cl[-1][-1]<=30: cl[-1].append(t)
            else: cl.append([t])
        txt=' '.join(f"{(EPOCH+dt.timedelta(minutes=c[0])).strftime('%H:%M')}n{len(c)}" for c in cl)
        if s!='N20' or y in('2025','2026'): print(dd,s,len(cl),'passagens:',txt)
