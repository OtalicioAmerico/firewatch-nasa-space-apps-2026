"""Orquestracao: config JSON + dados NASA -> tabelas de resultado reprodutiveis (sem interface)."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform

from . import coverage, harmonize, matching, utilidade
from .geo import Region, region_from_ibge_municipios
from .records import deduplicate, integrity_report, read_firms_csv


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_region(spec: dict, data_dir: str) -> Region:
    if spec["tipo"] == "ibge_uf":
        return region_from_ibge_municipios(data_dir, spec["uf"], spec["nome"])
    if spec["tipo"] == "retangulo":
        return Region.rectangle(spec["nome"], *spec["bbox"])
    raise ValueError(f"regiao desconhecida: {spec['tipo']}")


def load_inputs(cfg: dict, data_dir: str):
    raw, files = [], []
    for e in cfg["entradas"]:
        path = os.path.join(data_dir, *e["arquivo"].split("/"))
        recs = read_firms_csv(path, e["arquivo"], e["produto"], e.get("sha256"), e.get("linhas"))
        raw.extend(recs)
        files.append({"arquivo": e["arquivo"], "produto": e["produto"], "sha256": e.get("sha256"), "linhas": len(recs)})
    uniq = deduplicate(raw)
    return raw, uniq, files


def _write_csv(path: str, rows: list[dict], fields: list[str] | None = None) -> str:
    fields = fields or (list(rows[0].keys()) if rows else [])
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else (round(r[k], 6) if isinstance(r.get(k), float) else r.get(k)))
                        for k in fields})
    return path


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run(cfg: dict, data_dir: str, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    days = cfg["dias"]
    raw, uniq, files = load_inputs(cfg, data_dir)
    uniq = [r for r in uniq if r.date in set(days)]
    integ = integrity_report(uniq)
    region = build_region(cfg["regiao"], data_dir)

    # ---- cobertura/estado de dados (janela de aquisicao inteira, antes do filtro por regiao)
    req = cfg["satelites_requeridos"]
    sats = sorted({s for v in req.values() for s in v})
    st = coverage.sensor_day_status(uniq, days, sats, cfg["cobertura"]["min_ratio"], cfg["cobertura"]["agrupar_por_ano"])
    comp = {d: coverage.day_comparability(st, d, req) for d in days}
    # contagem na regiao por satelite-dia (descritivo)
    in_reg = [r for r in uniq if region.contains(r.lon, r.lat)]
    from collections import Counter
    reg_n = Counter((r.sat, r.date) for r in in_reg)
    sd_rows = [{"satelite": s, "dia": d, "n_janela_aquisicao": st[(s, d)]["n_janela"],
                "mediana_referencia": st[(s, d)]["mediana_ref"], "razao": st[(s, d)]["razao"],
                "status": st[(s, d)]["status"], "n_na_regiao": reg_n[(s, d)]}
               for s in sats for d in days]
    _write_csv(os.path.join(out_dir, "sensor_dia.csv"), sd_rows)

    # ---- evidencia: uma linha por deteccao na regiao, com referencias de origem (nao versionada)
    ev = [{"rid": r.refs[0], "todas_as_origens": ";".join(r.refs), "satelite": r.sat, "dia": r.date, "t_min_utc": r.t,
           "lat": r.lat, "lon": r.lon, "frp": r.frp, "confianca": r.conf} for r in sorted(in_reg, key=lambda r: r.refs[0])]
    _write_csv(os.path.join(out_dir, "evidencia_registros.csv"), ev)

    results = {"celulas": {}}
    sizes = [cfg["celulas"]["principal"]] + list(cfg["celulas"].get("sensibilidade", []))
    for size in sizes:
        cds = harmonize.build_cell_days(uniq, region, size)
        uni = harmonize.cell_universe(region, size, cds)
        nullk = harmonize.shifted_null_k(uniq, region, size, days)
        daily = harmonize.daily_summary(cds, days, len(uni), comp, nullk)
        for r in daily:
            r["n_deteccoes_por_satelite"] = json.dumps(r["n_deteccoes_por_satelite"], sort_keys=True)
        cdr = harmonize.cell_day_rows(cds, region, size, comp)
        tag = f"{size:g}"
        _write_csv(os.path.join(out_dir, f"dias_{tag}.csv"), daily)
        _write_csv(os.path.join(out_dir, f"celula_dia_{tag}.csv"), cdr)
        states = Counter((r["dia"], r["estado"]) for r in cdr)
        results["celulas"][tag] = {
            "universo": len(uni), "celulas_dia_com_deteccao": len(cdr),
            "concordancia": harmonize.pooled_concordance(daily),
            "estados_por_dia": {d: {s: states[(d, s)] for s in harmonize.STATES if states[(d, s)]} for d in days},
        }
        results["celulas"][tag]["daily"] = daily
        if size == cfg["celulas"]["principal"]:
            results["utilidade"] = utilidade.analyze(daily, uniq, days, req)

    # ---- correspondencias candidatas Aqua x N20 (MODIS dentro da regiao; VIIRS em toda a janela)
    mc = cfg["correspondencia"]
    tmin, tmax = mc["janela_min"]
    modis = [r for r in in_reg if r.sat == mc["modis"]]
    viirs = [r for r in uniq if r.sat == mc["viirs"]]
    shift = cfg["nulo_deslocamento_graus"]
    import copy
    nul_sets = []
    for dla, dlo in ((shift, 0), (-shift, 0), (0, shift), (0, -shift)):
        sv = []
        for v in viirs:
            c = copy.copy(v)
            c.lat, c.lon = v.lat + dla, v.lon + dlo
            sv.append(c)
        nul_sets.append(sv)
    corr = {}
    by_year = {y: [m for m in modis if m.date[:4] == y] for y in sorted({m.date[:4] for m in modis})}
    for R in mc["raios_m"]:
        entry = {}
        for y, ms in by_year.items():
            vy = viirs
            cands = matching.find_candidates(ms, vy, R, tmin, tmax)
            s = matching.summarize(ms, cands)
            nul = [len({c.modis_rid for c in matching.find_candidates(ms, sv, R, tmin, tmax)}) for sv in nul_sets]
            s["controle_deslocado_media_modis_com_candidato"] = sum(nul) / len(nul)
            entry[y] = s
            if R == mc["raio_principal_m"]:
                _write_csv(os.path.join(out_dir, f"candidatos_{R}m_{y}.csv"),
                           [{"modis_rid": c.modis_rid, "viirs_rid": c.viirs_rid, "dist_m": c.dist_m,
                             "dt_min": c.dt_min, "rotulo": c.label} for c in cands])
                # candidatos por dia
                from collections import defaultdict
                dd = Counter()
                rid_day = {m.rid: m.date for m in ms}
                for rid in {c.modis_rid for c in cands}:
                    dd[rid_day[rid]] += 1
                entry[y]["modis_com_candidato_por_dia"] = {d: dd[d] for d in days if d[:4] == y}
                entry[y]["modis_por_dia"] = dict(Counter(m.date for m in ms))
        corr[str(R)] = entry
    results["correspondencia"] = {"modis": mc["modis"], "viirs": mc["viirs"], "janela_min": [tmin, tmax],
                                  "parametros_nao_validados": True, "por_raio": corr}

    results["integridade"] = {"arquivos": files, "registros_brutos": len(raw), "registros_unicos_no_periodo": integ["n"],
                              "duplicatas_removidas": len(raw) - len(deduplicate(raw)),
                              "chaves_duplicadas_apos_dedup": integ["chaves_duplicadas"]}
    results["status_sensor_dia"] = {f"{s}|{d}": st[(s, d)]["status"] for s in sats for d in days}
    results["comparabilidade"] = comp

    manifest = {"config": cfg, "python": platform.python_version(), "resultados": results["integridade"],
                "saidas_sha256": {n: _sha(os.path.join(out_dir, n)) for n in sorted(os.listdir(out_dir))
                                  if n.endswith(".csv")}}
    with open(os.path.join(out_dir, "resumo.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(results, fh, indent=1, sort_keys=True, ensure_ascii=False, default=str)
        fh.write("\n")
    with open(os.path.join(out_dir, "manifesto_execucao.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True, ensure_ascii=False, default=str)
        fh.write("\n")
    return results
