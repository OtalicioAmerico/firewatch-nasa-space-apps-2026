"""Sondagem controlada da API NASA FIRMS (Missao 03.1): no maximo 9 requisicoes de 5 dias.

Seguranca da credencial:
  * a MAP_KEY vem SOMENTE da variavel de ambiente FIRMS_MAP_KEY; nunca de arquivo do repositorio;
  * a URL completa (que contem a chave) NUNCA e impressa nem gravada: todas as mensagens e manifestos usam
    ``descrever()``/``redigir()``; excecoes de rede sao reduzidas a classe + codigo HTTP;
  * o diretorio de saida deve ficar FORA do repositorio Git.

Modos:
  --plan                  mostra o plano (sem rede, sem chave)
  --check-key             consulta o status da chave e a cota (sem baixar dados de fogo); imprime so numeros
  --execute --confirm-sondagem   executa as 9 requisicoes do plano, uma por produto e periodo, parando ao 1o problema

Nenhuma outra aquisicao e feita. Politica de parada: HTTP != 200, resposta que nao e CSV FIRMS esperado, mais linhas
que o limite, consumo de transacoes diferente de 2 por dia-unidade, ou arquivo ja existente com conteudo diferente.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://firms.modaps.eosdis.nasa.gov"
BBOX = "-51.0,-13.75,-45.5,-4.9"
PRODUTOS = ["MODIS_SP", "VIIRS_SNPP_SP", "VIIRS_NOAA20_SP"]
PERIODOS = ["2022-08-10", "2025-03-10", "2025-08-10"]      # 5 dias cada: 10 a 14
DIAS = 5
TRANSACOES_POR_DIA = 2                                      # medido nos lotes 1-3 e em 03.1
MAX_LINHAS = 60000                                          # limite de seguranca por requisicao
ESPERADO_CABECALHO = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "frp"}
RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def plano():
    return [{"label": f"sondagem-{p}-{d}", "produto": p, "inicio": d, "dias": DIAS, "bbox": BBOX}
            for p in PRODUTOS for d in PERIODOS]


def plano_versoes():
    """Missao 03.2: 6 requisicoes de 1 dia (MODIS_SP, 12/08 de 2019 a 2024) para verificar a coluna version."""
    return [{"label": f"versao-MODIS_SP-{a}-08-12", "produto": "MODIS_SP", "inicio": f"{a}-08-12", "dias": 1, "bbox": BBOX}
            for a in range(2019, 2025)]


def descrever(req: dict) -> str:
    """Texto seguro (sem chave) de uma requisicao."""
    return f"{req['produto']} {req['inicio']} +{req['dias']}d bbox={req['bbox']}"


def redigir(texto: str, chave: str | None) -> str:
    return texto.replace(chave, "[CHAVE]") if chave else texto


def url_dados(chave: str, req: dict) -> str:
    return f"{BASE}/api/area/csv/{chave}/{req['produto']}/{req['bbox']}/{req['dias']}/{req['inicio']}"


def url_status(chave: str) -> str:
    return f"{BASE}/mapserver/mapkey_status/?MAP_KEY={chave}"


def _get(url: str, chave: str, timeout: int = 120):
    """GET; em erro devolve so (codigo, classe) sem URL."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "firecal-sondagem/0.1"}),
                                    timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:                                  # noqa: BLE001 - nunca propagar mensagem com URL
        return None, type(e).__name__.encode()


def status_chave(chave: str):
    cod, corpo = _get(url_status(chave), chave, 60)
    if cod != 200:
        return {"http": cod}
    try:
        d = json.loads(corpo.decode("utf-8"))
        return {"http": 200, "limite": int(d["transaction_limit"]), "atual": int(d["current_transactions"]),
                "intervalo": d.get("transaction_interval")}
    except Exception:                                       # noqa: BLE001
        return {"http": 200, "resposta": "inesperada"}


def validar_saida(out: str) -> str:
    out = os.path.abspath(out)
    if os.path.commonpath([out, RAIZ_REPO]) == RAIZ_REPO:
        raise SystemExit("diretorio de saida deve ficar FORA do repositorio Git")
    os.makedirs(out, exist_ok=True)
    return out


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def analisar_csv(corpo: bytes):
    """Valida e resume um CSV FIRMS. Levanta ValueError se inesperado."""
    texto = corpo.decode("utf-8")
    linhas = list(csv.DictReader(io.StringIO(texto)))
    campos = set(csv.DictReader(io.StringIO(texto)).fieldnames or [])
    if not ESPERADO_CABECALHO <= campos:
        raise ValueError("cabecalho inesperado")
    datas = {}
    versoes = set()
    for r in linhas:
        datas[r["acq_date"]] = datas.get(r["acq_date"], 0) + 1
        versoes.add(r.get("version", ""))
    return {"linhas": len(linhas), "datas": datas, "versoes": sorted(versoes)}


def executar(out: str, itens=None, nome_manifesto="manifesto_sondagem.jsonl"):
    itens = itens if itens is not None else plano()
    chave = os.environ.get("FIRMS_MAP_KEY")
    if not chave:
        raise SystemExit("FIRMS_MAP_KEY nao definida (nao ha chave; nada foi feito)")
    out = validar_saida(out)
    s0 = status_chave(chave)
    if s0.get("http") != 200 or "atual" not in s0:
        raise SystemExit(f"chave/cota nao verificada: {s0}")
    previsto = sum(r['dias'] for r in itens) * TRANSACOES_POR_DIA
    if s0["atual"] + previsto > 0.5 * s0["limite"]:
        raise SystemExit(f"cota insuficiente para a sondagem: atual={s0['atual']} limite={s0['limite']}")
    manifesto = os.path.join(out, nome_manifesto)
    for req in itens:
        antes = status_chave(chave)
        t0 = time.time()
        cod, corpo = _get(url_dados(chave, req), chave)
        dur = int((time.time() - t0) * 1000)
        reg = {"label": req["label"], "produto": req["produto"], "inicio": req["inicio"], "dias": req["dias"],
               "bbox": req["bbox"], "http": cod, "ms": dur, "bytes": len(corpo)}
        if cod != 200:
            _anexar(manifesto, {**reg, "parada": "http_nao_200"})
            raise SystemExit(f"PARADA: {descrever(req)} -> HTTP {cod}")
        try:
            info = analisar_csv(corpo)
        except ValueError as e:
            _anexar(manifesto, {**reg, "parada": "resposta_inesperada"})
            raise SystemExit(f"PARADA: {descrever(req)} -> {e}")
        depois = status_chave(chave)
        gasto = depois.get("atual", -1) - antes.get("atual", -1)
        reg.update({"sha256": sha256(corpo), **info, "transacoes_gastas": gasto,
                    "transacoes_esperadas": req["dias"] * TRANSACOES_POR_DIA})
        pasta = os.path.join(out, req["produto"], req["inicio"].replace("-", ""))
        os.makedirs(pasta, exist_ok=True)
        arq = os.path.join(pasta, reg["sha256"][:32] + ".csv")
        if os.path.exists(arq) and sha256(open(arq, "rb").read()) != reg["sha256"]:
            raise SystemExit("PARADA: arquivo existente com conteudo diferente")
        if not os.path.exists(arq):
            with open(arq, "wb") as fh:
                fh.write(corpo)
        reg["arquivo"] = os.path.relpath(arq, out).replace(os.sep, "/")
        _anexar(manifesto, reg)
        print(f"ok {descrever(req)}: linhas={info['linhas']} bytes={len(corpo)} ms={dur} transacoes={gasto}")
        if info["linhas"] > MAX_LINHAS:
            raise SystemExit("PARADA: linhas acima do limite de seguranca")
        if gasto != reg["transacoes_esperadas"]:
            raise SystemExit(f"PARADA: consumo {gasto} difere do esperado {reg['transacoes_esperadas']}")
    fim = status_chave(chave)
    print("transacoes totais na janela:", fim.get("atual"), "(antes:", s0["atual"], ")")


def _anexar(caminho: str, reg: dict):
    with open(caminho, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(reg, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--check-key", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--versoes", action="store_true", help="usa o plano da Missao 03.2 (6 requisicoes de 1 dia)")
    ap.add_argument("--confirm-sondagem", action="store_true")
    ap.add_argument("--out", help="diretorio de saida fora do Git")
    a = ap.parse_args(argv)
    itens = plano_versoes() if a.versoes else plano()
    if a.plan:
        for r in itens:
            print(descrever(r))
        print(f"{len(itens)} requisicoes; transacoes previstas: {sum(r['dias'] for r in itens) * TRANSACOES_POR_DIA}")
        return 0
    chave = os.environ.get("FIRMS_MAP_KEY")
    if a.check_key:
        if not chave:
            print("Chave encontrada: NAO (FIRMS_MAP_KEY nao definida)")
            return 2
        print("status:", status_chave(chave))
        return 0
    if a.execute:
        if not a.confirm_sondagem or not a.out:
            raise SystemExit("use --execute --confirm-sondagem --out <diretorio fora do Git>")
        executar(a.out, itens, "manifesto_versoes.jsonl" if a.versoes else "manifesto_sondagem.jsonl")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
