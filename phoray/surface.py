from __future__ import division

from abc import ABCMeta, abstractmethod
from math import *

import numpy as np
from numpy import (array, dot, cross, where, sqrt,
                   cos, sin, arccos, arcsin)

from .transformations import (rotation_matrix, angle_between_vectors,
                              vector_norm)
from .ray import Rays
from .solver import quadratic
from . import PhorayBase, Length


__all__ = ("Plane", "Cylinder", "Sphere", "Ellipsoid",
           "Toroid", "Paraboloid")


class Surface(PhorayBase, metaclass=ABCMeta):
    """
    An abstract representation of a 3D surface.
    Should not be instantiated but serves as a base class to be inherited.
    """

    def __init__(self, xsize:Length=1.0, ysize:Length=1.0):
        self.xsize, self.ysize = xsize, ysize

    @classmethod
    def get_module_name(cls):
        return cls.__module__.split(".")[-1]

    @abstractmethod
    def intersect(self, r):
        """This method needs to be implemented by an actual surface.
        Shall return the point where Ray r intersects the surface.
        """

    @abstractmethod
    def normal(self, p):
        """This method needs to be implemented by an actual surface.
        Shall return the normal to the surface at point p.
        """

    def grating_direction(self, ps):
        """
        Returns a vector oriented along the grating lines (if any).
        This vector always lies in the plane containing the normal and
        the local x-axis, and is tangential to the surface (i.e.
        perpendicular to the normal. It also always has a non-negative
        projection on the x-axis.

        FIXME: special case of n and x-axis parallel
        """
        normal = self.normal(ps)
        xaxis = array((1, 0, 0))
        a = cross(xaxis, normal)
        b = cross(normal, a)
        return (b.T / vector_norm(b, axis=1)).T

    def reflect(self, rays):
        """
        Reflect the given ray in the surface, returning the reflected ray.
        """

        r = rays.directions
        P = self.intersect(rays)
        if P is None:
            return None
        else:
            n = self.normal(P)
            dots = (r * n).sum(axis=1) * 2.0
            # Flip if backlit
            #dots = np.where(dots > 0, dots, -dots)
            refl = r - (n.T * dots).T
            return Rays(P, refl, rays.wavelengths)

    def diffract(self, rays, d, order, line_spacing_function=None):

        """
        Diffract the given ray in the surface, returning the diffracted ray.

        TODO: it's definitely possible to simplify this. Also, check for
        correctness!
        """

        refl = self.reflect(rays)
        P = refl.endpoints
        if order == 0 or d == 0:
            return refl
        if d is None:
            if line_spacing_function is None:
                return refl
            else:
                # VLS grating
                d = line_spacing_function(P)
        n = self.normal(P)
        r_ref = refl.directions
        # OK, this isn't great, but for now flip the normal if the
        # ray is hitting the back of the element.
        n = (n.T * np.sign((r_ref * n).sum(axis=1))).T
        g = self.grating_direction(P)
        a = cross(g, n)  # surface tangent

        alpha = angle_between_vectors(g, r_ref, axis=1)
        x = cos(alpha)
        y = sin(alpha)

        phi = arccos((g * r_ref).sum(axis=1))  # dot product
        theta = arccos((n * r_ref).sum(axis=1) / sin(phi))
        theta_m = arcsin(order * rays.wavelengths /
                         (d * sin(phi)) + sin(theta))
        r_diff = g.T * x + a.T * y * sin(theta_m) + n.T * y * cos(theta_m)
        return Rays(P, r_diff.T, rays.wavelengths)

    def refract(self, rays, i1, i2):
        """
        Refurns the refracted ray given an incident ray.
        Uses Snell's law. Does not simulate dispersion.

        FIXME: Completely wrong.
        TODO: port to numpy.
        """
        P = self.intersect(rays)
        if P is not None:
            r = ray.directions
            n = self.normal(P)
            dotp = dot(n, r)
            if dotp >= 0:
                n = -n
            theta_in = acos(dot(n, r))
            if sin(theta_in) == 0:
                return ray
            theta_out = asin((i1 / i2) * sin(theta_in))
            v = r % n
            r2 = dot(-n, rotation_matrix(theta_out, v)[:3, :3].T)
            return Ray(P, r2, ray.wavelength)
        else:
            return None

    def mesh(self, res=10):
        """
        Returns the vertices and faces of a mesh representing the surface.
        """
        print("meshing it up")
        w, h = self.xsize, self.ysize
        xs, ys = np.meshgrid(np.linspace(-w / 2, w / 2, res + 1),
                             np.linspace(-h / 2, h / 2, res + 1))
        n = (res + 1)**2
        rays = Rays(array((xs.flatten(), ys.flatten(), np.zeros(n))).T,
                    array((np.zeros(n), np.zeros(n), np.ones(n))).T, None)
        verts = self.intersect(rays)
        faces = []
        for i in range(res):
            for j in range(res):
                current = i * (res + 1) + j
                faces.append((current, current + 1, current + 2 + res))
                faces.append((current, current + 2 + res, current + 1 + res))
        return verts, faces


class Plane(Surface):

    """
    A plane through the origin and perpendicular to z, i.e. z = 0.
    """

    def normal(self, ps):
        return array([(0, 0, 1)] * len(ps))

    def intersect(self, rays):
        rx, ry, rz = r = rays.directions.T
        ax, ay, az = a = rays.endpoints.T
        bx, by, bz = a + r

        t = -az / (bz - az)
        p = a + t * r
        px, py, pz = p

        nans = np.empty((3, len(px)))
        nans[:] = np.NaN
        # remove rays that are outside or backlighting
        # TODO: is it possible to somehow mask out these values earlier?
        q = where(((abs(px) <= self.xsize / 2) & (abs(py) <= self.ysize / 2) &
                   (t >= 0)),
                  p, nans)
        return q.T


class Sphere(Surface):
    """
    Half a sphere of radius R. If R > 0, it is the 'top' half (z > 0)
    and if R < 0 it is the 'bottom' half (z < 0).
    """

    def __init__(self, R:Length=1, *args, **kwargs):
        self.R = R
        self.offset = array((0, 0, self.R))
        if "xsize" in kwargs:
            kwargs["xsize"] = min(kwargs["xsize"], abs(R))
        if "ysize" in kwargs:
            kwargs["ysize"] = min(kwargs["ysize"], abs(R))
        Surface.__init__(self, *args, **kwargs)

    def normal(self, p):
        return -(p + self.offset) / self.R

    def intersect(self, rays):

        rx, ry, rz = r = rays.directions.T
        #if r.z * self.R <= 0:  # backlit
            #print "backlit"
            #return None
        ax, ay, az = a = (rays.endpoints + self.offset).T
        t = quadratic(rz ** 2 + rx ** 2 + ry ** 2,
                      2 * az * rz + 2 * ax * rx + 2 * ay * ry,
                      (az ** 2 + ax ** 2 + ay ** 2) - self.R ** 2)
        # Figure out which intersection we should use
        if self.R > 0:
            p = where(az + np.max(t, axis=0) * rz > 0,
                      a + np.max(t, axis=0) * r,
                      a + np.min(t, axis=0) * r)
        else:
            p = where(az + np.min(t, axis=0) * rz < 0,
                      a + np.min(t, axis=0) * r,
                      a + np.max(t, axis=0) * r)
        px, py, pz = p
        halfxsize = self.xsize / 2
        halfysize = self.ysize / 2
        nans = np.empty((3, len(px)))
        nans[:] = np.NaN
        q = where((np.abs(px) <= halfxsize) & (np.abs(py) <= halfysize),
                  p, nans)
        return q.T - self.offset


class Toroid(Surface):

    """A toroidal surface.

    Note: The meridional (plane of reflection; xz) radius R is the
    radius of the outer *surface*, not the radius at the center of the
    ring. This is the conventional definition (according to Peatman).
    """

    def __init__(self, R:Length=1, r:Length=1, *args, **kwargs):
        self.R = R = abs(R)
        self.r = r = min(R - 1e-10, abs(r))  # crude!
        self._R = R - r
        self.offset = array((0, 0, R))
        if "xsize" in kwargs:
            kwargs["xsize"] = min(kwargs["xsize"], abs(R))
        if "ysize" in kwargs:
            kwargs["ysize"] = min(kwargs["ysize"], abs(r))
        Surface.__init__(self, *args, **kwargs)

    def normal(self, p):
        x, z, y = (p + self.offset).T
        a = x**2 + y**2 + z**2 - self.r**2 - self._R**2
        n = array((4*x * a, 4*z * a + 8 * self._R**2 * z, 4*y * a))
        return -(n / vector_norm(n, axis=0)).T

    def intersect(self, rays):

        rx, ry, rz = r = rays.directions.T
        ax, ay, az = a = (rays.endpoints + self.offset).T

        _R = self._R
        _r = self.r

        A = rx**2 + ry**2 + rz**2
        B = 2*(ax*rx + ay*ry + az*rz)
        C = (ax**2 + ay**2 + az**2) - _r**2 - _R**2

        poly = array((A**2,
                      2*A*B,
                      B**2 + 2*A*C + 4*_R**2*ry**2,
                      2*B*C + 8*_R**2*ay*ry,
                      C**2 + 4*_R**2*ay**2 - 4*_R**2*_r**2)).T
        t = array([np.roots(p) for p in poly]).T

        # Figure out which intersection we should use
        if self._R > 0:
            p = where(az + np.max(t, axis=0) * rz > 0,
                      a + np.real(np.max(t, axis=0)) * r,
                      a + np.real(np.min(t, axis=0)) * r)
        else:
            p = where(az + np.min(t, axis=0) * rz < 0,
                      a + np.real(np.min(t, axis=0)) * r,
                      a + np.real(np.max(t, axis=0)) * r)
        px, py, pz = p
        halfxsize = self.xsize / 2
        halfysize = self.ysize / 2
        nans = np.empty((3, len(px)))
        nans[:] = np.NaN
        q = where((np.abs(px) <= halfxsize) & (np.abs(py) <= halfysize),
                  p, nans)
        return q.T - self.offset

    def from_fermat(self, angle, arm_in, arm_out):
        R = 1 / ((1/arm_in + 1/arm_out) * (cos(radians(angle)) / 2))
        r = 1 / ((1/arm_in + 1/arm_out) / (2 * cos(radians(angle))))
        return Toroid(R=R, r=r, xsize=self.xsize, ysize=self.ysize)


class Cylinder(Surface):

    def __init__(self, R:Length=1.0, *args, **kwargs):
        self.R = R
        self.offset = array((0, 0, R))
        if "ysize" in kwargs:
            kwargs["ysize"] = min(kwargs["ysize"], abs(R * 1.5))
        Surface.__init__(self, *args, **kwargs)

    def normal(self, p):
        r = -(p + self.offset) / self.R
        r[:, 0] = 0
        return r

    def intersect(self, ray):
        rx, ry, rz = r = ray.directions.T

        # if rz * self.R <= 0:  # backlit
        #     return None

        ax, ay, az = a = (ray.endpoints + self.offset).T

        t = quadratic(rz ** 2 + ry ** 2,
                      2 * az * rz + 2 * ay * ry,
                      az ** 2 + ay ** 2 - self.R ** 2)

        # if t is None:  # no intersection
        #     return None
        # else:
        if self.R > 0:
            p = where(az + np.max(t, axis=0) * rz > 0,
                      a + np.max(t, axis=0) * r,
                      a + np.min(t, axis=0) * r)
        else:
            p = where(az + np.min(t, axis=0) * rz < 0,
                      a + np.min(t, axis=0) * r,
                      a + np.max(t, axis=0) * r)
        px, py, pz = p

        halfxsize = self.xsize / 2
        halfysize = self.ysize / 2
        nans = np.empty((3, len(px)))
        nans[:] = np.NaN
        q = where((np.abs(px) <= halfxsize) & (np.abs(py) <= halfysize), p, nans)
        return q.T - self.offset


class Ellipsoid(Surface):

    def __init__(self, a:Length=1.0, b:Length=1.0, c:Length=1.0,
                 *args, **kwargs):
        self.a, self.b, self.c = a, b, c
        self.offset = array((0, 0, c))
        if "xsize" in kwargs:
            kwargs["xsize"] = min(kwargs["xsize"], abs(a))
        if "ysize" in kwargs:
            kwargs["ysize"] = min(kwargs["ysize"], abs(b))
        Surface.__init__(self, *args, **kwargs)

    def normal(self, p):
        """
        Surface normal at point p, calculated through the gradient
        """
        p = -((p + self.offset) *
              (2 / self.a ** 2, 2 / self.b ** 2, 2 / self.c ** 2))
        return (p.T / vector_norm(p, axis=1)).T

    def intersect(self, ray):
        rx, ry, rz = r = ray.directions.T
        p0x, p0y, p0z = p0 = (ray.endpoints + self.offset).T

        a, b, c = self.a, self.b, self.c
        t = quadratic((rz ** 2 + c ** 2 * rx ** 2 / a ** 2 +
                       c ** 2 * ry ** 2 / b ** 2),
                      (2 * p0z * rz + c ** 2 * 2 * p0x * rx /
                       a ** 2 + c ** 2 * 2 * p0y * ry / b ** 2),
                      (p0z ** 2 + c ** 2 * p0x ** 2 / a ** 2 + c ** 2 *
                       p0y ** 2 / b ** 2 - c ** 2))

        # Figure out which intersection we should use
        if self.a * self.b * self.c > 0:
            p = where(p0z + np.max(t, axis=0) * rz > 0,
                      p0 + np.max(t, axis=0) * r,
                      p0 + np.min(t, axis=0) * r)
        else:
            p = where(p0z + np.min(t, axis=0) * rz < 0,
                      p0 + np.min(t, axis=0) * r,
                      p0 + np.max(t, axis=0) * r)
        px, py, pz = p
        xsize = self.xsize / 2
        ysize = self.ysize / 2
        nans = np.empty((3, len(px)))
        nans[:] = np.NaN
        q = where((np.abs(px) <= xsize) & (np.abs(py) <= ysize), p, nans)
        return q.T - self.offset


class Paraboloid(Surface):
    """
    A paraboloid (rotated parabola) described by z/c = (x/a)^2 + (y/b)^2
    """

    def __init__(self, a:Length=1.0, b:Length=1.0, c:Length=1.0,
                 *args, **kwargs):
        self.a = a
        self.b = b
        self.c = c

        Surface.__init__(self, *args, **kwargs)

        self.d = 2 * c / a ** 2
        self.e = 2 * c / b ** 2

        self.concave = a * b * c > 0

    def normal(self, p):
        px, py, pz = p.T
        f = sqrt((self.d * px) ** 2 + (self.e * py) ** 2 + 1)
        return array((self.d * px / f, self.e * py / f, 1 / f)).T

    def intersect(self, rays):
        rx, ry, rz = r = rays.directions.T
        px, py, pz = p = rays.endpoints.T
        a2, b2, c = self.a ** 2, self.b ** 2, -self.c
        t = quadratic(rx ** 2 / a2 + ry ** 2 / b2,
                      2 * px * rx / a2 + 2 * py * ry / b2 - rz / c,
                      px ** 2 / a2 + py ** 2 / b2 - pz / c)
        if self.concave:
            p += np.max(t, axis=0) * r
        else:
            p += np.min(t, axis=0) * r
        px, py, pz = p
        halfxsize = self.xsize / 2
        halfysize = self.ysize / 2
        nans = np.empty((3, len(px)))
        nans[:] = np.NaN
        q = where((np.abs(px) <= halfxsize) & (np.abs(py) <= halfysize),
                  p, nans)

        return q.T
