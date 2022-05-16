#! /usr/bin/env python3
#
# Load satellite data that has been downloaded 
# and prune to a lat/lon box
# Also, variables are reduced to a minimal set for
# being sent to ship
#
# May-2022, Pat Welch, pat@mousebrains.com

from LoadYAML import loadYAML
import xarray as xr
import numpy as np
import json
import os
import sys
import logging

def pruneData(info:dict, fn:str, dirname:str) -> str:
    for key in ["latMin", "latMax", "lonMin", "lonMax"]:
        if key not in info:
            logging.error("%s not in info", key)
            sys.exit(1)

    lonMin = min(info["lonMin"], info["lonMax"])
    lonMax = max(info["lonMin"], info["lonMax"])
    latMin = min(info["latMin"], info["latMax"])
    latMax = max(info["latMin"], info["latMax"])

    if "geoNames" in info:
        geoNames = info["geoNames"]
    else:
        geoNames = ["sst", "sst4", "chlor_a", "chl_ocx", "nflh", "sst_triple"]

    basename = os.path.basename(fn)
    ofn = os.path.join(dirname, basename)
    logging.info("Pruning %s -> %s", fn, ofn)
    with \
            xr.open_dataset(fn) as todo, \
            xr.open_dataset(fn, group="geophysical_data") as geo, \
            xr.open_dataset(fn, group="navigation_data") as nav, \
            xr.open_dataset(fn, group="scan_line_attributes") as scan:
        qLatLon = np.logical_and( # points inside our lat/lon box
                np.logical_and(nav.longitude >= lonMin, nav.longitude <= lonMax),
                np.logical_and(nav.latitude >= latMin, nav.latitude <= latMax)).data

        if not qLatLon.any():
            logging.debug("Nothing left in %s", fn)
            return None # Nothing to prune

        qLine = qLatLon.any(axis=1) # There is a point in this line we are interested in
        qPixel = qLatLon.any(axis=0) # There is a point in this pixel column we are interested in
        geo = geo.sel(number_of_lines=qLine, pixels_per_line=qPixel)
        nav = nav.sel(number_of_lines=qLine, pixel_control_points=qPixel)
        scan = scan.sel(number_of_lines=qLine)
        t = ((scan.year - 1970).astype("datetime64[Y]") + scan.day + scan.msec).data

        encBase = {"zlib": True, "complevel": 9}
        enc = {"t": encBase, "lon": encBase, "lat": encBase}

        geoItems = {}
        geoKeys = set(geo.keys())
        for key in geoNames:
            if key in geoKeys:
                geoItems[key] = (("t", "pixel"), geo[key].data)
                enc[key] = encBase

        if not geoItems:
            logging.error("Unsupported geo names in %s\n%s", fn, geo)
            return None

        ods = xr.Dataset(data_vars={
            "lon": (("t", "pixel"), nav.longitude.data),
            "lat": (("t", "pixel"), nav.latitude.data),
            },
            coords={
                "t": t,
                "pixel": np.arange(geo.dims["pixels_per_line"]),
                },
            attrs={"filename":fn},
            )
        ods = ods.assign(geoItems)
        ods.to_netcdf(ofn, encoding=enc)
        return ofn


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--yaml", type=str, default="SUNRISE.yaml", help="YAML configuration file")
    parser.add_argument("--pruned", type=str, default="data/Pruned", help="Where to store pruned data")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose messages")
    parser.add_argument("raw", type=str, nargs="+", help="Input NetCDF files")
    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
            level=logging.DEBUG if args.verbose else logging.INFO)

    info = loadYAML(args.yaml)
    logging.debug("%s ->\n%s", args.yaml, json.dumps(info, indent=True, sort_keys=True))

    if not os.path.isdir(args.pruned):
        logging.info("Making %s", args.pruned)
        os.makedirs(args.pruned, mode=0o755, exist_ok=True)
        
    for fn in args.raw:
        pruneData(info, fn, args.pruned)
