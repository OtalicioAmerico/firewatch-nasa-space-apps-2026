import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PADROES = [r"[A-Za-z]:" + "\\\\" + r"Users", r"C:" + "\\\\" + r"Trabalho", r"C:" + "\\\\" + r"NASA-Hackathon",
           "/Users/", "ota" + "li", r"password\s*=", r"api[_-]?key\s*=", r"MAP_KEY\s*=\s*['\"]?[A-Za-z0-9]{16,}", r"[0-9a-f]{32}(?<!sha)(?=.{0,0}$)", r"postgres(ql)?://"]


class TestHigiene(unittest.TestCase):
    def test_codigo_sem_caminhos_pessoais_ou_credenciais(self):
        achados = []
        for base in ("firecal", "tools", "config", "tests"):
            for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
                dn[:] = [d for d in dn if d not in (".cache", "__pycache__")]
                for f in fn:
                    if not f.endswith((".py", ".json", ".md")) or f == "test_sem_dados_pessoais.py":
                        continue
                    with open(os.path.join(dp, f), encoding="utf-8") as fh:
                        txt = fh.read()
                    for p in PADROES:
                        if re.search(p, txt, re.I):
                            achados.append((os.path.relpath(os.path.join(dp, f), ROOT), p))
        self.assertEqual(achados, [])

    def test_gitignore_bloqueia_dados_brutos(self):
        with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as fh:
            gi = fh.read()
        for p in ("*.csv", "*.tsv", "*.shp", "tools/validacao/.cache/"):
            self.assertIn(p, gi)

    def test_csv_so_em_resultados(self):
        for dp, dn, fn in os.walk(ROOT):
            dn[:] = [d for d in dn if d not in (".git", ".cache", "__pycache__")]
            for f in fn:
                if f.endswith((".csv", ".tsv", ".shp")):
                    self.assertEqual(os.path.relpath(dp, ROOT).replace(os.sep, "/").split("/")[0], "resultados", f)


if __name__ == "__main__":
    unittest.main()
