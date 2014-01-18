import abc
from collections import OrderedDict, Sequence
import inspect

from numpy import array, ndarray

DEBUG = True


class PhorayBase(object, metaclass=abc.ABCMeta):

    """Baseclass for all Phoray classes, with some basic meta stuff."""

    @abc.abstractmethod
    def __init__(self):
        pass

    @classmethod
    def signature(cls):
        return get_signature(cls)

    @classmethod
    def get_module_name(cls):
        return cls.__module__.split(".")[-1]

    def to_dict(self):
        return object_to_dict(self)


def debug(*args):
    if DEBUG:
        print(args)


def Position(*args):
    if len(args) == 1:
        if isinstance(args[0], dict):
            return array((args[0]["x"], args[0]["y"], args[0]["z"]))
        else:
            return array(args[0])
    elif len(args) == 3:
        return array(args)


def Rotation(x, y, z):
    return array((x, y, z))


class Length(float):
    pass


def get_signature(cls):
    """Return a dict describing the signature of a class' constructor."""
    result = OrderedDict()
    bases = inspect.getmro(cls)
    # walk through the inheritance graph up to, but not including, the
    # "object" class.
    for c in reversed(bases[:-1]):
        s = inspect.signature(c)
        params = s.parameters.items()
        for name, desc in params:
            if not name.startswith("_"):  # ignore attributes starting with "_"
                annot = desc.annotation  # the argument's annotated type info
                if annot != inspect._empty:
                    result[name] = {}
                    default = desc.default  # the argument's default value
                    if default != inspect._empty:
                        result[name]["value"] = default
                    if isinstance(annot, Sequence):
                        result[name]["type"] = Sequence
                        result[name]["subtype"] = annot[0]  # unflexible!
                    else:
                        result[name]["type"] = annot
    return result


def get_baseclass(cls):
    # Primitive way of getting the "canonical" baseclass, e.g.
    # Element, Source, Frame...
    mro = cls.__mro__
    baseclass = mro[-2]
    return baseclass


def object_to_dict(obj):
    objtype = obj.__class__.get_module_name() + "." + obj.__class__.__name__
    #objtype = obj.__class__.__name__
    objdict = {"class": objtype, "args": {}}
    schema = obj.signature()
    for name in schema:
        value = getattr(obj, name)
        objdict["args"][name] = convert_attr(value)
    # if hasattr(obj, "_id"):
    #     objdict["args"]["_id"] = obj._id
    return objdict


def convert_attr(attr):
    if hasattr(attr, "signature"):
        return object_to_dict(attr)
    elif isinstance(attr, ndarray):
        return dict(x=float(attr[0]), y=float(attr[1]), z=float(attr[2]))
    elif isinstance(attr, (list, tuple)):  # FIXME: too specific
        return [object_to_dict(item)
                if hasattr(item, "signature") else item
                for item in attr]
    else:
        return attr
