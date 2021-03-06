from numpy import sqrt, where, allclose


def quadratic(a, b, c):
    """
    Solve a quadratic function a*x**2 + b*y + c = 0
    """
    delta = sqrt(b ** 2 - 4 * a * c)
    x1 = where(a == 0, -c / b, (-b + delta) / (2 * a))
    x2 = where(a == 0, x1, (-b - delta) / (2 * a))
    return (x1, x2)


def closest_points(p, u, q, v):
    """
    Given two lines, described by intersection points p, q and
    directions u, v respectively, calculate the pair of points where
    the lines are closest.

    ==== solution using SymPy ====

    from sympy import *

    p = Matrix(var("p1 p2 p3"))
    q = Matrix(var("q1 q2 q3"))
    u = Matrix(var("u1 u2 u3"))
    v = Matrix(var("v1 v2 v3"))
    s, t = var("s t")
    P = p + s * u
    Q = q + t * v
    PQ = Q - P

    # PQ must be orthogonal to both u and v
    res = solve([PQ.dot(u), PQ.dot(v)], s, t)
    """

    p1, p2, p3 = p
    u1, u2, u3 = u
    q1, q2, q3 = q
    v1, v2, v3 = v

    print(u1, u2, u3)

    # make sure the directions are normalized
    assert allclose(u1**2 + u2**2 + u3**2, 1.0)
    assert allclose(v1**2 + v2**2 + v3**2, 1.0)

    y = 1 - (u1*v1 + u2*v2 + u3*v3)**2

    # plenty of simplification possible here, I'm sure
    if y != 0.0:
        t = (((p1*v1 + p2*v2 + p3*v3 - q1*v1 - q2*v2 - q3*v3) -
              (u1*v1 + u2*v2 + u3*v3) *
              (p1*u1 + p2*u2 + p3*u3 - q1*u1 - q2*u2 - q3*u3)) / y)
    else:
        t = None

    x = 1 - (u1*v1 + u2*v2 + u3*v3)**2

    if x != 0.0:
        s = ((x * (-p1*u1 - p2*u2 - p3*u3 + q1*u1 + q2*u2 + q3*u3) +
              ((p1*v1 + p2*v2 + p3*v3 - q1*v1 - q2*v2 - q3*v3) -
               (u1*v1 + u2*v2 + u3*v3) *
               (p1*u1 + p2*u2 + p3*u3 - q1*u1 - q2*u2 - q3*u3)) *
              (u1*v1 + u2*v2 + u3*v3)) / x)
    else:
        s = t

    # This is pretty ugly
    if t is None:
        t = s

    if t is None and s is None:
        raise ValueError

    return s, t
