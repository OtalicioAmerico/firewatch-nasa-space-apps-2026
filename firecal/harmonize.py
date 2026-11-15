"""Harmonizacao experimental por presenca em celula-dia (EXPERIMENTAL, NAO VALIDADO).

Definicoes (ver docs/METODO_HARMONIZACAO.md):

* unidade espacial: celula ``size`` x ``size`` graus (parametro experimental), grade ancorada em (0, 0);
* unidade temporal: dia UTC (``acq_date``);
* presenca MODIS(c, d) = 1 se ha >= 1 deteccao Terra ou Aqua na celula c no dia d; presenca VIIRS idem com NOAA-20
  (e demais VIIRS, se configurados). Contagens por satelite sao descritivas e NUNCA somadas entre sensores;
* todo indicador conjunto e calculado sobre CONJUNTOS de celulas (uniao/intersecao), nao sobre contagens, de modo que
  uma mesma celula nunca e contada duas vezes.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .geo import cell_center, cell_id, cell_index

STATES = ("AMBOS", "SO_MODIS", "SO_VIIRS", "MODIS_SEM_COMPARACAO", "VIIRS_SEM_COMPARACAO",
          "SEM_DETECCAO_REGISTRADA", "COBERTURA_INDETERMINADA")


@dataclass
class CellDay:
    date: str
    i: int
    j: int
    counts: Counter = field(default_factory=Counter)   # por satelite (descritivo)
    refs: list = field(default_factory=list)           # rid de todas as detecoes que sustentam

    @property
    def has_modis(self) -> bool:
        return any(n for s, n in self.counts.items() if s in MODIS_SATS)

    @property
    def has_viirs(self) -> bool:
        return any(n for s, n in self.counts.items() if s not in MODIS_SATS)


MODIS_SATS = ("Terra", "Aqua")


def cell_state(has_modis: bool, has_viirs: bool, comparable: bool) -> str:
    """Estado de uma celula-dia.

    A exclusividade so e afirmada quando o dia e comparavel (todos os satelites requeridos com volume nao
    anomalo). Fora disso, a deteccao e registrada mas SEM alegar que o outro sensor 'nao viu'.
    Ausencia de deteccoes nunca vira 'nenhum fogo'.
    """
    if has_modis and has_viirs:
        return "AMBOS"
    if has_modis:
        return "SO_MODIS" if comparable else "MODIS_SEM_COMPARACAO"
    if has_viirs:
        return "SO_VIIRS" if comparable else "VIIRS_SEM_COMPARACAO"
    return "SEM_DETECCAO_REGISTRADA" if comparable else "COBERTURA_INDETERMINADA"


def build_cell_days(records, region, size: float) -> dict:
    """Agrupa as deteccoes DENTRO da regiao em celula-dia. ``records`` deve estar deduplicado."""
    out: dict = {}
    for r in records:
        if not region.contains(r.lon, r.lat):
            continue
        i, j = cell_index(r.lat, r.lon, size)
        cd = out.get((r.date, i, j))
        if cd is None:
            cd = out[(r.date, i, j)] = CellDay(r.date, i, j)
        cd.counts[r.sat] += 1
        cd.refs.append(r.rid if len(r.refs) <= 1 else ";".join(r.refs))
    return out


def cell_universe(region, size: float, cell_days: dict) -> set:
    """Celulas da regiao: centro dentro da regiao OU com pelo menos uma deteccao registrada."""
    uni = {(i, j) for i, j in region.cells_overlapping_bbox(size)
           if region.contains(*reversed(cell_center(size, i, j)))}
    uni |= {(cd.i, cd.j) for cd in cell_days.values()}
    return uni


def daily_summary(cell_days: dict, days: list[str], universe_n: int, comparability: dict,
                  null_k: dict | None = None) -> list[dict]:
    """Uma linha por dia com conjuntos M, V e indicadores. Nao ha soma entre sensores."""
    by_day = defaultdict(list)
    for cd in cell_days.values():
        by_day[cd.date].append(cd)
    rows = []
    for d in days:
        cds = by_day.get(d, [])
        M = {(c.i, c.j) for c in cds if c.has_modis}
        V = {(c.i, c.j) for c in cds if c.has_viirs}
        both, union = M & V, M | V
        comp = comparability[d]
        row = {
            "dia": d,
            "comparavel": comp["comparavel"],
            "motivos_nao_comparavel": "|".join(comp["motivos"]),
            "celulas_universo": universe_n,
            "A_MODIS": len(M), "A_VIIRS": len(V), "A_AMBOS": len(both), "A_UNIAO": len(union),
            "SO_MODIS": len(M - V), "SO_VIIRS": len(V - M),
            # concordancia espacial: Jaccard = |M n V| / |M u V| (indefinido se uniao vazia)
            "K_jaccard": (len(both) / len(union)) if union else None,
            # referencia de independencia: celulas em comum esperadas se M e V fossem sorteios independentes
            "ambos_esperado_indep": (len(M) * len(V) / universe_n) if universe_n else None,
            "K_nulo_deslocado": (null_k or {}).get(d),
            "n_deteccoes_por_satelite": dict(sum((c.counts for c in cds), Counter())),
        }
        rows.append(row)
    # indice relativo por sensor: A_s(d) / mediana de A_s nos dias COMPARAVEIS do periodo
    for key, idx in (("A_MODIS", "I_MODIS"), ("A_VIIRS", "I_VIIRS")):
        ref = [r[key] for r in rows if r["comparavel"]]
        med = statistics.median(ref) if ref else 0
        for r in rows:
            r[idx] = (r[key] / med) if (med and r["comparavel"]) else None
        for r in rows:
            r["ref_mediana_" + key] = med
    for r in rows:
        # indicador conjunto experimental R(d): media dos dois indices relativos; indefinido se nao comparavel
        r["R_conjunto"] = ((r["I_MODIS"] + r["I_VIIRS"]) / 2
                           if r["I_MODIS"] is not None and r["I_VIIRS"] is not None else None)
        r["lift_vs_indep"] = (r["A_AMBOS"] / r["ambos_esperado_indep"]
                              if r["ambos_esperado_indep"] else None)
    return rows


def shifted_null_k(records, region, size: float, days: list[str],
                   shifts=((0.3, 0.0), (-0.3, 0.0), (0.0, 0.3), (0.0, -0.3))) -> dict:
    """Jaccard medio por dia com as presencas VIIRS deslocadas (controle de acaso).

    O deslocamento destroi a correspondencia geografica mantendo a distribuicao espacial grosseira. E um controle
    adequado em celulas pequenas e FRACO em celulas >= 0,5 grau (a atividade e agrupada em escala regional).
    """
    modis = defaultdict(set)
    viirs = defaultdict(list)
    for r in records:
        if not region.contains(r.lon, r.lat):
            continue
        if r.family == "MODIS":
            modis[r.date].add(cell_index(r.lat, r.lon, size))
        else:
            viirs[r.date].append((r.lat, r.lon))
    out = {}
    for d in days:
        vals = []
        for dla, dlo in shifts:
            V = {cell_index(la + dla, lo + dlo, size) for la, lo in viirs[d]}
            u = modis[d] | V
            if u:
                vals.append(len(modis[d] & V) / len(u))
        out[d] = (sum(vals) / len(vals)) if vals else None
    return out


def pooled_concordance(rows: list[dict]) -> dict:
    """Concordancia agregada sobre os dias (celula-dia como unidade), separando comparaveis."""
    def agg(rs):
        both = sum(r["A_AMBOS"] for r in rs)
        uni = sum(r["A_UNIAO"] for r in rs)
        m = sum(r["A_MODIS"] for r in rs)
        v = sum(r["A_VIIRS"] for r in rs)
        return {"dias": len(rs), "A_MODIS": m, "A_VIIRS": v, "A_AMBOS": both, "A_UNIAO": uni,
                "SO_MODIS": sum(r["SO_MODIS"] for r in rs), "SO_VIIRS": sum(r["SO_VIIRS"] for r in rs),
                "K_jaccard": (both / uni) if uni else None}
    return {"todos": agg(rows), "comparaveis": agg([r for r in rows if r["comparavel"]])}


def cell_day_rows(cell_days: dict, region, size: float, comparability: dict) -> list[dict]:
    """Linhas esparsas (so celulas com >= 1 deteccao), ordenadas, com estado e referencias."""
    rows = []
    for (d, i, j), cd in sorted(cell_days.items()):
        comp = comparability[d]["comparavel"]
        la0, lo0 = i * size, j * size
        rows.append({
            "dia": d, "celula": cell_id(size, i, j), "lat_min": la0, "lon_min": lo0,
            "celula_inteira_na_regiao": region.cell_fully_inside(size, i, j),
            "n_Terra": cd.counts.get("Terra", 0), "n_Aqua": cd.counts.get("Aqua", 0),
            "n_N20": cd.counts.get("N20", 0),
            "presenca_MODIS": int(cd.has_modis), "presenca_VIIRS": int(cd.has_viirs),
            "estado": cell_state(cd.has_modis, cd.has_viirs, comp),
            "dia_comparavel": comp, "n_registros_de_suporte": len(cd.refs),
        })
    return rows
