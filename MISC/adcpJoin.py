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
import sys

def concatenate_adcp(adcp:str, files: list, args:ArgumentParser) -> None:
    source = os.path.join(args.adcp, args.pattern + "*", "proc", adcp, "contour", adcp + ".nc")
    target = os.path.join(args.processed,
            args.cruise + "_" + args.platform + "_" + adcp + "_concat.nc")

    logging.debug("ADCP %s source %s tgt %s", adcp, source, target)

    # create the target file if it does not exist
    if not os.path.isfile(target):
        # use the first of the source files as a template
        # however we need to ensure the time dimension is unlimited
        # therefore use xarray to do the copy
        files = sorted(files) # Earliest first
        template = files[0]
        tmp = xr.open_dataset(template)
        tmp.to_netcdf(target,unlimited_dims=("time"),format="NETCDF3_CLASSIC")
        logging.info("Created %s from %s", target, template)

    # now open the target file and the source files as a multifile dataset
    with netCDF4.MFDataset(source, aggdim='time') as src, \
        netCDF4.Dataset(target,'a') as tgt:

        tgt_idx = len(tgt.dimensions["time"])
        src_idx = len(src.dimensions["time"])
        logging.info("%s target length %s source length %s adding %s datapoints",
                adcp, tgt_idx, src_idx, src_idx-tgt_idx)

        # check there is new data to add
        if tgt_idx >= src_idx:
            logging.info("No new data for %s", adcp)
            return

        # these datasets have no groups so we can simply loop over the variables
        for key in tgt.variables.keys():
            tgt_shape = tgt[key].shape
            src_shape = src[key].shape

            # skip scalar variables
            if not tgt_shape: continue

            # append new data
            if len(tgt_shape) == 1:
                tgt[key][tgt_idx:src_idx] = src[key][tgt_idx:src_idx]
            elif len(tgt_shape) == 2:
                tgt[key][tgt_idx:src_idx,:] = src[key][tgt_idx:src_idx,:]
            else:
                raise ValueError(f"ADCP, {adcp} {key}, variables have either 1 or 2 dimensions")


if __name__ == "__main__":
    from TPWUtils import Logger

    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--pattern", type=str, required=True, help="UHDAS pattern to concatenate")
    parser.add_argument("--platform", type=str, help="2 letter platform prefix")
    parser.add_argument("--adcp", type=str, default="/mnt/adcp", help="UHDAS directory")
    parser.add_argument("--processed", type=str, default="/mnt/sci/data/Processed_NC/ADCP_UHDAS",
            help="Location to store concatenated files")
    parser.add_argument("--cruise", type=str, default="SUNRISE2022", help="Cruise prefix")
    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

    if args.platform is None: args.platform = args.pattern[:2]

    files = {}
    for fn in glob.glob(os.path.join(args.adcp, args.pattern + "*", "proc", "*", "contour", "*.nc")):
        adcp = os.path.basename(fn)[:-3]
        if adcp not in files: files[adcp] = []
        files[adcp].append(fn)

    logging.info("ADCPS %s", files)

    logging.info("Args %s", args)
    for adcp in files:
        try:
            concatenate_adcp(adcp, files[adcp], args)
        except:
            logging.exception("Error processing %s", adcp)
