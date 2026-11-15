"""Prototipo de armazenamento local (SQLite): importa os CSV FIRMS preservados, deduplica e mede tamanho/tempo.

Uso (a partir da raiz do repositorio):  NASA_DATA_DIR=<dados NASA> python tools/pesquisa/sqlite_prototipo.py <diretorio de saida FORA do Git>
Somente leitura nos dados; grava a.db e b.db no diretorio de saida.
"""
import os,sys,glob,sqlite3,time,math
sys.path.insert(0,'.')
from firecal.records import read_firms_csv, deduplicate
R=os.environ['NASA_DATA_DIR']; S=sys.argv[1]
t0=time.time(); recs=[]; nbytes=0
for f in sorted(glob.glob(os.path.join(R,'NASA_FIRMS','**','*.csv'),recursive=True)+glob.glob(os.path.join(R,'EVIDENCIAS','amostras_dimensionamento','*.csv'))):
    rel=os.path.relpath(f,R).replace(os.sep,'/')
    try: recs+=read_firms_csv(f,rel,'x'); nbytes+=os.path.getsize(f)
    except Exception as e: pass
raw=len(recs); u=deduplicate(recs); print('raw',raw,'unicos',len(u),'bytes CSV',nbytes,round(nbytes/raw,1),'B/linha',round(time.time()-t0,1),'s')
for name,rtree in (('a.db',False),('b.db',True)):
    p=os.path.join(S,name)
    if os.path.exists(p): os.remove(p)
    c=sqlite3.connect(p); c.execute('pragma journal_mode=wal'); c.execute('pragma synchronous=off')
    c.executescript('''create table det(id integer primary key,sat text not null,t_min integer not null,acq_date text not null,lat real not null,lon real not null,frp real,conf text,scan real,track real,dn text,prov text not null,unique(sat,t_min,lat,lon));''')
    t0=time.time()
    c.executemany('insert into det(sat,t_min,acq_date,lat,lon,frp,conf,scan,track,dn,prov) values(?,?,?,?,?,?,?,?,?,?,?)',[(r.sat,r.t,r.date,r.lat,r.lon,r.frp,r.conf,r.scan,r.track,r.dn,r.refs[0]) for r in u])
    c.commit(); t1=time.time()-t0
    c.execute('create index ix_dsat on det(acq_date,sat)'); 
    c.execute('create index ix_cell on det(acq_date,cast(floor(lat/0.25) as integer),cast(floor(lon/0.25) as integer))') if False else None
    if rtree:
        c.execute('create virtual table rt using rtree(id,minlat,maxlat,minlon,maxlon)'); c.execute('insert into rt select id,lat,lat,lon,lon from det')
    c.commit(); c.execute('pragma wal_checkpoint(truncate)'); c.close()
    sz=os.path.getsize(p)
    c=sqlite3.connect(p); t=time.time()
    n=c.execute("select count(*) from (select acq_date,cast(lat/0.25 as int),cast(lon/0.25 as int),sat from det group by 1,2,3,4)").fetchone()[0]; ta=time.time()-t
    t=time.time(); q=c.execute("select count(*) from det where acq_date between '2025-07-21' and '2025-07-25' and lat between -13.4 and -5.2 and lon between -50.7 and -45.7").fetchone()[0]; tq=time.time()-t
    if rtree:
        t=time.time(); q2=c.execute("select count(*) from rt where minlat>=-13.4 and maxlat<=-5.2 and minlon>=-50.7 and maxlon<=-45.7").fetchone()[0]; tr=time.time()-t
    print(name,'rtree' if rtree else 'sem rtree','insert',round(t1,1),'s; tamanho',round(sz/1e6,1),'MB =',round(sz/len(u)),'B/linha; agregacao celula-dia',round(ta,2),'s ->',n,'linhas; consulta caixa+data',round(tq,3),'s ->',q, ('; rtree caixa '+str(round(tr,3))+'s -> '+str(q2)) if rtree else '')
