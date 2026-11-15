import importlib.util
import os
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("sondagem", os.path.join(ROOT, "tools", "aquisicao", "sondagem_firms.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

CSV = ("latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,"
       "bright_ti5,frp,daynight,type\n-10,-48,330,0.4,0.4,2022-08-10,418,N20,VIIRS,n,2.0NRT,290,1.5,N,0\n")


class TestSondagem(unittest.TestCase):
    def test_plano_tem_exatamente_nove_requisicoes_de_cinco_dias(self):
        p = S.plano()
        self.assertEqual(len(p), 9)
        self.assertEqual({(r["produto"], r["inicio"]) for r in p},
                         {(a, b) for a in S.PRODUTOS for b in S.PERIODOS})
        self.assertTrue(all(r["dias"] == 5 for r in p))
        self.assertEqual(len(p) * 5 * S.TRANSACOES_POR_DIA, 90)

    def test_descricao_e_redacao_nao_expoem_a_chave(self):
        chave = "CHAVE_FALSA_DE_TESTE_123"
        r = S.plano()[0]
        self.assertNotIn(chave, S.descrever(r))
        self.assertIn(chave, S.url_dados(chave, r))                 # a URL real a contem...
        self.assertNotIn(chave, S.redigir(S.url_dados(chave, r), chave))   # ...mas a versao redigida nao

    def test_erro_de_rede_nao_vaza_a_url(self):
        chave = "CHAVE_FALSA_DE_TESTE_123"
        with mock.patch("urllib.request.urlopen", side_effect=OSError(S.url_dados(chave, S.plano()[0]))):
            cod, corpo = S._get(S.url_dados(chave, S.plano()[0]), chave)
        self.assertIsNone(cod)
        self.assertNotIn(chave, corpo.decode())

    def test_saida_dentro_do_repositorio_e_recusada(self):
        with self.assertRaises(SystemExit):
            S.validar_saida(os.path.join(ROOT, "resultados", "x"))

    def test_sem_chave_nao_executa(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                S.executar(os.path.join(os.path.expanduser("~"), "fora_do_git_teste"))

    def test_analisar_csv_valido_e_invalido(self):
        info = S.analisar_csv(CSV.encode())
        self.assertEqual(info["linhas"], 1)
        self.assertEqual(info["datas"], {"2022-08-10": 1})
        with self.assertRaises(ValueError):
            S.analisar_csv(b"<html>erro</html>")

    def test_sem_chave_no_codigo(self):
        with open(os.path.join(ROOT, "tools", "aquisicao", "sondagem_firms.py"), encoding="utf-8") as fh:
            txt = fh.read()
        import re
        self.assertIsNone(re.search(r"[\"'][A-Za-z0-9]{32,}[\"']", txt))   # nenhum literal longo (possivel chave)


if __name__ == "__main__":
    unittest.main()
