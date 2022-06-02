#! /usr/bin/env python3
#
# Read AIS NEMA sentences as a UDP datagram or a serial line
# then decode the message, and store the data several different ways
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from TPWUtils import Thread
import pyais
import sqlite3
import psycopg
import time
import socket
import pty
import logging
import queue
import serial
import select
import os
import sys

class Faux(Thread.Thread):
    def __init__(self, name:str, args:ArgumentParser) -> None:
        Thread.Thread.__init__(self, name, args)
        self.sentences = []

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="Faux options")
        grp.add_argument("--fauxTime", type=float, default=1, help="Time between AIS prints")
        grp.add_argument("--fauxDB", type=str, default="sample.raw.db",
                help="Faux SQLite3 database")

    def pop(self) -> str:
        if not self.sentences:
            with sqlite3.connect(self.args.fauxDB) as db:
                cur = db.cursor()
                cur.execute("SELECT msg FROM raw ORDER BY t;") # Order for multipart messages
                for row in cur: self.sentences.append(row[0])
        return self.sentences.pop()

class FauxUDP(Faux):
    def __init__(self, args:ArgumentParser) -> None:
        Faux.__init__(self, "FauxUDP", args)
        args.udp = args.fauxUDP

    def runIt(self) -> None: # Called on thread start
        port = self.args.udp
        dt = self.args.fauxTime

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tgt = ("127.0.0.1", self.args.udp)

        logging.info("Starting tgt=%s dt=%s", tgt, dt)

        while True:
            time.sleep(dt)
            msg = self.pop()
            logging.info("Sending %s", msg)
            sock.sendto(msg, tgt)

class FauxSerial(Faux):
    def __init__(self, args:ArgumentParser) -> None:
        Faux.__init__(self, "FauxSerial", args)
        (self.__master, slave) = pty.openpty() # Create a pseudoTTY device pair
        args.serial = os.ttyname(slave)
        logging.info("Serial device name %s", args.serial)


    def runIt(self) -> None: # Called on thread start
        master = self.__master
        dt = self.args.fauxTime
        logging.info("Starting dt=%s", dt)
        while True:
            time.sleep(dt)
            msg = self.pop()
            logging.info("Sending %s", msg)
            os.write(master, msg)

class Reader(Thread.Thread):
    def __init__(self, name:str, args:ArgumentParser) -> None:
        Thread.Thread.__init__(self, name, args)
        self.queues = []

    def addQueue(self, q:queue.Queue) -> None:
        self.queues.append(q)

    def put(self, t:float, ipAddr:str, ipPort:int, msg:bytes) -> None:
        payload = (t, ipAddr, ipPort, msg)
        logging.info("Put %s %s %s %s", t, ipAddr, ipPort, msg)
        for q in self.queues: q.put(payload)

class ReadUDP(Reader):
    def __init__(self, args:ArgumentParser) -> None:
        Reader.__init__(self, "ReadUDP", args)

    def runIt(self) -> None: # Called on thread start
        port = self.args.udp
        sz = 20 * 85 # A huge upper limit for NEMA sentences
        logging.info("Starting port=%s size=%s", port, sz)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("", port))
            while True: # Read datagrams
                (data, senderAddr) = sock.recvfrom(sz)
                t = time.time()
                (ipAddr, ipPort) = senderAddr
                self.put(t, ipAddr, ipPort, data)

class ReadSerial(Reader):
    __Bytesizes = {
            5: serial.FIVEBITS,
            6: serial.SIXBITS,
            7: serial.SEVENBITS,
            8: serial.EIGHTBITS,
            }
    __Parity = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD,
            "Mark": serial.PARITY_MARK,
            "Spacer": serial.PARITY_SPACE,
            }
    __Stopbits = {
            1:   serial.STOPBITS_ONE,
            1.5: serial.STOPBITS_ONE_POINT_FIVE,
            2:   serial.STOPBITS_TWO,
            }

    def __init__(self, args:ArgumentParser) -> None:
        Reader.__init__(self, "ReadSerial", args)

    @classmethod
    def addArgs(cls,parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="Input serial related options")
        grp.add_argument("--serialBaudrate", type=int, default=115200, help="Serial port baudrate")
        grp.add_argument("--serialBytesize", type=int, default=8,
                choices=sorted(cls.__Bytesizes), help="Serial port byte size")
        grp.add_argument("--serialParity", type=str, default="None",
                choices=sorted(cls.__Parity), help="Serial port pairty")
        grp.add_argument("--serialStopbits", type=float, default=1,
                choices=sorted(cls.__Stopbits), help="Serial port number of stop bits")

    def runIt(self) -> None: # Called on thread start
        args = self.args
        device = args.serial
        logging.info("Starting %s", device)
        with serial.Serial(
                port=device,
                timeout=0, # Non-blocking, I'll use select to avoid buffering issues
                baudrate=args.serialBaudrate,
                bytesize=self.__Bytesizes[args.serialBytesize],
                parity=self.__Parity[args.serialParity],
                stopbits=self.__Stopbits[args.serialStopbits],
                ) as s:
            logging.info("s %s", s)
            while s.is_open:
                (rlist, wlist, xlist) = select.select([s], [], [])
                t = time.time()
                try:
                    data = s.read(65536) # Read a sentence
                    self.put(time.time(), None, None, data)
                except Exception as e:
                    logging.exception("While reading serial device")
        raise Exception(f"EOF while reading from {device}")

class RawWriter(Thread.Thread):
    def __init__(self, name:str, args:ArgumentParser, rdr) -> None:
        Thread.Thread.__init__(self, name, args)
        self.queue = queue.Queue()
        rdr.addQueue(self.queue)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="RawWrt related options")
        grp.add_argument("--rawTable", type=str, default="raw", help="Raw table name")

    def createTable(self, cursor) -> None:
        tbl = self.args.rawTable
        sql = f"CREATE TABLE IF NOT EXISTS {tbl} (\n"
        sql+= "  t DOUBLE PRECISION, -- UTC seconds\n"
        sql+= "  ipAddr TEXT,\n"
        sql+= "  port INTEGER,\n"
        sql+= "  msg TEXT, -- NEMA sentence\n"
        sql+= "  PRIMARY KEY(t, msg)\n"
        sql+= f"); -- {tbl}"
        logging.debug("Creating table:\n%s", sql)
        cursor.execute(sql)

    def dbWrite(self, cursor, payload:tuple) -> None:
        tbl = self.args.rawTable
        sql = f"INSERT OR IGNORE INTO {tbl} VALUES(?,?,?,?);"
        logging.info("%s", payload)
        cursor.execute(sql, payload)

class Raw2SQLite(RawWriter):
    def __init__(self, args:ArgumentParser, rdr) -> None:
        RawWriter.__init__(self, "R2SQLite", args, rdr)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="Raw2SQLite related options")
        grp.add_argument("--rawSQLite3", type=str, help="SQLite3 database filename")

    def runIt(self) -> None: # Called on thread start
        q = self.queue
        logging.info("Starting")
        qCreateTable = True
        while True:
            payload = q.get()
            q.task_done()
            with sqlite3.connect(args.rawSQLite3) as db:
                cursor = db.cursor()
                cursor.execute("BEGIN;")
                if qCreateTable: 
                    self.createTable(cursor)
                    qCreateTable = False
                self.dbWrite(cursor, payload)
                cursor.execute("COMMIT;")

class Raw2PostgreSQL(RawWriter):
    def __init__(self, args:ArgumentParser, rdr) -> None:
        RawWriter.__init__(self, "R2PSQL", args, rdr)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="Raw2PostgreSQL related options")
        grp.add_argument("--rawPostgreSQL", type=str, help="PostgreSQL database")

    def runIt(self) -> None: # Called on thread start
        q = self.queue
        logging.info("Starting")
        qCreateTable = True
        with psycopg.connect("dbname=" + args.rawPostgreSQL) as db:
            while True:
                payload = q.get()
                q.task_done()
                with sqlite3.connect(args.rawPostgreSQL) as db:
                    cursor = db.cursor()
                    cursor.execute("BEGIN;")
                    if qCreateTable: 
                        self.createTable(cursor)
                        qCreateTable = False
                    self.dbWrite(cursor, payload)
                    cursor.execute("COMMIT;")

parser = ArgumentParser()
Logger.addArgs(parser)
Faux.addArgs(parser)
ReadSerial.addArgs(parser)
RawWriter.addArgs(parser)
Raw2SQLite.addArgs(parser)
grp = parser.add_mutually_exclusive_group(required=True)
grp.add_argument("--udp", type=int, help="UDP port to listen to for datagrams")
grp.add_argument("--serial", type=str, help="Serial port to listen to")
grp.add_argument("--fauxUDP", type=int, help="Send faux UDP datagrams to myself")
grp.add_argument("--fauxSerial", action="store_true",
    help="Send faux NEMA sentences to myself via a serial connection")
args = parser.parse_args()

Logger.mkLogger(args)

thrds = []
if args.fauxUDP:
    thrds.append(FauxUDP(args))
elif args.fauxSerial:
    thrds.append(FauxSerial(args))
logging.info("args %s", args)

if args.udp:
    rdr = ReadUDP(args)
    thrds.append(rdr)
elif args.serial:
    rdr = ReadSerial(args)
    thrds.append(rdr)

if args.rawSQLite3:
    thrds.append(Raw2SQLite(args, rdr))

for thrd in thrds: thrd.start() # Start all the threads

Thread.Thread.waitForException()
