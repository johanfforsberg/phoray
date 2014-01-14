from collections import OrderedDict
import inspect
from pprint import pprint

import numpy as np

from phoray import surface, element, source, member
from phoray import Length, Position, Rotation


def list_to_dict(l):
    return OrderedDict(zip(map(str, range(len(l))), l))


def dict_to_list(d):
    pprint(d)
    indexes = d.keys()
    l = []
    if indexes:
        for i in range(int(max(indexes)) + 1):
            l.append(d[str(i)] if str(i) in d else {})
    return l


def dictdiff(d1, d2):
    c = {}
    for k in d2:
        if k not in d1:
            c[k] = d2[k]
            continue
        if d2[k] != d1[k]:
            if not (isinstance(d2[k], dict) or isinstance(d2[k], list)):
                c[k] = d2[k]
            else:
                if isinstance(d1[k], type(d2[k])):
                    c[k] = d2[k]
                    continue
                else:
                    if isinstance(d2[k], dict):
                        c[k] = dictdiff(d1[k], d2[k])
                        continue
                    elif isinstance(d2[k], list):
                        c[k] = dict_to_list(dictdiff(list_to_dict(d1[k]),
                                                     list_to_dict(d2[k])))
    return c


def object_to_dict(obj, schemas):
    objtype = obj.__class__.__name__
    objdict = {"class": objtype, "args": {}}
    schema = schemas[id(obj.__class__)]
    for name in schema:
        value = getattr(obj, name)
        objdict["args"][name] = convert_attr(value, schemas)
    # if hasattr(obj, "_id"):
    #     objdict["_id"] = obj._id
    return objdict


# def system_to_dict(obj, schemas, objtype=None):
#     schema = schemas["System"]
#     if objtype is None:
#         objtype = obj.__class__.__name__
#     objdict = {"type": objtype, "args": {}}
#     for name in schema[objdict["type"]]:
#         value = getattr(obj, name)
#         objdict["args"][name] = convert_attr(value, schema)
#     pprint(objdict)
#     if hasattr(obj, "_id"):
#         objdict["_id"] = obj._id
#     objdict["elements"] = [object_to_dict(el, schemas) for el in obj.elements]
#     objdict["sources"] = [object_to_dict(so, schemas) for so in obj.sources]
#     return objdict


def convert_attr(attr, schemas):
    if isinstance(attr, surface.Surface):
        return object_to_dict(attr, schemas)
    elif isinstance(attr, list):
        return [object_to_dict(item, schemas) for item in attr]
    elif isinstance(attr, np.ndarray):
        return dict(x=float(attr[0]), y=float(attr[1]), z=float(attr[2]))
    else:
        return attr


def signature(cls):
    """Takes a class and tries to figure out the types of its arguments.

    TODO: This is horrible.
    """

    sig = OrderedDict()
    bases = inspect.getmro(cls)
    for base in reversed(bases[:-1]):  # skip the object class
        #print()
        spec = base.__init__.__annotations__
        argspec = inspect.getfullargspec(base.__init__)
        arg_names = argspec[0]
        defaults = argspec[3] if argspec[3] else []
        #print(base.__name__, "argspec", argspec)
        arg_defaults = [None] * (len(arg_names) - len(defaults)) + list(defaults)

        args = [a for a in zip(argspec[0], arg_defaults)
                if a[0] in spec]  # keep the arguments in order
        #print("signature args", args)
        for arg, default in args:
            annot = spec[arg]
            argsubtype = None
            argtype = annot
            value = default
            if not arg.startswith("_"):  # ignore underscored arguments
                if argtype in (Position, np.ndarray, tuple):
                    argtype = "vector"
                    value = (dict(x=0, y=0, z=0) if not default
                             else dict(x=default[0], y=default[1], z=default[2]))
                elif type(argtype) == list:
                    if len(argtype) > 0:
                        argsubtype = argtype[0].__name__
                    argtype = "list"
                    value = default or []
                else:
                    argtype = argtype.__name__
                sig[arg] = dict(type=str(argtype), value=value)
                if argsubtype:
                    sig[arg]["subtype"] = argsubtype
    return sig
