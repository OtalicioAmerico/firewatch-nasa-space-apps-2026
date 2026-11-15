"""Processamento inicial dos dados historicos (Missao 04). Le o banco bruto; grava resultados em OUTRO arquivo.

Uso: python tools/historico/processar.py --bruto <bruto.db> --resultados <resultados.db> --saida <diretorio json>
Nao calcula o indicador combinado R; extensao e intensidade sao separadas; ausencia de registro nao e 'sem fogo'.
"""
import argparse
import collections
import datetime as dt
import json
import os
import sqlite3
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal import matching  # noqa: E402
from firecal.records import Record  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--bruto", required=True)
ap.add_argument("--resultados", required=True)
ap.add_argument("--saida", required=True)
a = ap.parse_args()
os.makedirs(a.saida, exist_ok=True)
b = sqlite3.connect(a.bruto)
if os.path.exists(a.resultados):
    os.remove(a.resultados)           # resultados derivados sao reconstruidos do zero (o bruto nunca e alterado)
r = sqlite3.connect(a.resultados)
out = {}
t0 = time.time()

D0, D1 = dt.date(2021, 1, 1), dt.date(2025, 12, 31)
dias = [(D0 + dt.timedelta(days=i)).isoformat() for i in range((D1 - D0).days + 1)]
FAM = {"Terra": "MODIS", "Aqua": "MODIS", "N20": "VIIRS"}

# ---- A. contagens (caixa inteira) por produto, ano, mes, satelite
q = b.execute("select produto, substr(dia_utc,1,4), substr(dia_utc,1,7), satelite, count(*) from deteccao group by 1,2,3,4").fetchall()
out["ano_produto"] = collections.defaultdict(lambda: collections.Counter())
out["mes_satelite"] = collections.defaultdict(dict)
for prod, ano, mes, sat, n in q:
    out["ano_produto"][f"{prod}|{ano}"][sat] += n
    out["mes_satelite"][mes][sat] = n
out["ano_produto"] = {k: dict(v) for k, v in out["ano_produto"].items()}
out["totais"] = {"deteccoes_unicas": b.execute("select count(*) from deteccao").fetchone()[0],
                 "em_tocantins": b.execute("select count(*) from deteccao where em_regiao=1").fetchone()[0],
                 "arquivos": b.execute("select count(*) from arquivo_origem").fetchone()[0],
                 "origens": b.execute("select count(*) from deteccao_origem").fetchone()[0],
                 "linhas_lidas_total": b.execute("select sum(linhas) from arquivo_origem").fetchone()[0]}
out["totais"]["duplicatas_unidas"] = out["totais"]["linhas_lidas_total"] - out["totais"]["deteccoes_unicas"]

# ---- B. dias com e sem registro (caixa inteira), por satelite
n_dia = collections.defaultdict(dict)
for sat, dia, n in b.execute("select satelite, dia_utc, count(*) from deteccao group by 1,2"):
    n_dia[sat][dia] = n
out["dias_sem_registro"] = {s: [d for d in dias if n_dia[s].get(d, 0) == 0] for s in ("Terra", "Aqua", "N20")}
sem_modis = [d for d in dias if n_dia["Terra"].get(d, 0) == 0 and n_dia["Aqua"].get(d, 0) == 0]
out["dias_sem_registro"]["MODIS(Terra+Aqua)"] = sem_modis
out["dias_ambos"] = sum(1 for d in dias if (n_dia["Terra"].get(d, 0) + n_dia["Aqua"].get(d, 0)) > 0 and n_dia["N20"].get(d, 0) > 0)
out["dias_total"] = len(dias)
out["dias_so_modis"] = [d for d in dias if (n_dia["Terra"].get(d, 0) + n_dia["Aqua"].get(d, 0)) > 0 and n_dia["N20"].get(d, 0) == 0]
out["dias_so_viirs"] = [d for d in dias if (n_dia["Terra"].get(d, 0) + n_dia["Aqua"].get(d, 0)) == 0 and n_dia["N20"].get(d, 0) > 0]
out["dias_nenhum"] = [d for d in dias if not any(n_dia[s].get(d, 0) for s in ("Terra", "Aqua", "N20"))]

# ---- C. extensao x intensidade (so Tocantins, celulas 0,25 graus); tabelas derivadas
r.executescript("""
create table res_celula_dia(dia text, cel_i integer, cel_j integer, satelite text, n integer, primary key(dia,cel_i,cel_j,satelite));
create table res_sensor_dia(dia text, sensor text, n_deteccoes integer, celulas_ativas integer, deteccoes_por_celula real,
  frp_mediana real, primary key(dia, sensor));
""")
rows = b.execute("select dia_utc, cel_i, cel_j, satelite, count(*) from deteccao where em_regiao=1 group by 1,2,3,4").fetchall()
r.executemany("insert into res_celula_dia values(?,?,?,?,?)", rows)
frp = collections.defaultdict(list)
for dia, sat, f in b.execute("select dia_utc, satelite, frp from deteccao where em_regiao=1 and frp is not null"):
    frp[(dia, "MODIS" if sat in ("Terra", "Aqua") else "VIIRS")].append(f)
cel = collections.defaultdict(set)
cnt = collections.Counter()
for dia, i, j, sat, n in rows:
    fam = "MODIS" if sat in ("Terra", "Aqua") else "VIIRS"
    cel[(dia, fam)].add((i, j))
    cnt[(dia, fam)] += n
sd = {}
for d in dias:
    for fam in ("MODIS", "VIIRS"):
        n, c = cnt[(d, fam)], len(cel[(d, fam)])
        f = frp.get((d, fam))
        sd[(d, fam)] = (n, c, (n / c) if c else None, statistics.median(f) if f else None)
        r.execute("insert into res_sensor_dia values(?,?,?,?,?,?)", (d, fam, n, c, sd[(d, fam)][2], sd[(d, fam)][3]))
r.commit()
out["sensor_dia"] = {f"{d}|{fam}": v for (d, fam), v in sd.items()}

def mes_resumo(fam, ym):
    ds = [d for d in dias if d.startswith(ym)]
    return {"deteccoes": sum(sd[(d, fam)][0] for d in ds),
            "celulas_ativas_med_dia": statistics.median(sd[(d, fam)][1] for d in ds),
            "det_por_celula_med_dia": statistics.median([sd[(d, fam)][2] for d in ds if sd[(d, fam)][2] is not None] or [0])}
out["mes_extensao_intensidade_TO"] = {ym: {fam: mes_resumo(fam, ym) for fam in ("MODIS", "VIIRS")}
                                      for ym in sorted({d[:7] for d in dias})}

# ---- D/E. oportunidades de correspondencia Aqua x NOAA-20 e horarios, por ano (Tocantins para o Aqua; toda a caixa para o NOAA-20)
def carregar(sat, dia, so_regiao):
    sql = "select id, satelite, t_min, dia_utc, lat, lon, frp, confianca, scan, track, dia_noite, produto from deteccao where satelite=? and dia_utc=?"
    if so_regiao:
        sql += " and em_regiao=1"
    return [Record(rid=str(x[0]), sat=x[1], t=x[2], date=x[3], lat=x[4], lon=x[5], frp=x[6], conf=x[7], scan=x[8], track=x[9],
                   dn=x[10], product=x[11]) for x in b.execute(sql, (sat, dia))]

hora = collections.defaultdict(list)
dt_hist = collections.defaultdict(collections.Counter)
aqua_n = collections.Counter()
prox = collections.defaultdict(lambda: collections.Counter())
for d in dias:
    A = carregar("Aqua", d, True)
    if not A:
        continue
    dd = dt.date.fromisoformat(d)
    V = []
    for k in (-1, 0, 1):
        V += carregar("N20", (dd + dt.timedelta(days=k)).isoformat(), False)
    ano = d[:4]
    aqua_n[ano] += len(A)
    for x in A:
        if x.dn == "D":
            hora[("Aqua", ano)].append(x.t % 1440)
    cand = matching.find_candidates(A, V, 1000, -360, 360)
    for c in cand:
        dt_hist[ano][(c.dt_min // 15) * 15] += 1
    for lim in (15, 30, 60):
        hit = {c.modis_rid for c in matching.find_candidates(A, V, 1000, -lim, lim)}
        prox[ano][lim] += len(hit)
    for lim, (lo, hi) in (("pares_1km_pm360", (-360, 360)),):
        pass
out["aqua_TO_por_ano"] = dict(aqua_n)
out["aqua_com_N20_a_1km_por_janela"] = {ano: {f"+-{lim}min": prox[ano][lim] for lim in (15, 30, 60)} for ano in sorted(prox)}
out["dt_modal_aqua_menos_n20"] = {ano: [(k, v) for k, v in dt_hist[ano].most_common(3)] for ano in sorted(dt_hist)}
for sat in ("Terra", "N20"):
    for dia_, hh in b.execute("select dia_utc, t_min % 1440 from deteccao where satelite=? and dia_noite='D' and em_regiao=1", (sat,)):
        hora[(sat, dia_[:4])].append(hh)
out["hora_utc_mediana_diurna_TO"] = {f"{s}|{ano}": round(statistics.median(v) / 60, 2) for (s, ano), v in sorted(hora.items()) if v}

# ---- F. versoes e transicao
ver = b.execute("select produto, satelite, versao_bruta, count(*), min(dia_utc), max(dia_utc) from deteccao group by 1,2,3 order by 1,2,5").fetchall()
out["versoes"] = [list(v) for v in ver]
dias_com_duas = b.execute("select count(*) from (select satelite, dia_utc from deteccao where produto='MODIS_SP' group by 1,2 having count(distinct versao_bruta)>1)").fetchone()[0]
out["dias_com_mais_de_uma_versao_modis"] = dias_com_duas
out["versoes_por_ano"] = [list(v) for v in b.execute("select produto, substr(dia_utc,1,4), versao_bruta, count(*) from deteccao group by 1,2,3 order by 1,2").fetchall()]

# razao mensal MODIS/NOAA-20 em celulas ativas e deteccoes (TO), para olhar a vizinhanca da transicao
meses = sorted({d[:7] for d in dias})
out["razao_mensal_modis_viirs_TO"] = {}
for ym in meses:
    m = mes_resumo("MODIS", ym); v = mes_resumo("VIIRS", ym)
    out["razao_mensal_modis_viirs_TO"][ym] = {"modis": m["deteccoes"], "viirs": v["deteccoes"],
                                              "razao_deteccoes": (m["deteccoes"] / v["deteccoes"]) if v["deteccoes"] else None,
                                              "celulas_med_modis": m["celulas_ativas_med_dia"], "celulas_med_viirs": v["celulas_ativas_med_dia"]}

# ---- G. tamanho e tempos
out["banco_bruto_bytes"] = os.path.getsize(a.bruto)
out["tempo_processamento_s"] = round(time.time() - t0)
json.dump(out, open(os.path.join(a.saida, "processamento_inicial.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True, default=str)
r.close()
print("ok", out["totais"], f"{out['tempo_processamento_s']}s")
