"""Auxiliares de teste. Os registros criados aqui sao SINTETICOS e servem so para testar logica; nunca sao
resultados cientificos nem dados NASA."""
import datetime as dt
import os
import unittest

from firecal.records import EPOCH, Record

DATA_DIR = os.environ.get("NASA_DATA_DIR")
needs_data = unittest.skipUnless(DATA_DIR and os.path.isdir(DATA_DIR),
                                 "defina NASA_DATA_DIR para rodar testes com dados NASA reais")


def minutes(date: str, hhmm: int) -> int:
    d = dt.datetime.strptime(date, "%Y-%m-%d") + dt.timedelta(hours=hhmm // 100, minutes=hhmm % 100)
    return int((d - EPOCH).total_seconds() // 60)


def mk(rid, sat, date, hhmm, lat, lon, product=None):
    product = product or ("MODIS_SP" if sat in ("Terra", "Aqua") else "VIIRS_NOAA20_SP")
    return Record(rid=rid, sat=sat, t=minutes(date, hhmm), date=date, lat=lat, lon=lon, frp=1.0, conf="n",
                  scan=1.0, track=1.0, dn="D", product=product, refs=(rid,))
