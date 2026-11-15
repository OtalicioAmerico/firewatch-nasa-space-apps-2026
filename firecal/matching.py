"""Correspondencias CANDIDATAS entre deteccoes MODIS (ex.: Aqua) e VIIRS (ex.: NOAA-20).

Uma candidata e apenas um par (MODIS, VIIRS) com distancia <= raio e diferenca de tempo dentro de uma janela.
Nao e um par validado, nao tem probabilidade de acerto e nao prova que se trate do mesmo evento.
dt = instante MODIS - instante VIIRS (minutos).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from .geo import haversine_m

LABEL = "CANDIDATA"
_GRID = 0.05  # graus; apenas indice espacial interno


@dataclass(frozen=True)
class Candidate:
    modis_rid: str
    viirs_rid: str
    dist_m: float
    dt_min: int
    label: str = LABEL


def find_candidates(modis, viirs, radius_m: float, tmin: int, tmax: int) -> list[Candidate]:
    """Todos os pares com dist <= radius_m e tmin <= dt <= tmax. Ordem deterministica."""
    if radius_m < 0 or tmin > tmax:
        raise ValueError("parametros invalidos")
    if not modis or not viirs:
        return []
    maxlat = max(abs(r.lat) for r in list(modis) + list(viirs))
    cell_m = 111320.0 * _GRID * max(math.cos(math.radians(min(maxlat, 89))), 0.01)
    ring = int(radius_m // cell_m) + 1
    grid = defaultdict(list)
    for v in viirs:
        grid[(math.floor(v.lat / _GRID), math.floor(v.lon / _GRID))].append(v)
    out = []
    for m in modis:
        ci, cj = math.floor(m.lat / _GRID), math.floor(m.lon / _GRID)
        for a in range(-ring, ring + 1):
            for b in range(-ring, ring + 1):
                for v in grid.get((ci + a, cj + b), ()):
                    d = m.t - v.t
                    if tmin <= d <= tmax:
                        dist = haversine_m(m.lat, m.lon, v.lat, v.lon)
                        if dist <= radius_m:
                            out.append(Candidate(m.rid, v.rid, round(dist, 1), d))
    out.sort(key=lambda c: (c.modis_rid, c.viirs_rid))
    return out


def relations(cands: list[Candidate]) -> list[dict]:
    """Componentes conexos do grafo bipartido de candidatas, classificados 1:1, 1:N, N:1 ou M:N.

    1:N = um MODIS com varios VIIRS (esperado: pixel MODIS ~1 km cobre varios pixels VIIRS de 375 m).
    """
    parent: dict = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for c in cands:
        parent[find(("m", c.modis_rid))] = find(("v", c.viirs_rid))
    comps = defaultdict(lambda: {"modis": set(), "viirs": set()})
    for x in list(parent):
        comps[find(x)]["modis" if x[0] == "m" else "viirs"].add(x[1])
    rows = []
    for k, comp in comps.items():
        nm, nv = len(comp["modis"]), len(comp["viirs"])
        tipo = "1:1" if nm == 1 and nv == 1 else "1:N" if nm == 1 else "N:1" if nv == 1 else "M:N"
        rows.append({"tipo": tipo, "n_modis": nm, "n_viirs": nv,
                     "modis": sorted(comp["modis"]), "viirs": sorted(comp["viirs"]), "rotulo": LABEL})
    rows.sort(key=lambda r: (r["modis"][0], r["viirs"][0]))
    return rows


def summarize(modis, cands: list[Candidate]) -> dict:
    """Contagens (sem porcentagem de certeza): MODIS com >= 1 candidato, pares, relacoes."""
    with_c = {c.modis_rid for c in cands}
    rel = relations(cands)
    tipos = {t: sum(1 for r in rel if r["tipo"] == t) for t in ("1:1", "1:N", "N:1", "M:N")}
    return {"n_modis": len(modis), "n_modis_com_candidato": len(with_c),
            "fracao_modis_com_candidato": (len(with_c) / len(modis)) if modis else None,
            "n_pares_candidatos": len(cands), "relacoes": tipos, "rotulo": LABEL}
