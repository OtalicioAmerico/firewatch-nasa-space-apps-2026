"""Validacao independente da exportacao (Missao 06B): compara os JSON derivados com o SQLite cientifico e com a Missao 05.

Nao importa o exportador. Le os bancos somente leitura. Saida: JSON com o resultado e codigo de saida != 0 se houver divergencia.
Uso: python tools/export_web/validar_export.py --bruto <bruto.db> --saidas <saidas_m05> --export <web/public/data/real> [--relatorio <arquivo.json>]
"""
import argparse
import collections
import hashlib
import json
import os
import sqlite3
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--bruto", required=True)
ap.add_argument("--saidas", required=True)
ap.add_argument("--export", required=True)
ap.add_argument("--relatorio")
a = ap.parse_args()

b = sqlite3.connect(f"file:{a.bruto}?mode=ro", uri=True)
J = lambda *p: json.load(open(os.path.join(a.export, *p), encoding="utf-8"))
diario = {x["dia"]: x for x in json.load(open(os.path.join(a.saidas, "calendario_diario.json"), encoding="utf-8"))}
meta = J("meta.json")
erros = []
res = {"verificacoes": {}}


def chk(nome, ok, detalhe=""):
    res["verificacoes"][nome] = bool(ok)
    if not ok:
        erros.append(f"{nome}: {detalhe}")


# ---- 1. totais e integridade
tot = b.execute("select count(*), sum(em_regiao), min(dia_utc), max(dia_utc) from deteccao").fetchone()
chk("total_bbox_1154932", tot[0] == 1154932 and meta["counts"]["uniqueDetectionsInBbox"] == 1154932, tot)
chk("total_tocantins_602856", tot[1] == 602856 and meta["counts"]["detectionsTocantins"] == 602856, tot)
chk("periodo", (tot[2], tot[3]) == ("2021-01-01", "2025-12-31"), tot)
chk("universo_433", len(meta["cells"]) == 433)
chk("dias_1826", meta["range"]["days"] == 1826 and len(diario) == 1826)
chk("integridade_sqlite", b.execute("pragma integrity_check").fetchone()[0] == "ok")
chk("manifesto_sha256", all(hashlib.sha256(open(os.path.join(a.export, k), "rb").read()).hexdigest() == v["sha256"] for k, v in J("MANIFEST.json").items()))

# ---- 2. TODOS os dias: contagens por satelite e celula (SQLite) == arquivo de celulas e arquivo de deteccoes
cells = [tuple(c) for c in meta["cells"]]
idx = {c: k for k, c in enumerate(cells)}
bd = collections.defaultdict(lambda: collections.defaultdict(int))
for dia, sat, i, j, n in b.execute("select dia_utc, satelite, cel_i, cel_j, count(*) from deteccao where em_regiao=1 group by 1,2,3,4"):
    bd[dia][(sat, idx[(i, j)])] = n
sat_idx = {"Terra": 1, "Aqua": 2, "N20": 3}
dif_cel = dif_det = dif_dia = 0
total_det_json = 0
for ym in sorted({d[:7] for d in diario}):
    cf = J("cells", f"{ym}.json")["days"]
    df = J("det", f"{ym}.json")["days"]
    for dia in [d for d in diario if d.startswith(ym)]:
        got = {}
        for r in cf[dia]["a"]:
            for sat, col in sat_idx.items():
                if r[col]:
                    got[(sat, r[0])] = r[col]
        if got != dict(bd[dia]):
            dif_cel += 1
        # deteccoes individuais agrupadas por (sat, celula)
        cnt = collections.Counter()
        for r in df.get(dia, []):
            cnt[({0: "Terra", 1: "Aqua", 2: "N20"}[r[1]], r[0])] += 1
        total_det_json += sum(cnt.values())
        if dict(cnt) != dict(bd[dia]):
            dif_det += 1
chk("celulas_vs_sqlite_todos_os_dias", dif_cel == 0, f"{dif_cel} dias divergentes")
chk("deteccoes_vs_sqlite_todos_os_dias", dif_det == 0, f"{dif_det} dias divergentes")
chk("deteccoes_json_total", total_det_json == 602856, total_det_json)

# ---- 3. indicadores diarios: ano JSON == calendario diario da Missao 05
dif_ind = 0
for y in (2021, 2022, 2023, 2024, 2025):
    for d in J("year", f"{y}.json")["days"]:
        m5 = diario[d["date"]]
        for esc in ("A", "B"):
            s = d[esc]
            if s["modis"]["extentNumerator"] != (m5[f"{esc}_modis_ext"] if m5[f"{esc}_modis_valido"] is not False else None) if esc == "A" else False:
                pass
            k = s["comparison"]["K"]
            if (k is None) != (m5[f"K_{esc}"] is None) or (k is not None and abs(k - m5[f"K_{esc}"]) > 1e-12):
                dif_ind += 1
            if s["comparison"]["comparable"] != m5[f"comparavel_{esc}"]:
                dif_ind += 1
            for nome, sk in (("modis", "modis"), ("viirs", "viirs")):
                e = s[sk]["extent"]
                ref = m5[f"{esc}_{nome}_extnorm"]
                if (e is None) != (ref is None) or (e is not None and abs(e - ref) > 1e-12):
                    dif_ind += 1
                if s[sk]["detections"] != m5[f"B_{nome}_det"]:
                    dif_ind += 1
chk("indicadores_vs_missao05_todos_os_dias", dif_ind == 0, f"{dif_ind} divergencias")

# ---- 4. amostras nomeadas (relatorio)
amostras = {
    "baixa_atividade": "2021-02-03",
    "alta_atividade": "2024-09-10",
    "dia_2021": "2021-08-02",
    "dia_2023": "2023-11-22",
    "dia_2025": "2025-08-21",
    "cmr_incompleto_noaa20": "2023-09-30",
    "cmr_incompleto_terra": "2022-10-12",
    "conflito_firms_cmr": "2025-05-14",
}
rel = {}
for nome, dia in amostras.items():
    y = int(dia[:4])
    d = next(x for x in J("year", f"{y}.json")["days"] if x["date"] == dia)
    m5 = diario[dia]
    ym = dia[:7]
    cf = J("cells", f"{ym}.json")["days"][dia]
    sql = {s: b.execute("select count(*) from deteccao where em_regiao=1 and dia_utc=? and satelite=?", (dia, s)).fetchone()[0] for s in ("Terra", "Aqua", "N20")}
    web = {"Terra": d["satellites"]["Terra"]["detections"], "Aqua": d["satellites"]["Aqua"]["detections"], "N20": d["satellites"]["NOAA-20"]["detections"]}
    cell_sum = {s: sum(r[c] for r in cf["a"]) for s, c in sat_idx.items()}
    ok = sql == web == cell_sum and d["B"]["modis"]["detections"] == sql["Terra"] + sql["Aqua"] and d["B"]["viirs"]["detections"] == sql["N20"]
    chk(f"amostra_{nome}", ok, (sql, web, cell_sum))
    rel[nome] = {"dia": dia, "sqlite": sql, "web": web, "celulas": cell_sum,
                 "K_B": d["B"]["comparison"]["K"], "comparavel_B": d["B"]["comparison"]["comparable"], "motivo": d["B"]["comparison"]["reason"],
                 "cobertura": {k: v["coverageState"] for k, v in d["satellites"].items()}}

# ---- 5. categorias de celula: uma celula MODIS-only/VIIRS-only/ambos conferida contra o SQLite
for dia in ("2024-09-10", "2021-08-02", "2025-08-21"):
    cf = J("cells", f"{dia[:7]}.json")["days"][dia]
    got = {"BOTH": None, "MODIS_ONLY": None, "VIIRS_ONLY": None}
    for r in cf["a"]:
        cat = {1: "BOTH", 2: "MODIS_ONLY", 3: "VIIRS_ONLY"}.get(r[5])
        if cat and got[cat] is None:
            got[cat] = r
    for cat, r in got.items():
        if r is None:
            continue
        i, j = cells[r[0]]
        sql = {s: b.execute("select count(*) from deteccao where em_regiao=1 and dia_utc=? and satelite=? and cel_i=? and cel_j=?", (dia, s, i, j)).fetchone()[0] for s in ("Terra", "Aqua", "N20")}
        m, v = sql["Terra"] + sql["Aqua"], sql["N20"]
        ok = (cat == "BOTH" and m > 0 and v > 0) or (cat == "MODIS_ONLY" and m > 0 and v == 0) or (cat == "VIIRS_ONLY" and v > 0 and m == 0)
        chk(f"categoria_{cat}_{dia}", ok, (cat, sql))
        rel.setdefault("celulas", []).append({"dia": dia, "celula": f"g0.25_{i}_{j}", "categoria_B": cat, "sqlite": sql})

# ---- 6. exemplos documentados na Missao 05
w = next(x for x in J("year", "2023.json")["weeks"] if x["semana_do_ano"] == 47)
chk("exemplo_A_modis_2023_s47_det163", w["B"]["modis"]["detections"] == 163 and w["B"]["modis"]["detectionsPosition"] == "BELOW" and w["B"]["modis"]["position"] == "ABOVE", w["B"]["modis"])
w = next(x for x in J("year", "2021.json")["weeks"] if x["semana_do_ano"] == 31)
chk("exemplo_B_viirs_2021_s31", w["B"]["viirs"]["detections"] == 3138 and w["B"]["viirs"]["detectionsPosition"] == "ABOVE" and w["B"]["viirs"]["position"] == "WITHIN", w["B"]["viirs"])
res["amostras"] = rel
res["erros"] = erros
if a.relatorio:
    json.dump(res, open(a.relatorio, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res["verificacoes"].items()}, indent=1))
print("ERROS:", erros if erros else "nenhum")
sys.exit(1 if erros else 0)
