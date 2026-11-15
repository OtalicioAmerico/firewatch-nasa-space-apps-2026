import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
db=pickle.load(open(os.path.join(SCR,'cache3.pkl'),'rb'))
D5={y:[f'{y}-07-{d}' for d in('21','22','23','24','25')] for y in('2025','2026')}
def sel(y,prod,sat=None,br=None,skip=None):
    out=[]
    for r in db:
        if r['prod']!=prod or r['date'] not in D5[y] or not r['full']: continue
        if sat and r['sat']!=sat: continue
        if br is not None and r['br']!=br: continue
        if skip and r['date']==skip: continue
        out.append(r)
    return out
CELL=0.05
def grid(pts):
    g=collections.defaultdict(list)
    for i,p in enumerate(pts): g[(int(math.floor(p['lat']/CELL)),int(math.floor(p['lon']/CELL)))].append(i)
    return g
def cands(M,V,R,T,shift=(0,0),tmin=None,tmax=None):
    """pares (i,j): dist<=R m, dt=tM-tV dentro de [tmin,tmax] (min). shift em graus aplicado a V (controle)."""
    if tmin is None: tmin,tmax=-T,T
    Vs=[dict(lat=v['lat']+shift[0],lon=v['lon']+shift[1],t=v['t']) for v in V] if shift!=(0,0) else V
    g=grid(Vs); pairs=[]
    for i,m in enumerate(M):
        ci,cj=int(math.floor(m['lat']/CELL)),int(math.floor(m['lon']/CELL))
        for a in(-1,0,1):
            for b in(-1,0,1):
                for j in g.get((ci+a,cj+b),()):
                    v=Vs[j]; d=m['t']-v['t']
                    if tmin<=d<=tmax and hav(m['lat'],m['lon'],v['lat'],v['lon'])<=R: pairs.append((i,j,d))
    return pairs
def comps(pairs):
    par={}
    def f(x):
        while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for i,j,_ in pairs: par[f(('m',i))]=f(('v',j))
    cm=collections.defaultdict(lambda:[0,0])
    for x in list(par): 
        r=f(x); cm[r][0 if x[0]=='m' else 1]+=1
    c=collections.Counter()
    for nm,nv in cm.values():
        c['1:1' if nm==1 and nv==1 else '1:N' if nm==1 else 'N:1' if nv==1 else 'M:N']+=1
    return c
def spearman(x,y):
    def rk(a):
        o=sorted(range(len(a)),key=lambda i:a[i]); r=[0]*len(a); i=0
        while i<len(a):
            j=i
            while j+1<len(a) and a[o[j+1]]==a[o[i]]: j+=1
            for k in range(i,j+1): r[o[k]]=(i+j)/2+1
            i=j+1
        return r
    rx,ry=rk(x),rk(y); n=len(x); mx=sum(rx)/n; my=sum(ry)/n
    sxy=sum((a-mx)*(b-my) for a,b in zip(rx,ry)); sx=sum((a-mx)**2 for a in rx); sy=sum((b-my)**2 for b in ry)
    return sxy/math.sqrt(sx*sy) if sx and sy else float('nan')
