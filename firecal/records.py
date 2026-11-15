"""Leitura, validacao de integridade e deduplicacao de detecoes FIRMS.

Somente biblioteca padrao. Codigo escrito para este projeto (nao deriva do projeto legado).
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
from dataclasses import dataclass, field

EPOCH = dt.datetime(1970, 1, 1)

#: codigo FIRMS -> nome canonico do satelite
SATELLITES = {"Terra": "Terra", "Aqua": "Aqua", "N20": "N20", "N21": "N21", "N": "SNPP"}
#: satelite -> familia de sensor
FAMILY = {"Terra": "MODIS", "Aqua": "MODIS", "N20": "VIIRS", "N21": "VIIRS", "SNPP": "VIIRS"}


class IntegrityError(ValueError):
    """Registro ou arquivo violou uma regra de integridade."""


@dataclass
class Record:
    rid: str            # "<arquivo relativo>:<linha do CSV (1 = cabecalho)>"
    sat: str            # Terra | Aqua | N20 | N21 | SNPP
    t: int              # minutos UTC desde 1970-01-01
    date: str           # dia UTC (acq_date)
    lat: float
    lon: float
    frp: float | None
    conf: str
    scan: float
    track: float
    dn: str
    product: str        # ex.: MODIS_SP
    refs: tuple = field(default_factory=tuple)  # todos os rid que contem esta mesma detecao

    @property
    def family(self) -> str:
        return FAMILY[self.sat]

    @property
    def key(self):
        return (self.sat, self.t, round(self.lat, 5), round(self.lon, 5))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_row(row: dict, rid: str, product: str) -> Record:
    """Converte uma linha CSV em Record; levanta IntegrityError se invalida."""
    try:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        sat = SATELLITES[row["satellite"]]
        hhmm = int(row["acq_time"])
        day = dt.datetime.strptime(row["acq_date"], "%Y-%m-%d")
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("coordenada fora do intervalo")
        if not (0 <= hhmm // 100 <= 23 and 0 <= hhmm % 100 <= 59):
            raise ValueError("acq_time invalido")
        t = int((day + dt.timedelta(hours=hhmm // 100, minutes=hhmm % 100) - EPOCH).total_seconds() // 60)
        frp = float(row["frp"]) if row.get("frp") not in (None, "") else None
        return Record(rid=rid, sat=sat, t=t, date=row["acq_date"], lat=lat, lon=lon, frp=frp,
                      conf=row.get("confidence", ""), scan=float(row["scan"]), track=float(row["track"]),
                      dn=row.get("daynight", ""), product=product, refs=(rid,))
    except (KeyError, ValueError) as exc:
        raise IntegrityError(f"{rid}: {exc}") from exc


def read_firms_csv(path: str, rel: str, product: str, expected_sha256: str | None = None,
                   expected_rows: int | None = None) -> list[Record]:
    """Le um CSV FIRMS conferindo SHA-256 e numero de linhas quando informados."""
    if expected_sha256 is not None:
        got = sha256_file(path)
        if got.lower() != expected_sha256.lower():
            raise IntegrityError(f"{rel}: SHA-256 diferente do esperado ({got} != {expected_sha256})")
    out = []
    with open(path, encoding="utf-8", newline="") as fh:
        for n, row in enumerate(csv.DictReader(fh), start=2):
            out.append(parse_row(row, f"{rel}:{n}", product))
    if expected_rows is not None and len(out) != expected_rows:
        raise IntegrityError(f"{rel}: {len(out)} linhas, esperado {expected_rows}")
    return out


def deduplicate(records: list[Record]) -> list[Record]:
    """Une detecoes identicas (mesmo satelite, instante, lat, lon) vindas de arquivos diferentes.

    Cada detecao fisica passa a existir uma unica vez; os rid de origem ficam em ``refs``.
    A ordem do primeiro aparecimento e mantida (resultado deterministico).
    """
    seen: dict = {}
    for r in records:
        k = r.key
        if k in seen:
            seen[k].refs = seen[k].refs + tuple(x for x in r.refs if x not in seen[k].refs)
        else:
            seen[k] = Record(**{**r.__dict__})
    return list(seen.values())


def integrity_report(records: list[Record]) -> dict:
    """Resumo de integridade: contagens, chaves duplicadas remanescentes e intervalo de datas."""
    keys = [r.key for r in records]
    return {
        "n": len(records),
        "chaves_duplicadas": len(keys) - len(set(keys)),
        "datas": sorted({r.date for r in records}),
        "satelites": sorted({r.sat for r in records}),
    }
