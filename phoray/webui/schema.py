import builtins
from collections import OrderedDict, Sequence
from itertools import chain

from phoray import Length, Position
from phoray.surface import Surface
from phoray.member import Member


def type_or_ref(t, mapping):
    """Return an appropriate JSON-schema description; either a type or a
    reference to another description, for the given type (assuming it
    is known).
    """
    # maps from python types to JSON-schema
    m = mapping.get(t.__name__)
    if m is None:
        return m
    else:
        return {"$ref": m} if m.startswith("#") else {"type": m}


def schema_from_class(cls, mapping):
    """Create a JSON schema for the constructor of a class."""
    name = cls.__name__
    signature = cls.signature()
    schema = OrderedDict()
    module = cls.get_module_name()
    schema["title"] = "%s.%s" % (module, name)
    schema["type"] = "object"
    schema["properties"] = props = {}
    schema["additionalProperties"] = False
    schema["required"] = ["class", "args"]
    props["class"] = {"enum": ["%s.%s" % (module, name)]}
    props["args"] = args = {"type": "object"}
    args["properties"] = props2 = OrderedDict()
    for arg, spec in signature.items():
        t = spec["type"]
        m = type_or_ref(t, mapping)
        if m is not None:
            props2[arg] = m
            if m.get("type") == "array":
                m2 = type_or_ref(spec["subtype"], mapping)
                if m2 is not None:
                    props2[arg]["items"] = m2
            if spec.get("value"):
                props2[arg]["default"] = spec["value"]
    args["additionalProperties"] = False
    args["required"] = list(props2.keys())
    return schema


def make_schema(classes):
    """Create a JSON schema covering all the available classes."""

    schema = OrderedDict()
    schema["$schema"] = "system-schema.json"
    schema["title"] = "Phoray schema"
    schema["$ref"] = "#/definitions/frame/GroupFrame"

    type_mapping = {
        # simple types
        "int": "integer",
        "Length": "number",
        "float": "number",
        "str": "string",
        "bool": "boolean",
        "Sequence": "array",
        # custom classes refer to their respective definitions
        "Position": "#/definitions/Vector",
        "Surface": "#/definitions/Geometry",
        "Member": "#/definitions/Member"}
    for base, subclss in classes.items():
        for name in subclss:
            type_mapping[name] = "#/definitions/%s/%s" % (base, name)

    member_subclasses = OrderedDict()
    for name, cls in classes["member"].items():
        member_subclasses[name] = schema_from_class(cls, type_mapping)
    geometry_subclasses = OrderedDict(
        (name, schema_from_class(cls, type_mapping))
        for name, cls in list(classes["surface"].items())[:])


    # member_subclasses = OrderedDict(
    #     (name, schema_from_class(cls, type_mapping))
    #     for name, cls in chain(list(classes["Frame"].items())[:],
    #                            list(classes["Element"].items())[:],
    #                            list(classes["Source"].items())[:]))

    schema["definitions"] = definitions = OrderedDict()

    definitions["Member"] = {
        "title": "Member",
        "type": "object",
        "oneOf": [{"$ref": "#/definitions/" + name.replace(".", "/")}
                  for name in member_subclasses.keys()]}

    definitions["Vector"] = {
        "type": "object",
        "properties": OrderedDict((
            ("x", {"type": "number"}),
            ("y", {"type": "number"}),
            ("z", {"type": "number"})
        )),
        "additionalProperties": False,
        "required": ["x", "y", "z"]}

    definitions["Geometry"] = {
        "type": "object",
        "oneOf": [{"$ref": "#/definitions/%s" % name.replace(".", "/")}
                  for name in geometry_subclasses]}

    definitions["frame"] = {name.split(".")[-1]: member_subclasses[name]
                            for name in classes["frame"]}
    definitions["element"] = {name.split(".")[-1]: member_subclasses[name]
                              for name in classes["element"]}
    definitions["source"] = {name.split(".")[-1]: member_subclasses[name]
                             for name in classes["source"]}
    definitions["surface"] = {name.split(".")[-1]: geometry_subclasses[name]
                              for name in classes["surface"]}
    # definitions.update(geometry_subclasses)
    # definitions.update(member_subclasses)

    return schema


# def test_schema_from_class():
#     from phoray import surface, element
#     from pprint import pprint
#     print(json.dumps(schema_from_class(surface.Toroid), indent=4))
#     print(json.dumps(schema_from_class(element.ReflectiveGrating), indent=4))


def test_make_schema():
    from meta import classes
    print(json.dumps(make_schema(classes), indent=4))

if __name__ == "__main__":
    import json
    #test_schema_from_class()
    test_make_schema()
