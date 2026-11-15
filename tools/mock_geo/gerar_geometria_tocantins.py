"""Gera a GEOMETRIA (limites) de Tocantins para o mockup web a partir da malha municipal IBGE 2025 (dados publicos).

So geometria: nenhuma observacao NASA. Saidas (para web/src/mock/geo/):
  tocantins-municipios.json   GeoJSON FeatureCollection simplificado (CD_MUN, NM_MUN)
  tocantins-contorno.json     GeoJSON do contorno do estado (uniao dos municipios, simplificado)
Uso: python tools/mock_geo/gerar_geometria_tocantins.py --ibge <dir com IBGE_2025/municipios> --saida web/src/mock/geo
Fonte: IBGE, Malha Municipal Digital 2025 (BR_Municipios_2025). Atribuicao: IBGE. Ver docs/RESULTADOS_MOCKUP_06A.md.
"""
import argparse
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal.geo import _read_dbf_column  # noqa: E402  (leitura de DBF ja existente no projeto)

ap = argparse.ArgumentParser()
ap.add_argument("--ibge", required=True)
ap.add_argument("--saida", required=True)
ap.add_argument("--tol-mun", type=float, default=0.004)
ap.add_argument("--tol-contorno", type=float, default=0.006)
a = ap.parse_args()
base = os.path.join(a.ibge, "IBGE_2025", "municipios", "BR_Municipios_2025")
cod = _read_dbf_column(base + ".dbf", "CD_MUN")
# the IBGE DBF stores UTF-8; _read_dbf_column decodes as latin1, so recover the real accents of the names
nom = [n.encode("latin1").decode("utf-8") for n in _read_dbf_column(base + ".dbf", "NM_MUN")]
keep = {i + 1 for i, c in enumerate(cod) if c.startswith("17")}
shp = open(base + ".shp", "rb").read()


def dp(pts, tol):
    """Douglas-Peucker em anel aberto (lista de (x,y))."""
    if len(pts) < 4:
        return pts
    keep_ = [False] * len(pts)
    keep_[0] = keep_[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        x1, y1 = pts[i]
        x2, y2 = pts[j]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1e-12
        best, k = 0.0, -1
        for m in range(i + 1, j):
            d = abs(dy * pts[m][0] - dx * pts[m][1] + x2 * y1 - y2 * x1) / n
            if d > best:
                best, k = d, m
        if best > tol:
            keep_[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, f in zip(pts, keep_) if f]


pos, rec, feats, edges = 100, 0, [], {}
while pos < len(shp):
    clen = struct.unpack(">i", shp[pos + 4:pos + 8])[0] * 2
    c = shp[pos + 8:pos + 8 + clen]
    pos += 8 + clen
    rec += 1
    if rec not in keep:
        continue
    npart, npts = struct.unpack("<ii", c[36:44])
    parts = list(struct.unpack("<%di" % npart, c[44:44 + 4 * npart])) + [npts]
    pts = struct.unpack("<%dd" % (2 * npts), c[44 + 4 * npart:44 + 4 * npart + 16 * npts])
    rings = []
    for s, e in zip(parts[:-1], parts[1:]):
        ring = [(round(pts[2 * k], 6), round(pts[2 * k + 1], 6)) for k in range(s, e)]
        for p, q in zip(ring[:-1], ring[1:]):
            key = (p, q) if p <= q else (q, p)
            edges[key] = edges.get(key, 0) + 1
        simp = dp(ring[:-1], a.tol_mun)
        if len(simp) >= 3:
            rings.append([[x, y] for x, y in simp] + [[simp[0][0], simp[0][1]]])
    feats.append({"type": "Feature", "properties": {"cd": cod[rec - 1], "nm": nom[rec - 1]},
                  "geometry": {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}})
os.makedirs(a.saida, exist_ok=True)
with open(os.path.join(a.saida, "tocantins-municipios.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump({"type": "FeatureCollection", "features": feats,
               "attribution": "Geometria: IBGE, Malha Municipal Digital 2025 (simplificada). Nenhuma observacao NASA."}, fh, ensure_ascii=False, separators=(",", ":"))

# contorno: arestas que aparecem uma unica vez (as compartilhadas entre municipios se cancelam)
borda = [k for k, n in edges.items() if n == 1]
adj = {}
for p, q in borda:
    adj.setdefault(p, []).append(q)
    adj.setdefault(q, []).append(p)
visto, aneis = set(), []
for p0 in list(adj):
    if p0 in visto:
        continue
    ring, p, prev = [p0], p0, None
    visto.add(p0)
    while True:
        nxt = [q for q in adj[p] if q != prev and q not in visto]
        if not nxt:
            break
        prev, p = p, nxt[0]
        visto.add(p)
        ring.append(p)
    if len(ring) > 20:
        aneis.append(ring)
aneis.sort(key=len, reverse=True)
principal = dp(aneis[0], a.tol_contorno)
json.dump({"type": "Feature", "properties": {"nm": "Tocantins", "aneis_encontrados": len(aneis)},
           "geometry": {"type": "Polygon", "coordinates": [[[x, y] for x, y in principal] + [[principal[0][0], principal[0][1]]]]},
           "attribution": "Geometria: IBGE, Malha Municipal Digital 2025 (simplificada)."},
          open(os.path.join(a.saida, "tocantins-contorno.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, separators=(",", ":"))
print("municipios:", len(feats), "| aneis de borda:", len(aneis), "| pontos do contorno:", len(principal))
