#! /usr/bin/env python3
#
# Join the NAV and ADCP data together and save to a netcdf file
#
# July-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
import logging
import psycopg2
import xarray as xr
import numpy as np
import pandas as pd
import netCDF4
import datetime
import os

def mkCTDTable(cur):
    sql = """
CREATE TABLE IF NOT EXISTS rhibTodoCTD (
    ship TEXT NOT NULL,
    box INTEGER NOT NULL,
    t TIMESTAMP WITH TIME ZONE NOT NULL,
    n INTEGER NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    temp REAL NOT NULL,
    SP REAL NOT NULL,
    qCSV bool DEFAULT false,
    qNetCDF bool DEFAULT false,
    PRIMARY KEY(ship,t)
    );
"""
    cur.execute(sql)

def mkTimeTable(cur):
    sql = """
CREATE TABLE IF NOT EXISTS rhibTimesCTD (
    ship TEXT PRIMARY KEY NOT NULL,
    t TIMESTAMP WITH TIME ZONE NOT NULL
    );
"""
    cur.execute(sql)

def joinTables(cur, ship:str, tLast:datetime.datetime) -> datetime.datetime:
    sql = """
INSERT INTO rhibTodoCTD
SELECT 
    rhibCTD.ship as ship,
    rhibCTD.box as box,
    rhibCTD.t as t,
    count(*) as n,
    avg(lat) as lat,
    avg(lon) as lon,
    temp,
    SP
    FROM rhibCTD
    LEFT JOIN rhibNAV
    ON rhibCTD.ship=rhibNAV.ship
    AND rhibCTD.t>=(rhibNAV.t - INTERVAL '10 seconds')
    AND rhibCTD.t<=(rhibNAV.t + INTERVAL '10 seconds')
    WHERE rhibCTD.ship=%s
        AND rhibCTD.t>(%s - INTERVAL '20 seconds')
        AND lat IS NOT NULL
        AND lon IS NOT NULL
    GROUP BY rhibCTD.ship,rhibCTD.t
    ON CONFLICT (ship,t) DO UPDATE SET
        n=EXCLUDED.n,
        lat=EXCLUDED.lat,
        lon=EXCLUDED.lon
    ;
"""
    cur.execute(sql, (ship, tLast))

    sql = """
INSERT INTO rhibTimesCTD
        SELECT ship,max(t) as t FROM rhibTodoCTD
        WHERE ship=%s
        GROUP BY ship
        ON CONFLICT (ship) DO UPDATE SET t=EXCLUDED.t
        ;
"""
    cur.execute(sql, (ship,))

def mkNetCDF(fn:str) -> None:
    if not os.path.isdir(os.path.basename(fn)):
        os.makedirs(os.path.basename(fn), mode=0o766, exists_ok=True)

    variables = dict(
            box=("t", np.empty(0, dtype=np.uint8)),
            n=("t", np.empty(0, dtype=np.uint16)),
            lat=("t", np.empty(0, dtype=np.double)),
            lon=("t", np.empty(0, dtype=np.double)),
            temp=("t", np.empty(0, dtype=np.single)),
            SP=("t", np.empty(0, dtype=np.single)),
            )

    ds = xr.Dataset(data_vars=variables,
        coords=dict(
            t=np.empty(0, dtype=np.double),
            ))
    ds.t.attrs["units"] = "seconds since 1970-01-01 00:00:00"
    ds.to_netcdf(fn, unlimited_dims="t")

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--db", type=str, default="sunrise", help="Database to work with")
parser.add_argument("--ship", type=str, required=True, help="Which RHIB to process")
parser.add_argument("--nc", type=str, required=True, help="Output netcdf filename")
args = parser.parse_args()

columns = (
        "ship",
        "t",
        "n",
        "lat",
        "lon",
        "u",
        "v",
        "w",
        )

if not os.path.isfile(args.nc):
    mkNetCDF(args.nc)

with psycopg2.connect(f"dbname={args.db}") as db:
    cur = db.cursor()
    cur.execute("BEGIN;")
    try:
        mkTimeTable(cur)
        mkCTDTable(cur)
        cur.execute("SELECT t FROM rhibTimesCTD WHERE ship=%s;", (args.ship,))
        row = cur.fetchone()
        tLast = row[0] if row else datetime.datetime(1970,1,1,0,0,0,tzinfo=datetime.timezone.utc)
        joinTables(cur, args.ship, tLast)
        cur.execute("COMMIT;")
    except:
        cur.execute("ROLLBACK;")
        logging.exception("Error building joined CTD information")

    # Output joined table
    sql = "SELECT box,t,n,lat,lon,temp,SP FROM rhibTodoCTD"
    sql+= " WHERE ship=%s AND qNetCDF=false"
    sql+= " ORDER BY t"
    sql+= ";"
    cur.execute(sql, (args.ship,))

    with netCDF4.Dataset(args.nc, mode="a") as nc:
        a = nc.variables
        tMax = None
        for row in cur:
            (box,t,m,lat,lon,temp,SP) = row
            tMax = t
            n = a["t"].size
            a["t"][n] = t.timestamp()
            a["box"][n] = box
            a["n"][n] = m
            a["lat"][n] = lat
            a["lon"][n] = lon
            a["temp"][n] = temp
            a["SP"][n] = SP

        sql = "UPDATE rhibTodoCTD SET qNetCDF=true"
        sql+= " WHERE ship=%s"
        sql+= " AND t<=%s"
        sql+= " AND qNetCDF=false"
        sql+= ";"
        cur.execute("BEGIN;")
        cur.execute(sql, (args.ship, tMax))
        cur.execute("COMMIT;")
