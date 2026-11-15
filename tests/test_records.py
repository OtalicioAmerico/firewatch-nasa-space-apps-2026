import csv
import os
import tempfile
import unittest

from firecal.records import IntegrityError, deduplicate, integrity_report, parse_row, read_firms_csv, sha256_file
from tests.helpers import mk

HDR = ["latitude", "longitude", "bright_ti4", "scan", "track", "acq_date", "acq_time", "satellite", "instrument",
       "confidence", "version", "bright_ti5", "frp", "daynight", "type"]


def row(**kw):
    base = dict(latitude="-10.0", longitude="-48.0", bright_ti4="330", scan="0.4", track="0.4", acq_date="2025-07-21",
                acq_time="418", satellite="N20", instrument="VIIRS", confidence="n", version="2", bright_ti5="290",
                frp="1.5", daynight="N", type="0")
    base.update(kw)
    return base


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HDR)
        w.writeheader()
        w.writerows(rows)


class TestIntegridade(unittest.TestCase):
    def test_parse_valido(self):
        r = parse_row(row(), "a.csv:2", "VIIRS_NOAA20_SP")
        self.assertEqual((r.sat, r.date, r.lat, r.lon), ("N20", "2025-07-21", -10.0, -48.0))
        self.assertEqual(r.refs, ("a.csv:2",))

    def test_coordenada_fora_do_intervalo(self):
        for bad in (dict(latitude="91"), dict(latitude="-91"), dict(longitude="181"), dict(latitude="x")):
            with self.assertRaises(IntegrityError, msg=str(bad)):
                parse_row(row(**bad), "a:2", "P")

    def test_hora_data_e_satelite_invalidos(self):
        for bad in (dict(acq_time="2460"), dict(acq_time="2500"), dict(acq_date="2025-13-01"), dict(satellite="XYZ")):
            with self.assertRaises(IntegrityError, msg=str(bad)):
                parse_row(row(**bad), "a:2", "P")

    def test_hash_e_numero_de_linhas(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.csv")
            write_csv(p, [row(), row(latitude="-11")])
            h = sha256_file(p)
            self.assertEqual(len(read_firms_csv(p, "t.csv", "P", h, 2)), 2)
            with self.assertRaises(IntegrityError):
                read_firms_csv(p, "t.csv", "P", "0" * 64, 2)
            with self.assertRaises(IntegrityError):
                read_firms_csv(p, "t.csv", "P", h, 3)

    def test_rid_aponta_para_linha_do_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.csv")
            write_csv(p, [row(), row(latitude="-11")])
            rs = read_firms_csv(p, "x/t.csv", "P")
            self.assertEqual([r.rid for r in rs], ["x/t.csv:2", "x/t.csv:3"])

    def test_satelite_N_vira_SNPP(self):
        self.assertEqual(parse_row(row(satellite="N"), "a:2", "P").sat, "SNPP")


class TestDeduplicacao(unittest.TestCase):
    def test_mesma_deteccao_em_dois_arquivos_conta_uma_vez(self):
        a = mk("f1.csv:2", "N20", "2025-07-21", 418, -10.0, -48.0)
        b = mk("f2.csv:9", "N20", "2025-07-21", 418, -10.0, -48.0)
        u = deduplicate([a, b])
        self.assertEqual(len(u), 1)
        self.assertEqual(u[0].refs, ("f1.csv:2", "f2.csv:9"))
        self.assertEqual(integrity_report(u)["chaves_duplicadas"], 0)

    def test_sensores_diferentes_no_mesmo_ponto_nao_sao_unidos(self):
        a = mk("f1:2", "Aqua", "2025-07-21", 1800, -10.0, -48.0)
        b = mk("f2:2", "N20", "2025-07-21", 1800, -10.0, -48.0)
        self.assertEqual(len(deduplicate([a, b])), 2)

    def test_instantes_diferentes_nao_sao_unidos(self):
        a = mk("f1:2", "N20", "2025-07-21", 1800, -10.0, -48.0)
        b = mk("f2:2", "N20", "2025-07-21", 1801, -10.0, -48.0)
        self.assertEqual(len(deduplicate([a, b])), 2)

    def test_deduplicacao_nao_altera_entrada(self):
        a = mk("f1:2", "N20", "2025-07-21", 418, -10.0, -48.0)
        b = mk("f2:2", "N20", "2025-07-21", 418, -10.0, -48.0)
        deduplicate([a, b])
        self.assertEqual(a.refs, ("f1:2",))


if __name__ == "__main__":
    unittest.main()
