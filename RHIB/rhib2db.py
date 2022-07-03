#! /usr/bin/env python3
#
# Parse RHIB files
#
# July-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from TPWUtils.Thread import Thread
from TPWUtils.INotify import INotify
from Monitor import MonitorINotify, MonitorPolling
import pyinotify
import logging
import re
import datetime
import numpy as np
import psycopg2
import os
import queue
import sys

class RHIB(Thread):
    def __init__(self, args:ArgumentParser) -> None:
        Thread.__init__(self, "RHIB", args)
        self.queue = queue.Queue()

    def runIt(self) -> None: # Called on thread start
        args = self.args
        q = self.queue
        logging.info("Starting")
        rhib = RHIB_Parser()
        dbname = f"dbname={args.db}"
        with psycopg2.connect(dbname) as db:
            cur = db.cursor()
            rhib.cursor(cur)
            cur.execute("BEGIN;")
            try:
                rhib.mkTables() # Make the tables
                cur.execute("COMMIT;")
            except Exception as e:
                cur.execute("ROLLBACK;")
                logging.exception("Error creating tables")
                raise e

        while True:
            fn = q.get()
            q.task_done()
            if not rhib.ship(fn): continue
            with psycopg2.connect(dbname) as db:
                cur = db.cursor()
                rhib.cursor(cur)
                try:
                    cur.execute("BEGIN;")
                    rhib.parseFile(fn)
                    cur.execute("COMMIT;")
                except:
                    cur.execute("ROLLBACK;")
                    logging.exception("Error processing %s", fn)

class RHIB_Parser:
    def __init__(self) -> None:
        self.__cursor = None
        self.__box = None
        self.__ship = None

        prefix = b"^\d{2}-\w+-\d{4} \d{2}:\d{2}:\d{2} UBOX(\d{2}) -- (\w+) -- "
        prefix+= b"(\d{4})/(\d{2})/(\d{2}) (\d{2}):(\d{2}):(\d{2}) UTC -- (.+)"
        self.__prefix = re.compile(prefix)

        navinfo = b"LAT ([+-]?\d+[.]\d+)"
        navinfo+= b" LON ([+-]?\d+[.]\d+)"
        navinfo+= b" HD"
        self.__navregex = re.compile(navinfo)

        keelctd = b"KDATE (\d{4})-(\d{2})-(\d{2})"
        keelctd+= b" KTIME (\d{2}):(\d{2}):(\d{2})[.](\d{3})"
        keelctd+= b" Temp\s+([+-]?\d+[.]\d*)"
        keelctd+= b" Sal\s+([+-]?\d+[.]\d*)"
        self.__keelctdregex = re.compile(keelctd)

        adcp = b"ADATE (\d{4})(\d{2})(\d{2})"
        adcp+= b" ATIME (\d{2})(\d{2})(\d{2})"
        adcp+= b" u ([+-]?\d+[.]\d+(?:,[+-]?\d+[.]\d+)*)"
        adcp+= b" v ([+-]?\d+[.]\d+(?:,[+-]?\d+[.]\d+)*)"
        adcp+= b" w ([+-]?\d+[.]\d+(?:,[+-]?\d+[.]\d+)*)"
        self.__adcpregex = re.compile(adcp)

        self.__shipregex = re.compile(r"_UBOX(\d+)_([a-zA-Z0-9]+)_\d+")

        self.__parsers = {
                "navinfo": self.__navinfo,
                "keelctd": self.__keelctd,
                "adcp": self.__adcp,
                "winchstatus": None,
                "pdbinfo": None,
                "param": None,
                "wpcount": None,
                "curwp": None,
                "waypt": None,
                }

    def cursor(self, cur) -> None:
        self.__cursor = cur

    def ship(self, fn:str) -> bool:
        matches = self.__shipregex.search(fn)
        if not matches:
            logging.error("Unrecognized filename structure, %s", fn)
            return False
        self.__box = matches[1]
        self.__ship = matches[2]
        return True

    def mkTables(self) -> None:
        self.__mkPositionTable()
        self.__mkNavigationTable()
        self.__mkCTDTable()
        self.__mkADCPTable()

    def __mkPositionTable(self) -> None:
        sql = "CREATE TABLE IF NOT EXISTS rhibPos (\n"
        sql+= "  filename TEXT PRIMARY KEY NOT NULL,\n"
        sql+= "  position INTEGER NOT NULL\n"
        sql+= ");"
        self.__cursor.execute(sql)

    def __mkNavigationTable(self) -> None:
        sql = "CREATE TABLE IF NOT EXISTS rhibNav (\n"
        sql+= "  ship TEXT NOT NULL,\n"
        sql+= "  box INTEGER NOT NULL,\n"
        sql+= "  t TIMESTAMP WITH TIME ZONE NOT NULL,\n"
        sql+= "  lat REAL NOT NULL,\n"
        sql+= "  lon REAL NOT NULL,\n"
        sql+= "  PRIMARY KEY(ship, t)\n"
        sql+= ");"
        self.__cursor.execute(sql)

    def __mkCTDTable(self) -> None:
        sql = "CREATE TABLE IF NOT EXISTS rhibCTD (\n"
        sql+= "  ship TEXT NOT NULL,\n"
        sql+= "  box INTEGER NOT NULL,\n"
        sql+= "  t TIMESTAMP WITH TIME ZONE NOT NULL,\n"
        sql+= "  temp REAL NOT NULL,\n"
        sql+= "  SP REAL NOT NULL,\n"
        sql+= "  PRIMARY KEY(ship, t)\n"
        sql+= ");"
        self.__cursor.execute(sql)

    def __mkADCPTable(self) -> None:
        sql = "CREATE TABLE IF NOT EXISTS rhibADCP (\n"
        sql+= "  ship TEXT NOT NULL,\n"
        sql+= "  box INTEGER NOT NULL,\n"
        sql+= "  t TIMESTAMP WITH TIME ZONE NOT NULL,\n"
        sql+= "  u REAL[] NOT NULL,\n"
        sql+= "  v REAL[] NOT NULL,\n"
        sql+= "  w REAL[] NOT NULL,\n"
        sql+= "  PRIMARY KEY(ship, t)\n"
        sql+= ");"
        self.__cursor.execute(sql)

    def __navinfo(self, box:int, t:datetime.datetime, tail:bytes, line:bytes) -> int:
        info = self.__navregex.match(tail)
        if not info:
            # logging.info("NAVINFO failure %s", bytes(line))
            return 0
        lat = float(info[1])
        lon = float(info[2])
        sql = "INSERT INTO rhibNAV VALUES(%s,%s,%s,%s,%s)"
        sql+= " ON CONFLICT DO NOTHING"
        sql+= ";"
        self.__cursor.execute(sql, (self.__ship, box, t, lat, lon));
        return 1

    def __keelctd(self, box:int, t:datetime.datetime, tail:bytes, line:bytes) -> int:
        info = self.__keelctdregex.match(tail)
        if not info:
            # logging.info("KEELCTD failure %s", bytes(line))
            return 0
        t = datetime.datetime(
                int(info[1]), int(info[2]), int(info[3]),
                int(info[4]), int(info[5]), int(info[6]),
                int(info[7]) * 1000,
                tzinfo=datetime.timezone.utc)
        temp = float(info[8])
        SP = float(info[9])
        sql = "INSERT INTO rhibCTD VALUES(%s,%s,%s,%s,%s)"
        sql+= " ON CONFLICT DO NOTHING"
        sql+= ";"
        self.__cursor.execute(sql, (self.__ship, box, t, temp, SP));
        return 1

    def __adcp(self, box:int, t:datetime.datetime, tail:bytes, line:bytes) -> int:
        info = self.__adcpregex.match(tail)
        if not info:
            # logging.info("ADCP failure %s", bytes(line))
            return 0
        t = datetime.datetime(
                int(info[1]), int(info[2]), int(info[3]),
                int(info[4]), int(info[5]), int(info[6]),
                tzinfo=datetime.timezone.utc)
        u = np.array(str(info[7], "UTF-8").split(",")).astype(float)
        v = np.array(str(info[8], "UTF-8").split(",")).astype(float)
        w = np.array(str(info[9], "UTF-8").split(",")).astype(float)
        if u.size != v.size or u.size != w.size:
            return 0
        sql = "INSERT INTO rhibADCP VALUES(%s,%s,%s,%s,%s,%s)"
        sql+= " ON CONFLICT DO NOTHING"
        sql+= ";"
        self.__cursor.execute(sql, (self.__ship, box, t, u.tolist(), v.tolist(), w.tolist()));
        return 1

    def __parseLines(self, buffer:bytearray) -> bytearray:
        parsers = self.__parsers
        cur = self.__cursor
        offset = 0
        cnt = 0
        while True:
            index = buffer.find(b"\n", offset)
            if index < 0: break
            line = buffer[offset:index]
            offset = index + 1
            prefix = self.__prefix.match(line)
            if not prefix:
                logging.debug("Unrecognized line %s", bytes(line))
                continue
            box = int(prefix[1])
            ident = str(prefix[2], "UTF-8")
            t = datetime.datetime(
                    int(prefix[3]), int(prefix[4]), int(prefix[5]),
                    int(prefix[6]), int(prefix[7]), int(prefix[8]),
                    tzinfo=datetime.timezone.utc)
            tail = prefix[9]
            if ident in parsers:
                if parsers[ident]:
                    cnt += parsers[ident](box, t, tail, line)
            else:
                logging.debug("Unrecognized id %s line %s", ident, bytes(line))

        return (buffer[offset:], cnt)

    def parseFile(self, fn:str) -> int:
        fn = os.path.abspath(os.path.expanduser(fn))
        cur = self.__cursor
        cur.execute("SELECT position FROM rhibPos WHERE filename=%s;", (fn,))
        row = cur.fetchone()
        spos = row[0] if row else 0
        fsize = os.path.getsize(fn)
        if spos == fsize:
            logging.info("Skipping %s, fully processed", fn)
            return
        
        if spos > fsize: # File was truncated, so reprocess
            logging.info("Truncated %s", fn)
            spos = 0

        with open(fn, "rb") as fp:
            cnt = 0
            if spos and spos > 0: fp.seek(spos - 1)
            buffer = bytearray()
            while True:
                content = fp.read(1024*1024) # Read in a chunk of the file
                if not content: break # EOF
                buffer += content
                (buffer, n) = self.__parseLines(buffer)
                cnt += n
            sql = "INSERT INTO rhibPos VALUES(%s,%s)"
            sql+= " ON CONFLICT (filename) DO UPDATE SET position=EXCLUDED.position;"
            cur.execute(sql, (fn, fp.tell() - len(buffer)))
            logging.info("Inserted %s records from %s", cnt, fn)

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--directory", type=str, required=True, help="Name of directory to monitor")
parser.add_argument("--dt", type=float, default=120, help="Seconds to wait after update")
parser.add_argument("--pattern", type=str, default=r"RHIB_status_GS3_UBOX\d+_\w+_\d+_\d+.txt",
        help="Filename pattern to match")
grp = parser.add_mutually_exclusive_group(required=True)
grp.add_argument("--inotify", action="store_true",
        help="Use INotify to monitor changes in a directory")
grp.add_argument("--polling", action="store_true",
        help="Poll for changes in a directory's contents")

parser.add_argument("--db", type=str, default="sunrise", help="Database name to connect to")
args = parser.parse_args()

Logger.mkLogger(args)

logging.info("Args %s", args)

try:
    rhib = RHIB(args)
    rhib.start()

    if args.inotify: # Use inotify
        i = INotify(args,
                flags=pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO | pyinotify.IN_MODIFY)
        monitor = MonitorINotify(args, i.queue)
        i.start()
        i.addTree(args.directory)
    else: # Use polling
        monitor = MonitorPolling(args, args.directory)

    monitor.addQueue(rhib.queue)
    monitor.start()

    # Send all the matching files to rhib from an initial scandir
    for item in os.scandir(args.directory):
        if item.is_dir(): continue # Skip directories
        fn = item.name
        if not monitor.pattern.match(fn): continue # Not a match
        rhib.queue.put(item.path)

    Thread.waitForException()
except:
    logging.exception("Unexpected exception")
