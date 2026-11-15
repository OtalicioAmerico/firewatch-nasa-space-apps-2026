"""Testes da Missao 05 sobre os dados reais ja adquiridos e carregados em SQLite. Exigem FIRECAL_BANCO_DIR (diretorio com
bruto_2021_2025.db e resultados_m05.db) e FIRECAL_GRANULOS (json do CMR). Sem eles, sao pulados."""
import csv
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.environ.get("FIRECAL_BANCO_DIR")
GRAN = os.environ.get("FIRECAL_GRANULOS")
pronto = unittest.skipUnless(BANCO and GRAN and os.path.exists(os.path.join(BANCO, "bruto_2021_2025.db")) and os.path.exists(GRAN),
                             "defina FIRECAL_BANCO_DIR e FIRECAL_GRANULOS")


def roda(saida):
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "historico", "calendario.py"),
                        "--bruto", os.path.join(BANCO, "bruto_2021_2025.db"), "--resultados", os.path.join(BANCO, "resultados_m05.db"),
                        "--granulos", GRAN, "--saida", saida], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[-800:]


def sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def le(p):
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pronto
class TestM05Real(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.a = os.path.join(cls.tmp.name, "a")
        cls.b = os.path.join(cls.tmp.name, "b")
        roda(cls.a)
        roda(cls.b)
        cls.D = le(os.path.join(cls.a, "calendario_diario.csv"))
        cls.W = le(os.path.join(cls.a, "calendario_semanal.csv"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_totais_e_integridade_do_banco(self):
        c = sqlite3.connect(f"file:{os.path.join(BANCO, 'bruto_2021_2025.db')}?mode=ro", uri=True)
        self.assertEqual(c.execute("select count(*) from deteccao").fetchone()[0], 1154932)
        self.assertEqual(c.execute("select count(*) from deteccao where em_regiao=1").fetchone()[0], 602856)
        self.assertEqual(c.execute("pragma integrity_check").fetchone()[0], "ok")
        self.assertEqual(c.execute("select count(*) from deteccao d where not exists(select 1 from deteccao_origem o where o.deteccao_id=d.id)").fetchone()[0], 0)
        c.close()

    def test_reprodutibilidade_bit_a_bit(self):
        for n in ("calendario_diario.csv", "calendario_semanal.csv", "calendario_mensal.csv", "calendario_diario.json"):
            self.assertEqual(sha(os.path.join(self.a, n)), sha(os.path.join(self.b, n)), n)

    def test_um_registro_por_dia_e_totais_por_sensor(self):
        self.assertEqual(len(self.D), 1826)
        self.assertEqual(len({x["dia"] for x in self.D}), 1826)
        self.assertEqual(sum(int(x["det_terra"]) + int(x["det_aqua"]) for x in self.D), 122496)
        self.assertEqual(sum(int(x["det_n20"]) for x in self.D), 480360)

    def test_proveniencia_em_todo_dia_com_deteccao(self):
        for x in self.D:
            if int(x["det_terra"]) + int(x["det_aqua"]) + int(x["det_n20"]) > 0:
                self.assertTrue(x["arquivos_origem"], x["dia"])

    def test_versao_modis_e_bloco_preservados(self):
        for x in self.D:
            if x["versao_modis"]:
                self.assertEqual(x["bloco_modis"], "A" if x["versao_modis"] == "6.03" else "B", x["dia"])
                self.assertEqual(x["bloco_modis_fonte"], "observado")
        self.assertEqual({x["bloco_modis"] for x in self.D if x["dia"] < "2023-01-01"}, {"A"})
        self.assertEqual({x["bloco_modis"] for x in self.D if x["dia"] >= "2023-01-01"}, {"B"})
        self.assertNotIn("6.03|61.03", {x["versao_modis"] for x in self.D})

    def test_k_nao_aplicavel_quando_nao_comparavel(self):
        for x in self.D:
            for esc in ("A", "B"):
                if x[f"comparavel_{esc}"] != "True":
                    self.assertEqual(x[f"K_{esc}"], "", x["dia"])
                    self.assertEqual(x[f"K_{esc}_nulo"], "", x["dia"])

    def test_dias_conhecidos_de_cmr_incompleto_e_conflito(self):
        d = {x["dia"]: x for x in self.D}
        self.assertEqual(d["2025-05-14"]["cmr_terra_conflito_firms_cmr"], "21")
        self.assertEqual(d["2025-05-14"]["comparavel_A"], "False")
        self.assertEqual(d["2023-09-30"]["cmr_n20_catalogo_completo"], "False")
        self.assertEqual(d["2023-09-30"]["comparavel_B"], "False")
        self.assertEqual(d["2022-04-05"]["cmr_aqua_catalogo_completo"], "False")
        self.assertNotEqual(d["2022-04-05"]["cmr_aqua_f_media"], "1.0")

    def test_cobertura_parcial_do_aqua_aparece_no_nivel_do_satelite(self):
        parc = [x for x in self.D if float(x["cmr_aqua_f_media"]) < 0.95]
        self.assertGreater(len(parc), 400)
        for x in parc[:50]:
            self.assertGreater(float(x["B_aqua_den"]), 0)

    def test_referencia_exclui_o_ano_avaliado_nas_semanas_reais(self):
        with open(os.path.join(self.a, "calendario_semanal.json"), encoding="utf-8") as fh:
            sem = json.load(fh)                       # JSON guarda a precisao completa (o CSV arredonda a 5 casas)
        por = {}
        for x in sem:
            por.setdefault(x["semana_do_ano"], {})[x["ano"]] = x["B_viirs_extnorm_media"]
        for x in sem:
            if x["B_viirs_extnorm_media"] is None or x["dias"] < 4:
                continue
            v = x["B_viirs_extnorm_media"]
            ref = [vv for y, vv in por[x["semana_do_ano"]].items() if y != x["ano"] and vv is not None]
            esperado = ("REFERENCIA_INSUFICIENTE" if len(ref) < 2 else "ACIMA_DA_REFERENCIA_DISPONIVEL" if v > max(ref)
                        else "ABAIXO_DA_REFERENCIA_DISPONIVEL" if v < min(ref) else "DENTRO_DA_FAIXA_DA_REFERENCIA")
            self.assertEqual(x["ref_B_viirs_extnorm_exclui_ano"], esperado, (x["ano"], x["semana_do_ano"]))

    def test_sem_indicador_combinado_e_sem_linguagem_de_ausencia_de_fogo(self):
        cols = set(self.D[0]) | set(self.W[0])
        self.assertFalse([c for c in cols if c.upper().startswith("R_") or c in ("R", "R_conjunto")])
        for x in self.W[:80]:
            for v in x.values():
                self.assertNotIn("SEM_FOGO", str(v).upper())
                self.assertNotIn("ANOMALIA", str(v).upper())


if __name__ == "__main__":
    unittest.main()
