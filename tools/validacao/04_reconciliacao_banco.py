import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import csv
u=pickle.load(open(os.path.join(SCR,'cache2.pkl'),'rb'))
BS='/'
db=[r for r in u if any(not ('amostras' in f) for f in r['files'])]   # exclui registros so existentes em amostras
print('raw unico (sem amostras)',len(db))
rows=list(csv.reader(open(P(r'\PESQUISA\data_work\_raw_export_lote3.tsv'),encoding='utf-8'),delimiter=chr(9)))
hdr=rows[1]; data=rows[2:]; print(hdr); print('tsv',len(data))
ix={h:i for i,h in enumerate(hdr)}
SM={'NOAA-20':'N20','NOAA-21':'N21','Terra':'Terra','Aqua':'Aqua','N20':'N20','N21':'N21','Suomi-NPP':'SNPP','SNPP':'SNPP'}
print(collections.Counter(d[ix['Satellite']] for d in data))
def tkey(d):
    t=dt.datetime.strptime(d[ix['acquired_utc']],'%Y-%m-%dT%H:%M:%S'); return int((t-EPOCH).total_seconds()//60)
tsv={}
for d in data:
    k=(d[ix['Satellite']],tkey(d),round(float(d[ix['Latitude']]),5),round(float(d[ix['Longitude']]),5))
    tsv.setdefault(k,[]).append(d)
print('tsv chaves unicas',len(tsv),'dup chaves',sum(1 for v in tsv.values() if len(v)>1))
print(collections.Counter(d[ix['FirmsSource']] for d in data))
sat_t=set(d[ix['Satellite']] for d in data)
# mapeamento satelite
def rk(r):
    return r['sat']
m=0; miss=[]
rawkeys=set()
for r in db:
    s=r['sat']; rawkeys.add((s,r['t'],round(r['lat'],5),round(r['lon'],5)))
tk=set((SM.get(k[0],k[0]),)+k[1:] for k in tsv)
print('raw nao no tsv',len(rawkeys-tk),'tsv nao no raw',len(tk-rawkeys),'intersec',len(rawkeys&tk))
x=list(rawkeys-tk)[:5]; print(x)
cnt=collections.Counter((k[0],k[1]//1440) for k in rawkeys-tk); print(sorted(collections.Counter(EPOCH.__add__(dt.timedelta(minutes=k[1])).strftime('%Y-%m-%d')+' '+k[0] for k in rawkeys-tk).items())[:30])
print('status',collections.Counter(d[ix['Status']] for d in data))
# Brasil (Inside) x bioma PIP
agree=collections.Counter()
rawmap={(r['sat'],r['t'],round(r['lat'],5),round(r['lon'],5)):r for r in db}
for k,v in tsv.items():
    kk=(SM.get(k[0],k[0]),)+k[1:]
    r=rawmap.get(kk)
    if r is None: continue
    st=v[0][ix['Status']]; agree[(st, 'bioma' if r['br'] else 'fora')]+=1
print(agree)
bi=collections.Counter()
for k,v in tsv.items():
    kk=(SM.get(k[0],k[0]),)+k[1:]; r=rawmap.get(kk)
    if r is None: continue
    if v[0][ix['Status']]=='Inside' and r['br']: bi[(v[0][ix['BiomeCode']], r['bioma'])]+=1
print('bioma legacy x ibge pip',sorted(bi.items()))
# anexar UF legacy
n=0
for k,v in tsv.items():
    kk=(SM.get(k[0],k[0]),)+k[1:]; r=rawmap.get(kk)
    if r is None: continue
    r['status']=v[0][ix['Status']]; r['uf']=v[0][ix['StateCode']] or None; r['mun']=v[0][ix['MunicipalityCode']] or None; n+=1
print('anexados',n)
pickle.dump(db,open(os.path.join(SCR,'cache3.pkl'),'wb'))
c=collections.Counter(); 
for r in db:
    c[(r.get('status'),r['br'])]+=1
print('status x bioma',c)
# discordancias: exemplos
dis=[r for r in db if (r.get('status')=='Inside')!=r['br']]
print('discordantes',len(dis)); 
import itertools
print(collections.Counter((r.get('status'),r['br']) for r in dis))
print([ (r['lat'],r['lon'],r['date'],r.get('uf')) for r in dis[:6]])
