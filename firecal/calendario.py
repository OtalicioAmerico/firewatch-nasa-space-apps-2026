"""Indicadores diarios por sensor, cenarios de cobertura A/B, concordancia K e referencia historica (Missao 05).

EXPERIMENTAL / NAO VALIDADO. Nada aqui e area queimada, numero de incendios ou probabilidade. Nao existe indicador combinado R.
Regras (fixadas antes de olhar os resultados): ver constantes abaixo e firecal/cobertura.py.

Grandezas por sensor (familia) e dia, dentro do territorio (universo de celulas de 0,25 grau):
  ext_celulas        numero de celulas com >= 1 deteccao registrada
  det                numero de deteccoes registradas (nas celulas consideradas pelo cenario)
  intens             det / ext_celulas (deteccoes por celula ativa)
  ext_norm           ext_celulas / denominador de cobertura (numerador e denominador sao guardados):
       cenario A (conservador): denominador = celulas com cobertura geometrica CORROBORADA; so celulas corroboradas entram,
                                dia excluido se corroboradas < MIN_FRAC_A do universo
       cenario B (exploratorio): denominador = soma, sobre o universo, de max(fracao de area coberta, 1 se houve deteccao);
                                 todas as deteccoes entram e as incertezas ficam sinalizadas
"""
from __future__ import annotations

import datetime as dt
import statistics

from . import cobertura as C

MIN_FRAC_A = 0.5          # cenario A: dia so tem extensao normalizada se >= 50 % do universo esta corroborado
MIN_FRAC_K = 0.8          # K so se >= 80 % do universo for comparavel (celulas cobertas pelos dois sensores)
MIN_DIAS_SEMANA = 4       # semana so tem valor se >= 4 dias validos
MIN_REF = 2               # comparacao com a referencia exige >= 2 anos de referencia
FAMILIA = {"Terra": "MODIS", "Aqua": "MODIS", "N20": "VIIRS"}
BLOCO_MODIS = {"6.03": "A", "61.03": "B"}      # inferido (nao confirmado oficialmente)


def bloco_modis(versao_bruta: str | None) -> str:
    return BLOCO_MODIS.get(versao_bruta or "", "DESCONHECIDO")


def semana_do_ano(dia: str) -> int:
    """Semana 1..53 de blocos fixos de 7 dias a partir de 1/jan (NAO e semana ISO); a 53 tem 1-2 dias."""
    d = dt.date.fromisoformat(dia)
    return (d.timetuple().tm_yday - 1) // 7 + 1


def classe_familia(classes: list[str]) -> str:
    """Estado de cobertura de uma celula para a familia (MODIS = Terra e Aqua), pelo melhor caso entre os satelites."""
    for k in (C.COBERTURA_GEOMETRICA_CORROBORADA, C.COBERTURA_GEOMETRICA_PARCIAL, C.COBERTURA_INDETERMINADA):
        if k in classes:
            return k
    return C.SEM_COBERTURA_GEOMETRICA_CORROBORADA


def indicadores_sensor(universo: list, det_por_celula: dict, f_celula: dict, classe_celula: dict) -> dict:
    """Indicadores de UMA familia num dia. ``det_por_celula``: {celula: n}; ``f_celula``: {celula: fracao de area (0..1)};
    ``classe_celula``: {celula: estado de cobertura}. Devolve cenarios A e B com numerador e denominador."""
    n_univ = len(universo)
    ativas = {c for c, n in det_por_celula.items() if n > 0}
    det_total = sum(det_por_celula.values())
    # ---- B (exploratorio)
    den_b = sum(max(f_celula.get(c, 0.0), 1.0 if c in ativas else 0.0) for c in universo)
    em_b = [c for c in ativas if c in set(universo)]
    det_b = sum(det_por_celula[c] for c in em_b)
    desconhecidas = sum(1 for c in universo if classe_celula.get(c) == C.COBERTURA_INDETERMINADA and c not in ativas)
    b = {"ext_celulas": len(em_b), "det": det_b, "intens": (det_b / len(em_b)) if em_b else None,
         "den_cobertura": round(den_b, 3), "ext_norm": (len(em_b) / den_b) if den_b > 0 else None,
         "celulas_cobertura_desconhecida": desconhecidas, "det_fora_do_universo": det_total - det_b}
    # ---- A (conservador)
    corrob = {c for c in universo if classe_celula.get(c) == C.COBERTURA_GEOMETRICA_CORROBORADA}
    excl_det = sum(n for c, n in det_por_celula.items() if c not in corrob)
    if len(corrob) >= MIN_FRAC_A * n_univ:
        ativ_a = ativas & corrob
        det_a = sum(det_por_celula[c] for c in ativ_a)
        a = {"ext_celulas": len(ativ_a), "det": det_a, "intens": (det_a / len(ativ_a)) if ativ_a else None,
             "den_cobertura": len(corrob), "ext_norm": len(ativ_a) / len(corrob), "valido": True,
             "det_excluidas": excl_det, "celulas_corroboradas": len(corrob)}
    else:
        a = {"ext_celulas": None, "det": None, "intens": None, "den_cobertura": len(corrob), "ext_norm": None, "valido": False,
             "det_excluidas": det_total, "celulas_corroboradas": len(corrob)}
    return {"A": a, "B": b, "ativas": ativas, "corroboradas": corrob, "det_total": det_total}


def concordancia(universo: list, ativas_m: set, ativas_v: set, comparaveis: set, null_v_fn=None) -> dict:
    """K (Jaccard) sobre as celulas COMPARAVEIS. K e 'nao aplicavel' se o dia nao for comparavel (< MIN_FRAC_K do universo)
    ou se nao houver celula ativa; o valor diagnostico e devolvido a parte e NAO deve ir para a saida publica."""
    n_univ = len(universo)
    comp = len(comparaveis)
    m, v = ativas_m & comparaveis, ativas_v & comparaveis
    uniao, inter = m | v, m & v
    diag = (len(inter) / len(uniao)) if uniao else None
    ok = comp >= MIN_FRAC_K * n_univ
    out = {"comparavel": bool(ok), "celulas_comparaveis": comp, "frac_comparavel": comp / n_univ if n_univ else None,
           "A_modis": len(m), "A_viirs": len(v), "A_ambos": len(inter), "A_uniao": len(uniao), "so_modis": len(m - v), "so_viirs": len(v - m),
           "K": diag if (ok and uniao) else None, "K_diagnostico": diag}
    if not ok:
        out["motivo_nao_aplicavel"] = "cobertura comparavel insuficiente"
    elif not uniao:
        out["motivo_nao_aplicavel"] = "sem celulas ativas"
    if null_v_fn is not None and out["K"] is not None:
        out["K_nulo"] = null_v_fn(comparaveis, m)
    return out


# ---------------- referencia historica ----------------
def valores_referencia(por_ano: dict, ano_avaliado: int, modo: str = "exclui_ano", anos_permitidos=None) -> list:
    """Valores da referencia para a mesma semana/mes, EXCLUINDO sempre o ano avaliado.
    modo 'exclui_ano': todos os outros anos; 'anteriores': so anos < ano_avaliado."""
    out = []
    for y, v in por_ano.items():
        if y == ano_avaliado or v is None:
            continue
        if modo == "anteriores" and y > ano_avaliado:
            continue
        if anos_permitidos is not None and y not in anos_permitidos:
            continue
        out.append(v)
    return out


def classificar_vs_referencia(x, ref: list) -> str:
    """Posicao de x frente aos valores de referencia. Sem teste de significancia: so a faixa observada (min-max) da referencia."""
    if x is None:
        return "SEM_DADO_NO_PERIODO"
    if len(ref) < MIN_REF:
        return "REFERENCIA_INSUFICIENTE"
    if x > max(ref):
        return "ACIMA_DA_REFERENCIA_DISPONIVEL"
    if x < min(ref):
        return "ABAIXO_DA_REFERENCIA_DISPONIVEL"
    return "DENTRO_DA_FAIXA_DA_REFERENCIA"


def media_valida(valores: list, minimo: int = MIN_DIAS_SEMANA):
    v = [x for x in valores if x is not None]
    return statistics.mean(v) if len(v) >= minimo else None


# ---------------- agregacoes semanais/mensais e classificacao ----------------
def agregar(linhas: list[dict], chave_fn, rotulos: tuple) -> list[dict]:
    """Agrega as linhas diarias por periodo (semana do ano ou mes). Cada valor medio exige >= MIN_DIAS_SEMANA dias validos;
    numerador e denominador por dia permanecem nas linhas diarias."""
    g: dict = {}
    for x in linhas:
        g.setdefault(chave_fn(x), []).append(x)
    out = []
    for k, xs in sorted(g.items()):
        o = {rotulos[0]: k[0], rotulos[1]: k[1], "dias": len(xs), "bloco_modis": "|".join(sorted({x["bloco_modis"] for x in xs}))}
        for nome in ("modis", "viirs"):
            for esc in ("A", "B"):
                v_ext = [x[f"{esc}_{nome}_extnorm"] for x in xs]
                v_int = [x[f"{esc}_{nome}_intens"] for x in xs]
                o[f"{esc}_{nome}_extnorm_media"] = media_valida(v_ext)
                o[f"{esc}_{nome}_intens_media"] = media_valida(v_int)
                o[f"{esc}_{nome}_dias_validos"] = sum(1 for z in v_ext if z is not None)
            o[f"B_{nome}_det_total"] = sum(x[f"B_{nome}_det"] or 0 for x in xs)
        o["det_terra"] = sum(x["det_terra"] for x in xs)
        o["det_aqua"] = sum(x["det_aqua"] for x in xs)
        o["det_n20"] = sum(x["det_n20"] for x in xs)
        o["dias_comparaveis_A"] = sum(1 for x in xs if x["comparavel_A"])
        o["dias_comparaveis_B"] = sum(1 for x in xs if x["comparavel_B"])
        ks = [x["K_A"] for x in xs if x["K_A"] is not None]
        o["K_A_media"] = statistics.mean(ks) if ks else None
        o["conflitos_firms_cmr"] = sum(x[f"cmr_{s}_conflito_firms_cmr"] for x in xs for s in ("terra", "aqua", "n20"))
        out.append(o)
    return out


def bloco_do_ano(ano: int) -> str:
    """Bloco MODIS esperado do ano: A (6.03) ate 2022, B (61.03) a partir de 2023 (OBSERVADO nesta serie; nao confirmado oficialmente)."""
    return "A" if ano <= 2022 else "B"


def classificar_periodos(tab: list[dict], chave_per: str, anos: list[int]) -> None:
    """Acrescenta a cada linha a posicao frente a referencia, SEMPRE excluindo o ano avaliado.
    MODIS: referencia no mesmo bloco de versao (principal) e entre todos os blocos (SENSIBILIDADE); VIIRS: todos os outros anos."""
    for nome in ("modis", "viirs"):
        for esc in ("A", "B"):
            for metrica in ("extnorm", "intens"):
                campo = f"{esc}_{nome}_{metrica}_media"
                por: dict = {}
                for x in tab:
                    por.setdefault(x[chave_per], {})[x["ano"]] = x[campo]
                for x in tab:
                    for modo in ("exclui_ano", "anteriores"):
                        if nome == "modis":
                            perm = {y for y in anos if bloco_do_ano(y) == bloco_do_ano(x["ano"])}
                            ref = valores_referencia(por[x[chave_per]], x["ano"], modo, perm)
                            x[f"ref_{esc}_{nome}_{metrica}_{modo}_mesmo_bloco"] = classificar_vs_referencia(x[campo], ref)
                            ref2 = valores_referencia(por[x[chave_per]], x["ano"], modo)
                            x[f"ref_{esc}_{nome}_{metrica}_{modo}_todos_blocos_SENSIBILIDADE"] = classificar_vs_referencia(x[campo], ref2)
                        else:
                            ref = valores_referencia(por[x[chave_per]], x["ano"], modo)
                            x[f"ref_{esc}_{nome}_{metrica}_{modo}"] = classificar_vs_referencia(x[campo], ref)
                    x[f"n_ref_{nome}_exclui_ano"] = len([1 for y, v in por[x[chave_per]].items() if y != x["ano"] and v is not None])
