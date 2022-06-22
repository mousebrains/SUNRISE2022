#! /usr/bin/env python3
#
# Join multiple ADCP files togetheer
#
# June-2022, Jamie Hilditch

from argparse import ArgumentParser
import logging
import netCDF4
import os
import xarray as xr

def concatenate_adcp(adcp: str, args:ArgumentParser) -> None:
    # source = f"/mnt/adcp/PE22_31_Shearman_ADCP_*/proc/{adcp}/contour/{adcp}.nc"
    # target = f"/mnt/sci/data/Processed_NC/ADCP_UHDAS/{adcp}_concat.nc"
    source = os.path.join(args.src, "proc", adcp, "contour", adcp + ".nc")
    target = args.tgt + adcp + "_concat.nc"

    logging.info("ADCP %s src %s tgt %s", adcp, source, target)

    # create the target file if it does not exist
    if not os.path.isfile(target):

        # use the first of the source files as a template
        # however we need to ensure the time dimension is unlimited
        # therefore use xarray to do the copy
        if adcp == "wh600":
            template = source.replace("*","2",1)
        else:
            template = source.replace("*","1",1)
        if not os.path.isfile(template):
            raise FileNotFoundError(f"Source file '{template}' does not exist")
        tmp = xr.open_dataset(template)
        tmp.to_netcdf(target,unlimited_dims=("time"),format="NETCDF3_CLASSIC")
        logging.info("Created %s from %s", target, template)

    # now open the target file and the source files as a multifile dataset
    with netCDF4.MFDataset(source,aggdim='time') as src, \
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
    parser.add_argument("--adcp", type=str, action="append", help="ADCP system(s) to join")
    parser.add_argument("--src", type=str, default="/mnt/adcp/PE22_31_Shearman_ADCP_*",
            help="Where UHDAS ADCP source files are")
    parser.add_argument("--tgt", type=str,
            default="/mnt/sci/data/Processed_NC/ADCP_UHDAS/SUNRISE2022_PE_",
            help="Where to store the output")

    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

    if args.adcp is None:
        args.adcp = ["wh1200", "wh600", "wh300"]

    logging.info("Args %s", args)

    for adcp in args.adcp:
        try:
            concatenate_adcp(adcp, args)
        except:
            logging.exception("Error processing %s", adcp)
