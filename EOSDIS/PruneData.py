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
        logging.debug("No need to prune %s", ofn)
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
            xr.open_dataset(fn, group="scan_line_attributes", decode_times=False) as scan:

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

        t = (scan.year - 1970).astype("datetime64[Y]")
        t+= (scan.day - 1).astype("timedelta64[D]") # 1-Jan is day 1, so offset by 1
        t+= scan.msec.astype("timedelta64[ms]")
        t = t.astype(float) / 1e9 # Convert to unix time
        t = np.tile(t, (nav.longitude.shape[1], 1)).T

        df = xr.Dataset({
                    "lon": (("i","j"), nav.longitude.data),
                    "lat": (("i","j"), nav.latitude.data),
                    "t": (("i","j"), t),
                    },
                    coords = {
                        "i": np.arange(nav.longitude.shape[0]),
                        "j": np.arange(nav.longitude.shape[1]),
                        },
                )
        
        nLatLon = df.lon.size # Number after lat/lon box

        # for points outside lat/lon box, due to swath angle, set them to NaN
        qLatLon =  np.logical_not(np.logical_and(
                np.logical_and(df.lon >= lonMin, df.lon <= lonMax),
                np.logical_and(df.lat >= latMin, df.lat <= latMax),
                )).data


        encBase = {"zlib": True, "complevel": 9}
        enc = {"lon": encBase, "lat": encBase}

        df = df.assign({"qFinite": (("i","j"), np.zeros(df.lon.shape))})
        for key in sorted(names):
            df = df.assign({key: (("i","j"), geo[key].data)})
            df[key].data[qLatLon] = None
            enc[key] = encBase
            for item in names[key]:
                if item in geo.variables:
                    qual = geo[item].data
                    (llim, ulim) = names[key][item]
                    qBad = np.logical_or(qual < llim, qual > ulim)
                    val = df[key].data
                    val[qBad] = None
                    df[key].data = val
            df.qFinite.data += np.isfinite(df[key].data)

        # filter columns and rows which have no finite values
        df = df.sel(j=df.j[df.qFinite.sum(dim="i") != 0])
        df = df.sel(i=df.i[df.qFinite.sum(dim="j") != 0])

        # Find times of "good" observations
        t = df.t.data.flatten()[df.qFinite.data.flatten() != 0]

        if t.size == 0: # Nothing finite left
            logging.debug("No data in finite box in %s", fn)
            return None

        # Convert to unix seconds
        attributes = {
            "units": "seconds since 1970-01-01 00:00:00",
            "calendar": "proleptic_gregorian",
            }

        df = df.assign({
            "tMin":   ([], t.min(),      attributes),
            "tMax":   ([], t.max(),      attributes),
            "tMean":  ([], t.mean(),     attributes),
            "tMedian":([], np.median(t), attributes),
            })
        df = df.drop(("t", "qFinite"))

        logging.info("Pruned %s %s%%",
                os.path.basename(fn),
                round(df.lon.size / nOrig * 100, 1),
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
