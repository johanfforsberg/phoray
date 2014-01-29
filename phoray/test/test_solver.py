from random import random

from phoray.solver import closest_points


from . import PhorayTestCase


class ClosestPointTestCase(PhorayTestCase):

    def test_lines_with_same_point(self):
        p1 = (random()-.5, random()-.5, random()-.5)
        r1 = (0, 0, 1)
        r2 = (0, -1, 0)
        a, b = closest_points(p1, r1, p1, r2)
        self.assertEqual(a, b)

    def test_intersecting_lines(self):
        p1 = (0, 0, 0)
        p2 = (1, 0, 0)
        r1 = (1, 1, 0)
        r2 = (0, 1, 0)
        a, b = closest_points(p1, r1, p2, r2)
        self.assertEqual(a, b)
        self.assertEqual(b, (1, 1, 0))

    def test_skew_lines(self):
        p1 = (0, 0, 0)
        p2 = (1, 0, 0)
        r1 = (1, 0, 1)
        r2 = (0, 1, 0)
        a, b = closest_points(p1, r1, p2, r2)
        self.assertEqual(a, (0.5, 0.0, 0.5))
        self.assertEqual(b, (1.0, 0.0, 0.0))
