"""Exportador reproduzivel: SQLite cientifico (Missao 05) -> JSON derivados para o frontend (Missao 06B).

EXPERIMENTAL / NAO VALIDADO. Nao recalcula o metodo: usa firecal.cobertura / firecal.calendario e as saidas da Missao 05
(calendario_diario/semanal/mensal.json) e VERIFICA, dia a dia, que os conjuntos por celula reproduzem os totais diarios.
Somente leitura nos bancos. Nao acessa rede, NASA FIRMS nem Supabase.

Uso:
  python tools/export_web/exportar_web.py --bruto <bruto.db> --resultados <resultados_m05.db> --saidas <saidas_m05> --saida <dir>
Layout da saida (schema 1):
  meta.json                 universo de celulas, fontes (arquivos NASA), resumo por ano, contagens, parametros
  year/YYYY.json           dias (A e B), semanas (com faixa de referencia) e meses do ano
  cells/YYYY-MM.json       por dia: celulas ativas (contagens por satelite, categoria A/B) e cobertura por satelite
  det/YYYY-MM.json         deteccoes individuais (Tocantins) por dia, carregadas sob demanda
  MANIFEST.json            tamanho e SHA-256 de cada arquivo
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import sqlite3
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal import calendario as K  # noqa: E402
from firecal import cobertura as C  # noqa: E402

SCHEMA = 1
ap = argparse.ArgumentParser()
ap.add_argument("--bruto", required=True)
ap.add_argument("--resultados", required=True)
ap.add_argument("--saidas", required=True)
ap.add_argument("--saida", required=True)
a = ap.parse_args()

CLS = {C.COBERTURA_GEOMETRICA_CORROBORADA: 0, C.COBERTURA_GEOMETRICA_PARCIAL: 1, C.COBERTURA_INDETERMINADA: 2,
       C.SEM_COBERTURA_GEOMETRICA_CORROBORADA: 3}
CLS_NAME = ["CORROBORATED", "PARTIAL", "INDETERMINATE", "NO_COVERAGE_CORROBORATED"]
SATS = ("Terra", "Aqua", "N20")
SAT_PUB = {"Terra": "Terra", "Aqua": "Aqua", "N20": "NOAA-20"}
CAT = {"NONE": 0, "BOTH": 1, "MODIS_ONLY": 2, "VIIRS_ONLY": 3, "UNCERTAIN": 4}
ANOS = [2021, 2022, 2023, 2024, 2025]

b = sqlite3.connect(f"file:{a.bruto}?mode=ro", uri=True)
r = sqlite3.connect(f"file:{a.resultados}?mode=ro", uri=True)
diario = json.load(open(os.path.join(a.saidas, "calendario_diario.json"), encoding="utf-8"))
semanal = json.load(open(os.path.join(a.saidas, "calendario_semanal.json"), encoding="utf-8"))
mensal = json.load(open(os.path.join(a.saidas, "calendario_mensal.json"), encoding="utf-8"))
D = {x["dia"]: x for x in diario}
DIAS = sorted(D)
assert len(DIAS) == 1826 and DIAS[0] == "2021-01-01" and DIAS[-1] == "2025-12-31"

universo = [(i, j) for _, i, j in r.execute("select idx, cel_i, cel_j from res_universo_celulas order by idx")]
N = len(universo)
assert N == 433
pos = {c: k for k, c in enumerate(universo)}

# ---- fontes (arquivos NASA/FIRMS importados)
fontes = []
fid = {}
sha12 = {}
for id_, sha, cam, prod, ini, dias, bbox, nbytes, linhas, vers, orig in b.execute(
        "select id, sha256, caminho, produto, inicio, dias, bbox, bytes, linhas, versoes, origem from arquivo_origem order by id"):
    fid[id_] = len(fontes)
    sha12.setdefault(sha[:12], len(fontes))
    fontes.append({"sha256": sha, "file": os.path.basename(cam.replace("\\", "/")), "product": prod, "start": ini, "days": dias,
                   "bbox": bbox, "bytes": nbytes, "rows": linhas, "versions": json.loads(vers)})

# ---- cobertura por satelite-dia (replica tools/historico/calendario.py)
cob = {}
for dia, sat, ng, cg, comp, conf, conf_flag, fb in r.execute(
        "select dia, satelite, n_granulos, contagem_global, catalogo_completo, conflito_n, conflito, f_bytes from res_cobertura_sat_dia"):
    f = [x / 100 for x in fb]
    comp_b = None if comp is None else bool(comp)
    cob[(dia, sat)] = {"f": f, "completo": comp_b, "conflito_n": conf, "ng": ng,
                       "classes": [C.classificar_cobertura(x, comp_b, bool(conf_flag)) for x in f]}

# ---- deteccoes (Tocantins)
det_cel = collections.defaultdict(dict)
for dia, sat, i, j, n in b.execute("select dia_utc, satelite, cel_i, cel_j, count(*) from deteccao where em_regiao=1 group by 1,2,3,4"):
    det_cel[(dia, sat)][(i, j)] = n
horas = collections.defaultdict(list)
versoes = collections.defaultdict(collections.Counter)
for dia, sat, tm, v in b.execute("select dia_utc, satelite, t_min % 1440, versao_bruta from deteccao where em_regiao=1"):
    horas[(dia, sat)].append(tm)
    versoes[(dia, sat)][v] += 1


def estado_dia(classes):
    """Estado de cobertura de um satelite-dia ou familia a partir das classes por celula (regra de APRESENTACAO, conservadora):
    INDETERMINADA se >= 50 % das celulas forem indeterminadas (catalogo incompleto ou conflito); CORROBORADA se >= 95 % das celulas
    forem corroboradas; SEM cobertura corroborada se todas forem 'sem cobertura'; caso contrario PARCIAL. Nao substitui o
    estado dominante do motor (cmr_*_estado_dominante), que continua no calendario diario da Missao 05."""
    n = len(classes)
    cnt = collections.Counter(CLS[x] for x in classes)
    if cnt[2] >= 0.5 * n:
        return "INDETERMINATE"
    if cnt[0] >= C.LIMIAR_CORROBORADA * n:
        return "CORROBORATED"
    if cnt[3] == n:
        return "NO_COVERAGE_CORROBORATED"
    return "PARTIAL"


def hhmm(minutos):
    return f"{int(minutos) // 60:02d}:{int(minutos) % 60:02d}"


def sat_info(dia, s):
    c = cob[(dia, s)]
    dets = sum(det_cel[(dia, s)].values())
    h = horas.get((dia, s))
    ver = versoes[(dia, s)].most_common(1)[0][0] if versoes[(dia, s)] else None
    return {"detections": dets, "passUtc": hhmm(statistics.median(h)) if h else None, "coverageFraction": round(sum(c["f"]) / N, 4),
            "coverageState": estado_dia(c["classes"]), "catalogueComplete": c["completo"], "conflictRecords": c["conflito_n"],
            "productVersion": ver, "granules": c["ng"]}


def familia(dia, sats):
    f = [max(cob[(dia, s)]["f"][k] for s in sats) for k in range(N)]
    cl = [K.classe_familia([cob[(dia, s)]["classes"][k] for s in sats]) for k in range(N)]
    return f, cl


def sensor_block(row, esc, nome, cls_fam, f_fam, ativas_n):
    pre = f"{esc}_{nome}_"
    ext = row[pre + "ext"]
    den = row[pre + "den"]
    o = {"detections": row[f"B_{nome}_det"], "valid": bool(row[pre + "valido"]) if esc == "A" else (den is not None and den > 0),
         "activeCells": ext, "extent": row[pre + "extnorm"], "extentNumerator": ext, "extentDenominator": den,
         "intensity": row[pre + "intens"], "coverageFraction": round(sum(f_fam) / N, 4), "coverageState": estado_dia(cls_fam),
         "excludedDetections": row.get(pre + "det_excluidas", 0) if esc == "A" else 0,
         "unknownCells": row.get(pre + "cel_cobertura_desconhecida", 0) if esc == "B" else 0}
    if not o["valid"]:
        o.update({"activeCells": None, "extent": None, "extentNumerator": None, "intensity": None})
    return o


# ---- referencia por semana/mes (min-max dos anos de referencia, SEMPRE excluindo o ano avaliado; mesma funcao do motor)
def por_ano(tab, chave, campo):
    g = {}
    for x in tab:
        g.setdefault(x[chave], {})[x["ano"]] = x[campo]
    return g


def faixa(tab, chave, x, nome, esc, metrica):
    campo = f"{esc}_{nome}_{metrica}"
    if nome == "modis":
        perm = {y for y in ANOS if K.bloco_do_ano(y) == K.bloco_do_ano(x["ano"])}
        ref = K.valores_referencia(por_ano(tab, chave, campo)[x[chave]], x["ano"], "exclui_ano", perm)
    else:
        ref = K.valores_referencia(por_ano(tab, chave, campo)[x[chave]], x["ano"], "exclui_ano")
    return ref


POS = {"ACIMA_DA_REFERENCIA_DISPONIVEL": "ABOVE", "DENTRO_DA_FAIXA_DA_REFERENCIA": "WITHIN", "ABAIXO_DA_REFERENCIA_DISPONIVEL": "BELOW",
       "REFERENCIA_INSUFICIENTE": "INSUFFICIENT", "SEM_DADO_NO_PERIODO": "NO_DATA"}


def ref_info(x, nome, esc, metrica="extnorm"):
    campo = f"ref_{esc}_{nome}_{metrica}_exclui_ano" + ("_mesmo_bloco" if nome == "modis" else "")
    return {"position": POS[x[campo]], "nReferenceYears": x[f"n_ref_{nome}_exclui_ano"] if nome == "viirs" else None}


# semanas: acrescenta contagem total frente a referencia (somente blocos completos de 7 dias)
for x in semanal:
    for nome in ("modis", "viirs"):
        x[f"B_{nome}_det_total_c"] = x[f"B_{nome}_det_total"] if x["dias"] == 7 else None
for x in semanal:
    for nome in ("modis", "viirs"):
        ref = faixa(semanal, "semana_do_ano", x, nome, "B", "det_total_c")
        x[f"detpos_{nome}"] = POS[K.classificar_vs_referencia(x[f"B_{nome}_det_total_c"], ref)]
        x[f"detref_{nome}"] = [min(ref), max(ref)] if ref else None


def n_ref_modis(tab, chave, x, esc):
    return len(faixa(tab, chave, x, "modis", esc, "extnorm_media"))


def period_block(tab, chave, x):
    o = {"year": x["ano"], chave: x[chave], "days": x["dias"], "modisBlock": x["bloco_modis"]}
    for esc in ("A", "B"):
        sc = {}
        for nome in ("modis", "viirs"):
            ref = faixa(tab, chave, x, nome, esc, "extnorm_media")
            sc[nome] = {"extent": x[f"{esc}_{nome}_extnorm_media"], "intensity": x[f"{esc}_{nome}_intens_media"],
                        "validDays": x[f"{esc}_{nome}_dias_validos"], "detections": x[f"B_{nome}_det_total"],
                        "position": POS[x[f"ref_{esc}_{nome}_extnorm_exclui_ano" + ("_mesmo_bloco" if nome == "modis" else "")]],
                        "nReferenceYears": len(ref), "refMin": min(ref) if ref else None, "refMax": max(ref) if ref else None,
                        "intensityPosition": POS[x[f"ref_{esc}_{nome}_intens_exclui_ano" + ("_mesmo_bloco" if nome == "modis" else "")]]}
            if esc == "B" and chave == "semana_do_ano":
                sc[nome]["detectionsPosition"] = x[f"detpos_{nome}"]
                sc[nome]["detectionsRef"] = x[f"detref_{nome}"]
        o[esc] = sc
    o["conflicts"] = x["conflitos_firms_cmr"]
    o["comparableDaysA"] = x["dias_comparaveis_A"]
    o["comparableDaysB"] = x["dias_comparaveis_B"]
    o["KMeanA"] = x["K_A_media"]
    return o


SEM = {(x["ano"], x["semana_do_ano"]): x for x in semanal}
WHY = {"cobertura comparavel insuficiente": "INSUFFICIENT_COVERAGE", "sem celulas ativas": "NO_ACTIVE_CELLS"}

# ---- dia a dia: conjuntos por celula, categorias, verificacao contra o calendario diario
days_by_year = collections.defaultdict(list)
cells_by_month = collections.defaultdict(dict)
verificacao = {"dias": 0, "celulas_ativas_por_categoria": collections.Counter()}
for dia in DIAS:
    row = D[dia]
    fm, clm = familia(dia, ("Terra", "Aqua"))
    fv, clv = familia(dia, ("N20",))
    dm = collections.Counter()
    for s in ("Terra", "Aqua"):
        dm.update(det_cel[(dia, s)])
    dv = collections.Counter(det_cel[(dia, "N20")])
    am, av = {c for c, n in dm.items() if n > 0}, {c for c, n in dv.items() if n > 0}
    corr_m = {universo[k] for k in range(N) if clm[k] == C.COBERTURA_GEOMETRICA_CORROBORADA}
    corr_v = {universo[k] for k in range(N) if clv[k] == C.COBERTURA_GEOMETRICA_CORROBORADA}
    comp_a = corr_m & corr_v
    comp_b = {universo[k] for k in range(N) if (fm[k] >= C.LIMIAR_CORROBORADA or universo[k] in am) and (fv[k] >= C.LIMIAR_CORROBORADA or universo[k] in av)}
    assert len(am - set(universo)) == 0 and len(av - set(universo)) == 0
    # verificacoes contra o motor (Missao 05)
    assert len(am) == row["B_modis_ext"] and len(av) == row["B_viirs_ext"], dia
    assert sum(dm.values()) == row["B_modis_det"] and sum(dv.values()) == row["B_viirs_det"], dia
    assert row["det_terra"] + row["det_aqua"] == sum(dm.values()) and row["det_n20"] == sum(dv.values()), dia
    for esc, comp in (("A", comp_a), ("B", comp_b)):
        assert len(comp) == row[f"celulas_comparaveis_{esc}"], (dia, esc)
        assert len(am & av & comp) == row[f"ativas_ambos_{esc}"], (dia, esc)
        assert len((am | av) & comp) == row[f"ativas_uniao_{esc}"], (dia, esc)
        if row[f"comparavel_{esc}"]:
            assert len((am & comp) - av) == row[f"so_modis_{esc}"] and len((av & comp) - am) == row[f"so_viirs_{esc}"], (dia, esc)
    # categorias por celula e cenario
    cel_rows = []
    for c in sorted(am | av):
        k = pos[c]
        cats = []
        for comp in (comp_a, comp_b):
            if c in am and c in av:
                cat = "BOTH" if c in comp else "UNCERTAIN"
            elif c in am:
                cat = "MODIS_ONLY" if c in comp else "UNCERTAIN"
            else:
                cat = "VIIRS_ONLY" if c in comp else "UNCERTAIN"
            cats.append(CAT[cat])
        exA = int((c in am and c not in corr_m) or (c in av and c not in corr_v))
        cel_rows.append([k, det_cel[(dia, "Terra")].get(c, 0), det_cel[(dia, "Aqua")].get(c, 0), det_cel[(dia, "N20")].get(c, 0), cats[0], cats[1], exA])
        verificacao["celulas_ativas_por_categoria"][("A", cats[0])] += 1
        verificacao["celulas_ativas_por_categoria"][("B", cats[1])] += 1
    # cobertura por satelite: uniforme -> [classe, f%], senao {c: string de classes, f: percentuais}
    cov = {}
    for s in SATS:
        cl = [CLS[x] for x in cob[(dia, s)]["classes"]]
        ff = [round(x * 100) for x in cob[(dia, s)]["f"]]
        if len(set(cl)) == 1 and len(set(ff)) == 1:
            cov[SAT_PUB[s]] = [cl[0], ff[0]]
        else:
            cov[SAT_PUB[s]] = {"c": "".join(str(x) for x in cl), "f": ff}
    # categoria "sem deteccao mas cobertura incerta" (UNCERTAIN no mapa), por familia
    def fam_codes(cl_names):
        codes = [CLS[x] for x in cl_names]
        return codes[0] if len(set(codes)) == 1 else "".join(str(x) for x in codes)
    # "fam": estado de cobertura por celula da FAMILIA (MODIS = melhor caso entre Terra e Aqua; VIIRS = NOAA-20), uniforme -> inteiro
    cells_by_month[dia[:7]][dia] = {"a": cel_rows, "cov": cov, "fam": [fam_codes(clm), fam_codes(clv)]}
    # registro do dia
    sw = SEM[(row["ano"], row["semana_do_ano"])]
    sats = {SAT_PUB[s]: sat_info(dia, s) for s in SATS}
    sc_out = {}
    for esc in ("A", "B"):
        km = row[f"K_{esc}"]
        sc_out[esc] = {
            "modis": sensor_block(row, esc, "modis", clm, fm, len(am)),
            "viirs": sensor_block(row, esc, "viirs", clv, fv, len(av)),
            "comparison": {"comparable": bool(row[f"comparavel_{esc}"]), "reason": WHY.get(row[f"K_{esc}_motivo_na"]) if row[f"K_{esc}_motivo_na"] else None,
                           "K": km, "Knull": row[f"K_{esc}_nulo"], "both": row[f"ativas_ambos_{esc}"],
                           "onlyModis": row[f"so_modis_{esc}"], "onlyViirs": row[f"so_viirs_{esc}"], "union": row[f"ativas_uniao_{esc}"],
                           "comparableCells": row[f"celulas_comparaveis_{esc}"],
                           "modisConfirmedShare": (row[f"ativas_ambos_{esc}"] / (row[f"ativas_ambos_{esc}"] + row[f"so_modis_{esc}"]))
                           if row[f"comparavel_{esc}"] and (row[f"ativas_ambos_{esc}"] + (row[f"so_modis_{esc}"] or 0)) > 0 else None},
            "referenceModis": {**ref_info(sw, "modis", esc), "nReferenceYears": n_ref_modis(semanal, "semana_do_ano", sw, esc)},
            "referenceViirs": ref_info(sw, "viirs", esc),
        }
    days_by_year[row["ano"]].append({
        "date": dia, "year": row["ano"], "month": row["mes"], "weekOfYear": row["semana_do_ano"], "modisBlock": row["bloco_modis"],
        "modisBlockSource": row["bloco_modis_fonte"], "modisVersion": row["versao_modis"] or None, "viirsVersion": row["versao_viirs"] or None,
        "satellites": sats, "A": sc_out["A"], "B": sc_out["B"], "passOffsetMin": row["dif_hora_mediana_aqua_menos_n20_min"],
        "granuleStartOffsetMin": row["dif_inicio_granulo_aqua_n20_min"],
        "sources": sorted({sha12[s] for s in row["arquivos_origem"].split(";") if s})})
    verificacao["dias"] += 1

# ---- escalas de cor (maximos globais por cenario e sensor) e contagem de dias incertos/excluidos
scale = {}
for esc in ("A", "B"):
    scale[esc] = {"extent": {}, "intensity": {}, "detections": {}}
    for nome, ik in (("modis", "MODIS"), ("viirs", "VIIRS")):
        ex = [x[f"{esc}_{nome}_extnorm"] for x in diario if x[f"{esc}_{nome}_extnorm"] is not None]
        it = [x[f"{esc}_{nome}_intens"] for x in diario if x[f"{esc}_{nome}_intens"] is not None]
        scale[esc]["extent"][ik] = max(ex)
        scale[esc]["intensity"][ik] = max(it)
        scale[esc]["detections"][ik] = max(x[f"B_{nome}_det"] for x in diario)
unc_dias = collections.Counter()
exc_dias = collections.Counter()
for y in ANOS:
    for dd in days_by_year[y]:
        for esc in ("A", "B"):
            for ik, key in (("MODIS", "modis"), ("VIIRS", "viirs")):
                if dd[esc][key]["coverageState"] != "CORROBORATED":
                    unc_dias[(y, esc, ik)] += 1
                if not dd[esc][key]["valid"]:
                    exc_dias[(y, esc, ik)] += 1

# ---- resumo por ano (medianas diarias do motor; nada recalculado alem de mediana)
resumo = {}
for y in ANOS:
    rs = [x for x in diario if x["ano"] == y]
    o = {"detections": {"MODIS": sum(x["B_modis_det"] for x in rs), "VIIRS": sum(x["B_viirs_det"] for x in rs)}}
    for esc in ("A", "B"):
        for nome, ik in (("modis", "MODIS"), ("viirs", "VIIRS")):
            ex = [x[f"{esc}_{nome}_extnorm"] for x in rs if x[f"{esc}_{nome}_extnorm"] is not None]
            it = [x[f"{esc}_{nome}_intens"] for x in rs if x[f"{esc}_{nome}_intens"] is not None]
            o.setdefault(esc, {})[ik] = {"medianExtent": statistics.median(ex) if ex else None, "medianIntensity": statistics.median(it) if it else None,
                                         "validDays": len(ex), "uncertainDays": unc_dias[(y, esc, ik)], "excludedDays": exc_dias[(y, esc, ik)]}
        ks = [x[f"K_{esc}"] for x in rs if x[f"K_{esc}"] is not None]
        o[esc]["comparableDays"] = sum(1 for x in rs if x[f"comparavel_{esc}"])
        o[esc]["kDays"] = len(ks)
        o[esc]["medianK"] = statistics.median(ks) if ks else None
        o[esc]["days"] = len(rs)
    resumo[str(y)] = o

# ---- escrita
os.makedirs(os.path.join(a.saida, "year"), exist_ok=True)
os.makedirs(os.path.join(a.saida, "cells"), exist_ok=True)
os.makedirs(os.path.join(a.saida, "det"), exist_ok=True)


def grava(rel, obj):
    p = os.path.join(a.saida, rel)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)


for y in ANOS:
    grava(f"year/{y}.json", {"schema": SCHEMA, "year": y, "days": days_by_year[y],
                             "weeks": [period_block(semanal, "semana_do_ano", x) for x in semanal if x["ano"] == y],
                             "months": [period_block(mensal, "mes", x) for x in mensal if x["ano"] == y]})
for ym, dd in sorted(cells_by_month.items()):
    grava(f"cells/{ym}.json", {"schema": SCHEMA, "month": ym, "days": dd})

# deteccoes individuais (Tocantins): [celula, satelite(0 Terra,1 Aqua,2 NOAA-20), minuto UTC do dia, lat, lon, FRP, confianca, D/N, scan, track, arquivo, linha]
SATIDX = {"Terra": 0, "Aqua": 1, "N20": 2}
detm = collections.defaultdict(lambda: collections.defaultdict(list))
q = ("select d.dia_utc, d.satelite, d.cel_i, d.cel_j, d.t_min % 1440, d.lat, d.lon, d.frp, d.confianca, d.dia_noite, d.scan, d.track, "
     "(select min(o.arquivo_id) from deteccao_origem o where o.deteccao_id = d.id), "
     "(select o.linha from deteccao_origem o where o.deteccao_id = d.id order by o.arquivo_id limit 1) "
     "from deteccao d where d.em_regiao = 1 order by d.dia_utc, d.satelite, d.t_min, d.lat, d.lon")
ndet = 0
for dia, sat, i, j, tm, la, lo, frp, conf, dn, sc, tr, arq, lin in b.execute(q):
    detm[dia[:7]][dia].append([pos[(i, j)], SATIDX[sat], tm, round(la, 5), round(lo, 5), frp, conf, dn, sc, tr, fid[arq], lin])
    ndet += 1
assert ndet == 602856, ndet
for ym, dd in sorted(detm.items()):
    grava(f"det/{ym}.json", {"schema": SCHEMA, "month": ym, "fields": ["cell", "sat", "minute", "lat", "lon", "frp", "confidence", "dayNight", "scan", "track", "file", "line"],
                              "days": dd})

tot = b.execute("select count(*), sum(em_regiao) from deteccao").fetchone()
meta = {"schema": SCHEMA, "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "EXPERIMENTAL / NAO VALIDADO",
        "range": {"first": DIAS[0], "last": DIAS[-1], "days": len(DIAS)}, "cellSizeDeg": 0.25,
        "cells": [list(c) for c in universo],
        "counts": {"uniqueDetectionsInBbox": tot[0], "detectionsTocantins": tot[1], "sources": len(fontes),
                   "activeCellDays": sum(len(v["a"]) for m in cells_by_month.values() for v in m.values())},
        "sources": fontes, "summary": resumo, "scale": scale,
        "modisVersions": {"A": {"years": [2021, 2022], "version": "6.03"}, "B": {"years": [2023, 2024, 2025], "version": "61.03"}, "viirsVersion": "2"},
        "parameters": {"corroboratedThreshold": C.LIMIAR_CORROBORADA, "catalogueThreshold": C.LIMIAR_CATALOGO, "minFractionScenarioA": K.MIN_FRAC_A,
                       "minFractionK": K.MIN_FRAC_K, "minReferenceYears": K.MIN_REF, "minValidDaysWeek": K.MIN_DIAS_SEMANA},
        "weekDefinition": "fixed 7-day blocks from Jan 1 (week 53 has 1-2 days); NOT ISO weeks"}
grava("meta.json", meta)

man = {}
for root, _, files in os.walk(a.saida):
    for fn in sorted(files):
        if fn == "MANIFEST.json":
            continue
        p = os.path.join(root, fn)
        man[os.path.relpath(p, a.saida).replace("\\", "/")] = {"bytes": os.path.getsize(p), "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()}
with open(os.path.join(a.saida, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(dict(sorted(man.items())), fh, indent=1)
print("ok:", verificacao["dias"], "dias verificados contra calendario_diario;", ndet, "deteccoes;", len(man), "arquivos;", sum(v["bytes"] for v in man.values()), "bytes")
print("celulas ativas (cenario, categoria):", dict(sorted(verificacao["celulas_ativas_por_categoria"].items())))
