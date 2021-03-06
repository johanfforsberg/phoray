from __future__ import division
from collections import defaultdict
from math import *
from abc import ABCMeta, abstractmethod

from numpy import array, NaN, empty, isfinite

from .member import Member
from .surface import Surface
from .ray import Rays

__all__ = ["Mirror", "Detector", "Screen", "ReflectiveGrating"]


class Element(Member, metaclass=ABCMeta):

    """This abstract class represents an optical element, i.e. something
    that can be used to change the path of rays during a trace. It cannot
    be instantiated itself, but should be inherited by real element
    classes.
    """

    def __init__(self, geometry:Surface, save_footprint=True, *args, **kwargs):
        self.geometry = geometry
        self.save_footprint = save_footprint
        self.footprint = defaultdict(list)
        Member.__init__(self, *args, **kwargs)

    def trace(self, incoming, _):
        outgoing = {}
        for source, rays in incoming.items():
            new_rays = self.propagate(self.localize(rays[-1]))
            if self.save_footprint:
                fp = array((new_rays.endpoints.T[0],
                            new_rays.endpoints.T[1],
                            new_rays.wavelengths))
                # remove rays that missed
                self.footprint[source] = fp.T[isfinite(fp[0])]
            outgoing[source] = [self.globalize(new_rays)]
        return outgoing

    @abstractmethod
    def propagate(self, rays):
        """Return the rays as modified by the element; e.g. reflected."""


class Mirror(Element):

    """A mirror reflects incoming rays in its surface."""

    def __init__(self, use_fermat:bool=False, incidence_angle:float=10,
                 entrance_arm:float=1, exit_arm:float=1, *args, **kwargs):
        self.exit_arm = exit_arm
        self.entrance_arm = entrance_arm
        self.incidence_angle = incidence_angle
        self.use_fermat = use_fermat
        geo = kwargs.get("geometry")
        if hasattr(geo, "from_fermat"):
            if use_fermat:
                kwargs["geometry"] = geo.from_fermat(incidence_angle,
                                                     entrance_arm, exit_arm)
        else:
            self.use_fermat = False

        Element.__init__(self, *args, **kwargs)

    def propagate(self, rays):
        return self.geometry.reflect(rays)


class Detector(Element):

    """A detector does not propagate rays further. It is intended to
    be the final element in a system.
    """

    def propagate(self, rays):
        p = self.geometry.intersect(rays)
        nans = empty((len(rays), 3))
        nans[:] = (NaN, NaN, NaN)
        return Rays(p, nans, rays.wavelengths)


class Screen(Element):

    """A screen does not interact with the direction of the imcoming
    rays, but simply passes them through. Useful for checking the
    intersection of a beam.
    """

    def propagate(self, rays):
        p = self.geometry.intersect(rays)
        return Rays(p, rays.directions, rays.wavelengths)


class ReflectiveGrating(Element):

    """A reflective grating diffracts incoming rays reflectively."""

    def __init__(self, d:float=0., order:int=0, *args, **kwargs):
        """
        Define a reflecting element with geometry shape given by s. If
        d>0 it will work as a grating with line spacing d and lines in
        the xz-plane and diffraction order given by order. Otherwise
        it works as a plain mirror.
        """
        self.d = d
        self.order = order
        #print "Mirror", args, kwargs
        Element.__init__(self, *args, **kwargs)

    def propagate(self, rays):
        diffracted_rays = self.geometry.diffract(
            rays, self.d, self.order)
        return diffracted_rays


class ReflectiveVLSGrating(Mirror):

    """A grating with varying line spacing. Not complete."""

    def __init__(self, an:[float]=[1.0], *args, **kwargs):
        self.an = an
        Mirror.__init__(self, *args, **kwargs)

    def get_line_distance(self, p):
        """
        Returns the local grating line density according to VLS
        parameters a(x) = a_0 + a_1*x + ... + a_n*x^n where x is the
        distance to the grating center.
        """

        y = 1000 * p.y
        R = 1000 * self.geometry.R
        x = copysign(sqrt(y ** 2 + (R - sqrt(R ** 2 - y ** 2))), y)
        x = 2 * R * asin(x / (2 * R))
        #x=y
        b = -x / sqrt(R ** 2 - x ** 2)
        theta = atan(b)  # grating tangent angle
        #print b, theta
        d = 0
        for n, a in enumerate(self.an):
            d += a * x ** n
        d *= cos(theta)
        return 1e-3 / d

    def propagate(self, rays):
        diffracted_rays = self.geometry.diffract(rays, None, self.order,
                                                 self.get_line_distance)
        return self.globalize(diffracted_rays)


class Glass(Element):

    """A glass surface, defined by the refraction indices on each side."""

    def __init__(self, index1:float=1.0, index2:float=1.0, *args, **kwargs):
        self.index1 = index1
        self.index2 = index2
        Element.__init__(self, *args, **kwargs)

    def propagate(self, rays):
        refracted_rays = self.geometry.refract(rays, self.index1,
                                               self.index2)
        return refracted_rays
