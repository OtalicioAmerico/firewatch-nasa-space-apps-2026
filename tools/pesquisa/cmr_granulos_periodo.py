"""Baixa (somente leitura, sem chave e sem transacoes FIRMS) os metadados de granulos L2 do CMR que tocam uma caixa, por dia.

Uso: python -I tools/pesquisa/cmr_granulos_periodo.py --ini 2021-01-01 --fim 2025-12-31 --bbox -51.0,-13.75,-45.5,-4.9 --saida <json fora do Git>
Retomavel: dias ja presentes no arquivo de saida nao sao consultados de novo. Satelites: Aqua, Terra, N20.
"""
import argparse
import datetime as dt
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

COLECOES = {"Aqua": "C2278858993-LPCLOUD", "Terra": "C2271754179-LPCLOUD", "N20": "C2734197957-LPCLOUD"}
ap = argparse.ArgumentParser()
ap.add_argument("--ini", required=True)
ap.add_argument("--fim", required=True)
ap.add_argument("--bbox", required=True)
ap.add_argument("--saida", required=True)
ap.add_argument("--fios", type=int, default=4)
a = ap.parse_args()
dados = json.load(open(a.saida, encoding="utf-8")) if os.path.exists(a.saida) else {}
lock = threading.Lock()


def consulta(sat, dia):
    p = urllib.parse.urlencode({"collection_concept_id": COLECOES[sat], "temporal": f"{dia}T00:00:00Z,{dia}T23:59:59Z",
                                "bounding_box": a.bbox, "page_size": 200})
    for k in range(4):
        try:
            e = json.load(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?" + p, timeout=90))["feed"]["entry"]
            return [{"t0": x["time_start"], "t1": x["time_end"], "dn": x.get("day_night_flag"),
                     "poly": (x.get("polygons") or [[None]])[0][0], "id": x["title"]} for x in e]
        except Exception:                                    # noqa: BLE001
            time.sleep(1 + k * 2)
    return None


d, fim = dt.date.fromisoformat(a.ini), dt.date.fromisoformat(a.fim)
tarefas = []
while d <= fim:
    for s in COLECOES:
        if f"{s}|{d}" not in dados:
            tarefas.append((s, d.isoformat()))
    d += dt.timedelta(days=1)
print("tarefas:", len(tarefas))


def run(t):
    s, dia = t
    r = consulta(s, dia)
    with lock:
        if r is not None:
            dados[f"{s}|{dia}"] = r
    return r is not None


with ThreadPoolExecutor(a.fios) as ex:
    ok = 0
    for i, r in enumerate(ex.map(run, tarefas), 1):
        ok += r
        if i % 500 == 0:
            with lock:
                json.dump(dados, open(a.saida, "w", encoding="utf-8"))
            print(i, "feitas", flush=True)
with lock:
    json.dump(dados, open(a.saida, "w", encoding="utf-8"))
print("concluido:", ok, "de", len(tarefas), "falhas:", len(tarefas) - ok)
