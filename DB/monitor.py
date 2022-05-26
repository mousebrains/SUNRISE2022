#! /usr/bin/env python3
#
# Monitor when a file is updated using inotify
# then read in the updates and pour the results into a database
# and into a NetCDF file
#
# May-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from TPWUtils.INotify import INotify
from TPWUtils.Thread import Thread
import pyinotify
import queue
import re
import time
import psycopg
import logging

class Reader(Thread):
    def __init__(self, args:ArgumentParser, q:queue.Queue) -> None:
        Thread.__init__(self, "Reader", args)
        self.__queue = q

    def runIt(self) -> None:
        q = self.__queue
        dbName = f"dbname={self.args.db}"
        logging.info("Starting %s", dbName)
        while True:
            fn = q.get()
            q.task_done()
            logging.info("fn %s", fn)
            with psycopg.connect(dbName) as db:
                pass

class Responder(Thread):
    def __init__(self, args:ArgumentParser, qIn:queue.Queue) -> None:
        Thread.__init__(self, "Responder", args)
        self.__regexp = args.pattern
        self.__qIn = qIn
        self.queue = queue.Queue()

    def runIt(self) -> None:
        dt = self.args.dt
        qIn = self.__qIn
        qOut = self.queue
        pattern = re.compile(self.__regexp)
        logging.info("Starting %s", pattern)
        seen = {}
        tNext = None
        while True:
            try:
                (t0, fn) = qIn.get(
                        timeout=None if tNext is None else max(0.1, tNext - time.time())
                        )
                qIn.task_done()
                logging.info("%s %s", t0, fn)
                if fn in seen: continue # Alread waiting to do something with this file
                matches = pattern.fullmatch(fn)
                logging.info("Matches %s", matches)
                if not matches: continue # Not an interesting file
                logging.info("Matched %s", matches[1])
                seen[fn] = time.time() + dt
                tNext = seen[fn] if tNext is None else tNext
            except queue.Empty:
                logging.info("Empty %s", seen)
                toRead = set()
                now = time.time()
                for fn in seen:
                    if seen[fn] <= now:
                        toRead.add(fn)
                        qOut.put(fn)
                logging.info("toRead %s", toRead)
                for key in toRead: del seen[key]
                tNext = None
                for key in seen:
                    tNext = min(tNext, seen[key]) if tNext else seen[key]




parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--directory", type=str, required=True, help="Name of directory to monitor")
parser.add_argument("--pattern", type=str, default=r".*/met.(\w+).csv$",
        help="Regular expression of MET data to match on")
parser.add_argument("--netcdf", type=str, default="~/Processed",
        help="Where to save NetCDF files to")
parser.add_argument("--db", type=str, default="sunrise", help="Database to use")
parser.add_argument("--table", type=str, default="MET", help="PostgreSQL database table name")
parser.add_argument("--dt", type=float, default=10,
        help="Seconds to sleep after a file has been updated")
args = parser.parse_args()

Logger.mkLogger(args)

logging.info("Args %s", args)

try:
    i = INotify(args, flags=pyinotify.IN_CLOSE_WRITE|pyinotify.IN_MOVED_TO)
    responder = Responder(args, i.queue)
    reader = Reader(args, responder.queue)
    i.start()
    responder.start()
    reader.start()

    i.addTree(args.directory)

    Thread.waitForException()
except:
    logging.exception("Unexpected exception")
