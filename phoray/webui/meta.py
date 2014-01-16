from collections import OrderedDict
from inspect import getmembers, isclass, getmro, isabstract
from imp import find_module, load_module
from itertools import chain
from operator import itemgetter
from pprint import pprint

from phoray import PhorayBase, frame, element, surface, source
from .schema import make_schema

# Some plugin stuff, not really ready for use
# PLUGIN_DIR = "plugins"
# plugins = [os.path.splitext(mod)[0]
#            for mod in os.listdir(PLUGIN_DIR) if mod.endswith(".py")]
# plugin_classes = [
#     #(plugin + "." + name, cls)
#     (name, cls) for plugin, module
#     in ((plug, load_module(plug, *find_module(plug, [PLUGIN_DIR])))
#         for plug in sorted(plugins))
#     for name, cls in sorted(getmembers(module, isclass), key=itemgetter(0))]


def get_classes(module):
    """Return a dict of Phoray classes contained in a given module."""
    module_dict = module.__dict__
    if "__all__" in module_dict:
        class_members = ((name, module_dict[name])
                         for name in module_dict["__all__"])
    else:
        class_members = sorted(getmembers(module, isclass),
                               key=itemgetter(0))
    return OrderedDict(("%s.%s" % (cls.get_module_name(), name), cls)
                       for name, cls in class_members
                       if cls.__module__ == module.__name__ and
                       PhorayBase in getmro(cls) and
                       not isabstract(cls))

# List all the things we can create
classes = dict(frame=get_classes(frame), element=get_classes(element),
               source=get_classes(source), surface=get_classes(surface))
classes["member"] = OrderedDict(chain(classes["frame"].items(),
                                      classes["element"].items(),
                                      classes["source"].items()))
print("\n".join(classes["member"].keys()))

schemas = make_schema(classes)


def hash_dict(d):
    return hash(repr(sorted(d.items())))


def create_geometry(spec={}):
    """Create a Surface instance from specifications."""
    cls = classes["surface"].get(spec.get("class", "surface.Plane"))
    geometry = cls(**spec.get("args", {}))
    return geometry


def create_member(spec={}, path=""):
    member_type = spec.get("class", list(classes["member"].keys())[0])
    cls = classes["member"][member_type]
    print(cls.get_module_name(), cls.__name__)
    schema = schemas["definitions"][cls.get_module_name()][cls.__name__]["properties"]\
             ["args"]["properties"]
    args = {key: value for key, value in spec.get("args", {}).items()
            if key in schema}
    pprint(args)
    if "children" in schema:
        args["children"] = [
            create_member(sp, "%s/args/children/%d" % (path, i))
            for i, sp in enumerate(args.get("children", []))]
    if "geometry" in schema:
        args["geometry"] = create_geometry(args.get("geometry", {}))
    mem = cls(**args)
    return mem


def object_from_spec(spec):
    # wip
    module, clsname = spec["class"].split(".")
    schema = schemas["definitions"][module][clsname]
    arguments = {}
    cls = classes[module][module + "." + clsname]
    signature = cls.signature()
    for arg, argspec in signature.items():
        argschema = schema["properties"]["args"]["properties"][arg]
        if "$ref" in argschema:
            print(arg, spec["args"][arg])
            value = object_from_spec(spec["args"][arg])
        elif "items" in argschema:
            if argschema["items"]["type"] == "object":
                print(arg, spec["args"][arg])
                value = [object_from_spec(a) for a in spec["args"][arg]]
            else:
                value = spec["args"][arg]
        else:
            value = spec[arg]
        arguments[arg] = value
    return cls(**arguments)

#create_member = object_from_spec

# def create_element(spec={}):
#     """Create an Element instance from specifications."""
#     cls = classes["Element"][spec.get("class", "Mirror")]
#     args = spec.get("args", {})
#     geo = create_geometry(args.get("geometry", {}))
#     args["children"] = [create_element(spec)
#                         for spec in args.get("children", [])]
#     args["geometry"] = geo
#     element = cls(_id=spec.get("_id"), **args)
#     return element


# def create_frame(spec={}):
#     return member.Frame(_id=spec.get("_id"), **spec.get("args", {}))


# def create_source(spec={}):
#     """Create a Source instance from specifications."""
#     cls = classes["Source"].get(spec.get("type", "GaussianSource"))
#     args = spec.get("args", {})
#     args["frames"] = [create_frame(framespec) for framespec in args.get(
#         "frames", [dict(args=dict(position=(0, 0, 0),
#                                   rotation=(0, 0, 0)))])]
#     source = cls(_id=spec.get("_id"), **args)
#     return source
