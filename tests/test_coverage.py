import unittest

from firecal import coverage
from tests.helpers import mk

REQ = {"MODIS": ["Terra", "Aqua"], "VIIRS": ["N20"]}


def many(sat, date, n, prefix):
    return [mk(f"{prefix}{date}:{k}", sat, date, 1800, -10 + k * 1e-3, -48.0) for k in range(n)]


class TestCobertura(unittest.TestCase):
    days = ["2026-07-21", "2026-07-22", "2026-07-23", "2026-07-24", "2026-07-25"]

    def base(self, aqua22):
        recs = []
        for d in self.days:
            recs += many("Terra", d, 20, "T") + many("N20", d, 100, "N")
            recs += many("Aqua", d, aqua22 if d == "2026-07-22" else 30, "A")
        return recs

    def test_dia_normal_e_ok(self):
        st = coverage.sensor_day_status(self.base(30), self.days, ["Terra", "Aqua", "N20"])
        self.assertTrue(all(v["status"] == "OK" for v in st.values()))

    def test_dia_anomalo_analogo_22_07_2026_volume_baixo(self):
        # ANALOGO SINTETICO do caso real (Aqua com ~10 % do volume tipico no dia 22)
        st = coverage.sensor_day_status(self.base(3), self.days, ["Terra", "Aqua", "N20"])
        self.assertEqual(st[("Aqua", "2026-07-22")]["status"], "VOLUME_BAIXO")
        self.assertEqual(st[("N20", "2026-07-22")]["status"], "OK")
        comp = coverage.day_comparability(st, "2026-07-22", REQ)
        self.assertFalse(comp["comparavel"])
        self.assertEqual(comp["motivos"], ["Aqua:VOLUME_BAIXO"])
        self.assertTrue(coverage.day_comparability(st, "2026-07-21", REQ)["comparavel"])

    def test_sem_dados_nao_vira_zero_ok(self):
        recs = [r for r in self.base(30) if not (r.sat == "Aqua" and r.date == "2026-07-23")]
        st = coverage.sensor_day_status(recs, self.days, ["Aqua"])
        self.assertEqual(st[("Aqua", "2026-07-23")]["status"], "SEM_DADOS")
        self.assertEqual(st[("Aqua", "2026-07-23")]["n_janela"], 0)

    def test_limiar_e_parametro(self):
        recs = self.base(10)          # 10/30 = 0,33 do volume tipico
        lo = coverage.sensor_day_status(recs, self.days, ["Aqua"], min_ratio=0.25)
        hi = coverage.sensor_day_status(recs, self.days, ["Aqua"], min_ratio=0.5)
        self.assertEqual(lo[("Aqua", "2026-07-22")]["status"], "OK")
        self.assertEqual(hi[("Aqua", "2026-07-22")]["status"], "VOLUME_BAIXO")

    def test_nao_ha_passagem_inventada(self):
        st = coverage.sensor_day_status(self.base(30), self.days, ["Aqua"])
        for v in st.values():
            self.assertEqual(set(v), {"n_janela", "mediana_ref", "razao", "status"})   # so contagens e estado

    def test_grupo_por_ano(self):
        recs = []
        for d, n in (("2025-07-21", 1000), ("2025-07-22", 1000), ("2026-07-21", 10), ("2026-07-22", 10)):
            recs += many("Aqua", d, n, "A")
        st = coverage.sensor_day_status(recs, ["2025-07-21", "2025-07-22", "2026-07-21", "2026-07-22"], ["Aqua"])
        self.assertTrue(all(v["status"] == "OK" for v in st.values()))   # 2026 comparado com 2026, nao com 2025


if __name__ == "__main__":
    unittest.main()
