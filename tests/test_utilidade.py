import unittest

from firecal import harmonize, utilidade
from firecal.geo import Region
from tests.helpers import mk

REG = Region.rectangle("t", -50.0, -13.0, -45.0, -5.0)


class TestUtilidade(unittest.TestCase):
    def test_spearman_valores_conhecidos(self):
        self.assertAlmostEqual(utilidade.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(utilidade.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertIsNone(utilidade.spearman([1, 2], [1, 2]))          # poucos pontos
        self.assertIsNone(utilidade.spearman([1, 1, 1], [1, 2, 3]))    # sem variancia

    def test_analyze_sobre_dados_sinteticos_roda_e_respeita_a_porta(self):
        days = ["2025-07-21", "2025-07-22", "2025-07-23", "2025-07-24"]
        recs = []
        for k, d in enumerate(days):
            for s, n in (("Terra", 5), ("Aqua", 40 if d != "2025-07-22" else 2), ("N20", 200)):
                for q in range(n):
                    recs.append(mk(f"{s}{d}{q}", s, d, 1800, -6.0 - 0.01 * q - 0.3 * (k % 2), -47.0 - 0.01 * (q % 40)))
        from firecal import coverage
        req = {"MODIS": ["Terra", "Aqua"], "VIIRS": ["N20"]}
        st = coverage.sensor_day_status(recs, days, ["Terra", "Aqua", "N20"])
        comp = {d: coverage.day_comparability(st, d, req) for d in days}
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        daily = harmonize.daily_summary(cds, days, 376, comp, harmonize.shifted_null_k(recs, REG, 0.25, days))
        out = utilidade.analyze(daily, recs, days, req)
        self.assertEqual(out["n_dias_comparaveis"], 3)
        self.assertIn("2025-07-22", out["dias_nao_comparaveis"])
        self.assertIn("0.25", out["sensibilidade_min_ratio_satdias_sinalizados"])


if __name__ == "__main__":
    unittest.main()
