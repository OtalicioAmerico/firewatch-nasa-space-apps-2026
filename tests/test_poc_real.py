"""Testes com dados NASA REAIS (Tocantins, 21-25/07/2025 e 2026). Exigem NASA_DATA_DIR."""
import csv
import json
import os
import tempfile
import unittest

from firecal import pipeline
from tests.helpers import DATA_DIR, needs_data

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config", "poc_tocantins.json")
COMMITTED = os.path.join(ROOT, "resultados", "missao02")


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@needs_data
class TestPoCReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = os.path.join(cls.tmp.name, "a")
        cls.res = pipeline.run(pipeline.load_config(CFG), DATA_DIR, cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _csv(self, name):
        with open(os.path.join(self.out, name), encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            for k in ("n_na_regiao", "n_janela_aquisicao"):
                if k in r:
                    r[k] = int(r[k])
        return rows

    def test_integridade_dos_registros(self):
        i = self.res["integridade"]
        self.assertEqual(i["registros_brutos"], 6890 + 2600 + 21827 + 11255 + 11255)
        self.assertEqual(i["duplicatas_removidas"], 11255)       # os dois arquivos NOAA-20/2026 sao identicos
        self.assertEqual(i["registros_unicos_no_periodo"], 6890 + 2600 + 21827 + 11255)   # contagens de referencia
        self.assertEqual(i["chaves_duplicadas_apos_dedup"], 0)

    def test_contagens_em_tocantins_reproduzem_a_missao_01(self):
        rows = {(r["satelite"], r["dia"]): r["n_na_regiao"] for r in self._csv("sensor_dia.csv")}
        aqua = {y: sum(v for (s, d), v in rows.items() if s == "Aqua" and d[:4] == y) for y in ("2025", "2026")}
        n20 = sum(v for (s, d), v in rows.items() if s == "N20")
        self.assertEqual(aqua, {"2025": 205, "2026": 306})
        self.assertEqual(n20, 3165)

    def test_dia_anomalo_22_07_2026(self):
        res = self.res
        self.assertEqual(res["status_sensor_dia"]["Aqua|2026-07-22"], "VOLUME_BAIXO")
        self.assertEqual(res["status_sensor_dia"]["N20|2026-07-22"], "OK")
        self.assertFalse(res["comparabilidade"]["2026-07-22"]["comparavel"])
        sd = {(r["satelite"], r["dia"]): r for r in self._csv("sensor_dia.csv")}
        self.assertEqual(sd[("Aqua", "2026-07-22")]["n_janela_aquisicao"], 32)
        self.assertEqual(sd[("Aqua", "2026-07-22")]["n_na_regiao"], 0)     # Tocantins: nenhum registro Aqua
        day = {r["dia"]: r for r in res["celulas"]["0.25"]["daily"]}["2026-07-22"]
        self.assertIsNone(day["R_conjunto"])
        self.assertIsNone(day["I_MODIS"])
        est = res["celulas"]["0.25"]["estados_por_dia"]["2026-07-22"]
        self.assertNotIn("SO_MODIS", est)
        self.assertNotIn("SO_VIIRS", est)
        self.assertEqual(sum(est.values()), day["A_UNIAO"])       # dia mantido, nada removido nem corrigido

    def test_somente_o_dia_anomalo_e_nao_comparavel(self):
        comp = self.res["comparabilidade"]
        self.assertEqual([d for d, v in comp.items() if not v["comparavel"]], ["2026-07-22"])

    def test_celulas_dia_referencia(self):
        daily = {r["dia"]: r for r in self.res["celulas"]["0.25"]["daily"]}
        d = daily["2025-07-21"]
        self.assertEqual((d["A_MODIS"], d["A_VIIRS"], d["A_AMBOS"], d["A_UNIAO"]), (26, 66, 22, 70))
        self.assertEqual(self.res["celulas"]["0.25"]["universo"], 376)

    def test_candidatas_reproduzem_a_missao_01(self):
        por = self.res["correspondencia"]["por_raio"]
        got = {(R, y): (e["n_modis"], e["n_modis_com_candidato"]) for R, ys in por.items() for y, e in ys.items()}
        self.assertEqual(got[("500", "2025")], (205, 31))
        self.assertEqual(got[("500", "2026")], (306, 53))
        self.assertEqual(got[("1000", "2025")], (205, 68))
        self.assertEqual(got[("1000", "2026")], (306, 90))
        self.assertEqual(got[("3000", "2025")], (205, 104))
        self.assertEqual(got[("3000", "2026")], (306, 130))
        self.assertEqual(por["500"]["2025"]["relacoes"], {"1:1": 15, "1:N": 12, "N:1": 0, "M:N": 2})

    def test_reprodutibilidade_bit_a_bit(self):
        out2 = os.path.join(self.tmp.name, "b")
        pipeline.run(pipeline.load_config(CFG), DATA_DIR, out2)
        m1 = _load(os.path.join(self.out, "manifesto_execucao.json"))
        m2 = _load(os.path.join(out2, "manifesto_execucao.json"))
        self.assertEqual(m1["saidas_sha256"], m2["saidas_sha256"])
        self.assertGreater(len(m1["saidas_sha256"]), 8)

    def test_resultados_versionados_batem_com_a_execucao(self):
        path = os.path.join(COMMITTED, "manifesto_execucao.json")
        if not os.path.exists(path):
            self.skipTest("resultados/missao02 ainda nao gerado")
        com = _load(path)["saidas_sha256"]
        mine = _load(os.path.join(self.out, "manifesto_execucao.json"))["saidas_sha256"]
        self.assertEqual(com, mine)


if __name__ == "__main__":
    unittest.main()
