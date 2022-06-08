#! /usr/bin/env python3
#
# Create a fake MET like data stream
#
# May-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import numpy as np
from shapely.geometry import Point
from shapely.ops import transform
import pyproj
from TPWUtils import Logger
import logging
import os
import math
import time
import yaml
import json
import sys

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--output", type=str, default="met.csv", help="Output CSV filename")
parser.add_argument("--yaml", type=str, default="pe.yaml", help="Input parameters")
parser.add_argument("--seed", type=int, default=int(time.time()), help="Random seed")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s", logLevel=logging.INFO)

with open(args.yaml, "r") as fp: info = yaml.safe_load(fp)

logging.info("Seed %s", args.seed)
logging.info("%s ->\n%s", args.yaml, json.dumps(info, indent=4, sort_keys=True))

rng = np.random.default_rng(args.seed)

dt = info["dt"]
vel = info["SOG"]
theta = info["COG"]
ctheta = math.cos(math.radians(theta))
stheta = math.sin(math.radians(theta))
direction = +1

lengthLimit = info["length"]
saltLimits = info["saltFront"] + info["saltWidth"] * np.array([-1, 1]) 
tempLimits = info["tempFront"] + info["tempWidth"] * np.array([-1, 1])
saltValues = np.array([info["saltNorth"], info["saltSouth"]])
tempValues = np.array([info["tempNorth"], info["tempSouth"]])

wgs84 = pyproj.CRS("EPSG:4326")
utm = pyproj.CRS("EPSG:32618")
project2UTM = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
project2WGS = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform
pt0 = transform(project2UTM, Point(info["lonCentroid"], info["latCentroid"]))
print(pt0)

offset = Point(0, 0) # UTM offset

if not os.path.isfile(args.output):
    dirname = os.path.dirname(args.output)
    if not os.path.isdir(dirname):
        os.makedirs(dirname, 0o766, exist_ok=True)
    with open(args.output, "w") as fp: fp.write("time,longitude,latitude,salinity,temperature\n")

while True:
    now = time.time()
    nxt = (math.floor(now / dt) + 1) * dt
    time2sleep = nxt - now
    logging.info("Sleeping for %s seconds", time2sleep)
    time.sleep(time2sleep)
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(math.floor(time.time() / dt) * dt))
    dist = dt * vel
    offset = Point(offset.x + direction * stheta * dist, offset.y + direction * ctheta * dist)
    pt1 = transform(project2WGS, Point(pt0.x + offset.x, pt0.y + offset.y))
    dist = math.sqrt(offset.x * offset.x + offset.y * offset.y)
    if dist > lengthLimit: # Flip the direction
        direction *= -1

    # Now interpolate salinity and temperature
    salt = float(np.interp(dist, saltLimits, saltValues) 
            + rng.standard_normal(1) * info["saltNoise"])
    temp = float(np.interp(dist, tempLimits, tempValues) 
            + rng.standard_normal(1) * info["tempNoise"])

    line = f"{now},{pt1.x:.6f},{pt1.y:.6f},{salt:0.3f},{temp:0.2f}"
    with open(args.output, "a") as fp: fp.write(line + "\n")
