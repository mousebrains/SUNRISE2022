#! /usr/bin/env python3
#
# Output fresh database records to a growing NetCDF file
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from TPWUtils import SingleInstance
from Config import Config
from tempfile import NamedTemporaryFile # For atomic operations
import psycopg2 # For PostgreSQL access
import logging
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import xarray as xr
import os
import sys
import time
import datetime

def buildNC(fn:str, args:ArgumentParser, cols:tuple[str]) -> Dataset:
    doubles = ("t", "longitude", "latitude", "lon", "lat")
    variables = {}
    for col in cols:
        if col in ["t"]: continue
        variables[col] = ("t", np.empty(0, dtype=np.double if col in doubles else np.single))
    ds = xr.Dataset(data_vars=variables,
        coords=dict(t=np.empty(0, dtype=np.double)))
    ds.t.attrs["units"] = "seconds since 1970-01-01 00:00:00"
    ds.to_netcdf(fn, unlimited_dims="t")

def writeNC(fn:str, df:pd.DataFrame) -> None:
    logging.info("Writing %s rows to %s", df.shape[0], fn)
    with Dataset(fn, mode="a") as nc:
        v = nc.variables
        n = v["t"].size
        for col in df.columns:
            a = df[col].astype(float)
            if col == "t" or np.any(np.isfinite(a)):
                v[col][n:] = a

parser = ArgumentParser()
Logger.addArgs(parser)
Config.addArgs(parser)
parser.add_argument("--force", action="store_true", help="Ignore qNetCDF flag in database")
parser.add_argument("--dryrun", action="store_true", help="Do not commit database changes")
parser.add_argument("--db", type=str, default="sunrise", help="Input database")
parser.add_argument("--table", type=str, default="met", help="Table to fetch data from")
parser.add_argument("nc", type=str, nargs="+", help="Output netcdf filename(s)")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

stime = time.time()

config = Config(args)

if not config.netcdf:
    logging.info("No netcdf information in %s for %s", args.yaml, args.key)
    sys.exit(0)

if "columns" not in config.netcdf:
    logging.info("NetCDF information is missing columns in %s for %s", args.yaml, args.key)
    sys.exit(1)

cols = config.netcdf["columns"]
columns = ["t"]
sqlCols = ["EXTRACT(EPOCH FROM t)::BIGINT as t"]
for col in cols:
    if col == "t": continue
    columns.append(col)
    sqlCols.append(col)

sql = "SELECT " + ",".join(sqlCols) + " FROM " + args.table
sql+= " WHERE ship=%s"
sqlArgs = [config.ship]
if not args.force:
    sql+= " AND qNetCDF=false"
if ("decimate" in config.netcdf) and config.netcdf["decimate"].isnumeric():
    dt = config.netcdf["decimate"]
    sql+= f" AND (EXTRACT(EPOCH FROM t) %% %s)=0"
    sqlArgs.append(dt)
sql+= " ORDER BY t ASC;"

sqlDates = f"SELECT min(t),max(t) FROM {args.table} WHERE ship=%s"
if not args.force:
    sqlDates+= " AND qNetCDF=false"
sqlDates+= ";"

sqlUpdate = f"UPDATE {args.table} SET qNetCDF=true"
sqlUpdate+= " WHERE t>=%s AND t<=%s AND ship=%s AND qNetCDF=false;"

nToFetch = 40000

with SingleInstance.SingleInstance(sys.argv[0] + "/" + args.key) as single:
    fn0 = args.nc[0] # Only work with first file, then rsync it to the others
    if not os.path.isfile(fn0): buildNC(fn0, args, columns) # empty nc file

    cnt = 0

    with psycopg2.connect(f"dbname={args.db}") as db:
        try:
            cur = db.cursor()
            cur.execute(sqlDates, (config.ship,)) # Get min/max dates
            (t0, t1) = cur.fetchone()

            cur.execute(sql, sqlArgs)
            rows = cur.fetchmany(size=nToFetch)
            while rows: # Walk through all the chunks
                n = len(rows)
                cnt += n
                writeNC(fn0, pd.DataFrame(rows, columns=columns))
                rows = cur.fetchmany(size=nToFetch)

            if cnt == 0:
                logging.info("No updates to %s took %s seconds", fn0, time.time()-stime)
                sys.exit(0)

            logging.info("Wrote %s rows to %s in %s seconds", cnt, fn0, time.time()-stime)
            stime=time.time()
            try:
                cur.execute("BEGIN;")
                cur.execute(sqlUpdate, (t0, t1, config.ship))
                if args.dryrun:
                    db.rollback()
                else:
                    db.commit()
            except:
                db.rollback()
                logging.exception("Error executing %s", sqlUpdate)
            logging.info("Took %s seconds to update", time.time() - stime)
        except SystemExit:
            pass
        except:
            logging.exception("Error executing %s", sql)
            sys.exit(1)

    if (cnt == 0) or (len(args.nc) == 1): sys.exit(0)

    stime = time.time()

    ofps = []
    ofns = {}
    for fn in args.nc[1:]: # Walkt through the rest of the targets and update from fn0
        tgt = os.path.abspath(os.path.expanduser(fn))
        fp = NamedTemporaryFile(dir=os.path.dirname(fn), delete=False)
        ofps.append(fp)
        ofns[fn] = fp.name

    with open(fn0, "rb") as ifp:
        while True:
            buffer = ifp.read(1024*1024) # 1MB at a time
            if not buffer: break # EOF
            for ofp in ofps: ofp.write(buffer)

    for ofp in ofps: ofp.close()

    logging.info("%s seconds to make copies", time.time() - stime)
    stime = time.time()

    mtime = os.path.getmtime(fn0)
    atime = os.path.getatime(fn0)

    for fn in ofns:
        os.chmod(ofns[fn], 0o664)
        os.utime(fn, times=(mtime,atime))
        os.rename(ofns[fn], fn)
    logging.info("%s seconds to adjust copies", time.time() - stime)
