"""Passo 1: inventario dos CSV FIRMS e conferencia SHA-256 contra MANIFESTOS/SHA256SUMS.txt."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import hashlib

sums = {}
for l in open(P('MANIFESTOS/SHA256SUMS.txt'), encoding='utf-8'):
    l = l.rstrip('\n')
    if ' *' in l:
        h, p = l.split(' *', 1)
        sums[p.replace(chr(92), '/').lower()] = h.lower()
files = sorted(glob.glob(os.path.join(R, 'NASA_FIRMS', '**', '*.csv'), recursive=True)
               + glob.glob(os.path.join(R, 'EVIDENCIAS', 'amostras_dimensionamento', '*.csv')))
bad = 0
for f in files:
    rel = os.path.relpath(f, R).replace(os.sep, '/')
    h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
    ok = sums.get(rel.lower()) == h
    if not ok:
        bad += 1
    rows = list(csv.DictReader(open(f, encoding='utf-8')))
    if rows and 'acq_date' not in rows[0]:
        continue
    n = len(rows)
    if n:
        dts = sorted({r['acq_date'] for r in rows})
        sats = collections.Counter(r['satellite'] for r in rows)
        la = [float(r['latitude']) for r in rows]
        lo = [float(r['longitude']) for r in rows]
        print(f"{'OK ' if ok else 'BAD'} {rel[10:]:78s} n={n:6d} {dts[0]}..{dts[-1]} nd={len(dts)} sats={dict(sats)} "
              f"lat[{min(la):.1f},{max(la):.1f}] lon[{min(lo):.1f},{max(lo):.1f}]")
    else:
        print(f"{'OK ' if ok else 'BAD'} {rel[10:]:80s} n=0")
print('files', len(files), 'hash mismatches/not found', bad)
