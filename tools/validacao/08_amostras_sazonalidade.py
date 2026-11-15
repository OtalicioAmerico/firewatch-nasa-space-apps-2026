import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
u=pickle.load(open(os.path.join(SCR,'cache2.pkl'),'rb')); F=[r for r in u if r['full']]
print('--- amostras dia 15: contagem retangulo / Brasil (bioma)')
rows=[]
for ym in ['2025-%02d'%m for m in range(1,13)]+['2026-%02d'%m for m in range(1,9)]:
    d=ym+'-15'; row={'d':d}
    for lab,p in(('MODIS','MODIS_SP'),('N20','VIIRS_NOAA20_SP')):
        a=[r for r in F if r['date']==d and r['prod']==p]; row[lab]=(len(a),sum(r['br'] for r in a))
    rows.append(row); print(d,'MODIS',row['MODIS'],'N20',row['N20'], 'razao BR',round(row['N20'][1]/row['MODIS'][1],2) if row['N20'][1] else '-')
# Spearman perfil mensal Brasil (meses com ambos)
both=[r for r in rows if r['N20'][0]]
x=[r['MODIS'][1] for r in both]; y=[r['N20'][1] for r in both]
print('n dias com ambos',len(both),'Spearman perfil (Brasil) MODIS x N20',round(spearman(x,y),3))
# 2025 vs 2026 jan-jul
for lab,k in(('MODIS',0),('N20',1)):
    a=[(r['d'],r[lab][1]) for r in rows if r['N20'][0] and r['d'][:4]=='2025' and r['d'][5:7]<='07']
    b=[(r['d'],r[lab][1]) for r in rows if r['N20'][0] and r['d'][:4]=='2026' and r['d'][5:7]<='07']
    print(lab,'jan-jul dia15 2025',[v for _,v in a],'2026',[v for _,v in b],'var% por mes',[round(100*(q/p-1)) for (_,p),(_,q) in zip(a,b)])
# MODIS agosto: serie diaria 2025 vs 2026 (Brasil)
print('--- MODIS_SP agosto diario (Brasil / retangulo) e passagens Aqua')
for y in('2025','2026'):
    ser=[]
    for dd in range(1,32):
        d=f'{y}-08-{dd:02d}'; a=[r for r in F if r['date']==d and r['prod']=='MODIS_SP']
        aq=sorted(r['t'] for r in a if r['sat']=='Aqua'); cl=0; prev=None
        for t in aq:
            if prev is None or t-prev>30: cl+=1
            prev=t
        ser.append((dd,len(a),sum(r['br'] for r in a),len(aq),cl))
    print(y,'diario (dia,tot,BR,Aqua,passagensAqua):',ser)
    tot=[s[1] for s in ser]; m=sum(tot)/len(tot); sd=(sum((v-m)**2 for v in tot)/(len(tot)-1))**.5
    print(y,'total mes',sum(tot),'BR',sum(s[2] for s in ser),'media/dia',round(m),'CV',round(sd/m,2),'min',min(tot),'max',max(tot))
