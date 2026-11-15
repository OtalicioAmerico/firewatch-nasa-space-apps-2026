"""Cobertura geometrica CMR x observacoes FIRMS (Missao 04). EXPERIMENTAL / NAO VALIDADO.

Estados por satelite-dia sobre Tocantins (celulas de 0,25 grau, centro dentro da regiao):
  SEM_GRANULO             nenhum granulo L2 do satelite toca a caixa naquele dia (observacao ausente no produto)
  PARCIAL                 granulos cobrem so parte das celulas da regiao (faixa parcial)
  TOTAL                   todas as celulas cobertas geometricamente por algum granulo
Presenca de granulo NAO e ceu limpo: nuvem, fumaça e angulo de visada seguem desconhecidos.

Uso: python tools/historico/cobertura_cmr.py --bruto <bruto.db> --granulos <json> --ibge <dir> --saida <dir>
"""
import argparse
import collections
import datetime as dt
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal.geo import region_from_ibge_municipios, cell_center  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--bruto", required=True)
ap.add_argument("--granulos", required=True)
ap.add_argument("--ibge", required=True)
ap.add_argument("--saida", required=True)
a = ap.parse_args()
EPOCH = dt.datetime(1970, 1, 1)
G = json.load(open(a.granulos, encoding="utf-8"))
b = sqlite3.connect(a.bruto)
reg = region_from_ibge_municipios(a.ibge, "17", "TO")
cells = [(i, j) for i, j in reg.cells_overlapping_bbox(0.25) if reg.contains(*reversed(cell_center(0.25, i, j)))]
centros = [(cell_center(0.25, i, j)[1], cell_center(0.25, i, j)[0]) for i, j in cells]      # (lon, lat)


def tmin(s):
    return int((dt.datetime.fromisoformat(s.replace("Z", "")) - EPOCH).total_seconds() // 60)


def poligono(s):
    v = [float(x) for x in s.split()]
    return [(v[k + 1], v[k]) for k in range(0, len(v), 2)]


def dentro(x, y, pg):
    ins = False
    for (x1, y1), (x2, y2) in zip(pg, pg[1:] + pg[:1]):
        if (y1 > y) != (y2 > y) and x1 + (y - y1) * (x2 - x1) / (y2 - y1) > x:
            ins = not ins
    return ins


# preparar granulos
prep = {}
for k, lst in G.items():
    prep[k] = [{"m0": tmin(g["t0"]), "m1": tmin(g["t1"]), "pg": poligono(g["poly"]), "dn": g["dn"]} for g in lst if g["poly"]]
estado = {}
for k, gs in prep.items():
    if not gs:
        estado[k] = ("SEM_GRANULO", 0.0, 0)
        continue
    cob = sum(1 for (x, y) in centros if any(dentro(x, y, g["pg"]) for g in gs))
    f = cob / len(centros)
    estado[k] = ("TOTAL" if f >= 0.999 else "PARCIAL" if f > 0 else "SEM_GRANULO", round(f, 3), len(gs))

# FIRMS (Tocantins): n por satelite-dia e consistencia registro x granulo
n_sd = collections.Counter()
inc = collections.Counter()
tot = collections.Counter()
for sat, dia, t, lat, lon in b.execute("select satelite, dia_utc, t_min, lat, lon from deteccao where em_regiao=1 and satelite in ('Aqua','Terra','N20')"):
    k = f"{sat}|{dia}"
    n_sd[k] += 1
    tot[sat] += 1
    gs = prep.get(k, [])
    if not any(g["m0"] - 1 <= t <= g["m1"] + 1 and dentro(lon, lat, g["pg"]) for g in gs):
        inc[sat] += 1

res = {"consistencia_registro_granulo_TO": {s: {"registros": tot[s], "sem_granulo_no_tempo_e_poligono": inc[s]} for s in tot}}
dias = sorted({k.split("|")[1] for k in estado})
tab = collections.defaultdict(collections.Counter)
zero = collections.defaultdict(collections.Counter)
com_registro_sem_granulo = collections.defaultdict(list)
mensal = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for k, (est, f, ng) in estado.items():
    sat, dia = k.split("|")
    tab[sat][est] += 1
    mensal[sat][dia[:7]][est] += 1
    if n_sd[k] == 0:
        zero[sat][est] += 1
    elif est == "SEM_GRANULO":
        com_registro_sem_granulo[sat].append(dia)
res["estado_por_satelite"] = {s: dict(v) for s, v in tab.items()}
res["dias_sem_registro_TO_por_estado_cmr"] = {s: dict(v) for s, v in zero.items()}
res["dias_com_registro_mas_SEM_GRANULO"] = {s: v for s, v in com_registro_sem_granulo.items()}
res["lista_sem_granulo"] = {s: sorted(k.split("|")[1] for k, (e, f, n) in estado.items() if k.startswith(s + "|") and e == "SEM_GRANULO") for s in ("Aqua", "Terra", "N20")}
res["lista_parcial"] = {s: sorted((k.split("|")[1], estado[k][1]) for k in estado if k.startswith(s + "|") and estado[k][0] == "PARCIAL") for s in ("Aqua", "Terra", "N20")}
res["mensal_parcial_ou_sem"] = {s: {m: dict(c) for m, c in sorted(mensal[s].items())} for s in mensal}
res["dias_total"] = len(dias)
os.makedirs(a.saida, exist_ok=True)
json.dump(res, open(os.path.join(a.saida, "cobertura_cmr.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print({s: dict(v) for s, v in tab.items()}, res["consistencia_registro_granulo_TO"])
