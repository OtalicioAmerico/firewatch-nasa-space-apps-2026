"""Uso: python -m firecal run --config config/poc_tocantins.json --data-dir <dados NASA> --out resultados/missao02"""
import argparse
import os
import sys

from . import pipeline


def main(argv=None):
    ap = argparse.ArgumentParser(prog="firecal", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="executa o motor sobre os dados NASA preservados (somente leitura)")
    r.add_argument("--config", required=True)
    r.add_argument("--data-dir", default=os.environ.get("NASA_DATA_DIR"),
                   help="diretorio dos dados NASA (ou variavel NASA_DATA_DIR)")
    r.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if not a.data_dir:
        ap.error("informe --data-dir ou NASA_DATA_DIR")
    res = pipeline.run(pipeline.load_config(a.config), os.path.abspath(a.data_dir), a.out)
    print("ok:", a.out, "| registros unicos:", res["integridade"]["registros_unicos_no_periodo"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
