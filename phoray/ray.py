from __future__ import division
from random import randint

from numpy import array
from numpy import ma

from .solver import closest_points


class Rays(object):

    def __init__(self, endpoints, directions, wavelengths):
        self.endpoints = ma.array(endpoints)
        self.directions = ma.array(directions)
        self.wavelengths = ma.array(wavelengths)

    def __repr__(self):
        return "%r, %r, %r" % (
            self.endpoints, self.directions, self.wavelengths)

    def __len__(self):
        return len(self.endpoints)

    def estimate_focus(self, samples=None):

        """
        A fairly stupid way to find the focus of the rays, by simply
        locating the center of where a number of randomly sampled ray
        pairs are closest to each oher.
        """

        total = len(self.endpoints)
        samples = samples or max(1, total // 100)

        xsum = ysum = zsum = 0

        for r in range(samples):
            n1 = randint(0, total-1)
            p1 = self.endpoints[n1]
            r1 = self.directions[n1]
            n2 = randint(0, total-1)
            while n2 == n1:
                n2 = randint(0, total-1)
            p2 = self.endpoints[n2]
            r2 = self.directions[n2]
            try:
                s, t = closest_points(p1, r1, p2, r2)
            except ValueError:
                samples -= 1
                continue
            x1, y1, z1 = p1 + s*r1
            x2, y2, z2 = p2 + t*r2

            xsum += (x1 + x2)
            ysum += (y1 + y2)
            zsum += (z1 + z2)

        if samples:
            return xsum / (2*samples), ysum / (2*samples), zsum / (2*samples)
        else:
            return None
