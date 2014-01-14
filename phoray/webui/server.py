#!/usr/bin/env python3

import json
from pprint import pprint
from time import time

from numpy import isnan, ndarray
from bottle import (Bottle, request, run, static_file, JSONPlugin,
                    response)
import jsonpatch

from .meta import schemas, create_member, create_geometry
from phoray.frame import GroupFrame


class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ndarray):  # and obj.ndim == 1:
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

app = Bottle()
app.install(JSONPlugin(
    json_dumps=lambda s: json.dumps(s, cls=NumpyAwareJSONEncoder)))


# == Route callbacks ===

@app.route('/')
def staticindex():
    return static_file('index.html', root='phoray/webui/ui')


@app.route('/static/<filepath:path>')
def staticpath(filepath):
    return static_file(filepath, root='phoray/webui/ui')


@app.get('/system-schema.json')
def get_schema():
    #print(json.dumps(schemas, indent=4))
    return schemas


@app.post('/system')
def define_system():
    global data  # please...
    #patch = request.json
    #new_spec = jsonpatch.apply_patch(spec, patch)
    new_spec = request.json
    print(json.dumps(new_spec, indent=4))
    data = create_member(new_spec)
    final_spec = data.to_dict()
    diff = jsonpatch.JsonPatch.from_diff(new_spec, final_spec)
    return diff.to_string()


@app.get('/system')
def get_system():
    response.set_header(
        "Content-Type", "application/json;"
        "profile=system-schema.json#/definitions/GroupFrame")
    print(json.dumps(data.to_dict(), indent=4))
    return json.dumps(data.to_dict())


@app.get('/create')
def create():
    query = request.query
    print("create", dict(query))
    member = create_member(query)
    result = member.to_dict()
    pprint(result)
    return result


@app.post('/mesh')  # this should be GET
def get_mesh():
    """Return a mesh representation of an element."""
    query = request.json
    spec = query["spec"]
    geo = create_geometry(spec)
    verts, faces = geo.mesh()
    return {"verts": verts, "faces": faces}


@app.get('/trace')
def trace():
    """Trace the paths of a number of rays through a system."""
    t0 = time()
    query = request.query
    #system = data[int(query.system)]
    #print("trace")
    #pprint(data)
    n = int(query.n)  # number of rays to trace
    traces = data.trace(n=n)
    #pprint(traces)
    # Format the footprint data for consumption by the UI.
    # Separates out the failed rays and add "dummies" for
    # non-terminated ones. TODO: should be easier.
    result = {}
    for source, trace in traces.items():
        succeeded = []
        failed = []
        for i in range(n):
            tmp2 = []
            for j, tr in enumerate(trace):
                broke = False
                if isnan(tr.endpoints[i][0]):
                    tmp2.append(tuple(trace[j-1].endpoints[i] +
                                      trace[j-1].directions[i]))
                    broke = True
                    break
                else:
                    tmp2.append(tuple(tr.endpoints[i]))
            if broke:
                failed.append(tmp2)
            else:
                if not isnan(tr.directions[i][0]):
                    tmp2.append(tuple(tr.endpoints[i] + tr.directions[i]))
                succeeded.append(tmp2)
        result[source] = dict(succeeded=succeeded, failed=failed)

    dt = time() - t0
    print("traced %d rays, took %f s." % (n, dt))
    return dict(traces=result, time=dt)


@app.get('/footprint')
def footprint():
    """Return the current traced footprint for the given element."""
    query = request.query
    sys_n = int(query.system)   # the containing system's index
    ele_n = int(query.element)  # the chosen element's index

    return {"footprint": data[sys_n].elements[ele_n].footprint}


data = GroupFrame([])

def main():
    import sys
    args = sys.argv
    if len(args) > 1:
        jsonfile = args[1]
        try:
            with open(jsonfile) as f:
                jsondata = json.load(f)
                global data
                data = create_member(jsondata)
        except FileNotFoundError as e:
            sys.exit("Could not find JSON file '%s': %s" % (jsonfile, e))
        except ValueError as e:
            sys.exit("Could not parse JSON file '%s': %s" % (jsonfile, e))

    # Start the server
    run(app, host='localhost', port=8080, debug=True, reloader=True)


if __name__ == "__main__":
    main()
