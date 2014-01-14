from collections import defaultdict
from math import *

from .member import Member
from .element import Element, Glass, Mirror
from .surface import Sphere
from .source import Source
from .ray import Ray


class Frame(Member):

    def __init__(self, children:[Member], *args, **kwargs):
        self.children = children
        Member.__init__(self, *args, **kwargs)

    def _localize_trace(self, trace):
        return {source: [self.localize(rays[0])]
                for source, rays in trace.items()}

    def trace(self, incoming=None, n=1):
        incoming = incoming or {}
        local_trace = self._localize_trace(incoming)
        outgoing = defaultdict(list)
        for c in self.children:
            local_trace = c.trace(local_trace, n)
            for source, rays in local_trace.items():
                outgoing[source] += [self.globalize(r) for r in rays]
        return outgoing


class GroupFrame(Frame):
    pass


# === stuff below should be moved into plugins or something ===

class SphericalLens(Frame):

    def __init__(self, R1:float=1.0, R2:float=1.0, thickness:float=0.1,
                 index:float=1.5, *args, **kwargs):
        self.R1 = R1
        self.R2 = R2
        self.index = index
        self.thickness = thickness

        glass1 = Glass(index1=1.0, index2=index, position=(0, 0, -thickness/2),
                       geometry=Sphere(-R1))
        glass2 = Glass(index1=index, index2=1.0, position=(0, 0, thickness/2),
                       geometry=Sphere(R2))
        if "children" in kwargs:
            del kwargs["children"]
        Frame.__init__(self, children=[glass1, glass2], *args, **kwargs)


class SequentialElement(Frame):

    def __init__(self, a:int=0, b:float=1.0, *args, **kwargs):
        self.a = a
        self.b = b
        Frame.__init__(self, *args, **kwargs)

    def make_member(self):
        return Mirror(geometry=Sphere())


class SequentialSystem(Frame):

    def __init__(self, elements:[SequentialElement]=[], *args, **kwargs):
        self.elements = elements
        if "children" in kwargs:
            del kwargs["children"]
        children = [SequentialElement(el).make_member() for el in elements]
        Frame.__init__(self, children=children, *args, **kwargs)
