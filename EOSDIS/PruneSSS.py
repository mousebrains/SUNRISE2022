#! /usr/bin/env python3
#
# Prune Sea Surface Salinity satellite data
#
# May-2022, Pat Welch, pat@mousebrains.com

from LoadYAML import loadYAML
import xarray as xr
import numpy as np
import json
import os
import sys
import logging

def pruneSSS(info:dict, fn:str, dirname:str, force:bool=False) -> str:
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

    if "varNames" not in info:
        logging.error("varNames not in YAML file\n%s", json.dumps(info, indent=4, sort_keys=True))
        return None

    varNames = info["varNames"]

    with xr.open_dataset(fn) as ds:
        names = {}
        for key in varNames:
            if key in ds.variables:
                names[key] = varNames[key]

        if not names:
            logging.error("No varNames found in %s", fn)
            return None

        qLatLon = np.logical_and( # points inside our lat/lon box
                np.logical_and(ds.lon >= lonMin, ds.lon <= lonMax),
                np.logical_and(ds.lat >= latMin, ds.lat <= latMax)).data

        if not qLatLon.any():
            logging.info("No data in lat/lon box in %s", fn)
            return None # Nothing to prune

        qLine = qLatLon.any(axis=1) # There is a point in this line we are interested in
        qPixel = qLatLon.any(axis=0) # There is a point in this pixel column we are interested in

        nOrig = ds.lon.size # Original number of elements

        ds = ds.sel(phony_dim_0=qLine, phony_dim_1=qPixel)

        rt = ds.row_time.data
        if isinstance(rt[0], np.float32):
            t = np.datetime64(int(ds.attrs["REV_START_YEAR"]) - 1970, "Y")
            t+= np.timedelta64(int(ds.attrs["REV_START_DAY_OF_YEAR"]) - 1, "D")
            t = t + rt.astype("timedelta64[s]") # Not in place due to size change
        else: # Datetime64
            t = rt

        t = np.tile(t, [ds.lon.shape[0], 1])

        df = xr.Dataset({
                    "lon": (("i","j"), ds.lon.data),
                    "lat": (("i","j"), ds.lat.data),
                    "t": (("i","j"), t),
                    },
                    coords = {
                        "i": np.arange(ds.lon.shape[0]),
                        "j": np.arange(ds.lon.shape[1]),
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
            df = df.assign({key: (("i","j"), ds[key].data)})
            df[key].data[qLatLon] = None
            enc[key] = encBase
            for item in names[key]:
                if item in ds.variables:
                    qual = ds[item].data
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
            logging.info("No data in finite box in %s", fn)
            return None

        t = t.astype(float) / 1e9 # UTC seconds
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
        pruneSSS(info, fn, args.pruned, args.force)
