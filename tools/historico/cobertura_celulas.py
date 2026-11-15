"""Cobertura por celula e satelite-dia (Missao 05): fracao de AREA coberta pelos granulos CMR, conflitos FIRMS x CMR e estados.

EXPERIMENTAL / NAO VALIDADO. Regras fixas em firecal/cobertura.py (definidas antes de olhar os resultados).
Uso:
  python tools/historico/cobertura_celulas.py --bruto <bruto.db> --resultados <resultados.db> --granulos <json> --ibge <dir>
         --contagem <json global 1> [--contagem <json global 2> ...] [--fios 8]
Grava (no banco de resultados, nunca no bruto): res_cobertura_sat_dia e universo de celulas.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import statistics
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal import cobertura as C  # noqa: E402
from firecal.geo import cell_bounds, cell_center, region_from_ibge_municipios  # noqa: E402

EPOCH = dt.datetime(1970, 1, 1)
TAM = 0.25
G = None
UNIV = None
BRUTO = None


def tmin(s):
    return int((dt.datetime.fromisoformat(s.replace("Z", "")) - EPOCH).total_seconds() // 60)


def iniciar(granulos_json, universo, bruto):
    global G, UNIV, BRUTO
    with open(granulos_json, encoding="utf-8") as fh:
        G = json.load(fh)
    UNIV = universo
    BRUTO = sqlite3.connect(f"file:{bruto}?mode=ro", uri=True)


def tarefa(chave):
    sat, dia = chave
    gl = []
    for g in G.get(f"{sat}|{dia}", []):
        if g.get("poly"):
            gl.append(C.Granulo(tmin(g["t0"]), tmin(g["t1"]), C.parse_poligono(g["poly"]), g.get("dn")))
    f = bytearray()
    for (i, j) in UNIV:
        la0, lo0, la1, lo1 = cell_bounds(TAM, i, j)
        f.append(round(100 * C.fracao_area_celula(gl, la0, lo0, la1, lo1)))
    n = nc = 0
    for t, la, lo in BRUTO.execute("select t_min, lat, lon from deteccao where satelite=? and dia_utc=? and em_regiao=1", (sat, dia)):
        n += 1
        if C.registro_corroborado(gl, t, la, lo):
            nc += 1
    nao_convexos = sum(1 for g in gl if not g.convexo)
    return (sat, dia, len(gl), n, nc, nao_convexos, bytes(f))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bruto", required=True)
    ap.add_argument("--resultados", required=True)
    ap.add_argument("--granulos", required=True)
    ap.add_argument("--ibge", required=True)
    ap.add_argument("--contagem", action="append", required=True)
    ap.add_argument("--fios", type=int, default=8)
    a = ap.parse_args()
    reg = region_from_ibge_municipios(a.ibge, "17", "Tocantins")
    universo_centros = {(i, j) for i, j in reg.cells_overlapping_bbox(TAM) if reg.contains(*reversed(cell_center(TAM, i, j)))}
    bb = sqlite3.connect(f"file:{a.bruto}?mode=ro", uri=True)
    celulas_det = {(i, j) for i, j in bb.execute("select distinct cel_i, cel_j from deteccao where em_regiao=1")}
    bb.close()
    # universo = celulas com centro no territorio + celulas de fronteira que tiveram deteccao no territorio
    universo = sorted(universo_centros | celulas_det)
    print("universo:", len(universo_centros), "centros +", len(universo) - len(universo_centros), "celulas de fronteira com deteccao")
    glob = {}
    for p in a.contagem:
        with open(p, encoding="utf-8") as fh:
            glob.update(json.load(fh))
    med = {s: statistics.median(v for k, v in glob.items() if k.startswith(s + "|") and "2021-01-01" <= k.split("|")[1] <= "2025-12-31" and v is not None)
           for s in ("Aqua", "Terra", "N20")}
    dias = [(dt.date(2021, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(1826)]
    tarefas = [(s, d) for s in ("Aqua", "Terra", "N20") for d in dias]
    r = sqlite3.connect(a.resultados)
    r.executescript("""
    drop table if exists res_universo_celulas; drop table if exists res_cobertura_sat_dia;
    create table res_universo_celulas(idx integer primary key, cel_i integer, cel_j integer);
    create table res_cobertura_sat_dia(dia text, satelite text, n_granulos integer, contagem_global integer, mediana_global real,
      catalogo_completo integer, registros_regiao integer, registros_corroborados integer, conflito_n integer, conflito integer,
      granulos_nao_convexos integer, f_media real, n_celulas integer, n_corroborada integer, n_parcial integer, n_indeterminada integer,
      n_sem_cobertura_corroborada integer, f_bytes blob, primary key(dia, satelite));""")
    r.executemany("insert into res_universo_celulas values(?,?,?)", [(k, i, j) for k, (i, j) in enumerate(universo)])
    with Pool(a.fios, initializer=iniciar, initargs=(a.granulos, universo, a.bruto)) as p:
        for k, (sat, dia, ng, n, nc, nconv, fb) in enumerate(p.imap(tarefa, tarefas, chunksize=20), 1):
            cg = glob.get(f"{sat}|{dia}")
            comp = C.catalogo_completo(cg, med[sat])
            conflito = n - nc
            fs = [b / 100 for b in fb]
            conflito_dia = conflito > 0
            cont = {C.COBERTURA_GEOMETRICA_CORROBORADA: 0, C.COBERTURA_GEOMETRICA_PARCIAL: 0, C.COBERTURA_INDETERMINADA: 0,
                    C.SEM_COBERTURA_GEOMETRICA_CORROBORADA: 0}
            for f in fs:
                cont[C.classificar_cobertura(f, comp, conflito_dia)] += 1
            r.execute("insert into res_cobertura_sat_dia values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (dia, sat, ng, cg, med[sat], None if comp is None else int(comp), n, nc, conflito, int(conflito_dia), nconv,
                       sum(fs) / len(fs), len(fs), cont[C.COBERTURA_GEOMETRICA_CORROBORADA], cont[C.COBERTURA_GEOMETRICA_PARCIAL],
                       cont[C.COBERTURA_INDETERMINADA], cont[C.SEM_COBERTURA_GEOMETRICA_CORROBORADA], fb))
            if k % 1000 == 0:
                r.commit()
                print(k, "de", len(tarefas), flush=True)
    r.commit()
    print("ok", r.execute("select count(*) from res_cobertura_sat_dia").fetchone()[0], "satelite-dias; celulas no universo", len(universo))
