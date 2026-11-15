"""O gerador de geometria nao pode voltar a produzir nomes de municipios corrompidos (IBGE grava o DBF em UTF-8)."""
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(RAIZ, "tools", "mock_geo", "gerar_geometria_tocantins.py")
NOMES = {"1709302": "Guaraí", "1721109": "Tocantínia", "1707207": "Dois Irmãos do Tocantins", "3550308": "São Paulo"}


def _circulo(cx, cy, r, n=40):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    return pts + [pts[0]]


def _escreve_dbf(path, registros):
    campos = [("CD_MUN", 7), ("NM_MUN", 40)]
    rec_len = 1 + sum(n for _, n in campos)
    header_len = 32 + 32 * len(campos) + 1
    out = bytearray(struct.pack("<BBBBIHH20x", 3, 26, 1, 1, len(registros), header_len, rec_len))
    for nome, n in campos:
        out += nome.encode().ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([n]) + b"\0" * 15
    out += b"\r"
    for cd, nm in registros:
        out += b" " + cd.encode().ljust(7) + nm.encode("utf-8").ljust(40)  # UTF-8, como no arquivo do IBGE
    with open(path, "wb") as fh:
        fh.write(bytes(out))


def _escreve_shp(path, aneis):
    corpo = b""
    for i, pts in enumerate(aneis, 1):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        c = struct.pack("<i4dii", 5, min(xs), min(ys), max(xs), max(ys), 1, len(pts)) + struct.pack("<i", 0)
        c += b"".join(struct.pack("<2d", x, y) for x, y in pts)
        corpo += struct.pack(">ii", i, len(c) // 2) + c
    cab = struct.pack(">i20xi", 9994, (100 + len(corpo)) // 2) + struct.pack("<ii8d", 1000, 5, *([0.0] * 8))
    with open(path, "wb") as fh:
        fh.write(cab + corpo)


class TestGeracaoMunicipios(unittest.TestCase):
    def test_nomes_com_acento_saem_corretos(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "ibge", "IBGE_2025", "municipios")
            os.makedirs(base)
            cods = list(NOMES)
            _escreve_dbf(os.path.join(base, "BR_Municipios_2025.dbf"), [(c, NOMES[c]) for c in cods])
            _escreve_shp(os.path.join(base, "BR_Municipios_2025.shp"), [_circulo(-48 + 3 * k, -10, 1.0) for k in range(len(cods))])
            saida = os.path.join(tmp, "saida")
            r = subprocess.run([sys.executable, "-I", SCRIPT, "--ibge", os.path.join(tmp, "ibge"), "--saida", saida],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(os.path.join(saida, "tocantins-municipios.json"), encoding="utf-8") as fh:
                d = json.load(fh)
            nomes = {f["properties"]["cd"]: f["properties"]["nm"] for f in d["features"]}
            self.assertEqual(set(nomes), {"1709302", "1721109", "1707207"})  # so UF 17
            for cd, nm in nomes.items():
                self.assertEqual(nm, NOMES[cd])
                self.assertFalse(set(nm) & {"Ã", "Â", "­", "�"}, nm)


if __name__ == "__main__":
    unittest.main()
