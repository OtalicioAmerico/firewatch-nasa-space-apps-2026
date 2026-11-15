"""Armazenamento local SQLite dos dados FIRMS (somente biblioteca padrao).

Separacao deliberada (ver docs): os CSV originais ficam FORA do banco (imutaveis, SHA-256 no manifesto);
o banco ``bruto`` guarda metadados de origem, deteccoes deduplicadas e versoes; os resultados derivados vao
para outro arquivo (``resultados``), reconstruivel. Importacao idempotente: um arquivo ja importado (mesmo SHA-256)
e ignorado; duplicatas entre arquivos sao unidas por chave unica e todas as origens ficam registradas.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
import datetime as dt

from .geo import cell_index

EPOCH = dt.datetime(1970, 1, 1)
SATELITES = {"Terra": "Terra", "Aqua": "Aqua", "N20": "N20", "N21": "N21", "N": "SNPP"}

DDL = """
create table if not exists arquivo_origem(
  id integer primary key, sha256 text not null unique, caminho text not null, produto text not null,
  inicio text not null, dias integer not null, bbox text not null, bytes integer not null, linhas integer not null,
  versoes text not null, origem text not null, http integer);
create table if not exists deteccao(
  id integer primary key, satelite text not null, produto text not null, t_min integer not null, dia_utc text not null,
  lat real not null, lon real not null, frp real, confianca text, scan real, track real, dia_noite text, tipo text,
  versao_bruta text not null, colecao_inferida text, em_regiao integer, cel_i integer not null, cel_j integer not null,
  unique(satelite, t_min, lat, lon));
create table if not exists deteccao_origem(
  deteccao_id integer not null, arquivo_id integer not null, linha integer not null,
  primary key(deteccao_id, arquivo_id, linha));
create table if not exists mapa_versao(
  produto text not null, versao_bruta text not null, colecao_inferida text not null, confirmada integer not null,
  fonte text, observacao text, primary key(produto, versao_bruta));
create table if not exists execucao_import(
  id integer primary key, descricao text, arquivos_novos integer, arquivos_ja_importados integer, linhas_lidas integer,
  linhas_novas integer, duplicatas integer);
create index if not exists ix_det_dia_sat on deteccao(dia_utc, satelite);
create index if not exists ix_det_cel on deteccao(dia_utc, cel_i, cel_j);
create index if not exists ix_det_ver on deteccao(satelite, versao_bruta, dia_utc);
create index if not exists ix_org_arq on deteccao_origem(arquivo_id);
"""

MAPA_VERSAO = [
    ("MODIS_SP", "6.03", "C6", 0, "inferido a partir do campo version", "nao consta na documentacao FIRMS; NAO confirmado"),
    ("MODIS_SP", "61.03", "C6.1", 0, "inferido a partir do campo version", "nao consta na documentacao FIRMS; NAO confirmado"),
    ("VIIRS_NOAA20_SP", "2", "VIIRS-C2", 0, "inferido a partir do campo version", "versao constante nas amostras; homogeneidade cientifica NAO assumida"),
]


def abrir(caminho: str) -> sqlite3.Connection:
    c = sqlite3.connect(caminho)
    c.execute("pragma journal_mode=wal")
    c.execute("pragma synchronous=normal")
    c.executescript(DDL)
    c.executemany("insert or ignore into mapa_versao values(?,?,?,?,?,?)", MAPA_VERSAO)
    c.commit()
    return c


def _sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _colecao(c, produto, versao):
    r = c.execute("select colecao_inferida from mapa_versao where produto=? and versao_bruta=?", (produto, versao)).fetchone()
    return r[0] if r else "DESCONHECIDA"


def importar_manifesto(c: sqlite3.Connection, dir_dados: str, manifesto: str, regiao=None, tamanho_celula=0.25,
                       descricao="importacao", log=print) -> dict:
    """Importa os arquivos validados de um manifesto JSONL. Idempotente. ``regiao``: objeto com ``contains(lon, lat)``."""
    novos = ja = lidas = novas = dups = 0
    with open(manifesto, encoding="utf-8") as fh:
        regs = [json.loads(l) for l in fh if l.strip()]
    for m in regs:
        if m.get("status", "ok") != "ok" or "arquivo" not in m:
            continue
        caminho = os.path.join(dir_dados, *m["arquivo"].split("/"))
        sha = _sha(caminho)
        if sha != m["sha256"]:
            raise ValueError(f"SHA-256 divergente: {m['arquivo']}")
        if c.execute("select 1 from arquivo_origem where sha256=?", (sha,)).fetchone():
            ja += 1
            continue
        cur = c.execute("insert into arquivo_origem(sha256,caminho,produto,inicio,dias,bbox,bytes,linhas,versoes,origem,http)"
                        " values(?,?,?,?,?,?,?,?,?,?,?)",
                        (sha, m["arquivo"], m["produto"], m["inicio"], m["dias"], m["bbox"], m["bytes"], m["linhas"],
                         json.dumps(m.get("versoes", {}), sort_keys=True), m.get("origem", "nasa_api"), m.get("http")))
        aid = cur.lastrowid
        c.execute("create temp table if not exists stage(linha integer, satelite text, t_min integer, lat real, lon real)")
        c.execute("delete from stage")
        linhas_arq = []
        stage = []
        with open(caminho, encoding="utf-8", newline="") as f:
            for n, r in enumerate(csv.DictReader(f), start=2):
                sat = SATELITES[r["satellite"]]
                hh = int(r["acq_time"])
                t = int((dt.datetime.strptime(r["acq_date"], "%Y-%m-%d") + dt.timedelta(hours=hh // 100, minutes=hh % 100) - EPOCH).total_seconds() // 60)
                lat, lon = float(r["latitude"]), float(r["longitude"])
                i, j = cell_index(lat, lon, tamanho_celula)
                em = (1 if regiao.contains(lon, lat) else 0) if regiao is not None else None
                ver = r["version"]
                linhas_arq.append((sat, m["produto"], t, r["acq_date"], lat, lon, float(r["frp"]) if r["frp"] != "" else None,
                                   r["confidence"], float(r["scan"]), float(r["track"]), r["daynight"], r.get("type"),
                                   ver, _colecao(c, m["produto"], ver), em, i, j))
                stage.append((n, sat, t, lat, lon))
        antes = c.execute("select count(*) from deteccao").fetchone()[0]
        c.executemany("insert or ignore into deteccao(satelite,produto,t_min,dia_utc,lat,lon,frp,confianca,scan,track,dia_noite,tipo,"
                      "versao_bruta,colecao_inferida,em_regiao,cel_i,cel_j) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", linhas_arq)
        depois = c.execute("select count(*) from deteccao").fetchone()[0]
        c.executemany("insert into stage values(?,?,?,?,?)", stage)
        c.execute("insert or ignore into deteccao_origem select d.id, ?, s.linha from stage s join deteccao d "
                  "on d.satelite=s.satelite and d.t_min=s.t_min and d.lat=s.lat and d.lon=s.lon", (aid,))
        c.commit()
        novos += 1
        lidas += len(stage)
        novas += depois - antes
        dups += len(stage) - (depois - antes)
        if novos % 50 == 0:
            log(f"importados {novos} arquivos; linhas {lidas}")
    c.execute("insert into execucao_import(descricao,arquivos_novos,arquivos_ja_importados,linhas_lidas,linhas_novas,duplicatas)"
              " values(?,?,?,?,?,?)", (descricao, novos, ja, lidas, novas, dups))
    c.commit()
    return {"arquivos_novos": novos, "arquivos_ja_importados": ja, "linhas_lidas": lidas, "linhas_novas": novas,
            "duplicatas": dups}


def verificar(c: sqlite3.Connection) -> dict:
    """Consistencia interna: toda deteccao tem origem; linhas por arquivo conferem com as origens registradas."""
    sem_origem = c.execute("select count(*) from deteccao d where not exists(select 1 from deteccao_origem o where o.deteccao_id=d.id)").fetchone()[0]
    dif = c.execute("select count(*) from arquivo_origem a where a.linhas != (select count(*) from deteccao_origem o where o.arquivo_id=a.id)").fetchone()[0]
    return {"deteccoes": c.execute("select count(*) from deteccao").fetchone()[0],
            "arquivos": c.execute("select count(*) from arquivo_origem").fetchone()[0],
            "deteccoes_sem_origem": sem_origem, "arquivos_com_contagem_divergente": dif}
