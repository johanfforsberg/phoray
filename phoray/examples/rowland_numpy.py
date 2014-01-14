import csv
from math import degrees, atan
from pprint import pprint
from time import time

import sys
sys.path.append("../")
print(sys.path)

from phoray.frame import GroupFrame as Group
from phoray.surface import Sphere, Plane, Cylinder
from phoray.element import ReflectiveGrating, Detector, Mirror
from phoray.source import GaussianSource
from .rowland2 import Rowland



"""Simulate a Rowland (spherical grating) spectrometer

The result is written to a textfile, "rowland.dat", where each line
describes one ray's position on the detector and its wavelength. It
can easily be plotted, e.g.:

import numpy as np
import matplotlib.pyplot as plt
data = np.loadtxt("rowland.dat").T
p = plt.scatter(data[0], data[1], c=data[2], s=0.1, linewidth=0)
"""

# parameters for a Rowland spectrometer, SI units unless otherwise stated
angle = 2        # incidence angle on the grating (degrees)
energy = 500     # center energy of the incident light (eV)
order = -1       # diffraction order to look at
R = 5.0          # radius of the grating
d = 1200e3       # grating line density, m^-1

# Grating, centered at origin
s = Sphere(5.0, xsize=0.1, ysize=0.1)
sg = ReflectiveGrating(d=1/d, order=order, geometry=s,
                       rotation=(90, 0, 0))

# Detector
p = Plane(xsize=0.1, ysize=0.1)
row = Rowland(R_gr=R, d_gr=d/1000, theta_in=angle)
detx, dety = row.add_ray(energy, order, 0)   # calculate the focal
det = Detector(geometry=p, position=(0, dety, detx),
               rotation=(90-degrees(2*atan(dety/detx)), 0., 0.))

# Incoming light distribution
xdisp = 10e-3     # divergence angle in horizontal direction (sigma, rad)
ydisp = 1e-3     # vertical divergence
xslit = 1e-4      # horizontal entrance slit / source size (sigma)
yslit = 1e-5      # vertical slit size

# To simulate three emission lines, we create three sources with
# equidistant energies, but otherwise identical.
dE = 1.0        # energy difference between lines (eV)
srcs = [GaussianSource(position=(0, row.source_y, row.source_x),
                       rotation=(angle, 0, 0),
                       size=(xslit, yslit, 0),
                       divergence=(xdisp, ydisp, 0),
                       wavelength=6.626068e-34*2.9979e8/(en*1.60217e-19))
        for en in (energy-dE, energy, energy+dE)]

# putting the whole system together
s = Group((Group(srcs), sg, det))

pprint(s.to_dict())

n_rays = 100000  # number of rays to calculate (per source)

print("Tracing %d rays..." % n_rays)
t0 = time()
trace = s.trace(n=n_rays)
print("Done, took %f s" % (time() - t0))

datafile = "rowland.dat"
print("Writing detector image to '%s'" % datafile)
with open(datafile, "w") as f:
    f.write("# xpos [m]\typos [m]\twavelength [m]\n")
    w = csv.writer(f, delimiter="\t")
    for energy in list(s.children[-1].footprint.values()):
        w.writerows(energy)

import json
with open("rowland.json", "w") as f:
    json.dump(s.to_dict(), f, indent=4)
