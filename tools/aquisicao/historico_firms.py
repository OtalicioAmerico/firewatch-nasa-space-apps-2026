"""Aquisicao historica FIRMS (Missao 04, Etapa 1): Tocantins, MODIS_SP + VIIRS_NOAA20_SP, 2021-01-01 a 2025-12-31.

Escopo fixo (nada alem disso e adquirido): 2 produtos x 1.826 dias; janelas de ate 5 dias sem sobreposicao.
Seguranca da credencial: MAP_KEY so de FIRMS_MAP_KEY; a URL (que contem a chave) nunca e impressa, gravada ou
incluida em excecoes; saida fora do repositorio Git.

Garantias: checkpoints persistentes (manifesto JSONL, uma linha por resposta validada); retomada automatica sem repetir o
que ja foi validado; arquivos originais imutaveis (somente leitura) e nunca sobrescritos; controle de taxa conservador
(janela deslizante de 10 min com teto local de 3.000 transacoes, 60 % do limite de 5.000); parada em erro, resposta
inesperada, falha de validacao, divergencia de custo ou HTTP 429 persistente.

Uso:
  python -I tools/aquisicao/historico_firms.py --plan
  python -I tools/aquisicao/historico_firms.py --run --out <dir fora do Git> [--workers 3]
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import stat
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sondagem_firms as S  # noqa: E402  (reaproveita BASE, _get, status_chave, url_*, redigir)

BBOX = S.BBOX
LON0, LAT0, LON1, LAT1 = (-51.0, -13.75, -45.5, -4.9)
PRODUTOS = ["MODIS_SP", "VIIRS_NOAA20_SP"]
INICIO = dt.date(2021, 1, 1)
FIM = dt.date(2025, 12, 31)
SATELITES = {"MODIS_SP": {"Terra", "Aqua"}, "VIIRS_NOAA20_SP": {"N20"}}
TETO_LOCAL = 3000           # transacoes por janela de 10 min (60 % do limite NASA)
MAX_LINHAS = 100000
REQ_FIELDS = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "frp", "version", "confidence", "scan",
              "track", "daynight"}
RAIZ_REPO = S.RAIZ_REPO


def chunks():
    """[(inicio, dias)]: 1 dia (01/01/2021) + janelas de 5 dias a partir de 02/01/2021 ate 31/12/2025, sem sobreposicao.
    O primeiro chunk curto alinha a grade a 2022-08-10, janela ja obtida na Missao 03.1 (reaproveitavel)."""
    out = [(INICIO, 1)]
    d = INICIO + dt.timedelta(days=1)
    while d <= FIM:
        n = min(5, (FIM - d).days + 1)
        out.append((d, n))
        d += dt.timedelta(days=n)
    return out


def plano():
    return [{"label": f"{p}-{d.isoformat()}", "produto": p, "inicio": d.isoformat(), "dias": n, "bbox": BBOX,
             "ano": d.year, "mes": d.month} for p in PRODUTOS for d, n in chunks()]


def transacoes_previstas(itens):
    return sum(i["dias"] for i in itens) * S.TRANSACOES_POR_DIA


# ---------------- validacao ----------------
class Invalido(Exception):
    pass


def validar(corpo: bytes, req: dict) -> dict:
    """Valida uma resposta CSV. Levanta Invalido em inconsistencia; devolve resumo."""
    try:
        texto = corpo.decode("utf-8")
    except UnicodeDecodeError as e:
        raise Invalido("corpo nao e UTF-8") from e
    if not texto.lstrip().lower().startswith("latitude,"):
        raise Invalido("corpo nao parece CSV FIRMS")
    rd = csv.DictReader(io.StringIO(texto))
    if not REQ_FIELDS <= set(rd.fieldnames or []):
        raise Invalido("campos obrigatorios ausentes")
    d0 = dt.date.fromisoformat(req["inicio"])
    d1 = d0 + dt.timedelta(days=req["dias"] - 1)
    permitidos = SATELITES[req["produto"]]
    n = 0
    chaves = set()
    dup = 0
    versoes = collections.Counter()
    sats = collections.Counter()
    datas = collections.Counter()
    for r in rd:
        n += 1
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
            dia = dt.date.fromisoformat(r["acq_date"])
            hh = int(r["acq_time"])
            float(r["frp"]) if r["frp"] != "" else None
            float(r["scan"])
            float(r["track"])
        except Exception as e:                                       # noqa: BLE001
            raise Invalido(f"linha {n + 1} com valor invalido") from e
        if not (LON0 <= lon <= LON1 and LAT0 <= lat <= LAT1):
            raise Invalido(f"linha {n + 1} fora da caixa")
        if not (d0 <= dia <= d1):
            raise Invalido(f"linha {n + 1} fora do periodo")
        if not (0 <= hh // 100 <= 23 and 0 <= hh % 100 <= 59):
            raise Invalido(f"linha {n + 1} com hora invalida")
        if r["satellite"] not in permitidos:
            raise Invalido(f"linha {n + 1} com satelite inesperado")
        k = (r["satellite"], r["acq_date"], r["acq_time"], r["latitude"], r["longitude"])
        if k in chaves:
            dup += 1
        chaves.add(k)
        versoes[r["version"]] += 1
        sats[r["satellite"]] += 1
        datas[r["acq_date"]] += 1
    if n > MAX_LINHAS:
        raise Invalido("linhas acima do limite de seguranca")
    return {"linhas": n, "duplicatas_no_arquivo": dup, "versoes": dict(versoes), "satelites": dict(sats),
            "datas": dict(sorted(datas.items()))}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _bytes(p: str) -> bytes:
    with open(p, "rb") as fh:
        return fh.read()


def _linhas(p: str):
    with open(p, encoding="utf-8") as fh:
        return fh.read().splitlines()


# ---------------- controle de taxa ----------------
class Janela:
    """Janela deslizante de 10 min com teto local de transacoes."""

    def __init__(self, teto=TETO_LOCAL, relogio=time.time, dormir=time.sleep):
        self.teto, self.relogio, self.dormir = teto, relogio, dormir
        self.ev = collections.deque()
        self.lock = threading.Lock()

    def soma(self):
        agora = self.relogio()
        while self.ev and agora - self.ev[0][0] >= 600:
            self.ev.popleft()
        return sum(t for _, t in self.ev)

    def adquirir(self, tokens: int):
        while True:
            with self.lock:
                if self.soma() + tokens <= self.teto:
                    self.ev.append((self.relogio(), tokens))
                    return
                espera = max(1.0, 600 - (self.relogio() - self.ev[0][0]))
            self.dormir(min(espera, 30))


# ---------------- adquiridor ----------------
class Parada(Exception):
    pass


class Adquiridor:
    def __init__(self, out, chave, get=S._get, status=None, janela=None, workers=3, log=print):
        self.out = out
        self.chave = chave
        self.get = get
        self.status = status or (lambda: S.status_chave(chave))
        self.janela = janela or Janela()
        self.workers = workers
        self.log = log
        self.lock = threading.Lock()
        self.parar = threading.Event()
        self.erro = None
        self.manifesto = os.path.join(out, "manifesto_historico.jsonl")
        self.erros = os.path.join(out, "erros_historico.jsonl")
        self.feitos = {}
        self.transacoes = 0
        self.n_novos = 0
        self.n_429 = 0
        self.t0 = time.time()

    # ---- checkpoints
    def carregar(self):
        self.feitos = {}
        if os.path.exists(self.manifesto):
            for l in _linhas(self.manifesto):
                m = json.loads(l)
                if m.get("status") == "ok":
                    self.feitos[m["label"]] = m
        ok = {}
        for k, m in self.feitos.items():                     # so vale checkpoint cujo arquivo existe e confere
            p = os.path.join(self.out, *m["arquivo"].split("/"))
            if os.path.exists(p) and sha256(_bytes(p)) == m["sha256"]:
                ok[k] = m
        self.feitos = ok

    def _anexar(self, caminho, reg):
        with self.lock:
            with open(caminho, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(reg, ensure_ascii=False, sort_keys=True) + "\n")

    def _gravar(self, req, corpo, sha):
        pasta = os.path.join(self.out, req["produto"], str(req["ano"]))
        os.makedirs(pasta, exist_ok=True)
        arq = os.path.join(pasta, f"{req['inicio']}_{req['dias']}d_{sha[:32]}.csv")
        if os.path.exists(arq):
            if sha256(_bytes(arq)) != sha:
                raise Parada("arquivo existente com conteudo diferente (nao sobrescrito)")
        else:
            with open(arq, "wb") as fh:
                fh.write(corpo)
            os.chmod(arq, stat.S_IREAD)                      # imutavel depois de validado
        return os.path.relpath(arq, self.out).replace(os.sep, "/")

    # ---- reaproveitamento (so quando produto, periodo, caixa e dias sao identicos)
    def reaproveitar(self, req, fonte_dir, fonte_manifesto):
        if not os.path.exists(fonte_manifesto):
            return False
        for l in _linhas(fonte_manifesto):
            m = json.loads(l)
            if (m.get("http") == 200 and m.get("produto") == req["produto"] and m.get("inicio") == req["inicio"]
                    and m.get("dias") == req["dias"] and m.get("bbox") == req["bbox"] and "arquivo" in m):
                p = os.path.join(fonte_dir, *m["arquivo"].split("/"))
                if not os.path.exists(p):
                    continue
                corpo = _bytes(p)
                if sha256(corpo) != m["sha256"]:
                    continue
                resumo = validar(corpo, req)
                arq = self._gravar(req, corpo, m["sha256"])
                reg = {"label": req["label"], "produto": req["produto"], "inicio": req["inicio"], "dias": req["dias"],
                       "bbox": req["bbox"], "status": "ok", "http": 200, "bytes": len(corpo), "sha256": m["sha256"],
                       "arquivo": arq, "origem": "reutilizado", "origem_manifesto": os.path.basename(fonte_manifesto),
                       "origem_arquivo": m["arquivo"], "ms": 0, "tentativas": 0, "transacoes": 0, **resumo}
                self._anexar(self.manifesto, reg)
                self.feitos[req["label"]] = reg
                return True
        return False

    # ---- uma requisicao
    def uma(self, req):
        if self.parar.is_set():
            return
        esperado = req["dias"] * S.TRANSACOES_POR_DIA
        for tent in range(1, 5):
            self.janela.adquirir(esperado)
            t0 = time.time()
            cod, corpo = self.get(S.url_dados(self.chave, req), self.chave)
            ms = int((time.time() - t0) * 1000)
            if cod == 429:
                self.n_429 += 1
                self._anexar(self.erros, {"label": req["label"], "http": 429, "tentativa": tent})
                self.log(f"429 em {req['label']} (tentativa {tent}); pausa e verificacao de cota")
                time.sleep(90)
                st = self.status()
                if st.get("http") != 200 or st.get("atual", 10 ** 9) > 0.5 * st.get("limite", 5000):
                    time.sleep(120)
                continue
            if cod is None or (cod == 200 and not corpo):
                self._anexar(self.erros, {"label": req["label"], "http": cod, "tentativa": tent, "detalhe": "sem corpo"})
                time.sleep(5 * tent)
                continue
            break
        else:
            raise Parada(f"{req['label']}: falhou apos tentativas (HTTP {cod})")
        if cod != 200:
            self._anexar(self.erros, {"label": req["label"], "http": cod})
            raise Parada(f"{req['label']}: HTTP {cod}")
        try:
            resumo = validar(corpo, req)
        except Invalido as e:
            self._anexar(self.erros, {"label": req["label"], "http": 200, "validacao": str(e)})
            raise Parada(f"{req['label']}: validacao falhou: {e}")
        sha = sha256(corpo)
        arq = self._gravar(req, corpo, sha)
        reg = {"label": req["label"], "produto": req["produto"], "inicio": req["inicio"], "dias": req["dias"],
               "bbox": req["bbox"], "status": "ok", "http": 200, "ms": ms, "bytes": len(corpo), "sha256": sha,
               "arquivo": arq, "origem": "nasa_api", "tentativas": tent, "transacoes": esperado, **resumo}
        self._anexar(self.manifesto, reg)
        with self.lock:
            self.feitos[req["label"]] = reg
            self.transacoes += esperado
            self.n_novos += 1
            n = self.n_novos
        if n % 25 == 0:
            self.verificar_custo()
            dur = time.time() - self.t0
            self.log(f"progresso: {n} novas, {len(self.feitos)} concluidas, transacoes {self.transacoes}, {dur / 60:.1f} min")

    def verificar_custo(self):
        st = self.status()
        if st.get("http") != 200 or "atual" not in st:
            raise Parada(f"status da chave inesperado: {st}")
        local = self.janela.soma()
        if st["atual"] > local + 100:
            raise Parada(f"divergencia de custo: NASA atual={st['atual']} > contagem local da janela={local}")

    def executar(self, itens, reuso=None):
        os.makedirs(self.out, exist_ok=True)
        self.carregar()
        st = self.status()
        if st.get("http") != 200 or "atual" not in st:
            raise Parada(f"chave/cota nao verificada: {st}")
        if st["atual"] > 0.2 * st["limite"]:
            raise Parada(f"cota ja em uso ({st['atual']}); aguarde a janela de 10 min")
        pend = [i for i in itens if i["label"] not in self.feitos]
        if reuso:
            for i in list(pend):
                if self.reaproveitar(i, *reuso):
                    pend.remove(i)
                    self.log(f"reutilizado {i['label']}")
        self.log(f"plano: {len(itens)} requisicoes; ja concluidas/reutilizadas: {len(itens) - len(pend)}; pendentes: {len(pend)}")
        fila = collections.deque(pend)
        lock_fila = threading.Lock()

        def trabalhador():
            while not self.parar.is_set():
                with lock_fila:
                    if not fila:
                        return
                    req = fila.popleft()
                try:
                    self.uma(req)
                except Parada as e:
                    self.erro = str(e)
                    self.parar.set()
                except Exception as e:                       # noqa: BLE001
                    self.erro = f"{type(e).__name__} em {req['label']}"
                    self.parar.set()

        ths = [threading.Thread(target=trabalhador) for _ in range(self.workers)]
        [t.start() for t in ths]
        [t.join() for t in ths]
        self.verificar_custo_final()
        if self.erro:
            raise Parada(self.erro)

    def verificar_custo_final(self):
        try:
            st = self.status()
            self.log(f"cota NASA no fim: atual={st.get('atual')} limite={st.get('limite')}; transacoes medidas por esta execucao (local): {self.transacoes}")
        except Exception:                                    # noqa: BLE001
            pass


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--reuso-dir", help="dir da sondagem anterior (Missao 03.1) com manifesto_sondagem.jsonl")
    a = ap.parse_args(argv)
    itens = plano()
    if a.plan:
        por = collections.Counter(i["produto"] for i in itens)
        print(f"{len(itens)} requisicoes {dict(por)}; dias por produto {sum(d for _, d in chunks())}; "
              f"transacoes previstas {transacoes_previstas(itens)}")
        print("primeiras:", [(i["inicio"], i["dias"]) for i in itens[:3]], "ultima:", (itens[len(itens) // 2 - 1]["inicio"], itens[len(itens) // 2 - 1]["dias"]))
        return 0
    if a.run:
        chave = os.environ.get("FIRMS_MAP_KEY")
        if not chave:
            raise SystemExit("FIRMS_MAP_KEY nao definida")
        if not a.out:
            raise SystemExit("informe --out (fora do Git)")
        out = S.validar_saida(a.out)
        reuso = None
        if a.reuso_dir:
            reuso = (a.reuso_dir, os.path.join(a.reuso_dir, "manifesto_sondagem.jsonl"))
        ad = Adquiridor(out, chave, workers=a.workers)
        try:
            ad.executar(itens, reuso)
        except Parada as e:
            print("PARADA:", e)
            return 2
        print("concluido:", len(ad.feitos), "de", len(itens))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
