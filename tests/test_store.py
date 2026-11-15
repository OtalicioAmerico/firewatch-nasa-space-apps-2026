import hashlib
import json
import os
import tempfile
import unittest

from firecal import store
from firecal.geo import Region

HDR = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight,type\n"


def linha(lat, lon, dia="2021-01-02", hhmm="1830", sat="Aqua", ver="6.03"):
    return f"{lat},{lon},330,1.0,1.0,{dia},{hhmm},{sat},MODIS,70,{ver},300,10.0,D,0\n"


def escreve(d, nome, linhas, produto="MODIS_SP", inicio="2021-01-02"):
    p = os.path.join(d, nome)
    corpo = (HDR + "".join(linhas)).encode()
    with open(p, "wb") as fh:
        fh.write(corpo)
    return {"label": nome, "produto": produto, "inicio": inicio, "dias": 5, "bbox": "-51.0,-13.75,-45.5,-4.9", "status": "ok",
            "http": 200, "bytes": len(corpo), "linhas": len(linhas), "sha256": hashlib.sha256(corpo).hexdigest(), "arquivo": nome,
            "versoes": {}, "origem": "nasa_api"}


def manifesto(d, regs):
    p = os.path.join(d, "man.jsonl")
    with open(p, "w", encoding="utf-8") as fh:
        for r in regs:
            fh.write(json.dumps(r) + "\n")
    return p


class TestStore(unittest.TestCase):
    def test_importacao_idempotente_e_verificavel(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            a = escreve(d, "a.csv", [linha(-10.0, -48.0), linha(-10.1, -48.1)])
            m = manifesto(d, [a])
            c = store.abrir(os.path.join(d, "bruto.db"))
            r1 = store.importar_manifesto(c, d, m, log=lambda *_: None)
            r2 = store.importar_manifesto(c, d, m, log=lambda *_: None)
            self.assertEqual((r1["linhas_novas"], r1["duplicatas"]), (2, 0))
            self.assertEqual((r2["arquivos_novos"], r2["arquivos_ja_importados"], r2["linhas_novas"]), (0, 1, 0))
            v = store.verificar(c)
            self.assertEqual(v, {"deteccoes": 2, "arquivos": 1, "deteccoes_sem_origem": 0, "arquivos_com_contagem_divergente": 0})
            c.close()

    def test_duplicata_entre_arquivos_une_registro_e_guarda_ambas_as_origens(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            a = escreve(d, "a.csv", [linha(-10.0, -48.0), linha(-10.1, -48.1)])
            b = escreve(d, "b.csv", [linha(-10.0, -48.0), linha(-10.2, -48.2)])
            c = store.abrir(os.path.join(d, "bruto.db"))
            r = store.importar_manifesto(c, d, manifesto(d, [a, b]), log=lambda *_: None)
            self.assertEqual((r["linhas_lidas"], r["linhas_novas"], r["duplicatas"]), (4, 3, 1))
            self.assertEqual(c.execute("select count(*) from deteccao").fetchone()[0], 3)
            self.assertEqual(c.execute("select count(*) from deteccao_origem").fetchone()[0], 4)
            n = c.execute("select count(*) from (select deteccao_id from deteccao_origem group by 1 having count(*)=2)").fetchone()[0]
            self.assertEqual(n, 1)
            self.assertEqual(store.verificar(c)["arquivos_com_contagem_divergente"], 0)

    def test_duplicata_dentro_do_mesmo_arquivo(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            a = escreve(d, "a.csv", [linha(-10.0, -48.0), linha(-10.0, -48.0)])
            c = store.abrir(os.path.join(d, "bruto.db"))
            r = store.importar_manifesto(c, d, manifesto(d, [a]), log=lambda *_: None)
            self.assertEqual((r["linhas_novas"], r["duplicatas"]), (1, 1))
            self.assertEqual(store.verificar(c)["arquivos_com_contagem_divergente"], 0)

    def test_versao_preservada_e_colecao_inferida_separada(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            a = escreve(d, "a.csv", [linha(-10.0, -48.0, ver="6.03")])
            b = escreve(d, "b.csv", [linha(-10.5, -48.5, dia="2023-08-12", ver="61.03")], inicio="2023-08-12")
            x = escreve(d, "x.csv", [linha(-10.7, -48.7, ver="9.99")])
            c = store.abrir(os.path.join(d, "bruto.db"))
            store.importar_manifesto(c, d, manifesto(d, [a, b, x]), log=lambda *_: None)
            got = dict(c.execute("select versao_bruta, colecao_inferida from deteccao").fetchall())
            self.assertEqual(got, {"6.03": "C6", "61.03": "C6.1", "9.99": "DESCONHECIDA"})
            self.assertEqual(c.execute("select min(confirmada) from mapa_versao").fetchone()[0], 0)   # nada confirmado

    def test_sha_divergente_recusa_importar(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            a = escreve(d, "a.csv", [linha(-10.0, -48.0)])
            a["sha256"] = "0" * 64
            c = store.abrir(os.path.join(d, "bruto.db"))
            with self.assertRaises(ValueError):
                store.importar_manifesto(c, d, manifesto(d, [a]), log=lambda *_: None)

    def test_regiao_e_celula(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            a = escreve(d, "a.csv", [linha(-10.0, -48.0), linha(-10.0, -44.0)])
            c = store.abrir(os.path.join(d, "bruto.db"))
            reg = Region.rectangle("t", -50.0, -13.0, -45.0, -5.0)
            store.importar_manifesto(c, d, manifesto(d, [a]), regiao=reg, log=lambda *_: None)
            em = dict(c.execute("select lon, em_regiao from deteccao").fetchall())
            self.assertEqual(em, {-48.0: 1, -44.0: 0})
            self.assertEqual(c.execute("select cel_i, cel_j from deteccao where lon=-48.0").fetchone(), (-40, -192))


if __name__ == "__main__":
    unittest.main()
