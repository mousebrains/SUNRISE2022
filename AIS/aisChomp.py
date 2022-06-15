#! /usr/bin/env python3
#
# Read AIS NEMA sentences as a UDP datagram or a serial line
# then decode the message, and store the data several different ways
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from TPWUtils import Thread
import ais # This is part of python3-ais package in Ubuntu
import re
import sqlite3
import psycopg2
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
            buffer = bytearray()
            while s.is_open:
                (rlist, wlist, xlist) = select.select([s], [], [])
                t = time.time()
                try:
                    buffer += s.read(65536) # Read a data
                    t = time.time()
                    lines = buffer.split(b"\n")
                    for line in lines:
                        if line == b"": continue
                        if (len(line) > 1) and line[-1:] == b"\r":
                            self.put(t, None, None, line)
                    if len(lines):
                        if lines[-1] == b"" or lines[-1][-1] == "\r":
                            buffer = bytearray()
                        else:
                            buffer = buffer[-len(lines[-1]):]
                except Exception as e:
                    logging.exception("While reading serial device")
        raise Exception(f"EOF while reading from {device}")

class RawWriter(Thread.Thread):
    def __init__(self, name:str, args:ArgumentParser, rdr:Reader) -> None:
        Thread.Thread.__init__(self, name, args)
        self.queue = queue.Queue()
        rdr.addQueue(self.queue)
        self.sqlInsert = None
        self.sqlCreate = f"CREATE TABLE IF NOT EXISTS {args.rawTable} (\n"
        self.sqlCreate+= "  t DOUBLE PRECISION, -- UTC seconds\n"
        self.sqlCreate+= "  ipAddr TEXT,\n"
        self.sqlCreate+= "  port INTEGER,\n"
        self.sqlCreate+= "  msg TEXT, -- NEMA sentence\n"
        self.sqlCreate+= "  PRIMARY KEY(t, msg)\n"
        self.sqlCreate+= f"); -- {args.rawTable}"

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="RawWrt related options")
        grp.add_argument("--rawTable", type=str, default="raw", help="Raw table name")

    def createTable(self, cursor) -> None:
        logging.debug("Creating table:\n%s", self.sqlCreate)
        cursor.execute(self.sqlCreate)

    def dbWrite(self, cursor, payload:tuple) -> None:
        if not self.sqlInsert: return
        try:
            payload = (payload[0], payload[1], payload[2], str(payload[3], "UTF-8"))
            logging.info("%s", payload)
            cursor.execute(self.sqlInsert, payload)
        except:
            logger.exception("Error handling %s", payload)

class Raw2SQLite(RawWriter):
    def __init__(self, args:ArgumentParser, rdr:Reader) -> None:
        RawWriter.__init__(self, "R2SQLite", args, rdr)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--rawSQLite3", type=str, help="SQLite3 database filename")

    def runIt(self) -> None: # Called on thread start
        args = self.args
        tbl = self.args.rawTable
        self.sqlInsert = f"INSERT OR IGNORE INTO {tbl} VALUES(?,?,?,?);"
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
    def __init__(self, args:ArgumentParser, rdr:Reader) -> None:
        RawWriter.__init__(self, "R2PSQL", args, rdr)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--rawPostgreSQL", type=str, help="PostgreSQL database")

    def runIt(self) -> None: # Called on thread start
        args = self.args
        tbl = self.args.rawTable
        self.sqlInsert = f"INSERT INTO {tbl} VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
        q = self.queue
        logging.info("Starting")
        qCreateTable = True
        with psycopg2.connect("dbname=" + args.rawPostgreSQL) as db:
            while True:
                payload = q.get()
                q.task_done()
                cursor = db.cursor()
                cursor.execute("BEGIN;")
                if qCreateTable:
                    self.createTable(cursor)
                    qCreateTable = False
                self.dbWrite(cursor, payload)
                cursor.execute("COMMIT;")

class Raw2CSV(RawWriter):
    def __init__(self, args:ArgumentParser, rdr:Reader) -> None:
        RawWriter.__init__(self, "R2CSV", args, rdr)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--rawCSV", type=str, help="CSV filename for Raw output")

    def runIt(self) -> None: # Called on thread start
        fn = self.args.rawCSV
        q = self.queue
        logging.info("Starting %s", fn)
        if not os.path.isfile(fn):
            with open(fn, "w") as fp:
                fp.write("t,ipAddr,port,body\n")

        while True:
            payload = q.get()
            q.task_done()
            try:
                (t, ipAddr, port, body) = payload
                body = str(body, "UTF-8")
                with open(fn, "a") as fp:
                    fp.write(f"{t},{ipAddr},{port},'{body}'\n")
            except:
                logging.exception("Error writing to %s, %s, %s, %s, %s", fn, t, ipAddr, port, body)
                
class Decrypt(Thread.Thread):
    def __init__(self, args:ArgumentParser, rdr:Reader) -> None:
        Thread.Thread.__init__(self, "Decrypt", args)
        self.queueIn = queue.Queue()
        self.__queues = []
        rdr.addQueue(self.queueIn)

    def addQueue(self, q:queue.Queue) -> None:
        self.__queues.append(q)

    def __chkSum(self, body:bytes, chksum:bytes) -> bool:
        aSum = 0
        for c in body: aSum ^= c
        if aSum == int(str(chksum, "UTF-8"), 16): return True
        logging.warning("Checksum mismatch, %s chksum %s != %s", body, chksum, f"{aSum:02X}")
        return False

    def __decrypt(self, payload:bytes, fillbits:int, t:float) -> None:
        try:
            payload = str(payload, "UTF-8")
            info = ais.decode(payload, fillbits)
            info["t"] = t
            for q in self.__queues: q.put(info)
        except:
            logging.exception("Error decoding %s, %s", payload, fillbits)

    def runIt(self) -> None: # Called on thread start
        logging.info("Starting")
        qIn = self.queueIn
        qOut = self.__queues
        reNEMA = re.compile(b"^\s*!(AIVD[MO],\d+,\d+,\d?,\w?,.*,[0-5])[*]([0-9A-Za-z]{2})\s*$")
        reIgnore = re.compile(b"^\s*[$](PFEC|AI(ALR|ABK|TXT)),")
        reSentence = re.compile(b"^(AIVD[MO]),(\d+),(\d+),(\d?),(\w?),(.*),([0-5])$")
        partials = {} # For accumulating partial messages
        while True:
            payload = qIn.get()
            qIn.task_done()
            (t, ipAddr, port, body) = payload
            matches = reNEMA.match(body)
            if not matches:
                if not reIgnore.match(body):
                    logging.warning("Unrecognized NEMA sentence, %s", body)
                continue
            if not self.__chkSum(matches[1], matches[2]): continue
            fields = reSentence.match(matches[1])
            if not fields:
                logging.warning("Unrecognized sentence, %s", matches[1])
                continue
            msg = dict(
                    name       = fields[1],      # AVID[MO]
                    nFragments = int(fields[2]), # Number of fragments
                    iFragment  = int(fields[3]), # Fragment Number
                    ident      = fields[4],      # Multipart identification count
                               # Radio channel, A or 1 -> 161.975MHz, B or 2 -> 162.025MHz
                    channel    = fields[5],      
                    payload    = fields[6],      # data payload
                    fillbits   = int(fields[7]), # Number of fill bits
                    )
            if msg["nFragments"] == 1: # Simple message
                self.__decrypt(msg["payload"], msg["fillbits"], t)
                continue
            # Multipart message
            ident = msg["ident"]
            if ident not in partials: partials[ident] = {"payloads": {}, "fillBits": 0, "age": t}
            info = partials[ident]
            info["payloads"][msg["iFragment"]] = msg["payload"]
            if msg["nFragments"] == msg["iFragment"]: info["fillbits"] = msg["fillbits"]
            if len(info["payloads"]) == msg["nFragments"]: # We are done
                content = bytearray()
                for frag in sorted(partials[ident]["payloads"]): content += info["payloads"][frag]
                self.__decrypt(content, msg["fillbits"], info["age"])
                del partials[ident]
            if partials: # Age out partials so we don't have a memory leak
                tMin = time.time() - 60 # At most 1 minute
                toDrop = set()
                for ident in partials:
                    if partials[ident]["age"] < tMin:
                        toDrop.add(ident)
                for ident in toDrop: 
                    logging.warning("Aged out partial message, %s", partials[ident])
                    del partials[ident]

class AIS2DB(Thread.Thread):
    def __init__(self, name:str, args:ArgumentParser, decrypt:Decrypt) -> None:
        Thread.Thread.__init__(self, name, args)
        self.queue = queue.Queue()
        decrypt.addQueue(self.queue)
        self.sqlInsert = None
        self.sqlCreate = f"CREATE TABLE IF NOT EXISTS {args.aisTable} (\n"
        self.sqlCreate+= "  mmsi TEXT, -- AIS unique identifier\n"
        self.sqlCreate+= "  key TEXT, -- Field name in AIS message\n"
        self.sqlCreate+= "  t DOUBLE PRECISION, -- UTC seconds\n"
        self.sqlCreate+= "  value TEXT, -- field value\n"
        self.sqlCreate+= "  PRIMARY KEY(mmsi, key, t)\n"
        self.sqlCreate+= f"); -- {args.aisTable}"

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--aisTable", type=str, default="ais", help="AIS table name")

    def createTable(self, cursor) -> None:
        logging.debug("Creating table:\n%s", self.sqlCreate)
        cursor.execute(self.sqlCreate)

    def dbWrite(self, cursor, info:dict) -> None:
        if "t" not in info: return
        if "mmsi" not in info: return
        sql = self.sqlInsert
        mmsi = info["mmsi"]
        t = info["t"]
        for key in info: cursor.execute(sql, (mmsi, key, t, str(info[key])))

class AIS2SQLite3(AIS2DB):
    def __init__(self, args:ArgumentParser, decrypt:Decrypt) -> None:
        AIS2DB.__init__(self, "AIS2SQLite", args, decrypt)
        self.sqlInsert = f"INSERT OR IGNORE INTO {args.aisTable} VALUES(?,?,?,?);"

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--aisSQLite3", type=str, help="SQLite3 database")

    def runIt(self) -> None: # Called on thread start
        q = self.queue
        logging.info("Starting")
        qCreateTable = True
        while True:
            msg = q.get()
            q.task_done()
            with sqlite3.connect(args.aisSQLite3) as db:
                cursor = db.cursor()
                cursor.execute("BEGIN;")
                if qCreateTable: 
                    self.createTable(cursor)
                    qCreateTable = False
                self.dbWrite(cursor, msg)
                cursor.execute("COMMIT;")

class AIS2PostgreSQL(AIS2DB):
    def __init__(self, args:ArgumentParser, decrypt:Decrypt) -> None:
        AIS2DB.__init__(self, "AIS2PSQL", args, decrypt)
        self.sqlInsert = f"INSERT INTO {args.aisTable} VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING;"

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--aisPostgreSQL", type=str, help="PostgreSQL database")

    def runIt(self) -> None: # Called on thread start
        q = self.queue
        logging.info("Starting")
        qCreateTable = True
        with psycopg2.connect("dbname=" + args.aisPostgreSQL) as db:
            while True:
                msg = q.get()
                q.task_done()
                cursor = db.cursor()
                cursor.execute("BEGIN;")
                if qCreateTable: 
                    self.createTable(cursor)
                    qCreateTable = False
                self.dbWrite(cursor, msg)
                cursor.execute("COMMIT;")

class AIS2CSV(AIS2DB):
    def __init__(self, args:ArgumentParser, decrypt:Decrypt) -> None:
        AIS2DB.__init__(self, "AIS2CSV", args, decrypt)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--aisCSV", type=str, help="Output decoded AIS messages in CSV format")

    def runIt(self) -> None: # Called on thread start
        q = self.queue
        fn = self.args.aisCSV
        logging.info("Starting %s", fn)
        fields = ["t", "mmsi", "x", "y", "sog", "cog"]
        if not os.path.isfile(fn):
            with open(fn, "w") as fp: fp.write(",".join(fields) + "\n")

        while True:
            msg = q.get()
            q.task_done()
            items = []
            for key in fields: items.append(str(msg[key]) if key in msg else "")
            with open(fn, "a") as fp: fp.write(",".join(items) + "\n")

parser = ArgumentParser()
Logger.addArgs(parser)
Faux.addArgs(parser)
ReadSerial.addArgs(parser)
RawWriter.addArgs(parser)
Raw2SQLite.addArgs(parser)
Raw2PostgreSQL.addArgs(parser)
Raw2CSV.addArgs(parser)
AIS2DB.addArgs(parser)
AIS2SQLite3.addArgs(parser)
AIS2PostgreSQL.addArgs(parser)
AIS2CSV.addArgs(parser)
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

if args.rawSQLite3: thrds.append(Raw2SQLite(args, rdr))
if args.rawPostgreSQL: thrds.append(Raw2PostgreSQL(args, rdr))
if args.rawCSV: thrds.append(Raw2CSV(args, rdr))

if args.aisCSV or args.aisSQLite3 or args.aisPostgreSQL:
    decoder = Decrypt(args, rdr)
    thrds.append(decoder)
    if args.aisCSV: thrds.append(AIS2CSV(args, decoder))
    if args.aisSQLite3: thrds.append(AIS2SQLite3(args, decoder))
    if args.aisPostgreSQL: thrds.append(AIS2PostgreSQL(args, decoder))

for thrd in thrds: thrd.start() # Start all the threads

Thread.Thread.waitForException()
