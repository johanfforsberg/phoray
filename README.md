## PHORAY ##

A "physical" raytracer written in python.

This is a sequential raytracer written in python. It's different from
most raytracers in that it calculates the rays *forward* in the
direction of light propagation, instead of backwards from the image
plane. It is not intended for producing images of reflective spheres,
but rather for simulating optical systems.


## License ##

Copytight 2013 Johan Forsberg (johan@slentrian.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

<http://www.gnu.org/licenses/>

Several third party JS libraries are included in the webui part, they
are covered by their respective licenses and are only included here
for convenience.


## Disclaimer ##

This software is *very* rough and has lots of known issues. It is
undergoing heavy development, and things may change without
notice. View it as a toy and do not even consider relying on it for
anything what so ever.


## Installation ##

*TODO*


## Requirements ##

*Phoray requires Python v3.x.*

It also depends on the following python modules:

* numpy (http://www.numpy.org/).
* jsonpatch (https://github.com/stefankoegl/python-json-patch)

Numpy has some heavy dependencies and should probably be installed
through whatever means is recommended for your operatins system;
e.g. through the package manager on Linux.

Jsonpatch can easily be installed from PyPi, e.g. using pip:

    pip install --user jsonpatch


## Usage ##

See examples. *TODO:* update the examples.

There is also a very experimental and incomplete browser UI, which can
be started by running "./run_server" in the phoray directory. Then
point a *WebGL capable* browser to http://localhost:8080 and play
around. (Note: only recent versions of Chrome and Firefox have been
tested and are known to work.)


## Running Unit Tests ##

Run "nosetests" (requires 'Nose' to be installed).
