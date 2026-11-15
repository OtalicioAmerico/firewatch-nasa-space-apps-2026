import unittest

from firecal import cobertura as C


def quad(lat0, lon0, lat1, lon1, t0=0, t1=5):
    """Granulo sintetico retangular (em lat/lon) de teste; NAO e dado NASA."""
    return C.Granulo(t0, t1, [(lat0, lon0), (lat0, lon1), (lat1, lon1), (lat1, lon0)])


class TestPoligonoEsferico(unittest.TestCase):
    def test_pertinencia_basica(self):
        g = quad(-12.0, -50.0, -6.0, -46.0)
        self.assertTrue(g.convexo)
        self.assertTrue(g.contem(-9.0, -48.0))
        self.assertFalse(g.contem(-9.0, -44.0))
        self.assertFalse(g.contem(-14.0, -48.0))

    def test_parse_poligono_remove_ponto_repetido(self):
        pts = C.parse_poligono("-10 -40 -10 -50 -5 -50 -5 -40 -10 -40")
        self.assertEqual(len(pts), 4)

    def test_tempo_com_tolerancia_de_1_minuto(self):
        g = quad(-12, -50, -6, -46, t0=100, t1=105)
        self.assertTrue(g.contem_no_tempo(99, -9, -48))
        self.assertTrue(g.contem_no_tempo(106, -9, -48))
        self.assertFalse(g.contem_no_tempo(107, -9, -48))
        self.assertFalse(g.contem_no_tempo(100, -9, -44))

    def test_aresta_de_circulo_maximo_difere_do_plano_em_poligonos_grandes(self):
        # aresta longa entre (10,-80) e (10,-20): o circulo maximo curva-se para o polo; pontos entre a reta plana e o arco
        g = C.Granulo(0, 5, [(10, -80), (10, -20), (-10, -20), (-10, -80)])
        self.assertTrue(g.contem(10.5, -50))      # acima da reta plana lat=10, mas dentro do arco esferico (que se curva para o polo)
        self.assertTrue(g.contem(-10.5, -50))     # idem na aresta sul (curva-se para o polo sul)
        self.assertFalse(g.contem(13.0, -50))     # alem do arco
        self.assertFalse(g.contem(-13.0, -50))


class TestFracaoArea(unittest.TestCase):
    def test_celula_inteira_dentro_fora_e_parcial(self):
        g = quad(-10.0, -50.0, -5.0, -47.0)
        self.assertEqual(C.fracao_area_celula([g], -8.0, -49.0, -7.75, -48.75), 1.0)
        self.assertEqual(C.fracao_area_celula([g], -8.0, -45.0, -7.75, -44.75), 0.0)
        f = C.fracao_area_celula([g], -8.0, -47.125, -7.75, -46.875)      # a aresta leste (lon -47) corta ao meio
        self.assertAlmostEqual(f, 0.4, delta=0.2)
        self.assertTrue(0 < f < 1)

    def test_centro_dentro_nao_equivale_a_celula_inteira(self):
        g = quad(-10.0, -50.0, -5.0, -47.0)
        # celula [-47.2, -46.7]: centro em lon -46.95 (fora) mas 40 % da area dentro; outra com centro dentro e ~40 % fora
        c1 = C.fracao_area_celula([g], -8.0, -47.2, -7.5, -46.7)
        c2 = C.fracao_area_celula([g], -8.0, -47.3, -7.5, -46.8)
        self.assertGreater(c1, 0)
        self.assertLess(c1, 1)
        self.assertLess(c2, 0.8)

    def test_sem_granulos_e_zero(self):
        self.assertEqual(C.fracao_area_celula([], -8, -49, -7.75, -48.75), 0.0)

    def test_uniao_de_dois_granulos(self):
        a = quad(-10, -50, -5, -48.0)
        b = quad(-10, -48.0, -5, -46)
        self.assertEqual(C.fracao_area_celula([a, b], -8.0, -48.125, -7.75, -47.875), 1.0)


class TestEstados(unittest.TestCase):
    def test_corroborada_exige_catalogo_completo_e_ausencia_de_conflito(self):
        self.assertEqual(C.classificar_cobertura(1.0, True, False), C.COBERTURA_GEOMETRICA_CORROBORADA)
        self.assertEqual(C.classificar_cobertura(0.96, True, False), C.COBERTURA_GEOMETRICA_CORROBORADA)
        self.assertEqual(C.classificar_cobertura(1.0, False, False), C.COBERTURA_INDETERMINADA)
        self.assertEqual(C.classificar_cobertura(1.0, None, False), C.COBERTURA_INDETERMINADA)
        self.assertEqual(C.classificar_cobertura(1.0, True, True), C.COBERTURA_INDETERMINADA)    # conflito invalida

    def test_parcial_e_sem_cobertura(self):
        self.assertEqual(C.classificar_cobertura(0.5, True, False), C.COBERTURA_GEOMETRICA_PARCIAL)
        self.assertEqual(C.classificar_cobertura(0.94, True, False), C.COBERTURA_GEOMETRICA_PARCIAL)
        self.assertEqual(C.classificar_cobertura(0.0, True, False), C.SEM_COBERTURA_GEOMETRICA_CORROBORADA)

    def test_cmr_incompleto_nao_prova_ausencia_de_observacao(self):
        # catalogo sem evidencia de completude (contagem global baixa): f = 0 NAO vira ausencia comprovada
        self.assertEqual(C.classificar_cobertura(0.0, False, False), C.COBERTURA_INDETERMINADA)
        self.assertEqual(C.classificar_cobertura(0.0, None, False), C.COBERTURA_INDETERMINADA)

    def test_catalogo_completo_por_contagem_global(self):
        self.assertTrue(C.catalogo_completo(289, 289))
        self.assertTrue(C.catalogo_completo(246, 289))
        self.assertFalse(C.catalogo_completo(160, 289))      # como Aqua em 22/07/2026
        self.assertIsNone(C.catalogo_completo(None, 289))

    def test_conflito_firms_cmr_registro_fora_dos_granulos(self):
        g = quad(-12, -50, -6, -46, t0=100, t1=105)
        self.assertTrue(C.registro_corroborado([g], 102, -9, -48))
        self.assertFalse(C.registro_corroborado([g], 102, -9, -44))     # fora do poligono
        self.assertFalse(C.registro_corroborado([g], 300, -9, -48))     # fora do tempo
        self.assertFalse(C.registro_corroborado([], 102, -9, -48))      # catalogo sem granulos (Terra 13-15/05/2025)

    def test_estados_sao_dimensoes_separadas(self):
        self.assertNotEqual(C.DETECCAO_REGISTRADA, C.COBERTURA_GEOMETRICA_PARCIAL)
        nomes = [C.DETECCAO_REGISTRADA, C.COBERTURA_GEOMETRICA_CORROBORADA, C.COBERTURA_GEOMETRICA_PARCIAL, C.CONFLITO_FIRMS_CMR,
                 C.COBERTURA_INDETERMINADA, C.AUSENCIA_DE_DETECCAO_REGISTRADA]
        for n in nomes:
            self.assertNotIn("SEM_FOGO", n)
            self.assertNotIn("NENHUM", n)


if __name__ == "__main__":
    unittest.main()
