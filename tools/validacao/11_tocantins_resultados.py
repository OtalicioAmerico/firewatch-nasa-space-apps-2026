import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
Fu=pickle.load(open(os.path.join(SCR,'cache_to.pkl'),'rb'))
TO=[r for r in Fu if r['mun_to']]
print('registros TO (bbox cheio, todos produtos)',len(TO))
days=sorted({r['date'] for r in TO if r['prod'] in('MODIS_SP','VIIRS_NOAA20_SP')})
print('--- TO por dia (MODIS_SP: Terra/Aqua ; N20_SP)')
for d in days:
    a=[r for r in TO if r['date']==d]
    t=sum(1 for r in a if r['prod']=='MODIS_SP' and r['sat']=='Terra'); q=sum(1 for r in a if r['prod']=='MODIS_SP' and r['sat']=='Aqua'); n=sum(1 for r in a if r['prod']=='VIIRS_NOAA20_SP')
    if (d[8:]=='15') or d.startswith('2025-07-2') or d.startswith('2026-07-2'): print(d,'Terra',t,'Aqua',q,'N20',n)
# agosto MODIS TO soma
for y in('2025','2026'):
    ser=[sum(1 for r in TO if r['date']==f'{y}-08-{d:02d}' and r['prod']=='MODIS_SP') for d in range(1,32)]
    print(y,'ago MODIS TO diario',ser,'total',sum(ser),'dias<10:',sum(1 for s in ser if s<10))
# celula-dia TO, 29 dias SP com ambos
both=[d for d in days if any(r['prod']=='MODIS_SP' and r['date']==d for r in TO) and any(r['prod']=='VIIRS_NOAA20_SP' and r['date']==d for r in TO)]
print('dias com ambos no TO',len(both))
for cs in(0.1,0.25,0.5):
    def cs_set(pr,sh=(0,0),dd=None): return {(int(math.floor((r['lat']+sh[0])/cs)),int(math.floor((r['lon']+sh[1])/cs)),r['date']) for r in TO if r['prod']==pr and r['date'] in dd}
    a=cs_set('MODIS_SP',dd=both); b=cs_set('VIIRS_NOAA20_SP',dd=both)
    nj=[]
    for sh in[(0.3,0),(-0.3,0),(0,0.3),(0,-0.3)]:
        bs=cs_set('VIIRS_NOAA20_SP',sh,both); nj.append(len(a&bs)/len(a|bs))
    print(f'TO cel {cs}: MODIS {len(a)} VIIRS {len(b)} ambos {len(a&b)} soMODIS {len(a-b)} soVIIRS {len(b-a)} Jaccard={len(a&b)/len(a|b):.3f} nulo={sum(nj)/4:.3f} MODIS_com_VIIRS={100*len(a&b)/len(a):.0f}%')
# candidatos individuais em TO (10 dias): Aqua x N20
print('--- TO: Aqua x N20 candidatos (janela 60-150 min)')
for y in('2025','2026'):
    V=[r for r in TO if r['prod']=='VIIRS_NOAA20_SP' and r['date'] in D5[y]]; A=[r for r in TO if r['prod']=='MODIS_SP' and r['sat']=='Aqua' and r['date'] in D5[y]]
    # vizinhos na borda: usa V completo do retangulo para candidatos perto da divisa do TO
    Vall=[r for r in sel(y,'VIIRS_NOAA20_SP')]
    for R_ in(500,1000,3000):
        p=cands(A,Vall,R_,0,tmin=60,tmax=150); hit={i for i,_,_ in p}
        print(y,R_,'Aqua TO',len(A),'com cand',len(hit),f'{100*len(hit)/len(A):.1f}%',dict(comps(p)))
# horas: passagens por satelite em TO nos 10 dias (hora local ~ UTC-3)
print('--- 22/07/2026 no TO:', {s:sum(1 for r in TO if r['date']=='2026-07-22' and r['sat']==s and r['prod'] in('MODIS_SP','VIIRS_NOAA20_SP')) for s in('Terra','Aqua','N20')})
# atributos: confianca, FRP
import statistics
for pr,sat in(('MODIS_SP','Aqua'),('VIIRS_NOAA20_SP','N20')):
    a=[r for r in TO if r['prod']==pr and r['sat']==sat and r['date'] in D5['2025']+D5['2026']]
    cf=collections.Counter(r['conf'] for r in a) if pr.startswith('VIIRS') else None
    fr=[r['frp'] for r in a if r['frp'] is not None]
    print(pr,sat,len(a),'FRP mediana',statistics.median(fr),'scan mediana',statistics.median(r['scan'] for r in a),'track',statistics.median(r['track'] for r in a),'dayNight',dict(collections.Counter(r['dn'] for r in a)),cf if cf else '')
