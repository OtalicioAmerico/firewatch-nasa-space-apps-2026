import unittest

from firecal import calendario as K
from firecal import cobertura as C

COR, PAR, IND, SEM = (C.COBERTURA_GEOMETRICA_CORROBORADA, C.COBERTURA_GEOMETRICA_PARCIAL, C.COBERTURA_INDETERMINADA,
                      C.SEM_COBERTURA_GEOMETRICA_CORROBORADA)
U = [(0, k) for k in range(10)]          # universo sintetico de 10 celulas (so para testes)


def cob(**kw):
    f = {c: kw.get("f", 1.0) for c in U}
    cl = {c: kw.get("classe", COR) for c in U}
    return f, cl


class TestVersaoEBloco(unittest.TestCase):
    def test_bloco_modis_por_versao_e_desconhecida(self):
        self.assertEqual(K.bloco_modis("6.03"), "A")
        self.assertEqual(K.bloco_modis("61.03"), "B")
        self.assertEqual(K.bloco_modis("9.99"), "DESCONHECIDO")
        self.assertEqual(K.bloco_modis(None), "DESCONHECIDO")

    def test_semana_do_ano_blocos_fixos(self):
        self.assertEqual(K.semana_do_ano("2021-01-01"), 1)
        self.assertEqual(K.semana_do_ano("2021-01-07"), 1)
        self.assertEqual(K.semana_do_ano("2021-01-08"), 2)
        self.assertEqual(K.semana_do_ano("2021-12-31"), 53)
        self.assertEqual(K.semana_do_ano("2024-12-31"), 53)


class TestCenarios(unittest.TestCase):
    def test_dia_sem_deteccoes_nao_e_sem_fogo_e_preserva_denominador(self):
        f, cl = cob()
        r = K.indicadores_sensor(U, {}, f, cl)
        self.assertEqual(r["B"]["ext_celulas"], 0)
        self.assertEqual(r["B"]["ext_norm"], 0.0)                 # 0 de 10 celulas cobertas: numerador e denominador visiveis
        self.assertEqual(r["B"]["den_cobertura"], 10)
        self.assertIsNone(r["B"]["intens"])                        # intensidade indefinida, nao zero
        self.assertEqual(r["A"]["ext_norm"], 0.0)

    def test_cobertura_parcial_reduz_o_denominador_e_nao_a_contagem(self):
        f = {c: (1.0 if c[1] < 5 else 0.0) for c in U}
        cl = {c: (COR if c[1] < 5 else IND) for c in U}
        det = {(0, 1): 3, (0, 2): 1}
        r = K.indicadores_sensor(U, det, f, cl)
        self.assertEqual(r["B"]["ext_celulas"], 2)
        self.assertEqual(r["B"]["den_cobertura"], 5)
        self.assertAlmostEqual(r["B"]["ext_norm"], 0.4)
        self.assertEqual(r["B"]["celulas_cobertura_desconhecida"], 5)
        self.assertEqual(r["A"]["den_cobertura"], 5)              # A: so corroboradas
        self.assertAlmostEqual(r["A"]["ext_norm"], 0.4)

    def test_celula_parcialmente_coberta_conta_fracao_no_denominador(self):
        f, cl = cob()
        f[(0, 0)] = 0.5
        cl[(0, 0)] = PAR
        r = K.indicadores_sensor(U, {(0, 5): 2}, f, cl)
        self.assertEqual(r["B"]["den_cobertura"], 9.5)
        self.assertNotIn((0, 0), r["corroboradas"])                # parcial nao entra no cenario A

    def test_deteccao_em_celula_sem_cobertura_cmr_conta_como_coberta_em_B_e_e_excluida_em_A(self):
        f, cl = cob(f=0.0, classe=IND)
        det = {(0, 3): 4}
        r = K.indicadores_sensor(U, det, f, cl)
        self.assertEqual(r["B"]["ext_celulas"], 1)
        self.assertEqual(r["B"]["den_cobertura"], 1.0)             # a deteccao prova observacao da celula
        self.assertFalse(r["A"]["valido"])                         # A: cobertura corroborada < 50 % => dia excluido
        self.assertEqual(r["A"]["det_excluidas"], 4)               # exclusao explicita, nao silenciosa
        self.assertIsNone(r["A"]["ext_norm"])

    def test_conflito_firms_cmr_torna_cobertura_indeterminada_e_exclui_do_cenario_A(self):
        f = {c: 1.0 for c in U}
        cl = {c: C.classificar_cobertura(1.0, True, True) for c in U}
        r = K.indicadores_sensor(U, {(0, 1): 1}, f, cl)
        self.assertEqual(r["corroboradas"], set())
        self.assertFalse(r["A"]["valido"])
        self.assertEqual(r["B"]["celulas_cobertura_desconhecida"], 9)   # 9 celulas indeterminadas sem deteccao

    def test_classe_da_familia_melhor_caso(self):
        self.assertEqual(K.classe_familia([IND, COR]), COR)
        self.assertEqual(K.classe_familia([PAR, IND]), PAR)
        self.assertEqual(K.classe_familia([SEM, SEM]), SEM)


class TestConcordancia(unittest.TestCase):
    def test_k_e_nao_aplicavel_em_dia_nao_comparavel_com_diagnostico_separado(self):
        comp = set(U[:5])                                           # 50 % < 80 %
        r = K.concordancia(U, {(0, 1), (0, 2)}, {(0, 2), (0, 3)}, comp)
        self.assertFalse(r["comparavel"])
        self.assertIsNone(r["K"])
        self.assertAlmostEqual(r["K_diagnostico"], 1 / 3)
        self.assertIn("motivo_nao_aplicavel", r)

    def test_k_em_dia_comparavel(self):
        r = K.concordancia(U, {(0, 1), (0, 2)}, {(0, 2), (0, 3)}, set(U))
        self.assertTrue(r["comparavel"])
        self.assertAlmostEqual(r["K"], 1 / 3)
        self.assertEqual((r["A_ambos"], r["A_uniao"], r["so_modis"], r["so_viirs"]), (1, 3, 1, 1))

    def test_k_so_conta_celulas_comparaveis(self):
        comp = set(U) - {(0, 1)}                                   # a celula 1 so tem MODIS e nao e comparavel
        r = K.concordancia(U, {(0, 1), (0, 2)}, {(0, 2)}, comp)
        self.assertEqual(r["K"], 1.0)

    def test_sem_celulas_ativas_k_nao_aplicavel(self):
        r = K.concordancia(U, set(), set(), set(U))
        self.assertIsNone(r["K"])
        self.assertEqual(r["motivo_nao_aplicavel"], "sem celulas ativas")

    def test_controle_de_acaso_so_com_k_aplicavel(self):
        r = K.concordancia(U, {(0, 1)}, {(0, 1)}, set(U), lambda comp, m: 0.1)
        self.assertEqual(r["K_nulo"], 0.1)
        r2 = K.concordancia(U, {(0, 1)}, {(0, 1)}, set(U[:2]), lambda comp, m: 0.1)
        self.assertNotIn("K_nulo", r2)


class TestReferencia(unittest.TestCase):
    por_ano = {2021: 1.0, 2022: 2.0, 2023: 3.0, 2024: 4.0, 2025: 10.0}

    def test_referencia_exclui_o_ano_avaliado(self):
        ref = K.valores_referencia(self.por_ano, 2025, "exclui_ano")
        self.assertNotIn(10.0, ref)
        self.assertEqual(sorted(ref), [1.0, 2.0, 3.0, 4.0])
        self.assertNotIn(self.por_ano[2023], K.valores_referencia(self.por_ano, 2023, "exclui_ano"))

    def test_modo_anteriores_usa_so_anos_anteriores(self):
        self.assertEqual(sorted(K.valores_referencia(self.por_ano, 2025, "anteriores")), [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(K.valores_referencia(self.por_ano, 2021, "anteriores"), [])
        self.assertEqual(sorted(K.valores_referencia(self.por_ano, 2023, "anteriores")), [1.0, 2.0])

    def test_restricao_por_bloco_modis(self):
        ref = K.valores_referencia(self.por_ano, 2025, "exclui_ano", anos_permitidos={2023, 2024, 2025})
        self.assertEqual(sorted(ref), [3.0, 4.0])

    def test_classificacao_com_linguagem_cautelosa(self):
        ref = [1.0, 2.0, 3.0, 4.0]
        self.assertEqual(K.classificar_vs_referencia(10.0, ref), "ACIMA_DA_REFERENCIA_DISPONIVEL")
        self.assertEqual(K.classificar_vs_referencia(0.1, ref), "ABAIXO_DA_REFERENCIA_DISPONIVEL")
        self.assertEqual(K.classificar_vs_referencia(2.5, ref), "DENTRO_DA_FAIXA_DA_REFERENCIA")
        self.assertEqual(K.classificar_vs_referencia(2.5, [1.0]), "REFERENCIA_INSUFICIENTE")
        self.assertEqual(K.classificar_vs_referencia(None, ref), "SEM_DADO_NO_PERIODO")
        for s in ("ACIMA_DA_REFERENCIA_DISPONIVEL", "ABAIXO_DA_REFERENCIA_DISPONIVEL"):
            self.assertNotIn("ANOMALIA", s)

    def test_media_valida_exige_dias_minimos(self):
        self.assertIsNone(K.media_valida([1.0, 2.0, None, None]))
        self.assertEqual(K.media_valida([1.0, 2.0, 3.0, 4.0, None]), 2.5)


def linha_dia(dia, ano, mes, sem, ext_m=0.1, ext_v=0.2, comp=True, k=0.3, bloco="A"):
    b = {"dia": dia, "ano": ano, "mes": mes, "semana_do_ano": sem, "bloco_modis": bloco, "det_terra": 5, "det_aqua": 5, "det_n20": 20,
         "comparavel_A": comp, "comparavel_B": comp, "K_A": k if comp else None}
    for n, e in (("modis", ext_m), ("viirs", ext_v)):
        for esc in ("A", "B"):
            b[f"{esc}_{n}_extnorm"] = e
            b[f"{esc}_{n}_intens"] = 2.0
        b[f"B_{n}_det"] = 10
    for s_ in ("terra", "aqua", "n20"):
        b[f"cmr_{s_}_conflito_firms_cmr"] = 0
    return b


def semana(ano, v_modis, v_viirs):
    xs = [linha_dia(f"{ano}-02-0{d}", ano, 2, 5, ext_m=v_modis, ext_v=v_viirs, bloco=K.bloco_do_ano(ano)) for d in range(1, 5)]
    return K.agregar(xs, lambda x: (x["ano"], x["semana_do_ano"]), ("ano", "semana_do_ano"))


class TestAgregacaoSemanalMensal(unittest.TestCase):
    def test_semana_exige_dias_minimos_e_conta_dias_validos(self):
        xs = [linha_dia(f"2021-01-0{d}", 2021, 1, 1, ext_m=0.1 * d) for d in range(1, 4)]
        s = K.agregar(xs, lambda x: (x["ano"], x["semana_do_ano"]), ("ano", "semana_do_ano"))
        self.assertIsNone(s[0]["B_modis_extnorm_media"])
        self.assertEqual(s[0]["B_modis_dias_validos"], 3)
        xs.append(linha_dia("2021-01-04", 2021, 1, 1, ext_m=0.4))
        s = K.agregar(xs, lambda x: (x["ano"], x["semana_do_ano"]), ("ano", "semana_do_ano"))
        self.assertAlmostEqual(s[0]["B_modis_extnorm_media"], 0.25)

    def test_soma_de_deteccoes_por_sensor_sem_misturar(self):
        xs = [linha_dia(f"2021-01-0{d}", 2021, 1, 1) for d in range(1, 5)]
        s = K.agregar(xs, lambda x: (x["ano"], x["mes"]), ("ano", "mes"))[0]
        self.assertEqual((s["det_terra"], s["det_aqua"], s["det_n20"]), (20, 20, 80))
        self.assertFalse([k for k in s if k.upper().startswith("R_") or k == "R"])

    def test_dias_comparaveis_e_k_nao_aplicavel_na_media(self):
        xs = [linha_dia(f"2021-01-0{d}", 2021, 1, 1, comp=(d != 2), k=0.5) for d in range(1, 5)]
        s = K.agregar(xs, lambda x: (x["ano"], x["mes"]), ("ano", "mes"))[0]
        self.assertEqual(s["dias_comparaveis_A"], 3)
        self.assertEqual(s["K_A_media"], 0.5)

    def test_classificacao_exclui_ano_avaliado_e_separa_blocos_modis(self):
        tab = []
        for y, v in zip(range(2021, 2026), (0.1, 0.2, 0.3, 0.4, 0.9)):
            tab += semana(y, v, v)
        K.classificar_periodos(tab, "semana_do_ano", [2021, 2022, 2023, 2024, 2025])
        r = {x["ano"]: x for x in tab}
        self.assertEqual(r[2025]["ref_B_viirs_extnorm_exclui_ano"], "ACIMA_DA_REFERENCIA_DISPONIVEL")
        self.assertEqual(r[2025]["ref_B_modis_extnorm_exclui_ano_mesmo_bloco"], "ACIMA_DA_REFERENCIA_DISPONIVEL")
        self.assertEqual(r[2025]["n_ref_viirs_exclui_ano"], 4)
        self.assertEqual(r[2021]["ref_B_modis_extnorm_exclui_ano_mesmo_bloco"], "REFERENCIA_INSUFICIENTE")      # so o 2022 no bloco A
        self.assertEqual(r[2021]["ref_B_modis_extnorm_exclui_ano_todos_blocos_SENSIBILIDADE"], "ABAIXO_DA_REFERENCIA_DISPONIVEL")
        self.assertEqual(r[2021]["ref_B_viirs_extnorm_anteriores"], "REFERENCIA_INSUFICIENTE")
        self.assertEqual(r[2025]["ref_B_viirs_extnorm_anteriores"], "ACIMA_DA_REFERENCIA_DISPONIVEL")

    def test_valor_do_ano_avaliado_nunca_entra_na_propria_referencia(self):
        def roda(v2025):
            tab = []
            for y, v in zip(range(2021, 2026), (0.1, 0.2, 0.3, 0.4, v2025)):
                tab += semana(y, v, v)
            K.classificar_periodos(tab, "semana_do_ano", [2021, 2022, 2023, 2024, 2025])
            return {x["ano"]: x["ref_B_viirs_extnorm_exclui_ano"] for x in tab}
        self.assertEqual(roda(0.35)[2025], "DENTRO_DA_FAIXA_DA_REFERENCIA")
        self.assertEqual(roda(5.0)[2025], "ACIMA_DA_REFERENCIA_DISPONIVEL")
        self.assertEqual(roda(5.0)[2025], roda(5.0)[2025])


if __name__ == "__main__":
    unittest.main()
