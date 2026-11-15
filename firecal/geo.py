"""Geometria: distancia, grade de celulas e regiao (poligono) com ponto-em-poligono.

Somente biblioteca padrao.
"""
from __future__ import annotations

import math
import os
import struct
from collections import defaultdict

_BAND = 0.02  # graus de latitude por faixa do indice de arestas


def haversine_m(la1: float, lo1: float, la2: float, lo2: float) -> float:
    """Distancia esferica (m). Erro < 0,5 % frente ao elipsoide nessas escalas."""
    p = math.pi / 180
    a = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742000.0 * math.asin(math.sqrt(a))


# ---------------- grade ----------------
def cell_index(lat: float, lon: float, size: float) -> tuple[int, int]:
    """Indice (i, j) da celula; grade ancorada em (0 deg, 0 deg); celula = [i*size, (i+1)*size)."""
    return (math.floor(lat / size + 1e-9), math.floor(lon / size + 1e-9))


def cell_id(size: float, i: int, j: int) -> str:
    return f"g{size:g}_{i}_{j}"


def cell_bounds(size: float, i: int, j: int) -> tuple[float, float, float, float]:
    """(lat_min, lon_min, lat_max, lon_max)."""
    return (i * size, j * size, (i + 1) * size, (j + 1) * size)


def cell_center(size: float, i: int, j: int) -> tuple[float, float]:
    return ((i + 0.5) * size, (j + 0.5) * size)


# ---------------- regiao ----------------
class Region:
    """Regiao definida por aneis de poligono (regra par-impar). Coordenadas (lon, lat)."""

    def __init__(self, name: str, rings: list[list[tuple[float, float]]]):
        self.name = name
        self.rings = rings
        xs = [x for r in rings for x, _ in r]
        ys = [y for r in rings for _, y in r]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))  # lon_min, lat_min, lon_max, lat_max
        self._bands: dict[int, list[tuple[float, float, float, float]]] = defaultdict(list)
        for ring in rings:
            for (x1, y1), (x2, y2) in zip(ring[:-1], ring[1:]):
                if y1 == y2:
                    continue
                lo, hi = (y1, y2) if y1 < y2 else (y2, y1)
                for b in range(math.floor(lo / _BAND), math.floor(hi / _BAND) + 1):
                    self._bands[b].append((x1, y1, x2, y2))

    @classmethod
    def rectangle(cls, name: str, lon_min: float, lat_min: float, lon_max: float, lat_max: float) -> "Region":
        return cls(name, [[(lon_min, lat_min), (lon_max, lat_min), (lon_max, lat_max), (lon_min, lat_max),
                           (lon_min, lat_min)]])

    def contains(self, lon: float, lat: float) -> bool:
        x0, y0, x1b, y1b = self.bbox
        if lon < x0 or lon > x1b or lat < y0 or lat > y1b:
            return False
        inside = False
        for (x1, y1, x2, y2) in self._bands.get(math.floor(lat / _BAND), ()):
            if (y1 > lat) != (y2 > lat) and x1 + (lat - y1) * (x2 - x1) / (y2 - y1) > lon:
                inside = not inside
        return inside

    def cell_fully_inside(self, size: float, i: int, j: int) -> bool:
        """Aproximacao: os 4 cantos da celula estao na regiao (nao detecta concavidades pequenas)."""
        la0, lo0, la1, lo1 = cell_bounds(size, i, j)
        return all(self.contains(lo, la) for la, lo in ((la0, lo0), (la0, lo1), (la1, lo0), (la1, lo1)))

    def cells_overlapping_bbox(self, size: float):
        x0, y0, x1, y1 = self.bbox
        i0, j0 = cell_index(y0, x0, size)
        i1, j1 = cell_index(y1, x1, size)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                yield i, j


# ---------------- IBGE (shapefile + dbf) ----------------
def _read_dbf_column(path: str, column: str) -> list[str]:
    data = open(path, "rb").read()
    n, header_len, rec_len = struct.unpack("<xxxxIHH", data[:12])
    offs, off, o = {}, 1, 32
    while data[o] != 13:
        name = data[o:o + 11].split(b"\0")[0].decode()
        ln = data[o + 16]
        offs[name] = (off, ln)
        off += ln
        o += 32
    a, ln = offs[column]
    return [data[header_len + i * rec_len + a: header_len + i * rec_len + a + ln].decode("latin1").strip()
            for i in range(n)]


def region_from_ibge_municipios(data_dir: str, uf_code: str, name: str,
                                shp_rel: str = "IBGE_2025/municipios/BR_Municipios_2025") -> Region:
    """Uniao dos municipios IBGE cujo CD_MUN comeca com ``uf_code`` (ex.: '17' = Tocantins)."""
    base = os.path.join(data_dir, *shp_rel.split("/"))
    codes = _read_dbf_column(base + ".dbf", "CD_MUN")
    keep = {i + 1 for i, c in enumerate(codes) if c.startswith(uf_code)}
    if not keep:
        raise ValueError(f"nenhum municipio com codigo iniciando em {uf_code}")
    shp = open(base + ".shp", "rb").read()
    pos, recno, rings = 100, 0, []
    while pos < len(shp):
        clen = struct.unpack(">i", shp[pos + 4:pos + 8])[0] * 2
        content = shp[pos + 8:pos + 8 + clen]
        pos += 8 + clen
        recno += 1
        if recno not in keep:
            continue
        npart, npts = struct.unpack("<ii", content[36:44])
        parts = list(struct.unpack("<%di" % npart, content[44:44 + 4 * npart])) + [npts]
        pts = struct.unpack("<%dd" % (2 * npts), content[44 + 4 * npart:44 + 4 * npart + 16 * npts])
        for a, b in zip(parts[:-1], parts[1:]):
            rings.append([(pts[2 * k], pts[2 * k + 1]) for k in range(a, b)])
    return Region(name, rings)
