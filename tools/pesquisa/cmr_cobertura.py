"""Consulta SOMENTE-LEITURA ao catalogo publico NASA CMR (sem chave, sem transacoes FIRMS) para obter cobertura
CONHECIDA de granulos L2 de deteccao de fogo: MYD14/MOD14 (MODIS 5 min) e VNP14IMG/VJ114IMG/VJ214IMG (VIIRS 6 min).

Subcomandos:
  granulos  <AAAA-MM-DD> <oeste,sul,leste,norte>   lista inicio dos granulos por satelite que tocam a caixa naquele dia
  contagem  <data_ini> <data_fim>                   numero de granulos por dia e satelite (todo o globo)

Nao baixa dados de fogo. Grava nada em disco. Uso: python -I tools/pesquisa/cmr_cobertura.py granulos 2026-07-22 -50.74,-13.47,-45.70,-5.17
"""
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json?"
COLECOES = {"Aqua": "C2278858993-LPCLOUD", "Terra": "C2271754179-LPCLOUD", "SNPP": "C2734202914-LPCLOUD",
            "N20": "C2734197957-LPCLOUD", "N21": "C2831626262-LPCLOUD"}


def _get(params):
    return urllib.request.urlopen(CMR + urllib.parse.urlencode(params), timeout=90)


def granulos(dia, bbox):
    for sat, cid in COLECOES.items():
        r = json.load(_get({"collection_concept_id": cid, "temporal": f"{dia}T00:00:00Z,{dia}T23:59:59Z",
                            "bounding_box": bbox, "page_size": 200}))
        print(sat, dia, [g["time_start"][11:16] for g in r["feed"]["entry"]])


def contagem(ini, fim):
    d, end = dt.date.fromisoformat(ini), dt.date.fromisoformat(fim)
    while d <= end:
        row = []
        for sat, cid in COLECOES.items():
            h = _get({"collection_concept_id": cid, "temporal": f"{d}T00:00:00Z,{d}T23:59:59Z", "page_size": 1})
            row.append(f"{sat}={h.headers.get('CMR-Hits')}")
        print(d, *row)
        d += dt.timedelta(days=1)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "granulos":
        granulos(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[1] == "contagem":
        contagem(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
