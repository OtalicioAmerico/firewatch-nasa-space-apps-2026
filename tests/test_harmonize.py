import unittest

from firecal import harmonize
from firecal.geo import Region
from firecal.records import deduplicate
from tests.helpers import mk

REG = Region.rectangle("t", -50.0, -13.0, -45.0, -5.0)
OK = {"comparavel": True, "motivos": []}
BAD = {"comparavel": False, "motivos": ["Aqua:VOLUME_BAIXO"]}


class TestEstados(unittest.TestCase):
    def test_todos_os_estados(self):
        f = harmonize.cell_state
        self.assertEqual(f(True, True, True), "AMBOS")
        self.assertEqual(f(True, True, False), "AMBOS")
        self.assertEqual(f(True, False, True), "SO_MODIS")
        self.assertEqual(f(False, True, True), "SO_VIIRS")
        self.assertEqual(f(True, False, False), "MODIS_SEM_COMPARACAO")
        self.assertEqual(f(False, True, False), "VIIRS_SEM_COMPARACAO")
        self.assertEqual(f(False, False, True), "SEM_DETECCAO_REGISTRADA")
        self.assertEqual(f(False, False, False), "COBERTURA_INDETERMINADA")

    def test_nenhum_estado_diz_nenhum_fogo(self):
        for s in harmonize.STATES:
            self.assertNotIn("NENHUM", s.upper())
            self.assertNotIn("SEM_FOGO", s.upper())


class TestAgrupamento(unittest.TestCase):
    def test_agrupa_por_celula_e_dia(self):
        recs = [mk("a", "Aqua", "2025-07-21", 1800, -10.10, -48.10),
                mk("b", "N20", "2025-07-21", 1700, -10.20, -48.20),     # mesma celula de 0,25 grau
                mk("c", "N20", "2025-07-21", 1700, -10.60, -48.20),     # outra celula
                mk("d", "N20", "2025-07-22", 1700, -10.20, -48.20)]     # outro dia
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        self.assertEqual(len(cds), 3)
        k = ("2025-07-21", -41, -193)
        self.assertEqual(dict(cds[k].counts), {"Aqua": 1, "N20": 1})
        self.assertTrue(cds[k].has_modis and cds[k].has_viirs)

    def test_dia_vem_de_acq_date_utc(self):
        recs = [mk("a", "N20", "2025-07-21", 2359, -10.2, -48.2), mk("b", "N20", "2025-07-22", 0, -10.2, -48.2)]
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        self.assertEqual(sorted(k[0] for k in cds), ["2025-07-21", "2025-07-22"])

    def test_limites_geograficos_filtra_fora_da_regiao(self):
        recs = [mk("in", "N20", "2025-07-21", 1700, -10.0, -48.0),
                mk("out_lon", "N20", "2025-07-21", 1700, -10.0, -44.0),
                mk("out_lat", "N20", "2025-07-21", 1700, -4.0, -48.0)]
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        self.assertEqual(sum(sum(c.counts.values()) for c in cds.values()), 1)

    def test_celula_na_fronteira_conta_so_o_que_esta_dentro(self):
        # a regiao termina em lat -5,0; a celula [-5,0; -4,75) tem um ponto dentro e outro fora
        recs = [mk("in", "N20", "2025-07-21", 1700, -5.05, -48.0), mk("out", "N20", "2025-07-21", 1700, -4.95, -48.0)]
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        self.assertEqual(sum(sum(c.counts.values()) for c in cds.values()), 1)


class TestSemSomasDuplicadas(unittest.TestCase):
    def test_deteccao_repetida_em_dois_arquivos_e_contada_uma_vez(self):
        a = mk("f1:2", "N20", "2025-07-21", 1700, -10.2, -48.2)
        b = mk("f2:2", "N20", "2025-07-21", 1700, -10.2, -48.2)
        cds = harmonize.build_cell_days(deduplicate([a, b]), REG, 0.25)
        (cd,) = cds.values()
        self.assertEqual(cd.counts["N20"], 1)
        self.assertEqual(len(cd.refs), 1)
        self.assertIn("f1:2;f2:2", cd.refs[0])      # origem das duas copias preservada

    def test_contagens_de_sensores_nao_sao_somadas(self):
        recs = [mk("a", "Aqua", "2025-07-21", 1800, -10.1, -48.1), mk("b", "N20", "2025-07-21", 1700, -10.2, -48.2)]
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        r = harmonize.daily_summary(cds, ["2025-07-21"], 100, {"2025-07-21": OK})[0]
        self.assertEqual((r["A_MODIS"], r["A_VIIRS"], r["A_AMBOS"], r["A_UNIAO"]), (1, 1, 1, 1))   # uniao = 1, nao 2
        self.assertLessEqual(r["A_UNIAO"], r["A_MODIS"] + r["A_VIIRS"])
        for k in r:
            self.assertNotIn("soma", k.lower())

    def test_uniao_igual_a_soma_so_quando_disjuntos(self):
        recs = [mk("a", "Aqua", "2025-07-21", 1800, -10.1, -48.1), mk("b", "N20", "2025-07-21", 1700, -12.2, -46.2)]
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        r = harmonize.daily_summary(cds, ["2025-07-21"], 100, {"2025-07-21": OK})[0]
        self.assertEqual((r["A_AMBOS"], r["A_UNIAO"], r["SO_MODIS"], r["SO_VIIRS"]), (0, 2, 1, 1))
        self.assertEqual(r["K_jaccard"], 0.0)


class TestIndicador(unittest.TestCase):
    def setUp(self):
        days = ["2025-07-21", "2025-07-22", "2025-07-23"]
        recs = []
        # dia 21 e 22: M = 2 celulas, V = 2 celulas, 1 em comum; dia 23: M = 1, V = 2
        for d, p in ((days[0], "a"), (days[1], "b")):
            recs += [mk(p + "1", "Aqua", d, 1800, -10.1, -48.1), mk(p + "2", "Aqua", d, 1800, -11.1, -48.1),
                     mk(p + "3", "N20", d, 1700, -10.1, -48.1), mk(p + "4", "N20", d, 1700, -12.1, -48.1)]
        recs += [mk("c1", "Aqua", days[2], 1800, -10.1, -48.1),
                 mk("p1", "N20", days[2], 1700, -10.1, -48.1), mk("p2", "N20", days[2], 1700, -12.1, -48.1)]
        self.days = days
        self.cds = harmonize.build_cell_days(recs, REG, 0.25)

    def test_jaccard_e_indices(self):
        comp = {d: OK for d in self.days}
        rows = harmonize.daily_summary(self.cds, self.days, 100, comp)
        self.assertAlmostEqual(rows[0]["K_jaccard"], 1 / 3)
        self.assertEqual(rows[0]["A_UNIAO"], 3)
        # mediana de A_MODIS = 2 (2,2,1) -> I_MODIS no dia 23 = 0,5; A_VIIRS = 2,2,2 -> I_VIIRS = 1
        self.assertEqual(rows[2]["I_MODIS"], 0.5)
        self.assertEqual(rows[2]["I_VIIRS"], 1.0)
        self.assertEqual(rows[2]["R_conjunto"], 0.75)       # media dos dois indices, nunca soma de contagens

    def test_dia_nao_comparavel_nao_gera_indice_nem_entra_na_mediana(self):
        comp = {self.days[0]: OK, self.days[1]: BAD, self.days[2]: OK}
        rows = harmonize.daily_summary(self.cds, self.days, 100, comp)
        self.assertIsNone(rows[1]["I_MODIS"])
        self.assertIsNone(rows[1]["R_conjunto"])
        self.assertEqual(rows[0]["ref_mediana_A_MODIS"], 1.5)   # mediana de {2, 1}
        self.assertEqual(rows[1]["motivos_nao_comparavel"], "Aqua:VOLUME_BAIXO")
        self.assertIsNotNone(rows[1]["K_jaccard"])               # K continua reportado, mas rotulado nao comparavel

    def test_estado_em_dia_nao_comparavel_nao_alega_exclusividade(self):
        comp = {d: BAD for d in self.days}
        rows = harmonize.cell_day_rows(self.cds, REG, 0.25, comp)
        estados = {r["estado"] for r in rows}
        self.assertTrue(estados <= {"AMBOS", "MODIS_SEM_COMPARACAO", "VIIRS_SEM_COMPARACAO"})

    def test_sem_registros_em_dia_nao_comparavel_e_indeterminado(self):
        r = harmonize.daily_summary({}, ["2025-07-21"], 100, {"2025-07-21": BAD})[0]
        self.assertEqual((r["A_MODIS"], r["A_VIIRS"], r["A_UNIAO"]), (0, 0, 0))
        self.assertIsNone(r["K_jaccard"])                        # indefinido, nao 0 nem 1
        self.assertEqual(harmonize.cell_state(False, False, r["comparavel"]), "COBERTURA_INDETERMINADA")

    def test_universo_inclui_celulas_sem_deteccao(self):
        uni = harmonize.cell_universe(REG, 0.25, self.cds)
        self.assertGreater(len(uni), len({(c.i, c.j) for c in self.cds.values()}))

    def test_nulo_deslocado_e_menor_que_observado_quando_ha_correspondencia(self):
        recs = []
        for k in range(20):
            lat = -12.0 - 0.05 * k
            recs.append(mk(f"m{k}", "Aqua", "2025-07-21", 1800, lat, -48.0))
            recs.append(mk(f"n{k}", "N20", "2025-07-21", 1700, lat, -48.0))
        n = harmonize.shifted_null_k(recs, REG, 0.25, ["2025-07-21"])["2025-07-21"]
        cds = harmonize.build_cell_days(recs, REG, 0.25)
        k = harmonize.daily_summary(cds, ["2025-07-21"], 100, {"2025-07-21": OK})[0]["K_jaccard"]
        self.assertEqual(k, 1.0)
        self.assertLess(n, k)


if __name__ == "__main__":
    unittest.main()
