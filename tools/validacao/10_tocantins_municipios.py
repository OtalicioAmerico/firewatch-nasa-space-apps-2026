import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
# --- municipios de TO (codigo 17xxxxx) por PIP independente
dbf=open(P(r'\IBGE_2025\municipios\BR_Municipios_2025.dbf'),'rb').read()
n,hl,rl=struct.unpack('<xxxxIHH',dbf[:12]); flds=[];o=32
while dbf[o]!=13: flds.append((dbf[o:o+11].split(b'\0')[0].decode(),dbf[o+16])); o+=32
print(flds[:6])
off=1; offs={}
for nm,ln in flds: offs[nm]=(off,ln); off+=ln
cod=[]; 
for i in range(n):
    rec=dbf[hl+i*rl:hl+(i+1)*rl]; a,l=offs['CD_MUN']; cod.append(rec[a:a+l].decode().strip())
nmx=offs.get('NM_MUN'); 
shp=open(P(r'\IBGE_2025\municipios\BR_Municipios_2025.shp'),'rb').read()
pos=100; recno=0; keep=set(i+1 for i,c in enumerate(cod) if c.startswith('17'))
print('municipios total',len(cod),'TO',len(keep))
class Mini: pass
band=0.02; bands=collections.defaultdict(list); bbox={}
while pos<len(shp):
    clen=struct.unpack('>i',shp[pos+4:pos+8])[0]*2; c=shp[pos+8:pos+8+clen]; pos+=8+clen; recno+=1
    if recno not in keep: continue
    bb=struct.unpack('<4d',c[4:36]); npart,npts=struct.unpack('<ii',c[36:44])
    parts=list(struct.unpack('<%di'%npart,c[44:44+4*npart]))+[npts]; pts=struct.unpack('<%dd'%(2*npts),c[44+4*npart:44+4*npart+16*npts]); bbox[recno]=bb
    for a,b in zip(parts[:-1],parts[1:]):
        for i in range(a,b-1):
            x1,y1,x2,y2=pts[2*i],pts[2*i+1],pts[2*i+2],pts[2*i+3]
            if y1==y2: continue
            lo,hi=(y1,y2) if y1<y2 else (y2,y1)
            for bi in range(int(math.floor(lo/band)),int(math.floor(hi/band))+1): bands[(recno,bi)].append((x1,y1,x2,y2))
def inTO(lon,lat):
    bi=int(math.floor(lat/band))
    for rn,b in bbox.items():
        if lon<b[0] or lon>b[2] or lat<b[1] or lat>b[3]: continue
        ins=False
        for (x1,y1,x2,y2) in bands.get((rn,bi),()):
            if (y1>lat)!=(y2>lat) and x1+(lat-y1)*(x2-x1)/(y2-y1)>lon: ins=not ins
        if ins: return cod[rn-1]
    return None
u=pickle.load(open(os.path.join(SCR,'cache2.pkl'),'rb'))
Fu=[r for r in u if r['full']]
allb=[min(b[0] for b in bbox.values()),min(b[1] for b in bbox.values()),max(b[2] for b in bbox.values()),max(b[3] for b in bbox.values())]
print('bbox TO',allb)
for r in Fu:
    r['mun_to']=inTO(r['lon'],r['lat']) if (allb[0]<=r['lon']<=allb[2] and allb[1]<=r['lat']<=allb[3]) else None
# concordancia com UF legacy (db tem uf)
legacy={(r['sat'],r['t'],round(r['lat'],5),round(r['lon'],5)):r.get('uf') for r in db}
c=collections.Counter()
for r in Fu:
    k=(r['sat'],r['t'],round(r['lat'],5),round(r['lon'],5))
    if k in legacy: c[(legacy[k]=='17', r['mun_to'] is not None)]+=1
print('concordancia TO legacy x PIP municipal (legacyTO,pipTO):',c)
pickle.dump(Fu,open(os.path.join(SCR,'cache_to.pkl'),'wb'))
