from unittest import TestCase
from numpy import allclose


class PhorayTestCase(TestCase):

    def assertAllClose(self, a, b, **kwargs):
        assert allclose(a, b, **kwargs), "Not close: %r, %r" % (a, b)
