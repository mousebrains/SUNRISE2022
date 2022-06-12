#! /usr/bin/env python3
#
# Spit out records from the Pelican data from 2021's SUNRISE cruise
# adjusting the time
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
import logging
import bz2
import os.path
import time
import sys

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--dt", type=float, default=1, help="Seconds betweeen output lines")
parser.add_argument("--sample", type=str, default="sample.csv.bz2",
        help="Compressed input sample data filename")
parser.add_argument("--output", type=str, required=True, help="Output filename")
parser.add_argument("--delimiter", type=str, default=",", help="Sample file delimiter")
parser.add_argument("--date", type=str, default="Date", help="Date column name")
parser.add_argument("--time", type=str, default="Time", help="Time column name")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

dateCol = None
timeCol = None
delim = bytes(args.delimiter, "utf-8")
dateName = bytes(args.date, "utf-8")
timeName = bytes(args.time, "utf-8")
dt = args.dt

logging.info("Starting sample %s output %s delim %s date %s time %s dt %s",
        args.sample, args.output, delim, dateName, timeName, dt)

now = time.time()

while True:
    logging.info("Starting to read sample %s", args.sample)
    with bz2.open(args.sample, mode="rb") as fp:
        hdr = fp.readline()
        if not hdr:
            logging.error("EOF in %s while reading header line", args.sample)
            sys.exit(1)
        if dateCol is None:
            fields = hdr.split(delim)
            for i in range(len(fields)):
                if fields[i] == dateName:
                    dateCol = i
                elif fields[i] == timeName:
                    timeCol = i
            if dateCol is None:
                logging.error("Date column, %s, not found in %s", args.date, args.sample)
                sys.exit(1)
            if timeCol is None:
                logging.error("Time column, %s, not found in %s", args.time, args.sample)
                sys.exit(1)

        minCol = max(dateCol, timeCol) + 1

        if not os.path.isfile(args.output):
            with open(args.output, "wb") as ofp: ofp.write(hdr)

        with open(args.output, "ab") as ofp: # Now loop over lines
            for line in fp.readlines():
                fields = line.split(delim)
                if len(fields) < minCol:
                    logging.warning("Skipping %s", line)
                    continue
                tm = time.gmtime(now)
                fields[dateCol] = bytes(time.strftime("%m/%d/%Y", tm), "utf-8")
                fields[timeCol] = bytes(time.strftime("%H:%M:%S", tm), "utf-8")
                ofp.write(delim.join(fields))
                ofp.flush()
                now += dt
                dtWait = max(0.01, now - time.time())
                time.sleep(dtWait)
