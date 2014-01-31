from math import sqrt
from random import seed

from numpy import array

from phoray.ray import Rays
from phoray.surface import Sphere
from phoray.element import Mirror
from phoray.source import GridSource
from . import PhorayTestCase


seed(123)  # make things more predictable


class RaysTestCase(PhorayTestCase):

    def test_estimate_focus_two_rays(self):
        p1 = (0, 0, 0)
        p2 = (1, 0, 0)
        r1 = (1/sqrt(2), 0, 1/sqrt(2))
        r2 = (0, 1, 0)
        rays = Rays(array((p1, p2)), array((r1, r2)),
                    array(((0, 0, 0), (0, 0, 0))))
        a = rays.estimate_focus(1)
        self.assertAllClose(a, (0.75, 0.0, 0.25))

    def test_estimate_focus_parallel_rays(self):
        p1 = (0, 0, 0)
        p2 = (1, 0, 0)
        r1 = (0, 1, 0)
        r2 = (0, 1, 0)
        rays = Rays(array((p1, p2)), array((r1, r2)),
                    array(((0, 0, 0), (0, 0, 0))))
        a = rays.estimate_focus(1)
        self.assertEqual(a, None)

    def test_estimate_focus_spherical_mirror(self):
        sphere = Sphere(1)
        mirror = Mirror(geometry=sphere, position=(0, 0, 1))
        source = GridSource(divergence=(0.1, 0.1, 0))

        rays = {0: [source.generate()]}
        refl = mirror.trace(rays)
        a = refl[0][0].estimate_focus()

        self.assertAllClose(a, (0, 0, 0))

    def test_estimate_focus_spherical_mirror_2(self):
        sphere = Sphere(1)
        mirror = Mirror(geometry=sphere, position=(0, 0, 2), rotation=(30, 0, 0))
        source = GridSource(divergence=(0.1, 0.1, 0))

        rays = {0: [source.generate()]}
        refl = mirror.trace(rays)
        a = refl[0][0].estimate_focus(100)
        self.assertAllClose(a, (-0.0, 0.57, 1.67), atol=0.05)
