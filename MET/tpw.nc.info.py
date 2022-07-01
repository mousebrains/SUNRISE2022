#! /usr/bin/env python3
#
# Print min/max dates and min/max time step
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import xarray as xr
import numpy as np

parser = ArgumentParser()
parser.add_argument("nc", type=str, nargs="+", help="NetCDF files to inspect")
args = parser.parse_args()

for fn in args.nc:
    with xr.open_dataset(fn) as ds:
        dt = np.diff(ds.t.data) / 1e9
        q = np.quantile(dt, np.linspace(0,1,11))
        print(fn, "n", ds.t.size, "tmin", ds.t.min().data, "tmax", ds.t.max().data)
        print("Quantiles", q)
