#! /usr/bin/env python3
#
# Monitor a directory for a changing MET CSV file
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils.Thread import Thread
from Monitor import Monitor
from Config import Config
from FilePosition import FilePosition
import os.path
import logging
import psycopg2
import queue

class DB(Thread):
    def __init__(self, args:ArgumentParser, monitor:Monitor, config:Config) -> None:
        Thread.__init__(self, "DB", args)
        self.__queue = queue.Queue()
        self.__config = config
        if monitor is not None:
            monitor.addQueue(self.__queue) # Receive file update notifications
        self.__filepos = FilePosition() # database cached filepositions

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--db", type=str, default="sunrise", help="PostgreSQL database name")
        parser.add_argument("--backup", type=int, default=1, help="Bytes to reread")

    def put(self, fn:str) -> None: # For debugging with out a monitor
        self.__queue.put(fn)

    def __mkTable(self, dbname:str) -> None:
        with psycopg2.connect(dbname) as db:
            cur = db.cursor()
            cur.execute("BEGIN;")
            self.__filepos.mkTable(cur) # Create the filePosition table
            self.__config.mkTable(cur) # Create met table
            cur.execute("COMMIT;")

    def __populateHeaders(self, fn:str) -> tuple[list[str], int]:
        fields = []
        with open(fn, "rb") as fp: # Read in the first line
            for cnt in range(self.__config.headerSkipBefore + 1): # Pre + hdr
                line = fp.readline()
            for fld in self.__config.delimiter.split(str(line.strip(), "UTF-8")):
                fields.append(fld.strip())
            for cnt in range(self.__config.headerSkipAfter): # post
                line = fp.readline()
            pos = fp.tell()

        return (fields, pos)

    def __procLines(self, fn:str, fp, header:list[str], cur) -> int:
        nHeaders = len(header)
        spos = fp.tell() # Starting position
        buffer = ""
        cur.execute("BEGIN;")
        while True:
            content = fp.read(1024*1024) # Read a chunk of data
            if not content: break # EOF
            buffer += content
            lines = buffer.split("\n")
            if not lines: break # No new lines found
            if len(lines[-1]): # last line is not empty, so drop it
                line = lines.pop()
                buffer = buffer[-len(line):] # drop everything except the last line
            else: # last line is empty
                buffer = "" # Full lines found
            for line in lines: # Walk through the lines and insert them
                fields = self.__config.delimiter.split(line)
                if len(fields) != nHeaders:
                    logging.info("Bad line, %s", line)
                    continue
                self.__config.insertRow(cur, fields)
        epos =  fp.tell() - len(buffer)
        if spos == epos: # Nothing happened
            cur.execute("ROLLBACK;")
        else:
            if self.__filepos.set(fn, epos, cur):
                cur.execute("COMMIT;")
            else:
                cur.execute("ROLLBACK;")
        return epos

    def runIt(self) -> None: # Called on thread start
        args = self.args
        q = self.__queue
        dbname = f"dbname={args.db}"
        backup = args.backup
        logging.info("Starting %s backup %s", dbname, backup)
        self.__mkTable(dbname)
        header = {} # Column headers for each file
        position = {} # File position of the last read
        posHeader = {} # First data position
        while True:
            fn = q.get()
            q.task_done()
            with psycopg2.connect(dbname) as db:
                cur = db.cursor()
                posDB = self.__filepos.get(fn, cur)
                if posDB and (posDB == os.path.getsize(fn)): 
                    logging.info("Already fully processed %s", fn)
                    continue # Nothing new get get
                if fn not in header:
                    (header[fn], posHeader[fn]) = self.__populateHeaders(fn)
                    logging.info("fn %s header %s", fn, header[fn])
                    position[fn] = posHeader[fn] if posDB is None else posDB
                    self.__config.mapColumns(header[fn])
                with open(fn, "r") as fp:
                    fp.seek(max(posHeader[fn] - 1, position[fn] - backup))
                    while True: # Skip forward to the EOF or new line
                        c = fp.read(1)
                        if not c or (c == "\n"): break # EOF or new line
                    position[fn] = self.__procLines(fn, fp, header[fn], cur)

if __name__ == "__main__":
    from TPWUtils import Logger

    parser = ArgumentParser()
    Logger.addArgs(parser)
    Config.addArgs(parser)
    DB.addArgs(parser)
    parser.add_argument("fn", type=str, nargs="+",
            help="Name of file(s) to insert into database")
    args = parser.parse_args()

    Logger.mkLogger(args)
    logging.info("Args %s", args)

    try:
        config = Config(args)
        db = DB(args, None, config)
        db.start()
        for fn in args.fn: db.put(fn)
        logging.warning("You'll have to control-C to stop the program from waiting forever!")
        Thread.waitForException()
    except:
        logging.exception("Unexpected exception")
