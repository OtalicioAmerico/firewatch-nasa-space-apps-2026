"""Estado de dados por satelite-dia (SEM inventar passagens, mascaras de nuvem ou flags de completude).

O que se sabe: quantas detecoes cada satelite tem em cada dia na janela de aquisicao carregada. O que NAO se sabe:
onde o sensor realmente olhou. Por isso o estado so pode dizer:

* SEM_DADOS      - nenhuma detecao do satelite naquele dia na janela de aquisicao carregada;
* VOLUME_BAIXO   - volume do dia < ``min_ratio`` x mediana do proprio satelite no grupo de referencia
                   (heuristica EXPERIMENTAL e NAO VALIDADA; sugere dado/passagem ausente, nao prova);
* OK             - nem um nem outro. NAO significa cobertura completa: so que o volume nao e anomalo.
"""
from __future__ import annotations

import statistics
from collections import Counter


def sensor_day_status(records, days: list[str], satellites: list[str], min_ratio: float = 0.25,
                      group_by_year: bool = True) -> dict:
    """Retorna {(sat, dia): dict(n, referencia, razao, status)} para todo sat em ``satellites`` e dia em ``days``.

    ``records``: detecoes da janela de aquisicao inteira (antes de filtrar pela regiao).
    A mediana de referencia usa os dias do mesmo satelite (e do mesmo ano, se ``group_by_year``), incluindo dias
    com contagem zero; assim um dia ausente nao e ignorado.
    """
    n = Counter((r.sat, r.date) for r in records)
    out = {}
    for sat in satellites:
        groups: dict = {}
        for d in days:
            groups.setdefault(d[:4] if group_by_year else "", []).append(d)
        for g, gdays in groups.items():
            counts = [n[(sat, d)] for d in gdays]
            ref = statistics.median(counts) if counts else 0
            for d in gdays:
                c = n[(sat, d)]
                if c == 0:
                    st = "SEM_DADOS"
                elif ref > 0 and c < min_ratio * ref:
                    st = "VOLUME_BAIXO"
                else:
                    st = "OK"
                out[(sat, d)] = {"n_janela": c, "mediana_ref": ref, "razao": (c / ref if ref else None), "status": st}
    return out


def day_comparability(status: dict, day: str, required: dict[str, list[str]]) -> dict:
    """Comparabilidade MODIS x VIIRS no dia: exige todos os satelites requeridos com status OK.

    Retorna {'comparavel': bool, 'motivos': [ 'Aqua:VOLUME_BAIXO', ... ]}.
    """
    motivos = []
    for _fam, sats in required.items():
        for s in sats:
            st = status[(s, day)]["status"]
            if st != "OK":
                motivos.append(f"{s}:{st}")
    return {"comparavel": not motivos, "motivos": motivos}
