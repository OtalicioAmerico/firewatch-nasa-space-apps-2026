"""Calendario historico real (Missao 05): indicadores por sensor, cenarios A/B, K, referencia historica; saidas CSV/JSON.

EXPERIMENTAL / NAO VALIDADO. Sem indicador combinado R. Sem area queimada. Ausencia de registro nao e ausencia de fogo.
Uso: python tools/historico/calendario.py --bruto <bruto.db> --resultados <resultados_m05.db> --granulos <json> --saida <dir>
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import sqlite3
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal import calendario as K  # noqa: E402
from firecal import cobertura as C  # noqa: E402
from firecal.geo import cell_index  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--bruto", required=True)
ap.add_argument("--resultados", required=True)
ap.add_argument("--granulos", required=True)
ap.add_argument("--saida", required=True)
a = ap.parse_args()
os.makedirs(a.saida, exist_ok=True)
EPOCH = dt.datetime(1970, 1, 1)
b = sqlite3.connect(f"file:{a.bruto}?mode=ro", uri=True)
r = sqlite3.connect(a.resultados)
DIAS = [(dt.date(2021, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(1826)]
SATS = ("Terra", "Aqua", "N20")

universo = [(i, j) for _, i, j in r.execute("select idx, cel_i, cel_j from res_universo_celulas order by idx")]
pos = {c: k for k, c in enumerate(universo)}
N = len(universo)
print("universo", N)

# ---- cobertura por satelite-dia
cob = {}
for dia, sat, ng, cg, med, comp, nreg, ncor, conf, conf_flag, nconv, fb, n_cor, n_par, n_ind, n_sem in r.execute(
        "select dia, satelite, n_granulos, contagem_global, mediana_global, catalogo_completo, registros_regiao, registros_corroborados,"
        " conflito_n, conflito, granulos_nao_convexos, f_bytes, n_corroborada, n_parcial, n_indeterminada, n_sem_cobertura_corroborada"
        " from res_cobertura_sat_dia"):
    f = [x / 100 for x in fb]
    comp_b = None if comp is None else bool(comp)
    dominante = max(((n_cor, C.COBERTURA_GEOMETRICA_CORROBORADA), (n_par, C.COBERTURA_GEOMETRICA_PARCIAL), (n_ind, C.COBERTURA_INDETERMINADA),
                     (n_sem, C.SEM_COBERTURA_GEOMETRICA_CORROBORADA)))[1]
    cob[(dia, sat)] = {"n_cor": n_cor, "n_par": n_par, "n_ind": n_ind, "n_sem": n_sem,
                       "estado": C.CONFLITO_FIRMS_CMR if conf_flag else dominante, "f": f, "ng": ng, "cg": cg, "completo": comp_b, "nreg": nreg, "conflito_n": conf, "conflito": bool(conf_flag),
                       "classes": [C.classificar_cobertura(x, comp_b, bool(conf_flag)) for x in f]}

# ---- deteccoes (Tocantins) por dia, satelite e celula
det = collections.defaultdict(dict)
for dia, sat, i, j, n in b.execute("select dia_utc, satelite, cel_i, cel_j, count(*) from deteccao where em_regiao=1 group by 1,2,3,4"):
    det[(dia, sat)][(i, j)] = n
n20_xy = collections.defaultdict(list)
for dia, la, lo in b.execute("select dia_utc, lat, lon from deteccao where em_regiao=1 and satelite='N20'"):
    n20_xy[dia].append((la, lo))
horas = collections.defaultdict(list)
for dia, sat, tm in b.execute("select dia_utc, satelite, t_min % 1440 from deteccao where em_regiao=1 and dia_noite='D' and satelite in ('Aqua','N20')"):
    horas[(dia, sat)].append(tm)
versoes = collections.defaultdict(collections.Counter)
for dia, sat, v, n in b.execute("select dia_utc, satelite, versao_bruta, count(*) from deteccao where em_regiao=1 group by 1,2,3"):
    versoes[(dia, sat)][v] += n
prov = collections.defaultdict(set)
for dia, sha in b.execute("select distinct d.dia_utc, substr(a.sha256,1,12) from deteccao d join deteccao_origem o on o.deteccao_id=d.id "
                          "join arquivo_origem a on a.id=o.arquivo_id where d.em_regiao=1"):
    prov[dia].add(sha)
gran = json.load(open(a.granulos, encoding="utf-8"))


def tmin(s):
    return int((dt.datetime.fromisoformat(s.replace("Z", "")) - EPOCH).total_seconds() // 60)


def fam_cov(dia, sats):
    """f e classe por celula para a familia (melhor caso entre satelites; f = maximo = limite inferior da uniao)."""
    f = [max(cob[(dia, s)]["f"][k] for s in sats) for k in range(N)]
    cl = [K.classe_familia([cob[(dia, s)]["classes"][k] for s in sats]) for k in range(N)]
    return {universo[k]: f[k] for k in range(N)}, {universo[k]: cl[k] for k in range(N)}


def flat(sat_list, dia):
    d = collections.Counter()
    for s in sat_list:
        d.update(det[(dia, s)])
    return dict(d)


def null_fn_factory(dia):
    def fn(comparaveis, m_ativas):
        vals = []
        comp = set(comparaveis)
        for dla, dlo in ((0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3)):
            v = {cell_index(la + dla, lo + dlo, 0.25) for la, lo in n20_xy[dia]} & comp
            u = m_ativas | v
            vals.append(len(m_ativas & v) / len(u) if u else None)
        vals = [x for x in vals if x is not None]
        return statistics.mean(vals) if vals else None
    return fn


linhas = []
diag = []
for dia in DIAS:
    f_m, cl_m = fam_cov(dia, ("Terra", "Aqua"))
    f_v, cl_v = fam_cov(dia, ("N20",))
    dm, dv = flat(("Terra", "Aqua"), dia), flat(("N20",), dia)
    im = K.indicadores_sensor(universo, dm, f_m, cl_m)
    iv = K.indicadores_sensor(universo, dv, f_v, cl_v)
    # K cenario A: celulas corroboradas para os dois; cenario B: geometria suficiente (>=0,95) ou deteccao da propria familia
    comp_a = im["corroboradas"] & iv["corroboradas"]
    comp_b = {c for c in universo if (f_m[c] >= C.LIMIAR_CORROBORADA or c in im["ativas"]) and (f_v[c] >= C.LIMIAR_CORROBORADA or c in iv["ativas"])}
    ka = K.concordancia(universo, im["ativas"], iv["ativas"], comp_a, null_fn_factory(dia))
    kb = K.concordancia(universo, im["ativas"], iv["ativas"], comp_b, null_fn_factory(dia))
    # indicadores por satelite (inclui Aqua isolado: a cobertura PARCIAL do Aqua fica visivel, ao contrario da familia MODIS = melhor caso)
    ind_sat = {}
    for s_ in SATS:
        f_s, cl_s = fam_cov(dia, (s_,))
        ind_sat[s_] = (K.indicadores_sensor(universo, dict(det[(dia, s_)]), f_s, cl_s), f_s)
    ia, f_aq = ind_sat["Aqua"]
    comp_a_aq = ia["corroboradas"] & iv["corroboradas"]
    comp_b_aq = {c for c in universo if (f_aq[c] >= C.LIMIAR_CORROBORADA or c in ia["ativas"]) and (f_v[c] >= C.LIMIAR_CORROBORADA or c in iv["ativas"])}
    kaq_a = K.concordancia(universo, ia["ativas"], iv["ativas"], comp_a_aq, null_fn_factory(dia))
    kaq_b = K.concordancia(universo, ia["ativas"], iv["ativas"], comp_b_aq, null_fn_factory(dia))
    ver_m = versoes[(dia, "Terra")] + versoes[(dia, "Aqua")]
    bloco = (K.bloco_modis(ver_m.most_common(1)[0][0]), "observado") if ver_m else (("A" if dia < "2023-01-01" else "B"), "inferido_pela_data")
    ha, hn = horas.get((dia, "Aqua")), horas.get((dia, "N20"))
    dif_h = round(statistics.median(ha) - statistics.median(hn)) if ha and hn else None
    ga = [tmin(g["t0"]) for g in gran.get(f"Aqua|{dia}", [])]
    gn = [tmin(g["t0"]) for g in gran.get(f"N20|{dia}", [])]
    dif_g = min(abs(x - y) for x in ga for y in gn) if ga and gn else None
    row = {"dia": dia, "ano": int(dia[:4]), "mes": int(dia[5:7]), "semana_do_ano": K.semana_do_ano(dia),
           "bloco_modis": bloco[0], "bloco_modis_fonte": bloco[1], "versao_modis": "|".join(sorted(ver_m)) or "",
           "versao_viirs": "|".join(sorted(versoes[(dia, "N20")])) or "",
           "det_terra": sum(det[(dia, "Terra")].values()), "det_aqua": sum(det[(dia, "Aqua")].values()), "det_n20": sum(dv.values()),
           "universo_celulas": N, "arquivos_origem": ";".join(sorted(prov[dia]))}
    for nome, ind in (("modis", im), ("viirs", iv)):
        B, A = ind["B"], ind["A"]
        row.update({f"B_{nome}_ext": B["ext_celulas"], f"B_{nome}_det": B["det"], f"B_{nome}_intens": B["intens"],
                    f"B_{nome}_den": B["den_cobertura"], f"B_{nome}_extnorm": B["ext_norm"],
                    f"B_{nome}_cel_cobertura_desconhecida": B["celulas_cobertura_desconhecida"], f"B_{nome}_det_fora_universo": B["det_fora_do_universo"],
                    f"A_{nome}_valido": A["valido"], f"A_{nome}_ext": A["ext_celulas"], f"A_{nome}_det": A["det"],
                    f"A_{nome}_intens": A["intens"], f"A_{nome}_den": A["den_cobertura"], f"A_{nome}_extnorm": A["ext_norm"],
                    f"A_{nome}_det_excluidas": A["det_excluidas"]})
    for s, nm in (("Terra", "terra"), ("Aqua", "aqua"), ("N20", "n20")):
        isat = ind_sat[s][0]
        row.update({f"B_{nm}_ext": isat["B"]["ext_celulas"], f"B_{nm}_den": isat["B"]["den_cobertura"], f"B_{nm}_extnorm": isat["B"]["ext_norm"],
                    f"B_{nm}_intens": isat["B"]["intens"], f"A_{nm}_valido": isat["A"]["valido"], f"A_{nm}_ext": isat["A"]["ext_celulas"],
                    f"A_{nm}_den": isat["A"]["den_cobertura"], f"A_{nm}_extnorm": isat["A"]["ext_norm"]})
        c = cob[(dia, s)]
        row.update({f"cmr_{nm}_granulos": c["ng"], f"cmr_{nm}_catalogo_completo": c["completo"], f"cmr_{nm}_f_media": round(sum(c["f"]) / N, 3),
                    f"cmr_{nm}_conflito_firms_cmr": c["conflito_n"], f"cmr_{nm}_estado_dominante": c["estado"],
                    f"cmr_{nm}_cel_corroboradas": c["n_cor"], f"cmr_{nm}_cel_parciais": c["n_par"], f"cmr_{nm}_cel_indeterminadas": c["n_ind"],
                    f"cmr_{nm}_cel_sem_cobertura_corroborada": c["n_sem"]})
    for esc, kk in (("A", ka), ("B", kb)):
        row.update({f"K_{esc}": kk["K"], f"K_{esc}_nulo": kk.get("K_nulo"), f"comparavel_{esc}": kk["comparavel"],
                    f"celulas_comparaveis_{esc}": kk["celulas_comparaveis"], f"ativas_ambos_{esc}": kk["A_ambos"], f"ativas_uniao_{esc}": kk["A_uniao"],
                    f"so_modis_{esc}": kk["so_modis"] if kk["comparavel"] else None, f"so_viirs_{esc}": kk["so_viirs"] if kk["comparavel"] else None,
                    f"K_{esc}_motivo_na": kk.get("motivo_nao_aplicavel", "")})
        if not kk["comparavel"] and kk["K_diagnostico"] is not None:
            diag.append({"dia": dia, "cenario": esc, "K_diagnostico": kk["K_diagnostico"], "celulas_comparaveis": kk["celulas_comparaveis"],
                         "nota": "DIAGNOSTICO; nao aplicavel; nao usar em saida publica"})
    for esc, kk in (("A", kaq_a), ("B", kaq_b)):
        row.update({f"Kaqua_{esc}": kk["K"], f"Kaqua_{esc}_nulo": kk.get("K_nulo"), f"Kaqua_{esc}_comparavel": kk["comparavel"],
                    f"Kaqua_{esc}_celulas_comparaveis": kk["celulas_comparaveis"], f"Kaqua_{esc}_motivo_na": kk.get("motivo_nao_aplicavel", "")})
        if not kk["comparavel"] and kk["K_diagnostico"] is not None:
            diag.append({"dia": dia, "cenario": esc + "_aqua", "K_diagnostico": kk["K_diagnostico"], "celulas_comparaveis": kk["celulas_comparaveis"],
                         "nota": "DIAGNOSTICO; nao aplicavel; nao usar em saida publica"})
    row.update({"dif_hora_mediana_aqua_menos_n20_min": dif_h, "dif_inicio_granulo_aqua_n20_min": dif_g})
    linhas.append(row)

# ---- agregacoes semanais e mensais + referencia historica (logica em firecal/calendario.py, testada)
ANOS = [2021, 2022, 2023, 2024, 2025]
sem = K.agregar(linhas, lambda x: (x["ano"], x["semana_do_ano"]), ("ano", "semana_do_ano"))
mes = K.agregar(linhas, lambda x: (x["ano"], x["mes"]), ("ano", "mes"))
K.classificar_periodos(sem, "semana_do_ano", ANOS)
K.classificar_periodos(mes, "mes", ANOS)


def grava_csv(nome, tab):
    cols = []
    for x in tab:
        for k in x:
            if k not in cols:
                cols.append(k)
    with open(os.path.join(a.saida, nome), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for x in tab:
            w.writerow({k: ("" if x.get(k) is None else (round(x[k], 5) if isinstance(x.get(k), float) else x.get(k))) for k in cols})


grava_csv("calendario_diario.csv", linhas)
grava_csv("calendario_semanal.csv", sem)
grava_csv("calendario_mensal.csv", mes)
grava_csv("diagnostico_K_dias_nao_comparaveis.csv", diag or [{"dia": "", "cenario": "", "K_diagnostico": "", "celulas_comparaveis": "", "nota": ""}])
with open(os.path.join(a.saida, "calendario_diario.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(linhas, fh, ensure_ascii=False, sort_keys=True, default=str)
with open(os.path.join(a.saida, "calendario_semanal.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(sem, fh, ensure_ascii=False, sort_keys=True, default=str)
with open(os.path.join(a.saida, "calendario_mensal.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(mes, fh, ensure_ascii=False, sort_keys=True, default=str)
print("ok:", len(linhas), "dias;", len(sem), "semanas;", len(mes), "meses;", len(diag), "diagnosticos de K (nao aplicavel)")
