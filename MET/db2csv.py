#! /usr/bin/env python3
#
# Output fresh database records to a CSV file
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from Config import Config
import psycopg2
import logging
import os.path
import sys

parser = ArgumentParser()
Logger.addArgs(parser)
Config.addArgs(parser)
parser.add_argument("--db", type=str, default="sunrise", help="Input database")
parser.add_argument("--table", type=str, default="met", help="Table to fetch data from")
parser.add_argument("--csv", type=str, required=True, help="Output CSV filename")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

config = Config(args)

if not config.csv:
    logging.info("No CSV information in %s for %s", args.yaml, args.key)
    sys.exit(0)

if "columns" not in config.csv:
    logging.info("CSV information is missing columns in %s for %s", args.yaml, args.key)
    sys.exit(1)

cols = config.csv["columns"]
tindex = cols.index("t")

dt = None if "decimate" not in config.csv else config.csv["decimate"]

if not os.path.isfile(args.csv):
    with open(args.csv, "w") as fp:
        fp.write(",".join(cols) + "\n");

sql = "WITH updated AS ("
sql+= f"UPDATE {args.table} SET qCSV=true"
sql+= f" WHERE ship='{config.ship}' AND qCSV=false"
if dt:
    sql+= f" AND (EXTRACT(EPOCH FROM t) % {dt})=0"
sql+= " RETURNING "
sql+= ",".join(cols)
sql+= ") SELECT * FROM updated ORDER BY t ASC LIMIT 10;"

print(sql)
with psycopg2.connect(f"dbname={args.db}") as db:
    cur = db.cursor()
    cur.execute("BEGIN;")
    try:
        cur.execute(sql)
        with open(args.csv, "a") as fp:
            cnt = 0
            times = []
            for row in cur:
                cnt += 1
                fields = []
                times.append(row[tindex])
                for i in range(len(row)):
                    if i == tindex:
                        fields.append(str(row[i].timestamp()))
                    else:
                        fields.append(str(row[i]))
                fp.write(",".join(fields) + "\n")
            logging.info("Wrote %s records to %s", cnt, args.csv)
        cur.execute("COMMIT;")
    except:
        cur.execute("ROLLBACK;")
        logging.error("Error executing %s", sql)
        sys.exit(1)
