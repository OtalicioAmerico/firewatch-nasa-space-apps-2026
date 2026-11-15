import unittest

from firecal import matching
from tests.helpers import mk

D500 = 0.0045   # ~500 m em graus de latitude


def v_at(hhmm):
    return [mk("v", "N20", "2025-07-21", hhmm, -10.0, -48.0)]


class TestCandidatas(unittest.TestCase):
    def test_distancia_dentro_e_fora_do_raio(self):
        m = [mk("m", "Aqua", "2025-07-21", 1800, -10.0, -48.0)]
        near = [mk("v", "N20", "2025-07-21", 1700, -10.0 - 0.8 * D500, -48.0)]     # ~400 m
        far = [mk("v", "N20", "2025-07-21", 1700, -10.0 - 1.4 * D500, -48.0)]      # ~700 m
        self.assertEqual(len(matching.find_candidates(m, near, 500, 0, 120)), 1)
        self.assertEqual(len(matching.find_candidates(m, far, 500, 0, 120)), 0)
        self.assertEqual(len(matching.find_candidates(m, far, 1000, 0, 120)), 1)

    def test_janela_de_tempo_fechada_e_sinal(self):
        m = [mk("m", "Aqua", "2025-07-21", 1800, -10.0, -48.0)]
        # dt = MODIS - VIIRS ; 1800 - 1700 = +60 min
        self.assertEqual(len(matching.find_candidates(m, v_at(1700), 100, 60, 150)), 1)   # +60 incluido
        self.assertEqual(len(matching.find_candidates(m, v_at(1530), 100, 60, 150)), 1)   # +150 incluido
        self.assertEqual(len(matching.find_candidates(m, v_at(1529), 100, 60, 150)), 0)   # +151 fora
        self.assertEqual(len(matching.find_candidates(m, v_at(1701), 100, 60, 150)), 0)   # +59 fora
        self.assertEqual(len(matching.find_candidates(m, v_at(1900), 100, 60, 150)), 0)   # dt negativo fora

    def test_atravessa_a_meia_noite(self):
        m = [mk("m", "Aqua", "2025-07-22", 30, -10.0, -48.0)]
        v = [mk("v", "N20", "2025-07-21", 2330, -10.0, -48.0)]
        self.assertEqual(matching.find_candidates(m, v, 100, 0, 120)[0].dt_min, 60)

    def test_multiplos_candidatos_e_relacao_1N(self):
        m = [mk("m", "Aqua", "2025-07-21", 1800, -10.0, -48.0)]
        v = [mk(f"v{k}", "N20", "2025-07-21", 1700, -10.0 - k * 0.001, -48.0) for k in range(3)]
        c = matching.find_candidates(m, v, 500, 0, 120)
        self.assertEqual(len(c), 3)
        self.assertEqual([r["tipo"] for r in matching.relations(c)], ["1:N"])
        self.assertEqual(matching.summarize(m, c)["n_modis_com_candidato"], 1)

    def test_relacoes_1_1_N_1_e_MN(self):
        m1 = mk("m1", "Aqua", "2025-07-21", 1800, -10.0, -48.0)
        v1 = mk("v1", "N20", "2025-07-21", 1700, -10.0, -48.0)
        m2a = mk("m2a", "Aqua", "2025-07-21", 1800, -11.0, -48.0)
        m2b = mk("m2b", "Aqua", "2025-07-21", 1800, -11.001, -48.0)
        v2 = mk("v2", "N20", "2025-07-21", 1700, -11.0005, -48.0)
        m3a = mk("m3a", "Aqua", "2025-07-21", 1800, -12.0, -48.0)
        m3b = mk("m3b", "Aqua", "2025-07-21", 1800, -12.002, -48.0)
        v3a = mk("v3a", "N20", "2025-07-21", 1700, -12.0005, -48.0)
        v3b = mk("v3b", "N20", "2025-07-21", 1700, -12.0015, -48.0)
        c = matching.find_candidates([m1, m2a, m2b, m3a, m3b], [v1, v2, v3a, v3b], 400, 0, 120)
        self.assertEqual(sorted(r["tipo"] for r in matching.relations(c)), ["1:1", "M:N", "N:1"])

    def test_rotulo_candidata_e_sem_probabilidade(self):
        m = [mk("m", "Aqua", "2025-07-21", 1800, -10.0, -48.0)]
        (c,) = matching.find_candidates(m, v_at(1700), 100, 0, 120)
        self.assertEqual(c.label, "CANDIDATA")
        self.assertEqual(set(c.__dataclass_fields__), {"modis_rid", "viirs_rid", "dist_m", "dt_min", "label"})
        for k in matching.summarize(m, [c]):
            self.assertNotIn("prob", k.lower())
            self.assertNotIn("certeza", k.lower())
        self.assertEqual(matching.relations([c])[0]["rotulo"], "CANDIDATA")

    def test_referencias_dos_registros_originais(self):
        m = [mk("arq_m.csv:7", "Aqua", "2025-07-21", 1800, -10.0, -48.0)]
        v = [mk("arq_v.csv:99", "N20", "2025-07-21", 1700, -10.0, -48.0)]
        (c,) = matching.find_candidates(m, v, 100, 0, 120)
        self.assertEqual((c.modis_rid, c.viirs_rid), ("arq_m.csv:7", "arq_v.csv:99"))

    def test_entradas_vazias_e_parametros_invalidos(self):
        self.assertEqual(matching.find_candidates([], [], 500, 0, 120), [])
        m = [mk("m", "Aqua", "2025-07-21", 1800, 0, 0)]
        with self.assertRaises(ValueError):
            matching.find_candidates(m, v_at(1700), 500, 120, 60)
        self.assertIsNone(matching.summarize([], [])["fracao_modis_com_candidato"])

    def test_raio_grande_nao_perde_vizinhos_alem_da_celula_do_indice(self):
        m = [mk("m", "Aqua", "2025-07-21", 1800, -10.0, -48.0)]
        v = [mk("v", "N20", "2025-07-21", 1700, -10.0 - 0.09, -48.0)]    # ~10 km
        self.assertEqual(len(matching.find_candidates(m, v, 12000, 0, 120)), 1)

    def test_determinismo_da_ordem(self):
        m = [mk(f"m{k}", "Aqua", "2025-07-21", 1800, -10.0 - k * 0.0001, -48.0) for k in range(5)]
        v = [mk(f"v{k}", "N20", "2025-07-21", 1700, -10.0 - k * 0.0001, -48.0) for k in range(5)]
        self.assertEqual(matching.find_candidates(m, v, 2000, 0, 120),
                         matching.find_candidates(list(reversed(m)), list(reversed(v)), 2000, 0, 120))


if __name__ == "__main__":
    unittest.main()
