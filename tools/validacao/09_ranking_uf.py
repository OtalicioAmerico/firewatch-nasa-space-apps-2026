import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
UFN={'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
WIN=(60,150)
tab={}
for y in('2025','2026'):
    V=sel(y,'VIIRS_NOAA20_SP'); A=sel(y,'MODIS_SP','Aqua'); T=sel(y,'MODIS_SP','Terra')
    pa=cands(A,V,1000,0,tmin=WIN[0],tmax=WIN[1]); hit={i for i,_,_ in pa}
    pa5=cands(A,V,500,0,tmin=WIN[0],tmax=WIN[1]); hit5={i for i,_,_ in pa5}
    for i,a in enumerate(A):
        if a['uf'] and a['br']:
            k=(a['uf'],y); s=tab.setdefault(k,collections.Counter()); s['aqua']+=1; s['hit1k']+= i in hit; s['hit500']+= i in hit5
    for r in T:
        if r['uf'] and r['br']: tab.setdefault((r['uf'],y),collections.Counter())['terra']+=1
    for r in V:
        if r['uf'] and r['br']: tab.setdefault((r['uf'],y),collections.Counter())['n20']+=1
        if r['uf'] and r['br']: tab[(r['uf'],y)]['n20_'+r['date']]+=1
    for r in A:
        if r['uf'] and r['br']: tab[(r['uf'],y)]['aq_'+r['date']]+=1
rows=[]
for uf in sorted({k[0] for k in tab}):
    a25,a26=tab[(uf,'2025')],tab[(uf,'2026')]
    mina=min(a25['aqua'],a26['aqua']); 
    dayok=sum(1 for y,t in(('2025',a25),('2026',a26)) for d in D5[y] if t['aq_'+d]>=5 and t['n20_'+d]>=5)
    rows.append((uf,UFN[uf],a25['aqua'],a26['aqua'],a25['terra'],a26['terra'],a25['n20'],a26['n20'],round(100*a25['hit1k']/max(a25['aqua'],1)),round(100*a26['hit1k']/max(a26['aqua'],1)),round(100*a25['hit500']/max(a25['aqua'],1)),round(100*a26['hit500']/max(a26['aqua'],1)),dayok))
rows.sort(key=lambda r:-min(r[2],r[3]))
print('UF cod | aqua25 aqua26 terra25 terra26 n20_25 n20_26 | %hit1km25 %hit1km26 %hit500_25 %hit500_26 | dias(de 10) com >=5 Aqua e >=5 N20')
for r in rows[:14]: print(r)
