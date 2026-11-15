"""Importa para SQLite local (fora do Git) os arquivos validados do manifesto historico. Idempotente.

Uso: python tools/historico/importar.py --dados <dir da aquisicao> --banco <arquivo .db fora do Git> --ibge <dir com IBGE_2025>
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from firecal import store  # noqa: E402
from firecal.geo import region_from_ibge_municipios  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--dados", required=True)
ap.add_argument("--banco", required=True)
ap.add_argument("--ibge", required=True, help="diretorio que contem IBGE_2025/municipios")
ap.add_argument("--manifesto", default="manifesto_historico.jsonl")
a = ap.parse_args()
repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.commonpath([os.path.abspath(a.banco), repo]) == repo:
    sys.exit("banco deve ficar FORA do repositorio Git")
t0 = time.time()
reg = region_from_ibge_municipios(a.ibge, "17", "Tocantins")
c = store.abrir(a.banco)
r = store.importar_manifesto(c, a.dados, os.path.join(a.dados, a.manifesto), regiao=reg, descricao="aquisicao historica 2021-2025")
print("importacao:", r, f"{time.time() - t0:.0f}s")
print("verificacao:", store.verificar(c))
print("tamanho do banco (bytes):", os.path.getsize(a.banco))
