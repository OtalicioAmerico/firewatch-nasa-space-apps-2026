"""Cobertura geometrica a partir de granulos L2 (CMR) e sua relacao com as deteccoes FIRMS.

EXPERIMENTAL / NAO VALIDADO. Principios:
* o CMR NAO e autoridade absoluta: o catalogo pode estar incompleto (ex.: Terra em 13-15/05/2025 tem deteccoes FIRMS e nenhum granulo);
* cobertura geometrica nao garante visibilidade (nuvem, fumaca, angulo) e ausencia de deteccao nunca vira "sem fogo";
* a fracao coberta de uma celula e a fracao da AREA da celula dentro do poligono do granulo, estimada por amostragem em grade
  (n x n pontos centrais), nao o teste do centro da celula;
* os poligonos dos granulos sao quadrilateros esfericos (arestas = circulos maximos): o teste de pertinencia e feito na esfera.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# ---- estados (dimensoes separadas)
DETECCAO_REGISTRADA = "DETECCAO_REGISTRADA"
AUSENCIA_DE_DETECCAO_REGISTRADA = "AUSENCIA_DE_DETECCAO_REGISTRADA"
COBERTURA_GEOMETRICA_CORROBORADA = "COBERTURA_GEOMETRICA_CORROBORADA"
COBERTURA_GEOMETRICA_PARCIAL = "COBERTURA_GEOMETRICA_PARCIAL"
SEM_COBERTURA_GEOMETRICA_CORROBORADA = "SEM_COBERTURA_GEOMETRICA_CORROBORADA"   # estado adicional: ausencia de granulo COM catalogo completo
CONFLITO_FIRMS_CMR = "CONFLITO_FIRMS_CMR"
COBERTURA_INDETERMINADA = "COBERTURA_INDETERMINADA"

# ---- regras fixadas ANTES de olhar os resultados (nao ajustar depois)
LIMIAR_CORROBORADA = 0.95        # fracao de area minima para "cobertura geometrica corroborada"
LIMIAR_CATALOGO = 0.85           # contagem global do dia >= 85 % da mediana do satelite => catalogo considerado completo no dia
TOLERANCIA_MIN = 1               # tolerancia de tempo entre deteccao e intervalo do granulo (minutos)
AMOSTRAS_POR_LADO = 5            # 5 x 5 pontos por celula


def _vec(lat, lon):
    p, l = math.radians(lat), math.radians(lon)
    return (math.cos(p) * math.cos(l), math.cos(p) * math.sin(l), math.sin(p))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def parse_poligono(texto: str):
    """'lat lon lat lon ...' (anel fechado) -> lista de (lat, lon) sem o ponto final repetido."""
    v = [float(x) for x in texto.split()]
    pts = [(v[k], v[k + 1]) for k in range(0, len(v) - 1, 2)]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts


@dataclass
class Granulo:
    t0: int            # minutos UTC desde 1970
    t1: int
    pontos: list       # [(lat, lon)]
    dia_noite: str | None = None

    def __post_init__(self):
        vs = [_vec(la, lo) for la, lo in self.pontos]
        self._n = [_cross(vs[k], vs[(k + 1) % len(vs)]) for k in range(len(vs))]
        c = (sum(v[0] for v in vs), sum(v[1] for v in vs), sum(v[2] for v in vs))
        sinais = [1 if _dot(n, c) >= 0 else -1 for n in self._n]
        self.convexo = len(set(sinais)) == 1
        self._s = sinais[0] if self.convexo else 1

    def contem(self, lat: float, lon: float) -> bool:
        """Pertinencia esferica (poligono convexo). Se nao convexo, usa teste plano em lon/lat (aproximado)."""
        if self.convexo:
            p = _vec(lat, lon)
            s = self._s
            for n in self._n:
                if s * _dot(n, p) < 0:
                    return False
            return True
        ins = False
        pts = [(lo, la) for la, lo in self.pontos]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            if (y1 > lat) != (y2 > lat) and x1 + (lat - y1) * (x2 - x1) / (y2 - y1) > lon:
                ins = not ins
        return ins

    def contem_no_tempo(self, t: int, lat: float, lon: float, tol: int = TOLERANCIA_MIN) -> bool:
        return self.t0 - tol <= t <= self.t1 + tol and self.contem(lat, lon)


def fracao_area_celula(granulos, lat_min, lon_min, lat_max, lon_max, n: int = AMOSTRAS_POR_LADO) -> float:
    """Fracao [0,1] da area da celula dentro da UNIAO dos poligonos (amostragem n x n; erro tipico <= 1/n^2 por borda).

    Atalho: 5 pontos (cantos + centro) todos dentro => 1,0; todos fora => 0,0 (um granulo que cruze a celula sem cobrir
    nenhum desses 5 pontos e ignorado; documentado como aproximacao)."""
    if not granulos:
        return 0.0

    def dentro(la, lo):
        return any(g.contem(la, lo) for g in granulos)

    amostra5 = [(lat_min, lon_min), (lat_min, lon_max), (lat_max, lon_min), (lat_max, lon_max),
                ((lat_min + lat_max) / 2, (lon_min + lon_max) / 2)]
    f5 = [dentro(la, lo) for la, lo in amostra5]
    if all(f5):
        return 1.0
    if not any(f5):
        return 0.0
    dla, dlo = (lat_max - lat_min) / n, (lon_max - lon_min) / n
    dentro_n = sum(1 for a in range(n) for b in range(n) if dentro(lat_min + (a + 0.5) * dla, lon_min + (b + 0.5) * dlo))
    return dentro_n / (n * n)


def registro_corroborado(granulos, t: int, lat: float, lon: float) -> bool:
    """A deteccao FIRMS cai em algum granulo (tempo +- 1 min e poligono)?"""
    return any(g.contem_no_tempo(t, lat, lon) for g in granulos)


def catalogo_completo(contagem_global: int | None, mediana: float | None) -> bool | None:
    """Evidencia independente de completude do catalogo no dia: contagem global >= 85 % da mediana. None = sem informacao."""
    if contagem_global is None or not mediana:
        return None
    return contagem_global >= LIMIAR_CATALOGO * mediana


def classificar_cobertura(f: float, catalogo_ok: bool | None, conflito_no_dia: bool) -> str:
    """Estado de COBERTURA de uma celula num satelite-dia (dimensao independente da deteccao).

    - conflito FIRMS x CMR no satelite-dia => a cobertura nao e aceita como evidencia: INDETERMINADA
    - f >= 0,95 e catalogo completo e sem conflito => CORROBORADA
    - 0 < f < 0,95 e sem conflito => PARCIAL (observacao parcial documentada pelo catalogo)
    - f == 0 e catalogo completo e sem conflito => SEM_COBERTURA_GEOMETRICA_CORROBORADA (nao e 'sem fogo')
    - demais casos (catalogo sem evidencia de completude ou desconhecido) => INDETERMINADA
    """
    if conflito_no_dia:
        return COBERTURA_INDETERMINADA
    if catalogo_ok is not True:
        return COBERTURA_INDETERMINADA
    if f >= LIMIAR_CORROBORADA:
        return COBERTURA_GEOMETRICA_CORROBORADA
    if f > 0:
        return COBERTURA_GEOMETRICA_PARCIAL
    return SEM_COBERTURA_GEOMETRICA_CORROBORADA
