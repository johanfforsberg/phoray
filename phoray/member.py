from math import *
from abc import ABCMeta, abstractmethod

from numpy import array, dot, ones, zeros, radians, ndarray
from numpy.linalg import inv as inverse_matrix

from .transformations import (euler_matrix, translation_matrix,
                              concatenate_matrices)
from .ray import Rays
from .phoray import current_id
from . import PhorayBase, Position


class Member(PhorayBase, metaclass=ABCMeta):

    """Baseclass for a generalized member of an optical system.

    Contains methods to convert from and to the local coordinate system.
    """

    def __init__(self, position:Position=(0, 0, 0), rotation:Position=(0, 0, 0),
                 _id:int=None):
        self.position = Position(position)
        self.rotation = Position(rotation)

        if _id is None:
            self._id = next(current_id)
        else:
            self._id = _id

        # Precalculate some matrices. Note that this means that the
        # frame can't be changed after creation, unless
        # calculate_matrices is called again afterwards.
        self.calculate_matrices()

    def calculate_matrices(self):
        rotate = euler_matrix(*radians(self.rotation), axes="rxyz")

        self._matloc = concatenate_matrices(
            inverse_matrix(rotate), translation_matrix(-self.position)).T
        self._matglob = inverse_matrix(self._matloc)

    def localize_position(self, v):
        """Turn global (relative to the frame) coordinates into local."""
        tmp = ones((len(v), 4))  # make 4-vectors for translations
        tmp[:, :3] = v
        return dot(tmp, self._matloc)[:, :3]

    def localize_direction(self, v):
        """A direction does not change with translation."""
        tmp = zeros((len(v), 4))  # make 4-vectors for translations
        tmp[:, :3] = v
        return dot(tmp, self._matloc)[:, :3]

    def globalize_position(self, v):
        """Turn local coordinates into global."""
        tmp = ones((len(v), 4))  # make 4-vectors for translations
        tmp[:, :3] = v
        return dot(tmp, self._matglob)[:, :3]

    def globalize_direction(self, v):
        """A direction does not change with translation."""
        tmp = zeros((len(v), 4))  # make 4-vectors for translations
        tmp[:, :3] = v
        return dot(tmp, self._matglob)[:, :3]

    def localize(self, rays):
        """
        Transform a Ray in global coordinates into local coordinates
        """
        local_endp = self.localize_position(rays.endpoints)
        local_dir = self.localize_direction(rays.directions)

        return Rays(local_endp, local_dir, rays.wavelengths)

    def globalize(self, rays):
        """
        Transform a local Ray into global coordinates
        """
        global_endp = self.globalize_position(rays.endpoints)
        global_dir = self.globalize_direction(rays.directions)

        return Rays(global_endp, global_dir, rays.wavelengths)

    def x_axis(self):
        return self.globalize_vector(array((1, 0, 0)))

    def y_axis(self):
        return self.globalize_vector(array((0, 1, 0)))

    def z_axis(self):
        return self.globalize_vector(array((0, 0, 1)))

    @abstractmethod
    def trace(self, incoming, n):
        pass
