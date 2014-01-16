from __future__ import division
from numpy import array
from numpy import ma


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
