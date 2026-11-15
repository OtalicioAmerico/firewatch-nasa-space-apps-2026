"""Resumos numericos da Missao 05 a partir das saidas do calendario (somente leitura). EXPERIMENTAL / NAO VALIDADO.

Uso: python tools/historico/analise_m05.py --saidas <dir> --resultados <resultados_m05.db> --bruto <bruto.db>
"""
import argparse
import collections
import csv
import json
import os
import sqlite3
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal.utilidade import spearman  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--saidas", required=True)
ap.add_argument("--resultados", required=True)
ap.add_argument("--bruto", required=True)
a = ap.parse_args()


def ler(nome):
    with open(os.path.join(a.saidas, nome), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fl(x):
    return None if x in ("", None) else float(x)


D = ler("calendario_diario.csv")
S = ler("calendario_semanal.csv")
M = ler("calendario_mensal.csv")
r = sqlite3.connect(a.resultados)
b = sqlite3.connect(f"file:{a.bruto}?mode=ro", uri=True)
out = {}

# 1. totais
out["totais"] = {"deteccoes": b.execute("select count(*) from deteccao").fetchone()[0],
                 "em_tocantins": b.execute("select count(*) from deteccao where em_regiao=1").fetchone()[0],
                 "celula_dia_satelite": b.execute("select count(*) from (select 1 from deteccao where em_regiao=1 group by dia_utc,satelite,cel_i,cel_j)").fetchone()[0],
                 "celula_dia_modis": b.execute("select count(*) from (select 1 from deteccao where em_regiao=1 and satelite in ('Terra','Aqua') group by dia_utc,cel_i,cel_j)").fetchone()[0],
                 "celula_dia_viirs": b.execute("select count(*) from (select 1 from deteccao where em_regiao=1 and satelite='N20' group by dia_utc,cel_i,cel_j)").fetchone()[0],
                 "dias": len(D), "semanas": len(S), "meses": len(M),
                 "universo_celulas": int(D[0]["universo_celulas"])}

# 2. indicadores por sensor e ano (medianas diarias)
ind = {}
for esc in ("A", "B"):
    for nome in ("modis", "viirs"):
        for y in range(2021, 2026):
            xs = [x for x in D if int(x["ano"]) == y]
            en = [fl(x[f"{esc}_{nome}_extnorm"]) for x in xs if fl(x[f"{esc}_{nome}_extnorm"]) is not None]
            it = [fl(x[f"{esc}_{nome}_intens"]) for x in xs if fl(x[f"{esc}_{nome}_intens"]) is not None]
            ex = [fl(x[f"{esc}_{nome}_ext"]) for x in xs if fl(x[f"{esc}_{nome}_ext"]) is not None]
            ind[f"{esc}|{nome}|{y}"] = {"dias_validos": len(en), "ext_celulas_mediana": statistics.median(ex) if ex else None,
                                        "extnorm_mediana": round(statistics.median(en), 4) if en else None,
                                        "intens_mediana": round(statistics.median(it), 3) if it else None}
out["indicadores_ano"] = ind

# 4. cobertura / inconsistencias
cob = {}
for s in ("Aqua", "Terra", "N20"):
    q = r.execute("select count(*), sum(catalogo_completo=0), sum(conflito), sum(conflito_n), sum(registros_regiao), sum(n_corroborada), sum(n_parcial),"
                  " sum(n_indeterminada), sum(n_sem_cobertura_corroborada), avg(f_media) from res_cobertura_sat_dia where satelite=?", (s,)).fetchone()
    cob[s] = dict(zip(("sat_dias", "catalogo_incompleto_dias", "conflito_dias", "registros_em_conflito", "registros_tocantins", "celulas_dia_corroborada",
                       "celulas_dia_parcial", "celulas_dia_indeterminada", "celulas_dia_sem_cobertura_corroborada", "f_media"), q))
    cob[s]["dias_com_alguma_celula_parcial"] = r.execute("select count(*) from res_cobertura_sat_dia where satelite=? and n_parcial>0", (s,)).fetchone()[0]
    cob[s]["dias_cobertura_media_inferior_95"] = r.execute("select count(*) from res_cobertura_sat_dia where satelite=? and f_media<0.95", (s,)).fetchone()[0]
out["cobertura"] = cob
out["cenario_A_dias_validos"] = {nome: sum(1 for x in D if x[f"A_{nome}_valido"] == "True") for nome in ("modis", "viirs")}
out["cenario_A_dias_excluidos_com_deteccoes"] = {nome: sum(1 for x in D if x[f"A_{nome}_valido"] != "True" and int(x[f"B_{nome}_det"] or 0) > 0) for nome in ("modis", "viirs")}
out["cenario_A_deteccoes_excluidas"] = {nome: sum(int(x[f"A_{nome}_det_excluidas"] or 0) for x in D) for nome in ("modis", "viirs")}
out["cenario_B_deteccoes_totais_modis_viirs"] = {nome: sum(int(x[f"B_{nome}_det"] or 0) for x in D) for nome in ("modis", "viirs")}
out["det_fora_universo"] = {nome: sum(int(x[f"B_{nome}_det_fora_universo"] or 0) for x in D) for nome in ("modis", "viirs")}

# normalizacao: ranking cru x normalizado
for nome, cols in (("modis", ("det_terra", "det_aqua")), ("viirs", ("det_n20",))):
    cru = [sum(int(x[c]) for c in cols) for x in D]
    ext = [fl(x[f"B_{nome}_ext"]) for x in D]
    en = [fl(x[f"B_{nome}_extnorm"]) or 0.0 for x in D]
    out[f"spearman_{nome}_contagem_x_extensao_B"] = spearman(cru, ext)
    out[f"spearman_{nome}_contagem_x_extnorm_B"] = spearman(cru, en)
    out[f"spearman_{nome}_extensao_x_extnorm_B"] = spearman(ext, en)
# efeito da normalizacao quando o Aqua cobre parcialmente
parc = [x for x in D if fl(x["cmr_aqua_f_media"]) is not None and fl(x["cmr_aqua_f_media"]) < 0.95 and fl(x["cmr_terra_f_media"]) is not None and fl(x["cmr_terra_f_media"]) >= 0.95]
out["dias_aqua_f_media_lt_95"] = sum(1 for x in D if fl(x["cmr_aqua_f_media"]) < 0.95)
out["dias_aqua_f_media_lt_50"] = sum(1 for x in D if fl(x["cmr_aqua_f_media"]) < 0.5)

# 6. blocos MODIS: mesmos meses (jul-out), mediana de extnorm_B, intensidade, razao MODIS/VIIRS
bl = {}
for blk, anos in (("A_6.03", (2021, 2022)), ("B_61.03", (2023, 2024, 2025))):
    for tri, ms in (("jun-out", (6, 7, 8, 9, 10)), ("mai-jun", (5, 6)), ("todos", tuple(range(1, 13)))):
        xs = [x for x in D if int(x["ano"]) in anos and int(x["mes"]) in ms]
        def med(c):
            v = [fl(x[c]) for x in xs if fl(x[c]) is not None]
            return round(statistics.median(v), 4) if v else None
        raz = [fl(x["B_modis_ext"]) / fl(x["B_viirs_ext"]) for x in xs if fl(x["B_viirs_ext"]) and fl(x["B_viirs_ext"]) > 0]
        bl[f"{blk}|{tri}"] = {"dias": len(xs), "modis_extnorm_B": med("B_modis_extnorm"), "modis_intens_B": med("B_modis_intens"),
                              "viirs_extnorm_B": med("B_viirs_extnorm"), "viirs_intens_B": med("B_viirs_intens"),
                              "razao_ext_modis_viirs_mediana": round(statistics.median(raz), 3) if raz else None}
out["blocos_modis"] = bl
por_ano_mes = {}
for y in range(2021, 2026):
    xs = [x for x in D if int(x["ano"]) == y and 6 <= int(x["mes"]) <= 10]
    raz = [fl(x["B_modis_ext"]) / fl(x["B_viirs_ext"]) for x in xs if fl(x["B_viirs_ext"]) and fl(x["B_viirs_ext"]) > 0]
    por_ano_mes[y] = round(statistics.median(raz), 3)
out["razao_ext_modis_viirs_jun_out_por_ano"] = por_ano_mes

# 7. concordancia
kk = {}
for esc in ("A", "B"):
    for y in range(2021, 2026):
        xs = [x for x in D if int(x["ano"]) == y]
        comp = [x for x in xs if x[f"comparavel_{esc}"] == "True"]
        ks = [fl(x[f"K_{esc}"]) for x in comp if fl(x[f"K_{esc}"]) is not None]
        kn = [fl(x[f"K_{esc}_nulo"]) for x in comp if fl(x[f"K_{esc}_nulo"]) is not None]
        kk[f"{esc}|{y}"] = {"dias": len(xs), "dias_comparaveis": len(comp), "dias_K_calculado": len(ks),
                            "K_mediana": round(statistics.median(ks), 3) if ks else None, "K_nulo_mediana": round(statistics.median(kn), 3) if kn else None,
                            "K_q25": round(sorted(ks)[len(ks) // 4], 3) if ks else None, "K_q75": round(sorted(ks)[3 * len(ks) // 4], 3) if ks else None}
out["concordancia"] = kk
out["comparaveis_total"] = {esc: sum(1 for x in D if x[f"comparavel_{esc}"] == "True") for esc in ("A", "B")}
out["K_nao_aplicavel_dias"] = {esc: sum(1 for x in D if x[f"K_{esc}"] == "") for esc in ("A", "B")}
out["motivos_NA_A"] = dict(collections.Counter(x["K_A_motivo_na"] for x in D if x["K_A"] == ""))
out["motivos_NA_B"] = dict(collections.Counter(x["K_B_motivo_na"] for x in D if x["K_B"] == ""))
ambos = [x for x in D if x["K_A"] != "" and x["K_B"] != ""]
out["K_A_vs_B_dias_em_comum"] = {"n": len(ambos), "spearman": spearman([fl(x["K_A"]) for x in ambos], [fl(x["K_B"]) for x in ambos]) if len(ambos) > 3 else None,
                                 "dif_media_abs": round(statistics.mean(abs(fl(x["K_A"]) - fl(x["K_B"])) for x in ambos), 4) if ambos else None}
# K versus defasagem de horario (Aqua - N20)
for esc in ("B",):
    pares = [(fl(x["dif_hora_mediana_aqua_menos_n20_min"]), fl(x[f"K_{esc}"])) for x in D if x[f"K_{esc}"] != "" and x["dif_hora_mediana_aqua_menos_n20_min"] != ""]
    out[f"K_{esc}_vs_defasagem_hora_spearman"] = {"n": len(pares), "rho": spearman([p[0] for p in pares], [p[1] for p in pares]) if len(pares) > 3 else None}
    faixa = collections.defaultdict(list)
    for dh, k in pares:
        faixa["<=30 min" if abs(dh) <= 30 else "30-90 min" if abs(dh) <= 90 else ">90 min"].append(k)
    out[f"K_{esc}_por_faixa_defasagem"] = {k: {"n": len(v), "K_mediana": round(statistics.median(v), 3)} for k, v in faixa.items()}

# 8. semanas/meses distintos (referencia que exclui o ano avaliado)
def cont_class(tab, ano=None, prefixo=""):
    c = collections.Counter()
    for x in tab:
        if ano and int(x["ano"]) != ano:
            continue
        for k, v in x.items():
            if k.startswith(prefixo) and "extnorm" in k:
                c[(k, v)] += 1
    return c
campos_pub = ["ref_B_modis_extnorm_exclui_ano_mesmo_bloco", "ref_B_viirs_extnorm_exclui_ano", "ref_A_modis_extnorm_exclui_ano_mesmo_bloco", "ref_A_viirs_extnorm_exclui_ano",
              "ref_B_modis_extnorm_anteriores_mesmo_bloco", "ref_B_viirs_extnorm_anteriores", "ref_B_modis_intens_exclui_ano_mesmo_bloco", "ref_B_viirs_intens_exclui_ano"]
cls = {}
for campo in campos_pub:
    for y in range(2021, 2026):
        c = collections.Counter(x[campo] for x in S if int(x["ano"]) == y)
        cls[f"{campo}|{y}"] = dict(c)
out["classificacao_semanal"] = cls
out["semanas_destaque"] = []
for x in S:
    if int(x["dias"]) >= 4 and x["ref_B_viirs_extnorm_exclui_ano"] == "ACIMA_DA_REFERENCIA_DISPONIVEL" and x["ref_B_modis_extnorm_exclui_ano_mesmo_bloco"] == "ACIMA_DA_REFERENCIA_DISPONIVEL":
        out["semanas_destaque"].append(("ambos_acima", int(x["ano"]), int(x["semana_do_ano"]), x["B_modis_extnorm_media"], x["B_viirs_extnorm_media"]))
    if x["ref_B_viirs_extnorm_exclui_ano"] == "ABAIXO_DA_REFERENCIA_DISPONIVEL" and x["ref_B_modis_extnorm_exclui_ano_mesmo_bloco"] == "ABAIXO_DA_REFERENCIA_DISPONIVEL":
        out["semanas_destaque"].append(("ambos_abaixo", int(x["ano"]), int(x["semana_do_ano"]), x["B_modis_extnorm_media"], x["B_viirs_extnorm_media"]))
    if {x["ref_B_viirs_extnorm_exclui_ano"], x["ref_B_modis_extnorm_exclui_ano_mesmo_bloco"]} == {"ACIMA_DA_REFERENCIA_DISPONIVEL", "ABAIXO_DA_REFERENCIA_DISPONIVEL"}:
        out["semanas_destaque"].append(("divergem", int(x["ano"]), int(x["semana_do_ano"]), x["B_modis_extnorm_media"], x["B_viirs_extnorm_media"]))
out["semanas_destaque_resumo"] = {f"{k[0]}|{k[1]}": v for k, v in collections.Counter((t[0], t[1]) for t in out["semanas_destaque"]).items()}
cm = {}
for campo in ("ref_B_modis_extnorm_exclui_ano_mesmo_bloco", "ref_B_viirs_extnorm_exclui_ano"):
    for y in range(2021, 2026):
        cm[f"{campo}|{y}"] = [(int(x["mes"]), x[campo]) for x in M if int(x["ano"]) == y]
out["classificacao_mensal"] = cm

# 9. ganho da harmonizacao: contagem bruta x extensao x K
# (i) semanas em que a classificacao pela contagem bruta difere da classificada pela extensao normalizada
def cls_semana(chave_valor):
    por = collections.defaultdict(dict)
    for x in S:
        v = chave_valor(x)
        por[int(x["semana_do_ano"])][int(x["ano"])] = v
    res = {}
    for x in S:
        y, w = int(x["ano"]), int(x["semana_do_ano"])
        res[(y, w)] = None
    return por
def classificar_tab(valfn, bloco):
    por = collections.defaultdict(dict)
    for x in S:
        if int(x["dias"]) >= 4:
            por[int(x["semana_do_ano"])][int(x["ano"])] = valfn(x)
    out_ = {}
    for x in S:
        y, w = int(x["ano"]), int(x["semana_do_ano"])
        ref = [v for yy, v in por[w].items() if yy != y and (not bloco or ((yy <= 2022) == (y <= 2022)))]
        v = por[w].get(y)
        out_[(y, w)] = None if v is None else ("REF_INSUF" if len(ref) < 2 else "ACIMA" if v > max(ref) else "ABAIXO" if v < min(ref) else "DENTRO")
    return out_
raw_m = classificar_tab(lambda x: float(x["det_terra"]) + float(x["det_aqua"]), True)
ext_m = classificar_tab(lambda x: fl(x["B_modis_extnorm_media"]) if fl(x["B_modis_extnorm_media"]) is not None else 0.0, True)
raw_v = classificar_tab(lambda x: float(x["det_n20"]), False)
ext_v = classificar_tab(lambda x: fl(x["B_viirs_extnorm_media"]) if fl(x["B_viirs_extnorm_media"]) is not None else 0.0, False)
for nome, rw, ex in (("modis", raw_m, ext_m), ("viirs", raw_v, ext_v)):
    validos = [k for k in rw if rw[k] not in (None, "REF_INSUF") and ex[k] not in (None, "REF_INSUF")]
    dif = [k for k in validos if rw[k] != ex[k]]
    out[f"semanas_classificacao_contagem_vs_extensao_{nome}"] = {"semanas_comparadas": len(validos), "classificacao_diferente": len(dif),
                                                                  "exemplos": [(k[0], k[1], rw[k], ex[k]) for k in sorted(dif)[:12]]}
# (ii) dias em que a contagem bruta MODIS e a extensao normalizada discordam em tercil, com cobertura parcial do Aqua
ordem_raw = sorted(range(len(D)), key=lambda i: int(D[i]["det_terra"]) + int(D[i]["det_aqua"]))
rank_raw = {i: k for k, i in enumerate(ordem_raw)}
vals = [fl(x["B_modis_extnorm"]) or 0.0 for x in D]
ordem_ext = sorted(range(len(D)), key=lambda i: vals[i])
rank_ext = {i: k for k, i in enumerate(ordem_ext)}
ex = sorted(range(len(D)), key=lambda i: -abs(rank_raw[i] - rank_ext[i]))[:10]
out["dias_maior_mudanca_de_posicao_modis_contagem_vs_extnorm"] = [
    {"dia": D[i]["dia"], "det_modis": int(D[i]["det_terra"]) + int(D[i]["det_aqua"]), "rank_contagem_pct": round(100 * rank_raw[i] / len(D)),
     "rank_extnorm_pct": round(100 * rank_ext[i] / len(D)), "aqua_f_media": D[i]["cmr_aqua_f_media"], "terra_f_media": D[i]["cmr_terra_f_media"],
     "B_modis_ext": D[i]["B_modis_ext"], "B_modis_den": D[i]["B_modis_den"]} for i in ex]
# (iii) K: dias em que contagens de MODIS e VIIRS estao altas mas K e baixo/NA
cm_q = statistics.quantiles([int(x["det_terra"]) + int(x["det_aqua"]) for x in D], n=4)
cv_q = statistics.quantiles([int(x["det_n20"]) for x in D], n=4)
alto = [x for x in D if int(x["det_terra"]) + int(x["det_aqua"]) >= cm_q[2] and int(x["det_n20"]) >= cv_q[2]]
out["dias_ambos_com_contagem_alta"] = {"n": len(alto), "K_B_nao_aplicavel": sum(1 for x in alto if x["K_B"] == ""), "K_A_nao_aplicavel": sum(1 for x in alto if x["K_A"] == ""),
                                       "K_B_mediana": round(statistics.median([fl(x["K_B"]) for x in alto if x["K_B"] != ""]), 3) if any(x["K_B"] != "" for x in alto) else None}
altoK = {}
for y in range(2021, 2026):
    xs = [x for x in alto if int(x["ano"]) == y and x["K_B"] != ""]
    altoK[y] = {"n": len(xs), "K_B_mediana": round(statistics.median([fl(x["K_B"]) for x in xs]), 3) if xs else None}
out["dias_contagem_alta_K_por_ano"] = altoK
out["spearman_K_B_vs_extnorm_modis"] = spearman([fl(x["K_B"]) for x in D if x["K_B"] != ""], [fl(x["B_modis_extnorm"]) or 0 for x in D if x["K_B"] != ""])
out["spearman_K_B_vs_extnorm_viirs"] = spearman([fl(x["K_B"]) for x in D if x["K_B"] != ""], [fl(x["B_viirs_extnorm"]) or 0 for x in D if x["K_B"] != ""])
out["spearman_modis_extnorm_vs_viirs_extnorm_B"] = spearman([fl(x["B_modis_extnorm"]) or 0 for x in D], [fl(x["B_viirs_extnorm"]) or 0 for x in D])
out["spearman_modis_contagem_vs_viirs_contagem"] = spearman([int(x["det_terra"]) + int(x["det_aqua"]) for x in D], [int(x["det_n20"]) for x in D])

# 10. Aqua isolado: efeito da normalizacao por cobertura e K Aqua x NOAA-20
parc = [x for x in D if fl(x["cmr_aqua_f_media"]) is not None and fl(x["cmr_aqua_f_media"]) < 0.95]
efeito = []
for x in parc:
    ext, den = fl(x["B_aqua_ext"]), fl(x["B_aqua_den"])
    if den and den > 0:
        efeito.append((ext / 433.0, ext / den, fl(x["cmr_aqua_f_media"])))   # extensao sobre universo inteiro x sobre cobertura efetiva
out["aqua_dias_cobertura_parcial"] = {"n": len(parc), "extnorm_sobre_universo_mediana": round(statistics.median(e[0] for e in efeito), 4) if efeito else None,
                                      "extnorm_sobre_cobertura_efetiva_mediana": round(statistics.median(e[1] for e in efeito), 4) if efeito else None,
                                      "razao_mediana_efetiva_sobre_universo": round(statistics.median(e[1] / e[0] for e in efeito if e[0] > 0), 3) if efeito else None,
                                      "f_media_mediana": round(statistics.median(e[2] for e in efeito), 3) if efeito else None}
tot = [x for x in D if fl(x["cmr_aqua_f_media"]) is not None and fl(x["cmr_aqua_f_media"]) >= 0.95]
out["aqua_dias_cobertura_total_extnorm_mediana"] = round(statistics.median([fl(x["B_aqua_extnorm"]) for x in tot if fl(x["B_aqua_extnorm"]) is not None]), 4)
out["aqua_dias_parcial_extnorm_B_mediana"] = round(statistics.median([fl(x["B_aqua_extnorm"]) for x in parc if fl(x["B_aqua_extnorm"]) is not None]), 4)
out["aqua_dias_parcial_ext_mediana"] = statistics.median([fl(x["B_aqua_ext"]) for x in parc])
out["aqua_dias_total_ext_mediana"] = statistics.median([fl(x["B_aqua_ext"]) for x in tot])
out["aqua_A_valido"] = sum(1 for x in D if x["A_aqua_valido"] == "True")
kq = {}
for esc in ("A", "B"):
    for y in range(2021, 2026):
        xs = [x for x in D if int(x["ano"]) == y]
        comp = [x for x in xs if x[f"Kaqua_{esc}_comparavel"] == "True"]
        ks = [fl(x[f"Kaqua_{esc}"]) for x in comp if fl(x[f"Kaqua_{esc}"]) is not None]
        kn = [fl(x[f"Kaqua_{esc}_nulo"]) for x in comp if fl(x[f"Kaqua_{esc}_nulo"]) is not None]
        kq[f"{esc}|{y}"] = {"dias_comparaveis": len(comp), "dias_K": len(ks), "K_mediana": round(statistics.median(ks), 3) if ks else None,
                            "K_nulo_mediana": round(statistics.median(kn), 3) if kn else None}
out["concordancia_aqua_n20"] = kq
out["aqua_K_motivos_NA_B"] = dict(collections.Counter(x["Kaqua_B_motivo_na"] for x in D if x["Kaqua_B"] == ""))
pares = [(fl(x["dif_hora_mediana_aqua_menos_n20_min"]), fl(x["Kaqua_B"])) for x in D if x["Kaqua_B"] != "" and x["dif_hora_mediana_aqua_menos_n20_min"] != ""]
out["Kaqua_B_vs_defasagem_spearman"] = {"n": len(pares), "rho": spearman([p[0] for p in pares], [p[1] for p in pares]) if len(pares) > 3 else None}
fx = collections.defaultdict(list)
for dh, k in pares:
    fx["|dif|<=30min" if abs(dh) <= 30 else "30-90min" if abs(dh) <= 90 else ">90min"].append(k)
out["Kaqua_B_por_faixa_defasagem"] = {k: {"n": len(v), "K_mediana": round(statistics.median(v), 3)} for k, v in fx.items()}
# defasagem de hora por ano (mediana dos dias)
dh_ano = {}
for y in range(2021, 2026):
    v = [fl(x["dif_hora_mediana_aqua_menos_n20_min"]) for x in D if int(x["ano"]) == y and x["dif_hora_mediana_aqua_menos_n20_min"] != ""]
    dh_ano[y] = {"n": len(v), "mediana_min": statistics.median(v)}
out["defasagem_hora_aqua_menos_n20_por_ano"] = dh_ano
with open(os.path.join(a.saidas, "analise_m05.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
print("ok", len(out), "blocos de resultado")
