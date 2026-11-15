import unittest

from firecal.geo import Region, cell_bounds, cell_id, cell_index, haversine_m


class TestGeo(unittest.TestCase):
    def test_haversine_um_grau_de_latitude(self):
        self.assertAlmostEqual(haversine_m(0, 0, 1, 0), 111195, delta=200)
        self.assertEqual(haversine_m(-10, -48, -10, -48), 0)

    def test_celula_bordas_e_negativos(self):
        self.assertEqual(cell_index(0.0, 0.0, 0.25), (0, 0))
        self.assertEqual(cell_index(0.2499, 0.25, 0.25), (0, 1))
        self.assertEqual(cell_index(-0.0001, -0.0001, 0.25), (-1, -1))
        self.assertEqual(cell_index(-10.0, -48.0, 0.25), (-40, -192))
        self.assertEqual(cell_index(0.3, 0.3, 0.1), (3, 3))   # 0.3/0.1 em ponto flutuante = 2.9999...

    def test_celula_contem_o_ponto(self):
        for lat, lon in ((-10.13, -48.77), (5.99, -73.01), (0.0, 0.0)):
            i, j = cell_index(lat, lon, 0.25)
            la0, lo0, la1, lo1 = cell_bounds(0.25, i, j)
            self.assertTrue(la0 <= lat < la1 and lo0 <= lon < lo1)
        self.assertEqual(cell_id(0.25, -40, -192), "g0.25_-40_-192")

    def test_regiao_retangulo(self):
        r = Region.rectangle("t", -50, -13, -45, -5)
        self.assertTrue(r.contains(-48, -10))
        self.assertFalse(r.contains(-44.9, -10))
        self.assertFalse(r.contains(-48, -4.9))

    def test_regiao_com_buraco(self):
        outer = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        hole = [(4, 4), (6, 4), (6, 6), (4, 6), (4, 4)]
        r = Region("t", [outer, hole])
        self.assertTrue(r.contains(1, 1))
        self.assertFalse(r.contains(5, 5))
        self.assertFalse(r.contains(11, 5))

    def test_regiao_concava(self):
        l_shape = [(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10), (0, 0)]
        r = Region("t", [l_shape])
        self.assertTrue(r.contains(2, 8))
        self.assertTrue(r.contains(8, 2))
        self.assertFalse(r.contains(8, 8))

    def test_celula_inteira_na_regiao(self):
        r = Region.rectangle("t", 0.0, 0.0, 1.0, 1.0)
        self.assertTrue(r.cell_fully_inside(0.25, 1, 1))     # [0.25,0.5]: dentro
        self.assertFalse(r.cell_fully_inside(0.25, 4, 4))    # [1.0,1.25]: fora
        wide = Region.rectangle("t", 0.1, 0.1, 1.0, 1.0)
        self.assertFalse(wide.cell_fully_inside(0.25, 0, 0))  # [0,0.25] so parcialmente dentro


if __name__ == "__main__":
    unittest.main()
