"""
Tests for the surface classes.

TODO: Most classes have only very basic tests. Expand.
"""

from math import sqrt, atan, sin, cos, asin
from random import uniform

from numpy import array, allclose, isnan

from phoray.surface import (Plane, Sphere, Cylinder, Ellipsoid, Paraboloid,
                            Toroid)
from phoray.ray import Rays

from . import PhorayTestCase


A, B, C = (uniform(-0.5, 0.5) for _ in range(3))


class PlaneSurfaceTestCase(PhorayTestCase):

    def test_intersect(self):
        plane = Plane()
        rays = Rays([(A, B, -1)], [(0, 0, 1)], None)
        intersection = plane.intersect(rays)
        self.assertTrue(allclose(intersection, [(A, B, 0)]))

    def test_intersect_miss(self):
        "Check that intersecting outside the edges returns NaNs"
        plane = Plane(xsize=0.1)
        rays = Rays([(A + 1, B, -1)], [(0, 0, 1)], None)
        intersection = plane.intersect(rays)
        self.assertTrue(all(isnan(intersection[0])))

    def test_reflect(self):
        plane = Plane()
        ray = Rays([(A, B, -1)], [(0, 0, 1)], None)
        reflection = plane.reflect(ray)
        self.assertTrue(allclose(reflection.endpoints, (A, B, 0)))
        self.assertTrue(allclose(reflection.directions, (0, 0, -1)))

    def test_reflect_miss(self):
        """Test that rays missing an element have NaN endpoints."""
        plane = Plane()
        ray = Rays([(A+1, B, -1)], [(0, 0, 1)], None)
        reflection = plane.reflect(ray)
        self.assertTrue(all(isnan(reflection.endpoints[0])))

    def test_diffract(self):
        """Test that diffraction works for a simple case."""
        plane = Plane()
        d = 1 / uniform(9e4, 1e5)
        order = -1
        wavelength = uniform(500e-9, 700e-9)
        ray = Rays([(0, -abs(B), 1)],
                   array([(0, abs(B), -1)]) / sqrt(B ** 2 + 1),
                   wavelength)
        diffraction = plane.diffract(ray, d, order)
        inc_angle = atan(abs(B))
        exit_angle = asin(sin(inc_angle) + order * wavelength / d)
        self.assertTrue(allclose(diffraction.directions[0],
                                 (0, -sin(exit_angle), cos(exit_angle))))

    def test_zeroth_order_diffraction_equals_reflection(self):
        plane = Plane()
        ray = Rays([(A, B, -1)], [(0, 0, 1)], uniform(100, 1000))
        reflection = plane.reflect(ray)
        diffraction = plane.diffract(ray, uniform(0.001, 0.002), 0)
        self.assertTrue(allclose(reflection.endpoints, diffraction.endpoints))
        self.assertTrue(allclose(reflection.directions,
                                 diffraction.directions))


class SphereSurfaceTestCase(PhorayTestCase):

    def test_reflect(self):
        sphere = Sphere(1)
        rays = Rays([(0, 0, -1)], array([(A, B, 1)]) / sqrt(A**2 + B**2 + 1), None)
        reflection = sphere.reflect(rays)
        self.assertTrue(allclose(reflection.endpoints + reflection.directions,
                                 [(0, 0, -1)]))


class CylinderSurfaceTestCase(PhorayTestCase):

    def test_reflect(self):
        surf = Cylinder(1)
        ray = Rays([(0, 0, -1)],
                   array([(A, B, 1)]) / sqrt(A**2 + B**2 + 1), None)
        reflection = surf.reflect(ray).directions[0]
        self.assertTrue(allclose(reflection[0], ray.directions[0][0]))
        self.assertTrue(allclose(reflection[1], -ray.directions[0][1]))
        self.assertTrue(allclose(reflection[2], -ray.directions[0][2]))


class EllipsoidSurfaceTestCase(PhorayTestCase):

    def test_reflect(self):
        """Check that an ellipsoid with all equal radii is a sphere."""
        sphere = Ellipsoid(1, 1, 1)
        rays = Rays([(0, 0, -1)], array([(A, B, 1)]) /
                    sqrt(A**2 + B**2 + 1), None)
        reflection = sphere.reflect(rays)
        self.assertTrue(allclose(reflection.endpoints + reflection.directions,
                                 [(0, 0, -1)]))


class ToroidSurfaceTestCase(PhorayTestCase):

    def test_reflect(self):
        """Check that a toroid tends toward a sphere when r -> R ."""
        sphere = Toroid(1, 1)
        C, D = 0.01 * A, 0.01 * B
        rays = Rays([(0, 0, -1)], array([(C, D, 1)]) / sqrt(C**2 + D**2 + 1),
                    None)
        reflection = sphere.reflect(rays)
        self.assertTrue(allclose(reflection.endpoints + reflection.directions,
                                 [(0, 0, -1)], atol=1e-5))


class ParaboloidSurfaceTestCase(PhorayTestCase):

    def test_reflect(self):
        """Test that a paraboloid parallelizes light originating from the focal
        point.
        """
        surf = Paraboloid(1, 1, 1)
        ray = Rays([(0, 0, -0.25)], [(A, B, 1)], None)
        reflection = surf.reflect(ray)
        self.assertAlmostEquals(reflection.directions[0][0], 0)
        self.assertAlmostEquals(reflection.directions[0][1], 0)
