from numpy import array, float64


def position(x, y, z):
    return array((x, y, z), dtype=float64)


def direction(x, y, z):
    return array((x, y, z), dtype=float64)
