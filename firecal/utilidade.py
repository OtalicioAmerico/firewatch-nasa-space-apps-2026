"""Teste de utilidade do indicador conjunto: o que ele acrescenta a MODIS e VIIRS lado a lado? (mensuravel)

Nao forca resultado positivo: devolve numeros e deixa a conclusao para o relatorio.
"""
from __future__ import annotations

import json

from . import coverage


def _ranks(a):
    order = sorted(range(len(a)), key=lambda i: a[i])
    r = [0.0] * len(a)
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and a[order[j + 1]] == a[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    if len(x) < 3:
        return None
    rx, ry = _ranks(x), _ranks(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = sum((a - mx) ** 2 for a in rx)
    sy = sum((b - my) ** 2 for b in ry)
    return sxy / (sx * sy) ** 0.5 if sx and sy else None


def analyze(daily: list[dict], records, days: list[str], required: dict, ratios=(0.1, 0.25, 0.4, 0.5, 0.6)) -> dict:
    comp = [r for r in daily if r["comparavel"]]
    out = {"n_dias": len(daily), "n_dias_comparaveis": len(comp)}

    # 1) Os dois calendarios de entrada concordam em ordem de dias? (lado a lado)
    out["spearman_I_MODIS_I_VIIRS_comparaveis"] = spearman([r["I_MODIS"] for r in comp], [r["I_VIIRS"] for r in comp])
    out["spearman_A_MODIS_A_VIIRS_todos_os_dias"] = spearman([r["A_MODIS"] for r in daily], [r["A_VIIRS"] for r in daily])

    # 2) O indicador conjunto R tem ordem diferente dos de entrada?
    out["spearman_R_I_MODIS"] = spearman([r["R_conjunto"] for r in comp], [r["I_MODIS"] for r in comp])
    out["spearman_R_I_VIIRS"] = spearman([r["R_conjunto"] for r in comp], [r["I_VIIRS"] for r in comp])
    out["spearman_R_A_UNIAO"] = spearman([r["R_conjunto"] for r in comp], [r["A_UNIAO"] for r in comp])

    # 3) A concordancia espacial K traz informacao que os totais por sensor nao trazem?
    excess = [r["K_jaccard"] - r["K_nulo_deslocado"] for r in daily if r["K_jaccard"] is not None]
    out["K_menos_nulo_por_dia"] = {r["dia"]: (r["K_jaccard"] - r["K_nulo_deslocado"]
                                              if r["K_jaccard"] is not None else None) for r in daily}
    out["K_minimo_maximo"] = (min(r["K_jaccard"] for r in daily), max(r["K_jaccard"] for r in daily))
    out["spearman_K_A_MODIS"] = spearman([r["K_jaccard"] for r in daily], [r["A_MODIS"] for r in daily])
    out["spearman_K_A_VIIRS"] = spearman([r["K_jaccard"] for r in daily], [r["A_VIIRS"] for r in daily])
    out["spearman_K_A_UNIAO"] = spearman([r["K_jaccard"] for r in daily], [r["A_UNIAO"] for r in daily])

    # 4) Efeito da comparabilidade (porta): K e indice MODIS com e sem os dias nao comparaveis
    nc = [r for r in daily if not r["comparavel"]]
    out["dias_nao_comparaveis"] = {r["dia"]: r["motivos_nao_comparavel"] for r in nc}
    if nc:
        med_all = sorted(r["A_MODIS"] for r in daily)[len(daily) // 2]
        out["indice_MODIS_ingenuo_dias_nao_comparaveis"] = {
            r["dia"]: (r["A_MODIS"] / r["ref_mediana_A_MODIS"] if r["ref_mediana_A_MODIS"] else None) for r in nc}
        out["K_dias_nao_comparaveis"] = {r["dia"]: r["K_jaccard"] for r in nc}
        out["K_media_dias_comparaveis"] = sum(r["K_jaccard"] for r in comp) / len(comp)

    # 5) Dispersao dia a dia (CV) do indice de cada sensor e do conjunto, nos dias comparaveis
    def cv(v):
        v = [x for x in v if x is not None]
        m = sum(v) / len(v)
        return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5 / m if len(v) > 1 and m else None
    out["cv_I_MODIS"] = cv([r["I_MODIS"] for r in comp])
    out["cv_I_VIIRS"] = cv([r["I_VIIRS"] for r in comp])
    out["cv_R_conjunto"] = cv([r["R_conjunto"] for r in comp])

    # 6) Entre anos (mediana por ano dos dias comparaveis)
    def med(v):
        v = sorted(v)
        n = len(v)
        return (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2) if v else None
    by = {}
    for y in sorted({r["dia"][:4] for r in comp}):
        rs = [r for r in comp if r["dia"][:4] == y]
        by[y] = {k: med([r[k] for r in rs]) for k in ("A_MODIS", "A_VIIRS", "A_AMBOS", "A_UNIAO", "K_jaccard")}
        by[y]["dias"] = len(rs)
    out["mediana_por_ano_dias_comparaveis"] = by

    # 6b) Calendario de contagens (entrada, por sensor, SEM somar sensores) x calendario de presenca em celulas
    def counts(r):
        n = r["n_deteccoes_por_satelite"]
        n = json.loads(n) if isinstance(n, str) else n
        return n.get("Terra", 0) + n.get("Aqua", 0), sum(v for k, v in n.items() if k not in ("Terra", "Aqua"))
    cm = [counts(r)[0] for r in daily]
    cv_ = [counts(r)[1] for r in daily]
    out["contagem_MODIS_por_dia"] = dict(zip([r["dia"] for r in daily], cm))
    out["contagem_VIIRS_por_dia"] = dict(zip([r["dia"] for r in daily], cv_))
    out["spearman_contagem_vs_presenca_MODIS"] = spearman(cm, [r["A_MODIS"] for r in daily])
    out["spearman_contagem_vs_presenca_VIIRS"] = spearman(cv_, [r["A_VIIRS"] for r in daily])
    chg = {}
    for y in sorted({r["dia"][:4] for r in daily}):
        rs = [r for r in daily if r["dia"][:4] == y and r["comparavel"]]
        chg[y] = {"mediana_contagem_MODIS": med([counts(r)[0] for r in rs]),
                  "mediana_contagem_VIIRS": med([counts(r)[1] for r in rs]),
                  "mediana_celulas_MODIS": med([r["A_MODIS"] for r in rs]),
                  "mediana_celulas_VIIRS": med([r["A_VIIRS"] for r in rs]),
                  "mediana_celulas_UNIAO": med([r["A_UNIAO"] for r in rs]),
                  "mediana_deteccoes_por_celula_ativa_VIIRS": med([counts(r)[1] / r["A_VIIRS"] for r in rs if r["A_VIIRS"]]),
                  "mediana_deteccoes_por_celula_ativa_MODIS": med([counts(r)[0] / r["A_MODIS"] for r in rs if r["A_MODIS"]])}
    out["calendario_contagem_vs_presenca_por_ano"] = chg

    # 7) Sensibilidade da regra de volume
    sats = sorted({s for v in required.values() for s in v})
    sens = {}
    for ratio in ratios:
        st = coverage.sensor_day_status(records, days, sats, ratio, True)
        sens[str(ratio)] = sorted(f"{s}|{d}:{v['status']}" for (s, d), v in st.items() if v["status"] != "OK")
    out["sensibilidade_min_ratio_satdias_sinalizados"] = sens
    return out
