from math import sqrt
from random import random

from phoray.solver import closest_points


from . import PhorayTestCase


class ClosestPointTestCase(PhorayTestCase):

    def test_lines_with_same_point(self):
        p1 = (random()-.5, random()-.5, random()-.5)
        r1 = (0, 0, 1)
        r2 = (0, -1, 0)
        s, t = closest_points(p1, r1, p1, r2)
        self.assertAllClose(s, t)

    def test_intersecting_lines(self):
        p1 = (0, 0, 0)
        p2 = (1, 0, 0)
        r1 = (1/sqrt(2), 1/sqrt(2), 0)
        r2 = (0, 1, 0)
        s, t = closest_points(p1, r1, p2, r2)
        self.assertAllClose(s, sqrt(2))
        self.assertAllClose(t, 1)

    def test_skew_lines(self):
        p1 = (0, 0, 0)
        p2 = (1, 0, 0)
        r1 = (1/sqrt(2), 0, 1/sqrt(2))
        r2 = (0, 1, 0)
        s, t = closest_points(p1, r1, p2, r2)
        self.assertAllClose(s, 1/sqrt(2))
        self.assertAllClose(t, 0)
