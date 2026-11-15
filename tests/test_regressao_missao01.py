"""Regressao: reexecuta tools/validacao e confere os valores efetivamente confirmados na Missao 01."""
import os
import subprocess
import sys
import tempfile
import unittest

from tests.helpers import DATA_DIR, needs_data

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@needs_data
class TestRegressaoMissao01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "validacao", "run_all.py"),
                            "--data-dir", DATA_DIR, "--work-dir", cls.tmp.name], capture_output=True, text=True,
                           encoding="utf-8")
        assert r.returncode == 0, r.stderr[-1500:]
        cls.out = {}
        d = os.path.join(cls.tmp.name, "saidas")
        for f in os.listdir(d):
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                cls.out[f[:2]] = fh.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def has(self, step, text):
        self.assertIn(text, self.out[step])

    def test_hashes_dos_111_arquivos(self):
        self.has("01", "files 111 hash mismatches/not found 0")

    def test_contagens_de_referencia(self):
        for t in ("2025 MODIS_SP 6890 dentro do Brasil(bioma) 3132",
                  "2025 VIIRS_NOAA20_SP 21827 dentro do Brasil(bioma) 10333",
                  "2026 MODIS_SP 2600 dentro do Brasil(bioma) 1511",
                  "2026 VIIRS_NOAA20_SP 11255 dentro do Brasil(bioma) 6296"):
            self.has("03", t)

    def test_29_dias_com_ambos_os_sensores(self):
        self.has("03", "SP dias com ambos 29")

    def test_dia_anomalo_22_07_2026(self):
        self.has("03", "2026-07-22 Terra=110(30) Aqua=32(6) N20=2169(1167)")
        self.has("03", "2026-07-22 Aqua 2 passagens: 06:06n11 07:43n21")

    def test_reconciliacao_com_o_banco(self):
        self.has("04", "raw unico (sem amostras) 136510")
        self.has("04", "raw nao no tsv 0 tsv nao no raw 0 intersec 136510")
        self.has("04", "('Inside', True): 88046, ('OutsideBrazil', False): 48463")

    def test_delta_t_modal(self):
        self.has("05", "2025 Aqua pares<=1km 7975 classes modais(min,n): [(90, 2427)")
        self.has("05", "2026 Terra pares<=1km 2373 classes modais(min,n): [(-270, 796)")

    def test_taxas_de_candidatos(self):
        self.has("06", "M=4330 com_candidato=961 (22.2%)")
        self.has("06", "M=4330 com_candidato=1589 (36.7%)")
        self.has("06", "M=1550 com_candidato=265 (17.1%)")
        self.has("06", "M=1550 com_candidato=456 (29.4%)")

    def test_variacao_anual(self):
        self.has("07", "('MODIS_SP', 3132, 1511, -51.8), ('VIIRS_NOAA20_SP', 10333, 6296, -39.1)")
        self.has("07", "('MODIS_SP', 2587, 1475, -43.0), ('VIIRS_NOAA20_SP', 8124, 5129, -36.9)")

    def test_tocantins(self):
        self.has("10", "(legacyTO,pipTO): Counter({(False, False): 125034, (True, True): 10194})")
        self.has("11", "2025 1000 Aqua TO 205 com cand 68 33.2%")
        self.has("11", "2026 1000 Aqua TO 306 com cand 90 29.4%")
        self.has("11", "--- 22/07/2026 no TO: {'Terra': 16, 'Aqua': 0, 'N20': 363}")

    def test_controle_viirs(self):
        self.has("12", "N20 N21 375 T60 (433, 223, 51.5")


if __name__ == "__main__":
    unittest.main()
