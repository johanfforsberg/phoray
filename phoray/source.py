import abc
from itertools import chain
from random import seed, randint, gauss
from sys import maxsize

from numpy import (array, ones, zeros, random, sum,
                   linspace, meshgrid, hstack, vstack)
from numpy.linalg import norm
from .member import Member
from .ray import Rays
from . import Rotation, Position, Length


class Source(Member, metaclass=abc.ABCMeta):

    "Source base class"

    def __init__(self, wavelength:Length=0.0, color:str="#ffffff",
                 *args, **kwargs):

        Member.__init__(self, *args, **kwargs)
        self.wavelength = wavelength
        self.color = color

        self.axis = array((0., 0., 1.0))

    @abc.abstractmethod
    def generate(self, n):
        """Needs to be overridden by child classes.
        Should return Rays, probably limited by n.
        """

    def trace(self, incoming, n=1):
        traces = self.generate(n)
        return dict(chain(incoming.items(), [(self._id, [traces])]))


class TrivialSource(Source):

    """A very simple pointsource that sends out rays in one direction."""

    def generate(self, n=1):
        endpoints = zeros((n, 3))
        directions = ones((n, 3)) * self.axis
        rays = Rays(endpoints, directions, zeros(n))
        return self.globalize(rays)


class GridSource(Source):

    """Sends out rays in a regular grid shape."""

    def __init__(self, size:Position=(0, 0, 0), divergence:Position=(0, 0, 0),
                 resolution:int=10, *args, **kwargs):
        self.size = Position(size)
        self.divergence = Position(divergence)
        self.resolution = resolution
        Source.__init__(self, *args, **kwargs)

    def generate(self, _=None):
        """TODO: make it more efficient by skipping identical rays."""
        n = self.resolution
        sx, sy, sz = self.size
        s = vstack(hstack(array(meshgrid(*(linspace(-s/2, s/2, n)
                                           for s in self.size))).T))

        dx, dy, dz = self.divergence
        d = vstack(hstack(array(meshgrid(linspace(-dx/2, dx/2, n),
                                         linspace(-dy/2, dy/2, n),
                                         zeros(n))).T + self.axis))
        d = (d.T / sum(d**2, axis=1)**0.5).T
        rays = self.globalize(
            Rays(endpoints=s, directions=d,
                 wavelengths=ones((n**3,)) * self.wavelength))

        return rays


class GaussianSource(Source):

    """A source that sends out rays according to a Gaussian distribution,
    in both origin and direction.

    FIXME: the divergence is only correct for small angles.
    """

    def __init__(self, size:Position=(0, 0, 0),
                 divergence:Position=(0, 0, 0),
                 random_seed:int=randint(0, maxsize),
                 *args, **kwargs):
        self.size = Position(size)
        self.divergence = Position(divergence)
        self.random_seed = random_seed
        random.seed(random_seed)

        Source.__init__(self, *args, **kwargs)

    def generate(self, n=1):

        sx, sy, sz = self.size
        s = array((zeros(n) if sx == 0 else random.normal(0, sx, n),
                   zeros(n) if sy == 0 else random.normal(0, sy, n),
                   zeros(n) if sz == 0 else random.normal(0, sz, n))).T

        dx, dy, dz = self.divergence
        d = array((zeros(n) if dx == 0 else random.normal(0, dx, n),
                   zeros(n) if dy == 0 else random.normal(0, dy, n),
                   zeros(n))).T + self.axis
        d = (d.T / sum(d**2, axis=1)**0.5).T  # this can't be the best way
                                              # to normalize the directions
        rays = self.globalize(Rays(endpoints=s, directions=d,
                                   wavelengths=ones((n,)) * self.wavelength))

        return rays
