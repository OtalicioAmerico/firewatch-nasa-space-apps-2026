"""Contagem GLOBAL de granulos L2 por dia e satelite no catalogo CMR (evidencia independente de completude do catalogo).
Somente leitura, sem chave. Uso: python -I tools/pesquisa/cmr_contagem_global.py --ini 2021-01-01 --fim 2023-12-31 --saida <json fora do Git>
"""
import argparse, datetime as dt, json, os, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

COL = {"Aqua": "C2278858993-LPCLOUD", "Terra": "C2271754179-LPCLOUD", "N20": "C2734197957-LPCLOUD"}
ap = argparse.ArgumentParser()
ap.add_argument("--ini", required=True); ap.add_argument("--fim", required=True); ap.add_argument("--saida", required=True)
ap.add_argument("--fios", type=int, default=6)
a = ap.parse_args()
dados = json.load(open(a.saida, encoding="utf-8")) if os.path.exists(a.saida) else {}


def hits(sat, dia):
    p = urllib.parse.urlencode({"collection_concept_id": COL[sat], "temporal": f"{dia}T00:00:00Z,{dia}T23:59:59Z", "page_size": 1})
    for k in range(4):
        try:
            return int(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?" + p, timeout=60).headers.get("CMR-Hits"))
        except Exception:                                    # noqa: BLE001
            time.sleep(1 + 2 * k)
    return None


d, fim = dt.date.fromisoformat(a.ini), dt.date.fromisoformat(a.fim)
tar = []
while d <= fim:
    tar += [(s, d.isoformat()) for s in COL if f"{s}|{d}" not in dados]
    d += dt.timedelta(days=1)
print("tarefas", len(tar), flush=True)
with ThreadPoolExecutor(a.fios) as ex:
    for i, ((s, dia), h) in enumerate(zip(tar, ex.map(lambda t: hits(*t), tar)), 1):
        if h is not None:
            dados[f"{s}|{dia}"] = h
        if i % 1000 == 0:
            json.dump(dados, open(a.saida, "w", encoding="utf-8")); print(i, flush=True)
json.dump(dados, open(a.saida, "w", encoding="utf-8"))
print("concluido", len(dados))
