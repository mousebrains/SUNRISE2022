#! /usr/bin/env python3
#
# Join multiple ADCP files togetheer
#
# June-2022, Jamie Hilditch

from argparse import ArgumentParser
import logging
import xarray as xr
import netCDF4
import glob
import os
import re
import sys

def findFiles(args:ArgumentParser) -> dict:
    pattern = os.path.abspath(os.path.expanduser(os.path.join(
        args.adcp, args.pattern + "*" ,"proc", "*", "contour", "*.nc")))
    files = {}
    toExclude = None
    if args.exclude:
        toExclude = []
        for item in args.exclude:
            toExclude.append(re.compile(item))
    
    for fn in glob.glob(pattern):
        if toExclude:
            qSkip = False
            for item in toExclude:
                if item.search(fn):
                    logging.debug("Skipping %s %s", fn, item)
                    qSkip = True
                    break
            if qSkip: continue

        mtime = os.path.getmtime(fn)
        adcp = os.path.basename(fn)[:-3]
        if adcp not in files: files[adcp] = {}
        if mtime not in files[adcp]: files[adcp][mtime] = []
        files[adcp][mtime].append(fn)

    adcps = {}
    for adcp in sorted(files):
        adcps[adcp] = []
        for mtime in sorted(files[adcp]):
            adcps[adcp].extend(files[adcp][mtime])

    return adcps

def concatenate_adcp(adcp:str, source: list[str], args:ArgumentParser) -> None:
    target = os.path.join(args.processed,
            args.cruise + "_" + args.platform + "_" + adcp + "_concat.nc")

    logging.debug("ADCP %s source %s tgt %s", adcp, source, target)

    if not os.path.isfile(target): # create the target file if it does not exist
        # use the first of the source files as a template
        # however we need to ensure the time dimension is unlimited
        # therefore use xarray to do the copy
        tmp = xr.open_dataset(source[0]) # Source is sorted based on mtime
        tmp.to_netcdf(target,unlimited_dims=("time"),format="NETCDF3_CLASSIC")
        logging.info("Created %s from %s", target, source[0])

    # now open the target file and the source files as a multifile dataset
    with netCDF4.MFDataset(source, aggdim='time') as src, \
        netCDF4.Dataset(target,'a') as tgt:

        tgt_idx = len(tgt.dimensions["time"])
        src_idx = len(src.dimensions["time"])

        # check there is new data to add
        if tgt_idx >= src_idx:
            logging.info("No new data for %s", adcp)
            return

        logging.info("%s target length %s source length %s adding %s datapoints",
                adcp, tgt_idx, src_idx, src_idx-tgt_idx)

        # these datasets have no groups so we can simply loop over the variables
        for key in tgt.variables.keys():
            tgt_shape = tgt[key].shape

            # skip scalar variables
            if not tgt_shape: continue

            # append new data
            if len(tgt_shape) == 1: # Vector
                tgt[key][tgt_idx:src_idx] = src[key][tgt_idx:src_idx]
            elif len(tgt_shape) == 2: # Array
                tgt[key][tgt_idx:src_idx,:] = src[key][tgt_idx:src_idx,:]
            else:
                raise ValueError(f"ADCP shape issue, {adcp} {key} shape %s{tgt_shape}")


if __name__ == "__main__":
    from TPWUtils import Logger

    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--pattern", type=str, required=True, help="UHDAS pattern to concatenate")
    parser.add_argument("--exclude", type=str, action="append",
            help="Regular expressions in patterns to exclude")
    parser.add_argument("--platform", type=str, help="2 letter platform prefix")
    parser.add_argument("--adcp", type=str, default="/mnt/adcp", help="UHDAS directory")
    parser.add_argument("--processed", type=str, default="/mnt/sci/data/Processed_NC/ADCP_UHDAS",
            help="Location to store concatenated files")
    parser.add_argument("--cruise", type=str, default="SUNRISE2022", help="Cruise prefix")
    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

    if args.platform is None: args.platform = args.pattern[:2]

    logging.info("Args %s", args)

    files = findFiles(args)

    for adcp in files:
        try:
            concatenate_adcp(adcp, files[adcp], args)
        except:
            logging.exception("Error processing %s", adcp)
