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

def pruneData(info:dict, fn:str, dirname:str, force:bool=False) -> str:
    if not os.path.isfile(fn):
        logging.error("%s is not a file", fn)
        return None

    basename = os.path.basename(fn)
    ofn = os.path.join(dirname, basename)

    if not force and os.path.isfile(ofn) and (os.path.getmtime(fn) < os.path.getmtime(ofn)):
        logging.info("No need to prune %s", ofn)
        return ofn

    for key in ["latMin", "latMax", "lonMin", "lonMax"]:
        if key not in info:
            logging.error("%s not in info", key)
            return None

    lonMin = min(info["lonMin"], info["lonMax"])
    lonMax = max(info["lonMin"], info["lonMax"])
    latMin = min(info["latMin"], info["latMax"])
    latMax = max(info["latMin"], info["latMax"])

    if "geoNames" not in info:
        logging.error("geoNames not in YAML file\n%s", json.dumps(info, indent=4, sort_keys=True))
        return None

    geoNames = info["geoNames"]

    with \
            xr.open_dataset(fn) as todo, \
            xr.open_dataset(fn, group="geophysical_data") as geo, \
            xr.open_dataset(fn, group="navigation_data") as nav, \
            xr.open_dataset(fn, group="scan_line_attributes") as scan:

        names = {}
        for key in geoNames:
            if key in geo.variables:
                names[key] = geoNames[key]

        if not names:
            logging.error("No geonames found in %s", fn)
            return None

        qLatLon = np.logical_and( # points inside our lat/lon box
                np.logical_and(nav.longitude >= lonMin, nav.longitude <= lonMax),
                np.logical_and(nav.latitude >= latMin, nav.latitude <= latMax)).data

        if not qLatLon.any():
            logging.debug("No data in lat/lon box in %s", fn)
            return None # Nothing to prune

        qLine = qLatLon.any(axis=1) # There is a point in this line we are interested in
        qPixel = qLatLon.any(axis=0) # There is a point in this pixel column we are interested in

        nOrig = nav.longitude.size # Original number of elements

        geo = geo.sel(number_of_lines=qLine, pixels_per_line=qPixel)
        nav = nav.sel(number_of_lines=qLine, pixel_control_points=qPixel)
        scan = scan.sel(number_of_lines=qLine)
        t = ((scan.year - 1970).astype("datetime64[Y]") + scan.day + scan.msec).data
        t = np.tile(t, (nav.longitude.shape[1], 1)).T

        # Now flatten and further filter on lat/lon and finite

        df = xr.Dataset({
                    "lon": ("i", nav.longitude.data.flatten()),
                    "lat": ("i", nav.latitude.data.flatten()),
                    "t": ("i", t.flatten()),
                    },
                    coords = {"i": np.arange(nav.longitude.size)},
                )
        
        nLatLon = df.lon.size # Number after lat/lon box

        encBase = {"zlib": True, "complevel": 9}
        enc = {"lon": encBase, "lat": encBase}

        q = np.zeros(df.t.size, dtype=bool)
        for key in sorted(names):
            df = df.assign({key: ("i", geo[key].data.flatten())})
            enc[key] = encBase
            for item in names[key]:
                if item in geo.variables:
                    qual = geo[item].data.flatten()
                    (llim, ulim) = names[key][item]
                    qKeep = np.logical_and(qual >= llim, qual <= ulim)
                    df[key][np.logical_not(qKeep)] = None
            qKey = np.isfinite(df[key].data)
            q = np.logical_or(q, qKey)

        df = df.sel(i=df.i[q])

        nFinite = df.lon.size # Number ofter quality check

        if not nFinite: return None # Nothing left

        df = df.assign({
            "tMin": df.t.min(),
            "tMax": df.t.max(),
            "tMean": df.t.mean(),
            })
        df = df.drop("t")

        qLatLon = np.logical_and(
                np.logical_and(df.lon >= lonMin, df.lon <= lonMax),
                np.logical_and(df.lat >= latMin, df.lat <= latMax),
                )
        df.sel(i=df.i[qLatLon])

        nLatLon2 = df.lon.size

        logging.info("Pruned %s %s%% lat/lon %s%% finite %s%%",
                os.path.basename(fn),
                round(nLatLon2 / nOrig * 100, 1),
                round(nLatLon / nOrig * 100, 1),
                round(nFinite / nOrig * 100, 1),
                )
        df.to_netcdf(ofn, encoding=enc)
        return ofn


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force pruning")
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
        pruneData(info, fn, args.pruned, args.force)
