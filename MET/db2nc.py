#! /usr/bin/env python3
#
# Output fresh database records to a growingn NetCDF file
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from Config import Config
import psycopg2
import logging
import os.path
from netCDF4 import Dataset
import numpy as np
import sys

def buildNC(args:ArgumentParser, cols:tuple[str]) -> Dataset:
    doubles = ("t", "longitude", "latitude", "lon", "lat")
    with Dataset(args.nc, mode="w", format="NETCDF4") as nc:
        nc.title = args.key
        nc.createDimension("t", None)
        for col in cols:
            nc.createVariable(col, 
                    np.float64 if col in doubles else np.float32, 
                    ('t',))
        nc.variables["t"].units = "seconds since 1970-01-01 00:00:00"

def writeNC(fn:str, data:dict) -> None:
    with Dataset(args.nc, mode="a")  as nc:
        sz = nc.variables["t"].size
        t = np.array(data["t"])
        i = sz + np.arange(t.size)
        nc.variables["t"][i] = t
        for key in data:
            if key == "t": continue
            nc.variables[key][i] = np.array(data[key])

parser = ArgumentParser()
Logger.addArgs(parser)
Config.addArgs(parser)
parser.add_argument("--db", type=str, default="sunrise", help="Input database")
parser.add_argument("--table", type=str, default="met", help="Table to fetch data from")
parser.add_argument("--nc", type=str, required=True, help="Output netcdf filename")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

config = Config(args)

if not config.netcdf:
    logging.info("No netcdf information in %s for %s", args.yaml, args.key)
    sys.exit(0)

if "columns" not in config.netcdf:
    logging.info("NetCDF information is missing columns in %s for %s", args.yaml, args.key)
    sys.exit(1)

cols = config.netcdf["columns"]
tindex = cols.index("t")

if ("decimate" in config.netcdf) and config.netcdf["decimate"].isnumeric():
    dt = config.netcdf["decimate"]
else:
    dt = None

if not os.path.isfile(args.nc):
    buildNC(args, cols)

sql = "WITH updated AS ("
sql+= f"UPDATE {args.table} SET qNetCDF=true"
sql+= f" WHERE ship='{config.ship}' AND qNetCDF=false"
if dt is not None:
    sql+= f" AND (EXTRACT(EPOCH FROM t) % {dt})=0"
sql+= " RETURNING "
sql+= ",".join(cols)
sql+= ") SELECT * FROM updated ORDER BY t ASC;"

data = {}
for col in cols: data[col] = []

with psycopg2.connect(f"dbname={args.db}") as db:
    cur = db.cursor()
    cur.execute("BEGIN;")
    try:
        cur.execute(sql)
        times = []
        for row in cur:
            for index in range(len(cols)):
                key = cols[index]
                if key == "t":
                    data[key].append(row[index].timestamp())
                else:
                    data[key].append(row[index])
        logging.info("Wrote %s records to %s", len(data["t"]), args.nc)

        writeNC(args.nc, data)
        cur.execute("COMMIT;")
    except:
        cur.execute("ROLLBACK;")
        logging.error("Error executing %s", sql)
        sys.exit(1)
