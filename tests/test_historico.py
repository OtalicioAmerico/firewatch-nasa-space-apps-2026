import datetime as dt
import importlib.util
import json
import os
import stat
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("historico", os.path.join(ROOT, "tools", "aquisicao", "historico_firms.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

HDR = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight,type\n"


def linha(lat=-10.0, lon=-48.0, dia="2021-01-02", hhmm="1830", sat="Aqua", ver="6.03"):
    return f"{lat},{lon},330,1.0,1.0,{dia},{hhmm},{sat},MODIS,70,{ver},300,10.0,D,0\n"


def corpo_para(req, n=2, sat=None, ver="6.03"):
    sat = sat or ("Aqua" if req["produto"] == "MODIS_SP" else "N20")
    return (HDR + "".join(linha(lat=-10.0 - k * 0.01, dia=req["inicio"], sat=sat, ver=ver) for k in range(n))).encode()


class TestChunks(unittest.TestCase):
    def test_cobertura_exata_sem_sobreposicao(self):
        ch = H.chunks()
        self.assertEqual(len(ch), 366)
        self.assertEqual(sum(n for _, n in ch), 1826)
        self.assertTrue(all(1 <= n <= 5 for _, n in ch))
        self.assertEqual(ch[0], (dt.date(2021, 1, 1), 1))
        prox = ch[0][0]
        for d, n in ch:
            self.assertEqual(d, prox)              # contiguos, sem lacuna nem sobreposicao
            prox = d + dt.timedelta(days=n)
        self.assertEqual(prox, dt.date(2026, 1, 1))
        self.assertIn(dt.date(2022, 8, 10), [d for d, _ in ch])    # alinha com a janela ja obtida na 03.1

    def test_plano_autorizado(self):
        p = H.plano()
        self.assertEqual(len(p), 732)
        self.assertEqual(H.transacoes_previstas(p), 7304)
        self.assertEqual({i["produto"] for i in p}, {"MODIS_SP", "VIIRS_NOAA20_SP"})
        self.assertEqual({i["bbox"] for i in p}, {"-51.0,-13.75,-45.5,-4.9"})


class TestValidacao(unittest.TestCase):
    req = {"produto": "MODIS_SP", "inicio": "2021-01-02", "dias": 5}

    def test_ok_e_resumo(self):
        r = H.validar(HDR.encode() + linha().encode() + linha(lat=-11, sat="Terra").encode(), self.req)
        self.assertEqual((r["linhas"], r["versoes"], r["satelites"]), (2, {"6.03": 2}, {"Aqua": 1, "Terra": 1}))

    def test_arquivo_vazio_so_cabecalho_e_valido(self):
        self.assertEqual(H.validar(HDR.encode(), self.req)["linhas"], 0)

    def test_falhas(self):
        casos = {"fora da caixa": linha(lat=-20.0), "fora do periodo": linha(dia="2021-02-01"),
                 "satelite": linha(sat="N20"), "hora": linha(hhmm="2475")}
        for nome, l in casos.items():
            with self.assertRaises(H.Invalido, msg=nome):
                H.validar(HDR.encode() + l.encode(), self.req)
        with self.assertRaises(H.Invalido):
            H.validar(b"<html>erro</html>", self.req)
        with self.assertRaises(H.Invalido):
            H.validar(b"latitude,longitude\n1,2\n", self.req)

    def test_duplicata_no_arquivo_e_contada(self):
        r = H.validar(HDR.encode() + linha().encode() * 2, self.req)
        self.assertEqual(r["duplicatas_no_arquivo"], 1)


class TestJanela(unittest.TestCase):
    def test_bloqueia_ao_atingir_o_teto_e_libera_depois(self):
        t = [0.0]
        esperas = []

        def dormir(s):
            esperas.append(s)
            t[0] += s
        j = H.Janela(teto=30, relogio=lambda: t[0], dormir=dormir)
        for _ in range(3):
            j.adquirir(10)
        self.assertEqual(esperas, [])
        j.adquirir(10)                          # excederia 30: espera ate sair da janela de 600 s
        self.assertTrue(esperas)
        self.assertGreaterEqual(t[0], 600 - 1)
        self.assertLessEqual(j.soma(), 30)


class FakeNet:
    def __init__(self, falha=None, invalido=None, c429=0):
        self.n = 0
        self.falha, self.invalido, self.c429 = falha, invalido, c429
        self.vistas = []

    def get(self, url, chave):
        self.n += 1
        # a "URL" real contem a chave: extrai produto/data do caminho para montar a resposta
        partes = url.split("/")
        produto, dias, inicio = partes[-4], int(partes[-2]), partes[-1]
        req = {"produto": produto, "inicio": inicio, "dias": dias}
        self.vistas.append(inicio)
        if self.c429 > 0:
            self.c429 -= 1
            return 429, b""
        if self.falha == inicio:
            return 500, b""
        if self.invalido == inicio:
            return 200, b"<html>limite</html>"
        return 200, corpo_para(req)


def itens_mini():
    return [{"label": f"MODIS_SP-2021-01-{d:02d}", "produto": "MODIS_SP", "inicio": f"2021-01-{d:02d}", "dias": 1,
             "bbox": H.BBOX, "ano": 2021, "mes": 1} for d in (1, 2, 3, 4)]


def novo(out, net, **kw):
    return H.Adquiridor(out, "CHAVE_FALSA_PARA_TESTE", get=net.get, status=lambda: {"http": 200, "limite": 5000, "atual": 0},
                        janela=H.Janela(teto=10 ** 6), workers=1, log=lambda *_: None, **kw)


class TestAdquiridor(unittest.TestCase):
    def test_manifesto_arquivos_imutaveis_e_retomada(self):
        with tempfile.TemporaryDirectory() as d:
            net = FakeNet()
            a = novo(d, net)
            a.executar(itens_mini())
            self.assertEqual(net.n, 4)
            m = [json.loads(x) for x in open(os.path.join(d, "manifesto_historico.jsonl"), encoding="utf-8")]
            self.assertEqual(len(m), 4)
            for r in m:
                self.assertTrue(all(k in r for k in ("http", "linhas", "bytes", "ms", "versoes", "sha256", "transacoes", "arquivo")))
                p = os.path.join(d, *r["arquivo"].split("/"))
                self.assertFalse(os.stat(p).st_mode & stat.S_IWRITE)        # somente leitura
            net2 = FakeNet()
            b = novo(d, net2)
            b.executar(itens_mini())
            self.assertEqual(net2.n, 0)                                     # retomada: nada repetido

    def test_retomada_refaz_so_o_que_falta_ou_esta_corrompido(self):
        with tempfile.TemporaryDirectory() as d:
            novo(d, FakeNet()).executar(itens_mini())
            m = [json.loads(x) for x in open(os.path.join(d, "manifesto_historico.jsonl"), encoding="utf-8")]
            alvo = os.path.join(d, *m[2]["arquivo"].split("/"))
            os.chmod(alvo, stat.S_IWRITE)
            os.remove(alvo)                                                 # arquivo sumiu
            net = FakeNet()
            novo(d, net).executar(itens_mini())
            self.assertEqual(net.vistas, ["2021-01-03"])

    def test_para_em_http_500_e_preserva_checkpoints(self):
        with tempfile.TemporaryDirectory() as d:
            net = FakeNet(falha="2021-01-03")
            with mock.patch("time.sleep"):
                with self.assertRaises(H.Parada):
                    novo(d, net).executar(itens_mini())
            m = [json.loads(x) for x in open(os.path.join(d, "manifesto_historico.jsonl"), encoding="utf-8")]
            self.assertEqual([r["inicio"] for r in m], ["2021-01-01", "2021-01-02"])
            self.assertTrue(os.path.exists(os.path.join(d, "erros_historico.jsonl")))

    def test_para_em_resposta_inesperada(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(H.Parada):
                novo(d, FakeNet(invalido="2021-01-02")).executar(itens_mini())

    def test_429_e_tratado_sem_perder_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            net = FakeNet(c429=1)
            with mock.patch("time.sleep"):
                novo(d, net).executar(itens_mini()[:2])
            m = [json.loads(x) for x in open(os.path.join(d, "manifesto_historico.jsonl"), encoding="utf-8")]
            self.assertEqual(len(m), 2)
            self.assertEqual(m[0]["tentativas"], 2)

    def test_nunca_sobrescreve_arquivo_diferente(self):
        with tempfile.TemporaryDirectory() as d:
            it = itens_mini()[:1]
            net = FakeNet()
            req = it[0]
            corpo = corpo_para(req)
            sha = H.sha256(corpo)
            pasta = os.path.join(d, "MODIS_SP", "2021")
            os.makedirs(pasta)
            alvo = os.path.join(pasta, f"2021-01-01_1d_{sha[:32]}.csv")
            with open(alvo, "wb") as fh:
                fh.write(b"conteudo diferente")
            with self.assertRaises(H.Parada):
                novo(d, net).executar(it)
            self.assertEqual(open(alvo, "rb").read(), b"conteudo diferente")

    def test_divergencia_de_custo_para(self):
        with tempfile.TemporaryDirectory() as d:
            net = FakeNet()
            a = H.Adquiridor(d, "CHAVE_FALSA_PARA_TESTE", get=net.get, status=lambda: {"http": 200, "limite": 5000, "atual": 0},
                             janela=H.Janela(teto=10 ** 6), workers=1, log=lambda *_: None)
            a.executar(itens_mini()[:1])
            a.status = lambda: {"http": 200, "limite": 5000, "atual": 900}
            with self.assertRaises(H.Parada):
                a.verificar_custo()

    def test_reaproveitamento_com_proveniencia(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as d:
            req = dict(itens_mini()[0])
            corpo = corpo_para(req)
            sha = H.sha256(corpo)
            os.makedirs(os.path.join(src, "MODIS_SP"))
            with open(os.path.join(src, "MODIS_SP", "x.csv"), "wb") as fh:
                fh.write(corpo)
            man = os.path.join(src, "manifesto_sondagem.jsonl")
            with open(man, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"produto": "MODIS_SP", "inicio": req["inicio"], "dias": 1, "bbox": H.BBOX, "http": 200,
                                     "arquivo": "MODIS_SP/x.csv", "sha256": sha}) + "\n")
                fh.write(json.dumps({"produto": "MODIS_SP", "inicio": "2021-01-02", "dias": 5, "bbox": H.BBOX, "http": 200,
                                     "arquivo": "MODIS_SP/x.csv", "sha256": sha}) + "\n")      # dias diferentes: nao serve
            net = FakeNet()
            novo(d, net).executar(itens_mini()[:2], (src, man))
            self.assertEqual(net.vistas, ["2021-01-02"])                     # so o segundo foi buscado
            m = [json.loads(x) for x in open(os.path.join(d, "manifesto_historico.jsonl"), encoding="utf-8")]
            self.assertEqual(m[0]["origem"], "reutilizado")
            self.assertEqual(m[0]["origem_arquivo"], "MODIS_SP/x.csv")


class TestSeguranca(unittest.TestCase):
    def test_erro_nao_expoe_chave(self):
        chave = "CHAVE_FALSA_PARA_TESTE"
        with tempfile.TemporaryDirectory() as d:
            net = FakeNet(falha="2021-01-01")
            try:
                with mock.patch("time.sleep"):
                    novo(d, net).executar(itens_mini()[:1])
            except H.Parada as e:
                self.assertNotIn(chave, str(e))
            erros = open(os.path.join(d, "erros_historico.jsonl"), encoding="utf-8").read()
            self.assertNotIn(chave, erros)


if __name__ == "__main__":
    unittest.main()
