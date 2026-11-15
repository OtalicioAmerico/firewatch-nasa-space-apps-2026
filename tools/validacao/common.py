"""Verificacao independente - Missao 01 (portada na Missao 02). Somente biblioteca padrao. Leitura apenas.

Configuracao (nenhum caminho pessoal no codigo):
  --data-dir <dir>  ou variavel NASA_DATA_DIR : diretorio com NASA_FIRMS, EVIDENCIAS, IBGE_2025, MANIFESTOS, PESQUISA
  --work-dir <dir>  ou variavel FIRECAL_WORK_DIR : caches e saidas (padrao: tools/validacao/.cache, ignorado pelo Git)
"""
import csv, glob, os, sys, math, struct, pickle, collections, datetime as dt, time, random


def _arg(name, env, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        v = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return v
    return os.environ.get(env, default)


R = _arg('--data-dir', 'NASA_DATA_DIR')
if not R:
    sys.exit('Informe o diretorio dos dados NASA: --data-dir <dir> ou NASA_DATA_DIR '
             '(o diretorio que contem NASA_FIRMS, EVIDENCIAS, IBGE_2025, MANIFESTOS, PESQUISA).')
R = os.path.abspath(R)
SCR = os.path.abspath(_arg('--work-dir', 'FIRECAL_WORK_DIR',
                           os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')))
os.makedirs(SCR, exist_ok=True)


def P(rel):
    """Caminho dentro do diretorio de dados; aceita barra normal ou invertida."""
    return os.path.join(R, *rel.replace(chr(92), '/').strip('/').split('/'))


SATMAP = {'Terra': 'Terra', 'Aqua': 'Aqua', 'N20': 'N20', 'N21': 'N21', 'N': 'SNPP'}
EPOCH = dt.datetime(1970, 1, 1)


def load_all():
    """Retorna lista de registros (dict) de todos os CSV FIRMS preservados, sem deduplicar."""
    recs = []
    files = sorted(glob.glob(os.path.join(R, 'NASA_FIRMS', '**', '*.csv'), recursive=True)
                   + glob.glob(os.path.join(R, 'EVIDENCIAS', 'amostras_dimensionamento', '*.csv')))
    for f in files:
        rel = os.path.relpath(f, R).replace(os.sep, '/')

        with open(f, encoding='utf-8') as fh:
            rd = csv.DictReader(fh)
            for r in rd:
                if 'acq_date' not in r:
                    break
                hhmm = int(r['acq_time'])
                d = dt.datetime.strptime(r['acq_date'], '%Y-%m-%d') + dt.timedelta(hours=hhmm // 100, minutes=hhmm % 100)
                src = os.path.basename(os.path.dirname(os.path.dirname(f))) if 'amostras' not in f else 'SAMPLE'
                prod = None
                recs.append(dict(
                    file=rel, lat=float(r['latitude']), lon=float(r['longitude']),
                    t=int((d - EPOCH).total_seconds() // 60),  # minutos UTC desde 1970
                    date=r['acq_date'], sat=SATMAP[r['satellite']], inst=r['instrument'],
                    scan=float(r['scan']), track=float(r['track']),
                    conf=r['confidence'], frp=float(r['frp']) if r['frp'] else None,
                    dn=r['daynight'], typ=r.get('type')))
    return recs


def sensor_of(sat):
    return 'MODIS' if sat in ('Terra', 'Aqua') else 'VIIRS'


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742000.0 * math.asin(math.sqrt(a))


# ---------- point in polygon sobre shapefile IBGE ----------
class ShpIndex:
    def __init__(self, shp, band=0.02):
        self.band = band
        self.bands = collections.defaultdict(list)  # (cod, bandidx) -> [(x1,y1,x2,y2)]
        self.bbox = {}
        s = open(shp, 'rb').read()
        pos = 100
        n = len(s)
        recno = 0
        while pos < n:
            clen = struct.unpack('>i', s[pos + 4:pos + 8])[0] * 2
            c = s[pos + 8:pos + 8 + clen]
            pos += 8 + clen
            st = struct.unpack('<i', c[:4])[0]
            if st == 0:
                recno += 1
                continue
            bb = struct.unpack('<4d', c[4:36])
            npart, npts = struct.unpack('<ii', c[36:44])
            parts = list(struct.unpack('<%di' % npart, c[44:44 + 4 * npart])) + [npts]
            pts = struct.unpack('<%dd' % (2 * npts), c[44 + 4 * npart:44 + 4 * npart + 16 * npts])
            recno += 1
            self.bbox[recno] = bb
            for a, b in zip(parts[:-1], parts[1:]):
                for i in range(a, b - 1):
                    x1, y1, x2, y2 = pts[2 * i], pts[2 * i + 1], pts[2 * i + 2], pts[2 * i + 3]
                    if y1 == y2:
                        continue
                    lo, hi = (y1, y2) if y1 < y2 else (y2, y1)
                    for bi in range(int(math.floor(lo / band)), int(math.floor(hi / band)) + 1):
                        self.bands[(recno, bi)].append((x1, y1, x2, y2))
        self.recs = sorted(self.bbox)

    def locate(self, lon, lat):
        bi = int(math.floor(lat / self.band))
        for rn in self.recs:
            b = self.bbox[rn]
            if lon < b[0] or lon > b[2] or lat < b[1] or lat > b[3]:
                continue
            inside = False
            for (x1, y1, x2, y2) in self.bands.get((rn, bi), ()):
                if (y1 > lat) != (y2 > lat):
                    if x1 + (lat - y1) * (x2 - x1) / (y2 - y1) > lon:
                        inside = not inside
            if inside:
                return rn
        return None


BIOMAS = {1: 'Amazonia', 2: 'Caatinga', 3: 'Cerrado', 4: 'Mata Atlantica', 5: 'Pampa', 6: 'Pantanal'}
